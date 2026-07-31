"""M5-T3 — S0 run state machine (MAIN-AGENT OWNED; packet §7/§8/§9).

Stages A→B→C→D→E→F, strictly ordered. Exposure semantics (packet §3, Aaron
2026-07-31): Stage A/B failures are PRE_RUN_ATTEMPT_FAILUREs — logged into an
attempts/ directory, exposure NOT consumed, trial id NOT burned. The atomic
run-start (create runs/ dir + append RUN_STARTED in one controlled
transition) marks Stage C entry and consumes researcher-exposure seq 1.
Stage C+ failures burn the trial (RUN_FAILURE_REPORT; next run needs a new
Aaron-approved trial id).

Everything here is dependency-injected and synthetic-testable: no real
loader, no frozen-hash re-implementation, no research computation of its
own. The REAL wiring lives in scripts/s0_real_run.py (zero CLI arguments)
and remains inert until the trial registry event chain reaches
RUN_AUTHORIZED via Aaron's exact sentence (packet §10).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Mapping, Sequence

from itsf.contracts import RunConfig, RunGateError, RunStage, TrialState
from itsf.s0 import runinfra

STAGE_ORDER = (RunStage.A_PRECHECK, RunStage.B_LOAD_VALIDATE,
               RunStage.C_COMPUTE, RunStage.D_INTEGRITY,
               RunStage.E_REPORT, RunStage.F_SEALED)


@dataclass(frozen=True)
class GateCheck:
    """One packet-§9 hard gate: name + zero-arg callable -> (ok, detail)."""
    name: str
    check: Callable[[], tuple[bool, str]]


@dataclass(frozen=True)
class RunnerDeps:
    """Injected environment. The runner NEVER reaches outside these."""
    config: RunConfig
    trial_state: TrialState                          # from the registry chain
    gates: Sequence[GateCheck]                       # packet §9, in order
    structural_checks: Sequence[GateCheck]           # Stage B (pre-exposure)
    compute: Callable[[], object]                    # Stage C -> dataset obj
    integrity_checks: Sequence[Callable[[object], tuple[bool, str]]]
    render_report: Callable[[object], Mapping[str, str]]  # name -> content
    append_registry_event: Callable[[str, str], None]     # (event, note)
    clock_utc: Callable[[], str]                     # injected (no Date.now)
    log: Callable[[str], None]                       # guarded logger


@dataclass
class RunOutcome:
    ok: bool
    terminal_stage: RunStage
    exposure_consumed: bool
    failure_kind: str = ""                 # "" | pre_run_attempt | run_failure
    failed_gate: str = ""
    attempts_dir: Path | None = None
    runs_dir: Path | None = None
    stages_completed: tuple[str, ...] = field(default_factory=tuple)


class S0Runner:
    """Strict-order stage machine. One instance == one attempt/run."""

    def __init__(self, deps: RunnerDeps) -> None:
        self._d = deps
        self._stages_done: list[str] = []

    # -- helpers -------------------------------------------------------------

    def _attempt_dir(self) -> Path:
        base = Path(self._d.config.attempts_dir)
        base.mkdir(parents=True, exist_ok=True)      # attempts root is cheap
        return base

    def _fail_pre_run(self, stage: RunStage, gate_name: str,
                      detail: str) -> RunOutcome:
        """Packet §3: mechanical failure BEFORE exposure. Keep everything,
        burn nothing."""
        adir = self._attempt_dir()
        rendered = runinfra.render_failure_report(
            report_type="PRE_RUN_ATTEMPT_FAILURE",
            run_config=self._d.config,
            stage=stage,
            trial_state=self._d.trial_state,
            failure_reason=f"gate '{gate_name}': {detail}",
            exception_type="RunGateError",   # pre-run gate semantics
            released_information=("guarded stage logs only",),
            chain_status={"manifest": "not_started",
                          "stages_completed": tuple(self._stages_done)},
            generated_at_utc=self._d.clock_utc())
        runinfra.write_failure_report(adir, rendered)
        self._d.append_registry_event(
            "PRE_RUN_ATTEMPT_FAILURE",
            f"stage {stage.value} gate '{gate_name}': {detail} "
            f"(exposure NOT consumed; artifacts in {adir.name})")
        self._d.log(f"stage {stage.value} failed pre-run at gate {gate_name}")
        return RunOutcome(ok=False, terminal_stage=stage,
                         exposure_consumed=False,
                         failure_kind="pre_run_attempt",
                         failed_gate=gate_name, attempts_dir=adir,
                         stages_completed=tuple(self._stages_done))

    def _fail_run(self, stage: RunStage, runs_dir: Path, gate_name: str,
                  detail: str) -> RunOutcome:
        """Stage C+ failure: exposure was consumed; the trial id is burned
        (packet §8). Nothing is deleted."""
        contract_errors = {"RunGateError", "NAConservationError",
                           "AssertionMismatchError", "LogLeakError"}
        exc_type = detail.split(":", 1)[0] if ":" in detail else ""
        rendered = runinfra.render_failure_report(
            report_type="RUN_FAILURE_REPORT",
            run_config=self._d.config,
            stage=stage,
            trial_state=TrialState.FAILED,
            failure_reason=f"'{gate_name}': {detail}",
            exception_type=(exc_type if exc_type in contract_errors
                            else "Unknown"),
            released_information=("guarded stage logs only",
                                  "partial artifacts retained in runs dir"),
            chain_status={"manifest": "retained_in_runs_dir",
                          "stages_completed": tuple(self._stages_done)},
            generated_at_utc=self._d.clock_utc())
        runinfra.write_failure_report(runs_dir, rendered)
        self._d.append_registry_event(
            "FAILED",
            f"stage {stage.value} '{gate_name}': {detail} "
            f"(trial permanently consumed; outputs retained)")
        self._d.log(f"stage {stage.value} failed post-exposure")
        return RunOutcome(ok=False, terminal_stage=stage,
                         exposure_consumed=True, failure_kind="run_failure",
                         failed_gate=gate_name, runs_dir=runs_dir,
                         stages_completed=tuple(self._stages_done))

    def _atomic_run_start(self) -> Path:
        """Create runs/ dir + append RUN_STARTED as ONE controlled transition
        (packet §6). The directory must not pre-exist; nothing is ever
        deleted on failure — a half-transition is disclosed, not hidden."""
        rdir = Path(self._d.config.runs_dir)
        if rdir.exists():
            raise RunGateError(f"runs dir {rdir} already exists — STOP")
        rdir.mkdir(parents=True, exist_ok=False)
        try:
            self._d.append_registry_event(
                "RUN_STARTED",
                "Stage C entry; researcher exposure seq consumed")
        except Exception as exc:                     # noqa: BLE001
            raise RunGateError(
                f"RUN_STARTED registry append failed after dir creation; "
                f"half-transition retained for audit: {exc}") from exc
        return rdir

    # -- the machine ---------------------------------------------------------

    def run(self) -> RunOutcome:
        d = self._d

        # ---- Stage A: mechanical hard gates (packet §9) --------------------
        d.log("stage A_PRECHECK begin")
        for gate in d.gates:
            ok, detail = gate.check()
            if not ok:
                return self._fail_pre_run(RunStage.A_PRECHECK, gate.name,
                                          detail)
        self._stages_done.append(RunStage.A_PRECHECK.value)
        d.log("stage A_PRECHECK complete")

        # ---- Stage B: structural validation (still pre-exposure) -----------
        d.log("stage B_LOAD_VALIDATE begin")
        for chk in d.structural_checks:
            ok, detail = chk.check()
            if not ok:
                return self._fail_pre_run(RunStage.B_LOAD_VALIDATE, chk.name,
                                          detail)
        self._stages_done.append(RunStage.B_LOAD_VALIDATE.value)
        d.log("stage B_LOAD_VALIDATE complete")

        # ---- atomic transition into Stage C (exposure boundary) ------------
        try:
            rdir = self._atomic_run_start()
        except RunGateError as exc:
            return self._fail_pre_run(RunStage.B_LOAD_VALIDATE,
                                      "atomic_run_start", str(exc))
        d.log("RUN_STARTED; stage C_COMPUTE begin")

        # ---- Stage C: compute (zero information release) -------------------
        try:
            result = d.compute()
        except Exception as exc:                     # noqa: BLE001
            return self._fail_run(RunStage.C_COMPUTE, rdir, "compute",
                                  f"{type(exc).__name__}: {exc}")
        self._stages_done.append(RunStage.C_COMPUTE.value)
        d.log("stage C_COMPUTE complete")

        # ---- Stage D: integrity (NA conservation, assertions) --------------
        for i, chk in enumerate(d.integrity_checks):
            try:
                ok, detail = chk(result)
            except Exception as exc:                 # noqa: BLE001
                ok, detail = False, f"{type(exc).__name__}: {exc}"
            if not ok:
                return self._fail_run(RunStage.D_INTEGRITY, rdir,
                                      f"integrity[{i}]", detail)
        self._stages_done.append(RunStage.D_INTEGRITY.value)
        d.log("stage D_INTEGRITY complete")

        # ---- Stage E: sealed report ---------------------------------------
        try:
            artifacts = d.render_report(result)
            for name, content in artifacts.items():
                (rdir / name).write_text(content, encoding="utf-8")
        except Exception as exc:                     # noqa: BLE001
            return self._fail_run(RunStage.E_REPORT, rdir, "render_report",
                                  f"{type(exc).__name__}: {exc}")
        self._stages_done.append(RunStage.E_REPORT.value)
        d.log("stage E_REPORT complete")

        # ---- Stage F: seal + registry COMPLETED ---------------------------
        d.append_registry_event("COMPLETED", "S0 report sealed")
        self._stages_done.append(RunStage.F_SEALED.value)
        d.log("stage F_SEALED")
        return RunOutcome(ok=True, terminal_stage=RunStage.F_SEALED,
                          exposure_consumed=True, runs_dir=rdir,
                          stages_completed=tuple(self._stages_done))


def append_registry_event_line(registry_path: Path, trial_id: str,
                               event: str, note: str, utc: str,
                               commit: str, actor: str) -> None:
    """MAIN-AGENT owned append-only registry writer: one markdown table row
    appended; existing bytes are never rewritten."""
    line = (f"| + | {utc} | {event} | {commit} | {actor} | "
            f"[{trial_id}] {note} |\n")
    with registry_path.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(line)
