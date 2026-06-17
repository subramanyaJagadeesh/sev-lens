from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from shared.contracts.incident_contracts import DecisionType, IncidentEventType, IncidentStatus


class AnalyzeIncidentRequest(BaseModel):
    incident_id: str = Field(min_length=1)
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


class OperativeContext(BaseModel):
    logs: dict[str, Any] | None = None
    metrics: dict[str, Any] | None = None
    deployments: list[dict[str, Any]] = Field(default_factory=list)
    service_metadata: dict[str, Any] | None = None


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
