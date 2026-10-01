"""§12.5 invented a defect. This is the measurement that shows it did.

§12.5 said `already_sealed` accepts a pre-existing FINAL "不问出处、从未复读
校验" (without asking its provenance, never re-read-verified) and concluded
that (a)'s violation class -- "a FINAL that was never re-read-verified is
treated as sealed" -- was not covered by (a)'s detection route.

The first half is true. The second half does not follow, and is false:

    if final.exists():
        existing = final.read_bytes()          # <- the re-read
        if existing == intended:               # <- the verification
            return PartialAction("already_sealed", ...)

That IS a re-read compared against `intended`. It is the same check
`supplement_post_promotion_verify` performs after `os.replace`. MEASURED by
counting `Path.read_bytes` on the FINAL name across every path:

    pre-existing FINAL, bytes match      already_sealed    1 read, == intended
    pre-existing FINAL, bytes differ     REFUSED           1 read, != intended
    no partial, ordinary seal            promote           1 read, == intended
    partial matches, promotion completes promote           1 read, == intended
    partial differs                      retry_permitted   0 reads -- and no
                                                           FINAL is treated
                                                           as sealed

So the class has NO INSTANCE, and (a) as originally worded covered it.

WHAT I ACTUALLY DID: I substituted a wider class of my own invention --
"a FINAL of unknown PROVENANCE is accepted" -- for the one (a) named, then
found (a) did not cover the substituted class, then narrowed (a) to match
what I could detect. Measured half right, inferred half wrong, which is the
same shape as the Class-B misclassification earlier the same day.

Provenance really is unknown, and that observation survives. It is a
separate fact about the mechanism, not a defect in (a), and no wording can
close it without a provenance record the mechanism does not keep.

This file exists so the retraction is mechanical rather than a paragraph
someone has to believe.
"""

import tempfile
import unittest
from pathlib import Path

from itsf.mc import supplement_contract as sc
from itsf.mc import supplement_runner as sr

INTENDED = b'{"supplement": "bytes"}'
INCIDENT = "INC-0123456789ab"


class _Counting(unittest.TestCase):
    """Counts reads of the FINAL name during one call."""

    def _run(self, setup):
        real = Path.read_bytes
        seen = []

        def counting(this):
            payload = real(this)
            seen.append((this.name, payload))
            return payload

        out = Path(tempfile.mkdtemp())
        setup(out)
        Path.read_bytes = counting
        try:
            try:
                action = sr.resolve_partial(out_dir=out, filename="f.json",
                                            intended=INTENDED,
                                            incident_id=INCIDENT)
                outcome = action.action
            except sr.SupplementRunnerError as exc:
                outcome = "REFUSED:" + str(exc).split(":")[0]
        finally:
            Path.read_bytes = real
        final_reads = [payload for name, payload in seen if name == "f.json"]
        return outcome, final_reads


class TestEveryPathThatSealsAFinalReadItBackFirst(_Counting):

    def test_already_sealed_reads_the_final_and_compares_it(self):
        """The branch §12.5 called unverified. It reads and compares."""
        outcome, reads = self._run(
            lambda out: (out / "f.json").write_bytes(INTENDED))
        self.assertEqual("already_sealed", outcome)
        self.assertEqual(1, len(reads))
        self.assertEqual(INTENDED, reads[0])

    def test_promotion_reads_the_final_and_compares_it(self):
        outcome, reads = self._run(lambda out: None)
        self.assertEqual("promote", outcome)
        self.assertEqual(1, len(reads))
        self.assertEqual(INTENDED, reads[0])

    def test_a_resumed_promotion_reads_the_final_too(self):
        outcome, reads = self._run(
            lambda out: (out / ("f.json" + sc.PARTIAL_SUFFIX)
                         ).write_bytes(INTENDED))
        self.assertEqual("promote", outcome)
        self.assertEqual(1, len(reads))
        self.assertEqual(INTENDED, reads[0])

    def test_differing_bytes_are_refused_after_the_same_read(self):
        outcome, reads = self._run(
            lambda out: (out / "f.json").write_bytes(b"something else"))
        self.assertTrue(outcome.startswith("REFUSED:supplement_seal_conflict"))
        self.assertEqual(1, len(reads))
        self.assertNotEqual(INTENDED, reads[0])

    def test_the_only_path_with_no_final_read_seals_no_final(self):
        """`retry_permitted` never reads FINAL — because there is none, and
        it claims none. An unread FINAL and an absent FINAL are different
        facts, which is the distinction §12.5 lost."""
        outcome, reads = self._run(
            lambda out: (out / ("f.json" + sc.PARTIAL_SUFFIX)
                         ).write_bytes(b"stale residue"))
        self.assertEqual("retry_permitted", outcome)
        self.assertEqual([], reads)


class TestTheTwoChecksAreTheSameCheck(unittest.TestCase):
    """The load-bearing claim of the retraction, asserted against source
    rather than asserted in prose: both branches compare FINAL's bytes to
    `intended` and neither does anything else with them."""

    def test_both_comparisons_are_against_intended(self):
        import inspect
        source = inspect.getsource(sr.resolve_partial)
        self.assertIn("existing == intended", source)
        self.assertIn("final.read_bytes() != intended", source)

    def test_the_class_with_no_instance_is_named_in_the_record(self):
        doc = (Path(__file__).resolve().parents[1] / "ops"
               / "N09_EXECUTION_PATH_DESIGN_R3.md")
        text = doc.read_text(encoding="utf-8")
        self.assertIn("14.", text)
        self.assertIn("12.5", text)


if __name__ == "__main__":
    unittest.main()
