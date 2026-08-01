"""Hand-computed checks for itsf.s0.context on SYNTHETIC days only.

No real market data is touched anywhere in this file (C:\\Users\\Aaron\\
quant-data is never opened); every session below is generated in memory by the
builders at the top, and every asserted number is derived from that generator
contract in the comment above the assertion.

Generator contract (used by every hand calculation):
  bar i of a session covers minute 570+i ET (09:30 = minute 570, frozen L29);
  open_0 = base, open_i = closes[i-1], high = max(open, close) + 0.25,
  low = min(open, close) - 0.25, volume constant.
  With `linear_closes(base, step)`: closes[i] = base + (i+1)*step, therefore
    O0930 = base                     (open of bar 0)
    C0959 = base + 30*step           (close of bar 29)
    O1000 = base + 30*step           (open of bar 30)
    C1544 = base + 375*step          (close of bar 374, minute 944)
    C1559 = base + 390*step          (close of bar 389, minute 959)
    RTH range = 390*step + 0.5       (high of the last bar - low of bar 0)
"""
from __future__ import annotations

import inspect
import re
from dataclasses import asdict
from datetime import date as _date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import pytest

from itsf.contracts import APPROVED_NA_REASONS
from itsf.s0 import context as ctx_mod
from itsf.s0 import features as features_mod
from itsf.s0.context import (
    EventCalendar,
    RollInterval,
    SessionSchedule,
    build_day_context,
    build_universe,
    window_bars,
)

ET = ZoneInfo("America/New_York")
RTH_BARS = 390
DEFAULT_EVENING = (20100.0, 20050.0)     # (high, low) of the 18:00 block
DEFAULT_PREOPEN = (20080.0, 20040.0)     # (high, low) of the pre-09:30 block


# ---------------------------------------------------------------------------
# synthetic session builders
# ---------------------------------------------------------------------------

def weekdays(start: str, n: int) -> list[str]:
    d = _date.fromisoformat(start)
    out: list[str] = []
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def linear_closes(base: float, step: float = 1.0,
                  n: int = RTH_BARS) -> list[float]:
    return [base + (i + 1) * step for i in range(n)]


def zero_open30_closes(base: float, n: int = RTH_BARS) -> list[float]:
    """Up 15 minutes then back down 15: C0959 == O0930 exactly (frozen L82)."""
    out = []
    for i in range(n):
        if i < 15:
            out.append(base + (i + 1))
        elif i < 30:
            out.append(base + (29 - i))      # i == 29 -> base + 0
        else:
            out.append(base + (i - 29))
    return out


def _ts(date: str, minute: int) -> datetime:
    d = _date.fromisoformat(date)
    return datetime(d.year, d.month, d.day, minute // 60, minute % 60,
                    tzinfo=ET)


def make_session(date: str, base: float = 20000.0, step: float = 1.0,
                 volume: float = 100.0, n_bars: int = RTH_BARS,
                 closes: list[float] | None = None,
                 skip_minutes: tuple[int, ...] = (),
                 evening: tuple[float, float] | None = DEFAULT_EVENING,
                 preopen: tuple[float, float] | None = DEFAULT_PREOPEN,
                 ) -> pd.DataFrame:
    """One ET date of 1-minute bars: RTH + optional evening / pre-open blocks."""
    cl = list(closes if closes is not None else linear_closes(base, step))
    rows = []
    prev_close = base
    for i in range(n_bars):
        minute = 570 + i
        o, c = prev_close, cl[i]
        prev_close = c
        if minute in skip_minutes:
            continue
        rows.append({"ts": _ts(date, minute), "open": o,
                     "high": max(o, c) + 0.25, "low": min(o, c) - 0.25,
                     "close": c, "volume": volume})
    if preopen is not None:
        hi, lo = preopen
        mid = (hi + lo) / 2.0
        for minute in range(4 * 60, 4 * 60 + 5):
            rows.append({"ts": _ts(date, minute), "open": mid, "high": hi,
                         "low": lo, "close": mid, "volume": 5.0})
    if evening is not None:
        hi, lo = evening
        mid = (hi + lo) / 2.0
        for minute in range(18 * 60, 18 * 60 + 5):
            rows.append({"ts": _ts(date, minute), "open": mid, "high": hi,
                         "low": lo, "close": mid, "volume": 5.0})
    return pd.DataFrame(rows).sort_values("ts").reset_index(drop=True)


def make_block(date: str, minute_lo: int, minute_hi: int, high: float,
               low: float) -> pd.DataFrame:
    """A non-session block (e.g. the Sunday evening reopen)."""
    mid = (high + low) / 2.0
    rows = [{"ts": _ts(date, m), "open": mid, "high": high, "low": low,
             "close": mid, "volume": 3.0}
            for m in range(minute_lo, minute_hi + 1)]
    return pd.DataFrame(rows)


def make_market(dates: list[str], spec: dict | None = None,
                degraded: tuple[str, ...] = (),
                extra_blocks: dict | None = None):
    """(bars_by_date, SessionSchedule) for a synthetic scheduled calendar.

    spec[date] = kwargs for make_session, plus the pseudo keys
      close_minute : official RTH close minute (960 == 16:00; < 960 = half day)
      no_bars      : the scheduled session produced no bar at all
    """
    spec = spec or {}
    bars: dict[str, pd.DataFrame] = {}
    close_minute: dict[str, int] = {}
    for d in dates:
        s = dict(spec.get(d, {}))
        close_minute[d] = int(s.pop("close_minute", 960))
        if s.pop("no_bars", False):
            continue
        bars[d] = make_session(d, **s)
    for d, df in (extra_blocks or {}).items():
        bars[d] = df
    return bars, SessionSchedule(close_minute=close_minute,
                                 vendor_degraded_dates=frozenset(degraded))


NO_EVENTS = EventCalendar()


def universe_of(dates, spec=None, degraded=(), extra_blocks=None,
                events: EventCalendar = NO_EVENTS,
                roll_intervals=()):
    bars, schedule = make_market(dates, spec, degraded, extra_blocks)
    return bars, build_universe(bars, schedule, events, roll_intervals)


# ---------------------------------------------------------------------------
# windows and the bar-start convention (frozen L29 / L41-42)
# ---------------------------------------------------------------------------

def test_obs_and_pm_windows_follow_the_frozen_bar_convention():
    dates = weekdays("2020-01-02", 20)
    bars, uni = universe_of(dates)
    c = build_day_context(dates[-1], bars, uni)
    # obs = 09:30..09:59 = 30 bars; pm = 10:00..15:44 = 345 bars (frozen L41-42)
    assert len(c.obs_bars) == 30
    assert len(c.pm_bars) == 345
    assert c.obs_bars["ts"].iloc[0].strftime("%H:%M") == "09:30"
    assert c.obs_bars["ts"].iloc[-1].strftime("%H:%M") == "09:59"
    assert c.pm_bars["ts"].iloc[0].strftime("%H:%M") == "10:00"
    assert c.pm_bars["ts"].iloc[-1].strftime("%H:%M") == "15:44"
    # anchors, generator contract with base 20000 step 1
    assert c.o0930 == 20000.0
    assert c.c0959 == 20030.0
    assert c.o1000 == 20030.0
    assert c.c1544 == 20375.0


def test_window_bars_never_invents_a_bar():
    df = make_session("2020-01-02", skip_minutes=(571, 572))
    obs = window_bars(df, 570, 599)
    assert len(obs) == 28                      # IR-15: absence stays absence
    assert 571 not in {t.hour * 60 + t.minute for t in obs["ts"]}


# ---------------------------------------------------------------------------
# timezone boundary (frozen L41-43; SA-6 F-16)
# ---------------------------------------------------------------------------

def _retz(bars: dict, tz: str | None) -> dict:
    """Same bars, re-expressed in `tz` (None == drop the tz, keep ET wall
    clock). tz_convert keeps the same instants, so a UTC frame differs from the
    ET one ONLY by its labels — exactly the silent-shift case F-16 is about."""
    out = {}
    for d, df in bars.items():
        g = df.copy()
        g["ts"] = (g["ts"].dt.tz_localize(None) if tz is None
                   else g["ts"].dt.tz_convert(tz))
        out[d] = g
    return out


def test_utc_bars_fail_closed_at_the_context_boundary():
    """A UTC frame would relabel the 09:30 ET bar as 14:30 and quietly move
    every minute-of-day window; the boundary must refuse it, not convert it."""
    dates = weekdays("2020-01-02", 20)
    bars, schedule = make_market(dates)
    build_universe(bars, schedule, NO_EVENTS, ())         # ET is accepted
    with pytest.raises(ValueError, match="got UTC"):
        build_universe(_retz(bars, "UTC"), schedule, NO_EVENTS, ())
    # a NON-UTC but still non-ET zone is refused for the same reason
    with pytest.raises(ValueError, match="America/New_York"):
        build_universe(_retz(bars, "America/Chicago"), schedule, NO_EVENTS, ())


def test_tz_naive_bars_fail_closed_at_the_context_boundary():
    dates = weekdays("2020-01-02", 20)
    bars, schedule = make_market(dates)
    with pytest.raises(ValueError, match="tz-aware datetime column"):
        build_universe(_retz(bars, None), schedule, NO_EVENTS, ())


def test_window_bars_and_day_context_also_enforce_the_et_boundary():
    dates = weekdays("2020-01-02", 20)
    bars, schedule = make_market(dates)
    uni = build_universe(bars, schedule, NO_EVENTS, ())    # built from ET bars
    with pytest.raises(ValueError, match="got UTC"):
        window_bars(_retz(bars, "UTC")[dates[10]], 570, 599)
    # the per-day entry point is guarded too: a universe built from ET bars
    # must not be able to slice a UTC frame afterwards
    with pytest.raises(ValueError, match="got UTC"):
        build_day_context(dates[10], _retz(bars, "UTC"), uni)


# ---------------------------------------------------------------------------
# duplicate minutes fail closed in EVERY block (frozen L29; SA-6 F-29)
# ---------------------------------------------------------------------------

def _duplicate_minute(df: pd.DataFrame, minute: int) -> pd.DataFrame:
    row = df.loc[(df["ts"].dt.hour * 60 + df["ts"].dt.minute) == minute]
    assert len(row) == 1, f"fixture has no single bar at minute {minute}"
    return (pd.concat([df, row], ignore_index=True)
            .sort_values("ts").reset_index(drop=True))


@pytest.mark.parametrize("minute,block", [
    (570 + 5, "RTH"),                       # 09:35, the pre-existing check
    (4 * 60 + 2, "pre-open"),               # 04:02, overnight window input
    (18 * 60 + 2, "evening"),               # 18:02, overnight window input
])
def test_duplicate_minute_fails_closed_in_every_block(minute, block):
    """A duplicated minute doubles the block's volume and hides an extremum.
    Before F-29 only the RTH window was checked, so the overnight blocks
    (frozen L43) could carry duplicates into F6/F7 unnoticed."""
    dates = weekdays("2020-01-02", 20)
    bars, schedule = make_market(dates)
    bars[dates[9]] = _duplicate_minute(bars[dates[9]], minute)
    with pytest.raises(ValueError, match=f"duplicate {block} minute"):
        build_universe(bars, schedule, NO_EVENTS, ())


def test_duplicate_free_market_still_builds():
    """Control for the parametrised test above: the untouched fixture, which
    holds RTH + pre-open + evening blocks on every date, must NOT raise."""
    dates = weekdays("2020-01-02", 20)
    bars, schedule = make_market(dates)
    assert len(build_universe(bars, schedule, NO_EVENTS, ())
               .funnel.observed_rth) == 20


# ---------------------------------------------------------------------------
# eligibility funnel (frozen L44 + approved preflight order)
# ---------------------------------------------------------------------------

def test_funnel_order_conservation_and_three_frozen_reasons():
    dates = weekdays("2020-01-02", 40)
    spec = {
        dates[3]: {"no_bars": True},                              # zero-bar
        dates[5]: {"close_minute": 810, "n_bars": 240},           # half day
        dates[7]: {"skip_minutes": tuple(range(600, 650))},       # 50/390 miss
    }
    bars, uni = universe_of(dates, spec)
    f = uni.funnel
    counts = f.counts()
    assert counts["L0_scheduled_trading_days"] == 40
    assert counts["minus_zero_bar_days"] == 1
    assert counts["L1_observed_rth_days"] == 39
    assert counts["minus_scheduled_early_close_days"] == 1
    assert counts["L2_regular_full_session_candidates"] == 38
    assert counts["minus_rth_missing_gt_10pct_days"] == 1     # 50/390 = 12.8%
    assert counts["L3_structurally_eligible_days"] == 37
    # ADR14 warm-up: the first day with 14 complete prior days is index 14,
    # but indices 3/5/7 are not complete, so the warm-up runs longer.
    assert counts["L3_structurally_eligible_days"] - \
        counts["minus_adr14_warmup_days"] == \
        counts["L4_final_feature_construction_dates"]
    assert all(f.checks.values()), f.checks
    # frozen L44: ONLY these three categories delete a day
    assert set(f.exclusion_reason.values()) == {
        "zero_bars", "half_day", "missing_gt_10pct"}
    assert f.exclusion_reason[dates[3]] == "zero_bars"
    assert f.exclusion_reason[dates[5]] == "half_day"
    assert f.exclusion_reason[dates[7]] == "missing_gt_10pct"
    # the half day is removed BEFORE the >10% test, so it is not double counted
    assert dates[5] not in f.removed_missing_gt_10pct
    assert dates[5] not in f.structurally_eligible


def test_adr14_warmup_days_stay_in_the_sample_with_na_adr(   # frozen L45
):
    dates = weekdays("2020-01-02", 20)
    bars, uni = universe_of(dates)
    assert dates[0] in uni.funnel.structurally_eligible
    assert dates[0] not in uni.funnel.final_dates
    c = build_day_context(dates[0], bars, uni)
    assert c.adr14 is None
    assert c.context_na_reasons["ret_open30"] == "adr14_warmup"


# ---------------------------------------------------------------------------
# ADR14 (frozen L49)
# ---------------------------------------------------------------------------

def test_adr14_hand_computed_over_prior_14_complete_days():
    dates = weekdays("2020-01-02", 20)
    # day index 5 has step 2 -> RTH range 390*2 + 0.5 = 780.5; all other
    # complete days have 390*1 + 0.5 = 390.5.
    bars, uni = universe_of(dates, {dates[5]: {"step": 2.0}})
    # day index 14 sees exactly the 14 prior complete days 0..13
    expected = (13 * 390.5 + 780.5) / 14
    assert uni.adr14[dates[14]] == pytest.approx(expected)
    assert uni.adr14[dates[13]] is None                 # only 13 prior days
    # day 15 drops day 0 and adds day 14 (both 390.5) -> unchanged
    assert uni.adr14[dates[15]] == pytest.approx(expected)


def test_adr14_uses_only_complete_rth_days():
    dates = weekdays("2020-01-02", 20)
    # day 2 misses one bar -> not a COMPLETE day -> not in the ADR14 basis
    bars, uni = universe_of(dates, {dates[2]: {"skip_minutes": (700,)}})
    assert dates[2] not in uni.funnel.complete_390
    assert dates[2] in uni.funnel.structurally_eligible   # 1/390 < 10%
    assert uni.adr14[dates[14]] is None                   # only 13 complete
    assert uni.adr14[dates[15]] == pytest.approx(390.5)


# ---------------------------------------------------------------------------
# F4 reference set (IR-20)
# ---------------------------------------------------------------------------

def test_f4_basis_ir20_includes_early_close_and_excludes_incomplete_morning():
    dates = weekdays("2020-01-02", 65)
    target = dates[60]
    # A scheduled EARLY CLOSE day is excluded from the sample but its
    # 09:30-09:59 window is a normal complete morning -> IR-20 keeps it in the
    # F4 reference set. With days 0..59 all complete-morning, the basis is 60.
    spec = {dates[3]: {"close_minute": 810, "n_bars": 240},
            target: {"volume": 150.0}}
    bars, uni = universe_of(dates, spec)
    assert dates[3] not in uni.funnel.structurally_eligible
    assert uni.f4_basis_size[target] == 60
    # median obs volume of the basis = 30 bars * 100 = 3000; the target day's
    # own obs volume = 30 * 150 = 4500 -> rvol = 1.5 (features.py does the
    # division; the context supplies the median).
    assert uni.rvol_median60[target] == pytest.approx(3000.0)
    c = build_day_context(target, bars, uni)
    assert c.rvol_median60 == pytest.approx(3000.0)
    assert "rvol_open30" not in c.context_na_reasons

    # Same market, but day 4's morning loses one bar: incomplete morning is
    # excluded from the basis (IR-20) -> only 59 reference days -> F4 NA.
    spec2 = dict(spec)
    spec2[dates[4]] = {"skip_minutes": (571,)}
    bars2, uni2 = universe_of(dates, spec2)
    assert uni2.f4_basis_size[target] == 59
    assert uni2.rvol_median60[target] is None
    c2 = build_day_context(target, bars2, uni2)
    assert c2.context_na_reasons["rvol_open30"] == "f4_lookback_warmup"


def test_f4_reference_set_is_strictly_prior():
    dates = weekdays("2020-01-02", 65)
    bars, uni = universe_of(dates)
    # basis size == number of complete-morning sessions strictly before d
    assert uni.f4_basis_size[dates[0]] == 0
    assert uni.f4_basis_size[dates[10]] == 10
    assert uni.rvol_median60[dates[59]] is None      # only 59 prior days
    assert uni.rvol_median60[dates[60]] is not None


# ---------------------------------------------------------------------------
# IR-22 — a non-finite REQUIRED opening-window volume is an INPUT DATA DEFECT
# (APPROVED_BY_AARON 2026-08-01, resolves DECISION_PACKET_F4_NAN_VOLUME).
# ---------------------------------------------------------------------------

def _market_with_volume(minute: int, value: float, n: int = 20, idx: int = 10):
    """A normal synthetic market whose day `idx` carries `value` as the volume
    of the bar starting at minute-of-day `minute`."""
    dates = weekdays("2020-01-02", n)
    target = dates[idx]
    bars, schedule = make_market(dates)
    g = bars[target].copy()
    sel = (g["ts"].dt.hour * 60 + g["ts"].dt.minute) == minute
    assert int(sel.sum()) == 1
    g.loc[sel, "volume"] = value
    bars[target] = g
    return bars, schedule, target


@pytest.mark.parametrize("bad", [np.nan, np.inf, -np.inf])
def test_nan_or_infinite_opening_volume_is_an_input_data_defect(bad):
    """IR-22: the day is NOT a day-level NA and NOT a silent 0 — the whole
    assembly STOPs, which is also what keeps the day out of the IR-20 F4
    reference set (there is no reference set to enter)."""
    from itsf.contracts import InputDataDefectError
    bars, schedule, target = _market_with_volume(580, bad)   # 09:40 bar
    with pytest.raises(InputDataDefectError) as exc:
        build_universe(bars, schedule, NO_EVENTS, ())
    message = str(exc.value)
    assert target in message and "volume" in message         # date + column


def test_opening_volume_defect_is_scoped_to_the_frozen_window():
    """The assertion covers the frozen 09:30-09:59 observation window (the F4
    input, frozen L56), not the rest of the session."""
    bars, schedule, target = _market_with_volume(700, np.nan)   # 11:40 bar
    uni = build_universe(bars, schedule, NO_EVENTS, ())
    assert uni.summaries[target].obs_volume == pytest.approx(30 * 100.0)


def test_opening_volume_is_a_plain_sum_of_the_present_bars():
    dates = weekdays("2020-01-02", 20)
    bars, uni = universe_of(dates, {dates[10]: {"volume": 150.0}})
    assert uni.summaries[dates[10]].obs_volume == pytest.approx(30 * 150.0)
    # a genuinely ABSENT minute is absence, never a defect (IR-15)
    bars2, uni2 = universe_of(dates, {dates[10]: {"skip_minutes": (580,)}})
    assert uni2.summaries[dates[10]].obs_volume == pytest.approx(29 * 100.0)


def test_context_never_calls_nansum_on_the_opening_window():
    """Anti-regression on the exact construct IR-22 forbids: np.nansum reads a
    NaN volume as 0 and yields a plausible-looking obs_volume of 0.0."""
    src = (Path(__file__).resolve().parents[1]
           / "src" / "itsf" / "s0" / "context.py").read_text(encoding="utf-8")
    calls = [ln for ln in src.splitlines()
             if "nansum(" in ln and not ln.lstrip().startswith("#")
             and "`" not in ln]
    assert not calls, calls


# ---------------------------------------------------------------------------
# prev_rth_close (IR-19)
# ---------------------------------------------------------------------------

def test_prev_rth_close_regular_session_anchor():
    dates = weekdays("2020-01-02", 20)
    bars, uni = universe_of(dates)
    d = dates[10]
    # previous session's 15:59 bar close = base + 390*step = 20390
    assert uni.prev_rth_close[d] == pytest.approx(20390.0)
    assert uni.prev_rth_close_cause[d] == ""
    assert d not in uni.prev_close_from_early_close


def test_prev_rth_close_early_close_day_uses_its_last_scheduled_bar():
    dates = weekdays("2020-01-02", 20)
    # previous session closes 13:30 -> its last SCHEDULED RTH bar starts 13:29
    # (minute 809, bar index 239) -> close = base + 240 = 20240. IR-19 calls
    # this the anchor itself, not a substitute for a missing 15:59 bar.
    bars, uni = universe_of(dates, {dates[9]: {"close_minute": 810,
                                               "n_bars": 240}})
    d = dates[10]
    assert uni.prev_session[d] == dates[9]
    assert uni.prev_rth_close[d] == pytest.approx(20240.0)
    assert d in uni.prev_close_from_early_close       # IR-19 sidecar flag
    c = build_day_context(d, bars, uni)
    assert c.sidecar["prev_close_from_early_close_day"] is True


def test_prev_rth_close_vendor_degraded_previous_session_is_na_not_skipped():
    dates = weekdays("2020-01-02", 20)
    bars, uni = universe_of(dates, {dates[9]: {"no_bars": True}},
                            degraded=(dates[9],))
    d = dates[10]
    assert uni.prev_session[d] == dates[9]            # never skipped (IR-19)
    assert uni.prev_rth_close[d] is None
    assert uni.prev_rth_close_cause[d] == "prev_day_vendor_degraded_zero_bar"
    c = build_day_context(d, bars, uni)
    assert c.context_na_reasons["gap"] == "prev_rth_close_anchor_missing"


def test_prev_rth_close_walks_through_a_true_closure_only():
    dates = weekdays("2020-01-02", 20)
    # a scheduled date with no session data and NOT vendor-degraded is treated
    # as a true closure: the reference day is the session before it.
    bars, uni = universe_of(dates, {dates[9]: {"no_bars": True}})
    d = dates[10]
    assert uni.prev_session[d] == dates[8]
    assert uni.prev_rth_close[d] == pytest.approx(20390.0)


def test_prev_rth_close_first_sample_day_is_na():
    dates = weekdays("2020-01-02", 20)
    bars, uni = universe_of(dates)
    assert uni.prev_session[dates[0]] is None
    assert uni.prev_rth_close[dates[0]] is None
    assert uni.prev_rth_close_cause[dates[0]] == \
        "no_prior_rth_session_in_sample"


def test_prev_rth_close_missing_1559_bar_is_na_never_substituted():
    dates = weekdays("2020-01-02", 20)
    bars, uni = universe_of(dates, {dates[9]: {"skip_minutes": (959,)}})
    d = dates[10]
    assert uni.prev_rth_close[d] is None              # no "last available bar"
    assert uni.prev_rth_close_cause[d] == "prev_day_1559_bar_absent"


# ---------------------------------------------------------------------------
# overnight window (frozen L43)
# ---------------------------------------------------------------------------

def test_overnight_window_spans_prev_session_1800_to_0930():
    dates = weekdays("2020-01-02", 20)
    # 2020-01-24 Fri / -27 Mon: past the 14-day ADR warm-up so F7 on_range
    # is computable (the pre-fix indices sat inside warm-up -> adr14_warmup NA)
    friday, monday = dates[16], dates[17]
    assert _date.fromisoformat(friday).weekday() == 4
    sunday = (_date.fromisoformat(monday) - timedelta(days=1)).isoformat()
    # Friday evening block 20100/20050, Sunday reopen 20200/20000, Monday
    # pre-open 20080/20040 -> overnight high 20200, low 20000.
    bars, uni = universe_of(
        dates, extra_blocks={sunday: make_block(sunday, 18 * 60, 18 * 60 + 30,
                                                20200.0, 20000.0)})
    assert uni.overnight_hl[monday] == (20200.0, 20000.0)
    assert uni.overnight_bars[monday] == 5 + 31 + 5
    c = build_day_context(monday, bars, uni)
    assert c.overnight_hl == (20200.0, 20000.0)
    assert "on_range" not in c.context_na_reasons


def test_overnight_window_empty_is_na():
    dates = weekdays("2020-01-02", 20)
    d = dates[10]
    bars, uni = universe_of(dates, {dates[9]: {"evening": None},
                                    d: {"preopen": None}})
    assert uni.overnight_bars[d] == 0
    assert uni.overnight_hl[d] is None
    assert uni.overnight_nan_blocks[d] == 0        # genuinely empty, not NaN
    c = build_day_context(d, bars, uni)
    assert c.context_na_reasons["open_loc_on"] == "overnight_window_empty"
    assert c.context_na_reasons["on_range"] == "overnight_window_empty"


def _blank_high_low(df: pd.DataFrame, minute_lo: int) -> pd.DataFrame:
    """Bars stay present; their high/low become NaN (vendor-degraded block)."""
    g = df.copy()
    sel = (g["ts"].dt.hour * 60 + g["ts"].dt.minute) >= minute_lo
    assert sel.any()
    g.loc[sel, ["high", "low"]] = np.nan
    return g


def test_overnight_block_with_nan_high_low_is_na_not_silently_dropped():
    """SA-6 F-30. A block with bars but no usable high/low used to be dropped
    from the max/min, leaving a NARROWER range that still looked complete while
    its bars kept counting in overnight_bars. It is now NA under the EXISTING
    approved reason, with a sidecar count disclosing why (no invented reason).
    """
    dates = weekdays("2020-01-02", 20)
    prev, d = dates[9], dates[10]
    bars, schedule = make_market(dates)
    bars[prev] = _blank_high_low(bars[prev], 18 * 60)    # evening block only
    uni = build_universe(bars, schedule, NO_EVENTS, ())

    assert uni.overnight_bars[d] == 5 + 5               # the bars ARE there
    assert uni.overnight_nan_blocks[d] == 1             # one unusable block
    assert uni.overnight_hl[d] is None                  # no partial range
    c = build_day_context(d, bars, uni)
    assert c.overnight_hl is None
    assert c.context_na_reasons["open_loc_on"] == "overnight_window_empty"
    assert c.context_na_reasons["on_range"] == "overnight_window_empty"
    assert "overnight_window_empty" in APPROVED_NA_REASONS   # nothing invented
    assert c.sidecar["overnight_nan_blocks"] == 1
    assert c.sidecar["overnight_bars"] == 10            # empty vs corrupted

    # control: the same market without the NaN block keeps a real range, and
    # the surviving pre-open block alone would have produced a plausible but
    # WRONG range (20080/20040) had the evening block been dropped silently.
    bars_ok, schedule_ok = make_market(dates)
    uni_ok = build_universe(bars_ok, schedule_ok, NO_EVENTS, ())
    assert uni_ok.overnight_nan_blocks[d] == 0
    assert uni_ok.overnight_hl[d] == (20100.0, 20040.0)


# ---------------------------------------------------------------------------
# F10 (IR-13 then IR-18/IR-12)
# ---------------------------------------------------------------------------

def test_f10_encoding_ir13_then_conflict_detection():
    cpi, nfp = "2020-01-06", "2020-01-08"
    both = "2020-01-07"
    unsched_only, unsched_with_cpi = "2020-01-09", "2020-01-10"
    ev = EventCalendar(
        cpi_dates=frozenset({cpi, both, unsched_with_cpi}),
        nfp_dates=frozenset({nfp, both}),
        fomc_statement_dates=frozenset({"2020-01-13", unsched_only,
                                        unsched_with_cpi}),
        unscheduled_fomc_dates=frozenset({unsched_only, unsched_with_cpi}),
        raw_multi_event_dates=frozenset({both, unsched_with_cpi}))
    assert ev.encode_f10(cpi) == "CPI"
    assert ev.encode_f10(nfp) == "NFP"
    assert ev.encode_f10("2020-01-13") == "FOMC"     # scheduled statement day
    assert ev.encode_f10(both) is None               # IR-12 multi-event NA
    assert ev.encode_f10("2020-01-14") == "none"
    # IR-13 removes the unscheduled action from the FOMC set FIRST, so a day
    # whose only remaining category is CPI encodes as CPI (IR-18), and a day
    # with no other category encodes as "none" — never as FOMC.
    assert ev.encode_f10(unsched_only) == "none"
    assert ev.encode_f10(unsched_with_cpi) == "CPI"
    assert "2020-01-13" in ev.scheduled_fomc_dates
    assert unsched_only not in ev.scheduled_fomc_dates


def test_f10_na_reason_and_multi_hot_stays_in_the_sidecar():
    dates = weekdays("2020-01-02", 20)
    d = dates[10]
    ev = EventCalendar(cpi_dates=frozenset({d}), nfp_dates=frozenset({d}),
                       raw_multi_event_dates=frozenset({d}))
    bars, uni = universe_of(dates, events=ev)
    c = build_day_context(d, bars, uni)
    assert c.event_flag is None                       # frozen F10 field = NA
    assert c.context_na_reasons["is_event_day"] == "multi_event_day_f10_na"
    assert c.sidecar["f10_categories"] == ("CPI", "NFP")   # diagnostic only
    assert c.sidecar["f10_multi_event"] is True
    assert c.sidecar["f10_raw_multi_event_day"] is True
    # the exclusive partition must still cover the whole population (IR-18)
    counts = uni.f10_exclusive_counts()
    assert counts["NA_multi_event"] == 1
    assert sum(counts.values()) == len(uni.funnel.structurally_eligible)


def test_unscheduled_fomc_is_diagnostic_only():
    dates = weekdays("2020-01-02", 20)
    d = dates[10]
    ev = EventCalendar(fomc_statement_dates=frozenset({d}),
                       unscheduled_fomc_dates=frozenset({d}))
    bars, uni = universe_of(dates, events=ev)
    c = build_day_context(d, bars, uni)
    assert c.event_flag == "none"                     # IR-13: not F10=FOMC
    assert c.sidecar["unscheduled_fomc_action"] is True


# ---------------------------------------------------------------------------
# F11 roll flags (frozen L30-32, mapping per IR-16)
# ---------------------------------------------------------------------------

def test_roll_transition_maps_to_first_rth_session_and_window_is_plus_minus_2():
    dates = weekdays("2020-01-02", 40)
    switch = dates[20]
    intervals = (RollInterval("2019-12-01", switch, "NQZ9", 1),
                 RollInterval(switch, "2020-06-01", "NQH0", 2))
    bars, uni = universe_of(dates, roll_intervals=intervals)
    assert uni.roll_transition_dates == frozenset({switch})
    assert uni.roll_window_dates == frozenset(dates[18:23])   # +-2 RTH days
    c = build_day_context(switch, bars, uni)
    assert c.is_roll_transition is True
    assert c.is_roll_window is True
    assert c.context_na_reasons["gap"] == "roll_transition_day_na"  # frozen L57
    edge = build_day_context(dates[22], bars, uni)
    assert (edge.is_roll_transition, edge.is_roll_window) == (False, True)
    outside = build_day_context(dates[23], bars, uni)
    assert (outside.is_roll_transition, outside.is_roll_window) == (False,
                                                                    False)


def test_roll_transition_on_a_non_session_date_moves_to_the_next_session():
    dates = weekdays("2020-01-02", 40)
    monday = dates[12]                           # 2020-01-20 Mon (synthetic)
    saturday = (_date.fromisoformat(monday) - timedelta(days=2)).isoformat()
    assert _date.fromisoformat(saturday).weekday() == 5
    intervals = (RollInterval("2019-12-01", saturday, "NQZ9", 1),
                 RollInterval(saturday, "2020-06-01", "NQH0", 2))
    bars, uni = universe_of(dates, roll_intervals=intervals)
    # the mapping switches at 00:00 UTC = the prior evening pre-open, so the
    # transition is booked on the first valid RTH session on/after the
    # interval start — never on the weekend date itself.
    assert uni.roll_transition_dates == frozenset({monday})
    assert uni.roll_transitions[0].rth_session_date == monday
    assert uni.roll_transitions[0].inside_official_interval is True


def test_roll_interval_with_no_session_at_all_fails_closed():
    """SA-6 F-31 + preflight f11_roll.all_map_to_valid_rth_trading_day: an
    interval whose start has no RTH session on/after it cannot be verified, so
    it stops the assembly instead of vanishing from the flag sets."""
    dates = weekdays("2020-01-02", 40)          # last session is in Feb 2020
    intervals = (RollInterval("2019-12-01", "2021-01-04", "NQZ9", 1),
                 RollInterval("2021-01-04", "2021-06-01", "NQH1", 2))
    with pytest.raises(ValueError, match="not inside the official interval"):
        universe_of(dates, roll_intervals=intervals)


def test_roll_transition_resolved_past_the_interval_end_fails_closed():
    """SA-6 F-31 + preflight f11_roll.all_inside_official_interval: the first
    session on/after the interval start falls beyond the interval's own end,
    so the booked date would contradict the official mapping."""
    dates = weekdays("2020-01-02", 40)
    friday = dates[16]
    assert _date.fromisoformat(friday).weekday() == 4
    saturday = (_date.fromisoformat(friday) + timedelta(days=1)).isoformat()
    sunday = (_date.fromisoformat(friday) + timedelta(days=2)).isoformat()
    # interval [Sat, Sun) contains no session; the next session is Monday,
    # which is already outside it.
    intervals = (RollInterval("2019-12-01", saturday, "NQZ9", 1),
                 RollInterval(saturday, sunday, "NQH0", 2))
    with pytest.raises(ValueError, match="not inside the official interval"):
        universe_of(dates, roll_intervals=intervals)


# ---------------------------------------------------------------------------
# anchors / NA vocabulary
# ---------------------------------------------------------------------------

def test_missing_opening_anchor_marks_anchor_dependent_features_na():
    dates = weekdays("2020-01-02", 20)
    d = dates[15]
    bars, uni = universe_of(dates, {d: {"skip_minutes": (570,)}})  # no 09:30
    c = build_day_context(d, bars, uni)
    assert c.o0930 is None
    assert c.c0959 == 20030.0
    r = c.context_na_reasons
    # IR-15: the 09:31 bar must NOT stand in for the 09:30 anchor
    for field in ("ret_open30", "de_open30", "gap", "open_loc_on",
                  "retrace_open30"):
        assert r[field] == "anchor_missing", field
    # anchor-free features keep their reasons free of anchor_missing
    assert "or_width" not in r
    assert "close_pos_open30" not in r


def test_every_context_na_reason_is_approved():
    dates = weekdays("2020-01-02", 30)
    d = dates[20]
    ev = EventCalendar(cpi_dates=frozenset({d}), nfp_dates=frozenset({d}))
    spec = {d: {"skip_minutes": (570, 599), "evening": None,
                "preopen": None},
            dates[19]: {"evening": None, "no_bars": False}}
    bars, uni = universe_of(dates, spec, events=ev)
    seen: set[str] = set()
    for date in uni.funnel.structurally_eligible:
        seen.update(build_day_context(date, bars, uni)
                    .context_na_reasons.values())
    assert seen, "fixture produced no NA at all"
    assert seen <= set(APPROVED_NA_REASONS), sorted(seen - set(
        APPROVED_NA_REASONS))


def test_f4_median_zero_uses_a_deliberately_unapproved_reason():
    # There is no frozen NA class for a zero F4 reference median; the reason
    # is intentionally outside APPROVED_NA_REASONS so the NA conservation
    # checker STOPs the run instead of silently absorbing it.
    assert ctx_mod.NA_UNAPPROVED_F4_MEDIAN_ZERO not in APPROVED_NA_REASONS


def test_build_day_context_refuses_an_excluded_day():
    dates = weekdays("2020-01-02", 20)
    bars, uni = universe_of(dates, {dates[5]: {"close_minute": 810,
                                               "n_bars": 240}})
    with pytest.raises(ValueError):
        build_day_context(dates[5], bars, uni)


# ---------------------------------------------------------------------------
# no look-ahead (task spec section D)
# ---------------------------------------------------------------------------

def _perturb_after(bars: dict, cutoff: str) -> dict:
    """Machine perturbation: every bar STRICTLY AFTER `cutoff` is changed."""
    out = {}
    for d, df in bars.items():
        if d <= cutoff:
            out[d] = df
            continue
        g = df.copy()
        for col in ("open", "high", "low", "close"):
            g[col] = g[col] * 3.0 + 7.0
        g["volume"] = g["volume"] * 11.0
        out[d] = g
    return out


def test_day_context_is_invariant_to_future_bars():
    dates = weekdays("2020-01-02", 65)
    target = dates[60]
    bars, uni = universe_of(dates)
    bars2, schedule = make_market(dates), None
    bars2 = _perturb_after(bars, target)
    uni2 = build_universe(bars2, uni.schedule, uni.events, ())

    a = build_day_context(target, bars, uni)
    b = build_day_context(target, bars2, uni2)
    assert a.adr14 == b.adr14
    assert a.rvol_median60 == b.rvol_median60
    assert a.prev_rth_close == b.prev_rth_close
    assert a.overnight_hl == b.overnight_hl
    assert (a.o0930, a.c0959, a.o1000, a.c1544) == (b.o0930, b.c0959, b.o1000,
                                                    b.c1544)
    assert dict(a.context_na_reasons) == dict(b.context_na_reasons)
    pd.testing.assert_frame_equal(a.obs_bars, b.obs_bars)
    # sanity: the perturbation really did change the following day
    assert not bars[dates[61]]["close"].equals(bars2[dates[61]]["close"])
    # NOTE: labels are excluded from this invariant BY DESIGN — they read the
    # same day's intraday future ([10:00, 15:45), frozen L86-91).


def _features_of(ctx) -> dict:
    """The frozen F1-F11 output of a context, as a plain dict."""
    return asdict(features_mod.compute_day_features(**ctx.feature_kwargs()))


def test_features_are_invariant_to_future_roll_and_event_information():
    """SA-6 F-23. The bar perturbation above leaves the two NON-PRICE inputs
    untested: a roll mapping and an event table dated AFTER the day must not
    reach back into it (F5/F10/F11 are day-local by frozen L30-32 / L62)."""
    dates = weekdays("2020-01-02", 40)
    target = dates[20]
    later = dates[25]                 # > 2 RTH days after target (frozen L30)
    bars, uni = universe_of(dates)
    base = build_day_context(target, bars, uni)

    events = EventCalendar(cpi_dates=frozenset({later}),
                           nfp_dates=frozenset({later}),
                           fomc_statement_dates=frozenset({dates[30]}),
                           raw_multi_event_dates=frozenset({later}))
    intervals = (RollInterval("2019-12-01", later, "NQZ9", 1),
                 RollInterval(later, "2020-12-01", "NQH0", 2))
    bars2, uni2 = universe_of(dates, events=events, roll_intervals=intervals)
    perturbed = build_day_context(target, bars2, uni2)

    assert (perturbed.is_roll_transition, perturbed.is_roll_window) == (False,
                                                                       False)
    assert perturbed.event_flag == base.event_flag == "none"
    assert dict(perturbed.context_na_reasons) == dict(base.context_na_reasons)
    assert _features_of(perturbed) == _features_of(base)

    # control: the future information IS live where it belongs
    future_ctx = build_day_context(later, bars2, uni2)
    assert future_ctx.is_roll_transition is True
    assert future_ctx.event_flag is None            # IR-12 multi-event NA
    assert build_day_context(dates[30], bars2, uni2).event_flag == "FOMC"


def test_features_are_invariant_to_same_day_bars_after_0959():
    """SA-6 F-23. The frozen observation window closes at 09:59 (L41): nothing
    a day does after its own decision minute may change that day's features.
    Labels are excluded BY DESIGN — they read [10:00, 15:45)."""
    dates = weekdays("2020-01-02", 40)
    target = dates[20]
    bars, uni = universe_of(dates)

    perturbed_bars = dict(bars)
    g = bars[target].copy()
    after = (g["ts"].dt.hour * 60 + g["ts"].dt.minute) > 599   # 10:00 onwards
    assert after.sum() > 0
    for col in ("open", "high", "low", "close"):
        g.loc[after, col] = g.loc[after, col] * 3.0 + 7.0
    g.loc[after, "volume"] = g.loc[after, "volume"] * 11.0
    perturbed_bars[target] = g
    uni2 = build_universe(perturbed_bars, uni.schedule, uni.events, ())

    a = build_day_context(target, bars, uni)
    b = build_day_context(target, perturbed_bars, uni2)
    assert (a.o0930, a.c0959) == (b.o0930, b.c0959)
    assert a.adr14 == b.adr14 and a.rvol_median60 == b.rvol_median60
    assert a.prev_rth_close == b.prev_rth_close
    assert a.overnight_hl == b.overnight_hl
    assert dict(a.context_na_reasons) == dict(b.context_na_reasons)
    pd.testing.assert_frame_equal(a.obs_bars, b.obs_bars)
    assert _features_of(a) == _features_of(b)
    # sanity: the same day's afternoon really did move (labels see it)
    assert a.c1544 != b.c1544


# ---------------------------------------------------------------------------
# purity discipline (task spec section C)
# ---------------------------------------------------------------------------

PURE_MODULES = ("src/itsf/s0/context.py", "src/itsf/s0/dataset.py")
FORBIDDEN_SOURCE_PATTERNS = (
    r"\bopen\s*\(", r"\bprint\s*\(", r"\bimport\s+os\b", r"\bimport\s+io\b",
    r"\bimport\s+random\b", r"\bimport\s+requests\b", r"\bimport\s+socket\b",
    r"\bimport\s+subprocess\b", r"\bfrom\s+pathlib\b", r"\bPath\s*\(",
    r"np\.random", r"read_csv", r"read_parquet", r"to_csv", r"quant-data",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("rel", PURE_MODULES)
def test_modules_do_no_io_and_no_randomness(rel):
    src = (_repo_root() / rel).read_text(encoding="utf-8")
    # docstrings legitimately mention paths; strip comment/doc prose lines only
    # where they would false-positive: the patterns below are code shaped.
    for pat in FORBIDDEN_SOURCE_PATTERNS:
        hits = [ln for ln in src.splitlines()
                if re.search(pat, ln) and not ln.lstrip().startswith("#")]
        assert not hits, f"{rel}: {pat} -> {hits[:3]}"


@pytest.mark.parametrize("rel", PURE_MODULES)
def test_modules_have_no_mutable_module_level_state(rel):
    import importlib
    mod = importlib.import_module(
        "itsf.s0." + Path(rel).stem)
    bad = [n for n, v in vars(mod).items()
           if not n.startswith("__") and isinstance(v, (list, set, dict))]
    assert not bad, f"mutable module-level state in {rel}: {bad}"


# Parameter names that would let a caller override a FROZEN constant.
FROZEN_PARAM_DENYLIST = {
    "theta", "theta_primary", "theta_secondary", "thetas", "adr_lookback",
    "adr_lookback_days", "adr14_lookback", "lookback", "lookback_days",
    "f4_lookback", "f4_lookback_days", "decile_count", "n_deciles",
    "era_boundary", "micro_era_boundary", "max_missing_fraction",
    "expected_rth_minutes", "roll_window_days", "roll_window_trading_days",
    "obs_start", "obs_end", "pm_end", "rth_open", "rth_close",
    "overnight_start", "platform_fee", "platform_fee_rt_usd", "tick",
    "tick_points", "point_value", "seed", "random_state", "rng",
    "entry_time", "forced_exit_bar_time", "window", "window_minutes",
}
FROZEN_DEFAULT_DENYLIST = (0.5, 0.3, 14, 60, 10, 390, 345, 0.10, 2.0,
                           "2019-05-06", "2010-06-06", "2022-01-01")


def _module_callables(mod):
    out = []
    for name, obj in vars(mod).items():
        if inspect.isfunction(obj) and obj.__module__ == mod.__name__:
            out.append((name, obj))
        elif inspect.isclass(obj) and obj.__module__ == mod.__name__:
            for mname, m in vars(obj).items():
                if inspect.isfunction(m):
                    out.append((f"{name}.{mname}", m))
    return out


@pytest.mark.parametrize("modname", ("itsf.s0.context", "itsf.s0.dataset"))
def test_no_parameter_can_override_a_frozen_constant(modname):
    import importlib
    mod = importlib.import_module(modname)
    for qual, fn in _module_callables(mod):
        sig = inspect.signature(fn)
        for pname, p in sig.parameters.items():
            assert pname.lower() not in FROZEN_PARAM_DENYLIST, \
                f"{modname}.{qual} exposes frozen constant parameter {pname}"
            if p.default is not inspect.Parameter.empty:
                assert not any(
                    type(p.default) is type(bad) and p.default == bad
                    for bad in FROZEN_DEFAULT_DENYLIST), \
                    f"{modname}.{qual}.{pname} defaults to a frozen value"


def test_context_constants_match_the_frozen_calendar_module():
    from itsf.data import calendar as cal
    assert ctx_mod.M_0930 == 9 * 60 + 30
    assert ctx_mod.M_0959 == 9 * 60 + 59
    assert ctx_mod.M_1000 == 10 * 60
    assert ctx_mod.M_1544 == 15 * 60 + 44
    assert ctx_mod.M_1559 == 15 * 60 + 59
    assert ctx_mod.OBS_WINDOW_BARS == 30
    assert ctx_mod.PM_WINDOW_BARS == 345
    assert ctx_mod.F4_LOOKBACK_DAYS == 60                 # frozen L56
    assert ctx_mod.MICRO_ERA_BOUNDARY == "2019-05-06"     # frozen L109
    assert cal.ADR_LOOKBACK_DAYS == 14                    # frozen L49
    assert cal.EXPECTED_RTH_MINUTES == 390                # frozen L41
    assert cal.MAX_MISSING_FRACTION == 0.10               # frozen L44
    assert cal.ROLL_WINDOW_TRADING_DAYS == 2              # frozen L30


def test_universe_is_deterministic():
    dates = weekdays("2020-01-02", 30)
    bars, uni_a = universe_of(dates)
    uni_b = build_universe(bars, uni_a.schedule, uni_a.events, ())
    assert dict(uni_a.adr14) == dict(uni_b.adr14)
    assert dict(uni_a.rvol_median60) == dict(uni_b.rvol_median60)
    assert dict(uni_a.prev_rth_close) == dict(uni_b.prev_rth_close)
    assert uni_a.funnel.counts() == uni_b.funnel.counts()


def test_no_real_data_paths_referenced_in_this_test_file():
    src = Path(__file__).read_text(encoding="utf-8")
    # concatenated so the checker line itself cannot self-match
    assert ("databento-" + "archive") not in src
    assert not np.any([False])          # numpy import is used, keep linters calm


# ---------------------------------------------------------------------------
# IR-26 (Aaron 2026-08-01): vendor-degraded flag is DIAGNOSTIC-ONLY; anchor
# availability is decided solely by the exact scheduled close bar's
# existence + finiteness on the (never-skipped) reference day.
# ---------------------------------------------------------------------------

def test_ir26_degraded_reference_with_exact_close_is_usable_with_diagnostic():
    """Rule 5+6: flagged reference day, exact 15:59 close present and finite
    -> anchor USABLE, diagnostic sidecar set. Goes red under the pre-IR-26
    'any degraded reference -> NA' mutation."""
    dates = weekdays("2020-01-02", 20)
    bars, uni = universe_of(dates, degraded=(dates[9],))
    d = dates[10]
    assert uni.prev_session[d] == dates[9]              # rule 2: not skipped
    assert uni.prev_rth_close[d] == pytest.approx(20390.0)
    assert uni.prev_rth_close_cause[d] == ""
    assert d in uni.prev_close_from_vendor_degraded     # rule 6 diagnostic
    assert dates[5] not in uni.prev_close_from_vendor_degraded
    c = build_day_context(d, bars, uni)
    assert c.sidecar["prev_close_from_vendor_degraded_day"] is True


def test_ir26_degraded_reference_with_missing_close_bar_is_na():
    """Rule 7+8: flagged reference WITH bars but the exact 15:59 bar absent
    -> NA; the degraded flag neither rescues nor is the cause; no nearest
    bar is substituted; the anchor-used diagnostic stays unset."""
    dates = weekdays("2020-01-02", 20)
    _, uni = universe_of(dates, {dates[9]: {"skip_minutes": (959,)}},
                         degraded=(dates[9],))
    d = dates[10]
    assert uni.prev_rth_close[d] is None
    assert uni.prev_rth_close_cause[d] == "prev_day_1559_bar_absent"
    assert d not in uni.prev_close_from_vendor_degraded


def test_ir26_non_finite_exact_close_is_na():
    """Rule 7: an exact close that exists but is non-finite (inf) is NA —
    np.isnan alone would wrongly accept it."""
    from types import SimpleNamespace
    sched = SessionSchedule(close_minute={"2020-01-13": 960,
                                          "2020-01-14": 960})
    summaries = {"2020-01-13": SimpleNamespace(
        n_rth=390, official_close=float("inf"))}
    value, cause, from_early, from_degraded = ctx_mod._prev_close_map(
        summaries, sched, {"2020-01-14": "2020-01-13"}, ["2020-01-14"])
    assert value["2020-01-14"] is None
    assert cause["2020-01-14"] == "prev_day_1559_bar_absent"
    assert from_degraded == set()


def test_ir26_preflight_equivalence_matrix_per_day():
    """IR-26 rule B (per-day equivalence): one market containing every case
    class of the preflight resolver's verbatim decision table
    (s0_input_preflight.py 'IR-19 reference-session machinery'); each day's
    (value/NA, cause, reference) must equal that table. The real-data
    counterpart (18 missing dates byte-identical to the locked json) is
    enforced by the Stage-B gate."""
    d = weekdays("2020-01-02", 16)
    bars, uni = universe_of(
        d,
        {d[2]: {"close_minute": 810, "n_bars": 240},   # early close, final bar present
         d[4]: {"no_bars": True},                      # unflagged zero-bar -> true closure
         d[6]: {"no_bars": True},                      # flagged zero-bar
         d[8]: {"skip_minutes": (959,)},               # regular, 15:59 absent
         d[10]: {"close_minute": 810, "n_bars": 239}}, # early close, final bar absent
        degraded=(d[6], d[12]))                        # d12: flagged, full bars
    expect = {
        d[0]:  ("NA", "no_prior_rth_session_in_sample", None),
        d[3]:  ("OK", "", d[2]),
        d[5]:  ("OK", "", d[3]),                       # walked THROUGH d4
        d[7]:  ("NA", "prev_day_vendor_degraded_zero_bar", d[6]),
        d[9]:  ("NA", "prev_day_1559_bar_absent", d[8]),
        d[11]: ("NA", "prev_day_early_close_final_scheduled_bar_absent",
                d[10]),
        d[13]: ("OK", "", d[12]),                      # IR-26 recovered class
    }
    for day, (state, cause, ref) in expect.items():
        if ref is not None:
            assert uni.prev_session[day] == ref, day
        assert (uni.prev_rth_close[day] is None) == (state == "NA"), day
        assert uni.prev_rth_close_cause[day] == cause, day
    assert uni.prev_close_from_vendor_degraded == {d[13]}
    assert d[3] in uni.prev_close_from_early_close
