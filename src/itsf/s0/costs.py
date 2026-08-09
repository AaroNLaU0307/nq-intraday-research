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

import math
from collections.abc import Mapping, Sequence
from dataclasses import replace as _dc_replace

import numpy as np

from itsf.contracts import (
    AARON_RULED_ADVERSE_TICKS_SENSITIVITY,
    MNQ_POINT_VALUE_USD,
    MNQ_TICK_POINTS,
    S0_PLATFORM_FEE_RT_USD,
    CostScenarioParams,
    SpreadCostMethod,
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

    DR-1 / IR-7 (Aaron 2026-08-10): the RULED production path is
    `build_scenarios_from_method`, which sources the adverse vector from the
    ruled `SpreadCostMethod` instead of from the defaults below and asserts
    that Stress's friction multiplier reaches the adverse ticks exactly once.
    THIS function keeps its un-ruled defaults and stays in place only for the
    callers that have not migrated yet; a run must not quote its numbers.
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


# ===========================================================================
# DR-1 (Aaron 2026-08-10) — this module is the production CONSUMER of the
# ruled `contracts.SpreadCostMethod`.
#
# Every function below takes the method dataclass as an EXPLICIT parameter and
# dispatches on its fields. Nothing defaults to a ruled value and nothing
# re-states one: the numbers come off `method`, and the only ruled STRINGS that
# appear here are DISPATCH KEYS — the exact rule ids this module implements.
# An unknown/un-ruled string is a ValueError with a precise code, never a
# silent fallback (fail closed).
# ===========================================================================

#: Column names of the derived spread table (produced by
#: `itsf.data.cost_calibration_loader.CostCalibrationLoader._spread_table`,
#: whose SPREAD_TABLE_COLUMNS is the authority). Named here rather than
#: imported so this module never pulls the raw-data loader (and its role
#: guards) into the compute path's import graph.
SPREAD_TABLE_MINUTE_COLUMN = "minute_of_day_et"
SPREAD_TABLE_TRIPLE_COLUMNS = ("spread_median_points", "spread_p90_points",
                               "spread_p95_points")

#: Rule B-i trading-window slot bounds, minute-of-day ET, INCLUSIVE. 600 ==
#: 10:00 (the entry minute) and 944 == 15:44 (the last minute an exit or a
#: stop can fill), so these are exactly the slots at which a fill can occur.
#: Slots outside the window contribute NOTHING to the scalars.
TRADING_WINDOW_MINUTE_LO = 600
TRADING_WINDOW_MINUTE_HI = 944

#: DISPATCH KEY, not a default: the exact `SpreadCostMethod.scalar_rule`
#: string this module implements. `derive_spread_scalars` requires the
#: caller's ruled method and refuses every other rule id — no code path
#: selects this value on its own.
SPREAD_SCALAR_RULE_B_I = "B_i_trading_window_q50med_q50p90_q50p95"

#: The cross-slot reduction of rule B-i: the median (Q50) over the in-window
#: SLOTS, taken separately in each of the three columns, equal-weighted (n_obs
#: is deliberately NOT a weight), numpy `method="linear"`, and NO rounding.
SPREAD_SCALAR_QUANTILE = 50.0
SPREAD_SCALAR_PERCENTILE_METHOD = "linear"

#: DISPATCH KEY for `SpreadCostMethod.adverse_semantics`: on a stop fill the
#: adverse ticks REPLACE the regular per-side slip (they are not added to it).
#: That is what `side_friction_points(scn, adverse=True)` has always done;
#: this constant makes the semantics checkable instead of implied.
ADVERSE_SEMANTICS_REPLACES_PER_SIDE = "replaces_per_side"

#: Selectable adverse-slippage channels. "primary" is the ruled IR-7 Option i
#: vector carried on the method; "sensitivity_plus1" is the IR-7 Option ii
#: SENSITIVITY vector and can only ever be reached by naming it explicitly.
ADVERSE_CHANNEL_PRIMARY = "primary"
ADVERSE_CHANNEL_SENSITIVITY = "sensitivity_plus1"

#: frozen: S0 §6 — the four cost scenarios `build_scenarios` returns.
SCENARIO_NAMES = ("Base", "Conservative", "Stress", "Severe")


def _require_spread_cost_method(method) -> SpreadCostMethod:
    if not isinstance(method, SpreadCostMethod):
        raise ValueError(
            "spread_cost_method_not_a_SpreadCostMethod:"
            f"{type(method).__name__}")
    return method


def _spread_table_columns(table) -> dict[str, np.ndarray]:
    """Normalise an accepted spread-table shape to {column: float64 1-D}.

    Accepted, all yielding identical arrays: a pandas DataFrame (anything with
    `.columns` and `table[name]`), a Mapping column -> sequence, or a Sequence
    of row Mappings. Fail closed on a missing column, a ragged/empty table or a
    non-numeric column — never a partial read.
    """
    needed = (SPREAD_TABLE_MINUTE_COLUMN,) + SPREAD_TABLE_TRIPLE_COLUMNS
    raw: dict[str, object] = {}
    if hasattr(table, "columns") and hasattr(table, "__getitem__"):
        names = {str(c) for c in table.columns}
        for want in needed:
            if want not in names:
                raise ValueError(f"spread_table_missing_column:{want}")
            raw[want] = table[want]
    elif isinstance(table, Mapping):
        for want in needed:
            if want not in table:
                raise ValueError(f"spread_table_missing_column:{want}")
            raw[want] = table[want]
    elif isinstance(table, Sequence) and not isinstance(table, (str, bytes)):
        rows = list(table)
        if not rows:
            raise ValueError("spread_table_empty")
        for want in needed:
            values = []
            for row in rows:
                if not isinstance(row, Mapping) or want not in row:
                    raise ValueError(f"spread_table_missing_column:{want}")
                values.append(row[want])
            raw[want] = values
    else:
        raise ValueError(
            f"spread_table_shape_unsupported:{type(table).__name__}")

    out: dict[str, np.ndarray] = {}
    for want in needed:
        try:
            arr = np.asarray(raw[want], dtype=float)
        except (TypeError, ValueError):
            raise ValueError(
                f"spread_table_column_not_numeric:{want}") from None
        if arr.ndim != 1:
            raise ValueError(f"spread_table_column_not_1d:{want}")
        out[want] = arr
    sizes = {int(v.size) for v in out.values()}
    if len(sizes) != 1:
        raise ValueError("spread_table_ragged_columns")
    if sizes == {0}:
        raise ValueError("spread_table_empty")
    return out


def derive_spread_scalars(table, method: SpreadCostMethod
                          ) -> tuple[float, float, float]:
    """The ruled DR-1 `(median, P90, P95)` spread scalars, in index points.

    Rule ``B_i_trading_window_q50med_q50p90_q50p95`` (Aaron 2026-08-10),
    implemented exactly:

      1. keep only the per-minute SLOTS whose ``minute_of_day_et`` lies in
         ``[600, 944]`` INCLUSIVE — 10:00 through 15:44, the only minutes at
         which an entry, a timed exit or a stop can fill. Every other slot is
         EXCLUDED and can never move the result;
      2. the triple is ``(Q50 over slots of spread_median_points,
         Q50 over slots of spread_p90_points,
         Q50 over slots of spread_p95_points)`` — three separate cross-slot
         medians, never a median of medians of a pooled column;
      3. slots are EQUAL-WEIGHT. ``n_obs`` is read by nothing here: a busy
         minute does not out-vote a quiet one under this ruling;
      4. ``numpy.percentile(..., 50.0, method="linear")`` — the endpoint sits
         at virtual index ``(m-1)/2`` of the sorted slot values and is
         linearly interpolated between neighbours on an even slot count;
      5. NO rounding of any kind — not to a tick, not to a decimal place.

    `method` is the ruled `contracts.SpreadCostMethod`; the rule id is read
    off it and any other value raises
    ``ValueError("spread_scalar_rule_not_ruled:<value>")``. There is no
    default rule and no fallback path.

    The returned triple satisfies ``0 <= median <= P90 <= P95``: the ordering
    is pointwise per slot in the input table and the median is monotone, so a
    violation means the TABLE is defective and is refused here (fail closed)
    rather than travelling into a `StudyConfig`.
    """
    _require_spread_cost_method(method)
    rule = method.scalar_rule
    if not isinstance(rule, str) or rule != SPREAD_SCALAR_RULE_B_I:
        raise ValueError(f"spread_scalar_rule_not_ruled:{rule}")

    cols = _spread_table_columns(table)
    minutes = cols[SPREAD_TABLE_MINUTE_COLUMN]
    if not np.all(np.isfinite(minutes)):
        raise ValueError("spread_table_minute_non_finite")
    if not np.all(minutes == np.round(minutes)):
        raise ValueError("spread_table_minute_not_integral")
    if np.unique(minutes).size != minutes.size:
        raise ValueError("spread_table_duplicate_minute_slot")

    in_window = ((minutes >= TRADING_WINDOW_MINUTE_LO)
                 & (minutes <= TRADING_WINDOW_MINUTE_HI))
    n_slots = int(np.count_nonzero(in_window))
    if n_slots == 0:
        raise ValueError(
            "spread_table_no_slots_in_trading_window:"
            f"[{TRADING_WINDOW_MINUTE_LO},{TRADING_WINDOW_MINUTE_HI}]")

    triple: list[float] = []
    for name in SPREAD_TABLE_TRIPLE_COLUMNS:
        values = cols[name][in_window]
        if not np.all(np.isfinite(values)):
            raise ValueError(f"spread_table_non_finite_in_window:{name}")
        if np.any(values < 0.0):
            raise ValueError(f"spread_table_negative_spread:{name}")
        triple.append(float(np.percentile(
            values, SPREAD_SCALAR_QUANTILE,
            method=SPREAD_SCALAR_PERCENTILE_METHOD)))

    median, p90, p95 = triple
    if not (0.0 <= median <= p90 <= p95):
        raise ValueError(
            "spread_scalars_not_ordered_median_le_p90_le_p95:"
            f"{median},{p90},{p95}")
    return (median, p90, p95)


def effective_adverse_ticks(scn: CostScenarioParams) -> float:
    """The adverse-slippage ticks a stop fill ACTUALLY pays under `scn`.

    Every consumer of the stop path (`scenario_stop_fill`,
    `side_friction_points(..., adverse=True)`, `paths.py`'s anchor stop and
    `evidence.py`'s independent EV-4 recompute) prices the adverse side as
    ``friction_multiplier * (spread/2 + adverse_slippage_ticks * TICK)``. So
    the FIELD is a PRE-multiplier tick count and the EFFECTIVE tick count is
    the product — this function is the single place that says so.

    `build_scenarios_from_method` uses it as a post-condition: the effective
    value must equal the ruled per-scenario number exactly. That is what stops
    Stress (ruled EFFECTIVE 2.0 = Base 1 x2) from being multiplied by its own
    friction_multiplier a SECOND time into 4.0.
    """
    return float(scn.friction_multiplier) * float(scn.adverse_slippage_ticks)


def adverse_ticks_for_channel(method: SpreadCostMethod, adverse_channel: str
                              ) -> dict[str, float]:
    """EFFECTIVE per-scenario adverse ticks for an explicitly named channel.

    ``"primary"``          -> `method.adverse_slippage_ticks` (the ruled IR-7
                              Option i vector; Stress already carries its x2).
    ``"sensitivity_plus1"``-> `contracts.AARON_RULED_ADVERSE_TICKS_SENSITIVITY`
                              (IR-7 Option ii). NEVER Primary, and reachable
                              only by naming this string.
    Anything else raises ``ValueError("adverse_channel_not_ruled:<value>")``.
    """
    _require_spread_cost_method(method)
    if adverse_channel == ADVERSE_CHANNEL_PRIMARY:
        source = method.adverse_slippage_ticks
    elif adverse_channel == ADVERSE_CHANNEL_SENSITIVITY:
        source = AARON_RULED_ADVERSE_TICKS_SENSITIVITY
    else:
        raise ValueError(f"adverse_channel_not_ruled:{adverse_channel}")
    if not isinstance(source, Mapping):
        raise ValueError("adverse_slippage_ticks_not_a_mapping")
    ticks: dict[str, float] = {}
    for name in SCENARIO_NAMES:
        if name not in source:
            raise ValueError(f"adverse_slippage_ticks_missing_scenario:{name}")
        value = source[name]
        if (isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(float(value)) or float(value) < 0.0):
            raise ValueError(
                f"adverse_slippage_ticks_value_invalid:{name}")
        ticks[name] = float(value)
    extra = sorted(set(map(str, source)) - set(SCENARIO_NAMES))
    if extra:
        raise ValueError(
            f"adverse_slippage_ticks_unknown_scenario:{','.join(extra)}")
    return ticks


def build_scenarios_from_method(spread_scalars,
                                method: SpreadCostMethod, *,
                                adverse_channel: str = ADVERSE_CHANNEL_PRIMARY,
                                platform_fee_rt_usd: float
                                = S0_PLATFORM_FEE_RT_USD,
                                ) -> dict[str, CostScenarioParams]:
    """The four frozen §6 scenarios with the RULED adverse-slippage vector.

    THE ONE THING THIS FUNCTION EXISTS FOR. `build_scenarios`' per-scenario
    `adverse_slippage_ticks` defaults are an un-ruled coding convention, and
    the naive fix — passing the ruled EFFECTIVE vector straight through —
    silently DOUBLE-COUNTS Stress: the field is a PRE-multiplier tick count
    (see `effective_adverse_ticks`), so a stored 2.0 becomes 4.0 effective
    ticks under `friction_multiplier=2.0`. Here the ruled effective value is
    divided by the scenario's own multiplier before storage and the
    post-condition ``effective_adverse_ticks(scn) == ruled[name]`` is then
    ASSERTED for all four scenarios. Stress's friction multiplier is therefore
    applied to the adverse ticks exactly once, by the fill formulas, never
    twice.

    No fill formula is touched: `entry_fill` / `timed_exit_fill` / `stop_fill`
    and their scenario wrappers are unchanged. Only the SOURCE of the tick
    values changes — from module-local defaults to the ruled method.

    `adverse_channel` is an explicit keyword defaulting to Primary; the
    sensitivity vector cannot be reached without naming it (see
    `adverse_ticks_for_channel`).
    """
    _require_spread_cost_method(method)
    semantics = method.adverse_semantics
    if (not isinstance(semantics, str)
            or semantics != ADVERSE_SEMANTICS_REPLACES_PER_SIDE):
        raise ValueError(f"adverse_semantics_not_ruled:{semantics}")

    scalars = tuple(spread_scalars)
    if len(scalars) != 3:
        raise ValueError(f"spread_scalars_wrong_length:{len(scalars)}")
    values = []
    for i, v in enumerate(scalars):
        if (isinstance(v, bool) or not isinstance(v, (int, float))
                or not math.isfinite(float(v)) or float(v) < 0.0):
            raise ValueError(f"spread_scalars_value_invalid:{i}")
        values.append(float(v))
    if not (values[0] <= values[1] <= values[2]):
        raise ValueError(
            "spread_scalars_not_ordered_median_le_p90_le_p95:"
            f"{values[0]},{values[1]},{values[2]}")

    ruled_effective = adverse_ticks_for_channel(method, adverse_channel)
    built = build_scenarios(*values, platform_fee_rt_usd=platform_fee_rt_usd)
    out: dict[str, CostScenarioParams] = {}
    for name in SCENARIO_NAMES:
        scn = built[name]
        mult = float(scn.friction_multiplier)
        if not math.isfinite(mult) or mult <= 0.0:
            raise ValueError(f"friction_multiplier_invalid:{name}")
        stored = ruled_effective[name] / mult
        out[name] = _dc_replace(scn, adverse_slippage_ticks=stored)
    for name in SCENARIO_NAMES:
        got = effective_adverse_ticks(out[name])
        want = ruled_effective[name]
        if not math.isclose(got, want, rel_tol=1e-12, abs_tol=1e-12):
            raise RuntimeError(
                "build_scenarios_from_method: effective adverse ticks for "
                f"{name} came out {got!r}, ruled value is {want!r} — the "
                "friction multiplier was applied to the adverse ticks a "
                "second time (double count); this is a bug, never a config")
    return out


def adverse_ticks_disclosure(scenarios: dict[str, CostScenarioParams],
                             method: SpreadCostMethod,
                             adverse_channel: str = ADVERSE_CHANNEL_PRIMARY,
                             ) -> dict[str, object]:
    """Report-facing disclosure of what the adverse channel actually did.

    Carries the stored (pre-multiplier) field, the friction multiplier and the
    EFFECTIVE ticks side by side, so a reader can see for themselves that
    Stress's x2 was applied once. Reads scenarios and method only; computes no
    fill and holds no threshold.
    """
    ruled = adverse_ticks_for_channel(method, adverse_channel)
    return {
        "adverse_channel": adverse_channel,
        "adverse_semantics": method.adverse_semantics,
        "scalar_rule": method.scalar_rule,
        "ruled_effective_ticks": dict(ruled),
        "per_scenario": {
            name: {
                "stored_pre_multiplier_ticks":
                    float(scenarios[name].adverse_slippage_ticks),
                "friction_multiplier":
                    float(scenarios[name].friction_multiplier),
                "effective_ticks": effective_adverse_ticks(scenarios[name]),
                "per_side_slippage_ticks":
                    float(scenarios[name].slippage_ticks_per_side),
            }
            for name in SCENARIO_NAMES if name in scenarios},
        "note": (
            "adverse ticks REPLACE the regular per-side slip on a stop fill "
            "(they are not added to it); the friction multiplier is applied "
            "to them exactly once, by the fill formulas"),
    }
