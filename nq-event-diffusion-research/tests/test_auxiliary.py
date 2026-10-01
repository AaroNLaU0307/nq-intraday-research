"""A1 -- the lower-half |R_init| auxiliary, and the proof that it is causal."""
from __future__ import annotations

import inspect

import pytest
import synth

from r1.auxiliary import (a1_memberships, a1_metric, evaluate_a1)
from r1.errors import R1Error
from r1.signal import Signal
from r1.trade import TradeResult


def _sig(date, r_init):
    return Signal(date_et=date, r_init=r_init,
                  d_event=(1 if r_init > 0 else -1 if r_init < 0 else 0))


def _res(date, y):
    return TradeResult(date_et=date, direction=1, cost_scenario="Base",
                       entry_ref=100.0, exit_ref=100.0, entry_fill=100.0,
                       exit_fill=100.0, gross_points=0.0, net_points=0.0,
                       y_net_usd=y)


DATES = [f"2015-{m:02d}-02" for m in range(1, 9)]


# ---------------------------------------------------------------- the metric
def test_metric_is_abs_r_init_over_adr14():
    assert a1_metric(_sig("d", 4.0), 8.0) == pytest.approx(0.5)
    assert a1_metric(_sig("d", -4.0), 8.0) == pytest.approx(0.5)


def test_metric_is_none_when_adr14_is_unavailable():
    assert a1_metric(_sig("d", 4.0), None) is None
    assert a1_metric(_sig("d", 4.0), 0.0) is None


# ---------------------------------------------------------------- the split
def test_the_split_is_trailing_and_the_first_event_is_never_a_member():
    m = a1_memberships(DATES[:4], [1.0, 2.0, 3.0, 0.5])
    assert m[0].boundary is None and m[0].is_member is False
    assert m[1].boundary == pytest.approx(1.0)      # median of [1.0]
    assert m[1].is_member is False                  # 2.0 > 1.0
    assert m[2].boundary == pytest.approx(1.5)      # median of [1.0, 2.0]
    assert m[2].is_member is False
    assert m[3].boundary == pytest.approx(2.0)      # median of [1,2,3]
    assert m[3].is_member is True                   # 0.5 <= 2.0


def test_a_missing_metric_is_not_a_member_and_does_not_move_the_boundary():
    m = a1_memberships(DATES[:4], [1.0, None, 3.0, 1.0])
    assert m[1].is_member is False
    assert m[2].boundary == pytest.approx(1.0)      # the None never entered
    assert m[3].boundary == pytest.approx(2.0)


def test_future_observations_cannot_change_historical_membership():
    """The A1 mutation test: append later events, earlier rows must not move."""
    early = a1_memberships(DATES[:4], [1.0, 2.0, 3.0, 0.5])
    extended = a1_memberships(DATES, [1.0, 2.0, 3.0, 0.5,
                                      99.0, 0.001, 42.0, 7.0])
    assert extended[:4] == early
    # and a wildly different future does not move them either
    other = a1_memberships(DATES, [1.0, 2.0, 3.0, 0.5,
                                   -0.0, 1e9, 1e-9, 0.0])
    assert other[:4] == early


def test_membership_is_independent_of_event_type_and_direction():
    """No event-type rescue: A1 sees |R_init| / ADR14 and nothing else."""
    sig = inspect.signature(a1_memberships)
    assert list(sig.parameters) == ["dates", "metrics"]
    src = inspect.getsource(a1_memberships)
    for banned in ("event_type", "CPI", "NFP", "d_event"):
        assert banned not in src


def test_no_new_parameter_exists():
    """No minimum-prior count, no tolerance, no alternative split."""
    for fn in (a1_metric, a1_memberships, evaluate_a1):
        for p in inspect.signature(fn).parameters.values():
            assert p.default is inspect.Parameter.empty, (fn.__name__, p.name)


def test_misaligned_inputs_refuse():
    with pytest.raises(R1Error, match="align"):
        a1_memberships(DATES[:2], [1.0])
    with pytest.raises(R1Error, match="align"):
        evaluate_a1([_res("d", 1.0)], a1_memberships(DATES[:2], [1.0, 2.0]))


# ---------------------------------------------------------------- evaluation
def test_a1_holds_when_the_lower_half_keeps_the_sign():
    memberships = a1_memberships(DATES[:4], [1.0, 2.0, 3.0, 0.5])
    results = [_res(d, y) for d, y in zip(DATES[:4], [5.0, 5.0, 5.0, 4.0])]
    out = evaluate_a1(results, memberships)
    assert out.n_members == 1
    assert out.mean_members == pytest.approx(4.0)
    assert out.sign_holds is True


def test_a1_fails_when_the_effect_lives_only_in_the_big_jumps():
    memberships = a1_memberships(DATES[:4], [1.0, 2.0, 3.0, 0.5])
    results = [_res(d, y) for d, y in zip(DATES[:4], [20.0, 20.0, 20.0, -9.0])]
    out = evaluate_a1(results, memberships)
    assert out.mean_all > 0 and out.mean_members < 0
    assert out.sign_holds is False


def test_a1_does_not_silently_pass_when_it_cannot_be_evaluated():
    memberships = a1_memberships(DATES[:2], [None, None])
    out = evaluate_a1([_res(DATES[0], 5.0), _res(DATES[1], 5.0)], memberships)
    assert out.n_members == 0
    assert out.evaluable is False
    assert out.sign_holds is False


def test_a1_is_non_confirmatory_and_cannot_create_support():
    """A1 True with an interval that spans M is still UNRESOLVED."""
    from r1.bootstrap import Interval
    from r1.verdict import UNRESOLVED, PrimaryEvidence, axis1_verdict
    spanning = Interval(lower=1.0, upper=9.0, point=5.0, level=0.95,
                        method="percentile", block_events=5, resamples=10_000,
                        seeds=(7, 13, 31))
    ev = PrimaryEvidence(base_interval=spanning, conservative_point_estimate=1.0,
                         c1_clears_m=False, a1_sign_holds=True,
                         materiality_m=3.99)
    assert axis1_verdict(ev) == UNRESOLVED


# ---------------------------------------------------------------- wiring
def test_run_study_computes_a1_itself(contract, tmp_path):
    """The production path takes NO caller-supplied A1 boolean."""
    from r1.pipeline import run_study
    params = inspect.signature(run_study).parameters
    assert "a1_sign_holds" not in params
    assert "n_shrunk_materially" not in params

    dates = [f"2015-{m:02d}-02" for m in range(1, 7)]
    prior = [f"2014-{m:02d}-1{d}" for m in range(1, 13) for d in (0, 5)]
    src = synth.source_with(contract, {})
    for d in prior:
        src.add_day(d, synth.rth_only_day(contract, high=110.0, low=100.0))
    # alternating |R_init| so some events genuinely fall in the lower half
    jumps = [1.0, 5.0, 2.0, 6.0, 1.5, 4.0]
    for d, jump in zip(dates, jumps):
        src.add_day(d, synth.event_day_bars(
            contract, pre_close=100.0, react_close=100.0 + jump,
            entry_open=100.0, exit_open=103.0,
            include_rth=True, rth_high=110.0, rth_low=100.0))
    out = run_study(src, dates, contract, run_dir=tmp_path, c1_draws=20)
    assert out.a1.memberships and len(out.a1.memberships) == len(dates)
    assert out.a1.memberships[0].boundary is None
    assert out.a1.n_members >= 1
    assert isinstance(out.a1.sign_holds, bool)


def test_a1_result_reaches_the_sealed_bundle(contract, tmp_path):
    from r1.outcome_seal import reveal
    from r1.pipeline import run_study
    dates = [f"2015-{m:02d}-02" for m in range(1, 5)]
    src = synth.simple_event_source(contract, dates, pre=100.0, react=101.0,
                                    entry=100.0, exit_price=102.0,
                                    include_rth=True, rth_high=110.0,
                                    rth_low=100.0)
    out = run_study(src, dates, contract, run_dir=tmp_path, c1_draws=20)
    body = reveal(out.handle,
                  owner_authorization="REVEAL_AUTHORIZED_BY_AARON:test")
    assert "a1_n_members" in body["payload"]
    assert "a1_sign_holds" in body["payload"]
