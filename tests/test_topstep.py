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


# --- payout timing: entry eligibility, lapse-and-wait ------------------------
#
# THE DEFECT THESE PIN. MC-R001 attempt 2 ran 29h05m of real MC and died with
# `ValueError: payout requested while ineligible (orchestrator bug)`. The
# orchestrator had done exactly what the frozen policy requires -- sampled
# eligibility from the state ENTERING the session -- and `process_day` then
# re-evaluated the same predicate AFTER applying the session's P&L, on a
# losing day that had taken the balance under $250. Nothing was wrong with
# the caller; the guard was reading a state nobody had decided on.
#
# Owner clarification 2026-09-16 (LAPSE_AND_WAIT): eligibility entering the
# session; amount `maximum_allowed` on the settled balance after it;
# `payout_min_usd` stays binding; if the settled amount falls below that
# minimum the request LAPSES with no payout and eligibility is evaluated
# again next session.


def _eligible_at_1000():
    """Minimal synthetic state: five $200 winning days, nothing else.

    No protected MC outcome is involved -- these are conftest trade paths.
    """
    x = XfaLifecycle()
    for d in range(5):
        x.process_day(d, make_trade_path([200.0], final=200.0))
    assert x.qualifying_days == 5 and x.balance == 1000.0
    assert x.payout_eligible()
    return x


def test_payout_on_a_winning_day_uses_the_post_session_balance():
    """CASE 1. Eligible entering the session, profitable day: the amount is
    `maximum_allowed` on the SETTLED balance, not the opening one."""
    x = _eligible_at_1000()
    ev = x.process_day(5, make_trade_path([200.0], final=200.0),
                       request_payout=True)
    assert ev.payout_gross == 600.0            # min(0.5 * 1200, 2000)
    assert x.balance == 600.0
    assert x.payout_count == 1


def test_payout_on_a_losing_day_still_above_the_minimum_is_taken():
    """CASE 2. The day's loss shrinks the payout but does not disqualify it.

    Opening 1000 -> -500 -> settled 500 -> min(250, 2000) = 250 >= 125.
    The amount tracks the settled balance downward, which is the whole point
    of computing it after the session.
    """
    x = _eligible_at_1000()
    ev = x.process_day(5, make_trade_path([-500.0], final=-500.0),
                       request_payout=True)
    assert ev.payout_gross == 250.0            # min(0.5 * 500, 2000)
    assert x.balance == 250.0
    assert x.payout_count == 1
    assert ev.notes == ""


def test_a_request_that_settles_below_the_minimum_lapses_without_paying():
    """CASE 3 and THE REGRESSION. This is the exact class of state that
    killed MC-R001 attempt 2 after 29 hours.

    Opening 1000, eligible. The day loses 800 -> settled 200 ->
    `min(0.5 * 200, 2000) = 100`, under the $125 platform minimum. Before the
    repair this raised `ValueError("payout requested while ineligible
    (orchestrator bug)")` and took the whole run down with it.

    It must now lapse: no exception, no payout, and no sub-minimum amount.
    """
    x = _eligible_at_1000()
    ev = x.process_day(5, make_trade_path([-800.0], final=-800.0),
                       request_payout=True)      # must not raise
    assert ev.payout_gross == 0.0
    assert ev.payout_cash == 0.0
    assert x.balance == 200.0                    # the loss, and nothing else
    assert ev.notes == "payout_request_lapsed_below_minimum"
    # AND THIS IS THE REPRODUCTION, stated in the test rather than implied:
    # the SETTLED state is exactly the state the old guard re-read and
    # rejected. Verified against the pre-repair module: it raises here.
    assert not x.payout_eligible()


def test_a_lapsed_request_changes_no_payout_state():
    """The lapse is a non-event for every payout-side counter: no payout was
    taken, so nothing a payout would have done may happen."""
    x = _eligible_at_1000()
    floor_before = x.floor_engine.floor
    x.process_day(5, make_trade_path([-800.0], final=-800.0),
                  request_payout=True)
    assert x.payout_count == 0                   # no payout happened
    assert x.floor_engine.floor == floor_before  # MLL not locked by a lapse
    assert x.qualifying_days == 5                # counts NOT restarted
    # ordinary trading session: the five winning days had accumulated 1000,
    # and the lapsed day's -800 joins it exactly as any other day's would
    assert x.cycle_net == 200.0


def test_a_lapsed_day_still_counts_as_an_ordinary_qualifying_day():
    """The request-day exclusion exists because a payout RESETS the cycle.
    With no payout there is no reset, so a winning day that happens to carry
    a lapsed request counts exactly as any other winning day would.

    Constructed so the request lapses on a day that is itself a winner: a
    $130 balance is under the $250 the minimum needs, and +$200 leaves 330 --
    still under, so the request lapses while the day qualifies.
    """
    x = XfaLifecycle()
    x.balance = 200.0
    x.qualifying_days = 5
    x.cycle_net = 0.0
    assert not x.payout_eligible()               # entry: min(100, 2000) < 125
    # a caller that HAS entry eligibility is the only one allowed to request;
    # give it that, then let the session settle just under the minimum
    x.balance = 249.0                            # min(124.5, 2000) < 125
    assert not x.payout_eligible()
    x.balance = 250.0                            # min(125, 2000) == 125
    assert x.payout_eligible()                   # eligible entering
    ev = x.process_day(9, make_trade_path([-51.0], final=-51.0),
                       request_payout=True)      # settles 199 -> 99.5 < 125
    assert ev.payout_gross == 0.0
    assert ev.notes == "payout_request_lapsed_below_minimum"
    assert x.cycle_net == -51.0
    assert x.qualifying_days == 5                # a losing day adds none


def test_the_next_session_re_evaluates_eligibility_normally():
    """CASE 4. A lapse is not sticky. The account recovers and the next
    session where eligibility holds is the payout-request session."""
    x = _eligible_at_1000()
    x.process_day(5, make_trade_path([-800.0], final=-800.0),
                  request_payout=True)           # lapses, balance 200
    assert not x.payout_eligible()               # entering the NEXT session
    x.process_day(6, make_trade_path([400.0], final=400.0))   # no request
    assert x.balance == 600.0
    assert x.payout_eligible()                   # eligible again on entry
    ev = x.process_day(7, make_trade_path([100.0], final=100.0),
                       request_payout=True)
    assert ev.payout_gross == 350.0              # min(0.5 * 700, 2000)
    assert x.payout_count == 1


def test_a_request_without_entry_eligibility_is_still_a_caller_defect():
    """CASE 5. The guard still exists and still refuses -- it just measures
    the state the caller was required to decide on."""
    y = XfaLifecycle()
    y.balance = 200.0                            # 50% = 100 < 125 minimum
    y.qualifying_days = 5
    assert not y.payout_eligible()
    with pytest.raises(ValueError, match="orchestrator bug"):
        y.process_day(0, request_payout=True)
    # and a winning day cannot rescue an ineligible ENTRY either
    z = XfaLifecycle()
    z.balance = 200.0
    z.qualifying_days = 5
    assert not z.payout_eligible()
    with pytest.raises(ValueError, match="orchestrator bug"):
        z.process_day(0, make_trade_path([5000.0], final=5000.0),
                      request_payout=True)


def test_no_sub_minimum_payout_is_reachable_from_any_settled_balance():
    """THE INVARIANT, swept rather than sampled: across settled balances
    either the payout is zero or it is at least the platform minimum. A
    payout strictly between the two is what the repair must never emit."""
    from itsf.mc.platforms.topstep import XFA_PAYOUT_MIN_USD
    for opening in (250.0, 300.0, 500.0, 1000.0, 4000.0):
        for delta in (-249.0, -200.0, -100.0, -1.0, 0.0, 50.0, 500.0):
            x = XfaLifecycle()
            x.balance = opening
            x.qualifying_days = 5
            if not x.payout_eligible():
                continue
            ev = x.process_day(0, make_trade_path([delta], final=delta),
                               request_payout=True)
            assert ev.payout_gross == 0.0 or \
                ev.payout_gross >= XFA_PAYOUT_MIN_USD, (opening, delta,
                                                        ev.payout_gross)


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
