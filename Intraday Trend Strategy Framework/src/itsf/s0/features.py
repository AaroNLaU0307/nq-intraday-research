"""S0 SS4 features F1-F11 on pre-sliced observation-window bars.

Subagent-owned module (ownership: features.py / labels.py + their tests).
Formulas are transcribed verbatim from the frozen STUDY_0_PREREGISTRATION.md
(tag s0-freeze-v1) SS4; NA policy from SS3. ``None`` == NA: the day STAYS in
the sample and per-table NA counts are reported downstream (frozen: S0 SS3).

Scope boundaries (deliberate):
- Inputs are pre-sliced by the calendar layer. ``obs_bars`` must already be
  the 09:30..09:59 1-min bars (bar convention: "HH:MM bar" starts at that
  minute — frozen: S0 SS1). This module does no session slicing.
- Exclusion-day logic (half-day / RTH no-trade / >10% missing bars —
  frozen: S0 SS3) is decided upstream; this module never drops a day and
  leaves ``excluded_day``/``exclusion_reason`` at their defaults.
- No real market data may flow through here before
  ``itsf.guards.assert_real_run_allowed()`` passes (main-agent owned gate).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from itsf.contracts import DayFeatures

# frozen: S0 SS4 F10 - closed event set {CPI, NFP, FOMC, none}
EVENT_FLAGS = ("CPI", "NFP", "FOMC", "none")


def _sign(x: float) -> int:
    """Strict sign: +1 / -1, and 0 only when exactly 0 (frozen: S0 SS5)."""
    return (x > 0) - (x < 0)


def compute_day_features(
    obs_bars: pd.DataFrame,
    overnight_hl: tuple[float, float] | None,
    adr14: float | None,
    prior_rth_close: float | None,
    rvol_median60: float | None,
    event_flag: str | None,
    is_roll_transition: bool,
    is_roll_window: bool,
) -> DayFeatures:
    """Compute DayFeatures (S0 SS4) for one trading day.

    Parameters are the pre-computed per-day context; ``obs_bars`` is the
    09:30..09:59 1-min OHLCV frame with a tz-aware ``ts`` column.
    """
    if event_flag is not None and event_flag not in EVENT_FLAGS:
        # frozen: S0 SS4 F10 - is_event_day must be one of {CPI, NFP, FOMC, none}
        # None == NA on an IR-12/18 multi-event day (M5-T0: contracts already
        # widened DayFeatures.is_event_day to `str | None`; this guard is the
        # single sanctioned edit to this module).
        raise ValueError(f"event_flag {event_flag!r} not in {EVENT_FLAGS}")
    if obs_bars is None or len(obs_bars) == 0:
        raise ValueError(
            "obs_bars must be non-empty; RTH no-trade days are exclusion "
            "days handled upstream (frozen: S0 SS3)")

    bars = obs_bars.sort_values("ts").reset_index(drop=True)
    trade_date = bars["ts"].iloc[0].date().isoformat()

    # frozen: S0 SS1 bar convention - O0930 = open of the 09:30 bar,
    # C0959 = close of the 09:59 bar (last observation-window bar).
    o0930 = float(bars["open"].iloc[0])
    c0959 = float(bars["close"].iloc[-1])
    closes = bars["close"].to_numpy(dtype=float)

    # ADR14 = mean of prior 14 complete RTH days' (high - low), excl. today
    # (frozen: S0 SS4 header). Missing or degenerate (<= 0) ADR14 makes every
    # /ADR14 feature NA; the day stays in sample (frozen: S0 SS3 NA policy).
    adr_ok = adr14 is not None and adr14 > 0

    # F1 ret_open30 = (C0959 - O0930) / ADR14           # frozen: S0 SS4 F1
    ret_open30 = (c0959 - o0930) / adr14 if adr_ok else None

    # F2 or_width = (H - L)_{09:30-10:00} / ADR14       # frozen: S0 SS4 F2
    win_h = float(bars["high"].max())
    win_l = float(bars["low"].min())
    or_width = (win_h - win_l) / adr14 if adr_ok else None

    # F3 de_open30 - close-path version ONLY (minute high/low forbidden):
    #   path_open30 = |C0930 - O0930| + sum_{t=09:31..09:59} |C_t - C_{t-1}|
    #   de_open30   = |C0959 - O0930| / path_open30
    # frozen: S0 SS4 F3 (verbatim). path_open30 == 0 -> NA (S0 SS3 NA policy).
    path_open30 = abs(closes[0] - o0930) + float(np.abs(np.diff(closes)).sum())
    de_open30 = (abs(c0959 - o0930) / path_open30) if path_open30 > 0 else None

    # F4 rvol_open30 = Vol(09:30-10:00) / prior-60-trading-day same-window
    # median                                            # frozen: S0 SS4 F4
    # Missing/degenerate median -> NA (frozen: S0 SS3). Roll-window layered
    # interpretation happens at reporting level, not here.
    obs_vol = float(bars["volume"].sum())
    if rvol_median60 is not None and rvol_median60 > 0:
        rvol_open30 = obs_vol / rvol_median60
    else:
        rvol_open30 = None

    # F5 gap = (O0930 - prior-day RTH close) / ADR14; is_roll_transition day
    # -> NA                                             # frozen: S0 SS4 F5
    if is_roll_transition or prior_rth_close is None or not adr_ok:
        gap = None
    else:
        gap = (o0930 - prior_rth_close) / adr14

    # F6 open_loc_on = (O0930 - ON_low) / (ON_high - ON_low)
    #                                                   # frozen: S0 SS4 F6
    # F7 on_range = (ON_high - ON_low) / ADR14          # frozen: S0 SS4 F7
    # Overnight window = prev 18:00 -> today 09:30 (frozen: S0 SS3).
    # Ruling R3 (ADJUDICATIONS.md, adopts audit finding): zero overnight range
    # makes F6 NA (0/0 undefined) but F7 = 0.0 per the LITERAL frozen formula
    # (no division-by-range involved). Missing overnight data -> both NA.
    # The above/inside/below category of F6 has no DayFeatures field; it is
    # derivable downstream (>1 above, <0 below, else inside).
    open_loc_on: float | None = None
    on_range: float | None = None
    if overnight_hl is not None:
        on_high, on_low = float(overnight_hl[0]), float(overnight_hl[1])
        on_rng = on_high - on_low
        on_range = (on_rng / adr14) if adr_ok else None
        if on_rng > 0:
            open_loc_on = (o0930 - on_low) / on_rng

    # F8 retrace_open30 - directional running-max drawdown (verbatim):
    #   z_t = d_open x (C_t - O0930),  t in [09:30..09:59]
    #   max_retrace    = max_t [ max_{u<=t}(z_u) - z_t ]
    #   retrace_open30 = max_retrace / |C0959 - O0930|   (denominator 0 -> NA)
    # frozen: S0 SS4 F8. d_open = sign(ret_open30) (frozen: S0 SS5); since
    # ADR14 > 0, that equals sign(C0959 - O0930), which is used here so F8
    # does not depend on ADR14 availability (scale-invariant; interpretation
    # noted in the subagent report).
    raw_move = c0959 - o0930
    if raw_move == 0:
        retrace_open30 = None
    else:
        z = _sign(raw_move) * (closes - o0930)
        running_max = np.maximum.accumulate(z)
        retrace_open30 = float(np.max(running_max - z)) / abs(raw_move)

    # F9 close_pos_open30 = (C0959 - L) / (H - L), window H/L
    #                                                   # frozen: S0 SS4 F9
    # Degenerate window (H == L) -> NA (frozen: S0 SS3 NA policy).
    if win_h > win_l:
        close_pos_open30 = (c0959 - win_l) / (win_h - win_l)
    else:
        close_pos_open30 = None

    return DayFeatures(
        trade_date=trade_date,
        ret_open30=ret_open30,
        or_width=or_width,
        de_open30=de_open30,
        rvol_open30=rvol_open30,
        gap=gap,
        open_loc_on=open_loc_on,
        on_range=on_range,
        retrace_open30=retrace_open30,
        close_pos_open30=close_pos_open30,
        is_event_day=event_flag,             # frozen: S0 SS4 F10
        is_roll_transition=is_roll_transition,   # frozen: S0 SS4 F11 / SS1
        is_roll_window=is_roll_window,           # frozen: S0 SS4 F11 / SS1
        adr14=adr14,
    )
