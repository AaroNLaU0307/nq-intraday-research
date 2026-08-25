"""Anti-rollback witness and conflict-copy detection for the trial registry.

Item 7 of `dec-eight-open-2026-08-26`, boundaries (1) and (2). Ruled by
Fable 5 on 2026-08-26 (`DELEGATED=YES`), adopted by Aaron the same day
(`ops/OWNER_DECISIONS_2026-08-26.md`).

WHY THIS EXISTS. `ops/TRIAL_REGISTRY.md` is the event source of truth and it
lives inside an actively OneDrive-synced tree. There is exactly one fatal
outcome — an event that DID happen goes missing while the file stays
well-formed and every gate passes, so the chain concludes the run never
started and authorises a second one. That is a double exposure.

TWO CHANNELS REACH IT, NOT ONE. The ruling text says a half-written row
"dies on the six-cell parse" and calls silent rollback the only fatal
channel. Measured, and it is why this module exists in this shape:

  * `parse_registry_events` CONTINUES past a cell-count mismatch
    (`scripts/s0_real_run.py:183-184`) — a malformed row is silently
    DROPPED, not rejected.
  * `ops/TRIAL_REGISTRY.md` is allowlisted out of the clean gate
    (`:113`, used at `:596`) — a dirty registry never trips `git_clean`.

So a truncated final row is observationally identical to a silent rollback.
The witness is the only interception point both channels pass through:
either one lowers the event count below the recorded witness.

Full failure model and recovery procedure: `ops/REGISTRY_SYNC_FAILURE_MODEL.md`.

NOT WIRED INTO ANY GATE YET, DELIBERATELY. The witness has to live under a
non-synced governed root, and creating anything under
`C:\\Users\\Aaron\\quant-data\\` needs its own authorization that ND1 keeps
separate from every other one. So `witness_path` is a required argument with
no default — this module cannot create, guess, or fall back to a location.
Wiring it into the runner's gate list is the landing step, and it waits on
that authorization.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

#: Returned by `verify_against_witness` when everything lines up.
OK = "OK"

#: The registry lost events relative to the last witness — channel A (sync
#: rollback) or channel B (truncated row). Both land here, which is the
#: whole point.
ROLLBACK = "REGISTRY_ROLLBACK"

#: No witness has ever been recorded. NOT the same as "no rollback": it is
#: the absence of evidence, and L6's rule is that absence renders UNKNOWN,
#: never NONE. A caller gating a trial-consuming run must refuse on it.
WITNESS_ABSENT = "WITNESS_ABSENT"

#: The witness file exists but its last line is not a witness record.
WITNESS_MALFORMED = "WITNESS_MALFORMED"

#: An OneDrive conflict copy of the registry is present.
CONFLICT_COPY = "REGISTRY_CONFLICT_COPY_PRESENT"

_REGISTRY_STEM = "TRIAL_REGISTRY"


def registry_facts(registry_text: str, event_rows) -> dict:
    """The three quantities a witness records, per the ruling.

    `event_rows` is the already-parsed row list — this module never
    re-implements the parser, because a second parser is a second truth and
    the divergence would be invisible. Callers pass
    `parse_registry_events(text)`.
    """
    rows = list(event_rows)
    return {
        "sha256": hashlib.sha256(registry_text.encode("utf-8")).hexdigest(),
        "event_count": len(rows),
        "last_row": _row_identity(rows[-1]) if rows else "",
    }


def _row_identity(row: dict) -> str:
    """A row's identity for superset checking.

    Deliberately NOT the raw line: the note field carries free text that a
    later correction may reflow. Sequence + utc + event is what makes a row
    the row it is.
    """
    return "|".join((str(row.get("seq", "")), str(row.get("utc", "")),
                     str(row.get("event", ""))))


def append_witness(witness_path: Path, facts: dict) -> None:
    """Append one witness record. Append-only, never rewritten.

    The file is opened in append mode with an explicit newline so the bytes
    do not depend on the platform — the same reasoning that governs
    `REGISTRY_AFTER_RUN_STARTED.json` in the run directory.

    Raises `FileNotFoundError` if the parent does not exist. That is
    deliberate: this module NEVER creates a directory. Creating one under
    the governed root is a separately-authorized act, and a helper that
    quietly `mkdir(parents=True)`-ed would be exactly the kind of merge of
    two authorizations that ND1 forbids.
    """
    line = json.dumps(facts, sort_keys=True, ensure_ascii=False)
    with witness_path.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(line + "\n")


def read_last_witness(witness_path: Path):
    """The most recent witness record, or `None` if there is no file.

    Returns `(facts, problem)`. `problem` is `None` on success,
    `WITNESS_ABSENT` when there is nothing to compare against, and
    `WITNESS_MALFORMED` when the tail is not a record. A malformed tail is
    NOT treated as absent — silently degrading a corrupted witness into "no
    witness yet" would turn the loudest possible signal into the quietest.
    """
    if not witness_path.exists():
        return None, WITNESS_ABSENT
    lines = [ln for ln in witness_path.read_text(
        encoding="utf-8").splitlines() if ln.strip()]
    if not lines:
        return None, WITNESS_ABSENT
    try:
        facts = json.loads(lines[-1])
    except ValueError:
        return None, WITNESS_MALFORMED
    if not isinstance(facts, dict) or "event_count" not in facts:
        return None, WITNESS_MALFORMED
    return facts, None


def verify_against_witness(registry_text: str, event_rows,
                           witness_path: Path) -> tuple[str, str]:
    """Fail-closed comparison. Returns `(code, human_reason)`.

    The registry must be a SUPERSET of the last witness:

      * its event count may not be lower, and
      * the witnessed last row must still be present.

    Growth is expected and fine — the registry gains rows between
    witnesses. Shrinking, or losing the witnessed row while the count
    happens to match, is a rollback.
    """
    last, problem = read_last_witness(witness_path)
    if problem is not None:
        return problem, {
            WITNESS_ABSENT: (
                "no witness has been recorded for this registry; absence of "
                "evidence renders UNKNOWN, never NONE"),
            WITNESS_MALFORMED: (
                "the witness file's last line is not a witness record"),
        }[problem]

    rows = list(event_rows)
    if len(rows) < int(last["event_count"]):
        return ROLLBACK, (
            "registry carries %d events; the last witness recorded %d. "
            "Events cannot disappear from an append-only ledger — this is "
            "either a sync rollback or a truncated row."
            % (len(rows), int(last["event_count"])))

    witnessed = str(last.get("last_row", ""))
    if witnessed and witnessed not in {_row_identity(r) for r in rows}:
        return ROLLBACK, (
            "the row the last witness recorded (%s) is absent from the "
            "registry, even though the event count did not fall. The tail "
            "was rewritten, not appended to." % witnessed)

    return OK, "registry is a superset of the last witness"


def find_conflict_copies(ops_dir: Path) -> list[Path]:
    """Boundary (2). Every `TRIAL_REGISTRY*` file that is not the registry.

    Deliberately broader than any specific OneDrive naming scheme. The
    conflict-copy formats vary by client version and locale
    (`-DESKTOP-XXXX`, `(… conflicted copy …)`, `-PC`), and a pattern list
    tuned to the ones seen so far would silently miss the next one. Any
    sibling that starts with the registry's stem is refused and a human
    looks at it.

    This is a NAMED guard for something `git_clean` already catches as an
    untracked file. Naming it is the point: a gate that says
    "REGISTRY_CONFLICT_COPY_PRESENT" tells the operator what happened,
    where "untracked file present" sends them looking for a stray script.
    """
    if not ops_dir.exists():
        return []
    return sorted(
        p for p in ops_dir.iterdir()
        if p.is_file()
        and p.name.startswith(_REGISTRY_STEM)
        and p.name != f"{_REGISTRY_STEM}.md")
