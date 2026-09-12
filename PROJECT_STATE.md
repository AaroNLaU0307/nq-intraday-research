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
STAGE               = S3 RUN — mechanical gate (N15). Two of the three
                      2026-09-13 blockers RETIRED as historical under vNext
                      §0; the third is REPAIRED. One Owner data pin and the
                      authorization itself remain. N16 not executed.
ACTIVE_HYPOTHESIS   = sealed Study-0 contract; MC pipeline must produce the
                      Checkpoint-0 statistic the sealed §10.4 decision table reads
DATA_GRANT          = the existing ITSF S0 grant only. No new grant. Protected
                      Development outcomes remain UNINSPECTED.
TRIAL_ACCOUNTING    = ops/TRIAL_REGISTRY.md
OUTCOME_EXPOSURE    = tracked — ops/EXPOSURE_LEDGER.md. RETAINED: this project has a
                      sealed preregistration and an unrevealed statistic, so
                      blinding is materially required (vNext §11).
OPEN_MATERIAL_BLOCKERS = NONE mechanical. The sealed bundle is identified,
                      unambiguous and now bound BY DIGEST in the gate, so a
                      substituted bundle at any path refuses.
                      `ops/MC_RUN_AUTHORIZATION.json` does not exist — which
                      is not a defect, it IS the authorization.
                      The two commits are now bound SEPARATELY:
                      `input_bundle_commit` = 876c1b74… (the sealed bundle's
                      provenance) and `mc_execution_commit` = the governed
                      checkout's HEAD, MEASURED by the gate. Because it is
                      measured at run time, ANY further commit invalidates a
                      standing authorization — authorize against the HEAD in
                      the block above and commit nothing before the run.
                      Non-blocking rows carried: B-35, NB1, B-29, B-30.
NEXT_OWNER_DECISION = write `ops/MC_RUN_AUTHORIZATION.json` against the
                      HEAD measured at that moment. REAL_MC = NOT
                      AUTHORIZED. N16 NOT EXECUTED. MC-R001 UNUSED —
                      twice authorized, twice stopped by mechanical
                      infrastructure BEFORE the run began, never started.
```

## The authorization's two commits, separated 2026-09-13

`authorized_commit` was one word for two identities that do not move
together. They are now separate required fields, and the sentence names
both:

```
input_bundle_commit   876c1b74131b4ab1a89dce433ecce646ba481f8c
                      the commit the sealed S0-T001 bundle was produced at;
                      historical and fixed. Compared against
                      `prepared.authorized_commit`.
mc_execution_commit   NOT PINNED HERE, and deliberately: it is whatever
                      the governed checkout is at when the run starts, so a
                      value written on this page would be stale the next
                      time anything is committed -- including the commit
                      that wrote it. MEASURE it:
                        scripts.mc_real_run:authorization_preview
                      It is measured by the gate through the
                      governed-identity resolver, never accepted from a
                      caller, and refused when any governed path is
                      modified.
```

Two consequences worth knowing before writing the authorization:

* the execution commit is measured AT RUN TIME, so any further commit
  invalidates a standing authorization and a fresh one is needed;
* `ops/MC_RUN_AUTHORIZATION.json` is NOT in the governed set
  (`covering_mechanism` returns None for it), so writing it does not dirty
  the governed checkout and cannot invalidate the gate it feeds.

## MC-R001: two non-executions and the repair — 2026-09-13

The Owner authorized MC-R001 twice. **It has never started.** Both launches
failed in this session's own launch/entry plumbing, before any bundle byte
was consumed by a run, and both authorizations are voided by rename:

```
ae964754…  ModuleNotFoundError: No module named 'scripts'
           `run_governed.py` launched the child with `-P`, which keeps the
           launcher's own directory off `sys.path`, so a `scripts.*` target
           could not be imported. Nothing ran. Repaired by appending the
           repository root after `src`; pinned by a regression test.
           VOID file: ops/MC_RUN_AUTHORIZATION.VOID_ae964754_never_executed.json

27fe40f3…  MCInputError: authorization_snapshot_missing
           THE GATE PASSED. The entry then built its own prepared input and
           handed `prepare_mc_input` the REGISTRY snapshot where a
           `{trial_id, authorized_commit}` mapping is required. Nothing ran.
           VOID file: ops/MC_RUN_AUTHORIZATION.VOID_27fe40f3_never_executed.json
```

EVIDENCE OF NON-EXECUTION, measured after the second failure: `runs/`
contains only `S0-T001_20260813T170432Z`; `attempts/` only
`S0-T001-A20260813T170432Z`; zero registry rows mention MC-R001; registry
sha256 `b964b19a6b788bf9f47d1d24018dfc93836f74cbfd7ef69e4680471368d11fe9`.

ROOT CAUSE OF THE SECOND, stated plainly because it was a builder error and
not a design gap: **the assembly already existed.**
`real_input._assemble_from_sealed_run` has been the production prepare
caller since R2.1 and already pins the Owner-bound bundle root as
`SEALED_RUN_DIR`. `scripts/mc_real_run.py` duplicated it and got it wrong.
An earlier builder statement on this page's lineage — "no pinned governed
bundle root exists in code" — was **wrong**, and that error is what made the
duplicate look necessary.

REPAIR (engineering only; no methodology, threshold, input, sample or
authority changed):

* the entry calls `real_input._assemble_from_sealed_run()` and contains no
  assembly of its own — enforced by an AST test that fails on any local
  `prepare_mc_input(` call;
* the bundle-root argument is checked against `SEALED_RUN_DIR` and refuses
  (exit 4) on disagreement, rather than silently preferring either;
* the gate's authorization path is passed explicitly, so the module constant
  and the file actually read cannot diverge through a def-time default;
* `main()` is now exercised end to end past the gate — the testability gap
  that allowed both failures. Previously nothing had ever executed it.

## The sealed bundle, Owner-bound 2026-09-13

```
BUNDLE_ROOT   C:\Users\Aaron\quant-data\itsf-runs\runs\S0-T001_20260813T170432Z
IDENTITY      bundle_summary_digest
              7263f0c1802c205ae3bf3732a0d2de5b46f17aac67a93fe5aedcc7bb71262d67
              (mc_bundle_ondisk_summary.v1 — the EXISTING governed aggregate,
               not a new format invented to make another hash)
INVENTORY     14/14 files, 440,688,080 bytes, every digest matching the
              code-pinned attestation table
COMMIT BOUND  876c1b74131b4ab1a89dce433ecce646ba481f8c (the bundle's own)
```

Exactly two directories on this machine carry that run name, and both
precheck to the SAME summary digest: the ruled runs root above and its
attested archive under `itsf-runs-archive`. They are one bundle at two
paths, not two candidates — `contracts` distinguishes the roles, and
`E:\quant-data` (the attested backup root) is not mounted. The gate now
binds the DIGEST, so the path is no longer the security-relevant choice: a
substituted bundle refuses wherever it sits.

## Two legacy obligations, reclassified 2026-09-13

Under vNext §0 the MC five-event registry chain
(`MC_PACKET_DRAFTED → … → MC_RUN_AUTHORIZED`) and the `SMOKE-001` / E3
production-scale smoke are **HISTORICAL_WORKFLOW_OBLIGATION**, not current
research obligations. Their only authority is
`ops/DELEGATED_RULINGS_2026-08-24.md` (G1, G8), whose own header records
`RECORD_TYPE=DELEGATED_RULING`, `DECIDED_BY=Codex GPT-5.6 Sol` and
`DELEGATED=YES —— 这是委托裁定，不是 Aaron 本人的判断`, and which instructs
that it never be recorded as Aaron's judgement. Neither obligation appears in
the sealed `STUDY_0_PREREGISTRATION.md`, in the FROZEN `MC_METHOD_SPEC.md`, in
`PROJECT_CHARTER.md`, or in any Aaron `OWNER_DECISION` row. That is vNext
level 4 — generic project history — and level 4 cannot add an obligation vNext
does not carry.

What survives, and is enforced: vNext §10 makes a real MC Owner-only, and
DEC-N14-R1-7 (Aaron, level 1) keeps the writer boundary — a generic serialized
writer may never create or advance authorization state. The retired chain and
smoke were **not** rebuilt, **not** executed for compatibility, and **no**
replacement governance mechanism was created. `mc_contract`'s ratified grammar
is untouched: historical artifacts are not rewritten.

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
