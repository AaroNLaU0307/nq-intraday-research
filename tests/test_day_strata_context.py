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


class TestCBuildNowREADSTheContextAndThatIsTheTripwireFiring(unittest.TestCase):
    """THE LIVE FORM. This class used to assert C_BUILD read NOTHING from
    the context, and said so in its own words:

        "The assertion below goes RED the moment the gates are wired --
         which is exactly when someone should look at whether the assembler
         supplies what they started reading."

    2026-08-30: fresh Sol returned the C_BUILD_2 wording review, the freeze
    on `supplement_runner.py` lifted, the parked wiring patch landed, and
    the three C_BUILD_1 gates became real classifiers. This is that look."""

    def test_the_three_C_BUILD_1_gates_now_read_the_outcome(self):
        need = ctxmod.required_fields("C_BUILD")
        self.assertIn("c_build_outcome", need,
                      "the wired gates read nothing from the context, so "
                      "either the patch did not land or they were wired to "
                      "reach around it")

    def test_the_completeness_check_is_no_longer_vacuous(self):
        """It used to pass over an empty requirement set. It now refuses a
        context with no outcome attached -- which is the whole point of
        `_classify_c_build_1`'s "absence is a refusal, never a pass"."""
        with self.assertRaises(ctxmod.ContextError) as caught:
            ctxmod.assert_complete(_bare(), "C_BUILD")
        self.assertIn("c_build_outcome", str(caught.exception))

    def test_a_context_carrying_an_outcome_is_complete_for_C_BUILD(self):
        from itsf.mc.day_strata_pipeline import CBuildOutcome

        full = _bare(c_build_outcome=CBuildOutcome((), None, None))
        ctxmod.assert_complete(full, "C_BUILD")

    def test_the_two_gates_deliberately_left_as_stubs_still_are(self):
        """`seal_staging_partial` (its wording is what Sol just HELD on) and
        `archive_policy_a` (Router B owns its outcome) were excluded from
        the patch ON PURPOSE, each for a stated reason. If either quietly
        becomes a classifier, the reason went with it."""
        import inspect

        from itsf.mc import supplement_runner as sr
        for gate in ("seal_staging_partial", "archive_policy_a"):
            with self.subTest(gate=gate):
                source = inspect.getsource(getattr(sr, "_g_" + gate))
                self.assertIn("unreachable in this build", source)

    def test_and_the_three_wired_ones_are_NOT_stubs_any_more(self):
        """The other direction, so this class cannot pass by everything
        being a stub again."""
        import inspect

        from itsf.mc import supplement_runner as sr
        for gate in ("row_schema_blind", "day_set_exact",
                     "rows_digest_recompute"):
            with self.subTest(gate=gate):
                source = inspect.getsource(getattr(sr, "_g_" + gate))
                self.assertNotIn("unreachable in this build", source)
                self.assertIn("_classify_c_build_1", source)


if __name__ == "__main__":
    unittest.main()
