# RCA: API Gateway Latency Spike

The latency spike was caused by a tighter upstream retry budget combined with an increase in route dwell time after the latest timeout change. The gateway remained healthy, but downstream retries saturated the request path and pushed p99 latency above the alert threshold.
