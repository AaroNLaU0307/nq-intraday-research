"""The emptiness guard, mutation-proven without touching quant-data.

Five tests were converted on 2026-08-29 from "the governed subtrees do not
exist" to "they exist by grant and are EMPTY". That conversion is only
worth anything if the new form actually fires, and the obvious way to check
-- write a file into a governed subtree -- is not available: the grant
covered CREATING the two empty parents and nothing else. Writing into them
needs the execution authorization, which has not been given.

So the helper is exercised against temporary directories instead, with
`GOVERNED_SUBTREES` redirected. What is under test is the helper's logic,
which is the only new thing; the real paths are supplied by a constant that
is asserted separately.
"""

import tempfile
import unittest
from pathlib import Path

import _governed_subtrees as gs

REPO = Path(__file__).resolve().parents[1]


class TestTheEmptinessCheckFires(unittest.TestCase):

    def setUp(self):
        self._real = gs.GOVERNED_SUBTREES
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.a, self.b = base / "runs" / "supplements", base / "arch" / "supplements"
        for p in (self.a, self.b):
            p.mkdir(parents=True)
        gs.GOVERNED_SUBTREES = (self.a, self.b)

    def tearDown(self):
        gs.GOVERNED_SUBTREES = self._real
        self._tmp.cleanup()

    def test_two_empty_subtrees_plus_a_used_grant_pass(self):
        gs.assert_governed_subtrees_are_empty(REPO)

    def test_a_FILE_in_a_subtree_fails(self):
        """The case the old `not exists()` form could never have caught."""
        (self.a / "leaked.json").write_bytes(b"{}")
        with self.assertRaises(AssertionError) as caught:
            gs.assert_governed_subtrees_are_empty(REPO)
        self.assertIn("leaked.json", str(caught.exception))
        self.assertIn("needs the execution authorization",
                      str(caught.exception))

    def test_a_nested_DIRECTORY_in_a_subtree_fails(self):
        """A run directory appearing without the runtime grant."""
        (self.b / "MC-DS-S001_20260829T000000Z").mkdir()
        with self.assertRaises(AssertionError) as caught:
            gs.assert_governed_subtrees_are_empty(REPO)
        self.assertIn("MC-DS-S001", str(caught.exception))

    def test_a_VANISHED_subtree_fails_differently(self):
        """Removal is not something any code path may do either, and it is
        a different defect from a leak -- so it says so."""
        self.a.rmdir()
        with self.assertRaises(AssertionError) as caught:
            gs.assert_governed_subtrees_are_empty(REPO)
        self.assertIn("is gone", str(caught.exception))

    def test_existence_without_a_recorded_grant_fails(self):
        """Existence alone proves nothing -- something could have created
        them unauthorized. The check is tied to the ledger row."""
        with tempfile.TemporaryDirectory() as fake_repo:
            ops = Path(fake_repo) / "ops"
            ops.mkdir()
            (ops / "DIRECTORY_CREATION_GRANTS.md").write_text(
                "no grant here", encoding="utf-8")
            with self.assertRaises(AssertionError) as caught:
                gs.assert_governed_subtrees_are_empty(Path(fake_repo))
        self.assertIn("outside any authorization", str(caught.exception))


class TestTheUntouchedCheckFires(unittest.TestCase):

    def setUp(self):
        self._real = gs.GOVERNED_SUBTREES
        self._tmp = tempfile.TemporaryDirectory()
        self.a = Path(self._tmp.name) / "supplements"
        self.a.mkdir()
        gs.GOVERNED_SUBTREES = (self.a,)

    def tearDown(self):
        gs.GOVERNED_SUBTREES = self._real
        self._tmp.cleanup()

    def test_an_untouched_subtree_passes(self):
        before = gs.snapshot()
        gs.assert_governed_subtrees_untouched(before, "nothing at all")

    def test_a_write_between_the_snapshots_fails(self):
        before = gs.snapshot()
        (self.a / "residue").write_bytes(b"x")
        with self.assertRaises(AssertionError) as caught:
            gs.assert_governed_subtrees_untouched(before, "the thing I ran")
        self.assertIn("the thing I ran", str(caught.exception))

    def test_creation_between_the_snapshots_fails(self):
        self.a.rmdir()
        before = gs.snapshot()
        self.assertEqual({str(self.a): None}, before)
        self.a.mkdir()
        with self.assertRaises(AssertionError):
            gs.assert_governed_subtrees_untouched(before, "the thing I ran")

    def test_absent_and_empty_are_not_the_same_reading(self):
        """`None` vs `()`. "I could not look" must never read as "nothing
        is there" -- the collapse the sister repository spent five review
        rounds on."""
        self.assertEqual((), gs.contents(self.a))
        self.a.rmdir()
        self.assertIsNone(gs.contents(self.a))


class TestTheRealConstantIsStillTheRealPaths(unittest.TestCase):
    """The helper above is tested against temp dirs, so the one thing that
    could silently rot is the constant naming the real ones."""

    def test_it_names_exactly_the_two_granted_paths(self):
        got = sorted(str(p) for p in gs.GOVERNED_SUBTREES)
        want = sorted([
            str(Path(r"C:\Users\Aaron\quant-data\itsf-runs") / "supplements"),
            str(Path(r"C:\Users\Aaron\quant-data\itsf-runs-archive")
                / "supplements")])
        self.assertEqual(want, got)

    def test_both_appear_verbatim_in_the_grant_row(self):
        record = (REPO / "ops" / "DIRECTORY_CREATION_GRANTS.md").read_text(
            encoding="utf-8")
        for p in gs.GOVERNED_SUBTREES:
            with self.subTest(path=str(p)):
                self.assertIn(str(p), record)


if __name__ == "__main__":
    unittest.main()
