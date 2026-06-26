from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class RcaMemoryRecord:
    rca_id: str
    document_id: str
    title: str
    service_name: str
    severity: str
    symptoms: list[str] = field(default_factory=list)
    root_cause: str = ""
    resolution: str = ""
    prevention_items: list[str] = field(default_factory=list)
    related_errors: list[str] = field(default_factory=list)
    related_dependencies: list[str] = field(default_factory=list)
    incident_date: str = ""
    source: str | None = None
    tags: list[str] = field(default_factory=list)
    archived: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    helpful_count: int = 0
    not_helpful_count: int = 0
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RcaMemoryMatch:
    rca_id: str
    document_id: str
    title: str
    service_name: str
    severity: str
    score: float
    match_explanation: str
    matched_signals: list[str] = field(default_factory=list)
    symptoms: list[str] = field(default_factory=list)
    root_cause: str = ""
    resolution: str = ""
    prevention_items: list[str] = field(default_factory=list)
    related_errors: list[str] = field(default_factory=list)
    related_dependencies: list[str] = field(default_factory=list)
    incident_date: str = ""
    source: str | None = None
    helpful_count: int = 0
    not_helpful_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RcaFeedbackRecord:
    feedback_id: str
    rca_id: str
    incident_id: str
    analysis_run_id: str | None
    helpful: bool
    note: str | None
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
