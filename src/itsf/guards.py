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


def assert_real_run_allowed() -> None:
    """Gate for ANY computation on real market data producing readable numbers."""
    verify_frozen_hashes()
    missing = [str(p) for p in (G9_FLAG, SECOND_COPY_FLAG) if not p.exists()]
    if missing:
        raise RunBlockedError(
            "real S0/MC computation blocked; missing attestations: "
            + "; ".join(missing))
