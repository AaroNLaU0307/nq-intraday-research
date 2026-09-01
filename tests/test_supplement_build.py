"""`supplement_build` assembles, and the five C_BUILD gates are not alike.

THE CLAIM, same as the other two stages: this module RECEIVES a
`CBuildOutcome` and never produces one. Proved by source, by signature and by
behaviour rather than asserted in a docstring.

THE FINDING THIS FILE IS BUILT TO MEASURE. Three of the five gates classify
an attached outcome; the other two refuse unconditionally and never read it.
That is stated in the runner's comments, and a comment is a claim -- five
review rounds in this repository turned on a comment that was true when
written and false when read. So it is MEASURED here with a tripwire outcome
that raises on any attribute access: a gate that touches it cannot stay
silent, and a gate that refuses while holding it provably never looked.

THE FIXTURE IS REUSED, NOT REBUILT. `test_day_strata_pipeline._run` already
produces a genuine outcome through the real pipeline with the two universe
builders mocked. A second copy here would be a hand-written mirror of someone
else's setup, which is the shape that keeps going stale.
"""

import ast
import hashlib
import inspect
import unittest
from pathlib import Path

from itsf import contracts as _c
from itsf.mc import supplement_build as sb
from itsf.mc import supplement_contract as sc
from itsf.mc import supplement_precheck as pc
from itsf.mc import supplement_runner as sr

import test_day_strata_pipeline as fx

GOVERNED = (Path(_c.RULED_RUNS_ROOT), Path(_c.RULED_ARCHIVE_ROOT))
MODULE = Path(sb.__file__)

#: The runner's own split, named here so a change to the contract's table
#: shows up as a failure rather than as a quietly different measurement.
#: It DID: `seal_staging_partial` moved from the right column to the left on
#: 2026-09-01 when `run_c_build_2` gave it an outcome to classify, and these
#: tests went red rather than quietly measuring something else. That is the
#: whole reason the split is pinned here instead of inferred at run time.
CLASSIFIERS = ("row_schema_blind", "day_set_exact", "rows_digest_recompute",
               "seal_staging_partial")
UNCONDITIONAL = ("archive_policy_a",)


def _blobs():
    out = []
    for root in GOVERNED:
        if root.exists():
            for path in sorted(root.rglob("*")):
                if path.is_file():
                    out.append((str(path),
                                hashlib.sha256(path.read_bytes()).hexdigest()))
    return sorted(out)


def _ctx():
    ctx, gaps = pc.assemble_precheck_context()
    assert gaps == (), gaps
    return ctx


class _Tripwire:
    """Raises on ANY attribute read. Attached as an outcome, it separates a
    gate that classifies from a gate that refuses without looking."""

    def __getattr__(self, name):
        raise AssertionError("the gate read .%s off the outcome" % name)


class TestItNeverProducesTheOutcome(unittest.TestCase):

    def test_the_source_carries_no_call_to_any_producer(self):
        tree = ast.parse(MODULE.read_text(encoding="utf-8"))
        called = {getattr(n.func, "attr", None) or getattr(n.func, "id", None)
                  for n in ast.walk(tree) if isinstance(n, ast.Call)}
        for forbidden in ("run_c_build", "build_supplement_from_authority",
                          "derive_day_strata_rows", "prepare_real_mc_input"):
            self.assertNotIn(
                forbidden, called,
                "%s calls %s; this module is supposed to RECEIVE an outcome, "
                "never make one" % (MODULE.name, forbidden))

    def test_outcome_is_a_required_parameter_of_both_public_functions(self):
        """A default would let a caller omit it, leaving the module to supply
        one -- the exact thing it must not do, while the docstring saying so
        would still read as true."""
        for fn in (sb.assemble_build_context, sb.run_build_gates):
            params = inspect.signature(fn).parameters
            self.assertIn("outcome", params, fn.__name__)
            self.assertIs(params["outcome"].default, inspect.Parameter.empty,
                          "%s gives `outcome` a default" % fn.__name__)

    def test_running_it_changes_no_governed_byte(self):
        before = _blobs()
        sb.run_build_gates(_ctx(), fx._run())
        self.assertEqual(before, _blobs())


class TestAbsenceIsARefusal(unittest.TestCase):

    def test_with_no_outcome_every_gate_refuses(self):
        """A pass here would put 'no defect found' on record about a build
        that never ran."""
        report = sb.run_build_gates(_ctx(), None)
        refusing = [n for n, d in report.results if d is not None]
        self.assertEqual(list(sc.GATE_TABLE["C_BUILD"]), refusing)
        self.assertFalse(report.passed)
        self.assertFalse(report.outcome_attached)

    def test_every_classifier_says_it_classified_nothing(self):
        report = sb.run_build_gates(_ctx(), None)
        detail = dict(report.results)
        for name in CLASSIFIERS:
            self.assertIn("classified nothing", detail[name], name)


class TestTheFiveAreNotAlike(unittest.TestCase):
    """The measurement, not a reading of the comments."""

    def test_the_unconditional_gate_never_reads_the_outcome(self):
        ctx = sb.assemble_build_context(_ctx(), _Tripwire())
        for name in UNCONDITIONAL:
            with self.assertRaises(sr.SupplementRunnerError) as caught:
                sr.GATES[name](ctx)
            self.assertIn("unreachable in this build", str(caught.exception))

    def test_the_three_classifiers_do_read_the_outcome(self):
        """The other half of the same measurement: if this passed too, the
        tripwire would be proving nothing about anybody."""
        ctx = sb.assemble_build_context(_ctx(), _Tripwire())
        for name in CLASSIFIERS:
            with self.assertRaises(AssertionError) as caught:
                sr.GATES[name](ctx)
            self.assertIn("read .belongs_to", str(caught.exception))

    def test_a_clean_outcome_passes_four_and_cannot_pass_the_last(self):
        report = sb.run_build_gates(_ctx(), fx._run())
        detail = dict(report.results)
        for name in CLASSIFIERS:
            self.assertIsNone(detail[name], "%s: %s" % (name, detail[name]))
        for name in UNCONDITIONAL:
            self.assertIsNotNone(detail[name], name)
            self.assertIn("unreachable in this build", detail[name])
        self.assertFalse(report.passed)
        self.assertEqual("", report.producer_failure)


class TestTheReportCoversEveryGate(unittest.TestCase):

    def test_it_reports_all_five_in_the_contracts_order(self):
        report = sb.run_build_gates(_ctx(), fx._run())
        self.assertEqual(list(sc.GATE_TABLE["C_BUILD"]),
                         [n for n, _d in report.results])

    def test_a_producer_refusal_is_carried_into_the_report(self):
        """A failing outcome must arrive as a refusal REPORT rather than as
        an exception escaping the reporter."""
        outcome = fx._run(days=fx.DAYS[:-1])
        report = sb.run_build_gates(_ctx(), outcome)
        self.assertEqual(len(sc.GATE_TABLE["C_BUILD"]), len(report.results))
        self.assertFalse(report.passed)
        # NOT `if outcome.failure is not None` -- a conditional assertion is
        # indistinguishable from one that never fires, which is the shape
        # this repository keeps meeting. Measured: this input refuses with
        # `vol_day_invented` at `day_set_exact`, so require it.
        self.assertIsNotNone(outcome.failure, "the fixture stopped failing")
        self.assertEqual("day_set_exact", outcome.failure.gate)
        self.assertIn(outcome.failure.code, report.producer_failure)
        self.assertEqual("day_set_exact", report.first_refusal[0])


def test_how_far_C_BUILD_gets(capsys):
    """THE MEASUREMENT this module was built to make -- printed so the number
    in any report comes from a run rather than from me."""
    report = sb.run_build_gates(_ctx(), fx._run())
    with capsys.disabled():
        print("\n  C_BUILD against a clean synthetic outcome:")
        for name, detail in report.results:
            print("    %-24s %s" % (name, "PASS" if detail is None
                                    else "REFUSE " + detail[:78]))
    assert len(report.results) == 5


if __name__ == "__main__":
    unittest.main()
