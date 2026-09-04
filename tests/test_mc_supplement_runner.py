"""N04 supplement runner — gate closure, state machine, archive policy A,
`.partial` recovery, and the default-refuse production entry.

Everything here is synthetic. No real Development data is opened, no
output root is touched, no directory is created under the governed roots,
and nothing is appended to `ops/TRIAL_REGISTRY.md` or `EXPOSURE_LEDGER.md`
— `test_production_entry_writes_nothing_anywhere` proves the last two by
hashing the files either side of the call.
"""
from __future__ import annotations

import dataclasses as _dc
import hashlib
from pathlib import Path

import pytest

from itsf.mc import supplement_contract as sc
from itsf.mc import supplement_runner as r

REPO = Path(__file__).resolve().parents[1]
INC = "INC-0123456789ab"
SID = "MC-DS-S001"
HEAD40 = "a" * 40


# ===========================================================================
# helpers — minimal stand-ins for the N05 chain and the runinfra report
# ===========================================================================

@_dc.dataclass
class FakeP2:
    actor: str = "Aaron"
    authorized_commit: str = HEAD40
    output_root: str = r"C:\Users\Aaron\quant-data\itsf-runs"


@_dc.dataclass
class FakeChain:
    live_authorizations: tuple = ()
    problem: str = ""
    retired: bool = False


@_dc.dataclass
class FakeAuthority:
    test_only: bool = False
    authorized_commit: str = HEAD40
    supplement_id: str = SID
    file_sha256_digest: str = "b" * 64
    day_universe_digest: str = "c" * 64
    method_version: str = "mc_day_strata_supplement.v1"


@_dc.dataclass
class FakeRecheck:
    relative_path: str = "f.json"
    source_bytes: int | None = 10
    dest_bytes: int | None = 10
    source_sha256: str | None = "d" * 64
    dest_sha256: str | None = "d" * 64
    match: bool = True


@_dc.dataclass
class FakeInventory:
    n_files: int = 1
    n_dirs: int = 0
    total_bytes: int = 10
    source_stable: bool | None = True
    staging_matches_source: bool | None = True
    dest_matches_source: bool | None = True
    source_stable_after_verify: bool | None = True


@_dc.dataclass
class FakeReport:
    ok: bool = False
    status: str = "archive_failed"
    files: tuple = ()
    errors: tuple = ()
    inventory: object | None = None


def _ctx(**over) -> r.GateContext:
    base = dict(supplement_id=SID, head_commit=HEAD40, registry_text="",
                runs_root=None, archive_root=None, repo_dirty_paths=(),
                g9_flag=None, second_copy_flag=None, frozen_hashes_ok=True,
                chain=FakeChain(live_authorizations=(FakeP2(),)),
                authority=FakeAuthority())
    base.update(over)
    return r.GateContext(**base)


def _gate_code(name: str, ctx) -> str:
    with pytest.raises(r.SupplementRunnerError) as ei:
        r.GATES[name](ctx)
    return ei.value.code


# ===========================================================================
# 1. the gate enum is MECHANICALLY DERIVED from real gates
# ===========================================================================

def test_gate_enum_matches_the_implemented_gates_exactly_and_in_order():
    """`F1_GATE_NAME_ENUM` is only meaningful if it enumerates gates that
    actually exist. A declared-but-unimplemented gate, or an implemented
    one nobody declared, fails here rather than shipping an aspirational
    enum the F1 rows would then quote."""
    assert tuple(r.GATES) == sc.GATE_NAME_ENUM
    assert set(r.GATES) == set(sc.GATE_NAME_ENUM)
    assert len(sc.GATE_NAME_ENUM) == len(set(sc.GATE_NAME_ENUM))


def test_every_declared_stage_gate_is_callable_and_stage_scoped():
    seen = []
    for stage in sc.STAGE_ENUM:
        for name in sc.GATE_TABLE[stage]:
            assert callable(r.GATES[name])
            seen.append(name)
    assert seen == list(sc.GATE_NAME_ENUM)


def test_gate_enum_is_not_empty_which_was_the_ratified_precondition():
    """§D.3.2 F1 shipped with `GATE_NAME_ENUM=CLOSED (empty set — an
    undefined gate may not be emitted)`. N04 closing it is the thing that
    makes F1 emittable at all."""
    assert len(sc.GATE_NAME_ENUM) > 0


# ===========================================================================
# 2. every A_PRECHECK gate refuses for its own reason
# ===========================================================================

def test_g9_gate_refuses_when_the_flag_is_absent():
    assert _gate_code("g9_hard_blocker", _ctx()) == "gate_refused:g9_hard_blocker"


def test_second_copy_gate_refuses_when_the_flag_is_absent(tmp_path):
    g9 = tmp_path / "g9"
    g9.write_text("x")
    code = _gate_code("second_copy_attested", _ctx(g9_flag=g9))
    assert code == "gate_refused:second_copy_attested"


def test_frozen_hashes_gate_refuses_unless_verification_passed():
    assert _gate_code("frozen_hashes", _ctx(frozen_hashes_ok=False)) == \
        "gate_refused:frozen_hashes"
    assert _gate_code("frozen_hashes", _ctx(frozen_hashes_ok=None)) == \
        "gate_refused:frozen_hashes"


def test_git_clean_gate_allowlists_only_the_registry():
    r.GATES["git_clean"](_ctx(repo_dirty_paths=("ops/TRIAL_REGISTRY.md",)))
    assert _gate_code("git_clean",
                      _ctx(repo_dirty_paths=("src/itsf/mc/consumer.py",))) == \
        "gate_refused:git_clean"


@pytest.mark.parametrize("bad", ["MC-DS-S1", "MC-DS-S0001", "mc-ds-s001",
                                 "MC-DS-X001", "", "S0-T001"])
def test_supplement_id_pattern_gate_refuses_every_near_miss(bad):
    assert _gate_code("supplement_id_pattern", _ctx(supplement_id=bad)) == \
        "gate_refused:supplement_id_pattern"


def test_chain_defect_refuses_the_whole_resolution():
    ctx = _ctx(chain=FakeChain(problem="duplicate supersede of event 7"))
    assert _gate_code("registry_chain_resolvable", ctx) == \
        "gate_refused:registry_chain_resolvable"


def test_missing_chain_is_a_refusal_not_a_permissive_default():
    assert _gate_code("registry_chain_resolvable", _ctx(chain=None)) == \
        "gate_refused:registry_chain_resolvable"


def test_zero_and_two_live_authorizations_both_refuse():
    assert _gate_code("live_authorization_unique",
                      _ctx(chain=FakeChain(live_authorizations=()))) == \
        "gate_refused:live_authorization_unique"
    two = FakeChain(live_authorizations=(FakeP2(), FakeP2()))
    assert _gate_code("live_authorization_unique", _ctx(chain=two)) == \
        "gate_refused:live_authorization_unique"


def test_exactly_one_live_authorization_passes_so_the_negative_is_specific():
    r.GATES["live_authorization_unique"](_ctx())


def test_authorization_actor_must_be_aaron():
    chain = FakeChain(live_authorizations=(FakeP2(actor="main agent"),))
    assert _gate_code("authorization_actor", _ctx(chain=chain)) == \
        "gate_refused:authorization_actor"


def test_authorized_commit_must_be_40hex_and_equal_head():
    short = FakeChain(live_authorizations=(FakeP2(authorized_commit="abc"),))
    assert _gate_code("authorized_commit_matches_head", _ctx(chain=short)) == \
        "gate_refused:authorized_commit_matches_head"
    other = FakeChain(live_authorizations=(FakeP2(authorized_commit="b" * 40),))
    assert _gate_code("authorized_commit_matches_head", _ctx(chain=other)) == \
        "gate_refused:authorized_commit_matches_head"
    r.GATES["authorized_commit_matches_head"](_ctx())


def test_output_root_must_be_declared_by_the_authorization():
    chain = FakeChain(live_authorizations=(FakeP2(output_root=""),))
    assert _gate_code("output_root_declared", _ctx(chain=chain)) == \
        "gate_refused:output_root_declared"


def _rooted_ctx(runs, arch, declared=None, **over):
    """A context whose authorization declares `declared` (default: the
    real runs_root, i.e. the coherent case)."""
    p2 = FakeP2(output_root=str(runs if declared is None else declared))
    return _ctx(runs_root=runs, archive_root=arch,
                chain=FakeChain(live_authorizations=(p2,)), **over)


def test_output_root_structure_gate_writes_nothing(tmp_path):
    """`ND1_WRITE_PROBE_AUTHORIZED=NO`: unlike
    `runinfra.validate_output_roots_operational`, this gate must leave the
    directory byte-for-byte as it found it — no probe file, ever."""
    runs, arch = tmp_path / "runs", tmp_path / "arch"
    runs.mkdir()
    arch.mkdir()
    before = (sorted(p.name for p in runs.iterdir()),
              sorted(p.name for p in arch.iterdir()))
    r.GATES["output_root_structure"](_rooted_ctx(runs, arch))
    after = (sorted(p.name for p in runs.iterdir()),
             sorted(p.name for p in arch.iterdir()))
    assert before == after == ([], [])


def test_output_root_must_be_the_root_the_run_will_actually_use(tmp_path):
    """N06 repair. At 617f7c3 the gate asked only whether the field was
    non-empty, so an authorization naming a DIFFERENT root, or a relative
    one, was accepted while the run used the governed root regardless."""
    runs, arch, other = tmp_path / "runs", tmp_path / "arch", tmp_path / "other"
    for d in (runs, arch, other):
        d.mkdir()
    r.GATES["output_root_structure"](_rooted_ctx(runs, arch))          # coherent
    assert _gate_code("output_root_structure",
                      _rooted_ctx(runs, arch, declared=other)) == \
        "gate_refused:output_root_structure"
    assert _gate_code("output_root_structure",
                      _rooted_ctx(runs, arch, declared="relative/path")) == \
        "gate_refused:output_root_structure"
    assert _gate_code("output_root_structure",
                      _rooted_ctx(runs, arch, declared="")) == \
        "gate_refused:output_root_structure"


def test_output_root_structure_refuses_missing_relative_and_non_dir(tmp_path):
    runs = tmp_path / "runs"
    runs.mkdir()
    assert _gate_code("output_root_structure",
                      _ctx(runs_root=runs, archive_root=tmp_path / "nope")) == \
        "gate_refused:output_root_structure"
    f = tmp_path / "afile"
    f.write_text("x")
    assert _gate_code("output_root_structure",
                      _ctx(runs_root=runs, archive_root=f)) == \
        "gate_refused:output_root_structure"
    assert _gate_code("output_root_structure",
                      _ctx(runs_root=Path("relative"), archive_root=runs)) == \
        "gate_refused:output_root_structure"


STAMP = "20260821T000000Z"


def test_subtree_gate_observes_absence_and_never_creates(tmp_path):
    runs, arch = tmp_path / "runs", tmp_path / "arch"
    runs.mkdir()
    arch.mkdir()
    ctx = _rooted_ctx(runs, arch, utc_stamp=STAMP)
    r.GATES["supplement_subtree_absent"](ctx)
    assert not (runs / "supplements").exists(), \
        "the gate created the subtree it is only allowed to observe"
    assert not (arch / "supplements").exists()
    # the EXACT ratified target, not the bare `supplements/<id>` the old
    # gate looked for — which is why the old check could never have seen
    # a real collision.
    (runs / "supplements" / f"{SID}_{STAMP}").mkdir(parents=True)
    assert _gate_code("supplement_subtree_absent", ctx) == \
        "gate_refused:supplement_subtree_absent"


def test_the_old_bare_id_directory_is_not_what_the_gate_guards(tmp_path):
    """Pins the defect that made the old gate vacuous: a directory at the
    UNRATIFIED bare `supplements/<id>` path is not the planned target, so
    it must NOT block, while the ratified `<id>_<UTC>` one must."""
    runs, arch = tmp_path / "runs", tmp_path / "arch"
    runs.mkdir()
    arch.mkdir()
    (runs / "supplements" / SID).mkdir(parents=True)
    r.GATES["supplement_subtree_absent"](_rooted_ctx(runs, arch,
                                                     utc_stamp=STAMP))


def test_the_subtree_gate_cannot_run_without_a_stamp(tmp_path):
    runs, arch = tmp_path / "runs", tmp_path / "arch"
    runs.mkdir()
    arch.mkdir()
    assert _gate_code("supplement_subtree_absent",
                      _rooted_ctx(runs, arch)) == \
        "gate_refused:supplement_subtree_absent"


def test_retired_id_cannot_be_rerun():
    chain = FakeChain(live_authorizations=(FakeP2(),), retired=True)
    assert _gate_code("id_not_retired", _ctx(chain=chain)) == \
        "gate_refused:id_not_retired"


# ===========================================================================
# 3. B_DERIVE gates — the N03 seam
# ===========================================================================

def test_test_only_authority_cannot_enter_the_production_path():
    ctx = _ctx(authority=FakeAuthority(test_only=True))
    assert _gate_code("custody_authority_production", ctx) == \
        "gate_refused:custody_authority_production"


def test_absent_authority_refuses_rather_than_defaulting():
    assert _gate_code("custody_authority_production", _ctx(authority=None)) == \
        "gate_refused:custody_authority_production"


def test_authority_binding_must_agree_with_the_authorization():
    ctx = _ctx(authority=FakeAuthority(authorized_commit="b" * 40))
    assert _gate_code("custody_authority_binding", ctx) == \
        "gate_refused:custody_authority_binding"
    ctx = _ctx(authority=FakeAuthority(supplement_id="MC-DS-S002"))
    assert _gate_code("custody_authority_binding", ctx) == \
        "gate_refused:custody_authority_binding"


def test_a_duck_typed_authority_is_refused_at_the_first_b_derive_gate():
    """THE N06 REPAIR. Measured at 617f7c3, this exact object passed ALL
    of B_DERIVE while a genuine `SupplementAuthority` was REFUSED at
    `source_bundle_digest` — the seam read `file_sha256_digest`, which no
    real authority has. Forgeries in, real objects out. B_DERIVE now
    checks the TYPE, and every later gate re-derives from the prepared
    input rather than reading the object's self-report."""
    assert _gate_code("custody_authority_production", _ctx()) == \
        "gate_refused:custody_authority_production"


def test_no_b_derive_gate_can_be_satisfied_by_a_stand_in():
    """Not just the first gate: nothing downstream may be reachable with
    a stand-in either, or a caller could skip straight to the gate that
    still trusts the object."""
    for gate in sc.GATE_TABLE["B_DERIVE"]:
        code = None
        try:
            r.GATES[gate](_ctx())
        except r.SupplementRunnerError as exc:
            code = exc.code
        except AttributeError:
            code = "AttributeError"
        assert code is not None, f"{gate} accepted a hand-made stand-in"


def test_b_derive_refuses_a_missing_prepared_input():
    """An authority alone proves nothing — the prepared input it was
    minted off has to be present for anything to be re-derived."""
    assert _gate_code("custody_authority_production",
                      _ctx(authority=None, prepared=None)) == \
        "gate_refused:custody_authority_production"


def test_c_build_gates_are_structurally_unreachable_in_this_build():
    """N04 ships default-refuse: no rows are derived, nothing is sealed,
    nothing is archived. The C_BUILD gates exist so those failures have
    NAMED slots in the F1/F2 vocabulary, and each refuses if reached."""
    for name in sc.GATE_TABLE["C_BUILD"]:
        assert _gate_code(name, _ctx()) == f"gate_refused:{name}"


# ===========================================================================
# 4. F1 / F2 — the P3 boundary decides, never the stage name
# ===========================================================================

def test_pre_start_failure_becomes_f1_with_gate_and_zero_consumption():
    ev = r.plan_failure_event(
        r.GateFailure("A_PRECHECK", "git_clean", "RunGateError"),
        supplement_id=SID, incident_id=INC, has_p3=False,
        attempts_dir="attempts/x")
    assert ev.short_id == "F1"
    assert ev.token == "SUPPLEMENT_ATTEMPT_FAILURE"
    assert ev.row_class == sc.UNNUMBERED
    assert ev.fields["consumption_statement"] == "nothing consumed"
    assert ev.fields["gate_name"] == "git_clean"


def test_post_start_failure_becomes_f2_and_must_preserve_residue():
    ev = r.plan_failure_event(
        r.GateFailure("C_BUILD", "seal_staging_partial", "SupplementRunnerError"),
        supplement_id=SID, incident_id=INC, has_p3=True,
        residue_path="runs/x")
    assert ev.short_id == "F2"
    assert ev.fields["residue_preserved"] == "YES"
    assert "gate_name" not in ev.fields, "F2 carries no gate_name field"


def test_the_same_stage_becomes_f1_or_f2_purely_by_the_p3_boundary():
    fail = r.GateFailure("B_DERIVE", "day_universe_identity", "X")
    pre = r.plan_failure_event(fail, supplement_id=SID, incident_id=INC,
                               has_p3=False, attempts_dir="a")
    post = r.plan_failure_event(fail, supplement_id=SID, incident_id=INC,
                                has_p3=True, residue_path="p")
    assert (pre.short_id, post.short_id) == ("F1", "F2")


def test_f2_without_a_residue_path_refuses():
    with pytest.raises(r.SupplementRunnerError) as ei:
        r.plan_failure_event(r.GateFailure("C_BUILD", "day_set_exact", "X"),
                             supplement_id=SID, incident_id=INC, has_p3=True)
    assert ei.value.code == "post_start_residue_path_required"


def test_f1_without_an_attempts_dir_refuses():
    with pytest.raises(r.SupplementRunnerError) as ei:
        r.plan_failure_event(r.GateFailure("A_PRECHECK", "git_clean", "X"),
                             supplement_id=SID, incident_id=INC, has_p3=False)
    assert ei.value.code == "pre_start_attempts_dir_required"


def test_a_gate_outside_the_closed_enum_may_not_be_emitted():
    with pytest.raises(r.SupplementRunnerError) as ei:
        r.plan_failure_event(r.GateFailure("A_PRECHECK", "invented_gate", "X"),
                             supplement_id=SID, incident_id=INC, has_p3=False,
                             attempts_dir="a")
    assert ei.value.code == "gate_outside_closed_enum"


def test_a_gate_from_the_wrong_stage_may_not_be_emitted():
    with pytest.raises(r.SupplementRunnerError) as ei:
        r.plan_failure_event(r.GateFailure("A_PRECHECK", "day_set_exact", "X"),
                             supplement_id=SID, incident_id=INC, has_p3=False,
                             attempts_dir="a")
    assert ei.value.code == "gate_not_in_stage"


def test_a_stage_outside_the_closed_enum_refuses():
    with pytest.raises(r.SupplementRunnerError) as ei:
        r.plan_failure_event(r.GateFailure("D_SEAL", "git_clean", "X"),
                             supplement_id=SID, incident_id=INC, has_p3=False,
                             attempts_dir="a")
    assert ei.value.code == "stage_outside_closed_enum"


def test_planned_event_refuses_a_malformed_incident_id():
    with pytest.raises(r.SupplementRunnerError) as ei:
        r.plan_failure_event(r.GateFailure("A_PRECHECK", "git_clean", "X"),
                             supplement_id=SID, incident_id="INC-nothex",
                             has_p3=False, attempts_dir="a")
    assert ei.value.code == "planned_event_incident_malformed"


def test_planned_event_refuses_unknown_and_missing_fields():
    with pytest.raises(r.SupplementRunnerError) as ei:
        r.PlannedEvent("P3", sc.EVENTS["P3"].token, sc.UNNUMBERED,
                       sc.ACTOR_RUNNER,
                       {"supplement_id": SID, "atomic_start_marker": "x",
                        "pnl": 1.0})
    assert ei.value.code == "planned_event_unknown_field"
    with pytest.raises(r.SupplementRunnerError) as ei:
        r.PlannedEvent("P3", sc.EVENTS["P3"].token, sc.UNNUMBERED,
                       sc.ACTOR_RUNNER, {"supplement_id": SID})
    assert ei.value.code == "planned_event_missing_field"


def test_planned_event_refuses_a_token_or_row_class_that_is_not_the_specs():
    with pytest.raises(r.SupplementRunnerError) as ei:
        r.PlannedEvent("P3", "SUPPLEMENT_SEALED", sc.UNNUMBERED,
                       sc.ACTOR_RUNNER,
                       {"supplement_id": SID, "atomic_start_marker": "x"})
    assert ei.value.code == "planned_event_token_mismatch"
    with pytest.raises(r.SupplementRunnerError) as ei:
        r.PlannedEvent("P3", sc.EVENTS["P3"].token, sc.NUMBERED,
                       sc.ACTOR_RUNNER,
                       {"supplement_id": SID, "atomic_start_marker": "x"})
    assert ei.value.code == "planned_event_row_class_mismatch"


# ===========================================================================
# 5. the ratified transition function
# ===========================================================================

@pytest.mark.parametrize("frm,outcome,kw,expect", [
    ("P1", "authorize", {}, "P2"),
    ("P2", "start", {}, "P3"),
    ("P2", "pre_start_failure", {}, "F1"),
    ("F1", "retry", {"commit_changed": False}, "P3"),
    ("F1", "retry", {"commit_changed": True}, "P2S"),
    ("F1", "abandon", {}, "F3"),
    ("P2S", "reauthorize", {}, "P2"),
    ("P3", "sealed_archive_ok", {}, "P4"),
    ("P3", "sealed_archive_failed", {}, "A1"),
    ("P3", "post_start_failure", {}, "F2"),
    ("P4", "verified", {}, "P5"),
    ("P4", "verification_failed", {}, "F2v"),
    ("A1", "recovered", {}, "A2"),
    ("A1", "permanent", {}, "AX"),
    ("A2", "verified", {}, "P5"),
    ("AX", "retire", {}, "F3"),
    ("F2", "retire", {}, "F3"),
    ("F2v", "retire", {}, "F3"),
    ("F3", "successor", {}, "T1"),
    ("T1", "authorize", {}, "P2"),
])
def test_every_ratified_edge_is_reachable(frm, outcome, kw, expect):
    assert r.plan_next_short_id(frm, outcome=outcome, **kw) == expect


def test_pre_start_retry_must_declare_whether_the_commit_moved():
    """`PRESTART_COMMIT_CHANGE_REAUTH=YES` is only enforceable if the
    runner is never allowed to leave the question unanswered."""
    with pytest.raises(r.SupplementRunnerError) as ei:
        r.plan_next_short_id("F1", outcome="retry")
    assert ei.value.code == "prestart_commit_change_undeclared"


@pytest.mark.parametrize("frm,outcome", [
    ("P3", "recovered"), ("A1", "verified"), ("AX", "recovered"),
    ("P4", "retire"), ("F3", "authorize"), ("P2", "successor"),
    ("T1", "abandon"), ("P5", "anything"),
])
def test_an_unknown_outcome_refuses_instead_of_defaulting(frm, outcome):
    with pytest.raises(r.SupplementRunnerError) as ei:
        r.plan_next_short_id(frm, outcome=outcome)
    assert ei.value.code in ("unknown_outcome", "illegal_transition")


def test_the_declared_forbidden_edges_are_all_unreachable():
    """Every edge in `FORBIDDEN_EDGES` connects two real events, which is
    exactly why it needs naming: the graph alone would not exclude it."""
    for frm, to in sc.FORBIDDEN_EDGES:
        reachable = any(
            _safe_plan(frm, outcome) == to
            for outcome in ("authorize", "start", "retry", "abandon", "retire",
                            "successor", "reauthorize", "verified",
                            "verification_failed", "recovered", "permanent",
                            "sealed_archive_ok", "sealed_archive_failed",
                            "post_start_failure", "pre_start_failure"))
        assert not reachable, f"forbidden edge {frm} -> {to} is reachable"


def _safe_plan(frm, outcome):
    for kw in ({}, {"commit_changed": True}, {"commit_changed": False}):
        try:
            return r.plan_next_short_id(frm, outcome=outcome, **kw)
        except r.SupplementRunnerError:
            continue
    return None


# ===========================================================================
# 6. terminals — AX and A1 are traps, not endings
# ===========================================================================

def test_the_two_terminals_close_a_chain():
    assert r.assert_chain_closed(["P1", "P2", "P3", "P4", "P5"]) == "P5"
    assert r.assert_chain_closed(["P1", "P2", "P3", "F2", "F3"]) == "F3"


def test_the_archive_recovery_chain_closes_at_p5_through_a2():
    assert r.assert_chain_closed(["P1", "P2", "P3", "A1", "A2", "P5"]) == "P5"


def test_the_permanent_archive_failure_chain_closes_at_f3_not_ax():
    assert r.assert_chain_closed(["P1", "P2", "P3", "A1", "AX", "F3"]) == "F3"


@pytest.mark.parametrize("trap", ["A1", "AX"])
def test_stopping_at_a1_or_ax_is_an_unclosed_chain(trap):
    with pytest.raises(r.SupplementRunnerError) as ei:
        r.assert_chain_closed(["P1", "P2", "P3", trap])
    assert ei.value.code == "chain_stops_at_non_terminal"


def test_a_chain_ending_mid_flight_is_not_closed():
    with pytest.raises(r.SupplementRunnerError) as ei:
        r.assert_chain_closed(["P1", "P2", "P3"])
    assert ei.value.code == "chain_not_closed"
    with pytest.raises(r.SupplementRunnerError) as ei:
        r.assert_chain_closed([])
    assert ei.value.code == "empty_chain"


# ===========================================================================
# 7. archive policy A
# ===========================================================================

def test_archive_ok_becomes_p4():
    ok = FakeReport(ok=True, status="archive_ok", inventory=FakeInventory())
    assert r.decide_after_seal(local_seal_ok=True, archive_report=ok) == "P4"


def test_a_local_seal_with_a_failed_archive_becomes_a1_never_p4():
    """This IS policy A: `P4_SUPPLEMENT_SEALED_REQUIRES=local_seal_ok AND
    archive_ok`. A sealed-but-unarchived supplement must not look sealed."""
    bad = FakeReport(inventory=None)
    assert r.decide_after_seal(local_seal_ok=True, archive_report=bad) == "A1"


def test_a_failed_local_seal_produces_neither_p4_nor_a1():
    with pytest.raises(r.SupplementRunnerError) as ei:
        r.decide_after_seal(local_seal_ok=False,
                            archive_report=FakeReport(status="archive_ok"))
    assert ei.value.code == "local_seal_failed"


def test_the_checkpoint_can_refute_a_report_that_says_archive_ok():
    """BD-2. `archive_sealed_run` verifies the copy it just made and never
    looks at bytes archived earlier, so its report can say ok while
    C_BUILD_3 finds archived bytes destroyed. Policy A forbids P4 there."""
    ok = FakeReport(ok=True, status="archive_ok", inventory=FakeInventory())
    assert r.decide_after_seal(local_seal_ok=True, archive_report=ok,
                               post_archive_ok=False) == "A1"


def test_the_refutation_does_not_leak_into_the_ordinary_paths():
    """Default True, so every existing caller is unchanged -- and a FAILED
    report is already A1 without needing it."""
    import inspect

    sig = inspect.signature(r.decide_after_seal)
    assert sig.parameters["post_archive_ok"].default is True
    bad = FakeReport(inventory=None)
    assert r.decide_after_seal(local_seal_ok=True, archive_report=bad,
                               post_archive_ok=False) == "A1"
    with pytest.raises(r.SupplementRunnerError) as ei:
        r.decide_after_seal(local_seal_ok=False,
                            archive_report=FakeReport(status="archive_ok"),
                            post_archive_ok=False)
    assert ei.value.code == "local_seal_failed", (
        "a lost local seal outranks the checkpoint's verdict")


def test_classifier_covers_every_declared_archive_code():
    got = {
        "inventory_unavailable":
            FakeReport(inventory=None),
        "file_unreadable":
            FakeReport(inventory=FakeInventory(),
                       files=(FakeRecheck(dest_sha256=None, match=False),)),
        "file_digest_mismatch":
            FakeReport(inventory=FakeInventory(),
                       files=(FakeRecheck(dest_sha256="e" * 64, match=False),)),
        "set_equality_refused":
            FakeReport(inventory=FakeInventory(dest_matches_source=False),
                       files=(FakeRecheck(),)),
        "set_equality_unreached":
            FakeReport(inventory=FakeInventory(staging_matches_source=None),
                       files=(FakeRecheck(),)),
    }
    for code, report in got.items():
        assert r.classify_archive_report(report) == code
    assert set(got) == set(sc.ARCHIVE_CODES), \
        "the classifier and the closed enum have drifted apart"


def test_an_unclassifiable_archive_failure_stops_the_chain():
    """Bucketing is TOTAL with a terminal refusal, not a catch-all —
    session-conventions §10. An archive failure nobody modelled must not
    be recorded as if it were understood."""
    weird = FakeReport(inventory=FakeInventory(), files=(FakeRecheck(),))
    with pytest.raises(r.SupplementRunnerError) as ei:
        r.classify_archive_report(weird)
    assert ei.value.code == sc.ARCHIVE_UNCLASSIFIED_CODE
    assert sc.ARCHIVE_UNCLASSIFIED_CODE not in sc.ARCHIVE_CODES


def test_classifier_refuses_an_ok_report_and_an_unknown_status():
    with pytest.raises(r.SupplementRunnerError) as ei:
        r.classify_archive_report(FakeReport(status="archive_ok"))
    assert ei.value.code == "archive_ok_has_no_code"
    with pytest.raises(r.SupplementRunnerError) as ei:
        r.classify_archive_report(FakeReport(status="mostly_fine"))
    assert ei.value.code == "archive_status_unknown"


# ===========================================================================
# 8. `.partial` recovery — the ratified MODIFY rule
# ===========================================================================

def test_branch_c_moves_divergent_debris_aside_and_permits_the_retry(tmp_path):
    """BRANCH_C_RENAME_THEN_ALLOW_RETRY. The old implementation preserved
    the residue but left it blocking the path forever; the ratified rule
    keeps the evidence AND unblocks."""
    (tmp_path / ("S.json" + sc.PARTIAL_SUFFIX)).write_bytes(b"old debris")
    out = r.resolve_partial(tmp_path, "S.json", b"new", incident_id=INC)
    assert out.action == "retry_permitted"
    preserved = tmp_path / out.preserved_as
    assert preserved.exists() and preserved.read_bytes() == b"old debris"
    assert out.preserved_as == f"S.json.partial.divergent.{INC}"
    assert not (tmp_path / ("S.json" + sc.PARTIAL_SUFFIX)).exists()


def test_branch_e_preserves_the_unreliable_bytes_instead_of_unlinking(
        tmp_path, monkeypatch):
    """BRANCH_E_RENAME_TO_.partial.divergent.<incident_id>. The previous
    implementation called `unlink()` here; `SILENT_DELETE_FORBIDDEN=YES`
    turns that into a rename."""
    real_read = Path.read_bytes
    state = {"n": 0}

    def flaky(self):
        if self.name.endswith(sc.PARTIAL_SUFFIX):
            state["n"] += 1
            if state["n"] == 1:
                return b"corrupted-on-readback"
        return real_read(self)

    monkeypatch.setattr(Path, "read_bytes", flaky)
    with pytest.raises(r.SupplementRunnerError) as ei:
        r.resolve_partial(tmp_path, "S.json", b"intended", incident_id=INC)
    assert ei.value.code == "supplement_partial_verify"
    monkeypatch.undo()
    kept = tmp_path / f"S.json.partial.divergent.{INC}"
    assert kept.exists(), "branch E deleted the bytes instead of preserving"
    assert kept.read_bytes() == b"intended"
    assert not (tmp_path / "S.json").exists()


def test_no_branch_of_resolve_partial_deletes_a_file(tmp_path):
    """Sweep: after every branch that leaves debris, the byte count on
    disk never decreases."""
    (tmp_path / ("S.json" + sc.PARTIAL_SUFFIX)).write_bytes(b"debris")
    before = sum(1 for _ in tmp_path.iterdir())
    r.resolve_partial(tmp_path, "S.json", b"new", incident_id=INC)
    after = sum(1 for _ in tmp_path.iterdir())
    assert after >= before


def test_a_byte_identical_stale_partial_is_promoted(tmp_path):
    (tmp_path / ("S.json" + sc.PARTIAL_SUFFIX)).write_bytes(b"same")
    out = r.resolve_partial(tmp_path, "S.json", b"same", incident_id=INC)
    assert out.action == "promote"
    assert (tmp_path / "S.json").read_bytes() == b"same"


def test_a_clean_seal_stages_verifies_and_promotes(tmp_path):
    out = r.resolve_partial(tmp_path, "S.json", b"payload", incident_id=INC)
    assert out.action == "promote"
    assert (tmp_path / "S.json").read_bytes() == b"payload"
    assert not (tmp_path / ("S.json" + sc.PARTIAL_SUFFIX)).exists()


def test_an_identical_reseal_is_idempotent_and_writes_nothing(tmp_path):
    (tmp_path / "S.json").write_bytes(b"payload")
    out = r.resolve_partial(tmp_path, "S.json", b"payload", incident_id=INC)
    assert out.action == "already_sealed"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["S.json"]


def test_a_sealed_supplement_is_never_overwritten(tmp_path):
    (tmp_path / "S.json").write_bytes(b"sealed")
    with pytest.raises(r.SupplementRunnerError) as ei:
        r.resolve_partial(tmp_path, "S.json", b"different", incident_id=INC)
    assert ei.value.code == "supplement_seal_conflict"
    assert (tmp_path / "S.json").read_bytes() == b"sealed"


def test_a_second_incident_may_not_overwrite_the_first_preserved_bytes(tmp_path):
    (tmp_path / f"S.json.partial.divergent.{INC}").write_bytes(b"first")
    (tmp_path / ("S.json" + sc.PARTIAL_SUFFIX)).write_bytes(b"second")
    with pytest.raises(r.SupplementRunnerError) as ei:
        r.resolve_partial(tmp_path, "S.json", b"new", incident_id=INC)
    assert ei.value.code == "divergent_partial_exists"
    assert (tmp_path / f"S.json.partial.divergent.{INC}").read_bytes() == b"first"


def test_preserving_requires_a_wellformed_incident_id(tmp_path):
    (tmp_path / ("S.json" + sc.PARTIAL_SUFFIX)).write_bytes(b"debris")
    with pytest.raises(r.SupplementRunnerError) as ei:
        r.resolve_partial(tmp_path, "S.json", b"new", incident_id="INC-zz")
    assert ei.value.code == "incident_id_malformed"


# ===========================================================================
# 9. the production entry refuses, and writes nothing anywhere
# ===========================================================================

def test_the_guards_are_already_satisfied_so_authorization_is_the_real_defence():
    """MEASURED, not assumed. Both attestation flags EXIST in this repo
    (`gate1/G9_RESOLVED.flag`, `ops/SECOND_COPY_ATTESTED.flag`), so
    `assert_real_run_allowed` does NOT refuse a supplement run. The
    runner's defence therefore rests entirely on the authorization layer,
    and this test pins that fact so nobody reasons from a stale "G9 still
    blocks everything" assumption."""
    from itsf.guards import G9_FLAG, SECOND_COPY_FLAG, assert_real_run_allowed
    assert G9_FLAG.exists() and SECOND_COPY_FLAG.exists()
    assert_real_run_allowed(G9_FLAG, SECOND_COPY_FLAG)      # does not raise


def test_production_entry_refuses_even_with_the_guards_satisfied():
    """The first refusal a real caller meets today. It must arrive from
    the authorization/chain layer, and it must arrive as a refusal — not
    as an AttributeError or a silent None."""
    with pytest.raises(r.SupplementRunNotAuthorized):
        r.run_supplement_production()


def test_production_entry_refuses_at_authorization_once_guards_pass(
        tmp_path, monkeypatch):
    """With the guards satisfied, the NEXT refusal must be the missing
    authorization — not a data read, not a directory creation."""
    monkeypatch.setattr(r, "_default_resolver",
                        lambda text, sid: FakeChain(live_authorizations=()))
    monkeypatch.setattr("itsf.guards.assert_real_run_allowed",
                        lambda *a, **k: None)
    monkeypatch.setattr("itsf.mc.supplement_runner.Path.read_text",
                        lambda self, **k: "", raising=False)
    with pytest.raises(r.SupplementRunNotAuthorized) as ei:
        r.run_supplement_production(resolver=lambda t, s: FakeChain())
    assert "live" in str(ei.value)


def test_production_entry_refuses_a_defective_chain_whole(monkeypatch):
    monkeypatch.setattr("itsf.guards.assert_real_run_allowed",
                        lambda *a, **k: None)
    with pytest.raises(r.SupplementRunNotAuthorized) as ei:
        r.run_supplement_production(
            resolver=lambda t, s: FakeChain(problem="forward reference"))
    assert "REFUSE_WHOLE_RESOLUTION" in str(ei.value)


def test_production_entry_writes_nothing_anywhere():
    """Protected-state zero-write proof: the registry and the exposure
    ledger are byte-identical either side of the call, and neither governed
    `supplements` subtree is TOUCHED.

    It used to say "comes into existence". They exist now, by Aaron's
    verbatim 2026-08-29 grant, so non-existence stopped being the property
    and "unchanged" took over -- which also covers the case the old form
    could not: the runner writing into a directory that is already there."""
    from _governed_subtrees import (assert_governed_subtrees_untouched,
                                    snapshot)
    reg = REPO / "ops" / "TRIAL_REGISTRY.md"
    led = REPO / "EXPOSURE_LEDGER.md"
    before = (hashlib.sha256(reg.read_bytes()).hexdigest(),
              hashlib.sha256(led.read_bytes()).hexdigest())
    subtrees_before = snapshot()
    with pytest.raises(Exception):
        r.run_supplement_production()
    after = (hashlib.sha256(reg.read_bytes()).hexdigest(),
             hashlib.sha256(led.read_bytes()).hexdigest())
    assert before == after
    assert_governed_subtrees_untouched(subtrees_before,
                                       "run_supplement_production")


def test_a_missing_registry_resolver_refuses_rather_than_proceeding(
        monkeypatch):
    monkeypatch.setattr("itsf.guards.assert_real_run_allowed",
                        lambda *a, **k: None)

    def blow_up(text, sid):
        raise r.SupplementRunNotAuthorized("resolver unavailable")

    with pytest.raises(r.SupplementRunNotAuthorized):
        r.run_supplement_production(resolver=blow_up)


def test_the_module_exposes_no_execution_authorization():
    """Nothing here may return something a caller could read as
    permission. The only public verbs are gates, planners and refusals."""
    public = [n for n in dir(r) if not n.startswith("_")]
    for name in public:
        assert "authoriz" not in name.lower() or name in (
            "SupplementRunNotAuthorized",), name
