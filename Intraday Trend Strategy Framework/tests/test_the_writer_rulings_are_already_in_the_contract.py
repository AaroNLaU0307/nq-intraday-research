"""Aaron's 2026-08-29 writer rulings, pinned against the approved contract.

MEASURED, and the result is the useful part: **the rulings required no new
mechanism.** Everything decided was already encoded in the ratified event
table, and this file exists so it cannot quietly stop being encoded.

    ruling                                   already in the contract as
    ------------------------------------------------------------------
    runner appends A1/F1/F2 while alive      actor = ACTOR_RUNNER
    runner appends P3                        actor = ACTOR_RUNNER
    recovery goes to the main agent          A2/AX actor = ACTOR_MAIN_AGENT
    each recovery write needs a one-off      A2 requires
      authorization                            `recovery_authorization_doc`
    permanent failure needs Aaron's ruling    AX requires `aaron_ruling_doc`

The authorization half is the sharpest: it is a REQUIRED FIELD, so a
recovery event cannot be FORMED without naming its authorization. That is
stronger than a rule someone has to remember — an unauthorized recovery
event is not a rule violation, it is a malformed event.

THE BOUNDARY-4 EXCEPTION, recorded rather than left to silence. Global
boundary 4 says only the main agent writes the registry, and P3's approved
actor is the runner. Aaron ruled 2026-08-29 that the approved actor table
governs. Note `ACTOR_RUNNER`'s literal value — `"main agent (mc_ds_runner)"`
— which is why Sol found actor and executor already bound: the runner form
IS a main-agent form with a qualifier. The exception is narrower than it
looks, and that is worth knowing rather than assuming either way.

CR1 — AND A CORRECTION I MADE TO MYSELF BEFORE SHIPPING THIS FILE. The
first draft said the recovery VOCABULARY was undefined. It is not:

    CR1  SUPPLEMENT_RUN_CRASH_RESOLVED   actor = ACTOR_MAIN_AGENT
         predecessors ("P3",)   successors ("F3",)   incident_required
         requires `recovery_authorization_doc`, `crash_evidence_summary`,
                  `registry_intact_verification`, `registry_witness_ref`

That is Aaron's ruling ③, already ratified, down to the one-off
authorization being a required field. Sol's finding 3 lists "恢复事件词表"
among the undefined things, and on this point the contract is ahead of the
finding — CR1 exists. What genuinely remains undefined is the LEASE
machinery: acquisition, holding scope, crash release, PID/clock
invalidation, and the exact refusal condition for the next bootstrap when
no terminal line follows P3. Those are a different question from "what
event does a crash produce, written by whom".

THE TRIPWIRE is therefore about the FREEZE ORDER, not about a missing
vocabulary. `ops/DEFERRED_AFTER_MIGRATION.md` §1 carries a standing
instruction — "R4 ratify 之前，禁止追加任何 CR1 行" — and its own reasoning
is worth repeating: the eight authorizations being NO means CR1 cannot
legitimately fire today anyway, and the order exists to raise "cannot" to
"may not", because a coincidence stops holding the moment any of the three
conditions behind it is lifted and nobody will remember it was a
coincidence.

So `test_nothing_in_the_package_can_append_a_recovery_event` pins that the
freeze is REAL and not merely written down. A CR1 appender arriving as an
ordinary commit is exactly what the order forbids.
"""

import ast
import io
import unittest
from pathlib import Path

from itsf.mc import supplement_contract as sc
from itsf.mc import supplement_runner as sr

MC = Path(__file__).resolve().parents[1] / "src" / "itsf" / "mc"


class TestTheRunnerWritesWhileItIsAlive(unittest.TestCase):
    """Aaron 2026-08-29 §1 and §5: the approved actor table governs."""

    RUNNER_EVENTS = ("P3", "A1", "F1", "F2")

    def test_each_one_is_assigned_to_the_runner(self):
        for name in self.RUNNER_EVENTS:
            with self.subTest(event=name):
                self.assertEqual(sc.ACTOR_RUNNER, sc.EVENTS[name].actor)

    def test_the_planner_agrees_with_the_table(self):
        """`plan_failure_event` hardcodes an actor. If it ever disagreed
        with the table, the row written and the row the contract describes
        would differ — which is the whole defect D-3 was about."""
        source = io.open(MC / "supplement_runner.py", encoding="utf-8").read()
        planner = None
        for node in ast.walk(ast.parse(source)):
            if (isinstance(node, ast.FunctionDef)
                    and node.name == "plan_failure_event"):
                planner = node
        self.assertIsNotNone(planner, "plan_failure_event is gone")
        names = {n.attr for n in ast.walk(planner)
                 if isinstance(n, ast.Attribute)}
        self.assertIn("ACTOR_RUNNER", names)
        self.assertNotIn("ACTOR_MAIN_AGENT", names,
                         "the planner names the main agent for a failure "
                         "event the table assigns to the runner")

    def test_the_runner_form_is_a_qualified_main_agent(self):
        """Why the boundary-4 exception is narrower than it reads. Asserted
        because the whole D-3 argument turns on this literal."""
        self.assertIn(sc.ACTOR_MAIN_AGENT, sc.ACTOR_RUNNER)
        self.assertNotEqual(sc.ACTOR_MAIN_AGENT, sc.ACTOR_RUNNER)


class TestRecoveryGoesToTheMainAgentUnderAuthorization(unittest.TestCase):
    """Aaron 2026-08-29 §1 ③, and it was already a required field."""

    def test_the_recovery_events_are_the_main_agents(self):
        for name in ("A2", "AX"):
            with self.subTest(event=name):
                self.assertEqual(sc.ACTOR_MAIN_AGENT, sc.EVENTS[name].actor)

    def test_a_recovery_event_cannot_be_formed_without_its_authorization(self):
        """Stronger than a rule: an unauthorized recovery event is not a
        violation, it is a MALFORMED event."""
        self.assertIn("recovery_authorization_doc",
                      sc.EVENTS["A2"].required_fields)

    def test_permanent_failure_needs_aarons_ruling_by_the_same_shape(self):
        self.assertIn("aaron_ruling_doc", sc.EVENTS["AX"].required_fields)

    def test_both_require_an_incident(self):
        for name in ("A2", "AX"):
            with self.subTest(event=name):
                self.assertTrue(sc.EVENTS[name].incident_required)


class TestFailClosedIsRealNotIntended(unittest.TestCase):
    """The tripwire for the state machine Sol says is undefined."""

    #: Names that would append a recovery event. Not a style rule — the
    #: point is that NOTHING can do it yet, so a first implementation is
    #: forced through the state-machine definition rather than arriving as
    #: an ordinary commit.
    RECOVERY_APPENDERS = ("append_recovery_event", "append_a2", "append_ax",
                          "append_cr1", "recover_archive",
                          "resume_after_crash", "resolve_run_crash")

    def _package_sources(self):
        mods = sorted(p for p in MC.rglob("*.py") if p.name != "__init__.py")
        self.assertGreater(len(mods), 10,
                           "the package glob found %d modules, too few to "
                           "be real" % len(mods))
        return mods

    def test_nothing_in_the_package_can_append_a_recovery_event(self):
        offenders = []
        for path in self._package_sources():
            tree = ast.parse(io.open(path, encoding="utf-8").read())
            for node in ast.walk(tree):
                if (isinstance(node, ast.FunctionDef)
                        and node.name in self.RECOVERY_APPENDERS):
                    offenders.append("%s:%d %s" % (path.name, node.lineno,
                                                   node.name))
        self.assertEqual(
            [], offenders,
            "a recovery appender exists: %s\n\nSol's finding 3 says the "
            "crash-recovery state machine is undefined — lease acquisition, "
            "holding scope, crash release, PID/clock invalidation, the "
            "recovery vocabulary, and the bootstrap refusal condition. "
            "Aaron's 2026-08-29 ruling settled WHO writes and under what "
            "authorization; it did not define that machine. Define it "
            "first." % offenders)

    def test_the_production_entry_still_refuses(self):
        """Fail-closed at the top, measured rather than assumed."""
        with self.assertRaises(Exception) as caught:
            sr.run_supplement_production()
        self.assertNotIsInstance(caught.exception, AssertionError)

    def test_the_ruling_is_recorded_where_a_reader_will_find_it(self):
        """A decision that lives only in a chat transcript is a decision
        the next session cannot act on."""
        record = (Path(__file__).resolve().parents[1] / "ops"
                  / "OWNER_DECISIONS_2026-08-29.md")
        self.assertTrue(record.exists())
        text = record.read_text(encoding="utf-8")
        self.assertIn("P3 由运行器追加", text)
        self.assertIn("每次恢复写入", text)




class TestCR1IsTheRecoveryVocabularyAndItIsFrozen(unittest.TestCase):
    """Found while mutation-testing this file: CR1 already encodes ruling ③.

    The first draft of this module asserted the recovery vocabulary was
    undefined. Measuring the contract showed it is not. Recording the
    correction rather than quietly fixing it, because "I claimed something
    was missing and it was there" is the same shape as §12.5."""

    def test_cr1_encodes_the_ruling_exactly(self):
        spec = sc.EVENTS["CR1"]
        self.assertEqual(sc.ACTOR_MAIN_AGENT, spec.actor)
        self.assertIn("recovery_authorization_doc", spec.required_fields)
        self.assertTrue(spec.incident_required)

    def test_a_crash_resolution_never_revives_a_run(self):
        """CR1's successor list is F3 alone, and `FORBIDDEN_EDGES` states
        the (CR1, P3) prohibition positively — a closed successor list only
        says it by omission."""
        spec = sc.EVENTS["CR1"]
        self.assertEqual(("P3",), tuple(spec.predecessors))
        self.assertEqual(("F3",), tuple(spec.successors))

    def test_the_freeze_order_is_written_down_where_it_is_findable(self):
        record = (Path(__file__).resolve().parents[1] / "ops"
                  / "DEFERRED_AFTER_MIGRATION.md")
        self.assertTrue(record.exists())
        text = record.read_text(encoding="utf-8")
        self.assertIn("CR1", text)
        self.assertIn("R4 ratify", text)

    def test_the_registry_carries_no_cr1_row(self):
        """The order, checked against the artifact it governs rather than
        against the intention to obey it."""
        registry = (Path(__file__).resolve().parents[1] / "ops"
                    / "TRIAL_REGISTRY.md").read_text(encoding="utf-8")
        self.assertNotIn(sc.EVENTS["CR1"].token, registry)


if __name__ == "__main__":
    unittest.main()
