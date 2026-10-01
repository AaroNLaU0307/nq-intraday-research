"""Path-builder + dual-oracle tests.  # frozen: S0 SS6/SS7/SS10.1; MC SS3

Synthetic days ONLY (tests/conftest.py generators; real data forbidden).

Hand-computed setup used throughout (scenario: spread 0.5 pt, 1 tick/side
slippage, 2 ticks adverse, fee $1.74):
  per-side friction        = 0.25 + 0.25 = 0.50 pt
  adverse-side friction    = 0.25 + 0.50 = 0.75 pt
conftest bars (09:30-16:00, base 20000, step 1):
  trend_up   bar i: open 20000+i, close +i+1, high close+0.25, low open-0.25
  trend_down bar i: open 20000-i, close -i-1, high open+0.25, low close-0.25
10:00 bar index = 30; 15:44 bar index = 374 -> full arrays = 345 elements.
"""
from __future__ import annotations

import pytest
from conftest import make_minute_bars

from itsf.contracts import CostScenarioParams
from itsf.s0 import costs, oracle, paths

SCN = CostScenarioParams(name="Base", spread_points=0.5,
                         slippage_ticks_per_side=1.0,
                         adverse_slippage_ticks=2.0)  # fee defaults to 1.74
DAY = "2026-08-03"
ENTRY_IDX = 30       # 10:00 bar in a 09:30-start session
END_IDX = 374        # 15:44 bar
FULL_LEN = END_IDX - ENTRY_IDX + 1  # 345


# --- E2 timed exits, hand-computed long AND short ---------------------------

def test_e2_long_trend_up_hand_computed():
    bars = make_minute_bars(DAY, "trend_up")
    rec = paths.build_record(bars, ENTRY_IDX, 1, "E2", SCN,
                             planned_stop=19999.75)
    # entry: 20030 + 0.5; timed exit: close_374 = 20375 -> 20374.5
    assert rec.entry_fill == pytest.approx(20030.5)
    assert rec.exit_fill == pytest.approx(20374.5)
    # (20374.5 - 20030.5)*$2 = 688.0 gross - 1.74 fee ONCE  # frozen: S0 SS10.1
    assert rec.final_pnl_per_contract == pytest.approx(686.26)
    assert len(rec.mtm_close_pnl_1m) == FULL_LEN
    assert len(rec.mtm_adverse_pnl_1m) == FULL_LEN
    # first-bar marks vs friction-inclusive entry fill:
    # close (20031-20030.5)*2 = 1.0; adverse low (20029.75-20030.5)*2 = -1.5
    assert rec.mtm_close_pnl_1m[0] == pytest.approx(1.0)
    assert rec.mtm_adverse_pnl_1m[0] == pytest.approx(-1.5)
    # exit element = realized (exit friction only at exit)
    assert rec.mtm_close_pnl_1m[-1] == pytest.approx(688.0)
    assert rec.max_favourable_pnl == pytest.approx(688.0)
    assert rec.max_adverse_pnl == pytest.approx(-1.5)
    assert rec.stop_triggered is False
    assert rec.actual_stop_fill is None
    assert rec.planned_stop is None      # E2 places no stop order
    assert rec.entry_ts.endswith("10:00:00-04:00")
    assert rec.exit_ts.endswith("15:44:00-04:00")


def test_e2_short_trend_down_hand_computed():
    bars = make_minute_bars(DAY, "trend_down")
    rec = paths.build_record(bars, ENTRY_IDX, -1, "E2", SCN,
                             planned_stop=20000.25)
    # entry: 19970 - 0.5 = 19969.5; exit: close_374 = 19625 -> +0.5 = 19625.5
    assert rec.entry_fill == pytest.approx(19969.5)
    assert rec.exit_fill == pytest.approx(19625.5)
    # -1*(19625.5-19969.5)*2 = 688.0 - 1.74
    assert rec.final_pnl_per_contract == pytest.approx(686.26)
    # short adverse mark uses minute HIGH: -(19970.25-19969.5)*2 = -1.5
    # frozen: S0 SS10.1
    assert rec.mtm_adverse_pnl_1m[0] == pytest.approx(-1.5)
    assert rec.mtm_close_pnl_1m[0] == pytest.approx(1.0)


# --- E1 stop fills ----------------------------------------------------------

def test_e1_long_stop_touch_truncation():
    bars = make_minute_bars(DAY, "trend_down")
    rec = paths.build_record(bars, ENTRY_IDX, 1, "E1", SCN,
                             planned_stop=19965.0)
    # first bar with low <= 19965 is abs idx 34 (low 19964.75), open 19966
    # above stop -> intrabar touch: fill = 19965 - 0.75 = 19964.25
    assert rec.stop_triggered is True
    assert rec.actual_stop_fill == pytest.approx(19964.25)
    assert rec.exit_fill == pytest.approx(19964.25)
    # truncation: length == stop bar relative index + 1  # frozen: S0 SS10.1
    stop_rel = 34 - ENTRY_IDX
    assert len(rec.mtm_close_pnl_1m) == stop_rel + 1 == 5
    assert len(rec.mtm_adverse_pnl_1m) == 5
    # realized: (19964.25 - 19970.5)*2 = -12.5; adverse truncates AT the fill
    assert rec.mtm_close_pnl_1m[-1] == pytest.approx(-12.5)
    assert rec.mtm_adverse_pnl_1m[-1] == pytest.approx(-12.5)
    assert rec.final_pnl_per_contract == pytest.approx(-14.24)  # - fee 1.74
    assert rec.max_adverse_pnl == pytest.approx(-12.5)
    assert rec.time_of_max_adverse == bars.iloc[34]["ts"].isoformat()
    assert rec.exit_ts == bars.iloc[34]["ts"].isoformat()
    assert rec.planned_stop == pytest.approx(19965.0)


def test_e1_long_gap_through_stop():
    # Stop ABOVE the entry bar open: the 10:00 bar opens beyond the stop ->
    # gap-through leg of trigger_ref = min(stop, bar_open).  # frozen: S0 SS6
    bars = make_minute_bars(DAY, "trend_down")
    rec = paths.build_record(bars, ENTRY_IDX, 1, "E1", SCN,
                             planned_stop=19972.0)
    # entry bar open 19970 < stop 19972 -> trigger_ref = 19970
    # fill = 19970 - 0.75 = 19969.25 (NOT at the stop price)
    assert rec.stop_triggered is True
    assert rec.actual_stop_fill == pytest.approx(19969.25)
    assert len(rec.mtm_close_pnl_1m) == 1          # truncated at entry bar
    # realized: (19969.25 - 19970.5)*2 = -2.5
    assert rec.mtm_adverse_pnl_1m == [pytest.approx(-2.5)]
    assert rec.final_pnl_per_contract == pytest.approx(-4.24)


def test_e1_short_stop_touch_hand_computed():
    bars = make_minute_bars(DAY, "trend_up")
    rec = paths.build_record(bars, ENTRY_IDX, -1, "E1", SCN,
                             planned_stop=20035.0)
    # entry: 20030 - 0.5 = 20029.5; first bar with high >= 20035 is abs idx 34
    # (high 20035.25), open 20034 < stop -> trigger_ref = max = 20035
    # fill = 20035 + 0.75 = 20035.75; realized -(20035.75-20029.5)*2 = -12.5
    assert rec.stop_triggered is True
    assert rec.actual_stop_fill == pytest.approx(20035.75)
    assert rec.final_pnl_per_contract == pytest.approx(-14.24)
    assert len(rec.mtm_close_pnl_1m) == 5


# --- SS10.1 adverse array vs close array (spike_down) -----------------------

def test_spike_down_adverse_catches_intraminute_low():
    # minute 61 (10:31) has a deep intraminute low the close path never sees
    bars = make_minute_bars(DAY, "spike_down")
    rec = paths.build_record(bars, ENTRY_IDX, 1, "E2", SCN,
                             planned_stop=19999.75)
    rel = 61 - ENTRY_IDX  # 31
    # close mark: (20062 - 20030.5)*2 = +63.0 — close path misses the spike
    assert rec.mtm_close_pnl_1m[rel] == pytest.approx(63.0)
    # adverse mark: low 20021 -> (20021 - 20030.5)*2 = -19.0  # frozen: S0 SS10.1
    assert rec.mtm_adverse_pnl_1m[rel] == pytest.approx(-19.0)
    assert rec.max_adverse_pnl == pytest.approx(-19.0)
    assert rec.time_of_max_adverse == bars.iloc[61]["ts"].isoformat()
    # the close array alone would report a far milder drawdown
    assert min(rec.mtm_close_pnl_1m) > rec.max_adverse_pnl


# --- sizing anchor (MC SS3: E2 uses counterfactual E1 stop distance) --------

def test_e2_anchor_equals_e1_anchor_same_day():
    bars = make_minute_bars(DAY, "trend_up")
    stop = 19999.75  # opening-range low (min low 09:30-09:59)
    e1 = paths.build_record(bars, ENTRY_IDX, 1, "E1", SCN, planned_stop=stop)
    e2 = paths.build_record(bars, ENTRY_IDX, 1, "E2", SCN, planned_stop=stop)
    # anchor = (entry 20030.5 - normal stop fill 19999.75-0.75)*$2 + fee 1.74
    #        = 63.0 + 1.74 = 64.74   # frozen: S0 SS8; MC SS3
    assert e1.sizing_anchor_usd == pytest.approx(64.74)
    assert e2.sizing_anchor_usd == pytest.approx(e1.sizing_anchor_usd)
    assert e1.planned_stop == pytest.approx(stop)
    assert e2.planned_stop is None       # counterfactual only — no order


def test_e2_places_no_stop_even_when_level_crossed():
    # Same day/stop where E1 stops out: E2 must run to the 15:44 close.
    bars = make_minute_bars(DAY, "trend_down")
    e1 = paths.build_record(bars, ENTRY_IDX, 1, "E1", SCN, planned_stop=19965.0)
    e2 = paths.build_record(bars, ENTRY_IDX, 1, "E2", SCN, planned_stop=19965.0)
    assert e1.stop_triggered is True
    assert e2.stop_triggered is False
    assert len(e2.mtm_close_pnl_1m) == FULL_LEN
    # (19624.5 - 19970.5)*2 - 1.74 = -693.74 — anchor is NOT a loss cap
    assert e2.final_pnl_per_contract == pytest.approx(-693.74)
    assert e2.final_pnl_per_contract < e1.final_pnl_per_contract
    # anchors still identical: (19970.5 - 19964.25)*2 + 1.74 = 14.24
    assert e1.sizing_anchor_usd == pytest.approx(14.24)
    assert e2.sizing_anchor_usd == pytest.approx(14.24)


# --- oracle layer -----------------------------------------------------------

def test_theoretical_geq_executable_on_trend_up():
    bars = make_minute_bars(DAY, "trend_up")
    or_high, or_low = 20030.25, 19999.75  # 09:30-10:00 extremes of this day
    theo = oracle.theoretical_oracle(bars, 1, SCN)
    # fav = max high in window = 20375.25 -> exit 20374.75:
    # (20374.75 - 20030.5)*2 - 1.74 = 686.76
    assert theo == pytest.approx(686.76)
    for engine in ("E1", "E2"):
        rec = oracle.executable_run(bars, 1, engine, SCN, or_high, or_low)
        assert theo >= rec.final_pnl_per_contract  # upper bound  # frozen: S0 SS7
        assert rec.final_pnl_per_contract == pytest.approx(686.26)


def test_executable_run_short_uses_or_high_as_stop():
    bars = make_minute_bars(DAY, "trend_down")
    rec = oracle.executable_run(bars, -1, "E1", SCN,
                                or_high=20000.25, or_low=19969.75)
    # short stop = OR high (opposite extreme)  # frozen: S0 SS7
    assert rec.planned_stop == pytest.approx(20000.25)
    assert rec.stop_triggered is False   # trend_down never revisits 20000.25
    assert rec.final_pnl_per_contract == pytest.approx(686.26)


def test_theoretical_short_hand_computed():
    bars = make_minute_bars(DAY, "trend_down")
    # fav = min low in window = 19624.75 -> exit 19625.25:
    # -(19625.25 - 19969.5)*2 - 1.74 = 686.76
    assert oracle.theoretical_oracle(bars, -1, SCN) == pytest.approx(686.76)


# --- guards -----------------------------------------------------------------

def test_no_direction_day_rejected():
    bars = make_minute_bars(DAY, "trend_up")
    with pytest.raises(ValueError):
        oracle.executable_run(bars, 0, "E1", SCN, 20030.25, 19999.75)
    with pytest.raises(ValueError):
        oracle.theoretical_oracle(bars, 0, SCN)


def test_build_record_guards():
    bars = make_minute_bars(DAY, "trend_up")
    with pytest.raises(ValueError):   # planned_stop required for BOTH engines
        paths.build_record(bars, ENTRY_IDX, 1, "E1", SCN, planned_stop=None)
    with pytest.raises(ValueError):
        paths.build_record(bars, ENTRY_IDX, 1, "E2", SCN, planned_stop=None)
    with pytest.raises(ValueError):   # entry must be the 10:00 bar (frozen SS3)
        paths.build_record(bars, ENTRY_IDX - 1, 1, "E1", SCN, planned_stop=19999.75)
    with pytest.raises(ValueError):   # unknown engine
        paths.build_record(bars, ENTRY_IDX, 1, "E3", SCN, planned_stop=19999.75)
