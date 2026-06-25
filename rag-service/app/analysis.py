from __future__ import annotations

import logging
import time

from shared.contracts.incident_contracts import IncidentEventType

from .llm_client import OpenAICompatibleLLMClient
from .normalization import normalize_recommendation_payload
from .prompts import SYSTEM_PROMPT, build_user_prompt
from .retrieval import KnowledgeBase
from .schemas import AnalyzeIncidentRequest, AnalyzeIncidentResponse, AnalysisEvent
from .tools import AnalysisToolchain


class AnalysisEngine:
    def __init__(
        self,
        knowledge_base: KnowledgeBase | None = None,
        llm_client: OpenAICompatibleLLMClient | None = None,
        toolchain: AnalysisToolchain | None = None,
    ) -> None:
        self.knowledge_base = knowledge_base or KnowledgeBase()
        self.toolchain = toolchain or AnalysisToolchain(knowledge_base=self.knowledge_base)
        self.llm_client = llm_client or OpenAICompatibleLLMClient()
        self.logger = logging.getLogger(__name__)

    def ensure_log_store_ready(self) -> None:
        self.toolchain.ensure_ready()

    def analyze(self, request: AnalyzeIncidentRequest) -> AnalyzeIncidentResponse:
        started_at = time.perf_counter()
        self.logger.info(
            "Starting analysis for incident_id=%s service=%s severity=%s",
            request.incident_id,
            request.service_name,
            request.severity,
        )

        base_bundle = self.toolchain.collect_context(request)
        query = self.toolchain.build_reference_query(request, base_bundle)
        bundle = self.toolchain.retrieve_reference_material(request, query, base_bundle)

        retrieved_chunks = [*bundle.context.runbook_chunks, *bundle.context.rca_chunks]
        self.logger.info(
            "Collected %s tool results and %s reference chunks for service=%s",
            len(bundle.tool_results),
            len(retrieved_chunks),
            request.service_name,
        )

        user_prompt = build_user_prompt(query, bundle.context, retrieved_chunks)
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
            "operational_context": bundle.context.model_dump(mode="json"),
            "tool_results": [tool_result.model_dump(mode="json") for tool_result in bundle.tool_results],
            "retrieved_chunks": [chunk.model_dump(mode="json") for chunk in retrieved_chunks],
            "llm_response": llm_result.raw_text,
        }

        analysis_events = [
            *bundle.tool_events,
            AnalysisEvent(
                event_type=IncidentEventType.RECOMMENDATION_GENERATED,
                message="Structured recommendation generated",
            ),
        ]
        self.logger.info(
            "Finished analysis for incident_id=%s in %.2fs",
            request.incident_id,
            time.perf_counter() - started_at,
        )
        return AnalyzeIncidentResponse(
            incident_id=request.incident_id,
            analysis_events=analysis_events,
            recommendation=recommendation,
        )
