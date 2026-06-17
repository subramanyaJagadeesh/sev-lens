# Database Connection Pool Runbook

## When to Use
Use this runbook when a service shows connection acquisition timeouts, pool exhaustion, or cascading latency.

## Investigation Steps
- Check connection pool utilization.
- Compare active and idle connections.
- Review recent deploys for query volume or pool configuration changes.

## Suggested Remediation
- Increase pool size only if downstream capacity allows it.
- Reduce concurrency or queue pressure if the pool is saturated.
- Escalate if database saturation is the source of the outage.

