"""Invariant 5 of dec-registry-migration-2026-08-27 — one construction site.

WHY THE EXISTING GUARD DID NOT COVER THIS. `test_registry_boundary.py`
asserts that no production module READS the governed path outside the
boundary, and it deliberately exempts three refusal stubs — each proved to
refuse by being CALLED. That architecture is sound for reads.

But migration changes the PATH, and the two sets do not overlap: the three
exempt modules each CONSTRUCTED the path themselves. The seat put it exactly
right — `registry_boundary`'s "the one governed path" comment described an
intention, not a mechanically guaranteed fact.

WHAT THE FOUR SITES ALSO CARRIED. Every one had
`read_text(...) if exists() else ""`, the same silent-empty fallback fixed
inside the boundary — so fixing the boundary alone would have closed nothing.
And `consumer.py` built a RELATIVE path, which resolved only when the
process happened to run from the repository root.

WHY THIS LANDS BEFORE THE ROUTE IS CHOSEN. The ruling made it route-
independent and ordered it first: whichever route wins, the path then
changes in one place instead of five.
"""

import ast
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src" / "itsf"

#: The one module allowed to spell the path.
_BOUNDARY = "registry_boundary"

#: How the path gets built: either the literal, or the segments joined.
_LITERAL = "ops/TRIAL_REGISTRY.md"
_FILENAME = "TRIAL_REGISTRY.md"


def _constructions(path: Path):
    """String constants naming the registry file, outside docstrings.

    AST rather than grep, because a docstring that DESCRIBES the path is
    not a construction of it — and this file's whole point is that the
    distinction was being made by eye."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node, clean=False)
            if doc is not None:
                docstrings.add(doc)
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value in docstrings:
                continue
            if _FILENAME in node.value or node.value == _LITERAL:
                found.append((node.lineno, node.value))
    return found


#: `scripts/` is not the package, and the first version of this guard did
#: not scan it. The migration-plan review found the gap: S6's "only one
#: place to change" was not proven to cover registry WRITERS, and
#: `scripts/s0_real_run.py` constructs the path itself at module level and
#: reads it in two more places.
#:
#: It is registered rather than converged. The script is the real-run entry
#: and its `CLEAN_GATE_ALLOWLIST_FILES` entry is GATE SEMANTICS the ruling
#: said not to touch; folding its path construction into the boundary is a
#: change to the real-run stack, not to this window's subject. So the
#: exception is named, counted, and will fail if it grows.
_KNOWN_SCRIPT_CONSTRUCTIONS = {
    "scripts/s0_real_run.py": 2,   # REGISTRY constant + clean-gate allowlist
}


class TestOneConstructionSite(unittest.TestCase):

    def test_scripts_constructions_are_exactly_the_registered_ones(self):
        """Not zero — REGISTERED. A count that grows means a new writer
        appeared outside the boundary, which is what would make a migration
        miss a path."""
        found = {}
        for path in sorted((REPO / "scripts").rglob("*.py")):
            hits = _constructions(path)
            if hits:
                found[path.relative_to(REPO).as_posix()] = len(hits)
        self.assertEqual(_KNOWN_SCRIPT_CONSTRUCTIONS, found,
                         "the set of registry-path constructions under "
                         "scripts/ changed; a migration would have to find "
                         "and update every one")

    def test_only_the_boundary_constructs_the_registry_path(self):
        offenders = []
        for path in sorted(SRC.rglob("*.py")):
            if path.stem == _BOUNDARY:
                continue
            for lineno, value in _constructions(path):
                offenders.append(
                    f"{path.relative_to(REPO).as_posix()}:{lineno} "
                    f"constructs {value!r}")
        self.assertEqual([], offenders,
                         "the governed registry path is constructed outside "
                         "registry_boundary; a migration would have to find "
                         "and update every one of these:\n  "
                         + "\n  ".join(offenders))

    def test_the_boundary_still_holds_it_exactly_once(self):
        """The other direction: if the constant disappeared, the guard above
        would pass vacuously."""
        found = _constructions(SRC / "mc" / "registry_boundary.py")
        self.assertEqual(1, len(found),
                         f"expected exactly one construction, got {found}")
        self.assertEqual(_LITERAL, found[0][1])


class TestTheConvergenceKeptTheSemantics(unittest.TestCase):
    """A refactor that changed what the gates do would be a different act
    from the one the ruling authorised."""

    def test_the_three_production_entries_still_refuse_gate_first(self):
        from itsf.mc import consumer, day_strata_supplement, real_input
        for fn in (day_strata_supplement.run_supplement_production,
                   consumer.run_real_mc,
                   real_input.prepare_real_mc_input):
            with self.assertRaises(Exception, msg=fn.__name__) as cm:
                fn()
            self.assertNotIsInstance(cm.exception, AssertionError)

    def test_they_route_through_the_boundary_now(self):
        """Named explicitly: if a site goes back to reading the file
        directly, the construction guard above catches the path but not a
        direct read of a path obtained some other way."""
        import inspect
        from itsf.mc import consumer, day_strata_supplement, real_input
        for fn in (day_strata_supplement.run_supplement_production,
                   consumer.run_real_mc,
                   real_input.prepare_real_mc_input):
            src = inspect.getsource(fn)
            self.assertIn("read_snapshot", src,
                          f"{fn.__name__} no longer reads through the "
                          "boundary")
            self.assertNotIn('else ""', src,
                             f"{fn.__name__} regained the silent-empty "
                             "fallback")


if __name__ == "__main__":
    unittest.main()
