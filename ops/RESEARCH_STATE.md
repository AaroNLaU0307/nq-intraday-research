# RESEARCH_STATE — ITSF (the ITSF stage authority under QROS-CF v2, per OD-CF-3)

```
RECORD_TYPE     = RESEARCH_STATE (QROS-CF v2 §2.2; one page; rewritten in place, history in git)
OUTCOME_CLEAN   = YES — never quarantined; restates no verdict, exposure count or revealed value
STAGE_AUTHORITY = this page (ITSF-only, DEC-0003). `qros check` validates seal / freshness / packet integrity and is not the stage authority
UPDATED         = 2026-09-10 (**N13 = CLOSED**. **N14 = ENTERED**, contract resolved from the quarantined DAG under Aaron's bounded-read authorization DEC-N14-READ-1; governed transport prepared, review NOT performed. REAL_MC = NOT AUTHORIZED; STATISTICAL_SIGNAL = NOT_TESTED)
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
| Last completed unit | **N11 — CLOSED** (see the Next-unit row). Before it, N10 — CLOSED. Before it, N09 — MC-DS-S004 terminal at P5 (registry seq 33, strict-blind headline replay PASS, 16/16 cells), framework HEAD `7a5570f` |
| Next unit | **N14 — ENTERED 2026-09-10, awaiting its required independent review.** The entry HOLD of earlier the same day is lifted: Aaron authorized a bounded read of the quarantined DAG authority (`DEC-N14-READ-1`) and **N14's contract is now resolved from authoritative text**. N14 = an **exact-tree review of the MC implementation**, `依赖 = N13` alone, actor = an independent non-builder seat, `数据面 = none`, and it **appends no READY row and authorizes nothing**. It sits **BEFORE any real MC**: N15 depends literally on `N14 PASS`, N16 is the real run and additionally needs Aaron's precise authorization, N17 is the reveal. Its completion token is **PASS**. Blindness (CLAIM_BLIND), budget (1 round, ≤ 2 per issue lineage) and failure routing come from `ops/REVIEWER_CONTRACT.md` §1/§2 and are recorded as a contestable builder determination in DEC-N14-READ-4. **The review has NOT been performed and N14 is NOT closed.** **Two** attempts were dispatched and **both returned no substantive verdict**: each seat stopped on a transport defect of the builder's making before inspecting any code. Attempt 1 was handed a dispatcher-only file that excluded itself from the read set; attempt 2 hit a requirement that the chat launch text be byte-identical to an on-disk Markdown block, which a chat layer cannot guarantee. Both recorded as **INVALID, not HOLD** (DEC-N14-ATTEMPT1-1, DEC-N14-ATTEMPT2-1); **neither consumed a round** and **neither produced an implementation finding**. Aaron struck the chat-byte-identity design out (DEC-N14-ATTEMPT2-2) and resolved the seat by session properties rather than product identity for this node only (DEC-N14-ATTEMPT2-3). Attempts 003, 004 and 005 followed, all stopped or retired before substantive review (DEC-N14-ATTEMPT3-1, DEC-N14-ATTEMPT4-1, DEC-N14-ATTEMPT5-1). **Aaron then adopted `CODE_REVIEW_BUNDLE_CONTRACT v1` prospectively (DEC-CRB-ADOPT-1)**: code-conformance review now travels as a sealed external bundle, and the old live-repo carrier/allowlist/freeze-pin transport is retired for that purpose. Attempts 001-005 keep their original contracts and rows. **Carried forward unchanged: LINEAGE = N14, SUBSTANTIVE_ROUND = 1 of at most 2, ROUND_CONSUMED = NO, IMPLEMENTATION_FINDING = NONE.** Aaron granted that admission and it was executed (DEC-CRB-ADMIT-1/2). The cut is now **HELD on a deeper blocker (B-35, DEC-CRB-HOLD-2)**: six of the 31 selected MC test files read outcome-carrying artifacts as part of their assertions, and five are the supplement batteries O13 and O4 depend on — so the surface cannot execute inside an OUTCOME_BLIND bundle without either removing the obligations or breaking the blindness model. REAL_MC = NOT AUTHORIZED. See DEC-N14-READ-1..6, B-33. |
| Last closed unit | **N13 — CLOSED 2026-09-10** (Aaron, DEC-N13-CLOSE-1/2). B-27 is implemented: the adopted ruling (full Cartesian M×K inside every B world, draws stable across phases, prefix-nested under doubling, within-world reduction then across-world P5/median, no pooling) is in `src/itsf/mc/grid_channel.py`, threaded through the ONE lifecycle site by a single `traded_selector` argument on `_paths_for_world`. The runner produces the K witness itself and reaches convergence → verdict → seal synthetically. The sealed `infeasible_by_sample` rule — mark, skip, report in full, continue — is implemented for the single-cell, mixed and **all-marked** grids. **Review history, preserved:** round 1 fresh Sol → HOLD on N13-F1; bounded repair; round 2 fresh GPT-6 Astra → HOLD on F1-R2-01; budget exhausted at 2 of 2; the round-2 HOLD escalated to Aaron, who authorized one bounded repair (`b2e7a3c`) and accepted it. **The final delta was NOT independently re-reviewed** — acceptance rests on builder-mechanical evidence, and the ledger says so. Tier A+B 5359 passed / 0 failed; full suite 5578 passed, 1 known B-20 xfail. Open NON-BLOCKING backlog: B-29 (N13-F2), B-30 (claim 13b). |
| Roadmap | N10 → N11 → N13 full MC → reveal / decision (owner checkpoint 3) → candidate strategy build → validation → final conclusion |
| Governance | **QROS-CF GOVERNANCE WINDOW = CLOSED.** **I1/I2 = SAFE TO ACTIVATE.** Closed by the final non-builder mechanical closure, which returned PASS on the closed-scope criteria A1–A6 / B1–B4 / S (TRANSPORT PASS; A+B 5253 passed 0 failed; full suite 5473 passed, 1 known historical B-20 xfail, 0 failed; real registry unchanged). Certified HEAD `2a358df37c1857ebe2a0c582139387f3b217936d`; final bounded repair `d063834bea5c0011cc4da503c2225e36f172bff7`; closure packet `ops/CLOSURE_CHECK_QROS_CF_FINAL_2026-09-07.md` sha256 `db878545e8475f662faf59fad38cd7f09567da50da8fd969c1dd2e704b5f15e9`; closure manifest sha256 `8dc5609c2b8996a9f8a6058688605d3d81712d65c26aaa193b21662409d8592e`. **No QROS-CF review or repair remains pending, and none is authorized.** The window's closing event is this closure itself, recorded as a row in `ops/DECISIONS.md` — DEC-0006's "first N10 AUTHORIZED row" formulation is superseded by that row, because N10 is not a run and has no AUTHORIZED row. Every earlier HOLD / returned-review record is preserved as history and none was rewritten into a PASS |

## 2. What exact research question are we answering

Verbatim from the sealed preregistration §0 (the question, not any answer):

- Q1: NQ 的 opening drive（09:30–10:00 方向性移动）之后，顺驱动方向的延续现象基础率与分布如何？
- Q2: 在 10:00 只完美知道"今天顺驱动方向交易是否值得"的 Oracle，受可执行约束与 Micro 整数仓位约束后，成本后表现如何？
- Q3: 将 Oracle 的逐日 USD P&L 分布交给 Prop MC，由商业 EV 裁决 GO / STOP / 边界区。

Current sub-question: the MC pipeline must produce the Checkpoint-0 statistic the sealed §10.4 decision table reads (STOP → GO → β → α, in that order). N09 supplied the day-strata supplement the MC consumes; N10/N11/N13 supply the rest.

## 3. What can legitimately block progress right now

Only rows in `ops/BACKLOG.md` §1 `CURRENT_BLOCKERS`. A row is admitted only if it names one of the six threats (T1 research correctness · T2 look-ahead/leakage · T3 data identity/provenance · T4 reproducibility · T5 real-run execution safety · T6 independent-verification validity) and a concrete failure path on the current or next stage. As of this update the table holds **zero open rows**; the candidates examined and why they were not admitted are listed under it.

**A CLOSED issue stays closed.** Reopening one requires NEW concrete evidence of a failure on the current path in exactly one of T1–T6 — correctness, reproducibility, data authority, independent-verification validity, or real-run safety. None of the following reopens anything: a cleaner architecture is imaginable; a stronger general guard could exist; another reviewer would add reassurance; historical packet wording could be improved. Two distinctions are load-bearing and were learned the expensive way during the QROS-CF window: a **transport / review-packaging** defect is not an implementation defect, and **reviewer-seat invalidation** is not an implementation HOLD. A closed-scope verification stays closed-scope; observations outside its criteria go to `ops/BACKLOG.md` §2.

## 4. What is explicitly deferred

`ops/BACKLOG.md` §2. Every older pending list (`WAITING_ON_AARON.md`, `NEXT_HANDOFF.md`, `PENDING_ANCHOR_UPDATES.md`, `DEFERRED_AFTER_MIGRATION.md`, `N08_SCOPE_UNRESOLVED.md`, the §B/§C/§D lists of `COMPLETION_AND_SIMPLIFICATION_PLAN_2026-09-05.md`, and the `qros status` HOLDs) has been triaged into it and now carries a pointer banner; none of them is a blocker source any more.

## 5. What evidence is required to finish this stage

- N10 (verification + attestation + pin): **CLOSED** by registry seq 33 and the I3 binding (B-21 discharged, DEC-N10-CLOSE-1). N11 (GRID/K wiring): tier A+B green at the governed-execution identity, synthetic end-to-end. N13 **BUILD** (the full MC runner): **CLOSED 2026-09-10** under §9's S3 exit plus §8's independent seat (DEC-N13-CLOSE-1/2). N13's **REAL RUN**, which is a different thing and is **NOT AUTHORIZED**: `PROPOSED` → Aaron's `AUTHORIZED` (binding the governed-execution identity and the output root) → `STARTED` → `SEALED` with a byte-identical archive copy → independent run-identity verification per declared scope (`ops/REVIEWER_CONTRACT.md` §3), recorded in the registry under the run grammar built inside N13's S3.
- Every consequential artifact recomputed inside some VERIFIED scope before the reveal reads it.
- The final Checkpoint-0 statistic: outcome-blind Stage I verification with the sealed preregistration's Lineage and the A2 record in the verifier's pre-freeze set, frozen recomputation before the sealed output is opened.

## 6. What is the termination condition

S4 terminates when N13's output is `SEALED`. S5 terminates when the Stage I verification is `VERIFIED`, the §10.4 decision table has been applied to the revealed statistic in the preregistered order, the result is expressed in legal KB vocabulary (`supported | not_promoted | falsified | unresolved`) with a `FAILURE_AUDIT` row if negative, and Aaron's checkpoint-5 decision is a row in `ops/DECISIONS.md`. Then the QROS §4 STOP rule applies: no further parameters, universes, thresholds or variants without a new research question and disclosed sample reuse.

Project-finishing rule (QROS-CF v2 §8, verbatim): if the current research question can be answered correctly and reproducibly, and no unresolved CURRENT_BLOCKER threatens that answer, proceed to the next research stage even if non-blocking governance backlog remains.

## 7. Who has authority to continue

- Engineering decisions: the builder (Aaron's delegation of 2026-08-29), recorded as rows, never approved.
- Owner checkpoints (QROS-CF v2 §7.4 + §2.3): (1) seal a FULL preregistration; (2) `AUTHORIZED` row for each real-data run; (3) reveal; (4) retire / re-research after a consequential negative or a third post-start failure for one purpose; (5) promote / falsify / not-promote, and any change to cost model, primary metric, or sample split; (6) verifier re-dispatch beyond the one retry, or any review beyond budget; (7) open a governance window. Owner hold / revocation rows: Aaron writes them himself in the registry.
- **Next owner act:** none outstanding for N10 — it is CLOSED. The next research unit is N11 (GRID/K wiring, structural, no run); the next real-data authorization is N13's. Previously: the other three P6 items are discharged: the window's implementation report was reviewed, the closing event is the final mechanical closure recorded in `ops/DECISIONS.md`, and the P2 gate-change review (DEC-0011) was superseded by the F01–F06 certification lineage that ended in that closure — nothing is PENDING_DISPATCH. No AUTHORIZED row is due for N10; the next real-data authorization is N13's.

## 8. When is an independent seat genuinely required

`ops/REVIEWER_CONTRACT.md` §2: the S2 pre-seal challenge (already past for ITSF-S0); claim-blind run-identity verification of every consequential sealed output, per declared scope; outcome-blind Stage I of the final statistic before reveal; a producer-vs-evidence conflict; a change to a tier-B authorization gate or to leakage-sensitive code (one round); Fable only on the QROS §7 trigger list. Nothing else by default.

## 9. When are tests enough

S3 exits on tier A+B green at the governed-execution identity plus a synthetic end-to-end exercise of the production path; no seat unless §8 names one. A reviewer who cannot name a threat returns PASS_WITH_BACKLOG, not HOLD.

## 10. When should the project STOP rather than add more governance

QROS-CF v2 §8: two consecutive proposed controls that protect only other controls; a review that cannot name a threat; a blocker extended once without clearing evidence; a verifier contaminated twice on one artifact. In each case: backlog, record, continue — or, if T1–T6 is threatened, a blocker row and Aaron decides. Governance change freeze is in force outside owner-opened windows.

## Known runtime gaps (informational, DEC-0003)

`qros status` for ITSF shows A2→B HOLD (sealed before the runtime existed; no runs/ A2 record can ever exist), I→J HOLD (Stage I bound to Review Packet records that predate the runtime; the S004 verification travelled as an attestation, not a packet), `trial_accounting` STALE (the pointer names the in-repo tombstone; the registry moved to `C:\Users\Aaron\quant-data\itsf-registry`), and 14 triggers UNASSESSED (no path map). All four are backlog rows; none holds a run mechanically (the runner's gates do not read `qros`).
