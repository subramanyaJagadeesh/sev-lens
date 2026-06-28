# SevLens Incident API

This service is the incident system of record for SevLens. It owns incident persistence, event history, analysis-run state, decisions, and the SSE stream that keeps the UI live.

## What it does

- persists incidents, events, decisions, and analysis runs in SQLite
- exposes the incident list, detail, decision, retry, and replay APIs
- streams incident updates over SSE so the UI stays in sync
- publishes analysis jobs to Redis Streams
- consumes worker results and merges them back into the incident timeline
- keeps the canonical incident status and decision history

## Why it exists

The UI should never be the source of truth for incident state. This service gives SevLens a stable backend that other incident tools can post into, while still preserving the full timeline and human decisions for auditability.

## Main features

- `POST /api/incidents/mock` creates a seeded demo incident and queues analysis
- `GET /api/incidents` returns the current incident list for the dashboard and incidents page
- `GET /api/incidents/{incidentId}` returns the full incident detail model
- `GET /api/incidents/{incidentId}/stream` streams incident events over SSE
- `POST /api/incidents/{incidentId}/decision` records approve/reject/escalate decisions
- `POST /api/incidents/{incidentId}/analysis/retry` re-queues the latest analysis for the same incident
- `GET /api/contracts` exposes the shared stage contracts and scenario catalog

## Requirements

- Python 3.12+
- Redis for async analysis handoff

## Install

From `incident-api/`:

```bash
pip install -r requirements.txt
```

## Run locally

```bash
uvicorn app.main:app --reload
```

Run the command from inside `incident-api/`. The service is packaged so it can resolve `shared/` without launching from the repo root.

If you want to watch the queue flow end to end, keep the RAG service and frontend running too.

## Environment variables

- `SEVLENS_REDIS_URL` — Redis connection string
- `SEVLENS_ANALYSIS_REQUEST_STREAM` — request stream name
- `SEVLENS_ANALYSIS_RESULT_STREAM` — result stream name
- `SEVLENS_ANALYSIS_RESULT_GROUP` — consumer group for result handling
- `SEVLENS_SYNC_ANALYSIS_FALLBACK` — enable the synchronous compatibility path

## Notes

- The service stays FastAPI-first and is intentionally runnable on its own.
- It owns the canonical incident data model and shared contract registry for the incident-side flow.
- The demo trigger endpoint creates seeded scenario incidents immediately and queues analysis in the background.
- The replayable timeline is built from persisted events, not from transient UI state.
- Any external incident manager can integrate by posting incidents into this service and letting SevLens continue the workflow.
