# SevLens V2 Manual Checklist

Use this checklist to sanity-check the current demo build.

## Incident flow

- Trigger a seeded mock incident.
- Confirm the incident appears immediately in the list.
- Confirm the incident detail page opens without errors.
- Confirm queued/analyzing/ready/failed states render clearly.

## Analysis runs

- Confirm a single-run incident does not show the analysis-run picker.
- Confirm multi-run incidents show the run selector.
- Confirm the selected run updates the timeline, evidence, and evaluation panels.
- Confirm retry creates a new run on failed incidents.

## Timeline and decisions

- Confirm SSE updates append to the timeline in order.
- Confirm finished runs show a finished timeline state.
- Confirm the decision state reads as decision pending until a decision is recorded.
- Confirm approve/reject/escalate updates the incident state and audit history.

## UI polish

- Confirm the sidebar collapses and expands cleanly.
- Confirm the light/dark theme toggle still works.
- Confirm the shared custom select renders properly in all dropdown locations.
- Confirm long recommendation and evidence text wraps without overflowing.

## Backend/runtime

- Confirm the incident API starts from `incident-api/` and the RAG service starts from `rag-service/`.
- Confirm the worker can be started independently.
- Confirm the frontend build passes under the Node 20 toolchain.
