"""LucidFlex 50K lifecycle (evaluation -> sim funded) for the S0-MC engine.

Parameters are transcribed from the frozen sources cited inline; this module
does NOT reinterpret them. Live migration is fully excluded (frozen: MC SS2.6):
after the 5th payout the account REMAINS sim -- it keeps trading, receives no
further payouts, and exposes eligible_terminal_gross() so the MC business
layer can compute terminal_value (frozen: payout_accounting
terminal_withdrawable_value; the split/rail arithmetic stays in MC).

Payout processing halt (frozen: MC SS4.2 lucidflex halt): the request day
itself is modeled as the halt (no new trade); the 2-business-day processing
delay is handled by the MC synthetic calendar, not here.

gate2_cost_guard note: Lucid execution software cost is modeled at $0 and the
"Lucid cannot independently trigger GO" guard lives at the verdict layer
(frozen: platform_params gate2_cost_guard) -- nothing to enforce in this class.

Evaluation fee: charged by the CALLER's failure/repurchase policy choice
(frozen: platform_params lucidflex_50k.evaluation.fees -- first 98 /
subsequent Primary 140); this class only records the ctor-supplied fee on the
first emitted AccountEvent. The fee is a business-layer cash cost and does not
touch the sim balance.
"""
from __future__ import annotations

from itsf.contracts import AccountEvent, TradePathRecord
from itsf.mc.platforms.authoritative import over_budget_status_for
from itsf.mc.platforms.base import TrailingFloorEngine

# --- frozen machine parameters ----------------------------------------------
START_BALANCE_USD = 50_000.0   # frozen: platform_params lucidflex_50k.mll_engine.starting_balance_usd
INITIAL_MLL_USD = 48_000.0     # frozen: platform_params lucidflex_50k.mll_engine.initial_mll_usd
TRAIL_DISTANCE_USD = 2_000.0   # frozen: platform_params lucidflex_50k.mll_engine.trail_distance_usd
LOCKED_MLL_USD = 50_100.0      # frozen: platform_params lucidflex_50k.mll_engine.locked_mll_usd

PROFIT_TARGET_USD = 3_000.0    # frozen: platform_params lucidflex_50k.evaluation.profit_target_usd
CONSISTENCY_MAX_FRACTION = 0.50  # frozen: platform_params lucidflex_50k.evaluation.consistency
                                 # strict 50% at pass time; cushion NOT modeled (frozen: G6)
EVAL_MAX_MICROS = 40           # frozen: platform_params lucidflex_50k.evaluation.max_position
                               # (scaling_in_evaluation: none -> full size from day 1)

# Funded scaling tiers on simulated profit = balance - 50000, EOD update,
# bidirectional (payout deduction can downgrade).
FUNDED_TIERS = (               # frozen: platform_params lucidflex_50k.funded.scaling_tiers.tiers_50k
    (0.0, 1_000.0, 20),
    (1_000.0, 2_000.0, 30),
    (2_000.0, float("inf"), 40),
)
NEGATIVE_TIER_MICROS = 20      # frozen: G7 conservative (negative simulated profit tier
                               # UNRESOLVED -> lowest tier 2/20, mandatory disclosure)
G7_NOTE = "G7_conservative_negative_profit_tier_2_20"

QUALIFYING_DAYS_REQUIRED = 5   # frozen: platform_params lucidflex_50k.payouts.qualifying_days_required
QUALIFYING_DAY_MIN_USD = 150.0  # frozen: platform_params lucidflex_50k.payouts.qualifying_day_min_profit_usd
MIN_REQUEST_USD = 500.0        # frozen: platform_params lucidflex_50k.payouts.min_request_usd
MAX_REQUEST_FRACTION = 0.50    # frozen: platform_params lucidflex_50k.payouts.max_request "50% of profit"
MAX_REQUEST_CAP_USD = 2_000.0  # frozen: platform_params lucidflex_50k.payouts.max_request "cap $2,000"
MAX_PAYOUTS = 5                # frozen: platform_params lucidflex_50k.payouts.max_payouts_before_live_review
TRADER_SPLIT = 0.90            # frozen: platform_params lucidflex_50k.funded.profit_split_trader_pct
PAYOUT_RAIL_FEE_USD = 30.0     # frozen: platform_params lucidflex_50k.payouts.payout_rail
                               # primary_fee_usd 30 (conservative_assumption)


class LucidLifecycle:
    """Evaluation -> sim funded -> (payouts x5) -> remain-sim, or dead on breach.

    API (frozen by task order):
      max_contracts_today() -> int          # micros; 0 == cannot trade (dead / payout halt)
      step_day(path, micros) -> AccountEvent
      eligible_terminal_gross() -> float    # for MC terminal_value (frozen: MC SS2.6, SS4.2)
    """

    def __init__(self, fee_usd: float = 98.0, generation: int = 0):
        # frozen: platform_params lucidflex_50k.evaluation.fees first_purchase_usd 98 /
        # subsequent_repurchase_primary_usd 140 -- caller chooses which applies.
        self.fee_usd = float(fee_usd)
        # Account generation (N02/D5-2): 0-based, +1 at every balance-RESET
        # boundary. This ctor IS such a boundary when the caller restarts a
        # lifecycle after death, so the caller passes the next generation in
        # (orchestrator._run_lucid); a standalone account starts at 0.
        self.generation = int(generation)
        self._fee_recorded = False
        self.phase = "evaluation"
        self.balance = START_BALANCE_USD
        self.floor_engine = TrailingFloorEngine(
            INITIAL_MLL_USD, TRAIL_DISTANCE_USD, LOCKED_MLL_USD)
        # evaluation bookkeeping
        self._largest_day_profit = 0.0
        # funded bookkeeping
        self._tier_micros = NEGATIVE_TIER_MICROS
        self._tier_is_g7 = False
        self._qualifying_days = 0
        self._cycle_net = 0.0
        self._payouts_done = 0
        self._payout_pending = False
        self._session_no = 0

    # -- public API -----------------------------------------------------------

    def max_contracts_today(self) -> int:
        """Micro-contract cap for the coming session (0 = no new trade)."""
        if self.phase == "dead":
            return 0
        if self.phase == "funded" and self._payout_pending:
            return 0  # frozen: MC SS4.2 lucidflex halt (request day = no new trade)
        if self.phase == "evaluation":
            return EVAL_MAX_MICROS  # frozen: platform_params lucidflex_50k.evaluation.max_position
        return self._tier_micros

    def step_day(self, path: TradePathRecord | None, micros: int,
                 *, requested_n: int | None = None) -> AccountEvent:
        """Advance one session. `path` is the per-contract intraday record
        (S0 SS10.1 schema); None == no-trade day.

        `requested_n` (N02/D5-1) is FACT-ONLY: the position size the caller
        wanted BEFORE any cap was applied, so `cap_applied` can be emitted
        truthfully when the caller (orchestrator) has already pre-clamped
        `micros` to this platform's cap. It never influences sizing, P&L or
        any state transition. Defaults to `micros` (direct callers request
        exactly what they pass).
        """
        self._session_no += 1
        day = path.trade_date if path is not None else f"sim-{self._session_no:04d}"
        req = int(micros) if requested_n is None else int(requested_n)
        fee = 0.0
        if not self._fee_recorded:
            fee = self.fee_usd  # one-time purchase fee recorded on first event only
            self._fee_recorded = True

        if self.phase == "dead":
            return AccountEvent(day=day, phase="dead", balance=self.balance,
                                floor=self.floor_engine.floor, fees_usd=fee,
                                notes="dead_no_action",
                                # inert: no trade, no balance move
                                day_net_usd=0.0, qualifying_day=None,
                                account_generation=self.generation,
                                requested_n=req, traded_n=0, cap_applied=False,
                                over_budget_status=over_budget_status_for(None, 0))

        if self.phase == "funded" and self._payout_pending:
            return self._process_payout(day, fee, req)

        return self._trade_day(day, fee, path, micros, req)

    def eligible_terminal_gross(self) -> float:
        """Gross amount withdrawable if the horizon ended now; 0 when not
        eligible. MC applies gross*split - rail fee itself (frozen:
        payout_accounting.terminal_withdrawable_value; MC SS4.2 terminal_value).
        After the 5th payout the account is remain-sim: always 0
        (frozen: MC SS2.6 live excluded)."""
        return self._gross_candidate() if self._payout_eligible() else 0.0

    # -- internals ------------------------------------------------------------

    def _profit(self) -> float:
        """Simulated profit basis for scaling AND payout sizing: balance after
        gross deductions minus 50000 (frozen: payout_accounting.scaling_and_mll_use
        gross_deducted_balance; funded.scaling_tiers on simulated profit)."""
        return self.balance - START_BALANCE_USD

    def _gross_candidate(self) -> float:
        # frozen: platform_params lucidflex_50k.payouts.max_request
        return min(MAX_REQUEST_FRACTION * self._profit(), MAX_REQUEST_CAP_USD)

    def _payout_eligible(self) -> bool:
        return (self.phase == "funded"
                and self._payouts_done < MAX_PAYOUTS     # frozen: MC SS2.6 remain sim after 5th
                and self._qualifying_days >= QUALIFYING_DAYS_REQUIRED
                and self._cycle_net > 0.0                # frozen: payouts.cycle_net_profit ">" 0
                and self._gross_candidate() >= MIN_REQUEST_USD)  # frozen: min_request 500 else wait

    def _update_tier(self) -> None:
        """End-of-session scaling update, bidirectional
        (frozen: platform_params lucidflex_50k.funded.scaling_tiers)."""
        profit = self._profit()
        if profit < 0.0:
            self._tier_micros, self._tier_is_g7 = NEGATIVE_TIER_MICROS, True  # frozen: G7 conservative
            return
        for lo, hi, mic in FUNDED_TIERS:
            if lo <= profit < hi:
                self._tier_micros, self._tier_is_g7 = mic, False
                return

    def _enter_funded(self) -> None:
        """Fresh sim funded account: balance 50000, same floor geometry
        (frozen: MC SS2.2; platform_params lucidflex_50k.mll_engine breach_scope
        'evaluation and funded identical')."""
        self.phase = "funded"
        # BALANCE-RESET BOUNDARY (N02/D5-2): the evaluation balance is
        # discarded and replaced by the funded start balance. Any consumer
        # differencing balances across this event would read the discarded
        # evaluation profit as a loss.
        self.generation += 1
        self.balance = START_BALANCE_USD
        self.floor_engine = TrailingFloorEngine(
            INITIAL_MLL_USD, TRAIL_DISTANCE_USD, LOCKED_MLL_USD)
        self._qualifying_days = 0
        self._cycle_net = 0.0
        self._payouts_done = 0
        self._payout_pending = False
        self._update_tier()  # profit 0 -> lowest tier 2/20 first funded day (frozen: platform_params N6)

    def _process_payout(self, day: str, fee: float,
                        requested_n: int = 0) -> AccountEvent:
        """Payout request day == halt day; no new trade even if a path was
        supplied (frozen: MC SS4.2 lucidflex halt). 2-business-day processing
        is the MC calendar's concern."""
        qual_before = self._qualifying_days
        gross = self._gross_candidate()
        # frozen: payout_accounting.trader_cash_received = gross x split - rail fee
        cash = gross * TRADER_SPLIT - PAYOUT_RAIL_FEE_USD
        # frozen: payout_accounting.account_balance_effect = balance - gross
        self.balance -= gross
        # frozen: platform_params lucidflex_50k.mll_engine.payout_effect mll_next = 50100
        self.floor_engine.set_floor(LOCKED_MLL_USD)
        self._payouts_done += 1
        self._qualifying_days = 0  # frozen: payouts.qualifying_day_min_profit "resets each cycle"
        self._cycle_net = 0.0
        self._payout_pending = False
        self._update_tier()  # frozen: scaling_tiers.bidirectional (payout deduction can downgrade)
        notes = "payout_request_halt"
        if self._payouts_done >= MAX_PAYOUTS:
            notes += ";remain_sim_no_further_payouts"  # frozen: MC SS2.6 live excluded
        if self._tier_is_g7:
            notes += ";" + G7_NOTE
        return AccountEvent(day=day, phase="funded", balance=self.balance,
                            floor=self.floor_engine.floor, payout_gross=gross,
                            payout_cash=cash, fees_usd=fee, notes=notes,
                            # AUTHORITATIVE day-fact layer (N02/D5-5): the
                            # halt day traded nothing, so its net TRADING
                            # result is 0.0. The balance fell by `gross`;
                            # differencing balances here would report this
                            # day as a -gross loss day. It is not one.
                            day_net_usd=0.0,
                            # funded phase -> the qualifying ruleset is in
                            # force; the platform's own counter did not
                            # increment today (it was reset to 0 above), so
                            # the day contributed no qualifying day.
                            qualifying_day=self._qualifying_days > qual_before,
                            account_generation=self.generation,
                            requested_n=requested_n, traded_n=0,
                            cap_applied=False,
                            over_budget_status=over_budget_status_for(None, 0))

    def _trade_day(self, day: str, fee: float,
                   path: TradePathRecord | None, micros: int,
                   requested_n: int = 0) -> AccountEvent:
        balance_at_open = self.balance
        qual_before = self._qualifying_days
        cap_today = self.max_contracts_today()
        contracts = max(0, min(int(micros), cap_today))
        traded = contracts if (path is not None and contracts > 0) else 0
        # cap_applied (N02/D5-1): the POSITION-SIZE cap in force is what cut
        # the request down, on a day that actually offered a trade. Halt /
        # dead / no-path days report False (their `traded_n=0` has nothing to
        # do with the scaling tier) while `requested_n`/`traded_n` stay raw,
        # so any other reading remains recoverable without this flag
        # asserting it.
        cap_applied = (path is not None and traded < requested_n
                       and cap_today < requested_n)
        facts = dict(account_generation=self.generation,
                     requested_n=requested_n, traded_n=traded,
                     cap_applied=cap_applied,
                     over_budget_status=over_budget_status_for(path, traded))
        if path is not None and contracts > 0:
            # Intraday breach on the ADVERSE path, equity incl. unrealized
            # (frozen: platform_params lucidflex_50k.mll_engine.intraday_breach;
            # MC SS2.2 conservative assumption V-A; MC SS3 adverse-path rule).
            equity_path = [self.balance + contracts * p for p in path.mtm_adverse_pnl_1m]
            _hit = self.floor_engine.breached_intraday(equity_path)
            if _hit is not None:
                self.phase = "dead"
                # Unified settlement (ruling R1): worse of floor / adverse mark,
                # minus adverse slippage (frozen MC SS2.2 触发价 ± adverse slippage).
                from itsf.mc.platforms.base import breach_settlement
                self.balance = breach_settlement(
                    self.floor_engine.floor, equity_path[_hit], contracts)
                return AccountEvent(day=day, phase="dead", balance=self.balance,
                                    floor=self.floor_engine.floor, breached=True,
                                    fees_usd=fee, notes="mll_breach_adverse_path",
                                    # The R1 settlement IS this day's realized
                                    # trading result; it is a same-day, same-
                                    # generation balance move, not a reset.
                                    day_net_usd=self.balance - balance_at_open,
                                    qualifying_day=None, **facts)
            day_net = contracts * path.final_pnl_per_contract
        else:
            day_net = 0.0
        self.balance += day_net

        if self.phase == "evaluation":
            self._largest_day_profit = max(self._largest_day_profit, day_net)
            # frozen: platform_params lucidflex_50k.mll_engine.eod_update
            self.floor_engine.eod_update(self.balance)
            profit = self._profit()
            if (profit >= PROFIT_TARGET_USD
                    and self._largest_day_profit <= CONSISTENCY_MAX_FRACTION * profit):
                # frozen: platform_params lucidflex_50k.evaluation.consistency formula
                # largest_single_day_profit / account_profit <= 0.50, checked at
                # pass time, STRICT (cushion not modeled -- frozen: G6)
                eval_balance = self.balance
                self._enter_funded()          # <- generation boundary
                facts["account_generation"] = self.generation
                return AccountEvent(day=day, phase="funded", balance=self.balance,
                                    floor=self.floor_engine.floor, fees_usd=fee,
                                    notes=f"evaluation_passed eval_balance={eval_balance:.2f}",
                                    # The day's trading result stands on its
                                    # own; the balance shown is already the
                                    # post-reset funded start balance, which
                                    # is why the generation moved. Consumers
                                    # MUST NOT difference across this event.
                                    day_net_usd=day_net,
                                    # phase 'funded' -> tri-state must be a
                                    # bool; the funded counter starts at 0 and
                                    # this (evaluation-rules) day added none.
                                    qualifying_day=self._qualifying_days > 0,
                                    **facts)
            return AccountEvent(day=day, phase="evaluation", balance=self.balance,
                                floor=self.floor_engine.floor, fees_usd=fee,
                                day_net_usd=day_net,
                                # evaluation has no qualifying-day concept
                                qualifying_day=None, **facts)

        # funded session end
        notes: list[str] = []
        self._cycle_net += day_net
        if day_net >= QUALIFYING_DAY_MIN_USD:
            # frozen: platform_params lucidflex_50k.payouts.qualifying_day_min_profit_usd 150
            self._qualifying_days += 1
        # frozen: platform_params lucidflex_50k.mll_engine.eod_update (same engine as eval)
        self.floor_engine.eod_update(self.balance)
        self._update_tier()  # frozen: scaling_tiers.update_time end_of_session
        if self._tier_is_g7:
            notes.append(G7_NOTE)
        if self._payout_eligible():
            # frozen: MC SS4.2 payout_policy_primary request_timing
            # first_eligible_session, request_amount maximum_allowed
            self._payout_pending = True
            notes.append("payout_eligible_next_session_halt")
        if self._payouts_done >= MAX_PAYOUTS:
            notes.append("remain_sim")  # frozen: MC SS2.6 (keeps trading, no payouts)
        return AccountEvent(day=day, phase="funded", balance=self.balance,
                            floor=self.floor_engine.floor, fees_usd=fee,
                            notes=";".join(notes),
                            day_net_usd=day_net,
                            # SINGLE SOURCE OF TRUTH: the platform's own
                            # counter transition above (frozen threshold
                            # QUALIFYING_DAY_MIN_USD applied exactly once, in
                            # one place). Never re-compare day_net here.
                            qualifying_day=self._qualifying_days > qual_before,
                            **facts)
