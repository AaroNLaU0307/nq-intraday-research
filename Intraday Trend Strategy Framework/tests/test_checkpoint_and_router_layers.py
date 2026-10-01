"""N09 R3 §2–§3 — the two layers that sit on top of the approved enums.

WHY THEY ARE LAYERS AND NOT EDITS. `GATE_TABLE` is an approved closed enum.
Both problems below are about how gates are DISPATCHED and how their
refusals are ROUTED, not about which gates exist — so they are separate
mappings over the same names. Editing the enum would be an R4-level act.

CHECKPOINT_OF closes R2's HOLD. R2 asserted one zero-side-effect rule across
all five C_BUILD gates. That is false by construction for two of them:
staging writes `.partial` before it can verify it, and by the archive gate
the archive attempt has already happened. Three moments, three different
invariants.

ROUTER_OF closes a defect measured while transcribing CR1:
`archive_policy_a` is a GATE, so its refusal routes through
`plan_failure_event` to F2 — while ratified `ND1_ARCHIVE_FAILURE_POLICY=A`
requires A1. `test_routing_it_as_an_ordinary_gate_contradicts_policy_a` in
the R3-facts file executes that contradiction; this file is the layer that
resolves it.

SCOPE. Structure only. Nothing here derives a row, seals, archives, or
appends anything — the buildable scope is still the restrictive reading of
the ruling's closing line, and the wide/narrow question is out for decision.
"""

import unittest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from itsf.mc import supplement_contract as sc


class TestTheApprovedEnumIsUntouched(unittest.TestCase):
    """The property that makes these layers legitimate at all."""

    def test_gate_table_still_holds_exactly_its_ratified_members(self):
        self.assertEqual(13, len(sc.GATE_TABLE["A_PRECHECK"]))
        self.assertEqual(5, len(sc.GATE_TABLE["B_DERIVE"]))
        self.assertEqual(5, len(sc.GATE_TABLE["C_BUILD"]))

    def test_the_layers_add_no_gate_and_remove_none(self):
        declared = {g for stage in sc.STAGE_ENUM for g in sc.GATE_TABLE[stage]}
        self.assertTrue(set(sc.CHECKPOINT_OF) <= declared,
                        "CHECKPOINT_OF names a gate the enum does not")
        self.assertTrue(set(sc.ROUTER_OF) <= declared,
                        "ROUTER_OF names a gate the enum does not")


class TestCheckpointDispatch(unittest.TestCase):

    def test_the_three_moments_partition_c_build_exactly(self):
        """A partition, not a covering: every C_BUILD gate has exactly one
        moment, and no moment is empty."""
        by_moment = {}
        for gate in sc.GATE_TABLE["C_BUILD"]:
            by_moment.setdefault(sc.checkpoint_of(gate), []).append(gate)
        self.assertEqual(
            {sc.CHECKPOINT_C_BUILD_1: ["row_schema_blind", "day_set_exact",
                                       "rows_digest_recompute"],
             sc.CHECKPOINT_C_BUILD_2: ["seal_staging_partial"],
             sc.CHECKPOINT_C_BUILD_3: ["archive_policy_a"]},
            {k: sorted(v, key=sc.GATE_TABLE["C_BUILD"].index)
             for k, v in by_moment.items()})

    def test_asking_a_non_c_build_gate_refuses(self):
        """Checkpoints partition C_BUILD only. Returning None for the other
        eighteen gates would read as 'no checkpoint needed' rather than
        'the question does not apply'."""
        for gate in ("g9_hard_blocker", "source_bundle_digest", "git_clean"):
            with self.assertRaises(sc.SupplementGrammarError):
                sc.checkpoint_of(gate)


class TestRouting(unittest.TestCase):

    def test_the_archive_gate_routes_to_the_post_seal_router(self):
        """THE defect this layer exists for. Ratified policy A: a local seal
        that succeeded while the archive failed becomes A1, never F2."""
        self.assertEqual(sc.ROUTER_POST_SEAL,
                         sc.router_of("archive_policy_a"))

    def test_every_other_gate_routes_to_the_failure_router(self):
        declared = [g for stage in sc.STAGE_ENUM for g in sc.GATE_TABLE[stage]]
        others = [g for g in declared if g != "archive_policy_a"]
        self.assertEqual(22, len(others))
        for gate in others:
            self.assertEqual(sc.ROUTER_GATE_FAILURE, sc.router_of(gate), gate)

    def test_an_undeclared_gate_refuses_rather_than_defaulting_to_a(self):
        """A typo that defaulted to router A would send an archive failure
        to F2 silently — the exact defect, reintroduced through a spelling
        mistake."""
        for bad in ("archive_policy", "Archive_Policy_A", "", "no_such_gate"):
            with self.assertRaises(sc.SupplementGrammarError,
                                   msg=f"{bad!r} was routed"):
                sc.router_of(bad)

    def test_router_b_is_used_by_exactly_one_gate(self):
        """If a second gate ever needs router B, that is a design change
        worth noticing rather than absorbing."""
        declared = [g for stage in sc.STAGE_ENUM for g in sc.GATE_TABLE[stage]]
        on_b = [g for g in declared
                if sc.router_of(g) == sc.ROUTER_POST_SEAL]
        self.assertEqual(["archive_policy_a"], on_b)


#: THE SINGLE SOURCE. Two tests need this set: the one that forbids these
#: names in the execution path, and the one that proves they are real symbols
#: (without which the first is vacuous). Spelling it twice let a typo in the
#: forbidding copy pass BOTH — measured, not supposed.
HERMETIC_CORE_SYMBOLS = ("build_day_strata_supplement_test_only",
                         "seal_supplement_test_only",
                         "build_supplement_from_authority",
                         "supplement_production")


class TestTheLayersDoNotExecuteAnything(unittest.TestCase):
    """Scope, asserted rather than promised."""

    def test_the_c_build_gates_all_still_refuse(self):
        from itsf.mc import supplement_runner as sr
        ctx = sr.GateContext(supplement_id="MC-DS-S001", head_commit="0" * 40,
                             registry_text="", runs_root=None,
                             archive_root=None)
        for gate in sc.GATE_TABLE["C_BUILD"]:
            with self.assertRaises(sr.SupplementRunnerError, msg=gate):
                sr.GATES[gate](ctx)

    def test_the_forbidden_names_are_real_symbols(self):
        """THE PREMISE THE GUARD BELOW CANNOT PROVE ABOUT ITSELF.

        It asserts four names are absent from `supplement_runner`. A typo in
        any one of them makes that name absent from the whole repository, so
        the assertion passes and the condition it enforces is silently
        unenforced. Pinning them as real symbols is what makes the absence
        mean something."""
        import ast
        from pathlib import Path
        src = Path(__file__).resolve().parents[1] / "src" / "itsf" / "mc"
        defined = {"supplement_production"}      # the module itself
        for path in src.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                     ast.ClassDef)):
                    defined.add(node.name)
        self.assertGreater(len(defined), 40,
                           f"the symbol scan reached {len(defined)} names; "
                           "at that count 'all four exist' proves nothing")
        missing = sorted(set(HERMETIC_CORE_SYMBOLS) - defined)
        self.assertEqual([], missing,
                         "the guard below forbids names that do not exist; "
                         "its absence assertion is vacuous for: "
                         + ", ".join(missing))

    def test_the_execution_path_does_not_reach_the_hermetic_core(self):
        """RULING 1 CONDITIONS 1 of dec-scope-boundary-2026-08-27.

        NARROW means the C_BUILD execution path may not derive rows or
        seal. The capability EXISTS —
        `supplement_production.build_supplement_from_authority` calls
        `build_day_strata_supplement_test_only` and is documented as the
        only production path from a sealed S0 input to a sealed supplement
        — it is simply not wired to anything. Measured: nothing outside
        that module calls it, and `supplement_runner` neither imports nor
        calls it.

        Same shape as `registry_witness.py`: written, correct, unwired,
        and unwired ON PURPOSE. What the condition adds is that wiring it
        must now go red rather than pass quietly.
        """
        import ast
        from pathlib import Path
        forbidden = set(HERMETIC_CORE_SYMBOLS)
        runner = (Path(__file__).resolve().parents[1] / "src" / "itsf" /
                  "mc" / "supplement_runner.py")
        tree = ast.parse(runner.read_text(encoding="utf-8"))
        docstrings = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                                 ast.AsyncFunctionDef)):
                doc = ast.get_docstring(node, clean=False)
                if doc is not None:
                    docstrings.add(doc)
        reached = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.split(".")[-1] in forbidden:
                    reached.append(f"import from {node.module} @L{node.lineno}")
                for alias in node.names:
                    if alias.name in forbidden:
                        reached.append(f"import {alias.name} @L{node.lineno}")
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[-1] in forbidden:
                        reached.append(f"import {alias.name} @L{node.lineno}")
            if isinstance(node, ast.Call):
                name = getattr(node.func, "id", None) or getattr(
                    node.func, "attr", None)
                if name in forbidden:
                    reached.append(f"call {name} @L{node.lineno}")
        self.assertEqual([], reached,
                         "the C_BUILD execution path now reaches row "
                         "production or sealing; ruling 1 is NARROW and "
                         "wiring these needs a NEW authorization, not a "
                         "reading of an existing sentence:\n  "
                         + "\n  ".join(reached))

    def test_the_layers_are_pure_lookups(self):
        """No I/O, no state: the same question twice gives the same answer,
        and neither call can have touched anything."""
        for gate in sc.GATE_TABLE["C_BUILD"]:
            self.assertEqual(sc.checkpoint_of(gate), sc.checkpoint_of(gate))
            self.assertEqual(sc.router_of(gate), sc.router_of(gate))


if __name__ == "__main__":
    unittest.main()
