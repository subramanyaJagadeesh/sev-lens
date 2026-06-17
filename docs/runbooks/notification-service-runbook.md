# Notification Service Runbook

## Purpose
Primary runbook for the notification service during customer-facing delivery incidents.

## Checks
- Confirm whether the service is still receiving new deployment traffic.
- Compare current error rate, latency, and Kafka lag against expected thresholds.
- Review the most recent incident events before making any change.

## Common Next Steps
- Retrieve the Kafka consumer lag runbook.
- Inspect the deployment that introduced retry or polling changes.
- Escalate to platform support if the service cannot drain backlog after mitigation.

