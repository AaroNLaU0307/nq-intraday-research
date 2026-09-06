# QROS-CF implementation window — run log (one file for the whole window)

```
RECORD_TYPE = WINDOW_LOG (the single run log of the DEC-0006 window; appended per phase, never one document per event)
WINDOW      = opened 2026-09-07 by DEC-0006; scope I1–I7 of QROS_CF_CONVERGENCE_2026-09-07.md §5; closes at the first N10 AUTHORIZED row
BUILDER     = Claude Fable 5.1 (design author, acting as builder by Aaron's explicit instruction — DEC-0010)
OUTCOME_CLEAN = YES
START_HEAD  = 7a5570fb2fbfd9dd28ed19c63d41c3ba01e5964a
```

## P0 — decisions recorded

Commit `13094d3`: `ops/DECISIONS.md` rows DEC-0001..DEC-0010 (OD-CF-1..7, Conditions A/B, order and boundaries), README index row. Document guards green (81 passed). No code, registry, or ledger change.

## P1 — I6 core documents and the T-F17 estimate

Created: `ops/RESEARCH_STATE.md` (ITSF stage authority, DEC-0003), `ops/BACKLOG.md` (the single blocker set: zero open rows; 19 backlog rows; 9 closed items with evidence), `ops/REVIEWER_CONTRACT.md`, this log. Every older pending list now carries a pointer banner to `BACKLOG.md`; `RECOVERY_ANCHOR.md` §3 points builders/owners at `RESEARCH_STATE.md` (blind seats keep the anchor as their only entry).

### T-F17 — minimal-vs-full scope estimate (measured on the tree at `13094d3`)

| scope | files changed (estimate) | verification work | risk introduced |
|---|---|---|---|
| **Minimal — I1–I7 only** (this window) | src: 1 new module (`execution_identity`), 2 new `mc/` modules (`owner_control`, `registry_integrity`), edits in `supplement_runner`, `supplement_precheck`, `supplement_registry`, `registry_boundary`, `day_strata_dryrun`, `day_strata_context`; scripts: 1 new (`build_verifier_dir.py`), 1 edit (`s0_real_run.py` pytest gate); tests: 4 new files, ~10 helper one-line edits (`environment_pinned=True`), 3 converted tests, `conftest.py` + a tier map `tiers.py` under `tests/` (P4); ops: 5 new documents, 7 banners, 3 templates, 1 spec. **≈ 40 files.** | targeted A+B runs per phase; full suite at P4 and at the end (≈ 7 min each); one fresh Sol claim-blind round on the gate change | bounded to the gate change (rollback: whole-tree HEAD binding) and the parser admission of an owner P2S (rollback: refuse `OWNER_REVOCATION`) |
| **Full cleanup** (converged design post-roadmap items) | tests: 143 files moved into three directories + ~35 retired; ops: 196 markdown files (222 total) archived with a generated index; public export ≈ 60 files re-presented; README index regenerated; L6 re-tabling touches the runtime repository | every moved test file re-verified; every retired test replayed against its original synthetic fault (T-F12); clean-room replay of the export (T-F16) | high churn on paths that `src/`, `tests/` and `qros-state.yaml` reference by name (22 ops files are path-referenced; moving one breaks production code); no research benefit before the roadmap ends |

Conclusion recorded: the minimal scope satisfies every obligation the converged design attaches to N10 (identity-bound authorization, owner control, verifier isolation, current-dependency invariant, non-blocking tier C, reviewer contract); the full cleanup buys nothing for research correctness before the roadmap ends and is deferred per DEC-0010.

### OD-CF-4 — mechanical proof before freezing the root exposure ledger

```
grep -rn "EXPOSURE_LEDGER" src scripts --include="*.py"
  src/itsf/mc/supplement_runner.py:24   (docstring: the runner never reads it)
readers of the ROOT file in tests:
  tests/test_exposure_ledger_migration.py   row identity root↔ops  -> converted at P5 (B-19)
  tests/test_governance_docs.py             structure pins on the root file -> untouched (root is frozen, pins keep holding)
  tests/test_mc_supplement_integration.py / test_mc_supplement_runner.py   assert the supplement surface writes nothing protected
qros-state.yaml inputs.exposure_record.path = ops/EXPOSURE_LEDGER.md  (the LIVE ledger, not the root)
```

No production or gate code reads the root ledger as a live authority. Compatibility kept minimally: the root file is not edited (append-only discipline and `test_governance_docs` pins stay intact); forward research-axis rows go only to `ops/EXPOSURE_LEDGER.md`; `test_exposure_ledger_migration` becomes prefix-identity at P5 when the first forward row lands.

## P2 — I1 governed-execution identity, I2 owner control (pending)

## P3 — I5 verifier tooling (pending)

## P4 — I3 registry invariant split, I4 marker selection (pending)

## P5 — N10 run family (pending)

## P6 — STOP before the first N10 AUTHORIZED row (pending)
