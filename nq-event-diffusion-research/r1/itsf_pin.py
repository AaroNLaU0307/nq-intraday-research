"""Pinned reference to the PARKED ITSF repository.

R1 reuses three pieces of ITSF frozen logic. It does NOT import them at
runtime: ITSF is a parked working tree, and a runtime import would make R1's
results depend on mutable state outside its own sealed commit. Instead R1
TRANSCRIBES the logic and pins the source file by sha256, exactly as PSMV did
for the eligibility funnel.

The transcription is not asserted. `tests/test_costs.py` imports ITSF's own
`costs.py` and cross-checks R1's transcribed formulas against it numerically,
and `verify_pins()` below refuses if the pinned file has moved. If the pin
fails, the honest outcome is a STOP, not a silent fallback: R1 would no longer
know which cost model it is using.

**R1 never writes to ITSF.** These paths are opened read-only, and only by the
verification helpers here and by the cross-check test.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from .errors import SealIdentityError

ITSF_ROOT = Path(__file__).resolve().parent.parent.parent / \
    "Intraday Trend Strategy Framework"

#: sha256 of the ITSF files R1 transcribes, at ITSF HEAD 11725fb (parked).
PINNED: dict[str, str] = {
    "src/itsf/s0/costs.py":
        "14f7116bcfe5316029c00f02f72a610799cd49e747eb66d266b6a51b36a0dcd7",
    "src/itsf/contracts.py":
        "97d50740d938cb40eccab6595e6ba7284c493e9a662e311ddce31700f294a002",
    "src/itsf/data/roles.py":
        "18a16d62224132ad6985ec59d5b6378898477bc34034249eaf76e16ace10fe9c",
}

ITSF_HEAD = "11725fb"


def available() -> bool:
    """True when the parked ITSF tree is present on this machine."""
    return ITSF_ROOT.is_dir()


def verify_pins(strict: bool = False) -> dict[str, str]:
    """Return {relpath: 'MATCH' | 'MOVED' | 'ABSENT'}.

    `strict=True` raises on anything that is not MATCH. The default is lenient
    because the cross-check is a TEST-time guarantee: R1's runtime must not
    depend on ITSF being present at all.
    """
    out: dict[str, str] = {}
    for rel, pin in PINNED.items():
        p = ITSF_ROOT / rel
        if not p.exists():
            out[rel] = "ABSENT"
        else:
            out[rel] = "MATCH" if hashlib.sha256(
                p.read_bytes()).hexdigest() == pin else "MOVED"
    if strict:
        bad = {k: v for k, v in out.items() if v != "MATCH"}
        if bad:
            raise SealIdentityError(f"ITSF pin verification failed: {bad}")
    return out
