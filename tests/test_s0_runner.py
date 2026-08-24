"""M5-T3 runner state-machine tests (synthetic; main-agent authored).

No real data, no research computation: `compute` returns a sentinel object.
Covers packet §3 exposure boundary, §6 atomic run-start, §7 stage order,
§8 failure semantics and the append-only registry writer.

SA-7 additions (2026-08-01) close the SA-6 audit findings: the guarded
logger is asserted to be ON THE WIRE (F-04), failure text degradation
(F-05), the four runinfra mechanisms are asserted to have real non-test
callers (F-06), and the scripts/s0_real_run.py gate LOGIC is exercised
against synthetic fixtures — never against the real archive (F-01/03/07/
08/09/11/34).
"""
from __future__ import annotations

import importlib.util
import inspect
import json
import subprocess
import sys
from pathlib import Path

import pytest

from itsf.contracts import (RULED_ARCHIVE_ROOT, RULED_RUNS_ROOT,
                            NAConservationError, RunConfig, RunGateError,
                            RunStage, TrialState)
from itsf.s0 import runinfra
from itsf.s0.runner import (
    GateCheck,
    RunnerDeps,
    S0Runner,
    append_registry_event_line,
    artifact_log_id,
    classify_exception,
)

CLOCK = "2026-07-31T12:00:00+00:00"
REPO = Path(__file__).resolve().parents[1]

_SCRIPT_CACHE: dict[str, object] = {}


# ===========================================================================
# L-5 ruling (2026-08-10) — real-ruled-root guard + tmp_path fixture helpers
# ===========================================================================
#
# CRITICAL (S3 file-ownership mandate): this test file must NEVER create a
# directory under the REAL ruled roots (contracts.RULED_RUNS_ROOT /
# RULED_ARCHIVE_ROOT). `make_deps` (above) and `_tmp_output_roots` (below)
# are the two places a RunConfig gets built in this file, and both pass
# EXPLICIT tmp_path-derived runs_root/archive_root — but a fixture default
# is exactly the kind of thing that silently rots, so this autouse guard is
# the INDEPENDENT, structural proof: it inspects the real filesystem
# itself, before and after EVERY test collected from this file, rather
# than trusting any single test (existing or future) to remember the rule.

_REAL_RULED_ROOTS: tuple[Path, ...] = (Path(RULED_RUNS_ROOT),
                                       Path(RULED_ARCHIVE_ROOT))


def _real_ruled_root_snapshot() -> dict[Path, frozenset[str] | None]:
    """`None` for a root that does not exist at all; otherwise the set of
    its top-level entry names. Deliberately tolerant of the root ALREADY
    holding real content (e.g. this machine has run real S0 trials before)
    — the guard's job is to prove this TEST FILE never ADDS to it, not to
    assert it is empty, which would be a false claim on a machine with
    real prior history."""
    snap: dict[Path, frozenset[str] | None] = {}
    for root in _REAL_RULED_ROOTS:
        snap[root] = (frozenset(p.name for p in root.iterdir())
                     if root.exists() else None)
    return snap


@pytest.fixture(autouse=True)
def _guard_real_ruled_roots_untouched():
    """Runs around every test in this module. Fails loudly if the set of
    top-level entries under either real ruled root changes across the
    test — that is the only way a directory could have been created (or
    removed) there by something this file did."""
    before = _real_ruled_root_snapshot()
    yield
    after = _real_ruled_root_snapshot()
    for root in _REAL_RULED_ROOTS:
        assert after[root] == before[root], (
            f"a test in this file touched the REAL ruled root {root} "
            f"(top-level entries before={before[root]!r} "
            f"after={after[root]!r}) — every RunConfig built in this file "
            "must pass an explicit tmp_path-based runs_root/archive_root "
            "override; never rely on RunConfig's ruled defaults inside a "
            "test")


def _tmp_output_roots(tmp_path: Path, *, trial: str = "S0-T001",
                      stamp: str = "20260810T000000Z"):
    """Explicit tmp_path-derived governed roots for a test that
    specifically exercises the L-5 root-governance gate or the archive
    step. `runs_root` and `archive_root` are SIBLINGS (so neither can ever
    contain the other by construction), mirroring the production layout
    `<runs_root>/runs/<trial>_<stamp>/` and `<runs_root>/attempts/<id>/`.

    Returns (runs_root, archive_root, runs_dir, attempts_dir), all
    `Path` objects, none created on disk yet — callers pass them straight
    into `make_deps(..., runs_root=..., archive_root=..., runs_dir=...,
    attempts_dir=...)`.
    """
    runs_root = tmp_path / "governed" / "runs_root"
    archive_root = tmp_path / "governed" / "archive_root"
    # R5: the OPERATIONAL readiness gate demands the ROOTS exist (it never
    # creates them — mirroring the production rule that only an operator
    # creates a real root). The per-run dirs stay uncreated.
    runs_root.mkdir(parents=True, exist_ok=True)
    archive_root.mkdir(parents=True, exist_ok=True)
    runs_dir = runs_root / "runs" / f"{trial}_{stamp}"
    attempts_dir = runs_root / "attempts" / f"{trial}-A001_{stamp}"
    return runs_root, archive_root, runs_dir, attempts_dir


def real_run_module():
    """Import scripts/s0_real_run.py once. Import MUST stay inert."""
    if "mod" not in _SCRIPT_CACHE:
        script = REPO / "scripts" / "s0_real_run.py"
        spec = importlib.util.spec_from_file_location("s0_real_run", script)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _SCRIPT_CACHE["mod"] = mod
    return _SCRIPT_CACHE["mod"]


def _as_stage_c_compute(fn):
    """M6.1.6 S1 arity shim.

    `RunnerDeps.compute` now takes the run-scoped object returned by the
    pre-exposure prepare seam. Callers of this factory (including
    tests/test_m6_chain.py, which imports it) still hand in ZERO-ARG
    computes; adapt those here so the lifecycle change stays confined to
    the runner plus this one factory. A compute that already declares a
    positional parameter is passed through UNCHANGED — which is what the
    identity assertions below depend on."""
    try:
        params = inspect.signature(fn).parameters
    except (TypeError, ValueError):                  # builtins / C callables
        params = {}
    takes_positional = any(
        p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD,
                   p.VAR_POSITIONAL)
        for p in params.values())
    if takes_positional:
        return fn
    return lambda prepared: fn()


def default_post_write_verify(runs_dir: Path, written, prepared):
    """M6.1.7 S1 — the synthetic stand-in for the production output-proof
    verifier the main agent wires into `RunnerDeps.post_write_verify`.

    It does the one thing the seam exists for: prove that each artifact's
    ON-DISK bytes are exactly the bytes the renderer produced. It is a real
    verifier, not a rubber stamp — every make_deps-built run in this suite
    (and in tests/test_m6_chain.py, which imports make_deps) therefore
    exercises the byte-fidelity invariant end to end."""
    for name, data in written:
        on_disk = (runs_dir / name).read_bytes()
        if on_disk != data:
            return False, f"on-disk bytes differ from renderer bytes: {name}"
    return True, f"{len(written)} artifact(s) byte-verified"


def make_deps(tmp_path: Path, *, gates=(), b_checks=(),
              compute=None, integrity=(), renderer=None,
              registry_events=None, log=None, append_event=None,
              runs_dir=None, attempts_dir=None, runs_root=None,
              archive_root=None, prepare=None, post_write_verify=None):
    """L-5 ruling (2026-08-10) fixture defaults, added without changing any
    EXISTING call site's behaviour.

    `runs_root` defaults to `tmp_path` itself; `archive_root` defaults to a
    SIBLING of `tmp_path` (a directory named from `tmp_path`'s own name,
    created next to it) so the two governed roots are disjoint by
    construction without needing every caller to think about it. Every
    call site in THIS repo that predates the L-5 root-governance gate
    already places `runs_dir`/`attempts_dir` somewhere under `tmp_path`
    (the historical defaults `tmp_path/"runs"/"S0-T001"` and
    `tmp_path/"attempts"/"A001"`, or an explicit override that is still a
    `tmp_path` descendant, e.g. `tmp_path / "runs" / "<stamp>"`) — so
    defaulting `runs_root` to `tmp_path` reproduces the OLD default
    `runs_dir`/`attempts_dir` values EXACTLY and keeps every such override
    validating cleanly under the new gate, with zero call-site changes.

    A test that specifically exercises the L-5 gate or the archive step
    passes explicit tmp_path-derived roots (see `_tmp_output_roots`).
    This fixture NEVER points at the real ruled roots
    (`contracts.RULED_RUNS_ROOT` / `RULED_ARCHIVE_ROOT`) — independently
    checked by the autouse `_guard_real_ruled_roots_untouched` fixture
    below, which runs around every test in this file.
    """
    resolved_runs_root = Path(runs_root) if runs_root is not None else tmp_path
    resolved_archive_root = (Path(archive_root) if archive_root is not None
                             else tmp_path.parent / f"{tmp_path.name}__archive_root")
    # R5: the OPERATIONAL readiness gate demands existing roots and never
    # creates them; the fixture is the test-world "operator action" for the
    # DEFAULT roots only. An explicit override is the caller's to create
    # (or to deliberately leave invalid for a refusal test).
    if runs_root is None:
        resolved_runs_root.mkdir(parents=True, exist_ok=True)
    if archive_root is None:
        resolved_archive_root.mkdir(parents=True, exist_ok=True)
    cfg = RunConfig(trial_id="S0-T001",
                    authorized_commit="a" * 40,
                    engineering_seed=20260731,
                    attempts_dir=str(attempts_dir or
                                     (resolved_runs_root / "attempts" / "A001")),
                    runs_dir=str(runs_dir or
                                (resolved_runs_root / "runs" / "S0-T001")),
                    assertions_path=str(tmp_path / "assertions.json"),
                    runs_root=str(resolved_runs_root),
                    archive_root=str(resolved_archive_root))
    events = registry_events if registry_events is not None else []

    def default_append(ev, note):
        events.append((ev, note))

    def default_prepare():
        """A FRESH prepared object per call — never a module-level cache, so
        two S0Runner instances can never end up sharing one."""
        return {"prepared": True}

    logs: list[str] = []
    deps = RunnerDeps(
        config=cfg,
        trial_state=TrialState.RUN_AUTHORIZED,
        gates=tuple(gates),
        structural_checks=tuple(b_checks),
        compute=_as_stage_c_compute(compute or (lambda prepared:
                                                {"sentinel": True})),
        integrity_checks=tuple(integrity),
        # M6.1.7 S1 follow-up: the Stage-E renderer takes TWO arguments,
        # (result, prepared). NO arity shim is applied here — unlike
        # `_as_stage_c_compute` above, a one-arg renderer is passed straight
        # through so the runner rejects it loudly. Adapting it here would
        # reintroduce exactly the silence the two-arg contract removes.
        render_report=renderer or (
            lambda result, prepared: {"S0_REPORT.md": "sealed"}),
        append_registry_event=append_event or default_append,
        clock_utc=lambda: CLOCK,
        log=log if log is not None else logs.append,
        # SA-11 N-E: an unwired recheck is now FAIL-CLOSED in the runner, so
        # the synthetic harness injects an explicit passing recheck.
        pre_exposure_recheck=lambda: (True, "synthetic recheck"),
        post_run_started_hook=None,
        # M6.1.6 S1: an unwired prepare seam is FAIL-CLOSED in the runner
        # (same rule as the recheck above), so the harness injects one.
        prepare_compute=prepare or default_prepare,
        # M6.1.7 S1: an unwired post-write verification seam is likewise
        # FAIL-CLOSED (pre-exposure), so the harness injects a real one.
        post_write_verify=post_write_verify or default_post_write_verify)
    return deps, events, logs


def guarded_logger(sink: list[str]):
    """Exactly the wrapper scripts/s0_real_run.py injects (F-04)."""
    def _log(message: str) -> None:
        runinfra.validate_log_event(message)
        sink.append(message)
    return _log


def ok_gate(name="g"):
    return GateCheck(name, lambda: (True, "ok"))


def bad_gate(name="g"):
    return GateCheck(name, lambda: (False, "boom"))


# --- Stage A/B: pre-exposure failures ---------------------------------------

def test_stage_a_gate_failure_is_pre_run_no_exposure(tmp_path):
    deps, events, _ = make_deps(tmp_path, gates=[ok_gate("g1"),
                                                 bad_gate("g2")])
    out = S0Runner(deps).run()
    assert out.ok is False
    assert out.exposure_consumed is False
    assert out.failure_kind == "pre_run_attempt"
    assert out.failed_gate == "g2"
    assert out.terminal_stage == RunStage.A_PRECHECK
    # attempt artifacts written; runs dir NEVER created
    assert (out.attempts_dir / "PRE_RUN_ATTEMPT_FAILURE.md").exists()
    assert not Path(deps.config.runs_dir).exists()
    # registry: only the attempt-failure event, no RUN_STARTED
    assert [e for e, _ in events] == ["PRE_RUN_ATTEMPT_FAILURE"]


def test_stage_b_failure_also_pre_run_and_gates_ran_first(tmp_path):
    deps, events, _ = make_deps(
        tmp_path, gates=[ok_gate("g1")],
        b_checks=[GateCheck("b1", lambda: (False, "count mismatch"))])
    out = S0Runner(deps).run()
    assert out.failure_kind == "pre_run_attempt"
    assert out.terminal_stage == RunStage.B_LOAD_VALIDATE
    assert out.exposure_consumed is False
    assert "A_PRECHECK" in out.stages_completed
    assert not Path(deps.config.runs_dir).exists()
    assert [e for e, _ in events] == ["PRE_RUN_ATTEMPT_FAILURE"]


# --- atomic run start (packet §6) -------------------------------------------

def test_atomic_run_start_pairs_dir_and_run_started_event(tmp_path):
    deps, events, _ = make_deps(tmp_path, gates=[ok_gate()])
    out = S0Runner(deps).run()
    assert out.ok is True
    assert Path(deps.config.runs_dir).is_dir()
    assert [e for e, _ in events] == ["RUN_STARTED", "COMPLETED"]
    assert out.exposure_consumed is True


def test_preexisting_runs_dir_blocks_before_exposure(tmp_path):
    deps, events, _ = make_deps(tmp_path, gates=[ok_gate()])
    Path(deps.config.runs_dir).mkdir(parents=True)
    out = S0Runner(deps).run()
    assert out.failure_kind == "pre_run_attempt"
    assert out.exposure_consumed is False
    assert "RUN_STARTED" not in [e for e, _ in events]


# --- Stage C+ failures burn the trial (packet §8) ---------------------------

def test_compute_failure_burns_trial_and_keeps_outputs(tmp_path):
    def broken():
        raise ValueError("synthetic compute crash")
    deps, events, _ = make_deps(tmp_path, gates=[ok_gate()], compute=broken)
    out = S0Runner(deps).run()
    assert out.failure_kind == "run_failure"
    assert out.exposure_consumed is True
    assert out.terminal_stage == RunStage.C_COMPUTE
    assert (out.runs_dir / "RUN_FAILURE_REPORT.md").exists()
    assert (out.runs_dir / "RUN_FAILURE_REPORT.json").exists()
    assert [e for e, _ in events] == ["RUN_STARTED", "FAILED"]
    payload = json.loads(
        (out.runs_dir / "RUN_FAILURE_REPORT.json").read_text("utf-8"))
    assert payload["report_type"] == "RUN_FAILURE_REPORT"


def test_integrity_failure_is_stage_d_run_failure(tmp_path):
    deps, events, _ = make_deps(
        tmp_path, gates=[ok_gate()],
        integrity=[lambda r: (False, "NA conservation broken")])
    out = S0Runner(deps).run()
    assert out.failure_kind == "run_failure"
    assert out.terminal_stage == RunStage.D_INTEGRITY
    assert "C_COMPUTE" in out.stages_completed


# --- happy path order + sealed report ---------------------------------------

def test_full_run_stage_order_and_sealed_report(tmp_path):
    deps, events, logs = make_deps(
        tmp_path, gates=[ok_gate("g1"), ok_gate("g2")],
        b_checks=[GateCheck("b1", lambda: (True, "ok"))],
        integrity=[lambda r: (True, "ok")])
    out = S0Runner(deps).run()
    assert out.ok is True
    assert out.stages_completed == ("A_PRECHECK", "B_LOAD_VALIDATE",
                                    "C_COMPUTE", "D_INTEGRITY", "E_REPORT",
                                    "F_SEALED")
    assert (out.runs_dir / "S0_REPORT.md").read_text("utf-8") == "sealed"
    assert events == [("RUN_STARTED",
                       "Stage C entry; researcher exposure seq consumed"),
                      ("COMPLETED", "S0 report sealed")]
    # Stage C log lines are schema-shaped only (F-04)
    assert "stage=C_COMPUTE status=start" in logs
    assert "stage=C_COMPUTE status=end" in logs


# --- registry append-only writer --------------------------------------------

def test_registry_append_never_rewrites_existing_bytes(tmp_path):
    reg = tmp_path / "TRIAL_REGISTRY.md"
    reg.write_text("| header |\n", encoding="utf-8")
    before = reg.read_text("utf-8")
    append_registry_event_line(reg, "S0-T001", "RUN_STARTED", "note",
                               CLOCK, "b" * 7, "main agent")
    after = reg.read_text("utf-8")
    assert after.startswith(before)                  # strictly appended
    assert "RUN_STARTED" in after.splitlines()[-1]


def test_zero_cli_argument_entrypoint():
    """Packet §5: the real entrypoint must accept no arguments at all."""
    mod = real_run_module()                          # import must be inert
    import inspect
    assert inspect.signature(mod.main).parameters == {}
    assert getattr(mod, "USES_ARGPARSE", False) is False


# ===========================================================================
# F-04 — the Stage-C log guard is actually ON THE WIRE
# ===========================================================================


def test_every_runner_message_passes_the_log_guard_happy_path(tmp_path):
    sink: list[str] = []
    deps, _, _ = make_deps(tmp_path, gates=[ok_gate()],
                           b_checks=[GateCheck("b1", lambda: (True, "ok"))],
                           integrity=[lambda r: (True, "ok")],
                           log=guarded_logger(sink))
    out = S0Runner(deps).run()
    assert out.ok is True, "a guarded logger must not break the happy path"
    assert sink, "the runner must actually log through the guard"
    for message in sink:                             # re-assert independently
        runinfra.validate_log_event(message)


@pytest.mark.parametrize("scenario", ["gate_fail", "compute_fail"])
def test_every_runner_message_passes_the_log_guard_on_failure(tmp_path,
                                                              scenario):
    sink: list[str] = []
    kwargs = {"log": guarded_logger(sink)}
    if scenario == "gate_fail":
        kwargs["gates"] = [bad_gate("g1")]
    else:
        def boom():
            raise ValueError("synthetic crash 0.4213 oracle label")
        kwargs["gates"] = [ok_gate()]
        kwargs["compute"] = boom
    deps, _, _ = make_deps(tmp_path, **kwargs)
    out = S0Runner(deps).run()
    assert out.ok is False
    assert sink
    for message in sink:
        runinfra.validate_log_event(message)


def test_logger_rejection_escalates_to_a_stage_failure(tmp_path):
    """A guard rejection must stop the run, never be swallowed."""
    def hostile_log(message: str) -> None:
        raise runinfra.LogLeakError("synthetic guard rejection")

    deps, events, _ = make_deps(tmp_path, gates=[ok_gate()], log=hostile_log)
    out = S0Runner(deps).run()
    assert out.ok is False
    assert out.failed_gate == "log_guard"
    assert out.exposure_consumed is False
    assert [e for e, _ in events] == ["PRE_RUN_ATTEMPT_FAILURE"]


# ===========================================================================
# F-05 — failure-text degradation (error class + opaque incident id)
# ===========================================================================


def test_raw_failure_text_never_reaches_registry_or_report(tmp_path):
    secret = "trading day 2013-05-27 y_cont 0.7314"

    def broken():
        raise ValueError(secret)

    deps, events, _ = make_deps(tmp_path, gates=[ok_gate()], compute=broken)
    out = S0Runner(deps).run()

    assert out.incident_id.startswith("INC-")
    note = dict(events)["FAILED"]
    assert secret not in note and "ValueError" not in note
    assert out.incident_id in note

    report = (out.runs_dir / "RUN_FAILURE_REPORT.md").read_text("utf-8")
    payload = json.loads((out.runs_dir / "RUN_FAILURE_REPORT.json")
                         .read_text("utf-8"))
    assert secret not in report
    assert secret not in json.dumps(payload)
    assert out.incident_id in payload["failure_reason"]

    sealed = (out.runs_dir / f"INCIDENT_{out.incident_id}.md").read_text("utf-8")
    assert secret in sealed                          # raw detail is retained
    assert "SEALED FAILURE DETAIL" in sealed


def test_pre_run_failure_also_seals_detail_in_attempt_dir(tmp_path):
    secret = "porcelain shows M features_private_notes.txt"
    deps, events, _ = make_deps(
        tmp_path, gates=[GateCheck("git_clean", lambda: (False, secret))])
    out = S0Runner(deps).run()
    note = dict(events)["PRE_RUN_ATTEMPT_FAILURE"]
    assert secret not in note
    assert out.incident_id in note
    assert secret in (out.attempts_dir
                      / f"INCIDENT_{out.incident_id}.md").read_text("utf-8")


# ===========================================================================
# F-27 — exception_type comes from isinstance, not from parsing text
# ===========================================================================


def test_exception_type_cannot_be_spoofed_by_message_text(tmp_path):
    def liar():
        raise ValueError("LogLeakError: pretend this was a governance abort")

    deps, _, _ = make_deps(tmp_path, gates=[ok_gate()], compute=liar)
    out = S0Runner(deps).run()
    payload = json.loads((out.runs_dir / "RUN_FAILURE_REPORT.json")
                         .read_text("utf-8"))
    assert payload["exception_type"] == "Unknown"


def test_check_return_value_cannot_dress_itself_as_a_contract_error(tmp_path):
    """The pre-fix runner read exception_type off the head of the DETAIL
    STRING — and a check that merely RETURNS (False, "LogLeakError: ...")
    controls that string completely."""
    deps, _, _ = make_deps(
        tmp_path, gates=[ok_gate()],
        integrity=[lambda r: (False, "LogLeakError: fabricated by the check")])
    out = S0Runner(deps).run()
    payload = json.loads((out.runs_dir / "RUN_FAILURE_REPORT.json")
                         .read_text("utf-8"))
    assert payload["exception_type"] == "Unknown"
    assert out.terminal_stage == RunStage.D_INTEGRITY


def test_real_contract_error_is_classified_by_isinstance(tmp_path):
    def na_broken(result):
        raise NAConservationError("unregistered reason in F5")

    deps, _, _ = make_deps(tmp_path, gates=[ok_gate()], integrity=[na_broken])
    out = S0Runner(deps).run()
    payload = json.loads((out.runs_dir / "RUN_FAILURE_REPORT.json")
                         .read_text("utf-8"))
    assert payload["exception_type"] == "NAConservationError"
    assert out.terminal_stage == RunStage.D_INTEGRITY


def test_classify_exception_unit():
    assert classify_exception(RunGateError("x")) == "RunGateError"
    assert classify_exception(NAConservationError("x")) == "NAConservationError"
    assert classify_exception(ValueError("RunGateError: nope")) == "Unknown"
    assert classify_exception(None) == "Unknown"


# ===========================================================================
# F-06 — Stage E manifest chain + Stage F verification are wired
# ===========================================================================


def test_stage_e_writes_hash_chain_and_stage_f_verifies_it(tmp_path):
    deps, _, sink_logs = make_deps(
        tmp_path, gates=[ok_gate()],
        renderer=lambda result, prepared: {"S0_REPORT.md": "sealed",
                                           "counts.md": "n=1"})
    out = S0Runner(deps).run()
    assert out.ok is True

    manifest = out.runs_dir / "manifest.jsonl"
    records = [json.loads(ln) for ln in
               manifest.read_text("utf-8").splitlines() if ln.strip()]
    kinds = [r["record_type"] for r in records]
    assert kinds.count("file") == 2
    assert kinds[-1] == "stage_seal"
    verdict = runinfra.verify_chain_records(
        records, file_hash_provider=lambda rel:
        runinfra.hashlib.sha256((out.runs_dir / rel).read_bytes()).hexdigest())
    assert verdict.valid, verdict.errors
    assert verdict.sealed_stages == ("E_REPORT",)


def test_stage_f_fails_when_a_sealed_artifact_is_altered(tmp_path, monkeypatch):
    """Stage F must actually re-verify: tamper with an artifact between the
    manifest append and the verification and the run must fail."""
    deps, _, _ = make_deps(tmp_path, gates=[ok_gate()])
    original = S0Runner._record_artifacts

    def tampering_record(self, rdir, stage, written):
        original(self, rdir, stage, written)
        (rdir / "S0_REPORT.md").write_text("TAMPERED", encoding="utf-8")

    monkeypatch.setattr(S0Runner, "_record_artifacts", tampering_record)
    out = S0Runner(deps).run()

    assert out.ok is False
    assert out.terminal_stage == RunStage.F_SEALED
    assert out.failed_gate == "verify_chain"
    assert out.exposure_consumed is True


def test_stage_e_requires_at_least_one_artifact(tmp_path):
    deps, _, _ = make_deps(tmp_path, gates=[ok_gate()],
                           renderer=lambda result, prepared: {})
    out = S0Runner(deps).run()
    assert out.ok is False
    assert out.terminal_stage == RunStage.E_REPORT


# ===========================================================================
# F-08 / F-10 — orphan disclosure, prefix scan, gate exceptions
# ===========================================================================


def test_prior_run_directory_for_same_trial_blocks_even_with_new_stamp(tmp_path):
    runs_root = tmp_path / "runs"
    (runs_root / "S0-T001_20260731T090000Z").mkdir(parents=True)
    deps, events, _ = make_deps(
        tmp_path, gates=[ok_gate()],
        runs_dir=runs_root / "S0-T001_20260731T120000Z")
    out = S0Runner(deps).run()
    assert out.failure_kind == "pre_run_attempt"
    assert out.exposure_consumed is False
    assert "RUN_STARTED" not in [e for e, _ in events]


def test_failed_run_started_append_leaves_half_transition_marker(tmp_path):
    calls: list[str] = []

    def flaky_append(event, note):
        calls.append(event)
        if event == "RUN_STARTED":
            raise OSError("registry locked by another process")

    deps, _, _ = make_deps(tmp_path, gates=[ok_gate()],
                           append_event=flaky_append)
    out = S0Runner(deps).run()
    marker = Path(deps.config.runs_dir) / "HALF_TRANSITION.md"
    assert marker.exists()
    text = marker.read_text("utf-8")
    assert "ORPHAN" in text and "S0-T001" in text
    assert out.failure_kind == "pre_run_attempt"
    assert "PRE_RUN_ATTEMPT_FAILURE" in calls


def test_gate_that_raises_becomes_a_pre_run_failure_not_a_traceback(tmp_path):
    def exploding():
        raise KeyError("gate blew up")

    deps, events, _ = make_deps(
        tmp_path, gates=[GateCheck("locked_input_hashes", exploding)])
    out = S0Runner(deps).run()
    assert out.failure_kind == "pre_run_attempt"
    assert out.failed_gate == "locked_input_hashes"
    assert out.exposure_consumed is False
    assert [e for e, _ in events] == ["PRE_RUN_ATTEMPT_FAILURE"]
    assert (out.attempts_dir / "PRE_RUN_ATTEMPT_FAILURE.md").exists()


def test_structural_check_that_raises_is_also_pre_run(tmp_path):
    def exploding():
        raise RuntimeError("structural check blew up")

    deps, _, _ = make_deps(tmp_path, gates=[ok_gate()],
                           b_checks=[GateCheck("b1", exploding)])
    out = S0Runner(deps).run()
    assert out.failure_kind == "pre_run_attempt"
    assert out.terminal_stage == RunStage.B_LOAD_VALIDATE
    assert not Path(deps.config.runs_dir).exists()


# ===========================================================================
# scripts/s0_real_run.py — registry parsing / authorization (F-01, F-11)
# ===========================================================================


HEADER = ("| # | utc | event | commit | actor | 原因/备注 |\n"
          "|---|---|---|---|---|---|\n")


def _sentence(commit: str, trial_id: str = "S0-T001") -> str:
    mod = real_run_module()
    return mod.AUTHORIZATION_SENTENCE_TEMPLATE.format(trial_id=trial_id,
                                                      commit=commit)


def _auth_row(seq, commit: str, trial_id: str = "S0-T001",
              cell: str | None = None) -> str:
    """One format-legal RUN_AUTHORIZED row (IR-25: cell == sentence commit
    unless the test overrides `cell` to prove the inconsistency rejection)."""
    return (f"| {seq} | 2026-08-01 | RUN_AUTHORIZED | "
            f"{commit if cell is None else cell} | Aaron | "
            f"{_sentence(commit, trial_id)} |\n")


def _supersede_row(seq, target_seq, target_commit: str,
                   trial_id: str = "S0-T001",
                   reason: str = "RUNTIME_SELFBLOCK_FIX",
                   incident: str = "INC-e6fe49ec63de",
                   note: str | None = None) -> str:
    if note is None:
        note = (f"[{trial_id}] supersedes_event_sequence: {target_seq}; "
                f"superseded_commit: {target_commit}; "
                f"reason_code: {reason}; incident_id: {incident}")
    return (f"| {seq} | 2026-08-01 | RUN_AUTHORIZATION_SUPERSEDED | - | "
            f"main agent | {note} |\n")


def test_prose_mentioning_run_authorized_is_not_an_event_row():
    mod = real_run_module()
    text = ("状态机见 packet §0: ... RUN_AUTHORIZED → RUNNING → COMPLETED。\n"
            + HEADER
            + "| 1 | 2026-07-31 | TRIAL_REGISTERED | 79d7ca3 | main | 登记 |\n")
    rows = mod.parse_registry_events(text)
    assert [r["event"] for r in rows] == ["TRIAL_REGISTERED"]
    row, commit, detail = mod.find_authorization_event(text)
    assert row is None and commit == ""
    assert "no RUN_AUTHORIZED row" in detail


def test_live_registry_structurally_valid_in_any_state():
    """IR-25 (Aaron P1-B): STATE-AGNOSTIC. Suite outcome must not depend on
    whether the real registry is currently unauthorized or authorized.
    Asserted instead: the real registry parses; its append-only prefix is
    intact; the authorization chain is well-formed (no malformed row, no
    broken supersede reference); live authorizations number at most one;
    and if one exists it satisfies the strict verbatim-§10 validation."""
    import re as _re
    mod = real_run_module()
    text = mod.REGISTRY.read_text(encoding="utf-8")
    rows = mod.parse_registry_events(text)
    assert rows, "real registry parsed to zero event rows"
    assert [r["event"] for r in rows[:3]] == [
        "TRIAL_REGISTERED", "GOVERNANCE_FRAMEWORK_APPROVED",
        "PACKET_APPROVED"]
    live, problem = mod.resolve_authorizations(text)
    assert problem == "", problem
    assert len(live) <= 1
    if live:
        row, commit = live[0]
        assert _re.match(r"^[0-9a-f]{40}$", commit)
        assert _sentence(commit) in row["note"]
        assert row["commit"] == commit


def test_exact_sentence_with_full_hash_is_accepted():
    mod = real_run_module()
    commit = "b" * 40
    text = HEADER + _auth_row(4, commit)
    row, parsed, detail = mod.find_authorization_event(text)
    assert row is not None
    assert parsed == commit, detail


@pytest.mark.parametrize("note", [
    "开始跑吧",
    "可以跑，授权 S0-T001",
    "启动第一次真实S0，授权trial_id: S0-T001，使用commit: b62016a",
    "启动第一次真实S0, 授权trial_id: S0-T001, 使用commit: " + "b" * 40,
    "启动第一次真实S0，授权trial_id: S0-T002，使用commit: " + "b" * 40,
    "启动第一次真实S0，授权trial_id: S0-T001，使用commit: " + "B" * 40,
])
def test_near_miss_authorization_notes_are_rejected(note):
    mod = real_run_module()
    text = HEADER + f"| 4 | 2026-08-01 | RUN_AUTHORIZED | b62016a | Aaron | {note} |\n"
    _, commit, _ = mod.find_authorization_event(text)
    assert commit == ""


def test_sentence_in_a_non_run_authorized_row_is_rejected():
    mod = real_run_module()
    text = HEADER + (f"| 4 | 2026-08-01 | NOTE | b62016a | Aaron | "
                     f"{_sentence('c' * 40)} |\n")
    _, commit, _ = mod.find_authorization_event(text)
    assert commit == ""


def test_two_live_authorization_rows_are_rejected():
    """IR-25 fixture 8: two format-legal LIVE authorizations fail closed."""
    mod = real_run_module()
    text = HEADER + _auth_row(4, "c" * 40) + _auth_row(5, "d" * 40)
    _, commit, detail = mod.find_authorization_event(text)
    assert commit == ""
    assert "2 live RUN_AUTHORIZED rows" in detail


# --- IR-25 supersede semantics (Aaron P2-A, fixtures 4/7/9-13) --------------

def test_fenced_authorization_row_is_documentation_not_an_event():
    """IR-25 fixture 4: a fully legal row quoted inside a ``` fence."""
    mod = real_run_module()
    text = (HEADER
            + "| 1 | 2026-07-31 | TRIAL_REGISTERED | 79d7ca3 | main | 登记 |\n"
            + "```\n" + _auth_row(4, "c" * 40) + "```\n")
    rows = mod.parse_registry_events(text)
    assert [r["event"] for r in rows] == ["TRIAL_REGISTERED"]
    _, commit, detail = mod.find_authorization_event(text)
    assert commit == "" and "no RUN_AUTHORIZED row" in detail


def test_commit_cell_sentence_mismatch_fails_closed():
    """IR-25 fixture 7: row commit cell != sentence commit (incl. the old
    abbreviated-cell style) is an internal inconsistency, never accepted."""
    mod = real_run_module()
    for cell in ("b62016a", "c" * 40):
        text = HEADER + _auth_row(4, "b" * 40, cell=cell)
        _, commit, detail = mod.find_authorization_event(text)
        assert commit == "", cell
        assert "commit cell" in detail


def test_superseded_authorization_resolves_to_unauthorized():
    """IR-25 fixture 9: one authorization, then a legal supersede -> 0 live."""
    mod = real_run_module()
    text = (HEADER + _auth_row(6, "c" * 40)
            + _supersede_row(7, 6, "c" * 40))
    live, problem = mod.resolve_authorizations(text)
    assert problem == "" and live == []
    _, commit, detail = mod.find_authorization_event(text)
    assert commit == "" and "no RUN_AUTHORIZED row" in detail


def test_superseded_old_plus_legal_new_authorizes_the_new():
    """IR-25 fixture 9b — the production reauthorization path: dead old row,
    one live new row -> the new commit is authorized."""
    mod = real_run_module()
    text = (HEADER + _auth_row(6, "c" * 40)
            + _supersede_row(7, 6, "c" * 40)
            + _auth_row(8, "d" * 40))
    row, commit, detail = mod.find_authorization_event(text)
    assert commit == "d" * 40, detail
    assert row["seq"] == "8"


def test_supersede_of_nonexistent_sequence_fails_closed():
    """IR-25 fixture 10."""
    mod = real_run_module()
    text = (HEADER + _auth_row(6, "c" * 40)
            + _supersede_row(7, 99, "c" * 40))
    live, problem = mod.resolve_authorizations(text)
    assert live == [] and "not an existing RUN_AUTHORIZED row" in problem
    _, commit, _ = mod.find_authorization_event(text)
    assert commit == ""


def test_forward_referencing_supersede_fails_closed():
    """IR-25 fixture 11: the supersede appears BEFORE its target row."""
    mod = real_run_module()
    text = (HEADER + _supersede_row(5, 6, "c" * 40)
            + _auth_row(6, "c" * 40))
    live, problem = mod.resolve_authorizations(text)
    assert live == [] and "forward reference" in problem


def test_duplicate_supersede_fails_closed():
    """IR-25 fixture 12."""
    mod = real_run_module()
    text = (HEADER + _auth_row(6, "c" * 40)
            + _supersede_row(7, 6, "c" * 40)
            + _supersede_row(8, 6, "c" * 40))
    live, problem = mod.resolve_authorizations(text)
    assert live == [] and "duplicate supersede" in problem


def test_supersede_reference_mismatches_fail_closed():
    """IR-25 fixture 13: wrong trial in the supersede note, or a
    superseded_commit that differs from the referenced row's commit."""
    mod = real_run_module()
    base = HEADER + _auth_row(6, "c" * 40)
    wrong_trial = base + _supersede_row(7, 6, "c" * 40, trial_id="S0-T002")
    live, problem = mod.resolve_authorizations(wrong_trial)
    assert live == [] and "S0-T002" in problem
    wrong_commit = base + _supersede_row(7, 6, "d" * 40)
    live, problem = mod.resolve_authorizations(wrong_commit)
    assert live == [] and "does not equal the referenced row" in problem


def test_unparsable_supersede_note_fails_closed():
    """IR-25: a supersede row missing required fields is never ignored."""
    mod = real_run_module()
    text = (HEADER + _auth_row(6, "c" * 40)
            + _supersede_row(7, 6, "c" * 40,
                             note="[S0-T001] supersedes event 6, see incident"))
    live, problem = mod.resolve_authorizations(text)
    assert live == [] and "not machine-parsable" in problem


def test_dual_state_satisfiability_layouts(tmp_path, monkeypatch):
    """IR-25 (Aaron §4): both layouts resolve through the PRODUCTION parser
    against production-shaped registry bytes — no mocks.

    Layout A: the real registry exactly as committed (whatever its state,
    the chain must be well-formed — this is what the battery/full_pytest
    gate sees at run time). Layout B: the real bytes plus one appended
    format-legal RUN_AUTHORIZED row whose commit equals THIS layout's git
    HEAD; the production resolver and the production snapshot chain must
    both authorize exactly that commit."""
    import subprocess
    mod = real_run_module()
    real = mod.REGISTRY.read_text(encoding="utf-8")
    head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                          text=True, cwd=REPO).stdout.strip()
    assert len(head) == 40

    # Layout A — as committed: well-formed, at most one live.
    live, problem = mod.resolve_authorizations(real)
    assert problem == "", problem
    assert len(live) <= 1

    # Layout B — exactly one live authorization for this HEAD. IR-25
    # erratum (SA-14): retire whatever is ALREADY live in the real bytes
    # first — without this, the test itself is a second self-block: in the
    # authorized state the probe row makes 2 live rows, the parser
    # correctly fails closed, and the suite goes red mid-run.
    reg_b = tmp_path / "TRIAL_REGISTRY.md"
    n_supersedes = real.count("RUN_AUTHORIZATION_SUPERSEDED")
    retire = "".join(_supersede_row(89, r["seq"], c) for r, c in live)
    text_b = real + retire + _auth_row(90 + n_supersedes, head)
    reg_b.write_text(text_b, encoding="utf-8")
    row, commit, detail = mod.find_authorization_event(text_b)
    assert commit == head, detail
    monkeypatch.setattr(mod, "REGISTRY", reg_b)
    snap = mod.RealChain().authorization_snapshot()
    assert snap["authorized_commit"] == head
    assert snap["exact_authorization_text_sha256"]


def test_head_gate_compares_against_the_parsed_commit_not_head(tmp_path):
    """F-11: authorized_commit is the value from Aaron's sentence; the gate
    must fail when HEAD differs, and never compare HEAD with itself."""
    mod = real_run_module()
    registry = tmp_path / "TRIAL_REGISTRY.md"
    registry.write_text(HEADER + _auth_row(4, "d" * 40), encoding="utf-8")
    gates = {g.name: g for g in mod.build_gates(registry=registry)}
    ok, detail = gates["run_authorized_event"].check()
    assert ok, detail
    ok, detail = gates["head_matches_authorized_commit"].check()
    assert not ok
    assert "does not equal" in detail


# ===========================================================================
# scripts/s0_real_run.py — clean gate allowlist (F-03) and env hygiene (F-09)
# ===========================================================================


@pytest.mark.parametrize("line,exempt", [
    (" M ops/TRIAL_REGISTRY.md", True),
    ("?? attempts/S0-T001-A20260801T000000Z/", True),
    ("?? runs/S0-T001_20260801T000000Z/manifest.jsonl", True),
    (" M src/itsf/s0/labels.py", False),
    ("?? scripts/sneaky_patch.py", False),
    ("R  a.py -> src/itsf/s0/features.py", False),
])
def test_clean_gate_allowlist(line, exempt):
    mod = real_run_module()
    assert mod._clean_gate_exempt(line) is exempt


def test_gitignore_covers_attempt_and_run_directories():
    body = (REPO / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "attempts/" in body
    assert "runs/" in body


def test_clean_env_drops_gate_weakening_variables(monkeypatch):
    mod = real_run_module()
    for var in ("PYTEST_ADDOPTS", "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE",
                "GIT_CONFIG_GLOBAL", "PYTHONPATH", "PYTHONSTARTUP"):
        monkeypatch.setenv(var, "hostile")
    env = mod.clean_env()
    for var in ("PYTEST_ADDOPTS", "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE",
                "GIT_CONFIG_GLOBAL", "PYTHONPATH", "PYTHONSTARTUP"):
        assert var not in env
    assert "PATH" in env or "Path" in env or env  # allowlist survives


def test_clean_env_keeps_windows_shell_folder_variables():
    """Scrubbing too hard is its own failure mode: with SystemDrive absent a
    child process materialises a literal '%SystemDrive%' directory in its
    cwd (= the repo), which would then break the git-clean gate."""
    mod = real_run_module()
    import os
    env = mod.clean_env()
    for var in ("SYSTEMDRIVE", "SYSTEMROOT", "PROGRAMDATA", "TEMP"):
        if var in os.environ:
            assert env.get(var) == os.environ[var], var


def test_subprocess_with_clean_env_leaves_no_stray_directory(tmp_path):
    mod = real_run_module()
    before = set(p.name for p in tmp_path.iterdir())
    subprocess.run(
        [sys.executable, "-c",
         "import pathlib;pathlib.Path.home();"
         "import tempfile;tempfile.gettempdir()"],
        capture_output=True, text=True, cwd=str(tmp_path), env=mod.clean_env())
    assert set(p.name for p in tmp_path.iterdir()) == before


def test_subprocess_actually_receives_the_scrubbed_env(monkeypatch):
    mod = real_run_module()
    monkeypatch.setenv("PYTEST_ADDOPTS", "-k nothing_matches")
    proc = subprocess.run(
        [sys.executable, "-c",
         "import os;print(os.environ.get('PYTEST_ADDOPTS','ABSENT'))"],
        capture_output=True, text=True, env=mod.clean_env())
    assert proc.stdout.strip() == "ABSENT"


@pytest.mark.parametrize("output,expected", [
    ("347 passed in 13.83s", 347),
    ("340 passed, 7 skipped in 1.00s", 347),
    ("1 failed, 346 passed in 2.00s", 347),
    ("5 passed, 342 deselected in 0.30s", 347),
    ("no summary here", None),
])
def test_parse_pytest_collected(output, expected):
    mod = real_run_module()
    assert mod.parse_pytest_collected(output) == expected


def test_pytest_gate_floor_is_the_audit_baseline():
    """SA-10 N3: the floor tracks the CURRENT suite, closing the
    silent-collection-drop headroom."""
    mod = real_run_module()
    assert mod.MIN_COLLECTED_TESTS == 4051


# ===========================================================================
# scripts/s0_real_run.py — the added hard gates (F-07, F-08, F-34)
# ===========================================================================


def test_gate_list_covers_every_packet_section_9_gate():
    mod = real_run_module()
    names = [g.name for g in mod.build_gates()]
    assert names == [
        "parent_env_clean",                      # SA-10 N4 / F-09(b)
        "frozen_constants_in_process",           # SA-6 F-19
        "real_run_allowed",                      # §9.6/8/9 via guards (F-34)
        "git_clean",                             # §9.1
        "run_authorized_event",                  # §9.12
        "head_matches_authorized_commit",        # §9.2 + §9.13
        "key_closure_attestation_present",       # §9.7
        "locked_input_hashes",                   # §9.10
        "raw_file_set_digest",                   # §4 set digest
        "seal_check",                            # §9.4
        "structure_assertions",                  # §9.5
        "runs_dir_absent_for_trial",             # §9.11
        "full_pytest",                           # §9.3
    ]
    assert len(names) == len(set(names))


def test_first_gate_delegates_to_guards_assert_real_run_allowed(monkeypatch):
    """F-34: no second implementation of the frozen-hash/flag checks."""
    mod = real_run_module()
    from itsf import guards
    calls: list[str] = []
    monkeypatch.setattr(guards, "assert_real_run_allowed",
                        lambda *a, **k: calls.append("called"))
    gate = {g.name: g for g in mod.build_gates()}["real_run_allowed"]
    ok, _ = gate.check()
    assert ok and calls == ["called"]


def test_locked_inputs_include_the_assertion_file_and_a1_manifest():
    mod = real_run_module()
    # M5-T5 rerun lock (IR-22/23/24 applied; IR-24 divergence==0 evidenced)
    assert mod.LOCKED["preflight_json"][1].startswith("9d6dd1c1")
    assert mod.LOCKED_EXTERNAL["a1_manifest"][1].startswith("d8d1edc7")
    assert mod.RAW_FILE_SET_SHA256.startswith("08fca11b")


def test_locked_preflight_hash_matches_the_repo_file():
    """Compare-only: the assertion file's bytes at this commit."""
    mod = real_run_module()
    rel, want = mod.LOCKED["preflight_json"]
    assert mod._sha(REPO / rel) == want


def test_raw_file_set_digest_is_order_independent_and_content_sensitive():
    mod = real_run_module()
    a = [("x.dbn.zst", 10, "a" * 64), ("y.dbn.zst", 20, "b" * 64)]
    assert mod.compute_raw_file_set_sha256(a) == \
        mod.compute_raw_file_set_sha256(list(reversed(a)))
    renamed = [("z.dbn.zst", 10, "a" * 64), ("y.dbn.zst", 20, "b" * 64)]
    assert mod.compute_raw_file_set_sha256(renamed) != \
        mod.compute_raw_file_set_sha256(a)
    resized = [("x.dbn.zst", 11, "a" * 64), ("y.dbn.zst", 20, "b" * 64)]
    assert mod.compute_raw_file_set_sha256(resized) != \
        mod.compute_raw_file_set_sha256(a)


def test_a1_manifest_entries_reads_metadata_only(tmp_path):
    mod = real_run_module()
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"job_id": "J", "files": [
        {"filename": "a.dbn.zst", "hash": "sha256:" + "a" * 64, "size": 7},
        {"filename": "b.dbn.zst", "hash": "sha256:" + "b" * 64, "size": 9},
    ]}), encoding="utf-8")
    entries = mod.a1_manifest_entries(manifest)
    assert entries == [("a.dbn.zst", 7, "a" * 64), ("b.dbn.zst", 9, "b" * 64)]


def test_a1_manifest_entries_fails_closed_on_unknown_schema(tmp_path):
    mod = real_run_module()
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"files": [{"name": "a.dbn.zst"}]}),
                        encoding="utf-8")
    with pytest.raises(ValueError):
        mod.a1_manifest_entries(manifest)


def test_raw_file_set_gate_fails_closed_on_wrong_count(tmp_path):
    mod = real_run_module()
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"files": [
        {"filename": "a.dbn.zst", "hash": "sha256:" + "a" * 64, "size": 7}]}),
        encoding="utf-8")
    gates = {g.name: g for g in mod.build_gates(a1_manifest=manifest)}
    ok, detail = gates["raw_file_set_digest"].check()
    assert not ok
    assert "file count" in detail


def test_seal_check_gate_uses_the_tool_exit_code(tmp_path):
    """Synthetic stand-in for quant-data/tools/seal_check.py — the real tool
    is never invoked from the test suite."""
    mod = real_run_module()
    passing = tmp_path / "seal_pass.py"
    passing.write_text("print('SEAL_CHECK: PASS (ready)')\n", encoding="utf-8")
    failing = tmp_path / "seal_fail.py"
    failing.write_text("import sys;print('SEAL_CHECK: FAIL');sys.exit(1)\n",
                       encoding="utf-8")
    missing = tmp_path / "not_here.py"

    def gate(tool):
        return {g.name: g for g in
                mod.build_gates(seal_check_tool=tool)}["seal_check"]

    assert gate(passing).check()[0] is True
    assert gate(failing).check()[0] is False
    assert gate(missing).check()[0] is False


def test_seal_check_gate_points_at_the_real_read_only_tool():
    mod = real_run_module()
    assert mod.SEAL_CHECK_TOOL.name == "seal_check.py"
    assert "quant-data" in str(mod.SEAL_CHECK_TOOL).replace("\\", "/")


def test_structure_assertion_gate_parses_yaml(tmp_path):
    mod = real_run_module()
    repo = tmp_path / "repo"
    (repo / "gate1").mkdir(parents=True)
    target = repo / mod.STRUCTURE_YAML

    target.write_text("\n".join(f"k{i}: {i}" for i in range(10)) + "\n",
                      encoding="utf-8")
    gates = {g.name: g for g in mod.build_gates(repo=repo)}
    ok, detail = gates["structure_assertions"].check()
    assert ok and "10 top-level keys" in detail

    target.write_text("k1: 1\n", encoding="utf-8")
    ok, _ = {g.name: g for g in
             mod.build_gates(repo=repo)}["structure_assertions"].check()
    assert not ok

    target.write_text("k1: [unclosed\n", encoding="utf-8")
    ok, detail = {g.name: g for g in
                  mod.build_gates(repo=repo)}["structure_assertions"].check()
    assert not ok and "does not parse" in detail


def test_structure_assertion_gate_on_the_real_frozen_params():
    """gate1/platform_params.yaml is a frozen, hash-locked repo file."""
    mod = real_run_module()
    gates = {g.name: g for g in mod.build_gates()}
    ok, detail = gates["structure_assertions"].check()
    assert ok, detail


def test_runs_dir_gate_scans_by_trial_prefix(tmp_path):
    mod = real_run_module()
    runs_root = tmp_path / "runs"
    gates = {g.name: g for g in mod.build_gates(runs_root=runs_root)}
    assert gates["runs_dir_absent_for_trial"].check()[0] is True
    (runs_root / "S0-T001_20260801T000000Z").mkdir(parents=True)
    gates = {g.name: g for g in mod.build_gates(runs_root=runs_root)}
    ok, detail = gates["runs_dir_absent_for_trial"].check()
    assert not ok and "S0-T001" in detail


# ===========================================================================
# scripts/s0_real_run.py — Stage B / Stage D wiring (F-02, F-06, F-14)
# ===========================================================================


def test_stage_b_holds_the_stage_c_wiring_gate_before_exposure():
    """Post Aaron 2026-08-01 SAN.4: real wiring EXISTS (RealChain). The gate
    stays pre-exposure: without a wiring probe it fails inert; with the real
    probe it reflects artifact readiness — and it still sits BEFORE the
    assertion comparison."""
    mod = real_run_module()
    checks = mod.build_structural_checks(REPO / "S0_INPUT_PREFLIGHT.json")
    names = [c.name for c in checks]
    assert "stage_c_wiring_activated" in names
    gate = {c.name: c for c in checks}["stage_c_wiring_activated"]
    ok, detail = gate.check()
    assert ok is False                       # no probe supplied -> inert
    assert "not supplied" in detail
    # with the real probe: M6 keeps the chain FAIL-CLOSED (pre-exposure)
    # while the DR-M6 method rulings pend — readiness returns only when
    # PENDING_METHOD_DECISIONS is empty AND artifacts are on disk.
    wired = mod.build_structural_checks(
        REPO / "S0_INPUT_PREFLIGHT.json",
        wiring_status=mod.RealChain().ready)
    g2 = {c.name: c for c in wired}["stage_c_wiring_activated"]
    ok2, detail2 = g2.check()
    if mod.PENDING_METHOD_DECISIONS:
        assert ok2 is False and "pending method rulings" in detail2
    else:
        assert ok2 is True and "ready" in detail2
    # ordering: the wiring gate precedes the assertion comparison
    assert names.index("stage_c_wiring_activated") < names.index(
        "preflight_assertions_match")


def _check_passes(check) -> bool:
    try:
        ok, _ = check.check()
    except Exception:                                # noqa: BLE001
        return False
    return ok


def test_stage_b_assertion_comparison_is_really_wired(tmp_path):
    """F-06: compare_preflight_assertions must have a real caller — feed a
    synthetic actuals provider and watch the verdict flip."""
    mod = real_run_module()
    expected = {"funnel.L0": 2989, "funnel.L4": 2868}

    def checks(actuals):
        return {c.name: c for c in mod.build_structural_checks(
            tmp_path / "assertions.json",
            expected_loader=lambda p: dict(expected),
            actuals_provider=lambda: actuals)}

    ok, detail = checks(dict(expected))["preflight_assertions_match"].check()
    assert ok, detail
    ok, detail = checks({"funnel.L0": 2989, "funnel.L4": 9999}
                        )["preflight_assertions_match"].check()
    assert not ok and "funnel.L4" in detail
    ok, detail = checks({"funnel.L0": 2989})["preflight_assertions_match"].check()
    assert not ok and "shape_ok=False" in detail


def test_stage_b_translation_check_uses_the_real_locked_assertion_file():
    mod = real_run_module()
    checks = {c.name: c for c in mod.build_structural_checks(
        REPO / "S0_INPUT_PREFLIGHT.json")}
    ok, detail = checks["preflight_assertions_translatable"].check()
    assert ok and "expected assertions translated" in detail


def test_stage_b_actuals_provider_is_inert_today():
    mod = real_run_module()
    with pytest.raises(RunGateError):
        mod.stage_c_actuals_unavailable()


def test_stage_d_na_conservation_is_really_wired():
    """F-06: check_na_conservation must have a real caller, and a violation
    must raise the contract error (so F-27 classifies it correctly)."""
    mod = real_run_module()
    check = mod.build_integrity_checks()[0]

    good = {"na_reason_counts": {"F5": {"roll_transition_day_na": 3}},
            "reported_total_na": {"F5": 3}}
    ok, detail = check(good)
    assert ok, detail

    bad = {"na_reason_counts": {"F5": {"roll_transition_day_na": 3}},
           "reported_total_na": {"F5": 4}}
    with pytest.raises(NAConservationError):
        check(bad)

    unregistered = {"na_reason_counts": {"F5": {"because_i_said_so": 1}},
                    "reported_total_na": {"F5": 1}}
    with pytest.raises(NAConservationError):
        check(unregistered)

    with pytest.raises(NAConservationError):
        check({"sentinel": True})


def test_entrypoint_compute_is_the_real_chain():
    """F-02 aftermath + Aaron SAN.4/6: the placeholder is GONE entirely;
    main() wires RealChain.compute / structural_actuals / render_s0_report."""
    mod = real_run_module()
    import inspect
    source = inspect.getsource(mod.main)
    assert "compute_unreachable" not in source
    assert "RealChain" in source
    assert "chain.compute" in source
    assert "build_structural_checks" in source
    # M6.1.6: the render is wired through the chain's governance-proof
    # entry point, which builds an INDEPENDENT context and then delegates
    # to render_s0_report. Both halves are pinned so neither can be
    # quietly dropped.
    assert "chain.render_report_with_governance_proof" in source
    assert "render_s0_report(" in inspect.getsource(
        mod.RealChain.render_report_with_governance_proof)
    # M6.1.7: the prepare seam is NO LONGER the bare bound method. Stage A's
    # authorization snapshot lives in make_snapshot_control's closure, and
    # `chain.prepare` has no way to reach it, so the seam is bound inside
    # that closure as `prepare_for_run`. Both the new wiring and the ABSENCE
    # of the old one are pinned: re-wiring `chain.prepare` directly would
    # force prepare to re-derive the snapshot itself, which is the second
    # independent read of one fact that this milestone exists to remove.
    assert "prepare_compute=prepare_for_run" in source
    assert "prepare_compute=chain.prepare" not in source
    # M6.1.7: the disk seam is part of the "entrypoint is the real chain"
    # claim now — the renderer's strings cannot answer whether the bytes
    # that landed are the right bytes, so the release verdict is taken from
    # disk by the chain's own post-write verifier.
    assert "post_write_verify=chain.post_write_verify" in source


# =========================================================================
# Synthetic END-TO-END (Aaron 2026-08-01 SAN.7/8): Stage A->B->C->D->E over
# the REAL chain functions (structural_actuals_from / stage_c_result /
# render_s0_report / build_structural_checks / build_integrity_checks) with
# a synthetic universe. No real data; no placeholder anywhere on the path.
# =========================================================================

def _touch_json(path: Path) -> Path:
    path.write_text("{}", encoding="utf-8")
    return path


def _synthetic_dataset():
    import sys as _sys
    tests_dir = str(Path(__file__).resolve().parent)
    if tests_dir not in _sys.path:
        _sys.path.insert(0, tests_dir)
    from test_s0_context import universe_of, weekdays
    from itsf.s0.dataset import build_s0_dataset
    dates = weekdays("2020-01-02", 30)
    bars, uni = universe_of(dates)
    return build_s0_dataset(bars, uni), uni


def test_e2e_synthetic_full_chain_a_through_e(tmp_path):
    """M6.1 O1: the legacy structural-only seal path is REMOVED — the
    production renderer refuses any payload without the formal study
    sections (sealing only via the full contract-validated path)."""
    mod = real_run_module()
    import pytest as _pt
    with _pt.raises(ValueError, match="refusing non-study payload"):
        mod.render_s0_report({"dataset": object(), "frequency": {}})


def test_e2e_structural_mismatch_stops_pre_exposure(tmp_path):
    mod = real_run_module()
    ds, uni = _synthetic_dataset()
    actuals = mod.structural_actuals_from(ds, uni)
    tampered = dict(actuals)
    first = next(iter(tampered))
    tampered[first] = int(tampered[first]) + 1     # one expected value off

    deps, events, _ = make_deps(
        tmp_path, gates=[ok_gate()],
        b_checks=mod.build_structural_checks(
            _touch_json(tmp_path / "assertions.json"),
            expected_loader=lambda p: tampered,
            actuals_provider=lambda: mod.structural_actuals_from(ds, uni),
            wiring_status=lambda: (True, "ready")),
        compute=lambda: mod.stage_c_result(ds))
    out = S0Runner(deps).run()
    assert out.failure_kind == "pre_run_attempt"
    assert out.exposure_consumed is False
    assert "RUN_STARTED" not in [e for e, _ in events]


def test_real_chain_has_no_placeholder_left():
    """Aaron SAN.6: no NotImplementedError / placeholder failure gate may
    remain anywhere on the Stage-C path."""
    src = (REPO / "scripts" / "s0_real_run.py").read_text("utf-8")
    assert "NotImplementedError" not in src
    assert "compute_unreachable" not in src
    mod = real_run_module()
    assert hasattr(mod, "RealChain")
    assert callable(mod.RealChain.compute)


# --- SA-10 blocking-fix gates (N2/N3/N4/N6/F-19) -----------------------------

def test_parent_env_clean_gate_blocks_hostile_vars(monkeypatch):
    mod = real_run_module()
    gates = {g.name: g for g in mod.build_gates()}
    monkeypatch.delenv("PYTHONPATH", raising=False)
    monkeypatch.delenv("PYTEST_ADDOPTS", raising=False)
    ok, _ = gates["parent_env_clean"].check()
    # may still fail if the live session carries other hostile vars; assert
    # the DETECTION direction instead of the ambient state:
    monkeypatch.setenv("GIT_DIR", "/tmp/evil")
    ok2, detail2 = gates["parent_env_clean"].check()
    assert ok2 is False and "GIT_DIR" in detail2


def test_frozen_constants_in_process_gate(monkeypatch):
    mod = real_run_module()
    gates = {g.name: g for g in mod.build_gates()}
    ok, detail = gates["frozen_constants_in_process"].check()
    assert ok is True and "verified" in detail
    # in-process rebind must be caught (SA-6 F-19's exact vector)
    from itsf.s0 import dataset as ds_mod
    monkeypatch.setattr(ds_mod, "THETA_PRIMARY", 0.7)
    ok2, detail2 = gates["frozen_constants_in_process"].check()
    assert ok2 is False and "THETA_PRIMARY" in detail2


def test_ir22_defect_is_classified_by_name():
    from itsf.contracts import InputDataDefectError
    from itsf.s0.runner import classify_exception
    assert classify_exception(
        InputDataDefectError("x")) == "InputDataDefectError"


def test_ir24_divergence_guard_blocks_nonzero(tmp_path):
    """SA-10 N6: a non-empty opening-numerator-zero set must fail Stage B."""
    mod = real_run_module()
    chain = mod.RealChain()

    class _FakeDS:
        na_table = {"diagnostics":
                    {"opening_numerator_zero_ret_open30_undefined": 2}}
    chain._ds, chain._uni = _FakeDS(), object()
    ok, detail = chain.ir24_divergence_guard()
    assert ok is False and "Aaron" in detail
    chain._ds = type("D", (), {"na_table": {"diagnostics": {
        "opening_numerator_zero_ret_open30_undefined": 0}}})()
    ok2, _ = chain.ir24_divergence_guard()
    assert ok2 is True


# =========================================================================
# SA-11 final-readiness fixes: Aaron section-3 snapshot control coverage
# (N-B), sentence-hash binding (N-C), exposure classification of a post-
# RUN_STARTED hook failure (N-D), fail-closed unwired recheck (N-E),
# roster-membership pins for the appended gates (N-F), fail-closed missing
# diagnostics key (N-G).
# =========================================================================

from dataclasses import replace as _dc_replace


def test_unwired_pre_exposure_recheck_is_fail_closed(tmp_path):
    """N-E: no recheck wired -> the atomic transition refuses, PRE-exposure."""
    deps, events, _ = make_deps(tmp_path, gates=[ok_gate()])
    deps = _dc_replace(deps, pre_exposure_recheck=None)
    out = S0Runner(deps).run()
    assert out.failure_kind == "pre_run_attempt"
    assert out.exposure_consumed is False
    assert "RUN_STARTED" not in [e for e, _ in events]


def test_failing_pre_exposure_recheck_blocks_before_exposure(tmp_path):
    deps, events, _ = make_deps(tmp_path, gates=[ok_gate()])
    deps = _dc_replace(deps, pre_exposure_recheck=lambda: (
        False, "registry changed"))
    out = S0Runner(deps).run()
    assert out.failure_kind == "pre_run_attempt"
    assert out.exposure_consumed is False
    assert not Path(deps.config.runs_dir).exists()


def test_post_run_started_hook_failure_is_a_RUN_failure(tmp_path):
    """N-D: RUN_STARTED appended -> exposure consumed; a hook crash must be
    classified run_failure (trial burned, outputs retained), never pre-run."""
    def boom(rdir):
        raise OSError("disk hiccup")
    deps, events, _ = make_deps(tmp_path, gates=[ok_gate()])
    deps = _dc_replace(deps, post_run_started_hook=boom)
    out = S0Runner(deps).run()
    assert out.failure_kind == "run_failure"
    assert out.exposure_consumed is True
    assert [e for e, _ in events] == ["RUN_STARTED", "FAILED"]
    assert (out.runs_dir / "RUN_FAILURE_REPORT.md").exists()


def test_post_run_started_hook_success_runs_and_seals(tmp_path):
    seen: list[Path] = []
    deps, events, _ = make_deps(tmp_path, gates=[ok_gate()])
    deps = _dc_replace(deps, post_run_started_hook=seen.append)
    out = S0Runner(deps).run()
    assert out.ok is True
    assert seen == [Path(deps.config.runs_dir)]


def _authorized_registry(tmp_path, commit: str) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    reg = tmp_path / "TRIAL_REGISTRY.md"
    sentence = f"启动第一次真实S0，授权trial_id: S0-T001，使用commit: {commit}"
    reg.write_text(
        "| # | utc | event | commit | actor | note |\n"
        "|---|---|---|---|---|---|\n"
        f"| 1 | 2026-08-02 | PACKET_APPROVED | x | Aaron | note |\n"
        f"| 2 | 2026-08-02 | RUN_AUTHORIZED | {commit} | Aaron | "
        f"[S0-T001] {sentence} |\n", encoding="utf-8")
    return reg


def test_authorization_snapshot_binds_the_exact_sentence(tmp_path, monkeypatch):
    """N-C: two different authorized commits must yield two DIFFERENT
    exact_authorization_text_sha256 values (it used to hash the parser's
    'ok' reason — constant across commits)."""
    mod = real_run_module()
    hashes = []
    for commit in ("a" * 40, "b" * 40):
        reg = _authorized_registry(tmp_path / commit[:2], commit)
        monkeypatch.setattr(mod, "REGISTRY", reg)
        chain = mod.RealChain()
        snap = chain.authorization_snapshot()
        assert snap["authorized_commit"] == commit
        assert snap["exact_authorization_text_sha256"]
        hashes.append(snap["exact_authorization_text_sha256"])
    assert hashes[0] != hashes[1]
    import hashlib as _h
    expected = _h.sha256(
        ("启动第一次真实S0，授权trial_id: S0-T001，使用commit: "
         + "b" * 40).encode("utf-8")).hexdigest()
    assert hashes[1] == expected


def test_snapshot_control_production_closures(tmp_path, monkeypatch):
    """SA-12 N-B: execute the PRODUCTION §三 closures from
    make_snapshot_control — the same objects main() wires into RunnerDeps.

    (i) the Stage-A gate writes AUTHORIZATION_SNAPSHOT.json AND populates
    the shared state; (ii) the recheck fails closed with no snapshot,
    passes on an unchanged registry, and FAILS after an appended event
    (this assertion goes red if the comparison is mutated fail-open);
    (iii) the post hook writes REGISTRY_AFTER_RUN_STARTED.json carrying
    the post-append registry hash and the Stage-A snapshot.

    M6.1.7 adds a FOURTH production closure to the same factory,
    `prepare_for_run`, and (iv)/(v) below cover it: it is fail-closed
    pre-exposure with no Stage-A snapshot, and it hands `chain.prepare`
    THE SAME snapshot OBJECT the recheck holds as its reference side.
    That identity is the point — `chain.prepare` deliberately does not
    call `authorization_snapshot()` itself, because a second independent
    read of one fact is what produced the defect this milestone closes
    (Stage C re-read the registry AFTER its own RUN_STARTED row had been
    appended, so the sealed registry_sequence_snapshot was the
    pre-exposure count plus one — invisible, because the seal-time
    expectation re-read the same moved source and drifted with it)."""
    import hashlib as _h
    mod = real_run_module()
    commit = "c" * 40
    reg = _authorized_registry(tmp_path, commit)
    monkeypatch.setattr(mod, "REGISTRY", reg)
    chain = mod.RealChain()
    assert chain.authorization_snapshot() == chain.authorization_snapshot()
    attempts = tmp_path / "attempts"
    # M6.1.7: FOUR closures — the prepare seam is built here too, because
    # it is the only way it can reach this closure's Stage-A snapshot.
    gate, recheck, hook, prepare_for_run = mod.make_snapshot_control(
        chain, attempts)

    ok, why = recheck()                       # before the gate: fail closed
    assert ok is False and "no Stage-A" in why

    # (iv) M6.1.7 — the prepare seam is fail-closed the same way, and this
    # refusal happens PRE-exposure (the seam runs before _atomic_run_start,
    # so a RuntimeError here is a PRE_RUN_ATTEMPT_FAILURE that burns
    # nothing; the runner-level proof of that routing is
    # test_prepare_failure_is_pre_exposure_and_compute_never_runs).
    with pytest.raises(RuntimeError,
                       match="no Stage-A authorization snapshot"):
        prepare_for_run()

    # ... and a malformed snapshot is attributable AS a snapshot defect:
    # prepare validates the snapshot structurally BEFORE it resolves any
    # config, so this never surfaces as "stage-C config unavailable".
    with pytest.raises(RuntimeError, match="missing required fields"):
        chain.prepare({"trial_id": "S0-T001"})

    # From here on, record every snapshot the chain produces, so the
    # identity claims below are about OBJECTS and not about equal values
    # (every snapshot of an unchanged registry compares equal — identity is
    # the only thing that distinguishes "the Stage-A object" from "a fresh
    # re-read that happens to agree").
    produced: list = []
    real_snapshot = chain.authorization_snapshot

    def recording_snapshot():
        snap_obj = real_snapshot()
        produced.append(snap_obj)
        return snap_obj

    monkeypatch.setattr(chain, "authorization_snapshot", recording_snapshot)

    ok, _ = gate()                            # (i) gate side-effects
    assert ok is True
    snap = json.loads(
        (attempts / "AUTHORIZATION_SNAPSHOT.json").read_text("utf-8"))
    assert snap["authorized_commit"] == commit
    assert len(produced) == 1                 # the gate took exactly one
    stage_a_snapshot = produced[0]

    ok, _ = recheck()                         # (ii) unchanged -> pass
    assert ok is True
    # the recheck compares the STORED Stage-A object against a FRESH read:
    # a second snapshot object now exists, equal but not identical.
    assert len(produced) == 2
    assert produced[1] == stage_a_snapshot
    assert produced[1] is not stage_a_snapshot

    # (v) M6.1.7 — prepare_for_run hands chain.prepare THAT SAME OBJECT,
    # and takes no snapshot of its own.
    handed: list = []

    def recording_prepare(snapshot):
        handed.append(snapshot)
        return "PREPARED"

    monkeypatch.setattr(chain, "prepare", recording_prepare)
    assert prepare_for_run() == "PREPARED"
    assert handed == [stage_a_snapshot]
    assert handed[0] is stage_a_snapshot      # identity, not equality
    assert len(produced) == 2                 # prepare re-read NOTHING

    rdir = tmp_path / "runs"                  # (iii) hook side-effects
    rdir.mkdir()
    hook(rdir)
    after = json.loads(
        (rdir / "REGISTRY_AFTER_RUN_STARTED.json").read_text("utf-8"))
    assert (after["registry_sha256_after_run_started"]
            == _h.sha256(reg.read_bytes()).hexdigest())
    assert after["snapshot_before"]["authorized_commit"] == commit

    reg.write_text(reg.read_text("utf-8")     # (ii) appended event -> FAIL
                   + "| 3 | 2026-08-02 | X | y | z | inserted |\n",
                   encoding="utf-8")
    ok, why = recheck()
    assert ok is False and "CHANGED" in why


def test_main_wires_snapshot_control_and_appended_gates():
    """N-F + N-E production pins: main() must wire both section-3 hooks and
    append the two extra gates to the rosters."""
    import inspect
    mod = real_run_module()
    src = inspect.getsource(mod.main)
    assert "make_snapshot_control" in src        # SA-12 N-B: factory wired
    assert "pre_exposure_recheck=pre_exposure_recheck" in src
    assert "post_run_started_hook=post_run_started_hook" in src
    assert "authorization_snapshot_recorded" in src
    assert "ir24_f8_divergence_empty" in src


def test_ir24_gate_fails_closed_when_diagnostics_key_missing():
    """N-G: an absent diagnostics counter must FAIL the gate, not pass it.
    Covers BOTH branches (SA-12): the diagnostics dict entirely absent AND
    the dict present with the counter key absent — the second goes red if
    `or key not in diag` is deleted."""
    mod = real_run_module()
    for na_table in ({}, {"diagnostics": {}}):
        chain = mod.RealChain()
        chain._ds = type("D", (), {"na_table": na_table})()
        chain._uni = object()
        ok, detail = chain.ir24_divergence_guard()
        assert ok is False and "fail closed" in detail, na_table


def test_actuals_prev_close_missing_counted_by_value_none():
    """IR-26 rule A: the prev-close map holds a key for EVERY eligible day
    (missing anchors stored as None + cause) — a None VALUE must count as
    missing and produce the conserved aggregate reason key. This test goes
    red if the actuals revert to key-membership detection."""
    mod = real_run_module()

    def ns(**kw):
        return type("NS", (), kw)()

    days = ("2020-01-02", "2020-01-03")
    summaries = {d: ns(o0930=1.0, c0959=1.0, o1000=1.0, c1544=1.0)
                 for d in days}
    uni = ns(summaries=summaries,
             prev_rth_close={days[0]: None, days[1]: 100.0},
             prev_rth_close_cause={days[0]: "no_prior_rth_session_in_sample",
                                   days[1]: ""})
    per = {f: {"not_na": 2, "na": 0, "reasons": {}}
           for f in mod.FEATURE_FIELD_TO_F}
    ds = ns(records=[ns(trade_date=days[0]), ns(trade_date=days[1])],
            funnel_counts={k: 2 for k in (
                "L0_scheduled_trading_days", "L1_observed_rth_days",
                "L2_regular_full_session_candidates",
                "L3_structurally_eligible_days",
                "L4_final_feature_construction_dates")},
            f10_counts={"none": 2},
            na_table={"per_field": {"features": per}, "population": 2},
            label_anchor_availability={
                k: {"available_days": 2, "unavailable_days": 0}
                for k in mod.LABEL_KEY_TO_NAME})
    out = mod.structural_actuals_from(ds, uni)
    assert out["anchor.prev_rth_close.missing"] == 1
    assert out["anchor.prev_rth_close.available"] == 1
    assert out["na_reason.anchor.prev_rth_close."
               "prev_rth_close_anchor_missing"] == 1


# =========================================================================
# M6.1.6 S1 — the PRE-EXPOSURE PREPARE SEAM
#
# Lifecycle under test:
#     Stage B all pass -> prepare_compute() -> final registry recheck
#     -> _atomic_run_start / RUN_STARTED (exposure) -> compute(prepared)
#
# The point of the seam: a refusal that happens during prepare is a
# PRE_RUN_ATTEMPT_FAILURE and costs nothing, whereas the identical refusal
# raised inside `compute` routes to _fail_run and permanently burns the
# trial id. Every test here is synthetic and goes through the real runner.
# =========================================================================


def _counting_compute(counter: dict):
    def compute(prepared):
        counter["compute"] = counter.get("compute", 0) + 1
        counter["seen"] = prepared
        return {"sentinel": True}
    return compute


def test_prepare_failure_is_pre_exposure_and_compute_never_runs(tmp_path):
    """Requirement 5: prepare refuses -> PRE-run failure. No RUN_STARTED,
    no runs directory, exposure intact, Stage C never entered."""
    counter: dict = {}

    def refusing_prepare():
        raise RunGateError("synthetic prepare refusal (unresolved config)")

    deps, events, _ = make_deps(tmp_path, gates=[ok_gate()],
                                prepare=refusing_prepare,
                                compute=_counting_compute(counter))
    out = S0Runner(deps).run()

    assert out.failure_kind == "pre_run_attempt"
    assert out.exposure_consumed is False
    assert "RUN_STARTED" not in [e for e, _ in events]
    assert [e for e, _ in events] == ["PRE_RUN_ATTEMPT_FAILURE"]
    assert not Path(deps.config.runs_dir).exists()
    assert counter.get("compute", 0) == 0
    assert out.failed_gate == "prepare_compute"
    assert out.terminal_stage == RunStage.B_LOAD_VALIDATE
    # the same refusal INSIDE compute would have burned the trial:
    assert (out.attempts_dir / "PRE_RUN_ATTEMPT_FAILURE.md").exists()


def test_prepare_returning_nothing_is_also_a_pre_exposure_refusal(tmp_path):
    """A prepare that returns None yields no object at all, and that is
    fail-closed, not a silent pass: Stage C must be handed an object or not
    run. (M6.1.7 S1: `None` specifically — a FALSY object is still an
    object and is forwarded unchanged; see the falsy pass-through test.)"""
    counter: dict = {}
    deps, events, _ = make_deps(tmp_path, gates=[ok_gate()],
                                prepare=lambda: None,
                                compute=_counting_compute(counter))
    out = S0Runner(deps).run()
    assert out.failure_kind == "pre_run_attempt"
    assert out.exposure_consumed is False
    assert "RUN_STARTED" not in [e for e, _ in events]
    assert not Path(deps.config.runs_dir).exists()
    assert counter.get("compute", 0) == 0


def test_compute_receives_the_identical_object_prepare_returned(tmp_path):
    """Requirement 2/4: identity, not equality — Stage C gets THE object."""
    token = {"prepared": ["run", "scoped"]}
    counter: dict = {}
    deps, _, _ = make_deps(tmp_path, gates=[ok_gate()],
                           prepare=lambda: token,
                           compute=_counting_compute(counter))
    out = S0Runner(deps).run()
    assert out.ok is True
    assert counter["seen"] is token


def test_two_runner_instances_do_not_share_a_prepared_object(tmp_path):
    """Requirement 7: the prepared object is run-scoped. No cross-run
    global, no class attribute, no module cache."""
    made: list[object] = []

    def prepare():
        obj = {"prepared": len(made)}      # a FRESH object every call
        made.append(obj)
        return obj

    seen: list[object] = []

    def compute(prepared):
        seen.append(prepared)
        return {"sentinel": True}

    deps_a, _, _ = make_deps(tmp_path / "a", gates=[ok_gate()],
                             prepare=prepare, compute=compute)
    deps_b, _, _ = make_deps(tmp_path / "b", gates=[ok_gate()],
                             prepare=prepare, compute=compute)
    assert S0Runner(deps_a).run().ok is True
    assert S0Runner(deps_b).run().ok is True

    assert len(made) == 2 and len(seen) == 2
    assert seen[0] is made[0] and seen[1] is made[1]
    assert seen[0] is not seen[1]


def test_mutating_the_source_after_prepare_does_not_change_the_prepared(
        tmp_path):
    """The prepared object is a run-scoped SNAPSHOT: mutating the original
    mutable input after prepare has returned must not reach Stage C."""
    import copy
    source = {"rows": [1, 2, 3]}

    def prepare():
        return copy.deepcopy(source)

    counter: dict = {}

    def recheck_that_mutates_the_source():
        # runs strictly AFTER prepare and strictly BEFORE the transition
        source["rows"].append(999)
        return True, "source mutated after prepare"

    deps, _, _ = make_deps(tmp_path, gates=[ok_gate()], prepare=prepare,
                           compute=_counting_compute(counter))
    deps = _dc_replace(deps,
                       pre_exposure_recheck=recheck_that_mutates_the_source)
    out = S0Runner(deps).run()

    assert out.ok is True
    assert source["rows"] == [1, 2, 3, 999]          # the mutation happened
    assert counter["seen"] == {"rows": [1, 2, 3]}    # ... and did not land


def test_stage_c_never_calls_back_into_prepare(tmp_path):
    """Requirement 1/4: prepare is called exactly once per run, from the
    pre-exposure seam only — Stage C consumes, it does not re-prepare."""
    counter = {"prepare": 0}

    def prepare():
        counter["prepare"] += 1
        return {"prepared": counter["prepare"]}

    def compute(prepared):
        counter["compute"] = counter.get("compute", 0) + 1
        return {"sentinel": True}

    deps, _, _ = make_deps(tmp_path, gates=[ok_gate()],
                           b_checks=[GateCheck("b1", lambda: (True, "ok"))],
                           integrity=[lambda r: (True, "ok")],
                           prepare=prepare, compute=compute)
    out = S0Runner(deps).run()
    assert out.ok is True
    assert counter["prepare"] == 1
    assert counter["compute"] == 1


def test_unwired_prepare_seam_is_fail_closed(tmp_path):
    """Requirement 6: no prepare seam wired -> pre-exposure refusal, exactly
    like the unwired pre_exposure_recheck rule it is modelled on. The source
    must also SAY that it mirrors that precedent."""
    counter: dict = {}
    deps, events, _ = make_deps(tmp_path, gates=[ok_gate()],
                                compute=_counting_compute(counter))
    deps = _dc_replace(deps, prepare_compute=None)
    out = S0Runner(deps).run()

    assert out.failure_kind == "pre_run_attempt"
    assert out.exposure_consumed is False
    assert "RUN_STARTED" not in [e for e, _ in events]
    assert not Path(deps.config.runs_dir).exists()
    assert counter.get("compute", 0) == 0
    assert out.failed_gate == "prepare_compute"
    # the precedent is stated in the runner source, not only here
    source = inspect.getsource(S0Runner.run)
    assert "fail closed" in source
    assert "pre-exposure registry recheck" in source


def test_prepare_runs_after_stage_b_before_recheck_and_before_exposure(
        tmp_path):
    """Requirement 1/3 — the whole point of the milestone, pinned as one
    observed sequence through the real runner."""
    order: list[str] = []

    def gate_a():
        order.append("stage_a")
        return True, "ok"

    def check_b():
        order.append("stage_b")
        return True, "ok"

    def prepare():
        order.append("prepare")
        return {"prepared": True}

    def recheck():
        order.append("pre_exposure_recheck")
        return True, "synthetic recheck"

    def compute(prepared):
        order.append("compute")
        return {"sentinel": True}

    def append_event(event, note):
        order.append(f"event:{event}")

    deps, _, _ = make_deps(tmp_path, gates=[GateCheck("g1", gate_a)],
                           b_checks=[GateCheck("b1", check_b)],
                           prepare=prepare, compute=compute,
                           append_event=append_event)
    deps = _dc_replace(deps, pre_exposure_recheck=recheck)
    out = S0Runner(deps).run()

    assert out.ok is True
    assert order == ["stage_a", "stage_b", "prepare", "pre_exposure_recheck",
                     "event:RUN_STARTED", "compute", "event:COMPLETED"]


def test_prepare_failure_never_reaches_the_registry_recheck(tmp_path):
    """Ordering, negatively: a refusing prepare must stop the lifecycle
    before the final registry recheck ever runs."""
    seen: list[str] = []

    def recheck():
        seen.append("recheck")
        return True, "synthetic recheck"

    def refusing_prepare():
        raise RunGateError("synthetic prepare refusal")

    deps, _, _ = make_deps(tmp_path, gates=[ok_gate()],
                           prepare=refusing_prepare)
    deps = _dc_replace(deps, pre_exposure_recheck=recheck)
    out = S0Runner(deps).run()
    assert out.failure_kind == "pre_run_attempt"
    assert seen == []


# =========================================================================
# M6.1.7 S1 — (c) the runner never reads the prepared object's TRUTH VALUE
#
# The M6.1.6 `if not prepared` gate is reverted to `if prepared is None`.
# Two things are pinned below: a falsy prepared object reaches Stage C
# UNCHANGED (the runner is a generic lifecycle component — whether an
# object is *meaningful* is the application's business), and an object
# whose __bool__ raises passes through the runner untouched, proving no
# application-controlled truth-value code runs inside the gate.
# =========================================================================


@pytest.mark.parametrize("falsy", [0, 0.0, "", (), {}, [], frozenset(),
                                   set()],
                         ids=["int0", "float0", "emptystr", "emptytuple",
                              "emptydict", "emptylist", "frozenset",
                              "set"])
def test_falsy_prepared_object_passes_through_to_compute_unchanged(tmp_path,
                                                                   falsy):
    """M6.1.7 S1 requirement 6: an empty tuple / empty mapping / 0 is a
    legitimate prepared object. It must reach Stage C — by IDENTITY, not by
    equality — and the run must seal normally. An application that wants
    emptiness to be a refusal raises inside its own prepare seam."""
    seen: list = []

    def compute(prepared):
        seen.append(prepared)
        return {"sentinel": True}

    deps, events, _ = make_deps(tmp_path, gates=[ok_gate()],
                                prepare=lambda: falsy, compute=compute)
    out = S0Runner(deps).run()

    assert out.ok is True, (out.failure_kind, out.failed_gate)
    assert out.exposure_consumed is True
    assert [e for e, _ in events] == ["RUN_STARTED", "COMPLETED"]
    assert len(seen) == 1
    assert seen[0] is falsy                          # identity, unchanged


class _TruthValueBomb:
    """Any attempt to evaluate this object's truth value detonates.

    `not x` consults __bool__ and falls back to __len__, so BOTH are armed.
    A runner that asks "is the prepared object meaningful?" cannot survive
    contact with this object; a runner that only asks "is it None?" never
    notices it is unusual."""

    def __bool__(self) -> bool:
        raise AssertionError(
            "the runner evaluated the prepared object's __bool__")

    def __len__(self) -> int:
        raise AssertionError(
            "the runner evaluated the prepared object's __len__")


def test_prepared_object_truth_value_is_never_read_by_the_runner(tmp_path):
    """M6.1.7 S1 requirement 7. The failure mode this pins is exact: under
    `if not prepared`, this object's __bool__ runs INSIDE the runner's
    pre-exposure gate and the AssertionError escapes `run()` entirely (it is
    raised outside every try block), so the lifecycle dies with a bare
    traceback and no governance record at all."""
    bomb = _TruthValueBomb()
    seen: dict = {}

    def compute(prepared):
        seen["compute"] = prepared
        return {"sentinel": True}

    def renderer(result, prepared):
        seen["render"] = prepared
        return {"S0_REPORT.md": MULTILINE_ARTIFACT}

    def verify(rdir, written, prepared):
        seen["verify"] = prepared
        return True, "ok"

    deps, events, _ = make_deps(tmp_path, gates=[ok_gate()],
                                prepare=lambda: bomb, compute=compute,
                                renderer=renderer, post_write_verify=verify)
    out = S0Runner(deps).run()                       # must not raise

    assert out.ok is True, (out.failure_kind, out.failed_gate)
    assert [e for e, _ in events] == ["RUN_STARTED", "COMPLETED"]
    # M6.1.7 S1 follow-up: the bomb survives ALL THREE forwarding sites —
    # Stage C, the Stage-E renderer and the post-write verifier — so no
    # stage of the lifecycle evaluates the prepared object's truth value.
    assert set(seen) == {"compute", "render", "verify"}
    for where, obj in seen.items():
        assert obj is bomb, where                    # forwarded, unexamined
    # and the runner's own source no longer contains the truth-value gate
    source = inspect.getsource(S0Runner.run)
    assert "if prepared is None:" in source
    assert "if not prepared:" not in source


# =========================================================================
# M6.1.7 S1 — (a) BYTE FIDELITY: on-disk bytes == renderer bytes == the
# bytes in the hash chain.
#
# Measured defect at HEAD 185e47f7: Stage E wrote artifacts with
# `write_text(content, encoding="utf-8")`, which on Windows translates
# '\n' -> '\r\n', so the string the renderer produced and the bytes on
# disk were different values. The runner hashed the DISK bytes into the
# manifest while the renderer's own report recorded the IN-MEMORY digest —
# two digests for one artifact inside one sealed output. Every fixture
# below therefore contains a MULTI-LINE artifact: a single-line artifact
# cannot reproduce the defect (it has no '\n' to translate).
# =========================================================================


MULTILINE_ARTIFACT = (
    "# S0 REPORT\n\nline one\nline two\n\n- bullet\n- bullet\n")
JSON_ARTIFACT = '{\n  "sealed_files": {\n    "a": 1\n  }\n}\n'
SINGLE_LINE_ARTIFACT = '{"admitted": []}'


def _byte_fixture_renderer(result, prepared):
    """Three artifacts: two multi-line (the defect's shape) and one
    single-line (the one artifact that agreed even before the fix).

    Two-arg, per the M6.1.7 S1 follow-up render contract."""
    return {"S0_REPORT.md": MULTILINE_ARTIFACT,
            "S0_REPORT.json": JSON_ARTIFACT,
            "HANDOFF_ADMISSION.json": SINGLE_LINE_ARTIFACT}


def _fixture_artifacts():
    """The fixture's {name: content} map, for assertions."""
    return _byte_fixture_renderer(None, None)


def test_on_disk_bytes_are_exactly_the_bytes_the_renderer_produced(tmp_path):
    """Byte-for-byte, for EVERY written artifact, including the multi-line
    ones. This assertion is red at HEAD 185e47f7 on Windows."""
    deps, _, _ = make_deps(tmp_path, gates=[ok_gate()],
                           renderer=_byte_fixture_renderer)
    out = S0Runner(deps).run()
    assert out.ok is True, (out.failure_kind, out.failed_gate)

    for name, content in _fixture_artifacts().items():
        on_disk = (out.runs_dir / name).read_bytes()
        assert on_disk == content.encode("utf-8"), name
        assert b"\r\n" not in on_disk, name          # no text-mode translation

    # the multi-line artifact really does carry newlines (guard against a
    # fixture that would make this test vacuous)
    assert MULTILINE_ARTIFACT.count("\n") >= 5
    assert b"\n" in (out.runs_dir / "S0_REPORT.md").read_bytes()


def test_hash_chain_records_the_digest_of_those_exact_bytes(tmp_path):
    """The chain's file_sha256 must equal sha256(renderer bytes) AND
    sha256(on-disk bytes) — one number, not two."""
    deps, _, _ = make_deps(tmp_path, gates=[ok_gate()],
                           renderer=_byte_fixture_renderer)
    out = S0Runner(deps).run()
    assert out.ok is True

    records = [json.loads(ln) for ln in
               (out.runs_dir / "manifest.jsonl").read_text("utf-8").splitlines()
               if ln.strip()]
    recorded = {r["relative_path"]: r["file_sha256"]
                for r in records if r["record_type"] == "file"}
    assert set(recorded) == set(_fixture_artifacts())

    for name, content in _fixture_artifacts().items():
        renderer_digest = runinfra.hashlib.sha256(
            content.encode("utf-8")).hexdigest()
        disk_digest = runinfra.hashlib.sha256(
            (out.runs_dir / name).read_bytes()).hexdigest()
        assert recorded[name] == renderer_digest, name
        assert recorded[name] == disk_digest, name


def test_stage_e_logs_the_same_digest_it_chained(tmp_path):
    """The guarded `file=<id> sha256=<64hex>` log line is the third place a
    digest is published; it must agree with the other two.

    M6.1.8 S1 (H-1): the IDENTIFIER in that line is now the artifact's
    opaque ordinal in the write order, not its name. The DIGEST — which is
    what this test is about — is unchanged and is still the same number the
    chain recorded."""
    sink: list[str] = []
    deps, _, _ = make_deps(tmp_path, gates=[ok_gate()],
                           renderer=lambda result, prepared: {
                               "S0_REPORT.md": MULTILINE_ARTIFACT},
                           log=guarded_logger(sink))
    out = S0Runner(deps).run()
    assert out.ok is True
    digest = runinfra.hashlib.sha256(
        MULTILINE_ARTIFACT.encode("utf-8")).hexdigest()
    assert f"file={artifact_log_id(1)} sha256={digest}" in sink
    # and the manifest still carries the REAL name against that digest
    records = [json.loads(ln) for ln in
               (out.runs_dir / "manifest.jsonl").read_text("utf-8").splitlines()
               if ln.strip()]
    assert [(r["relative_path"], r["file_sha256"]) for r in records
            if r["record_type"] == "file"] == [("S0_REPORT.md", digest)]


# =========================================================================
# M6.1.7 S1 — (b) the REQUIRED post-write verification seam
# =========================================================================


def test_unwired_post_write_verifier_refuses_before_exposure(tmp_path):
    """Requirement 4: the WIRING check is pre-exposure, exactly like the
    `prepare_compute` and `pre_exposure_recheck` precedents — no
    RUN_STARTED, no runs directory, exposure NOT consumed, Stage C never
    entered."""
    counter: dict = {}
    deps, events, _ = make_deps(tmp_path, gates=[ok_gate()],
                                compute=_counting_compute(counter))
    deps = _dc_replace(deps, post_write_verify=None)
    out = S0Runner(deps).run()

    assert out.failure_kind == "pre_run_attempt"
    assert out.exposure_consumed is False
    assert out.failed_gate == "post_write_verify"
    assert out.terminal_stage == RunStage.B_LOAD_VALIDATE
    assert [e for e, _ in events] == ["PRE_RUN_ATTEMPT_FAILURE"]
    assert "RUN_STARTED" not in [e for e, _ in events]
    assert not Path(deps.config.runs_dir).exists()
    assert counter.get("compute", 0) == 0
    assert (out.attempts_dir / "PRE_RUN_ATTEMPT_FAILURE.md").exists()
    # the precedent and the asymmetry are stated in the runner source
    source = inspect.getsource(S0Runner.run)
    assert "fail closed" in source
    assert "ASYMMETRY" in source


def test_post_write_verifier_refusal_is_a_stage_e_run_failure(tmp_path):
    """The other half of the asymmetry: the verification itself happens
    AFTER the bytes exist, i.e. after exposure. A refusal burns the trial
    and must preserve every diagnostic artifact."""
    deps, events, _ = make_deps(
        tmp_path, gates=[ok_gate()], renderer=_byte_fixture_renderer,
        post_write_verify=lambda rdir, written, prepared: (
            False, "digest disagreement in S0_REPORT.md"))
    out = S0Runner(deps).run()

    assert out.ok is False
    assert out.failure_kind == "run_failure"
    assert out.exposure_consumed is True
    assert out.terminal_stage == RunStage.E_REPORT
    assert out.failed_gate == "post_write_verify"
    assert [e for e, _ in events] == ["RUN_STARTED", "FAILED"]

    # ARTIFACTS PRESERVED: nothing written before the refusal is removed,
    # and the failure evidence is written alongside it.
    for name, content in _fixture_artifacts().items():
        assert (out.runs_dir / name).read_bytes() == content.encode("utf-8")
    assert (out.runs_dir / "RUN_FAILURE_REPORT.md").exists()
    assert (out.runs_dir / "RUN_FAILURE_REPORT.json").exists()
    assert (out.runs_dir / f"INCIDENT_{out.incident_id}.md").exists()
    # F-05 still holds on this path: the raw detail is sealed, not published
    note = dict(events)["FAILED"]
    assert "digest disagreement" not in note
    assert out.incident_id in note
    assert "digest disagreement" in (
        out.runs_dir / f"INCIDENT_{out.incident_id}.md").read_text("utf-8")


def test_post_write_verifier_that_raises_is_also_a_stage_e_run_failure(
        tmp_path):
    def exploding(rdir, written, prepared):
        raise RunGateError("verifier blew up")

    deps, events, _ = make_deps(tmp_path, gates=[ok_gate()],
                                post_write_verify=exploding)
    out = S0Runner(deps).run()
    assert out.failure_kind == "run_failure"
    assert out.terminal_stage == RunStage.E_REPORT
    assert out.failed_gate == "post_write_verify"
    payload = json.loads((out.runs_dir / "RUN_FAILURE_REPORT.json")
                         .read_text("utf-8"))
    assert payload["exception_type"] == "RunGateError"   # F-27 isinstance


def test_post_write_verifier_receives_the_prepared_object(tmp_path):
    """Requirement 3: the prepared object is handed over EXPLICITLY as a
    parameter — identity, not equality, and no module-level temporary."""
    token = {"prepared": ["run", "scoped"]}
    seen: dict = {}

    def verify(rdir, written, prepared):
        seen["runs_dir"] = rdir
        seen["written"] = written
        seen["prepared"] = prepared
        return True, "ok"

    deps, _, _ = make_deps(tmp_path, gates=[ok_gate()],
                           prepare=lambda: token,
                           renderer=_byte_fixture_renderer,
                           post_write_verify=verify)
    out = S0Runner(deps).run()

    assert out.ok is True
    assert seen["prepared"] is token
    assert seen["runs_dir"] == out.runs_dir
    assert dict(seen["written"]) == {
        n: c.encode("utf-8") for n, c in _fixture_artifacts().items()}


def test_post_write_verifier_receives_a_falsy_prepared_object_too(tmp_path):
    """The two M6.1.7 halves meet: a falsy prepared object is forwarded to
    the verifier unchanged, so the verifier must not be handed a
    'meaningfulness' verdict the runner made on its behalf."""
    seen: dict = {}
    empty = ()

    def verify(rdir, written, prepared):
        seen["prepared"] = prepared
        return True, "ok"

    deps, _, _ = make_deps(tmp_path, gates=[ok_gate()], prepare=lambda: empty,
                           post_write_verify=verify)
    assert S0Runner(deps).run().ok is True
    assert seen["prepared"] is empty


def test_verifier_runs_after_every_write_and_before_the_chain(tmp_path):
    """Placement, pinned by observation: when the verifier runs, EVERY
    renderer artifact is already closed on disk and NOTHING has entered the
    manifest yet — so the append-only chain can never record a digest for
    an artifact whose bytes were not first proven. Stage E has not
    completed either."""
    observed: dict = {}

    def verify(rdir, written, prepared):
        observed["names_on_disk"] = sorted(
            p.name for p in rdir.iterdir() if p.is_file())
        observed["manifest_exists"] = (rdir / "manifest.jsonl").exists()
        observed["written_names"] = sorted(n for n, _ in written)
        return True, "ok"

    deps, _, _ = make_deps(tmp_path, gates=[ok_gate()],
                           renderer=_byte_fixture_renderer,
                           post_write_verify=verify)
    out = S0Runner(deps).run()

    assert out.ok is True
    expected = sorted(_fixture_artifacts())
    assert observed["names_on_disk"] == expected     # all files written
    assert observed["written_names"] == expected     # all handed over
    assert observed["manifest_exists"] is False      # chain not yet touched
    # ... and afterwards the chain does exist and Stage E completed
    assert (out.runs_dir / "manifest.jsonl").exists()
    assert "E_REPORT" in out.stages_completed


def test_a_refusing_verifier_leaves_no_manifest_record_behind(tmp_path):
    """The consequence of the placement above, stated as a fact about the
    failed run: unproven bytes never entered the append-only chain."""
    deps, _, _ = make_deps(
        tmp_path, gates=[ok_gate()], renderer=_byte_fixture_renderer,
        post_write_verify=lambda rdir, written, prepared: (False, "nope"))
    out = S0Runner(deps).run()
    assert out.ok is False
    assert not (out.runs_dir / "manifest.jsonl").exists()
    assert "E_REPORT" not in out.stages_completed


def test_default_synthetic_verifier_actually_catches_a_byte_difference(
        tmp_path):
    """The harness verifier is not a rubber stamp: hand it a doctored
    `written` pair and it refuses. Without this, every make_deps-built run
    in this suite would 'verify' vacuously."""
    ok, detail = default_post_write_verify(tmp_path, (), None)
    assert ok is True and "0 artifact" in detail

    (tmp_path / "S0_REPORT.md").write_bytes(
        MULTILINE_ARTIFACT.encode("utf-8"))
    ok, detail = default_post_write_verify(
        tmp_path, (("S0_REPORT.md", MULTILINE_ARTIFACT.encode("utf-8")),),
        None)
    assert ok is True

    crlf = MULTILINE_ARTIFACT.replace("\n", "\r\n").encode("utf-8")
    ok, detail = default_post_write_verify(
        tmp_path, (("S0_REPORT.md", crlf),), None)
    assert ok is False
    assert "S0_REPORT.md" in detail


# =========================================================================
# M6.1.7 S1 follow-up — (b2) the Stage-E RENDERER receives the prepared
# object, as an explicit second argument.
#
# Motivation (main agent, measured): `render_report` is wired into
# RunnerDeps at CONSTRUCTION time, before prepare_compute() has run, so a
# one-arg renderer cannot close over the run's pre-exposure authority and
# has to re-derive it at render time — from a registry the run's own
# RUN_STARTED append has already advanced by one event. The contract check
# and its expectation then drift together and agree while being wrong: the
# same structural blindness as the CRLF/two-digest defect above.
#
# The fix is the rule already applied to `compute` and `post_write_verify`:
# post-exposure stages that need the pre-exposure authority take it as a
# parameter. Two arguments, no arity shim.
# =========================================================================


def test_render_report_receives_the_identical_prepared_object(tmp_path):
    """Identity, not equality — the renderer gets THE object `prepare`
    returned, so it never has to go looking for the run's authority."""
    token = {"prepared": ["run", "scoped"], "event_sequence": 7}
    seen: dict = {}

    def renderer(result, prepared):
        seen["result"] = result
        seen["prepared"] = prepared
        return {"S0_REPORT.md": MULTILINE_ARTIFACT}

    sentinel = {"sentinel": True}
    deps, events, _ = make_deps(tmp_path, gates=[ok_gate()],
                                prepare=lambda: token,
                                compute=lambda prepared: sentinel,
                                renderer=renderer)
    out = S0Runner(deps).run()

    assert out.ok is True, (out.failure_kind, out.failed_gate)
    assert seen["prepared"] is token                 # the pre-exposure object
    assert seen["result"] is sentinel                # ... and the Stage-C one
    assert [e for e, _ in events] == ["RUN_STARTED", "COMPLETED"]
    # the same object reached all three post-exposure stages
    assert (out.runs_dir / "S0_REPORT.md").read_bytes() == \
        MULTILINE_ARTIFACT.encode("utf-8")


def test_one_argument_render_report_is_rejected_not_tolerated(tmp_path):
    """No arity shim: a renderer that declares only `(result)` must FAIL,
    loudly, instead of being quietly accommodated by an optional second
    argument — an optional parameter would let exactly the defective
    one-arg renderer keep re-deriving the run's authority in silence.

    The failure is a Stage-E RUN failure (the renderer cannot be called
    before its inputs exist, so the arity defect is only observable after
    the exposure boundary): trial burned, artifacts and failure evidence
    retained. That cost is the point — it is loud."""
    calls: list = []

    def one_arg_renderer(result):                    # the defective wiring
        calls.append(result)
        return {"S0_REPORT.md": MULTILINE_ARTIFACT}

    deps, events, _ = make_deps(tmp_path, gates=[ok_gate()],
                                renderer=one_arg_renderer)
    out = S0Runner(deps).run()

    assert out.ok is False
    assert out.failure_kind == "run_failure"
    assert out.terminal_stage == RunStage.E_REPORT
    assert out.failed_gate == "render_report"
    assert calls == []                               # never even entered
    assert [e for e, _ in events] == ["RUN_STARTED", "FAILED"]
    # nothing was written or chained on the strength of a defective renderer
    assert not (out.runs_dir / "S0_REPORT.md").exists()
    assert not (out.runs_dir / "manifest.jsonl").exists()
    assert "E_REPORT" not in out.stages_completed
    # the failure is DISCLOSED, not swallowed: report + sealed raw detail
    assert (out.runs_dir / "RUN_FAILURE_REPORT.md").exists()
    sealed = (out.runs_dir
              / f"INCIDENT_{out.incident_id}.md").read_text("utf-8")
    assert "TypeError" in sealed                     # the arity error itself
    # F-27 still holds: a TypeError is not one of the governance contracts
    payload = json.loads((out.runs_dir / "RUN_FAILURE_REPORT.json")
                         .read_text("utf-8"))
    assert payload["exception_type"] == "Unknown"


def test_runner_source_wires_the_two_argument_render_call():
    """The contract lives in the runner, not only in these fixtures: the
    call site passes `prepared`, and NO arity-adapting shim exists anywhere
    in the module (an `inspect.signature`-based adapter is the exact thing
    that would restore the silence)."""
    source = inspect.getsource(S0Runner.run)
    assert "d.render_report(result, prepared)" in source
    assert "d.render_report(result)" not in source
    module_source = inspect.getsource(sys.modules[S0Runner.__module__])
    for shim in ("import inspect", "inspect.signature", "getfullargspec",
                 "co_argcount", "except TypeError"):
        assert shim not in module_source, shim


# =========================================================================
# M6.1.8 S1 — defect H-1: the Stage-E artifact log line burned real runs
#
# THE DEFECT. Eight of the ten official sealed artifact names are
# `MC_HANDOFF_<engine>_<scenario>.jsonl` over the frozen engine axis
# `("E1", "E2")`, and `runinfra._FORBIDDEN_VOCAB_RE` matches `e1`/`e2`
# case-insensitively. The Stage-E log line used to interpolate the real
# name, so the production guarded logger refused eight lines per run;
# `_safe_log` banked each refusal in `_log_errors`, whose next inspection
# was at Stage F. A run therefore sealed every artifact correctly,
# completed Stage E, and was then killed at Stage F with gate='log_guard',
# exposure already consumed. It fires on any run that reaches Stage-E
# artifact recording without having failed earlier for another reason.
#
# THE FRAMING. The guard rejection is a FALSE POSITIVE. These names are
# run-invariant structural constants fixed by the frozen contract's
# engine x scenario matrix, identical in every run and carrying zero
# data-derived information; the guard (SA-6 F-04) exists to stop
# Stage-C-derived VALUES from reaching logs. The fix is a WORKAROUND that
# respects a guard vocabulary this lane is not authorized to edit — not
# the correction of a real leak, and nothing here implies the names were
# ever dangerous. The opaque ordinal is informationally EQUIVALENT to the
# name it replaces (the write order is fixed and documented), which is
# fine precisely because the names carry no information — it must not be
# described as hiding anything.
#
# The existing suite missed all of this because every renderer fixture in
# it emitted guard-safe names such as "S0_REPORT.md" / "a.txt".
# =========================================================================

# The frozen engine x scenario matrix, spelled out here rather than imported
# so this pin is INDEPENDENT of the constants the production renderer uses.
# Cross-checked against itsf.s0.study.ENGINES / itsf.s0.handoff.SCENARIOS by
# `test_h1_official_artifact_name_fixture_matches_the_frozen_axes`.
_H1_ENGINES = ("E1", "E2")
_H1_SCENARIOS = ("Base", "Conservative", "Stress", "Severe")

# The ten official sealed artifact names, in the production write order
# (scripts/s0_real_run.py: the engine x scenario handoff files, then
# HANDOFF_ADMISSION.json, then S0_REPORT.md).
OFFICIAL_SEALED_ARTIFACTS: tuple[str, ...] = tuple(
    f"MC_HANDOFF_{eng}_{scn}.jsonl"
    for eng in _H1_ENGINES for scn in _H1_SCENARIOS
) + ("HANDOFF_ADMISSION.json", "S0_REPORT.md")

# Synthetic bodies: multi-line, distinct per artifact, zero research content.
_H1_BODIES: dict[str, str] = {
    name: f"synthetic body for slot {i}\nline two\n"
    for i, name in enumerate(OFFICIAL_SEALED_ARTIFACTS)
}


def _h1_renderer(result, prepared):
    """Stage-E renderer emitting the OFFICIAL names, in the official order."""
    return dict(_H1_BODIES)


def _h1_digest(name: str) -> str:
    return runinfra.hashlib.sha256(
        _H1_BODIES[name].encode("utf-8")).hexdigest()


def _h1_manifest_file_records(runs_dir: Path):
    records = [json.loads(ln) for ln in
               (runs_dir / "manifest.jsonl").read_text("utf-8").splitlines()
               if ln.strip()]
    return [r for r in records if r["record_type"] == "file"]


def test_h1_official_artifact_name_fixture_matches_the_frozen_axes():
    """The fixture above is only evidence if it is the REAL matrix."""
    from itsf.s0 import handoff as _handoff
    from itsf.s0 import study as _study
    assert tuple(_study.ENGINES) == _H1_ENGINES
    assert tuple(_handoff.SCENARIOS) == _H1_SCENARIOS
    assert len(OFFICIAL_SEALED_ARTIFACTS) == 10
    assert len(set(OFFICIAL_SEALED_ARTIFACTS)) == 10
    # and the production renderer builds the handoff names this exact way
    script = (REPO / "scripts" / "s0_real_run.py").read_text("utf-8")
    assert 'name = f"MC_HANDOFF_{eng}_{scn}.jsonl"' in script


def test_h1_preimage_real_names_are_refused_by_the_production_guard():
    """The defect's preimage, re-measured here rather than asserted: in the
    OLD log form, 8 of the 10 official names are refused by
    `runinfra.validate_log_event` and 2 pass. This is what made a fully
    sealed run die at Stage F. It also pins that the fix did NOT relax the
    guard: if this test ever passes 10/10, someone edited
    `_FORBIDDEN_VOCAB`, which M6.1.8 S1 forbids."""
    refused, passed = [], []
    for name in OFFICIAL_SEALED_ARTIFACTS:
        message = f"file={name} sha256={_h1_digest(name)}"
        try:
            runinfra.validate_log_event(message)
            passed.append(name)
        except runinfra.LogLeakError:
            refused.append(name)
    assert refused == [f"MC_HANDOFF_{eng}_{scn}.jsonl"
                       for eng in _H1_ENGINES for scn in _H1_SCENARIOS]
    assert passed == ["HANDOFF_ADMISSION.json", "S0_REPORT.md"]
    # the guard vocabulary itself is untouched by this milestone
    assert "e1" in runinfra._FORBIDDEN_VOCAB
    assert "e2" in runinfra._FORBIDDEN_VOCAB


def test_h1_every_official_artifact_passes_the_guard_in_its_new_log_form():
    """Requirement 1: all ten official names, in the form the runner now
    emits, pass the PRODUCTION guard `runinfra.validate_log_event`."""
    for position, name in enumerate(OFFICIAL_SEALED_ARTIFACTS, start=1):
        message = f"file={artifact_log_id(position)} sha256={_h1_digest(name)}"
        runinfra.validate_log_event(message)         # raises on refusal
        # explicitly against the file-hash schema, not merely "some schema"
        runinfra.validate_log_event(message, schema="file_hash")


def test_h1_opaque_id_is_zero_padded_and_order_derived_only():
    """The id encodes the WRITE ORDER and nothing else — no engine, no
    scenario, no theta, no cost, no result."""
    assert artifact_log_id(1) == "artifact_0001"
    assert artifact_log_id(10) == "artifact_0010"
    assert artifact_log_id(9999) == "artifact_9999"
    # pure function of the ordinal: same input, same output, no run state
    assert artifact_log_id(3) == artifact_log_id(3)
    source = inspect.getsource(sys.modules[S0Runner.__module__])
    for banned in ("engine", "scenario", "theta"):
        assert f"artifact_log_id({banned}" not in source


@pytest.mark.parametrize("wiring", ["bare_validator", "sinking_wrapper"])
def test_h1_full_run_with_official_artifact_names_completes(tmp_path, wiring):
    """THE REGRESSION THAT WOULD HAVE CAUGHT H-1. A full A->F run through
    the REAL S0Runner, with the official artifact names and the production
    log guard wired, must reach COMPLETED."""
    sink: list[str] = []
    log = (runinfra.validate_log_event if wiring == "bare_validator"
           else guarded_logger(sink))
    deps, events, _ = make_deps(tmp_path, gates=[ok_gate()],
                                b_checks=[GateCheck("b1",
                                                    lambda: (True, "ok"))],
                                integrity=[lambda r: (True, "ok")],
                                renderer=_h1_renderer, log=log)
    out = S0Runner(deps).run()
    assert out.ok is True, f"H-1 regression: {out.failed_gate}"
    assert out.failed_gate == ""
    assert out.terminal_stage == RunStage.F_SEALED
    assert out.exposure_consumed is True
    assert out.stages_completed == ("A_PRECHECK", "B_LOAD_VALIDATE",
                                    "C_COMPUTE", "D_INTEGRITY", "E_REPORT",
                                    "F_SEALED")
    assert [e for e, _ in events] == ["RUN_STARTED", "COMPLETED"]
    # all ten artifacts are on disk with the renderer's exact bytes
    for name in OFFICIAL_SEALED_ARTIFACTS:
        assert (out.runs_dir / name).read_bytes() == \
            _H1_BODIES[name].encode("utf-8")


def test_h1_artifact_log_lines_carry_only_the_opaque_id_and_a_digest(tmp_path):
    """Every artifact line the logger RECEIVES is `file=artifact_NNNN
    sha256=<64hex>` — no E1/E2, no other forbidden vocabulary anywhere in
    any line the run emitted."""
    sink: list[str] = []
    deps, _, _ = make_deps(tmp_path, gates=[ok_gate()],
                           renderer=_h1_renderer, log=guarded_logger(sink))
    out = S0Runner(deps).run()
    assert out.ok is True

    file_lines = [m for m in sink if m.startswith("file=")]
    assert len(file_lines) == len(OFFICIAL_SEALED_ARTIFACTS)
    expected = [f"file={artifact_log_id(i)} sha256={_h1_digest(name)}"
                for i, name in enumerate(OFFICIAL_SEALED_ARTIFACTS, start=1)]
    assert file_lines == expected

    # The IDENTIFIER token is where a name would have leaked; it must not
    # contain e1/e2 at all, in any case. (The 64-hex digest is checked
    # separately below: `e1` occurs there as an ordinary hex substring, which
    # is exactly why the production guard is a word-boundary regex and not a
    # substring test — asserting a bare `"e1" not in message` here would be a
    # test that cannot pass for reasons unrelated to the defect.)
    for message in file_lines:
        token = message.split(" ", 1)[0].removeprefix("file=")
        lowered = token.lower()
        assert "e1" not in lowered and "e2" not in lowered, token
        assert token in {artifact_log_id(i) for i in
                         range(1, len(OFFICIAL_SEALED_ARTIFACTS) + 1)}

    for message in sink:
        # no real artifact name survived into any log line
        for name in OFFICIAL_SEALED_ARTIFACTS:
            assert name not in message
        # no forbidden vocabulary anywhere, by the PRODUCTION regex — which
        # is the same test the guard itself applies, `e1`/`e2` included
        assert runinfra._FORBIDDEN_VOCAB_RE.search(message) is None, message
        runinfra.validate_log_event(message)


def test_h1_manifest_keeps_real_names_digests_and_order(tmp_path):
    """Requirement 3: the manifest is EVIDENCE and is untouched — real
    names, real digests, existing order — and the digest it records is the
    digest of the bytes actually on disk."""
    sink: list[str] = []
    deps, _, _ = make_deps(tmp_path, gates=[ok_gate()],
                           renderer=_h1_renderer, log=guarded_logger(sink))
    out = S0Runner(deps).run()
    assert out.ok is True

    files = _h1_manifest_file_records(out.runs_dir)
    assert [r["relative_path"] for r in files] == list(
        OFFICIAL_SEALED_ARTIFACTS)
    for record, name in zip(files, OFFICIAL_SEALED_ARTIFACTS):
        assert record["file_sha256"] == _h1_digest(name)
        assert record["file_sha256"] == runinfra.hashlib.sha256(
            (out.runs_dir / name).read_bytes()).hexdigest()
    # the opaque log id appears NOWHERE in the sealed manifest bytes
    manifest_text = (out.runs_dir / "manifest.jsonl").read_text("utf-8")
    for position in range(1, len(OFFICIAL_SEALED_ARTIFACTS) + 1):
        assert artifact_log_id(position) not in manifest_text
    # and the logged digests are exactly the chained digests, in order
    assert [m.split("sha256=")[1] for m in sink if m.startswith("file=")] == \
        [r["file_sha256"] for r in files]


def test_h1_log_errors_is_empty_after_a_successful_run(tmp_path):
    """Nothing was banked and silently carried: a clean run ends with an
    EMPTY `_log_errors`, so no checkpoint anywhere had anything to find."""
    deps, _, _ = make_deps(tmp_path, gates=[ok_gate()],
                           b_checks=[GateCheck("b1", lambda: (True, "ok"))],
                           integrity=[lambda r: (True, "ok")],
                           renderer=_h1_renderer,
                           log=guarded_logger([]))
    runner = S0Runner(deps)
    out = runner.run()
    assert out.ok is True
    assert runner._log_errors == []


def test_h1_stage_e_log_defect_is_attributed_to_stage_e(tmp_path):
    """The ATTRIBUTION half. With a logger that refuses only `file=` lines,
    the failure is now reported against E_REPORT (stage did not close), not
    against F_SEALED.

    This is explicitly NOT the fix: both checkpoints are post-exposure, so
    `exposure_consumed` is True either way and the trial burns either way —
    only the reported stage changes."""
    def refuses_file_lines(message: str) -> None:
        if message.startswith("file="):
            raise runinfra.LogLeakError("synthetic Stage-E refusal")

    deps, events, _ = make_deps(tmp_path, gates=[ok_gate()],
                                renderer=_h1_renderer,
                                log=refuses_file_lines)
    out = S0Runner(deps).run()
    assert out.ok is False
    assert out.terminal_stage == RunStage.E_REPORT
    assert out.failed_gate == "log_guard"
    assert out.exposure_consumed is True              # unchanged: post-exposure
    assert "E_REPORT" not in out.stages_completed
    assert "D_INTEGRITY" in out.stages_completed
    assert [e for e, _ in events] == ["RUN_STARTED", "FAILED"]
    # artifacts and manifest are RETAINED for adjudication
    assert len(_h1_manifest_file_records(out.runs_dir)) == len(
        OFFICIAL_SEALED_ARTIFACTS)
    assert (out.runs_dir / "RUN_FAILURE_REPORT.md").exists()


@pytest.mark.parametrize("seam", ["prepare_compute", "post_write_verify",
                                  "pre_exposure_recheck"])
def test_h1_unwired_critical_seam_still_refuses_before_exposure(tmp_path,
                                                                seam):
    """UNCHANGED BEHAVIOUR pin. The M6.1.8 checkpoint move must not have
    dragged any fail-closed wiring check across the exposure boundary: an
    unwired critical callback still refuses PRE-exposure — no runs dir, no
    RUN_STARTED, trial not burned."""
    deps, events, _ = make_deps(tmp_path, gates=[ok_gate()],
                                renderer=_h1_renderer)
    object.__setattr__(deps, seam, None)
    out = S0Runner(deps).run()
    assert out.ok is False
    assert out.exposure_consumed is False
    assert out.failure_kind == "pre_run_attempt"
    assert out.terminal_stage == RunStage.B_LOAD_VALIDATE
    assert [e for e, _ in events] == ["PRE_RUN_ATTEMPT_FAILURE"]
    assert not Path(deps.config.runs_dir).exists()


# --- completeness pin -----------------------------------------------------
# A fix that is only LOCALLY correct is not a fix. `:519` was claimed to be
# the only log emission carrying a variable payload; the test below makes
# that claim CHECKABLE at source level instead of asserted, by walking every
# `self._safe_log(...)` call in the module and proving each one interpolates
# nothing but RunStage enum values (plus fixed status literals) — with a
# single, named exception: the artifact line, which may interpolate only the
# opaque ordinal and the digest.

_H1_ALLOWED_STAGE_EXPRS = frozenset({
    "RunStage.A_PRECHECK.value", "RunStage.B_LOAD_VALIDATE.value",
    "RunStage.C_COMPUTE.value", "RunStage.D_INTEGRITY.value",
    "RunStage.E_REPORT.value", "RunStage.F_SEALED.value",
    "stage.value",                       # the RunStage parameter of _fail_*
})
_H1_ALLOWED_STAGE_LITERALS = frozenset({
    "stage=", " status=start", " status=end", " status=fail", " status=pass",
})
_H1_ALLOWED_ARTIFACT_EXPRS = frozenset({"artifact_log_id(position)", "digest"})
_H1_ALLOWED_ARTIFACT_LITERALS = frozenset({"file=", " sha256="})
_H1_SAFE_LOG_CALL_COUNT = 15             # pin: a NEW log call must be reviewed


def _h1_safe_log_calls():
    """Every `self._safe_log(...)` in runner.py as
    (enclosing_function_name, literal_parts, interpolated_exprs)."""
    import ast
    module = sys.modules[S0Runner.__module__]
    tree = ast.parse(inspect.getsource(module))
    owner: dict[int, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for child in ast.walk(node):
                owner.setdefault(id(child), node.name)
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        if not (isinstance(fn, ast.Attribute) and fn.attr == "_safe_log"
                and isinstance(fn.value, ast.Name) and fn.value.id == "self"):
            continue
        assert len(node.args) == 1 and not node.keywords, ast.dump(node)
        arg = node.args[0]
        assert isinstance(arg, ast.JoinedStr), (
            "a _safe_log argument that is not an f-string literal cannot be "
            f"reviewed statically: {ast.unparse(arg)}")
        literals = [p.value for p in arg.values
                    if isinstance(p, ast.Constant)]
        exprs = [ast.unparse(p.value) for p in arg.values
                 if isinstance(p, ast.FormattedValue)]
        # no format-spec / conversion trickery on the way to the logger
        assert all(p.conversion == -1 and p.format_spec is None
                   for p in arg.values
                   if isinstance(p, ast.FormattedValue)), ast.unparse(arg)
        found.append((owner.get(id(node), "<module>"), literals, exprs))
    return found


def test_h1_completeness_only_record_artifacts_logs_a_variable_payload():
    """COMPLETENESS PIN. Prove `:519` was the ONLY log emission with a
    variable payload: every other `self._safe_log` call in runner.py
    interpolates nothing but RunStage enum values and fixed status
    literals."""
    calls = _h1_safe_log_calls()
    assert len(calls) == _H1_SAFE_LOG_CALL_COUNT, (
        f"the number of _safe_log call sites changed ({len(calls)} != "
        f"{_H1_SAFE_LOG_CALL_COUNT}); a new log emission must be reviewed "
        f"against the H-1 finding and this pin updated deliberately")

    variable = [c for c in calls
                if not set(c[2]) <= _H1_ALLOWED_STAGE_EXPRS]
    assert len(variable) == 1, (
        "exactly one log emission may carry a variable payload; found "
        + repr([(fn, exprs) for fn, _, exprs in variable]))

    fn_name, literals, exprs = variable[0]
    assert fn_name == "_record_artifacts", fn_name
    assert set(exprs) <= _H1_ALLOWED_ARTIFACT_EXPRS, exprs
    assert set(literals) <= _H1_ALLOWED_ARTIFACT_LITERALS, literals
    # the artifact NAME is not among them — that is the H-1 fix
    assert "name" not in exprs

    for fn_name, literals, exprs in calls:
        if fn_name == "_record_artifacts":
            continue
        assert set(exprs) <= _H1_ALLOWED_STAGE_EXPRS, (fn_name, exprs)
        assert set(literals) <= _H1_ALLOWED_STAGE_LITERALS, (fn_name, literals)


def test_h1_log_errors_checkpoint_follows_record_artifacts():
    """The attribution checkpoint is where the brief put it: immediately
    after `_record_artifacts`, before Stage E is marked complete."""
    source = inspect.getsource(S0Runner.run)
    after = source.split("self._record_artifacts(", 1)[1]
    idx_check = after.index("if self._log_errors:")
    idx_stage_done = after.index(
        "self._stages_done.append(RunStage.E_REPORT.value)")
    assert idx_check < idx_stage_done
    checkpoint = after[idx_check:idx_stage_done]
    assert '"log_guard"' in checkpoint
    assert "RunStage.E_REPORT" in checkpoint


# ===========================================================================
# L-5 ruling (2026-08-10) — output-root validation gate + post-seal archive
# ===========================================================================
#
# Deliverables covered in this section:
#   1. validate_output_roots direct unit tests (runinfra, pure logic)
#   2. the intrinsic Stage-A gate wiring in runner.py: order, naming, the
#      repo-runs/ refusal (never creates a directory under the repo tree)
#   3. the post-seal archive step: success + injected-mismatch paths
#   4. the exact-set disk proof on the new root: full pipeline COMPLETED,
#      zero-whitelist extra-file refusal, attempts/ under the same root


def _rc(**overrides) -> RunConfig:
    """Minimal RunConfig for direct `validate_output_roots` unit tests —
    every field the gate does not care about is a fixed sentinel."""
    base = dict(trial_id="S0-T001", authorized_commit="a" * 40,
               engineering_seed=1, attempts_dir="UNSET", runs_dir="UNSET",
               assertions_path="UNSET", runs_root="UNSET",
               archive_root="UNSET")
    base.update(overrides)
    return RunConfig(**base)


# --- 1. validate_output_roots — direct unit tests (runinfra) ---------------


def test_validate_output_roots_passes_with_disjoint_tmp_roots(tmp_path):
    runs_root = tmp_path / "runs_root"
    archive_root = tmp_path / "archive_root"
    cfg = _rc(runs_root=str(runs_root), archive_root=str(archive_root),
             runs_dir=str(runs_root / "runs" / "S0-T001"),
             attempts_dir=str(runs_root / "attempts" / "A001"))
    runinfra.validate_output_roots(cfg, REPO)          # must not raise


def test_validate_output_roots_refuses_non_runconfig_cfg():
    with pytest.raises(RunGateError, match="RunConfig"):
        runinfra.validate_output_roots(object(), REPO)


def test_validate_output_roots_refuses_non_path_repo_root(tmp_path):
    runs_root = tmp_path / "runs_root"
    cfg = _rc(runs_root=str(runs_root),
             archive_root=str(tmp_path / "archive_root"),
             runs_dir=str(runs_root / "runs" / "S0-T001"),
             attempts_dir=str(runs_root / "attempts" / "A001"))
    with pytest.raises(RunGateError, match="repo_root"):
        runinfra.validate_output_roots(cfg, str(REPO))


def test_validate_output_roots_refuses_relative_runs_root(tmp_path):
    cfg = _rc(runs_root="relative/runs_root",
             archive_root=str(tmp_path / "archive_root"),
             runs_dir=str(tmp_path / "runs_root" / "runs" / "S0-T001"),
             attempts_dir=str(tmp_path / "runs_root" / "attempts" / "A001"))
    with pytest.raises(RunGateError, match="runs_root"):
        runinfra.validate_output_roots(cfg, REPO)


def test_validate_output_roots_refuses_relative_archive_root(tmp_path):
    runs_root = tmp_path / "runs_root"
    cfg = _rc(runs_root=str(runs_root), archive_root="relative/archive",
             runs_dir=str(runs_root / "runs" / "S0-T001"),
             attempts_dir=str(runs_root / "attempts" / "A001"))
    with pytest.raises(RunGateError, match="archive_root"):
        runinfra.validate_output_roots(cfg, REPO)


def test_validate_output_roots_refuses_relative_runs_dir(tmp_path):
    runs_root = tmp_path / "runs_root"
    cfg = _rc(runs_root=str(runs_root),
             archive_root=str(tmp_path / "archive_root"),
             runs_dir="relative/runs_dir",
             attempts_dir=str(runs_root / "attempts" / "A001"))
    with pytest.raises(RunGateError, match="runs_dir"):
        runinfra.validate_output_roots(cfg, REPO)


def test_validate_output_roots_refuses_runs_root_inside_repo_tree(tmp_path):
    """The exact historical bug this ruling closes:
    `RUNS_ROOT = REPO / "runs"`."""
    runs_root = REPO / "runs"
    cfg = _rc(runs_root=str(runs_root),
             archive_root=str(tmp_path / "archive_root"),
             runs_dir=str(runs_root / "runs" / "S0-T001"),
             attempts_dir=str(runs_root / "attempts" / "A001"))
    with pytest.raises(RunGateError, match="disjoint"):
        runinfra.validate_output_roots(cfg, REPO)


def test_validate_output_roots_refuses_repo_root_nested_inside_runs_root(tmp_path):
    """The INVERTED containment case: runs_root is an ANCESTOR of the repo
    root. Disjointness must be checked in both directions."""
    runs_root = REPO.parent
    cfg = _rc(runs_root=str(runs_root),
             archive_root=str(tmp_path / "archive_root"),
             runs_dir=str(runs_root / "runs" / "S0-T001"),
             attempts_dir=str(runs_root / "attempts" / "A001"))
    with pytest.raises(RunGateError, match="disjoint"):
        runinfra.validate_output_roots(cfg, REPO)


def test_validate_output_roots_refuses_archive_root_inside_repo_tree(tmp_path):
    runs_root = tmp_path / "runs_root"
    cfg = _rc(runs_root=str(runs_root), archive_root=str(REPO / "archive"),
             runs_dir=str(runs_root / "runs" / "S0-T001"),
             attempts_dir=str(runs_root / "attempts" / "A001"))
    with pytest.raises(RunGateError, match="disjoint"):
        runinfra.validate_output_roots(cfg, REPO)


def test_validate_output_roots_refuses_archive_root_equal_to_runs_root(tmp_path):
    shared = tmp_path / "shared_root"
    cfg = _rc(runs_root=str(shared), archive_root=str(shared),
             runs_dir=str(shared / "runs" / "S0-T001"),
             attempts_dir=str(shared / "attempts" / "A001"))
    with pytest.raises(RunGateError, match="disjoint"):
        runinfra.validate_output_roots(cfg, REPO)


def test_validate_output_roots_refuses_archive_root_nested_inside_runs_root(tmp_path):
    runs_root = tmp_path / "runs_root"
    cfg = _rc(runs_root=str(runs_root),
             archive_root=str(runs_root / "archive_root"),
             runs_dir=str(runs_root / "runs" / "S0-T001"),
             attempts_dir=str(runs_root / "attempts" / "A001"))
    with pytest.raises(RunGateError, match="disjoint"):
        runinfra.validate_output_roots(cfg, REPO)


def test_validate_output_roots_refuses_runs_root_nested_inside_archive_root(tmp_path):
    archive_root = tmp_path / "archive_root"
    runs_root = archive_root / "runs_root"
    cfg = _rc(runs_root=str(runs_root), archive_root=str(archive_root),
             runs_dir=str(runs_root / "runs" / "S0-T001"),
             attempts_dir=str(runs_root / "attempts" / "A001"))
    with pytest.raises(RunGateError, match="disjoint"):
        runinfra.validate_output_roots(cfg, REPO)


def test_validate_output_roots_refuses_runs_dir_not_under_runs_root(tmp_path):
    runs_root = tmp_path / "runs_root"
    elsewhere = tmp_path / "elsewhere" / "S0-T001"
    cfg = _rc(runs_root=str(runs_root),
             archive_root=str(tmp_path / "archive_root"),
             runs_dir=str(elsewhere),
             attempts_dir=str(runs_root / "attempts" / "A001"))
    with pytest.raises(RunGateError, match="runs_dir"):
        runinfra.validate_output_roots(cfg, REPO)


def test_validate_output_roots_refuses_runs_dir_equal_to_runs_root(tmp_path):
    """`runs_dir` must resolve STRICTLY under `runs_root` — equal is not
    good enough (it must be a proper descendant)."""
    runs_root = tmp_path / "runs_root"
    cfg = _rc(runs_root=str(runs_root),
             archive_root=str(tmp_path / "archive_root"),
             runs_dir=str(runs_root),
             attempts_dir=str(runs_root / "attempts" / "A001"))
    with pytest.raises(RunGateError, match="runs_dir"):
        runinfra.validate_output_roots(cfg, REPO)


def test_validate_output_roots_refuses_attempts_dir_not_under_runs_root(tmp_path):
    runs_root = tmp_path / "runs_root"
    cfg = _rc(runs_root=str(runs_root),
             archive_root=str(tmp_path / "archive_root"),
             runs_dir=str(runs_root / "runs" / "S0-T001"),
             attempts_dir=str(tmp_path / "elsewhere" / "A001"))
    with pytest.raises(RunGateError, match="attempts_dir"):
        runinfra.validate_output_roots(cfg, REPO)


def test_runconfig_defaults_are_the_ruled_roots():
    """Sanity check on the contracts.py interface this gate depends on."""
    cfg = RunConfig(trial_id="x", authorized_commit="a" * 40,
                    engineering_seed=1, attempts_dir="a", runs_dir="r",
                    assertions_path="p")
    assert cfg.runs_root == RULED_RUNS_ROOT
    assert cfg.archive_root == RULED_ARCHIVE_ROOT


# --- 2. the intrinsic Stage-A gate wiring (runner.py) -----------------------


def test_output_roots_gate_refuses_runs_root_inside_repo_tree_via_runner(tmp_path):
    """Deliverable 2: a config whose runs_root/runs_dir sits inside the
    repo tree (the exact historical bug, `RUNS_ROOT = REPO / "runs"`) is
    refused by the runner's own Stage-A gate, pre-exposure — and NOTHING
    is ever created under the repo tree in the process.

    UPDATED BY CODEX ROUND-2 #2. This test used to close by asserting
    "the attempts artifacts DID land, but only in the safe tmp location"
    — i.e. it pinned the very behaviour the round-2 holding refuses. A
    failure of `output_roots_validated` means every governed output path
    on the config is unvalidated, INCLUDING an `attempts_dir` that looks
    fit; the refusal must therefore write to none of them. The assertion
    is inverted below, and `test_root_gate_refusal_writes_nothing_even_to_
    a_valid_looking_attempts_dir` is the dedicated regression."""
    bad_runs_root = REPO / "runs"
    safe_attempts_dir = tmp_path / "attempts" / "A001"
    safe_archive_root = tmp_path / "archive_root"
    deps, events, _ = make_deps(
        tmp_path, gates=[ok_gate()],
        runs_root=bad_runs_root,
        runs_dir=bad_runs_root / "runs" / "S0-T001_20260810T000000Z",
        attempts_dir=safe_attempts_dir,
        archive_root=safe_archive_root)
    out = S0Runner(deps).run()
    assert out.ok is False
    assert out.failure_kind == "pre_run_attempt"
    assert out.failed_gate == "output_roots_validated"
    assert out.terminal_stage == RunStage.A_PRECHECK
    assert out.exposure_consumed is False
    assert [e for e, _ in events] == ["PRE_RUN_ATTEMPT_FAILURE"]
    # the hard constraint, proven directly against the real filesystem:
    # nothing landed under the repo tree at all.
    assert not bad_runs_root.exists()
    assert not (REPO / "runs").exists()
    # Codex round-2 #2: and NOTHING landed on the safe-looking attempts
    # path either — a refusal of the root gate is zero-I/O on every
    # configured output path, not just the ones that look unfit.
    assert not safe_attempts_dir.exists()
    assert out.attempts_dir is None


def test_output_roots_gate_runs_before_any_injected_stage_a_gate(tmp_path):
    """Proves the intrinsic gate runs FIRST: an injected gate that would
    otherwise pass never even executes when the roots are bad."""
    calls: list[str] = []

    def tracking_gate():
        calls.append("injected_gate_ran")
        return True, "ok"

    bad_runs_root = REPO / "runs"
    deps, events, _ = make_deps(
        tmp_path, gates=[GateCheck("tracked", tracking_gate)],
        runs_root=bad_runs_root,
        runs_dir=bad_runs_root / "runs" / "S0-T001",
        attempts_dir=tmp_path / "attempts" / "A001",
        archive_root=tmp_path / "archive_root")
    out = S0Runner(deps).run()
    assert out.failed_gate == "output_roots_validated"
    assert calls == []                     # the injected gate never ran
    assert not bad_runs_root.exists()


def test_output_roots_gate_unconditional_even_with_zero_injected_gates(tmp_path):
    """The intrinsic gate does not depend on the caller (the entry
    script) remembering to wire anything into `d.gates` — an EMPTY gate
    list still refuses a bad runs_root."""
    bad_runs_root = REPO / "runs"
    deps, events, _ = make_deps(
        tmp_path, gates=[],
        runs_root=bad_runs_root,
        runs_dir=bad_runs_root / "runs" / "S0-T001",
        attempts_dir=tmp_path / "attempts" / "A001",
        archive_root=tmp_path / "archive_root")
    out = S0Runner(deps).run()
    assert out.failed_gate == "output_roots_validated"
    assert not bad_runs_root.exists()


# --- 3. post-seal archive step -----------------------------------------—---


def test_archive_sealed_run_success_full_recheck_manifest(tmp_path):
    src = tmp_path / "runs_root" / "runs" / "S0-T001_20260810T000000Z"
    src.mkdir(parents=True)
    (src / "S0_REPORT.md").write_bytes(b"sealed report body\n")
    (src / "manifest.jsonl").write_bytes(b'{"a":1}\n')
    nested = src / "sub"
    nested.mkdir()
    (nested / "leaf.txt").write_bytes(b"leaf bytes")
    archive_root = tmp_path / "archive_root"

    report = runinfra.archive_sealed_run(src, archive_root)

    assert report.ok is True
    assert report.status == "archive_ok"
    assert report.errors == ()
    assert report.run_dir_name == src.name
    by_rel = {f.relative_path: f for f in report.files}
    assert set(by_rel) == {"S0_REPORT.md", "manifest.jsonl", "sub/leaf.txt"}
    for rel, rec in by_rel.items():
        assert rec.match is True
        assert rec.source_sha256 == rec.dest_sha256
        assert rec.source_bytes == rec.dest_bytes
        dest_path = archive_root / src.name / rel
        assert dest_path.read_bytes() == (src / rel).read_bytes()
    # nothing about the SOURCE (sealed run) directory was touched
    assert (src / "S0_REPORT.md").read_bytes() == b"sealed report body\n"


def test_archive_sealed_run_detects_injected_mismatch(tmp_path, monkeypatch):
    """Injected-mismatch path: the DEST-side write is tampered with after
    the source is read, simulating a copy that silently corrupted one
    file. The independent re-read + re-hash on both sides must catch it."""
    src = tmp_path / "runs_root" / "runs" / "S0-T001_20260810T000000Z"
    src.mkdir(parents=True)
    (src / "S0_REPORT.md").write_bytes(b"sealed report body\n")
    (src / "manifest.jsonl").write_bytes(b'{"a":1}\n')
    archive_root = tmp_path / "archive_root"

    real_write_bytes = Path.write_bytes

    def tampering_write_bytes(self, data):
        if self.name == "manifest.jsonl" and archive_root.name in self.parts:
            data = data + b"TAMPERED"
        return real_write_bytes(self, data)

    monkeypatch.setattr(Path, "write_bytes", tampering_write_bytes)

    report = runinfra.archive_sealed_run(src, archive_root)

    assert report.ok is False
    assert report.status == "archive_failed"
    assert report.errors
    by_rel = {f.relative_path: f for f in report.files}
    assert by_rel["manifest.jsonl"].match is False
    assert by_rel["S0_REPORT.md"].match is True
    # the SOURCE (sealed run) file is untouched by the injected tamper
    assert (src / "manifest.jsonl").read_bytes() == b'{"a":1}\n'


def test_archive_sealed_run_refuses_missing_runs_dir(tmp_path):
    with pytest.raises(FileNotFoundError):
        runinfra.archive_sealed_run(tmp_path / "does_not_exist",
                                    tmp_path / "archive_root")


def test_archive_sealed_run_refuses_existing_destination(tmp_path):
    src = tmp_path / "runs_root" / "runs" / "S0-T001"
    src.mkdir(parents=True)
    (src / "a.txt").write_bytes(b"x")
    archive_root = tmp_path / "archive_root"
    (archive_root / src.name).mkdir(parents=True)

    report = runinfra.archive_sealed_run(src, archive_root)
    assert report.ok is False
    assert report.status == "archive_failed"
    assert any("already exists" in e for e in report.errors)


def test_archive_step_failure_does_not_unseal_or_flip_ok(tmp_path, monkeypatch):
    """Deliverable 3: any mismatch/copy failure keeps the run SEALED —
    `ok` stays True, `terminal_stage` stays F_SEALED, the registry keeps
    COMPLETED, and runs_dir is untouched — while archive_status/
    archive_report loudly record the problem."""
    runs_root, archive_root, runs_dir, attempts_dir = _tmp_output_roots(tmp_path)
    deps, events, _ = make_deps(
        tmp_path, gates=[ok_gate()],
        runs_root=runs_root, archive_root=archive_root,
        runs_dir=runs_dir, attempts_dir=attempts_dir)

    def failing_archive(rdir, aroot):
        return runinfra.ArchiveReport(
            ok=False, status="archive_failed", run_dir_name=rdir.name,
            source_dir=str(rdir), dest_dir=str(Path(aroot) / rdir.name),
            files=(), errors=("synthetic injected archive failure",))

    monkeypatch.setattr(runinfra, "archive_sealed_run", failing_archive)
    out = S0Runner(deps).run()

    assert out.ok is True                          # the run STAYS sealed
    assert out.terminal_stage == RunStage.F_SEALED
    assert out.exposure_consumed is True
    assert out.archive_status == "archive_failed"
    assert out.archive_report.errors == ("synthetic injected archive failure",)
    assert events[-1][0] == "COMPLETED"             # registry unaffected
    assert (runs_dir / "S0_REPORT.md").exists()     # sealed run dir intact
    assert not (archive_root / runs_dir.name).exists()


def test_archive_step_exception_is_captured_not_propagated(tmp_path, monkeypatch):
    runs_root, archive_root, runs_dir, attempts_dir = _tmp_output_roots(tmp_path)
    deps, events, _ = make_deps(
        tmp_path, gates=[ok_gate()],
        runs_root=runs_root, archive_root=archive_root,
        runs_dir=runs_dir, attempts_dir=attempts_dir)

    def exploding_archive(rdir, aroot):
        raise RuntimeError("synthetic archive-side crash")

    monkeypatch.setattr(runinfra, "archive_sealed_run", exploding_archive)
    out = S0Runner(deps).run()

    assert out.ok is True
    assert out.archive_status == "archive_failed"
    assert out.archive_report is not None
    assert "synthetic archive-side crash" in out.archive_report.errors[0]


def test_archive_step_never_attempted_for_a_failed_run(tmp_path):
    """The archive step is called EXACTLY once, only after F_SEALED — a
    run that fails earlier never triggers it and never touches
    archive_root at all."""
    runs_root, archive_root, runs_dir, attempts_dir = _tmp_output_roots(tmp_path)

    def broken(prepared):
        raise ValueError("synthetic compute crash")

    deps, events, _ = make_deps(
        tmp_path, gates=[ok_gate()], compute=broken,
        runs_root=runs_root, archive_root=archive_root,
        runs_dir=runs_dir, attempts_dir=attempts_dir)
    out = S0Runner(deps).run()

    assert out.ok is False
    assert out.archive_status == ""
    assert out.archive_report is None
    # R5: make_deps pre-creates the default roots (operational gate), so
    # existence is no longer the proxy — the semantic proof is that the
    # archive step left the root EMPTY and reported no archive activity.
    assert archive_root.exists() and not any(archive_root.iterdir())
    assert not out.archive_status          # ''/None: never attempted


# --- 4. exact-set proof on the new root -------------------------------------


def test_full_synthetic_pipeline_reaches_completed_with_new_root_wiring(tmp_path):
    """Deliverable 4, part 1 (+ exercises deliverable 3's success path):
    the full synthetic A-to-F pipeline reaches COMPLETED with the new
    runs_root/archive_root wiring, and the post-seal archive step lands a
    byte-identical copy under archive_root."""
    runs_root, archive_root, runs_dir, attempts_dir = _tmp_output_roots(tmp_path)
    deps, events, logs = make_deps(
        tmp_path, gates=[ok_gate("g1")],
        b_checks=[GateCheck("b1", lambda: (True, "ok"))],
        integrity=[lambda r: (True, "ok")],
        runs_root=runs_root, archive_root=archive_root,
        runs_dir=runs_dir, attempts_dir=attempts_dir)
    out = S0Runner(deps).run()

    assert out.ok is True
    assert out.stages_completed == ("A_PRECHECK", "B_LOAD_VALIDATE",
                                    "C_COMPUTE", "D_INTEGRITY", "E_REPORT",
                                    "F_SEALED")
    assert out.runs_dir == runs_dir
    assert runs_dir.resolve().is_relative_to(runs_root.resolve())
    assert (runs_dir / "S0_REPORT.md").exists()
    assert [e for e, _ in events][0] == "RUN_STARTED"
    assert [e for e, _ in events][-1] == "COMPLETED"
    # the archive step also ran, over the SAME roots, and succeeded
    assert out.archive_status == "archive_ok"
    assert out.archive_report.ok is True
    archived_dir = archive_root / runs_dir.name
    assert (archived_dir / "S0_REPORT.md").read_bytes() == \
        (runs_dir / "S0_REPORT.md").read_bytes()


def test_extra_file_in_run_dir_fails_exact_set_disk_proof_zero_whitelist(tmp_path):
    """Deliverable 4, part 2: zero-whitelist stays. A stray file planted
    in the run directory before the post-write verification seam runs —
    the synthetic analog of a OneDrive sync artifact (`desktop.ini`,
    `*.tmp`) landing in the run dir, which is exactly the L-5 scenario —
    must fail the disk proof. No filename is exempted; this mirrors
    output_proof.py's `REFUSAL_DISK_EXTRA_FILE` zero-whitelist discipline
    (exercised against the real production checker in
    tests/test_m6_chain.py) as the synthetic-harness analog, run through
    S0Runner's own post-write verification seam."""
    runs_root, archive_root, runs_dir, attempts_dir = _tmp_output_roots(tmp_path)

    def exact_set_post_write_verify(rdir, written, prepared):
        declared = {name for name, _ in written}
        on_disk = {p.name for p in rdir.iterdir() if p.is_file()}
        extra = on_disk - declared
        if extra:
            return False, f"disk_extra_file: {sorted(extra)}"
        for name, data in written:
            if (rdir / name).read_bytes() != data:
                return False, f"byte mismatch: {name}"
        return True, f"{len(written)} artifact(s) byte-verified, zero extras"

    def compute_with_stray_file(prepared):
        # The run directory already exists here — Stage C runs strictly
        # after the atomic run-start creates it (packet §6).
        (runs_dir / "desktop.ini").write_bytes(b"[stray sync artifact]")
        return {"sentinel": True}

    deps, events, _ = make_deps(
        tmp_path, gates=[ok_gate()], compute=compute_with_stray_file,
        post_write_verify=exact_set_post_write_verify,
        runs_root=runs_root, archive_root=archive_root,
        runs_dir=runs_dir, attempts_dir=attempts_dir)
    out = S0Runner(deps).run()

    assert out.ok is False
    assert out.failure_kind == "run_failure"
    assert out.terminal_stage == RunStage.E_REPORT
    assert out.failed_gate == "post_write_verify"
    assert out.exposure_consumed is True            # trial already burned
    assert (runs_dir / "desktop.ini").exists()       # nothing deleted
    assert [e for e, _ in events][0] == "RUN_STARTED"
    assert [e for e, _ in events][-1] == "FAILED"
    # a failed run never reaches the archive step
    assert out.archive_status == ""


def test_attempts_dir_lands_under_same_runs_root_as_runs_dir(tmp_path):
    """Deliverable 4, part 3: attempts/ migrates to the SAME root as
    runs/. Exercised via an ordinary Stage-A gate failure (unrelated to
    output-root validation) so the attempts directory actually gets
    created on disk, then checked against runs_root."""
    runs_root, archive_root, runs_dir, attempts_dir = _tmp_output_roots(tmp_path)
    deps, events, _ = make_deps(
        tmp_path, gates=[bad_gate("some_other_gate")],
        runs_root=runs_root, archive_root=archive_root,
        runs_dir=runs_dir, attempts_dir=attempts_dir)
    out = S0Runner(deps).run()

    assert out.failure_kind == "pre_run_attempt"
    assert out.failed_gate == "some_other_gate"
    assert out.attempts_dir is not None
    assert out.attempts_dir.is_dir()
    assert out.attempts_dir.resolve().is_relative_to(runs_root.resolve())
    assert runs_dir.resolve().is_relative_to(runs_root.resolve())
    assert not Path(deps.config.runs_dir).exists()   # never reached Stage C


# ===========================================================================
# S0 CLOSEOUT — Codex final review #3: the L-5 exact-set WINDOW
# ===========================================================================
#
# THE HOLDING. The last full enumeration of the run directory happened in
# the post_write_verify seam, which runs BEFORE `_record_artifacts` writes
# manifest.jsonl and before Stage F exists at all. Everything after that
# point — the manifest write, the chain replay, the eve of the COMPLETED
# registry append — was unwatched, so a file that appeared in that window
# sealed silently inside the evidentiary directory.
#
# Every planting test below wires the SAME exact-set post_write_verify the
# L-5 section already uses, and plants strictly AFTER it has passed. So
# each of them is a direct measurement of the window: on the pre-fix
# runner the seam says "zero extras", the chain verifies, and the run
# reaches COMPLETED with the stray entry on disk.


def _exact_set_post_write_verify(rdir, written, prepared):
    """The M6.1.7 disk seal as the L-5 section models it — the check that
    USED to be the last enumeration of the run directory."""
    declared = {name for name, _ in written}
    on_disk = {p.name for p in rdir.iterdir() if p.is_file()}
    extra = on_disk - declared
    if extra:
        return False, f"disk_extra_file: {sorted(extra)}"
    for name, data in written:
        if (rdir / name).read_bytes() != data:
            return False, f"byte mismatch: {name}"
    return True, f"{len(written)} artifact(s) byte-verified, zero extras"


def _hook_writing_registry_record(rdir: Path) -> None:
    """The synthetic analog of the production `post_run_started_hook`,
    which writes REGISTRY_AFTER_RUN_STARTED.json into the run directory
    (scripts/s0_real_run.py `make_snapshot_control`). The final exact-set
    proof must ACCEPT it — it is one of the run's own writes — without any
    name being hardcoded or whitelisted in the runner."""
    (rdir / "REGISTRY_AFTER_RUN_STARTED.json").write_text(
        json.dumps({"registry_sha256_after_run_started": "0" * 64}, indent=1,
                   sort_keys=True), encoding="utf-8", newline="\n")


def _plant_during_chain_verify(monkeypatch, plant, *, after_verify=False):
    """Injection point BETWEEN the manifest write and the final exact-set
    proof: the runner calls `runinfra.verify_chain_records` there, so a
    wrapper around it runs exactly inside the window Codex #3 names.
    `after_verify=True` delays `plant()` until the real verification has
    already returned its verdict — which is how a DELETION can be tested
    without turning it into a verify_chain failure instead."""
    real = runinfra.verify_chain_records

    def wrapper(*args, **kwargs):
        if not after_verify:
            plant()
        verdict = real(*args, **kwargs)
        if after_verify:
            plant()
        return verdict

    monkeypatch.setattr(runinfra, "verify_chain_records", wrapper)


def test_final_exact_set_honest_run_completes_with_run_started_hook_file(
        tmp_path):
    """The honest path is unchanged: a full synthetic A->F run whose
    post-RUN_STARTED hook writes a file into the run directory still
    reaches COMPLETED. The proof's expected set is derived from the run's
    OWN writes (baseline + artifacts + manifest), so the hook's file is
    accounted for by observation rather than by a hardcoded name."""
    runs_root, archive_root, runs_dir, attempts_dir = _tmp_output_roots(tmp_path)
    deps, events, _ = make_deps(
        tmp_path, gates=[ok_gate("g1")],
        b_checks=[GateCheck("b1", lambda: (True, "ok"))],
        integrity=[lambda r: (True, "ok")],
        runs_root=runs_root, archive_root=archive_root,
        runs_dir=runs_dir, attempts_dir=attempts_dir)
    deps = _dc_replace(deps, post_run_started_hook=_hook_writing_registry_record)
    out = S0Runner(deps).run()

    assert out.ok is True, out.failed_gate
    assert out.terminal_stage == RunStage.F_SEALED
    assert [e for e, _ in events] == ["RUN_STARTED", "COMPLETED"]
    assert {p.name for p in runs_dir.iterdir()} == {
        "REGISTRY_AFTER_RUN_STARTED.json", "S0_REPORT.md", "manifest.jsonl"}


def test_file_planted_during_manifest_write_fails_final_exact_set(
        tmp_path, monkeypatch):
    """THE REGRESSION FOR CODEX #3, first half of the window: a file that
    lands WHILE `_record_artifacts` is writing manifest.jsonl. The
    post_write_verify seam has already run and passed (zero extras at that
    moment), so nothing before this fix could see it."""
    runs_root, archive_root, runs_dir, attempts_dir = _tmp_output_roots(tmp_path)
    real_append = runinfra.append_manifest_record
    planted = runs_dir / "desktop.ini"

    def planting_append(path, record):
        planted.write_bytes(b"[stray sync artifact]")
        return real_append(path, record)

    monkeypatch.setattr(runinfra, "append_manifest_record", planting_append)
    deps, events, _ = make_deps(
        tmp_path, gates=[ok_gate()],
        post_write_verify=_exact_set_post_write_verify,
        runs_root=runs_root, archive_root=archive_root,
        runs_dir=runs_dir, attempts_dir=attempts_dir)
    out = S0Runner(deps).run()

    assert out.ok is False
    assert out.failure_kind == "run_failure"
    assert out.terminal_stage == RunStage.F_SEALED
    assert out.failed_gate == "final_exact_inventory"
    assert out.exposure_consumed is True
    # the registry learns FAILED, never COMPLETED
    assert [e for e, _ in events] == ["RUN_STARTED", "FAILED"]
    # nothing is deleted, and the detection is recorded on disk
    assert planted.exists()
    assert (runs_dir / "RUN_FAILURE_REPORT.md").exists()
    incident = runs_dir / f"INCIDENT_{out.incident_id}.md"
    assert "desktop.ini" in incident.read_text(encoding="utf-8")
    # a failed run never reaches the archive step
    assert out.archive_status == ""


def test_file_planted_between_chain_verify_and_completed_fails_final_exact_set(
        tmp_path, monkeypatch):
    """THE REGRESSION FOR CODEX #3, second half of the window: the plant
    happens inside Stage F, after the manifest is written and while the
    chain is being verified — i.e. on the eve of the COMPLETED append."""
    runs_root, archive_root, runs_dir, attempts_dir = _tmp_output_roots(tmp_path)
    verified: list[str] = []

    def verifying_seam(rdir, written, prepared):
        ok, detail = _exact_set_post_write_verify(rdir, written, prepared)
        verified.append(detail)
        return ok, detail

    _plant_during_chain_verify(
        monkeypatch,
        lambda: (runs_dir / "S0_REPORT.md.tmp").write_bytes(b"sync temp"))
    deps, events, _ = make_deps(
        tmp_path, gates=[ok_gate()], post_write_verify=verifying_seam,
        runs_root=runs_root, archive_root=archive_root,
        runs_dir=runs_dir, attempts_dir=attempts_dir)
    out = S0Runner(deps).run()

    # the OLD last-enumeration ran, and saw a clean directory
    assert verified and "zero extras" in verified[0]
    # the NEW one catches what the old one structurally could not
    assert out.ok is False
    assert out.failed_gate == "final_exact_inventory"
    assert out.terminal_stage == RunStage.F_SEALED
    assert [e for e, _ in events] == ["RUN_STARTED", "FAILED"]
    assert (runs_dir / "S0_REPORT.md.tmp").exists()


def test_subdirectory_planted_in_the_window_fails_final_exact_set(
        tmp_path, monkeypatch):
    """Subdirectories are extras. The enumeration is by ENTRY NAME and
    non-recursive, so a directory dropped into the run dir is surplus
    exactly like a file — the pre-existing seam analog filters on
    `p.is_file()` and would have missed this one entirely."""
    runs_root, archive_root, runs_dir, attempts_dir = _tmp_output_roots(tmp_path)
    _plant_during_chain_verify(
        monkeypatch, lambda: (runs_dir / ".sync_conflict").mkdir())
    deps, events, _ = make_deps(
        tmp_path, gates=[ok_gate()],
        post_write_verify=_exact_set_post_write_verify,
        runs_root=runs_root, archive_root=archive_root,
        runs_dir=runs_dir, attempts_dir=attempts_dir)
    out = S0Runner(deps).run()

    assert out.ok is False
    assert out.failed_gate == "final_exact_inventory"
    assert (runs_dir / ".sync_conflict").is_dir()      # nothing deleted
    incident = runs_dir / f"INCIDENT_{out.incident_id}.md"
    assert ".sync_conflict" in incident.read_text(encoding="utf-8")


def test_declared_artifact_removed_in_the_window_fails_final_exact_set(
        tmp_path, monkeypatch):
    """The proof is an EQUALITY, not a subset test: an artifact that
    DISAPPEARS after the chain verified is refused by the same statement
    that refuses a surplus one. The deletion is timed after the real
    verification returns, so this is a genuine final-exact-set catch and
    not a verify_chain failure wearing its name."""
    runs_root, archive_root, runs_dir, attempts_dir = _tmp_output_roots(tmp_path)
    _plant_during_chain_verify(
        monkeypatch, lambda: (runs_dir / "S0_REPORT.md").unlink(),
        after_verify=True)
    deps, events, _ = make_deps(
        tmp_path, gates=[ok_gate()],
        post_write_verify=_exact_set_post_write_verify,
        runs_root=runs_root, archive_root=archive_root,
        runs_dir=runs_dir, attempts_dir=attempts_dir)
    out = S0Runner(deps).run()

    assert out.ok is False
    assert out.failed_gate == "final_exact_inventory"
    assert [e for e, _ in events] == ["RUN_STARTED", "FAILED"]
    incident = runs_dir / f"INCIDENT_{out.incident_id}.md"
    assert ("S0_REPORT.md: in the set derived from this run's own writes "
            "but MISSING from the run directory at seal time"
            in incident.read_text(encoding="utf-8"))


def test_final_exact_set_runs_after_chain_verify_and_before_completed():
    """Placement pin (the fix is only a fix at this exact point): the
    proof sits after the chain verdict and strictly before the COMPLETED
    registry append."""
    source = inspect.getsource(S0Runner.run)
    idx_verify = source.index("verdict = runinfra.verify_chain_records(")
    idx_exact = source.index('"final_exact_inventory"')
    idx_completed = source.index('d.append_registry_event("COMPLETED"')
    assert idx_verify < idx_exact < idx_completed
    # ZERO WHITELIST, pinned as the exact expressions: the expectation is
    # the run's own writes and nothing else — the baseline inventory, the
    # renderer artifacts derived from the WRITTEN BYTES, and the manifest
    # read-back. A tolerated filename would have to be added here, and
    # this breaks if one is.
    assert "expected_inventory = dict(baseline_inventory)" in source
    assert "for name, data in written:" in source
    assert "sha256=_sha256_bytes(data))" in source
    assert ("expected_inventory[manifest_entry.relative_path] = "
            "manifest_entry") in source
    # and the comparison is an EQUALITY over the full inventory diff,
    # never a subset test and never a name-only set
    assert "if final_errors or inventory_diff:" in source
    # NO NAME-ONLY ENUMERATION SURVIVES ANYWHERE IN `run`: every look at
    # the run directory goes through the shared reducer. Comment lines are
    # excluded because the round-3 rationale quotes the expression it
    # replaced.
    code_only = [ln for ln in source.splitlines()
                 if not ln.lstrip().startswith("#")]
    assert [ln for ln in code_only if "iterdir" in ln] == []


# ===========================================================================
# S0 CLOSEOUT round 3 — Codex B3: the COMPLETED gate is a CONTENT+TYPE
# exact inventory, built by the SHARED reducer
# ===========================================================================
#
# THE HOLDING. Codex #3 (above) closed the window against files APPEARING
# and DISAPPEARING, by comparing top-level NAMES. That left the other half
# of the same window open, and it is the half that matters most for an
# evidentiary directory: with the name set held constant, a file's CONTENT
# could be rewritten, or the file could be replaced by a same-named
# DIRECTORY, and the run still sealed. The gate is now a full inventory —
# relative path, entry TYPE, size, SHA-256 per file — measured by
# `runinfra.build_tree_inventory`, the same reducer the archive uses.
#
# Every test below plants strictly AFTER `verify_chain_records` has
# returned its verdict, so none of them is a chain failure wearing the
# gate's name, and each one leaves the top-level NAME SET exactly as an
# honest run leaves it: on the name-only gate every single one of them
# reaches COMPLETED.


_B3_HOOK_ARTIFACT = "REGISTRY_AFTER_RUN_STARTED.json"
_B3_HONEST_NAMES = {_B3_HOOK_ARTIFACT, "S0_REPORT.md", "manifest.jsonl"}
_b3_seam_verdicts: list[str] = []


def _b3_post_write_verify(rdir, written, prepared):
    """The M6.1.7 disk seal — the check that used to be the last look at
    the run directory — wired the way a run WITH a post-RUN_STARTED hook
    must wire it: the hook's snapshot is one of the run's own writes, so
    the APPLICATION's seam declares it by NAME (`_exact_set_post_write_
    verify` above would call it an extra). That name-level tolerance is
    precisely what the round-3 gate replaces with content — and this seam
    still runs, and still returns "zero extras", in every test below."""
    declared = {name for name, _ in written} | {_B3_HOOK_ARTIFACT}
    on_disk = {p.name for p in rdir.iterdir() if p.is_file()}
    extra = on_disk - declared
    if extra:
        return False, f"disk_extra_file: {sorted(extra)}"
    for name, data in written:
        if (rdir / name).read_bytes() != data:
            return False, f"byte mismatch: {name}"
    detail = f"{len(written)} artifact(s) byte-verified, zero extras"
    _b3_seam_verdicts.append(detail)
    return True, detail


def _b3_wiring(tmp_path):
    """The honest round-3 wiring: tmp_path-derived governed roots, the
    seam above as `post_write_verify` (so the OLD last enumeration still
    runs and still passes), and the production-shaped
    `post_run_started_hook` that writes REGISTRY_AFTER_RUN_STARTED.json."""
    runs_root, archive_root, runs_dir, attempts_dir = _tmp_output_roots(tmp_path)
    _b3_seam_verdicts.clear()
    deps, events, _ = make_deps(
        tmp_path, gates=[ok_gate()],
        post_write_verify=_b3_post_write_verify,
        runs_root=runs_root, archive_root=archive_root,
        runs_dir=runs_dir, attempts_dir=attempts_dir)
    deps = _dc_replace(deps,
                       post_run_started_hook=_hook_writing_registry_record)
    return deps, events, runs_dir


def _b3_names(runs_dir: Path) -> set[str]:
    return {p.name for p in runs_dir.iterdir()}


def test_b3_honest_run_completes_and_publishes_the_verified_entry_count(
        tmp_path):
    """The honest path still COMPLETES, and the outcome CARRIES the proof
    that the final inventory ran: `final_inventory_entries` is the number
    of entries it verified by path, type, size and digest — 3 here (the
    hook's registry snapshot, the sealed report, the manifest)."""
    deps, events, runs_dir = _b3_wiring(tmp_path)
    out = S0Runner(deps).run()

    assert out.ok is True, out.failed_gate
    assert out.terminal_stage == RunStage.F_SEALED
    assert [e for e, _ in events] == ["RUN_STARTED", "COMPLETED"]
    assert _b3_names(runs_dir) == _B3_HONEST_NAMES
    assert out.final_inventory_entries == 3
    # and the archive step downstream agreed with it, over the same tree
    assert out.archive_status == "archive_ok"
    assert out.archive_report.inventory.n_files == 3


def test_b3_same_name_file_content_changed_in_the_window_fails(
        tmp_path, monkeypatch):
    """SAME NAME, SAME SIZE, DIFFERENT BYTES. The report is rewritten
    after the chain verified, to a payload of IDENTICAL LENGTH — so the
    name set matches, the byte count matches, and only the SHA-256
    diverges. Nothing but a content proof can see this."""
    deps, events, runs_dir = _b3_wiring(tmp_path)
    report = runs_dir / "S0_REPORT.md"
    forged: list[bytes] = []

    def rewrite_same_length():
        original = report.read_bytes()
        forged.append(b"X" * len(original))
        assert forged[0] != original and len(forged[0]) == len(original)
        report.write_bytes(forged[0])

    _plant_during_chain_verify(monkeypatch, rewrite_same_length,
                               after_verify=True)
    out = S0Runner(deps).run()

    # the OLD last enumeration ran, and reported a clean directory
    assert _b3_seam_verdicts == ["1 artifact(s) byte-verified, zero extras"]
    assert out.ok is False
    assert out.failure_kind == "run_failure"
    assert out.terminal_stage == RunStage.F_SEALED
    assert out.failed_gate == "final_exact_inventory"
    assert out.exposure_consumed is True
    assert out.final_inventory_entries is None      # verdict never reached
    # the registry learns FAILED, and NEVER COMPLETED
    assert [e for e, _ in events] == ["RUN_STARTED", "FAILED"]
    # the name-only gate would have passed: the name set is untouched
    assert _b3_names(runs_dir) - {"RUN_FAILURE_REPORT.md",
                                  "RUN_FAILURE_REPORT.json",
                                  f"INCIDENT_{out.incident_id}.md"} == \
        _B3_HONEST_NAMES
    incident = (runs_dir / f"INCIDENT_{out.incident_id}.md").read_text(
        encoding="utf-8")
    assert ("S0_REPORT.md: inventory mismatch against the run directory at "
            "seal time" in incident)
    assert "type=file" in incident                  # type unchanged, hash not
    # nothing was deleted or repaired
    assert report.read_bytes() == forged[0]


def test_b3_file_replaced_by_a_same_name_directory_fails(
        tmp_path, monkeypatch):
    """SAME NAME, DIFFERENT TYPE. `S0_REPORT.md` becomes a DIRECTORY after
    the chain verified. The top-level name set is bit-for-bit what an
    honest run produces; only the entry TYPE moved."""
    deps, events, runs_dir = _b3_wiring(tmp_path)

    def swap_for_directory():
        (runs_dir / "S0_REPORT.md").unlink()
        (runs_dir / "S0_REPORT.md").mkdir()

    _plant_during_chain_verify(monkeypatch, swap_for_directory,
                               after_verify=True)
    out = S0Runner(deps).run()

    assert out.ok is False
    assert out.failed_gate == "final_exact_inventory"
    assert [e for e, _ in events] == ["RUN_STARTED", "FAILED"]
    assert (runs_dir / "S0_REPORT.md").is_dir()     # nothing repaired
    incident = (runs_dir / f"INCIDENT_{out.incident_id}.md").read_text(
        encoding="utf-8")
    assert ("S0_REPORT.md: inventory mismatch against the run directory at "
            "seal time" in incident)
    assert "expected type=file" in incident
    assert "seal time type=dir" in incident


def test_b3_baseline_registry_snapshot_content_mutated_in_the_window_fails(
        tmp_path, monkeypatch):
    """THE BASELINE IS CAPTURED BY CONTENT. The post-RUN_STARTED hook's
    artifact — in production the REGISTRY_AFTER_RUN_STARTED.json snapshot,
    the record of what the registry looked like the moment exposure burned
    — is rewritten in the window. It is the one file the runner itself
    never re-derives, so before B3 the baseline knew only its NAME and this
    rewrite sealed silently."""
    deps, events, runs_dir = _b3_wiring(tmp_path)
    snapshot = runs_dir / "REGISTRY_AFTER_RUN_STARTED.json"

    _plant_during_chain_verify(
        monkeypatch,
        lambda: snapshot.write_text(
            json.dumps({"registry_sha256_after_run_started": "f" * 64},
                       indent=1, sort_keys=True),
            encoding="utf-8", newline="\n"),
        after_verify=True)
    out = S0Runner(deps).run()

    assert out.ok is False
    assert out.failed_gate == "final_exact_inventory"
    assert [e for e, _ in events] == ["RUN_STARTED", "FAILED"]
    incident = (runs_dir / f"INCIDENT_{out.incident_id}.md").read_text(
        encoding="utf-8")
    assert ("REGISTRY_AFTER_RUN_STARTED.json: inventory mismatch against "
            "the run directory at seal time" in incident)
    assert snapshot.read_text(encoding="utf-8").count("f" * 64) == 1


def test_b3_manifest_content_mutated_in_the_window_fails(
        tmp_path, monkeypatch):
    """THE MANIFEST IS COMPARED AGAINST ITS READ-BACK. manifest.jsonl is
    the one artifact whose bytes the runner never held — `_record_artifacts`
    appends it record by record — so its expectation is the read-back taken
    the instant the last record was written. The mutation lands after
    `verify_chain_records` has already returned its verdict, which is
    precisely why the chain replay cannot be the thing that catches it."""
    deps, events, runs_dir = _b3_wiring(tmp_path)
    manifest = runs_dir / "manifest.jsonl"
    verdicts: list[bool] = []
    real_verify = runinfra.verify_chain_records

    def verify_then_mutate(*args, **kwargs):
        verdict = real_verify(*args, **kwargs)
        verdicts.append(verdict.valid)
        manifest.write_bytes(manifest.read_bytes()
                             + b'{"record_type":"forged"}\n')
        return verdict

    monkeypatch.setattr(runinfra, "verify_chain_records", verify_then_mutate)
    out = S0Runner(deps).run()

    # the chain verify RAN and PASSED — the catch is the inventory's alone
    assert verdicts == [True]
    assert out.ok is False
    assert out.failed_gate == "final_exact_inventory"
    assert [e for e, _ in events] == ["RUN_STARTED", "FAILED"]
    incident = (runs_dir / f"INCIDENT_{out.incident_id}.md").read_text(
        encoding="utf-8")
    assert ("manifest.jsonl: inventory mismatch against the run directory "
            "at seal time" in incident)
    assert b'"forged"' in manifest.read_bytes()      # retained as evidence


def test_b3_manifest_expectation_is_captured_before_the_chain_verify():
    """PLACEMENT PIN for the read-back: it happens immediately after
    `_record_artifacts` returns and strictly BEFORE the chain verify. Taken
    any later, the expectation and the thing it is meant to test would be
    two reads of the same possibly-mutated file."""
    source = inspect.getsource(S0Runner.run)
    idx_record = source.index("self._record_artifacts(rdir,")
    idx_capture = source.index("manifest_bytes = (rdir / MANIFEST_NAME)"
                               ".read_bytes()")
    idx_verify = source.index("verdict = runinfra.verify_chain_records(")
    assert idx_record < idx_capture < idx_verify
    # exactly ONE read-back, and the entry is built from those bytes
    assert source.count("manifest_bytes") == 3       # read, len(), sha256()
    assert "size=len(manifest_bytes)" in source
    assert "sha256=_sha256_bytes(manifest_bytes)" in source


def test_b3_one_shared_reducer_serves_the_runner_gate_and_the_archive(
        tmp_path, monkeypatch):
    """ONE IMPLEMENTATION, proven by calls rather than by reading. Every
    inventory in a full honest run — the runner's baseline, the runner's
    final gate, and all of the archive's — is recorded here as a call to
    the SAME public `runinfra.build_tree_inventory`."""
    deps, events, runs_dir = _b3_wiring(tmp_path)
    archive_root = Path(deps.config.archive_root)
    real_reducer = runinfra.build_tree_inventory
    roots: list[Path] = []

    def recording_reducer(root):
        roots.append(Path(root))
        return real_reducer(root)

    monkeypatch.setattr(runinfra, "build_tree_inventory", recording_reducer)
    out = S0Runner(deps).run()

    assert out.ok is True, out.failed_gate
    assert out.archive_status == "archive_ok"
    # the runner side: baseline (post-RUN_STARTED) + final gate
    assert roots[:2] == [runs_dir, runs_dir]
    # the archive side, in order: source, post-copy source, staging,
    # promoted dest, post-verification source (round-3 step 6)
    assert roots[2:] == [runs_dir, runs_dir,
                         archive_root / f"{runs_dir.name}.partial",
                         archive_root / runs_dir.name, runs_dir]
    # and it is PUBLIC — the private name is gone, not aliased
    assert not hasattr(runinfra, "_build_inventory")


def test_b3_archive_source_mutated_after_final_verification_is_refused(
        tmp_path, monkeypatch):
    """(6) THE ARCHIVE WINDOW IS THE WHOLE OPERATION. The source is mutated
    AFTER the promoted destination has passed its final verification —
    step 3 (post-copy) and step 5 (post-promotion) have both already
    succeeded, so every pre-B3 proof passes and the archive would have been
    declared ok while holding bytes the sealed run no longer has.

    The mutation is injected through the reducer itself, keyed on the DEST
    inventory: that is the last step that ran before the new one."""
    src = _sealed_source(tmp_path)
    archive_root = tmp_path / "archive_root"
    dest = archive_root / src.name
    real_reducer = runinfra.build_tree_inventory

    def mutate_after_dest_inventory(root):
        result = real_reducer(root)
        if Path(root) == dest:
            (src / "S0_REPORT.md").write_bytes(b"MUTATED AFTER VERIFY\n")
        return result

    monkeypatch.setattr(runinfra, "build_tree_inventory",
                        mutate_after_dest_inventory)
    report = runinfra.archive_sealed_run(src, archive_root)

    assert report.ok is False
    assert report.status == "archive_failed"
    # every earlier proof passed; only the new one refused
    assert all(f.match for f in report.files)
    assert _archive_inventory_summary_fields(report) == (True, True, True)
    assert report.inventory.source_stable_after_verify is False
    assert any("post-verification source re-inventory" in e
               for e in report.errors)
    assert any("CHANGED during the archive window" in e
               for e in report.errors)
    # THE EVIDENCE RULE, unchanged: the promotion already happened, so the
    # destination is retained (never deleted, never repaired) and no
    # partial is left behind
    assert any("RETAINED as evidence" in e for e in report.errors)
    assert dest.is_dir()
    assert (dest / "S0_REPORT.md").read_bytes() == b"sealed report body\n"
    assert _archive_partials(archive_root) == []
    # and the sealed source is untouched by the archive itself
    assert (src / "S0_REPORT.md").read_bytes() == b"MUTATED AFTER VERIFY\n"


# ===========================================================================
# S0 CLOSEOUT — Codex final review #4: the attempts directory used to be
# created by the very gate that was refusing it
# ===========================================================================


def test_attempts_dir_inside_repo_tree_is_never_created_by_the_refusal(
        tmp_path):
    """THE REGRESSION FOR CODEX #4. `_fail_pre_run` -> `_attempt_dir` used
    to mkdir `config.attempts_dir` unconditionally — including when the
    failing gate IS `output_roots_validated`, so the refusal of an unfit
    output path created one. Here BOTH governed paths are bad: runs_root
    is inside the repo tree (the L-5 defect) and so is attempts_dir. The
    runner must refuse at the output-roots gate and create NOTHING under
    the repo, while still producing a well-formed pre-run attempt."""
    bad_runs_root = REPO / "runs"
    bad_attempts_dir = REPO / "s0_attempts_must_never_be_created"
    assert not bad_attempts_dir.exists()             # precondition
    deps, events, _ = make_deps(
        tmp_path, gates=[ok_gate()],
        runs_root=bad_runs_root,
        runs_dir=bad_runs_root / "runs" / "S0-T001",
        attempts_dir=bad_attempts_dir,
        archive_root=tmp_path / "archive_root")
    out = S0Runner(deps).run()

    # refused at the output-roots gate, pre-exposure
    assert out.ok is False
    assert out.failure_kind == "pre_run_attempt"
    assert out.failed_gate == "output_roots_validated"
    assert out.terminal_stage == RunStage.A_PRECHECK
    assert out.exposure_consumed is False
    # THE FIX: nothing was created under the repo tree — not the runs
    # root, and not the attempts directory the failure path itself wanted
    assert not bad_attempts_dir.exists()
    assert not bad_runs_root.exists()
    # still a well-formed attempt: no disk artifacts, but the outcome is
    # complete and the registry event is appended (SA-6 F-10 / F-05)
    assert out.attempts_dir is None
    assert out.incident_id.startswith("INC-")
    assert [e for e, _ in events] == ["PRE_RUN_ATTEMPT_FAILURE"]
    assert "NO_ATTEMPT_DIR" in events[0][1]
    assert out.incident_id in events[0][1]           # opaque id, no raw text


def test_attempts_dir_self_check_refuses_a_relative_path(tmp_path):
    """The self-check's other two clauses: a non-absolute (and therefore
    ambiguous) attempts path is refused before any mkdir, and the attempt
    still degrades gracefully."""
    deps, events, _ = make_deps(
        tmp_path, gates=[ok_gate()],
        attempts_dir=Path("relative_attempts_dir"),
        runs_dir=tmp_path / "runs" / "S0-T001")
    out = S0Runner(deps).run()

    assert out.failure_kind == "pre_run_attempt"
    assert out.failed_gate == "output_roots_validated"
    assert out.attempts_dir is None
    assert not Path("relative_attempts_dir").exists()
    assert [e for e, _ in events] == ["PRE_RUN_ATTEMPT_FAILURE"]


def test_attempts_dir_self_check_is_not_a_second_validate_output_roots():
    """Scope pin. The self-check is narrow BY DESIGN: it must not call
    `validate_output_roots`, because `runs_root` can be the very thing
    being reported — a failure path that can only write its evidence when
    the thing it is reporting is valid writes no evidence at all."""
    source = inspect.getsource(S0Runner._attempts_dir_self_check)
    assert "runinfra.validate_output_roots(" not in source
    assert "_package_repo_root()" in source
    # and it is consulted BEFORE any mkdir on the attempts path
    attempt_dir_src = inspect.getsource(S0Runner._attempt_dir)
    assert attempt_dir_src.index("self._attempts_dir_self_check()") < \
        attempt_dir_src.index("base.mkdir(")


def test_valid_attempts_dir_still_created_by_a_pre_run_failure(tmp_path):
    """The self-check is a self-DEFENCE, not a new refusal: a normal
    tmp_path attempts directory (disjoint from the repo, absolute) is
    still created and still receives the failure report."""
    deps, events, _ = make_deps(tmp_path, gates=[bad_gate("unrelated_gate")])
    out = S0Runner(deps).run()

    assert out.failed_gate == "unrelated_gate"
    assert out.attempts_dir is not None
    assert out.attempts_dir.is_dir()
    assert (out.attempts_dir / "PRE_RUN_ATTEMPT_FAILURE.md").exists()


# ===========================================================================
# S0 CLOSEOUT — Codex ROUND 2 #2: a root-gate refusal must be ZERO-I/O on
# EVERY configured output path, not only on the ones that look unfit
# ===========================================================================
#
# THE HOLDING. Codex #4 stopped `_attempt_dir` from creating an attempts
# path inside the repo tree, but its self-check is narrow by construction:
# absolute + disjoint from the repo. An `attempts_dir` that satisfies that
# and yet belongs to a config whose ROOTS were just refused was still
# mkdir-ed, and still received INCIDENT_*.md and the
# PRE_RUN_ATTEMPT_FAILURE report. When the FAILING gate is
# `output_roots_validated`, every governed output path is by definition
# unvalidated — the refusal must write to none of them.


def test_root_gate_refusal_writes_nothing_even_to_a_valid_looking_attempts_dir(
        tmp_path):
    """THE REGRESSION FOR CODEX ROUND-2 #2. `attempts_dir` here is exactly
    the case Codex #4's narrow self-check waves through: absolute, well
    outside the repo tree, under tmp — so before this fix it WAS created
    and WAS written into. The failing gate is the root gate, so it must
    now be left completely untouched."""
    bad_runs_root = REPO / "runs"                    # the L-5 defect
    valid_looking_attempts = tmp_path / "looks_perfectly_fine" / "A001"
    assert not valid_looking_attempts.exists()       # precondition
    deps, events, _ = make_deps(
        tmp_path, gates=[ok_gate()],
        runs_root=bad_runs_root,
        runs_dir=bad_runs_root / "runs" / "S0-T001",
        attempts_dir=valid_looking_attempts,
        archive_root=tmp_path / "archive_root")
    out = S0Runner(deps).run()

    assert out.failed_gate == "output_roots_validated"
    assert out.failure_kind == "pre_run_attempt"
    assert out.terminal_stage == RunStage.A_PRECHECK
    assert out.exposure_consumed is False
    # ZERO I/O on BOTH configured paths: not the directory, and therefore
    # not the incident file or the failure report that would live in it.
    assert not valid_looking_attempts.exists()
    assert not valid_looking_attempts.parent.exists()
    assert not bad_runs_root.exists()
    # ...while the refusal is still fully recorded
    assert out.attempts_dir is None
    assert out.incident_id.startswith("INC-")
    assert [e for e, _ in events] == ["PRE_RUN_ATTEMPT_FAILURE"]
    assert "NO_ATTEMPT_DIR" in events[0][1]
    assert out.incident_id in events[0][1]


def test_non_root_gate_stage_a_failure_still_writes_the_attempt_record(
        tmp_path):
    """THE OTHER HALF, and the reason it is safe: `allow_disk` is keyed on
    the gate NAME, so every other Stage-A gate keeps today's behaviour.
    Those failures can only be reached once the root gate has already
    PASSED (it runs first), i.e. once `attempts_dir` is root-gate
    validated — so the attempt record still lands on disk in full."""
    deps, events, _ = make_deps(
        tmp_path, gates=[bad_gate("some_other_stage_a_gate")])
    out = S0Runner(deps).run()

    assert out.failed_gate == "some_other_stage_a_gate"
    assert out.terminal_stage == RunStage.A_PRECHECK
    assert out.attempts_dir is not None and out.attempts_dir.is_dir()
    assert (out.attempts_dir / "PRE_RUN_ATTEMPT_FAILURE.md").exists()
    assert (out.attempts_dir / "PRE_RUN_ATTEMPT_FAILURE.json").exists()
    assert (out.attempts_dir / f"INCIDENT_{out.incident_id}.md").exists()
    assert [e for e, _ in events] == ["PRE_RUN_ATTEMPT_FAILURE"]
    assert "NO_ATTEMPT_DIR" not in events[0][1]


def test_a_raising_root_gate_is_also_zero_disk(tmp_path, monkeypatch):
    """Both Stage-A exits route through the same flag. A gate that RAISES
    is still a failure of that gate, so an exception out of the root gate
    must not create output paths either."""
    import itsf.s0.runner as runner_mod
    valid_looking_attempts = tmp_path / "raise_path_attempts" / "A001"
    deps, events, _ = make_deps(
        tmp_path, attempts_dir=valid_looking_attempts,
        runs_dir=tmp_path / "runs" / "S0-T001")

    def _boom(cfg):
        raise RuntimeError("synthetic root-gate explosion")

    monkeypatch.setattr(runner_mod, "_output_roots_gate_check", _boom)
    out = S0Runner(deps).run()

    assert out.failed_gate == "output_roots_validated"
    assert out.failure_kind == "pre_run_attempt"
    assert out.attempts_dir is None
    assert not valid_looking_attempts.exists()
    assert [e for e, _ in events] == ["PRE_RUN_ATTEMPT_FAILURE"]


def test_zero_disk_refusal_is_keyed_on_the_one_gate_name_constant():
    """Scope pin for the mechanism. The gate name exists ONCE, as
    `runner.OUTPUT_ROOTS_GATE_NAME`, and is what both the gate
    construction and the `allow_disk` decision read — if those two ever
    drifted apart, the refusal would quietly start writing into the paths
    it had just declared unfit."""
    import itsf.s0.runner as runner_mod
    assert runner_mod.OUTPUT_ROOTS_GATE_NAME == "output_roots_validated"
    assert (runner_mod.OUTPUT_ROOTS_OPS_GATE_NAME
            == "output_roots_operational")
    run_src = inspect.getsource(S0Runner.run)
    assert 'GateCheck(OUTPUT_ROOTS_GATE_NAME,' in run_src
    assert 'GateCheck(OUTPUT_ROOTS_OPS_GATE_NAME,' in run_src
    # R5: BOTH root gates are zero-disk on their own failure.
    assert ("allow_disk = gate.name not in (OUTPUT_ROOTS_GATE_NAME,"
            in run_src)
    # and the flag is what selects the already-graceful adir-None path
    fail_src = inspect.getsource(S0Runner._fail_pre_run)
    assert "self._attempt_dir() if allow_disk else None" in fail_src


# ===========================================================================
# S0 CLOSEOUT — Codex final review #5: archive recoverability
# ===========================================================================
#
# THE HOLDING. `archive_sealed_run` copied straight into the FINAL
# destination, so a mid-copy failure left a half-copy there — which the
# `dest.exists()` refusal then treated as a completed archive. The failure
# was permanent: every retry refused, and the only remedy was manual
# deletion. The fix builds under `<dest>.partial` and promotes by rename
# only after every file is copied AND re-verified.


def _failing_write_bytes(target_name: str, archive_root: Path,
                         flag: list[bool]):
    """A `Path.write_bytes` that raises OSError for `target_name` anywhere
    under `archive_root` while `flag[0]` is True.

    Keyed on the ARCHIVE ROOT rather than on the `.partial` name on
    purpose: the injection must be meaningful against the PRE-fix
    copy-straight-into-the-destination behaviour too, otherwise these
    tests would only be measuring their own patch predicate. The sealed
    run directory is never under `archive_root` (the two governed roots
    are disjoint by construction), so the source side is untouched."""
    real = Path.write_bytes
    root = str(archive_root)

    def patched(self, data):
        if flag[0] and self.name == target_name and str(self).startswith(root):
            raise OSError("synthetic mid-copy failure")
        return real(self, data)

    return patched


def _archive_partials(archive_root: Path) -> list[Path]:
    return ([p for p in archive_root.iterdir() if p.name.endswith(".partial")]
            if archive_root.exists() else [])


def _sealed_source(tmp_path: Path) -> Path:
    src = tmp_path / "runs_root" / "runs" / "S0-T001_20260810T000000Z"
    src.mkdir(parents=True)
    (src / "S0_REPORT.md").write_bytes(b"sealed report body\n")
    (src / "manifest.jsonl").write_bytes(b'{"a":1}\n')
    return src


def test_archive_mid_copy_failure_leaves_no_destination_and_no_partial(
        tmp_path, monkeypatch):
    """THE REGRESSION FOR CODEX #5. A mid-copy failure must leave the
    final destination ABSENT (so the next attempt is a plain retry) and
    must not leave debris behind either."""
    src = _sealed_source(tmp_path)
    archive_root = tmp_path / "archive_root"
    monkeypatch.setattr(Path, "write_bytes",
                        _failing_write_bytes("manifest.jsonl", archive_root,
                                             [True]))

    report = runinfra.archive_sealed_run(src, archive_root)

    assert report.ok is False
    assert report.status == "archive_failed"
    assert any("copy failed" in e for e in report.errors)
    # the destination of record was never created, and no partial remains
    assert not (archive_root / src.name).exists()
    assert _archive_partials(archive_root) == []
    # the sealed run directory is untouched
    assert (src / "manifest.jsonl").read_bytes() == b'{"a":1}\n'


def test_archive_retry_after_a_mid_copy_failure_succeeds(tmp_path, monkeypatch):
    """The point of the fix, stated as behaviour: the SAME call that used
    to be blocked forever by its own debris now simply succeeds on the
    second attempt."""
    src = _sealed_source(tmp_path)
    archive_root = tmp_path / "archive_root"
    flag = [True]
    monkeypatch.setattr(Path, "write_bytes",
                        _failing_write_bytes("manifest.jsonl", archive_root,
                                             flag))

    first = runinfra.archive_sealed_run(src, archive_root)
    assert first.ok is False

    flag[0] = False                                   # the transient clears
    second = runinfra.archive_sealed_run(src, archive_root)

    assert second.ok is True
    assert second.status == "archive_ok"
    assert second.errors == ()
    archived = archive_root / src.name
    for rel in ("S0_REPORT.md", "manifest.jsonl"):
        assert (archived / rel).read_bytes() == (src / rel).read_bytes()
    assert _archive_partials(archive_root) == []


def test_archive_success_promotes_and_leaves_no_partial(tmp_path):
    """A successful archive lands only at the final name."""
    src = _sealed_source(tmp_path)
    nested = src / "sub"
    nested.mkdir()
    (nested / "leaf.txt").write_bytes(b"leaf bytes")
    archive_root = tmp_path / "archive_root"

    report = runinfra.archive_sealed_run(src, archive_root)

    assert report.ok is True
    assert report.dest_dir == str(archive_root / src.name)
    assert sorted(p.name for p in archive_root.iterdir()) == [src.name]
    assert (archive_root / src.name / "sub" / "leaf.txt").read_bytes() == \
        b"leaf bytes"


def test_archive_removes_a_stale_partial_from_a_crashed_prior_attempt(
        tmp_path):
    """A `*.partial` is never the archive of record, so debris from a
    crashed process is removed rather than written into — stale files
    must not survive underneath a fresh copy."""
    src = _sealed_source(tmp_path)
    archive_root = tmp_path / "archive_root"
    stale = archive_root / f"{src.name}.partial"
    stale.mkdir(parents=True)
    (stale / "GHOST_FROM_A_CRASHED_ATTEMPT.txt").write_bytes(b"stale")

    report = runinfra.archive_sealed_run(src, archive_root)

    assert report.ok is True
    archived = archive_root / src.name
    assert not (archived / "GHOST_FROM_A_CRASHED_ATTEMPT.txt").exists()
    assert sorted(p.name for p in archived.iterdir()) == ["S0_REPORT.md",
                                                          "manifest.jsonl"]
    assert _archive_partials(archive_root) == []


def test_archive_never_overwrites_a_completed_archive(tmp_path):
    """The `dest.exists()` refusal is UNCHANGED by the partial/promote
    rework: a completed archive is never overwritten, and a second call
    cannot alter its bytes."""
    src = _sealed_source(tmp_path)
    archive_root = tmp_path / "archive_root"
    assert runinfra.archive_sealed_run(src, archive_root).ok is True
    archived_bytes = (archive_root / src.name / "S0_REPORT.md").read_bytes()

    (src / "S0_REPORT.md").write_bytes(b"DIFFERENT BYTES\n")
    again = runinfra.archive_sealed_run(src, archive_root)

    assert again.ok is False
    assert any("already exists" in e for e in again.errors)
    assert (archive_root / src.name / "S0_REPORT.md").read_bytes() == \
        archived_bytes
    assert _archive_partials(archive_root) == []


def test_archive_failure_in_the_runner_still_keeps_the_run_sealed(
        tmp_path, monkeypatch):
    """End to end through the real runner with the REAL archive function:
    a mid-copy failure is loud (`archive_failed` + errors) but never flips
    the run's verdict, and leaves no half-archive to block a retry."""
    runs_root, archive_root, runs_dir, attempts_dir = _tmp_output_roots(tmp_path)
    deps, events, _ = make_deps(
        tmp_path, gates=[ok_gate()],
        runs_root=runs_root, archive_root=archive_root,
        runs_dir=runs_dir, attempts_dir=attempts_dir)
    monkeypatch.setattr(Path, "write_bytes",
                        _failing_write_bytes("manifest.jsonl", archive_root,
                                             [True]))
    out = S0Runner(deps).run()

    assert out.ok is True                             # the run STAYS sealed
    assert out.terminal_stage == RunStage.F_SEALED
    assert out.archive_status == "archive_failed"
    assert out.archive_report.errors
    assert events[-1][0] == "COMPLETED"
    assert not (archive_root / runs_dir.name).exists()
    assert _archive_partials(archive_root) == []


# ===========================================================================
# S0 CLOSEOUT — Codex ROUND 2 #3: the archive is an EXACT-INVENTORY,
# reparse-refusing proof
# ===========================================================================
#
# THE HOLDING. The per-file recheck proves each COPIED file's bytes and
# nothing else. It cannot see (a) a symlink/junction standing in for a real
# entry, (b) the sealed source CHANGING while the archive was being built —
# a file mutated after its own recheck, while a later file was still being
# copied, passes every per-file test — (c) an EXTRA or MISSING entry in the
# staging tree, which has no per-file recheck to fail, or (d) a destination
# that diverged during/after promotion, since every prior proof was made at
# a path that no longer exists. Five inventory steps close all four.


def _make_junction(link: Path, target: Path) -> bool:
    """Create a Windows directory JUNCTION (`mklink /J`), returning True on
    success. Junctions — unlike symlinks — need no special privilege on
    this box, which is what makes the reparse-point tests REAL rather than
    monkeypatched: a junction reports `Path.is_symlink() == False` while
    carrying FILE_ATTRIBUTE_REPARSE_POINT (measured attrs 0x410), so it is
    exactly the entry the `is_symlink`-only probe would wave through."""
    if sys.platform != "win32":
        return False
    proc = subprocess.run(["cmd", "/c", "mklink", "/J", str(link),
                           str(target)], capture_output=True, text=True)
    return proc.returncode == 0 and link.exists()


def _archive_inventory_summary_fields(report):
    return (report.inventory.source_stable,
            report.inventory.staging_matches_source,
            report.inventory.dest_matches_source)


def test_archive_refuses_a_real_junction_in_the_source_tree(tmp_path):
    """(1) REPARSE REFUSAL, with a REAL Windows junction — not a mock.
    Skipped only if the OS refuses to create one at all."""
    src = _sealed_source(tmp_path)
    outside = tmp_path / "somewhere_else"
    outside.mkdir()
    (outside / "smuggled.txt").write_bytes(b"not part of the sealed run")
    # Anti-skip discipline (final_candidate_scans): a box where mklink /J
    # fails must surface LOUDLY, not silently shrink coverage.
    assert _make_junction(src / "junction", outside), (
        "directory junction creation failed (mklink /J) — reparse-refusal "
        "evidence cannot be produced on this box")
    archive_root = tmp_path / "archive_root"

    report = runinfra.archive_sealed_run(src, archive_root)

    assert report.ok is False
    assert report.status == "archive_failed"
    assert any("reparse point/junction" in e for e in report.errors)
    assert any(e.startswith("junction:") for e in report.errors)
    # refused BEFORE anything was promoted, and no debris left behind
    assert not (archive_root / src.name).exists()
    assert _archive_partials(archive_root) == []
    # and the probe really is the attribute one: a junction is NOT a symlink
    assert (src / "junction").is_symlink() is False


def test_archive_refuses_a_symlink_entry_via_a_monkeypatched_probe(
        tmp_path, monkeypatch):
    """(1) the SYMLINK half of the same refusal, tested through the probe
    rather than through a real symlink.

    HONEST ABOUT THE LIMITATION, hence the test name: creating a symlink
    on this box raises `OSError [WinError 1314] A required privilege is
    not held by the client`, so the real entry cannot be built here. What
    IS exercised is the real code path — `Path.is_symlink()` returning
    True inside `build_tree_inventory` — with only the OS probe replaced. The
    junction test above covers the other branch for real."""
    src = _sealed_source(tmp_path)
    real_is_symlink = Path.is_symlink

    def patched(self):
        if self.name == "S0_REPORT.md" and str(self).startswith(str(src)):
            return True
        return real_is_symlink(self)

    monkeypatch.setattr(Path, "is_symlink", patched)

    report = runinfra.archive_sealed_run(src, tmp_path / "archive_root")

    assert report.ok is False
    assert any("S0_REPORT.md: symlink or reparse point/junction" in e
               for e in report.errors)
    assert not (tmp_path / "archive_root" / src.name).exists()


def test_archive_refuses_a_junction_planted_in_the_staging_tree(
        tmp_path, monkeypatch):
    """(1) SAME CHECK ON STAGING ENTRIES. A junction that appears inside
    the `.partial` tree during the copy is refused there too — the staging
    inventory is built by the same `build_tree_inventory` call as the source
    one, so the refusal is structurally the same refusal."""
    src = _sealed_source(tmp_path)
    archive_root = tmp_path / "archive_root"
    outside = tmp_path / "junction_target"
    outside.mkdir()
    real_write = Path.write_bytes
    planted: list[bool] = []

    def patched(self, data):
        result = real_write(self, data)
        # after the LAST staging file is written, plant a junction next to it
        if (self.name == "manifest.jsonl"
                and str(self).startswith(str(archive_root)) and not planted):
            planted.append(_make_junction(self.parent / "sneaky", outside))
        return result

    monkeypatch.setattr(Path, "write_bytes", patched)
    report = runinfra.archive_sealed_run(src, archive_root)
    monkeypatch.undo()
    # Anti-skip discipline: same rule as the source-side junction test.
    assert planted and planted[0], (
        "directory junction creation failed (mklink /J) — staging "
        "reparse-refusal evidence cannot be produced on this box")

    assert report.ok is False
    assert any("sneaky: symlink or reparse point/junction" in e
               for e in report.errors)
    assert report.inventory.staging_matches_source is False
    assert not (archive_root / src.name).exists()
    assert _archive_partials(archive_root) == []


def test_archive_refuses_a_source_mutated_between_copy_and_reinventory(
        tmp_path, monkeypatch):
    """(3) POST-COPY SOURCE RE-INVENTORY. The mutation is timed so that
    EVERY per-file recheck still passes: `S0_REPORT.md` sorts first, so it
    is copied and rechecked, and only then — while `manifest.jsonl` is
    being written — does its source change. Before this fix the archive
    would have been declared ok while holding bytes the sealed run no
    longer had."""
    src = _sealed_source(tmp_path)
    archive_root = tmp_path / "archive_root"
    real_write = Path.write_bytes

    def patched(self, data):
        result = real_write(self, data)
        if (self.name == "manifest.jsonl"
                and str(self).startswith(str(archive_root))):
            real_write(src / "S0_REPORT.md", b"MUTATED MID-ARCHIVE\n")
        return result

    monkeypatch.setattr(Path, "write_bytes", patched)
    report = runinfra.archive_sealed_run(src, archive_root)

    assert report.ok is False
    assert report.status == "archive_failed"
    # every per-file recheck passed — this is precisely the blind spot
    assert all(f.match for f in report.files)
    assert any("CHANGED while it was being archived" in e
               for e in report.errors)
    assert any("post-copy source re-inventory" in e for e in report.errors)
    assert _archive_inventory_summary_fields(report) == (False, None, None)
    assert not (archive_root / src.name).exists()
    assert _archive_partials(archive_root) == []


def test_archive_refuses_an_extra_file_injected_into_staging(
        tmp_path, monkeypatch):
    """(4) STAGING SET-LEVEL EQUALITY. An extra file in the `.partial`
    tree has no per-file recheck to fail — only the inventory equality
    catches it."""
    src = _sealed_source(tmp_path)
    archive_root = tmp_path / "archive_root"
    real_write = Path.write_bytes

    def patched(self, data):
        result = real_write(self, data)
        if (self.name == "manifest.jsonl"
                and str(self).startswith(str(archive_root))):
            real_write(self.parent / "GHOST.txt", b"undeclared\n")
        return result

    monkeypatch.setattr(Path, "write_bytes", patched)
    report = runinfra.archive_sealed_run(src, archive_root)

    assert report.ok is False
    assert all(f.match for f in report.files)         # again: no per-file signal
    assert any("GHOST.txt: EXTRA entry in the staging (.partial) tree" in e
               for e in report.errors)
    assert _archive_inventory_summary_fields(report) == (True, False, None)
    assert not (archive_root / src.name).exists()
    assert _archive_partials(archive_root) == []


def test_archive_refuses_a_missing_file_dropped_from_staging(
        tmp_path, monkeypatch):
    """(4) the other direction of the same equality: a staging file that
    disappears after its own recheck."""
    src = _sealed_source(tmp_path)
    archive_root = tmp_path / "archive_root"
    real_write = Path.write_bytes

    def patched(self, data):
        result = real_write(self, data)
        if (self.name == "manifest.jsonl"
                and str(self).startswith(str(archive_root))):
            (self.parent / "S0_REPORT.md").unlink()
        return result

    monkeypatch.setattr(Path, "write_bytes", patched)
    report = runinfra.archive_sealed_run(src, archive_root)

    assert report.ok is False
    assert any("S0_REPORT.md: in the source inventory but MISSING from the "
               "staging (.partial) tree" in e for e in report.errors)
    assert not (archive_root / src.name).exists()


def test_archive_final_verify_mismatch_leaves_the_promoted_dest_in_place(
        tmp_path, monkeypatch):
    """(5) FINAL INVENTORY AFTER PROMOTION, and the CLEANUP ASYMMETRY.
    The corruption is injected through the promotion seam (`os.replace`),
    i.e. strictly after the staging tree was proven equal — so it is
    invisible to every earlier step. The archive must be marked failed
    WITH the mismatch listed, and the promoted directory must be RETAINED:
    it is evidence, not debris."""
    src = _sealed_source(tmp_path)
    archive_root = tmp_path / "archive_root"
    real_replace = runinfra.os.replace

    def patched(a, b):
        real_replace(a, b)
        Path(b, "S0_REPORT.md").write_bytes(b"CORRUPTED AFTER PROMOTION\n")

    monkeypatch.setattr(runinfra.os, "replace", patched)
    report = runinfra.archive_sealed_run(src, archive_root)

    assert report.ok is False
    assert report.status == "archive_failed"
    assert any("S0_REPORT.md: inventory mismatch against the promoted "
               "archive directory" in e for e in report.errors)
    assert any("RETAINED as evidence" in e for e in report.errors)
    assert _archive_inventory_summary_fields(report) == (True, True, False)
    # THE ASYMMETRY: the promoted destination is still there, corrupt bytes
    # and all, and no partial was left behind
    dest = archive_root / src.name
    assert dest.is_dir()
    assert (dest / "S0_REPORT.md").read_bytes() == \
        b"CORRUPTED AFTER PROMOTION\n"
    assert _archive_partials(archive_root) == []


def test_archive_honest_run_all_three_inventories_agree(tmp_path):
    """(2)+(3)+(4)+(5) on the happy path: an honest archive still
    succeeds, all three equality verdicts are True, the summary counts
    describe the real tree, and an EMPTY source directory is reproduced —
    the last one matters because an exact-set staging proof would refuse
    an honest run whose empty dirs the copy loop silently dropped."""
    src = _sealed_source(tmp_path)
    nested = src / "sub"
    nested.mkdir()
    (nested / "leaf.txt").write_bytes(b"leaf bytes")
    (src / "empty_dir").mkdir()
    archive_root = tmp_path / "archive_root"

    report = runinfra.archive_sealed_run(src, archive_root)

    assert report.ok is True
    assert report.status == "archive_ok"
    assert report.errors == ()
    assert _archive_inventory_summary_fields(report) == (True, True, True)
    # round-3 B3 step (6): the source was still equal to its pre-copy
    # inventory even AFTER the promoted destination had been verified
    assert report.inventory.source_stable_after_verify is True
    assert report.inventory.n_files == 3            # report, manifest, leaf
    assert report.inventory.n_dirs == 2             # sub, empty_dir
    assert report.inventory.total_bytes == sum(
        len((src / rel).read_bytes())
        for rel in ("S0_REPORT.md", "manifest.jsonl", "sub/leaf.txt"))
    dest = archive_root / src.name
    assert (dest / "empty_dir").is_dir()            # empty dir reproduced
    assert (dest / "sub" / "leaf.txt").read_bytes() == b"leaf bytes"
    # and the inventory the report summarises really is the tree on disk
    src_inv, src_errs = runinfra.build_tree_inventory(src)
    dest_inv, dest_errs = runinfra.build_tree_inventory(dest)
    assert (src_errs, dest_errs) == ([], [])
    assert src_inv == dest_inv


def test_archive_inventory_is_none_only_before_it_could_be_built(tmp_path):
    """The `inventory` field's contract: None means "never reached", not
    "empty". A destination-already-exists refusal happens before the
    source is ever inventoried; every later outcome carries a summary."""
    src = _sealed_source(tmp_path)
    archive_root = tmp_path / "archive_root"
    assert runinfra.archive_sealed_run(src, archive_root).inventory is not None

    again = runinfra.archive_sealed_run(src, archive_root)
    assert again.ok is False
    assert any("already exists" in e for e in again.errors)
    assert again.inventory is None
