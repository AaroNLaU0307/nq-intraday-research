"""The chain: three moments composed, and where each one can stop it.

DRIVEN AS REAL AS IT CAN BE. The authority and the prepared input are the
production-shaped ones from the provenance battery, the supplement is built
by the real factory and sealed by the real production sealer into a real
temporary directory. Only two things are substituted, and each because there
is no honest alternative: the two S0 universe builders (there is no dataset
here to build a universe from) and the archive step (it is the one call that
copies a directory tree, and the codes under test are about what a report
SAYS, not about copying).

WHAT THE STRUCTURAL TESTS ARE FOR. The chain must select gates by MOMENT.
Selecting by stage always reaches `archive_policy_a`, which is ruled to
Router B and always refuses -- a chain built that way could never complete,
and the failure would look like a run problem rather than a wiring one. That
is asserted against the source, and the partition is asserted to be exact.
"""

import ast
import hashlib
import unittest
from pathlib import Path
from unittest import mock

import pytest

from itsf.mc import day_strata_pipeline as dsp
from itsf.mc import day_strata_supplement as dss
from itsf.mc import supplement_chain as chain
from itsf.mc import supplement_contract as sc
from itsf.mc import supplement_production as sp
from itsf.mc import supplement_runner as sr

import test_day_strata_pipeline as fxp
import test_mc_supplement_provenance_battery as fx

from _pytest.fixtures import FixtureFunctionDefinition as _FixtureDef

_REEXPORTED = []
for _name in dir(fx):
    _obj = getattr(fx, _name)
    if isinstance(_obj, _FixtureDef):
        globals()[_name] = _obj
        _REEXPORTED.append(_name)
assert "prod" in _REEXPORTED and "authority" in _REEXPORTED, (
    "the fixture re-export found %r; it is matching nothing" % (_REEXPORTED,))

MODULE = Path(chain.__file__)


class _Report:
    """Only what `classify_archive_report` and Router B actually read."""

    def __init__(self, status, inventory=None, files=()):
        self.status = status
        self.inventory = inventory
        self.files = files


def _base_ctx():
    return sr.GateContext(supplement_id=fx.SID, head_commit="0" * 40,
                          registry_text="", runs_root=None, archive_root=None)


_STAMP = "20260902T120000Z"


def _plan(tmp_path, *, make=True):
    """The ratified planner's paths. Since the H1 repair the chain takes
    these instead of three free paths, so a test cannot seal into one tree
    and archive another either."""
    runs_root, archive_root = tmp_path / "runs", tmp_path / "archive"
    runs_root.mkdir(exist_ok=True)
    archive_root.mkdir(exist_ok=True)
    planned = sr.plan_supplement_paths(
        runs_root=runs_root, archive_root=archive_root,
        supplement_id=fx.SID, utc_stamp=_STAMP)
    if make:
        planned.runs_target.mkdir(parents=True, exist_ok=True)
    return planned


def _drive(authority, prod, tmp_path, *, report=None, before=(), after=None,
           days=None, planned=None):
    """One chain run, with the two unavoidable substitutions in place."""
    days = days if days is not None else sorted(authority.expected_day_set)
    planned = planned or _plan(tmp_path)
    seam = mock.Mock(return_value=report or _Report("archive_ok"))
    with fxp._patched({d: "T1" for d in days}, {d: "none" for d in days}),             mock.patch.object(chain, "ARCHIVE_SEAM", seam):
        return chain.run_supplement_chain(
            _base_ctx(), planned=planned, authority=authority, prepared=prod,
            universe=object(), vol_method="vol20", flag_by_date={},
            event_na_mapping="none", incident_id=fx.INC,
            archive_before=before,
            archive_after_reader=lambda: (after if after is not None
                                          else before))


# ===========================================================================
# gates_at - the inverse CHECKPOINT_OF never had
# ===========================================================================

class TestGatesAt(unittest.TestCase):

    def test_the_three_moments_partition_C_BUILD_exactly(self):
        """Every gate in exactly one moment, and no gate invented."""
        seen = [g for c in sc.CHECKPOINT_ORDER for g in sc.gates_at(c)]
        self.assertEqual(sorted(sc.GATE_TABLE["C_BUILD"]), sorted(seen))
        self.assertEqual(len(seen), len(set(seen)), "a gate is in two moments")

    def test_order_comes_from_the_gate_table_not_the_checkpoint_map(self):
        table = list(sc.GATE_TABLE["C_BUILD"])
        for c in sc.CHECKPOINT_ORDER:
            got = list(sc.gates_at(c))
            self.assertEqual(sorted(got, key=table.index), got, c)

    def test_an_unknown_checkpoint_is_a_refusal_not_an_empty_tuple(self):
        """An empty tuple would run no gates and look exactly like a moment
        that legitimately has none."""
        with self.assertRaises(sc.SupplementGrammarError):
            sc.gates_at("C_BUILD_4")

    def test_the_third_moment_is_the_router_b_gate_alone(self):
        self.assertEqual(("archive_policy_a",),
                         sc.gates_at(sc.CHECKPOINT_C_BUILD_3))


class TestItSelectsByMomentNotByStage(unittest.TestCase):

    def test_the_chain_never_calls_run_stage_gates(self):
        """It always reaches `archive_policy_a`, which always refuses."""
        tree = ast.parse(MODULE.read_text(encoding="utf-8"))
        called = {getattr(n.func, "attr", None) or getattr(n.func, "id", None)
                  for n in ast.walk(tree) if isinstance(n, ast.Call)}
        self.assertNotIn("run_stage_gates", called)

    def test_and_that_gate_would_indeed_have_stopped_it(self):
        """The other half: proof the avoidance is load-bearing rather than
        stylistic."""
        ctx = sr.GateContext(supplement_id=fx.SID, head_commit="0" * 40,
                             registry_text="", runs_root=None,
                             archive_root=None,
                             c_build_outcome=dsp.CBuildOutcome((), None, None))
        with self.assertRaises(sr.SupplementRunnerError):
            sr.run_stage_gates("C_BUILD", ctx)


# ===========================================================================
# The chain itself
# ===========================================================================

def test_the_clean_chain_reaches_P4(prod, authority, tmp_path):
    planned = _plan(tmp_path)
    result = _drive(authority, prod, tmp_path, planned=planned)
    assert result.verdict == "P4"
    assert result.sealed is True
    assert result.archive_status == "archive_ok"
    assert len(result.rows) == len(authority.expected_day_set)
    assert (planned.runs_target / dss.SUPPLEMENT_FILENAME).is_file()


def test_a_failed_archive_reaches_A1_not_P4(prod, authority, tmp_path):
    """Ratified Policy A: a local seal that succeeded while the archive
    failed does NOT become P4."""
    report = _Report("archive_failed", inventory=None)
    result = _drive(authority, prod, tmp_path, report=report)
    assert result.verdict == "A1"
    assert result.sealed is False


def test_a_C_BUILD_1_refusal_stops_before_anything_is_sealed(prod, authority,
                                                             tmp_path):
    """The point of the first moment being BEFORE the first write."""
    planned = _plan(tmp_path)
    days = sorted(authority.expected_day_set)
    with pytest.raises(chain.ChainRefusal) as caught:
        _drive(authority, prod, tmp_path, days=days[:-1], planned=planned)
    assert caught.value.moment == "C_BUILD_1"
    assert list(planned.runs_target.iterdir()) == [],         "it sealed despite refusing"


def test_a_lost_local_seal_is_refused_by_router_b(prod, authority, tmp_path):
    """`local_seal_absent` means the seal did not survive, which is exactly
    `local_seal_ok=False` -- and Router B already answers that."""
    planned = _plan(tmp_path)

    def _vanish(runs_dir, archive_parent):
        (planned.runs_target / dss.SUPPLEMENT_FILENAME).unlink()
        return _Report("archive_ok")

    days = sorted(authority.expected_day_set)
    with fxp._patched({d: "T1" for d in days}, {d: "none" for d in days}),             mock.patch.object(chain, "ARCHIVE_SEAM", _vanish):
        with pytest.raises(chain.ChainRefusal) as caught:
            chain.run_supplement_chain(
                _base_ctx(), planned=planned, authority=authority,
                prepared=prod, universe=object(), vol_method="vol20",
                flag_by_date={}, event_na_mapping="none",
                incident_id=fx.INC, archive_before=(),
                archive_after_reader=tuple)
    assert caught.value.moment == "C_BUILD_3"
    assert "nothing was sealed" in str(caught.value)


def test_archived_bytes_deleted_has_no_ruled_terminal_and_refuses(
        prod, authority, tmp_path):
    """BD-5 RETRACTED 2026-09-02. This used to assert A1, on an elimination
    the reviewing seat refuted and that reproduces: P3's ratified successors
    are P4, A1, F2 AND CR1, so the space was never closed; an A1 row needs an
    `archive_code` and this is not one of the five; and A2, A1's only exit,
    asserts things about THIS run's copy. It refuses by name again."""
    before = (("old.json", 3, "a" * 64),)
    with pytest.raises(chain.ChainRefusal) as caught:
        _drive(authority, prod, tmp_path, before=before, after=())
    assert caught.value.moment == "C_BUILD_3"
    assert caught.value.code == "archived_bytes_deleted"
    assert "no ratified terminal covers that" in str(caught.value)


def test_the_successor_set_that_retracted_BD_5(prod, authority, tmp_path):
    """The measured fact, pinned here as well as at the router: the argument
    must not be reconstructible from memory."""
    successors = sorted(e.short_id for e in sc.EVENTS.values()
                        if "P3" in getattr(e, "predecessors", ()))
    assert successors == ["A1", "CR1", "F2", "P4"], successors
    assert "archived_bytes_deleted" not in sc.ARCHIVE_CODES


def test_an_unknown_C_BUILD_3_code_still_refuses(prod, authority, tmp_path):
    """BD-5 settled ONE code. Fail-closed is still the rule for the next
    one, exactly as BD-1 requires of seal codes."""
    broken = dsp.CBuildOutcome(
        (), None, dsp.CBuildFailure("archive_policy_a", "some_future_code",
                                    "stubbed"))
    with mock.patch.object(dsp, "run_c_build_3", return_value=broken):
        with pytest.raises(chain.ChainRefusal) as caught:
            _drive(authority, prod, tmp_path)
    assert caught.value.code == "some_future_code"
    assert "no ruled verdict covers" in str(caught.value)


def test_a_router_b_seal_code_never_reaches_the_gates(prod, authority,
                                                      tmp_path):
    """BD-1's two codes get no gate, so asking the gates would report green
    over a seal that did not happen."""
    exc = sp.SupplementProductionError("production_payload_drift", "stubbed")
    planned = _plan(tmp_path)
    days = sorted(authority.expected_day_set)
    with fxp._patched({d: "T1" for d in days}, {d: "none" for d in days}),             mock.patch.object(sp, "seal_supplement_production",
                              side_effect=exc),             mock.patch.object(sr, "GATES", dict(sr.GATES)) as gates:
        gates["seal_staging_partial"] = mock.Mock(
            side_effect=AssertionError("the gate was consulted"))
        with pytest.raises(chain.ChainRefusal) as caught:
            chain.run_supplement_chain(
                _base_ctx(), planned=planned, authority=authority,
                prepared=prod, universe=object(), vol_method="vol20",
                flag_by_date={}, event_na_mapping="none",
                incident_id=fx.INC, archive_before=(),
                archive_after_reader=tuple)
    assert caught.value.moment == "C_BUILD_2"
    assert caught.value.code == "production_payload_drift"


def test_a_second_run_into_the_same_directory_stops_at_C_BUILD_1(
        prod, authority, tmp_path):
    """WAS `test_a_seal_conflict_stops_at_the_second_moment`, and the change
    is a second defect the H1 repair uncovered.

    C_BUILD_1 asserts the supplement byte set under `runs_root` is EMPTY
    before the first write. While `out_dir` and `runs_dir` were free
    parameters that check ran against a directory the seal never touched --
    so "empty before the first write" was as vacuous as "the seal is
    archived" was false. Bound to one planned target, it now sees the
    previous seal and stops BEFORE writing.

    `supplement_seal_conflict` is therefore unreachable through the chain
    over one planned directory, which is correct: the planner refuses a
    target that already exists, so two runs never legitimately share one.
    It stays exercised at the producer level in
    `tests/test_run_c_build_2.py`, driven against the real sealer."""
    planned = _plan(tmp_path)
    _drive(authority, prod, tmp_path, planned=planned)
    sealed = planned.runs_target / dss.SUPPLEMENT_FILENAME
    assert sealed.is_file()

    with pytest.raises(chain.ChainRefusal) as caught:
        _drive(authority, prod, tmp_path, planned=planned)
    assert caught.value.moment == "C_BUILD_1"
    assert "c_build_1_not_empty" in str(caught.value)
    assert sealed.is_file(), "the refusal destroyed the previous seal"


def test_the_seal_lands_inside_the_tree_that_gets_archived(prod, authority,
                                                            tmp_path):
    """H1, from the 2026-09-02 engineering-safety HOLD.

    Reproduced before it was fixed: with `out_dir` and `runs_dir` as free
    parameters the chain returned P4 and archive_ok while the sealed
    supplement sat outside the archived tree -- the archive copied an empty
    directory. Policy A requires a second copy, and nothing in the code made
    one.

    The fix is not a binding rule invented here. `plan_supplement_paths` is
    the ratified planner and already owns the relationship: `runs_target` is
    where the run writes, and `archive_parent` is, in its own words, "what
    `archive_sealed_run` must be passed". The chain takes those instead of
    three free paths, so the two cannot be unbound."""
    runs_root, archive_root = tmp_path / "runs", tmp_path / "archive"
    runs_root.mkdir()
    archive_root.mkdir()
    planned = sr.plan_supplement_paths(
        runs_root=runs_root, archive_root=archive_root,
        supplement_id=fx.SID, utc_stamp="20260902T120000Z")
    planned.runs_target.mkdir(parents=True)

    days = sorted(authority.expected_day_set)
    with fxp._patched({d: "T1" for d in days}, {d: "none" for d in days}):
        result = chain.run_supplement_chain(          # REAL archive step
            _base_ctx(), planned=planned, authority=authority, prepared=prod,
            universe=object(), vol_method="vol20", flag_by_date={},
            event_na_mapping="none", incident_id=fx.INC,
            archive_before=(), archive_after_reader=tuple)

    assert result.verdict == "P4"
    sealed = planned.runs_target / dss.SUPPLEMENT_FILENAME
    assert sealed.is_file(), "the seal did not land in the run directory"
    archived = planned.archive_target / dss.SUPPLEMENT_FILENAME
    assert archived.is_file(), (
        "P4 with the seal absent from the archive -- Policy A's second copy "
        "is exactly what P4 is supposed to mean")
    assert archived.read_bytes() == sealed.read_bytes()


def test_it_creates_no_directory_of_its_own(prod, authority, tmp_path):
    """It writes only where the ratified planner said, and creates nothing
    the caller did not.

    REWRITTEN after the H1 repair. The old version asserted that `runs` and
    `archive` did not exist after a P4 -- which passed for the wrong reason:
    the archive had copied an empty directory and the seal was somewhere
    else entirely. That assertion was a symptom of the defect, recorded as
    an expectation.

    What is actually worth holding is that the chain does not INVENT a
    directory: the run target is created by the caller, the archive side is
    made by `archive_sealed_run` under the planned parent, and nothing
    appears outside those."""
    planned = _plan(tmp_path)
    before = {str(p) for p in tmp_path.rglob("*") if p.is_dir()}
    _drive(authority, prod, tmp_path, planned=planned)
    after = {str(p) for p in tmp_path.rglob("*") if p.is_dir()}

    invented = sorted(after - before)
    assert invented == [], (
        "the chain created directories nobody asked for: %s" % invented)
    assert (planned.runs_target / dss.SUPPLEMENT_FILENAME).is_file()
if __name__ == "__main__":
    unittest.main()
