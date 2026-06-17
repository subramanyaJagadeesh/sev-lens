from __future__ import annotations

import json
from typing import Any

from .schemas import RecommendationPayload

ALLOWED_CONFIDENCE_VALUES = {"low", "medium", "high"}


def normalize_recommendation_payload(raw_payload: Any) -> RecommendationPayload:
    if isinstance(raw_payload, str):
        raw_payload = json.loads(raw_payload)

    if not isinstance(raw_payload, dict):
        raise ValueError("LLM response must be a JSON object.")

    required_fields = {"summary", "evidence", "recommended_actions", "confidence", "requires_human_approval"}
    missing_fields = required_fields - raw_payload.keys()
    if missing_fields:
        raise ValueError(f"LLM response is missing required fields: {sorted(missing_fields)}")

    if raw_payload["confidence"] not in ALLOWED_CONFIDENCE_VALUES:
        raise ValueError("LLM response confidence must be low, medium, or high.")

    if not isinstance(raw_payload["evidence"], list) or not all(isinstance(item, str) for item in raw_payload["evidence"]):
        raise ValueError("LLM response evidence must be a list of strings.")

    if not isinstance(raw_payload["recommended_actions"], list) or not all(
        isinstance(item, str) for item in raw_payload["recommended_actions"]
    ):
        raise ValueError("LLM response recommended_actions must be a list of strings.")

    if not isinstance(raw_payload["summary"], str):
        raise ValueError("LLM response summary must be a string.")

    if not isinstance(raw_payload["requires_human_approval"], bool):
        raise ValueError("LLM response requires_human_approval must be a boolean.")

    return RecommendationPayload.model_validate(raw_payload)

