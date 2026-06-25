# RAG Service

FastAPI-based incident analysis and recommendation service for SevLens.

## Purpose

This service loads mock operational context, retrieves supporting docs, and produces structured analysis and recommendations.

## Source of Truth

- Active implementation plan: `SEVLENS_V2_STAGE_TRACKER.md`
- Closed V1 reference: `SEVLENS_V1_STAGE_TRACKER.md`

## Local setup

From `rag-service/`:

1. Create or activate the service virtualenv.
2. Install dependencies with `pip install -r requirements.txt`.
3. Start Redis and OpenSearch locally.
4. Run the API with `uvicorn app.main:app --reload`.
5. Run the worker with `python -m app.worker` in a separate terminal if you want async processing.

Run the command from inside `rag-service/`; no repo-root launch or `PYTHONPATH` setup is required.

## Local Ollama setup

For local testing, copy `rag-service/.env.example` to `.env` and keep:

- `RAG_LLM_PROVIDER=ollama`
- `RAG_LLM_BASE_URL=http://localhost:11434/api`
- `RAG_LLM_MODEL=qwen3.5:4b`

The service uses Ollama's native chat endpoint at `/api/chat`, while OpenAI-compatible providers can still use `/v1/chat/completions`.

If the first local generation is slow, increase `RAG_LLM_TIMEOUT_SECONDS` or warm up the model with a quick `curl` request first.

## Notes

- The service is FastAPI-based and runs independently from its own virtualenv.
- The code is split into `app/api/` for routes, `app/core/` for runtime bootstrap, and the existing service modules for analysis, retrieval, queueing, and storage.
- It uses local markdown mock data and seeds scenario log evidence into OpenSearch on startup.
- In V2 Stage 6, the worker still consumes `SEVLENS_ANALYSIS_REQUEST_STREAM` and now uses named internal tools for log search, metrics, deployment, service catalog, runbook, and RCA context.
- The synchronous `/analyze` endpoint remains available for the local compatibility path and for direct analysis testing.
- Direct `/analyze` requests now need `scenario_id` so the service can fetch the matching OpenSearch log evidence.
- End-to-end V2 handoff docs live in `docs/v2-architecture.md`, `docs/v2-demo-script.md`, `docs/v2-manual-checklist.md`, and `docs/v2-known-limitations-and-v3-plan.md`.
