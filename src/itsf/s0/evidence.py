"""S0 CANONICAL EVIDENCE — the atom-anchored half of the seal boundary
(M6.1.4-S1, Codex-ordered RC-1 fix).

WHY THIS MODULE EXISTS
======================
`B0_SOURCE_LINEAGE_MATRIX.md` measured RC-1 as a number: of the 148
decision-bearing leaves in the sealed S0 report, **14 have any verification
anchor that a synchronized tampering could not move**. Every other check in
`report.py` re-derives a leaf from the payload's own claims (VF-1/3/4/5/6/7/
8/9) or from a PRODUCER AGGREGATE (`study[...]["d_tp"]`, VF-11) — never from
an atom. The recompute chain stops one level above the facts.

This module carries the missing level. `capture_evidence(...)` runs at
COMPUTE time, where the atoms are still in scope (`S0Dataset.records`, the
1-minute bars, the four `CostScenarioParams` objects, the §10.1
`TradePathRecord` set), and freezes them into an immutable
`CanonicalS0Evidence`. `reducers` then rebuild the formal subtrees FROM
those atoms, and `reconcile_with_evidence(...)` compares the sealed bytes
and the formal payload against them.

It is a SECOND COMPUTATION PATH, not a copy of `study.py`'s intermediates:

  * the trade-constructibility / opening-range / theoretical-oracle facts
    are RE-DERIVED from `bars_by_date` through `context.window_bars`,
    `study.StudyDayInput`, `paths.bar_index_at` and the `costs.*` fill
    primitives — the same frozen formulas, driven a second time off the raw
    frame, never read out of `study["per_theta"][...]`;
  * every P&L figure is taken from the AF2 records
    (`compute_result["records"]` -> `TradePathRecord.final_pnl_per_contract`),
    the family that survives to disk intact, NEVER from
    `study[...]["d_tp"]`, which is the pre-aggregated copy VF-11 already
    (insufficiently) anchors on;
  * the theta partition, the frequency denominators and the day universe
    are rebuilt from `labels.y_cont` / `labels.d_open` per day (EV-1),
    never from `oracle_daily.<theta>.day_universe`, which is the very claim
    under test.

HOW FAR THE AF2 ANCHOR ACTUALLY REACHES (PHASE-E blind audit, HIGH-1)
====================================================================
An earlier version of this docstring called AF2 "the only ATOMIC family
that survives to disk intact". That reads as a claim that a sealed
`TradePathRecord` is itself an atom. It is not: matrix Table 14 marks
L130-L137 PARTIAL because the true atom underneath `entry_fill`/`exit_fill`
/`mtm_*` is BAR DATA, and the bars are process-local. The honest claim is
two-part:

  * POST-CAPTURE byte tampering is closed. `record_fields` freezes every
    serialized field of every record at compute time and
    `_reconcile_record_fields` binds the PARSED sealed rows to it
    field-for-field with strict types, so a shifted fill pair, a rewritten
    FP-day exit, a rewritten mark array or an out-of-order timestamp is
    refused even when every downstream aggregate was repaired to match.
  * The FILL PREIMAGE is not. ENTRY fills on the theoretical-union (TP)
    days are anchored to `EV-2.entry_ref_price` (the 10:00 bar open,
    re-read from the frame) through the EV-4 cost snapshot; EXIT fills, and
    entry fills on FP-only days, have no captured bar preimage at all. A
    HOSTILE PRODUCER patched BEFORE compute poisons capture and the seal
    together, and nothing in this module can see it. That gap is disclosed
    permanently as `PARTIAL:records.executable_fills:...` and must never be
    described as closed.

Arithmetic reuse is deliberate and is NOT an independence gap: where the
matrix's `pure_reducer` column names an existing producer function
(`study._series_block`, `study._by_era_and_pooled`,
`study._worst_day_percentiles`, `gridmix._pools`), this module CALLS that
function rather than restating the formula — a restatement would add a
CR-4/CR-5/CR-11-class duplicate. What this module refuses to reuse is the
producer's OUTPUT.

WHAT THIS MODULE DOES NOT DO
============================
It rules no open research question and invents no vocabulary. For the
DR-gated axes (DR-1 cost layer, DR-2 volatility terciles, DR-3 FP
allocation basis, DR-4 bootstrap population/statistic, DR-6 event stratum,
DR-7 stability population, DR-8 P1/P5 estimator) the evidence is CAPTURED
ANYWAY with an honest provenance label — an `UNRESOLVED_DR-M6-x` axis label
stays `UNRESOLVED_DR-M6-x`. Per matrix §S6.2 that yields "a reproducible
record of an undefined partition", which is strictly better than today's
nothing and is explicitly NOT a closure claim. Every such section is
reported by `reconcile_with_evidence` as a deterministic
`PARTIAL:<section>:<reason>` marker, never as coverage.

Matrix §S6.3 in particular: `_approved_injectables()` returns `None`, so no
production `StudyConfig` exists and every USD figure in the report is
provisional until DR-1 lands. This module makes P&L RE-DERIVABLE from
`TradePathRecord` + `CostScenarioSnapshot`; it does not make the cost model
final, and it never says otherwise.

CALL-SITE WIRING (main agent — scripts/s0_real_run.py)
=====================================================
The one production call site is the END of
`build_full_study_result(ds, bars_by_date, *, config, governance_meta,
n_boot)`, where `ds`, `bars_by_date` and `config` are parameters in scope
and the compute-result tree is the dict being returned. Wire it as:

    from itsf.s0 import evidence as ev
    result = { ...the existing dict, unchanged... }
    result["evidence"] = ev.capture_evidence(ds, bars_by_date, result, config)
    return result

`"evidence"` is neither a `report.FORMAL_SECTIONS` member nor a
`report._INTERNAL_KEYS` member, so `report.split_envelope` DROPS it from
both halves — it can never leak into the sealed payload by accident, and
the renderer must pass it explicitly:

    evd  = result["evidence"]
    rec2 = ev.reconcile_with_evidence(evd, formal, files)
    hard, partial = ev.split_problems(rec2)
    if hard:
        raise ValueError("evidence reconciliation failed: " + "; ".join(hard))
    # `partial` is a DISCLOSURE list, never a pass/fail gate.

To build the formal payload FROM evidence rather than from the compute
tree's pre-aggregated copies (the actual RC-1 fix), the renderer replaces
the corresponding assignments with `ev.reducers[...](evd)` — see `reducers`
below for the exact subtree each one authoritatively rebuilds.

Optional keyword arguments unlock the three evidence objects whose atoms do
not live on `ds`/`bars_by_date`:

  * `universe=` — the `S0Universe` (`RealChain._uni`) unlocks EV-9's funnel
    DATE tuples and EV-10's raw F10 category sets. `build_full_study_result`
    does not receive it today; without it those two objects are captured in
    a reduced form with `provenance` saying so, and reconcile emits a
    PARTIAL marker instead of silently claiming coverage.
  * `frozen_hash_observations=` — the `{path: sha256}` result of the
    Stage-A `guards.verify_frozen_hashes()` RE-HASH (EV-13). Without it,
    `governance.frozen_hashes` stays the tautology matrix L127 describes.

    CALLER-ATTESTATION BOUNDARY (PHASE-E blind audit, C4): this argument is
    an ATTESTATION, and at reconcile time a caller that simply feeds
    `guards.FROZEN_HASHES` (the same hardcoded dict the payload was built
    from) back in is INDISTINGUISHABLE from a caller that re-hashed the
    files. Nothing in this module can tell them apart — the trust anchor is
    the PRODUCTION WIRING, which must pass the result of a genuine on-disk
    re-hash and nothing else. `provenance["EV-13"]` records only that
    SOMETHING was supplied, never that it was measured.
  * `scenarios=` — the already-built `costs.build_scenarios(...)` map, which
    must be EXACTLY the frozen §6 four-scenario axis (a reduced axis is
    refused: it would narrow the evidence and silently skip sealed files).
    When omitted this module builds its own from `config.spread_scalars`,
    which is the stronger (second-path) reading and the default.

DISCIPLINE
==========
`capture_evidence` is PURE and deterministic given its inputs and performs
no I/O; it may raise on a structurally impossible input exactly where
`build_study` would (it is a compute-time function, and a silent divergence
from the producer would be worse than a fail-closed raise). The three
consumer-side entry points — `reducers[*]`, `reconcile_with_evidence` and
`split_problems` — are GATES and never raise, for arbitrary input.
"""
from __future__ import annotations

import hashlib
import json
import math
from collections import Counter as _Counter
from dataclasses import dataclass, replace as _dc_replace
from types import MappingProxyType
from typing import Callable, Mapping, Sequence

import numpy as np

from itsf.contracts import (
    MNQ_POINT_VALUE_USD,
    MNQ_TICK_POINTS as _MNQ_TICK_POINTS,
    RESEARCH_BOOTSTRAP_SEEDS,
)
from itsf.s0 import context as _ctx
from itsf.s0 import costs as _costs
from itsf.s0 import gridmix as _gridmix
from itsf.s0 import oracle as _oracle
from itsf.s0 import paths as _paths
from itsf.s0 import report as _report
from itsf.s0 import stability as _stability
from itsf.s0 import stats as _stats
from itsf.s0 import study as _study
from itsf.s0.dataset import (
    DIRECTION_DIRECTIONAL,
    ERA_ACTUAL,
    ERA_PROXY,
    FEATURE_NA_FIELDS,
    LABEL_NA_FIELDS,
    PRE_Y6_LABEL_NA_FIELDS,
    STABILITY_EPOCHS,
)

SCHEMA_VERSION = "s0-canonical-evidence-1"

# frozen: S0 §9 — Primary block 5 trading days / Sensitivity 21. Stated here
# for the same reason report.py states it (`report._BLOCKS`): the owning
# constant lives in the main-agent-owned entrypoint script, which a library
# module must not import.
FROZEN_BLOCKS: tuple[int, ...] = (5, 21)
_SCENARIO_AXIS: tuple[str, ...] = ("Base", "Conservative", "Stress", "Severe")
# frozen: the funnel levels `structural.funnel_counts` publishes (matrix
# L001). Stated once here so EV-9's applicable population is a constant this
# module owns rather than something read off the evidence under test.
_FUNNEL_LEVELS: tuple[str, ...] = (
    "L0_scheduled_trading_days", "L1_observed_rth_days",
    "L2_regular_full_session_candidates", "L3_structurally_eligible_days",
    "L4_final_feature_construction_dates",
    "side_diagnostic_complete_390_bar_rth_days")

# --- provenance vocabulary (labels, never research vocabulary) -------------
PROV_REDERIVED_FROM_BARS = "rederived_from_bars"
PROV_ATOM_DAY_RECORD = "atom_S0Dataset.records"
PROV_ATOM_TRADE_PATH_RECORD = "atom_TradePathRecord"
PROV_ATOM_UNIVERSE = "atom_S0Universe"
PROV_CONFIG_DERIVED = "config_derived"
PROV_FROZEN_CONSTANT = "frozen_module_constant"
PROV_CALLER_SUPPLIED = "caller_supplied"
PROV_NOT_SUPPLIED = "not_supplied"

# DR markers — the EXACT strings the existing chain already uses, never a
# new vocabulary (handoff.py `_unresolved("DR-M6-F")` -> "UNRESOLVED_DR-M6-F",
# stability.py `status == "unresolved"`).
UNRESOLVED_VOL = "UNRESOLVED_DR-M6-B-v2"
UNRESOLVED_EVENT_STRATUM = "UNRESOLVED_DR-M6-F"
UNRESOLVED_SPREAD_RULE = "UNRESOLVED_DR-M6-A-v2"
STATUS_UNRESOLVED = "unresolved"
STATUS_RESOLVED = "resolved"
STATUS_TEST_ONLY = "test_only"

# frozen: App A / handoff._TP_FP_VALUES — the ONLY three classes.
TP_CLASS, FP_CLASS, NON_TRADEABLE_CLASS = "TP", "FP", "non_tradeable"

PARTIAL_PREFIX = "PARTIAL:"

# frozen: the App-A stratum key axes. Stated as a module constant (it used to
# be an inline literal inside `capture_evidence`) so EV-6.stratum_axes has
# something to be BOUND to rather than merely carried.
GRID_STRATUM_AXES: tuple = ("year", "volatility_regime", "event_flag")

# The EV-8 observation-method disclosure vocabulary. Same reason: a
# disclosure token nobody can compare is a string, not evidence.
NA_OBSERVATION_METHOD_ID: Mapping[str, str] = MappingProxyType({
    table: (f"pandas.isna over S0Dataset.{table}_table "
            "(structurally distinct from DayRecord.*_na_reasons)")
    for table in ("features", "labels")})

# the exact ternary `build_full_study_result` uses for an unruled DR-8
_ESTIMATOR_STATUS_UNRESOLVED = "unresolved_DR-M6-H"

# EV-1 vocabularies, from the modules that own them
_DIRECTION_NA: frozenset = frozenset(
    {_ctx.NA_ZERO_DIRECTION, _ctx.NA_DIRECTION_UNDETERMINABLE})
_UNTRADEABLE_VOCAB: frozenset = frozenset(_study.UNTRADEABLE_REASONS)

# EV-2's favourable-extreme timestamp has no captured preimage; the only
# research-free rail is the frozen SS3 trade window it must lie in.
_TS_LO: str = _paths.ENTRY_TIME.strftime("%H:%M")
_TS_HI: str = _paths.FORCED_EXIT_BAR_TIME.strftime("%H:%M")


# ===========================================================================
# 0. deep-freeze primitives (mandate item 3: ZERO shared mutable identity)
# ===========================================================================
def _sort_key(value):
    """Total order over heterogeneous keys (same discipline as
    `report._sort_key`, restated locally so this module never depends on a
    private name in another module)."""
    tname = type(value).__name__
    if isinstance(value, str):
        return (tname, value, "")
    if isinstance(value, bool):
        return (tname, "", str(int(value)))
    if isinstance(value, (int, float)):
        try:
            return (tname, "", f"{float(value):+032.6f}")
        except Exception:                                # noqa: BLE001
            return (tname, "", repr(type(value)))
    try:
        return (tname, "", repr(value))
    except Exception:                                    # noqa: BLE001
        return (tname, "", "<unreprable>")


def freeze(obj):
    """Recursively convert a plain tree into an IMMUTABLE one.

    dict -> `MappingProxyType` over a FRESHLY BUILT dict this module alone
    holds a reference to; list/tuple -> tuple; set/frozenset -> a sorted
    tuple; scalars pass through. The point is mandate item 3: after
    canonicalization, evidence and any formal payload must share ZERO
    mutable dict/list object identity, so mutating the formal tree after
    capture cannot retroactively change what reconciliation sees.
    """
    if isinstance(obj, Mapping):
        return MappingProxyType({k: freeze(v) for k, v in obj.items()})
    if isinstance(obj, (frozenset, set)):
        return tuple(freeze(v) for v in sorted(obj, key=_sort_key))
    if isinstance(obj, (list, tuple)):
        return tuple(freeze(v) for v in obj)
    return obj


def to_plain(obj):
    """Inverse of `freeze` for JSON-shaped output: MappingProxyType -> a
    FRESH dict, tuple -> a FRESH list. Every call returns brand-new
    containers, so a caller can never mutate its way back into the frozen
    evidence."""
    if isinstance(obj, Mapping):
        return {k: to_plain(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_plain(v) for v in obj]
    return obj


# ===========================================================================
# 1. EV-1 .. EV-13 — the evidence objects named in matrix §S2
# ===========================================================================

@dataclass(frozen=True)
class CanonicalDayFact:
    """EV-1 — one row per STRUCTURALLY ELIGIBLE day (not just per traded
    day). Unblocks L018, L021, L022, L023, L024, L065, L067, L068, L069,
    L070, L089 — i.e. the entire theta partition and the whole A6 frequency
    block, today the highest-leverage unreconstructible family in the
    report.

    `era` and `year` are RE-DERIVED here (`date < context.MICRO_ERA_BOUNDARY`,
    `date[:4]`) rather than copied off the DayRecord, so a drift between the
    dataset's own labelling and the frozen definition is visible;
    `record_era`/`record_year` carry the producer's claim for exactly that
    comparison.
    """
    trade_date: str
    year: str
    era: str
    record_year: str
    record_era: str
    d_open: int
    y_cont: float | None
    y_cont_available: bool
    direction_status: str
    oracle_candidate: bool            # RE-derived: d_open in {+1,-1} and y_cont
    record_oracle_candidate: bool     # the DayRecord's own claim
    tradeable_direction: bool
    trade_constructible: bool
    untradeable_reason: str | None
    is_event_day: str | None          # F10 final flag; None == multi-event NA


@dataclass(frozen=True)
class TheoreticalPathRecord:
    """EV-2 — the §7 economic-upper-bound analogue of `TradePathRecord`, one
    per day in the theoretical union. Unblocks all of A3 (L036-L040), which
    is ENTIRELY unfalsifiable post-seal today: `oracle.theoretical_oracle`
    emits a bare float and the bars are process-local."""
    trade_date: str
    direction: int
    scenario_name: str
    entry_ref_price: float
    entry_fill: float
    favourable_extreme_price: float
    favourable_extreme_ts: str
    exit_fill: float
    pnl_per_contract: float
    platform_fee_rt_usd: float


@dataclass(frozen=True)
class OpeningRangeFact:
    """EV-3 — one per trade-constructible day. Unblocks every E2 sizing
    figure (L048/L050/L136/L137 E2 branch): `planned_stop` is stored `None`
    for E2, so the opening-range level reaches NO sealed artifact today."""
    trade_date: str
    or_high: float
    or_low: float
    n_obs_bars: int
    anchor_stop: float
    d_open: int


@dataclass(frozen=True)
class CostScenarioSnapshot:
    """EV-4 — one per cost scenario (4). Unblocks the cost layer of every
    USD leaf (L053/L054/L131/L137). `reduction_rule_id` is the id of the
    DR-1 reduction that produced `spread_scalars`; while DR-1 pends it is
    `UNRESOLVED_DR-M6-A-v2` (matrix §S6.3 — CAPTURE is unblocked, the
    VALUES are not)."""
    name: str
    spread_points: float
    slippage_ticks_per_side: float
    adverse_slippage_ticks: float
    friction_multiplier: float
    platform_fee_rt_usd: float
    spread_scalars: tuple
    reduction_rule_id: str
    adverse_semantics: str


@dataclass(frozen=True)
class DayStratumFact:
    """EV-5 — one per day: `build_day_strata`'s payload, which NO production
    caller builds today (matrix L144, NOT PRODUCED). Capture is unblocked;
    the stratum VOCABULARY is DR-2 (volatility) + DR-6 (event), so those two
    axes are captured with their existing UNRESOLVED markers. Per matrix
    §S6.2 this is a reproducible record of an undefined partition, never a
    replayable pool."""
    trade_date: str
    year: str
    micro_execution_era: str
    stability_epoch: str
    d_open: int
    volatility_regime_label: str
    vol_status: str
    event_flag_final: str
    event_na: bool
    event_stratum: str
    tp_fp_class: Mapping            # theta_key -> TP | FP | non_tradeable


@dataclass(frozen=True)
class GridPoolFact:
    """EV-6 — one per (theta, engine, scenario): the RNG PREIMAGE
    `gridmix._select` draws from. Without it no App-A replay is possible at
    all (L097/L101/L103). The pool CONTENTS inherit DR-2/DR-3/DR-6."""
    theta_key: str
    engine: str
    scenario: str
    tp_pools: Mapping               # stratum key -> sorted date tuple
    fp_pools: Mapping
    tp_avail: Mapping               # stratum key -> count
    fp_avail: Mapping
    n_tp_available: int
    n_fp_available: int
    grid_stream_tag: int
    stratum_axes: tuple             # ("year", "volatility_regime", "event_flag")


@dataclass(frozen=True)
class BootstrapInputFact:
    """EV-7 — one per `bootstrap_ci` cell key (32). The ordered (date, usd)
    series DIGEST is what lets a replay PROVE it consumed the same series,
    which is unprovable today (L082/L085).

    `series_mean_sum_over_n` and `series_mean_numpy` are BOTH captured on
    purpose: matrix CR-2 records three separate implementations of "the
    sample mean of the D_TP series" (`study._series_block`'s `sum/len`,
    `stability._cell`'s `sum/n`, `stats`' `numpy.ndarray.mean()` pairwise
    summation) that are NEVER compared. Carrying both readings is what
    turns that into a checkable identity in `reconcile_with_evidence`."""
    cell_key: str
    theta_key: str
    engine: str
    scenario: str
    block_len: int
    n: int
    series_sha256: str
    series_mean_sum_over_n: float | None
    series_mean_numpy: float | None
    series_sum: float
    first_date: str | None
    last_date: str | None
    seeds: tuple
    stats_stream_tag: int
    block_stream_key: int
    n_boot: int
    ci_level: float
    percentile_method_id: str


@dataclass(frozen=True)
class NAObservationFact:
    """EV-8 — a SECOND, STRUCTURALLY DIFFERENT NA observation: a raw null
    scan of `S0Dataset.features_table`/`labels_table` (a different code path
    from `DayRecord.*_na_reasons`). Matrix CR-1: today FIVE 'independent'
    NA recomputes all trace to the one `ds.na_table` preimage.

    SCOPE, precisely (PHASE-E blind audit): this closes CR-1 at the
    NA/NOT-NA COUNT level only — `_reconcile_na_table` compares these null
    counts against `structural.na_table.per_field.<table>.<field>.na`, and
    a payload that moves `na_table` and `disclosures.na_conservation`
    TOGETHER is now refused. It does NOT close the REASON level: the
    per-date `reasons` breakdown still has exactly one preimage
    (`DayRecord.*_na_reasons`), and a permanent
    `PARTIAL:structural.na_table.reasons:` marker says so."""
    table: str
    column: str
    n_null: int
    n_not_null: int
    observation_method_id: str


@dataclass(frozen=True)
class FunnelFact:
    """EV-9 — the funnel as MEMBERSHIP, not counts (L001).

    SCOPE (PHASE-E blind audit — the earlier "turns five counts into a
    re-derivable set chain" claim was an overclaim): the captured L0..L4
    date tuples plus the `complete_390` side diagnostic let
    `_reconcile_funnel` rebuild ALL TEN published `funnel_counts` keys and
    refuse a fabricated count. The DEDUCTIONS themselves (which day was
    dropped for which frozen L44 reason) are re-derivable only as far as
    `exclusion_reason` records them; this evidence does NOT re-run the
    session-schedule / early-close / >10%-missing predicates from bars, so
    a funnel built on a poisoned schedule is out of its reach."""
    level_dates: Mapping            # level name -> date tuple
    exclusion_reason: Mapping       # date -> reason
    provenance: str


@dataclass(frozen=True)
class F10MembershipFact:
    """EV-10 — per date the RAW (multi-hot) category set and the final
    exclusive category. L003 has NO verifier of any kind today."""
    trade_date: str
    raw_categories: tuple
    final_category: str
    raw_provenance: str


@dataclass(frozen=True)
class LabelAvailabilityFact:
    """EV-11 — per date the five IR-23 dependency booleans that
    `dataset._label_anchor_availability` computes and discards (L012, and
    the label half of L007). RE-DERIVED here from the bars + the DayRecord's
    own adr14/direction_status, never copied out of the availability
    counts.

    SCOPE (PHASE-E blind audit): `_reconcile_label_availability` aggregates
    these booleans and refuses a fabricated
    `structural.label_anchor_availability`, so L012 is CHECKED. The label
    half of L007 (`na_table.per_field.labels.*.reasons`) is NOT — anchor
    EXISTENCE and NA-BY-REASON are different questions and only the first
    has a second observation here."""
    trade_date: str
    o1000: bool
    c1544: bool
    pm_ok: bool
    adr_ok: bool
    dir_ok: bool
    available: Mapping              # label -> bool


@dataclass(frozen=True)
class EstimatorIdentityFact:
    """EV-12 — the estimator string ACTUALLY used at compute time by each of
    the three independent module constants matrix CR-5 names, plus the
    `estimator_status` a payload is entitled to claim. Closes packet P-6 /
    blind-audit G1-G2: `worst_day_report.percentile_estimator` is never
    cross-asserted against `e2_worst_days.estimator_status` today."""
    study_percentile_method: str
    stability_percentile_method: str
    stats_percentile_method: str
    all_three_agree: bool
    worst_day_estimator_ruling: str | None
    estimator_status_expected: str


@dataclass(frozen=True)
class FrozenHashObservationFact:
    """EV-13 — the `guards.verify_frozen_hashes()` RE-HASH RESULT carried
    from the Stage-A gate into the evidence, so `governance.frozen_hashes`
    can be compared against BYTES instead of against the same hardcoded
    `guards.FROZEN_HASHES` dict it was built from (matrix L127: the seal
    boundary check is tautological today)."""
    observed: Mapping               # path -> freshly computed sha256
    provenance: str


@dataclass(frozen=True)
class CanonicalS0Evidence:
    """The INTERNAL immutable evidence object. Deliberately NOT a formal
    report section: the frozen formal payload's 13 top-level keys
    (`report.FORMAL_SECTIONS`) are unchanged by this module."""
    schema_version: str
    thetas: tuple
    engines: tuple
    scenarios: tuple
    eras: tuple
    blocks: tuple
    day_facts: tuple                 # EV-1
    theoretical_paths: tuple         # EV-2
    opening_ranges: tuple            # EV-3
    cost_scenarios: tuple            # EV-4
    day_strata: tuple                # EV-5
    grid_pools: tuple                # EV-6
    bootstrap_inputs: tuple          # EV-7
    na_observations: tuple           # EV-8
    funnel: FunnelFact               # EV-9
    f10_memberships: tuple           # EV-10
    label_availability: tuple        # EV-11
    estimator_identity: EstimatorIdentityFact       # EV-12
    frozen_hash_observation: FrozenHashObservationFact   # EV-13
    record_pnl: Mapping              # (engine, scenario) -> date -> usd (AF2)
    record_fields: Mapping           # (engine, scenario) -> date -> row
    provenance: Mapping

    # M6.1.4 integration (main): the object is DEEPLY immutable by
    # construction, so a deep copy could only ever produce an identical
    # object — copy IS identity. This also keeps a compute-result dict that
    # carries the evidence deepcopy-able (MappingProxyType containers are
    # not picklable, and test fixtures deepcopy payloads freely).
    def __deepcopy__(self, memo):
        return self

    def __copy__(self):
        return self

    # --- convenience accessors (pure, never raise) ------------------------
    def day_fact_map(self) -> dict:
        return {f.trade_date: f for f in self.day_facts}

    def theta_keys(self) -> tuple:
        return tuple(_study.theta_key(t) for t in self.thetas)

    def labelled_partition(self, theta: float) -> tuple:
        """(tp_labelled, fp_labelled) over the TRADEABLE population —
        `study._partition`'s population, rebuilt from EV-1 atoms."""
        tp, fp = [], []
        for f in self.day_facts:
            if not f.oracle_candidate:
                continue
            (tp if float(f.y_cont) >= theta else fp).append(f.trade_date)
        return tuple(tp), tuple(fp)

    def partition(self, theta: float) -> tuple:
        """(tp_days, fp_days) — the labelled partition narrowed to the
        TRADE-CONSTRUCTIBLE days, i.e. exactly `build_study`'s `tp_days`/
        `fp_days`, in ascending date order."""
        constructible = {f.trade_date for f in self.day_facts
                         if f.trade_constructible}
        tp, fp = self.labelled_partition(theta)
        return (tuple(d for d in tp if d in constructible),
                tuple(d for d in fp if d in constructible))


# ===========================================================================
# 2. capture_evidence — the SECOND computation path
# ===========================================================================
def _rederived_era(date: str) -> str:
    """frozen §6 L109-115 — era is a pure function of the date against the
    frozen `context.MICRO_ERA_BOUNDARY`."""
    return ERA_PROXY if date < _ctx.MICRO_ERA_BOUNDARY else ERA_ACTUAL


def _epoch_of_year(year: str) -> str:
    """frozen §2 — `dataset.STABILITY_EPOCHS` half-open string ranges.

    Matrix CR-4 records FOUR implementations of this one frozen definition
    with two different interval conventions. This module reuses the DATASET
    one (the convention `structural.groups.stability_epochs` is built with);
    `_reconcile_day_strata` then CROSS-CHECKS every captured
    `stability_epoch` against `stability._epoch_of`'s INCLUSIVE INTEGER
    convention, so the two conventions agreeing is asserted rather than
    assumed (they agree today only because the boundaries are contiguous
    integer years)."""
    for name, lo, hi in STABILITY_EPOCHS:
        if lo <= year < hi:
            return name
    return _stability.OUTSIDE_EPOCHS


def _series_digest(pairs: Sequence[tuple]) -> str:
    """sha256 of a canonical serialization of an ordered (date, usd)
    series. `sort_keys`/`separators` fixed, `allow_nan=False`, no indent —
    the same canonical-JSON discipline `handoff.dumps_canonical` uses."""
    payload = json.dumps([[str(d), float(v)] for d, v in pairs],
                         sort_keys=True, allow_nan=False,
                         separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _capture_day_inputs(ds, bars_by_date):
    """RE-DERIVE the per-day trade-construction inputs from the RAW bars.

    Mirrors `scripts/s0_real_run.py::make_day_inputs` (read-only reference)
    by construction rather than by import — this is the second path, so it
    must not consume the first path's output."""
    day_inputs: dict = {}
    obs_bar_counts: dict = {}
    for r in ds.records:
        if r.labels.d_open not in (1, -1):
            continue
        bars = bars_by_date.get(r.trade_date)
        if bars is None:
            continue
        obs = _ctx.window_bars(bars, _ctx.OBS_LO_MINUTE, _ctx.OBS_HI_MINUTE)
        pm = _ctx.window_bars(bars, _ctx.PM_LO_MINUTE, _ctx.PM_HI_MINUTE)
        if not len(obs) or not len(pm):
            continue
        day_inputs[r.trade_date] = _study.StudyDayInput(
            trade_date=r.trade_date, pm_bars=pm,
            or_high=float(obs["high"].max()), or_low=float(obs["low"].min()),
            d_open=int(r.labels.d_open))
        obs_bar_counts[r.trade_date] = int(len(obs))
    return day_inputs, obs_bar_counts


def _theoretical_path(trade_date: str, inp, scenario) -> TheoreticalPathRecord:
    """RE-DERIVE the §7 theoretical upper bound and, on the same pass,
    CROSS-CHECK it against `oracle.theoretical_oracle`'s bare float. The
    components (entry ref, favourable extreme + its timestamp, both fills)
    are what EV-2 exists to preserve; the oracle call is the agreement
    check the matrix says A3 has never had."""
    d = int(inp.d_open)
    bars = inp.pm_bars
    entry_idx = _paths.bar_index_at(bars, _paths.ENTRY_TIME)
    end_idx = _paths.bar_index_at(bars, _paths.FORCED_EXIT_BAR_TIME)
    window = bars.iloc[entry_idx:end_idx + 1]
    entry_ref = float(window.iloc[0]["open"])
    entry_fill = float(_costs.scenario_entry_fill(entry_ref, d, scenario))
    if d == 1:
        label = window["high"].idxmax()
        fav_px = float(window["high"].max())
    else:
        label = window["low"].idxmin()
        fav_px = float(window["low"].min())
    fav_ts = str(window.loc[label, "ts"].isoformat())
    exit_fill = float(_costs.scenario_timed_exit_fill(fav_px, d, scenario))
    pnl = (d * (exit_fill - entry_fill) * MNQ_POINT_VALUE_USD
           - scenario.platform_fee_rt_usd)
    return TheoreticalPathRecord(
        trade_date=trade_date, direction=d, scenario_name=scenario.name,
        entry_ref_price=entry_ref, entry_fill=entry_fill,
        favourable_extreme_price=fav_px, favourable_extreme_ts=fav_ts,
        exit_fill=exit_fill, pnl_per_contract=float(pnl),
        platform_fee_rt_usd=float(scenario.platform_fee_rt_usd))


def _label_availability(trade_date: str, record, bars) -> LabelAvailabilityFact:
    """RE-DERIVE the five IR-23 dependency booleans from the raw frame plus
    the DayRecord's own adr14 / direction_status. `dataset.
    _label_anchor_availability` reads them off `S0Universe.summaries`; this
    is the other route to the same facts, which is what makes L012
    checkable."""
    o1000 = c1544 = False
    pm_ok = False
    if bars is not None:
        pm = _ctx.window_bars(bars, _ctx.PM_LO_MINUTE, _ctx.PM_HI_MINUTE)
        pm_ok = bool(len(pm) > 0)
        if pm_ok:
            times = {ts.time(): i for i, ts in enumerate(pm["ts"])}
            entry_i = times.get(_paths.ENTRY_TIME)
            exit_i = times.get(_paths.FORCED_EXIT_BAR_TIME)
            if entry_i is not None:
                o1000 = bool(np.isfinite(float(pm.iloc[entry_i]["open"])))
            if exit_i is not None:
                c1544 = bool(np.isfinite(float(pm.iloc[exit_i]["close"])))
    adr_ok = record.features.adr14 is not None
    dir_ok = record.direction_status == DIRECTION_DIRECTIONAL
    available = {
        "y_cont": o1000 and c1544 and adr_ok and dir_ok,
        "y1": o1000 and c1544 and adr_ok,
        "y2_de_pm": o1000 and c1544 and pm_ok,
        "y3_close_pos_pm": c1544 and pm_ok,
        "y4_mfe": o1000 and pm_ok and adr_ok and dir_ok,
        "y5_mae": o1000 and pm_ok and adr_ok and dir_ok,
    }
    return LabelAvailabilityFact(
        trade_date=trade_date, o1000=o1000, c1544=c1544, pm_ok=pm_ok,
        adr_ok=bool(adr_ok), dir_ok=bool(dir_ok),
        available=freeze(available))


def _method_status(value, test_only: bool) -> str:
    """The honest three-way status of a DR-gated method value: pending ->
    `unresolved`, resolved-but-synthetic -> `test_only`, resolved ->
    `resolved`. Never claims a ruling this module has not seen."""
    if value is None:
        return STATUS_UNRESOLVED
    return STATUS_TEST_ONLY if test_only else STATUS_RESOLVED


def capture_evidence(ds, bars_by_date, compute_result, config, *,
                     scenarios=None, universe=None,
                     frozen_hash_observations=None,
                     thetas: Sequence[float] = _study.FROZEN_THETAS,
                     blocks: Sequence[int] = FROZEN_BLOCKS,
                     n_boot: int = _stats.N_BOOT,
                     ci_level: float = _stats.CI_LEVEL,
                     bootstrap_seeds: Sequence[int] = RESEARCH_BOOTSTRAP_SEEDS,
                     day_value_snapshot=None,
                     ) -> CanonicalS0Evidence:
    """Capture EV-1..EV-13 at compute time. See the module docstring for the
    exact `scripts/s0_real_run.py` call site this signature is shaped for.

    Parameters
    ----------
    ds
        the assembled `S0Dataset` — `records` (AF1 atoms), plus
        `features_table`/`labels_table` for EV-8's second NA observation.
    bars_by_date
        `{trade_date: DataFrame}`, the AF3 raw 1-minute frame. Read-only:
        every window is taken through `context.window_bars`, which never
        invents a bar (IR-15).
    compute_result
        the `build_full_study_result` tree. ONLY `["records"]` is consumed —
        the §10.1 `TradePathRecord` set, i.e. the AF2 ATOMS. The
        pre-aggregated `study[...]["d_tp"]` / `["executable"]` copies are
        deliberately NOT read: anchoring on them is precisely the VF-11
        defect the matrix names.
    config
        the `StudyConfig`. Consumed for `spread_scalars` (EV-4),
        `vol_axis_of` (EV-5), `methods.*` (EV-4/EV-5/EV-12 provenance).
    """
    theta_values = tuple(float(t) for t in thetas)
    block_values = tuple(int(b) for b in blocks)
    scn_map = (dict(scenarios) if scenarios is not None
               else _costs.build_scenarios(*config.spread_scalars))
    # C12b (PHASE-E blind audit): a caller-supplied `scenarios` map that is
    # NOT the frozen §6 four-scenario axis silently narrowed
    # `evidence.scenarios`, and `_parse_sealed_rows` then SKIPPED the files
    # outside the reduced axis — an evidence object that looks complete
    # while covering half the sealed set. Refused at capture time (a
    # compute-time function is entitled to fail closed) rather than
    # disclosed after the fact.
    scn_names = tuple(n for n in _SCENARIO_AXIS if n in scn_map)
    if set(scn_map) != set(_SCENARIO_AXIS):
        raise ValueError(
            "capture_evidence: `scenarios` must be EXACTLY the frozen §6 "
            f"four-scenario axis {list(_SCENARIO_AXIS)}, got "
            f"{sorted(scn_map)} — a reduced axis would silently narrow the "
            "evidence and skip sealed MC_HANDOFF files (fail closed)")
    methods = getattr(config, "methods", None)
    test_only = bool(getattr(methods, "test_only", False))
    provenance: dict = {}

    records_sorted = sorted(ds.records, key=lambda r: r.trade_date)
    day_inputs, obs_counts = _capture_day_inputs(ds, bars_by_date)

    # --- EV-1 CanonicalDayFact --------------------------------------------
    day_facts: list = []
    for r in records_sorted:
        d_open = int(r.labels.d_open or 0)
        y_cont = r.labels.y_cont
        oracle_candidate = d_open in (1, -1) and y_cont is not None
        reason = None
        constructible = False
        if oracle_candidate:
            inp = day_inputs.get(r.trade_date)
            reason = (_study.REASON_NO_DAY_INPUT if inp is None
                      else inp.defect_reason())
            constructible = reason is None
        day_facts.append(CanonicalDayFact(
            trade_date=r.trade_date,
            year=r.trade_date[:4],
            era=_rederived_era(r.trade_date),
            record_year=str(r.year),
            record_era=str(r.era),
            d_open=d_open,
            y_cont=(None if y_cont is None else float(y_cont)),
            y_cont_available=y_cont is not None,
            direction_status=str(r.direction_status),
            oracle_candidate=bool(oracle_candidate),
            record_oracle_candidate=bool(r.oracle_candidate),
            tradeable_direction=bool(r.tradeable_direction),
            trade_constructible=bool(constructible),
            untradeable_reason=reason,
            is_event_day=r.features.is_event_day))
    provenance["EV-1"] = PROV_ATOM_DAY_RECORD + "+" + PROV_REDERIVED_FROM_BARS

    constructible_dates = frozenset(
        f.trade_date for f in day_facts if f.trade_constructible)

    # --- EV-3 OpeningRangeFact --------------------------------------------
    opening_ranges = tuple(
        OpeningRangeFact(
            trade_date=d, or_high=float(day_inputs[d].or_high),
            or_low=float(day_inputs[d].or_low),
            n_obs_bars=int(obs_counts.get(d, 0)),
            anchor_stop=float(day_inputs[d].anchor_stop),
            d_open=int(day_inputs[d].d_open))
        for d in sorted(constructible_dates))
    provenance["EV-3"] = PROV_REDERIVED_FROM_BARS

    # --- EV-2 TheoreticalPathRecord ---------------------------------------
    base_scn = scn_map[_study.BASE_SCENARIO_NAME]
    theoretical_union: set = set()
    for theta in theta_values:
        tp_days, _fp = _partition_from_facts(day_facts, theta,
                                             constructible_dates)
        theoretical_union.update(tp_days)
    theoretical_paths: list = []
    oracle_disagreements: list = []
    for d in sorted(theoretical_union):
        fact = _theoretical_path(d, day_inputs[d], base_scn)
        cross = float(_oracle.theoretical_oracle(
            day_inputs[d].pm_bars, day_inputs[d].d_open, base_scn))
        if not math.isclose(cross, fact.pnl_per_contract,
                            rel_tol=1e-9, abs_tol=1e-9):
            oracle_disagreements.append(d)
        theoretical_paths.append(fact)
    provenance["EV-2"] = PROV_REDERIVED_FROM_BARS
    if oracle_disagreements:
        # NEVER silently reconciled: the two paths disagreeing about a
        # frozen formula is a defect, disclosed here and turned into a hard
        # problem by `reconcile_with_evidence`.
        provenance["EV-2_oracle_cross_check"] = (
            "DISAGREEMENT:" + ",".join(sorted(oracle_disagreements)[:5]))
    else:
        provenance["EV-2_oracle_cross_check"] = "agrees"

    # --- EV-4 CostScenarioSnapshot ----------------------------------------
    spread_cost = getattr(methods, "spread_cost", None)
    reduction_rule_id = (str(getattr(spread_cost, "scalar_rule", ""))
                         if spread_cost is not None else "")
    if not reduction_rule_id:
        reduction_rule_id = UNRESOLVED_SPREAD_RULE
    adverse_semantics = (str(getattr(spread_cost, "adverse_semantics", ""))
                         if spread_cost is not None else "")
    if not adverse_semantics:
        adverse_semantics = UNRESOLVED_SPREAD_RULE
    cost_scenarios = tuple(
        CostScenarioSnapshot(
            name=scn_map[n].name,
            spread_points=float(scn_map[n].spread_points),
            slippage_ticks_per_side=float(scn_map[n].slippage_ticks_per_side),
            adverse_slippage_ticks=float(scn_map[n].adverse_slippage_ticks),
            friction_multiplier=float(scn_map[n].friction_multiplier),
            platform_fee_rt_usd=float(scn_map[n].platform_fee_rt_usd),
            spread_scalars=tuple(float(v) for v in config.spread_scalars),
            reduction_rule_id=reduction_rule_id,
            adverse_semantics=adverse_semantics)
        for n in scn_names)
    provenance["EV-4"] = PROV_CONFIG_DERIVED
    provenance["EV-4_dr1_status"] = _method_status(spread_cost, test_only)

    # --- EV-5 DayStratumFact ----------------------------------------------
    vol_status = _method_status(getattr(methods, "volatility_regime", None),
                                test_only)
    event_rule = getattr(methods, "event_na_mapping", None)
    day_strata: list = []
    for f in day_facts:
        # F-1 (Codex final-review blocker #1, 2026-08-10): post-exposure
        # code consumes the PREPARE-TIME immutable value snapshot when one
        # is supplied — the production entry always supplies it (pinned by
        # chain test); the config callable is a pre-exposure/legacy-test
        # fallback only.
        try:
            if day_value_snapshot is not None:
                vol_label = str(day_value_snapshot.vol_axis(f.trade_date))
            else:
                vol_label = str(config.vol_axis_of(f.trade_date))
        except Exception:                                # noqa: BLE001
            vol_label = UNRESOLVED_VOL
        if vol_status == STATUS_UNRESOLVED:
            vol_label = UNRESOLVED_VOL
        flag = f.is_event_day
        if flag is not None:
            event_stratum = str(flag)
            event_final = str(flag)
        else:
            # IR-12/18 vocabulary is only reachable under a ruled/TEST_ONLY
            # mapping; otherwise the existing UNRESOLVED marker, never an
            # invention. Routed through the DR-6 consumer (Aaron 2026-08-10)
            # so this module cannot drift from dataset.event_stratum_of —
            # the TEST_ONLY synthetic value stays test-gated there.
            event_final = "NA_multi_event"
            try:
                from itsf.s0.dataset import event_stratum_of as _eso
                event_stratum = str(_eso(flag, event_rule,
                                         bool(getattr(methods, "test_only",
                                                      False))))
            except Exception:                            # noqa: BLE001
                event_stratum = UNRESOLVED_EVENT_STRATUM
        classes = {}
        for theta in theta_values:
            if not f.oracle_candidate:
                classes[_study.theta_key(theta)] = NON_TRADEABLE_CLASS
            else:
                classes[_study.theta_key(theta)] = (
                    TP_CLASS if float(f.y_cont) >= theta else FP_CLASS)
        day_strata.append(DayStratumFact(
            trade_date=f.trade_date, year=f.year,
            micro_execution_era=f.era,
            stability_epoch=_epoch_of_year(f.year),
            d_open=f.d_open,
            volatility_regime_label=vol_label, vol_status=vol_status,
            event_flag_final=event_final, event_na=flag is None,
            event_stratum=event_stratum, tp_fp_class=freeze(classes)))
    provenance["EV-5"] = PROV_ATOM_DAY_RECORD + "+" + PROV_CONFIG_DERIVED
    provenance["EV-5_dr2_status"] = vol_status
    provenance["EV-5_dr6_status"] = _method_status(event_rule, test_only)

    stratum_of = {s.trade_date: (s.year, s.volatility_regime_label,
                                 s.event_stratum) for s in day_strata}

    # --- AF2 atoms: per (engine, scenario) date -> record ------------------
    raw_records = (compute_result.get("records")
                   if isinstance(compute_result, Mapping) else None)
    record_pnl: dict = {}
    record_fields: dict = {}
    if isinstance(raw_records, Mapping):
        for eng, by_scn in raw_records.items():
            if not isinstance(by_scn, Mapping):
                continue
            for scn, recs in by_scn.items():
                pnl: dict = {}
                rows: dict = {}
                for rec in (recs or ()):
                    row = _report.record_to_formal_dict(rec)
                    rows[str(row["trade_date"])] = freeze(row)
                    pnl[str(row["trade_date"])] = float(
                        row["final_pnl_per_contract"])
                key = f"{eng}|{scn}"
                record_pnl[key] = freeze(pnl)
                record_fields[key] = freeze(rows)
    provenance["AF2"] = PROV_ATOM_TRADE_PATH_RECORD

    engines = tuple(_study.ENGINES)

    # --- EV-6 GridPoolFact -------------------------------------------------
    grid_pools: list = []
    for theta in theta_values:
        tkey = _study.theta_key(theta)
        tp_days, fp_days = _partition_from_facts(day_facts, theta,
                                                 constructible_dates)
        tp_pools = _gridmix._pools({d: 0.0 for d in tp_days}, stratum_of)
        fp_pools = _gridmix._pools({d: 0.0 for d in fp_days}, stratum_of)
        for eng in engines:
            for scn in scn_names:
                grid_pools.append(GridPoolFact(
                    theta_key=tkey, engine=eng, scenario=scn,
                    tp_pools=freeze(tp_pools), fp_pools=freeze(fp_pools),
                    tp_avail=freeze({k: len(v) for k, v in tp_pools.items()}),
                    fp_avail=freeze({k: len(v) for k, v in fp_pools.items()}),
                    n_tp_available=len(tp_days), n_fp_available=len(fp_days),
                    grid_stream_tag=int(_gridmix.GRID_STREAM_TAG),
                    stratum_axes=GRID_STRATUM_AXES))
    provenance["EV-6"] = PROV_ATOM_DAY_RECORD + "+" + PROV_CONFIG_DERIVED

    # --- EV-7 BootstrapInputFact ------------------------------------------
    seeds = tuple(int(s) for s in bootstrap_seeds)
    bootstrap_inputs: list = []
    for theta in theta_values:
        tkey = _study.theta_key(theta)
        tp_days, _fp = _partition_from_facts(day_facts, theta,
                                             constructible_dates)
        for eng in engines:
            for scn in scn_names:
                pnl = record_pnl.get(f"{eng}|{scn}", {})
                # `build_full_study_result` feeds the bootstrap
                # `[d_tp[d] for d in sorted(d_tp)]` — the same ordering,
                # rebuilt from AF2 atoms restricted to EV-1's authoritative
                # TP membership.
                ordered = [(d, float(pnl[d])) for d in sorted(tp_days)
                           if d in pnl]
                values = [v for _d, v in ordered]
                n = len(values)
                total = float(sum(values)) if values else 0.0
                mean_np = (float(np.asarray(values, dtype=float).mean())
                           if values else None)
                for blk in block_values:
                    bootstrap_inputs.append(BootstrapInputFact(
                        cell_key=f"{tkey}|{eng}|{scn}|block{blk}",
                        theta_key=tkey, engine=eng, scenario=scn,
                        block_len=int(blk), n=n,
                        series_sha256=_series_digest(ordered),
                        series_mean_sum_over_n=((total / n) if n else None),
                        series_mean_numpy=mean_np,
                        series_sum=total,
                        first_date=(ordered[0][0] if ordered else None),
                        last_date=(ordered[-1][0] if ordered else None),
                        seeds=seeds,
                        stats_stream_tag=int(_stats.STATS_STREAM_TAG),
                        block_stream_key=int(
                            _stats.block_stream_key(float(blk))),
                        n_boot=int(n_boot), ci_level=float(ci_level),
                        percentile_method_id=str(_stats.PERCENTILE_METHOD)))
    provenance["EV-7"] = PROV_ATOM_TRADE_PATH_RECORD
    provenance["EV-7_dr4_status"] = _method_status(
        getattr(methods, "bootstrap_method", None), test_only)

    # --- EV-8 NAObservationFact -------------------------------------------
    na_observations: list = []
    for table_name, frame, fields in (("features", ds.features_table,
                                       FEATURE_NA_FIELDS),
                                      ("labels", ds.labels_table,
                                       LABEL_NA_FIELDS)):
        n_rows = int(len(frame)) if frame is not None else 0
        for col in fields:
            if frame is None or col not in getattr(frame, "columns", ()):
                continue
            n_null = int(frame[col].isna().sum())
            na_observations.append(NAObservationFact(
                table=table_name, column=col, n_null=n_null,
                n_not_null=n_rows - n_null,
                observation_method_id=NA_OBSERVATION_METHOD_ID[
                    table_name]))
    provenance["EV-8"] = "raw_null_scan_of_S0Dataset_tables"

    # --- EV-9 FunnelFact ---------------------------------------------------
    funnel_obj = getattr(universe, "funnel", None)
    if funnel_obj is not None:
        # C27 (PHASE-E blind audit): a duck-typed object exposing `.funnel`
        # used to EARN the atom_S0Universe provenance and thereby DROP the
        # PARTIAL marker without any check running. The provenance label no
        # longer gates the marker (that is now `_reconcile_funnel`'s job),
        # and the capture itself fails closed to the reduced form unless
        # every frozen funnel level is genuinely present.
        try:
            level_dates = {
                "L0_scheduled_trading_days": tuple(funnel_obj.scheduled),
                "L1_observed_rth_days": tuple(funnel_obj.observed_rth),
                "L2_regular_full_session_candidates":
                    tuple(funnel_obj.regular),
                "L3_structurally_eligible_days":
                    tuple(funnel_obj.structurally_eligible),
                "L4_final_feature_construction_dates":
                    tuple(funnel_obj.final_dates),
                # the funnel's SIDE DIAGNOSTIC (frozen L49 ADR14 lookback
                # basis) — never a deduction stage, but `funnel_counts`
                # publishes it, so the reducer needs it to rebuild all ten
                # published keys rather than five of them.
                "side_diagnostic_complete_390_bar_rth_days":
                    tuple(funnel_obj.complete_390),
            }
            exclusions = dict(funnel_obj.exclusion_reason)
        except Exception:                                # noqa: BLE001
            level_dates, exclusions = None, None
    else:
        level_dates, exclusions = None, None
    if level_dates is not None:
        funnel = FunnelFact(level_dates=freeze(level_dates),
                            exclusion_reason=freeze(exclusions),
                            provenance=PROV_ATOM_UNIVERSE)
    else:
        funnel = FunnelFact(
            level_dates=freeze({
                "L4_final_feature_construction_dates":
                    tuple(f.trade_date for f in day_facts)}),
            exclusion_reason=freeze({}),
            provenance=PROV_NOT_SUPPLIED)
    provenance["EV-9"] = funnel.provenance

    # --- EV-10 F10MembershipFact ------------------------------------------
    events = getattr(universe, "events", None)
    # `S0Universe.f10_exclusive_counts()` / `raw_category_membership_counts()`
    # iterate `funnel.structurally_eligible`, so EV-10 must cover THAT
    # population for the reconcile comparison to be exact rather than
    # approximately-right-on-this-dataset.
    f10_population = tuple(funnel_obj.structurally_eligible) \
        if (funnel_obj is not None and level_dates is not None) \
        else tuple(f.trade_date for f in day_facts)
    record_flag_of = {f.trade_date: f.is_event_day for f in day_facts}
    f10_memberships: list = []
    f10_flag_disagreements: list = []
    for date in f10_population:
        raw, raw_prov = (), PROV_NOT_SUPPLIED
        final = record_flag_of.get(date)
        final_from_calendar = None
        if events is not None:
            try:
                raw = tuple(events.categories(date))
                # SECOND PATH for the exclusive category: the calendar's own
                # encoder, not the DayRecord feature the na_table was built
                # from. Where both exist they must agree.
                final_from_calendar = events.encode_f10(date)
                raw_prov = PROV_ATOM_UNIVERSE
            except Exception:                            # noqa: BLE001
                raw, raw_prov, final_from_calendar = (), PROV_NOT_SUPPLIED, None
        if (final_from_calendar is not None or date in record_flag_of):
            if (date in record_flag_of and raw_prov == PROV_ATOM_UNIVERSE
                    and final_from_calendar != final):
                f10_flag_disagreements.append(date)
        if date not in record_flag_of:
            final = final_from_calendar
        f10_memberships.append(F10MembershipFact(
            trade_date=date, raw_categories=raw,
            final_category=(final if final is not None else "NA_multi_event"),
            raw_provenance=raw_prov))
    provenance["EV-10"] = (PROV_ATOM_UNIVERSE if events is not None
                           else PROV_NOT_SUPPLIED)
    provenance["EV-10_flag_cross_check"] = (
        "agrees" if not f10_flag_disagreements else
        "DISAGREEMENT:" + ",".join(sorted(f10_flag_disagreements)[:5]))

    # --- EV-11 LabelAvailabilityFact --------------------------------------
    label_availability = tuple(
        _label_availability(r.trade_date, r, bars_by_date.get(r.trade_date))
        for r in records_sorted)
    provenance["EV-11"] = PROV_REDERIVED_FROM_BARS

    # --- EV-12 EstimatorIdentityFact --------------------------------------
    ruling = getattr(methods, "worst_day_estimator", None)
    estimator_identity = EstimatorIdentityFact(
        study_percentile_method=str(_study.PERCENTILE_METHOD),
        stability_percentile_method=str(_stability.PERCENTILE_METHOD),
        stats_percentile_method=str(_stats.PERCENTILE_METHOD),
        all_three_agree=(_study.PERCENTILE_METHOD
                         == _stability.PERCENTILE_METHOD
                         == _stats.PERCENTILE_METHOD),
        worst_day_estimator_ruling=(None if ruling is None else str(ruling)),
        # EXACTLY `build_full_study_result`'s own ternary, re-derived from
        # the config rather than copied from the payload it produced.
        estimator_status_expected=("resolved" if ruling is not None
                                   else "unresolved_DR-M6-H"))
    provenance["EV-12"] = PROV_FROZEN_CONSTANT + "+" + PROV_CONFIG_DERIVED

    # --- EV-13 FrozenHashObservationFact ----------------------------------
    if isinstance(frozen_hash_observations, Mapping):
        # CLOSEOUT (auditor-1 round-2 MEDIUM, C3): an EMPTY observation is a
        # caller error, never a byte-anchored provenance that compares
        # nothing. COMPLETENESS of the path set is checked one layer up, in
        # `reconcile_with_evidence`, against the DECLARED
        # `governance.frozen_hashes` — the only place the expected path set
        # is visible. (In production that declared set is itself pinned to
        # `guards.FROZEN_HASHES` by `validate_formal_payload`'s
        # expected-governance comparison, so observed == declared ==
        # FROZEN_HASHES transitively.)
        if not frozen_hash_observations:
            raise ValueError(
                "capture_evidence: frozen_hash_observations is EMPTY — pass "
                "the full re-hash result or omit the argument entirely; an "
                "empty observation cannot anchor governance.frozen_hashes")
        frozen_obs = FrozenHashObservationFact(
            observed=freeze({str(k): str(v) for k, v
                             in frozen_hash_observations.items()}),
            provenance=PROV_CALLER_SUPPLIED)
    else:
        frozen_obs = FrozenHashObservationFact(observed=freeze({}),
                                               provenance=PROV_NOT_SUPPLIED)
    provenance["EV-13"] = frozen_obs.provenance
    provenance["schema_version"] = SCHEMA_VERSION

    return CanonicalS0Evidence(
        schema_version=SCHEMA_VERSION,
        thetas=theta_values, engines=engines, scenarios=scn_names,
        eras=tuple(_study.ERA_AXIS), blocks=block_values,
        day_facts=tuple(day_facts),
        theoretical_paths=tuple(theoretical_paths),
        opening_ranges=opening_ranges,
        cost_scenarios=cost_scenarios,
        day_strata=tuple(day_strata),
        grid_pools=tuple(grid_pools),
        bootstrap_inputs=tuple(bootstrap_inputs),
        na_observations=tuple(na_observations),
        funnel=funnel,
        f10_memberships=tuple(f10_memberships),
        label_availability=label_availability,
        estimator_identity=estimator_identity,
        frozen_hash_observation=frozen_obs,
        record_pnl=freeze(record_pnl),
        record_fields=freeze(record_fields),
        provenance=freeze(provenance))


def _partition_from_facts(day_facts, theta, constructible):
    tp, fp = [], []
    for f in day_facts:
        if not f.oracle_candidate:
            continue
        if f.trade_date not in constructible:
            continue
        (tp if float(f.y_cont) >= theta else fp).append(f.trade_date)
    return tp, fp


# ===========================================================================
# 3. reducers — CanonicalS0Evidence -> the formal subtrees it can
#    AUTHORITATIVELY rebuild (matrix `pure_reducer` column).
#
# Byte/shape compatibility with the current formal schema is the contract:
# `tests/test_s0_report.py`'s shape pins must still pass on a payload whose
# corresponding subtree came from here instead of from the compute tree.
# The two prose leaves study.py emits as INLINE literals (they are not
# module constants, so they cannot be imported) are duplicated below with a
# CR-DUP marker AND pinned against real `build_study` output by
# `tests/test_s0_evidence.py`, so a drift is caught by a test rather than by
# a reader.
# ===========================================================================

# CR-DUP: study.py `build_study` per-theta `universe["definition"]`.
_DAY_UNIVERSE_DEFINITION = (
    "frozen App A / §7 L133: D_TP = tradeable days with "
    "Y_cont >= θ (boundary inclusive — Y_cont == θ IS a "
    "continuation event); D_FP = tradeable days with Y_cont < θ, "
    "traded under the SAME rules in direction d_open.")
# CR-DUP: study.py `build_study` per-theta `theoretical["note"]`.
_THEORETICAL_NOTE = (
    "frozen §7 — ECONOMIC UPPER BOUND ONLY: 10:00 entry, exit "
    "at the most favourable in-window price, minus BASE "
    "costs. Never an executable result and never compared to "
    "a strategy claim.")
# CR-DUP: study.py `_frequency_block` literals.
_FREQUENCY_DENOMINATOR_DEFINITION = (
    "N_directional_tradeable = days with d_open in {+1,-1} (frozen §5) "
    "AND a computable Y_cont (frozen §5 label table); equals "
    "DayRecord.oracle_candidate. Input-side untradeable disclosures "
    "stay IN this denominator.")
_FREQUENCY_NOTE = (
    "frozen §10.5 mandatory frequency output: 基础率 p, 每年可交易"
    "日数 (by_year.n_directional_tradeable), Oracle 月均频率. "
    "Appendix-A grid trade counts F(q,r) are produced downstream.")


def rebuild_structural_eras(evidence) -> dict:
    """`structural.eras` (matrix L013, currently_reconstructible = YES):
    era is a pure function of `trade_date` against the frozen
    `MICRO_ERA_BOUNDARY`, over the date population EV-1 carries."""
    dates = [f.trade_date for f in evidence.day_facts]
    return {ERA_PROXY: [d for d in dates if _rederived_era(d) == ERA_PROXY],
            ERA_ACTUAL: [d for d in dates if _rederived_era(d) == ERA_ACTUAL]}


def rebuild_structural_groups(evidence) -> dict:
    """`structural.groups` (L014/L015/L016) — by_year / leave_one_year_out /
    stability_epochs, all pure functions of the same date population.
    `stability_epochs` uses the DATASET's half-open string convention, which
    is the one this subtree is built with (matrix CR-4)."""
    dates = [f.trade_date for f in evidence.day_facts]
    by_year: dict = {}
    for d in dates:
        by_year.setdefault(d[:4], []).append(d)
    years = {y: list(v) for y, v in sorted(by_year.items())}
    loyo = {y: [d for d in dates if d[:4] != y] for y in years}
    epochs = {name: [d for d in dates if lo <= d[:4] < hi]
              for name, lo, hi in STABILITY_EPOCHS}
    return {"by_year": years, "leave_one_year_out": loyo,
            "stability_epochs": epochs}


def rebuild_era_axis_axes(evidence) -> list:
    """`era_axis.axes` (L111) — the frozen two-era axis."""
    return list(evidence.eras)


def rebuild_day_universe(evidence) -> dict:
    """`oracle_daily.<theta>.day_universe` for every frozen theta — the
    FULL real 12-key `build_study` shape (L017-L024).

    This is the highest-leverage reducer in the module: `tp_days`/`fp_days`
    (L023) is "the single highest-leverage unreconstructible leaf in the
    whole report" today, because `y_cont` reaches no sealed artifact. Here
    it is rebuilt from the EV-1 atoms."""
    out: dict = {}
    n_tradeable = sum(1 for f in evidence.day_facts if f.oracle_candidate)
    n_constructible = sum(1 for f in evidence.day_facts
                          if f.trade_constructible)
    n_disclosed = sum(1 for f in evidence.day_facts
                      if f.oracle_candidate and not f.trade_constructible)
    for theta in evidence.thetas:
        tp_days, fp_days = evidence.partition(theta)
        tp_all, fp_all = evidence.labelled_partition(theta)
        out[_study.theta_key(theta)] = {
            "theta": float(theta),
            "n_directional_tradeable": n_tradeable,
            "n_trade_constructible": n_constructible,
            "n_untradeable_disclosed": n_disclosed,
            "n_tp": len(tp_days),
            "n_fp": len(fp_days),
            "n_tp_labelled": len(tp_all),
            "n_fp_labelled": len(fp_all),
            "tp_days": list(tp_days),
            "fp_days": list(fp_days),
            "conservation": {
                "tradeable_equals_constructible_plus_disclosed":
                    n_tradeable == n_constructible + n_disclosed,
                "constructible_equals_tp_plus_fp":
                    n_constructible == len(tp_days) + len(fp_days),
                "tradeable_equals_tp_plus_fp_plus_disclosed":
                    n_tradeable == len(tp_days) + len(fp_days) + n_disclosed,
                "labelled_equals_tp_plus_fp":
                    n_tradeable == len(tp_all) + len(fp_all),
            },
            "definition": _DAY_UNIVERSE_DEFINITION,
        }
    return out


def _frequency_cell(slice_facts, tradeable, traded, tp_labelled, tp_traded):
    """study.py `_frequency_cell`'s arithmetic over EV-1 facts. The
    denominators are EV-1's `oracle_candidate` population — the very
    quantity L065/L068 cannot reconstruct today."""
    dates = {f.trade_date for f in slice_facts}
    months = sorted({f.trade_date[:7] for f in slice_facts})
    n_dir = len(dates & tradeable)
    n_lab = len(dates & tp_labelled)
    n_trd = len(dates & tp_traded)
    n_traded_days = len(dates & traded)
    return {
        "n_days_in_sample": len(dates),
        "n_directional_tradeable": n_dir,
        "n_trade_constructible": n_traded_days,
        "n_continuation_days_labelled": n_lab,
        "n_continuation_days_traded": n_trd,
        "continuation_base_rate_p": (n_lab / n_dir) if n_dir else None,
        "continuation_base_rate_p_traded_only": (
            (n_trd / n_dir) if n_dir else None),
        "n_months_in_slice": len(months),
        "oracle_monthly_frequency": (n_trd / len(months)) if months else None,
        "oracle_monthly_frequency_labelled": (
            (n_lab / len(months)) if months else None),
    }


def rebuild_frequency(evidence) -> dict:
    """`frequency` (A6, L062-L070) for every frozen theta. L068
    (`continuation_base_rate_p`) is the highest-leverage UNVERIFIED anchor
    in the report — VF-7's `F_expected` recompute reads it off the payload
    — and it becomes atom-derived here."""
    facts = list(evidence.day_facts)
    tradeable = frozenset(f.trade_date for f in facts if f.oracle_candidate)
    traded = frozenset(f.trade_date for f in facts if f.trade_constructible)
    by_year: dict = {}
    for f in facts:
        by_year.setdefault(f.year, []).append(f)
    out: dict = {}
    for theta in evidence.thetas:
        tp_all, _fp_all = evidence.labelled_partition(theta)
        tp_days, _fp = evidence.partition(theta)
        tp_labelled, tp_traded = frozenset(tp_all), frozenset(tp_days)

        def cell(rows):
            return _frequency_cell(rows, tradeable, traded, tp_labelled,
                                   tp_traded)

        out[_study.theta_key(theta)] = {
            "denominator_definition": _FREQUENCY_DENOMINATOR_DEFINITION,
            "note": _FREQUENCY_NOTE,
            _study.POOLED: cell(facts),
            "by_era": {era: cell([f for f in facts if f.era == era])
                       for era in evidence.eras},
            "by_year": {y: cell(rows) for y, rows in sorted(by_year.items())},
        }
    return out


def rebuild_theoretical_oracle(evidence) -> dict:
    """`theoretical_oracle` (A3, L034-L040) from EV-2.

    DR-8 CAVEAT (never silent): the `worst_day_pnl_percentiles` sub-block
    is produced by `study._worst_day_percentiles`, i.e. the SAME disclosed-
    but-UNAPPROVED numpy linear-interpolation convention the producer uses.
    Rebuilding it from atoms makes the value REPRODUCIBLE, not APPROVED —
    `reconcile_with_evidence` therefore emits a
    `PARTIAL:theoretical_oracle.worst_day_pnl_percentiles:DR-8...` marker
    and never counts it as coverage."""
    theo = {p.trade_date: p.pnl_per_contract
            for p in evidence.theoretical_paths}
    era_of = {f.trade_date: f.era for f in evidence.day_facts}
    out: dict = {}
    for theta in evidence.thetas:
        tp_days, _fp = evidence.partition(theta)
        pairs = [(d, theo[d]) for d in tp_days if d in theo]
        out[_study.theta_key(theta)] = {
            "scenario": _study.BASE_SCENARIO_NAME,
            "note": _THEORETICAL_NOTE,
            **_study._by_era_and_pooled(pairs, era_of, "daily_usd"),
        }
    return out


reducers: Mapping[str, Callable] = MappingProxyType({
    "structural.eras": rebuild_structural_eras,
    "structural.groups": rebuild_structural_groups,
    "era_axis.axes": rebuild_era_axis_axes,
    "oracle_daily.day_universe": rebuild_day_universe,
    "frequency": rebuild_frequency,
    "theoretical_oracle": rebuild_theoretical_oracle,
})


# ===========================================================================
# 4. reconcile_with_evidence — the evidence-anchored gate
# ===========================================================================
def split_problems(items) -> tuple[list, list]:
    """(hard_problems, partial_markers). Only the FIRST list may block a
    seal; the second is a disclosure list. Never raises."""
    hard, partial = [], []
    try:
        seq = list(items)
    except Exception:                                    # noqa: BLE001
        return (["split_problems_input_not_iterable"], [])
    for item in seq:
        text = item if isinstance(item, str) else _report._safe_repr(item)
        (partial if text.startswith(PARTIAL_PREFIX) else hard).append(text)
    return hard, partial


def _num(v):
    return (isinstance(v, (int, float)) and not isinstance(v, bool)
            and math.isfinite(v))


def _close(a, b) -> bool:
    return _num(a) and _num(b) and math.isclose(float(a), float(b),
                                                rel_tol=1e-9, abs_tol=1e-9)


def _eq_number_or_none(a, b) -> bool:
    if a is None and b is None:
        return True
    return _close(a, b)


def _get(obj, *path, default=None):
    """Walk a nested mapping without ever raising."""
    cur = obj
    for key in path:
        if not isinstance(cur, Mapping):
            return default
        try:
            cur = cur.get(key, default)
        except Exception:                                # noqa: BLE001
            return default
        if cur is default:
            return default
    return cur


_MC_FILE_RE_PREFIX = "MC_HANDOFF_"


# ===========================================================================
# 3b. THE DISPOSITION REGISTRY (M6.1.4-ARCH, finding F-2)
# ===========================================================================
# WHY THIS EXISTS
# ---------------
# F-2 RECURRED after a round that added `checks[...]` flags and an AST
# tripwire. An independent reviewer proved a STRIPPED evidence object seals
# through the real renderer:
#
#   dataclasses.replace(evidence, opening_ranges=(), day_strata=(),
#                       bootstrap_inputs=(), provenance=freeze({}))
#
# produced hard_problems == [], the SAME 11 PARTIAL markers as the honest
# run, and BYTE-IDENTICAL sealed files. Measurement during the design phase
# found THREE further facts the finding did not name:
#
#   * `record_pnl` with the (engine|scenario) keys present but every inner
#     row dict emptied is ALSO silent (the `ran` flag lives inside the
#     date-intersection loop, and no marker was registered for the field);
#   * `estimator_identity` with all three percentile-method strings blanked
#     is silent, because reconcile trusted the CAPTURED `all_three_agree`
#     boolean instead of re-deriving it;
#   * and, decisively, PARTIAL strips are silent too — EV-3 at 1 of 32
#     rows, EV-7 at 1 of 32 cells and EV-5 at 23 of 46 rows each still
#     produce hard == [] and the identical marker list.
#
# That last class is why NON-EMPTINESS is not the fix. `ran = compared_count
# > 0` passes on 1-of-32. THE GATE IS COMPLETENESS:
#
#     complete  <=>  compared_count >= applicable
#
# where `applicable` is produced by a registry-owned population callable
# that NEVER READS THE FIELD IT GUARDS, so an emptied field cannot shrink
# its own expectation. `ran` survives only as a derived convenience.
#
# A legitimately-empty population is therefore always DERIVED from an
# authoritative second source (e.g. "no trade-constructible day at all =>
# zero sealed rows to anchor => EV-3 not applicable"), never a blanket
# "empty means fine" (which would mask a stripped field) and never a
# blanket "empty means fail" (which would break an honest zero-sample run).
#
# DISPOSITION VOCABULARY — and an honest note about two of the five names.
# `PURE_METADATA` and `EXPLICIT_NOT_APPLICABLE` carry ZERO top-level
# members, and that is deliberate: every field of `CanonicalS0Evidence` is
# load-bearing, and giving any of them a static free pass would be the same
# failure mode as the blanket rule above. `PURE_METADATA` has real members
# only at the PROVENANCE-KEY level (`PROVENANCE_REGISTRY`, the EV-N label
# strings); `EXPLICIT_NOT_APPLICABLE` exists only as a RUNTIME outcome
# state derived from an authoritative population, never as a static
# registration. The empty categories are reported rather than filled.
# ===========================================================================
REQUIRED_COMPARED = "required-and-compared"
CONDITIONAL = "conditionally-applicable"
EXPLICIT_PARTIAL = "explicitly-PARTIAL"
PURE_METADATA = "pure-metadata"
EXPLICIT_NOT_APPLICABLE = "explicitly-not-applicable"

_KIND_HARD = "hard"
_KIND_PARTIAL = "partial"


@dataclass(frozen=True)
class CheckOutcome:
    """The structured result of ONE registered check.

    `ran`, `complete` and `not_applicable` are DERIVED properties, never
    assignable fields — a branch cannot report "I ran" while comparing
    nothing, which is exactly how the EV-3/EV-7 partial strips and the
    empty-inner `record_pnl` slipped through.
    """
    check: str
    field: str | None
    applicable: int
    compared_count: int
    hard_problems: tuple = ()
    partial_markers: tuple = ()
    expected_tokens: frozenset | None = None
    actual_tokens: tuple = ()

    @property
    def ran(self) -> bool:
        """Derived convenience ONLY. `compared_count > 0` is NOT the gate —
        see `complete` (a 1-of-32 EV-3 satisfies `ran` and still hides a
        stripped field)."""
        return self.compared_count > 0

    @property
    def complete(self) -> bool:
        """THE GATE (M6.1.4-R2). Completeness is MULTISET EQUALITY of the
        emitted tokens against the expected entity set whenever tokens are
        supplied, so the right NUMBER of the WRONG tokens is INCOMPLETE —
        which is exactly what `compared_count >= applicable` could never
        see. That count comparison is retired as the criterion of record:
        it survives only as a NECESSARY (never sufficient) conjunct, and
        alone only for the four byte-side rails that own no evidence field
        and therefore no leaf."""
        if self.expected_tokens is not None:
            counted = _Counter(self.actual_tokens)
            if not (set(counted) == set(self.expected_tokens)
                    and all(v == 1 for v in counted.values())):
                return False
        return self.compared_count >= self.applicable

    @property
    def not_applicable(self) -> bool:
        return self.applicable == 0


@dataclass(frozen=True)
class CheckSpec:
    """One registered check: which field it consumes, which authoritative
    population sizes it, and what an INCOMPLETE consumption means."""
    field: str | None
    population: str
    incomplete_kind: str
    partial_section: str | None = None
    partial_reason: str = ""
    na_section: str | None = None
    na_reason: str = ""
    never_ran_section: str | None = None
    never_ran_reason: str = ""

    def markers_for(self, outcome: CheckOutcome) -> tuple:
        if outcome.not_applicable and self.na_section is not None:
            return (f"{PARTIAL_PREFIX}{self.na_section}:{self.na_reason}",)
        if (not outcome.not_applicable and not outcome.complete
                and self.incomplete_kind == _KIND_PARTIAL
                and self.partial_section is not None):
            return (f"{PARTIAL_PREFIX}{self.partial_section}:"
                    f"{self.partial_reason}",)
        return ()

    def never_ran_markers(self) -> tuple:
        if self.never_ran_section is not None:
            return (f"{PARTIAL_PREFIX}{self.never_ran_section}:"
                    f"{self.never_ran_reason}",)
        if self.partial_section is not None:
            return (f"{PARTIAL_PREFIX}{self.partial_section}:"
                    f"{self.partial_reason}",)
        return ()


@dataclass(frozen=True)
class FieldDisposition:
    """The ONE registered disposition of ONE `CanonicalS0Evidence` field.

    `empty_hard_codes` / `empty_partial_sections` are the registry's
    DECLARATION of what emptying (or partially stripping) this field must
    produce. The behavioural tests are generated from them, so a check that
    quietly stops comparing fails the test rather than updating the
    expectation — the registry is the oracle, never a copy of the code.
    """
    disposition: str
    population_source: str
    legitimately_empty: str
    checks: tuple
    empty_hard_codes: tuple = ()
    empty_partial_sections: tuple = ()


# --- the exact PARTIAL reason texts, extracted verbatim so an honest run's
#     marker list (and therefore HANDOFF_ADMISSION.json's bytes) is
#     unchanged by this refactor. ------------------------------------------
_R_FUNNEL = ("EV-9 not consumed by a comparison — either no S0Universe was "
             "supplied to capture_evidence (the L0..L3 date tuples behind "
             "the counts are absent) or the payload carries no usable "
             "funnel_counts (matrix L001)")
_R_F10 = ("EV-10 not fully consumed — the exclusive partition and/or the "
          "raw multi-hot membership could not be compared (the raw sets "
          "need the EventCalendar); matrix L002/L003, and L003 has NO "
          "verifier at all in the tree today")
_R_LABEL = "EV-11 not consumed by a comparison (matrix L012)"
_R_NA = ("EV-8 not consumed by a comparison — the na/not_na counts are "
         "producer-only for this payload (CR-1 open at every level)")
_R_FIELD_BINDING = ("the sealed rows were NOT bound to evidence.record_fields "
                    "field-for-field — post-capture byte tampering is "
                    "UNCHECKED for this payload")
_R_UNTRADEABLE = ("not a row list in this payload, so EV-1's "
                  "untradeable_reason / y_cont could not be compared (matrix "
                  "L119 — the only place y_cont reaches the sealed payload)")
_R_COVERAGE = ("not recomputed from the sealed sizing_anchor_usd rows for "
               "this payload (matrix L059/L060)")
_R_FROZEN_HASHES = ("EV-13 comparison did not run over a non-empty observed "
                    "set — the seal-boundary equality stays tautological "
                    "(matrix L127)")
_R_STREAM_TAGS = ("absent from this payload (CR-9 prose leaf L122 not "
                  "emitted)")
_R_AF1_AXIS = ("no S0Universe was supplied, so EV-9 carries no "
               "L3_structurally_eligible_days level and the AF1 day "
               "population has NO authority that does not read the families "
               "it guards; leaf completeness is SKIPPED for every leaf on "
               "that axis rather than sized from the guarded family")

# --- NOT_APPLICABLE reasons: emitted ONLY when an authoritative population
#     is genuinely empty. Never reachable by emptying the guarded field. ---
_NA_EV2 = ("no day is in the theoretical union at either frozen theta "
           "(authoritative population: EV-1 oracle candidates x "
           "study.FROZEN_THETAS), so there is no EV-2 path to compare")
_NA_EV3 = ("no trade-constructible day exists (authoritative population: "
           "EV-1.trade_constructible), so there is no sealed sizing row for "
           "an opening range to anchor")

CHECK_REGISTRY: Mapping[str, CheckSpec] = MappingProxyType({
    # --- axes: bound to the frozen module constants ----------------------
    "schema_version.binding": CheckSpec(
        "schema_version", "one", _KIND_HARD),
    "axis.thetas": CheckSpec("thetas", "axis_thetas", _KIND_HARD),
    "axis.engines": CheckSpec("engines", "axis_engines", _KIND_HARD),
    "axis.scenarios": CheckSpec("scenarios", "axis_scenarios", _KIND_HARD),
    "axis.eras": CheckSpec("eras", "axis_eras", _KIND_HARD),
    "axis.blocks": CheckSpec("blocks", "axis_blocks", _KIND_HARD),
    # --- EV-1 -------------------------------------------------------------
    "EV-1.sealed_day_membership": CheckSpec(
        "day_facts", "sealed_dates", _KIND_HARD),
    "EV-1.reducer_subtrees": CheckSpec(
        "day_facts", "reducer_keys", _KIND_HARD),
    "EV-1.stability_views": CheckSpec(
        "day_facts", "theta_eng_scn", _KIND_HARD),
    "EV-1.untradeable": CheckSpec(
        "day_facts", "one", _KIND_PARTIAL,
        "disclosures.untradeable", _R_UNTRADEABLE),
    "EV-1.coverage_budgets": CheckSpec(
        "day_facts", "coverage_cells", _KIND_PARTIAL,
        "sizing_outputs.coverage.by_budget_usd", _R_COVERAGE),
    # --- EV-2 -------------------------------------------------------------
    "EV-2.tp_union_coverage": CheckSpec(
        "theoretical_paths", "tp_union", _KIND_HARD,
        na_section="theoretical_oracle.not_applicable", na_reason=_NA_EV2),
    "EV-2.entry_fill_binding": CheckSpec(
        "theoretical_paths", "tp_union_rows", _KIND_HARD,
        na_section="records.entry_fill.not_applicable", na_reason=_NA_EV2),
    # --- EV-3 -------------------------------------------------------------
    "EV-3.record_sizing_anchor": CheckSpec(
        "opening_ranges", "sealed_rows", _KIND_HARD,
        na_section="records.sizing_anchor.not_applicable", na_reason=_NA_EV3),
    "EV-3.sizing_rows": CheckSpec(
        "opening_ranges", "sizing_rows", _KIND_HARD,
        na_section="sizing_outputs.rows.not_applicable", na_reason=_NA_EV3),
    # --- EV-4 .. EV-8 -----------------------------------------------------
    "EV-4.cost_snapshots": CheckSpec(
        "cost_scenarios", "axis_scenarios", _KIND_HARD),
    "EV-5.day_strata": CheckSpec("day_strata", "af1_days", _KIND_HARD),
    "EV-6.grid_pools": CheckSpec("grid_pools", "theta_eng_scn", _KIND_HARD),
    "EV-7.cell_coverage": CheckSpec(
        "bootstrap_inputs", "bootstrap_cells", _KIND_HARD),
    "EV-8.field_coverage": CheckSpec(
        "na_observations", "na_fields", _KIND_HARD),
    "EV-8.na_table": CheckSpec(
        "na_observations", "na_fields", _KIND_PARTIAL,
        "structural.na_table", _R_NA),
    # --- EV-9 .. EV-13 ----------------------------------------------------
    "EV-9.funnel_counts": CheckSpec(
        "funnel", "funnel_levels", _KIND_PARTIAL,
        "structural.funnel_counts", _R_FUNNEL),
    "EV-10.exclusive_partition": CheckSpec(
        "f10_memberships", "f10_population", _KIND_HARD),
    "EV-10.raw_membership": CheckSpec(
        "f10_memberships", "f10_population", _KIND_PARTIAL,
        "structural.f10_counts", _R_F10),
    "EV-11.day_coverage": CheckSpec(
        "label_availability", "af1_days", _KIND_HARD),
    "EV-11.label_anchor_availability": CheckSpec(
        "label_availability", "af1_days", _KIND_PARTIAL,
        "structural.label_anchor_availability", _R_LABEL),
    "EV-12.estimator_identity": CheckSpec(
        "estimator_identity", "estimator_leaves", _KIND_HARD),
    "EV-13.frozen_hashes": CheckSpec(
        "frozen_hash_observation", "declared_hashes", _KIND_PARTIAL,
        "governance.frozen_hashes", _R_FROZEN_HASHES),
    # --- AF2 projections + provenance -------------------------------------
    "AF2.record_fields": CheckSpec(
        "record_fields", "sealed_rows", _KIND_PARTIAL,
        "records.field_binding", _R_FIELD_BINDING),
    "AF2.record_pnl": CheckSpec("record_pnl", "sealed_rows", _KIND_HARD),
    "provenance.registry": CheckSpec(
        "provenance", "provenance_keys", _KIND_HARD),
    # --- byte-side rails: consume the SEALED BYTES, no evidence field -----
    "bytes.parse": CheckSpec(None, "sealed_files", _KIND_HARD),
    "bytes.record_ranges": CheckSpec(None, "sealed_rows", _KIND_HARD),
    "bytes.manifest_counts": CheckSpec(None, "sealed_files", _KIND_HARD),
    "CR-9.stream_tags": CheckSpec(
        None, "one", _KIND_PARTIAL,
        "disclosures.method_conventions.stream_tags", _R_STREAM_TAGS),
})

FIELD_REGISTRY: Mapping[str, FieldDisposition] = MappingProxyType({
    "schema_version": FieldDisposition(
        REQUIRED_COMPARED, "the frozen module constant SCHEMA_VERSION",
        "never — a single constant", ("schema_version.binding",),
        ("evidence_schema_version_mismatch",),
        ()),
    "thetas": FieldDisposition(
        REQUIRED_COMPARED, "study.FROZEN_THETAS", "never — frozen axis",
        ("axis.thetas",),
        ("evidence_check_incomplete:axis.thetas",),
        ()),
    "engines": FieldDisposition(
        REQUIRED_COMPARED, "study.ENGINES", "never — frozen axis",
        ("axis.engines",),
        ("evidence_check_incomplete:axis.engines",),
        ()),
    "scenarios": FieldDisposition(
        REQUIRED_COMPARED, "_SCENARIO_AXIS (frozen §6)",
        "never — frozen axis", ("axis.scenarios",),
        ("evidence_check_incomplete:axis.scenarios",),
        ()),
    "eras": FieldDisposition(
        REQUIRED_COMPARED, "study.ERA_AXIS", "never — frozen axis",
        ("axis.eras",),
        ("evidence_check_incomplete:axis.eras",),
        ()),
    "blocks": FieldDisposition(
        REQUIRED_COMPARED, "FROZEN_BLOCKS (frozen §9)",
        "never — frozen axis", ("axis.blocks",),
        ("evidence_check_incomplete:axis.blocks",),
        ()),
    "day_facts": FieldDisposition(
        REQUIRED_COMPARED,
        "the date union parsed from the sealed MC_HANDOFF bytes, plus the "
        "six reducer subtrees and the theta x engine x scenario cell grid",
        "never — an empty EV-1 can build no reducer subtree and matches no "
        "sealed row",
        ("EV-1.sealed_day_membership", "EV-1.reducer_subtrees",
         "EV-1.stability_views", "EV-1.untradeable",
         "EV-1.coverage_budgets"),
        ("evidence_ev1_missing_for_sealed_date",
         "evidence_check_incomplete:EV-1.sealed_day_membership"),
        ()),
    "theoretical_paths": FieldDisposition(
        CONDITIONAL,
        "the theoretical union: EV-1 oracle candidates partitioned at "
        "study.FROZEN_THETAS (read from day_facts, never from EV-2)",
        "applicable == 0 iff no day is TP at either frozen theta — then "
        "NOT_APPLICABLE, derived from EV-1",
        ("EV-2.tp_union_coverage", "EV-2.entry_fill_binding"),
        ("evidence_ev2_missing_for_tp_day",
         "evidence_check_incomplete:EV-2.tp_union_coverage"),
        ()),
    "opening_ranges": FieldDisposition(
        CONDITIONAL,
        "the sealed-record universe union(theta) (tp | fp), derived from "
        "EV-1.trade_constructible (never from EV-3)",
        "applicable == 0 iff no trade-constructible day exists — then "
        "NOT_APPLICABLE, derived from EV-1",
        ("EV-3.record_sizing_anchor", "EV-3.sizing_rows"),
        ("evidence_ev3_missing_for_applicable_day",
         "evidence_check_incomplete:EV-3.record_sizing_anchor",
         "evidence_ev3_sizing_row_not_anchored",
         "evidence_check_incomplete:EV-3.sizing_rows"),
        ()),
    "cost_scenarios": FieldDisposition(
        REQUIRED_COMPARED, "the frozen §6 four-scenario axis",
        "never — frozen axis", ("EV-4.cost_snapshots",),
        ("evidence_ev4_snapshot_absent",
         "evidence_check_incomplete:EV-4.cost_snapshots"),
        ()),
    "day_strata": FieldDisposition(
        REQUIRED_COMPARED,
        "the AF1 day population = every EV-1 trade_date",
        "applicable == 0 iff day_facts is empty, which is itself hard at "
        "EV-1.sealed_day_membership",
        ("EV-5.day_strata",),
        ("evidence_ev5_missing_for_day",
         "evidence_check_incomplete:EV-5.day_strata"),
        ()),
    "grid_pools": FieldDisposition(
        REQUIRED_COMPARED, "theta_keys x engines x scenarios",
        "never — frozen axes", ("EV-6.grid_pools",),
        ("evidence_grid_pool_missing",
         "evidence_check_incomplete:EV-6.grid_pools"),
        ()),
    "bootstrap_inputs": FieldDisposition(
        REQUIRED_COMPARED,
        "theta_keys x engines x scenarios x blocks (the A7 cell product)",
        "never — all four axes are frozen and separately bound",
        ("EV-7.cell_coverage",),
        ("evidence_ev7_cell_absent",
         "evidence_check_incomplete:EV-7.cell_coverage"),
        ()),
    "na_observations": FieldDisposition(
        REQUIRED_COMPARED,
        "the frozen dataset.FEATURE_NA_FIELDS + LABEL_NA_FIELDS lists",
        "never — the frozen NA field list is the schema contract",
        ("EV-8.field_coverage", "EV-8.na_table"),
        ("evidence_na_observation_absent",
         "evidence_check_incomplete:EV-8.field_coverage"),
        ("structural.na_table",)),
    "funnel": FieldDisposition(
        CONDITIONAL, "the six frozen funnel level names",
        "a reduced capture (no S0Universe) leaves levels absent — a "
        "dedicated PARTIAL, never silence",
        ("EV-9.funnel_counts",),
        (),
        ("structural.funnel_counts",)),
    "f10_memberships": FieldDisposition(
        CONDITIONAL,
        "the funnel's L3_structurally_eligible_days (the population "
        "S0Universe.f10_exclusive_counts iterates), falling back to the "
        "EV-1 day population",
        "the RAW multi-hot half needs the EventCalendar; without it a "
        "dedicated PARTIAL. The EXCLUSIVE partition is always required",
        ("EV-10.exclusive_partition", "EV-10.raw_membership"),
        ("evidence_check_incomplete:EV-10.exclusive_partition",),
        ("structural.f10_counts",)),
    "label_availability": FieldDisposition(
        REQUIRED_COMPARED, "the AF1 day population = every EV-1 trade_date",
        "applicable == 0 iff day_facts is empty (hard elsewhere)",
        ("EV-11.day_coverage", "EV-11.label_anchor_availability"),
        ("evidence_ev11_missing_for_day",
         "evidence_check_incomplete:EV-11.day_coverage"),
        ("structural.label_anchor_availability",)),
    "estimator_identity": FieldDisposition(
        REQUIRED_COMPARED,
        "the three LIVE module constants study/stability/stats."
        "PERCENTILE_METHOD plus the theta x scenario e2_worst_days cells",
        "never — three module constants always exist",
        ("EV-12.estimator_identity",),
        ("evidence_percentile_constant_drift",),
        ()),
    "frozen_hash_observation": FieldDisposition(
        EXPLICIT_PARTIAL,
        "the payload's DECLARED governance.frozen_hashes key set",
        "not supplied is the honest default and is DISCLOSED by a "
        "permanent-shaped PARTIAL, never dropped",
        ("EV-13.frozen_hashes",),
        (),
        ("governance.frozen_hashes",)),
    "record_pnl": FieldDisposition(
        REQUIRED_COMPARED,
        "(engine, scenario) x the parsed sealed-row dates",
        "applicable == 0 iff no sealed row parsed, which is hard at "
        "bytes.parse", ("AF2.record_pnl",),
        ("evidence_record_pnl_absent",
         "evidence_check_incomplete:AF2.record_pnl"),
        ()),
    "record_fields": FieldDisposition(
        REQUIRED_COMPARED,
        "(engine, scenario) x the parsed sealed-row dates",
        "applicable == 0 iff no sealed row parsed (hard at bytes.parse)",
        ("AF2.record_fields",),
        ("evidence_record_fields_absent",),
        ("records.field_binding",)),
    "provenance": FieldDisposition(
        REQUIRED_COMPARED,
        "the frozen PROVENANCE_REGISTRY key set",
        "never — the registry is a frozen table",
        ("provenance.registry",),
        ("evidence_provenance_key_absent",
         "evidence_check_incomplete:provenance.registry"),
        ()),
})


# ===========================================================================
# 4b. LEAF LINEAGE (M6.1.4-R2) — the registry and the completeness criterion
#     ONE LEVEL BELOW `FIELD_REGISTRY`.
#
# F-2 recurred because `CheckSpec.field` names a TOP-LEVEL field, `applicable`
# counts ELEMENTS and `compared_count` counts CONSUMED ELEMENTS. Below the
# element there was no registry, no completeness criterion and no disclosure,
# so "a captured leaf that no comparison ever reads" was both possible and
# structurally invisible.
#
# The criterion of record is now TOKEN COMPLETENESS:
#
#     complete  <=>  actual_tokens == expected_tokens   (as MULTISETS)
#
# `compared_count >= applicable` is retired as a completion criterion. The two
# counters survive ONLY as derived `len()`s so the six-seed determinism
# comparison basis in the review packet still renders.
#
# HONEST SCOPE, stated once and never softened: token completeness proves a
# check VISITED every leaf. It does NOT prove the leaf's VALUE has an
# independent authority. Ten registered leaves have none at any granularity;
# they are registered DISCLOSURE_UNVERIFIED and each carries a PARTIAL naming
# its own path. This round must never be described as "every captured leaf is
# now verified".
# ===========================================================================
INDEPENDENT_BOUND = "INDEPENDENT_BOUND"
DERIVED_REDUNDANT = "DERIVED_REDUNDANT"
DISCLOSURE_UNVERIFIED = "DISCLOSURE_UNVERIFIED"
DR_PARTIAL = "DR_PARTIAL"
AUTHORITATIVE_NOT_APPLICABLE = "AUTHORITATIVE_NOT_APPLICABLE"
REMOVE_UNUSED = "REMOVE_UNUSED"

_LEAF_DISPOSITIONS = frozenset({
    INDEPENDENT_BOUND, DERIVED_REDUNDANT, DISCLOSURE_UNVERIFIED, DR_PARTIAL,
    AUTHORITATIVE_NOT_APPLICABLE, REMOVE_UNUSED})


@dataclass(frozen=True)
class LeafSpec:
    """ONE registered captured leaf (or leaf-path pattern).

    `entity_axis` names the population the leaf's tokens are measured
    against, and `ENTITY_AXIS_AUTHORITIES` records — as data, enforced by a
    test — which evidence families that axis reads. An axis may NEVER read
    the family it guards; that is the F-2 invariant, one level down.
    """
    family: str
    leaf: str
    disposition: str
    entity_axis: str
    key_vocab_axis: str = ""
    authority: str = ""
    marker_section: str = ""

    @property
    def leaf_id(self) -> str:
        return f"{self.family}.{self.leaf}"


@dataclass(frozen=True)
class EntityAxisAuthority:
    """Where one entity axis comes from, and which LEAVES it reads to get
    there.

    `reads` is leaf-precise on purpose. Family-level would be a stronger
    but WRONG approximation: `excluded_days` is built from
    `EV-9.level_dates` and guards `EV-9.exclusion_reason` — a different leaf
    of the same family, and `level_dates` is independently bound to the ten
    published funnel_counts keys. The invariant that matters is that an axis
    never reads the leaf it guards, and that is what the test enforces.
    """
    source: str
    reads: tuple = ()


ENTITY_AXIS_AUTHORITIES: Mapping[str, EntityAxisAuthority] = MappingProxyType({
    "singleton": EntityAxisAuthority("the constant 1"),
    "af1_days": EntityAxisAuthority(
        "EV-9.level_dates['L3_structurally_eligible_days'] (S0Universe atom); "
        "UNAUTHORITATIVE when no universe was supplied — then a dedicated "
        "PARTIAL, never a fallback to the guarded family", ("EV-9.level_dates",)),
    "f10_population": EntityAxisAuthority(
        "the same EV-9 L3 population S0Universe.f10_exclusive_counts iterates",
        ("EV-9.level_dates",)),
    "sealed_dates": EntityAxisAuthority("the parsed MC_HANDOFF bytes"),
    "sealed_cell_dates": EntityAxisAuthority(
        "(engine|scenario, date) over the parsed MC_HANDOFF bytes"),
    "record_field_tokens": EntityAxisAuthority(
        "(engine|scenario, date, field) over the parsed bytes x "
        "report.FORMAL_RECORD_FIELDS"),
    "constructible_days": EntityAxisAuthority(
        "EV-1.trade_constructible", ("EV-1.trade_constructible",)),
    "constructible_days_long": EntityAxisAuthority(
        "EV-1.trade_constructible narrowed to d_open == +1", ("EV-1.trade_constructible", "EV-1.d_open")),
    "constructible_days_short": EntityAxisAuthority(
        "EV-1.trade_constructible narrowed to d_open == -1", ("EV-1.trade_constructible", "EV-1.d_open")),
    "tp_union": EntityAxisAuthority(
        "EV-1 oracle candidates x study.FROZEN_THETAS", ("EV-1.oracle_candidate", "EV-1.y_cont",
         "EV-1.trade_constructible")),
    "theta_eng_scn": EntityAxisAuthority("frozen theta x engine x scenario"),
    "boot_cells": EntityAxisAuthority("theta x engine x scenario x block"),
    "na_fields": EntityAxisAuthority(
        "dataset.FEATURE_NA_FIELDS + LABEL_NA_FIELDS"),
    "funnel_levels": EntityAxisAuthority("the frozen _FUNNEL_LEVELS tuple"),
    "excluded_days": EntityAxisAuthority(
        "the EV-9 level DIFFERENCES (L0-L1) | (L1-L2) | (L2-L3)", ("EV-9.level_dates",)),
    "frozen_hash_paths": EntityAxisAuthority(
        "the DECLARED governance.frozen_hashes key set (empty, i.e. "
        "AUTHORITATIVE_NOT_APPLICABLE, when no observation was supplied)"),
    "provenance_keys": EntityAxisAuthority("the frozen PROVENANCE_REGISTRY"),
    "axis_thetas": EntityAxisAuthority("study.FROZEN_THETAS"),
    "axis_engines": EntityAxisAuthority("study.ENGINES"),
    "axis_scenarios": EntityAxisAuthority("the frozen four-scenario axis"),
    "axis_eras": EntityAxisAuthority("study.ERA_AXIS"),
    "axis_blocks": EntityAxisAuthority("FROZEN_BLOCKS"),
})

# Dynamic-Mapping key vocabularies. A Mapping leaf is checked as an EXACT
# key set x entity set against one of these — never by iterating whatever
# keys happen to exist, which is precisely what made the EV-11 `available`
# key deletion invisible.
KEY_VOCAB_AXES: Mapping[str, str] = MappingProxyType({
    "label_vocab": "dataset.PRE_Y6_LABEL_NA_FIELDS (frozen, 6 labels)",
    "theta_keys": "study.theta_key over study.FROZEN_THETAS",
})

# --- the new DISCLOSURE_UNVERIFIED marker sections -------------------------
_S_FAV_TS = "theoretical_oracle.favourable_extreme_ts"
_S_OR_NON_ANCHOR = "sizing_outputs.opening_range_non_anchor_extreme"
_S_EV11_BOOLS = "structural.label_anchor_availability.dependency_booleans"
_S_EV11_VALUES = "structural.label_anchor_availability.per_day_values"
_S_F10_PER_DATE = "structural.f10_raw_membership.per_date"
_S_AF1_AXIS = "evidence.entity_axis.af1_days"


def _leaf(family, leaf, disposition, axis, vocab="", authority="",
          section=""):
    return LeafSpec(family, leaf, disposition, axis, vocab, authority, section)


LEAF_REGISTRY: Mapping[str, LeafSpec] = MappingProxyType({
    s.leaf_id: s for s in (
        # --- EV-1 -----------------------------------------------------------
        _leaf("EV-1", "trade_date", INDEPENDENT_BOUND, "af1_days",
              authority="EV-9 L3 + the parsed sealed dates"),
        _leaf("EV-1", "year", INDEPENDENT_BOUND, "af1_days",
              authority="structural.groups.by_year / frequency"),
        _leaf("EV-1", "era", INDEPENDENT_BOUND, "af1_days",
              authority="ctx.MICRO_ERA_BOUNDARY / structural.eras"),
        _leaf("EV-1", "record_year", DERIVED_REDUNDANT, "af1_days",
              authority="== EV-1.year (the drift check EV-1's docstring "
                        "promises and never performed)"),
        _leaf("EV-1", "record_era", DERIVED_REDUNDANT, "af1_days",
              authority="== EV-1.era"),
        _leaf("EV-1", "d_open", INDEPENDENT_BOUND, "af1_days",
              authority="sealed direction / stability_views.by_direction"),
        _leaf("EV-1", "y_cont", INDEPENDENT_BOUND, "af1_days",
              authority="theta partition -> sealed rows; untradeable.y_cont"),
        _leaf("EV-1", "y_cont_available", DERIVED_REDUNDANT, "af1_days",
              authority="== (y_cont is not None); population total vs EV-8 "
                        "labels.y_cont.not_na"),
        _leaf("EV-1", "direction_status", INDEPENDENT_BOUND, "af1_days",
              authority="dataset.py:307-308 (directional <=> d_open != 0) "
                        "and structural.na_table.direction class counts"),
        _leaf("EV-1", "oracle_candidate", INDEPENDENT_BOUND, "af1_days",
              authority="oracle_daily.day_universe / frequency"),
        _leaf("EV-1", "record_oracle_candidate", DERIVED_REDUNDANT,
              "af1_days", authority="== EV-1.oracle_candidate (dataset:247)"),
        _leaf("EV-1", "tradeable_direction", DERIVED_REDUNDANT, "af1_days",
              authority="== (d_open != 0) (dataset.py:246)"),
        _leaf("EV-1", "trade_constructible", INDEPENDENT_BOUND, "af1_days",
              authority="the sealed row population / frequency"),
        _leaf("EV-1", "untradeable_reason", INDEPENDENT_BOUND, "af1_days",
              authority="disclosures.untradeable + study.UNTRADEABLE_REASONS"),
        _leaf("EV-1", "is_event_day", INDEPENDENT_BOUND, "af1_days",
              authority="EV-10.final_category per date; None-count vs EV-8 "
                        "features.is_event_day.na"),
        # --- EV-2 -----------------------------------------------------------
        _leaf("EV-2", "trade_date", INDEPENDENT_BOUND, "tp_union",
              authority="EV-1 x study.FROZEN_THETAS"),
        _leaf("EV-2", "direction", DERIVED_REDUNDANT, "tp_union",
              authority="== EV-1.d_open"),
        _leaf("EV-2", "scenario_name", INDEPENDENT_BOUND, "tp_union",
              authority="== study.BASE_SCENARIO_NAME"),
        _leaf("EV-2", "entry_ref_price", INDEPENDENT_BOUND, "tp_union",
              authority="the sealed entry_fill through costs.entry_fill"),
        _leaf("EV-2", "entry_fill", DERIVED_REDUNDANT, "tp_union",
              authority="costs.scenario_entry_fill(entry_ref_price, d, Base)"),
        _leaf("EV-2", "favourable_extreme_price", DERIVED_REDUNDANT,
              "tp_union",
              authority="costs.timed_exit_fill inverted from exit_fill"),
        _leaf("EV-2", "favourable_extreme_ts", DISCLOSURE_UNVERIFIED,
              "tp_union",
              authority="NONE — the bars are process-local; only a structural "
                        "ISO/window rail is asserted",
              section=_S_FAV_TS),
        _leaf("EV-2", "exit_fill", DERIVED_REDUNDANT, "tp_union",
              authority="entry_fill + (pnl + fee)/(d * MNQ_POINT_VALUE_USD)"),
        _leaf("EV-2", "pnl_per_contract", INDEPENDENT_BOUND, "tp_union",
              authority="the theoretical_oracle subtree"),
        _leaf("EV-2", "platform_fee_rt_usd", DERIVED_REDUNDANT, "tp_union",
              authority="== EV-4['Base'].platform_fee_rt_usd"),
        # --- EV-3 -----------------------------------------------------------
        _leaf("EV-3", "trade_date", INDEPENDENT_BOUND, "constructible_days",
              authority="EV-1.trade_constructible"),
        _leaf("EV-3", "or_high@short", DERIVED_REDUNDANT,
              "constructible_days_short",
              authority="== anchor_stop when d_open == -1 (study.py:225-228)"),
        _leaf("EV-3", "or_high@long", DISCLOSURE_UNVERIFIED,
              "constructible_days_long",
              authority="NONE — the non-anchor extreme reaches no sealed "
                        "artifact; only or_high >= or_low is asserted",
              section=_S_OR_NON_ANCHOR),
        _leaf("EV-3", "or_low@long", DERIVED_REDUNDANT,
              "constructible_days_long",
              authority="== anchor_stop when d_open == +1 (study.py:225-228)"),
        _leaf("EV-3", "or_low@short", DISCLOSURE_UNVERIFIED,
              "constructible_days_short",
              authority="NONE — the non-anchor extreme", section=_S_OR_NON_ANCHOR),
        _leaf("EV-3", "n_obs_bars", DISCLOSURE_UNVERIFIED,
              "constructible_days",
              authority="NONE — no sealed consumer; only the frozen "
                        "observation-window range rail is asserted",
              section=_S_OR_NON_ANCHOR),
        _leaf("EV-3", "anchor_stop", INDEPENDENT_BOUND, "constructible_days",
              authority="sealed stop_level_points / E1 planned_stop"),
        _leaf("EV-3", "d_open", DERIVED_REDUNDANT, "constructible_days",
              authority="== EV-1.d_open"),
        # --- EV-4 -----------------------------------------------------------
        _leaf("EV-4", "name", INDEPENDENT_BOUND, "axis_scenarios",
              authority="the frozen four-scenario axis"),
        _leaf("EV-4", "spread_points", INDEPENDENT_BOUND, "axis_scenarios",
              authority="sealed fills + sizing_outputs.cost_usd_per_1_MNQ"),
        _leaf("EV-4", "slippage_ticks_per_side", INDEPENDENT_BOUND,
              "axis_scenarios", authority="sealed fills + the A5 cost leaf"),
        _leaf("EV-4", "adverse_slippage_ticks", INDEPENDENT_BOUND,
              "axis_scenarios", authority="the A5 stop-exit cost leaf"),
        _leaf("EV-4", "friction_multiplier", INDEPENDENT_BOUND,
              "axis_scenarios", authority="sealed fills + the A5 cost leaf"),
        _leaf("EV-4", "platform_fee_rt_usd", INDEPENDENT_BOUND,
              "axis_scenarios", authority="the L132 P&L recompute"),
        _leaf("EV-4", "spread_scalars", INDEPENDENT_BOUND, "axis_scenarios",
              authority="costs.build_scenarios(*spread_scalars) must rebuild "
                        "all four snapshots"),
        _leaf("EV-4", "reduction_rule_id", DR_PARTIAL, "axis_scenarios",
              authority="DR-1 unruled; only the vocabulary and the iff "
                        "against provenance['EV-4_dr1_status'] are asserted",
              section="sizing_outputs.cost_layer"),
        _leaf("EV-4", "adverse_semantics", DR_PARTIAL, "axis_scenarios",
              authority="DR-1 unruled (IR-7); same consistency rail",
              section="sizing_outputs.cost_layer"),
        # --- EV-5 -----------------------------------------------------------
        _leaf("EV-5", "trade_date", INDEPENDENT_BOUND, "af1_days",
              authority="the AF1 day population"),
        _leaf("EV-5", "year", DERIVED_REDUNDANT, "af1_days",
              authority="== EV-1.year (a corrupt year used to be SWALLOWED "
                        "by a bare except, silently disabling CR-4)"),
        _leaf("EV-5", "micro_execution_era", DERIVED_REDUNDANT, "af1_days",
              authority="== EV-1.era"),
        _leaf("EV-5", "stability_epoch", INDEPENDENT_BOUND, "af1_days",
              authority="CR-4: dataset.STABILITY_EPOCHS vs "
                        "stability._epoch_of"),
        _leaf("EV-5", "d_open", DERIVED_REDUNDANT, "af1_days",
              authority="== EV-1.d_open"),
        _leaf("EV-5", "volatility_regime_label", DR_PARTIAL, "af1_days",
              authority="DR-2: no atom exists anywhere in the chain",
              section="stability_views.vol_terciles"),
        _leaf("EV-5", "vol_status", INDEPENDENT_BOUND, "af1_days",
              authority="== provenance['EV-5_dr2_status'], vocabulary-bound"),
        _leaf("EV-5", "event_flag_final", DERIVED_REDUNDANT, "af1_days",
              authority="== EV-1.is_event_day or 'NA_multi_event'"),
        _leaf("EV-5", "event_na", DERIVED_REDUNDANT, "af1_days",
              authority="== (EV-1.is_event_day is None)"),
        _leaf("EV-5", "event_stratum", DR_PARTIAL, "af1_days",
              authority="DR-6: the stratum vocabulary is unruled",
              section="day_strata"),
        _leaf("EV-5", "tp_fp_class", INDEPENDENT_BOUND, "af1_days",
              vocab="theta_keys",
              authority="the EV-1 theta partition, keyed by the frozen axis"),
        # --- EV-6 -----------------------------------------------------------
        _leaf("EV-6", "theta_key", INDEPENDENT_BOUND, "theta_eng_scn",
              authority="the frozen cell axis"),
        _leaf("EV-6", "engine", INDEPENDENT_BOUND, "theta_eng_scn",
              authority="the frozen cell axis"),
        _leaf("EV-6", "scenario", INDEPENDENT_BOUND, "theta_eng_scn",
              authority="the frozen cell axis"),
        _leaf("EV-6", "tp_pools.UNION", INDEPENDENT_BOUND, "theta_eng_scn",
              authority="the union of the pools must BE the EV-1 TP "
                        "partition, exactly and without duplicates"),
        _leaf("EV-6", "fp_pools.UNION", INDEPENDENT_BOUND, "theta_eng_scn",
              authority="the union must BE the EV-1 FP partition"),
        _leaf("EV-6", "tp_pools.STRATUM", DR_PARTIAL, "theta_eng_scn",
              authority="DR-2 + DR-3 + DR-6: the stratum ASSIGNMENT has no "
                        "defined vocabulary",
              section="feasibility_grid.per_seed"),
        _leaf("EV-6", "fp_pools.STRATUM", DR_PARTIAL, "theta_eng_scn",
              authority="DR-2 + DR-3 + DR-6",
              section="feasibility_grid.per_seed"),
        _leaf("EV-6", "tp_avail", DERIVED_REDUNDANT, "theta_eng_scn",
              authority="== {k: len(v)} of tp_pools"),
        _leaf("EV-6", "fp_avail", DERIVED_REDUNDANT, "theta_eng_scn",
              authority="== {k: len(v)} of fp_pools"),
        _leaf("EV-6", "n_tp_available", DERIVED_REDUNDANT, "theta_eng_scn",
              authority="== sum(tp_avail.values()) == |EV-1 TP|"),
        _leaf("EV-6", "n_fp_available", DERIVED_REDUNDANT, "theta_eng_scn",
              authority="== sum(fp_avail.values()) == |EV-1 FP|"),
        _leaf("EV-6", "grid_stream_tag", INDEPENDENT_BOUND, "theta_eng_scn",
              authority="== gridmix.GRID_STREAM_TAG (live constant, CR-9)"),
        _leaf("EV-6", "stratum_axes", INDEPENDENT_BOUND, "theta_eng_scn",
              authority="== the frozen GRID_STRATUM_AXES constant"),
        # --- EV-7 -----------------------------------------------------------
        _leaf("EV-7", "cell_key", INDEPENDENT_BOUND, "boot_cells",
              authority="the A7 cell product"),
        _leaf("EV-7", "theta_key", DERIVED_REDUNDANT, "boot_cells",
              authority="== cell_key component 0"),
        _leaf("EV-7", "engine", DERIVED_REDUNDANT, "boot_cells",
              authority="== cell_key component 1"),
        _leaf("EV-7", "scenario", DERIVED_REDUNDANT, "boot_cells",
              authority="== cell_key component 2"),
        _leaf("EV-7", "block_len", INDEPENDENT_BOUND, "boot_cells",
              authority="FROZEN_BLOCKS + cell_key component 3"),
        _leaf("EV-7", "n", DERIVED_REDUNDANT, "boot_cells",
              authority="len of the series rebuilt from EV-1 x the bytes"),
        _leaf("EV-7", "series_sha256", INDEPENDENT_BOUND, "boot_cells",
              authority="_series_digest over the bytes-derived D_TP"),
        _leaf("EV-7", "series_mean_sum_over_n", INDEPENDENT_BOUND,
              "boot_cells", authority="CR-2 three-way mean identity"),
        _leaf("EV-7", "series_mean_numpy", INDEPENDENT_BOUND, "boot_cells",
              authority="CR-2 three-way mean identity"),
        _leaf("EV-7", "series_sum", DERIVED_REDUNDANT, "boot_cells",
              authority="== series_mean_sum_over_n * n"),
        _leaf("EV-7", "first_date", DERIVED_REDUNDANT, "boot_cells",
              authority="first of the rebuilt ordered series"),
        _leaf("EV-7", "last_date", DERIVED_REDUNDANT, "boot_cells",
              authority="last of the rebuilt ordered series"),
        _leaf("EV-7", "seeds", INDEPENDENT_BOUND, "boot_cells",
              authority="EXACT tuple == contracts.RESEARCH_BOOTSTRAP_SEEDS"),
        _leaf("EV-7", "stats_stream_tag", INDEPENDENT_BOUND, "boot_cells",
              authority="== stats.STATS_STREAM_TAG"),
        _leaf("EV-7", "block_stream_key", INDEPENDENT_BOUND, "boot_cells",
              authority="== stats.block_stream_key(block_len)"),
        _leaf("EV-7", "n_boot", INDEPENDENT_BOUND, "boot_cells",
              authority="== stats.N_BOOT and the per-seed payload"),
        _leaf("EV-7", "ci_level", INDEPENDENT_BOUND, "boot_cells",
              authority="== stats.CI_LEVEL"),
        _leaf("EV-7", "percentile_method_id", INDEPENDENT_BOUND, "boot_cells",
              authority="== stats.PERCENTILE_METHOD == EV-12's stats reading"),
        # --- EV-8 -----------------------------------------------------------
        _leaf("EV-8", "table", INDEPENDENT_BOUND, "na_fields",
              authority="the frozen NA field lists"),
        _leaf("EV-8", "column", INDEPENDENT_BOUND, "na_fields",
              authority="the frozen NA field lists"),
        _leaf("EV-8", "n_null", INDEPENDENT_BOUND, "na_fields",
              authority="structural.na_table.per_field + the population "
                        "conservation identity"),
        _leaf("EV-8", "n_not_null", INDEPENDENT_BOUND, "na_fields",
              authority="structural.na_table.per_field + conservation"),
        _leaf("EV-8", "observation_method_id", INDEPENDENT_BOUND, "na_fields",
              authority="== NA_OBSERVATION_METHOD_ID[table] (disclosure "
                        "vocabulary, so exact equality is the right check)"),
        # --- EV-9 -----------------------------------------------------------
        _leaf("EV-9", "level_dates", INDEPENDENT_BOUND, "funnel_levels",
              authority="the ten published funnel_counts keys, plus sorted / "
                        "unique / nested-level rails"),
        _leaf("EV-9", "exclusion_reason", INDEPENDENT_BOUND, "excluded_days",
              authority="the level DIFFERENCES decide both the key set and "
                        "the reason; vocabulary = frozen L44 "
                        "(context.py:566-575)"),
        _leaf("EV-9", "provenance", INDEPENDENT_BOUND, "singleton",
              authority="PROVENANCE_REGISTRY['EV-9'] binding"),
        # --- EV-10 ----------------------------------------------------------
        _leaf("EV-10", "trade_date", INDEPENDENT_BOUND, "f10_population",
              authority="== the EV-9 L3 set exactly (the exclusive check used "
                        "to count elements without keying by date)"),
        _leaf("EV-10", "raw_categories", DISCLOSURE_UNVERIFIED,
              "f10_population",
              authority="totals bind to f10_raw_membership_counts when the "
                        "calendar is supplied; the PER-DATE attribution has "
                        "no second observation",
              section=_S_F10_PER_DATE),
        _leaf("EV-10", "final_category", INDEPENDENT_BOUND, "f10_population",
              authority="per date == EV-1.is_event_day (or NA_multi_event), "
                        "and the counts vs structural.f10_counts"),
        _leaf("EV-10", "raw_provenance", INDEPENDENT_BOUND, "f10_population",
              authority="PROVENANCE_REGISTRY['EV-10'] binding"),
        # --- EV-11 ----------------------------------------------------------
        _leaf("EV-11", "trade_date", INDEPENDENT_BOUND, "af1_days",
              authority="the AF1 day population"),
        _leaf("EV-11", "o1000", DISCLOSURE_UNVERIFIED, "af1_days",
              authority="NONE — no per-day and no aggregate authority; only "
                        "the implication rail from EV-2 coverage",
              section=_S_EV11_BOOLS),
        _leaf("EV-11", "c1544", DISCLOSURE_UNVERIFIED, "af1_days",
              authority="NONE", section=_S_EV11_BOOLS),
        _leaf("EV-11", "pm_ok", DISCLOSURE_UNVERIFIED, "af1_days",
              authority="NONE — only the trade_constructible implication rail",
              section=_S_EV11_BOOLS),
        _leaf("EV-11", "adr_ok", DISCLOSURE_UNVERIFIED, "af1_days",
              authority="the POPULATION TOTAL is hard-bound to EV-8 "
                        "features.adr14.not_na; the per-day value is not",
              section=_S_EV11_BOOLS),
        _leaf("EV-11", "dir_ok", INDEPENDENT_BOUND, "af1_days",
              authority="<=> EV-1.d_open != 0 (dataset.py:307-308 and 687) — "
                        "a mechanical identity, NOT the fenced label reducer"),
        _leaf("EV-11", "available.KEYSET", INDEPENDENT_BOUND, "af1_days",
              vocab="label_vocab",
              authority="EXACT key set == dataset.PRE_Y6_LABEL_NA_FIELDS for "
                        "EVERY entity — closes the measured key-deletion hole"),
        _leaf("EV-11", "available.VALUE", DISCLOSURE_UNVERIFIED, "af1_days",
              vocab="label_vocab",
              authority="NONE at per-day granularity. The per-label TOTALS "
                        "stay bound to structural.label_anchor_availability; "
                        "the five-boolean -> label-set reducer exists only in "
                        "the UNFROZEN dataset.py:688-695 and IR-23 enumerates "
                        "y1 exactly, y2/y3 interpretively and y_cont/y4/y5 "
                        "not at all — so it is NOT derived here",
              section=_S_EV11_VALUES),
        # --- EV-12 ----------------------------------------------------------
        _leaf("EV-12", "study_percentile_method", INDEPENDENT_BOUND,
              "singleton", authority="study.PERCENTILE_METHOD"),
        _leaf("EV-12", "stability_percentile_method", INDEPENDENT_BOUND,
              "singleton", authority="stability.PERCENTILE_METHOD"),
        _leaf("EV-12", "stats_percentile_method", INDEPENDENT_BOUND,
              "singleton", authority="stats.PERCENTILE_METHOD"),
        _leaf("EV-12", "all_three_agree", INDEPENDENT_BOUND, "singleton",
              authority="re-derived from the three strings"),
        _leaf("EV-12", "worst_day_estimator_ruling", DERIVED_REDUNDANT,
              "singleton",
              authority="None <=> estimator_status_expected is the "
                        "unresolved DR-M6-H token"),
        _leaf("EV-12", "estimator_status_expected", INDEPENDENT_BOUND,
              "singleton", authority="e2_worst_days.<t>.<scn>.estimator_status"),
        # --- EV-13 ----------------------------------------------------------
        _leaf("EV-13", "observed", INDEPENDENT_BOUND, "frozen_hash_paths",
              authority="the EXACT declared governance.frozen_hashes key set"),
        _leaf("EV-13", "provenance", INDEPENDENT_BOUND, "singleton",
              authority="PROVENANCE_REGISTRY['EV-13'] binding"),
        # --- top level ------------------------------------------------------
        _leaf("TOP", "schema_version", INDEPENDENT_BOUND, "singleton",
              authority="the frozen SCHEMA_VERSION constant"),
        _leaf("TOP", "thetas", INDEPENDENT_BOUND, "axis_thetas",
              authority="study.FROZEN_THETAS"),
        _leaf("TOP", "engines", INDEPENDENT_BOUND, "axis_engines",
              authority="study.ENGINES"),
        _leaf("TOP", "scenarios", INDEPENDENT_BOUND, "axis_scenarios",
              authority="the frozen four-scenario axis"),
        _leaf("TOP", "eras", INDEPENDENT_BOUND, "axis_eras",
              authority="study.ERA_AXIS"),
        _leaf("TOP", "blocks", INDEPENDENT_BOUND, "axis_blocks",
              authority="FROZEN_BLOCKS"),
        _leaf("TOP", "record_pnl", INDEPENDENT_BOUND, "sealed_cell_dates",
              authority="the parsed sealed final_pnl_per_contract, both "
                        "directions of the date key set"),
        _leaf("TOP", "record_fields", INDEPENDENT_BOUND,
              "record_field_tokens",
              authority="exact date set x FORMAL_RECORD_FIELDS, strict types"),
        _leaf("TOP", "provenance", INDEPENDENT_BOUND, "provenance_keys",
              authority="the frozen PROVENANCE_REGISTRY, both directions"),
    )
})


@dataclass(frozen=True)
class LeafOutcome:
    """The token-completeness result of ONE registered leaf.

    `complete` is MULTISET EQUALITY and nothing else: the right NUMBER of
    the WRONG tokens is incomplete, which is exactly what a
    `compared_count >= applicable` gate could never see.
    """
    leaf_id: str
    expected: int
    actual: int
    missing: tuple = ()
    extra: tuple = ()
    duplicate: tuple = ()
    skipped_reason: str = ""

    @property
    def complete(self) -> bool:
        return not (self.missing or self.extra or self.duplicate)


def _leaf_outcome_from(leaf_id, expected, counter) -> LeafOutcome:
    """Build a LeafOutcome from an expected entity set and an emitted
    multiset. Never raises."""
    try:
        exp = set(expected)
        got = dict(counter)
    except Exception:                                    # noqa: BLE001
        return LeafOutcome(leaf_id, 0, 0, missing=("<unreadable>",))
    missing = tuple(_report._safe_sorted(exp - set(got)))
    extra = tuple(_report._safe_sorted(set(got) - exp))
    dup = tuple(_report._safe_sorted(k for k, v in got.items() if v > 1))
    return LeafOutcome(leaf_id, len(exp), sum(got.values()),
                       missing=missing, extra=extra, duplicate=dup)


# --- provenance: absent / wrong type / out of vocabulary / disagreeing are
#     FOUR distinct deterministic dispositions. Absent is NEVER "agrees". --
_PROV_VOCABULARY: frozenset = frozenset({
    PROV_REDERIVED_FROM_BARS, PROV_ATOM_DAY_RECORD,
    PROV_ATOM_TRADE_PATH_RECORD, PROV_ATOM_UNIVERSE, PROV_CONFIG_DERIVED,
    PROV_FROZEN_CONSTANT, PROV_CALLER_SUPPLIED, PROV_NOT_SUPPLIED,
    "raw_null_scan_of_S0Dataset_tables",
})
_DR_STATUS_VOCABULARY: frozenset = frozenset(
    {STATUS_RESOLVED, STATUS_UNRESOLVED, STATUS_TEST_ONLY})
_XCHECK_AGREES = "agrees"
_XCHECK_DISAGREE_PREFIX = "DISAGREEMENT"

_PROV_LABEL = "label"          # "+"-joined PROV_* tokens
_PROV_XCHECK = "cross_check"   # exactly "agrees" or DISAGREEMENT:<...>
_PROV_DR_STATUS = "dr_status"  # resolved | unresolved | test_only
_PROV_BOUND = "bound"          # must equal another captured field


@dataclass(frozen=True)
class ProvKeySpec:
    kind: str
    disposition: str
    bound_to: str = ""


PROVENANCE_REGISTRY: Mapping[str, ProvKeySpec] = MappingProxyType({
    "EV-1": ProvKeySpec(_PROV_LABEL, PURE_METADATA),
    "EV-2": ProvKeySpec(_PROV_LABEL, PURE_METADATA),
    "EV-3": ProvKeySpec(_PROV_LABEL, PURE_METADATA),
    "EV-4": ProvKeySpec(_PROV_LABEL, PURE_METADATA),
    "EV-5": ProvKeySpec(_PROV_LABEL, PURE_METADATA),
    "EV-6": ProvKeySpec(_PROV_LABEL, PURE_METADATA),
    "EV-7": ProvKeySpec(_PROV_LABEL, PURE_METADATA),
    "EV-8": ProvKeySpec(_PROV_LABEL, PURE_METADATA),
    "EV-11": ProvKeySpec(_PROV_LABEL, PURE_METADATA),
    "EV-12": ProvKeySpec(_PROV_LABEL, PURE_METADATA),
    "AF2": ProvKeySpec(_PROV_LABEL, PURE_METADATA),
    "EV-4_dr1_status": ProvKeySpec(_PROV_DR_STATUS, REQUIRED_COMPARED),
    "EV-5_dr2_status": ProvKeySpec(_PROV_DR_STATUS, REQUIRED_COMPARED),
    "EV-5_dr6_status": ProvKeySpec(_PROV_DR_STATUS, REQUIRED_COMPARED),
    "EV-7_dr4_status": ProvKeySpec(_PROV_DR_STATUS, REQUIRED_COMPARED),
    "EV-2_oracle_cross_check": ProvKeySpec(_PROV_XCHECK, REQUIRED_COMPARED),
    "EV-10_flag_cross_check": ProvKeySpec(_PROV_XCHECK, REQUIRED_COMPARED),
    "EV-9": ProvKeySpec(_PROV_BOUND, REQUIRED_COMPARED, "funnel.provenance"),
    "EV-10": ProvKeySpec(_PROV_BOUND, REQUIRED_COMPARED,
                         "f10_memberships.raw_provenance"),
    "EV-13": ProvKeySpec(_PROV_BOUND, REQUIRED_COMPARED,
                         "frozen_hash_observation.provenance"),
    "schema_version": ProvKeySpec(_PROV_BOUND, REQUIRED_COMPARED,
                                  "schema_version"),
})

# The unconditional disclosure markers: never field-conditional, so they are
# a frozen TABLE rather than literals inside a marker-assembling function.
# S0 closeout (Aaron 2026-08-10): the eight DR rulings LANDED — every marker
# below states the REMAINING verification gap truthfully, never a "pending
# ruling" that no longer pends. A sealed release must not publish a
# disclosure asserting rulings were unmade (conformance finding F6.1).
PERMANENT_MARKERS: tuple = (
    f"{PARTIAL_PREFIX}oracle_daily.worst_day_pnl_percentiles:"
    "DR-8 RULED (linear, 2026-08-10) — EV-12 binds the estimator constant "
    "and the ruling; the percentile VALUES still have no independent "
    "re-computation here (matrix L029/L033)",
    f"{PARTIAL_PREFIX}theoretical_oracle.worst_day_pnl_percentiles:"
    "DR-8 RULED — same residual value-replay gap (matrix L039)",
    f"{PARTIAL_PREFIX}stability_views:"
    "DR-7 RULED (both populations, 2026-08-10) — cells are reproducible "
    "and population-tagged; per-view value replay remains out of evidence "
    "scope (matrix S6.1)",
    f"{PARTIAL_PREFIX}stability_views.vol_terciles:"
    "DR-2 RULED (2026-08-10) — the vol20 axis has a ruled producer "
    "(dataset.build_vol20_regime_mapping); EV-5 carries its labels, but "
    "this module still holds NO close-series atom to re-derive them from "
    "(matrix L078 residual)",
    f"{PARTIAL_PREFIX}bootstrap_ci.ci_lo_ci_hi:"
    "no 10,000-resample replay is performed here (32 cells x 3 seeds); "
    "EV-7 binds the INPUT SERIES digest and the DR-4 ruled-sequence "
    "counts only (matrix L082)",
    f"{PARTIAL_PREFIX}feasibility_grid.per_seed:"
    "DR-2/3/6 RULED (2026-08-10) — the stratum key vocabulary is defined "
    "and draws are membership-checked (CR-8); full per-seed RNG replay "
    "of the DR-5 K-repeat streams stays out of evidence scope",
    f"{PARTIAL_PREFIX}sizing_outputs.cost_layer:"
    "DR-1 RULED (B-i + IR-7 Option i, 2026-08-10) — EV-4 snapshots the "
    "scenario objects; the B-i reduction from the locked spread table is "
    "verified at the injectable source (sha256 pin), not re-derived here "
    "(matrix S6.3 residual)",
    f"{PARTIAL_PREFIX}usd_layer:"
    "USD figures inherit the DR-1 RULED cost input; the ruling closed the "
    "definition gap — the residual is that this module re-verifies fills "
    "against EV-4 snapshots, not against the raw cost table "
    "(matrix L132/S6.3)",
    f"{PARTIAL_PREFIX}structural.na_table.reasons:"
    "CR-1 — EV-8 closes the na/not_na COUNT level with a structurally "
    "different null scan, but the per-date NA-REASON attribution still "
    "has ONE preimage (DayRecord.*_na_reasons); reason-level counts "
    "stay producer-only",
    f"{PARTIAL_PREFIX}day_strata:"
    "DR-2/DR-6 RULED (2026-08-10) — EV-5 is consumed (tp_fp_class vs "
    "EV-1, CR-4 epoch convention, era) and both axes now carry ruled "
    "vocabulary; the residual is that the per-day vol labels are "
    "producer-derived, with no close-series atom here to re-derive them "
    "(matrix L144 residual)",
    f"{PARTIAL_PREFIX}{_S_FAV_TS}:"
    "M6.1.4-R2 leaf lineage — EV-2's favourable-extreme TIMESTAMP has no "
    "captured preimage (the bars are process-local) and reaches no sealed "
    "leaf; only an ISO/window rail against the frozen SS3 trade span is "
    "asserted",
    f"{PARTIAL_PREFIX}{_S_OR_NON_ANCHOR}:"
    "M6.1.4-R2 leaf lineage — only the opening-range extreme that IS the "
    "anchor (study.py:225-228) reaches a sealed artifact; the opposite "
    "extreme and n_obs_bars carry range rails only",
    f"{PARTIAL_PREFIX}{_S_EV11_BOOLS}:"
    "M6.1.4-R2 leaf lineage — EV-11's o1000/c1544/pm_ok have NO second "
    "observation at any granularity and adr_ok is bound only as a "
    "POPULATION TOTAL against EV-8; dir_ok is separately bound to "
    "EV-1.d_open and is NOT covered by this marker",
    f"{PARTIAL_PREFIX}{_S_EV11_VALUES}:"
    "M6.1.4-R2 leaf lineage — the per-day available[<label>] VALUES are "
    "unverified: the five-boolean -> label-set reducer exists only in the "
    "UNFROZEN dataset.py:688-695, and approved IR-23 enumerates y1 exactly, "
    "y2/y3 interpretively and y_cont/y4/y5 not at all, so it is NOT derived "
    "here (DECISION_REQUIRED). The per-label TOTALS remain bound; an "
    "aggregate-preserving swap is invisible and this marker says so",
    f"{PARTIAL_PREFIX}{_S_F10_PER_DATE}:"
    "M6.1.4-R2 leaf lineage — EV-10's raw multi-hot categories bind at the "
    "COUNT level only; the per-date attribution has no second observation",
    f"{PARTIAL_PREFIX}records.executable_fills:"
    "matrix L130-L137 — the true atom under entry_fill/exit_fill/mtm_* "
    "is BAR DATA and the bars are process-local. Post-capture byte "
    "tampering is closed (record_fields binding) and TP-day ENTRY fills "
    "are anchored to EV-2.entry_ref_price + EV-4; EXIT fills and "
    "FP-only-day entry fills have NO captured preimage, so a producer "
    "poisoned BEFORE compute is out of reach",
)


def _markers_from_registry(outcomes: Mapping) -> set:
    """Derive the whole PARTIAL set from REGISTRY x OUTCOMES.

    The loop iterates `CHECK_REGISTRY`, never `outcomes` — so a check that
    writes an outcome nobody reads is impossible by construction, and a
    check that produced NO outcome at all (the `checks["day_strata"]` bug,
    inverted) still yields its marker. Never raises."""
    out: set = set(PERMANENT_MARKERS)
    for check_id, spec in CHECK_REGISTRY.items():
        try:
            outcome = outcomes.get(check_id) if isinstance(outcomes, Mapping) \
                else None
            if outcome is None:
                out.update(spec.never_ran_markers())
            else:
                out.update(spec.markers_for(outcome))
        except Exception:                                # noqa: BLE001
            out.add(f"{PARTIAL_PREFIX}registry.{check_id}:"
                    "marker derivation failed for this check")
    return out


_FIELD_TO_FAMILY: Mapping[str, str] = MappingProxyType({
    "day_facts": "EV-1", "theoretical_paths": "EV-2",
    "opening_ranges": "EV-3", "cost_scenarios": "EV-4",
    "day_strata": "EV-5", "grid_pools": "EV-6", "bootstrap_inputs": "EV-7",
    "na_observations": "EV-8", "funnel": "EV-9", "f10_memberships": "EV-10",
    "label_availability": "EV-11", "estimator_identity": "EV-12",
    "frozen_hash_observation": "EV-13",
})


def _attach_leaf_tokens(outcomes, leaf_outcomes) -> None:
    """Give every registered check the TOKEN view of its own field, so
    `CheckOutcome.complete` is dominated by leaf-level multiset equality
    wherever the field owns leaves. The projection is one token per
    registered leaf, present exactly when that leaf reached token
    completeness — so a family with any incomplete leaf can no longer report
    a complete check. `_FIELD_TO_FAMILY` records the field -> family mapping
    explicitly rather than inferring it from a name; the four byte-side
    rails (`field is None`) own no leaf and keep the count path."""
    by_family: dict = {}
    for leaf_id, outcome in leaf_outcomes.items():
        spec = LEAF_REGISTRY.get(leaf_id)
        if spec is None or outcome.skipped_reason:
            continue
        by_family.setdefault(spec.family, []).append(outcome)
    for check_id, outcome in list(outcomes.items()):
        rows = by_family.get(_FIELD_TO_FAMILY.get(outcome.field or ""))
        if not rows:
            continue
        outcomes[check_id] = _dc_replace(
            outcome,
            expected_tokens=frozenset(o.leaf_id for o in rows),
            actual_tokens=tuple(o.leaf_id for o in rows if o.complete))


def reconcile_outcomes(evidence, formal, sealed_files) -> Mapping:
    """The STRUCTURED sibling of `reconcile_with_evidence`: {check_id ->
    CheckOutcome}. Never raises. `reconcile_with_evidence` is a flat-string
    projection of this, so the renderer's contract is unchanged."""
    acc: dict = {}
    _report._guarded(
        "reconcile_outcomes",
        lambda problems: _reconcile_inner(evidence, formal, sealed_files,
                                          problems, acc),
        [])
    return MappingProxyType(dict(acc))


def reconcile_with_evidence(evidence, formal, sealed_files) -> list[str]:
    """Reconcile the formal payload AND the sealed bytes against the
    canonical evidence. Returns a flat list of strings mixing HARD problems
    (any one of them must refuse the seal) and `PARTIAL:<section>:<reason>`
    markers (disclosure, never coverage); use `split_problems` to separate
    them. Never raises, for arbitrary input.

    What it does, and against WHICH authority (matrix column
    `authoritative_atomic_source`, never "another self-reported subtree"):

      (a) the eight `MC_HANDOFF_<eng>_<scn>.jsonl` BYTES are PARSED back
          into `TradePathRecord`-shaped rows — the payload's manifest is not
          consulted for this, so a synchronized manifest+bytes rewrite is
          still measured against evidence;
      (b) D_TP / D_FP per theta are REBUILT from those rows'
          `final_pnl_per_contract` keyed by the AUTHORITATIVE day membership
          in EV-1 — never from `formal["oracle_daily"][t]["day_universe"]`,
          which is the claim under test;
      (c) exactly ONE record per engine x scenario x date, identity fields
          valid (engine/scenario == file identity, direction in {+1,-1},
          ISO trade_date), every numeric leaf FINITE;
      (d) `oracle_daily` series + aggregates vs (b); `stability_views` sums
          vs (b)+EV-1 meta; `sizing_outputs` rows vs AF2 + EV-3 + EV-4;
          `bootstrap_ci` input series vs the EV-7 DIGEST; `feasibility_grid`
          availability vs the EV-6 pools; `day_universe`/`frequency`/
          `theoretical_oracle`/`structural.eras`/`structural.groups` vs the
          `reducers` above;
      (e) the checkable consistency risks: CR-2 (oracle mean vs
          bootstrap-input mean over the SAME series, both readings), CR-3
          (the four-way theta-partition-size identity), CR-6 (the three E2
          P1/P5 payload paths must agree), CR-9 (`method_conventions`
          stream-tag prose vs the module constants), CR-12
          (`risk_usd_per_1_MNQ_planned == minimum_1_contract_risk`), CR-4
          (the dataset half-open epoch convention vs `stability`'s
          inclusive-integer one), CR-1 at the COUNT level (EV-8's second
          null scan vs `structural.na_table` AND vs the A11 restatement, so
          moving the two together no longer works);
      (g) the sealed rows are bound to `evidence.record_fields`
          FIELD-FOR-FIELD with strict types — the invariant that closes the
          post-capture byte-tamper family;
      (h) the A1 `structural` sections are compared against their evidence:
          EV-9 -> `funnel_counts` (all ten keys), EV-10 ->
          `f10_counts`/`f10_raw_membership_counts`, EV-11 ->
          `label_anchor_availability`, EV-8 -> `na_table`; plus
          `disclosures.untradeable` vs EV-1 and `coverage.by_budget_usd`
          recomputed from the sealed anchors;
      (f) PARTIAL markers. HONEST SCOPE (corrected after the PHASE-E blind
          audit, then again in M6.1.4-ARCH): a marker names a section this
          function does NOT independently rebuild, together with the DR /
          matrix row that makes it so. It is emitted whenever the
          corresponding check did NOT reach `complete` (compared_count >=
          the authoritative applicable population), and the permanent ones
          (DR-1/2/6/7/8, the bar-data fill preimage, the NA reason level)
          are emitted unconditionally. The marker set is DERIVED by
          `_markers_from_registry` from CHECK_REGISTRY x outcomes — never
          hand-assembled — so a check whose outcome is never read cannot
          exist. It is still NOT a claim that every unrebuildable leaf in
          the report has a marker: anything outside the registry and the
          checks above is simply not covered by this function.
    """
    return _report._guarded(
        "reconcile_with_evidence",
        lambda acc: _reconcile_inner(evidence, formal, sealed_files, acc),
        [])


def _parse_sealed_rows(sealed_files, engines, scenarios, problems):
    """(a)+(c): parse the ACTUAL bytes. Returns {(eng, scn): {date: row}}."""
    parsed: dict = {}
    if not isinstance(sealed_files, Mapping):
        problems.append("evidence_sealed_files_not_a_mapping")
        return parsed
    for eng in engines:
        for scn in scenarios:
            name = f"{_MC_FILE_RE_PREFIX}{eng}_{scn}.jsonl"
            body = _get(sealed_files, name)
            if not isinstance(body, str):
                problems.append(f"evidence_sealed_file_missing:{name}")
                continue
            rows: dict = {}
            for i, line in enumerate(body.splitlines()):
                try:
                    row = json.loads(line)
                except Exception:                        # noqa: BLE001
                    problems.append(f"evidence_line_not_json:{name}:{i}")
                    continue
                if not isinstance(row, dict):
                    problems.append(f"evidence_line_not_object:{name}:{i}")
                    continue
                if set(row) != set(_report.FORMAL_RECORD_FIELDS):
                    problems.append(
                        f"evidence_line_field_set:{name}:{i}")
                    continue
                date = row.get("trade_date")
                if not isinstance(date, str) or not _report._is_date_str(date):
                    problems.append(f"evidence_line_trade_date:{name}:{i}")
                    continue
                if row.get("engine") != eng or row.get("cost_scenario") != scn:
                    problems.append(
                        f"evidence_line_identity:{name}:{i}:{date}")
                    continue
                if row.get("direction") not in (1, -1) or isinstance(
                        row.get("direction"), bool):
                    problems.append(
                        f"evidence_line_direction:{name}:{i}:{date}")
                    continue
                bad = [k for k in ("entry_fill", "exit_fill",
                                   "final_pnl_per_contract", "max_adverse_pnl",
                                   "max_favourable_pnl", "sizing_anchor_usd")
                       if not _num(row.get(k))]
                for k in ("planned_stop", "actual_stop_fill"):
                    if row.get(k) is not None and not _num(row.get(k)):
                        bad.append(k)
                for k in ("mtm_close_pnl_1m", "mtm_adverse_pnl_1m"):
                    seq = row.get(k)
                    if (not isinstance(seq, list) or not seq
                            or not all(_num(x) for x in seq)):
                        bad.append(k)
                if bad:
                    problems.append(
                        f"evidence_line_nonfinite_or_illtyped:{name}:{i}:"
                        f"{date}:{sorted(bad)}")
                    continue
                if date in rows:
                    problems.append(
                        f"evidence_duplicate_record:{eng}|{scn}:{date}")
                    continue
                rows[date] = row
            parsed[(eng, scn)] = rows
    return parsed


# ---------------------------------------------------------------------------
# The orchestrator (M6.1.4-ARCH). `_reconcile_inner` no longer decides which
# markers to emit: it runs every REGISTERED check through `_run_check`, which
# is the ONLY writer into `outcomes`, and the marker set is then derived from
# CHECK_REGISTRY x outcomes. A written-but-never-read check is impossible.
# ---------------------------------------------------------------------------
_FIELD_SHAPES: Mapping[str, tuple] = MappingProxyType({
    "schema_version": ("str",),
    "thetas": ("tuple",), "engines": ("tuple",), "scenarios": ("tuple",),
    "eras": ("tuple",), "blocks": ("tuple",), "day_facts": ("tuple",),
    "theoretical_paths": ("tuple",), "opening_ranges": ("tuple",),
    "cost_scenarios": ("tuple",), "day_strata": ("tuple",),
    "grid_pools": ("tuple",), "bootstrap_inputs": ("tuple",),
    "na_observations": ("tuple",), "f10_memberships": ("tuple",),
    "label_availability": ("tuple",),
    "record_pnl": ("mapping",), "record_fields": ("mapping",),
    "provenance": ("mapping",),
    "funnel": ("dataclass", FunnelFact),
    "estimator_identity": ("dataclass", EstimatorIdentityFact),
    "frozen_hash_observation": ("dataclass", FrozenHashObservationFact),
})


def _preflight_field_shapes(evidence, problems) -> None:
    """Type-gate EVERY field before any consumer touches it, so a malformed
    field yields a REGISTERED hard problem (and leaves the whole marker set
    intact) instead of an exception that wipes the disclosure list."""
    for name, shape in _FIELD_SHAPES.items():
        value = getattr(evidence, name, None)
        kind = shape[0]
        ok = False
        if kind == "str":
            ok = isinstance(value, str)
        elif kind == "tuple":
            ok = isinstance(value, tuple)
        elif kind == "mapping":
            ok = isinstance(value, Mapping)
        elif kind == "dataclass":
            ok = isinstance(value, shape[1])
        if not ok:
            problems.append(
                f"evidence_field_type:{name}:{type(value).__name__}")


def _authoritative_populations(evidence, formal, parsed) -> dict:
    """Size every applicable population from an authority that NEVER READS
    THE FIELD IT GUARDS. That property is what makes an emptied field unable
    to shrink its own expectation, and it is enforced by a test."""
    frozen_thetas = tuple(_study.FROZEN_THETAS)
    n_eng_scn = len(_study.ENGINES) * len(_SCENARIO_AXIS)
    n_cells = len(frozen_thetas) * n_eng_scn

    sealed_dates: set = set()
    sealed_rows = 0
    for rows in parsed.values():
        if isinstance(rows, Mapping):
            sealed_dates.update(rows)
            sealed_rows += len(rows)

    # EV-2's and EV-3's populations come from EV-1 (day_facts) — a different
    # field, itself guarded — never from EV-2/EV-3 themselves.
    day_facts = evidence.day_facts if isinstance(evidence.day_facts,
                                                 tuple) else ()
    constructible = {f.trade_date for f in day_facts
                     if getattr(f, "trade_constructible", False)}
    tp_union: set = set()
    sizing_rows = 0
    for theta in frozen_thetas:
        tp, _fp = _partition_from_facts(day_facts, theta, constructible)
        tp_union.update(tp)
        sizing_rows += len(tp) * n_eng_scn

    levels = getattr(evidence.funnel, "level_dates", None)
    l3 = _get(levels, "L3_structurally_eligible_days") \
        if isinstance(levels, Mapping) else None
    f10_population = len(l3) if isinstance(l3, tuple) else len(day_facts)

    declared = _get(formal, "governance", "frozen_hashes")
    return {
        "one": 1,
        "axis_thetas": len(frozen_thetas),
        "axis_engines": len(_study.ENGINES),
        "axis_scenarios": len(_SCENARIO_AXIS),
        "axis_eras": len(_study.ERA_AXIS),
        "axis_blocks": len(FROZEN_BLOCKS),
        "sealed_files": n_eng_scn,
        "sealed_dates": len(sealed_dates),
        "sealed_rows": sealed_rows,
        "reducer_keys": len(reducers),
        "theta_eng_scn": n_cells,
        "coverage_cells": n_cells * len(_study.RISK_BUDGETS_USD),
        "bootstrap_cells": n_cells * len(FROZEN_BLOCKS),
        "tp_union": len(tp_union),
        "tp_union_rows": len(tp_union) * n_eng_scn,
        "sizing_rows": sizing_rows,
        "af1_days": len(day_facts),
        "na_fields": len(FEATURE_NA_FIELDS) + len(LABEL_NA_FIELDS),
        "funnel_levels": len(_FUNNEL_LEVELS),
        "f10_population": f10_population,
        "estimator_leaves": 3 + len(frozen_thetas) * len(_SCENARIO_AXIS),
        "declared_hashes": (len(declared) if isinstance(declared, Mapping)
                            and declared else 1),
        "provenance_keys": len(PROVENANCE_REGISTRY),
    }


# ---------------------------------------------------------------------------
# The entity axes, and the leaf checks that emit tokens against them.
# ---------------------------------------------------------------------------
def _af1_axis_is_authoritative(evidence) -> bool:
    """The AF1 day population is authoritative ONLY when EV-9 carries the
    S0Universe L3 level. Without a universe there is NO non-circular source
    (`len(day_facts)` reads the family the axis guards), so the axis fails
    closed into a dedicated PARTIAL rather than sizing itself."""
    levels = getattr(evidence.funnel, "level_dates", None)
    if not isinstance(levels, Mapping):
        return False
    l3 = _get(levels, "L3_structurally_eligible_days")
    return isinstance(l3, tuple) and bool(l3)


def entity_axes_for(evidence, formal, parsed) -> dict:
    """Every entity axis, each built from an authority that NEVER reads the
    family it guards (`ENTITY_AXIS_AUTHORITIES` records which families each
    one does read, and a test enforces the disjointness)."""
    frozen_thetas = tuple(_study.FROZEN_THETAS)
    theta_keys = tuple(_study.theta_key(t) for t in frozen_thetas)
    engines = tuple(_study.ENGINES)

    day_facts = evidence.day_facts if isinstance(evidence.day_facts,
                                                 tuple) else ()
    levels = getattr(evidence.funnel, "level_dates", None)
    if _af1_axis_is_authoritative(evidence):
        af1 = frozenset(_get(levels, "L3_structurally_eligible_days"))
    else:
        af1 = frozenset()

    constructible = {f.trade_date for f in day_facts
                     if getattr(f, "trade_constructible", False)}
    d_open_of = {f.trade_date: getattr(f, "d_open", 0) for f in day_facts}
    tp_union: set = set()
    for theta in frozen_thetas:
        tp, _fp = _partition_from_facts(day_facts, theta, constructible)
        tp_union.update(tp)

    excluded: set = set()
    if isinstance(levels, Mapping):
        chain = ("L0_scheduled_trading_days", "L1_observed_rth_days",
                 "L2_regular_full_session_candidates",
                 "L3_structurally_eligible_days")
        for a, b in zip(chain, chain[1:]):
            hi, lo = _get(levels, a), _get(levels, b)
            if isinstance(hi, tuple) and isinstance(lo, tuple):
                excluded.update(set(hi) - set(lo))

    cell_dates: set = set()
    field_tokens: set = set()
    if isinstance(parsed, Mapping):
        for (eng, scn), rows in parsed.items():
            if not isinstance(rows, Mapping):
                continue
            for d in rows:
                cell_dates.add(f"{eng}|{scn}|{d}")
                for name in _report.FORMAL_RECORD_FIELDS:
                    field_tokens.add(f"{eng}|{scn}|{d}|{name}")

    obs = getattr(evidence.frozen_hash_observation, "observed", None)
    declared = _get(formal, "governance", "frozen_hashes")
    hash_paths = (frozenset(map(str, declared))
                  if (isinstance(obs, Mapping) and obs
                      and isinstance(declared, Mapping)) else frozenset())

    return {
        "singleton": frozenset({"*"}),
        "af1_days": af1,
        "f10_population": af1,
        "sealed_dates": frozenset(
            d for rows in (parsed or {}).values()
            if isinstance(rows, Mapping) for d in rows),
        "sealed_cell_dates": frozenset(cell_dates),
        "record_field_tokens": frozenset(field_tokens),
        "constructible_days": frozenset(constructible),
        "constructible_days_long": frozenset(
            d for d in constructible if d_open_of.get(d) == 1),
        "constructible_days_short": frozenset(
            d for d in constructible if d_open_of.get(d) == -1),
        "tp_union": frozenset(tp_union),
        "theta_eng_scn": frozenset(
            f"{t}|{e}|{s}" for t in theta_keys for e in engines
            for s in _SCENARIO_AXIS),
        "boot_cells": frozenset(
            f"{t}|{e}|{s}|block{b}" for t in theta_keys for e in engines
            for s in _SCENARIO_AXIS for b in FROZEN_BLOCKS),
        "na_fields": frozenset(
            [f"features.{c}" for c in FEATURE_NA_FIELDS]
            + [f"labels.{c}" for c in LABEL_NA_FIELDS]),
        "funnel_levels": frozenset(_FUNNEL_LEVELS),
        "excluded_days": frozenset(excluded),
        "frozen_hash_paths": hash_paths,
        "provenance_keys": frozenset(PROVENANCE_REGISTRY),
        "axis_thetas": frozenset(str(i) for i in range(len(frozen_thetas))),
        "axis_engines": frozenset(str(i) for i in range(len(engines))),
        "axis_scenarios": frozenset(_SCENARIO_AXIS),
        "axis_eras": frozenset(str(e) for e in _study.ERA_AXIS),
        "axis_blocks": frozenset(str(b) for b in FROZEN_BLOCKS),
    }


def _emit(tokens, leaf_id, entity) -> None:
    """The ONLY writer into the leaf-token accumulator."""
    tokens.setdefault(leaf_id, _Counter())[entity] += 1


def _leaves_ev1(evidence, formal, tokens, problems) -> None:
    facts = evidence.day_facts if isinstance(evidence.day_facts,
                                             tuple) else ()
    f10_final = {}
    memberships = (evidence.f10_memberships
                   if isinstance(evidence.f10_memberships, tuple) else ())
    for m in memberships:
        f10_final.setdefault(getattr(m, "trade_date", None),
                             getattr(m, "final_category", None))
    dir_counts: dict = {}
    na_none = 0
    for f in facts:
        d = f.trade_date
        for name in ("trade_date", "year", "era", "d_open", "y_cont",
                     "oracle_candidate", "trade_constructible",
                     "untradeable_reason", "record_year", "record_era",
                     "record_oracle_candidate", "tradeable_direction",
                     "y_cont_available", "direction_status", "is_event_day"):
            _emit(tokens, f"EV-1.{name}", d)
        # --- producer mirrors: the drift comparison EV-1's docstring
        #     promises and that nothing performed ------------------------
        for name, want in (("record_year", f.year), ("record_era", f.era),
                           ("record_oracle_candidate", f.oracle_candidate),
                           ("tradeable_direction", f.d_open != 0),
                           ("y_cont_available", f.y_cont is not None)):
            if not _strict_equal(getattr(f, name), want):
                problems.append(
                    f"evidence_ev1_mirror_drift:{name}:{d}:"
                    f"{getattr(f, name)!r}!={want!r}")
        # --- direction_status: dataset.py:307-308 makes the DIRECTIONAL
        #     predicate an exact function of d_open ----------------------
        status = f.direction_status
        dir_counts[status] = dir_counts.get(status, 0) + 1
        if (status == DIRECTION_DIRECTIONAL) != (f.d_open != 0):
            problems.append(
                f"evidence_ev1_direction_status_vs_d_open:{d}:{status!r}:"
                f"d_open={f.d_open}")
        elif status != DIRECTION_DIRECTIONAL and status not in _DIRECTION_NA:
            problems.append(
                f"evidence_ev1_direction_status_vocabulary:{d}:{status!r}")
        if f.untradeable_reason is not None and \
                f.untradeable_reason not in _UNTRADEABLE_VOCAB:
            problems.append(
                f"evidence_ev1_untradeable_reason_vocabulary:{d}:"
                f"{f.untradeable_reason!r}")
        # --- is_event_day: EV-10's per-date category is the second reading
        if f.is_event_day is None:
            na_none += 1
        want_cat = (f.is_event_day if f.is_event_day is not None
                    else "NA_multi_event")
        got_cat = f10_final.get(d)
        if got_cat is not None and not _strict_equal(got_cat, want_cat):
            problems.append(
                f"evidence_ev1_is_event_day_vs_ev10:{d}:{f.is_event_day!r}!="
                f"{got_cat!r}")
    declared_dir = _get(formal, "structural", "na_table", "direction")
    if isinstance(declared_dir, Mapping) and facts:
        for cls in (DIRECTION_DIRECTIONAL,) + tuple(sorted(_DIRECTION_NA)):
            got = _get(declared_dir, cls)
            if got is not None and not _strict_equal(got,
                                                     dir_counts.get(cls, 0)):
                problems.append(
                    f"evidence_ev1_direction_status_counts:{cls}:{got!r}!="
                    f"{dir_counts.get(cls, 0)!r}")
    want_na = _get(formal, "structural", "na_table", "per_field", "features",
                   "is_event_day", "na")
    if want_na is not None and facts and not _strict_equal(want_na, na_none):
        problems.append(
            f"evidence_ev1_is_event_day_na_count:{want_na!r}!={na_none!r}")


def _leaves_ev2(evidence, tokens, problems) -> None:
    paths = (evidence.theoretical_paths
             if isinstance(evidence.theoretical_paths, tuple) else ())
    facts = evidence.day_facts if isinstance(evidence.day_facts,
                                             tuple) else ()
    d_open_of = {f.trade_date: f.d_open for f in facts}
    snaps = {s.name: s for s in (evidence.cost_scenarios
                                 if isinstance(evidence.cost_scenarios, tuple)
                                 else ())}
    base = snaps.get(_study.BASE_SCENARIO_NAME)
    for p in paths:
        d = p.trade_date
        for name in ("trade_date", "direction", "scenario_name",
                     "entry_ref_price", "entry_fill",
                     "favourable_extreme_price", "favourable_extreme_ts",
                     "exit_fill", "pnl_per_contract", "platform_fee_rt_usd"):
            _emit(tokens, f"EV-2.{name}", d)
        want_dir = d_open_of.get(d)
        if want_dir is not None and not _strict_equal(int(p.direction),
                                                      int(want_dir)):
            problems.append(f"evidence_ev2_leaf:direction:{d}:"
                            f"{p.direction!r}!={want_dir!r}")
        if not _strict_equal(p.scenario_name, _study.BASE_SCENARIO_NAME):
            problems.append(f"evidence_ev2_leaf:scenario_name:{d}:"
                            f"{p.scenario_name!r}")
        if base is None or want_dir not in (1, -1):
            continue
        if not _close(p.platform_fee_rt_usd, base.platform_fee_rt_usd):
            problems.append(f"evidence_ev2_leaf:platform_fee_rt_usd:{d}")
        want_entry = _costs.entry_fill(
            float(p.entry_ref_price), int(want_dir),
            base.friction_multiplier * base.spread_points,
            base.friction_multiplier * base.slippage_ticks_per_side)
        if not _close(p.entry_fill, want_entry):
            problems.append(f"evidence_ev2_leaf:entry_fill:{d}:"
                            f"{p.entry_fill!r}!={want_entry!r}")
        # exit_fill is DETERMINED by the bound pnl + entry_fill + fee
        want_exit = (float(p.entry_fill)
                     + (float(p.pnl_per_contract)
                        + float(base.platform_fee_rt_usd))
                     / (int(want_dir) * MNQ_POINT_VALUE_USD))
        if not _close(p.exit_fill, want_exit):
            problems.append(f"evidence_ev2_leaf:exit_fill:{d}:"
                            f"{p.exit_fill!r}!={want_exit!r}")
        # ...and the favourable extreme is the timed-exit formula inverted
        want_fav = (float(p.exit_fill) + int(want_dir) * (
            base.friction_multiplier * base.spread_points / 2.0
            + base.friction_multiplier * base.slippage_ticks_per_side
            * _MNQ_TICK_POINTS))
        if not _close(p.favourable_extreme_price, want_fav):
            problems.append(
                f"evidence_ev2_leaf:favourable_extreme_price:{d}:"
                f"{p.favourable_extreme_price!r}!={want_fav!r}")
        # the ts has NO captured preimage — only a structural window rail
        ts = p.favourable_extreme_ts
        ok = (isinstance(ts, str) and ts[:10] == d and "T" in ts
              and _TS_LO <= ts[11:16] <= _TS_HI)
        if not ok:
            problems.append(f"evidence_ev2_favourable_extreme_ts:{d}:{ts!r}")


def _leaves_ev3(evidence, tokens, problems) -> None:
    ranges = (evidence.opening_ranges
              if isinstance(evidence.opening_ranges, tuple) else ())
    facts = evidence.day_facts if isinstance(evidence.day_facts,
                                             tuple) else ()
    d_open_of = {f.trade_date: f.d_open for f in facts}
    span = _ctx.OBS_HI_MINUTE - _ctx.OBS_LO_MINUTE + 1
    for o in ranges:
        d = o.trade_date
        for name in ("trade_date", "anchor_stop", "d_open", "n_obs_bars"):
            _emit(tokens, f"EV-3.{name}", d)
        _emit(tokens, "EV-3.or_high@long" if o.d_open == 1
              else "EV-3.or_high@short", d)
        _emit(tokens, "EV-3.or_low@long" if o.d_open == 1
              else "EV-3.or_low@short", d)
        want_dir = d_open_of.get(d)
        if want_dir is not None and not _strict_equal(int(o.d_open),
                                                      int(want_dir)):
            problems.append(f"evidence_ev3_d_open_vs_ev1:{d}:{o.d_open!r}!="
                            f"{want_dir!r}")
        # study.py:225-228 — the anchor is the OPPOSITE opening-range extreme
        want_anchor = o.or_low if o.d_open == 1 else o.or_high
        if not _close(o.anchor_stop, want_anchor):
            problems.append(f"evidence_ev3_anchor_side:{d}:"
                            f"{o.anchor_stop!r}!={want_anchor!r}")
        if not (_num(o.or_high) and _num(o.or_low)
                and float(o.or_high) >= float(o.or_low)):
            problems.append(f"evidence_ev3_or_range_rail:{d}")
        if not (isinstance(o.n_obs_bars, int)
                and not isinstance(o.n_obs_bars, bool)
                and 1 <= o.n_obs_bars <= span):
            problems.append(f"evidence_ev3_n_obs_bars_range:{d}:"
                            f"{o.n_obs_bars!r}")


def _leaves_ev4(evidence, tokens, problems) -> None:
    snaps = (evidence.cost_scenarios
             if isinstance(evidence.cost_scenarios, tuple) else ())
    dr1 = _get(evidence.provenance, "EV-4_dr1_status")
    scalars = None
    for s in snaps:
        for name in ("name", "spread_points", "slippage_ticks_per_side",
                     "adverse_slippage_ticks", "friction_multiplier",
                     "platform_fee_rt_usd", "spread_scalars",
                     "reduction_rule_id", "adverse_semantics"):
            _emit(tokens, f"EV-4.{name}", s.name)
        if scalars is None:
            scalars = tuple(s.spread_scalars)
        elif tuple(s.spread_scalars) != scalars:
            problems.append(
                f"evidence_ev4_spread_scalars:not_identical_across_axis:"
                f"{s.name}")
        # DR-1 tokens: unruled VALUES, but the iff against the recorded
        # status is a real consistency rail.
        for name in ("reduction_rule_id", "adverse_semantics"):
            value = getattr(s, name)
            if not isinstance(value, str) or not value:
                problems.append(f"evidence_ev4_dr1_token:{name}:{s.name}:"
                                f"{value!r}")
                continue
            claims_unresolved = value == UNRESOLVED_SPREAD_RULE
            if claims_unresolved != (dr1 == STATUS_UNRESOLVED):
                problems.append(
                    f"evidence_ev4_dr1_token:{name}:{s.name}:{value!r} vs "
                    f"provenance EV-4_dr1_status={dr1!r}")
    if scalars is None:
        return
    try:
        rebuilt = _costs.build_scenarios(*scalars)
    except Exception as exc:                             # noqa: BLE001
        problems.append(f"evidence_ev4_spread_scalars:unusable:"
                        f"{type(exc).__name__}")
        return
    by_name = {s.name: s for s in snaps}
    for name in _SCENARIO_AXIS:
        want, got = rebuilt.get(name), by_name.get(name)
        if want is None or got is None:
            continue
        for field in ("spread_points", "slippage_ticks_per_side",
                      "adverse_slippage_ticks", "friction_multiplier",
                      "platform_fee_rt_usd"):
            if not _close(getattr(got, field), getattr(want, field)):
                problems.append(
                    f"evidence_ev4_spread_scalars:{name}.{field}:"
                    f"{getattr(got, field)!r}!={getattr(want, field)!r}")


def _leaves_ev5(evidence, tokens, problems) -> None:
    strata = evidence.day_strata if isinstance(evidence.day_strata,
                                               tuple) else ()
    fact_map = evidence.day_fact_map()
    dr2 = _get(evidence.provenance, "EV-5_dr2_status")
    dr6 = _get(evidence.provenance, "EV-5_dr6_status")
    theta_keys = tuple(_study.theta_key(t) for t in _study.FROZEN_THETAS)
    for s in strata:
        d = s.trade_date
        for name in ("trade_date", "year", "micro_execution_era",
                     "stability_epoch", "d_open", "volatility_regime_label",
                     "vol_status", "event_flag_final", "event_na",
                     "event_stratum", "tp_fp_class"):
            _emit(tokens, f"EV-5.{name}", d)
        fact = fact_map.get(d)
        if fact is not None:
            want_flag = (fact.is_event_day if fact.is_event_day is not None
                         else "NA_multi_event")
            for name, want in (("year", fact.year), ("d_open", fact.d_open),
                               ("event_flag_final", want_flag),
                               ("event_na", fact.is_event_day is None)):
                if not _strict_equal(getattr(s, name), want):
                    problems.append(
                        f"evidence_ev5_mirror:{name}:{d}:"
                        f"{getattr(s, name)!r}!={want!r}")
        if not _strict_equal(s.vol_status, dr2):
            problems.append(f"evidence_ev5_vol_status:{d}:{s.vol_status!r}!="
                            f"{dr2!r}")
        if s.vol_status == STATUS_UNRESOLVED and \
                s.volatility_regime_label != UNRESOLVED_VOL:
            problems.append(f"evidence_ev5_dr2_label:{d}:"
                            f"{s.volatility_regime_label!r}")
        if dr6 == STATUS_UNRESOLVED and s.event_na and \
                s.event_stratum != UNRESOLVED_EVENT_STRATUM:
            problems.append(f"evidence_ev5_dr6_stratum:{d}:"
                            f"{s.event_stratum!r}")
        # the dynamic Mapping is checked as an EXACT key set against the
        # FROZEN theta axis, never by iterating whatever keys exist.
        keys = set(s.tp_fp_class) if isinstance(s.tp_fp_class, Mapping) \
            else set()
        if keys != set(theta_keys):
            problems.append(
                f"evidence_ev5_tp_fp_class_key_set:{d}:"
                f"missing={sorted(set(theta_keys) - keys)}:"
                f"extra={sorted(keys - set(theta_keys))}")


def _leaves_ev6(evidence, tokens, problems, membership) -> None:
    pools = evidence.grid_pools if isinstance(evidence.grid_pools,
                                              tuple) else ()
    for g in pools:
        cell = f"{g.theta_key}|{g.engine}|{g.scenario}"
        for name in ("theta_key", "engine", "scenario", "tp_pools.UNION",
                     "fp_pools.UNION", "tp_pools.STRATUM", "fp_pools.STRATUM",
                     "tp_avail", "fp_avail", "n_tp_available",
                     "n_fp_available", "grid_stream_tag", "stratum_axes"):
            _emit(tokens, f"EV-6.{name}", cell)
        if not _strict_equal(g.grid_stream_tag,
                             int(_gridmix.GRID_STREAM_TAG)):
            problems.append(f"evidence_ev6_leaf:grid_stream_tag:{cell}:"
                            f"{g.grid_stream_tag!r}")
        if tuple(g.stratum_axes) != GRID_STRATUM_AXES:
            problems.append(f"evidence_ev6_leaf:stratum_axes:{cell}:"
                            f"{tuple(g.stratum_axes)!r}")
        want_tp, want_fp = membership.get(g.theta_key, ((), ()))
        for side, pool, avail, count, want in (
                ("tp", g.tp_pools, g.tp_avail, g.n_tp_available, want_tp),
                ("fp", g.fp_pools, g.fp_avail, g.n_fp_available, want_fp)):
            if not isinstance(pool, Mapping) or not isinstance(avail, Mapping):
                problems.append(f"evidence_ev6_pool_shape:{side}:{cell}")
                continue
            flat = [d for v in pool.values() for d in (v or ())]
            if sorted(flat) != sorted(want) or len(set(flat)) != len(flat):
                problems.append(
                    f"evidence_ev6_pool_union:{side}:{cell}:"
                    f"missing={sorted(set(want) - set(flat))[:3]}:"
                    f"extra={sorted(set(flat) - set(want))[:3]}")
            if set(avail) != set(pool):
                problems.append(f"evidence_ev6_leaf:{side}_avail:{cell}:"
                                "key set differs from the pool")
            elif any(avail.get(k) != len(pool.get(k) or ())
                     for k in sorted(pool)):
                problems.append(f"evidence_ev6_leaf:{side}_avail:{cell}")
            if not _strict_equal(count, len(want)):
                problems.append(
                    f"evidence_ev6_leaf:n_{side}_available:{cell}:"
                    f"{count!r}!={len(want)!r}")


def _leaves_ev7(evidence, tokens, problems, d_tp, membership) -> None:
    cells = (evidence.bootstrap_inputs
             if isinstance(evidence.bootstrap_inputs, tuple) else ())
    want_seeds = tuple(int(s) for s in RESEARCH_BOOTSTRAP_SEEDS)
    for b in cells:
        key = b.cell_key
        for name in ("cell_key", "theta_key", "engine", "scenario",
                     "block_len", "n", "series_sha256",
                     "series_mean_sum_over_n", "series_mean_numpy",
                     "series_sum", "first_date", "last_date", "seeds",
                     "stats_stream_tag", "block_stream_key", "n_boot",
                     "ci_level", "percentile_method_id"):
            _emit(tokens, f"EV-7.{name}", key)
        parts = str(key).split("|")
        if len(parts) == 4:
            for name, want in (("theta_key", parts[0]), ("engine", parts[1]),
                               ("scenario", parts[2])):
                if not _strict_equal(getattr(b, name), want):
                    problems.append(f"evidence_ev7_leaf:{name}:{key}")
            if parts[3] != f"block{b.block_len}":
                problems.append(f"evidence_ev7_leaf:block_len:{key}")
        for name, want in (("seeds", want_seeds),
                           ("stats_stream_tag", int(_stats.STATS_STREAM_TAG)),
                           ("n_boot", int(_stats.N_BOOT)),
                           ("ci_level", float(_stats.CI_LEVEL)),
                           ("percentile_method_id",
                            str(_stats.PERCENTILE_METHOD))):
            got = tuple(getattr(b, name)) if name == "seeds" \
                else getattr(b, name)
            if not _strict_equal(got, want):
                problems.append(f"evidence_ev7_leaf:{name}:{key}:{got!r}!="
                                f"{want!r}")
        try:
            want_bsk = int(_stats.block_stream_key(float(b.block_len)))
        except Exception:                                # noqa: BLE001
            want_bsk = None
        if want_bsk is not None and not _strict_equal(b.block_stream_key,
                                                      want_bsk):
            problems.append(f"evidence_ev7_leaf:block_stream_key:{key}:"
                            f"{b.block_stream_key!r}!={want_bsk!r}")
        pnl = d_tp.get((b.theta_key, b.engine, b.scenario), {})
        tp_days = membership.get(b.theta_key, ((), ()))[0]
        ordered = [(d, float(pnl[d])) for d in sorted(tp_days) if d in pnl]
        if not _strict_equal(b.n, len(ordered)):
            problems.append(f"evidence_ev7_leaf:n:{key}:{b.n!r}!="
                            f"{len(ordered)!r}")
        want_first = ordered[0][0] if ordered else None
        want_last = ordered[-1][0] if ordered else None
        for name, want in (("first_date", want_first),
                           ("last_date", want_last)):
            if not _strict_equal(getattr(b, name), want):
                problems.append(f"evidence_ev7_leaf:{name}:{key}:"
                                f"{getattr(b, name)!r}!={want!r}")
        want_sum = float(sum(v for _d, v in ordered)) if ordered else 0.0
        if not _close(b.series_sum, want_sum):
            problems.append(f"evidence_ev7_leaf:series_sum:{key}:"
                            f"{b.series_sum!r}!={want_sum!r}")


def _leaves_ev8(evidence, tokens, problems, formal) -> None:
    obs = (evidence.na_observations
           if isinstance(evidence.na_observations, tuple) else ())
    population = _get(formal, "structural", "na_table", "population")
    for o in obs:
        key = f"{o.table}.{o.column}"
        for name in ("table", "column", "n_null", "n_not_null",
                     "observation_method_id"):
            _emit(tokens, f"EV-8.{name}", key)
        want_id = NA_OBSERVATION_METHOD_ID.get(o.table)
        if want_id is not None and not _strict_equal(o.observation_method_id,
                                                     want_id):
            problems.append(
                f"evidence_ev8_leaf:observation_method_id:{key}:"
                f"{o.observation_method_id!r}")
        if population is not None and not _strict_equal(
                o.n_null + o.n_not_null, population):
            problems.append(
                f"evidence_ev8_leaf:na_conservation:{key}:"
                f"{o.n_null + o.n_not_null}!={population!r}")


def _leaves_ev9(evidence, tokens, problems) -> None:
    levels = getattr(evidence.funnel, "level_dates", None)
    reasons = getattr(evidence.funnel, "exclusion_reason", None)
    _emit(tokens, "EV-9.provenance", "*")
    if isinstance(levels, Mapping):
        for level in _FUNNEL_LEVELS:
            dates = _get(levels, level)
            if not isinstance(dates, tuple):
                continue
            _emit(tokens, "EV-9.level_dates", level)
            if list(dates) != sorted(set(dates)):
                problems.append(
                    f"evidence_ev9_level_not_sorted_unique:{level}")
        chain = _FUNNEL_LEVELS[:5]
        for a, b in zip(chain, chain[1:]):
            hi, lo = _get(levels, a), _get(levels, b)
            if isinstance(hi, tuple) and isinstance(lo, tuple) and \
                    not set(lo) <= set(hi):
                problems.append(f"evidence_ev9_level_not_nested:{b}<={a}")
    # the key set AND the reason are both decided by the level differences
    want: dict = {}
    if isinstance(levels, Mapping):
        for a, b, reason in (
                ("L0_scheduled_trading_days", "L1_observed_rth_days",
                 _ctx.REASON_ZERO_BARS),
                ("L1_observed_rth_days", "L2_regular_full_session_candidates",
                 _ctx.REASON_HALF_DAY),
                ("L2_regular_full_session_candidates",
                 "L3_structurally_eligible_days",
                 _ctx.REASON_MISSING_GT_10PCT)):
            hi, lo = _get(levels, a), _get(levels, b)
            if isinstance(hi, tuple) and isinstance(lo, tuple):
                for d in set(hi) - set(lo):
                    want[d] = reason
    if not isinstance(reasons, Mapping):
        if want:
            problems.append("evidence_ev9_exclusion_reason_not_a_mapping")
        return
    got_keys = set(_report._safe_keys(reasons))
    for d in _report._safe_sorted(got_keys):
        _emit(tokens, "EV-9.exclusion_reason", d)
    for d in _report._safe_sorted(got_keys - set(want)):
        problems.append(f"evidence_ev9_exclusion_reason_extra:{d}")
    for d in sorted(set(want) - got_keys):
        problems.append(f"evidence_ev9_exclusion_reason_missing:{d}")
    for d in sorted(set(want) & got_keys):
        if not _strict_equal(_get(reasons, d), want[d]):
            problems.append(
                f"evidence_ev9_exclusion_reason_mismatch:{d}:"
                f"{_get(reasons, d)!r}!={want[d]!r}")


def _leaves_ev10(evidence, tokens, problems) -> None:
    memberships = (evidence.f10_memberships
                   if isinstance(evidence.f10_memberships, tuple) else ())
    fact_map = evidence.day_fact_map()
    for m in memberships:
        d = m.trade_date
        for name in ("trade_date", "raw_categories", "final_category",
                     "raw_provenance"):
            _emit(tokens, f"EV-10.{name}", d)
        fact = fact_map.get(d)
        if fact is None:
            continue
        want = (fact.is_event_day if fact.is_event_day is not None
                else "NA_multi_event")
        if not _strict_equal(m.final_category, want):
            problems.append(
                f"evidence_ev10_final_category_vs_ev1:{d}:"
                f"{m.final_category!r}!={want!r}")


def _leaves_ev11(evidence, tokens, problems, formal) -> None:
    """EV-11's leaves. THE fenced family (matrix S3).

    What binds here without touching the IR-23 reducer: the EXACT
    `available` key set against the frozen `PRE_Y6_LABEL_NA_FIELDS`
    vocabulary, `dir_ok` against EV-1.d_open, and the `adr_ok` POPULATION
    TOTAL against EV-8's independent null scan. What does NOT bind, and is
    disclosed rather than dressed up: the per-day values of
    o1000/c1544/pm_ok/adr_ok and every per-day `available[<label>]`.
    """
    rows = (evidence.label_availability
            if isinstance(evidence.label_availability, tuple) else ())
    fact_map = evidence.day_fact_map()
    constructible = {d for d, f in fact_map.items()
                     if getattr(f, "trade_constructible", False)}
    tp_dates = {p.trade_date for p in (evidence.theoretical_paths
                                       if isinstance(evidence.theoretical_paths,
                                                     tuple) else ())}
    vocab = frozenset(PRE_Y6_LABEL_NA_FIELDS)
    n_adr = 0
    for r in rows:
        d = r.trade_date
        for name in ("trade_date", "o1000", "c1544", "pm_ok", "adr_ok",
                     "dir_ok"):
            _emit(tokens, f"EV-11.{name}", d)
        if r.adr_ok:
            n_adr += 1
        # dir_ok: dataset.py:307-308 + 687 make this an exact identity
        fact = fact_map.get(d)
        if fact is not None and not _strict_equal(bool(r.dir_ok),
                                                  fact.d_open != 0):
            problems.append(
                f"evidence_ev11_dir_ok_vs_d_open:{d}:{r.dir_ok!r}!="
                f"{fact.d_open != 0!r}")
        # one-directional rails (never a closure claim)
        if d in constructible and not r.pm_ok:
            problems.append(f"evidence_ev11_pm_ok_rail:{d}")
        if d in tp_dates and not r.o1000:
            problems.append(f"evidence_ev11_o1000_rail:{d}")
        # the dynamic Mapping: EXACT key set x entity set against the frozen
        # vocabulary. Iterating whatever keys exist is what made a key
        # deleted from EVERY row byte-identical to an honest run.
        keys = set(_report._safe_keys(r.available)) \
            if isinstance(r.available, Mapping) else set()
        if keys != vocab:
            problems.append(
                f"evidence_ev11_available_key_set:{d}:"
                f"missing={sorted(vocab - keys)}:extra={sorted(keys - vocab)}")
            continue
        if any(not isinstance(_get(r.available, k), bool) for k in vocab):
            problems.append(f"evidence_ev11_available_value_type:{d}")
            continue
        _emit(tokens, "EV-11.available.KEYSET", d)
        _emit(tokens, "EV-11.available.VALUE", d)
    want_adr = _get(formal, "structural", "na_table", "per_field", "features",
                    "adr14", "not_na")
    if rows and want_adr is not None and not _strict_equal(n_adr, want_adr):
        problems.append(
            f"evidence_ev11_adr_ok_total_vs_ev8:{n_adr}!={want_adr!r}")


def _leaves_ev12_ev13_top(evidence, tokens, problems, parsed) -> None:
    ident = evidence.estimator_identity
    for name in ("study_percentile_method", "stability_percentile_method",
                 "stats_percentile_method", "all_three_agree",
                 "worst_day_estimator_ruling", "estimator_status_expected"):
        _emit(tokens, f"EV-12.{name}", "*")
    ruling = getattr(ident, "worst_day_estimator_ruling", None)
    want_status = ("resolved" if ruling is not None
                   else _ESTIMATOR_STATUS_UNRESOLVED)
    if not _strict_equal(getattr(ident, "estimator_status_expected", None),
                         want_status):
        problems.append(
            f"evidence_ev12_ruling_vs_status:{ruling!r} implies "
            f"{want_status!r}, got "
            f"{getattr(ident, 'estimator_status_expected', None)!r}")
    _emit(tokens, "EV-13.provenance", "*")
    observed = getattr(evidence.frozen_hash_observation, "observed", None)
    if isinstance(observed, Mapping):
        for path in _report._safe_sorted(_report._safe_keys(observed)):
            _emit(tokens, "EV-13.observed", str(path))
    _emit(tokens, "TOP.schema_version", "*")
    for name, axis_value in (("thetas", evidence.thetas),
                             ("engines", evidence.engines),
                             ("scenarios", evidence.scenarios),
                             ("eras", evidence.eras),
                             ("blocks", evidence.blocks)):
        if not isinstance(axis_value, tuple):
            continue
        for i, value in enumerate(axis_value):
            _emit(tokens, f"TOP.{name}",
                  str(value) if name in ("scenarios", "eras", "blocks")
                  else str(i))
    prov = evidence.provenance
    if isinstance(prov, Mapping):
        for key in _report._safe_sorted(_report._safe_keys(prov)):
            _emit(tokens, "TOP.provenance", key)
            if key not in PROVENANCE_REGISTRY:
                problems.append(f"evidence_provenance_key_extra:{key}")
    if not isinstance(parsed, Mapping):
        return
    pnl = evidence.record_pnl
    fields = evidence.record_fields
    for (eng, scn), rows in sorted(parsed.items()):
        cell = f"{eng}|{scn}"
        cap_pnl = _get(pnl, cell)
        if isinstance(cap_pnl, Mapping):
            for d in _report._safe_sorted(_report._safe_keys(cap_pnl)):
                _emit(tokens, "TOP.record_pnl", f"{cell}|{d}")
                if d not in rows:
                    problems.append(
                        f"evidence_record_pnl_extra_row:{cell}:{d}")
        cap_f = _get(fields, cell)
        if isinstance(cap_f, Mapping):
            for d in _report._safe_sorted(_report._safe_keys(cap_f)):
                for name in _report.FORMAL_RECORD_FIELDS:
                    _emit(tokens, "TOP.record_fields", f"{cell}|{d}|{name}")


def _reconcile_leaves(evidence, formal, parsed, membership, d_tp, problems,
                      leaf_outcomes) -> None:
    """Run every leaf check, then apply TOKEN COMPLETENESS. The ONLY writer
    into `leaf_outcomes`. Never raises."""
    tokens: dict = {}
    for fn in (
            lambda: _leaves_ev1(evidence, formal, tokens, problems),
            lambda: _leaves_ev2(evidence, tokens, problems),
            lambda: _leaves_ev3(evidence, tokens, problems),
            lambda: _leaves_ev4(evidence, tokens, problems),
            lambda: _leaves_ev5(evidence, tokens, problems),
            lambda: _leaves_ev6(evidence, tokens, problems, membership),
            lambda: _leaves_ev7(evidence, tokens, problems, d_tp, membership),
            lambda: _leaves_ev8(evidence, tokens, problems, formal),
            lambda: _leaves_ev9(evidence, tokens, problems),
            lambda: _leaves_ev10(evidence, tokens, problems),
            lambda: _leaves_ev11(evidence, tokens, problems, formal),
            lambda: _leaves_ev12_ev13_top(evidence, tokens, problems, parsed),
    ):
        try:
            fn()
        except Exception as exc:                         # noqa: BLE001
            problems.append(f"evidence_leaf_check_raised:{type(exc).__name__}")
    axes = entity_axes_for(evidence, formal, parsed)
    # Every axis whose only authority is EV-9's L3 level fails closed
    # TOGETHER: without a universe there is no non-circular source for any
    # of them, and a reduced capture is a legitimate, DISCLOSED state.
    unauthoritative = (() if _af1_axis_is_authoritative(evidence)
                       else ("af1_days", "f10_population", "funnel_levels",
                             "excluded_days"))
    if unauthoritative:
        problems.append(
            f"{PARTIAL_PREFIX}{_S_AF1_AXIS}:{_R_AF1_AXIS}")
    for leaf_id, spec in LEAF_REGISTRY.items():
        got = tokens.get(leaf_id, _Counter())
        if spec.entity_axis in unauthoritative:
            leaf_outcomes[leaf_id] = LeafOutcome(
                leaf_id, 0, sum(got.values()),
                skipped_reason="entity axis has no authority without a "
                               "universe")
            continue
        outcome = _leaf_outcome_from(leaf_id, axes.get(spec.entity_axis, ()),
                                     got)
        leaf_outcomes[leaf_id] = outcome
        if not outcome.complete:
            problems.append(
                f"evidence_leaf_incomplete:{leaf_id}:"
                f"missing={list(outcome.missing[:3])}:"
                f"extra={list(outcome.extra[:3])}:"
                f"duplicate={list(outcome.duplicate[:3])}")


def reconcile_leaf_outcomes(evidence, formal, sealed_files) -> Mapping:
    """{leaf_id -> LeafOutcome} for one full reconcile. Never raises."""
    acc: dict = {}
    _report._guarded(
        "reconcile_leaf_outcomes",
        lambda problems: _reconcile_inner(evidence, formal, sealed_files,
                                          problems, None, acc),
        [])
    return MappingProxyType(dict(acc))


def _run_check(check_id, fn, outcomes, problems, pops) -> None:
    """The ONLY writer into `outcomes`. Refuses an unregistered id, refuses
    a duplicate id, attributes the problems the check appended, and applies
    THE GATE: an incomplete HARD check is a hard problem BY CONSTRUCTION,
    even if the check function itself forgot to say so."""
    spec = CHECK_REGISTRY.get(check_id)
    if spec is None:
        problems.append(f"evidence_check_unregistered:{check_id}")
        return
    if check_id in outcomes:
        problems.append(f"evidence_check_registered_twice:{check_id}")
        return
    before = len(problems)
    try:
        compared = int(fn())
    except Exception as exc:                             # noqa: BLE001
        problems.append(f"evidence_check_raised:{check_id}:"
                        f"{type(exc).__name__}")
        compared = 0
    outcome = CheckOutcome(
        check=check_id, field=spec.field,
        applicable=int(pops.get(spec.population, 0)),
        compared_count=max(0, compared))
    if (spec.incomplete_kind == _KIND_HARD and not outcome.not_applicable
            and not outcome.complete):
        problems.append(
            f"evidence_check_incomplete:{check_id}:"
            f"{outcome.compared_count}!={outcome.applicable}")
    outcome = _dc_replace(outcome, hard_problems=tuple(problems[before:]))
    outcomes[check_id] = _dc_replace(
        outcome, partial_markers=tuple(sorted(spec.markers_for(outcome))))


def _reconcile_inner(evidence, formal, sealed_files, problems,
                     outcomes=None, leaf_outcomes=None):
    if outcomes is None:
        outcomes = {}
    if leaf_outcomes is None:
        leaf_outcomes = {}
    if not isinstance(evidence, CanonicalS0Evidence):
        problems.append("evidence_not_canonical")
        return problems
    if not isinstance(formal, Mapping):
        problems.append("evidence_formal_not_a_mapping")
        return problems
    try:
        _reconcile_checks(evidence, formal, sealed_files, problems, outcomes,
                          leaf_outcomes)
    finally:
        # DISCLOSURE INTEGRITY: the marker set is appended even when a check
        # blew up above, so an internal error can never silently empty the
        # PARTIAL list the way it did before this round.
        problems.extend(sorted(_markers_from_registry(outcomes)))
    return problems


def _reconcile_checks(evidence, formal, sealed_files, problems, outcomes,
                      leaf_outcomes=None):
    if leaf_outcomes is None:
        leaf_outcomes = {}
    _preflight_field_shapes(evidence, problems)
    engines = tuple(evidence.engines)
    scenarios = tuple(evidence.scenarios)
    theta_keys = evidence.theta_keys()
    fact_map = evidence.day_fact_map()
    era_of = {d: f.era for d, f in fact_map.items()}

    # (a)+(c) the ACTUAL bytes ---------------------------------------------
    parsed: dict = {}
    pops = {"sealed_files": len(_study.ENGINES) * len(_SCENARIO_AXIS)}
    _run_check("bytes.parse",
               lambda: _parse_into(parsed, sealed_files, engines, scenarios,
                                   problems),
               outcomes, problems, pops)
    pops = _authoritative_populations(evidence, formal, parsed)

    # (b) rebuild D_TP / D_FP from BYTES + EV-1 membership -----------------
    membership: dict = {}
    for theta, tkey in zip(evidence.thetas, theta_keys):
        tp_days, fp_days = evidence.partition(theta)
        membership[tkey] = (tuple(tp_days), tuple(fp_days))
    universe_dates: set = set()
    for tp, fp in membership.values():
        universe_dates.update(tp)
        universe_dates.update(fp)

    d_tp: dict = {}
    d_fp: dict = {}
    for (eng, scn), rows in parsed.items():
        got = set(rows)
        if got != universe_dates:
            problems.append(
                "evidence_record_population_mismatch:"
                f"{eng}|{scn}:missing={sorted(universe_dates - got)[:5]}:"
                f"extra={sorted(got - universe_dates)[:5]}")
        for tkey in theta_keys:
            tp, fp = membership[tkey]
            d_tp[(tkey, eng, scn)] = {
                d: float(rows[d]["final_pnl_per_contract"])
                for d in tp if d in rows}
            d_fp[(tkey, eng, scn)] = {
                d: float(rows[d]["final_pnl_per_contract"])
                for d in fp if d in rows}

    # --- identity / axis bindings -----------------------------------------
    _run_check("schema_version.binding",
               lambda: _reconcile_schema_version(evidence, problems),
               outcomes, problems, pops)
    for check_id, name, frozen in (
            ("axis.thetas", "thetas", tuple(_study.FROZEN_THETAS)),
            ("axis.engines", "engines", tuple(_study.ENGINES)),
            ("axis.scenarios", "scenarios", _SCENARIO_AXIS),
            ("axis.eras", "eras", tuple(_study.ERA_AXIS)),
            ("axis.blocks", "blocks", tuple(FROZEN_BLOCKS))):
        _run_check(check_id,
                   (lambda n=name, f=frozen:
                    _reconcile_axis(evidence, n, f, problems)),
                   outcomes, problems, pops)
    _run_check("provenance.registry",
               lambda: _reconcile_provenance(evidence, problems),
               outcomes, problems, pops)

    # --- EV-1 --------------------------------------------------------------
    _run_check("EV-1.sealed_day_membership",
               lambda: _reconcile_sealed_day_membership(evidence, parsed,
                                                        problems),
               outcomes, problems, pops)
    _run_check("EV-1.reducer_subtrees",
               lambda: _reconcile_reducer_subtrees(evidence, formal, problems),
               outcomes, problems, pops)

    # (d) oracle_daily executable series + aggregates vs (b) ---------------
    for tkey in theta_keys:
        for eng in engines:
            for scn in scenarios:
                pnl = d_tp.get((tkey, eng, scn), {})
                tp_days = membership[tkey][0]
                cell = _get(formal, "oracle_daily", tkey, "executable", eng,
                            scn)
                pairs = [(d, pnl[d]) for d in tp_days if d in pnl]
                _compare_series_block(
                    pairs, _get(cell, "pooled"),
                    f"oracle_daily|{tkey}|{eng}|{scn}|pooled",
                    "daily_pnl_usd", problems)
                for era in evidence.eras:
                    era_pairs = [(d, v) for d, v in pairs
                                 if era_of.get(d) == era]
                    _compare_series_block(
                        era_pairs, _get(cell, "by_era", era),
                        f"oracle_daily|{tkey}|{eng}|{scn}|by_era|{era}",
                        "daily_pnl_usd", problems)
                # CR-6: the SAME two numbers live at three payload paths.
                _check_cr6(formal, tkey, eng, scn, problems)

    # --- AF2 projections + byte rails -------------------------------------
    _run_check("AF2.record_fields",
               lambda: _reconcile_record_fields(evidence, parsed, problems),
               outcomes, problems, pops)
    _run_check("AF2.record_pnl",
               lambda: _reconcile_record_pnl(evidence, parsed, problems),
               outcomes, problems, pops)
    _run_check("bytes.record_ranges",
               lambda: _reconcile_record_ranges(evidence, parsed, problems),
               outcomes, problems, pops)

    # --- EV-2 --------------------------------------------------------------
    _run_check("EV-2.tp_union_coverage",
               lambda: _reconcile_ev2_coverage(evidence, problems),
               outcomes, problems, pops)
    _run_check("EV-2.entry_fill_binding",
               lambda: _reconcile_entry_fill_vs_ev2(evidence, parsed,
                                                    problems),
               outcomes, problems, pops)

    # --- EV-4 --------------------------------------------------------------
    _run_check("EV-4.cost_snapshots",
               lambda: _reconcile_cost_snapshots(evidence, problems),
               outcomes, problems, pops)

    # --- the A1 `structural` consumers (EV-8/EV-9/EV-10/EV-11) and EV-5 ---
    _run_check("EV-9.funnel_counts",
               lambda: _reconcile_funnel(evidence, formal, problems),
               outcomes, problems, pops)
    _run_check("EV-10.exclusive_partition",
               lambda: _reconcile_f10_exclusive(evidence, formal, problems),
               outcomes, problems, pops)
    _run_check("EV-10.raw_membership",
               lambda: _reconcile_f10_raw(evidence, formal, problems),
               outcomes, problems, pops)
    _run_check("EV-11.day_coverage",
               lambda: _reconcile_ev11_coverage(evidence, problems),
               outcomes, problems, pops)
    _run_check("EV-11.label_anchor_availability",
               lambda: _reconcile_label_availability(evidence, formal,
                                                     problems),
               outcomes, problems, pops)
    _run_check("EV-8.field_coverage",
               lambda: _reconcile_na_field_coverage(evidence, problems),
               outcomes, problems, pops)
    _run_check("EV-8.na_table",
               lambda: _reconcile_na_table(evidence, formal, problems),
               outcomes, problems, pops)
    _run_check("EV-5.day_strata",
               lambda: _reconcile_day_strata(evidence, problems),
               outcomes, problems, pops)
    _run_check("EV-1.untradeable",
               lambda: _reconcile_untradeable(evidence, formal, problems),
               outcomes, problems, pops)
    _run_check("EV-1.coverage_budgets",
               lambda: _reconcile_coverage_budgets(
                   evidence, formal, parsed, membership, engines, scenarios,
                   theta_keys, problems),
               outcomes, problems, pops)

    # --- EV-3 --------------------------------------------------------------
    _run_check("EV-3.record_sizing_anchor",
               lambda: _reconcile_record_internals(evidence, parsed, problems),
               outcomes, problems, pops)
    _run_check("EV-3.sizing_rows",
               lambda: _reconcile_sizing(
                   evidence, formal, parsed, membership, fact_map, engines,
                   scenarios, theta_keys, problems),
               outcomes, problems, pops)

    # --- EV-1 stability / EV-7 / EV-6 --------------------------------------
    _run_check("EV-1.stability_views",
               lambda: _reconcile_stability(
                   evidence, formal, d_tp, membership, fact_map, engines,
                   scenarios, theta_keys, problems),
               outcomes, problems, pops)
    _run_check("EV-7.cell_coverage",
               lambda: _reconcile_bootstrap(evidence, formal, d_tp,
                                            membership, problems),
               outcomes, problems, pops)
    _run_check("EV-6.grid_pools",
               lambda: _reconcile_grid(
                   evidence, formal, parsed, membership, engines, scenarios,
                   theta_keys, problems),
               outcomes, problems, pops)

    # --- manifest / EV-12 / CR-9 / EV-13 ----------------------------------
    _run_check("bytes.manifest_counts",
               lambda: _reconcile_manifest_counts(formal, parsed, problems),
               outcomes, problems, pops)
    _run_check("EV-12.estimator_identity",
               lambda: _reconcile_estimator_identity(evidence, formal,
                                                     theta_keys, scenarios,
                                                     problems),
               outcomes, problems, pops)
    _run_check("CR-9.stream_tags",
               lambda: _reconcile_method_conventions(formal, problems),
               outcomes, problems, pops)
    _run_check("EV-13.frozen_hashes",
               lambda: _reconcile_frozen_hashes(evidence, formal, problems),
               outcomes, problems, pops)

    # --- LEAF LINEAGE (M6.1.4-R2): the completeness criterion one level
    #     down. Runs LAST so every population above it is already built.
    _reconcile_leaves(evidence, formal, parsed, membership, d_tp, problems,
                      leaf_outcomes)
    _attach_leaf_tokens(outcomes, leaf_outcomes)

    # A registered check that never produced an outcome is a HARD problem —
    # this is the `checks["day_strata"]` bug (written, never read) inverted.
    for check_id in CHECK_REGISTRY:
        if check_id not in outcomes:
            problems.append(f"evidence_check_not_run:{check_id}")
    return problems


def _parse_into(parsed, sealed_files, engines, scenarios, problems) -> int:
    parsed.update(_parse_sealed_rows(sealed_files, engines, scenarios,
                                     problems))
    return len(parsed)


def _reconcile_schema_version(evidence, problems) -> int:
    if not _strict_equal(evidence.schema_version, SCHEMA_VERSION):
        problems.append(
            f"evidence_schema_version_mismatch:{evidence.schema_version!r}!="
            f"{SCHEMA_VERSION!r}")
    return 1


def _reconcile_axis(evidence, name, frozen_axis, problems) -> int:
    """Bind one captured axis to its FROZEN module constant, position by
    position. An emptied axis compares 0 of len(frozen) and is refused by
    the completeness gate, never by a 'looks non-empty' test."""
    got = getattr(evidence, name, None)
    got = tuple(got) if isinstance(got, tuple) else ()
    compared = 0
    for i, want in enumerate(frozen_axis):
        if i >= len(got):
            break
        compared += 1
        if not _strict_equal(got[i], want):
            problems.append(
                f"evidence_axis_mismatch:{name}[{i}]:{got[i]!r}!={want!r}")
    if len(got) > len(frozen_axis):
        problems.append(
            f"evidence_axis_extra:{name}:{len(got)}>{len(frozen_axis)}")
    return compared


def _reconcile_provenance(evidence, problems) -> int:
    """The four DISTINCT deterministic dispositions of a critical provenance
    key: ABSENT, WRONG TYPE, OUT OF VOCABULARY, EXPLICITLY DISAGREEING.

    Absent is never equivalent to "agrees" — that equivalence is exactly
    what let a stripped `provenance` seal (finding F-2). Every key of
    `PROVENANCE_REGISTRY` must be present and valid; a missing one is BOTH
    its own hard problem and an incompleteness against the frozen key set.
    """
    prov = evidence.provenance
    if not isinstance(prov, Mapping):
        problems.append(
            f"evidence_provenance_not_a_mapping:{type(prov).__name__}")
        return 0
    bound = {
        "funnel.provenance": getattr(evidence.funnel, "provenance", None),
        "frozen_hash_observation.provenance": getattr(
            evidence.frozen_hash_observation, "provenance", None),
        "schema_version": evidence.schema_version,
    }
    raw_provs = {getattr(m, "raw_provenance", None)
                 for m in (evidence.f10_memberships
                           if isinstance(evidence.f10_memberships, tuple)
                           else ())}
    bound["f10_memberships.raw_provenance"] = (
        next(iter(raw_provs)) if len(raw_provs) == 1 else None)
    compared = 0
    for key, spec in PROVENANCE_REGISTRY.items():
        if key not in prov:
            problems.append(f"evidence_provenance_key_absent:{key}")
            continue
        value = prov.get(key)
        if not isinstance(value, str):
            problems.append(
                f"evidence_provenance_key_type:{key}:"
                f"{type(value).__name__}")
            continue
        compared += 1
        if spec.kind == _PROV_XCHECK:
            if value == _XCHECK_AGREES:
                pass
            elif value.startswith(_XCHECK_DISAGREE_PREFIX):
                # the EXISTING code for EV-2, preserved verbatim.
                if key == "EV-2_oracle_cross_check":
                    problems.append(
                        f"evidence_theoretical_oracle_cross_check:{value}")
                else:
                    problems.append(f"evidence_f10_flag_cross_check:{value}")
            else:
                problems.append(
                    f"evidence_provenance_key_vocabulary:{key}:{value!r}")
        elif spec.kind == _PROV_DR_STATUS:
            if value not in _DR_STATUS_VOCABULARY:
                problems.append(
                    f"evidence_provenance_key_vocabulary:{key}:{value!r}")
        elif spec.kind == _PROV_BOUND:
            want = bound.get(spec.bound_to)
            if want is None or not _strict_equal(value, want):
                problems.append(
                    f"evidence_provenance_binding:{key}:{value!r}!={want!r}")
        else:                                            # _PROV_LABEL
            for token in value.split("+"):
                if token not in _PROV_VOCABULARY:
                    problems.append(
                        f"evidence_provenance_key_vocabulary:{key}:"
                        f"{token!r}")
    return compared


def _reconcile_sealed_day_membership(evidence, parsed, problems) -> int:
    """Every date that reached the sealed bytes must have an EV-1 fact. The
    population is the PARSED date union — the bytes, not EV-1 itself."""
    fact_map = evidence.day_fact_map()
    dates: set = set()
    for rows in parsed.values():
        if isinstance(rows, Mapping):
            dates.update(rows)
    compared = 0
    for date in sorted(dates):
        if date not in fact_map:
            problems.append(f"evidence_ev1_missing_for_sealed_date:{date}")
            continue
        compared += 1
    return compared


def _reconcile_reducer_subtrees(evidence, formal, problems) -> int:
    theta_keys = evidence.theta_keys()
    _compare_tree(rebuild_day_universe(evidence),
                  {t: _get(formal, "oracle_daily", t, "day_universe")
                   for t in theta_keys},
                  "oracle_daily.day_universe", problems)
    _compare_tree(rebuild_frequency(evidence), _get(formal, "frequency"),
                  "frequency", problems)
    _compare_tree(rebuild_theoretical_oracle(evidence),
                  _get(formal, "theoretical_oracle"), "theoretical_oracle",
                  problems,
                  skip_leaf=lambda p: "worst_day_pnl_percentiles" in p)
    _compare_tree(rebuild_structural_eras(evidence),
                  _get(formal, "structural", "eras"), "structural.eras",
                  problems)
    _compare_tree(rebuild_structural_groups(evidence),
                  _get(formal, "structural", "groups"), "structural.groups",
                  problems)
    axes_f = _get(formal, "era_axis", "axes")
    if list(axes_f or []) != rebuild_era_axis_axes(evidence):
        problems.append("evidence_era_axis_axes_mismatch")
    return len(reducers)


def _reconcile_ev2_coverage(evidence, problems) -> int:
    """EV-2 must cover the WHOLE theoretical union, and the union is derived
    from EV-1 — so an EV-2 stripped to one row (which used to seal, because
    every consumer used `.get(date)`) is refused by the population."""
    day_facts = evidence.day_facts
    constructible = {f.trade_date for f in day_facts if f.trade_constructible}
    union: set = set()
    for theta in _study.FROZEN_THETAS:
        tp, _fp = _partition_from_facts(day_facts, theta, constructible)
        union.update(tp)
    have = {p.trade_date for p in evidence.theoretical_paths}
    compared = 0
    for date in sorted(union):
        if date not in have:
            problems.append(f"evidence_ev2_missing_for_tp_day:{date}")
            continue
        compared += 1
    return compared


def _reconcile_cost_snapshots(evidence, problems) -> int:
    have = {s.name: s for s in evidence.cost_scenarios}
    compared = 0
    for name in _SCENARIO_AXIS:
        snap = have.get(name)
        if snap is None:
            problems.append(f"evidence_ev4_snapshot_absent:{name}")
            continue
        compared += 1
        if not _num(snap.platform_fee_rt_usd) or not _num(
                snap.friction_multiplier):
            problems.append(f"evidence_ev4_snapshot_nonfinite:{name}")
    return compared


def _reconcile_ev11_coverage(evidence, problems) -> int:
    """EV-11 must carry one usable availability row per AF1 day."""
    have = {f.trade_date: f for f in evidence.label_availability}
    compared = 0
    for fact in evidence.day_facts:
        row = have.get(fact.trade_date)
        if row is None or not isinstance(row.available, Mapping) \
                or not row.available:
            problems.append(
                f"evidence_ev11_missing_for_day:{fact.trade_date}")
            continue
        compared += 1
    return compared


def _reconcile_na_field_coverage(evidence, problems) -> int:
    """EV-8 must cover the FROZEN NA field list. The authority is
    `dataset.FEATURE_NA_FIELDS` / `LABEL_NA_FIELDS` — a frozen schema
    contract, independent of both the payload and EV-8 itself."""
    have = {(o.table, o.column) for o in evidence.na_observations}
    compared = 0
    for table, fields in (("features", FEATURE_NA_FIELDS),
                          ("labels", LABEL_NA_FIELDS)):
        for col in fields:
            if (table, col) not in have:
                problems.append(
                    f"evidence_na_observation_absent:{table}.{col}")
                continue
            compared += 1
    return compared


def _reconcile_manifest_counts(formal, parsed, problems) -> int:
    compared = 0
    for (eng, scn), rows in sorted(parsed.items()):
        compared += 1
        reported = _get(formal, "mc_handoff_manifest", "counts", eng, scn,
                        "n_records")
        if reported != len(rows):
            problems.append(
                f"evidence_manifest_count_mismatch:{eng}|{scn}:"
                f"{reported}!={len(rows)}")
    return compared


def _reconcile_estimator_identity(evidence, formal, theta_keys, scenarios,
                                  problems) -> int:
    """EV-12 (CR-5), RE-DERIVED rather than trusted.

    Before this round reconcile read the CAPTURED `all_three_agree` boolean
    and nothing else, so an `EstimatorIdentityFact` carrying three BLANK
    method strings with `all_three_agree=True` sealed cleanly. Two things
    changed: the three strings are BOUND to the LIVE module constants
    (`study`/`stability`/`stats`.PERCENTILE_METHOD), and agreement is
    RE-DERIVED from the strings and cross-checked against the captured
    claim. What this does NOT do is rule the estimator — DR-8 is unruled and
    the two `worst_day_pnl_percentiles` markers stay permanent."""
    ident = evidence.estimator_identity
    compared = 0
    for label, got, want in (
            ("study", ident.study_percentile_method,
             str(_study.PERCENTILE_METHOD)),
            ("stability", ident.stability_percentile_method,
             str(_stability.PERCENTILE_METHOD)),
            ("stats", ident.stats_percentile_method,
             str(_stats.PERCENTILE_METHOD))):
        compared += 1
        if not _strict_equal(got, want):
            problems.append(
                f"evidence_percentile_constant_drift:{label}:{got!r}!="
                f"{want!r}")
    rederived = (ident.study_percentile_method
                 == ident.stability_percentile_method
                 == ident.stats_percentile_method)
    if not _strict_equal(bool(ident.all_three_agree), bool(rederived)):
        problems.append(
            "evidence_estimator_agreement_not_rederivable:"
            f"{ident.all_three_agree!r}!={rederived!r}")
    if not rederived:
        problems.append(
            "evidence_percentile_estimator_constants_disagree:"
            f"{ident.study_percentile_method}|"
            f"{ident.stability_percentile_method}|"
            f"{ident.stats_percentile_method}")
    for tkey in theta_keys:
        for scn in scenarios:
            compared += 1
            status = _get(formal, "e2_worst_days", tkey, scn,
                          "estimator_status")
            if status != ident.estimator_status_expected:
                problems.append(
                    f"evidence_estimator_status_mismatch:{tkey}|{scn}:"
                    f"{status!r}!={ident.estimator_status_expected!r}")
    return compared


def _reconcile_method_conventions(formal, problems) -> int:
    """CR-9 — method_conventions stream-tag prose vs the module constants."""
    tags = _get(_get(formal, "disclosures", "method_conventions"),
                "stream_tags")
    if tags is None:
        return 0
    if not isinstance(tags, str):
        problems.append("evidence_cr9_stream_tags_not_a_string")
        return 0
    for label, value in (("stats", _stats.STATS_STREAM_TAG),
                         ("gridmix", _gridmix.GRID_STREAM_TAG)):
        if str(value) not in tags:
            problems.append(
                f"evidence_cr9_stream_tag_prose_drift:{label}:{value}")
    return 1


def _reconcile_frozen_hashes(evidence, formal, problems) -> int:
    """EV-13 — `governance.frozen_hashes` against BYTES, not against itself.

    (C4's declared-fed-back remains a documented caller-attestation
    boundary: the production wiring's disk re-hash is the trust anchor.)"""
    obs = evidence.frozen_hash_observation
    declared = _get(formal, "governance", "frozen_hashes")
    if not (isinstance(obs.observed, Mapping) and obs.observed):
        return 0
    if not isinstance(declared, Mapping):
        problems.append("evidence_frozen_hashes_missing")
        return 0
    # COMPLETENESS: the observation must cover EXACTLY the declared path set.
    obs_keys = set(map(str, obs.observed))
    try:
        dec_keys = {str(k) for k in declared}
    except BaseException:
        dec_keys = set()     # unreadable keys: coverage is 0
    if obs_keys != dec_keys:
        problems.append(
            "evidence_frozen_hash_key_set_mismatch:missing="
            f"{sorted(dec_keys - obs_keys)}:extra="
            f"{sorted(obs_keys - dec_keys)}")
    # The paths that ARE observed are compared either way, so a wrong digest
    # is never masked by an incomplete key set.
    for path, digest in sorted(obs.observed.items()):
        if not _strict_equal(_get(declared, path), digest):
            problems.append(f"evidence_frozen_hash_mismatch:{path}")
    return len(dec_keys) if (obs_keys == dec_keys and dec_keys) else 0


# ---------------------------------------------------------------------------
# HIGH-2 (PHASE-E blind audit) — the A1 `structural` consumers.
#
# The finding: EV-5/EV-8/EV-9/EV-10/EV-11 (and `record_pnl`/`record_fields`)
# were CAPTURED and never READ, and the PARTIAL markers were gated on the
# capture PROVENANCE STRING rather than on a check having run. Supplying a
# universe therefore DROPPED the markers while nothing was verified, and
# these all sealed silently AND undisclosed:
#   C20 funnel_counts + 500 · C21 f10_raw_membership_counts + 77
#   C22 na_table moved together with disclosures.na_conservation
#   C23 label_anchor_availability + 13
# Every function below returns a `ran` flag, and a marker may be dropped
# ONLY when its check ran with a NON-EMPTY comparison.
# ---------------------------------------------------------------------------
def _reconcile_funnel(evidence, formal, problems) -> int:
    """EV-9 membership -> ALL TEN published `structural.funnel_counts` keys
    (C20). The four `minus_*` deductions are the level differences, and the
    side diagnostic is `complete_390`'s own size.

    Returns the number of FROZEN funnel levels actually consumed; the
    registry sizes the population at `len(_FUNNEL_LEVELS)`, so a reduced
    capture is an incompleteness rather than a silent `False`."""
    levels = evidence.funnel.level_dates
    needed = _FUNNEL_LEVELS
    present = [k for k in needed
               if isinstance(levels, Mapping) and k in levels]
    if len(present) < len(needed):
        return len(present)
    n = {k: len(levels[k]) for k in needed}
    expected = {
        "L0_scheduled_trading_days": n["L0_scheduled_trading_days"],
        "minus_zero_bar_days": (n["L0_scheduled_trading_days"]
                                - n["L1_observed_rth_days"]),
        "L1_observed_rth_days": n["L1_observed_rth_days"],
        "minus_scheduled_early_close_days":
            n["L1_observed_rth_days"] - n["L2_regular_full_session_candidates"],
        "L2_regular_full_session_candidates":
            n["L2_regular_full_session_candidates"],
        "minus_rth_missing_gt_10pct_days":
            (n["L2_regular_full_session_candidates"]
             - n["L3_structurally_eligible_days"]),
        "L3_structurally_eligible_days": n["L3_structurally_eligible_days"],
        "minus_adr14_warmup_days": (n["L3_structurally_eligible_days"]
                                    - n["L4_final_feature_construction_dates"]),
        "L4_final_feature_construction_dates":
            n["L4_final_feature_construction_dates"],
        "side_diagnostic_complete_390_bar_rth_days":
            n["side_diagnostic_complete_390_bar_rth_days"],
    }
    declared = _get(formal, "structural", "funnel_counts")
    if not isinstance(declared, Mapping):
        problems.append("evidence_funnel_counts_missing")
        return 0
    for key in sorted(expected):
        if not _strict_equal(_get(declared, key), expected[key]):
            problems.append(
                f"evidence_funnel_count_mismatch:{key}:"
                f"{_get(declared, key)!r}!={expected[key]!r}")
    # monotonicity of the level chain itself (an internal EV-9 invariant)
    order = needed[:5]
    for a, b in zip(order, order[1:]):
        if n[a] < n[b]:
            problems.append(f"evidence_funnel_not_monotonic:{a}<{b}")
    return len(needed)


def _reconcile_f10_exclusive(evidence, formal, problems) -> int:
    """EV-10 per-date membership -> `structural.f10_counts` (the exclusive
    partition) — C21. The applicable population is the funnel's
    L3_structurally_eligible_days (the population
    `S0Universe.f10_exclusive_counts` iterates), so a HALF-stripped EV-10
    is refused by the completeness gate instead of quietly comparing 23
    dates against a 46-date count."""
    exclusive = {"CPI": 0, "NFP": 0, "FOMC": 0, "none": 0,
                 "NA_multi_event": 0}
    compared = 0
    for m in evidence.f10_memberships:
        if m.final_category in exclusive:
            exclusive[m.final_category] += 1
            compared += 1
    if not compared:
        return 0
    declared = _get(formal, "structural", "f10_counts")
    if not isinstance(declared, Mapping):
        problems.append("evidence_f10_counts_missing")
        return 0
    for cat in sorted(exclusive):
        if not _strict_equal(_get(declared, cat), exclusive[cat]):
            problems.append(
                f"evidence_f10_count_mismatch:{cat}:"
                f"{_get(declared, cat)!r}!={exclusive[cat]!r}")
    return compared


def _reconcile_f10_raw(evidence, formal, problems) -> int:
    """EV-10 RAW multi-hot membership -> `structural.f10_raw_membership_
    counts` (matrix L003, which has NO verifier of any kind in the tree
    today). The raw sets need the EventCalendar; without it the check
    compares nothing and the dedicated PARTIAL stays up."""
    memberships = evidence.f10_memberships
    if not memberships:
        return 0
    if not all(m.raw_provenance == PROV_ATOM_UNIVERSE for m in memberships):
        return 0
    raw = {"CPI": 0, "NFP": 0, "FOMC": 0, "none": 0, "multi_category": 0}
    for m in memberships:
        cats = tuple(m.raw_categories)
        for c in cats:
            if c in raw:
                raw[c] += 1
            else:
                # CLOSEOUT (auditor-1 round-2 LOW): a category outside the
                # frozen IR-12/18 vocabulary means the calendar disagrees
                # with the frozen event set — a HARD problem, never a
                # silent skip.
                problems.append(
                    "evidence_f10_out_of_vocabulary_category:"
                    f"{m.trade_date}:{c!r}")
        if not cats:
            raw["none"] += 1
        elif len(cats) > 1:
            raw["multi_category"] += 1
    declared_raw = _get(formal, "structural", "f10_raw_membership_counts")
    if not isinstance(declared_raw, Mapping):
        problems.append("evidence_f10_raw_membership_missing")
        return 0
    for cat in sorted(raw):
        if not _strict_equal(_get(declared_raw, cat), raw[cat]):
            problems.append(
                f"evidence_f10_raw_membership_mismatch:{cat}:"
                f"{_get(declared_raw, cat)!r}!={raw[cat]!r}")
    return len(memberships)


def _reconcile_label_availability(evidence, formal, problems) -> int:
    """EV-11's five per-day IR-23 dependency booleans, re-derived from the
    BARS, aggregated and compared against
    `structural.label_anchor_availability` (C23 / matrix L012)."""
    facts = evidence.label_availability
    if not facts:
        return 0
    counts: dict = {}
    compared = 0
    for fact in facts:
        available = fact.available
        if not isinstance(available, Mapping):
            continue
        compared += 1
        for label, ok in available.items():
            row = counts.setdefault(label, {"available_days": 0,
                                            "unavailable_days": 0})
            row["available_days" if ok else "unavailable_days"] += 1
    if not counts:
        return 0
    declared = _get(formal, "structural", "label_anchor_availability")
    if not isinstance(declared, Mapping):
        problems.append("evidence_label_anchor_availability_missing")
        return 0
    for label in sorted(counts):
        for field in ("available_days", "unavailable_days"):
            got = _get(declared, label, field)
            if not _strict_equal(got, counts[label][field]):
                problems.append(
                    f"evidence_label_anchor_mismatch:{label}.{field}:"
                    f"{got!r}!={counts[label][field]!r}")
    return compared


def _reconcile_na_table(evidence, formal, problems) -> int:
    """EV-8's SECOND, structurally different null scan vs
    `structural.na_table` (C22).

    This is CR-1's actual closure at the COUNT level: `na_table` and
    `disclosures.na_conservation` both descend from `ds.na_table`, so
    moving them TOGETHER satisfies every existing check (VF-8, VF-11(d),
    VF-13). EV-8 read `features_table`/`labels_table` through
    `pandas.isna` — a different code path — so it does not move with them.
    The reason-level breakdown still has ONE preimage and stays PARTIAL."""
    obs = evidence.na_observations
    if not obs:
        return 0
    per_field = _get(formal, "structural", "na_table", "per_field")
    if not isinstance(per_field, Mapping):
        problems.append("evidence_na_table_per_field_missing")
        return 0
    population = len([f for f in evidence.day_facts])
    declared_pop = _get(formal, "structural", "na_table", "population")
    if not _strict_equal(declared_pop, population):
        problems.append(
            f"evidence_na_table_population_mismatch:"
            f"{declared_pop!r}!={population!r}")
    compared = 0
    for o in obs:
        row = _get(per_field, o.table, o.column)
        if not isinstance(row, Mapping):
            problems.append(
                f"evidence_na_table_row_missing:{o.table}.{o.column}")
            continue
        compared += 1
        if not _strict_equal(_get(row, "na"), o.n_null):
            problems.append(
                f"evidence_na_count_mismatch:{o.table}.{o.column}.na:"
                f"{_get(row, 'na')!r}!={o.n_null!r}")
        if not _strict_equal(_get(row, "not_na"), o.n_not_null):
            problems.append(
                f"evidence_na_count_mismatch:{o.table}.{o.column}.not_na:"
                f"{_get(row, 'not_na')!r}!={o.n_not_null!r}")
    # and the A11 restatement must agree with the SAME second observation,
    # so moving na_table and na_conservation together no longer works.
    totals = {"features": 0, "labels": 0}
    for o in obs:
        if o.table in totals:
            totals[o.table] += o.n_null
    declared_totals = _get(formal, "disclosures", "na_conservation",
                           "per_table_total_na")
    if isinstance(declared_totals, Mapping):
        for table in ("features", "labels"):
            got = _get(declared_totals, table)
            if got is not None and not _strict_equal(got, totals[table]):
                problems.append(
                    f"evidence_na_conservation_vs_second_observation:{table}:"
                    f"{got!r}!={totals[table]!r}")
    return compared


def _reconcile_day_strata(evidence, problems) -> int:
    """EV-5 is CONSUMED here (it stays permanently PARTIAL on the DR-2 /
    DR-6 vocabulary, but "unruled vocabulary" is not a licence to leave the
    object unread):

      * `tp_fp_class` must agree with EV-1's own theta partition — the two
        are derived from the same `y_cont` and a divergence is a capture
        defect;
      * `stability_epoch` is the CR-4 cross-check the `_epoch_of_year`
        docstring promises: the DATASET half-open string convention vs
        `stability._epoch_of`'s INCLUSIVE INTEGER convention. Four
        implementations of one frozen definition agree today only because
        the boundaries are contiguous integer years; here that is asserted.
      * `micro_execution_era` must equal EV-1's re-derived era.

    The applicable population is the AF1 day population (every EV-1
    trade_date), so an EV-5 emptied — or merely HALVED, which used to be
    just as silent — is refused by the completeness gate. Its DR-2/DR-6
    vocabulary stays permanently PARTIAL; unruled vocabulary is not a
    licence to leave the object unread.
    """
    fact_map = evidence.day_fact_map()
    compared = 0
    covered: set = set()
    for s in evidence.day_strata:
        fact = fact_map.get(s.trade_date)
        if fact is None:
            problems.append(f"evidence_day_stratum_orphan:{s.trade_date}")
            continue
        if s.trade_date not in covered:
            covered.add(s.trade_date)
            compared += 1
        try:
            want_epoch = _stability._epoch_of(int(s.year))
        except Exception:                                # noqa: BLE001
            # D5 (M6.1.4-R2): this used to be swallowed, so a corrupt `year`
            # silently DISABLED the CR-4 cross-convention check for that row.
            problems.append(
                f"evidence_cr4_epoch_unparseable_year:{s.trade_date}:"
                f"{s.year!r}")
            want_epoch = None
        if want_epoch is not None and s.stability_epoch != want_epoch:
            problems.append(
                f"evidence_cr4_epoch_convention_disagreement:{s.trade_date}:"
                f"{s.stability_epoch!r}!={want_epoch!r}")
        if s.micro_execution_era != fact.era:
            problems.append(
                f"evidence_day_stratum_era_mismatch:{s.trade_date}")
        for theta in evidence.thetas:
            tkey = _study.theta_key(theta)
            if not fact.oracle_candidate:
                want = NON_TRADEABLE_CLASS
            else:
                want = (TP_CLASS if float(fact.y_cont) >= float(theta)
                        else FP_CLASS)
            if _get(s.tp_fp_class, tkey) != want:
                problems.append(
                    f"evidence_day_stratum_tp_fp_mismatch:{s.trade_date}:"
                    f"{tkey}")
    for date in sorted(set(fact_map) - covered):
        problems.append(f"evidence_ev5_missing_for_day:{date}")
    return compared


def _reconcile_untradeable(evidence, formal, problems) -> int:
    """MEDIUM C6 — `disclosures.untradeable` rows were never validated at
    all (matrix L119: "no shape, count or vocabulary check whatsoever", and
    it is the ONLY place `y_cont` reaches the sealed payload). Compared
    row-for-row against EV-1's own `untradeable_reason` / `y_cont` /
    `d_open` / era / year, so a FABRICATED disclosure row is refused and a
    SUPPRESSED one is caught by the count."""
    expected = {f.trade_date: f for f in evidence.day_facts
                if f.oracle_candidate and f.untradeable_reason is not None}
    rows = _get(formal, "disclosures", "untradeable")
    if not isinstance(rows, list):
        # the fixture-era `{"note": ...}` shape is not a row list; report it
        # rather than skipping silently.
        if rows is not None:
            problems.append("evidence_untradeable_not_a_list")
        return 0
    seen: set = set()
    for i, row in enumerate(rows):
        if not isinstance(row, Mapping):
            problems.append(f"evidence_untradeable_row_type:{i}")
            continue
        date = _get(row, "trade_date")
        fact = expected.get(date) if isinstance(date, str) else None
        if fact is None:
            problems.append(f"evidence_untradeable_row_fabricated:{date!r}")
            continue
        seen.add(date)
        for field, want in (("year", fact.year), ("era", fact.era),
                            ("d_open", fact.d_open),
                            ("reason", fact.untradeable_reason)):
            if not _strict_equal(_get(row, field), want):
                problems.append(
                    f"evidence_untradeable_row_mismatch:{date}:{field}")
        if not _eq_number_or_none(_get(row, "y_cont"), fact.y_cont):
            problems.append(
                f"evidence_untradeable_row_mismatch:{date}:y_cont")
    for date in sorted(set(expected) - seen):
        problems.append(f"evidence_untradeable_row_suppressed:{date}")
    return 1


def _reconcile_coverage_budgets(evidence, formal, parsed, membership,
                                engines, scenarios, theta_keys,
                                problems) -> int:
    """MEDIUM C5 — `sizing_outputs.<theta>.coverage.<eng>.<scn>.
    by_budget_usd` (L059/L060) is fully AF2-derivable (`count of
    sizing_anchor_usd <= budget`) and had no verifier, so zeroing it
    sealed. Recomputed here from the SEALED rows."""
    compared = 0
    for tkey in theta_keys:
        tp_days = membership.get(tkey, ((), ()))[0]
        for eng in engines:
            for scn in scenarios:
                rows = parsed.get((eng, scn), {})
                anchors = [float(rows[d]["sizing_anchor_usd"])
                           for d in tp_days if d in rows]
                n = len(anchors)
                cov = _get(formal, "sizing_outputs", tkey, "coverage", eng,
                           scn, "by_budget_usd")
                if not isinstance(cov, Mapping):
                    problems.append(
                        f"evidence_coverage_by_budget_missing:"
                        f"{tkey}|{eng}|{scn}")
                    continue
                for budget in _study.RISK_BUDGETS_USD:
                    covered = sum(1 for a in anchors if a <= budget)
                    cell = _get(cov, str(budget))
                    if not isinstance(cell, Mapping):
                        problems.append(
                            f"evidence_coverage_budget_row_missing:"
                            f"{tkey}|{eng}|{scn}:{budget}")
                        continue
                    compared += 1
                    if not _strict_equal(_get(cell, "n_covered"), covered):
                        problems.append(
                            f"evidence_coverage_n_covered_mismatch:"
                            f"{tkey}|{eng}|{scn}:{budget}:"
                            f"{_get(cell, 'n_covered')!r}!={covered!r}")
                    want_fraction = (covered / n) if n else None
                    if not _eq_number_or_none(_get(cell, "fraction"),
                                              want_fraction):
                        problems.append(
                            f"evidence_coverage_fraction_mismatch:"
                            f"{tkey}|{eng}|{scn}:{budget}")
    return compared


# --- comparison helpers -----------------------------------------------------
def _compare_tree(expected, actual, path: str, problems: list,
                  skip_leaf=None) -> None:
    """Structural + leaf comparison of a rebuilt subtree against the formal
    one. Numbers compare with `math.isclose`; everything else exactly."""
    if skip_leaf is not None and skip_leaf(path):
        return
    if isinstance(expected, Mapping):
        if not isinstance(actual, Mapping):
            problems.append(f"evidence_subtree_missing:{path}")
            return
        exp_keys = list(expected)
        act_keys = _report._safe_keys(actual)
        for k in _report._safe_sorted(
                _report._safe_set_diff(exp_keys, act_keys)):
            problems.append(f"evidence_subtree_key_missing:{path}.{k}")
        for k in _report._safe_sorted(
                _report._safe_set_diff(act_keys, exp_keys)):
            problems.append(
                f"evidence_subtree_key_extra:{path}."
                f"{k if isinstance(k, str) else _report._safe_repr(k)}")
        shared = [k for k in exp_keys
                  if not _report._safe_not_in(act_keys, k)]
        for k in _report._safe_sorted(shared):
            _compare_tree(expected[k], _get(actual, k), f"{path}.{k}",
                          problems, skip_leaf)
        return
    if isinstance(expected, (list, tuple)):
        if not isinstance(actual, (list, tuple)):
            problems.append(f"evidence_subtree_not_a_list:{path}")
            return
        if len(expected) != len(actual):
            problems.append(
                f"evidence_subtree_length:{path}:{len(actual)}!="
                f"{len(expected)}")
            return
        for i, (e, a) in enumerate(zip(expected, actual)):
            _compare_tree(e, a, f"{path}[{i}]", problems, skip_leaf)
        return
    # C10b: `!=` accepted `True == 1`. Bool/str/None leaves are compared
    # STRICTLY (type class pinned), so a smuggled 1/0 is a mismatch.
    if expected is None or isinstance(expected, (bool, str)):
        if not _strict_equal(expected, actual):
            problems.append(
                f"evidence_leaf_mismatch:{path}:{actual!r}!={expected!r}")
        return
    if _num(expected):
        if not _close(expected, actual):
            problems.append(
                f"evidence_leaf_mismatch:{path}:{actual!r}!={expected!r}")
        return
    if expected != actual:
        problems.append(f"evidence_leaf_mismatch:{path}")


def _compare_series_block(pairs, block, path, value_key, problems) -> None:
    """One `study._series_block` output vs a series rebuilt from atoms. The
    percentile sub-block is DELIBERATELY excluded (DR-8) and reported as a
    PARTIAL marker instead."""
    if not isinstance(block, Mapping):
        problems.append(f"evidence_series_block_missing:{path}")
        return
    expected = _study._series_block(pairs, value_key)
    # C10b: `n` is a COUNT — `32 == 32.0` and `1 == True` must both fail.
    if not _strict_equal(_get(block, "n"), expected["n"]):
        problems.append(
            f"evidence_series_n:{path}:{_get(block, 'n')!r}!="
            f"{expected['n']!r}")
    got_series = _get(block, value_key)
    if not isinstance(got_series, list):
        problems.append(f"evidence_series_missing:{path}")
    else:
        want = [[d, float(v)] for d, v in pairs]
        if len(got_series) != len(want):
            problems.append(
                f"evidence_series_length:{path}:{len(got_series)}!="
                f"{len(want)}")
        else:
            for i, (g, w) in enumerate(zip(got_series, want)):
                ok = (isinstance(g, (list, tuple)) and len(g) == 2
                      and g[0] == w[0] and _close(g[1], w[1]))
                if not ok:
                    problems.append(
                        f"evidence_series_pair_mismatch:{path}[{i}]:"
                        f"{g!r}!={w!r}")
    for field in ("sum_usd", "mean_usd", "min_usd", "max_usd"):
        if not _eq_number_or_none(_get(block, field), expected[field]):
            problems.append(
                f"evidence_series_{field}:{path}:{_get(block, field)!r}!="
                f"{expected[field]!r}")


def _check_cr6(formal, tkey, eng, scn, problems) -> None:
    """CR-6 — the E2 worst-day P1/P5 pair appears at THREE payload paths and
    `validate_formal_payload` checks P1<=P5 at each independently while
    NEVER checking that the three agree. A tamper on one path is invisible
    today."""
    if eng != "E2":
        return
    a = _get(formal, "oracle_daily", tkey, "executable", "E2", scn, "pooled",
             "worst_day_pnl_percentiles")
    b = _get(formal, "oracle_daily", tkey, "executable", "E2", scn,
             "worst_day_report", "pooled")
    c = _get(formal, "e2_worst_days", tkey, scn, "pooled")
    for name, x, y in (("A2pooled_vs_worstdayreport", a, b),
                       ("worstdayreport_vs_A4", b, c)):
        for pct in ("P1", "P5"):
            xv, yv = _get(x, pct), _get(y, pct)
            if not _eq_number_or_none(xv, yv):
                problems.append(
                    f"evidence_cr6_e2_percentile_disagreement:{tkey}|{scn}:"
                    f"{name}:{pct}:{xv!r}!={yv!r}")
    a_era = _get(formal, "oracle_daily", tkey, "executable", "E2", scn,
                 "by_era")
    b_era = _get(formal, "oracle_daily", tkey, "executable", "E2", scn,
                 "worst_day_report", "by_era")
    c_era = _get(formal, "e2_worst_days", tkey, scn, "by_era")
    for era in (ERA_PROXY, ERA_ACTUAL):
        av = _get(a_era, era, "worst_day_pnl_percentiles")
        for name, other in (("A2byera_vs_worstdayreport", _get(b_era, era)),
                            ("worstdayreport_vs_A4", _get(c_era, era))):
            for pct in ("P1", "P5"):
                if not _eq_number_or_none(_get(av, pct), _get(other, pct)):
                    problems.append(
                        "evidence_cr6_e2_percentile_disagreement:"
                        f"{tkey}|{scn}|{era}:{name}:{pct}")


def _reconcile_stability(evidence, formal, d_tp, membership, fact_map,
                         engines, scenarios, theta_keys, problems) -> int:
    """Recompute the estimator-free stability fields from the BYTES-derived
    D_TP + EV-1 meta. Percentiles (DR-8) and `vol_terciles` (DR-2) are out
    of scope by construction and stay PARTIAL."""
    compared = 0
    for tkey in theta_keys:
        for eng in engines:
            for scn in scenarios:
                pnl = d_tp.get((tkey, eng, scn), {})
                cell = _get(formal, "stability_views", tkey, eng, scn)
                if not isinstance(cell, Mapping):
                    problems.append(
                        f"evidence_stability_cell_missing:{tkey}|{eng}|{scn}")
                    continue
                compared += 1
                epoch_b: dict = {lab: [] for lab in
                                 _stability.ALL_EPOCH_LABELS}
                year_b: dict = {}
                dir_b: dict = {"+1": [], "-1": []}
                for d in sorted(pnl):
                    fact = fact_map.get(d)
                    if fact is None:
                        problems.append(
                            f"evidence_stability_day_meta_missing:"
                            f"{tkey}|{eng}|{scn}:{d}")
                        continue
                    v = float(pnl[d])
                    epoch_b[_stability._epoch_of(int(fact.year))].append((d, v))
                    year_b.setdefault(fact.year, []).append((d, v))
                    dkey = _stability.DIRECTION_KEYS.get(fact.d_open)
                    if dkey is not None:
                        dir_b[dkey].append((d, v))
                for axis, buckets in (("epochs", epoch_b),
                                      ("by_year", year_b),
                                      ("by_direction", dir_b)):
                    for label, pairs in sorted(buckets.items()):
                        _compare_stability_bucket(
                            pairs, _get(cell, axis, label),
                            f"stability_views|{tkey}|{eng}|{scn}|{axis}|"
                            f"{label}", problems)
                loyo_f = _get(cell, "leave_one_year_out")
                for year in sorted(year_b):
                    pairs = [(d, v) for y, rows in year_b.items()
                             if y != year for d, v in rows]
                    _compare_stability_bucket(
                        pairs, _get(loyo_f, year),
                        f"stability_views|{tkey}|{eng}|{scn}|"
                        f"leave_one_year_out|{year}", problems)
    return compared


def _compare_stability_bucket(pairs, bucket, path, problems) -> None:
    if not isinstance(bucket, Mapping):
        problems.append(f"evidence_stability_bucket_missing:{path}")
        return
    expected = _stability._cell(pairs)
    for field in ("n", "n_positive", "n_negative", "n_zero"):
        if _get(bucket, field) != expected[field]:
            problems.append(
                f"evidence_stability_mismatch:{path}.{field}:"
                f"{_get(bucket, field)!r}!={expected[field]!r}")
    for field in ("sum_usd", "mean_usd", "best_day", "worst_day"):
        if not _eq_number_or_none(_get(bucket, field), expected[field]):
            problems.append(
                f"evidence_stability_mismatch:{path}.{field}:"
                f"{_get(bucket, field)!r}!={expected[field]!r}")


def _reconcile_sizing(evidence, formal, parsed, membership, fact_map,
                      engines, scenarios, theta_keys, problems) -> int:
    """A5 rows against AF2 (the parsed BYTES) + EV-3 (the opening-range
    level `planned_stop` never carries for E2) + EV-4 (the cost scenario
    objects that never enter the payload). Includes CR-12.

    Returns how many A5 rows were actually EV-3-anchored: the registry
    sizes the population at theta x engine x scenario x |tp_days|, so an
    EV-3 that covers only some of them is an incompleteness, not a set of
    quietly skipped `stop_level_points` / `stop_distance_points` leaves."""
    anchor = {o.trade_date: o for o in evidence.opening_ranges}
    scn_snap = {s.name: s for s in evidence.cost_scenarios}
    compared = 0
    unanchored: set = set()
    for tkey in theta_keys:
        tp_days = membership[tkey][0]
        for eng in engines:
            for scn in scenarios:
                rows_f = _get(formal, "sizing_outputs", tkey, "rows", eng, scn)
                recs = parsed.get((eng, scn), {})
                if not isinstance(rows_f, list):
                    problems.append(
                        f"evidence_sizing_rows_missing:{tkey}|{eng}|{scn}")
                    continue
                if len(rows_f) != len(tp_days):
                    problems.append(
                        f"evidence_sizing_row_count:{tkey}|{eng}|{scn}:"
                        f"{len(rows_f)}!={len(tp_days)}")
                # CR-3(c): coverage.n_trades is a FOURTH reducer of the same
                # partition size and floats free today.
                n_trades = _get(formal, "sizing_outputs", tkey, "coverage",
                                eng, scn, "n_trades")
                if n_trades != len(tp_days):
                    problems.append(
                        f"evidence_cr3_coverage_n_trades:{tkey}|{eng}|{scn}:"
                        f"{n_trades}!={len(tp_days)}")
                snapshot = scn_snap.get(scn)
                for i, row in enumerate(rows_f):
                    if not isinstance(row, Mapping):
                        problems.append(
                            f"evidence_sizing_row_type:{tkey}|{eng}|{scn}:{i}")
                        continue
                    date = _get(row, "trade_date")
                    rec = recs.get(date) if isinstance(date, str) else None
                    if rec is None:
                        problems.append(
                            f"evidence_sizing_row_no_record:"
                            f"{tkey}|{eng}|{scn}:{i}:{date!r}")
                        continue
                    fact = fact_map.get(date)
                    orf = anchor.get(date)
                    path = f"sizing_outputs|{tkey}|{eng}|{scn}|{date}"
                    for field, want in (("engine", eng),
                                        ("cost_scenario", scn),
                                        ("direction", rec["direction"]),
                                        ("stop_triggered",
                                         rec["stop_triggered"]),
                                        ("counterfactual_anchor", eng == "E2")):
                        if _get(row, field) != want:
                            problems.append(
                                f"evidence_sizing_field:{path}.{field}")
                    if fact is not None:
                        for field, want in (("era", fact.era),
                                            ("year", fact.year)):
                            if _get(row, field) != want:
                                problems.append(
                                    f"evidence_sizing_field:{path}.{field}")
                    planned = float(rec["sizing_anchor_usd"])
                    if not _close(_get(row, "risk_usd_per_1_MNQ_planned"),
                                  planned):
                        problems.append(
                            f"evidence_sizing_field:{path}."
                            "risk_usd_per_1_MNQ_planned")
                    # CR-12 — two leaves, one value, identity NEVER asserted.
                    if not _eq_number_or_none(
                            _get(row, "minimum_1_contract_risk"),
                            _get(row, "risk_usd_per_1_MNQ_planned")):
                        problems.append(
                            f"evidence_cr12_minimum_risk_identity:{path}")
                    realized_want = (-float(rec["final_pnl_per_contract"])
                                     if (eng == "E1" and rec["stop_triggered"])
                                     else None)
                    if not _eq_number_or_none(
                            _get(row, "risk_usd_per_1_MNQ_realized"),
                            realized_want):
                        problems.append(
                            f"evidence_sizing_field:{path}."
                            "risk_usd_per_1_MNQ_realized")
                    if orf is None:
                        if date not in unanchored:
                            unanchored.add(date)
                            problems.append(
                                "evidence_ev3_sizing_row_not_anchored:"
                                f"{date}")
                    else:
                        compared += 1
                        if not _close(_get(row, "stop_level_points"),
                                      orf.anchor_stop):
                            problems.append(
                                f"evidence_sizing_field:{path}."
                                "stop_level_points")
                        if not _close(_get(row, "stop_distance_points"),
                                      abs(float(rec["entry_fill"])
                                          - orf.anchor_stop)):
                            problems.append(
                                f"evidence_sizing_field:{path}."
                                "stop_distance_points")
                        # E1's sealed `planned_stop` must equal EV-3's level;
                        # E2 stores None, which is exactly the EV-3 gap.
                        if eng == "E1" and rec["planned_stop"] is not None:
                            if not _close(rec["planned_stop"],
                                          orf.anchor_stop):
                                problems.append(
                                    f"evidence_e1_planned_stop_vs_ev3:{path}")
                    if snapshot is not None:
                        want_cost = _cost_usd(snapshot,
                                              bool(rec["stop_triggered"]))
                        if not _close(_get(row, "cost_usd_per_1_MNQ"),
                                      want_cost):
                            problems.append(
                                f"evidence_sizing_field:{path}."
                                "cost_usd_per_1_MNQ")
                        want_pct = (None if planned <= 0.0
                                    else want_cost / planned)
                        if not _eq_number_or_none(_get(row, "cost_as_pct_of_R"),
                                                  want_pct):
                            problems.append(
                                f"evidence_sizing_field:{path}."
                                "cost_as_pct_of_R")
    return compared


# USD magnitude ceiling for a single MNQ contract's per-day leaves. Not a
# research bound: a purely STRUCTURAL sanity rail (the frozen §3 session is
# one RTH day of one micro contract, so 1e9 USD is ~7 orders of magnitude of
# headroom). It exists because C29 showed 1e308 / 10**16+1 / 5e-324 sealing
# as "finite numbers" — `math.isfinite` alone is not a range check.
_USD_LEAF_ABS_MAX = 1e9
_SCALAR_USD_FIELDS = ("entry_fill", "exit_fill", "final_pnl_per_contract",
                      "max_adverse_pnl", "max_favourable_pnl",
                      "sizing_anchor_usd")


def _strict_equal(a, b) -> bool:
    """Value equality that also pins the TYPE class, so `True == 1` and
    `32 == 32.0` are NOT accepted as equal (C10b). Floats compare with
    `math.isclose`; bool/int/str/None compare exactly and by type."""
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a is b
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, int) and isinstance(b, int):
        return a == b
    if isinstance(a, float) and isinstance(b, float):
        return _num(a) and _num(b) and math.isclose(
            float(a), float(b), rel_tol=1e-12, abs_tol=1e-12)
    if isinstance(a, (int, float)) or isinstance(b, (int, float)):
        # a NUMBER against a non-number, or an int against a float: both are
        # type drift (C10b — `32 == 32.0` used to pass).
        return False
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return (len(a) == len(b)
                and all(_strict_equal(x, y) for x, y in zip(a, b)))
    return type(a) is type(b) and a == b


def _reconcile_record_fields(evidence, parsed, problems) -> int:
    """HIGH-1 — bind the PARSED sealed rows to `evidence.record_fields`
    FIELD-FOR-FIELD.

    `record_fields` freezes every serialized field of every
    `TradePathRecord` at COMPUTE time, before any byte exists on disk. This
    one invariant is what kills the whole post-capture byte-tamper family
    the PHASE-E audit demonstrated, each of which had previously sealed
    because the downstream aggregates were repaired to match:

      C32  a P&L-PRESERVING shift (entry_fill += 3.25, exit_fill += 3.25,
           sizing_anchor_usd repaired, the A5 rows repaired) — every
           derived quantity still reconciled;
      C1   an FP-day exit_fill + final_pnl rewrite across all eight JSONL
           with the grid mixture repaired — FP days are OUTSIDE the
           TP-only EV-7 digest support, so nothing else covered them;
      C7   `mtm_*` arrays rewritten with `max_adverse_pnl = min(...)`
           repaired and `max_favourable_pnl = 12345`;
      C8   `exit_timestamp` before `entry_timestamp`;
      C29  `max_favourable_pnl := 1e308 / -0.0 / 5e-324 / 10**16+1`.

    Comparison is STRICT-typed (`_strict_equal`), so a float smuggled in
    where the record held an int — or `True` where it held `1` — is a
    mismatch, not a pass.
    """
    compared = 0
    for (eng, scn), rows in sorted(parsed.items()):
        key = f"{eng}|{scn}"
        captured = _get(evidence.record_fields, key)
        fname = f"{_MC_FILE_RE_PREFIX}{eng}_{scn}.jsonl"
        if not isinstance(captured, Mapping):
            problems.append(f"evidence_record_fields_absent:{key}")
            continue
        cap_dates, got_dates = set(captured), set(rows)
        for d in sorted(cap_dates - got_dates):
            problems.append(f"evidence_record_fields_missing_row:{fname}:{d}")
        for d in sorted(got_dates - cap_dates):
            problems.append(f"evidence_record_fields_extra_row:{fname}:{d}")
        for d in sorted(cap_dates & got_dates):
            want, got = captured[d], rows[d]
            compared += 1
            for field in _report.FORMAL_RECORD_FIELDS:
                if not _strict_equal(_get(want, field), got.get(field)):
                    problems.append(
                        f"evidence_record_fields_mismatch:{fname}:{d}:{field}")
    return compared


def _reconcile_record_pnl(evidence, parsed, problems) -> int:
    """`record_pnl` is the P&L projection of the same AF2 atoms EV-7
    digests. Binding it explicitly means the field is CONSUMED and that a
    capture-side inconsistency between the two projections is visible.

    M6.1.4-ARCH: this used to be the quietest hole of all. The `ran` flag
    lived INSIDE the date-intersection loop and no marker was registered
    for the field, so `record_pnl` with all eight (engine|scenario) keys
    present and every inner row dict EMPTIED produced zero problems, zero
    markers and byte-identical sealed files. The population is now the
    parsed sealed rows and a missing row is named."""
    compared = 0
    for (eng, scn), rows in sorted(parsed.items()):
        key = f"{eng}|{scn}"
        captured = _get(evidence.record_pnl, key)
        if not isinstance(captured, Mapping):
            problems.append(f"evidence_record_pnl_absent:{key}")
            continue
        for d in sorted(set(rows) - set(captured)):
            problems.append(f"evidence_record_pnl_missing_row:{key}:{d}")
        # ...and the other direction, which was measured SILENT: a captured
        # date with no sealed row at all.
        for d in _report._safe_sorted(set(captured) - set(rows)):
            problems.append(f"evidence_record_pnl_extra_row:{key}:{d}")
        for d in sorted(set(captured) & set(rows)):
            compared += 1
            if not _strict_equal(captured[d],
                                 rows[d].get("final_pnl_per_contract")):
                problems.append(
                    f"evidence_record_pnl_mismatch:{eng}|{scn}:{d}")
    return compared


def _reconcile_record_ranges(evidence, parsed, problems) -> int:
    """Line-internal STRUCTURAL rails that double as capture-side guards
    (C7 / C8 / C29): timestamp ordering, a USD magnitude ceiling on every
    numeric leaf, and the two mark-array invariants that hold by
    construction in `paths.build_record`
    (`max_adverse == min(mtm_adverse)`, `max_favourable >=
    max(mtm_close)`)."""
    compared = 0
    for (eng, scn), rows in sorted(parsed.items()):
        fname = f"{_MC_FILE_RE_PREFIX}{eng}_{scn}.jsonl"
        for d in sorted(rows):
            row = rows[d]
            compared += 1
            entry_ts, exit_ts = row.get("entry_timestamp"), \
                row.get("exit_timestamp")
            if (isinstance(entry_ts, str) and isinstance(exit_ts, str)
                    and exit_ts < entry_ts):
                problems.append(
                    f"evidence_record_timestamp_order:{fname}:{d}:"
                    f"{entry_ts}>{exit_ts}")
            for field in _SCALAR_USD_FIELDS:
                v = row.get(field)
                if _num(v) and abs(float(v)) > _USD_LEAF_ABS_MAX:
                    problems.append(
                        f"evidence_record_value_out_of_range:{fname}:{d}:"
                        f"{field}:{v!r}")
            for field in ("mtm_close_pnl_1m", "mtm_adverse_pnl_1m"):
                seq = row.get(field)
                if isinstance(seq, list) and any(
                        _num(x) and abs(float(x)) > _USD_LEAF_ABS_MAX
                        for x in seq):
                    problems.append(
                        f"evidence_record_value_out_of_range:{fname}:{d}:"
                        f"{field}")
            closes = row.get("mtm_close_pnl_1m")
            fav = row.get("max_favourable_pnl")
            if (isinstance(closes, list) and closes
                    and all(_num(x) for x in closes) and _num(fav)
                    and float(fav) < max(float(x) for x in closes) - 1e-9):
                problems.append(
                    f"evidence_record_max_favourable_below_close_path:"
                    f"{fname}:{d}")
    return compared


def _reconcile_entry_fill_vs_ev2(evidence, parsed, problems) -> int:
    """The ONE fill with a captured bar preimage: the entry reference price.

    `EV-2.entry_ref_price` is the 10:00 bar OPEN re-read from the frame at
    capture time, and `costs.scenario_entry_fill` is a pure function of it
    and the EV-4 snapshot — so for every day EV-2 covers (the theoretical
    union, i.e. the TP days across both frozen thetas) the sealed
    `entry_fill` is checkable against a bar-derived quantity under EVERY
    scenario, not just Base.

    It does NOT cover exit fills, and it does NOT cover entry fills on
    FP-only days (EV-2 is built on the TP union). That residue is the
    permanent `PARTIAL:records.executable_fills:` marker."""
    ref_of = {p.trade_date: p.entry_ref_price
              for p in evidence.theoretical_paths}
    dir_of = {f.trade_date: f.d_open for f in evidence.day_facts}
    snaps = {s.name: s for s in evidence.cost_scenarios}
    compared = 0
    for (eng, scn), rows in sorted(parsed.items()):
        snapshot = snaps.get(scn)
        if snapshot is None:
            continue
        fname = f"{_MC_FILE_RE_PREFIX}{eng}_{scn}.jsonl"
        for d in sorted(rows):
            ref = ref_of.get(d)
            direction = dir_of.get(d)
            if ref is None or direction not in (1, -1):
                continue
            compared += 1
            want = _costs.entry_fill(
                float(ref), int(direction),
                snapshot.friction_multiplier * snapshot.spread_points,
                snapshot.friction_multiplier
                * snapshot.slippage_ticks_per_side)
            if not _close(rows[d].get("entry_fill"), want):
                problems.append(
                    f"evidence_record_entry_fill_vs_ev2:{fname}:{d}:"
                    f"{rows[d].get('entry_fill')!r}!={want!r}")
    return compared


def _reconcile_record_internals(evidence, parsed, problems) -> int:
    """The recomputes matrix Table 14 says NOTHING performs today:

      * L132 — `final_pnl_per_contract` is "the single most-consumed atom,
        with zero internal recompute": `d*(exit_fill - entry_fill)*
        MNQ_POINT_VALUE_USD - platform_fee` uses three fields that sit on
        the SAME sealed line plus EV-4's fee, and is never checked;
      * L134 — `max_adverse_pnl` is trivially `min(mtm_adverse_pnl_1m)` on
        the same line and is never checked against it;
      * L137 — `sizing_anchor_usd` (which MC divides its risk budget by) is
        `paths.sizing_anchor_usd(entry_fill, planned_stop, d, scn)`; for E2
        the stop level reaches no sealed artifact at all, so this recompute
        REQUIRES EV-3.

    CORRECTION (M6.1.4-ARCH, finding F-2). An earlier version of this
    docstring said the L137 recompute "is what makes a synchronized
    bytes+payload rewrite detectable". That was FALSE as written: the
    recompute was reached through `anchor.get(date)` and an EV-3 that did
    not cover the date — including a WHOLLY EMPTY EV-3, and equally an EV-3
    stripped to a single row — skipped it silently, with no `ran` flag, no
    marker and no problem. The claim is now true only because the
    applicable population (the sealed-record universe, derived from EV-1)
    is enforced by the registry: an uncovered date is named here and the
    completeness gate refuses the seal. The wording is deliberately narrow
    — this reaches POST-CAPTURE rewrites only; a producer poisoned BEFORE
    compute poisons capture and seal together and stays disclosed as
    `PARTIAL:records.executable_fills:`.
    """
    anchor = {o.trade_date: o for o in evidence.opening_ranges}
    snaps = {s.name: s for s in evidence.cost_scenarios}
    compared = 0
    missing_ev3: set = set()
    for (eng, scn), rows in sorted(parsed.items()):
        snapshot = snaps.get(scn)
        if snapshot is None:
            problems.append(f"evidence_cost_snapshot_missing:{scn}")
            continue
        fee = float(snapshot.platform_fee_rt_usd)
        for date in sorted(rows):
            row = rows[date]
            d = int(row["direction"])
            path = f"record|{eng}|{scn}|{date}"
            want_final = (d * (float(row["exit_fill"])
                               - float(row["entry_fill"]))
                          * MNQ_POINT_VALUE_USD - fee)
            if not _close(row["final_pnl_per_contract"], want_final):
                problems.append(
                    f"evidence_record_final_pnl_recompute:{path}:"
                    f"{row['final_pnl_per_contract']!r}!={want_final!r}")
            adverse = row["mtm_adverse_pnl_1m"]
            if isinstance(adverse, list) and adverse:
                if not _close(row["max_adverse_pnl"], min(adverse)):
                    problems.append(
                        f"evidence_record_max_adverse_recompute:{path}")
            orf = anchor.get(date)
            if orf is None:
                # F-2: this `continue` used to be the whole defect — the
                # ONE recompute that requires EV-3 vanished without a word.
                if date not in missing_ev3:
                    missing_ev3.add(date)
                    problems.append(
                        f"evidence_ev3_missing_for_applicable_day:{date}")
                continue
            compared += 1
            side_adverse = snapshot.friction_multiplier * (
                snapshot.spread_points / 2.0
                + snapshot.adverse_slippage_ticks * _MNQ_TICK_POINTS)
            normal_stop_px = orf.anchor_stop - d * side_adverse
            want_anchor = (d * (float(row["entry_fill"]) - normal_stop_px)
                           * MNQ_POINT_VALUE_USD + fee)
            if not _close(row["sizing_anchor_usd"], want_anchor):
                problems.append(
                    f"evidence_record_sizing_anchor_recompute:{path}:"
                    f"{row['sizing_anchor_usd']!r}!={want_anchor!r}")
    return compared


def _cost_usd(snapshot, stop_exit: bool) -> float:
    """`costs.round_turn_cost_usd` recomputed from the EV-4 SNAPSHOT (the
    four `CostScenarioParams` objects never enter the payload — matrix
    L053/EV-4), not from a live scenario object."""
    def side(adverse: bool) -> float:
        ticks = (snapshot.adverse_slippage_ticks if adverse
                 else snapshot.slippage_ticks_per_side)
        return snapshot.friction_multiplier * (
            snapshot.spread_points / 2.0 + ticks * _MNQ_TICK_POINTS)

    return ((side(False) + side(stop_exit)) * MNQ_POINT_VALUE_USD
            + snapshot.platform_fee_rt_usd)


def _reconcile_bootstrap(evidence, formal, d_tp, membership, problems) -> int:
    """A7 input series vs the EV-7 DIGEST, plus CR-2.

    M6.1.4-ARCH (F-2): the cell loop iterates `by_cell`, so an EMPTY EV-7
    made every digest binding AND the CR-2 comparison vanish without a
    word, and a SINGLE surviving cell was just as silent. The A7 cell
    product (theta x engine x scenario x block) is now the applicable
    population and is checked against EV-7 itself, not only against the
    payload's own key set."""
    by_cell = {f.cell_key: f for f in evidence.bootstrap_inputs}
    cells_f = _get(formal, "bootstrap_ci")
    # DR-4 (Aaron 2026-08-10): the published per-seed mean is the RULED
    # population statistic — full eligible trading-day sequence, oracle days
    # carrying P&L, eligible-but-unselected days zero-filled, NA days
    # (undeterminable direction / Y_cont NA) dropped n1-style. Zero-filled
    # days add nothing to the sum, so the independent expectation is
    # series_sum / n_ruled, with n_ruled REBUILT here from EV-1 day facts
    # (theta-independent by construction: the NA predicate does not read
    # theta). The TP-only series mean stays what the ORACLE pooled mean is
    # compared against — the two are different statistics under the ruling.
    _n_eligible = 0
    _n_ruled = 0
    for _f in evidence.day_facts:
        _n_eligible += 1
        _y = getattr(_f, "y_cont", None)
        _d = getattr(_f, "d_open", 0)
        if _y is not None and int(_d or 0) != 0:
            _n_ruled += 1
    _n_na_dropped = _n_eligible - _n_ruled
    # The frozen §9 block axis is EV-7's own; a cell whose block_len is not
    # on it (or a payload whose A7 key set does not cover the full
    # theta x engine x scenario x block product) is refused here rather
    # than left to the payload-internal key-set rule alone.
    allowed_blocks = {int(b) for b in evidence.blocks}
    expected_cells = {
        f"{_study.theta_key(t)}|{eng}|{scn}|block{blk}"
        for t in evidence.thetas for eng in evidence.engines
        for scn in evidence.scenarios for blk in evidence.blocks}
    for key in sorted(by_cell):
        if int(by_cell[key].block_len) not in allowed_blocks:
            problems.append(
                f"evidence_bootstrap_block_axis:{key}:"
                f"{by_cell[key].block_len}")
    if isinstance(cells_f, Mapping):
        got = set(_report._safe_keys(cells_f))
        for key in sorted(expected_cells - got):
            problems.append(f"evidence_bootstrap_cell_absent:{key}")
    # ...and the SAME product against EV-7 itself (the F-2 hole).
    for key in sorted(expected_cells - set(by_cell)):
        problems.append(f"evidence_ev7_cell_absent:{key}")
    compared = 0
    for key in sorted(by_cell):
        fact = by_cell[key]
        if key in expected_cells:
            compared += 1
        pnl = d_tp.get((fact.theta_key, fact.engine, fact.scenario), {})
        tp_days = membership.get(fact.theta_key, ((), ()))[0]
        ordered = [(d, float(pnl[d])) for d in sorted(tp_days) if d in pnl]
        digest = _series_digest(ordered)
        if digest != fact.series_sha256:
            problems.append(
                f"evidence_bootstrap_series_digest_mismatch:{key}")
        cell = _get(cells_f, key)
        if not isinstance(cell, Mapping):
            problems.append(f"evidence_bootstrap_cell_missing:{key}")
            continue
        # CR-2 — three implementations of ONE statistic, never compared.
        if not _eq_number_or_none(fact.series_mean_sum_over_n,
                                  fact.series_mean_numpy):
            problems.append(
                f"evidence_cr2_mean_reducer_disagreement:{key}:"
                f"{fact.series_mean_sum_over_n!r}!="
                f"{fact.series_mean_numpy!r}")
        pooled_mean = _get(formal, "oracle_daily", fact.theta_key,
                           "executable", fact.engine, fact.scenario, "pooled",
                           "mean_usd")
        if not _eq_number_or_none(pooled_mean, fact.series_mean_sum_over_n):
            problems.append(
                f"evidence_cr2_oracle_mean_vs_series:{key}:"
                f"{pooled_mean!r}!={fact.series_mean_sum_over_n!r}")
        # DR-4 ruled-sequence accounting published on the cell must agree
        # with the EV-1-rebuilt counts and the TP-series facts.
        ruled_mean = ((fact.series_sum / _n_ruled)
                      if _n_ruled else None)
        for pub_key, want in (("n_days_in_sequence", _n_ruled),
                              ("n_oracle_traded_days", fact.n),
                              ("n_na_days_dropped", _n_na_dropped)):
            got = _get(cell, pub_key)
            if got != want:
                problems.append(
                    f"evidence_dr4_sequence_count:{key}:{pub_key}:"
                    f"{got!r}!={want!r}")
        per_seed = _get(cell, "per_seed")
        for seed in fact.seeds:
            entry = _get(per_seed, str(seed))
            if entry is None:
                entry = _get(per_seed, seed)
            if not isinstance(entry, Mapping):
                problems.append(f"evidence_bootstrap_seed_missing:{key}:{seed}")
                continue
            if not _eq_number_or_none(_get(entry, "mean"), ruled_mean):
                problems.append(
                    f"evidence_cr2_bootstrap_mean_vs_series:{key}:{seed}:"
                    f"{_get(entry, 'mean')!r}!={ruled_mean!r}")
            if _get(entry, "n_boot") != fact.n_boot:
                problems.append(f"evidence_bootstrap_n_boot:{key}:{seed}")
            if _get(entry, "block_len") != fact.block_len:
                problems.append(f"evidence_bootstrap_block_len:{key}:{seed}")
    return compared


def _reconcile_grid_draws(cell, tp_set, fp_set, rows, cell_id,
                          problems) -> None:
    """M6.1.4 fix-round (PHASE D class 4 / CR-8): anchor every per-seed
    DRAW to independent preimages. A drawn date must be a MEMBER of the
    evidence partition (an out-of-universe or cross-class date is refused
    regardless of how consistently the totals were repaired); the counts,
    realized ratios, day_markers and allocations must be arithmetic
    restatements of the draw; and mixture_mean_pnl must equal the mean of
    the PARSED sealed-byte P&L over exactly the drawn dates. Never raises."""
    grid_pts = cell.get("grid") if isinstance(cell, Mapping) else None
    if not isinstance(grid_pts, Mapping):
        problems.append(f"evidence_grid_points_missing:{cell_id}")
        return
    for pkey in sorted(grid_pts, key=str):
        point = grid_pts[pkey]
        if not isinstance(point, Mapping):
            continue                    # shape is the report validator's job
        per_seed = point.get("per_seed")
        if not isinstance(per_seed, Mapping):
            continue
        for skey in sorted(per_seed, key=str):
            rowd = per_seed[skey]
            if not isinstance(rowd, Mapping):
                continue
            loc = f"{cell_id}:{pkey}:{skey}"
            tpd = rowd.get("tp_dates")
            fpd = rowd.get("fp_dates")
            if (not isinstance(tpd, (list, tuple))
                    or not isinstance(fpd, (list, tuple))):
                problems.append(f"evidence_grid_draw_shape:{loc}")
                continue
            try:
                bad_tp = sorted(str(d) for d in tpd if d not in tp_set)
                bad_fp = sorted(str(d) for d in fpd if d not in fp_set)
            except Exception:
                problems.append(f"evidence_grid_draw_shape:{loc}")
                continue
            if bad_tp:
                problems.append(
                    f"evidence_grid_draw_membership_tp:{loc}:{bad_tp[:3]}")
            if bad_fp:
                problems.append(
                    f"evidence_grid_draw_membership_fp:{loc}:{bad_fp[:3]}")
            if len(set(tpd)) != len(tpd) or len(set(fpd)) != len(fpd):
                problems.append(f"evidence_grid_draw_duplicates:{loc}")
            if set(tpd) & set(fpd):
                problems.append(f"evidence_grid_draw_overlap:{loc}")
            if rowd.get("n_tp_actual") != len(tpd):
                problems.append(f"evidence_grid_draw_n_tp_actual:{loc}")
            if rowd.get("n_fp_actual") != len(fpd):
                problems.append(f"evidence_grid_draw_n_fp_actual:{loc}")
            marks = rowd.get("day_markers")
            want_marks = sorted([[str(d), "tp"] for d in tpd]
                                + [[str(d), "fp"] for d in fpd])
            try:
                got_marks = (sorted([list(m) for m in marks])
                             if isinstance(marks, (list, tuple)) else None)
            except Exception:
                got_marks = None
            if got_marks != want_marks:
                problems.append(f"evidence_grid_draw_markers:{loc}")
            n_tot = len(tpd) + len(fpd)
            want_prec = (len(tpd) / n_tot) if n_tot else None
            if rowd.get("realized_precision") != want_prec:
                problems.append(
                    f"evidence_grid_draw_realized_precision:{loc}")
            if tp_set and rowd.get("realized_recall") != len(tpd) / len(tp_set):
                problems.append(f"evidence_grid_draw_realized_recall:{loc}")
            for aname, drawn_n in (("allocation_tp", len(tpd)),
                                   ("allocation_fp", len(fpd))):
                alloc = rowd.get(aname)
                if isinstance(alloc, Mapping):
                    try:
                        total = sum(v for v in alloc.values()
                                    if isinstance(v, int)
                                    and not isinstance(v, bool))
                    except Exception:
                        total = None
                    if total != drawn_n:
                        problems.append(
                            f"evidence_grid_draw_{aname}:{loc}")
            drawn = [str(d) for d in tpd] + [str(d) for d in fpd]
            missing = sorted(d for d in drawn
                             if not isinstance(rows.get(d), Mapping))
            if missing:
                problems.append(
                    f"evidence_grid_draw_pnl_rows_missing:{loc}:"
                    f"{missing[:3]}")
            elif drawn:
                try:
                    import numpy as _np
                    want_mix = float(_np.mean(
                        [float(rows[d]["final_pnl_per_contract"])
                         for d in drawn]))
                except Exception:
                    want_mix = None
                got_mix = rowd.get("mixture_mean_pnl")
                ok = (want_mix is not None
                      and isinstance(got_mix, float)
                      and not isinstance(got_mix, bool)
                      and abs(got_mix - want_mix) <= 1e-9)
                if not ok:
                    problems.append(
                        f"evidence_grid_draw_mixture_mean:{loc}:"
                        f"{got_mix!r}!={want_mix!r}")


def _reconcile_grid(evidence, formal, parsed, membership, engines, scenarios,
                    theta_keys, problems) -> int:
    """A8 availability vs the EV-6 pools, and CR-3's four-way identity."""
    pools = {(g.theta_key, g.engine, g.scenario): g
             for g in evidence.grid_pools}
    compared = 0
    for tkey in theta_keys:
        tp_days, fp_days = membership[tkey]
        for eng in engines:
            for scn in scenarios:
                cell = _get(formal, "feasibility_grid", "cells",
                            f"{tkey}|{eng}|{scn}")
                pool = pools.get((tkey, eng, scn))
                if pool is None:
                    problems.append(
                        f"evidence_grid_pool_missing:{tkey}|{eng}|{scn}")
                    continue
                compared += 1
                if sum(pool.tp_avail.values()) != len(tp_days):
                    problems.append(
                        f"evidence_grid_pool_tp_sum:{tkey}|{eng}|{scn}")
                if sum(pool.fp_avail.values()) != len(fp_days):
                    problems.append(
                        f"evidence_grid_pool_fp_sum:{tkey}|{eng}|{scn}")
                if not isinstance(cell, Mapping):
                    problems.append(
                        f"evidence_grid_cell_missing:{tkey}|{eng}|{scn}")
                    continue
                # CR-3 (b): the grid's own availability figures are the
                # basis VF-7 TRUSTS for n_tp_target and are never compared
                # against the theta partition anywhere today.
                if _get(cell, "n_tp_available") != len(tp_days):
                    problems.append(
                        f"evidence_cr3_grid_n_tp_available:{tkey}|{eng}|{scn}:"
                        f"{_get(cell, 'n_tp_available')}!={len(tp_days)}")
                if _get(cell, "n_fp_available") != len(fp_days):
                    problems.append(
                        f"evidence_cr3_grid_n_fp_available:{tkey}|{eng}|{scn}:"
                        f"{_get(cell, 'n_fp_available')}!={len(fp_days)}")
                # CR-3 (d): manifest counts == n_tp + n_fp, measured against
                # the ACTUAL parsed line population, not the payload's own
                # day_universe.
                n_records = len(parsed.get((eng, scn), {}))
                if n_records != len(tp_days) + len(fp_days):
                    problems.append(
                        f"evidence_cr3_records_vs_partition:"
                        f"{tkey}|{eng}|{scn}:{n_records}!="
                        f"{len(tp_days) + len(fp_days)}")
                # M6.1.4 fix-round (PHASE D class 4 / CR-8): the DRAW
                # CONTENTS of every per-seed selection are anchored —
                # membership against the EV-1 partition, arithmetic
                # identities, marker/selection agreement, and the mixture
                # mean re-derived from the PARSED sealed bytes. Only the
                # RNG replay itself (WHICH member dates the stream draws)
                # stays PARTIAL while DR-2/3/6 pend.
                _reconcile_grid_draws(
                    cell, set(tp_days), set(fp_days),
                    parsed.get((eng, scn), {}),
                    f"{tkey}|{eng}|{scn}", problems)
    return compared


__all__ = [
    "SCHEMA_VERSION", "FROZEN_BLOCKS", "PARTIAL_PREFIX",
    "CheckOutcome", "CheckSpec", "FieldDisposition", "ProvKeySpec",
    "CHECK_REGISTRY", "FIELD_REGISTRY", "PROVENANCE_REGISTRY",
    "PERMANENT_MARKERS", "reconcile_outcomes",
    "LeafSpec", "LeafOutcome", "EntityAxisAuthority", "LEAF_REGISTRY",
    "ENTITY_AXIS_AUTHORITIES", "KEY_VOCAB_AXES", "entity_axes_for",
    "reconcile_leaf_outcomes", "GRID_STRATUM_AXES",
    "NA_OBSERVATION_METHOD_ID",
    "INDEPENDENT_BOUND", "DERIVED_REDUNDANT", "DISCLOSURE_UNVERIFIED",
    "DR_PARTIAL", "AUTHORITATIVE_NOT_APPLICABLE", "REMOVE_UNUSED",
    "REQUIRED_COMPARED", "CONDITIONAL", "EXPLICIT_PARTIAL", "PURE_METADATA",
    "EXPLICIT_NOT_APPLICABLE",
    "CanonicalDayFact", "TheoreticalPathRecord", "OpeningRangeFact",
    "CostScenarioSnapshot", "DayStratumFact", "GridPoolFact",
    "BootstrapInputFact", "NAObservationFact", "FunnelFact",
    "F10MembershipFact", "LabelAvailabilityFact", "EstimatorIdentityFact",
    "FrozenHashObservationFact", "CanonicalS0Evidence",
    "capture_evidence", "reducers", "reconcile_with_evidence",
    "split_problems", "freeze", "to_plain",
    "rebuild_structural_eras", "rebuild_structural_groups",
    "rebuild_era_axis_axes", "rebuild_day_universe", "rebuild_frequency",
    "rebuild_theoretical_oracle",
]
