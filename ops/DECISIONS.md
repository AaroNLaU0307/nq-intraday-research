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
