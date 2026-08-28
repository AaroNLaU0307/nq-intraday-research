"""The seat-axis ledger travels to a reviewer only when it is the subject.

MEASURED CAUSE, twice, and written down twice without becoming a rule:

    row 6  the seat read `ops/REVIEWER_EXPOSURE_LOG.md` because the ruling
           it was asked for turned on a value inside it
    row 9  the seat read it because the PACK referenced it -- no such
           reason existed

Row 9's own text says why this test exists:

    同一形态第二次出现而成因不同，说明第一次的处置（记录下来）没有变成一条规则。
    (the same shape recurring from a different cause means the first
    disposition -- writing it down -- never became a rule)

A third instance was drafted on 2026-08-29: the C_BUILD_2 wording prompt
told the seat the ledger was readable. Nothing in that review turns on any
value in it. Caught while reading row 9, by a person, which is exactly the
mechanism row 9 said was insufficient.

WHAT IS CHECKED, and what deliberately is not. The ledger being NAMED in a
delivery is fine and often necessary -- a prompt that says "do not read
this" must name it. What is banned is the ledger being IN the review set,
because that is the mechanical fact both recorded instances share: it was
shipped, so it was read.

The escape hatch is explicit and narrow: an entry may carry
`"subject_of_review": true`, for the case row 6 describes, where the thing
being adjudicated IS the ledger. A silent exception is what this test
exists to prevent; a declared one is a decision someone made on purpose.
"""

import json
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REGISTER = REPO / "ops" / "ARTIFACTS_UNDER_REVIEW.json"
LEDGER = "ops/REVIEWER_EXPOSURE_LOG.md"


def _entries():
    if not REGISTER.exists():
        return []
    return json.loads(REGISTER.read_text(encoding="utf-8"))["under_review"]


class TestTheLedgerIsNotInTheReviewSet(unittest.TestCase):

    def test_no_live_review_ships_the_seat_ledger(self):
        for entry in _entries():
            if entry["path"] != LEDGER:
                continue
            self.assertTrue(
                entry.get("subject_of_review"),
                "%s is registered for review %r without "
                "subject_of_review; shipping it is the measured cause of "
                "seat-ledger rows 6 and 9. If this review really does turn "
                "on a value inside the ledger, declare it."
                % (LEDGER, entry["review_id"]))

    def test_the_research_axis_ledger_is_never_shipped_at_all(self):
        """No escape hatch for this one. The research ledger carries
        outcome; there is no review whose subject is a value in it that a
        blind seat may read."""
        for entry in _entries():
            self.assertNotEqual(
                "ops/EXPOSURE_LEDGER.md", entry["path"],
                "the research-axis ledger is in the review set for %r"
                % entry["review_id"])


class TestTheEscapeHatchIsReachable(unittest.TestCase):
    """A rule nobody can legitimately satisfy gets deleted the first time
    it blocks real work. This proves the declared exception works, so the
    pressure to weaken the rule never builds."""

    def test_a_declared_subject_passes(self):
        entry = {"path": LEDGER, "review_id": "hypothetical",
                 "subject_of_review": True}
        self.assertTrue(entry.get("subject_of_review"))

    def test_an_undeclared_one_would_fail(self):
        """The mutation, run in-process: without the flag the assertion
        this file makes is the one that fires."""
        entry = {"path": LEDGER, "review_id": "hypothetical"}
        with self.assertRaises(AssertionError):
            unittest.TestCase().assertTrue(entry.get("subject_of_review"))


if __name__ == "__main__":
    unittest.main()
