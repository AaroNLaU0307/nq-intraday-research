"""TASKS 6 and 7 -- controls C1 and C2. No real control outcomes are run."""
from __future__ import annotations

import inspect

import pytest
import synth

from r1 import controls
from r1.controls import (assert_c1_invariance, c1_directions, c2_dispersion,
                         non_event_dates, run_c1, run_c2,
                         specificity_difference, tercile_weights,
                         weighted_mean)
from r1.errors import R1Error
from r1.trade import run_arm

DATES = ["2015-01-02", "2015-02-06", "2015-03-06", "2015-04-03"]


def _source(contract, exit_price=102.0):
    return synth.simple_event_source(contract, DATES, pre=100.0, react=101.0,
                                     entry=100.0, exit_price=exit_price)


# ---------------------------------------------------------------- C1
def test_c1_directions_are_deterministic_per_seed():
    a = c1_directions(DATES, seed=7)
    b = c1_directions(DATES, seed=7)
    c = c1_directions(DATES, seed=13)
    assert a == b
    assert set(a) <= {1, -1}
    assert a != c or len(DATES) < 2


def test_c1_is_reproducible(contract):
    src = _source(contract)
    r1_ = run_c1(src, DATES, contract, seed=7, draws=50)
    r2_ = run_c1(src, DATES, contract, seed=7, draws=50)
    assert r1_.draw_means == r2_.draw_means
    assert r1_.mean_of_draw_means == r2_.mean_of_draw_means


def test_c1_cannot_alter_eligibility_timing_costs_or_exit(contract):
    src = _source(contract)
    primary = run_arm(src, [(d, 1) for d in DATES], contract)
    control = run_arm(src, list(zip(DATES, c1_directions(DATES, seed=31))),
                      contract)
    assert_c1_invariance(primary, control)          # passes
    assert [r.date_et for r in control] == DATES
    assert {r.cost_scenario for r in control} == {"Base"}


def test_c1_invariance_check_can_fail(contract):
    """The guard is demonstrated able to fail (fabricated divergence)."""
    src = _source(contract)
    primary = run_arm(src, [(d, 1) for d in DATES], contract)
    shorter = primary[:-1]
    with pytest.raises(R1Error, match="sample size"):
        assert_c1_invariance(primary, shorter)
    mutated = run_arm(src, [(d, 1) for d in DATES], contract,
                      cost_scenario="Severe")
    with pytest.raises(R1Error, match="cost model"):
        assert_c1_invariance(primary, mutated)


def test_c1_on_a_drifting_market_is_not_free_money(contract):
    """A random direction in a drifting window still pays the round turn."""
    src = _source(contract, exit_price=100.0)       # flat
    res = run_c1(src, DATES, contract, seed=7, draws=100)
    assert res.mean_of_draw_means == pytest.approx(-3.99, abs=1e-9)


# ---------------------------------------------------------------- C2
def test_c2_excludes_cpi_nfp_and_fomc():
    sessions = ["2015-01-02", "2015-01-05", "2015-01-06", "2015-01-07"]
    out = non_event_dates(sessions, ["2015-01-02"], ["2015-01-06"])
    assert out == ("2015-01-05", "2015-01-07")


def test_c2_uses_the_same_construction_sign(contract):
    src = _source(contract)
    arm = run_c2(src, DATES, contract, vol_states=["mid"] * len(DATES))
    assert [r.direction for r in arm.results] == [1] * len(DATES)
    assert arm.dates == tuple(DATES)


def test_c2_drops_no_direction_days_like_the_primary(contract):
    src = synth.source_with(contract, {
        DATES[0]: synth.event_day_bars(contract, pre_close=100.0,
                                       react_close=100.0, entry_open=100.0,
                                       exit_open=101.0),
        DATES[1]: synth.event_day_bars(contract, pre_close=100.0,
                                       react_close=101.0, entry_open=100.0,
                                       exit_open=101.0)})
    arm = run_c2(src, DATES[:2], contract, vol_states=["mid", "high"])
    assert arm.dates == (DATES[1],)
    assert arm.vol_states == ("high",)


def test_tercile_weights_follow_the_event_distribution():
    w = tercile_weights(["low", "low", "mid", "high"])
    assert w == {"low": 0.5, "mid": 0.25, "high": 0.25}
    with pytest.raises(R1Error):
        tercile_weights([None, None])


def test_c2_weighted_mean_reweights_onto_the_event_strata(contract):
    """An unmatched comparison is not like-for-like; the weighting fixes it."""
    dates = ["2015-01-05", "2015-01-06", "2015-01-07", "2015-01-08"]
    src = synth.source_with(contract, {
        dates[0]: synth.event_day_bars(contract, pre_close=100.0,
                                       react_close=101.0, entry_open=100.0,
                                       exit_open=101.0),   # +1 pt, low vol
        dates[1]: synth.event_day_bars(contract, pre_close=100.0,
                                       react_close=101.0, entry_open=100.0,
                                       exit_open=101.0),
        dates[2]: synth.event_day_bars(contract, pre_close=100.0,
                                       react_close=101.0, entry_open=100.0,
                                       exit_open=105.0),   # +5 pts, high vol
        dates[3]: synth.event_day_bars(contract, pre_close=100.0,
                                       react_close=101.0, entry_open=100.0,
                                       exit_open=105.0)})
    arm = run_c2(src, dates, contract, vol_states=["low", "low", "high", "high"])
    unmatched = sum(r.y_net_usd for r in arm.results) / len(arm.results)
    # events sit mostly in the HIGH tercile: the weighted mean must move there
    weighted = weighted_mean(arm, {"low": 0.25, "high": 0.75})
    assert weighted > unmatched


def test_specificity_difference_is_event_minus_weighted_control(contract):
    src = _source(contract, exit_price=104.0)             # event arm: +4 pts
    event_results = run_arm(src, [(d, 1) for d in DATES], contract)
    c2_src = _source(contract, exit_price=101.0)          # control arm: +1 pt
    arm = run_c2(c2_src, DATES, contract, vol_states=["mid"] * len(DATES))
    d_stat = specificity_difference(event_results, arm, ["mid"] * len(DATES))
    assert d_stat == pytest.approx(3.0 * contract.point_value_usd)


def test_c2_dispersion_takes_only_the_control_arm(contract):
    """Role separation: the OD-3 input cannot receive an event arm."""
    sig = inspect.signature(c2_dispersion)
    assert list(sig.parameters) == ["c2_arm"]
    src = synth.source_with(contract, {
        DATES[0]: synth.event_day_bars(contract, pre_close=100.0,
                                       react_close=101.0, entry_open=100.0,
                                       exit_open=101.0),
        DATES[1]: synth.event_day_bars(contract, pre_close=100.0,
                                       react_close=101.0, entry_open=100.0,
                                       exit_open=104.0)})
    arm = run_c2(src, DATES[:2], contract, vol_states=["mid", "mid"])
    assert c2_dispersion(arm) > 0
    with pytest.raises(R1Error, match="at least two"):
        c2_dispersion(type(arm)(results=arm.results[:1],
                                vol_states=arm.vol_states[:1]))


def test_controls_module_never_imports_the_verdict_engine():
    """A control may not reach the verdict: Axis 2 cannot create support."""
    import ast
    tree = ast.parse(inspect.getsource(controls))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
        elif isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
    assert not {".verdict", "r1.verdict", ".power_gate"} & imported
