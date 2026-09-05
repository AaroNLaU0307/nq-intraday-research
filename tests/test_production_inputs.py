"""The four real inputs: the authorization is enforced, the rest is checked.

NO DEVELOPMENT DATA IS READ HERE. The two functions that open authorized
files are asserted STRUCTURALLY -- they must verify the authorization and go
through the gate-first loader. The two that do not (the frozen F10 table in
this repository, and the exchange calendar) are exercised for real, because
they can be.

WHY THE AUTHORIZATION CHECK IS CODE AND NOT A COMMENT. `_check_role` cannot
tell the attested primary from an unattested copy -- measured 2026-09-05,
both pass it -- so without an explicit path and manifest check the constants
naming Aaron's authorization would protect nothing.
"""

import ast
import hashlib
import json
import unittest
from pathlib import Path

from itsf.mc import production_inputs as pi

MODULE = Path(pi.__file__)


class TestTheAuthorizationIsEnforced(unittest.TestCase):

    def test_a_different_job_dir_is_refused(self):
        """The unattested OneDrive copy passes `_check_role`. It must not
        pass this."""
        other = (r"C:\Users\Aaron\OneDrive\Desktop\CV\quant-data"
                 r"\databento-archive\intraday-trend\development_signal"
                 r"\GLBX-20260727-DL3BEBCHJA")
        with self.assertRaises(PermissionError) as caught:
            pi.verify_authorized_job_dir(other)
        self.assertIn("not the authorized directory", str(caught.exception))

    def test_a_changed_manifest_is_refused(self, ):
        """The authorization named a manifest by hash, so the authorized file
        set is whatever THAT manifest listed. A different manifest is a
        different set."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / AUTH_NAME
            fake.mkdir(parents=True)
            (fake / "manifest.json").write_text("{}", encoding="utf-8")
            # Point the constant at the temp copy so the PATH check passes
            # and the HASH check is the one under test.
            original = pi.AUTHORIZED_JOB_DIR
            try:
                pi.AUTHORIZED_JOB_DIR = fake
                with self.assertRaises(PermissionError) as caught:
                    pi.verify_authorized_job_dir(fake)
            finally:
                pi.AUTHORIZED_JOB_DIR = original
        self.assertIn("authorization pinned", str(caught.exception))

    def test_a_missing_manifest_refuses_rather_than_reading_anything(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / AUTH_NAME
            empty.mkdir(parents=True)
            original = pi.AUTHORIZED_JOB_DIR
            try:
                pi.AUTHORIZED_JOB_DIR = empty
                with self.assertRaises(FileNotFoundError):
                    pi.verify_authorized_job_dir(empty)
            finally:
                pi.AUTHORIZED_JOB_DIR = original

    def test_the_pinned_constants_are_the_ones_aaron_named(self):
        self.assertEqual("GLBX-20260727-DL3BEBCHJA",
                         pi.AUTHORIZED_JOB_DIR.name)
        self.assertIn("development_signal", str(pi.AUTHORIZED_JOB_DIR))
        self.assertEqual(64, len(pi.AUTHORIZED_MANIFEST_SHA256))


AUTH_NAME = "GLBX-20260727-DL3BEBCHJA"


class TestTheReadersAreGateFirst(unittest.TestCase):
    """Structural, because running them opens Development files."""

    def _calls(self, function_name):
        tree = ast.parse(MODULE.read_text(encoding="utf-8"))
        fn = next(n for n in ast.walk(tree)
                  if isinstance(n, ast.FunctionDef) and n.name == function_name)
        return {getattr(n.func, "attr", None) or getattr(n.func, "id", None)
                for n in ast.walk(fn) if isinstance(n, ast.Call)}

    def test_both_readers_verify_the_authorization_first(self):
        for name in ("load_bars_by_date", "build_roll_intervals"):
            with self.subTest(function=name):
                self.assertIn("verify_authorized_job_dir", self._calls(name))

    def test_bars_go_through_the_gate_first_loader(self):
        """`load_real` runs `assert_real_run_allowed`, the data-role check
        and the per-file manifest hash before decoding. Reading files any
        other way would step around all three."""
        calls = self._calls("load_bars_by_date")
        self.assertIn("load_real", calls)
        for forbidden in ("read_parquet", "read_csv", "from_file", "open"):
            self.assertNotIn(forbidden, calls, forbidden)

    def test_only_files_the_manifest_lists_are_read(self):
        self.assertIn("_manifest_data_files", self._calls("load_bars_by_date"))


class TestTheEventCalendar(unittest.TestCase):
    """The frozen F10 table is a repository file, so this runs for real."""

    def test_the_three_sets_come_from_the_three_flags(self):
        events = pi.build_event_calendar()
        # ~12 CPI and ~12 NFP releases a year over 11.5 years, and 8 scheduled
        # FOMC statements plus the enumerated unscheduled ones.
        self.assertGreater(len(events.cpi_dates), 130)
        self.assertGreater(len(events.nfp_dates), 130)
        self.assertGreater(len(events.fomc_statement_dates), 90)
        self.assertLess(len(events.fomc_statement_dates), 110)

    def test_the_two_fields_with_no_column_are_left_empty(self):
        """`unscheduled_fomc_dates` is IR-13's enumerated list and
        `raw_multi_event_dates` is IR-12's sidecar. Neither is a column in
        the frozen table, and inferring them would put a derived set where
        the source has none."""
        events = pi.build_event_calendar()
        self.assertEqual(frozenset(), events.unscheduled_fomc_dates)
        self.assertEqual(frozenset(), events.raw_multi_event_dates)


class TestTheSessionSchedule(unittest.TestCase):
    """The exchange calendar is not Development data, so this runs for real."""

    def test_a_full_session_closes_at_960_not_the_futures_close(self):
        """The calendar reports 17:00 for the futures session; RTH closes at
        16:00, and a `close_minute` below 960 is what marks a frozen L44
        excluded day."""
        schedule = pi.build_session_schedule("2021-11-29", "2021-12-01")
        self.assertEqual({960}, set(schedule.close_minute.values()))

    def test_a_half_day_keeps_its_early_close(self):
        schedule = pi.build_session_schedule("2021-11-24", "2021-11-27")
        self.assertEqual(780, schedule.close_minute["2021-11-26"])
        self.assertEqual(960, schedule.close_minute["2021-11-24"])

    def test_degraded_dates_are_scheduled_sessions_with_no_bars_at_all(self):
        """Partially missing sessions are excluded by the funnel's missing
        fraction; this covers the case IR-19 needs -- a session that happened
        and about which nothing is held."""
        schedule = pi.build_session_schedule(
            "2021-11-29", "2021-12-01",
            bars_by_date={"2021-11-29": object(), "2021-12-01": object()})
        self.assertEqual(frozenset({"2021-11-30"}),
                         schedule.vendor_degraded_dates)

    def test_no_bars_argument_means_no_degraded_claim(self):
        """Absence of the argument must not be read as 'nothing is
        degraded' about days nobody looked at."""
        schedule = pi.build_session_schedule("2021-11-29", "2021-12-01")
        self.assertEqual(frozenset(), schedule.vendor_degraded_dates)


if __name__ == "__main__":
    unittest.main()
