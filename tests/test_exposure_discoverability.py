"""Both exposure axes must be discoverable from the live artifacts.

D-1 condition 1, ruled by Fable 5 on 2026-08-26 (`DELEGATED=YES`) over the
four-item decision packet. The ruling was A — do NOT add a pointer row to
`ops/EXPOSURE_LEDGER.md` — on the ground that a pointer row supplies
DISCOVERABILITY, not information, and discoverability can be had
mechanically without touching an append-only ledger or amending a ratified
"exactly one" invariant.

This file is the "mechanically". Without it the ruling rests on people
remembering there are two ledgers, which is the thing it was chosen to
avoid.

THE TWO AXES ARE NOT THE SAME QUANTITY.

  research axis  ops/EXPOSURE_LEDGER.md        consumes the study's degrees
                                               of freedom
  seat axis      ops/REVIEWER_EXPOSURE_LOG.md  a reviewer seat is burned and
                                               cannot serve blind again

Burning a seat costs no degrees of freedom. Filing them on one axis would
invent a researcher exposure that never happened — which is why they are
separate, and why finding one must lead to the other.

WHY THE POINTERS ARE COMMENTS. `outcome_exposure.scope` is a closed runtime
enum and the block rejects unknown sibling fields — measured: adding
`ledgers:` was refused with `OUTCOME_EXPOSURE_SHAPE`. So the pointers live
in YAML comments beside it, and the enforcement lives here.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
STATE = REPO / "qros-state.yaml"
HANDOFF = REPO / "ops" / "NEXT_HANDOFF.md"
QUARANTINE = REPO / "ops" / "OUTCOME_CARRYING_ARTIFACTS.json"

RESEARCH_AXIS = "ops/EXPOSURE_LEDGER.md"
SEAT_AXIS = "ops/REVIEWER_EXPOSURE_LOG.md"


def test_the_state_file_names_both_ledgers():
    """`qros-state.yaml` declares this project's exposure state. A reader
    who finds it must be led to BOTH axes, not just the one `scope` speaks
    for."""
    text = STATE.read_text(encoding="utf-8")
    for axis, label in ((RESEARCH_AXIS, "research"), (SEAT_AXIS, "seat")):
        assert axis in text, (
            f"qros-state.yaml does not name the {label} axis ledger "
            f"({axis}). D-1 was ruled A on the basis that discoverability "
            "would be mechanical; this is where that promise is kept.")


def test_the_live_handoff_carrier_names_both_ledgers():
    """The other live artifact that states exposure posture is the thing
    handed to reviewers. A seat told about one axis and not the other
    cannot report its own position correctly."""
    text = HANDOFF.read_text(encoding="utf-8")
    for axis in (RESEARCH_AXIS, SEAT_AXIS):
        assert axis in text, (
            f"{HANDOFF.name} does not name {axis}")


def test_the_seat_ledger_is_inside_the_outcome_clean_scan():
    """D-1 condition 2, verified rather than assumed.

    The seat ledger records what reviewers saw. If it ever starts
    restating a quarantined value it must be caught like anything else —
    so it has to be inside the scanner's reach and not on its self-exclusion
    list."""
    import test_review_artifacts_are_outcome_clean as clean

    scanned = {p.relative_to(clean.REPO).as_posix()
               for p in clean.REPO.rglob("*.md")}
    assert SEAT_AXIS in scanned, "the seat ledger is outside the scan"
    assert SEAT_AXIS not in clean._SELF, (
        "the seat ledger is on the scanner's self-exclusion list; it must "
        "be scanned like any other document")


def test_the_seat_ledger_is_not_quarantined():
    """It exists to BE READ — by Aaron, and by anyone checking whether a
    seat is still blind. Quarantining it would defeat its purpose, and D-1
    chose A partly to avoid exactly that outcome.

    If this ever fails, the seat ledger has started carrying a restating
    value and the fix is to remove the restatement, NOT to quarantine the
    ledger."""
    entries = json.loads(QUARANTINE.read_text(encoding="utf-8"))
    paths = {e if isinstance(e, str) else e.get("path", "")
             for e in entries["carries_outcome"]}
    assert any(paths), "the quarantine register yielded no paths"
    assert SEAT_AXIS not in paths, (
        "the seat-exposure ledger has been quarantined — the log that says "
        "which seats are burned is now unreadable to the seats that need "
        "to know. Remove the restating text instead.")
