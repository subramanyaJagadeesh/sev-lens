# SevLens V2 Known Limitations and V3 Direction

## Known limitations

- The demo still relies on locally seeded scenarios and mock operational context.
- Redis Streams is the async transport, but it is intentionally lightweight and local-first.
- OpenSearch is used as the local log backend rather than a production ingestion pipeline.
- LLM calls still depend on a locally configured model or compatible API endpoint.
- Manual testing remains the primary validation approach.

## V3 direction

- Move beyond the demo-oriented scenario registry toward production incident ingestion.
- Replace local-only log seeding with real log pipelines and broader search queries.
- Evaluate stronger queueing / stream processing options where needed at scale.
- Introduce production auth, access control, and observability around the incident workflow.
- Keep the current incident system of record and recommendation contract as the baseline for future expansion.
- Add multi agent system for RAG to implement retry, context expansion, and for overall better evidence collection
