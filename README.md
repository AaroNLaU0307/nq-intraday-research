# nq-intraday-research — NQ intraday research programme (publication mirror)

Published at <https://github.com/AaroNLaU0307/nq-intraday-research> (renamed 2026-10-02 from
`Intraday-Trend-Strategy-Framework`; GitHub redirects the old name).

This repository publishes one research programme on intraday behaviour in Nasdaq-100 futures
(NQ / MNQ), run under a preregister-then-test workflow ([`QUANT_WORKFLOW_VNEXT.md`](QUANT_WORKFLOW_VNEXT.md),
see [`WORKFLOW_COPY_NOTE.md`](WORKFLOW_COPY_NOTE.md)). It holds three projects, each with its own
full git history:

| subfolder | what it is | status (from its own `PROJECT_STATE.md`) | reproduce |
|---|---|---|---|
| [`Intraday Trend Strategy Framework/`](Intraday%20Trend%20Strategy%20Framework/PROJECT_STATE.md) (ITSF) | the framework and its Study 0: NQ opening-drive (09:30-10:00) continuation, an Oracle's cost-after performance, and a prop-account Monte-Carlo adjudication | **STOPPED / PARKED** (2026-09-16); final evidence verdict INSUFFICIENT_EVIDENCE (KB term `unresolved`); no governed MC result was produced | `python -m pytest tests` |
| [`nq-event-diffusion-research/`](nq-event-diffusion-research/PROJECT_STATE.md) (R1) | scheduled-release (CPI / NFP) information-diffusion continuation in NQ; one sealed, preregistered, once-only test | **CLOSED** at S4, lifecycle STOP (tag `r1-final`); R1_FINAL_VERDICT INSUFFICIENT_EVIDENCE (KB `unresolved`) | see below |
| [`nq-letf-rebalancing-research/`](nq-letf-rebalancing-research/PROJECT_STATE.md) (R2) | leveraged-ETF daily-reset rebalancing pressure transmitted into NQ | **PRE-S1 / WAITING_FOR_EXTERNAL_EVIDENCE**: no hypothesis, no preregistration, no outcome; waiting on vendor point-in-time evidence | `python tools/reproduce.py` |

Nothing here states a result beyond what each project's own records state. No NQ market data,
no raw vendor data and no NQ returns are in this repository.

## Mirror rule

- **Records are written only in the three local project repositories.** This repository is a
  publication mirror built with `git subtree add` (no squash): every original commit is
  preserved and resolvable here. Nothing in a subfolder is ever edited in the mirror.
- Re-sync with `powershell -ExecutionPolicy Bypass -File tools\sync_mirror.ps1`, which runs
  `git subtree pull` for each project and re-imports the projects' tags. It never adds a remote
  and never pushes; publishing is the Owner's own act.
- The root files (`README.md`, `QUANT_WORKFLOW_VNEXT.md`, `WORKFLOW_COPY_NOTE.md`,
  `tools/sync_mirror.ps1`, `.gitattributes`) belong to the mirror. `.gitattributes` is `* -text`,
  like each project's: checked-out bytes equal committed bytes, so every recorded sha256
  verifies from a clone.
- The ITSF subfolder keeps its workspace name, **`Intraday Trend Strategy Framework`** (with
  spaces), while the repository is named `nq-intraday-research`. Reason: R1's code resolves its sibling as
  `../Intraday Trend Strategy Framework` (`r1/events.py:39`, `r1/itsf_pin.py:26`,
  `psmv/psmv_structural.py:57`). With a hyphenated folder R1's suite silently skips 13 ITSF-pin
  and calendar tests (272 passed, 13 skipped); with the workspace name it runs in full (285).
  No record had to be edited.
- Local placement: the mirror lives at `Quant trade/_publish/Intraday-Trend-Strategy-Framework/`
  (the local folder keeps the original name; `tools/sync_mirror.ps1` resolves paths from it)
  in the author's workspace — an explicit path binding for the GitHub mirror, kept out of the
  project folders (`_Archive` is the precedent for an underscore root directory).

## Source heads (as imported, 2026-10-02)

| subfolder | source branch | source HEAD | annotated tags imported unchanged |
|---|---|---|---|
| `Intraday Trend Strategy Framework/` | `master` | `11725fb9c2a7b3212a5f3cc9eb36820fa7d22003` | `mc-freeze-v1`, `s0-freeze-v1` |
| `nq-event-diffusion-research/` | `main` | `6bacfaecb62be70485e1a78bfca8c659e985367c` | `r1-pre-seal`, `r1-s1-sealed`, `r1-s2-built`, `r1-final` |
| `nq-letf-rebalancing-research/` | `main` | `5c84a498e9eb8532bbdf11c63fbdbd157b248781` | none |

Each HEAD resolves inside this repository (`git cat-file -t <hash>` → `commit`), and each tag
object is identical to the source's.

## Reproduce, from inside the mirror

**R2** — `cd nq-letf-rebalancing-research && python tools/reproduce.py` (offline; needs `pytest`,
and `tzdata` on Windows). Result in the mirror at import: tests 44 passed + 12 subtests;
16/16 snapshots verified; 15 log rows; NATURAL 10 (2 catch-ups), MANUAL 6; 34 links;
**REPRODUCE PASS**.

**R1** — from `nq-event-diffusion-research/`:

```bash
python -m pytest tests                  # 285 passed
python tools/validate_state.py          # 60 passed, 0 failed
python psmv/validate_prereg.py          # 183 passed, 2 failed (the two standing seal-time
                                        # state assertions; checked at the seal commits instead)
GIT_DIR="$(git rev-parse --git-common-dir)" GIT_WORK_TREE="$PWD" \
  python tools/validate_seal_snapshot.py   # PASS (161 at CONTENT_COMMIT, 185 at the attestation)
```

`validate_seal_snapshot.py` runs `git archive <commit>` from the R1 folder. In this mirror that
folder is not the repository root, so plain `python tools/validate_seal_snapshot.py` archives an
empty sub-path and stops with a tar `ReadError`. Pointing git's work tree at the R1 folder, as
above, runs the unmodified tool against this repository's own objects and tags.

**ITSF** — from `Intraday Trend Strategy Framework/`: `python -m pytest tests`. Result in the
mirror at import: **5 failed, 5840 passed, 1 xfailed, 564 subtests passed** (13 min 44 s). Failing:
`test_execution_identity.py::test_the_real_repository_identity_covers_src_and_excludes_ops_documents`,
`test_issued_deliveries_are_registered.py::TestAnIssuedDeliveryIsArmed::test_the_new_file_exemption_is_exactly_one_commit_wide`,
`test_qros_cf_astra_repairs.py::test_F01_the_governed_identity_does_not_and_cannot_cover_a_pyc`,
`test_qros_cf_astra_round2.py::test_F01_setting_only_the_writable_mirror_does_not_attest`,
`test_the_precommit_hook_is_installed.py::TestTheHookIsPresentAndConnected::test_hooks_path_points_at_it`
(asserts the local `core.hooksPath = tools/githooks`, which no clone carries). Reading, **unverified**:
all five inspect the git repository itself (repository identity, commit history, local hook
config), and in this mirror ITSF is a subfolder rather than the repository root; they are
environmental to the mirror, not a change to ITSF's code or records. ITSF is stopped and its
tests are reported as found, not fixed. A trial run elsewhere also failed
`test_day_strata_dryrun.py::...::test_it_leaks_no_scratch_path_into_what_it_prints` when the copy
sat under a temporary directory; it passed here.

## Rigour audit CP-AUDIT-01 (2026-10-01)

A read-only multi-agent rigour audit of **R1 (at `18639ee`) and R2 (at `7fc4e83`)** was run on
2026-10-01 by a separate Claude Code session and accepted by the delegate seat. ITSF was not
audited. Reports and the resulting corrections:

- reports, byte-identical, with hashes:
  `nq-letf-rebalancing-research/audits/2026-10-01_CP-AUDIT-01/` (both reports, run-ID index,
  workflow scripts) and `nq-event-diffusion-research/audits/2026-10-01_CP-AUDIT-01_R1.md`;
- R1 corrections: `nq-event-diffusion-research/R1_RECORD_CORRECTIONS_2026-10-02.md` (new dated
  file; sealed records untouched; verdict unchanged), plus a fix to the unsealed
  `tools/validate_state.py`;
- R2 corrections: dated correction sections appended to the affected records, tools fixes, and
  rows `COR-R2-*` / `FIX-R2-*` in `nq-letf-rebalancing-research/DECISION_LOG.md`.

Any later audit of these projects is run against this mirror.

## What becomes public with this repository

- **Third-party snapshots** (ITSF, captured 2026-07-28 for fee and prop-rule evidence):
  `Intraday Trend Strategy Framework/gate1/snapshots/2026-07-28/` — the CME fee schedule
  (`cme_fee_schedule_2026-07-27.pdf`, `.xls`), the Topstep XFA scaling table
  (`topstep_xfa_scaling_table.png`), 33 saved web pages from CME, NFA, Topstep, TopstepX and
  Lucid, 5 snapshot manifests, and 33 text extractions under `extracted/`; also
  `gate1/lucid_pricing_2026-07-28/`, `gate1/lucid_inquiry_reply/`, and the public BLS / Federal
  Reserve calendar pages under `gate1/f10_event_calendar/raw/`.
- Derived reference data, no raw market data: the F10 event calendar, the NQ `.v.0` symbology
  map and ITSF's per-minute spread-cost table.
- The author's machine name and Windows username appear in file paths and logs; commit
  metadata carries the author name and a GitHub noreply address. Vendor public contact lines
  and addresses appear in R2's vendor records. The university name and a vendor support-case
  number are withheld from every published file and commit.
