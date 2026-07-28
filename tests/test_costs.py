"""Hand-computed tests for itsf.s0.costs.  # frozen: S0 SS6

All numbers below are worked by hand:
TICK = 0.25 points; spread 0.5 -> spread/2 = 0.25/side;
1 tick slippage = 0.25; 2 ticks adverse = 0.5.
"""
from __future__ import annotations

import pytest

from itsf.contracts import S0_PLATFORM_FEE_RT_USD, CostScenarioParams
from itsf.s0 import costs


# --- signed-d fill primitives (hand-computed, long AND short) ---------------

def test_entry_fill_long_hand():
    # 20000 + (+1)*(0.5/2 + 1*0.25) = 20000.5   # frozen: S0 SS6
    assert costs.entry_fill(20000.0, 1, 0.5, 1.0) == pytest.approx(20000.5)


def test_entry_fill_short_hand():
    # 20000 + (-1)*(0.25 + 0.25) = 19999.5
    assert costs.entry_fill(20000.0, -1, 0.5, 1.0) == pytest.approx(19999.5)


def test_timed_exit_fill_mirror_hand():
    # long exit pays DOWN, short exit pays UP   # frozen: S0 SS6
    assert costs.timed_exit_fill(20000.0, 1, 0.5, 1.0) == pytest.approx(19999.5)
    assert costs.timed_exit_fill(20000.0, -1, 0.5, 1.0) == pytest.approx(20000.5)


def test_stop_fill_intrabar_long_hand():
    # open 19995 above stop 19990 -> trigger_ref = min(19990, 19995) = 19990
    # fill = 19990 - (0.25 + 2*0.25) = 19989.25   # frozen: S0 SS6
    assert costs.stop_fill(19990.0, 19995.0, 1, 0.5, 2.0) == pytest.approx(19989.25)


def test_stop_fill_intrabar_short_hand():
    # trigger_ref = max(20010, 20005) = 20010; fill = 20010 + 0.75 = 20010.75
    assert costs.stop_fill(20010.0, 20005.0, -1, 0.5, 2.0) == pytest.approx(20010.75)


def test_stop_fill_gap_through_long_hand():
    # bar OPENS beyond the stop: open 19980 < stop 19990
    # trigger_ref = min(stop, bar_open) = 19980; fill = 19979.25  # frozen: S0 SS6
    assert costs.stop_fill(19990.0, 19980.0, 1, 0.5, 2.0) == pytest.approx(19979.25)


def test_stop_fill_gap_through_short_hand():
    # open 20020 > stop 20010 -> trigger_ref = 20020; fill = 20020.75
    assert costs.stop_fill(20010.0, 20020.0, -1, 0.5, 2.0) == pytest.approx(20020.75)


def test_invalid_direction_rejected():
    with pytest.raises(ValueError):
        costs.entry_fill(20000.0, 0, 0.5, 1.0)
    with pytest.raises(ValueError):
        costs.stop_fill(19990.0, 19995.0, 0, 0.5, 2.0)


# --- scenario grid ----------------------------------------------------------

def test_build_scenarios_grid():
    scns = costs.build_scenarios(0.5, 1.0, 1.5)
    assert set(scns) == {"Base", "Conservative", "Stress", "Severe"}
    # frozen: S0 SS6 — median+1t / P90+2t / P95+3t
    assert scns["Base"].spread_points == 0.5
    assert scns["Base"].slippage_ticks_per_side == 1.0
    assert scns["Conservative"].spread_points == 1.0
    assert scns["Conservative"].slippage_ticks_per_side == 2.0
    assert scns["Severe"].spread_points == 1.5
    assert scns["Severe"].slippage_ticks_per_side == 3.0


def test_stress_doubles_friction_not_fee():
    scns = costs.build_scenarios(0.5, 1.0, 1.5)
    base, stress = scns["Base"], scns["Stress"]
    # frozen: S0 SS6 — Stress = Base market friction x2
    assert stress.spread_points == base.spread_points
    assert stress.slippage_ticks_per_side == base.slippage_ticks_per_side
    assert stress.friction_multiplier == 2.0
    assert costs.side_friction_points(stress) == pytest.approx(
        2.0 * costs.side_friction_points(base))
    # frozen: S0 SS6 + platform_params s0_cost_handoff — fee NOT doubled,
    # identical 1.74 across every scenario
    for s in scns.values():
        assert s.platform_fee_rt_usd == S0_PLATFORM_FEE_RT_USD


def test_scenario_wrappers_apply_multiplier():
    stress = costs.build_scenarios(0.5, 1.0, 1.5)["Stress"]
    # entry: 20000 + 2*(0.25 + 0.25) = 20001.0
    assert costs.scenario_entry_fill(20000.0, 1, stress) == pytest.approx(20001.0)
    assert costs.scenario_timed_exit_fill(20000.0, 1, stress) == pytest.approx(19999.0)
    # stop intrabar: 19990 - 2*(0.25 + 0.25) = 19989.0 (adverse also doubled)
    assert costs.scenario_stop_fill(19990.0, 19995.0, 1, stress) == pytest.approx(19989.0)


# --- USD conversion / round-turn cost ---------------------------------------

def test_points_to_usd():
    assert costs.points_to_usd(1.0) == pytest.approx(2.0)   # $2/point (contracts)
    assert costs.points_to_usd(0.25) == pytest.approx(0.5)  # 1 tick = $0.50


def test_round_turn_cost_usd_timed_and_stop():
    scn = CostScenarioParams(name="Base", spread_points=0.5,
                             slippage_ticks_per_side=1.0,
                             adverse_slippage_ticks=2.0)
    # timed RT: (0.5 + 0.5) pts = $2.00 friction + $1.74 fee ONCE = $3.74
    assert costs.round_turn_cost_usd(scn) == pytest.approx(3.74)
    # stop exit RT: (0.5 + 0.75) pts = $2.50 + $1.74 = $4.24
    assert costs.round_turn_cost_usd(scn, stop_exit=True) == pytest.approx(4.24)


def test_round_turn_cost_usd_stress_fee_once():
    stress = costs.build_scenarios(0.5, 1.0, 1.5)["Stress"]
    # friction doubled: 2*(0.5+0.5) pts = $4.00; fee stays single $1.74
    # frozen: S0 SS6; platform_params execution_costs.s0_cost_handoff
    assert costs.round_turn_cost_usd(stress) == pytest.approx(5.74)
