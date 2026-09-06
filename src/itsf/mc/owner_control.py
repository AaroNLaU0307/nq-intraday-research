"""Owner hold and release rows: Aaron's revocation path that needs no code.

QROS-CF v2 §2.3 (DEC-0001, DEC-0006 I2, DEC-0009 Condition B).

THE GAP THIS CLOSES. Under the governed-execution identity an authorization
is voided only by a change of what runs. Astra's finding F06: that left
Aaron no way to stop an authorized run whose code had NOT changed. The
supplement grammar already carries an owner-actor P2S (the revocation of one
authorization); what was missing was a durable, legally-parsed HOLD that
refuses every start until Aaron releases it.

CONDITION B, MEASURED 2026-09-07. `supplement_registry.parse_registry_rows`
parses EVERY six-cell row and the two family grammars skip tokens they do
not own (`SUPPLEMENT_*` and `MC_*`), so a row whose event is `OWNER_HOLD` or
`OWNER_RELEASE` is representable in the registry today without touching
either grammar. Nothing READ such rows, so this module is the minimum
parser support Condition B puts inside I2: it reads them, validates them
fail-closed, and answers one question -- is a hold in force for this id?

ROW SHAPE (six cells, like every other row; NUMBERED, so a release can name
the hold it releases):

    | <seq> | <utc> | OWNER_HOLD    | <commit> | Aaron | [GLOBAL] reason: <text> |
    | <seq> | <utc> | OWNER_RELEASE | <commit> | Aaron | [GLOBAL] releases_event_sequence: <n>; reason: <text> |

The bracket is `GLOBAL` (every id) or one run id (that id only). The actor
cell is exactly `Aaron`: no main-agent form exists for these rows, because
a hold the builder can write is a hold the builder can also forget to
write. A malformed owner row is REFUSED, and a refusal refuses the start:
an owner row nobody can read must never read as "no hold".

THIS MODULE NEVER RESOLVES A CHAIN AND NEVER READS THE REGISTRY FILE. It is
handed text (the gate context's snapshot, or the boundary's re-read at the
seam) and returns rows.
"""
from __future__ import annotations

import dataclasses as _dc
import re

from . import supplement_registry as _sr

__all__ = ["OWNER_HOLD", "OWNER_RELEASE", "OWNER_TOKENS", "OWNER_ACTOR",
           "GLOBAL_SCOPE", "OwnerControlRefusal", "OwnerRow",
           "parse_owner_rows", "active_holds", "assert_no_owner_hold",
           "owner_intent_lines"]

OWNER_HOLD = "OWNER_HOLD"
OWNER_RELEASE = "OWNER_RELEASE"
OWNER_TOKENS = (OWNER_HOLD, OWNER_RELEASE)
OWNER_ACTOR = "Aaron"
GLOBAL_SCOPE = "GLOBAL"

_SCOPE_RE = re.compile(r"^\[(GLOBAL|[A-Z][A-Z0-9-]*)\]\s*(.*)\Z", re.S)
_FIELD_RE = re.compile(r"^([a-z_]+):\s*(.+)\Z", re.S)


class OwnerControlRefusal(Exception):
    """A malformed or inconsistent owner row. Fail-closed by every caller."""

    def __init__(self, code: str, detail: str = "", line_no: int | None = None):
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code
        self.detail = detail
        self.line_no = line_no


@_dc.dataclass(frozen=True)
class OwnerRow:
    seq: int
    utc: str
    token: str
    scope: str
    reason: str
    releases: int | None
    line_no: int


def _fields(remainder: str, line_no: int) -> dict:
    out: dict = {}
    for segment in (s.strip() for s in remainder.split(";")):
        if not segment:
            continue
        m = _FIELD_RE.match(segment)
        if not m:
            raise OwnerControlRefusal("owner_control_row_malformed",
                                      f"note segment {segment!r} is not "
                                      "'key: value'", line_no)
        key, value = m.group(1), m.group(2).strip()
        if key in out:
            raise OwnerControlRefusal("owner_control_row_malformed",
                                      f"duplicate field {key!r}", line_no)
        out[key] = value
    return out


#: A line that LOOKS like a registry row and CARRIES an owner-control token.
#: Deliberately loose: it must match things the shared row parser will NOT
#: yield as a row, because those are exactly the lines that used to vanish.
_OWNER_INTENT_RE = re.compile(
    r"^\s*\|.*(?<![A-Z0-9_])(OWNER_HOLD|OWNER_RELEASE)(?![A-Z0-9_])")


def owner_intent_lines(text: str) -> tuple:
    """`(line_no, token, line)` for every line that ASSERTS owner control.

    Intent is read off the raw text, not off the shared parser's output,
    because the defect this closes is a line the shared parser silently drops.
    """
    out = []
    for i, line in enumerate(text.splitlines(), 1):
        m = _OWNER_INTENT_RE.match(line)
        if m:
            out.append((i, m.group(1), line))
    return tuple(out)


def parse_owner_rows(text: str) -> tuple:
    """Every OWNER_* row in `text`, validated. Other rows are ignored.

    OWNER-CONTROL INTENT FAILS CLOSED (QROS-CF F05). The shared row parser
    skips lines it cannot read as six-cell rows -- correct for prose, fatal
    for an owner's hold: reproduced 2026-09-07, a hold with a missing final
    pipe, an extra pipe inside the reason, or the wrong cell count returned
    NO ACTIVE HOLDS and a start could proceed. So before anything is
    ignored, every line carrying a recognizable owner-control token must
    have produced a validated owner row; a line that did not is a deterministic
    refusal, not silence.

    No second parser and no parallel ledger: the intent scan decides only
    WHICH lines must be accounted for, and the shared parser still does all
    the reading.
    """
    intents = owner_intent_lines(text)
    rows, refusal = _sr.parse_registry_rows(text)
    if refusal is not None:
        raise OwnerControlRefusal("owner_control_registry_unparseable",
                                  f"{refusal.code}: {refusal.detail}",
                                  getattr(refusal, "line_no", None))
    readable_lines = {row.line_no for row in rows
                      if row.event.strip("*").strip() in OWNER_TOKENS}
    for line_no, token, _line in intents:
        if line_no not in readable_lines:
            raise OwnerControlRefusal(
                "owner_control_row_unreadable",
                f"line {line_no} carries {token} but the registry row parser "
                "cannot read it as an owner-control row; an owner-control "
                "line is never ignored",
                line_no)
    out = []
    holds_by_seq: dict = {}
    released: set = set()
    for row in rows:
        token = row.event.strip("*").strip()
        if token not in OWNER_TOKENS:
            continue
        if (row.actor or "").strip() != OWNER_ACTOR:
            raise OwnerControlRefusal(
                "owner_control_actor_not_owner",
                f"{token} actor must be exactly {OWNER_ACTOR!r}; got "
                f"{row.actor!r}", row.line_no)
        if not re.fullmatch(r"[0-9]+", (row.seq or "").strip()):
            raise OwnerControlRefusal(
                "owner_control_row_malformed",
                f"{token} must be a NUMBERED row so a release can name it; "
                f"seq cell is {row.seq!r}", row.line_no)
        seq = int(row.seq)
        m = _SCOPE_RE.match(row.note.strip())
        if not m:
            raise OwnerControlRefusal(
                "owner_control_row_malformed",
                f"{token} note must start with [GLOBAL] or [<run id>]",
                row.line_no)
        scope, remainder = m.group(1), m.group(2).strip()
        fields = _fields(remainder, row.line_no)
        reason = fields.get("reason", "").strip()
        if not reason:
            raise OwnerControlRefusal("owner_control_row_malformed",
                                      f"{token} carries no reason", row.line_no)
        releases = None
        if token == OWNER_RELEASE:
            target = fields.get("releases_event_sequence", "").strip()
            if not re.fullmatch(r"[0-9]+", target):
                raise OwnerControlRefusal(
                    "owner_control_row_malformed",
                    "OWNER_RELEASE must name releases_event_sequence",
                    row.line_no)
            releases = int(target)
            hold = holds_by_seq.get(releases)
            if hold is None:
                raise OwnerControlRefusal(
                    "owner_control_release_without_hold",
                    f"OWNER_RELEASE at seq {seq} releases event {releases}, "
                    "which is not an earlier OWNER_HOLD", row.line_no)
            if hold.scope != scope:
                raise OwnerControlRefusal(
                    "owner_control_release_scope_mismatch",
                    f"OWNER_RELEASE scope [{scope}] != the hold's [{hold.scope}]",
                    row.line_no)
            if releases in released:
                raise OwnerControlRefusal(
                    "owner_control_release_twice",
                    f"OWNER_HOLD {releases} is already released", row.line_no)
            released.add(releases)
        if seq in holds_by_seq or any(r.seq == seq for r in out):
            raise OwnerControlRefusal("owner_control_seq_duplicate",
                                      f"sequence {seq} used twice by owner rows",
                                      row.line_no)
        parsed = OwnerRow(seq, row.utc, token, scope, reason, releases,
                          row.line_no)
        if token == OWNER_HOLD:
            holds_by_seq[seq] = parsed
        out.append(parsed)
    return tuple(out)


def active_holds(text: str, run_id: str) -> tuple:
    """Unreleased holds whose scope is GLOBAL or exactly `run_id`."""
    rows = parse_owner_rows(text)
    released = {r.releases for r in rows if r.token == OWNER_RELEASE}
    return tuple(r for r in rows
                 if r.token == OWNER_HOLD and r.seq not in released
                 and r.scope in (GLOBAL_SCOPE, run_id))


def assert_no_owner_hold(text: str, run_id: str) -> None:
    """Raise `OwnerControlRefusal('owner_hold_in_force')` if a hold applies.
    A malformed owner row raises its own code -- also a refusal."""
    holds = active_holds(text, run_id)
    if holds:
        last = holds[-1]
        raise OwnerControlRefusal(
            "owner_hold_in_force",
            f"OWNER_HOLD seq {last.seq} [{last.scope}] {last.utc}: {last.reason}",
            last.line_no)
