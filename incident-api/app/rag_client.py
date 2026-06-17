from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any
from urllib import error, request

from .config import RAG_SERVICE_BASE_URL, RAG_SERVICE_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RAGClientResponse:
    recommendation: dict[str, Any]
    analysis_events: list[dict[str, Any]]
    raw_response: dict[str, Any]


def request_recommendation(payload: dict[str, Any]) -> RAGClientResponse:
    body = json.dumps(payload).encode("utf-8")
    logger.info(
        "Sending RAG request to %s/analyze incident_id=%s service=%s",
        RAG_SERVICE_BASE_URL,
        payload.get("incident_id"),
        payload.get("service_name"),
    )
    http_request = request.Request(
        f"{RAG_SERVICE_BASE_URL}/analyze",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(http_request, timeout=RAG_SERVICE_TIMEOUT_SECONDS) as response:
            response_body = response.read().decode("utf-8")
        logger.info(
            "Received RAG response from %s/analyze incident_id=%s",
            RAG_SERVICE_BASE_URL,
            payload.get("incident_id"),
        )
    except error.URLError as exc:  # pragma: no cover - exercised in manual integration only
        logger.exception(
            "RAG request failed for incident_id=%s service=%s",
            payload.get("incident_id"),
            payload.get("service_name"),
        )
        raise RuntimeError(f"RAG service request failed: {exc}") from exc

    raw_response = json.loads(response_body)
    return RAGClientResponse(
        recommendation=raw_response["recommendation"],
        analysis_events=raw_response.get("analysis_events", []),
        raw_response=raw_response,
    )
