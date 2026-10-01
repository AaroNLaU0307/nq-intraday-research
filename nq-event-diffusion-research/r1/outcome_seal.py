"""TASK 12 -- outcome sealing, so the OD-3 gate is executable rather than notional.

Four output classes, kept apart on purpose (sealed R.1 S2-9):

    BUILD_OUTPUT            synthetic, free to print -- it is not a result
    POWER_GATE_OUTPUT       outcome-blind dispersion and MDEs; readable BEFORE
                            any reveal, because that is the whole point of OD-3
    SEALED_R1_OUTCOME       the real Primary. Written to a run directory,
                            digest-recorded, and NEVER returned or printed
    OWNER_AUTHORIZED_REVEAL the same values, released only against an explicit
                            Aaron authorization

A sealed outcome leaves this module as a `SealedOutcomeHandle`: a path, a
digest and a class -- no values, and a `__repr__` that cannot leak one even
into a traceback or a notebook echo. `reveal()` is the only door, and it needs
an Owner token.

No real outcome is created in S2. `seal_outcome` refuses a bundle that is not
marked synthetic unless it carries an S3 authorization token.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .errors import AuthorityError, OutcomeExposureError

BUILD_OUTPUT = "BUILD_OUTPUT"
POWER_GATE_OUTPUT = "POWER_GATE_OUTPUT"
SEALED_R1_OUTCOME = "SEALED_R1_OUTCOME"
OWNER_AUTHORIZED_REVEAL = "OWNER_AUTHORIZED_REVEAL"

OUTPUT_CLASSES = (BUILD_OUTPUT, POWER_GATE_OUTPUT, SEALED_R1_OUTCOME,
                  OWNER_AUTHORIZED_REVEAL)

S3_TOKEN_PREFIX = "S3_RUN_AUTHORIZED_BY_AARON:"
REVEAL_TOKEN_PREFIX = "REVEAL_AUTHORIZED_BY_AARON:"


@dataclass(frozen=True)
class SealedOutcomeHandle:
    """A receipt. Deliberately value-free."""
    output_class: str
    path: Path
    sha256: str
    n_records: int
    written_utc: str
    synthetic: bool

    def __repr__(self) -> str:                       # no values, ever
        return (f"<SealedOutcomeHandle {self.output_class} "
                f"n={self.n_records} sha256={self.sha256[:12]} "
                f"synthetic={self.synthetic} -- values withheld>")

    __str__ = __repr__


def _canonical(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)


def seal_outcome(payload: Mapping[str, Any], run_dir: Path | str, *,
                 output_class: str = SEALED_R1_OUTCOME,
                 synthetic: bool = True,
                 s3_authorization: str | None = None) -> SealedOutcomeHandle:
    """Write an outcome bundle to the run directory. Returns a receipt only.

    Nothing is printed and nothing is returned but the receipt: an accidental
    `print(seal_outcome(...))` cannot expose a result.
    """
    if output_class not in OUTPUT_CLASSES:
        raise OutcomeExposureError(f"unknown output class {output_class!r}")
    if not synthetic:
        if not isinstance(s3_authorization, str) or \
                not s3_authorization.startswith(S3_TOKEN_PREFIX):
            raise AuthorityError(
                "a REAL R1 outcome may only be sealed under S3 authorization. "
                "S2 BUILD produces synthetic bundles.")

    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    written = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    body = _canonical({
        "output_class": output_class,
        "synthetic": synthetic,
        "written_utc": written,
        "exposure_note": ("sealed; not to be read without an Owner-authorized "
                          "reveal (sealed I.3 / M)"),
        "payload": payload,
    })
    path = run_dir / f"{output_class.lower()}.json"
    path.write_text(body + "\n", encoding="utf-8")
    return SealedOutcomeHandle(
        output_class=output_class, path=path,
        sha256=hashlib.sha256(body.encode("utf-8")).hexdigest(),
        n_records=len(payload.get("records", []) or []),
        written_utc=written, synthetic=synthetic)


def read_power_gate_output(handle: SealedOutcomeHandle) -> dict[str, Any]:
    """POWER_GATE_OUTPUT is readable WITHOUT a reveal -- that is OD-3's point."""
    if handle.output_class != POWER_GATE_OUTPUT:
        raise OutcomeExposureError(
            f"{handle.output_class} is not readable without an Owner-authorized "
            f"reveal; only POWER_GATE_OUTPUT is pre-reveal readable.")
    return json.loads(handle.path.read_text(encoding="utf-8"))


def reveal(handle: SealedOutcomeHandle, *,
           owner_authorization: str | None = None) -> dict[str, Any]:
    """The only door to a sealed outcome. Needs an explicit Owner token."""
    if handle.output_class in (BUILD_OUTPUT, POWER_GATE_OUTPUT):
        return json.loads(handle.path.read_text(encoding="utf-8"))
    if not isinstance(owner_authorization, str) or \
            not owner_authorization.startswith(REVEAL_TOKEN_PREFIX):
        raise OutcomeExposureError(
            "revealing a sealed R1 outcome requires an explicit Aaron "
            "authorization. Reading it without one consumes the reveal the "
            "OD-3 gate exists to protect.")
    data = json.loads(handle.path.read_text(encoding="utf-8"))
    data["output_class"] = OWNER_AUTHORIZED_REVEAL
    data["revealed_under"] = owner_authorization.split(":", 1)[0] + ":<token>"
    return data
