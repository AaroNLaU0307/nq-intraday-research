"""Business-layer lifecycle orchestrator (MAIN-AGENT AUTHORED, milestone 2).

Coordinates the canonical platform lifecycles (ruling R5) over a synthetic
template calendar and owns EVERYTHING the platforms must not own:

  - the 24-month, 6-evaluation-starts attempt counter
        # frozen: MC SS4.3 lifecycle_attempt_policy (incl. initial; funded
        # failure restarts consume the same counter; terminate on exhaustion)
  - Back2Funded usage (max 2 per XFA, 30-day window, does NOT consume an
    evaluation start — it is a distinct failure_policy action, not a
    new_evaluation/new_combine)          # frozen: MC SS4.3; platform_params b2f
  - the Lucid payout processing halt window (request day is halted by the
    platform; the following 2 template trading days are halted here —
    Implementation Resolution IR-8)      # frozen: MC SS4.2 lucidflex halt
  - required execution costs: TopstepX API $29 per 30 calendar days
        # frozen: platform_params topstep_50k.api (Primary conservative $29);
        # billed from lifecycle start (IR-9, conservative)
  - the four EV ledgers (SOLE owner; platforms only report fees on events)
        # frozen: MC SS4.4
  - terminal value via platform eligible_terminal_gross()
        # frozen: payout_accounting.terminal_withdrawable_value

It must NEVER: touch trade-level costs (already inside
TradePathRecord.final_pnl_per_contract — double_counting_guard), replicate
platform MLL/scaling/payout-eligibility formulas, or enter a live state.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from itsf.contracts import AccountEvent, TradePathRecord
from itsf.mc import account as acct
from itsf.mc.platforms import lucid as lucid_mod
from itsf.mc.platforms import topstep as ts
from itsf.mc.platforms.lucid import LucidLifecycle
from itsf.mc.platforms.topstep import (CombineLifecycle, SubscriptionEngine,
                                       XfaLifecycle)

# frozen: MC SS4.3 lifecycle_attempt_policy
MAX_EVALUATION_STARTS = 6
# frozen: platform_params topstep_50k.xfa.back2funded (max 2, 30-day window, $599)
B2F_MAX_PER_XFA = 2
B2F_WINDOW_DAYS = 30
# frozen: platform_params topstep_50k.api list price (Primary conservative)
API_FEE_USD = 29.0
API_INTERVAL_DAYS = 30
# frozen: MC SS4.2 + platform_params lucid payouts.processing "2 个工作日" (IR-8)
LUCID_PROCESSING_HALT_DAYS = 2
# frozen: platform_params lucidflex_50k.evaluation.fees
LUCID_FIRST_PURCHASE_USD = 98.0
LUCID_RESET_USD = 95.0                  # evaluation failure  # frozen: MC SS4.3
LUCID_REPURCHASE_USD = 140.0            # funded failure      # frozen: MC SS4.3
# frozen: MC SS4.4 EV unit = 24-month total / 24
HORIZON_MONTHS = 24
# frozen: MC SS4.4 risk_haircut retention scenarios
RETENTIONS = (1.00, 0.75, 0.50)

_ALLOWED_PHASES = frozenset(
    {"evaluation", "funded", "combine", "xfa", "dead", "done"})


@dataclass(frozen=True)
class TemplateDay:
    """One trading day on the frozen synthetic template calendar (MC SS4.1).

    cal_offset = calendar days since template start — the 30-day billing
    arithmetic runs on calendar offsets, NOT on trading-day counts."""
    day_id: str
    cal_offset: int


@dataclass(frozen=True)
class LifecycleConfig:
    platform: str                        # 'lucid' | 'topstep'
    sizing_policy: str = acct.PRIMARY_POLICY   # frozen: MC SS2.5 Primary = P2
    research_costs_usd: float = 0.0      # net_business_EV_after_RD input
    decision_role: str = "primary"       # 'primary' | 'sensitivity' (isolation)
    # IR-10 (APPROVED_BY_AARON 2026-07-28): Primary = separate counters —
    # B2F does NOT consume the global evaluation-start counter. The
    # conservative variant (B2F consumes) is SENSITIVITY-ONLY and can never
    # flip the Primary Checkpoint-0 verdict (enforced in run_lifecycle).
    b2f_consumes_attempt: bool = False


@dataclass
class Ledgers:
    """SOLE owner of the four EV ledgers (frozen: MC SS4.4).

    Trade-level costs NEVER appear here (double_counting_guard): day P&L
    reaches balances exclusively through final_pnl_per_contract."""
    payout_cash: float = 0.0             # gross x split - rail (platform-computed)
    fees: dict[str, float] = field(default_factory=dict)
    terminal_cash: float = 0.0
    strategy_account_pnl: float = 0.0    # sim balance deltas (pre-split, info)

    def book_fee(self, kind: str, usd: float) -> None:
        """Always materializes the key — zero-amount markers (e.g. a credit-
        funded reset) must stay visible in the itemized ledger."""
        self.fees[kind] = self.fees.get(kind, 0.0) + usd

    def fees_total(self) -> float:
        return sum(self.fees.values())

    def report(self, research_costs_usd: float) -> dict:
        # frozen: MC SS4.4 accounting chain (no double count / no omission)
        prop_operating = self.payout_cash + self.terminal_cash - self.fees_total()
        after_rd = prop_operating - research_costs_usd
        haircut = {
            f"{int(r * 100)}": r * (self.payout_cash + self.terminal_cash)
            - self.fees_total() - research_costs_usd
            for r in RETENTIONS
        }
        return {
            "strategy_account_ev_total": self.strategy_account_pnl,
            "payout_cash_total": self.payout_cash,
            "terminal_cash": self.terminal_cash,
            "fees": dict(self.fees),
            "fees_total": self.fees_total(),
            "prop_operating_ev_total": prop_operating,
            "prop_operating_ev_monthly": prop_operating / HORIZON_MONTHS,
            "net_business_ev_after_rd_total": after_rd,
            "risk_haircut_ev_total": haircut,
        }


@dataclass
class LifecycleResult:
    config: LifecycleConfig
    events: list[AccountEvent]
    ledger_report: dict
    attempts_used: int
    terminated_by_exhaustion: bool
    b2f_used_total: int
    skips_n0: int


class _ApiBiller:
    """TopstepX API $29 / 30 calendar days, from lifecycle start (IR-9)."""

    def __init__(self, start_offset_cal: int, enabled: bool):
        self.enabled = enabled
        self.next_due = start_offset_cal

    def on_day(self, cal_offset: int) -> float:
        if not self.enabled:
            return 0.0
        fees = 0.0
        while cal_offset >= self.next_due:
            fees += API_FEE_USD
            self.next_due += API_INTERVAL_DAYS
        return fees


def _n_for_day(policy: str, balance: float, floor: float,
               anchor_usd: float, platform_cap: int) -> int:
    """Sizing via account.py pure functions ONLY (no formula duplication)."""
    buf = acct.buffer_at_entry(balance, floor)
    budget = acct.risk_budget_usd(policy, buf)
    return acct.n_micros(budget, anchor_usd, platform_cap)


def run_lifecycle(cfg: LifecycleConfig, days: list[TemplateDay],
                  paths_by_day: dict[str, TradePathRecord],
                  start_offset: int = 0) -> LifecycleResult:
    """SOLE synthetic entry point. Deterministic in its inputs.

    start_offset skips the first N template days (frozen: MC SS5 inner
    randomness source (1) = start-phase offset)."""
    if cfg.platform not in ("lucid", "topstep"):
        raise ValueError(f"unknown platform {cfg.platform!r}")
    if cfg.b2f_consumes_attempt and cfg.decision_role == "primary":
        # IR-10: the consuming variant is a conservative SENSITIVITY only.
        raise ValueError("b2f_consumes_attempt=True is sensitivity-only "
                         "(IR-10 APPROVED_BY_AARON: Primary = separate counters)")
    run = (_run_lucid if cfg.platform == "lucid" else _run_topstep)
    result = run(cfg, days[start_offset:], paths_by_day)
    for ev in result.events:
        # Live is structurally unreachable (frozen: MC SS2.6); enforce loudly.
        if ev.phase not in _ALLOWED_PHASES:
            raise AssertionError(f"forbidden phase emitted: {ev.phase!r}")
    return result


def run_real_lifecycle(*args, g9_flag=None, second_copy_flag=None, **kwargs):
    """SOLE entry for real-data business simulation. Gate logic runs first;
    flag paths injectable for hermetic gate tests (defaults = production)."""
    from itsf.guards import (G9_FLAG, SECOND_COPY_FLAG,
                             assert_real_run_allowed)
    assert_real_run_allowed(g9_flag or G9_FLAG,
                            second_copy_flag or SECOND_COPY_FLAG)
    raise NotImplementedError(
        "real S0 execution awaits Aaron's QA-report approval (guards passed)")


# --- Lucid ------------------------------------------------------------------

def _run_lucid(cfg: LifecycleConfig, days: list[TemplateDay],
               paths_by_day: dict[str, TradePathRecord]) -> LifecycleResult:
    led = Ledgers()
    events: list[AccountEvent] = []
    attempts = 1                          # includes the initial start (frozen)
    exhausted = False
    skips = 0
    halt_left = 0
    life = LucidLifecycle(fee_usd=0.0)    # fees booked HERE, not via ctor event
    led.book_fee("lucid_purchase", LUCID_FIRST_PURCHASE_USD)
    prev_balance = life.balance
    died_in = ""                          # phase the account was in when it broke

    for td in days:
        path = paths_by_day.get(td.day_id)

        if life.phase == "dead":
            # frozen: MC SS4.3 failure_policy (lucid): evaluation death ->
            # reset $95; funded death -> new evaluation at $140. Both consume
            # one evaluation start (lifecycle_attempt_policy).
            if attempts >= MAX_EVALUATION_STARTS:
                exhausted = True
                break
            attempts += 1
            funded_death = died_in == "funded"
            led.book_fee("lucid_repurchase" if funded_death else "lucid_reset",
                         LUCID_REPURCHASE_USD if funded_death else LUCID_RESET_USD)
            life = LucidLifecycle(fee_usd=0.0)
            prev_balance = life.balance
            died_in = ""

        if halt_left > 0:                 # IR-8: 2-day processing halt window
            halt_left -= 1
            ev = life.step_day(None, 0)
            ev.day = td.day_id            # template calendar label is canonical
            ev.notes = (ev.notes + ";" if ev.notes else "") + "processing_halt"
            events.append(ev)
            continue

        micros = life.max_contracts_today()
        if path is not None and micros > 0 and life.phase in ("evaluation", "funded"):
            n = _n_for_day(cfg.sizing_policy, life.balance,
                           life.floor_engine.floor, path.sizing_anchor_usd, micros)
        else:
            n = 0
        if path is not None and n == 0 and micros > 0:
            skips += 1                    # frozen: MC SS3 n=0 -> skip counted

        phase_before = life.phase
        ev = life.step_day(path if n > 0 else None, n)
        ev.day = td.day_id                # template calendar label is canonical
        events.append(ev)
        if ev.breached:
            died_in = phase_before        # eval vs funded death for restart fee
        led.book_fee("lucid_event_fees", ev.fees_usd)   # ctor fee 0 -> only real ones
        if ev.payout_gross > 0.0:
            led.payout_cash += ev.payout_cash           # platform-computed cash
            halt_left = LUCID_PROCESSING_HALT_DAYS      # IR-8
        led.strategy_account_pnl += (ev.balance - prev_balance) + ev.payout_gross
        prev_balance = ev.balance

    # frozen: payout_accounting.terminal_withdrawable_value = gross x split - rail
    tg = life.eligible_terminal_gross()
    if tg > 0.0:
        led.terminal_cash = tg * lucid_mod.TRADER_SPLIT - lucid_mod.PAYOUT_RAIL_FEE_USD

    return LifecycleResult(cfg, events, led.report(cfg.research_costs_usd),
                           attempts, exhausted, 0, skips)


# --- Topstep ----------------------------------------------------------------

def _run_topstep(cfg: LifecycleConfig, days: list[TemplateDay],
                 paths_by_day: dict[str, TradePathRecord]) -> LifecycleResult:
    led = Ledgers()
    events: list[AccountEvent] = []
    attempts = 1                          # initial Combine (frozen: incl. initial)
    exhausted = False
    skips = 0
    b2f_total = 0

    api = _ApiBiller(days[0].cal_offset if days else 0, enabled=True)  # IR-9
    sub = SubscriptionEngine(anchor_day=days[0].cal_offset if days else 0)
    combine: CombineLifecycle | None = CombineLifecycle(subscription=sub)
    xfa: XfaLifecycle | None = None
    b2f_used = 0
    xfa_death_cal: int | None = None
    prev_balance = combine.balance

    for td in days:
        path = paths_by_day.get(td.day_id)
        led.book_fee("topstep_api", api.on_day(td.cal_offset))

        if xfa is not None:
            if xfa.dead:
                # frozen: MC SS4.3 failure_policy pre-first-payout -> B2F
                # (max 2, 30-day window, $599, does NOT consume an attempt);
                # exhausted / post-payout -> new Combine (consumes attempt).
                can_b2f = (xfa.b2f_eligible and b2f_used < B2F_MAX_PER_XFA
                           and xfa_death_cal is not None
                           and td.cal_offset - xfa_death_cal <= B2F_WINDOW_DAYS)
                if can_b2f and cfg.b2f_consumes_attempt:
                    # IR-10 conservative SENSITIVITY: B2F also draws on the
                    # global evaluation-start counter.
                    can_b2f = attempts < MAX_EVALUATION_STARTS
                if can_b2f:
                    if cfg.b2f_consumes_attempt:
                        attempts += 1
                    b2f_used += 1
                    b2f_total += 1
                    led.book_fee("topstep_b2f", ts.B2F_FEE_USD)
                    xfa = XfaLifecycle()
                    prev_balance = xfa.balance
                else:
                    if attempts >= MAX_EVALUATION_STARTS:
                        exhausted = True
                        break
                    attempts += 1
                    sub = SubscriptionEngine(anchor_day=td.cal_offset,
                                             credits=sub.credits)  # credits survive
                    combine = CombineLifecycle(subscription=sub)
                    xfa = None
                    b2f_used = 0
                    prev_balance = combine.balance
            if xfa is not None and not xfa.dead:
                n = 0
                if path is not None:
                    n = _n_for_day(cfg.sizing_policy, xfa.balance,
                                   xfa.floor_engine.floor,
                                   path.sizing_anchor_usd, xfa.micro_cap)
                    if n == 0:
                        skips += 1
                # frozen: MC SS4.2 payout_policy_primary first_eligible_session,
                # maximum_allowed; Topstep XFA does NOT halt.
                req = xfa.payout_eligible()
                ev = xfa.process_day(td.cal_offset, path if n > 0 else None,
                                     n, request_payout=req)
                ev.day = td.day_id        # template calendar label is canonical
                events.append(ev)
                if ev.payout_gross > 0.0:
                    led.payout_cash += ev.payout_cash
                if ev.breached:
                    xfa_death_cal = td.cal_offset
                led.strategy_account_pnl += (ev.balance - prev_balance) + ev.payout_gross
                prev_balance = ev.balance
                continue
            if xfa is None and combine is not None:
                prev_balance = combine.balance   # restart bookkeeping continuity

        if combine is not None and not combine.passed:
            if combine.breached:
                # frozen: MC SS4.3 evaluation_failure.topstep ->
                # invoke_subscription_reset_engine; consumes one attempt.
                if attempts >= MAX_EVALUATION_STARTS:
                    exhausted = True
                    break
                attempts += 1
                fee, used_credit = combine.reset(td.cal_offset)
                led.book_fee("topstep_reset_paid", fee)
                if used_credit:
                    led.book_fee("topstep_reset_credit_used", 0.0)
                prev_balance = combine.balance
            n = 0
            if path is not None and not combine.breached:
                n = _n_for_day(cfg.sizing_policy, combine.balance,
                               combine.floor_engine.floor,
                               path.sizing_anchor_usd, ts.COMBINE_MAX_MICROS)
                if n == 0:
                    skips += 1
            ev = combine.process_day(td.cal_offset, path if n > 0 else None, n)
            ev.day = td.day_id            # template calendar label is canonical
            events.append(ev)
            led.book_fee("topstep_subscription_activation", ev.fees_usd)
            led.strategy_account_pnl += ev.balance - prev_balance
            prev_balance = ev.balance
            if combine.passed:
                # frozen: MC SS2.3 pass -> activation (fee already in event),
                # XFA starts at $0 next session
                xfa = XfaLifecycle()
                b2f_used = 0
                prev_balance = xfa.balance
        elif combine is None and xfa is None:
            break

    tg = 0.0
    if xfa is not None and not xfa.dead:
        tg = xfa.eligible_terminal_gross()
    if tg > 0.0:
        led.terminal_cash = tg * ts.TRADER_SPLIT - ts.PAYOUT_RAIL_FEE_USD

    return LifecycleResult(cfg, events, led.report(cfg.research_costs_usd),
                           attempts, exhausted, b2f_total, skips)
