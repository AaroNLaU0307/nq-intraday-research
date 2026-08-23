"""Ratified N-D1 supplement vocabulary — the ONE declaration in code.

MAIN-AGENT OWNED. Read-only for the N03 (authority) and N05 (registry)
lanes: both import from here, neither edits it. Interface change requests
go back to the main agent, never applied in place by a lane.

WHAT MAKES THIS AUTHORITATIVE. Every token, row class, commit width,
required-field list and permitted transition below is transcribed from
the RATIFIED governance text — `ops/DECISION_PACKET_N00_AND_ND1.md`
§D.3.1/§D.3.2/§D.3.3/§D.3.5/§D.3.7 as approved by Aaron under
`ND1_RECOMMENDED_PROFILE_R2` (sha256 a3d40b7c…, ratified 2026-08-23,
bound to doc head c56286b…), which corrected R1's two P3
contradictions and is the profile the P3 edges below now rest on.
R1 (sha256 0a08319a…, bound to doc head
803d991…, recorded verbatim in `ops/ND1_PROFILE_RATIFICATION.md`).
`tests/test_mc_supplement_integration.py` re-derives the token set from
that document at test time and asserts equality with this module, so a
rename here goes RED against the governance text rather than silently
redefining what a sealed registry row means.

NOT IMPLEMENTED, DELIBERATELY. `P6` / `SUPPLEMENT_CONSUMED_BY_GRID_REPLAY`,
the `MC-R001` family and every other MC batch-2 event are N-D3 business
(§D.3.4). They are named in `ND3_DEFERRED_TOKENS` ONLY so the parser can
refuse them BY NAME instead of falling through an unknown-token branch.

NOTHING HERE AUTHORIZES ANYTHING. Ratifying the grammar is not
authorizing a run (`ops/ND1_PROFILE_RATIFICATION.md` §4).
"""
from __future__ import annotations

import re
from types import MappingProxyType
from typing import Mapping

# ---------------------------------------------------------------------------
# §D.3.1 global format rules (the profile ratified these as format-only)
# ---------------------------------------------------------------------------

#: `SUPPLEMENT_ID_PATTERN` (§D.3.1). The id namespace is CLOSED: three
#: digits, never reused once a run has started (`ID_REUSE_POLICY=
#: NEVER_AFTER_START`, derived in `ND1_PROFILE_RATIFICATION.md` §6).
#: Anchored with \\Z, NOT $. Python's $ also matches immediately
#: BEFORE a trailing newline, so "MC-DS-S001\\n" satisfied the id
#: grammar and the newline then travelled into a planned directory
#: name. An independent adversarial battery against the N06 repair
#: found it; EVERY anchored pattern in this module and in
#: `supplement_runner` was swept for the same defect, not just the one
#: that was reported (session-conventions §10: fixing an instance does
#: not sweep the class).
SUPPLEMENT_ID_PATTERN = re.compile(r"^MC-DS-S[0-9]{3}\Z")
FIRST_SUPPLEMENT_ID = "MC-DS-S001"

#: Row classes. A NUMBERED row consumes the EXISTING global registry
#: sequence (profile: `ND1_SUPPLEMENT_SEQUENCE_NAMESPACE=GLOBAL`); an
#: UNNUMBERED row is a runner-emitted `+` row and consumes no number.
NUMBERED = "NUMBERED"
UNNUMBERED = "UNNUMBERED"
UNNUMBERED_SEQ_TOKEN = "+"

#: `COMMIT_WIDTH_BY_ROW_CLASS` (§D.3.1): governance rows carry the full
#: 40-hex; runner rows carry the 7-hex short hash, mirroring the existing
#: S0 chain (registry rows 6/9/13 vs the `+` rows beneath them).
COMMIT_WIDTH = MappingProxyType({NUMBERED: 40, UNNUMBERED: 7})
HEX40_RE = re.compile(r"^[0-9a-f]{40}\Z")
HEX7_RE = re.compile(r"^[0-9a-f]{7}\Z")
HEX64_RE = re.compile(r"^[0-9a-f]{64}\Z")
INCIDENT_RE = re.compile(r"^INC-[0-9a-f]{12}\Z")
REASON_CODE_RE = re.compile(r"^[A-Z0-9_]+\Z")

#: Six-cell row contract, from the EXISTING parser
#: (`scripts/s0_real_run.py::parse_registry_events`). Restated here so the
#: supplement parser is pinned to the same shape rather than inventing one.
ROW_CELLS = ("seq", "utc", "event", "commit", "actor", "note")

# ---------------------------------------------------------------------------
# §D.3.2 event vocabulary
# ---------------------------------------------------------------------------

#: Stage vocabulary carried by F1 and F2. CLOSED (§D.3.2 F1
#: `STAGE_ENUM`). Which of F1/F2 a failure becomes is decided by the P3
#: boundary at resolution time, NEVER by the stage name.
STAGE_ENUM = ("A_PRECHECK", "B_DERIVE", "C_BUILD")

#: `F1_GATE_NAME_ENUM` — §D.3.2 left this as "CLOSED, to be fixed with the
#: N04 runner; empty set until then, and an undefined gate may not be
#: emitted". This IS that closure. The runner builds its gate callables
#: from this table and `tests/test_mc_supplement_runner.py` asserts the
#: implemented set equals it exactly, so the enum stays MECHANICALLY
#: DERIVED from real gates instead of being an aspirational list.
GATE_TABLE: Mapping[str, tuple] = MappingProxyType({
    "A_PRECHECK": (
        "g9_hard_blocker",              # guards.G9_FLAG absent -> refuse
        "second_copy_attested",         # charter second-copy flag
        "frozen_hashes",                # guards.verify_frozen_hashes
        "git_clean",                    # worktree clean (registry allowlisted)
        "supplement_id_pattern",        # SUPPLEMENT_ID_PATTERN
        "registry_chain_resolvable",    # whole-chain resolution or refuse
        "live_authorization_unique",    # exactly one live P2 for this id
        "authorization_actor",          # P2 actor must be Aaron
        "authorized_commit_matches_head",   # exact 40-hex HEAD binding
        "output_root_declared",         # P2 named an output root
        "output_root_structure",        # roots valid; NEVER created here
        "supplement_subtree_absent",    # observed, never created
        "id_not_retired",               # no F3/AX terminal for this id
    ),
    "B_DERIVE": (
        "custody_authority_production",  # test_only authority refused
        "custody_authority_binding",     # trial/commit/source triple
        "source_bundle_digest",          # 14-file digest table equality
        "day_universe_identity",         # the §D.2.2 structural identity
        "method_version_pinned",         # frozen method digest
    ),
    "C_BUILD": (
        "row_schema_blind",             # four structural keys only
        "day_set_exact",                # exact sealed-universe coverage
        "rows_digest_recompute",        # declared digest re-derived
        "seal_staging_partial",         # .partial discipline (profile MODIFY)
        "archive_policy_a",             # local_seal_ok AND archive_ok
    ),
})

#: Flat closed enum, derived — never hand-listed.
GATE_NAME_ENUM: tuple = tuple(g for stage in STAGE_ENUM
                              for g in GATE_TABLE[stage])

#: `FAILURE_CODE_ENUM` for F2v (§D.3.2 F2v). CLOSED.
VERIFICATION_FAILURE_CODES = ("rederivation_mismatch",
                              "headline_replay_mismatch",
                              "s0_sealed_bytes_moved")

#: `ARCHIVE_CODE_ENUM` (§D.3.2 P4) — CLOSED. These are NOT invented
#: names: each maps to a STRUCTURALLY DISTINGUISHABLE state of an
#: `itsf.s0.runinfra.ArchiveReport`, and `supplement_runner
#: .classify_archive_report` is the one classifier that produces them.
#: `archive_sealed_run` reports failures as free-text `errors` lines plus
#: a two-word `status`, so classifying on prose would be fragile; the
#: classifier reads STRUCTURE only (`inventory is None`, a recheck with a
#: missing digest, a recheck with `match=False`, a set-equality verdict
#: that is False, one that is None). The classifier's bucketing is TOTAL
#: with a terminal refusal (`archive_report_unclassified`) rather than a
#: catch-all bucket — session-conventions §10 "make bucketing total".
ARCHIVE_CODES = ("inventory_unavailable", "file_unreadable",
                 "file_digest_mismatch", "set_equality_refused",
                 "set_equality_unreached")

#: Emitted by the classifier when an `archive_failed` report matches NONE
#: of the above. It is a RUNNER REFUSAL, never a legal A1 archive_code —
#: an unclassifiable archive failure must stop the chain, not be recorded
#: as if it were understood.
ARCHIVE_UNCLASSIFIED_CODE = "archive_report_unclassified"

#: `.partial` recovery, as ratified (`ND1_PARTIAL_RECOVERY_RULE=MODIFY`,
#: `ND1_PARTIAL_MODIFY_TEXT=BRANCH_E_RENAME_TO_.partial.divergent.
#: <incident_id>;BRANCH_C_RENAME_THEN_ALLOW_RETRY`). Silent delete is
#: forbidden on every branch (derived: `SILENT_DELETE_FORBIDDEN=YES`).
PARTIAL_SUFFIX = ".partial"
DIVERGENT_PARTIAL_TEMPLATE = ".partial.divergent.{incident_id}"
SILENT_DELETE_FORBIDDEN = True


class EventSpec:
    """One ratified registry event. Frozen by convention: the module
    exposes only the shared instances and nothing mutates them."""

    __slots__ = ("short_id", "token", "row_class", "actor",
                 "required_fields", "predecessors", "successors",
                 "terminal", "incident_required")

    def __init__(self, short_id: str, token: str, row_class: str, actor: str,
                 required_fields: tuple, predecessors: tuple,
                 successors: tuple, terminal: bool,
                 incident_required: bool = False) -> None:
        self.short_id = short_id
        self.token = token
        self.row_class = row_class
        self.actor = actor
        self.required_fields = required_fields
        self.predecessors = predecessors      # () == chain start
        self.successors = successors
        self.terminal = terminal
        self.incident_required = incident_required

    @property
    def commit_width(self) -> int:
        return COMMIT_WIDTH[self.row_class]

    def __repr__(self) -> str:                       # pragma: no cover
        return f"<EventSpec {self.short_id} {self.token}>"


#: Actor constraints. `AARON` is the only actor a P2 may carry (§D.3.2 P2,
#: mirroring the RUN_AUTHORIZED precedent at registry rows 6/9/13).
ACTOR_AARON = "Aaron"
ACTOR_MAIN_AGENT = "main agent"
ACTOR_RUNNER = "main agent (mc_ds_runner)"
ACTOR_VERIFIER = "<verifier>"
ACTOR_AARON_OR_MAIN_AGENT = "Aaron|main agent"

_SPECS = (
    EventSpec("P1", "SUPPLEMENT_PROPOSED", NUMBERED, ACTOR_MAIN_AGENT,
              ("supplement_id", "ir_basis", "schema",
               "non_authorization_disclaimer"),
              (), ("P2", "F3"), False),
    # MODELLING NOTE, not a reconciliation. §D.3.2 P2 says
    # `PERMITTED_PREDECESSOR=P1 | P2S`, and T1 is ALSO a P1-token row
    # (§D.3.2 T1: "复用 P1 词，不新增词表条目"), so the document's "P1"
    # already covers a successor registration. `T1` appears here only
    # because THIS module splits one token into two short ids to keep the
    # successor-registration fields distinguishable.
    EventSpec("P2", "SUPPLEMENT_EXECUTION_AUTHORIZED", NUMBERED, ACTOR_AARON,
              ("supplement_id", "authorized_commit_40hex", "output_root",
               "verbatim_authorization_sentence"),
              ("P1", "P2S", "T1"), ("P3", "F1", "F3"), False),
    EventSpec("P2S", "SUPPLEMENT_EXECUTION_AUTHORIZATION_SUPERSEDED",
              NUMBERED, ACTOR_AARON_OR_MAIN_AGENT,
              ("supplement_id", "supersedes_event_sequence",
               "superseded_authorized_commit", "reason_code", "incident_id",
               "successor_authorized_commit", "same_id_reauthorization"),
              ("F1",), ("P2",), False, incident_required=True),
    # RECONCILED, DISCLOSED — TWO omissions on this one event, same class.
    #
    # (a) SUCCESSORS. §D.3.2 P3 lists `PERMITTED_SUCCESSOR=P4 | F2`,
    # but §D.3.3's diagram draws `P3 -> A1` on the archive_failed branch and
    # §D.3.2 A1 declares `PERMITTED_PREDECESSOR=P3`. Two of the three
    # ratified statements put A1 after P3; the third omits it. Taking the
    # omission literally would make A1 UNREACHABLE — reintroducing exactly
    # the unreachable-branch defect rounds 2 and 3 removed. Implemented as
    # {P4, A1, F2} and reported to Aaron rather than reconciled silently.
    #
    # (b) PREDECESSORS. §D.3.2 P3 lists `PERMITTED_PREDECESSOR=P2`, while
    # §D.3.2 F1 lists `P3` among its successors ("commit 未变化，且原 P2
    # 仍 live → P3") and §D.3.3 draws that edge. Again two statements
    # against one omission; taking the omission literally would make the
    # same-commit pre-start retry unreachable. Implemented as {P2, F1}:
    # F1 is the immediate PREDECESSOR ROW, P2 remains the AUTHORIZING row,
    # and the `live_authorization_unique` gate still requires that P2 to
    # be live at the retry.
    EventSpec("P3", "SUPPLEMENT_RUN_STARTED", UNNUMBERED, ACTOR_RUNNER,
              ("supplement_id", "atomic_start_marker"),
              ("P2", "F1"), ("P4", "A1", "F2"), False),
    EventSpec("P4", "SUPPLEMENT_SEALED", UNNUMBERED, ACTOR_RUNNER,
              ("supplement_id", "sealed_sha256", "rows_digest",
               "day_universe_digest", "source_input_sha256",
               "method_version", "n_rows", "archive"),
              ("P3",), ("P5", "F2v"), False),
    EventSpec("A1", "SUPPLEMENT_ARCHIVE_FAILED", UNNUMBERED, ACTOR_RUNNER,
              ("supplement_id", "local_seal_sha256", "archive_code",
               "incident_id", "local_seal_immutable",
               "archive_root_attempted"),
              ("P3",), ("A2", "AX"), False, incident_required=True),
    EventSpec("A2", "SUPPLEMENT_ARCHIVE_RECOVERED", NUMBERED,
              ACTOR_MAIN_AGENT,
              ("supplement_id", "recovery_authorization_doc",
               "source_and_archive_exact_inventory_match",
               "per_file_sha256_match", "n_files",
               "local_seal_sha256_unchanged", "incident_id"),
              ("A1",), ("P5",), False, incident_required=True),
    EventSpec("AX", "SUPPLEMENT_ARCHIVE_PERMANENTLY_FAILED", NUMBERED,
              ACTOR_MAIN_AGENT,
              ("supplement_id", "archive_code", "attempts_count",
               "incident_id", "aaron_ruling_doc", "local_seal_sha256",
               "local_seal_immutable"),
              ("A1",), ("F3",), False, incident_required=True),
    EventSpec("P5", "SUPPLEMENT_INDEPENDENTLY_VERIFIED", NUMBERED,
              ACTOR_VERIFIER,
              ("supplement_id", "rederivation_reproduced",
               "headline_replay_identity", "n_cells", "attestation_sha256"),
              ("P4", "A2"), (), True),
    EventSpec("F1", "SUPPLEMENT_ATTEMPT_FAILURE", UNNUMBERED, ACTOR_RUNNER,
              ("supplement_id", "stage", "gate_name", "error_class",
               "incident_id", "consumption_statement", "attempts_dir"),
              ("P2",), ("P3", "P2S", "F3"), False, incident_required=True),
    EventSpec("F2", "SUPPLEMENT_FAILED", UNNUMBERED, ACTOR_RUNNER,
              ("supplement_id", "stage", "error_class", "incident_id",
               "residue_path", "residue_preserved"),
              ("P3",), ("F3",), False, incident_required=True),
    EventSpec("F2v", "SUPPLEMENT_VERIFICATION_FAILED", NUMBERED,
              ACTOR_VERIFIER,
              ("supplement_id", "failure_code", "detail",
               "sealed_artifact_deleted", "supersession_required"),
              ("P4",), ("F3",), False),
    EventSpec("F3", "SUPPLEMENT_SUPERSEDED", NUMBERED, ACTOR_MAIN_AGENT,
              ("supersedes_event_sequence", "superseded_supplement_id",
               "superseded_commit", "reason_code", "incident_id",
               "successor_supplement_id"),
              ("P1", "P2", "F1", "F2", "F2v", "AX"), ("T1",), True,
              incident_required=True),
    EventSpec("T1", "SUPPLEMENT_PROPOSED", NUMBERED, ACTOR_MAIN_AGENT,
              ("successor_supplement_id", "predecessor_supplement_id",
               "superseded_at_event", "reason_code", "schema",
               "non_authorization_disclaimer"),
              ("F3",), ("P2",), False),
)

#: short id -> spec. T1 reuses P1's TOKEN deliberately (§D.3.2 T1: "复用
#: P1 词，不新增词表条目"), so token -> short id is NOT a function; a
#: resolver disambiguates T1 from P1 by its successor-registration fields.
EVENTS: Mapping[str, EventSpec] = MappingProxyType(
    {s.short_id: s for s in _SPECS})

#: Every legal token. `SUPPLEMENT_PROPOSED` appears once even though two
#: specs carry it.
EVENT_TOKENS: tuple = tuple(sorted({s.token for s in _SPECS}))

#: Deferred to N-D3 (§D.3.4). Named so the parser refuses them BY NAME.
ND3_DEFERRED_TOKENS = ("SUPPLEMENT_CONSUMED_BY_GRID_REPLAY",
                       "MC_RUN_AUTHORIZED", "MC_RUN_STARTED",
                       "MC_RUN_SEALED", "MC_RUN_FAILED")

#: The two terminals (§D.3.3). `A1` and `AX` are explicitly NOT terminals.
TERMINAL_SHORT_IDS = ("P5", "F3")
NON_TERMINAL_TRAPS = ("A1", "AX")

#: Edges the resolver must refuse even though both endpoints are legal
#: events (§D.3.3 "不存在的边"). Kept as data so a test can assert the
#: resolver rejects every one of them.
FORBIDDEN_EDGES = (
    ("F1", "P2"),     # changing commit without going through P2S
    ("A1", "P5"),     # skipping archive recovery
    ("A1", "P4"),
    ("AX", "A2"),
    ("AX", "P5"),
    ("P2S", "P3"),    # must pass through the new P2
    ("P3", "P2S"),    # past the pre-start boundary
    ("F2", "P3"),     # post-start in-place retry
)


class SupplementGrammarError(ValueError):
    """Fail-closed refusal from the supplement grammar layer. `code` is
    the machine-readable reason (mirrors `consumer.MCInputError` and
    `day_strata_supplement.SupplementError`)."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(f"{code}: {detail}" if detail else code)


def spec_for_short_id(short_id: str) -> EventSpec:
    try:
        return EVENTS[short_id]
    except KeyError:
        raise SupplementGrammarError("unknown_event_short_id",
                                     repr(short_id)) from None


def is_forbidden_edge(from_id: str, to_id: str) -> bool:
    return (from_id, to_id) in FORBIDDEN_EDGES


def transition_allowed(from_id: str, to_id: str) -> bool:
    """True only when the edge is in the successor list AND not on the
    forbidden list. Both conditions, always — the forbidden list exists
    because some illegal edges connect two events that ARE otherwise
    neighbours in the graph."""
    if is_forbidden_edge(from_id, to_id):
        return False
    return to_id in spec_for_short_id(from_id).successors
