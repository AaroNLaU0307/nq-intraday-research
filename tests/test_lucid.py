"""Tests for LucidLifecycle. Synthetic paths ONLY (conftest generators);
no real market data, no research numbers (frozen: G9 hard_run_blocker)."""
from __future__ import annotations

import pytest
from conftest import make_trade_path

from itsf.mc.platforms.lucid import LucidLifecycle


def day_path(pnl: float, adverse_extra: float = 0.0, date: str = "2026-08-03"):
    """Two-minute per-contract path ending at `pnl` USD (close == adverse
    when adverse_extra == 0)."""
    return make_trade_path([0.0, float(pnl)], adverse_extra=adverse_extra, date=date)


def make_funded(fee: float = 98.0) -> LucidLifecycle:
    """Pass evaluation with 2 x +1500 days (exactly at the 50% consistency
    boundary: 1500 <= 0.5 * 3000)."""
    acct = LucidLifecycle(fee_usd=fee)
    acct.step_day(day_path(1500.0), 1)
    ev = acct.step_day(day_path(1500.0), 1)
    assert ev.phase == "funded"
    return acct


class TestEvaluation:
    def test_fee_recorded_on_first_event_only(self):
        acct = LucidLifecycle(fee_usd=98.0)
        ev1 = acct.step_day(day_path(100.0), 1)
        ev2 = acct.step_day(day_path(100.0), 1)
        assert ev1.fees_usd == 98.0  # frozen: evaluation.fees first_purchase_usd
        assert ev2.fees_usd == 0.0   # one_time_no_rebilling

    def test_subsequent_repurchase_fee_pass_through(self):
        # frozen: evaluation.fees subsequent_repurchase_primary_usd 140 (caller's choice)
        acct = LucidLifecycle(fee_usd=140.0)
        assert acct.step_day(day_path(50.0), 1).fees_usd == 140.0

    def test_target_alone_does_not_pass_without_consistency(self):
        acct = LucidLifecycle(fee_usd=98.0)
        acct.step_day(day_path(2000.0), 1)
        # profit 3000 >= target, but largest day 2000 > 0.5*3000 -> blocked
        ev = acct.step_day(day_path(1000.0), 1)
        assert ev.phase == "evaluation"
        # profit 4000, largest 2000 <= 0.5*4000 -> passes now
        ev = acct.step_day(day_path(1000.0), 1)
        assert ev.phase == "funded"
        assert ev.balance == 50000.0  # fresh funded balance
        assert ev.floor == 48000.0    # fresh floor geometry

    def test_pass_at_exact_50_pct_boundary(self):
        acct = make_funded()  # 1500/3000 == 0.50 exactly -> pass (<=, strict formula)
        assert acct.phase == "funded"

    def test_eval_max_contracts_is_40_micros_no_scaling(self):
        # frozen: evaluation.max_position micros 40; scaling_in_evaluation none
        acct = LucidLifecycle(fee_usd=98.0)
        assert acct.max_contracts_today() == 40


class TestTrailingFloor:
    def test_trail_rises_and_locks_at_50100(self):
        acct = LucidLifecycle(fee_usd=98.0)
        ev = acct.step_day(day_path(500.0), 1)
        assert ev.floor == 48500.0    # max(48000, 50500-2000)
        ev = acct.step_day(day_path(2500.0), 1)   # balance 53000
        assert ev.floor == 50100.0    # locked (min with lock_at)
        assert ev.phase == "evaluation"  # consistency blocks pass (2500 > 1500)
        ev = acct.step_day(day_path(-100.0), 1)   # balance falls
        assert ev.floor == 50100.0    # floor never retreats


class TestBreach:
    def test_adverse_spike_breaches_while_close_path_survives(self):
        # adverse min -2100 vs 2000 gap to floor -> breach on adverse path only
        spike = day_path(100.0, adverse_extra=2100.0)
        dead = LucidLifecycle(fee_usd=98.0)
        ev = dead.step_day(spike, 1)
        assert ev.breached and ev.phase == "dead"
        # Ruling R1: min(floor 48000, eq_at_trigger 47900) - 1*$1 = 47899
        assert ev.balance == 47899.0
        assert dead.max_contracts_today() == 0

        alive = LucidLifecycle(fee_usd=98.0)
        ev = alive.step_day(day_path(100.0), 1)  # same close path, no spike
        assert not ev.breached and ev.phase == "evaluation"
        assert ev.balance == 50100.0

    def test_breach_scales_with_contract_count(self):
        path = day_path(100.0, adverse_extra=1100.0)  # per-contract adverse min -1100
        one = LucidLifecycle(fee_usd=98.0)
        assert not one.step_day(path, 1).breached     # -1100 stays above 48000
        two = LucidLifecycle(fee_usd=98.0)
        assert two.step_day(path, 2).breached         # 2 x -1100 touches 47800 <= 48000

    def test_dead_account_is_inert(self):
        acct = LucidLifecycle(fee_usd=98.0)
        acct.step_day(day_path(100.0, adverse_extra=2100.0), 1)
        ev = acct.step_day(day_path(500.0), 1)
        assert ev.phase == "dead"
        assert ev.balance == 47899.0   # Ruling R1 settlement, inert thereafter
        assert ev.payout_gross == 0.0


class TestFundedPayouts:
    def test_payout_resets_floor_count_and_can_downgrade_scaling(self):
        acct = make_funded()
        assert acct.max_contracts_today() == 20  # first funded day lowest tier (frozen: N6)
        for _ in range(4):
            acct.step_day(day_path(300.0), 1)
        assert acct.max_contracts_today() == 30  # profit 1200 -> tier [1000,2000)
        ev = acct.step_day(day_path(300.0), 1)   # 5th qualifying day, profit 1500
        assert "payout_eligible" in ev.notes
        assert acct.max_contracts_today() == 0   # halt: request day is next session
        assert acct.eligible_terminal_gross() == pytest.approx(750.0)

        ev = acct.step_day(day_path(999.0), 1)   # request day: supplied path must be IGNORED
        assert ev.payout_gross == pytest.approx(750.0)  # min(0.5*1500, 2000)
        assert ev.payout_cash == pytest.approx(750.0 * 0.90 - 30.0)  # split 90, rail 30
        assert ev.balance == pytest.approx(50750.0)     # 51500 - gross, NOT +999
        assert ev.floor == 50100.0               # payout_effect: mll -> 50100
        assert acct.max_contracts_today() == 20  # downgraded from 30 (bidirectional)
        assert acct.eligible_terminal_gross() == 0.0  # qualifying count restarted

    def test_qualifying_count_restarts_each_cycle(self):
        acct = make_funded()
        for _ in range(5):
            acct.step_day(day_path(300.0), 1)
        acct.step_day(None, 0)                   # payout request day
        for _ in range(4):
            ev = acct.step_day(day_path(300.0), 1)
            assert ev.payout_gross == 0.0
        assert acct.eligible_terminal_gross() == 0.0  # only 4 new qualifying days
        acct.step_day(day_path(300.0), 1)        # 5th new qualifying day
        # profit 750 + 1500 = 2250 -> min(1125, 2000)
        assert acct.eligible_terminal_gross() == pytest.approx(1125.0)

    def test_min_request_500_waits(self):
        acct = make_funded()
        for _ in range(5):
            acct.step_day(day_path(160.0), 1)    # 5 qualifying days, profit 800
        assert acct.max_contracts_today() == 20  # gross 400 < 500 -> wait, no halt
        assert acct.eligible_terminal_gross() == 0.0
        acct.step_day(day_path(160.0), 1)        # profit 960 -> gross 480, still waits
        ev = acct.step_day(day_path(160.0), 1)   # profit 1120 -> gross 560 >= 500
        assert "payout_eligible" in ev.notes
        assert acct.step_day(None, 0).payout_gross == pytest.approx(560.0)

    def test_negative_profit_tier_floor_2_lots_with_g7_flag(self):
        acct = make_funded()
        for _ in range(4):
            acct.step_day(day_path(400.0), 1)    # profit 1600 -> tier 30 (only 4 qual. days)
        assert acct.max_contracts_today() == 30
        ev = acct.step_day(day_path(-1700.0), 1)  # profit -100, no breach (floor 49600)
        assert not ev.breached
        assert acct.max_contracts_today() == 20   # frozen: G7 conservative lowest tier
        assert "G7" in ev.notes                   # mandatory disclosure flag

    def test_five_payout_cap_then_remain_sim(self):
        acct = make_funded()
        grosses = []
        for _ in range(5):
            for _ in range(5):
                acct.step_day(day_path(300.0), 1)
            ev = acct.step_day(None, 0)           # request day
            grosses.append(ev.payout_gross)
        assert grosses == pytest.approx([750.0, 1125.0, 1312.5, 1406.25, 1453.125])
        # cap reached: account remains sim, keeps trading, never pays out again
        bal_before = acct.balance
        for _ in range(5):                        # 5 more qualifying-grade days
            ev = acct.step_day(day_path(300.0), 1)
            assert ev.phase == "funded"
            assert ev.payout_gross == 0.0
            assert "remain_sim" in ev.notes
        assert acct.balance == pytest.approx(bal_before + 1500.0)  # still trading
        assert acct.max_contracts_today() > 0     # no payout halt pending
        assert acct.eligible_terminal_gross() == 0.0  # frozen: MC SS2.6 no further payouts
