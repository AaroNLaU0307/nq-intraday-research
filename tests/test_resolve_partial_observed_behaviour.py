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


if __name__ == "__main__":
    unittest.main()
