# Database Service Ownership

The database-service owns application connection pooling and shared database access for the incident demo.

## Key signals

- connection acquisition latency
- pool exhaustion
- long-running queries

## First checks

1. Inspect connection pool usage.
2. Review query saturation and retry behavior.
3. Compare current traffic with recent change windows.
