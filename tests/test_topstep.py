"""Tests for the Topstep 50K lifecycle engines (synthetic paths only).

All trade paths come from tests/conftest.py generators; no real market data,
no research numbers. Frozen-source citations live in the module under test.
"""
from __future__ import annotations

import pytest
from conftest import make_trade_path

from itsf.mc.platforms.topstep import (
    CombineLifecycle,
    ResetCredit,
    SubscriptionEngine,
    XfaLifecycle,
)


# --- SubscriptionEngine ------------------------------------------------------

def test_subscription_rebill_cadence_and_credit_banked():
    sub = SubscriptionEngine(anchor_day=0)
    # purchase-day charge (charged_at_purchase) is NOT a rebill: no credit
    assert sub.on_day(0) == 49.0
    assert sub.credits == []
    for d in range(1, 30):
        assert sub.on_day(d) == 0.0
    # rebill every 30 calendar days from anchor; each rebill banks 1 credit
    assert sub.on_day(30) == 49.0
    assert len(sub.credits) == 1 and sub.credits[0].granted_day == 30
    assert sub.on_day(31) == 0.0
    assert sub.on_day(60) == 49.0
    assert len(sub.credits) == 2


def test_reset_consumes_oldest_credit_first_then_paid_and_anchor_shifts():
    sub = SubscriptionEngine(anchor_day=0)
    for d in range(0, 61):
        sub.on_day(d)                      # credits banked on day 30 and 60
    fee, used = sub.reset(70)
    assert (fee, used) == (0.0, True)      # credit consumed, no charge
    assert [c.granted_day for c in sub.credits] == [60]   # oldest (30) gone
    # anchor moved to reset day + 30: old cadence (day 90) is dead
    assert sub.on_day(90) == 0.0
    assert sub.on_day(99) == 0.0
    assert sub.on_day(100) == 49.0         # 70 + 30
    assert len(sub.credits) == 2           # rebill on day 100 banked another
    fee, used = sub.reset(101)
    assert (fee, used) == (0.0, True)      # consumes day-60 credit (oldest)
    fee, used = sub.reset(102)
    assert (fee, used) == (0.0, True)      # consumes day-100 credit
    fee, used = sub.reset(103)
    assert (fee, used) == (49.0, False)    # no credits left -> paid reset
    assert sub.on_day(132) == 0.0
    assert sub.on_day(133) == 49.0         # anchor = last reset 103 + 30


def test_reset_daily_limit_and_cancelled_subscription():
    sub = SubscriptionEngine(anchor_day=0)
    sub.on_day(0)
    sub.reset(5)
    sub.reset(5)
    with pytest.raises(RuntimeError):      # max 2 resets per account per day
        sub.reset(5)
    sub.cancel()
    with pytest.raises(RuntimeError):      # cancelled subscription: no reset
        sub.reset(6)


def test_reset_credit_expires_at_365_days():
    def engine_with_day30_credit():
        s = SubscriptionEngine(anchor_day=0)
        s.on_day(0)
        s.on_day(30)
        return s

    fresh = engine_with_day30_credit()
    fee, used = fresh.reset(30 + 364)      # age 364d: still usable
    assert (fee, used) == (0.0, True)

    stale = engine_with_day30_credit()
    fee, used = stale.reset(30 + 365)      # age 365d: expired -> paid reset
    assert (fee, used) == (49.0, False)


def test_credit_matching_is_size_and_type_tagged():
    foreign = ResetCredit(granted_day=0, size="100k", path="standard")
    sub = SubscriptionEngine(anchor_day=0, credits=[foreign])
    sub.on_day(0)
    fee, used = sub.reset(1)               # tag mismatch -> cannot consume
    assert (fee, used) == (49.0, False)
    assert len(sub.credits) == 1           # foreign credit untouched


# --- CombineLifecycle --------------------------------------------------------

def test_combine_soft_consistency_target_inflation():
    c = CombineLifecycle()
    c.process_day(0, make_trade_path([500.0, 1800.0], final=1800.0))
    # best_day 1800 > 0.5 * 3000 -> new target = 1800 / 0.50 = 3600 (soft, alive)
    assert c.target == 3600.0
    assert not c.passed and not c.breached
    assert c.balance == 51800.0
    assert c.floor_engine.floor == 49800.0     # trail: 51800 - 2000


def test_combine_no_pass_on_profit_alone_when_consistency_unsatisfied():
    c = CombineLifecycle()
    c.process_day(0, make_trade_path([3500.0], final=3500.0))
    # profit 3500 >= original 3000 target, but best_day inflated target to 7000
    assert c.target == 7000.0
    assert not c.passed


def test_combine_pass_charges_activation_and_cancels_subscription():
    sub = SubscriptionEngine(anchor_day=0)
    c = CombineLifecycle(subscription=sub)
    ev0 = c.process_day(0, make_trade_path([1800.0], final=1800.0))
    assert ev0.fees_usd == 49.0                # purchase-day subscription charge
    c.process_day(1, make_trade_path([1300.0], final=1300.0))
    assert not c.passed                        # profit 3100 < inflated target 3600
    ev2 = c.process_day(2, make_trade_path([700.0], final=700.0))
    # profit 3800 >= 3600 and best_day 1800 <= 0.5 * 3800 -> pass
    assert c.passed
    assert ev2.phase == "done"
    assert ev2.fees_usd == 149.0               # standard-path activation fee
    assert not sub.active                      # auto_cancel_on_pass
    ev30 = c.process_day(30)                   # across a would-be rebill date
    assert ev30.fees_usd == 0.0 and ev30.phase == "done"


def test_combine_breach_on_touch_subscription_continues_reset_restores():
    sub = SubscriptionEngine(anchor_day=0)
    c = CombineLifecycle(subscription=sub)
    ev = c.process_day(0, make_trade_path([-500.0, -2000.0, -100.0]))
    # adverse equity path [49500, 48000, 49900]: touch of 48000 == breach
    assert ev.breached and c.breached
    # Ruling R1: min(floor 48000, eq 48000) - 1*$1 = 47999
    assert c.balance == 47999.0
    assert ev.fees_usd == 49.0                 # purchase charge still billed
    # practice mode until reset: trades ignored, subscription keeps billing
    ev30 = c.process_day(30, make_trade_path([100.0], final=100.0))
    assert ev30.fees_usd == 49.0               # rebill (banks a credit)
    assert ev30.notes == "awaiting_reset"
    assert c.balance == 47999.0                # trade did not count (R1 settled)
    fee, used = c.reset(31)
    assert (fee, used) == (0.0, True)          # day-30 credit consumed first
    assert not c.breached
    assert c.balance == 50000.0
    assert c.floor_engine.floor == 48000.0
    assert c.target == 3000.0 and c.best_day == 0.0   # stats_reset_on_reset


# --- XfaLifecycle ------------------------------------------------------------

def test_xfa_floor_trails_then_locks_at_zero_once_balance_hits_2000():
    x = XfaLifecycle()
    x.process_day(0, make_trade_path([1000.0], final=1000.0))
    assert x.floor_engine.floor == -1000.0     # trail: 1000 - 2000
    x.process_day(1, make_trade_path([1000.0], final=1000.0))
    assert x.balance == 2000.0
    assert x.floor_engine.floor == 0.0         # locked at 0
    x.process_day(2, make_trade_path([-100.0], final=-100.0))
    assert x.balance == 1900.0
    assert x.floor_engine.floor == 0.0         # never retreats


def test_xfa_payout_sets_floor_zero_restarts_counts_excludes_request_day():
    x = XfaLifecycle()
    for d in range(5):
        x.process_day(d, make_trade_path([200.0], final=200.0))
    assert x.qualifying_days == 5 and x.balance == 1000.0
    assert x.payout_eligible()
    ev = x.process_day(5, make_trade_path([200.0], final=200.0),
                       request_payout=True)
    assert ev.payout_gross == 600.0            # min(0.5 * 1200, 2000)
    assert ev.payout_cash == 540.0             # 600 * 0.90 - 0 (Wise)
    assert x.balance == 600.0                  # gross deducted from balance
    assert x.floor_engine.floor == 0.0         # MLL permanently 0
    assert x.payout_count == 1
    # request-day exclusion: today's +200 winning day counts toward NOTHING
    assert x.qualifying_days == 0
    assert x.cycle_net == 0.0
    # no halt during processing: next session trades and counts normally
    x.process_day(6, make_trade_path([200.0], final=200.0))
    assert x.qualifying_days == 1
    assert x.cycle_net == 200.0


def test_xfa_payout_cap_2000_and_min_125():
    x = XfaLifecycle()
    x.balance = 6000.0                          # white-box state setup
    x.qualifying_days = 5
    assert x.payout_eligible()
    ev = x.process_day(0, request_payout=True)  # payout on a no-trade day
    assert ev.payout_gross == 2000.0            # cap binds: min(3000, 2000)
    assert ev.payout_cash == 1800.0
    assert x.balance == 4000.0

    y = XfaLifecycle()
    y.balance = 200.0                           # 50% = 100 < 125 minimum
    y.qualifying_days = 5
    assert not y.payout_eligible()
    with pytest.raises(ValueError):
        y.process_day(0, request_payout=True)


def test_xfa_cycle_net_gate_applies_only_after_first_payout():
    x = XfaLifecycle()
    x.balance = 1000.0
    x.qualifying_days = 5
    x.process_day(0, request_payout=True)       # first payout: gate exempt
    assert x.payout_count == 1 and x.balance == 500.0
    d = 1
    for _ in range(5):
        x.process_day(d, make_trade_path([150.0], final=150.0))
        d += 1
    assert x.qualifying_days == 5 and x.cycle_net == 750.0
    for _ in range(2):
        x.process_day(d, make_trade_path([-500.0], final=-500.0))
        d += 1
    # 5 winning days and gross 125 >= 125, but cycle_net -250 < $0.01 -> blocked
    assert x.balance == 250.0 and x.cycle_net == -250.0
    assert not x.payout_eligible()
    x.process_day(d, make_trade_path([300.0], final=300.0))
    assert x.cycle_net == 50.0
    assert x.payout_eligible()


def test_xfa_scaling_updates_next_session_only_and_downgrades_after_payout():
    x = XfaLifecycle()
    assert x.micro_cap == 20                    # balance 0 -> lowest tier
    x.process_day(0, make_trade_path([80.0], final=80.0), n_micros=20)
    assert x.balance == 1600.0
    assert x.micro_cap == 30                    # tier [1500, 2000] from next session
    # request 50 micros mid-tier: platform clips to the cap fixed last session
    x.process_day(1, make_trade_path([20.0], final=20.0), n_micros=50)
    assert x.balance == 2200.0                  # 1600 + 30 * 20, not 50 * 20
    assert x.micro_cap == 50                    # > 2000 tier from next session
    x.qualifying_days = 5                       # white-box: make payout eligible
    x.process_day(2, request_payout=True)       # gross min(1100, 2000) = 1100
    assert x.balance == 1100.0
    assert x.micro_cap == 20                    # payout downgrade next session


def test_xfa_adverse_path_breach_is_permanent_and_b2f_signal():
    x = XfaLifecycle()
    tr = make_trade_path([-1000.0, -1500.0, 100.0], adverse_extra=600.0)
    # close path ends +100 but adverse path [-1600, -2100, -500] touches -2000
    ev = x.process_day(0, tr)
    assert ev.breached and ev.phase == "dead"
    assert x.dead
    # Ruling R1: min(floor -2000, eq -2100) - 1*$1 = -2101
    assert x.balance == -2101.0
    assert x.b2f_eligible                       # no payout taken yet
    ev2 = x.process_day(1, make_trade_path([100.0], final=100.0))
    assert ev2.phase == "dead" and x.balance == -2101.0   # inert once dead (R1)


def test_xfa_b2f_not_eligible_after_any_payout():
    x = XfaLifecycle()
    x.balance = 1000.0
    x.qualifying_days = 5
    x.process_day(0, request_payout=True)       # floor now permanently 0
    x.process_day(1, make_trade_path([-600.0], final=-600.0))
    # adverse equity 500 - 600 = -100 <= floor 0 -> dead
    assert x.dead
    assert not x.b2f_eligible                   # payout already taken
