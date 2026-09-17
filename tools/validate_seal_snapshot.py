"""SEAL_SNAPSHOT_VALIDATION -- run the sealed validator in its own context.

`psmv/validate_prereg.py` is sealed. It asserts things that were true AT SEAL
TIME, including the project state of that moment. Running it against today's
working tree and calling the result "184 passed, 1 expected failure" would be
reporting a validator failure as a normal state; running it against the state
it was sealed with is the correct test, and it passes cleanly there.

This tool extracts the sealed commits into a temporary directory with
`git archive` -- no checkout, no worktree, nothing touched -- and runs the
sealed validator inside each.

    CONTENT_COMMIT           the sealed content, before the attestation existed
    SEAL_ATTESTATION_COMMIT  the same content plus its attestation

Both must pass. Current-state validation is a different question and lives in
`tools/validate_state.py`.

Run:  python tools/validate_seal_snapshot.py
"""
from __future__ import annotations

import json
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEAL_FILE = ROOT / "R1_S1_SEAL_ATTESTATION.json"
VALIDATOR = "psmv/validate_prereg.py"


def _git(*args: str, capture_bytes: bool = False):
    out = subprocess.run(["git", *args], cwd=ROOT, check=True,
                         stdout=subprocess.PIPE)
    return out.stdout if capture_bytes else out.stdout.decode().strip()


def snapshot(commit: str, into: Path) -> Path:
    """Extract one commit's tree. Read-only: the working tree is untouched."""
    into.mkdir(parents=True, exist_ok=True)
    blob = _git("archive", commit, capture_bytes=True)
    tar_path = into / "snapshot.tar"
    tar_path.write_bytes(blob)
    with tarfile.open(tar_path) as tf:
        tf.extractall(into, filter="data")
    tar_path.unlink()
    return into


def run_sealed_validator(where: Path) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, VALIDATOR], cwd=where,
                          capture_output=True, text=True,
                          env={"PYTHONIOENCODING": "utf-8", **_env()})
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def _env() -> dict[str, str]:
    import os
    return {k: v for k, v in os.environ.items()}


def main() -> int:
    seal = json.loads(SEAL_FILE.read_text(encoding="utf-8"))
    content_commit = seal["CONTENT_COMMIT"]
    attestation_commit = _git("rev-list", "-1", "--all",
                              "--grep=SEAL_ATTESTATION_COMMIT", "--", ".") \
        or _git("rev-parse", "r1-s1-sealed^{commit}")

    failures = 0
    with tempfile.TemporaryDirectory(prefix="r1-seal-snapshot-") as tmp:
        for label, commit in (("CONTENT_COMMIT", content_commit),
                              ("SEAL_ATTESTATION_COMMIT", attestation_commit)):
            where = snapshot(commit, Path(tmp) / label.lower())
            code, output = run_sealed_validator(where)
            tail = [ln for ln in output.strip().splitlines() if ln.strip()][-1:]
            status = "PASS" if code == 0 else "FAIL"
            failures += code != 0
            print(f"{status}  seal snapshot {label} {commit[:12]} -- "
                  f"{tail[0] if tail else 'no output'}")
            if code != 0:
                for line in output.splitlines():
                    if line.startswith("FAIL"):
                        print(f"        {line}")

    print()
    print(f"SEAL_SNAPSHOT_VALIDATION = {'PASS' if not failures else 'FAIL'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
