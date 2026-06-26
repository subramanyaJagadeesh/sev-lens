from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from datetime import datetime, timezone

from shared.contracts.analysis_contracts import AnalysisRequestEnvelope, AnalysisResultEnvelope
from shared.contracts.incident_contracts import DecisionType, IncidentEventType, IncidentStatus

from .events import EventBus
from .repository import IncidentRepository
from .scenarios import MOCK_INCIDENT_SCENARIOS
from .rag_client import request_recommendation


class IncidentService:
    def __init__(self, repository: IncidentRepository, event_bus: EventBus, sync_fallback_enabled: bool | None = None) -> None:
        self.repository = repository
        self.event_bus = event_bus
        self.sync_fallback_enabled = (
            sync_fallback_enabled
            if sync_fallback_enabled is not None
            else os.getenv("SEVLENS_SYNC_ANALYSIS_FALLBACK", "false").lower() in {"1", "true", "yes"}
        )

    def _load_scenario(self, scenario_id: str) -> dict[str, Any]:
        # Stage 4 supports the seeded scenario catalog from the shared registry.
        scenario_record = MOCK_INCIDENT_SCENARIOS.get(scenario_id)
        if scenario_record is None:
            raise KeyError(scenario_id)
        scenario_path = Path(__file__).resolve().parents[2] / str(scenario_record["scenario_path"])
        with scenario_path.open("r", encoding="utf-8") as file_handle:
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
        analysis_request = self._build_analysis_request(incident, scenario_id)

        recommendation = None
        analysis_events: list[dict[str, Any]] = []
        if self.sync_fallback_enabled:
            self.repository.update_incident_status(incident["incident_id"], IncidentStatus.ANALYZING)
            latest_run = self.repository.create_analysis_run(incident["incident_id"], scenario, "mock-create-sync")
            analysis_started_at = self._utc_now()
            self.repository.update_analysis_run(
                latest_run["analysis_run_id"],
                status=IncidentStatus.ANALYZING.value,
                started_at=analysis_started_at.isoformat(),
            )
            analysis_started = self.repository.add_event(
                incident["incident_id"],
                IncidentEventType.ANALYSIS_STARTED,
                "Analysis started for mock incident",
                payload={"scenario": scenario_id},
            )
            analysis_request_payload = analysis_request.to_dict()
            try:
                analysis_response = request_recommendation(analysis_request_payload)
                recommendation = self.repository.save_recommendation(
                    incident["incident_id"], analysis_response.recommendation
                )
                for event in analysis_response.analysis_events:
                    saved_event = self.repository.add_event(
                        incident["incident_id"],
                        IncidentEventType(event["event_type"]),
                        event["message"],
                        payload=event.get("payload"),
                    )
                    analysis_events.append(saved_event)
                self.repository.update_incident_status(incident["incident_id"], IncidentStatus.RECOMMENDATION_READY)
                self._update_analysis_run_from_recommendation(
                    incident["incident_id"],
                    scenario,
                    analysis_response.recommendation,
                    IncidentStatus.RECOMMENDATION_READY.value,
                    completed_at=self._utc_now(),
                    started_at=analysis_started_at,
                )
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
                self.repository.update_analysis_run(
                    self.repository.get_latest_analysis_run(incident["incident_id"])["analysis_run_id"],
                    status=IncidentStatus.FAILED.value,
                    completed_at=self._utc_now().isoformat(),
                    analysis_latency_ms=self._analysis_latency_ms(
                        analysis_started_at,
                        self._utc_now(),
                        incident["created_at"],
                    ),
                )
            incident = self.repository.get_incident(incident["incident_id"])
            return {
                # We return both the current incident snapshot and the timeline events that were written.
                "incident": incident,
                "events": [created_event, analysis_started, *analysis_events],
                "recommendation": recommendation or self.repository.get_recommendation(incident["incident_id"]),
                "decision": self.repository.get_decision(incident["incident_id"]),
                "analysis_request": None,
            }

        self.repository.update_incident_status(incident["incident_id"], IncidentStatus.QUEUED)
        self.repository.create_analysis_run(incident["incident_id"], scenario, "mock-create")
        queued_event = self.repository.add_event(
            incident["incident_id"],
            IncidentEventType.ANALYSIS_QUEUED,
            "Analysis job queued for async processing",
            payload={"scenario": scenario_id, "correlation_id": incident["incident_id"]},
        )
        incident = self.repository.get_incident(incident["incident_id"])
        return {
            # We return both the current incident snapshot and the timeline events that were written.
            "incident": incident,
            "events": [created_event, queued_event],
            "recommendation": recommendation,
            "decision": self.repository.get_decision(incident["incident_id"]),
            "analysis_request": analysis_request,
        }

    def retry_analysis(self, incident_id: str) -> dict[str, Any] | None:
        # Retry reuses the existing incident record and its original scenario context.
        incident = self.repository.get_incident(incident_id)
        if incident is None:
            return None
        if incident["status"] != IncidentStatus.FAILED:
            raise ValueError("Incident must be failed before retrying analysis")

        scenario_id = self._get_scenario_id_for_incident(incident_id)
        analysis_request = self._build_analysis_request(incident, scenario_id)
        updated_incident = self.repository.update_incident_status(incident_id, IncidentStatus.QUEUED)
        self.repository.create_analysis_run(incident_id, self._load_scenario(scenario_id), "retry")
        retry_event = self.repository.add_event(
            incident_id,
            IncidentEventType.ANALYSIS_QUEUED,
            "Analysis job re-queued for async retry",
            payload={"scenario": scenario_id, "correlation_id": incident_id, "retry": True},
        )
        return {
            "incident": updated_incident,
            "events": [retry_event],
            "recommendation": self.repository.get_recommendation(incident_id),
            "decision": self.repository.get_decision(incident_id),
            "analysis_request": analysis_request,
        }

    def list_incidents(self) -> list[dict[str, Any]]:
        return self.repository.list_incidents()

    def get_incident_detail(self, incident_id: str) -> dict[str, Any] | None:
        # The UI needs a single payload that contains all incident context in one request.
        incident = self.repository.get_incident(incident_id)
        if incident is None:
            return None
        analysis_runs = self._build_analysis_run_views(incident_id)
        return {
            "incident": incident,
            "events": self.repository.get_events(incident_id),
            "recommendation": self.repository.get_recommendation(incident_id),
            "decision": self.repository.get_decision(incident_id),
            "analysis_run": analysis_runs[-1] if analysis_runs else None,
            "analysis_runs": analysis_runs,
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

    def apply_analysis_result(self, result: AnalysisResultEnvelope) -> dict[str, Any] | None:
        incident = self.repository.get_incident(result.incident_id)
        if incident is None:
            return None

        scenario_id = self._get_scenario_id_for_incident(result.incident_id)
        scenario = self._load_scenario(scenario_id)
        latest_run = self.repository.get_latest_analysis_run(result.incident_id)

        event_records: list[dict[str, Any]] = []
        started_at: datetime | None = None
        completed_at = self._utc_now()
        has_failure_event = any(
            event.get("event_type") == IncidentEventType.ANALYSIS_FAILED.value for event in result.analysis_events
        )
        has_start_event = any(
            event.get("event_type") == IncidentEventType.ANALYSIS_STARTED.value for event in result.analysis_events
        )
        for event in result.analysis_events:
            event_type = event.get("event_type")
            if event_type is None:
                continue
            payload = event.get("payload")
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except json.JSONDecodeError:
                    payload = {"raw": payload}
            saved_event = self.repository.add_event(
                result.incident_id,
                IncidentEventType(event_type),
                event.get("message", ""),
                payload=payload,
            )
            event_records.append(saved_event)
            if event_type == IncidentEventType.ANALYSIS_STARTED.value:
                started_at = saved_event["created_at"]

        if result.analysis_status == "ANALYZING":
            if not has_start_event:
                started_event = self.repository.add_event(
                    result.incident_id,
                    IncidentEventType.ANALYSIS_STARTED,
                    "Analysis started for mock incident",
                )
                event_records.append(started_event)
                started_at = started_event["created_at"]
            else:
                started_event = next((event for event in event_records if event["event_type"] == IncidentEventType.ANALYSIS_STARTED), None)
                if started_event is not None:
                    started_at = started_event["created_at"]
            updated_incident = self.repository.update_incident_status(result.incident_id, IncidentStatus.ANALYZING)
            if latest_run is not None:
                self.repository.update_analysis_run(
                    latest_run["analysis_run_id"],
                    status=IncidentStatus.ANALYZING.value,
                    started_at=(started_at or completed_at).isoformat(),
                )
        elif result.analysis_status == "RECOMMENDATION_READY":
            recommendation = result.recommendation
            if recommendation is not None:
                if result.workflow_state is not None:
                    raw_model_output = recommendation.get("raw_model_output")
                    if isinstance(raw_model_output, dict):
                        raw_model_output.setdefault("workflow_state", result.workflow_state)
                    else:
                        recommendation["raw_model_output"] = {"workflow_state": result.workflow_state}
                self.repository.save_recommendation(result.incident_id, recommendation)
            updated_incident = self.repository.update_incident_status(result.incident_id, IncidentStatus.RECOMMENDATION_READY)
            if latest_run is not None:
                self._update_analysis_run_from_recommendation(
                    result.incident_id,
                    scenario,
                    recommendation or {},
                    IncidentStatus.RECOMMENDATION_READY.value,
                    completed_at=completed_at,
                    started_at=started_at,
                )
        elif result.analysis_status == "FAILED":
            if result.error and not has_failure_event:
                event_records.append(
                    self.repository.add_event(
                        result.incident_id,
                        IncidentEventType.ANALYSIS_FAILED,
                        "Analysis failed",
                        payload={"error": result.error},
                    )
                )
            updated_incident = self.repository.update_incident_status(result.incident_id, IncidentStatus.FAILED)
            if latest_run is not None:
                self.repository.update_analysis_run(
                    latest_run["analysis_run_id"],
                    status=IncidentStatus.FAILED.value,
                    completed_at=completed_at.isoformat(),
                    started_at=(started_at or completed_at).isoformat(),
                    analysis_latency_ms=self._analysis_latency_ms(started_at, completed_at, latest_run["created_at"]),
                )
        else:
            raise ValueError(f"Unknown analysis status: {result.analysis_status}")

        return {
            "incident": updated_incident,
            "events": event_records,
            "recommendation": self.repository.get_recommendation(result.incident_id),
        }

    def _build_analysis_request(self, incident: dict[str, Any], scenario_id: str) -> AnalysisRequestEnvelope:
        return AnalysisRequestEnvelope(
            incident_id=incident["incident_id"],
            scenario_id=scenario_id,
            service_name=incident["service_name"],
            severity=incident["severity"],
            symptom=incident["symptom"],
            metric_name=incident["metric_name"],
            metric_value=incident["metric_value"],
            threshold_value=incident["threshold_value"],
            created_at=incident["created_at"],
            correlation_id=incident["incident_id"],
            source="incident-api",
        )

    def _update_analysis_run_from_recommendation(
        self,
        incident_id: str,
        scenario: dict[str, Any],
        recommendation: dict[str, Any],
        status: str,
        *,
        completed_at: datetime,
        started_at: datetime | None = None,
    ) -> None:
        latest_run = self.repository.get_latest_analysis_run(incident_id)
        if latest_run is None:
            return
        recommendation_payload = recommendation or {}
        raw_model_output = recommendation_payload.get("raw_model_output") if isinstance(recommendation_payload, dict) else None
        retrieved_chunks = []
        if isinstance(raw_model_output, dict):
            retrieved_chunks = raw_model_output.get("retrieved_chunks") or []

        evidence_texts = self._collect_evidence_texts(recommendation_payload, raw_model_output, retrieved_chunks)
        expected_signals = scenario.get("expected_evidence_signals") or []
        hit_count = 0
        if expected_signals:
            for signal in expected_signals:
                signal_lower = str(signal).lower()
                if any(signal_lower in text for text in evidence_texts):
                    hit_count += 1
        expected_document_hit_rate = (hit_count / len(expected_signals)) if expected_signals else 0.0

        started_at_value = started_at or latest_run.get("started_at")
        self.repository.update_analysis_run(
            latest_run["analysis_run_id"],
            status=status,
            started_at=(started_at_value or latest_run["created_at"]).isoformat(),
            completed_at=completed_at.isoformat(),
            analysis_latency_ms=self._analysis_latency_ms(started_at_value, completed_at, latest_run["created_at"]),
            retrieved_document_count=len(retrieved_chunks),
            expected_document_hit_rate=expected_document_hit_rate,
            evidence_count=len(recommendation_payload.get("evidence", [])) if isinstance(recommendation_payload, dict) else 0,
            recommended_action_count=len(recommendation_payload.get("recommended_actions", []))
            if isinstance(recommendation_payload, dict)
            else 0,
            confidence_value=recommendation_payload.get("confidence") if isinstance(recommendation_payload, dict) else None,
        )

    def _collect_evidence_texts(
        self,
        recommendation: dict[str, Any],
        raw_model_output: dict[str, Any] | None,
        retrieved_chunks: list[dict[str, Any]],
    ) -> list[str]:
        texts: list[str] = []
        if isinstance(recommendation, dict):
            texts.extend(str(item).lower() for item in recommendation.get("evidence", []))
            texts.extend(str(item).lower() for item in recommendation.get("recommended_actions", []))
            if recommendation.get("summary"):
                texts.append(str(recommendation["summary"]).lower())
        if isinstance(raw_model_output, dict):
            texts.extend(str(item).lower() for item in raw_model_output.get("retrieved_chunks", []))
        for chunk in retrieved_chunks:
            if isinstance(chunk, dict):
                texts.append(str(chunk.get("title", "")).lower())
                texts.append(str(chunk.get("content", "")).lower())
        return texts

    def _build_analysis_run_views(self, incident_id: str) -> list[dict[str, Any]]:
        runs = self.repository.list_analysis_runs(incident_id)
        if not runs:
            return []

        events = self.repository.get_events(incident_id)
        recommendations = self.repository.list_recommendations(incident_id)
        run_views: list[dict[str, Any]] = []

        for index, run in enumerate(runs):
            next_run_created_at = runs[index + 1]["created_at"] if index + 1 < len(runs) else None
            recommendation = self._select_run_recommendation(run["created_at"], next_run_created_at, recommendations)
            analysis_events = [
                event
                for event in events
                if event["created_at"] >= run["created_at"]
                and (next_run_created_at is None or event["created_at"] < next_run_created_at)
            ]
            run_views.append(
                {
                    **run,
                    "recommendation": recommendation,
                    "analysis_events": analysis_events,
                }
            )

        return run_views

    def _select_run_recommendation(
        self,
        run_created_at: datetime,
        next_run_created_at: datetime | None,
        recommendations: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        selected: dict[str, Any] | None = None
        for recommendation in recommendations:
            created_at = recommendation.get("created_at")
            if not isinstance(created_at, datetime):
                continue
            if created_at < run_created_at:
                continue
            if next_run_created_at is not None and created_at >= next_run_created_at:
                continue
            selected = recommendation
        return selected

    def _utc_now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _analysis_latency_ms(
        self,
        started_at: datetime | None,
        completed_at: datetime,
        fallback_start_at: datetime,
    ) -> int:
        start_point = started_at or fallback_start_at
        return max(int((completed_at - start_point).total_seconds() * 1000), 0)

    def _get_scenario_id_for_incident(self, incident_id: str) -> str:
        # The seeded scenario id is preserved in the first incident event payload.
        for event in self.repository.get_events(incident_id):
            payload = event.get("payload")
            if not isinstance(payload, dict):
                continue
            scenario_id = payload.get("scenario") or payload.get("scenario_id")
            if isinstance(scenario_id, str) and scenario_id:
                return scenario_id
        raise ValueError(f"Unable to determine scenario for incident {incident_id}")
