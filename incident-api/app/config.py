from __future__ import annotations

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_PATH = DATA_DIR / "incident_api.sqlite3"
SCENARIO_PATH = BASE_DIR.parent / "shared" / "mock-data" / "scenarios" / "notification-service-kafka-timeout.json"
RAG_SERVICE_BASE_URL = os.getenv("OPSPULSE_RAG_SERVICE_BASE_URL", "http://localhost:8001")
RAG_SERVICE_TIMEOUT_SECONDS = float(os.getenv("OPSPULSE_RAG_SERVICE_TIMEOUT_SECONDS", "30"))
