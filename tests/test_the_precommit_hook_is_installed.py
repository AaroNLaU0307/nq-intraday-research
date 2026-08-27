"""The brake has to be connected, and only the suite can say whether it is.

`tools/githooks/pre-commit` is versioned; `core.hooksPath` is NOT. It lives in
`.git/config`, which no clone carries and no commit records. So the hook can
be present in the tree, look installed, and be doing nothing — on a fresh
clone, after a `git config --unset`, or on a second machine.

That is the exact shape this repository has been paying for all day: a
mechanism that exists, is correct, and is not connected to anything.
`registry_boundary`'s "the one governed path" was an intention rather than a
guaranteed fact; the freeze register existed while nothing forced it to be
armed; the round-4 prompt's own rule was written down and broken by its
author. A hook whose installation is invisible would be the next one.

So the suite checks the wiring. The hook guards commits; this guards the hook.

NOT self-installing. A test that silently ran `git config` would be a test
that changes the developer's environment as a side effect of being run, and
the failure message is one command long.
"""

import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EXPECTED = "tools/githooks"
HOOK = REPO / EXPECTED / "pre-commit"

INSTALL = "git config core.hooksPath tools/githooks"


def _config(key):
    out = subprocess.run(["git", "-C", str(REPO), "config", "--get", key],
                         capture_output=True, text=True)
    return out.stdout.strip()


class TestTheHookIsPresentAndConnected(unittest.TestCase):

    def test_the_hook_script_is_in_the_tree(self):
        self.assertTrue(HOOK.exists(),
                        f"{EXPECTED}/pre-commit is missing; the transport "
                        "guards then run only at full-suite time, which is "
                        "six minutes after the commit that broke them")

    def test_the_hook_is_tracked_by_git(self):
        """A hook that is only in the worktree disappears on the next clone
        just as quietly as an unset config."""
        out = subprocess.run(
            ["git", "-C", str(REPO), "ls-files", "--error-unmatch",
             f"{EXPECTED}/pre-commit"], capture_output=True, text=True)
        self.assertEqual(0, out.returncode,
                        f"{EXPECTED}/pre-commit is untracked")

    def test_hooks_path_points_at_it(self):
        got = _config("core.hooksPath")
        self.assertEqual(EXPECTED, got,
                         "core.hooksPath is %r, so the pre-commit brake is "
                         "NOT connected in this working copy. It is local "
                         "config and no clone carries it. Fix:\n    %s"
                         % (got or "(unset)", INSTALL))

    def test_the_hook_actually_runs_the_transport_guards(self):
        """Naming the right file is not the same as that file doing the job.
        A hook rewritten to `exit 0` would satisfy every check above."""
        text = HOOK.read_text(encoding="utf-8")
        for needed in ("test_artifacts_under_review_are_frozen",
                       "test_issued_deliveries_are_registered",
                       "pytest"):
            self.assertIn(needed, text,
                          f"the installed hook does not mention {needed!r}; "
                          "it is not running the transport guards")

    def test_the_hook_refuses_when_it_finds_no_guards_at_all(self):
        """The failure mode a narrow hook invites: rename the test files and
        the hook has nothing to run. It must refuse, not pass silently."""
        text = HOOK.read_text(encoding="utf-8")
        self.assertIn("refusing", text.lower(),
                      "the hook has no branch for 'no guards found'; renaming "
                      "the test files would disarm it silently")


if __name__ == "__main__":
    unittest.main()
