# Notification Service Ownership

The notification-service owns customer-facing delivery of alerts, email notifications, and downstream fanout for incident updates.

## Key signals

- Kafka consumer lag
- retry timing changes
- delivery timeout spikes

## First checks

1. Confirm recent deployment changes.
2. Check consumer lag and worker throughput.
3. Verify alert delivery and callback retries.
