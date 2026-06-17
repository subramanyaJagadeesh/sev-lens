# Kafka Consumer Lag Runbook

## When to Use
Use this runbook when Kafka consumers are timing out, falling behind, or showing sustained lag growth.

## Investigation Steps
1. Check current consumer lag.
2. Confirm the number of active consumers.
3. Review recent deploys that changed polling, retry, or batch-size settings.
4. Compare lag against the service threshold.

## Suggested Remediation
- Scale consumers if lag is trending upward and capacity is available.
- Reduce batch size or tune polling if the service has recently changed behavior.
- Escalate if lag remains elevated after the first mitigation pass.

