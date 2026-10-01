"""TASK 5 (cost half) -- the pinned cost adapter.

ITSF's frozen S0 SS6 fill formulas and scenario grid, TRANSCRIBED rather than
imported, because importing from a parked working tree would make R1 depend on
mutable state outside its own sealed commit (`r1.itsf_pin` explains the
choice). The transcription is cross-checked numerically against ITSF's own
module in `tests/test_costs.py`, and against the sealed G.2 table here.

    entry_fill      = ref + d * (spread/2 + slip_ticks * TICK)
    timed_exit_fill = ref - d * (spread/2 + slip_ticks * TICK)
    side friction   = friction_multiplier * (spread/2 + ticks * TICK)
    round turn USD  = points_to_usd(entry friction + exit friction)
                      + platform fee, applied EXACTLY ONCE

R1's one deviation from ITSF, and it is a specialisation rather than a change:
the entry minute (08:33) and the exit minute (09:29) have different spread
distributions (sealed E.3), so friction is priced per side. With equal spreads
the two collapse to ITSF's formula exactly -- `tests/test_costs.py` asserts it.
"""
from __future__ import annotations

from .contract import CostScenario, SealedContract
from .errors import R1Error


def _check_d(d: int) -> None:
    if d not in (1, -1):
        raise R1Error(f"direction d must be +1 or -1, got {d!r}")


def points_to_usd(points: float, contract: SealedContract) -> float:
    return points * contract.point_value_usd


def scenario(contract: SealedContract, name: str) -> CostScenario:
    try:
        return contract.cost_scenarios[name]
    except KeyError as exc:
        raise R1Error(f"unknown cost scenario {name!r}; the sealed grid is "
                      f"{sorted(contract.cost_scenarios)}") from exc


def side_friction_points(contract: SealedContract, name: str,
                         side: str) -> float:
    """Per-side market friction in points. `side` is 'entry' or 'exit'."""
    scn = scenario(contract, name)
    if side == "entry":
        spread = scn.entry_spread_points
    elif side == "exit":
        spread = scn.exit_spread_points
    else:
        raise R1Error(f"side must be 'entry' or 'exit', got {side!r}")
    return scn.friction_multiplier * (
        spread / 2.0 + scn.slippage_ticks_per_side * contract.tick_points)


def entry_fill(ref: float, d: int, contract: SealedContract,
               name: str) -> float:
    """Signed entry fill in points. Frozen S0 SS6."""
    _check_d(d)
    return ref + d * side_friction_points(contract, name, "entry")


def timed_exit_fill(ref: float, d: int, contract: SealedContract,
                    name: str) -> float:
    """Signed timed-exit fill in points. Frozen S0 SS6.

    R1's Primary has NO STOP (sealed C.1, R.2), so there is no stop-fill path
    here at all. That is deliberate: a stop would introduce a parameter and an
    optimisation surface the sealed design refuses to have.
    """
    _check_d(d)
    return ref - d * side_friction_points(contract, name, "exit")


def round_turn_cost_usd(contract: SealedContract, name: str) -> float:
    """Per-contract round-turn cost in USD: friction both sides + fee once."""
    scn = scenario(contract, name)
    friction = (side_friction_points(contract, name, "entry")
                + side_friction_points(contract, name, "exit"))
    return points_to_usd(friction, contract) + scn.platform_fee_rt_usd


def all_round_turn_costs_usd(contract: SealedContract) -> dict[str, float]:
    return {name: round_turn_cost_usd(contract, name)
            for name in contract.cost_scenarios}
