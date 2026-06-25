# SevLens V2 Demo Script

Use this script for a short end-to-end demo of the current V2 flow.

## 1) Start the services

Open four terminals:

```bash
# Terminal 1
cd incident-api
uvicorn app.main:app --reload
```

```bash
# Terminal 2
cd rag-service
uvicorn app.main:app --reload
```

```bash
# Terminal 3
cd rag-service
python -m app.worker
```

```bash
# Terminal 4
cd frontend
npm run dev
```

## 2) Trigger an incident

1. Open the frontend.
2. Go to **Incidents**.
3. Pick a seeded scenario.
4. Click **Trigger mock incident**.

## 3) Narrate the async flow

Call out what the audience should see:

- the incident appears immediately
- the incident starts in a queued or analyzing state
- the timeline fills as the worker progresses
- recommendation, evidence, and evaluation data appear once analysis completes

## 4) Show the decision path

1. Open the incident detail page.
2. Inspect the recommendation.
3. Choose **Approve**, **Reject**, or **Escalate**.
4. Point out that the decision is persisted and reflected in the incident state.

## 5) Optional retry demo

If you have a failed analysis run available:

1. Open the failed incident.
2. Click **Retry analysis**.
3. Show the incident re-entering the queue and the timeline updating again.

## Suggested close

Explain that V2 is now an event-driven incident response demo with:

- async request/result handoff
- persisted analysis runs
- OpenSearch-backed evidence
- live SSE updates
- human decision tracking
