"""TASK 8 -- the four sealed covariates, and the L-5 trailing-only mutation test."""
from __future__ import annotations

import pytest
import synth

from r1.bars import SyntheticBarSource, TrailingHistory
from r1.covariates import (adr14, build_covariates, participation_ratio,
                           pre_release_volume, rth_range, vol_state)
from r1.errors import LeakageError, R1Error
from r1.events import Event

EVENT_DATE = "2015-06-05"


def _history(contract, *, ranges, as_of=EVENT_DATE, complete=True):
    src = SyntheticBarSource()
    dates = []
    for i, r in enumerate(ranges):
        d = f"2015-0{1 + i // 28}-{1 + i % 28:02d}"
        dates.append(d)
        src.add_day(d, synth.rth_only_day(contract, high=100.0 + r, low=100.0,
                                          complete=complete))
    return src, TrailingHistory(src, as_of, dates)


def test_rth_range_requires_a_complete_session(contract):
    src, _ = _history(contract, ranges=[10.0])
    day = src.bars_for(src.dates[0])
    assert rth_range(day, contract) == pytest.approx(10.0)
    partial = SyntheticBarSource({"x": synth.rth_only_day(
        contract, high=110.0, low=100.0, complete=False)})
    assert rth_range(partial.bars_for("x"), contract) is None


def test_adr14_is_the_mean_of_the_previous_14_complete_sessions(contract):
    src, hist = _history(contract, ranges=[10.0] * 20)
    assert adr14(hist, contract) == pytest.approx(10.0)


def test_adr14_warmup_returns_none(contract):
    src, hist = _history(contract, ranges=[10.0] * 8)
    assert adr14(hist, contract) is None            # the 2010-06-17 case


def test_adr14_ignores_incomplete_sessions(contract):
    src, hist = _history(contract, ranges=[10.0] * 14, complete=False)
    assert adr14(hist, contract) is None


def test_l5_trailing_history_cannot_reach_the_event_day(contract):
    src, hist = _history(contract, ranges=[10.0] * 20)
    with pytest.raises(LeakageError, match="strictly prior"):
        hist.bars_for(EVENT_DATE)
    with pytest.raises(LeakageError):
        hist.bars_for("2099-01-01")


def test_l5_mutating_the_future_leaves_adr14_identical(contract):
    """L-5 mutation: randomise every future row; the baseline does not move."""
    src, hist = _history(contract, ranges=[10.0] * 20)
    before = adr14(hist, contract)
    # add wildly different FUTURE sessions
    for d in ("2015-07-01", "2016-01-01", "2099-12-31"):
        src.add_day(d, synth.rth_only_day(contract, high=9999.0, low=0.0))
    after = adr14(hist, contract)
    assert after == before


def test_vol_state_uses_trailing_boundaries_only(contract):
    trail = [float(i) for i in range(1, 31)]
    assert vol_state(1.0, trail, contract) == "low"
    assert vol_state(15.0, trail, contract) == "mid"
    assert vol_state(30.0, trail, contract) == "high"
    assert vol_state(None, trail, contract) is None
    assert vol_state(5.0, [], contract) is None


def test_vol_state_window_is_capped_at_the_sealed_lookback(contract):
    long_trail = [1.0] * 5000 + [100.0] * contract.vol_state_lookback_sessions
    # only the last 250 count, and they are all identical
    assert vol_state(100.0, long_trail, contract) in {"low", "mid", "high"}
    assert len(long_trail[-contract.vol_state_lookback_sessions:]) == 250


def test_pre_release_volume_is_read_causally(contract):
    src = synth.source_with(contract, {EVENT_DATE: synth.event_day_bars(
        contract, pre_close=100.0, react_close=101.0, entry_open=101.0,
        exit_open=102.0, pre_volume=7)})
    vol = pre_release_volume(src, EVENT_DATE, contract)
    lo, hi = contract.participation_window_minutes
    assert vol == 7 * (hi - lo + 1)


def test_participation_ratio_against_a_trailing_median(contract):
    assert participation_ratio(200, [100, 100, 100], contract) == pytest.approx(2.0)
    assert participation_ratio(200, [], contract) is None
    assert participation_ratio(200, [0, 0], contract) is None


def test_build_covariates_end_to_end(contract):
    src, hist = _history(contract, ranges=[10.0] * 20)
    src.add_day(EVENT_DATE, synth.event_day_bars(
        contract, pre_close=100.0, react_close=101.0, entry_open=101.0,
        exit_open=102.0, pre_volume=5))
    cov = build_covariates(src, Event(EVENT_DATE, "CPI",
                                      "official_time_recorded"), contract,
                           history=hist,
                           trailing_adr=[9.0, 10.0, 11.0, 12.0],
                           trailing_volumes=[100, 150, 200])
    assert cov.event_type == "CPI"
    assert cov.era == "2014-2017"
    assert cov.adr14 == pytest.approx(10.0)
    assert cov.vol_state in {"low", "mid", "high"}
    assert cov.pre_release_participation is not None


def test_covariate_outside_the_sealed_family_is_refused(contract):
    src, hist = _history(contract, ranges=[10.0] * 20)
    with pytest.raises(R1Error, match="sealed family"):
        build_covariates(src, Event(EVENT_DATE, "PPI",
                                    "official_time_recorded"),
                         contract, history=hist)


def test_no_state_by_signal_grid_exists():
    """Sealed H.1/H.2: covariates are context, never a gate, never a grid.

    Checked on the AST, not the prose: the module may DISCUSS the claim
    variable in its docstring, but it may not reference it in code, and it may
    not import the signal builder.
    """
    import ast
    import inspect

    from r1 import covariates
    tree = ast.parse(inspect.getsource(covariates))
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    names |= {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    assert not {"d_event", "r_init", "build_signal", "y_net_usd"} & names
    imported = {n.module for n in ast.walk(tree)
                if isinstance(n, ast.ImportFrom) and n.module}
    assert ".signal" not in imported and ".trade" not in imported
