# PRE_RUN_ATTEMPT_FAILURE

- trial_id: S0-T001
- authorized_commit: 08e74235afb4868acc7df80bbe0e0a13a1b5ba5a
- stage_at_failure: B_LOAD_VALIDATE
- trial_state_at_failure: PACKET_APPROVED
- generated_at_utc: 2026-08-01T16:20:47+00:00
- exception_type: RunGateError

## Failure point

RunGateError at gate 'preflight_assertions_match' (incident INC-fa9234e0e541); raw detail sealed in INCIDENT_INC-fa9234e0e541.md inside the attempt directory

## Released information (exposure so far)

- guarded stage logs only

## Chain status

```json
{
  "manifest": "not_started",
  "stages_completed": [
    "A_PRECHECK"
  ]
}
```
