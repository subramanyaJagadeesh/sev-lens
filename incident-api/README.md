# Incident API

FastAPI-based incident system of record for OpsPulse.

## Purpose

This service owns incident persistence, incident detail APIs, SSE streaming, and decision storage.

## Source of Truth

- Active implementation plan: `OPSPULSE_V2_STAGE_TRACKER.md`
- Closed V1 reference: `OPSPULSE_V1_STAGE_TRACKER.md`

## Local setup

From `incident-api/`:

1. Create or activate the service virtualenv.
2. Install dependencies with `pip install -r requirements.txt`.
3. Run the service with `uvicorn app.main:app --reload`.

Run the command from inside `incident-api/`; no repo-root launch or `PYTHONPATH` setup is required.

## Notes

- The service is FastAPI-based and runs independently from its own virtualenv.
- It uses the shared contract registry and local mock data under `shared/`.
- In V2, this service will become the producer/consumer boundary for async analysis work.
