# DELIVERY / OFF-LIMITS CARRIER -- review `N14-EXACT-TREE-001`

```
RECORD_TYPE=OFF_LIMITS_CARRIER_AND_READ_ALLOWLIST
REVIEW_ID=N14-EXACT-TREE-001
DELIVERY_STATUS=ISSUED
    ISSUED means FINALISED FOR HANDOVER -- these bytes are the ones a seat will
    hash, so they must not move. It does NOT mean a seat is reading them: this
    package is PENDING_DISPATCH and Aaron dispatches it. The builder wrote the
    code under review and may neither dispatch nor perform the review.
NODE=N14
NODE_AUTHORITY=ops/outcome_quarantine/MC_TO_STRATEGY_MASTER_PLAN.md section 4 (Canonical DAG),
    read under Aaron's bounded authorization ops/DECISIONS.md DEC-N14-READ-1 and
    transcribed into DEC-N14-READ-2. THAT FILE IS OFF-LIMITS TO YOU -- it is on the
    outcome quarantine list. Everything you need from it is in section 4 below.
REVIEWED_SET_UNCHANGED_SINCE=b2e7a3c9bdc15e085ba80c2ba9194116c6cb811d
ISSUE_LINEAGE=N14  (a NEW lineage; see section 5)
REVIEW_ROUND=1 of at most 2 (ops/REVIEWER_CONTRACT.md S1: "HOLD -> builder fixes ->
    ONE re-review covering the fix plus a builder-declared, reviewer-contestable impact
    scope -> still HOLD -> Aaron. Two rounds per issue lineage.")
FOR=ONE NEW fresh top-level GPT-6 Astra session, claim-blind
SEAT_AUTHORITY=ops/REVIEWER_CONTRACT.md S2.1 -- the seat is
    `OWNER_DEFAULT_INDEPENDENT_REVIEWER`, resolved at dispatch, which Aaron set to
    GPT-6 Astra for NEW work on 2026-09-10. The node authority's own actor column says
    "Codex"; that was classified as a capability-era default rather than obeyed as a
    product requirement -- see DEC-N14-READ-5 for the four facts behind that call.
MUST_NOT_BE=the builder session, any subagent of it, or the GPT-6 Astra session that
    reviewed round 2 of the N13-F1 lineage. That last exclusion is this repository's own
    rule, not politeness: the seat that raised a defect may not certify its closure
    (ops/N06_ROUND2_SOL_PROMPT.md line 30).
BUILDER=Claude Opus / Claude Code, which wrote every line under review and may neither
    dispatch nor perform this review
BLINDNESS=CLAIM_BLIND
BUDGET=1 round (ops/REVIEWER_CONTRACT.md S2, row "Change to a tier-B authorization gate
    or leakage-sensitive code"), extended by S1's lineage rule to at most 2 for any one
    issue lineage. A second HOLD goes to Aaron, not to a third round.
IMPLEMENTATION_REVIEW_TARGET=b2e7a3c9bdc15e085ba80c2ba9194116c6cb811d   <-- the CODE under review
IMPLEMENTATION_REVIEW_TREE=84f9388d53557685e641929a9b5fb6e85a575e4e
    NOTE: `REVIEWED_SET_UNCHANGED_SINCE` above is the FREEZE PIN over the whole 93-file
    allowlist and is a DIFFERENT quantity. In this package the two happen to be the same
    commit, because the newest change to any allowlisted path IS the implementation
    commit. That is a COINCIDENCE of this package, not an identity -- in the previous two
    packages they differed -- so both are stated and both are separately verifiable.
ALLOWLIST_SIZE=93 repository files, 0 external files
CREATED=2026-09-10
```

**Read this file from disk.** Chat-carried bytes are never a source of truth in this
project. Its header block must carry the line
`REVIEWED_SET_UNCHANGED_SINCE=b2e7a3c9bdc15e085ba80c2ba9194116c6cb811d`; if the copy in front of
you says anything else, it is stale -- open the file. (A line NUMBER is deliberately not
cited: this document has already been regenerated once and the number moved.)

## 0. Read this before anything else

This is **N14**, a node of the project's canonical DAG, and it is the node's whole
content: an independent exact-tree review of the Monte Carlo implementation. It is not
a re-review of anything. Section 5 tells you what came before it and why none of that
discharges it.

Section 3 is the exhaustive set of paths you may read. **If an obligation in the brief
requires a path that is not in section 3, STOP and report it as a transport defect** --
do not go and find the file. A transport defect costs a package; a contaminated seat
costs a seat, and in this project seats do not regenerate.

**No conclusion is asserted here.** This document takes no position on the state of the
tree, on the adequacy of its tests, or on what your verdict ought to be.
Where it states a fact the builder measured, it labels it SELF-REPORTED, and under
`ops/REVIEWER_CONTRACT.md` S1 a self-reported restatement is never BLOCKING and never
PASSING either.

## 1. The forbidden set

Reading any of these makes you outcome-exposed and permanently disqualifies you from
the outcome-blind Stage I seat this project still needs. It is not recoverable.
**Treat every path in the OFF-LIMITS block below as closed**, prefixes included:

```
ops/outcome_quarantine/                 the whole subtree, including the node authority
                                        this review's own definition came from
ops/EXPOSURE_LEDGER.md  and  EXPOSURE_LEDGER.md (repository root)
qros-state.yaml                         RESTATES A REVEALED VERDICT and is NOT yet on the
                                        quarantine list, because that guard walks *.md only
                                        (ops/DECISIONS.md DEC-N14-ENTRY-4). Treat it as
                                        forbidden. It is deliberately absent from section 3.
any file matching S0_T001_RESULT_*      the revealed outcome material itself
ops/DECISIONS.md, ops/RESEARCH_STATE.md, ops/BACKLOG.md
                                        not outcome-carrying, but they are the CLAIM record.
                                        Reading them is what claim-blind means you do not do.
```

The first two groups are checkable: `ops/OUTCOME_CARRYING_ARTIFACTS.json` is in your
allowlist precisely so you can verify the forbidden set yourself rather than trust this
section. `qros-state.yaml` is the one item that is forbidden here but NOT on that list;
that gap is a known open issue and is the reason it is named explicitly.

## 2. How to read the tree, and how to run the tests

**The tree is static under you.** `git log b2e7a3c9bdc15e085ba80c2ba9194116c6cb811d..HEAD` touching any
allowlisted path is EMPTY by construction -- the pin was derived as the newest
last-change commit across the 93 files, not typed. Every commit after it touches `ops/`
bookkeeping only: this delivery, the freeze register and the append-only ledgers.
Verify that yourself:

```
git log b2e7a3c9bdc15e085ba80c2ba9194116c6cb811d..HEAD -- src/ tests/ STUDY_0_PREREGISTRATION.md
```

It is the one claim in this document that, if false, would mean you are reviewing a
moving tree.

**The tests.** Bare `pytest` is not on PATH in this environment; the module form is. No
virtualenv exists and none is expected -- `.python-version` is `3.13` and the pinned
packages are in `ops/requirements.lock.txt`. From the repository root:

```
# the whole MC surface -- category E in one command
python -m pytest -q tests/test_mc_*.py tests/test_no_public_mc_function_is_unreached.py

# the frozen-grid semantics and the sealed infeasibility rule
python -m pytest -q tests/test_mc_grid_channel_b27.py tests/test_mc_grid_replay_n11.py

# the runner, the seal path and the convergence/verdict chain
python -m pytest -q tests/test_mc_runner_n13.py tests/test_mc_cold_replay.py \
    tests/test_mc_node_integration.py tests/test_mc_consumer.py

# the registry boundary and the authorization gates
python -m pytest -q tests/test_mc_registry_contract.py tests/test_mc_registry_parser.py \
    tests/test_mc_supplement_authority.py tests/test_mc_feasibility_gates.py
```

If `python` resolves elsewhere in your session, the interpreter used was
`C:\Users\Aaron\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\python.exe`
(3.13.14, pytest 9.1.1). `scripts/run_governed.cmd` is the sanctioned entry for a
governed RUN, **not** for tests -- do not use it here, and do not execute a real MC run
under any circumstances: none is authorized and N14 explicitly authorizes nothing.

**Do NOT run the full suite.** Several tier-C governance tests walk `ops/` recursively
and read quarantined bytes inside the test process. Under `ops/REVIEWER_CONTRACT.md`
section 4.2 that is execution rather than inspection, but there is no reason to incur
it: no obligation in the brief needs it. If you run it anyway, declare it under
`MODULES_EXECUTED_NOT_INSPECTED`.

**Builder-side transport validation, and what it is NOT.** The builder ran the commands
above at the frozen target immediately before preparing this package and they started
and completed; the counts are in the DISPATCH. That is evidence the commands work in
this environment. It is SELF-REPORTED with respect to the implementation. A green suite
the builder ran is not evidence the code is right; your run and your reading are.

## 3. The read allowlist -- exhaustive: 93 repository files

Nothing outside this list. The list was built by rule -- glob the MC subsystem, resolve
its imports from the AST, glob its tests -- so that it is the tree rather than a
selection from it.

### A -- reviewer authority (restated in the brief too, so nothing needs hunting)  (4)

| sha256 | bytes | path at `b2e7a3c9bdc1` |
|---|---|---|
| `ce076ca55a3400ffb3b8725ad891097e09915ffb911082c630d0889ce02b43c1` | 8418 | `ops/REVIEWER_CONTRACT.md` |
| `bae72767ec6d6e89a546495a5114c12713ae20f9b9801c15d2d8c711cd90d651` | 2805 | `ops/templates/VERIFICATION_BRIEF_TEMPLATE.md` |
| `fb1bd88098543cb82a1cf63cdf2912deb62177f2a5988aa1a9f68d28c26b06b6` | 1246 | `ops/templates/ATTESTATION_HEADER_TEMPLATE.md` |
| `a61c125b4e2e551955ce59816c9ccbc6a449a91d7f7701095eeb586e5c155f4b` | 2563 | `ops/OUTCOME_CARRYING_ARTIFACTS.json` |

4 file(s).

Your own contract. Read it before deciding what may block. `OUTCOME_CARRYING_ARTIFACTS.json` is
here so you can check the forbidden set yourself instead of trusting section 1.

### B -- the SEALED preregistration  (1)

| sha256 | bytes | path at `b2e7a3c9bdc1` |
|---|---|---|
| `6cca20b7b1ce496d582ef5b4677333ba1b74bc577020ab29df00ff0c0d1af132` | 22498 | `STUDY_0_PREREGISTRATION.md` |

1 file(s).

The frozen grid, the sealed arithmetic and the `infeasible_by_sample` rule are defined here and
nowhere else. Where the code and this file disagree, this file is the authority.

**It is on this allowlist but deliberately NOT in the freeze register**, and you should know
why rather than notice the gap. Its line 157 names a quarantined ledger without an off-limits
marker, so registering it turns a transport guard red; the only way to register it would be to
EDIT AN APPROVED FROZEN DOCUMENT to make a test pass, which this project has already ruled is
backwards. Its bytes are still protected for you by the sha256 above -- a mismatch is a STOP,
exactly as for every other row. Recorded in ops/DECISIONS.md as a discovered issue rather than
smoothed over.

### C -- the MC implementation, EXHAUSTIVE (this is the tree under review)  (44)

| sha256 | bytes | path at `b2e7a3c9bdc1` |
|---|---|---|
| `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 0 | `src/itsf/mc/__init__.py` |
| `27a4d763fc7c58b498a50d8b738d4846fdc5b8a4ce7d818e3167e2934e6c5db6` | 9312 | `src/itsf/mc/account.py` |
| `86ff419f98558592e0a3c4d9cac0dcb7ddbff2d3f8598f88827e23440b91f964` | 73278 | `src/itsf/mc/atoms.py` |
| `5c039332dd5539782f254306157b622db75d34e978e72639a9e82464fbe1c0ee` | 5995 | `src/itsf/mc/bootstrap.py` |
| `9dafd4e85d35b215f8d8a51a16b0d16d169fea55e2dba9625432f912db3ee184` | 7102 | `src/itsf/mc/bundle_precheck.py` |
| `e271757385c3f1d0bf1e4b2e3b24eebe2e4785667d2c5e25e87b91f89dd9c6f1` | 12732 | `src/itsf/mc/cold_reducer.py` |
| `4375af108e1d03cce266fb59f44b6fbc5e7fbb18e2fd8a40d746919e38f2ee8a` | 179753 | `src/itsf/mc/consumer.py` |
| `f87b723c61b46d8e1aa24f7f5d2c7b72bd85244276e6fbad8d082e0ddc5e6830` | 21836 | `src/itsf/mc/day_strata_classify.py` |
| `b714af3866081501305137ca51330e201b43a6ac188ceae7d13f262a5b6a0fa9` | 8870 | `src/itsf/mc/day_strata_context.py` |
| `24213a4956a60590c74534c1ac0a05270bf9e3beb0644e09978cf23581d4ba53` | 12583 | `src/itsf/mc/day_strata_dryrun.py` |
| `6a9ec1ffad7ede1cf7055205698642d788bd1258d816babad864d184c30de058` | 6778 | `src/itsf/mc/day_strata_failure.py` |
| `39a28b3499e23ab02002661aafa3e699840a281a1bf823121fe405929e437f7c` | 20571 | `src/itsf/mc/day_strata_pipeline.py` |
| `8761cf36d82e9ff3b8e6d0c0e84524d44b764bdc2ec96118e9ca044368f75dab` | 10988 | `src/itsf/mc/day_strata_rows.py` |
| `3554cd326c06c04c3298ba44164338dcdd9e63df9a253f63ca3b0d82aa30f410` | 22095 | `src/itsf/mc/day_strata_supplement.py` |
| `3431a3b4d96710079b8c6df233d12a8d1771f11178627d4551a6e7f8e38237da` | 13363 | `src/itsf/mc/feasibility.py` |
| `e6f3c4284242d4fdc739b2367e56b1f90d9ddc88d7d6ac30435d7412d4086816` | 3733 | `src/itsf/mc/fixed_world.py` |
| `765200e90364c458c3ea7369913ae667e994e51c118541054e1330cd1f923398` | 30141 | `src/itsf/mc/grid_channel.py` |
| `c7b9dd29d886a2261b96988d5f40a0b9fba2d51556d2a1a53c3b9f7feddde485` | 52810 | `src/itsf/mc/grid_replay.py` |
| `817419cd5910fd352bf291c8c74d6e4723cc6afefcd1a1f5fe3cb1326bd88e34` | 10894 | `src/itsf/mc/mc_contract.py` |
| `d4a881a81b9b5d0c5ddba179ed7b2f673f12eb013347156ea81a27bd660834be` | 24351 | `src/itsf/mc/mc_registry.py` |
| `cc5dc4a02e8e887716e86edd7925df7aff5970efe790668b0a4225746acf2b37` | 19397 | `src/itsf/mc/mc_runner.py` |
| `272a804505b5ba51acc4ac62ca5c044a616213d770672f3330205352c8232088` | 24144 | `src/itsf/mc/orchestrator.py` |
| `95082b32e6d41f2d277c36ce893d4e34696ea11e63d9386ede82092e67c00b78` | 5655 | `src/itsf/mc/over_budget.py` |
| `29941d3d5306cb1a3e8951f662068c91e2beed49a3fcb44f47785a8ce72317bc` | 16235 | `src/itsf/mc/owner_control.py` |
| `474a5c83f90ab4f13f698fc118564bbace3f8153d2faf245c54edf583963d4fc` | 13439 | `src/itsf/mc/production_inputs.py` |
| `b07827067ed68033f1b21834f680546ef7f2c99629fb71c78deab62fdc76ea2a` | 4649 | `src/itsf/mc/real_input.py` |
| `549964e3ad657cf91ac3ec44dc4272c453760e1dd9d1b9f6a7d38866ab5391a4` | 47337 | `src/itsf/mc/registry_boundary.py` |
| `499224b94113f47333fc2d2e8f2d3bcf6b24bc803a699d7419f51a716e1b3ede` | 13331 | `src/itsf/mc/registry_integrity.py` |
| `774cd76f927effa4560e699f4243269d833b34f09dbd8fff800044fe39d9b652` | 37130 | `src/itsf/mc/supplement_authority.py` |
| `536c570074742e908fe14ed286030c1f291c117fabfa4ec5025a3a821298a01c` | 4581 | `src/itsf/mc/supplement_build.py` |
| `2f895ead2cda7ff3d1016db5450c5ad8921eaadd85353a248d5b09da4fbf83d5` | 19463 | `src/itsf/mc/supplement_chain.py` |
| `e93a75e44c72d77d19abf72c7cd0d923d4b719ddd1e19e34f6924c19fbc0e24f` | 34389 | `src/itsf/mc/supplement_contract.py` |
| `2f34f65a6d5e67928f63a9cb01829d44d61ec9e76f9ae7ca6e802fa378a78692` | 3984 | `src/itsf/mc/supplement_derive.py` |
| `d15611ce834f228069521e48c248a1936e2804a9894d1ca2c5c38c2e48f8290a` | 4853 | `src/itsf/mc/supplement_inputs.py` |
| `61f4bc013b0f28f922869de569c7fe323fdb60b9adb1894827072e5f2d057ce2` | 7090 | `src/itsf/mc/supplement_precheck.py` |
| `7f737955c35954516cafc208c1c4382f4ff876b7218cd07d728327570b5ac976` | 22989 | `src/itsf/mc/supplement_production.py` |
| `ff4ba0f66aee5625e4ee1d53d915bfc3e78cf31c110dd0cf6bd85d579e2042b5` | 72459 | `src/itsf/mc/supplement_registry.py` |
| `9ba7ad59ed012112e700aac59451ec729660ca3fa25a3d89a9bf5ef74784b166` | 67929 | `src/itsf/mc/supplement_runner.py` |
| `e6141c51159a88e3a782d453ac65245f06d61eddf43e3f50a6d53231d7fba8ee` | 5479 | `src/itsf/mc/verdict.py` |
| `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 0 | `src/itsf/mc/platforms/__init__.py` |
| `c6dab81cc747d185bf83aab54f5d8950bae45ab95c10d4e1128611303c05d648` | 30202 | `src/itsf/mc/platforms/authoritative.py` |
| `3cec89ba6865d2dd9b6901de362b6553a8a12afc77019c5cce17ee759eb14cb4` | 2260 | `src/itsf/mc/platforms/base.py` |
| `21a453404719bd8b04debb74091e57faa6b657540275e7140cb99f8b59a206ec` | 20131 | `src/itsf/mc/platforms/lucid.py` |
| `036b8ac5804bedb5ad90fff4bb3f545e247187494300960125bfe9c2423ecf08` | 27037 | `src/itsf/mc/platforms/topstep.py` |

44 file(s).

Every module under `src/itsf/mc/`, with no module withheld. "Exact-tree" means exactly that:
the subsystem as it stands, not a delta and not the parts the builder found interesting.

### D -- the import boundary, resolved from the AST rather than chosen  (13)

| sha256 | bytes | path at `b2e7a3c9bdc1` |
|---|---|---|
| `97d50740d938cb40eccab6595e6ba7284c493e9a662e311ddce31700f294a002` | 64677 | `src/itsf/contracts.py` |
| `47804ecb3269e805fb95537c4d7b3c3b4f85342051d7dead1b82a22ad117523c` | 7779 | `src/itsf/data/calendar.py` |
| `c34a9d13368eb4106d432c0b77ce25f7fd8e56f43642e5d1dee4f20e46c6d41a` | 6148 | `src/itsf/data/dbn_loader.py` |
| `eb6e499e4348f2a43138aaf24fa33cedda035b01d445b39a1d3e39ad44c9a17d` | 8050 | `src/itsf/data/manifests.py` |
| `d4cedff56a0711e3dcdf7680b2c11d77c15ce03156a8d817ef2872a4f9dd861d` | 44099 | `src/itsf/execution_identity.py` |
| `2e850c8dd099a7b7c6dae87a14c4dfc23dbef240b489d7a27f73b8fc66ce3e61` | 6022 | `src/itsf/guards.py` |
| `c2add6d8a0d8e14a5c91bbf19fe39c10f09286db4d5e55113fb612f9ed23727a` | 59084 | `src/itsf/s0/context.py` |
| `240a59366c19cd96dd08c944e513cb0e5ad7927f483823275f19210de13b3b32` | 56989 | `src/itsf/s0/dataset.py` |
| `c5ecded879c62c6509645bd63751be9e73a9d82c956b6132391b759ddea6049e` | 69193 | `src/itsf/s0/gridmix.py` |
| `b28394f997693269e7635b9324f5315e0b7e865cb1489f6a74fa0378dbc81810` | 182402 | `src/itsf/s0/handoff.py` |
| `af1ddae6815c6c46fcd7f96caf245d6c0deedfe3a7aa793f81ad17276ac1e1c6` | 179039 | `src/itsf/s0/report.py` |
| `888d639194578b8d22d93e4d61ab87d2cb8860d00759bfc1994f5b27c4f3b276` | 90687 | `src/itsf/s0/runinfra.py` |
| `405d3e2001dc691bd1591cdb22a0a67075d31e1c584faf2a432f2049eb471416` | 40283 | `src/itsf/s0/study.py` |

13 file(s).

Produced by walking every `ImportFrom` in category C and keeping what resolves outside `mc/`.
It is therefore the real boundary, not the builder's opinion of it. If you find an import that
reaches a module not listed here, that is a transport defect and I want to hear about it.

### E -- the MC test surface, EXHAUSTIVE  (31)

| sha256 | bytes | path at `b2e7a3c9bdc1` |
|---|---|---|
| `a0b1be2eed2f84d7d68888b8d31d761c3e0d374639abeec07c25aa9d2dc17568` | 57065 | `tests/test_mc_atoms.py` |
| `a5840d3d6878c5753e3ee3eed13cfcb75eece2c33923110b70c23e57fe479458` | 20962 | `tests/test_mc_b26_reduction_feasibility.py` |
| `4e80f9269dcee1ae25461d9fcbae86aa6ac56db4ec74b9098618638eab8213c3` | 28462 | `tests/test_mc_battery_boundary.py` |
| `983879967b6450cba07d2c4c6e58e477ecd26ffc316f00ef42967dda1e321275` | 16129 | `tests/test_mc_bprov_seal_provenance.py` |
| `f9b5fc01ed6abc15e1406376149742e3c75ed7bb0a4971a8c5c2d3b1b924746f` | 8087 | `tests/test_mc_bundle_precheck.py` |
| `8538d499ced68c5e78944af09c09c9677c7eeaec892259981687f5bfbb754608` | 55588 | `tests/test_mc_cold_replay.py` |
| `2bae7b182d712faebc98de7c438e78845cb81441b5e6e1d97c018c0ece04daf5` | 34168 | `tests/test_mc_consumer.py` |
| `556dae13146bd357b0f4c27316385995b6d7a45f321a4bdf9e291aa0b5c92d3a` | 51592 | `tests/test_mc_convergence_provenance.py` |
| `2d40779d3b8c7371b93377bd038cadcc096740583be6fa14572a595c2bfa5ee8` | 18514 | `tests/test_mc_custody_calendar.py` |
| `ece6593aa21cf1321e967940e0748f1d843baadac5fba5dfd5577d2767d97c88` | 12147 | `tests/test_mc_day_strata_supplement.py` |
| `0694b8a32e0b503586dd2c5682dac470d66a496910e886212385d480741da573` | 7075 | `tests/test_mc_feasibility_composition.py` |
| `61fffa86ccbce81d9c5f66fe64cc3c507a120826b6399c34c69a037249c5f0c3` | 11216 | `tests/test_mc_feasibility_gates.py` |
| `3efdb80a820c7f100901c1abdb87381ecd0e9a05fa9d7e56e178e5ab47950846` | 6867 | `tests/test_mc_fixed_world_selection.py` |
| `3b45600ac9458aec41cec0fd15519a04e791246ee660f6e2a18a682e7a2fe7f4` | 58439 | `tests/test_mc_grid_channel_b27.py` |
| `5e55324444e83d6c44f4e6b58e1d49da743c1687c8761e0a6ad94203c06bb050` | 42439 | `tests/test_mc_grid_replay_n11.py` |
| `27a64a381616252b5ca94fb8a796e7f7f1d573b4a0604746c3dcb5ed38c01cd2` | 36310 | `tests/test_mc_n01_repairs.py` |
| `6eddc15410abd4ee2351931ebeaf855521186b3e52787e1444866037344780b9` | 28128 | `tests/test_mc_node_integration.py` |
| `a047a3e0a3fc5fe6b96e64506b87e36d74d56d2c79a9606a151084d4fd6c09f3` | 5517 | `tests/test_mc_over_budget_predicate.py` |
| `899a7da44b02a9d856d162bad26f708c9f5edfd9c61484d124923b4e7ccd3b69` | 11953 | `tests/test_mc_r2_2_integration.py` |
| `0005efa64df6599e1669a3d6557f1c786001b9e36f19cff1a6a36aa2f26c6fa4` | 33020 | `tests/test_mc_r2_3_evidence.py` |
| `347e0133c6e1c787809e202f2fb8880be1788d787e7bbac6f0bbeb2e7a001cdf` | 13223 | `tests/test_mc_registry_contract.py` |
| `73e837fa94421b97fd9abdf034102fa2e32ba00203ed23277752d1b7a0baa1f0` | 25548 | `tests/test_mc_registry_parser.py` |
| `8c3b22702d3ef12b809ec98c458086f43711cf7c6a1a9df6fa4bd7d97526efa6` | 12409 | `tests/test_mc_runner_n13.py` |
| `980d3334b5f6f52c2b8e29752cda2772f2f42e281734d01dcc407ada0549c6d1` | 48952 | `tests/test_mc_supplement_authority.py` |
| `a28a53006e8c9ed5608967e16c3b1a2bdc59ba38c99fe6246aaa6eacd079552e` | 10082 | `tests/test_mc_supplement_coercion_census.py` |
| `100a1b22a84c7da1bac7a372fda4d2784ecf82208dae4f78d733e2c6e61a1f83` | 36197 | `tests/test_mc_supplement_integration.py` |
| `ac5d00209d80c85a3e337046ab774eb7b6a835a78b0ca0fba71ff64b114f6769` | 70966 | `tests/test_mc_supplement_paths_battery.py` |
| `57ad8a7c13cd8b5859ebbfc36015bdca544ce21ff5a24f9b5f545cfa63f37399` | 106582 | `tests/test_mc_supplement_provenance_battery.py` |
| `aabec2537e2f3c31c6440ed37f7e0c713d951df301fa0f80e73e6a3054c68bfd` | 49387 | `tests/test_mc_supplement_registry.py` |
| `4ddba05a6e334af77b68c55f51db0f3f898f50ea2b0c7178b1f8119006a921d6` | 39363 | `tests/test_mc_supplement_runner.py` |
| `81a26b98bd91e5c9c2033ab5864d7bd3dd61453b993af358ebe17150af746ba5` | 6640 | `tests/test_no_public_mc_function_is_unreached.py` |

31 file(s).

The tests are IN the review, not evidence for it. A test that pins the wrong behaviour is a
finding -- this project has shipped two of those and both were caught by a reviewer, not by me.

Plus this delivery document itself, `ops/OFF_LIMITS_N14_EXACT_TREE_2026-09-10.md`, which you are
reading. It is registered and hashed like everything else.

## 4. What N14 is, from the node authority -- and what it is NOT

You may not read the node authority; it is quarantined. Its N14 row, transcribed:

```
dependency : N13, and nothing else
content    : independent exact-tree MC review
actor      : the independent non-builder seat
data face  : none
prohibitions: appends NO `READY` row; authorizes NOTHING
successor  : N15, whose dependency cell reads literally "N14 PASS"
```

Three consequences that bound your work:

1. **This review happens BEFORE any real Monte Carlo run.** The real run is N16, two
   nodes downstream, and it additionally requires the Owner's explicit authorization.
   `REAL_MC_AUTHORIZED = NO`, `REAL_MC_EXECUTED = NO`, and no sealed run output exists.
   If an obligation seems to require one, that is a transport defect -- report it.
2. **Your verdict is the node's completion condition.** N15 cannot begin without a PASS
   here. That is the weight this seat carries; it is also why a finding that cannot name
   a threat and a concrete failure path belongs in `PASS_WITH_BACKLOG`, not in a HOLD.
3. **Nothing you do appends a READY row or authorizes a run**, and neither does anything
   the builder does on the strength of your verdict.

## 5. What came before this, and why none of it discharges N14

Stated because withholding it would let you re-derive it from scratch, and because if
any of it is wrong you should say so.

- The MC implementation received **two** independent claim-blind rounds earlier, both
  scoped to one delta (a grid-selector change), not to the tree. **Both returned HOLD.**
- The second HOLD named a real defect. The builder repaired it, and the Owner accepted
  that repair on **builder-mechanical evidence only**: the repair commit --
  `b2e7a3c9bdc15e085ba80c2ba9194116c6cb811d`, the tree you are reviewing -- **has never been**
  **examined by any independent seat.** The ordinary two-round budget for that issue
  lineage was spent before the repair existed.
- Those rounds belong to the issue lineage `N13-F1`. **This is a different lineage with
  its own budget**, because the node authority makes N14 a separate node with a separate
  actor and a `PASS` that no seat has produced. The exhausted N13-F1 budget is not
  inherited and no unlimited budget was invented.

None of that is a claim about correctness in either direction, and you are not being
asked to ratify the Owner's acceptance.

## 6. Known open backlog rows, carried in so you do not spend a finding on them

All three are already recorded as NON-BLOCKING. Re-raising one is not wrong, but say so
explicitly if you think a classification is mistaken -- reviewers classify, builders may
not reclassify.

- **B-29** -- a hand-built `GridDraw` is forgeable via `object.__new__` plus a
  recomputed self-digest. Classified non-blocking by an earlier seat on the ground that
  the governed runner accepts no caller-supplied draw on the seal path. That ground is
  inside your scope; if it does not hold, this becomes blocking.
- **B-30** -- whether the sealed `infeasible_by_sample` state is reachable on the real
  data path. Settling it needs the outcome-derived day split, which is blinded from you
  and from the builder. `UNKNOWN REACHABILITY != KNOWN DEFECT`.
- **B-33** -- N14's own completion row belongs in a quarantined file. A governance
  bookkeeping problem for the Owner, with no bearing on the code.

## 7. What this review is not

- Not an authorization of anything, and not a READY append.
- Not a statistical review: no MC has been run, nothing is revealed, and no outcome
  exists to review. `STATISTICAL_SIGNAL = NOT_TESTED`.
- Not a governance audit of `ops/`. The three ledgers are deliberately off your list.
- Not a review of a review. If you conclude the earlier rounds erred, that is a finding
  about the code they passed over, not about them.

## 8. Cross-references

- Verdict shape, threats, evidence classes, rounds: `ops/REVIEWER_CONTRACT.md` S1.
- Seat and blindness: same file, S2 row "Change to a tier-B authorization gate or
  leakage-sensitive code", resolved through S2.1. **That row was chosen by the builder**
  because S2 is keyed by situation and has no node rows; the choice is recorded as a
  contestable determination in `ops/DECISIONS.md` DEC-N14-READ-4. If you judge a
  different row applicable, say so as a transport finding.
- Contamination protocol: same file, S4. Exposure before freeze means STOP and a row on
  the seat axis.
- The dispatch and the verdict are one row each in `ops/DECISIONS.md` (S5). You write
  neither; you return the attestation and Aaron records it.

