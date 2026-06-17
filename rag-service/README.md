# RAG Service

FastAPI-based incident analysis and recommendation service for OpsPulse.

## Purpose

This service loads mock operational context, retrieves supporting docs, and produces structured analysis and recommendations.

## Source of Truth

- Active implementation plan: `OPSPULSE_V2_STAGE_TRACKER.md`
- Closed V1 reference: `OPSPULSE_V1_STAGE_TRACKER.md`

## Local setup

From `rag-service/`:

1. Create or activate the service virtualenv.
2. Install dependencies with `pip install -r requirements.txt`.
3. Run the service with `uvicorn app.main:app --reload`.

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
- It uses local markdown/JSON mock data and supports Ollama for local testing.
- V2 will shift the analysis trigger path to async queue consumption.
