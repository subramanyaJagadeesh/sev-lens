# SevLens RAG Service

This service owns the investigation side of SevLens: retrieval, structured recommendation generation, knowledge management, RCA memory, and the worker that processes queued incidents.

## What it does

- runs the `/analyze` API and the background worker
- retrieves context from the local knowledge base, RCA memory, metrics, and OpenSearch-backed log evidence
- generates structured recommendations and intermediate investigation events
- exposes Knowledge Base and RCA Memory management endpoints
- persists local KB metadata in SQLite and document chunks in the vector store
- records RCA feedback so historical matches can improve over time

## Why it exists

The incident API should stay focused on incident state. This service handles the heavier analysis work so the product can explain how it arrived at a recommendation instead of returning a black-box answer.

## Main features

- `/analyze` for direct analysis/testing and sync fallback
- worker support for async incident processing through Redis Streams
- Knowledge Base APIs for listing, creating, editing, re-indexing, and searching docs
- RCA Memory APIs for browsing similar incidents and saving helpful/not-helpful feedback
- OpenSearch log search for scenario-specific and service-specific evidence
- embedding and knowledge backend abstractions so storage can evolve without changing the API

## Requirements

- Python 3.12+
- Redis for async worker communication
- OpenSearch for log evidence search
- Optional: Ollama or another OpenAI-compatible LLM provider

## Install

From `rag-service/`:

```bash
pip install -r requirements.txt
```

## Run locally

Start the API:

```bash
uvicorn app.main:app --reload
```

Start the worker in a second terminal:

```bash
python -m app.worker
```

Run both commands from inside `rag-service/` so the package resolves `shared/` without a repo-root launch.

If you are testing local AI behavior, point `RAG_LLM_PROVIDER` at either `openai` or `ollama` before starting the API.

## Environment variables

### LLM

- `RAG_LLM_PROVIDER` — `ollama` or `openai`
- `RAG_LLM_BASE_URL` — provider base URL
- `RAG_LLM_MODEL` — model name
- `RAG_LLM_TIMEOUT_SECONDS` — request timeout

### Knowledge and embeddings

- `KNOWLEDGE_BACKEND` — `local` or reserved `dify`
- `SEVLENS_EMBEDDING_PROVIDER` — embedding provider selector

### Infrastructure

- `SEVLENS_REDIS_URL` — Redis connection string
- `SEVLENS_LOG_INDEX` — OpenSearch index name for log evidence
- `SEVLENS_KB_DB_PATH` — local SQLite path for KB metadata

## Notes

- The service keeps the knowledge backend and embedding provider behind explicit interfaces so the implementation can evolve without changing the API contract.
- Local knowledge documents and RCAs are persisted; they are not in-memory-only demo data.
- OpenSearch is the only log search backend for the current V3 flow.
- The synchronous `/analyze` endpoint remains available for direct testing and compatibility.
- The worker emits step-level investigation events so the incident detail page can show how a recommendation was assembled.
