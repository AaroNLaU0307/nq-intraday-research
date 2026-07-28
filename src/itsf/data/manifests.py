"""Manifest verification for the canonical data archive (main-agent authored).

Every real data file must be listed in its job directory's _local_manifest.json
(or the archive checksum manifest) and match its recorded SHA-256 byte-for-byte
BEFORE any decode. Mismatch == hard failure — no auto-repair, ever.
# frozen: charter data-governance (canonical corpus SHA-256 verified)
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


class ManifestError(RuntimeError):
    pass


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def load_manifest(job_dir: Path) -> dict:
    mp = job_dir / "_local_manifest.json"
    if not mp.exists():
        raise ManifestError(f"missing _local_manifest.json in {job_dir}")
    return json.loads(mp.read_text(encoding="utf-8"))


def verify_file_against_manifest(path: Path, manifest: dict) -> None:
    """Fail closed unless `path` is listed with a matching sha256.

    Manifest schema: {"files": {filename: {"sha256": ...}}} — the loader
    writes/reads this exact shape; fabricated fixtures use it too.
    """
    files = manifest.get("files")
    if not isinstance(files, dict):
        raise ManifestError("manifest has no 'files' mapping (schema violation)")
    entry = files.get(path.name)
    if entry is None:
        raise ManifestError(f"file not listed in manifest: {path.name}")
    want = entry.get("sha256")
    if not want:
        raise ManifestError(f"manifest entry for {path.name} lacks sha256")
    got = sha256_file(path)
    if got != want:
        raise ManifestError(
            f"sha256 mismatch for {path.name}: manifest {want[:16]}..., "
            f"actual {got[:16]}...")
