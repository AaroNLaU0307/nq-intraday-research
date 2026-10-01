"""Tests for itsf.data.calendar.SessionCalendar (synthetic tables only).

DST unit tests are mandated by frozen S0 SS3. US 2026 transitions:
spring-forward Sun 2026-03-08, fall-back Sun 2026-11-01.
"""
from __future__ import annotations

from datetime import timedelta, timezone


def utc_span(start, end) -> timedelta:
    """True elapsed time. Same-tzinfo aware subtraction is wall-clock in
    Python, so convert to UTC before differencing."""
    return end.astimezone(timezone.utc) - start.astimezone(timezone.utc)

from conftest import make_minute_bars

from itsf.data.calendar import (
    REASON_HALF_DAY,
    REASON_MISSING_GT_10PCT,
    REASON_ZERO_BARS,
    SessionCalendar,
)


def make_cal(trading_days=None, holidays=None, half_days=None,
             roll_transitions=None) -> SessionCalendar:
    return SessionCalendar(
        holidays=set(holidays or ()),
        half_days=set(half_days or ()),
        roll_transitions=set(roll_transitions or ()),
        trading_days=list(trading_days or []),
    )


# ---- DST: rth_window UTC offsets (frozen: S0 SS3 DST unit tests) -----------

def test_rth_window_est_before_spring_forward():
    cal = make_cal()
    start, end = cal.rth_window("2026-03-06")  # Fri before 2026-03-08 change
    assert start.utcoffset() == timedelta(hours=-5)
    assert end.utcoffset() == timedelta(hours=-5)
    assert (start.hour, start.minute) == (9, 30)
    assert (end.hour, end.minute) == (16, 0)


def test_rth_window_edt_after_spring_forward():
    cal = make_cal()
    start, end = cal.rth_window("2026-03-09")  # Mon after spring-forward
    assert start.utcoffset() == timedelta(hours=-4)
    assert end.utcoffset() == timedelta(hours=-4)
    assert (start.hour, start.minute) == (9, 30)


def test_rth_window_edt_before_fall_back():
    cal = make_cal()
    start, end = cal.rth_window("2026-10-30")  # Fri before 2026-11-01 change
    assert start.utcoffset() == timedelta(hours=-4)
    assert end.utcoffset() == timedelta(hours=-4)


def test_rth_window_est_after_fall_back():
    cal = make_cal()
    start, end = cal.rth_window("2026-11-02")  # Mon after fall-back
    assert start.utcoffset() == timedelta(hours=-5)
    assert end.utcoffset() == timedelta(hours=-5)


def test_overnight_window_spans_spring_forward():
    # frozen: S0 SS3 overnight = prev trading day 18:00 -> date 09:30
    cal = make_cal(trading_days=["2026-03-05", "2026-03-06", "2026-03-09"])
    start, end = cal.overnight_window("2026-03-09")
    assert start.utcoffset() == timedelta(hours=-5)   # Fri 18:00 EST
    assert end.utcoffset() == timedelta(hours=-4)     # Mon 09:30 EDT
    # Fri 23:00Z -> Mon 13:30Z = 62.5h (one wall-clock hour skipped)
    assert utc_span(start, end) == timedelta(hours=62, minutes=30)


def test_overnight_window_spans_fall_back():
    cal = make_cal(trading_days=["2026-10-30", "2026-11-02"])
    start, end = cal.overnight_window("2026-11-02")
    assert start.utcoffset() == timedelta(hours=-4)   # Fri 18:00 EDT
    assert end.utcoffset() == timedelta(hours=-5)     # Mon 09:30 EST
    # Fri 22:00Z -> Mon 14:30Z = 64.5h (one wall-clock hour repeated)
    assert utc_span(start, end) == timedelta(hours=64, minutes=30)


# ---- session slicing (frozen: S0 SS3) --------------------------------------

def test_slice_counts_full_session():
    cal = make_cal()
    bars = make_minute_bars("2026-08-03")            # full 09:30-16:00 session
    rth = cal.slice_rth(bars, "2026-08-03")
    obs = cal.slice_obs(bars, "2026-08-03")
    pm = cal.slice_pm(bars, "2026-08-03")
    assert len(rth) == 390
    assert len(obs) == 30                            # 09:30..09:59 bars
    assert len(pm) == 345                            # 10:00..15:44 bars
    assert obs["ts"].iloc[0].strftime("%H:%M") == "09:30"
    assert obs["ts"].iloc[-1].strftime("%H:%M") == "09:59"
    assert pm["ts"].iloc[0].strftime("%H:%M") == "10:00"
    assert pm["ts"].iloc[-1].strftime("%H:%M") == "15:44"


def test_slices_on_dst_transition_week_day():
    # Session on the Monday after spring-forward still has 390 wall-clock bars.
    cal = make_cal()
    bars = make_minute_bars("2026-03-09")
    assert len(cal.slice_rth(bars, "2026-03-09")) == 390
    assert len(cal.slice_obs(bars, "2026-03-09")) == 30
    assert len(cal.slice_pm(bars, "2026-03-09")) == 345


# ---- exclusions (frozen: S0 SS3, ONLY three reasons) -----------------------

def test_half_day_excluded_even_with_full_bars():
    cal = make_cal(half_days=["2026-08-04"])
    bars = make_minute_bars("2026-08-04")
    excluded, reason = cal.is_excluded("2026-08-04", bars)
    assert excluded is True
    assert reason == REASON_HALF_DAY


def test_zero_bars_excluded():
    cal = make_cal()
    bars = make_minute_bars("2026-08-03")
    excluded, reason = cal.is_excluded("2026-08-03", bars.iloc[0:0])
    assert excluded is True
    assert reason == REASON_ZERO_BARS


def test_missing_over_10pct_excluded_and_boundary_kept():
    cal = make_cal()
    full = make_minute_bars("2026-08-03")            # 390 bars
    # 350 bars -> 40/390 = 10.26% missing > 10% -> excluded
    excluded, reason = cal.is_excluded("2026-08-03", full.iloc[:350])
    assert excluded is True
    assert reason == REASON_MISSING_GT_10PCT
    # 351 bars -> 39/390 = exactly 10% missing, NOT > 10% -> kept (frozen: S0 SS3)
    excluded, reason = cal.is_excluded("2026-08-03", full.iloc[:351])
    assert excluded is False
    assert reason == ""


def test_normal_full_day_not_excluded():
    cal = make_cal()
    bars = make_minute_bars("2026-08-03")
    assert cal.is_excluded("2026-08-03", bars) == (False, "")


# ---- ADR14 (frozen: S0 SS4 ADR14) ------------------------------------------

def test_adr14_thirteen_days_is_none():
    cal = make_cal()
    assert cal.adr14([(110.0, 100.0)] * 13) is None


def test_adr14_fourteen_days_mean():
    cal = make_cal()
    hl = [(100.0 + i, 100.0) for i in range(1, 15)]  # ranges 1..14
    assert cal.adr14(hl) == sum(range(1, 15)) / 14


def test_adr14_uses_last_fourteen_only():
    cal = make_cal()
    hl = [(1100.0, 100.0)] + [(110.0, 100.0)] * 14   # outlier is 15th-back
    assert cal.adr14(hl) == 10.0


# ---- roll flags (frozen: S0 SS1) -------------------------------------------

def test_roll_window_boundaries_exact_plus_minus_two():
    days = [f"2026-08-{d:02d}" for d in range(3, 14)]  # 11 injected trading days
    transition = days[5]
    cal = make_cal(trading_days=days, roll_transitions=[transition])

    assert cal.is_roll_transition(transition) is True
    for d in days:
        if d != transition:
            assert cal.is_roll_transition(d) is False

    in_window = {days[3], days[4], days[5], days[6], days[7]}  # +-2 trading days
    for d in days:
        assert cal.is_roll_window(d) is (d in in_window)
    # +-3 explicitly out
    assert cal.is_roll_window(days[2]) is False
    assert cal.is_roll_window(days[8]) is False


def test_roll_window_uses_trading_day_ordering_not_calendar_days():
    # Gap over a synthetic long weekend: window counts TRADING days.
    days = ["2026-08-03", "2026-08-04", "2026-08-07",
            "2026-08-10", "2026-08-11"]
    cal = make_cal(trading_days=days, roll_transitions=["2026-08-07"])
    assert cal.is_roll_window("2026-08-03") is True   # 2 trading days before
    assert cal.is_roll_window("2026-08-11") is True   # 2 trading days after
    assert cal.is_roll_window("2026-08-07") is True   # transition itself
