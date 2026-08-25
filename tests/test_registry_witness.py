"""The witness must actually catch both channels, not just the famous one.

Item 7 boundaries (1) and (2) of `dec-eight-open-2026-08-26`.

The ruling that ordered this work says a half-written row "dies on the
six-cell parse", and calls silent sync rollback the only fatal channel.
That is wrong in a way these tests exist to pin: the real parser CONTINUES
past a cell-count mismatch, so a truncated row is silently dropped, and the
registry is allowlisted out of the clean gate so a dirty file never trips
`git_clean`. A truncated tail therefore looks exactly like a rollback.

`test_a_truncated_final_row_is_caught_the_same_as_a_rollback` is the one
that matters. If someone later trims boundary (1) believing the parser
covers half-writes, that test is the thing that says otherwise — and it
uses the PRODUCTION parser, not a local imitation, so it cannot drift into
agreeing with a premise that was never true.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from itsf.s0 import registry_witness as rw  # noqa: E402


def _production_parser():
    """The REAL `parse_registry_events`, loaded from the runner script.

    Loaded rather than reimplemented: the whole claim under test is about
    how the production parser treats a malformed row. A local copy would
    let the test keep passing while the real one changed.
    """
    spec = importlib.util.spec_from_file_location(
        "_s0_real_run_for_test", REPO / "scripts" / "s0_real_run.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.parse_registry_events


HEADER = ("| # | utc | event | commit | actor | 原因/备注 |\n"
          "|---|---|---|---|---|---|\n")


def _registry(rows):
    body = "".join(
        "| %s | %s | %s | abc1234 | main agent | note |\n" % r for r in rows)
    return HEADER + body


ROWS3 = [("1", "2026-01-01", "TRIAL_REGISTERED"),
         ("2", "2026-01-02", "RUN_AUTHORIZED"),
         ("+", "2026-01-03", "RUN_STARTED")]


def test_the_production_parser_really_does_drop_a_malformed_row():
    """The premise the ruling got wrong, asserted directly.

    Not a claim about our own code — a measurement of the parser the real
    runner uses. If this ever fails, the parser started rejecting malformed
    rows and the second channel closed on its own; update the failure model
    rather than deleting the witness.
    """
    parse = _production_parser()
    good = _registry(ROWS3)
    truncated = good[:good.rindex("| + |")] + "| + | 2026-01-03 | RUN_ST\n"
    assert len(parse(good)) == 3
    assert len(parse(truncated)) == 2, (
        "the production parser rejected or kept a malformed row; the "
        "failure model in ops/REGISTRY_SYNC_FAILURE_MODEL.md assumes it is "
        "silently dropped")


def test_a_growing_registry_verifies(tmp_path):
    parse = _production_parser()
    wit = tmp_path / "w.jsonl"
    text = _registry(ROWS3[:2])
    rw.append_witness(wit, rw.registry_facts(text, parse(text)))
    grown = _registry(ROWS3)
    code, why = rw.verify_against_witness(grown, parse(grown), wit)
    assert code == rw.OK, why


def test_a_silent_rollback_is_caught(tmp_path):
    parse = _production_parser()
    wit = tmp_path / "w.jsonl"
    text = _registry(ROWS3)
    rw.append_witness(wit, rw.registry_facts(text, parse(text)))
    rolled = _registry(ROWS3[:2])          # sync put the file back
    code, why = rw.verify_against_witness(rolled, parse(rolled), wit)
    assert code == rw.ROLLBACK, why


def test_a_truncated_final_row_is_caught_the_same_as_a_rollback(tmp_path):
    """THE ONE THAT MATTERS — channel B, which the ruling said could not
    happen because the parser would reject it. The parser does not reject
    it (see the first test), so without the witness this state is
    indistinguishable from a run that never started."""
    parse = _production_parser()
    wit = tmp_path / "w.jsonl"
    text = _registry(ROWS3)
    rw.append_witness(wit, rw.registry_facts(text, parse(text)))
    truncated = text[:text.rindex("| + |")] + "| + | 2026-01-03 | RUN_ST\n"
    code, why = rw.verify_against_witness(truncated, parse(truncated), wit)
    assert code == rw.ROLLBACK, (
        "a truncated final row slipped past the witness. This is the exact "
        "state the ruling believed the parser would reject: " + why)


def test_a_rewritten_tail_is_caught_even_when_the_count_matches(tmp_path):
    """Count alone is not enough — a conflict resolution can replace the
    last row with a different one and keep the length."""
    parse = _production_parser()
    wit = tmp_path / "w.jsonl"
    text = _registry(ROWS3)
    rw.append_witness(wit, rw.registry_facts(text, parse(text)))
    swapped = _registry(ROWS3[:2] + [("+", "2026-01-03", "COMPLETED")])
    code, why = rw.verify_against_witness(swapped, parse(swapped), wit)
    assert code == rw.ROLLBACK, why


def test_a_row_deleted_from_the_middle_is_caught_by_the_count(tmp_path):
    """The case the count check exists for, and the one I had missed.

    Mutation testing found it: disabling the event-count comparison broke
    NO test, because every rollback case I had written also lost the last
    row, so `last_row` alone was doing all the work. A conflict resolution
    that drops an interior row while preserving the tail defeats the
    `last_row` check entirely — only the count sees it.

    Two checks, two distinct failure shapes. Neither is redundant, and now
    both are exercised.
    """
    parse = _production_parser()
    wit = tmp_path / "w.jsonl"
    text = _registry(ROWS3)
    rw.append_witness(wit, rw.registry_facts(text, parse(text)))
    gutted = _registry([ROWS3[0], ROWS3[2]])       # row 2 gone, tail intact
    assert (_row_identity_of_last(parse(gutted))
            == _row_identity_of_last(parse(text))), (
        "the tail must be unchanged for this test to mean anything")
    code, why = rw.verify_against_witness(gutted, parse(gutted), wit)
    assert code == rw.ROLLBACK, (
        "an interior row vanished and the witness let it through — the "
        "count comparison is the only thing that sees this shape: " + why)


def _row_identity_of_last(rows):
    return rw._row_identity(rows[-1])


def test_no_witness_is_unknown_not_ok(tmp_path):
    """L6: absence of a record renders UNKNOWN, never NONE. A caller
    gating a trial-consuming run must refuse on this, not proceed."""
    parse = _production_parser()
    text = _registry(ROWS3)
    code, _ = rw.verify_against_witness(text, parse(text),
                                        tmp_path / "missing.jsonl")
    assert code == rw.WITNESS_ABSENT


def test_a_corrupted_witness_is_not_downgraded_to_absent(tmp_path):
    """Degrading a corrupted witness into "none yet" would turn the loudest
    signal into the quietest, and the caller would treat it as a
    first-run."""
    wit = tmp_path / "w.jsonl"
    wit.write_text("{not json\n", encoding="utf-8")
    parse = _production_parser()
    text = _registry(ROWS3)
    code, _ = rw.verify_against_witness(text, parse(text), wit)
    assert code == rw.WITNESS_MALFORMED


def test_valid_json_that_is_not_a_witness_record_is_malformed(tmp_path):
    """The second half of the malformed check, and mutation testing had to
    find it too.

    My first corrupted-witness test wrote invalid JSON, so it exercised the
    `except ValueError` path and left the shape check — is this a dict, does
    it carry event_count — completely untested. Changing that branch to
    return WITNESS_ABSENT broke nothing.

    It matters because the two codes mean opposite things to a caller: an
    ABSENT witness looks like a first run, while a MALFORMED one means the
    evidence file itself is damaged and nothing about the registry can be
    concluded. Silently turning the second into the first is the same
    fail-silent shape the whole module exists to prevent.
    """
    parse = _production_parser()
    text = _registry(ROWS3)
    for payload in ('[1, 2, 3]', '{"sha256": "abc"}', '"just a string"',
                    'null'):
        wit = tmp_path / f"w{abs(hash(payload))}.jsonl"
        wit.write_text(payload + "\n", encoding="utf-8")
        code, _ = rw.verify_against_witness(text, parse(text), wit)
        assert code == rw.WITNESS_MALFORMED, (
            f"a witness tail of {payload!r} was not reported as malformed; "
            "if it came back ABSENT the caller would treat a damaged "
            "evidence file as a first run")


def test_the_witness_never_creates_a_directory(tmp_path):
    """ND1 keeps directory creation as its own authorization. A helper that
    quietly made the parent would merge two authorizations that must not be
    merged — so absence is an error, not a thing to fix silently."""
    missing = tmp_path / "not_authorized_yet" / "w.jsonl"
    with pytest.raises(FileNotFoundError):
        rw.append_witness(missing, {"sha256": "x", "event_count": 0,
                                    "last_row": ""})
    assert not missing.parent.exists(), (
        "append_witness created a directory under a governed root")


def test_the_witness_file_is_append_only_in_practice(tmp_path):
    wit = tmp_path / "w.jsonl"
    rw.append_witness(wit, {"sha256": "a", "event_count": 1, "last_row": "x"})
    rw.append_witness(wit, {"sha256": "b", "event_count": 2, "last_row": "y"})
    lines = wit.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["sha256"] == "a", "an earlier record moved"
    facts, problem = rw.read_last_witness(wit)
    assert problem is None and facts["sha256"] == "b"


def test_conflict_copies_are_found_whatever_the_client_named_them(tmp_path):
    ops = tmp_path / "ops"
    ops.mkdir()
    canonical = ops / "TRIAL_REGISTRY.md"
    canonical.write_text("real", encoding="utf-8")
    (ops / "README.md").write_text("not it", encoding="utf-8")
    assert rw.find_conflict_copies(canonical) == []
    for name in ("TRIAL_REGISTRY-DESKTOP-4F2A1B.md",
                 "TRIAL_REGISTRY (Aaron's conflicted copy 2026-08-26).md",
                 "TRIAL_REGISTRY-PC.md"):
        (ops / name).write_text("copy", encoding="utf-8")
    found = {p.name for p in rw.find_conflict_copies(canonical)}
    assert len(found) == 3
    assert "TRIAL_REGISTRY.md" not in found, "the registry itself was flagged"
    assert "README.md" not in found


def test_the_witness_module_names_no_registry_and_so_passes_the_c2_guard():
    """MEASURED FAILURE, 2026-08-26 — the full suite caught this, not me.

    My first version held `_REGISTRY_STEM = "TRIAL_REGISTRY"`, and
    `tests/test_registry_boundary.py`'s
    `test_no_production_module_reads_the_registry_path_outside_the_boundary`
    went red: a production module that both names the registry and does
    file I/O is exactly the second-reader shape C2 was rewritten to close
    after MC-REG-COLLISION-001.

    The guard was right. The module changed — the caller passes the
    canonical path — rather than the guard being widened to admit it.
    Weakening a guard to fit an implementation constant is the direction
    D-4 explicitly refused.

    This asserts the property locally so the reason survives next to the
    code, instead of living only in a boundary test that names no module.
    """
    import ast
    src = (REPO / "src" / "itsf" / "s0" / "registry_witness.py").read_text(
        encoding="utf-8")
    tree = ast.parse(src)
    docstrings = set()
    # Only these four carry a docstring, and only these four have a `body`
    # that is a list. `ast.Lambda` and `ast.IfExp` also have `.body`, and
    # subscripting theirs raises — which is how the first draft of this
    # test failed. The boundary guard this mirrors has the same filter.
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.FunctionDef,
                                 ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        body = node.body
        if (body and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)):
            docstrings.add(id(body[0].value))
    named = [n.value for n in ast.walk(tree)
             if isinstance(n, ast.Constant) and isinstance(n.value, str)
             and id(n) not in docstrings and "TRIAL_REGISTRY" in n.value]
    assert not named, (
        "registry_witness.py carries a registry filename outside a "
        f"docstring ({named}); the C2 boundary guard will refuse it")


def test_the_failure_model_document_still_says_both_channels_exist():
    """The document is the reason anyone would keep boundary (1). If the
    two-channel finding is ever edited out of it, the tests above become
    orphaned assertions nobody understands."""
    doc = (REPO / "ops" / "REGISTRY_SYNC_FAILURE_MODEL.md").read_text(
        encoding="utf-8")
    for token in ("183-184", "_clean_gate_exempt", "通道 B"):
        assert token in doc, (
            f"the failure model no longer records {token}; boundary (1)'s "
            "justification has been weakened")
