"""The D1 predicate: pin the three bases, not just the arithmetic.

MC §3 mandates two E2 disclosures and defines neither predicate, so the
whole content of D1 is a choice among bases: which loss, per-contract or
whole position, policy budget or n x anchor. The arithmetic is trivial and
the bases are the ruling. These tests pin the bases.
"""
from __future__ import annotations

import pytest

from itsf.mc import over_budget as ob


def test_the_loss_basis_is_the_whole_position_not_one_contract():
    """The ruling's dimensional argument, made executable. $40 lost per
    contract on 3 contracts is $120 against a $100 budget -- over. Read
    per-contract it is $40 and under, and the whole disclosure inverts."""
    v = ob.evaluate(final_pnl_per_contract=-40.0, max_adverse_pnl=-40.0,
                    traded_n=3, budget=100.0)
    assert v.realised_loss == pytest.approx(120.0)
    assert v.realised_over_budget is True

    one = ob.evaluate(final_pnl_per_contract=-40.0, max_adverse_pnl=-40.0,
                      traded_n=1, budget=100.0)
    assert one.realised_over_budget is False


def test_the_budget_basis_is_the_policy_amount_not_n_times_anchor():
    """P2 is $100 per trade whatever n is. Under an `n x anchor` reading
    the same day would be judged against 3 x anchor and could pass; the
    ruling took the policy amount because MC §3's only quantity named
    'budget' is risk_budget in the sizing formula."""
    v = ob.evaluate(final_pnl_per_contract=-40.0, max_adverse_pnl=0.0,
                    traded_n=3, budget=100.0)
    assert v.budget == 100.0          # not 3 x anything
    assert v.realised_over_budget is True


def test_both_booleans_are_produced_and_stay_separate():
    """The frozen text mandates two probabilities. A day can be over on the
    intraday path and back under by the close -- exactly the case that a
    single predicate would erase."""
    v = ob.evaluate(final_pnl_per_contract=-10.0, max_adverse_pnl=-60.0,
                    traded_n=2, budget=100.0)
    assert v.realised_loss == pytest.approx(20.0)
    assert v.intraday_adverse_loss == pytest.approx(120.0)
    assert v.realised_over_budget is False
    assert v.intraday_adverse_over_budget is True


def test_a_profitable_day_has_no_loss_rather_than_a_negative_one():
    v = ob.evaluate(final_pnl_per_contract=250.0, max_adverse_pnl=0.0,
                    traded_n=4, budget=100.0)
    assert v.realised_loss == 0.0
    assert v.intraday_adverse_loss == 0.0
    assert v.realised_over_budget is False
    assert v.intraday_adverse_over_budget is False


def test_a_profitable_close_still_reports_its_adverse_excursion():
    """Profit at the close does not retract the drawdown that happened on
    the way. Collapsing this to one boolean would hide the excursion the
    frozen text asks about by name."""
    v = ob.evaluate(final_pnl_per_contract=30.0, max_adverse_pnl=-80.0,
                    traded_n=2, budget=100.0)
    assert v.realised_over_budget is False
    assert v.intraday_adverse_over_budget is True


def test_the_comparison_is_strict():
    """Frozen text says `> 预算`. A loss landing exactly on the budget is
    not over it, and off-by-one here moves a mandated probability."""
    on = ob.evaluate(final_pnl_per_contract=-50.0, max_adverse_pnl=-50.0,
                     traded_n=2, budget=100.0)
    assert on.realised_loss == pytest.approx(100.0)
    assert on.realised_over_budget is False

    over = ob.evaluate(final_pnl_per_contract=-50.01, max_adverse_pnl=0.0,
                       traded_n=2, budget=100.0)
    assert over.realised_over_budget is True


def test_the_predicate_refuses_a_day_that_held_no_position():
    """Applicability is the caller's, but a nonsense call must fail loudly
    rather than return False -- which downstream reads as measured."""
    for n in (0, -1):
        with pytest.raises(ValueError) as ei:
            ob.evaluate(final_pnl_per_contract=-500.0, max_adverse_pnl=-500.0,
                        traded_n=n, budget=100.0)
        assert "over_budget_not_applicable" in str(ei.value)


def test_the_predicate_refuses_a_budget_that_cannot_judge():
    for bad in (0.0, -100.0):
        with pytest.raises(ValueError) as ei:
            ob.evaluate(final_pnl_per_contract=-500.0, max_adverse_pnl=0.0,
                        traded_n=1, budget=bad)
        assert "over_budget_bad_budget" in str(ei.value)


def test_the_losses_travel_with_the_booleans():
    """`P(loss > budget)` is a frozen obligation. A bare boolean cannot be
    re-derived, re-thresholded under a later ruling, or checked."""
    v = ob.evaluate(final_pnl_per_contract=-33.0, max_adverse_pnl=-77.0,
                    traded_n=3, budget=100.0)
    assert v.realised_loss == pytest.approx(99.0)
    assert v.intraday_adverse_loss == pytest.approx(231.0)
    assert v.budget == 100.0
    assert v.traded_n == 3
    assert v.post_freeze_definition is True
    assert v.delegated is True
    assert v.ruling == "D1_RATIFIED_2026-08-24"


def test_adverse_sign_convention_matches_the_producer():
    """`max_adverse_pnl` is min(mtm_adverse_pnl_1m): negative when the path
    went against the position, 0.0 when it never did. A positive value
    would be a producer bug, and treating it as a loss would invent one."""
    never = ob.evaluate(final_pnl_per_contract=-10.0, max_adverse_pnl=0.0,
                        traded_n=5, budget=100.0)
    assert never.intraday_adverse_loss == 0.0
    assert ob.intraday_adverse_loss_usd(5.0, 5) == 0.0
