"""Session calendar for ITSF S0 (NQ opening drive).

All calendar tables (holidays / half-days / roll transitions / trading days)
are INJECTED. Tests use synthetic tables; real tables (pandas-market-calendars
CME Equity + CME notice check, frozen: S0 SS3) arrive later via the same ctor.

Frozen sources:
  # frozen: S0 SS1  (is_roll_transition / is_roll_window = transition +-2 RTH trading days)
  # frozen: S0 SS3  (ET timezone, RTH 09:30-16:00, obs 09:30-09:59, decision 10:00,
  #                  forced exit 15:44 bar, overnight prev 18:00 -> 09:30,
  #                  exclusion = ONLY {half-day, no RTH trades, >10% missing bars})
  # frozen: S0 SS4 ADR14 (mean RTH (high-low) of prior 14 complete days, excl today)
"""
from __future__ import annotations

from datetime import date as _date_cls, datetime, time
from zoneinfo import ZoneInfo

import pandas as pd

ET = ZoneInfo("America/New_York")  # frozen: S0 SS3

RTH_OPEN = time(9, 30)       # frozen: S0 SS3
RTH_CLOSE = time(16, 0)      # frozen: S0 SS3
OBS_END = time(10, 0)        # obs window = [09:30, 10:00) bar starts; frozen: S0 SS3
PM_END = time(15, 45)        # forced exit @ 15:44 bar close -> pm = [10:00, 15:45); frozen: S0 SS3
OVERNIGHT_START = time(18, 0)  # frozen: S0 SS3

EXPECTED_RTH_MINUTES = 390          # 09:30..15:59 inclusive, 1-min bars
MAX_MISSING_FRACTION = 0.10         # frozen: S0 SS3 (excluded iff missing > 10%)
ADR_LOOKBACK_DAYS = 14              # frozen: S0 SS4 ADR14
ROLL_WINDOW_TRADING_DAYS = 2        # frozen: S0 SS1

# Exclusion reason strings — frozen: S0 SS3, ONLY these three categories.
REASON_HALF_DAY = "half_day"
REASON_ZERO_BARS = "zero_bars"
REASON_MISSING_GT_10PCT = "missing_gt_10pct"


def _iso(d: str | _date_cls) -> str:
    """Normalize a date argument to 'YYYY-MM-DD'."""
    if isinstance(d, str):
        return d
    return d.isoformat()


class SessionCalendar:
    """Injected-table session calendar. Bar timestamps are tz-aware ET;
    'HH:MM bar' means the 1-minute bar STARTING at that instant (frozen: S0 SS1
    ts_event convention)."""

    def __init__(self, holidays: set[str], half_days: set[str],
                 roll_transitions: set[str], trading_days: list[str]):
        self.holidays = set(holidays)
        self.half_days = set(half_days)
        self.roll_transitions = set(roll_transitions)
        self.trading_days = list(trading_days)
        self._td_index = {d: i for i, d in enumerate(self.trading_days)}
        # Precompute roll-window membership: transition day +- 2 TRADING days,
        # positions taken from the injected trading_days ordering. frozen: S0 SS1
        self._roll_window_days: set[str] = set()
        for t in self.roll_transitions:
            self._roll_window_days.add(t)  # day 0 is within +-2
            i = self._td_index.get(t)
            if i is None:
                continue  # transition not in injected trading_days: flag day only
            lo = max(0, i - ROLL_WINDOW_TRADING_DAYS)
            hi = min(len(self.trading_days) - 1, i + ROLL_WINDOW_TRADING_DAYS)
            self._roll_window_days.update(self.trading_days[lo:hi + 1])

    # ---- time windows ------------------------------------------------------

    def _dt(self, date: str | _date_cls, t: time) -> datetime:
        d = _date_cls.fromisoformat(_iso(date))
        return datetime.combine(d, t, tzinfo=ET)

    def rth_window(self, date: str | _date_cls) -> tuple[datetime, datetime]:
        """RTH 09:30-16:00 ET that date (tz-aware). frozen: S0 SS3"""
        return self._dt(date, RTH_OPEN), self._dt(date, RTH_CLOSE)

    def prev_trading_day(self, date: str | _date_cls) -> str:
        """Previous trading day per the injected trading_days ordering."""
        d = _iso(date)
        i = self._td_index.get(d)
        if i is None:
            raise ValueError(f"{d} not in injected trading_days")
        if i == 0:
            raise ValueError(f"{d} has no prior trading day in injected trading_days")
        return self.trading_days[i - 1]

    def overnight_window(self, date: str | _date_cls) -> tuple[datetime, datetime]:
        """Overnight range window: prev trading day 18:00 ET -> date 09:30 ET.
        frozen: S0 SS3"""
        prev = self.prev_trading_day(date)
        return self._dt(prev, OVERNIGHT_START), self._dt(date, RTH_OPEN)

    # ---- bar slicing -------------------------------------------------------

    @staticmethod
    def _slice(bars_df: pd.DataFrame, start: datetime, end: datetime) -> pd.DataFrame:
        if bars_df is None or len(bars_df) == 0 or "ts" not in bars_df.columns:
            return bars_df.iloc[0:0] if bars_df is not None else pd.DataFrame(columns=["ts"])
        mask = (bars_df["ts"] >= start) & (bars_df["ts"] < end)
        return bars_df.loc[mask]

    def slice_rth(self, bars_df: pd.DataFrame, date: str | _date_cls) -> pd.DataFrame:
        """Bars with ts in [09:30, 16:00) — i.e. the 09:30..15:59 bars. frozen: S0 SS3"""
        start, end = self.rth_window(date)
        return self._slice(bars_df, start, end)

    def slice_obs(self, bars_df: pd.DataFrame, date: str | _date_cls) -> pd.DataFrame:
        """Observation window bars, ts in [09:30, 10:00) == 09:30..09:59 bars.
        frozen: S0 SS3"""
        return self._slice(bars_df, self._dt(date, RTH_OPEN), self._dt(date, OBS_END))

    def slice_pm(self, bars_df: pd.DataFrame, date: str | _date_cls) -> pd.DataFrame:
        """PM window bars, ts in [10:00, 15:45) == 10:00..15:44 bars (forced exit
        at the 15:44 bar close). frozen: S0 SS3"""
        return self._slice(bars_df, self._dt(date, OBS_END), self._dt(date, PM_END))

    # ---- exclusion (frozen: ONLY these three reasons, S0 SS3) --------------

    def is_excluded(self, date: str | _date_cls,
                    rth_bars: pd.DataFrame) -> tuple[bool, str]:
        """(excluded, reason). reason in {half_day, zero_bars, missing_gt_10pct}
        or '' when not excluded. NA policy (frozen: S0 SS3): NO other whole-day
        deletions are permitted — uncomputable features are recorded NA and the
        day stays in the sample."""
        d = _iso(date)
        if d in self.half_days:
            return True, REASON_HALF_DAY                    # frozen: S0 SS3
        bars = self.slice_rth(rth_bars, d)
        n = len(bars)
        if n == 0:
            return True, REASON_ZERO_BARS                   # frozen: S0 SS3 (RTH no trades)
        missing = EXPECTED_RTH_MINUTES - n
        if missing / EXPECTED_RTH_MINUTES > MAX_MISSING_FRACTION:
            return True, REASON_MISSING_GT_10PCT            # frozen: S0 SS3 (> 10%)
        return False, ""

    # ---- ADR14 -------------------------------------------------------------

    @staticmethod
    def adr14(prior_days_hl: list[tuple[float, float]]) -> float | None:
        """Mean of (RTH high - RTH low) over the LAST 14 complete prior days
        (current day excluded by construction — caller passes prior days only).
        None if fewer than 14 available. frozen: S0 SS4 ADR14"""
        if len(prior_days_hl) < ADR_LOOKBACK_DAYS:
            return None
        window = prior_days_hl[-ADR_LOOKBACK_DAYS:]
        return sum(h - l for h, l in window) / ADR_LOOKBACK_DAYS

    # ---- roll flags (frozen: S0 SS1) ---------------------------------------

    def is_roll_transition(self, date: str | _date_cls) -> bool:
        """True on the trading day the continuous mapping actually switches.
        frozen: S0 SS1"""
        return _iso(date) in self.roll_transitions

    def is_roll_window(self, date: str | _date_cls) -> bool:
        """True within transition day +- 2 TRADING days (trading_days ordering),
        inclusive of the transition day itself. frozen: S0 SS1"""
        return _iso(date) in self._roll_window_days
