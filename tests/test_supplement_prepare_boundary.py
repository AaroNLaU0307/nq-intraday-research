"""N09's prepare carries the real-data gate and NOT the MC-run gate.

AARON'S RULING, 2026-09-05. The day-strata supplement reading the sealed S0
bundle to assemble structural facts does not require the real MC to have been
authorized -- the MC is DOWNSTREAM of this supplement (N09 -> N10 -> N11 ->
N13), so routing N09 through `prepare_real_mc_input` inverted the approved
order and closed a cycle: the supplement waited on an MC that waits on the
supplement's own sealed output.

WHAT THIS GUARD IS FOR, and it is the risky half. Removing a gate is exactly
the shape of change that quietly removes MORE than it was authorised to. So
this asserts BOTH directions: the supplement path dropped `authorize_real_mc`,
and the real-MC path still has it and still refuses. A future edit that
"simplifies" the two entries into one would fail here rather than silently
opening the MC.

REACHABILITY, not a line count. A gate can be re-added or lost through a
helper, so the call sets are closed over the module's own functions; asserting
only on the entry body would miss a gate moved one hop away.

NO BYTES ARE READ HERE. `assert_real_run_allowed` PASSES today (both real-data
attestations exist since 2026-08-25), so CALLING the supplement entry would
open the sealed run on every suite run. Structural on purpose.
"""

import ast
import unittest
from pathlib import Path

from itsf.mc import real_input

MODULE = Path(real_input.__file__)
RUNNER = MODULE.parent / "supplement_runner.py"

REAL_DATA_GATE = "assert_real_run_allowed"
MC_RUN_GATE = "authorize_real_mc"


def _functions(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {n.name: n for n in ast.walk(tree)
            if isinstance(n, ast.FunctionDef)}


def _direct_calls(node):
    return {getattr(n.func, "attr", None) or getattr(n.func, "id", None)
            for n in ast.walk(node) if isinstance(n, ast.Call)}


def _reachable_calls(path, entry):
    """Every name called by `entry`, following calls into the module's own
    functions. A gate hidden one hop down still counts as present."""
    defs = _functions(path)
    seen, pending, found = set(), [entry], set()
    while pending:
        name = pending.pop()
        if name in seen or name not in defs:
            continue
        seen.add(name)
        for called in _direct_calls(defs[name]):
            found.add(called)
            pending.append(called)
    return found


class TestTheSupplementPath(unittest.TestCase):

    def test_it_keeps_the_real_data_gate(self):
        """It opens the sealed S0 run, which is real bytes. The ruling kept
        this gate explicitly."""
        self.assertIn(REAL_DATA_GATE,
                      _reachable_calls(MODULE, "prepare_supplement_mc_input"))

    def test_it_does_not_carry_the_mc_run_gate(self):
        self.assertNotIn(MC_RUN_GATE,
                         _reachable_calls(MODULE,
                                          "prepare_supplement_mc_input"))

    def test_the_runner_uses_it_and_not_the_mc_entry(self):
        """The miswiring this replaces was in the runner, not in the gate."""
        source = RUNNER.read_text(encoding="utf-8")
        called = _direct_calls(ast.parse(source))
        self.assertIn("prepare_supplement_mc_input", called)
        self.assertNotIn("prepare_real_mc_input", called)


class TestTheMcGateWasNotWeakened(unittest.TestCase):
    """Requirement 4 of the ruling: the real MC's own authorization is
    untouched."""

    def test_the_real_entry_still_carries_the_mc_run_gate(self):
        self.assertIn(MC_RUN_GATE,
                      _reachable_calls(MODULE, "prepare_real_mc_input"))

    def test_the_real_entry_still_refuses_naming_its_blocker(self):
        """WIDENED AT THE PRE-CERT REPAIR (R3), and the property is unchanged.

        A real run started outside the trusted launch boundary is now blocked
        BEFORE authorization is consulted, so a bare call meets the launch
        refusal first. That refusal names its own blocker, which is correct for
        its layer -- but the property this test owns is about the MC
        authorization layer, so the launch fact is attested for the duration of
        the call and the assertion is made where it belongs. Accepting whatever
        message arrived first would have quietly deleted the check."""
        import unittest.mock as mock

        from itsf import execution_identity as ei
        attested = ei.LaunchAttestation("/injected", 0, "injected", True)
        with mock.patch.object(ei, "launch_attestation",
                               lambda: attested):
            with self.assertRaises(Exception) as caught:
                real_input.prepare_real_mc_input()
        self.assertNotIsInstance(caught.exception, AssertionError)
        self.assertIn("MC_RUN_AUTHORIZED", str(caught.exception))

    def test_the_real_entry_ALSO_refuses_outside_the_trusted_launch(self):
        """The new outer refusal, asserted rather than merely worked around."""
        from itsf.guards import RunBlockedError
        with self.assertRaises(RunBlockedError) as caught:
            real_input.prepare_real_mc_input()
        self.assertIn("trusted launch boundary", str(caught.exception))

    def test_no_mc_run_authorized_row_was_minted_to_dodge_the_problem(self):
        """Requirement 5. The refusal above must be the registry's, not a
        stub that happens to raise."""
        from itsf.mc.registry_boundary import read_snapshot
        self.assertNotIn("MC_RUN_AUTHORIZED", read_snapshot().text)


class TestTheAssemblyWasFactoredNotCopied(unittest.TestCase):

    def test_there_is_exactly_one_prepare_call_in_the_module(self):
        """Two entries, one assembly. A copy would let the paths drift --
        and drift is how the gated one loses its gate unnoticed."""
        source = MODULE.read_text(encoding="utf-8")
        self.assertEqual(1, source.count("mcc.prepare_mc_input("))

    def test_both_entries_reach_that_one_assembly(self):
        for entry in ("prepare_real_mc_input", "prepare_supplement_mc_input"):
            with self.subTest(entry=entry):
                self.assertIn("prepare_mc_input",
                              _reachable_calls(MODULE, entry))


if __name__ == "__main__":
    unittest.main()
