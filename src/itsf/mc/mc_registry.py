"""The MC run registry — parser, validator and chain resolver (G1..G8).

WHAT THIS OWNS, AND HOW OWNERSHIP IS DECIDED. Every row in
`ops/TRIAL_REGISTRY.md` whose event token starts with `MC_`. Ownership is by
PREFIX, not by membership in the ratified sixteen, and that distinction is
the whole fail-closed property: a token inside this prefix that this grammar
does not know is REFUSED, never skipped. A parser that owns only what it
recognises leaves `MC_RUN_AUTHORIZEDD` belonging to nobody, and a row
belonging to nobody is a row that passes.

Rows outside the prefix belong to other lifecycles — S0-T001's own chain,
the day-strata supplement — and are skipped, because one registry file
carries all of them. Skipping a foreign row is not permissiveness; it is the
only way a shared file can work at all.

WHAT IT REUSES AND WHAT IT REFUSES TO REUSE. The six-cell row scan and the
`[id] key: value; ...` note shape are the FILE FORMAT, shared by every
lifecycle in the file by construction, so `parse_registry_rows` is called
rather than re-implemented — a second scanner over the same bytes is a
second thing to keep in agreement. The VOCABULARY is not shared: nothing
here consults `supplement_contract`, and `mc_contract` names its own sixteen
events. Follow the shape; do not assume identity.

A CONTRADICTION THAT WAS OPEN, AND HOW IT CLOSED. G8 puts these rows in
`ops/TRIAL_REGISTRY.md`. The N05 supplement grammar refused
`MC_RUN_AUTHORIZED` and `MC_RUN_STARTED` BY NAME, totally
(`ANY_CHAIN_DEFECT=REFUSE_WHOLE_RESOLUTION`). Both were ratified, and
together they were not implementable: the day-strata supplement is an INPUT
to the MC run, so the first real MC run would have broken the mechanism
proving its own input was authorized.

Resolved 2026-08-25 as `MC-REG-COLLISION-001` — Fable proposed R2, a fresh
Sol ratified it with modifications, Aaron adjudicated. `DELEGATED=YES`.
§D.3.4's deferral carried its own discharge condition ("before the N-D3
ruling") and its own reason (incomplete lifecycle definitions); N-D3
supplied the definitions, so the guard was discharged on its own terms
rather than weakened. Exactly two names moved; the ratified five-name
transcription stays verifiable behind an explicit exclusion.

What replaced the by-name refusal is STRICTER, and it is not in this module:
`registry_boundary` reads the registry once and runs both lifecycles against
that single immutable snapshot, so a broken MC record makes the file
unusable for the supplement lifecycle too. Sol's own modification — Fable's
version would have let each reader take its own read of a mutable file, and
four such reads existed. Nothing may read that path or call either resolver
outside the boundary; the exceptions are unconditional-refusal stubs, proved
to refuse by calling them.

Records: `ops/DECISION_MC_REGISTRY_COLLISION.md`,
`ops/RULING_MC_REG_COLLISION_SOL_RATIFICATION_2026-08-25.md`.

DEFAULT REFUSE, EVERYWHERE. A missing chain is not a permissive default; a
malformed element refuses the whole resolution rather than the one row; and
zero live authorizations means NOT AUTHORIZED, never "no objection".
"""
from __future__ import annotations

import dataclasses as _dc
import re
from types import MappingProxyType

from itsf.mc import mc_contract as mcc
#: FILE-FORMAT layer only — the six-cell row scan and the field separator.
#: No vocabulary, no event spec and no refusal code crosses this import.
from itsf.mc import supplement_registry as _fmt

__all__ = ["McRefusal", "McEvent", "McChain", "MC_PREFIX", "REFUSAL_CODES",
           "is_mc_row", "parse_mc_events", "resolve_mc_chains",
           "find_live_mc_authorization", "NOT_AUTHORIZED_NO_CHAIN"]

MC_PREFIX = "MC_"

NOT_AUTHORIZED_NO_CHAIN = (
    "no MC event chain exists for this run id — NOT AUTHORIZED (default "
    "refuse; a missing chain is never a permissive default)")


@_dc.dataclass(frozen=True)
class McRefusal:
    code: str
    detail: str = ""
    seq: str = ""
    run_id: str = ""
    line_no: int = 0

    def __str__(self) -> str:                          # pragma: no cover
        where = f" (line {self.line_no}, seq {self.seq})" if self.line_no \
            else ""
        return f"{self.code}: {self.detail}{where}"


@_dc.dataclass(frozen=True)
class McEvent:
    """A registry row classified as one of the ratified sixteen."""
    token: str
    run_id: str
    seq: str
    utc: str
    commit: str
    actor: str
    fields: object = _dc.field(default_factory=dict)
    line_no: int = 0
    pos: int = 0


@_dc.dataclass(frozen=True)
class McChain:
    """One run id's events in file order, plus its live authorizations."""
    run_id: str
    events: tuple
    live_authorizations: tuple = ()


REFUSAL_CODES = frozenset({
    "mc_row_malformed",
    "mc_unknown_event_token",
    "mc_note_bracket_missing",
    "mc_run_id_malformed",
    "mc_note_segment_not_field",
    "mc_duplicate_field_in_note",
    "mc_field_value_empty",
    "mc_missing_conditional_field",
    "mc_unknown_field_in_note",
    "mc_commit_malformed",
    "mc_actor_not_aaron",
    "mc_seq_not_integer",
    "mc_seq_duplicate",
    "mc_seq_not_next_value",
    "mc_smoke_ref_malformed",
    "mc_authorization_sentence_mismatch",
    "mc_utc_malformed",
    "mc_illegal_transition",
    "mc_chain_starts_mid_lifecycle",
    "mc_run_id_reused_after_start",
    "mc_supersede_note_unparsable",
    "mc_supersede_target_missing",
    "mc_supersede_target_ambiguous",
    "mc_supersede_forward_reference",
    "mc_supersede_duplicate",
    "mc_supersede_commit_mismatch",
})

_MC_TOKEN_SCAN_RE = re.compile(r"(?<![A-Z0-9_])(MC_[A-Z0-9_]+)")
_NOTE_BRACKET_RE = re.compile(r"^\[\s*([^\]]*?)\s*\]\s*(.*)$", re.S)
_FIELD_RE = re.compile(r"^([a-z][a-z0-9_]*)\s*:\s*(.*)$", re.S)
_UTC_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T"
                     r"[0-9]{2}:[0-9]{2}:[0-9]{2}Z\Z")

#: Fields any MC row may carry beyond its conditional set. Kept short on
#: purpose: an open note is an unvalidated note.
_ALWAYS_ALLOWED_FIELDS = ("run_id", "doc", "aaron_ruling_doc")


def is_mc_row(row) -> bool:
    """Prefix ownership. See the module docstring: this is the property
    that makes an unknown `MC_*` token refusable rather than orphaned."""
    return row.event.startswith(MC_PREFIX)


# ===========================================================================
# Stage 1 — rows
# ===========================================================================

def _malformed_mc_line(text: str):
    """Policy B over the WHOLE `MC_` prefix.

    The shared stage-1 scan already refuses a malformed row-shaped line
    carrying `SUPPLEMENT_*` or `MC_RUN_*`. It does not cover `MC_BRANCH_*`,
    `MC_PACKET_*` or `MC_ERRATUM`, which did not exist when it was written —
    so a broken `MC_BRANCH_SEALED` line would be dropped silently. This
    closes the prefix.
    """
    in_fence = False
    for line_no, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        # A row-shaped line inside a fence is documentation, never an event,
        # and therefore never malformed — the rule stage 1 already applies.
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or not stripped.startswith("|"):
            continue
        found = _MC_TOKEN_SCAN_RE.findall(stripped)
        if not found:
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if stripped.endswith("|") and len(cells) == 6:
            continue                                    # well-formed enough
        return McRefusal(
            "mc_row_malformed",
            f"row-shaped line carries MC token(s) {sorted(set(found))} but "
            "violates the six-cell row contract; the row is refused rather "
            "than silently dropped",
            line_no=line_no)
    return None


# ===========================================================================
# Stage 2 — events
# ===========================================================================

def _parse_note(row):
    """`[MC-R001] k: v; k: v` -> `(run_id, fields, refusal)`."""
    def no(code, detail, rid=""):
        return ("", {}, McRefusal(code, detail, seq=row.seq, run_id=rid,
                                  line_no=row.line_no))

    m = _NOTE_BRACKET_RE.match((row.note or "").strip())
    if not m:
        return no("mc_note_bracket_missing",
                  "an MC row's note must open with `[<run_id>]`; without it "
                  "the row belongs to no run and cannot be chained")
    run_id, remainder = m.group(1), m.group(2).strip()
    if not mcc.RUN_ID_RE.match(run_id):
        return no("mc_run_id_malformed",
                  f"{run_id!r} is not MC-R### (mc_contract.RUN_ID_RE)")

    fields: dict = {}
    for raw in remainder.split(_fmt.FIELD_SEPARATOR):
        seg = raw.strip()
        if not seg:
            continue                                # tolerate a trailing ';'
        fm = _FIELD_RE.match(seg)
        if not fm:
            return no("mc_note_segment_not_field",
                      f"{seg!r} is not a `key: value` field; MC notes are "
                      "machine-parsed so that missing and unknown fields can "
                      "be refused rather than guessed", run_id)
        key, value = fm.group(1), fm.group(2).strip()
        if key in fields:
            return no("mc_duplicate_field_in_note",
                      f"field {key!r} appears twice", run_id)
        if not value:
            return no("mc_field_value_empty",
                      f"field {key!r} has an empty value", run_id)
        fields[key] = value
    return (run_id, fields, None)


def _classify(row):
    """One `RegistryRow` -> `(McEvent, None)` or `(None, McRefusal)`."""
    def no(code, detail, rid=""):
        return (None, McRefusal(code, detail, seq=row.seq, run_id=rid,
                                line_no=row.line_no))

    token = row.event
    if token not in mcc.EVENTS:
        # Prefix ownership: inside `MC_`, unknown is refused, not skipped.
        return no("mc_unknown_event_token",
                  f"{token!r} carries the MC prefix but is not one of the "
                  f"ratified sixteen (G1); legal tokens are "
                  f"{list(mcc.EVENTS)} — no best-effort parse")

    run_id, fields, refusal = _parse_note(row)
    if refusal:
        return (None, refusal)

    if not mcc.COMMIT_RE.match((row.commit or "").strip()):
        return no("mc_commit_malformed",
                  f"{row.commit!r} is not 40 lowercase hex; an abbreviated "
                  "commit binds nothing", run_id)
    if not _UTC_RE.match((row.utc or "").strip()):
        return no("mc_utc_malformed",
                  f"{row.utc!r} is not `YYYY-MM-DDThh:mm:ssZ`", run_id)
    if token in mcc.AARON_ONLY_EVENTS \
            and (row.actor or "").strip() != mcc.ACTOR_AARON:
        return no("mc_actor_not_aaron",
                  f"actor {row.actor!r} is not {mcc.ACTOR_AARON!r} — G1 "
                  "reuses S0-T001's actual history, in which only Aaron "
                  "authorizes a run", run_id)

    required = mcc.CONDITIONAL_FIELDS[token]
    missing = [k for k in required if k not in fields]
    if missing:
        return no("mc_missing_conditional_field",
                  f"{token} requires {list(required)}; missing {missing}",
                  run_id)
    if token == "MC_RUN_AUTHORIZED":
        # REBUILD, do not compare a transported string to itself. The
        # sentence is re-derived from the run id in the bracket, the commit
        # in the commit cell and smoke_ref in the note, so a row can only
        # pass by carrying the sentence those three actually produce.
        try:
            expected = mcc.authorization_sentence(
                run_id, row.commit.strip(), fields["smoke_ref"])
        except mcc.MCGrammarError as exc:
            return no("mc_smoke_ref_malformed", str(exc), run_id)
        if fields["authorization_sentence"] != expected:
            return no("mc_authorization_sentence_mismatch",
                      "the row's authorization_sentence is not the sentence "
                      "this run id, this commit and this smoke_ref produce; "
                      "a row that merely says AUTHORIZED is not an "
                      "authorization", run_id)

    allowed = set(required) | set(_ALWAYS_ALLOWED_FIELDS)
    unknown = sorted(k for k in fields if k not in allowed)
    if unknown:
        return no("mc_unknown_field_in_note",
                  f"{token} does not carry {unknown}; an unvalidated field "
                  "in a governance row is a field nobody checked", run_id)

    return (McEvent(token=token, run_id=run_id, seq=row.seq,
                    utc=row.utc.strip(), commit=row.commit.strip(),
                    actor=(row.actor or "").strip(),
                    fields=MappingProxyType(dict(fields)),
                    line_no=row.line_no, pos=row.pos), None)


def parse_mc_events(text: str):
    """Registry text -> `(events, refusal)`. Row-level validation only."""
    bad = _malformed_mc_line(text)
    if bad:
        return ((), bad)
    rows, refusal = _fmt.parse_registry_rows(text)
    if refusal:
        # A stage-1 refusal from the shared scanner is surfaced under this
        # grammar's own code, so a caller never has to know which module
        # produced it — but the original detail travels intact.
        return ((), McRefusal("mc_row_malformed", str(refusal),
                              line_no=getattr(refusal, "line_no", 0)))
    events: list = []
    for row in rows:
        if not is_mc_row(row):
            continue                             # another lifecycle's row
        event, refusal = _classify(row)
        if refusal:
            return ((), refusal)
        events.append(event)
    return (tuple(events), None)


# ===========================================================================
# Stage 3 — chains
# ===========================================================================

def _resolve_supersedes(events, all_by_seq):
    """G4's pre-start loop: which `MC_RUN_AUTHORIZED` rows are still live.

    Verbatim in shape from S0-T001's `resolve_authorizations`, which G1
    ratifies reusing: live = every format-legal AUTHORIZED row minus those
    PRECISELY referenced by a format-legal SUPERSEDED row. Every malformed
    element fails the whole chain closed — a supersede nobody can resolve
    must never leave the row it aimed at looking live.
    """
    auth = [e for e in events if e.token == "MC_RUN_AUTHORIZED"]
    superseded_positions: set = set()
    seen_targets: set = set()

    for event in events:
        if event.token != "MC_RUN_AUTHORIZATION_SUPERSEDED":
            continue
        target_seq = event.fields.get("supersedes_event_sequence", "")
        if target_seq in seen_targets:
            return ((), McRefusal(
                "mc_supersede_duplicate",
                f"event sequence {target_seq} is superseded twice; the "
                "second supersede has no live row to act on",
                seq=event.seq, run_id=event.run_id, line_no=event.line_no))
        seen_targets.add(target_seq)

        targets = [a for a in auth if a.seq == target_seq]
        if not targets:
            return ((), McRefusal(
                "mc_supersede_target_missing",
                f"supersede references event sequence {target_seq}, which "
                "is not an MC_RUN_AUTHORIZED row in this chain",
                seq=event.seq, run_id=event.run_id, line_no=event.line_no))
        if len(targets) > 1:
            return ((), McRefusal(
                "mc_supersede_target_ambiguous",
                f"supersede reference {target_seq} matches "
                f"{len(targets)} rows",
                seq=event.seq, run_id=event.run_id, line_no=event.line_no))
        target = targets[0]
        if target.pos >= event.pos:
            return ((), McRefusal(
                "mc_supersede_forward_reference",
                "a supersede must appear after the row it supersedes",
                seq=event.seq, run_id=event.run_id, line_no=event.line_no))
        if event.fields.get("superseded_commit", "") != target.commit:
            return ((), McRefusal(
                "mc_supersede_commit_mismatch",
                "superseded_commit does not equal the referenced row's "
                "authorized commit; a supersede that names a different "
                "commit has not identified the authorization it retires",
                seq=event.seq, run_id=event.run_id, line_no=event.line_no))
        superseded_positions.add(target.pos)

    live = tuple(a for a in auth if a.pos not in superseded_positions)
    return (live, None)


def _walk(run_id: str, events):
    """Transition legality and the two id rules (G5/G6)."""
    # An erratum corrects a row rather than advancing the lifecycle, so it
    # is validated like any other row and excluded from the ordering. Left
    # in the walk, every correction would read as an illegal transition.
    events = [e for e in events if e.token not in mcc.OUT_OF_CHAIN]
    if not events:
        return None
    first = events[0]
    if first.token != "MC_PACKET_DRAFTED":
        return McRefusal(
            "mc_chain_starts_mid_lifecycle",
            f"the first row for {run_id} is {first.token}; a chain that "
            "starts mid-lifecycle has no evidence for the steps it skipped",
            seq=first.seq, run_id=run_id, line_no=first.line_no)

    started = False
    for prev, cur in zip(events, events[1:]):
        if (prev.token, cur.token) not in mcc.LEGAL_TRANSITIONS:
            return McRefusal(
                "mc_illegal_transition",
                f"{prev.token} -> {cur.token} is not a legal MC transition "
                "(G1)", seq=cur.seq, run_id=run_id, line_no=cur.line_no)
        # G5/G6. Once STARTED, the id is spent: it was bound to one
        # decisive execution by the authorization sentence and the exposure
        # slot, so a re-authorization under it would break the map from
        # sealed bytes to execution.
        if prev.token == "MC_RUN_STARTED" or started:
            started = True
            if cur.token in ("MC_RUN_AUTHORIZED", "MC_RUN_STARTED"):
                return McRefusal(
                    "mc_run_id_reused_after_start",
                    f"{run_id} is re-{cur.token.split('_')[-1].lower()} "
                    "after MC_RUN_STARTED; "
                    f"ID_REUSE_FORBIDDEN={mcc.ID_REUSE_FORBIDDEN} and "
                    "POSTSTART_FAILURE_REQUIRES_NEW_ID="
                    f"{mcc.POSTSTART_FAILURE_REQUIRES_NEW_ID} — a re-run "
                    "takes a new id", seq=cur.seq, run_id=run_id,
                    line_no=cur.line_no)
    return None


def _check_global_sequence(rows, mc_positions):
    """`SEQUENCE_NAMESPACE=GLOBAL` — the same rule, applied to MC rows.

    MEASURED, 2026-08-25, and the reason this exists. The supplement
    grammar enforces that a numbered row takes the NEXT value of the
    sequence every numbered row in the file occupies, and it computes
    "highest so far" over ALL numbered rows, foreign ones included. An MC
    row landing at 99 after a file whose highest is 2 therefore wedges every
    future numbered supplement row with `supplement_seq_not_next_value` —
    reproduced, not reasoned about.

    The rule is a property of the FILE, not of either grammar, and it is
    already ratified. It reads the same whether MC rows share
    `ops/TRIAL_REGISTRY.md` or get their own file, so applying it here does
    not presume how `MC-REG-COLLISION-001` is resolved.

    Rows outside the MC family whose sequence cell is not an integer are
    ignored rather than refused: this parser owns the MC family only and
    must never fail closed on a row it does not govern.
    """
    seen: dict = {}
    highest = None
    for row in rows:
        is_mc = row.pos in mc_positions
        if not re.fullmatch(r"[0-9]+", (row.seq or "").strip()):
            if is_mc:
                return McRefusal(
                    "mc_seq_not_integer",
                    f"{row.seq!r} is not an integer sequence value; every "
                    "row in S0-T001's actual history is numbered and G1 "
                    "reuses it", seq=row.seq, line_no=row.line_no)
            continue                       # another family's unnumbered row
        value = int(row.seq)
        if is_mc:
            if value in seen:
                return McRefusal(
                    "mc_seq_duplicate",
                    f"sequence {value} is already used by the row at line "
                    f"{seen[value]}", seq=row.seq, line_no=row.line_no)
            expected = 1 if highest is None else highest + 1
            if value != expected:
                return McRefusal(
                    "mc_seq_not_next_value",
                    f"sequence {value} is not the next value of the global "
                    f"registry sequence (expected {expected}; highest so "
                    f"far {highest}). A gap leaves phantom slots in a "
                    "sequence whose whole job is to make the event chain "
                    "countable, and it wedges the next numbered row of "
                    "every other lifecycle in the file",
                    seq=row.seq, line_no=row.line_no)
        seen.setdefault(value, row.line_no)
        highest = value if highest is None else max(highest, value)
    return None


def resolve_mc_chains(text: str):
    """Registry text -> `({run_id: McChain}, refusal)`.

    ANY chain defect refuses the WHOLE resolution and returns no chains.
    Returning the chains that happened to parse would let a caller act on a
    file whose governance record is known to be broken.
    """
    events, refusal = parse_mc_events(text)
    if refusal:
        return ({}, refusal)
    if not events:
        return ({}, None)

    # The sequence namespace is the FILE's, so this walks every row --
    # including the ones other lifecycles own.
    rows, row_refusal = _fmt.parse_registry_rows(text)
    if row_refusal:                                   # pragma: no cover
        return ({}, McRefusal("mc_row_malformed", str(row_refusal)))
    refusal = _check_global_sequence(rows, {e.pos for e in events})
    if refusal:
        return ({}, refusal)

    by_run: dict = {}
    for event in events:
        by_run.setdefault(event.run_id, []).append(event)

    all_by_seq = {e.seq: e for e in events}
    chains: dict = {}
    for run_id, chain_events in sorted(by_run.items()):
        problem = _walk(run_id, chain_events)
        if problem:
            return ({}, problem)
        live, refusal = _resolve_supersedes(chain_events, all_by_seq)
        if refusal:
            return ({}, refusal)
        chains[run_id] = McChain(run_id=run_id,
                                 events=tuple(chain_events),
                                 live_authorizations=live)
    return (chains, None)


def find_live_mc_authorization(text: str, run_id: str):
    """G1's LIVE semantics -> `(event | None, commit, detail)`.

    `commit` is non-empty ONLY when exactly one live `MC_RUN_AUTHORIZED`
    row exists for this run id. Zero live rows means NOT AUTHORIZED. More
    than one, or any malformed chain element, fails CLOSED — two live
    authorizations do not mean the newer one wins; they mean the registry
    does not say which run is authorized.
    """
    chains, refusal = resolve_mc_chains(text)
    if refusal:
        return (None, "", str(refusal))
    chain = chains.get(run_id)
    if chain is None:
        return (None, "", NOT_AUTHORIZED_NO_CHAIN)
    live = chain.live_authorizations
    if not live:
        return (None, "", f"{run_id}: no live MC_RUN_AUTHORIZED row — the "
                          "authorization sentence has not been issued, or "
                          "every issuance has been superseded")
    if len(live) > 1:
        return (None, "", f"{run_id}: {len(live)} live MC_RUN_AUTHORIZED "
                          "rows; exactly one is required and a tie is "
                          "refused rather than broken")
    return (live[0], live[0].commit, "ok")
