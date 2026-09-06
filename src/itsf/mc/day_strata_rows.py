"""The day-strata ROW PRODUCER — N09 R3 §4's pinned call graph, and nothing else.

WHAT WAS MISSING. Everything else the supplement needs already existed:
`day_strata_supplement` validates and digests rows, `supplement_production`
builds the product from an authority, mints the receipt and seals it. What
had never been written is the step that PRODUCES the rows, and R3 §4 pins
its call graph byte for byte because getting it wrong crosses the
supplement's structural-only boundary:

    itsf.data.dbn_loader : DevelopmentSignalLoader.load_real -> bars_by_date
    itsf.s0.context      : build_universe(...)               -> S0Universe
    itsf.s0.dataset      : build_vol20_regime_mapping_from_universe(
                             universe, method)   # eligible population,
                             then projected onto the sealed day set
    itsf.s0.dataset      : build_event_stratum_map(...)
    => row = ROW_FIELDS = ("trade_date", "year", "vol_stratum",
                           "event_stratum")

FORBIDDEN, and mechanically so (`tests/test_n09_scaffold_criteria.py`
scans every module in this package): `build_s0_dataset`, `compute_day`,
`iter_day_contexts`, any label, Oracle or study construction, and
`RealChain._ensure`. Each of those computes LABELS; a supplement that
touched one would stop being structural-only.

THIS MODULE READS NOTHING. It takes an assembled universe and the event
flags as arguments. The real-data acquisition — `load_real` — sits behind
`assert_real_run_allowed` in the runner and is NOT called from here: a
producer that opened Development data would put a second real-data read
into a module the authorization gate does not guard.

NO STRATIFICATION LOGIC OF ITS OWN. R3 §4: "生产者自身不得携带任何分层逻辑".
Every stratum value is read out of a mapping the ruled S0 functions
returned. This module decides nothing about what T1 or `NA_multi_event`
mean; it transcribes.

VOCABULARY IS COMPARED BY SET, NEVER BY ORDER. Measured, and R3 §4 says so
explicitly because the two orders differ:

    itsf.s0.dataset.EVENT_STRATA           ('CPI','NFP','FOMC','none','NA_multi_event')
    itsf.mc.day_strata_supplement.EVENT_STRATA
                                           ('CPI','FOMC','NFP','NA_multi_event','none')

An order comparison here would fail on identical vocabularies.
"""

from __future__ import annotations

from typing import Mapping, Sequence

from . import day_strata_supplement as ds

__all__ = ["DayStrataRowsError", "derive_day_strata_rows",
           "assert_vocabularies_agree"]


class DayStrataRowsError(Exception):
    """Raised when the producer will not emit rows. Refuses; never repairs."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}" if detail else code)


def assert_vocabularies_agree() -> None:
    """The two packages' strata vocabularies must be the SAME SETS.

    Called before any row is built, because a vocabulary drift makes every
    row's `vol_stratum` / `event_stratum` a value the supplement's own
    validator would later refuse — and refusing there would name the wrong
    defect. R3 §4 requires the comparison be by set: the orders differ
    today and that is not a defect."""
    from ..s0 import dataset as _s0

    if set(_s0.VOL_ALL_LABELS) != set(ds.VOL_STRATA):
        raise DayStrataRowsError(
            "vol_vocabulary_drift",
            f"s0 {sorted(_s0.VOL_ALL_LABELS)} != mc {sorted(ds.VOL_STRATA)}")
    if set(_s0.EVENT_STRATA) != set(ds.EVENT_STRATA):
        raise DayStrataRowsError(
            "event_vocabulary_drift",
            f"s0 {sorted(_s0.EVENT_STRATA)} != mc {sorted(ds.EVENT_STRATA)}")


def derive_day_strata_rows(*, universe, vol_method: str,
                           flag_by_date: Mapping,
                           event_na_mapping: str,
                           expected_day_set: frozenset) -> list[dict]:
    """One row per day of the SEALED day universe, in R3 §4's call graph.

    `expected_day_set` is the already-sealed universe carried over from the
    S0 authority, and it is the OUTPUT row population: one row per day of
    it, no more and no fewer.

    THE EVENT MAPPING is compared against it EXACTLY and day-by-day — R3 §4:
    "对 `authority.expected_day_set` 做逐日精确相等对拍（不是覆盖，不是包含）".
    A missing day and an invented day are separate refusals there, because
    they are different defects: the first means the producer lost a day, the
    second means it invented one.

    THE VOL MAPPING is compared by COVERAGE, not equality, and that is the
    2026-09-06 repair rather than a relaxation: its population is now the
    structurally eligible sample S0-T001 cut its terciles over, which is a
    deliberate superset of the sealed set. Only a sealed day the population
    fails to cover is still a defect. See the call site below.

    Rows come back sorted by `trade_date` so the digest is independent of
    the order the mappings happened to iterate in.
    """
    from ..s0 import dataset as _s0

    assert_vocabularies_agree()

    if not isinstance(expected_day_set, frozenset):
        raise DayStrataRowsError(
            "expected_day_set_not_frozenset",
            f"{type(expected_day_set).__name__} — the sealed day universe "
            "must arrive as a frozenset, exactly as the supplement builder "
            "requires it")
    if not expected_day_set:
        raise DayStrataRowsError(
            "expected_day_set_empty",
            "an empty sealed universe would make every conservation check "
            "below pass over nothing")

    days = sorted(expected_day_set)

    # THE VOL THRESHOLD POPULATION IS NOT THE OUTPUT ROW POPULATION, and
    # conflating them is the defect the strict-blind MC-DS-S003 verification
    # proved. `build_vol20_regime_mapping` computes the two tercile cut
    # points ONCE over exactly the `days` it is handed -- its own docstring
    # says "the FULL Development sample day set to label (every structurally
    # eligible day)" and `tercile_reference` ruled that population. This
    # producer used to hand it `sorted(expected_day_set)`: the SEALED OUTPUT
    # set. A narrower sample moves the quantiles, so days sitting near a cut
    # got a different tercile than the run being reconstructed had given
    # them -- a silent relabelling, invisible to every conservation check
    # because the labels were internally consistent either way.
    #
    # The repair is to call the primitive the way S0-T001 itself calls it
    # (`scripts/s0_real_run.py`: the mapping is built from the universe with
    # NO `days` argument, so it defaults to the structurally eligible
    # population) and then PROJECT the resulting labels onto the sealed
    # output set. Omitting the argument rather than naming the population
    # again is deliberate: one expression of "which population", in the
    # ruled function, shared by both callers.
    vol = _s0.build_vol20_regime_mapping_from_universe(universe, vol_method)
    events = _s0.build_event_stratum_map(flag_by_date, event_na_mapping)

    # BOTH MAPPINGS' SHAPES FIRST, then their contents. Grouping them is
    # not cosmetic: a malformed event mapping and an incomplete vol
    # population are independent defects, and whichever check runs first
    # decides which one gets NAMED. Shape before content means a mapping
    # that is not a mapping is always reported as that, never as a
    # consequence of the other axis being examined first.
    population = getattr(vol, "label_of", None)
    if not isinstance(population, Mapping):
        raise DayStrataRowsError(
            "vol_mapping_shape",
            "the ruled vol mapping exposes no `label_of` mapping")
    stratum_of = events.get("stratum_of")
    if not isinstance(stratum_of, Mapping):
        raise DayStrataRowsError(
            "event_mapping_shape",
            "the ruled event map exposes no `stratum_of` mapping")

    # COVERAGE, not exact equality -- and the difference matters. The
    # threshold population is a SUPERSET of the sealed output set by design
    # now, so a day in the population that is not in the sealed set is no
    # longer a defect on this axis: that is what widening the population
    # MEANS. Only the missing direction can still be one, and it is checked
    # HERE rather than after the projection, because a projection onto the
    # sealed set has that set as its key set BY CONSTRUCTION -- an exact-set
    # assertion after it could never fail, which is the vacuous-guard shape
    # this project keeps finding. The code is unchanged (`vol_day_missing`)
    # because the defect it names is unchanged: the vol mapping does not
    # cover a day the seal requires.
    missing = sorted(expected_day_set - frozenset(population))
    if missing:
        raise DayStrataRowsError(
            "vol_day_missing",
            f"{len(missing)} sealed day(s) absent from the vol population, "
            f"first {missing[:3]}")
    label_of = {day: population[day] for day in days}

    _assert_day_by_day(expected_day_set, frozenset(stratum_of), "event")

    rows = []
    for day in days:
        vol_stratum = label_of[day]
        event_stratum = stratum_of[day]
        if vol_stratum not in ds.VOL_STRATA:
            raise DayStrataRowsError(
                "vol_stratum_outside_vocabulary", f"{day}: {vol_stratum!r}")
        if event_stratum not in ds.EVENT_STRATA:
            raise DayStrataRowsError(
                "event_stratum_outside_vocabulary",
                f"{day}: {event_stratum!r}")
        rows.append({
            "trade_date": day,
            "year": _year_of(day),
            "vol_stratum": vol_stratum,
            "event_stratum": event_stratum,
        })
    return rows


def _year_of(day: str) -> int:
    """`YYYY-MM-DD` -> `YYYY`, refusing anything else.

    Not `int(day[:4])`: that silently accepts `20xy-...` as a year by
    reading four characters that were never checked to be digits, and this
    value lands in the sealed bytes."""
    if not ds._ISO_DATE.match(day or ""):
        raise DayStrataRowsError("trade_date_malformed", repr(day))
    return int(day[:4])


def _assert_day_by_day(expected: frozenset, produced: frozenset,
                       which: str) -> None:
    """Exact set equality, with the two directions reported separately."""
    missing = sorted(expected - produced)
    invented = sorted(produced - expected)
    if missing:
        raise DayStrataRowsError(
            f"{which}_day_missing",
            f"{len(missing)} sealed day(s) absent from the {which} mapping, "
            f"first {missing[:3]}")
    if invented:
        raise DayStrataRowsError(
            f"{which}_day_invented",
            f"{len(invented)} day(s) in the {which} mapping are outside the "
            f"sealed universe, first {invented[:3]}")
