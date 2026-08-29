"""A prepared patch that has silently stopped applying is worse than none.

`ops/PREPARED_C_BUILD_1_GATE_WIRING.patch` is finished work parked until a
review returns. Parked work rots: if `supplement_runner.py` moves for any
other reason first, the patch stops applying and NOTHING SAYS SO. The
record keeps reading "PREPARED", the next session trusts it, and discovers
the rot at the moment it was counting on the work being ready.

So the patch is checked the only way that means anything -- by actually
applying it to a scratch copy of the tree, in reverse-safe form, and
throwing the result away.
"""

import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PATCH = REPO / "ops" / "PREPARED_C_BUILD_1_GATE_WIRING.patch"
RECORD = REPO / "ops" / "PREPARED_C_BUILD_1_GATE_WIRING.md"
REGISTER = REPO / "ops" / "ARTIFACTS_UNDER_REVIEW.json"
TARGET = "src/itsf/mc/supplement_runner.py"


def _git(*args):
    return subprocess.run(["git", "-C", str(REPO), *args],
                          capture_output=True, text=True)


class TestTheParkedWorkIsStillGood(unittest.TestCase):

    def test_the_patch_and_its_record_both_exist(self):
        self.assertTrue(PATCH.exists(), "the prepared patch is gone but its "
                                        "record still says PREPARED")
        self.assertTrue(RECORD.exists())

    def test_it_still_applies_cleanly_to_the_current_tree(self):
        """`--check` applies nothing; it only reports whether it could."""
        out = _git("apply", "--check", str(PATCH))
        self.assertEqual(
            0, out.returncode,
            "the parked C_BUILD_1 wiring no longer applies:\n%s\n\n"
            "%s changed underneath it. Regenerate the patch from a fresh "
            "edit, or delete both files and stop advertising work that is "
            "not ready." % (out.stderr.strip(), TARGET))

    def test_it_touches_only_the_file_it_says_it_touches(self):
        """A parked patch that quietly grew a second target would apply
        cleanly and change something nobody reviewed."""
        touched = {line.split(" b/")[-1].strip()
                   for line in PATCH.read_text(encoding="utf-8").splitlines()
                   if line.startswith("diff --git ")}
        self.assertEqual({TARGET}, touched)

    def test_the_patch_is_not_empty(self):
        """`git apply --check` succeeds on an empty patch, so the check
        above passes over nothing if the file is ever truncated."""
        text = PATCH.read_text(encoding="utf-8")
        self.assertGreater(len(text.splitlines()), 40)
        self.assertIn("_classify_c_build_1", text)
        self.assertIn("c_build_outcome", text)


class TestTheReasonItIsParkedIsStillTrue(unittest.TestCase):
    """If the review returns, the block lifts -- and this says so instead
    of leaving finished work parked indefinitely because nobody rechecked
    the condition."""

    def test_the_target_is_still_held_by_a_reviewer(self):
        import json
        register = json.loads(REGISTER.read_text(encoding="utf-8"))
        rows = register["under_review"]
        self.assertGreater(len(rows), 0,
                           "the register is empty, so the membership test "
                           "below would pass over nothing")
        held = [e for e in rows if e.get("path") == TARGET]
        if held:
            return          # still parked for the stated reason
        self.fail(
            "%s is no longer in ops/ARTIFACTS_UNDER_REVIEW.json, so the "
            "reason the C_BUILD_1 wiring is parked no longer holds.\n\n"
            "This is NOT a defect -- it is the unblock. Apply "
            "ops/PREPARED_C_BUILD_1_GATE_WIRING.patch, then follow section 4 "
            "of its record: the three day_strata_context tripwires go red BY "
            "DESIGN and must be converted to their live form, not deleted."
            % TARGET)


if __name__ == "__main__":
    unittest.main()
