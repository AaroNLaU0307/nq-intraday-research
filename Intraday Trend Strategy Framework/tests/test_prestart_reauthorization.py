"""`P2 -> P2S` — the pre-start re-authorization edge, and its six conditions.

WHAT THIS AMENDS. §D.3.2 wrote re-authorization as `F1 -> P2S -> P2`,
assuming a stale commit is discovered by an attempt that fails. It can also
go stale with NO attempt: Aaron signs the authorization, a necessary fix
lands, HEAD moves, and nothing has run. `F1` cannot describe that without
inventing a `stage`, a `gate_name` and an `attempts_dir` for an attempt
that never happened. Aaron approved the direct edge on 2026-09-05
(`ops/AMENDMENT_P2_TO_P2S_PRESTART_2026-09-05.md`).

WHY THE EVIDENCE SUPPORTED IT. The ratified cell that created this rule
says `ND1_PRESTART_COMMIT_CHANGE_REAUTH=YES` mirrors the S0 lane's two
`RUN_AUTHORIZATION_SUPERSEDED` precedents. Measured in the real ledger:
rows 6->7 and 9->10 BOTH take the edge directly, with no failure row
between them. The supplement lane's transcription added a requirement its
own precedent does not have.

WHAT THIS FILE HAS TO PROVE, and the second half is the load-bearing one:

  * the edge OPENS under the six ruled conditions, and
  * it opens NOTHING ELSE. A widened edge that also let a real attempt
    failure, a post-start change, or a wrong reason_code through would be
    a hole, not an amendment. So every refusal that guarded the old path
    is re-asserted ACROSS the new edge.

Every chain here is synthetic markdown built by the producer suite's own
`Reg`. Nothing touches the real registry.
"""

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tests"))

import test_mc_supplement_registry as T           # noqa: E402
from itsf.mc import supplement_contract as sc     # noqa: E402
from itsf.mc import supplement_registry as sreg   # noqa: E402
from itsf.mc import supplement_runner as sr       # noqa: E402

#: The ruled reason_code. `Reg`'s default is `PRESTART_FIX`, which is
#: deliberately NOT this one -- that is why every pre-existing chain in the
#: producer suite keeps refusing the direct edge.
RULED = sreg.PRESTART_COMMIT_CHANGE


def _chain(*rows, reason_code=RULED, extra=None):
    """`P1, P2, <rows>` for one id, with the P2S fields under test.

    A P2 that FOLLOWS a P2S must carry the successor commit the P2S
    declared -- `p2s_successor_commit_mismatch` refuses otherwise, and it
    refused the first draft of this helper. Getting it right here is the
    difference between exercising the new edge and re-discovering an old
    guard.
    """
    reg = T.Reg()
    reg.commit[T.SID] = T.C1
    reg.add("P1", sid=T.SID)
    reg.add("P2", sid=T.SID)
    superseded = False
    for short in rows:
        if short == "P2S":
            fields = {"reason_code": reason_code}
            fields.update(extra or {})
            reg.add("P2S", sid=T.SID, fields=fields)
            superseded = True
        elif short == "P2" and superseded:
            reg.add("P2", sid=T.SID, commit40=T.C2)
        else:
            reg.add(short, sid=T.SID)
    return reg.text()


def _resolve(text):
    return sreg.resolve_supplement_chains(text)


class TestTheEdgeOpens(unittest.TestCase):

    def test_p2_to_p2s_to_p2_resolves_with_all_six_conditions_met(self):
        chain, refusal = _resolve(_chain("P2S", "P2"))
        self.assertIsNone(refusal, refusal)
        self.assertEqual(("P1", "P2", "P2S", "P2"),
                         chain[T.SID].short_ids)

    def test_the_superseded_authorization_stops_being_live(self):
        """The point of the edge. Two live P2s is what wedges the chain."""
        chain, refusal = _resolve(_chain("P2S", "P2"))
        self.assertIsNone(refusal, refusal)
        self.assertEqual(1, len(chain[T.SID].live_authorizations))

    def test_the_contract_now_carries_the_edge_both_ways(self):
        self.assertIn("P2S", sc.EVENTS["P2"].successors)
        self.assertIn("P2", sc.EVENTS["P2S"].predecessors)
        self.assertTrue(sc.transition_allowed("P2", "P2S"))

    def test_the_transition_function_names_it_distinctly(self):
        """`prestart_reauthorize` is not `pre_start_failure`. One says no
        attempt was made; the other says one failed. Collapsing them is how
        a manufactured F1 gets in."""
        self.assertEqual("P2S", sr.plan_next_short_id(
            "P2", outcome="prestart_reauthorize"))
        self.assertEqual("F1", sr.plan_next_short_id(
            "P2", outcome="pre_start_failure"))


class TestItOpensNothingElse(unittest.TestCase):
    """The half that matters. Each of these must still refuse."""

    def test_the_old_path_still_works(self):
        chain, refusal = _resolve(_chain("F1", "P2S", "P2",
                                         reason_code="PRESTART_FIX"))
        self.assertIsNone(refusal, refusal)
        self.assertEqual(("P1", "P2", "F1", "P2S", "P2"),
                         chain[T.SID].short_ids)

    def test_a_different_reason_code_still_needs_its_F1(self):
        """Condition 5. `PRESTART_FIX` is `Reg`'s default, so every chain
        the producer suite already builds keeps the old requirement."""
        _chains, refusal = _resolve(_chain("P2S", "P2",
                                           reason_code="PRESTART_FIX"))
        self.assertIsNotNone(refusal)
        self.assertEqual("p2s_without_preceding_f1", refusal.code)

    def test_an_empty_reason_code_does_not_open_it(self):
        """It refuses EARLIER, at the field check -- named here because
        a test asserting only "some refusal" would look identical to one
        that proved the edge check saw it."""
        _chains, refusal = _resolve(_chain("P2S", "P2", reason_code=""))
        self.assertIsNotNone(refusal)
        self.assertEqual("field_value_empty", refusal.code)

    def test_p2s_after_p3_is_still_its_own_refusal(self):
        """Conditions 1 and 2 at the chain level: once a run has started
        the supplement is past pre-start, and this edge may not be used."""
        _chains, refusal = _resolve(_chain("P3", "P2S"))
        self.assertIsNotNone(refusal)
        self.assertEqual("p2s_after_p3", refusal.code)

    def test_a_p2s_with_no_p2_to_supersede_still_refuses(self):
        """MEASURED, and the measurement changed what this test claims.
        It was written as "P1 -> P2S is still refused" -- true, but not
        what happens: with no P2 in the chain there is no supersede
        target, so `supersedes_event_sequence` fails its own field check
        and the row never reaches the edge code at all.

        Which means the `prev == "P2"` half of the exception cannot be
        violated THROUGH a chain: reaching a P2S with a valid target and
        no P3 leaves only P2 and F1 as possible predecessors. That half
        is proved on the predicate below instead -- and this test says so
        rather than passing for a reason it does not name.
        """
        reg = T.Reg()
        reg.commit[T.SID] = T.C1
        reg.add("P1", sid=T.SID)
        reg.add("P2S", sid=T.SID, fields={"reason_code": RULED})
        _chains, refusal = _resolve(reg.text())
        self.assertIsNotNone(refusal)
        self.assertEqual("integer_field_below_minimum", refusal.code)

    def test_the_new_edge_does_not_bypass_the_commit_change_requirement(self):
        """Condition 4, across the new edge. A supersede whose successor
        commit equals the superseded one records no change at all, and the
        existing code must still say so rather than the edge swallowing it."""
        _chains, refusal = _resolve(
            _chain("P2S", extra={"successor_authorized_commit": T.C1}))
        self.assertIsNotNone(refusal)
        self.assertEqual("p2s_successor_equals_superseded", refusal.code)

    def test_the_new_edge_does_not_bypass_the_target_checks(self):
        """Condition 6, across the new edge. `supersedes_event_sequence`
        must still land on the P2 it claims."""
        _chains, refusal = _resolve(
            _chain("P2S", extra={"supersedes_event_sequence": "99"}))
        self.assertIsNotNone(refusal)
        self.assertIn("p2s", refusal.code)


class TestThePredicateItself(unittest.TestCase):
    """Two of the six cannot be reached through a chain, and saying so is
    better than building a chain that pretends they can.

    `same_id_reauthorization` is a `_YES_FIELDS` field, so the parser
    refuses any other value before the walk ever runs; and a chain with an
    earlier P3 but a P2 immediately before the P2S is not constructible,
    because returning to P2 after P3 requires a P2S or a T1 in between and
    T1 files under the successor id. Both conditions are still CHECKED --
    they are checked here, on the predicate, rather than asserted nowhere.
    """

    class _Ev:
        def __init__(self, **fields):
            self.fields = fields

    def _ev(self, **over):
        base = {"reason_code": RULED, "same_id_reauthorization": "YES"}
        base.update(over)
        return self._Ev(**base)

    def test_it_admits_the_ruled_shape(self):
        self.assertTrue(sreg._is_prestart_reauthorization(
            "P2", self._ev(), started=False))

    def test_a_started_run_closes_it(self):
        self.assertFalse(sreg._is_prestart_reauthorization(
            "P2", self._ev(), started=True))

    def test_same_id_reauthorization_must_be_yes(self):
        self.assertFalse(sreg._is_prestart_reauthorization(
            "P2", self._ev(same_id_reauthorization="NO"), started=False))

    def test_it_admits_no_predecessor_but_p2(self):
        for prev in ("P1", "P3", "F1", "F2", "T1", "P2S", ""):
            with self.subTest(prev=prev):
                self.assertFalse(sreg._is_prestart_reauthorization(
                    prev, self._ev(), started=False))

    def test_a_missing_field_does_not_crash_it_open(self):
        self.assertFalse(sreg._is_prestart_reauthorization(
            "P2", self._Ev(), started=False))


if __name__ == "__main__":
    unittest.main()
