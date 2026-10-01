"""The review register must say "this is the delivery" in exactly one way.

MEASURED FAILURE, 2026-08-30, and it cost a blocked commit. I registered the
round-6 packet with `"role": "delivery"`. One guard
(`test_issued_deliveries_are_registered`) reads `role`. Two others
(`test_artifacts_under_review_are_frozen`, `test_the_delivery_cannot_pin_itself`)
read `is_the_delivery_document`. So the entry satisfied one guard and was
invisible to the other two: the delivery was pinned as though it were a
reference, and both pin guards fired -- correctly -- after the issue had
already gone out.

TWO SPELLINGS OF ONE CONCEPT IS A HAND-WRITTEN MIRROR, which is the defect
shape this project keeps meeting: `_divergent_name` assembled by hand, a
prompt guard parsing a table format I had invented, `reached` typed out
beside a derived `declared`. A mirror does not announce that it has gone
stale; something downstream just quietly stops being checked.

WHY THE FLAG IS REQUIRED RATHER THAN DEFAULTED. `role` defaulted to
"delivery" when absent and `is_the_delivery_document` defaulted to false --
the two defaults point OPPOSITE WAYS, so an entry carrying neither field is
simultaneously the delivery and not the delivery depending on who is asking.
Requiring the flag makes that state unrepresentable instead of ambiguous.
"""

import json
import unittest
from pathlib import Path

REGISTER = (Path(__file__).resolve().parent.parent / "ops"
            / "ARTIFACTS_UNDER_REVIEW.json")
FLAG = "is_the_delivery_document"


def entries(register=REGISTER):
    return json.loads(register.read_text(encoding="utf-8"))["under_review"]


def vocabulary_problems(rows):
    """Every way the delivery marking can be wrong. Empty means consistent."""
    problems = []
    by_review = {}
    for row in rows:
        if FLAG not in row:
            problems.append(
                "%s carries no %s; the two guards that read this register "
                "default in OPPOSITE directions, so an entry without it is "
                "the delivery to one and a reference to the other"
                % (row.get("path", row), FLAG))
        elif not isinstance(row[FLAG], bool):
            problems.append("%s: %s is %r, not a bool"
                            % (row["path"], FLAG, row[FLAG]))
        if "role" in row:
            agrees = (row["role"] == "delivery") == bool(row.get(FLAG))
            if not agrees:
                problems.append(
                    "%s: role=%r disagrees with %s=%r -- one register, one "
                    "vocabulary" % (row["path"], row["role"], FLAG,
                                    row.get(FLAG)))
        by_review.setdefault(row.get("review_id"), []).append(row)

    for review_id, group in sorted(by_review.items(), key=lambda kv: str(kv[0])):
        marked = [r for r in group if r.get(FLAG)]
        if len(marked) != 1:
            problems.append(
                "%s has %d entries marked as the delivery; a review has "
                "exactly one delivery document and the pin derivation "
                "excludes exactly it" % (review_id, len(marked)))
    return problems


class TestTheRegisterIsUnambiguous(unittest.TestCase):

    def test_every_entry_says_plainly_whether_it_is_the_delivery(self):
        self.assertEqual([], vocabulary_problems(entries()))

    def test_the_guards_that_read_this_register_read_the_same_field(self):
        """Derived from the guard SOURCES, so adding a third spelling
        somewhere else shows up here rather than in a blocked commit."""
        tests = Path(__file__).resolve().parent
        readers = sorted(p.name for p in tests.glob("test_*.py")
                         if "ARTIFACTS_UNDER_REVIEW" in
                         p.read_text(encoding="utf-8"))
        self.assertGreater(len(readers), 2,
                           "found %d readers of the register; at that count "
                           "this proves nothing" % len(readers))
        rogue = []
        for name in readers:
            if name == Path(__file__).name:
                continue
            text = (tests / name).read_text(encoding="utf-8")
            if 'get("role"' in text or "get('role'" in text:
                rogue.append(name)
        self.assertEqual(
            [], rogue,
            "these still ask the register for `role` while the rest ask for "
            "%s: %s -- that split is what let an issued delivery be frozen "
            "as a reference on 2026-08-30" % (FLAG, rogue))


class TestTheGuardIsNotVACUOUS(unittest.TestCase):
    """The register is empty between reviews, so `[] == []` would pass here
    forever without checking anything. Each clause gets a row built to break
    it."""

    GOOD = {"path": "ops/P.md", "review_id": "r", FLAG: True}

    def test_an_entry_missing_the_flag_is_reported(self):
        row = {"path": "ops/P.md", "review_id": "r"}
        self.assertTrue(any("carries no" in p
                            for p in vocabulary_problems([row])))

    def test_the_exact_mistake_of_2026_08_30_is_reported(self):
        """`role: delivery` alone -- what I actually wrote."""
        rows = [{"path": "ops/P.md", "review_id": "r", "role": "delivery"},
                {"path": "src/a.py", "review_id": "r", "role": "reference"}]
        problems = vocabulary_problems(rows)
        self.assertTrue(any("carries no" in p for p in problems))
        self.assertTrue(any("exactly one delivery" in p for p in problems))

    def test_disagreeing_spellings_are_reported(self):
        row = dict(self.GOOD, role="reference")
        self.assertTrue(any("one vocabulary" in p
                            for p in vocabulary_problems([row])))

    def test_two_deliveries_in_one_review_are_reported(self):
        rows = [self.GOOD, dict(self.GOOD, path="ops/Q.md")]
        self.assertTrue(any("exactly one delivery" in p
                            for p in vocabulary_problems(rows)))

    def test_zero_deliveries_in_one_review_are_reported(self):
        rows = [dict(self.GOOD, **{FLAG: False})]
        self.assertTrue(any("exactly one delivery" in p
                            for p in vocabulary_problems(rows)))

    def test_a_non_bool_flag_is_reported(self):
        rows = [dict(self.GOOD, **{FLAG: "yes"})]
        self.assertTrue(any("not a bool" in p
                            for p in vocabulary_problems(rows)))

    def test_a_well_formed_review_really_passes(self):
        rows = [self.GOOD,
                {"path": "src/a.py", "review_id": "r", FLAG: False,
                 "role": "reference"}]
        self.assertEqual([], vocabulary_problems(rows))


if __name__ == "__main__":
    unittest.main()
