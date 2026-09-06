r"""The `$`-anchor sweep, derived from source instead of hand-listed.

`tests/test_mc_supplement_paths_battery.py::test_no_anchored_pattern_admits
_a_trailing_newline` already sweeps this class. It sweeps SEVEN patterns,
all of them in `itsf.mc.supplement_contract`, from a hand-written tuple with
`assert len(ANCHORED_PATTERNS) == 7` pinning the count.

MEASURED 2026-08-29: five identity patterns elsewhere in `src/` were never
in that tuple, and all five accepted a trailing newline.

    atoms._UPPER_CONST     ^[A-Z][A-Z0-9_]*$
    atoms._HEX64           ^[0-9a-f]{64}$
    consumer._HEX64_RE     ^[0-9a-f]{64}$
    report._DATE_RE        ^\d{4}-\d{2}-\d{2}$
    runinfra._HEX64_RE     ^[0-9a-f]{64}$

Three of them validate SHA-256 digests.

THE SHAPE, again: a guard scoped to the module its author was working in,
while the property it names ("no anchored pattern admits a trailing
newline") is a property of the repository. The existing guard is not wrong
— it pins what it declares — but nothing widened it, and nothing could
have noticed.

SO THIS ONE DERIVES ITS LIST. Module-level `re.compile` assignments whose
pattern starts with `^`, ends with `$` or `\Z`, and contains no named group
are IDENTITY patterns: they validate a whole token. Every one found must
end at `\Z`. A line parser that legitimately anchors with `$` must be
declared in `LINE_PARSERS` with a reason — the same fail-closed shape as
the approvals guard, for the same reason: a list nobody derives goes stale
the first time someone adds a file.
"""

import ast
import io
import re
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"

#: Patterns that end at `$` on purpose, with the reason. A `$`-anchored
#: LINE parser is correct: it runs on lines already split from a document,
#: so no trailing newline can reach it. Anything not listed must use `\Z`.
LINE_PARSERS = {
    # `^...(.*)$` with `re.S`, applied to `.strip()`ed note text. The `$`
    # here is "capture to the end", not an identity anchor, and the input
    # is stripped before it arrives — measured at the four call sites
    # (mc_registry.py:208,223 and supplement_registry.py:660,708).
    ("mc_registry.py", "_NOTE_BRACKET_RE"): "note parser, stripped input",
    ("mc_registry.py", "_FIELD_RE"): "field parser over a segment",
    ("supplement_registry.py", "_NOTE_BRACKET_RE"): "note parser, stripped",
    ("supplement_registry.py", "_FIELD_RE"): "field parser over a segment",
    # QROS-CF F05. This one is an INTENT SCAN, not an identity validator, and
    # anchoring it would defeat its purpose: it must match a line the row
    # parser CANNOT read -- a missing final pipe, an extra pipe inside the
    # reason, the wrong cell count -- so the tail is by definition arbitrary.
    # It runs per line (`text.splitlines()`), so no trailing newline reaches
    # it, and it decides nothing about validity: every line it matches must
    # then be produced as a validated row by the shared parser or the start
    # refuses.
    ("owner_control.py", "_OWNER_INTENT_RE"):
        "per-line intent scan; must match rows the row parser rejects",
}


def _pattern_text(node):
    """The pattern source, for a literal OR an f-string.

    WIDENED A SECOND TIME on 2026-08-29, an hour after the first widening.
    The first version required `ast.Constant`, so three of `runinfra`'s four
    log-schema patterns — built with `rf"...{_STAGE_ALT}..."` — were
    invisible. Interpolation is not a different kind of pattern.

    Only the literal segments are recoverable; an interpolated name could
    contribute anything. That is enough for this check, which asks how the
    pattern STARTS and ENDS, and both ends are literal in every case here.
    A placeholder marks the interpolated middle so nothing downstream reads
    the result as the real pattern."""
    if isinstance(node, ast.Constant):
        return node.value if isinstance(node.value, str) else None
    if isinstance(node, ast.JoinedStr):
        parts = []
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(value.value)
            else:
                parts.append("…")           # an interpolated segment
        return "".join(parts)
    return None


def _identity_patterns():
    """Every whole-token validator in `src/`, wherever it is compiled.

    WIDENED 2026-08-29, hours after this file was written, and the reason is
    the thing this file is about. The first version walked `tree.body` — only
    `NAME = re.compile(...)` at module level. It therefore could not see:

        consumer.py:1048   `hex64 = re.compile(...)` INSIDE a function
        runinfra.py:722    four patterns inside a dict LITERAL

    So the guard written to stop a sweep being narrower than the property it
    names was itself narrower than the property it named, for one evening.
    Two of the three sweeps in this repository have now had this defect.

    It walks the whole tree. The name reported is the assignment target when
    there is one, else `<line N>` — a pattern with no name still counts."""
    found = []
    for path in sorted(SRC.rglob("*.py")):
        source = io.open(path, encoding="utf-8").read()
        try:
            tree = ast.parse(source)
        except SyntaxError:                      # pragma: no cover
            continue
        names = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                target = node.targets[0]
                if isinstance(target, ast.Name):
                    names[id(node.value)] = target.id
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call)
                    and getattr(node.func, "attr", "") == "compile"
                    and getattr(getattr(node.func, "value", None), "id", "")
                    == "re"):
                continue
            if not node.args:
                continue
            pattern = _pattern_text(node.args[0])
            if pattern is None or not pattern.startswith("^"):
                continue
            if "(?P<" in pattern:
                continue                          # a parser, not a validator
            found.append((path.name,
                          names.get(id(node), "<line %d>" % node.lineno),
                          pattern, node.lineno))
    return found


class TestNoIdentityPatternAdmitsATrailingNewline(unittest.TestCase):

    def test_every_derived_pattern_ends_at_backslash_Z(self):
        offenders = []
        for filename, name, pattern, line in _identity_patterns():
            if (filename, name) in LINE_PARSERS:
                continue
            if not pattern.endswith(r"\Z"):
                offenders.append("%s:%d %s = %r" % (filename, line, name,
                                                    pattern))
        self.assertEqual(
            [], offenders,
            "these whole-token validators do not end at \\Z, so each admits "
            "a trailing newline:\n  " + "\n  ".join(offenders)
            + "\n\nEither anchor them at \\Z, or declare them in "
              "LINE_PARSERS with the reason they may end at '$'.")

    def test_the_derivation_actually_finds_patterns(self):
        """A sweep that matches nothing reports clean. The count is a floor,
        not a pin: adding a validator must not make this test fail."""
        found = _identity_patterns()
        self.assertGreater(len(found), 8,
                           "the derivation found %d whole-token validators, "
                           "which is too few to be real" % len(found))

    def test_it_finds_the_five_this_file_was_written_for(self):
        """Named so a change to the derivation that silently stops seeing
        them fails here rather than passing quietly."""
        seen = {(f, n) for f, n, _p, _l in _identity_patterns()}
        for pair in (("atoms.py", "_UPPER_CONST"), ("atoms.py", "_HEX64"),
                     ("consumer.py", "_HEX64_RE"), ("report.py", "_DATE_RE"),
                     ("runinfra.py", "_HEX64_RE")):
            with self.subTest(pattern=pair):
                self.assertIn(pair, seen)

    def test_the_declared_exemptions_all_exist(self):
        """An exemption for a pattern that is gone is an exemption nobody
        will notice is stale."""
        seen = {(f, n) for f, n, _p, _l in _identity_patterns()}
        for pair in LINE_PARSERS:
            with self.subTest(exemption=pair):
                self.assertIn(pair, seen)


class TestTheFivePatternsBehave(unittest.TestCase):
    """Behaviour, not just spelling — the spelling check above would pass
    against a pattern that ends at `\\Z` and is wrong for another reason."""

    def _cases(self):
        from itsf.mc import atoms, consumer
        from itsf.s0 import report, runinfra
        return (("atoms._UPPER_CONST", atoms._UPPER_CONST, "ABC_1"),
                ("atoms._HEX64", atoms._HEX64, "a" * 64),
                ("consumer._HEX64_RE", consumer._HEX64_RE, "a" * 64),
                ("report._DATE_RE", report._DATE_RE, "2026-08-29"),
                ("runinfra._HEX64_RE", runinfra._HEX64_RE, "a" * 64))

    def test_a_trailing_newline_is_refused(self):
        for name, pattern, good in self._cases():
            with self.subTest(pattern=name):
                self.assertFalse(pattern.match(good + "\n"))

    def test_the_clean_value_still_matches(self):
        for name, pattern, good in self._cases():
            with self.subTest(pattern=name):
                self.assertTrue(pattern.match(good))


if __name__ == "__main__":
    unittest.main()
