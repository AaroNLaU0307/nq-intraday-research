"""F06 across MODULES: every supported governed-registry writer, serialized.

WHAT THIS FILE EXISTS TO CATCH, stated first because it is the exact defect
that got past three earlier rounds of F06 work.

The final-certification writer inventory found `itsf.s0.runner.
append_registry_event_line`: a WORKFLOW-SUPPORTED writer of the governed
registry that received the registry path as a PARAMETER and called
`open(..., "a")` + `write(...)`. `scripts/s0_real_run.py` passes it the governed
REGISTRY, built from `registry_boundary`'s own frozen constants, so it was a
real supported path -- not a hypothetical.

Reproduced two ways before the repair:
  * it wrote while `_AppendLock` was HELD by another writer;
  * it read nothing, so an OWNER_HOLD that landed first was invisible and its
    row went on top of it.

WHY THE EARLIER GUARDS COULD NOT SEE IT. `test_n09_scaffold_criteria` proves
things about `registry_boundary`'s own module -- correctly, and that is all it
claims. `test_registry_path_single_construction` keys on the path LITERAL, and
this writer never spells the path: it is handed one. So a guard scoped to one
module plus a guard keyed on a string both reported clean while a third
supported writer mutated the same bytes outside serialization.

Hence this file's rule is deliberately NOT about literals or about one module:
it asks which functions can mutate a file that is or may be the governed
registry, and requires each to reach the one shared boundary.

ROOT CAUSE WAS LOCATION, NOT INTENT. The lock and the physical write lived only
inside a private function, so a supported writer in another module had nothing
to call. `registry_boundary.serialized_append` is that boundary, exposed.
"""
from __future__ import annotations

import ast
import sys
import tempfile
import threading
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tests"))

from itsf.mc import owner_control as oc                        # noqa: E402
from itsf.mc import registry_boundary as rb                    # noqa: E402
from itsf.mc import supplement_registry as sreg                # noqa: E402
from itsf.s0.runner import append_registry_event_line          # noqa: E402

C40 = "a" * 40
UTC = "2026-09-07T00:00:00+00:00"
PRIMITIVE = "serialized_append"
WRITE_CALLS = {"write_bytes", "write_text", "writelines", "write"}


# ===========================================================================
# 1 — the completeness rule
# ===========================================================================

def _mutation_candidates():
    """Functions under src/ and scripts/ that can mutate a registry-shaped file.

    THE RULE, and each clause earned its place:
      (a) it performs a write call, or opens something in APPEND mode -- the
          append-mode clause is what a `write_bytes`-only scan misses;
      (b) AND it is plausibly about the registry: its own name or one of its
          parameter names mentions "registry", or its body names the governed
          filename, or it calls the shared boundary.

    Clause (b)'s PARAMETER-NAME half is the one that catches the real defect: a
    writer handed the path never mentions it. A rule keyed only on the literal
    is the rule that already failed.
    """
    out = []
    for root in ("src", "scripts"):
        for path in sorted((REPO / root).rglob("*.py")):
            rel = path.relative_to(REPO).as_posix()
            text = path.read_text(encoding="utf-8")
            try:
                tree = ast.parse(text)
            except SyntaxError:                                # pragma: no cover
                continue
            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                body = ast.unparse(node)
                called = {getattr(c.func, "attr", None) or getattr(c.func, "id", None)
                          for c in ast.walk(node) if isinstance(c, ast.Call)}
                appends = ".open('a'" in body or '.open("a"' in body
                if not (called & WRITE_CALLS or appends):
                    continue
                params = {a.arg for a in node.args.args}
                about_registry = (
                    # (b1) the module that OWNS the governed path. Without this
                    # the rule could not see the primitive or its
                    # compare-and-swap caller at all, and two of the three
                    # registered entries below could never fire -- a registered
                    # entry that cannot fire misrepresents what this test
                    # checks, which is the failure mode this repository calls
                    # a vacuous guard.
                    rel.endswith("mc/registry_boundary.py")
                    or "registry" in node.name.lower()
                    or any("registry" in q.lower() for q in params)
                    or "TRIAL_REGISTRY.md" in body
                    or PRIMITIVE in called)
                if about_registry:
                    out.append({"path": rel, "symbol": node.name,
                                "calls_primitive": PRIMITIVE in called,
                                "append_mode": appends})
    return out


#: The supported governed-registry mutation paths, REGISTERED. Anything the rule
#: finds that is not here fails, and anything here that stops reaching the
#: primitive fails. Registered rather than converged, because the honest answer
#: for each is a sentence, not a boolean.
SUPPORTED = {
    # the boundary itself: the one physical write, under the one lock
    ("src/itsf/mc/registry_boundary.py", "serialized_append"): "THE PRIMITIVE",
    # `_compare_and_append` is deliberately NOT here. Since the repair it
    # performs no write and opens nothing, so it is not a mutation candidate at
    # all -- it is a CALLER of the primitive. Registering it would have been a
    # row that could never fire, which is what the dead-entry test above exists
    # to refuse. `test_n09_scaffold_criteria` is what pins its delegation.
    # the cross-module writer this file exists for
    ("src/itsf/s0/runner.py", "append_registry_event_line"): "DELEGATES",
}


def test_every_registered_entry_can_actually_fire():
    """No dead rows. A registered writer the rule never yields would look like
    coverage and be none -- and this file found exactly that in its own first
    version: clauses keyed on names and literals could not see
    `serialized_append` or `_compare_and_append`, so two of the three rows below
    were decorative. Clause (b1) is the fix, and this is the test that would
    have caught it."""
    found = {(h["path"], h["symbol"]) for h in _mutation_candidates()}
    dead = sorted(k for k in SUPPORTED if k not in found)
    assert dead == [], (
        "these are registered as supported writers but the rule never yields "
        "them, so nothing about them is actually checked: %r" % (dead,))


def test_the_rule_reaches_enough_code_to_prove_anything():
    """`assertEqual([], offenders)` is true when the scan found nothing. A wrong
    root or a changed glob would report clean loudly, which is worse than no
    guard."""
    scanned = sum(1 for _ in (REPO / "src").rglob("*.py"))
    scanned += sum(1 for _ in (REPO / "scripts").rglob("*.py"))
    assert scanned > 40, f"the scan reached {scanned} modules; at that count it proves nothing"
    assert _mutation_candidates(), "the rule matched no function at all"


def test_every_supported_registry_writer_reaches_the_shared_primitive():
    """THE INVARIANT. Not 'the boundary's writers' -- every supported one."""
    offenders = []
    for hit in _mutation_candidates():
        key = (hit["path"], hit["symbol"])
        if key not in SUPPORTED:
            offenders.append(
                "%s::%s can mutate a registry-shaped file and is not "
                "registered; classify it, and if it is a supported governed "
                "writer route it through %s"
                % (hit["path"], hit["symbol"], PRIMITIVE))
            continue
        if SUPPORTED[key] == "THE PRIMITIVE":
            continue
        if not hit["calls_primitive"]:
            offenders.append(
                "%s::%s is a supported governed-registry writer that does NOT "
                "call %s -- this is the exact defect the final-cert inventory "
                "found" % (hit["path"], hit["symbol"], PRIMITIVE))
    assert offenders == [], "\n  " + "\n  ".join(offenders)


def test_no_supported_writer_still_opens_the_registry_in_append_mode():
    """The specific shape of the defect, named so a regression is unmistakable."""
    bad = [f"{h['path']}::{h['symbol']}" for h in _mutation_candidates()
           if h["append_mode"] and not h["calls_primitive"]]
    assert bad == [], (
        "these open a registry-shaped file in APPEND MODE without the shared "
        "boundary: " + ", ".join(bad))


def test_the_rule_would_catch_the_original_defect():
    """THE MUTATION, run against the pre-repair shape rather than asserted.

    A guard nobody has seen fail is a guard nobody knows works, and this one
    exists because two earlier guards silently did not."""
    pre_repair = (
        "def append_registry_event_line(registry_path, trial_id, event, note,\n"
        "                               utc, commit, actor):\n"
        "    line = 'x'\n"
        "    with registry_path.open('a', encoding='utf-8') as fh:\n"
        "        fh.write(line)\n")
    tree = ast.parse(pre_repair)
    fn = tree.body[0]
    body = ast.unparse(fn)
    params = {a.arg for a in fn.args.args}
    called = {getattr(c.func, "attr", None) or getattr(c.func, "id", None)
              for c in ast.walk(fn) if isinstance(c, ast.Call)}
    appends = ".open('a'" in body or '.open("a"' in body
    assert appends, "the append-mode clause no longer fires"
    assert any("registry" in q.lower() for q in params), (
        "the parameter-name clause no longer fires -- that clause is the ONLY "
        "reason this writer is visible, because it never names the path")
    assert PRIMITIVE not in called
    assert "TRIAL_REGISTRY.md" not in body, (
        "the pre-repair writer named the path literal after all, which would "
        "mean the literal-keyed guard should have caught it")


def test_run_artifact_and_witness_writers_are_not_misclassified():
    """The other direction. A guard that swept in every file writer would be
    unusable and would get relaxed, so the exclusions are asserted."""
    found = {(h["path"], h["symbol"]) for h in _mutation_candidates()}
    for path, symbol in (
            ("src/itsf/s0/registry_witness.py", "append_witness"),
            ("src/itsf/s0/runinfra.py", "append_manifest_record"),
            ("src/itsf/mc/supplement_runner.py", "resolve_partial"),
            ("src/itsf/mc/day_strata_supplement.py",
             "seal_supplement_test_only")):
        assert (REPO / path).exists(), f"{path} vanished; re-check the exclusion"
        assert (path, symbol) not in found, (
            f"{path}::{symbol} writes a run artifact or a witness file, not the "
            "governed registry, and must not be classified as a registry writer")


# ===========================================================================
# 2 — deterministic interleavings involving the S0 writer
# ===========================================================================

@pytest.fixture
def ledger(tmp_path):
    path = tmp_path / "TRIAL_REGISTRY.md"
    import test_qros_cf_astra_repairs as R1
    sid = R1._two_row_ledger(path)
    return path, sid


def _s0(path, note="note", event="RUN_STARTED"):
    append_registry_event_line(path, "S0-T001", event, note, UTC, "abc1234",
                               "main agent (s0_real_run)")


def _events(path):
    return [ln.split("|")[3].strip()
            for ln in path.read_text(encoding="utf-8").splitlines()
            if ln.strip().startswith("|") and len(ln.split("|")) > 4]


def test_case_A_owner_hold_wins_so_the_S0_start_is_REFUSED(ledger):
    """A. INVERTED AT THE OWNER-SEMANTICS REPAIR, AND THIS TEST WAS WRONG.

    It used to assert that the S0 append lands AFTER the hold and called that
    correct, on the reasoning that reading under the lock made the ordering
    honest. Ordering was never the question. `RUN_STARTED` is a START-EQUIVALENT
    commit, and an applicable unreleased hold must REFUSE it -- which is exactly
    the failure the final certification reproduced and held on.

    So this file, written to close an F06 defect, asserted the next F06 defect
    as the intended behaviour. Serialization was right and semantics were
    missing, and a test that checks only the half you fixed will happily bless
    the half you did not.

    The ordering property it did care about is kept for GENERIC events, which is
    where it actually belongs: see `test_case_A_generic_events_still_order`.
    """
    path, _sid = ledger
    rb.append_owner_hold(scope=oc.GLOBAL_SCOPE, reason="stop",
                         head_commit=C40, utc_stamp=UTC, path=path)
    before = path.read_bytes()
    with pytest.raises(rb.AppendRefused) as caught:
        _s0(path, note="after the hold")
    assert caught.value.code == "start_refused_owner_hold_in_force"
    assert path.read_bytes() == before, "bytes moved under a refused start"
    assert "RUN_STARTED" not in _events(path)
    assert oc.holds_applicable_to_start(
        path.read_text(encoding="utf-8"), "MC-DS-S001"), "the hold was lost"


def test_case_A_generic_events_still_order_behind_a_hold(ledger):
    """The property the inverted test above was really about, kept where it
    belongs: a GENERIC append reads under the lock and builds on the committed
    version, so it can never reorder or replace a hold."""
    path, _sid = ledger
    rb.append_owner_hold(scope=oc.GLOBAL_SCOPE, reason="stop",
                         head_commit=C40, utc_stamp=UTC, path=path)
    before = path.read_bytes()
    _s0(path, note="generic after the hold", event="STAGE_D_COMPLETE")
    after = path.read_bytes()
    assert after.startswith(before), (
        "the generic append did not build on the committed version")
    ev = _events(path)
    assert ev.index("OWNER_HOLD") < ev.index("STAGE_D_COMPLETE")


def test_case_B_the_S0_append_wins_and_a_later_hold_is_ordered_after(ledger):
    """B. The S0 append wins; the hold is ordered afterwards and neither is
    erased."""
    path, _sid = ledger
    _s0(path, note="first")
    rb.append_owner_hold(scope=oc.GLOBAL_SCOPE, reason="stop",
                         head_commit=C40, utc_stamp=UTC, path=path)
    ev = _events(path)
    assert ev.index("RUN_STARTED") < ev.index("OWNER_HOLD")
    assert oc.active_holds(path.read_text(encoding="utf-8"), "MC-DS-S001")


def test_case_C_STARTED_and_the_S0_append_race_and_neither_erases_the_other(
        ledger, monkeypatch):
    """C. The interleaving driven deterministically: the S0 append lands while
    P3 holds its decision. P3's compare-and-swap must refuse -- and the S0 row
    must survive, because refusing is not the same as rolling back."""
    path, sid = ledger
    real = rb.serialized_append
    state = {"fired": False}

    def interleave(target, addition, *, decided=None, validate=None):
        if decided is not None and not state["fired"]:
            state["fired"] = True
            # A GENERIC S0 event, not a start: the point here is that P3's
            # compare-and-swap refuses on ANY intervening change, and that a
            # refusal is not a rollback of the other writer's row. Using a
            # start event would now (correctly) be refused itself, which would
            # test the owner rule instead of the CAS.
            _s0(target, note="landed under P3's decision",
                event="STAGE_D_COMPLETE")
        return real(target, addition, decided=decided, validate=validate)

    monkeypatch.setattr(rb, "serialized_append", interleave)
    with pytest.raises(rb.AppendRefused) as caught:
        rb.append_run_started(sid, head_commit=C40, utc_stamp=UTC, path=path)
    assert caught.value.code == "p3_registry_changed_under_decision"
    text = path.read_text(encoding="utf-8")
    assert "SUPPLEMENT_RUN_STARTED" not in text, "P3 bytes were written"
    assert "STAGE_D_COMPLETE" in text, "the other row was erased by the refusal"


def test_case_D_two_S0_appends_lose_nothing_and_corrupt_nothing(ledger):
    """D. Sequential and CONCURRENT. Two threads each append; both rows must be
    present, whole, and on their own lines."""
    path, _sid = ledger
    base = len(_events(path))
    _s0(path, note="one")
    _s0(path, note="two")
    assert len(_events(path)) == base + 2

    errors = []

    def worker(n):
        try:
            _s0(path, note="thread-%d" % n)
        except Exception as exc:                               # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == [], f"a concurrent append failed: {errors}"
    text = path.read_text(encoding="utf-8")
    for i in range(4):
        assert text.count("thread-%d" % i) == 1, (
            "row thread-%d was lost or duplicated" % i)
    lines = [ln for ln in text.splitlines() if "thread-" in ln]
    assert len(lines) == 4
    for ln in lines:
        assert ln.startswith("| + | ") and ln.endswith(" |"), (
            f"a row was interleaved mid-write: {ln!r}")
    assert not sreg.parse_registry_rows(text)[1], (
        "the ledger no longer parses after concurrent appends")


def test_case_E_an_exception_under_the_lock_leaves_no_residue(ledger):
    """E. A writer that raises while serialization is held must not continue
    unlocked and must not leave a stale lock behind, or the next append refuses
    forever."""
    path, _sid = ledger
    lock = path.with_name(path.name + rb.LOCK_SUFFIX)
    before = path.read_bytes()

    real_read = Path.read_bytes

    def boom(self):
        if self == path:
            raise RuntimeError("failure while the lock is held")
        return real_read(self)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(Path, "read_bytes", boom)
        with pytest.raises(RuntimeError, match="while the lock is held"):
            _s0(path)

    assert not lock.exists(), (
        "the lock file survived an exception; every later append would refuse "
        "with p3_append_lock_unavailable")
    assert path.read_bytes() == before, "a partial write escaped"
    # and the next append still works, which is what 'no residue' has to mean
    _s0(path, note="after the failure")
    assert "after the failure" in path.read_text(encoding="utf-8")


def test_case_E2_the_S0_writer_refuses_rather_than_writing_unlocked(ledger):
    """The half that was the defect: with the lock held, it must REFUSE."""
    path, _sid = ledger
    lock = path.with_name(path.name + rb.LOCK_SUFFIX)
    lock.write_bytes(b"")
    before = path.read_bytes()
    old = rb.LOCK_TIMEOUT_SECONDS
    try:
        rb.LOCK_TIMEOUT_SECONDS = 0.05
        with pytest.raises(rb.AppendRefused) as caught:
            _s0(path)
        assert caught.value.code == "p3_append_lock_unavailable"
    finally:
        rb.LOCK_TIMEOUT_SECONDS = old
        lock.unlink()
    assert path.read_bytes() == before


def test_case_F_the_existing_STARTED_and_HOLD_ordering_still_holds(ledger):
    """F. The three event writers keep their behaviour: the shared boundary was
    extracted, not redesigned."""
    path, sid = ledger
    hold = rb.append_owner_hold(scope=oc.GLOBAL_SCOPE, reason="stop",
                                head_commit=C40, utc_stamp=UTC, path=path)
    seq = int(hold.split("|")[1].strip())
    rb.append_owner_release(scope=oc.GLOBAL_SCOPE, reason="go",
                            head_commit=C40, utc_stamp=UTC,
                            releases_event_sequence=seq, path=path)
    assert oc.active_holds(path.read_text(encoding="utf-8"), "MC-DS-S001") == ()
    row = rb.append_run_started(sid, head_commit=C40, utc_stamp=UTC, path=path)
    text = path.read_text(encoding="utf-8")
    assert row in text
    chain = sreg.resolve_supplement_chain(text, sid)
    assert chain.started is True and "P3" in chain.short_ids


def test_the_S0_row_is_byte_identical_to_the_pre_repair_format(ledger):
    """Formatting and event semantics preserved: only the write is serialized."""
    path, _sid = ledger
    _s0(path, note="check", event="RUN_STARTED")
    expected = ("| + | %s | RUN_STARTED | abc1234 | main agent (s0_real_run) | "
                "[S0-T001] check |" % UTC)
    assert path.read_text(encoding="utf-8").splitlines()[-1] == expected


def test_a_tailless_ledger_refuses_instead_of_joining_two_rows(tmp_path):
    """The corrupt-row case D names, at the boundary rather than per writer."""
    path = tmp_path / "TRIAL_REGISTRY.md"
    path.write_bytes(b"| 1 | x | X | abc | Aaron | no trailing newline |")
    with pytest.raises(rb.AppendRefused) as caught:
        _s0(path)
    assert caught.value.code == "registry_tail_is_not_a_line"


def test_nothing_here_wrote_to_the_real_registry():
    import test_qros_cf_astra_repairs as R1
    assert (rb.REGISTRY_REPO_ROOT / rb.REGISTRY_PATH).read_text(
        encoding="utf-8") == R1.LIVE_REGISTRY
