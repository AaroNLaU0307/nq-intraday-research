"""The three feasibility gates, as ratified — and only as ratified.

PROVENANCE, which matters more here than in most modules. The frozen text
(S0 §10.4 row 2, MC §6) NAMES three gates -- integer position, frequency,
payout path -- and never defines how any of them passes. Everything in this
module is therefore a POST-FREEZE DEFINITION, ruled on 2026-08-24 by Codex
GPT-5.6 Sol under Aaron's named batch delegation, over a proposal by Fable
5. `DELEGATED=YES`: this is a delegated ruling, not Aaron's own judgement,
and anything citing these gates at N17 must say so.

WHERE THE NUMBERS COME FROM — say this plainly, because one of them was
briefly claimed to be something it is not. All three thresholds were SET in
that ruling. None is derived from the frozen text, from platform arithmetic,
or from any prior document; a repository-wide search found no source for any
of them. M2's 5.0 was at one point argued to follow from platform arithmetic
-- five qualifying days cannot fit in a month with fewer than five trading
days -- but the platform has no calendar-month window at all
(`qualifying_days_required: 5`, reset only after an approved payout), so the
days accumulate across months and the argument does not hold. The value
stands; the claim that it was derived does not.

AND THEY WERE SET AFTER THE REVEAL. S0-T001 was unblinded before any of this
was decided. That cannot be undone, only disclosed, and O3 carries the
disclosure into the report, the post-run attestation and the N17 terminal
event.

Every gate returns its measured value beside its threshold, never a bare
boolean, so the evidence survives into the record instead of collapsing to
pass/fail at the point where it stops being auditable.
"""
from __future__ import annotations

import dataclasses as _dc
from typing import Mapping, Sequence

from . import atoms as _atoms

__all__ = ["FEASIBILITY_RULING", "GATE_SCENARIOS", "GateOutcome",
           "payout_gate", "integer_position_gate", "frequency_gate",
           "FeasibilityGateError"]


class FeasibilityGateError(ValueError):
    """A gate could not be evaluated. Never a silent False."""

    def __init__(self, code: str, detail: str = ""):
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code


#: The ruling these definitions come from. Carried into every result so a
#: reader never has to go looking for whose decision this was.
FEASIBILITY_RULING = "ND2_ND3_RATIFIED_WITH_MODIFICATIONS_2026-08-24"
FEASIBILITY_RULING_DELEGATED = True

# --- M5: which scenarios the path-shaped gates are computed in --------------
# The frozen decision table binds its EV conditions to Conservative (P5) and
# Stress (median) and binds the feasibility clause to NO scenario at all.
# M5 reads the feasibility clause as sharing the row it appears in: both
# scenarios, each must pass. Base and Severe are reported and gate nothing.
GATE_SCENARIOS = ("Conservative", "Stress")

# --- M1: payout gate --------------------------------------------------------
#: Per-path boolean is `payout_count >= 1`; per-world share is over that
#: world's M paths; the gate is the epistemic P5 of those shares. SET, not
#: derived. Reads as: in the 5% most adverse worlds, a payout is still the
#: majority outcome.
PAYOUT_WORLD_SHARE_P5_MIN = 0.50

# --- M2: frequency gate -----------------------------------------------------
#: Oracle tradeable days per month, from the SEALED DAY UNIVERSE -- dates,
#: not results. SET, not derived (see the module docstring). Scenario-
#: independent: it is an S0-side measurement and takes the same value for
#: every combo.
FREQUENCY_ORACLE_DAYS_PER_MONTH_MIN = 5.0

# --- M3: integer-position gate ---------------------------------------------
#: Denominator is ATTEMPTED days -- `skips_n0 + executed_trade_days` -- not
#: offered days. The gate measures how often sizing starves when it is
#: actually consulted; days with no sizing question (dead account, halt)
#: would only dilute that. The atom invariant already holds
#: `skips_n0 + executed_trade_days <= offered_days`.
SKIP_RATE_P95_MAX = 0.25


@_dc.dataclass(frozen=True)
class GateOutcome:
    """One gate's verdict WITH the number that produced it.

    `passed` is never returned alone. A gate that collapses to a boolean at
    the point of evaluation cannot be audited afterwards, and these three
    are exactly the ones N17 will be asked to justify."""
    gate: str
    passed: bool
    measured: float
    threshold: float
    comparison: str
    scenario: str
    n_worlds: int
    detail: str = ""
    ruling: str = FEASIBILITY_RULING
    delegated: bool = FEASIBILITY_RULING_DELEGATED
    post_freeze_definition: bool = True

    def __post_init__(self):
        if self.comparison not in (">=", "<="):
            raise FeasibilityGateError("feasibility_bad_comparison",
                                       self.comparison)


def _by_world(observations) -> dict:
    """world_index -> that world's atoms. One atom per (world, phase)."""
    out: dict = {}
    for atom in observations.atoms:
        out.setdefault(atom.world_index, []).append(atom)
    if not out:
        raise FeasibilityGateError("feasibility_no_worlds",
                                   "the observation set carries no atoms")
    return out


#: `percentile_linear` takes q in 0-100, NOT 0-1. Passing 0.05 and 0.95 is
#: silent: it returns something near the minimum for BOTH gates, so the
#: payout gate reads a lower tail it never meant and the skip gate reads a
#: lower tail instead of its upper one. Caught here only because one test
#: used a deliberately asymmetric sample; every symmetric fixture passes.
P5 = 5.0
P95 = 95.0


def _epistemic(shares: Sequence[float], q: float) -> float:
    """The frozen type-7 estimator, on the epistemic layer. `q` is 0-100.

    M4 declines Wilson intervals deliberately: paths cluster inside a world
    and are not independent, so an interval built on n = B x M would be
    systematically too narrow -- false confidence, which the ruling treats
    as no better than false looseness. The epistemic quantile is the
    machinery the frozen text already chose for exactly this uncertainty."""
    # A RANGE CHECK CANNOT CATCH THIS. 0.95 is a perfectly legal 0.95th
    # percentile, so "meant 95, wrote 0.95" passes any bounds test -- which
    # is exactly how the first cut of this module shipped both gates
    # reading a lower tail. The only check that works is an allowlist: this
    # module has exactly two ratified quantiles, and anything else is
    # either a slip or a ruling nobody made.
    if q not in (P5, P95):
        raise FeasibilityGateError(
            "feasibility_quantile_not_ratified",
            f"q={q!r}; only P5={P5} and P95={P95} are ratified, and a "
            "0-1 value would read the wrong tail without ever leaving "
            "the legal range")
    return _atoms.percentile_linear(sorted(shares), q)


def payout_gate(observations, *, scenario: str) -> GateOutcome:
    """M1. Per-path payout_count >= 1 -> per-world share -> epistemic P5.

    Truncated cycles at the 24-month horizon are counted as they fall: an
    unfinished cycle simply produces no payout event. That matches the
    frozen terminal rule, where a balance not yet withdrawable counts 0
    rather than being pro-rated into existence."""
    worlds = _by_world(observations)
    shares = []
    for _index, atoms in sorted(worlds.items()):
        paid = sum(1 for a in atoms if a.payout_count >= 1)
        shares.append(paid / len(atoms))
    measured = _epistemic(shares, P5)
    return GateOutcome(
        gate="payout", scenario=scenario,
        passed=measured >= PAYOUT_WORLD_SHARE_P5_MIN,
        measured=measured, threshold=PAYOUT_WORLD_SHARE_P5_MIN,
        comparison=">=", n_worlds=len(shares),
        detail="epistemic P5 of the per-world share of paths with >=1 payout")


def integer_position_gate(observations, *, scenario: str) -> GateOutcome:
    """M3. Per-world skip share over ATTEMPTED days -> epistemic P95.

    Two fail-closed rules, both from the ruling and both load-bearing:

    * a world that offered days but attempted none scores 1.0, not 0/0 and
      not "skip". Without it a world whose account died early would vanish
      from the gate, and starvation and death would cover for each other.
    * if NO world offered a day, the gate FAILS rather than returning a
      vacuous pass over an empty set."""
    worlds = _by_world(observations)
    shares = []
    any_offered = False
    for _index, atoms in sorted(worlds.items()):
        offered = sum(a.offered_days for a in atoms)
        skips = sum(a.skips_n0 for a in atoms)
        executed = sum(a.executed_trade_days for a in atoms)
        attempted = skips + executed
        if offered:
            any_offered = True
        if attempted == 0:
            shares.append(1.0 if offered else 0.0)
            continue
        shares.append(skips / attempted)
    if not any_offered:
        return GateOutcome(
            gate="integer_position", scenario=scenario, passed=False,
            measured=float("nan"), threshold=SKIP_RATE_P95_MAX,
            comparison="<=", n_worlds=len(shares),
            detail="no world offered a day; the gate fails rather than "
                   "passing vacuously over an empty set")
    measured = _epistemic(shares, P95)
    return GateOutcome(
        gate="integer_position", scenario=scenario,
        passed=measured <= SKIP_RATE_P95_MAX,
        measured=measured, threshold=SKIP_RATE_P95_MAX,
        comparison="<=", n_worlds=len(shares),
        detail="epistemic P95 of per-world skips_n0 / (skips_n0 + executed)")


def frequency_gate(day_universe: Sequence[str]) -> GateOutcome:
    """M2. Oracle tradeable days per month, from the sealed day universe.

    The input is DATES, not results -- which is what makes this computable
    without touching a revealed value. The threshold, however, was set after
    the reveal like the other two, and O3 discloses that.

    Months are counted as distinct calendar months spanned, so a universe
    inside one month divides by 1 rather than by a fraction."""
    days = sorted(str(d) for d in day_universe)
    if not days:
        return GateOutcome(
            gate="frequency", scenario="ALL", passed=False,
            measured=float("nan"),
            threshold=FREQUENCY_ORACLE_DAYS_PER_MONTH_MIN,
            comparison=">=", n_worlds=0,
            detail="empty day universe; fails rather than dividing by zero")
    months = len({d[:7] for d in days})
    measured = len(days) / months
    return GateOutcome(
        gate="frequency", scenario="ALL",
        passed=measured >= FREQUENCY_ORACLE_DAYS_PER_MONTH_MIN,
        measured=measured,
        threshold=FREQUENCY_ORACLE_DAYS_PER_MONTH_MIN,
        comparison=">=", n_worlds=0,
        detail=f"{len(days)} oracle days across {months} calendar month(s)")
