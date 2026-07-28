"""Hand-computed checks for itsf.s0.labels on conftest synthetic days.

All bars come from the conftest generators only (no real market data).
PM window [10:00, 15:45) = 345 bars; final close = the 15:44 bar close.
trend_up pm bars (base 20000): bar i open=20000+i, close=20001+i,
high=close+0.25, low=open-0.25 -> C1000=20001, C1544=20345.
"""
from datetime import datetime

import pytest
from conftest import ET, make_minute_bars

from itsf.s0.labels import compute_day_labels, d_open_from_ret_open30

DATE = "2026-08-03"


def pm(pattern="trend_up", base=20000.0):
    return make_minute_bars(DATE, pattern, start="10:00", end="15:45",
                            base_price=base)


def test_trend_up_long_hand_computed():
    lab = compute_day_labels(pm("trend_up"), o1000=20000.0, adr14=100.0,
                             d_open=1)
    assert lab.trade_date == DATE
    assert lab.d_open == 1
    # Y_cont = +1 * (20345 - 20000) / 100              # frozen: S0 SS5 Y_cont
    assert lab.y_cont == pytest.approx(3.45)
    # Y1 = (20345 - 20000) / 100                       # frozen: S0 SS5 Y1
    assert lab.y1 == pytest.approx(3.45)
    # Y2: path_pm = |20001-20000| + 344*1 = 345; |345|/345 = 1
    #                                                  # frozen: S0 SS5 Y2
    assert lab.y2_de_pm == pytest.approx(1.0)
    # Y3: H=20345.25, L=19999.75 -> (20345 - 19999.75)/345.5
    assert lab.y3_close_pos_pm == pytest.approx(345.25 / 345.5)
    # Y4 MFE (extremes, long -> minute highs): (20345.25 - 20000)/100
    #                                                  # frozen: S0 SS5 Y4
    assert lab.y4_mfe == pytest.approx(3.4525)
    # Y5 MAE (extremes, long -> minute lows): (19999.75 - 20000)/100
    #                                                  # frozen: S0 SS5 Y5
    assert lab.y5_mae == pytest.approx(-0.0025)
    # Y6 assigned at dataset level only               # frozen: S0 SS5 Y6
    assert lab.y6_cont_decile is None


def test_trend_down_short_mirror():
    lab = compute_day_labels(pm("trend_down"), o1000=20000.0, adr14=100.0,
                             d_open=-1)
    # C1544 = 20000 - 345 = 19655
    assert lab.y1 == pytest.approx(-3.45)
    # Y_cont = -1 * (19655 - 20000)/100 = +3.45 (continuation in direction)
    assert lab.y_cont == pytest.approx(3.45)
    assert lab.y2_de_pm == pytest.approx(1.0)
    # short favourable = minute lows: min low = 19654.75
    assert lab.y4_mfe == pytest.approx(3.4525)
    # short adverse = minute highs: max high = 20000.25 (first bar)
    assert lab.y5_mae == pytest.approx(-0.0025)


def test_chop_low_pm_efficiency():
    lab = compute_day_labels(pm("chop"), o1000=20000.0, adr14=100.0, d_open=1)
    # chop closes alternate; 345 bars end at 20001 -> path 345, |1|/345
    assert lab.y2_de_pm == pytest.approx(1.0 / 345.0)
    assert lab.y1 == pytest.approx(0.01)
    assert lab.y_cont == pytest.approx(0.01)


def test_spike_day_mae_uses_minute_extremes():
    # spike_down: full-session generator puts a deep intraminute low at
    # minute 61 (10:31 bar): low = 20061 - 40 = 20021. Slice pm window.
    full = make_minute_bars(DATE, "spike_down", start="09:30", end="16:00")
    t10 = datetime(2026, 8, 3, 10, 0, tzinfo=ET)
    t1545 = datetime(2026, 8, 3, 15, 45, tzinfo=ET)
    bars = full[(full["ts"] >= t10) & (full["ts"] < t1545)]
    assert len(bars) == 345
    o1000 = float(bars["open"].iloc[0])   # 20030
    lab = compute_day_labels(bars, o1000=o1000, adr14=100.0, d_open=1)
    # Y5 from minute LOW extreme: (20021 - 20030)/100 = -0.09; the close
    # path never dips below o1000, so a close-based MAE would be +0.01 -
    # this pins the extreme-based reading.  # frozen: S0 SS5 Y5
    assert lab.y5_mae == pytest.approx(-0.09)
    assert lab.y5_mae < 0
    # Y4 from minute HIGH extreme: (20375.25 - 20030)/100
    assert lab.y4_mfe == pytest.approx(3.4525)
    # Y_cont uses closes only: (20375 - 20030)/100    # frozen: S0 SS5 Y_cont
    assert lab.y_cont == pytest.approx(3.45)


def test_d_open_zero_day_all_na():
    # frozen: S0 SS5 - ret_open30 == 0: no direction, not tradeable,
    # counted separately; only trade_date/d_open populated.
    lab = compute_day_labels(pm("trend_up"), o1000=20000.0, adr14=100.0,
                             d_open=0)
    assert lab.trade_date == DATE
    assert lab.d_open == 0
    assert lab.y_cont is None
    assert lab.y1 is None
    assert lab.y2_de_pm is None
    assert lab.y3_close_pos_pm is None
    assert lab.y4_mfe is None
    assert lab.y5_mae is None
    assert lab.y6_cont_decile is None


def test_missing_adr14_na_policy():
    # frozen: S0 SS3 - /ADR14 labels record NA; ADR14-free labels remain.
    lab = compute_day_labels(pm("trend_up"), o1000=20000.0, adr14=None,
                             d_open=1)
    assert lab.y_cont is None
    assert lab.y1 is None
    assert lab.y4_mfe is None
    assert lab.y5_mae is None
    assert lab.y2_de_pm == pytest.approx(1.0)
    assert lab.y3_close_pos_pm is not None


def test_d_open_helper_sign():
    # frozen: S0 SS5 - d_open = sign(ret_open30)
    assert d_open_from_ret_open30(0.3) == 1
    assert d_open_from_ret_open30(-0.2) == -1
    assert d_open_from_ret_open30(0.0) == 0
    assert d_open_from_ret_open30(None) == 0


def test_invalid_d_open_rejected():
    with pytest.raises(ValueError):
        compute_day_labels(pm(), o1000=20000.0, adr14=100.0, d_open=2)
