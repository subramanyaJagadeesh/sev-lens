# SevLens

SevLens is an open-source incident intelligence demo for exploring how an incident console, async analysis pipeline, knowledge base, and RCA memory can work together in one local-first product.

It ships with:

- a React dashboard for incidents, trends, knowledge, and RCA memory
- a FastAPI incident API that owns incident state and event history
- a FastAPI RAG/analysis service that retrieves evidence and produces recommendations
- Redis Streams for async request/result handoff
- local knowledge, RCA, and log evidence stores for repeatable demo runs

## Why this repo exists

SevLens is designed as a reusable reference implementation for incident workflows:

- trigger a seeded incident
- stream the evolving timeline
- inspect evidence, recommendations, and analysis runs
- capture decisions and feedback
- browse the knowledge base and RCA memory behind the analysis

The codebase is intentionally stage-driven so the roadmap, runtime behavior, and documentation stay aligned.

## Requirements

- **Node.js 20+** for the frontend
- **Python 3.12+** for the backend services
- **Redis** for async analysis handoff
- **OpenSearch** for local log evidence search
- Optional: **Ollama** or an OpenAI-compatible LLM endpoint for local analysis

## Repository layout

- `frontend/` — React dashboard and incident console
- `incident-api/` — FastAPI incident system of record
- `rag-service/` — FastAPI RAG, knowledge base, RCA memory, and worker logic
- `shared/` — shared contracts, scenario metadata, and seed data
- `docs/` — demo notes, architecture docs, and seeded content

## Quick start

### 1) Install dependencies

From the repo root:

```bash
cd frontend && npm install
cd ../incident-api && pip install -r requirements.txt
cd ../rag-service && pip install -r requirements.txt
```

### 2) Start infrastructure

Run Redis and OpenSearch locally before starting the backend services.

### 3) Start the services

Open three terminals:

```bash
# terminal 1
cd incident-api
uvicorn app.main:app --reload
```

```bash
# terminal 2
cd rag-service
uvicorn app.main:app --reload
python -m app.worker
```

```bash
# terminal 3
cd frontend
npm run dev
```

## Environment variables

### Frontend

- `VITE_INCIDENT_API_BASE_URL` — incident API base URL
- `VITE_RAG_API_BASE_URL` — RAG service base URL

### Incident API

- `SEVLENS_REDIS_URL` — Redis connection string
- `SEVLENS_ANALYSIS_REQUEST_STREAM` — async request stream
- `SEVLENS_ANALYSIS_RESULT_STREAM` — async result stream
- `SEVLENS_ANALYSIS_RESULT_GROUP` — result consumer group
- `SEVLENS_SYNC_ANALYSIS_FALLBACK` — local synchronous fallback toggle

### RAG service

- `RAG_LLM_PROVIDER` — `ollama` or `openai`
- `RAG_LLM_BASE_URL` — LLM API base URL
- `RAG_LLM_MODEL` — model name
- `KNOWLEDGE_BACKEND` — local knowledge backend selector
- `SEVLENS_EMBEDDING_PROVIDER` — embedding provider selector

## Current capabilities

- seeded mock incidents with real-time SSE updates
- async analysis with worker handoff
- persisted analysis runs and decision history
- knowledge base documents with retrieval preview
- RCA memory browsing and feedback
- OpenSearch-backed log evidence

## Source of truth

- Active roadmap: `SEVLENS_V3_STAGE_TRACKER.md`
- Frozen V2 baseline: `SEVLENS_V2_STAGE_TRACKER.md`
- Closed V1 baseline: `SEVLENS_V1_STAGE_TRACKER.md`

## Documentation

- `docs/v2-architecture.md`
- `docs/v2-demo-script.md`
- `docs/v2-manual-checklist.md`
- `docs/v2-known-limitations-and-v3-plan.md`

## Contributing

This repository is organized to stay easy to reuse:

- keep shared contracts in `shared/`
- keep service entrypoints thin
- prefer explicit stage-tracked changes
- update the relevant README when service behavior changes

