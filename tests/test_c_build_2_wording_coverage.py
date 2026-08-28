"""What `already_sealed` establishes, and what it does not.

CORRECTED 2026-08-29 (round-2 review, MEDIUM). This docstring used to end
"Nothing in that branch verifies anything; it compares", and used that to
argue (a)'s violation class was uncovered. §14 of the design retracts that:

    existing = final.read_bytes()      # the re-read
    if existing == intended:           # the verification

is the same check `supplement_post_promotion_verify` performs. Comparison
against `intended` IS the verification. The class "a FINAL that was never
re-read-verified is treated as sealed" has no instance, and the original
wording covered it.

Leaving the old text here while the design said the opposite meant a
reviewer reading the tests and a reviewer reading the design got different
stories from the same author. That is worse than either being wrong alone.

WHAT SURVIVES, and it is a different thing: `already_sealed` does not
establish PROVENANCE. It does not know who wrote the FINAL — a hand-copy,
a restore from backup, an older build. That is true, unclosable without a
provenance record the mechanism does not keep, and NOT part of (a)'s class.
§14.8 records it as a standalone fact about the mechanism.

WHAT THE ROUND-2 REVIEW ADDED, and it is the sharper point: whether a
comparison HAPPENED is a PROCESS property, and no post-call filesystem
state can establish it. Measured — a mutant that returns `already_sealed`
without reading anything leaves an identical post-call state. So the
route for (a) is a PINNED MECHANISM PROPERTY, held by
`test_wrong_bytes_are_still_refused` and the read-counting in
`test_every_sealed_final_was_read_back.py`, not by observing the tree.
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

    def test_a_final_of_unknown_provenance_is_accepted(self):
        """The PROVENANCE residual, pinned. Nothing here produced this
        FINAL. Its bytes ARE re-read and compared — that is the
        verification — but nothing establishes who wrote it.

        RENAMED 2026-08-29: was `..._accepted_on_bytes_alone`, which read
        as "accepted without checking". It is accepted ON its bytes, having
        checked them."""
        out = self._out()
        (out / "f.json").write_bytes(INTENDED)
        act = sr.resolve_partial(out_dir=out, filename="f.json",
                                 intended=INTENDED, incident_id="i1")
        self.assertEqual("already_sealed", act.action)

    def test_post_call_state_cannot_show_the_comparison_happened(self):
        """ROUND-2 HIGH, pinned as a test rather than as a paragraph.

        The post-call fact "FINAL present and bytes == intended" holds
        identically whether or not the mechanism compared anything —
        measured against a mutant that returns `already_sealed` without
        reading. So this observation is NOT evidence that verification
        occurred, and (a)'s detection route may not be described as a pure
        filesystem fact.

        What this test asserts is the observation's WEAKNESS, which is why
        it is worth having: it stops anyone re-deriving the wrong
        classification from a passing check."""
        out = self._out()
        (out / "f.json").write_bytes(INTENDED)
        sr.resolve_partial(out_dir=out, filename="f.json",
                           intended=INTENDED, incident_id="i1")
        observed = (out / "f.json").exists() and (
            out / "f.json").read_bytes() == INTENDED
        self.assertTrue(observed)
        self.assertIn("test_wrong_bytes_are_still_refused", dir(self),
                      "the behavioural pin that DOES hold the property must "
                      "live in this class; if it moves, this note is stale")

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

    def _force_branch_e(self):
        """Make the post-write re-read disagree, which is what branch E
        classifies. Patched at `Path.read_bytes` for the staging file only:
        the real trigger is a filesystem that hands back different bytes,
        which cannot be staged in a temp directory."""
        real = Path.read_bytes
        state = {"seen": False}

        def diverging(self):
            if self.name.endswith(sc.PARTIAL_SUFFIX) and not state["seen"]:
                state["seen"] = True
                return b"not what was written"
            return real(self)

        Path.read_bytes = diverging
        self.addCleanup(setattr, Path, "read_bytes", real)

    def test_branch_e_writes_the_named_divergent_file(self):
        """ADDED 2026-08-29. §12.7 claimed the class assertion below spanned
        all four outcomes; the wording review measured that it ran three and
        never reached branch E. That was an evidence-map error in the design
        document, not a defect in the mechanism — branch E was covered
        elsewhere — but a claim of four-outcome coverage that runs three is
        the same shape §12.8 is about, so it is closed rather than
        explained."""
        out = Path(tempfile.mkdtemp())
        self._force_branch_e()
        with self.assertRaises(sr.SupplementRunnerError) as caught:
            sr.resolve_partial(out_dir=out, filename="f.json",
                               intended=INTENDED, incident_id=INCIDENT)
        self.assertIn("supplement_partial_verify", str(caught.exception))
        self.assertIn("f.json.partial.divergent." + INCIDENT,
                      [p.name for p in out.iterdir()])

    def test_no_divergence_outcome_destroys_bytes(self):
        """The CLASS (c) actually names, asserted across all four outcomes.

        It now runs four. Before 2026-08-29 it ran three and the design
        document said four."""
        out = self._staged()
        sr.resolve_partial(out_dir=out, filename="f.json",
                           intended=INTENDED, incident_id=INCIDENT)
        self.assertTrue(list(out.iterdir()), "branch C destroyed the bytes")

        out = Path(tempfile.mkdtemp())                      # branch E
        self._force_branch_e()
        with self.assertRaises(sr.SupplementRunnerError):
            sr.resolve_partial(out_dir=out, filename="f.json",
                               intended=INTENDED, incident_id=INCIDENT)
        self.assertTrue(list(out.iterdir()), "branch E destroyed the bytes")

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

if __name__ == "__main__":
    unittest.main()
