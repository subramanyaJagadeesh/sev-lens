from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
import json
from typing import Any


@dataclass(frozen=True)
class AnalysisRequestEnvelope:
    incident_id: str
    scenario_id: str
    service_name: str
    severity: str
    symptom: str
    metric_name: str
    metric_value: str
    threshold_value: str
    created_at: datetime
    correlation_id: str
    source: str = "incident-api"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["created_at"] = self.created_at.isoformat()
        return payload

    def to_stream_message(self) -> dict[str, str]:
        return {
            "payload": json.dumps(self.to_dict()),
            "incident_id": self.incident_id,
            "scenario_id": self.scenario_id,
            "correlation_id": self.correlation_id,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AnalysisRequestEnvelope":
        return cls(
            incident_id=payload["incident_id"],
            scenario_id=payload["scenario_id"],
            service_name=payload["service_name"],
            severity=payload["severity"],
            symptom=payload["symptom"],
            metric_name=payload["metric_name"],
            metric_value=payload["metric_value"],
            threshold_value=payload["threshold_value"],
            created_at=datetime.fromisoformat(payload["created_at"]),
            correlation_id=payload["correlation_id"],
            source=payload.get("source", "incident-api"),
        )

    @classmethod
    def from_stream_message(cls, payload: dict[str, Any]) -> "AnalysisRequestEnvelope":
        raw_payload = payload.get("payload")
        if isinstance(raw_payload, str):
            return cls.from_dict(json.loads(raw_payload))
        return cls.from_dict(payload)


@dataclass(frozen=True)
class AnalysisResultEnvelope:
    incident_id: str
    analysis_status: str
    recommendation: dict[str, Any] | None = None
    analysis_events: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None
    workflow_state: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_stream_message(self) -> dict[str, str]:
        return {
            "payload": json.dumps(self.to_dict()),
            "incident_id": self.incident_id,
            "analysis_status": self.analysis_status,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AnalysisResultEnvelope":
        return cls(
            incident_id=payload["incident_id"],
            analysis_status=payload["analysis_status"],
            recommendation=payload.get("recommendation"),
            analysis_events=payload.get("analysis_events", []),
            error=payload.get("error"),
            workflow_state=payload.get("workflow_state"),
        )

    @classmethod
    def from_stream_message(cls, payload: dict[str, Any]) -> "AnalysisResultEnvelope":
        raw_payload = payload.get("payload")
        if isinstance(raw_payload, str):
            return cls.from_dict(json.loads(raw_payload))
        return cls.from_dict(payload)
