# SevLens Frontend

This package contains the React dashboard and incident console for SevLens.

## What it does

- shows the incident dashboard and seeded trend charts
- lists incidents and opens incident detail views
- streams incident timeline updates over SSE
- supports decisions, retries, and analysis run selection
- exposes the Knowledge Base and RCA Memory screens
- gives the user a single place to inspect evidence, recommendations, and feedback

## Why it exists

The frontend is the operator surface for SevLens. It is built to make the investigation legible: what happened, what the system found, what evidence it used, and how the team responded.

## Main screens

- `Dashboard` shows top-level incident counts, status spread, trend charts, and recent incidents
- `Incidents` lets you search, filter, and trigger a demo incident for the current scenario catalog
- `Incident detail` shows the live SSE timeline, recommendation, RCA memory, log evidence, tool context, and decision actions
- `Knowledge Base` lets you add, edit, archive, re-index, and preview retrieval for docs
- `Knowledge detail` shows stored chunks, metadata, and RCA-linked content
- `RCA Memory` lets you browse historical incident memories and review helpful/not-helpful feedback

## Requirements

- Node.js 20+
- npm

## Install

From `frontend/`:

```bash
npm install
```

## Run locally

```bash
npm run dev
```

The dev server expects the backend services to be running:

- `VITE_INCIDENT_API_BASE_URL` defaults to `http://localhost:8000`
- `VITE_RAG_API_BASE_URL` defaults to `http://localhost:8001`

## Build

```bash
npm run build
```

## Notes

- The app uses React Router, shared contexts for layout/theme/data, and a reusable custom select component.
- The sidebar is collapsible and the page header includes shared back/theme controls.
- The frontend is intentionally data-driven so it can reuse the same incident and knowledge contracts as the backend services.
- The charts use Highcharts and the incident detail page updates live from SSE, so refreshes and streamed updates should stay in sync.
