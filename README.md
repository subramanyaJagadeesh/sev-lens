# SevLens

SevLens is an open-source incident intelligence system for showing how an incident console can do more than display alerts. It ties together incident intake, live timelines, retrieval, recommendations, RCA memory, and human decisioning in one local-first app.

## Why SevLens Exists

Most incident tools stop at the alert, dashboard, or ticket. SevLens shows the rest of the workflow:

- why an incident happened
- what evidence supports the recommendation
- how the analysis was assembled
- how past RCAs and internal docs can improve the next response
- how a team can review and override the recommendation when needed

That makes it useful as both a product demo and a reference architecture for organizations that already have incident management in place.

## What It Includes

- `Dashboard` for high-level incident and analysis trends
- `Incidents` list for searching, filtering, and opening active incidents
- `Incident detail` for the live timeline, recommendation, RCA memory, and decision flow
- `Knowledge Base` for managing runbooks, policies, and support docs
- `RCA Memory` for browsing historical incident memories and feedback
- `FastAPI incident-api` as the incident system of record
- `FastAPI rag-service` for retrieval, recommendations, knowledge, and RCA memory
- `Redis Streams` for async request/result handoff
- `OpenSearch` for local log evidence search

## How It Works

1. The incident API creates or accepts an incident and stores it in SQLite.
2. The incident is queued for analysis through Redis Streams.
3. The RAG service retrieves logs, runbooks, knowledge docs, and RCA memory.
4. The worker produces a recommendation and streams step-by-step events back.
5. The UI shows the investigation timeline, evidence, and decision controls.

The default demo flow uses seeded incidents, but any existing incident management system can post an incident into SevLens and let it continue the workflow.

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

### 4) Use the app

- Open the dashboard to see top-level metrics and recent incidents.
- Go to `Incidents` to trigger a seeded demo incident or inspect a live one.
- Open `Incident detail` to follow the timeline, recommendation, RCA matches, and decision history.
- Use `Knowledge Base` to add or edit docs the RAG flow can retrieve.
- Use `RCA Memory` to inspect historic incidents and feedback signals.

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
- local vector-backed KB persistence
- step-by-step investigation events in the incident timeline

## Source of truth

- Active roadmap: `SEVLENS_V3_STAGE_TRACKER.md`
- Frozen V2 baseline: `SEVLENS_V2_STAGE_TRACKER.md`
- Closed V1 baseline: `SEVLENS_V1_STAGE_TRACKER.md`

## Documentation

- `docs/v2-architecture.md`
- `docs/v2-demo-script.md`
- `docs/v2-manual-checklist.md`
- `docs/v2-known-limitations-and-v3-plan.md`

## License

This project is licensed under the Apache License 2.0. See the `LICENSE` file for details.

## Contributing

This repository is organized to stay easy to reuse:

- keep shared contracts in `shared/`
- keep service entrypoints thin
- prefer explicit stage-tracked changes
- update the relevant README when service behavior changes
