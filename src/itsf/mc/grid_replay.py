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

HOW THAT IS APPLIED, mechanically, IN TWO ORDERED STEPS.

STEP 1 — the CELL-LEVEL existential decision, and nothing else, decides
whether M8 is engaged at all. Membership is `satisfying(cell) != empty`, so
`compare_region_maps` compares the two CLASSES first and moves on when they
agree. WITNESS SUBSTITUTION IS THEREFORE NOT A BOUNDARY EVENT: a cell whose
support moves from combination A to combination B — `satisfying(K) = {A}`,
`satisfying(2K) = {B}`, IN at both passes — has an identical class, so M8 is
never reached. The satisfying SET changed and the cell's MEMBERSHIP did not,
and B-25 governs membership. (An earlier draft of this docstring claimed a
cell's class "changes exactly when the satisfying set changes". That is
false, and the counterexample above is why; the CODE has always compared
classes first, so only this description was wrong. Pinned now by
`test_b25_caseA_witness_substitution_is_not_an_existential_crossing`.)

STEP 2 — only once the class actually changed are the deciding combinations
identified, and there the symmetric difference `satisfying(K) XOR
satisfying(2K)` is exact: a class flip means one of the two sets is empty,
so the XOR is precisely the combinations that entered or left the region. A
combination satisfying in neither pass (combo A in Aaron's case) never
contributed to membership and is irrelevant; one satisfying in both cannot
coexist with a flip.

Combination-level movement that does NOT change membership is not waved
through — it is simply not M8's business. Rule (c) still measures every
combination's drift, so the witness-substitution cell above is reported as
non-converged by (c) on its own.

Both steps are read off the existential itself, so the ruling adds NO
epsilon, threshold, percentage or second tolerance: the only tolerance in
this module remains `frozen_tolerance`, i.e. (c)'s max($25, 5%), and
`_in_band` is still M8's predicate unchanged.

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
    "GRID_CONVERGENCE_SCHEMA", "GridConvergenceAcrossSeeds",
    "aggregate_k_replay_evidence", "verify_grid_convergence",
    "per_seed_grid_report", "MARKED_CELL_FIELDS", "SAMPLED_CELL_FIELDS",
    "GRID_PASS_SCHEMA", "GridPass", "verify_grid_pass", "grid_pass_for_tests",
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
#: N13-F1. The SEALED preregistration's fourth class, spelled with its own
#: token: 「全部层合计仍不足时，该网格点标记 `infeasible_by_sample` 跳过并
#: 完整报告」 — when all strata together still fall short, MARK the grid
#: point, SKIP it, REPORT it in full. It is a class rather than a flavour of
#: OUT because "we evaluated this cell and no combination cleared zero" and
#: "this cell was never sampleable" are different facts, and a region map
#: that renders them the same has lost the one the seal asked to be reported.
INFEASIBLE_BY_SAMPLE = "infeasible_by_sample"
CELL_CLASSES = (IN_REGION, OUT_OF_REGION, BOUNDARY_BAND, INFEASIBLE_BY_SAMPLE)

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

    # (2) THE BINDING HEADER MUST NAME THIS PREPARED INPUT -- every field.
    #
    # It used to check one: the day-universe digest. That admitted a
    # supplement built for a DIFFERENT sealed run whose day universe happened
    # to match -- a foreign trial id, a foreign authorized commit and a
    # foreign source-input digest rode straight into the authority, and
    # recomputing the artifact's own hash over the foreign values made it
    # look consistent. A self-hash proves the bytes hash to what they claim;
    # it cannot prove whose bytes they are.
    #
    # The comparison is `supplement_authority`'s, not a second copy of it:
    # that module already performs exactly this check for its own authority
    # object, and two implementations of one rule drift.
    binding = supplement.get("binding")
    if not isinstance(binding, Mapping):
        raise MCInputError("grid_replay_supplement_binding_absent",
                           "the sealed supplement carries no binding header")
    recomputed = _sa.day_universe_digest(identity.day_universe)
    declared_digest = binding.get("day_universe_digest")
    if declared_digest != recomputed:
        # kept ahead of the general check so this one field keeps its own
        # refusal code: it is the coverage question, and it is worth naming
        raise MCInputError(
            "grid_replay_supplement_day_universe_digest_mismatch",
            f"binding declares {str(declared_digest)[:12]}, the prepared "
            f"input's universe hashes to {recomputed[:12]}")
    try:
        _sa.verify_supplement_binding(binding, prepared, identity=identity)
    except _sa.SupplementError as exc:
        raise MCInputError(
            "grid_replay_supplement_binding_mismatch",
            "%s: %s" % (exc.code, exc)) from exc

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


@dataclass(frozen=True, slots=True)
class InfeasibleCell:
    """N13-F1 — a grid point the SEALED rule MARKS, SKIPS and REPORTS in full.

    It deliberately carries NO statistics and no `identity`. That is the whole
    design: `CellStatistics.__post_init__` demands at least one combination
    and finite values for every one of them, so there is no way to express
    "this cell was never sampleable" as a `CellStatistics` without inventing a
    P5, a median or a feasibility verdict. Rather than weaken that guard, an
    unsampleable cell gets its own type, and every consumer that assumed
    statistics now says so explicitly (`is_infeasible`).

    It carries exactly what "report in full" needs to be auditable: which
    cell, which seed, which pass, why, and the frozen arithmetic that decided
    it — `n_fp` demanded against `fp_available` held. `s0.gridmix._grid_point`
    reports the same facts one layer down (`infeasible_by_sample` plus
    `infeasible_reason`) and this mirrors it rather than inventing a second
    vocabulary.
    """
    reason: str
    q_mil: int
    r_mil: int
    master_seed: int
    doublings: int
    n_tp: int
    n_fp: int
    fp_available: int
    detail: str

    def __post_init__(self):
        if self.reason != INFEASIBLE_BY_SAMPLE:
            raise MCInputError(
                "grid_replay_infeasible_reason_unknown",
                f"{self.reason!r} is not {INFEASIBLE_BY_SAMPLE!r}; this type "
                "exists for the ONE state the sealed rule names, and reusing "
                "it for another would make the mark mean less than it says")


def is_infeasible(cell) -> bool:
    """Is this cell the sealed marked-and-skipped kind?

    Exact-type, not `isinstance`, for the same reason `satisfying_combos`
    checks `type(cell) is not CellStatistics`: a subclass could carry
    statistics and would then be read as a valid ruled cell by half the
    consumers and a skipped one by the other half.
    """
    return type(cell) is InfeasibleCell


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

    N13-F1: a cell the sealed rule marked and skipped classifies as
    `INFEASIBLE_BY_SAMPLE`. Not OUT — Appendix A's existential over an empty
    witness set is vacuously false, so OUT would be *arithmetically* defensible
    and would still be the wrong report: it would say "evaluated, nothing
    cleared zero" about a cell that was never sampled. The seal asked for the
    mark to be reported, so the mark is what the map carries.
    """
    _require_kind(kind)
    if is_infeasible(cell):
        return INFEASIBLE_BY_SAMPLE
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
        # N13-F1, BEFORE the identity clause: a marked-and-skipped cell has
        # no `identity` and no statistics, so every comparison below is
        # undefined for it rather than merely awkward.
        #
        # The sealed infeasibility test is `n_fp > sum(fp_available)`, whose
        # terms are the (q, r) quotas and the aggregate pool — neither depends
        # on k. So a cell marked at K is marked at 2K, the classes agree, and
        # there is nothing to compare: that is the whole handling.
        #
        # If the classes DISAGREE, one pass sampled a cell the other could
        # not. That should be unreachable, and it is exactly why it is not
        # silently banded: `residual` below picks it up from the relabelled
        # maps and reports it as flipped, so convergence goes False and a
        # human sees it. Fail closed rather than assume the arithmetic.
        if is_infeasible(cell_k) or is_infeasible(cell_2k):
            continue
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
        # STEP 1 (B-25): the CELL-LEVEL existential decision gates M8. Equal
        # classes end it here — witness substitution ({A} -> {B}, IN -> IN)
        # is not a boundary event, however much the satisfying set moved.
        if map_k[key] == map_2k[key]:
            continue
        # STEP 2: the class flipped, so it is exempt only as a boundary cell.
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
        # N13-F1: a marked-and-skipped cell produced no statistic, so it has
        # nothing that could drift. Skipping it is not an exemption from (c)
        # — there is no measurement to hold to the tolerance.
        if is_infeasible(cells_at_k[key]) or is_infeasible(cells_at_2k[key]):
            continue
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
    "region_map_digest_by_kind", "adjusted_map_by_kind", "test_only")


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
    #: THE COMPARISON-ADJUSTED MAP AT K, per kind, as an ordered tuple of
    #: ((q_mil, r_mil), class) pairs.
    #:
    #: M8 relabels a boundary-band cell in BOTH maps and re-compares; that
    #: relabelling is the comparison's product and it used to live only inside
    #: `region_map_digest_by_kind`, where nothing could read it. Publication
    #: therefore rebuilt its own maps from the raw K pass and silently dropped
    #: every band cell -- the third frozen class vanished between the
    #: comparison that created it and the result that reports it. Carrying the
    #: adjusted map here is what lets publication consume the comparison
    #: instead of re-deriving something else.
    adjusted_map_by_kind: Mapping
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
                     "region_map_digest_by_kind", "adjusted_map_by_kind"):
            object.__setattr__(self, name,
                               MappingProxyType(dict(getattr(self, name))))

    def adjusted_map(self, kind: str) -> Mapping:
        """The comparison-adjusted map for `kind`, keyed by cell.

        Stored as ordered pairs so the payload stays JSON-shaped for the
        self-digest, and rebuilt here so a consumer never has to know that.
        """
        _require_kind(kind)
        rows = self.adjusted_map_by_kind.get(kind)
        if not rows:
            raise MCInputError(
                "k_replay_evidence_adjusted_map_absent",
                f"the witness carries no adjusted map for {kind!r}")
        return MappingProxyType({tuple(key): cls for key, cls in rows})

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
            payload[name] = {str(k): _jsonable(v)
                             for k, v in sorted(value.items())}
        else:
            payload[name] = _jsonable(value)
    return payload


def derive_k_replay_evidence(authority, *, master_seed: int,
                             cells_at_k, cells_at_2k,
                             k: int | None = None,
                             k_doubled: int | None = None) -> KReplayEvidence:
    """THE only minter: compare the two grid passes and certify the result.

    The comparison is performed HERE, from the supplied passes, so an
    evidence object cannot carry a convergence claim that was never computed.
    `k` defaults to the authority's frozen `k_per_seed`.

    THE ARMS ARE `GridPass` OBJECTS, not mappings of cells, and that is the
    F04 repair. A mapping could be built by hand: `CellStatistics` is public
    and validates only shape and finiteness, so invented statistics used to
    mint a witness that verified perfectly and sealed CONVERGED. A pass can
    only come from the governed producer, carries the authority and prepared
    input it was produced under, and re-verifies its digest against its own
    live cells here -- so neither the identity nor the statistics can be
    substituted after production.
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

    # THE ARMS MUST BE THE GOVERNED PRODUCER'S. Placed after the seed and k
    # refusals above so every existing refusal keeps its code and its order;
    # what is new is that a mapping of cells is no longer admissible at all.
    at_k = verify_grid_pass(cells_at_k)
    at_2k = verify_grid_pass(cells_at_2k)
    for arm, pass_ in (("K", at_k), ("2K", at_2k)):
        if pass_.authority_digest != authority.authority_digest:
            raise MCInputError(
                "k_replay_evidence_pass_authority_mismatch",
                f"the {arm} pass was produced under authority "
                f"{pass_.authority_digest[:12]}, not {authority.authority_digest[:12]}")
        if pass_.master_seed != int(master_seed):
            raise MCInputError(
                "k_replay_evidence_pass_seed_mismatch",
                f"the {arm} pass carries master_seed={pass_.master_seed}, "
                f"the witness is being minted for {master_seed}")
        if pass_.test_only is not bool(authority.test_only):
            raise MCInputError(
                "k_replay_evidence_pass_test_only_mismatch",
                f"the {arm} pass is test_only={pass_.test_only} and the "
                f"authority is test_only={authority.test_only}")
    if at_2k.doublings != at_k.doublings + 1:
        raise MCInputError(
            "k_replay_evidence_pass_doubling_mismatch",
            f"the arms are at doublings={at_k.doublings} and "
            f"{at_2k.doublings}; the doubled arm is exactly one doubling "
            "above the base arm")
    if at_k.B != at_2k.B or at_k.channel != at_2k.channel:
        raise MCInputError(
            "k_replay_evidence_pass_scale_mismatch",
            "K is grid-analysis only: B and the theta channel may not move "
            f"between the arms (B {at_k.B} -> {at_2k.B}, channel "
            f"{at_k.channel!r} -> {at_2k.channel!r})")
    cells_at_k, cells_at_2k = at_k.cells, at_2k.cells

    converged, band, flipped, drift, digests = {}, {}, {}, {}, {}
    adjusted = {}
    for kind in REGION_KINDS:
        comparison = compare_region_maps(kind, cells_at_k, cells_at_2k,
                                         k=k, k_doubled=k_doubled)
        converged[kind] = comparison.converged
        band[kind] = comparison.boundary_band_cells
        flipped[kind] = comparison.flipped_cells
        drift[kind] = comparison.drift_violations
        # the RELABELLED map, in the frozen cell order, so publication
        # consumes what the comparison decided rather than re-deriving a map
        # the comparison never saw
        adjusted[kind] = tuple(
            (tuple(key), comparison.map_at_k[key]) for key in GRID_CELL_KEYS)
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
        "adjusted_map_by_kind": adjusted,
        "test_only": bool(authority.test_only),
    }
    preimage = {}
    for name in K_EVIDENCE_PAYLOAD_FIELDS:
        value = payload[name]
        if isinstance(value, dict):
            preimage[name] = {str(kk): _jsonable(vv)
                              for kk, vv in sorted(value.items())}
        else:
            preimage[name] = _jsonable(value)
    return KReplayEvidence(
        capability=_K_EVIDENCE_CAPABILITY,
        evidence_digest=_digest(_EVIDENCE_DIGEST_SCHEMA, preimage),
        **payload)


def _jsonable(value):
    """Tuples -> lists, recursively. One helper for both preimage builders,
    so a nested shape cannot hash one way when minted and another when
    verified -- which would make every witness refuse itself."""
    if isinstance(value, tuple):
        return [_jsonable(v) for v in value]
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    return value


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
# GridPass — the governed producer's product, and the only admissible cells
# ---------------------------------------------------------------------------

GRID_PASS_SCHEMA = "mc_grid_pass.v1"
_GRID_PASS_DIGEST_SCHEMA = "mc_grid_pass_digest.v1"


class _GridPassCapability:
    """Factory-only construction, the same capability the authority and the
    witness use. `_mint_grid_pass` is the one call site and the governed
    producer is its one caller."""
    __slots__ = ()


_GRID_PASS_CAPABILITY = _GridPassCapability()

GRID_PASS_PAYLOAD_FIELDS = (
    "schema", "authority_digest", "prepared_digest", "master_seed",
    "doublings", "B", "channel", "cell_keys", "cell_payloads", "test_only")


def _cell_payload(cell) -> dict:
    """One cell, as digestible structure. A MARKED cell digests its mark and
    its arithmetic; a sampled one digests its statistics. Neither borrows the
    other's shape, which is what keeps `marked` from being forgeable by
    supplying zeros."""
    if is_infeasible(cell):
        return {"marked": True,
                "reason": cell.reason, "detail": cell.detail,
                "q_mil": int(cell.q_mil), "r_mil": int(cell.r_mil),
                "master_seed": int(cell.master_seed),
                "doublings": int(cell.doublings),
                "n_tp": int(cell.n_tp), "n_fp": int(cell.n_fp),
                "fp_available": int(cell.fp_available)}
    if type(cell) is not CellStatistics:
        raise MCInputError(
            "grid_pass_cell_type_unknown",
            f"{type(cell).__name__} is neither CellStatistics nor "
            "InfeasibleCell")
    return {"marked": False,
            "conservative_p5": {str(k): float(v) for k, v
                                in sorted(cell.conservative_p5.items())},
            "stress_median": {str(k): float(v) for k, v
                              in sorted(cell.stress_median.items())},
            "feasible": {str(k): cell.feasible[k]
                         for k in sorted(cell.feasible)},
            "identity": {str(k): cell.identity[k]
                         for k in sorted(cell.identity)}}


@dataclass(frozen=True, slots=True)
class GridPass:
    """ONE seed's grid pass AT ONE SCALE, as produced by the governed path.

    WHAT THIS EXISTS TO STOP, exactly. `derive_k_replay_evidence` took two
    plain mappings of cells. A caller could build `CellStatistics` by hand --
    the dataclass is public, and it validates only that the numbers are finite
    and the combination sets agree -- hand them in, and receive a
    `KReplayEvidence` that verified perfectly and sealed as CONVERGED with
    `may_support_h1_entry` True. Nothing anywhere established that the
    governed grid producer had made those statistics. The witness's
    self-digest could not: it hashed the caller's own values, so it certified
    internal consistency and called it provenance.

    So the admissible unit is no longer a mapping of cells but a PASS, and a
    pass can only be minted by `grid_channel.run_grid_pass` through
    `_mint_grid_pass`. It carries the production identity the cells came out
    of -- which authority licensed it, which prepared input, which seed, which
    doubling scale, which B and which theta channel -- and a digest over that
    identity TOGETHER WITH every cell, so neither the cells nor the identity
    can be changed afterwards without the digest saying so.

    THIS IS NOT A `producer=True` FLAG. There is no field a caller can set to
    claim provenance; the capability object is the claim, it exists once at
    import time, and it is dropped the moment it is checked.

    TEST PATHWAY. `grid_pass_for_tests` mints one from caller-supplied cells
    and refuses unless the authority is already `test_only` -- so synthetic
    cells are explicitly typed as synthetic and ride that flag into the
    witness, the cross-seed standing and the seal, where the runner refuses
    them on the production path.
    """
    capability: object
    schema: str
    authority_digest: str
    prepared_digest: str
    master_seed: int
    doublings: int
    B: int
    channel: str
    cell_keys: tuple
    cell_payloads: tuple
    test_only: bool
    pass_digest: str
    cells: Mapping

    def __post_init__(self):
        if self.capability is not _GRID_PASS_CAPABILITY:
            raise MCInputError(
                "grid_pass_capability_required",
                "GridPass is factory-only -- it is minted by the governed "
                "grid producer (grid_channel.run_grid_pass), or by "
                "grid_pass_for_tests against a test_only authority. A "
                "direct constructor call or dataclasses.replace cannot mint "
                "one")
        object.__setattr__(self, "capability", None)
        object.__setattr__(self, "cells",
                           MappingProxyType(dict(self.cells)))


def _grid_pass_payload(pass_) -> dict:
    declared = {fld.name for fld in _dc_fields(pass_)} - {
        "capability", "pass_digest", "cells"}
    if declared != set(GRID_PASS_PAYLOAD_FIELDS):
        raise MCInputError(
            "grid_pass_payload_field_drift",
            f"{sorted(declared ^ set(GRID_PASS_PAYLOAD_FIELDS))}")
    return {name: _jsonable(getattr(pass_, name))
            for name in GRID_PASS_PAYLOAD_FIELDS}


def _mint_grid_pass(authority, *, prepared_digest: str, master_seed: int,
                    doublings: int, B: int, channel: str,
                    cells: Mapping) -> GridPass:
    """THE only minter. Private on purpose: the governed producer calls it,
    and `grid_pass_for_tests` calls it for explicitly synthetic evidence."""
    verify_grid_replay_authority(authority)
    if authority.prepared_digest != str(prepared_digest):
        raise MCInputError(
            "grid_pass_prepared_mismatch",
            f"the authority binds {authority.prepared_digest[:12]}, the pass "
            f"was produced from {str(prepared_digest)[:12]}")
    keys = tuple(tuple(k) for k in sorted(cells))
    payloads = tuple(_cell_payload(cells[key]) for key in keys)
    payload = {
        "schema": GRID_PASS_SCHEMA,
        "authority_digest": authority.authority_digest,
        "prepared_digest": str(prepared_digest),
        "master_seed": int(master_seed),
        "doublings": int(doublings),
        "B": int(B),
        "channel": str(channel),
        "cell_keys": keys,
        "cell_payloads": payloads,
        "test_only": bool(authority.test_only),
    }
    if set(payload) != set(GRID_PASS_PAYLOAD_FIELDS):
        raise MCInputError(
            "grid_pass_payload_field_drift",
            f"{sorted(set(payload) ^ set(GRID_PASS_PAYLOAD_FIELDS))}")
    preimage = {k: _jsonable(v) for k, v in payload.items()}
    return GridPass(capability=_GRID_PASS_CAPABILITY,
                    pass_digest=_digest(_GRID_PASS_DIGEST_SCHEMA, preimage),
                    cells=dict(cells), **payload)


def verify_grid_pass(pass_) -> GridPass:
    """Re-derive the digest from the pass's own identity AND its live cells.

    Re-deriving the cell payloads rather than reusing the stored ones is the
    point: a mutated `cells` mapping would otherwise hash to the value the
    pass was minted with and verify clean.
    """
    if type(pass_) is not GridPass:
        raise MCInputError(
            "grid_pass_required",
            f"{type(pass_).__name__} is not a GridPass -- seal-admissible "
            "grid evidence comes from the governed producer, never from a "
            "caller-assembled mapping of cells")
    payload = _grid_pass_payload(pass_)
    keys = tuple(tuple(k) for k in sorted(pass_.cells))
    live = {"cell_keys": _jsonable(keys),
            "cell_payloads": _jsonable(
                tuple(_cell_payload(pass_.cells[key]) for key in keys))}
    for name, value in live.items():
        if payload[name] != value:
            raise MCInputError(
                "grid_pass_cells_mutated",
                f"the pass's {name} no longer match the cells it carries")
    expect = _digest(_GRID_PASS_DIGEST_SCHEMA, payload)
    if pass_.pass_digest != expect:
        raise MCInputError(
            "grid_pass_digest_mismatch",
            f"carries {pass_.pass_digest[:12]}, its own fields hash to "
            f"{expect[:12]}")
    return pass_


def grid_pass_for_tests(authority, *, prepared_digest: str, master_seed: int,
                        doublings: int, B: int, channel: str,
                        cells: Mapping) -> GridPass:
    """A pass over CALLER-SUPPLIED cells, admissible only as synthetic.

    Refuses unless the authority is already `test_only`, so this cannot be
    the route by which hand-built statistics acquire production standing: the
    flag rides into the witness, into the cross-seed standing and into the
    seal candidate, and the runner refuses test-only grid evidence on the
    production path.
    """
    verify_grid_replay_authority(authority)
    if not authority.test_only:
        raise MCInputError(
            "grid_pass_for_tests_requires_test_authority",
            "caller-supplied cells are synthetic evidence and may only be "
            "minted against a test_only authority; a production authority's "
            "passes come from grid_channel.run_grid_pass")
    return _mint_grid_pass(authority, prepared_digest=prepared_digest,
                           master_seed=master_seed, doublings=doublings,
                           B=B, channel=channel, cells=cells)


# ---------------------------------------------------------------------------
# The full per-seed report
# ---------------------------------------------------------------------------

#: The absence metadata a MARKED cell reports, read off `InfeasibleCell`'s own
#: fields so the report cannot drift from the type. `reason` and `detail` say
#: WHY; the three counts are the frozen arithmetic that decided it.
MARKED_CELL_FIELDS = ("reason", "detail", "n_tp", "n_fp", "fp_available")

#: What a SAMPLED cell reports. Statistics only -- no class, no verdict.
SAMPLED_CELL_FIELDS = ("conservative_p5", "stress_median", "feasible",
                       "identity")


def per_seed_grid_report(passes_by_seed: Mapping,
                         witness_by_seed: Mapping) -> Mapping:
    """EVERY governed seed, EVERY cell, with absence stated as absence.

    WHAT THIS EXISTS TO STOP. The producer held all of it -- three seeds, 63
    cells each, every marked cell's reason and counts -- and the returned
    object kept merged region maps and base-seed summaries. A reader could
    see that a published cell was BOUNDARY_BAND and could not see which seed
    marked it, why, or against what arithmetic. "Mark, skip and REPORT IN
    FULL" is the sealed rule; the first two were implemented and the third
    stopped at the return statement.

    A MARKED CELL CARRIES NO STATISTICS. Not zeros, not None, not an empty
    mapping: the keys are absent, and `marked` is True. `CellStatistics`
    cannot express "never sampleable" without inventing a P5, a median or a
    feasibility verdict, and neither can this report.

    The per-kind class comes from the COMPARISON-ADJUSTED map, so a cell the
    comparison relabelled `boundary_band` reads as that here too, rather than
    as whatever the raw pass said before the comparison ran.
    """
    if set(passes_by_seed) != set(RESEARCH_BOOTSTRAP_SEEDS):
        raise MCInputError(
            "grid_report_seed_set_incomplete",
            f"{sorted(passes_by_seed)} != {list(RESEARCH_BOOTSTRAP_SEEDS)}")
    if set(witness_by_seed) != set(passes_by_seed):
        raise MCInputError(
            "grid_report_witness_set_mismatch",
            f"{sorted(witness_by_seed)} != {sorted(passes_by_seed)}")
    report = {}
    for seed in RESEARCH_BOOTSTRAP_SEEDS:
        at_k = verify_grid_pass(passes_by_seed[seed]["at_k"])
        cells_at_k = at_k.cells
        witness = verify_k_replay_evidence(witness_by_seed[seed])
        if at_k.master_seed != seed:
            raise MCInputError(
                "grid_report_pass_seed_mismatch",
                f"the pass filed under seed {seed} was produced for "
                f"{at_k.master_seed}")
        adjusted = {kind: witness.adjusted_map(kind) for kind in REGION_KINDS}
        cells, marked, sampled = {}, [], []
        for key in GRID_CELL_KEYS:
            cell = cells_at_k[tuple(key)]
            entry = {"class_by_kind": MappingProxyType(
                {kind: adjusted[kind][tuple(key)] for kind in REGION_KINDS})}
            if is_infeasible(cell):
                entry["marked"] = True
                for name in MARKED_CELL_FIELDS:
                    entry[name] = getattr(cell, name)
                marked.append(tuple(key))
            else:
                entry["marked"] = False
                for name in SAMPLED_CELL_FIELDS:
                    entry[name] = MappingProxyType(
                        dict(getattr(cell, name)))
                sampled.append(tuple(key))
            cells[tuple(key)] = MappingProxyType(entry)
        report[seed] = MappingProxyType({
            "master_seed": int(seed),
            "k": witness.k,
            "k_doubled": witness.k_doubled,
            "converged_by_kind": MappingProxyType(
                dict(witness.converged_by_kind)),
            "marked_cells": tuple(marked),
            "sampled_cells": tuple(sampled),
            "cells": MappingProxyType(cells),
        })
    return MappingProxyType(report)


# ---------------------------------------------------------------------------
# The cross-seed grid standing
# ---------------------------------------------------------------------------

GRID_CONVERGENCE_SCHEMA = "mc_grid_convergence_across_seeds.v1"
_GRID_CONVERGENCE_DIGEST_SCHEMA = "mc_grid_convergence_digest.v1"


class _GridConvergenceCapability:
    """The same factory-only capability the authority and the witness use."""
    __slots__ = ()


_GRID_CONVERGENCE_CAPABILITY = _GridConvergenceCapability()

GRID_CONVERGENCE_PAYLOAD_FIELDS = (
    "schema", "authority_digest", "prepared_digest", "k", "k_doubled",
    "seeds", "converged_by_kind", "converged_by_seed",
    "witness_digest_by_seed", "doublings_executed", "max_doublings",
    "test_only")


@dataclass(frozen=True, slots=True)
class GridConvergenceAcrossSeeds:
    """THE grid section's standing, over EVERY governed seed.

    WHAT THIS EXISTS TO STOP. Three witnesses were being built -- one per
    research seed, each from its own K and 2K pass -- and exactly one of them
    reached the final grid status and the H1-entry eligibility. The other two
    seeds' doubled-scale results were computed and then dropped, so a seed
    whose region map failed to converge could not move the outcome, and rule
    (b)'s cross-seed requirement was satisfied in the arithmetic and lost at
    integration.

    THE RULE IS CONJUNCTIVE, and it has to be: M10 publishes the INTERSECTION
    across seeds and M7 gives a non-converged region its consequence, so a
    region that converged for one seed and not another has not converged. Any
    other aggregation would publish a region no single seed's evidence
    supports.

    THE BOUND RIDES ALONG rather than being re-derived downstream. (e) doubles
    K while a region has not converged, bounded by the ruled
    `GridRepeatPolicy.max_doublings`; `doublings_executed` records how many
    doublings the evidence actually spans so a reader can check the bound was
    honoured instead of assuming it.

    It carries DIGESTS of the witnesses, never a second copy of their maps: a
    standing that restated the evidence could disagree with it.
    """
    capability: object
    schema: str
    authority_digest: str
    prepared_digest: str
    k: int
    k_doubled: int
    seeds: tuple
    converged_by_kind: Mapping
    converged_by_seed: Mapping
    witness_digest_by_seed: Mapping
    doublings_executed: int
    max_doublings: int
    test_only: bool
    convergence_digest: str

    def __post_init__(self):
        if self.capability is not _GRID_CONVERGENCE_CAPABILITY:
            raise MCInputError(
                "grid_convergence_capability_required",
                "GridConvergenceAcrossSeeds is factory-only -- use "
                "aggregate_k_replay_evidence()")
        object.__setattr__(self, "capability", None)
        for name in ("converged_by_kind", "converged_by_seed",
                     "witness_digest_by_seed"):
            object.__setattr__(self, name,
                               MappingProxyType(dict(getattr(self, name))))

    @property
    def grid_converged(self) -> bool:
        """Both frozen regions, across every governed seed."""
        return all(bool(v) for v in self.converged_by_kind.values())

    @property
    def grid_seal_status(self) -> str:
        return "CONVERGED" if self.grid_converged else "NON_CONVERGED"

    @property
    def may_support_h1_entry(self) -> bool:
        """M7, across seeds: only a converged `deployable_region` may."""
        return bool(self.converged_by_kind.get(DEPLOYABLE_REGION))


def _grid_convergence_payload(standing) -> dict:
    declared = {fld.name for fld in _dc_fields(standing)} - {
        "capability", "convergence_digest"}
    if declared != set(GRID_CONVERGENCE_PAYLOAD_FIELDS):
        raise MCInputError(
            "grid_convergence_payload_field_drift",
            f"{sorted(declared ^ set(GRID_CONVERGENCE_PAYLOAD_FIELDS))}")
    payload = {}
    for name in GRID_CONVERGENCE_PAYLOAD_FIELDS:
        value = getattr(standing, name)
        if isinstance(value, Mapping):
            payload[name] = {str(k): _jsonable(v)
                             for k, v in sorted(value.items())}
        else:
            payload[name] = _jsonable(value)
    return payload


def aggregate_k_replay_evidence(witness_by_seed: Mapping
                                ) -> GridConvergenceAcrossSeeds:
    """THE only minter: every governed seed's witness, verified, then ANDed.

    Requires exactly `RESEARCH_BOOTSTRAP_SEEDS`. A two-seed aggregation would
    quietly weaken rule (b) in the same way publishing from two maps would
    weaken M10, and the seed set is an identity requirement rather than a
    convenience.
    """
    if set(witness_by_seed) != set(RESEARCH_BOOTSTRAP_SEEDS):
        raise MCInputError(
            "grid_convergence_seed_set_incomplete",
            f"{sorted(witness_by_seed)} != {list(RESEARCH_BOOTSTRAP_SEEDS)}")
    seeds = tuple(RESEARCH_BOOTSTRAP_SEEDS)
    witnesses = {}
    for seed in seeds:
        witnesses[seed] = verify_k_replay_evidence(witness_by_seed[seed])
        if witnesses[seed].master_seed != seed:
            raise MCInputError(
                "grid_convergence_witness_seed_mismatch",
                f"the witness filed under seed {seed} carries master_seed="
                f"{witnesses[seed].master_seed}")
    first = witnesses[seeds[0]]
    for seed in seeds[1:]:
        other = witnesses[seed]
        for field, code in (("authority_digest",
                             "grid_convergence_authority_mismatch"),
                            ("prepared_digest",
                             "grid_convergence_prepared_mismatch"),
                            ("k", "grid_convergence_k_mismatch"),
                            ("k_doubled", "grid_convergence_k_mismatch"),
                            ("test_only",
                             "grid_convergence_test_only_mismatch")):
            if getattr(other, field) != getattr(first, field):
                raise MCInputError(
                    code,
                    f"seed {seed} witness {field}={getattr(other, field)!r} "
                    f"!= seed {seeds[0]}'s {getattr(first, field)!r}")
    converged_by_kind = {
        kind: all(bool(witnesses[seed].converged_by_kind.get(kind))
                  for seed in seeds)
        for kind in REGION_KINDS}
    # (e)'s bound, read off the ruled policy rather than written here, and
    # DERIVED from the evidence: how many doublings does k -> k_doubled span?
    from itsf import contracts as _contracts
    policy = _contracts.aaron_ruled_methods().grid_policy
    executed = 0
    span = int(first.k_doubled)
    while span > int(first.k):
        span //= 2
        executed += 1
    if executed < 1 or span != int(first.k):
        raise MCInputError(
            "grid_convergence_doubling_span_invalid",
            f"k={first.k} -> k_doubled={first.k_doubled} is not a whole "
            "number of doublings")
    if executed > int(policy.max_doublings):
        raise MCInputError(
            "grid_convergence_doublings_exceed_bound",
            f"{executed} doubling(s) executed, the ruled bound is "
            f"{policy.max_doublings}")
    payload = {
        "schema": GRID_CONVERGENCE_SCHEMA,
        "authority_digest": first.authority_digest,
        "prepared_digest": first.prepared_digest,
        "k": int(first.k),
        "k_doubled": int(first.k_doubled),
        "seeds": seeds,
        "converged_by_kind": converged_by_kind,
        "converged_by_seed": {
            seed: witnesses[seed].grid_converged for seed in seeds},
        "witness_digest_by_seed": {
            seed: witnesses[seed].evidence_digest for seed in seeds},
        "doublings_executed": executed,
        "max_doublings": int(policy.max_doublings),
        "test_only": bool(first.test_only),
    }
    if set(payload) != set(GRID_CONVERGENCE_PAYLOAD_FIELDS):
        raise MCInputError(
            "grid_convergence_payload_field_drift",
            f"{sorted(set(payload) ^ set(GRID_CONVERGENCE_PAYLOAD_FIELDS))}")
    preimage = {}
    for name in GRID_CONVERGENCE_PAYLOAD_FIELDS:
        value = payload[name]
        preimage[name] = ({str(k): _jsonable(v)
                           for k, v in sorted(value.items())}
                          if isinstance(value, dict) else _jsonable(value))
    return GridConvergenceAcrossSeeds(
        capability=_GRID_CONVERGENCE_CAPABILITY,
        convergence_digest=_digest(_GRID_CONVERGENCE_DIGEST_SCHEMA, preimage),
        **payload)


def verify_grid_convergence(standing) -> GridConvergenceAcrossSeeds:
    """Re-check the standing's self-digest, so a mutated one refuses."""
    if type(standing) is not GridConvergenceAcrossSeeds:
        raise MCInputError(
            "grid_convergence_required",
            f"{type(standing).__name__} is not a GridConvergenceAcrossSeeds")
    expect = _digest(_GRID_CONVERGENCE_DIGEST_SCHEMA,
                     _grid_convergence_payload(standing))
    if standing.convergence_digest != expect:
        raise MCInputError(
            "grid_convergence_digest_mismatch",
            f"carries {standing.convergence_digest[:12]}, its own fields hash "
            f"to {expect[:12]}")
    return standing


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
        elif classes == {INFEASIBLE_BY_SAMPLE}:
            # N13-F1. The sealed mark survives publication when every seed
            # made it, which is what will happen: the sealed test compares the
            # (q, r) quota with the aggregate pool and consults no seed. Left
            # to the `else`, a unanimously unsampleable cell would publish as
            # BOUNDARY_BAND — asserting its statistics hug zero when it has
            # none. That is the invented semantics this branch exists to
            # avoid, not a new region rule.
            published[tuple(key)] = INFEASIBLE_BY_SAMPLE
        else:
            # disagreement, or any seed already in the band -> union band.
            # A cell some seeds marked and others sampled lands here and is
            # thereby DISCLOSED rather than resolved — the existing rule,
            # reused rather than replaced.
            published[tuple(key)] = BOUNDARY_BAND
    return MappingProxyType(published)
