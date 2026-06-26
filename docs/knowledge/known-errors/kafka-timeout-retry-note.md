# Kafka Timeout Retry Note

Repeated Kafka timeout errors often mean the service is retrying faster than downstream acknowledgements can recover.

## Common causes

- consumer lag growth
- reduced retry windows
- worker concurrency reduction
