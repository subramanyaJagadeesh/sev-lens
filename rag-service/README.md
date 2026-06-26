# SevLens RAG Service

This service owns analysis, retrieval, knowledge management, RCA memory, and the worker side of async incident processing.

## What it does

- runs the analysis API and the background worker
- retrieves context from the local knowledge base and RCA memory
- searches OpenSearch for log evidence
- generates structured recommendations
- exposes KB and RCA management endpoints

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

