"""Aaron's 2026-08-30 ruling: the C_BUILD_2 wording review stops at 8 rounds.

    > 修复这个环节记得以后不超过八次，如果到了八次就按最好的方式执行就行

WHY THIS IS A TEST AND NOT A NOTE. A cap that lives only in a document is a
cap that gets forgotten at 02:00 on round nine, when the next HOLD arrives
and issuing another round is the obvious next move. This repository's habit
is to make a rule fire rather than describe it, and a limit on my own
behaviour is the kind of rule that needs it most.

WHERE THE NUMBER COMES FROM. It is READ OUT OF THE RULING, not spelled here.
Same reason `ERROR_CLASS_OF_PRODUCER_REFUSAL` is derived from the class
rather than typed: a hand-copied constant is a second source of truth, and
the two drift. Aaron edits the ruling, the guard follows. The ruling goes
missing, the guard goes red -- silence is never taken for permission.

THE SECOND HALF, and the one I would actually skip. Reaching the cap is a
decision to STOP ITERATING; it is not a finding that the residuals closed.
Whatever is still standing at round eight goes out standing. So at the cap
the packet must mark those residuals ACCEPTED_BY_CAP -- not ACCEPTED, which
would claim someone judged the cost acceptable. Writing "accepted" there
would be using Aaron's time limit to dress up the technical state, which is
the exact defect shape this review has now found nine times over:
A CLAIM WIDER THAN THE FACT.
"""

import re
import tempfile
import unittest
from pathlib import Path

OPS = Path(__file__).resolve().parent.parent / "ops"
RULING = OPS / "OWNER_DECISIONS_2026-08-30.md"
#: Round 1 predates the numbering, so its file carries no digit.
FIRST_ROUND_STEM = "PROMPT_C_BUILD_2_WORDING_SOL_REVIEW"
GLOB = "PROMPT_C_BUILD_2_WORDING_SOL_*.md"
CAP_LINE = re.compile(r"^CAP\s+(\d+)\s*轮\s*$", re.M)


def declared_cap(ruling=RULING):
    """The cap AS RULED. Absent or unreadable is a failure, never a default.

    A missing ruling must not degrade into "no cap": that is the
    could-not-look / nothing-is-there collapse this repository refuses
    everywhere else."""
    if not ruling.is_file():
        raise AssertionError(
            "%s is missing; the round cap is Aaron's ruling and this guard "
            "will not invent one" % ruling.name)
    found = CAP_LINE.findall(ruling.read_text(encoding="utf-8"))
    if len(found) != 1:
        raise AssertionError(
            "expected exactly one CAP <n> line in %s, found %d"
            % (ruling.name, len(found)))
    return int(found[0])


def rounds_present(ops=OPS):
    """Round numbers that exist on disk, sorted. The DIRECTORY is the universe.

    Nothing is declared and then looked for -- the shape
    `supplement_bytes_snapshot` uses, and for the same reason: a count driven
    by a list can be lowered by editing the list."""
    numbers = []
    for path in sorted(ops.glob(GLOB)):
        if path.stem == FIRST_ROUND_STEM:
            numbers.append(1)
            continue
        match = re.fullmatch(r"PROMPT_C_BUILD_2_WORDING_SOL_ROUND(\d+)",
                             path.stem)
        if match is None:
            raise AssertionError(
                "%s matches the review-prompt glob but not the naming this "
                "guard counts by; rename it or widen the guard, but do not "
                "leave a round it cannot see" % path.name)
        numbers.append(int(match.group(1)))
    return sorted(numbers)


def cap_violations(ops=OPS, ruling=RULING):
    """Every way the round series can be wrong. Empty list means compliant."""
    cap, rounds = declared_cap(ruling), rounds_present(ops)
    problems = []
    if rounds != list(range(1, len(rounds) + 1)):
        problems.append(
            "the round numbers are not contiguous from 1: %r -- a gap means "
            "a round is missing or misnamed, so the count is not the number "
            "of rounds actually run" % (rounds,))
    if len(rounds) > cap:
        problems.append(
            "%d rounds exist but Aaron capped this review at %d "
            "(OD-1, 2026-08-30). At the cap the wording ships as it stands; "
            "a further round is not mine to open." % (len(rounds), cap))
    if len(rounds) == cap and rounds:
        final = ops / ("PROMPT_C_BUILD_2_WORDING_SOL_ROUND%d.md" % rounds[-1])
        body = final.read_text(encoding="utf-8") if final.is_file() else ""
        if "ACCEPTED_BY_CAP" not in body:
            problems.append(
                "round %d is the cap, so every residual still standing goes "
                "out standing and %s must mark them ACCEPTED_BY_CAP. Marking "
                "them ACCEPTED instead would claim someone judged the cost "
                "acceptable, when what actually happened is that the rounds "
                "ran out." % (rounds[-1], final.name))
    return problems


class TestTheCapIsRespected(unittest.TestCase):

    def test_no_more_rounds_exist_than_aaron_allowed(self):
        self.assertEqual([], cap_violations())

    def test_the_cap_is_read_from_the_ruling_not_from_this_file(self):
        self.assertEqual(8, declared_cap(),
                         "the ruling says something else; that is the "
                         "authority, so change the expectation here only "
                         "after reading why it moved")

    def test_the_rounds_on_disk_are_the_rounds_i_think_they_are(self):
        rounds = rounds_present()
        self.assertEqual(list(range(1, len(rounds) + 1)), rounds)
        self.assertLessEqual(len(rounds), declared_cap())


class TestTheGuardIsNotVACUOUS(unittest.TestCase):
    """Every clause above passes today. So each one is exercised against a
    directory built to break it -- otherwise a green result here is equally
    consistent with the guard checking nothing at all."""

    def _fake(self, cap_text, names):
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        root = Path(holder.name)
        (root / "R.md").write_text("```\n%s\n```\n" % cap_text,
                                   encoding="utf-8")
        for name in names:
            (root / name).write_text("body\n", encoding="utf-8")
        return root, root / "R.md"

    def _names(self, n):
        return ["%s.md" % FIRST_ROUND_STEM] + [
            "PROMPT_C_BUILD_2_WORDING_SOL_ROUND%d.md" % i
            for i in range(2, n + 1)]

    def test_a_ninth_round_is_reported(self):
        root, ruling = self._fake("CAP 8 轮", self._names(9))
        self.assertTrue(any("capped this review at 8" in p
                            for p in cap_violations(root, ruling)))

    def test_the_eighth_round_without_the_marking_is_reported(self):
        root, ruling = self._fake("CAP 8 轮", self._names(8))
        self.assertTrue(any("ACCEPTED_BY_CAP" in p
                            for p in cap_violations(root, ruling)))

    def test_the_eighth_round_WITH_the_marking_passes(self):
        """That clause must not simply refuse round eight -- round eight is
        allowed. It is round nine that is not."""
        root, ruling = self._fake("CAP 8 轮", self._names(8))
        (root / "PROMPT_C_BUILD_2_WORDING_SOL_ROUND8.md").write_text(
            "residual X: ACCEPTED_BY_CAP\n", encoding="utf-8")
        self.assertEqual([], cap_violations(root, ruling))

    def test_a_gap_in_the_series_is_reported(self):
        names = [n for n in self._names(5) if not n.endswith("ROUND3.md")]
        root, ruling = self._fake("CAP 8 轮", names)
        self.assertTrue(any("not contiguous" in p
                            for p in cap_violations(root, ruling)))

    def test_a_missing_ruling_refuses_rather_than_defaulting(self):
        root, ruling = self._fake("CAP 8 轮", self._names(3))
        ruling.unlink()
        with self.assertRaises(AssertionError) as caught:
            cap_violations(root, ruling)
        self.assertIn("will not invent one", str(caught.exception))

    def test_an_unparseable_cap_refuses_rather_than_defaulting(self):
        root, ruling = self._fake("CAP eight rounds", self._names(3))
        with self.assertRaises(AssertionError):
            cap_violations(root, ruling)

    def test_a_round_file_this_guard_cannot_count_is_reported(self):
        root, ruling = self._fake("CAP 8 轮", self._names(3))
        (root / "PROMPT_C_BUILD_2_WORDING_SOL_FINAL.md").write_text(
            "x", encoding="utf-8")
        with self.assertRaises(AssertionError) as caught:
            cap_violations(root, ruling)
        self.assertIn("do not leave a round it cannot see",
                      str(caught.exception))

    def test_a_compliant_directory_really_passes(self):
        root, ruling = self._fake("CAP 8 轮", self._names(6))
        self.assertEqual([], cap_violations(root, ruling))


if __name__ == "__main__":
    unittest.main()
