"""TASKS 3 and 4 -- the signal builder and the E4 signal-defined exclusion."""
from __future__ import annotations

import pytest
import synth

from r1.bars import SyntheticBarSource
from r1.errors import AuthorityError, LeakageError
from r1.signal import apply_e4, build_signal, sign, try_build_signal


def _src(contract, **kw):
    return synth.source_with(contract, {"2015-01-02": synth.event_day_bars(
        contract, **kw)})


# ---------------------------------------------------------------- positive
def test_positive_r_init(contract):
    s = build_signal(_src(contract, pre_close=100.0, react_close=101.5,
                          entry_open=101.5, exit_open=103.0),
                     "2015-01-02", contract)
    assert s.r_init == pytest.approx(1.5)
    assert s.d_event == 1 and s.has_direction


def test_negative_r_init(contract):
    s = build_signal(_src(contract, pre_close=100.0, react_close=98.25,
                          entry_open=98.25, exit_open=97.0),
                     "2015-01-02", contract)
    assert s.r_init == pytest.approx(-1.75)
    assert s.d_event == -1


def test_exact_zero_is_no_direction(contract):
    s = build_signal(_src(contract, pre_close=100.0, react_close=100.0,
                          entry_open=100.0, exit_open=101.0),
                     "2015-01-02", contract)
    assert s.r_init == 0.0
    assert s.d_event == 0 and not s.has_direction


def test_sign_is_exact_with_no_epsilon():
    """A tolerance would be a magnitude threshold, which L-8 forbids."""
    assert sign(1e-12) == 1
    assert sign(-1e-12) == -1
    assert sign(0.0) == 0
    assert sign(-0.0) == 0


def test_signal_reads_only_the_two_sealed_anchors(contract):
    from r1.bars import SignalWindow
    src = _src(contract, pre_close=100.0, react_close=101.0,
               entry_open=101.0, exit_open=102.0)
    w = SignalWindow(src, "2015-01-02", contract)
    w.require(contract.pre_release_anchor_minute)
    w.require(contract.reaction_close_minute)
    assert set(w.reads) == {contract.pre_release_anchor_minute,
                            contract.reaction_close_minute}


# ---------------------------------------------------------------- L-1
def test_l1_mutating_every_post_0831_bar_leaves_the_signal_identical(contract):
    """L-1 mutation test: the signal cannot see 08:32 or later."""
    base = build_signal(_src(contract, pre_close=100.0, react_close=101.0,
                             entry_open=101.0, exit_open=102.0),
                        "2015-01-02", contract)
    for noise in (+37.5, -91.25, 1e6):
        mutated = build_signal(
            _src(contract, pre_close=100.0, react_close=101.0,
                 entry_open=101.0, exit_open=102.0, noise_after_signal=noise),
            "2015-01-02", contract)
        assert mutated.r_init == base.r_init
        assert mutated.d_event == base.d_event


def test_l1_reading_the_signal_horizon_raises(contract):
    from r1.bars import SignalWindow
    src = _src(contract, pre_close=100.0, react_close=101.0,
               entry_open=101.0, exit_open=102.0)
    w = SignalWindow(src, "2015-01-02", contract)
    with pytest.raises(LeakageError, match="horizon"):
        w.get(contract.signal_complete_minute)
    with pytest.raises(LeakageError):
        w.get(contract.entry_minute)


# ---------------------------------------------------------------- L-12 / NA
def test_missing_anchor_is_na_not_substituted(contract):
    bars = [b for b in synth.event_day_bars(
        contract, pre_close=100.0, react_close=101.0, entry_open=101.0,
        exit_open=102.0) if b.minute != contract.pre_release_anchor_minute]
    src = synth.source_with(contract, {"2015-01-02": bars})
    assert try_build_signal(src, "2015-01-02", contract) is None


def test_malformed_event_day_is_na(contract):
    src = SyntheticBarSource({"2015-01-02": []})
    assert try_build_signal(src, "2015-01-02", contract) is None


# ---------------------------------------------------------------- E4
def test_e4_partitions_the_sample(contract):
    dates = ["2015-01-02", "2015-02-06", "2015-03-06", "2015-04-03"]
    src = SyntheticBarSource()
    src.add_day(dates[0], synth.event_day_bars(
        contract, pre_close=100.0, react_close=101.0, entry_open=101.0,
        exit_open=102.0))
    src.add_day(dates[1], synth.event_day_bars(
        contract, pre_close=100.0, react_close=99.0, entry_open=99.0,
        exit_open=98.0))
    src.add_day(dates[2], synth.event_day_bars(               # exact zero
        contract, pre_close=100.0, react_close=100.0, entry_open=100.0,
        exit_open=101.0))
    src.add_day(dates[3], [])                                 # malformed
    res = apply_e4(src, dates, contract, structural_n=4)
    assert res.e4_count == 1 and res.e4_dates == (dates[2],)
    assert res.na_dates == (dates[3],)
    assert len(res.signals) == 2
    assert res.post_seal_signal_defined_n == 4 - 1 - 1


def test_e4_arithmetic_matches_the_sealed_definition(contract):
    dates = ["2015-01-02", "2015-02-06"]
    src = synth.simple_event_source(contract, dates, pre=100.0, react=100.0,
                                    entry=100.0, exit_price=101.0)
    res = apply_e4(src, dates, contract, structural_n=252)
    assert res.e4_count == 2
    assert res.post_seal_signal_defined_n == 252 - 2


def test_e4_refuses_a_non_synthetic_source_in_s2(contract):
    class PretendRealSource:
        role = "development_signal"

        def bars_for(self, date_et):
            raise AssertionError("must never be reached in S2")

        def has_date(self, date_et):
            return True

    with pytest.raises(AuthorityError, match="S2 BUILD"):
        apply_e4(PretendRealSource(), ["2015-01-02"], contract)


def test_e4_is_applied_after_structural_eligibility(contract):
    """E4 only ever sees dates that already passed E0..E3."""
    import inspect
    src = inspect.getsource(apply_e4)
    assert "structural_n" in src
    from r1 import events
    assert "apply_e4" not in inspect.getsource(events)
