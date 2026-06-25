# Frontend

React dashboard for SevLens.

## Purpose

This app provides the incident dashboard, incidents list, and incident detail views for the current V2 track.

## Source of Truth

- Active implementation plan: `SEVLENS_V2_STAGE_TRACKER.md`
- Closed V1 reference: `SEVLENS_V1_STAGE_TRACKER.md`

## Local Development

From `frontend/`:

1. Install dependencies.
2. Run the dev server with Vite.
3. Use the configured Node 20 toolchain for builds.

The frontend uses React Router, context-based theme/layout/data state, and talks to the local incident API.
In V2 Stage 4 it includes a scenario selector for creating the seeded incidents and still shows queued incidents immediately while analysis is waiting on the Redis-backed async flow.
In V2 Stage 9 the shared dropdowns were replaced with a reusable custom select component so the dashboard, filters, and analysis-run controls share the same styling and behavior.
