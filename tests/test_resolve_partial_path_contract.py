"""A CLOSED contract over `resolve_partial`'s exit paths.

WHY IT EXISTS — fresh Sol, c-build-2-wording-r3, VERDICT=HOLD, HIGH finding.
Reproduced before being accepted, and the first reproduction was WRONG:
mutations that fired on the filenames the tests use went red, which proved
nothing. Sol's mutations guard the new path on a condition no test
exercises. Redone faithfully, both go 59/59 GREEN:

    a NEW branch that writes FINAL and returns `already_sealed` without
    ever reading it back                                     -> 59/59 green
    a NEW branch that deletes the `.partial` via
    `getattr(p, "unlink")()` and returns `retry_permitted`    -> 59/59 green

The existing guards enumerate the paths that EXIST and test the behaviours
those paths produce. Neither notices a path being ADDED. Sol's words for it:
"这些测试再次把'我列出的现有路径'当成'所有可能路径'" — and its instruction
was explicit: do not just append these two counter-examples as new cases.

WHAT THIS DOES INSTEAD. It does not try to understand a new path. It
refuses to let one appear silently: every exit is derived from the AST as
(kind, action-or-code, guard source), and the derived set must equal the
DECLARED set below. Add a branch and this goes red until its author writes
it down and answers the three obligations. That is the closed
return/exception contract the HOLD asked for.

THE THREE OBLIGATIONS, from CRITERION_1:

    (a) a path that returns `already_sealed` must have READ the final file
        and compared it to `intended`
    (b) no path may destroy a `.partial` — `SILENT_DELETE_FORBIDDEN=YES`
    (c) a path that returns `retry_permitted` must name what it preserved

Each is checked structurally below, so a declared path still cannot lie.
"""

import ast
import io
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RUNNER = REPO / "src" / "itsf" / "mc" / "supplement_runner.py"

#: EVERY exit of `resolve_partial`, declared. (kind, name, guard)
#: `kind`  "return" | "raise"
#: `name`  the PartialAction action literal, or the error code
#: `guard` the conjunction of enclosing `if` tests, as source
#:
#: Adding a branch to the function makes the derived set differ from this
#: one, and the test names what appeared. Answering the obligations means
#: adding the entry AND satisfying the structural checks further down.
DECLARED_EXITS = {
    ("return", "already_sealed",
     "final.exists() AND existing == intended"),
    ("raise", "supplement_seal_conflict",
     "final.exists()"),
    ("return", "retry_permitted",
     "partial.exists() AND residue != intended"),
    ("raise", "supplement_partial_verify",
     "partial.read_bytes() != intended"),
    ("raise", "supplement_post_promotion_verify",
     "final.read_bytes() != intended"),
    ("return", "promote", ""),
}


class _Exits(ast.NodeVisitor):
    """Every return/raise with the conjunction of `if` tests above it."""

    def __init__(self):
        self.stack = []
        self.found = set()
        self.nodes = []

    def _guard(self):
        return " AND ".join(self.stack)

    def visit_If(self, node):
        self.stack.append(ast.unparse(node.test))
        for child in node.body:
            self.visit(child)
        self.stack.pop()
        self.stack.append("NOT(%s)" % ast.unparse(node.test))
        for child in node.orelse:
            self.visit(child)
        self.stack.pop()

    def _name_of(self, call):
        if not isinstance(call, ast.Call):
            return ast.unparse(call)[:40]
        for arg in call.args[:1]:
            if isinstance(arg, ast.Constant):
                return arg.value
        for kw in call.keywords:
            if kw.arg == "action" and isinstance(kw.value, ast.Constant):
                return kw.value.value
        return ast.unparse(call.func)

    def visit_Return(self, node):
        if node.value is not None:
            self.found.add(("return", self._name_of(node.value), self._guard()))
            self.nodes.append(("return", node, self._guard()))

    def visit_Raise(self, node):
        self.found.add(("raise", self._name_of(node.exc), self._guard()))
        self.nodes.append(("raise", node, self._guard()))


def _resolve_partial():
    tree = ast.parse(io.open(RUNNER, encoding="utf-8").read())
    fns = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
           and n.name == "resolve_partial"]
    assert len(fns) == 1, "resolve_partial is gone or duplicated"
    return fns[0]


def _exits():
    walker = _Exits()
    walker.visit(_resolve_partial())
    return walker


class TestTheExitSetIsCLOSED(unittest.TestCase):
    """The half that makes a new path impossible to add quietly."""

    def test_the_declared_exits_are_exactly_the_real_ones(self):
        found = _exits().found
        appeared = sorted(found - DECLARED_EXITS)
        vanished = sorted(DECLARED_EXITS - found)
        self.assertEqual(
            ([], []), (appeared, vanished),
            "resolve_partial's exit set changed.\n"
            "  APPEARED: %s\n  VANISHED: %s\n\n"
            "A new exit is not a test failure to silence -- it is the "
            "contract asking for its obligations. Add it to DECLARED_EXITS "
            "and make it satisfy (a) it reads FINAL before answering "
            "already_sealed, (b) it destroys no .partial, (c) it names what "
            "it preserved before answering retry_permitted."
            % (appeared, vanished))

    def test_the_derivation_is_not_looking_at_an_empty_function(self):
        """A rename or a parse change would make the set empty, and empty
        equals empty is the vacuous pass this whole file exists to stop."""
        self.assertGreaterEqual(len(_exits().found), 6)


class TestObligationA_alreadySealedMustHaveREAD(unittest.TestCase):

    def test_every_already_sealed_exit_compared_against_intended(self):
        for kind, name, guard in _exits().found:
            if name != "already_sealed":
                continue
            with self.subTest(guard=guard):
                self.assertIn(
                    "== intended", guard,
                    "a path answers `already_sealed` without its guard "
                    "comparing anything to `intended`. That is Sol's "
                    "counter-example (a): FINAL written and never read back.")

    def test_and_the_thing_compared_was_READ_from_the_final_file(self):
        """`== intended` alone is not enough -- the left side has to be
        bytes that came off disk, not a variable someone set."""
        fn = _resolve_partial()
        reads = {}
        for node in ast.walk(fn):
            if (isinstance(node, ast.Assign)
                    and isinstance(node.value, ast.Call)
                    and getattr(node.value.func, "attr", "") == "read_bytes"
                    and isinstance(node.targets[0], ast.Name)):
                reads[node.targets[0].id] = ast.unparse(node.value)
        self.assertTrue(reads, "nothing in resolve_partial reads bytes")
        for kind, name, guard in _exits().found:
            if name != "already_sealed":
                continue
            left = guard.split("== intended")[0].split("AND")[-1].strip()
            with self.subTest(compared=left):
                self.assertIn(left, reads,
                              "%r is compared to intended but was never "
                              "read from disk in this function" % left)
                self.assertIn("final", reads[left],
                              "%r was read, but not from the FINAL path" % left)


class TestObligationB_nothingDestroysAPartial(unittest.TestCase):
    """`SILENT_DELETE_FORBIDDEN=YES`. Sol's counter-example (b) reached the
    deletion through `getattr(p, "unlink")()`, so a check for the attribute
    name alone would have missed it."""

    DESTRUCTIVE = ("unlink", "remove", "rmtree", "removedirs", "rmdir")

    def _calls(self, fn):
        for node in ast.walk(fn):
            if isinstance(node, ast.Call):
                yield node

    def test_no_direct_destructive_call(self):
        offenders = [ast.unparse(c)[:70] for c in self._calls(_resolve_partial())
                     if getattr(c.func, "attr", "") in self.DESTRUCTIVE
                     or getattr(c.func, "id", "") in self.DESTRUCTIVE]
        self.assertEqual([], offenders,
                         "resolve_partial destroys bytes: %s" % offenders)

    def test_no_destructive_call_reached_through_getattr(self):
        """The exact shape of Sol's counter-example (b)."""
        offenders = []
        for call in self._calls(_resolve_partial()):
            if getattr(call.func, "id", "") != "getattr":
                continue
            for arg in call.args[1:2]:
                if (isinstance(arg, ast.Constant)
                        and arg.value in self.DESTRUCTIVE):
                    offenders.append(ast.unparse(call)[:70])
        self.assertEqual([], offenders,
                         "a destructive call is reached by name: %s"
                         % offenders)

    def test_nor_through_any_dynamic_attribute_at_all(self):
        """Wider than the two shapes seen: ANY `getattr` on a path-like
        name inside this function is refused, because the argument may be
        computed and this check cannot evaluate it."""
        offenders = [ast.unparse(c)[:70] for c in self._calls(_resolve_partial())
                     if getattr(c.func, "id", "") == "getattr"]
        self.assertEqual(
            [], offenders,
            "resolve_partial reaches an attribute dynamically: %s\n"
            "The contract cannot see what a computed name resolves to, so "
            "the whole construct is refused here rather than pattern-matched."
            % offenders)

    def test_the_only_move_is_a_RENAME(self):
        """Preservation, not destruction: bytes move aside."""
        moves = [ast.unparse(c) for c in self._calls(_resolve_partial())
                 if getattr(c.func, "attr", "") in ("replace", "rename")]
        self.assertTrue(moves, "nothing moves the .partial at all")
        for move in moves:
            with self.subTest(move=move):
                self.assertTrue(move.startswith("os.replace"), move)


class TestObligationC_retryMustNameWhatItPreserved(unittest.TestCase):

    def test_every_retry_permitted_exit_passes_preserved_as(self):
        for kind, node, guard in _exits().nodes:
            if kind != "return" or not isinstance(node.value, ast.Call):
                continue
            name = _Exits()._name_of(node.value)
            if name != "retry_permitted":
                continue
            kwargs = {kw.arg for kw in node.value.keywords}
            with self.subTest(guard=guard):
                self.assertIn(
                    "preserved_as", kwargs,
                    "a path answers `retry_permitted` without naming what "
                    "it preserved. That is Sol's counter-example (c): the "
                    "residue is gone and the row says a retry is fine.")

    def test_the_preserved_name_came_from_the_preserving_helper(self):
        """`preserved_as=""` would satisfy the check above and preserve
        nothing."""
        fn = _resolve_partial()
        preserved = {}
        for node in ast.walk(fn):
            if (isinstance(node, ast.Assign)
                    and isinstance(node.value, ast.Call)
                    and getattr(node.value.func, "id", "") == "_preserve"
                    and isinstance(node.targets[0], ast.Name)):
                preserved[node.targets[0].id] = True
        self.assertTrue(preserved, "_preserve is never called")
        for kind, node, guard in _exits().nodes:
            if kind != "return" or not isinstance(node.value, ast.Call):
                continue
            if _Exits()._name_of(node.value) != "retry_permitted":
                continue
            for kw in node.value.keywords:
                if kw.arg == "preserved_as":
                    with self.subTest(value=ast.unparse(kw.value)):
                        self.assertIsInstance(
                            kw.value, ast.Name,
                            "preserved_as is a literal, not a name bound "
                            "from _preserve")
                        self.assertIn(kw.value.id, preserved)


class TestTheContractCoversTheHELPERS_too(unittest.TestCase):
    """`resolve_partial` delegates the move to `_preserve`. A contract that
    stopped at the function boundary would let the deletion move one level
    down -- the same narrowness that produced tonight's other findings."""

    HELPERS = ("_preserve", "_divergent_name")

    def test_no_helper_destroys_anything_either(self):
        tree = ast.parse(io.open(RUNNER, encoding="utf-8").read())
        offenders = []
        for fn in ast.walk(tree):
            if not (isinstance(fn, ast.FunctionDef)
                    and fn.name in self.HELPERS):
                continue
            for node in ast.walk(fn):
                if not isinstance(node, ast.Call):
                    continue
                name = (getattr(node.func, "attr", "")
                        or getattr(node.func, "id", ""))
                if name in ("unlink", "remove", "rmtree", "getattr"):
                    offenders.append("%s: %s" % (fn.name,
                                                 ast.unparse(node)[:60]))
        self.assertEqual([], offenders,
                         "a helper destroys or dynamically reaches: %s"
                         % offenders)

    def test_both_helpers_still_exist(self):
        """The premise. A renamed helper would empty the scan above."""
        tree = ast.parse(io.open(RUNNER, encoding="utf-8").read())
        names = {n.name for n in ast.walk(tree)
                 if isinstance(n, ast.FunctionDef)}
        for helper in self.HELPERS:
            with self.subTest(helper=helper):
                self.assertIn(helper, names)


if __name__ == "__main__":
    unittest.main()
