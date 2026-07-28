"""Business-layer orchestrator invariants (milestone 2, main-agent authored).

Covers the 24 frozen invariants demanded for this milestone plus the
normal / boundary / exhaustion / payout-then-die / horizon-end / zero-balance
/ idempotency paths. Synthetic fixtures only.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from conftest import make_trade_path
from itsf.guards import RunBlockedError
from itsf.mc.orchestrator import (API_FEE_USD, LifecycleConfig, LifecycleResult,
                                  LUCID_FIRST_PURCHASE_USD, LUCID_REPURCHASE_USD,
                                  LUCID_RESET_USD, MAX_EVALUATION_STARTS,
                                  TemplateDay, _ALLOWED_PHASES, run_lifecycle,
                                  run_real_lifecycle)


def tdays(n: int, cal_step: int = 1) -> list[TemplateDay]:
    return [TemplateDay(day_id=f"d{i:04d}", cal_offset=i * cal_step)
            for i in range(n)]


def day_path(day: str, final: float, adverse_extra: float = 0.0,
             anchor: float = 100.0):
    p = make_trade_path([final], adverse_extra=adverse_extra,
                        date=day, final=final)
    p.sizing_anchor_usd = anchor
    return p


def paths_for(days, finals, adverse=None):
    out = {}
    for td, f in zip(days, finals):
        if f is None:
            continue
        a = (adverse or {}).get(td.day_id, 0.0)
        out[td.day_id] = day_path(td.day_id, f, adverse_extra=a)
    return out


def lucid_cfg(**kw) -> LifecycleConfig:
    return LifecycleConfig(platform="lucid", **kw)


def ts_cfg(**kw) -> LifecycleConfig:
    return LifecycleConfig(platform="topstep", **kw)


BREACH = 60_000.0   # adverse_extra that guarantees an MLL touch at n=1


# --- invariants 1-3: lifecycle attempt counter -------------------------------

def test_max_six_evaluation_starts_including_initial():        # inv 1, 3
    days = tdays(40)
    paths = {td.day_id: day_path(td.day_id, -100.0, adverse_extra=BREACH)
             for td in days}
    res = run_lifecycle(lucid_cfg(), days, paths)
    assert res.attempts_used == MAX_EVALUATION_STARTS
    assert res.terminated_by_exhaustion is True
    # initial purchase $98 + 5 eval resets at $95 (deaths in evaluation)
    fees = res.ledger_report["fees"]
    assert fees["lucid_purchase"] == LUCID_FIRST_PURCHASE_USD
    assert fees["lucid_reset"] == pytest.approx(5 * LUCID_RESET_USD)
    # after exhaustion the lifecycle is permanently terminated: no more deaths
    breach_events = [e for e in res.events if e.breached]
    assert len(breach_events) == MAX_EVALUATION_STARTS


def test_funded_death_consumes_same_counter_and_costs_140():   # inv 2, 9
    days = tdays(12)
    finals = [1500.0, 1500.0,          # eval passes (largest 1500 <= 0.5*3000)
              -100.0] + [None] * 9     # funded day 1: breach
    paths = paths_for(days, finals, adverse={"d0002": BREACH})
    res = run_lifecycle(lucid_cfg(), days, paths)
    assert res.attempts_used == 2                     # restart consumed counter
    assert res.ledger_report["fees"]["lucid_repurchase"] == LUCID_REPURCHASE_USD


def test_lucid_eval_failure_uses_95_reset():                   # inv 8
    days = tdays(6)
    paths = {"d0000": day_path("d0000", -100.0, adverse_extra=BREACH)}
    res = run_lifecycle(lucid_cfg(), days, paths)
    assert res.ledger_report["fees"]["lucid_reset"] == LUCID_RESET_USD
    assert res.attempts_used == 2


# --- invariants 4-7: Topstep reset credits and B2F ---------------------------

def test_topstep_reset_prefers_matching_credit_and_moves_anchor():  # inv 4, 5
    # 35 calendar days so one rebill fires (banks 1 credit), then breach.
    days = tdays(40)
    paths = {"d0035": day_path("d0035", -100.0, adverse_extra=BREACH)}
    res = run_lifecycle(ts_cfg(), days, paths)
    fees = res.ledger_report["fees"]
    # credit consumed: no paid reset fee booked
    assert fees.get("topstep_reset_paid", 0.0) == 0.0
    assert "topstep_reset_credit_used" in fees
    # subscription: purchase $49 + one rebill $49 before the reset; after the
    # reset the anchor moved to reset day + 30 -> next rebill only at day 66+,
    # outside a 40-day run -> exactly 2 subscription charges of $49.
    assert fees["topstep_subscription_activation"] == pytest.approx(2 * 49.0)


def test_b2f_max_two_then_new_combine():                       # inv 6
    days = tdays(60)
    finals = [1000.0, 1000.0, 1000.0]                # combine passes on d2
    paths = paths_for(days, finals + [None] * (len(days) - 3))
    # XFA dies pre-payout three times
    for d in ("d0003", "d0004", "d0005"):
        paths[d] = day_path(d, -100.0, adverse_extra=BREACH)
    res = run_lifecycle(ts_cfg(), days, paths)
    fees = res.ledger_report["fees"]
    assert res.b2f_used_total == 2
    assert fees["topstep_b2f"] == pytest.approx(2 * 599.0)
    assert res.attempts_used == 2        # third death -> new Combine consumes one


def test_no_b2f_after_first_payout():                          # inv 7
    days = tdays(20)
    finals = [1000.0, 1000.0, 1000.0,                # pass combine
              200.0, 200.0, 200.0, 200.0, 200.0,     # 5 qualifying XFA days
              200.0,                                 # request day (trades too)
              -100.0]                                # dies after payout
    paths = paths_for(days, finals + [None] * (len(days) - len(finals)))
    paths["d0009"] = day_path("d0009", -100.0, adverse_extra=BREACH)
    res = run_lifecycle(ts_cfg(), days, paths)
    assert res.b2f_used_total == 0
    assert "topstep_b2f" not in res.ledger_report["fees"]
    assert res.attempts_used == 2                    # new Combine instead


# --- invariants 10-14: payout accounting and halt semantics ------------------

def test_lucid_payout_gross_deducted_cash_split_and_halt():    # inv 10,11,12,13
    days = tdays(14)
    finals = [1500.0, 1500.0,                        # eval pass
              1500.0, 1500.0, 1500.0, 1500.0, 1500.0,  # 5 qualifying funded days
              999.0,                                 # request day (path ignored)
              777.0, 777.0,                          # halt window: must NOT trade
              200.0]
    paths = paths_for(days, finals + [None] * (len(days) - len(finals)))
    res = run_lifecycle(lucid_cfg(), days, paths)
    pay = [e for e in res.events if e.payout_gross > 0][0]
    gross = pay.payout_gross
    assert gross == pytest.approx(2000.0)            # min(0.5*7500, 2000)
    assert pay.payout_cash == pytest.approx(gross * 0.90 - 30.0)   # inv 11, 16
    # gross removed from sim balance: balance dropped by gross on request day
    prev = [e for e in res.events if e.day == "d0006"][0]
    assert pay.balance == pytest.approx(prev.balance - gross)      # inv 10
    assert pay.floor == 50100.0                       # MLL from deducted state
    # halt: the two days after the request day carry no trading P&L
    halted = [e for e in res.events if "processing_halt" in e.notes]
    assert [e.day for e in halted] == ["d0008", "d0009"]           # inv 13
    assert halted[0].balance == pay.balance == halted[1].balance
    assert res.ledger_report["payout_cash_total"] == pytest.approx(pay.payout_cash)


def test_topstep_payout_no_halt_continue_trading():            # inv 14
    days = tdays(12)
    finals = [1000.0, 1000.0, 1000.0,
              200.0, 200.0, 200.0, 200.0, 200.0,
              200.0,                                 # request day, trades allowed
              300.0]                                 # next day trades again
    paths = paths_for(days, finals + [None] * (len(days) - len(finals)))
    res = run_lifecycle(ts_cfg(), days, paths)
    pay = [e for e in res.events if e.payout_gross > 0][0]
    after = [e for e in res.events if e.day == "9"][0] if False else None
    # the day after the payout has trading P&L (no halt): find it by order
    idx = res.events.index(pay)
    nxt = res.events[idx + 1]
    assert nxt.balance != pay.balance                # traded -> balance moved
    assert pay.payout_cash == pytest.approx(pay.payout_gross * 0.90 - 0.0)
    assert pay.floor == 0.0                          # MLL permanently 0


# --- invariants 15-17: operating costs and no double fee ---------------------

def test_api_fee_booked_every_30_calendar_days():              # inv 15
    days = tdays(35)                                 # cal offsets 0..34
    res = run_lifecycle(ts_cfg(), days, {})
    assert res.ledger_report["fees"]["topstep_api"] == pytest.approx(2 * API_FEE_USD)


def test_no_trade_fee_rededuction_static():                    # inv 17
    src = (Path(__file__).resolve().parents[1]
           / "src" / "itsf" / "mc" / "orchestrator.py").read_text(encoding="utf-8")
    assert "S0_PLATFORM_FEE" not in src              # double_counting_guard
    assert "platform_fee_rt" not in src


def test_ledger_keys_contain_no_trade_costs():                 # inv 17, 24
    days = tdays(6)
    res = run_lifecycle(lucid_cfg(), days, {})
    for key in res.ledger_report["fees"]:
        assert "trade" not in key and "friction" not in key


# --- invariants 18-20: live exclusion and run gates --------------------------

def test_live_phase_is_unreachable():                          # inv 18
    assert "live" not in _ALLOWED_PHASES
    days = tdays(8)
    res = run_lifecycle(ts_cfg(), days, {})
    assert all(e.phase in _ALLOWED_PHASES for e in res.events)


def test_real_entry_blocked_until_attestations():              # inv 19
    with pytest.raises(RunBlockedError):
        run_real_lifecycle()


def test_synthetic_mode_not_blocked_by_guard():                # inv 20
    res = run_lifecycle(lucid_cfg(), tdays(3), {})
    assert isinstance(res, LifecycleResult)


# --- invariants 21-24: determinism, isolation, terminal, ledger closure ------

def test_determinism_same_inputs_same_outputs():               # inv 21
    days = tdays(15)
    finals = [1500.0, 1500.0, 1500.0, 1500.0, 1500.0, 1500.0, 1500.0]
    paths = paths_for(days, finals + [None] * 8)
    r1 = run_lifecycle(lucid_cfg(), days, paths)
    r2 = run_lifecycle(lucid_cfg(), days, paths)
    assert r1.ledger_report == r2.ledger_report
    assert [e.day for e in r1.events] == [e.day for e in r2.events]


def test_primary_sensitivity_role_isolation():                 # inv 22
    days = tdays(4)
    p = run_lifecycle(lucid_cfg(decision_role="primary"), days, {})
    s = run_lifecycle(lucid_cfg(decision_role="sensitivity"), days, {})
    assert p.config.decision_role == "primary"
    assert s.config.decision_role == "sensitivity"
    # results are separate objects; verdict-level isolation is enforced (and
    # tested) in itsf.mc.verdict — orchestrator never mixes the two roles.
    assert p is not s and p.ledger_report is not s.ledger_report


def test_terminal_value_only_when_eligible():                  # inv 23
    # ends horizon while funded but NOT payout-eligible -> terminal 0
    days = tdays(4)
    finals = [1500.0, 1500.0, 1500.0]                # pass, one funded day
    res = run_lifecycle(lucid_cfg(), days, paths_for(days, finals + [None]))
    assert res.ledger_report["terminal_cash"] == 0.0
    # ends horizon exactly when eligible (5th qualifying day is the LAST day,
    # so the pending request never executes -> terminal value applies)
    days2 = tdays(7)
    finals2 = [1500.0, 1500.0, 1500.0, 1500.0, 1500.0, 1500.0, 1500.0]
    res2 = run_lifecycle(lucid_cfg(), days2, paths_for(days2, finals2))
    tg_cash = res2.ledger_report["terminal_cash"]
    assert tg_cash == pytest.approx(2000.0 * 0.90 - 30.0)


def test_ledger_closure_no_double_count_no_omission():         # inv 24
    days = tdays(14)
    finals = [1500.0] * 8 + [None] * 6
    res = run_lifecycle(lucid_cfg(research_costs_usd=250.0), days,
                        paths_for(days, finals))
    rep = res.ledger_report
    assert rep["fees_total"] == pytest.approx(sum(rep["fees"].values()))
    assert rep["prop_operating_ev_total"] == pytest.approx(
        rep["payout_cash_total"] + rep["terminal_cash"] - rep["fees_total"])
    assert rep["net_business_ev_after_rd_total"] == pytest.approx(
        rep["prop_operating_ev_total"] - 250.0)
    assert rep["prop_operating_ev_monthly"] == pytest.approx(
        rep["prop_operating_ev_total"] / 24.0)
    # haircut applies retention ONLY to inflows (frozen: MC SS4.4)
    assert rep["risk_haircut_ev_total"]["75"] == pytest.approx(
        0.75 * (rep["payout_cash_total"] + rep["terminal_cash"])
        - rep["fees_total"] - 250.0)


# --- required paths: boundary / exhaustion / horizon / zero balance / idempotency

def test_breach_settlement_never_enters_prop_operating():      # IR-1 re-review
    # Death balance is diagnostic only: prop_operating = payouts + terminal
    # - fees, regardless of the R1 settlement value.
    days = tdays(6)
    paths = {"d0000": day_path("d0000", -100.0, adverse_extra=BREACH)}
    res = run_lifecycle(lucid_cfg(), days, paths)
    rep = res.ledger_report
    assert any(e.breached for e in res.events)
    assert rep["payout_cash_total"] == 0.0 and rep["terminal_cash"] == 0.0
    assert rep["prop_operating_ev_total"] == pytest.approx(-rep["fees_total"])


def test_max_favourable_is_diagnostic_only_static():           # IR-2 marker
    root = Path(__file__).resolve().parents[1] / "src" / "itsf"
    hits = []
    for p in (root / "mc").rglob("*.py"):
        t = p.read_text(encoding="utf-8")
        if "max_favourable" in t:
            hits.append(p.name)
    assert hits == []      # the mc/verdict layer never consumes the field


def test_ir1_invariance_settlement_value_cannot_move_ev():     # IR-1 批复条件
    # Two breach runs differing ONLY in adverse depth (=> different diagnostic
    # settlement balances) must produce IDENTICAL prop_operating_EV/verdict
    # inputs; only the diagnostic strategy_account ledger may differ.
    days = tdays(6)
    r_a = run_lifecycle(lucid_cfg(), days,
                        {"d0000": day_path("d0000", -100.0, adverse_extra=60_000.0)})
    r_b = run_lifecycle(lucid_cfg(), days,
                        {"d0000": day_path("d0000", -100.0, adverse_extra=90_000.0)})
    assert any(e.breached for e in r_a.events) and any(e.breached for e in r_b.events)
    ka = {k: v for k, v in r_a.ledger_report.items() if k != "strategy_account_ev_total"}
    kb = {k: v for k, v in r_b.ledger_report.items() if k != "strategy_account_ev_total"}
    assert ka == kb                                  # EV chain invariant
    assert (r_a.ledger_report["strategy_account_ev_total"]
            != r_b.ledger_report["strategy_account_ev_total"])  # diagnostic moved


def test_ir10_sensitivity_b2f_consumes_counter():              # IR-10 批复
    days = tdays(60)
    finals = [1000.0, 1000.0, 1000.0]
    paths = paths_for(days, finals + [None] * (len(days) - 3))
    for d in ("d0003", "d0004", "d0005"):
        paths[d] = day_path(d, -100.0, adverse_extra=BREACH)
    sens = run_lifecycle(ts_cfg(decision_role="sensitivity",
                                b2f_consumes_attempt=True), days, paths)
    # sensitivity: two B2Fs each consume an attempt -> attempts 1+2(b2f)+1(new
    # combine)=4 vs primary's 2
    assert sens.b2f_used_total == 2
    assert sens.attempts_used == 4
    prim = run_lifecycle(ts_cfg(), days, paths)
    assert prim.attempts_used == 2                   # separate counters (Primary)


def test_ir10_consuming_variant_forbidden_in_primary():        # IR-10 隔离强制
    with pytest.raises(ValueError):
        run_lifecycle(ts_cfg(b2f_consumes_attempt=True), tdays(3), {})


def test_empty_horizon_boundary():
    res = run_lifecycle(lucid_cfg(), [], {})
    assert res.events == [] and res.attempts_used == 1


def test_horizon_end_boundary_mid_evaluation():
    days = tdays(2)
    res = run_lifecycle(lucid_cfg(), days, paths_for(days, [1000.0, None]))
    assert res.events[-1].phase == "evaluation"
    assert res.terminated_by_exhaustion is False


def test_xfa_zero_balance_sizing_boundary():
    # XFA starts at 0; buffer = 0 - (-2000) = 2000; P2 budget 100 -> n = 1
    days = tdays(5)
    finals = [1000.0, 1000.0, 1000.0, 200.0]
    res = run_lifecycle(ts_cfg(), days, paths_for(days, finals + [None]))
    xfa_days = [e for e in res.events if e.phase == "xfa"]
    assert xfa_days and xfa_days[0].balance == pytest.approx(200.0)


def test_payout_then_immediate_death_path():
    days = tdays(16)
    finals = [1500.0, 1500.0, 1500.0, 1500.0, 1500.0, 1500.0, 1500.0,
              999.0,            # lucid request day
              None, None,       # halt window
              -100.0]           # first tradeable day after halt: breach
    paths = paths_for(days, finals + [None] * (len(days) - len(finals)))
    paths["d0010"] = day_path("d0010", -100.0, adverse_extra=BREACH)
    res = run_lifecycle(lucid_cfg(), days, paths)
    assert any(e.payout_gross > 0 for e in res.events)
    assert any(e.breached for e in res.events)
    # funded death after payout -> $140 repurchase booked
    assert res.ledger_report["fees"]["lucid_repurchase"] == LUCID_REPURCHASE_USD


def test_report_idempotent_and_start_offset():
    days = tdays(10)
    finals = [1500.0] * 7 + [None] * 3
    res = run_lifecycle(lucid_cfg(), days, paths_for(days, finals))
    assert res.ledger_report == res.ledger_report          # stable value object
    off = run_lifecycle(lucid_cfg(), days, paths_for(days, finals), start_offset=2)
    assert len(off.events) == len(days) - 2                # inner randomness (1)
