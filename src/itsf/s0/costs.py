"""S0 cost model: signed-d fill formulas, cost-scenario grid, USD conversion.

Frozen sources:
- S0 SS6: fill formulas (signed d, spread/2 per side, gap-through trigger_ref,
  never assume a fill at the stop price itself), scenario grid
  Base / Conservative / Stress / Severe, and the rule
  "Stress = Base market_friction x 2 (platform_fee NOT doubled)".
- gate1/platform_params.yaml execution_costs.s0_cost_handoff: single
  conservative platform fee 1.74 USD per round turn, constant over the full
  horizon, burned into S0 per-trade P&L exactly ONCE (MC must not re-apply;
  double_counting_guard).

Units: all price refs and spreads are index POINTS (spread = FULL bid-ask
width; each side pays spread/2 — frozen S0 SS6); slippage inputs are ticks.
"""
from __future__ import annotations

from itsf.contracts import (
    MNQ_POINT_VALUE_USD,
    MNQ_TICK_POINTS,
    S0_PLATFORM_FEE_RT_USD,
    CostScenarioParams,
)


def _check_d(d: int) -> None:
    if d not in (1, -1):
        raise ValueError(f"direction d must be +1 or -1, got {d!r}")


# --- signed-d fill primitives (points) --------------------------------------

def entry_fill(ref: float, d: int, spread_points: float, slip_ticks: float) -> float:
    """entry_fill = ref + d * (spread/2 + slip_ticks*TICK).  # frozen: S0 SS6"""
    _check_d(d)
    return ref + d * (spread_points / 2.0 + slip_ticks * MNQ_TICK_POINTS)


def timed_exit_fill(ref: float, d: int, spread_points: float, slip_ticks: float) -> float:
    """timed_exit_fill = ref - d * (spread/2 + slip_ticks*TICK).  # frozen: S0 SS6"""
    _check_d(d)
    return ref - d * (spread_points / 2.0 + slip_ticks * MNQ_TICK_POINTS)


def stop_fill(stop: float, bar_open: float, d: int, spread_points: float,
              adverse_slip_ticks: float) -> float:
    """Stop fill on 1-minute OHLC.  # frozen: S0 SS6

    long  (d=+1): trigger_ref = min(stop, bar_open)  (bar opens below stop
                  -> gap-through, trigger at bar_open)
    short (d=-1): trigger_ref = max(stop, bar_open)
    intrabar touch collapses to trigger_ref = stop under the same min/max.
    fill = trigger_ref - d * (spread/2 + adverse_slip_ticks*TICK)
    Never assume the fill happens at the stop price (frozen prohibition).
    """
    _check_d(d)
    trigger_ref = min(stop, bar_open) if d == 1 else max(stop, bar_open)
    return trigger_ref - d * (spread_points / 2.0 + adverse_slip_ticks * MNQ_TICK_POINTS)


# --- scenario grid ----------------------------------------------------------

def build_scenarios(spread_median_points: float,
                    spread_p90_points: float,
                    spread_p95_points: float,
                    adverse_slippage_ticks: dict[str, float] | None = None,
                    platform_fee_rt_usd: float = S0_PLATFORM_FEE_RT_USD,
                    ) -> dict[str, CostScenarioParams]:
    """Build the four frozen cost scenarios from spread distribution stats.

    # frozen: S0 SS6 —
    Base         = period-median spread + 1 tick/side
    Conservative = P90 spread          + 2 ticks/side
    Stress       = Base market_friction x 2  (friction_multiplier=2.0 applied
                   to spread AND slippage; platform_fee NOT doubled)
    Severe       = P95 spread          + 3 ticks/side
    # frozen: platform_params execution_costs.s0_cost_handoff — single
    platform fee 1.74 RT for every scenario (Stress included).

    `adverse_slippage_ticks`: optional per-scenario override map
    {"Base": .., "Conservative": .., "Stress": .., "Severe": ..}. S0 SS6
    freezes the per-side slippage grid but does NOT freeze a separate numeric
    grid for stop-fill adverse slippage; the default here (= the scenario's
    own per-side slippage ticks) is a coding convention flagged to the main
    agent, NOT a frozen value.
    """
    adv = dict(adverse_slippage_ticks or {})

    def _a(name: str, default: float) -> float:
        return adv.get(name, default)

    base = CostScenarioParams(
        name="Base", spread_points=spread_median_points,
        slippage_ticks_per_side=1.0, adverse_slippage_ticks=_a("Base", 1.0),
        friction_multiplier=1.0, platform_fee_rt_usd=platform_fee_rt_usd)
    conservative = CostScenarioParams(
        name="Conservative", spread_points=spread_p90_points,
        slippage_ticks_per_side=2.0,
        adverse_slippage_ticks=_a("Conservative", 2.0),
        friction_multiplier=1.0, platform_fee_rt_usd=platform_fee_rt_usd)
    # frozen: S0 SS6 — Stress reuses Base raw friction params with x2
    # multiplier; platform fee stays single (not doubled).
    stress = CostScenarioParams(
        name="Stress", spread_points=spread_median_points,
        slippage_ticks_per_side=1.0,
        adverse_slippage_ticks=_a("Stress", _a("Base", 1.0)),
        friction_multiplier=2.0, platform_fee_rt_usd=platform_fee_rt_usd)
    severe = CostScenarioParams(
        name="Severe", spread_points=spread_p95_points,
        slippage_ticks_per_side=3.0, adverse_slippage_ticks=_a("Severe", 3.0),
        friction_multiplier=1.0, platform_fee_rt_usd=platform_fee_rt_usd)
    return {s.name: s for s in (base, conservative, stress, severe)}


# --- scenario-aware helpers -------------------------------------------------

def side_friction_points(scn: CostScenarioParams, adverse: bool = False) -> float:
    """Per-side market friction in points under a scenario.

    = friction_multiplier * (spread/2 + ticks*TICK); adverse=True uses the
    stop-fill adverse slippage ticks.  # frozen: S0 SS6 (Stress multiplies
    market friction only — the platform fee is handled separately).
    """
    ticks = scn.adverse_slippage_ticks if adverse else scn.slippage_ticks_per_side
    return scn.friction_multiplier * (scn.spread_points / 2.0 + ticks * MNQ_TICK_POINTS)


def scenario_entry_fill(ref: float, d: int, scn: CostScenarioParams) -> float:
    """entry_fill under a scenario (friction_multiplier applied).  # frozen: S0 SS6"""
    return entry_fill(ref, d, scn.friction_multiplier * scn.spread_points,
                      scn.friction_multiplier * scn.slippage_ticks_per_side)


def scenario_timed_exit_fill(ref: float, d: int, scn: CostScenarioParams) -> float:
    """timed_exit_fill under a scenario (friction_multiplier applied).  # frozen: S0 SS6"""
    return timed_exit_fill(ref, d, scn.friction_multiplier * scn.spread_points,
                           scn.friction_multiplier * scn.slippage_ticks_per_side)


def scenario_stop_fill(stop: float, bar_open: float, d: int,
                       scn: CostScenarioParams) -> float:
    """stop_fill under a scenario (friction_multiplier applied to spread AND
    adverse slippage).  # frozen: S0 SS6"""
    return stop_fill(stop, bar_open, d,
                     scn.friction_multiplier * scn.spread_points,
                     scn.friction_multiplier * scn.adverse_slippage_ticks)


# --- USD conversion ---------------------------------------------------------

def points_to_usd(points: float) -> float:
    """Index points -> USD per 1 MNQ contract (contracts.MNQ_POINT_VALUE_USD)."""
    return points * MNQ_POINT_VALUE_USD


def round_turn_cost_usd(scn: CostScenarioParams, stop_exit: bool = False) -> float:
    """Per-contract round-turn trade cost in USD.

    = market friction (entry side + exit side, points -> USD)
      + platform_fee_rt_usd applied exactly ONCE per round turn.
    stop_exit=True prices the exit side with adverse slippage.
    # frozen: S0 SS6 (Stress doubles friction, NOT the platform fee);
    # frozen: platform_params execution_costs.s0_cost_handoff (1.74 RT once,
    # MC never re-applies).
    """
    friction_pts = (side_friction_points(scn, adverse=False)
                    + side_friction_points(scn, adverse=stop_exit))
    return points_to_usd(friction_pts) + scn.platform_fee_rt_usd
