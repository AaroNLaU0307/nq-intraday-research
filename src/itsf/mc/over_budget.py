"""The E2 over-budget predicate, defined at last — and defined twice.

WHAT WAS MISSING. MC §3 mandates two E2 disclosures, `P(realised_loss >
预算)` and `P(intraday_adverse_loss > 预算)`, and then defines neither
predicate. It fixes none of the three bases a per-day boolean needs: WHICH
loss, per-contract or whole position, policy budget or `n x anchor`. Nothing
in platform_params or any IR supplies them. So the fact layer has been
emitting a typed `PENDING_RULING` rather than a fabricated boolean --
because writing False for an unruled quantity reads downstream as a measured
"did not exceed" and manufactures evidence out of nothing.

THE RULING (D1, 2026-08-24, delegated to Codex GPT-5.6 Sol under Aaron's
named batch delegation, over a Fable 5 proposal). `DELEGATED=YES`: not
Aaron's own judgement, and anything citing it must say so.

  scope        E2 combos, on days that actually held a position (n >= 1)
  loss         WHOLE POSITION, per-contract x traded_n
  budget       the POLICY risk budget for that combo's sizing policy
               (Primary = P2 = $100), not `n x anchor`
  booleans     BOTH, in parallel, never mixed into one accumulator

WHY POLICY BUDGET, NOT n x ANCHOR. It is a question of what the frozen text
names. MC §3's only quantity called 预算 is `risk_budget` in the sizing
formula; reading it as `n x anchor` requires "budget" to denote a derived
quantity that section never calls by that name.

WHY WHOLE POSITION. Dimensional consistency: `risk_budget` is a
whole-position policy amount, and a per-contract loss has no defined
relation to it.

NOTHING IS LOST ON THE n x ANCHOR SIDE. The frozen text separately mandates
the `realised_loss / sizing_anchor` distribution, and `loss/anchor > n` is
exactly `whole-position loss > n x anchor`. That reading survives in full
through a disclosure the freeze already required; the two differ only on
days where `n` was clipped by a scaling cap, and that subset is itself a
reportable column rather than a silent difference.

WHY TWO BOOLEANS. The frozen text mandates two probabilities. Defining one
predicate would quietly discharge half of a frozen obligation.

SIGN CONVENTION, since both inputs are P&L rather than loss.
`final_pnl_per_contract` is positive for profit. `max_adverse_pnl` is
`min(mtm_adverse_pnl_1m)`, so it is negative when the path went against the
position and 0.0 when it never did. Loss is the negation of each, floored at
zero: a profitable day has no loss to compare, not a negative one.
"""
from __future__ import annotations

import dataclasses as _dc

__all__ = ["OVER_BUDGET_RULING", "OverBudgetVerdict", "evaluate",
           "realised_loss_usd", "intraday_adverse_loss_usd"]

#: Provenance, carried on every verdict so a reader never has to hunt it.
OVER_BUDGET_RULING = "D1_RATIFIED_2026-08-24"
OVER_BUDGET_RULING_DELEGATED = True

#: The comparison is STRICT. Frozen text says `> 预算`; a loss landing
#: exactly on the budget is not over it.
COMPARISON = ">"


def realised_loss_usd(final_pnl_per_contract: float, traded_n: int) -> float:
    """Whole-position realised loss, close-path day-end. Never negative.

    A profitable day yields 0.0 rather than a negative loss, so the
    comparison against a positive budget is well-defined on every day."""
    if traded_n <= 0:
        return 0.0
    whole = float(final_pnl_per_contract) * int(traded_n)
    return -whole if whole < 0.0 else 0.0


def intraday_adverse_loss_usd(max_adverse_pnl: float, traded_n: int) -> float:
    """Whole-position worst adverse excursion. Never negative.

    `max_adverse_pnl` is already the minimum of the adverse mark-to-market
    series, so it is <= 0; a path that never went against the position
    carries 0.0 and yields no loss."""
    if traded_n <= 0:
        return 0.0
    whole = float(max_adverse_pnl) * int(traded_n)
    return -whole if whole < 0.0 else 0.0


@_dc.dataclass(frozen=True)
class OverBudgetVerdict:
    """Both booleans, both losses and the budget that judged them.

    The losses travel with the booleans on purpose. `P(loss > budget)` is a
    frozen disclosure obligation, and a bare boolean cannot be re-derived,
    re-thresholded under a later ruling, or checked."""
    realised_over_budget: bool
    intraday_adverse_over_budget: bool
    realised_loss: float
    intraday_adverse_loss: float
    budget: float
    traded_n: int
    ruling: str = OVER_BUDGET_RULING
    delegated: bool = OVER_BUDGET_RULING_DELEGATED
    post_freeze_definition: bool = True


def evaluate(*, final_pnl_per_contract: float, max_adverse_pnl: float,
             traded_n: int, budget: float) -> OverBudgetVerdict:
    """Both E2 predicates for one day that held a position.

    The caller decides applicability -- E2 engine, `traded_n >= 1`. This
    function does the arithmetic and refuses a nonsensical budget rather
    than returning a boolean that means nothing."""
    if traded_n < 1:
        raise ValueError(
            "over_budget_not_applicable: the predicate is scoped to days "
            f"that held a position; traded_n={traded_n!r}")
    if not budget > 0.0:
        raise ValueError(
            f"over_budget_bad_budget: budget={budget!r}; a non-positive "
            "policy budget cannot judge a loss")
    realised = realised_loss_usd(final_pnl_per_contract, traded_n)
    adverse = intraday_adverse_loss_usd(max_adverse_pnl, traded_n)
    return OverBudgetVerdict(
        realised_over_budget=realised > budget,
        intraday_adverse_over_budget=adverse > budget,
        realised_loss=realised, intraday_adverse_loss=adverse,
        budget=float(budget), traded_n=int(traded_n))
