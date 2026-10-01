"""The quarantine register may lose a path, never an entry.

R5 condition 2 of `dec-remaining-2026-08-26`, ruled by Fable on 2026-08-26
under Aaron's delegation and executed on 2026-08-27: the carve-out permits
editing `path` fields to TRACK a physical migration, and nothing else. Its
exact words: entry identity and carries_outcome status survive under the new
path, the entry count never decreases because of it, and deletion by editing
remains impossible.

That is a promise about a register nobody may quietly shrink, so it needs a
mechanism rather than a habit. This is it.

MEASURED DEFECT IN THIS FILE'S OWN FIRST VERSION. It keyed entries by
basename, and `EXPOSURE_LEDGER.md` and `ops/EXPOSURE_LEDGER.md` share one —
so one silently overwrote the other, and two mutations that should have gone
red passed: blanking an entry's payload, and moving a path outside the
prefix, both landing on the swallowed entry. A guard that cannot see two of
twelve entries is worse than none, because it reports confidently on the
other ten. Matching is now done on the full path.

WHY IT COMPARES AGAINST GIT RATHER THAN A HARDCODED LIST. A list of twelve
paths written here would be a second copy of the register, and the two would
drift. The pre-migration commit already holds the authoritative "before", so
the test reads it out of git. A future migration that drops an entry fails
here however the register is edited; a future legitimate ADDITION passes,
because the rule is "never fewer, never a lost identity", not "exactly
these twelve".

WHAT IT DOES NOT CLAIM. It does not check that quarantined files are still
excluded behaviourally — `test_review_artifacts_are_outcome_clean` does that
by skipping registered paths, and `test_delivery_names_no_quarantined_path`
does it for deliveries. This one guards the register's own integrity across
a path edit.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REGISTER = REPO / "ops" / "OUTCOME_CARRYING_ARTIFACTS.json"

#: The commit immediately before the R5 migration moved ten paths. Its
#: register is the "before" every later state is measured against.
PRE_MIGRATION = "e8243c9"

#: The prefix the migration moved entries into.
QUARANTINE_PREFIX = "ops/outcome_quarantine/"


def _entries(text):
    """The register as a list of (path, payload) — NOT keyed by basename."""
    data = json.loads(text)["carries_outcome"]
    out = []
    for e in data:
        path = e if isinstance(e, str) else e.get("path", "")
        assert path, f"register entry with no path: {e}"
        out.append((path, e.get("restates") if isinstance(e, dict) else None))
    paths = [p for p, _ in out]
    assert len(set(paths)) == len(paths), f"duplicate paths in register: {paths}"
    return out


def _register_at(revision):
    out = subprocess.run(
        ["git", "show", f"{revision}:ops/OUTCOME_CARRYING_ARTIFACTS.json"],
        cwd=REPO, capture_output=True, text=True, encoding="utf-8")
    assert out.returncode == 0, out.stderr
    return _entries(out.stdout)


def _allowed_after(path):
    """Where an entry's path may legally be after a tracked migration:
    exactly where it was, or the same basename under the prefix."""
    return {path, QUARANTINE_PREFIX + path.rsplit("/", 1)[-1]}


def _match(before, after):
    """Map each pre-migration entry to its survivor, by PATH not basename.

    An entry may survive at exactly one of two places, so the mapping is
    unambiguous without ever comparing filenames alone. Consumed survivors
    are removed, which makes the mapping injective — two entries cannot
    both claim the same survivor.

    Returns (pairs, unmatched_before).
    """
    remaining = list(after)
    pairs, lost = [], []
    for old_path, old_payload in before:
        allowed = _allowed_after(old_path)
        hit = next((x for x in remaining if x[0] in allowed), None)
        if hit is None:
            lost.append(old_path)
            continue
        remaining.remove(hit)
        pairs.append(((old_path, old_payload), hit))
    return pairs, lost


def test_no_entry_was_lost_by_the_migration():
    """The carve-out's load-bearing sentence, as a check.

    Deletion by editing `path` must remain impossible — so every entry
    present before the migration still has a survivor, either where it was
    or under the prefix, and nowhere else.
    """
    before = _register_at(PRE_MIGRATION)
    after = _entries(REGISTER.read_text(encoding="utf-8"))
    _pairs, lost = _match(before, after)
    assert not lost, (
        "these entries were in the quarantine register before the migration "
        f"({PRE_MIGRATION}) and have no survivor now:\n  " + "\n  ".join(lost)
        + "\n\nThe carve-out permits editing `path` to track a move — into "
          "the prefix, and nowhere else. It does not permit an entry to "
          "leave, and it does not permit a path to go anywhere else.")


def test_the_entry_count_never_fell():
    before = _register_at(PRE_MIGRATION)
    after = _entries(REGISTER.read_text(encoding="utf-8"))
    assert len(after) >= len(before), (
        f"the register held {len(before)} entries at {PRE_MIGRATION} and "
        f"holds {len(after)} now. Entries are added by ruling and never "
        "removed by editing.")


def test_every_surviving_entry_kept_its_payload():
    """Identity is the `restates` payload, not the path.

    A migration that preserved the filename but blanked what the entry says
    it restates would satisfy a naive count check and still have destroyed
    the entry — the register would name a file and no longer say why it is
    quarantined.
    """
    before = _register_at(PRE_MIGRATION)
    after = _entries(REGISTER.read_text(encoding="utf-8"))
    pairs, _lost = _match(before, after)
    changed = [f"{op}: {opay!r} -> {npay!r}"
               for (op, opay), (_np, npay) in pairs if opay != npay]
    assert not changed, (
        "the migration changed what these entries say they restate, which "
        "the carve-out forbids — only `path` may be edited:\n  "
        + "\n  ".join(changed))


def test_the_prefix_is_not_the_authority():
    """R1's cost, made mechanical.

    A-prime deliberately left both exposure ledgers outside the subtree, so
    a guard that queried the prefix instead of the register would go blind
    to exactly the two most sensitive files in the project. This asserts the
    condition that makes that safe: the register still holds entries the
    prefix does not cover, so nobody can quietly substitute one for the
    other and believe the coverage is equal.
    """
    after = _entries(REGISTER.read_text(encoding="utf-8"))
    outside = [p for p, _ in after if not p.startswith(QUARANTINE_PREFIX)]
    assert outside, (
        "every quarantined path now lives under the prefix. That makes "
        "prefix-matching look equivalent to reading the register, and the "
        "day it stops being equivalent nothing will say so. If this is "
        "deliberate, delete this test in the same commit that proves the "
        "register and the prefix are the same set.")
    assert len(after) > len(outside), (
        "no entry is under the quarantine prefix at all — the migration was "
        "reverted or the register was rebuilt")
