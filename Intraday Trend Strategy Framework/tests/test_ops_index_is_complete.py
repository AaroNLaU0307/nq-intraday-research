"""`ops/README.md` must list every governance record in `ops/`.

An index rots the week after it is written. This is the thing that stops it:
add a file to `ops/` without indexing it and the suite goes red.

WHY AN INDEX AND NOT A REORGANISATION. Measured 2026-08-26: of 52 markdown
files in `ops/`, 47 are referenced from somewhere — 22 of them by PATH from
`src/`, `tests/`, `scripts/`, `qros-state.yaml` or `ops/*.json`. Moving one
of those breaks production code; moving one of the other 25 leaves a dead
link and buys nothing. So the directory stays flat and becomes navigable
instead.
"""
from __future__ import annotations

import json
from pathlib import Path

OPS = Path(__file__).resolve().parent.parent / "ops"
INDEX = OPS / "README.md"
HANDOFF = OPS / "NEXT_HANDOFF.md"

#: The index and the fixed handoff pointer do not index themselves.
_SELF = {"README.md", "NEXT_HANDOFF.md"}


def _ops_documents():
    """Every governance record under ops/, INCLUDING the quarantine subtree.

    Widened on 2026-08-27 when the R5 migration moved ten quarantined files
    into `ops/outcome_quarantine/`. A top-level-only glob would have let
    them fall out of the index silently — the index would still have been
    "complete" while ten records had no entry anywhere. Quarantined records
    are exactly the ones a person most needs the index to locate, because
    they are the ones nobody may go looking for by hand.
    """
    return sorted(OPS.rglob("*.md"))


def test_every_ops_document_appears_in_the_index():
    text = INDEX.read_text(encoding="utf-8")
    missing = sorted(p.name for p in _ops_documents()
                     if p.name not in _SELF and p.name not in text)
    assert not missing, (
        "these ops documents are not in ops/README.md:\n  "
        + "\n  ".join(missing)
        + "\n\nAdd them to the right section. An unindexed governance record "
          "is one nobody will find when it matters.")


def test_the_index_names_no_document_that_no_longer_exists():
    """The other direction: a stale entry sends someone to a dead path."""
    import re

    text = INDEX.read_text(encoding="utf-8")
    named = set(re.findall(r"`([A-Z0-9_][A-Za-z0-9_.-]*\.md)`", text))
    present = {p.name for p in _ops_documents()}
    gone = sorted(n for n in named if n not in present)
    assert not gone, (
        "ops/README.md points at documents that are not there:\n  "
        + "\n  ".join(gone))


def test_the_fixed_handoff_pointer_exists_and_carries_the_off_limits_list():
    """`NEXT_HANDOFF.md` is the answer to "which prompt do I paste".

    It is also the permanent carrier for the off-limits list, because a
    Review Packet is machine-generated and has no field for it — the gap
    that burned a second reviewer seat on 2026-08-26.
    """
    assert HANDOFF.exists(), "the fixed handoff pointer is gone"
    text = HANDOFF.read_text(encoding="utf-8")
    assert "OUTCOME_CARRYING_ARTIFACTS.json" in text
    carriers = json.loads(
        (OPS / "OUTCOME_CARRYING_ARTIFACTS.json").read_text(encoding="utf-8"))
    paths = [e if isinstance(e, str) else e.get("path", "")
             for e in carriers.get("carries_outcome", ())]
    assert any(paths), "the outcome-carrying register yielded no paths"
    for anchor in [p for p in paths if "MASTER_PLAN" in p]:
        assert anchor in text, (
            f"{anchor} is outcome-carrying AND the recovery anchor; "
            "NEXT_HANDOFF.md must warn every reviewer off it by name")


def test_the_index_points_at_the_fixed_handoff_first():
    """Someone opening README.md to find a prompt must be sent straight
    there, not left to scan fifty filenames — which is the complaint this
    whole index exists to answer."""
    head = INDEX.read_text(encoding="utf-8")[:400]
    assert "NEXT_HANDOFF.md" in head
