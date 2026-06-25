from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from shared.contracts.incident_contracts import DecisionType, IncidentEventType, IncidentStatus


class IncidentCreateMockRequest(BaseModel):
    scenario: str = Field(min_length=1)


class IncidentDecisionRequest(BaseModel):
    decision: DecisionType
    note: str | None = None


class IncidentEventResponse(BaseModel):
    event_id: str
    incident_id: str
    event_type: IncidentEventType
    message: str
    payload: dict[str, Any] | None = None
    created_at: datetime
    sequence: int


class IncidentRecommendationResponse(BaseModel):
    summary: str | None = None
    evidence: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    confidence: str | None = None
    requires_human_approval: bool = True
    raw_model_output: dict[str, Any] | None = None
    created_at: datetime | None = None


class IncidentDecisionResponse(BaseModel):
    decision_id: str
    incident_id: str
    decision: DecisionType
    decided_by: str
    note: str | None = None
    created_at: datetime


class IncidentAnalysisRunResponse(BaseModel):
    analysis_run_id: str
    incident_id: str
    scenario_id: str
    scenario_type: str
    trigger_type: str
    status: str
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    analysis_latency_ms: int | None = None
    retrieved_document_count: int = 0
    expected_document_hit_rate: float = 0.0
    evidence_count: int = 0
    recommended_action_count: int = 0
    confidence_value: str | None = None
    human_decision_outcome: str | None = None
    expected_evidence_signals: list[str] = Field(default_factory=list)
    expected_recommendation_direction: str = ""
    recommendation: IncidentRecommendationResponse | None = None
    analysis_events: list[IncidentEventResponse] = Field(default_factory=list)


class IncidentSummaryResponse(BaseModel):
    incident_id: str
    service_name: str
    severity: str
    symptom: str
    metric_name: str | None = None
    metric_value: str | None = None
    threshold_value: str | None = None
    status: IncidentStatus
    created_at: datetime
    updated_at: datetime
    recommendation_status: str
    approval_status: str | None = None


class IncidentDetailResponse(BaseModel):
    incident: IncidentSummaryResponse
    events: list[IncidentEventResponse]
    recommendation: IncidentRecommendationResponse | None = None
    decision: IncidentDecisionResponse | None = None
    analysis_run: IncidentAnalysisRunResponse | None = None
    analysis_runs: list[IncidentAnalysisRunResponse] = Field(default_factory=list)


class IncidentResponse(BaseModel):
    incident_id: str
    service_name: str
    severity: str
    symptom: str
    metric_name: str | None = None
    metric_value: str | None = None
    threshold_value: str | None = None
    status: IncidentStatus
    created_at: datetime
    updated_at: datetime
    recommendation_status: str
    approval_status: str | None = None


class StreamEventResponse(BaseModel):
    incident_id: str
    event_type: IncidentEventType
    message: str
    created_at: datetime
    sequence: int
    payload: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    detail: str
