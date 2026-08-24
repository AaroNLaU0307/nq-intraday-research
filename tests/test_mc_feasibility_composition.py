"""M4's conjunction, and the one boolean the verdict table consumes.

The property this file exists for: `VerdictInput.feasible` may only ever
come from measured gate outcomes. R2 once had a necessary-conditions
boolean that a caller could assert; PHASE G retracted it and left the gate
refusing outright, which is what kept Checkpoint-0 unreachable. M1-M5
supplied the reduction, so the gate can be crossed now -- and the thing
that must not come back is a caller-assertable boolean.
"""
from __future__ import annotations

import pytest

from itsf.mc import consumer as mcc
from itsf.mc import feasibility as fz

from test_mc_consumer import _prepare, PRIMARY


class _Atom:
    def __init__(self, world_index, payout_count=0, offered_days=0,
                 skips_n0=0, executed_trade_days=0):
        self.world_index = world_index
        self.payout_count = payout_count
        self.offered_days = offered_days
        self.skips_n0 = skips_n0
        self.executed_trade_days = executed_trade_days


class _Obs:
    def __init__(self, atoms):
        self.atoms = tuple(atoms)


def _healthy(n=20):
    return _Obs([_Atom(w, payout_count=2, offered_days=10, skips_n0=0,
                       executed_trade_days=10) for w in range(n)])


def _starving(n=20):
    return _Obs([_Atom(w, payout_count=2, offered_days=10, skips_n0=10,
                       executed_trade_days=0) for w in range(n)])


DAYS = [f"2026-0{m}-{d:02d}" for m in (1, 2, 3) for d in range(1, 11)]


# --- the conjunction --------------------------------------------------------

def test_all_three_gates_passing_yields_feasible():
    out = fz.combo_feasibility(
        {"Conservative": _healthy(), "Stress": _healthy()}, DAYS)
    assert out.feasible is True
    assert out.failing() == ()
    assert len(out.outcomes) == 5      # frequency once + 2 gates x 2 scenarios


def test_one_failing_scenario_fails_the_combo():
    """M5 requires BOTH. A combo healthy under Conservative and starving
    under Stress is not feasible, and the failing outcome says which."""
    out = fz.combo_feasibility(
        {"Conservative": _healthy(), "Stress": _starving()}, DAYS)
    assert out.feasible is False
    failing = out.failing()
    assert [o.scenario for o in failing] == ["Stress"]
    assert [o.gate for o in failing] == ["integer_position"]


def test_a_missing_scenario_is_a_refusal_not_a_skip():
    """Evaluating whichever scenario the caller supplied would weaken the
    conjunction to whatever was passed -- permissively, every time."""
    with pytest.raises(fz.FeasibilityGateError) as ei:
        fz.combo_feasibility({"Conservative": _healthy()}, DAYS)
    assert ei.value.code == "feasibility_scenario_missing"
    assert "Stress" in str(ei.value)


def test_the_frequency_gate_is_evaluated_once_not_per_scenario():
    out = fz.combo_feasibility(
        {"Conservative": _healthy(), "Stress": _healthy()}, DAYS)
    freq = [o for o in out.outcomes if o.gate == "frequency"]
    assert len(freq) == 1
    assert freq[0].scenario == "ALL"


def test_a_failing_frequency_gate_sinks_the_combo_in_both_scenarios():
    thin = ["2026-01-05", "2026-02-05", "2026-03-05"]
    out = fz.combo_feasibility(
        {"Conservative": _healthy(), "Stress": _healthy()}, thin)
    assert out.feasible is False
    assert [o.gate for o in out.failing()] == ["frequency"]


def test_the_outcomes_travel_with_the_boolean():
    """`feasible` is the last thing anyone can interrogate at N17, so the
    gates it was composed from must not be discarded when it forms."""
    out = fz.combo_feasibility(
        {"Conservative": _healthy(), "Stress": _starving()}, DAYS)
    assert out.post_freeze_definition is True
    assert out.delegated is True
    assert out.scenarios == ("Conservative", "Stress")
    for o in out.outcomes:
        assert o.measured is not None and o.threshold is not None


# --- the gate the verdict table sits behind ---------------------------------

def _epi(prepared, scenario):
    return mcc.run_epistemic(prepared, platform="topstep", engine="E1",
                             scenario=scenario, channel=PRIMARY, B=2,
                             master_seed=7)


def test_the_go_gate_refuses_a_bare_boolean():
    """THE PROPERTY THIS WHOLE FILE PROTECTS. `True` carries no gate
    outcomes, no scenario set and no ruling id, so a caller passing one
    would be asserting feasibility that nothing measured -- which is
    precisely what R2's retracted boolean allowed."""
    prepared = _prepare()
    cons, stress = _epi(prepared, "Conservative"), _epi(prepared, "Stress")
    for bad in (True, False, 1, "yes", {"feasible": True}):
        with pytest.raises(mcc.MCInputError) as ei:
            mcc.epistemic_go_gate_input(cons, stress, feasibility=bad)
        assert ei.value.code == "feasibility_not_composed_evidence", bad


def test_the_go_gate_refuses_an_absent_feasibility():
    prepared = _prepare()
    cons, stress = _epi(prepared, "Conservative"), _epi(prepared, "Stress")
    with pytest.raises(mcc.MCInputError) as ei:
        mcc.epistemic_go_gate_input(cons, stress)
    assert ei.value.code == "feasibility_gate_input_absent"


def test_the_go_gate_refuses_evidence_from_another_ruling():
    """A verdict must not be assembled from gates evaluated under a rule
    this build no longer holds."""
    import dataclasses
    prepared = _prepare()
    cons, stress = _epi(prepared, "Conservative"), _epi(prepared, "Stress")
    good = fz.combo_feasibility(
        {"Conservative": _healthy(), "Stress": _healthy()}, DAYS)
    stale = dataclasses.replace(good, ruling="SOME_EARLIER_RULING")
    with pytest.raises(mcc.MCInputError) as ei:
        mcc.epistemic_go_gate_input(cons, stress, feasibility=stale)
    assert ei.value.code == "feasibility_ruling_mismatch"


def test_composed_evidence_builds_a_verdict_input():
    prepared = _prepare()
    cons, stress = _epi(prepared, "Conservative"), _epi(prepared, "Stress")
    good = fz.combo_feasibility(
        {"Conservative": _healthy(), "Stress": _healthy()}, DAYS)
    vi = mcc.epistemic_go_gate_input(cons, stress, feasibility=good)
    assert vi.feasible is True
    assert vi.platform == "topstep" and vi.engine == "E1"
    assert vi.channel == PRIMARY
    assert vi.p5_cons == cons.p5 and vi.median_stress == stress.median


def test_the_evidence_layer_still_carries_no_feasible_boolean():
    """Kept from the pre-ruling guards, and it matters more now than it
    did then: the reduction exists, so the only thing stopping evidence
    from being mistaken for a verdict is that the boolean lives one layer
    up, in a type that carries what produced it."""
    prepared = _prepare()
    obs = mcc.run_observation_set(prepared, run_label="base",
                                  platform="topstep", engine="E1",
                                  scenario="Conservative", channel=PRIMARY,
                                  B=2, master_seed=7)
    fe = mcc.FeasibilityEvidence.from_observations(obs)
    assert not hasattr(fe, "feasible")
    assert "feasible" not in fe.metrics
