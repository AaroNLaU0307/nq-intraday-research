"""Platform-authoritative day facts on AccountEvent (lane S2 / node N02).

WHAT THIS FILE DEFENDS
----------------------
Every consumer of the MC event stream used to have to guess a day's trading
result from adjacent balances. That reading is wrong on two whole classes of
day, both in the unsafe direction:

  * PAYOUT DAYS — the platform removes the payout gross from the sim balance
    (frozen: platform_params payout_accounting.account_balance_effect), so a
    balance difference reports the best day of the cycle as a big loss;
  * BALANCE-RESET BOUNDARIES — evaluation->funded, Combine reset, Combine
    pass -> XFA, Back2Funded, new Combine: the balance is REPLACED, so the
    difference across the boundary is a phantom.

The platforms now emit the facts directly. These tests pin the emission, the
tri-state semantics, the generation boundaries, and — with explicit baseline
counterexamples — that the old balance-difference readings really are wrong.

ORACLE DISCIPLINE: every expected number below is derived by hand from the
frozen parameters cited inline (never by calling the production reducer).
SYNTHETIC ONLY: conftest generators; no real market data, no research values.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from conftest import make_trade_path

from itsf.contracts import (DAY_FACT_REJECTION_CODES,
                            FACT_CAP_FLAG_INCONSISTENT,
                            FACT_DAY_NET_NOT_FINITE,
                            FACT_NEGATIVE_CONTRACTS,
                            FACT_NEGATIVE_GENERATION,
                            FACT_OVER_BUDGET_STATUS_TYPE,
                            FACT_OVER_BUDGET_UNRULED,
                            FACT_QUALIFYING_PHASE_MISMATCH,
                            FACT_TRADED_EXCEEDS_REQUESTED,
                            OVER_BUDGET_PREDICATE_RULED, QUALIFYING_PHASES,
                            AccountEvent, AuthoritativeFactError,
                            OverBudgetStatus)
from itsf.mc import orchestrator as orch
from itsf.mc.platforms import authoritative as auth
from itsf.mc.platforms.lucid import (QUALIFYING_DAY_MIN_USD,
                                     START_BALANCE_USD, LucidLifecycle)
from itsf.mc.platforms.topstep import (COMBINE_MAX_MICROS,
                                       XFA_QUALIFYING_DAY_MIN_NET_USD,
                                       CombineLifecycle, SubscriptionEngine,
                                       XfaLifecycle)
from itsf.mc.orchestrator import (LifecycleConfig, TemplateDay, run_lifecycle)

BREACH = 60_000.0            # adverse_extra guaranteeing an MLL touch at n=1
REPO = Path(__file__).resolve().parents[1]


# --------------------------------------------------------------------------
# fixtures / helpers (no production formulas are replicated here)
# --------------------------------------------------------------------------

def tdays(n: int, step: int = 1) -> list[TemplateDay]:
    return [TemplateDay(day_id=f"d{i:04d}", cal_offset=i * step)
            for i in range(n)]


def day_path(day: str, final: float, adverse_extra: float = 0.0,
             anchor: float = 100.0, engine: str = "E1"):
    p = make_trade_path([final], adverse_extra=adverse_extra, date=day,
                        final=final, engine=engine)
    p.sizing_anchor_usd = anchor
    return p


def paths_for(days, finals, adverse=None, anchor=100.0, engine="E1"):
    out = {}
    for td, f in zip(days, finals):
        if f is None:
            continue
        a = (adverse or {}).get(td.day_id, 0.0)
        out[td.day_id] = day_path(td.day_id, f, adverse_extra=a, anchor=anchor,
                                  engine=engine)
    return out


def unit_path(pnl: float, adverse_extra: float = 0.0, engine: str = "E1"):
    """Two-minute per-contract path ending at `pnl` (as in tests/test_lucid)."""
    return make_trade_path([0.0, float(pnl)], adverse_extra=adverse_extra,
                           date="2026-08-03", engine=engine)


def make_funded(fee: float = 98.0) -> LucidLifecycle:
    """Pass Lucid evaluation with 2 x +1500 (exactly the 50% consistency
    boundary: 1500 <= 0.5 * 3000)."""
    a = LucidLifecycle(fee_usd=fee)
    a.step_day(unit_path(1500.0), 1)
    ev = a.step_day(unit_path(1500.0), 1)
    assert ev.phase == "funded"
    return a


# The scenario battery every sweep test runs over. Hand-built, deterministic.
def _battery():
    out = {}

    d = tdays(3)
    out["lucid_simple"] = ("lucid", d, paths_for(d, [300.0, 200.0, None]), {})

    d = tdays(2)
    out["lucid_eval_pass"] = ("lucid", d, paths_for(d, [1500.0, 1500.0]), {})

    d = tdays(14)
    f = [1500.0] * 7 + [999.0, 777.0, 777.0, 200.0]
    out["lucid_payout_halt"] = ("lucid", d, paths_for(d, f + [None] * 3), {})

    d = tdays(40)
    out["lucid_exhaustion"] = (
        "lucid", d,
        {t.day_id: day_path(t.day_id, -100.0, adverse_extra=BREACH) for t in d},
        {})

    d = tdays(12)
    out["lucid_funded_death"] = (
        "lucid", d,
        paths_for(d, [1500.0, 1500.0, -100.0] + [None] * 9,
                  adverse={"d0002": BREACH}), {})

    d = tdays(16)
    p = paths_for(d, [1500.0] * 7 + [999.0, None, None, -100.0] + [None] * 5)
    p["d0010"] = day_path("d0010", -100.0, adverse_extra=BREACH)
    out["lucid_payout_then_death"] = ("lucid", d, p, {})

    d = tdays(4)
    out["lucid_cap_clamp"] = ("lucid", d,
                              paths_for(d, [10.0] * 3 + [None], anchor=1.0), {})

    d = tdays(5)
    out["lucid_skip_n0"] = ("lucid", d,
                            paths_for(d, [300.0] * 4 + [None], anchor=150.0), {})

    d = tdays(20)
    f = [1000.0] * 3 + [200.0] * 6 + [-100.0]
    p = paths_for(d, f + [None] * 10)
    p["d0009"] = day_path("d0009", -100.0, adverse_extra=BREACH)
    out["topstep_payout_then_new_combine"] = ("topstep", d, p, {})

    d = tdays(60)
    p = paths_for(d, [1000.0] * 3 + [None] * 57)
    for k in ("d0003", "d0004", "d0005"):
        p[k] = day_path(k, -100.0, adverse_extra=BREACH)
    out["topstep_b2f_twice"] = ("topstep", d, p, {})

    d = tdays(40)
    out["topstep_reset_credit"] = (
        "topstep", d, {"d0035": day_path("d0035", -100.0, adverse_extra=BREACH)},
        {})

    d = tdays(12)
    f = [1000.0] * 3 + [200.0] * 6 + [300.0]
    out["topstep_payout_no_halt"] = ("topstep", d, paths_for(d, f + [None] * 2),
                                     {})

    d = tdays(6)
    out["topstep_cap_clamp"] = ("topstep", d,
                                paths_for(d, [10.0] * 5 + [None], anchor=1.0), {})

    d = tdays(35)
    out["topstep_api_only"] = ("topstep", d, {}, {})

    d = tdays(15)
    out["lucid_rd_costs"] = ("lucid", d, paths_for(d, [1500.0] * 8 + [None] * 7),
                             {"research_costs_usd": 250.0})

    d = tdays(10)
    out["lucid_e2_engine"] = ("lucid", d,
                              paths_for(d, [1500.0] * 7 + [None] * 3,
                                        engine="E2"), {})
    return out


BATTERY = _battery()


def run_scenario(name):
    platform, days, paths, kw = BATTERY[name]
    return run_lifecycle(LifecycleConfig(platform=platform, **kw), days, paths)


def by_day(res, day_id):
    return [e for e in res.events if e.day == day_id][0]


# ==========================================================================
# 1. POSITIVE — the facts are emitted, with hand-computed values
# ==========================================================================

def test_lucid_evaluation_day_emits_every_fact():
    # frozen: evaluation.max_position micros 40; P2 budget $100 / anchor $100
    # -> the caller asks for 1 micro. day net = 1 x $300.
    acct = LucidLifecycle(fee_usd=98.0)
    ev = acct.step_day(unit_path(300.0), 1)
    assert ev.phase == "evaluation"
    assert ev.day_net_usd == pytest.approx(300.0)
    assert ev.balance == pytest.approx(START_BALANCE_USD + 300.0)
    assert ev.qualifying_day is None          # evaluation has no such concept
    assert ev.account_generation == 0
    assert (ev.requested_n, ev.traded_n, ev.cap_applied) == (1, 1, False)
    assert ev.over_budget is None
    assert ev.over_budget_status is OverBudgetStatus.NOT_APPLICABLE   # E1


def test_lucid_funded_qualifying_day_is_the_platform_counter_at_the_frozen_floor():
    # frozen: lucidflex_50k.payouts.qualifying_day_min_profit_usd = 150,
    # inclusive floor -> exactly $150 qualifies, $149.99 does not.
    assert QUALIFYING_DAY_MIN_USD == 150.0
    at_floor = make_funded()
    ev = at_floor.step_day(unit_path(150.0), 1)
    assert ev.phase == "funded" and ev.qualifying_day is True
    assert ev.day_net_usd == pytest.approx(150.0)

    below = make_funded()
    ev2 = below.step_day(unit_path(149.99), 1)
    assert ev2.qualifying_day is False        # measured, did NOT qualify
    assert ev2.day_net_usd == pytest.approx(149.99)


def test_xfa_qualifying_day_is_the_platform_counter_at_the_frozen_floor():
    # frozen: xfa.payout_paths.standard.qualifying "每日净利 >= $150"
    assert XFA_QUALIFYING_DAY_MIN_NET_USD == 150.0
    x = XfaLifecycle()
    ev = x.process_day(0, make_trade_path([150.0], final=150.0))
    assert ev.phase == "xfa" and ev.qualifying_day is True
    y = XfaLifecycle()
    ev2 = y.process_day(0, make_trade_path([149.99], final=149.99))
    assert ev2.qualifying_day is False


def test_combine_never_carries_a_qualifying_day():
    # frozen: qualifying days exist only under xfa.payout_paths — the Combine
    # ruleset has no such concept, so the tri-state must be None, never False.
    # 2 x +1500 with a flat day between: best_day 1500 <= 0.5 x target 3000,
    # so the soft consistency target never inflates and profit 3000 passes.
    sub = SubscriptionEngine(anchor_day=0)
    c = CombineLifecycle(subscription=sub)
    evs = [c.process_day(0, make_trade_path([1500.0], final=1500.0)),
           c.process_day(1),                                  # no-trade day
           c.process_day(2, make_trade_path([1500.0], final=1500.0))]
    assert [e.phase for e in evs] == ["combine", "combine", "done"]
    assert all(e.qualifying_day is None for e in evs)
    assert [e.day_net_usd for e in evs] == pytest.approx([1500.0, 0.0, 1500.0])


def test_no_trade_and_dead_days_report_zero_not_none():
    acct = LucidLifecycle(fee_usd=98.0)
    idle = acct.step_day(None, 0)
    assert idle.day_net_usd == 0.0            # a real measured zero
    assert idle.over_budget_status is OverBudgetStatus.NOT_APPLICABLE_NO_TRADE
    acct.step_day(unit_path(100.0, adverse_extra=2100.0), 1)   # breach
    dead = acct.step_day(unit_path(500.0), 1)
    assert dead.phase == "dead"
    assert dead.day_net_usd == 0.0            # inert: nothing traded
    assert dead.qualifying_day is None
    assert dead.traded_n == 0


def test_breach_day_reports_the_settled_loss_as_its_day_net():
    # Ruling R1 settlement (tests/test_lucid pins the value): balance goes
    # 50000 -> 47899, so the day's realized trading result is -2101.
    acct = LucidLifecycle(fee_usd=98.0)
    ev = acct.step_day(unit_path(100.0, adverse_extra=2100.0), 1)
    assert ev.breached and ev.balance == pytest.approx(47899.0)
    assert ev.day_net_usd == pytest.approx(47899.0 - 50000.0)
    assert ev.traded_n == 1                   # the position WAS on
    assert ev.qualifying_day is None          # phase 'dead'


# ==========================================================================
# 2. THE PAYOUT-DAY POLLUTION FIX (D5-5)
# ==========================================================================

def test_lucid_payout_day_net_is_zero_while_the_balance_drops_by_gross():
    # make_funded then 5 x +300 -> profit 1500 -> gross = min(0.5*1500, 2000)
    # = 750 (frozen: payouts.max_request). The request day is a HALT: no
    # trade, so its trading net is 0 even though the balance falls 750.
    acct = make_funded()
    for _ in range(5):
        acct.step_day(unit_path(300.0), 1)
    before = acct.balance
    ev = acct.step_day(unit_path(999.0), 1)   # path must be ignored (halt)
    assert ev.payout_gross == pytest.approx(750.0)
    assert ev.balance == pytest.approx(before - 750.0)
    # THE OLD READING (kept here as an executable counterexample):
    assert ev.balance - before == pytest.approx(-750.0)
    # THE AUTHORITATIVE FACT:
    assert ev.day_net_usd == 0.0
    assert ev.traded_n == 0
    assert ev.qualifying_day is False         # funded phase, counter reset


def test_xfa_payout_day_separates_trading_net_from_the_gross_deduction():
    # 5 x +200 -> balance 1000, qualifying 5. Request day also trades +200:
    # balance 1200, gross = min(0.5*1200, 2000) = 600, balance 600.
    x = XfaLifecycle()
    for d in range(5):
        x.process_day(d, make_trade_path([200.0], final=200.0))
    assert x.balance == pytest.approx(1000.0) and x.qualifying_days == 5
    ev = x.process_day(5, make_trade_path([200.0], final=200.0),
                       request_payout=True)
    assert ev.payout_gross == pytest.approx(600.0)
    assert ev.balance == pytest.approx(600.0)
    assert ev.balance - 1000.0 == pytest.approx(-400.0)   # old reading: "loss"
    assert ev.day_net_usd == pytest.approx(200.0)         # authoritative
    # frozen MC SS4.2 / payout_paths.standard.after_payout: the request day
    # counts toward NOTHING — a naive "net >= 150" re-derivation says True.
    assert ev.day_net_usd >= XFA_QUALIFYING_DAY_MIN_NET_USD
    assert ev.qualifying_day is False


def test_qualifying_day_is_not_a_threshold_rederivation():
    """PROBE: swap the emitted flag for the naive rule and the streams
    disagree — on exactly the payout-request day."""
    res = run_scenario("topstep_payout_no_halt")
    emitted = [(e.day, e.qualifying_day) for e in res.events
               if e.phase in QUALIFYING_PHASES]
    naive = [(e.day, e.day_net_usd >= XFA_QUALIFYING_DAY_MIN_NET_USD)
             for e in res.events if e.phase in QUALIFYING_PHASES]
    disagree = [a[0] for a, b in zip(emitted, naive) if a[1] != b[1]]
    payout_days = [e.day for e in res.events if e.payout_gross > 0.0]
    assert payout_days == ["d0008"]
    assert disagree == payout_days            # mutation to naive => red


# ==========================================================================
# 3. GENERATION BOUNDARIES (D5-2)
# ==========================================================================

def test_lucid_evaluation_to_funded_is_a_generation_boundary():
    acct = LucidLifecycle(fee_usd=98.0)
    e1 = acct.step_day(unit_path(1500.0), 1)
    e2 = acct.step_day(unit_path(1500.0), 1)          # passes
    assert e1.account_generation == 0 and e2.account_generation == 1
    # the balance was REPLACED (53000 -> 50000) while the day earned +1500
    assert e1.balance == pytest.approx(51500.0)
    assert e2.balance == pytest.approx(50000.0)
    assert e2.balance - e1.balance == pytest.approx(-1500.0)   # phantom
    assert e2.day_net_usd == pytest.approx(1500.0)             # authoritative


def test_combine_reset_and_xfa_construction_bump_the_generation():
    sub = SubscriptionEngine(anchor_day=0)
    c = CombineLifecycle(subscription=sub, generation=3)
    assert c.process_day(0).account_generation == 3
    c.reset(1)
    assert c.process_day(2).account_generation == 4
    assert XfaLifecycle(generation=9).process_day(0).account_generation == 9


def test_full_generation_sequence_lucid_restart_after_death():
    # d0000 dies in evaluation -> restart (gen 1). Every later event is gen 1.
    res = run_scenario("lucid_exhaustion")
    gens = [e.account_generation for e in res.events]
    # 6 attempts (frozen: MAX_EVALUATION_STARTS) -> generations 0..5, one
    # event each (every account dies on its first day).
    assert res.attempts_used == orch.MAX_EVALUATION_STARTS
    assert gens == [0, 1, 2, 3, 4, 5]


def test_full_generation_sequence_topstep_combine_xfa_b2f_newcombine():
    # Hand-derived boundary walk for `topstep_b2f_twice`:
    #   gen 0  initial Combine (d0000..d0002, passes on d0002)
    #   gen 1  XFA after the pass            (dies d0003)
    #   gen 2  B2F #1 fresh XFA              (dies d0004)
    #   gen 3  B2F #2 fresh XFA              (dies d0005)
    #   gen 4  new Combine (B2F exhausted)   (rest of the horizon)
    res = run_scenario("topstep_b2f_twice")
    assert res.b2f_used_total == 2 and res.attempts_used == 2
    seq = [(e.day, e.account_generation) for e in res.events[:8]]
    assert seq == [("d0000", 0), ("d0001", 0), ("d0002", 0),
                   ("d0003", 1), ("d0004", 2), ("d0005", 3),
                   ("d0006", 4), ("d0007", 4)]
    assert max(e.account_generation for e in res.events) == 4


def test_generation_is_monotone_and_moves_by_at_most_one():
    for name in BATTERY:
        res = run_scenario(name)
        gens = [e.account_generation for e in res.events]
        assert all(g is not None for g in gens), name
        assert all(0 <= b - a <= 1 for a, b in zip(gens, gens[1:])), name


# ==========================================================================
# 4. NO-OMISSION PROOF for the generation-boundary inventory
# ==========================================================================

def _identity_residual(prev, ev):
    """`day_net - (balance delta + payout_gross)` — the D5-4 cross-check,
    computed here independently of the production helper."""
    return ev.day_net_usd - ((ev.balance - prev.balance) + ev.payout_gross)


def test_every_unexplained_balance_jump_is_marked_by_a_generation_change():
    """THE no-omission argument: a MISSED reset boundary is precisely a
    balance jump the day's net cannot explain. If any such jump carried an
    unchanged generation, a consumer differencing balances inside one
    generation would silently absorb a reset."""
    for name in BATTERY:
        res = run_scenario(name)
        for prev, ev in zip(res.events, res.events[1:]):
            if abs(_identity_residual(prev, ev)) > 1e-6:
                assert ev.account_generation != prev.account_generation, (
                    f"{name}: unexplained jump at {ev.day} with generation "
                    f"unchanged ({ev.account_generation})")


def test_no_spurious_generation_bumps_in_the_battery():
    """The converse direction, scenario-specific: in this battery every
    generation change really is a balance reset, so a bump that marked
    nothing would fail here."""
    for name in BATTERY:
        res = run_scenario(name)
        for prev, ev in zip(res.events, res.events[1:]):
            if ev.account_generation != prev.account_generation:
                assert abs(_identity_residual(prev, ev)) > 1e-6, (
                    f"{name}: generation moved at {ev.day} without a reset")


def test_balance_reset_site_inventory_is_pinned():
    """PROBE / structural: the reset-boundary inventory is finite and every
    member is classified. A NEW `self.balance = <start constant>` site (i.e.
    a new reset path) makes this red until it is classified and given a
    generation bump."""
    reset_sites = {}
    for rel in ("src/itsf/mc/platforms/lucid.py",
                "src/itsf/mc/platforms/topstep.py"):
        src = (REPO / rel).read_text(encoding="utf-8")
        rhs = re.findall(r"self\.balance\s*=\s*([A-Za-z_][A-Za-z_0-9]*)", src)
        reset_sites[rel] = sorted(rhs)
    assert reset_sites == {
        # ctor (lifecycle start / caller-driven restart) + _enter_funded
        "src/itsf/mc/platforms/lucid.py":
            ["START_BALANCE_USD", "START_BALANCE_USD", "breach_settlement"],
        # Combine _fresh_state (ctor + reset) + XFA ctor
        "src/itsf/mc/platforms/topstep.py":
            ["COMBINE_START_BALANCE_USD", "XFA_START_BALANCE_USD",
             "breach_settlement", "breach_settlement"],
    }


def test_probe_missing_generation_bump_is_caught(monkeypatch):
    """PROBE (mutation): drop ONE boundary marker — the Lucid
    evaluation->funded bump — and the fact layer must go red."""

    class _MissedBoundary(LucidLifecycle):
        def _enter_funded(self):
            keep = self.generation
            super()._enter_funded()
            self.generation = keep            # injected defect

    monkeypatch.setattr(orch, "LucidLifecycle", _MissedBoundary)
    res = run_scenario("lucid_eval_pass")
    codes = {v.code for v in auth.check_event_facts(res.events)}
    assert auth.AUTH_DAY_NET_INVARIANT in codes
    with pytest.raises(auth.AuthoritativeStreamError):
        auth.check_event_facts(res.events, strict=True)


def test_probe_day_net_replaced_by_balance_delta_is_caught():
    """PROBE (mutation): substitute the OLD balance-difference reading for
    the authoritative net and the cross-check must reject it."""
    res = run_scenario("lucid_payout_halt")
    assert auth.check_event_facts(res.events, strict=True) == []
    doctored = [e for e in res.events]
    for prev, ev in zip(res.events, res.events[1:]):
        ev.day_net_usd = ev.balance - prev.balance      # the old defect
    codes = {v.code for v in auth.check_event_facts(doctored)}
    assert auth.AUTH_DAY_NET_INVARIANT in codes


# ==========================================================================
# 5. BASELINE COUNTEREXAMPLES — the old derivations really are wrong
# ==========================================================================

def _legacy_counts(events):
    """The pre-N02 consumer derivation, reproduced verbatim as a
    COUNTEREXAMPLE (balance delta vs the frozen $150 floor). Never used as
    an oracle — it is the thing being falsified."""
    winning = ge150 = 0
    prev = None
    for ev in events:
        if prev is not None:
            delta = ev.balance - prev
            if delta > 0.0:
                winning += 1
            if delta >= 150.0:
                ge150 += 1
        prev = ev.balance
    return winning, ge150


def _authoritative_counts(events):
    winning = sum(1 for e in events[1:] if e.day_net_usd > 0.0)
    ge150 = sum(1 for e in events[1:] if e.day_net_usd >= 150.0)
    return winning, ge150


def test_baseline_counterexample_lucid_generation_boundary_hides_a_winning_day():
    # Hand walk of `lucid_payout_halt` (events d0001..d0013, matching the
    # legacy window that skips the first event):
    #   d0001 +1500 (evaluation pass; balance 51500 -> 50000)
    #   d0002..d0006 +1500 each (funded)
    #   d0007 payout request/halt: net 0, balance -2000
    #   d0008/d0009 processing halt: net 0
    #   d0010 +200 ; d0011..d0013 no path: net 0
    # => authoritative winning days = 1 + 5 + 1 = 7
    #    legacy loses d0001 (a +1500 day read as -1500) => 6
    res = run_scenario("lucid_payout_halt")
    assert _authoritative_counts(res.events) == (7, 7)
    assert _legacy_counts(res.events) == (6, 6)


def test_baseline_counterexample_topstep_payout_and_reset_hide_two_days():
    # Hand walk of `topstep_payout_no_halt` (events d0001..d0011):
    #   d0001,d0002 +1000 (combine)          -> legacy OK
    #   d0003 +200  (first XFA day, balance 53000 -> 200)   -> legacy phantom
    #   d0004..d0007 +200 each               -> legacy OK
    #   d0008 +200 payout day (balance 1000 -> 600)         -> legacy phantom
    #   d0009 +300 ; d0010,d0011 no path
    # => authoritative winning = 2 + 1 + 4 + 1 + 1 = 9 ; legacy = 7
    res = run_scenario("topstep_payout_no_halt")
    assert _authoritative_counts(res.events) == (9, 9)
    assert _legacy_counts(res.events) == (7, 7)


# ==========================================================================
# 6. requested_n / traded_n / cap_applied
# ==========================================================================

def test_cap_clamp_day_is_visible_at_unit_level():
    # frozen: evaluation.max_position micros 40 -> a 100-micro request is cut
    acct = LucidLifecycle(fee_usd=98.0)
    ev = acct.step_day(unit_path(10.0), 100)
    assert (ev.requested_n, ev.traded_n, ev.cap_applied) == (100, 40, True)
    assert ev.day_net_usd == pytest.approx(400.0)      # 40 x $10


def test_cap_clamp_through_the_orchestrator_uses_the_pre_clamp_request():
    # P2 budget $100 / anchor $1 -> the strategy asks for 100 micros; Lucid
    # evaluation caps at 40 (frozen), Topstep Combine at 50 (frozen).
    lucid = run_scenario("lucid_cap_clamp")
    ev = by_day(lucid, "d0000")
    assert (ev.requested_n, ev.traded_n, ev.cap_applied) == (100, 40, True)
    assert ev.day_net_usd == pytest.approx(400.0)
    ts = run_scenario("topstep_cap_clamp")
    ev2 = by_day(ts, "d0000")
    assert (ev2.requested_n, ev2.traded_n, ev2.cap_applied) == (
        100, COMBINE_MAX_MICROS, True)
    assert ev2.day_net_usd == pytest.approx(500.0)


def test_xfa_scaling_tier_clamp_is_reported():
    # frozen: xfa.scaling_tiers balance 0 -> 20 micros next session
    x = XfaLifecycle()
    ev = x.process_day(0, make_trade_path([80.0], final=80.0), n_micros=50)
    assert (ev.requested_n, ev.traded_n, ev.cap_applied) == (50, 20, True)
    assert ev.day_net_usd == pytest.approx(1600.0)     # 20 x $80


def test_skip_n0_day_reports_zero_request_not_a_cap_hit():
    # anchor $150 > P2 budget $100 -> floor(100/150) = 0 micros -> skip
    res = run_scenario("lucid_skip_n0")
    ev = by_day(res, "d0000")
    assert (ev.requested_n, ev.traded_n, ev.cap_applied) == (0, 0, False)
    assert ev.day_net_usd == 0.0
    assert res.skips_n0 == 4


def test_halt_and_dead_days_do_not_claim_a_cap_hit():
    res = run_scenario("lucid_payout_halt")
    halted = [e for e in res.events
              if "payout_request_halt" in e.notes or "processing_halt" in e.notes]
    assert [e.day for e in halted] == ["d0007", "d0008", "d0009"]
    for e in halted:
        assert e.cap_applied is False and e.traded_n == 0
        assert e.day_net_usd == 0.0
        assert e.account_generation == by_day(res, "d0006").account_generation


def test_uncapped_request_helper_never_changes_the_traded_size():
    # `_n_for_day` returns (pre-cap request, real size); only the second may
    # move a trade. Pre-cap >= real, and real is the capped value.
    for balance, floor, anchor, cap in ((50000.0, 48000.0, 100.0, 40),
                                        (50000.0, 48000.0, 1.0, 40),
                                        (0.0, -2000.0, 100.0, 20),
                                        (0.0, -2000.0, 25.0, 20)):
        req, n = orch._n_for_day("P2", balance, floor, anchor, cap)
        assert req >= n and n <= cap


# ==========================================================================
# 7. over_budget — typed unruled state (D5-3)
# ==========================================================================

def test_over_budget_is_never_a_boolean_while_unruled():
    assert OVER_BUDGET_PREDICATE_RULED is False
    for name in BATTERY:
        res = run_scenario(name)
        assert all(e.over_budget is None for e in res.events), name
        assert all(isinstance(e.over_budget_status, OverBudgetStatus)
                   for e in res.events), name


def test_over_budget_status_distinguishes_the_two_kinds_of_none():
    e1 = run_scenario("lucid_payout_halt")
    e2 = run_scenario("lucid_e2_engine")
    traded_e1 = [e for e in e1.events if e.traded_n > 0]
    traded_e2 = [e for e in e2.events if e.traded_n > 0]
    assert traded_e1 and traded_e2
    assert all(e.over_budget_status is OverBudgetStatus.NOT_APPLICABLE
               for e in traded_e1)            # E1: frozen MC SS3 is E2-scoped
    assert all(e.over_budget_status is OverBudgetStatus.PENDING_RULING
               for e in traded_e2)            # E2: mandated, undefined
    idle = [e for e in e2.events if e.traded_n == 0]
    assert all(e.over_budget_status is OverBudgetStatus.NOT_APPLICABLE_NO_TRADE
               for e in idle)


def test_over_budget_status_helper_mapping_and_unknown_engine():
    p1 = day_path("d", 10.0, engine="E1")
    p2 = day_path("d", 10.0, engine="E2")
    assert auth.over_budget_status_for(p1, 3) is OverBudgetStatus.NOT_APPLICABLE
    assert auth.over_budget_status_for(p2, 3) is OverBudgetStatus.PENDING_RULING
    assert (auth.over_budget_status_for(p2, 0)
            is OverBudgetStatus.NOT_APPLICABLE_NO_TRADE)
    assert (auth.over_budget_status_for(None, 5)
            is OverBudgetStatus.NOT_APPLICABLE_NO_TRADE)
    bad = day_path("d", 10.0)
    bad.engine = "E9"
    with pytest.raises(ValueError):
        auth.over_budget_status_for(bad, 1)


def test_a_fabricated_over_budget_boolean_is_refused_at_construction():
    with pytest.raises(AuthoritativeFactError) as ei:
        AccountEvent(day="d", phase="xfa", balance=0.0, floor=0.0,
                     over_budget=False)       # the exact "False == measured" trap
    assert ei.value.code == FACT_OVER_BUDGET_UNRULED
    with pytest.raises(AuthoritativeFactError):
        AccountEvent(day="d", phase="xfa", balance=0.0, floor=0.0,
                     over_budget=True)


# ==========================================================================
# 8. NEGATIVES — one per rejection code
# ==========================================================================

def _ev(**kw):
    base = dict(day="d", phase="xfa", balance=0.0, floor=0.0)
    base.update(kw)
    return AccountEvent(**base)


@pytest.mark.parametrize("kwargs,code", [
    (dict(requested_n=-1), FACT_NEGATIVE_CONTRACTS),
    (dict(traded_n=-1), FACT_NEGATIVE_CONTRACTS),
    (dict(requested_n=1, traded_n=2), FACT_TRADED_EXCEEDS_REQUESTED),
    (dict(requested_n=2, traded_n=2, cap_applied=True),
     FACT_CAP_FLAG_INCONSISTENT),
    (dict(phase="combine", qualifying_day=True), FACT_QUALIFYING_PHASE_MISMATCH),
    (dict(phase="combine", qualifying_day=False), FACT_QUALIFYING_PHASE_MISMATCH),
    (dict(phase="dead", qualifying_day=False), FACT_QUALIFYING_PHASE_MISMATCH),
    (dict(day_net_usd=float("nan")), FACT_DAY_NET_NOT_FINITE),
    (dict(day_net_usd=float("inf")), FACT_DAY_NET_NOT_FINITE),
    (dict(account_generation=-1), FACT_NEGATIVE_GENERATION),
    (dict(over_budget=True), FACT_OVER_BUDGET_UNRULED),
    (dict(over_budget_status="PENDING_RULING"), FACT_OVER_BUDGET_STATUS_TYPE),
])
def test_structural_rejections_at_construction(kwargs, code):
    with pytest.raises(AuthoritativeFactError) as ei:
        _ev(**kwargs)
    assert ei.value.code == code
    assert code in DAY_FACT_REJECTION_CODES


def test_stream_checker_rejects_missing_facts():
    legacy = AccountEvent(day="d", phase="xfa", balance=0.0, floor=0.0)
    codes = {v.code for v in auth.check_event_facts([legacy])}
    assert codes == {auth.AUTH_FACTS_MISSING}
    assert auth.check_event_facts([legacy], require_facts=False) == []


def test_stream_checker_rejects_generation_regression_and_jumps():
    a = _ev(day="a", day_net_usd=0.0, account_generation=5)
    b = _ev(day="b", day_net_usd=0.0, account_generation=4)
    c = _ev(day="c", day_net_usd=0.0, account_generation=9)
    assert auth.AUTH_GENERATION_NOT_MONOTONE in {
        v.code for v in auth.check_event_facts([a, b])}
    assert auth.AUTH_GENERATION_JUMP in {
        v.code for v in auth.check_event_facts([a, c])}


def test_stream_checker_rejects_missing_generation_and_bad_states():
    miss = _ev(day_net_usd=0.0, account_generation=None,
               over_budget_status=OverBudgetStatus.NOT_APPLICABLE_NO_TRADE)
    codes = {v.code for v in auth.check_event_facts([miss])}
    assert codes == {auth.AUTH_GENERATION_MISSING}

    no_status = _ev(day_net_usd=0.0, account_generation=0)
    assert auth.AUTH_OVER_BUDGET_STATE in {
        v.code for v in auth.check_event_facts([no_status])}

    ok = _ev(day_net_usd=0.0, account_generation=0,
             over_budget_status=OverBudgetStatus.NOT_APPLICABLE_NO_TRADE)
    assert auth.check_event_facts([ok]) == []
    ok.over_budget = True                     # post-construction bypass
    assert auth.AUTH_OVER_BUDGET_STATE in {
        v.code for v in auth.check_event_facts([ok])}


def test_stream_checker_rejects_tristate_and_cap_flag_violations():
    ev = _ev(day_net_usd=0.0, account_generation=0,
             over_budget_status=OverBudgetStatus.NOT_APPLICABLE_NO_TRADE)
    ev.phase = "combine"
    ev.qualifying_day = False                 # post-construction bypass
    assert auth.AUTH_QUALIFYING_TRISTATE in {
        v.code for v in auth.check_event_facts([ev])}
    ev2 = _ev(day_net_usd=0.0, account_generation=0,
              over_budget_status=OverBudgetStatus.NOT_APPLICABLE_NO_TRADE)
    ev2.cap_applied = True                    # traded_n == requested_n == 0
    assert auth.AUTH_CAP_FLAG in {
        v.code for v in auth.check_event_facts([ev2])}


def test_all_stream_rejection_codes_are_registered_and_strict_raises():
    assert auth.AUTH_REJECTION_CODES == {
        auth.AUTH_FACTS_MISSING, auth.AUTH_GENERATION_MISSING,
        auth.AUTH_GENERATION_NOT_MONOTONE, auth.AUTH_GENERATION_JUMP,
        auth.AUTH_DAY_NET_INVARIANT, auth.AUTH_QUALIFYING_TRISTATE,
        auth.AUTH_OVER_BUDGET_STATE, auth.AUTH_CAP_FLAG,
    }
    with pytest.raises(auth.AuthoritativeStreamError) as ei:
        auth.check_event_facts(
            [AccountEvent(day="x", phase="xfa", balance=0.0, floor=0.0)],
            strict=True)
    assert ei.value.violations[0].code == auth.AUTH_FACTS_MISSING


def test_orchestrator_refuses_an_event_without_the_fact_layer(monkeypatch):
    class _Amnesiac(LucidLifecycle):
        def step_day(self, path, micros, *, requested_n=None):
            ev = super().step_day(path, micros, requested_n=requested_n)
            ev.day_net_usd = None             # a new emission site forgets
            return ev

    monkeypatch.setattr(orch, "LucidLifecycle", _Amnesiac)
    with pytest.raises(AssertionError, match="authoritative day-facts"):
        run_scenario("lucid_simple")


def test_cross_check_helper_declines_across_generations():
    a = _ev(day="a", balance=100.0, day_net_usd=0.0, account_generation=0,
            over_budget_status=OverBudgetStatus.NOT_APPLICABLE_NO_TRADE)
    b = _ev(day="b", balance=999.0, day_net_usd=0.0, account_generation=1,
            over_budget_status=OverBudgetStatus.NOT_APPLICABLE_NO_TRADE)
    assert auth.day_net_cross_check(a, b) is None        # boundary: N/A
    c = _ev(day="c", balance=150.0, day_net_usd=50.0, account_generation=0,
            over_budget_status=OverBudgetStatus.NOT_APPLICABLE_NO_TRADE)
    assert auth.day_net_cross_check(a, c) == pytest.approx(0.0)


# ==========================================================================
# 9. SWEEP + EV LEDGER INVARIANCE (D5-4)
# ==========================================================================

def test_whole_battery_passes_the_fact_verifier():
    for name in BATTERY:
        res = run_scenario(name)
        assert res.events, name
        assert auth.check_event_facts(res.events, strict=True) == []


def test_ev_chain_values_are_pinned_and_unchanged():
    """Frozen MC SS4.4 accounting must not drift under this node. Values are
    derived by hand from the frozen fee/split/rail parameters."""
    r = run_scenario("lucid_payout_halt").ledger_report
    # gross 2000 (cap) x 0.90 split - $30 Lucid rail = 1770
    assert r["payout_cash_total"] == pytest.approx(1770.0)
    assert r["terminal_cash"] == pytest.approx(0.0)
    assert r["fees"] == {"lucid_purchase": 98.0, "lucid_event_fees": 0.0}
    assert r["prop_operating_ev_total"] == pytest.approx(1770.0 - 98.0)
    assert r["prop_operating_ev_monthly"] == pytest.approx(1672.0 / 24.0)
    assert r["net_business_ev_after_rd_total"] == pytest.approx(1672.0)
    assert r["risk_haircut_ev_total"]["50"] == pytest.approx(
        0.50 * 1770.0 - 98.0)
    assert r["strategy_account_ev_total"] == pytest.approx(7700.0)

    t = run_scenario("topstep_payout_no_halt").ledger_report
    # gross 600 x 0.90 - $0 Wise rail = 540 ; fees: API 29 + sub 49 + act 149
    assert t["payout_cash_total"] == pytest.approx(540.0)
    assert t["fees"] == {"topstep_api": 29.0,
                         "topstep_subscription_activation": 198.0}
    assert t["prop_operating_ev_total"] == pytest.approx(540.0 - 227.0)
    assert t["strategy_account_ev_total"] == pytest.approx(4500.0)


def test_authoritative_layer1_equals_legacy_except_at_lucid_evaluation_passes():
    """The legacy layer-1 accumulator is retained byte-identical; the
    authoritative sum sits beside it. Their difference is EXACTLY the
    evaluation profit discarded at each Lucid pass — derived here from the
    `eval_balance=` disclosure the platform already writes into notes, not
    from any production reducer."""
    for name in BATTERY:
        res = run_scenario(name)
        legacy = res.ledger_report["strategy_account_ev_total"]
        authoritative = res.strategy_account_pnl_authoritative
        discarded = sum(
            float(m.group(1)) - START_BALANCE_USD
            for e in res.events
            for m in [re.search(r"eval_balance=([0-9.]+)", e.notes)] if m)
        assert authoritative == pytest.approx(legacy + discarded), name
        if BATTERY[name][0] == "topstep":
            assert discarded == 0.0 and authoritative == pytest.approx(legacy)

    # the concrete, hand-checked instance: two +1500 days booked as ZERO by
    # the balance-difference proxy, +3000 by the authoritative sum.
    res = run_scenario("lucid_eval_pass")
    assert res.ledger_report["strategy_account_ev_total"] == pytest.approx(0.0)
    assert res.strategy_account_pnl_authoritative == pytest.approx(3000.0)


def test_authoritative_layer1_is_the_sum_of_emitted_day_nets():
    for name in BATTERY:
        res = run_scenario(name)
        assert res.strategy_account_pnl_authoritative == pytest.approx(
            sum(e.day_net_usd for e in res.events)), name


def test_balance_difference_formula_is_not_presented_as_a_definition():
    """D5-4: the formula may appear only as a bounded cross-check. Every
    source line that still computes it must be flagged as legacy/cross-check
    within its comment block."""
    src = (REPO / "src" / "itsf" / "mc" / "orchestrator.py").read_text("utf-8")
    lines = src.splitlines()
    hits = [i for i, ln in enumerate(lines)
            if "ev.balance - prev_balance" in ln]
    assert hits, "the legacy accumulator lines vanished — re-check D5-4"
    for i in hits:
        window = "\n".join(lines[max(0, i - 6):i])
        assert "LEGACY" in window and "NOT the" in window.replace(
            "not the", "NOT the"), lines[i]


# ==========================================================================
# 10. PUBLIC SEAM + determinism
# ==========================================================================

def test_public_field_names_and_defaults_are_stable():
    """The S1 adapter reads these EXACT names; a rename is a breaking change
    and must fail here first."""
    ev = AccountEvent(day="d", phase="xfa", balance=1.0, floor=0.0)
    assert ev.day_net_usd is None             # migration marker
    assert ev.qualifying_day is None
    assert ev.account_generation is None
    assert (ev.requested_n, ev.traded_n, ev.cap_applied) == (0, 0, False)
    assert ev.over_budget is None and ev.over_budget_status is None
    assert QUALIFYING_PHASES == frozenset({"funded", "xfa"})


def test_platform_apis_accept_requested_n_without_changing_sizing():
    """`requested_n` is fact-only: identical trading outcome with and
    without it."""
    a = LucidLifecycle(fee_usd=0.0).step_day(unit_path(300.0), 2)
    b = LucidLifecycle(fee_usd=0.0).step_day(unit_path(300.0), 2,
                                             requested_n=999)
    assert a.balance == b.balance and a.day_net_usd == b.day_net_usd
    assert a.traded_n == b.traded_n == 2
    assert (a.requested_n, a.cap_applied) == (2, False)
    assert (b.requested_n, b.cap_applied) == (999, True)

    x = XfaLifecycle().process_day(0, make_trade_path([50.0], final=50.0), 3)
    y = XfaLifecycle().process_day(0, make_trade_path([50.0], final=50.0), 3,
                                   requested_n=77)
    assert x.balance == y.balance and x.day_net_usd == y.day_net_usd

    sub = SubscriptionEngine(anchor_day=0)
    c = CombineLifecycle(subscription=sub).process_day(
        0, make_trade_path([50.0], final=50.0), 3)
    sub2 = SubscriptionEngine(anchor_day=0)
    d = CombineLifecycle(subscription=sub2).process_day(
        0, make_trade_path([50.0], final=50.0), 3, requested_n=77)
    assert c.balance == d.balance and c.day_net_usd == d.day_net_usd


def test_facts_are_deterministic_across_repeated_runs():
    for name in ("lucid_payout_halt", "topstep_b2f_twice"):
        a = run_scenario(name)
        b = run_scenario(name)
        key = lambda r: [(e.day, e.day_net_usd, e.qualifying_day,  # noqa: E731
                          e.account_generation, e.requested_n, e.traded_n,
                          e.cap_applied, e.over_budget,
                          e.over_budget_status) for e in r.events]
        assert key(a) == key(b), name
