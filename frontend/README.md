# SevLens Frontend

This package contains the React dashboard and incident console for SevLens.

## What it does

- shows the incident dashboard and seeded trend charts
- lists incidents and opens incident detail views
- streams incident timeline updates over SSE
- supports decisions, retries, and analysis run selection
- exposes the Knowledge Base and RCA Memory screens

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

