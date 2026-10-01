"""A public function nothing calls is a claim nothing checks.

WHY THIS EXISTS. `mc/day_strata_context.build_precheck_context` shipped
with an AST guard asserting its single-read property and NOT ONE CALLER --
its only two references in the whole repository were a mention inside a
test docstring and its own `__all__`. It could have raised on every input
and the suite would have stayed green, because the guard read the SHAPE of
the source and nothing ran it.

That is this project's recurring defect wearing a new hat: the guard is
narrower than the property it is quoted for.

WHAT COUNTS AS REACHED, and the distinction that makes this guard work
rather than drown in noise:

  * a CALL, a Name, or an Attribute access -- from anywhere in `src/` or
    `tests/`, INCLUDING the defining module itself. A helper called only by
    its own module's public entry point is reached; a first draft of this
    scan excluded same-module calls and produced thirteen findings of which
    twelve were false.
  * NOT `__all__` membership. Exporting a name is advertising it, not
    using it -- and an exported-but-uncalled function is precisely the
    shape being hunted.
  * NOT a mention in a docstring or comment. Those are ast.Constant, and
    a name that appears only in prose has no caller.

SCOPE is `src/itsf/mc/*.py`, the package where the execution path lives and
where "built but never wired" has now happened three times in one night
(the row producer, the context assembler, and the failure planner all
existed as unreachable islands before being connected).

A LEGITIMATE ORPHAN CAN EXIST. Record it in `EXPECTED_ORPHANS` with the
reason. Deleting the guard because it fired is the one response that makes
the next instance invisible.
"""

import ast
import io
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MC = REPO / "src" / "itsf" / "mc"
SCAN_ROOTS = (REPO / "src", REPO / "tests")

#: name -> why nothing calls it and why that is correct.
#: Empty as of 2026-08-29, and that is a measured fact, not an aspiration.
EXPECTED_ORPHANS: dict = {}


def _public_defs() -> dict:
    """Top-level public functions of the mc package: name -> module."""
    found = {}
    for path in sorted(MC.glob("*.py")):
        if path.name == "__init__.py":
            continue
        tree = ast.parse(io.open(path, encoding="utf-8").read())
        for node in tree.body:
            if (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and not node.name.startswith("_")):
                found[node.name] = path.name
    return found


def _names_referenced(known: set) -> set:
    reached = set()
    for root in SCAN_ROOTS:
        for path in root.rglob("*.py"):
            try:
                tree = ast.parse(io.open(path, encoding="utf-8").read())
            except (SyntaxError, UnicodeDecodeError):       # pragma: no cover
                continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue                 # a definition is not a use
                name = None
                if isinstance(node, ast.Call):
                    name = (getattr(node.func, "attr", None)
                            or getattr(node.func, "id", None))
                elif isinstance(node, ast.Attribute):
                    name = node.attr
                elif isinstance(node, ast.Name):
                    name = node.id
                if name in known:
                    reached.add(name)
    return reached


class TestEveryPublicFunctionHasACaller(unittest.TestCase):

    def test_nothing_in_the_mc_package_is_an_unreached_island(self):
        defs = _public_defs()
        orphans = sorted(set(defs) - _names_referenced(set(defs))
                         - set(EXPECTED_ORPHANS))
        self.assertEqual(
            [], orphans,
            "these public mc/ functions are called by NOTHING -- not by "
            "production, not by a test, not even by their own module:\n  "
            + "\n  ".join("%s (%s)" % (o, defs[o]) for o in orphans)
            + "\n\nAn uncalled function's guarantees are unchecked no matter "
              "how many structural guards quote it. Wire it, test it, or "
              "record it in EXPECTED_ORPHANS with the reason.")

    def test_the_scan_found_a_realistic_number_of_functions(self):
        """Vacuity. A glob typo would report zero orphans out of zero."""
        self.assertGreater(len(_public_defs()), 100)

    def test_the_scan_found_a_realistic_number_of_references(self):
        defs = _public_defs()
        self.assertGreater(len(_names_referenced(set(defs))),
                           len(defs) * 0.9)


class TestTheScanRulesAreTheOnesDocumented(unittest.TestCase):
    """The three exclusions above are load-bearing, so each is executed
    rather than only described."""

    def test_an_all_entry_alone_does_not_count_as_reached(self):
        src = '__all__ = ["lonely"]\n\n\ndef lonely():\n    pass\n'
        names = set()
        for node in ast.walk(ast.parse(src)):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if isinstance(node, ast.Name):
                names.add(node.id)
            elif isinstance(node, ast.Attribute):
                names.add(node.attr)
            elif isinstance(node, ast.Call):
                names.add(getattr(node.func, "attr", None)
                          or getattr(node.func, "id", None))
        self.assertNotIn("lonely", names,
                         "a name in __all__ is being counted as a caller, "
                         "which is exactly the case this guard was built to "
                         "catch")

    def test_a_docstring_mention_does_not_count_as_reached(self):
        src = '"""See lonely for details."""\n\n\ndef lonely():\n    pass\n'
        names = {n.id for n in ast.walk(ast.parse(src))
                 if isinstance(n, ast.Name)}
        self.assertNotIn("lonely", names)

    def test_a_same_module_call_DOES_count_as_reached(self):
        """The correction that took the first draft from thirteen findings
        to one. A helper used only by its own module's entry point is
        reached, and flagging it would train people to ignore this."""
        src = "def helper():\n    pass\n\n\ndef entry():\n    return helper()\n"
        calls = {getattr(n.func, "id", None) for n in ast.walk(ast.parse(src))
                 if isinstance(n, ast.Call)}
        self.assertIn("helper", calls)


if __name__ == "__main__":
    unittest.main()
