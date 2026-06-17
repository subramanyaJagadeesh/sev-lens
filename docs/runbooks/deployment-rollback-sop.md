# Deployment Rollback SOP

## Purpose
Use this procedure when a recent deployment is strongly correlated with the incident and a rollback is the safest mitigation.

## Preconditions
- Identify the suspect deployment.
- Confirm rollback risk with the incident owner.
- Capture the reason for rollback in the audit trail.

## Rollback Guidance
- Prefer the most recent known-good build.
- Roll back one change at a time when multiple deploys overlap.
- Re-run validation checks after rollback before closing the loop.

