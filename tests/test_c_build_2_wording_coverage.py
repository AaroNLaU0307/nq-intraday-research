"""What (a) of the §12 draft actually detects, versus what it claims.

The draft's (a) names its violation class as

    "一份没被复读校验过的 FINAL 被当作已封存"
    (a FINAL that was never re-read-verified, treated as sealed)

and gives its detection route as a fact about the filesystem AFTER the call:
FINAL, if present, has bytes == intended.

MEASURED: those are not the same set. `resolve_partial` returns
`already_sealed` for ANY pre-existing FINAL whose bytes match, whatever
produced it — a hand-copy, a restore from backup, an older build without
the post-promotion re-read. Nothing in that branch verifies anything; it
compares. The claimed class is strictly wider than the route that detects
it.

That is the same shape the sister repository spent five review rounds on:
the guard is narrower than the property it claims. It is worse than an
honest boundary, because a reader of the wording believes the wider class
is covered.

So the draft is corrected to name what it detects, and the residual — a
FINAL of unknown provenance is accepted on bytes alone — is PINNED HERE
rather than left silent. Closing it would need a provenance record the
mechanism does not have, and inventing one is a design change, which the
ruling forbids this draft from making.
"""

import tempfile
import unittest
from pathlib import Path

from itsf.mc import supplement_contract as sc
from itsf.mc import supplement_runner as sr

INTENDED = b'{"supplement": "bytes"}'
INCIDENT = "INC-0123456789ab"


class TestWhatAlreadySealedActuallyChecks(unittest.TestCase):

    def _out(self):
        return Path(tempfile.mkdtemp())

    def test_a_final_of_unknown_provenance_is_accepted_on_bytes_alone(self):
        """The residual, pinned. Nothing here produced this FINAL and
        nothing re-read-verified it; matching bytes are the whole test."""
        out = self._out()
        (out / "f.json").write_bytes(INTENDED)
        act = sr.resolve_partial(out_dir=out, filename="f.json",
                                 intended=INTENDED, incident_id="i1")
        self.assertEqual("already_sealed", act.action)

    def test_the_detection_route_passes_for_it(self):
        """(a)'s route is 'FINAL present => bytes == intended'. It holds
        here, which is exactly why the route cannot see the claimed class."""
        out = self._out()
        (out / "f.json").write_bytes(INTENDED)
        sr.resolve_partial(out_dir=out, filename="f.json",
                           intended=INTENDED, incident_id="i1")
        self.assertEqual(INTENDED, (out / "f.json").read_bytes())

    def test_wrong_bytes_are_still_refused(self):
        """What the route DOES detect, and the class the corrected wording
        names. This must keep working or the correction has traded one
        false claim for another."""
        out = self._out()
        (out / "f.json").write_bytes(b"different")
        with self.assertRaises(sr.SupplementRunnerError) as caught:
            sr.resolve_partial(out_dir=out, filename="f.json",
                               intended=INTENDED, incident_id="i1")
        self.assertIn("supplement_seal_conflict", str(caught.exception))

    def test_a_final_this_call_promoted_is_verified(self):
        """The half that IS covered: when the call does the promotion, the
        post-promotion re-read runs unconditionally."""
        out = self._out()
        act = sr.resolve_partial(out_dir=out, filename="f.json",
                                 intended=INTENDED, incident_id="i1")
        self.assertEqual("promote", act.action)
        self.assertIn("verified", act.detail)


class TestTheResidualIsWrittenDownRatherThanClaimedClosed(unittest.TestCase):
    """A residual that lives only in a test comment is one the next reader
    of the design document never sees."""

    def test_the_design_records_it(self):
        doc = (Path(__file__).resolve().parents[1] / "ops"
               / "N09_EXECUTION_PATH_DESIGN_R3.md")
        text = doc.read_text(encoding="utf-8")
        self.assertIn("already_sealed", text)
        self.assertIn("12.5", text)


if __name__ == "__main__":
    unittest.main()


class TestHowManyDivergenceOutcomesThereActuallyAre(unittest.TestCase):
    """(c) said "两条分歧结局". MEASURED: there are four.

        branch C                  retry_permitted        divergent file written
        branch E                  supplement_partial_verify   divergent file written
        divergent_partial_exists  refusal                residue stays as `.partial`
        incident_id_malformed     refusal                residue stays as `.partial`

    The claimed CLASS ("divergence happened and left no traceable residue")
    still holds for all four -- the last two leave the bytes in place under
    their original name, which is traceable. But the ROUTE as written
    enumerates two outcomes out of four, so a reader checking the route
    against reality finds it short. Third instance in this document of the
    same shape (see §12.5, §12.6).
    """

    def _staged(self, residue=b"stale"):
        out = Path(tempfile.mkdtemp())
        (out / ("f.json" + sc.PARTIAL_SUFFIX)).write_bytes(residue)
        return out

    def test_branch_c_writes_the_named_divergent_file(self):
        out = self._staged()
        act = sr.resolve_partial(out_dir=out, filename="f.json",
                                 intended=INTENDED, incident_id=INCIDENT)
        self.assertEqual("retry_permitted", act.action)
        self.assertEqual("f.json.partial.divergent." + INCIDENT,
                         act.preserved_as)
        self.assertIn(act.preserved_as, [p.name for p in out.iterdir()])

    def test_a_second_incident_with_the_same_id_refuses_and_keeps_both(self):
        """No named file is produced for THIS attempt, and nothing is lost:
        the residue stays as `.partial` and the prior evidence is intact."""
        out = self._staged()
        prior = out / ("f.json.partial.divergent." + INCIDENT)
        prior.write_bytes(b"prior incident")
        with self.assertRaises(sr.SupplementRunnerError) as caught:
            sr.resolve_partial(out_dir=out, filename="f.json",
                               intended=INTENDED, incident_id=INCIDENT)
        self.assertIn("divergent_partial_exists", str(caught.exception))
        names = sorted(p.name for p in out.iterdir())
        self.assertIn("f.json" + sc.PARTIAL_SUFFIX, names)
        self.assertEqual(b"prior incident", prior.read_bytes())

    def test_a_malformed_incident_id_refuses_and_keeps_the_residue(self):
        out = self._staged()
        with self.assertRaises(sr.SupplementRunnerError) as caught:
            sr.resolve_partial(out_dir=out, filename="f.json",
                               intended=INTENDED, incident_id="not an id")
        self.assertIn("incident_id_malformed", str(caught.exception))
        self.assertEqual([("f.json" + sc.PARTIAL_SUFFIX)],
                         [p.name for p in out.iterdir()])

    def test_no_divergence_outcome_destroys_bytes(self):
        """The CLASS (c) actually names, asserted across all four outcomes
        rather than across the two the route enumerates."""
        out = self._staged()
        sr.resolve_partial(out_dir=out, filename="f.json",
                           intended=INTENDED, incident_id=INCIDENT)
        self.assertTrue(list(out.iterdir()), "branch C destroyed the bytes")
        for bad_id, prior in ((INCIDENT, True), ("not an id", False)):
            out = self._staged()
            if prior:
                (out / ("f.json.partial.divergent." + INCIDENT)).write_bytes(b"p")
            with self.assertRaises(sr.SupplementRunnerError):
                sr.resolve_partial(out_dir=out, filename="f.json",
                                   intended=INTENDED, incident_id=bad_id)
            self.assertIn("f.json" + sc.PARTIAL_SUFFIX,
                          [p.name for p in out.iterdir()],
                          "a refusal destroyed the residue it refused over")
