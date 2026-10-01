"""Which worlds the conditional-aleatoric report fixes — M11, as ratified.

WHAT WAS MISSING. MC §5 says the conditional aleatoric layer reports "the
distribution of M account paths WITHIN A FIXED WORLD" and never says which
world. Until now the consumer refused to choose: the caller had to NAME a
world, and `test_no_fixed_world_selection_rule_was_invented` stood guard so
that nobody quietly invented a rule and passed it off as frozen.

THE RULING (M11, 2026-08-24, delegated to Codex GPT-5.6 Sol under Aaron's
named batch delegation, over a Fable 5 proposal). `DELEGATED=YES`.

Three worlds, by ORDER STATISTIC on the world-mean monthly prop_operating
EV, ascending: positions ceil(0.05B), ceil(0.5B), ceil(0.95B), 1-indexed.
At B=1000 that is the 50th, 500th and 950th. Ties resolve to the lower
world index, so the rule is total and leaves no discretion anywhere.

WHY NOT A SINGLE PRE-REGISTERED WORLD. S0-T001 is already unblinded, so
naming one world now is a choice made with the results in hand and is
exactly the kind of thing that cannot be defended at N17. An order
statistic names no world; it names a position.

WHY NOT ALL B WORLDS. The conditional aleatoric layer is frozen as
reporting that never gates GO, and B=1000 slices multiply the sealed bytes
and the custody minutes for a diagnostic. Any slice can be recovered from
the sealed handoff by cold replay afterwards; the reverse is not true.

WHY "NEIGHBOURHOOD" IS AN ORDER STATISTIC AND NOT A DISTANCE. A distance
metric would be one more free parameter nobody ratified. A position is
exact.

THE GUARD DID NOT GO AWAY, IT INVERTED. It used to assert that no selection
rule existed. It now asserts that THIS rule exists and that it is the only
one — and specifically that the consumer boundary still refuses to choose,
because the selection happens here and travels as an explicit world index.
A guard left asserting "no rule" while a ratified rule lives one module
away would pass forever and protect nothing.
"""
from __future__ import annotations

import math

__all__ = ["FIXED_WORLD_RULING", "FIXED_WORLD_QUANTILES",
           "select_fixed_worlds", "FixedWorldError"]


class FixedWorldError(ValueError):
    def __init__(self, code: str, detail: str = ""):
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code


FIXED_WORLD_RULING = "M11_RATIFIED_2026-08-24"
FIXED_WORLD_RULING_DELEGATED = True

#: The three ratified positions, as fractions. 1-indexed after ceil().
#: These are the whole of the rule: change one and the report changes.
FIXED_WORLD_QUANTILES = (0.05, 0.50, 0.95)


def select_fixed_worlds(world_means) -> tuple:
    """The three world indices, low -> mid -> high by world-mean EV.

    `world_means[i]` is world i's mean monthly prop_operating EV, ordered
    by world index — the shape `ObservationSet.world_means()` returns.

    Returns world INDICES, not positions: the caller passes them to
    `run_conditional_aleatoric(world_index=...)`, which still refuses to
    choose for itself."""
    means = tuple(world_means)
    b = len(means)
    if b == 0:
        raise FixedWorldError("fixed_world_no_worlds",
                              "no world means to order")
    # ascending by mean, ties to the LOWER world index -- (mean, index)
    # sorts on the index only when the means are equal, which is what
    # makes the rule total rather than leaving a tie to chance.
    order = sorted(range(b), key=lambda i: (means[i], i))
    picked = []
    for q in FIXED_WORLD_QUANTILES:
        pos = math.ceil(q * b)          # 1-indexed position
        pos = min(max(pos, 1), b)       # a tiny B must not index outside
        picked.append(order[pos - 1])
    return tuple(picked)
