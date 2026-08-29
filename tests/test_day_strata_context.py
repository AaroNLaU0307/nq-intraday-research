"""The context assembler: a derived requirement map, and a refusal.

WHAT WAS MISSING. `GateContext` existed, the gates existed, and nothing in
`src/` ever built one — only tests did, seven times. Same gap shape as the
row producer: every piece present, no production path between them.

WHY REFUSING MATTERS. Every optional field defaults to `None`, and a gate
handed `None` does not fail loudly — it evaluates whatever `None` makes its
condition do and reports a verdict about nothing. The assembler refuses a
context a stage cannot evaluate rather than letting five gates discover it
one at a time and the first one to notice name the defect.

THE MAP IS DERIVED. `required_fields` reads the runner's AST. A hand-
written mirror of another module goes stale the first time that module
changes; this project produced five instances of exactly that in one day.
"""

import unittest

from itsf.mc import day_strata_context as ctxmod
from itsf.mc import supplement_contract as sc
from itsf.mc.supplement_runner import GateContext


def _bare(**overrides):
    fields = dict(supplement_id="MC-DS-S001", head_commit="a" * 40,
                  registry_text="", runs_root=None, archive_root=None)
    fields.update(overrides)
    return GateContext(**fields)


class TestTheRequirementMapIsDerived(unittest.TestCase):

    def test_a_precheck_needs_what_its_gates_actually_read(self):
        need = ctxmod.required_fields("A_PRECHECK")
        for field in ("chain", "g9_flag", "second_copy_flag", "runs_root",
                      "archive_root", "utc_stamp", "repo_dirty_paths"):
            with self.subTest(field=field):
                self.assertIn(field, need)

    def test_b_derive_needs_the_authority_and_its_prepared_input(self):
        """N06's repair: the authority alone proves nothing — every fact it
        carries has to be re-derivable from the SAME prepared input."""
        need = ctxmod.required_fields("B_DERIVE")
        self.assertIn("authority", need)
        self.assertIn("prepared", need)

    def test_an_unknown_stage_refuses(self):
        with self.assertRaises(ctxmod.ContextError):
            ctxmod.required_fields("NOT_A_STAGE")

    def test_a_gate_the_runner_does_not_define_refuses(self):
        """The derivation's own vacuity guard. If the gate table named a
        function that does not exist, the walk would find nothing for it
        and silently under-report what the stage needs."""
        original = dict(sc.GATE_TABLE)
        patched = dict(original)
        patched["A_PRECHECK"] = tuple(original["A_PRECHECK"]) + ("ghost_gate",)
        sc.GATE_TABLE = patched
        try:
            with self.assertRaises(ctxmod.ContextError) as caught:
                ctxmod.required_fields("A_PRECHECK")
            self.assertIn("ghost_gate", str(caught.exception))
        finally:
            sc.GATE_TABLE = original


class TestAnIncompleteContextIsRefused(unittest.TestCase):

    def test_a_bare_context_cannot_answer_a_precheck(self):
        with self.assertRaises(ctxmod.ContextError) as caught:
            ctxmod.assert_complete(_bare(), "A_PRECHECK")
        message = str(caught.exception)
        self.assertIn("chain", message)
        self.assertIn("runs_root", message)

    def test_b_derive_names_the_authority_and_prepared(self):
        with self.assertRaises(ctxmod.ContextError) as caught:
            ctxmod.assert_complete(_bare(), "B_DERIVE")
        self.assertIn("authority", str(caught.exception))
        self.assertIn("prepared", str(caught.exception))

    def test_a_clean_repository_is_not_a_missing_field(self):
        """`repo_dirty_paths=()` means CLEAN — the value the gate most
        wants to see. Treating empty as "not supplied" would make a clean
        repository look like an assembly failure."""
        need = ctxmod.required_fields("A_PRECHECK")
        self.assertIn("repo_dirty_paths", need)
        full = _bare(runs_root="x", archive_root="y", chain=object(),
                     g9_flag="g", second_copy_flag="s", frozen_hashes_ok=False,
                     utc_stamp="20260829T000000Z", repo_dirty_paths=())
        ctxmod.assert_complete(full, "A_PRECHECK")

    def test_a_field_the_context_does_not_HAVE_is_named_differently(self):
        """The drift case, and the last uncovered branch in this module.

        `required_fields` is derived from what the gates read; the context
        is a dataclass with a fixed field set. If a gate starts reading
        `ctx.something_new` and nobody adds it, the two disagree — and
        "the context has no such field" is a different defect from "the
        field is there and empty". The first is a code mismatch, the second
        is an assembly failure, and an operator needs different actions."""

        class _Missing:
            """Everything A_PRECHECK needs except `chain`, which it does
            not merely leave None — it does not define at all."""

            def __init__(self):
                for name in ctxmod.required_fields("A_PRECHECK"):
                    if name != "chain":
                        setattr(self, name, "supplied")

        with self.assertRaises(ctxmod.ContextError) as caught:
            ctxmod.assert_complete(_Missing(), "A_PRECHECK")
        message = str(caught.exception)
        self.assertIn("chain (no such field)", message)
        self.assertNotIn("chain,", message)

    def test_frozen_hashes_false_is_an_answer_not_an_absence(self):
        """`False` means the check RAN and failed — a gate must see that,
        not be told the field is missing."""
        self.assertIn("frozen_hashes_ok", ctxmod._FALSY_IS_VALID)

    def test_a_falsy_but_PRESENT_value_is_present(self):
        """The `is None` choice, tested directly.

        My first pass tested this with `repo_dirty_paths=()` — which is in
        `_FALSY_IS_VALID`, so a mutation from `is None` to `not value` was
        INVISIBLE: the exemption absorbed it either way. The principle was
        stated in a comment and held by nothing.

        `chain` is not exempt, so a falsy-but-present chain separates the
        two readings. A resolved chain that happens to be falsy is still a
        resolved chain, and a gate must be given it rather than told the
        context is incomplete."""

        class _FalsyChain:
            def __bool__(self):
                return False

        full = _bare(runs_root="x", archive_root="y", chain=_FalsyChain(),
                     g9_flag="g", second_copy_flag="s", frozen_hashes_ok=True,
                     utc_stamp="20260829T000000Z", repo_dirty_paths=())
        ctxmod.assert_complete(full, "A_PRECHECK")


class TestCBuildHasNoRequirementsYetAndThatIsATripwire(unittest.TestCase):
    """C_BUILD's gates are still default-refuse stubs, so they read nothing
    from the context and `assert_complete(ctx, "C_BUILD")` passes over an
    empty set.

    That is the vacuous shape, stated rather than left to be discovered. The
    assertion below goes RED the moment the gates are wired — which is
    exactly when someone should look at whether the assembler supplies what
    they started reading."""

    def test_c_build_reads_nothing_from_the_context_today(self):
        self.assertEqual(frozenset(), ctxmod.required_fields("C_BUILD"),
                         "a C_BUILD gate now reads the context. Wire the "
                         "assembler to supply those fields, then update "
                         "this test to assert the new requirement instead "
                         "of the empty set.")

    def test_so_the_completeness_check_is_vacuous_for_it(self):
        ctxmod.assert_complete(_bare(), "C_BUILD")

    def test_and_the_gates_are_still_stubs(self):
        """The premise for the two above. If a gate stopped being a stub
        without starting to read the context, this file would still pass
        while describing something untrue."""
        import inspect

        from itsf.mc import supplement_runner as sr
        for gate in sc.GATE_TABLE["C_BUILD"]:
            with self.subTest(gate=gate):
                source = inspect.getsource(getattr(sr, "_g_" + gate))
                self.assertIn("unreachable in this build", source)


if __name__ == "__main__":
    unittest.main()
