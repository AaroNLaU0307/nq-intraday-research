"""Authoritative day-fact helpers for the platform state machines (N02/D5).

Two jobs, both deliberately thin:

1. `over_budget_status_for` — the single place that maps a day's traded
   position onto the typed E2 over-budget state (frozen text mandates the
   E2 disclosure and defines no predicate; see contracts.OverBudgetStatus).

2. `check_event_facts` — a VERIFICATION pass over an emitted event stream.

CROSS-CHECK, NOT DEFINITION (frozen scope, N02/D5-4). The identity

        day_net_usd == balance - prev_balance + payout_gross

is a cross-check with a strictly bounded domain: two ADJACENT events of the
SAME account_generation, where the later event is not a balance-reset event.
It is NOT the definition of a day's net — the definition is whatever the
platform state machine computed when it moved the balance, which is exactly
what `day_net_usd` carries. Across generations (evaluation->funded, Combine
reset, Combine pass -> XFA, Back2Funded, new Combine) the identity does not
hold and must never be applied; the generation field is what makes that
detectable instead of silent.

Deliberately NOT a runtime assertion inside the platforms: elevating a
cross-check to a load-bearing production invariant would (a) contradict the
frozen scope above and (b) fire on legitimate white-box state seeding in
main-agent-owned tests. It is a callable verifier instead, run by the N02
battery over every scenario.
"""
from __future__ import annotations

from dataclasses import dataclass

from itsf.contracts import (QUALIFYING_PHASES, AccountEvent, OverBudgetStatus,
                            TradePathRecord)

# --- verification rejection codes -------------------------------------------
AUTH_FACTS_MISSING = "authoritative_facts_missing"
AUTH_GENERATION_MISSING = "account_generation_missing"
AUTH_GENERATION_NOT_MONOTONE = "account_generation_not_monotone"
AUTH_GENERATION_JUMP = "account_generation_jump_gt_1"
AUTH_DAY_NET_INVARIANT = "day_net_cross_check_violation"
AUTH_QUALIFYING_TRISTATE = "qualifying_day_tristate_violation"
AUTH_OVER_BUDGET_STATE = "over_budget_state_invalid"
AUTH_CAP_FLAG = "cap_applied_inconsistent"

AUTH_REJECTION_CODES = frozenset({
    AUTH_FACTS_MISSING, AUTH_GENERATION_MISSING, AUTH_GENERATION_NOT_MONOTONE,
    AUTH_GENERATION_JUMP, AUTH_DAY_NET_INVARIANT, AUTH_QUALIFYING_TRISTATE,
    AUTH_OVER_BUDGET_STATE, AUTH_CAP_FLAG,
})

# Money tolerance for the cross-check: platform arithmetic is plain float
# addition of USD amounts, so only representation error is expected.
CROSS_CHECK_TOL_USD = 1e-6


class AuthoritativeStreamError(AssertionError):
    """Raised by `check_event_facts(..., strict=True)`; carries `.violations`."""

    def __init__(self, violations: list["FactViolation"]):
        self.violations = list(violations)
        head = "; ".join(f"{v.code}@{v.index}({v.day}) {v.detail}"
                         for v in self.violations[:5])
        more = "" if len(self.violations) <= 5 else f" (+{len(self.violations) - 5} more)"
        super().__init__(f"{len(self.violations)} day-fact violation(s): {head}{more}")


@dataclass(frozen=True)
class FactViolation:
    code: str
    index: int
    day: str
    detail: str = ""


def over_budget_status_for(path: TradePathRecord | None,
                           traded_n: int) -> OverBudgetStatus:
    """Typed E2 over-budget state for a day (never a fabricated boolean).

    Engine attribution comes from the day's TradePathRecord.engine (frozen
    S0 SS10.1 schema: 'E1' | 'E2'); an unknown engine is a hard failure
    rather than a silent default.
    """
    if path is None or traded_n <= 0:
        return OverBudgetStatus.NOT_APPLICABLE_NO_TRADE
    engine = path.engine
    if engine == "E1":
        # frozen: MC SS3 scopes the over-budget disclosure to E2 ("E2 强制
        # 报告") — the obligation does not reach E1 days.
        return OverBudgetStatus.NOT_APPLICABLE
    if engine == "E2":
        return OverBudgetStatus.PENDING_RULING
    raise ValueError(f"unknown engine {engine!r} (frozen set: E1 | E2)")


def day_net_cross_check(prev: AccountEvent, ev: AccountEvent) -> float | None:
    """Signed cross-check residual, or None when the identity does not apply.

    Applies ONLY within one generation (see module docstring). Returns
    `day_net_usd - (balance - prev.balance + payout_gross)`.
    """
    if (ev.day_net_usd is None
            or ev.account_generation is None
            or prev.account_generation is None
            or ev.account_generation != prev.account_generation):
        return None
    return ev.day_net_usd - ((ev.balance - prev.balance) + ev.payout_gross)


def check_event_facts(events: list[AccountEvent], *,
                      require_facts: bool = True,
                      strict: bool = False) -> list[FactViolation]:
    """Verify the authoritative day-fact layer of an emitted event stream.

    `require_facts=False` tolerates legacy events (day_net_usd is None) so
    the verifier can be pointed at a mixed stream; every other check still
    runs on the events that DO carry facts.
    """
    out: list[FactViolation] = []
    prev: AccountEvent | None = None
    for i, ev in enumerate(events):
        if ev.day_net_usd is None:
            if require_facts:
                out.append(FactViolation(AUTH_FACTS_MISSING, i, ev.day,
                                         "day_net_usd is None"))
            prev = ev
            continue
        if ev.account_generation is None:
            out.append(FactViolation(AUTH_GENERATION_MISSING, i, ev.day))
        if (ev.qualifying_day is not None
                and ev.phase not in QUALIFYING_PHASES):
            out.append(FactViolation(
                AUTH_QUALIFYING_TRISTATE, i, ev.day,
                f"phase={ev.phase!r} carries qualifying_day="
                f"{ev.qualifying_day!r}; non-qualifying phases emit None"))
        if ev.over_budget_status is None or ev.over_budget is not None:
            out.append(FactViolation(
                AUTH_OVER_BUDGET_STATE, i, ev.day,
                f"status={ev.over_budget_status!r} value={ev.over_budget!r}"))
        if ev.cap_applied and not ev.traded_n < ev.requested_n:
            out.append(FactViolation(
                AUTH_CAP_FLAG, i, ev.day,
                f"traded_n={ev.traded_n} requested_n={ev.requested_n}"))
        if prev is not None and prev.account_generation is not None \
                and ev.account_generation is not None:
            delta = ev.account_generation - prev.account_generation
            if delta < 0:
                out.append(FactViolation(
                    AUTH_GENERATION_NOT_MONOTONE, i, ev.day,
                    f"{prev.account_generation} -> {ev.account_generation}"))
            elif delta > 1:
                out.append(FactViolation(
                    AUTH_GENERATION_JUMP, i, ev.day,
                    f"{prev.account_generation} -> {ev.account_generation}"))
        if prev is not None:
            resid = day_net_cross_check(prev, ev)
            if resid is not None and abs(resid) > CROSS_CHECK_TOL_USD:
                out.append(FactViolation(
                    AUTH_DAY_NET_INVARIANT, i, ev.day,
                    f"day_net={ev.day_net_usd!r} balance_delta="
                    f"{ev.balance - prev.balance!r} payout_gross="
                    f"{ev.payout_gross!r} residual={resid!r}"))
        prev = ev
    if strict and out:
        raise AuthoritativeStreamError(out)
    return out
