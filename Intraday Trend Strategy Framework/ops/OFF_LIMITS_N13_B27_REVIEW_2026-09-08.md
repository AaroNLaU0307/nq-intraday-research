# DELIVERY / OFF-LIMITS CARRIER -- review `N13-B27-GRID-SELECTOR-001`

```
RECORD_TYPE=OFF_LIMITS_CARRIER_AND_READ_ALLOWLIST
REVIEW_ID=N13-B27-GRID-SELECTOR-001
DELIVERY_STATUS=RETURNED
RETURNED_2026-09-08=HOLD -- one BLOCKING finding (N13-F1, T1 research
    correctness: the sealed mark/skip/report/continue rule for
    `infeasible_by_sample` was not implemented). Claims 1-11 and 14
    established; claim 12 refuted but NON-BLOCKING (N13-F2); claim 13b
    INCONCLUSIVE_NON_BLOCKING. Ledger row: ops/DECISIONS.md DEC-N13-B27-7.
    This package described the tree at c98a0ef and is kept as the
    historical record of the round that produced that verdict. The
    repaired tree is a NEW target and needs its own transport.
REVIEWED_SET_UNCHANGED_SINCE=c98a0ef776df76b3d0b0c76935bb8f388413c246
DELIVERY_REVISION=2 (2026-09-08) -- supersedes revision 1 of the same review_id.
    R1 was verified as a transport by a fresh seat and then stopped it: its
    Claim 13 demanded proof of real governed `infeasible_by_sample`
    reachability, which needs the outcome-derived TP/FP split that the
    allowlist deliberately withholds, so the seat returned
    ALLOWLIST_INSUFFICIENT and no substantive review happened. R2 fixes the
    BRIEF's over-strength, not the implementation. See section 4.
FOR=the fresh Sol claim-blind seat required by ops/REVIEWER_CONTRACT.md section 2,
    row "Change to a tier-B authorization gate or leakage-sensitive code"
BLINDNESS=CLAIM_BLIND
BUDGET=1 round
IMPLEMENTATION_REVIEW_TARGET=commit c98a0ef776df76b3d0b0c76935bb8f388413c246
IMPLEMENTATION_REVIEW_TREE=17a8aa37d3db133343dce38965e31d2ac2fe9aa8
CREATED=2026-09-08
```

**Read this file from disk.** Chat-carried bytes are never a source of truth in
this project. Line 7 of it must read
`REVIEWED_SET_UNCHANGED_SINCE=c98a0ef776df76b3d0b0c76935bb8f388413c246`; if the copy in front of you says
anything else it is stale -- open the file.

## 0. Why you are reading this before anything else

Two seats have been spent on this review and neither reached a verdict. Both
failures were the transport's:

1. The first had no governed transport at all -- no brief, no declared hashes,
   no allowlist -- so it went looking for the review authority itself, and the
   path to it runs through the quarantined subtree. It is not reusable.
2. The second verified this transport correctly and then stopped on
   `ALLOWLIST_INSUFFICIENT`, because one review item had been written as a
   mandatory claim whose only proof lies in material the allowlist withholds on
   purpose. **That item was too strong, and it is fixed in section 4.** No
   implementation verdict was issued and no implementation defect was
   established.

So: section 3 is the exhaustive set of paths you may read. **If a MANDATORY
claim requires a path that is not in section 3, STOP and report it as a
transport defect.** But read section 4 first -- the `infeasible_by_sample` item
is explicitly NOT such a claim, and unknown reachability there is a recorded
non-blocking outcome, never a reason to stop.

## 1. The forbidden set

The authoritative register is `ops/OUTCOME_CARRYING_ARTIFACTS.json` (in section
3, category A -- read it). Every path in it restates revealed research outcome.
Reading one makes you record `OUTCOME_EXPOSED` and ends your eligibility as a
future outcome-blind Stage I seat; those seats do not regenerate.

Do not open, grep, list or enumerate any of these:

- OFF-LIMITS -- the whole subtree `ops/outcome_quarantine/**`, and in particular `ops/outcome_quarantine/MC_TO_STRATEGY_MASTER_PLAN.md`, which is also this project's historical recovery anchor. That is exactly the trap: a seat orienting itself normally walks into it. You do not need it -- the frozen rule you are verifying is quoted verbatim in the brief.
- OFF-LIMITS (outcome-carrying) -- `EXPOSURE_LEDGER.md` at the repository root, and `ops/EXPOSURE_LEDGER.md`.
- OFF-LIMITS -- `S0_REPORT.json`, `S0_REPORT.md`, and any `S0_T001_RESULT_*` record.
- OFF-LIMITS -- any `.dbn.zst` and any Development bar data under `C:\Users\Aaron\quant-data\`.
- OFF-LIMITS -- the registry repository `C:\Users\Aaron\quant-data\itsf-registry\` and the registry witness root. This review needs neither: the runner never resolves the registry outside `registry_boundary`, which IS in section 3.
- OFF-LIMITS -- the per-day TP/FP classification of the governed population, and any artifact carrying per-day outcome labels. **This is not withheld to inconvenience you; it is derived from per-day P&L.** Section 4 is written so that you never need it.
- OFF-LIMITS, and read this one carefully because it is a trap inside an allowlisted file: the SEALED preregistration is on your allowlist, and its exposure-accounting bullet (`researcher_exposure`, around line 157) names `EXPOSURE_LEDGER.md` as the place researcher exposure is recorded. **That ledger is quarantined and you must not open it.** The preregistration is sealed and cannot be edited to carry this warning itself, so the warning lives here. Reading the sentence is fine; following it is not.

`BLIND_SEAT_MAY_NOT_SEARCH_THE_REPOSITORY` -- no repository-wide grep, no
recursive directory listing, no broad symbol search, and no "let me get oriented
by reading neighbouring files". Section 3 is exhaustive by construction.

The permitted outcome-clean entry point, if you want project orientation at all,
is `ops/RECOVERY_ANCHOR.md`. This review does not require it, and it is
deliberately NOT in section 3 -- ask for it rather than assuming.

## 2. How to run the tests, and what running them touches

The second seat reported that `pytest` was unavailable and the authorized suite
never started. The cause is mundane and needs no new environment: **bare
`pytest` is not on PATH in this environment; the module form is.** No virtualenv
exists and none is expected -- `.python-version` is `3.13` and the pinned
packages are in `ops/requirements.lock.txt`.

Run from the repository root. Both commands below were executed by the builder
at the frozen target immediately before dispatch:

```
python -m pytest -q tests/test_mc_grid_channel_b27.py
    -> 19 passed in 5.20s

python -m pytest -q tests/test_mc_grid_channel_b27.py tests/test_mc_runner_n13.py ^
    tests/test_mc_grid_replay_n11.py tests/test_mc_b26_reduction_feasibility.py ^
    tests/test_mc_cold_replay.py tests/test_mc_consumer.py ^
    tests/test_registry_path_single_construction.py
    -> 207 passed in 11.28s
```

If `python` resolves to something else in your session, the interpreter used was
`C:\Users\Aaron\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\python.exe`
(3.13.14, pytest 9.1.1). `scripts/run_governed.cmd` is the sanctioned entry for
a governed RUN, not for tests -- do not use it here.

**What that command touches, measured rather than asserted.** The builder ran the
seven-file command under a `sys.addaudithook` recording every `open`:
**0 files opened under `ops/`, 0 under `ops/outcome_quarantine/`.** The hook sees
`open` and does not see `os.stat`/`exists()` or reads by C extensions; that limit
is stated rather than hidden, and it is the same limit the repository's own
derived read-set test discloses.

**Do NOT run the full suite.** Several tier-C governance tests walk `ops/`
recursively and read quarantined bytes inside the test process. Under
`ops/REVIEWER_CONTRACT.md` section 4.2 that would be execution rather than
inspection, but there is no reason to incur it: **no claim in the brief needs
anything beyond the seven files above.** If you run it anyway, declare it in your
attestation under `MODULES_EXECUTED_NOT_INSPECTED`.

## 3. The read allowlist -- exhaustive: 28 repository files + 1 external file

Recompute every hash before any substantive work. **A mismatch is STOP.** These
are the bytes at the frozen implementation target, and
`ops/ARTIFACTS_UNDER_REVIEW.json` pins them: no commit after `c98a0ef776df` may
touch any of them, which you can verify yourself with
`git log c98a0ef776df..HEAD -- <path>` (expected: empty output).

### A -- review authority (what governs this review; also restated below and in the brief so you need not hunt)

| sha256 | bytes | path at `c98a0ef776df` |
|---|---|---|
| `14e2d84defc6a77e408bba37806246d220e1bd2ee5af836a730843443d87d72a` | 5985 | `ops/REVIEWER_CONTRACT.md` |
| `fb1bd88098543cb82a1cf63cdf2912deb62177f2a5988aa1a9f68d28c26b06b6` | 1246 | `ops/templates/ATTESTATION_HEADER_TEMPLATE.md` |
| `bae72767ec6d6e89a546495a5114c12713ae20f9b9801c15d2d8c711cd90d651` | 2805 | `ops/templates/VERIFICATION_BRIEF_TEMPLATE.md` |
| `a61c125b4e2e551955ce59816c9ccbc6a449a91d7f7701095eeb586e5c155f4b` | 2563 | `ops/OUTCOME_CARRYING_ARTIFACTS.json` |

4 file(s).

### B -- the N13 contract, the SEALED preregistration, and the backlog rows that define what was owed

| sha256 | bytes | path at `c98a0ef776df` |
|---|---|---|
| `a5775555e2e2f01ca496e8e26bd05ce498b6a4fb467146a2df1b1371f73b4611` | 11418 | `ops/RESEARCH_STATE.md` |
| `db2a29dd3677fa8ed37a6e83d9dcabafc5ee38420bd139ea1a595c82955bd678` | 18702 | `ops/BACKLOG.md` |
| `6cca20b7b1ce496d582ef5b4677333ba1b74bc577020ab29df00ff0c0d1af132` | 22498 | `STUDY_0_PREREGISTRATION.md` |

3 file(s).

### C -- the implementation under review

| sha256 | bytes | path at `c98a0ef776df` |
|---|---|---|
| `ea0880caf1fd836f1aac35ff68c5b9110f897a01c53cabe29c3ad876496d5ff7` | 22883 | `src/itsf/mc/grid_channel.py` |
| `4375af108e1d03cce266fb59f44b6fbc5e7fbb18e2fd8a40d746919e38f2ee8a` | 179753 | `src/itsf/mc/consumer.py` |
| `336f9780590e3d9a191dcb839f5fbdc99fff907e7d3f22ae23d437a799411ec4` | 17748 | `src/itsf/mc/mc_runner.py` |
| `712fb186957d31ad7945785e844cff7d85bff613509830806140db048902dcd4` | 47474 | `src/itsf/mc/grid_replay.py` |

4 file(s).

### D -- direct dependencies and interfaces the claims are stated over

| sha256 | bytes | path at `c98a0ef776df` |
|---|---|---|
| `86ff419f98558592e0a3c4d9cac0dcb7ddbff2d3f8598f88827e23440b91f964` | 73278 | `src/itsf/mc/atoms.py` |
| `3431a3b4d96710079b8c6df233d12a8d1771f11178627d4551a6e7f8e38237da` | 13363 | `src/itsf/mc/feasibility.py` |
| `c5ecded879c62c6509645bd63751be9e73a9d82c956b6132391b759ddea6049e` | 69193 | `src/itsf/s0/gridmix.py` |
| `405d3e2001dc691bd1591cdb22a0a67075d31e1c584faf2a432f2049eb471416` | 40283 | `src/itsf/s0/study.py` |
| `97d50740d938cb40eccab6595e6ba7284c493e9a662e311ddce31700f294a002` | 64677 | `src/itsf/contracts.py` |
| `3554cd326c06c04c3298ba44164338dcdd9e63df9a253f63ca3b0d82aa30f410` | 22095 | `src/itsf/mc/day_strata_supplement.py` |
| `549964e3ad657cf91ac3ec44dc4272c453760e1dd9d1b9f6a7d38866ab5391a4` | 47337 | `src/itsf/mc/registry_boundary.py` |
| `817419cd5910fd352bf291c8c74d6e4723cc6afefcd1a1f5fe3cb1326bd88e34` | 10894 | `src/itsf/mc/mc_contract.py` |
| `774cd76f927effa4560e699f4243269d833b34f09dbd8fff800044fe39d9b652` | 37130 | `src/itsf/mc/supplement_authority.py` |
| `e93a75e44c72d77d19abf72c7cd0d923d4b719ddd1e19e34f6924c19fbc0e24f` | 34389 | `src/itsf/mc/supplement_contract.py` |

10 file(s).

### E -- tests that carry the evidence (see section 2 for the exact command that runs them)

| sha256 | bytes | path at `c98a0ef776df` |
|---|---|---|
| `5b2e5b972dbeebc77024a7a2e14061153d9fbc57330e7c67bb3faf87b7f4ceec` | 29341 | `tests/test_mc_grid_channel_b27.py` |
| `8c3b22702d3ef12b809ec98c458086f43711cf7c6a1a9df6fa4bd7d97526efa6` | 12409 | `tests/test_mc_runner_n13.py` |
| `5e55324444e83d6c44f4e6b58e1d49da743c1687c8761e0a6ad94203c06bb050` | 42439 | `tests/test_mc_grid_replay_n11.py` |
| `a5840d3d6878c5753e3ee3eed13cfcb75eece2c33923110b70c23e57fe479458` | 20962 | `tests/test_mc_b26_reduction_feasibility.py` |
| `8538d499ced68c5e78944af09c09c9677c7eeaec892259981687f5bfbb754608` | 55588 | `tests/test_mc_cold_replay.py` |
| `2bae7b182d712faebc98de7c438e78845cb81441b5e6e1d97c018c0ece04daf5` | 34168 | `tests/test_mc_consumer.py` |
| `e4d6a79220380a6b1251f36b1db8ae6f3ab998d4ef8faf34d7f386a457062756` | 14037 | `tests/test_registry_path_single_construction.py` |

7 file(s).


### F -- the one external file, for the `infeasible_by_sample` item only

- `C:\Users\Aaron\quant-data\itsf-runs\supplements\MC-DS-S004_20260906T135831Z\DAY_STRATA_SUPPLEMENT.json`
  -- sha256 `f59a009213f2e3b9ce3b4b4937c1945227c89e724fc6c4fa0c063d0326417e4d`, 233387 bytes.
  The SEALED day-strata supplement `MC-DS-S004`. Its rows carry exactly four
  fields -- `trade_date`, `year`, `vol_stratum`, `event_stratum` -- for 2842
  days. It contains **no PnL, no return, no direction, no per-day label and no
  performance value of any kind**; measured by scanning it against the six
  outcome patterns in `tests/test_review_artifacts_are_outcome_clean.py` (zero
  matches). It gives the stratum partition of the governed day population. It
  does NOT give the TP/FP split, and that is deliberate -- see section 4.

**One row above is allowlisted but NOT in the freeze register, deliberately.**
`STUDY_0_PREREGISTRATION.md` is SEALED (`seal_revision c685ebc1...`), unchanged
since the July freeze commit `89e2505`, and `qros check` verifies its bytes
against HEAD on every run -- so it is frozen more strongly than a register entry
could manage. It is kept out of `ops/ARTIFACTS_UNDER_REVIEW.json` because
registering it pulls it into a governance guard that fires on its own line 157
(see section 1's last bullet), and the only ways to clear that guard would be
editing a sealed artifact or widening the guard. Neither is permitted. Recorded
as a transport-tool conflict in `ops/DECISIONS.md`, not silently resolved.

Nothing else. Not `ops/DECISIONS.md` -- that is the dispatch ledger, and it
records this delivery's own sha256, so hashing it into a table this document
carries would be circular; ask for it if you want the dispatch row's provenance.
Not `ops/README.md`. Not the registry. No run directory beyond the one file above.

## 4. The `infeasible_by_sample` item -- CONDITIONAL, and not a reason to stop

**This section supersedes revision 1's version of it.** R1 asked you to
establish real governed reachability. That cannot be done inside a claim-blind
allowlist, because reachability turns on the TP/FP split of the governed
population, which is derived from per-day P&L. Asking for it made an item that
had always been non-blocking into a mandatory claim, and the review stopped.

### 4.1 Lawful handling already exists, and it is sealed

This is the fact R1 failed to surface. The sealed preregistration
`STUDY_0_PREREGISTRATION.md` (category B; the frozen grid and rounding section)
already rules what happens to such a cell:

> 某分层的可用日不足时，缺额按其余层的可用日数比例重新分配；全部层合计仍不足时，
> 该网格点标记 `infeasible_by_sample` 跳过并完整报告。

That is: when a stratum falls short the shortfall is redistributed over the
remaining strata in proportion to their available days; **when all strata
together still fall short, that grid point is MARKED `infeasible_by_sample`,
SKIPPED, and REPORTED IN FULL.** So "no lawful handling exists" is already false
by authority, and the open question is a narrower and entirely non-outcome one:

- `s0.gridmix._grid_point` implements the sealed text at the S0 layer: it sets
  `point["infeasible_by_sample"] = True`, adds `infeasible_reason`, and returns
  the point -- mark, skip, report.
- `mc.grid_channel.derive_cell_draws` at the MC layer **raises**
  `MCInputError("grid_cell_infeasible_by_sample", ...)`.

**Whether raising at the MC layer preserves the sealed "mark / skip / report in
full" -- or aborts a pass that the sealed rule says should continue with that
cell marked -- is a question you can settle entirely from category B, C and D
material.** The builder has NOT settled it and does not assert an answer either
way; it is surfaced here because R1's framing hid it behind a question that
could not be answered at all. Treat it as part of the mandatory review (it is
claim 13a in the brief), and name a threat if you find one.

### 4.2 Reachability: three classifications, all of which continue the review

Apply exactly this logic and record which branch you took:

- **A.** Allowlisted non-outcome evidence mechanically proves the frozen
  governed 63-cell geometry **cannot** reach `infeasible_by_sample` ->
  `NON_BLOCKING -- governed geometry mechanically feasible`.
- **B.** Allowlisted evidence mechanically proves it **IS** reachable on the
  governed path -> then ask whether current authority already defines lawful
  handling. Per 4.1 it does. **Only if reachable AND no lawful handling existed**
  could this become a real current-path blocker.
- **C.** Reachability depends on outcome-derived information you are not
  authorized to access -> `INCONCLUSIVE_NON_BLOCKING -- reachability cannot be
  established within the blind allowlist`, **and you CONTINUE with the rest of
  the review.**

Branch C **must not**: trigger `ALLOWLIST_INSUFFICIENT`; stop or defer any other
claim; require disclosure of per-day outcomes; require the governed TP/FP split
merely for reassurance; or by itself invalidate the B-27 implementation.

The governing principle, stated so it is not re-derived:
**UNKNOWN REACHABILITY != KNOWN CURRENT-PATH DEFECT.**

Do not fabricate a region statistic and do not propose changing the
implementation's existing fail-closed handling in order to make this item
decidable. If the non-outcome supplement is insufficient for a reachability
verdict, branch C is the correct and expected answer.

### 4.3 The authority for treating it this way

Not the builder's preference. `ops/RESEARCH_STATE.md` section 9: "A reviewer who
cannot name a threat returns PASS_WITH_BACKLOG, not HOLD." Section 10: a review
that cannot name a threat -> "backlog, record, continue". Section 6, quoting
QROS-CF v2 section 8 verbatim: proceed "even if non-blocking governance backlog
remains". `ops/REVIEWER_CONTRACT.md` section 1: "NON-BLOCKING findings are listed
and become rows in `ops/BACKLOG.md`; they never hold." And nothing in
`RESEARCH_STATE.md` sections 5, 8 or 9, in `ops/REVIEWER_CONTRACT.md`, or in
`ops/BACKLOG.md` makes `infeasible_by_sample` reachability an N13 closure
condition -- the token appears in none of them.

## 5. What this review is not

You are not asked to judge the research question, any statistical result, the
wisdom of the frozen Owner ruling, or whether the strategy has an edge. No real
Monte Carlo has been executed and none is authorized: `execute_full_mc` is
gate-first behind `authorize_real_mc`, which still refuses unconditionally.
Every fixture in the category-E tests is synthetic and says so. **If you find a
statistical research result anywhere in this package, that is an incident --
report it.**

## 6. Cross-references

- Verdict shape, threats, budget: `ops/REVIEWER_CONTRACT.md` sections 1, 2, 5.
- Attestation header to copy verbatim: `ops/templates/ATTESTATION_HEADER_TEMPLATE.md`.
- The frozen set and its pin: `ops/ARTIFACTS_UNDER_REVIEW.json`, review id
  `N13-B27-GRID-SELECTOR-001`.
- The dispatch record: `ops/DECISIONS.md`, kind `REVIEW_DISPATCH`.
