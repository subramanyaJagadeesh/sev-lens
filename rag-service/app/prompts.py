from __future__ import annotations

import json
from typing import Iterable

from .schemas import OperativeContext, RetrievedDocumentChunk


SYSTEM_PROMPT = """You are an incident response assistant.
Use only the provided incident context, tool execution results, operational data, and retrieved documents.
The analysis is part of a controlled multi-step workflow; use the supplied investigation state as source material.
Return a single JSON object matching this schema:
{
  "summary": "string",
  "evidence": ["string"],
  "recommended_actions": ["string"],
  "confidence": "low|medium|high",
  "requires_human_approval": true,
  "incident_summary": "string|null",
  "symptoms": ["string"],
  "risk_level": "low|medium|high|null",
  "hypotheses": [{"hypothesis":"string","confidence":"string","supporting_signals":["string"],"evidence_gaps":["string"]}],
  "source_documents": [{"title":"string","doc_type":"string","service":"string|null","source":"string|null"}],
  "similar_rcas": [{"title":"string","service_name":"string","match_explanation":"string","score":0.0}],
  "unsupported_areas": ["string"],
  "action_evidence_links": [{"action":"string","evidence":["string"],"source_documents":["string"],"similar_rcas":["string"]}]
}
Do not claim you performed any action. Do not include markdown fences."""

PLANNER_SYSTEM_PROMPT = """You are an incident investigation planner.
Choose the next best investigation action based only on the current incident state and evidence.
Return a single JSON object matching this schema:
{
  "next_action": "collect_context|retrieve_knowledge|retrieve_rca|compose_response",
  "reason": "string",
  "query": "string|null",
  "focus": "string|null"
}
Do not include markdown fences or chain-of-thought."""


def build_user_prompt(
    query: str,
    operational_context: OperativeContext,
    retrieved_chunks: Iterable[RetrievedDocumentChunk],
    workflow_state: dict[str, object] | None = None,
) -> str:
    chunk_payload = [chunk.model_dump(mode="json") for chunk in retrieved_chunks]
    context_payload = operational_context.model_dump(mode="json")
    tool_results_payload = context_payload.pop("tool_results", [])
    context_payload.pop("runbook_chunks", None)
    context_payload.pop("rca_chunks", None)
    workflow_payload = json.dumps(workflow_state, indent=2) if workflow_state else "null"
    return "\n\n".join(
        [
            "Incident context:",
            query,
            "Investigation workflow state:",
            workflow_payload,
            "Tool execution results:",
            json.dumps(tool_results_payload, indent=2) if tool_results_payload else "[]",
            "Operational context:",
            json.dumps(context_payload, indent=2),
            "Retrieved documents:",
            json.dumps(chunk_payload, indent=2) if chunk_payload else "[]",
        ]
    )


def build_planner_prompt(
    query: str,
    operational_context: OperativeContext,
    workflow_state: dict[str, object] | None = None,
    available_actions: list[dict[str, str]] | None = None,
    iteration: int = 0,
    max_iterations: int = 4,
) -> str:
    context_payload = operational_context.model_dump(mode="json")
    tool_results_payload = context_payload.pop("tool_results", [])
    retrieved_runbooks = context_payload.pop("runbook_chunks", [])
    retrieved_rcas = context_payload.pop("rca_chunks", [])
    workflow_payload = json.dumps(workflow_state, indent=2) if workflow_state else "null"
    actions_payload = json.dumps(available_actions or [], indent=2)
    return "\n\n".join(
        [
            "Incident context:",
            query,
            "Current workflow state:",
            workflow_payload,
            "Planner iteration:",
            json.dumps({"iteration": iteration, "max_iterations": max_iterations}, indent=2),
            "Available actions:",
            actions_payload,
            "Tool execution results:",
            json.dumps(tool_results_payload, indent=2) if tool_results_payload else "[]",
            "Retrieved runbooks:",
            json.dumps(retrieved_runbooks, indent=2) if retrieved_runbooks else "[]",
            "Retrieved RCAs:",
            json.dumps(retrieved_rcas, indent=2) if retrieved_rcas else "[]",
            "Operational context:",
            json.dumps(context_payload, indent=2),
        ]
    )
