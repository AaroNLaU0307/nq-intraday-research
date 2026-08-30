"""No two rows of the seat-exposure ledger may carry the same id.

MEASURED 2026-08-30, while appending three rows for review rounds 5, 6 and 7.
The ledger already held ids 1..9; an earlier session of mine had restarted
numbering at 4, so 4, 5 and 6 each appeared TWICE, and my append collided 7,
8 and 9 on top of that.

WHY IT MATTERS MORE HERE THAN IN AN ORDINARY TABLE. This ledger is the record
of which reviewer seats have been consumed and what each one saw. Its rows get
cited by number in rulings and decision packets -- "the cause is the same as
row 6" -- and a duplicated number makes a citation point at two different
events, one of which was a clean seat and the other an incident. That is not a
tidiness problem; it is a record that reads as saying something it does not.

THE LEDGER IS APPEND-ONLY, so the existing collisions CANNOT be repaired by
renumbering. They are frozen below by exact value, and the guard refuses any
NEW one. Freezing them is not forgiveness: it records that this file's history
contains an ambiguity a reader must resolve by section, and it makes a fourth
collision impossible rather than merely regrettable.
"""

import re
import unittest
from collections import Counter
from pathlib import Path

LEDGER = (Path(__file__).resolve().parent.parent / "ops"
          / "REVIEWER_EXPOSURE_LOG.md")
ROW = re.compile(r"^\| (\d+) \|", re.M)

#: Ids that were ALREADY duplicated when this guard was written. Frozen by
#: value, never widened to silence a new one -- adding to this set is how a
#: guard stops being a guard.
KNOWN_COLLISIONS = frozenset({4, 5, 6})


def ids(ledger=LEDGER):
    return [int(n) for n in ROW.findall(ledger.read_text(encoding="utf-8"))]


def new_collisions(row_ids, known=KNOWN_COLLISIONS):
    """Ids appearing more than once that were not already doing so."""
    return sorted(n for n, count in Counter(row_ids).items()
                  if count > 1 and n not in known)


class TestTheLedgerIdsAreUsable(unittest.TestCase):

    def test_no_new_id_collides(self):
        self.assertEqual(
            [], new_collisions(ids()),
            "a seat-ledger row id is used twice. Rows are cited by number in "
            "rulings, so a repeat makes a citation ambiguous between a clean "
            "seat and an incident. The ledger is append-only: give the new "
            "row the next unused number instead of reusing one.")

    def test_the_known_collisions_are_still_exactly_what_was_frozen(self):
        """If one of them stops colliding, someone edited an append-only
        ledger, and that is worth a red test even though it looks like a
        repair."""
        actual = {n for n, count in Counter(ids()).items() if count > 1}
        self.assertEqual(
            set(KNOWN_COLLISIONS), actual,
            "the frozen collision set no longer matches the file. If rows "
            "were renumbered, an append-only record was rewritten; if new "
            "ones collided, the guard above should have caught it first.")

    def test_the_ledger_was_actually_read(self):
        """Vacuity: a broken regex would make every assertion above pass
        over an empty list."""
        self.assertGreater(len(ids()), 10,
                           "found %d rows; at that count this file proves "
                           "nothing" % len(ids()))


class TestTheGuardIsNotVACUOUS(unittest.TestCase):

    def test_a_fresh_duplicate_is_reported(self):
        self.assertEqual([12], new_collisions([1, 2, 12, 12]))

    def test_a_frozen_duplicate_is_not_reported(self):
        self.assertEqual([], new_collisions([4, 4, 5, 5, 6, 6, 7]))

    def test_a_frozen_id_colliding_a_THIRD_time_is_still_tolerated(self):
        """Stated so the limit is visible rather than discovered later: the
        freeze is by ID, not by count. A fourth row numbered 4 would pass
        here and be caught by the append discipline instead."""
        self.assertEqual([], new_collisions([4, 4, 4]))

    def test_a_clean_series_reports_nothing(self):
        self.assertEqual([], new_collisions([1, 2, 3, 7, 8]))


if __name__ == "__main__":
    unittest.main()
