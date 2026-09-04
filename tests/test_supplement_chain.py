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


def _drive(authority, prod, tmp_path, *, report=None, before=(), after=None,
           days=None):
    """One chain run, with the two unavoidable substitutions in place."""
    days = days if days is not None else sorted(authority.expected_day_set)
    out = tmp_path / "seal"
    out.mkdir(exist_ok=True)
    seam = mock.Mock(return_value=report or _Report("archive_ok"))
    with fxp._patched({d: "T1" for d in days}, {d: "none" for d in days}), \
            mock.patch.object(chain, "ARCHIVE_SEAM", seam):
        return chain.run_supplement_chain(
            _base_ctx(), authority=authority, prepared=prod,
            universe=object(), vol_method="vol20", flag_by_date={},
            event_na_mapping="none", out_dir=out,
            runs_dir=tmp_path / "runs", archive_root=tmp_path / "archive",
            incident_id=fx.INC, archive_before=before,
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
    result = _drive(authority, prod, tmp_path)
    assert result.verdict == "P4"
    assert result.sealed is True
    assert result.archive_status == "archive_ok"
    assert len(result.rows) == len(authority.expected_day_set)
    assert (tmp_path / "seal" / dss.SUPPLEMENT_FILENAME).is_file()


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
    out = tmp_path / "seal"
    out.mkdir()
    days = sorted(authority.expected_day_set)
    with pytest.raises(chain.ChainRefusal) as caught:
        _drive(authority, prod, tmp_path, days=days[:-1])
    assert caught.value.moment == "C_BUILD_1"
    assert list(out.iterdir()) == [], "it sealed despite refusing"


def test_a_lost_local_seal_is_refused_by_router_b(prod, authority, tmp_path):
    """`local_seal_absent` means the seal did not survive, which is exactly
    `local_seal_ok=False` -- and Router B already answers that."""
    def _vanish(runs_dir, archive_root):
        (tmp_path / "seal" / dss.SUPPLEMENT_FILENAME).unlink()
        return _Report("archive_ok")

    out = tmp_path / "seal"
    out.mkdir()
    days = sorted(authority.expected_day_set)
    with fxp._patched({d: "T1" for d in days}, {d: "none" for d in days}), \
            mock.patch.object(chain, "ARCHIVE_SEAM", _vanish):
        with pytest.raises(chain.ChainRefusal) as caught:
            chain.run_supplement_chain(
                _base_ctx(), authority=authority, prepared=prod,
                universe=object(), vol_method="vol20", flag_by_date={},
                event_na_mapping="none", out_dir=out,
                runs_dir=tmp_path / "runs", archive_root=tmp_path / "arch",
                incident_id=fx.INC, archive_before=(),
                archive_after_reader=tuple)
    assert caught.value.moment == "C_BUILD_3"
    assert "nothing was sealed" in str(caught.value)


def test_archived_bytes_deleted_reaches_A1_and_never_P4(prod, authority,
                                                        tmp_path):
    """BD-5, executed. The report says `archive_ok` -- it verifies the copy
    it just made -- while C_BUILD_3 finds bytes archived EARLIER are gone.
    Policy A forbids P4, the seal plainly survived so a refused seal is
    false, and this router's answer space is closed: A1 is the remainder."""
    before = (("old.json", 3, "a" * 64),)
    result = _drive(authority, prod, tmp_path, before=before, after=())
    assert result.verdict == "A1"
    assert result.sealed is False
    assert result.archive_status == "archive_ok", (
        "the report itself said ok; if it now says otherwise this test is "
        "no longer exercising the disagreement it was written for")


def test_A1_here_is_not_the_same_as_carrying_on(prod, authority, tmp_path):
    """The half of BD-5 that makes the elimination sufficient. A1 is a
    NON-TERMINAL trap -- `P5` is unreachable until an explicit `A2` -- so
    mapping destroyed evidence onto it blocks completion rather than
    waving it through."""
    assert "A1" in sc.NON_TERMINAL_TRAPS
    assert "A1" not in sc.TERMINAL_SHORT_IDS


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
    out = tmp_path / "seal"
    out.mkdir()
    days = sorted(authority.expected_day_set)
    with fxp._patched({d: "T1" for d in days}, {d: "none" for d in days}), \
            mock.patch.object(sp, "seal_supplement_production",
                              side_effect=exc), \
            mock.patch.object(sr, "GATES", dict(sr.GATES)) as gates:
        gates["seal_staging_partial"] = mock.Mock(
            side_effect=AssertionError("the gate was consulted"))
        with pytest.raises(chain.ChainRefusal) as caught:
            chain.run_supplement_chain(
                _base_ctx(), authority=authority, prepared=prod,
                universe=object(), vol_method="vol20", flag_by_date={},
                event_na_mapping="none", out_dir=out,
                runs_dir=tmp_path / "runs", archive_root=tmp_path / "arch",
                incident_id=fx.INC, archive_before=(),
                archive_after_reader=tuple)
    assert caught.value.moment == "C_BUILD_2"
    assert caught.value.code == "production_payload_drift"


def test_a_seal_conflict_stops_at_the_second_moment(prod, authority,
                                                    tmp_path):
    """The gate-owned half of the same moment, driven for real."""
    _drive(authority, prod, tmp_path)
    sealed = tmp_path / "seal" / dss.SUPPLEMENT_FILENAME
    sealed.write_bytes(sealed.read_bytes() + b" ")
    with pytest.raises(chain.ChainRefusal) as caught:
        _drive(authority, prod, tmp_path)
    assert caught.value.moment == "C_BUILD_2"
    assert "supplement_seal_conflict" in str(caught.value)


def test_bars_to_P4_with_NOTHING_mocked_but_the_archive(prod, authority,
                                                        tmp_path):
    """THE END-TO-END, and the strongest thing that can be shown without
    touching Development data.

    Synthetic 1-minute bars -> `build_universe` -> day contexts -> the RULED
    vol and event methods -> real rows -> the three C_BUILD_1 gates -> the
    real production sealer -> `resolve_partial` -> Router B -> P4. The two
    S0 universe builders are NOT patched here, unlike everywhere else in
    this file, so the vol and event mappings are the real ones.

    Only the archive step is substituted, and only because it copies a
    directory tree; what the chain reads from it is a status.

    WHAT THIS DOES NOT SHOW. The bars are synthetic. `load_real` has never
    run, and this says nothing about what real bars would produce -- only
    that every step between bars and a verdict is composed and works.
    """
    import test_s0_context as s0t
    from itsf.mc import supplement_inputs as si

    history = ["2026-07-%02d" % d for d in range(1, 32)]
    dates = sorted(set(history) | set(authority.expected_day_set))
    bars, schedule = s0t.make_market(dates)
    inputs = si.assemble_chain_inputs(
        bars_by_date=bars, schedule=schedule, events=s0t.NO_EVENTS,
        expected_day_set=authority.expected_day_set)
    assert sorted(inputs.flag_by_date) == sorted(authority.expected_day_set)

    out = tmp_path / "seal"
    out.mkdir()
    with mock.patch.object(chain, "ARCHIVE_SEAM",
                           mock.Mock(return_value=_Report("archive_ok"))):
        result = chain.run_supplement_chain(
            _base_ctx(), authority=authority, prepared=prod,
            universe=inputs.universe, vol_method=inputs.vol_method,
            flag_by_date=inputs.flag_by_date,
            event_na_mapping=inputs.event_na_mapping, out_dir=out,
            runs_dir=tmp_path / "runs", archive_root=tmp_path / "arch",
            incident_id=fx.INC, archive_before=(),
            archive_after_reader=tuple)

    assert result.verdict == "P4"
    assert len(result.rows) == len(authority.expected_day_set)
    sealed = out / dss.SUPPLEMENT_FILENAME
    assert sealed.is_file()
    assert hashlib.sha256(sealed.read_bytes()).hexdigest() == \
        result.local_seal_sha256


def test_the_unscoped_event_map_is_refused_rather_than_trimmed_silently(
        prod, authority, tmp_path):
    """Why `assemble_chain_inputs` takes the sealed day set at all.

    Measured: the synthetic market yields 36 structurally eligible days
    against a 5-day sealed universe, and an unscoped mapping refuses with
    `event_day_invented`. Scoping is the caller's job, and the gate is what
    says so."""
    import test_s0_context as s0t
    from itsf.mc import supplement_inputs as si

    history = ["2026-07-%02d" % d for d in range(1, 32)]
    dates = sorted(set(history) | set(authority.expected_day_set))
    bars, schedule = s0t.make_market(dates)
    everything = si.assemble_chain_inputs(
        bars_by_date=bars, schedule=schedule, events=s0t.NO_EVENTS,
        expected_day_set=frozenset(dates))
    assert len(everything.flag_by_date) > len(authority.expected_day_set)

    out = tmp_path / "seal"
    out.mkdir()
    with pytest.raises(chain.ChainRefusal) as caught:
        chain.run_supplement_chain(
            _base_ctx(), authority=authority, prepared=prod,
            universe=everything.universe, vol_method=everything.vol_method,
            flag_by_date=everything.flag_by_date,
            event_na_mapping=everything.event_na_mapping, out_dir=out,
            runs_dir=tmp_path / "runs", archive_root=tmp_path / "arch",
            incident_id=fx.INC, archive_before=(),
            archive_after_reader=tuple)
    assert caught.value.moment == "C_BUILD_1"
    assert "event_day_invented" in str(caught.value)
    assert list(out.iterdir()) == [], "it sealed despite refusing"


def test_it_creates_no_directory_of_its_own(prod, authority, tmp_path):
    """`runs_dir` and `archive_root` are handed in and never made here --
    creating one is Aaron's authorization to give, not this module's."""
    _drive(authority, prod, tmp_path)
    assert not (tmp_path / "runs").exists()
    assert not (tmp_path / "archive").exists()


if __name__ == "__main__":
    unittest.main()
