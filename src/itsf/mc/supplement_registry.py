"""N05 — supplement registry grammar parser + chain resolver. FAIL-CLOSED.

LANE-OWNED (N05). The ratified vocabulary lives in `supplement_contract`
(main-agent owned, read-only here): every token, row class, commit width,
required-field list, successor list and forbidden edge is IMPORTED from
there, never restated. This module adds only the two things the contract
deliberately leaves out: how registry BYTES become events, and how a
sequence of events becomes a resolvable chain.

WHAT THIS IS NOT. It is not an authorization. `find_live_authorization`
returning a row is a GRAMMATICAL fact about registry text — it says a
format-legal `SUPPLEMENT_EXECUTION_AUTHORIZED` row exists and is not
superseded, nothing more. The ratified profile still says
`SUPPLEMENT_EXECUTION_AUTHORIZED=NO`
(`ops/ND1_PROFILE_RATIFICATION.md` §4), and N04's production entry
refuses even when a live row is found. Nothing here creates a directory,
reads data, appends a row, or performs ANY I/O: every entry point takes
registry TEXT and returns values.

DISCIPLINE MIRRORED FROM THE EXISTING PARSER. `scripts/s0_real_run.py`
(`parse_registry_events` / `_validate_authorized_row` /
`resolve_authorizations`) is the ONE existing registry parser and this is
its supplement analogue, not its replacement: same six-cell row contract,
same `**bold**` stripping, same fenced-block exclusion, same
header/separator skipping, same "any chain defect fails the WHOLE
resolution" rule, same IR-25 fixture-7 row-commit-cell check.

THE ONE DELIBERATE DIVERGENCE (§D.3.6, ratified as
`ND1_PARSER_MALFORMED_ROW_POLICY=B_REFUSE`). The S0 parser treats a line
whose cell count is not 6 as "not a row" and silently drops it. For the
supplement family that is a real risk — a mistyped `SUPPLEMENT_SEALED`
row would VANISH instead of erroring. Here, any row-shaped line
(`|`-leading) that carries a supplement-family token but violates the
six-cell contract REFUSES with `supplement_row_malformed`.

GRAMMAR DECISION, DISCLOSED. §D.3.5 requires
`UNKNOWN_FIELD_IN_NOTE` / `DUPLICATE_FIELD_IN_NOTE` /
`MISSING_REQUIRED_FIELD` to be mechanically detectable. That is only
possible if notes carry machine-readable fields, so every supplement note
is parsed as::

    [<supplement_id>] key: value; key: value; ...

which is exactly the shape the existing `RUN_AUTHORIZATION_SUPERSEDED`
rows already use (`ops/TRIAL_REGISTRY.md` rows 7/10) and the shape
§D.3.2 writes for P2S/F3. The packet renders P1/P3's NOTE_SHAPE as prose;
this parser requires the field form for them too. P2 is the single
exception, and only because its note IS Aaron's verbatim §13.5 sentence
— whose three lines are themselves `key: value` pairs, so the same field
machinery validates it after the sentence header is matched.
"""
from __future__ import annotations

import os as _os
import re
from types import MappingProxyType
from typing import Mapping, Sequence

from . import supplement_contract as sc

__all__ = [
    "Refusal", "RegistryRow", "SupplementEvent", "ChainResolution",
    "SupplementRegistryError",
    "parse_registry_rows", "parse_supplement_events",
    "resolve_supplement_chains", "resolve_supplement_chain", "resolve_chain",
    "resolve_supplement_chains_or_raise", "find_live_authorization",
    "execution_sentence_header",
    "REFUSAL_CODES", "P2S_REFUSAL_CODES", "ARCHIVE_REFUSAL_CODES",
    "FORBIDDEN_EDGE_CODES", "ALLOWED_NOTE_FIELDS", "REQUIRED_NOTE_KEYS",
    "NOT_AUTHORIZED_NO_CHAIN",
]


# ===========================================================================
# Refusal
# ===========================================================================

class SupplementRegistryError(sc.SupplementGrammarError):
    """Raised only by the explicit `*_or_raise` entry points. Every other
    entry point returns a `(value, Refusal | None)` pair so that a caller
    cannot accidentally swallow a refusal with a bare `except`."""


class Refusal:
    """A machine-readable refusal. Always truthy, so `if problem:` works
    exactly like the existing parser's non-empty `problem` string."""

    __slots__ = ("code", "detail", "seq", "supplement_id", "line_no")

    def __init__(self, code: str, detail: str = "", *, seq: str = "",
                 supplement_id: str = "", line_no: int = 0) -> None:
        self.code = code
        self.detail = detail
        self.seq = seq
        self.supplement_id = supplement_id
        self.line_no = line_no

    def __bool__(self) -> bool:              # a refusal is never falsy
        return True

    def __str__(self) -> str:
        where = []
        if self.supplement_id:
            where.append(self.supplement_id)
        if self.seq:
            where.append(f"row #{self.seq}")
        elif self.line_no:
            where.append(f"line {self.line_no}")
        loc = f" [{', '.join(where)}]" if where else ""
        return f"{self.code}{loc}: {self.detail}" if self.detail else \
               f"{self.code}{loc}"

    def __repr__(self) -> str:               # pragma: no cover
        return f"<Refusal {self.code}>"

    def raise_(self) -> None:
        raise SupplementRegistryError(self.code, str(self))


# ===========================================================================
# Row / event containers
# ===========================================================================

class RegistryRow:
    """One six-cell registry table row, supplement-family or not."""

    __slots__ = ("pos", "seq", "utc", "event", "commit", "actor", "note",
                 "line_no")

    def __init__(self, pos: int, seq: str, utc: str, event: str, commit: str,
                 actor: str, note: str, line_no: int) -> None:
        self.pos = pos
        self.seq = seq
        self.utc = utc
        self.event = event
        self.commit = commit
        self.actor = actor
        self.note = note
        self.line_no = line_no

    @property
    def numbered(self) -> bool:
        return self.seq != sc.UNNUMBERED_SEQ_TOKEN

    def __repr__(self) -> str:               # pragma: no cover
        return f"<RegistryRow #{self.seq} {self.event}>"


class SupplementEvent:
    """A registry row that has been classified as a ratified supplement
    event and validated at row level (class, widths, actor, fields).

    The attribute surface `authorized_commit` / `output_root` / `actor` is
    what N04's gates read off a live authorization
    (`supplement_runner._g_authorization_actor`,
    `_g_authorized_commit_matches_head`, `_g_output_root_declared`)."""

    __slots__ = ("row", "short_id", "supplement_id", "fields")

    def __init__(self, row: RegistryRow, short_id: str, supplement_id: str,
                 fields: Mapping[str, str]) -> None:
        self.row = row
        self.short_id = short_id
        self.supplement_id = supplement_id
        self.fields = MappingProxyType(dict(fields))

    # -- passthroughs -------------------------------------------------
    @property
    def pos(self) -> int:
        return self.row.pos

    @property
    def seq(self) -> str:
        return self.row.seq

    @property
    def commit(self) -> str:
        return self.row.commit

    @property
    def actor(self) -> str:
        return self.row.actor

    @property
    def note(self) -> str:
        return self.row.note

    @property
    def token(self) -> str:
        return self.row.event

    @property
    def spec(self) -> sc.EventSpec:
        return sc.EVENTS[self.short_id]

    # -- authorization surface (P2 only; "" elsewhere) ----------------
    @property
    def authorized_commit(self) -> str:
        return self.fields.get("authorized_commit", "")

    @property
    def output_root(self) -> str:
        return self.fields.get("output_root", "")

    def __repr__(self) -> str:               # pragma: no cover
        return f"<SupplementEvent {self.short_id} #{self.seq} " \
               f"{self.supplement_id}>"


class ChainResolution:
    """The resolution of ONE supplement id's chain.

    `problem` is "" only when the WHOLE document resolved: §D.3.5
    `ANY_CHAIN_DEFECT=REFUSE_WHOLE_RESOLUTION` means a defect anywhere
    poisons every id, never just the offending row. `live_authorizations`
    is empty whenever `problem` is set, so a caller that ignores
    `problem` still cannot read authorization out of a broken registry.
    """

    __slots__ = ("supplement_id", "events", "live_authorizations", "retired",
                 "started", "terminal", "problem", "refusal", "detail")

    def __init__(self, supplement_id: str, *,
                 events: Sequence[SupplementEvent] = (),
                 live_authorizations: Sequence[SupplementEvent] = (),
                 retired: bool = False, started: bool = False,
                 terminal: str = "", problem: str = "",
                 refusal: Refusal | None = None, detail: str = "") -> None:
        self.supplement_id = supplement_id
        self.events = tuple(events)
        self.live_authorizations = tuple(live_authorizations)
        self.retired = retired
        self.started = started
        self.terminal = terminal
        self.problem = problem
        self.refusal = refusal
        self.detail = detail

    @property
    def short_ids(self) -> tuple:
        """Feeds `supplement_runner.assert_chain_closed`."""
        return tuple(e.short_id for e in self.events)

    @property
    def closed(self) -> bool:
        return self.terminal in sc.TERMINAL_SHORT_IDS

    def __repr__(self) -> str:               # pragma: no cover
        return (f"<ChainResolution {self.supplement_id} "
                f"{'/'.join(self.short_ids) or 'EMPTY'}"
                f"{' PROBLEM' if self.problem else ''}>")


# ===========================================================================
# §D.3.1 note grammar
# ===========================================================================

#: `[<supplement_id>] <rest>` — the bracket is the CHAIN KEY of every
#: supplement row (mirrors the `[S0-T001]` prefix the existing supersede
#: rows already carry).
_NOTE_BRACKET_RE = re.compile(r"^\[\s*([^\]]*?)\s*\]\s*(.*)$", re.S)
_FIELD_RE = re.compile(r"^([a-z][a-z0-9_]*)\s*:\s*(.*)$", re.S)
FIELD_SEPARATOR = ";"

#: A line that LOOKS like a table row and carries one of these tokens must
#: be a legal row or be refused (§D.3.6 policy B). Prose that merely
#: mentions a token is still never an event (§D.3.0).
_TOKEN_SCAN_RE = re.compile(r"(?<![A-Z0-9_])(SUPPLEMENT_[A-Z0-9_]+"
                            r"|MC_RUN_[A-Z0-9_]+)")

#: Fields carried in a note that the contract does not list as REQUIRED
#: but §D.3.2's NOTE_SHAPE / actor rules do allow. Anything else refuses.
_OPTIONAL_FIELDS: Mapping[str, tuple] = MappingProxyType({
    # §D.3.2 P2S actor rule: a main-agent P2S must cite Aaron's ruling
    # verbatim ("Aaron 批复: <doc>"); Aaron's own P2S need not.
    "P2S": ("aaron_ruling_doc",),
    # §D.3.2 F2v INCIDENT_FIELD: "可选；若已开 incident 则必填".
    "F2v": ("incident_id",),
})

#: The contract names P2's commit field `authorized_commit_40hex`; the
#: ratified §13.5 sentence Aaron actually sends writes the key
#: `authorized_commit`. This table is the ONE place the two names are
#: reconciled (reported to the main agent as an interface note).
_FIELD_KEY_ALIASES: Mapping[str, Mapping[str, str]] = MappingProxyType({
    "P2": MappingProxyType({"authorized_commit_40hex": "authorized_commit"}),
})

#: Required "fields" that are not `key: value` pairs at all. P2's
#: `verbatim_authorization_sentence` is the sentence itself and is checked
#: structurally instead.
_SYNTHETIC_FIELDS: Mapping[str, frozenset] = MappingProxyType({
    "P2": frozenset({"verbatim_authorization_sentence"}),
})


def _note_key(short_id: str, field: str) -> str:
    return _FIELD_KEY_ALIASES.get(short_id, {}).get(field, field)


def _required_keys(short_id: str) -> tuple:
    spec = sc.EVENTS[short_id]
    synth = _SYNTHETIC_FIELDS.get(short_id, frozenset())
    keys = [_note_key(short_id, f) for f in spec.required_fields
            if f not in synth]
    # `supplement_id` is carried by the note's bracket for every event
    # EXCEPT P2, whose §13.5 sentence must spell it out verbatim.
    if short_id != "P2":
        keys = [k for k in keys if k != "supplement_id"]
    return tuple(keys)


def _allowed_keys(short_id: str) -> tuple:
    keys = set(_required_keys(short_id))
    keys.update(_OPTIONAL_FIELDS.get(short_id, ()))
    keys.add("supplement_id")            # always permitted, must match bracket
    return tuple(sorted(keys))


REQUIRED_NOTE_KEYS: Mapping[str, tuple] = MappingProxyType(
    {s: _required_keys(s) for s in sc.EVENTS})
ALLOWED_NOTE_FIELDS: Mapping[str, tuple] = MappingProxyType(
    {s: _allowed_keys(s) for s in sc.EVENTS})


# --- value vocabularies ----------------------------------------------------

_HEX64_FIELDS = frozenset({"sealed_sha256", "rows_digest",
                           "day_universe_digest", "source_input_sha256",
                           "local_seal_sha256", "attestation_sha256",
                           # R3: CR1_FIELD_DOMAIN_registry_intact_verification
                           # = SHA256_HEX64_OF_REGISTRY_BYTES_AS_READ_BEFORE...
                           "registry_intact_verification"})

#: Fields the ratified grammar pins to a single literal value. R3 gives CR1
#: `CR1_FIELD_DOMAIN_dangling_event=P3`; a profile line that nothing enforces
#: is a claim, not a constraint.
_LITERAL_DOMAIN_FIELDS = {"dangling_event": "P3"}
_HEX40_FIELDS = frozenset({"authorized_commit", "superseded_authorized_commit",
                           "successor_authorized_commit", "superseded_commit"})
_INT_FIELDS = frozenset({"supersedes_event_sequence", "n_rows", "n_cells",
                         "n_files", "attempts_count", "superseded_at_event"})
#: N06 repair. Being an integer was the whole check at 617f7c3, so
#: `n_rows: -5` parsed happily and a sealed row could claim a negative
#: population. Every one of these counts a thing that exists, so the
#: floor is 1: a supplement with no rows, an attestation over no cells, an
#: archive of no files, a zeroth attempt and a reference to event 0 are
#: all nonsense the chain must refuse rather than record.
_INT_MIN = {"supersedes_event_sequence": 1, "n_rows": 1, "n_cells": 1,
            "n_files": 1, "attempts_count": 1, "superseded_at_event": 1}
_YES_FIELDS = frozenset({"local_seal_immutable", "same_id_reauthorization",
                         "residue_preserved", "supersession_required",
                         "source_and_archive_exact_inventory_match",
                         "per_file_sha256_match"})
_NO_FIELDS = frozenset({"sealed_artifact_deleted"})
_ID_FIELDS = frozenset({"supplement_id", "superseded_supplement_id",
                        "predecessor_supplement_id",
                        "successor_supplement_id"})
_ENUM_FIELDS: Mapping[str, tuple] = MappingProxyType({
    "stage": sc.STAGE_ENUM,
    "gate_name": sc.GATE_NAME_ENUM,
    "failure_code": sc.VERIFICATION_FAILURE_CODES,
    "rederivation_reproduced": ("YES", "NO"),
    "headline_replay_identity": ("PASS", "FAIL"),
})
_ENUM_FIELD_CODES: Mapping[str, str] = MappingProxyType({
    "stage": "stage_outside_closed_enum",
    "gate_name": "gate_name_outside_closed_enum",
    "failure_code": "failure_code_outside_closed_enum",
})

ARCHIVE_OK = "archive_ok"
ARCHIVE_FAILED_PREFIX = "archive_failed:"


def execution_sentence_header(supplement_id: str) -> str:
    """The verbatim §13.5 sentence header for one supplement id.

    This is the string a P2 note must contain; it is NOT an authorization
    and deliberately carries no commit and no output root — the parser
    needs the header to LOCATE Aaron's sentence, and building a complete
    sentence is not this module's business."""
    return ("START_" + supplement_id.replace("-", "_")
            + "_DAY_STRATA_SUPPLEMENT_EXECUTION")


# ===========================================================================
# Refusal codes (lowercase mirrors of the packet's UPPER names)
# ===========================================================================

#: §D.3.2 P2S block — exactly eleven, in packet order.
P2S_REFUSAL_CODES = (
    "p2s_no_target_p2",
    "p2s_target_not_live",
    "p2s_target_ambiguous",
    "p2s_forward_reference",
    "p2s_commit_mismatch",
    "p2s_supplement_id_mismatch",
    "p2s_duplicate_supersede",
    "p2s_successor_equals_superseded",
    "p2s_without_preceding_f1",
    "p2s_after_p3",
    "multiple_live_p2_after_p2s",
)

#: §D.3.5 archive block (policy A).
ARCHIVE_REFUSAL_CODES = (
    "p4_with_archive_failed_under_policy_a",
    "a1_without_local_seal_digest",
    "a1_archive_code_outside_closed_enum",
    "a2_without_preceding_a1",
    "a2_without_recovery_authorization_doc",
    "a2_inventory_mismatch_claimed_ok",
    "a2_local_seal_digest_changed",
    "ax_without_preceding_a1",
    "ax_without_aaron_ruling_doc",
    "p5_predecessor_not_p4_or_a2",
    "p5_after_a1_without_a2",
    "p5_after_ax",
    "ax_successor_not_f3",
    "ax_treated_as_terminal",
)

#: Edge -> code for every pair in `supplement_contract.FORBIDDEN_EDGES`.
#: A test asserts this mapping covers that tuple exactly, so adding a
#: forbidden edge upstream goes RED here instead of falling through to a
#: generic code.
FORBIDDEN_EDGE_CODES: Mapping[tuple, str] = MappingProxyType({
    ("F1", "P2"): "f1_to_p2_without_p2s",
    ("A1", "P5"): "p5_after_a1_without_a2",
    ("A1", "P4"): "a1_to_p4_forbidden",
    ("AX", "A2"): "ax_successor_not_f3",
    ("AX", "P5"): "p5_after_ax",
    ("P2S", "P3"): "p2s_to_p3_without_new_p2",
    ("P3", "P2S"): "p2s_after_p3",
    ("F2", "P3"): "f2_to_p3_in_place_retry",
    # R-A = FULL. Ruling condition: each new edge carries a dedicated code,
    # and the mutation proof must assert THE CODE surfaces, not merely that
    # a refusal happened. If a code can never surface because an earlier
    # check preempts it, FULL buys nothing and the ruling falls back to ZERO.
    ("CR1", "P4"): "cr1_to_p4_forbidden",
    ("CR1", "P5"): "p5_after_cr1",
    ("CR1", "P3"): "cr1_does_not_revive_a_run",
})

REFUSAL_CODES = frozenset((
    # row shape / class
    "supplement_row_malformed",
    "unknown_event_token",
    "token_deferred_to_nd3",
    "note_missing_supplement_id_bracket",
    "supplement_id_pattern_violation",
    "note_segment_not_field",
    "field_value_empty",
    "unknown_field_in_note",
    "duplicate_field_in_note",
    "missing_required_field",
    "supplement_id_bracket_field_mismatch",
    "numbered_row_with_plus_seq",
    "unnumbered_row_with_integer_seq",
    "supplement_seq_not_integer",
    "supplement_seq_not_next_value",
    "integer_field_below_minimum",
    "output_root_blank",
    "output_root_not_absolute",
    "output_root_not_normalisable",
    "supplement_seq_duplicate",
    "commit_width_mismatch_for_row_class",
    "actor_not_permitted_for_event",
    "verifier_actor_is_producer_or_aaron",
    # value vocabularies
    "digest_field_not_64hex",
    "commit_field_not_40hex",
    "integer_field_not_integer",
    "yes_field_not_yes",
    "no_field_not_no",
    "supplement_id_field_malformed",
    "incident_id_malformed",
    "reason_code_malformed",
    "stage_outside_closed_enum",
    "gate_name_outside_closed_enum",
    "failure_code_outside_closed_enum",
    "archive_code_outside_closed_enum",
    "enum_field_outside_closed_enum",
    "archive_field_malformed",
    # P2
    "p2_actor_not_aaron",
    "p2_missing_verbatim_authorization_sentence",
    "p2_row_commit_cell_ne_sentence_commit",
    "p2s_main_agent_without_aaron_ruling_doc",
    "p2s_successor_commit_mismatch",
    "multiple_live_p2_for_one_id",
    # chain structure
    "chain_does_not_start_at_proposal",
    "illegal_transition",
    "forbidden_edge",
    "event_after_terminal",
    "retired_supplement_id_reused",
    "p3_without_live_p2",
    "p3_commit_not_authorized_by_live_p2",
    "prestart_commit_change_requires_p2s",
    "p5_claims_failed_verification",
    # F3 / T1
    "f3_no_target_row",
    "f3_target_ambiguous",
    "f3_forward_reference",
    "f3_commit_mismatch",
    "f3_supplement_id_mismatch",
    "f3_target_supplement_id_mismatch",
    "f3_duplicate_supersede",
    "f3_successor_equals_superseded_id",
    "f3_successor_not_registered_by_t1",
    "t1_bracket_id_not_successor_id",
    "t1_successor_equals_predecessor",
    "t1_predecessor_not_superseded_by_f3",
    "t1_predecessor_f3_names_other_successor",
    "t1_superseded_at_event_mismatch",
    "t1_forward_reference",
) + P2S_REFUSAL_CODES + ARCHIVE_REFUSAL_CODES
    + tuple(FORBIDDEN_EDGE_CODES.values()))

#: What a resolver says about an id it has never seen. Never permissive.
NOT_AUTHORIZED_NO_CHAIN = (
    "no supplement event chain exists for this id — NOT AUTHORIZED "
    "(default refuse; a missing chain is never a permissive default)")


# ===========================================================================
# Stage 1 — rows
# ===========================================================================

def parse_registry_rows(text: str) -> tuple:
    """Parse EVERY six-cell registry row (supplement-family or not).

    Non-supplement rows are returned too because the ratified sequence
    namespace is GLOBAL: a numbered supplement row has to slot into the
    same increasing integer sequence the S0 rows already occupy.

    Returns `(rows, refusal | None)`. The only refusal at this stage is
    the §D.3.6 policy-B one: a row-shaped line carrying a
    supplement-family token that violates the six-cell contract.
    """
    rows: list = []
    in_fence = False
    for line_no, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        # IR-25 fixture 4: a row-shaped line inside a fenced code block is
        # documentation, never an event — and therefore never malformed.
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not stripped.startswith("|"):
            continue                      # prose mention is never an event
        bad = _malformed_supplement_line(stripped, line_no)
        if not stripped.endswith("|"):
            if bad:
                return ((), bad)
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) != 6:
            if bad:
                return ((), bad)
            continue
        if cells[0] and set(cells[0]) <= set("-: "):
            continue                                      # separator row
        if cells[0] == "#" and cells[1] == "utc":
            continue                                      # header row
        rows.append(RegistryRow(pos=len(rows), seq=cells[0], utc=cells[1],
                                event=cells[2].strip("*").strip(),
                                commit=cells[3], actor=cells[4],
                                note=cells[5], line_no=line_no))
    return (tuple(rows), None)


def _malformed_supplement_line(stripped: str, line_no: int) -> Refusal | None:
    """§D.3.6 / `ND1_PARSER_MALFORMED_ROW_POLICY=B_REFUSE`."""
    found = _TOKEN_SCAN_RE.findall(stripped)
    if not found:
        return None
    return Refusal(
        "supplement_row_malformed",
        f"row-shaped line carries supplement-family token(s) "
        f"{sorted(set(found))} but violates the six-cell row contract; "
        "policy B refuses instead of silently dropping it",
        line_no=line_no)


# ===========================================================================
# Stage 2 — events
# ===========================================================================

_TOKEN_TO_SHORT_IDS: Mapping[str, tuple] = MappingProxyType({
    token: tuple(s for s in sc.EVENTS if sc.EVENTS[s].token == token)
    for token in sc.EVENT_TOKENS
})

#: §D.3.2 T1 reuses P1's token; these keys are what tells them apart.
_T1_MARKER_FIELDS = ("successor_supplement_id", "predecessor_supplement_id",
                     "superseded_at_event")


def is_supplement_row(row: RegistryRow) -> bool:
    """Which rows this grammar OWNS.

    `ND3_STILL_REFUSED_BY_NAME`, not `ND3_DEFERRED_TOKENS`: the two
    discharged MC tokens are now owned and validated by `mc_registry`, so
    they are skipped here as another lifecycle's rows — exactly as
    `MC_BRANCH_SEALED` always was. See the exclusion in
    `supplement_contract` (MC-REG-COLLISION-001 C3, DELEGATED=YES)."""
    return (row.event.startswith("SUPPLEMENT_")
            or row.event in sc.ND3_STILL_REFUSED_BY_NAME)


def parse_supplement_events(text: str) -> tuple:
    """Rows -> validated `SupplementEvent`s. Returns `(events, refusal)`.

    Row-level validation only (token, bracket, fields, values, row class,
    commit width, actor). Chain structure is `resolve_supplement_chains`.
    """
    rows, refusal = parse_registry_rows(text)
    if refusal:
        return ((), refusal)
    events: list = []
    for row in rows:
        if not is_supplement_row(row):
            continue
        event, refusal = _classify_and_validate(row)
        if refusal:
            return ((), refusal)
        events.append(event)
    return (tuple(events), None)


def _classify_and_validate(row: RegistryRow):
    """One supplement row -> `(SupplementEvent, None)` or `(None, Refusal)`."""
    def no(code, detail, sid=""):
        return (None, Refusal(code, detail, seq=row.seq, supplement_id=sid,
                              line_no=row.line_no))

    token = row.event
    # --- token ------------------------------------------------------
    if token in sc.ND3_STILL_REFUSED_BY_NAME:
        return no("token_deferred_to_nd3",
                  f"{token} is deferred to N-D3 (§D.3.4) and is NOT "
                  "implemented by the N-D1 grammar; it is refused BY NAME "
                  "rather than ignored. Two of §D.3.4's five names are no "
                  f"longer refused here — {list(sc.ND3_DEFERRAL_DISCHARGED)} "
                  f"were discharged by {sc.ND3_DEFERRAL_DISCHARGED_BY} and "
                  "belong to mc_registry; this token is not one of them")
    if token not in sc.EVENT_TOKENS:
        return no("unknown_event_token",
                  f"{token!r} is not a ratified supplement event token; "
                  f"legal tokens are {list(sc.EVENT_TOKENS)} — no "
                  "best-effort parse (mirrors "
                  "day_strata_supplement.authorize_supplement)")

    # --- note bracket ------------------------------------------------
    m = _NOTE_BRACKET_RE.match(row.note.strip())
    if not m:
        return no("note_missing_supplement_id_bracket",
                  "a supplement note must start with [<supplement_id>]")
    sid, remainder = m.group(1), m.group(2).strip()
    if not sc.SUPPLEMENT_ID_PATTERN.match(sid):
        return no("supplement_id_pattern_violation",
                  f"{sid!r} does not match "
                  f"{sc.SUPPLEMENT_ID_PATTERN.pattern}")

    # --- P2's verbatim §13.5 sentence --------------------------------
    candidates = _TOKEN_TO_SHORT_IDS[token]
    if candidates == ("P2",):
        header = execution_sentence_header(sid)
        if not remainder.startswith(header):
            return no("p2_missing_verbatim_authorization_sentence",
                      f"note does not carry the verbatim §13.5 sentence "
                      f"header {header!r}", sid)
        remainder = remainder[len(header):].strip()

    # --- fields -------------------------------------------------------
    fields, refusal = _parse_fields(remainder, row, sid)
    if refusal:
        return (None, refusal)

    # --- short id -----------------------------------------------------
    if len(candidates) == 1:
        short_id = candidates[0]
    else:                                    # SUPPLEMENT_PROPOSED: P1 or T1
        short_id = "T1" if any(f in fields for f in _T1_MARKER_FIELDS) \
            else "P1"

    for check in (_check_row_class, _check_commit_width, _check_actor,
                  _check_fields_against_spec, _check_field_values):
        refusal = check(row, short_id, sid, fields)
        if refusal:
            return (None, refusal)
    return (SupplementEvent(row, short_id, sid, fields), None)


def _parse_fields(remainder: str, row: RegistryRow, sid: str):
    fields: dict = {}
    if not remainder:
        return (fields, None)
    for raw in remainder.split(FIELD_SEPARATOR):
        seg = raw.strip()
        if not seg:
            continue                          # tolerate a trailing ';'
        m = _FIELD_RE.match(seg)
        if not m:
            return (None, Refusal(
                "note_segment_not_field",
                f"{seg!r} is not a `key: value` field; supplement notes are "
                "machine-parsed so that unknown/duplicate/missing fields can "
                "be refused (§D.3.5)",
                seq=row.seq, supplement_id=sid, line_no=row.line_no))
        key, value = m.group(1), m.group(2).strip()
        if key in fields:
            return (None, Refusal(
                "duplicate_field_in_note", f"field {key!r} appears twice",
                seq=row.seq, supplement_id=sid, line_no=row.line_no))
        if not value:
            return (None, Refusal(
                "field_value_empty", f"field {key!r} has an empty value",
                seq=row.seq, supplement_id=sid, line_no=row.line_no))
        fields[key] = value
    return (fields, None)


def _check_row_class(row, short_id, sid, fields) -> Refusal | None:
    spec = sc.EVENTS[short_id]
    plus = row.seq == sc.UNNUMBERED_SEQ_TOKEN
    if spec.row_class == sc.NUMBERED:
        if plus:
            return Refusal("numbered_row_with_plus_seq",
                           f"{spec.short_id} is a NUMBERED governance row and "
                           "may not carry the runner '+' sequence",
                           seq=row.seq, supplement_id=sid,
                           line_no=row.line_no)
        if not re.fullmatch(r"[0-9]+", row.seq or ""):
            return Refusal("supplement_seq_not_integer",
                           f"{row.seq!r} is not an integer sequence number "
                           "(SEQUENCE_NAMESPACE=GLOBAL)",
                           seq=row.seq, supplement_id=sid,
                           line_no=row.line_no)
    elif not plus:
        return Refusal("unnumbered_row_with_integer_seq",
                       f"{spec.short_id} is a runner '+' row and consumes no "
                       "registry sequence number",
                       seq=row.seq, supplement_id=sid, line_no=row.line_no)
    return None


def _check_commit_width(row, short_id, sid, fields) -> Refusal | None:
    spec = sc.EVENTS[short_id]
    width = spec.commit_width
    pattern = sc.HEX40_RE if width == 40 else sc.HEX7_RE
    if not pattern.match(row.commit or ""):
        return Refusal("commit_width_mismatch_for_row_class",
                       f"{spec.short_id} is {spec.row_class} and requires a "
                       f"{width}-hex commit cell; got {row.commit!r}",
                       seq=row.seq, supplement_id=sid, line_no=row.line_no)
    return None


def _check_actor(row, short_id, sid, fields) -> Refusal | None:
    spec = sc.EVENTS[short_id]
    actor = (row.actor or "").strip()
    def bad(code, detail):
        return Refusal(code, detail, seq=row.seq, supplement_id=sid,
                       line_no=row.line_no)

    if spec.actor == sc.ACTOR_AARON:                      # P2
        if actor != sc.ACTOR_AARON:
            return bad("p2_actor_not_aaron",
                       f"actor {actor!r} is not {sc.ACTOR_AARON!r} — §D.3.2 "
                       "P2 mirrors the RUN_AUTHORIZED precedent (registry "
                       "rows 6/9/13)")
        return None
    if spec.actor == sc.ACTOR_AARON_OR_MAIN_AGENT:        # P2S
        if actor == sc.ACTOR_AARON:
            return None
        if not actor.startswith(sc.ACTOR_MAIN_AGENT):
            return bad("actor_not_permitted_for_event",
                       f"P2S actor must be {sc.ACTOR_AARON!r} or "
                       f"{sc.ACTOR_MAIN_AGENT!r}; got {actor!r}")
        if not fields.get("aaron_ruling_doc"):
            return bad("p2s_main_agent_without_aaron_ruling_doc",
                       "a main-agent P2S must cite Aaron's supersession "
                       "ruling verbatim (aaron_ruling_doc); without the "
                       "citation the row is illegal (§D.3.2 P2S ACTOR)")
        return None
    if spec.actor == sc.ACTOR_VERIFIER:                   # P5 / F2v
        if not actor:
            return bad("actor_not_permitted_for_event",
                       f"{spec.short_id} requires a named verifier actor")
        if actor == sc.ACTOR_AARON or actor.startswith(sc.ACTOR_MAIN_AGENT):
            return bad("verifier_actor_is_producer_or_aaron",
                       f"{spec.short_id} actor {actor!r} is the producing "
                       "seat or Aaron; §D.3.2 P5 requires a fresh "
                       "top-level verifier ('不得是产出会话')")
        return None
    if spec.actor == sc.ACTOR_RUNNER:                     # P3/P4/A1/F1/F2
        if actor != sc.ACTOR_RUNNER:
            return bad("actor_not_permitted_for_event",
                       f"{spec.short_id} is runner-emitted; actor must be "
                       f"{sc.ACTOR_RUNNER!r}, got {actor!r}")
        return None
    # ACTOR_MAIN_AGENT — the existing registry appends a parenthetical
    # "（Aaron 批复 <doc>）" to this cell, so a prefix match is what the
    # real rows satisfy.
    if not actor.startswith(sc.ACTOR_MAIN_AGENT):
        return bad("actor_not_permitted_for_event",
                   f"{spec.short_id} actor must start with "
                   f"{sc.ACTOR_MAIN_AGENT!r}; got {actor!r}")
    return None


def _check_fields_against_spec(row, short_id, sid, fields) -> Refusal | None:
    def bad(code, detail):
        return Refusal(code, detail, seq=row.seq, supplement_id=sid,
                       line_no=row.line_no)

    allowed = ALLOWED_NOTE_FIELDS[short_id]
    for key in fields:
        if key not in allowed:
            return bad("unknown_field_in_note",
                       f"{key!r} is not a field of "
                       f"{sc.EVENTS[short_id].token} ({short_id}); allowed: "
                       f"{list(allowed)}")
    if "supplement_id" in fields and fields["supplement_id"] != sid:
        return bad("supplement_id_bracket_field_mismatch",
                   f"note bracket says {sid!r} but the supplement_id field "
                   f"says {fields['supplement_id']!r}")
    if short_id == "P2":
        # §13.5: "三字段齐全，缺一即无效".
        for key in ("supplement_id", "authorized_commit", "output_root"):
            if key not in fields:
                return bad("p2_missing_verbatim_authorization_sentence",
                           f"the §13.5 sentence is missing {key!r}; all "
                           "three fields must be present or the sentence is "
                           "not verbatim")
    for key in REQUIRED_NOTE_KEYS[short_id]:
        if key in fields:
            continue
        # §D.3.5 names dedicated codes for three archive omissions.
        if short_id == "A1" and key == "local_seal_sha256":
            return bad("a1_without_local_seal_digest",
                       "A1 must record the immutable local seal digest")
        if short_id == "A2" and key == "recovery_authorization_doc":
            return bad("a2_without_recovery_authorization_doc",
                       "an archive retry needs Aaron's SEPARATE exact "
                       "authorization cited in the row")
        if short_id == "AX" and key == "aaron_ruling_doc":
            return bad("ax_without_aaron_ruling_doc",
                       "AX records Aaron's permanent-failure ruling and must "
                       "cite it")
        return bad("missing_required_field",
                   f"{sc.EVENTS[short_id].token} ({short_id}) requires "
                   f"{key!r}; present: {sorted(fields)}")
    return None


def _check_field_values(row, short_id, sid, fields) -> Refusal | None:
    def bad(code, detail):
        return Refusal(code, detail, seq=row.seq, supplement_id=sid,
                       line_no=row.line_no)

    for key, value in fields.items():
        want = _LITERAL_DOMAIN_FIELDS.get(key)
        if want is not None and value != want:
            return bad("field_outside_ratified_domain",
                       f"{key}={value!r}; the ratified grammar pins it to "
                       f"{want!r}")
        if key in _HEX64_FIELDS and not sc.HEX64_RE.match(value):
            return bad("digest_field_not_64hex",
                       f"{key}={value!r} is not a 64-hex digest")
        if key in _HEX40_FIELDS and not sc.HEX40_RE.match(value):
            return bad("commit_field_not_40hex",
                       f"{key}={value!r} is not a full 40-hex commit")
        if key in _INT_FIELDS:
            if not re.fullmatch(r"-?[0-9]+", value):
                return bad("integer_field_not_integer", f"{key}={value!r}")
            floor = _INT_MIN.get(key)
            if floor is not None and int(value) < floor:
                return bad("integer_field_below_minimum",
                           f"{key}={value} is below the minimum {floor}")
        if key == "output_root":
            # N06 repair. At 617f7c3 any non-empty string was accepted, so
            # an authorization could name a relative path the runner would
            # never use. The authorized root is the ONE place the evidence
            # may land; it has to be a real absolute path.
            raw = value.strip()
            if not raw:
                return bad("output_root_blank",
                           "the authorization names no output root")
            if "\x00" in raw:
                return bad("output_root_not_normalisable",
                           "output_root contains a null byte")
            try:
                normalised = _os.path.normpath(raw)
            except Exception:                                 # noqa: BLE001
                return bad("output_root_not_normalisable", f"{raw!r}")
            if not _os.path.isabs(normalised):
                return bad("output_root_not_absolute",
                           f"output_root={raw!r} is not an absolute path")
        if key == "local_seal_sha256_unchanged":
            if value == "NO":
                return bad("a2_local_seal_digest_changed",
                           "the archive retry changed the local sealed "
                           "artifact; the local seal is immutable")
            if value != "YES":
                return bad("yes_field_not_yes", f"{key}={value!r}")
        elif key in _YES_FIELDS and value != "YES":
            return bad("yes_field_not_yes", f"{key}={value!r} must be 'YES'")
        if key in _NO_FIELDS and value != "NO":
            return bad("no_field_not_no", f"{key}={value!r} must be 'NO'")
        if key in _ID_FIELDS and value != "NONE" \
                and not sc.SUPPLEMENT_ID_PATTERN.match(value):
            return bad("supplement_id_field_malformed",
                       f"{key}={value!r} does not match "
                       f"{sc.SUPPLEMENT_ID_PATTERN.pattern}")
        if key == "incident_id" and not sc.INCIDENT_RE.match(value):
            return bad("incident_id_malformed", f"{key}={value!r}")
        if key == "reason_code" and not sc.REASON_CODE_RE.match(value):
            return bad("reason_code_malformed", f"{key}={value!r}")
        if key in _ENUM_FIELDS and value not in _ENUM_FIELDS[key]:
            return bad(_ENUM_FIELD_CODES.get(key,
                                             "enum_field_outside_closed_enum"),
                       f"{key}={value!r} is outside the closed enum "
                       f"{list(_ENUM_FIELDS[key])}")
        if key == "archive_code" and value not in sc.ARCHIVE_CODES:
            code = "a1_archive_code_outside_closed_enum"                 if short_id == "A1" else "archive_code_outside_closed_enum"
            return bad(code,
                       f"archive_code={value!r} is outside "
                       f"{list(sc.ARCHIVE_CODES)}")
        if key == "archive":
            refusal = _check_archive_field(value, bad)
            if refusal:
                return refusal
    if short_id == "P2" and row.commit != fields.get("authorized_commit"):
        # IR-25 fixture 7, mirrored: an internally inconsistent
        # authorization row fails closed rather than picking a winner.
        return bad("p2_row_commit_cell_ne_sentence_commit",
                   f"row commit cell {row.commit!r} does not equal the "
                   f"§13.5 sentence commit "
                   f"{fields.get('authorized_commit')!r}")
    if short_id == "P5":
        if fields.get("rederivation_reproduced") != "YES" \
                or fields.get("headline_replay_identity") != "PASS":
            return bad("p5_claims_failed_verification",
                       "a P5 row that records a failed re-derivation or "
                       "replay is a verification FAILURE and must be "
                       f"emitted as {sc.EVENTS['F2v'].token}")
    if short_id == "A2":
        if fields.get("source_and_archive_exact_inventory_match") == "YES" \
                and (fields.get("per_file_sha256_match") != "YES"
                     or not re.fullmatch(r"[1-9][0-9]*",
                                         fields.get("n_files", ""))):
            return bad("a2_inventory_mismatch_claimed_ok",
                       "A2 claims an exact inventory match without a "
                       "complete per-file SHA table (n_files must be a "
                       "positive count and per_file_sha256_match must be "
                       "YES)")
    return None


def _check_archive_field(value: str, bad) -> Refusal | None:
    """Policy A: `P4_SUPPLEMENT_SEALED_REQUIRES=local_seal_ok AND
    archive_ok`, so a P4 carrying `archive_failed:<code>` is refused —
    that outcome is an A1 row, not a P4."""
    if value == ARCHIVE_OK:
        return None
    if value.startswith(ARCHIVE_FAILED_PREFIX):
        code = value[len(ARCHIVE_FAILED_PREFIX):].strip()
        if code not in sc.ARCHIVE_CODES:
            return bad("archive_code_outside_closed_enum",
                       f"archive_code={code!r} is outside "
                       f"{list(sc.ARCHIVE_CODES)}")
        return bad("p4_with_archive_failed_under_policy_a",
                   f"under ratified archive policy A a sealed row requires "
                   f"{ARCHIVE_OK}; {value!r} must be recorded as "
                   f"{sc.EVENTS['A1'].token}")
    return bad("archive_field_malformed",
               f"archive={value!r} must be {ARCHIVE_OK!r} or "
               f"'{ARCHIVE_FAILED_PREFIX}<code>'")


# ===========================================================================
# Stage 3 — chains
# ===========================================================================

#: The ONE `reason_code` that opens the pre-start `P2 -> P2S` edge.
#: Aaron's 2026-09-05 amendment names it, so a supersede claiming any other
#: reason still needs its F1.
PRESTART_COMMIT_CHANGE = "PRESTART_COMMIT_CHANGE"


def _is_prestart_reauthorization(prev: str, event, started: bool) -> bool:
    """Aaron's 2026-09-05 §D.3.2 amendment, and ONLY it.

    THE GAP IT CLOSES. §D.3.2 wrote re-authorization as `F1 -> P2S -> P2`
    because it assumed a stale commit is discovered by an attempt that
    fails. It can also go stale with no attempt at all: the authorization
    is signed, a necessary fix lands, HEAD moves, and nothing has run.
    `F1` cannot describe that without inventing a `stage`, a `gate_name`
    and an `attempts_dir` for an attempt that never happened -- and the S0
    precedent this rule says it mirrors (real ledger rows 6->7 and 9->10)
    took the edge DIRECTLY, with no failure row between.

    THE SIX RULED CONDITIONS, and where each is enforced:

      1. no P3 under this id            `started` -- checked here
      2. nothing consumed               ALSO `started`: consumption happens
                                        at P3 (`SUPPLEMENT_RUN_STARTED`
                                        is the row that takes the slot), so
                                        this is not a second check, it is
                                        the same fact. Said plainly rather
                                        than implied by a field that does
                                        not exist.
      3. same_id_reauthorization=YES    checked here (and the parser
                                        already forces YES on the field)
      4. superseded != successor        existing `p2s_successor_equals_
                                        superseded`
      5. reason_code=PRESTART_...       checked here
      6. supersedes_event_sequence
         points at the old P2           existing `p2s_no_target_p2`,
                                        `p2s_target_not_live`,
                                        `p2s_commit_mismatch`,
                                        `p2s_supplement_id_mismatch`

    Four of the six were already enforced; `_resolve_supersedes` runs
    BEFORE this walk, so they hold whatever the predecessor is. Only 1/2
    and 5 are new, and both are read off the row and the walk -- nothing
    here trusts a caller's word for them.
    """
    if prev != "P2" or started:
        return False
    fields = getattr(event, "fields", None) or {}
    return (fields.get("reason_code") == PRESTART_COMMIT_CHANGE
            and fields.get("same_id_reauthorization") == "YES")


def _edge_code(prev: str, cur: str, *, event=None,
               started: bool = False) -> str | None:
    """The refusal code for one chain edge, or None when legal.

    Specific named codes win over the generic ones so that the packet's
    vocabulary (`P2S_AFTER_P3`, `P5_AFTER_AX`, ...) is what a caller
    actually sees. Order matters and is deliberate.
    """
    if cur == "P2S":
        if prev == "P3":
            return "p2s_after_p3"
        if prev == "F1":
            return None
        if _is_prestart_reauthorization(prev, event, started):
            return None
        return "p2s_without_preceding_f1"
    if cur == "P5" and prev not in ("P4", "A2"):
        if prev == "A1":
            return "p5_after_a1_without_a2"
        if prev == "AX":
            return "p5_after_ax"
        # MEASURED before transcribing, 2026-08-27: without this branch
        # ("CR1","P5") returns the generic `p5_predecessor_not_p4_or_a2`
        # and its dedicated code never surfaces — the exact condition
        # ruling R-A says would make FULL worthless. The branch is not a
        # workaround invented to satisfy the ruling: A1 and AX sit in the
        # same position and are handled the same way, two lines above.
        if prev == "CR1":
            return "p5_after_cr1"
        return "p5_predecessor_not_p4_or_a2"
    if prev == "AX" and cur != "F3":
        return "ax_successor_not_f3"
    if cur == "A2" and prev != "A1":
        return "a2_without_preceding_a1"
    if cur == "AX" and prev != "A1":
        return "ax_without_preceding_a1"
    override = FORBIDDEN_EDGE_CODES.get((prev, cur))
    if override:
        return override
    if sc.is_forbidden_edge(prev, cur):
        return "forbidden_edge"
    if not sc.transition_allowed(prev, cur):
        return "illegal_transition"
    return None


def _check_live_p2_uniqueness(live_count: int, *, after_p2s: bool
                              ) -> str | None:
    """§D.3.5 `MULTIPLE_LIVE_P2_FOR_ONE_ID` / §D.3.2
    `MULTIPLE_LIVE_P2_AFTER_P2S`. Exposed as a helper because the
    post-P2S form is a POST-CONDITION: the pre-condition check on the
    incoming P2 row already makes two live P2s unreachable through
    registry text, and this is the defence that keeps it that way."""
    if live_count <= 1:
        return None
    return "multiple_live_p2_after_p2s" if after_p2s \
        else "multiple_live_p2_for_one_id"


def resolve_supplement_chains(text: str) -> tuple:
    """Whole-document resolution. Returns `(chains, refusal | None)`.

    On ANY defect the mapping is EMPTY and the refusal is returned:
    §D.3.5 `ANY_CHAIN_DEFECT=REFUSE_WHOLE_RESOLUTION`. There is no
    partial-success shape — a caller cannot obtain "the good chains" out
    of a defective registry.
    """
    events, refusal = parse_supplement_events(text)
    if refusal:
        return ({}, refusal)

    rows, _ = parse_registry_rows(text)
    by_seq: dict = {}
    for ev in events:
        if ev.row.numbered:
            by_seq.setdefault(int(ev.seq), []).append(ev)

    # PASS ORDER, deliberate: supersede-reference resolution runs BEFORE
    # the global sequence check so that two rows sharing a sequence number
    # are reported as P2S_TARGET_AMBIGUOUS when a P2S points at them (the
    # packet requires that code to exist) and as a duplicate sequence
    # otherwise. Both are refusals; only the name differs.
    state, refusal = _resolve_supersedes(events, by_seq)
    if refusal:
        return ({}, refusal)
    refusal = _check_global_sequence(rows, events)
    if refusal:
        return ({}, refusal)

    chains: dict = {}
    for ev in events:
        chains.setdefault(ev.supplement_id, []).append(ev)

    resolved: dict = {}
    for sid, chain_events in chains.items():
        resolution, refusal = _walk_chain(sid, chain_events, state)
        if refusal:
            return ({}, refusal)
        resolved[sid] = resolution

    refusal = _check_cross_chain(resolved, state)
    if refusal:
        return ({}, refusal)
    return (resolved, None)


class _SupersedeState:
    __slots__ = ("dead_p2_positions", "retired_at", "p2s_by_target",
                 "f3_by_target", "f3_by_id")

    def __init__(self) -> None:
        # p2 row position -> position of the P2S that kills it. Liveness
        # is TIME-AWARE: a P2 is live for every row between its own
        # position and its P2S's, which is what makes the P3 that runs
        # BEFORE a later P2S legal.
        self.dead_p2_positions: dict = {}
        self.retired_at: dict = {}         # supplement_id -> F3 pos
        self.p2s_by_target: dict = {}      # target seq -> P2S event
        self.f3_by_target: dict = {}       # target seq -> F3 event
        self.f3_by_id: dict = {}           # supplement_id -> F3 event

    def live_at(self, candidates, pos: int) -> list:
        """The subset of `candidates` still live at document position
        `pos` (a P2 superseded LATER was live here)."""
        return [p for p in candidates
                if self.dead_p2_positions.get(p.pos, pos + 1) > pos]


def _resolve_supersedes(events, by_seq):
    """§D.3.2 P2S (eleven codes) and §D.3.2 F3 (six fail-closed cases)."""
    state = _SupersedeState()

    def bad(ev, code, detail):
        return Refusal(code, detail, seq=ev.seq,
                       supplement_id=ev.supplement_id,
                       line_no=ev.row.line_no)

    for ev in events:
        if ev.short_id not in ("P2S", "F3"):
            continue
        target_seq = int(ev.fields["supersedes_event_sequence"])
        candidates = by_seq.get(target_seq, [])
        is_p2s = ev.short_id == "P2S"

        if is_p2s:
            if target_seq in state.p2s_by_target:
                return (None, bad(ev, "p2s_duplicate_supersede",
                                  f"event sequence {target_seq} is already "
                                  "superseded by an earlier P2S"))
            p2_targets = [c for c in candidates if c.short_id == "P2"]
            if not p2_targets:
                return (None, bad(ev, "p2s_no_target_p2",
                                  f"event sequence {target_seq} is not an "
                                  f"existing {sc.EVENTS['P2'].token} row"))
            if len(candidates) > 1:
                return (None, bad(ev, "p2s_target_ambiguous",
                                  f"event sequence {target_seq} matches "
                                  f"{len(candidates)} rows"))
            target = p2_targets[0]
            if target.pos >= ev.pos:
                return (None, bad(ev, "p2s_forward_reference",
                                  "a P2S must appear after the row it "
                                  "supersedes"))
            if target.supplement_id != ev.supplement_id:
                return (None, bad(ev, "p2s_supplement_id_mismatch",
                                  f"P2S is for {ev.supplement_id} but "
                                  f"sequence {target_seq} authorizes "
                                  f"{target.supplement_id}"))
            retired = state.retired_at.get(target.supplement_id)
            if target.pos in state.dead_p2_positions or (
                    retired is not None and retired < ev.pos):
                return (None, bad(ev, "p2s_target_not_live",
                                  f"the P2 at sequence {target_seq} is no "
                                  "longer live (already superseded or its "
                                  "id retired)"))
            if ev.fields["superseded_authorized_commit"] != target.commit:
                return (None, bad(ev, "p2s_commit_mismatch",
                                  "superseded_authorized_commit does not "
                                  "equal the referenced P2 row's commit"))
            if ev.fields["successor_authorized_commit"] == \
                    ev.fields["superseded_authorized_commit"]:
                return (None, bad(ev, "p2s_successor_equals_superseded",
                                  "successor_authorized_commit equals the "
                                  "superseded commit — nothing changed, so "
                                  "there is nothing to re-authorize"))
            state.p2s_by_target[target_seq] = ev
            state.dead_p2_positions[target.pos] = ev.pos
            continue

        # --- F3 ------------------------------------------------------
        if target_seq in state.f3_by_target:
            return (None, bad(ev, "f3_duplicate_supersede",
                              f"event sequence {target_seq} is already "
                              "superseded by an earlier F3"))
        if not candidates:
            return (None, bad(ev, "f3_no_target_row",
                              f"event sequence {target_seq} is not an "
                              "existing supplement row"))
        if len(candidates) > 1:
            return (None, bad(ev, "f3_target_ambiguous",
                              f"event sequence {target_seq} matches "
                              f"{len(candidates)} rows"))
        target = candidates[0]
        if target.pos >= ev.pos:
            return (None, bad(ev, "f3_forward_reference",
                              "an F3 must appear after the row it "
                              "supersedes"))
        if ev.fields["superseded_supplement_id"] != ev.supplement_id:
            return (None, bad(ev, "f3_supplement_id_mismatch",
                              "superseded_supplement_id does not equal the "
                              "note's bracket id"))
        if target.supplement_id != ev.supplement_id:
            return (None, bad(ev, "f3_target_supplement_id_mismatch",
                              f"sequence {target_seq} belongs to "
                              f"{target.supplement_id}"))
        if ev.fields["superseded_commit"] != target.commit:
            return (None, bad(ev, "f3_commit_mismatch",
                              "superseded_commit does not equal the "
                              "referenced row's commit"))
        successor = ev.fields["successor_supplement_id"]
        if successor == ev.supplement_id:
            return (None, bad(ev, "f3_successor_equals_superseded_id",
                              "ID_REUSE_POLICY=NEVER_AFTER_START — the "
                              "successor may not reuse the retired id"))
        state.f3_by_target[target_seq] = ev
        state.f3_by_id[ev.supplement_id] = ev
        state.retired_at[ev.supplement_id] = ev.pos
    return (state, None)


def _check_global_sequence(rows, events) -> Refusal | None:
    """`SEQUENCE_NAMESPACE=GLOBAL`: a numbered supplement row takes the
    next value of the SAME increasing integer sequence the existing rows
    occupy. Non-supplement rows whose sequence cell is not an integer are
    ignored rather than refused — this parser owns the supplement family
    only, and must never fail closed on an S0 row it does not govern."""
    supplement_positions = {e.pos for e in events if e.row.numbered}
    seen: dict = {}
    highest = None
    for row in rows:
        if not row.numbered or not re.fullmatch(r"[0-9]+", row.seq or ""):
            continue
        value = int(row.seq)
        is_supplement = row.pos in supplement_positions
        if value in seen and is_supplement:
            return Refusal("supplement_seq_duplicate",
                           f"sequence {value} is already used by row at "
                           f"line {seen[value]}",
                           seq=row.seq, line_no=row.line_no)
        if is_supplement:
            # N06 repair. "Increasing" was not enough: at 617f7c3 a
            # supplement row could follow the existing highest (13) with
            # 99 and be accepted, leaving 85 phantom slots in a sequence
            # whose whole job is to make the event chain countable.
            # `SEQUENCE_NAMESPACE=GLOBAL` means the NEXT value, not merely
            # a larger one.
            expected = 1 if highest is None else highest + 1
            if value != expected:
                return Refusal(
                    "supplement_seq_not_next_value",
                    f"sequence {value} is not the next value of the global "
                    f"registry sequence (expected {expected}; highest so "
                    f"far {highest})",
                    seq=row.seq, line_no=row.line_no)
        seen.setdefault(value, row.line_no)
        highest = value if highest is None else max(highest, value)
    return None


def _walk_chain(sid: str, chain_events, state: _SupersedeState):
    """The §D.3.3 state machine for ONE supplement id."""
    def bad(ev, code, detail):
        return Refusal(code, detail, seq=ev.seq, supplement_id=sid,
                       line_no=ev.row.line_no)

    live: list = []
    prev: str = ""
    prev_event: SupplementEvent | None = None
    terminal = ""
    started = False
    consumed_by_p3: set = set()

    for ev in chain_events:
        short = ev.short_id
        if terminal:
            code = "retired_supplement_id_reused" if terminal == "F3" \
                else "event_after_terminal"
            return (None, bad(ev, code,
                              f"{sc.EVENTS[terminal].token} already closed "
                              f"this chain; {ev.token} may not follow"))
        current_live = state.live_at(live, ev.pos)
        # For a P2 row the liveness question is asked BEFORE the generic
        # transition question, because "a second authorization while one
        # is live" is the diagnosis §D.3.5 names
        # (`MULTIPLE_LIVE_P2_FOR_ONE_ID`) and it is the more specific of
        # the two refusals the same row triggers. An explicitly FORBIDDEN
        # edge still wins over both: `F1 -> P2` must be reported as the
        # missing-P2S defect it is, not as a liveness accident.
        if (short == "P2" and current_live and prev != "P2S"
                and not sc.is_forbidden_edge(prev, short)):
            return (None, bad(ev, "multiple_live_p2_for_one_id",
                              "a second authorization while one is still "
                              "live; at most one live P2 per supplement id "
                              "at any time"))
        if not prev:
            if short not in ("P1", "T1"):
                return (None, bad(ev, "chain_does_not_start_at_proposal",
                                  f"a chain starts at a proposal row (P1 or "
                                  f"the T1 successor registration), not "
                                  f"{short}"))
        else:
            code = _edge_code(prev, short, event=ev, started=started)
            if code:
                return (None, bad(ev, code,
                                  f"{prev} -> {short} is not a legal "
                                  "transition (§D.3.3)"))

        if short == "P2":
            if prev == "P2S":
                want = prev_event.fields["successor_authorized_commit"]
                if ev.commit != want:
                    return (None, bad(ev, "p2s_successor_commit_mismatch",
                                      f"the re-authorization must carry the "
                                      f"successor_authorized_commit declared "
                                      f"by the P2S ({want[:12]}...), got "
                                      f"{ev.commit[:12]}..."))
            live = current_live + [ev]
            code = _check_live_p2_uniqueness(len(live),
                                             after_p2s=(prev == "P2S"))
            if code:
                return (None, bad(ev, code, "at most one live P2 per id"))
        elif short == "P2S":
            live = current_live
            code = _check_live_p2_uniqueness(len(live), after_p2s=True)
            if code:
                return (None, bad(ev, code,
                                  "the P2S did not reduce the live "
                                  "authorization set to at most one"))
        elif short == "P3":
            if len(current_live) != 1:
                return (None, bad(ev, "p3_without_live_p2",
                                  f"{len(current_live)} live authorizations "
                                  "at the pre-start boundary; exactly one is "
                                  "required"))
            p2 = current_live[0]
            if not p2.authorized_commit.startswith(ev.commit):
                code = "prestart_commit_change_requires_p2s" if prev == "F1" \
                    else "p3_commit_not_authorized_by_live_p2"
                return (None, bad(ev, code,
                                  f"run commit {ev.commit} is not the live "
                                  f"authorization's commit "
                                  f"{p2.authorized_commit[:12]}… — a "
                                  "pre-start commit change must go "
                                  "F1 -> P2S -> P2(new commit) -> P3, or "
                                  "P2 -> P2S -> P2(new commit) -> P3 when "
                                  "no attempt was made (2026-09-05 "
                                  "amendment)"))
            consumed_by_p3.add(p2.pos)
            started = True

        if sc.EVENTS[short].terminal:
            terminal = short
        prev, prev_event = short, ev

    if prev == "AX":
        return (None, Refusal(
            "ax_treated_as_terminal",
            f"{sc.EVENTS['AX'].token} is NOT a terminal; its only successor "
            f"is {sc.EVENTS['F3'].token}, and without it the chain is "
            "unclosed", supplement_id=sid,
            seq=chain_events[-1].seq, line_no=chain_events[-1].row.line_no))

    live = [p for p in live if p.pos not in state.dead_p2_positions
            and p.pos not in consumed_by_p3]
    if sid in state.retired_at:
        live = []
    resolution = ChainResolution(
        sid, events=chain_events, live_authorizations=live,
        retired=(sid in state.retired_at
                 or any(e.short_id == "AX" for e in chain_events)),
        started=started, terminal=terminal)
    return (resolution, None)


def _check_cross_chain(resolved: Mapping[str, ChainResolution],
                       state: _SupersedeState) -> Refusal | None:
    """`F3 -> T1 -> P2'` spans two ids, so it is checked here rather than
    inside either chain (§D.3.2 T1; `SUCCESSOR_REGISTRATION_REQUIRED=YES`,
    `ID_REUSE_POLICY=NEVER_AFTER_START`)."""
    t1_by_id: dict = {}
    for sid, res in resolved.items():
        for ev in res.events:
            if ev.short_id == "T1":
                t1_by_id[sid] = ev

    for sid, t1 in t1_by_id.items():
        def bad(code, detail):
            return Refusal(code, detail, seq=t1.seq, supplement_id=sid,
                           line_no=t1.row.line_no)
        if t1.fields["successor_supplement_id"] != sid:
            return bad("t1_bracket_id_not_successor_id",
                       f"the successor registration is filed under {sid} but "
                       f"names {t1.fields['successor_supplement_id']!r}")
        predecessor = t1.fields["predecessor_supplement_id"]
        if predecessor == sid:
            return bad("t1_successor_equals_predecessor",
                       "ID_REUSE_POLICY=NEVER_AFTER_START")
        f3 = state.f3_by_id.get(predecessor)
        if f3 is None:
            return bad("t1_predecessor_not_superseded_by_f3",
                       f"{predecessor} has no {sc.EVENTS['F3'].token} row; a "
                       "successor may only be registered after the "
                       "predecessor is superseded")
        if f3.fields["successor_supplement_id"] != sid:
            return bad("t1_predecessor_f3_names_other_successor",
                       f"{predecessor}'s F3 names successor "
                       f"{f3.fields['successor_supplement_id']!r}")
        if int(t1.fields["superseded_at_event"]) != int(f3.seq):
            return bad("t1_superseded_at_event_mismatch",
                       f"superseded_at_event "
                       f"{t1.fields['superseded_at_event']} != the F3 row's "
                       f"sequence {f3.seq}")
        if t1.pos <= f3.pos:
            return bad("t1_forward_reference",
                       "the successor registration must follow the F3 row")

    for sid, f3 in state.f3_by_id.items():
        successor = f3.fields["successor_supplement_id"]
        if successor == "NONE":
            continue
        successor_chain = resolved.get(successor)
        if successor_chain is None:
            continue          # registration still pending: not a defect yet
        t1 = t1_by_id.get(successor)
        if t1 is None or t1.fields["predecessor_supplement_id"] != sid:
            return Refusal(
                "f3_successor_not_registered_by_t1",
                f"{successor} has registry rows but was never registered as "
                f"{sid}'s successor by a T1 row (F3 -> T1 -> P2' is the only "
                "legal post-start retry path)",
                seq=f3.seq, supplement_id=sid, line_no=f3.row.line_no)
    return None


# ===========================================================================
# Entry points
# ===========================================================================

def resolve_supplement_chains_or_raise(text: str) -> Mapping[str,
                                                             ChainResolution]:
    chains, refusal = resolve_supplement_chains(text)
    if refusal:
        refusal.raise_()
    return chains


def resolve_supplement_chain(registry_text: str,
                             supplement_id: str) -> ChainResolution:
    """THE N04 SEAM (`supplement_runner.RESOLVER_SEAM`). Never raises.

    Always returns a `ChainResolution`. `problem` carries any refusal —
    from anywhere in the document, per
    `ANY_CHAIN_DEFECT=REFUSE_WHOLE_RESOLUTION` — and
    `live_authorizations` is then empty. An id with no chain at all
    resolves to an EMPTY, un-started, un-authorized result: the default
    is refusal, never permission.
    """
    try:
        chains, refusal = resolve_supplement_chains(registry_text or "")
    except Exception as exc:                                  # noqa: BLE001
        # Belt and braces: an unexpected internal error must still present
        # as a refusal, never as an exception a caller might treat as
        # "no problem found".
        return ChainResolution(supplement_id,
                               problem=f"resolver_internal_error: {exc!r}",
                               detail="resolution aborted")
    if refusal:
        return ChainResolution(supplement_id, problem=str(refusal),
                               refusal=refusal,
                               detail="whole resolution refused")
    resolution = chains.get(supplement_id)
    if resolution is None:
        return ChainResolution(supplement_id, detail=NOT_AUTHORIZED_NO_CHAIN)
    return resolution


#: `supplement_runner._default_resolver` probes these names in order.
resolve_chain = resolve_supplement_chain


def find_live_authorization(text: str, supplement_id: str) -> tuple:
    """Locate THE live P2 row for one supplement id.

    Returns `(event | None, detail)`. A non-None event means only that a
    format-legal, un-superseded, un-consumed
    `SUPPLEMENT_EXECUTION_AUTHORIZED` row exists in the supplied TEXT. It
    is NOT permission to execute: `ND1_SUPPLEMENT_EXECUTION_AUTHORIZED=NO`
    and every real execution still needs Aaron's own exact sentence bound
    to the full 40-hex commit (`ops/ND1_PROFILE_RATIFICATION.md` §4).
    Zero live rows, a consumed authorization, a retired id or ANY chain
    defect all return None.
    """
    resolution = resolve_supplement_chain(text, supplement_id)
    if resolution.problem:
        return (None, f"NOT AUTHORIZED — {resolution.problem}")
    if not resolution.events:
        return (None, NOT_AUTHORIZED_NO_CHAIN)
    if resolution.retired:
        return (None, f"NOT AUTHORIZED — {supplement_id} was retired")
    live = resolution.live_authorizations
    if len(live) != 1:
        return (None, f"NOT AUTHORIZED — {len(live)} live "
                      f"{sc.EVENTS['P2'].token} row(s) for {supplement_id}; "
                      "exactly one is required")
    return (live[0], "one live authorization row found (grammar only — this "
                     "is not permission to execute)")
