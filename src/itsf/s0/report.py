"""S0 formal-report boundary (M6.1 Track E2+E3).

Scope: this module owns exactly the pieces the formal S0 report needs
before Stage E may seal anything (S0_REPORT_CONTENT_CONTRACT.md;
M6_HOLD_RESPONSE.md items 2 and 10):

  1. `record_to_formal_dict` / `to_formal_json` — the FROZEN §10.1 atomic-
     record serialization and a hard-failing (never silently-stringifying)
     JSON encoder for the sealed release.
  2. `split_envelope` — the internal/formal payload split (M6_HOLD_RESPONSE
     item 2's "oracle_daily -> study drift" defect: the formal side is
     keyed EXACTLY by the contract's A-keys at the top level, nothing lives
     one level down inside a "study" wrapper, and no live object — dataset,
     TradePathRecord, DataFrame, ... — may cross into it).
  3. `validate_formal_payload` / `validate_sealed_files` — the machine gate
     S0_REPORT_CONTENT_CONTRACT.md §B describes; ANY problem in the
     returned list means Stage E must refuse to seal (fail-closed).

M6.1.1-S1 hardening (Codex M6.1 seal-boundary findings): the exact theta
axis {0.5, 0.3}; A2 day_universe conservation flags (literally True, no
exceptions); the A2 executable E1/E2 x 4-scenario matrix UNCONDITIONALLY
(no longer gated on mc_handoff_manifest); the A1 structural sub-keys
(funnel/F10 dual report/na_table/label_anchor_availability/eras/groups);
required-field completeness for frequency/sizing_outputs/stability_views/
feasibility_grid against their REAL src/itsf/s0 producer shapes; a
disclosures.pending_method_decisions key that must EXIST (missing is a
problem distinct from non-empty); and a `governance` CONTEXT cross-check
(`expected_governance`) that a formal payload's embedded governance block
must match EXACTLY — omitting it is itself a sealing-blocking problem.
`validate_sealed_files` gained the matching hardening for the manifest
file-key set, a triple count equality, per-line engine/cost_scenario
identity, per-file trade_date uniqueness, and an EXACT per-file
trade_date-set match against the payload's own day universe. See
`validate_formal_payload`'s docstring for the mandatory TWO-CALL contract
the Stage-E renderer must follow (pre- and post-manifest-injection).

M6.1.2-S1 hardening (Codex M6.1.1 FAIL/HOLD finding: the validator checked
key presence and non-empty dicts but not real producer-shape CONTENT, so a
structurally-plausible but semantically-garbage payload could seal):
LEAF-LEVEL value-type checks (numbers int/float and finite, date strings
matching `YYYY-MM-DD`, lists actually lists) layered on top of every
existing field-set-completeness rule, never replacing "key exists" with
"key exists and is well-typed"; A2 day_universe hard invariants (n_tp/n_fp
COUNT identity against tp_days/fp_days, no duplicate day in either list, the
TP/FP partition disjoint, and the tp∪fp union IDENTICAL across both frozen
thetas); A2's executable matrix now validated against the REAL study.py
`_series_block`/`_by_era_and_pooled` shape (pooled + both eras + the
worst_day_report P1/P5), not just "is a non-empty dict"; A3 theoretical_
oracle given the same theta-coverage + series-block depth it always should
have had; A2b stability_views' `conservation_ok` checked LITERALLY True on
every partitioning axis (previously only its KEY SET was checked, never its
VALUE), and vol_terciles — when resolved — required to carry the complete
stratum set (the three opaque-vocabulary terciles + the reserved `vol_na`
bucket, stability.py's `VOL_NA_BUCKET`), each a full `_cell`; Appendix A
feasibility_grid now validates the FULL frozen 63-point (q, r) grid inside
every `cells[...]["grid"]` (axes derived from `gridmix.Q_GRID_MILLIS`/
`R_GRID_MILLIS`, never a separately hardcoded list), per-point per-seed
{7,13,31} coverage (or an `infeasible_by_sample` exemption) and per-seed
field completeness against `gridmix._seed_report`'s real shape; A11
disclosures now requires a `na_conservation` sub-block (`
{"per_table_total_na": {"features": int, "labels": int}, "conservation_ok":
True}` — the contract's "NA 守恒复述") that NO current producer populates
(see the hand-off note this carries for the main agent); `validate_sealed_
files`' per-file date-set comparison is now UNCONDITIONAL (previously an
empty day universe short-circuited the whole comparison via `if universe:`,
so a non-empty file against an empty universe went unnoticed).

This module does not render anything and does not decide what numbers go
into a study payload — it is the boundary that either lets a payload
through onto disk or explains, in a flat list of strings, exactly why not.
No real data is loaded here and nothing in this file consumes researcher
exposure; every function is a pure transform/check over plain Python
objects supplied by the caller.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping
from dataclasses import asdict, is_dataclass

from itsf.s0 import gridmix
from itsf.s0.dataset import ERA_ACTUAL, ERA_PROXY
from itsf.s0.study import BASE_SCENARIO_NAME, ENGINES, FROZEN_THETAS, theta_key

# ---------------------------------------------------------------------------
# 1. frozen top-level section keys (S0_REPORT_CONTENT_CONTRACT.md §A1-A12,
#    plus A2b stability_views per M6_HOLD_RESPONSE.md item 3). VERBATIM and
#    FROZEN to this exact tuple — a change here is an interface break that
#    only the main agent may make.
# ---------------------------------------------------------------------------
FORMAL_SECTIONS: tuple[str, ...] = (
    "structural", "oracle_daily", "theoretical_oracle", "e2_worst_days",
    "sizing_outputs", "frequency", "stability_views", "bootstrap_ci",
    "feasibility_grid", "mc_handoff_manifest", "era_axis", "disclosures",
    "governance",
)

# Keys that stay OFF the sealed formal release (numbers-bearing but never
# published verbatim; Stage-D integrity adapters and record objects live
# here — `split_envelope` moves them here, never into a FORMAL_SECTIONS key).
_INTERNAL_KEYS: tuple[str, ...] = (
    "dataset", "na_reason_counts", "reported_total_na", "records",
)

# --- grid axes reused by the validator (frozen citations; ENGINES/ERA_* are
#     imported so this module can never drift from the single source of
#     truth already frozen in study.py / dataset.py). ------------------------
_SCENARIOS: tuple[str, ...] = ("Base", "Conservative", "Stress", "Severe")
# frozen: S0 §6 (four cost scenarios)
_BLOCKS: tuple[int, ...] = (5, 21)
# frozen: S0 §9 (Primary block 5 trading days / Sensitivity block 21)
_ERAS: tuple[str, ...] = (ERA_PROXY, ERA_ACTUAL)
# frozen: S0 §6 L109-115 (counterfactual_micro_execution / actual era)
_EPOCHS: tuple[str, ...] = ("2010-2013", "2014-2017", "2018-2021")
# frozen: S0 §2 (three stability epochs — M6_HOLD_RESPONSE.md item 3)
_DIRECTIONS: tuple[str, ...] = ("+1", "-1")
# frozen: S0 §2 (多空分开 — long/short split)
FROZEN_N_BOOT = 10_000
# frozen: S0 §9 (10,000 resamples)

# frozen: S0 §7 L133 — the theta axis is EXACTLY the frozen pair, never a
# superset/subset/renamed key (M6.1 seal-boundary finding: a single-theta
# payload must never seal).
_EXPECTED_THETA_KEYS: frozenset[str] = frozenset(
    theta_key(t) for t in FROZEN_THETAS)

# --- A1 structural required sub-keys — VERBATIM S0Dataset attribute names
#     (src/itsf/s0/dataset.py::S0Dataset), so the producer
#     (scripts/s0_real_run.py build_full_study_result) can populate
#     "structural" with a direct `ds.<name>` pull, no re-derivation. Contract
#     citation: S0_REPORT_CONTENT_CONTRACT.md A1 "漏斗/F10 双报/NA 表/锚点/
#     标签可用性/eras/groups". ------------------------------------------------
_STRUCTURAL_REQUIRED_KEYS: tuple[str, ...] = (
    "funnel_counts", "f10_counts", "f10_raw_membership_counts",
    "na_table", "label_anchor_availability", "eras", "groups",
)
# frozen: S0 §4/§5 funnel levels L0-L4 (dataset.py funnel.counts() keys).
_FUNNEL_LEVELS: tuple[str, ...] = (
    "L0_scheduled_trading_days", "L1_observed_rth_days",
    "L2_regular_full_session_candidates", "L3_structurally_eligible_days",
    "L4_final_feature_construction_dates",
)
# frozen: S0 §5 label table (dataset.py _LABEL_DEPS keys).
_LABEL_ANCHOR_KEYS: tuple[str, ...] = (
    "y_cont", "y1", "y2_de_pm", "y3_close_pos_pm", "y4_mfe", "y5_mae",
)
# frozen: S0 §2 L36 groupings (dataset.py _groups() keys).
_GROUPS_REQUIRED_KEYS: tuple[str, ...] = (
    "by_year", "leave_one_year_out", "stability_epochs",
)

# frozen: S0 §10.5 — study.py `_frequency_cell` real per-cell field set.
_FREQUENCY_CELL_FIELDS: tuple[str, ...] = (
    "n_days_in_sample", "n_directional_tradeable", "n_trade_constructible",
    "n_continuation_days_labelled", "n_continuation_days_traded",
    "continuation_base_rate_p", "continuation_base_rate_p_traded_only",
    "n_months_in_slice", "oracle_monthly_frequency",
    "oracle_monthly_frequency_labelled",
)

# frozen: S0 §8 — study.py `_sizing_row` real per-row field set.
_SIZING_ROW_FIELDS: tuple[str, ...] = (
    "trade_date", "engine", "cost_scenario", "direction", "era", "year",
    "stop_level_points", "counterfactual_anchor", "stop_distance_points",
    "risk_usd_per_1_MNQ_planned", "risk_usd_per_1_MNQ_realized",
    "cost_usd_per_1_MNQ", "cost_as_pct_of_R", "minimum_1_contract_risk",
    "stop_triggered", "nonpositive_planned_risk",
)
# frozen: S0 §8/§10.1 non-decisional risk budgets — study.py RISK_BUDGETS_USD.
_COVERAGE_BUDGETS: tuple[str, ...] = ("50", "75", "100", "150")

# frozen: Appendix A — gridmix.py `build_grid` real top-level return keys.
_FEASIBILITY_CELL_FIELDS: tuple[str, ...] = (
    "grid", "n_tp_available", "n_fp_available", "method",
)

# frozen: S0 §2 — stability.py `_cell()` real descriptive-cell field set.
_STABILITY_CELL_FIELDS: tuple[str, ...] = (
    "n", "sum_usd", "mean_usd", "worst_day_pnl_percentiles",
    "best_day", "worst_day", "n_positive", "n_negative", "n_zero",
)
# bookkeeping keys that ride alongside real buckets on a stability axis —
# never a descriptive cell themselves (stability.py's conservation flag /
# the epoch axis's overflow bucket is a real cell, "outside_epochs" IS a
# real bucket too — only "conservation_ok" is bookkeeping, not a cell).
_STABILITY_AXIS_BOOKKEEPING_KEYS: frozenset[str] = frozenset({"conservation_ok"})


# ---------------------------------------------------------------------------
# 1b. M6.1.2-S1 — leaf-level VALUE type predicates + real producer field-type
#     maps. `_check_field_types` is layered on top of every EXISTING
#     field-SET completeness check ("key exists"); it never replaces one —
#     a caller still reports the missing-key problem on its own, and only
#     calls this for a key that IS present, to reject a present-but-wrong-
#     shaped leaf (Codex M6.1.1 finding: "key exists and dict non-empty" is
#     not the same claim as "the value is what the real producer emits").
# ---------------------------------------------------------------------------
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _is_number(v) -> bool:
    """int/float, never bool, and FINITE."""
    return (isinstance(v, (int, float)) and not isinstance(v, bool)
            and math.isfinite(v))


def _is_number_or_none(v) -> bool:
    return v is None or _is_number(v)


def _is_int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def _is_bool(v) -> bool:
    return isinstance(v, bool)


def _is_str(v) -> bool:
    return isinstance(v, str)


def _is_list(v) -> bool:
    return isinstance(v, list)


def _is_mapping(v) -> bool:
    return isinstance(v, dict)


def _is_date_str(v) -> bool:
    return isinstance(v, str) and bool(_DATE_RE.match(v))


def _check_field_types(d, type_map: Mapping[str, object], path: str,
                       problems: list[str]) -> None:
    """Leaf-level VALUE type check for a dict already known to carry (a
    superset of) `type_map`'s keys. Silently no-ops on a non-dict `d` or an
    absent field — presence/completeness is always the CALLER's own rule;
    this only rejects a PRESENT-but-wrong-shaped value."""
    if not isinstance(d, dict):
        return
    for field, predicate in type_map.items():
        if field not in d:
            continue
        if not predicate(d[field]):
            problems.append(f"leaf_type_invalid:{path}.{field}")


# frozen: S0 §10.5 — real study.py `_frequency_cell` per-field types.
_FREQUENCY_CELL_FIELD_TYPES: Mapping[str, object] = {
    "n_days_in_sample": _is_int, "n_directional_tradeable": _is_int,
    "n_trade_constructible": _is_int,
    "n_continuation_days_labelled": _is_int,
    "n_continuation_days_traded": _is_int,
    "continuation_base_rate_p": _is_number_or_none,
    "continuation_base_rate_p_traded_only": _is_number_or_none,
    "n_months_in_slice": _is_int,
    "oracle_monthly_frequency": _is_number_or_none,
    "oracle_monthly_frequency_labelled": _is_number_or_none,
}

# frozen: S0 §8 — real study.py `_sizing_row` per-field types.
_SIZING_ROW_FIELD_TYPES: Mapping[str, object] = {
    "trade_date": _is_date_str, "engine": _is_str, "cost_scenario": _is_str,
    "direction": _is_int, "era": _is_str, "year": _is_str,
    "stop_level_points": _is_number, "counterfactual_anchor": _is_bool,
    "stop_distance_points": _is_number,
    "risk_usd_per_1_MNQ_planned": _is_number,
    "risk_usd_per_1_MNQ_realized": _is_number_or_none,
    "cost_usd_per_1_MNQ": _is_number,
    "cost_as_pct_of_R": _is_number_or_none,
    "minimum_1_contract_risk": _is_number,
    "stop_triggered": _is_bool, "nonpositive_planned_risk": _is_bool,
}

# frozen: S0 §2 — real stability.py `_cell()` per-field types.
_STABILITY_CELL_FIELD_TYPES: Mapping[str, object] = {
    "n": _is_int, "sum_usd": _is_number, "mean_usd": _is_number_or_none,
    "worst_day_pnl_percentiles": _is_mapping,
    "best_day": _is_number_or_none, "worst_day": _is_number_or_none,
    "n_positive": _is_int, "n_negative": _is_int, "n_zero": _is_int,
}

# frozen: Appendix A — real gridmix.py `build_grid` top cell field types.
_FEASIBILITY_CELL_FIELD_TYPES: Mapping[str, object] = {
    "grid": _is_mapping, "n_tp_available": _is_int, "n_fp_available": _is_int,
    "method": _is_str,
}

# frozen: Appendix A — real gridmix.py `_seed_report` per-seed field set +
# per-field types (the "day-marker summary" is the real `day_markers` list).
_GRID_SEED_FIELDS: tuple[str, ...] = (
    "target_precision", "target_recall", "realized_precision",
    "realized_recall", "day_markers", "F_expected")
_GRID_SEED_FIELD_TYPES: Mapping[str, object] = {
    "target_precision": _is_number, "target_recall": _is_number,
    "realized_precision": _is_number_or_none,
    "realized_recall": _is_number_or_none,
    "day_markers": _is_list, "F_expected": _is_number,
}

# frozen: Appendix A — the FULL frozen (q, r) grid, DERIVED from gridmix's
# OWN axis construction (never a separately hardcoded list — mission
# requirement). 9 q-values x 7 r-values = 63 points; key format matches
# gridmix.py's own `f"q{q_mil/1000:.2f}_r{r_mil/1000:.2f}"` exactly.
_FEASIBILITY_GRID_POINT_KEYS: frozenset[str] = frozenset(
    f"q{q_mil / 1000:.2f}_r{r_mil / 1000:.2f}"
    for q_mil in gridmix.Q_GRID_MILLIS for r_mil in gridmix.R_GRID_MILLIS)

# frozen: S0 §7 — real study.py `_series_block` scalar-field types (the
# per-day (date, USD) pair LIST itself is checked separately, since its key
# name varies: "daily_pnl_usd" for oracle_daily's executable matrix,
# "daily_usd" for theoretical_oracle).
_SERIES_BLOCK_SCALAR_TYPES: Mapping[str, object] = {
    "n": _is_int, "sum_usd": _is_number, "mean_usd": _is_number_or_none,
    "min_usd": _is_number_or_none, "max_usd": _is_number_or_none,
    "worst_day_pnl_percentiles": _is_mapping,
}

# frozen: S0 §4/§5 — real dataset.py `build_na_table` per-field-row shape
# (na/not_na counts + the reasons breakdown).
_NA_TABLE_FIELD_ROW_TYPES: Mapping[str, object] = {
    "na": _is_int, "not_na": _is_int, "reasons": _is_mapping,
}

# A11 disclosures.na_conservation minimal shape (mission item 8 / contract
# §A11 "NA 守恒复述"): the reported total NA per table plus a boolean flag
# restating that it agrees with dataset.py's own na_table accounting. NOT
# populated by any current producer — see this module's docstring.
_NA_CONSERVATION_TABLES: tuple[str, ...] = ("features", "labels")


# ---------------------------------------------------------------------------
# 1c. M6.1.2-S3 — sealed-record LEAF TYPES (mission item 2): validate_sealed_
#     files previously checked the per-line field SET only (FORMAL_RECORD_
#     FIELDS all present) and never that each field's VALUE is the real
#     §10.1 type — a numeric string ("20000.0" for entry_fill, "1" for
#     direction) on a sealed JSONL line sailed straight through. Reused
#     alongside the existing leaf predicates rather than duplicating them.
# ---------------------------------------------------------------------------
def _is_direction_value(v) -> bool:
    """frozen: S0 §5 — direction is +1 (long) or -1 (short), an int, never a
    numeric string and never any other integer."""
    return isinstance(v, int) and not isinstance(v, bool) and v in (1, -1)


def _is_nonempty_number_list(v) -> bool:
    """frozen: S0 §10.1 — mtm_close_pnl_1m/mtm_adverse_pnl_1m are the
    per-minute mark series of an ACTUAL trade path; a trade path with zero
    minute marks is not a real §3 trade, so an empty list is refused here
    the same as a wrong type."""
    return (isinstance(v, list) and len(v) > 0
           and all(_is_number(x) for x in v))


# frozen: S0 §10.1 — real per-line FORMAL_RECORD_FIELDS leaf types (the
# atomic per-contract intraday path record, exactly as record_to_formal_dict
# emits it onto a sealed MC_HANDOFF_<engine>_<scenario>.jsonl line).
_SEALED_RECORD_FIELD_TYPES: Mapping[str, object] = {
    "trade_date": _is_date_str, "engine": _is_str, "cost_scenario": _is_str,
    "direction": _is_direction_value,
    "entry_timestamp": _is_str, "exit_timestamp": _is_str,
    "entry_fill": _is_number, "exit_fill": _is_number,
    "final_pnl_per_contract": _is_number,
    "mtm_close_pnl_1m": _is_nonempty_number_list,
    "mtm_adverse_pnl_1m": _is_nonempty_number_list,
    "max_adverse_pnl": _is_number, "max_favourable_pnl": _is_number,
    "time_of_max_adverse": _is_str,
    "planned_stop": _is_number_or_none, "actual_stop_fill": _is_number_or_none,
    "stop_triggered": _is_bool, "sizing_anchor_usd": _is_number,
    "ambiguous_stop_vs_floor": _is_bool,
}


# ---------------------------------------------------------------------------
# 2. record_to_formal_dict — FROZEN §10.1 field names
# ---------------------------------------------------------------------------
_TS_RENAME = {"entry_ts": "entry_timestamp", "exit_ts": "exit_timestamp"}

# frozen: S0 §10.1 atomic per-contract intraday trade path — trade_date,
# entry_timestamp/exit_timestamp (renamed from entry_ts/exit_ts), direction,
# entry_fill, exit_fill, final_pnl_per_contract, mtm_close_pnl_1m,
# mtm_adverse_pnl_1m, max_adverse_pnl, max_favourable_pnl,
# time_of_max_adverse, planned_stop, actual_stop_fill, stop_triggered —
# PLUS the four M6.1 extension fields already carried on
# contracts.TradePathRecord: engine, cost_scenario, sizing_anchor_usd,
# ambiguous_stop_vs_floor. Every non-timestamp name is verbatim.
FORMAL_RECORD_FIELDS: tuple[str, ...] = (
    "trade_date", "engine", "cost_scenario", "direction",
    "entry_timestamp", "exit_timestamp", "entry_fill", "exit_fill",
    "final_pnl_per_contract", "mtm_close_pnl_1m", "mtm_adverse_pnl_1m",
    "max_adverse_pnl", "max_favourable_pnl", "time_of_max_adverse",
    "planned_stop", "actual_stop_fill", "stop_triggered",
    "sizing_anchor_usd", "ambiguous_stop_vs_floor",
)


def record_to_formal_dict(rec) -> dict:
    """TradePathRecord (or an equivalent plain dict) -> the FROZEN §10.1
    formal-record dict.

    `entry_ts`/`exit_ts` are renamed to `entry_timestamp`/`exit_timestamp`;
    every other field keeps its internal name. Raises ValueError if the
    resulting field set is not EXACTLY `FORMAL_RECORD_FIELDS` (no silent
    drop, no silent extra) and TypeError if `rec` is neither a dataclass
    instance nor a plain dict. Key order in the returned dict is
    deterministic (alphabetically sorted).
    """
    if is_dataclass(rec) and not isinstance(rec, type):
        raw = asdict(rec)
    elif isinstance(rec, dict):
        raw = dict(rec)
    else:
        raise TypeError(
            "record_to_formal_dict: expected a TradePathRecord dataclass "
            f"instance or a plain dict, got {type(rec).__name__}")
    renamed = {_TS_RENAME.get(k, k): v for k, v in raw.items()}
    got, want = set(renamed), set(FORMAL_RECORD_FIELDS)
    if got != want:
        raise ValueError(
            "record_to_formal_dict: field set mismatch vs frozen S0 §10.1 "
            f"— missing={sorted(want - got)} extra={sorted(got - want)}")
    return {k: renamed[k] for k in sorted(renamed)}


# ---------------------------------------------------------------------------
# 3. to_formal_json — strict serializer, no silent stringification
# ---------------------------------------------------------------------------
class _StrictEncoder(json.JSONEncoder):
    """Defense-in-depth only: `_clean` (below) already rejects every
    disallowed type/key/non-finite-float BEFORE `json.dumps` ever runs, so
    `default` should never actually fire on a `_clean`-ed tree. It exists so
    a stray type that somehow reaches `json.dumps` still gets a hard raise
    instead of any `str(...)` fallback."""

    def default(self, o):
        raise TypeError(
            f"to_formal_json: unsupported type reached the encoder: "
            f"{type(o).__name__} (no default=str fallback — fix the "
            "producer, or fix `_clean` if this type should be rejected "
            "earlier)")


def _clean(obj, path: str = "$"):
    """Validate + copy `obj` into a JSON-safe tree (tuple -> list).

    Allowed leaf/container types: dict (str keys only), list, tuple, str,
    int, bool, None, and FINITE float. Anything else raises — TypeError for
    a disallowed type or a non-str dict key, ValueError for a non-finite
    float — a hard failure, never a `default=str` fallback. Reused by
    `split_envelope` (validation only; the transformed copy is discarded
    there) so the two callers can never drift into different type policies.
    """
    if isinstance(obj, dict):
        cleaned = {}
        for key, value in obj.items():
            if not isinstance(key, str):
                raise TypeError(
                    f"to_formal_json: dict key at {path} must be str, got "
                    f"{type(key).__name__}: {key!r}")
            cleaned[key] = _clean(value, f"{path}.{key}")
        return cleaned
    if isinstance(obj, (list, tuple)):
        return [_clean(v, f"{path}[{i}]") for i, v in enumerate(obj)]
    if isinstance(obj, bool) or obj is None or isinstance(obj, str):
        return obj
    if isinstance(obj, float):
        if not math.isfinite(obj):
            raise ValueError(
                f"to_formal_json: non-finite float at {path}: {obj!r}")
        return obj
    if isinstance(obj, int):
        return obj
    raise TypeError(
        f"to_formal_json: unsupported type at {path}: {type(obj).__name__} "
        "(no default=str fallback — fix the producer)")


def to_formal_json(obj) -> str:
    """Strict JSON serialization for the sealed formal release.

    `sort_keys=True, indent=1, allow_nan=False` and NO `default=` fallback:
    anything that is not a plain dict/list/tuple/str/int/bool/None/finite
    float is a hard raise (M6_HOLD_RESPONSE.md item 2's `default=str` /
    `n_boot=40` leak class of defect). Non-finite floats are rejected by an
    explicit `math.isfinite` walk (`_clean`) BEFORE `json.dumps` runs;
    `allow_nan=False` on the dumps call is a redundant second net, not the
    primary guard (and the walk also catches things allow_nan alone would
    not — e.g. a bool/int/float/None dict key, which `json.dumps` would
    otherwise silently stringify rather than reject).
    """
    cleaned = _clean(obj)
    return json.dumps(cleaned, cls=_StrictEncoder, sort_keys=True, indent=1,
                      allow_nan=False)


# ---------------------------------------------------------------------------
# 4. split_envelope — internal vs formal payload split
# ---------------------------------------------------------------------------
def split_envelope(compute_result: dict) -> tuple[dict, dict]:
    """Split a Stage-C compute result into (internal, formal).

    internal = whichever of {"dataset", "na_reason_counts",
    "reported_total_na", "records"} are present in `compute_result`
    (objects allowed — this side never reaches Stage E's sealed release).

    formal = whichever of `FORMAL_SECTIONS` are present, UNCHANGED (a
    section simply absent from `compute_result` stays simply absent here
    too — `validate_formal_payload` is what reports that as a problem;
    this function never invents a placeholder section).

    Raises TypeError/ValueError (via the same strict-type walk `to_formal_
    json` uses) if any FORMAL_SECTIONS value contains anything other than
    plain dict/list/tuple/str/int/bool/None/finite-float — in particular a
    raw dataset object or a TradePathRecord instance can never reach the
    formal side; the fix is to keep such data on the internal side or
    convert it (e.g. via `record_to_formal_dict`) before it enters
    `compute_result` under a FORMAL_SECTIONS key.
    """
    if not isinstance(compute_result, dict):
        raise TypeError(
            "split_envelope: compute_result must be a dict, got "
            f"{type(compute_result).__name__}")
    internal = {k: compute_result[k] for k in _INTERNAL_KEYS
               if k in compute_result}
    formal: dict = {}
    for key in FORMAL_SECTIONS:
        if key not in compute_result:
            continue
        value = compute_result[key]
        _clean(value, path=f"${key}")          # raises on any non-plain object
        formal[key] = value
    return internal, formal


# ---------------------------------------------------------------------------
# 5. validate_formal_payload — S0_REPORT_CONTENT_CONTRACT.md §B, rules R1-R10
# ---------------------------------------------------------------------------
def _walk_r8(obj, path: str, problems: list[str]) -> None:
    """Rule R8: whole-payload scan for a non-finite float, a non-str dict
    key, a stringified-object leak ("...object at 0x..."), or a literal
    "dataset" key anywhere in the tree (not just at the top level)."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == "dataset":
                problems.append(f"dataset_key_present:{path}.{key}")
            if not isinstance(key, str):
                problems.append(f"non_str_key:{path}:{key!r}")
                _walk_r8(value, f"{path}.<{key!r}>", problems)
                continue
            _walk_r8(value, f"{path}.{key}", problems)
        return
    if isinstance(obj, (list, tuple)):
        for i, value in enumerate(obj):
            _walk_r8(value, f"{path}[{i}]", problems)
        return
    if isinstance(obj, bool) or obj is None or isinstance(obj, int):
        return
    if isinstance(obj, float):
        if not math.isfinite(obj):
            problems.append(f"non_finite_float:{path}")
        return
    if isinstance(obj, str):
        if "object at 0x" in obj:
            problems.append(f"object_repr_leak:{path}")
        return
    # `split_envelope`/`to_formal_json` already reject every other type
    # before a payload reaches this validator; this is a defensive net so
    # a hand-built or malformed payload degrades to a problem, not a crash.
    problems.append(f"unexpected_type:{path}:{type(obj).__name__}")


def _check_series_block(block, path: str, problems: list[str], *,
                        value_key: str = "daily_pnl_usd",
                        allowed_dates: frozenset[str] | None = None) -> None:
    """Deep leaf check for one real study.py `_series_block` output — the
    per-day (date, USD) pair LIST under `value_key`, plus the scalar
    descriptive fields — never just "is a non-empty dict" (mission item 5).

    mission M6.1.2-S3 item 5 (SELF-CONSISTENCY, re-derived, never merely
    leaf-typed): every date in the series must belong to `allowed_dates`
    (the theta's tp_days UNION fp_days day population — a "ghost" date that
    belongs to neither is refused, not just an ill-formed one); `n` must
    equal the ACTUAL pair count; `sum_usd` must equal the actual sum of the
    ACTUAL values and `mean_usd` the actual sum/n — compared via
    `math.isclose` (rel_tol=abs_tol=1e-9) because the recomputed sum should
    reproduce the producer's own float64 accumulation bit-for-bit when the
    stored pair order is untouched (this is a safety net against float
    reordering, not the primary tolerance). The sum/mean/n cross-check is
    skipped when the series itself carries an ill-typed pair (already
    flagged by the per-pair checks below) so this never double-reports the
    same defect under two different problem codes.
    """
    if not isinstance(block, dict):
        problems.append(f"series_block_missing:{path}")
        return
    for field in _SERIES_BLOCK_SCALAR_TYPES:
        if field not in block:
            problems.append(f"series_block_field_missing:{path}.{field}")
    _check_field_types(block, _SERIES_BLOCK_SCALAR_TYPES, path, problems)
    series = block.get(value_key)
    if not isinstance(series, list):
        problems.append(f"series_block_series_missing:{path}.{value_key}")
    else:
        valid_pairs: list[tuple[str, float]] = []
        all_valid = True
        for i, pair in enumerate(series):
            if not (isinstance(pair, list) and len(pair) == 2):
                problems.append(f"series_block_pair_shape:{path}.{i}")
                all_valid = False
                continue
            d, v = pair
            d_ok, v_ok = _is_date_str(d), _is_number(v)
            if not d_ok:
                problems.append(
                    f"series_block_date_invalid:{path}.{i}:{d!r}")
                all_valid = False
            if not v_ok:
                problems.append(
                    f"series_block_value_invalid:{path}.{i}:{v!r}")
                all_valid = False
            if d_ok and v_ok:
                valid_pairs.append((d, float(v)))
        if allowed_dates is not None:
            for d, _v in valid_pairs:
                if d not in allowed_dates:
                    problems.append(f"series_block_ghost_date:{path}:{d}")
        if all_valid:
            actual_n = len(valid_pairs)
            declared_n = block.get("n")
            if (isinstance(declared_n, int) and not isinstance(declared_n, bool)
                    and declared_n != actual_n):
                problems.append(
                    f"series_block_n_mismatch:{path}:"
                    f"{declared_n}!={actual_n}")
            actual_sum = sum(v for _d, v in valid_pairs) if valid_pairs \
                else 0.0
            declared_sum = block.get("sum_usd")
            if (_is_number(declared_sum)
                    and not math.isclose(declared_sum, actual_sum,
                                         rel_tol=1e-9, abs_tol=1e-9)):
                problems.append(
                    f"series_block_sum_usd_mismatch:{path}:"
                    f"{declared_sum}!={actual_sum}")
            expected_mean = (actual_sum / actual_n) if actual_n else None
            declared_mean = block.get("mean_usd")
            mean_ok = (
                (expected_mean is None and declared_mean is None)
                or (expected_mean is not None and _is_number(declared_mean)
                    and math.isclose(declared_mean, expected_mean,
                                     rel_tol=1e-9, abs_tol=1e-9)))
            if not mean_ok:
                problems.append(
                    f"series_block_mean_usd_mismatch:{path}:"
                    f"{declared_mean}!={expected_mean}")
    wpp = block.get("worst_day_pnl_percentiles")
    if isinstance(wpp, dict) and not {"P1", "P5"} <= set(wpp):
        problems.append(f"series_block_percentiles_incomplete:{path}")


def _check_executable_cell(cell, path: str, problems: list[str], *,
                           allowed_dates: frozenset[str] | None = None
                           ) -> None:
    """Deep leaf check for one oracle_daily `executable[engine][scenario]`
    cell against the REAL study.py shape: pooled + by_era{PROXY,ACTUAL}
    (both era keys) + the worst_day_report P1/P5 block (mission item 5) —
    never just "is a non-empty dict". `allowed_dates` (mission M6.1.2-S3
    item 5) is the theta's tp_days UNION fp_days day population, forwarded
    into every series block so a "ghost" date foreign to that theta's day
    universe is refused."""
    if not isinstance(cell, dict) or not cell:
        problems.append(f"oracle_daily_executable_missing:{path}")
        return
    _check_series_block(cell.get("pooled"), f"{path}|pooled", problems,
                        allowed_dates=allowed_dates)
    by_era = cell.get("by_era")
    if not isinstance(by_era, dict) or not set(_ERAS) <= set(by_era):
        problems.append(f"oracle_daily_executable_by_era_missing:{path}")
    else:
        for era in _ERAS:
            _check_series_block(by_era.get(era), f"{path}|by_era|{era}",
                                problems, allowed_dates=allowed_dates)
    wdr = cell.get("worst_day_report")
    if not isinstance(wdr, dict):
        problems.append(f"oracle_daily_worst_day_report_missing:{path}")
        return
    pooled_pct = wdr.get("pooled")
    if not isinstance(pooled_pct, dict) or not {"P1", "P5"} <= set(pooled_pct):
        problems.append(f"oracle_daily_worst_day_report_pooled:{path}")
    era_pct = wdr.get("by_era")
    if not isinstance(era_pct, dict) or not set(_ERAS) <= set(era_pct):
        problems.append(f"oracle_daily_worst_day_report_by_era:{path}")
    else:
        for era in _ERAS:
            cell_pct = era_pct.get(era)
            if (not isinstance(cell_pct, dict)
                    or not {"P1", "P5"} <= set(cell_pct)):
                problems.append(
                    f"oracle_daily_worst_day_report_by_era:{path}|{era}")


def _check_feasibility_cell(cval, path: str, problems: list[str]) -> None:
    """Deep leaf check for one `feasibility_grid.cells[theta|engine|scenario]`
    entry against the REAL gridmix.py `build_grid` return shape: the FULL
    frozen 63-point (q, r) grid (mission item 7) — not just the outer
    {grid, n_tp_available, n_fp_available, method} field set."""
    if (not isinstance(cval, dict)
            or not set(_FEASIBILITY_CELL_FIELDS) <= set(cval)):
        problems.append(f"feasibility_grid_cell_incomplete:{path}")
        return
    _check_field_types(cval, _FEASIBILITY_CELL_FIELD_TYPES, path, problems)
    grid = cval.get("grid")
    if not isinstance(grid, dict):
        problems.append(f"feasibility_grid_inner_missing:{path}")
        return
    actual = set(grid)
    for k in sorted(_FEASIBILITY_GRID_POINT_KEYS - actual):
        problems.append(f"feasibility_grid_point_missing:{path}:{k}")
    for k in sorted(actual - _FEASIBILITY_GRID_POINT_KEYS):
        problems.append(f"feasibility_grid_point_extra:{path}:{k}")
    for k in sorted(_FEASIBILITY_GRID_POINT_KEYS & actual):
        point = grid[k]
        if not isinstance(point, dict) or "infeasible_by_sample" not in point:
            problems.append(
                f"feasibility_grid_point_infeasible_flag_missing:{path}:{k}")
            continue
        if point["infeasible_by_sample"] is True:
            # frozen: S0 Appendix A — an infeasible point is still REPORTED
            # in full but carries no per-seed selection (gridmix.py's
            # `_grid_point` returns immediately once n_fp exceeds
            # availability, leaving `per_seed` at its initial `{}` — never
            # populated); requiring {7,13,31} here would be wrong.
            # mission M6.1.2-S3 item 7: the OLD gate skipped this branch
            # entirely, so a per_seed entry FABRICATED onto an infeasible
            # point (smuggling a realized_precision the real producer never
            # computes) sailed through unseen — absent or EMPTY is the only
            # shape the real producer ever emits here.
            per_seed = point.get("per_seed")
            if per_seed not in (None, {}):
                problems.append(
                    f"feasibility_grid_infeasible_point_has_per_seed:"
                    f"{path}:{k}")
            continue
        per_seed = point.get("per_seed")
        if isinstance(per_seed, dict):
            try:
                seeds = sorted(int(s) for s in per_seed)
            except (TypeError, ValueError):
                seeds = None
        else:
            seeds = None
        if seeds != [7, 13, 31]:
            problems.append(f"feasibility_grid_point_seeds:{path}:{k}")
            continue
        for seed in (7, 13, 31):
            entry = per_seed.get(seed, per_seed.get(str(seed)))
            if (not isinstance(entry, dict)
                    or not set(_GRID_SEED_FIELDS) <= set(entry)):
                problems.append(
                    f"feasibility_grid_seed_entry_incomplete:"
                    f"{path}:{k}:{seed}")
            else:
                _check_field_types(
                    entry, _GRID_SEED_FIELD_TYPES, f"{path}:{k}:{seed}",
                    problems)


def _stability_axis_n_sum(axis: object) -> int | None:
    """mission M6.1.2-S3 item 1 helper: sum(cell["n"]) over every REAL
    (non-bookkeeping) bucket of one stability_views axis dict, or None when
    `axis` is not a dict or any bucket's "n" is not a usable int (the
    leaf-type-completeness check elsewhere already reports that defect on
    its own — this never double-reports it as a spurious conservation
    mismatch). "outside_epochs"/"vol_na" are REAL buckets and are summed;
    only "conservation_ok"/"status"/"reason" are bookkeeping."""
    if not isinstance(axis, dict):
        return None
    total = 0
    for bkey, bval in axis.items():
        if bkey in (_STABILITY_AXIS_BOOKKEEPING_KEYS | {"status", "reason"}):
            continue
        n = bval.get("n") if isinstance(bval, dict) else None
        if not isinstance(n, int) or isinstance(n, bool):
            return None
        total += n
    return total


def validate_formal_payload(payload, *, expected_governance=None) -> list[str]:
    """S0_REPORT_CONTENT_CONTRACT.md §B machine check, rules R1-R10 + the
    M6.1 seal-boundary hardening (conservation gates, exact schemas, the
    governance CONTEXT cross-check).

    Returns a flat list of problem strings; EMPTY means sealable. Never
    raises on a malformed payload — every rule below degrades to a problem
    string instead (a validator that can crash is not a fail-closed gate).

    `expected_governance`: the caller's INDEPENDENTLY-derived governance
    truth (fresh `guards.FROZEN_HASHES`, a freshly re-parsed registry
    event, the trial_id/authorized_commit/engineering_seed/
    registry_sequence_snapshot the CALLER — never the payload itself —
    believes are current). Formal sealing REQUIRES this: omitting it (the
    default, `None`) is ITSELF a problem (`governance_context_not_supplied`)
    rather than a silent pass, because a payload can be internally
    well-formed while its embedded `governance` block is stale or
    fabricated. When supplied, every field is compared for EXACT equality
    (`trial_id`, `authorized_commit`, `engineering_seed`, `frozen_hashes`
    as a whole-dict equality, `registry_sequence_snapshot`); any mismatch
    is `governance_mismatch:<field>`.

    TWO-CALL CONTRACT (M6.1 finding on the seal boundary): this function
    cannot see the sealed JSONL bytes — those are serialized by the
    renderer AFTER this payload is judged sealable, and the
    `mc_handoff_manifest.counts` -> `mc_handoff_manifest.files` manifest is
    injected into the payload only at that point. The renderer (main-agent
    owned, scripts/s0_real_run.py `render_s0_report`) MUST therefore call
    this function TWICE: once on the pre-injection payload (as today), and
    AGAIN on the manifest-injected payload immediately before sealing —
    the second call is safe (a `files` sub-key under `mc_handoff_manifest`
    is never inspected here and never rejected) but is not sufficient by
    itself: a counts-vs-actual-bytes conflict is invisible to a
    payload-only check and is caught only by `validate_sealed_files`
    (called against the same post-injection payload). See
    `test_post_injection_corruption_caught_by_second_validate_call` in
    tests/test_s0_report.py for a worked example of why both calls plus
    `validate_sealed_files` are required together.
    """
    if not isinstance(payload, dict):
        return ["payload_not_dict"]

    problems: list[str] = []

    # R1 — every section present, non-empty, and a dict.
    for key in FORMAL_SECTIONS:
        if key not in payload:
            problems.append(f"missing_section:{key}")
        elif not isinstance(payload[key], dict):
            problems.append(f"wrong_type:{key}")
        elif not payload[key]:
            problems.append(f"empty_section:{key}")
    if problems:
        # deeper rules assume every section exists and is a non-empty dict;
        # fail closed on the coarse defect rather than risk KeyError noise.
        return problems

    # frozen: S0 §7 L133 — the theta axis is EXACTLY {0.5, 0.3}, never a
    # subset (a single-theta payload), a superset, or a renamed key.
    tkeys = sorted(payload["oracle_daily"])
    if set(tkeys) != _EXPECTED_THETA_KEYS:
        problems.append(
            f"theta_axis_mismatch:got={tkeys}:"
            f"expected={sorted(_EXPECTED_THETA_KEYS)}")

    # R-DU — A2 day_universe: n_tp/n_fp/tp_days/fp_days present, and every
    # conservation flag LITERALLY True (frozen App A: under every one of
    # the four readings study.py checks, nothing may be silently dropped;
    # a single False anywhere is a defect, never a warning).
    theta_unions: dict[str, frozenset] = {}
    theta_tp_days: dict[str, frozenset] = {}
    for tkey in tkeys:
        tcell = payload["oracle_daily"].get(tkey)
        du = tcell.get("day_universe") if isinstance(tcell, dict) else None
        if not isinstance(du, dict):
            problems.append(f"day_universe_missing:{tkey}")
            continue
        for field in ("n_tp", "n_fp"):
            v = du.get(field)
            if not isinstance(v, int) or isinstance(v, bool) or v < 0:
                problems.append(f"day_universe_field_invalid:{tkey}:{field}")

        # mission M6.1.2-S3 item 6a — EMPTY-STUDY FLOOR: a zero-day universe
        # (n_tp == n_fp == 0) has no D_TP series to describe at all and must
        # never seal, regardless of how "clean" every other section looks.
        n_tp_raw, n_fp_raw = du.get("n_tp"), du.get("n_fp")
        if (isinstance(n_tp_raw, int) and not isinstance(n_tp_raw, bool)
                and isinstance(n_fp_raw, int) and not isinstance(n_fp_raw, bool)
                and n_tp_raw == 0 and n_fp_raw == 0):
            problems.append(f"day_universe_empty_universe:{tkey}")
        day_lists: dict[str, list] = {}
        for field in ("tp_days", "fp_days"):
            v = du.get(field)
            if not isinstance(v, list):
                problems.append(f"day_universe_field_invalid:{tkey}:{field}")
            else:
                day_lists[field] = v
                bad = [d for d in v if not _is_date_str(d)]
                if bad:
                    problems.append(
                        f"day_universe_date_format_invalid:{tkey}:{field}:"
                        f"{bad[:3]}")
        cons = du.get("conservation")
        if not isinstance(cons, dict) or not cons:
            problems.append(f"day_universe_conservation_missing:{tkey}")
        else:
            for flag, val in cons.items():
                if val is not True:
                    problems.append(
                        f"day_universe_conservation_false:{tkey}:{flag}")

        # mission hardening: n_tp/n_fp COUNT identity against the actual
        # lists, no duplicate day within either list, and the TP/FP
        # partition itself disjoint — each a DISTINCT problem code, never
        # folded into one generic flag.
        tp_days, fp_days = day_lists.get("tp_days"), day_lists.get("fp_days")
        n_tp, n_fp = du.get("n_tp"), du.get("n_fp")
        if (isinstance(tp_days, list) and isinstance(n_tp, int)
                and not isinstance(n_tp, bool) and len(tp_days) != n_tp):
            problems.append(
                f"day_universe_count_mismatch:{tkey}:n_tp:"
                f"{n_tp}!={len(tp_days)}")
        if (isinstance(fp_days, list) and isinstance(n_fp, int)
                and not isinstance(n_fp, bool) and len(fp_days) != n_fp):
            problems.append(
                f"day_universe_count_mismatch:{tkey}:n_fp:"
                f"{n_fp}!={len(fp_days)}")
        if isinstance(tp_days, list):
            dupes = sorted({d for d in tp_days if tp_days.count(d) > 1})
            if dupes:
                problems.append(
                    f"day_universe_duplicate_days:{tkey}:tp_days:{dupes}")
        if isinstance(fp_days, list):
            dupes = sorted({d for d in fp_days if fp_days.count(d) > 1})
            if dupes:
                problems.append(
                    f"day_universe_duplicate_days:{tkey}:fp_days:{dupes}")
        if isinstance(tp_days, list) and isinstance(fp_days, list):
            overlap = sorted(set(tp_days) & set(fp_days))
            if overlap:
                problems.append(
                    f"day_universe_tp_fp_overlap:{tkey}:{overlap}")
            theta_unions[tkey] = frozenset(tp_days) | frozenset(fp_days)
            theta_tp_days[tkey] = frozenset(tp_days)

    # cross-theta consistency (mission item 3): the union tp∪fp is the SAME
    # day population under every frozen theta — only the partition moves
    # (frozen App A). Compared only across thetas whose lists were both
    # well-typed above; a theta already flagged malformed is skipped here
    # rather than raising noise on top of its own specific problem.
    if len(theta_unions) >= 2 and len({*theta_unions.values()}) > 1:
        problems.append(
            "day_universe_cross_theta_population_mismatch:"
            + ",".join(sorted(theta_unions)))

    # THETA NESTING (mission M6.1.2-S3 item 3): D_TP(theta) = {d: Y_cont(d)
    # >= theta} (frozen App A / S0 §7 L133, `study._partition`), so raising
    # theta can only ever SHRINK the TP set over the SAME day population —
    # the STRICTER (larger) frozen theta's tp_days is necessarily a SUBSET
    # of the LOOSER (smaller) frozen theta's tp_days. FROZEN_THETAS is the
    # exact pair (0.5 primary, 0.3 secondary) imported from study.py, never
    # a generic "sorted thetas" comparison.
    _hi_tkey, _lo_tkey = theta_key(max(FROZEN_THETAS)), theta_key(min(FROZEN_THETAS))
    if _hi_tkey in theta_tp_days and _lo_tkey in theta_tp_days:
        leaked = sorted(theta_tp_days[_hi_tkey] - theta_tp_days[_lo_tkey])
        if leaked:
            problems.append(
                f"day_universe_theta_nesting_violation:{_hi_tkey}_not_"
                f"subset_of_{_lo_tkey}:{leaked}")

    # R-EXEC — A2 executable matrix: E1/E2 x {Base,Conservative,Stress,
    # Severe}, for EVERY frozen theta, UNCONDITIONALLY (the M6.1 relaxation
    # that only checked this when mc_handoff_manifest also validated is
    # removed now that the fixture mirrors the real study.py producer
    # shape — frozen S0 §7).
    for tkey in tkeys:
        tcell = payload["oracle_daily"].get(tkey)
        ex = tcell.get("executable") if isinstance(tcell, dict) else None
        if not isinstance(ex, dict):
            problems.append(f"oracle_daily_executable_missing:{tkey}")
            continue
        for eng in ENGINES:
            eng_block = ex.get(eng)
            if not isinstance(eng_block, dict):
                problems.append(
                    f"oracle_daily_executable_missing:{tkey}|{eng}")
                continue
            for scn in _SCENARIOS:
                cell = eng_block.get(scn)
                _check_executable_cell(cell, f"{tkey}|{eng}|{scn}", problems,
                                       allowed_dates=theta_unions.get(tkey))

    # R-STRUCT — A1 structural: funnel + F10 dual report (final + raw
    # membership) + na_table + label_anchor_availability + eras + groups.
    # Key names are VERBATIM S0Dataset attribute names (see the
    # _STRUCTURAL_REQUIRED_KEYS citation above) — the entrypoint populates
    # this section with a direct `ds.<name>` pull.
    st = payload["structural"]
    for key in _STRUCTURAL_REQUIRED_KEYS:
        if key not in st:
            problems.append(f"structural_missing:{key}")
    # NOTE (M6.1.2-S1 fix): each check below used to be gated `if v is not
    # None and (...)`, which meant a required sub-key literally present but
    # set to None (or any other falsy-but-not-dict value) sailed through
    # with ZERO problem reported — a real leaf-level gap (mission item 2:
    # "leaf set to None" must be refused) distinct from "structural_missing"
    # (which only fires when the KEY itself is absent). The gate is removed:
    # a None/wrong-type value here now always fails its own shape check.
    fc = st.get("funnel_counts")
    if not isinstance(fc, dict) or not set(_FUNNEL_LEVELS) <= set(fc):
        problems.append("structural_funnel_counts_incomplete")
    else:
        for level in _FUNNEL_LEVELS:
            if not _is_int(fc.get(level)):
                problems.append(f"leaf_type_invalid:structural.funnel_counts."
                                f"{level}")
        # non-blocking hardening: the funnel is a NARROWING sequence L0 (all
        # scheduled trading days) down to L4 (final feature construction
        # dates) — frozen S0 §4/§5 each level is a subset of the one before
        # it, so the counts must be non-increasing L0>=L1>=L2>=L3>=L4.
        levels = [fc.get(level) for level in _FUNNEL_LEVELS]
        if all(_is_int(v) for v in levels) and any(
                levels[i] < levels[i + 1] for i in range(len(levels) - 1)):
            problems.append("structural_funnel_counts_not_monotonic")
    for key in ("f10_counts", "f10_raw_membership_counts"):
        v = st.get(key)
        if not (isinstance(v, dict) and v):
            problems.append(f"structural_{key}_empty")
        else:
            for cat, n in v.items():
                if not _is_int(n):
                    problems.append(f"leaf_type_invalid:structural.{key}."
                                    f"{cat}")
    nat = st.get("na_table")
    per_field = nat.get("per_field") if isinstance(nat, dict) else None
    if (not isinstance(nat, dict) or "population" not in nat
            or not isinstance(per_field, dict)
            or not {"features", "labels"} <= set(per_field)):
        problems.append("structural_na_table_incomplete")
    else:
        if not _is_int(nat.get("population")):
            problems.append("leaf_type_invalid:structural.na_table.population")
        for table in ("features", "labels"):
            rows = per_field.get(table)
            if not isinstance(rows, dict):
                continue
            for field, row in rows.items():
                if (not isinstance(row, dict)
                        or not set(_NA_TABLE_FIELD_ROW_TYPES) <= set(row)):
                    problems.append(
                        f"structural_na_table_row_incomplete:{table}.{field}")
                else:
                    _check_field_types(
                        row, _NA_TABLE_FIELD_ROW_TYPES,
                        f"structural.na_table.per_field.{table}.{field}",
                        problems)
    laa = st.get("label_anchor_availability")
    if not isinstance(laa, dict) or not set(_LABEL_ANCHOR_KEYS) <= set(laa):
        problems.append("structural_label_anchor_availability_incomplete")
    else:
        for label in _LABEL_ANCHOR_KEYS:
            row = laa.get(label)
            if (not isinstance(row, dict) or not _is_int(row.get(
                    "available_days")) or not _is_int(row.get(
                        "unavailable_days"))):
                problems.append(
                    f"leaf_type_invalid:structural.label_anchor_"
                    f"availability.{label}")
    er = st.get("eras")
    if not isinstance(er, dict) or not set(_ERAS) <= set(er):
        problems.append("structural_eras_incomplete")
    else:
        for era in _ERAS:
            v = er.get(era)
            if not isinstance(v, list) or any(not _is_date_str(d)
                                              for d in v):
                problems.append(f"leaf_type_invalid:structural.eras.{era}")
    gr = st.get("groups")
    if not isinstance(gr, dict) or not set(_GROUPS_REQUIRED_KEYS) <= set(gr):
        problems.append("structural_groups_incomplete")
    else:
        for group in _GROUPS_REQUIRED_KEYS:
            buckets = gr.get(group)
            if not isinstance(buckets, dict):
                problems.append(
                    f"leaf_type_invalid:structural.groups.{group}")
                continue
            for bkey, dates in buckets.items():
                if not isinstance(dates, list) or any(
                        not _is_date_str(d) for d in dates):
                    problems.append(
                        f"leaf_type_invalid:structural.groups.{group}."
                        f"{bkey}")

    # R2 + R3 — bootstrap_ci grid + per-cell shape.
    expected_ci = {f"{t}|{e}|{s}|block{b}"
                   for t in tkeys for e in ENGINES for s in _SCENARIOS
                   for b in _BLOCKS}
    actual_ci = set(payload["bootstrap_ci"])
    for k in sorted(expected_ci - actual_ci):
        problems.append(f"bootstrap_ci_missing:{k}")
    for k in sorted(actual_ci - expected_ci):
        problems.append(f"bootstrap_ci_extra:{k}")
    for key in sorted(expected_ci & actual_ci):
        blk = int(key.rsplit("block", 1)[1])
        cell = payload["bootstrap_ci"][key]
        if not isinstance(cell, dict):
            problems.append(f"bootstrap_ci_cell_type:{key}")
            continue
        per_seed = cell.get("per_seed")
        # Key TYPE is deliberately not pinned: stats.bootstrap_mean_ci's
        # native return uses int seed keys, but a sealed (JSON-safe) payload
        # can only use str keys (to_formal_json hard-rejects a non-str dict
        # key) — so a payload that is ALREADY sealable must use "7"/"13"/
        # "31" string keys. Both are accepted here and normalised to the
        # seed IDENTITY (int) for the {7,13,31} comparison; only the key's
        # value, never its str/int type, is what R3 actually cares about.
        if isinstance(per_seed, dict):
            try:
                seeds = sorted(int(k) for k in per_seed)
            except (TypeError, ValueError):
                seeds = None
        else:
            seeds = None
        if seeds != [7, 13, 31]:
            problems.append(f"bootstrap_ci_seeds:{key}")
        if cell.get("quoted_seed") != 7:
            problems.append(f"bootstrap_ci_quoted_seed:{key}")
        for seed in (7, 13, 31):
            entry = None
            if isinstance(per_seed, dict):
                entry = per_seed.get(seed, per_seed.get(str(seed)))
            if not isinstance(entry, dict):
                problems.append(f"bootstrap_ci_seed_entry:{key}:{seed}")
                continue
            # non-blocking hardening: n_boot/block_len must be an actual int
            # — `10000 == 10000.0` in Python, so a bare `!=` value check lets
            # a FLOAT-typed n_boot/block_len (e.g. n_boot=10000.0) sail
            # through unnoticed; the frozen text counts resamples/days, never
            # a fractional quantity.
            n_boot_val = entry.get("n_boot")
            if (not isinstance(n_boot_val, int) or isinstance(n_boot_val, bool)
                    or n_boot_val != FROZEN_N_BOOT):
                problems.append(f"bootstrap_ci_n_boot:{key}:{seed}")
            block_len_val = entry.get("block_len")
            if (not isinstance(block_len_val, int)
                    or isinstance(block_len_val, bool)
                    or block_len_val != blk):
                problems.append(f"bootstrap_ci_block_len:{key}:{seed}")
            lo, hi = entry.get("ci_lo"), entry.get("ci_hi")
            bounds_ok = (
                isinstance(lo, (int, float)) and not isinstance(lo, bool)
                and isinstance(hi, (int, float)) and not isinstance(hi, bool)
                and math.isfinite(lo) and math.isfinite(hi) and lo <= hi)
            if not bounds_ok:
                problems.append(f"bootstrap_ci_bounds:{key}:{seed}")
        conv = cell.get("convergence")
        if (not isinstance(conv, dict)
                or not {"max_abs_ci_lo_diff", "max_abs_ci_hi_diff"}
                       <= set(conv)):
            problems.append(f"bootstrap_ci_convergence_missing:{key}")

    # R4 — oracle_daily / e2_worst_days / sizing_outputs / frequency /
    # theoretical_oracle.
    for section in ("oracle_daily", "e2_worst_days", "sizing_outputs",
                    "frequency", "theoretical_oracle"):
        if sorted(payload[section]) != tkeys:
            problems.append(f"theta_keys_mismatch:{section}")

    # frozen: S0 §7 — theoretical_oracle per-theta shape (A3): Base scenario
    # only, pooled + by_era both eras, the SAME real study.py series-block
    # shape as oracle_daily's executable matrix (value_key "daily_usd").
    for tkey in tkeys:
        to_cell = payload["theoretical_oracle"].get(tkey)
        if not isinstance(to_cell, dict):
            problems.append(f"theoretical_oracle_missing:{tkey}")
            continue
        if to_cell.get("scenario") != BASE_SCENARIO_NAME:
            problems.append(f"theoretical_oracle_scenario:{tkey}")
        _check_series_block(to_cell.get("pooled"),
                            f"theoretical_oracle|{tkey}|pooled", problems,
                            value_key="daily_usd",
                            allowed_dates=theta_unions.get(tkey))
        to_by_era = to_cell.get("by_era")
        if not isinstance(to_by_era, dict) or not set(_ERAS) <= set(to_by_era):
            problems.append(f"theoretical_oracle_by_era_missing:{tkey}")
        else:
            for era in _ERAS:
                _check_series_block(
                    to_by_era.get(era),
                    f"theoretical_oracle|{tkey}|by_era|{era}", problems,
                    value_key="daily_usd",
                    allowed_dates=theta_unions.get(tkey))

    # frozen: S0 §10.5 — frequency required-field completeness against the
    # REAL study.py `_frequency_block`/`_frequency_cell` shape (pooled +
    # by_era{PROXY,ACTUAL} + by_year{...}, each a full frequency cell).
    for tkey in tkeys:
        freq = payload["frequency"].get(tkey)
        if not isinstance(freq, dict):
            problems.append(f"frequency_missing:{tkey}")
            continue
        pooled = freq.get("pooled")
        if (not isinstance(pooled, dict)
                or not set(_FREQUENCY_CELL_FIELDS) <= set(pooled)):
            problems.append(f"frequency_cell_incomplete:{tkey}|pooled")
        else:
            _check_field_types(pooled, _FREQUENCY_CELL_FIELD_TYPES,
                               f"frequency|{tkey}|pooled", problems)
        by_era = freq.get("by_era")
        if not isinstance(by_era, dict) or not set(_ERAS) <= set(by_era):
            problems.append(f"frequency_by_era_missing:{tkey}")
        else:
            for era in _ERAS:
                cell = by_era.get(era)
                if (not isinstance(cell, dict)
                        or not set(_FREQUENCY_CELL_FIELDS) <= set(cell)):
                    problems.append(
                        f"frequency_cell_incomplete:{tkey}|by_era|{era}")
                else:
                    _check_field_types(
                        cell, _FREQUENCY_CELL_FIELD_TYPES,
                        f"frequency|{tkey}|by_era|{era}", problems)
        by_year = freq.get("by_year")
        if not isinstance(by_year, dict) or not by_year:
            problems.append(f"frequency_by_year_missing:{tkey}")
        else:
            for y, cell in by_year.items():
                if (not isinstance(cell, dict)
                        or not set(_FREQUENCY_CELL_FIELDS) <= set(cell)):
                    problems.append(
                        f"frequency_cell_incomplete:{tkey}|by_year|{y}")
                else:
                    _check_field_types(
                        cell, _FREQUENCY_CELL_FIELD_TYPES,
                        f"frequency|{tkey}|by_year|{y}", problems)

    for tkey in tkeys:
        for scn in _SCENARIOS:
            eng_block = payload["e2_worst_days"].get(tkey, {})
            cell = (eng_block.get(scn) if isinstance(eng_block, dict)
                    else None)
            if not isinstance(cell, dict):
                problems.append(f"e2_worst_days_missing:{tkey}|{scn}")
                continue
            pooled = cell.get("pooled")
            if (not isinstance(pooled, dict) or "P1" not in pooled
                    or "P5" not in pooled):
                problems.append(f"e2_worst_days_pooled:{tkey}|{scn}")
            by_era = cell.get("by_era")
            if (not isinstance(by_era, dict)
                    or sorted(by_era) != sorted(_ERAS)):
                problems.append(f"e2_worst_days_by_era:{tkey}|{scn}")
            else:
                for era in _ERAS:
                    era_cell = by_era.get(era, {})
                    if (not isinstance(era_cell, dict)
                            or "P1" not in era_cell or "P5" not in era_cell):
                        problems.append(
                            f"e2_worst_days_by_era_p1p5:{tkey}|{scn}|{era}")

    for tkey in tkeys:
        cell = payload["sizing_outputs"].get(tkey, {})
        for label in ("rows", "coverage"):
            block = cell.get(label) if isinstance(cell, dict) else None
            if not isinstance(block, dict):
                problems.append(f"sizing_outputs_{label}_missing:{tkey}")
                continue
            for eng in ENGINES:
                eng_block = block.get(eng)
                if not isinstance(eng_block, dict):
                    problems.append(
                        f"sizing_outputs_{label}_cell_missing:{tkey}|{eng}")
                    continue
                for scn in _SCENARIOS:
                    if scn not in eng_block:
                        problems.append(
                            f"sizing_outputs_{label}_cell_missing:"
                            f"{tkey}|{eng}|{scn}")

    # frozen: S0 §8 — sizing_outputs required-field completeness against
    # the REAL study.py `_sizing_row`/`_coverage` shapes.
    for tkey in tkeys:
        cell = payload["sizing_outputs"].get(tkey, {})
        rows_block = cell.get("rows") if isinstance(cell, dict) else None
        cov_block = cell.get("coverage") if isinstance(cell, dict) else None
        for eng in ENGINES:
            for scn in _SCENARIOS:
                if isinstance(rows_block, dict):
                    eng_rows = rows_block.get(eng)
                    rows = (eng_rows.get(scn)
                           if isinstance(eng_rows, dict) else None)
                    if isinstance(rows, list):
                        for i, row in enumerate(rows):
                            if (not isinstance(row, dict)
                                    or not set(_SIZING_ROW_FIELDS)
                                           <= set(row)):
                                problems.append(
                                    f"sizing_outputs_row_incomplete:"
                                    f"{tkey}|{eng}|{scn}:{i}")
                            else:
                                _check_field_types(
                                    row, _SIZING_ROW_FIELD_TYPES,
                                    f"sizing_outputs|{tkey}|{eng}|{scn}|"
                                    f"rows[{i}]", problems)
                if isinstance(cov_block, dict):
                    eng_cov = cov_block.get(eng)
                    cov = (eng_cov.get(scn)
                          if isinstance(eng_cov, dict) else None)
                    if isinstance(cov, dict):
                        by_budget = cov.get("by_budget_usd")
                        if (not isinstance(by_budget, dict)
                                or not set(_COVERAGE_BUDGETS)
                                       <= set(by_budget)):
                            problems.append(
                                f"sizing_outputs_coverage_incomplete:"
                                f"{tkey}|{eng}|{scn}")

    # mission M6.1.2-S3 item 6b — SIZING NON-EMPTINESS via the REAL producer
    # relation: study.py builds `sizing_rows[engine][scenario]` as ONE row
    # per trade-constructible day that is ALSO in that theta's tp_set
    # (`rows = [_sizing_row(...) for rec in trade_records[engine][name] if
    # rec.trade_date in tp_set]`, s0/study.py `build_study`) — every engine x
    # scenario shares the SAME `usable` day population, so this count is
    # EXACTLY that theta's day_universe["n_tp"], never merely "some rows
    # present". A count that drifts (including down to zero while n_tp>0,
    # i.e. an emptied rows list) is refused.
    for tkey in tkeys:
        tcell_rows = payload["oracle_daily"].get(tkey)
        du_rows = (tcell_rows.get("day_universe")
                  if isinstance(tcell_rows, dict) else None)
        n_tp_for_rows = (du_rows.get("n_tp")
                        if isinstance(du_rows, dict) else None)
        if (not isinstance(n_tp_for_rows, int)
                or isinstance(n_tp_for_rows, bool) or n_tp_for_rows < 0):
            continue        # day_universe_field_invalid already reported
        rows_block = payload["sizing_outputs"].get(tkey, {})
        rows_block = (rows_block.get("rows")
                     if isinstance(rows_block, dict) else None)
        if not isinstance(rows_block, dict):
            continue         # sizing_outputs_rows_missing already reported
        for eng in ENGINES:
            eng_rows = rows_block.get(eng)
            for scn in _SCENARIOS:
                rows = (eng_rows.get(scn)
                       if isinstance(eng_rows, dict) else None)
                if not isinstance(rows, list):
                    continue    # sizing_outputs_rows_cell_missing reported
                if len(rows) != n_tp_for_rows:
                    problems.append(
                        "sizing_outputs_rows_count_mismatch:"
                        f"{tkey}|{eng}|{scn}:{len(rows)}!={n_tp_for_rows}")

    # R5 — stability_views (M6_HOLD_RESPONSE.md item 3 / frozen S0 §2).
    for tkey in tkeys:
        for eng in ENGINES:
            for scn in _SCENARIOS:
                eng_block = payload["stability_views"].get(tkey, {})
                eng_block = (eng_block.get(eng)
                            if isinstance(eng_block, dict) else None)
                cell = (eng_block.get(scn) if isinstance(eng_block, dict)
                        else None)
                if not isinstance(cell, dict):
                    problems.append(
                        f"stability_views_missing:{tkey}|{eng}|{scn}")
                    continue
                epochs = cell.get("epochs")
                # structural extras allowed: outside_epochs bucket (days
                # beyond the three frozen epochs, disclosed not dropped)
                # and the per-axis conservation flag.
                if (not isinstance(epochs, dict)
                        or not set(_EPOCHS) <= set(epochs)
                        or not set(epochs) <= (set(_EPOCHS)
                                               | {"outside_epochs",
                                                  "conservation_ok"})):
                    problems.append(
                        f"stability_views_epochs:{tkey}|{eng}|{scn}")
                by_year = cell.get("by_year")
                if not by_year:
                    problems.append(
                        f"stability_views_by_year:{tkey}|{eng}|{scn}")
                loyo = cell.get("leave_one_year_out")
                if not loyo:
                    problems.append(
                        f"stability_views_loyo:{tkey}|{eng}|{scn}")
                by_dir = cell.get("by_direction")
                if (not isinstance(by_dir, dict)
                        or not set(_DIRECTIONS) <= set(by_dir)
                        or not set(by_dir) <= (set(_DIRECTIONS)
                                               | {"conservation_ok"})):
                    problems.append(
                        f"stability_views_by_direction:{tkey}|{eng}|{scn}")

                # mission item 6: every PARTITIONING axis's conservation_ok
                # must be LITERALLY True — previously only the axis's KEY
                # SET was checked above, never the flag's own VALUE, so a
                # False (or missing) flag sailed through silently.
                for axis_name, axis_dict in (
                        ("epochs", epochs), ("by_year", by_year),
                        ("leave_one_year_out", loyo),
                        ("by_direction", by_dir)):
                    if (not isinstance(axis_dict, dict)
                            or axis_dict.get("conservation_ok") is not True):
                        problems.append(
                            "stability_views_conservation_not_true:"
                            f"{tkey}|{eng}|{scn}|{axis_name}")

                vol = cell.get("vol_terciles")
                if not isinstance(vol, dict):
                    problems.append(
                        f"stability_views_vol_terciles:{tkey}|{eng}|{scn}")
                elif vol.get("status") == "unresolved":
                    # frozen S0 §2 vol axis blocked on DR-M6-B — sealing
                    # must fail closed until the sub-definition ruling lands.
                    problems.append("vol_axis_unresolved")
                else:
                    # RESOLVED (mission item 6): the complete stratum set is
                    # the three opaque-vocabulary terciles PLUS the reserved
                    # vol_na bucket (stability.py's VOL_NA_BUCKET), and the
                    # axis's own conservation_ok literally True — a
                    # vocabulary-agnostic count check, never a hardcoded
                    # tercile-name list (DR-M6-B is still open).
                    if vol.get("conservation_ok") is not True:
                        problems.append(
                            "stability_views_conservation_not_true:"
                            f"{tkey}|{eng}|{scn}|vol_terciles")
                    if "vol_na" not in vol:
                        problems.append(
                            f"stability_views_vol_na_missing:"
                            f"{tkey}|{eng}|{scn}")
                    tercile_keys = set(vol) - {"vol_na", "conservation_ok"}
                    if len(tercile_keys) != 3:
                        problems.append(
                            "stability_views_vol_tercile_count:"
                            f"{tkey}|{eng}|{scn}:{sorted(tercile_keys)}")

                # frozen: S0 §2 — required-field completeness AND leaf-level
                # value-type checks of the real stability.py `_cell()`
                # descriptive shape, checked on every real bucket of every
                # partitioning axis INCLUDING vol_terciles's own resolved
                # strata (bookkeeping keys like "conservation_ok"/"status"/
                # "reason" are not cells and are skipped).
                vol_buckets = vol if isinstance(vol, dict) else {}
                for axis_name, buckets in (
                        ("epochs", epochs),
                        ("by_year", by_year),
                        ("leave_one_year_out", loyo),
                        ("by_direction", by_dir),
                        ("vol_terciles", vol_buckets)):
                    if not isinstance(buckets, dict):
                        continue
                    for bkey, bval in buckets.items():
                        if bkey in (_STABILITY_AXIS_BOOKKEEPING_KEYS
                                   | {"status", "reason"}):
                            continue
                        if (not isinstance(bval, dict)
                                or not set(_STABILITY_CELL_FIELDS)
                                       <= set(bval)):
                            problems.append(
                                f"stability_views_cell_incomplete:"
                                f"{tkey}|{eng}|{scn}|{axis_name}|{bkey}")
                        else:
                            _check_field_types(
                                bval, _STABILITY_CELL_FIELD_TYPES,
                                f"stability_views|{tkey}|{eng}|{scn}|"
                                f"{axis_name}|{bkey}", problems)

    # mission M6.1.2-S3 item 1 — STABILITY CONSERVATION RE-DERIVED, never
    # merely read off the axis's own self-reported "conservation_ok" flag.
    # stability.py's `_engine_scenario_view` slices ONE theta's D_TP series
    # (`per_theta_block["d_tp"][engine][scenario]`, len == that theta's
    # day_universe["n_tp"] — s0/study.py: `d_tp[engine][name] = {d: pnl[d]
    # for d in tp_days}`) along four axes; the TRUE invariant per
    # stability.py's own conservation-discipline docstring is:
    #   epochs / by_direction / vol_terciles (resolved) — sum(cell["n"] over
    #     every REAL bucket, "outside_epochs"/"vol_na" INCLUDED, only the
    #     bookkeeping "conservation_ok" key excluded) == n_tp;
    #   by_year — same total, since by_year is a partition of the SAME
    #     series (frozen S0 §2 按年表格（强制）);
    #   leave_one_year_out — NOT a partition (each bucket is the complement
    #     of one year): loyo[y]["n"] == n_tp - by_year[y]["n"] for every y
    #     (stability.py `_loyo_axis`'s own check, re-derived here rather
    #     than trusted).
    # A payload whose "conservation_ok" reads True on every axis while the
    # actual n's do not sum this way is refused — the defect class this
    # hardening closes.
    for tkey in tkeys:
        tcell_stab = payload["oracle_daily"].get(tkey)
        du_stab = (tcell_stab.get("day_universe")
                  if isinstance(tcell_stab, dict) else None)
        n_tp_stab = du_stab.get("n_tp") if isinstance(du_stab, dict) else None
        if (not isinstance(n_tp_stab, int) or isinstance(n_tp_stab, bool)
                or n_tp_stab < 0):
            continue        # day_universe_field_invalid already reported
        for eng in ENGINES:
            for scn in _SCENARIOS:
                eng_block = payload["stability_views"].get(tkey, {})
                eng_block = (eng_block.get(eng)
                            if isinstance(eng_block, dict) else None)
                cell = (eng_block.get(scn) if isinstance(eng_block, dict)
                        else None)
                if not isinstance(cell, dict):
                    continue     # stability_views_missing already reported

                epochs, by_year = cell.get("epochs"), cell.get("by_year")
                by_dir, vol = cell.get("by_direction"), cell.get("vol_terciles")
                for axis_name, axis_dict in (
                        ("epochs", epochs), ("by_direction", by_dir)):
                    total = _stability_axis_n_sum(axis_dict)
                    if total is not None and total != n_tp_stab:
                        problems.append(
                            "stability_views_conservation_recompute_"
                            f"mismatch:{tkey}|{eng}|{scn}|{axis_name}:"
                            f"{total}!={n_tp_stab}")
                if isinstance(vol, dict) and vol.get("status") != "unresolved":
                    total = _stability_axis_n_sum(vol)
                    if total is not None and total != n_tp_stab:
                        problems.append(
                            "stability_views_conservation_recompute_"
                            f"mismatch:{tkey}|{eng}|{scn}|vol_terciles:"
                            f"{total}!={n_tp_stab}")
                by_year_total = _stability_axis_n_sum(by_year)
                if by_year_total is not None and by_year_total != n_tp_stab:
                    problems.append(
                        "stability_views_conservation_recompute_"
                        f"mismatch:{tkey}|{eng}|{scn}|by_year:"
                        f"{by_year_total}!={n_tp_stab}")

                loyo = cell.get("leave_one_year_out")
                if isinstance(by_year, dict) and isinstance(loyo, dict):
                    for y, by_year_cell in by_year.items():
                        if y in _STABILITY_AXIS_BOOKKEEPING_KEYS:
                            continue
                        by_year_n = (by_year_cell.get("n")
                                    if isinstance(by_year_cell, dict)
                                    else None)
                        loyo_cell = loyo.get(y)
                        loyo_n = (loyo_cell.get("n")
                                 if isinstance(loyo_cell, dict) else None)
                        if (not isinstance(by_year_n, int)
                                or isinstance(by_year_n, bool)
                                or not isinstance(loyo_n, int)
                                or isinstance(loyo_n, bool)):
                            continue
                        expected_loyo_n = n_tp_stab - by_year_n
                        if loyo_n != expected_loyo_n:
                            problems.append(
                                "stability_views_loyo_recompute_mismatch:"
                                f"{tkey}|{eng}|{scn}|{y}:"
                                f"{loyo_n}!={expected_loyo_n}")

    # A10 — era_axis: all-tables era-axis declaration (frozen S0 §6), against
    # the REAL s0_real_run.py shape: `axes` is EXACTLY the two frozen era-axis
    # NAMES (never a superset/subset/renamed key), `counterfactual_
    # disclosure` a non-empty disclosure string.
    ea = payload["era_axis"]
    axes = ea.get("axes")
    if not isinstance(axes, list) or set(axes) != set(_ERAS):
        problems.append("era_axis_axes_incomplete")
    elif len(axes) != len(_ERAS):
        # non-blocking hardening: `set(axes) == set(_ERAS)` alone is blind to
        # a DUPLICATE entry (e.g. [PROXY, PROXY, ACTUAL]) — the set collapses
        # it away — so a repeated era name needs its own length check.
        problems.append("era_axis_axes_duplicate")
    disc = ea.get("counterfactual_disclosure")
    if not isinstance(disc, str) or not disc.strip():
        problems.append("era_axis_counterfactual_disclosure_missing")

    # R6 — disclosures.pending_method_decisions: the key MUST EXIST and MUST
    # be empty to seal — a MISSING key and a NON-EMPTY value are distinct
    # problems (a validator that treats "absent" and "empty" the same way
    # can't tell "nothing pends" from "the producer forgot to disclose").
    disclosures = payload["disclosures"]
    if "pending_method_decisions" not in disclosures:
        problems.append("pending_method_decisions_missing")
    elif disclosures["pending_method_decisions"]:
        problems.append("pending_method_decisions_unresolved")

    # A11 — na_conservation restatement (mission item 8 / contract §A11 "NA
    # 守恒复述"): a `na_conservation` sub-block MUST exist and carry the
    # reported total NA per table plus a LITERAL True conservation flag.
    # NOT populated by any current producer (scripts/s0_real_run.py
    # build_full_study_result never emits this key) — see this module's
    # docstring for the exact minimal shape the producer must add.
    nac = disclosures.get("na_conservation")
    if not isinstance(nac, dict):
        problems.append("disclosures_na_conservation_missing")
    else:
        totals = nac.get("per_table_total_na")
        totals_ok = (isinstance(totals, dict)
                    and set(_NA_CONSERVATION_TABLES) <= set(totals)
                    and all(_is_int(totals.get(k)) and totals.get(k) >= 0
                           for k in _NA_CONSERVATION_TABLES))
        if not totals_ok:
            problems.append("disclosures_na_conservation_totals_invalid")
        if nac.get("conservation_ok") is not True:
            problems.append("disclosures_na_conservation_flag_not_true")

        # mission M6.1.2-S3 item 4 — A11 RECONCILIATION: `per_table_total_
        # na[t]` is a RESTATEMENT of structural.na_table's own per-field NA
        # counts (dataset.py `build_na_table`: na_table["per_field"][table]
        # [field]["na"]) — it must equal the ACTUAL sum derivable from that
        # table, never merely be a well-typed non-negative int on its own
        # (a totals block that reads {"features": 0, "labels": 0} while
        # na_table shows real NA rows is exactly the "self-reported number,
        # never re-derived" defect class this hardening closes).
        if totals_ok:
            st_for_recon = payload.get("structural")
            nat_for_recon = (st_for_recon.get("na_table")
                            if isinstance(st_for_recon, dict) else None)
            per_field_for_recon = (nat_for_recon.get("per_field")
                                   if isinstance(nat_for_recon, dict)
                                   else None)
            if isinstance(per_field_for_recon, dict):
                for table in _NA_CONSERVATION_TABLES:
                    rows = per_field_for_recon.get(table)
                    if not isinstance(rows, dict):
                        continue
                    na_values = [row.get("na") for row in rows.values()
                                if isinstance(row, dict)]
                    if not all(_is_int(v) for v in na_values):
                        continue    # structural_na_table_row_* reports this
                    actual_total = sum(na_values)
                    reported_total = totals.get(table)
                    if reported_total != actual_total:
                        problems.append(
                            "disclosures_na_conservation_total_mismatch:"
                            f"{table}:{reported_total}!={actual_total}")

    # R7 — governance.
    gov = payload["governance"]
    trial_id = gov.get("trial_id")
    if not isinstance(trial_id, str) or not trial_id:
        problems.append("governance_trial_id")
    commit = gov.get("authorized_commit")
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}",
                                                        commit or ""):
        problems.append("governance_authorized_commit")
    seed = gov.get("engineering_seed")
    if not isinstance(seed, int) or isinstance(seed, bool):
        problems.append("governance_engineering_seed")
    hashes = gov.get("frozen_hashes")
    if not isinstance(hashes, dict) or len(hashes) != 7:
        problems.append("governance_frozen_hashes_count")
    else:
        for hpath, hval in hashes.items():
            if (not isinstance(hpath, str) or not isinstance(hval, str)
                    or not re.fullmatch(r"[0-9a-f]{64}", hval)):
                problems.append(f"governance_frozen_hash_format:{hpath}")
    seq = gov.get("registry_sequence_snapshot")
    if not isinstance(seq, int) or isinstance(seq, bool) or seq < 1:
        problems.append("governance_registry_sequence_snapshot")

    # governance CONTEXT cross-check (M6.1 seal-boundary finding): a
    # payload can be internally well-formed (every format check above
    # passes) while its embedded governance block is STALE or fabricated
    # relative to reality — e.g. a fake frozen_hashes entry, or a commit
    # that does not match the CURRENT registry authorization. Formal
    # sealing REQUIRES an independently-derived `expected_governance` to
    # compare against; not supplying one is itself a problem, never a
    # silent pass (packet §0-5).
    if not isinstance(expected_governance, Mapping):
        problems.append("governance_context_not_supplied")
    else:
        for field in ("trial_id", "authorized_commit", "engineering_seed",
                     "registry_sequence_snapshot"):
            if gov.get(field) != expected_governance.get(field):
                problems.append(f"governance_mismatch:{field}")
        if gov.get("frozen_hashes") != expected_governance.get("frozen_hashes"):
            problems.append("governance_mismatch:frozen_hashes")

    # R9 — mc_handoff_manifest counts grid. NOTE: only the "counts" sub-key
    # is inspected here — a "files" sub-key (added by the renderer AFTER
    # this payload seals, see the two-call contract in this function's
    # docstring) is never inspected and never rejected, so this validator
    # is safe to call again on the manifest-injected payload.
    counts = payload["mc_handoff_manifest"].get("counts")
    if not isinstance(counts, dict):
        problems.append("mc_handoff_manifest_counts_missing")
    else:
        for eng in ENGINES:
            eng_block = counts.get(eng)
            for scn in _SCENARIOS:
                cell = (eng_block.get(scn) if isinstance(eng_block, dict)
                        else None)
                if not isinstance(cell, dict) or "n_records" not in cell:
                    problems.append(
                        f"mc_handoff_manifest_counts_missing:{eng}|{scn}")
                    continue
                n = cell["n_records"]
                if not isinstance(n, int) or isinstance(n, bool) or n < 0:
                    problems.append(
                        f"mc_handoff_manifest_counts_invalid:{eng}|{scn}")

    # R10 — feasibility_grid: exact (theta, engine, scenario) cell coverage
    # (frozen: Appendix A grid) + per-cell field completeness against the
    # REAL gridmix.py `build_grid` return shape.
    fg = payload["feasibility_grid"]
    cells = fg.get("cells")
    expected_cells = {f"{t}|{e}|{s}" for t in tkeys for e in ENGINES
                      for s in _SCENARIOS}
    if not isinstance(cells, dict) or not cells:
        problems.append("feasibility_grid_cells_empty")
    else:
        actual_cells = set(cells)
        for k in sorted(expected_cells - actual_cells):
            problems.append(f"feasibility_grid_missing:{k}")
        for k in sorted(actual_cells - expected_cells):
            problems.append(f"feasibility_grid_extra:{k}")
        for k in sorted(expected_cells & actual_cells):
            _check_feasibility_cell(cells[k], k, problems)
    if fg.get("regions", {}).get("status") != "pending_mc":
        problems.append("feasibility_grid_regions_not_pending_mc")

    # R8 — whole-payload walk (runs last so the section-shape problems above
    # are reported with their own, more specific codes first).
    _walk_r8(payload, "$", problems)

    # A9 record-count conservation: mc_handoff_manifest counts per engine x
    # scenario must equal n_tp + n_fp for EVERY frozen theta (every theta's
    # TP/FP partition covers the SAME trade-constructible population, so
    # this identity holds for both thetas simultaneously — frozen App A).
    # The executable-matrix completeness itself is R-EXEC above, now
    # UNCONDITIONAL; this block is the count arithmetic only.
    mh_counts = payload["mc_handoff_manifest"].get("counts", {})
    for tkey in tkeys:
        uni = payload["oracle_daily"].get(tkey, {}).get("day_universe", {})
        n_exp = None
        if isinstance(uni, dict):
            try:
                n_exp = int(uni["n_tp"]) + int(uni["n_fp"])
            except Exception:
                n_exp = None
        if n_exp is None:
            continue
        for eng in ENGINES:
            for scn in _SCENARIOS:
                # defensive at every level (mission item 1/9): a mutated
                # counts[eng] or counts[eng][scn] that is not itself a dict
                # (None, a list, ...) must degrade to "no count on record"
                # here, never an AttributeError — this validator must never
                # crash on a malformed payload.
                eng_counts = (mh_counts.get(eng)
                             if isinstance(mh_counts, dict) else None)
                scn_counts = (eng_counts.get(scn)
                             if isinstance(eng_counts, dict) else None)
                n_rec = (scn_counts.get("n_records")
                         if isinstance(scn_counts, dict) else None)
                if n_rec != n_exp:
                    problems.append(
                        f"records_conservation:{tkey}|{eng}|{scn}:"
                        f"{n_rec}!={n_exp}")
    return problems


# FROZEN §10.1 names every sealed JSONL line must carry (leak check).
_FROZEN_LINE_FIELDS: tuple[str, ...] = ("entry_timestamp",
                                        "exit_timestamp", "trade_date")
# Internal names that must NEVER appear on a sealed line (leak check).
_INTERNAL_NAME_LEAK: tuple[str, ...] = ("entry_ts", "exit_ts")


def validate_sealed_files(files: Mapping[str, str], payload, *,
                          trade_date_universe=None) -> list[str]:
    """Verify the sealed JSONL bodies against `payload["mc_handoff_manifest"]
    ["files"]` (name -> {"file", "n_records", "sha256"}) — the SECOND half
    of the M6.1 seal-boundary gate. `validate_formal_payload` alone cannot
    catch a defect that only exists in the actual sealed bytes (they do not
    exist until the renderer serializes them); this function is what does,
    and it must be called on the SAME manifest-injected payload that the
    renderer's second `validate_formal_payload` call also inspects (see
    that function's docstring for the full two-call contract).

    Checks (S0_REPORT_CONTENT_CONTRACT.md A9 + M6.1 findings):
      * manifest file-KEY SET is EXACTLY {E1,E2} x {Base,Conservative,
        Stress,Severe} — 8 keys, no fewer/more/renamed;
      * per manifest entry: the named file exists in `files`; its sha256
        (of the UTF-8 bytes) matches; its LINE COUNT (`str.splitlines()` —
        correct with or without a trailing newline, unlike a bare
        `str.split("\\n")` which off-by-ones on a trailing newline) equals
        BOTH the manifest's own `n_records` AND
        `payload["mc_handoff_manifest"]["counts"][eng][scn]["n_records"]`
        (a triple equality: manifest vs actual bytes vs the formal
        payload's own record-count section — a payload-only check can
        never see the first two, and a bytes-only check can never see the
        third);
      * every line parses as a JSON object whose field set is EXACTLY
        `FORMAL_RECORD_FIELDS` (missing/extra -> problem, on top of the
        FROZEN §10.1 name-specific check below), and whose `engine` /
        `cost_scenario` equal the file's OWN eng/scn (parsed from the
        manifest key "eng|scn") — a line that quietly belongs to the wrong
        file is never accepted;
      * an internal `entry_ts`/`exit_ts` name anywhere on a line is a leak,
        never silently accepted as a synonym for entry_timestamp/
        exit_timestamp;
      * per FILE (not pooled across files), no duplicate `trade_date`;
      * per FILE, the trade_date SET is EXACTLY the union, across every
        theta in `payload["oracle_daily"]`, of that theta's TP ∪ FP day
        universe (`day_universe["tp_days"]`/`["fp_days"]`) — every engine x
        scenario trades the SAME trade-constructible population, so a
        MISSING day, an EXTRA day, and a same-count REPLACED day (one date
        swapped for another — invisible to a count-only check) are all
        flagged.

    `trade_date_universe`: normally omitted (default `None`), in which case
    the day-set is derived from `payload["oracle_daily"]` as described
    above — this is now the MANDATORY default behaviour (the M6.1 relaxation
    that made this an opt-in, caller-supplied, pooled-only check is
    removed). An explicit iterable of "YYYY-MM-DD" strings OVERRIDES that
    derivation, for a caller validating a narrower payload that carries no
    `oracle_daily` section at all.
    """
    problems: list[str] = []
    manifest = (payload.get("mc_handoff_manifest", {})
               if isinstance(payload, dict) else {})
    file_specs = manifest.get("files") if isinstance(manifest, dict) else None
    if not isinstance(file_specs, dict) or not file_specs:
        return ["mc_handoff_manifest_files_missing"]

    expected_keys = {f"{e}|{s}" for e in ENGINES for s in _SCENARIOS}
    got_keys = set(file_specs)
    if got_keys != expected_keys:
        problems.append(
            "mc_handoff_manifest_files_key_set_mismatch:"
            f"missing={sorted(expected_keys - got_keys)}:"
            f"extra={sorted(got_keys - expected_keys)}")

    if trade_date_universe is not None:
        universe = set(trade_date_universe)
    else:
        od = payload.get("oracle_daily", {}) if isinstance(payload, dict) \
            else {}
        universe = {
            d for tcell in (od.values() if isinstance(od, dict) else ())
            if isinstance(tcell, dict)
            for grp in ("tp_days", "fp_days")
            for d in ((tcell.get("day_universe") or {}).get(grp) or ())
        }

    counts = manifest.get("counts", {}) if isinstance(manifest, dict) else {}

    for name, spec in file_specs.items():
        eng, sep, scn = name.partition("|")
        if not sep:
            problems.append(f"sealed_file_spec_key_format:{name}")
            eng = scn = None
        if not isinstance(spec, dict):
            problems.append(f"sealed_file_spec_type:{name}")
            continue
        fname = spec.get("file")
        want_sha = spec.get("sha256")
        want_n = spec.get("n_records")
        if fname not in files:
            problems.append(f"sealed_file_missing:{name}:{fname}")
            continue
        body = files[fname]
        got_sha = hashlib.sha256(body.encode("utf-8")).hexdigest()
        if got_sha != want_sha:
            problems.append(f"sealed_file_sha256_mismatch:{name}")
        lines = body.splitlines() if body else []
        if len(lines) != want_n:
            problems.append(
                f"sealed_file_line_count_mismatch:{name}:"
                f"{len(lines)}!={want_n}")
        if eng is not None:
            eng_counts = counts.get(eng) if isinstance(counts, dict) else None
            scn_counts = (eng_counts.get(scn)
                         if isinstance(eng_counts, dict) else None)
            n_counts = (scn_counts.get("n_records")
                       if isinstance(scn_counts, dict) else None)
            if n_counts != want_n:
                problems.append(
                    f"sealed_file_counts_mismatch:{name}:"
                    f"{n_counts}!={want_n}")

        per_file_dates: list[str] = []
        for i, line in enumerate(lines):
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                problems.append(f"sealed_file_line_not_json:{name}:{i}")
                continue
            if not isinstance(rec, dict):
                problems.append(f"sealed_file_line_not_object:{name}:{i}")
                continue
            for field in _FROZEN_LINE_FIELDS:
                if field not in rec:
                    problems.append(
                        f"sealed_file_line_missing_field:{name}:{i}:{field}")
            got_fields, want_fields = set(rec), set(FORMAL_RECORD_FIELDS)
            if got_fields != want_fields:
                problems.append(
                    f"sealed_file_line_field_set_mismatch:{name}:{i}:"
                    f"missing={sorted(want_fields - got_fields)}:"
                    f"extra={sorted(got_fields - want_fields)}")
            leaked = [f for f in _INTERNAL_NAME_LEAK if f in rec]
            if leaked:
                problems.append(
                    f"sealed_file_line_internal_name_leak:{name}:{i}:"
                    f"{leaked}")
            # mission M6.1.2-S3 item 2 — SEALED-RECORD LEAF TYPES: the field
            # SET check above never inspected each field's VALUE, so a
            # numeric string ("20000.0" for entry_fill, "1" for direction)
            # sailed through unnoticed on an otherwise complete line. Checked
            # on every PRESENT field regardless of the field-set outcome
            # above (a present-but-wrong-typed field is its own defect).
            for field, predicate in _SEALED_RECORD_FIELD_TYPES.items():
                if field in rec and not predicate(rec[field]):
                    problems.append(
                        f"sealed_file_line_field_type_invalid:{name}:{i}:"
                        f"{field}")
            if eng is not None:
                if rec.get("engine") != eng:
                    problems.append(
                        f"sealed_file_line_engine_mismatch:{name}:{i}:"
                        f"{rec.get('engine')!r}!={eng!r}")
                if rec.get("cost_scenario") != scn:
                    problems.append(
                        f"sealed_file_line_scenario_mismatch:{name}:{i}:"
                        f"{rec.get('cost_scenario')!r}!={scn!r}")
            trade_date = rec.get("trade_date")
            if isinstance(trade_date, str):
                per_file_dates.append(trade_date)

        dupes = sorted({d for d in per_file_dates
                        if per_file_dates.count(d) > 1})
        if dupes:
            problems.append(f"sealed_file_duplicate_trade_date:{name}:{dupes}")

        # UNCONDITIONAL (mission item 4): even an EMPTY day universe (e.g. a
        # payload whose oracle_daily tp/fp lists are all empty) must still
        # be compared against the file's own date set — a prior `if
        # universe:` guard here would give a non-empty file a free pass
        # whenever the universe happened to be empty.
        file_dates = set(per_file_dates)
        missing = sorted(universe - file_dates)
        extra = sorted(file_dates - universe)
        if missing:
            problems.append(
                f"sealed_file_missing_trade_dates:{name}:{missing}")
        if extra:
            problems.append(
                f"sealed_file_extra_trade_dates:{name}:{extra}")

    # mission M6.1.2-S3 item 8 — SEALED-FILE COMPLETENESS: the renderer
    # (scripts/s0_real_run.py::render_s0_report) now stamps
    # `mc_handoff_manifest["sealed_files"]` = {filename: {"sha256": <64hex>,
    # "bytes": <int>}} covering EVERY file it writes EXCEPT S0_REPORT.json
    # itself (listed under `"self_excluded"` — it carries the manifest, so
    # it cannot hash itself; Stage F's chain seal covers it separately).
    # The OLD gate above only ever looks at the 8 canonical MC_HANDOFF
    # {engine}|{scenario} keys via `file_specs`/`counts` — an EXTRA planted
    # file (e.g. a stray artifact with no integrity entry at all) or an
    # entry whose sha256/bytes drifted from the ACTUAL bytes is invisible to
    # it. This reconciles the two independently.
    sealed_files = manifest.get("sealed_files") if isinstance(manifest, dict) \
        else None
    if not isinstance(sealed_files, dict):
        problems.append("sealed_files_manifest_missing")
    else:
        self_excluded = set(manifest.get("self_excluded") or [])
        for fname, spec in sealed_files.items():
            if fname not in files:
                problems.append(
                    f"sealed_files_manifest_entry_missing_file:{fname}")
                continue
            if not isinstance(spec, dict):
                problems.append(f"sealed_files_manifest_entry_type:{fname}")
                continue
            body_bytes = files[fname].encode("utf-8")
            got_sha = hashlib.sha256(body_bytes).hexdigest()
            if spec.get("sha256") != got_sha:
                problems.append(
                    f"sealed_files_manifest_sha256_mismatch:{fname}")
            if spec.get("bytes") != len(body_bytes):
                problems.append(
                    f"sealed_files_manifest_bytes_mismatch:{fname}")
        uncovered = sorted(set(files) - set(sealed_files) - self_excluded)
        if uncovered:
            problems.append(
                "sealed_files_manifest_incomplete:" + ",".join(uncovered))

    return problems
