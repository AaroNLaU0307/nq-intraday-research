"""The rehearsal, and the two doors that keep it a rehearsal.

WHAT IT ALREADY EARNED. The first end-to-end walk found a real defect in
code written the same night: `run_c_build` classified EVERY builder
exception as `row_schema_blind`, on a comment saying "the builder validates
the rows it was handed". It also validates the AUTHORITY, so a
`production_authority_test_only` refusal was being filed as a row-schema
defect at the wrong stage -- a wrong gate name and a wrong stage, which are
exactly the two things an F1/F2 row carries.

Every part had passing tests. The joint did not, because nothing had ever
walked the joint. That is the argument for a rehearsal in one sentence.
"""

import datetime as dt
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tests"))

import test_mc_supplement_authority as A       # noqa: E402
import test_mc_supplement_registry as T        # noqa: E402
from itsf import contracts                     # noqa: E402
from itsf.mc import day_strata_dryrun as dry    # noqa: E402
from itsf.mc import supplement_authority as sa  # noqa: E402

TARGET = list(A.ALL_DAYS)
FLAGS = {"2026-08-03": "CPI", "2026-08-04": "none", "2026-08-05": "FOMC",
         "2026-08-06": "none", "2026-08-07": "NFP"}


def synthetic_universe(target=TARGET, n_history=40):
    """A made-up day universe. No Development bars are read: the closes are
    invented, which is the whole point -- a rehearsal must be safe to point
    at anything, and real bars are neither safe nor available here."""
    day = dt.date.fromisoformat(target[0])
    history = []
    while len(history) < n_history:
        day -= dt.timedelta(days=1)
        if day.weekday() < 5:
            history.append(day.isoformat())
    days = sorted(history) + list(target)

    class _Summary:
        def __init__(self, close):
            self.official_close = close

    class _Funnel:
        observed_rth = days
        structurally_eligible = days

    class _Universe:
        funnel = _Funnel()
        summaries = {d: _Summary(20000.0 + (i * 7 % 53) * 3.5)
                     for i, d in enumerate(days)}
        roll_transition_dates = ()

    return _Universe()


def _authority():
    prepared = A._prepare_for_tests(A._bundle())
    return sa.derive_supplement_authority_for_tests(prepared), prepared


def _rehearse(scratch, *, flags=None, prepared=None, authority=None):
    methods = contracts.aaron_ruled_methods()
    auth, prep = _authority()
    auth = authority if authority is not None else auth
    prep = prepared if prepared is not None else prep
    T.ROOT = str(Path(scratch) / "runs")
    reg = T.Reg()
    reg.commit[T.SID] = A.COMMIT
    reg.add("P1", sid=T.SID)
    reg.add("P2", sid=T.SID)
    return dry.rehearse(
        authority=auth, prepared=prep, universe=synthetic_universe(),
        vol_method=methods.volatility_regime,
        flag_by_date=FLAGS if flags is None else flags,
        event_na_mapping=methods.event_na_mapping,
        expected_day_set=auth.expected_day_set,
        registry_text=reg.text(), head_commit=A.COMMIT,
        utc_stamp="20260829T000000Z", scratch_root=scratch)


class TestTheTwoDoors(unittest.TestCase):
    """A rehearsal that could carry real data, or write under a governed
    root, would not be a rehearsal."""

    def test_a_non_test_only_prepared_input_is_refused(self):
        class _Real:
            test_only = False

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(dry.DryRunRefused) as caught:
                dry.rehearse(
                    authority=None, prepared=_Real(), universe=None,
                    vol_method=None, flag_by_date={}, event_na_mapping="",
                    expected_day_set=frozenset(), registry_text="",
                    head_commit="a" * 40, utc_stamp="20260829T000000Z",
                    scratch_root=tmp)
        self.assertIn("test_only=True", str(caught.exception))
        self.assertIn("degree of freedom", str(caught.exception))

    def test_a_missing_test_only_attribute_is_refused_too(self):
        """`is not True` rather than falsiness: an object with no such
        attribute must not read as 'not test data'."""
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(dry.DryRunRefused):
                dry.rehearse(
                    authority=None, prepared=object(), universe=None,
                    vol_method=None, flag_by_date={}, event_na_mapping="",
                    expected_day_set=frozenset(), registry_text="",
                    head_commit="a" * 40, utc_stamp="20260829T000000Z",
                    scratch_root=tmp)

    def test_a_scratch_root_inside_a_governed_root_is_refused(self):
        _, prepared = _authority()
        governed = dry._GOVERNED[0] / "supplements" / "would-be-scratch"
        with self.assertRaises(dry.DryRunRefused) as caught:
            dry.rehearse(
                authority=None, prepared=prepared, universe=None,
                vol_method=None, flag_by_date={}, event_na_mapping="",
                expected_day_set=frozenset(), registry_text="",
                head_commit="a" * 40, utc_stamp="20260829T000000Z",
                scratch_root=governed)
        self.assertIn("governed root", str(caught.exception))

    def test_the_refusal_happens_BEFORE_any_directory_is_laid(self):
        """Order matters: refusing after creating the scratch would leave
        the thing it refused to make."""
        _, prepared = _authority()
        target = dry._GOVERNED[0] / "supplements" / "never-created"
        with self.assertRaises(dry.DryRunRefused):
            dry.rehearse(
                authority=None, prepared=prepared, universe=None,
                vol_method=None, flag_by_date={}, event_na_mapping="",
                expected_day_set=frozenset(), registry_text="",
                head_commit="a" * 40, utc_stamp="20260829T000000Z",
                scratch_root=target)
        self.assertFalse(target.exists())


class TestTheWalkItself(unittest.TestCase):

    def test_A_PRECHECK_passes_and_B_DERIVE_refuses_on_the_partition(self):
        """The shape of every rehearsal, and it is correct rather than a
        limitation: `custody_authority_production` refuses a test_only
        authority, which is the same partition that makes this safe."""
        with tempfile.TemporaryDirectory() as tmp:
            report = _rehearse(tmp)
        self.assertTrue(report.stage("A_PRECHECK").all_passed,
                        report.stage("A_PRECHECK").refused)
        self.assertEqual(("custody_authority_production",),
                         report.stage("B_DERIVE").refused)
        self.assertFalse(report.reached_c_build)

    def test_the_C_BUILD_mechanism_still_runs_and_is_classified(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = _rehearse(tmp)
        self.assertIsNotNone(report.outcome)
        self.assertIsNotNone(report.outcome.failure)
        self.assertEqual("B_DERIVE", report.outcome.failure.stage)
        self.assertEqual("production_authority_test_only",
                         report.outcome.failure.code)

    def test_it_plans_the_row_that_WOULD_be_recorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = _rehearse(tmp)
        planned = report.planned_event
        self.assertIsNotNone(planned)
        self.assertEqual("F1", planned.short_id)
        self.assertEqual("B_DERIVE", planned.fields["stage"])
        self.assertEqual("nothing consumed",
                         planned.fields["consumption_statement"])

    def test_the_planned_row_names_the_class_it_ACTUALLY_came_from(self):
        """THE SECOND CORRECTION the rehearsal forced, one layer up.

        The planner spelled `DayStrataRowsError` for every failure, so a
        `SupplementProductionError` was being recorded as a producer error.
        Same defect as the wrong gate name -- a false statement in the
        registry -- just in a different field."""
        with tempfile.TemporaryDirectory() as tmp:
            report = _rehearse(tmp)
        self.assertEqual("SupplementProductionError",
                         report.planned_event.fields["error_class"])
        self.assertEqual("SupplementProductionError",
                         report.outcome.failure.error_class)

    def test_a_producer_refusal_still_names_the_producer(self):
        """The other direction. A fix that made every class name wrong in a
        new way would pass the test above."""
        with tempfile.TemporaryDirectory() as tmp:
            report = _rehearse(tmp, flags={})
        self.assertEqual("DayStrataRowsError",
                         report.outcome.failure.error_class)
        self.assertEqual("DayStrataRowsError",
                         report.planned_event.fields["error_class"])

    def test_every_class_name_it_can_emit_is_a_real_class(self):
        """The convention `test_day_strata_failure_planning` established:
        the value must NAME A CLASS THAT EXISTS, not merely look like one."""
        import builtins
        import importlib
        import pkgutil

        import itsf

        known = {n for n in dir(builtins)
                 if isinstance(getattr(builtins, n), type)
                 and issubclass(getattr(builtins, n), BaseException)}
        for info in pkgutil.walk_packages(itsf.__path__, "itsf."):
            try:
                module = importlib.import_module(info.name)
            except Exception:                                 # noqa: BLE001
                continue
            for name in dir(module):
                obj = getattr(module, name)
                if isinstance(obj, type) and issubclass(obj, BaseException):
                    known.add(name)
        for flags in ({}, FLAGS):
            with tempfile.TemporaryDirectory() as tmp:
                report = _rehearse(tmp, flags=flags)
            with self.subTest(flags=bool(flags)):
                self.assertIn(report.outcome.failure.error_class, known)

    def test_a_missing_event_flag_is_caught_by_the_producer_first(self):
        """A different failure reached through the same walk, so the report
        is not pinned to one path."""
        with tempfile.TemporaryDirectory() as tmp:
            report = _rehearse(tmp, flags={})
        self.assertEqual("day_set_exact", report.outcome.failure.gate)
        self.assertEqual("C_BUILD", report.outcome.failure.stage)
        self.assertEqual("event_day_missing", report.outcome.failure.code)

    def test_the_rendered_report_is_honest_about_what_it_is_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            text = dry.render(_rehearse(tmp))
        self.assertIn("THE GATES DID NOT APPROVE THIS", text)
        self.assertIn("NOT evidence a real run would", text)
        self.assertIn("NOTHING WAS WRITTEN", text)


class TestItVerifiesItsOwnClaim(unittest.TestCase):
    """'Writes nothing' is checked, not promised."""

    def test_the_governed_subtrees_are_unchanged_in_fact(self):
        before = dry._snapshot_governed()
        with tempfile.TemporaryDirectory() as tmp:
            _rehearse(tmp)
        self.assertEqual(before, dry._snapshot_governed())

    def test_a_rehearsal_that_DID_change_one_refuses_at_the_end(self):
        """Mutation-proven without writing under quant-data: the snapshot
        function is made to report a change, and the rehearsal must refuse
        rather than return a report qualified with a warning."""
        real = dry._snapshot_governed
        calls = []

        def shifting():
            calls.append(1)
            return {"pretend": len(calls)}      # different every call

        dry._snapshot_governed = shifting
        try:
            with tempfile.TemporaryDirectory() as tmp:
                with self.assertRaises(dry.DryRunRefused) as caught:
                    _rehearse(tmp)
        finally:
            dry._snapshot_governed = real
        self.assertIn("changed a governed supplements subtree",
                      str(caught.exception))
        self.assertGreaterEqual(len(calls), 2,
                                "the probe was consulted once, so the "
                                "before/after comparison never happened")

    def test_the_real_snapshot_sees_the_real_subtrees(self):
        """The probe above is a stand-in. If the real one looked at
        nothing, the test above it would be proving nothing."""
        snap = dry._snapshot_governed()
        self.assertEqual(2, len(snap))
        for key, value in snap.items():
            with self.subTest(subtree=key):
                self.assertTrue(key.endswith("supplements"))
                self.assertEqual((), value,
                                 "the governed subtree is not empty: %s"
                                 % (value,))


if __name__ == "__main__":
    unittest.main()
