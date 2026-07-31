"""M5-T3 runner state-machine tests (synthetic; main-agent authored).

No real data, no research computation: `compute` returns a sentinel object.
Covers packet §3 exposure boundary, §6 atomic run-start, §7 stage order,
§8 failure semantics and the append-only registry writer.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from itsf.contracts import RunConfig, RunStage, TrialState
from itsf.s0.runner import (
    GateCheck,
    RunnerDeps,
    S0Runner,
    append_registry_event_line,
)

CLOCK = "2026-07-31T12:00:00+00:00"


def make_deps(tmp_path: Path, *, gates=(), b_checks=(),
              compute=None, integrity=(), renderer=None,
              registry_events=None):
    cfg = RunConfig(trial_id="S0-T001",
                    authorized_commit="a" * 40,
                    seed=20260731,
                    attempts_dir=str(tmp_path / "attempts" / "A001"),
                    runs_dir=str(tmp_path / "runs" / "S0-T001"),
                    assertions_path=str(tmp_path / "assertions.json"))
    events = registry_events if registry_events is not None else []
    logs: list[str] = []
    deps = RunnerDeps(
        config=cfg,
        trial_state=TrialState.RUN_AUTHORIZED,
        gates=tuple(gates),
        structural_checks=tuple(b_checks),
        compute=compute or (lambda: {"sentinel": True}),
        integrity_checks=tuple(integrity),
        render_report=renderer or (lambda r: {"S0_REPORT.md": "sealed"}),
        append_registry_event=lambda ev, note: events.append((ev, note)),
        clock_utc=lambda: CLOCK,
        log=logs.append)
    return deps, events, logs


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
    # Stage C log lines are stage/heartbeat text only (guarded upstream)
    assert any("C_COMPUTE begin" in ln for ln in logs)


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
    import importlib.util
    from pathlib import Path as _P
    script = (_P(__file__).resolve().parents[1] / "scripts"
              / "s0_real_run.py")
    spec = importlib.util.spec_from_file_location("s0_real_run", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)                     # import must be inert
    import inspect
    assert inspect.signature(mod.main).parameters == {}
    assert getattr(mod, "USES_ARGPARSE", False) is False
