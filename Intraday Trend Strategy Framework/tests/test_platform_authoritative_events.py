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

import inspect
import re
from pathlib import Path

import pytest
from conftest import make_trade_path

from itsf import contracts as C
from itsf.contracts import (DAY_FACT_REJECTION_CODES,
                            FACT_CAP_FLAG_INCONSISTENT,
                            FACT_DAY_NET_NOT_FINITE,
                            FACT_NEGATIVE_CONTRACTS,
                            FACT_NEGATIVE_GENERATION,
                            FACT_OVER_BUDGET_STATUS_TYPE,
                            FACT_OVER_BUDGET_UNRULED,
                            FACT_OVER_BUDGET_RULED_WITHOUT_VALUES,
                            FACT_OVER_BUDGET_VALUE_UNDER_ABSENCE,
                            FACT_QUALIFYING_MISSING,
                            FACT_QUALIFYING_NOT_BOOL,
                            FACT_QUALIFYING_PHASE_MISMATCH,
                            FACT_TRADED_EXCEEDS_REQUESTED,
                            OVER_BUDGET_PREDICATE_RULED, QUALIFYING_PHASES,
                            AccountEvent, AuthoritativeFactError,
                            OverBudgetStatus, fact_layer_active)
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
    # `_n_for_day` returns (pre-cap request, real size, risk budget); only
    # the second may move a trade. Pre-cap >= real, and real is the capped
    # value. The budget rides along so the over-budget predicate compares
    # against the SAME number the sizing used -- for P3/P4 it depends on
    # buffer_at_entry, so recomputing it a frame later would silently judge
    # a day against a different budget.
    for balance, floor, anchor, cap in ((50000.0, 48000.0, 100.0, 40),
                                        (50000.0, 48000.0, 1.0, 40),
                                        (0.0, -2000.0, 100.0, 20),
                                        (0.0, -2000.0, 25.0, 20)):
        req, n, budget = orch._n_for_day("P2", balance, floor, anchor, cap)
        assert req >= n and n <= cap
        assert budget == 100.0            # P2 is flat, so this is exact


# ==========================================================================
# 7. over_budget — typed unruled state (D5-3)
# ==========================================================================

def test_a_boolean_appears_exactly_where_the_predicate_applies():
    """WAS `test_over_budget_is_never_a_boolean_while_unruled`, which held
    while MC SS3 mandated the disclosure and defined no predicate. D1
    supplied it on 2026-08-24, so "never a boolean" would now pin the past.

    What survives is the sharper statement: a boolean exists if and only
    if the status says RULED. Everywhere else it is still absent, and the
    typed status still says which kind of absent -- so a reader can never
    confuse "no position was taken" with "measured, did not exceed"."""
    assert OVER_BUDGET_PREDICATE_RULED is True
    for name in BATTERY:
        res = run_scenario(name)
        for e in res.events:
            assert isinstance(e.over_budget_status, OverBudgetStatus), name
            ruled = e.over_budget_status is OverBudgetStatus.RULED
            for value in (e.over_budget, e.intraday_over_budget):
                if ruled:
                    assert isinstance(value, bool), (name, e.day)
                else:
                    assert value is None, (name, e.day, e.over_budget_status)


def test_over_budget_status_distinguishes_the_two_kinds_of_none():
    e1 = run_scenario("lucid_payout_halt")
    e2 = run_scenario("lucid_e2_engine")
    traded_e1 = [e for e in e1.events if e.traded_n > 0]
    traded_e2 = [e for e in e2.events if e.traded_n > 0]
    assert traded_e1 and traded_e2
    assert all(e.over_budget_status is OverBudgetStatus.NOT_APPLICABLE
               for e in traded_e1)            # E1: frozen MC SS3 is E2-scoped
    assert all(e.over_budget_status is OverBudgetStatus.RULED
               for e in traded_e2)            # E2: mandated, and D1 ruled it
    # ...and RULED means the values are there, which is the whole
    # difference between this token and the three absences
    assert all(isinstance(e.over_budget, bool)
               and isinstance(e.intraday_over_budget, bool)
               for e in traded_e2)
    idle = [e for e in e2.events if e.traded_n == 0]
    assert all(e.over_budget_status is OverBudgetStatus.NOT_APPLICABLE_NO_TRADE
               for e in idle)


def test_over_budget_status_helper_mapping_and_unknown_engine():
    p1 = day_path("d", 10.0, engine="E1")
    p2 = day_path("d", 10.0, engine="E2")
    assert auth.over_budget_status_for(p1, 3) is OverBudgetStatus.NOT_APPLICABLE
    assert auth.over_budget_status_for(p2, 3) is OverBudgetStatus.RULED
    assert (auth.over_budget_status_for(p2, 0)
            is OverBudgetStatus.NOT_APPLICABLE_NO_TRADE)
    assert (auth.over_budget_status_for(None, 5)
            is OverBudgetStatus.NOT_APPLICABLE_NO_TRADE)
    bad = day_path("d", 10.0)
    bad.engine = "E9"
    with pytest.raises(ValueError):
        auth.over_budget_status_for(bad, 1)


@pytest.mark.parametrize("value", [False, True])
def test_a_fabricated_over_budget_boolean_is_refused_at_construction(value):
    """The "False == measured" trap, restated for the ruled world.

    Unruled, ANY boolean was fabricated. Ruled, a boolean is fabricated
    when it arrives with NO status -- an untyped value is exactly the
    reading the typed state exists to prevent, and False is the dangerous
    polarity because it reads as "measured, did not exceed"."""
    with pytest.raises(AuthoritativeFactError) as ei:
        AccountEvent(day="d", phase="xfa", balance=0.0, floor=0.0,
                     over_budget=value)
    assert ei.value.code == FACT_OVER_BUDGET_RULED_WITHOUT_VALUES

    # and under an absence label, which is the post-D1 shape of the same trap
    with pytest.raises(AuthoritativeFactError) as ei:
        AccountEvent(
            day="d", phase="xfa", balance=0.0, floor=0.0,
            over_budget=value, intraday_over_budget=value,
            over_budget_status=OverBudgetStatus.NOT_APPLICABLE_NO_TRADE)
    assert ei.value.code == FACT_OVER_BUDGET_VALUE_UNDER_ABSENCE


# ==========================================================================
# 8. NEGATIVES — one per rejection code
# ==========================================================================

def _ev(**kw):
    """A MIGRATION-STATE event by default (no day_net_usd) — the legacy
    shape the fact-layer rules deliberately do not reach."""
    base = dict(day="d", phase="xfa", balance=0.0, floor=0.0)
    base.update(kw)
    return AccountEvent(**base)


def _fact_ev(**kw):
    """A minimal event with a LIVE production fact layer.

    `qualifying_day=False` is not decoration: phase 'xfa' has a qualifying
    ruleset, so under the C2 biconditional a live fact layer there MUST
    carry a bool. Constructing this without it is itself a refusal, which
    `test_c2_reverse_direction_*` pins."""
    base = dict(day="d", phase="xfa", balance=0.0, floor=0.0,
                day_net_usd=0.0, account_generation=0, qualifying_day=False,
                over_budget_status=OverBudgetStatus.NOT_APPLICABLE_NO_TRADE)
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
    # Ruled since D1, so an untyped boolean is no longer refused for
    # lacking a ruling -- it is refused for lacking a STATUS, which is
    # the statement that says which kind of absence a None would be.
    (dict(over_budget=True), FACT_OVER_BUDGET_RULED_WITHOUT_VALUES),
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
    a = _fact_ev(day="a", account_generation=5)
    b = _fact_ev(day="b", account_generation=4)
    c = _fact_ev(day="c", account_generation=9)
    assert auth.AUTH_GENERATION_NOT_MONOTONE in {
        v.code for v in auth.check_event_facts([a, b])}
    assert auth.AUTH_GENERATION_JUMP in {
        v.code for v in auth.check_event_facts([a, c])}


def test_stream_checker_rejects_missing_generation_and_bad_states():
    miss = _ev(day_net_usd=0.0, account_generation=None,
               over_budget_status=OverBudgetStatus.NOT_APPLICABLE_NO_TRADE)
    codes = {v.code for v in auth.check_event_facts([miss])}
    assert codes == {auth.AUTH_GENERATION_MISSING}

    no_status = _ev(day_net_usd=0.0, account_generation=0,
                    qualifying_day=False)
    assert auth.AUTH_OVER_BUDGET_STATUS_MISSING in {
        v.code for v in auth.check_event_facts([no_status])}

    ok = _fact_ev()
    assert auth.check_event_facts([ok]) == []
    # post-construction bypass: the type cannot see this, the checker can.
    # Ruled, the defect is a value under a label that denies it.
    ok.over_budget = True
    assert auth.AUTH_OVER_BUDGET_VALUE_UNDER_ABSENCE in {
        v.code for v in auth.check_event_facts([ok])}


def test_stream_checker_rejects_tristate_and_cap_flag_violations():
    ev = _fact_ev()
    ev.phase = "combine"
    ev.qualifying_day = False                 # post-construction bypass
    assert auth.AUTH_QUALIFYING_TRISTATE in {
        v.code for v in auth.check_event_facts([ev])}
    ev2 = _fact_ev()
    ev2.cap_applied = True                    # traded_n == requested_n == 0
    assert auth.AUTH_CAP_FLAG in {
        v.code for v in auth.check_event_facts([ev2])}


def test_all_stream_rejection_codes_are_registered_and_strict_raises():
    assert auth.AUTH_REJECTION_CODES == {
        auth.AUTH_FACTS_MISSING, auth.AUTH_DAY_NET_NOT_FINITE,
        auth.AUTH_GENERATION_MISSING, auth.AUTH_GENERATION_MALFORMED,
        auth.AUTH_GENERATION_NOT_MONOTONE, auth.AUTH_GENERATION_JUMP,
        auth.AUTH_QUALIFYING_TRISTATE, auth.AUTH_QUALIFYING_MISSING,
        auth.AUTH_QUALIFYING_NOT_BOOL,
        auth.AUTH_CONTRACT_COUNT_MALFORMED,
        auth.AUTH_TRADED_EXCEEDS_REQUESTED, auth.AUTH_CAP_FLAG,
        auth.AUTH_OVER_BUDGET_VALUE_UNRULED,
        auth.AUTH_OVER_BUDGET_VALUE_NOT_BOOL,
        auth.AUTH_OVER_BUDGET_STATUS_MISSING,
        auth.AUTH_OVER_BUDGET_STATUS_TYPE,
        auth.AUTH_OVER_BUDGET_STATUS_MISMATCH,
        auth.AUTH_OVER_BUDGET_VALUE_UNDER_ABSENCE,
        auth.AUTH_OVER_BUDGET_RULED_WITHOUT_VALUES,
        auth.AUTH_DAY_NET_INVARIANT, auth.AUTH_BALANCE_NOT_FINITE,
        auth.AUTH_PHASE_UNKNOWN, auth.AUTH_PHASE_PLATFORM_MISMATCH,
        auth.AUTH_ENGINE_UNKNOWN, auth.AUTH_PLATFORM_UNKNOWN,
    }
    # every code is a distinct, stable string (an accidental alias would
    # make two different defects indistinguishable to lane S1')
    # 22 + the two D1 coherence codes (value under an absence label,
    # RULED standing over missing values) + AUTH_BALANCE_NOT_FINITE, added
    # 2026-08-26 when a NaN balance was found to defeat the day-net identity
    # silently. This pin's job is to make an addition deliberate, and it did:
    # the fix could not land until this number moved by hand.
    assert len(auth.AUTH_REJECTION_CODES) == 25
    with pytest.raises(auth.AuthoritativeStreamError) as ei:
        auth.check_event_facts(
            [AccountEvent(day="x", phase="xfa", balance=0.0, floor=0.0)],
            strict=True)
    assert ei.value.violations[0].code == auth.AUTH_FACTS_MISSING


def test_orchestrator_refuses_an_event_without_the_fact_layer(monkeypatch):
    class _Amnesiac(LucidLifecycle):
        def step_day(self, path, micros, *, requested_n=None,
                     budget=0.0):
            ev = super().step_day(path, micros, requested_n=requested_n,
                                  budget=budget)
            ev.day_net_usd = None             # a new emission site forgets
            return ev

    monkeypatch.setattr(orch, "LucidLifecycle", _Amnesiac)
    with pytest.raises(AssertionError, match="authoritative day-facts"):
        run_scenario("lucid_simple")


def test_cross_check_helper_declines_across_generations():
    a = _fact_ev(day="a", balance=100.0)
    b = _fact_ev(day="b", balance=999.0, account_generation=1)
    assert auth.day_net_cross_check(a, b) is None        # boundary: N/A
    c = _fact_ev(day="c", balance=150.0, day_net_usd=50.0)
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


# ==========================================================================
# 11. C2 — the qualifying_day BICONDITIONAL (N02 boundary repair)
#
# The pre-repair rule was ONE-WAY: only "qualifying_day is not None on a
# non-qualifying phase" was refused. The reverse — a live funded/XFA fact
# layer emitting None — was unenforced at construction, at the orchestrator
# gate and in the stream checker alike, while contracts.py's comment claimed
# the biconditional was "machine-enforced". These tests pin both directions
# and the migration boundary that bounds them.
#
# ORACLE: the rule is restated here from the frozen ruleset inventory (only
# Lucid funded and Topstep XFA define a qualifying day at all), never by
# calling the production validator.
# ==========================================================================

NON_QUALIFYING_PHASES = ("evaluation", "combine", "dead", "done")


@pytest.mark.parametrize("phase", NON_QUALIFYING_PHASES)
@pytest.mark.parametrize("value", [True, False])
def test_c2_forward_direction_bool_on_nonqualifying_phase_is_refused(phase,
                                                                     value):
    """=> direction, UNCONDITIONAL (holds for legacy events too): a phase
    with no qualifying-day ruleset may never carry a bool. False is as bad
    as True — it reads downstream as "measured, did not qualify"."""
    with pytest.raises(AuthoritativeFactError) as ei:
        AccountEvent(day="d", phase=phase, balance=0.0, floor=0.0,
                     qualifying_day=value)
    assert ei.value.code == FACT_QUALIFYING_PHASE_MISMATCH
    # and again with the fact layer live, so the repair cannot have made the
    # unconditional direction accidentally conditional
    with pytest.raises(AuthoritativeFactError) as ei2:
        AccountEvent(day="d", phase=phase, balance=0.0, floor=0.0,
                     qualifying_day=value, day_net_usd=0.0,
                     account_generation=0)
    assert ei2.value.code == FACT_QUALIFYING_PHASE_MISMATCH


@pytest.mark.parametrize("phase", sorted(QUALIFYING_PHASES))
def test_c2_reverse_direction_none_on_qualifying_phase_is_refused(phase):
    """<= direction: THE hole this node closes. funded / xfa with a live
    fact layer must carry a real bool; None claims the ruleset has no
    qualifying-day concept and deletes the day from every count."""
    with pytest.raises(AuthoritativeFactError) as ei:
        AccountEvent(day="d", phase=phase, balance=0.0, floor=0.0,
                     day_net_usd=0.0, account_generation=0,
                     qualifying_day=None)
    assert ei.value.code == FACT_QUALIFYING_MISSING
    assert FACT_QUALIFYING_MISSING in DAY_FACT_REJECTION_CODES
    # both bools are accepted (the rule refuses ABSENCE, not a value)
    for value in (True, False):
        ok = AccountEvent(day="d", phase=phase, balance=0.0, floor=0.0,
                          day_net_usd=0.0, account_generation=0,
                          qualifying_day=value)
        assert ok.qualifying_day is value


@pytest.mark.parametrize("phase", sorted(QUALIFYING_PHASES))
def test_c2_legacy_migration_event_stays_compatible(phase):
    """COMPATIBILITY BOUNDARY: `day_net_usd is None` is the migration
    marker (itsf.mc.account.run_account still emits such events), so the
    reverse direction must NOT reach it. Partial facts do not activate the
    layer either — that shape is a malformed PRODUCTION event and the
    stream verifier names it `account_generation_missing`, a strictly more
    specific diagnosis than "qualifying day missing"."""
    legacy = AccountEvent(day="d", phase=phase, balance=1.0, floor=0.0)
    assert legacy.qualifying_day is None
    assert fact_layer_active(legacy.day_net_usd,
                             legacy.account_generation) is False
    # generation alone does not activate it
    half = AccountEvent(day="d", phase=phase, balance=1.0, floor=0.0,
                        account_generation=0)
    assert half.qualifying_day is None
    # day_net alone does not either
    other_half = AccountEvent(day="d", phase=phase, balance=1.0, floor=0.0,
                              day_net_usd=0.0)
    assert other_half.qualifying_day is None
    assert auth.check_event_facts([legacy], require_facts=False) == []


@pytest.mark.parametrize("value", [1, 0, "True", 1.0])
def test_c2_qualifying_day_must_be_a_real_bool(value):
    """Tri-state means None | True | False. A truthy int satisfies every
    `is not None` guard downstream and is then counted as a qualifying
    day the platform never reported."""
    with pytest.raises(AuthoritativeFactError) as ei:
        AccountEvent(day="d", phase="xfa", balance=0.0, floor=0.0,
                     day_net_usd=0.0, account_generation=0,
                     qualifying_day=value)
    assert ei.value.code == FACT_QUALIFYING_NOT_BOOL


def test_c2_real_producer_bool_flipped_to_none_is_refused_by_verify_event_stream():
    """THE mutable-dataclass argument, executed. A REAL producer stream is
    emitted, then one funded day's qualifying bool is set to None AFTER
    construction — exactly the bypass __post_init__ cannot see. The stream
    verifier must still refuse, because it re-derives the rule from the
    object the consumer will actually read."""
    res = run_scenario("lucid_payout_halt")
    auth.verify_event_stream(res.events, engine="E1", platform="lucid")

    targets = [e for e in res.events if e.phase in QUALIFYING_PHASES]
    assert targets, "scenario emitted no qualifying-phase day"
    assert all(isinstance(e.qualifying_day, bool) for e in targets)
    victim = targets[0]
    victim.qualifying_day = None              # post-construction bypass
    with pytest.raises(AuthoritativeFactError) as ei:
        auth.verify_event_stream(res.events, engine="E1", platform="lucid")
    assert ei.value.code == auth.AUTH_QUALIFYING_MISSING
    assert victim.day in str(ei.value)

    victim.qualifying_day = False             # restored -> accepted again
    assert auth.verify_event_stream(res.events, engine="E1",
                                    platform="lucid") is None


def test_c2_real_producer_bool_moved_to_a_nonqualifying_day_is_refused():
    """The mirror bypass: move a bool onto a day whose ruleset has no
    qualifying concept (here the Topstep Combine)."""
    res = run_scenario("topstep_payout_no_halt")
    auth.verify_event_stream(res.events, engine="E1", platform="topstep")
    victim = [e for e in res.events if e.phase == "combine"][0]
    victim.qualifying_day = False             # post-construction bypass
    with pytest.raises(AuthoritativeFactError) as ei:
        auth.verify_event_stream(res.events, engine="E1", platform="topstep")
    assert ei.value.code == auth.AUTH_QUALIFYING_TRISTATE


def test_c2_every_production_event_satisfies_the_biconditional():
    """Sweep: over the whole battery the emitted tri-state IS the
    biconditional, checked here by an independent restatement rather than
    by calling the verifier."""
    seen_bool = seen_none = 0
    for name in BATTERY:
        res = run_scenario(name)
        for e in res.events:
            live = fact_layer_active(e.day_net_usd, e.account_generation)
            assert live, f"{name}/{e.day}: production event without facts"
            if e.phase in QUALIFYING_PHASES:
                assert isinstance(e.qualifying_day, bool), (name, e.day)
                seen_bool += 1
            else:
                assert e.qualifying_day is None, (name, e.day)
                seen_none += 1
    # both arms are actually exercised (a vacuous sweep proves nothing)
    assert seen_bool > 0 and seen_none > 0


# ==========================================================================
# 12. C4 — `verify_event_stream`, the production-chain fact gate
#
# ORACLE DISCIPLINE: `_valid_stream()` below is hand-built with arithmetic
# done in this file (balance 100 -> 150 on a +50 day, no payout, so the
# identity residual is 50 - ((150 - 100) + 0) = 0). Every negative is that
# stream with ONE field mutated, so the expected code follows from the rule
# text, never from running the production reducer.
# ==========================================================================

def _valid_stream():
    """Two adjacent same-generation XFA days on a Topstep/E2 run.

    day 'a': idle           net 0.0, balance 100.0, traded 0
    day 'b': 1 micro, +50   net 50.0, balance 150.0, traded 1 of 1 requested
    identity on the pair: 50.0 - ((150.0 - 100.0) + 0.0) == 0.0
    """
    a = AccountEvent(day="a", phase="xfa", balance=100.0, floor=0.0,
                     day_net_usd=0.0, account_generation=0,
                     qualifying_day=False, requested_n=0, traded_n=0,
                     cap_applied=False,
                     over_budget_status=OverBudgetStatus.NOT_APPLICABLE_NO_TRADE)
    # D1 (2026-08-24): a traded E2 day now carries the ruled predicate's
    # two booleans. Both False here -- a profitable day exceeded nothing,
    # and under the ruling that IS the measurement rather than an absence.
    b = AccountEvent(day="b", phase="xfa", balance=150.0, floor=0.0,
                     day_net_usd=50.0, account_generation=0,
                     qualifying_day=False, requested_n=1, traded_n=1,
                     cap_applied=False, over_budget=False,
                     intraday_over_budget=False,
                     over_budget_status=OverBudgetStatus.RULED)
    return [a, b]


def _set(field, value):
    def mutate(stream):
        setattr(stream[1], field, value)
    return mutate


def _set_pair(f1, v1, f2, v2):
    """Two fields at once, for a defect that needs the pair to disagree."""
    def mutate(stream):
        setattr(stream[1], f1, v1)
        setattr(stream[1], f2, v2)
    return mutate


def _set_first(field, value):
    def mutate(stream):
        setattr(stream[0], field, value)
    return mutate


# One negative per stable code. Turning OFF the corresponding rule in
# `_iter_violations` makes exactly the matching row red (mutation probe).
STREAM_NEGATIVES = [
    (auth.AUTH_FACTS_MISSING, _set("day_net_usd", None)),
    (auth.AUTH_DAY_NET_NOT_FINITE, _set("day_net_usd", float("nan"))),
    (auth.AUTH_DAY_NET_NOT_FINITE, _set("day_net_usd", float("inf"))),
    (auth.AUTH_GENERATION_MISSING, _set("account_generation", None)),
    (auth.AUTH_GENERATION_MALFORMED, _set("account_generation", -1)),
    (auth.AUTH_GENERATION_MALFORMED, _set("account_generation", 1.0)),
    (auth.AUTH_GENERATION_NOT_MONOTONE, _set_first("account_generation", 3)),
    (auth.AUTH_GENERATION_JUMP, _set("account_generation", 2)),
    (auth.AUTH_QUALIFYING_TRISTATE, _set("phase", "done")),
    (auth.AUTH_QUALIFYING_MISSING, _set("qualifying_day", None)),
    (auth.AUTH_QUALIFYING_NOT_BOOL, _set("qualifying_day", 1)),
    (auth.AUTH_CONTRACT_COUNT_MALFORMED, _set("traded_n", -1)),
    (auth.AUTH_CONTRACT_COUNT_MALFORMED, _set("requested_n", "1")),
    (auth.AUTH_TRADED_EXCEEDS_REQUESTED, _set("traded_n", 2)),
    (auth.AUTH_CAP_FLAG, _set("requested_n", 3)),        # clamp NOT reported
    (auth.AUTH_CAP_FLAG, _set("cap_applied", True)),     # clamp NOT real
    (auth.AUTH_CAP_FLAG, _set("cap_applied", "yes")),
    # These two moved out of this table on 2026-08-24. Their code fires
    # only while OVER_BUDGET_PREDICATE_RULED is False, and this table runs
    # against the live constant -- so they are exercised, under the unruled
    # state, in test_the_unruled_defect_code_is_still_reachable below. The
    # code is NOT dead: the constant is the switch, and a retraction must
    # find the verifier still able to say so.
    (auth.AUTH_OVER_BUDGET_VALUE_UNDER_ABSENCE,
     _set_first("over_budget", True)),
    (auth.AUTH_OVER_BUDGET_RULED_WITHOUT_VALUES,
     _set("over_budget", None)),
    (auth.AUTH_OVER_BUDGET_RULED_WITHOUT_VALUES,
     _set("intraday_over_budget", None)),
    (auth.AUTH_OVER_BUDGET_STATUS_MISSING, _set("over_budget_status", None)),
    (auth.AUTH_OVER_BUDGET_STATUS_TYPE,
     _set("over_budget_status", "PENDING_RULING")),
    (auth.AUTH_OVER_BUDGET_STATUS_MISMATCH,
     _set("over_budget_status", OverBudgetStatus.NOT_APPLICABLE)),
    (auth.AUTH_OVER_BUDGET_STATUS_MISMATCH,
     _set("over_budget_status", OverBudgetStatus.NOT_APPLICABLE_NO_TRADE)),
    (auth.AUTH_DAY_NET_INVARIANT, _set("balance", 999.0)),
    (auth.AUTH_DAY_NET_INVARIANT, _set("payout_gross", 25.0)),
    (auth.AUTH_PHASE_UNKNOWN, _set("phase", "live")),
    (auth.AUTH_PHASE_PLATFORM_MISMATCH, _set("phase", "funded")),
]


def test_verify_event_stream_accepts_the_hand_built_valid_stream():
    """No false positives: the whole rule set is satisfiable, and the gate
    returns None rather than any derived quantity."""
    assert auth.verify_event_stream(_valid_stream(), engine="E2",
                                    platform="topstep") is None
    assert auth.check_event_facts(_valid_stream(), engine="E2",
                                  platform="topstep") == []


@pytest.mark.parametrize("code,mutate", STREAM_NEGATIVES,
                         ids=[f"{c}-{i}" for i, (c, _m)
                              in enumerate(STREAM_NEGATIVES)])
def test_verify_event_stream_refuses_one_defect_per_stable_code(code, mutate):
    stream = _valid_stream()
    mutate(stream)
    with pytest.raises(AuthoritativeFactError) as ei:
        auth.verify_event_stream(stream, engine="E2", platform="topstep")
    assert ei.value.code == code
    assert code in auth.AUTH_REJECTION_CODES


def test_verify_event_stream_refuses_unknown_engine_and_platform_labels():
    """The labels are part of the fact, not decoration: a typo would make
    the engine-scoped over-budget rule silently inapplicable."""
    with pytest.raises(AuthoritativeFactError) as ei:
        auth.verify_event_stream(_valid_stream(), engine="E3",
                                 platform="topstep")
    assert ei.value.code == auth.AUTH_ENGINE_UNKNOWN
    with pytest.raises(AuthoritativeFactError) as ei2:
        auth.verify_event_stream(_valid_stream(), engine="E2",
                                 platform="apex")
    assert ei2.value.code == auth.AUTH_PLATFORM_UNKNOWN
    assert auth.ENGINES == ("E1", "E2")
    assert auth.PLATFORMS == ("lucid", "topstep")


def test_verify_event_stream_refuses_a_non_bool_over_budget_once_ruled(
        monkeypatch):
    """FORWARD GUARD ONLY — this test does NOT rule the E2 over-budget
    predicate and defines nothing (that is Aaron's call, master plan
    N-D2). It exercises the type guard that becomes load-bearing the day
    the flag flips, so the flip cannot land an untyped value."""
    stream = _valid_stream()
    stream[1].over_budget = "yes"
    monkeypatch.setattr(C, "OVER_BUDGET_PREDICATE_RULED", True)
    with pytest.raises(AuthoritativeFactError) as ei:
        auth.verify_event_stream(stream, engine="E2", platform="topstep")
    assert ei.value.code == auth.AUTH_OVER_BUDGET_VALUE_NOT_BOOL
    # and the unruled refusal is what fires while the flag is False
    monkeypatch.setattr(C, "OVER_BUDGET_PREDICATE_RULED", False)
    with pytest.raises(AuthoritativeFactError) as ei2:
        auth.verify_event_stream(stream, engine="E2", platform="topstep")
    assert ei2.value.code == auth.AUTH_OVER_BUDGET_VALUE_UNRULED


@pytest.mark.parametrize("engine,traded,expected", [
    ("E1", 0, OverBudgetStatus.NOT_APPLICABLE_NO_TRADE),
    ("E2", 0, OverBudgetStatus.NOT_APPLICABLE_NO_TRADE),
    ("E1", 3, OverBudgetStatus.NOT_APPLICABLE),
    ("E2", 3, OverBudgetStatus.RULED),
])
def test_over_budget_status_applicability_conditions(engine, traded,
                                                     expected):
    """The three applicability conditions, restated from frozen MC SS3
    (the disclosure is E2-scoped; a day with no position has no budget
    draw to compare) — the verifier's oracle, not a copy of the emission
    helper."""
    assert auth.expected_over_budget_status(engine, traded) is expected


def test_engine_scoped_status_rule_catches_a_swapped_engine():
    """An E2 run whose days report the E1 status would erase the mandated
    disclosure from the whole path atom."""
    stream = _valid_stream()
    # the stream is internally consistent for E2 ...
    assert auth.verify_event_stream(stream, engine="E2",
                                    platform="topstep") is None
    # ... and therefore MUST be refused when replayed as E1
    with pytest.raises(AuthoritativeFactError) as ei:
        auth.verify_event_stream(stream, engine="E1", platform="topstep")
    assert ei.value.code == auth.AUTH_OVER_BUDGET_STATUS_MISMATCH


# --------------------------------------------------------------------------
# 12b. the day-net identity: its applicability conditions, one by one
# --------------------------------------------------------------------------

def test_identity_skip_S1_stream_head_has_no_predecessor():
    """(S1) The first event carries an arbitrary opening balance that no
    event can explain; the pair does not exist yet. Everything INSIDE the
    day is still checked."""
    head = _valid_stream()[:1]
    head[0].balance = 12_345.0                # unexplained by its own net
    assert auth.verify_event_stream(head, engine="E2",
                                    platform="topstep") is None
    assert auth.day_net_identity_applies(None, head[0]) is False


def test_identity_skip_S2_generation_change_and_only_that():
    """(S2) A generation bump marks a balance RESET, so the difference is a
    phantom and the identity must not be applied. The skip is bounded: the
    SAME jump inside one generation is refused."""
    ok = _valid_stream()
    ok[1].balance = 99_999.0
    ok[1].account_generation = 1              # a declared reset boundary
    assert auth.day_net_identity_applies(ok[0], ok[1]) is False
    assert auth.verify_event_stream(ok, engine="E2",
                                    platform="topstep") is None

    bad = _valid_stream()
    bad[1].balance = 99_999.0                 # same jump, no boundary
    assert auth.day_net_identity_applies(bad[0], bad[1]) is True
    with pytest.raises(AuthoritativeFactError) as ei:
        auth.verify_event_stream(bad, engine="E2", platform="topstep")
    assert ei.value.code == auth.AUTH_DAY_NET_INVARIANT


def test_identity_skip_S3_legacy_event_is_unreachable_in_production():
    """(S3) The legacy skip exists only for the mixed-stream inspection
    form. Under `verify_event_stream` a factless event is refused BEFORE a
    pair can be formed, so S3 can never be used to dodge the identity."""
    mixed = _valid_stream()
    mixed[0].day_net_usd = None
    assert auth.day_net_identity_applies(mixed[0], mixed[1]) is False
    with pytest.raises(AuthoritativeFactError) as ei:
        auth.verify_event_stream(mixed, engine="E2", platform="topstep")
    assert ei.value.code == auth.AUTH_FACTS_MISSING
    # the collecting form tolerates it and still checks everything else
    assert auth.check_event_facts(mixed, require_facts=False, engine="E2",
                                  platform="topstep") == []


def test_identity_is_a_hard_refusal_not_a_downgradeable_warning():
    """PROBE: the residual is not exposed as an advisory number anywhere on
    the production path — the only production entry point RAISES."""
    bad = _valid_stream()
    bad[1].day_net_usd = bad[1].balance - bad[0].balance + 1.0   # off by $1
    with pytest.raises(AuthoritativeFactError):
        auth.verify_event_stream(bad, engine="E2", platform="topstep")
    # and the tolerance really is representation-error-sized
    edge = _valid_stream()
    edge[1].day_net_usd = 50.0 + auth.CROSS_CHECK_TOL_USD / 2.0
    assert auth.verify_event_stream(edge, engine="E2",
                                    platform="topstep") is None


def test_balance_mutation_site_inventory_is_pinned():
    """PROBE / structural — the evidence behind "no other skip exists".

    The identity's domain argument enumerates every way a sim balance can
    move: a trading settlement folded into `day_net_usd`, the payout gross
    deduction carried by `payout_gross`, or a reset to a start constant
    (which bumps the generation). A NEW mutation site makes this red until
    it is classified against one of those three."""
    sites = {}
    for rel in ("src/itsf/mc/platforms/lucid.py",
                "src/itsf/mc/platforms/topstep.py"):
        src = (REPO / rel).read_text(encoding="utf-8")
        sites[rel] = sorted(re.findall(
            r"self\.balance\s*(\+=|-=|=)\s*([A-Za-z_][A-Za-z_0-9]*)", src))
    assert sites == {
        "src/itsf/mc/platforms/lucid.py": [
            ("+=", "day_net"),              # trading settlement -> day_net_usd
            ("-=", "gross"),                # payout -> payout_gross
            ("=", "START_BALANCE_USD"),     # ctor reset -> generation bump
            ("=", "START_BALANCE_USD"),     # _enter_funded -> generation bump
            ("=", "breach_settlement"),     # R1 same-day -> day_net_usd
        ],
        "src/itsf/mc/platforms/topstep.py": [
            ("+=", "day_net"),              # XFA trading -> day_net_usd
            ("+=", "day_pnl"),              # Combine trading -> day_net_usd
            ("-=", "payout_gross"),         # payout -> payout_gross
            ("=", "COMBINE_START_BALANCE_USD"),   # reset -> generation bump
            ("=", "XFA_START_BALANCE_USD"),       # reset -> generation bump
            ("=", "breach_settlement"),           # R1 same-day -> day_net_usd
            ("=", "breach_settlement"),
        ],
    }


# --------------------------------------------------------------------------
# 12c. the production sweep + the seam contract lane S1' codes against
# --------------------------------------------------------------------------

ENGINE_OF = {"lucid_e2_engine": "E2"}


def test_verify_event_stream_accepts_the_whole_production_battery():
    """The gate must be satisfiable by every real producer path, or it is
    a denial-of-service on the consumer rather than a guard."""
    for name in BATTERY:
        platform = BATTERY[name][0]
        engine = ENGINE_OF.get(name, "E1")
        res = run_scenario(name)
        assert res.events, name
        assert auth.verify_event_stream(res.events, engine=engine,
                                        platform=platform) is None, name


@pytest.mark.parametrize("platform", ["lucid", "topstep"])
@pytest.mark.parametrize("anchor", [1.0, 25.0, 100.0, 150.0, 10_000.0])
@pytest.mark.parametrize("pnl", [900.0, 150.0, 0.0, -400.0])
def test_cap_biconditional_holds_across_a_sizing_sweep(platform, anchor, pnl):
    """THE risk the `<=` half of rule 4 carries: `cap_applied` is False on a
    day that traded less than it requested for a reason OTHER than the
    position cap (a policy skip), and the biconditional then refuses a
    legitimate run.

    It cannot happen on the production path, and this sweep holds that
    mechanically rather than by reading. `_n_for_day` returns
    (floor(budget/anchor), min(that, cap)), so traded < requested requires
    cap < requested, which requires cap > 0 — and whenever a platform cap
    is 0 the orchestrator's guards make requested_n 0 as well. The anchor
    grid spans cap-bound days (anchor 1), exact-fit days and n == 0 skips
    (anchor 10000)."""
    days = tdays(40)
    paths = {t.day_id: day_path(t.day_id, pnl, anchor=anchor) for t in days}
    res = run_lifecycle(LifecycleConfig(platform=platform), days, paths)
    assert res.events
    assert auth.verify_event_stream(res.events, engine="E1",
                                    platform=platform) is None
    # independent restatement of the same biconditional
    for e in res.events:
        assert e.cap_applied is (e.traded_n < e.requested_n), (
            f"{platform}/{anchor}/{pnl} day {e.day}: cap_applied="
            f"{e.cap_applied} traded_n={e.traded_n} "
            f"requested_n={e.requested_n}")


def test_cap_biconditional_sweep_is_not_vacuous():
    """The sweep above proves nothing unless it actually reaches both arms:
    real cap hits AND real zero-traded days."""
    days = tdays(40)
    clamped = run_lifecycle(
        LifecycleConfig(platform="lucid"), days,
        {t.day_id: day_path(t.day_id, 10.0, anchor=1.0) for t in days})
    assert any(e.cap_applied for e in clamped.events)
    assert any(e.traded_n > 0 for e in clamped.events)
    skipped = run_lifecycle(
        LifecycleConfig(platform="lucid"), days,
        {t.day_id: day_path(t.day_id, 10.0, anchor=10_000.0) for t in days})
    assert any(e.traded_n == 0 for e in skipped.events)
    assert all(not e.cap_applied for e in skipped.events)
    assert skipped.skips_n0 > 0


def test_verify_event_stream_signature_is_the_cross_lane_contract():
    """Lane S1' calls this by keyword in `_run_path_atom`; a signature
    change is a breaking change and must fail here first."""
    sig = inspect.signature(auth.verify_event_stream)
    assert list(sig.parameters) == ["events", "engine", "platform"]
    assert sig.parameters["events"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    for name in ("engine", "platform"):
        p = sig.parameters[name]
        assert p.kind is inspect.Parameter.KEYWORD_ONLY, name
        assert p.default is inspect.Parameter.empty, name
    assert sig.return_annotation == "None"


def test_platform_phase_inventory_is_complete_and_reachable():
    """Every allowed phase belongs to exactly the platform(s) that can emit
    it; a phase in neither set would make the platform check vacuous, and a
    phase in the wrong set would let a wiring error through."""
    assert set(auth.ALLOWED_PHASES) == orch._ALLOWED_PHASES
    union = set().union(*auth.PLATFORM_PHASES.values())
    assert union == set(auth.ALLOWED_PHASES)
    assert set(auth.PLATFORM_PHASES) == set(auth.PLATFORMS)
    observed = {"lucid": set(), "topstep": set()}
    for name in BATTERY:
        res = run_scenario(name)
        observed[BATTERY[name][0]].update(e.phase for e in res.events)
    for platform, phases in observed.items():
        assert phases <= auth.PLATFORM_PHASES[platform], platform
        assert phases, platform


def test_check_event_facts_stays_available_as_the_collecting_form():
    """Backwards compatibility for the whole-list callers; production
    semantics remain `verify_event_stream`'s."""
    stream = _valid_stream()
    stream[1].qualifying_day = None           # one defect
    stream[1].traded_n = 5                    # a second, independent one
    codes = [v.code for v in auth.check_event_facts(stream, engine="E2",
                                                    platform="topstep")]
    assert codes == [auth.AUTH_QUALIFYING_MISSING,
                     auth.AUTH_TRADED_EXCEEDS_REQUESTED]
    # ... while the production gate stops at the FIRST one
    with pytest.raises(AuthoritativeFactError) as ei:
        auth.verify_event_stream(stream, engine="E2", platform="topstep")
    assert ei.value.code == auth.AUTH_QUALIFYING_MISSING


def test_verify_event_stream_is_a_pure_gate():
    """It returns None, always — a verifier that returned a number would
    become a quiet second definition of the facts it checks."""
    assert auth.verify_event_stream([], engine="E1", platform="lucid") is None
    res = run_scenario("lucid_simple")
    assert auth.verify_event_stream(res.events, engine="E1",
                                    platform="lucid") is None
    src = (REPO / "src" / "itsf" / "mc" / "platforms"
           / "authoritative.py").read_text("utf-8")
    body = src.split("def verify_event_stream")[1].split("\ndef ")[0]
    assert "return None" in body
    assert "sum(" not in body and "len(" not in body


def test_the_unruled_defect_code_is_still_reachable(monkeypatch):
    """`over_budget_value_without_ruling` cannot fire while the predicate
    is ruled, which is correct and is exactly why it needs its own test.

    A code that no live state can produce looks identical to a code that
    was quietly dropped. The constant is the switch: a retraction of D1
    must find the verifier still able to refuse a boolean, so the code is
    exercised in the state that produces it rather than deleted from the
    catalogue for being inconvenient today."""
    from itsf import contracts as _c
    streams = [_valid_stream(), _valid_stream()]      # built while ruled
    monkeypatch.setattr(_c, "OVER_BUDGET_PREDICATE_RULED", False)
    for value, stream in zip((True, False), streams):
        stream[1].over_budget_status = OverBudgetStatus.PENDING_RULING
        stream[1].over_budget = value
        stream[1].intraday_over_budget = None
        with pytest.raises(AuthoritativeFactError) as ei:
            auth.verify_event_stream(stream, engine="E2", platform="topstep")
        assert ei.value.code == auth.AUTH_OVER_BUDGET_VALUE_UNRULED
    assert auth.AUTH_OVER_BUDGET_VALUE_UNRULED in auth.AUTH_REJECTION_CODES


# ===========================================================================
# NaN defeats the day-net identity — Fable V2 Medium, 2026-08-20
# ===========================================================================

def test_a_nan_balance_does_not_silently_satisfy_the_day_net_identity():
    """RED PROOF for the Fable V2 Medium finding, reproduced from scratch.

    The identity is `day_net == (balance - prev.balance) + payout_gross`,
    enforced as `abs(residual) > CROSS_CHECK_TOL_USD`. If any input is NaN
    the residual is NaN, and `abs(nan) > tol` is **False** — so the
    comparison reports no violation. Silence, not a failure.

    `day_net_usd` is separately checked for finiteness, so a NaN there is
    caught under its own code. `balance` never was: nothing in this module
    checked it. A NaN balance therefore defeated the identity with no
    day-net violation at all — it behaved EXACTLY like a satisfied
    identity, which is the worst shape a check can have.

    The assertion below is on the SPECIFIC code, deliberately. An earlier
    draft asserted merely that some violation existed and passed against an
    unrelated `engine_label_unknown` — including for a pair whose identity
    was deliberately violated. A proof that cannot tell those apart proves
    nothing.
    """
    import math

    from itsf.mc.platforms import authoritative as auth

    prev = _fact_ev(day="2026-08-03", phase="funded", balance=50000.0,
                    day_net_usd=0.0)
    broken = _fact_ev(day="2026-08-04", phase="funded", balance=99999.0,
                      day_net_usd=100.0)
    nan_balance = _fact_ev(day="2026-08-04", phase="funded",
                           balance=float("nan"), day_net_usd=100.0)

    def codes(pair):
        return {v.code for v in auth.check_event_facts(
            pair, engine="E2", platform="lucid")}

    # the residual really is NaN, and the comparison really is False
    resid = auth.day_net_cross_check(prev, nan_balance)
    assert resid is not None and math.isnan(resid)
    assert not (abs(resid) > auth.CROSS_CHECK_TOL_USD)

    # the control: a plainly violated identity IS reported
    assert auth.AUTH_DAY_NET_INVARIANT in codes([prev, broken]), (
        "the control failed — this test cannot detect the defect it is for")

    # the defect: NaN must not be indistinguishable from a satisfied identity
    assert auth.AUTH_DAY_NET_INVARIANT in codes([prev, nan_balance])         or auth.AUTH_BALANCE_NOT_FINITE in codes([prev, nan_balance]), (
        "a NaN balance produced no day-net violation — it is indis"
        "tinguishable from an identity that holds")


def test_a_non_finite_residual_is_never_read_as_no_violation():
    """Defence in depth, one layer below the root cause.

    Fixing `balance` closes the reachable path. It does not fix the
    comparison, which still reads any NaN residual as "within tolerance".
    Anything that produces a non-finite residual in future — a new field in
    the identity, an inf balance — would be silently absorbed again."""
    import math

    from itsf.mc.platforms import authoritative as auth

    for value in (float("nan"), float("inf"), float("-inf")):
        assert not (abs(value) > auth.CROSS_CHECK_TOL_USD) or math.isinf(
            value), f"{value!r} unexpectedly compared as over tolerance"
    # inf DOES exceed tolerance; nan does not. Only nan is silent.
    assert not (abs(float("nan")) > auth.CROSS_CHECK_TOL_USD)
