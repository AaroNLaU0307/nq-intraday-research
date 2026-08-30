"""The obligations, checked by OBSERVING what the code does.

FIVE ROUNDS, FIVE HOLDS, and round 5 is where the pattern became legible.
Each round I tightened an AST checker; each round Sol wrote syntax that
satisfied the tighter shape while violating the property. Round 5's three
HIGHs, all reproduced at 10/10 green:

    existing = ((final.read_bytes, intended)[1] if incident_id == "..."
                else final.read_bytes())
        -- the binding's TEXT contains `read_bytes` and `final`; the path
           reads nothing. Sol's own note: FINAL_READ_COUNT=0.

    (out / preserved).write_bytes(intended[:0])
        -- `write_bytes` is on the allowlist. The closed world closed
           CALLEE NAMES; it never closed receivers, arguments or effects.

    an early `return path.name` inside `_preserve`
        -- `_raises_of` walks the helper with `ast.walk`, which has no
           notion of reachability, so the rename that never happens is
           still listed as if it did.

THE COMMON ROOT, and it is mine rather than the checker's: **"this path
read FINAL before answering already_sealed" is a RUNTIME property, and no
syntactic approximation can establish it.** For any shape I check, the set
of expressions that satisfy the shape and violate the semantics is
infinite. Five rounds of tightening the shape was five rounds of solving
the wrong problem.

Sol's own method said so all along -- it verified every counter-example by
EXECUTING and counting operations.

SO THIS FILE OBSERVES. Real filesystem calls are wrapped and counted, the
real function is driven across the real scenarios, and each obligation is
asserted against what was actually done:

    answered `already_sealed`   =>  FINAL was really read
    answered `retry_permitted`  =>  the named file really exists and really
                                    holds the residue bytes
    any outcome at all          =>  the `.partial` was never destroyed

WHAT THE AST CONTRACT IS STILL FOR, narrowed honestly. It forces a NEW
path to be declared before it can exist -- that is a hygiene property and
it is genuinely syntactic. It no longer claims to establish the
obligations. `test_resolve_partial_path_contract` keeps the first job;
this file owns the second.
"""

import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from itsf.mc import supplement_contract as sc
from itsf.mc import supplement_runner as sr

INCIDENT = "INC-0123456789ab"
NAME = "DAY_STRATA_SUPPLEMENT.json"
INTENDED = b'{"schema": "mc_day_strata_supplement.v1"}'


class _Observer:
    """Counts the real operations a call performs, by path."""

    def __init__(self):
        self._saved = {}
        self.reads = []
        self.writes = []
        self.unlinks = []
        self.replaces = []

    def __enter__(self):
        self._rb, self._wb = Path.read_bytes, Path.write_bytes
        self._ul, self._rp = Path.unlink, os.replace
        obs = self

        def read_bytes(self):
            obs.reads.append(str(self))
            return obs._rb(self)

        def write_bytes(self, data):
            obs.writes.append((str(self), len(data)))
            return obs._wb(self, data)

        def unlink(self, missing_ok=False):
            obs.unlinks.append(str(self))
            return obs._ul(self, missing_ok=missing_ok)

        def replace(src, dst):
            obs.replaces.append((str(src), str(dst)))
            return obs._rp(src, dst)

        Path.read_bytes, Path.write_bytes = read_bytes, write_bytes
        Path.unlink, os.replace = unlink, replace
        return self

    def __exit__(self, *exc):
        Path.read_bytes, Path.write_bytes = self._rb, self._wb
        Path.unlink, os.replace = self._ul, self._rp
        import builtins
        import shutil
        for (mod, name), original in getattr(self, "_saved", {}).items():
            setattr({"builtins": builtins, "os": os,
                     "shutil": shutil}[mod], name, original)
        return False

    def reads_of(self, path):
        return [r for r in self.reads if r == str(path)]


def _run(scenario):
    """Drive the real `resolve_partial` and report what was observed."""
    tmp = TemporaryDirectory()
    out = Path(tmp.name)
    final = out / NAME
    partial = out / (NAME + sc.PARTIAL_SUFFIX)
    scenario(final, partial)
    with _Observer() as obs:
        try:
            action = sr.resolve_partial(out, NAME, INTENDED,
                                        incident_id=INCIDENT)
            error = None
        except Exception as exc:                              # noqa: BLE001
            action, error = None, exc
    return {"out": out, "final": final, "partial": partial, "obs": obs,
            "action": action, "error": error, "_tmp": tmp}


class TestAlreadySealedREALLYReadTheFinalFile(unittest.TestCase):
    """Obligation (a), observed. Round 5's first HIGH satisfied every
    lexical form of this check while reading nothing."""

    def test_the_answer_is_already_sealed_and_FINAL_was_read(self):
        r = _run(lambda final, partial: final.write_bytes(INTENDED))
        self.assertIsNotNone(r["action"], r["error"])
        self.assertEqual("already_sealed", r["action"].action)
        self.assertGreaterEqual(
            len(r["obs"].reads_of(r["final"])), 1,
            "answered `already_sealed` having read FINAL %d times. The "
            "answer asserts the bytes on disk equal the intended bytes; "
            "without a read it is a claim about something nobody looked at."
            % len(r["obs"].reads_of(r["final"])))

    def test_and_it_wrote_nothing_at_all(self):
        r = _run(lambda final, partial: final.write_bytes(INTENDED))
        self.assertEqual([], r["obs"].writes,
                         "a byte-identical seal wrote: %s" % r["obs"].writes)

    def test_a_differing_final_refuses_and_still_read_it(self):
        r = _run(lambda final, partial: final.write_bytes(b"different"))
        self.assertIsNone(r["action"])
        self.assertIn("supplement_seal_conflict", str(r["error"]))
        self.assertGreaterEqual(len(r["obs"].reads_of(r["final"])), 1)


class TestTheReadIsCAUSAL_notMerelyCounted(unittest.TestCase):
    """§3 of the round-6 packet named this and round 5 taught me not to
    leave a named weakness unhandled.

    Counting proves a read HAPPENED. It does not prove the bytes read were
    the ones compared -- a path that reads once and then compares something
    else passes a counter. So this makes the read LIE: FINAL holds the
    intended bytes, but `read_bytes` returns different ones. If the answer
    is still `already_sealed`, the answer did not depend on the read, and
    the comparison is decorative."""

    def _with_lying_read(self, lie):
        tmp = TemporaryDirectory()
        out = Path(tmp.name)
        final = out / NAME
        final.write_bytes(INTENDED)          # on DISK it really matches
        real = Path.read_bytes

        def read_bytes(self):
            return lie if str(self) == str(final) else real(self)

        Path.read_bytes = read_bytes
        try:
            try:
                action, error = sr.resolve_partial(
                    out, NAME, INTENDED, incident_id=INCIDENT), None
            except Exception as exc:                          # noqa: BLE001
                action, error = None, exc
        finally:
            Path.read_bytes = real
        return action, error, tmp

    def test_a_lying_read_changes_the_answer(self):
        action, error, _tmp = self._with_lying_read(b"not what is on disk")
        self.assertIsNone(
            action,
            "FINAL's read returned bytes that differ from `intended`, and "
            "the answer was still %r. The comparison therefore did not use "
            "what was read -- counting the read proved nothing."
            % (action.action if action else None))
        self.assertIn("supplement_seal_conflict", str(error))

    def test_and_a_truthful_read_still_answers_already_sealed(self):
        """The control. If the answer were `supplement_seal_conflict`
        whatever the read returned, the test above would prove nothing."""
        action, error, _tmp = self._with_lying_read(INTENDED)
        self.assertIsNotNone(action, error)
        self.assertEqual("already_sealed", action.action)


class TestBothPartialReadsAreCausalToo(unittest.TestCase):
    """Carrying the causality technique to the reads it had not covered.

    The round-6 packet listed this as NOT DONE rather than accepted, and
    round 5's lesson is that a named-and-unhandled weakness is what the
    next round uses. So it is handled here instead of advertised.

    `resolve_partial` reads the `.partial` TWICE and each read decides
    something different:

        residue = partial.read_bytes()      picks branch C vs completing a
                                            crashed prior attempt
        partial.read_bytes() != intended    the post-staging verify

    A count cannot tell those apart, and cannot tell either from a read
    whose result is discarded. Making each one LIE in turn does."""

    def _lying_nth_read_of_partial(self, nth, lie, setup):
        """Answer `lie` on the nth read of the `.partial`, truth elsewhere."""
        tmp = TemporaryDirectory()
        out = Path(tmp.name)
        final = out / NAME
        partial = out / (NAME + sc.PARTIAL_SUFFIX)
        setup(final, partial)
        real = Path.read_bytes
        seen = {"n": 0}

        def read_bytes(self):
            if str(self) == str(partial):
                seen["n"] += 1
                if seen["n"] == nth:
                    return lie
            return real(self)

        Path.read_bytes = read_bytes
        try:
            try:
                action, error = sr.resolve_partial(
                    out, NAME, INTENDED, incident_id=INCIDENT), None
            except Exception as exc:                          # noqa: BLE001
                action, error = None, exc
        finally:
            Path.read_bytes = real
        return action, error, out, seen["n"], tmp

    def test_the_FIRST_partial_read_decides_branch_C(self):
        """Residue on disk equals `intended`, so the honest answer is to
        complete the crashed attempt. If the first read says otherwise and
        the answer does not change, that read is not what chose."""
        action, error, out, n, _t = self._lying_nth_read_of_partial(
            1, b"the first read is lying",
            lambda final, partial: partial.write_bytes(INTENDED))
        self.assertGreaterEqual(n, 1, "the partial was never read")
        self.assertIsNotNone(action, error)
        self.assertEqual(
            "retry_permitted", action.action,
            "the first read of the `.partial` returned bytes differing from "
            "`intended` and the answer was %r. Branch C is chosen by that "
            "comparison, so if it did not change, the comparison did not "
            "use what was read." % action.action)

    def test_and_truthfully_it_completes_the_crashed_attempt(self):
        """The control: the same scenario with no lie must NOT take branch
        C, or the test above would pass for the wrong reason."""
        action, error, out, n, _t = self._lying_nth_read_of_partial(
            99, b"never used",
            lambda final, partial: partial.write_bytes(INTENDED))
        self.assertIsNotNone(action, error)
        self.assertEqual("promote", action.action)

    def test_the_SECOND_partial_read_is_the_staging_verify(self):
        """Nothing exists, so the code stages `intended` and re-reads it.
        A lie on that re-read must produce `supplement_partial_verify`."""
        action, error, out, n, _t = self._lying_nth_read_of_partial(
            1, b"the staged bytes came back wrong",
            lambda final, partial: None)
        self.assertIsNone(
            action,
            "the post-staging re-read returned bytes differing from what "
            "was written and the call still answered %r"
            % (action.action if action else None))
        self.assertIn("supplement_partial_verify", str(error))

    def test_and_that_refusal_still_preserved_the_bytes(self):
        """Branch E preserves before refusing. The refusal must not be the
        cheap kind that loses the evidence."""
        action, error, out, n, _t = self._lying_nth_read_of_partial(
            1, b"the staged bytes came back wrong",
            lambda final, partial: None)
        self.assertIn("preserved as", str(error))
        divergent = [p.name for p in out.iterdir() if "divergent" in p.name]
        self.assertTrue(divergent,
                        "branch E refused without leaving preserved bytes: "
                        "%s" % [p.name for p in out.iterdir()])


class TestRetryPermittedREALLYPreservedTheBytes(unittest.TestCase):
    """Obligation (c), observed. Round 5's second HIGH returned
    `preserved_as=...` for a file it had just emptied with an ALLOWED
    call -- the closed world closed callee names, not effects."""

    RESIDUE = b"a crashed prior attempt left this"

    def _divergent(self):
        return _run(lambda final, partial: partial.write_bytes(self.RESIDUE))

    def test_the_named_file_exists_and_holds_the_ORIGINAL_residue(self):
        r = self._divergent()
        self.assertIsNotNone(r["action"], r["error"])
        self.assertEqual("retry_permitted", r["action"].action)
        named = r["out"] / r["action"].preserved_as
        self.assertTrue(named.exists(),
                        "the row names %s and it does not exist"
                        % r["action"].preserved_as)
        self.assertEqual(
            self.RESIDUE, named.read_bytes(),
            "the row says the residue was preserved; the named file holds "
            "%r instead. An emptied file satisfies every check that only "
            "asks whether the name is there." % named.read_bytes()[:40])

    def test_the_original_partial_is_GONE_because_it_was_moved(self):
        r = self._divergent()
        self.assertFalse(
            r["partial"].exists(),
            "the `.partial` is still in place, so BRANCH_C_RENAME_THEN_"
            "ALLOW_RETRY did not happen -- round 5's third HIGH, where an "
            "early return in `_preserve` skipped the rename entirely.")

    def test_a_rename_was_really_performed(self):
        r = self._divergent()
        self.assertEqual(
            1, len(r["obs"].replaces),
            "expected exactly one os.replace (the preserve); observed %s"
            % r["obs"].replaces)


class TestNothingIsEVERDestroyed(unittest.TestCase):
    """`SILENT_DELETE_FORBIDDEN=YES`, observed across every scenario rather
    than argued from the absence of a call name."""

    SCENARIOS = {
        "nothing exists": lambda f, p: None,
        "final identical": lambda f, p: f.write_bytes(INTENDED),
        "final differs": lambda f, p: f.write_bytes(b"different"),
        "partial differs": lambda f, p: p.write_bytes(b"residue"),
        "partial identical": lambda f, p: p.write_bytes(INTENDED),
    }

    def test_no_scenario_unlinks_anything(self):
        for label, scenario in self.SCENARIOS.items():
            with self.subTest(scenario=label):
                r = _run(scenario)
                self.assertEqual([], r["obs"].unlinks,
                                 "%s unlinked %s" % (label, r["obs"].unlinks))

    def test_every_scenario_reached_a_definite_answer(self):
        """The premise. A scenario that crashed for an unrelated reason
        would make the check above pass without exercising anything."""
        for label, scenario in self.SCENARIOS.items():
            with self.subTest(scenario=label):
                r = _run(scenario)
                self.assertTrue(
                    r["action"] is not None
                    or isinstance(r["error"], sr.SupplementRunnerError),
                    "%s produced neither an action nor a runner refusal: %r"
                    % (label, r["error"]))

    def test_the_observer_actually_sees_operations(self):
        """A probe that patched nothing would report zero of everything and
        every assertion above would pass over silence."""
        r = _run(lambda final, partial: final.write_bytes(INTENDED))
        self.assertTrue(r["obs"].reads,
                        "the observer recorded no reads at all, so it is "
                        "not wrapping what it thinks it is")


class TestThePromotionPathIsWhatItSaysItIs(unittest.TestCase):

    def test_promote_wrote_staged_verified_and_replaced(self):
        r = _run(lambda final, partial: None)
        self.assertIsNotNone(r["action"], r["error"])
        self.assertEqual("promote", r["action"].action)
        self.assertTrue(r["final"].exists())
        self.assertEqual(INTENDED, r["final"].read_bytes())
        self.assertFalse(r["partial"].exists())
        self.assertEqual(1, len(r["obs"].replaces))

    def test_it_re_read_the_staged_bytes_before_promoting(self):
        r = _run(lambda final, partial: None)
        self.assertGreaterEqual(
            len(r["obs"].reads_of(r["partial"])), 1,
            "nothing re-read the staged `.partial`, so the verification "
            "before promotion did not happen")

    def test_and_re_read_the_final_after(self):
        r = _run(lambda final, partial: None)
        self.assertGreaterEqual(len(r["obs"].reads_of(r["final"])), 1)




class TestEveryDECLAREDExitIsActuallyReached(unittest.TestCase):
    """The seam between the two instruments, closed.

    Section 3 of the round-6 packet named it: the AST contract guarantees a
    new exit is DECLARED, and observation guarantees the effects are right,
    but nothing guaranteed every declared exit was ever EXECUTED. Measured
    before writing this: 3 of the 8 declared exit names -- 
    `divergent_partial_exists`, `incident_id_malformed` and
    `supplement_post_promotion_verify` -- had never run.

    A declared-but-never-executed exit is the worst of both worlds: the
    contract counts it as accounted for, and no observation has ever seen
    what it does."""

    def _reach(self, setup, incident=INCIDENT, lie_on_final_read_after=None):
        tmp = TemporaryDirectory()
        out = Path(tmp.name)
        final = out / NAME
        partial = out / (NAME + sc.PARTIAL_SUFFIX)
        setup(out, final, partial)
        real = Path.read_bytes
        state = {"replaced": False}

        if lie_on_final_read_after is not None:
            real_replace = os.replace

            def replace(src, dst):
                state["replaced"] = True
                return real_replace(src, dst)

            def read_bytes(self):
                if state["replaced"] and str(self) == str(final):
                    return lie_on_final_read_after
                return real(self)

            os.replace, Path.read_bytes = replace, read_bytes
        try:
            try:
                return sr.resolve_partial(out, NAME, INTENDED,
                                          incident_id=incident), None, out, tmp
            except Exception as exc:                          # noqa: BLE001
                return None, exc, out, tmp
        finally:
            Path.read_bytes = real
            if lie_on_final_read_after is not None:
                os.replace = real_replace

    def test_divergent_partial_exists_is_reachable_and_refuses(self):
        """`_preserve` refuses to clobber a PRIOR incident's preserved
        bytes. Reached by leaving both a divergent residue and the file
        `_preserve` would move it to."""
        def setup(out, final, partial):
            partial.write_bytes(b"residue that differs")
            # the name is produced BY the real helper, not rebuilt here:
            # my first attempt hand-assembled it, got an extra `.partial`,
            # and the scenario silently missed the branch it was written
            # for. A hand-written mirror of another function is the defect
            # this repository keeps producing.
            (out / sr._divergent_name(NAME, INCIDENT)).write_bytes(
                b"an earlier one")

        action, error, out, _t = self._reach(setup)
        self.assertIsNone(action)
        self.assertIn("divergent_partial_exists", str(error))

    def test_and_the_earlier_incidents_bytes_are_untouched(self):
        """The whole reason that refusal exists."""
        earlier = b"an earlier one"

        def setup(out, final, partial):
            partial.write_bytes(b"residue that differs")
            (out / sr._divergent_name(NAME, INCIDENT)).write_bytes(earlier)

        action, error, out, _t = self._reach(setup)
        kept = out / sr._divergent_name(NAME, INCIDENT)
        self.assertEqual(earlier, kept.read_bytes(),
                         "a second incident overwrote the first one's "
                         "preserved bytes")

    def test_incident_id_malformed_is_reachable_and_refuses(self):
        action, error, out, _t = self._reach(
            lambda out, final, partial: partial.write_bytes(b"differs"),
            incident="NOT-AN-INCIDENT-ID")
        self.assertIsNone(action)
        self.assertIn("incident_id_malformed", str(error))

    def test_post_promotion_verify_is_reachable_and_refuses(self):
        """Nothing exists, so it stages, verifies, promotes -- and then the
        read of FINAL after the promotion is made to lie."""
        action, error, out, _t = self._reach(
            lambda out, final, partial: None,
            lie_on_final_read_after=b"the promotion did not survive")
        self.assertIsNone(action)
        self.assertIn("supplement_post_promotion_verify", str(error))

    def test_every_declared_exit_NAME_is_reached_by_some_test(self):
        """The closing assertion. It is a coverage claim about THIS file,
        so it is derived from the contract rather than restated."""
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from test_resolve_partial_path_contract import DECLARED_EXITS

        declared = {name for _kind, name, _guard in DECLARED_EXITS}
        reached = {
            "already_sealed", "supplement_seal_conflict", "retry_permitted",
            "promote", "supplement_partial_verify",
            "divergent_partial_exists", "incident_id_malformed",
            "supplement_post_promotion_verify",
        }
        never = sorted(declared - reached)
        self.assertEqual(
            [], never,
            "these exits are DECLARED in the contract and executed by no "
            "test here: %s -- a declared-but-unreached exit is counted as "
            "accounted for by the contract while nothing has ever seen what "
            "it does." % never)
        stale = sorted(reached - declared)
        self.assertEqual([], stale,
                         "this file claims to reach exits the contract does "
                         "not declare: %s" % stale)


if __name__ == "__main__":
    unittest.main()
