"""No committed enumeration descends into the quarantined subtree.

WRITTEN AFTER AN INCIDENT I CAUSED, 2026-08-29. Sweeping `ops/` from an
ad-hoc shell loop, I ran a content grep over
`ops/outcome_quarantine/MC_TO_STRATEGY_MASTER_PLAN.md`. Only a count came
back, so nothing was revealed — but `ops/RECOVERY_ANCHOR.md` §5 records
that the third burnt reviewer seat was touched by exactly that: one
single-pattern grep. The pattern being narrow was luck.

I cannot mechanise my own shell. What I CAN mechanise is the property the
committed code currently has and could quietly lose:

    ops.glob("*.md")            non-recursive, cannot descend      MEASURED
    rglob("*.py") anywhere      the quarantine holds only .md      MEASURED

Both are true today by accident of shape, not by anyone's intent. A change
from `glob` to `rglob` in a test that walks `ops/`, or one `.py` file
landing in the quarantine, silently removes the protection. Neither would
fail any existing check.

So this file pins both, and states plainly what it does not cover: it says
nothing about interactive commands, and `grep -v outcome_quarantine` in a
shell loop is a habit, not a guard. The real answer remains the one the
recovery anchor gives — while the content sits in a searchable tree, any
search can surface it.
"""

import ast
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OPS = REPO / "ops"
QUARANTINE = OPS / "outcome_quarantine"

#: Enumeration calls that descend. `glob` does not; `rglob` does.
DESCENDING = {"rglob", "walk"}


def _target_names(target):
    """Names bound by a `for`/comprehension target, tuples included."""
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, (ast.Tuple, ast.List)):
        names = set()
        for element in target.elts:
            names |= _target_names(element)
        return names
    return set()


class TestTheQuarantineHoldsNothingAPythonWalkWouldFind(unittest.TestCase):

    def test_the_quarantine_exists(self):
        """A guard over an empty or moved directory proves nothing. If the
        subtree is gone, this file must be revisited rather than left
        passing vacuously."""
        self.assertTrue(QUARANTINE.is_dir(),
                        "the quarantine subtree is missing; the migration "
                        "may have moved it and this guard now watches "
                        "nothing")
        self.assertTrue(list(QUARANTINE.iterdir()),
                        "the quarantine is empty")

    def test_it_contains_only_markdown(self):
        """The reason `rglob('*.py')` sweeps cannot reach it. One `.py`
        landing here removes that protection with nothing else changing."""
        others = sorted(p.name for p in QUARANTINE.rglob("*")
                        if p.is_file() and p.suffix != ".md")
        self.assertEqual([], others,
                         "non-markdown files are in the quarantine, so "
                         "source sweeps can now reach it: %s" % others)


#: Recursive walks over `ops/` that have been examined and are legitimate.
#: A blanket ban would be wrong: `ops/README.md` MUST index the quarantined
#: records by NAME, or ten governance records fall out of the index while
#: it still calls itself complete — and Aaron ruled 2026-08-27 that a
#: filename is not content. What is forbidden is recursing and then READING.
REVIEWED_RECURSIVE_WALKS = {
    "test_ops_index_is_complete.py":
        "the index must list quarantined records by name; uses p.name only",
}

#: Reading a walked path, as opposed to naming it.
READING = {"read_text", "read_bytes", "open"}


class TestEveryRecursiveOpsWalkHasBeenExamined(unittest.TestCase):
    """Fail closed on a NEW one rather than ban the category.

    The first version of this class banned recursion outright and went red
    on the index guard — which is doing the right thing. That is the same
    error the week has been about: a rule wider than the property it means
    to protect. The property is "no committed code recurses into the
    quarantine AND READS WHAT IT FINDS"."""

    def _ops_walkers(self):
        for path in sorted((REPO / "tests").glob("*.py")):
            if path.name == Path(__file__).name:
                continue
            source = path.read_text(encoding="utf-8")
            if "OPS" not in source and "ops" not in source:
                continue
            yield path, source

    def _recursive_sites(self):
        for path, source in self._ops_walkers():
            try:
                tree = ast.parse(source)
            except SyntaxError:                     # pragma: no cover
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                if getattr(node.func, "attr", "") not in DESCENDING:
                    continue
                base = getattr(getattr(node.func, "value", None), "id", "")
                if base in ("OPS", "ops"):
                    yield path, node, tree

    def test_no_unexamined_recursive_walk_exists(self):
        unexamined = sorted({
            "%s:%d" % (path.name, node.lineno)
            for path, node, _tree in self._recursive_sites()
            if path.name not in REVIEWED_RECURSIVE_WALKS})
        self.assertEqual(
            [], unexamined,
            "a committed test recurses into ops/ and has not been examined "
            "for whether it READS what it finds: %s\nExamine it, then add "
            "the file to REVIEWED_RECURSIVE_WALKS with the reason. Do NOT "
            "add it without reading it." % unexamined)

    @staticmethod
    def _names_bound_from_walking(tree):
        """Every local name that ends up holding a path the walk produced.

        Seeded with the functions that return the walk, then extended
        through `for`/comprehension targets that iterate them. A read on
        any of these names is a read of something the walk found; a read on
        `INDEX` or `HANDOFF` is not, which is the distinction the first
        version of this test missed — it flagged every read in the file and
        went red on five reads of named constants."""
        producers = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for inner in ast.walk(node):
                    if (isinstance(inner, ast.Call)
                            and getattr(inner.func, "attr", "") in DESCENDING):
                        producers.add(node.name)
        bound = set()
        for node in ast.walk(tree):
            iterated = getattr(node, "iter", None)
            if iterated is None:
                for gen in getattr(node, "generators", []):
                    iterated = gen.iter
                    target = gen.target
                    if getattr(getattr(iterated, "func", None), "id",
                               "") in producers:
                        bound.update(_target_names(target))
                continue
            call = getattr(iterated, "func", None)
            if getattr(call, "id", "") in producers or getattr(
                    call, "attr", "") in DESCENDING:
                bound.update(_target_names(node.target))
        return bound

    def test_the_examined_walk_still_only_uses_names(self):
        """The reason it is allowed, re-checked every run rather than
        trusted because it was true when the entry was written."""
        for path, _node, tree in self._recursive_sites():
            if path.name not in REVIEWED_RECURSIVE_WALKS:
                continue
            walked = self._names_bound_from_walking(tree)
            reads = sorted(
                n.lineno for n in ast.walk(tree)
                if isinstance(n, ast.Call)
                and getattr(n.func, "attr", "") in READING
                and getattr(getattr(n.func, "value", None), "id", "") in walked)
            self.assertEqual(
                [], reads,
                "%s recurses into ops/ AND reads a path the walk produced "
                "(lines %s, via %s); its entry in REVIEWED_RECURSIVE_WALKS "
                "says it uses names only, and that is no longer true"
                % (path.name, reads, sorted(walked)))

    def test_that_check_can_actually_see_a_walked_name(self):
        """The guard's own guard. If the binding analysis ever stops
        finding the walked names, the test above passes by seeing nothing —
        which is the exact failure mode this repository keeps hitting."""
        for path, _node, tree in self._recursive_sites():
            if path.name not in REVIEWED_RECURSIVE_WALKS:
                continue
            self.assertTrue(
                self._names_bound_from_walking(tree),
                "%s: no name was traced back to the walk, so the read check "
                "over it is vacuous" % path.name)

    def test_the_sweep_found_the_walk_it_knows_about(self):
        """A scan that silently matches nothing reports clean. This asserts
        the one known site is actually being seen."""
        seen = {path.name for path, _n, _t in self._recursive_sites()}
        self.assertEqual(set(REVIEWED_RECURSIVE_WALKS), seen,
                         "the sweep sees %s but the allowlist names %s; one "
                         "of them is stale"
                         % (sorted(seen), sorted(REVIEWED_RECURSIVE_WALKS)))

    def test_the_sweep_actually_examined_something(self):
        """The failure mode of every scan-based guard: matching nothing and
        reporting clean."""
        examined = list(self._ops_walkers())
        self.assertGreater(len(examined), 3,
                           "the ops-walker sweep found %d files, which is "
                           "too few to be real" % len(examined))


class TestWhatThisDoesNotCover(unittest.TestCase):
    """Said out loud, because a guard whose limits are implied gets read as
    covering more than it does — the defect this repository has spent the
    week on."""

    def test_the_incident_record_states_the_residual(self):
        record = (OPS
                  / "INCIDENT_BUILDER_GREPPED_A_QUARANTINED_FILE_20260829.md")
        self.assertTrue(record.exists())
        text = record.read_text(encoding="utf-8")
        self.assertIn("grep -v", text)
        self.assertIn("不是那个问题的解", text)


if __name__ == "__main__":
    unittest.main()
