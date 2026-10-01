"""S0 per-contract intraday trade-path builder -> TradePathRecord.

Mark-to-market convention (stated per instruction; # frozen: S0 SS10.1):
- Both 1-minute arrays are USD P&L per 1 MNQ contract of the OPEN position,
  marked against the friction-inclusive entry fill (entry-side friction is
  therefore included from the first element on; at the entry instant the
  position marks at minus the entry friction).
- mtm_close_pnl_1m[t]   marks at the bar CLOSE.
- mtm_adverse_pnl_1m[t] marks at the bar's most adverse extreme: minute LOW
  for longs, minute HIGH for shorts (frozen SS10.1).
- Exit-side friction enters ONLY at the exit element:
  * Stop bar (E1): both arrays' last element = realized P&L at the stop fill.
    Frozen SS10.1 text: the stop bar's adverse mark truncates at the stop
    fill level (worst case realized) and later minutes are dropped. The
    close-path element of that bar is set to the same realized level because
    the position no longer exists at the bar close (stated convention).
  * Timed-exit bar (15:44): close element = realized P&L at the timed exit
    fill; adverse element = the WORSE of (intraminute extreme mark, realized
    exit) — the position is open during that minute and SS10.1 mandates the
    account-unfavourable reading when intraminute order is unknown.
- The platform fee (1.74 RT) is NOT in the arrays; it is deducted exactly
  once in final_pnl_per_contract (contracts.TradePathRecord field comment;
  # frozen: platform_params execution_costs.s0_cost_handoff).
- Arrays start at the entry bar (10:00) and, when an E1 stop triggers on bar
  j (relative index r = j - entry_idx), truncate to length r + 1.
- A live E1 stop order fills on any intrabar touch, so on the 15:44 bar the
  stop check precedes the timed exit.
"""
from __future__ import annotations

from datetime import time as dtime

import pandas as pd

from itsf.contracts import MNQ_POINT_VALUE_USD, CostScenarioParams, TradePathRecord
from itsf.s0 import costs

ENTRY_TIME = dtime(10, 0)         # frozen: S0 SS3/SS7 — entry at the 10:00 bar open
FORCED_EXIT_BAR_TIME = dtime(15, 44)  # frozen: S0 SS3 — timed exit at the 15:44 bar close


def bar_index_at(day_bars: pd.DataFrame, t: dtime) -> int:
    """First positional index whose bar-start wall-clock time == t
    (bars carry ET tz per frozen S0 SS3 / SS1 ts_event convention)."""
    for i, ts in enumerate(day_bars["ts"]):
        if ts.time() == t:
            return i
    raise ValueError(f"no bar starting at {t} in day_bars")


def sizing_anchor_usd(entry_px: float, planned_stop: float, d: int,
                      scn: CostScenarioParams) -> float:
    """Planned per-contract USD risk of the E1 stop, costs included.

    Assumes a NORMAL intrabar stop touch (trigger_ref = stop, no gap-through)
    plus adverse-slippage exit friction and the platform fee once — i.e.
    S0 SS8 `risk_usd_per_1_MNQ_planned`.  # frozen: S0 SS8; MC SS3 (E1 anchor
    = actual planned stop distance incl cost; E2 anchor = the SAME formula on
    the counterfactual E1 stop — no stop order is placed).
    """
    costs._check_d(d)
    normal_stop_px = planned_stop - d * costs.side_friction_points(scn, adverse=True)
    return d * (entry_px - normal_stop_px) * MNQ_POINT_VALUE_USD + scn.platform_fee_rt_usd


def build_record(day_bars_pm: pd.DataFrame, entry_idx: int, direction: int,
                 engine: str, scenario: CostScenarioParams,
                 planned_stop: float | None = None) -> TradePathRecord:
    """Build the frozen SS10.1 atomic per-contract TradePathRecord.

    day_bars_pm: 1-minute bars (ts/open/high/low/close) covering at least the
    entry bar through the 15:44 bar; entry_idx must point at the 10:00 bar.
    E1: planned_stop is the live stop order (opening-range opposite extreme,
        frozen S0 SS7); arrays truncate at the stop bar.
    E2: NO stop order is placed; planned_stop is interpreted as the
        counterfactual E1 stop used ONLY for sizing_anchor_usd
        (# frozen: MC SS3) and the record's planned_stop field is stored as
        None (stated convention: no stop was planned/ordered).
    """
    costs._check_d(direction)
    if engine not in ("E1", "E2"):
        raise ValueError(f"engine must be 'E1' or 'E2', got {engine!r}")
    if planned_stop is None:
        # Needed for the sizing anchor under BOTH engines (frozen: MC SS3).
        raise ValueError("planned_stop required: E1 live stop / E2 counterfactual anchor")

    d = direction
    entry_row = day_bars_pm.iloc[entry_idx]
    if entry_row["ts"].time() != ENTRY_TIME:
        raise ValueError(f"entry_idx must point at the {ENTRY_TIME} bar, "
                         f"got {entry_row['ts']}")  # frozen: S0 SS3/SS7
    end_idx = bar_index_at(day_bars_pm, FORCED_EXIT_BAR_TIME)
    if end_idx < entry_idx:
        raise ValueError("15:44 bar precedes entry bar")

    pv = MNQ_POINT_VALUE_USD
    entry_px = costs.scenario_entry_fill(float(entry_row["open"]), d, scenario)

    mtm_close: list[float] = []
    mtm_adverse: list[float] = []
    stop_triggered = False
    actual_stop_fill: float | None = None
    exit_row = entry_row
    exit_px = entry_px
    realized = 0.0
    # Ruling R4 (ADJUDICATIONS.md): max_favourable is EXTREME-based, symmetric
    # with the adverse convention (minute high for long / low for short) on
    # open minutes; on stop/exit bars only the realized value is credited
    # (account-unfavourable reading: unproven favourable order not credited).
    max_favourable = float("-inf")

    for i in range(entry_idx, end_idx + 1):
        row = day_bars_pm.iloc[i]
        if engine == "E1" and not stop_triggered:
            touched = (float(row["low"]) <= planned_stop if d == 1
                       else float(row["high"]) >= planned_stop)
            if touched:
                # frozen: S0 SS6 — gap-through trigger_ref via min/max(stop, bar_open)
                exit_px = costs.scenario_stop_fill(planned_stop, float(row["open"]),
                                                   d, scenario)
                realized = d * (exit_px - entry_px) * pv
                # frozen: S0 SS10.1 — adverse mark truncates at the stop fill
                # (worst case realized); arrays end at this bar.
                mtm_close.append(realized)
                mtm_adverse.append(realized)
                max_favourable = max(max_favourable, realized)
                stop_triggered = True
                actual_stop_fill = exit_px
                exit_row = row
                break
        close_mark = d * (float(row["close"]) - entry_px) * pv
        adverse_extreme = float(row["low"]) if d == 1 else float(row["high"])
        adverse_mark = d * (adverse_extreme - entry_px) * pv
        fav_extreme = float(row["high"]) if d == 1 else float(row["low"])
        fav_mark = d * (fav_extreme - entry_px) * pv
        if i == end_idx:
            # frozen: S0 SS3/SS7 — forced timed exit at the 15:44 bar close
            exit_px = costs.scenario_timed_exit_fill(float(row["close"]), d, scenario)
            realized = d * (exit_px - entry_px) * pv
            mtm_close.append(realized)
            # frozen: S0 SS10.1 — account-unfavourable reading intraminute
            mtm_adverse.append(min(adverse_mark, realized))
            max_favourable = max(max_favourable, realized)
            exit_row = row
        else:
            mtm_close.append(close_mark)
            mtm_adverse.append(adverse_mark)
            max_favourable = max(max_favourable, fav_mark)

    # frozen: platform_params execution_costs.s0_cost_handoff — 1.74 RT
    # deducted exactly ONCE here; MC must not re-apply. NOT multiplied by
    # friction_multiplier (frozen: S0 SS6 Stress rule).
    final_pnl = realized - scenario.platform_fee_rt_usd

    max_adverse = min(mtm_adverse)
    idx_ma = mtm_adverse.index(max_adverse)  # first occurrence on ties
    # max_favourable accumulated in the loop (ruling R4, extreme-based)

    return TradePathRecord(
        trade_date=str(entry_row["ts"].date()),
        engine=engine,
        cost_scenario=scenario.name,
        direction=d,
        entry_ts=entry_row["ts"].isoformat(),
        exit_ts=exit_row["ts"].isoformat(),
        entry_fill=entry_px,
        exit_fill=exit_px,
        final_pnl_per_contract=final_pnl,
        mtm_close_pnl_1m=mtm_close,
        mtm_adverse_pnl_1m=mtm_adverse,
        max_adverse_pnl=max_adverse,
        max_favourable_pnl=max_favourable,
        time_of_max_adverse=day_bars_pm.iloc[entry_idx + idx_ma]["ts"].isoformat(),
        planned_stop=planned_stop if engine == "E1" else None,
        actual_stop_fill=actual_stop_fill,
        stop_triggered=stop_triggered,
        sizing_anchor_usd=sizing_anchor_usd(entry_px, planned_stop, d, scenario),
        ambiguous_stop_vs_floor=False,  # stop-vs-MLL ordering is MC's concern
    )
