from pathlib import Path
import sys
import os
import logging

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

LOG_LEVEL = os.getenv("OPSPULSE_LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logging.getLogger().setLevel(LOG_LEVEL)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .analysis import AnalysisEngine
from .schemas import AnalyzeIncidentRequest, AnalyzeIncidentResponse

app = FastAPI(title="OpsPulse RAG Service")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("OPSPULSE_CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
analysis_engine = AnalysisEngine()
logger = logging.getLogger(__name__)
logger.info(
    "RAG config resolved provider=%s base_url=%s model=%s timeout_seconds=%s",
    os.getenv("RAG_LLM_PROVIDER", "ollama"),
    os.getenv("RAG_LLM_BASE_URL", "http://localhost:11434/api"),
    os.getenv("RAG_LLM_MODEL", "qwen3.5:4b"),
    os.getenv("RAG_LLM_TIMEOUT_SECONDS", "300"),
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeIncidentResponse)
def analyze_incident(payload: AnalyzeIncidentRequest) -> AnalyzeIncidentResponse:
    try:
        logger.info(
            "Received /analyze request incident_id=%s service=%s severity=%s",
            payload.incident_id,
            payload.service_name,
            payload.severity,
        )
        return analysis_engine.analyze(payload)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail="Required mock data is missing") from exc
