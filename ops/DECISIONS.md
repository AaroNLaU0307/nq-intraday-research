# DECISIONS — append-only ledger of owner decisions and review verdicts (QROS-CF)

```
RECORD_TYPE   = DECISIONS_LEDGER (QROS-CF v2 §10.1; replaces OWNER_DECISIONS_* / RULING_* / SEAT_RESULT_* as kinds)
APPEND_ONLY   = YES — rows are appended, never edited or reordered; a correction is a new row citing the row it corrects
OUTCOME_CLEAN = YES — no revealed verdict, exposure count, or measured value is ever restated here
CREATED       = 2026-09-07, P0 of the QROS-CF implementation window
```

Older owner decisions stay where they were written (`ops/OWNER_DECISIONS_2026-08-25.md` … `ops/OWNER_DECISIONS_2026-09-06.md`, `ADJUDICATIONS.md`, `ops/DELEGATED_RULINGS_2026-08-24.md`); this ledger starts at the QROS-CF acceptance and points backwards rather than copying.

Row shape: `id | date | decider | kind | verbatim or verdict | evidence pointer (path + sha256) | consequence`.

## Design lineage (files outside this repository, hashes recorded here)

| file (under `Quant trade\qros-cf-redesign\`) | sha256 | role |
|---|---|---|
| `QROS_CF_REDESIGN_PROPOSAL_2026-09-06.md` | `6a92343d49836671ae16e339bba2d0129a58ba9c97edc319c9f189191eedc904` | Fable first proposal v1 |
| `QROS_CF_ASTRA_CHALLENGE_PACKET_2026-09-06.md` | `dace95f7d82479f717da99ffb1c0f39c76dca947724b4d14ab600842a44ffedd` | challenge packet |
| `ASTRA_CHALLENGE_REPORT_2026-09-07_TRANSCRIPTION.md` | `ee04f37ee0ee8bc97724ee6d6a7899b5ea9c0d79b2a544651e02dc5e64f1ebff` | Astra report, transcription of a chat-carried review |
| `QROS_CF_CONVERGENCE_2026-09-07.md` | `b3fe115d554a6804d6644898a0a6b36b6be7bc31010057a45c9f882b5b4d8a8b` | converged design v2 (the authority for this window) |

## Rows

### DEC-0001 · 2026-09-07 · Aaron · OWNER_DECISION · QROS-CF v2 accepted (OD-CF-1)

Transcribed verbatim from Aaron's message of 2026-09-07 (chat-carried; this row certifies the transcription):

> Aaron has reviewed QROS-CF converged design v2. The convergence is ACCEPTED for ITSF. Do not reopen architecture design. Do not dispatch Astra again. Do not add a new redesign round.
>
> OD-CF-1 = ACCEPT
> QROS-CF v2 becomes the operating workflow for ITSF now.
> Other quant projects adopt it only at their next natural S1 boundary. This does not force an immediate migration of other projects.

Consequence: `QROS_CF_CONVERGENCE_2026-09-07.md` §2 is the operating workflow for ITSF from this row onward. Project-level; the global QROS v2.0.1 and L6 spec are not amended.

### DEC-0002 · 2026-09-07 · Aaron · OWNER_DECISION · directory creation folded into RUN authorization (OD-CF-2)

> OD-CF-2 = ACCEPT
> RUN authorization also authorizes creation of the run-specific subdirectory under the explicitly named output_root.
> Retire the separate directory-grant ceremony for future QROS-CF runs.

Consequence: for future runs the `AUTHORIZED` / P2 row's `output_root` grants creation of `<output_root>\supplements\<id>_<UTC>` (and the archive mirror). `ops/DIRECTORY_CREATION_GRANTS.md` is historical; no new grant records or pre/post snapshots are produced. The runner's `make_run_directory` seam is unchanged in this window (its authorization source is now the P2 row rather than a separate grant).

### DEC-0003 · 2026-09-07 · Aaron · OWNER_DECISION · L6 compatibility, ITSF-only scope (OD-CF-3)

> OD-CF-3 = ACCEPT WITH ITSF-ONLY SCOPE
> For ITSF: the structurally unsatisfiable legacy L6 HOLDs are INFORMATIONAL.
> RESEARCH_STATE.md becomes the ITSF stage authority.
> qros check remains a validator for: seal, freshness, packet integrity — and is NOT the ITSF stage authority.
> This interpretation is ITSF-specific. It does NOT amend the global L6 runtime specification or automatically apply to other projects.

Consequence: the state page `RESEARCH_STATE.md` under `ops/` (created at P1) is the ITSF stage authority. `qros status` transition HOLDs for ITSF (A2→B; I→J bound to packet records that predate the runtime) are recorded as backlog rows, not blockers. The three L6-recognised reviews (A2, Stage I, material-measurement) keep travelling as Review Packet v1 so §5.5.6 stays satisfiable.

### DEC-0004 · 2026-09-07 · Aaron · OWNER_DECISION · root exposure ledger frozen as history (OD-CF-4)

> OD-CF-4 = ACCEPT
> Freeze the root EXPOSURE_LEDGER.md as historical.
> Forward research-axis entries go only to the live ops exposure ledger.
> Before changing behaviour, mechanically prove no production or gate code still uses the historical root ledger as the live authority.
> If compatibility is required, preserve it minimally.

Consequence: recorded in this window's log (`QROS_CF_WINDOW_LOG_2026-09-07.md` under `ops/`, created at P1) with the mechanical proof (grep of `src/` and `scripts/` for readers of the root ledger). Forward research-axis rows go only to `ops/EXPOSURE_LEDGER.md`; the root file receives no further rows; the seat axis stays in `ops/REVIEWER_EXPOSURE_LOG.md`.

### DEC-0005 · 2026-09-07 · Aaron · OWNER_DECISION · builder may read the master plan for N10/N11/N13 (OD-CF-5)

> OD-CF-5 = ACCEPT OPTION 甲
> Aaron authorizes the builder to read the quarantined master plan necessary to recover the exact definitions and dependencies of: N10, N11, N13.
> Record the required research-axis exposure according to the existing rules.
> Do not inspect unrelated quarantined material.

Consequence: executed at P5 of this window; the read is bounded to the N10/N11/N13 definitions and its research-axis row is appended to `ops/EXPOSURE_LEDGER.md` per the existing classification rules.

### DEC-0006 · 2026-09-07 · Aaron · OWNER_DECISION · implementation window authorized, I1–I7 only (OD-CF-6)

> OD-CF-6 = ACCEPT
> Aaron explicitly authorizes implementation of ONLY convergence v2 §5: I1 through I7 in the migration order of §6.
> This governance implementation window begins now.
> It ENDS automatically at: P6 — the first N10 AUTHORIZED row.
> After that row, QROS-CF governance design is frozen again unless one of the explicit governance-reopen triggers occurs or Aaron opens a new window.
> Do not expand implementation beyond I1-I7.

Consequence: window open from this row; scope I1–I7; closes at the first N10 AUTHORIZED row, which this window does not append (P6 stops before it). Two implementation conditions attached, transcribed below as DEC-0008 and DEC-0009.

### DEC-0007 · 2026-09-07 · Aaron · OWNER_DECISION · verifier retry after one contamination (OD-CF-7)

> OD-CF-7 = ACCEPT
> After one verifier contamination, the builder may dispatch exactly ONE fresh retry without returning to Aaron.
> A second contamination for the same verification target requires Aaron.

Consequence: recorded in the reviewer contract page (`REVIEWER_CONTRACT.md` under `ops/`, created at P1) §4.

### DEC-0008 · 2026-09-07 · Aaron · IMPLEMENTATION_CONDITION · Condition A, T-F01 semantic dependency coverage

> The T-F01 perturbation battery must not interpret "dependency" as only repository files.
> Mechanically consider every input capable of changing production semantics, including where applicable: repository files; environment variables; external config; installed package/version drift; calendars; data/cache identity; external executable/runtime identity.
> Not every dependency must live inside GOVERNED_SET. But every production-semantic dependency must be constrained by at least one of: governed execution identity; lockfile/version gate; data identity manifest; explicit configuration identity; another existing fail-closed production gate.
> The acceptance test is behavioural: if a dependency can change the production result or its temporal/data semantics, changing it after authorization must either: 1. change the authorized identity, or 2. cause a refusal before the first write.

Consequence: the dependency register and the T-F01 battery (the execution-identity test module created at P2) are built to this condition; the coverage table is in the window log.

### DEC-0009 · 2026-09-07 · Aaron · IMPLEMENTATION_CONDITION · Condition B, owner-control grammar completeness

> Before implementing I2, mechanically inspect the current external registry grammar/parser. Determine whether it already supports legal representation of: OWNER_HOLD, OWNER_RELEASE, REVOKED.
> If any required row type is not representable: the MINIMUM parser/append support necessary for I2 is inside I2 scope.
> Do not create parallel ledgers or document-based owner holds as a workaround. The start gate must never depend on an owner-control state that cannot be legally and durably represented.

Consequence: inspection result and the minimum grammar support are recorded in the window log at P2.

### DEC-0010 · 2026-09-07 · Aaron · OWNER_INSTRUCTION · implementation order and completion-first boundaries

Aaron's order: P0 record decisions → P1 I6 documents + T-F17 estimate → P2 I1 + I2 with T-F01, T-F06, then exactly one fresh Sol/Astra claim-blind review of the tier-B gate change (max one round) → P3 I5 verifier tooling, T-F03 sentinel, S004 directory rehearsal → P4 I3 invariant split, I4 marker selection, T-F13, T-F15, A+B green, full suite green → P5 read the authorized minimum master-plan material and determine the exact N10 run family; implement a new grammar only if N10 genuinely requires it, inside N10 S3 with T-F02/T-F11 fixtures before PROPOSED → P6 STOP before appending the first N10 AUTHORIZED row and present the implementation to Aaron.

Boundaries before N10, verbatim: do NOT move the test directory tree merely for organisation; retire tier-C tests in bulk; archive ops/; build the public export; write governance-summary.md unless mechanically required by I1–I7; re-table L6; work on GRAD-*; modify the supplement grammar; reverify S004; redesign the research question; add trial-accounting rules; resolve second-volume backup; perform open-ended governance cleanup.

Routing note recorded by the builder: this window is implemented by the Fable session that authored the design, acting as builder by Aaron's explicit instruction (default routing would have used Opus). The P2 gate-change review is dispatched to a fresh Sol/Astra seat precisely because the producer may not certify it.

### DEC-0011 · 2026-09-07 · builder (prepared) / Aaron (dispatches) · REVIEW_DISPATCH · P2 gate-change review, claim-blind, one round — PENDING_DISPATCH

| field | value |
|---|---|
| scope | the P2 commit `bb7e69e` (governed-execution identity, owner control, condition.json manifest check) against its parent `7f78c47` |
| seat | fresh Sol/Astra session (`ops/REVIEWER_CONTRACT.md` §2, row "Change to a tier-B authorization gate"); MUST_NOT_BE the builder session or a subagent |
| blindness | CLAIM_BLIND |
| budget | one round; a HOLD is fixed once with a declared impact scope and re-reviewed once; then Aaron |
| brief | `C:\Users\Aaron\quant-data\review\itsf-qros-cf-p2-gate-review-2026-09-07\BRIEF.md` sha256 `fe7b76b8f9fbc9707bea6f47a65f744c685406b5f57f01fb6926c6e6886c0411` |
| dispatch | by Aaron, using `ops/templates/DISPATCH_TEMPLATE.md`; the builder may not dispatch a review of its own gate change |
| status | PENDING_DISPATCH — P3/P4/P5 do not depend on its result; the verdict lands as a REVIEW_VERDICT row citing the attestation's sha256 |

## QROS-CF governance window closure (2026-09-07)

| id | date | decider | kind | verdict | evidence pointer | consequence |
|---|---|---|---|---|---|---|
| DEC-CF-CLOSE-1 | 2026-09-07 | non-builder mechanical closure seat | REVIEW_VERDICT | **PASS** — A1–A6 PASS · B1–B4 PASS · S PASS · TRANSPORT PASS; `I1/I2 SAFE TO ACTIVATE`; `QROS-CF GOVERNANCE WINDOW CLOSED`; `MECHANICAL CLOSURE COMPLETE`; `NO FURTHER REVIEW OR REPAIR AUTHORIZED` | `ops/CLOSURE_CHECK_QROS_CF_FINAL_2026-09-07.md` sha256 `db878545e8475f662faf59fad38cd7f09567da50da8fd969c1dd2e704b5f15e9`; closure manifest sha256 `8dc5609c2b8996a9f8a6058688605d3d81712d65c26aaa193b21662409d8592e`; certified HEAD `2a358df37c1857ebe2a0c582139387f3b217936d`; final bounded repair `d063834bea5c0011cc4da503c2225e36f172bff7` | the QROS-CF governance window is CLOSED and I1/I2 are SAFE TO ACTIVATE. A+B 5253 passed / 0 failed; full suite 5473 passed / 1 known historical B-20 xfail / 0 failed; real registry unchanged |
| DEC-CF-CLOSE-2 | 2026-09-07 | Aaron | OWNER_DECISION | this closure is the window's closing event, superseding DEC-0006's "first N10 AUTHORIZED row" formulation (N10 is not a run and has no AUTHORIZED row) | this ledger; `ops/RESEARCH_STATE.md` §1 Governance | the window closes without waiting for a run that the DAG never required |
| DEC-CF-CLOSE-3 | 2026-09-07 | Aaron | OWNER_DECISION | the P2 gate-change review recorded above as `PENDING_DISPATCH` (DEC-0011) is **superseded, not owed**: the same gate change was carried into the F01–F06 certification lineage and adjudicated by the closure in DEC-CF-CLOSE-1 | `ops/FABLE_DESIGN_REVIEW_QROS_CF_FINAL_2026-09-07_TRANSCRIPTION.md`; the three preserved HOLD packets | nothing is PENDING_DISPATCH; no QROS-CF review or repair remains authorized |
| DEC-CF-CLOSE-4 | 2026-09-07 | Aaron | OWNER_DECISION | research resumes at **N10 → N11 → N13**; N10/N11/N13 were deliberately untouched throughout the governance window | `ops/RESEARCH_STATE.md` §1 Roadmap | the next research unit is N10; no automatic PR, push, merge or revert is authorized unless Aaron asks for it |

## N10 closure (2026-09-07)

| id | date | decider | kind | verdict | evidence pointer | consequence |
|---|---|---|---|---|---|---|
| DEC-N10-CLOSE-1 | 2026-09-07 | Aaron | OWNER_DECISION | **N10 = CLOSED.** B-21 discharged. Its authoritative definition (DEC-0005 bounded read) is "independent verification + attestation + pin (two-commit sequence)", it has **no event family** and is not a run; all three parts already existed and were reconciled mechanically rather than re-created | independent verification: registry seq 33 `SUPPLEMENT_INDEPENDENTLY_VERIFIED`, actor `independent verifier (fable_5.1_session_2f29a987)`, `rederivation_reproduced: YES`, `headline_replay_identity: PASS`, `n_cells: 16` · attestation `0b5d9382c2d547309578a2d5e8f1ff4b345c4d45feaf2c9f367c322f158cb8b7` (`P5_ATTESTATION_MC-DS-S004.md`, bytes hash to the cited value; restates `MC-DS-S004`, sealed artifact `f59a009213f2e3b9ce3b4b4937c1945227c89e724fc6c4fa0c063d0326417e4d`, rows digest `cd8b6701768de1d648471ed2b6be6fa281bf7766445fd219f416cdad191f7255`, session `2f29a987`) · witness `WITNESS_P5_S004_APPENDED_2026-09-06.json` · pin: `registry_integrity.current_dependency_check` returns `ok=True`, checks `binding of P5 seq 33`, zero problems, run live against the registry at `729daa8` | N10 is closed with **no registry mutation** (it has no events), **no new evidence**, and **no new reviewer round** — the required independent verification already exists and was performed by a non-builder seat. Next research unit: **N11** |
| DEC-N10-CLOSE-2 | 2026-09-07 | Aaron | OWNER_DECISION | the definition's **"two-commit sequence"** is discharged, not outstanding: it named the after-the-fact registration pattern that QROS-CF **retired**, and the surviving sequence is registry-append then framework-binding, in that order | first `729daa80196aa4f7fa1aa590e32840942d827392` (registry, 2026-09-06 22:34:46 +0800, seq-33 P5 appended) → second `56cf03898848f5c39601ebc8155cc412f2896d18` (framework, 2026-09-07 03:58:59 +0800, I3 binding introduced; the registration table removed from `tests/test_mc_supplement_integration.py`, now 0 occurrences) | ordering PASS; no third commit is owed and none was created for tidiness |

## N11 design read (2026-09-08)

| id | date | decider | kind | verdict | evidence pointer | consequence |
|---|---|---|---|---|---|---|
| DEC-N11-READ-1 | 2026-09-08 | Aaron | OWNER_DECISION | **bounded read authorized** of the quarantined material needed to recover the authoritative N11 design — scoped to N11, `GridReplayAuthority`, `KReplayEvidence`, the GRID→K wiring, the rule (a)-(d) computation, replay identity / provenance / binding semantics, and the N11 closure condition; explicitly NOT authorization to open the plan broadly, inspect unrelated outcomes, expose target metrics, or read N13 outcome material | research-axis row appended to `ops/EXPOSURE_LEDGER.md` (NO_OUTCOME, 数量=0, 3 lines redacted by the six outcome patterns and never displayed); the DEC-0005 extractor mechanism, unchanged | the design was recovered: **N-D2 items M6-M10**, `RATIFIED_UNCHANGED` 2026-08-24 (Sol, under Aaron's named batch delegation, `DELEGATED=YES`). N11 is implemented on that basis. One point M8 leaves unsettled is referred back as **B-25** rather than settled by the builder |

## B-25 — the boundary band and the existential (2026-09-08)

| id | date | decider | kind | verdict | evidence pointer | consequence |
|---|---|---|---|---|---|---|
| DEC-N11-B25-1 | 2026-09-08 | Aaron | OWNER_DECISION | **interpretation (ii).** Boundary-band classification applies to the CELL-LEVEL EXISTENTIAL REGION DECISION. A non-decisive combination must NOT veto convergence merely because its own statistics lie outside the band. A cell is boundary only when the combination-level statistic(s) that actually determine its existential region membership lie within the already-frozen M8 band. For the referred case — combo A stably far negative (−$5000), combo B the existentially relevant candidate moving +$3 → −$2 — the boundary logic is governed by B and is NOT vetoed by A. **This ruling introduces no new tolerance**; only the already-ratified M8 band is used, and it must not be reinterpreted as "all combinations must satisfy the band" | `src/itsf/mc/grid_replay.py` — `satisfying_combos` (the frozen per-combination predicate, single source of both the cell's class and of which combinations changed it) and `compare_region_maps` (deciding set = `satisfying(K) XOR satisfying(2K)`); `tests/test_mc_grid_replay_n11.py::test_b25_case1_a_non_decisive_combination_does_not_veto` fails under (i) and passes only under (ii); `::test_b25_case4_the_ruling_introduced_no_new_tolerance` asserts mechanically that no epsilon, threshold, percentage or second tolerance entered | **B-25 CLOSED**; the refusal code `grid_replay_boundary_band_multi_combo_unruled` is removed because the case it named is now ruled. **N11 = CLOSED** — its closure conditions are satisfied (tier A+B 5295 passed / 0 failed; full suite 5515 passed, 1 known B-20 xfail). B-26 is untouched and out of scope |
| DEC-N11-B25-2 | 2026-09-08 | Aaron | OWNER_DECISION | **B-25 semantic acceptance check: PASS, and a CORRECTION to the evidence wording of DEC-N11-B25-1.** That row described the deciding set as `satisfying(K) XOR satisfying(2K)` without stating the precondition, and the module docstring went further and claimed a cell's class "changes exactly when the satisfying set changes". **That claim is false**: witness substitution — `satisfying(K)={A}`, `satisfying(2K)={B}`, IN at both passes — changes the set completely while membership holds. The RULING and the CODE were never wrong: `compare_region_maps` compares the cell-level classes first and returns before the deciding set is computed, so M8 was never reachable by witness substitution. Only the prose was wrong | measured: `satisfying(K)={A}`, `satisfying(2K)={B}`, XOR={A,B} non-empty, `cell_category` IN at both, `boundary_band_cells=()` and `flipped_cells=()` — M8 did NOT fire, while rule (c) independently reported 126 drift violations and `converged=False`. The executable AST of `grid_replay.py` is byte-identical to the pre-correction commit with docstrings stripped, so the fix is documentation-only. Pinned by `tests/test_mc_grid_replay_n11.py::test_b25_caseA..caseD` and `::test_b25_membership_not_witness_identity_gates_m8`, which asserts `M8 fired IFF the class changed` across all four cases | **B-25 stays CLOSED** and **N11 stays CLOSED**; no production-logic change was made and none was warranted. Tier A+B 5300 passed / 0 failed; full suite 5520 passed, 1 known B-20 xfail |

## N13 / B-27 — the adopted GRID semantics and the review it owes (2026-09-08)

| id | date | decider | kind | verdict | evidence pointer | consequence |
|---|---|---|---|---|---|---|
| DEC-N13-B27-1 | 2026-09-08 | Aaron | OWNER_DECISION | **the adopted B-27 ruling, recorded verbatim in substance and frozen for implementation:** "the GRID channel shall compose K stratified TP/FP marker draws per cell and governed seed with M exhaustive legal start phases by the full Cartesian product within every existing B/world. Each draw shall retain its marker sequence across phase evaluations, and every `(world, phase, draw)` combination shall contribute exactly once through the governed lifecycle using the unchanged prepared population and calendar. The M×K inner empirical distribution shall enter the existing within-world statistical reduction, with Conservative P5 and Stress median computed through the unchanged epistemic aggregation across B worlds; raw lifecycle outcomes shall not be pooled across worlds to redefine those percentiles. Doubling K shall append K draws, preserve the first K draws and their outputs through the frozen streams and common random numbers, and leave B, M, non-GRID randomness, Oracle semantics, feasibility methodology, and convergence criteria unchanged. Computational optimizations are permitted only when exactly equivalent to this rule. Adoption permits bounded N13 implementation to resume and grants no real-MC or N14 authorization." | implemented at commit `c98a0ef776df76b3d0b0c76935bb8f388413c246` (tree `17a8aa37d3db133343dce38965e31d2ac2fe9aa8`): `src/itsf/mc/grid_channel.py` composes B×M×K atoms keyed `(world, phase, draw)`; the selector seam is one `traded_selector` argument on `consumer._paths_for_world`; the within-world reduction and the across-world P5/median are the repository's own unchanged functions. Pinned by `tests/test_mc_grid_channel_b27.py` (proofs A–H) and `tests/test_mc_runner_n13.py` | **B-27 DESIGN CLOSED, IMPLEMENTATION COMPLETE.** The ruling's own scope limit stands: **no real-MC authorization and no N14 authorization** follow from it. The architecture question is not reopened |
| DEC-N13-B27-2 | 2026-09-08 | builder (prepared) / Aaron (dispatches) | REVIEW_DISPATCH | **N13 gate-change review, claim-blind, one round — PENDING_DISPATCH.** Required by `ops/REVIEWER_CONTRACT.md` §2 row "Change to a tier-B authorization gate or leakage-sensitive code": the GRID selector decides which days a cell trades, which is T2 look-ahead/leakage territory, and `ops/RESEARCH_STATE.md` §9 defers to §8, placing the round inside N13's exit rather than N14's. **This dispatch is the one fresh retry §4.4 allows after a transport failure**: the first seat never reached implementation inspection because the governed transport did not exist, and it touched the quarantined subtree during authority discovery, so it is not reusable. That was a TRANSPORT failure and is not evidence of a B-27 implementation defect | scope: framework commit `c98a0ef776df76b3d0b0c76935bb8f388413c246`, tree `17a8aa37d3db133343dce38965e31d2ac2fe9aa8`, parent `21d2dc75b4d9ae27cb630930c4c3d8ffc52001af` · seat: fresh Sol session, `MUST_NOT_BE` the producing session, a subagent of it, or the failed seat · blindness: CLAIM_BLIND · budget: one round · brief: `C:\Users\Aaron\quant-data\review\itsf-n13-b27-grid-selector-review-2026-09-08\BRIEF.md` sha256 `e9c483667399e4a82102e31d8ea4ec892ca351e7d576df92118cb4453b5edb03` · dispatch: `…\DISPATCH.md` sha256 `4b719633d3ebe1efd540629406722e21e0cdb342275ea12ea355bc85c0f2a8b6` · spec/manifest (off-limits list AND exhaustive read allowlist, one file): `ops/OFF_LIMITS_N13_B27_REVIEW_2026-09-08.md` sha256 `3192f1018ffb05f6476515c1adbd467bf561f2878e1cf908e81909ed3f86048d` · authority: `ops/REVIEWER_CONTRACT.md` sha256 `14e2d84defc6a77e408bba37806246d220e1bd2ee5af836a730843443d87d72a` · frozen set and pin: `ops/ARTIFACTS_UNDER_REVIEW.json`, 28 entries, pin `c98a0ef776df76b3d0b0c76935bb8f388413c246` (the pin is the one `derive_pin` computes, and it equals the review target) · review id: see that register | **PENDING_DISPATCH — dispatched by Aaron; the builder may not dispatch a review of its own leakage-sensitive code and may not perform it.** N13 stays `BUILDER_COMPLETE_AWAITING_VALID_FRESH_REVIEW`; `READY_FOR_N14 = NO`. The verdict lands as a second row (kind REVIEW_VERDICT) citing the attestation's sha256, at which point the register is cleared **before** any repair |
| DEC-N13-B27-3 | 2026-09-08 | builder | TRANSPORT_NOTE | the contamination protocol (`ops/REVIEWER_CONTRACT.md` §4, `scripts/build_verifier_dir.py`) is **not** the mechanism for this review, and the reason is mechanical rather than a preference: that script refuses every source under `ops/` or `tests/`, so it cannot carry a review whose object is code and whose evidence is its tests. §2's last line governs instead — "every review outside the three L6-recognised ones is a one-page brief" — and the precedent for this table row is the P2 gate-change review of 2026-09-07, which scoped reads **in** the repository at a frozen commit and hashed twelve files including two under `tests/` | `scripts/build_verifier_dir.py` `_forbidden_source` (refuses `ops/`, `tests/`) and its `code_paths` check (`rel.startswith(("ops/", "tests/"))` is "not exportable"); `C:\Users\Aaron\quant-data\review\itsf-qros-cf-p2-gate-review-2026-09-07\BRIEF.md` §2 (12-file hash table, `tests/tiers.py` and two `tests/test_*.py` among them); DEC-0011 | the precedent is followed and tightened where the previous seat actually broke: its deny-list becomes an exhaustive **allow**list, and out-of-allowlist access is STOP rather than discouraged. No new dispatch grammar was invented |

## N13 / B-27 — transport revision 2 (2026-09-08)

| id | date | decider | kind | verdict | evidence pointer | consequence |
|---|---|---|---|---|---|---|
| DEC-N13-B27-4 | 2026-09-08 | builder (prepared) / Aaron (dispatches) | REVIEW_DISPATCH | **transport revision 2 — supersedes DEC-N13-B27-2's package, PENDING_DISPATCH.** The second fresh Sol seat verified the R1 transport correctly and then stopped with `ALLOWLIST_INSUFFICIENT`: R1's Claim 13 demanded proof of real governed `infeasible_by_sample` reachability, which turns on the outcome-derived TP/FP split the allowlist withholds on purpose. **That was a REVIEW/PACKAGING defect — the brief turned a conditional, always-non-blocking item into a mandatory claim whose uncertainty stopped the entire substantive review.** No implementation verdict was issued and no implementation defect was established. R2 rewrites that one item and nothing else: claims 1–12 and 14 are byte-identical in substance, and **no production byte changed** | brief `C:\Users\Aaron\quant-data\review\itsf-n13-b27-grid-selector-review-2026-09-08\BRIEF.md` sha256 `4c3df08117164bf3dceb4fc37db12b5574132017e6f84651d53a5b9efec1fbd1` · dispatch `…\DISPATCH.md` sha256 `0230f9de82e4c005db890b06efbbf30e1dfc61d3f00ec28d26f2b406aeb1dca7` · manifest/allowlist `ops/OFF_LIMITS_N13_B27_REVIEW_2026-09-08.md` sha256 `b416a156331d76ff9d7756d32cb52349703ee91db965ffd54f5020ccb8166470` · sealed prereg `STUDY_0_PREREGISTRATION.md` sha256 `6cca20b7b1ce496d582ef5b4677333ba1b74bc577020ab29df00ff0c0d1af132` · register `ops/ARTIFACTS_UNDER_REVIEW.json`, 28 entries, pin `c98a0ef776df76b3d0b0c76935bb8f388413c246` (re-derived, unchanged) · target commit `c98a0ef776df76b3d0b0c76935bb8f388413c246`, tree `17a8aa37d3db133343dce38965e31d2ac2fe9aa8` · review id: see that register | **PENDING_DISPATCH to ONE NEW fresh Sol seat, claim-blind, one round.** Neither prior seat is reusable. N13 stays `BUILDER_COMPLETE_AWAITING_VALID_FRESH_REVIEW`; `READY_FOR_N14 = NO` |
| DEC-N13-B27-5 | 2026-09-08 | builder | AUTHORITY_FINDING | **no repository authority makes `infeasible_by_sample` reachability an N13 closure proof, and lawful handling for the state already exists and is SEALED.** The token appears nowhere in `ops/RESEARCH_STATE.md` §§5/8/9, `ops/REVIEWER_CONTRACT.md` or `ops/BACKLOG.md`. It appears **once** in the sealed preregistration, which rules it: 「全部层合计仍不足时，该网格点标记 `infeasible_by_sample` 跳过并完整报告」 — mark the grid point, skip it, report it in full | `ops/RESEARCH_STATE.md` §9 "A reviewer who cannot name a threat returns PASS_WITH_BACKLOG, not HOLD"; §10 "backlog, record, continue"; §6 quoting QROS-CF v2 §8 verbatim ("even if non-blocking governance backlog remains"); `ops/REVIEWER_CONTRACT.md` §1 "NON-BLOCKING findings … never hold"; `STUDY_0_PREREGISTRATION.md` (frozen grid / rounding section), sha256 `6cca20b7b1ce496d582ef5b4677333ba1b74bc577020ab29df00ff0c0d1af132` | the item is **CONDITIONAL_NON_BLOCKING**. Because lawful handling exists, the open question narrows to one that needs no outcome data: `s0.gridmix._grid_point` marks/skips/returns, while `mc.grid_channel.derive_cell_draws` **raises** — whether the raise preserves the sealed semantics is claim 13a and is the reviewer's to settle. **The builder asserts no answer** |
| DEC-N13-B27-6 | 2026-09-08 | builder | TRANSPORT_TOOL_CONFLICT | **reported, not silently resolved.** The sealed preregistration is now on the reviewer's allowlist (it is the authority for 13a, and without it the reviewer would verify code against a builder-supplied quote). Registering it in `ops/ARTIFACTS_UNDER_REVIEW.json` pulls it into `tests/test_delivery_names_no_quarantined_path.py::test_a_live_delivery_never_names_a_quarantined_path_unmarked`, which fires on its **line 157** — the preregistered `researcher_exposure` plan, which names `EXPOSURE_LEDGER.md` without an off-limits marker. The only two ways to clear that guard are **editing a SEALED artifact** (breaking `seal_revision c685ebc1…`, whose bytes `qros check` verifies) or **widening a governance guard** whose own docstring rejects widening. Neither is permitted | the guard at `tests/test_delivery_names_no_quarantined_path.py` lines 109–129 (registered `.md` paths are pulled into `_live_delivery_documents`) and 212–229; `STUDY_0_PREREGISTRATION.md:157`; `qros-state.yaml` `seal_revision`; the prereg's last change is the July freeze commit `89e2505`, and `git log c98a0ef776df76b3d0b0c76935bb8f388413c246..HEAD -- STUDY_0_PREREGISTRATION.md` is empty | **resolution taken:** the prereg is handed over through the delivery's allowlist **without** a register entry — the register is the only route into that guard's scope, since the file is at the repository root rather than under `ops/` — and the delivery carries an explicit off-limits marker warning the seat that the prereg's own line names a quarantined ledger. The guard's protective purpose is served by the document the builder controls instead of by falsifying a sealed one. **Its bytes are frozen more strongly than a register entry could manage**: unchanged since `89e2505` and verified against HEAD by `qros check` on every run. **No governance code was altered.** If Aaron prefers a different resolution, this row is the place it changes |

## N13 — the fresh-Sol verdict, and the F1 repair (2026-09-08)

| id | date | decider | kind | verdict | evidence pointer | consequence |
|---|---|---|---|---|---|---|
| DEC-N13-B27-7 | 2026-09-08 | fresh Sol seat (claim-blind, one round) | REVIEW_VERDICT | **HOLD.** The mandatory gate-change review of the frozen implementation completed as a review process and returned one BLOCKING finding. **Claims 1-11 and 14 ESTABLISHED.** **Claim 12 REFUTED but classified NON-BLOCKING** (a hand-built `GridDraw` can be forged via `object.__new__` plus a recomputed self-digest; the governed runner accepts no caller-supplied draw on the seal path) -> **N13-F2**. **Claim 13a REFUTED and BLOCKING** -> **N13-F1**, threat **T1 research correctness**: the sealed preregistration requires an `infeasible_by_sample` grid point to be marked, skipped, reported in full and the pass CONTINUED, while the implementation raises out of `derive_cell_draws` and aborts the whole pass. **Claim 13b `INCONCLUSIVE_NON_BLOCKING`**, which is the branch the revised brief anticipated | reviewed target `c98a0ef776df76b3d0b0c76935bb8f388413c246`, tree `17a8aa37d3db133343dce38965e31d2ac2fe9aa8`; transport revision 2 (brief `4c3df08117164bf3dceb4fc37db12b5574132017e6f84651d53a5b9efec1fbd1`, manifest `b416a156331d76ff9d7756d32cb52349703ee91db965ffd54f5020ccb8166470`); review id and retired freeze set in `ops/ARTIFACTS_UNDER_REVIEW.json` `_last_returned_review`. **The attestation file was NOT supplied to the builder** — the verdict reached this session as Aaron's transcription in the repair instruction, so **no attestation sha256 is cited and none was invented**; a correcting row is the place to add it | the register was cleared **before** any repair (verdict returns -> clear -> repair). **N13-F1 is a real current-path blocker and is repaired in this run.** N13-F2 stays NON-BLOCKING backlog and is **not** repaired. Claim 13b needs nothing. The repaired tree is a NEW target: this verdict does **not** transfer to it |
