from __future__ import annotations

import json
from typing import Iterable

from .schemas import OperativeContext, RetrievedDocumentChunk


SYSTEM_PROMPT = """You are an incident response assistant.
Use only the provided incident context, operational data, and retrieved documents.
Return a single JSON object matching this schema:
{
  "summary": "string",
  "evidence": ["string"],
  "recommended_actions": ["string"],
  "confidence": "low|medium|high",
  "requires_human_approval": true
}
Do not claim you performed any action. Do not include markdown fences."""


def build_user_prompt(
    query: str,
    operational_context: OperativeContext,
    retrieved_chunks: Iterable[RetrievedDocumentChunk],
) -> str:
    chunk_payload = [chunk.model_dump(mode="json") for chunk in retrieved_chunks]
    context_payload = operational_context.model_dump(mode="json")
    return "\n\n".join(
        [
            "Incident context:",
            query,
            "Operational context:",
            json.dumps(context_payload, indent=2),
            "Retrieved documents:",
            json.dumps(chunk_payload, indent=2) if chunk_payload else "[]",
        ]
    )
