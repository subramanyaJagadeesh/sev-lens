# SevLens V2 Stage Tracker

This document is the source of truth for the V2 rollout plan, current stage, what has been implemented, what comes next, and any design fixes we agree on along the way.

## Current State

* **Current stage:** V2 complete
* **Implementation status:** V2 complete
* **V1 status:** Complete
* **Main V1 limitation:** Incident analysis is still triggered synchronously when a mock incident is created.
* **V2 direction:** Make SevLens truly event-driven first, then add local observability-style log search and richer incident scenarios.

## V2 Goal

V2 should evolve SevLens from a synchronous mock incident assistant into an asynchronous event-driven incident analysis system.

The target V2 flow is:

```text
Incident created
→ analysis job is queued
→ analysis worker picks up the job
→ RAG pipeline analyzes incident
→ progress is written to the event timeline
→ recommendation is persisted
→ UI receives updates through SSE
→ user approves, rejects, or escalates
```

V2 should also introduce local OpenSearch-backed log search, but only after the async queue/worker flow is working.

## Project-wide V2 Decisions

* V2 should preserve the working V1 demo flow.
* The first major V2 change is replacing synchronous analysis with queued async analysis.
* Redis Streams is the recommended message queue for V2 because it is lightweight and easy to run locally.
* Kafka and Flink are deferred to V3.
* OpenSearch is the recommended local log-search backend for V2.
* Do not run both OpenSearch and Elasticsearch in V2; use OpenSearch only.
* OpenSearch should simulate ELK-style log search locally.
* V2 should keep mock metrics and deployment data simple.
* V2 should support multiple incident scenarios.
* The seeded scenario catalog now exposes multiple selectable incident types through the shared contract registry and the frontend trigger flow.
* The frontend should clearly show queued, analyzing, completed, and failed analysis states.
* Manual testing remains the default validation approach.
* Terminal analysis events should refresh the incident detail from the API so the UI never shows stale recommendation or status data.
* Failed analysis should show retry affordances instead of decision controls, and the incidents filter should derive severity choices from seeded contract-backed values.
* Evaluation metrics are stored per analysis run in SQLite and rendered back in the incident detail flow and dashboard charts.
* Human approval state should read as decision pending until a decision is stored, and completed analysis timelines should show finished instead of paused.

---

# V2 Stage 0 — Planning and V1 Baseline Review

**Status:** Completed

## Goal

Confirm the V1 baseline and define the V2 async architecture before making code changes.

## What this stage covers

* Review the current synchronous analysis flow.
* Identify where the incident API calls the RAG service directly.
* Decide the message queue boundary.
* Define what gets published when an incident is created.
* Confirm that V1 can still run end-to-end.
* Decide whether sync mode remains as a local fallback.

## Stage 0 deliverables

* Updated V2 tracker.
* Clear async boundary between incident creation and analysis.
* Decision on Redis Streams as the V2 queue.
* V1 regression checklist.
* Closed V1 tracker and updated repo-facing docs to point at V2.

## Stage 0 exit condition

* We know exactly how to replace the synchronous analysis call with a queued analysis job.

## Stage 0 notes

* V1 is frozen as the closed baseline reference.
* V2 is now the active rollout track in the main README and service READMEs.
* Redis Streams remains the recommended queue for Stage 1.

---

# V2 Stage 1 — Queue-Based Analysis Request Flow

**Status:** Completed

## Goal

Make incident creation non-blocking by publishing an analysis job to a message queue.

## What this stage covers

* Add Redis locally.
* Add an analysis request queue.
* When a mock incident is created, store the incident immediately.
* Publish an analysis request event.
* Return the incident response without waiting for the RAG service.
* Show the incident as queued in the UI.

## Stage 1 deliverables

* Redis added to local development setup.
* Incident API publishes analysis jobs.
* Incident status supports a queued state.
* UI can show that an incident is waiting for analysis.
* Existing V1 flow still works behind a fallback flag if needed.

## Stage 1 notes

* Incident creation now writes `QUEUED` and `ANALYSIS_QUEUED` records on the async path.
* The incident API now publishes an analysis request envelope to Redis Streams before returning.
* The synchronous compatibility path remains available behind `SEVLENS_SYNC_ANALYSIS_FALLBACK=true`.
* The frontend now treats queued incidents as a waiting state in the list, detail, and recommendation views.

## Stage 1 exit condition

* Creating a mock incident no longer waits for RAG analysis to complete.

---

# V2 Stage 2 — Analysis Worker

**Status:** Completed

## Goal

Create a worker that consumes queued analysis jobs and runs the existing RAG pipeline asynchronously.

## What this stage covers

* Add a separate analysis worker process.
* Worker reads analysis jobs from Redis Streams.
* Worker updates incident status to analyzing.
* Worker runs the existing RAG/recommendation pipeline.
* Worker persists recommendation results.
* Worker writes analysis timeline events.
* Worker marks the incident as recommendation ready or failed.

## Stage 2 notes

* The RAG service now runs a dedicated async worker entrypoint that consumes `SEVLENS_ANALYSIS_REQUEST_STREAM`.
* The worker publishes `ANALYZING`, `RECOMMENDATION_READY`, and `FAILED` result envelopes to `SEVLENS_ANALYSIS_RESULT_STREAM`.
* The incident API runs a background result consumer that persists recommendations and timeline events into SQLite.

## Stage 2 deliverables

* Analysis worker process.
* Async analysis pipeline.
* Timeline events generated by the worker.
* Failed analysis state.
* Recommendation persisted after worker completion.

## Stage 2 exit condition

* The full V1 demo works without the incident API calling the RAG service synchronously.

---

# V2 Stage 3 — Analysis Runs, Retry, and Replay

**Status:** Completed

## Goal

Make analysis attempts trackable and replayable.

## What this stage covers

* Add the idea of an analysis run.
* Track each analysis attempt separately.
* Store started/completed/failed status for each run.
* Add retry for failed analysis.
* Add replay for completed incidents.
* Allow the UI to show previous analysis runs.
* The persisted incident row must retain `metric_name`, `metric_value`, and `threshold_value` so analysis requests can be rebuilt without re-reading the seeded scenario file.

## Stage 3 deliverables

* Analysis run tracking.
* Retry analysis action.
* Replay analysis action.
* Incident detail shows active or latest analysis run.
* Timeline distinguishes between different analysis attempts.

## Stage 3 exit condition

* A user can trigger an incident, complete analysis, and then replay analysis as a new run.

---

# V2 Stage 4 — Multi-Scenario Incident Support

**Status:** Completed

## Goal

Expand beyond the single notification-service Kafka timeout scenario.

## What this stage covers

Add at least four supported scenarios:

1. Notification service Kafka timeout.
2. Database connection pool exhaustion.
3. API gateway latency spike.
4. Worker queue backlog.

Each scenario should have:

* incident payload
* mock metrics
* mock deployment/change context
* service catalog entry
* runbook
* RCA or historical incident note
* expected recommendation direction

## Stage 4 deliverables

* Scenario registry.
* Scenario selector in the UI.
* Four supported incident scenarios.
* Scenario-specific recommendations.
* Scenario-specific timeline events.

## Stage 4 exit condition

* User can trigger any of the four scenarios and get a distinct evidence-backed recommendation.

---

# V2 Stage 5 — Local OpenSearch Log Search

**Status:** Completed

## Goal

Replace the simple JSON log lookup with a local OpenSearch-backed log search system.

## What this stage covers

* Add OpenSearch locally.
* Add OpenSearch Dashboards optionally.
* Create a local log index.
* Seed logs for each scenario.
* Add a log search tool in the RAG service.
* Query logs by service, scenario, and time window.
* Return summarized log evidence to the recommendation pipeline.

## What this stage should not do

* Do not add real production log ingestion.
* Do not add Flink.
* Do not add Kafka.
* Do not send raw logs directly to the LLM.
* Do not run both Elasticsearch and OpenSearch.

## Stage 5 deliverables

* OpenSearch runs locally.
* Scenario logs are seeded into OpenSearch.
* RAG service fetches summarized logs from OpenSearch.
* Recommendations cite log summaries as evidence.

## Stage 5 exit condition

* For each incident scenario, the recommendation can include log evidence fetched from OpenSearch.

---

# V2 Stage 6 — Tool Layer Cleanup

**Status:** Completed

## Goal

Make the RAG service cleaner by organizing context gathering into named tools.

## What this stage covers

Create clean internal tools for:

* log search
* metrics lookup
* deployment/change lookup
* service catalog lookup
* runbook retrieval
* RCA retrieval
* recommendation evaluation

This does not need to be a fully autonomous agent yet. The flow can still be code-driven.

## Stage 6 deliverables

* Clear tool modules in the RAG service.
* Each tool returns structured context.
* Tool usage appears in timeline events.
* Tool failures degrade gracefully.

## Stage 6 notes

* The RAG pipeline now uses named internal tools for log search, metrics, deployments, service catalog, runbooks, and RCAs.
* The LLM still synthesizes recommendations; the code layer owns tool orchestration and structured context gathering.

## Stage 6 exit condition

* The RAG pipeline is easier to extend because each context source is isolated behind a tool-like interface.

---

# V2 Stage 7 — Evaluation Metrics

**Status:** Completed

## Goal

Add basic measurement so the system can be discussed as more than a demo.

## What this stage covers

Track:

* analysis latency
* retrieved document count
* expected document hit rate
* evidence count
* recommended action count
* confidence value
* human decision
* scenario type

## Stage 7 deliverables

* Evaluation result per analysis run.
* Scenario-level expected documents/actions.
* Evaluation panel in incident detail.
* Dashboard charts for latency, approvals, and retrieval quality.

## Stage 7 exit condition

* Each analysis run has measurable quality and latency metadata.

## Stage 7 notes

* Each analysis run now persists a lightweight evaluation record alongside the incident data.
* The incident detail page shows run-level evaluation fields, and the dashboard charts latency and hit-rate trends from completed runs.

---

# V2 Stage 8 — Frontend V2 Updates

**Status:** Completed

## Goal

Update the UI to make the V2 async and multi-scenario behavior visible.

## What this stage covers

* Scenario dropdown.
* Queued/analyzing/completed/failed states.
* Analysis run selector.
* Retry and replay buttons.
* OpenSearch log evidence display.
* Tool/context panel.
* Evaluation panel.
* Dashboard charts for V2 metrics.

## Stage 8 deliverables

* UI supports async analysis states.
* UI supports scenario selection.
* UI supports retry/replay.
* UI shows log evidence and evaluation metrics.
* UI remains clean and demo-friendly.

## Stage 8 notes

* The incident detail page now supports selecting analysis runs, showing the selected run timeline, and switching the recommendation/evidence/context view with that selection.
* The dashboard keeps the high-level summary focused while adding V2 latency and evidence-hit-rate charts.

## Stage 8 exit condition

* V2 can be demoed fully from the frontend without manually inspecting backend logs.

---

# V2 Stage 9 — End-to-End Polish and Documentation

**Status:** Completed

## Goal

Make V2 stable, explainable, and ready for a demo, blog, or paper direction.

## What this stage covers

* Manual regression testing.
* Fix broken edge cases.
* Improve loading/error states.
* Update README.
* Update architecture diagram.
* Add demo script.
* Document known limitations.
* Document V3 plan.
* Refactor the backend into clearer API/core/runtime layers.
* Replace the frontend's native dropdowns with a shared custom select component.

## Stage 9 deliverables

* Updated README.
* Updated architecture diagram.
* Updated tracker.
* Manual test checklist.
* V2 demo script.
* Known limitations section.
* Production-shaped backend folder structure and shared frontend select component.

## Stage 9 exit condition

* V2 is demo-ready and can be presented as an event-driven incident intelligence system.

## Stage 9 notes

* The incident API now boots through `app/api/app.py` with a thin `app/main.py` wrapper.
* The RAG service now boots through `app/api/app.py` with a thin `app/main.py` wrapper.
* Shared dropdowns in the frontend now use a reusable custom select component for scenario, status, severity, and analysis-run selection.
* The service READMEs now describe the layered API/core bootstrap structure so the repo layout matches the implementation.
* The Stage 9 handoff docs now include an architecture diagram, demo script, manual checklist, and known-limitations/V3 plan.

---

# Recommended V2 Build Order

Build in this order:

```text
Stage 0 — Planning and V1 baseline review
Stage 1 — Queue-based analysis request flow
Stage 2 — Analysis worker
Stage 3 — Analysis runs, retry, and replay
Stage 4 — Multi-scenario incident support
Stage 5 — Local OpenSearch log search
Stage 6 — Tool layer cleanup
Stage 7 — Evaluation metrics
Stage 8 — Frontend V2 updates
Stage 9 — End-to-end polish and documentation
```

The key ordering decision is:

```text
Queue and worker first.
OpenSearch second.
Kafka/Flink later.
```

---

# V2 Acceptance Criteria

V2 is complete when:

1. Incident creation no longer blocks on RAG analysis.
2. Analysis jobs are queued.
3. A worker consumes analysis jobs asynchronously.
4. SSE timeline still updates as analysis progresses.
5. Failed analysis can be retried.
6. Completed analysis can be replayed.
7. At least four incident scenarios are supported.
8. OpenSearch is running locally and stores seeded logs.
9. Recommendations can include OpenSearch-backed log evidence.
10. Each analysis run has basic evaluation metrics.
11. The frontend shows scenario, queue state, analysis runs, log evidence, and evaluation.

---

# V2 One-Line Pitch

**SevLens V2 converts the V1 synchronous incident assistant into a true event-driven incident intelligence system with queued analysis, async workers, replayable runs, multi-scenario support, and local OpenSearch-backed log evidence.**

---

# V3 Preview

V3 can focus on real ingestion and production-style observability:

* Kafka event bus.
* Flink stream aggregation.
* Prometheus/Grafana integration.
* OpenTelemetry traces.
* Real alert ingestion.
* Slack/PagerDuty integration.
* Service dependency graph.
* Kubernetes deployment.
* Auth and RBAC.
* Dead-letter queues and production retry policies.
