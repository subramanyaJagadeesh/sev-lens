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
    raw_model_output: dict[str, Any] | None = None


class AnalyzeIncidentResponse(BaseModel):
    incident_id: str
    analysis_events: list[AnalysisEvent]
    recommendation: RecommendationPayload


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
    tool_results: list[ToolResult] = Field(default_factory=list)


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
