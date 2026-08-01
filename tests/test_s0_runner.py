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
import json
import subprocess
import sys
from pathlib import Path

import pytest

from itsf.contracts import (NAConservationError, RunConfig, RunGateError,
                            RunStage, TrialState)
from itsf.s0 import runinfra
from itsf.s0.runner import (
    GateCheck,
    RunnerDeps,
    S0Runner,
    append_registry_event_line,
    classify_exception,
)

CLOCK = "2026-07-31T12:00:00+00:00"
REPO = Path(__file__).resolve().parents[1]

_SCRIPT_CACHE: dict[str, object] = {}


def real_run_module():
    """Import scripts/s0_real_run.py once. Import MUST stay inert."""
    if "mod" not in _SCRIPT_CACHE:
        script = REPO / "scripts" / "s0_real_run.py"
        spec = importlib.util.spec_from_file_location("s0_real_run", script)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _SCRIPT_CACHE["mod"] = mod
    return _SCRIPT_CACHE["mod"]


def make_deps(tmp_path: Path, *, gates=(), b_checks=(),
              compute=None, integrity=(), renderer=None,
              registry_events=None, log=None, append_event=None,
              runs_dir=None):
    cfg = RunConfig(trial_id="S0-T001",
                    authorized_commit="a" * 40,
                    seed=20260731,
                    attempts_dir=str(tmp_path / "attempts" / "A001"),
                    runs_dir=str(runs_dir or (tmp_path / "runs" / "S0-T001")),
                    assertions_path=str(tmp_path / "assertions.json"))
    events = registry_events if registry_events is not None else []

    def default_append(ev, note):
        events.append((ev, note))

    logs: list[str] = []
    deps = RunnerDeps(
        config=cfg,
        trial_state=TrialState.RUN_AUTHORIZED,
        gates=tuple(gates),
        structural_checks=tuple(b_checks),
        compute=compute or (lambda: {"sentinel": True}),
        integrity_checks=tuple(integrity),
        render_report=renderer or (lambda r: {"S0_REPORT.md": "sealed"}),
        append_registry_event=append_event or default_append,
        clock_utc=lambda: CLOCK,
        log=log if log is not None else logs.append,
        # SA-11 N-E: an unwired recheck is now FAIL-CLOSED in the runner, so
        # the synthetic harness injects an explicit passing recheck.
        pre_exposure_recheck=lambda: (True, "synthetic recheck"),
        post_run_started_hook=None)
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
        renderer=lambda r: {"S0_REPORT.md": "sealed", "counts.md": "n=1"})
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
    deps, _, _ = make_deps(tmp_path, gates=[ok_gate()], renderer=lambda r: {})
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

    # Layout B — exactly one live authorization for this HEAD.
    reg_b = tmp_path / "TRIAL_REGISTRY.md"
    n_supersedes = real.count("RUN_AUTHORIZATION_SUPERSEDED")
    text_b = real + _auth_row(90 + n_supersedes, head)
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
    assert mod.MIN_COLLECTED_TESTS == 519


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
    # with the real probe the gate reports readiness (artifacts on disk)
    wired = mod.build_structural_checks(
        REPO / "S0_INPUT_PREFLIGHT.json",
        wiring_status=mod.RealChain().ready)
    g2 = {c.name: c for c in wired}["stage_c_wiring_activated"]
    ok2, detail2 = g2.check()
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
    assert "render_s0_report" in source
    assert "build_structural_checks" in source


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
    mod = real_run_module()
    ds, uni = _synthetic_dataset()
    actuals = mod.structural_actuals_from(ds, uni)

    sink: list[str] = []
    deps, events, _ = make_deps(
        tmp_path,
        gates=[ok_gate("g1")],
        b_checks=mod.build_structural_checks(
            _touch_json(tmp_path / "assertions.json"),
            expected_loader=lambda p: dict(actuals),   # expected == actual
            actuals_provider=lambda: mod.structural_actuals_from(ds, uni),
            wiring_status=lambda: (True, "synthetic wiring ready")),
        compute=lambda: mod.stage_c_result(ds),
        integrity=mod.build_integrity_checks(),
        renderer=mod.render_s0_report,
        log=guarded_logger(sink))
    out = S0Runner(deps).run()
    assert out.ok is True, out
    assert out.stages_completed[-1] == "F_SEALED"

    # (1) exposure consumed exactly at Stage C entry
    assert [e for e, _ in events][0] == "RUN_STARTED"
    assert out.exposure_consumed is True

    # (2) no research number in any intermediate log line: every line passed
    # the guard (guarded_logger raises otherwise) - and none mentions a
    # frequency/base-rate style token
    assert sink, "guarded logger saw no traffic - guard not on the wire"

    # (3) NA conservation ran itemized over the synthetic dataset
    # (build_integrity_checks raises NAConservationError on violation;
    # reaching F_SEALED proves it passed on real per-column adapters)
    adapters = mod.stage_c_result(ds)
    assert adapters["na_reason_counts"] and adapters["reported_total_na"]

    # (4) manifest chain sealed per stage in the runs dir (SA-10 N9: exact
    # filename, hard assertion — no case-insensitivity crutch)
    manifest = Path(deps.config.runs_dir) / "manifest.jsonl"
    assert manifest.exists()
    lines = [json.loads(x) for x in manifest.read_text("utf-8").splitlines()]
    assert any(r.get("record_type") == "stage_seal" for r in lines)

    # (5) the complete report is released only at Stage E, as whole files
    report = json.loads((Path(deps.config.runs_dir) / "S0_REPORT.json")
                        .read_text("utf-8"))
    assert report["funnel"] and report["f10_final_mutually_exclusive"]
    assert report["y6_rule"] == ds.y6_rule
    # frequency structure is INSIDE the sealed report, never in logs
    assert "overall" in report["frequency"]


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
    the post-append registry hash and the Stage-A snapshot."""
    import hashlib as _h
    mod = real_run_module()
    commit = "c" * 40
    reg = _authorized_registry(tmp_path, commit)
    monkeypatch.setattr(mod, "REGISTRY", reg)
    chain = mod.RealChain()
    assert chain.authorization_snapshot() == chain.authorization_snapshot()
    attempts = tmp_path / "attempts"
    gate, recheck, hook = mod.make_snapshot_control(chain, attempts)

    ok, why = recheck()                       # before the gate: fail closed
    assert ok is False and "no Stage-A" in why

    ok, _ = gate()                            # (i) gate side-effects
    assert ok is True
    snap = json.loads(
        (attempts / "AUTHORIZATION_SNAPSHOT.json").read_text("utf-8"))
    assert snap["authorized_commit"] == commit

    ok, _ = recheck()                         # (ii) unchanged -> pass
    assert ok is True

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
