# API Gateway Latency Runbook

## Goal

Reduce request latency spikes at the edge without introducing unnecessary churn.

## Immediate checks

- Confirm upstream timeout and retry saturation.
- Check whether one backend is dragging the entire gateway request path.
- Verify whether recent timeout changes widened request dwell time.

## Recommended actions

- Revert or reduce the last timeout increase if it correlates with the spike.
- Rate-limit the hottest route while backlog clears.
- Escalate to the owning backend team if the gateway is only the symptom.
