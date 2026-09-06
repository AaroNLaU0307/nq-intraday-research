# RESEARCH_STATE — ITSF (the ITSF stage authority under QROS-CF v2, per OD-CF-3)

```
RECORD_TYPE     = RESEARCH_STATE (QROS-CF v2 §2.2; one page; rewritten in place, history in git)
OUTCOME_CLEAN   = YES — never quarantined; restates no verdict, exposure count or revealed value
STAGE_AUTHORITY = this page (ITSF-only, DEC-0003). `qros check` validates seal / freshness / packet integrity and is not the stage authority
UPDATED         = 2026-09-07 (P5 of the QROS-CF implementation window)
```

## 0. Who is reading this

- **Outcome-blind seat** (Stage I, A2, anything told to stay blind): stop here. Read `ops/RECOVERY_ANCHOR.md` §0–§2 and §5 only, do not search this repository, and take every byte you need from the dispatcher's external evidence directory (`ops/REVIEWER_CONTRACT.md` §3).
- **Builder / owner / exposed seat**: this page answers the ten questions below; everything pending is in `ops/BACKLOG.md`; every decision is a row in `ops/DECISIONS.md`.

## 1. What stage are we in

| Field | Value |
|---|---|
| Research id · lane | ITSF-S0 · FULL (declared by Aaron 2026-08-24) |
| QROS-CF stage | **S4 RUN** for the MC pipeline (QROS alias C/E): sealed preregistration, build complete through N09, real-data runs in progress |
| Preregistration | `STUDY_0_PREREGISTRATION.md`, sealed (`qros check` SEAL=VERIFIED at the revision named in `qros-state.yaml`) |
| Last completed unit | N09 — MC-DS-S004 terminal at P5 (registry seq 33, strict-blind headline replay PASS, 16/16 cells), framework HEAD `7a5570f` |
| Next unit | **N10 is not a run.** Its master-plan definition (DEC-0005 bounded read, P5): "独立验证＋attestation＋pin（两 commit 序列）", depends on N09, kind 工程＋Codex, structural. The independent verification and the attestation exist (registry seq 33, strict-blind P5 PASS, attestation `0b5d9382…`); the "pin" — formerly a two-commit registration of the rows into the framework — is now carried by the I3 binding (`registry_integrity.current_dependency_check`, verified live at P4). **Whether N10 is thereby closed is Aaron's call (P6 item).** N11 = GRID/K wiring (GridReplayAuthority + KReplayEvidence), depends on N07 and N10, structural, no run. N13 = the full MC runner, depends on N11, N-D3, N12; its MC_RUN_* events are the deferred ND-3 tokens — the first family that needs the QROS-CF run grammar, to be built inside N13's S3 with T-F02/T-F11 fixtures before its PROPOSED row |
| Roadmap | N10 → N11 → N13 full MC → reveal / decision (owner checkpoint 3) → candidate strategy build → validation → final conclusion |
| Governance | QROS-CF implementation window: I1–I7 implemented (P0–P5 committed); DEC-0006 closes it "at the first N10 AUTHORIZED row" — N10 has no AUTHORIZED row because it is not a run, so the closing event is Aaron's to name at P6 (recommendation: the first AUTHORIZED row of the first run after N10, i.e. N13's, or an explicit closing row in DECISIONS.md) |

## 2. What exact research question are we answering

Verbatim from the sealed preregistration §0 (the question, not any answer):

- Q1: NQ 的 opening drive（09:30–10:00 方向性移动）之后，顺驱动方向的延续现象基础率与分布如何？
- Q2: 在 10:00 只完美知道"今天顺驱动方向交易是否值得"的 Oracle，受可执行约束与 Micro 整数仓位约束后，成本后表现如何？
- Q3: 将 Oracle 的逐日 USD P&L 分布交给 Prop MC，由商业 EV 裁决 GO / STOP / 边界区。

Current sub-question: the MC pipeline must produce the Checkpoint-0 statistic the sealed §10.4 decision table reads (STOP → GO → β → α, in that order). N09 supplied the day-strata supplement the MC consumes; N10/N11/N13 supply the rest.

## 3. What can legitimately block progress right now

Only rows in `ops/BACKLOG.md` §1 `CURRENT_BLOCKERS`. A row is admitted only if it names one of the six threats (T1 research correctness · T2 look-ahead/leakage · T3 data identity/provenance · T4 reproducibility · T5 real-run execution safety · T6 independent-verification validity) and a concrete failure path on the current or next stage. As of this update the table holds **zero open rows**; the candidates examined and why they were not admitted are listed under it.

## 4. What is explicitly deferred

`ops/BACKLOG.md` §2. Every older pending list (`WAITING_ON_AARON.md`, `NEXT_HANDOFF.md`, `PENDING_ANCHOR_UPDATES.md`, `DEFERRED_AFTER_MIGRATION.md`, `N08_SCOPE_UNRESOLVED.md`, the §B/§C/§D lists of `COMPLETION_AND_SIMPLIFICATION_PLAN_2026-09-05.md`, and the `qros status` HOLDs) has been triaged into it and now carries a pointer banner; none of them is a blocker source any more.

## 5. What evidence is required to finish this stage

- N10 (verification + attestation + pin): closed by registry seq 33 and the I3 binding if Aaron so decides (B-21). N11 (GRID/K wiring): tier A+B green at the governed-execution identity, synthetic end-to-end. N13 (the full MC runner): `PROPOSED` → Aaron's `AUTHORIZED` (binding the governed-execution identity and the output root) → `STARTED` → `SEALED` with a byte-identical archive copy → independent run-identity verification per declared scope (`ops/REVIEWER_CONTRACT.md` §3), recorded in the registry under the run grammar built inside N13's S3.
- Every consequential artifact recomputed inside some VERIFIED scope before the reveal reads it.
- The final Checkpoint-0 statistic: outcome-blind Stage I verification with the sealed preregistration's Lineage and the A2 record in the verifier's pre-freeze set, frozen recomputation before the sealed output is opened.

## 6. What is the termination condition

S4 terminates when N13's output is `SEALED`. S5 terminates when the Stage I verification is `VERIFIED`, the §10.4 decision table has been applied to the revealed statistic in the preregistered order, the result is expressed in legal KB vocabulary (`supported | not_promoted | falsified | unresolved`) with a `FAILURE_AUDIT` row if negative, and Aaron's checkpoint-5 decision is a row in `ops/DECISIONS.md`. Then the QROS §4 STOP rule applies: no further parameters, universes, thresholds or variants without a new research question and disclosed sample reuse.

Project-finishing rule (QROS-CF v2 §8, verbatim): if the current research question can be answered correctly and reproducibly, and no unresolved CURRENT_BLOCKER threatens that answer, proceed to the next research stage even if non-blocking governance backlog remains.

## 7. Who has authority to continue

- Engineering decisions: the builder (Aaron's delegation of 2026-08-29), recorded as rows, never approved.
- Owner checkpoints (QROS-CF v2 §7.4 + §2.3): (1) seal a FULL preregistration; (2) `AUTHORIZED` row for each real-data run; (3) reveal; (4) retire / re-research after a consequential negative or a third post-start failure for one purpose; (5) promote / falsify / not-promote, and any change to cost model, primary metric, or sample split; (6) verifier re-dispatch beyond the one retry, or any review beyond budget; (7) open a governance window. Owner hold / revocation rows: Aaron writes them himself in the registry.
- **Next owner act (P6):** review the window's implementation report; decide whether N10 is closed by seq 33 + the I3 binding; name the window's closing event; dispatch the pending P2 gate-change review (DEC-0011). No AUTHORIZED row is due for N10; the next real-data authorization is N13's.

## 8. When is an independent seat genuinely required

`ops/REVIEWER_CONTRACT.md` §2: the S2 pre-seal challenge (already past for ITSF-S0); claim-blind run-identity verification of every consequential sealed output, per declared scope; outcome-blind Stage I of the final statistic before reveal; a producer-vs-evidence conflict; a change to a tier-B authorization gate or to leakage-sensitive code (one round); Fable only on the QROS §7 trigger list. Nothing else by default.

## 9. When are tests enough

S3 exits on tier A+B green at the governed-execution identity plus a synthetic end-to-end exercise of the production path; no seat unless §8 names one. A reviewer who cannot name a threat returns PASS_WITH_BACKLOG, not HOLD.

## 10. When should the project STOP rather than add more governance

QROS-CF v2 §8: two consecutive proposed controls that protect only other controls; a review that cannot name a threat; a blocker extended once without clearing evidence; a verifier contaminated twice on one artifact. In each case: backlog, record, continue — or, if T1–T6 is threatened, a blocker row and Aaron decides. Governance change freeze is in force outside owner-opened windows.

## Known runtime gaps (informational, DEC-0003)

`qros status` for ITSF shows A2→B HOLD (sealed before the runtime existed; no runs/ A2 record can ever exist), I→J HOLD (Stage I bound to Review Packet records that predate the runtime; the S004 verification travelled as an attestation, not a packet), `trial_accounting` STALE (the pointer names the in-repo tombstone; the registry moved to `C:\Users\Aaron\quant-data\itsf-registry`), and 14 triggers UNASSESSED (no path map). All four are backlog rows; none holds a run mechanically (the runner's gates do not read `qros`).
