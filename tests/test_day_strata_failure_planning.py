"""The last link: a C_BUILD refusal becomes a described registry row.

THE LOAD-BEARING TEST IN THIS FILE is not that F1 and F2 are routed
correctly -- the runner already decided that. It is
`TestThePoisonedChainRefusesRatherThanReadingFalse`. F1's payload contains
the literal `consumption_statement="nothing consumed"`, and a poisoned
resolution hands back `started=False` as a dataclass DEFAULT rather than as
an observation. So the way to write a false statement into the registry is
not to make a mistake: it is to trust that default. The refusal is what
stands between those two.

NOTHING HERE APPENDS, and `TestThePlannerCannotWrite` measures that rather
than trusting the docstring.
"""

import ast
import io
import unittest
from pathlib import Path
from types import SimpleNamespace

from itsf.mc import day_strata_failure as dsf
from itsf.mc import day_strata_pipeline as dsp
from itsf.mc import supplement_contract as sc
from itsf.mc.supplement_registry import ChainResolution

def runner_path():
    return (Path(__file__).resolve().parents[1] / "src" / "itsf" / "mc"
            / "supplement_runner.py")


MODULE = (Path(__file__).resolve().parents[1]
          / "src" / "itsf" / "mc" / "day_strata_failure.py")
SID = "MC-DS-S001"
INC = "INC-0123456789ab"   # sc.INCIDENT_RE: 12 hex digits


def _chain(*, started=False, shorts=(), problem=""):
    return ChainResolution(SID, problem=problem, started=started,
                           events=tuple(SimpleNamespace(short_id=s)
                                        for s in shorts))


def _failed(gate="day_set_exact", code="vol_day_missing", detail="2026-01-05"):
    return dsp.CBuildOutcome(rows=(), product=None,
                             failure=dsp.CBuildFailure(gate, code, detail))


class TestThePoisonedChainRefusesRatherThanReadingFalse(unittest.TestCase):
    """The whole reason this module exists."""

    def test_a_problem_chain_refuses(self):
        with self.assertRaises(dsf.FailurePlanError) as caught:
            dsf.p3_boundary(_chain(problem="MC resolution refused"))
        message = str(caught.exception)
        self.assertIn("dataclass default rather than an observation", message)
        self.assertIn("nothing consumed", message)

    def test_and_so_does_the_planner_that_would_have_used_it(self):
        """The refusal has to survive the layer above it. A guard that only
        fires when called directly guards nothing."""
        with self.assertRaises(dsf.FailurePlanError):
            dsf.plan_for_c_build_failure(
                _failed(), supplement_id=SID,
                chain=_chain(problem="poisoned"), incident_id=INC,
                attempts_dir="x")

    def test_the_false_direction_is_the_dangerous_one_and_it_is_stated(self):
        """The asymmetry is the argument. If someone later 'simplifies'
        this to a default, the reason it was not a default should still be
        readable in the source."""
        text = io.open(MODULE, encoding="utf-8").read()
        self.assertIn("Unknown is not not-started.", text)

    def test_an_absent_chain_is_also_unknown(self):
        with self.assertRaises(dsf.FailurePlanError) as caught:
            dsf.p3_boundary(None)
        self.assertIn("It is not False", str(caught.exception))


class TestTheTwoDerivationsMustAgree(unittest.TestCase):
    """`started` is set inside a 100-line loop with early returns. The
    events are the second witness. If they ever disagree, neither can
    choose between F1 and F2, so neither is used."""

    def test_started_without_a_p3_row_refuses(self):
        with self.assertRaises(dsf.FailurePlanError) as caught:
            dsf.p3_boundary(_chain(started=True, shorts=("P2",)))
        self.assertIn("do not carry", str(caught.exception))

    def test_a_p3_row_without_started_refuses(self):
        with self.assertRaises(dsf.FailurePlanError) as caught:
            dsf.p3_boundary(_chain(started=False, shorts=("P2", "P3")))
        self.assertIn("carry the P3 row", str(caught.exception))

    def test_agreement_in_both_directions_is_accepted(self):
        self.assertFalse(dsf.p3_boundary(_chain(shorts=("P2",))))
        self.assertTrue(dsf.p3_boundary(
            _chain(started=True, shorts=("P2", "P3"))))

    def test_an_empty_chain_is_a_real_pre_start_answer(self):
        """A supplement id absent from a fully resolved registry genuinely
        has no P3 row. That is an observation, not an unknown -- the
        difference from a poisoned chain, which has `problem` set."""
        self.assertFalse(dsf.p3_boundary(_chain()))


class TestTheBoundaryChoosesTheRow(unittest.TestCase):

    def test_pre_start_plans_an_f1_that_names_what_it_did_not_consume(self):
        planned = dsf.plan_for_c_build_failure(
            _failed(), supplement_id=SID, chain=_chain(shorts=("P2",)),
            incident_id=INC, attempts_dir="runs/attempts")
        self.assertEqual("F1", planned.short_id)
        self.assertEqual("nothing consumed",
                         planned.fields["consumption_statement"])
        self.assertEqual("day_set_exact", planned.fields["gate_name"])
        self.assertEqual("C_BUILD", planned.fields["stage"])

    def test_post_start_plans_an_f2_that_preserves_its_residue(self):
        planned = dsf.plan_for_c_build_failure(
            _failed(), supplement_id=SID,
            chain=_chain(started=True, shorts=("P2", "P3")),
            incident_id=INC, residue_path="runs/residue")
        self.assertEqual("F2", planned.short_id)
        self.assertEqual("YES", planned.fields["residue_preserved"])

    def test_the_runner_still_enforces_its_own_requirements(self):
        """F2 without a residue path must fail in the RUNNER, not be
        papered over here. This module supplies the boundary; it does not
        re-implement what the boundary implies."""
        from itsf.mc.supplement_runner import SupplementRunnerError
        with self.assertRaises(SupplementRunnerError):
            dsf.plan_for_c_build_failure(
                _failed(), supplement_id=SID,
                chain=_chain(started=True, shorts=("P2", "P3")),
                incident_id=INC)


class TestErrorClassIsTheExceptionNameNotTheCode(unittest.TestCase):
    """Measured against every existing `_fail` site rather than chosen."""

    def test_the_planned_row_carries_the_class_name(self):
        planned = dsf.plan_for_c_build_failure(
            _failed(), supplement_id=SID, chain=_chain(shorts=("P2",)),
            incident_id=INC, attempts_dir="a")
        self.assertEqual("DayStrataRowsError", planned.fields["error_class"])

    def test_the_code_is_not_lost_it_moves_to_the_detail(self):
        planned = dsf.plan_for_c_build_failure(
            _failed(code="trade_date_malformed"), supplement_id=SID,
            chain=_chain(shorts=("P2",)), incident_id=INC,
            attempts_dir="a")
        self.assertNotIn("trade_date_malformed",
                         planned.fields["error_class"])

    def test_every_runner_fail_site_names_a_REAL_exception_class(self):
        """The premise, and a correction to my own first draft.

        I asserted the convention was "the value ends in Error". Running it
        measured that false at once: `SupplementRunNotAuthorized` is a real
        `_fail` error_class and ends in nothing of the kind. The convention
        is not a spelling rule -- it is that the value NAMES A CLASS THAT
        EXISTS. That is also the only version worth enforcing: a spelling
        rule would accept `FooError` for a class nobody ever wrote."""
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
            except Exception:                              # noqa: BLE001
                continue
            for name in dir(module):
                obj = getattr(module, name)
                if isinstance(obj, type) and issubclass(obj, BaseException):
                    known.add(name)
        self.assertGreater(len(known), 40,
                           "the exception sweep found %d classes, too few "
                           "to be the real namespace" % len(known))

        tree = ast.parse(io.open(runner_path(), encoding="utf-8").read())
        seen = 0
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call)
                    and getattr(node.func, "id", "") == "_fail"
                    and len(node.args) >= 3
                    and isinstance(node.args[2], ast.Constant)):
                seen += 1
                with self.subTest(error_class=node.args[2].value):
                    self.assertIn(node.args[2].value, known)
        self.assertGreater(seen, 15,
                           "found %d _fail sites, too few to establish the "
                           "convention" % seen)


class TestASuccessCannotBecomeAFailureRow(unittest.TestCase):

    def test_a_succeeding_outcome_refuses(self):
        good = dsp.CBuildOutcome(rows=({"trade_date": "2026-01-05"},),
                                 product=object(), failure=None)
        with self.assertRaises(dsf.FailurePlanError) as caught:
            dsf.plan_for_c_build_failure(
                good, supplement_id=SID, chain=_chain(shorts=("P2",)),
                incident_id=INC, attempts_dir="a")
        self.assertIn("worse than no row", str(caught.exception))

    def test_a_failure_with_no_gate_refuses(self):
        blank = dsp.CBuildOutcome(
            rows=(), product=None,
            failure=dsp.CBuildFailure("", "some_code", "detail"))
        with self.assertRaises(dsf.FailurePlanError) as caught:
            dsf.plan_for_c_build_failure(
                blank, supplement_id=SID, chain=_chain(shorts=("P2",)),
                incident_id=INC, attempts_dir="a")
        self.assertIn("half of what an F1 row carries",
                      str(caught.exception))


class TestThePlannerCannotWrite(unittest.TestCase):
    """Measured, not asserted in prose. The eight authorization fields are
    NO; a module that described rows AND could append them would be one
    edit away from appending one."""

    FORBIDDEN = ("open", "write_text", "write_bytes", "mkdir", "unlink",
                 "rename", "replace", "touch", "remove", "rmtree",
                 "append_event", "append_row")

    def test_no_write_call_appears_anywhere_in_the_module(self):
        tree = ast.parse(io.open(MODULE, encoding="utf-8").read())
        offenders = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = (getattr(node.func, "attr", None)
                    or getattr(node.func, "id", None))
            if name in self.FORBIDDEN:
                offenders.append("line %d: %s" % (node.lineno, name))
        self.assertEqual([], offenders,
                         "the planner can write: %s" % offenders)

    def test_it_imports_no_filesystem_module(self):
        tree = ast.parse(io.open(MODULE, encoding="utf-8").read())
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        for banned in ("os", "shutil", "pathlib", "io", "tempfile"):
            with self.subTest(module=banned):
                self.assertNotIn(banned, imported)

    def test_the_scan_is_looking_at_the_right_file(self):
        """A vacuity guard: a path typo would make both checks above pass
        over nothing."""
        text = io.open(MODULE, encoding="utf-8").read()
        self.assertIn("def plan_for_c_build_failure", text)
        self.assertIn("def p3_boundary", text)


class TestTheGateNamesReachTheRealTable(unittest.TestCase):

    def test_every_gate_a_producer_failure_can_carry_is_a_c_build_gate(self):
        from itsf.mc import day_strata_classify as dsc
        for gate in sorted(set(dsc.GATE_OF_PRODUCER_CODE.values())):
            with self.subTest(gate=gate):
                planned = dsf.plan_for_c_build_failure(
                    _failed(gate=gate), supplement_id=SID,
                    chain=_chain(shorts=("P2",)), incident_id=INC,
                    attempts_dir="a")
                self.assertIn(planned.fields["gate_name"],
                              sc.GATE_TABLE["C_BUILD"])


if __name__ == "__main__":
    unittest.main()
