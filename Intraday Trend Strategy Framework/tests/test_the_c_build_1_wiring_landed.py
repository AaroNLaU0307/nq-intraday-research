"""The parked wiring LANDED. This is what that guard became.

WHAT IT USED TO DO. `ops/PREPARED_C_BUILD_1_GATE_WIRING.patch` was finished
work held back because `supplement_runner.py` was pinned to a live review.
This file guarded it against rot and, in its own words, would "announce the
unblock" when the review returned.

2026-08-30 it did exactly that: fresh Sol returned `c-build-2-wording-r3`
(VERDICT=HOLD), the register entry came out, the two tests here went red on
purpose, the patch applied cleanly, and the three C_BUILD_1 gates became
real classifiers.

The `.patch` file is gone -- a patch that no longer applies is a trap for
whoever reads it next, and its content lives in git history and in
`ops/PREPARED_C_BUILD_1_GATE_WIRING.md`.

WHAT IT DOES NOW. The value was never the patch; it was that the wiring is
correct and stays correct. So the checks moved onto the landed code: the
three gates classify, the two deliberately-excluded ones still refuse, and
the reason each was excluded is still true.
"""

import ast
import inspect
import io
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RUNNER = REPO / "src" / "itsf" / "mc" / "supplement_runner.py"
RECORD = REPO / "ops" / "PREPARED_C_BUILD_1_GATE_WIRING.md"

WIRED = ("row_schema_blind", "day_set_exact", "rows_digest_recompute",
         # 2026-09-01. Its old exclusion read "its WORDING is what Sol just
         # HELD on, and nothing on this path is ever sealed" -- and the
         # second half turned out to be about a MISSING CLASSIFIER, not a
         # missing mechanism: `seal_supplement_production` already sealed
         # and staged in full. `run_c_build_2` supplies the outcome, so the
         # exclusion's own reason no longer holds and the gate is wired.
         "seal_staging_partial")
#: Excluded on purpose, and now only one -- for a reason that is a RULING
#: rather than unfinished work, which is why it does not expire the way the
#: other exclusion did.
EXCLUDED = {
    "archive_policy_a":
        "C_BUILD_3. Router B owns its outcome (ROUTER_OF); wiring it as an "
        "ordinary gate re-creates the Policy-A contradiction.",
}


class TestTheWiringLanded(unittest.TestCase):

    def test_every_wired_gate_is_a_classifier_now(self):
        from itsf.mc import supplement_runner as sr
        for gate in WIRED:
            with self.subTest(gate=gate):
                source = inspect.getsource(getattr(sr, "_g_" + gate))
                self.assertIn("_classify_c_build_1", source)
                self.assertNotIn("unreachable in this build", source)

    def test_the_context_carries_what_they_read(self):
        from itsf.mc import day_strata_context as ctxmod
        self.assertIn("c_build_outcome", ctxmod.required_fields("C_BUILD"))

    def test_absence_of_an_outcome_is_still_a_REFUSAL(self):
        """The load-bearing half of the wiring: a gate with nothing to
        classify must refuse, never pass. Passing would record "no defect"
        about a build that never ran."""
        from itsf.mc import supplement_runner as sr
        ctx = sr.GateContext(supplement_id="MC-DS-S001", head_commit="a" * 40,
                             registry_text="", runs_root=None,
                             archive_root=None)
        for gate in WIRED:
            with self.subTest(gate=gate):
                with self.assertRaises(sr.SupplementRunnerError) as caught:
                    sr.GATES[gate](ctx)
                self.assertIn("classified nothing", str(caught.exception))

    def test_the_patch_file_is_retired(self):
        """A patch that no longer applies is worse than no patch: it reads
        as ready work."""
        self.assertFalse((REPO / "ops"
                          / "PREPARED_C_BUILD_1_GATE_WIRING.patch").exists())

    def test_the_record_says_it_landed(self):
        text = RECORD.read_text(encoding="utf-8")
        self.assertIn("STATUS      = APPLIED", text)


class TestTheTwoExclusionsAreStillJustified(unittest.TestCase):
    """Wiring three of five was a choice with a reason per gate. If either
    reason stops being true, the exclusion needs revisiting rather than
    inheriting."""

    def test_the_remaining_excluded_gate_still_refuses_unconditionally(self):
        from itsf.mc import supplement_runner as sr
        for gate in EXCLUDED:
            with self.subTest(gate=gate):
                source = inspect.getsource(getattr(sr, "_g_" + gate))
                self.assertIn("unreachable in this build", source)

    def test_archive_policy_a_is_still_router_Bs(self):
        from itsf.mc import supplement_contract as sc
        self.assertEqual(sc.ROUTER_POST_SEAL,
                         sc.ROUTER_OF.get("archive_policy_a"))

    def test_the_C_BUILD_2_wording_is_still_under_a_HOLD(self):
        """The other exclusion's reason. If a round ever returns PASS, this
        goes red and the exclusion should be re-argued, not assumed."""
        ruling = (REPO / "ops"
                  / "RULING_SOL_C_BUILD_2_R3_HOLD_2026-08-30.md")
        self.assertTrue(ruling.exists())
        text = ruling.read_text(encoding="utf-8")
        self.assertIn("VERDICT=HOLD", text)
        self.assertIn("WORDING_MAY_GO_TO_AARON=NO", text)

    def test_each_exclusion_carries_a_reason_here_too(self):
        for gate, reason in EXCLUDED.items():
            with self.subTest(gate=gate):
                self.assertGreater(len(reason), 40)


class TestTheRunnerIsNoLongerHeldByAnyReview(unittest.TestCase):

    def test_if_it_is_pinned_again_the_wiring_has_not_moved(self):
        """WAS `test_it_is_out_of_the_freeze_register`, and its own failure
        message already knew better than its assertion:

            "the runner is pinned to a review again. That is not a defect
             -- it means a new round is out, and the wiring must not move
             while it is."

        Round 5 went out and pinned it, so the absolute form went red on a
        state it had itself described as correct. The property worth
        holding is the second half of that sentence: while a reviewer holds
        the file, the wiring stays exactly what they were handed."""
        import hashlib
        import json

        register = json.loads((REPO / "ops" / "ARTIFACTS_UNDER_REVIEW.json")
                              .read_text(encoding="utf-8"))
        held = [e for e in register["under_review"]
                if e.get("path") == "src/itsf/mc/supplement_runner.py"]
        if not held:
            return                      # no live round; nothing to hold to
        current = hashlib.sha256(RUNNER.read_bytes()).hexdigest()
        for entry in held:
            with self.subTest(review=entry.get("review_id")):
                self.assertEqual(
                    entry["sha256"], current,
                    "the runner moved while %s holds it -- their recheck "
                    "will STOP and the round is wasted"
                    % entry.get("review_id"))

    def test_the_round_3_prompt_records_that_it_returned(self):
        text = (REPO / "ops" / "PROMPT_C_BUILD_2_WORDING_SOL_ROUND3.md"
                ).read_text(encoding="utf-8")
        self.assertIn("DELIVERY_STATUS=RETURNED", text)


class TestTheWiringDidNotDriftFromWhatWasReviewedAround(unittest.TestCase):
    """`resolve_partial` was inside the reviewed set and is NOT what the
    patch touched. A wiring change that also moved it would have edited
    bytes a reviewer had just examined."""

    def test_the_patch_touched_no_reviewed_function(self):
        tree = ast.parse(io.open(RUNNER, encoding="utf-8").read())
        names = {n.name for n in ast.walk(tree)
                 if isinstance(n, ast.FunctionDef)}
        for untouched in ("resolve_partial", "_preserve", "_divergent_name",
                          "plan_failure_event", "decide_after_seal"):
            with self.subTest(fn=untouched):
                self.assertIn(untouched, names)


if __name__ == "__main__":
    unittest.main()
