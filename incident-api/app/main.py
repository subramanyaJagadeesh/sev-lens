from __future__ import annotations

import asyncio
import json
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from shared.contract_store import fetch_contract_registry

from .events import EventBus
from .repository import IncidentRepository
from .schemas import (
    IncidentCreateMockRequest,
    IncidentDecisionRequest,
    IncidentDecisionResponse,
    IncidentDetailResponse,
    IncidentEventResponse,
    IncidentRecommendationResponse,
    IncidentSummaryResponse,
    StreamEventResponse,
)
from .service import IncidentService

repository = IncidentRepository()
event_bus = EventBus()
incident_service = IncidentService(repository, event_bus)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # We keep the lifespan hook in place so startup/shutdown work can be added later.
    yield


app = FastAPI(title="OpsPulse Incident API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("OPSPULSE_CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check() -> dict[str, str]:
    # Simple health endpoint for local smoke checks and container probes.
    return {"status": "ok"}


@app.get("/api/contracts")
def get_contracts() -> dict:
    # The frontend can fetch this to stay aligned with DB-backed shared shapes.
    return fetch_contract_registry()


@app.exception_handler(KeyError)
async def key_error_handler(_: Request, exc: KeyError):
    # Scenario lookup failures are treated as missing resources.
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": f"Unknown scenario: {exc.args[0]}"})


@app.post("/api/incidents/mock", response_model=IncidentSummaryResponse)
async def create_mock_incident(payload: IncidentCreateMockRequest) -> IncidentSummaryResponse:
    try:
        result = incident_service.create_mock_incident(payload.scenario)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown scenario: {exc.args[0]}") from exc

    # Publish the bootstrap events so any SSE client can replay the incident timeline.
    for event in result["events"]:
        await event_bus.publish(event)
    incident = result["incident"]
    return IncidentSummaryResponse(**incident)


@app.get("/api/incidents", response_model=list[IncidentSummaryResponse])
async def list_incidents() -> list[IncidentSummaryResponse]:
    return [IncidentSummaryResponse(**incident) for incident in incident_service.list_incidents()]


@app.get("/api/incidents/{incident_id}", response_model=IncidentDetailResponse)
async def get_incident_detail(incident_id: str) -> IncidentDetailResponse:
    # Detail responses combine the incident record, timeline, recommendation, and decision.
    detail = incident_service.get_incident_detail(incident_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return IncidentDetailResponse(
        incident=IncidentSummaryResponse(**detail["incident"]),
        events=[IncidentEventResponse(**event) for event in detail["events"]],
        recommendation=IncidentRecommendationResponse(**detail["recommendation"]) if detail["recommendation"] else None,
        decision=IncidentDecisionResponse(**detail["decision"]) if detail["decision"] else None,
    )


@app.post("/api/incidents/{incident_id}/decision", response_model=IncidentDecisionResponse)
async def post_decision(incident_id: str, payload: IncidentDecisionRequest) -> IncidentDecisionResponse:
    # Human decisions update incident status and emit an audit event.
    result = incident_service.record_decision(incident_id, payload.decision, payload.note)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    await event_bus.publish(result["event"])
    return IncidentDecisionResponse(**result["decision"])


@app.get("/api/incidents/{incident_id}/stream")
async def incident_stream(incident_id: str):
    if incident_service.get_incident_detail(incident_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    async def event_generator():
        # First replay already-stored events so the UI can catch up after reconnecting.
        last_sequence = 0
        for event in repository.get_events(incident_id):
            last_sequence = event["sequence"]
            yield _format_sse(event)

        # Then stay open and stream any new events as they arrive.
        async for queue in event_bus.subscribe():
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
    # SSE wants a tiny text envelope, so we serialize the structured event as JSON.
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
