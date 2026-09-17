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
| 3 | 2026-09-17T23:30:00Z | `S2_BUILD_COMPLETE` | main agent (Claude Opus), after ChatGPT bounded repair | S2 BUILD r2 COMPLETE. S2_FINAL_BUILD_COMMIT=0bc815dc22863e50777311a9c2c25922ecfeb4fd. Operational ledger, Development adapter and A1 wiring added; sealed registry untouched. No real R1 data executed; trial NOT consumed; S3 NOT authorized. | `b9da072437058ea1820d6667c64a5bf4d6452178c43450edd5003145e5e4f3b6` | `543975b3ae228ba3e89bdefa364140dca23304da7b77bedc9d01b69c2a8a027d` |
| 4 | 2026-09-18T00:20:00Z | `S2_BUILD_COMPLETE` | main agent (Claude Opus), identity repair | S2_BUILD_IDENTITY_FROZEN. S2_CODE_COMMIT=433e2cc035391ec73c5c94135ad9cf6afaca746e; S2_BUILD_ATTESTATION_COMMIT = the commit adding R1_S2_BUILD_ATTESTATION.json, tagged r1-s2-built; runtime rollup 3f64307d2b214c9cc21d7873c198be4ebc247de5b5fbcc56a082e6a17acad2a5 over 23 r1/*.py files. Metadata only: no executable source changed in that child commit. No research event; trial NOT consumed. | `543975b3ae228ba3e89bdefa364140dca23304da7b77bedc9d01b69c2a8a027d` | `d7cb7563b5f74c532b44279108301f90e7e80ac09b2db0ee0fba1afff4c07c9d` |
| 5 | 2026-09-18T01:10:00Z | `S3_AUTHORIZED` | Aaron (Owner), executed by Claude Opus | S3-A ONLY: real-data pre-run / pre-reveal power gate. Identity gate PASS (14/14): CONTENT_COMMIT=46b8aef, SEAL_ATTESTATION_COMMIT=595af1c, S2_CODE_COMMIT=433e2cc, S2_BUILD_ATTESTATION_COMMIT=b99e10e, tag r1-s2-built resolves exactly, 12/12 sealed digests, sealed registry byte-identical, no RUN_STARTED, trial NOT consumed. REAL_INPUT_PREFLIGHT PASS: role development_signal, vendor manifest d8d1edc7, 139 files verified, rollup 320b12c4 identical to the PSMV-recorded rollup, 3586 ET dates, structural universe reproduced = 252 (CPI 118 / NFP 134, roll exclusions 0), all four anchors present on all 252. NOT RUN_STARTED; the Primary run remains forbidden. | `d7cb7563b5f74c532b44279108301f90e7e80ac09b2db0ee0fba1afff4c07c9d` | `2c075dafea2c58ed8c4586150907a1cc12ce3a6a273d7274441eb26c48d2b5ca` |
| 6 | 2026-09-18T01:12:00Z | `POWER_GATE_EXECUTED` | Claude Opus under S3-A authorization | OD-3 pre-reveal power gate on REAL control dispersion. E4_EVALUATED_PRE_RUN: E4_COUNT=6, anchor-NA=0, POST_SEAL_SIGNAL_DEFINED_N=246. C2 dispersion-only population 2331 non-event days; s_hat=28.2082 USD/MNQ; SE_hat=1.7985; MDE_50=6.9485; MDE_80=8.4610; M=3.99; CI_half_width_would_exceed_M=False. Artifact artifacts/R1_S3A_POWER_GATE.json sha256 f8760918c7ce79f47492bcf7aaf2da4ae3c00d1df42cc3d6f891ce2ef6dd5cfd. NO Primary outcome, no C2 performance statistic, no outcome bundle. OWNER_POWER_DECISION PENDING. RUN_STARTED not appended; TRIAL NOT CONSUMED. | `2c075dafea2c58ed8c4586150907a1cc12ce3a6a273d7274441eb26c48d2b5ca` | `80f3a3c6f680aedcfe8235fde537fe0367aa5c357c17a84e9a1af24644490d76` |
