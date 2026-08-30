"""DECLARATION HYGIENE for `resolve_partial`'s exits. NOT the obligations.

WHAT THIS FILE CLAIMED FOR THREE ROUNDS, AND WHY THE CLAIM WAS WRONG.
It said it enforced three obligations -- that `already_sealed` had read
FINAL, that nothing destroyed a `.partial`, that `retry_permitted` had
preserved something. Rounds 3, 4 and 5 each walked through the then-current
version, and round 5's three counter-examples ended the argument:

    existing = ((final.read_bytes, intended)[1] if incident_id == "..."
                else final.read_bytes())     -> text passes, reads nothing
    (out / preserved).write_bytes(intended[:0])
                                             -> allowed callee, empties the file
    an early `return path.name` in `_preserve`
                                             -> the rename never happens

None of those is a syntax bug to be pattern-matched away. **"This path read
FINAL before answering" is a RUNTIME property, and for any shape a checker
demands, the set of expressions satisfying the shape while violating the
semantics is infinite.** Five rounds of tightening the shape was five
rounds of solving the wrong problem.

SO THE CLAIM IS NARROWED TO WHAT IS GENUINELY SYNTACTIC: a new exit cannot
appear without being declared. That is real, useful, and checkable -- it
forces an author to write the path down and a reviewer to see it.

THE OBLIGATIONS MOVED to `test_resolve_partial_observed_behaviour.py`,
which wraps the real filesystem calls, drives the real function, and
asserts on what was actually done. All three round-5 counter-examples fail
there, each named for what it really did.

WHAT REMAINS HERE, and it still earns its place:

1. THE EXIT LIST IS ORDERED AND CLOSED. Exits are compared element by
   element, never as a set -- round 4 walked a second `already_sealed`
   path through a set that deduplicated it.
2. THE CALL WORLD IS CLOSED BY SHAPE. `Name(...)` and `x.attr(...)` with
   enumerated callees; a callee that is a Call, Subscript or Lambda is
   refused. This does NOT close effects -- round 5 proved that with an
   allowed `write_bytes` -- and no longer pretends to.
3. THE STATEMENT WORLD IS CLOSED. An unrecognised statement type fails
   loudly rather than being walked past.
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
    # REGENERATED 2026-08-30 after round 8. The walker now FORKS THE
    # REMAINDER at every branch that falls through, so two branches that
    # rejoin no longer share one declared exit. That is why `promote`,
    # `supplement_partial_verify` and the post-promotion verify each appear
    # TWICE: once reached with a byte-identical residue already staged, once
    # reached having staged the bytes here. Sol proved those two were
    # indistinguishable, and that deleting one scenario left coverage green.
    #
    # 12 entries became 17. NONE of the new ones is a new code path -- they
    # were always executable and were being counted as one.
    ("raise", "filename_not_a_plain_name",
     'VIA _require_plain_name'),
    ("raise", "filename_not_a_plain_name",
     'VIA _require_plain_name'),
    ("return", "already_sealed",
     'final.exists() AND existing == intended'),
    ("raise", "supplement_seal_conflict",
     'final.exists() AND NOT(existing == intended)'),
    ("raise", "divergent_partial_exists",
     'NOT(final.exists()) AND partial.exists() AND residue != '
     'intended AND VIA _preserve'),
    ("raise", "incident_id_malformed",
     'NOT(final.exists()) AND partial.exists() AND residue != '
     'intended AND VIA _preserve -> _divergent_name'),
    ("return", "retry_permitted",
     'NOT(final.exists()) AND partial.exists() AND residue != '
     'intended'),
    ("raise", "divergent_partial_exists",
     'NOT(final.exists()) AND partial.exists() AND NOT(residue '
     '!= intended) AND partial.read_bytes() != intended AND '
     'VIA _preserve'),
    ("raise", "incident_id_malformed",
     'NOT(final.exists()) AND partial.exists() AND NOT(residue '
     '!= intended) AND partial.read_bytes() != intended AND '
     'VIA _preserve -> _divergent_name'),
    ("raise", "supplement_partial_verify",
     'NOT(final.exists()) AND partial.exists() AND NOT(residue '
     '!= intended) AND partial.read_bytes() != intended'),
    ("raise", "supplement_post_promotion_verify",
     'NOT(final.exists()) AND partial.exists() AND NOT(residue '
     '!= intended) AND NOT(partial.read_bytes() != intended) '
     'AND final.read_bytes() != intended'),
    ("return", "promote",
     'NOT(final.exists()) AND partial.exists() AND NOT(residue '
     '!= intended) AND NOT(partial.read_bytes() != intended) '
     'AND NOT(final.read_bytes() != intended)'),
    ("raise", "divergent_partial_exists",
     'NOT(final.exists()) AND NOT(partial.exists()) AND '
     'partial.read_bytes() != intended AND VIA _preserve'),
    ("raise", "incident_id_malformed",
     'NOT(final.exists()) AND NOT(partial.exists()) AND '
     'partial.read_bytes() != intended AND VIA _preserve -> '
     '_divergent_name'),
    ("raise", "supplement_partial_verify",
     'NOT(final.exists()) AND NOT(partial.exists()) AND '
     'partial.read_bytes() != intended'),
    ("raise", "supplement_post_promotion_verify",
     'NOT(final.exists()) AND NOT(partial.exists()) AND '
     'NOT(partial.read_bytes() != intended) AND '
     'final.read_bytes() != intended'),
    ("return", "promote",
     'NOT(final.exists()) AND NOT(partial.exists()) AND '
     'NOT(partial.read_bytes() != intended) AND '
     'NOT(final.read_bytes() != intended)'),
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
    # ADDED 2026-08-30 as a deliberate act, not to silence a failure:
    # round 7 disproved the "every write lands under out_dir" claim with
    # `resolve_partial(out, "../escaped.json", ...)`, and this is the
    # refusal that makes the claim true. It only reads and raises.
    "_require_plain_name",
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
            # The RAISE line inside the helper travels too, added 2026-08-30.
            # One call site can reach two different raises in the same helper
            # (`_require_plain_name` refuses an unnamed path and a forbidden
            # character from two statements), and those are two paths. The
            # call-site line alone collapses them, which is the same shape as
            # the collapse round 7 found one level up.
            out.append((node.exc.args[0].value, path, node.lineno))
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


def _always_exits(body):
    """Whether every path through `body` leaves the function.

    Only the LAST statement is consulted, plus the both-branches case for a
    trailing `if`. That is exact for a loop-free function whose statement
    world is closed -- which `test_the_target_is_still_loop_free` and the
    UNDERSTOOD tuple both enforce -- and it fails in the SAFE direction
    anyway: judging an exiting branch as falling through duplicates a
    declared path that nothing can execute, which the coverage assertion
    reports rather than hides."""
    if not body:
        return False
    last = body[-1]
    if isinstance(last, (ast.Return, ast.Raise)):
        return True
    if isinstance(last, ast.If):
        return _always_exits(last.body) and _always_exits(last.orelse)
    return False


class _PathWalk:
    """Straight-line + if/else walk carrying per-path bindings."""

    def __init__(self):
        self.exits = []          # ordered, never deduplicated

    def _record(self, kind, name, guards, binds, node=None, raise_line=None,
                lines=()):
        self.exits.append({"kind": kind, "name": name,
                           #: Every statement line on the path that reaches
                           #: this exit. Added 2026-08-30 so a downstream
                           #: instrument can match a declared PATH against
                           #: an executed one -- the exit line alone made
                           #: two branches that rejoin indistinguishable.
                           "lines": tuple(lines),
                           "guard": " AND ".join(guards),
                           "binds": dict(binds), "node": node,
                           #: The raise line INSIDE a helper, when this exit
                           #: came through one. With `node.lineno` (the call
                           #: site) it forms the exit's PATH IDENTITY, which
                           #: `test_resolve_partial_state_diff.py` matches
                           #: real runs against. Round 7's HIGH-1 was that
                           #: instrument having only the NAME to go on.
                           "raise_line": raise_line})

    def _helper_exits(self, stmt, guards, binds, lines=()):
        for node in ast.walk(stmt):
            if not isinstance(node, ast.Call):
                continue
            callee = getattr(node.func, "id", None)
            if callee and callee in _FNS():
                for code, via, raise_line in _raises_of(callee, callee):
                    # The CALL node, added 2026-08-30. A helper exit's identity
                    # is the CALL SITE, not the helper: `_preserve` raises
                    # `divergent_partial_exists` on branch C and again on
                    # branch E, and those are two different paths through
                    # resolve_partial. Round 7 found the state instrument
                    # collapsing exactly that pair, so the line has to travel
                    # with the exit or nothing downstream can tell them apart.
                    self._record("raise", code, guards + ["VIA " + via],
                                 binds, node, raise_line, lines)

    #: Statement types this walk UNDERSTANDS. Everything else is refused
    #: rather than walked past, for the same reason the call world is
    #: closed: round 4 escaped two OPEN-world checks, and a `return` inside
    #: a `try` or a `with` would be invisible to a walk that only recurses
    #: into `if`. Closing the statement world too, before it is the next
    #: finding rather than after.
    UNDERSTOOD = (ast.If, ast.Assign, ast.Return, ast.Raise, ast.Expr,
                  ast.Pass, ast.ImportFrom, ast.Import)

    def walk(self, body, guards, binds, lines=()):
        lines = list(lines)
        for index, stmt in enumerate(body):
            lines.append(stmt.lineno)
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
                # FORK THE REMAINDER, 2026-08-30 (round 8 HIGH).
                #
                # This used to walk both branches and then `continue`, which
                # walked everything AFTER the `if` exactly once, carrying the
                # guards from BEFORE it. Two branches that fall through and
                # rejoin therefore produced ONE declared exit between them.
                # Sol measured the consequence: the "nothing staged, write
                # it" path and the "identical residue already staged, skip
                # the write" path both end at `promote` on the same line, so
                # they shared an identity -- and deleting one of them from
                # the scenario generator left the coverage assertion green.
                #
                # A branch that exits on every path has no remainder. One
                # that falls through carries the rest of the function with
                # it, once per branch, under that branch's guard.
                test = ast.unparse(stmt.test)
                rest = body[index + 1:]
                for branch, guard in ((stmt.body, test),
                                      (stmt.orelse, "NOT(%s)" % test)):
                    tail = (list(branch) if _always_exits(branch)
                            else list(branch) + rest)
                    self.walk(tail, guards + [guard], dict(binds),
                              lines)
                return
            self._helper_exits(stmt, guards, binds, lines)
            if isinstance(stmt, ast.Assign) and isinstance(stmt.targets[0],
                                                           ast.Name):
                binds[stmt.targets[0].id] = ast.unparse(stmt.value)
            elif isinstance(stmt, ast.Return) and stmt.value is not None:
                self._record("return", _action_of(stmt.value), guards,
                             binds, stmt.value, None, lines)
            elif isinstance(stmt, ast.Raise):
                self._record("raise", _action_of(stmt.exc), guards,
                             binds, stmt.exc, None, lines)


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


class TestTheDeclaredShapeOfAlreadySealed(unittest.TestCase):
    """A SHAPE check, and labelled as one since round 5.

    It catches a path whose guard compares nothing, or compares a name
    bound to something with no read in it. It does NOT establish that a
    read happened -- round 5's conditional expression satisfies every
    lexical form of this and reads nothing. That obligation is owned by
    `test_resolve_partial_observed_behaviour.py`."""

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


class TestTheDeclaredShapeOfRetryPermitted(unittest.TestCase):
    """Shape only, same caveat: it checks that a name bound from
    `_preserve` is passed. Whether the file it names still holds the
    residue is observed elsewhere."""

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


class TestTheCallWorldIsClosedBySHAPE(unittest.TestCase):
    """Shapes, not effects -- round 5 emptied a preserved file with an
    ALLOWED `write_bytes`, so this closes routes and not consequences.

    Round 4's second HIGH. A blacklist of destructive NAMES is an open
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
