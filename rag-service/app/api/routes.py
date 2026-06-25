from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from ..schemas import AnalyzeIncidentRequest, AnalyzeIncidentResponse
from ..core.runtime import get_runtime

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/analyze", response_model=AnalyzeIncidentResponse)
def analyze_incident(payload: AnalyzeIncidentRequest) -> AnalyzeIncidentResponse:
    try:
        logger.info(
            "Received /analyze request incident_id=%s service=%s severity=%s",
            payload.incident_id,
            payload.service_name,
            payload.severity,
        )
        return get_runtime().analysis_engine.analyze(payload)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail="Required mock data is missing") from exc
