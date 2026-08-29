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


# ===========================================================================
# The SEAL step's refusals
# ===========================================================================
#
# `seal_supplement_production` refuses in two ways: its own drift checks,
# and whatever `resolve_partial` raises underneath it. Both need a gate
# name, and the gate names the DEFECT — not the moment it was noticed. A
# rows defect found at seal time is still a rows defect.
#
# THE STAGE MATTERS TOO, and this is why the table carries pairs. Two of
# the seal's drift checks are about the AUTHORITY, and the ratified gate
# table puts those in B_DERIVE, not C_BUILD:
#
#     B_DERIVE  custody_authority_production · custody_authority_binding ·
#               source_bundle_digest · day_universe_identity ·
#               method_version_pinned
#
# Reading them off the raise sites rather than off their names:

#: Seal refusal code -> (stage, gate). Each mapping is justified by what
#: the raise site actually compares, cited by line.
STAGE_GATE_OF_SEAL_CODE = {
    # "the payload binding is not the one the authority derives" (:412)
    "production_binding_drift": ("B_DERIVE", "custody_authority_binding"),
    # "day-universe digest moved" (:414)
    "production_day_universe_drift": ("B_DERIVE", "day_universe_identity"),
    # `got_days != authority.expected_day_set`, missing/extra (:418)
    "production_day_set_drift": ("C_BUILD", "day_set_exact"),
    # `declared["rows_digest"] != canonical_rows_digest(rows)` (:424)
    "production_rows_digest_drift": ("C_BUILD", "rows_digest_recompute"),
    # the seal's own comment: "a forbidden row field IS the blind-guarantee
    # violation and deserves its own name" (:440)
    "production_forbidden_row_field": ("C_BUILD", "row_schema_blind"),
    # `resolve_partial`'s outcomes ARE the staging outcome, so these are
    # the one group whose gate is settled by what they are.
    "supplement_seal_conflict": ("C_BUILD", "seal_staging_partial"),
    "supplement_partial_verify": ("C_BUILD", "seal_staging_partial"),
    "supplement_post_promotion_verify": ("C_BUILD", "seal_staging_partial"),
    "divergent_partial_exists": ("C_BUILD", "seal_staging_partial"),
    "incident_id_malformed": ("C_BUILD", "seal_staging_partial"),
}

#: Codes whose gate the ratified table does NOT settle, with the question.
#:
#: NOT a placeholder to fill in later by guessing. `classify_seal_failure`
#: refuses these LOUDLY, because a code arriving under a gate someone
#: picked would write that gate's name into the F1/F2 event — and the
#: event is what the registry keeps.
UNDECIDED_SEAL_CODES = {
    "production_supplement_object_invalid":
        "the SUPPLEMENT OBJECT's field set is wrong (:403). C_BUILD's only "
        "schema gate is `row_schema_blind`, and this is not a row. Does the "
        "supplement object's schema belong to that gate, or is a C_BUILD "
        "gate missing?",
    "production_payload_drift":
        "the declared payload is not what the authority and these rows "
        "rebuild to (:456). That is a whole-payload consistency claim; no "
        "C_BUILD gate names it and no B_DERIVE gate does either.",
}


def classify_seal_failure(code: str) -> tuple:
    """(stage, gate) for a seal refusal, or a loud refusal.

    Returns a PAIR because two of the seal's checks belong to B_DERIVE.
    Classifying them into C_BUILD would put the right defect under the
    wrong stage, and the stage is half of what the failure event carries."""
    if code in UNDECIDED_SEAL_CODES:
        raise ClassificationError(
            "seal code %r has no ratified gate. %s\n\nThis is recorded as "
            "UNDECIDED rather than guessed: the gate name is written into "
            "the F1/F2 event, so a picked gate would put a defect on "
            "record under a name nobody ruled."
            % (code, UNDECIDED_SEAL_CODES[code]))
    pair = STAGE_GATE_OF_SEAL_CODE.get(code)
    if pair is None:
        raise ClassificationError(
            "seal code %r is in neither table. Add it to "
            "STAGE_GATE_OF_SEAL_CODE with the raise site that justifies "
            "the gate, or to UNDECIDED_SEAL_CODES with the question." % code)
    return pair
