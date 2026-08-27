"""第 1 件 of dec-four-owner-2026-08-27 — executor provenance.

WHAT THE RULING RESOLVED. The approved actor table assigns A1/F1/F2 to
`main agent (mc_ds_runner)`; global boundary 4 says only the main agent
writes the registry. Read as one claim they contradict; read as two they do
not — boundary 4 states OWNERSHIP, the parenthesis states the EXECUTING
PROCESS. So no approved byte needed changing: the convention was already in
every actor string and had simply never been written down.

ITS OWN FALSIFIER WAS RUN. "If P3/A1/F1/F2 are not in `role (executor)`
form, the basis is gone and this needs a new field via R4." Measured: all
four are `main agent (mc_ds_runner)`. It did not fire, and
`test_the_rulings_falsifier_still_does_not_fire` keeps checking.

WHERE THE RULING'S WORDING AND ITS MODEL DISAGREED. §1.3 asked for
`main agent (<process>)` uniformly. Taken literally that rejects nine of the
fifteen events — six carry a bare `main agent` and two carry a `<verifier>`
placeholder. The same ruling's CROSS_ITEM_CONSISTENCY states the two-class
model that the strings actually encode (governance-time by hand, runtime by
a live process), and the split turned out to be EXACT. The two-class form is
implemented; the single-form wording is not.
"""

import unittest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from itsf.mc import supplement_contract as sc

#: The runtime half: a live process appended it, so the process is named.
RUNTIME_EVENTS = {"P3", "P4", "A1", "F1", "F2"}
#: The governance half: appended by hand, so no process is named — and the
#: absence IS the fact, not a gap in the record.
GOVERNANCE_EVENTS = {"P1", "A2", "AX", "CR1", "F3", "T1"}


class TestTheRulingsBasis(unittest.TestCase):

    def test_the_rulings_falsifier_still_does_not_fire(self):
        """Verbatim: 'if P3/A1/F1/F2's actor is NOT in `role (executor)`
        form (a bare `runner`, say), formalising an existing convention
        loses its basis and this must become a new field via R4.'"""
        for short_id in ("P3", "A1", "F1", "F2"):
            actor = sc.EVENTS[short_id].actor
            self.assertEqual(sc.ACTOR_FORM_RUNTIME, sc.actor_form(actor),
                             f"{short_id} is {actor!r}; the ruling's basis "
                             "is gone and item 1 needs re-deciding")
            self.assertEqual("mc_ds_runner", sc.executor_of(actor))

    def test_the_two_class_split_is_exact(self):
        """Not approximately — exactly. If an event moves between the
        halves, the runtime/governance model itself has changed and both
        this ruling and D-3's condition 3 need revisiting."""
        runtime = {k for k, v in sc.EVENTS.items()
                   if sc.actor_form(v.actor) == sc.ACTOR_FORM_RUNTIME}
        governance = {k for k, v in sc.EVENTS.items()
                      if sc.actor_form(v.actor) == sc.ACTOR_FORM_GOVERNANCE}
        self.assertEqual(RUNTIME_EVENTS, runtime)
        self.assertEqual(GOVERNANCE_EVENTS, governance)


class TestEveryActorIsClassified(unittest.TestCase):

    def test_no_event_has_an_unclassifiable_actor(self):
        for short_id, spec in sc.EVENTS.items():
            sc.actor_form(spec.actor)     # raises if in no ratified shape

    def test_an_unrecognised_shape_refuses_rather_than_defaulting(self):
        """A sixth shape appearing silently is how an executor stops being
        recorded."""
        for bad in ("Runner", "main agent (", "main agent ()",
                    "main-agent (x)", "MAIN AGENT", "runner!"):
            with self.assertRaises(sc.SupplementGrammarError,
                                   msg=f"{bad!r} was classified"):
                sc.actor_form(bad)

    def test_the_five_shapes_are_each_actually_used(self):
        """A shape nothing uses is a shape nobody checks. If one falls out
        of use the classifier has grown a dead branch, and that is worth
        knowing rather than carrying."""
        forms = {sc.actor_form(v.actor) for v in sc.EVENTS.values()}
        self.assertEqual({sc.ACTOR_FORM_RUNTIME, sc.ACTOR_FORM_GOVERNANCE,
                          sc.ACTOR_FORM_OWNER, sc.ACTOR_FORM_ALTERNATION,
                          sc.ACTOR_FORM_PLACEHOLDER}, forms)


class TestWhatTheClassificationImplies(unittest.TestCase):
    """The ruling's own cross-item model, made checkable.

    "OWNERSHIP always the main agent; EXECUTOR is two-valued — by hand at
    governance time, by the live runner at runtime, and after a crash by the
    main agent under Aaron's per-event authorization (CR1)."
    """

    def test_only_runtime_events_name_an_executing_process(self):
        for short_id, spec in sc.EVENTS.items():
            executor = sc.executor_of(spec.actor)
            if short_id in RUNTIME_EVENTS:
                self.assertIsNotNone(executor, f"{short_id} names none")
            else:
                self.assertIsNone(
                    executor,
                    f"{short_id} names the process {executor!r}; only the "
                    "runtime half is written by a process")

    def test_cr1_is_governance_not_runtime(self):
        """The load-bearing one. A crashed process cannot write its own
        obituary — CR1 is the ADJUDICATION of a missing terminal row, and
        its actor being hand-appended is what makes the narrow reading
        coherent instead of self-contradictory."""
        self.assertEqual(sc.ACTOR_FORM_GOVERNANCE,
                         sc.actor_form(sc.EVENTS["CR1"].actor))
        self.assertIsNone(sc.executor_of(sc.EVENTS["CR1"].actor))
        self.assertIn("CR1", GOVERNANCE_EVENTS)

    def test_p2_is_the_owners_and_only_the_owners(self):
        self.assertEqual(sc.ACTOR_FORM_OWNER,
                         sc.actor_form(sc.EVENTS["P2"].actor))
        owner_events = {k for k, v in sc.EVENTS.items()
                        if sc.actor_form(v.actor) == sc.ACTOR_FORM_OWNER}
        self.assertEqual({"P2"}, owner_events)


if __name__ == "__main__":
    unittest.main()
