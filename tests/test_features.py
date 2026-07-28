"""Hand-computed checks for itsf.s0.features on conftest synthetic days.

All bars come from the conftest generators only (no real market data).
Hand calculations below assume the generator contract:
trend_up bar i: open=20000+i, close=20001+i, high=close+0.25, low=open-0.25.
Obs window 09:30..09:59 = 30 bars -> O0930=20000, C0959=20030.
"""
import pandas as pd
import pytest
from conftest import make_minute_bars

from itsf.s0.features import EVENT_FLAGS, compute_day_features

DATE = "2026-08-03"


def obs(pattern="trend_up"):
    return make_minute_bars(DATE, pattern, start="09:30", end="10:00")


def features(bars, **overrides):
    kw = dict(
        overnight_hl=(20010.0, 19990.0),
        adr14=100.0,
        prior_rth_close=19990.0,
        rvol_median60=1500.0,
        event_flag="none",
        is_roll_transition=False,
        is_roll_window=False,
    )
    kw.update(overrides)
    return compute_day_features(bars, **kw)


def test_trend_up_hand_computed():
    f = features(obs("trend_up"))
    assert f.trade_date == DATE
    # F1: (20030 - 20000) / 100                       # frozen: S0 SS4 F1
    assert f.ret_open30 == pytest.approx(0.3)
    # F2: H=20030.25, L=19999.75 -> 30.5 / 100        # frozen: S0 SS4 F2
    assert f.or_width == pytest.approx(0.305)
    # F3: path = |20001-20000| + 29*1 = 30; |30|/30   # frozen: S0 SS4 F3
    assert f.de_open30 == pytest.approx(1.0)
    # F4: 30 bars * 100 vol / 1500                    # frozen: S0 SS4 F4
    assert f.rvol_open30 == pytest.approx(2.0)
    # F5: (20000 - 19990) / 100                       # frozen: S0 SS4 F5
    assert f.gap == pytest.approx(0.1)
    # F6: (20000 - 19990) / (20010 - 19990)           # frozen: S0 SS4 F6
    assert f.open_loc_on == pytest.approx(0.5)
    # F7: 20 / 100                                    # frozen: S0 SS4 F7
    assert f.on_range == pytest.approx(0.2)
    # F8: monotone up close path -> zero retrace      # frozen: S0 SS4 F8
    assert f.retrace_open30 == pytest.approx(0.0)
    # F9: (20030 - 19999.75) / 30.5                   # frozen: S0 SS4 F9
    assert f.close_pos_open30 == pytest.approx(30.25 / 30.5)
    assert f.is_event_day == "none"
    assert f.is_roll_transition is False
    assert f.is_roll_window is False
    assert f.adr14 == 100.0
    assert f.excluded_day is False


def test_trend_down_mirror():
    f = features(obs("trend_down"))
    # C0959 = 19970 -> (19970 - 20000)/100
    assert f.ret_open30 == pytest.approx(-0.3)
    # monotone path down: efficiency 1, retrace 0 (direction-adjusted z rises)
    assert f.de_open30 == pytest.approx(1.0)
    assert f.retrace_open30 == pytest.approx(0.0)


def test_chop_low_efficiency():
    f = features(obs("chop"))
    # closes alternate +1/-1; 30 bars end where they started: C0959 = 20000
    assert f.ret_open30 == pytest.approx(0.0)
    # F3: path = 1 + 29*1 = 30, |C0959 - O0930| = 0 -> de = 0
    assert f.de_open30 == pytest.approx(0.0)
    # F8: denominator |C0959 - O0930| == 0 -> NA      # frozen: S0 SS4 F8
    assert f.retrace_open30 is None
    # F4 unaffected by pattern
    assert f.rvol_open30 == pytest.approx(2.0)


def test_reversal_retrace_hand_computed():
    # 20 up bars (09:30-09:50, closes 20001..20020) then 10 down bars
    # (09:50-10:00 from 20020, closes 20019..20010) - both from the
    # conftest generator, concatenated.
    up = make_minute_bars(DATE, "trend_up", start="09:30", end="09:50")
    down = make_minute_bars(DATE, "trend_down", start="09:50", end="10:00",
                            base_price=20020.0)
    f = features(pd.concat([up, down], ignore_index=True))
    # raw move = 20010 - 20000 = +10 -> d_open = +1
    assert f.ret_open30 == pytest.approx(0.1)
    # F8: z peaks at +20 then ends +10 -> max_retrace = 10; 10/|10| = 1
    #                                                  # frozen: S0 SS4 F8
    assert f.retrace_open30 == pytest.approx(1.0)
    # F3: path = 1 + 19 + 10 = 30; |10|/30            # frozen: S0 SS4 F3
    assert f.de_open30 == pytest.approx(10.0 / 30.0)
    # F9: H = 20020.25, L = 19999.75 -> (20010 - 19999.75)/20.5 = 0.5
    assert f.close_pos_open30 == pytest.approx(0.5)


def test_zero_overnight_range():
    # Ruling R3: zero range -> F6 NA (0/0) but F7 = 0.0 (literal frozen F7)
    f = features(obs(), overnight_hl=(20000.0, 20000.0))
    assert f.open_loc_on is None
    assert f.on_range == pytest.approx(0.0)


def test_missing_overnight_na():
    f = features(obs(), overnight_hl=None)
    assert f.open_loc_on is None
    assert f.on_range is None


def test_roll_transition_gap_na():
    # frozen: S0 SS4 F5 - is_roll_transition day records gap as NA
    f = features(obs(), is_roll_transition=True, is_roll_window=True)
    assert f.gap is None
    assert f.is_roll_transition is True
    assert f.is_roll_window is True
    # other features unaffected
    assert f.ret_open30 == pytest.approx(0.3)


def test_missing_adr14_na_policy():
    # frozen: S0 SS3 - features that cannot be computed record NA; the day
    # stays in sample. ADR14-free features remain populated.
    f = features(obs(), adr14=None)
    assert f.ret_open30 is None
    assert f.or_width is None
    assert f.gap is None
    assert f.on_range is None
    assert f.adr14 is None
    # F3/F9 do not use ADR14
    assert f.de_open30 == pytest.approx(1.0)
    assert f.close_pos_open30 == pytest.approx(30.25 / 30.5)
    # F6 does not use ADR14
    assert f.open_loc_on == pytest.approx(0.5)


def test_missing_rvol_median_na():
    f = features(obs(), rvol_median60=None)
    assert f.rvol_open30 is None


def test_event_flag_stored_and_validated():
    f = features(obs(), event_flag="CPI")
    assert f.is_event_day == "CPI"
    assert set(EVENT_FLAGS) == {"CPI", "NFP", "FOMC", "none"}
    with pytest.raises(ValueError):
        features(obs(), event_flag="OPEX")   # frozen: S0 SS4 F10 closed set
