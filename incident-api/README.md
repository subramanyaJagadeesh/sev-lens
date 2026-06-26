# SevLens Incident API

This service is the incident system of record for SevLens.

## What it does

- persists incidents, events, decisions, and analysis runs
- exposes list/detail/decision APIs
- streams incident updates over SSE
- publishes analysis jobs to Redis Streams
- applies worker results back into SQLite and the live event timeline

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

## Environment variables

- `SEVLENS_REDIS_URL` — Redis connection string
- `SEVLENS_ANALYSIS_REQUEST_STREAM` — request stream name
- `SEVLENS_ANALYSIS_RESULT_STREAM` — result stream name
- `SEVLENS_ANALYSIS_RESULT_GROUP` — consumer group for result handling
- `SEVLENS_SYNC_ANALYSIS_FALLBACK` — enable the synchronous compatibility path

## Notes

- The service stays FastAPI-first and is intentionally runnable on its own.
- It owns the canonical incident data model and shared contract registry for the incident-side flow.
- The mock incident endpoint creates the seeded scenario incidents immediately and queues analysis in the background.
- The replayable timeline is built from persisted events, not from transient UI state.

