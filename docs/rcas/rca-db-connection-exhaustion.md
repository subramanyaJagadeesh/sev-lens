# RCA: Database Connection Exhaustion

## Summary
The service exhausted its connection pool during a traffic spike while request concurrency remained unchanged.

## Root Cause
- Active requests exceeded the pool's steady-state capacity.
- Slow queries increased connection hold time.
- Recovery required reducing pressure before increasing pool limits.

## Resolution
- Reduced request pressure.
- Tuned pool configuration.
- Added follow-up checks for pool utilization and slow query volume.

