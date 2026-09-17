"""A1 -- THE EFFECT IS NOT JUST THE ANNOUNCEMENT JUMP.

Sealed L: *"restricted to the LOWER HALF of |R_init| (median split on a
causally computable, ADR14-normalized quantity, computed within trailing
information only), the primary estimate retains the SAME SIGN."*

    metric_i      = |R_init_i| / ADR14_i          causal, scale-free
    boundary_i    = median(metric_1 .. metric_{i-1})   STRICTLY PRIOR events
    member_i      = metric_i <= boundary_i
    A1 holds      <=>  sign(mean(Y_net | members)) == sign(mean(Y_net | all))

**Why the split is trailing rather than full-sample.** A full-sample median is
a look-ahead: an event's membership would depend on events that had not
happened yet, and L-5 bans exactly that. Here event *i*'s boundary is fixed the
moment event *i* occurs and can never move again -- `tests/test_auxiliary.py`
appends later events and asserts every earlier membership is byte-identical.

**No new parameter, and no place to put one.** There is no minimum-prior count,
no tolerance, no winsorisation and no alternative split: the first event simply
has no prior median and is not a member. Adding any of those would be the
threshold sealed C.3 and L-8 forbid.

**A1 is NON-CONFIRMATORY.** It is a guard on support, never a source of it: it
can only prevent `PREDICTIVE_EFFECT_SUPPORTED_ON_SAMPLE`, never create it, and
it says nothing on its own about the verdict. A failing A1 does not exclude the
effect either -- it records that the effect lives in the large jumps, which is
a different and far less tradeable phenomenon (sealed L, M.3).
"""
from __future__ import annotations

from dataclasses import dataclass
from statistics import median

from .errors import R1Error
from .signal import Signal


@dataclass(frozen=True)
class A1Membership:
    date_et: str
    metric: float | None          # |R_init| / ADR14, None when ADR14 is NA
    boundary: float | None        # the trailing median in force at this event
    is_member: bool               # in the lower half of |R_init|


@dataclass(frozen=True)
class A1Result:
    memberships: tuple[A1Membership, ...]
    n_members: int
    mean_all: float | None
    mean_members: float | None
    sign_holds: bool

    @property
    def evaluable(self) -> bool:
        return self.mean_members is not None and self.mean_all is not None


def a1_metric(signal: Signal, adr14_value: float | None) -> float | None:
    """|R_init| normalised by the causal ADR14. None when ADR14 is unavailable."""
    if adr14_value is None or adr14_value <= 0:
        return None
    return abs(signal.r_init) / adr14_value


def a1_memberships(dates, metrics) -> tuple[A1Membership, ...]:
    """Trailing median split, in event order. Future events cannot reach back."""
    dates, metrics = tuple(dates), tuple(metrics)
    if len(dates) != len(metrics):
        raise R1Error("A1: dates and metrics must align")
    out: list[A1Membership] = []
    prior: list[float] = []
    for date_et, metric in zip(dates, metrics):
        boundary = median(prior) if prior else None
        member = (metric is not None and boundary is not None
                  and metric <= boundary)
        out.append(A1Membership(date_et=date_et, metric=metric,
                                boundary=boundary, is_member=member))
        if metric is not None:
            prior.append(metric)          # only AFTER this event is classified
    return tuple(out)


def _sign(x: float) -> int:
    return 1 if x > 0 else (-1 if x < 0 else 0)


def evaluate_a1(results, memberships) -> A1Result:
    """Does the primary estimate keep its sign on the lower half of |R_init|?"""
    results, memberships = tuple(results), tuple(memberships)
    if len(results) != len(memberships):
        raise R1Error("A1: results and memberships must align")
    all_values = [r.y_net_usd for r in results]
    member_values = [r.y_net_usd for r, m in zip(results, memberships)
                     if m.is_member]
    mean_all = sum(all_values) / len(all_values) if all_values else None
    mean_members = (sum(member_values) / len(member_values)
                    if member_values else None)
    # An unevaluable A1 does not silently pass: with no members there is no
    # evidence that the effect survives outside the large jumps.
    holds = (mean_all is not None and mean_members is not None
             and _sign(mean_members) == _sign(mean_all) and _sign(mean_all) != 0)
    return A1Result(memberships=memberships, n_members=len(member_values),
                    mean_all=mean_all, mean_members=mean_members,
                    sign_holds=holds)
