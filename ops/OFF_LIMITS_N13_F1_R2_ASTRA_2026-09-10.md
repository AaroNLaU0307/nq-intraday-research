# DELIVERY / OFF-LIMITS CARRIER -- review `N13-F1-REREVIEW-002`

```
RECORD_TYPE=OFF_LIMITS_CARRIER_AND_READ_ALLOWLIST
REVIEW_ID=N13-F1-REREVIEW-002
DELIVERY_STATUS=ISSUED
REVIEWED_SET_UNCHANGED_SINCE=c423183baebdff3c5e189ed99d053613c21d8f50
ISSUE_LINEAGE=N13-F1
REVIEW_ROUND=2 of 2 (ops/REVIEWER_CONTRACT.md S1: "HOLD -> builder fixes -> ONE
    re-review covering the fix plus a builder-declared, reviewer-contestable
    impact scope -> still HOLD -> Aaron. Two rounds per issue lineage.")
    Round 1 returned HOLD on N13-F1. This is the ONE re-review. A further HOLD
    goes to Aaron, not to a third round.
FOR=ONE NEW fresh GPT-6 Astra session, claim-blind
SEAT_AUTHORITY=ops/REVIEWER_CONTRACT.md S2.1 -- the row's seat is
    `OWNER_DEFAULT_INDEPENDENT_REVIEWER`, resolved at dispatch, and Aaron set
    that to GPT-6 Astra for NEW work on 2026-09-10. GPT-5.6 Sol keeps the
    legacy / fallback / frozen-lineage seat. Substituting the model relaxes
    nothing else: fresh top-level session, claim-blind, independent of the
    producing session, never its subagent.
BUILDER=Claude Opus / Claude Code (which made the repair and may neither
    dispatch nor perform this review)
BLINDNESS=CLAIM_BLIND
BUDGET=1 re-review
IMPLEMENTATION_REVIEW_TARGET=commit b9eb342f0e8aa43bd20a3938f097489d0f4a1a7b   <-- the CODE under review
    NOTE: `REVIEWED_SET_UNCHANGED_SINCE` above is the FREEZE PIN over the whole
    allowlist and is a DIFFERENT commit. See section 3.
IMPLEMENTATION_REVIEW_TREE=c0413d6f89865e38564bf22c2f1c945b1a0d6e93
PRIOR_REVIEWED_TARGET=c98a0ef776df76b3d0b0c76935bb8f388413c246 -- HISTORICAL EVIDENCE ONLY. It is the tree round
    1 reviewed and it must NOT be substituted as this round's target.
CREATED=2026-09-10
```

**Read this file from disk.** Chat-carried bytes are never a source of truth in
this project. Line 7 of it must read
`REVIEWED_SET_UNCHANGED_SINCE=c423183baebdff3c5e189ed99d053613c21d8f50`; if the copy in front of you says
anything else it is stale -- open the file.

## 0. Read this before anything else

Round 1 of this lineage completed as a review process and returned **HOLD** on
one BLOCKING finding. The builder then made a bounded repair. **You are reviewing
the repair.**

Section 3 is the exhaustive set of paths you may read. **If a MANDATORY claim
requires a path that is not in section 3, STOP and report it as a transport
defect.** Two carve-outs, both deliberate and both explained where they arise:

* **Claim 13b (reachability) is NOT a mandatory claim.** If blind evidence cannot
  settle it, `INCONCLUSIVE_NON_BLOCKING` is the correct and expected answer --
  never `ALLOWLIST_INSUFFICIENT`, never a STOP, never an N13 blocker. Section 5.
* **N13-F2 is NON-BLOCKING BACKLOG** and is not yours to re-open unless the
  repaired diff creates a new governed path from a forged draw to consequential
  output. Section 6.

Three seats have now been spent on this lineage and only one produced a verdict.
Please return a substantive PASS / PASS_WITH_BACKLOG / HOLD.

## 1. The forbidden set

The authoritative register is `ops/OUTCOME_CARRYING_ARTIFACTS.json` (section 3,
category A -- read it). Every path in it restates revealed research outcome.
Reading one makes you record `OUTCOME_EXPOSED` and ends your eligibility as a
future outcome-blind Stage I seat; those seats do not regenerate.

Do not open, grep, list or enumerate any of these:

- OFF-LIMITS -- the whole subtree `ops/outcome_quarantine/**`, and in particular `ops/outcome_quarantine/MC_TO_STRATEGY_MASTER_PLAN.md`, which is also this project's historical recovery anchor. That is exactly the trap: a seat orienting itself normally walks into it. The sealed rule you are verifying against is quoted verbatim in the brief and the sealed file itself is on your allowlist.
- OFF-LIMITS (outcome-carrying) -- `EXPOSURE_LEDGER.md` at the repository root, and `ops/EXPOSURE_LEDGER.md`.
- OFF-LIMITS -- `S0_REPORT.json`, `S0_REPORT.md`, and any `S0_T001_RESULT_*` record.
- OFF-LIMITS -- any `.dbn.zst` and any Development bar data under `C:\Users\Aaron\quant-data\`.
- OFF-LIMITS -- the registry repository `C:\Users\Aaron\quant-data\itsf-registry\` and the registry witness root. Neither is needed: the runner never resolves the registry outside `registry_boundary`, which IS in section 3.
- OFF-LIMITS -- the per-day TP/FP classification of the governed population, and any artifact carrying per-day outcome labels. **It is not withheld to inconvenience you; it is derived from per-day P&L.** Section 5 is written so that you never need it.
- OFF-LIMITS, and read this carefully because it is a trap inside an allowlisted file: the SEALED preregistration is on your allowlist, and its exposure-accounting bullet (`researcher_exposure`, around line 157) names `EXPOSURE_LEDGER.md` as where researcher exposure is recorded. **That ledger is quarantined and you must not open it.** The preregistration is sealed and cannot be edited to carry this warning itself, so the warning lives here. Reading the sentence is fine; following it is not.

`BLIND_SEAT_MAY_NOT_SEARCH_THE_REPOSITORY` -- no repository-wide grep, no
recursive directory listing, no broad symbol search, and no "let me get oriented
by reading neighbouring files". Section 3 is exhaustive by construction.

The permitted outcome-clean entry point, if you want project orientation at all,
is `ops/RECOVERY_ANCHOR.md`. This review does not require it and it is
deliberately NOT in section 3 -- ask rather than assume.

## 2. How to inspect the diff, and how to run the tests

**The diff under review, without any search.** Three files changed between the
round-1 tree and the repaired tree, and this command shows all of it:

```
git diff c98a0ef776df b9eb342f0e8a -- src/itsf/mc/grid_channel.py src/itsf/mc/grid_replay.py tests/test_mc_grid_channel_b27.py
```

`git log b9eb342f0e8a..HEAD -- src/ tests/` is **EMPTY**. Every commit after
the repair touches `ops/` bookkeeping only -- this delivery, the freeze register,
the ops index and the two append-only ledgers. So the transport-bookkeeping HEAD is
later than `b9eb342f0e8a` while the reviewed production tree is exactly
`c0413d6f89865e38564bf22c2f1c945b1a0d6e93`. Verify that yourself rather than taking it from here; it is the one
claim in this document that, if false, would mean you are reviewing a moving tree.

**The tests.** Bare `pytest` is not on PATH in this environment; the module form
is. No virtualenv exists and none is expected -- `.python-version` is `3.13` and
the pinned packages are in `ops/requirements.lock.txt`. Run from the repository
root:

```
# 1. the F1 rule itself, plus the B-27 Cartesian proofs, in one file
python -m pytest -q tests/test_mc_grid_channel_b27.py

# 2. just the F1 section
python -m pytest -q tests/test_mc_grid_channel_b27.py -k F1

# 3. downstream region-map / KReplayEvidence handling, and the S0-layer
#    precedent for the sealed semantics
python -m pytest -q tests/test_mc_grid_replay_n11.py tests/test_gridmix_rulings.py

# 4. N13 runner integration and the seal path
python -m pytest -q tests/test_mc_runner_n13.py tests/test_mc_cold_replay.py ^
    tests/test_mc_b26_reduction_feasibility.py tests/test_mc_consumer.py ^
    tests/test_registry_path_single_construction.py
```

If `python` resolves elsewhere in your session, the interpreter used was
`C:\Users\Aaron\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\python.exe`
(3.13.14, pytest 9.1.1). `scripts/run_governed.cmd` is the sanctioned entry for a
governed RUN, not for tests -- do not use it here.

**Builder-side transport validation, and what it is NOT.** The builder ran all
four commands at the frozen target immediately before dispatch and they started
and completed. Those counts appear in the DISPATCH. They are evidence that **the
command works in this environment** -- transport validation. They are
SELF-REPORTED with respect to the implementation and under
`ops/REVIEWER_CONTRACT.md` S1 a SELF-REPORTED restatement of the producer's
tables is never BLOCKING **and never PASSING** either. A green suite the builder
ran is not evidence the repair is correct; your own run and your own reading are.

**What running them touches, measured rather than asserted.** The builder ran the
category-E files under a `sys.addaudithook` recording every `open`: **0 files
opened under `ops/`, 0 under `ops/outcome_quarantine/`**. The hook sees `open` and
does not see `os.stat`/`exists()` or reads by C extensions; that limit is stated
rather than hidden.

**Do NOT run the full suite.** Several tier-C governance tests walk `ops/`
recursively and read quarantined bytes inside the test process. Under
`ops/REVIEWER_CONTRACT.md` section 4.2 that is execution rather than inspection,
but there is no reason to incur it: no claim in the brief needs it. If you run it
anyway, declare it under `MODULES_EXECUTED_NOT_INSPECTED`.

## 3. The read allowlist -- exhaustive: 26 repository files + 1 external file

Recompute every hash before any substantive work. **A mismatch is STOP.**

**Two different commits appear in this package and they are NOT the same quantity.**
`IMPLEMENTATION_REVIEW_TARGET` = `b9eb342f0e8a` is the code you are reviewing.
`REVIEWED_SET_UNCHANGED_SINCE` = `c423183baebd` is the FREEZE PIN over this whole
allowlist, and it is later because the Owner's reviewer-routing migration edited two
authority files that are IN the allowlist -- `ops/REVIEWER_CONTRACT.md`, which
defines your seat, and `ops/RESEARCH_STATE.md`. A pin is only meaningful at or after
every listed path's last change, so it tracks the SET; the target tracks the CODE.
Both hold at once, and both are yours to verify rather than take from here:

    git log c423183baebd..HEAD -- <any allowlisted path>   ->  expected: empty
    git log b9eb342f0e8a..HEAD -- src/ tests/           ->  expected: empty

The second is the one that answers "am I reviewing a moving tree": **no
implementation byte has changed since `b9eb342f0e8a`.**

### A -- reviewer authority (also restated below and in the brief, so nothing needs hunting)

| sha256 | bytes | path at `b9eb342f0e8a` |
|---|---|---|
| `ce076ca55a3400ffb3b8725ad891097e09915ffb911082c630d0889ce02b43c1` | 8418 | `ops/REVIEWER_CONTRACT.md` |
| `fb1bd88098543cb82a1cf63cdf2912deb62177f2a5988aa1a9f68d28c26b06b6` | 1246 | `ops/templates/ATTESTATION_HEADER_TEMPLATE.md` |
| `bae72767ec6d6e89a546495a5114c12713ae20f9b9801c15d2d8c711cd90d651` | 2805 | `ops/templates/VERIFICATION_BRIEF_TEMPLATE.md` |
| `a61c125b4e2e551955ce59816c9ccbc6a449a91d7f7701095eeb586e5c155f4b` | 2563 | `ops/OUTCOME_CARRYING_ARTIFACTS.json` |

4 file(s).

### B -- the SEALED preregistration and the N13 contract

| sha256 | bytes | path at `b9eb342f0e8a` |
|---|---|---|
| `6cca20b7b1ce496d582ef5b4677333ba1b74bc577020ab29df00ff0c0d1af132` | 22498 | `STUDY_0_PREREGISTRATION.md` |
| `4df52245c02e7eb20c0f797ad5fa051b1312cc1307b8794f60825f6df00f557b` | 11598 | `ops/RESEARCH_STATE.md` |

2 file(s).

### C -- the repaired implementation (this is the diff under review)

| sha256 | bytes | path at `b9eb342f0e8a` |
|---|---|---|
| `4027542f61e2dac8269320ab86079783e83bd8058cae75ae28338a9800636c39` | 29338 | `src/itsf/mc/grid_channel.py` |
| `c7b9dd29d886a2261b96988d5f40a0b9fba2d51556d2a1a53c3b9f7feddde485` | 52810 | `src/itsf/mc/grid_replay.py` |

2 file(s).

### D -- consumers and interfaces the declared impact scope reaches

| sha256 | bytes | path at `b9eb342f0e8a` |
|---|---|---|
| `336f9780590e3d9a191dcb839f5fbdc99fff907e7d3f22ae23d437a799411ec4` | 17748 | `src/itsf/mc/mc_runner.py` |
| `4375af108e1d03cce266fb59f44b6fbc5e7fbb18e2fd8a40d746919e38f2ee8a` | 179753 | `src/itsf/mc/consumer.py` |
| `c5ecded879c62c6509645bd63751be9e73a9d82c956b6132391b759ddea6049e` | 69193 | `src/itsf/s0/gridmix.py` |
| `86ff419f98558592e0a3c4d9cac0dcb7ddbff2d3f8598f88827e23440b91f964` | 73278 | `src/itsf/mc/atoms.py` |
| `3431a3b4d96710079b8c6df233d12a8d1771f11178627d4551a6e7f8e38237da` | 13363 | `src/itsf/mc/feasibility.py` |
| `3554cd326c06c04c3298ba44164338dcdd9e63df9a253f63ca3b0d82aa30f410` | 22095 | `src/itsf/mc/day_strata_supplement.py` |
| `97d50740d938cb40eccab6595e6ba7284c493e9a662e311ddce31700f294a002` | 64677 | `src/itsf/contracts.py` |
| `405d3e2001dc691bd1591cdb22a0a67075d31e1c584faf2a432f2049eb471416` | 40283 | `src/itsf/s0/study.py` |
| `817419cd5910fd352bf291c8c74d6e4723cc6afefcd1a1f5fe3cb1326bd88e34` | 10894 | `src/itsf/mc/mc_contract.py` |
| `549964e3ad657cf91ac3ec44dc4272c453760e1dd9d1b9f6a7d38866ab5391a4` | 47337 | `src/itsf/mc/registry_boundary.py` |

10 file(s).

### E -- tests (section 2 gives the exact commands)

| sha256 | bytes | path at `b9eb342f0e8a` |
|---|---|---|
| `f9bfb5e251806726ce8be0eebdc45126393f12e4050ba513a9d219336ef33990` | 44895 | `tests/test_mc_grid_channel_b27.py` |
| `8c3b22702d3ef12b809ec98c458086f43711cf7c6a1a9df6fa4bd7d97526efa6` | 12409 | `tests/test_mc_runner_n13.py` |
| `5e55324444e83d6c44f4e6b58e1d49da743c1687c8761e0a6ad94203c06bb050` | 42439 | `tests/test_mc_grid_replay_n11.py` |
| `a5840d3d6878c5753e3ee3eed13cfcb75eece2c33923110b70c23e57fe479458` | 20962 | `tests/test_mc_b26_reduction_feasibility.py` |
| `8538d499ced68c5e78944af09c09c9677c7eeaec892259981687f5bfbb754608` | 55588 | `tests/test_mc_cold_replay.py` |
| `2bae7b182d712faebc98de7c438e78845cb81441b5e6e1d97c018c0ece04daf5` | 34168 | `tests/test_mc_consumer.py` |
| `e4d6a79220380a6b1251f36b1db8ae6f3ab998d4ef8faf34d7f386a457062756` | 14037 | `tests/test_registry_path_single_construction.py` |
| `289e4c783ed46f3162856da4c6772bdc62f7ca61a11e7c3c53a4330ff27ba630` | 48673 | `tests/test_gridmix_rulings.py` |

8 file(s).


### F -- the one external file, for the conditional reachability item only

- `C:\Users\Aaron\quant-data\itsf-runs\supplements\MC-DS-S004_20260906T135831Z\DAY_STRATA_SUPPLEMENT.json`
  -- sha256 `f59a009213f2e3b9ce3b4b4937c1945227c89e724fc6c4fa0c063d0326417e4d`, 233387 bytes.
  The SEALED day-strata supplement `MC-DS-S004`. Its rows carry exactly four
  fields -- `trade_date`, `year`, `vol_stratum`, `event_stratum` -- for 2842 days.
  **No PnL, no return, no direction, no per-day label, no performance value**;
  measured against the six outcome patterns in
  `tests/test_review_artifacts_are_outcome_clean.py` (zero matches). It gives the
  stratum partition of the governed day population. It does NOT give the TP/FP
  split, and that is deliberate -- section 5.

**One row above is allowlisted but NOT in the freeze register, deliberately.**
`STUDY_0_PREREGISTRATION.md` is SEALED, unchanged since the July freeze commit
`89e2505`, and `qros check` verifies its bytes against HEAD every run -- so it is
frozen harder than a register entry could manage. It is kept out of
`ops/ARTIFACTS_UNDER_REVIEW.json` because registering it pulls it into a
governance guard that fires on its own line 157 (section 1's last bullet), and
the only ways to clear that guard would be editing a sealed artifact or widening
the guard. Recorded as a transport-tool conflict in `ops/DECISIONS.md`
DEC-N13-B27-6, not silently resolved.

Nothing else, and two exclusions are worth their reasons.

`ops/DECISIONS.md` and `ops/BACKLOG.md` are both **append-only governance ledgers
that legitimately move**: DECISIONS records this delivery's own sha256 (so hashing
it into a table this document carries would be circular), and BACKLOG grows a row
every time a finding lands. Pinning either to the implementation commit would
produce a declaration that is stale the moment it is written -- the exact failure
this project measured on 2026-08-25 -- so neither is in the frozen set. What you
would want from them is restated in the brief: the round-1 verdict (brief S2), the
declared impact scope (S4, recorded at `DECISIONS.md` DEC-N13-B27-9), the 13b
classification (S6, B-30) and the F2 classification (S7, B-29). **Ask for either
file if you want its provenance rather than the brief's account of it** -- that is
a transport request, not an allowlist breach. Not `ops/README.md`.
Not the registry. No run directory beyond the one file above. **Neither the round-1
transport** (`ops/OFF_LIMITS_N13_B27_REVIEW_2026-09-08.md` and its brief) **nor the
withdrawn Sol package for this round** (`ops/OFF_LIMITS_N13_F1_REREVIEW_R2_2026-09-10.md`): the first
described the superseded tree, it is preserved as history, and reading it would
tell you what the previous seat concluded -- which is exactly what claim-blindness
is protecting.

## 4. The fourth cell class needs independent scrutiny

The repair introduced `INFEASIBLE_BY_SAMPLE` as an explicit non-statistical cell
class and propagated it. **Establish for yourself** that it implements only the
sealed mark/skip/report semantics and does NOT silently change M8, rule (c), M10,
`KReplayEvidence` meaning, convergence mathematics, or region-membership
mathematics for feasible cells. The places to look, named so you need no search:
`cell_category`, `compare_region_maps`, `cell_drift_violations`,
`publish_region`, the region-map digest inside `derive_k_replay_evidence`, and
the K/2K comparison path.

One branch to adjudicate specifically. A mixed state -- one seed marking a cell
`INFEASIBLE_BY_SAMPLE` while another seed carries sampled statistics for it --
is representable. Decide which it is: **reachable under current governed
semantics**, **defensive / fail-closed only**, or **an unintended new research
rule**. The builder's position is that the sealed test consults no seed and is
therefore seed-independent, making the branch unreachable and defensive only.
**That is a claim to test, not a fact to accept.** No new majority or voting rule
may be introduced by anyone, including by you.

## 5. Claim 13b -- reachability -- remains conditional and NON-BLOCKING

The mandatory question this round is whether the implementation **handles the
state correctly IF reached**. Whether it IS reached on the real governed path
turns on the TP/FP split of the governed population, which is derived from
per-day P&L and is withheld from a claim-blind seat by design.

If allowlisted non-outcome evidence settles reachability, say so. If it does not:
`INCONCLUSIVE_NON_BLOCKING`, and **continue**. That outcome must not become
`ALLOWLIST_INSUFFICIENT`, a STOP, a disclosure requirement, or an N13 blocker.
`UNKNOWN REACHABILITY != KNOWN CURRENT-PATH DEFECT`. Recorded as B-30 in
`ops/BACKLOG.md`.

Authority, so this is not read as the builder's preference:
`ops/RESEARCH_STATE.md` S9 -- "A reviewer who cannot name a threat returns
PASS_WITH_BACKLOG, not HOLD"; S10 -- "backlog, record, continue"; S6 quoting
QROS-CF v2 S8 verbatim -- proceed "even if non-blocking governance backlog
remains"; `ops/REVIEWER_CONTRACT.md` S1 -- "NON-BLOCKING findings ... never hold".

## 6. N13-F2 -- NON-BLOCKING BACKLOG, not this round's business

Round 1 established that a self-consistent `GridDraw` can be forged outside the
governed runner path (`object.__new__` plus a recomputed self-digest), and
classified it NON-BLOCKING because the governed runner accepts no caller-supplied
draw on the seal path. It was deliberately NOT repaired: hardening `verify_draw`
under an F1-scoped authorization would have widened a leakage-sensitive
provenance surface for a route nothing currently takes. Recorded as B-29.

Do not make it a round-2 blocker **unless the repaired diff creates a new actual
governed path from a forged draw to consequential output** -- if it does, that is
a genuine finding and you should say so. Do not require hardening unrelated to
the F1 repair.

## 6a. Why this package exists twice, and what that does NOT mean

A Sol package for this same round was prepared on 2026-09-10 and **never
dispatched**: no Sol seat saw its bytes, no verdict came from it, and it consumed
no round. Aaron then migrated the seat for NEW review work to GPT-6 Astra, so the
round was reissued under the SAME review_id -- which is precisely what keeps
`ISSUE_LINEAGE=N13-F1` and `REVIEW_ROUND=2 of 2` intact. The round counter was
NOT reset by changing the model.

The withdrawal is recorded in `ops/ARTIFACTS_UNDER_REVIEW.json`
`_withdrawn_before_dispatch` with `was_dispatched: false`, the repository's existing
vocabulary for a package prepared and never sent. The Sol package itself is still on
disk and in git as historical evidence; it is deliberately NOT on your allowlist,
for the same reason the round-1 transport is not -- it would tell you what a prior
package framed, and you are claim-blind.

**Round 1 of this lineage WAS executed, by a Sol seat, and returned a valid HOLD.**
That verdict stands and is not re-attributed to any other model. What you are doing
is round 2.

## 7. What this review is not

You are not asked to judge the research question, any statistical result, the
wisdom of the frozen Owner ruling, or whether the strategy has an edge. No real
Monte Carlo has been executed and none is authorized: `execute_full_mc` is
gate-first behind `authorize_real_mc`, which still refuses unconditionally. Every
fixture in the category-E tests is synthetic and says so. **If you find a
statistical research result anywhere in this package, that is an incident --
report it.** Do not reopen claims round 1 already established, merely for
reassurance; section 3 of the brief scopes what is yours.

## 8. Cross-references

- Verdict shape, threats, evidence classes, rounds: `ops/REVIEWER_CONTRACT.md` S1.
- Why this seat is mandatory: S2, row "Change to a tier-B authorization gate or
  leakage-sensitive code".
- Attestation header to copy verbatim: `ops/templates/ATTESTATION_HEADER_TEMPLATE.md`.
- The frozen set and its pin: `ops/ARTIFACTS_UNDER_REVIEW.json`, review id
  `N13-F1-REREVIEW-002`.
- The dispatch record: `ops/DECISIONS.md`, kind `REVIEW_DISPATCH`.
