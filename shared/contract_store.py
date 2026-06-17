from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
CONTRACT_DB_PATH = DATA_DIR / "shared_contracts.sqlite3"
CONTRACT_SEED_PATH = BASE_DIR / "contracts" / "incident_contracts.json"


def _load_seed_payload() -> dict[str, Any]:
    with CONTRACT_SEED_PATH.open("r", encoding="utf-8") as file_handle:
        return json.load(file_handle)


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(CONTRACT_DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def ensure_contract_store() -> None:
    seed = _load_seed_payload()
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS incident_statuses (
                code TEXT PRIMARY KEY,
                sort_order INTEGER NOT NULL,
                is_terminal INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS incident_event_types (
                code TEXT PRIMARY KEY,
                sort_order INTEGER NOT NULL,
                category TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS decision_types (
                code TEXT PRIMARY KEY,
                sort_order INTEGER NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS recommendation_schema_fields (
                field_name TEXT PRIMARY KEY,
                field_type TEXT NOT NULL,
                required INTEGER NOT NULL DEFAULT 1,
                description TEXT NOT NULL DEFAULT ''
            )
            """
        )

        connection.execute("DELETE FROM incident_statuses")
        connection.execute("DELETE FROM incident_event_types")
        connection.execute("DELETE FROM decision_types")
        connection.execute("DELETE FROM recommendation_schema_fields")

        for index, code in enumerate(seed["incident_statuses"]):
            connection.execute(
                "INSERT INTO incident_statuses (code, sort_order, is_terminal) VALUES (?, ?, ?)",
                (code, index, int(code in {"APPROVED", "REJECTED", "ESCALATED", "FAILED"})),
            )
        for index, code in enumerate(seed["event_types"]):
            connection.execute(
                "INSERT INTO incident_event_types (code, sort_order, category) VALUES (?, ?, ?)",
                (code, index, "human" if code.startswith("HUMAN_") else "analysis" if code != "INCIDENT_CREATED" else "lifecycle"),
            )
        for index, code in enumerate(seed["decision_types"]):
            connection.execute(
                "INSERT INTO decision_types (code, sort_order) VALUES (?, ?)",
                (code, index),
            )
        recommendation_schema = seed["recommendation_schema"]
        for index, (field_name, field_value) in enumerate(recommendation_schema.items()):
            field_type = "boolean" if isinstance(field_value, bool) else "list[string]" if isinstance(field_value, list) else "string"
            connection.execute(
                """
                INSERT INTO recommendation_schema_fields (field_name, field_type, required, description)
                VALUES (?, ?, ?, ?)
                """,
                (field_name, field_type, int(field_name != "raw_model_output"), f"Seeded field {index}"),
            )


def fetch_contract_registry() -> dict[str, Any]:
    ensure_contract_store()
    with _connect() as connection:
        statuses = []
        for row in connection.execute("SELECT * FROM incident_statuses ORDER BY sort_order"):
            record = dict(row)
            record["is_terminal"] = bool(record["is_terminal"])
            statuses.append(record)
        event_types = [dict(row) for row in connection.execute("SELECT * FROM incident_event_types ORDER BY sort_order")]
        decision_types = [dict(row) for row in connection.execute("SELECT * FROM decision_types ORDER BY sort_order")]
        recommendation_fields = [
            {**dict(row), "required": bool(row["required"])}
            for row in connection.execute("SELECT * FROM recommendation_schema_fields ORDER BY field_name")
        ]
    return {
        "incident_statuses": statuses,
        "incident_event_types": event_types,
        "decision_types": decision_types,
        "recommendation_schema_fields": recommendation_fields,
    }


def fetch_contract_values() -> dict[str, list[str]]:
    registry = fetch_contract_registry()
    return {
        "incident_statuses": [item["code"] for item in registry["incident_statuses"]],
        "event_types": [item["code"] for item in registry["incident_event_types"]],
        "decision_types": [item["code"] for item in registry["decision_types"]],
    }


def fetch_recommendation_schema() -> dict[str, dict[str, Any]]:
    registry = fetch_contract_registry()
    return {
        item["field_name"]: {
            "field_type": item["field_type"],
            "required": item["required"],
            "description": item["description"],
        }
        for item in registry["recommendation_schema_fields"]
    }
