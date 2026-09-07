"""Run gates (MAIN-AGENT OWNED, read-only for subagents).

Two frozen hard gates stand between code and any real research number:
  1. G9 hard_run_blocker  — CME fee component unconfirmed (platform_params).
  2. Second physical copy — charter data-governance clause.
Both are represented as explicit attestation flag files that do NOT exist yet.
Creating them is a main-agent + Aaron action recorded in FREEZE_LOG.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

G9_FLAG = REPO / "gate1" / "G9_RESOLVED.flag"
SECOND_COPY_FLAG = REPO / "ops" / "SECOND_COPY_ATTESTED.flag"

# Frozen-file byte hashes as registered in FREEZE_LOG.md (Registry Commits B).
FROZEN_HASHES = {
    "PROJECT_CHARTER.md":
        "5176320fb54a30e5e5dcc7f1ee96b828e7d38f727a573e8bd152ca3ff4299327",
    "STUDY_0_PREREGISTRATION.md":
        "6cca20b7b1ce496d582ef5b4677333ba1b74bc577020ab29df00ff0c0d1af132",
    "purchase_plan.yaml":
        "02edbc2cb8481089ecf7b30156fd86eb3cf524112e3f97d253f94acc60c39e6c",
    "MC_METHOD_SPEC.md":
        "a6de4a286eaff5ab7487298593f590cbee845afa1939ad4ea675ec219cf29608",
    # MC1.1-G9 evidence-resolution addendum (2026-07-28): params + registry
    # updated per MC_METHOD_SPEC SS7; at-freeze hashes remain anchored in
    # FREEZE_LOG (65bfdd9e... / c14d576b...); these are the CURRENT canonical
    # bytes registered by the addendum entry.
    "gate1/platform_params.yaml":
        "702b983baba88d833ebf7122d358beaf9feb946c99c2e85aad41ecee2863d9ff",
    "gate1/evidence_registry.yaml":
        "8ec318088ebedc9a3e3ce65bedf743b8a7741bfaa97481e841dc1802cb66a198",
    "gate1/snapshots/2026-07-28/snapshot_manifest_v5.json":
        "5b6083b5ee61db9c44b119fae3bfdb2c0c039b9c53f5d7c67a74c69f6d4e0434",
}


class RunBlockedError(RuntimeError):
    pass


class FrozenTamperError(RuntimeError):
    pass


def verify_frozen_hashes() -> None:
    """Raise if any frozen file's bytes differ from its registered hash."""
    for rel, want in FROZEN_HASHES.items():
        got = hashlib.sha256((REPO / rel).read_bytes()).hexdigest()
        if got != want:
            raise FrozenTamperError(f"frozen file modified: {rel} ({got[:16]}...)")


def assert_trusted_launch(launch=None) -> None:
    """Refuse unless this process came through the trusted launch boundary.

    QROS-CF R3, PRE-CERT REPAIR. Preparing the final-certification transport
    measured that `scripts/s0_real_run.py` referenced neither `seam_recheck`
    nor `assert_governed_launch` nor `execution_identity` -- not once. So the
    trusted-launch proof covered exactly one path (the P3 seam) while eight
    production entries reached real bytes without it, and the earlier claim
    that the boundary was "mechanically enforced" was true of the seam and
    false of every real-run entry. That is the claim-wider-than-the-fact shape
    this project keeps finding, and this time it was mine.

    THIS GATE IS WHERE IT BELONGS, because it is already the single real-run
    gate: `assert_real_run_allowed` is called with the production defaults by
    `s0_real_run`, `run_data_qa`, `qa_addendum_a1`, `qa_addendum_a2`,
    `consumer.run_real_mc`, `real_input` (twice) and
    `supplement_runner.run_supplement_production`, and reached through the
    default-flag loader by `s0_input_preflight`. One requirement here covers
    every one of them, and covers a future entry that calls the gate without
    anyone remembering to add anything.

    `launch` is an explicit injection seam, the same shape `seam_recheck` uses
    for its environment and bytecode reports, so a test can exercise the gate
    without being launched through the boundary. It is a named parameter, not a
    branch on whether the caller looks like a test.
    """
    from . import execution_identity as _ei

    attested = _ei.launch_attestation() if launch is None else launch
    if attested is None:
        raise RunBlockedError(
            "real run blocked: this process was not started through the "
            "trusted launch boundary, so no startup surface or bytecode-cache "
            "proof exists for it. Launch through scripts/run_governed.py "
            "(or scripts\\run_governed.cmd), which runs the governed child "
            "under -S with a private pycache prefix and attests before any "
            "governed import.")


def assert_real_run_allowed(g9_flag: Path = G9_FLAG,
                            second_copy_flag: Path = SECOND_COPY_FLAG,
                            *, launch=None) -> None:
    """Gate for ANY computation on real market data producing readable numbers.

    The flag-path parameters exist so unit tests can exercise this exact gate
    logic against temporary attestation files; production callers use the
    defaults. The gate logic itself is never bypassed or monkeypatched.

    THE TRUSTED-LAUNCH REQUIREMENT APPLIES TO A REAL AUTHORIZED RUN (R3), which
    is precisely a call made with BOTH production attestation paths. A call
    carrying temporary flag paths is exercising this gate's logic against
    fixtures and cannot be a real authorized run on those flags.

    THAT CONDITION IS NAMED RATHER THAN HIDDEN, and here is what it does not
    cover: a caller that supplies temporary flag paths while pointing a loader
    at the real job directory would read real bytes without the launch proof.
    That seam is the pre-existing purpose of the flag parameters, it predates
    this window, and this repair neither widens nor closes it. It is stated so
    the next reader does not mistake this gate for more than it is.
    """
    verify_frozen_hashes()
    missing = [str(p) for p in (g9_flag, second_copy_flag) if not p.exists()]
    if missing:
        raise RunBlockedError(
            "real S0/MC computation blocked; missing attestations: "
            + "; ".join(missing))
    if (Path(g9_flag) == G9_FLAG
            and Path(second_copy_flag) == SECOND_COPY_FLAG):
        assert_trusted_launch(launch)
