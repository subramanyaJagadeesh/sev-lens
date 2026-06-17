# RCA: Notification Service Kafka Timeout

## Summary
The notification service experienced elevated Kafka timeout errors after a deployment changed retry timing and reduced consumer batch size.

## Root Cause
- Kafka consumer lag grew faster than the service could drain it.
- The retry timeout change extended the time spent waiting on downstream acknowledgements.
- The consumer change reduced throughput during peak traffic.

## Resolution
- Increased consumer capacity.
- Rechecked lag and error rate after mitigation.
- Documented the retry and polling behavior in the runbook.

