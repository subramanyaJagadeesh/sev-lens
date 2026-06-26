# API Gateway Ownership

The api-gateway owns request routing, upstream fanout, and latency shielding for user-facing traffic.

## Key signals

- elevated request latency
- upstream dependency slowdown
- retry storm behavior

## First checks

1. Check upstream latency breakdown.
2. Verify dependency health.
3. Review any recent gateway config changes.
