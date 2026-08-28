"""The cost-calibration loader's refusals that nothing had ever executed.

FOUND by line coverage, and the interesting part is what the number meant.
`src/itsf/data/cost_calibration_loader.py` is the least-covered module in
the repository at 61.2% (next lowest 87.6%, repository total 93.1%). That
looks like a testing gap and mostly is not: the uncovered lines are the
REAL-DATA paths — `assert_real_run_allowed`, manifest verification,
`databento` decode, forensics over real frames — and
`REAL_DATA_READ_AUTHORIZED=NO`. Coverage stops where the authorization
does, which is the correct state, not a deficiency.

Saying "61% coverage, therefore under-tested" would be the same move this
week keeps producing: measure one thing, state another.

BUT NOT ALL OF IT. Four uncovered pieces need no real data at all, and one
of them is a safety boundary:

    _check_role      the MIXED-ROLE refusal — a path carrying another data
                     role's marker. Frozen data-role isolation, fail
                     closed, and never executed by any test.
    _decode          the `synthetic_csv` branch (reads a CSV, no vendor)
    _decode          the unknown-source_format refusal
    _spread_table    the missing-column refusal

A data-role isolation guard nobody has run is a guard nobody has seen work.
These tests add no production change and read no real data: every path here
is a temporary directory whose NAME carries the role markers.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from itsf.data import cost_calibration_loader as ccl
from itsf.data import validation


class TestTheRoleIsolationRefusals(unittest.TestCase):
    """`_check_role` is called before every read. Its own-role check was
    covered; its mixed-role check was not."""

    def _loader(self, dirname):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        job = Path(tmp.name) / dirname
        job.mkdir()
        return ccl.CostCalibrationLoader(job_dir=job)

    def test_a_path_without_the_role_marker_is_refused(self):
        loader = self._loader("some_other_place")
        with self.assertRaises(ccl.RoleError) as caught:
            loader._check_role()
        self.assertIn("non-cost path", str(caught.exception))

    def test_a_path_carrying_a_foreign_role_marker_is_refused(self):
        """THE ONE NOTHING HAD RUN. Own marker present is necessary and
        not sufficient: a directory named for both roles would pass the
        first check and hand cost-calibration code a signal-role tree."""
        loader = self._loader(
            "%s_and_%s" % (ccl.ROLE_DIRNAME, "development_signal"))
        with self.assertRaises(ccl.RoleError) as caught:
            loader._check_role()
        message = str(caught.exception)
        self.assertIn("foreign", message)
        self.assertIn("development_signal", message)
        self.assertIn("mixed-role", message)

    def test_every_other_declared_role_is_caught_as_foreign(self):
        """Not just the one I thought of. Each other member of the enum is
        tried, so a role added later is covered or this test names it."""
        others = [r.value for r in ccl.DataRole if r.value != ccl.ROLE_DIRNAME]
        self.assertTrue(others, "there is only one data role; this test is "
                                "asserting over nothing")
        for foreign in others:
            with self.subTest(foreign=foreign):
                loader = self._loader("%s__%s" % (ccl.ROLE_DIRNAME, foreign))
                with self.assertRaises(ccl.RoleError) as caught:
                    loader._check_role()
                self.assertIn(foreign, str(caught.exception))

    def test_the_clean_own_role_path_passes(self):
        """The over-reach these refusals invite."""
        self._loader(ccl.ROLE_DIRNAME)._check_role()


class TestDecodeRefusesWhatItCannotName(unittest.TestCase):

    def test_an_unknown_source_format_is_refused(self):
        with self.assertRaises(ValueError) as caught:
            ccl.CostCalibrationLoader._decode(Path("irrelevant"), "parquet")
        self.assertIn("unknown source_format", str(caught.exception))

    def test_the_synthetic_csv_branch_parses_and_normalises_ts(self):
        """No vendor library and no real data — a CSV written here. The
        branch existed uncovered, so nothing had shown that `ts` comes back
        as UTC-aware rather than as text."""
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "bbo.csv"
        path.write_text("ts,bid_px,ask_px\n"
                        "2026-01-05T14:30:00Z,100.00,100.25\n"
                        "2026-01-05T14:31:00Z,100.25,100.50\n",
                        encoding="utf-8")
        frame = ccl.CostCalibrationLoader._decode(path, "synthetic_csv")
        self.assertEqual(2, len(frame))
        self.assertEqual("UTC", str(frame["ts"].dt.tz))


class TestSpreadTableSchemaGap(unittest.TestCase):
    """`_spread_table` fails closed on a missing column rather than
    producing a table with a silently absent field."""

    def test_each_required_column_is_named_when_missing(self):
        full = pd.DataFrame({"ts": pd.to_datetime(["2026-01-05T14:30:00Z"]),
                             "bid_px": [100.0], "ask_px": [100.25]})
        for column in ("ts", "bid_px", "ask_px"):
            with self.subTest(missing=column):
                with self.assertRaises(validation.ValidationError) as caught:
                    ccl.CostCalibrationLoader._spread_table(
                        full.drop(columns=[column]))
                self.assertIn(column, str(caught.exception))
                self.assertIn("fail closed", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
