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


# ===========================================================================
# DR-1 (Aaron 2026-08-10) — costs.py as the production consumer of the ruled
# `contracts.SpreadCostMethod`. Every ruled value is IMPORTED from contracts;
# no ruling literal is restated in this file. All tables are SYNTHETIC — the
# real spread_cost_table.csv is never read here.
# ===========================================================================
import dataclasses

import numpy as np

from itsf.contracts import (
    AARON_RULED_ADVERSE_TICKS_PRIMARY,
    AARON_RULED_ADVERSE_TICKS_SENSITIVITY,
    aaron_ruled_methods,
)

RULED = aaron_ruled_methods()
RULED_SPREAD = RULED.spread_cost

# Four IN-WINDOW slots (an EVEN count, so the Q50 endpoint sits at virtual
# index 1.5 and MUST be linearly interpolated between two order statistics).
IN_WINDOW = (600, 601, 602, 603)
MED_IN = (0.5, 0.75, 1.0, 1.25)
P90_IN = (1.0, 1.25, 1.5, 1.75)
P95_IN = (1.5, 1.75, 2.0, 2.25)

# Hand-computed rule B-i triple: sorted 4 values -> (v[1] + v[2]) / 2.
EXPECTED_TRIPLE = (0.875, 1.375, 1.875)

# POISON slots, all OUTSIDE [600, 944] and all far ABOVE the in-window values:
# 570 = 09:30 (RTH open), 599 = 09:59 (one minute early), 945 = 15:45 (one
# minute late), 959 = 15:59. If any of them leaked in, the triple would move.
POISON = {570: (10.0, 20.0, 30.0), 599: (11.0, 21.0, 31.0),
          945: (12.0, 22.0, 32.0), 959: (13.0, 23.0, 33.0)}
# Hand-computed triple if the window were widened to [570, 959] (8 slots):
# median col sorted [.5,.75,1,1.25,10,11,12,13] -> (1.25+10)/2 = 5.625, etc.
WIDENED_TRIPLE = (5.625, 10.875, 16.125)


def spread_rows(extra_minutes=(), n_obs=None):
    """Synthetic per-minute spread table in the loader's column schema."""
    minutes = list(IN_WINDOW)
    med, p90, p95 = list(MED_IN), list(P90_IN), list(P95_IN)
    for minute in extra_minutes:
        minutes.append(minute)
        m, a, b = POISON[minute]
        med.append(m)
        p90.append(a)
        p95.append(b)
    counts = list(n_obs) if n_obs is not None else [1000] * len(minutes)
    return {"minute_of_day_et": minutes, "spread_median_points": med,
            "spread_p90_points": p90, "spread_p95_points": p95,
            "n_obs": counts}


# --- the ruled reduction ----------------------------------------------------

def test_dr1_triple_is_q50_per_column_with_linear_interpolation():
    """Rule B-i, exact: three SEPARATE cross-slot medians, linear method."""
    got = costs.derive_spread_scalars(spread_rows(), RULED_SPREAD)
    assert got == EXPECTED_TRIPLE
    # linear interpolation is load-bearing: 'lower' / 'higher' / 'nearest'
    # would all return an ORDER STATISTIC, and none of them is 0.875.
    for method_name in ("lower", "higher", "nearest", "midpoint"):
        alt = float(np.percentile(MED_IN, 50.0, method=method_name))
        if method_name == "midpoint":
            assert alt == got[0]        # midpoint coincides on an even count
        else:
            assert alt != got[0], method_name


def test_dr1_no_rounding_is_applied():
    """NO rounding — not to a tick, not to a decimal place."""
    median = costs.derive_spread_scalars(spread_rows(), RULED_SPREAD)[0]
    assert median != round(median * 4) / 4          # not tick-rounded
    assert median != round(median, 2)               # not 2dp-rounded
    assert median == 0.875


def test_dr1_out_of_window_slots_are_excluded():
    """A poisoned slot at 599 or 945 must not move the triple by one bit."""
    clean = costs.derive_spread_scalars(spread_rows(), RULED_SPREAD)
    for minute in (570, 599, 945, 959):
        poisoned = costs.derive_spread_scalars(
            spread_rows(extra_minutes=(minute,)), RULED_SPREAD)
        assert poisoned == clean, minute
    both = costs.derive_spread_scalars(
        spread_rows(extra_minutes=(570, 599, 945, 959)), RULED_SPREAD)
    assert both == clean == EXPECTED_TRIPLE


def test_dr1_window_bounds_are_600_and_944_inclusive():
    assert (costs.TRADING_WINDOW_MINUTE_LO,
            costs.TRADING_WINDOW_MINUTE_HI) == (600, 944)
    # both endpoints are INSIDE: a table made only of them is usable
    edge = {"minute_of_day_et": [600, 944],
            "spread_median_points": [0.5, 1.5],
            "spread_p90_points": [1.0, 2.0],
            "spread_p95_points": [1.5, 2.5], "n_obs": [10, 10]}
    assert costs.derive_spread_scalars(edge, RULED_SPREAD) == (1.0, 1.5, 2.0)


def test_dr1_mutation_widening_the_window_changes_the_answer():
    """MUTATION GUARD: [570, 959] is a materially different answer.

    The fixture is built so the two windows CANNOT coincide; if a future edit
    widens `TRADING_WINDOW_MINUTE_LO/HI`, the pin above turns red instead of
    quietly re-quoting a different spread.
    """
    table = spread_rows(extra_minutes=(570, 599, 945, 959))
    widened = tuple(
        float(np.percentile(table[col], 50.0, method="linear"))
        for col in ("spread_median_points", "spread_p90_points",
                    "spread_p95_points"))
    assert widened == WIDENED_TRIPLE
    assert widened != EXPECTED_TRIPLE
    assert costs.derive_spread_scalars(table, RULED_SPREAD) == EXPECTED_TRIPLE


def test_dr1_slots_are_equal_weight_n_obs_is_never_a_weight():
    """One busy minute must not out-vote three quiet ones."""
    flat = costs.derive_spread_scalars(spread_rows(n_obs=[1, 1, 1, 1]),
                                       RULED_SPREAD)
    skewed = costs.derive_spread_scalars(
        spread_rows(n_obs=[1, 1, 1, 10 ** 9]), RULED_SPREAD)
    assert flat == skewed == EXPECTED_TRIPLE
    # an n_obs-WEIGHTED median of the same slots would be the top value
    assert float(np.median(np.repeat(MED_IN, [1, 1, 1, 50]))) != flat[0]


def test_dr1_ordering_invariant_is_preserved_and_checked():
    median, p90, p95 = costs.derive_spread_scalars(spread_rows(), RULED_SPREAD)
    assert 0.0 <= median <= p90 <= p95
    bad = spread_rows()
    bad["spread_p90_points"] = [0.0, 0.0, 0.0, 0.0]     # p90 below the median
    with pytest.raises(ValueError, match="spread_scalars_not_ordered"):
        costs.derive_spread_scalars(bad, RULED_SPREAD)


# --- fail-closed dispatch ---------------------------------------------------

def test_dr1_unruled_scalar_rule_is_refused():
    for unruled in ("A", "A_i_rth_pooled", "C", "", "B_i"):
        method = dataclasses.replace(RULED_SPREAD, scalar_rule=unruled)
        with pytest.raises(ValueError,
                           match=f"spread_scalar_rule_not_ruled:{unruled}"):
            costs.derive_spread_scalars(spread_rows(), method)


def test_dr1_ruled_rule_id_matches_the_contracts_ruling():
    """The dispatch key IS the ruled string — no second vocabulary."""
    assert costs.SPREAD_SCALAR_RULE_B_I == RULED_SPREAD.scalar_rule


def test_dr1_table_defects_fail_closed():
    with pytest.raises(ValueError, match="spread_table_missing_column"):
        costs.derive_spread_scalars({"minute_of_day_et": [600]}, RULED_SPREAD)
    dup = spread_rows()
    dup["minute_of_day_et"] = [600, 600, 602, 603]
    with pytest.raises(ValueError, match="duplicate_minute_slot"):
        costs.derive_spread_scalars(dup, RULED_SPREAD)
    outside = {"minute_of_day_et": [570, 959],
               "spread_median_points": [0.5, 0.5],
               "spread_p90_points": [1.0, 1.0],
               "spread_p95_points": [1.5, 1.5]}
    with pytest.raises(ValueError, match="no_slots_in_trading_window"):
        costs.derive_spread_scalars(outside, RULED_SPREAD)
    nan = spread_rows()
    nan["spread_p95_points"] = [1.5, float("nan"), 2.0, 2.25]
    with pytest.raises(ValueError, match="non_finite_in_window"):
        costs.derive_spread_scalars(nan, RULED_SPREAD)


def test_dr1_accepts_dataframe_mapping_and_rows_identically():
    import pandas as pd
    cols = spread_rows(extra_minutes=(599, 945))
    frame = pd.DataFrame(cols)
    rows = [dict(zip(cols, values)) for values in zip(*cols.values())]
    a = costs.derive_spread_scalars(cols, RULED_SPREAD)
    b = costs.derive_spread_scalars(frame, RULED_SPREAD)
    c = costs.derive_spread_scalars(rows, RULED_SPREAD)
    assert a == b == c == EXPECTED_TRIPLE


# --- IR-7 adverse slippage: sourcing, channel, and the double-count trap ----

def test_ir7_primary_effective_ticks_equal_the_ruled_vector():
    scns = costs.build_scenarios_from_method((0.5, 1.0, 1.5), RULED_SPREAD)
    for name in costs.SCENARIO_NAMES:
        assert costs.effective_adverse_ticks(scns[name]) == (
            AARON_RULED_ADVERSE_TICKS_PRIMARY[name]), name


def test_ir7_stress_adverse_is_never_remultiplied():
    """The double-count trap, pinned behaviourally.

    Stress's ruled adverse value is already Base x2, so the scenario's own
    friction_multiplier must NOT be applied to it a second time. The stored
    field is PRE-multiplier (1.0) and the effective count is 2.0 — not 4.0.
    """
    stress = costs.build_scenarios_from_method(
        (0.5, 1.0, 1.5), RULED_SPREAD)["Stress"]
    assert stress.friction_multiplier == 2.0
    assert costs.effective_adverse_ticks(stress) == 2.0
    assert stress.adverse_slippage_ticks == 1.0        # pre-multiplier field

    # adverse side friction: 2.0 * (0.5/2 + 1.0*0.25) = 1.0 points
    assert costs.side_friction_points(stress, adverse=True) == pytest.approx(1.0)
    # the double-counted value (stored 2.0 -> 4 effective ticks) is 1.5 points
    assert costs.side_friction_points(stress, adverse=True) != pytest.approx(1.5)
    # stop fill: 19990 - (2*0.5/2 + 2*1.0*0.25) = 19989.0, NOT 19988.5
    assert costs.scenario_stop_fill(19990.0, 19995.0, 1, stress) == (
        pytest.approx(19989.0))

    naive = dataclasses.replace(
        stress, adverse_slippage_ticks=AARON_RULED_ADVERSE_TICKS_PRIMARY[
            "Stress"])
    assert costs.effective_adverse_ticks(naive) == 4.0     # the trap, shown
    assert costs.scenario_stop_fill(19990.0, 19995.0, 1, naive) == (
        pytest.approx(19988.5))


def test_ir7_adverse_replaces_the_per_side_slip_never_adds_to_it():
    """`replaces_per_side`: the adverse ticks stand IN PLACE of the regular
    per-side slip on a stop fill; the old 'extra for stop fills' wording is a
    comment defect, not the implementation's behaviour."""
    base = costs.build_scenarios_from_method(
        (0.5, 1.0, 1.5), RULED_SPREAD,
        adverse_channel=costs.ADVERSE_CHANNEL_SENSITIVITY)["Base"]
    assert costs.effective_adverse_ticks(base) == (
        AARON_RULED_ADVERSE_TICKS_SENSITIVITY["Base"])       # 2.0
    assert base.slippage_ticks_per_side == 1.0
    # REPLACES: 1.0 * (0.25 + 2.0*0.25) = 0.75 points
    assert costs.side_friction_points(base, adverse=True) == pytest.approx(0.75)
    # ADDS would be 1.0 * (0.25 + (1.0+2.0)*0.25) = 1.00 points
    assert costs.side_friction_points(base, adverse=True) != pytest.approx(1.0)


def test_ir7_sensitivity_channel_cannot_be_reached_silently():
    primary = costs.build_scenarios_from_method((0.5, 1.0, 1.5), RULED_SPREAD)
    explicit = costs.build_scenarios_from_method(
        (0.5, 1.0, 1.5), RULED_SPREAD,
        adverse_channel=costs.ADVERSE_CHANNEL_PRIMARY)
    sens = costs.build_scenarios_from_method(
        (0.5, 1.0, 1.5), RULED_SPREAD,
        adverse_channel=costs.ADVERSE_CHANNEL_SENSITIVITY)
    for name in costs.SCENARIO_NAMES:
        # default IS Primary
        assert (costs.effective_adverse_ticks(primary[name])
                == costs.effective_adverse_ticks(explicit[name])
                == AARON_RULED_ADVERSE_TICKS_PRIMARY[name])
        assert costs.effective_adverse_ticks(sens[name]) == (
            AARON_RULED_ADVERSE_TICKS_SENSITIVITY[name])
        assert (costs.effective_adverse_ticks(sens[name])
                != costs.effective_adverse_ticks(primary[name]))
    for bogus in ("sensitivity", "plus1", "", "Primary"):
        with pytest.raises(ValueError,
                           match=f"adverse_channel_not_ruled:{bogus}"):
            costs.build_scenarios_from_method((0.5, 1.0, 1.5), RULED_SPREAD,
                                              adverse_channel=bogus)


def test_ir7_unruled_semantics_and_broken_vectors_fail_closed():
    with pytest.raises(ValueError, match="adverse_semantics_not_ruled:extra"):
        costs.build_scenarios_from_method(
            (0.5, 1.0, 1.5),
            dataclasses.replace(RULED_SPREAD, adverse_semantics="extra"))
    short = dataclasses.replace(
        RULED_SPREAD, adverse_slippage_ticks={"Base": 1.0, "Severe": 3.0})
    with pytest.raises(ValueError,
                       match="adverse_slippage_ticks_missing_scenario"):
        costs.build_scenarios_from_method((0.5, 1.0, 1.5), short)
    extra = dict(AARON_RULED_ADVERSE_TICKS_PRIMARY)
    extra["Apocalyptic"] = 9.0
    with pytest.raises(ValueError,
                       match="adverse_slippage_ticks_unknown_scenario"):
        costs.build_scenarios_from_method(
            (0.5, 1.0, 1.5),
            dataclasses.replace(RULED_SPREAD, adverse_slippage_ticks=extra))
    with pytest.raises(ValueError, match="spread_scalars_not_ordered"):
        costs.build_scenarios_from_method((1.5, 1.0, 0.5), RULED_SPREAD)
    with pytest.raises(ValueError, match="not_a_SpreadCostMethod"):
        costs.build_scenarios_from_method((0.5, 1.0, 1.5), object())


def test_ir7_disclosure_shows_one_multiplication_per_scenario():
    scns = costs.build_scenarios_from_method((0.5, 1.0, 1.5), RULED_SPREAD)
    disc = costs.adverse_ticks_disclosure(scns, RULED_SPREAD)
    assert disc["adverse_channel"] == costs.ADVERSE_CHANNEL_PRIMARY
    assert disc["adverse_semantics"] == RULED_SPREAD.adverse_semantics
    assert disc["ruled_effective_ticks"] == dict(
        AARON_RULED_ADVERSE_TICKS_PRIMARY)
    for name, row in disc["per_scenario"].items():
        assert (row["stored_pre_multiplier_ticks"] * row["friction_multiplier"]
                == row["effective_ticks"] ==
                AARON_RULED_ADVERSE_TICKS_PRIMARY[name])


def test_ir7_end_to_end_from_a_synthetic_table():
    """Table -> ruled scalars -> ruled scenarios, with no literal in between."""
    scalars = costs.derive_spread_scalars(
        spread_rows(extra_minutes=(599, 945)), RULED_SPREAD)
    scns = costs.build_scenarios_from_method(scalars, RULED_SPREAD)
    assert scns["Base"].spread_points == scalars[0]
    assert scns["Conservative"].spread_points == scalars[1]
    assert scns["Severe"].spread_points == scalars[2]
    assert scns["Stress"].spread_points == scalars[0]      # Base spread x2 mult
    for name in costs.SCENARIO_NAMES:
        assert costs.effective_adverse_ticks(scns[name]) == (
            AARON_RULED_ADVERSE_TICKS_PRIMARY[name])
