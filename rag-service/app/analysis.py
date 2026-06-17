from __future__ import annotations

import logging
import time
from collections.abc import Iterable
from typing import Any

from shared.contracts.incident_contracts import IncidentEventType

from .data_loader import load_logs, load_metrics, load_recent_deployments, load_service_metadata
from .llm_client import OpenAICompatibleLLMClient
from .normalization import normalize_recommendation_payload
from .prompts import SYSTEM_PROMPT, build_user_prompt
from .retrieval import KnowledgeBase, format_context_for_query
from .schemas import AnalyzeIncidentRequest, AnalyzeIncidentResponse, AnalysisEvent, OperativeContext


class AnalysisEngine:
    def __init__(
        self,
        knowledge_base: KnowledgeBase | None = None,
        llm_client: OpenAICompatibleLLMClient | None = None,
    ) -> None:
        self.knowledge_base = knowledge_base or KnowledgeBase()
        self.llm_client = llm_client or OpenAICompatibleLLMClient()
        self.logger = logging.getLogger(__name__)

    def load_operational_context(self, request: AnalyzeIncidentRequest) -> OperativeContext:
        context = OperativeContext(
            logs=load_logs(request.service_name),
            metrics=load_metrics(request.service_name),
            deployments=load_recent_deployments(request.service_name),
            service_metadata=load_service_metadata(request.service_name),
        )
        self.logger.info(
            "Loaded operational context for %s: logs=%s metrics=%s deployments=%s service_metadata=%s",
            request.service_name,
            bool(context.logs),
            bool(context.metrics),
            len(context.deployments),
            bool(context.service_metadata),
        )
        return context

    def build_query(self, request: AnalyzeIncidentRequest, context: OperativeContext) -> str:
        deployment_summary = None
        if context.deployments:
            latest = context.deployments[0]
            deployment_summary = ", ".join(latest.get("changes", []))
        return format_context_for_query(
            service_name=request.service_name,
            severity=request.severity,
            symptom=request.symptom,
            metric_name=request.metric_name,
            metric_value=request.metric_value,
            threshold_value=request.threshold_value,
            deployment_summary=deployment_summary,
        )

    def analyze(self, request: AnalyzeIncidentRequest) -> AnalyzeIncidentResponse:
        started_at = time.perf_counter()
        self.logger.info(
            "Starting analysis for incident_id=%s service=%s severity=%s",
            request.incident_id,
            request.service_name,
            request.severity,
        )
        context = self.load_operational_context(request)
        query = self.build_query(request, context)

        retrieved_chunks = self.knowledge_base.search(query, top_k=5, service_name=request.service_name)
        self.logger.info(
            "Retrieved %s knowledge chunks for service=%s",
            len(retrieved_chunks),
            request.service_name,
        )
        user_prompt = build_user_prompt(query, context, retrieved_chunks)
        self.logger.info(
            "Built LLM prompt for incident_id=%s query_chars=%s prompt_chars=%s",
            request.incident_id,
            len(query),
            len(user_prompt),
        )
        llm_started_at = time.perf_counter()
        llm_result = self.llm_client.generate_json(SYSTEM_PROMPT, user_prompt)
        self.logger.info(
            "LLM completed for incident_id=%s in %.2fs",
            request.incident_id,
            time.perf_counter() - llm_started_at,
        )
        recommendation = normalize_recommendation_payload(llm_result.parsed_json)
        recommendation.raw_model_output = {
            "query": query,
            "operational_context": context.model_dump(mode="json"),
            "retrieved_chunks": [chunk.model_dump(mode="json") for chunk in retrieved_chunks],
            "llm_response": llm_result.raw_text,
        }

        analysis_events = self._build_events(context, retrieved_chunks)
        return AnalyzeIncidentResponse(
            incident_id=request.incident_id,
            analysis_events=analysis_events,
            recommendation=recommendation,
        )

    def _build_events(self, context: OperativeContext, retrieved_chunks: Iterable[Any]) -> list[AnalysisEvent]:
        events = [
            AnalysisEvent(
                event_type=IncidentEventType.LOGS_FETCHED,
                message="Fetched mock logs for service",
                payload={"found": bool(context.logs)},
            ),
            AnalysisEvent(
                event_type=IncidentEventType.METRICS_FETCHED,
                message="Fetched mock metrics for service",
                payload={"found": bool(context.metrics)},
            ),
            AnalysisEvent(
                event_type=IncidentEventType.DEPLOYMENT_CHECKED,
                message="Reviewed recent deployment history",
                payload={"deployment_count": len(context.deployments)},
            ),
        ]
        retrieved_list = list(retrieved_chunks)
        if retrieved_list:
            docs = [chunk.title for chunk in retrieved_list]
            docs_by_type = {chunk.doc_type for chunk in retrieved_list}
            if "runbook" in docs_by_type:
                events.append(
                    AnalysisEvent(
                        event_type=IncidentEventType.RUNBOOK_RETRIEVED,
                        message="Retrieved relevant runbook guidance",
                        payload={"documents": docs},
                    )
                )
            if "rca" in docs_by_type:
                events.append(
                    AnalysisEvent(
                        event_type=IncidentEventType.RCA_RETRIEVED,
                        message="Retrieved similar RCA context",
                        payload={"documents": docs},
                    )
                )
        events.append(
            AnalysisEvent(
                event_type=IncidentEventType.RECOMMENDATION_GENERATED,
                message="Structured recommendation generated",
            )
        )
        return events
