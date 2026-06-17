from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from shared.contracts.incident_contracts import DecisionType, IncidentEventType, IncidentStatus

from .config import SCENARIO_PATH
from .events import EventBus
from .repository import IncidentRepository
from .rag_client import request_recommendation


class IncidentService:
    def __init__(self, repository: IncidentRepository, event_bus: EventBus) -> None:
        self.repository = repository
        self.event_bus = event_bus

    def _load_scenario(self, scenario_id: str) -> dict[str, Any]:
        # Stage 2 only supports the seeded scenario from the shared mock-data folder.
        with SCENARIO_PATH.open("r", encoding="utf-8") as file_handle:
            scenario = json.load(file_handle)
        if scenario["scenario_id"] != scenario_id:
            raise KeyError(scenario_id)
        return scenario

    def create_mock_incident(self, scenario_id: str) -> dict[str, Any]:
        # Create the incident record, then emit the initial audit trail entries.
        scenario = self._load_scenario(scenario_id)
        incident = self.repository.create_incident(scenario)
        created_event = self.repository.add_event(
            incident["incident_id"],
            IncidentEventType.INCIDENT_CREATED,
            f"Incident created for {incident['service_name']}",
            payload={"scenario": scenario_id},
        )
        self.repository.update_incident_status(incident["incident_id"], IncidentStatus.ANALYZING)
        analysis_started = self.repository.add_event(
            incident["incident_id"],
            IncidentEventType.ANALYSIS_STARTED,
            "Analysis started for mock incident",
            payload={"scenario": scenario_id},
        )
        recommendation = None
        analysis_events: list[dict[str, Any]] = []
        analysis_request = {
            "incident_id": incident["incident_id"],
            "service_name": scenario["service_name"],
            "severity": scenario["severity"],
            "symptom": scenario["symptom"],
            "metric_name": scenario["metric_name"],
            "metric_value": scenario["metric_value"],
            "threshold_value": scenario["threshold_value"],
        }
        try:
            analysis_response = request_recommendation(analysis_request)
            recommendation = self.repository.save_recommendation(incident["incident_id"], analysis_response.recommendation)
            for event in analysis_response.analysis_events:
                saved_event = self.repository.add_event(
                    incident["incident_id"],
                    IncidentEventType(event["event_type"]),
                    event["message"],
                    payload=event.get("payload"),
                )
                analysis_events.append(saved_event)
            self.repository.update_incident_status(incident["incident_id"], IncidentStatus.RECOMMENDATION_READY)
        except Exception as exc:  # pragma: no cover - manual integration path
            analysis_events = [
                self.repository.add_event(
                    incident["incident_id"],
                    IncidentEventType.ANALYSIS_FAILED,
                    "Analysis failed while calling the RAG service",
                    payload={"error": str(exc)},
                )
            ]
            self.repository.update_incident_status(incident["incident_id"], IncidentStatus.FAILED)
        incident = self.repository.get_incident(incident["incident_id"])
        return {
            # We return both the current incident snapshot and the timeline events that were written.
            "incident": incident,
            "events": [created_event, analysis_started, *analysis_events],
            "recommendation": recommendation or self.repository.get_recommendation(incident["incident_id"]),
            "decision": self.repository.get_decision(incident["incident_id"]),
        }

    def list_incidents(self) -> list[dict[str, Any]]:
        return self.repository.list_incidents()

    def get_incident_detail(self, incident_id: str) -> dict[str, Any] | None:
        # The UI needs a single payload that contains all incident context in one request.
        incident = self.repository.get_incident(incident_id)
        if incident is None:
            return None
        return {
            "incident": incident,
            "events": self.repository.get_events(incident_id),
            "recommendation": self.repository.get_recommendation(incident_id),
            "decision": self.repository.get_decision(incident_id),
        }

    def record_decision(self, incident_id: str, decision: DecisionType, note: str | None = None) -> dict[str, Any] | None:
        # Decisions are stored under a hardcoded demo user so Stage 2 stays simple.
        incident = self.repository.get_incident(incident_id)
        if incident is None:
            return None
        saved_decision = self.repository.save_decision(incident_id, decision, "demo-user", note)
        # Each decision maps to a terminal incident status.
        status_by_decision = {
            DecisionType.APPROVE: IncidentStatus.APPROVED,
            DecisionType.REJECT: IncidentStatus.REJECTED,
            DecisionType.ESCALATE: IncidentStatus.ESCALATED,
        }
        updated_incident = self.repository.update_incident_status(incident_id, status_by_decision[decision])
        # We also record the human action as an audit event for replay and traceability.
        event_type_by_decision = {
            DecisionType.APPROVE: IncidentEventType.HUMAN_APPROVED,
            DecisionType.REJECT: IncidentEventType.HUMAN_REJECTED,
            DecisionType.ESCALATE: IncidentEventType.HUMAN_ESCALATED,
        }
        decision_event = self.repository.add_event(
            incident_id,
            event_type_by_decision[decision],
            f"Human decision recorded: {decision.value}",
            payload={"decision": decision.value, "decided_by": "demo-user", "note": note},
        )
        return {
            "decision": saved_decision,
            "incident": updated_incident,
            "event": decision_event,
        }
