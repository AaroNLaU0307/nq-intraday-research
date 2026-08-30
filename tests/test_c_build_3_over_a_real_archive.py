"""C_BUILD_3 driven by REAL snapshots of a REAL directory.

THE JOINT THAT HAD NOT BEEN WALKED. `run_c_build_3` takes `archive_before`
and `archive_after` as arguments, and every existing test hands it
tuple LITERALS -- `(("a.json", 2, "d" * 64),)`. So the function was well
tested and the SEAM was not: nothing had ever produced those tuples with
`supplement_bytes_snapshot` around a real directory operation.

WHY THAT SEAM CAN FAIL SILENTLY. `supplement_bytes_snapshot` keys entries
by a POSIX RELATIVE name; `_archived_bytes_lost` looks them up by that key.
If the two ever disagreed about the name form -- absolute vs relative,
backslash vs slash, rooted at a different directory -- the lookup would
never match. In one direction that fails closed (everything looks lost),
which is the safe direction; in the other, comparing a snapshot against
ITSELF passes whatever happened in between. Neither is visible from a test
that writes both tuples by hand.

Same shape as the C_BUILD_1 chain before the rehearsal walked it: every
part tested, the joint untested.

WHAT IS NOT HAPPENING HERE. No real archive is performed -- archiving needs
an execution authorization that has not been given. Every directory below
is a temporary one, and the "archive" is an ordinary file copy standing in
for the operation whose EFFECTS C_BUILD_3 classifies.
"""

import hashlib
import shutil
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from itsf.mc import day_strata_pipeline as pipe


class _Archive:
    """A real directory, snapshotted the way production would."""

    def __init__(self, case):
        self._tmp = TemporaryDirectory()
        case.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "archive"
        self.root.mkdir()
        self.sealed = Path(self._tmp.name) / "DAY_STRATA_SUPPLEMENT.json"

    def seal(self, body=b'{"schema": "mc_day_strata_supplement.v1"}'):
        self.sealed.write_bytes(body)
        return hashlib.sha256(body).hexdigest()

    def put(self, relative, body):
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body)
        return target

    def snapshot(self):
        return pipe.supplement_bytes_snapshot(self.root)

    def classify(self, digest, before, after):
        return pipe.run_c_build_3(sealed_path=self.sealed,
                                  local_seal_sha256=digest,
                                  archive_before=before, archive_after=after)


class TestTheSnapshotAndTheComparisonAGREE(unittest.TestCase):
    """The seam itself, and the part no literal-tuple test could reach."""

    def test_a_snapshot_compared_against_itself_reports_no_loss(self):
        a = _Archive(self)
        digest = a.seal()
        a.put("run/manifest.jsonl", b"one")
        a.put("run/nested/deep.json", b"two")
        snap = a.snapshot()
        self.assertEqual(2, len(snap),
                         "two files were written; the snapshot holds %d"
                         % len(snap))
        self.assertIsNone(a.classify(digest, snap, snap).failure)

    def test_the_names_the_snapshot_emits_are_the_names_lookup_uses(self):
        """If these disagreed, every entry would look lost and C_BUILD_3
        would refuse every successful archive -- or, comparing a snapshot
        to itself, pass whatever happened."""
        a = _Archive(self)
        a.put("run/nested/deep.json", b"two")
        names = [name for name, _size, _digest in a.snapshot()]
        self.assertEqual(["run/nested/deep.json"], names)
        self.assertNotIn("\\", names[0])
        self.assertFalse(Path(names[0]).is_absolute())

    def test_adding_files_is_FINE_because_archiving_adds(self):
        """The one-directional property, over a real copy rather than an
        argument about tuples."""
        a = _Archive(self)
        digest = a.seal()
        a.put("existing.json", b"already archived")
        before = a.snapshot()
        shutil.copy(a.sealed, a.root / a.sealed.name)   # the "archive"
        after = a.snapshot()
        self.assertGreater(len(after), len(before))
        self.assertIsNone(a.classify(digest, before, after).failure,
                          "a successful archive was refused")


class TestRealLossesAreCaught(unittest.TestCase):

    def test_a_really_deleted_file_refuses(self):
        a = _Archive(self)
        digest = a.seal()
        victim = a.put("prior/evidence.json", b"an earlier run's bytes")
        before = a.snapshot()
        victim.unlink()
        outcome = a.classify(digest, before, a.snapshot())
        self.assertEqual("archived_bytes_deleted", outcome.failure.code)
        self.assertIn("evidence.json", outcome.failure.detail)

    def test_a_really_overwritten_file_refuses(self):
        """Present but different is a loss of the bytes that were there."""
        a = _Archive(self)
        digest = a.seal()
        victim = a.put("prior/evidence.json", b"an earlier run's bytes")
        before = a.snapshot()
        victim.write_bytes(b"something else entirely")
        outcome = a.classify(digest, before, a.snapshot())
        self.assertEqual("archived_bytes_deleted", outcome.failure.code)

    def test_a_same_SIZE_overwrite_is_caught_too(self):
        """Size alone would miss this; the digest is what makes the check
        real, and a same-length replacement is the case that proves it."""
        a = _Archive(self)
        digest = a.seal()
        victim = a.put("prior/evidence.json", b"AAAAAAAA")
        before = a.snapshot()
        victim.write_bytes(b"BBBBBBBB")
        self.assertEqual(8, victim.stat().st_size)
        outcome = a.classify(digest, before, a.snapshot())
        self.assertEqual("archived_bytes_deleted", outcome.failure.code)

    def test_a_whole_vanished_archive_root_refuses(self):
        a = _Archive(self)
        digest = a.seal()
        a.put("prior/evidence.json", b"bytes")
        before = a.snapshot()
        shutil.rmtree(a.root)
        outcome = a.classify(digest, before, a.snapshot())
        self.assertEqual("archived_bytes_deleted", outcome.failure.code)


class TestTheSealsImmutabilityIsRECOMPUTED(unittest.TestCase):
    """§11.3's flag-read warning: a boolean saying "unchanged" is not
    evidence. These mutate the real file and let it recompute."""

    def test_a_byte_changed_on_disk_refuses(self):
        a = _Archive(self)
        digest = a.seal()
        snap = a.snapshot()
        a.sealed.write_bytes(b'{"schema": "mc_day_strata_supplement.v2"}')
        outcome = a.classify(digest, snap, snap)
        self.assertEqual("local_seal_mutated", outcome.failure.code)

    def test_a_same_length_change_refuses_as_well(self):
        a = _Archive(self)
        body = b"0123456789"
        digest = a.seal(body)
        snap = a.snapshot()
        a.sealed.write_bytes(b"9876543210")
        self.assertEqual(len(body), a.sealed.stat().st_size)
        outcome = a.classify(digest, snap, snap)
        self.assertEqual("local_seal_mutated", outcome.failure.code)

    def test_a_vanished_seal_refuses_DIFFERENTLY(self):
        """Absent and mutated are different defects and an operator needs
        different actions, so they carry different codes."""
        a = _Archive(self)
        digest = a.seal()
        snap = a.snapshot()
        a.sealed.unlink()
        outcome = a.classify(digest, snap, snap)
        self.assertEqual("local_seal_absent", outcome.failure.code)

    def test_a_seal_replaced_by_a_DIRECTORY_refuses(self):
        """`is_file()` rather than `exists()`. A directory where the seal
        should be is not a seal, and `exists()` would call it present."""
        a = _Archive(self)
        digest = a.seal()
        snap = a.snapshot()
        a.sealed.unlink()
        a.sealed.mkdir()
        outcome = a.classify(digest, snap, snap)
        self.assertEqual("local_seal_absent", outcome.failure.code)


class TestTheHarnessIsNotVacuous(unittest.TestCase):

    def test_an_untouched_archive_really_passes(self):
        """If every case refused, the refusal tests above would prove
        nothing."""
        a = _Archive(self)
        digest = a.seal()
        a.put("prior/evidence.json", b"bytes")
        snap = a.snapshot()
        self.assertIsNone(a.classify(digest, snap, snap).failure)

    def test_the_snapshot_really_sees_the_files(self):
        a = _Archive(self)
        a.put("one.json", b"1")
        a.put("two/three.json", b"22")
        self.assertEqual(2, len(a.snapshot()))


if __name__ == "__main__":
    unittest.main()
