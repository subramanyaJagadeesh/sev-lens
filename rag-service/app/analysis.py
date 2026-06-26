from __future__ import annotations

import logging
import time

from .knowledge_backend import KnowledgeBackend, create_knowledge_backend
from .llm_client import OpenAICompatibleLLMClient
from .schemas import AnalyzeIncidentRequest, AnalyzeIncidentResponse
from .tools import AnalysisToolchain
from .workflow import InvestigationWorkflow


class AnalysisEngine:
    def __init__(
        self,
        knowledge_backend: KnowledgeBackend | None = None,
        llm_client: OpenAICompatibleLLMClient | None = None,
        toolchain: AnalysisToolchain | None = None,
    ) -> None:
        self.knowledge_backend = knowledge_backend or create_knowledge_backend()
        self.toolchain = toolchain or AnalysisToolchain(knowledge_backend=self.knowledge_backend)
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

        workflow = InvestigationWorkflow(
            knowledge_backend=self.knowledge_backend,
            llm_client=self.llm_client,
            toolchain=self.toolchain,
            logger=self.logger,
        )
        analysis_events, recommendation, workflow_state = workflow.run(request)
        self.logger.info(
            "Finished analysis for incident_id=%s in %.2fs",
            request.incident_id,
            time.perf_counter() - started_at,
        )
        return AnalyzeIncidentResponse(
            incident_id=request.incident_id,
            analysis_events=analysis_events,
            recommendation=recommendation,
            workflow_state=workflow_state,
        )
