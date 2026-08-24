"""O4's errata register: the rules, enforced rather than described.

The ruling approved a PROCEDURE and explicitly withheld approval of any
content -- the decision packet carried no errata list, and blanket approval
of unenumerated content is a blank cheque. So the register exists, its
rules are mechanical, and it starts empty.

The rule that actually matters is the third one. An erratum that touches a
sealed number is not an erratum; it is a change of conclusion wearing one's
clothes, and it has its own procedure. `NUMERIC_CHANGE=NO` is how each
entry states it is not that.
"""
from __future__ import annotations

import re
from pathlib import Path

REGISTER = Path(__file__).resolve().parent.parent / "ops" / \
    "FEASIBILITY_ERRATA_REGISTER.md"

REQUIRED = ("TARGET", "ORIGINAL", "CORRECTED", "REASON", "NUMERIC_CHANGE")

_ENTRY = re.compile(r"^### ERRATUM-(\d+)\b", re.M)


def _text():
    return REGISTER.read_text(encoding="utf-8")


def _entries(text):
    """Each entry is a level-3 heading plus everything up to the next."""
    marks = [(m.start(), m.group(1)) for m in _ENTRY.finditer(text)]
    out = []
    for i, (pos, num) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        out.append((num, text[pos:end]))
    return out


def test_the_register_exists_and_declares_its_discipline():
    text = _text()
    assert "APPEND_ONLY=YES" in text
    assert "DELEGATED=YES" in text
    for rule in ("一字不动", "NUMERIC_CHANGE=NO", "逐字"):
        assert rule in text, rule


def test_every_entry_carries_all_five_fields():
    for num, body in _entries(_text()):
        for field in REQUIRED:
            assert field in body, f"ERRATUM-{num} missing {field}"


def test_no_entry_may_declare_a_numeric_change():
    """The fail-closed rule. An erratum touching a sealed number is out of
    scope by construction, so there is no way to write one here that
    passes -- it has to go through whatever procedure changes a
    conclusion, and be visible as that."""
    for num, body in _entries(_text()):
        assert "NUMERIC_CHANGE=NO" in body, (
            f"ERRATUM-{num} does not declare NUMERIC_CHANGE=NO; an erratum "
            "that touches a sealed value is a change of conclusion, not a "
            "correction of wording, and belongs in another procedure")
        assert "NUMERIC_CHANGE=YES" not in body, f"ERRATUM-{num}"


def test_entry_numbers_are_unique_and_sequential():
    """Append-only means the numbering is a witness. A gap or a repeat is
    either a deleted entry or a rewritten one, and both are the thing this
    register is built to make impossible."""
    nums = [int(n) for n, _ in _entries(_text())]
    assert nums == sorted(nums), nums
    assert len(nums) == len(set(nums)), nums
    assert nums == list(range(1, len(nums) + 1)), nums


def test_the_declared_count_matches_the_entries():
    text = _text()
    declared = re.search(r"^ENTRIES=(\d+)$", text, re.M)
    assert declared, "the header must declare ENTRIES=<n>"
    assert int(declared.group(1)) == len(_entries(text))
