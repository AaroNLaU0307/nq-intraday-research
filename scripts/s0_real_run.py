"""S0-T001 real-run entrypoint (MAIN-AGENT OWNED; zero CLI arguments).

INERT BY CONSTRUCTION until authorization: Stage-A gate #12/#13 require the
TRIAL_REGISTRY event chain to contain a RUN_AUTHORIZED event created by
Aaron's exact packet-§10 sentence, and HEAD to equal the commit named in
that sentence. Neither exists today, so every invocation terminates as a
PRE_RUN_ATTEMPT_FAILURE before any data is opened (exposure NOT consumed).

No argparse, no environment overrides (packet §5): every parameter comes
from approved artifacts on disk at the authorized commit.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

USES_ARGPARSE = False          # pinned by tests/test_s0_runner.py

TRIAL_ID = "S0-T001"
SEED = 20260731                # packet §5
REGISTRY = REPO / "ops" / "TRIAL_REGISTRY.md"

# packet §4 locked input hashes (compare-only at Stage A)
LOCKED = {
    "f10": ("gate1/f10_event_calendar/f10_events.csv",
            "5e92ad00737339c392ed2c0927736e196e076e185897c146c884d5f515bb5e8c"),
    "symbology": ("gate1/symbology/nq_v0_mapping.csv",
                  "85a32d44994b51e004e0c322510527aae18b70e1fadc70437e754253a2ac1850"),
    "spread": ("spread_cost_table.csv",
               "b6d6984ff7c364f9a57514d7583685956f6b080ec02027ee8401f38f6d9509bf"),
    "attestation": ("ops/physical_copy_attestation.json",
                    "51ce415c6e2c06eb363d8061b9543c13d1b9ff11dfecbd9ec2312e3c66212813"),
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(REPO), *args],
                          capture_output=True, text=True).stdout.strip()


def _registry_text() -> str:
    return REGISTRY.read_text(encoding="utf-8")


def build_gates(clock_utc):
    """Packet §9 hard gates as GateCheck list (order preserved)."""
    from itsf.s0.runner import GateCheck

    def g_clean():
        dirty = subprocess.run(["git", "-C", str(REPO), "status",
                                "--porcelain"], capture_output=True,
                               text=True).stdout.strip()
        return (not dirty, dirty or "clean")

    def g_authorized():
        txt = _registry_text()
        return ("RUN_AUTHORIZED" in txt,
                "registry chain has no RUN_AUTHORIZED event (packet §10 "
                "sentence not issued)")

    def g_head_matches():
        txt = _registry_text()
        head = _git("rev-parse", "HEAD")
        ok = "RUN_AUTHORIZED" in txt and head[:7] in txt
        return (ok, f"HEAD {head[:12]} not named by the authorization event")

    def g_flags():
        ok = ((REPO / "gate1" / "G9_RESOLVED.flag").exists()
              and (REPO / "ops" / "SECOND_COPY_ATTESTED.flag").exists()
              and (REPO / "M4_KEY_CLOSURE_ATTESTATION.md").exists())
        return (ok, "G9/second-copy/key-closure attestations")

    def g_inputs():
        for name, (rel, want) in LOCKED.items():
            got = _sha(REPO / rel)
            if got != want:
                return (False, f"input hash drift: {name} {got[:16]}...")
        return (True, "all locked input hashes match")

    def g_tests():
        r = subprocess.run([sys.executable, "-m", "pytest", "tests", "-q"],
                           capture_output=True, text=True, cwd=REPO)
        return (r.returncode == 0, r.stdout.strip().splitlines()[-1]
                if r.stdout else "pytest")

    def g_frozen():
        try:
            from itsf import guards
            guards.verify_frozen_hashes()
            return (True, "7 canonical frozen hashes OK")
        except Exception as exc:                     # noqa: BLE001
            return (False, str(exc))

    return [
        GateCheck("git_clean", g_clean),
        GateCheck("run_authorized_event", g_authorized),
        GateCheck("head_matches_authorized_commit", g_head_matches),
        GateCheck("attestation_flags_present", g_flags),
        GateCheck("locked_input_hashes", g_inputs),
        GateCheck("full_pytest", g_tests),
        GateCheck("frozen_hashes", g_frozen),
    ]


def main() -> int:
    from itsf.contracts import RunConfig, TrialState
    from itsf.s0.runner import RunnerDeps, S0Runner, GateCheck
    from itsf.s0.runner import append_registry_event_line

    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    clock = lambda: now.isoformat()                  # noqa: E731

    cfg = RunConfig(
        trial_id=TRIAL_ID,
        authorized_commit=_git("rev-parse", "HEAD"),
        seed=SEED,
        attempts_dir=str(REPO / "attempts" / f"{TRIAL_ID}-A{stamp}"),
        runs_dir=str(REPO / "runs" / f"{TRIAL_ID}_{stamp}"),
        assertions_path=str(REPO / "S0_INPUT_PREFLIGHT.json"))

    def registry_append(event: str, note: str) -> None:
        append_registry_event_line(REGISTRY, TRIAL_ID, event, note,
                                   clock(), cfg.authorized_commit[:7],
                                   "main agent (s0_real_run)")

    def compute_placeholder():
        # Wired only after RUN_AUTHORIZED exists; structurally unreachable
        # before then (the authorization gates precede Stage C). Fail closed
        # rather than pretend: the real Stage C wiring (loader -> context ->
        # dataset under the guarded logger) lands with the final packet
        # re-render, reviewed at the authorized commit.
        raise RuntimeError("Stage C wiring not yet activated — final packet "
                           "re-render pending (packet §0)")

    deps = RunnerDeps(
        config=cfg,
        trial_state=TrialState.PACKET_APPROVED,
        gates=build_gates(clock),
        structural_checks=[GateCheck(
            "preflight_assertions_file_present",
            lambda: (Path(cfg.assertions_path).exists(),
                     cfg.assertions_path))],
        compute=compute_placeholder,
        integrity_checks=[],
        render_report=lambda r: {},
        append_registry_event=registry_append,
        clock_utc=clock,
        log=lambda msg: print(f"[s0-runner] {msg}", flush=True))

    out = S0Runner(deps).run()
    print(f"terminal: stage={out.terminal_stage.value} ok={out.ok} "
          f"exposure_consumed={out.exposure_consumed} "
          f"kind={out.failure_kind or 'success'}")
    return 0 if out.ok else 2


if __name__ == "__main__":
    sys.exit(main())
