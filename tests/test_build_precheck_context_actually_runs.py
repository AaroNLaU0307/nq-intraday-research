"""`build_precheck_context` had an AST guard and no execution.

FOUND BY MEASUREMENT, and it was mine. A scan for public `mc/` functions
with no caller outside their own module returned thirteen names. Twelve
were false alarms -- called from inside their own module, which the scan
excluded by construction, and reached by tests through their module's other
entry points. One was real:

    build_precheck_context   referenced twice in the whole repository --
                             once in a test DOCSTRING, once in its own
                             `__all__`. Nothing ever called it.

Written the same night as `test_registry_boundary`'s live assertion that
every production `GateContext` takes `registry_text` and `chain` from ONE
`resolve_for_supplement` call. That assertion reads the SHAPE of the source.
It would pass just as happily if the function raised on every input.

Same shape as the defect this project keeps producing: the guard is
narrower than the property it is quoted for. So this file RUNS the thing.

WHY RUNNING IT IS SAFE. It reads `ops/TRIAL_REGISTRY.md` (the event truth
source, not quarantined), asks git for HEAD and porcelain status, and calls
`verify_frozen_hashes`. It writes nothing, creates no directory, appends no
row, and touches no Development data.
"""

import unittest
from pathlib import Path

from itsf.mc import day_strata_context as ctxmod
from itsf.mc import registry_boundary as rb
from itsf.mc.supplement_runner import GateContext

SID = "MC-DS-S001"
STAMP = "20260829T000000Z"


class TestItRunsAtAll(unittest.TestCase):
    """The gap this file exists to close."""

    @classmethod
    def setUpClass(cls):
        cls.ctx = ctxmod.build_precheck_context(
            supplement_id=SID, utc_stamp=STAMP)

    def test_it_returns_a_gate_context(self):
        self.assertIsInstance(self.ctx, GateContext)

    def test_the_head_it_reports_is_a_real_40_hex_commit(self):
        self.assertRegex(self.ctx.head_commit, r"\A[0-9a-f]{40}\Z")

    def test_the_roots_are_the_RULED_ones_not_invented(self):
        from itsf import contracts
        self.assertEqual(Path(contracts.RULED_RUNS_ROOT), self.ctx.runs_root)
        self.assertEqual(Path(contracts.RULED_ARCHIVE_ROOT),
                         self.ctx.archive_root)

    def test_frozen_hashes_ok_is_an_ANSWER_not_None(self):
        """The try/except must produce a verdict either way. `None` would
        mean the check never ran, and `assert_complete` exempts this field
        from the None test -- so a silent None here would travel."""
        self.assertIsInstance(self.ctx.frozen_hashes_ok, bool)

    def test_and_the_FAILING_branch_answers_False_not_None(self):
        """The half the line above cannot reach, and a measured hole in my
        own first draft.

        Mutating `frozen_ok = False` to `frozen_ok = None` left the test
        above GREEN: the frozen files on this machine are intact, so
        `verify_frozen_hashes` succeeds and the except branch never runs.
        The assertion was real and the branch it was quoted for was
        untouched by it.

        A tampered frozen file is exactly when this field matters -- it is
        what `_g_frozen_hashes` refuses on -- so the failing branch is
        forced here rather than waited for."""
        from itsf import guards

        real = guards.verify_frozen_hashes

        def boom():
            raise guards.FrozenTamperError("forced for this test")

        guards.verify_frozen_hashes = boom
        try:
            ctx = ctxmod.build_precheck_context(supplement_id=SID,
                                                utc_stamp=STAMP)
        finally:
            guards.verify_frozen_hashes = real
        self.assertIs(False, ctx.frozen_hashes_ok,
                      "a failed frozen-hash check must be recorded as "
                      "False; None would mean 'never ran' and travels "
                      "through assert_complete's exemption unnoticed")

    def test_the_forced_failure_probe_really_bites(self):
        """The probe's own check: if the patch did not take, the test above
        would be asserting against the untampered success path."""
        from itsf import guards

        real = guards.verify_frozen_hashes
        guards.verify_frozen_hashes = lambda: (_ for _ in ()).throw(
            RuntimeError("probe"))
        try:
            with self.assertRaises(RuntimeError):
                guards.verify_frozen_hashes()
        finally:
            guards.verify_frozen_hashes = real
        guards.verify_frozen_hashes()      # restored, and still passing

    def test_dirty_paths_is_a_tuple_and_empty_means_clean(self):
        self.assertIsInstance(self.ctx.repo_dirty_paths, tuple)
        for entry in self.ctx.repo_dirty_paths:
            with self.subTest(entry=entry):
                self.assertIsInstance(entry, str)
                self.assertNotEqual("", entry.strip())


class TestItSuppliesWhatTheGatesActuallyRead(unittest.TestCase):
    """The integration claim, which neither function could make alone.

    `required_fields` derives what A_PRECHECK's gates read from the
    runner's AST; `build_precheck_context` assembles a context. Nothing
    tied the two together -- so the assembler could have been missing a
    field the whole time and both halves would still have passed."""

    def test_a_built_context_is_COMPLETE_for_a_precheck(self):
        ctx = ctxmod.build_precheck_context(supplement_id=SID,
                                            utc_stamp=STAMP)
        ctxmod.assert_complete(ctx, "A_PRECHECK")

    def test_and_it_is_deliberately_INCOMPLETE_for_b_derive(self):
        """The documented boundary, pinned. `authority` and `prepared` come
        from real Development input behind `assert_real_run_allowed`; an
        assembler that reached for them would be a second real-data read in
        a module that gate does not guard."""
        ctx = ctxmod.build_precheck_context(supplement_id=SID,
                                            utc_stamp=STAMP)
        self.assertIsNone(ctx.authority)
        self.assertIsNone(ctx.prepared)
        with self.assertRaises(ctxmod.ContextError) as caught:
            ctxmod.assert_complete(ctx, "B_DERIVE")
        message = str(caught.exception)
        self.assertIn("authority", message)
        self.assertIn("prepared", message)


class TestTheSingleReadIsBEHAVIOURALLyTrue(unittest.TestCase):
    """`test_registry_boundary` proves this by reading the source. Source
    shape is not behaviour: a function can look right and call something
    else at runtime. This counts the calls."""

    def test_the_boundary_is_consulted_exactly_once(self):
        calls = []
        real = rb.resolve_for_supplement

        def counting(*args, **kwargs):
            calls.append(args[0] if args else kwargs.get("supplement_id"))
            return real(*args, **kwargs)

        rb.resolve_for_supplement = counting
        try:
            ctx = ctxmod.build_precheck_context(supplement_id=SID,
                                                utc_stamp=STAMP)
        finally:
            rb.resolve_for_supplement = real
        self.assertEqual([SID], calls,
                         "the assembler consulted the registry boundary %d "
                         "times; two reads of one mutable file can disagree, "
                         "and then the chain a gate refuses on is not the "
                         "registry the run recorded" % len(calls))
        self.assertIsNotNone(ctx.chain)

    def test_the_counter_would_actually_have_noticed(self):
        """The probe's own check. If the patch did not take, the test above
        would report one call no matter what the function did."""
        calls = []
        real = rb.resolve_for_supplement

        def counting(*args, **kwargs):
            calls.append(1)
            return real(*args, **kwargs)

        rb.resolve_for_supplement = counting
        try:
            rb.resolve_for_supplement(SID)
            rb.resolve_for_supplement(SID)
        finally:
            rb.resolve_for_supplement = real
        self.assertEqual(2, len(calls))


class TestItInventsNoAuthorization(unittest.TestCase):
    """An id with no chain must come back with no chain -- not with a
    fabricated empty one that later reads as 'resolved, nothing wrong'."""

    def test_an_unknown_supplement_id_still_builds_but_grants_nothing(self):
        ctx = ctxmod.build_precheck_context(
            supplement_id="MC-DS-S999", utc_stamp=STAMP)
        self.assertIsNotNone(ctx.chain)
        self.assertEqual((), tuple(ctx.chain.live_authorizations))
        self.assertFalse(ctx.chain.started)


class TestGitFailureRefusesRatherThanGuessing(unittest.TestCase):

    def test_a_root_that_is_not_a_repository_refuses(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ctxmod.ContextError) as caught:
                ctxmod.build_precheck_context(
                    supplement_id=SID, utc_stamp=STAMP, repo_root=tmp)
            self.assertIn("git", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
