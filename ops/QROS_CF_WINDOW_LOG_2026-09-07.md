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

## P2 — I1 governed-execution identity, I2 owner control

### Condition B — inspection result (mechanical, before I2)

| owner-control state | representable before I2? | what I2 added (minimum) |
|---|---|---|
| OWNER_HOLD / OWNER_RELEASE | as rows, yes: `parse_registry_rows` parses every six-cell row and both family grammars skip tokens they do not own; **nothing read them** | `src/itsf/mc/owner_control.py` reads and validates them fail-closed (actor exactly `Aaron`, NUMBERED, `[GLOBAL]` or `[<id>]`, `reason`, release names its hold); the `live_authorization_unique` gate refuses under an active hold; `append_run_started` re-checks on its fresh read; all three registry parsers tolerate the rows (tested) |
| REVOKED (supplement family) | no: `P2 -> P2S` was admitted only for `PRESTART_COMMIT_CHANGE` with a 40-hex successor | an owner-actor P2S with `reason_code: OWNER_REVOCATION` and `successor_authorized_commit: NONE` is admitted (`_is_owner_revocation`); chain state after it is AWAITING_REAUTHORIZATION; a later P2 by Aaron may name any commit; a main-agent row carrying it is refused (`p2s_without_preceding_f1`); after P3 it is still `p2s_after_p3` |
| REVOKED (new run families) | grammar not implemented (B-16) | nothing; defined in converged §2.4 for when a family needs it |

No parallel ledger, no document-based hold: every owner-control state is a registry row Aaron writes himself.

### Condition A — coverage table (dependency class → constraining mechanism → test)

| class | dependency | mechanism | proved by |
|---|---|---|---|
| repository files | `src/`, `scripts/`, `gate1/`, lockfile, `.python-version`, `tests/conftest.py`, `tests/tiers.py`, every tier A/B test file | GOVERNED_IDENTITY (blob OIDs at the authorized commit vs HEAD) | toy-repository perturbation per path class; a deleted tier-A test; a tier map edit; a tier-C edit is invisible |
| repository files read by gates outside the identity | two existence flags; `ops/S0_T001_POST_RUN_ATTESTATION.md`; the seven `guards.FROZEN_HASHES` files | EXISTENCE_FLAG_GATE · CODE_PINNED_HASH · FROZEN_HASH | dependency register; existing gate tests |
| environment variables | the ten interpreter/git override variables | ENVIRONMENT_GATE (pin measured, gate refuses) | each variable, injected |
| installed packages / version drift | 49 pins in `ops/requirements.lock.txt` | LOCKFILE_GATE | drift, missing package, empty lockfile |
| interpreter | `.python-version` | PYTHON_VERSION_GATE | mismatch injected |
| calendars | `gate1/f10_event_calendar/f10_events.csv`, `gate1/symbology/nq_v0_mapping.csv` (identity); `pandas_market_calendars` (lockfile) | GOVERNED_IDENTITY · LOCKFILE_GATE | derived read-set sees both CSV reads |
| data / cache identity | authorized `manifest.json` (pinned sha), every `.dbn.zst` (per-file sha), **`condition.json` — listed in the manifest, never verified until I1** | DATA_MANIFEST | replaced manifest refused; tampered file refused; `condition.json` tampered after the pin → `ManifestError` before it is read; the real `condition.json` hashes to its manifest entry today (`04195104…`), so S001–S004 read the manifest's bytes |
| sealed S0-T001 bundle | 14 files | CUSTODY_BATTERY | existing battery |
| external executable / runtime | git (`rev-parse`, `status`, `ls-tree`, `show`) | NOT_SEMANTIC, recorded | register |
| check-then-replace race | HEAD, governed worktree, environment between precheck and first write | first-write seam re-check | seam refuses `seam_head_moved`, `seam_governed_tree_dirty` (ops and tier-C edits ignored, tier-A edits refused), `seam_environment_unpinned`; the runner appends no P3 after a seam refusal |
| derived read-set | every repository path the production entry points open on synthetic input (`assemble_precheck_context`, both calendar builders, the full rehearsal) | must be covered by a governed prefix or an exact register entry | `test_every_repository_path_production_opens_is_covered_by_a_mechanism` (audit hook; fails closed on an unregistered read) |

### Results

```
tests/test_execution_identity.py   T-F01   47 tests  PASS
tests/test_owner_control.py        T-F06   26 tests  PASS
affected existing files (35) + meta-guards   PASS after two helper contexts gained `environment_pinned=True`
real repository: identity(HEAD) == identity(7a5570f) across the three documentation commits of P0/P1 (document-blind, measured);
                 identity(HEAD) != identity(ac16c39) by exactly tests/test_mc_supplement_integration.py (the registration table);
                 468 governed blobs; 0.07 s per comparison; environment pinned (python 3.13, 49/49 packages, no override variable)
gate names        unchanged (thirteen; `authorized_commit_matches_head` keeps its ratified name, its comparison is now the governed-execution identity)
```

Files changed at P2: `src/itsf/execution_identity.py` (new), `src/itsf/mc/owner_control.py` (new), `src/itsf/mc/supplement_runner.py` (GateContext fields, two gates, seam wrapper), `src/itsf/mc/supplement_precheck.py`, `src/itsf/mc/day_strata_context.py`, `src/itsf/mc/day_strata_dryrun.py` (measured pin), `src/itsf/mc/supplement_registry.py` (owner revocation admission), `src/itsf/mc/registry_boundary.py` (hold re-check at the P3 append), `src/itsf/mc/production_inputs.py` (`condition.json` verified), `tests/tiers.py` (new, empty governance list until P4), two test helpers, two new test files.

Rollback for this phase (converged §9): revert `_g_authorized_commit_matches_head` to commit equality; refuse `OWNER_REVOCATION`; both are single-function reverts.

The fresh Sol/Astra claim-blind review of this tier-B gate change (DEC-0010 P2, one round) is prepared as an external brief after the P2 commit; see DECISIONS.md for the dispatch row.

## P3 — I5 verifier tooling

Created: `scripts/build_verifier_dir.py` (two-phase builder: pre-freeze allowlist copy + code exported with `git show` at the authorized commit + `ALLOWLIST.sha256` + `README_VERIFIER.md`; post-freeze comparands refused until `FREEZE_MARKER.json` names a frozen result whose sha256 matches; refuses sources under the framework's `ops/`/`tests/`, the registry repository, the witness directory, memory files or another review directory; refuses a path listed in both phases), `ops/templates/VERIFICATION_BRIEF_TEMPLATE.md`, `ops/templates/ATTESTATION_HEADER_TEMPLATE.md`, `ops/templates/DISPATCH_TEMPLATE.md` (carries the dispatch's own hash — the gap Astra reported), `ops/verifier_specs/MC-DS-S004_pre_freeze_rehearsal.json`.

### T-F03 — sentinel test (`tests/test_verifier_dir_builder.py`, 12 tests, PASS)

A synthetic sealed output carrying `SENTINEL_OUTCOME_9f3a_DO_NOT_LEAK` is the post-freeze comparand. Measured: absent from the whole directory after pre-freeze; still absent after a post-freeze attempt without a marker (refused) and after one with a wrong hash (refused); present ONLY under `post_freeze/` after a matching marker; a second post-freeze delivery is refused; the exported code is the committed bytes, not the edited worktree; seven leak-shaped specs are refused before anything is written; the CLI exits 2 on refusal and writes nothing.

### S004 rehearsal — directory rebuilt from the spec, hashes compared to the original custody record

```
target      C:\Users\Aaron\quant-data\review\mc-ds-s004-verifier-dir-rehearsal-2026-09-07\
allowlist   24 files (run + archive supplement, 14 sealed S0-T001 files, the frozen F10 table, 6 code modules at ac16c399, the brief)
compared    17 hashes against itsf-mc-ds-s004-strict-blind-verifier-2026-09-06/phase2_custody.json
            run f59a0092…, archive f59a0092…, all 14 S0-T001 files, F10 csv 5e92ad00… (= the S0-time preflight hash)
mismatches  0
post_freeze absent (as designed until a marker exists)
```

Exit criterion of P3 (converged §6: "rebuilding the S004 directory reproduces its custody hashes") met.

## P4 — I3 registry invariant split, I4 marker selection (pending)

## P5 — N10 run family (pending)

## P6 — STOP before the first N10 AUTHORIZED row (pending)
