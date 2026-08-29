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
           "ClassificationError", "STAGE_GATE_OF_SEAL_CODE",
           "classify_seal_failure", "ROUTER_B_SEAL_CODES",
           "seal_failure_router", "ROUTER_A", "ROUTER_B"]


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

#: RULED 2026-08-29, `ops/BUILDER_DECISIONS_2026-08-29.md` BD-1. These two
#: were `UNDECIDED_SEAL_CODES`; they are now decided, and the decision is
#: that THEY GET NO GATE.
#:
#: They are seal-step failures, and the outcome of a failed seal is already
#: owned by Router B, which has a defined answer for it:
#:
#:     local_seal_ok=False -> decide_after_seal -> `local_seal_failed`
#:                            "no P4 and no A1: nothing was sealed"
#:
#: WHY NOT PICK A GATE. `archive_policy_a` is the executed precedent, not a
#: hypothesis: it IS a C_BUILD gate, and routing it as an ordinary gate
#: sends it through Router A to F2 while ratified
#: `ND1_ARCHIVE_FAILURE_POLICY=A` requires A1.
#: `test_routing_it_as_an_ordinary_gate_contradicts_policy_a` runs that
#: contradiction. `ROUTER_OF` resolved it by giving Router B the outcome.
#: This is the same shape, so it takes the same resolution.
#:
#: And no existing gate says either thing: `row_schema_blind` is about
#: ROWS, while a supplement object is the container. Stretching a row gate
#: over a container is the "the guard is narrower than its claim" defect
#: this project has now produced eight times. Adding a gate is not
#: available either -- `GATE_TABLE` is an approved closed enum and editing
#: it is an R4-level act.
ROUTER_B_SEAL_CODES = {
    "production_supplement_object_invalid":
        "the SUPPLEMENT OBJECT's field set is wrong (:403). Not a row, so "
        "`row_schema_blind` does not name it; the seal did not complete, so "
        "Router B does.",
    "production_payload_drift":
        "the declared payload is not what the authority and these rows "
        "rebuild to (:456). A whole-payload consistency claim that no gate "
        "names, raised while sealing, so Router B owns the outcome.",
}

#: Which router decides what a seal refusal becomes. Mirrors
#: `supplement_contract.ROUTER_GATE_FAILURE` / `ROUTER_POST_SEAL`.
ROUTER_A = "A"      # plan_failure_event: F1 or F2 by the P3 boundary
ROUTER_B = "B"      # decide_after_seal: P4, A1, or a refused seal


def seal_failure_router(code: str) -> str:
    """Which router owns this seal refusal's outcome. Refuses the unknown.

    The whole point of BD-1: an unmapped code must not silently acquire a
    router any more than it may silently acquire a gate."""
    if code in ROUTER_B_SEAL_CODES:
        return ROUTER_B
    if code in STAGE_GATE_OF_SEAL_CODE:
        return ROUTER_A
    raise ClassificationError(
        "seal code %r is in neither table, so no router owns it. Add it to "
        "STAGE_GATE_OF_SEAL_CODE with the raise site that justifies the "
        "gate, or to ROUTER_B_SEAL_CODES with the reason no gate names it."
        % code)


def classify_seal_failure(code: str) -> tuple:
    """(stage, gate) for a seal refusal, or a loud refusal.

    Returns a PAIR because two of the seal's checks belong to B_DERIVE.
    Classifying them into C_BUILD would put the right defect under the
    wrong stage, and the stage is half of what the failure event carries."""
    if code in ROUTER_B_SEAL_CODES:
        raise ClassificationError(
            "seal code %r has no gate, and that is the RULING (BD-1), not "
            "an open question. %s\n\nRouter B owns this outcome: call "
            "`supplement_runner.decide_after_seal(local_seal_ok=False, ...)`, "
            "which answers `local_seal_failed` -- no P4 and no A1. Routing "
            "it through a gate would send it to Router A's F1/F2, the exact "
            "contradiction `archive_policy_a` was found to create."
            % (code, ROUTER_B_SEAL_CODES[code]))
    pair = STAGE_GATE_OF_SEAL_CODE.get(code)
    if pair is None:
        raise ClassificationError(
            "seal code %r is in neither table. Add it to "
            "STAGE_GATE_OF_SEAL_CODE with the raise site that justifies "
            "the gate, or to ROUTER_B_SEAL_CODES with the reason no gate "
            "names it (BD-1)." % code)
    return pair
