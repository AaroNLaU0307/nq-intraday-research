"""TASKS 6 and 7 -- controls C1 and C2.

Both are built in the SAME code path as the Primary (`r1.trade.run_arm`), so a
divergence between control and Primary is impossible by construction rather
than by discipline (sealed R.1 S2-5).

C1 -- SIGN-RANDOMIZED (sealed K.1)
    identical event set, identical O(08:33) -> O(09:29), identical cost model;
    only the DIRECTION is replaced by a seeded fair coin, 10,000 draws.
    Decision role: a GUARD. If C1 also clears M, the effect is not attributable
    to the reaction direction and the Primary is NOT supported.

C2 -- NON-EVENT MATCHED CLOCK (sealed K.2)
    the same trade on non-event days (no CPI, no NFP, no FOMC calendar entry),
    direction = the same construction sign of C(08:31) - C(08:29), reported
    unmatched AND weighted by the same trailing vol terciles, because event
    days are systematically higher-volatility and an unmatched comparison is
    not like-for-like.

    D = mean(Y_net | event) - mean(Y_net | C2, vol-tercile-weighted)
    MECHANISM_SPECIFICITY_ESTABLISHED  <=>  95% lower bound of D > 0

    NON-CONFIRMATORY. It cannot create support; it selects verdict LANGUAGE.
    And even when established it is not causal (sealed K.2).

C2 later serves two separate purposes and this module keeps them apart:
  (1) the mechanism-specificity comparison, which needs the event arm;
  (2) outcome-blind dispersion for the OD-3 power gate, which must NOT.
`c2_dispersion` computes (2) from C2 alone and never accepts an event arm --
see `r1.power_gate`.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from .bars import BarSource
from .contract import SealedContract
from .errors import R1Error
from .signal import build_signal, try_build_signal
from .trade import TradeResult, mean_y_net, run_arm


# --------------------------------------------------------------------------
# C1 -- sign randomized
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class C1Result:
    seed: int
    draws: int
    mean_of_draw_means: float
    draw_means: tuple[float, ...]

    def clears(self, threshold: float) -> bool:
        """Descriptive: the naive 'does the average random arm clear M'."""
        return self.mean_of_draw_means > threshold


def c1_directions(dates, seed: int) -> tuple[int, ...]:
    """One fair-coin direction per event, from a declared seed."""
    rng = random.Random(seed)
    return tuple(rng.choice((1, -1)) for _ in dates)


def run_c1(source: BarSource, dates, contract: SealedContract, *,
           seed: int, draws: int | None = None,
           cost_scenario: str | None = None) -> C1Result:
    """The sign-randomized control. Same days, same minutes, same costs."""
    dates = tuple(dates)
    draws = draws if draws is not None else contract.c1_draws
    scen = cost_scenario or contract.primary_cost_scenario
    rng = random.Random(seed)
    means: list[float] = []
    for _ in range(draws):
        directed = [(d, rng.choice((1, -1))) for d in dates]
        means.append(mean_y_net(run_arm(source, directed, contract,
                                        cost_scenario=scen)))
    return C1Result(seed=seed, draws=draws,
                    mean_of_draw_means=sum(means) / len(means),
                    draw_means=tuple(means))


def assert_c1_invariance(primary: "tuple[TradeResult, ...]",
                         control: "tuple[TradeResult, ...]") -> None:
    """Mechanically check that C1 changed the DIRECTION and nothing else.

    Event eligibility, timing, cost model, exit and sample construction must be
    identical; only `direction` (and therefore the P&L) may differ.
    """
    if len(primary) != len(control):
        raise R1Error("C1 altered the sample size")
    for a, b in zip(primary, control):
        if a.date_et != b.date_et:
            raise R1Error(f"C1 altered the event set at {a.date_et}")
        if a.cost_scenario != b.cost_scenario:
            raise R1Error("C1 altered the cost model")
        if a.entry_ref != b.entry_ref or a.exit_ref != b.exit_ref:
            raise R1Error("C1 altered the entry or exit reference")


# --------------------------------------------------------------------------
# C2 -- non-event matched clock
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class C2Arm:
    results: tuple[TradeResult, ...]
    vol_states: tuple[str | None, ...]

    @property
    def dates(self) -> tuple[str, ...]:
        return tuple(r.date_et for r in self.results)


def non_event_dates(session_dates, event_dates, fomc_dates) -> tuple[str, ...]:
    """Sealed K.2: no CPI, no NFP, no FOMC calendar entry."""
    excluded = set(event_dates) | set(fomc_dates)
    return tuple(d for d in sorted(session_dates) if d not in excluded)


def run_c2(source: BarSource, dates, contract: SealedContract, *,
           vol_states=None, cost_scenario: str | None = None) -> C2Arm:
    """The matched-clock control arm. Same construction sign, same minutes."""
    dates = tuple(dates)
    scen = cost_scenario or contract.primary_cost_scenario
    directed: list[tuple[str, int]] = []
    kept_states: list[str | None] = []
    states = tuple(vol_states) if vol_states is not None else (None,) * len(dates)
    if len(states) != len(dates):
        raise R1Error("vol_states must align with dates")
    for d, st in zip(dates, states):
        sig = try_build_signal(source, d, contract)
        if sig is None or not sig.has_direction:
            continue                      # same NA / no-direction discipline
        directed.append((d, sig.d_event))
        kept_states.append(st)
    return C2Arm(results=run_arm(source, directed, contract,
                                 cost_scenario=scen),
                 vol_states=tuple(kept_states))


def tercile_weights(event_vol_states) -> dict[str, float]:
    """The EVENT distribution over vol terciles -- the weights C2 is held to."""
    states = [s for s in event_vol_states if s is not None]
    if not states:
        raise R1Error("no vol states: C2 cannot be weighted like-for-like")
    out: dict[str, float] = {}
    for s in states:
        out[s] = out.get(s, 0.0) + 1.0
    return {k: v / len(states) for k, v in out.items()}


def weighted_mean(arm: C2Arm, weights: dict[str, float]) -> float:
    """C2's mean reweighted onto the event vol-tercile distribution (K.2)."""
    by_state: dict[str, list[float]] = {}
    for r, s in zip(arm.results, arm.vol_states):
        if s is None:
            continue
        by_state.setdefault(s, []).append(r.y_net_usd)
    if not by_state:
        raise R1Error("C2 carries no vol states; refuse to fake a match")
    usable = {s: w for s, w in weights.items() if s in by_state}
    total = sum(usable.values())
    if total <= 0:
        raise R1Error("no overlapping vol strata between the event arm and C2")
    return sum((w / total) * (sum(by_state[s]) / len(by_state[s]))
               for s, w in usable.items())


def specificity_difference(event_results, c2_arm: C2Arm,
                           event_vol_states) -> float:
    """D = mean(Y_net | event) - mean(Y_net | C2, vol-tercile-weighted)."""
    return (mean_y_net(event_results)
            - weighted_mean(c2_arm, tercile_weights(event_vol_states)))


def c2_dispersion(c2_arm: C2Arm) -> float:
    """OUTCOME-BLIND: the standard deviation of C2's own Y_net. Role (2).

    This function takes ONLY the control arm. It has no parameter through
    which an event-arm object could reach it, which is what keeps the OD-3
    power gate independent of the Primary (see `r1.power_gate`).
    """
    vals = [r.y_net_usd for r in c2_arm.results]
    if len(vals) < 2:
        raise R1Error("dispersion needs at least two control observations")
    mean = sum(vals) / len(vals)
    var = sum((v - mean) ** 2 for v in vals) / (len(vals) - 1)
    return var ** 0.5


def control_direction_for(source: BarSource, date_et: str,
                          contract: SealedContract) -> int:
    """The C2 construction sign -- identical construction to the Primary."""
    return build_signal(source, date_et, contract).d_event
