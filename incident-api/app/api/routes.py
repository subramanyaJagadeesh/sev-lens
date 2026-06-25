from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from shared.contract_store import fetch_contract_registry
from ..schemas import (
    IncidentAnalysisRunResponse,
    IncidentCreateMockRequest,
    IncidentDecisionRequest,
    IncidentDecisionResponse,
    IncidentDetailResponse,
    IncidentEventResponse,
    IncidentRecommendationResponse,
    IncidentSummaryResponse,
    StreamEventResponse,
)
from ..core.runtime import get_runtime

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/api/contracts")
def get_contracts() -> dict:
    return fetch_contract_registry()


@router.post("/api/incidents/mock", response_model=IncidentSummaryResponse)
async def create_mock_incident(payload: IncidentCreateMockRequest) -> IncidentSummaryResponse:
    runtime = get_runtime()
    try:
        result = runtime.incident_service.create_mock_incident(payload.scenario)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown scenario: {exc.args[0]}") from exc

    if result["analysis_request"] is not None:
        await asyncio.to_thread(runtime.analysis_queue.publish, result["analysis_request"])
    for event in result["events"]:
        await runtime.event_bus.publish(event)
    return IncidentSummaryResponse(**result["incident"])


@router.get("/api/incidents", response_model=list[IncidentSummaryResponse])
async def list_incidents() -> list[IncidentSummaryResponse]:
    runtime = get_runtime()
    return [IncidentSummaryResponse(**incident) for incident in runtime.incident_service.list_incidents()]


@router.get("/api/incidents/{incident_id}", response_model=IncidentDetailResponse)
async def get_incident_detail(incident_id: str) -> IncidentDetailResponse:
    runtime = get_runtime()
    detail = runtime.incident_service.get_incident_detail(incident_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return IncidentDetailResponse(
        incident=IncidentSummaryResponse(**detail["incident"]),
        events=[IncidentEventResponse(**event) for event in detail["events"]],
        recommendation=IncidentRecommendationResponse(**detail["recommendation"]) if detail["recommendation"] else None,
        decision=IncidentDecisionResponse(**detail["decision"]) if detail["decision"] else None,
        analysis_run=IncidentAnalysisRunResponse(**detail["analysis_run"]) if detail.get("analysis_run") else None,
        analysis_runs=[IncidentAnalysisRunResponse(**analysis_run) for analysis_run in detail.get("analysis_runs", [])],
    )


@router.get("/api/incidents/{incident_id}/analysis-runs", response_model=list[IncidentAnalysisRunResponse])
async def get_incident_analysis_runs(incident_id: str) -> list[IncidentAnalysisRunResponse]:
    runtime = get_runtime()
    detail = runtime.incident_service.get_incident_detail(incident_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return [IncidentAnalysisRunResponse(**analysis_run) for analysis_run in detail.get("analysis_runs", [])]


@router.post("/api/incidents/{incident_id}/decision", response_model=IncidentDecisionResponse)
async def post_decision(incident_id: str, payload: IncidentDecisionRequest) -> IncidentDecisionResponse:
    runtime = get_runtime()
    result = runtime.incident_service.record_decision(incident_id, payload.decision, payload.note)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    await runtime.event_bus.publish(result["event"])
    return IncidentDecisionResponse(**result["decision"])


@router.post("/api/incidents/{incident_id}/analysis/retry", response_model=IncidentSummaryResponse)
async def retry_analysis(incident_id: str) -> IncidentSummaryResponse:
    runtime = get_runtime()
    try:
        result = runtime.incident_service.retry_analysis(incident_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    if result["analysis_request"] is not None:
        await asyncio.to_thread(runtime.analysis_queue.publish, result["analysis_request"])
    for event in result["events"]:
        await runtime.event_bus.publish(event)
    return IncidentSummaryResponse(**result["incident"])


@router.get("/api/incidents/{incident_id}/stream")
async def incident_stream(incident_id: str):
    runtime = get_runtime()
    if runtime.incident_service.get_incident_detail(incident_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    async def event_generator():
        last_sequence = 0
        for event in runtime.repository.get_events(incident_id):
            last_sequence = event["sequence"]
            yield _format_sse(event)

        async for queue in runtime.event_bus.subscribe():
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=1)
                except TimeoutError:
                    yield ": keep-alive\n\n"
                    continue
                if event["incident_id"] != incident_id:
                    continue
                if event["sequence"] <= last_sequence:
                    continue
                last_sequence = event["sequence"]
                yield _format_sse(event)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


def _format_sse(event: dict) -> str:
    stream_event = StreamEventResponse(
        incident_id=event["incident_id"],
        event_type=event["event_type"],
        message=event["message"],
        created_at=event["created_at"],
        sequence=event["sequence"],
        payload=event["payload"],
    )
    body = stream_event.model_dump(mode="json")
    return f"event: incident-event\ndata: {json.dumps(body)}\n\n"
