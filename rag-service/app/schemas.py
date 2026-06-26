from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from shared.contracts.incident_contracts import DecisionType, IncidentEventType, IncidentStatus


class AnalyzeIncidentRequest(BaseModel):
    incident_id: str = Field(min_length=1)
    scenario_id: str = Field(min_length=1)
    service_name: str = Field(min_length=1)
    severity: str = Field(min_length=1)
    symptom: str = Field(min_length=1)
    metric_name: str | None = None
    metric_value: str | None = None
    threshold_value: str | None = None


class AnalysisEvent(BaseModel):
    event_type: IncidentEventType
    message: str
    payload: dict[str, Any] | None = None


class InvestigationStepRecord(BaseModel):
    step_name: str
    event_type: IncidentEventType
    status: str
    message: str
    payload: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class InvestigationPlanRecord(BaseModel):
    iteration: int
    next_action: str
    reason: str
    query: str | None = None
    focus: str | None = None
    status: str = "success"
    error: str | None = None


class ToolResult(BaseModel):
    tool_name: str
    event_type: IncidentEventType
    status: str
    message: str
    payload: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None

    def to_analysis_event(self) -> AnalysisEvent:
        event_payload = dict(self.payload)
        event_payload.setdefault("tool_name", self.tool_name)
        event_payload.setdefault("status", self.status)
        if self.error is not None:
            event_payload.setdefault("error", self.error)
        return AnalysisEvent(event_type=self.event_type, message=self.message, payload=event_payload or None)


class RecommendationPayload(BaseModel):
    summary: str
    evidence: list[str]
    recommended_actions: list[str]
    confidence: str
    requires_human_approval: bool = True
    incident_summary: str | None = None
    symptoms: list[str] = Field(default_factory=list)
    risk_level: str | None = None
    hypotheses: list[dict[str, Any]] = Field(default_factory=list)
    source_documents: list[dict[str, Any]] = Field(default_factory=list)
    similar_rcas: list[dict[str, Any]] = Field(default_factory=list)
    unsupported_areas: list[str] = Field(default_factory=list)
    action_evidence_links: list[dict[str, Any]] = Field(default_factory=list)
    raw_model_output: dict[str, Any] | None = None


class AnalyzeIncidentResponse(BaseModel):
    incident_id: str
    analysis_events: list[AnalysisEvent]
    recommendation: RecommendationPayload
    workflow_state: dict[str, Any] | None = None


class AnalysisContextBundle(BaseModel):
    context: OperativeContext
    tool_results: list[ToolResult] = Field(default_factory=list)
    tool_events: list[AnalysisEvent] = Field(default_factory=list)


class OperativeContext(BaseModel):
    log_evidence: list["LogEvidenceRecord"] = Field(default_factory=list)
    metrics: dict[str, Any] | None = None
    deployments: list[dict[str, Any]] = Field(default_factory=list)
    service_metadata: dict[str, Any] | None = None
    runbook_chunks: list["RetrievedDocumentChunk"] = Field(default_factory=list)
    rca_chunks: list["RetrievedDocumentChunk"] = Field(default_factory=list)
    rca_matches: list[dict[str, Any]] = Field(default_factory=list)
    tool_results: list[ToolResult] = Field(default_factory=list)


class InvestigationWorkflowState(BaseModel):
    incident_id: str
    scenario_id: str
    service_name: str
    severity: str
    symptom: str
    classification: dict[str, Any] = Field(default_factory=dict)
    query: str = ""
    context: OperativeContext
    hypotheses: list[dict[str, Any]] = Field(default_factory=list)
    verification: list[dict[str, Any]] = Field(default_factory=list)
    planner_decisions: list[InvestigationPlanRecord] = Field(default_factory=list)
    iteration_count: int = 0
    next_action: str = ""
    context_collected: bool = False
    knowledge_retrieved: bool = False
    rca_retrieved: bool = False
    step_records: list[InvestigationStepRecord] = Field(default_factory=list)
    fallback_used: bool = False
    notes: list[str] = Field(default_factory=list)


class RetrievedDocumentChunk(BaseModel):
    source: str
    title: str
    doc_type: str
    service: str | None = None
    tags: list[str] = Field(default_factory=list)
    chunk_index: int
    text: str
    score: float


class DocumentRecord(BaseModel):
    source: str
    title: str
    doc_type: str
    service: str | None = None
    tags: list[str] = Field(default_factory=list)
    text: str


class LogEvidenceRecord(BaseModel):
    scenario_id: str
    service_name: str
    time_window: str
    summary: str
    top_errors: list[dict[str, Any]] = Field(default_factory=list)
    sample_messages: list[str] = Field(default_factory=list)
    source: str
    score: float = 1.0


class KnowledgeDocumentCreateRequest(BaseModel):
    document_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    doc_type: str = Field(min_length=1)
    content: str = Field(min_length=1)
    service: str | None = None
    tags: list[str] = Field(default_factory=list)
    source: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeDocumentUpdateRequest(BaseModel):
    title: str | None = None
    doc_type: str | None = None
    content: str | None = None
    service: str | None = None
    tags: list[str] | None = None
    source: str | None = None
    archived: bool | None = None
    metadata: dict[str, Any] | None = None


class KnowledgeDocumentResponse(BaseModel):
    document_id: str
    title: str
    doc_type: str
    content: str
    service: str | None = None
    tags: list[str] = Field(default_factory=list)
    source: str | None = None
    archived: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str | None = None
    updated_at: str | None = None
    indexed_at: str | None = None
    chunk_count: int = 0
    chunk_ids: list[str] = Field(default_factory=list)


class KnowledgeChunkResponse(BaseModel):
    chunk_id: str
    document_id: str
    title: str
    doc_type: str
    text: str
    chunk_index: int
    service: str | None = None
    tags: list[str] = Field(default_factory=list)
    source: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeDocumentDetailResponse(BaseModel):
    document: KnowledgeDocumentResponse
    chunks: list[KnowledgeChunkResponse] = Field(default_factory=list)


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=8, ge=1, le=50)
    service_name: str | None = None
    doc_types: list[str] | None = None
    tags: list[str] | None = None


class KnowledgeSearchResult(BaseModel):
    document_id: str
    title: str
    doc_type: str
    text: str
    score: float
    service: str | None = None
    tags: list[str] = Field(default_factory=list)
    source: str | None = None
    chunk_index: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class RcaMemoryResponse(BaseModel):
    rca_id: str
    document_id: str
    title: str
    service_name: str
    severity: str
    symptoms: list[str] = Field(default_factory=list)
    root_cause: str = ""
    resolution: str = ""
    prevention_items: list[str] = Field(default_factory=list)
    related_errors: list[str] = Field(default_factory=list)
    related_dependencies: list[str] = Field(default_factory=list)
    incident_date: str = ""
    source: str | None = None
    tags: list[str] = Field(default_factory=list)
    archived: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    helpful_count: int = 0
    not_helpful_count: int = 0
    created_at: str = ""
    updated_at: str = ""


class RcaMemoryMatchResponse(BaseModel):
    rca_id: str
    document_id: str
    title: str
    service_name: str
    severity: str
    score: float
    match_explanation: str
    matched_signals: list[str] = Field(default_factory=list)
    symptoms: list[str] = Field(default_factory=list)
    root_cause: str = ""
    resolution: str = ""
    prevention_items: list[str] = Field(default_factory=list)
    related_errors: list[str] = Field(default_factory=list)
    related_dependencies: list[str] = Field(default_factory=list)
    incident_date: str = ""
    source: str | None = None
    helpful_count: int = 0
    not_helpful_count: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class RcaMemoryFeedbackRequest(BaseModel):
    incident_id: str = Field(min_length=1)
    rca_id: str = Field(min_length=1)
    helpful: bool
    analysis_run_id: str | None = None
    note: str | None = None


class RcaMemoryFeedbackResponse(BaseModel):
    feedback_id: str
    rca_id: str
    incident_id: str
    analysis_run_id: str | None = None
    helpful: bool
    note: str | None = None
    created_at: str


class RcaMemorySearchRequest(BaseModel):
    service_name: str = Field(min_length=1)
    severity: str = Field(min_length=1)
    symptom: str = Field(min_length=1)
    metric_name: str | None = None
    metric_value: str | None = None
    threshold_value: str | None = None
    top_k: int = Field(default=5, ge=1, le=20)
    tags: list[str] | None = None


class RcaMemoryDetailResponse(BaseModel):
    memory: RcaMemoryResponse
    feedback: list[RcaMemoryFeedbackResponse] = Field(default_factory=list)
