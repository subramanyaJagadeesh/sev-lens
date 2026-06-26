# Queue Drain Lag Note

Queue drain lag usually shows up when incoming work exceeds worker throughput for more than a few minutes.

## Common causes

- worker concurrency too low
- downstream service slowdown
- backoff configuration too aggressive
