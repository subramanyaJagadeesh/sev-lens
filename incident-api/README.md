# Incident API

FastAPI-based incident system of record for SevLens.

## Purpose

This service owns incident persistence, incident detail APIs, SSE streaming, decision storage, and V2 queue publication.

## Source of Truth

- Active implementation plan: `SEVLENS_V2_STAGE_TRACKER.md`
- Closed V1 reference: `SEVLENS_V1_STAGE_TRACKER.md`

## Local setup

From `incident-api/`:

1. Create or activate the service virtualenv.
2. Install dependencies with `pip install -r requirements.txt`.
3. Start Redis locally, or set `SEVLENS_SYNC_ANALYSIS_FALLBACK=true` for the synchronous compatibility path.
4. Run the service with `uvicorn app.main:app --reload`.

Run the command from inside `incident-api/`; no repo-root launch or `PYTHONPATH` setup is required.

## Notes

- The service is FastAPI-based and runs independently from its own virtualenv.
- The code is split into `app/api/` for routes, `app/core/` for runtime bootstrap, and the existing service modules for persistence, queueing, and analysis orchestration.
- It uses the shared contract registry and local mock data under `shared/`.
- The mock incident trigger now resolves against the shared scenario registry so the frontend can select between multiple seeded incidents.
- In V2 Stage 1, this service publishes analysis jobs to Redis Streams and returns queued incidents immediately.
- `SEVLENS_REDIS_URL` and `SEVLENS_ANALYSIS_REQUEST_STREAM` control the queue target.
- `SEVLENS_ANALYSIS_RESULT_STREAM` and `SEVLENS_ANALYSIS_RESULT_GROUP` control the worker result consumer.
- `SEVLENS_SYNC_ANALYSIS_FALLBACK=true` keeps a local synchronous path available for compatibility.
- The incident API now runs a background result consumer that applies worker output back into SQLite and SSE.
- End-to-end V2 handoff docs live in `docs/v2-architecture.md`, `docs/v2-demo-script.md`, `docs/v2-manual-checklist.md`, and `docs/v2-known-limitations-and-v3-plan.md`.
