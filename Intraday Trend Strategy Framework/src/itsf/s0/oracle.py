"""S0 dual oracle (# frozen: S0 SS7).

Direction is ALWAYS d_open (frozen). Day selection — the oracle trades only
continuation-event days (Y_cont >= theta) — happens UPSTREAM; these functions
never look at labels or any future information beyond the price path they are
explicitly given.
"""
from __future__ import annotations

import pandas as pd

from itsf.contracts import MNQ_POINT_VALUE_USD, CostScenarioParams, TradePathRecord
from itsf.s0 import costs, paths


def theoretical_oracle(day_bars: pd.DataFrame, d_open: int,
                       scenario: CostScenarioParams) -> float:
    """Theoretical oracle: ECONOMIC UPPER BOUND ONLY.  # frozen: S0 SS7

    Enter at the 10:00 bar open in direction d_open; exit at the most
    favourable in-window price (long: max high, short: min low; window =
    10:00 bar through the 15:44 forced-exit bar, inclusive), minus costs.
    The frozen text fixes BASE costs for this bound — the caller is expected
    to pass the Base scenario; this function applies whatever scenario it is
    given. Returns per-contract USD P&L with the platform fee deducted once
    (# frozen: platform_params execution_costs.s0_cost_handoff).
    """
    costs._check_d(d_open)
    entry_idx = paths.bar_index_at(day_bars, paths.ENTRY_TIME)
    end_idx = paths.bar_index_at(day_bars, paths.FORCED_EXIT_BAR_TIME)
    window = day_bars.iloc[entry_idx:end_idx + 1]

    entry_px = costs.scenario_entry_fill(float(window.iloc[0]["open"]), d_open, scenario)
    fav_px = float(window["high"].max()) if d_open == 1 else float(window["low"].min())
    exit_px = costs.scenario_timed_exit_fill(fav_px, d_open, scenario)
    return (d_open * (exit_px - entry_px) * MNQ_POINT_VALUE_USD
            - scenario.platform_fee_rt_usd)


def executable_run(day_bars: pd.DataFrame, d_open: int, engine: str,
                   scenario: CostScenarioParams,
                   or_high: float, or_low: float) -> TradePathRecord:
    """Executable oracle for one day.  # frozen: S0 SS7

    At most one trade, no overnight; entry at the 10:00 bar open +- costs.
    E1: live initial stop = opening-range (09:30-10:00) opposite extreme —
        long -> or_low, short -> or_high; unstopped positions exit at the
        15:44 bar close (frozen S0 SS3/SS7).
    E2: NO stop order, timed exit at the 15:44 bar close; the same
        opening-range level is passed down as the COUNTERFACTUAL E1 stop so
        sizing_anchor_usd is computed and stored even though no stop is
        placed (# frozen: MC SS3).
    d_open == 0 days are non-tradeable (frozen S0 SS5) -> ValueError.
    """
    costs._check_d(d_open)  # rejects d_open == 0 (no-direction day, frozen SS5)
    stop = or_low if d_open == 1 else or_high
    entry_idx = paths.bar_index_at(day_bars, paths.ENTRY_TIME)
    return paths.build_record(day_bars, entry_idx, d_open, engine, scenario,
                              planned_stop=stop)
