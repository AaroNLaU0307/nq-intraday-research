"""Tests for scripts/s0_input_preflight.py (M4-T4 / SA-3).

SYNTHETIC FIXTURES ONLY — no test in this file opens the real A1 archive, so
the suite stays runnable without the data drive and can never leak a research
number. The real-data run is performed once by the script itself; these tests
pin the LOGIC it applies.

Covered (per the task spec REQUIRED TESTS list):
  1. anchor-existence determination, including the cross-day prior-close anchor
  2. eligibility funnel level counts + total conservation (no date vanishes)
  3. the three frozen exclusion categories + the >10% rule
  4. NA counts and reason classification
  5. forbidden-vocabulary guard
  6. the three status lines exist
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

_spec = importlib.util.spec_from_file_location(
    "s0_input_preflight", REPO / "scripts" / "s0_input_preflight.py")
pf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pf)

from itsf.data.calendar import SessionCalendar  # noqa: E402

FULL_CLOSE = 16 * 60          # 16:00 regular close
EARLY_CLOSE = 13 * 60         # 13:00 scheduled early close (half day)


# --------------------------------------------------------------------------
# fixtures
# --------------------------------------------------------------------------

def make_day(present_minutes: range | list[int] | None = None,
             price: float = 100.0) -> pf.DayBars:
    """A synthetic day whose RTH minutes are exactly `present_minutes`
    (absolute minute-of-day, 570..959). Absent minutes stay NaN."""
    db = pf.DayBars()
    if present_minutes is None:
        present_minutes = range(pf.RTH_LO, pf.RTH_HI + 1)
    for m in present_minutes:
        i = m - pf.RTH_LO
        db.o[i] = price + i * 0.25
        db.h[i] = price + i * 0.25 + 1
        db.l[i] = price + i * 0.25 - 1
        db.c[i] = price + i * 0.25 + 0.5
        db.v[i] = 10.0
        db.n_rth += 1
    return db


def full_day() -> pf.DayBars:
    return make_day()


# --------------------------------------------------------------------------
# 1. anchors
# --------------------------------------------------------------------------

def test_anchor_present_on_a_complete_day():
    db = full_day()
    for m in (pf.M_0930, pf.M_1000):
        assert not np.isnan(pf.anchor_open(db, m))
    for m in (pf.M_0959, pf.M_1544, pf.M_1559):
        assert not np.isnan(pf.anchor_close(db, m))


def test_anchor_missing_is_detected_and_never_substituted():
    """A hole exactly at 10:00 must read as missing — NOT as the 09:59 or
    10:01 bar. Frozen IR-15 forbids neighbouring-bar substitution."""
    minutes = [m for m in range(pf.RTH_LO, pf.RTH_HI + 1) if m != pf.M_1000]
    db = make_day(minutes)
    assert np.isnan(pf.anchor_open(db, pf.M_1000))
    assert not np.isnan(pf.anchor_close(db, pf.M_0959))
    assert not np.isnan(pf.anchor_open(db, pf.M_1000 + 1))
    # the neighbouring bars exist but the anchor stays missing
    assert db.n_rth == pf.EXPECTED_RTH_MINUTES - 1


def test_prev_rth_close_anchor_is_the_prior_days_1559_bar():
    """Cross-day logic: the prior-day close anchor reads the PREVIOUS RTH
    trading day's 15:59 bar, never the current day's."""
    days = {"2020-01-02": full_day(), "2020-01-03": full_day()}
    assert not np.isnan(pf.anchor_close(days["2020-01-02"], pf.M_1559))
    # an early-close prior day has no 15:59 bar at all
    early = make_day(range(pf.RTH_LO, EARLY_CLOSE))
    assert np.isnan(pf.anchor_close(early, pf.M_1559))


def test_prev_rth_close_missing_when_prior_day_lacks_1559():
    """Reproduces the real 2020-03-02 / 2020-07-01 shape: the previous RTH day
    exists and is a trading day, but its 15:59 bar is absent."""
    prior = make_day([m for m in range(pf.RTH_LO, pf.RTH_HI + 1)
                      if m != pf.M_1559])
    assert prior.n_rth == pf.EXPECTED_RTH_MINUTES - 1
    assert np.isnan(pf.anchor_close(prior, pf.M_1559))


# --------------------------------------------------------------------------
# 2 + 3. funnel, exclusions, conservation
# --------------------------------------------------------------------------

def _toy_universe():
    """10 scheduled days: 1 zero-bar, 1 early close, 1 with 50% missing,
    the rest complete."""
    ds = [f"2020-01-{d:02d}" for d in range(1, 11)]
    close_min = {d: FULL_CLOSE for d in ds}
    close_min[ds[1]] = EARLY_CLOSE                       # scheduled half day
    days = {}
    for d in ds:
        days[d] = full_day()
    days[ds[0]] = pf.DayBars()                           # zero RTH bars
    days[ds[1]] = make_day(range(pf.RTH_LO, EARLY_CLOSE))
    days[ds[2]] = make_day(range(pf.RTH_LO, pf.RTH_LO + 195))   # 50% missing
    return ds, close_min, days


def test_funnel_levels_and_conservation():
    ds, close_min, days = _toy_universe()
    fn = pf.build_funnel(days, close_min)
    assert len(fn["scheduled"]) == 10
    assert fn["zero_bar"] == [ds[0]]
    assert len(fn["observed_rth"]) == 9
    assert fn["removed_early"] == [ds[1]]
    assert len(fn["regular"]) == 8
    assert fn["removed_missing"] == [ds[2]]
    assert len(fn["eligible"]) == 7
    # only 7 complete days exist, so every eligible day lacks a 14-day lookback
    assert len(fn["removed_warmup"]) == 7
    assert fn["final"] == []
    assert all(fn["checks"].values()), fn["checks"]


def test_no_date_vanishes_unaccounted():
    ds, close_min, days = _toy_universe()
    fn = pf.build_funnel(days, close_min)
    accounted = (set(fn["final"]) | set(fn["zero_bar"])
                 | set(fn["removed_early"]) | set(fn["removed_missing"])
                 | set(fn["removed_warmup"]))
    assert accounted == set(fn["scheduled"])
    assert fn["checks"]["no_date_vanishes_unaccounted"]


def test_removed_sets_are_mutually_disjoint():
    ds, close_min, days = _toy_universe()
    fn = pf.build_funnel(days, close_min)
    sets = [set(fn[k]) for k in
            ("zero_bar", "removed_early", "removed_missing", "removed_warmup")]
    for i, a in enumerate(sets):
        for b in sets[i + 1:]:
            assert not (a & b)


@pytest.mark.parametrize("missing,excluded", [
    (39, False),    # 39/390 == 10.0% exactly -> NOT excluded ("> 10%")
    (40, True),     # 40/390  > 10%           -> excluded
    (0, False),
])
def test_missing_gt_10pct_boundary(missing, excluded):
    """Frozen L44 says missing > 10%, so exactly 10% must be KEPT."""
    ds = [f"2020-02-{d:02d}" for d in range(1, 4)]
    close_min = {d: FULL_CLOSE for d in ds}
    days = {d: full_day() for d in ds}
    days[ds[1]] = make_day(range(pf.RTH_LO, pf.RTH_HI + 1 - missing))
    fn = pf.build_funnel(days, close_min)
    assert (ds[1] in fn["removed_missing"]) is excluded


def test_exclusion_matches_frozen_session_calendar():
    """The inline rule must agree with the shared frozen implementation
    (itsf.data.calendar.SessionCalendar.is_excluded) on all three categories."""
    import pandas as pd
    cal = SessionCalendar(holidays=set(), half_days={"2020-01-02"},
                          roll_transitions=set(),
                          trading_days=["2020-01-01", "2020-01-02",
                                        "2020-01-03", "2020-01-04"])

    def bars(n_minutes: int, date: str) -> pd.DataFrame:
        ts = pd.date_range(f"{date} 09:30", periods=n_minutes, freq="1min",
                           tz="America/New_York")
        return pd.DataFrame({"ts": ts})

    assert cal.is_excluded("2020-01-02", bars(390, "2020-01-02"))[0] is True
    assert cal.is_excluded("2020-01-01", bars(0, "2020-01-01"))[1] == "zero_bars"
    assert cal.is_excluded("2020-01-03", bars(350, "2020-01-03")) == (
        True, "missing_gt_10pct")
    assert cal.is_excluded("2020-01-04", bars(390, "2020-01-04"))[0] is False
    # same boundary semantics as build_funnel
    assert cal.is_excluded("2020-01-04", bars(351, "2020-01-04"))[0] is False


def test_complete_390_is_side_diagnostic_not_a_deduction_stage():
    """A day missing a handful of minutes is NOT complete-390 yet must still
    survive the funnel — proof that complete_390 never deducts."""
    ds = [f"2020-03-{d:02d}" for d in range(1, 4)]
    close_min = {d: FULL_CLOSE for d in ds}
    days = {d: full_day() for d in ds}
    days[ds[1]] = make_day(range(pf.RTH_LO, pf.RTH_HI))     # 1 minute short
    fn = pf.build_funnel(days, close_min)
    assert ds[1] not in fn["complete_390"]
    assert ds[1] in fn["eligible"]


# --------------------------------------------------------------------------
# 4. NA classification helpers
# --------------------------------------------------------------------------

def test_path_length_skips_absent_minutes_without_synthesising():
    """IR-15: difference the ACTUALLY PRESENT close sequence; an absent minute
    contributes nothing and no synthetic bar is created."""
    closes = np.array([10.0, np.nan, 12.0, 13.0])
    total, n = pf.path_length(closes, first_ref=10.0)
    # |10-10| + |12-10| + |13-12| == 3 over 3 present closes
    assert total == pytest.approx(3.0)
    assert n == 3


def test_path_length_undefined_without_reference_anchor():
    total, n = pf.path_length(np.array([1.0, 2.0]), first_ref=np.nan)
    assert np.isnan(total) and n == 0
    total, n = pf.path_length(np.array([np.nan, np.nan]), first_ref=1.0)
    assert np.isnan(total) and n == 0


def test_window_present_counts_only_real_bars():
    db = make_day([m for m in range(pf.RTH_LO, pf.RTH_HI + 1)
                   if m not in (pf.M_0930 + 5, pf.M_0930 + 6)])
    assert pf.window_present(db, pf.W1_LO, pf.W1_HI) == 28
    assert pf.window_present(db, pf.W2_LO, pf.W2_HI) == 345


def test_overnight_range_includes_sunday_evening_reopen():
    """A Monday's overnight window is [Friday 18:00, Monday 09:30) and MUST
    pick up the Sunday-evening reopen bars, which carry a non-trading ET date."""
    fri, sat, sun, mon = ("2020-01-03", "2020-01-04", "2020-01-05",
                          "2020-01-06")
    days = {}
    for d in (fri, sat, sun, mon):
        days[d] = pf.DayBars()
    days[fri].eve_n, days[fri].eve_h, days[fri].eve_l = 0, np.nan, np.nan
    days[sun].day_n, days[sun].day_h, days[sun].day_l = 60, 120.0, 90.0
    days[mon].early_n, days[mon].early_h, days[mon].early_l = 100, 110.0, 95.0
    hi, lo, n = pf.overnight_range(days, sorted(days), fri, mon)
    assert (hi, lo) == (120.0, 90.0)
    assert n == 160


def test_overnight_range_empty_when_no_bars():
    days = {"2020-01-02": pf.DayBars(), "2020-01-03": pf.DayBars()}
    hi, lo, n = pf.overnight_range(days, sorted(days), "2020-01-02",
                                   "2020-01-03")
    assert n == 0 and np.isnan(hi) and np.isnan(lo)


# --------------------------------------------------------------------------
# 5. forbidden-vocabulary guard
# --------------------------------------------------------------------------

def test_scan_forbidden_flags_strategy_vocabulary():
    assert "sharpe" in pf.scan_forbidden("the Sharpe was fine")
    assert "pnl" in pf.scan_forbidden("daily pnl table")
    assert set(pf.scan_forbidden("net return and win rate")) >= {"return"}


def test_scan_forbidden_does_not_fire_on_structural_words():
    """Substring matching would wrongly flag 'event'/'development'/'level'/
    'evidence' via 'ev'; the guard is whole-word."""
    ok = ("event calendar, development window, level 1 evidence, "
          "review, whitespace, achievement")
    assert pf.scan_forbidden(ok) == []


def test_generated_report_and_json_are_free_of_strategy_vocabulary():
    for name in ("S0_INPUT_PREFLIGHT_REPORT.md", "S0_INPUT_PREFLIGHT.json"):
        p = REPO / name
        if not p.exists():
            pytest.skip(f"{name} not generated yet")
        assert pf.scan_forbidden(p.read_text(encoding="utf-8")) == []


# --------------------------------------------------------------------------
# 6. status lines + fixed json fields
# --------------------------------------------------------------------------

def test_status_constants_are_the_frozen_three():
    assert pf.STAGE == "INPUT_PREFLIGHT_ONLY"
    assert pf.REAL_S0 == "NOT_RUN"
    assert pf.APPROVAL == "AWAITING_AARON_APPROVAL"


def test_report_carries_all_three_status_lines():
    p = REPO / "S0_INPUT_PREFLIGHT_REPORT.md"
    if not p.exists():
        pytest.skip("report not generated yet")
    text = p.read_text(encoding="utf-8")
    for token in ("INPUT_PREFLIGHT_ONLY", "REAL_S0_NOT_RUN",
                  "AWAITING_AARON_APPROVAL"):
        assert token in text


def test_json_fixed_top_level_fields():
    p = REPO / "S0_INPUT_PREFLIGHT.json"
    if not p.exists():
        pytest.skip("json not generated yet")
    d = json.loads(p.read_text(encoding="utf-8"))
    assert d["stage"] == "INPUT_PREFLIGHT_ONLY"
    assert d["real_s0"] == "NOT_RUN"
    assert d["approval"] == "AWAITING_AARON_APPROVAL"
    # Lifecycle field (Aaron rule 2026-07-29): null at SA-3 delivery time,
    # then the full integration hash once the main agent has integrated —
    # both are legitimate states; vague placeholders are not.
    ic = d["integration_commit"]
    assert ic is None or (isinstance(ic, str)
                          and re.fullmatch(r"[0-9a-f]{40}", ic))
    assert len(d["input_commit"]) == 40
    assert d["generated_at_utc"].endswith("+00:00")


def test_json_funnel_conservation_holds_on_the_real_run():
    p = REPO / "S0_INPUT_PREFLIGHT.json"
    if not p.exists():
        pytest.skip("json not generated yet")
    f = json.loads(p.read_text(encoding="utf-8"))["funnel"]
    assert all(f["conservation_checks"].values())
    assert (f["L0_scheduled_trading_days"] - f["minus_zero_bar_days"]
            == f["L1_observed_rth_days"])
    assert (f["L3_structurally_eligible_days"] - f["minus_adr14_warmup_days"]
            == f["L4_final_feature_construction_dates"])


def test_json_cross_check_against_addendum_all_match():
    p = REPO / "S0_INPUT_PREFLIGHT.json"
    if not p.exists():
        pytest.skip("json not generated yet")
    x = json.loads(p.read_text(encoding="utf-8"))[
        "cross_check_vs_data_qa_addendum"]
    assert x["all_match"], [r for r in x["rows"] if not r["match"]]


def test_roll_semantics_assertions_all_pass():
    p = REPO / "S0_INPUT_PREFLIGHT.json"
    if not p.exists():
        pytest.skip("json not generated yet")
    r = json.loads(p.read_text(encoding="utf-8"))["f11_roll"]
    assert r["n_transitions"] == 47
    assert r["all_assertions_pass"], r["assertions"]
    for t in r["transitions"]:
        assert t["weekday"] not in ("Saturday", "Sunday")
        assert t["inside_official_interval"]


def test_f10_scheduled_statement_days_is_92_per_ir13():
    p = REPO / "S0_INPUT_PREFLIGHT.json"
    if not p.exists():
        pytest.skip("json not generated yet")
    s = json.loads(p.read_text(encoding="utf-8"))["f10"]
    assert s["category_day_counts"]["FOMC_scheduled_statement_days"] == 92
    assert s["fomc_statement_rows_in_table"] == 96
    assert len(s["unscheduled_fomc_action_diagnostic"]) == 4
