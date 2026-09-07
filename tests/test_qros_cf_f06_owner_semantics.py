"""F06-OWNER-SEMANTICS: the decisive hold check and the start commit are ONE
serialized decision.

THE CONFIRMED FAILURE, which the final GPT-6 Astra certification reproduced and
which made that certification a HOLD:

    1. a start-equivalent transition performs its final owner/control check
    2. an applicable unreleased OWNER_HOLD commits
    3. the in-progress transition appends RUN_STARTED
    4. the transition returns successfully

Serialization was working. The SEMANTICS at the commit boundary were wrong, for
two separate and both-real reasons:

  * the S0 start path performed NO owner-control check anywhere -- measured, not
    inferred: `grep` for owner_control/active_holds/assert_no_owner_hold across
    `scripts/s0_real_run.py` and `src/itsf/s0/` returned nothing -- and appended
    with no `decided` snapshot, so nothing could have noticed;
  * the supplement path did check, but on bytes read BEFORE the lock. Its
    compare-and-swap made that safe in EFFECT, and "safe because a second
    mechanism happens to catch it" is not the contract.

THE REPAIR is that the check moved inside: `serialized_start_append` runs the
applicable-hold decision under the lock, on the bytes being committed against,
immediately before the write.

WHAT IS DELIBERATELY UNCHANGED. Generic ordered registry appends carry no
start-only validation -- case I asserts a non-start event still commits under an
active GLOBAL hold, because subjecting every registry event to a start refusal
would be a different and wrong change.
"""
from __future__ import annotations

import ast
import dataclasses
import sys
import tempfile
import threading
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tests"))

from itsf.mc import owner_control as oc                          # noqa: E402
from itsf.mc import registry_boundary as rb                      # noqa: E402
from itsf.mc import supplement_registry as sreg                  # noqa: E402
from itsf.s0.runner import append_registry_event_line            # noqa: E402

C40 = "a" * 40
UTC = "2026-09-07T00:00:00+00:00"
S0_TRIAL = "S0-T001"


def _hold_row(seq=90, scope="GLOBAL", reason="stop everything"):
    return ("| %d | %s | OWNER_HOLD | %s | Aaron | [%s] reason: %s |\n"
            % (seq, UTC, C40, scope, reason))


def _release_row(seq, releases, scope="GLOBAL"):
    return ("| %d | %s | OWNER_RELEASE | %s | Aaron | [%s] "
            "releases_event_sequence: %d; reason: resume |\n"
            % (seq, UTC, C40, scope, releases))


def _s0_ledger(tmp_path, name="TRIAL_REGISTRY.md"):
    path = tmp_path / name
    path.write_bytes(
        b"| 1 | 2026-01-01T00:00:00+00:00 | RUN_AUTHORIZED | " + C40.encode()
        + b" | Aaron | [S0-T001] authorized |\n")
    return path


def _s0_start(path, note="Stage C entry", event="RUN_STARTED",
              trial=S0_TRIAL):
    append_registry_event_line(path, trial, event, note, UTC, "abc1234",
                               "main agent (s0_real_run)")


def _events(path):
    return [ln.split("|")[3].strip()
            for ln in path.read_text(encoding="utf-8").splitlines()
            if ln.strip().startswith("|") and len(ln.split("|")) > 4]


@pytest.fixture
def supplement_ledger(tmp_path):
    import test_qros_cf_astra_repairs as R1
    path = tmp_path / "TRIAL_REGISTRY.md"
    sid = R1._two_row_ledger(path)
    return path, sid


# ===========================================================================
# A — HOLD FIRST
# ===========================================================================

def test_A_hold_first_refuses_the_S0_start_and_writes_nothing(tmp_path):
    path = _s0_ledger(tmp_path)
    rb.serialized_append(path, _hold_row().encode("utf-8"))
    before = path.read_bytes()
    with pytest.raises(rb.AppendRefused) as caught:
        _s0_start(path)
    assert caught.value.code == "start_refused_owner_hold_in_force"
    assert path.read_bytes() == before, "bytes changed under a refused start"
    assert "RUN_STARTED" not in _events(path)


def test_A_hold_first_refuses_the_supplement_start_and_writes_nothing(
        supplement_ledger):
    path, sid = supplement_ledger
    rb.append_owner_hold(scope=oc.GLOBAL_SCOPE, reason="stop",
                         head_commit=C40, utc_stamp=UTC, path=path)
    before = path.read_bytes()
    with pytest.raises(rb.AppendRefused) as caught:
        rb.append_run_started(sid, head_commit=C40, utc_stamp=UTC, path=path)
    # the cheap pre-lock check fires first here and keeps its own code; either
    # refusal is correct, and BOTH must leave no start row.
    assert caught.value.code in ("p3_owner_hold_in_force",
                                 "start_refused_owner_hold_in_force")
    assert path.read_bytes() == before
    assert "SUPPLEMENT_RUN_STARTED" not in path.read_text(encoding="utf-8")


# ===========================================================================
# B — START FIRST
# ===========================================================================

def test_B_start_first_commits_and_a_later_hold_is_ordered_after(tmp_path):
    path = _s0_ledger(tmp_path)
    _s0_start(path)
    assert "RUN_STARTED" in _events(path)
    rb.serialized_append(path, _hold_row().encode("utf-8"))
    ev = _events(path)
    assert ev.index("RUN_STARTED") < ev.index("OWNER_HOLD")
    assert oc.holds_applicable_to_start(
        path.read_text(encoding="utf-8"), S0_TRIAL), "the later hold was lost"
    assert not sreg.parse_registry_rows(path.read_text(encoding="utf-8"))[1]


# ===========================================================================
# C — THE CRITICAL RACE: the exact prior final-Astra failure shape
# ===========================================================================

def test_C_the_exact_astra_ordering_can_no_longer_commit_a_start(tmp_path,
                                                                 monkeypatch):
    """THE REGRESSION TEST FOR THE CONFIRMED DEFECT.

    Preliminary validation completes, the process pauses, an applicable HOLD
    commits, the start resumes -- and the FINAL SERIALIZED decision sees the
    hold. Before the repair this sequence committed RUN_STARTED and returned
    successfully.
    """
    path = _s0_ledger(tmp_path)

    # 1. the transition's preliminary validation, on the pre-hold bytes. This
    #    is the S0 pre-exposure recheck's shape: registry == Stage-A snapshot.
    snapshot = path.read_bytes()
    assert path.read_bytes() == snapshot, "preliminary validation must pass"

    # 2. the pause, and the hold commits during it. Driven at the lock so the
    #    interleaving is deterministic rather than timing-dependent.
    real_enter = rb._AppendLock.__enter__
    fired = {"once": False}

    def enter_then_hold(self):
        got = real_enter(self)
        if not fired["once"]:
            fired["once"] = True
            # committed by direct serialized write: the hold is already in the
            # authoritative bytes by the time the decision runs.
            self.path.parent.joinpath(path.name).write_bytes(
                path.read_bytes() + _hold_row().encode("utf-8"))
        return got

    monkeypatch.setattr(rb._AppendLock, "__enter__", enter_then_hold)

    # 3. resume the start.
    with pytest.raises(rb.AppendRefused) as caught:
        _s0_start(path)

    # 4. the final serialized decision saw the hold and refused.
    assert caught.value.code == "start_refused_owner_hold_in_force"
    assert "RUN_STARTED" not in _events(path), (
        "the prior failure shape still commits a start; the repair does not hold")
    assert "OWNER_HOLD" in _events(path), "the interleaved hold was lost"


def test_C_the_owner_refusal_takes_precedence_over_the_stale_snapshot_code(
        supplement_ledger, monkeypatch):
    """When both would fire, the reason reported must be the TRUE one.

    The supplement start passes a `decided` snapshot, so a hold landing under it
    also changes the bytes and the compare-and-swap would refuse too. If the CAS
    answered first the operator would be told "the registry moved" when what
    actually happened is "an owner stopped you". The owner decision is therefore
    ordered first inside the boundary, and that ordering is asserted."""
    path, sid = supplement_ledger
    real = rb.serialized_start_append

    def hold_then_start(target, addition, *, run_id, decided=None):
        rb.serialized_append(target, _hold_row().encode("utf-8"))
        return real(target, addition, run_id=run_id, decided=decided)

    monkeypatch.setattr(rb, "serialized_start_append", hold_then_start)
    with pytest.raises(rb.AppendRefused) as caught:
        rb.append_run_started(sid, head_commit=C40, utc_stamp=UTC, path=path)
    assert caught.value.code == "start_refused_owner_hold_in_force", (
        "the compare-and-swap answered before the owner decision, so the "
        "refusal names the wrong cause")
    assert "SUPPLEMENT_RUN_STARTED" not in path.read_text(encoding="utf-8")


# ===========================================================================
# D — RELEASE
# ===========================================================================

def test_D_a_valid_applicable_release_lets_the_start_proceed(tmp_path):
    path = _s0_ledger(tmp_path)
    rb.serialized_append(path, _hold_row(seq=90).encode("utf-8"))
    with pytest.raises(rb.AppendRefused):
        _s0_start(path)
    rb.serialized_append(path, _release_row(91, 90).encode("utf-8"))
    _s0_start(path)                                   # now permitted
    assert "RUN_STARTED" in _events(path)
    assert oc.holds_applicable_to_start(
        path.read_text(encoding="utf-8"), S0_TRIAL) == ()


# ===========================================================================
# E — WRONG SCOPE
# ===========================================================================

def test_E_a_non_applicable_scoped_hold_does_not_block_another_run(
        supplement_ledger):
    """A hold scoped to MC-DS-S004 must not stop MC-DS-S001."""
    path, sid = supplement_ledger
    assert sid != "MC-DS-S004"
    rb.append_owner_hold(scope="MC-DS-S004", reason="stop only that one",
                         head_commit=C40, utc_stamp=UTC, path=path)
    row = rb.append_run_started(sid, head_commit=C40, utc_stamp=UTC, path=path)
    assert row in path.read_text(encoding="utf-8")


def test_E_a_scoped_hold_for_an_S0_trial_is_NOT_EXPRESSIBLE(tmp_path):
    """THE BOUNDARY OF THIS REPAIR, asserted rather than left implicit.

    `holds_applicable_to_start` answers GLOBAL-only for an id the canonical
    grammar does not recognize. That is not a shortcut: a `[S0-T001]` scope is
    REFUSED by `parse_owner_rows` (F05), so GLOBAL is the complete applicable
    set for an S0 trial and no capability is lost.

    If scoped holds for S0 trials are ever wanted, that is an extension of the
    canonical run-id grammar and a decision about F05 -- not part of this
    bounded repair. This test is what makes that a recorded fact instead of an
    assumption."""
    path = _s0_ledger(tmp_path)
    text = path.read_text(encoding="utf-8") + _hold_row(scope=S0_TRIAL)
    with pytest.raises(oc.OwnerControlRefusal) as caught:
        oc.parse_owner_rows(text)
    assert caught.value.code == "owner_control_scope_unrecognized"
    assert oc.canonical_run_id_family(S0_TRIAL) is None


# ===========================================================================
# F — GLOBAL HOLD blocks every prohibited start scope
# ===========================================================================

def test_F_a_global_hold_refuses_both_start_families(tmp_path,
                                                     supplement_ledger):
    s0_path = _s0_ledger(tmp_path, name="S0_TRIAL_REGISTRY.md")
    rb.serialized_append(s0_path, _hold_row().encode("utf-8"))
    with pytest.raises(rb.AppendRefused) as c1:
        _s0_start(s0_path)
    assert c1.value.code == "start_refused_owner_hold_in_force"

    sup_path, sid = supplement_ledger
    rb.append_owner_hold(scope=oc.GLOBAL_SCOPE, reason="stop",
                         head_commit=C40, utc_stamp=UTC, path=sup_path)
    with pytest.raises(rb.AppendRefused):
        rb.append_run_started(sid, head_commit=C40, utc_stamp=UTC,
                              path=sup_path)
    assert "SUPPLEMENT_RUN_STARTED" not in sup_path.read_text(encoding="utf-8")


def test_F_every_start_equivalent_token_is_refused_under_a_global_hold(
        tmp_path):
    """Keyed on the TOKEN SET, so a family whose writer arrives later inherits
    the refusal instead of having to remember it."""
    for token in rb.START_EQUIVALENT_TOKENS:
        path = _s0_ledger(tmp_path, name="reg_%s.md" % token)
        rb.serialized_append(path, _hold_row().encode("utf-8"))
        before = path.read_bytes()
        with pytest.raises(rb.AppendRefused, match="owner_hold_in_force"):
            _s0_start(path, event=token)
        assert path.read_bytes() == before, f"{token} committed under a hold"


def test_F_a_bold_or_padded_start_token_cannot_evade_the_refusal(tmp_path):
    """The row grammar admits `**TOKEN**`; a start hiding behind asterisks
    would be exactly the bypass this classification exists to stop."""
    for spelling in ("**RUN_STARTED**", "  RUN_STARTED  "):
        assert rb.is_start_equivalent(spelling), spelling
        path = _s0_ledger(tmp_path, name="reg_%s.md" % abs(hash(spelling)))
        rb.serialized_append(path, _hold_row().encode("utf-8"))
        with pytest.raises(rb.AppendRefused, match="owner_hold_in_force"):
            _s0_start(path, event=spelling)


# ===========================================================================
# G — TWO STARTS
# ===========================================================================

def test_G_two_supplement_starts_preserve_the_transition_grammar(
        supplement_ledger):
    path, sid = supplement_ledger
    rb.append_run_started(sid, head_commit=C40, utc_stamp=UTC, path=path)
    with pytest.raises(rb.AppendRefused) as caught:
        rb.append_run_started(sid, head_commit=C40, utc_stamp=UTC, path=path)
    assert caught.value.code == "p3_already_present"
    text = path.read_text(encoding="utf-8")
    assert text.count("SUPPLEMENT_RUN_STARTED") == 1


def test_G_concurrent_S0_starts_are_serialized_and_none_corrupts(tmp_path):
    path = _s0_ledger(tmp_path)
    errors, done = [], []

    def worker(n):
        try:
            _s0_start(path, note="attempt-%d" % n)
            done.append(n)
        except Exception as exc:                                # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == [], f"a concurrent start failed unexpectedly: {errors}"
    text = path.read_text(encoding="utf-8")
    for i in done:
        assert text.count("attempt-%d" % i) == 1, "a row was lost/duplicated"
    for ln in text.splitlines():
        assert ln.startswith("| ") and ln.endswith(" |"), f"half row: {ln!r}"
    assert not sreg.parse_registry_rows(text)[1]


# ===========================================================================
# H — the ACTUAL S0 start transition
# ===========================================================================

def test_H_the_real_S0_transition_cannot_commit_a_start_under_a_hold(tmp_path):
    """Drives `S0Runner._atomic_run_start` itself, with the real writer wired to
    a synthetic registry. This is the confirmed Astra path end to end."""
    import test_s0_runner as T
    from itsf.s0.runner import S0Runner

    (tmp_path / "ledger").mkdir(exist_ok=True)
    reg = _s0_ledger(tmp_path / "ledger")
    rb.serialized_append(reg, _hold_row().encode("utf-8"))

    deps, events, _ = T.make_deps(tmp_path, gates=[T.ok_gate()])
    deps = dataclasses.replace(
        deps,
        append_registry_event=lambda ev, note: append_registry_event_line(
            reg, S0_TRIAL, ev, note, UTC, "abc1234", "main agent"))

    out = S0Runner(deps).run()
    assert out.ok is False, "the run reported success under an active hold"
    assert out.exposure_consumed is False, "exposure was consumed under a hold"
    assert "RUN_STARTED" not in _events(reg)
    assert "OWNER_HOLD" in _events(reg)
    # the dir is created before the append by design, so a refusal must be
    # DISCLOSED as a half transition rather than hidden.
    rdir = Path(deps.config.runs_dir)
    if rdir.exists():
        from itsf.s0.runner import HALF_TRANSITION_NAME
        assert (rdir / HALF_TRANSITION_NAME).exists(), (
            "an orphan run directory was left with no half-transition marker")


def test_H_the_real_S0_transition_still_starts_when_nothing_holds(tmp_path):
    """The positive path: a repair that refuses every start is not a repair."""
    import test_s0_runner as T
    from itsf.s0.runner import S0Runner

    (tmp_path / "ledger").mkdir(exist_ok=True)
    reg = _s0_ledger(tmp_path / "ledger")
    deps, events, _ = T.make_deps(tmp_path, gates=[T.ok_gate()])
    deps = dataclasses.replace(
        deps,
        append_registry_event=lambda ev, note: append_registry_event_line(
            reg, S0_TRIAL, ev, note, UTC, "abc1234", "main agent"))
    out = S0Runner(deps).run()
    assert out.ok is True, "the run failed with no hold in force"
    assert out.exposure_consumed is True
    assert "RUN_STARTED" in _events(reg)


# ===========================================================================
# I — generic (non-start) registry events keep their semantics
# ===========================================================================

def test_I_a_generic_S0_event_is_not_subjected_to_start_validation(tmp_path):
    """The distinction that must NOT be lost: generic ordered mutation is
    serialized and carries no start refusal. Asserted under an ACTIVE hold,
    because that is the only way to prove the start rule was not applied to
    everything."""
    path = _s0_ledger(tmp_path)
    rb.serialized_append(path, _hold_row().encode("utf-8"))
    before = path.read_bytes()
    for generic in ("STAGE_D_COMPLETE", "PRE_RUN_ATTEMPT_FAILURE",
                    "COMPLETED", "RUN_AUTHORIZED"):
        assert not rb.is_start_equivalent(generic), generic
        _s0_start(path, event=generic, note="generic %s" % generic)
    assert path.read_bytes() != before, "generic events were wrongly refused"
    assert "RUN_STARTED" not in _events(path)


def test_I_owner_rows_themselves_are_not_start_equivalent(supplement_ledger):
    """A hold or a release is not a start, so filing one is never subject to the
    start refusal -- otherwise the first hold would make the second unfileable."""
    path, _sid = supplement_ledger
    for token in (oc.OWNER_HOLD, oc.OWNER_RELEASE):
        assert not rb.is_start_equivalent(token)
    first = rb.append_owner_hold(scope=oc.GLOBAL_SCOPE, reason="one",
                                 head_commit=C40, utc_stamp=UTC, path=path)
    seq = int(first.split("|")[1].strip())
    rb.append_owner_hold(scope=oc.GLOBAL_SCOPE, reason="two",
                         head_commit=C40, utc_stamp=UTC, path=path)
    rb.append_owner_release(scope=oc.GLOBAL_SCOPE, reason="go",
                            head_commit=C40, utc_stamp=UTC,
                            releases_event_sequence=seq, path=path)
    assert path.read_text(encoding="utf-8").count("OWNER_HOLD") == 2


# ===========================================================================
# J — exception under serialization
# ===========================================================================

def test_J_a_failure_while_deciding_leaves_no_lock_and_no_partial_write(
        tmp_path, monkeypatch):
    path = _s0_ledger(tmp_path)
    lock = path.with_name(path.name + rb.LOCK_SUFFIX)
    before = path.read_bytes()

    def boom(_text, _run_id):
        raise RuntimeError("failure while the decision is being made")

    monkeypatch.setattr(oc, "assert_no_hold_blocks_start", boom)
    with pytest.raises(RuntimeError, match="while the decision"):
        _s0_start(path)
    assert not lock.exists(), "a stale lock survived a failed decision"
    assert path.read_bytes() == before, "a partial mutation escaped"
    monkeypatch.undo()
    _s0_start(path)                        # and the path still works afterwards
    assert "RUN_STARTED" in _events(path)


def test_J_an_unreadable_owner_row_refuses_the_start(tmp_path):
    """Fail-closed: an owner row nobody can parse must never read as no hold."""
    path = _s0_ledger(tmp_path)
    rb.serialized_append(
        path, _hold_row(scope="MC-DS-S004-").encode("utf-8"))   # illegal scope
    before = path.read_bytes()
    with pytest.raises(rb.AppendRefused) as caught:
        _s0_start(path)
    assert caught.value.code == "start_refused_owner_control_unreadable"
    assert path.read_bytes() == before


# ===========================================================================
# completeness guard — targets START SEMANTICS, not function names
# ===========================================================================

def _start_committing_functions():
    """Functions that hand a start-equivalent token to a registry append.

    Keyed on the TOKEN, not on a function name: a future path called anything at
    all is caught as soon as it passes a start token to a writer. Also catches
    the shape where the token arrives as a PARAMETER and is dispatched, which is
    how the S0 path looked.
    """
    tokens = set(rb.START_EQUIVALENT_TOKENS)
    out = []
    for root in ("src", "scripts"):
        for path in sorted((REPO / root).rglob("*.py")):
            rel = path.relative_to(REPO).as_posix()
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except SyntaxError:                                # pragma: no cover
                continue
            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                body = ast.unparse(node)
                called = {getattr(c.func, "attr", None) or getattr(c.func, "id", None)
                          for c in ast.walk(node) if isinstance(c, ast.Call)}
                appends = called & {"serialized_append", "serialized_start_append",
                                    "_compare_and_append",
                                    "append_registry_event_line",
                                    "append_registry_event"}
                literal = any(
                    isinstance(n, ast.Constant) and isinstance(n.value, str)
                    and n.value.strip().strip("*") in tokens
                    for n in ast.walk(node))
                dispatches = "is_start_equivalent" in called
                # Calling the start API is itself a start signal. Without this
                # clause `append_run_started` is invisible: it names its token
                # through the RUN_STARTED_TOKEN CONSTANT, not a literal -- the
                # same class of miss as a path arriving as a parameter.
                uses_api = "serialized_start_append" in called
                if appends and (literal or dispatches or uses_api):
                    out.append({"path": rel, "symbol": node.name,
                                "uses_start_api":
                                    "serialized_start_append" in called,
                                "dispatches": dispatches,
                                "generic_only":
                                    "serialized_append" in called
                                    and "serialized_start_append" not in called})
    return out


#: Registered start-committing paths. A new one fails until it is classified.
START_COMMITTERS = {
    ("src/itsf/mc/registry_boundary.py", "append_run_started"): "START_API",
    ("src/itsf/s0/runner.py", "append_registry_event_line"): "DISPATCHES",
    ("src/itsf/s0/runner.py", "_atomic_run_start"): "DELEGATES_TO_WRITER",
}


def test_the_start_guard_reaches_code_and_is_not_vacuous():
    found = _start_committing_functions()
    assert found, "the start-semantics rule matched nothing at all"
    dead = sorted(k for k in START_COMMITTERS
                  if k not in {(h["path"], h["symbol"]) for h in found})
    assert dead == [], f"registered rows the rule cannot yield: {dead}"


def test_no_start_equivalent_path_commits_outside_the_start_api():
    offenders = []
    for hit in _start_committing_functions():
        key = (hit["path"], hit["symbol"])
        if key not in START_COMMITTERS:
            offenders.append(
                "%s::%s hands a start-equivalent token to a registry append and "
                "is not registered; route it through serialized_start_append"
                % key)
            continue
        kind = START_COMMITTERS[key]
        if kind == "START_API" and not hit["uses_start_api"]:
            offenders.append("%s::%s no longer uses serialized_start_append" % key)
        if kind == "DISPATCHES" and not hit["dispatches"]:
            offenders.append(
                "%s::%s stopped classifying start-equivalent events, so a start "
                "could reach the generic writer" % key)
    assert offenders == [], "\n  " + "\n  ".join(offenders)


def test_the_decisive_owner_check_is_inside_the_serialized_boundary():
    """The property itself, on the AST: the hold decision is passed INTO the
    boundary as the validate callback, not performed before it and trusted."""
    src = (REPO / "src" / "itsf" / "mc" / "registry_boundary.py").read_text(
        encoding="utf-8")
    tree = ast.parse(src)
    fns = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}

    start = ast.unparse(fns["serialized_start_append"])
    assert "assert_no_hold_blocks_start" in start
    # ROOT B: the decision is handed to the PRIVATE physical write as `decide`.
    # It used to be a public `validate=` parameter on the generic entry, which
    # made it a caller-controlled bypass -- the reviewer committed raw start
    # bytes through it.
    assert "decide=_decide" in start, (
        "the start entry no longer hands its decision to the boundary")

    boundary = ast.unparse(fns["_physical_serialized_write"])
    lock = boundary.index("_AppendLock")
    read = boundary.index("now = target.read_bytes()")
    call = boundary.index("decide(now)")
    write = boundary.index("target.write_bytes(")
    assert lock < read < call < write, (
        "the decision is not taken under the lock between the read and the "
        "write; that ordering IS the invariant")


def test_the_start_refusal_precedes_the_stale_snapshot_refusal():
    """So the reported cause is the true one when both would fire."""
    boundary = ast.unparse(ast.parse(
        (REPO / "src" / "itsf" / "mc" / "registry_boundary.py").read_text(
            encoding="utf-8")))
    assert boundary.index("decide(now)") < boundary.index(
        "if decided is not None and now != decided")


def test_nothing_here_wrote_to_the_real_registry():
    import test_qros_cf_astra_repairs as R1
    assert (rb.REGISTRY_REPO_ROOT / rb.REGISTRY_PATH).read_text(
        encoding="utf-8") == R1.LIVE_REGISTRY
