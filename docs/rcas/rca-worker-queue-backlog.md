# RCA: Worker Queue Backlog

The backlog was triggered by a concurrency reduction during a maintenance window and a downstream dependency slowdown. Jobs accumulated faster than workers could drain them, which inflated queue depth and job latency until the queue breached the incident threshold.
