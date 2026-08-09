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

SA-6 hardening (2026-08-01), by finding id:
  F-04  every log line this module emits conforms to a runinfra whitelisted
        schema, and a logger rejection escalates to a stage failure;
  F-05  failure reports / registry notes carry error class + opaque incident
        id only; raw exception text goes to a sealed INCIDENT_*.md inside the
        attempt/run directory;
  F-06  Stage E writes each closed artifact into the append-only manifest
        hash chain and seals the stage; Stage F replays and verifies it;
  F-08  the "run directory must not pre-exist" test scans the runs root by
        trial-id prefix, and a failed RUN_STARTED append leaves a
        HALF_TRANSITION.md marker in the orphan directory;
  F-10  Stage A/B gate exceptions and directory-creation errors take the
        PRE_RUN_ATTEMPT_FAILURE path instead of escaping as tracebacks;
  F-27  the reported exception_type comes from isinstance, never from
        parsing the error text.

M6.1.6 S1 — PRE-EXPOSURE PREPARE SEAM. The lifecycle gained one step
between Stage B and the atomic run-start:

    Stage B checks all pass
      -> prepare_compute()                    (NEW; still pre-exposure)
      -> final pre-exposure registry recheck  (inside _atomic_run_start)
      -> _atomic_run_start / RUN_STARTED      (exposure consumed here)
      -> compute(prepared)                    (Stage C)

Whatever a Stage-C computation needs in order to be CONSTRUCTIBLE at all
is now built while the attempt is still cheap. A refusal raised during
prepare is a PRE_RUN_ATTEMPT_FAILURE (nothing burned); the SAME refusal
raised inside `compute` would be a RUN_FAILURE that permanently consumes
the trial id. The runner learns nothing about what the prepared object
holds — it only forwards it to Stage C.

M6.1.7 S1 — BYTE FIDELITY AT STAGE E + THE POST-WRITE VERIFICATION SEAM.

  (a) Measured defect closed. Stage E used to write each artifact with
      `path.write_text(content, encoding="utf-8")`. On Windows that opens
      the file in TEXT mode, so every `\n` in `content` became `\r\n` on
      disk: the in-memory string and the on-disk bytes were two different
      values. The runner then hashed `path.read_bytes()` (the DISK bytes)
      into the manifest chain while the renderer's own report recorded the
      IN-MEMORY digest for the same artifact — two digests for one file
      inside one sealed output. Measured at HEAD 185e47f7: 9 of the 10
      `mc_handoff_manifest.sealed_files` digests did not match the bytes
      actually on disk (only the single-line HANDOFF_ADMISSION.json,
      which contains no newline, agreed). Stage F could not see it because
      BOTH of its sides were disk-derived.

      The fix is a single source of truth: each artifact's content is
      encoded to UTF-8 EXACTLY ONCE, and that one `bytes` value is what is
      written (`write_bytes`, binary mode, no newline translation), what
      enters the hash chain, and what is handed to the verification seam.
      Nothing on this path re-reads the file to obtain a digest, so a
      second digest for one artifact can no longer be constructed.

  (b) REQUIRED post-write verification seam (`RunnerDeps.post_write_verify`)
      runs after ALL renderer artifacts are written and BEFORE Stage E
      completes — specifically before the manifest chain records them, so
      the append-only chain can never carry a digest for an artifact whose
      bytes were not first proven. It is handed the run directory, the
      written (name, bytes) pairs and the PREPARED OBJECT explicitly, as
      parameters; the runner keeps no module-level or instance-level
      temporary state for it.

      THE ASYMMETRY, stated deliberately: the WIRING of the verifier is
      checked pre-exposure (an unwired seam refuses before RUN_STARTED,
      exactly like `prepare_compute` and `pre_exposure_recheck`), but the
      VERIFICATION ITSELF can only happen after the bytes exist on disk —
      i.e. after the exposure boundary. A verification REFUSAL is therefore
      a Stage-E RUN failure: the trial id is already burned and cannot be
      given back. That is the accepted trade-off, and it is why the refusal
      path deletes nothing: every artifact, the failure report and the
      sealed incident detail are all retained for adjudication.

  (b2) `render_report` takes the prepared object too — `(result, prepared)`,
      TWO arguments, no arity shim. Stage E is post-exposure, and the
      renderer is wired at deps-construction time (before `prepare_compute`
      runs), so a one-argument renderer that needs the run's pre-exposure
      authority has no choice but to re-derive it at render time from a
      source the run's own RUN_STARTED registry append has already moved.
      Both sides of the resulting contract check then drift together and
      agree while being wrong — the same structural blindness as (a). The
      generalized rule: the prepared object is the run's PRE-EXPOSURE
      authority, and every post-exposure stage that needs it (`compute`,
      `render_report`, `post_write_verify`) takes it as an explicit
      parameter. A one-argument renderer fails loudly (TypeError -> Stage-E
      run failure) instead of being quietly accommodated.

  (c) `prepared is None` restored (the M6.1.6 `if not prepared` is
      reverted). Evaluating `not prepared` executes application-controlled
      `__bool__`/`__len__` code INSIDE the runner's gate — foreign code in
      the gate — and it also broke the runner's generality: whether a
      prepared object is *meaningful* is the application's business, not a
      generic lifecycle component's. A falsy prepared object (empty tuple,
      empty mapping, 0) is forwarded to `compute` unchanged.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Mapping, Sequence

from itsf.contracts import (AssertionMismatchError, InputDataDefectError,
                            LogLeakError, NAConservationError, RunConfig,
                            RunGateError, RunStage, TrialState)
from itsf.s0 import runinfra

STAGE_ORDER = (RunStage.A_PRECHECK, RunStage.B_LOAD_VALIDATE,
               RunStage.C_COMPUTE, RunStage.D_INTEGRITY,
               RunStage.E_REPORT, RunStage.F_SEALED)

MANIFEST_NAME = "manifest.jsonl"
HALF_TRANSITION_NAME = "HALF_TRANSITION.md"

# SA-6 F-27: the failure report's `exception_type` must come from a real
# isinstance test on the caught exception, never from parsing an error
# STRING (a compute crash whose message merely started with "LogLeakError:"
# used to be reported as a genuine log-leak abort).
_CONTRACT_ERRORS: tuple[type[BaseException], ...] = (
    RunGateError, NAConservationError, AssertionMismatchError, LogLeakError,
    InputDataDefectError)                      # SA-10 N2: IR-22 defects named


def classify_exception(exc: BaseException | None) -> str:
    """Map a caught exception onto one of the four contracts.py governance
    error names, or 'Unknown'. isinstance only — never string parsing."""
    for cls in _CONTRACT_ERRORS:
        if isinstance(exc, cls):
            return cls.__name__
    return "Unknown"


def make_incident_id(*parts: object) -> str:
    """Deterministic, opaque incident id (SA-6 F-05).

    The registry (a git-tracked file) and the failure-report body carry ONLY
    the error class plus this id; the raw exception text — which can embed
    dates, counts, prices or any other Stage-C-derived string — is written
    exclusively to the sealed detail file inside the attempt/run directory.
    """
    digest = hashlib.sha256("|".join(str(p) for p in parts).encode("utf-8"))
    return f"INC-{digest.hexdigest()[:12]}"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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
    compute: Callable[[object], object]              # Stage C(prepared) -> obj
    """M6.1.6 S1: Stage C receives the run-scoped object that
    `prepare_compute` returned, explicitly, as its single argument. The
    runner neither inspects nor stores it beyond the forwarding call."""
    integrity_checks: Sequence[Callable[[object], tuple[bool, str]]]
    render_report: Callable[[object, object], Mapping[str, str]]
    """Stage E renderer: (result, prepared) -> {artifact_name: content}.

    M6.1.7 S1 follow-up — TWO arguments, deliberately, and no compatibility
    shim. `render_report` is wired into this dataclass at CONSTRUCTION time,
    i.e. before `prepare_compute()` has run, so a renderer cannot close over
    the run's pre-exposure authority; without a parameter it has to go
    re-derive that authority itself at render time, from whatever source is
    reachable — and that source has by then been mutated by the run's own
    RUN_STARTED registry append. That is a same-source-both-sides defect of
    exactly the shape as the CRLF/two-digest bug this milestone closed: the
    check and its expectation drift together, so the error is structurally
    invisible.

    The rule this encodes is the same one `compute` and `post_write_verify`
    follow: the prepared object is the run's PRE-EXPOSURE authority, and any
    post-exposure stage that needs that authority receives it as an explicit
    parameter rather than fishing for it. A one-argument renderer is a wiring
    defect and MUST fail loudly (TypeError -> Stage-E run failure), never be
    silently tolerated by an optional second argument.

    As everywhere else, the runner learns nothing about the object: it
    forwards it, reads no attribute on it, and never evaluates its truth
    value."""
    append_registry_event: Callable[[str, str], None]     # (event, note)
    clock_utc: Callable[[], str]                     # injected (no Date.now)
    log: Callable[[str], None]
    """Guarded logger. SA-6 F-04: the caller MUST pass a logger that routes
    every message through runinfra.validate_log_event before emitting it.
    Every message this module produces is written in one of the whitelisted
    schemas (`stage=<STAGE> status=start|end|fail`, `file=<path>
    sha256=<64hex>`), so the guard is satisfiable by construction; a rejected
    message is recorded and escalated to a stage failure rather than
    swallowed."""
    # Aaron 2026-08-02 §三 registry authorization-snapshot control. Optional
    # (synthetic deps stay minimal); production wires both:
    #   pre_exposure_recheck : re-verify the registry is byte-identical to
    #     the Stage-A authorization snapshot, IMMEDIATELY before the atomic
    #     transition (blocks event-insertion between authorization and run).
    #   post_run_started_hook : record the post-append registry hash into
    #     the freshly-created runs directory.
    pre_exposure_recheck: Callable[[], tuple[bool, str]] | None = None
    post_run_started_hook: Callable[[Path], None] | None = None
    # M6.1.6 S1 §prepare seam. Called once, after every Stage-B check has
    # passed and strictly BEFORE the atomic run-start transition; returns
    # the run-scoped prepared object that Stage C is then handed. Declared
    # Optional so the dataclass stays constructible, but an UNWIRED seam is
    # FAIL-CLOSED at run time — see the refusal in `run()`, which mirrors
    # the `pre_exposure_recheck is None` precedent in `_atomic_run_start`.
    prepare_compute: Callable[[], object] | None = None
    # M6.1.7 S1 §post-write verification seam. Called ONCE per run, after
    # every renderer artifact has been written and strictly BEFORE the
    # manifest chain records any of them (so an unproven artifact never
    # enters the append-only chain) and before Stage E completes.
    #
    #     post_write_verify(runs_dir, written, prepared) -> (ok, detail)
    #
    #   runs_dir : the run directory the artifacts were written into;
    #   written  : an immutable sequence of (relative_name, bytes) pairs —
    #              the EXACT byte values that were written to disk and that
    #              are about to enter the hash chain;
    #   prepared : the run-scoped object `prepare_compute` returned, passed
    #              EXPLICITLY as a parameter (never stashed on the runner,
    #              never a module-level temporary).
    #
    # Declared Optional so the dataclass stays constructible, but an
    # UNWIRED seam is FAIL-CLOSED PRE-EXPOSURE — see the refusal in `run()`,
    # which mirrors the `prepare_compute is None` / `pre_exposure_recheck is
    # None` precedents. The wiring check is pre-exposure; the verification
    # itself is necessarily post-write, hence a Stage-E run failure (see the
    # module docstring, M6.1.7 (b)).
    post_write_verify: Callable[
        [Path, Sequence[tuple[str, bytes]], object],
        tuple[bool, str]] | None = None


@dataclass
class RunOutcome:
    ok: bool
    terminal_stage: RunStage
    exposure_consumed: bool
    failure_kind: str = ""                 # "" | pre_run_attempt | run_failure
    failed_gate: str = ""
    attempts_dir: Path | None = None
    runs_dir: Path | None = None
    incident_id: str = ""                  # opaque id; raw detail stays sealed
    stages_completed: tuple[str, ...] = field(default_factory=tuple)


class S0Runner:
    """Strict-order stage machine. One instance == one attempt/run."""

    def __init__(self, deps: RunnerDeps) -> None:
        self._d = deps
        self._stages_done: list[str] = []
        self._log_errors: list[str] = []

    # -- helpers -------------------------------------------------------------

    def _attempt_dir(self) -> Path | None:
        """Attempt root, or None if it cannot be created (SA-6 F-10: a mkdir
        failure must still produce a registry event, not a bare traceback)."""
        base = Path(self._d.config.attempts_dir)
        try:
            base.mkdir(parents=True, exist_ok=True)  # attempts root is cheap
        except OSError:
            return None
        return base

    def _safe_log(self, message: str) -> None:
        """Stage logging must never turn a governance failure into a crash;
        a guard rejection is itself recorded, not swallowed silently."""
        try:
            self._d.log(message)
        except Exception as exc:                     # noqa: BLE001
            self._log_errors.append(f"{type(exc).__name__}: {message!r}")

    def _seal_incident_detail(self, directory: Path | None, incident_id: str,
                              stage: RunStage, gate_name: str,
                              detail: str) -> bool:
        """Write the RAW failure text to a sealed detail file inside the
        attempt/run directory (SA-6 F-05). Returns True if it landed."""
        if directory is None:
            return False
        body = (f"# SEALED FAILURE DETAIL {incident_id}\n\n"
                f"trial_id: {self._d.config.trial_id}\n"
                f"stage: {stage.value}\n"
                f"gate: {gate_name}\n"
                f"generated_at_utc: {self._d.clock_utc()}\n\n"
                f"RAW DETAIL (not for the registry, not for any report body,\n"
                f"not for the console — this file stays inside the run/attempt\n"
                f"directory and is covered by the directory's retention rule):\n\n"
                f"{detail}\n")
        try:
            # M6.1.7 S1: newline="\n" — a governance file's bytes must not
            # depend on the platform the run happened on (text mode would
            # emit \r\n on Windows). Same rule as the artifact writes in
            # Stage E and as append_registry_event_line below.
            (directory / f"INCIDENT_{incident_id}.md").write_text(
                body, encoding="utf-8", newline="\n")
        except OSError:
            return False
        return True

    def _fail_pre_run(self, stage: RunStage, gate_name: str, detail: str,
                      exc: BaseException | None = None) -> RunOutcome:
        """Packet §3: mechanical failure BEFORE exposure. Keep everything,
        burn nothing. Raw detail is sealed, never surfaced (F-05)."""
        adir = self._attempt_dir()
        incident = make_incident_id(self._d.config.trial_id, stage.value,
                                    gate_name, detail, self._d.clock_utc())
        exc_type = classify_exception(exc) if exc is not None else "RunGateError"
        sealed = self._seal_incident_detail(adir, incident, stage, gate_name,
                                            detail)
        public_reason = (
            f"{exc_type} at gate '{gate_name}' (incident {incident}); raw "
            f"detail " + (f"sealed in INCIDENT_{incident}.md inside the "
                          f"attempt directory" if sealed
                          else "could NOT be sealed (attempt directory "
                               "unavailable) and is therefore withheld"))
        if adir is not None:
            try:
                rendered = runinfra.render_failure_report(
                    report_type="PRE_RUN_ATTEMPT_FAILURE",
                    run_config=self._d.config,
                    stage=stage,
                    trial_state=self._d.trial_state,
                    failure_reason=public_reason,
                    exception_type=exc_type,
                    released_information=("guarded stage logs only",),
                    chain_status={"manifest": "not_started",
                                  "stages_completed": tuple(self._stages_done)},
                    generated_at_utc=self._d.clock_utc())
                runinfra.write_failure_report(adir, rendered)
            except Exception as report_exc:          # noqa: BLE001
                self._log_errors.append(
                    f"failure-report write failed: {type(report_exc).__name__}")
        self._d.append_registry_event(
            "PRE_RUN_ATTEMPT_FAILURE",
            f"stage {stage.value} gate '{gate_name}': {exc_type} "
            f"(incident {incident}; exposure NOT consumed; artifacts in "
            f"{adir.name if adir is not None else 'NO_ATTEMPT_DIR'})")
        self._safe_log(f"stage={stage.value} status=fail")
        return RunOutcome(ok=False, terminal_stage=stage,
                         exposure_consumed=False,
                         failure_kind="pre_run_attempt",
                         failed_gate=gate_name, attempts_dir=adir,
                         incident_id=incident,
                         stages_completed=tuple(self._stages_done))

    def _fail_run(self, stage: RunStage, runs_dir: Path, gate_name: str,
                  detail: str, exc: BaseException | None = None) -> RunOutcome:
        """Stage C+ failure: exposure was consumed; the trial id is burned
        (packet §8). Nothing is deleted; raw detail is sealed (F-05) and the
        exception type comes from isinstance, not from the text (F-27)."""
        incident = make_incident_id(self._d.config.trial_id, stage.value,
                                    gate_name, detail, self._d.clock_utc())
        exc_type = classify_exception(exc)
        sealed = self._seal_incident_detail(runs_dir, incident, stage,
                                            gate_name, detail)
        public_reason = (
            f"{exc_type} at '{gate_name}' (incident {incident}); raw detail "
            + (f"sealed in INCIDENT_{incident}.md inside the run directory"
               if sealed else "could NOT be sealed and is therefore withheld"))
        rendered = runinfra.render_failure_report(
            report_type="RUN_FAILURE_REPORT",
            run_config=self._d.config,
            stage=stage,
            trial_state=TrialState.FAILED,
            failure_reason=public_reason,
            exception_type=exc_type,
            released_information=("guarded stage logs only",
                                  "partial artifacts retained in runs dir"),
            chain_status={"manifest": "retained_in_runs_dir",
                          "stages_completed": tuple(self._stages_done)},
            generated_at_utc=self._d.clock_utc())
        runinfra.write_failure_report(runs_dir, rendered)
        self._d.append_registry_event(
            "FAILED",
            f"stage {stage.value} '{gate_name}': {exc_type} "
            f"(incident {incident}; trial permanently consumed; outputs "
            f"retained)")
        self._safe_log(f"stage={stage.value} status=fail")
        return RunOutcome(ok=False, terminal_stage=stage,
                         exposure_consumed=True, failure_kind="run_failure",
                         failed_gate=gate_name, runs_dir=runs_dir,
                         incident_id=incident,
                         stages_completed=tuple(self._stages_done))

    def _atomic_run_start(self) -> Path:
        """Create runs/ dir + append RUN_STARTED as ONE controlled transition
        (packet §6). The directory must not pre-exist; nothing is ever
        deleted on failure — a half-transition is disclosed, not hidden.

        SA-6 F-08: the "must not exist" test scans the runs root for ANY
        directory belonging to this trial id, not just the exact timestamped
        name (a second-resolution stamp made the literal test vacuous), and a
        RUN_STARTED append failure leaves a HALF_TRANSITION.md marker in the
        orphan directory so it can never be mistaken for an untouched dir.
        """
        rdir = Path(self._d.config.runs_dir)
        if rdir.exists():
            raise RunGateError(f"runs dir {rdir} already exists — STOP")
        prior = sorted(p.name for p in rdir.parent.glob(
            f"{self._d.config.trial_id}*")) if rdir.parent.is_dir() else []
        if prior:
            raise RunGateError(
                f"runs root already holds {len(prior)} directory/ies for trial "
                f"{self._d.config.trial_id} ({prior[0]} ...) — STOP")
        # Aaron 2026-08-02 §三.5: immediately before the transition, re-verify
        # the registry is byte-identical to the Stage-A authorization snapshot
        # (no event may be inserted between authorization and run start).
        # SA-11 N-E: an UNWIRED recheck is fail-closed, not fail-open — the
        # synthetic deps must inject an explicit passing recheck.
        if self._d.pre_exposure_recheck is None:
            raise RunGateError(
                "no pre-exposure registry recheck wired — fail closed "
                "(Aaron §三.5)")
        ok, why = self._d.pre_exposure_recheck()
        if not ok:
            raise RunGateError(
                f"pre-exposure registry recheck failed: {why} — STOP")
        rdir.mkdir(parents=True, exist_ok=False)
        try:
            self._d.append_registry_event(
                "RUN_STARTED",
                "Stage C entry; researcher exposure seq consumed")
        except Exception as exc:                     # noqa: BLE001
            marker = (
                "# HALF_TRANSITION\n\n"
                f"trial_id: {self._d.config.trial_id}\n"
                f"generated_at_utc: {self._d.clock_utc()}\n\n"
                "The run directory was created but the paired RUN_STARTED "
                "registry event could NOT be appended, so the atomic Stage-C\n"
                "entry transition did not complete. This directory is an "
                "ORPHAN: it is retained (never deleted) and must not be\n"
                "treated as a started run. Exposure status is indeterminate "
                "until Aaron adjudicates; see the registry chain.\n"
                f"registry append error class: {type(exc).__name__}\n")
            try:
                (rdir / HALF_TRANSITION_NAME).write_text(
                    marker, encoding="utf-8", newline="\n")   # M6.1.7 S1
            except OSError:
                pass
            raise RunGateError(
                f"RUN_STARTED registry append failed after dir creation; "
                f"half-transition disclosed in {HALF_TRANSITION_NAME}: "
                f"{type(exc).__name__}") from exc
        return rdir

    # -- Stage E/F manifest chain (packet §6; SA-6 F-06) ---------------------

    def _chain_tail(self, manifest: Path) -> str:
        if not manifest.exists():
            return runinfra.GENESIS_PREVIOUS_HASH
        last = None
        for line in manifest.read_text(encoding="utf-8").splitlines():
            if line.strip():
                last = line
        if last is None:
            return runinfra.GENESIS_PREVIOUS_HASH
        return json.loads(last)["record_hash"]

    def _append_chain_record(self, manifest: Path,
                             payload: dict[str, object]) -> str:
        canonical = runinfra.canonicalize_manifest_record(
            payload, manifest_relative_path=manifest.name)
        record_hash = runinfra.compute_record_hash(canonical)
        runinfra.append_manifest_record(
            manifest, {**payload, "record_hash": record_hash,
                       "finalized": True})
        return record_hash

    def _record_artifacts(self, runs_dir: Path, stage: RunStage,
                          written: Sequence[tuple[str, bytes]]) -> None:
        """One `file` record per closed artifact + the stage seal.

        M6.1.7 S1: `written` carries the EXACT byte values that were written
        to disk (see Stage E). The chain hashes those values directly — it
        never re-reads the files — so the digest in the manifest and the
        digest of the bytes on disk are the same number by construction,
        not by coincidence. Stage F then re-derives the same digest from
        disk, which is a genuine cross-check precisely because the write
        path performs no translation of any kind.
        """
        manifest = runs_dir / MANIFEST_NAME
        tail = self._chain_tail(manifest)
        for name, data in written:
            tail = self._append_chain_record(manifest, {
                "record_type": "file",
                "stage": stage.value,
                "relative_path": name,
                "file_sha256": _sha256_bytes(data),
                "previous_record_hash": tail})
            self._safe_log(f"file={name} sha256={_sha256_bytes(data)}")
        self._append_chain_record(manifest, {
            "record_type": "stage_seal",
            "stage": stage.value,
            "sealed_record_hash": tail,
            "previous_record_hash": tail})

    # -- the machine ---------------------------------------------------------

    def _log_guard_breach(self) -> str:
        """Any message the injected guarded logger REJECTED is itself a
        governance stop condition (packet §7 Stage-C log guard)."""
        return "; ".join(self._log_errors)

    def run(self) -> RunOutcome:
        d = self._d

        # ---- Stage A: mechanical hard gates (packet §9) --------------------
        # SA-6 F-10: a gate that RAISES is a gate that failed — it must take
        # the PRE_RUN_ATTEMPT_FAILURE path (report + registry event), never
        # escape as a bare traceback with no record of the attempt.
        self._safe_log(f"stage={RunStage.A_PRECHECK.value} status=start")
        for gate in d.gates:
            try:
                ok, detail = gate.check()
            except Exception as exc:                 # noqa: BLE001
                return self._fail_pre_run(
                    RunStage.A_PRECHECK, gate.name,
                    f"gate raised {type(exc).__name__}: {exc}", exc)
            if not ok:
                return self._fail_pre_run(RunStage.A_PRECHECK, gate.name,
                                          detail)
        if self._log_errors:
            return self._fail_pre_run(RunStage.A_PRECHECK, "log_guard",
                                      self._log_guard_breach(), LogLeakError())
        self._stages_done.append(RunStage.A_PRECHECK.value)
        self._safe_log(f"stage={RunStage.A_PRECHECK.value} status=end")

        # ---- Stage B: structural validation (still pre-exposure) -----------
        self._safe_log(f"stage={RunStage.B_LOAD_VALIDATE.value} status=start")
        for chk in d.structural_checks:
            try:
                ok, detail = chk.check()
            except Exception as exc:                 # noqa: BLE001
                return self._fail_pre_run(
                    RunStage.B_LOAD_VALIDATE, chk.name,
                    f"check raised {type(exc).__name__}: {exc}", exc)
            if not ok:
                return self._fail_pre_run(RunStage.B_LOAD_VALIDATE, chk.name,
                                          detail)
        if self._log_errors:
            return self._fail_pre_run(RunStage.B_LOAD_VALIDATE, "log_guard",
                                      self._log_guard_breach(), LogLeakError())
        self._stages_done.append(RunStage.B_LOAD_VALIDATE.value)
        self._safe_log(f"stage={RunStage.B_LOAD_VALIDATE.value} status=end")

        # ---- pre-exposure PREPARE seam (M6.1.6 S1) -------------------------
        # Last cheap step before the exposure boundary: build the run-scoped
        # object Stage C will need. Anything that can REFUSE — an unresolved
        # configuration, an unconstructible input — must refuse HERE, where
        # the failure is a PRE_RUN_ATTEMPT_FAILURE, instead of inside
        # `compute`, where the identical refusal would route to `_fail_run`
        # and permanently burn the trial id.
        #
        # Two invariants the ordering below encodes: prepare runs BEFORE the
        # final registry recheck (which lives inside `_atomic_run_start`, so
        # the recheck stays the LAST thing that happens before the
        # transition), and the prepared object is a plain local — never a
        # module-level or class-level cache — so two runner instances can
        # never share one.
        #
        # FAIL-CLOSED WHEN UNWIRED. This mirrors the pre-exposure
        # registry-recheck precedent in `_atomic_run_start` (the
        # `pre_exposure_recheck is None` branch, Aaron §三.5 / SA-11 N-E): a
        # deps object with no prepare seam refuses pre-exposure rather than
        # silently skipping ahead to compute. A prepare that returns nothing
        # is treated the same way — Stage C must be handed a real object.
        if d.prepare_compute is None:
            return self._fail_pre_run(
                RunStage.B_LOAD_VALIDATE, "prepare_compute",
                "no pre-exposure prepare seam wired — fail closed (mirrors "
                "the pre-exposure registry recheck at _atomic_run_start)",
                RunGateError())
        # M6.1.7 S1: the post-write verification seam is REQUIRED, and its
        # WIRING is checked here — pre-exposure, alongside the two seams it
        # is modelled on (`prepare_compute` above, `pre_exposure_recheck` in
        # `_atomic_run_start`). A deps object with no verifier must never
        # reach RUN_STARTED, because a run that cannot prove its own output
        # bytes is not worth the trial id it would consume.
        #
        # ASYMMETRY, deliberately accepted (module docstring M6.1.7 (b)):
        # only the WIRING can be checked before exposure. The verification
        # itself needs bytes on disk, so it necessarily runs post-write —
        # and a verification REFUSAL is therefore a Stage-E RUN failure with
        # the trial id already burned, not a free pre-run attempt. That is
        # why the refusal path retains every artifact.
        if d.post_write_verify is None:
            return self._fail_pre_run(
                RunStage.B_LOAD_VALIDATE, "post_write_verify",
                "no post-write verification seam wired — fail closed "
                "(mirrors the pre-exposure prepare seam and registry "
                "recheck; only the WIRING is checkable pre-exposure)",
                RunGateError())
        try:
            prepared = d.prepare_compute()
        except Exception as exc:                     # noqa: BLE001
            return self._fail_pre_run(
                RunStage.B_LOAD_VALIDATE, "prepare_compute",
                f"prepare raised {type(exc).__name__}: {exc}", exc)
        # M6.1.7 S1 — `is None`, NOT `not prepared` (the M6.1.6 A1-1 change
        # is reverted). Two reasons, both structural:
        #   1. `not prepared` executes application-controlled __bool__ /
        #      __len__ code INSIDE the runner's gate. Foreign code in the
        #      gate is precisely the class of defect this project has been
        #      burned by before; an object whose __bool__ raises would take
        #      down the lifecycle from inside a governance check.
        #   2. It breaks this component's generality. S0Runner is a generic
        #      lifecycle machine: "was an object produced?" is its question,
        #      "is that object MEANINGFUL?" is the application's. A falsy
        #      prepared object — an empty tuple, an empty mapping, 0 — is a
        #      legitimate prepared object and is forwarded to `compute`
        #      unchanged. An application that wants emptiness to be a
        #      refusal raises inside its own `prepare_compute`.
        if prepared is None:
            return self._fail_pre_run(
                RunStage.B_LOAD_VALIDATE, "prepare_compute",
                "prepare returned no prepared object (None) — fail closed",
                RunGateError())

        # ---- atomic transition into Stage C (exposure boundary) ------------
        try:
            rdir = self._atomic_run_start()
        except RunGateError as exc:
            return self._fail_pre_run(RunStage.B_LOAD_VALIDATE,
                                      "atomic_run_start", str(exc), exc)
        except OSError as exc:                       # mkdir refused (F-10)
            return self._fail_pre_run(
                RunStage.B_LOAD_VALIDATE, "atomic_run_start",
                f"run directory could not be created: {type(exc).__name__}: "
                f"{exc}", exc)
        # SA-11 N-D: RUN_STARTED has been appended — exposure IS consumed.
        # A §三.6 post-hook failure is therefore a RUN failure (trial burned,
        # outputs retained), never a pre-run attempt.
        if d.post_run_started_hook is not None:
            try:
                d.post_run_started_hook(rdir)
            except Exception as exc:                 # noqa: BLE001
                return self._fail_run(
                    RunStage.C_COMPUTE, rdir, "post_run_started_hook",
                    f"registry-hash record failed after RUN_STARTED: "
                    f"{type(exc).__name__}: {exc}", exc)
        self._safe_log(f"stage={RunStage.C_COMPUTE.value} status=start")

        # ---- Stage C: compute (zero information release) -------------------
        # The prepared object built pre-exposure is handed over explicitly;
        # Stage C never calls back into the prepare seam.
        try:
            result = d.compute(prepared)
        except Exception as exc:                     # noqa: BLE001
            return self._fail_run(RunStage.C_COMPUTE, rdir, "compute",
                                  f"{type(exc).__name__}: {exc}", exc)
        self._stages_done.append(RunStage.C_COMPUTE.value)
        self._safe_log(f"stage={RunStage.C_COMPUTE.value} status=end")
        if self._log_errors:
            return self._fail_run(RunStage.C_COMPUTE, rdir, "log_guard",
                                  self._log_guard_breach(), LogLeakError())

        # ---- Stage D: integrity (NA conservation, assertions) --------------
        self._safe_log(f"stage={RunStage.D_INTEGRITY.value} status=start")
        for i, chk in enumerate(d.integrity_checks):
            caught: BaseException | None = None
            try:
                ok, detail = chk(result)
            except Exception as exc:                 # noqa: BLE001
                ok, detail, caught = False, f"{type(exc).__name__}: {exc}", exc
            if not ok:
                return self._fail_run(RunStage.D_INTEGRITY, rdir,
                                      f"integrity[{i}]", detail, caught)
        self._stages_done.append(RunStage.D_INTEGRITY.value)
        self._safe_log(f"stage={RunStage.D_INTEGRITY.value} status=end")

        # ---- Stage E: sealed report + manifest chain (packet §6) -----------
        self._safe_log(f"stage={RunStage.E_REPORT.value} status=start")
        written: list[tuple[str, bytes]] = []
        try:
            # M6.1.7 S1 follow-up: the renderer receives the run-scoped
            # prepared object EXPLICITLY, as its second argument — the same
            # rule as `compute(prepared)` and `post_write_verify(...,
            # prepared)`. A one-arg renderer raises TypeError here and takes
            # the Stage-E run-failure path; there is no arity shim, because
            # an optional second argument would let a one-arg renderer go on
            # silently re-deriving the run's authority from a source this
            # run has already mutated.
            artifacts = d.render_report(result, prepared)
            if not artifacts:
                raise RunGateError(
                    "render_report produced no artifacts; a sealed S0 report "
                    "is mandatory at Stage E")
            for name, content in artifacts.items():
                # M6.1.7 S1 — ONE encode, ONE byte value. `data` is the only
                # representation of this artifact that exists downstream: it
                # is written verbatim in BINARY mode (write_bytes performs no
                # newline translation, so a '\n' stays 0x0A on every
                # platform), it is what `_record_artifacts` hashes into the
                # chain, and it is what the verification seam is handed.
                # Nothing here re-reads the file to obtain a digest, so the
                # disk bytes and the recorded digest cannot diverge.
                data = content.encode("utf-8")
                (rdir / name).write_bytes(data)
                written.append((name, data))
        except Exception as exc:                     # noqa: BLE001
            return self._fail_run(RunStage.E_REPORT, rdir, "render_report",
                                  f"{type(exc).__name__}: {exc}", exc)

        # ---- REQUIRED post-write verification seam (M6.1.7 S1) -------------
        # Every renderer artifact is now closed on disk, and NOTHING has
        # entered the manifest chain yet. The verifier is handed the run
        # directory, the exact byte values that were written, and the
        # prepared object — explicitly, as parameters. Running it here (not
        # after `_record_artifacts`) means the append-only chain can never
        # carry a digest for an artifact whose bytes were not first proven.
        #
        # Exposure is ALREADY consumed at this point (see the asymmetry note
        # at the pre-exposure wiring check): a refusal is a Stage-E RUN
        # failure that burns the trial id. Nothing is deleted or rewritten on
        # that path — the artifacts stay, `_fail_run` seals the raw detail in
        # INCIDENT_*.md and writes RUN_FAILURE_REPORT.{md,json} into the run
        # directory, so the discrepancy can be adjudicated from the evidence.
        try:
            verified, verify_detail = d.post_write_verify(
                rdir, tuple(written), prepared)
        except Exception as exc:                     # noqa: BLE001
            return self._fail_run(
                RunStage.E_REPORT, rdir, "post_write_verify",
                f"post-write verification raised {type(exc).__name__}: {exc}",
                exc)
        if not verified:
            return self._fail_run(
                RunStage.E_REPORT, rdir, "post_write_verify",
                f"post-write verification refused: {verify_detail}",
                RunGateError())

        # every closed, VERIFIED artifact enters the append-only hash chain,
        # then the stage seal closes E (SA-6 F-06 / packet §6)
        try:
            self._record_artifacts(rdir, RunStage.E_REPORT, written)
        except Exception as exc:                     # noqa: BLE001
            return self._fail_run(RunStage.E_REPORT, rdir, "render_report",
                                  f"{type(exc).__name__}: {exc}", exc)
        self._stages_done.append(RunStage.E_REPORT.value)
        self._safe_log(f"stage={RunStage.E_REPORT.value} status=end")

        # ---- Stage F: verify the chain, then registry COMPLETED -----------
        self._safe_log(f"stage={RunStage.F_SEALED.value} status=start")
        try:
            manifest = rdir / MANIFEST_NAME
            records = [json.loads(ln) for ln
                       in manifest.read_text(encoding="utf-8").splitlines()
                       if ln.strip()]
            verdict = runinfra.verify_chain_records(
                records, manifest_relative_path=MANIFEST_NAME,
                file_hash_provider=lambda rel: _sha256_bytes(
                    (rdir / rel).read_bytes()))
        except Exception as exc:                     # noqa: BLE001
            return self._fail_run(RunStage.F_SEALED, rdir, "verify_chain",
                                  f"{type(exc).__name__}: {exc}", exc)
        if not verdict.valid:
            return self._fail_run(
                RunStage.F_SEALED, rdir, "verify_chain",
                "manifest chain invalid: " + "; ".join(verdict.errors),
                RunGateError())
        if self._log_errors:
            return self._fail_run(RunStage.F_SEALED, rdir, "log_guard",
                                  self._log_guard_breach(), LogLeakError())
        d.append_registry_event("COMPLETED", "S0 report sealed")
        self._stages_done.append(RunStage.F_SEALED.value)
        self._safe_log(f"stage={RunStage.F_SEALED.value} status=end")
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
