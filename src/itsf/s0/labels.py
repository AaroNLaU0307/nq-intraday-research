"""S0 SS5 direction and labels on pre-sliced afternoon bars.

Subagent-owned module (ownership: features.py / labels.py + their tests).
Formulas transcribed verbatim from the frozen STUDY_0_PREREGISTRATION.md
(tag s0-freeze-v1) SS5; NA policy from SS3. ``None`` == NA.

Scope boundaries (deliberate):
- ``pm_bars`` is the pre-sliced [10:00, 15:45) 1-min window; the final close
  is the 15:44 bar close (forced-exit basis - frozen: S0 SS3). No slicing
  or calendar logic here.
- ``y6_cont_decile`` is ALWAYS ``None`` at this level: Y6 is the decile of
  Y_cont within each Development YEAR (frozen: S0 SS5 Y6), a cross-day
  cross-sectional rank that can only be assigned at dataset level once all
  days of that year exist. The dataset-stage assembler owns that pass.
- No real market data before ``itsf.guards.assert_real_run_allowed()``.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from itsf.contracts import DayLabels


def d_open_from_ret_open30(ret_open30: float | None) -> int:
    """d_open = sign(ret_open30) (frozen: S0 SS5).

    ret_open30 == 0 -> 0: no-direction day, not tradeable, counted
    separately (frozen: S0 SS5). ret_open30 NA (e.g. ADR14 missing) -> 0 as
    well: the direction is undeterminable, so the day is not tradeable; the
    day itself stays in sample per the NA policy (frozen: S0 SS3).
    """
    if ret_open30 is None:
        return 0
    return (ret_open30 > 0) - (ret_open30 < 0)


def compute_day_labels(
    pm_bars: pd.DataFrame,
    o1000: float,
    adr14: float | None,
    d_open: int,
) -> DayLabels:
    """Compute DayLabels (S0 SS5) for one trading day.

    ``pm_bars`` = [10:00, 15:45) 1-min OHLCV frame with tz-aware ``ts``;
    ``o1000`` = the 10:00 bar open (entry reference - frozen: S0 SS3).
    """
    if d_open not in (-1, 0, 1):
        raise ValueError(f"d_open must be -1, 0 or +1, got {d_open!r}")
    if pm_bars is None or len(pm_bars) == 0:
        raise ValueError(
            "pm_bars must be non-empty; RTH no-trade days are exclusion "
            "days handled upstream (frozen: S0 SS3)")

    bars = pm_bars.sort_values("ts").reset_index(drop=True)
    trade_date = bars["ts"].iloc[0].date().isoformat()

    if d_open == 0:
        # frozen: S0 SS5 - ret_open30 == 0: no direction, NOT tradeable,
        # counted separately. All labels stay NA (main-agent instruction:
        # only trade_date/d_open are populated on no-direction days).
        return DayLabels(trade_date=trade_date, d_open=0)

    # frozen: S0 SS1 bar convention - C1000 = close of the 10:00 bar;
    # C1544 = close of the 15:44 bar (last pm bar; forced exit - S0 SS3).
    c1000 = float(bars["close"].iloc[0])
    c1544 = float(bars["close"].iloc[-1])
    closes = bars["close"].to_numpy(dtype=float)
    highs = bars["high"].to_numpy(dtype=float)
    lows = bars["low"].to_numpy(dtype=float)

    # Missing/degenerate ADR14 -> every /ADR14 label NA (frozen: S0 SS3).
    adr_ok = adr14 is not None and adr14 > 0

    # Y_cont = d_open x (C1544 - O1000) / ADR14 (primary, Oracle deciding)
    #                                            # frozen: S0 SS5 Y_cont
    y_cont = d_open * (c1544 - o1000) / adr14 if adr_ok else None

    # Y1 = (C1544 - O1000) / ADR14 (descriptive only; FORBIDDEN as Oracle
    # direction)                                 # frozen: S0 SS5 Y1
    y1 = (c1544 - o1000) / adr14 if adr_ok else None

    # Y2 de_pm - close-path version ONLY (verbatim):
    #   path_pm = |C1000 - O1000| + sum_{t=10:01..15:44} |C_t - C_{t-1}|
    #   de_pm   = |C1544 - O1000| / path_pm
    # frozen: S0 SS5 Y2. path_pm == 0 -> NA (frozen: S0 SS3 NA policy).
    path_pm = abs(c1000 - o1000) + float(np.abs(np.diff(closes)).sum())
    y2_de_pm = (abs(c1544 - o1000) / path_pm) if path_pm > 0 else None

    # Y3 close_pos_pm - closing position of the pm window. Frozen text gives
    # the name only; implemented as the F9 analogue on the [10:00, 15:45)
    # window: (C1544 - L_pm) / (H_pm - L_pm)     # frozen: S0 SS5 Y3 (name),
    # formula pattern per S0 SS4 F9; interpretation flagged in the report.
    pm_h = float(highs.max())
    pm_l = float(lows.min())
    y3_close_pos_pm = ((c1544 - pm_l) / (pm_h - pm_l)) if pm_h > pm_l else None

    # Y4 MFE / Y5 MAE - relative to d_open, measured from O1000, / ADR14
    #                                            # frozen: S0 SS5 Y4/Y5
    # Extreme-based (main-agent instruction): the favourable path uses the
    # minute HIGH for d_open=+1 / minute LOW for d_open=-1; the adverse path
    # the opposite extreme (consistent with the adverse-mark convention of
    # S0 SS10.1). Sign convention: y4_mfe >= 0, y5_mae <= 0 (signed
    # excursions in d_open units). Close-vs-extreme ambiguity of the frozen
    # one-liner is recorded in the subagent report.
    fav = highs if d_open == 1 else lows
    adv = lows if d_open == 1 else highs
    if adr_ok:
        y4_mfe = float(np.max(d_open * (fav - o1000))) / adr14
        y5_mae = float(np.min(d_open * (adv - o1000))) / adr14
    else:
        y4_mfe = None
        y5_mae = None

    return DayLabels(
        trade_date=trade_date,
        d_open=d_open,
        y_cont=y_cont,
        y1=y1,
        y2_de_pm=y2_de_pm,
        y3_close_pos_pm=y3_close_pos_pm,
        y4_mfe=y4_mfe,
        y5_mae=y5_mae,
        y6_cont_decile=None,   # dataset-level pass; frozen: S0 SS5 Y6 (see module docstring)
    )
