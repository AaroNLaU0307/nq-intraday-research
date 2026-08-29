"""C_BUILD's gates as CLASSIFIERS of the producer's outcome.

R3 §3's gate doctrine, and the reason this module is thin: a gate
classifies the outcome of a call; it does not observe inside the call and
does not implement a second copy of the invariant. `_g_row_schema_blind`
says so in its own comment — "the blind guarantee is enforced row-by-row by
`day_strata_supplement._validate_row`; this gate exists so the failure has
a NAMED stage/gate in the F1/F2 vocabulary".

So the mechanism refuses, and this maps its refusal onto the ratified
(stage, gate) vocabulary. Writing the checks again HERE would be the R2
mistake in a new place: two implementations of one invariant, drifting.

WHY A TABLE AND NOT A CHAIN OF `if`s. An unmapped code must be a LOUD
failure, not a fall-through to some default gate. `classify` refuses on an
unknown code, and `test_every_producer_code_has_exactly_one_gate` pins that
every code the producer can raise is in the table — derived from the
producer's source, not from a list someone remembered to update.

NOTHING HERE RUNS A SUPPLEMENT. It maps error codes. The production entry
stays refused at `assert_real_run_allowed`, and this module neither reads
Development data, creates a directory, nor appends a registry row.
"""

from __future__ import annotations

from . import day_strata_rows as dsr

__all__ = ["GATE_OF_PRODUCER_CODE", "classify_producer_failure",
           "ClassificationError"]


class ClassificationError(Exception):
    """A producer code with no gate. Refuses rather than guessing one."""


#: Producer refusal code -> the C_BUILD gate that names it.
#:
#: The three C_BUILD_1 gates partition the producer's failure modes:
#:
#:   row_schema_blind       a ROW is not what a row must be — its date, its
#:                          stratum values, the vocabulary they come from
#:   day_set_exact          the DAY UNIVERSE does not match the sealed one
#:   rows_digest_recompute  the digest does not reproduce
#:
#: `expected_day_set_*` belong to `day_set_exact`: a universe that is not a
#: frozenset, or is empty, is a defect in the day universe the caller
#: supplied, not in any row.
GATE_OF_PRODUCER_CODE = {
    "trade_date_malformed": "row_schema_blind",
    "vol_stratum_outside_vocabulary": "row_schema_blind",
    "event_stratum_outside_vocabulary": "row_schema_blind",
    "vol_vocabulary_drift": "row_schema_blind",
    "event_vocabulary_drift": "row_schema_blind",
    "vol_mapping_shape": "row_schema_blind",
    "event_mapping_shape": "row_schema_blind",
    "vol_day_missing": "day_set_exact",
    "vol_day_invented": "day_set_exact",
    "event_day_missing": "day_set_exact",
    "event_day_invented": "day_set_exact",
    "expected_day_set_not_frozenset": "day_set_exact",
    "expected_day_set_empty": "day_set_exact",
}


def classify_producer_failure(exc: dsr.DayStrataRowsError) -> str:
    """The C_BUILD gate that names this refusal.

    Refuses an unknown code rather than defaulting. A default would let a
    new producer refusal arrive under someone else's gate name, and the
    gate name is what the F1/F2 event carries — so the registry would
    record the wrong defect."""
    if not isinstance(exc, dsr.DayStrataRowsError):
        raise ClassificationError(
            "not a producer refusal: %s" % type(exc).__name__)
    gate = GATE_OF_PRODUCER_CODE.get(exc.code)
    if gate is None:
        raise ClassificationError(
            "producer code %r has no gate. Add it to "
            "GATE_OF_PRODUCER_CODE — do NOT let it fall through to a "
            "default, because the gate name is what the failure event "
            "carries." % exc.code)
    return gate
