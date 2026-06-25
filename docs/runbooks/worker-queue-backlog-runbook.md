# Worker Queue Backlog Runbook

## Goal

Drain the backlog safely and restore steady worker throughput.

## Immediate checks

- Confirm whether workers are unhealthy or under-provisioned.
- Check queue depth growth against worker concurrency changes.
- Inspect downstream dependency timeouts that can stall job completion.

## Recommended actions

- Scale workers up temporarily if the queue is saturating.
- Roll back recent concurrency reductions if they caused starvation.
- Pause non-critical producers until the backlog falls below threshold.
