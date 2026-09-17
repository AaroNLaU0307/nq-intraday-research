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
STAGE                = S1 PRE-SEAL
S0                   = CLOSED  (Owner decision: RESEARCH — see R1_S0_PROVENANCE.md)
S1                   = UNSEALED  (draft r4; ready for final acceptance)
PSMV                 = AUTHORIZED · COMPLETE 2026-09-17
                       record-repaired 2026-09-17 (output surface only):
                         PSMV_MDE_SCOPE_VIOLATION = RECORD_HYGIENE_ONLY
                         R1_OUTCOME_CONTAMINATION = NO
                         PSMV_RERUN_REQUIRED      = NO
                         PSMV_RERUN               = NO
PLANNING_POWER_TABLE = TO_BE_REFRESHED_OUTSIDE_PSMV / BEFORE_SEAL IF REQUIRED
S2                   = NOT AUTHORIZED
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
PRE_SEAL_PROJECT_COMMIT = PENDING
IS_SEALED_COMMIT     = NO   (the seal is a separate Aaron Owner act)
OPEN_MATERIAL_BLOCKERS = NONE
OPEN_PRE_SEAL_ITEMS  = P-5 only (cost residual, NON-BLOCKING). P-1..P-4, P-7
                       and P-8 are CLOSED; P-6 is not applicable yet.
CURRENT_NEXT_ACTION  = PRE-SEAL CLEANUP — COMPLETE. Next: ChatGPT/Aaron final
                       acceptance of the r4 UNSEALED preregistration, then
                       Aaron's seal. Nothing else is authorized.
NEXT_OWNER_DECISION  = seal or withhold the R1 preregistration
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
| `R1_S1_PREREGISTRATION_DRAFT_UNSEALED.md` | the r4 design — **UNSEALED** |
| `R1_PREREG_MANIFEST.json` | structured companion to the prereg (closes P-7); **not authoritative** |
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
