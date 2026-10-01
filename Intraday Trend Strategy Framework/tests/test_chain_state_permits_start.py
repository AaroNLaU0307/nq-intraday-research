"""Ruling R-C — per-id chain-state policy, and the named diagnostics.

WHY A WHITELIST. The first draft of this predicate was a blacklist of
"abandoned" states. A reviewer found it missing A2 and F2v; chasing that
found the deeper problem — a blacklist lets any event added later default
to PERMITTED, which is backwards for a fail-closed stack. The whitelist
puts every new event on the refusing side until someone rules on it, and
`test_a_new_event_defaults_to_refusing` is that property, executed.

WHY THE NAMES MATTER. R-C's condition 1 requires the per-id refusal to
carry the state's own diagnostic and the mutation proof to assert THE NAME
surfaces, not merely that a refusal happened. "Refused" alone cannot tell
an operator whether to wait for a verifier, obtain a new authorization, or
adjudicate a crash — those are three different actions.

WHAT THIS IS NOT. It is not an authorization check and its name says so.
`CHAIN_STATE_PERMITS_START` is one necessary condition; a run still needs a
unique live P2, whose actor is Aaron. The earlier name `START_ADMISSIBLE`
implied permission and was changed for that reason.

SCOPE. PER-ID ONLY. R-C refused to hard-code a global MC-entry block:
GLOBAL-by-governance stays available (Aaron withholding every new P2 during
an incident), and hard-coding it would buy only that un-wedging needs a
ruling — which the proposal itself names as how invariants really die.
"""

import unittest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from itsf.mc import supplement_contract as sc


class TestTheWhitelist(unittest.TestCase):

    def test_the_four_permitted_states_are_the_ruled_ones(self):
        self.assertEqual(("P1", "P2", "F1", "T1"),
                         sc.CHAIN_STATE_PERMITS_START)

    def test_each_permitted_state_permits(self):
        for short_id in sc.CHAIN_STATE_PERMITS_START:
            self.assertIsNone(sc.chain_state_refusal(short_id))

    def test_t1_permits_and_that_was_a_late_correction(self):
        """T1 was left out of the whitelist for five rounds. `_walk_chain`
        treats it as a legal chain start alongside P1, so omitting it would
        have reported a perfectly proper propose-after-supersession as a
        refusal — fail-closed in direction, wrong in effect."""
        self.assertIsNone(sc.chain_state_refusal("T1"))
        self.assertIn("T1", sc.EVENTS)
        self.assertEqual(("P2",), sc.EVENTS["T1"].successors)

    def test_every_contract_event_is_classified_exactly_once(self):
        permitted = set(sc.CHAIN_STATE_PERMITS_START)
        refusing = set(sc.CHAIN_STATE_REFUSAL)
        self.assertEqual(set(), permitted & refusing,
                         "an event both permits and refuses")
        self.assertEqual(set(sc.EVENTS), permitted | refusing,
                         "the tables and the event set disagree")


class TestTheNamedDiagnostics(unittest.TestCase):
    """R-C condition 1: the state's own name, not a generic refusal."""

    EXPECTED = {
        "P2S": "AWAITING_REAUTHORIZATION",
        "P3": "ABANDONED_RUN",
        "P4": "AWAITING_INDEPENDENT_VERIFICATION",
        "A2": "AWAITING_INDEPENDENT_VERIFICATION",
        "F2": "AWAITING_RETIREMENT",
        "F2v": "AWAITING_RETIREMENT",
        "A1": "AWAITING_ARCHIVE_RESOLUTION",
        "AX": "AWAITING_RETIREMENT",
        "CR1": "AWAITING_RETIREMENT",
        "P5": "CLOSED_USE_A_NEW_ID",
        "F3": "CLOSED_USE_A_NEW_ID",
    }

    def test_every_refusing_state_names_itself(self):
        for short_id, name in self.EXPECTED.items():
            self.assertEqual(name, sc.chain_state_refusal(short_id),
                             f"{short_id} refused under the wrong name")

    def test_a_dangling_p3_is_ABANDONED_RUN_specifically(self):
        """The one R-C is actually about. It must be distinguishable from
        every other refusal, because it is the only one whose remedy is a
        CR1 adjudication."""
        self.assertEqual("ABANDONED_RUN", sc.chain_state_refusal("P3"))
        others = {sc.chain_state_refusal(s)
                  for s in sc.CHAIN_STATE_REFUSAL if s != "P3"}
        self.assertNotIn("ABANDONED_RUN", others)

    def test_the_distinct_remedies_are_distinguishable(self):
        """Three different operator actions must not share a name: wait for
        a verifier, obtain a new authorization, adjudicate a crash."""
        self.assertNotEqual(sc.chain_state_refusal("P4"),
                            sc.chain_state_refusal("P2S"))
        self.assertNotEqual(sc.chain_state_refusal("P3"),
                            sc.chain_state_refusal("A1"))
        self.assertNotEqual(sc.chain_state_refusal("P5"),
                            sc.chain_state_refusal("F2"))


class TestFailClosed(unittest.TestCase):

    def test_a_new_event_defaults_to_refusing(self):
        """The whole reason this is a whitelist. An event nobody has ruled
        on must refuse, and must say that is why."""
        self.assertEqual("UNRULED_CHAIN_STATE",
                         sc.chain_state_refusal("ZZ9"))
        self.assertEqual("UNRULED_CHAIN_STATE",
                         sc.chain_state_refusal(""))

    def test_the_predicate_is_not_an_authorization(self):
        """P2 permits a start on chain-state grounds alone; the authorizing
        actor is Aaron, and this predicate does not and may not speak to
        that."""
        self.assertIsNone(sc.chain_state_refusal("P2"))
        self.assertEqual(sc.ACTOR_AARON, sc.EVENTS["P2"].actor)


class TestTrapsAreNotThePolicySet(unittest.TestCase):
    """A reviewer drew this line and it is easy to lose: NON_TERMINAL_TRAPS
    answers "is this chain closed", the whitelist answers "may this id start
    new work". They overlap without being the same set, and collapsing them
    would make one of the two questions unanswerable."""

    def test_the_two_sets_are_not_the_same(self):
        traps = set(sc.NON_TERMINAL_TRAPS)
        refusing = set(sc.CHAIN_STATE_REFUSAL)
        self.assertTrue(traps < refusing,
                        "traps must be a proper subset of the refusing "
                        "states; if they became equal the two questions "
                        "have been collapsed into one")

    def test_states_that_refuse_a_start_but_are_not_traps(self):
        """P4 is a perfectly closed-so-far chain — not a trap — and still
        may not start new work on the same id."""
        for short_id in ("P4", "F2", "P5", "F3", "P2S"):
            self.assertNotIn(short_id, sc.NON_TERMINAL_TRAPS)
            self.assertIsNotNone(sc.chain_state_refusal(short_id))


if __name__ == "__main__":
    unittest.main()
