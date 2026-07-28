"""Second-physical-copy verification (Aaron's milestone gate, 2026-07-28 spec).

THREE-WAY check (main-agent hardening of the two-way spec):
    primary bytes  <->  official Databento manifests  <->  backup bytes
Only if all three agree does the tool emit the attestation DRAFT. It NEVER
creates ops/SECOND_COPY_ATTESTED.flag — that final act happens only after
Aaron reviews the attestation (frozen instruction: no self-certification).

Usage:  python scripts/physical_copy_verify.py <backup_root>
        e.g.  python scripts/physical_copy_verify.py E:\\quant-data
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PRIMARY_ROOT = Path(r"C:\Users\Aaron\quant-data")
ATTESTATION_OUT = Path(r"C:\Users\Aaron\OneDrive\Desktop\Quant trade"
                       r"\Intraday Trend Strategy Framework\ops"
                       r"\physical_copy_attestation.json")


def sha256_file(p: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def collect(root: Path) -> dict[str, str]:
    """Relative path -> sha256 for every file under root."""
    out = {}
    for p in sorted(root.rglob("*")):
        if p.is_file():
            out[str(p.relative_to(root)).replace("\\", "/")] = sha256_file(p)
    return out


def official_manifest_hashes(root: Path) -> dict[str, str]:
    """Recorded sha256 from Databento job manifests under root."""
    want: dict[str, str] = {}
    for mf in root.rglob("_local_checksums.json"):
        data = json.loads(mf.read_text(encoding="utf-8"))
        # recovery-format manifests carry per-file lists in various shapes;
        # only 'files' mappings with sha256 are authoritative here
        files = data.get("files")
        if isinstance(files, dict):
            for name, entry in files.items():
                if isinstance(entry, dict) and entry.get("sha256"):
                    want[str(mf.parent.relative_to(root) / name).replace("\\", "/")] = entry["sha256"]
    for mf in root.rglob("_local_manifest.json"):
        data = json.loads(mf.read_text(encoding="utf-8"))
        files = data.get("files")
        if isinstance(files, dict):
            for name, entry in files.items():
                if isinstance(entry, dict) and entry.get("sha256"):
                    want[str(mf.parent.relative_to(root) / name).replace("\\", "/")] = entry["sha256"]
    return want


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    backup_root = Path(sys.argv[1])
    if not backup_root.exists():
        print(f"backup root not found: {backup_root}")
        return 1

    print("hashing primary ...")
    primary = collect(PRIMARY_ROOT)
    print(f"  {len(primary)} files")
    print("hashing backup ...")
    backup = collect(backup_root)
    print(f"  {len(backup)} files")

    missing_in_backup = sorted(set(primary) - set(backup))
    extra_in_backup = sorted(set(backup) - set(primary))
    mismatched = sorted(k for k in set(primary) & set(backup)
                        if primary[k] != backup[k])

    print("checking primary against official Databento manifests ...")
    official = official_manifest_hashes(PRIMARY_ROOT)
    official_mismatch = sorted(
        k for k, want in official.items()
        if primary.get(k) is not None and primary[k] != want)
    official_missing = sorted(k for k in official if k not in primary)

    ok = not (missing_in_backup or mismatched or official_mismatch
              or official_missing)
    att = {
        "primary_root": str(PRIMARY_ROOT),
        "backup_root": str(backup_root),
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
        "verifier": "Aaron (copy confirmed) + main-agent machine verification",
        "primary_file_count": len(primary),
        "backup_file_count": len(backup),
        "official_manifest_entries_checked": len(official),
        "all_raw_sha256_match": ok,
        "missing_in_backup": missing_in_backup[:20],
        "extra_in_backup": extra_in_backup[:20],
        "primary_vs_backup_mismatches": mismatched[:20],
        "primary_vs_official_mismatches": official_mismatch[:20],
        "official_entries_missing_from_primary": official_missing[:20],
        "flag_created": False,   # ALWAYS false here — Aaron reviews first
    }
    ATTESTATION_OUT.parent.mkdir(parents=True, exist_ok=True)
    ATTESTATION_OUT.write_text(json.dumps(att, indent=2, ensure_ascii=False),
                               encoding="utf-8")
    print(json.dumps({k: att[k] for k in
                      ("primary_file_count", "backup_file_count",
                       "official_manifest_entries_checked",
                       "all_raw_sha256_match")}, indent=2))
    print(f"attestation DRAFT written: {ATTESTATION_OUT}")
    print("NOTE: SECOND_COPY flag NOT created — awaiting Aaron review/approval.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
