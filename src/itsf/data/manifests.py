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
    """Load per-file hashes, normalized to {"files": {name: {"sha256": ...}}}.

    Two accepted sources, in priority order:
      1. _local_manifest.json with a "files" mapping (fabricated fixtures /
         future pipelines);
      2. the official Databento manifest.json ({"job_id", "files": [
         {"filename", "hash": "sha256:..."}]}) — the canonical archive format.
    """
    local = job_dir / "_local_manifest.json"
    if local.exists():
        data = json.loads(local.read_text(encoding="utf-8"))
        if isinstance(data.get("files"), dict):
            return data
    official = job_dir / "manifest.json"
    if official.exists():
        data = json.loads(official.read_text(encoding="utf-8"))
        entries = data.get("files")
        if isinstance(entries, list):
            files = {}
            for e in entries:
                h = str(e.get("hash", ""))
                if e.get("filename") and h.startswith("sha256:"):
                    files[e["filename"]] = {"sha256": h.split(":", 1)[1]}
            if files:
                return {"files": files, "source": "databento_manifest_json"}
    raise ManifestError(
        f"no usable manifest in {job_dir} (need _local_manifest.json with a "
        "'files' mapping or official Databento manifest.json)")


def load_authorized_manifest(job_dir: Path) -> dict:
    """The OFFICIAL manifest only -- no `_local_manifest.json` override.

    QROS-CF F03. `load_manifest` prefers `_local_manifest.json`, which is
    right for fabricated fixtures and wrong for the governed production path:
    the production identity pins the sha256 of `manifest.json`, so an
    unbound local manifest could sit beside an unchanged authorized one and
    silently become the authority for every per-file digest. Reproduced
    2026-09-07: an authorized manifest naming one `condition.json` digest, a
    conflicting `_local_manifest.json`, and a replacement `condition.json`
    verified clean.

    A separate ENTRY rather than a flag on `load_manifest`, because a
    keyword whose default keeps the unsafe behaviour is how the unsafe
    behaviour survives.
    """
    official = job_dir / "manifest.json"
    if not official.exists():
        raise ManifestError(
            f"no manifest.json under {job_dir} -- the authorized production "
            "path accepts no other manifest authority")
    data = json.loads(official.read_text(encoding="utf-8"))
    entries = data.get("files")
    if not isinstance(entries, list):
        raise ManifestError(
            "manifest.json has no 'files' list (official Databento shape)")
    files = {}
    for e in entries:
        h = str(e.get("hash", ""))
        if e.get("filename") and h.startswith("sha256:"):
            files[e["filename"]] = {"sha256": h.split(":", 1)[1]}
    if not files:
        raise ManifestError("manifest.json lists no sha256 entry")
    return {"files": files, "source": "databento_manifest_json"}


def _want_sha256(name: str, manifest: dict) -> str:
    files = manifest.get("files")
    if not isinstance(files, dict):
        raise ManifestError("manifest has no 'files' mapping (schema violation)")
    entry = files.get(name)
    if entry is None:
        raise ManifestError(f"file not listed in manifest: {name}")
    want = entry.get("sha256")
    if not want:
        raise ManifestError(f"manifest entry for {name} lacks sha256")
    return want


def verify_bytes_against_manifest(name: str, data: bytes,
                                  manifest: dict) -> bytes:
    """Verify BYTES ALREADY IN HAND and return them, so the caller consumes
    exactly what was checked.

    QROS-CF F04. `verify_file_against_manifest` hashes a PATHNAME; a caller
    that then re-opens that pathname consumes whatever is there by then.
    Reproduced 2026-09-07 on `condition.json`: verified "available", swapped,
    consumed "degraded". Verification and consumption must share one byte
    payload, and returning it is what makes that the easy thing to write.
    """
    want = _want_sha256(name, manifest)
    got = hashlib.sha256(data).hexdigest()
    if got != want:
        raise ManifestError(
            f"sha256 mismatch for {name}: manifest {want[:16]}..., "
            f"actual {got[:16]}...")
    return data


def read_verified_bytes(path: Path, manifest: dict) -> bytes:
    """Read ONCE, verify those bytes, hand them back. The only safe order."""
    return verify_bytes_against_manifest(path.name, path.read_bytes(), manifest)


def verify_file_against_manifest(path: Path, manifest: dict) -> None:
    """Fail closed unless `path` is listed with a matching sha256.

    Manifest schema: {"files": {filename: {"sha256": ...}}} — the loader
    writes/reads this exact shape; fabricated fixtures use it too.

    THIS ENTRY VERIFIES A PATHNAME, so it proves nothing about bytes a later
    reopen returns. It stays for the .dbn.zst decode path, which verifies and
    decodes under one call. A caller that wants to PARSE the file must use
    `read_verified_bytes` instead (QROS-CF F04).
    """
    got = sha256_file(path)
    want = _want_sha256(path.name, manifest)
    if got != want:
        raise ManifestError(
            f"sha256 mismatch for {path.name}: manifest {want[:16]}..., "
            f"actual {got[:16]}...")
