from __future__ import annotations

import logging
from typing import Any

from langgraph.graph import END, StateGraph

from shared.contracts.incident_contracts import INCIDENT_SCENARIOS, IncidentEventType

from .knowledge_backend import KnowledgeBackend
from .llm_client import OpenAICompatibleLLMClient
from .normalization import normalize_recommendation_payload
from .prompts import PLANNER_SYSTEM_PROMPT, SYSTEM_PROMPT, build_planner_prompt, build_user_prompt
from .schemas import (
    AnalyzeIncidentRequest,
    AnalysisContextBundle,
    AnalysisEvent,
    InvestigationPlanRecord,
    InvestigationStepRecord,
    InvestigationWorkflowState,
    OperativeContext,
    RecommendationPayload,
    RetrievedDocumentChunk,
)
from .tools import AnalysisToolchain


class InvestigationWorkflow:
    """Run the controlled LangGraph investigation loop for a single incident.

    The workflow gathers operational context, retrieves supporting knowledge and
    RCA memories, asks the LLM planner what to inspect next, and finally asks
    the synthesis model to produce the operator-facing recommendation.
    """

    def __init__(
        self,
        knowledge_backend: KnowledgeBackend,
        llm_client: OpenAICompatibleLLMClient,
        toolchain: AnalysisToolchain,
        logger: logging.Logger | None = None,
    ) -> None:
        """Capture the shared dependencies used by the workflow graph.

        The backend and toolchain supply deterministic context, while the LLM
        client powers both the planner loop and the final recommendation
        synthesis step.
        """
        self.knowledge_backend = knowledge_backend
        self.llm_client = llm_client
        self.toolchain = toolchain
        self.logger = logger or logging.getLogger(__name__)
        self._graph = self._build_graph()

    def run(self, request: AnalyzeIncidentRequest) -> tuple[list[AnalysisEvent], RecommendationPayload, dict[str, Any]]:
        """Execute the LangGraph workflow and return events, output, and state."""
        return self._run_graph(request)

    def _run_graph(self, request: AnalyzeIncidentRequest) -> tuple[list[AnalysisEvent], RecommendationPayload, dict[str, Any]]:
        """Invoke the compiled graph and normalize its return payload."""
        graph_state = self._graph.invoke({"request": request})
        return (
            list(graph_state["analysis_events"]),
            graph_state["recommendation"],
            graph_state["workflow_state"],
        )

    def _build_graph(self):  # type: ignore[no-untyped-def]
        """Assemble the ordered investigation graph and its planner loop.

        The entry point starts with incident classification, then the planner
        decides whether we need more context, KB documents, RCA memories, or
        whether we should stop and synthesize a recommendation.
        """
        builder = StateGraph(dict)
        builder.add_node("incident_classifier", self._graph_incident_classifier)
        builder.add_node("investigation_planner", self._graph_investigation_planner)
        builder.add_node("context_collector", self._graph_context_collector)
        builder.add_node("knowledge_retriever", self._graph_knowledge_retriever)
        builder.add_node("rca_retriever", self._graph_rca_retriever)
        builder.add_node("hypothesis_generator", self._graph_hypothesis_generator)
        builder.add_node("evidence_verifier", self._graph_evidence_verifier)
        builder.add_node("recommendation_planner", self._graph_recommendation_planner)
        builder.add_node("response_composer", self._graph_response_composer)
        builder.add_node("final_recommendation", self._graph_final_recommendation)
        builder.add_edge("incident_classifier", "investigation_planner")
        builder.add_conditional_edges(
            "investigation_planner",
            self._route_investigation_planner,
            {
                "context_collector": "context_collector",
                "knowledge_retriever": "knowledge_retriever",
                "rca_retriever": "rca_retriever",
                "compose_response": "hypothesis_generator",
            },
        )
        builder.add_edge("context_collector", "investigation_planner")
        builder.add_edge("knowledge_retriever", "investigation_planner")
        builder.add_edge("rca_retriever", "investigation_planner")
        builder.add_edge("hypothesis_generator", "evidence_verifier")
        builder.add_edge("evidence_verifier", "recommendation_planner")
        builder.add_edge("recommendation_planner", "response_composer")
        builder.add_edge("response_composer", "final_recommendation")
        builder.add_edge("final_recommendation", END)
        builder.set_entry_point("incident_classifier")

        return builder.compile()

    def _graph_incident_classifier(self, state: dict[str, Any]) -> dict[str, Any]:
        """Classify the incident and seed the workflow state for later steps."""
        request: AnalyzeIncidentRequest = state["request"]
        self._log_node_state("incident_classifier", state, "start", service=request.service_name, severity=request.severity)
        workflow_state = self._initialize_state(request)
        classification_event, classification = self._classify_incident(request)
        state["classification"] = classification
        workflow_state.classification = classification
        state.setdefault("analysis_events", []).append(classification_event)
        state.setdefault("step_records", []).append(self._record_step("incident_classifier", classification_event))
        workflow_state.step_records = list(state["step_records"])
        state["workflow_state"] = workflow_state.model_dump(mode="json")
        state.setdefault("planner_decisions", [])
        state.setdefault("planner_iteration", 0)
        self._log_node_state(
            "incident_classifier",
            state,
            "complete",
            category=classification.get("category"),
            confidence=classification.get("confidence"),
        )
        return state

    def _graph_investigation_planner(self, state: dict[str, Any]) -> dict[str, Any]:
        """Ask the LLM planner what the next investigation action should be."""
        request: AnalyzeIncidentRequest = state["request"]
        self._log_node_state(
            "investigation_planner",
            state,
            "start",
            iteration=int(state.get("planner_iteration", 0)) + 1,
            context_collected=self._workflow_state_flag(state, "context_collected"),
            knowledge_retrieved=self._workflow_state_flag(state, "knowledge_retrieved"),
            rca_retrieved=self._workflow_state_flag(state, "rca_retrieved"),
        )
        workflow_state = InvestigationWorkflowState.model_validate(state["workflow_state"])
        workflow_state.step_records = list(state.get("step_records", []))
        workflow_state.planner_decisions = list(workflow_state.planner_decisions)
        workflow_state.iteration_count = int(state.get("planner_iteration", workflow_state.iteration_count)) + 1

        available_actions = self._planner_actions()
        planner_prompt = build_planner_prompt(
            self.toolchain.build_reference_query(request, state.get("context_bundle", AnalysisContextBundle(context=OperativeContext()))),
            self._latest_context_bundle(state).context,
            workflow_state=workflow_state.model_dump(mode="json"),
            available_actions=available_actions,
            iteration=workflow_state.iteration_count,
            max_iterations=4,
        )
        planner_payload: dict[str, Any] = {"reason": "", "focus": "", "query": "", "raw_model_output": None}
        try:
            llm_result = self.llm_client.generate_json(PLANNER_SYSTEM_PROMPT, planner_prompt)
            planner_payload["raw_model_output"] = llm_result.raw_text
            decision = self._normalize_planner_decision(llm_result.parsed_json)
        except Exception as exc:  # noqa: BLE001
            planner_payload["raw_model_output"] = None
            planner_payload["reason"] = f"planner fallback: {exc}"
            decision = {"next_action": "compose_response", "reason": "Planner fallback or invalid output", "query": "", "focus": ""}

        next_action = self._normalize_action(decision.get("next_action"))
        if workflow_state.iteration_count >= 4 and next_action != "compose_response":
            next_action = "compose_response"
            decision["reason"] = f"{decision.get('reason', '')} (forced compose after max iterations)".strip()
        decision["next_action"] = next_action
        planner_record = {
            "iteration": workflow_state.iteration_count,
            "next_action": next_action,
            "reason": str(decision.get("reason") or ""),
            "query": str(decision.get("query") or "") or None,
            "focus": str(decision.get("focus") or "") or None,
        }
        workflow_state.next_action = next_action
        workflow_state.planner_decisions.append(InvestigationPlanRecord.model_validate(planner_record))
        state["planner_iteration"] = workflow_state.iteration_count
        state["planner_decision"] = planner_record
        state["planner_payload"] = planner_payload
        state["workflow_state"] = workflow_state.model_dump(mode="json")

        planner_event = self._build_event(
            IncidentEventType.INVESTIGATION_PLANNED,
            "Investigation planner selected the next step",
            {
                "iteration": workflow_state.iteration_count,
                "next_action": next_action,
                "reason": planner_record["reason"],
                "query": planner_record["query"],
                "focus": planner_record["focus"],
            },
        )
        workflow_state.step_records.append(self._record_step("investigation_planner", planner_event))
        state["workflow_state"] = workflow_state.model_dump(mode="json")
        state.setdefault("analysis_events", []).append(planner_event)
        state.setdefault("step_records", []).append(self._record_step("investigation_planner", planner_event))
        self._log_node_state(
            "investigation_planner",
            state,
            "complete",
            next_action=next_action,
            reason=planner_record["reason"],
        )
        return state

    def _route_investigation_planner(self, state: dict[str, Any]) -> str:
        """Translate the planner decision into the next graph node name."""
        workflow_state = InvestigationWorkflowState.model_validate(state["workflow_state"])
        if not workflow_state.context_collected:
            self._log_node_state("investigation_planner", state, "route", route="context_collector")
            return "context_collector"
        if not workflow_state.knowledge_retrieved:
            self._log_node_state("investigation_planner", state, "route", route="knowledge_retriever")
            return "knowledge_retriever"
        if not workflow_state.rca_retrieved:
            self._log_node_state("investigation_planner", state, "route", route="rca_retriever")
            return "rca_retriever"
        action = self._normalize_action(str(state.get("planner_decision", {}).get("next_action", "")))
        if action in {"context_collector", "knowledge_retriever", "rca_retriever", "compose_response"}:
            self._log_node_state("investigation_planner", state, "route", route=action)
            return action
        self._log_node_state("investigation_planner", state, "route", route="compose_response")
        return "compose_response"

    def _graph_context_collector(self, state: dict[str, Any]) -> dict[str, Any]:
        """Collect logs, metrics, deployment data, and service metadata."""
        request: AnalyzeIncidentRequest = state["request"]
        self._log_node_state("context_collector", state, "start", service=request.service_name)
        workflow_state = InvestigationWorkflowState.model_validate(state["workflow_state"])
        analysis_events = state.setdefault("analysis_events", [])
        bundle = self._collect_context(request, workflow_state, analysis_events)
        state["context_bundle"] = bundle
        workflow_state.context = bundle.context
        workflow_state.context_collected = True
        workflow_state.step_records = list(state.get("step_records", []))
        state["workflow_state"] = workflow_state.model_dump(mode="json")
        self._log_node_state(
            "context_collector",
            state,
            "complete",
            log_count=len(bundle.context.log_evidence),
            metric_keys=sorted(bundle.context.metrics.keys()) if isinstance(bundle.context.metrics, dict) else [],
            deployment_count=len(bundle.context.deployments),
            service_metadata=bool(bundle.context.service_metadata),
        )
        return state

    def _graph_knowledge_retriever(self, state: dict[str, Any]) -> dict[str, Any]:
        """Retrieve runbooks and operational docs for the current query."""
        request: AnalyzeIncidentRequest = state["request"]
        self._log_node_state("knowledge_retriever", state, "start", service=request.service_name)
        workflow_state = InvestigationWorkflowState.model_validate(state["workflow_state"])
        analysis_events = state.setdefault("analysis_events", [])
        bundle = self._ensure_context_bundle(request, state, workflow_state, analysis_events)
        query = str(state.get("planner_decision", {}).get("query") or "").strip()
        if not query:
            query = self.toolchain.build_reference_query(request, bundle)
        state["query"] = query
        runbook_result = self.toolchain.runbook_retrieval.run(request, query)
        bundle.tool_results.append(runbook_result)
        bundle.tool_events.append(runbook_result.to_analysis_event())
        runbook_docs = self._extract_documents(runbook_result, "documents")
        bundle.context.runbook_chunks = [RetrievedDocumentChunk.model_validate(chunk) for chunk in runbook_docs]
        bundle.context.tool_results = bundle.tool_results
        retrieval_event = self._build_event(
            IncidentEventType.KNOWLEDGE_RETRIEVED,
            "Knowledge retrieval completed" if runbook_result.status == "success" else "Knowledge retrieval completed with partial failures",
            {
                "status": runbook_result.status,
                "runbook_count": len(bundle.context.runbook_chunks),
                "runbook_titles": [chunk.title for chunk in bundle.context.runbook_chunks[:3]],
                "tool_failures": [runbook_result.tool_name] if runbook_result.status != "success" else [],
                "query": query,
            },
        )
        workflow_state.context = bundle.context
        workflow_state.query = query
        state["context_bundle"] = bundle
        state["retrieval_bundle"] = bundle
        workflow_state.knowledge_retrieved = True
        workflow_state.step_records = list(state.get("step_records", []))
        workflow_state.step_records.append(self._record_step("knowledge_retriever", retrieval_event))
        state["workflow_state"] = workflow_state.model_dump(mode="json")
        state.setdefault("analysis_events", []).append(runbook_result.to_analysis_event())
        state.setdefault("analysis_events", []).append(retrieval_event)
        state.setdefault("step_records", []).append(self._record_step("knowledge_retriever", retrieval_event))
        self._log_node_state(
            "knowledge_retriever",
            state,
            "complete",
            runbook_count=len(bundle.context.runbook_chunks),
            tool_status=runbook_result.status,
            query=query,
        )
        return state

    def _graph_rca_retriever(self, state: dict[str, Any]) -> dict[str, Any]:
        """Retrieve similar historical RCAs and attach the matches to state."""
        request: AnalyzeIncidentRequest = state["request"]
        self._log_node_state("rca_retriever", state, "start", service=request.service_name)
        workflow_state = InvestigationWorkflowState.model_validate(state["workflow_state"])
        analysis_events = state.setdefault("analysis_events", [])
        bundle = self._ensure_context_bundle(request, state, workflow_state, analysis_events)
        query = str(state.get("planner_decision", {}).get("query") or "").strip()
        if not query:
            query = self.toolchain.build_reference_query(request, bundle)
        state["query"] = query
        rca_result = self.toolchain.rca_retrieval.run(request, query)
        bundle.tool_results.append(rca_result)
        bundle.tool_events.append(rca_result.to_analysis_event())
        rca_docs = self._extract_documents(rca_result, "documents")
        bundle.context.rca_chunks = [RetrievedDocumentChunk.model_validate(chunk) for chunk in rca_docs]
        rca_matches = rca_result.payload.get("matches")
        bundle.context.rca_matches = list(rca_matches) if isinstance(rca_matches, list) else []
        bundle.context.tool_results = bundle.tool_results
        retrieval_event = self._build_event(
            IncidentEventType.RCA_RETRIEVED,
            "RCA retrieval completed" if rca_result.status == "success" else "RCA retrieval completed with partial failures",
            {
                "status": rca_result.status,
                "rca_count": len(bundle.context.rca_chunks),
                "rca_match_count": len(bundle.context.rca_matches),
                "rca_titles": [chunk.title for chunk in bundle.context.rca_chunks[:3]],
                "tool_failures": [rca_result.tool_name] if rca_result.status != "success" else [],
                "query": query,
            },
        )
        workflow_state.context = bundle.context
        workflow_state.query = query
        state["context_bundle"] = bundle
        state["retrieval_bundle"] = bundle
        workflow_state.rca_retrieved = True
        workflow_state.step_records = list(state.get("step_records", []))
        workflow_state.step_records.append(self._record_step("rca_retriever", retrieval_event))
        state["workflow_state"] = workflow_state.model_dump(mode="json")
        state.setdefault("analysis_events", []).append(rca_result.to_analysis_event())
        state.setdefault("analysis_events", []).append(retrieval_event)
        state.setdefault("step_records", []).append(self._record_step("rca_retriever", retrieval_event))
        self._log_node_state(
            "rca_retriever",
            state,
            "complete",
            rca_count=len(bundle.context.rca_chunks),
            rca_match_count=len(bundle.context.rca_matches),
            tool_status=rca_result.status,
            query=query,
        )
        return state

    def _graph_hypothesis_generator(self, state: dict[str, Any]) -> dict[str, Any]:
        """Turn gathered context into candidate root-cause hypotheses."""
        request: AnalyzeIncidentRequest = state["request"]
        self._log_node_state("hypothesis_generator", state, "start", service=request.service_name)
        classification = state["classification"]
        bundle = self._latest_context_bundle(state)
        runbook_chunks = list(bundle.context.runbook_chunks)
        rca_chunks = list(bundle.context.rca_chunks)
        hypotheses, hypothesis_payload = self._generate_hypotheses(request, classification, bundle, runbook_chunks, rca_chunks)
        state["hypotheses"] = hypotheses
        workflow_state = InvestigationWorkflowState.model_validate(state["workflow_state"])
        workflow_state.step_records = list(state.get("step_records", []))
        workflow_state.hypotheses = hypotheses
        hypothesis_event = self._build_event(
            IncidentEventType.HYPOTHESIS_GENERATED,
            "Hypotheses generated from collected context",
            hypothesis_payload,
        )
        workflow_state.step_records.append(self._record_step("hypothesis_generator", hypothesis_event))
        state["workflow_state"] = workflow_state.model_dump(mode="json")
        state.setdefault("analysis_events", []).append(hypothesis_event)
        state.setdefault("step_records", []).append(self._record_step("hypothesis_generator", hypothesis_event))
        self._log_node_state(
            "hypothesis_generator",
            state,
            "complete",
            hypothesis_count=len(hypotheses),
            primary_confidence=classification.get("confidence"),
        )
        return state

    def _graph_evidence_verifier(self, state: dict[str, Any]) -> dict[str, Any]:
        """Check which hypotheses are actually supported by the evidence."""
        request: AnalyzeIncidentRequest = state["request"]
        self._log_node_state("evidence_verifier", state, "start", service=request.service_name)
        bundle = self._latest_context_bundle(state)
        runbook_chunks = list(bundle.context.runbook_chunks)
        rca_chunks = list(bundle.context.rca_chunks)
        hypotheses = state["hypotheses"]
        verification, verification_payload = self._verify_evidence(request, hypotheses, bundle, runbook_chunks, rca_chunks)
        state["verification"] = verification
        workflow_state = InvestigationWorkflowState.model_validate(state["workflow_state"])
        workflow_state.step_records = list(state.get("step_records", []))
        workflow_state.verification = verification
        evidence_event = self._build_event(
            IncidentEventType.EVIDENCE_VERIFIED,
            "Evidence verification completed",
            verification_payload,
        )
        workflow_state.step_records.append(self._record_step("evidence_verifier", evidence_event))
        state["workflow_state"] = workflow_state.model_dump(mode="json")
        state.setdefault("analysis_events", []).append(evidence_event)
        state.setdefault("step_records", []).append(self._record_step("evidence_verifier", evidence_event))
        self._log_node_state(
            "evidence_verifier",
            state,
            "complete",
            verified_count=sum(1 for item in verification if item.get("supported")),
            verification_count=len(verification),
        )
        return state

    def _graph_recommendation_planner(self, state: dict[str, Any]) -> dict[str, Any]:
        """Summarize the investigation into a concrete action direction."""
        request: AnalyzeIncidentRequest = state["request"]
        self._log_node_state("recommendation_planner", state, "start", service=request.service_name)
        classification = state["classification"]
        hypotheses = state["hypotheses"]
        verification = state["verification"]
        recommendation_plan_payload = self._build_recommendation_plan_payload(request, classification, hypotheses, verification)
        recommendation_plan_event = self._build_event(
            IncidentEventType.RECOMMENDATION_PLANNED,
            "Recommendation plan assembled",
            recommendation_plan_payload,
        )
        workflow_state = InvestigationWorkflowState.model_validate(state["workflow_state"])
        workflow_state.step_records = list(state.get("step_records", []))
        workflow_state.step_records.append(self._record_step("recommendation_planner", recommendation_plan_event))
        state["workflow_state"] = workflow_state.model_dump(mode="json")
        state.setdefault("analysis_events", []).append(recommendation_plan_event)
        state.setdefault("step_records", []).append(self._record_step("recommendation_planner", recommendation_plan_event))
        self._log_node_state(
            "recommendation_planner",
            state,
            "complete",
            supported_count=len([item for item in verification if item.get("supported")]),
            likely_cause=classification.get("likely_cause"),
        )
        return state

    def _graph_response_composer(self, state: dict[str, Any]) -> dict[str, Any]:
        """Ask the synthesis model to write the final recommendation payload."""
        request: AnalyzeIncidentRequest = state["request"]
        self._log_node_state("response_composer", state, "start", service=request.service_name)
        bundle = self._latest_context_bundle(state)
        classification = state["classification"]
        hypotheses = state["hypotheses"]
        verification = state["verification"]
        workflow_state = InvestigationWorkflowState.model_validate(state["workflow_state"])
        workflow_state.step_records = list(state.get("step_records", []))
        runbook_chunks = list(bundle.context.runbook_chunks)
        rca_chunks = list(bundle.context.rca_chunks)
        recommendation, response_event, llm_payload = self._compose_response(
            request=request,
            state=workflow_state,
            bundle=bundle,
            runbook_chunks=runbook_chunks,
            rca_chunks=rca_chunks,
            classification=classification,
            hypotheses=hypotheses,
            verification=verification,
        )
        recommendation = self._enrich_recommendation(
            recommendation,
            request=request,
            bundle=bundle,
            classification=classification,
            hypotheses=hypotheses,
            verification=verification,
            runbook_chunks=runbook_chunks,
            rca_chunks=rca_chunks,
        )
        workflow_state.fallback_used = bool(llm_payload.get("fallback_used"))
        workflow_state.notes.extend([str(item) for item in llm_payload.get("notes", []) if str(item).strip()])
        workflow_state.step_records.append(self._record_step("response_composer", response_event))
        state["recommendation"] = recommendation
        state["llm_payload"] = llm_payload
        state["workflow_state"] = workflow_state.model_dump(mode="json")
        state.setdefault("analysis_events", []).append(response_event)
        state.setdefault("step_records", []).append(self._record_step("response_composer", response_event))
        self._log_node_state(
            "response_composer",
            state,
            "complete",
            fallback_used=workflow_state.fallback_used,
            confidence=recommendation.confidence,
            evidence_count=len(recommendation.evidence),
            action_count=len(recommendation.recommended_actions),
        )
        return state

    def _graph_final_recommendation(self, state: dict[str, Any]) -> dict[str, Any]:
        """Attach the final recommendation to the workflow state and emit it."""
        recommendation: RecommendationPayload = state["recommendation"]
        self._log_node_state("final_recommendation", state, "start", confidence=recommendation.confidence)
        workflow_state = InvestigationWorkflowState.model_validate(state["workflow_state"])
        workflow_state.step_records = list(state.get("step_records", []))
        workflow_state.fallback_used = bool(state.get("llm_payload", {}).get("fallback_used"))
        workflow_state.notes.extend([str(item) for item in state.get("llm_payload", {}).get("notes", []) if str(item).strip()])
        recommendation_event = self._build_event(
            IncidentEventType.RECOMMENDATION_GENERATED,
            "Structured recommendation generated",
            {
                "workflow_stage": "response_composed",
                "confidence": recommendation.confidence,
                "fallback_used": workflow_state.fallback_used,
            },
        )
        workflow_state.step_records.append(self._record_step("final_recommendation", recommendation_event))
        state["workflow_state"] = workflow_state.model_dump(mode="json")
        state.setdefault("analysis_events", []).append(recommendation_event)
        state.setdefault("step_records", []).append(self._record_step("final_recommendation", recommendation_event))
        recommendation.raw_model_output = {
            "workflow_state": state["workflow_state"],
            "classification": state.get("classification", {}),
            "query": state.get("query", ""),
            "operational_context": self._latest_context_bundle(state).context.model_dump(mode="json"),
            "tool_results": [tool_result.model_dump(mode="json") for tool_result in self._latest_context_bundle(state).tool_results],
            "retrieved_chunks": [chunk.model_dump(mode="json") for chunk in [*self._latest_context_bundle(state).context.runbook_chunks, *self._latest_context_bundle(state).context.rca_chunks]],
            "hypotheses": state.get("hypotheses", []),
            "verification": state.get("verification", []),
            "incident_summary": recommendation.incident_summary,
            "symptoms": recommendation.symptoms,
            "risk_level": recommendation.risk_level,
            "source_documents": recommendation.source_documents,
            "similar_rcas": recommendation.similar_rcas,
            "unsupported_areas": recommendation.unsupported_areas,
            "action_evidence_links": recommendation.action_evidence_links,
            "fallback_used": workflow_state.fallback_used,
            **state.get("llm_payload", {}),
        }
        self._log_node_state(
            "final_recommendation",
            state,
            "complete",
            fallback_used=workflow_state.fallback_used,
            total_steps=len(workflow_state.step_records),
        )
        return state

    def _latest_context_bundle(self, state: dict[str, Any]) -> AnalysisContextBundle:
        """Return the most recent context bundle, or an empty one if absent."""
        bundle = state.get("retrieval_bundle") or state.get("context_bundle")
        if isinstance(bundle, AnalysisContextBundle):
            return bundle
        return AnalysisContextBundle(context=OperativeContext())

    def _ensure_context_bundle(
        self,
        request: AnalyzeIncidentRequest,
        state: dict[str, Any],
        workflow_state: InvestigationWorkflowState,
        analysis_events: list[AnalysisEvent],
    ) -> AnalysisContextBundle:
        """Guarantee that the workflow has a context bundle before retrieval."""
        bundle = state.get("context_bundle")
        if isinstance(bundle, AnalysisContextBundle):
            return bundle
        bundle = self._collect_context(request, workflow_state, analysis_events)
        state["context_bundle"] = bundle
        state["workflow_state"] = workflow_state.model_dump(mode="json")
        state.setdefault("step_records", []).extend(workflow_state.step_records[-1:])
        return bundle

    def _planner_actions(self) -> list[dict[str, str]]:
        """Return the allowed next-step actions shown to the LLM planner."""
        return [
            {"action": "context_collector", "description": "Gather logs, metrics, deployment context, and service metadata."},
            {"action": "knowledge_retriever", "description": "Retrieve runbooks and operational documentation."},
            {"action": "rca_retriever", "description": "Retrieve similar historical RCAs and incident memories."},
            {"action": "compose_response", "description": "Stop gathering data and synthesize the recommendation."},
        ]

    def _normalize_planner_decision(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Sanitize the planner JSON so invalid values collapse to safe defaults."""
        next_action = self._normalize_action(str(payload.get("next_action", "")))
        return {
            "next_action": next_action,
            "reason": str(payload.get("reason") or ""),
            "query": str(payload.get("query") or "").strip(),
            "focus": str(payload.get("focus") or "").strip(),
        }

    def _normalize_action(self, action: str) -> str:
        """Map a planner action string onto the supported graph node names."""
        normalized = action.strip().lower().replace(" ", "_").replace("-", "_")
        allowed = {"context_collector", "knowledge_retriever", "rca_retriever", "compose_response"}
        return normalized if normalized in allowed else "compose_response"

    def _initialize_state(self, request: AnalyzeIncidentRequest) -> InvestigationWorkflowState:
        """Create a fresh workflow state object for the incoming incident."""
        return InvestigationWorkflowState(
            incident_id=request.incident_id,
            scenario_id=request.scenario_id,
            service_name=request.service_name,
            severity=request.severity,
            symptom=request.symptom,
            context=OperativeContext(),
        )

    def _classify_incident(self, request: AnalyzeIncidentRequest) -> tuple[AnalysisEvent, dict[str, Any]]:
        """Derive the initial incident classification from the request payload."""
        classification = self._derive_classification(request)
        event = self._build_event(
            IncidentEventType.INCIDENT_CLASSIFIED,
            "Incident classified for investigation",
            classification,
        )
        return event, classification

    def _collect_context(
        self,
        request: AnalyzeIncidentRequest,
        state: InvestigationWorkflowState,
        analysis_events: list[AnalysisEvent],
    ) -> AnalysisContextBundle:
        """Gather logs, metrics, deployments, and service metadata in one pass."""
        bundle = self.toolchain.collect_context(request)
        tool_failures = [tool_result.tool_name for tool_result in bundle.tool_results if tool_result.status != "success"]
        context_status = "success" if not tool_failures else "partial"
        summary_event = self._build_event(
            IncidentEventType.CONTEXT_COLLECTED,
            "Context collection completed" if not tool_failures else "Context collection completed with partial failures",
            {
                "status": context_status,
                "log_evidence_count": len(bundle.context.log_evidence),
                "metric_keys": sorted(bundle.context.metrics.keys()) if isinstance(bundle.context.metrics, dict) else [],
                "deployment_count": len(bundle.context.deployments),
                "has_service_metadata": bool(bundle.context.service_metadata),
                "tool_failures": tool_failures,
            },
        )
        state.step_records.append(self._record_step("context_collector", summary_event))
        analysis_events.extend(bundle.tool_events)
        analysis_events.append(summary_event)
        return bundle

    def _retrieve_reference_material(
        self,
        request: AnalyzeIncidentRequest,
        query: str,
        bundle: AnalysisContextBundle,
        state: InvestigationWorkflowState,
        analysis_events: list[AnalysisEvent],
    ) -> AnalysisContextBundle:
        """Retrieve the primary knowledge documents for the current incident."""
        bundle = self.toolchain.retrieve_reference_material(request, query, bundle)
        retrieval_failures = [tool_result.tool_name for tool_result in bundle.tool_results if tool_result.status != "success"]
        retrieval_summary = self._build_event(
            IncidentEventType.KNOWLEDGE_RETRIEVED,
            "Knowledge retrieval completed" if not retrieval_failures else "Knowledge retrieval completed with partial failures",
            {
                "status": "success" if not retrieval_failures else "partial",
                "runbook_count": len(bundle.context.runbook_chunks),
                "rca_count": len(bundle.context.rca_chunks),
                "rca_match_count": len(bundle.context.rca_matches),
                "runbook_titles": [chunk.title for chunk in bundle.context.runbook_chunks[:3]],
                "rca_titles": [match.get("title") for match in bundle.context.rca_matches[:3] if isinstance(match, dict)],
                "tool_failures": retrieval_failures,
            },
        )
        state.step_records.append(self._record_step("knowledge_retriever", retrieval_summary))
        analysis_events.append(retrieval_summary)
        return bundle

    def _generate_hypotheses(
        self,
        request: AnalyzeIncidentRequest,
        classification: dict[str, Any],
        bundle: AnalysisContextBundle,
        runbook_chunks: list[RetrievedDocumentChunk],
        rca_chunks: list[RetrievedDocumentChunk],
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Create candidate hypotheses from classification, docs, and RCAs."""
        scenario = self._scenario_for_request(request.scenario_id)
        direction = str(scenario.get("expected_recommendation_direction") or "investigate_deeper")
        hypotheses: list[dict[str, Any]] = []

        primary_hypothesis = {
            "hypothesis": classification["likely_cause"],
            "confidence": classification["confidence"],
            "supporting_signals": classification["signals"],
            "evidence_gaps": [],
        }
        hypotheses.append(primary_hypothesis)

        if rca_chunks:
            hypotheses.append(
                {
                    "hypothesis": f"Historical RCA memory suggests the issue aligns with {direction.replace('_', ' ')}.",
                    "confidence": "medium" if len(rca_chunks) > 1 else "low",
                    "supporting_signals": [chunk.title for chunk in rca_chunks[:3]],
                    "evidence_gaps": [],
                }
            )

        if runbook_chunks:
            hypotheses.append(
                {
                    "hypothesis": f"Runbook guidance supports {direction.replace('_', ' ')} for {request.service_name}.",
                    "confidence": "medium",
                    "supporting_signals": [chunk.title for chunk in runbook_chunks[:3]],
                    "evidence_gaps": [],
                }
            )

        payload = {
            "status": "success",
            "hypothesis_count": len(hypotheses),
            "hypotheses": hypotheses,
            "expected_direction": direction,
        }
        return hypotheses, payload

    def _verify_evidence(
        self,
        request: AnalyzeIncidentRequest,
        hypotheses: list[dict[str, Any]],
        bundle: AnalysisContextBundle,
        runbook_chunks: list[RetrievedDocumentChunk],
        rca_chunks: list[RetrievedDocumentChunk],
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Check which hypotheses are actually supported by the evidence set."""
        evidence_texts = self._gather_evidence_texts(bundle, runbook_chunks, rca_chunks)
        verified: list[dict[str, Any]] = []
        for hypothesis in hypotheses:
            support_hits = [
                evidence
                for evidence in evidence_texts
                if any(signal.lower() in evidence for signal in hypothesis.get("supporting_signals", []))
            ]
            verified.append(
                {
                    "hypothesis": hypothesis["hypothesis"],
                    "supported": bool(support_hits),
                    "supporting_evidence": support_hits[:5],
                    "confidence": hypothesis["confidence"],
                }
            )
        payload = {
            "status": "success",
            "verified_count": sum(1 for item in verified if item["supported"]),
            "verification": verified,
        }
        return verified, payload

    def _build_recommendation_plan_payload(
        self,
        request: AnalyzeIncidentRequest,
        classification: dict[str, Any],
        hypotheses: list[dict[str, Any]],
        verification: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Summarize the investigation into a small action-oriented payload."""
        supported = [item for item in verification if item["supported"]]
        return {
            "status": "success",
            "incident_category": classification["category"],
            "likely_cause": classification["likely_cause"],
            "supported_hypotheses": [item["hypothesis"] for item in supported],
            "action_direction": self._scenario_for_request(request.scenario_id).get("expected_recommendation_direction", ""),
            "hypothesis_count": len(hypotheses),
            "supported_count": len(supported),
        }

    def _compose_response(
        self,
        request: AnalyzeIncidentRequest,
        state: InvestigationWorkflowState,
        bundle: AnalysisContextBundle,
        runbook_chunks: list[RetrievedDocumentChunk],
        rca_chunks: list[RetrievedDocumentChunk],
        classification: dict[str, Any],
        hypotheses: list[dict[str, Any]],
        verification: list[dict[str, Any]],
    ) -> tuple[RecommendationPayload, AnalysisEvent, dict[str, Any]]:
        """Call the synthesis LLM and normalize it into the recommendation schema."""
        prompt = build_user_prompt(
            self.toolchain.build_reference_query(request, bundle),
            bundle.context,
            [*runbook_chunks, *rca_chunks],
            workflow_state=state.model_dump(mode="json"),
        )
        llm_payload: dict[str, Any] = {"prompt": prompt, "notes": []}
        recommendation: RecommendationPayload
        fallback_used = False
        try:
            llm_result = self.llm_client.generate_json(SYSTEM_PROMPT, prompt)
            recommendation = normalize_recommendation_payload(llm_result.parsed_json)
            llm_payload["llm_response"] = llm_result.raw_text
        except Exception as exc:  # noqa: BLE001
            fallback_used = True
            llm_payload["notes"].append(str(exc))
            recommendation = self._build_fallback_recommendation(
                request=request,
                classification=classification,
                hypotheses=hypotheses,
                verification=verification,
                bundle=bundle,
                runbook_chunks=runbook_chunks,
                rca_chunks=rca_chunks,
            )
            llm_payload["llm_response"] = None

        response_event = self._build_event(
            IncidentEventType.RESPONSE_COMPOSED,
            "Final response composed from investigation workflow",
            {
                "status": "success" if not fallback_used else "fallback",
                "fallback_used": fallback_used,
                "confidence": recommendation.confidence,
                "evidence_count": len(recommendation.evidence),
                "recommended_action_count": len(recommendation.recommended_actions),
            },
        )
        llm_payload["fallback_used"] = fallback_used
        return recommendation, response_event, llm_payload

    def _build_fallback_recommendation(
        self,
        request: AnalyzeIncidentRequest,
        classification: dict[str, Any],
        hypotheses: list[dict[str, Any]],
        verification: list[dict[str, Any]],
        bundle: AnalysisContextBundle,
        runbook_chunks: list[RetrievedDocumentChunk],
        rca_chunks: list[RetrievedDocumentChunk],
    ) -> RecommendationPayload:
        """Create a deterministic recommendation when the synthesis LLM fails."""
        scenario = self._scenario_for_request(request.scenario_id)
        direction = str(scenario.get("expected_recommendation_direction") or "investigate_deeper")
        action_map = {
            "stabilize_kafka_consumers": [
                "Increase Kafka consumer capacity and reduce retry pressure.",
                "Restore safer consumer retry and polling settings.",
            ],
            "scale_connection_pool": [
                "Increase the database connection pool limit.",
                "Reduce connection hold time and retry pressure.",
            ],
            "tune_gateway_timeouts": [
                "Tune gateway timeout and retry budget settings.",
                "Review upstream dependency saturation and route dwell time.",
            ],
            "scale_workers_and_drain_queue": [
                "Scale worker concurrency to clear the backlog.",
                "Drain pending jobs and check downstream dependency latency.",
            ],
        }
        evidence = self._build_evidence(request, classification, bundle, runbook_chunks, rca_chunks, hypotheses, verification)
        confidence = "high" if len(rca_chunks) or len(runbook_chunks) > 1 else "medium"
        recommendation = RecommendationPayload(
            summary=(
                f"{request.service_name} is showing {classification['category'].replace('_', ' ')} signals. "
                f"Recommended focus: {direction.replace('_', ' ')}."
            ),
            evidence=evidence,
            recommended_actions=action_map.get(direction, [f"Investigate and mitigate {direction.replace('_', ' ')}."]),
            confidence=confidence,
            requires_human_approval=True,
            incident_summary=f"{request.service_name} incident with {request.severity} severity",
            symptoms=[request.symptom],
            risk_level=self._risk_level_for_request(request, classification, verification),
            hypotheses=hypotheses,
            source_documents=[
                {
                    "title": chunk.title,
                    "doc_type": chunk.doc_type,
                    "service": chunk.service,
                    "source": chunk.source,
                    "tags": list(chunk.tags),
                    "chunk_index": chunk.chunk_index,
                    "score": chunk.score,
                }
                for chunk in [*runbook_chunks, *rca_chunks]
            ],
            similar_rcas=[
                {
                    "title": match.get("title"),
                    "service_name": match.get("service_name"),
                    "score": match.get("score"),
                    "match_explanation": match.get("match_explanation"),
                    "matched_signals": match.get("matched_signals", []),
                    "root_cause": match.get("root_cause"),
                    "resolution": match.get("resolution"),
                }
                for match in bundle.context.rca_matches
                if isinstance(match, dict)
            ],
            unsupported_areas=[item["hypothesis"] for item in verification if not item.get("supported")],
            action_evidence_links=[
                {
                    "action": action,
                    "evidence": evidence[:3],
                    "source_documents": [chunk.title for chunk in [*runbook_chunks, *rca_chunks][:3]],
                    "similar_rcas": [match.get("title") for match in bundle.context.rca_matches[:3] if isinstance(match, dict)],
                }
                for action in action_map.get(direction, [f"Investigate and mitigate {direction.replace('_', ' ')}."])
            ],
        )
        return recommendation

    def _build_evidence(
        self,
        request: AnalyzeIncidentRequest,
        classification: dict[str, Any],
        bundle: AnalysisContextBundle,
        runbook_chunks: list[RetrievedDocumentChunk],
        rca_chunks: list[RetrievedDocumentChunk],
        hypotheses: list[dict[str, Any]],
        verification: list[dict[str, Any]],
    ) -> list[str]:
        """Convert the gathered signals into concise operator-facing evidence lines."""
        evidence: list[str] = []
        if bundle.context.metrics:
            metric_name = request.metric_name or "metric"
            evidence.append(
                f"Metrics show {metric_name} at {request.metric_value} versus threshold {request.threshold_value}."
            )
        if bundle.context.log_evidence:
            evidence.append(f"Logs summarize {len(bundle.context.log_evidence)} operational signals from OpenSearch.")
        if runbook_chunks:
            evidence.append(f"Runbooks retrieved: {', '.join(chunk.title for chunk in runbook_chunks[:3])}.")
        if rca_chunks:
            evidence.append(f"Similar RCAs retrieved: {', '.join(chunk.title for chunk in rca_chunks[:3])}.")
        evidence.append(f"Classification: {classification['likely_cause']}")
        evidence.extend(
            f"Hypothesis: {item['hypothesis']} ({'supported' if item['supported'] else 'not fully supported'})"
            for item in verification
        )
        return evidence[:8]

    def _enrich_recommendation(
        self,
        recommendation: RecommendationPayload,
        *,
        request: AnalyzeIncidentRequest,
        bundle: AnalysisContextBundle,
        classification: dict[str, Any],
        hypotheses: list[dict[str, Any]],
        verification: list[dict[str, Any]],
        runbook_chunks: list[RetrievedDocumentChunk],
        rca_chunks: list[RetrievedDocumentChunk],
    ) -> RecommendationPayload:
        """Attach structured evidence metadata to the recommendation payload."""
        source_documents = [
            {
                "title": chunk.title,
                "doc_type": chunk.doc_type,
                "service": chunk.service,
                "source": chunk.source,
                "tags": list(chunk.tags),
                "chunk_index": chunk.chunk_index,
                "score": chunk.score,
            }
            for chunk in [*runbook_chunks, *rca_chunks]
        ]
        similar_rcas = [
            {
                "title": match.get("title"),
                "service_name": match.get("service_name"),
                "score": match.get("score"),
                "match_explanation": match.get("match_explanation"),
                "matched_signals": match.get("matched_signals", []),
                "root_cause": match.get("root_cause"),
                "resolution": match.get("resolution"),
            }
            for match in bundle.context.rca_matches
            if isinstance(match, dict)
        ]
        action_evidence_links: list[dict[str, Any]] = []
        source_titles = [item["title"] for item in source_documents if item.get("title")]
        rca_titles = [item["title"] for item in similar_rcas if item.get("title")]
        for action in recommendation.recommended_actions:
            action_evidence_links.append(
                {
                    "action": action,
                    "evidence": recommendation.evidence[:3],
                    "source_documents": source_titles[:3],
                    "similar_rcas": rca_titles[:3],
                }
            )

        unsupported_areas = [item["hypothesis"] for item in verification if not item.get("supported")]
        if not runbook_chunks:
            unsupported_areas.append("No runbook was retrieved for this incident.")
        if not rca_chunks:
            unsupported_areas.append("No similar RCA was retrieved for this incident.")
        if not bundle.context.log_evidence:
            unsupported_areas.append("No log evidence was retrieved for this incident.")

        recommendation.incident_summary = f"{request.service_name} incident with {request.severity} severity"
        recommendation.symptoms = [request.symptom]
        recommendation.risk_level = self._risk_level_for_request(request, classification, verification)
        recommendation.hypotheses = hypotheses
        recommendation.source_documents = source_documents
        recommendation.similar_rcas = similar_rcas
        recommendation.unsupported_areas = list(dict.fromkeys(unsupported_areas))
        recommendation.action_evidence_links = action_evidence_links
        return recommendation

    def _gather_evidence_texts(
        self,
        bundle: AnalysisContextBundle,
        runbook_chunks: list[RetrievedDocumentChunk],
        rca_chunks: list[RetrievedDocumentChunk],
    ) -> list[str]:
        """Flatten all operational artifacts into searchable lowercase text."""
        texts: list[str] = []
        for log in bundle.context.log_evidence:
            texts.append(str(log.summary).lower())
            texts.extend(str(error.get("error", "")).lower() for error in log.top_errors if isinstance(error, dict))
            texts.extend(str(message).lower() for message in log.sample_messages)
        if bundle.context.metrics:
            texts.append(str(bundle.context.metrics).lower())
        if bundle.context.deployments:
            texts.append(str(bundle.context.deployments).lower())
        if bundle.context.service_metadata:
            texts.append(str(bundle.context.service_metadata).lower())
        for chunk in [*runbook_chunks, *rca_chunks]:
            texts.append(chunk.title.lower())
            texts.append(chunk.text.lower())
        for match in bundle.context.rca_matches:
            if isinstance(match, dict):
                texts.append(str(match.get("match_explanation", "")).lower())
                texts.append(str(match.get("root_cause", "")).lower())
                texts.append(str(match.get("resolution", "")).lower())
        return texts

    def _risk_level_for_request(
        self,
        request: AnalyzeIncidentRequest,
        classification: dict[str, Any],
        verification: list[dict[str, Any]],
    ) -> str:
        """Estimate a readable risk level from severity and evidence support."""
        severity = request.severity.upper()
        if severity in {"P0", "P1"}:
            return "high"
        if severity == "P2":
            return "medium" if any(item.get("supported") for item in verification) else "high"
        if classification.get("confidence") == "high" and any(item.get("supported") for item in verification):
            return "medium"
        return "low"

    def _derive_classification(self, request: AnalyzeIncidentRequest) -> dict[str, Any]:
        """Infer a lightweight incident classification from the scenario text."""
        symptom = request.symptom.lower()
        category = "service_degradation"
        signals: list[str] = [request.service_name, request.severity, request.symptom]
        likely_cause = f"{request.service_name} incident"
        confidence = "medium"

        if "timeout" in symptom or "latency" in symptom:
            category = "latency_timeout"
            likely_cause = f"{request.service_name} is impacted by latency and timeout pressure"
            signals.append("timeout/latency symptoms")
            confidence = "high"
        if "queue" in symptom or "backlog" in symptom:
            category = "queue_backlog"
            likely_cause = f"{request.service_name} is experiencing queue pressure and worker saturation"
            signals.append("queue pressure")
            confidence = "high"
        if "connection" in symptom or "pool" in symptom:
            category = "resource_exhaustion"
            likely_cause = f"{request.service_name} is likely experiencing resource exhaustion"
            signals.append("resource exhaustion")
            confidence = "high"

        scenario = self._scenario_for_request(request.scenario_id)
        if scenario:
            signals.extend([scenario.get("label", ""), scenario.get("description", "")])

        return {
            "category": category,
            "service_name": request.service_name,
            "severity": request.severity,
            "likely_cause": likely_cause,
            "confidence": confidence,
            "signals": [signal for signal in signals if str(signal).strip()],
        }

    def _scenario_for_request(self, scenario_id: str) -> dict[str, Any]:
        """Look up the seeded scenario metadata for the current request."""
        for scenario in INCIDENT_SCENARIOS:
            if scenario["scenario_id"] == scenario_id:
                return scenario
        return {}

    def _record_step(self, step_name: str, event: AnalysisEvent) -> InvestigationStepRecord:
        """Translate an emitted event into the persisted workflow step format."""
        payload = event.payload or {}
        return InvestigationStepRecord(
            step_name=step_name,
            event_type=event.event_type,
            status=str(payload.get("status", "success")) if payload else "success",
            message=event.message,
            payload=dict(payload),
            error=payload.get("error") if isinstance(payload, dict) else None,
        )

    def _build_event(
        self,
        event_type: IncidentEventType,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> AnalysisEvent:
        """Create a normalized workflow event for the incident timeline."""
        return AnalysisEvent(event_type=event_type, message=message, payload=payload or None)

    def _extract_documents(self, result: Any, key: str) -> list[dict[str, Any]]:
        """Pull a document list from a tool result payload in a safe, uniform way."""
        payload = getattr(result, "payload", {})
        documents = payload.get(key) if isinstance(payload, dict) else None
        return list(documents) if isinstance(documents, list) else []

    def _log_node_state(self, node_name: str, state: dict[str, Any], phase: str, **details: Any) -> None:
        """Emit a compact, readable trace line for each graph node transition."""
        workflow_state = state.get("workflow_state")
        incident_id = ""
        iteration = state.get("planner_iteration")
        next_action = state.get("planner_decision", {}).get("next_action")
        if isinstance(workflow_state, dict):
            incident_id = str(workflow_state.get("incident_id", ""))
            iteration = workflow_state.get("iteration_count", iteration)
            next_action = workflow_state.get("next_action", next_action)
        self.logger.info(
            "workflow node=%s phase=%s incident_id=%s iteration=%s next_action=%s details=%s",
            node_name,
            phase,
            incident_id or str(state.get("request", {}).incident_id if state.get("request") else ""),
            iteration,
            next_action,
            details,
        )

    def _workflow_state_flag(self, state: dict[str, Any], flag_name: str) -> bool:
        """Read a boolean flag from the serialized workflow state if present."""
        workflow_state = state.get("workflow_state")
        if isinstance(workflow_state, dict):
            return bool(workflow_state.get(flag_name, False))
        return False
