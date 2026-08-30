"""`REVIEWED_SET_UNCHANGED_SINCE=<sha>` must be TRUE, not asserted.

ROUND 4 MEDIUM, and it is the plainest instance of this project's recurring
defect I have produced. The round-4 packet declared

    REVIEWED_SET_UNCHANGED_SINCE=dba55d9

and then `eab7992` -- my own next commit, the one that hardened the
contract -- touched `tests/test_resolve_partial_path_contract.py`, which is
IN the reviewed set. Every SHA-256 in the packet's table was correct. The
RANGE CLAIM was false.

A reviewer is told to trust that line. It is the thing that lets them stop
worrying about what moved. Writing it by hand and hoping is the same shape
as every other finding tonight: **a stated property wider than what is
true**.

WHAT THIS CHECKS. For every prompt whose claim is still LIVE -- ISSUED, or
PREPARED_NOT_ISSUED -- the declared commit must actually have no commits
after it touching the files that prompt puts under review. Derived from
git, not from the prompt's own say-so.

WHAT IT DELIBERATELY DOES NOT CHECK. A RETURNED prompt: its claim was true
when it was live, and the repository has moved on since by design. Holding
finished deliveries to a live claim would train people to ignore this.

A PLACEHOLDER is allowed and is the recommended state before issue -- the
pin is a fact about the moment of issue, so it should be filled then and
verified here, not written days early and hoped over.
"""

import json
import re
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OPS = REPO / "ops"

PIN = re.compile(r"REVIEWED_SET_UNCHANGED_SINCE=([0-9a-f]{7,40})\b")
STATUS = re.compile(r"DELIVERY_STATUS=([A-Z_]+)")
#: A transport-table row, in the format the repository already uses:
#: `| <sha256> | <bytes> | \`<path>\` |`. My first draft invented a
#: different shape (`| reference | \`path\` | ...`) and then reported that
#: a correctly-formed prompt "lists no reference file" -- a guard written
#: against a convention I made up rather than the one in use.
ROW = re.compile(r"^\|\s*`?[0-9a-fA-F]{64}`?\s*\|\s*\d+\s*\|\s*`([^`]+)`",
                 re.M)

LIVE = {"ISSUED", "PREPARED_NOT_ISSUED"}


def _prompts():
    return sorted(OPS.glob("PROMPT_*.md"))


def _git(*args):
    out = subprocess.run(["git", "-C", str(REPO), *args],
                         capture_output=True, encoding="utf-8",
                         errors="replace")
    return out.returncode, (out.stdout or "")


class TestALiveRangeClaimIsTrue(unittest.TestCase):

    def test_no_live_prompt_claims_a_range_that_has_moved(self):
        offenders = []
        for path in _prompts():
            text = path.read_text(encoding="utf-8")
            status = STATUS.search(text)
            if not status or status.group(1) not in LIVE:
                continue
            pin = PIN.search(text)
            if not pin:
                # ROUND 5 MEDIUM, first false green: this used to `continue`
                # for ANY prompt without a pin, including an ISSUED one --
                # so an issued delivery with no pin passed WITHOUT A SINGLE
                # GIT CALL. A placeholder is only legitimate before issue.
                if status.group(1) == "ISSUED":
                    offenders.append("%s: ISSUED with no pin at all -- the "
                                     "line a reviewer is told to trust is "
                                     "absent, and nothing was checked"
                                     % path.name)
                continue
            listed = ROW.findall(text)
            # ROUND 5 MEDIUM, second false green: this used to FILTER the
            # table by `.exists()`, so a reviewed path that had been DELETED
            # was silently dropped and never queried. A missing reviewed
            # file is the loudest possible change, not a row to skip.
            missing = [f for f in listed if not (REPO / f).exists()]
            if missing:
                offenders.append("%s: its table lists reviewed paths that do "
                                 "not exist: %s" % (path.name, missing))
                continue
            files = listed
            if not files:
                offenders.append("%s: declares a pin but its table lists no "
                                 "reference file at all" % path.name)
                continue
            code, out = _git("log", "--format=%h %s",
                             "%s..HEAD" % pin.group(1), "--", *files)
            if code != 0:
                offenders.append("%s: pin %s is not a commit"
                                 % (path.name, pin.group(1)))
                continue
            touched = [line for line in out.splitlines() if line.strip()]
            if touched:
                offenders.append("%s: %s..HEAD touched its reviewed set:\n"
                                 "      %s"
                                 % (path.name, pin.group(1),
                                    "\n      ".join(touched[:4])))
        self.assertEqual(
            [], offenders,
            "a LIVE prompt's range claim is false: %s\n\nThe reviewer is "
            "told to trust that line. Fill the pin at ISSUE time and let "
            "this verify it -- writing it by hand days early is how round 4 "
            "got a MEDIUM." % offenders)

    def test_a_returned_prompt_is_deliberately_exempt(self):
        """Stated so the exemption is a decision rather than an oversight:
        a finished delivery's claim was true when it was live, and the tree
        has moved since by design."""
        returned = [p.name for p in _prompts()
                    if "DELIVERY_STATUS=RETURNED" in p.read_text(
                        encoding="utf-8")]
        self.assertTrue(returned,
                        "no RETURNED prompt exists, so this exemption "
                        "currently protects nothing and should be removed "
                        "with its rationale")

    def test_the_scan_found_prompts_at_all(self):
        """Vacuity against a glob typo. The OTHER vacuity worry -- every
        prompt being RETURNED, so the check above passes over nothing -- is
        covered by `TestTheCheckCanActuallyFail`, which drives the mechanism
        over a real file and a real stale pin."""
        self.assertGreaterEqual(len(_prompts()), 3)

    def test_a_live_prompt_exists_EXACTLY_WHEN_the_register_is_armed(self):
        """REPLACED an assertion that a live prompt always exists, 2026-08-30.

        It went red the moment round 6 returned and its register entries were
        cleared -- correctly, because between rounds NOTHING is in flight and
        no prompt is live. "There is always a live review" is simply false.

        What is always true is the correspondence, and it is the stronger
        claim: a review is in flight exactly when its delivery says so and its
        artifacts are frozen. Either half without the other is a real defect
        -- an ISSUED prompt with an empty register means a reviewer is holding
        bytes nothing is protecting, and an armed register with no live prompt
        means the freeze outlives the review and the next repair collides
        with it. Both have happened here."""
        # ISSUED only, NOT the whole LIVE set. Getting this wrong is what
        # the guard's first version did, within the hour: it keyed on LIVE,
        # which includes PREPARED_NOT_ISSUED, and went red the moment a
        # round-7 packet was prepared. A PREPARED packet is CORRECTLY
        # unarmed -- "finish the edits, commit, THEN arm" is the ordering
        # this repository learned twice the hard way, so a prepared-and-
        # unarmed prompt is the rule being followed, not broken.
        issued = sorted(p.name for p in _prompts()
                        if "DELIVERY_STATUS=ISSUED" in
                        p.read_text(encoding="utf-8"))
        register = json.loads(
            (OPS / "ARTIFACTS_UNDER_REVIEW.json").read_text(encoding="utf-8"))
        armed = sorted({e["review_id"] for e in register["under_review"]})
        self.assertEqual(
            bool(issued), bool(armed),
            "ISSUED prompts %s but armed reviews %s -- a review is in flight "
            "exactly when its delivery says ISSUED and its artifacts are "
            "frozen; either half alone is the defect" % (issued, armed))

    def test_the_round4_packet_records_the_correction(self):
        """The miss itself stays on record; a fix that erased it would hide
        that the guard was born from a real false claim."""
        text = (OPS / "PROMPT_C_BUILD_2_WORDING_SOL_ROUND4.md").read_text(
            encoding="utf-8")
        self.assertIn("错的是 range 声称", text)
        self.assertIn("test_a_prompts_range_claim_actually_holds", text)


class TestTheCheckCanActuallyFail(unittest.TestCase):
    """A guard nobody has seen fail is a guard nobody knows works."""

    def test_a_stale_pin_over_a_real_file_is_detected(self):
        touched = _git("log", "--format=%h", "-1", "--",
                       "tests/test_resolve_partial_path_contract.py")[1].strip()
        self.assertTrue(touched, "the probe file has no history")
        older = _git("rev-parse", "%s~1" % touched)[1].strip()
        code, out = _git("log", "--format=%h", "%s..HEAD" % older, "--",
                         "tests/test_resolve_partial_path_contract.py")
        self.assertEqual(0, code)
        self.assertTrue(
            [line for line in out.splitlines() if line.strip()],
            "a pin one commit BEFORE a known change reports nothing "
            "touched, so the detection above cannot fire at all")


if __name__ == "__main__":
    unittest.main()
