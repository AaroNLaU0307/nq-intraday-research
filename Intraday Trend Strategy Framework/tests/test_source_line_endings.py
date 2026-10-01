"""Our own source stays LF. The evidence tree is not ours to normalise.

WHY, and it is a near-miss rather than a style preference. On 2026-08-24 a
`pathlib.write_text` edit silently rewrote two test files from LF to CRLF --
`write_text` translates newlines to os.linesep on Windows -- and they were
committed that way. The real change in each was a few lines; the diff showed
1124 and 945 changed lines, which is how a review stops being able to see
what moved.

The fix I reached for first was worse than the defect: a loop over
`git ls-files` converting everything to LF. That swept 214 files, including
gate1/snapshots, the raw Fed and BLS HTML, PNG, PDF and XLS, and
snapshot_manifest_v5.json -- SEALED EVIDENCE PINNED BY SHA256. Reverted
before commit, and the manifest still hashes to
5b6083b5ee61db9c44b119fae3bfdb2c0c039b9c53f5d7c67a74c69f6d4e0434.

Those 212 files are legitimately CRLF: they are bytes as fetched, and their
line endings are part of what was sealed. Normalising them would break every
hash pin in the evidence chain.

So the invariant is scoped to what we author. src/ and tests/ are ours and
stay LF. Everything else is left exactly as it arrived.
"""
from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OURS = ("src", "tests", "scripts")

#: Pre-existing CRLF, registered rather than swept. This file has been CRLF
#: since 2026-07-29, long before this rule and unrelated to the 2026-08-24
#: incident. Its bytes are pinned nowhere and it is not in the frozen-hash
#: set, so converting it would be safe -- but it would add ~700 lines of
#: churn to whatever commit did it, which is the exact harm this rule
#: exists to prevent. Converting it is its own change, on its own day,
#: with nothing else in the diff.
KNOWN_CRLF = {"scripts/s0_input_preflight.py"}


def test_our_own_python_sources_are_lf():
    crlf = []
    for top in OURS:
        for path in sorted((REPO / top).rglob("*.py")):
            rel = str(path.relative_to(REPO)).replace(chr(92), "/")
            if rel in KNOWN_CRLF:
                continue
            if b"\r\n" in path.read_bytes():
                crlf.append(rel)
    assert not crlf, (
        "CRLF in files we author -- almost certainly a pathlib.write_text on "
        "Windows, which translates newlines. The next diff will show every "
        "line as changed and hide the real one:\n  " + "\n  ".join(crlf))


def test_the_evidence_tree_is_not_swept_into_this_rule():
    """The guard must stay narrow. A future version that walks the whole
    repository would rewrite sealed bytes, which is the mistake this file
    exists to remember rather than repeat."""
    assert "gate1" not in OURS
    assert "ops" not in OURS
    evidence = REPO / "gate1" / "snapshots" / "2026-07-28" / \
        "snapshot_manifest_v5.json"
    if evidence.exists():
        import hashlib
        assert hashlib.sha256(evidence.read_bytes()).hexdigest() == (
            "5b6083b5ee61db9c44b119fae3bfdb2c0c039b9c53f5d7c67a74c69f6d4e"
            "0434"), "sealed manifest bytes moved"
