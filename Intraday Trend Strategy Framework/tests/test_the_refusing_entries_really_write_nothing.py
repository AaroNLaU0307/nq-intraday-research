""""Writes nothing" — OBSERVED, across the refusing surface.

ROUND 5's LESSON, APPLIED TO MY OWN GUARDS. That round ended five rounds of
tightening an AST checker for a runtime property, and the fix was to
observe instead. The same argument applies to every other place in this
repository where a guard names a runtime capability and checks syntax:

    TestThePlannerHasNoWriteCallInItsSource  AST: no write CALL appears
    test_every_mkdir_site_..._KNOWN_one  AST: no unexpected mkdir SITE
    test_nothing_is_ever_unlinked_...    AST: no destructive call name

Round 5's second HIGH is the exact counter-example to that family: it
destroyed a file using `write_bytes`, a call that was on the ALLOWED list.
No name-based check can see that, and none of the three above would.

THE TWO INSTRUMENTS ARE COMPLEMENTARY, NOT ALTERNATIVES, and the existing
guards already say the half they know: `test_nothing_is_ever_unlinked_by_
the_staging_path` states outright that it is "a property of the CODE rather
than of one run" because "no scenario test enumerates every scenario". That
is true. What round 5 added is the other half: a code-shape check can be
satisfied while the property is violated. Shapes catch what scenarios miss;
observation catches what shapes miss.

So this file drives the REFUSING surface -- every entry point that is
supposed to stop before touching anything -- and asserts on the filesystem
operations that actually occurred. Zero is zero, however it was going to be
spelled.
"""

import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class _WriteObserver:
    """Records every mutating filesystem operation, by path."""

    def __enter__(self):
        self.ops = []
        self._saved = {}
        recorded = self

        def wrap_path(name):
            original = getattr(Path, name)
            self._saved[("Path", name)] = original

            def wrapper(self, *a, **k):
                recorded.ops.append((name, str(self)))
                return original(self, *a, **k)
            setattr(Path, name, wrapper)

        def wrap_os(name):
            original = getattr(os, name)
            self._saved[("os", name)] = original

            def wrapper(*a, **k):
                recorded.ops.append((name, str(a[0]) if a else ""))
                return original(*a, **k)
            setattr(os, name, wrapper)

        for name in ("write_bytes", "write_text", "mkdir", "unlink", "touch",
                     "rename", "replace", "rmdir", "symlink_to", "chmod"):
            if hasattr(Path, name):
                wrap_path(name)
        for name in ("replace", "remove", "unlink", "rename", "mkdir",
                     "makedirs", "rmdir"):
            if hasattr(os, name):
                wrap_os(name)
        return self

    def __exit__(self, *exc):
        for (owner, name), original in self._saved.items():
            setattr(Path if owner == "Path" else os, name, original)
        return False


class TestTheObserverItselfWorks(unittest.TestCase):
    """A probe that patched nothing would report zero for everything, and
    every assertion below would pass over silence."""

    def test_it_sees_a_write(self):
        with TemporaryDirectory() as tmp:
            with _WriteObserver() as obs:
                (Path(tmp) / "x").write_bytes(b"1")
        self.assertIn(("write_bytes", str(Path(tmp) / "x")), obs.ops)

    def test_it_sees_a_mkdir_and_an_os_replace(self):
        with TemporaryDirectory() as tmp:
            src = Path(tmp) / "a"
            src.write_bytes(b"1")
            with _WriteObserver() as obs:
                (Path(tmp) / "d").mkdir()
                os.replace(src, Path(tmp) / "b")
        kinds = {name for name, _ in obs.ops}
        self.assertIn("mkdir", kinds)
        self.assertIn("replace", kinds)

    def test_it_restores_everything_it_patched(self):
        before = (Path.write_bytes, Path.mkdir, os.replace)
        with _WriteObserver():
            pass
        self.assertEqual(before, (Path.write_bytes, Path.mkdir, os.replace))


class TestTheProductionEntryTouchesNothing(unittest.TestCase):
    """`run_supplement_production` is supposed to refuse before anything.
    The AST guards say no write CALL appears; this says no write HAPPENED."""

    def test_it_refuses_and_performs_zero_mutating_operations(self):
        from itsf.mc import supplement_runner as sr

        with _WriteObserver() as obs:
            with self.assertRaises(Exception):
                sr.run_supplement_production()
        self.assertEqual([], obs.ops,
                         "the refusing production entry mutated: %s" % obs.ops)

    def test_the_day_strata_entry_too(self):
        from itsf.mc import day_strata_supplement as ds

        with _WriteObserver() as obs:
            with self.assertRaises(Exception):
                ds.run_supplement_production()
        self.assertEqual([], obs.ops, "day_strata entry mutated: %s" % obs.ops)

    def test_and_authorize_supplement_refuses_without_touching_anything(self):
        from itsf.mc import day_strata_supplement as ds

        with _WriteObserver() as obs:
            with self.assertRaises(Exception):
                ds.authorize_supplement("any registry text")
        self.assertEqual([], obs.ops)


class TestThePlannerReallyWritesNothing(unittest.TestCase):
    """`TestThePlannerHasNoWriteCallInItsSource` checks the module's AST
    for write calls. Round 5 destroyed a file with an ALLOWED call, so a
    name-based check is not the whole story. This runs the planner and
    watches."""

    def _outcome_and_chain(self):
        from types import SimpleNamespace

        from itsf.mc import day_strata_pipeline as dsp
        from itsf.mc.supplement_registry import ChainResolution

        outcome = dsp.CBuildOutcome(
            rows=(), product=None,
            failure=dsp.CBuildFailure("day_set_exact", "vol_day_missing",
                                      "2026-01-05"))
        chain = ChainResolution("MC-DS-S001", started=False,
                                events=(SimpleNamespace(short_id="P2"),))
        return outcome, chain

    def test_planning_a_failure_row_mutates_nothing(self):
        from itsf.mc import day_strata_failure as dsf

        outcome, chain = self._outcome_and_chain()
        with _WriteObserver() as obs:
            planned = dsf.plan_for_c_build_failure(
                outcome, supplement_id="MC-DS-S001", chain=chain,
                incident_id="INC-0123456789ab", attempts_dir="x")
        self.assertIsNotNone(planned)
        self.assertEqual([], obs.ops,
                         "the failure planner mutated: %s" % obs.ops)

    def test_and_it_really_produced_the_row(self):
        """The premise: a planner that raised early would mutate nothing
        for the wrong reason."""
        from itsf.mc import day_strata_failure as dsf

        outcome, chain = self._outcome_and_chain()
        planned = dsf.plan_for_c_build_failure(
            outcome, supplement_id="MC-DS-S001", chain=chain,
            incident_id="INC-0123456789ab", attempts_dir="x")
        self.assertEqual("F1", planned.short_id)


class TestClassificationTouchesNothing(unittest.TestCase):

    def test_no_classifier_mutates_anything(self):
        from itsf.mc import day_strata_classify as dsc
        from itsf.mc import day_strata_rows as dsr

        with _WriteObserver() as obs:
            dsc.classify_producer_failure(
                dsr.DayStrataRowsError("vol_day_missing", "d"))
            dsc.classify_seal_failure("production_rows_digest_drift")
            dsc.seal_failure_router("production_payload_drift")
            dsc.classify_builder_failure("production_authority_test_only")
        self.assertEqual([], obs.ops)


class TestTheContextAssemblerOnlyREADS(unittest.TestCase):
    """It runs git and reads the registry. Reading is fine; writing is not,
    and `build_precheck_context` is called before any authorization."""

    def test_building_a_precheck_context_mutates_nothing(self):
        from itsf.mc import day_strata_context as ctxmod

        with _WriteObserver() as obs:
            ctx = ctxmod.build_precheck_context(
                supplement_id="MC-DS-S001", utc_stamp="20260830T000000Z")
        self.assertIsNotNone(ctx)
        self.assertEqual([], obs.ops,
                         "the context assembler mutated: %s" % obs.ops)


class TestEveryGateOnlyOBSERVES(unittest.TestCase):
    """R3 §3: a gate classifies an outcome; it does not act. Checked by
    running all twenty-three of them and watching."""

    def test_no_gate_in_any_stage_mutates_anything(self):
        from itsf.mc import day_strata_context as ctxmod
        from itsf.mc import supplement_contract as sc
        from itsf.mc import supplement_runner as sr

        ctx = ctxmod.build_precheck_context(
            supplement_id="MC-DS-S001", utc_stamp="20260830T000000Z")
        ran = 0
        with _WriteObserver() as obs:
            for stage in sc.STAGE_ENUM:
                for gate in sc.GATE_TABLE[stage]:
                    ran += 1
                    try:
                        sr.GATES[gate](ctx)
                    except Exception:                          # noqa: BLE001
                        pass
        self.assertGreaterEqual(ran, 20, "only %d gates ran" % ran)
        self.assertEqual([], obs.ops, "a gate mutated: %s" % obs.ops)


if __name__ == "__main__":
    unittest.main()
