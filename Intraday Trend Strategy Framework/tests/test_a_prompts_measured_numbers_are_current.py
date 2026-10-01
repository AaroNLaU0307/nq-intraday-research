"""A number a LIVE packet quotes must still be the number today.

THE SHAPE THIS EXISTS FOR, which bit three rounds running and was
true-when-written every time:

    R6  "现在还包 builtins.open / os.open / shutil.*" -- I wrote the PLAN into
        the packet, went to fix two other items, and never came back.
    R7  "调用观测器 23/23 全绿" -- true when measured. I then deleted the
        hand-typed coverage test from that file and never revisited the
        sentence. Sol counted 22.
    R6  The reviewed-set section was numbered as something else, so the pin
        and the transport table were simply absent.

None was a lie in the moment. Each was a claim that stopped being true while
the document stood still.

HOW THIS CHECKS IT, AND WHY NOT THE OBVIOUS WAY. The obvious way is to run
the command the packet quotes. I wrote that version, and it took the machine
down TWICE on 2026-08-30: the round-8 packet quotes a command that runs this
file, so each level re-read the packet and spawned the next, 41 python
processes deep. My first fix guarded the packet scan but not the vacuity test
beside it, which spawned just the same -- the second crash.

So the subprocess is gone entirely, and the claim is decomposed instead:

    "that file has N tests"     <- counted here, statically, from the AST
    "and they pass"             <- established by THIS SUITE, which runs them

Together those are the quoted sentence, and neither half needs to execute
anything. Removing the capability is what closes the recursion; a third
guard on top of a fork bomb would have been the wrong shape of answer, and I
had already built two.

WHAT IT DOES NOT CATCH, stated rather than left to be discovered: a platform
skip. `N passed` on a machine where three tests skip is not the collected
count. The ADS guards in `test_resolve_partial_state_diff.py` skip off
Windows, so a Linux run of that file reports fewer passed than collected.
Packets are written and reviewed on the same Windows machine, so the two
agree here -- and if that ever stops being true, this guard says so loudly
rather than quietly.

WHY LIVE ONLY. A RETURNED packet's numbers were true while it was out and the
tree has moved since, by design -- the exemption
`test_a_prompts_range_claim_actually_holds` makes, for the same reason.
"""

import ast
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OPS = REPO / "ops"
LIVE = ("ISSUED", "PREPARED_NOT_ISSUED")
STATUS = re.compile(r"^DELIVERY_STATUS=([A-Z_]+)\s*$", re.M)
#: The convention round 7's packet introduced, matched as written there. A
#: packet using a different shape is not silently skipped --
#: `test_a_live_packet_actually_carries_measured_claims` refuses that.
CLAIM = re.compile(
    r"核验\s+python -m pytest (?P<path>\S+) -q\s*\n"
    r"预期\s+(?P<passed>\d+) passed", re.M)


def live_packets():
    texts = {p: p.read_text(encoding="utf-8")
             for p in sorted(OPS.glob("PROMPT_*.md"))}
    return [p for p, text in texts.items()
            if STATUS.search(text)
            and any("DELIVERY_STATUS=%s" % k in text for k in LIVE)]


class Uncountable(Exception):
    """This file's collected count cannot be established from the AST.

    RAISED RATHER THAN GUESSED, 2026-08-31, after this counter shipped a
    wrong number to a reviewer. `tests/test_registry_boundary.py` carries a
    `@pytest.mark.parametrize` whose argvalues are a NAME, not a literal --
    `_REFUSAL_STUBS`, five entries. The walk counted the function once;
    pytest collects five. 14 against 18, and the packet quoted 14.

    The old docstring said "how many tests pytest would collect", which was
    wider than the code by exactly that gap. A counter that cannot see
    parametrisation must SAY so; silently returning the smaller number is
    the could-not-look / nothing-is-there collapse this repository refuses
    everywhere else -- and here it collapsed inside the guard built to stop
    stale numbers reaching a reviewer."""


def _parametrize_factor(node):
    """How many cases a decorator multiplies a test into.

    A literal list or tuple is countable. A NAME is not, without importing
    the module and running its top level -- which this file will not do."""
    factor = 1
    for dec in getattr(node, "decorator_list", []):
        if not isinstance(dec, ast.Call):
            continue
        name = getattr(dec.func, "attr", None) or getattr(dec.func, "id", None)
        if name != "parametrize":
            continue
        values = dec.args[1] if len(dec.args) > 1 else None
        if isinstance(values, (ast.List, ast.Tuple)):
            factor *= len(values.elts)
        else:
            raise Uncountable(
                "%s is parametrised over %s, which is not a literal; the "
                "number of cases cannot be read from the source"
                % (node.name, ast.unparse(values) if values else "?"))
    return factor


def defined_tests(path):
    """How many test FUNCTIONS are defined -- parametrisation not applied.

    Split out 2026-08-31. `collected_tests` began multiplying by
    parametrisation, and the indentation walk below cannot see cases at all,
    so the two derivations stopped measuring the same thing and started
    disagreeing on files where both were right. Two routes to one number is
    the point; two routes to two different numbers is noise wearing the
    costume of a cross-check."""
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    count = 0
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            count += node.name.startswith("test")
        elif isinstance(node, ast.ClassDef):
            count += sum(
                isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                and child.name.startswith("test")
                for child in node.body)
    return count


def collected_tests(path):
    """How many tests pytest would collect from `path`.

    Module-level `def test_*` plus every `def test_*` inside a class, each
    multiplied by its parametrisation. Read from the AST, so it costs
    nothing and cannot run anything -- and RAISES `Uncountable` rather than
    under-report when the source does not say."""
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    count = 0
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("test"):
                count += _parametrize_factor(node)
        elif isinstance(node, ast.ClassDef):
            for child in node.body:
                if (isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                        and child.name.startswith("test")):
                    count += _parametrize_factor(child)
    return count


def stale_claims(packet):
    """Every quoted number that no longer matches. Empty means current."""
    text = packet.read_text(encoding="utf-8")
    problems = []
    for claim in CLAIM.finditer(text):
        target, quoted = claim.group("path"), int(claim.group("passed"))
        if not (REPO / target).is_file():
            problems.append(
                "%s: %s does not exist, so its command cannot run. A check "
                "that cannot run is not a check -- round 7 shipped one."
                % (packet.name, target))
            continue
        try:
            actual = collected_tests(REPO / target)
        except Uncountable as exc:
            problems.append(
                "%s quotes a number for %s, whose count cannot be read from "
                "the source: %s. Quote a file whose count IS readable, or "
                "quote no number -- a guess that happens to be wrong is what "
                "sent 14 to a reviewer when pytest reports 18."
                % (packet.name, target, exc))
            continue
        if actual != quoted:
            problems.append(
                "%s: claims %d passed for %s, which now holds %d tests. The "
                "number was true when written and is false now -- re-measure "
                "at ISSUE time, never reuse an earlier reading."
                % (packet.name, quoted, target, actual))
    return problems


class TestALivePacketsNumbersAreStillTrue(unittest.TestCase):

    def test_no_live_packet_quotes_a_stale_number(self):
        problems = []
        for packet in live_packets():
            problems += stale_claims(packet)
        self.assertEqual([], problems, "\n  ".join([""] + problems))

    def test_a_live_packet_actually_carries_measured_claims(self):
        """Vacuity, and the one that matters most: a packet that stopped
        using the `核验/预期` shape would make the check above pass over
        nothing while reading as though every number had been verified."""
        for packet in live_packets():
            with self.subTest(packet=packet.name):
                self.assertTrue(
                    CLAIM.search(packet.read_text(encoding="utf-8")),
                    "%s is live but carries no `核验 python -m pytest ... / "
                    "预期 N passed` pair. Either it quotes no measurements, "
                    "or it quotes them in a shape this guard cannot see -- "
                    "which is the same as not checking them." % packet.name)


class TestTheCounterAgreesWithPytest(unittest.TestCase):
    """The static count is only useful if it equals what pytest collects.

    Checked against THIS file and against files with a mix of shapes, so a
    counting bug shows up here rather than as a false accusation in a
    packet."""

    def test_it_counts_methods_inside_classes(self):
        self.assertEqual(2, _count_source(
            "class A(unittest.TestCase):\n"
            "    def test_one(self): pass\n"
            "    def test_two(self): pass\n"
            "    def helper(self): pass\n"))

    def test_it_counts_module_level_functions(self):
        self.assertEqual(1, _count_source(
            "def test_alone(): pass\ndef not_a_test(): pass\n"))

    def test_it_counts_both_together(self):
        self.assertEqual(3, _count_source(
            "def test_a(): pass\n"
            "class B(unittest.TestCase):\n"
            "    def test_b(self): pass\n"
            "    def test_c(self): pass\n"))

    def test_it_does_not_count_nested_helpers(self):
        """A `def test_*` defined inside a method is not collected."""
        self.assertEqual(1, _count_source(
            "class A(unittest.TestCase):\n"
            "    def test_outer(self):\n"
            "        def test_inner(): pass\n"))

    def test_a_SECOND_derivation_agrees_on_every_test_file(self):
        """The anchor, and NOT a hand-typed number.

        Writing `self.assertEqual(14, ...)` here would have been the fourth
        hand-written mirror this review has produced, and mirrors go stale
        silently -- which is the whole reason this file exists. So the check
        is two INDEPENDENT derivations agreeing: the AST walk above, and
        INDENTATION over the raw source. They reach the answer by different
        routes and fail in different ways, so agreement is worth something.

        The indentation route needs the nesting rule stated, and stating it
        found a real case: `tests/test_m6_chain.py` line 838 holds a
        `@property def test_only` on a `_Bomb` class nested inside a method.
        pytest does not collect it, the AST walk correctly skips it, and a
        naive regex counted it -- 101 against 100. A `def` collected by
        pytest sits at column 0 or column 4; deeper is nested.
        """
        pattern = re.compile(r"^(?P<indent> *)(?:async )?def (test\w*)", re.M)
        checked = 0
        for path in sorted((REPO / "tests").glob("test_*.py")):
            source = path.read_text(encoding="utf-8")
            by_indent = [m for m in pattern.finditer(source)
                         if len(m.group("indent")) <= 4]
            # DEFINITIONS against definitions. `collected_tests` counts
            # CASES, which a regex cannot see, so comparing it here would
            # make the two routes disagree wherever both are right.
            self.assertEqual(
                len(by_indent), defined_tests(path),
                "the AST walk and the indentation walk disagree on %s; one "
                "of them is wrong and a packet's numbers depend on which"
                % path.name)
            try:
                self.assertGreaterEqual(collected_tests(path),
                                        defined_tests(path))
            except Uncountable:
                pass          # named loudly by `stale_claims`, not silenced
            checked += 1
        self.assertGreater(checked, 50,
                           "only %d files compared; at that count this "
                           "proves nothing" % checked)

    def test_the_indentation_route_really_would_disagree_if_wrong(self):
        """Non-vacuity for the pairing: without the depth rule the two
        routes DO differ, on a real file in this repository."""
        source = (REPO / "tests" / "test_m6_chain.py").read_text(
            encoding="utf-8")
        naive = re.findall(r"^\s*(?:async )?def (test\w*)", source, re.M)
        self.assertEqual(defined_tests(REPO / "tests" / "test_m6_chain.py"),
                         len(naive) - 1,
                         "the nested `@property def test_only` this rule "
                         "exists for is gone; find the new witness or drop "
                         "this test rather than leaving it passing on a "
                         "coincidence")


def _count_source(source):
    import tempfile
    handle = tempfile.NamedTemporaryFile("w", suffix=".py", delete=False,
                                         encoding="utf-8")
    handle.write(source)
    handle.close()
    try:
        return collected_tests(handle.name)
    finally:
        Path(handle.name).unlink()


class TestTheGuardIsNotVACUOUS(unittest.TestCase):
    """Between rounds there is no live packet at all, so the class above can
    pass over an empty list. These drive the machinery directly."""

    def _packet(self, body):
        import tempfile
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        path = Path(holder.name) / "PROMPT_fake.md"
        path.write_text(body, encoding="utf-8")
        return path

    def test_a_wrong_number_is_reported(self):
        packet = self._packet(
            "DELIVERY_STATUS=ISSUED\n\n核验  python -m pytest "
            "tests/test_the_seat_ledger_ids_are_unique.py -q\n"
            "预期  99999 passed\n")
        self.assertTrue(any("true when written" in p
                            for p in stale_claims(packet)))

    def test_the_RIGHT_number_is_accepted(self):
        """Otherwise the test above would pass even if this always failed."""
        target = "tests/test_the_seat_ledger_ids_are_unique.py"
        packet = self._packet("DELIVERY_STATUS=ISSUED\n\n核验  python -m "
                              "pytest %s -q\n预期  %d passed\n"
                              % (target, collected_tests(REPO / target)))
        self.assertEqual([], stale_claims(packet))

    def test_a_command_that_cannot_run_is_reported(self):
        packet = self._packet(
            "DELIVERY_STATUS=ISSUED\n\n核验  python -m pytest "
            "tests/test_no_such_file_exists.py -q\n预期  3 passed\n")
        self.assertTrue(any("cannot run" in p for p in stale_claims(packet)))

    def test_a_SELF_REFERENTIAL_claim_is_now_HARMLESS(self):
        """The one that crashed the machine twice.

        A packet quoting this file's own count is reasonable -- its number
        deserves checking like any other. It is safe now for a structural
        reason rather than a defensive one: nothing here executes, so there
        is nothing to re-enter."""
        target = "tests/test_a_prompts_measured_numbers_are_current.py"
        packet = self._packet("DELIVERY_STATUS=ISSUED\n\n核验  python -m "
                              "pytest %s -q\n预期  %d passed\n"
                              % (target, collected_tests(REPO / target)))
        self.assertEqual([], stale_claims(packet))

    def test_a_packet_with_no_claims_reports_nothing_to_check(self):
        packet = self._packet("DELIVERY_STATUS=ISSUED\n\nno claims here\n")
        self.assertEqual([], stale_claims(packet))


if __name__ == "__main__":
    unittest.main()
