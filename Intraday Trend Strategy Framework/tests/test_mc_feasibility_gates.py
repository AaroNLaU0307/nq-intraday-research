"""The three ratified feasibility gates, pinned to the ruling that set them.

Each gate is a POST-FREEZE DEFINITION set on 2026-08-24 by delegated ruling.
The tests below pin the DEFINITIONS, not merely the numbers: a threshold can
be changed by a later ruling, but the denominator M3 uses, the fail-closed
branches, and the refusal to collapse to a bare boolean are the parts that
were argued for and are the parts that quietly rot.
"""
from __future__ import annotations

import math

import pytest

from itsf.mc import feasibility as fz


class _Atom:
    """The four fields the gates read. Deliberately not a real atom -- these
    tests are about the gate arithmetic, not about atom validation."""

    def __init__(self, world_index, payout_count=0, offered_days=0,
                 skips_n0=0, executed_trade_days=0):
        self.world_index = world_index
        self.payout_count = payout_count
        self.offered_days = offered_days
        self.skips_n0 = skips_n0
        self.executed_trade_days = executed_trade_days


class _Obs:
    def __init__(self, atoms):
        self.atoms = tuple(atoms)


# --- M1 ---------------------------------------------------------------------

def test_payout_gate_measures_the_per_world_share_not_the_pooled_one():
    """The pooled share and the P5 of per-world shares are different
    numbers, and the ruling picked the second on purpose: a handful of
    worlds paying out many times must not cover for worlds paying none."""
    # 20 worlds x 5 paths. Ten worlds pay on every path, ten on none.
    # Pooled: 50/100 = 0.50 -- which would PASS the 0.50 threshold.
    # Per-world P5: the bottom of a half-empty distribution -- which fails.
    atoms = []
    for w in range(10):
        atoms += [_Atom(w, payout_count=3) for _ in range(5)]
    for w in range(10, 20):
        atoms += [_Atom(w, payout_count=0) for _ in range(5)]
    out = fz.payout_gate(_Obs(atoms), scenario="Conservative")
    assert out.n_worlds == 20
    assert out.measured == pytest.approx(0.0)
    assert out.passed is False


def test_payout_gate_carries_its_number_and_its_provenance():
    atoms = [_Atom(w, payout_count=1) for w in range(10)]
    out = fz.payout_gate(_Obs(atoms), scenario="Stress")
    assert out.passed is True
    assert out.measured == 1.0
    assert out.threshold == 0.50
    assert out.comparison == ">="
    assert out.scenario == "Stress"
    assert out.post_freeze_definition is True
    assert out.delegated is True
    assert "2026-08-24" in out.ruling


# --- M3 ---------------------------------------------------------------------

def test_integer_position_denominator_is_attempted_not_offered():
    """The ruling's single most consequential choice. One world, 100
    offered days, of which only 10 ever reached sizing: 5 skips, 5
    executed. Over ATTEMPTED the skip share is 0.5; over OFFERED it would
    be 0.05 -- a tenfold difference from the denominator alone."""
    atoms = [_Atom(0, offered_days=100, skips_n0=5, executed_trade_days=5)]
    out = fz.integer_position_gate(_Obs(atoms), scenario="Conservative")
    assert out.measured == pytest.approx(0.5)
    assert out.passed is False          # 0.5 > 0.25


def test_a_world_that_offered_days_but_attempted_none_scores_one():
    """Fail-closed. Without this a world whose account died early drops out
    of the gate entirely, and starvation and death cover for each other."""
    atoms = [_Atom(0, offered_days=40, skips_n0=0, executed_trade_days=0)]
    out = fz.integer_position_gate(_Obs(atoms), scenario="Conservative")
    assert out.measured == 1.0
    assert out.passed is False


def test_no_world_offered_a_day_fails_rather_than_passing_vacuously():
    atoms = [_Atom(0, offered_days=0), _Atom(1, offered_days=0)]
    out = fz.integer_position_gate(_Obs(atoms), scenario="Stress")
    assert out.passed is False
    assert math.isnan(out.measured)
    assert "vacuous" in out.detail


def test_integer_position_uses_p95_so_the_bad_tail_decides():
    """Skips are the bad quantity, so the gate looks at the worst worlds.
    19 clean worlds and 1 starving one must not average away."""
    # Three starving worlds in twenty. ONE would not fail the gate and
    # should not: P95 over 20 worlds sits below a single outlier, which is
    # the tail rule working rather than a leniency.
    atoms = [_Atom(w, offered_days=10, skips_n0=0, executed_trade_days=10)
             for w in range(17)]
    atoms += [_Atom(w, offered_days=10, skips_n0=10, executed_trade_days=0)
              for w in (17, 18, 19)]
    out = fz.integer_position_gate(_Obs(atoms), scenario="Conservative")
    assert out.measured == pytest.approx(1.0)
    assert out.passed is False

    lone = [_Atom(w, offered_days=10, skips_n0=0, executed_trade_days=10)
            for w in range(19)]
    lone.append(_Atom(19, offered_days=10, skips_n0=10,
                      executed_trade_days=0))
    out = fz.integer_position_gate(_Obs(lone), scenario="Conservative")
    assert out.passed is True, "one outlier in twenty must not fail P95"


# --- M2 ---------------------------------------------------------------------

def test_frequency_gate_counts_calendar_months_spanned():
    days = [f"2026-0{m}-{d:02d}" for m in (1, 2) for d in range(1, 7)]
    out = fz.frequency_gate(days)
    assert out.measured == pytest.approx(6.0)     # 12 days / 2 months
    assert out.passed is True


def test_frequency_gate_fails_below_the_set_threshold():
    days = ["2026-01-05", "2026-01-12", "2026-02-03"]
    out = fz.frequency_gate(days)
    assert out.measured == pytest.approx(1.5)
    assert out.passed is False


def test_frequency_gate_refuses_an_empty_universe():
    out = fz.frequency_gate([])
    assert out.passed is False
    assert math.isnan(out.measured)


def test_frequency_gate_is_scenario_independent():
    """It is an S0-side measurement over the sealed day universe, so it
    takes one value for every combo. Anything that made it vary by scenario
    would mean it had started reading MC output."""
    days = [f"2026-01-{d:02d}" for d in range(1, 11)]
    assert fz.frequency_gate(days).scenario == "ALL"


# --- the ruling's own record ------------------------------------------------

def test_the_thresholds_are_the_ratified_ones():
    assert fz.PAYOUT_WORLD_SHARE_P5_MIN == 0.50
    assert fz.FREQUENCY_ORACLE_DAYS_PER_MONTH_MIN == 5.0
    assert fz.SKIP_RATE_P95_MAX == 0.25
    assert fz.GATE_SCENARIOS == ("Conservative", "Stress")


def test_the_module_does_not_claim_any_threshold_was_derived():
    """M2's 5.0 was briefly argued to follow from platform arithmetic --
    five qualifying days cannot fit in a month with fewer than five trading
    days. The platform has no calendar-month window
    (`qualifying_days_required: 5`, reset only after an approved payout), so
    the days accumulate across months and the argument fails. The value
    stands; the claim must not come back."""
    import pathlib
    src = pathlib.Path(fz.__file__).read_text(encoding="utf-8")
    lowered = src.lower()
    assert "set, not derived" in lowered
    for forbidden in ("zero free parameters", "derived from platform"):
        assert forbidden not in lowered, forbidden


def test_the_gates_read_the_tail_they_claim_to_read():
    """REGRESSION, and it shipped for about ten minutes.

    `percentile_linear` takes q in 0-100. The first cut of this module
    passed 0.05 and 0.95, which returns something near the MINIMUM for
    both -- so the payout gate read a lower tail it never meant and the
    skip gate read a lower tail instead of its upper one. Both gates were
    wrong in the permissive direction and no symmetric fixture notices.

    The asymmetric sample below is the whole point: 19 worlds at one value
    and 1 at another, so P5 and P95 must land on opposite ends."""
    # payout: 19 worlds pay nothing, 1 pays -> P5 must sit at the bad end
    atoms = [_Atom(w, payout_count=0) for w in range(19)]
    atoms.append(_Atom(19, payout_count=1))
    low = fz.payout_gate(_Obs(atoms), scenario="Conservative")
    assert low.measured == pytest.approx(0.0)
    assert low.passed is False

    # skips: 17 clean worlds, 3 starving -> P95 must sit at the bad end.
    # Under the 0-1 bug this read the LOWER tail and returned 0.0.
    atoms = [_Atom(w, offered_days=10, skips_n0=0, executed_trade_days=10)
             for w in range(17)]
    atoms += [_Atom(w, offered_days=10, skips_n0=10, executed_trade_days=0)
              for w in (17, 18, 19)]
    high = fz.integer_position_gate(_Obs(atoms), scenario="Conservative")
    assert high.measured == pytest.approx(1.0)
    assert high.passed is False


def test_a_quantile_that_is_not_one_of_the_two_ratified_ones_is_refused():
    """The first guard I wrote here was theatre: it range-checked 0-100,
    and 0.95 is a legal 0.95th percentile, so it caught nothing. The only
    check that separates "meant 95" from "wrote 0.95" is an allowlist of
    the two quantiles the ruling actually set."""
    for wrong in (0.05, 0.95, 50.0, 99.0):
        with pytest.raises(fz.FeasibilityGateError) as ei:
            fz._epistemic([0.0, 1.0], wrong)
        assert ei.value.code == "feasibility_quantile_not_ratified"
    # n=2, so h = 1 * 0.95 and the answer interpolates to 0.95,
    # not 1.0 -- type-7 on a two-element sample, not a bug.
    assert fz._epistemic([0.0, 1.0], fz.P95) == pytest.approx(0.95)


def test_every_module_carrying_a_ratified_number_is_in_the_config_digest():
    """The harvest list decides what a change to a constant invalidates.

    Its own rule is harvested-by-default with written exemptions, and the
    exemption set is empty. Three modules created on 2026-08-24 carry
    numbers that reach the verdict -- the gate thresholds, the strict
    over-budget comparison, the order-statistic positions -- so leaving any
    of them out would mean a threshold could move without the digest
    noticing, and atoms produced under the old value would still look
    current.

    This is cheap today only because production scale has never run and no
    MC atom exists to invalidate. After N16 it would not be."""
    from itsf.mc import atoms as at

    for module in ("itsf.mc.feasibility", "itsf.mc.over_budget",
                   "itsf.mc.fixed_world"):
        assert module in at.HARVESTED_CONSTANT_MODULES, module


def test_moving_a_ratified_threshold_moves_the_config_digest():
    """The property the harvest list exists for, exercised rather than
    assumed: change a gate threshold and every atom minted afterwards
    carries a different lifecycle_config_digest."""
    import itsf.mc.feasibility as target
    from itsf.mc import atoms as at

    before = at.harvest_frozen_constants()
    original = target.SKIP_RATE_P95_MAX
    try:
        target.SKIP_RATE_P95_MAX = 0.30
        after = at.harvest_frozen_constants()
    finally:
        target.SKIP_RATE_P95_MAX = original

    assert before != after, (
        "the skip-rate threshold moved and the harvested constants did "
        "not; a ruled number can then change without invalidating a "
        "single atom produced under the old one")
    assert at.harvest_frozen_constants() == before      # restored
