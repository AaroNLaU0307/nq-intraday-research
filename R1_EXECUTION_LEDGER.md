# R1 EXECUTION LEDGER — operational, append-only

```
RECORD_TYPE       = OPERATIONAL_EXECUTION_LEDGER (append-only hash chain)
SEALED            = NO -- deliberately OUTSIDE the S1 sealed digest set
SEALED_COUNTERPART= R1_TRIAL_REGISTRY.md, which is sealed byte-for-byte and is
                    the IMMUTABLE lineage / trial-registration snapshot. It is
                    never edited, and no lifecycle event is ever added to it.
INTEGRITY         = each entry commits to its parent's digest; editing,
                    deleting or reordering any historical entry breaks every
                    descendant. Verified by `r1.ledger.verify_chain`.
```

**What belongs here:** every post-seal lifecycle event — S2 build completion,
S3 authorization, `RUN_STARTED` (the row that CONSUMES the trial), power-gate
execution and the Owner's decision on it, outcome-bundle creation, reveal
authorization, the reveal itself, and verdict closure.

**What does not:** anything that changes scientific design. This ledger records
what happened; it never states what is true about the market.

| # | utc | event | actor | detail | parent | digest |
|---|---|---|---|---|---|---|
| 1 | 2026-09-17T00:00:00Z | `GENESIS` | main agent | lineage R1 (Scheduled-Release Information-Diffusion Continuation); SAMPLE_FORMAL_TRIAL_ORDINAL=2; PRIOR_LINEAGE=ITSF S0-T001; INHERITED_RESEARCHER_EXPOSURE_COUNT=1575; SEALED_TRIAL_REGISTRY_SHA256=56715810cdadea3ee2b1da67d287ad243c64f0ae76a22efeddf074b576cc5fdd; CONTENT_COMMIT=46b8aef9d2471dd427db6a780435e743660a6f24; SEAL_ATTESTATION_COMMIT=595af1c9663eb868e9f2d72f44abfe2f426ca24d | `-` | `85bc416dc8d813c30b338b24d304cab20ecd9d4a928d4cedbd9f868429887802` |
| 2 | 2026-09-17T00:05:00Z | `S2_BUILD_COMPLETE` | main agent (Claude Opus) | S2 BUILD complete; engine implemented and synthetic-validated; trial NOT consumed | `85bc416dc8d813c30b338b24d304cab20ecd9d4a928d4cedbd9f868429887802` | `b9da072437058ea1820d6667c64a5bf4d6452178c43450edd5003145e5e4f3b6` |
