# SevLens AI

SevLens AI is a stage-driven incident response demo.

## Current Focus

- **V1:** complete and preserved as the baseline reference.
- **V2:** complete and documented.
- V2 Stage 1 introduced Redis-backed async incident creation between the incident API and RAG flow.
- V2 Stage 2 added the async worker/result handoff between the RAG service and the incident API.
- V2 Stage 4 expands the seeded demo into a multi-scenario incident catalog with a scenario selector in the UI.
- V2 Stage 5 adds local OpenSearch-backed log search for scenario evidence.
- V2 Stage 6 is refactoring the RAG side into explicit tools for each context source.
- V2 Stage 9 completed the final cleanup and documentation pass, including the custom select and production-shaped service layers.

## Sources of Truth

- The working source of truth for the current implementation is `SEVLENS_V2_STAGE_TRACKER.md`.
- `SEVLENS_V1_STAGE_TRACKER.md` documents the closed V1 implementation and decisions.

## What This Repo Contains

- A FastAPI incident API.
- A FastAPI RAG/analysis service.
- A React frontend dashboard.
- Layered service packages for API routes, runtime bootstrap, and reusable application modules.
- Shared contracts, mock data, and stage-tracked implementation notes.

## V2 Handoff Docs

- Architecture diagram: `docs/v2-architecture.md`
- Demo script: `docs/v2-demo-script.md`
- Manual checklist: `docs/v2-manual-checklist.md`
- Known limitations and V3 direction: `docs/v2-known-limitations-and-v3-plan.md`
