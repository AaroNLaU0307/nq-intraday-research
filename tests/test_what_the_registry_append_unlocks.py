"""The measurement behind `ops/MEASURED_WHAT_THE_REGISTRY_APPEND_UNLOCKS.md`.

A recommendation to Aaron that lives only in a prose document is a
recommendation nobody can recheck. Every number in that record is produced
here, from synthetic registry text, so the advice can be falsified by
running the suite rather than by trusting me.

WHY IT EXISTS AT ALL. The previous grant (A1, directory creation) was
described to Aaron as unblocking a gate. Measured afterwards: it unblocks
none. So this time the measurement came first, and it says the same thing
about P1 -- appending a proposal row changes ZERO gates. What it does is
make P2 legal, which is a different and real reason.

NOTHING HERE TOUCHES THE REAL REGISTRY. Every chain is resolved from a
string built in memory.
"""

import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tests"))

import test_mc_supplement_registry as T           # noqa: E402
from itsf import contracts, guards                # noqa: E402
from itsf.mc import supplement_contract as sc     # noqa: E402
from itsf.mc import supplement_registry as sreg   # noqa: E402
from itsf.mc import supplement_runner as sr       # noqa: E402

RECORD = REPO / "ops" / "MEASURED_WHAT_THE_REGISTRY_APPEND_UNLOCKS.md"


def _head():
    out = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"],
                         capture_output=True, text=True)
    return out.stdout.strip()


def _ctx(text, chain, head):
    return sr.GateContext(
        supplement_id=T.SID, head_commit=head, registry_text=text,
        runs_root=Path(contracts.RULED_RUNS_ROOT),
        archive_root=Path(contracts.RULED_ARCHIVE_ROOT),
        repo_dirty_paths=(), g9_flag=Path(guards.G9_FLAG),
        second_copy_flag=Path(guards.SECOND_COPY_FLAG),
        frozen_hashes_ok=True, chain=chain, utc_stamp="20260829T000000Z",
        # QROS-CF I1: the identity gate refuses an unmeasured pin
        environment_pinned=True, environment_detail="test context")


def _verdicts(text, head, stage="A_PRECHECK"):
    chain = sreg.resolve_supplement_chain(text, T.SID)
    ctx = _ctx(text, chain, head)
    out = {}
    for name in sc.GATE_TABLE[stage]:
        try:
            sr.GATES[name](ctx)
            out[name] = "PASS"
        except Exception:                                     # noqa: BLE001
            out[name] = "REFUSE"
    return out


def _registry(*rows, head=None, root=None):
    T.ROOT = root or str(contracts.RULED_RUNS_ROOT)
    reg = T.Reg()
    reg.commit[T.SID] = head
    for short in rows:
        reg.add(short, sid=T.SID)
    return reg.text()


class TestAppendingP1UnlocksNoGate(unittest.TestCase):
    """§1 of the record. The headline, and the reason the recommendation
    is 'not yet'."""

    def test_the_verdicts_are_identical_with_and_without_a_P1(self):
        head = _head()
        empty = _verdicts("", head)
        with_p1 = _verdicts(_registry("P1", head=head), head)
        self.assertEqual(
            empty, with_p1,
            "a P1 row changed a gate verdict, which would make the "
            "recommendation in %s wrong" % RECORD.name)

    def test_and_five_gates_do_change_once_P2_is_there(self):
        """The premise: the comparison above is only meaningful if these
        gates CAN move. They move on P2 -- Aaron's row, not mine."""
        head = _head()
        empty = _verdicts("", head)
        with_p2 = _verdicts(_registry("P1", "P2", head=head), head)
        moved = sorted(k for k in empty if empty[k] != with_p2[k])
        self.assertEqual(
            ["authorization_actor", "authorized_commit_matches_head",
             "live_authorization_unique", "output_root_declared",
             "output_root_structure"], moved)
        for gate in moved:
            with self.subTest(gate=gate):
                self.assertEqual("REFUSE", empty[gate])
                self.assertEqual("PASS", with_p2[gate])

    def test_a_correct_P1_plus_P2_opens_all_thirteen(self):
        head = _head()
        verdicts = _verdicts(_registry("P1", "P2", head=head), head)
        self.assertEqual({"PASS"}, set(verdicts.values()),
                         "still refusing: %s"
                         % sorted(k for k, v in verdicts.items()
                                  if v != "PASS"))


class TestP1IsStructurallyRequiredAnyway(unittest.TestCase):
    """§2. The real reason to append it, as opposed to the assumed one."""

    def test_a_P2_with_no_preceding_P1_poisons_the_chain(self):
        head = _head()
        chain = sreg.resolve_supplement_chain(
            _registry("P2", head=head), T.SID)
        self.assertIn("chain_does_not_start_at_proposal", chain.problem)
        self.assertEqual(0, len(chain.live_authorizations))

    def test_P1_then_P2_resolves_cleanly(self):
        head = _head()
        chain = sreg.resolve_supplement_chain(
            _registry("P1", "P2", head=head), T.SID)
        self.assertEqual("", chain.problem)
        self.assertEqual(1, len(chain.live_authorizations))
        self.assertEqual(("P1", "P2"), chain.short_ids)


class TestP1DoesNotDecayButP2Does(unittest.TestCase):
    """§3. This is what makes 'wait' cost nothing."""

    def test_P1_carries_no_commit_as_a_required_field(self):
        self.assertNotIn(
            "authorized_commit_40hex", sc.EVENTS["P1"].required_fields)
        self.assertFalse(any("commit" in f
                             for f in sc.EVENTS["P1"].required_fields))

    def test_P2_does_carry_one(self):
        self.assertIn("authorized_commit_40hex",
                      sc.EVENTS["P2"].required_fields)

    def test_a_P1_written_at_an_older_commit_still_supports_a_new_P2(self):
        old, new = "1" * 40, "2" * 40
        T.ROOT = str(contracts.RULED_RUNS_ROOT)
        reg = T.Reg()
        reg.commit[T.SID] = old
        reg.add("P1", sid=T.SID)
        reg.commit[T.SID] = new
        reg.add("P2", sid=T.SID)
        chain = sreg.resolve_supplement_chain(reg.text(), T.SID)
        self.assertEqual("", chain.problem)
        self.assertEqual(
            new, chain.live_authorizations[0].authorized_commit,
            "the live authorization must take the P2 commit, not the P1 one")


class TestEvenWithBothRowsItStillCannotRun(unittest.TestCase):
    """§4. The part that keeps the recommendation honest: this is not the
    last thing standing between here and a real run."""

    def test_B_DERIVE_still_refuses_every_gate(self):
        head = _head()
        verdicts = _verdicts(_registry("P1", "P2", head=head), head,
                             stage="B_DERIVE")
        self.assertEqual({"REFUSE"}, set(verdicts.values()))

    def test_C_BUILD_still_refuses_every_gate_because_they_are_stubs(self):
        head = _head()
        verdicts = _verdicts(_registry("P1", "P2", head=head), head,
                             stage="C_BUILD")
        self.assertEqual({"REFUSE"}, set(verdicts.values()))

    def test_the_production_entry_refuses_when_nothing_authorises_it(self):
        """REWRITTEN 2026-09-05. It used to drive this off the REAL ledger
        and assert the ledger had no live authorization. Aaron signed the
        P2 at row 15 and the assertion became false — while the property,
        "no live authorization means no run", never stopped holding.

        Everything else in this module resolves from a string built in
        memory, exactly so the measurement does not depend on what the real
        ledger says this week. This test was the one exception and it is no
        longer one: the refusal is driven through the resolver seam
        `run_supplement_production` documents for this purpose.
        """
        def _nothing_authorises(_text, supplement_id):
            return sreg.resolve_supplement_chain("", supplement_id)

        with self.assertRaises(Exception) as caught:
            sr.run_supplement_production(resolver=_nothing_authorises)
        self.assertIn("0 live SUPPLEMENT_EXECUTION_AUTHORIZED",
                      str(caught.exception))


class TestTheRecordAgreesWithTheMeasurement(unittest.TestCase):
    """A prose recommendation that drifts from its own evidence is worse
    than no recommendation."""

    def test_the_record_exists_and_states_the_zero(self):
        text = RECORD.read_text(encoding="utf-8")
        self.assertIn("追加 P1 改变的门数：0", text)
        self.assertIn("chain_does_not_start_at_proposal", text)
        self.assertIn("现在别给", text)

    def test_the_real_registry_carries_no_supplement_row_yet(self):
        """The measurement's own premise, and the thing that would make
        every table above describe the wrong world."""
        registry = (REPO / "ops" / "TRIAL_REGISTRY.md").read_text(
            encoding="utf-8")
        self.assertNotIn(sc.EVENTS["P1"].token, registry)
        self.assertNotIn(sc.EVENTS["P2"].token, registry)


if __name__ == "__main__":
    unittest.main()
