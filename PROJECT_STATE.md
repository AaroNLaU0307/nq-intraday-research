# PROJECT_STATE — R1 Scheduled-Release Information-Diffusion Continuation

Current **state** of this project under
[`QUANT_WORKFLOW_VNEXT.md`](../QUANT_WORKFLOW_VNEXT.md) (cutover 2026-09-12) —
state, never workflow authority (vNext §0).

```
PROJECT              = R1 Scheduled-Release Information-Diffusion Continuation
RESEARCH_QUESTION    = After a public scheduled information release, and after a
                       realistically executable decision delay, does economically
                       meaningful directional price adjustment remain in NQ?
RESEARCH_ID · LANE   = R1 · FULL
STAGE                = S2 BUILD (COMPLETE)
S0                   = CLOSED  (Owner decision: RESEARCH — see R1_S0_PROVENANCE.md)
S1                   = SEALED  (r4, 2026-09-17)
PREREG_SEALED        = YES
SEALED_BY            = Aaron (Owner)
SEAL_EXECUTED_BY     = Claude Opus (Main Agent), under explicit Aaron
                       authorization
SEAL_IDENTITY        = R1_S1_SEAL_ATTESTATION.json (CONTENT_COMMIT + digests)
CONTENT_COMMIT       = 46b8aef9d2471dd427db6a780435e743660a6f24
                       (the commit whose tree IS the sealed content)
SEAL_ATTESTATION_COMMIT = its child, tagged `r1-s1-sealed`; it adds the
                       attestation and this line, and changes no sealed file
PSMV                 = AUTHORIZED · COMPLETE 2026-09-17
                       record-repaired 2026-09-17 (output surface only):
                         PSMV_MDE_SCOPE_VIOLATION = RECORD_HYGIENE_ONLY
                         R1_OUTCOME_CONTAMINATION = NO
                         PSMV_RERUN_REQUIRED      = NO
                         PSMV_RERUN               = NO
PLANNING_POWER_TABLE = TO_BE_REFRESHED_OUTSIDE_PSMV / BEFORE_SEAL IF REQUIRED
DATA_GRANT           = OD-1 GRANT, R1 scope only:
                         · existing NQ Development OHLCV
                           (NQ.v.0 ohlcv-1m, 2010-06-06 → 2022-01-01 exclusive,
                            manifest d8d1edc7b549b441d691dda74331806c957a19946e746bd795978e01d73c3ae8)
                         · frozen F10 CPI/NFP event calendar
                           (sha256 5e92ad00737339c392ed2c0927736e196e076e185897c146c884d5f515bb5e8c)
                         · derived spread-cost table (spread_cost_table.csv)
INTERNAL_VALIDATION  = NOT GRANTED   (and not present on this machine)
LOCKBOX              = NOT GRANTED   (and not present on this machine)
PROTECTED_ITSF_OUTCOMES = NOT GRANTED
OUTCOME_REVEAL       = NOT GRANTED
R1_OUTCOME_EXPOSURE  = NONE
TRIAL_ACCOUNTING     = R1_TRIAL_REGISTRY.md  (separate R1 lineage; the ITSF
                       registry at C:\Users\Aaron\quant-data\itsf-registry is
                       referenced by identity and is NEVER mutated)
VERSION_CONTROL      = standalone local git repository (OD-5 = OPTION A
                       implementation). No remote. Nothing pushed.
PRE_SEAL_PROJECT_COMMIT = 8656701564d798a227efa9f46e2f581353017ff5
                       (the full pre-seal state. The commit that RECORDS
                        this line is its child; git carries the rest.)
IS_SEALED_COMMIT     = NO   (the seal is a separate Aaron Owner act)
OPEN_MATERIAL_BLOCKERS = NONE
OPEN_PRE_SEAL_ITEMS  = P-5 only (cost residual, NON-BLOCKING). P-1..P-4, P-7
                       and P-8 are CLOSED; P-6 is not applicable yet.
S2                   = BUILD COMPLETE 2026-09-17 (authorized by Aaron:
                       implementation + synthetic validation ONLY)
S3_RUN               = NOT AUTHORIZED
OD3_POWER_GATE       = NOT RUN
R1_OUTCOME           = NOT COMPUTED
TRIAL_CONSUMED       = NO
ENGINE               = r1/ (22 modules) + tests/ (264 tests, all passing)
                       See S2_BUILD_REPORT.md (r2, after bounded repair).
S2_CODE_COMMIT       = 433e2cc035391ec73c5c94135ad9cf6afaca746e
                       (the attested EXECUTABLE code and tests)
S2_BUILD_ATTESTATION = R1_S2_BUILD_ATTESTATION.json, in the metadata-only child
                       commit, tagged `r1-s2-built`. A commit cannot contain its
                       own SHA; the tag resolves it.
EXECUTABLE_IDENTITY  = enforced at S3 preflight by
                       r1.build_identity.assert_executable_identity: a
                       metadata-only ledger append does NOT invalidate it, a
                       runtime-source edit DOES.
REAL_DATA_ADAPTER    = IMPLEMENTED (r1/dev_adapter.py); NOT EXECUTED on R1
SEALED_REGISTRY      = IMMUTABLE — R1_TRIAL_REGISTRY.md, byte-for-byte
OPERATIONAL_LEDGER   = R1_EXECUTION_LEDGER.md (append-only chain, UNSEALED)
SEALED_ERRATA        = R1_SEALED_ERRATA.md (post-seal, descriptive only)
VALIDATION           = SEAL_SNAPSHOT_VALIDATION = PASS (seal-time context)
                       CURRENT_STATE_VALIDATION = PASS (tools/validate_state.py)
                       S2_TEST_SUITE            = PASS
CURRENT_NEXT_ACTION  = S2 BUILD — COMPLETE AND STOPPED HERE. S3 RUN is the next
                       possible stage and is NOT authorized. No material
                       blocker remains.
NEXT_OWNER_DECISION  = authorize S3 RUN, or do not
```

## What this project is, in one paragraph

R1 asks whether the direction of NQ's own two-minute reaction to a scheduled BLS
08:30 ET release (CPI or Employment Situation) predicts a cost-surviving return
over an executable window that starts at `O(08:33)` and ends at `O(09:29)`, one
minute before the cash-equity open. It is a **new lineage**. It is **not** a
continuation of the parked ITSF study, whose sealed preregistration asks a
different question about the 09:30–10:00 opening drive.

## Files

| file | role |
|---|---|
| `PROJECT_STATE.md` | this page — current state only |
| `R1_S0_PROVENANCE.md` | how R1 reached `RESEARCH`; the S0 chain and the parallel dispositions |
| `R1_DELEGATED_OWNER_DECISIONS.md` | the operative OD-1…OD-7 and P-2 ruling record |
| `R1_S1_PREREGISTRATION_SEALED.md` | the r4 design — **SEALED** 2026-09-17 |
| `R1_S1_SEAL_ATTESTATION.json` | the seal: CONTENT_COMMIT + every sealed sha256 |
| `R1_PREREG_MANIFEST.json` | structured companion to the prereg (closes P-7); **not authoritative** |
| `R1_EXECUTION_LEDGER.md` | operational append-only lifecycle chain — **not sealed** |
| `R1_SEALED_ERRATA.md` | post-seal descriptive corrections — **not sealed** |
| `R1_S2_BUILD_ATTESTATION.json` | the attested S2 executable identity — **not sealed** |
| `S2_BUILD_REPORT.md` | the S2 build record |
| `R1_TRIAL_REGISTRY.md` | R1's own trial/exposure identity |
| `psmv/psmv_structural.py` | the pre-seal structural reader (L-13 constrained) |
| `psmv/psmv_purity_guard.py` | the L-13 guard and its mutation demonstration |
| `psmv/validate_prereg.py` | the mechanical record validator (prereg + manifest + state) |
| `artifacts/PSMV_STRUCTURAL_REPORT.json` | the PSMV artifact |
| `artifacts/PSMV_PURITY_ATTESTATION.json` | the L-13 attestation |

## Relationship to the parked ITSF repository

ITSF (`../Intraday Trend Strategy Framework`) is **STOPPED / PARKED** and is
**never modified by this project**. R1 reuses three ITSF assets, all **read-only
and digest-pinned**:

* the purchased NQ Development data (under OD-1);
* the frozen F10 event calendar and the NQ `.v.0` symbology map;
* the derived per-minute spread-cost table.

R1 also **transcribes** four pieces of ITSF frozen logic — the eligibility
funnel, the `complete_390` / ADR14 warm-up rule, the roll-transition session
mapping and the `±2` roll window — rather than importing ITSF code, so that
running R1 can never execute, import or dirty the parked repository. The
transcription is validated by reproduction: PSMV independently reproduces every
published ITSF preflight figure (see `R1_TRIAL_REGISTRY.md` §3).

## Deliberately not built

No governance framework, no reviewer machinery, no QROS/L6 artifacts, no packet
taxonomy, no state/seal runtime. vNext §15: a new project needs the workflow
file, a minimal `PROJECT_STATE.md` and a preregistration.

Version control is now initialised — a standalone local git repository with no
remote — as ordinary technical implementation of OD-5 = OPTION A, not as a new
scientific decision. No market-data file, no protected outcome and no ITSF file
is tracked. The pre-seal commit is **not** a seal: sealing remains an Aaron
Owner act, and the eventual seal must bind to a committed state.
