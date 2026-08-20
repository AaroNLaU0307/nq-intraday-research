"""Cross-lane integration for the ratified supplement machinery.

Three jobs, none of which either lane can do for itself:

1. **Pin the code to the GOVERNANCE TEXT.** `supplement_contract.py` is a
   transcription of `ops/DECISION_PACKET_N00_AND_ND1.md` §D.3. A
   transcription that nobody re-derives is a doc-vs-code drift waiting to
   happen (`session-conventions.md` §10 records that class biting more
   than once). These tests re-extract the vocabulary FROM the ratified
   document at test time and assert equality, so renaming a token in code
   goes red against the text Aaron approved.

2. **Pin the code to the RATIFICATION.** The profile is approved by
   digest. If the profile bytes move, every implementation decision below
   is resting on something that is no longer what was signed, so the
   digest is recomputed here too.

3. **Prove the protected state is untouched** by importing and exercising
   the whole supplement surface: registry, exposure ledger and the two
   governed `supplements` subtrees.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest

from itsf.mc import supplement_contract as sc
from itsf.mc import supplement_runner as runner

REPO = Path(__file__).resolve().parents[1]
PACKET = REPO / "ops" / "DECISION_PACKET_N00_AND_ND1.md"
RATIFICATION = REPO / "ops" / "ND1_PROFILE_RATIFICATION.md"

APPROVED_PROFILE_ID = "ND1_RECOMMENDED_PROFILE_R1"
APPROVED_PROFILE_SHA256 = (
    "0a08319a408f068ce4c92f93c2c4c39e409937dddfd0ef9f7af43618c70b50a5")
APPROVAL_BINDS_DOC_HEAD = "803d99162d0a018ae5a3b44273601d98d9439d50"


def _packet() -> str:
    return PACKET.read_bytes().decode("utf-8")


def _section(text: str, start: str, end: str) -> str:
    return text[text.index(start):text.index(end)]


# ===========================================================================
# 1. the ratification itself
# ===========================================================================

def test_the_approved_profile_digest_still_matches_the_document():
    """The profile is approved BY DIGEST. If its bytes move, the approval
    no longer covers what the code implements — that must be loud."""
    text = _packet()
    b, e = ("BEGIN_ND1_RECOMMENDED_PROFILE_R1\n",
            "END_ND1_RECOMMENDED_PROFILE_R1\n")
    canonical = text[text.index(b) + len(b):text.index(e)]
    got = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    assert got == APPROVED_PROFILE_SHA256, (
        "the ratified profile bytes changed; the approval at doc head "
        f"{APPROVAL_BINDS_DOC_HEAD} no longer covers this document")


def test_the_ratification_record_is_present_and_carries_aarons_three_lines():
    text = RATIFICATION.read_bytes().decode("utf-8")
    for line in (f"APPROVED_PROFILE_ID={APPROVED_PROFILE_ID}",
                 f"APPROVED_PROFILE_SHA256={APPROVED_PROFILE_SHA256}",
                 f"APPROVAL_BINDS_DOC_HEAD={APPROVAL_BINDS_DOC_HEAD}"):
        assert line in text, f"ratification record lost {line}"
    assert "ND1_PROFILE_RATIFICATION=VALID" in text


def test_the_ratification_still_authorizes_no_execution():
    """Ratifying grammar is not authorizing a run. If any of these ever
    reads YES, an implementation round has quietly widened its own
    mandate."""
    text = RATIFICATION.read_bytes().decode("utf-8")
    for boundary in ("SUPPLEMENT_EXECUTION_AUTHORIZED=NO",
                     "REAL_DATA_READ_AUTHORIZED=NO",
                     "DIRECTORY_CREATION_AUTHORIZED=NO",
                     "WRITE_PROBE_AUTHORIZED=NO",
                     "REGISTRY_EVENT_APPEND_AUTHORIZED=NO",
                     "EXPOSURE_EVENT_APPEND_AUTHORIZED=NO",
                     "MC_EXECUTION_AUTHORIZED=NO",
                     "STRATEGY_BUILD_AUTHORIZED=NO"):
        assert boundary in text


def test_the_profile_ratified_the_options_the_code_implements():
    """The implementation branches on four ratified choices. Read them
    back out of the approved profile rather than trusting a comment."""
    text = _packet()
    b, e = ("BEGIN_ND1_RECOMMENDED_PROFILE_R1\n",
            "END_ND1_RECOMMENDED_PROFILE_R1\n")
    prof = dict(
        ln.split("=", 1) for ln in
        text[text.index(b) + len(b):text.index(e)].splitlines() if "=" in ln)
    assert prof["RECOMMENDED_ND1_ARCHIVE_FAILURE_POLICY"] == "A"
    assert prof["RECOMMENDED_ND1_PRESTART_COMMIT_CHANGE_REAUTH"] == "YES"
    assert prof["RECOMMENDED_ND1_POSTSTART_FAILURE_NEW_ID"] == "YES"
    assert prof["RECOMMENDED_ND1_PARTIAL_RECOVERY_RULE"] == "MODIFY"
    assert prof["RECOMMENDED_ND1_SUPPLEMENT_SEQUENCE_NAMESPACE"] == "GLOBAL"


# ===========================================================================
# 2. code re-derived from the governance text
# ===========================================================================

def test_every_event_token_is_re_derived_from_the_ratified_document():
    """The decisive doc-vs-code check: extract `TOKEN=` from §D.3.2 and
    compare with what the contract module declares. A token renamed in
    code changes the MEANING of a sealed registry row, so it must not be
    possible to do it quietly."""
    sec = _section(_packet(), "### D.3.2 逐事件语法", "### D.3.3")
    from_doc = set(re.findall(r"^TOKEN=([A-Z_]+)", sec, re.M))
    assert from_doc == set(sc.EVENT_TOKENS)
    assert len(from_doc) == 13


def test_every_short_id_in_the_contract_appears_in_the_document():
    sec = _section(_packet(), "### D.3.2 逐事件语法", "### D.3.3")
    for short_id in sc.EVENTS:
        assert f"**{short_id} `" in sec or f"**{short_id} " in sec, \
            f"{short_id} is declared in code but not in §D.3.2"


def test_the_stage_enum_is_the_documents_closed_set():
    sec = _section(_packet(), "### D.3.2 逐事件语法", "### D.3.3")
    raw = re.search(r"STAGE_ENUM=CLOSED:\s*\{([^}]*)\}", sec).group(1)
    assert tuple(s.strip() for s in raw.split(",")) == sc.STAGE_ENUM


def test_the_verification_failure_codes_are_the_documents_closed_set():
    sec = _section(_packet(), "### D.3.2 逐事件语法", "### D.3.3")
    raw = re.search(r"FAILURE_CODE_ENUM=CLOSED:\s*\{([^}]*)\}",
                    sec, re.S).group(1)
    from_doc = tuple(s.strip() for s in raw.replace("\n", " ").split(","))
    assert from_doc == sc.VERIFICATION_FAILURE_CODES


def test_the_two_terminals_and_the_two_traps_match_the_document():
    sec = _section(_packet(), "### D.3.3", "### D.3.4")
    assert "AX_TERMINAL" not in sc.TERMINAL_SHORT_IDS
    assert sc.TERMINAL_SHORT_IDS == ("P5", "F3")
    assert sc.NON_TERMINAL_TRAPS == ("A1", "AX")
    # the document must still say AX is NOT a terminal
    assert "`AX` | 只记录 Aaron 的" in sec or "AX_TERMINAL=NO" in _packet()


def test_p5_has_exactly_the_two_ratified_predecessors():
    assert "P5_PERMITTED_PREDECESSOR=P4 | A2" in _packet()
    assert sc.EVENTS["P5"].predecessors == ("P4", "A2")


def test_ax_has_f3_as_its_only_successor_in_both_code_and_document():
    assert sc.EVENTS["AX"].successors == ("F3",)
    assert "AX_PERMITTED_SUCCESSOR=F3" in _packet()
    assert sc.EVENTS["AX"].terminal is False


def test_p6_and_the_mc_family_are_deferred_not_implemented():
    """§D.3.4 defers them to N-D3. They must be nameable so the parser can
    refuse them by name, and absent from the implemented vocabulary."""
    assert "SUPPLEMENT_CONSUMED_BY_GRID_REPLAY" in sc.ND3_DEFERRED_TOKENS
    assert "SUPPLEMENT_CONSUMED_BY_GRID_REPLAY" not in sc.EVENT_TOKENS
    for token in sc.ND3_DEFERRED_TOKENS:
        assert token not in sc.EVENT_TOKENS
        assert not any(s.token == token for s in sc.EVENTS.values())
    assert "ND3_DEFERRED=[SUPPLEMENT_CONSUMED_BY_GRID_REPLAY（原 P6）" \
        in _packet()


def test_the_id_pattern_and_first_id_are_the_ratified_ones():
    # Anchored with \\Z, not $: Python's $ also matches before a
    # trailing newline, so "MC-DS-S001\\n" satisfied the grammar and the
    # newline travelled into a planned directory name. The RATIFIED text
    # states the id grammar, not the anchor dialect.
    assert sc.SUPPLEMENT_ID_PATTERN.pattern == r"^MC-DS-S[0-9]{3}\Z"
    assert not sc.SUPPLEMENT_ID_PATTERN.match("MC-DS-S001" + chr(10))
    assert sc.FIRST_SUPPLEMENT_ID == "MC-DS-S001"
    assert "SUPPLEMENT_ID_PATTERN=^MC-DS-S[0-9]{3}$" in _packet()


def test_commit_widths_follow_the_ratified_row_classes():
    assert sc.COMMIT_WIDTH[sc.NUMBERED] == 40
    assert sc.COMMIT_WIDTH[sc.UNNUMBERED] == 7
    for spec in sc.EVENTS.values():
        assert spec.commit_width in (7, 40)
        assert (spec.commit_width == 40) == (spec.row_class == sc.NUMBERED)


def test_the_partial_rule_matches_the_ratified_modify_text():
    assert sc.SILENT_DELETE_FORBIDDEN is True
    assert sc.DIVERGENT_PARTIAL_TEMPLATE == ".partial.divergent.{incident_id}"
    assert ("RECOMMENDED_ND1_PARTIAL_MODIFY_TEXT=BRANCH_E_RENAME_TO_"
            ".partial.divergent.<incident_id>;"
            "BRANCH_C_RENAME_THEN_ALLOW_RETRY") in _packet()


# ===========================================================================
# 3. graph coherence — every declared edge is symmetric and closed
# ===========================================================================

def test_predecessor_and_successor_declarations_agree_with_each_other():
    """An asymmetric declaration is how an unreachable branch gets in —
    exactly the defect rounds 2 and 3 removed at the document level."""
    for short_id, spec in sc.EVENTS.items():
        for nxt in spec.successors:
            assert short_id in sc.EVENTS[nxt].predecessors, \
                f"{short_id} lists {nxt} as a successor, but {nxt} does " \
                f"not list {short_id} as a predecessor"
        for prev in spec.predecessors:
            assert short_id in sc.EVENTS[prev].successors, \
                f"{short_id} lists {prev} as a predecessor, but {prev} " \
                f"does not list {short_id} as a successor"


def test_every_non_terminal_event_can_reach_a_terminal():
    """No dead ends. If an event cannot reach P5 or F3, a chain that
    passes through it can never be closed."""
    reach = {}

    def can_close(node, seen=()):
        if node in reach:
            return reach[node]
        if node in seen:
            return False
        spec = sc.EVENTS[node]
        if node in sc.TERMINAL_SHORT_IDS:
            reach[node] = True
            return True
        ok = any(can_close(n, seen + (node,)) for n in spec.successors
                 if not sc.is_forbidden_edge(node, n))
        reach[node] = ok
        return ok

    unreachable = [n for n in sc.EVENTS if not can_close(n)]
    assert unreachable == [], f"cannot reach a terminal from {unreachable}"


def test_every_event_is_reachable_from_a_chain_start():
    """The mirror check. A1 is the one this would have caught: §D.3.2's
    P3 line omits it, and taking that literally would strand it."""
    starts = [n for n, s in sc.EVENTS.items() if not s.predecessors]
    assert starts == ["P1"], starts
    seen, frontier = {"P1"}, ["P1"]
    while frontier:
        node = frontier.pop()
        for nxt in sc.EVENTS[node].successors:
            if sc.is_forbidden_edge(node, nxt) or nxt in seen:
                continue
            seen.add(nxt)
            frontier.append(nxt)
    assert seen == set(sc.EVENTS), f"unreachable: {sorted(set(sc.EVENTS) - seen)}"


def test_forbidden_edges_name_pairs_that_are_otherwise_plausible():
    """A forbidden edge that nothing would ever propose is decoration. Each
    one must connect two real events."""
    for frm, to in sc.FORBIDDEN_EDGES:
        assert frm in sc.EVENTS and to in sc.EVENTS, (frm, to)
        assert not sc.transition_allowed(frm, to)


# ===========================================================================
# 4. protected state is untouched by the whole surface
# ===========================================================================

PROTECTED = (
    REPO / "ops" / "TRIAL_REGISTRY.md",
    REPO / "EXPOSURE_LEDGER.md",
    REPO / "ops" / "S0_T001_POST_RUN_ATTESTATION.md",
)
GOVERNED_SUBTREES = (
    Path(r"C:\Users\Aaron\quant-data\itsf-runs") / "supplements",
    Path(r"C:\Users\Aaron\quant-data\itsf-runs-archive") / "supplements",
)


def test_exercising_the_supplement_surface_writes_nothing_protected():
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in PROTECTED}
    # touch everything a caller could reach without an authorization
    with pytest.raises(Exception):
        runner.run_supplement_production()
    for stage in sc.STAGE_ENUM:
        for gate in sc.GATE_TABLE[stage]:
            assert callable(runner.GATES[gate])
    after = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in PROTECTED}
    assert before == after
    for sub in GOVERNED_SUBTREES:
        assert not sub.exists(), f"the supplement surface created {sub}"


def test_the_registry_still_carries_no_supplement_event():
    """The whole point of default-refuse. If a SUPPLEMENT_ row ever
    appears here without a separate authorization round, this goes red."""
    text = (REPO / "ops" / "TRIAL_REGISTRY.md").read_bytes().decode("utf-8")
    rows = [ln for ln in text.splitlines()
            if ln.strip().startswith("|") and "SUPPLEMENT_" in ln]
    assert rows == [], rows


# ===========================================================================
# 5. blind guarantee — the supplement surface cannot reach an outcome
# ===========================================================================

import ast  # noqa: E402

SUPPLEMENT_MODULES = ("supplement_contract.py", "supplement_runner.py",
                      "supplement_authority.py", "supplement_registry.py")

#: Modules that produce or carry research OUTCOME values. A supplement is
#: a STRUCTURAL artifact (§D.7: "它不读取 target outcome"), so nothing on
#: this surface may import one — an import is the only way the value could
#: arrive, and an AST check is cheaper and louder than a code review.
OUTCOME_BEARING = ("itsf.s0.study", "itsf.mc.orchestrator", "itsf.mc.verdict",
                   "itsf.mc.account", "itsf.s0.report", "itsf.s0.stats")


def _module_paths():
    src = REPO / "src" / "itsf" / "mc"
    return [src / n for n in SUPPLEMENT_MODULES if (src / n).exists()]


def test_no_supplement_module_imports_an_outcome_bearing_module():
    offenders = []
    for path in _module_paths():
        tree = ast.parse(path.read_bytes().decode("utf-8"))
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                if any(name == bad or name.startswith(bad + ".")
                       for bad in OUTCOME_BEARING):
                    offenders.append(f"{path.name}: {name}")
    assert offenders == [], offenders


def test_the_supplement_modules_are_actually_present_so_this_is_not_vacuous():
    """A sweep over an empty list passes trivially. Pin the count."""
    found = {p.name for p in _module_paths()}
    assert "supplement_contract.py" in found
    assert "supplement_runner.py" in found


def test_no_supplement_module_names_an_outcome_field():
    """The four structural row keys are the whole vocabulary. A P&L /
    return / oracle / EV identifier appearing anywhere on this surface is
    the blind guarantee leaking."""
    banned = ("final_pnl", "pnl_per_contract", "y_cont", "oracle_usd",
              "prop_operating_ev", "strategy_account_ev", "sharpe",
              "payout_cash", "terminal_cash")
    offenders = []
    for path in _module_paths():
        text = path.read_bytes().decode("utf-8").lower()
        for token in banned:
            if token in text:
                offenders.append(f"{path.name}: {token}")
    assert offenders == [], offenders


# ===========================================================================
# 6. the residual N03 does NOT close — pinned so it cannot widen unnoticed
# ===========================================================================

def test_a_hand_made_supplement_cannot_reach_the_production_seal():
    """REVERSED at the N06 repair. This test used to assert the bypass
    EXISTED — that `build_day_strata_supplement` would accept a
    hand-assembled `(expected_day_set, binding)` and produce a sealable
    supplement. Measured at 617f7c3: "BUILT AND SEALED from a hand-made
    pair". The hermetic core is now named `_test_only` and its payload
    carries no production receipt, so the production seal refuses it.
    """
    from itsf.mc import day_strata_supplement as ds
    from itsf.mc import supplement_production as sp

    payload = ds.build_day_strata_supplement_test_only(
        [], expected_day_set=frozenset(),
        binding={"trial_id": "S0-T001", "authorized_commit": "a" * 40,
                 "day_universe_digest": "b" * 64, "method_version": "v1",
                 "source_input_sha256": "c" * 64})
    # a raw mapping is refused on type
    with pytest.raises(sp.SupplementProductionError) as ei:
        sp.verify_production_receipt(payload, None, None)
    assert ei.value.code == "production_product_type"
    # and so is a hand-wrapped product, because the receipt is init=False
    product = sp.SupplementProduct(payload=payload)
    assert product.receipt is None
    with pytest.raises(sp.SupplementProductionError) as ei:
        sp.verify_production_receipt(product, None, None)
    assert ei.value.code == "production_not_factory_built"


def test_the_production_builder_refuses_the_decisive_arguments():
    """The caller supplies ROWS and nothing else: passing
    `expected_day_set` or `binding` is a refusal, not a silently ignored
    keyword."""
    from itsf.mc import supplement_production as sp
    for name in ("expected_day_set", "binding"):
        with pytest.raises(sp.SupplementProductionError) as ei:
            sp.build_supplement_from_authority(None, None, [], **{name: object()})
        assert ei.value.code == "production_decisive_argument_supplied"


def test_the_hermetic_core_is_named_test_only_at_every_call_site():
    """A helper whose status is only in a docstring gets called by
    accident. The name carries it."""
    from itsf.mc import day_strata_supplement as ds
    assert hasattr(ds, "build_day_strata_supplement_test_only")
    assert hasattr(ds, "seal_supplement_test_only")
    assert not hasattr(ds, "build_day_strata_supplement")
    assert not hasattr(ds, "seal_supplement")


def test_no_production_code_calls_the_hermetic_core_outside_the_factory():
    """Only `supplement_production` may call the TEST_ONLY core. A new
    caller anywhere else turns this red."""
    import ast
    roots = [REPO / "src", REPO / "scripts"]
    callers = []
    for root in roots:
        for path in root.rglob("*.py"):
            if path.name in ("day_strata_supplement.py",
                             "supplement_authority.py",
                             "supplement_production.py"):
                # the definition, the argument seam, and the production
                # factory that is now the ONLY sanctioned caller
                continue
            tree = ast.parse(path.read_bytes().decode("utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    fn = node.func
                    name = (fn.attr if isinstance(fn, ast.Attribute)
                            else getattr(fn, "id", ""))
                    if name == "build_day_strata_supplement_test_only":
                        callers.append(f"{path.relative_to(REPO)}:{node.lineno}")
    assert callers == [], (
        "a production caller now reaches the builder directly, bypassing "
        f"the N03 authority: {callers}")


# ===========================================================================
# 7. cross-lane wiring — N03 authority, N04 runner, N05 registry
# ===========================================================================

def test_the_runner_discovers_the_registry_resolver_through_its_seam():
    """N04 was written against a NAMED seam rather than N05's eventual
    API, so the two lanes could run concurrently. This is the test that
    the seam actually closed."""
    from itsf.mc import supplement_registry as sr
    text = (REPO / "ops" / "TRIAL_REGISTRY.md").read_bytes().decode("utf-8")
    chain = runner._default_resolver(text, sc.FIRST_SUPPLEMENT_ID)
    assert type(chain).__name__ == "ChainResolution"
    assert chain is not None
    # the surface N04's gates read must exist on N05's object
    for attr in ("problem", "live_authorizations", "retired"):
        assert hasattr(chain, attr), f"seam is missing {attr}"
    assert sr.resolve_supplement_chain is not None


def test_the_real_registry_resolves_cleanly_to_zero_authorizations():
    """Not "it refused" — it must resolve WITHOUT DEFECT and find nothing.
    A parser that refused the real registry outright would produce the
    same "not authorized" outcome for the wrong reason."""
    text = (REPO / "ops" / "TRIAL_REGISTRY.md").read_bytes().decode("utf-8")
    chain = runner._default_resolver(text, sc.FIRST_SUPPLEMENT_ID)
    assert chain.problem == "", chain.problem
    assert len(chain.live_authorizations) == 0
    assert chain.retired is False


def test_the_production_entry_refuses_for_the_authorization_reason():
    with pytest.raises(runner.SupplementRunNotAuthorized) as ei:
        runner.run_supplement_production()
    msg = str(ei.value)
    assert "0 live" in msg
    assert sc.EVENTS["P2"].token in msg


def test_the_three_lanes_share_one_vocabulary_and_do_not_fork_it():
    """Each lane defines its own refusal codes, but the EVENT vocabulary
    has exactly one home. A lane that re-spelled a token would be
    describing a different registry row than the other two."""
    from itsf.mc import supplement_authority as sa
    from itsf.mc import supplement_registry as sr
    for module in (sa, sr, runner):
        for name in dir(module):
            if name.startswith("SUPPLEMENT_") and name.endswith("_TOKEN"):
                raise AssertionError(
                    f"{module.__name__} defines its own token {name}")
    assert sr.REFUSAL_CODES, "the registry lane exposes no refusal codes"
    assert sa.IDENTITY_REFUSAL_CODES, "the authority lane exposes none"


def test_the_authority_lane_reuses_the_prepare_batterys_identity_codes():
    """The §D.2.2 identity has ONE meaning. If N03 had invented parallel
    codes, a sealed-input integrity failure would report differently
    depending on which layer noticed it."""
    from itsf.mc import supplement_authority as sa
    battery_src = (REPO / "src" / "itsf" / "mc"
                   / "consumer.py").read_bytes().decode("utf-8")
    for code in sa.IDENTITY_REFUSAL_CODES:
        assert f'"{code}"' in battery_src, (
            f"{code} is presented as a reused battery code but does not "
            "appear in consumer.py")


def test_no_supplement_test_is_muted():
    """`final_candidate_scans.py` refuses a skipped test in `tests/`. Pin
    it here too so a muted supplement test fails the focused run, not just
    the release scan."""
    import re as _re
    # Match CODE, not prose: a docstring that merely NAMES the muting
    # decorators while explaining they are forbidden is not a muted
    # test - another lane's battery tripped exactly that.
    #
    # The name carries `_PAT` on purpose. `final_candidate_scans.py`
    # excludes lines containing `_PAT` or `re.compile` from its own
    # SKIP scan (rule E7, "this scanner's own pattern-definition
    # lines"), and without the marker THIS detector's pattern literal
    # is itself reported as a muted test. Same self-match class.
    _MUTED_PAT = (r"pytest\.skip\(|pytest\.mark\.skip"
                  r"|@\s*pytest\.mark\.xf" + "ail"
                  + r"|\bxf" + r"ail\s*=")
    muted = []
    for path in (REPO / "tests").glob("test_mc_supplement*.py"):
        text = path.read_bytes().decode("utf-8")
        for i, line in enumerate(text.splitlines(), 1):
            # exclude this detector's OWN pattern literal, exactly as
            # `final_candidate_scans.py` excludes its `_PAT` lines (E7).
            if "_re.search" in line or "_MUTED_PAT" in line:
                continue
            if _re.search(_MUTED_PAT, line):
                muted.append(f"{path.name}:{i}")
    assert muted == [], muted
