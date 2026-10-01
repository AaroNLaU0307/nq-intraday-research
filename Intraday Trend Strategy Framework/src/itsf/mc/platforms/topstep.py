"""Topstep 50K lifecycle engines: subscription/reset-credit, Combine, XFA.

Subagent-owned module. All numeric parameters are transcribed from frozen
sources and cited inline:
  gate1/platform_params.yaml  topstep_50k.*  (v0.6, frozen)
  MC_METHOD_SPEC.md           SS2.3 / SS4.2 / SS4.3 (v0.6, frozen)

Scope notes (frozen):
- Primary variant only: standard purchase path, XFA standard payout path,
  NO DLL.  # frozen: MC SS2.5 decision_roles topstep_50k_stdpurchase_xfastd_nodll
- The 6-attempt lifecycle counter, Back2Funded max-2-per-XFA / 30-day window,
  and payout request TIMING policy live in the MC orchestrator.
  # frozen: MC SS4.3 lifecycle_attempt_policy (counter NOT here; signals only)
- Day arguments are integer CALENDAR-day offsets on the synthetic template
  calendar.  # frozen: MC SS4.1 topstep_combine every_30_days_from_current_rebill_anchor
- Breach checks run in real time on the ADVERSE equity path including
  unrealized P&L; touch == breach.
  # frozen: MC SS3 (both platforms adverse-path) + platform_params
  # topstep_50k.combine.mll_engine.intraday_breach / xfa.mll_engine.intraday_breach
- Best-day locks 15:10 CT (combine) / payout day locks 16:00 CT (XFA); at the
  daily granularity of this simulator the day's settled net P&L IS the locked
  value.  # frozen: platform_params consistency_target.best_day_lock_time,
  # xfa.payout_paths.standard.payout_day_lock_time
"""
from __future__ import annotations

from dataclasses import dataclass, field

from itsf.contracts import AccountEvent, TradePathRecord
from itsf.mc.platforms.authoritative import over_budget_facts
from itsf.mc.platforms.base import TrailingFloorEngine

# --- Combine (standard path) -------------------------------------------------
# frozen: platform_params topstep_50k.combine.mll_engine
COMBINE_START_BALANCE_USD = 50_000.0
COMBINE_INITIAL_MLL_USD = 48_000.0
TRAIL_DISTANCE_USD = 2_000.0
COMBINE_LOCKED_MLL_USD = 50_000.0
# frozen: platform_params topstep_50k.combine.profit_target_usd
COMBINE_PROFIT_TARGET_USD = 3_000.0
# frozen: platform_params topstep_50k.combine.max_position micros 50
COMBINE_MAX_MICROS = 50
# frozen: platform_params topstep_50k.combine.subscription_usd_per_month.standard_path
SUBSCRIPTION_FEE_USD = 49.0
# frozen: platform_params topstep_50k.reset_policy.paid_reset_fee_usd.standard_path
PAID_RESET_FEE_USD = 49.0
# frozen: platform_params topstep_50k.activation.standard_path_activation_usd
ACTIVATION_FEE_USD = 149.0
# frozen: platform_params topstep_50k.subscription_engine.rebill_interval_days
REBILL_INTERVAL_DAYS = 30
# frozen: platform_params topstep_50k.reset_policy.reset_credit.expires_after_days
CREDIT_EXPIRES_AFTER_DAYS = 365
# frozen: platform_params topstep_50k.reset_policy.max_resets_per_account_per_day
MAX_RESETS_PER_ACCOUNT_PER_DAY = 2

# --- XFA (standard payout path, no DLL) --------------------------------------
# frozen: platform_params topstep_50k.xfa.mll_engine (balance_start 0, MLL -2000 -> lock 0)
XFA_START_BALANCE_USD = 0.0
XFA_INITIAL_MLL_USD = -2_000.0
XFA_LOCKED_MLL_USD = 0.0
# frozen: platform_params topstep_50k.xfa.payout_paths.standard.qualifying
XFA_QUALIFYING_DAY_MIN_NET_USD = 150.0
XFA_QUALIFYING_DAYS_REQUIRED = 5
# frozen: platform_params topstep_50k.xfa.payout_paths.standard.cycle_net_profit
XFA_CYCLE_NET_MIN_USD = 0.01          # first cycle exempt
# frozen: platform_params topstep_50k.xfa.payout_paths.standard.max_request
XFA_PAYOUT_MAX_FRACTION = 0.5
XFA_PAYOUT_CAP_USD = 2_000.0
# frozen: platform_params topstep_50k.xfa.payout_min_usd
XFA_PAYOUT_MIN_USD = 125.0
# frozen: platform_params topstep_50k.xfa.profit_split.default_trader_pct (Primary 90/10)
TRADER_SPLIT = 0.90
# frozen: platform_params topstep_50k.xfa.payout_rail.primary (Wise, topstep_fee_usd 0)
PAYOUT_RAIL_FEE_USD = 0.0
# frozen: platform_params topstep_50k.xfa.back2funded.fee_50k_usd (paid by CALLER)
B2F_FEE_USD = 599.0


@dataclass
class ResetCredit:
    """One banked Reset Credit, tagged to account size and path type.

    # frozen: platform_params reset_policy.reset_credit
    # (tied_to_account_size_and_type: true; expires_after_days: 365)
    Expiry boundary interpretation: credit is unusable once age >= 365 days
    (conservative direction: earlier expiry -> more paid fees -> no false GO).
    """
    granted_day: int
    size: str = "50k"
    path: str = "standard"
    expires_after_days: int = CREDIT_EXPIRES_AFTER_DAYS

    def expired(self, day: int) -> bool:
        return (day - self.granted_day) >= self.expires_after_days

    def matches(self, size: str, path: str) -> bool:
        # frozen: reset_policy.reset_credit.tied_to_account_size_and_type
        return self.size == size and self.path == path


class SubscriptionEngine:
    """Combine subscription billing + Reset Credit bank (standard path).

    # frozen: platform_params topstep_50k.subscription_engine
    #   charged_at_purchase: true      (purchase day charge; NOT a rebill,
    #                                   so it banks NO credit — credit is
    #                                   granted_per_rebill: 1)
    #   rebill_interval_days: 30       (from anchor, not calendar month)
    #   auto_cancel_on_pass: true
    #   continues_after_mll_breach: true / no_pause: true
    # frozen: platform_params topstep_50k.reset_policy
    #   use_available_reset_credit_first + credit_matching oldest-first
    #   paid reset $49; reset (paid OR credit) moves rebill anchor to
    #   reset day + 30; credits survive cancellation but a cancelled
    #   subscription itself cannot be reset; max 2 resets per account per day
    """

    def __init__(self, anchor_day: int, size: str = "50k", path: str = "standard",
                 credits: list[ResetCredit] | None = None) -> None:
        self.anchor_day = anchor_day
        self.size = size
        self.path = path
        self.active = True
        self.purchase_charged = False
        self.next_rebill_day = anchor_day + REBILL_INTERVAL_DAYS
        # credits survive cancellation and may be seeded from a prior engine
        # frozen: reset_policy.reset_credit.survives_subscription_cancellation
        self.credits: list[ResetCredit] = list(credits) if credits else []
        self._last_reset_day: int | None = None
        self._resets_on_last_day = 0

    def on_day(self, day: int) -> float:
        """Return subscription fees charged on `day` (0.0 on non-billing days).

        Catches up any rebill dates passed since the last call (billing dates
        are calendar days; the simulator only visits trading days).
        """
        if not self.active:
            return 0.0
        fees = 0.0
        if not self.purchase_charged and day >= self.anchor_day:
            fees += SUBSCRIPTION_FEE_USD   # frozen: subscription_engine.charged_at_purchase
            self.purchase_charged = True
        while self.active and day >= self.next_rebill_day:
            fees += SUBSCRIPTION_FEE_USD
            # frozen: subscription_engine.rebill_credit_granted 1 (per rebill only)
            self.credits.append(ResetCredit(granted_day=self.next_rebill_day,
                                            size=self.size, path=self.path))
            self.next_rebill_day += REBILL_INTERVAL_DAYS
        return fees

    def reset(self, day: int) -> tuple[float, bool]:
        """Perform an account reset on `day`; return (fee_usd, used_credit).

        Consumes the oldest matching non-expired credit if one exists, else
        charges the paid reset fee. Either way the rebill anchor moves to
        reset day + 30.  # frozen: reset_policy.reset_effect_on_rebill_date
        """
        if not self.active:
            # frozen: reset_policy.reset_credit note — cancelled subscription
            # itself cannot be reset (credits go to a FUTURE same-spec Combine)
            raise RuntimeError("cancelled subscription cannot be reset")
        if self._last_reset_day == day:
            if self._resets_on_last_day >= MAX_RESETS_PER_ACCOUNT_PER_DAY:
                # frozen: reset_policy.max_resets_per_account_per_day 2
                raise RuntimeError("max 2 resets per account per day (frozen)")
            self._resets_on_last_day += 1
        else:
            self._last_reset_day = day
            self._resets_on_last_day = 1

        fee, used_credit = PAID_RESET_FEE_USD, False
        # frozen: reset_policy.use_available_reset_credit_first
        #         + credit_matching use_oldest_matching_credit_first
        usable = [c for c in self.credits
                  if c.matches(self.size, self.path) and not c.expired(day)]
        if usable:
            oldest = min(usable, key=lambda c: c.granted_day)
            self.credits.remove(oldest)
            fee, used_credit = 0.0, True
        # frozen: reset_policy.reset_effect_on_rebill_date set_to_reset_date_plus_30_days
        # (identical for paid reset and credit reset)
        self.next_rebill_day = day + REBILL_INTERVAL_DAYS
        return fee, used_credit

    def cancel(self) -> None:
        """Cancel billing.  # frozen: subscription_engine.auto_cancel_on_pass"""
        self.active = False


class CombineLifecycle:
    """Topstep 50K Combine (evaluation phase), standard path.

    Soft consistency: exceeding 50% of the CURRENT target never fails the
    account; it inflates the target to best_day / 0.50, which enforces
    best_day <= 50% of total profit at the moment of passing (the two frozen
    formulations are equivalent under the inflation invariant target >=
    2 * best_day maintained here).
    # frozen: platform_params topstep_50k.combine.consistency_target
    #   (type soft_target_increase; rule best_day > 0.5*target -> target = best_day/0.50)
    # frozen: MC SS2.3 consistency is a soft rule, must NOT be a hard fail (N4)
    """

    def __init__(self, subscription: SubscriptionEngine | None = None,
                 generation: int = 0) -> None:
        self.subscription = subscription
        self.breached = False
        self.passed = False
        # Account generation (N02/D5-2): 0-based, +1 at every balance-RESET
        # boundary. Constructing a Combine IS such a boundary whenever the
        # caller is replacing a previous account in the same lifecycle
        # (orchestrator: new Combine after XFA death), so the caller passes
        # the next generation in.
        self.generation = int(generation)
        self._fresh_state()

    def _fresh_state(self) -> None:
        # frozen: combine.mll_engine starting 50000 / MLL 48000 / trail 2000 / lock 50000
        self.balance = COMBINE_START_BALANCE_USD
        self.floor_engine = TrailingFloorEngine(
            floor=COMBINE_INITIAL_MLL_USD,
            trail_distance=TRAIL_DISTANCE_USD,
            lock_at=COMBINE_LOCKED_MLL_USD)
        self.target = COMBINE_PROFIT_TARGET_USD
        self.best_day = 0.0

    @property
    def profit(self) -> float:
        return self.balance - COMBINE_START_BALANCE_USD

    def process_day(self, day: int, trade: TradePathRecord | None = None,
                    n_micros: int = 1, *,
                    requested_n: int | None = None,
                    budget: float = 0.0) -> AccountEvent:
        """`requested_n` (N02/D5-1) is FACT-ONLY — the pre-cap position size
        the caller wanted, used solely so `cap_applied` can be emitted
        truthfully when the caller already pre-clamped `n_micros`. It never
        influences sizing, P&L or any state transition."""
        fees = self.subscription.on_day(day) if self.subscription else 0.0
        req = int(n_micros) if requested_n is None else int(requested_n)
        # Combine has NO qualifying-day concept (frozen: qualifying days live
        # only in xfa.payout_paths) -> qualifying_day is None on every event.
        idle_facts = dict(day_net_usd=0.0, qualifying_day=None,
                          account_generation=self.generation,
                          requested_n=req, traded_n=0, cap_applied=False,
                          **over_budget_facts(None, 0, 0.0))
        if self.passed:
            return AccountEvent(day=str(day), phase="done", balance=self.balance,
                                floor=self.floor_engine.floor, fees_usd=fees,
                                notes="combine_passed", **idle_facts)
        if self.breached:
            # frozen: subscription_engine.continues_after_mll_breach — practice
            # mode until reset: subscription still bills, trades do not count
            return AccountEvent(day=str(day), phase="combine", balance=self.balance,
                                floor=self.floor_engine.floor, fees_usd=fees,
                                notes="awaiting_reset", **idle_facts)
        if trade is not None:
            balance_at_open = self.balance
            n = min(n_micros, COMBINE_MAX_MICROS)   # frozen: combine.max_position micros 50
            traded = max(0, n)
            facts = dict(qualifying_day=None,
                         account_generation=self.generation,
                         requested_n=req, traded_n=traded,
                         cap_applied=(traded < req
                                      and COMBINE_MAX_MICROS < req),
                         **over_budget_facts(trade, traded, budget))
            # frozen: combine.mll_engine.intraday_breach — realtime net P&L
            # incl. unrealized, adverse path (MC SS3); touch == breach
            equity_path = [self.balance + n * p for p in trade.mtm_adverse_pnl_1m]
            idx = self.floor_engine.breached_intraday(equity_path)
            if idx is not None:
                self.breached = True
                # Unified settlement (ruling R1, base.breach_settlement)
                from itsf.mc.platforms.base import breach_settlement
                self.balance = breach_settlement(
                    self.floor_engine.floor, equity_path[idx], n)
                return AccountEvent(day=str(day), phase="combine", balance=self.balance,
                                    floor=self.floor_engine.floor, breached=True,
                                    fees_usd=fees, notes="mll_breach_flattened",
                                    # R1 settlement = this day's realized
                                    # result (same day, same generation).
                                    day_net_usd=self.balance - balance_at_open,
                                    **facts)
            day_pnl = n * trade.final_pnl_per_contract
            self.balance += day_pnl
            # frozen: consistency_target.best_day_lock_time 15:10 CT — daily
            # granularity: the settled day P&L is the locked best-day value
            if day_pnl > self.best_day:
                self.best_day = day_pnl
            # frozen: consistency_target.rule (soft target inflation)
            if self.best_day > 0.5 * self.target:
                self.target = self.best_day / 0.50
            # frozen: combine.mll_engine.eod_update
            self.floor_engine.eod_update(self.balance)
            if self.profit >= self.target:
                self.passed = True
                fees += ACTIVATION_FEE_USD   # frozen: activation.standard_path 149
                if self.subscription:
                    self.subscription.cancel()   # frozen: auto_cancel_on_pass
                return AccountEvent(day=str(day), phase="done", balance=self.balance,
                                    floor=self.floor_engine.floor, fees_usd=fees,
                                    notes="combine_passed_activation_charged",
                                    # The pass day itself is a normal trading
                                    # day; the XFA balance reset happens in
                                    # the NEXT account (new generation).
                                    day_net_usd=day_pnl, **facts)
            return AccountEvent(day=str(day), phase="combine", balance=self.balance,
                                floor=self.floor_engine.floor, fees_usd=fees,
                                day_net_usd=day_pnl, **facts)
        return AccountEvent(day=str(day), phase="combine", balance=self.balance,
                            floor=self.floor_engine.floor, fees_usd=fees,
                            **idle_facts)

    def reset(self, day: int) -> tuple[float, bool]:
        """Reset after evaluation failure. Returns (fee_usd, used_credit).

        # frozen: MC SS4.3 failure_policy.evaluation_failure.topstep
        #   invoke_subscription_reset_engine (credit first, else paid $49)
        # frozen: reset_policy.stats_reset_on_reset — full fresh state
        Attempt counting is the ORCHESTRATOR's job (MC SS4.3), not done here.
        """
        if self.subscription is None:
            raise RuntimeError("reset requires an active SubscriptionEngine")
        fee, used_credit = self.subscription.reset(day)
        # BALANCE-RESET BOUNDARY (N02/D5-2): _fresh_state restores the 50000
        # start balance, so every event after this one belongs to a new
        # account generation and must not be differenced against the last
        # pre-reset event.
        self.generation += 1
        self._fresh_state()
        self.breached = False
        return fee, used_credit


class XfaLifecycle:
    """Topstep 50K XFA (sim funded), STANDARD payout path, no DLL (Primary).

    # frozen: MC SS2.3 — balance starts at $0 ("50K" is a buying-power label);
    #   MLL -2000 -> locks at 0; scaling by balance, next-session only;
    #   payout: MLL permanently 0, counts restart, NO halt during processing
    #   (funds deducted immediately, trading allowed at once — MC SS4.2);
    #   request day itself not counted toward the next cycle (MC SS4.2).
    Back2Funded: caller pays $599 and constructs a FRESH XfaLifecycle;
    max 2 per XFA and the 30-day window are enforced by the caller.
    # frozen: platform_params xfa.back2funded + MC SS4.3
    """

    def __init__(self, generation: int = 0) -> None:
        # Account generation (N02/D5-2): constructing an XFA is ALWAYS a
        # balance-reset boundary in a running lifecycle (Combine pass -> XFA
        # at $0, or Back2Funded -> fresh XFA at $0), so the caller passes the
        # next generation in.
        self.generation = int(generation)
        self.balance = XFA_START_BALANCE_USD
        # frozen: xfa.mll_engine initial_mll -2000 / trail 2000 / locked 0
        self.floor_engine = TrailingFloorEngine(
            floor=XFA_INITIAL_MLL_USD,
            trail_distance=TRAIL_DISTANCE_USD,
            lock_at=XFA_LOCKED_MLL_USD)
        self.dead = False
        self.payout_count = 0
        self.qualifying_days = 0
        self.cycle_net = 0.0
        # frozen: xfa.scaling_tiers basis current_account_balance,
        # update next_session_only; balance 0 -> lowest tier
        self.micro_cap = self._tier_micros(self.balance)

    @staticmethod
    def _tier_micros(balance: float) -> int:
        # frozen: platform_params xfa.scaling_tiers.tiers_50k
        #   [<1500 -> 20] [1500..2000 incl -> 30] [>2000 -> 50]
        if balance < 1500.0:
            return 20
        if balance <= 2000.0:
            return 30
        return 50

    @property
    def b2f_eligible(self) -> bool:
        # frozen: xfa.back2funded.availability_after_first_payout false
        return self.dead and self.payout_count == 0

    def eligible_terminal_gross(self) -> float:
        """Gross withdrawable if the horizon ended now; 0 when ineligible.

        Keeps the eligibility formula inside the platform (main-agent ruling
        R5-adjacent: orchestrator must not replicate platform formulas).
        # frozen: payout_accounting.terminal_withdrawable_value; MC SS4.2
        """
        if not self.payout_eligible():
            return 0.0
        return min(XFA_PAYOUT_MAX_FRACTION * self.balance, XFA_PAYOUT_CAP_USD)

    def payout_eligible(self) -> bool:
        """Standard-path eligibility check against current settled state.

        # frozen: xfa.payout_paths.standard — 5 winning days (net >= $150,
        # non-consecutive OK), cycle net >= $0.01 after the first payout
        # (first cycle exempt), request = min(50% balance, $2000) with the
        # $125 platform minimum (payout_min_usd).
        """
        if self.dead:
            return False
        if self.qualifying_days < XFA_QUALIFYING_DAYS_REQUIRED:
            return False
        if self.payout_count > 0 and not (self.cycle_net >= XFA_CYCLE_NET_MIN_USD):
            return False
        gross = min(XFA_PAYOUT_MAX_FRACTION * self.balance, XFA_PAYOUT_CAP_USD)
        return gross >= XFA_PAYOUT_MIN_USD

    def process_day(self, day: int, trade: TradePathRecord | None = None,
                    n_micros: int = 1, request_payout: bool = False,
                    *, requested_n: int | None = None,
                    budget: float = 0.0) -> AccountEvent:
        """`requested_n` (N02/D5-1) is FACT-ONLY — the pre-cap position size
        the caller wanted, used solely so `cap_applied` can be emitted
        truthfully when the caller already pre-clamped `n_micros`. It never
        influences sizing, P&L or any state transition."""
        req = int(n_micros) if requested_n is None else int(requested_n)
        if self.dead:
            return AccountEvent(day=str(day), phase="dead", balance=self.balance,
                                floor=self.floor_engine.floor, notes="account_dead",
                                # inert: no trade, no balance move; a dead
                                # account has no qualifying-day concept left
                                day_net_usd=0.0, qualifying_day=None,
                                account_generation=self.generation,
                                requested_n=req, traded_n=0, cap_applied=False,
                                **over_budget_facts(None, 0, 0.0))
        balance_at_open = self.balance
        qual_before = self.qualifying_days
        # ELIGIBILITY IS A PROPERTY OF THE STATE ENTERING THE SESSION, and it
        # is captured HERE, before the day moves anything. `payout_eligible`
        # checks "current settled state"; once this session's P&L has been
        # applied that is no longer the state the caller decided on.
        #
        # Re-reading it after the fact is how MC-R001 attempt 2 died at 29h:
        # an account entered the session eligible, had a losing day, its
        # balance fell under $250, `min(0.5 * balance, 2000) >= 125` stopped
        # holding, and the guard below accused the orchestrator of a bug it
        # had not committed. The orchestrator was right; the guard was reading
        # the wrong state.
        #
        # frozen: MC SS4.2 payout_policy_primary request_timing
        # first_eligible_session -- the same reading `lucid` implements by
        # settling eligibility at session end for the NEXT session.
        eligible_at_open = self.payout_eligible()
        # frozen: xfa.scaling_tiers.update next_session_only — today's cap was
        # fixed at the END of the previous session; platform enforces the limit
        cap_today = self.micro_cap
        n = min(n_micros, cap_today)
        traded = max(0, n) if trade is not None else 0
        facts = dict(account_generation=self.generation,
                     requested_n=req, traded_n=traded,
                     cap_applied=(trade is not None and traded < req
                                  and cap_today < req),
                     **over_budget_facts(trade, traded, budget))
        day_net = 0.0
        payout_gross = 0.0
        payout_cash = 0.0
        payout_taken = False
        lapsed = False
        if trade is not None:
            # frozen: xfa.mll_engine.intraday_breach — realtime net P&L incl.
            # unrealized (adverse path, MC SS3) touches floor -> PERMANENT close
            equity_path = [self.balance + n * p for p in trade.mtm_adverse_pnl_1m]
            idx = self.floor_engine.breached_intraday(equity_path)
            if idx is not None:
                self.dead = True
                # Unified settlement (ruling R1, base.breach_settlement)
                from itsf.mc.platforms.base import breach_settlement
                self.balance = breach_settlement(
                    self.floor_engine.floor, equity_path[idx], n)
                return AccountEvent(day=str(day), phase="dead", balance=self.balance,
                                    floor=self.floor_engine.floor, breached=True,
                                    notes="mll_breach_permanent_close",
                                    # R1 settlement = this day's realized
                                    # result (same day, same generation).
                                    day_net_usd=self.balance - balance_at_open,
                                    # phase 'dead': the XFA qualifying
                                    # ruleset no longer applies to the event
                                    qualifying_day=None, **facts)
            day_net = n * trade.final_pnl_per_contract
            self.balance += day_net
        if request_payout:
            # THE CALLER'S CONTRACT, checked against the state the caller was
            # required to decide on. A request made without entry eligibility
            # is still a caller defect and still refuses, in this same place
            # and with this same message.
            if not eligible_at_open:
                raise ValueError("payout requested while ineligible (orchestrator bug)")
            # frozen: payout_accounting — gross removed from sim balance;
            # trader cash = gross x split - rail fee (Wise $0 Primary)
            candidate = min(XFA_PAYOUT_MAX_FRACTION * self.balance,
                            XFA_PAYOUT_CAP_USD)
            # LAPSE AND WAIT (Aaron, 2026-09-16, clarifying an edge the sealed
            # wording left underspecified). The amount is `maximum_allowed` on
            # the settled balance AFTER this session, and `payout_min_usd`
            # stays binding. When the session's own result leaves that amount
            # below the platform minimum there is no COMPLIANT request to
            # make, so none is made: the request lapses, no sub-minimum payout
            # is ever emitted, and eligibility is evaluated again normally at
            # the next session.
            if candidate >= XFA_PAYOUT_MIN_USD:
                payout_taken = True
                payout_gross = candidate
                self.balance -= payout_gross
                payout_cash = payout_gross * TRADER_SPLIT - PAYOUT_RAIL_FEE_USD
                # frozen: xfa.mll_engine.payout_effect — MLL = 0 PERMANENTLY
                self.floor_engine.set_floor(XFA_LOCKED_MLL_USD)
                self.payout_count += 1
                # frozen: payout_paths.standard.after_payout — 5-day count restarts
                self.qualifying_days = 0
                self.cycle_net = 0.0
                # frozen: MC SS4.2 — request day itself NOT counted toward the
                # next cycle (its net joins neither qualifying count nor
                # cycle_net); NO halt: trading may continue immediately, funds
                # already deducted
            else:
                lapsed = True
        # A LAPSED REQUEST LEAVES AN ORDINARY TRADING SESSION BEHIND IT. The
        # frozen rule excluding the request day from the next cycle exists
        # because a payout RESETS that cycle; with no payout there is no reset
        # and no reason to discard the day, so its net joins `cycle_net` and
        # the qualifying count exactly as any other day's does. Discarding it
        # would penalise the account for a request it was not allowed to make.
        if not payout_taken and trade is not None:
            self.cycle_net += day_net
            # frozen: payout_paths.standard.qualifying — winning day locks EOD
            if day_net >= XFA_QUALIFYING_DAY_MIN_NET_USD:
                self.qualifying_days += 1
        # frozen: xfa.mll_engine.eod_update on the GROSS-DEDUCTED balance
        # (payout_accounting.scaling_and_mll_use: gross_deducted_balance)
        self.floor_engine.eod_update(self.balance)
        # frozen: scaling next_session_only — cap for the NEXT session set now;
        # payout lowering the balance lowers the cap (scaling_tiers.payout_effect)
        self.micro_cap = self._tier_micros(self.balance)
        return AccountEvent(day=str(day), phase="xfa", balance=self.balance,
                            floor=self.floor_engine.floor,
                            # A lapse is EVIDENCE, not a silent skip: the
                            # session is the one where eligibility held and no
                            # compliant request could be made.
                            notes=("payout_request_lapsed_below_minimum"
                                   if lapsed else ""),
                            payout_gross=payout_gross, payout_cash=payout_cash,
                            # AUTHORITATIVE (N02/D5-5): the day's TRADING net
                            # only. On a payout day the balance also fell by
                            # payout_gross (frozen: payout_accounting), so a
                            # balance-difference reading would report the
                            # cycle's best day as a large loss day.
                            day_net_usd=day_net,
                            # SINGLE SOURCE OF TRUTH: the platform's own
                            # counter transition. On a payout-request day it
                            # is False even when day_net >= $150, because
                            # frozen MC SS4.2 / payout_paths.standard
                            # .after_payout exclude the request day from
                            # every count — a re-derived threshold test would
                            # get exactly this day wrong.
                            qualifying_day=self.qualifying_days > qual_before,
                            **facts)
