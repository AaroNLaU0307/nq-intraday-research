"""TASK 5 (cost half) -- the pinned cost adapter, cross-checked against ITSF."""
from __future__ import annotations

import sys

import pytest

from r1 import itsf_pin
from r1.costs import (all_round_turn_costs_usd, entry_fill, points_to_usd,
                      round_turn_cost_usd, side_friction_points,
                      timed_exit_fill)
from r1.errors import R1Error

SEALED_G2 = {"Base": 3.99, "Conservative": 5.49, "Stress": 6.24, "Severe": 6.74}


def test_reproduces_the_sealed_g2_table(contract):
    got = all_round_turn_costs_usd(contract)
    for name, expected in SEALED_G2.items():
        assert got[name] == pytest.approx(expected, abs=1e-9), name


def test_stress_doubles_friction_but_not_the_fee(contract):
    base_friction = (side_friction_points(contract, "Base", "entry")
                     + side_friction_points(contract, "Base", "exit"))
    stress_friction = (side_friction_points(contract, "Stress", "entry")
                       + side_friction_points(contract, "Stress", "exit"))
    assert stress_friction == pytest.approx(2 * base_friction)
    fee = contract.cost_scenarios["Stress"].platform_fee_rt_usd
    assert fee == contract.cost_scenarios["Base"].platform_fee_rt_usd
    assert round_turn_cost_usd(contract, "Stress") == pytest.approx(
        points_to_usd(stress_friction, contract) + fee)


def test_fills_are_signed_against_the_trader(contract):
    long_entry = entry_fill(100.0, 1, contract, "Base")
    short_entry = entry_fill(100.0, -1, contract, "Base")
    assert long_entry > 100.0 > short_entry
    long_exit = timed_exit_fill(100.0, 1, contract, "Base")
    short_exit = timed_exit_fill(100.0, -1, contract, "Base")
    assert long_exit < 100.0 < short_exit


def test_flat_market_costs_exactly_the_round_turn(contract):
    for name in SEALED_G2:
        for d in (1, -1):
            e = entry_fill(100.0, d, contract, name)
            x = timed_exit_fill(100.0, d, contract, name)
            net = points_to_usd(d * (x - e), contract) \
                - contract.cost_scenarios[name].platform_fee_rt_usd
            assert net == pytest.approx(-round_turn_cost_usd(contract, name))


def test_unknown_scenario_is_a_refusal(contract):
    with pytest.raises(R1Error, match="unknown cost scenario"):
        round_turn_cost_usd(contract, "Optimistic")


def test_invalid_direction_is_a_refusal(contract):
    with pytest.raises(R1Error, match="direction"):
        entry_fill(100.0, 0, contract, "Base")


def test_no_stop_fill_path_exists():
    """The sealed Primary has no stop; the module must not contain one."""
    import r1.costs as costs
    assert not hasattr(costs, "stop_fill")
    assert not hasattr(costs, "scenario_stop_fill")


# ------------------------------------------------------- ITSF cross-check
def test_itsf_pins_are_recorded():
    pins = itsf_pin.verify_pins()
    assert set(pins) == set(itsf_pin.PINNED)


@pytest.mark.skipif(not itsf_pin.available(),
                    reason="parked ITSF repository not present")
def test_transcription_matches_itsf_numerically(contract):
    """R1's transcribed formulas vs ITSF's own module, on the pinned source.

    With EQUAL per-side spreads R1 collapses to ITSF exactly; R1's only
    deviation is pricing entry and exit at their own sealed spreads (E.3).
    """
    pins = itsf_pin.verify_pins()
    if any(v != "MATCH" for v in pins.values()):
        pytest.skip(f"ITSF pin moved: {pins}")

    src = str(itsf_pin.ITSF_ROOT / "src")
    if src not in sys.path:
        sys.path.insert(0, src)
    try:
        from itsf.contracts import CostScenarioParams
        from itsf.s0 import costs as itsf_costs
    except Exception as exc:                       # pragma: no cover
        pytest.skip(f"ITSF import unavailable: {exc}")

    for name, scn in contract.cost_scenarios.items():
        for spread in (scn.entry_spread_points, scn.exit_spread_points):
            itsf_scn = CostScenarioParams(
                name=name, spread_points=spread,
                slippage_ticks_per_side=scn.slippage_ticks_per_side,
                adverse_slippage_ticks=scn.slippage_ticks_per_side,
                friction_multiplier=scn.friction_multiplier,
                platform_fee_rt_usd=scn.platform_fee_rt_usd)
            itsf_side = itsf_costs.side_friction_points(itsf_scn)
            # R1 prices each side at that side's own spread
            r1_side = scn.friction_multiplier * (
                spread / 2.0 + scn.slippage_ticks_per_side * contract.tick_points)
            assert r1_side == pytest.approx(itsf_side), f"{name} side friction"

            assert itsf_costs.entry_fill(
                100.0, 1, scn.friction_multiplier * spread,
                scn.friction_multiplier * scn.slippage_ticks_per_side
            ) == pytest.approx(100.0 + r1_side)
            assert itsf_costs.timed_exit_fill(
                100.0, 1, scn.friction_multiplier * spread,
                scn.friction_multiplier * scn.slippage_ticks_per_side
            ) == pytest.approx(100.0 - r1_side)

        # symmetric case: equal spreads -> R1 == ITSF round turn exactly
        sym = CostScenarioParams(
            name=name, spread_points=scn.entry_spread_points,
            slippage_ticks_per_side=scn.slippage_ticks_per_side,
            adverse_slippage_ticks=scn.slippage_ticks_per_side,
            friction_multiplier=scn.friction_multiplier,
            platform_fee_rt_usd=scn.platform_fee_rt_usd)
        itsf_rt = itsf_costs.round_turn_cost_usd(sym)
        r1_rt = (points_to_usd(2 * side_friction_points(contract, name, "entry"),
                               contract) + scn.platform_fee_rt_usd)
        assert r1_rt == pytest.approx(itsf_rt), f"{name} symmetric round turn"
