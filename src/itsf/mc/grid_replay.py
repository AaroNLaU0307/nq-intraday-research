"""N11 — GRID/K replay wiring: `GridReplayAuthority` + `KReplayEvidence`.

WHAT THIS CLOSES. Until now the consumer refused the K axis outright
(`k_axis_evidence_blocked_grid_replay`): grid replay needed the per-day
`year × vol × event` stratum assignment of the WHOLE day pool, the original
S0-T001 seal never carried it (`CAN_GRID_SAMPLES_BE_RECONSTRUCTED_FROM_
CURRENT_SEAL=NO`, `MISSING_AUTHORITY=EXACT_PER_DAY_DAY_STRATA`), and so no
ACTUAL K-doubled evidence could exist — outer metadata claiming `double_K`
was pure impersonation. N09 sealed that missing authority as the Option-B
blind supplemental DAY_STRATA artifact, which is the in-source unblock
condition the consumer names ("GRID-B supplement sealed"). This module is
the other half: the typed authority minted FROM the sealed supplement, and
the typed K-dependent evidence the authority licenses.

NOTHING HERE RUNS A GRID OR AN MC. The authority is a certificate over an
already-sealed artifact; the evidence is a comparison over region maps its
producer hands in. Producing region maps at real scale is the N13 runner's
job (per M10 that is 3 seeds × {K, 2K} grid passes). This module is
structural, exercised synthetically, and reads no market data.

--------------------------------------------------------------------------
THE RATIFIED DESIGN THIS IMPLEMENTS (N-D2 items M6–M10, `RATIFIED_UNCHANGED`
by Sol under Aaron's named delegation 2026-08-24; the frozen text they rest
on is MC_METHOD_SPEC §5 and STUDY_0_PREREGISTRATION Appendix A v0.6)

  frozen §5 convergence rules
    (a) B, M and K each doubled → the decision category must not change
    (b) the three master seeds 7/13/31 agree on the category
    (c) key-quantile change ≤ max($25, relative 5%)
    (d) within-world MCSE ≤ 10% of the between-world SD
    (e) any of them unsatisfied → double and rerun; a non-converged result
        may not be used to judge

  frozen Appendix A v0.6 (prereg L289–292), the two region definitions
    positive_EV_region = {(q,r) : SOME combo has Conservative P5 > 0}
    deployable_region  = {(q,r) : the SAME combo satisfies Conservative
                          P5 > 0 AND Stress median >= 0 AND frequency /
                          integer-position / payout-path feasible}
    Both are reported; ONLY `deployable_region` may support entry into H1.

  M6 — the K-convergence OBJECT is those two per-cell classification maps,
        compared between the K and the 2K grid pass OF THE SAME SEED. It is
        explicitly NOT a Checkpoint category, because the Checkpoint layer
        does not consume K and calling it twice would be empty verification.
  M7 — the maps' ROLE: report items for Checkpoint-0 (never a kill, never a
        GO/STOP input), but their K-convergence is the grid section's OWN
        validity precondition. Not converged → per (e) double K, bounded by
        the ruled `GridRepeatPolicy.max_doublings`; while not converged the
        grid section seals as NON_CONVERGED and `deployable_region` may not
        support any H1 entry claim. The Checkpoint-0 verdict is NOT withheld.
  M8 — EQUALITY WITH A BOUNDARY BAND: the two maps must agree cell by cell;
        the only exemption is a "boundary band" cell, whose classifying
        statistics sit within the frozen (c) tolerance of zero at BOTH K and
        2K and move by no more than that same tolerance. Such cells are
        relabelled to a third class in both maps and re-compared. Any
        non-boundary-band flip = not converged. Exact equality was rejected
        as non-terminating; inventing a second tolerance was rejected as a
        new number, so the band reuses (c)'s max($25, 5%).
  M9 — rule (c) IS transplanted to the cell layer, K arm only, over the key
        set {Conservative P5, Stress median} — the classifying statistics
        themselves, because drift that has not yet flipped a class is the
        precursor to flipping. The dollar term keeps its meaning (cells are
        the same unit as §4.4, USD/calendar-month). Non-USD keys are
        configuration/identity, NOT governed by (c): they must be identical.
  M10 — quantifiers: K doubling on ALL THREE seeds; the published region is
        the INTERSECTION of the three seeds' maps, with the boundary band
        taking the UNION, and any cell the seeds classify differently lands
        in that union band and is disclosed.

--------------------------------------------------------------------------
HOW THE BAND TEST MEETS THE EXISTENTIAL — AARON'S B-25 RULING (2026-09-08).

A cell carries classifying statistics PER PRIMARY COMBINATION, and both
region definitions quantify EXISTENTIALLY over combinations. M8 speaks of
"its classifying statistic" in the singular and does not say how the band
test combines across them. Two readings survived its text: (i) every
combination must sit in the band, or (ii) only the combination that decides
the existential must. They disagree on an ordinary case — combo A stable at
−$5000 while combo B flips +$3 → −$2 — and the difference decides whether
`deployable_region` may support H1 entry, so it was referred to Aaron.

AARON RULED (ii). Boundary classification applies to the CELL-LEVEL
EXISTENTIAL REGION DECISION: a non-decisive combination must NOT veto
convergence merely because its own statistics sit outside the band. A cell
is boundary when the combination-level statistics that actually determine
its region membership lie inside the ALREADY-FROZEN M8 band.

WHICH COMBINATIONS "ACTUALLY DETERMINE" IT, mechanically. Membership is
`satisfying(cell) != empty`. A cell's class therefore changes exactly when
the SATISFYING SET changes, so the deciding combinations are the symmetric
difference `satisfying(K) XOR satisfying(2K)` — those that entered or left
the region. A combination satisfying in neither pass (combo A above) never
contributed to membership and is irrelevant; one satisfying in both cannot
coexist with a class flip. This is read off the existential itself, so the
ruling adds NO epsilon, threshold, percentage or second tolerance: the only
tolerance in this module remains `frozen_tolerance`, i.e. (c)'s
max($25, 5%), and `_in_band` is still M8's predicate unchanged.

Within a deciding combination, M8 is applied AS RATIFIED — all of that
combination's classifying statistics (Conservative P5, plus the Stress
median for `deployable_region`). The ruling narrowed WHICH COMBINATIONS are
consulted; it did not reinterpret what M8 asks of one.
"""
from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from dataclasses import fields as _dc_fields
from types import MappingProxyType
from typing import Mapping

from itsf.contracts import RESEARCH_BOOTSTRAP_SEEDS
from itsf.mc import consumer as _mcc
from itsf.mc import day_strata_supplement as _ds
from itsf.mc import supplement_authority as _sa
from itsf.mc import supplement_contract as _sc
from itsf.mc.atoms import MCInputError, canonical_json
from itsf.s0 import gridmix as _gridmix

__all__ = (
    "GRID_REPLAY_AUTHORITY_SCHEMA", "K_REPLAY_EVIDENCE_SCHEMA",
    "POSITIVE_EV_REGION", "DEPLOYABLE_REGION", "REGION_KINDS",
    "IN_REGION", "OUT_OF_REGION", "BOUNDARY_BAND",
    "GRID_CELL_KEYS", "frozen_tolerance", "CellStatistics",
    "cell_category", "satisfying_combos",
    "GridReplayAuthority", "derive_grid_replay_authority",
    "derive_grid_replay_authority_for_tests", "verify_grid_replay_authority",
    "region_map", "RegionComparison", "compare_region_maps",
    "cell_drift_violations",
    "KReplayEvidence", "derive_k_replay_evidence", "publish_region",
)

GRID_REPLAY_AUTHORITY_SCHEMA = "mc_grid_replay_authority.v1"
K_REPLAY_EVIDENCE_SCHEMA = "mc_k_replay_evidence.v1"
_AUTHORITY_DIGEST_SCHEMA = "mc_grid_replay_authority_digest.v1"
_EVIDENCE_DIGEST_SCHEMA = "mc_k_replay_evidence_digest.v1"

#: frozen Appendix A v0.6 region names — the two objects M6 makes the K
#: convergence target. Spelled exactly as the prereg spells them.
POSITIVE_EV_REGION = "positive_EV_region"
DEPLOYABLE_REGION = "deployable_region"
REGION_KINDS = (POSITIVE_EV_REGION, DEPLOYABLE_REGION)

#: cell classes. `BOUNDARY_BAND` is M8's third class — it exists so a cell
#: whose sign is below the frozen decision tolerance is labelled honestly
#: rather than forced onto one side.
IN_REGION = "in"
OUT_OF_REGION = "out"
BOUNDARY_BAND = "boundary_band"

#: The Appendix A grid, taken from `s0.gridmix` rather than re-spelled, so a
#: change to the frozen grid cannot leave this module describing a different
#: one. Keys are per-mille integers (350 == q of 0.35), never floats.
GRID_CELL_KEYS = tuple(sorted(
    (q, r) for q in _gridmix.Q_GRID_MILLIS for r in _gridmix.R_GRID_MILLIS))

#: The stratum axes the DAY_STRATA authority must carry, from the row schema
#: `day_strata_supplement` already froze (DR-2 / DR-6 vocabularies).
STRATUM_AXES = tuple(f for f in _ds.ROW_FIELDS if f != "trade_date")


def frozen_tolerance(baseline) -> float:
    """Rule (c)'s tolerance: `max($25, relative 5%)` of the BASELINE value.

    Both constants come from `consumer` (`CONV_ABS_USD` / `CONV_REL`) — the
    frozen pair is not re-spelled here. The baseline is the K-arm value,
    because (c) bounds the CHANGE from the base run; using the doubled value
    instead would let a drifting statistic widen its own tolerance.
    """
    return max(_mcc.CONV_ABS_USD, _mcc.CONV_REL * abs(float(baseline)))


def _finite(value, where: str) -> float:
    out = float(value)
    if not math.isfinite(out):
        raise MCInputError("grid_replay_cell_statistic_invalid",
                           f"{where} carries a non-finite value")
    return out


def _digest(schema: str, payload) -> str:
    return hashlib.sha256(
        canonical_json({"schema": schema, "payload": payload})
        .encode("ascii")).hexdigest()


# ---------------------------------------------------------------------------
# The authority: factory-only, unforgeable, bound to the SEALED supplement
# ---------------------------------------------------------------------------

class _GridAuthorityCapability:
    """Module-private construction capability, the pattern `consumer.
    BatteryReceipt` and `supplement_authority.SupplementAuthority` already
    use: one import-time instance, one call site, dropped once checked, so
    holding a genuine authority cannot mint a second one and
    `dataclasses.replace` (a constructor call carrying `capability=None`)
    dies at the same gate."""
    __slots__ = ()


_GRID_AUTHORITY_CAPABILITY = _GridAuthorityCapability()

#: Every value-bearing field, in the authority's self-digest preimage.
#: `capability` (dropped) and `authority_digest` (the digest itself) are
#: excluded; the payload builder refuses if this list ever drifts from the
#: dataclass, mirroring `AUTHORITY_PAYLOAD_FIELDS` next door.
GRID_AUTHORITY_PAYLOAD_FIELDS = (
    "schema", "supplement_id", "supplement_schema", "sealed_artifact_sha256",
    "rows_digest", "day_universe_digest", "n_days", "stratum_axes",
    "grid_stream_tag", "k_per_seed", "prepared_digest", "test_only")


@dataclass(frozen=True, slots=True)
class GridReplayAuthority:
    """TYPED LICENCE FOR GRID REPLAY: the binding between a sealed Option-B
    DAY_STRATA supplement and the prepared input it must belong to.

    It is a CERTIFICATE, not a permission and not an input: every field is a
    structural fact — an identifier, a digest, a count or an axis name — and
    nothing reads a field of it as authorization to run anything. What it
    certifies is exactly the audit's `MISSING_AUTHORITY`: that a per-day
    `year × vol × event` stratum assignment covering the WHOLE frozen day
    universe exists, is sealed, and belongs to this prepared input.

    Construction is FACTORY-ONLY; the two derivation entries are
    `derive_grid_replay_authority` (production) and
    `derive_grid_replay_authority_for_tests` (synthetic fixtures).
    """
    capability: object
    schema: str
    supplement_id: str
    supplement_schema: str
    sealed_artifact_sha256: str
    rows_digest: str
    day_universe_digest: str
    n_days: int
    stratum_axes: tuple
    grid_stream_tag: int
    k_per_seed: int
    prepared_digest: str
    test_only: bool
    authority_digest: str

    def __post_init__(self):
        if self.capability is not _GRID_AUTHORITY_CAPABILITY:
            raise MCInputError(
                "grid_replay_authority_capability_required",
                "GridReplayAuthority is factory-only — use "
                "derive_grid_replay_authority(); a direct constructor call "
                "or dataclasses.replace cannot mint one")
        object.__setattr__(self, "capability", None)


def _authority_payload(authority) -> dict:
    declared = {f.name for f in _dc_fields(authority)} - {
        "capability", "authority_digest"}
    if declared != set(GRID_AUTHORITY_PAYLOAD_FIELDS):
        raise MCInputError(
            "grid_replay_authority_payload_field_drift",
            f"{sorted(declared ^ set(GRID_AUTHORITY_PAYLOAD_FIELDS))}")
    payload = {}
    for name in GRID_AUTHORITY_PAYLOAD_FIELDS:
        value = getattr(authority, name)
        payload[name] = list(value) if isinstance(value, tuple) else value
    return payload


def _validated_rows(supplement) -> tuple:
    """The supplement's rows, re-validated against the FROZEN vocabularies.

    Re-validated rather than trusted: `day_strata_supplement` validated them
    when the artifact was built, but an authority minted here must not
    inherit that verdict — the whole point of the missing-authority finding
    was that a plausible-looking table is not an authority.
    """
    rows = supplement.get("rows")
    if not isinstance(rows, (list, tuple)) or not rows:
        raise MCInputError("grid_replay_supplement_rows_absent",
                           "the sealed supplement carries no rows")
    out = []
    for i, row in enumerate(rows):
        if not isinstance(row, Mapping) or set(row) != set(_ds.ROW_FIELDS):
            raise MCInputError(
                "grid_replay_supplement_row_schema_violation",
                f"row {i} keys {sorted(row) if isinstance(row, Mapping) else row!r}"
                f" != {sorted(_ds.ROW_FIELDS)}")
        if row["vol_stratum"] not in _ds.VOL_STRATA:
            raise MCInputError(
                "grid_replay_supplement_vol_stratum_violation",
                f"row {i} carries {row['vol_stratum']!r}")
        if row["event_stratum"] not in _ds.EVENT_STRATA:
            raise MCInputError(
                "grid_replay_supplement_event_stratum_violation",
                f"row {i} carries {row['event_stratum']!r}")
        out.append(dict(row))
    return tuple(out)


def _mint_authority(prepared, supplement, *, sealed_artifact_sha256: str,
                    identity, production: bool) -> GridReplayAuthority:
    """THE only minter. Both derivation entries reach it only after the
    battery receipt and the day-universe identity have been enforced."""
    rows = _validated_rows(supplement)

    # (1) COVERAGE — the audit's actual finding. Stratified sampling needs
    # every day of the frozen pool assigned; a subset is not an authority.
    # Exact set equality, so a missing day, an extra day and a duplicated
    # day each refuse with their own code rather than one vague mismatch.
    dates = [str(r["trade_date"]) for r in rows]
    if len(set(dates)) != len(dates):
        dupes = sorted({d for d in dates if dates.count(d) > 1})
        raise MCInputError("grid_replay_supplement_duplicate_day",
                           f"{len(dupes)} duplicated trade_date(s): "
                           f"{dupes[:5]}")
    universe = set(identity.day_universe)
    covered = set(dates)
    if covered != universe:
        raise MCInputError(
            "grid_replay_supplement_day_universe_incomplete",
            f"missing={len(universe - covered)} extra={len(covered - universe)}"
            f" — the per-day stratum table must cover the frozen day universe"
            f" exactly ({len(universe)} days)")

    # (2) The supplement's own binding header must name the same universe.
    binding = supplement.get("binding")
    if not isinstance(binding, Mapping):
        raise MCInputError("grid_replay_supplement_binding_absent",
                           "the sealed supplement carries no binding header")
    declared_digest = binding.get("day_universe_digest")
    recomputed = _sa.day_universe_digest(identity.day_universe)
    if declared_digest != recomputed:
        raise MCInputError(
            "grid_replay_supplement_day_universe_digest_mismatch",
            f"binding declares {str(declared_digest)[:12]}, the prepared "
            f"input's universe hashes to {recomputed[:12]}")

    # (3) Identity of the artifact itself: rows digest and sealed bytes.
    rows_digest = _ds.canonical_rows_digest(rows)
    declared_rows = supplement.get("rows_digest")
    if declared_rows is not None and declared_rows != rows_digest:
        raise MCInputError(
            "grid_replay_supplement_rows_digest_mismatch",
            f"declares {str(declared_rows)[:12]}, rows hash to "
            f"{rows_digest[:12]}")
    recomputed_bytes = hashlib.sha256(
        _ds.canonical_supplement_bytes(supplement)).hexdigest()
    if str(sealed_artifact_sha256) != recomputed_bytes:
        raise MCInputError(
            "grid_replay_sealed_artifact_sha256_mismatch",
            f"caller pinned {str(sealed_artifact_sha256)[:12]}, the "
            f"canonical bytes hash to {recomputed_bytes[:12]}")

    # (4) Vocabulary + family: the schema and a canonical supplement id.
    if supplement.get("schema") != _ds.SUPPLEMENT_SCHEMA:
        raise MCInputError(
            "grid_replay_supplement_schema_violation",
            f"{supplement.get('schema')!r} != {_ds.SUPPLEMENT_SCHEMA!r}")
    supplement_id = str(binding.get("supplement_id")
                        or supplement.get("supplement_id") or "")
    if not _sc.SUPPLEMENT_ID_PATTERN.match(supplement_id):
        raise MCInputError(
            "grid_replay_supplement_id_not_canonical",
            f"{supplement_id!r} is not a canonical supplement id")

    # (5) test_only may never be laundered. A synthetic supplement cannot
    # license a production replay, and the flag rides INTO the authority so
    # a downstream consumer can refuse on it too.
    prepared_test_only = bool(prepared.test_only)
    if production and prepared_test_only:
        raise MCInputError(
            "grid_replay_authority_test_only_prepared",
            "a test_only prepared input cannot mint a production grid "
            "replay authority")

    payload = {
        "schema": GRID_REPLAY_AUTHORITY_SCHEMA,
        "supplement_id": supplement_id,
        "supplement_schema": str(supplement.get("schema")),
        "sealed_artifact_sha256": str(sealed_artifact_sha256),
        "rows_digest": rows_digest,
        "day_universe_digest": recomputed,
        "n_days": len(universe),
        "stratum_axes": STRATUM_AXES,
        "grid_stream_tag": int(_gridmix.GRID_STREAM_TAG),
        "k_per_seed": int(prepared.k_per_seed),
        "prepared_digest": _mcc.prepared_digest(prepared),
        "test_only": (prepared_test_only or not production),
    }
    if set(payload) != set(GRID_AUTHORITY_PAYLOAD_FIELDS):
        raise MCInputError(
            "grid_replay_authority_payload_field_drift",
            f"{sorted(set(payload) ^ set(GRID_AUTHORITY_PAYLOAD_FIELDS))}")
    preimage = {k: (list(v) if isinstance(v, tuple) else v)
                for k, v in payload.items()}
    return GridReplayAuthority(
        capability=_GRID_AUTHORITY_CAPABILITY,
        authority_digest=_digest(_AUTHORITY_DIGEST_SCHEMA, preimage),
        **payload)


def _derive_impl(prepared, supplement, *, sealed_artifact_sha256: str,
                 production: bool) -> GridReplayAuthority:
    if not isinstance(prepared, _mcc.PreparedMCInput):
        raise MCInputError(
            "grid_replay_prepared_input_required",
            f"{type(prepared).__name__} is not a PreparedMCInput — the "
            "authority binds to the battery's own product, never to a "
            "caller-assembled look-alike")
    # The battery receipt first: it is what proves this prepared input came
    # out of the ten-check battery rather than being hand-built.
    _mcc.verify_battery_receipt(prepared)
    if not isinstance(supplement, Mapping):
        raise MCInputError("grid_replay_supplement_required",
                           f"{type(supplement).__name__} is not a mapping")
    if int(prepared.k_per_seed) != _mcc.K_PER_SEED_FROZEN:
        raise MCInputError(
            "grid_replay_k_per_seed_not_frozen",
            f"prepared carries k_per_seed={prepared.k_per_seed}, frozen is "
            f"{_mcc.K_PER_SEED_FROZEN}")
    # §D.2.2 day-universe identity, INDEPENDENTLY re-derived (not the
    # battery's earlier verdict) — the same call the supplement build path
    # uses, so the authority and the artifact cannot disagree about which
    # day universe they mean.
    identity = _sa.enforce_day_universe_identity(prepared)
    return _mint_authority(prepared, supplement,
                           sealed_artifact_sha256=sealed_artifact_sha256,
                           identity=identity, production=production)


def derive_grid_replay_authority(prepared, supplement, *,
                                 sealed_artifact_sha256: str
                                 ) -> GridReplayAuthority:
    """PRODUCTION entry: mint the authority from a SEALED supplement.

    `supplement` is the already-sealed artifact's parsed object and
    `sealed_artifact_sha256` the hash it was sealed under; this function
    re-hashes the canonical bytes and refuses a mismatch, so a caller cannot
    pin one artifact and hand over another. Nothing here opens a path, reads
    market data or appends a registry row.
    """
    return _derive_impl(prepared, supplement,
                        sealed_artifact_sha256=sealed_artifact_sha256,
                        production=True)


def derive_grid_replay_authority_for_tests(prepared, supplement, *,
                                           sealed_artifact_sha256: str
                                           ) -> GridReplayAuthority:
    """Synthetic-fixture entry. Identical checks; the minted authority is
    marked `test_only=True` whatever the prepared input says, so a synthetic
    authority is visibly synthetic downstream."""
    return _derive_impl(prepared, supplement,
                        sealed_artifact_sha256=sealed_artifact_sha256,
                        production=False)


def verify_grid_replay_authority(authority) -> GridReplayAuthority:
    """Re-check an authority's self-digest. Cheap, and it is what lets a
    consumer refuse a mutated certificate without re-deriving it."""
    if type(authority) is not GridReplayAuthority:
        raise MCInputError(
            "grid_replay_authority_required",
            f"{type(authority).__name__} is not a GridReplayAuthority")
    expect = _digest(_AUTHORITY_DIGEST_SCHEMA, _authority_payload(authority))
    if authority.authority_digest != expect:
        raise MCInputError(
            "grid_replay_authority_digest_mismatch",
            f"carries {authority.authority_digest[:12]}, its own fields hash "
            f"to {expect[:12]}")
    if authority.schema != GRID_REPLAY_AUTHORITY_SCHEMA:
        raise MCInputError("grid_replay_authority_schema_violation",
                           f"{authority.schema!r}")
    return authority


# ---------------------------------------------------------------------------
# Cells and the two frozen region maps
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class CellStatistics:
    """One (q_mil, r_mil) cell's CLASSIFYING statistics, per Primary combo.

    `conservative_p5` and `stress_median` are the two statistics Appendix A
    classifies on, in §4.4's unit (USD per calendar month), so rule (c)'s
    dollar term applies to them unchanged (M9b). `feasible` is the frozen
    third conjunct of `deployable_region`; `None` is the repository's
    explicit PENDING semantics, never a silent False. `identity` holds the
    NON-USD keys (realized precision/recall, sample counts, ...) which M9
    exempts from (c) and requires to be identical K → 2K.
    """
    conservative_p5: Mapping
    stress_median: Mapping
    feasible: Mapping
    identity: Mapping = MappingProxyType({})

    def __post_init__(self):
        combos = set(self.conservative_p5)
        if not combos:
            raise MCInputError("grid_replay_cell_no_combination",
                               "a cell must carry at least one combination")
        for name, mapping in (("stress_median", self.stress_median),
                              ("feasible", self.feasible)):
            if set(mapping) != combos:
                raise MCInputError(
                    "grid_replay_cell_combination_set_mismatch",
                    f"{name} covers {sorted(set(mapping) ^ combos)} "
                    "differently from conservative_p5")
        for cid in combos:
            _finite(self.conservative_p5[cid], f"conservative_p5[{cid}]")
            _finite(self.stress_median[cid], f"stress_median[{cid}]")
            flag = self.feasible[cid]
            if flag is not None and type(flag) is not bool:
                raise MCInputError(
                    "grid_replay_cell_feasibility_invalid",
                    f"feasible[{cid}] carries {type(flag).__name__} — only "
                    "True, False or None (PENDING) are legal")
        object.__setattr__(self, "conservative_p5",
                           MappingProxyType(dict(self.conservative_p5)))
        object.__setattr__(self, "stress_median",
                           MappingProxyType(dict(self.stress_median)))
        object.__setattr__(self, "feasible",
                           MappingProxyType(dict(self.feasible)))
        object.__setattr__(self, "identity",
                           MappingProxyType(dict(self.identity)))

    def classifying_values(self, kind: str, combos=None) -> tuple:
        """The statistics `kind` classifies on, as ((label, value), ...).

        positive_EV_region reads Conservative P5 alone; deployable_region
        additionally reads the Stress median (M8's parenthesis).

        `combos` restricts the result to the named combinations. M8's band
        test passes the DECIDING combinations (B-25, ruled (ii)); passing
        None keeps every combination, which is what rule (c) wants — (c)
        governs drift per statistic and has nothing to do with which
        combination decides the existential.
        """
        _require_kind(kind)
        keys = (sorted(self.conservative_p5) if combos is None
                else sorted(c for c in self.conservative_p5 if c in combos))
        out = [(f"conservative_p5[{cid}]", float(self.conservative_p5[cid]))
               for cid in keys]
        if kind == DEPLOYABLE_REGION:
            out += [(f"stress_median[{cid}]", float(self.stress_median[cid]))
                    for cid in keys]
        return tuple(out)


def _require_kind(kind: str) -> str:
    if kind not in REGION_KINDS:
        raise MCInputError("grid_replay_region_kind_unknown",
                           f"{kind!r} is not one of {list(REGION_KINDS)}")
    return kind


def cell_category(cell, kind: str) -> str:
    """Classify ONE cell by the FROZEN Appendix A v0.6 definition.

    positive_EV_region : SOME combo has Conservative P5 > 0.
    deployable_region  : the SAME combo has Conservative P5 > 0 AND Stress
                         median >= 0 AND is feasible.

    Note the asymmetry is the prereg's, not a choice made here: P5 is
    strictly positive, the Stress median is `>= 0`.

    A cell whose deployable verdict turns on a combo with `feasible=None`
    REFUSES. That combo might be the existential witness, so answering
    either way would be inventing a feasibility verdict the gate has not
    issued — `qualifying_distribution_vs_payout_requirements` is still
    DECISION_REQUIRED.
    """
    return (IN_REGION if satisfying_combos(cell, kind) else OUT_OF_REGION)


def satisfying_combos(cell, kind: str) -> frozenset:
    """The combinations that satisfy `kind`'s FROZEN per-combination
    predicate — the witnesses of Appendix A's existential.

    THE single source of both the cell's class (`cell_category` is just
    "is this set non-empty") and, per Aaron's B-25 ruling, of which
    combinations decide a class change. Deriving both from one function is
    what keeps "decisive" honest: a combination is decisive exactly when
    its membership in THIS set differs between the two passes.
    """
    _require_kind(kind)
    if type(cell) is not CellStatistics:
        raise MCInputError("grid_replay_cell_required",
                           f"{type(cell).__name__} is not a CellStatistics")
    if kind == POSITIVE_EV_REGION:
        return frozenset(cid for cid, v in cell.conservative_p5.items()
                         if float(v) > 0.0)
    satisfying, pending = set(), []
    for cid in sorted(cell.conservative_p5):
        ev_met = (float(cell.conservative_p5[cid]) > 0.0
                  and float(cell.stress_median[cid]) >= 0.0)
        if not ev_met:
            continue
        if cell.feasible[cid] is None:
            pending.append(cid)
        elif cell.feasible[cid]:
            satisfying.add(cid)
    if pending and not satisfying:
        raise MCInputError(
            "deployable_region_feasibility_pending",
            f"combination(s) {pending} meet the frozen EV evidence but carry "
            "feasible=None (PENDING) — the deployable region cannot be "
            "formed while the feasibility verdict is undecided")
    return frozenset(satisfying)


def region_map(cells: Mapping, kind: str) -> Mapping:
    """The per-cell classification map for one grid pass.

    The cell key set must be EXACTLY the frozen Appendix A grid: a partial
    grid is the same class of defect as a partial day universe — it looks
    like a map and silently narrows what "the region" means.
    """
    _require_kind(kind)
    if not isinstance(cells, Mapping):
        raise MCInputError("grid_replay_cells_required",
                           f"{type(cells).__name__} is not a mapping")
    keys = {tuple(k) for k in cells}
    if keys != set(GRID_CELL_KEYS):
        raise MCInputError(
            "grid_replay_grid_incomplete",
            f"missing={len(set(GRID_CELL_KEYS) - keys)} "
            f"extra={len(keys - set(GRID_CELL_KEYS))} — the map must cover "
            f"all {len(GRID_CELL_KEYS)} frozen Appendix A cells")
    return MappingProxyType({tuple(k): cell_category(cells[k], kind)
                             for k in cells})


# ---------------------------------------------------------------------------
# M8 — equality with a boundary band
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class RegionComparison:
    """The result of comparing one region kind between the K and 2K passes."""
    kind: str
    k: int
    k_doubled: int
    converged: bool
    boundary_band_cells: tuple
    flipped_cells: tuple
    drift_violations: tuple
    map_at_k: Mapping
    map_at_2k: Mapping


def _in_band(v_k: float, v_2k: float) -> bool:
    """M8's boundary-band predicate for ONE statistic: hugging zero at both
    K and 2K, and moving by no more than the same frozen tolerance."""
    tol = frozen_tolerance(v_k)
    return (abs(v_k) <= tol and abs(v_2k) <= tol and abs(v_2k - v_k) <= tol)


def compare_region_maps(kind: str, cells_at_k: Mapping, cells_at_2k: Mapping,
                        *, k: int, k_doubled: int) -> RegionComparison:
    """M8: the two maps must agree cell by cell, boundary-band cells exempt.

    A flipped cell is exempt when the combinations that DECIDE its region
    membership all sit in the frozen band (Aaron's B-25 ruling, (ii)); a
    combination that satisfied the region in neither pass is irrelevant to
    that decision and cannot veto it. See this module's docstring.
    """
    _require_kind(kind)
    if int(k_doubled) != 2 * int(k):
        raise MCInputError("grid_replay_k_doubling_violation",
                           f"k_doubled={k_doubled} is not 2 x k={k}")
    map_k = region_map(cells_at_k, kind)
    map_2k = region_map(cells_at_2k, kind)

    band, flipped = [], []
    for key in GRID_CELL_KEYS:
        cell_k, cell_2k = cells_at_k[key], cells_at_2k[key]
        # M9's identity clause is checked here too, because a cell whose
        # configuration changed between passes is not the same cell and
        # comparing its class would be meaningless.
        if set(cell_k.identity) != set(cell_2k.identity):
            raise MCInputError(
                "grid_replay_cell_identity_key_set_mismatch",
                f"cell {key} identity keys differ between K and 2K")
        for name in sorted(cell_k.identity):
            if cell_k.identity[name] != cell_2k.identity[name]:
                raise MCInputError(
                    "grid_replay_cell_identity_mismatch",
                    f"cell {key} identity key {name!r} is not identical "
                    "K -> 2K; non-USD keys are configuration, not statistics")
        if map_k[key] == map_2k[key]:
            continue
        # The class flipped, so it is exempt only as a boundary-band cell.
        # B-25 (Aaron, ruled (ii)): consult the combinations that ACTUALLY
        # DETERMINE membership — the ones that entered or left the region —
        # and no others. A combination satisfying in neither pass never
        # contributed to membership and may not veto convergence.
        deciding = (satisfying_combos(cell_k, kind)
                    ^ satisfying_combos(cell_2k, kind))
        stats_k = dict(cell_k.classifying_values(kind, deciding))
        stats_2k = dict(cell_2k.classifying_values(kind, deciding))
        if set(stats_k) != set(stats_2k):
            raise MCInputError(
                "grid_replay_cell_combination_set_mismatch",
                f"cell {key} carries different combinations at K and 2K")
        # Within a deciding combination M8 is unchanged: ALL of its
        # classifying statistics must sit in the frozen band.
        if stats_k and all(_in_band(stats_k[name], stats_2k[name])
                           for name in stats_k):
            band.append(key)
        else:
            flipped.append(key)

    relabelled_k = dict(map_k)
    relabelled_2k = dict(map_2k)
    for key in band:
        relabelled_k[key] = BOUNDARY_BAND
        relabelled_2k[key] = BOUNDARY_BAND
    # M8: after relabelling, the maps must STILL be equal cell by cell.
    residual = [key for key in GRID_CELL_KEYS
                if relabelled_k[key] != relabelled_2k[key]]
    # M9 rides along: (c) and M8 are both convergence rules and (e) gives
    # them the same consequence, so one object reports both.
    drift = cell_drift_violations(kind, cells_at_k, cells_at_2k)
    return RegionComparison(
        kind=kind, k=int(k), k_doubled=int(k_doubled),
        converged=(not residual and not drift),
        boundary_band_cells=tuple(band), flipped_cells=tuple(residual),
        drift_violations=drift,
        map_at_k=MappingProxyType(relabelled_k),
        map_at_2k=MappingProxyType(relabelled_2k))


def cell_drift_violations(kind: str, cells_at_k: Mapping,
                          cells_at_2k: Mapping) -> tuple:
    """M9: rule (c) transplanted to the cell layer, K arm only.

    Returns the statistics that moved by more than max($25, 5%), as
    ((cell_key, statistic_name), ...) — it does NOT raise. A failed (c) is
    a CONVERGENCE outcome, not a malformed input: per (e) the response is
    to double K and rerun, which is what a False convergence flag records.
    `ConvergenceReport.quantile_drift_ok` is a bool at the Checkpoint layer
    for exactly the same reason.

    Drift that has not yet flipped a class is the precursor to flipping, so
    (c) reports it explicitly rather than waiting for M8 to notice.
    """
    _require_kind(kind)
    violations = []
    for key in GRID_CELL_KEYS:
        stats_k = dict(cells_at_k[key].classifying_values(kind))
        stats_2k = dict(cells_at_2k[key].classifying_values(kind))
        for name in sorted(stats_k):
            v_k, v_2k = stats_k[name], stats_2k[name]
            if abs(v_2k - v_k) > frozen_tolerance(v_k):
                violations.append((key, name))
    return tuple(violations)


# ---------------------------------------------------------------------------
# KReplayEvidence — the inner K witness
# ---------------------------------------------------------------------------

class _KEvidenceCapability:
    """Same capability pattern as the authority: factory-only construction."""
    __slots__ = ()


_K_EVIDENCE_CAPABILITY = _KEvidenceCapability()

K_EVIDENCE_PAYLOAD_FIELDS = (
    "schema", "authority_digest", "master_seed", "k", "k_doubled",
    "prepared_digest", "converged_by_kind", "boundary_band_by_kind",
    "flipped_by_kind", "drift_violations_by_kind",
    "region_map_digest_by_kind", "test_only")


@dataclass(frozen=True, slots=True)
class KReplayEvidence:
    """THE K-dependent evidence object M6 asked for, and the INNER WITNESS
    the outer `RunEvidence.K` is bound to.

    Why the witness lives here and not in the atom layer: K is inner random
    source (2) of MC §5, "TP/FP stratified sampling, K repeats, GRID ANALYSIS
    ONLY". The epistemic layer is B worlds x M start phases and does not
    consume K at all, so there is no honest K field to put on
    `EpistemicResult` / `ObservationSet` / `SimulationPathObservation` — a K
    field there would be decoration. The witness that a K-doubled pass
    actually happened is the pair of region maps, and that is what this
    object carries: an outer `K` can no longer be asserted, it has to match
    a comparison that was actually computed from two grid passes.

    `converged_by_kind` is a REPORT, not a gate on the Checkpoint-0 verdict
    (M7). A False entry seals the grid section NON_CONVERGED and withdraws
    `deployable_region`'s right to support H1 entry; it does not withhold
    the Checkpoint-0 verdict, which takes no grid input.
    """
    capability: object
    schema: str
    authority_digest: str
    master_seed: int
    k: int
    k_doubled: int
    prepared_digest: str
    converged_by_kind: Mapping
    boundary_band_by_kind: Mapping
    flipped_by_kind: Mapping
    drift_violations_by_kind: Mapping
    region_map_digest_by_kind: Mapping
    test_only: bool
    evidence_digest: str

    def __post_init__(self):
        if self.capability is not _K_EVIDENCE_CAPABILITY:
            raise MCInputError(
                "k_replay_evidence_capability_required",
                "KReplayEvidence is factory-only — use "
                "derive_k_replay_evidence()")
        object.__setattr__(self, "capability", None)
        for name in ("converged_by_kind", "boundary_band_by_kind",
                     "flipped_by_kind", "drift_violations_by_kind",
                     "region_map_digest_by_kind"):
            object.__setattr__(self, name,
                               MappingProxyType(dict(getattr(self, name))))

    @property
    def grid_converged(self) -> bool:
        """True only when BOTH frozen regions converged."""
        return all(bool(v) for v in self.converged_by_kind.values())

    @property
    def grid_seal_status(self) -> str:
        return "CONVERGED" if self.grid_converged else "NON_CONVERGED"

    @property
    def may_support_h1_entry(self) -> bool:
        """M7: only a converged `deployable_region` may support H1 entry."""
        return bool(self.converged_by_kind.get(DEPLOYABLE_REGION))


def _k_evidence_payload(evidence) -> dict:
    declared = {f.name for f in _dc_fields(evidence)} - {
        "capability", "evidence_digest"}
    if declared != set(K_EVIDENCE_PAYLOAD_FIELDS):
        raise MCInputError(
            "k_replay_evidence_payload_field_drift",
            f"{sorted(declared ^ set(K_EVIDENCE_PAYLOAD_FIELDS))}")
    payload = {}
    for name in K_EVIDENCE_PAYLOAD_FIELDS:
        value = getattr(evidence, name)
        if isinstance(value, Mapping):
            payload[name] = {str(k): (list(v) if isinstance(v, tuple) else v)
                             for k, v in sorted(value.items())}
        elif isinstance(value, tuple):
            payload[name] = list(value)
        else:
            payload[name] = value
    return payload


def derive_k_replay_evidence(authority, *, master_seed: int,
                             cells_at_k: Mapping, cells_at_2k: Mapping,
                             k: int | None = None,
                             k_doubled: int | None = None) -> KReplayEvidence:
    """THE only minter: compare the two grid passes and certify the result.

    The comparison is performed HERE, from the supplied cells, so an
    evidence object cannot carry a convergence claim that was never computed.
    `k` defaults to the authority's frozen `k_per_seed`.
    """
    verify_grid_replay_authority(authority)
    if master_seed not in RESEARCH_BOOTSTRAP_SEEDS:
        raise MCInputError(
            "k_replay_evidence_seed_not_research_seed",
            f"{master_seed!r} is not one of {list(RESEARCH_BOOTSTRAP_SEEDS)}")
    k = int(authority.k_per_seed if k is None else k)
    if k != _mcc.K_PER_SEED_FROZEN:
        raise MCInputError("grid_replay_k_per_seed_not_frozen",
                           f"k={k}, frozen is {_mcc.K_PER_SEED_FROZEN}")
    k_doubled = int(2 * k if k_doubled is None else k_doubled)

    converged, band, flipped, drift, digests = {}, {}, {}, {}, {}
    for kind in REGION_KINDS:
        comparison = compare_region_maps(kind, cells_at_k, cells_at_2k,
                                         k=k, k_doubled=k_doubled)
        converged[kind] = comparison.converged
        band[kind] = comparison.boundary_band_cells
        flipped[kind] = comparison.flipped_cells
        drift[kind] = comparison.drift_violations
        digests[kind] = _digest(
            "mc_region_map.v1",
            {"kind": kind,
             "at_k": [[list(key), comparison.map_at_k[key]]
                      for key in GRID_CELL_KEYS],
             "at_2k": [[list(key), comparison.map_at_2k[key]]
                       for key in GRID_CELL_KEYS]})

    payload = {
        "schema": K_REPLAY_EVIDENCE_SCHEMA,
        "authority_digest": authority.authority_digest,
        "master_seed": int(master_seed),
        "k": k,
        "k_doubled": k_doubled,
        "prepared_digest": authority.prepared_digest,
        "converged_by_kind": converged,
        "boundary_band_by_kind": band,
        "flipped_by_kind": flipped,
        "drift_violations_by_kind": drift,
        "region_map_digest_by_kind": digests,
        "test_only": bool(authority.test_only),
    }
    preimage = {}
    for name in K_EVIDENCE_PAYLOAD_FIELDS:
        value = payload[name]
        if isinstance(value, dict):
            preimage[name] = {
                str(kk): ([list(x) for x in vv] if isinstance(vv, tuple)
                          else vv)
                for kk, vv in sorted(value.items())}
        else:
            preimage[name] = value
    return KReplayEvidence(
        capability=_K_EVIDENCE_CAPABILITY,
        evidence_digest=_digest(_EVIDENCE_DIGEST_SCHEMA, preimage),
        **payload)


def verify_k_replay_evidence(evidence) -> KReplayEvidence:
    """Re-check the evidence's self-digest, so a mutated witness refuses."""
    if type(evidence) is not KReplayEvidence:
        raise MCInputError(
            "k_replay_evidence_required",
            f"{type(evidence).__name__} is not a KReplayEvidence")
    expect = _digest(_EVIDENCE_DIGEST_SCHEMA, _k_evidence_payload(evidence))
    if evidence.evidence_digest != expect:
        raise MCInputError(
            "k_replay_evidence_digest_mismatch",
            f"carries {evidence.evidence_digest[:12]}, its own fields hash to "
            f"{expect[:12]}")
    return evidence


# ---------------------------------------------------------------------------
# M10 — the published, cross-seed region
# ---------------------------------------------------------------------------

def publish_region(kind: str, maps_by_seed: Mapping) -> Mapping:
    """M10(c): the published region is the INTERSECTION of the three seeds'
    maps; the boundary band takes the UNION, and any cell the seeds classify
    differently lands in that union band and is thereby disclosed rather
    than resolved by majority.

    Requires exactly the three research seeds — a two-seed publication would
    quietly weaken rule (b).
    """
    _require_kind(kind)
    if set(maps_by_seed) != set(RESEARCH_BOOTSTRAP_SEEDS):
        raise MCInputError(
            "grid_replay_cross_seed_set_incomplete",
            f"{sorted(maps_by_seed)} != {list(RESEARCH_BOOTSTRAP_SEEDS)}")
    published = {}
    for key in GRID_CELL_KEYS:
        classes = set()
        for seed in RESEARCH_BOOTSTRAP_SEEDS:
            seed_map = maps_by_seed[seed]
            if tuple(key) not in seed_map:
                raise MCInputError(
                    "grid_replay_cross_seed_cell_absent",
                    f"seed {seed} has no cell {key}")
            classes.add(seed_map[tuple(key)])
        if classes == {IN_REGION}:
            published[tuple(key)] = IN_REGION          # intersection
        elif classes == {OUT_OF_REGION}:
            published[tuple(key)] = OUT_OF_REGION
        else:
            # disagreement, or any seed already in the band -> union band
            published[tuple(key)] = BOUNDARY_BAND
    return MappingProxyType(published)
