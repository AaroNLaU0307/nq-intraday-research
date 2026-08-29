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
           "seal_failure_router", "ROUTER_A", "ROUTER_B",
           "STAGE_GATE_OF_BUILDER_CODE", "CALLER_ERROR_BUILDER_CODES",
           "classify_builder_failure", "UNMAPPED_BUILDER_CODES"]


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


#: `build_supplement_from_authority`'s own refusals -> (stage, gate).
#:
#: FOUND BY THE REHEARSAL, 2026-08-29. `run_c_build` classified EVERY
#: builder exception as `row_schema_blind`, on a comment that said "the
#: builder's own refusals are row-schema refusals by construction: it
#: validates the rows it was handed". Walking the chain end to end showed
#: that claim is false -- the builder also validates the AUTHORITY, and a
#: `production_authority_test_only` refusal was being filed as a row-schema
#: defect at the wrong stage.
#:
#: Each mapping is justified by what the raise site actually compares:
STAGE_GATE_OF_BUILDER_CODE = {
    # `type(authority) is not SupplementAuthority` (:259)
    "production_authority_type": ("B_DERIVE", "custody_authority_production"),
    # `authority.test_only` (:264)
    "production_authority_test_only": ("B_DERIVE",
                                       "custody_authority_production"),
    # payload stamped with an id the authority was not minted for (:290)
    "production_supplement_id_divergence": ("B_DERIVE",
                                            "custody_authority_binding"),
}

#: Builder refusals that are CALLER BUGS, not run defects.
#:
#: These fire when code passes a forbidden or unknown keyword. Filing a
#: programming error as a gate failure would put it in the research
#: registry as though a run had failed, so `classify_builder_failure`
#: refuses them instead of naming a gate. A bug is fixed, not recorded.
CALLER_ERROR_BUILDER_CODES = frozenset({
    "production_unknown_argument",
    "production_decisive_argument_supplied",
})


#: Builder refusals that CAN reach a caller and that no ratified gate
#: names. Found 2026-08-29 by widening the derivation to follow calls: the
#: first version scanned only raise sites inside
#: `build_supplement_from_authority` itself, so a code raised one level
#: down escaped both the table and the test that was supposed to police it.
#: The guard was narrower than its claim -- this project's recurring shape.
#:
#: NOT a placeholder to fill in by guessing. BD-1's rule applies: the gate
#: name is written into the F1/F2 row, so picking one puts a defect on
#: record under a name nobody ruled.
UNMAPPED_BUILDER_CODES = {
    "production_payload_unsupported_type":
        "a payload key or value is not exactly a built-in -- a hostile "
        "subclass surviving the freeze (`_freeze_value`). That is an "
        "INTEGRITY defect, not a row-schema one: `row_schema_blind` names "
        "the four structural row fields and the blind guarantee, and this "
        "is about Python types anywhere in the payload, which may have come "
        "from the rows OR from the authority's binding. No C_BUILD gate "
        "names it, and unlike the seal codes there is no post-seal router "
        "to own it either. Needs a ruling: a new gate (an R4-level act on "
        "the approved closed enum), or an assignment to an existing one "
        "with the reasoning written down.",
}


def classify_builder_failure(code: str) -> tuple:
    """(stage, gate) for a `build_supplement_from_authority` refusal.

    Refuses a caller bug, refuses an unmapped-but-known code with its open
    question, and refuses an unknown code. All three refusals are louder
    than a default, because the gate name is what the F1/F2 row carries and
    a defaulted gate writes a defect under a name nobody ruled."""
    if code in UNMAPPED_BUILDER_CODES:
        raise ClassificationError(
            "builder code %r reaches callers but no ratified gate names it. "
            "%s\n\nThis is recorded as UNMAPPED rather than guessed, for "
            "BD-1's reason: a picked gate would put a defect on record "
            "under a name nobody ruled." % (code, UNMAPPED_BUILDER_CODES[code]))
    if code in CALLER_ERROR_BUILDER_CODES:
        raise ClassificationError(
            "builder code %r is a CALLER BUG (a forbidden or unknown "
            "keyword), not a run defect. It has no gate on purpose: filing "
            "a programming error as a gate failure would record a failed "
            "run that never happened. Fix the call site." % code)
    pair = STAGE_GATE_OF_BUILDER_CODE.get(code)
    if pair is None:
        raise ClassificationError(
            "builder code %r is in neither builder table. Add it to "
            "STAGE_GATE_OF_BUILDER_CODE with the raise site that justifies "
            "the (stage, gate), or to CALLER_ERROR_BUILDER_CODES if it is a "
            "programming error." % code)
    return pair


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
