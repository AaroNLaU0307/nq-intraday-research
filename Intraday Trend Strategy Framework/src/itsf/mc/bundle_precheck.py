"""Re-derive the sealed bundle from DISK, before anything is authorized.

WHY THIS EXISTS, stated as the thing it refuses to let anyone say. Four
N06 review rounds ended with a residual: `SupplementAuthority.__new__` plus
`object.__setattr__` builds an exact-type authority, and a matching forged
`PreparedMCInput` makes the pair self-consistent, so
`verify_supplement_authority` returns success. Measured on 2026-08-24: a
fully forged pair was accepted, and the lie never reached a sealed byte
only because `bundle_table_digest` happens not to be among the binding's
keys.

So the verifier proves INTERNAL CONSISTENCY and nothing else. Reading it as
evidence that a real 14-file bundle exists, or that its bytes are the ones
that were sealed, is a step that does not hold -- and the N09 ruling
(2026-08-24, delegated to Codex GPT-5.6 Sol) requires the trust root to be
rebuilt at the execution boundary rather than inferred there.

WHAT THIS TAKES, AND WHAT IT REFUSES TO TAKE. A path and the bytes behind
it. No `PreparedMCInput`, no `SupplementAuthority`, no object of any kind
that could report its own contents -- that is the whole point, so the
signature carries none and a test pins that it never will. The expected
table comes from the post-run attestation, whose own bytes are pinned in
code; a table from anywhere else is refused unless a caller says
`for_tests=True` out loud.

WHAT IT PRODUCES. The recomputed table, so the run evidence carries what
was actually on disk rather than a claim that it matched, plus one summary
digest over the whole set. A mismatch of any kind refuses before STARTED.
"""
from __future__ import annotations

import dataclasses as _dc
import hashlib
from pathlib import Path

__all__ = ["BundlePrecheckError", "BundleEntry", "BundlePrecheck",
           "frozen_bundle_table", "precheck_bundle_on_disk",
           "PRECHECK_RULING", "SUMMARY_DIGEST_SCHEMA"]

PRECHECK_RULING = "N09_REQUIRED_MITIGATION_2026-08-24"
PRECHECK_RULING_DELEGATED = True

#: Domain-separated so a bundle summary can never collide with any other
#: digest in this system.
SUMMARY_DIGEST_SCHEMA = "mc_bundle_ondisk_summary.v1"


class BundlePrecheckError(ValueError):
    """The bundle on disk is not the sealed one. Never a warning."""

    def __init__(self, code: str, detail: str = ""):
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code


@_dc.dataclass(frozen=True)
class BundleEntry:
    name: str
    size: int
    sha256: str


@_dc.dataclass(frozen=True)
class BundlePrecheck:
    """What was ACTUALLY on disk, not a verdict that it matched.

    The recomputed table travels into the run evidence. A boolean would
    let the evidence say "checked" while nothing recorded against what."""
    bundle_root: str
    recomputed: tuple
    expected_source: str
    summary_digest: str
    ruling: str = PRECHECK_RULING
    delegated: bool = PRECHECK_RULING_DELEGATED

    @property
    def n_files(self) -> int:
        return len(self.recomputed)


def _summary(entries, schema: str = SUMMARY_DIGEST_SCHEMA) -> str:
    """One digest over the whole set, order-independent by construction.

    `schema` is a parameter so a DIFFERENT file-table artifact class can
    use THIS formula instead of copying it (`run_output` digests the
    run's own output inventory). It defaults to the bundle schema, so
    every existing caller and every recorded bundle digest is unchanged;
    a different class passes its own string, which is what keeps the two
    from colliding.
    """
    body = "\n".join(f"{e.name}={e.size}={e.sha256}"
                     for e in sorted(entries, key=lambda x: x.name))
    return hashlib.sha256(
        (schema + "\n" + body).encode("utf-8")).hexdigest()


def frozen_bundle_table():
    """The expected table, from the attestation whose bytes are code-pinned.

    Reads the attestation through the same constructor production uses, so
    the pin is enforced here rather than re-implemented -- one rule, one
    place. A second parser would be a second thing to keep in agreement,
    which is the shape that produced four Highs in this subsystem."""
    from .consumer import load_custody_authority_from_attestation
    authority = load_custody_authority_from_attestation()
    table = dict(authority.file_sha256)
    sizes = dict(getattr(authority, "file_bytes", {}) or {})
    return tuple(
        BundleEntry(name=name, sha256=str(digest),
                    size=int(sizes.get(name, -1)))
        for name, digest in sorted(table.items()))


def precheck_bundle_on_disk(bundle_root, expected=None, *,
                            for_tests: bool = False) -> BundlePrecheck:
    """Recompute every sealed file's SHA-256 from the bytes on disk.

    `bundle_root` is a PATH. Nothing here accepts an object that could
    report its own contents; the N09 ruling requires exactly that, because
    an object's self-report is what the forged-pair residual can fabricate.

    Refuses -- before STARTED, never after -- on a missing file, a size
    that differs, a digest that differs, or a file present in the bundle
    that the sealed set does not name.
    """
    root = Path(bundle_root)
    if not root.is_dir():
        raise BundlePrecheckError(
            "bundle_root_absent",
            f"{root} is not a directory; the precheck reads bytes and has "
            "nothing to read")
    if expected is None:
        expected = frozen_bundle_table()
        source = "attestation(code-pinned)"
    elif for_tests:
        source = "caller(for_tests)"
    else:
        raise BundlePrecheckError(
            "bundle_expected_table_unpinned",
            "an expected table was supplied without for_tests=True. In "
            "production the table comes from the code-pinned attestation; "
            "accepting a caller's table would put the trust root back "
            "where N09 took it from")
    if not expected:
        raise BundlePrecheckError("bundle_expected_table_empty",
                                  "nothing to check against")

    recomputed, problems = [], []
    for entry in expected:
        path = root / entry.name
        if not path.is_file():
            problems.append(f"{entry.name}: MISSING")
            continue
        raw = path.read_bytes()
        got = BundleEntry(name=entry.name, size=len(raw),
                          sha256=hashlib.sha256(raw).hexdigest())
        recomputed.append(got)
        if entry.size >= 0 and got.size != entry.size:
            problems.append(
                f"{entry.name}: {got.size} bytes on disk, sealed table says "
                f"{entry.size}")
        if got.sha256 != entry.sha256:
            problems.append(
                f"{entry.name}: sha256 {got.sha256[:12]} on disk, sealed "
                f"table says {entry.sha256[:12]}")

    named = {e.name for e in expected}
    extra = sorted(p.name for p in root.iterdir()
                   if p.is_file() and p.name not in named)
    if extra:
        problems.append(
            f"present but not in the sealed set: {extra}. A bundle with an "
            "extra file is not the bundle that was sealed")
    if problems:
        raise BundlePrecheckError(
            "bundle_ondisk_mismatch",
            f"{len(problems)} problem(s) against {source}:\n  "
            + "\n  ".join(problems))
    return BundlePrecheck(
        bundle_root=str(root), recomputed=tuple(recomputed),
        expected_source=source, summary_digest=_summary(recomputed))
