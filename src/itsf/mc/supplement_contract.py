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
              ("P2", "F1"), ("P4", "A1", "F2", "CR1"), False),
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
    # ND1_RECOMMENDED_PROFILE_R3, ratified 2026-08-27 (doc HEAD 2728e43,
    # profile d40ad864..., grammar block c251335f...). Transcribed verbatim
    # from BEGIN_ND1_CR1_GRAMMAR_R3 — the approved bytes define this spec,
    # not the other way round.
    #
    # A dangling P3 means a run started and its process died before any
    # terminal event. CR1 is how that gets ADJUDICATED, and its successor
    # list is F3 alone: crash resolution never revives a run. The
    # ("CR1","P3") edge in FORBIDDEN_EDGES states that positively, because
    # a closed successor list only says it by omission.
    EventSpec("CR1", "SUPPLEMENT_RUN_CRASH_RESOLVED", NUMBERED,
              ACTOR_MAIN_AGENT,
              ("supplement_id", "dangling_event", "incident_id",
               "crash_evidence_summary", "recovery_authorization_doc",
               "registry_intact_verification", "registry_witness_ref"),
              ("P3",), ("F3",), False, incident_required=True),
    EventSpec("F3", "SUPPLEMENT_SUPERSEDED", NUMBERED, ACTOR_MAIN_AGENT,
              ("supersedes_event_sequence", "superseded_supplement_id",
               "superseded_commit", "reason_code", "incident_id",
               "successor_supplement_id"),
              ("P1", "P2", "F1", "F2", "F2v", "AX", "CR1"), ("T1",), True,
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
#: THE RATIFIED FIVE-NAME TRANSCRIPTION — unchanged, and deliberately so.
#: Two of them are no longer refused by this grammar (see below), but the
#: transcription itself stays verifiable against §D.3.4: C3 of the
#: MC-REG-COLLISION-001 ruling requires the discharge to be recorded as an
#: explicit exclusion citing the ruling, NOT as a silent deletion of names
#: from a ratified list.
ND3_DEFERRED_TOKENS = ("SUPPLEMENT_CONSUMED_BY_GRID_REPLAY",
                       "MC_RUN_AUTHORIZED", "MC_RUN_STARTED",
                       "MC_RUN_SEALED", "MC_RUN_FAILED")

#: THE EXCLUSION. `MC-REG-COLLISION-001`, C3, ratified by a fresh Codex
#: GPT-5.6 Sol session 2026-08-25 over a Fable 5 proposal. `DELEGATED=YES`.
#:
#: §D.3.4 deferred these names for a stated REASON — "其生命周期定义（前置/
#: 后继/终态/与 MC run 序列的耦合）尚不完整" — under a stated CONSEQUENCE,
#: "在 N-D3 裁定前". Both have now fired for exactly these two: the N-D3
#: ruling (G1-G8, 2026-08-24) supplied the missing lifecycle definitions,
#: and `mc_registry` owns and validates them. This is a guard being
#: DISCHARGED on its own terms, not a refusal being weakened.
#:
#: The other three are NOT discharged, for two different reasons:
#:   SUPPLEMENT_CONSUMED_BY_GRID_REPLAY — deferred over the GRID-replay
#:     coupling, which N-D3 did not rule. Its condition has not fired.
#:   MC_RUN_SEALED / MC_RUN_FAILED — anticipated at N05, never created by
#:     the ruling (it made MC_BRANCH_SEALED and MC_RUN_FAILED_POSTSTART
#:     instead). Nothing to discharge; a name that means nothing stays
#:     refused.
ND3_DEFERRAL_DISCHARGED_BY = "MC-REG-COLLISION-001 (C3, DELEGATED=YES)"
ND3_DEFERRAL_DISCHARGED = ("MC_RUN_AUTHORIZED", "MC_RUN_STARTED")

#: What this grammar still refuses BY NAME. Derived, never hand-listed —
#: a second hand-written tuple is a second thing to keep in agreement.
ND3_STILL_REFUSED_BY_NAME = tuple(
    t for t in ND3_DEFERRED_TOKENS if t not in ND3_DEFERRAL_DISCHARGED)

#: The two terminals (§D.3.3). `A1` and `AX` are explicitly NOT terminals.
TERMINAL_SHORT_IDS = ("P5", "F3")
NON_TERMINAL_TRAPS = ("A1", "AX", "CR1")

#: DECISION-SEAT RULING, 第 1 件 of dec-four-owner-2026-08-27 — executor
#: provenance, formalised rather than added.
#:
#: THE CONTRADICTION IT RESOLVES. The approved actor table assigns A1/F1/F2
#: to `main agent (mc_ds_runner)` while global boundary 4 says only the main
#: agent writes the registry. Those read as conflicting only if both are
#: about the same thing. They are not: boundary 4 states OWNERSHIP, and the
#: parenthesis states the EXECUTING PROCESS. The convention was already
#: here, in every actor string, and was never written down.
#:
#: TWO CLASSES, AND THE SPLIT IS EXACT (measured 2026-08-27):
#:
#:   runtime, written by a live process   P3 P4 A1 F1 F2  -> "role (process)"
#:   governance, appended by hand         P1 A2 AX CR1 F3 T1 -> "role"
#:
#: The ruling's §1.3 wording asked for `main agent (<process>)` uniformly;
#: taken literally that rejects nine of fifteen events. The two-class form
#: below is the model the same ruling states in its own
#: CROSS_ITEM_CONSISTENCY section, and it is what the actor strings already
#: encode. Its own falsifier — "if P3/A1/F1/F2 are not in `role (executor)`
#: form" — was run and did not fire.
ACTOR_FORM_RUNTIME = "runtime"        # role (process): a live process wrote it
ACTOR_FORM_GOVERNANCE = "governance"  # bare role: appended by hand
ACTOR_FORM_OWNER = "owner"            # Aaron
ACTOR_FORM_ALTERNATION = "alternation"  # either of two roles
ACTOR_FORM_PLACEHOLDER = "placeholder"  # the seat is not yet named

_ACTOR_RUNTIME_RE = re.compile(r"^[a-z][a-z ]*\(([A-Za-z0-9_.]+)\)\Z")
_ACTOR_GOVERNANCE_RE = re.compile(r"^[a-z][a-z ]*[a-z]\Z")
_ACTOR_PLACEHOLDER_RE = re.compile(r"^<[a-z]+>\Z")


def actor_form(actor: str) -> str:
    """Which of the five shapes an actor string is, or raise.

    Fail-closed: an actor in none of the shapes is a refusal, not a
    default. A sixth shape appearing silently is how an executor stops
    being recorded."""
    if actor == ACTOR_AARON:
        return ACTOR_FORM_OWNER
    if "|" in actor:
        return ACTOR_FORM_ALTERNATION
    if _ACTOR_PLACEHOLDER_RE.match(actor):
        return ACTOR_FORM_PLACEHOLDER
    if _ACTOR_RUNTIME_RE.match(actor):
        return ACTOR_FORM_RUNTIME
    if _ACTOR_GOVERNANCE_RE.match(actor):
        return ACTOR_FORM_GOVERNANCE
    raise SupplementGrammarError(
        "actor_form_unrecognised",
        "%r is in none of the five ratified actor shapes; an executor that "
        "cannot be classified is an executor that is not recorded" % actor)


def executor_of(actor: str) -> str | None:
    """The executing process an actor string names, or `None` when it names
    no process — which is itself the fact that it was appended by hand."""
    m = _ACTOR_RUNTIME_RE.match(actor)
    return m.group(1) if m else None


#: DECISION-SEAT RULING R-C (dec-item6-open-2026-08-27) = PER_ID_ONLY.
#:
#: Whether a chain's LAST event leaves the id able to start new work. A
#: WHITELIST, deliberately: a blacklist would let any event added later
#: default to permitted, which is backwards for a fail-closed stack. A new
#: event lands on the refusing side until someone rules otherwise.
#:
#: NOT AN AUTHORIZATION. The name says `CHAIN_STATE_PERMITS_START`, not
#: `START_ADMISSIBLE`, because this is one necessary condition among
#: several — a run still needs a unique live P2, whose actor is Aaron.
#:
#: SCOPE IS PER-ID AND ONLY PER-ID. R-C considered blocking the whole MC
#: entry whenever any id has a dangling P3 and refused to hard-code it:
#: P3 is UNNUMBERED and consumes no exposure slot, so a dangling P3 is one
#: id's unclosed lifecycle, not a registry-integrity event; real registry
#: damage is already covered by conditional global fail-closed (the witness
#: superset criterion, A_PRECHECK re-resolution). GLOBAL-BY-GOVERNANCE
#: REMAINS AVAILABLE AND UNCHANGED — Aaron withholding every new P2 during
#: an incident blocks everything, with no code and no un-wedging ruling.
#: What the ruling refused was hard-coding that discretion, not the
#: discretion.
CHAIN_STATE_PERMITS_START = ("P1", "P2", "F1", "T1")

#: Why each refusing state refuses, one distinct name per state — a
#: reviewer asked for that explicitly, because "refused" alone cannot tell
#: an operator whether to wait, re-authorize, or adjudicate.
CHAIN_STATE_REFUSAL = MappingProxyType({
    "P2S": "AWAITING_REAUTHORIZATION",
    "P3": "ABANDONED_RUN",
    "P4": "AWAITING_INDEPENDENT_VERIFICATION",
    "A2": "AWAITING_INDEPENDENT_VERIFICATION",
    "F2": "AWAITING_RETIREMENT",
    "F2v": "AWAITING_RETIREMENT",
    "A1": "AWAITING_ARCHIVE_RESOLUTION",
    "AX": "AWAITING_RETIREMENT",
    "CR1": "AWAITING_RETIREMENT",
    "P5": "CLOSED_USE_A_NEW_ID",
    "F3": "CLOSED_USE_A_NEW_ID",
})


def chain_state_refusal(last_short_id: str) -> str | None:
    """`None` when the chain state permits a start; otherwise the named
    reason. Fail-closed on an unknown event: a short id in neither table
    refuses with a name that says so, rather than falling through."""
    if last_short_id in CHAIN_STATE_PERMITS_START:
        return None
    return CHAIN_STATE_REFUSAL.get(last_short_id, "UNRULED_CHAIN_STATE")


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
    # Decision-seat ruling R-A (dec-item6-open-2026-08-27) = FULL. All three,
    # not two: a two-edge middle state was the sixth review round's Finding 1.
    # The seat's ground was measured, not asserted — every one of the eight
    # edges above is ALSO redundant against a closed successor list, so this
    # table has never been a correctness mechanism. It is the named-policy
    # layer, and leaving CR1 out would have made it the table's one exception.
    ("CR1", "P4"),    # a crash adjudication does not become a seal
    ("CR1", "P5"),    # nor an independent verification
    ("CR1", "P3"),    # THE restart edge: crash resolution never revives a run
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
