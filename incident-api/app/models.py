from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from shared.contracts.incident_contracts import DecisionType, IncidentEventType, IncidentStatus


@dataclass(frozen=True)
class IncidentRecord:
    id: UUID
    service_name: str
    severity: str
    symptom: str
    metric_name: str | None = None
    metric_value: str | None = None
    threshold_value: str | None = None
    status: IncidentStatus = IncidentStatus.CREATED
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class IncidentEventRecord:
    id: UUID
    incident_id: UUID
    event_type: IncidentEventType
    message: str
    payload: dict[str, Any] | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class IncidentRecommendationRecord:
    id: UUID
    incident_id: UUID
    summary: str
    evidence: list[str]
    recommended_actions: list[str]
    confidence: str
    requires_human_approval: bool = True
    incident_summary: str | None = None
    symptoms: list[str] = field(default_factory=list)
    risk_level: str | None = None
    hypotheses: list[dict[str, Any]] = field(default_factory=list)
    source_documents: list[dict[str, Any]] = field(default_factory=list)
    similar_rcas: list[dict[str, Any]] = field(default_factory=list)
    unsupported_areas: list[str] = field(default_factory=list)
    action_evidence_links: list[dict[str, Any]] = field(default_factory=list)
    raw_model_output: dict[str, Any] | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class IncidentDecisionRecord:
    id: UUID
    incident_id: UUID
    decision: DecisionType
    decided_by: str
    note: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
