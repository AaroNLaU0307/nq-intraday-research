"""Invariant 8 of dec-registry-migration-2026-08-27 — absence is a refusal.

WHAT WAS WRONG. `_read_text` returned "" for a missing file, and the
downstream refusal for an empty registry is byte-identical to the refusal
for a real registry with no chain for that id:

    "no supplement event chain exists for this id - NOT AUTHORIZED
     (default refuse; a missing chain is never a permissive default)"

So a wrong path looked exactly like "nothing has been authorised yet".
Measured before the fix, not inferred.

WHY IT MATTERS MOST NOW. The migration ruling directs the registry out of
the synced tree, and the path is constructed in five production places. One
un-updated site would then refuse quietly, in language that reads as correct
governance, indefinitely. The seat classified it as the same defect shape as
calling a crash "unauthorised" — a failure the system cannot see wearing the
costume of a refusal it understands.

WHY REFUSING IS SAFE. The empty string was never a legitimate registry
state: the governed file has existed and been appended to since the first
trial, and an append-only file does not become empty. There is no case where
"absent" should be read as "empty".
"""

import unittest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from itsf.mc import registry_boundary as rb


class TestAbsenceRefuses(unittest.TestCase):

    def test_a_missing_registry_raises_rather_than_reading_empty(self):
        with self.assertRaises(rb.BoundaryError):
            rb._read_text(Path("C:/definitely/not/here/TRIAL_REGISTRY.md"))

    def test_read_snapshot_refuses_too(self):
        """The refusal must survive the layer above; a snapshot of nothing
        is what everything downstream would reason about."""
        with self.assertRaises(rb.BoundaryError):
            rb.read_snapshot("C:/definitely/not/here/TRIAL_REGISTRY.md")

    def test_the_message_says_why_absence_is_not_emptiness(self):
        """A refusal an operator cannot act on is barely better than the
        silent empty string. It has to say the path is wrong."""
        try:
            rb.read_snapshot("C:/definitely/not/here/TRIAL_REGISTRY.md")
        except rb.BoundaryError as exc:
            text = str(exc)
        self.assertIn("absent", text)
        self.assertIn("append-only", text)
        self.assertNotIn("not authorised yet.", text.replace(
            "never that nothing has been authorised yet.", ""))

    def test_the_real_registry_still_reads(self):
        """The obvious failure of the fix: refusing everything."""
        snapshot = rb.read_snapshot()
        self.assertGreater(snapshot.n_bytes, 0)
        self.assertEqual(64, len(snapshot.sha256))

    def test_an_empty_but_present_file_is_still_read_not_refused(self):
        """The distinction the fix draws is ABSENT vs EMPTY. A file that
        exists and happens to be empty is a different fact — it is a
        registry someone truncated, and the anti-rollback witness is what
        catches that. Conflating the two would hide a real incident behind
        a path error."""
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            empty = Path(d) / "TRIAL_REGISTRY.md"
            empty.write_text("", encoding="utf-8")
            snapshot = rb.read_snapshot(str(empty))
            self.assertEqual(0, snapshot.n_bytes)


class TestATombstoneIsRefusedByName(unittest.TestCase):
    """MIGRATION-PLAN REVIEW, HIGH/medium confidence — and it reproduced.

    The absence check refuses a MISSING file. A migration tombstone is
    PRESENT, so it read as a 97-byte snapshot and the downstream refusal was
    the same string a missing registry gives: "no supplement event chain
    exists for this id". A deliberate marker reading as "nothing has been
    authorised yet" is the defect the absence check exists to close, wearing
    a different costume.

    NOT WIDENED TO "reject anything unparseable". A truncated or rolled-back
    registry is a DIFFERENT incident and the anti-rollback witness is its
    designed detector; folding it in here would hide a real incident behind
    a path error. So the tombstone is refused by its own marker."""

    def _tomb(self, body):
        import tempfile
        d = Path(tempfile.mkdtemp())
        t = d / "TRIAL_REGISTRY.md"
        t.write_text(body, encoding="utf-8")
        return t

    def test_a_tombstone_refuses(self):
        t = self._tomb("%s\nMoved to the itsf-registry repository.\n"
                       % rb.REGISTRY_TOMBSTONE_MARKER)
        with self.assertRaises(rb.BoundaryError):
            rb.read_snapshot(str(t))

    def test_the_refusal_says_it_is_a_tombstone_not_an_empty_registry(self):
        t = self._tomb("%s -> C:/new/place\n" % rb.REGISTRY_TOMBSTONE_MARKER)
        try:
            rb.read_snapshot(str(t))
        except rb.BoundaryError as exc:
            text = str(exc)
        self.assertIn("tombstone", text)
        self.assertIn("C:/new/place", text)

    def test_an_ordinary_truncated_registry_is_still_read(self):
        """The line this draws: truncation goes to the witness, not here."""
        t = self._tomb("")
        self.assertEqual(0, rb.read_snapshot(str(t)).n_bytes)

    def test_the_real_registry_carries_no_marker(self):
        """Otherwise the guard would refuse the live registry."""
        repo = Path(__file__).resolve().parents[1]
        text = (repo / "ops" / "TRIAL_REGISTRY.md").read_text(encoding="utf-8")
        self.assertNotIn(rb.REGISTRY_TOMBSTONE_MARKER, text)


class TestWhatTheDefectLookedLike(unittest.TestCase):
    """Pinned so the reason survives the fix.

    If these two refusals ever become distinguishable by some other route,
    the fix above stops being the only thing standing between a path typo
    and a plausible-looking refusal — worth knowing, not worth assuming."""

    def test_the_two_refusals_are_still_identical_for_a_present_registry(self):
        from itsf.mc import supplement_registry as sr
        import io
        repo = Path(__file__).resolve().parents[1]
        real = io.open(repo / "ops" / "TRIAL_REGISTRY.md",
                       encoding="utf-8").read()
        _v_empty, r_empty = sr.find_live_authorization("", "MC-DS-S001")
        _v_real, r_real = sr.find_live_authorization(real, "MC-DS-S001")
        self.assertEqual(r_empty, r_real,
                         "the empty-vs-no-chain refusals diverged; the "
                         "absence check is no longer the only guard against "
                         "a path typo reading as 'not authorised yet'")


if __name__ == "__main__":
    unittest.main()
