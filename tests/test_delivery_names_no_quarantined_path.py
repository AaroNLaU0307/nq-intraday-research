"""A live delivery may not point a reviewer at a quarantined file.

THE RULE ALREADY EXISTED AND NOTHING ENFORCED IT. `ops/NEXT_HANDOFF.md`
says, in as many words: before handing anything over, intersect every
`ops/...md` path the document names with
`ops/OUTCOME_CARRYING_ARTIFACTS.json`, and stop if the intersection is not
empty. It even names the mechanical way to do it.

There was no mechanism. This is it.

WHAT IT COST. `ops/DECISION_PACKET_FOUR_OPEN_2026-08-26.md` carried the
off-limits list in one section and, in another, told the reviewer to reuse
the format of `ops/RULING_PROPOSAL_ND2_ND3_FABLE_2026-08-24.md` — which is
on the list. Prohibition and instruction contradicting each other inside
one document. Fable checked the register first and was not burned; that was
the reviewer being careful, not the delivery being correct. Three seats
have been burned in this project and two of them never deliberately opened
anything.

WHAT IT CAUGHT ON ITS FIRST RUN. `ops/NEXT_HANDOFF.md` — the document
handed to EVERY reviewer — carried the two-axis exposure table with the
research axis written as "研究自由度消耗（累计量在此）" and no marker at
all, while `ops/RECOVERY_ANCHOR.md` writes the same table with
【OFF-LIMITS】 on that row. The copy that travels had lost the marker the
original keeps, and "the cumulative amount is in here" is as close to a
pointer as a sentence gets.

A MENTION IS NOT AUTOMATICALLY A POINTER. A delivery MUST be able to name a
quarantined path — that is how you warn someone off it. What it may not do
is name one unmarked, because an unmarked path in a document you were told
to work from reads as a place to go.

SCOPE IS LIVE DELIVERIES ONLY, keyed on `review_id` exactly as the guards
in `test_artifacts_under_review_are_frozen.py` are. A guard that fires on
finished work trains people to ignore it.

WHAT THIS DOES NOT COVER, measured rather than assumed. The scope is
documents that NAME the live review — the prompt and the packet. It is NOT
every file the reviewer is handed: a registered evidence path does not
name the review it is evidence for, so it is never scanned.

Extending it to every registered path was tried and rejected on evidence.
It produces eleven findings across three files, and all eleven are the
"mention is not a pointer" kind — `不得动：两份 EXPOSURE_LEDGER.md` is a
prohibition, and `为什么另立一份，而不是记进 ops/EXPOSURE_LEDGER.md` is a
heading explaining why NOT to use it. Making them pass would mean writing
OFF-LIMITS markers into `ops/D124_RULINGS_CLEAN_EXTRACT.md`, whose whole
value is being a byte-verbatim copy of a ruling nobody may open and
therefore nobody can diff against. A guard that can only be satisfied by
falsifying a transcription is the wrong guard.

So the gap is real, bounded, and deliberate: this catches a DELIVERY that
points at quarantine, not an EVIDENCE FILE that discusses it. If that ever
needs closing, close it by keeping quarantined content out of evidence
files, not by annotating verbatim text.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OPS = REPO / "ops"
REGISTER = OPS / "ARTIFACTS_UNDER_REVIEW.json"
QUARANTINE = OPS / "OUTCOME_CARRYING_ARTIFACTS.json"

#: Text that marks a path as forbidden rather than offering it. Drawn from
#: how the live documents are actually written, not invented here.
_MARKERS = ("OFF-LIMITS", "OFF_LIMITS", "outcome-carrying", "⚠",
            "隔离", "禁区", "不得读", "不得打开", "当作关闭")


def _entries():
    if not REGISTER.exists():
        return []
    return json.loads(REGISTER.read_text(encoding="utf-8"))["under_review"]


def _live_review_ids():
    return {e["review_id"] for e in _entries()}


def _quarantined_paths():
    data = json.loads(QUARANTINE.read_text(encoding="utf-8"))
    paths = [e if isinstance(e, str) else e.get("path", "")
             for e in data.get("carries_outcome", ())]
    paths = [p for p in paths if p]
    assert paths, (
        "the quarantine register yielded no paths — its shape changed and "
        "this guard would silently check nothing. That failure mode has "
        "happened four times in this repository; it is asserted, not hoped.")
    return paths


def _live_delivery_documents():
    """Every file a live reviewer is handed or told to open.

    Includes the packet itself: `qros packet` builds FILE_MANIFEST from a
    diff, so committing a change to a quarantined file and then generating
    a packet whose base predates it would put that path in front of the
    reviewer mechanically, with no human ever typing it.
    """
    live = _live_review_ids()
    if not live:
        return []
    out, seen = [], set()
    # The register IS the handover list. Searching for the review_id finds
    # `qros packet` output (which embeds REVIEW_ID) and any document that
    # cites the review, but a hand-written delivery that never prints its
    # own id was invisible here — registered, frozen, sent, unscanned.
    # Measured 2026-08-27 on ops/DECISION_PACKET_ITEM6_OPEN_FABLE.md.
    if REGISTER.exists():
        for e in json.loads(REGISTER.read_text(encoding="utf-8"))["under_review"]:
            p = REPO / e["path"]
            if p.suffix == ".md" and p.exists() and p not in seen:
                seen.add(p)
                out.append((p, p.read_text(encoding="utf-8")))
    for path in sorted(OPS.glob("*.md")) + sorted(OPS.glob("packets/*.packet")):
        if path in seen:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if any(rid in text for rid in live):
            out.append((path, text))
    return out


def _marked_lines(text):
    """Which line numbers an off-limits marking covers.

    A marker counts on its own line, and ALSO over a fenced block it
    introduces. The block form is not a loophole invented to make this
    pass — it is how the live documents were already written: a sentence
    saying "treat every path in it as closed, named in particular:" and
    then a fence holding the path.

    Demanding the marker on the same line as the path would force those
    fences to be rewritten into something less readable for no gain in
    safety. The window is deliberately tight — the marker must fall in the
    two lines immediately above the opening fence — so a marker further up
    the document cannot silently cover a later, unrelated block.
    """
    lines = text.splitlines()
    marked, in_block, block_marked = set(), False, False
    for i, line in enumerate(lines, 1):
        if line.lstrip().startswith("```"):
            if in_block:
                in_block = False
            else:
                in_block = True
                block_marked = any(any(m in prev for m in _MARKERS)
                                   for prev in lines[max(0, i - 3):i - 1])
            if block_marked:
                marked.add(i)
            continue
        if any(m in line for m in _MARKERS) or (in_block and block_marked):
            marked.add(i)
    return marked


def test_every_registered_artifact_is_actually_reached_by_this_guard():
    """The false-assurance mode, closed.

    `_live_delivery_documents` finds deliveries by searching ops/*.md for a
    LIVE review_id. A hand-written packet that never prints its own
    review_id is therefore invisible here — registered, frozen, sent to a
    reviewer, and silently skipped by the one guard whose whole job is to
    check what that reviewer is handed.

    Measured 2026-08-27: registering ops/DECISION_PACKET_ITEM6_OPEN_FABLE.md
    and then STRIPPING its off-limits marker left this file at 3 passed. The
    guard was not lenient — it never saw the packet at all. `qros packet`
    output embeds REVIEW_ID so it was reached; a hand-written one is not.

    So the reachability is asserted rather than assumed: every .md path in
    the register must be among the documents actually scanned.
    """
    import json as _json
    if not REGISTER.exists():
        return
    entries = _json.loads(REGISTER.read_text(encoding="utf-8"))["under_review"]
    if not entries:
        return
    scanned = {p.relative_to(REPO).as_posix()
               for p, _t in _live_delivery_documents()}
    unreached = sorted(
        e["path"] for e in entries
        if e["path"].endswith(".md") and e["path"] not in scanned)
    assert not unreached, (
        "these artifacts are registered as under review but this guard "
        "never scans them, because their text does not contain their own "
        "review_id. They are being handed to a reviewer unchecked — print "
        "REVIEW_ID=<id> in each:\n  " + "\n  ".join(unreached))


def test_a_live_delivery_never_names_a_quarantined_path_unmarked():
    quarantined = _quarantined_paths()
    problems = []
    for path, text in _live_delivery_documents():
        marked = _marked_lines(text)
        for line_no, line in enumerate(text.splitlines(), 1):
            if line_no in marked:
                continue
            for q in quarantined:
                if q.rsplit("/", 1)[-1] in line:
                    problems.append(
                        f"{path.relative_to(REPO).as_posix()}:{line_no} names "
                        f"{q} with no off-limits marker:\n"
                        f"      {line.strip()[:90]}")
    assert not problems, (
        "a document being handed to a live reviewer names a quarantined "
        "file without marking it forbidden. An unmarked path in a delivery "
        "reads as somewhere to go:\n  " + "\n  ".join(problems))


def test_a_live_delivery_carries_the_register_itself():
    """Naming the marked exceptions is not enough — the delivery has to say
    where the authoritative list lives, because the list changes and the
    document does not.

    ROLE-SCOPED, and the scoping is the point. The register distinguishes a
    `delivery` (a document authored for this review) from a `reference`
    (pre-existing bytes handed along). Only a delivery must carry the list.

    Measured 2026-08-27: requiring it of every registered file demanded that
    ops/ND1_PROFILE_RATIFICATION.md — Aaron's verbatim approval record —
    grow a governance paragraph to satisfy a test. Editing an approved
    record to make a guard green is backwards, so the guard learned the
    distinction instead.
    """
    deliveries = {e["path"] for e in _entries()
                  if e.get("role", "delivery") == "delivery"}
    missing = [p.relative_to(REPO).as_posix()
               for p, text in _live_delivery_documents()
               if p.suffix == ".md"
               and p.relative_to(REPO).as_posix() in deliveries
               and "OUTCOME_CARRYING_ARTIFACTS.json" not in text]
    assert not missing, (
        "these live delivery documents never name the quarantine register, "
        "so a reviewer reading only them has no way to check any other "
        "path:\n  " + "\n  ".join(missing))


def test_the_marker_vocabulary_actually_matches_the_live_documents():
    """A marker list that matched nothing would make the first test vacuous
    — it would skip no lines, find no unmarked mentions, and pass.

    So: if a live delivery exists at all, at least one covered line must
    name a quarantined path. If that stops being true the vocabulary has
    drifted and the guard above is checking nothing."""
    docs = _live_delivery_documents()
    if not docs:
        return
    quarantined = _quarantined_paths()
    hits = 0
    for _path, text in docs:
        marked = _marked_lines(text)
        for line_no, line in enumerate(text.splitlines(), 1):
            if line_no in marked and any(
                    q.rsplit("/", 1)[-1] in line for q in quarantined):
                hits += 1
    assert hits, (
        "no covered line in any live delivery names a quarantined path. "
        "Either no delivery warns anyone off anything, or _MARKERS no "
        "longer matches how they are written — in which case the guard "
        "above skips nothing and protects nothing.")
