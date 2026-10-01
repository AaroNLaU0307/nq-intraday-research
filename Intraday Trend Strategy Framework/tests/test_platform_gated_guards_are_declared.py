"""A guard that only runs on one platform must SAY SO somewhere.

THE PROBLEM, and it is the same shape as everything else this month. The
alternate-data-stream guards in `test_resolve_partial_state_diff.py` call
`skipTest` off Windows. On this machine they are real protection. On a Linux
CI they report as skipped, the suite goes green, and the sentence "the
snapshot sees every blob of bytes in the directory" is being enforced by
nothing at all.

A skip is not a failure and should not be one -- there are no alternate data
streams to miss on ext4, so skipping is the CORRECT answer there. What is
wrong is that the fact goes UNRECORDED: a green run says the same thing
whether three guards ran or none did.

So this file does not forbid platform gating. It requires that the SET of
gated guards be declared, and refuses any that appear without being declared.
Adding a fourth Windows-only guard without recording it turns the suite red
on every platform, including the one where it runs.

WHY A DECLARATION AND NOT A COUNT. A count would let one guard be deleted and
another added silently. The declaration names them, so the diff is legible to
a reviewer -- which is the whole point of writing it down.
"""

import ast
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent

#: Guards that RUN ON WINDOWS ONLY, with the reason each is gated. A guard
#: named here is understood to be INACTIVE anywhere else; that is the
#: statement this file exists to keep true and visible.
#:
#: This is a declaration, not a mirror of the code -- the code is walked
#: below and any gate missing from here is reported. Adding a name to silence
#: a failure is how a declaration stops meaning anything, so each entry
#: carries why the platform matters.
WINDOWS_ONLY = {
    ("test_resolve_partial_state_diff.py",
     "test_an_ADS_TRUNCATION_is_reported"):
        "NTFS alternate data streams do not exist off Windows, so there is "
        "nothing to truncate -- but nothing verifies the stream walk either",
    ("test_resolve_partial_state_diff.py",
     "test_the_MAIN_bytes_surviving_does_not_excuse_a_lost_stream"):
        "same: the bypass it proves closed is an NTFS-only bypass",
    ("test_resolve_partial_state_diff.py",
     "test_a_written_stream_is_found_and_read_back"):
        "non-vacuity for the FindFirstStreamW binding, which is a Win32 call",
    ("test_resolve_partial_state_diff.py",
     "test_a_file_with_no_streams_reports_none"):
        "the other half of the same binding check",
}


def platform_gated(path):
    """Every test in `path` that skips itself on a platform check.

    Found by walking the AST for `sys.platform != ...` guarding a
    `skipTest`, so a gate added in a new test is seen whether or not anyone
    remembers this file."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not node.name.startswith("test"):
            continue
        if _reads_sys_platform(node) and _calls_skiptest(node):
            found.add(node.name)
    return found


def _reads_sys_platform(node):
    """A real `sys.platform` ATTRIBUTE ACCESS, not the text of one.

    The first version matched `ast.unparse(node)` against the strings
    "sys.platform" and "skipTest", and immediately reported ITSELF: this
    file's own vacuity tests build fake sources containing those words as
    string literals. A checker that cannot tell a mention from a use is the
    same mistake, in miniature, as five rounds of matching syntax."""
    return any(isinstance(inner, ast.Attribute) and inner.attr == "platform"
               and isinstance(inner.value, ast.Name)
               and inner.value.id == "sys"
               for inner in ast.walk(node))


def _calls_skiptest(node):
    return any(isinstance(inner, ast.Call)
               and getattr(inner.func, "attr", None) == "skipTest"
               for inner in ast.walk(node))


def undeclared_gates():
    problems = []
    for path in sorted(TESTS.glob("test_*.py")):
        for name in sorted(platform_gated(path)):
            if (path.name, name) not in WINDOWS_ONLY:
                problems.append(
                    "%s::%s skips itself on a platform check but is not in "
                    "WINDOWS_ONLY. A green suite must not mean two different "
                    "things depending on where it ran -- declare the gate, "
                    "with why the platform matters." % (path.name, name))
    return problems


def stale_declarations():
    """Declared gates that no longer exist. A declaration that outlives its
    guard reads as coverage nobody has."""
    live = {(path.name, name)
            for path in sorted(TESTS.glob("test_*.py"))
            for name in platform_gated(path)}
    return sorted("%s::%s is declared platform-gated but no longer gates "
                  "itself (or no longer exists)" % key
                  for key in WINDOWS_ONLY if key not in live)


class TestEveryPlatformGateIsDeclared(unittest.TestCase):

    def test_no_gate_is_undeclared(self):
        self.assertEqual([], undeclared_gates(),
                         "\n  ".join([""] + undeclared_gates()))

    def test_no_declaration_is_stale(self):
        self.assertEqual([], stale_declarations(),
                         "\n  ".join([""] + stale_declarations()))

    def test_every_declaration_says_WHY(self):
        """A reason is what lets a reviewer disagree. A gate with an empty
        justification is an unexamined one."""
        thin = sorted(key for key, why in WINDOWS_ONLY.items()
                      if len(why) < 40)
        self.assertEqual([], thin, "these gates give no real reason: %s" % thin)

    def test_the_walk_actually_finds_the_gates(self):
        """Vacuity: a broken AST walk would report nothing undeclared AND
        nothing stale, which reads exactly like a healthy result."""
        found = platform_gated(TESTS / "test_resolve_partial_state_diff.py")
        self.assertGreaterEqual(
            len(found), 4,
            "found %d platform gates in the state-diff file; the ADS guards "
            "are gated, so a lower number means the walk is broken rather "
            "than the file being clean" % len(found))


class TestTheWalkIsNotVACUOUS(unittest.TestCase):

    def _walk(self, source):
        import tempfile
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        path = Path(holder.name) / "test_x.py"
        path.write_text(source, encoding="utf-8")
        return platform_gated(path)

    def test_a_gated_test_is_found(self):
        self.assertEqual({"test_gated"}, self._walk(
            "class A(unittest.TestCase):\n"
            "    def test_gated(self):\n"
            "        if sys.platform != 'win32':\n"
            "            self.skipTest('nope')\n"))

    def test_an_ungated_test_is_not_found(self):
        self.assertEqual(set(), self._walk(
            "class A(unittest.TestCase):\n"
            "    def test_plain(self):\n"
            "        self.assertTrue(True)\n"))

    def test_an_unconditional_skip_is_not_a_PLATFORM_gate(self):
        """Different problem, different guard. A test skipped everywhere is
        dead code; a test skipped on one platform is uneven coverage."""
        self.assertEqual(set(), self._walk(
            "class A(unittest.TestCase):\n"
            "    def test_skipped(self):\n"
            "        self.skipTest('always')\n"))


if __name__ == "__main__":
    unittest.main()
