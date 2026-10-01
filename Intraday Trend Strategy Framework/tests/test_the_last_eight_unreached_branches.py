"""The eight lines coverage said nothing had ever executed.

FOUND BY MEASURING, not by reading. `day_strata_rows` and
`day_strata_pipeline` were at 93% and 95% with eight uncovered lines
between them, and every one of them is a REFUSAL or the recording half of
a snapshot -- exactly the code whose whole job is to be reached on the bad
day and is therefore never reached on a good one.

THE ONE THAT MATTERS MOST is `supplement_bytes_snapshot`'s loop body. Its
docstring says "the DIRECTORY is the universe... everything present is
recorded, so a byte that should not be there changes the snapshot instead
of being invisible to it". Coverage said no test had ever pointed it at a
directory that contained a file. Only the empty case ran.

That is not a cosmetic gap. C_BUILD_1 asserts the supplement set is EMPTY
and UNCHANGED using this snapshot. A snapshot that silently returned `()`
for a non-empty directory would make C_BUILD_1 pass on a dirty root -- the
same false-pass direction as reading a poisoned chain's default, and just
as reachable without anybody making a mistake.
"""

import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from itsf.mc import day_strata_pipeline as dsp
from itsf.mc import day_strata_rows as dsr
from itsf.mc import day_strata_supplement as ds
from itsf.s0 import dataset as _s0


class TestTheSnapshotActuallyRECORDS(unittest.TestCase):
    """The half that was never run."""

    def test_a_file_in_the_root_appears_with_its_size_and_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            body = b"not supposed to be here"
            (Path(tmp) / "stray.json").write_bytes(body)
            snap = dsp.supplement_bytes_snapshot(Path(tmp))
        self.assertEqual(
            (("stray.json", len(body), hashlib.sha256(body).hexdigest()),),
            snap)

    def test_nested_files_are_recorded_with_posix_relative_names(self):
        """`rglob` plus `as_posix` -- so the snapshot is the same on any
        platform and a file hidden one level down is still in the universe."""
        with tempfile.TemporaryDirectory() as tmp:
            deep = Path(tmp) / "a" / "b"
            deep.mkdir(parents=True)
            (deep / "buried.txt").write_bytes(b"x")
            names = [row[0] for row in dsp.supplement_bytes_snapshot(Path(tmp))]
        self.assertEqual(["a/b/buried.txt"], names)

    def test_directories_themselves_are_not_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "empty_dir").mkdir()
            self.assertEqual((), dsp.supplement_bytes_snapshot(Path(tmp)))

    def test_a_changed_byte_changes_the_snapshot(self):
        """The property the whole thing exists for, executed."""
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "f.bin"
            target.write_bytes(b"before")
            first = dsp.supplement_bytes_snapshot(Path(tmp))
            target.write_bytes(b"after!")
            second = dsp.supplement_bytes_snapshot(Path(tmp))
        self.assertEqual(len(first), len(second))
        self.assertNotEqual(first, second)

    def test_and_C_BUILD_1_therefore_refuses_a_dirty_root(self):
        """The consequence, end to end. A snapshot that could not see files
        would make this pass, which is why the gap was worth closing."""
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "leftover").write_bytes(b"residue")
            snap = dsp.supplement_bytes_snapshot(Path(tmp))
            with self.assertRaises(Exception) as caught:
                dsp._assert_c_build_1(snap, snap, "runs_root")
        self.assertIn("runs_root", str(caught.exception))


class TestTheDeclaredDigestFallbacks(unittest.TestCase):

    def test_a_product_carrying_it_as_an_ATTRIBUTE_is_accepted(self):
        """The second getter -- reached only when the first one raises."""

        class _Product:
            rows_digest = "a" * 64

        self.assertEqual("a" * 64, dsp._declared_digest(_Product()))

    def test_a_product_carrying_it_as_a_KEY_is_accepted(self):
        self.assertEqual("b" * 64,
                         dsp._declared_digest({"rows_digest": "b" * 64}))

    def test_a_product_carrying_it_NOWHERE_refuses_by_name(self):
        class _Bare:
            pass

        with self.assertRaises(dsr.DayStrataRowsError) as caught:
            dsp._declared_digest(_Bare())
        self.assertEqual("product_carries_no_rows_digest",
                         caught.exception.code)
        self.assertIn("_Bare", str(caught.exception))

    def test_an_empty_string_digest_is_not_a_digest(self):
        """`if isinstance(value, str) and value` -- the truthiness half.
        An empty digest would otherwise be returned as one."""
        with self.assertRaises(dsr.DayStrataRowsError):
            dsp._declared_digest({"rows_digest": ""})


class TestTheVocabularyDriftRefusals(unittest.TestCase):
    """Both directions of `assert_vocabularies_agree`, which is called
    before any row is built precisely so a drift cannot reach a row."""

    def test_a_vol_vocabulary_drift_refuses_and_prints_both_sides(self):
        with mock.patch.object(_s0, "VOL_ALL_LABELS",
                               tuple(ds.VOL_STRATA) + ("EXTRA",)):
            with self.assertRaises(dsr.DayStrataRowsError) as caught:
                dsr.assert_vocabularies_agree()
        self.assertEqual("vol_vocabulary_drift", caught.exception.code)
        self.assertIn("EXTRA", str(caught.exception))

    def test_an_event_vocabulary_drift_refuses_too(self):
        with mock.patch.object(_s0, "EVENT_STRATA",
                               tuple(ds.EVENT_STRATA) + ("GHOST",)):
            with self.assertRaises(dsr.DayStrataRowsError) as caught:
                dsr.assert_vocabularies_agree()
        self.assertEqual("event_vocabulary_drift", caught.exception.code)
        self.assertIn("GHOST", str(caught.exception))

    def test_the_real_vocabularies_do_agree(self):
        """The premise. If they had drifted for real, the two tests above
        would be asserting against an already-broken baseline."""
        dsr.assert_vocabularies_agree()


class TestTheMappingShapeRefusals(unittest.TestCase):
    """A ruled producer that hands back the wrong SHAPE must be refused by
    name, not crash later with an AttributeError somebody has to trace."""

    DAYS = ("2026-01-05", "2026-01-06")

    def _derive(self, vol_obj, event_map):
        with mock.patch.multiple(
                _s0,
                build_vol20_regime_mapping_from_universe=mock.Mock(
                    return_value=vol_obj),
                build_event_stratum_map=mock.Mock(return_value=event_map)):
            return dsr.derive_day_strata_rows(
                universe=object(), vol_method="ruled", flag_by_date={},
                event_na_mapping="ruled",
                expected_day_set=frozenset(self.DAYS))

    def test_a_vol_object_with_no_label_of_mapping_refuses(self):
        class _NoLabelOf:
            label_of = "not a mapping"

        with self.assertRaises(dsr.DayStrataRowsError) as caught:
            self._derive(_NoLabelOf(), {"stratum_of": {}})
        self.assertEqual("vol_mapping_shape", caught.exception.code)

    def test_an_event_map_with_no_stratum_of_mapping_refuses(self):
        class _Vol:
            label_of = {}

        with self.assertRaises(dsr.DayStrataRowsError) as caught:
            self._derive(_Vol(), {"stratum_of": ["not", "a", "mapping"]})
        self.assertEqual("event_mapping_shape", caught.exception.code)


class TestTheEventStratumVocabularyCheck(unittest.TestCase):

    DAYS = ("2026-01-05", "2026-01-06")

    def test_an_event_stratum_outside_the_vocabulary_refuses(self):
        class _Vol:
            label_of = {d: tuple(ds.VOL_STRATA)[0] for d in
                        ("2026-01-05", "2026-01-06")}

        bad = {d: "NOT_A_STRATUM" for d in self.DAYS}
        with mock.patch.multiple(
                _s0,
                build_vol20_regime_mapping_from_universe=mock.Mock(
                    return_value=_Vol()),
                build_event_stratum_map=mock.Mock(
                    return_value={"stratum_of": bad})):
            with self.assertRaises(dsr.DayStrataRowsError) as caught:
                dsr.derive_day_strata_rows(
                    universe=object(), vol_method="ruled", flag_by_date={},
                    event_na_mapping="ruled",
                    expected_day_set=frozenset(self.DAYS))
        self.assertEqual("event_stratum_outside_vocabulary",
                         caught.exception.code)
        self.assertIn("NOT_A_STRATUM", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
