"""The fifteen refusals in `day_strata_supplement` that had never run.

Coverage put the module at 90% with fifteen uncovered lines, and every one
is a REFUSAL -- code whose entire job is to be reached on the bad day, and
which is therefore never reached on a good one. An untested refusal is a
promise, not a mechanism: it can be wrong in either direction (never firing,
or firing with the wrong code) and the suite would stay green.

THE TWO WORTH SINGLING OUT are `seal_supplement_test_only`'s post-write
checks. The seal stages bytes to `.partial`, RE-READS them, byte-compares
against the intent, promotes with a single `os.replace`, then re-reads the
promoted file and compares AGAIN. Both comparisons existed and neither had
ever been made to fail.

They are the code that answers Sol's D-3 High finding -- "OneDrive
atomicity cannot be excluded by reading the code". Reading the code is
indeed not enough. So this makes the disk lie, in both places, and checks
that the seal notices: it refuses, and on the staging path it removes the
bad `.partial` rather than leaving debris a later run would have to
interpret.
"""

import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from itsf.mc import day_strata_supplement as dss

COMMIT = "a" * 40
TRIAL = "S0-T001"
DIGEST_A = "b" * 64
DIGEST_B = "c" * 64
_DAYS = (("2024-03-12", 2024, "T2", "CPI"),
         ("2025-01-10", 2025, "vol_na", "NFP"))


def _rows():
    return [{"trade_date": d, "year": y, "vol_stratum": v,
             "event_stratum": e} for d, y, v, e in _DAYS]


def _binding():
    return {"trial_id": TRIAL, "authorized_commit": COMMIT,
            "day_universe_digest": DIGEST_A,
            "method_version": "mc-freeze-v1",
            "source_input_sha256": DIGEST_B}


def _build():
    return dss.build_day_strata_supplement_test_only(
        _rows(), expected_day_set=frozenset(r["trade_date"] for r in _rows()),
        binding=_binding())


class TestTheSealNoticesWhenTheDiskLies(unittest.TestCase):
    """The pair that answers "atomicity cannot be excluded by reading the
    code" by not reading the code."""

    def test_a_short_staging_write_is_caught_on_the_re_read(self):
        supplement = _build()
        real_write = Path.write_bytes

        def truncating(self, data):
            return real_write(self, data[:-5])      # the disk lies

        with TemporaryDirectory() as tmp:
            with mock.patch.object(Path, "write_bytes", truncating):
                with self.assertRaises(dss.SupplementError) as caught:
                    dss.seal_supplement_test_only(supplement, Path(tmp))
            self.assertEqual("supplement_partial_verify",
                             caught.exception.code)
            self.assertIn("re-read differently", str(caught.exception))
            left = sorted(p.name for p in Path(tmp).iterdir())
        self.assertEqual([], left,
                         "the bad .partial was left on disk; a later run "
                         "would have to interpret debris the seal already "
                         "knew was wrong")

    def test_an_unremovable_bad_partial_still_REFUSES(self):
        """`except OSError: pass` around the unlink, and the priority it
        encodes. Cleaning up the debris is best-effort; REFUSING is not.
        If the two were reversed -- a failed cleanup swallowing the
        refusal -- a corrupt staging write would be reported as success."""
        supplement = _build()
        real_write = Path.write_bytes

        def truncating(self, data):
            return real_write(self, data[:-5])

        def cannot_remove(self, missing_ok=False):
            raise OSError("locked by another process")

        with TemporaryDirectory() as tmp:
            with mock.patch.object(Path, "write_bytes", truncating), \
                    mock.patch.object(Path, "unlink", cannot_remove):
                with self.assertRaises(dss.SupplementError) as caught:
                    dss.seal_supplement_test_only(supplement, Path(tmp))
            self.assertEqual("supplement_partial_verify",
                             caught.exception.code)
            left = sorted(p.name for p in Path(tmp).iterdir())
        self.assertEqual(1, len(left),
                         "the debris should still be there -- the point is "
                         "that it did not stop the refusal, not that it "
                         "vanished")
        self.assertTrue(left[0].endswith(".partial"), left)

    def test_the_final_file_is_re_read_AFTER_promotion_too(self):
        """The second comparison, which a correct staging write cannot
        exercise. `os.replace` succeeding is not proof the bytes survived."""
        supplement = _build()
        real_replace = os.replace

        def replace_then_corrupt(src, dst):
            real_replace(src, dst)
            Path(dst).write_bytes(b"{}")            # something moved it

        with TemporaryDirectory() as tmp:
            with mock.patch.object(dss.os, "replace", replace_then_corrupt):
                with self.assertRaises(dss.SupplementError) as caught:
                    dss.seal_supplement_test_only(supplement, Path(tmp))
        self.assertEqual("supplement_partial_verify", caught.exception.code)
        self.assertIn("post-promotion", str(caught.exception))

    def test_an_honest_disk_seals_and_returns_the_sha_of_what_it_wrote(self):
        """The premise. If sealing were broken outright, the two tests
        above would be measuring a failure that has nothing to do with the
        lie they inject."""
        import hashlib

        supplement = _build()
        with TemporaryDirectory() as tmp:
            digest = dss.seal_supplement_test_only(supplement, Path(tmp))
            final = Path(tmp) / dss.SUPPLEMENT_FILENAME
            self.assertTrue(final.exists())
            self.assertEqual(hashlib.sha256(final.read_bytes()).hexdigest(),
                             digest)
            self.assertEqual([dss.SUPPLEMENT_FILENAME],
                             [p.name for p in Path(tmp).iterdir()])


class TestTheBindingRefusals(unittest.TestCase):

    def test_a_binding_that_is_not_a_mapping_refuses(self):
        with self.assertRaises(dss.SupplementError) as caught:
            dss._validate_binding(["not", "a", "mapping"])
        self.assertEqual("supplement_binding_schema", caught.exception.code)
        self.assertIn("list", str(caught.exception))

    def test_a_binding_with_a_missing_or_extra_key_refuses(self):
        for mutate, label in (
                (lambda b: b.pop("trial_id"), "missing"),
                (lambda b: b.update(surprise="x"), "extra")):
            with self.subTest(case=label):
                bad = _binding()
                mutate(bad)
                with self.assertRaises(dss.SupplementError) as caught:
                    dss._validate_binding(bad)
                self.assertEqual("supplement_binding_schema",
                                 caught.exception.code)

    def test_an_empty_or_non_string_trial_id_refuses_by_its_own_code(self):
        """A DIFFERENT code from the schema failure: the field set is
        right and the value is wrong, which is a different defect."""
        for value in ("", 7, None):
            with self.subTest(value=value):
                bad = _binding()
                bad["trial_id"] = value
                with self.assertRaises(dss.SupplementError) as caught:
                    dss._validate_binding(bad)
                self.assertEqual("supplement_binding_malformed",
                                 caught.exception.code)
                self.assertIn("trial_id", str(caught.exception))

    def test_method_version_is_checked_by_the_same_rule(self):
        bad = _binding()
        bad["method_version"] = ""
        with self.assertRaises(dss.SupplementError) as caught:
            dss._validate_binding(bad)
        self.assertEqual("supplement_binding_malformed", caught.exception.code)


class TestTheRowRefusals(unittest.TestCase):

    def test_a_row_that_is_not_a_mapping_refuses_with_its_index(self):
        with self.assertRaises(dss.SupplementError) as caught:
            dss._validate_row(("tuple", "not", "mapping", "x"), 3)
        self.assertEqual("supplement_row_schema", caught.exception.code)
        self.assertIn("row 3", str(caught.exception))
        self.assertIn("tuple", str(caught.exception))

    def test_a_row_missing_a_field_refuses_and_names_it(self):
        row = _rows()[0]
        del row["year"]
        with self.assertRaises(dss.SupplementError) as caught:
            dss._validate_row(row, 0)
        self.assertEqual("supplement_row_schema", caught.exception.code)
        self.assertIn("year", str(caught.exception))

    def test_a_trade_date_that_is_not_ISO_refuses(self):
        """Checked as a STRING PATTERN, not by parsing. `12/03/2024` is a
        real date and still wrong here: the day universe is compared by
        exact string equality, so a differently-spelled day is a day the
        comparison cannot match."""
        for value in ("12/03/2024", "2024-3-12", "20240312", 20240312, None):
            with self.subTest(value=value):
                row = _rows()[0]
                row["trade_date"] = value
                with self.assertRaises(dss.SupplementError) as caught:
                    dss._validate_row(row, 1)
                self.assertEqual("supplement_row_schema",
                                 caught.exception.code)
                self.assertIn("not ISO", str(caught.exception))

    def test_an_extra_field_is_the_BLIND_GUARANTEE_violation_not_a_schema_one(self):
        """Forbidden-first, and the distinction is the whole point: an
        outcome field riding along is a different defect from an
        incomplete row, and only one of them is a leak."""
        row = _rows()[0]
        row["pnl_usd"] = 1234.5
        with self.assertRaises(dss.SupplementError) as caught:
            dss._validate_row(row, 0)
        self.assertEqual("supplement_forbidden_field", caught.exception.code)
        self.assertIn("blind guarantee", str(caught.exception))


class TestTheObjectRefusals(unittest.TestCase):

    def test_an_object_with_the_wrong_field_set_refuses(self):
        bad = dict(_build())
        bad.pop("n_rows")
        with self.assertRaises(dss.SupplementError) as caught:
            dss._validate_supplement_object(bad)
        self.assertEqual("supplement_object_schema", caught.exception.code)

    def test_a_wrong_schema_or_id_refuses(self):
        for key, value in (("schema", "something.else.v9"),
                           ("supplement_id", "MC-DS-S999")):
            with self.subTest(key=key):
                bad = dict(_build())
                bad[key] = value
                with self.assertRaises(dss.SupplementError) as caught:
                    dss._validate_supplement_object(bad)
                self.assertEqual("supplement_object_schema",
                                 caught.exception.code)
                self.assertIn(value, str(caught.exception))

    def test_an_n_rows_that_disagrees_with_the_rows_refuses(self):
        bad = dict(_build())
        bad["n_rows"] = bad["n_rows"] + 1
        with self.assertRaises(dss.SupplementError) as caught:
            dss._validate_supplement_object(bad)
        self.assertEqual("supplement_object_schema", caught.exception.code)
        self.assertIn("n_rows", str(caught.exception))


class TestTheBuilderRefusal(unittest.TestCase):

    def test_a_day_set_that_is_not_a_frozenset_refuses(self):
        """The sealed universe must ARRIVE as a frozenset. A list would be
        mutable between the authority and the row set."""
        with self.assertRaises(dss.SupplementError) as caught:
            dss.build_day_strata_supplement_test_only(
                _rows(), expected_day_set=[r["trade_date"] for r in _rows()],
                binding=_binding())
        self.assertEqual("supplement_day_set_authority",
                         caught.exception.code)
        self.assertIn("list", str(caught.exception))


class TestTheProductionEntryStillRefusesBeforeAnything(unittest.TestCase):

    def test_it_never_reaches_its_own_unreachable_line(self):
        """`run_supplement_production` ends with
        `raise AssertionError("unreachable: authorize_supplement always
        raises")`. That line is a tripwire, and the correct state of the
        world is that it stays uncovered -- so this asserts the REASON it
        is unreachable instead of trying to reach it."""
        with self.assertRaises(Exception) as caught:
            dss.authorize_supplement("any registry text at all")
        self.assertNotIsInstance(caught.exception, AssertionError)

        with self.assertRaises(Exception) as caught:
            dss.run_supplement_production()
        self.assertNotIsInstance(
            caught.exception, AssertionError,
            "the production entry reached its unreachable line, which means "
            "authorize_supplement stopped always raising")


if __name__ == "__main__":
    unittest.main()
