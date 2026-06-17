from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from shared.contracts.incident_contracts import DecisionType, IncidentEventType, IncidentStatus

from .config import DATABASE_PATH


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return utc_now().isoformat()


def parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


class IncidentRepository:
    def __init__(self, database_path: Path = DATABASE_PATH) -> None:
        self.database_path = database_path
        # RLock lets repository methods call each other without deadlocking.
        self._lock = threading.RLock()
        # SQLite keeps Stage 2 self-contained without needing an external service.
        self._connection = sqlite3.connect(self.database_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        # The database schema mirrors the Stage 1 migration so the runtime can bootstrap itself.
        with self._connection:
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS incidents (
                    id TEXT PRIMARY KEY,
                    service_name TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    symptom TEXT NOT NULL,
                    metric_name TEXT,
                    metric_value TEXT,
                    threshold_value TEXT,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS incident_events (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    id TEXT NOT NULL UNIQUE,
                    incident_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    payload TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS incident_recommendations (
                    id TEXT PRIMARY KEY,
                    incident_id TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    evidence TEXT NOT NULL,
                    recommended_actions TEXT NOT NULL,
                    confidence TEXT NOT NULL,
                    requires_human_approval INTEGER NOT NULL DEFAULT 1,
                    raw_model_output TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS incident_decisions (
                    id TEXT PRIMARY KEY,
                    incident_id TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    decided_by TEXT NOT NULL,
                    note TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            self._connection.execute(
                "CREATE INDEX IF NOT EXISTS incident_events_incident_id_idx ON incident_events (incident_id, sequence)"
            )
            self._connection.execute(
                "CREATE INDEX IF NOT EXISTS incident_decisions_incident_id_idx ON incident_decisions (incident_id, created_at DESC)"
            )

    @contextmanager
    def _locked(self):
        with self._lock:
            yield

    def _row_to_incident(self, row: sqlite3.Row) -> dict:
        # Normalize database rows into the shape the API returns to clients.
        return {
            "incident_id": row["id"],
            "service_name": row["service_name"],
            "severity": row["severity"],
            "symptom": row["symptom"],
            "status": IncidentStatus(row["status"]),
            "created_at": parse_dt(row["created_at"]),
            "updated_at": parse_dt(row["updated_at"]),
            "recommendation_status": self.get_recommendation_status(row["id"]),
            "approval_status": self.get_approval_status(row["id"]),
        }

    def _row_to_event(self, row: sqlite3.Row) -> dict:
        # Event payloads are stored as JSON strings in SQLite and rehydrated here.
        return {
            "sequence": row["sequence"],
            "event_id": row["id"],
            "incident_id": row["incident_id"],
            "event_type": IncidentEventType(row["event_type"]),
            "message": row["message"],
            "payload": json.loads(row["payload"]) if row["payload"] else None,
            "created_at": parse_dt(row["created_at"]),
        }

    def _row_to_recommendation(self, row: sqlite3.Row) -> dict:
        return {
            "incident_id": row["incident_id"],
            "summary": row["summary"],
            "evidence": json.loads(row["evidence"]),
            "recommended_actions": json.loads(row["recommended_actions"]),
            "confidence": row["confidence"],
            "requires_human_approval": bool(row["requires_human_approval"]),
            "raw_model_output": json.loads(row["raw_model_output"]) if row["raw_model_output"] else None,
            "created_at": parse_dt(row["created_at"]),
        }

    def _row_to_decision(self, row: sqlite3.Row) -> dict:
        return {
            "decision_id": row["id"],
            "incident_id": row["incident_id"],
            "decision": DecisionType(row["decision"]),
            "decided_by": row["decided_by"],
            "note": row["note"],
            "created_at": parse_dt(row["created_at"]),
        }

    def create_incident(self, scenario: dict) -> dict:
        # Insert a brand-new incident row using the seeded mock scenario fields.
        incident_id = str(uuid4())
        timestamp = iso_now()
        with self._locked(), self._connection:
            self._connection.execute(
                """
                INSERT INTO incidents (
                    id, service_name, severity, symptom, metric_name, metric_value, threshold_value, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    incident_id,
                    scenario["service_name"],
                    scenario["severity"],
                    scenario["symptom"],
                    scenario["metric_name"],
                    scenario["metric_value"],
                    scenario["threshold_value"],
                    IncidentStatus.CREATED.value,
                    timestamp,
                    timestamp,
                ),
            )
        return self.get_incident(incident_id)

    def update_incident_status(self, incident_id: str, status: IncidentStatus) -> dict:
        timestamp = iso_now()
        with self._locked(), self._connection:
            self._connection.execute(
                "UPDATE incidents SET status = ?, updated_at = ? WHERE id = ?",
                (status.value, timestamp, incident_id),
            )
        return self.get_incident(incident_id)

    def get_incident_row(self, incident_id: str) -> sqlite3.Row | None:
        with self._locked():
            cursor = self._connection.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,))
            return cursor.fetchone()

    def get_incident(self, incident_id: str) -> dict | None:
        row = self.get_incident_row(incident_id)
        if row is None:
            return None
        return self._row_to_incident(row)

    def list_incidents(self) -> list[dict]:
        with self._locked():
            cursor = self._connection.execute("SELECT * FROM incidents ORDER BY created_at DESC")
            return [self._row_to_incident(row) for row in cursor.fetchall()]

    def add_event(
        self,
        incident_id: str,
        event_type: IncidentEventType,
        message: str,
        payload: dict | None = None,
    ) -> dict:
        # Every incident action becomes an immutable timeline entry.
        timestamp = iso_now()
        event_id = str(uuid4())
        with self._locked(), self._connection:
            self._connection.execute(
                """
                INSERT INTO incident_events (id, incident_id, event_type, message, payload, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    incident_id,
                    event_type.value,
                    message,
                    json.dumps(payload) if payload is not None else None,
                    timestamp,
                ),
            )
            cursor = self._connection.execute("SELECT * FROM incident_events WHERE id = ?", (event_id,))
            row = cursor.fetchone()
        return self._row_to_event(row)

    def get_events(self, incident_id: str) -> list[dict]:
        with self._locked():
            cursor = self._connection.execute(
                "SELECT * FROM incident_events WHERE incident_id = ? ORDER BY sequence ASC",
                (incident_id,),
            )
            return [self._row_to_event(row) for row in cursor.fetchall()]

    def get_events_after(self, incident_id: str, sequence: int) -> list[dict]:
        with self._locked():
            cursor = self._connection.execute(
                """
                SELECT * FROM incident_events
                WHERE incident_id = ? AND sequence > ?
                ORDER BY sequence ASC
                """,
                (incident_id, sequence),
            )
            return [self._row_to_event(row) for row in cursor.fetchall()]

    def get_last_sequence(self, incident_id: str) -> int:
        with self._locked():
            cursor = self._connection.execute(
                "SELECT COALESCE(MAX(sequence), 0) AS max_sequence FROM incident_events WHERE incident_id = ?",
                (incident_id,),
            )
            row = cursor.fetchone()
            return int(row["max_sequence"]) if row else 0

    def save_recommendation(self, incident_id: str, recommendation: dict) -> dict:
        # Stage 2 does not generate recommendations yet, but the table is ready for Stage 3.
        recommendation_id = str(uuid4())
        timestamp = iso_now()
        with self._locked(), self._connection:
            self._connection.execute(
                """
                INSERT INTO incident_recommendations (
                    id, incident_id, summary, evidence, recommended_actions, confidence,
                    requires_human_approval, raw_model_output, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    recommendation_id,
                    incident_id,
                    recommendation["summary"],
                    json.dumps(recommendation["evidence"]),
                    json.dumps(recommendation["recommended_actions"]),
                    recommendation["confidence"],
                    1 if recommendation.get("requires_human_approval", True) else 0,
                    json.dumps(recommendation["raw_model_output"]) if recommendation.get("raw_model_output") else None,
                    timestamp,
                ),
            )
            cursor = self._connection.execute("SELECT * FROM incident_recommendations WHERE id = ?", (recommendation_id,))
            row = cursor.fetchone()
        return self._row_to_recommendation(row)

    def get_recommendation(self, incident_id: str) -> dict | None:
        with self._locked():
            cursor = self._connection.execute(
                """
                SELECT * FROM incident_recommendations
                WHERE incident_id = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (incident_id,),
            )
            row = cursor.fetchone()
            if row is None:
                return None
        return self._row_to_recommendation(row)

    def save_decision(self, incident_id: str, decision: DecisionType, decided_by: str, note: str | None = None) -> dict:
        # Human decisions are stored separately from timeline events so the UI can show both.
        decision_id = str(uuid4())
        timestamp = iso_now()
        with self._locked(), self._connection:
            self._connection.execute(
                """
                INSERT INTO incident_decisions (id, incident_id, decision, decided_by, note, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (decision_id, incident_id, decision.value, decided_by, note, timestamp),
            )
            cursor = self._connection.execute("SELECT * FROM incident_decisions WHERE id = ?", (decision_id,))
            row = cursor.fetchone()
        return self._row_to_decision(row)

    def get_decision(self, incident_id: str) -> dict | None:
        with self._locked():
            cursor = self._connection.execute(
                """
                SELECT * FROM incident_decisions
                WHERE incident_id = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (incident_id,),
            )
            row = cursor.fetchone()
            if row is None:
                return None
        return self._row_to_decision(row)

    def get_recommendation_status(self, incident_id: str) -> str:
        recommendation = self.get_recommendation(incident_id)
        return "READY" if recommendation else "PENDING"

    def get_approval_status(self, incident_id: str) -> str | None:
        decision = self.get_decision(incident_id)
        return decision["decision"].value if decision else None
