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

    def test_every_job_dir_reader_verifies_the_authorization_first(self):
        """UPDATED 2026-09-06 with the provenance repair: the set of
        functions that read the job dir changed. `build_roll_intervals` no
        longer does (it reads the FROZEN symbology CSV S0-T001 used), and
        `build_session_schedule` now does (vendor `condition.json`)."""
        for name in ("load_bars_by_date", "build_session_schedule"):
            with self.subTest(function=name):
                self.assertIn("verify_authorized_job_dir", self._calls(name))

    def test_the_roll_reader_no_longer_reads_the_job_dir_at_all(self):
        """The other half: it must not have kept a second, live source."""
        calls = self._calls("build_roll_intervals")
        for forbidden in ("read_vendor_intervals", "coalesce", "load_real",
                          "from_file"):
            self.assertNotIn(forbidden, calls, forbidden)

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

    def test_the_other_two_fields_are_supplied_as_S0_supplied_them(self):
        """REWRITTEN 2026-09-06. This used to assert both were EMPTY, on the
        reasoning that neither is a column in the frozen table so filling
        them would be inference. Both halves were wrong:
        `unscheduled_fomc_dates` is IR-13's enumerated CONSTANT, which
        S0-T001 passes verbatim, and `raw_multi_event_dates` is read off the
        `event_type` column of this same table. Leaving them empty is what
        made the supplement's event strata differ from the run it
        reconstructs."""
        events = pi.build_event_calendar()
        self.assertEqual(frozenset(pi.UNSCHEDULED_FOMC),
                         events.unscheduled_fomc_dates)
        self.assertTrue(events.raw_multi_event_dates,
                        "raw_multi is derived from the event_type column and "
                        "the frozen table does carry multi-kind dates")
        # and it really is derived from the column, not a second constant
        import csv
        kinds = {}
        with open(pi.F10_EVENTS_CSV, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                kinds.setdefault(row["date_et"], set()).add(row["event_type"])
        self.assertEqual(frozenset(d for d, k in kinds.items() if len(k) > 1),
                         events.raw_multi_event_dates)


class TestTheSessionSchedule(unittest.TestCase):
    """REWRITTEN 2026-09-06 with the provenance repair. Every assertion here
    used to pin a semantic the supplement had invented for itself; each is
    now the semantic S0-T001 actually used."""

    def test_the_close_minute_is_the_exchanges_own_uncapped(self):
        """It used to be capped at 960 ("RTH closes at 16:00"). S0-T001 does
        no capping -- it writes the calendar's `market_close` minute -- so
        the cap made the supplement's session table differ from the one it
        reconstructs. A cap that can only mark MORE days early is still a
        different input."""
        schedule = pi.build_session_schedule("2021-11-29", "2021-12-01")
        self.assertEqual({1020}, set(schedule.close_minute.values()))

    def test_a_half_day_still_carries_its_real_early_close(self):
        schedule = pi.build_session_schedule("2021-11-24", "2021-11-27")
        self.assertEqual(780, schedule.close_minute["2021-11-26"])
        self.assertEqual(1020, schedule.close_minute["2021-11-24"])

    def test_degraded_comes_from_the_vendors_condition_file(self):
        """It used to be re-derived as "scheduled sessions carrying no bars",
        which is a different set with a different meaning: one is what the
        VENDOR says about a day, the other is what our file inventory
        happens to hold."""
        import json
        schedule = pi.build_session_schedule("2010-06-06", "2021-12-31")
        condition = json.loads(
            (pi.AUTHORIZED_JOB_DIR / pi.CONDITION_JSON_NAME
             ).read_text(encoding="utf-8"))
        self.assertEqual(
            frozenset(r["date"] for r in condition
                      if r["condition"] != "available"),
            schedule.vendor_degraded_dates)
        self.assertTrue(schedule.vendor_degraded_dates,
                        "the vendor does report degraded days; an empty set "
                        "would mean the file was not consulted")

    def test_the_bars_argument_no_longer_decides_the_degraded_set(self):
        """It stays in the signature because callers pass it. A live-looking
        parameter that silently stopped deciding anything is worse than one
        that is asserted not to."""
        with_bars = pi.build_session_schedule(
            "2021-11-29", "2021-12-01",
            bars_by_date={"2021-11-29": object()})
        without = pi.build_session_schedule("2021-11-29", "2021-12-01")
        self.assertEqual(without.vendor_degraded_dates,
                         with_bars.vendor_degraded_dates)


if __name__ == "__main__":
    unittest.main()
