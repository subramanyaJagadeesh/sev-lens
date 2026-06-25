from __future__ import annotations

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_PATH = DATA_DIR / "incident_api.sqlite3"
RAG_SERVICE_BASE_URL = os.getenv("SEVLENS_RAG_SERVICE_BASE_URL", "http://localhost:8001")
RAG_SERVICE_TIMEOUT_SECONDS = float(os.getenv("SEVLENS_RAG_SERVICE_TIMEOUT_SECONDS", "30"))
REDIS_URL = os.getenv("SEVLENS_REDIS_URL", "redis://localhost:6379/0")
ANALYSIS_REQUEST_STREAM = os.getenv("SEVLENS_ANALYSIS_REQUEST_STREAM", "sevlens:analysis:requests")
ANALYSIS_RESULT_STREAM = os.getenv("SEVLENS_ANALYSIS_RESULT_STREAM", "sevlens:analysis:results")
ANALYSIS_RESULT_GROUP = os.getenv("SEVLENS_ANALYSIS_RESULT_GROUP", "sevlens:analysis:results:incident-api")
ANALYSIS_RESULT_CONSUMER = os.getenv("SEVLENS_ANALYSIS_RESULT_CONSUMER", "incident-api-1")
ENABLE_SYNC_ANALYSIS_FALLBACK = os.getenv("SEVLENS_SYNC_ANALYSIS_FALLBACK", "false").lower() in {"1", "true", "yes"}
