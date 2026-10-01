"""Shared fixtures. Synthetic only -- no real Development data is reachable here."""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from r1.contract import load_sealed_contract          # noqa: E402

SEALED_FILES = (
    "R1_S1_SEAL_ATTESTATION.json",
    "R1_PREREG_MANIFEST.json",
    "R1_S1_PREREGISTRATION_SEALED.md",
    "R1_DELEGATED_OWNER_DECISIONS.md",
    "R1_S0_PROVENANCE.md",
    "R1_TRIAL_REGISTRY.md",
    "artifacts/PSMV_STRUCTURAL_REPORT.json",
    "artifacts/PSMV_PURITY_ATTESTATION.json",
    "psmv/psmv_structural.py",
    "psmv/psmv_purity_guard.py",
    "psmv/validate_prereg.py",
    ".gitattributes",
    ".gitignore",
)


@pytest.fixture(scope="session")
def contract():
    return load_sealed_contract()


@pytest.fixture
def sealed_copy(tmp_path):
    """A writable copy of the sealed set, for MUTATION tests.

    Mutating the real sealed files is forbidden; mutating a copy and proving
    the loader refuses it is how the seal binding is shown to be real.
    """
    for rel in SEALED_FILES:
        src = PROJECT_ROOT / rel
        dst = tmp_path / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    return tmp_path


def rewrite_json(path: Path, mutate) -> str:
    """Apply `mutate` to a JSON file in place and refresh its digest entry."""
    data = json.loads(path.read_text(encoding="utf-8"))
    mutate(data)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path.name


def refresh_digest(root: Path, rel: str) -> None:
    """Keep the attestation's digest consistent after a deliberate mutation, so
    the test exercises the SEMANTIC check rather than only the hash check."""
    import hashlib
    seal_path = root / "R1_S1_SEAL_ATTESTATION.json"
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    seal["sealed_digests"][rel] = hashlib.sha256(
        (root / rel).read_bytes()).hexdigest()
    seal_path.write_text(json.dumps(seal, indent=2) + "\n", encoding="utf-8")
