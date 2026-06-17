# Frontend

React dashboard for OpsPulse.

## Purpose

This app provides the incident dashboard, incidents list, and incident detail views for the current V2 track.

## Source of Truth

- Active implementation plan: `OPSPULSE_V2_STAGE_TRACKER.md`
- Closed V1 reference: `OPSPULSE_V1_STAGE_TRACKER.md`

## Local Development

From `frontend/`:

1. Install dependencies.
2. Run the dev server with Vite.
3. Use the configured Node 20 toolchain for builds.

The frontend uses React Router, context-based theme/layout/data state, and talks to the local incident API.
