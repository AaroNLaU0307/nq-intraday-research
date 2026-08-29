"""Every approval in the ratification record, not just the first one.

ROUND-2 HIGH. The reviewer wrote:

    现有 premise test 不会在「新批准值追加、代码仍旧」时变红，因此判据 (4)
    所称的陈旧化保护尚未成立。

REPRODUCED, and it was worse than the finding described. Appending a
fabricated superseding approval left all 34 guards green — and then the
enumeration showed **superseding approvals already existed**:

    R1  0a08319a…  2026-08-20  ops/DECISION_PACKET_N00_AND_ND1.md
    R2  a3d40b7c…  2026-08-23  R1_STATUS=SUPERSEDED_BY_R2_FOR_P3_ONLY
    R3  d40ad864…  2026-08-27  R2_STATUS=SUPERSEDED_BY_R3_FOR_P3_AND_F3_ONLY

§13.2 closed the ruling's falsifier against R1's bytes alone, and nothing
noticed there were two later approvals. The anchoring turned out to be
sound — all three carry byte-identical values for the three fields the
wording anchors on — but that was LUCK, not a guarantee. Nothing checked.

WHAT THIS FILE DOES

    1. reconstructs EVERY approved preimage by hash, from the commit each
       approval binds, wherever in that tree it lives (R3's is in a
       different file from R1's and R2's — found by hash, not by guess)
    2. asserts the three anchored values are identical across every
       PROFILE approval, so a future one that changes any of them goes red
       HERE rather than being discovered by a reviewer
    3. asserts none of them constrains WHEN the gate runs — the ruling's
       falsifier, now checked against every approval instead of the oldest
    4. FAILS CLOSED when an unexamined approval appears, because that is
       exactly the state this file exists to prevent

AND THEN IT HAPPENED TO THIS FILE. The first version enumerated three
approvals and called itself "every approval". Drafting the round-3 prompt
turned up a FOURTH approved artefact — `APPROVED_CR1_GRAMMAR_SHA256`, the
CR1 event grammar, approved as its own canonical block and bound into R3
by a single line. The detection pattern was `APPROVED_PROFILE_SHA256`,
which could not see it.

So the file written to stop me anchoring on a subset was itself anchored
on a subset, for one day. The pattern is now any `APPROVED_*SHA256`, and
every kind must declare in KIND_SCOPE which checks apply to it.
"""

import hashlib
import re
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RECORD = REPO / "ops" / "ND1_PROFILE_RATIFICATION.md"

#: Each approval, located BY HASH in the tree its own record binds. The
#: (path, line, span) are search results, not assumptions — the hash is
#: what identifies the bytes, and every one is re-verified below.
APPROVALS = (
    ("R1", "profile",
     "0a08319a408f068ce4c92f93c2c4c39e409937dddfd0ef9f7af43618c70b50a5",
     "803d99162d0a018ae5a3b44273601d98d9439d50",
     "ops/DECISION_PACKET_N00_AND_ND1.md", 1309, 49),
    ("R2", "profile",
     "a3d40b7ce218294b75265622306bb91fc01081f98a0bacce8f8e86a3d3d8741d",
     "c56286b684b03d7544db9db16b59b5443182f9e6",
     "ops/DECISION_PACKET_N00_AND_ND1.md", 1614, 51),
    ("R3", "profile",
     "d40ad864571ec4773d68cdd4049b0eb8423da4cdf3fee7a145705f29c65f0d1d",
     "2728e437b4c01ced97349e45077f2f87db7ac21d",
     "ops/PREP_ITEM6_ND1_R3_AMENDMENT_PROPOSAL.md", 110, 60),
    # A FOURTH APPROVED ARTEFACT, found 2026-08-29 while drafting the round-3
    # prompt. The first version of this file enumerated three and called
    # itself "every approval". The CR1 grammar is approved separately as
    # `APPROVED_CR1_GRAMMAR_SHA256` because it is NOT inside the profile
    # block: it is its own canonical block, bound into R3 by one line
    # (`RECOMMENDED_CR1_GRAMMAR_SHA256`). Three-of-four is exactly the
    # defect round 2 found — anchoring on a subset without knowing it.
    ("CR1_GRAMMAR", "grammar",
     "c251335f8d8c4dc89bce4ff7fb445f862d29a04b676bb3a90f6ef5ce5d5e3483",
     "2728e437b4c01ced97349e45077f2f87db7ac21d",
     "ops/PREP_ITEM6_ND1_R3_AMENDMENT_PROPOSAL.md", 188, 17),
)

#: Why the anchored-value check does not apply to every kind. Stated per
#: kind rather than hidden in an `if`, so a new kind cannot be added
#: without someone writing down what it is exempt from and why.
KIND_SCOPE = {
    "profile": "carries the ND1 field values; the anchored values must "
               "appear verbatim",
    "grammar": "the CR1 event grammar, a separate canonical block. It "
               "carries no ND1 field values, so the anchored-value check "
               "does not apply — but the falsifier check does, and the "
               "preimage must still reconstruct.",
}

#: The values the C_BUILD_2 wording anchors on. If a future approval changes
#: any of them, the wording's criterion-(4) claim is stale.
ANCHORED = (
    "RECOMMENDED_ND1_PARTIAL_RECOVERY_RULE=MODIFY",
    "RECOMMENDED_ND1_PARTIAL_MODIFY_TEXT="
    "BRANCH_E_RENAME_TO_.partial.divergent.<incident_id>;"
    "BRANCH_C_RENAME_THEN_ALLOW_RETRY",
    "RECOMMENDED_ND1_ARCHIVE_FAILURE_POLICY=A",
)

TIMING = re.compile(
    r"staging|期间|during|时机|when|运行时|中途|\bmid\b|checkpoint",
    re.IGNORECASE)


def _preimage(commit, path, start, span):
    out = subprocess.run(["git", "-C", str(REPO), "show",
                          "%s:%s" % (commit, path)], capture_output=True)
    assert out.returncode == 0, out.stderr
    lines = out.stdout.decode("utf-8").split("\n")
    return "\n".join(lines[start - 1:start - 1 + span]) + "\n"


class TestEveryApprovedPreimageReconstructs(unittest.TestCase):

    def test_each_one_hashes_to_its_declared_value(self):
        for label, _kind, sha, commit, path, start, span in APPROVALS:
            with self.subTest(approval=label):
                body = _preimage(commit, path, start, span)
                self.assertEqual(
                    sha, hashlib.sha256(body.encode("utf-8")).hexdigest(),
                    "%s does not reconstruct; its (path, line, span) is "
                    "stale and those bytes are not the approved ones"
                    % label)


class TestTheAnchoredValuesAgreeAcrossEveryApproval(unittest.TestCase):
    """The check that was missing. §13.2 anchored on R1 alone while R2 and
    R3 already existed."""

    def test_the_values_are_identical_in_every_profile_approval(self):
        checked = 0
        for label, kind, _sha, commit, path, start, span in APPROVALS:
            if kind != "profile":
                continue
            checked += 1
            body = _preimage(commit, path, start, span)
            for value in ANCHORED:
                with self.subTest(approval=label, value=value[:48]):
                    self.assertIn(
                        value, body,
                        "%s does not carry %r. The wording anchors on it, so "
                        "either the anchor is stale or the supersession is "
                        "scoped in a way the wording must state."
                        % (label, value))
        self.assertGreater(checked, 2,
                           "only %d profile approvals were checked; the "
                           "loop is skipping them" % checked)

    def test_the_supersession_scopes_are_recorded(self):
        """R1 and R2 are superseded only FOR NAMED EVENTS. That scoping is
        why R1's values can still govern the fields this wording uses, and
        it must be readable rather than inferred."""
        text = RECORD.read_text(encoding="utf-8")
        self.assertIn("R1_STATUS=SUPERSEDED_BY_R2_FOR_P3_ONLY", text)
        self.assertIn("R2_STATUS=SUPERSEDED_BY_R3_FOR_P3_AND_F3_ONLY", text)


class TestTheFalsifierIsCheckedAgainstEveryApproval(unittest.TestCase):
    """Not only the oldest one, which is what §13.2 did."""

    def test_no_approval_constrains_when_the_gate_runs(self):
        for label, _kind, _sha, commit, path, start, span in APPROVALS:
            body = _preimage(commit, path, start, span)
            offenders = [line for line in body.split("\n")
                         if TIMING.search(line)]
            with self.subTest(approval=label):
                self.assertEqual(
                    [], offenders,
                    "%s constrains WHEN the gate runs, which triggers the "
                    "ruling's falsifier and voids decision B: %r"
                    % (label, offenders))


class TestAFourthApprovalFailsClosed(unittest.TestCase):
    """The staleness protection itself. An approval nobody has examined is
    the state this file exists to prevent, so its appearance is a failure
    rather than something for a reviewer to notice later.

    WHAT THIS DOES **NOT** COVER, stated because Sol's MEDIUM was that the
    claim outran the domain. The scan reads ONE file,
    `ops/ND1_PROFILE_RATIFICATION.md`. An approval recorded somewhere else
    entirely is outside it and always was.

    That gap is not closable from here: closing it needs
    `SIGNABLE_RATIFICATION_ROUTES=1` -- "an approval takes effect only when
    appended to this record" -- to be an AUTHORITATIVE, frozen governance
    invariant, and today it is a builder self-report. Sol listed exactly
    that as `UNRESOLVED_FOR_AARON`. Until it is ratified, this file's honest
    claim is "every approval RECORDED HERE", not "every approval", and the
    difference is written down rather than left for the next reviewer to
    find again."""

    def test_the_record_declares_exactly_the_approvals_we_checked(self):
        text = RECORD.read_text(encoding="utf-8")
        # WIDENED 2026-08-29. The pattern used to be
        # `APPROVED_PROFILE_SHA256` alone, which silently ignored
        # `APPROVED_CR1_GRAMMAR_SHA256` — a fourth approved artefact this
        # file claimed to account for and did not. Any APPROVED_*SHA256
        # now counts.
        declared = set(re.findall(
            r"APPROVED_[A-Z0-9_]*SHA256=([0-9a-f]{64})", text))
        # WIDENED AGAIN 2026-08-30, fresh Sol c-build-2-wording-r3 MEDIUM.
        # Reproduced before accepting: an approval written as PROSE --
        # carrying the profile id, the SHA-256 and the doc HEAD in a
        # sentence rather than in the field -- left this 8/8 GREEN. The
        # detection domain was "this file, and only text matching the field
        # syntax", while the claim was "every approval".
        #
        # A field-shaped pattern can always be stepped around by not using
        # the field, so the domain is now the HASH: any 64-hex in the record
        # must be an approval this file has examined. Measured at the time
        # of writing: 4 in the record, 4 declared by field, 4 examined --
        # zero false positives, so the widening installs clean rather than
        # needing an allowlist that would rot.
        declared |= set(re.findall(r"\b[0-9a-f]{64}\b", text))
        known = {sha for _l, _k, sha, _c, _p, _s, _n in APPROVALS}
        unexamined = declared - known
        self.assertEqual(
            set(), unexamined,
            "the ratification record declares approval(s) this file has "
            "never examined: %s\nReconstruct each preimage, check the "
            "anchored values and the falsifier against it, then add it to "
            "APPROVALS. Do NOT widen the pattern to make this pass."
            % sorted(unexamined))

    def test_nothing_we_checked_has_vanished_from_the_record(self):
        """The other direction: an approval we anchor on being edited out
        would leave this file asserting against bytes nobody stands behind.
        The record is append-only, so this should be impossible — which is
        why it is worth asserting."""
        text = RECORD.read_text(encoding="utf-8")
        for label, _kind, sha, _c, _p, _s, _n in APPROVALS:
            with self.subTest(approval=label):
                self.assertIn(sha, text)



class TestEveryKindDeclaresWhatItIsCheckedFor(unittest.TestCase):
    """A kind added without a KIND_SCOPE entry would silently skip the
    anchored-value check — the same silence that let the CR1 grammar sit
    outside this file for a day."""

    def test_every_kind_used_has_a_recorded_scope(self):
        used = {kind for _l, kind, _s, _c, _p, _st, _n in APPROVALS}
        self.assertEqual(set(KIND_SCOPE), used,
                         "kinds in APPROVALS: %s; kinds with a recorded "
                         "scope: %s" % (sorted(used), sorted(KIND_SCOPE)))

    def test_the_grammar_kind_really_carries_no_anchored_value(self):
        """The exemption, verified rather than asserted. If the CR1 grammar
        ever does carry one of these values, the exemption is wrong and the
        anchored-value check must cover it."""
        for label, kind, _sha, commit, path, start, span in APPROVALS:
            if kind != "grammar":
                continue
            body = _preimage(commit, path, start, span)
            for value in ANCHORED:
                with self.subTest(approval=label, value=value[:40]):
                    self.assertNotIn(
                        value, body,
                        "%s carries %r, so exempting it from the "
                        "anchored-value check is wrong" % (label, value))


if __name__ == "__main__":
    unittest.main()
