# SevLens V3 Stage Tracker

This document is the source of truth for the SevLens V3 rollout plan, current stage, what has been implemented, what comes next, and any design fixes we agree on along the way.

---

## Current State

* **Current stage:** V3 Stage 7
* **Implementation status:** V3 Stages 5 and 6 complete
* **V1 status:** Complete
* **V2 direction:** Async queue-backed incident analysis, analysis worker, multi-scenario support, local OpenSearch-backed log evidence, retry/replay, and evaluation basics.
* **V3 direction:** Agentic RAG, local knowledge base, RCA memory, evidence-linked recommendations, post-incident learning, and richer product UI.
* **V4 direction:** Kafka, Flink, real telemetry ingestion, stream aggregation, and production-scale infrastructure.

---

## V3 Goal

V3 should evolve SevLens from an async incident recommendation system into an **Agentic RAG Incident Intelligence Platform**.

The target V3 flow is:

```text
Incident created
→ analysis worker starts investigation
→ LangGraph workflow classifies the incident
→ tools gather logs, metrics, deployments, service metadata, runbooks, and RCAs
→ knowledge base retrieves relevant operational docs
→ RCA memory finds similar historical incidents
→ agent generates hypotheses
→ verifier checks evidence against recommendations
→ UI shows investigation, evidence, RCA matches, service context, and next actions
→ human approves, rejects, escalates, or gives feedback
→ resolved incident can become a new RCA in the knowledge base
```

---

## Product Principle

V3 should make SevLens feel smarter and more useful, not just more distributed.

V3 should prioritize:

* better Agentic RAG
* better RCA retrieval
* better operational knowledge management
* better investigation visibility
* better UI surfaces
* better post-incident learning

V3 should not prioritize Kafka, Flink, or real-time telemetry ingestion. Those belong in V4.

---

## Project-Wide V3 Decisions

* V3 uses the V2 async worker architecture.
* V3 introduces LangGraph for the agentic investigation workflow.
* V3 builds a local SevLens knowledge base by default.
* Dify may be supported later as an optional knowledge backend, but not as the core SevLens brain.
* Knowledge retrieval should be abstracted behind a backend interface.
* Local KB is the default backend.
* RCA retrieval becomes a first-class feature.
* Recommendations should be linked to evidence.
* Agent steps should produce visible investigation outputs, not hidden reasoning.
* Resolved incidents should be convertible into draft RCAs.
* Human feedback should be captured for recommendations and retrieved knowledge.
* Kafka and Flink are deferred to V4.
* Auto-remediation is not part of V3.
* Manual testing remains the default validation approach.

---

# V3 Stage 0 — V2 Baseline and Intelligence Scope Review

**Status:** Complete

## Goal

Confirm that V2 is stable and define the V3 intelligence scope.

## What this stage covers

* Confirm the V2 async incident flow is the frozen baseline: queued creation, worker handoff, retry/replay, multi-scenario support, and OpenSearch-backed log evidence.
* Capture the V2 limitations that V3 is meant to address: seeded scenarios, local-first queueing, local KB/log backends, and manual validation.
* Finalize the V3 intelligence scope:
  * local knowledge base as the default backend
  * LangGraph as a controlled agentic workflow, not an uncontrolled agent
  * RCA memory as a first-class retrieval path
  * evidence-linked recommendations and visible investigation steps
  * Dify only as an optional future backend, not the core path
* Define the initial V3 workflow shape:
  * incident classifier
  * context collector
  * knowledge retriever
  * RCA retriever
  * hypothesis generator
  * evidence verifier
  * recommendation planner
  * response composer
* Keep the V2 handoff docs as the frozen baseline reference and point active rollout planning at this tracker.

## Stage 0 deliverables

* Updated V3 tracker.
* V2 limitation summary for the V3 handoff.
* Finalized V3 intelligence scope.
* Initial local knowledge base design.
* Initial LangGraph workflow design.
* V3 regression checklist for the Stage 0 baseline.

## Stage 0 exit condition

* The team agrees that V3 focuses on Agentic RAG, local knowledge base, RCA memory, richer UI, and post-incident learning.
* V2 is frozen as the stable baseline while V3 proceeds from this tracker.

## Stage 0 baseline notes

* V2 remains local-first and demo-oriented.
* V2 still depends on seeded scenarios and mock operational context.
* V2 still uses Redis Streams and OpenSearch as lightweight local infrastructure.
* V2 still relies on manual validation and locally configured LLM access.
* V3 begins with the intelligence and knowledge-systems problem, not production ingestion.

## Stage 0 regression checklist

* Trigger a seeded incident and confirm the queue/result handoff still completes.
* Confirm retry/replay still works on failed or completed incidents.
* Confirm multi-scenario incident creation still behaves as expected.
* Confirm OpenSearch-backed log evidence still appears in the current demo flow.
* Confirm the UI still reaches a stable incident detail state before any V3 work starts.

---

# V3 Stage 1 — Knowledge Backend Abstraction

**Status:** Complete

## Goal

Create a clean knowledge backend interface so SevLens can use a local KB now and optionally support Dify or other KB systems later.

## What this stage covers

Define a common interface for knowledge operations:

* add document
* list documents
* get document
* update document
* delete/archive document
* re-index document
* search knowledge
* retrieve by incident context
* retrieve by document type
* retrieve by service
* retrieve by tags

## Backend strategy

Default:

```text
KNOWLEDGE_BACKEND=local
```

Future optional:

```text
KNOWLEDGE_BACKEND=dify
```

V3 should only require the local backend.

## Stage 1 deliverables

* Knowledge backend interface.
* Local knowledge backend skeleton.
* Backend configuration flag.
* Shared knowledge document contract.
* Shared retrieval result contract.
* Analysis pipeline wired to the backend interface instead of direct storage helpers.

## Stage 1 exit condition

* The RAG pipeline can call a knowledge backend interface without knowing whether the backend is local or external.
* The local backend is the default path, and a future backend can be swapped in without changing the analysis flow.

---

# V3 Stage 2 — Local Knowledge Base

**Status:** Complete

## Goal

Build a local incident-focused knowledge base for operational documents.

## What this stage covers

Support these document types:

1. Runbooks.
2. RCAs.
3. SOPs.
4. Escalation policies.
5. Service ownership docs.
6. Architecture notes.
7. Troubleshooting guides.
8. Known error notes.

The local KB should support:

* create document from UI text input
* upload or seed markdown/text documents
* list documents
* view document
* update document metadata
* archive/delete document
* re-index document
* chunk document
* embed chunks
* store chunk metadata
* search by query
* filter by service, document type, severity, and tags
* persist document metadata and chunk embeddings across restarts

## Recommended V3 storage

Use the current local stack where possible:

* SQLite or the current local DB for document metadata.
* Chroma or existing vector store for embeddings.
* Markdown/text as the first supported content format.

Do not add PDF/DOCX parsing yet unless everything else is complete.

## Stage 2 deliverables

* Local knowledge document model.
* Local chunk metadata model.
* Ingestion pipeline for markdown/text.
* Embedding/indexing pipeline.
* Knowledge search API.
* At least 20 seeded documents across runbooks, RCAs, SOPs, service docs, and known-error notes.
* Persistent local metadata storage and vector retrieval backed by SQLite + Chroma.

## Stage 2 exit condition

* A user can add or seed operational knowledge documents, and the system can retrieve relevant chunks with metadata filters from the persisted local KB.

---

# V3 Stage 3 — Knowledge Base UI

**Status:** Complete

## Goal

Add product screens for managing and inspecting the local knowledge base.

## What this stage covers

Add a **Knowledge Base** section in the UI.

Required screens:

1. **Knowledge List**

   * title
   * document type
   * service
   * tags
   * indexing status
   * updated time

2. **Knowledge Detail**

   * metadata
   * raw content
   * chunks
   * linked incidents
   * indexing state

3. **Add Knowledge**

   * title
   * document type
   * service
   * tags
   * severity relevance
   * content textarea
   * save and index action

4. **Retrieval Preview**

   * test a query against the KB
   * show retrieved chunks
   * show source documents
   * show scores and metadata

## Stage 3 deliverables

* Knowledge Base navigation item.
* Knowledge list page.
* Knowledge detail page.
* Add/edit knowledge screen.
* Retrieval preview panel.
* Re-index action.
* Embedding provider abstraction so the knowledge backend delegates vector generation to a provider module instead of embedding inline.

## Stage 3 implementation notes

* The RAG service now exposes persisted knowledge endpoints for list, detail, create, update, archive, re-index, and retrieval preview.
* Embedding generation moved behind a provider module so the local knowledge backend owns persistence and retrieval orchestration, not vectorization logic.
* The shared runtime now holds one configured knowledge backend instance so analysis and the upcoming UI use the same persisted KB view.

## Stage 3 exit condition

* A user can create, inspect, search, and re-index knowledge documents from the UI.

## Stage 3 completion notes

* Added a routed **Knowledge Base** section in the frontend with list, detail, add/edit, and retrieval preview flows.
* Exposed persisted KB management endpoints from the RAG service for list, detail, create, update, archive, re-index, and retrieval preview.
* Moved embedding generation behind a provider module so the local knowledge backend delegates vectorization through a clean interface.

---

# V3 Stage 4 — RCA Memory and Similar Incident Retrieval

**Status:** Complete

## Goal

Make RCA retrieval a first-class capability.

SevLens should not only retrieve generic runbooks. It should find similar historical incidents and explain why they match.

## What this stage covers

* Store RCA documents as structured incident memories.
* Extract or capture RCA metadata:

  * affected service
  * severity
  * symptoms
  * root cause
  * resolution
  * prevention items
  * related errors
  * related dependencies
  * incident date
* Retrieve similar RCAs using incident context.
* Explain why each RCA matched.
* Use RCA matches in recommendations.
* Allow users to mark RCA matches as helpful or not helpful.

## Stage 4 deliverables

* RCA memory model.
* Similar RCA retrieval.
* RCA match explanation.
* RCA match feedback.
* RCA memory screen.
* RCA match panel inside incident detail.

## Stage 4 exit condition

* For any supported incident scenario, SevLens can show similar historical RCAs and use them to improve the recommendation.

## Stage 4 completion notes

* Added structured RCA memory contracts and persisted RCA feedback in the RAG service.
* Extended RCA ingestion so seeded RCA markdown docs are stored as first-class RCA memory records.
* Added RCA retrieval with match explanations and relevance scores, and fed those matches into the analysis pipeline context.
* Added an RCA memory browse page in the frontend and an RCA match panel in incident detail for feedback capture.

---

# V3 Stage 5 — LangGraph Agentic Investigation Workflow

**Status:** Complete

## Goal

Move from a linear RAG pipeline to a structured agentic investigation workflow.

This should be a controlled workflow, not an uncontrolled autonomous agent.

## What this stage covers

Introduce a LangGraph workflow with the following investigation steps:

1. **Incident Classifier**

   * classify incident type, service, severity, and likely category.

2. **Context Collector**

   * gather logs, metrics, deployment context, service metadata, ownership, and dependency hints.

3. **Knowledge Retriever**

   * retrieve runbooks, SOPs, service docs, and troubleshooting guides.

4. **RCA Retriever**

   * retrieve similar historical incidents and RCA memories.

5. **Hypothesis Generator**

   * generate possible root-cause hypotheses.

6. **Evidence Verifier**

   * check which hypotheses are supported by logs, metrics, RCAs, and docs.

7. **Recommendation Planner**

   * generate actions with evidence and risk level.

8. **Response Composer**

   * create the final operator-facing recommendation.

## Stage 5 deliverables

* LangGraph workflow implementation.
* Step-level outputs.
* Step-level timeline events.
* Workflow state model.
* Clear separation between symptoms, evidence, hypotheses, and actions.
* Fallback path if one step fails.

## Stage 5 exit condition

* Incident analysis shows a transparent multi-step investigation workflow instead of a single one-shot RAG response.

## Stage 5 completion notes

* Replaced the linear analysis path with a LangGraph-backed investigation workflow that emits classification, planner, context, retrieval, hypothesis, verification, planning, and response events.
* Added an LLM planner loop so the graph can decide whether to collect more context, retrieve more KB/RCA evidence, or stop and synthesize.
* Kept the existing analysis boundary stable while expanding the result payload with structured workflow state, planner decisions, and step outputs.
* Added a controlled fallback at the synthesis layer so partial evidence can still produce a recommendation and timeline for the incident.
* Reclassified the remaining product-facing surface work into Stage 7 so the investigation experience can be finished as a cohesive screen.

---

# V3 Stage 6 — Evidence-Linked Recommendation Model

**Status:** Complete

## Goal

Make every recommendation explainable by linking actions to evidence.

## What this stage covers

Create a recommendation model that separates:

* incident summary
* symptoms
* evidence
* hypotheses
* recommended actions
* risk level
* confidence
* required approval
* source documents
* similar RCAs
* unsupported or low-confidence areas

Each recommended action should link back to one or more evidence items.

Example:

```text
Action:
Scale notification workers from 4 to 8.

Supported by:
- Kafka consumer lag increased from 120 to 18,450.
- KafkaTimeoutException appeared 842 times.
- Similar RCA resolved issue by scaling workers.
- Kafka Consumer Lag Runbook recommends scaling consumers.
```

## Stage 6 deliverables

* Evidence model.
* Hypothesis model.
* Evidence-to-action links.
* Updated recommendation schema.
* Updated incident detail recommendation UI.
* Clear low-confidence/unsupported evidence section.

## Stage 6 exit condition

* A user can understand why each recommendation was made without reading hidden model reasoning.

## Stage 6 completion notes

* Added structured recommendation fields for incident summary, symptoms, evidence, hypotheses, actions, confidence, risk, source documents, similar RCAs, and unsupported areas.
* Linked recommendation actions to evidence-backed source material and surfaced that shape in the incident detail UI.
* Reworked the recommendation panel presentation so the structured payload reads cleanly and can be extended by the Investigation View in Stage 7.

---

# V3 Stage 7 — Investigation View

**Status:** In progress

## Goal

Add a richer incident investigation screen that uses the information produced by the agentic workflow and absorbs the remaining investigation/recommendation presentation work that was reclassified from Stages 5 and 6.

## What this stage covers

Add an **Investigation View** for each incident.

The screen should show:

* investigation steps
* collected context
* retrieved runbooks
* similar RCAs
* hypotheses
* evidence verification
* recommendation plan
* final response
* source links
* confidence/risk indicators
* recommendation presentation polish carried forward from Stage 6
* the remaining evidence/action storytelling surface for the LangGraph workflow

Possible UI formats:

* evidence chain
* step-by-step investigation timeline
* grouped cards by agent step
* evidence-to-action map
* lightweight graph view if practical

## Stage 7 deliverables

* Investigation View route.
* Agent step cards.
* Evidence panel.
* Hypothesis panel.
* Retrieved knowledge panel.
* RCA match panel.
* Action-to-evidence display.
* Final product-friendly recommendation presentation in the investigation screen.

## Stage 7 exit condition

* The UI exposes the full investigation process in a product-friendly way.

---

# V3 Stage 8 — Service Intelligence Screens

**Status:** Not Started

## Goal

Add service-level intelligence pages so SevLens is useful beyond individual incidents.

## What this stage covers

Create a **Services** section.

Each service detail page should show:

* service name
* owner/team
* criticality
* dependencies
* linked runbooks
* linked RCAs
* known errors
* recent incidents
* common symptoms
* common root causes
* recent recommendations
* documentation coverage

## Stage 8 deliverables

* Services list page.
* Service detail page.
* Service-to-document links.
* Service-to-RCA links.
* Service incident history.
* Common failure pattern summary.
* Documentation coverage card.

## Stage 8 exit condition

* A user can open a service and understand its operational history, knowledge coverage, and common failure patterns.

---

# V3 Stage 9 — Knowledge Gap Detection

**Status:** Not Started

## Goal

Use incident analysis to identify missing or weak operational documentation.

## What this stage covers

Detect cases such as:

* no runbook found for a service
* no similar RCA found
* runbook exists but does not mention observed error
* repeated incident has no prevention item
* recommendation confidence is low due to missing docs
* service has many incidents but poor documentation coverage

## Stage 9 deliverables

* Knowledge gap detection logic.
* Knowledge gap panel in incident detail.
* Knowledge gaps dashboard.
* Suggested runbook/RCA topics.
* Service-level documentation coverage score.

## Stage 9 exit condition

* SevLens can tell the user what operational knowledge is missing and suggest what to document next.

---

# V3 Stage 10 — RCA Draft Generation and Post-Incident Learning

**Status:** Not Started

## Goal

Close the loop after an incident by converting resolved incidents into reusable knowledge.

## What this stage covers

After an incident is resolved, SevLens should generate a draft RCA using:

* incident summary
* timeline events
* evidence
* hypotheses
* recommendation
* human decision
* resolution notes
* feedback
* related docs
* related services

RCA draft sections:

* incident summary
* impact
* timeline
* symptoms
* root cause hypothesis
* confirmed root cause
* resolution
* what went well
* what went wrong
* prevention items
* related runbooks
* related services

## Stage 10 deliverables

* RCA draft generator.
* RCA draft editing screen.
* Save RCA to knowledge base.
* Link RCA back to original incident.
* Re-index RCA after save.

## Stage 10 exit condition

* A resolved incident can become a searchable RCA in the SevLens knowledge base.

---

# V3 Stage 11 — Feedback and Quality Loop

**Status:** Not Started

## Goal

Capture human feedback to improve future recommendations and retrieval quality.

## What this stage covers

Capture feedback on:

* recommendation usefulness
* RCA match usefulness
* runbook usefulness
* incorrect hypothesis
* missing evidence
* risky action
* generic action
* correct action
* bad retrieval result

## Stage 11 deliverables

* Feedback buttons.
* Feedback notes.
* Feedback stored per recommendation, RCA match, and retrieved document.
* Evaluation page updated with feedback signals.
* Dashboard chart for recommendation usefulness and retrieval usefulness.

## Stage 11 exit condition

* SevLens can track which recommendations and retrieved knowledge were useful to humans.

---

# V3 Stage 12 — Product UI Expansion and Polish

**Status:** Not Started

## Goal

Turn SevLens from an incident detail demo into a broader incident intelligence product.

## UI sections by the end of V3

1. **Dashboard**

   * incident trends
   * recommendation outcomes
   * knowledge coverage
   * top risky services
   * recent RCA additions

2. **Incidents**

   * incident list
   * filters by service, severity, status, scenario, owner
   * incident detail
   * investigation view

3. **Knowledge Base**

   * docs
   * add/edit
   * retrieval preview
   * indexing status

4. **RCA Memory**

   * RCA list
   * RCA detail
   * similar incident search

5. **Services**

   * service list
   * service profile
   * linked docs
   * incident history
   * knowledge gaps

6. **Evaluation**

   * retrieval quality
   * recommendation usefulness
   * latency
   * approval/rejection/escalation rates

7. **Settings**

   * model provider
   * embedding provider
   * knowledge backend
   * retrieval mode
   * confidence thresholds

## Stage 12 deliverables

* Updated navigation.
* New routed pages.
* UI states for KB, RCA memory, services, investigation, feedback, and evaluation.
* Cleaner product-level dashboard.
* Demo-ready polish.

## Stage 12 exit condition

* V3 can be demoed as a full incident intelligence product, not just an incident recommendation page.

---

# V3 Stage 13 — Documentation, Demo, and Research Direction

**Status:** Not Started

## Goal

Package V3 as a strong portfolio, blog, and research project.

## What this stage covers

* Update README.
* Update architecture diagram.
* Add demo script.
* Add screenshots.
* Add known limitations.
* Add V4 plan.
* Write a technical blog outline.
* Write a paper direction outline.

## Suggested paper/blog title

**SevLens: Agentic RAG for Evidence-Grounded Incident Response and Post-Incident Learning**

## Core contribution

V3’s strongest contribution is not just RAG. It is:

* agentic investigation workflow
* local incident knowledge base
* RCA memory retrieval
* evidence-linked recommendations
* knowledge gap detection
* post-incident RCA generation loop

## Stage 13 deliverables

* Updated README.
* Updated architecture document.
* V3 demo script.
* Screenshots.
* Blog/paper outline.
* Known limitations.
* V4 infrastructure plan.

## Stage 13 exit condition

* V3 is ready to present as an Agentic RAG incident intelligence platform.

---

# Recommended V3 Build Order

Build in this order:

```text
Stage 0 — V2 baseline and intelligence scope review
Stage 1 — Knowledge backend abstraction
Stage 2 — Local knowledge base
Stage 3 — Knowledge base UI
Stage 4 — RCA memory and similar incident retrieval
Stage 5 — LangGraph agentic investigation workflow
Stage 6 — Evidence-linked recommendation model
Stage 7 — Investigation view
Stage 8 — Service intelligence screens
Stage 9 — Knowledge gap detection
Stage 10 — RCA draft generation and post-incident learning
Stage 11 — Feedback and quality loop
Stage 12 — Product UI expansion and polish
Stage 13 — Documentation, demo, and research direction
```

---

# V3 Acceptance Criteria

V3 is complete when:

1. SevLens has a local knowledge base for runbooks, RCAs, SOPs, service docs, escalation policies, architecture notes, troubleshooting guides, and known-error notes.
2. Users can add, view, search, tag, index, and re-index knowledge documents.
3. The RAG pipeline retrieves knowledge through a backend abstraction.
4. RCA retrieval is a first-class feature.
5. Similar RCA matches are visible and explainable.
6. LangGraph powers a structured agentic investigation workflow.
7. Agent steps produce visible investigation outputs.
8. Recommendations are linked to evidence.
9. Incident detail includes an investigation view.
10. Service pages show operational knowledge, incident history, common errors, and documentation coverage.
11. Knowledge gaps are detected and displayed.
12. Resolved incidents can generate draft RCAs.
13. RCA drafts can be saved back into the knowledge base.
14. Human feedback is captured for recommendations and retrieved knowledge.
15. The UI has multiple product screens beyond dashboard and incident detail.
16. Kafka and Flink remain deferred to V4.

---

# V3 One-Line Pitch

**SevLens V3 transforms the system from an async incident assistant into an Agentic RAG incident intelligence platform with local knowledge management, RCA memory, evidence-linked recommendations, service intelligence, and post-incident learning.**

---

# V4 Preview

V4 should focus on scalable ingestion and production infrastructure.

V4 can add:

* Kafka event backbone.
* Flink stream aggregation.
* Real alert ingestion.
* Real telemetry ingestion.
* Prometheus/Grafana integration.
* OpenTelemetry traces.
* Service dependency graph from live metadata.
* Slack/PagerDuty integrations.
* Kubernetes deployment.
* Production retries, DLQs, and worker scaling.
* Auth and RBAC.

V4 target flow:

```text
Logs / metrics / traces / deployment events
→ Kafka
→ Flink aggregation
→ incident candidate generation
→ SevLens analysis queue
→ Agentic RAG investigation
→ human-approved response
```
