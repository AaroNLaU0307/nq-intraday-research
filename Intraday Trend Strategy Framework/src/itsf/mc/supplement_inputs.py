"""Assemble the chain's four inputs from bars -- and never load the bars.

THE LAST LAYER BEFORE THE REAL-DATA BOUNDARY, and the same split as the four
before it: this RECEIVES `bars_by_date` and never opens a file. Loading real
bars is `itsf.data.dbn_loader.DevelopmentSignalLoader.load_real`, which is
gate-first by construction (`assert_real_run_allowed` before any open, then a
data-role check, then a manifest verification). Nothing here weakens that,
and nothing here can reach it.

SO THE BOUNDARY IS EXACTLY ONE STEP WIDE. Everything from bars onward --
`build_universe`, the day contexts, the ruled method values -- is pure and
runs today over synthetic bars. The only thing an authorization has to open
is the bars themselves.

THE RULED VALUES ARE READ, NOT WRITTEN DOWN HERE. `vol_method` and
`event_na_mapping` come from `contracts.aaron_ruled_methods()`. Copying their
current values into literals would work today and drift silently the first
time the ratified spec moved -- the same "a sentence that was true when
written" defect this package keeps meeting.

AND `vol_method` IS AN OBJECT, NOT A STRING. `_validate_vol_method` compares
six of its fields against the ruled values and refuses anything else, so a
producer cannot quietly publish a different statistic under the same name.
Worth stating because `supplement_chain` annotated it `str` and passed
"vol20" in its tests for a day: the tests mock the consumer, so nothing
objected. The annotation is corrected and this module hands over the real
object.
"""
from __future__ import annotations

import dataclasses as _dc
from typing import Mapping

__all__ = ["ChainInputs", "ruled_methods", "assemble_chain_inputs"]


@_dc.dataclass(frozen=True, slots=True)
class ChainInputs:
    """Exactly what `run_supplement_chain` needs, and nothing else."""
    universe: object
    vol_method: object              # a VolatilityRegimeMethod, never a str
    flag_by_date: Mapping
    event_na_mapping: str


def ruled_methods():
    """`(vol_method, event_na_mapping)` as the ratified spec carries them."""
    from .. import contracts as _c

    methods = _c.aaron_ruled_methods()
    return methods.volatility_regime, methods.event_na_mapping


def assemble_chain_inputs(*, bars_by_date: Mapping, schedule, events,
                          expected_day_set: frozenset,
                          roll_intervals=()) -> ChainInputs:
    """Build the universe and the per-day event flags from bars already in
    hand, SCOPED to the sealed day universe.

    `bars_by_date` and `expected_day_set` are REQUIRED with no defaults, for
    the same reason `prepared` and `outcome` are in the layers below: a
    default would let a caller omit one and leave this module to find it.

    WHY THE SCOPING, AND WHY IT HIDES NOTHING. `derive_day_strata_rows`
    compares the event mapping to the sealed universe by EXACT set equality.
    An unscoped mapping carries every structurally eligible day the market
    produced -- measured here: 36 eligible days against a 5-day sealed set --
    and refuses with `event_day_invented`, correctly. Scoping is therefore
    the caller's job and this is the caller.

    It cannot mask the opposite defect. `_assert_day_by_day` reports BOTH
    directions, so a sealed day the universe does not contain simply never
    enters the mapping and arrives at the gate as `event_day_missing`.
    Refusing here as well would be a second implementation of one invariant,
    which is the R2 defect this package already paid for once.

    Pure. It opens nothing, writes nothing, and creates no directory --
    asserted rather than claimed, in `test_supplement_inputs.py`.
    """
    from ..s0.context import build_universe

    universe = build_universe(bars_by_date, schedule, events, roll_intervals)
    sealed = frozenset(expected_day_set)
    # `encode_f10`, NOT `iter_day_contexts`. The first draft walked day
    # contexts and read `ctx.event_flag`, and
    # `test_no_module_in_the_package_reaches_a_forbidden_name` refused it:
    # `iter_day_contexts` is on the S0 dataset assembly path, which reaches
    # label computation, and the supplement is STRUCTURAL-ONLY. That guard
    # had been widened from two named files to the whole package precisely
    # so a new module like this one could not cross the boundary quietly.
    #
    # The value is identical -- `build_day_context` sets
    # `event_flag=universe.events.encode_f10(date)` (:1051) -- and this way
    # gets it from the injected event calendar alone: no bars, no contexts,
    # no labels.
    flag_by_date = {day: universe.events.encode_f10(day)
                    for day in universe.funnel.structurally_eligible
                    if day in sealed}
    vol_method, event_na_mapping = ruled_methods()
    return ChainInputs(universe, vol_method, flag_by_date, event_na_mapping)
