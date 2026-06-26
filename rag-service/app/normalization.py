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

    optional_list_fields = {
        "symptoms": str,
        "unsupported_areas": str,
        "hypotheses": dict,
        "source_documents": dict,
        "similar_rcas": dict,
        "action_evidence_links": dict,
    }
    for field_name, item_type in optional_list_fields.items():
        if field_name not in raw_payload or raw_payload[field_name] is None:
            continue
        value = raw_payload[field_name]
        if not isinstance(value, list) or not all(isinstance(item, item_type) for item in value):
            raise ValueError(f"LLM response {field_name} must be a list of {item_type.__name__} values.")

    if "incident_summary" in raw_payload and raw_payload["incident_summary"] is not None and not isinstance(
        raw_payload["incident_summary"], str
    ):
        raise ValueError("LLM response incident_summary must be a string.")

    if "risk_level" in raw_payload and raw_payload["risk_level"] is not None and not isinstance(raw_payload["risk_level"], str):
        raise ValueError("LLM response risk_level must be a string.")

    return RecommendationPayload.model_validate(raw_payload)
