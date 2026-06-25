# SevLens V1 Stage Tracker

This document is the source of truth for the V1 rollout plan, current stage, what has been implemented, what comes next, and any design fixes we agree on along the way.

## Current State

- **Current stage:** Closed
- **Implementation status:** V1 complete and archived
- **Design changes agreed so far:** FastAPI for both backend services; manual testing only; stage tracker is the source of truth; incident API uses a local SQLite-backed persistence layer for the V1 demo/runtime; shared incident/recommendation shapes are now DB-backed and exposed through the incident API; the recommendation schema itself is DB-backed; the incident API calls the RAG service synchronously when creating the seeded mock incident; both backend services are independently runnable from their own folders/venvs; `shared` resolves through each service's local startup bootstrap; both backend services allow the frontend origin via the shared CORS allowlist; RAG service uses local markdown/JSON data with optional Chroma-backed retrieval; local LLM testing uses Ollama through its native `/api/chat` endpoint; Ollama defaults now use `RAG_LLM_BASE_URL=http://localhost:11434/api` plus `RAG_LLM_MODEL=qwen3.5:4b`; the RAG service auto-loads its local `.env` file on startup; the service loads service-specific mock log/metric files with `-logs` and `-metrics` suffixes; the RAG service now emits targeted info logs for request receipt, context loading, retrieval count, prompt size, and LLM timing; the frontend theme now uses a light/dark token system with a warm mud-orange accent palette; the frontend now uses a routed page architecture with theme/layout/data contexts, a fully collapsible left nav that animates closed and open, the collapse/expand control located in the page header, dashboard and incidents as separate pages, incident detail on its own route, dashboard showing only charts and recent incidents, the incidents page handling search/filter controls, and the incident detail page placing the event chain next to the recommendation/decision stack; page headers are now plain inline bars rather than cards, with transparent icon buttons for sidebar toggle, back navigation, and theme switching; the sidebar is now a fixed page edge rail with a right border instead of being embedded in the main content container; dashboard charts now use multi-color, heatmap-like palettes rather than a monochrome accent; the frontend dashboard now includes Highcharts incident/event metrics plus recent incidents and live SSE-backed incident detail views on the incidents route; Stage 3 uses a balanced LLM scope where code handles retrieval/validation and the LLM handles synthesis; Stage 4 frontend tooling is configured for Node 20 with standard React/TypeScript interop and a CommonJS Tailwind config.

## Project-wide decisions

- The stage tracker is the source of truth for implementation.
- Both backend services are FastAPI-based.
- Manual testing is the default validation approach.
- The design document is advisory and may change as implementation decisions evolve.
- The incident API persists V1 incident data locally with SQLite for the current demo/runtime.
- Shared incident/recommendation contract values are stored in a DB-backed registry and exposed via the incident API.
- The recommendation schema is stored in the same DB-backed registry.
- Both backend services are independently runnable from their own folders and virtualenvs.
- Each backend service has a local startup bootstrap so `shared` resolves when launched from its own folder.
- Both backend services share the frontend CORS allowlist via `SEVLENS_CORS_ORIGINS`.
- The RAG service uses local markdown and JSON mock data, with Chroma as the vector-store option for retrieval.
- Local LLM testing uses Ollama by default through its native `/api/chat` endpoint and the `/api` base URL.
- The local Ollama timeout is intentionally generous so the larger RAG prompt has time to finish.
- The RAG service auto-loads its `.env` file from `rag-service/` before resolving LLM settings.
- Stage 3 uses a balanced LLM scope: code gathers context and validates output, while the LLM synthesizes the recommendation.
- Stage 4 frontend tooling uses a Node 20-compatible Vite setup with standard React/TypeScript interop.
- The incident API invokes the RAG service synchronously during seeded mock-incident creation.
- The first fully supported V1 scenario remains `notification-service` Kafka timeout.

## Stage 1 — Foundation and Incident Data Model

**Status:** Completed

**Goal:** Lay the groundwork for the V1 incident-response loop without building the full UI or analysis pipeline yet.

**What this stage covers:**

- Create the initial repo structure for frontend, incident API, rag service, and shared docs/data folders.
- Define the core incident data model and audit/event schema.
- Add the initial database migration(s) for incidents, events, recommendations, and decisions.
- Add the first mock incident scenario for notification-service Kafka timeout.
- Add the seed runbooks, RCAs, and mock operational data needed by the later stages.
- Establish the baseline service contracts and status values used across the app.

**Stage 1 deliverables:**

- Repository scaffolding aligned to the V1 architecture.
- Database schema for incident tracking and audit history.
- Mock data and seed documents for the first end-to-end scenario.
- A clear contract for incident status, event types, and decision types.

**Stage 1 exit condition:**

- We can represent a mock incident in the system shape described by the design doc, with the supporting data needed for analysis and retrieval work in later stages.

## Stage 2 — Incident API and Mock Incident Flow

**Status:** Completed

**Scope:** Build the FastAPI incident API, mock incident creation endpoint, incident listing/detail endpoints, SSE streaming, and decision storage.

## Stage 3 — RAG Service and Recommendation Pipeline

**Status:** Completed

**Scope:** Build the FastAPI analysis service, mock operational-data helpers, document ingestion, retrieval, and structured recommendation generation.

## Stage 4 — React Dashboard and Real-Time Timeline

**Status:** Completed

**Scope:** Build the dashboard, incident detail view, timeline rendering, recommendation panel, and human decision actions.

## Stage 5 — End-to-End Integration and Polish

**Status:** Completed

**Scope:** Wire the services together, refine any design mismatches, tighten the demo flow, and record any agreed changes to the original design.

## Stage Notes

- **Implementation notes:** Stage 2 implemented the mock incident endpoint, list/detail endpoints, SSE stream, and decision storage with `decided_by = demo-user`.
- **Stage 3 progress:** Analysis request/response contracts, local data loaders, retrieval, prompt assembly, and response normalization are in place.
- **Stage 3 progress:** The RAG service now defaults to local Ollama testing via the OpenAI-compatible chat endpoint.
- **Stage 4 progress:** Shared contract values are now DB-backed and available through the incident API.
- **Stage 4 progress:** React dashboard scaffold, API client, CORS support, SSE wiring, and the frontend build pipeline are in place.
- **Stage 5 progress:** The incident API now calls the RAG service when creating the seeded mock incident, and the recommendation is persisted back into the incident database.
- **Stage 5 progress:** The frontend now surfaces the DB-backed recommendation schema alongside the incident and event type registry.
- **Stage 5 progress:** The seeded mock incident now flows end to end through trigger, analysis, persistence, live timeline, and decision handling.
- **Stage 5 progress:** Both backend services now have service-local setup instructions and bootstrapped startup paths so they can run independently.
- **Stage 5 progress:** The frontend dashboard is summary-only with charts and recent incidents, and the incidents page provides search and filters before opening incident detail.
- **Stage 5 progress:** The sidebar now fully collapses away when closed, and the page header owns the collapse/expand control so the main content pane reclaims the available width.
- **Stage 5 progress:** The frontend is now split into routed pages with a reusable app shell and theme/layout/data contexts instead of keeping all behavior inside `App.tsx`.
- **Stage 5 progress:** The frontend production build passes under the Node 20 toolchain used for the Vite app.
- **Stage 5 progress:** The incident detail page now shows the event chain alongside the recommendation and decision area, with no duplicate incident metadata or standalone selected-event side panel.
- **Stage 5 progress:** Page headers are now plain inline bars, and the sidebar/back actions use compact icon buttons.
- **Stage 5 progress:** The sidebar now reads like a flat edge rail with a right border rather than a floating card.
- **Stage 5 progress:** The sidebar now sits outside the main content container as a fixed page-edge rail.
- **Stage 5 progress:** The header icon controls are now transparent wall-mounted buttons instead of card-like toggles.
- **Stage 5 progress:** Dashboard charts now use multi-color palettes with a heatmap-like feel instead of a single monochrome accent.
- **Closure note:** V1 is frozen as the baseline reference for the V2 handoff.
- **Design fixes:** Backend services are FastAPI; manual testing is the default; tracker overrides the design doc when they differ.
- **Next step after approval:** Begin V2 Stage 1 implementation from the V2 tracker.
