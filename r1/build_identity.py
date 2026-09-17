"""S2 implementation identity -- what code is actually about to run.

The S1 seal answers "what design is fixed". This module answers the other
question a real run must answer: **"are the executable bytes the ones that were
built, tested and attested?"** They are different questions, and conflating
them is how a run ends up claiming one implementation identity while executing
another.

Two identities, built on the same no-self-reference pattern as the S1 seal:

    S2_CODE_COMMIT               the commit whose tree IS the final executable
                                 code and tests
    S2_BUILD_ATTESTATION_COMMIT  its metadata-only child, which adds
                                 R1_S2_BUILD_ATTESTATION.json and changes no
                                 executable source. Identified by tag
                                 `r1-s2-built`, because a commit cannot contain
                                 its own hash.

**Nothing here hard-codes a commit.** The authoritative S2 code identity is read
from the build attestation on disk; if that file is missing or malformed the
answer is a refusal, never a stale historical default.

The check that matters at S3 preflight is `assert_executable_identity`. It
compares a rollup over the RUNTIME SOURCE -- `r1/*.py`, this project's only
runtime dependency -- against the rollup recorded at attestation time. So:

    a later metadata-only ledger append      does NOT invalidate it
    a later edit to any runtime source file  DOES invalidate it
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from .contract import PROJECT_ROOT, sha256_file
from .errors import SealIdentityError

ATTESTATION_FILE = "R1_S2_BUILD_ATTESTATION.json"

#: The executable surface this project owns and a run depends on. `tools/` are
#: validators, not runtime, and are deliberately outside the rollup.
RUNTIME_SOURCE_DIR = "r1"
RUNTIME_SOURCE_GLOB = "*.py"

REQUIRED_FIELDS = ("S2_CODE_COMMIT", "CONTENT_COMMIT",
                   "SEAL_ATTESTATION_COMMIT", "runtime_source",
                   "sealed_digests", "state")


def runtime_source_files(root: Path | None = None) -> tuple[Path, ...]:
    root = root or PROJECT_ROOT
    return tuple(sorted((root / RUNTIME_SOURCE_DIR).glob(RUNTIME_SOURCE_GLOB)))


def runtime_source_map(root: Path | None = None) -> dict[str, str]:
    """{relative path -> sha256} over every runtime source file."""
    root = root or PROJECT_ROOT
    return {f"{RUNTIME_SOURCE_DIR}/{p.name}": sha256_file(p)
            for p in runtime_source_files(root)}


def runtime_source_rollup(root: Path | None = None) -> str:
    """One digest over the whole runtime surface, path-sensitive.

    Adding, removing, renaming or editing a runtime file all move this value.
    """
    payload = "\n".join(f"{rel}:{digest}"
                        for rel, digest in sorted(runtime_source_map(root).items()))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class BuildIdentity:
    s2_code_commit: str
    content_commit: str
    seal_attestation_commit: str
    runtime_source_rollup_sha256: str
    runtime_source_files: int
    attestation_path: Path

    @property
    def s2_build_attestation_commit(self) -> str:
        """Not a value: a commit cannot contain its own hash. Resolve the tag."""
        return "tag:r1-s2-built"


def load_build_identity(root: Path | None = None) -> BuildIdentity:
    """Read the authoritative S2 identity. Refuses rather than defaulting."""
    root = root or PROJECT_ROOT
    path = root / ATTESTATION_FILE
    if not path.exists():
        raise SealIdentityError(
            f"{ATTESTATION_FILE} is missing: this tree has no attested S2 code "
            f"identity. A run may not assume one -- build, validate and attest "
            f"first.")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SealIdentityError(f"{ATTESTATION_FILE} is malformed") from exc
    missing = [f for f in REQUIRED_FIELDS if f not in data]
    if missing:
        raise SealIdentityError(
            f"{ATTESTATION_FILE} is missing required fields {missing}")
    commit = data["S2_CODE_COMMIT"]
    if not isinstance(commit, str) or len(commit) != 40:
        raise SealIdentityError(
            f"S2_CODE_COMMIT must be a full 40-character sha, got {commit!r}")
    return BuildIdentity(
        s2_code_commit=commit,
        content_commit=data["CONTENT_COMMIT"],
        seal_attestation_commit=data["SEAL_ATTESTATION_COMMIT"],
        runtime_source_rollup_sha256=data["runtime_source"]["rollup_sha256"],
        runtime_source_files=data["runtime_source"]["n_files"],
        attestation_path=path,
    )


def assert_executable_identity(root: Path | None = None) -> BuildIdentity:
    """S3 PREFLIGHT: refuse if the executable bytes are not the attested ones.

    This is the check that makes "we ran S2_CODE_COMMIT" a fact rather than a
    claim. It is deliberately insensitive to metadata -- ledger appends, state
    pointers, reports -- and exactly sensitive to runtime source.
    """
    root = root or PROJECT_ROOT
    identity = load_build_identity(root)
    current = runtime_source_rollup(root)
    if current != identity.runtime_source_rollup_sha256:
        attested = set(json.loads(
            (root / ATTESTATION_FILE).read_text(encoding="utf-8")
        )["runtime_source"]["files"].items())
        live = set(runtime_source_map(root).items())
        changed = sorted({rel for rel, _ in attested ^ live})
        raise SealIdentityError(
            f"executable identity mismatch: the runtime source is not the "
            f"attested S2_CODE_COMMIT {identity.s2_code_commit[:12]}. "
            f"Changed or unattested: {changed[:6]}. Re-build, re-validate and "
            f"re-attest before running; do NOT run one identity while claiming "
            f"another.")
    return identity
