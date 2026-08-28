"""The approved bytes themselves, reconstructed and checked -- not a transcription.

The C_BUILD_2 wording review returned HIGH: the ruling's falsifier turns on
what the APPROVED ND1 text says, and the pack shipped
`src/itsf/mc/supplement_contract.py`, which is a TRANSCRIPTION of three
values. A transcription cannot close a question about the original, however
faithful it is -- checking it against itself is not a check.

So the original is reconstructed here, from git, every run:

    commit   803d99162d0a018ae5a3b44273601d98d9439d50
    file     ops/DECISION_PACKET_N00_AND_ND1.md
    span     49 lines beginning at line 1309, 2527 bytes, LF, UTF-8
    sha256   0a08319a408f068ce4c92f93c2c4c39e409937dddfd0ef9f7af43618c70b50a5
             == APPROVED_PROFILE_SHA256 in ops/ND1_PROFILE_RATIFICATION.md

WHAT THE APPROVED BYTES SAY ABOUT WHEN THE GATE RUNS: nothing. Searched for
staging / during / 期间 / 时机 / when / 运行时 / 中途 / mid / checkpoint /
gate across all 49 lines; one hit, `RECOMMENDED_F1_GATE_NAME_ENUM=
DEFER_TO_N04`, which is about a gate's NAME. The ruling's falsifier is
therefore not triggered -- and now that conclusion rests on the ratified
bytes rather than on a search of documents that quote them.

A SECOND THING THE RECONSTRUCTION SHOWED, which nobody asked for:
`SILENT_DELETE_FORBIDDEN` is NOT in the approved preimage. It is DERIVED --
`MODIFY ⇒ YES` -- by a table at line 1299, which sits OUTSIDE the span
beginning at 1309. §12.1(b) cited it as "已批准" (approved). It is a derived
value with an approved antecedent, which is a weaker and different thing,
and the difference matters exactly where (4) 锚定保全 is being claimed.
"""

import hashlib
import re
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
COMMIT = "803d99162d0a018ae5a3b44273601d98d9439d50"
DOC = "ops/DECISION_PACKET_N00_AND_ND1.md"
SHA = "0a08319a408f068ce4c92f93c2c4c39e409937dddfd0ef9f7af43618c70b50a5"
FIRST_LINE, SPAN, SIZE = 1309, 49, 2527


def _doc_at_commit():
    out = subprocess.run(["git", "-C", str(REPO), "show",
                          "%s:%s" % (COMMIT, DOC)], capture_output=True)
    assert out.returncode == 0, out.stderr
    return out.stdout.decode("utf-8").split("\n")


def _preimage():
    lines = _doc_at_commit()
    return "\n".join(lines[FIRST_LINE - 1:FIRST_LINE - 1 + SPAN]) + "\n"


class TestTheApprovedBytesAreTheOnesBeingReasonedAbout(unittest.TestCase):

    def test_the_preimage_hashes_to_the_ratified_value(self):
        body = _preimage()
        self.assertEqual(SIZE, len(body.encode("utf-8")))
        self.assertEqual(SHA, hashlib.sha256(body.encode("utf-8")).hexdigest())

    def test_the_ratification_record_still_declares_that_hash(self):
        """If the ratification record is ever edited to name a different
        hash, this reconstruction is pinned to a superseded approval and
        must fail rather than keep agreeing with itself."""
        text = (REPO / "ops" / "ND1_PROFILE_RATIFICATION.md").read_text("utf-8")
        self.assertIn("APPROVED_PROFILE_SHA256=" + SHA, text)
        self.assertIn(COMMIT, text)


class TestTheFalsifierIsClosedOnApprovedBytes(unittest.TestCase):

    TIMING = re.compile(
        r"staging|期间|during|时机|when|运行时|中途|\bmid\b|checkpoint",
        re.IGNORECASE)

    def test_no_approved_line_says_when_the_gate_runs(self):
        offenders = [line for line in _preimage().split("\n")
                     if self.TIMING.search(line)]
        self.assertEqual([], offenders,
                         "the approved profile constrains WHEN the gate "
                         "runs, which triggers the ruling's falsifier and "
                         "voids decision B: %r" % offenders)

    def test_the_three_relevant_values_are_present_and_verbatim(self):
        """What the approved bytes DO say. If any of these ever changes,
        the wording's anchoring claims are stale."""
        body = _preimage()
        for value in (
                "RECOMMENDED_ND1_PARTIAL_RECOVERY_RULE=MODIFY",
                "RECOMMENDED_ND1_PARTIAL_MODIFY_TEXT="
                "BRANCH_E_RENAME_TO_.partial.divergent.<incident_id>;"
                "BRANCH_C_RENAME_THEN_ALLOW_RETRY",
                "RECOMMENDED_ND1_ARCHIVE_FAILURE_POLICY=A"):
            self.assertIn(value, body)


class TestSilentDeleteForbiddenIsDerivedNotApproved(unittest.TestCase):
    """Found by the reconstruction, not by the review. Pinned so the
    wording cannot go on calling it an approved value."""

    def test_it_is_absent_from_the_approved_preimage(self):
        self.assertNotIn("SILENT_DELETE_FORBIDDEN", _preimage())

    def test_its_derivation_rule_sits_outside_the_approved_span(self):
        lines = _doc_at_commit()
        rows = [i + 1 for i, line in enumerate(lines)
                if "SILENT_DELETE_FORBIDDEN" in line]
        self.assertTrue(rows, "the derivation table row is gone")
        for row in rows:
            self.assertLess(row, FIRST_LINE,
                            "a SILENT_DELETE_FORBIDDEN row is inside the "
                            "approved span after all; if so it IS an "
                            "approved value and this whole class is wrong")

    def test_its_antecedent_is_approved(self):
        """The half that IS approved, and the reason the derived value is
        still usable -- just not describable as approved."""
        self.assertIn("RECOMMENDED_ND1_PARTIAL_RECOVERY_RULE=MODIFY",
                      _preimage())


if __name__ == "__main__":
    unittest.main()
