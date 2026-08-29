"""A PATH-SENSITIVE, CLOSED-WORLD contract over `resolve_partial`'s exits.

ROUND 4 HOLD, and the objection named the root cause exactly:

    合同推导是路径不敏感的集合，并且只识别有限的调用语法；
    它仍会把"同形但语义不同的路径"折叠掉。

Both HIGHs reproduced at 12/12 GREEN before anything was changed:

    a SECOND `already_sealed` path whose guard reads identically but whose
    `existing` is bound to `intended` rather than to a read of FINAL
    -> the set DEDUPLICATED it away, and the provenance check only proved
       that SOME line in the function reads FINAL, not that THIS path does

    `next(iter((Path.unlink,)))(out / preserved)` after `_preserve`
    -> the destructive call is reached as a VALUE, so a check that reads
       call names never sees it; the row still says `preserved_as=...`
       while the file is gone

TWO ROOT CAUSES, and this file attacks those rather than the two examples.

1. PATH-INSENSITIVE, SET-BASED. Exits are now an ORDERED LIST, compared
   element by element, and each carries the BINDINGS VISIBLE ON ITS OWN
   PATH. Two identically-shaped paths are two entries, and obligation (a)
   is answered against this path's bindings, not the function's.

   The target is straight-line plus if/else with no loops, so a linear
   walk that copies bindings per branch is exact rather than approximate.
   `test_the_target_is_still_loop_free` keeps that premise honest.

2. OPEN-WORLD CALL RECOGNITION. Blacklisting destructive NAMES is an open
   world -- round 4 escaped it twice. The call world is now CLOSED: every
   call inside `resolve_partial` and its helpers must match one of a small
   set of permitted SHAPES with a permitted callee. A call whose `func` is
   itself a call, a subscript, a lambda, or anything else is refused
   without needing to know what it resolves to.
"""

import ast
import io
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RUNNER = REPO / "src" / "itsf" / "mc" / "supplement_runner.py"
HELPERS = ("_preserve", "_divergent_name")

#: EVERY exit, IN TRAVERSAL ORDER. A list, never a set: two paths that look
#: identical are two exits, and collapsing them is what round 4 walked
#: through.
DECLARED_EXITS = [
    ("return", "already_sealed", "final.exists() AND existing == intended"),
    ("raise", "supplement_seal_conflict", "final.exists()"),
    ("raise", "divergent_partial_exists",
     "partial.exists() AND residue != intended AND VIA _preserve"),
    ("raise", "incident_id_malformed",
     "partial.exists() AND residue != intended AND VIA _preserve -> "
     "_divergent_name"),
    ("return", "retry_permitted", "partial.exists() AND residue != intended"),
    ("raise", "divergent_partial_exists",
     "partial.read_bytes() != intended AND VIA _preserve"),
    ("raise", "incident_id_malformed",
     "partial.read_bytes() != intended AND VIA _preserve -> _divergent_name"),
    ("raise", "supplement_partial_verify", "partial.read_bytes() != intended"),
    ("raise", "supplement_post_promotion_verify",
     "final.read_bytes() != intended"),
    ("return", "promote", ""),
]

#: THE CLOSED CALL WORLD. Anything not matching one of these shapes with a
#: permitted callee is refused, so a destructive call cannot arrive by a
#: route nobody enumerated.
#: ADDING TO EITHER LIST IS A DELIBERATE ACT, not a way to silence this
#: test. Each name here is one the reviewer should be able to see and
#: object to; a name added to make a failure go away is how a closed world
#: becomes an open one again.
ALLOWED_NAME_CALLS = frozenset({
    "PartialAction", "SupplementRunnerError", "Path", "str", "len",
    "_preserve", "_divergent_name",
    "repr",                      # _divergent_name's refusal message
})
ALLOWED_ATTR_CALLS = frozenset({
    "exists", "read_bytes", "write_bytes", "removesuffix", "format",
    "replace", "resolve", "is_dir", "is_file",
    "match",                     # sc.INCIDENT_RE.match — a read, not a write
})


def _module_functions():
    tree = ast.parse(io.open(RUNNER, encoding="utf-8").read())
    return {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}


def _FNS():
    """Re-read on every call, NOT cached at import.

    Round 4's §4 listed "`_MODULE_FUNCTIONS` is evaluated once at import"
    as a weakness and then did nothing about it -- and round 4's whole
    lesson is that LISTING a weakness is not HANDLING one. A cached
    snapshot means the contract can be checked against a file that is no
    longer the file on disk.
    """
    return _module_functions()


def _raises_of(name, path, seen=None):
    seen = seen or set()
    fns = _FNS()
    if name in seen or name not in fns:
        return []
    seen.add(name)
    out = []
    for node in ast.walk(fns[name]):
        if (isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call)
                and node.exc.args
                and isinstance(node.exc.args[0], ast.Constant)):
            out.append((node.exc.args[0].value, path))
        if isinstance(node, ast.Call):
            callee = getattr(node.func, "id", None)
            if callee and callee in fns and callee != name:
                out += _raises_of(callee, path + " -> " + callee, seen)
    return out


def _action_of(call):
    if not isinstance(call, ast.Call):
        return ast.unparse(call)[:40]
    for arg in call.args[:1]:
        if isinstance(arg, ast.Constant):
            return arg.value
    for kw in call.keywords:
        if kw.arg == "action" and isinstance(kw.value, ast.Constant):
            return kw.value.value
    return ast.unparse(call.func)


class _PathWalk:
    """Straight-line + if/else walk carrying per-path bindings."""

    def __init__(self):
        self.exits = []          # ordered, never deduplicated

    def _record(self, kind, name, guards, binds, node=None):
        self.exits.append({"kind": kind, "name": name,
                           "guard": " AND ".join(guards),
                           "binds": dict(binds), "node": node})

    def _helper_exits(self, stmt, guards, binds):
        for node in ast.walk(stmt):
            if not isinstance(node, ast.Call):
                continue
            callee = getattr(node.func, "id", None)
            if callee and callee in _FNS():
                for code, via in _raises_of(callee, callee):
                    self._record("raise", code, guards + ["VIA " + via], binds)

    #: Statement types this walk UNDERSTANDS. Everything else is refused
    #: rather than walked past, for the same reason the call world is
    #: closed: round 4 escaped two OPEN-world checks, and a `return` inside
    #: a `try` or a `with` would be invisible to a walk that only recurses
    #: into `if`. Closing the statement world too, before it is the next
    #: finding rather than after.
    UNDERSTOOD = (ast.If, ast.Assign, ast.Return, ast.Raise, ast.Expr,
                  ast.Pass, ast.ImportFrom, ast.Import)

    def walk(self, body, guards, binds):
        for stmt in body:
            if not isinstance(stmt, self.UNDERSTOOD):
                raise AssertionError(
                    "resolve_partial contains a %s at line %d. This walk "
                    "understands only %s, so a `return` inside it would be "
                    "INVISIBLE -- the same open-world defect round 4 used "
                    "twice. Teach the walk that statement type (and its "
                    "path semantics) before using it here."
                    % (type(stmt).__name__, stmt.lineno,
                       ", ".join(t.__name__ for t in self.UNDERSTOOD)))
            if isinstance(stmt, ast.Assign) and not isinstance(
                    stmt.targets[0], ast.Name):
                raise AssertionError(
                    "resolve_partial binds something other than a plain name "
                    "at line %d (%s). Tuple unpacking and attribute targets "
                    "are not tracked, so obligation (a)'s provenance would "
                    "silently miss them." % (stmt.lineno,
                                             ast.unparse(stmt)[:60]))
            if isinstance(stmt, ast.If):
                self.walk(stmt.body,
                          guards + [ast.unparse(stmt.test)], dict(binds))
                self.walk(stmt.orelse,
                          guards + ["NOT(%s)" % ast.unparse(stmt.test)],
                          dict(binds))
                continue
            self._helper_exits(stmt, guards, binds)
            if isinstance(stmt, ast.Assign) and isinstance(stmt.targets[0],
                                                           ast.Name):
                binds[stmt.targets[0].id] = ast.unparse(stmt.value)
            elif isinstance(stmt, ast.Return) and stmt.value is not None:
                self._record("return", _action_of(stmt.value), guards, binds,
                             stmt.value)
            elif isinstance(stmt, ast.Raise):
                self._record("raise", _action_of(stmt.exc), guards, binds,
                             stmt.exc)


def _resolve_partial():
    fns = [n for n in ast.walk(ast.parse(io.open(RUNNER, encoding="utf-8")
                                         .read()))
           if isinstance(n, ast.FunctionDef) and n.name == "resolve_partial"]
    assert len(fns) == 1, "resolve_partial is gone or duplicated"
    return fns[0]


def _exits():
    walker = _PathWalk()
    walker.walk(_resolve_partial().body, [], {})
    return walker.exits


class TestTheExitLISTIsClosed(unittest.TestCase):

    def test_the_declared_exits_match_ONE_FOR_ONE_in_order(self):
        found = [(e["kind"], e["name"], e["guard"]) for e in _exits()]
        self.assertEqual(
            DECLARED_EXITS, found,
            "resolve_partial's exits changed.\n  declared: %s\n  found:    %s"
            "\n\nCompared as an ORDERED LIST, not a set: round 4 walked a "
            "second `already_sealed` path straight through a set that "
            "deduplicated it against the first."
            % (DECLARED_EXITS, found))

    def test_two_identically_shaped_paths_are_two_entries(self):
        """The dedup defect, executed on the derivation itself rather than
        argued about."""
        walker = _PathWalk()
        tree = ast.parse("def f():\n"
                         "    if a:\n"
                         "        return 1\n"
                         "    if a:\n"
                         "        return 1\n")
        walker.walk(tree.body[0].body, [], {})
        self.assertEqual(2, len(walker.exits))

    def test_the_derivation_is_not_looking_at_an_empty_function(self):
        self.assertGreaterEqual(len(_exits()), 10)

    def test_the_target_is_still_loop_free(self):
        """The premise for path-sensitivity. A loop would make a linear
        walk an approximation, and the obligations below would be claiming
        more than they check."""
        for node in ast.walk(_resolve_partial()):
            with self.subTest(node=type(node).__name__):
                self.assertNotIsInstance(node, (ast.For, ast.While,
                                                ast.AsyncFor))


class TestObligationA_isAnsweredOnTHISPath(unittest.TestCase):
    """Round 4's first HIGH. The old check proved SOME line in the function
    read FINAL; it did not prove this path did."""

    def test_every_already_sealed_exit_compares_a_name_read_from_FINAL(self):
        seen = 0
        for exit_ in _exits():
            if exit_["name"] != "already_sealed":
                continue
            seen += 1
            guard = exit_["guard"]
            with self.subTest(guard=guard):
                self.assertIn("== intended", guard,
                              "no comparison against intended on this path")
                left = guard.split("== intended")[0].split("AND")[-1].strip()
                source = exit_["binds"].get(left)
                self.assertIsNotNone(
                    source,
                    "%r is compared to intended but is not bound anywhere on "
                    "this path" % left)
                self.assertIn(
                    "read_bytes", source,
                    "on THIS path %r is bound to %r, which is not a read. "
                    "Round 4 walked exactly this through: `existing = "
                    "intended` satisfies a function-wide provenance check "
                    "and reads nothing." % (left, source))
                self.assertIn("final", source,
                              "%r was read, but not from the FINAL path"
                              % left)
        self.assertGreaterEqual(seen, 1, "no already_sealed exit was checked")


class TestObligationC_isAnsweredOnTHISPath(unittest.TestCase):

    def test_every_retry_permitted_exit_preserves_on_its_own_path(self):
        seen = 0
        for exit_ in _exits():
            if exit_["name"] != "retry_permitted":
                continue
            seen += 1
            kwargs = {kw.arg: kw.value for kw in exit_["node"].keywords}
            with self.subTest(guard=exit_["guard"]):
                self.assertIn("preserved_as", kwargs)
                value = kwargs["preserved_as"]
                self.assertIsInstance(value, ast.Name,
                                      "preserved_as is a literal, not a name")
                source = exit_["binds"].get(value.id)
                self.assertIsNotNone(source,
                                     "%s is not bound on this path" % value.id)
                self.assertIn("_preserve(", source)
        self.assertGreaterEqual(seen, 1)


class TestObligationB_theCallWorldIsCLOSED(unittest.TestCase):
    """Round 4's second HIGH. A blacklist of destructive NAMES is an open
    world: `next(iter((Path.unlink,)))(...)` reaches the deletion as a
    VALUE and no name check can see it. So the permitted shapes are
    enumerated instead, and everything else is refused without needing to
    know what it resolves to."""

    def _functions(self):
        yield "resolve_partial", _resolve_partial()
        fns = _FNS()
        for name in HELPERS:
            yield name, fns[name]

    def test_every_call_matches_a_permitted_SHAPE(self):
        offenders = []
        for owner, fn in self._functions():
            for node in ast.walk(fn):
                if not isinstance(node, ast.Call):
                    continue
                func = node.func
                if isinstance(func, ast.Name):
                    if func.id not in ALLOWED_NAME_CALLS:
                        offenders.append("%s: %s (name not permitted)"
                                         % (owner, ast.unparse(node)[:60]))
                elif isinstance(func, ast.Attribute):
                    if func.attr not in ALLOWED_ATTR_CALLS:
                        offenders.append("%s: %s (attribute not permitted)"
                                         % (owner, ast.unparse(node)[:60]))
                else:
                    offenders.append(
                        "%s: %s (callee is a %s -- not a plain name or "
                        "attribute)" % (owner, ast.unparse(node)[:60],
                                        type(func).__name__))
        self.assertEqual(
            [], offenders,
            "a call outside the closed world: %s\n\nThe permitted shapes are "
            "`Name(...)` and `x.attr(...)` with an enumerated callee. "
            "Anything else -- a call of a call, a subscript, a lambda -- is "
            "refused, because the contract cannot see what it resolves to."
            % offenders)

    def test_no_destructive_callable_is_even_NAMED(self):
        """Belt and braces: the shape rule already refuses reaching one,
        but a bare reference to `Path.unlink` has no business here at all."""
        banned = ("unlink", "remove", "rmtree", "rmdir", "removedirs")
        offenders = []
        for owner, fn in self._functions():
            for node in ast.walk(fn):
                if isinstance(node, ast.Attribute) and node.attr in banned:
                    offenders.append("%s: %s" % (owner, ast.unparse(node)))
                if isinstance(node, ast.Name) and node.id in banned:
                    offenders.append("%s: %s" % (owner, node.id))
        self.assertEqual([], offenders,
                         "a destructive callable is named: %s" % offenders)

    def test_the_shape_check_is_looking_at_real_calls(self):
        total = sum(1 for _, fn in self._functions()
                    for n in ast.walk(fn) if isinstance(n, ast.Call))
        self.assertGreater(total, 10,
                           "only %d calls found across the three functions"
                           % total)

    def test_the_only_move_is_a_RENAME(self):
        moves = [ast.unparse(n) for _, fn in self._functions()
                 for n in ast.walk(fn) if isinstance(n, ast.Call)
                 and getattr(n.func, "attr", "") in ("replace", "rename")]
        self.assertTrue(moves, "nothing moves the .partial at all")
        for move in moves:
            with self.subTest(move=move):
                self.assertTrue(move.startswith("os.replace"), move)


if __name__ == "__main__":
    unittest.main()
