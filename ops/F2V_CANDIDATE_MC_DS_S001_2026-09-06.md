# CANDIDATE ROW FOR AARON — NOT APPENDED

```
CANDIDATE_EVENT=F2v SUPPLEMENT_VERIFICATION_FAILED
PREDECESSOR=P4 (chain P1/P2/P2S/P2/P2S/P2/P2S/P2/P3/P4)
GLOBAL_SEQUENCE=22 (highest before: 21)
ACTOR=fresh fable verifier (form: governance)
COMMIT=3df1656f105b9314235bd28957336a7dec4bde05 (framework HEAD at verification, worktree clean)
ATTESTATION=P5_VERIFIER_ATTESTATION_MC_DS_S001_2026-09-06.md sha256 cc733337ed4fb39c994e11f188f49f20e2239870bbb0d82e645bc974d1c8053a
PREFLIGHT_PROBLEMS=0
STATE_AFTER_APPEND=AWAITING_RETIREMENT ; successors ['F3']
```

Row, verbatim (one line):

```
| 22 | 2026-09-05T18:00:16+00:00 | SUPPLEMENT_VERIFICATION_FAILED | 3df1656f105b9314235bd28957336a7dec4bde05 | fresh fable verifier | [MC-DS-S001] supplement_id: MC-DS-S001; failure_code: headline_replay_mismatch; detail: 8 of 2842 days carry a stratum label different from the one the S0-T001 run stratified on (vol T2 vs T3 on 2012-11-26 2012-11-27 2013-05-06 2014-10-20 2015-12-10 and event FOMC vs none on 2019-10-11 2020-03-03 2020-03-23), headline draw reproduced in 0 of 1008 cells as sealed and in 1008 of 1008 with those eight labels restored, verifier attestation ops/P5_VERIFIER_ATTESTATION_MC_DS_S001_2026-09-06.md sha256 cc733337ed4fb39c994e11f188f49f20e2239870bbb0d82e645bc974d1c8053a; sealed_artifact_deleted: NO; supersession_required: YES |
```

Memory-only preflight: see P5_VERIFY_REGISTRY_MC_DS_S001_2026-09-06.json.
Registry, sealed artifact and archive copy were NOT modified.
