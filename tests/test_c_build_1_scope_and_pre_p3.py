"""C_BUILD_1's archive scope, and the pre-P3 read that now precedes it.

WHAT THE N09 v2 RUN PROVED, at the cost of one authorization. C_BUILD_1
asserts that the supplement byte set is unchanged across the gates AND
empty. The runs side was asked about the run's own leaf; the archive side
was asked about `planned.archive_parent` -- the whole governed archive
tree. That tree is empty exactly once, for the first supplement ever
archived. MC-DS-S001's sealed artifact lives there permanently, so from the
moment it landed, EVERY successor run was going to refuse at C_BUILD_1.
MC-DS-S002 did: it spent its P3, created its directory, and then met
`c_build_1_not_empty` over a sibling's bytes.

TWO REPAIRS, AND THEY ARE DIFFERENT CLAIMS.

  (A) SCOPE. The archive side now asks about `planned.archive_target`.
      A historical sibling leaf is not this run's residue.

  (B) TIMING. The emptiness half is decided by a PURE READ before the P3
      append, so the same refusal costs nothing instead of an
      authorization. It does NOT replace C_BUILD_1, which still runs and
      still refuses -- and still carries the before/after half a pre-run
      read cannot have.

Nothing here touches the real governed trees: every case is a tmp_path.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tests"))

from itsf.mc import day_strata_pipeline as dsp      # noqa: E402
from itsf.mc import day_strata_rows as dsr          # noqa: E402
from itsf.mc import registry_boundary as rb         # noqa: E402
from itsf.mc import supplement_chain as ch          # noqa: E402
from itsf.mc import supplement_runner as sr         # noqa: E402

SID = "MC-DS-S003"
STAMP = "20260906T120000Z"
SEALED = "DAY_STRATA_SUPPLEMENT.json"


def roots(tmp_path):
    """The two governed roots, with MC-DS-S001-shaped history already in
    the archive -- which is the state that broke the real run."""
    runs = tmp_path / "itsf-runs"
    archive = tmp_path / "itsf-runs-archive"
    for r in (runs, archive):
        (r / "supplements").mkdir(parents=True)
    sibling = archive / "supplements" / "MC-DS-S001_20260905T170810Z"
    sibling.mkdir()
    (sibling / SEALED).write_bytes(b'{"sealed": "sibling"}')
    return runs, archive


def planned_for(tmp_path):
    runs, archive = roots(tmp_path)
    return sr.plan_supplement_paths(runs_root=runs, archive_root=archive,
                                    supplement_id=SID, utc_stamp=STAMP)


def put_residue(leaf: Path, body=b'{"residue": true}'):
    leaf.mkdir(parents=True, exist_ok=True)
    (leaf / SEALED).write_bytes(body)


# ===========================================================================
# A — the planner already had the field; no second path construction
# ===========================================================================

def test_the_planner_already_names_this_runs_archive_leaf(tmp_path):
    """The repair needed a path the planner had all along."""
    p = planned_for(tmp_path)
    assert p.archive_target.name == p.runs_target.name == f"{SID}_{STAMP}"
    assert p.archive_target.parent == p.archive_parent
    assert p.archive_target != p.archive_parent


def test_the_chain_passes_the_leaf_to_c_build_1_and_the_parent_to_archiving():
    """Both facts in one place, because the bug was using one where the
    other belonged. Read off the source: the behavioural halves are below,
    but a future edit that swaps them back must fail HERE, by name."""
    import inspect
    body = inspect.getsource(ch.run_supplement_chain)
    assert "archive_root=planned.archive_target)" in body
    assert "archive_root=planned.archive_parent" not in body
    # moment 3 genuinely wants the parent, and must keep it
    assert "ARCHIVE_SEAM(out_dir, planned.archive_parent)" in body


# ===========================================================================
# A — the three scope invariants, executed
# ===========================================================================

def _c_build_1(planned):
    """C_BUILD_1's own assertions over the two roots the chain passes,
    with no rows derived and no product built."""
    for label, root in (("runs_leaf", planned.runs_target),
                        ("archive_leaf", planned.archive_target)):
        snap = dsp.supplement_bytes_snapshot(root)
        dsp._assert_c_build_1(snap, snap, label)


def test_a_historical_archive_sibling_does_not_refuse_this_run(tmp_path):
    """INVARIANT 3, and the whole point of the repair."""
    planned = planned_for(tmp_path)
    assert dsp.supplement_bytes_snapshot(planned.archive_parent), \
        "the fixture must actually carry a sibling, or this proves nothing"
    _c_build_1(planned)                      # does not raise
    dsp.assert_current_run_namespaces_are_clear(
        runs_leaf=planned.runs_target, archive_leaf=planned.archive_target)


def test_residue_in_this_runs_archive_leaf_refuses(tmp_path):
    """INVARIANT 2."""
    planned = planned_for(tmp_path)
    put_residue(planned.archive_target)
    with pytest.raises(dsr.DayStrataRowsError) as ei:
        _c_build_1(planned)
    assert ei.value.code == "c_build_1_not_empty"


def test_residue_in_this_runs_runs_leaf_refuses(tmp_path):
    """INVARIANT 1."""
    planned = planned_for(tmp_path)
    put_residue(planned.runs_target)
    with pytest.raises(dsr.DayStrataRowsError) as ei:
        _c_build_1(planned)
    assert ei.value.code == "c_build_1_not_empty"


def test_the_no_mutation_half_survives_the_repair(tmp_path):
    """INVARIANT 4. Narrowing the scope must not have cost C_BUILD_1 its
    other claim: bytes appearing DURING the checkpoint are still refused,
    and under their own code."""
    planned = planned_for(tmp_path)
    before = dsp.supplement_bytes_snapshot(planned.runs_target)
    put_residue(planned.runs_target)
    after = dsp.supplement_bytes_snapshot(planned.runs_target)
    assert before != after
    with pytest.raises(dsr.DayStrataRowsError) as ei:
        dsp._assert_c_build_1(before, after, "runs_leaf")
    assert ei.value.code == "c_build_1_bytes_moved"


# ===========================================================================
# B — the pre-P3 read, and that it is the SAME predicate
# ===========================================================================

def test_pre_p3_and_c_build_1_share_one_emptiness_predicate():
    """Not "they agree today" -- they call the same function. Proved by
    breaking it once: if `_refuse_if_not_empty` stops raising, BOTH stop
    refusing. Two implementations could not both go quiet."""
    import inspect
    assert "_refuse_if_not_empty" in inspect.getsource(
        dsp.assert_current_run_namespaces_are_clear)
    assert "_refuse_if_not_empty" in inspect.getsource(dsp._assert_c_build_1)

    with mock.patch.object(dsp, "_refuse_if_not_empty", lambda *a: None):
        dsp.assert_current_run_namespaces_are_clear(
            runs_leaf=None, archive_leaf=None)
        dsp._assert_c_build_1((("x", 1, "d"),), (("x", 1, "d"),), "l")


def test_pre_p3_catches_the_same_residue_c_build_1_would(tmp_path):
    """REGRESSION 4: the early check and the late one refuse the same
    thing, with the same code."""
    for leaf_of in (lambda p: p.runs_target, lambda p: p.archive_target):
        planned = planned_for(tmp_path / str(id(leaf_of)))
        put_residue(leaf_of(planned))
        with pytest.raises(dsr.DayStrataRowsError) as early:
            dsp.assert_current_run_namespaces_are_clear(
                runs_leaf=planned.runs_target,
                archive_leaf=planned.archive_target)
        with pytest.raises(dsr.DayStrataRowsError) as late:
            _c_build_1(planned)
        assert early.value.code == late.value.code == "c_build_1_not_empty"


def test_the_pre_p3_check_precedes_the_p3_append_in_the_chain():
    """Order is the property. A read after the append would still be a
    read -- and would still have burned the authorization."""
    import inspect
    lines = inspect.getsource(ch.run_supplement_gate_first).splitlines()
    i_check = next(i for i, l in enumerate(lines)
                   if "assert_current_run_namespaces_are_clear" in l)
    i_p3 = next(i for i, l in enumerate(lines)
                if l.strip() == "append_run_started()")
    i_md = next(i for i, l in enumerate(lines)
                if "make_run_directory(" in l)
    assert i_check < i_p3 < i_md


def _drive(planned, *, append, make_dir, authority=None):
    """Run the gate-first chain with every gate and the authority stubbed,
    so the only thing under test is the pre-P3 ordering."""
    from itsf.mc import supplement_authority as _sa
    ctx = sr.GateContext(supplement_id=SID, head_commit="a" * 40,
                         registry_text="", runs_root=None, archive_root=None)
    with mock.patch.object(sr, "GATES",
                           {k: (lambda c: None) for k in sr.GATES}), \
            mock.patch.object(_sa, "derive_supplement_authority",
                              return_value=authority
                              if authority is not None else object()):
        return ch.run_supplement_gate_first(
            ctx, planned=planned, prepared=object(), universe=object(),
            vol_method=object(), flag_by_date={},
            event_na_mapping="none", incident_id="INC-0123456789ab",
            archive_before=(), archive_after_reader=tuple,
            make_run_directory=make_dir, append_run_started=append)


def test_pre_p3_residue_appends_no_p3_and_creates_no_directory(tmp_path):
    """REGRESSIONS 5 and 6, executed rather than read off the source.

    The archive leaf is the one seeded, because that is the case the real
    run met and the case the old code could not even see."""
    planned = planned_for(tmp_path)
    put_residue(planned.archive_target)
    appended, made = [], []
    with pytest.raises(ch.ChainRefusal) as ei:
        _drive(planned, append=lambda: appended.append("P3"),
               make_dir=lambda t: made.append(t))
    assert ei.value.code == "c_build_1_not_empty"
    assert appended == [], "a P3 was appended despite the pre-P3 refusal"
    assert made == [], "a run directory was created despite the refusal"
    assert not planned.runs_target.exists()


def test_the_chain_hands_c_build_1_this_runs_archive_leaf(tmp_path):
    """The scope repair, EXECUTED rather than read off the source.

    A mutation probe found the source-level assertion above was the only
    thing catching a revert to `archive_parent`; every behavioural case
    called C_BUILD_1 directly with a leaf and so could not see which path
    the chain chooses. This intercepts `run_c_build` and reads the argument
    it was actually given."""
    planned = planned_for(tmp_path)
    seen = {}

    def capture(**kw):
        seen.update(kw)
        raise dsr.DayStrataRowsError("stop_here", "captured")

    stub = mock.Mock(expected_day_set=frozenset())
    with mock.patch.object(ch._dsp, "run_c_build", capture):
        with pytest.raises(ch.ChainRefusal):
            _drive(planned, append=lambda: None,
                   make_dir=lambda t: t.mkdir(parents=True), authority=stub)
    assert seen["archive_root"] == planned.archive_target
    assert seen["archive_root"] != planned.archive_parent
    assert seen["runs_root"] == planned.runs_target


def test_a_sibling_only_archive_does_not_stop_the_run_before_p3(tmp_path):
    """The mirror image, and the one that would have been missed by
    testing only the refusal: with ONLY a historical sibling present, the
    chain must reach the P3 append."""
    planned = planned_for(tmp_path)
    appended, made = [], []
    with pytest.raises(Exception):
        # It proceeds past P3 and dies later on the stubbed authority; what
        # matters is that it GOT past the pre-P3 check.
        _drive(planned, append=lambda: appended.append("P3"),
               make_dir=lambda t: made.append(t) or t.mkdir(parents=True))
    assert appended == ["P3"], "the sibling stopped a run it must not stop"


# ===========================================================================
# C — the planner can now express a gateless post-start failure
# ===========================================================================

RESIDUE = r"C:\somewhere\MC-DS-S003_20260906T120000Z"
INC = "INC-0123456789ab"


def test_the_real_failure_can_now_be_planned_as_f2():
    """REGRESSION 11. `c_build_1_not_empty` is a checkpoint side-effect
    code, not a gate; F2 carries no gate_name, so planning it must not
    require one."""
    ev = sr.plan_failure_event(
        sr.GateFailure(stage="C_BUILD", gate_name="c_build_1_not_empty",
                       error_class="DayStrataRowsError"),
        supplement_id=SID, incident_id=INC, has_p3=True,
        residue_path=RESIDUE)
    assert ev.short_id == "F2"
    assert ev.fields["stage"] == "C_BUILD"
    assert ev.fields["error_class"] == "DayStrataRowsError"
    assert ev.fields["residue_path"] == RESIDUE
    assert ev.fields["residue_preserved"] == "YES"
    assert "gate_name" not in ev.fields


def test_c_build_1_not_empty_was_not_smuggled_into_the_gate_enum():
    """The repair the ruling forbade. Making a checkpoint assertion look
    like a gate would have let it be emitted in an F1 row."""
    from itsf.mc import supplement_contract as sc
    assert "c_build_1_not_empty" not in sc.GATE_NAME_ENUM
    for stage in sc.STAGE_ENUM:
        assert "c_build_1_not_empty" not in sc.GATE_TABLE[stage]


def test_f1_still_binds_the_closed_gate_enum():
    """REGRESSIONS 12 and 13. F1 DOES carry gate_name, so nothing there
    was loosened -- three ways."""
    for gate, code in (("invented_gate", "gate_outside_closed_enum"),
                       ("c_build_1_not_empty", "gate_outside_closed_enum"),
                       ("day_set_exact", "gate_not_in_stage")):
        with pytest.raises(sr.SupplementRunnerError) as ei:
            sr.plan_failure_event(
                sr.GateFailure(stage="A_PRECHECK", gate_name=gate,
                               error_class="X"),
                supplement_id=SID, incident_id=INC, has_p3=False,
                attempts_dir="a")
        assert ei.value.code == code, (gate, ei.value.code)


def test_the_stage_enum_still_binds_both_sides():
    """The half that was NOT moved: an invented stage refuses whether or
    not a P3 exists."""
    for has_p3, extra in ((False, {"attempts_dir": "a"}),
                          (True, {"residue_path": RESIDUE})):
        with pytest.raises(sr.SupplementRunnerError) as ei:
            sr.plan_failure_event(
                sr.GateFailure(stage="D_SEAL", gate_name="git_clean",
                               error_class="X"),
                supplement_id=SID, incident_id=INC, has_p3=has_p3, **extra)
        assert ei.value.code == "stage_outside_closed_enum", has_p3


def test_an_f2_still_needs_its_residue_path():
    """RESIDUE=NEVER_DELETED: the field the F2 row actually carries is
    still required, so nothing was traded away for the gate relaxation."""
    with pytest.raises(sr.SupplementRunnerError) as ei:
        sr.plan_failure_event(
            sr.GateFailure(stage="C_BUILD", gate_name="c_build_1_not_empty",
                           error_class="DayStrataRowsError"),
            supplement_id=SID, incident_id=INC, has_p3=True)
    assert ei.value.code == "post_start_residue_path_required"


# ===========================================================================
# The real trees, untouched
# ===========================================================================

def test_no_case_here_names_a_governed_path():
    """Every fixture above is a tmp_path. Stated as a test because the one
    thing worse than a failing repair is a passing one that wrote into the
    real evidence.

    AST over this module's own string constants, compared against the
    ruled roots LOOKED UP at runtime. The first version grepped for the
    roots' spelling as a literal and found its own assertion -- a guard
    that could only ever fail, which is the mirror of a guard that could
    only ever pass."""
    import ast
    from itsf import contracts as c

    governed = tuple(str(Path(p)).lower()
                     for p in (c.RULED_RUNS_ROOT, c.RULED_ARCHIVE_ROOT))
    assert all(governed), "the ruled roots did not resolve"
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    named = [n.value for n in ast.walk(tree)
             if isinstance(n, ast.Constant) and isinstance(n.value, str)
             and any(g in n.value.lower() for g in governed)]
    assert named == [], named
