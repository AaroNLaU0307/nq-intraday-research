"""The recovery anchor must stay safe for an outcome-blind seat to read.

D-2, ruled C by Fable on 2026-08-26 (`DELEGATED=YES`): split the anchor AND
keep the fences. `ops/RECOVERY_ANCHOR.md` is the split half — the entry
point a fresh session reads first.

WHY IT EXISTS AT ALL. The old entry point was
`ops/MC_TO_STRATEGY_MASTER_PLAN.md` §1, and that file is quarantined. So the
documented first step of orienting yourself led every outcome-blind reviewer
into a file they must not read. Three seats have now been touched by it and
only one opened it deliberately: the second was burned by a broad symbol
search, the third by a single targeted grep.

The anchor removes the SOURCE — the entry point no longer leads there. The
search ban (S1(b)) removes the other route. Both are needed: a burned seat
does not regenerate, and a one-shot irreversible harm does not get a single
layer of defence.

These tests are the "outcome-clean and stays that way" half. Without them
the anchor is one careless paste away from becoming the thing it replaced.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ANCHOR = REPO / "ops" / "RECOVERY_ANCHOR.md"
QUARANTINE = REPO / "ops" / "OUTCOME_CARRYING_ARTIFACTS.json"


def _quarantined_paths():
    data = json.loads(QUARANTINE.read_text(encoding="utf-8"))
    paths = [e if isinstance(e, str) else e.get("path", "")
             for e in data["carries_outcome"]]
    assert any(paths), (
        "the quarantine register yielded no paths — its shape changed and "
        "these guards would silently check nothing")
    return paths


def test_the_anchor_exists():
    assert ANCHOR.exists(), (
        "the outcome-clean recovery anchor is gone; the entry point falls "
        "back to a quarantined file, which is what D-2 was ruled to stop")


def test_the_anchor_restates_no_revealed_outcome():
    """The same scanner the whole repository is held to. Written out
    separately because this file's whole value is that a blind seat may
    read it — a failure here is not a filing problem, it is a burned seat
    waiting to happen."""
    import test_review_artifacts_are_outcome_clean as clean

    carries = clean._scan(ANCHOR.read_text(encoding="utf-8"))
    assert not carries, (
        f"the recovery anchor now restates {carries}. Remove the "
        "restatement — do NOT quarantine the anchor. Quarantining it would "
        "recreate the exact trap D-2 removed.")


def test_the_anchor_is_not_quarantined():
    rel = ANCHOR.relative_to(REPO).as_posix()
    assert rel not in _quarantined_paths(), (
        "the recovery anchor has been quarantined. Every outcome-blind seat "
        "now has no safe entry point at all, which is strictly worse than "
        "before the split.")


def test_every_quarantined_path_the_anchor_names_is_marked_off_limits():
    """D-2 condition 1. The anchor MAY name a quarantined file — it has to,
    to warn people off it — but never without the marker. An unmarked
    mention reads as a pointer, and a pointer is how the first seat went."""
    text = ANCHOR.read_text(encoding="utf-8")
    unmarked = []
    for path in _quarantined_paths():
        name = path.rsplit("/", 1)[-1]
        if name not in text:
            continue
        for line in text.splitlines():
            if name in line and "OFF-LIMITS" not in line.upper():
                # a line that merely says the register holds more paths is
                # not a mention of this one
                unmarked.append(f"{path}: {line.strip()[:70]}")
                break
    assert not unmarked, (
        "the anchor names quarantined paths without an OFF-LIMITS marker; "
        "an unmarked mention reads as a pointer:\n  " + "\n  ".join(unmarked))


def test_the_anchor_carries_the_search_ban_and_both_exposure_axes():
    """A seat that reads only the anchor must still learn the two things
    that keep it alive: it may not search, and there are two ledgers."""
    text = ANCHOR.read_text(encoding="utf-8")
    for token, why in (
            ("OUTCOME_CARRYING_ARTIFACTS.json", "the quarantine register"),
            ("PULL_PROTOCOL", "how bytes are supplied instead of searched"),
            ("ops/REVIEWER_EXPOSURE_LOG.md", "the seat axis"),
            ("ops/EXPOSURE_LEDGER.md", "the research axis")):
        assert token in text, f"the anchor does not name {why} ({token})"


def test_the_master_plan_carries_the_redirect_banner():
    """D-2 condition 2: append-only. The old §1 is not deleted or edited;
    a banner declares it superseded. Checked by presence of the banner and
    of the old section — if the old section vanished, someone edited an
    append-only anchor instead of appending to it."""
    plan = REPO / "ops" / "MC_TO_STRATEGY_MASTER_PLAN.md"
    text = plan.read_text(encoding="utf-8")
    assert "## 1. 恢复序" in text, (
        "the master plan's original §1 is gone — D-2 condition 2 requires "
        "it be left byte-unchanged and superseded by an appended banner")
    assert "RECOVERY_ANCHOR.md" in text, (
        "the master plan carries no redirect banner to the new anchor")
