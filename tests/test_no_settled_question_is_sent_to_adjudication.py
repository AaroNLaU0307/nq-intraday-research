"""A decision packet must say where it checked the question was still open.

WHAT HAPPENED, 2026-08-30. `ops/DECISION_PACKET_FOUR_OPEN_2026-08-29.md`
asked an adjudication seat to rule on the runtime directory-grant form.
Aaron had already ruled it -- `ops/OWNER_DECISIONS_2026-08-29.md` §5, in as
many words, option 乙 -- and `ops/DIRECTORY_CREATION_GRANTS.md` said
"Aaron 尚未裁", which was simply false.

The seat recognised it and refused to re-rule. That was the seat working,
not the process working. Had it ruled differently, a subagent's answer
would have silently overridden an owner decision.

WHAT THIS GUARD CAN AND CANNOT DO, stated plainly because a guard that
oversells itself is the defect this repository keeps producing.

  CANNOT  detect that a question is semantically the same as a ruling
          already recorded. That needs judgment, and a test that pretended
          to have it would be worse than nothing.

  CAN     refuse a packet that does not SAY where it looked. The failure
          above was not a hard judgment call -- the ruling was in the file
          the packet's own subject matter pointed at, and nobody looked.
          Forcing the citation makes the looking happen and leaves a trace
          the next reader can check in seconds.

So this is a PROCESS guard. It asserts the check was performed and
recorded, not that its conclusion was right.
"""

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OPS = REPO / "ops"

#: The citation a packet must carry per question.
CITATION = re.compile(r"已核对未裁[：:]\s*(\S+)")

#: Packets written before this convention existed. Each is listed with what
#: is known about it rather than waved through -- an allowlist whose entries
#: carry no reason is how a guard becomes decoration.
LEGACY_PACKETS = {
    "DECISION_PACKET_FOUR_OWNER_ITEMS.md":
        "2026-08-27, RETURNED and ruled. Predates the convention.",
    "DECISION_PACKET_ND2_ND3.md":
        "quarantined subtree; outcome-carrying, not opened.",
    "DECISION_PACKET_SCOPE_AND_BOUNDARY.md":
        "2026-08-28, predates the convention.",
    "DECISION_PACKET_N00_AND_ND1.md":
        "the N00/ND1 packet; predates the convention.",
    "DECISION_PACKET_FOUR_OPEN_2026-08-29.md":
        "THE ONE THAT FAILED. Kept here rather than fixed: its question 2 "
        "was already ruled, and the packet now carries an appended "
        "correction saying so. Rewriting it to pass this test would erase "
        "the evidence that the convention was born from a real miss.",
}


def _packets():
    return sorted(p for p in OPS.glob("DECISION_PACKET_*.md"))


class TestEveryPacketSaysWhereItLooked(unittest.TestCase):

    def test_each_question_cites_where_it_was_checked_still_open(self):
        offenders = []
        for path in _packets():
            if path.name in LEGACY_PACKETS:
                continue
            text = path.read_text(encoding="utf-8")
            questions = re.findall(r"^## 第 .+ 件", text, re.M)
            citations = CITATION.findall(text)
            if len(citations) < len(questions):
                offenders.append(
                    "%s: %d question(s), %d 已核对未裁 citation(s)"
                    % (path.name, len(questions), len(citations)))
        self.assertEqual(
            [], offenders,
            "a decision packet does not say where it checked each question "
            "was still open: %s\n\nWrite `已核对未裁：<file> §<n>` under each "
            "question. This guard cannot tell you whether a question is "
            "settled -- it can only refuse a packet where nobody looked."
            % offenders)

    def test_every_cited_file_exists(self):
        missing = []
        for path in _packets():
            for cited in CITATION.findall(path.read_text(encoding="utf-8")):
                target = REPO / cited.strip("`。，,")
                if not target.exists():
                    missing.append("%s -> %s" % (path.name, cited))
        self.assertEqual([], missing,
                         "a packet cites a file that does not exist: %s"
                         % missing)

    def test_the_scan_found_packets_at_all(self):
        """Vacuity. A glob typo would report zero offenders out of zero."""
        self.assertGreaterEqual(len(_packets()), 3)

    def test_the_legacy_allowlist_names_only_real_files(self):
        """An entry for a file that no longer exists is an exemption
        protecting nothing, and it hides that the list was never revisited."""
        names = {p.name for p in _packets()}
        # the quarantined one is not reachable from here by design
        stale = sorted(n for n in LEGACY_PACKETS
                       if n not in names and "ND2_ND3" not in n)
        self.assertEqual([], stale, "stale allowlist entries: %s" % stale)

    def test_every_legacy_entry_carries_a_reason(self):
        for name, reason in LEGACY_PACKETS.items():
            with self.subTest(packet=name):
                self.assertGreater(len(reason), 30,
                                   "%s is exempted with no reason" % name)


class TestTheMissThatCausedThisIsStillOnRecord(unittest.TestCase):
    """The correction must survive, in both places it belongs."""

    def test_the_grants_ledger_carries_the_correction(self):
        text = (OPS / "DIRECTORY_CREATION_GRANTS.md").read_text(
            encoding="utf-8")
        self.assertIn("订正-ALREADY-RULED-2026-08-30", text)
        self.assertIn("「Aaron 尚未裁」是假的", text)

    def test_the_packet_carries_the_withdrawal(self):
        text = (OPS / "DECISION_PACKET_FOUR_OPEN_2026-08-29.md").read_text(
            encoding="utf-8")
        self.assertIn("撤回：已裁", text)
        self.assertIn("原文保留于下，不修改", text)

    def test_the_ruling_it_missed_is_where_the_correction_says(self):
        """The citation, checked. A correction pointing at nothing would be
        the same defect one level up."""
        text = (OPS / "OWNER_DECISIONS_2026-08-29.md").read_text(
            encoding="utf-8")
        self.assertIn("乙：运行时刻再签一份", text)
        self.assertIn("形制已定（乙）", text)


if __name__ == "__main__":
    unittest.main()
