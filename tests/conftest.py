"""Shared synthetic fixtures (MAIN-AGENT OWNED, read-only for subagents).

Real market data is FORBIDDEN in this phase (G9 hard_run_blocker + second-copy
gate). All tests build days from these deterministic generators.
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

import pandas as pd  # noqa: E402

ET = ZoneInfo("America/New_York")


def make_minute_bars(date: str, pattern: str = "trend_up",
                     start: str = "09:30", end: str = "16:00",
                     base_price: float = 20000.0, step: float = 1.0,
                     volume: int = 100) -> pd.DataFrame:
    """Deterministic 1-min bars, ET session. Patterns:
    trend_up   : close rises `step`/min, low=open-1t, high=close+1t
    trend_down : mirror of trend_up
    chop       : alternates +step/-step, net ~0
    spike_down : trend_up but one deep intraminute low at minute 61 (10:31)
    """
    d = datetime.fromisoformat(date)
    t0 = d.replace(hour=int(start[:2]), minute=int(start[3:]), tzinfo=ET)
    t1 = d.replace(hour=int(end[:2]), minute=int(end[3:]), tzinfo=ET)
    rows = []
    px = base_price
    i = 0
    t = t0
    while t < t1:
        if pattern == "trend_up":
            o, c = px, px + step
        elif pattern == "trend_down":
            o, c = px, px - step
        elif pattern == "chop":
            o, c = px, px + (step if i % 2 == 0 else -step)
        elif pattern == "spike_down":
            o, c = px, px + step
        else:
            raise ValueError(pattern)
        h, l = max(o, c) + 0.25, min(o, c) - 0.25
        if pattern == "spike_down" and i == 61:
            l = min(o, c) - 40 * step        # deep intraminute adverse spike
        rows.append({"ts": t, "open": o, "high": h, "low": l, "close": c,
                     "volume": volume})
        px = c
        i += 1
        t += timedelta(minutes=1)
    return pd.DataFrame(rows)


def make_overnight_bars(date: str, high: float = 20010.0, low: float = 19990.0,
                        base_price: float = 20000.0) -> pd.DataFrame:
    """Minimal overnight window (prev 18:00 -> 09:30) with a given range."""
    prev = datetime.fromisoformat(date) - timedelta(days=1)
    t = prev.replace(hour=18, minute=0, tzinfo=ET)
    rows = [
        {"ts": t, "open": base_price, "high": high, "low": low,
         "close": base_price, "volume": 10},
    ]
    return pd.DataFrame(rows)


def make_trade_path(pnl_per_min: list[float], adverse_extra: float = 0.0,
                    date: str = "2026-08-03", engine: str = "E1",
                    direction: int = 1, final: float | None = None):
    """Quick TradePathRecord for platform/MC tests."""
    from itsf.contracts import TradePathRecord
    close = list(pnl_per_min)
    adverse = [p - abs(adverse_extra) for p in close]
    return TradePathRecord(
        trade_date=date, engine=engine, cost_scenario="Conservative",
        direction=direction, entry_ts=f"{date}T10:00:00-04:00",
        exit_ts=f"{date}T15:44:00-04:00",
        entry_fill=20000.0, exit_fill=20000.0 + (close[-1] if close else 0.0) / 2.0,
        final_pnl_per_contract=final if final is not None else (close[-1] if close else 0.0),
        mtm_close_pnl_1m=close, mtm_adverse_pnl_1m=adverse,
        max_adverse_pnl=min(adverse) if adverse else 0.0,
        max_favourable_pnl=max(close) if close else 0.0,
        time_of_max_adverse="", planned_stop=None, actual_stop_fill=None,
        stop_triggered=False, sizing_anchor_usd=100.0)
