# PROJECT_STATE — ITSF

Current **state** of this project under
[`QUANT_WORKFLOW_VNEXT.md`](../QUANT_WORKFLOW_VNEXT.md) (cutover 2026-09-12) — state,
never workflow authority (vNext §0). One page, rewritten in place, history in git.

```
RESEARCH_QUESTION   = NQ opening-drive (09:30-10:00) continuation: base rate and
                      distribution (Q1); a 10:00 Oracle's cost-after performance
                      under executable + Micro integer-position constraints (Q2);
                      Prop MC commercial-EV adjudication GO / STOP / boundary on
                      the Oracle's daily USD P&L distribution (Q3).
                      Verbatim and binding: STUDY_0_PREREGISTRATION.md (SEALED).
RESEARCH_ID · LANE  = ITSF-S0 · FULL
STAGE               = S3 RUN — mechanical gate (N15) RUN 2026-09-13: HOLD.
                      Code, data, prereg, environment, runner safety and
                      reproducibility are green; three Owner-gated
                      prerequisites remain. N16 not executed.
ACTIVE_HYPOTHESIS   = sealed Study-0 contract; MC pipeline must produce the
                      Checkpoint-0 statistic the sealed §10.4 decision table reads
DATA_GRANT          = the existing ITSF S0 grant only. No new grant. Protected
                      Development outcomes remain UNINSPECTED.
TRIAL_ACCOUNTING    = ops/TRIAL_REGISTRY.md
OUTCOME_EXPOSURE    = tracked — ops/EXPOSURE_LEDGER.md. RETAINED: this project has a
                      sealed preregistration and an unrevealed statistic, so
                      blinding is materially required (vNext §11).
OPEN_MATERIAL_BLOCKERS = THREE, all Owner-gated, none a code defect and none
                      repairable by the builder (see "N15 as it measured"):
                      (1) no MC event chain exists for run id MC-R001;
                      (2) SMOKE-001 (the E3 production-scale smoke) has never
                          been run, and READY requires its PASS record;
                      (3) `consumer.authorize_real_mc` refuses unconditionally
                          by construction and its own docstring requires a
                          deliberate reviewed change to make it conditional.
                      Non-blocking rows carried: B-35, NB1, B-29, B-30.
NEXT_OWNER_DECISION = resolve the three N15 prerequisites above, in that order.
                      Each is Aaron's; none is a builder repair. REAL_MC =
                      NOT AUTHORIZED. N16 NOT EXECUTED.
```

## N15 as it measured — 2026-09-13

The S3 mechanical run gate was executed read-only. **Green:** code identity
(`HEAD e523a740`; `src/itsf` `e8fffdfd…` and `src/itsf/mc` `bfed0b62…` are
byte-identical to the independently verified R2 target `537354bf`, and nothing
under `src/` or `tests/` has changed since) · data identity (the authorized job
dir resolves, its `manifest.json` hashes to the pinned
`d8d1edc7b549b441…`, 141 manifest entries, 139 `.dbn.zst` present and NOT
opened; the sealed DAY_STRATA supplement MC-DS-S004 hashes to the registry's
own `f59a0092…`) · prereg binding (`guards.verify_frozen_hashes()` PASS) ·
environment (Python 3.13.14, all 49 pinned packages present, zero drift) ·
runner safety (the production entry is gate-first and its gate refuses
unconditionally; `assert_real_run_allowed` refuses outside the trusted launch
boundary; `runner_readycheck` is read-only and appended nothing) ·
reproducibility (5771 passed, 1 xfailed, 0 failed).

**Not green:** the three prerequisites above. `runner_readycheck(MC-R001)`
returns `live_authorization=False`, `may_start=False`, "no MC event chain
exists for this run id". The ratified chain is
`MC_PACKET_DRAFTED → MC_PACKET_APPROVED → MC_RUNNER_READYCHECKED(smoke_ref)
→ MC_READY_FOR_RUN_AUTHORIZATION → MC_RUN_AUTHORIZED` (Aaron-only), and no row
of it exists. `MC_RUNNER_READYCHECKED` and Aaron's sentence both require
`SMOKE-001=PASS`, which has never been produced —
`ops/MC_COST_PROBE_FINDINGS.md` says so in its own words and estimates E3 at
roughly three hours for two runs. Nothing was appended, no smoke was run, and
no protected outcome was inspected.

## Node mapping at cutover

| node | status |
|---|---|
| N13 | CLOSED 2026-09-10 (Aaron, DEC-N13-CLOSE-1/2) |
| **N14** — exact-tree independent review of the MC implementation | **CLOSED** by Aaron, on the independent `FINAL_R2_VERIFIED` return of `N14-POSTHOLD-RESIDUAL-VERIFY-004` (R2 CLOSED against `537354bf`, nine controls NO_REGRESSION). Every round, finding and return is preserved unrewritten — see below. |
| **N15** | the **S3 mechanical run gate**: code identity · data identity · prereg binding · runtime/environment identity · runner safety · replay/reproducibility · outcome-access state · Owner authorization present. Mechanical only — no reviewer seat, no review packet, no sealed bundle unless a concrete blindness need arises. **Not executed.** |
| **N16** | the real MC run. Owner-only. Requires the N15 gate green **and** Aaron's precise authorization. **Not executed.** |
| N17 | the reveal. Owner-only, after S4 mechanical recomputation. Outcome blinding holds until then. |

### N14, as it actually closed

Round 1 → **HOLD, consumed**: Finding A not reproduced on the reviewed bytes and
frozen as 16 evidence tests; Finding B reproduced and repaired — `serialized_append`
now refuses any event that creates or advances authorization state. Round 2 →
**HOLD, consumed**. **No round 3 was ever opened: the two-round substantive ceiling
(vNext §6) is spent.** The post-hold verifications below are Owner-authorized bounded
closure checks, not new substantive rounds.

An independent post-hold residual verification then **closed F02-K, F04, F06 and
R1, with all four non-regression controls NO_REGRESSION**, leaving one item —
**R2 / F02-B**: non-base seeds compared their doubled-B drift against the base
seed's baseline instead of their own. Aaron authorized one micro-repair
(DEC-N14-R2-1); it reproduced exactly in isolation and was repaired so each arm is
measured against the arm it doubles, with the pairing recorded in
`ConvergenceReport.drift_reference_by_axis` (DEC-N14-R2-2/3/4).

Three further verification deliveries were cut. Their true dispatch history:

| delivery | dispatched | outcome |
|---|---|---|
| `N14-POSTHOLD-RESIDUAL-VERIFY-001` | **NO** | superseded before dispatch — it bound an incomplete target; retained under its DO_NOT_DISPATCH marker |
| `N14-POSTHOLD-RESIDUAL-VERIFY-003` | **YES** | **PROCEDURAL STOP** — the reviewer opened an optional, reviewer-selected file the package had not admitted. A **transport/packaging defect**: **no substantive verdict, no substantive review round consumed** |
| `N14-POSTHOLD-RESIDUAL-VERIFY-004` | **YES** | **FINAL_R2_VERIFIED** — R2 independently verified **CLOSED** against commit `537354bf9f9f2511679c739b284873401c3221f1`, with **all nine controls NO_REGRESSION** |

On that return Aaron made the Owner decision **N14 = CLOSED**. All three
deliveries are retained intact under their markers. Under vNext no further
verification node follows: a finding becomes a row, a bounded repair, or an Owner
decision — never automatically another node.

Carried forward as a **non-blocking row**, unrepaired and not re-litigated: the
verifier's **NB1** — the public aggregation/seal API accepts a deliberately
truncated attempt chain as NON_CONVERGED, judged non-blocking because the runner
never emits such a chain.

## What changed for this project at cutover

Retired as default routing — **kept for reproducing pre-cutover work, never
rewritten**: the QROS-CF A–L stage chain and `qros next` routing; Review Packet
issuance / outcome binding; the per-node reviewer-seat and blind-transport
machinery in `ops/REVIEWER_CONTRACT.md`; closure and residual-verification
packages; review-of-review; `PASS_WITH_BACKLOG` routing; automatic node creation
from reviewer findings. `qros check` / `qros status` remain **on-demand** mechanical
diagnostics — the four known runtime gaps (A2→B, I→J, `trial_accounting` STALE,
14 UNASSESSED triggers) are information, not gates.

Still in force: the **sealed preregistration**, outcome blinding and the exposure
ledger, the immutable registry and `runs/` discipline, and every Owner gate in
vNext §10. `ops/REVIEWER_CONTRACT.md` §3 remains the reference for blindness
levels **if and when** a blind seat is actually needed (vNext §11) — it is no
longer a standing obligation.

Reading order for a new session: this file → `ops/BACKLOG.md` §1 → `ops/DECISIONS.md`
for the decision behind anything here. `ops/RESEARCH_STATE.md` is the pre-cutover
stage authority, retained as history.
