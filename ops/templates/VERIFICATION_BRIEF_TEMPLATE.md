# VERIFICATION BRIEF — <run id or scope name>

```
BRIEF_VERSION        = 1 (QROS-CF v2 §2.8; ops/REVIEWER_CONTRACT.md §3)
VERIFICATION_SCOPE   = <run ids / artifacts covered by THIS dispatch, exhaustively>
OBLIGATION           = RUN_IDENTITY | STAGE_I | BOTH
BLINDNESS            = CLAIM_BLIND | OUTCOME_BLIND
FRAMEWORK_COMMIT     = <40-hex: the authorized governed-execution identity the code is exported from>
DISPATCHED_BY        = <Aaron | builder (one retry under DEC-0007 only)>
DISPATCHED_AT_UTC    = <ISO time>
THIS_BRIEF_SHA256    = (recorded in ops/DECISIONS.md by the dispatcher; the brief cannot contain its own hash)
```

## 1. What you are verifying, and what "reproduced" means

- Object(s): <sealed artifact paths as they appear under pre_freeze/, with the sha256 you must find>
- Recompute: <exactly what is recomputed from which inputs>
- Matching rules (FIXED HERE, before dispatch — a rule with judgment space that is not written here is not blind):
  - byte identity: sha256 equality of <files>
  - structural identity: <e.g. canonical serialization == sealed bytes; n_rows == declared>
  - replay identity: <e.g. every headline cell reproduced field-by-field; tolerance: none / <value>>
- What you are NOT asked to judge: <e.g. the research outcome; whether the design was wise>

## 2. Pre-freeze set (everything you may read before FREEZE)

`pre_freeze/ALLOWLIST.sha256` is the exhaustive list. Recompute every hash first; a mismatch is STOP.

## 3. Freeze

Write your result file, then `pre_freeze/FREEZE_MARKER.json` = {"frozen_result": "<relative path>", "sha256": "<sha256>", "frozen_at_utc": "<ISO>"}. Tell the dispatcher. Only then will `post_freeze/` be delivered.

## 4. Post-freeze set (delivered after your marker)

<the producer's claims: registry rows, prior attestations — compare claim by claim; the frozen result does not change>

## 5. Six threats — name one for any BLOCKING finding

T1 research correctness · T2 look-ahead/leakage · T3 data identity/provenance · T4 reproducibility · T5 real-run execution safety · T6 independent-verification validity. A finding that names none is NON-BLOCKING and goes to backlog.

## 6. Output

Verdict `PASS | PASS_WITH_BACKLOG | HOLD` (or, for a run: the family's VERIFIED / FAILED row candidate), findings table `id | BLOCKING? | threat | evidence class (REPRODUCED/REASONED/SELF-REPORTED) | evidence | minimal fix | minimal test`, and the attestation with the header in `ATTESTATION_HEADER_TEMPLATE.md`. State independence per dimension (context · authorship · model diversity · empirical) and per target.

## 7. Contamination

Anything read outside `pre_freeze/` before freeze: STOP and say so. One fresh retry may be dispatched by the builder (DEC-0007); a second exposure on this target goes to Aaron.
