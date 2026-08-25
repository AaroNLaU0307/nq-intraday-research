"""The single production validation boundary for `ops/TRIAL_REGISTRY.md`.

RULED, NOT CHOSEN. `MC-REG-COLLISION-001`, C2 as modified and ratified by a
fresh Codex GPT-5.6 Sol session on 2026-08-25 (`DELEGATED=YES`), over a
Fable 5 proposal. Sol replaced Fable's C2 outright; this module exists
because of what it replaced it with.

WHAT FABLE'S C2 MISSED. It required every production reader to be covered,
and stopped there — each reader could still take its OWN read of a MUTABLE
shared file. So MC validation could succeed against one version of
`ops/TRIAL_REGISTRY.md` while supplement resolution acted on another.
Measured before the ruling: FOUR independent `read_text` calls on that path
lived in `consumer`, `day_strata_supplement`, `real_input` and
`supplement_runner`. The loophole was reachable, not theoretical.

THE INVARIANT THIS MODULE IS. One read. Both lifecycles against the
identical immutable snapshot. A refusal from EITHER yields no usable result
and no downstream action.

That last clause is the part worth reading twice: a supplement chain that
resolves perfectly is still UNUSABLE if MC resolution refused over the same
bytes, because the file's governance record is broken and neither lifecycle
gets to act on a broken record. `supplement_chain()` carries an MC refusal
out as the chain's own `problem`, so the existing A_PRECHECK gate
`registry_chain_resolvable` enforces the coupling with no gate change —
`ANY_CHAIN_DEFECT=REFUSE_WHOLE_RESOLUTION` already meant exactly this, one
lifecycle wider.

NO BYPASS. Production code may not read that path or call either resolver
directly. The only exceptions C2 allows are unconditional-refusal stubs —
functions incapable of returning authorization, readiness or a usable chain
— and those are enumerated and BEHAVIOURALLY proved to refuse in
`tests/test_registry_boundary.py`, not merely declared.
"""
from __future__ import annotations

import dataclasses as _dc
import hashlib
from pathlib import Path
from types import MappingProxyType

__all__ = ["RegistrySnapshot", "MediatedResolution", "BoundaryError",
           "REGISTRY_PATH", "BOUNDARY_RULING", "read_snapshot", "mediate",
           "resolve_registry", "supplement_chain", "resolve_for_supplement"]

BOUNDARY_RULING = "MC_REG_COLLISION_001_C2_AS_MODIFIED_2026-08-25"
BOUNDARY_RULING_DELEGATED = True

#: The one governed path. Relative to the repo root.
REGISTRY_PATH = "ops/TRIAL_REGISTRY.md"

_REPO_ROOT = Path(__file__).resolve().parents[3]


class BoundaryError(RuntimeError):
    """The boundary itself could not produce a snapshot. Never a warning."""


@_dc.dataclass(frozen=True)
class RegistrySnapshot:
    """The bytes, read once. Everything downstream reasons about THESE.

    Carries its own digest so evidence can record WHICH registry state a
    decision was taken against, rather than a claim that one was read."""
    text: str
    sha256: str
    source: str

    @property
    def n_bytes(self) -> int:
        return len(self.text.encode("utf-8"))


@_dc.dataclass(frozen=True)
class MediatedResolution:
    """Both lifecycles, one snapshot.

    `refusal` non-empty means NOTHING here is usable — and the constructor
    enforces that rather than trusting callers to check, because "the
    caller will check" is how a refused resolution becomes a permitted
    action."""
    snapshot: RegistrySnapshot
    supplement_chains: object = _dc.field(default_factory=dict)
    mc_chains: object = _dc.field(default_factory=dict)
    refusal: str = ""
    refusing_lifecycle: str = ""          # "" | "supplement" | "mc"
    ruling: str = BOUNDARY_RULING
    delegated: bool = BOUNDARY_RULING_DELEGATED

    def __post_init__(self) -> None:
        if self.refusal:
            if self.supplement_chains or self.mc_chains:
                raise BoundaryError(
                    "a refused resolution carries chains; a refusal from "
                    "either lifecycle must leave NOTHING usable "
                    f"({self.refusing_lifecycle}: {self.refusal})")
            if self.refusing_lifecycle not in ("supplement", "mc"):
                raise BoundaryError(
                    f"refusing_lifecycle={self.refusing_lifecycle!r} names "
                    "no lifecycle; a refusal nobody owns cannot be acted on")
        elif self.refusing_lifecycle:
            raise BoundaryError(
                "refusing_lifecycle is set with no refusal")

    @property
    def usable(self) -> bool:
        return not self.refusal


# ---------------------------------------------------------------------------
# The read
# ---------------------------------------------------------------------------

def _read_text(path: Path) -> str:
    """THE production read of the governed registry path.

    Deliberately one tiny function: the no-bypass test asserts that no
    other production module reads this path, and the behavioural test
    counts calls HERE to prove one mediation performs exactly one read."""
    return path.read_text(encoding="utf-8") if path.exists() else ""


def read_snapshot(path: str | Path | None = None) -> RegistrySnapshot:
    """Read the registry ONCE and freeze what was read."""
    target = Path(path) if path is not None else (_REPO_ROOT / REGISTRY_PATH)
    text = _read_text(target)
    return RegistrySnapshot(
        text=text,
        sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        source=str(target))


# ---------------------------------------------------------------------------
# The mediation
# ---------------------------------------------------------------------------

def mediate(snapshot: RegistrySnapshot) -> MediatedResolution:
    """Run BOTH lifecycles against the identical snapshot.

    Order is not significance: whichever refuses first wins, and either
    refusal is total. A resolver that blows up is converted to a refusal
    rather than allowed to propagate — an exception a caller might catch
    and read as "no problem found" is the failure this whole subsystem
    exists to prevent.
    """
    from . import mc_registry as _mc
    from . import supplement_registry as _sup

    try:
        sup_chains, sup_refusal = _sup.resolve_supplement_chains(
            snapshot.text)
    except Exception as exc:                                  # noqa: BLE001
        return MediatedResolution(
            snapshot=snapshot,
            refusal=f"supplement_resolver_internal_error: {exc!r}",
            refusing_lifecycle="supplement")
    if sup_refusal:
        return MediatedResolution(snapshot=snapshot, refusal=str(sup_refusal),
                                  refusing_lifecycle="supplement")

    try:
        mc_chains, mc_refusal = _mc.resolve_mc_chains(snapshot.text)
    except Exception as exc:                                  # noqa: BLE001
        return MediatedResolution(
            snapshot=snapshot,
            refusal=f"mc_resolver_internal_error: {exc!r}",
            refusing_lifecycle="mc")
    if mc_refusal:
        return MediatedResolution(snapshot=snapshot, refusal=str(mc_refusal),
                                  refusing_lifecycle="mc")

    return MediatedResolution(
        snapshot=snapshot,
        supplement_chains=MappingProxyType(dict(sup_chains)),
        mc_chains=MappingProxyType(dict(mc_chains)))


def resolve_registry(path: str | Path | None = None) -> MediatedResolution:
    """One read, both lifecycles. THE production entry."""
    return mediate(read_snapshot(path))


# ---------------------------------------------------------------------------
# Per-lifecycle accessors — the only way out of the boundary
# ---------------------------------------------------------------------------

def supplement_chain(resolution: MediatedResolution, supplement_id: str):
    """One supplement id's chain, poisoned by an MC refusal.

    Returns the same `ChainResolution` shape `supplement_registry` does, so
    the A_PRECHECK gates consume it unchanged. When MC resolution refused,
    the chain comes back with that refusal as its own `problem` — which is
    how the cross-lifecycle coupling reaches gates that were written before
    MC rows existed, without touching a single gate.
    """
    from .supplement_registry import (NOT_AUTHORIZED_NO_CHAIN,
                                      ChainResolution)

    if resolution.refusal:
        return ChainResolution(
            supplement_id,
            problem=f"[{resolution.refusing_lifecycle}] {resolution.refusal}",
            detail=("whole resolution refused over registry snapshot "
                    f"{resolution.snapshot.sha256[:12]}; a refusal from "
                    "either lifecycle leaves nothing usable (C2)"))
    chain = resolution.supplement_chains.get(supplement_id)
    if chain is None:
        return ChainResolution(supplement_id, detail=NOT_AUTHORIZED_NO_CHAIN)
    return chain


def resolve_for_supplement(supplement_id: str,
                           path: str | Path | None = None):
    """`(snapshot, ChainResolution)` from ONE read. The runner's entry."""
    resolution = resolve_registry(path)
    return (resolution.snapshot, supplement_chain(resolution, supplement_id))
