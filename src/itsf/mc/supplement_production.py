"""The ONLY production path from a sealed S0 input to a sealed supplement.

MAIN-AGENT OWNED.

WHAT THIS CLOSES (N06 HOLD). N03 made the two decisive arguments of the
day-strata builder DERIVABLE from a `SupplementAuthority`; it did not make
them UNSUPPLIABLE. Measured at `617f7c3` on the public boundary:

    hand-made (expected_day_set, binding)
      -> BUILT AND SEALED from a hand-made pair (sha f4de1c34…)

That is the same shape as the factory-boundary defect Codex found in
`PreparedMCInput` at `c5c819b`: construction stayed public, so only the
LAST gate was closed and everything upstream of it could be forged. The
repair is the same one that worked there — a capability-minted receipt
that is NOT an init parameter, so the only object a production seal will
accept is one this module's builder produced.

THE SHAPE OF THE BOUNDARY

    build_supplement_from_authority(authority, prepared, day_rows)
        |  re-verifies authority against prepared (N03),
        |  DERIVES expected_day_set + binding itself — the caller
        |  cannot supply either
        v
    SupplementProduct(payload=..., receipt=<minted here, init=False>)
        |
        v
    seal_supplement_production(product, out_dir)
        |  refuses a Mapping, refuses a receipt-less product, refuses a
        |  receipt that does not describe THIS payload, then re-verifies
        |  the binding, the day-universe digest and the FULL day set
        v
    bytes on disk, via the ratified `.partial` discipline

`day_strata_supplement.build_day_strata_supplement_test_only` and
`seal_supplement_test_only` remain as the hermetic core, renamed so their
status is unmistakable at every call site. Their product carries no
receipt and therefore cannot reach the production seal — which is a test
in `tests/test_mc_supplement_production.py`, not a claim here.

NOTHING HERE AUTHORIZES ANYTHING. `SUPPLEMENT_EXECUTION_AUTHORIZED=NO`
stands; the production entry in `supplement_runner` still refuses before
any of this is reachable.
"""
from __future__ import annotations

import dataclasses as _dc
import hashlib
from pathlib import Path
from types import MappingProxyType
from typing import Mapping, Sequence

from . import day_strata_supplement as _ds
from . import supplement_authority as _sa
from . import supplement_contract as _sc
from . import supplement_runner as _run

PRODUCTION_RECEIPT_SCHEMA = "mc_supplement_production_receipt.v1"

#: Components digested SEPARATELY rather than folded into one identity, so
#: a mismatch NAMES what moved instead of reporting "identity changed" —
#: the same reason `consumer._battery_component_digests` is a table.
RECEIPT_COMPONENTS = ("authority", "prepared", "binding", "day_universe",
                      "rows", "payload")


class SupplementProductionError(ValueError):
    """Fail-closed refusal from the production boundary."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(f"{code}: {detail}" if detail else code)


class _ProductionCapability:
    """Module-private minting right. Not exported, never retained on an
    instance, so holding a genuine receipt cannot mint a second one."""
    __slots__ = ()


_CAPABILITY = _ProductionCapability()


def _digest(obj) -> str:
    return hashlib.sha256(
        _ds.canonical_json(obj).encode("utf-8")).hexdigest()


@_dc.dataclass(frozen=True, slots=True)
class ProductionReceipt:
    """Proof that a payload came out of `build_supplement_from_authority`.

    `capability` is required by `__post_init__` and then DROPPED, so a
    caller who somehow obtains a receipt cannot mint another from it and
    `dataclasses.replace` fails for the same reason."""
    capability: object
    schema: str
    supplement_id: str
    trial_id: str
    authorized_commit: str
    components: Mapping

    def __post_init__(self) -> None:
        if self.capability is not _CAPABILITY:
            raise SupplementProductionError(
                "production_receipt_capability_required",
                "a supplement production receipt is minted by the builder "
                "alone")
        missing = [c for c in RECEIPT_COMPONENTS if c not in self.components]
        if missing:
            raise SupplementProductionError("production_receipt_incomplete",
                                            f"missing {missing}")
        object.__setattr__(self, "components",
                           MappingProxyType(dict(self.components)))
        object.__setattr__(self, "capability", None)


@_dc.dataclass(frozen=True, slots=True)
class SupplementProduct:
    """A built supplement plus the receipt proving where it came from.

    `receipt` is `init=False`: the public constructor cannot be handed
    one, and `dataclasses.replace` skips `init=False` fields entirely, so
    a replaced product is receipt-LESS by construction. `default_factory`
    rather than a plain default is required under `slots=True` — the same
    subtlety `PreparedMCInput.battery_receipt` documents."""
    payload: Mapping
    receipt: "ProductionReceipt | None" = _dc.field(
        init=False, repr=False, compare=False, default_factory=lambda: None)

    def __post_init__(self) -> None:
        if not isinstance(self.payload, Mapping):
            raise SupplementProductionError(
                "production_payload_type",
                f"payload is {type(self.payload).__name__}, not a mapping")
        object.__setattr__(self, "payload",
                           MappingProxyType(dict(self.payload)))

    @property
    def supplement_id(self) -> str:
        return str(self.payload.get("supplement_id", ""))


def _components(authority, prepared, payload: Mapping) -> dict:
    from .consumer import prepared_digest as _prep_digest
    return {
        "authority": authority.authority_digest,
        "prepared": _prep_digest(prepared),
        "binding": _digest(dict(payload["binding"])),
        "day_universe": authority.day_universe_digest,
        "rows": payload["rows_digest"],
        "payload": hashlib.sha256(
            _ds.canonical_supplement_bytes(payload)).hexdigest(),
    }


def build_supplement_from_authority(authority, prepared, day_rows: Sequence,
                                    *, supplement_id: str | None = None,
                                    **forbidden) -> SupplementProduct:
    """PRODUCTION builder. The caller supplies the ROWS and nothing else.

    `expected_day_set` and `binding` are derived here from the authority
    (re-verified against `prepared` by N03's
    `supplement_build_inputs`), never accepted from the caller — passing
    either is a refusal, not a silently ignored keyword."""
    for name in ("expected_day_set", "binding"):
        if name in forbidden:
            raise SupplementProductionError(
                "production_decisive_argument_supplied",
                f"{name} is DERIVED from the authority; a caller may not "
                "supply it")
    if forbidden:
        raise SupplementProductionError("production_unknown_argument",
                                        f"{sorted(forbidden)}")
    # F4b (adversarial battery): the runner moved to an exact-type check
    # while this stayed `isinstance`, so a `__new__`-built SUBCLASS cleared
    # the builder's own guard and died one layer down under an
    # authority-layer code. One seam, one rule.
    if type(authority) is not _sa.SupplementAuthority:
        raise SupplementProductionError(
            "production_authority_type",
            f"{type(authority).__name__} is not exactly SupplementAuthority; "
            "a subclass or a field-compatible stand-in is not an authority")
    if authority.test_only:
        raise SupplementProductionError(
            "production_authority_test_only",
            "a test_only authority may never build a production supplement")
    sid = supplement_id or authority.supplement_id
    expected_day_set, binding = _sa.supplement_build_inputs(
        authority, prepared, supplement_id=sid)
    payload = _ds.build_day_strata_supplement_test_only(
        day_rows, expected_day_set=expected_day_set, binding=binding)
    # F6 (adversarial battery, Medium). The hermetic core stamps the
    # module-level `SUPPLEMENT_ID`, which need not be the id the authority
    # was minted for: an authority for MC-DS-S002 produced a payload
    # stamped MC-DS-S001 whose receipt said S002, and that verified. One
    # object may not carry two identities.
    stamped = str(payload.get("supplement_id", ""))
    if stamped != sid:
        raise SupplementProductionError(
            "production_supplement_id_divergence",
            f"payload is stamped {stamped!r} but the authority is for "
            f"{sid!r}")
    product = SupplementProduct(payload=payload)
    receipt = ProductionReceipt(
        capability=_CAPABILITY, schema=PRODUCTION_RECEIPT_SCHEMA,
        supplement_id=sid, trial_id=authority.trial_id,
        authorized_commit=authority.authorized_commit,
        components=_components(authority, prepared, product.payload))
    object.__setattr__(product, "receipt", receipt)
    return product


def verify_production_receipt(product, authority, prepared
                              ) -> ProductionReceipt:
    """Recompute every component from the LIVE objects and compare."""
    if not isinstance(product, SupplementProduct):
        raise SupplementProductionError(
            "production_product_type",
            f"{type(product).__name__} is not a SupplementProduct; a "
            "hand-assembled mapping is not a production product")
    receipt = product.receipt
    if receipt is None:
        raise SupplementProductionError(
            "production_not_factory_built",
            "this product carries no production receipt — it was hand-built "
            "or produced by dataclasses.replace")
    if not isinstance(authority, _sa.SupplementAuthority):
        raise SupplementProductionError("production_authority_type",
                                        type(authority).__name__)
    _sa.verify_supplement_authority(authority, prepared,
                                    supplement_id=receipt.supplement_id)
    want = _components(authority, prepared, product.payload)
    for name in RECEIPT_COMPONENTS:
        if receipt.components.get(name) != want[name]:
            raise SupplementProductionError(
                "production_receipt_mismatch",
                f"component {name!r} does not describe this product")
    if receipt.trial_id != authority.trial_id:
        raise SupplementProductionError("production_receipt_trial_mismatch",
                                        receipt.trial_id)
    if receipt.authorized_commit != authority.authorized_commit:
        raise SupplementProductionError("production_receipt_commit_mismatch",
                                        receipt.authorized_commit[:12])
    return receipt


def seal_supplement_production(product, out_dir: Path, *, authority,
                               prepared, incident_id: str):
    """PRODUCTION seal. Refuses anything the production builder did not
    make, then RE-VERIFIES the binding, the day-universe digest and the
    FULL day set before a byte is staged."""
    verify_production_receipt(product, authority, prepared)
    payload = product.payload

    binding = dict(payload["binding"])
    _, want_binding = _sa.supplement_build_inputs(
        authority, prepared, supplement_id=product.supplement_id)
    if binding != dict(want_binding):
        raise SupplementProductionError(
            "production_binding_drift",
            "the payload binding is not the one the authority derives")
    if binding["day_universe_digest"] != authority.day_universe_digest:
        raise SupplementProductionError("production_day_universe_drift",
                                        "day-universe digest moved")
    rows = payload["rows"]
    got_days = frozenset(r["trade_date"] for r in rows)
    if got_days != authority.expected_day_set:
        missing = sorted(authority.expected_day_set - got_days)[:3]
        extra = sorted(got_days - authority.expected_day_set)[:3]
        raise SupplementProductionError(
            "production_day_set_drift",
            f"missing={missing} extra={extra}")
    if payload["rows_digest"] != _ds.canonical_rows_digest(rows):
        raise SupplementProductionError("production_rows_digest_drift", "")

    # F3 (adversarial battery, High). ORDER MATTERS: the per-row check
    # runs BEFORE `_validate_supplement_object`, because a forbidden row
    # field IS the blind-guarantee violation and deserves its own name.
    # With the order reversed the specific code was dead — F7b, found by
    # the same battery INSIDE this repair.
    # F3 (adversarial battery, High). The production seal must not be
    # WEAKER than the hermetic core it replaced. `seal_supplement_test_only`
    # re-runs `_validate_supplement_object` at the seal boundary, and that
    # check IS the blind no-outcome guarantee: it refuses any row key
    # outside the four structural ones. Without it, a payload whose rows
    # each carried `"pnl": 12.5` was refused by the TEST-ONLY seal and
    # SEALED by the production one — measured, not hypothesised. Re-run it
    # here, on the exact object about to be serialised.
    for i, row in enumerate(rows):
        extra = sorted(set(row) - set(_ds.ROW_FIELDS))
        if extra:
            raise SupplementProductionError(
                "production_forbidden_row_field",
                f"row {i}: {extra} — DAY_STRATA rows carry the four "
                "structural keys ONLY; an outcome field may never ride "
                "along (blind guarantee)")
    try:
        _ds._validate_supplement_object(payload)
    except _ds.SupplementError as exc:
        raise SupplementProductionError(
            "production_supplement_object_invalid",
            f"{exc.code}: {exc}") from exc

    intended = _ds.canonical_supplement_bytes(payload)
    action = _run.resolve_partial(Path(out_dir), _ds.SUPPLEMENT_FILENAME,
                                  intended, incident_id=incident_id)
    return action, hashlib.sha256(intended).hexdigest()


SUPPLEMENT_PRODUCTION_IS_NOT_AUTHORIZATION = (
    "Building or sealing a supplement through this module is an "
    "ENGINEERING capability, not permission to run one. Execution still "
    "requires Aaron's exact authorization sentence binding the supplement "
    "id, the full 40-hex commit and the output root "
    "(ops/ND1_PROFILE_RATIFICATION.md §4).")
