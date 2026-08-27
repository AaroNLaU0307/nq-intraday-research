"""A guard that asserts an absence must prove it could have seen a presence.

THE DEFECT CLASS. `self.assertEqual([], offenders)` after a filesystem scan
is true two ways: nothing was wrong, or nothing was looked at. The second
reads exactly like the first — clean, and loudly so. A wrong root, a changed
glob, a package move, a parse that silently yields nothing, and the guard
reports success forever while enforcing nothing.

MEASURED, NOT SUPPOSED. A sweep of both repositories on 2026-08-27 found four
instances. Two of them sat directly beside a sibling test that already did it
right — `assertEqual(checked, 14)` in one case, an explicit `"premise: ..."`
assertion plus a whole test proving git honours the probed file in the other.
So the pattern was known here; it just was not applied uniformly, which is
precisely the kind of gap a standing check exists to hold.

WHY AN ALLOWLIST RATHER THAN A CLEAN ZERO. Some flagged tests are correct:
the premise may live in a sibling test, or failing-safe may be structural. The
allowlist below names WHERE the premise lives for each. That is the difference
between a registered exception and a suppressed warning — an entry has to say
something checkable. It is enforced in both directions: a new unregistered
instance fails, and so does an entry for a test that no longer trips.

THIS FILE IS SUBJECT TO ITS OWN RULE. `test_the_detector_detects` runs the
scanner over a synthetic sample containing the defect. Without it, a detector
that matched nothing at all would report both repositories clean — the same
failure one level up.
"""

import ast
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TESTS = REPO / "tests"

#: FILESYSTEM discovery only. `split` and `read_text` were in this set first
#: and produced two false positives: reading one named file cannot yield zero
#: files, so a guard over it is not vacuous in the way this looks for.
DISCOVERY = {"glob", "rglob", "iterdir", "listdir", "scandir"}

#: `walk` is filesystem discovery as `os.walk` and NOT as `ast.walk`, which
#: appears in nearly every structural test here. Counting the bare attribute
#: name flagged three tests that parse one named file — a detector that
#: cannot tell those apart is one nobody keeps.
_QUALIFIED_DISCOVERY = {("os", "walk")}


def _qualified_calls(node):
    out = set()
    for x in ast.walk(node):
        if (isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute)
                and isinstance(x.func.value, ast.Name)):
            out.add((x.func.value.id, x.func.attr))
    return out

#: Where the premise lives, per registered exception. "It's fine" is not a
#: reason; the entry has to name the thing that carries the proof.
_JUSTIFIED = {
    "tests/test_registry_path_single_construction.py::"
    "test_only_the_boundary_constructs_the_registry_path":
        "the premise lives in test_the_scan_actually_reaches_files, in the "
        "same class: it asserts the identical SRC.rglob('*.py') reaches >20 "
        "modules, so this guard's scan cannot be silently empty either",
    #: The line above is the whole point of an allowlist ENTRY rather than a
    #: suppression: it names the test that carries the proof, and if that
    #: test is deleted this reason becomes checkably false.
    #:
    #: Otherwise EMPTY, and that is the measured state — not an aspiration. The first
    #: draft of this file registered three exceptions; tightening the detector
    #: (filesystem discovery only; `assertEqual(checked, 23)` recognised as a
    #: premise) cleared all three, and the staleness check below is what said
    #: so. Zero here means zero found, not zero looked for.
}


def _called_names(node):
    out = set()
    for x in ast.walk(node):
        if isinstance(x, ast.Call):
            f = x.func
            out.add(getattr(f, "attr", getattr(f, "id", "")))
    return out


def _resolved_bodies(fn, helpers):
    """`fn`, plus one level of the `self._helper(...)` methods it calls.

    Needed because the house style delegates the assertion into a helper
    (`self._refuses(value)`); without following it, every such test looks
    assertion-free and the signal drowns."""
    yield fn
    for x in ast.walk(fn):
        if (isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute)
                and isinstance(x.func.value, ast.Name)
                and x.func.value.id == "self"):
            helper = helpers.get(x.func.attr)
            if helper is not None:
                yield helper


def _nonempty_literal(arg):
    if isinstance(arg, ast.Constant) and isinstance(arg.value, int):
        return arg.value > 0
    if isinstance(arg, (ast.List, ast.Set, ast.Tuple)):
        return bool(arg.elts)
    if isinstance(arg, ast.Dict):
        return bool(arg.keys)
    return False


def scan(tests_dir: Path, root: Path):
    """(relpath, lineno, name) for every test that asserts emptiness over a
    discovered collection without asserting the collection was non-empty."""
    flagged = []
    for path in sorted(tests_dir.rglob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for cls in ast.walk(tree):
            if not isinstance(cls, ast.ClassDef):
                continue
            helpers = {m.name: m for m in cls.body
                       if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))}
            for fn in cls.body:
                if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if not fn.name.startswith("test"):
                    continue
                parts = list(_resolved_bodies(fn, helpers))
                called = set()
                for part in parts:
                    called |= _called_names(part)
                qualified = set()
                for part in parts:
                    qualified |= _qualified_calls(part)
                if not (called & DISCOVERY) and not (
                        qualified & _QUALIFIED_DISCOVERY):
                    continue
                asserts_empty = premise = False
                for part in parts:
                    for x in ast.walk(part):
                        if not (isinstance(x, ast.Call)
                                and isinstance(x.func, ast.Attribute)):
                            continue
                        attr = x.func.attr
                        if attr == "assertFalse":
                            asserts_empty = True
                        if attr in ("assertEqual", "assertListEqual",
                                    "assertSetEqual"):
                            for arg in x.args[:2]:
                                if isinstance(arg, (ast.List, ast.Set, ast.Dict)) \
                                        and not (getattr(arg, "elts", None)
                                                 or getattr(arg, "keys", None)):
                                    asserts_empty = True
                                if _nonempty_literal(arg):
                                    premise = True
                        if attr in ("assertTrue", "assertGreater", "assertIn",
                                    "assertGreaterEqual", "assertNotEqual",
                                    "assertLess"):
                            premise = True
                if asserts_empty and not premise:
                    flagged.append((path.relative_to(root).as_posix(),
                                    fn.lineno, fn.name))
    return flagged


class TestNoUnregisteredVacuousGuards(unittest.TestCase):

    def test_the_scan_reaches_the_test_tree(self):
        """THIS FILE OBEYS ITS OWN RULE.

        With an empty allowlist the guard below is `assertEqual([], [])`,
        which is exactly the shape this file exists to catch: true when
        nothing is wrong, and equally true when nothing was looked at. A
        wrong `TESTS` root would report the suite clean forever."""
        files = list(TESTS.rglob("test_*.py"))
        self.assertGreater(len(files), 10,
                           f"the vacuity scan reached {len(files)} test "
                           "files; at that count it proves nothing")

    def test_every_flagged_guard_is_registered_with_its_premise(self):
        found = {f"{rel}::{name}" for rel, _ln, name in scan(TESTS, REPO)}
        new = sorted(found - set(_JUSTIFIED))
        self.assertEqual([], new,
                         "these guards assert an absence over a scanned "
                         "collection without proving the scan found anything, "
                         "so they pass when they look at nothing:\n  "
                         + "\n  ".join(new))

    def test_no_registered_exception_has_gone_stale(self):
        """The other direction. An allowlist nobody prunes is how a check
        stops being believed — the same reasoning as the freeze register's
        orphan-entry rule."""
        found = {f"{rel}::{name}" for rel, _ln, name in scan(TESTS, REPO)}
        stale = sorted(set(_JUSTIFIED) - found)
        self.assertEqual([], stale,
                         "these are registered as justified exceptions but no "
                         "longer trip the detector; delete the entries:\n  "
                         + "\n  ".join(stale))


class TestTheDetectorDetects(unittest.TestCase):
    """Without this, a detector that matched nothing would report clean."""

    def _sample(self, body):
        import tempfile
        d = Path(tempfile.mkdtemp())
        (d / "test_sample.py").write_text(
            "import unittest\n"
            "from pathlib import Path\n"
            "class T(unittest.TestCase):\n" + body, encoding="utf-8")
        return d

    def test_it_flags_the_shape(self):
        d = self._sample(
            "    def test_x(self):\n"
            "        bad = [p for p in Path('.').rglob('*.py') if p.stat()]\n"
            "        self.assertEqual([], bad)\n")
        self.assertEqual(1, len(scan(d, d)))

    def test_it_clears_the_same_shape_once_a_count_is_added(self):
        d = self._sample(
            "    def test_x(self):\n"
            "        bad = [p for p in Path('.').rglob('*.py') if p.stat()]\n"
            "        self.assertGreater(len(list(Path('.').rglob('*.py'))), 3)\n"
            "        self.assertEqual([], bad)\n")
        self.assertEqual([], scan(d, d))

    def test_it_follows_a_helper_rather_than_calling_it_assertion_free(self):
        """The false-positive direction, pinned: 30-odd tests here delegate
        their assertion into `self._refuses(...)`."""
        d = self._sample(
            "    def _check(self, xs):\n"
            "        self.assertEqual([], xs)\n"
            "    def test_x(self):\n"
            "        self._check([p for p in Path('.').rglob('*.py')])\n")
        self.assertEqual(1, len(scan(d, d)))

    def test_ast_walk_is_not_filesystem_discovery(self):
        """The false positive that would have made this file worthless: three
        structural tests parse ONE named file and call `ast.walk` on it."""
        d = self._sample(
            "    def test_x(self):\n"
            "        import ast\n"
            "        bad = [n for n in ast.walk(ast.parse('1'))]\n"
            "        self.assertEqual([], bad)\n")
        self.assertEqual([], scan(d, d))

    def test_os_walk_still_counts(self):
        d = self._sample(
            "    def test_x(self):\n"
            "        import os\n"
            "        bad = [r for r, _d, _f in os.walk('.')]\n"
            "        self.assertEqual([], bad)\n")
        self.assertEqual(1, len(scan(d, d)))

    def test_reading_one_named_file_is_not_discovery(self):
        """Why `read_text`/`split` are not in DISCOVERY: they cannot yield
        zero files, and treating them as discovery made two false positives."""
        d = self._sample(
            "    def test_x(self):\n"
            "        bad = [ln for ln in Path('x').read_text().split('\\n')]\n"
            "        self.assertEqual([], bad)\n")
        self.assertEqual([], scan(d, d))


if __name__ == "__main__":
    unittest.main()
