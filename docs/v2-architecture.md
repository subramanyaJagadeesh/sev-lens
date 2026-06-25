# SevLens V2 Architecture

This diagram captures the current V2 flow from incident trigger through async analysis and human decision.

```mermaid
graph LR
  User["User"] --> Frontend["React Frontend"]
  Frontend -->|"HTTP: trigger/list/detail/decision"| IncidentAPI["FastAPI Incident API"]

  IncidentAPI -->|"publish analysis request"| RequestStream[("Redis Streams: analysis:requests")]
  RequestStream -->|"consume request"| RagWorker["FastAPI RAG Worker"]

  RagWorker -->|"retrieve evidence"| OpenSearch[("OpenSearch")]
  RagWorker -->|"synthesize recommendation"| LLM["Ollama / OpenAI-compatible LLM"]
  RagWorker -->|"publish analysis result"| ResultStream[("Redis Streams: analysis:results")]

  ResultStream -->|"consume result"| IncidentAPI
  IncidentAPI --> SQLite[("SQLite incident store")]
  IncidentAPI --> SSE["Incident SSE stream"]
  SSE --> Frontend

  Frontend -->|"approve / reject / escalate"| IncidentAPI

  Shared["Shared contracts, scenarios, runbooks, RCAs"] --> IncidentAPI
  Shared --> RagWorker
  Shared --> Frontend
```

## Notes

- The incident API is the system of record for incidents, events, decisions, and persisted recommendations.
- The RAG worker owns retrieval, evidence gathering, prompt assembly, and recommendation synthesis.
- Redis Streams is the async boundary between services.
- OpenSearch is the local log evidence backend for V2.
- SSE keeps the frontend synchronized with persisted incident updates.
