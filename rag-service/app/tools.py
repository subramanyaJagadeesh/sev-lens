from __future__ import annotations

from typing import Any

from shared.contracts.incident_contracts import IncidentEventType

from .data_loader import load_metrics, load_recent_deployments, load_service_metadata
from .knowledge_backend import KnowledgeBackend, create_knowledge_backend, format_context_for_query
from .opensearch_store import OpenSearchLogStore
from .schemas import (
    AnalyzeIncidentRequest,
    AnalysisContextBundle,
    AnalysisEvent,
    OperativeContext,
    RetrievedDocumentChunk,
    ToolResult,
)


def _to_retrieved_chunk(document: Any) -> RetrievedDocumentChunk:
    if isinstance(document, RetrievedDocumentChunk):
        return document
    return RetrievedDocumentChunk.model_validate(
        {
            "source": getattr(document, "source", None) or "",
            "title": getattr(document, "title", ""),
            "doc_type": getattr(document, "doc_type", ""),
            "service": getattr(document, "service", None),
            "tags": list(getattr(document, "tags", [])),
            "chunk_index": int(getattr(document, "chunk_index", 0)),
            "text": getattr(document, "text", ""),
            "score": float(getattr(document, "score", 0.0)),
        }
    )


def _serialize_chunks(chunks: list[Any]) -> list[dict[str, Any]]:
    return [_to_retrieved_chunk(chunk).model_dump(mode="json") for chunk in chunks]


class LogSearchTool:
    def __init__(self, log_store: OpenSearchLogStore | None = None) -> None:
        self.log_store = log_store or OpenSearchLogStore()

    def run(self, request: AnalyzeIncidentRequest) -> ToolResult:
        try:
            evidence = self.log_store.search(service_name=request.service_name, scenario_id=request.scenario_id)
            return ToolResult(
                tool_name="log_search",
                event_type=IncidentEventType.LOGS_FETCHED,
                status="success",
                message="Fetched summarized log evidence from OpenSearch",
                payload={
                    "found": bool(evidence),
                    "evidence_count": len(evidence),
                    "source": "opensearch",
                    "log_evidence": [item.model_dump(mode="json") for item in evidence],
                },
            )
        except Exception as exc:  # noqa: BLE001
            return ToolResult(
                tool_name="log_search",
                event_type=IncidentEventType.LOGS_FETCHED,
                status="failed",
                message="Log search failed but analysis will continue with partial context",
                payload={"found": False, "evidence_count": 0, "source": "opensearch"},
                error=str(exc),
            )


class MetricsLookupTool:
    def run(self, request: AnalyzeIncidentRequest) -> ToolResult:
        try:
            metrics = load_metrics(request.service_name)
            return ToolResult(
                tool_name="metrics_lookup",
                event_type=IncidentEventType.METRICS_FETCHED,
                status="success",
                message="Fetched mock metrics for service",
                payload={"found": bool(metrics), "metrics": metrics},
            )
        except Exception as exc:  # noqa: BLE001
            return ToolResult(
                tool_name="metrics_lookup",
                event_type=IncidentEventType.METRICS_FETCHED,
                status="failed",
                message="Metrics lookup failed but analysis will continue with partial context",
                payload={"found": False, "metrics": None},
                error=str(exc),
            )


class DeploymentLookupTool:
    def run(self, request: AnalyzeIncidentRequest) -> ToolResult:
        try:
            deployments = load_recent_deployments(request.service_name)
            latest_changes: list[str] = []
            if deployments:
                latest_changes = list(deployments[0].get("changes", []))
            return ToolResult(
                tool_name="deployment_lookup",
                event_type=IncidentEventType.DEPLOYMENT_CHECKED,
                status="success",
                message="Reviewed recent deployment history",
                payload={
                    "deployment_count": len(deployments),
                    "deployments": deployments,
                    "latest_changes": latest_changes,
                },
            )
        except Exception as exc:  # noqa: BLE001
            return ToolResult(
                tool_name="deployment_lookup",
                event_type=IncidentEventType.DEPLOYMENT_CHECKED,
                status="failed",
                message="Deployment lookup failed but analysis will continue with partial context",
                payload={"deployment_count": 0, "deployments": [], "latest_changes": []},
                error=str(exc),
            )


class ServiceCatalogLookupTool:
    def run(self, request: AnalyzeIncidentRequest) -> ToolResult:
        try:
            service_metadata = load_service_metadata(request.service_name)
            return ToolResult(
                tool_name="service_catalog_lookup",
                event_type=IncidentEventType.SEVERITY_CLASSIFIED,
                status="success",
                message="Loaded service catalog metadata",
                payload={"found": bool(service_metadata), "service_metadata": service_metadata},
            )
        except Exception as exc:  # noqa: BLE001
            return ToolResult(
                tool_name="service_catalog_lookup",
                event_type=IncidentEventType.SEVERITY_CLASSIFIED,
                status="failed",
                message="Service catalog lookup failed but analysis will continue with partial context",
                payload={"found": False, "service_metadata": None},
                error=str(exc),
            )


class RunbookRetrievalTool:
    def __init__(self, knowledge_backend: KnowledgeBackend | None = None) -> None:
        self.knowledge_backend = knowledge_backend or create_knowledge_backend()

    def run(self, request: AnalyzeIncidentRequest, query: str) -> ToolResult:
        try:
            documents = self.knowledge_backend.retrieve_by_document_type(
                document_types=["runbook"],
                query=query,
                top_k=3,
                service_name=request.service_name,
            )
            retrieved_documents = [_to_retrieved_chunk(document) for document in documents]
            return ToolResult(
                tool_name="runbook_retrieval",
                event_type=IncidentEventType.RUNBOOK_RETRIEVED,
                status="success",
                message="Retrieved relevant runbook guidance",
                payload={"documents": _serialize_chunks(retrieved_documents), "document_count": len(retrieved_documents)},
            )
        except Exception as exc:  # noqa: BLE001
            return ToolResult(
                tool_name="runbook_retrieval",
                event_type=IncidentEventType.RUNBOOK_RETRIEVED,
                status="failed",
                message="Runbook retrieval failed but analysis will continue with partial context",
                payload={"documents": [], "document_count": 0},
                error=str(exc),
            )


class RcaRetrievalTool:
    def __init__(self, knowledge_backend: KnowledgeBackend | None = None) -> None:
        self.knowledge_backend = knowledge_backend or create_knowledge_backend()

    def run(self, request: AnalyzeIncidentRequest, query: str) -> ToolResult:
        try:
            matches = self.knowledge_backend.search_rca_memories(
                incident_context={
                    "service_name": request.service_name,
                    "severity": request.severity,
                    "symptom": request.symptom,
                    "metric_name": request.metric_name,
                    "metric_value": request.metric_value,
                    "threshold_value": request.threshold_value,
                },
                top_k=3,
            )
            retrieved_documents = [
                RetrievedDocumentChunk(
                    source=match.source or match.document_id,
                    title=match.title,
                    doc_type="rca",
                    service=match.service_name,
                    tags=list(match.metadata.get("tags", [])) if isinstance(match.metadata, dict) else [],
                    chunk_index=int(match.metadata.get("chunk_index", 0)) if isinstance(match.metadata, dict) else 0,
                    text=(
                        f"{match.match_explanation}. Root cause: {match.root_cause}. "
                        f"Resolution: {match.resolution}"
                    ),
                    score=match.score,
                )
                for match in matches
            ]
            return ToolResult(
                tool_name="rca_retrieval",
                event_type=IncidentEventType.RCA_RETRIEVED,
                status="success",
                message="Retrieved similar RCA context",
                payload={
                    "documents": _serialize_chunks(retrieved_documents),
                    "matches": [match.to_dict() for match in matches],
                    "document_count": len(retrieved_documents),
                },
            )
        except Exception as exc:  # noqa: BLE001
            return ToolResult(
                tool_name="rca_retrieval",
                event_type=IncidentEventType.RCA_RETRIEVED,
                status="failed",
                message="RCA retrieval failed but analysis will continue with partial context",
                payload={"documents": [], "matches": [], "document_count": 0},
                error=str(exc),
            )


class AnalysisToolchain:
    def __init__(
        self,
        knowledge_backend: KnowledgeBackend | None = None,
        log_store: OpenSearchLogStore | None = None,
    ) -> None:
        self.knowledge_backend = knowledge_backend or create_knowledge_backend()
        self.log_store = log_store or OpenSearchLogStore()
        self.log_search = LogSearchTool(self.log_store)
        self.metrics_lookup = MetricsLookupTool()
        self.deployment_lookup = DeploymentLookupTool()
        self.service_catalog_lookup = ServiceCatalogLookupTool()
        self.runbook_retrieval = RunbookRetrievalTool(self.knowledge_backend)
        self.rca_retrieval = RcaRetrievalTool(self.knowledge_backend)

    def ensure_ready(self) -> None:
        self.log_store.ensure_seeded()

    def collect_context(self, request: AnalyzeIncidentRequest) -> AnalysisContextBundle:
        tool_results: list[ToolResult] = []
        tool_events: list[AnalysisEvent] = []

        for tool in (
            self.log_search,
            self.metrics_lookup,
            self.deployment_lookup,
            self.service_catalog_lookup,
        ):
            result = tool.run(request)
            tool_results.append(result)
            tool_events.append(result.to_analysis_event())

        log_evidence = self._extract_log_evidence(tool_results[0])
        metrics = self._extract_metrics(tool_results[1])
        deployments = self._extract_deployments(tool_results[2])
        service_metadata = self._extract_service_metadata(tool_results[3])

        operational_context = OperativeContext(
            log_evidence=log_evidence,
            metrics=metrics,
            deployments=deployments,
            service_metadata=service_metadata,
            tool_results=tool_results,
        )
        bundle = AnalysisContextBundle(
            context=operational_context,
            tool_results=tool_results,
            tool_events=tool_events,
        )
        return bundle

    def retrieve_reference_material(self, request: AnalyzeIncidentRequest, query: str, bundle: AnalysisContextBundle) -> AnalysisContextBundle:
        runbook_result = self.runbook_retrieval.run(request, query)
        bundle.tool_results.append(runbook_result)
        bundle.tool_events.append(runbook_result.to_analysis_event())

        rca_result = self.rca_retrieval.run(request, query)
        bundle.tool_results.append(rca_result)
        bundle.tool_events.append(rca_result.to_analysis_event())

        runbook_docs = self._extract_documents(runbook_result, "documents")
        rca_docs = self._extract_documents(rca_result, "documents")
        bundle.context.runbook_chunks = [RetrievedDocumentChunk.model_validate(chunk) for chunk in runbook_docs]
        bundle.context.rca_chunks = [RetrievedDocumentChunk.model_validate(chunk) for chunk in rca_docs]
        rca_matches = rca_result.payload.get("matches")
        bundle.context.rca_matches = list(rca_matches) if isinstance(rca_matches, list) else []
        bundle.context.tool_results = bundle.tool_results
        return bundle

    def build_reference_query(self, request: AnalyzeIncidentRequest, bundle: AnalysisContextBundle) -> str:
        deployment_summary = None
        if bundle.context.deployments:
            latest = bundle.context.deployments[0]
            deployment_summary = ", ".join(latest.get("changes", []))

        service_profile_summary = None
        if bundle.context.service_metadata:
            metadata = bundle.context.service_metadata
            dependencies = metadata.get("dependencies")
            dependency_summary = ", ".join(dependencies) if isinstance(dependencies, list) else None
            service_profile_summary = ", ".join(
                part
                for part in (
                    f"Owner team: {metadata.get('owner_team')}" if metadata.get("owner_team") else None,
                    f"Criticality: {metadata.get('criticality')}" if metadata.get("criticality") else None,
                    f"Dependencies: {dependency_summary}" if dependency_summary else None,
                )
                if part
            )

        return format_context_for_query(
            service_name=request.service_name,
            severity=request.severity,
            symptom=request.symptom,
            metric_name=request.metric_name,
            metric_value=request.metric_value,
            threshold_value=request.threshold_value,
            deployment_summary=deployment_summary,
            service_profile_summary=service_profile_summary,
        )

    def _extract_log_evidence(self, result: ToolResult) -> list[dict[str, Any]]:
        raw_evidence = result.payload.get("log_evidence", [])
        return list(raw_evidence) if isinstance(raw_evidence, list) else []

    def _extract_metrics(self, result: ToolResult) -> dict[str, Any] | None:
        metrics = result.payload.get("metrics")
        return metrics if isinstance(metrics, dict) else None

    def _extract_deployments(self, result: ToolResult) -> list[dict[str, Any]]:
        deployments = result.payload.get("deployments")
        return list(deployments) if isinstance(deployments, list) else []

    def _extract_service_metadata(self, result: ToolResult) -> dict[str, Any] | None:
        metadata = result.payload.get("service_metadata")
        return metadata if isinstance(metadata, dict) else None

    def _extract_documents(self, result: ToolResult, key: str) -> list[dict[str, Any]]:
        documents = result.payload.get(key)
        return list(documents) if isinstance(documents, list) else []
