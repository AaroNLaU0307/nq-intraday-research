"""Artifacts a reviewer MUST read must not restate outcome.

WHY — a real cost, 2026-08-24. A delegated Sol session carried a forbidden-
read list and still had to declare OUTCOME_EXPOSED=TARGET_METRIC, because
two of the four artifacts it was REQUIRED to read restated the very things
the list forbade: the revealed verdict, the cumulative exposure count, and
a verbatim quote of the addendum's feasibility-PASS assertion. It recorded
itself as no longer qualifying as a future outcome-blind Stage I reviewer.

I wrote both artifacts. The intent was honest disclosure -- telling the
reviewer such a file exists and that ruling on it is Aaron's. The intent
was right and the placement was wrong: disclosing that something exists
does not require restating what it says.

That was the third instance of one mistake. First the exposure ledger went
into a reviewer's readable whitelist while embedding a post-reveal summary;
then I read that line myself after saying I would not; then this. The
common error is treating "where is the outcome" as a location question when
it is a content question. A file is an exposure surface because of what it
says, not because of what it is called.

Stage I seats do not regenerate. ITSF cannot supply an A2 pilot -- it was
sealed before this runtime existed and no runs/ A2 record exists -- so
Stage I is the only GRAD-* pilot it can offer, and each burned session
costs one.

WHAT THIS GUARD IS, after the first scan. Sweeping the whole repository
found TEN outcome-carrying files, not the two the reviewer reported, and
three of them matter more than the ones that were caught:
  * ops/MC_TO_STRATEGY_MASTER_PLAN.md -- the recovery anchor every
    resuming session reads, so sessions are outcome-exposed by
    construction unless the anchor is kept out of review sets;
  * ops/ND2_ND3_FABLE_DECISION_PROMPT.md -- the prompt I sent Fable put
    the verdict and the exposure total inside the paragraph explaining
    the firewall, so Fable was exposed by the firewall itself;
  * ops/MC_FACTORY_BOUNDARY_STAGE_I.md -- a file named STAGE_I that
    restates the verdict.

So a transient "under review" register is the wrong home for this. Files
that carry outcome carry it permanently, and the register empties when a
review returns. ops/OUTCOME_CARRYING_ARTIFACTS.json is the permanent
quarantine; this guard checks that nothing quarantined enters a
mandatory-read set, and that the quarantine has not fallen behind the
repository.

It cannot prove a file is clean. It stops the phrasings already known to
burn a seat. The judgement stays mine.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REGISTER = REPO / "ops" / "ARTIFACTS_UNDER_REVIEW.json"
QUARANTINE = REPO / "ops" / "OUTCOME_CARRYING_ARTIFACTS.json"

#: (label, pattern, why it burns a seat). Each was measured, not imagined.
OUTCOME_RESTATEMENTS = (
    ("revealed verdict",
     re.compile(r"INCONCLUSIVE_PENDING_MC"),
     "restates the revealed S0-T001 verdict"),
    ("cumulative exposure count",
     re.compile(r"exposure[^\n]{0,12}1575|1575[^\n]{0,12}exposure"),
     "restates the revealed cumulative researcher-exposure total"),
    ("addendum feasibility assertion",
     re.compile(r"可行性天花板[^\n]{0,20}PASS"),
     "quotes a post-reveal feasibility result classification verbatim"),
    ("per-theta result",
     re.compile(r"theta_0\.[35][^\n]{0,40}(?:result|结果|verdict)"),
     "restates a per-theta result"),
    ("endpoint spread value",
     re.compile(r"0\.20477498240675374"),
     "restates a revealed measured value"),
    ("zero-direction cell count",
     re.compile(r"16\s*个\s*zero-direction"),
     "restates a revealed grid fact"),
)

#: This file necessarily names the patterns it bans, and the incident record
#: quotes the leak in order to document it. Neither is handed to a reviewer.
_SELF = {"tests/test_review_artifacts_are_outcome_clean.py",
         "ops/INCIDENT_HANDOFF_ARTIFACTS_CARRY_OUTCOME_20260824.md"}


def _registered():
    if not REGISTER.exists():
        return []
    return json.loads(REGISTER.read_text(encoding="utf-8"))["under_review"]


def _quarantined():
    if not QUARANTINE.exists():
        return {}
    data = json.loads(QUARANTINE.read_text(encoding="utf-8"))
    return {e["path"]: e["restates"] for e in data["carries_outcome"]}


def _scan(text):
    return [label for label, pattern, _ in OUTCOME_RESTATEMENTS
            if pattern.search(text)]


def test_no_quarantined_artifact_is_handed_to_a_reviewer():
    """The load-bearing one. A reviewer who reads an outcome-carrying file
    must record OUTCOME_EXPOSED and stops qualifying as a future
    outcome-blind Stage I -- and those seats do not regenerate."""
    quarantined = _quarantined()
    hits = [f"{e['path']} -> issued to {e['issued_to']} "
            f"({', '.join(quarantined[e['path']])})"
            for e in _registered() if e["path"] in quarantined]
    assert not hits, (
        "a mandatory-read artifact is on the outcome quarantine list:\n  "
        + "\n  ".join(hits)
        + "\n\nHand the reviewer a scoped extract instead. Disclose that "
          "the file EXISTS and who rules on it; never what it says.")


def test_the_quarantine_has_not_fallen_behind_the_repository():
    """A file that starts restating outcome must be quarantined the same
    day. A stale quarantine reads as an all-clear it never earned."""
    quarantined = _quarantined()
    missing = []
    for path in sorted(REPO.rglob("*.md")):
        rel = path.relative_to(REPO).as_posix()
        if rel in _SELF or ".git" in rel or rel in quarantined:
            continue
        carries = _scan(path.read_text(encoding="utf-8", errors="replace"))
        if carries:
            missing.append(f"{rel}  [{', '.join(carries)}]")
    assert not missing, (
        "these restate revealed outcome and are not quarantined:\n  "
        + "\n  ".join(missing)
        + "\n\nAdd them to ops/OUTCOME_CARRYING_ARTIFACTS.json, or remove "
          "the restating text.")


def test_every_quarantined_file_still_carries_what_it_claims():
    """Stale entries hide that a file was cleaned, which is how a
    quarantine quietly stops meaning anything."""
    stale = []
    for path, claimed in _quarantined().items():
        target = REPO / path
        if not target.exists():
            stale.append(f"{path}: MISSING")
            continue
        actual = set(_scan(target.read_text(encoding="utf-8",
                                            errors="replace")))
        gone = sorted(set(claimed) - actual)
        if gone:
            stale.append(f"{path}: no longer restates {gone}")
    assert not stale, (
        "quarantine entries no longer describe their files -- update them:"
        "\n  " + "\n  ".join(stale))


def test_the_blocklist_itself_still_matches_the_leak_it_was_built_from():
    """If the patterns stop matching the recorded incident, the guard has
    drifted away from the thing it exists to catch."""
    record = REPO / "ops" / "INCIDENT_HANDOFF_ARTIFACTS_CARRY_OUTCOME_20260824.md"
    matched = _scan(record.read_text(encoding="utf-8"))
    assert len(matched) >= 1, (
        f"only {matched} still match the incident record -- the blocklist "
        "no longer describes the leak it was written for")
