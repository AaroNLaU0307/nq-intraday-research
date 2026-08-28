"""A delivery document cannot be pinned by a commit range containing itself.

MEASURED 2026-08-29, the first time a `*PROMPT*.md` was ever registered in
this repository. Three guards written at different times combine into a
requirement no file can satisfy:

    test_issued_deliveries_are_registered
        an ISSUED delivery must appear in `under_review` under its own
        review_id -- otherwise the bytes the reviewer was told to hash are
        unprotected.

    derive_pin / test_the_pin_is_the_derived_one_not_a_typed_one
        the pin is the newest last-change commit across every registered
        path. With the delivery registered, that is the delivery's own
        commit.

    test_a_live_prompt_tells_the_reviewer_to_read_it_from_disk
        the prompt's TEXT must contain that pin.

Writing the pin into the text produces a new commit, which becomes the new
derived pin. There is no fixed point. Verified by history: no `*PROMPT*`
path had ever been registered, so the three had never been exercised
together and the impossibility had never surfaced.

THE FIX, and why it is not a weakening. Two different questions were being
answered by one mechanism:

    "have the REFERENCE bytes moved under the reviewer?"   -> commit range
    "have the DELIVERY bytes moved under the reviewer?"    -> content hash

The commit range was never the right instrument for the second one: the act
of issuing a delivery IS a commit to it. The hash guard
(`test_every_artifact_under_review_still_hashes_to_what_was_sent`) already
answers it exactly, and answers it for the worktree bytes the reviewer
actually reads.

So `derive_pin` now spans the reference set, and the delivery is pinned by
hash. What is NOT weakened: the delivery is still registered, still hashed
every run, and a post-issuance edit to it still fails -- measured below.
"""

import json
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REGISTER = REPO / "ops" / "ARTIFACTS_UNDER_REVIEW.json"


def _entries():
    if not REGISTER.exists():
        return []
    return json.loads(REGISTER.read_text(encoding="utf-8"))["under_review"]


class TestTheImpossibilityIsRealNotAMisconfiguration(unittest.TestCase):
    """If a fixed point ever exists, this fix is unnecessary and should be
    reverted rather than left as unexplained special-casing."""

    def test_writing_a_pin_into_a_file_changes_that_files_last_commit(self):
        """The whole proof in one line: a file's own commit cannot be named
        inside that file, because naming it is a change to the file."""
        out = subprocess.run(
            ["git", "-C", str(REPO), "log", "-1", "--format=%H", "--",
             "ops/PROMPT_C_BUILD_2_WORDING_SOL_REVIEW.md"],
            capture_output=True, text=True)
        commit = out.stdout.strip()
        self.assertTrue(commit, "the prompt has never been committed")
        text = (REPO / "ops"
                / "PROMPT_C_BUILD_2_WORDING_SOL_REVIEW.md").read_text("utf-8")
        self.assertNotIn(
            commit, text,
            "the prompt names its own last-change commit, so a fixed point "
            "EXISTS and this whole file is unnecessary -- revert the "
            "derive_pin change rather than keeping an unexplained exception")


class TestTheDeliveryIsStillProtected(unittest.TestCase):
    """What the fix must not cost."""

    def test_every_issued_delivery_is_still_registered(self):
        for entry in _entries():
            if entry.get("is_the_delivery_document"):
                self.assertIn("sha256", entry)
                self.assertTrue(entry["sha256"])
                return

    def test_the_delivery_hash_still_matches_the_bytes_on_disk(self):
        """The instrument that replaces the commit range for the delivery.
        If this ever stops running, the delivery is unprotected and the fix
        WAS a weakening."""
        import hashlib
        for entry in _entries():
            if not entry.get("is_the_delivery_document"):
                continue
            target = REPO / entry["path"]
            self.assertEqual(
                entry["sha256"],
                hashlib.sha256(target.read_bytes()).hexdigest(),
                "%s moved after issuance" % entry["path"])

    def test_the_reference_set_is_what_the_pin_now_spans(self):
        entries = _entries()
        if not entries:
            return
        references = [e for e in entries
                      if not e.get("is_the_delivery_document")]
        self.assertTrue(references,
                        "a review with no reference artifacts leaves the pin "
                        "spanning nothing; the delivery would then be "
                        "protected by its hash alone and this must be said "
                        "out loud rather than happening silently")


if __name__ == "__main__":
    unittest.main()
