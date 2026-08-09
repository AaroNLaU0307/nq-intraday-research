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

M6.1.3-S1 hardening (closing the "trust the tree's own claims" class at
this boundary): (1) a module-level SCHEMA MATRIX for every A1-A12 section
(§1e below) — an UNKNOWN key inside a section is now a problem
(`*_unknown_key`), with the allowed set traced to the real producer
function that emits it, never guessed; this includes the top-level payload
itself (an extra key beyond `FORMAL_SECTIONS` was previously invisible to
R1). (2) Appendix A grid hardening: n_tp_target/n_fp_target/F_expected are
RECOMPUTED via gridmix's own frozen arithmetic
(`floor_n_tp`/`n_fp_for`/`f_expected`, F == p*r*N/q against the SAME theta's
`frequency.pooled.continuation_base_rate_p`), realized_precision/recall/
n_tp_actual/n_fp_actual are recomputed from each seed's own tp_dates/
fp_dates, an infeasible point must carry `infeasible_reason`, and the
per-seed field set is the FULL real 13-key `_seed_report` shape (was a
6-key required subset). (3) bootstrap_ci: "mean" is now leaf-typed AND
cross-seed-consistency-checked (all three seeds resample the same series,
so their sample mean can never differ), and an optional "quoted" block, if
present, must equal `per_seed[7]` verbatim. (4) P1 <= P5 is now checked as
a numeric-ordering invariant everywhere a worst-day percentile pair
appears — independent of, and never approving, the disclosed-but-
RULED numpy linear-interpolation ESTIMATOR (DR-8, 2026-08-10). (5) A4
e2_worst_days now carries a mandatory `estimator_status`; sealing REQUIRES
it read exactly "resolved" — the real producer's default posture (DR-M6-H
open, no config resolves `worst_day_estimator`) emits
"unresolved_DR-M6-H", and this boundary fail-closes on it
(`worst_day_estimator_unresolved`) rather than silently sealing an
unapproved P1/P5 estimator into a formal release. (6) `validate_sealed_
files`' `self_excluded` is capped to the module-internal frozen constant
`_ALLOWED_SELF_EXCLUDED = ("S0_REPORT.json",)` — a payload naming anything
else there no longer buys a bypass around the item-8 completeness
reconciliation (and a non-list self_excluded degrades to a problem instead
of silently iterating as a string of characters). (7) `reconcile_with_
internal(internal, formal) -> list[str]` — a NEW pure function (not wired
into any sealing gate by this module) that cross-checks the formal payload
against the RAW internal producer envelope (`scripts/s0_real_run.py::
build_full_study_result`'s own return dict — dataset/records/study, never
`split_envelope`'s "internal" half, which drops "study"): stability_views
per-bucket stats recomputed from `study[...]["d_tp"]` + a day_meta derived
from `internal["dataset"].records`; oracle_daily executable series values
compared against that same `d_tp` series; mc_handoff_manifest record
counts against `len(records[eng][scn])`; na_conservation totals against
`internal["reported_total_na"]`. Requires "study"/"records" (dataset/
reported_total_na unlock two further checks each) — passing the FORMAL
payload itself as `internal` can never vacuously succeed, since none of
those keys are ever `FORMAL_SECTIONS` members. See tests/test_s0_report.py
for the exact fixture-derivation and the cross-field-synchronized-
tampering worked example these hardenings close.
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


# ---------------------------------------------------------------------------
# 1b-0. M6.1.4-S1 NEVER-CRASH PRIMITIVES (Codex RC-1 fix round).
#
# Every public entry point in this module is a FAIL-CLOSED GATE: it must
# return a problem LIST for ARBITRARY JSON-like input and must never raise,
# because an exception escaping a gate is not a refusal — it is an
# unhandled crash that the caller may catch, log and route around. The
# concrete crash classes Codex enumerated, all reproduced as tests before
# being fixed here:
#   (a) `sorted(set(d) - set(allowed))` on a dict carrying BOTH str and int
#       keys -> TypeError ("'<' not supported between instances of 'int'
#       and 'str'") inside the unknown-key reporter;
#   (b) `name.partition("|")` on a NON-STRING manifest key -> AttributeError
#       inside validate_sealed_files;
#   (c) bool/int/tuple dict keys, deeply aberrant mappings and outright
#       MALICIOUS objects (a key whose `__hash__`/`__eq__` raises, a value
#       whose property access raises) anywhere in the tree.
#
# `_safe_sorted` gives every heterogeneous key set a TOTAL order without
# ever comparing across types; `_safe_key_set`/`_safe_keys` survive a
# raising `__hash__`; `_safe_repr` survives a raising `__repr__`; and
# `_guarded` is the last-resort net that converts any residual exception
# into one more problem string (fail-closed: a non-empty list refuses the
# seal) instead of letting it escape.
# ---------------------------------------------------------------------------
def _safe_repr(value) -> str:
    """`repr(value)` that can never raise (a malicious __repr__ is itself a
    tampering vector, so it degrades to a type name, never to a crash)."""
    try:
        return repr(value)
    except Exception:                                    # noqa: BLE001
        try:
            return f"<unreprable {type(value).__name__}>"
        except Exception:                                # noqa: BLE001
            return "<unreprable>"


def _sort_key(value):
    """A TOTAL order over arbitrary JSON-like keys: sort by type name first,
    then by the value itself when it is a plain str/int/float, else by its
    safe repr. Never compares an int against a str, so a mixed-type key set
    can no longer explode the `sorted()` calls this module makes."""
    tname = type(value).__name__
    if isinstance(value, str):
        return (tname, value, "")
    if isinstance(value, bool):
        return (tname, "", str(int(value)))
    if isinstance(value, (int, float)):
        try:
            return (tname, "", f"{float(value):+032.6f}")
        except Exception:                                # noqa: BLE001
            return (tname, "", _safe_repr(value))
    return (tname, "", _safe_repr(value))


def _safe_sorted(values) -> list:
    """`sorted(values)` that never raises on a heterogeneous / hostile set."""
    try:
        items = list(values)
    except Exception:                                    # noqa: BLE001
        return []
    try:
        return sorted(items, key=_sort_key)
    except Exception:                                    # noqa: BLE001
        return items


def _safe_list_text(values) -> str:
    """`str(list_of_keys)` for a problem message, hostile-repr-proof, and
    BYTE-IDENTICAL to the old `f"...:{sorted(extra)}"` rendering for the
    ordinary all-plain-key case (so no existing problem-code assertion in
    tests/test_s0_report.py changes shape)."""
    display = [v if isinstance(v, (str, int, float, type(None))) else
               _safe_repr(v) for v in values]
    try:
        return str(display)
    except Exception:                                    # noqa: BLE001
        return "[<unreprable>]"


def _safe_keys(d) -> list:
    """`list(d)` for a mapping whose keys may raise on iteration."""
    if not isinstance(d, Mapping):
        return []
    try:
        return list(d)
    except Exception:                                    # noqa: BLE001
        return []


def _safe_key_set(d) -> set:
    """`set(d)` that tolerates a key whose `__hash__` raises: unhashable /
    hostile keys are reported as their safe repr rather than crashing the
    caller (they are ALWAYS a defect — `_walk_r8` reports them separately —
    so degrading their identity here loses no signal)."""
    out: set = set()
    for key in _safe_keys(d):
        try:
            out.add(key)
        except Exception:                                # noqa: BLE001
            out.add(f"<unhashable:{type(key).__name__}>")
    return out


def _safe_in(container, key) -> bool:
    """`key in container` that never raises (a hostile key's `__eq__` fires
    on any hash-bucket collision, so even a plain `"x" in d` membership test
    is reachable by an attacker-supplied mapping)."""
    try:
        return key in container
    except Exception:                                    # noqa: BLE001
        return False


def _safe_not_in(container, key) -> bool:
    """`key not in container`, FAIL-CLOSED: a membership test that RAISES
    (a hostile `__eq__` firing on a hash-bucket collision) is treated as
    "not present", i.e. as an unknown/extra key. Answering "present" there
    would let an attacker hide a smuggled key behind a raising comparison."""
    try:
        return key not in container
    except Exception:                                    # noqa: BLE001
        return True


def _safe_set_diff(left, right) -> list:
    """Elements of `left` not in `right`, tolerating hostile members on
    either side (a bare `set - set` invokes `__eq__` on collision)."""
    try:
        items = list(left)
    except Exception:                                    # noqa: BLE001
        return []
    return [k for k in items if _safe_not_in(right, k)]


def _safe_get(d, key, default=None):
    """`d.get(key, default)` that never raises. Same rationale as
    `_safe_in`; also survives a Mapping subclass with a hostile
    `__getitem__`."""
    if not isinstance(d, Mapping):
        return default
    try:
        return d.get(key, default)
    except Exception:                                    # noqa: BLE001
        return default


def _guarded(name: str, fn, problems: list[str]) -> list[str]:
    """Run `fn(problems)` and convert ANY escaping exception into a final
    `validator_internal_error:<entry point>:<ExcType>` problem.

    This is a NET, not a substitute for the structural fixes above: the
    specific crash classes Codex listed are each fixed at their source so
    hostile input still yields a PRECISE problem code. What this guarantees
    on top is the absolute property the mandate requires — the function
    RETURNS a problem list for arbitrary input, always, and every problem
    accumulated before the failure is still reported (fail-closed: a
    non-empty list means Stage E refuses to seal)."""
    try:
        fn(problems)
    except Exception as exc:                             # noqa: BLE001
        try:
            etype = type(exc).__name__
        except Exception:                                # noqa: BLE001
            etype = "Exception"
        problems.append(f"validator_internal_error:{name}:{etype}")
    return problems


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


def _is_date_str_list(v) -> bool:
    """frozen: Appendix A — gridmix.py `_seed_report`'s tp_dates/fp_dates:
    a list of ISO date strings (possibly empty — a seed may legitimately
    select zero days from one side)."""
    return isinstance(v, list) and all(_is_date_str(x) for x in v)


def _is_nonneg_int_mapping(v) -> bool:
    """frozen: Appendix A — gridmix.py `_seed_report`'s allocation_tp/
    allocation_fp: stratum-key -> non-negative selected-day count."""
    return (isinstance(v, dict)
            and all(isinstance(k, str) for k in v)
            and all(_is_int(n) and n >= 0 for n in v.values()))


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
# M6.1.3-S1 (mission item 1): extended from the original 6-field REQUIRED
# subset to the FULL real 13-key `_seed_report` shape — a real producer
# field silently unchecked (tp_dates/fp_dates/n_tp_actual/n_fp_actual/
# mixture_mean_pnl/allocation_tp/allocation_fp) is exactly as much a
# "trust the tree's own claims" gap as an unknown key sailing through.
_GRID_SEED_FIELDS: tuple[str, ...] = (
    "target_precision", "target_recall", "realized_precision",
    "realized_recall", "day_markers", "F_expected",
    "tp_dates", "fp_dates", "n_tp_actual", "n_fp_actual",
    "mixture_mean_pnl", "allocation_tp", "allocation_fp")
_GRID_SEED_FIELD_TYPES: Mapping[str, object] = {
    "target_precision": _is_number, "target_recall": _is_number,
    "realized_precision": _is_number_or_none,
    "realized_recall": _is_number_or_none,
    "day_markers": _is_list, "F_expected": _is_number,
    "tp_dates": _is_date_str_list, "fp_dates": _is_date_str_list,
    "n_tp_actual": _is_int, "n_fp_actual": _is_int,
    "mixture_mean_pnl": _is_number_or_none,
    "allocation_tp": _is_nonneg_int_mapping,
    "allocation_fp": _is_nonneg_int_mapping,
}

# frozen: Appendix A — the FULL frozen (q, r) grid, DERIVED from gridmix's
# OWN axis construction (never a separately hardcoded list — mission
# requirement). 9 q-values x 7 r-values = 63 points; key format matches
# gridmix.py's own `f"q{q_mil/1000:.2f}_r{r_mil/1000:.2f}"` exactly.
_FEASIBILITY_GRID_POINT_KEYS: frozenset[str] = frozenset(
    f"q{q_mil / 1000:.2f}_r{r_mil / 1000:.2f}"
    for q_mil in gridmix.Q_GRID_MILLIS for r_mil in gridmix.R_GRID_MILLIS)
# mission item 3 — the exact (q_mil, r_mil) INTEGER millis a grid-point key
# was built from, DERIVED the same way (never re-parsed from the string),
# so a recompute of n_tp_target/n_fp_target/F_expected can call gridmix's
# OWN frozen arithmetic (`floor_n_tp`/`n_fp_for`/`f_expected`) rather than
# trusting the point's self-reported numbers.
_FEASIBILITY_GRID_KEY_TO_MILLIS: Mapping[str, tuple[int, int]] = {
    f"q{q_mil / 1000:.2f}_r{r_mil / 1000:.2f}": (q_mil, r_mil)
    for q_mil in gridmix.Q_GRID_MILLIS for r_mil in gridmix.R_GRID_MILLIS}

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
# 1d. M6.1.3-S1 mission item 5(c) — P1 <= P5 numeric ordering.
#
# This is a STRUCTURAL/NUMERIC sanity invariant of any real percentile pair
# (the 1st percentile of a distribution can never exceed its 5th), and is
# checked independently of numpy's linear-interpolation ESTIMATOR —
# `PERCENTILE_METHOD = "linear"` (study.py / stability.py) is the DR-8
# RULED estimator (Aaron 2026-08-10; mission item 5(a)/(b) below); this boundary
# never describes it as frozen or approved.
# ---------------------------------------------------------------------------
def _check_p1_le_p5(pct, path: str, problems: list[str]) -> None:
    if not isinstance(pct, dict):
        return
    p1, p5 = pct.get("P1"), pct.get("P5")
    if _is_number(p1) and _is_number(p5) and p1 > p5:
        problems.append(f"percentile_p1_gt_p5:{path}:{p1}>{p5}")


# ---------------------------------------------------------------------------
# 1e. M6.1.3-S1 mission item 1 — SCHEMA MATRIX: for every A1-A12 section
#     (+ A2b stability_views) the EXACT set of keys the REAL producer
#     (scripts/s0_real_run.py::build_full_study_result and the
#     src/itsf/s0/{study,stability,gridmix,stats,dataset}.py functions it
#     calls, all READ to confirm this — never guessed) is ever seen to emit
#     at each documented nesting level. Every constant below is traceable to
#     the producer function/return statement named in its comment — a
#     DOCUMENTED allowance, per mission item 1: "UNKNOWN keys inside a
#     section = problem (fail-closed), with a documented allowance ONLY for
#     keys the producer genuinely emits."
#
#     `_check_no_unknown_keys` is deliberately an ALLOWED-SUPERSET check
#     (a key OUTSIDE `allowed` = problem), never a full equality check:
#     several constants below include keys that are ALLOWED but not
#     independently REQUIRED elsewhere by this module (e.g. disclosures'
#     "methods_test_only", na_conservation's richer evidence fields, A9's
#     pre-/post-manifest-injection union) — this boundary's job is to catch
#     an UNDOCUMENTED key smuggled in (a cross-field-tampering vector,
#     mission item 7), never to re-litigate which subset is mandatory (that
#     stays each existing rule's own job).
# ---------------------------------------------------------------------------
def _check_no_unknown_keys(d, allowed, path: str, problems: list[str], *,
                           code: str) -> None:
    """`d`'s key set must be a SUBSET of `allowed`. No-ops on a non-dict `d`
    — the caller's own type/presence check already reports that defect;
    this only ever adds an unknown-key problem on a dict whose key set
    exceeds the documented allowance.

    M6.1.4-S1 (Codex crash class (a)): the key set is diffed and ordered
    through `_safe_key_set`/`_safe_sorted`, so a section carrying BOTH str
    and int keys (e.g. `{"pooled": ..., 7: ...}`) now REPORTS
    `<code>:<path>:[7]` instead of raising TypeError out of `sorted()`."""
    if not isinstance(d, dict):
        return
    extra = _safe_sorted(_safe_set_diff(_safe_keys(d), set(allowed)))
    if extra:
        problems.append(f"{code}:{path}:{_safe_list_text(extra)}")


# A1 structural — s0_real_run.py build_full_study_result's own
# `_strkeys({...})` literal (7 keys == _STRUCTURAL_REQUIRED_KEYS).
_STRUCTURAL_ALLOWED_KEYS: frozenset[str] = frozenset(_STRUCTURAL_REQUIRED_KEYS)
# dataset.py `build_na_table`'s real top-level return (6 keys: population,
# per_field, direction, diagnostics, totals_by_reason, checks).
_NA_TABLE_ALLOWED_KEYS: frozenset[str] = frozenset({
    "population", "per_field", "direction", "diagnostics",
    "totals_by_reason", "checks"})
_LABEL_ANCHOR_ROW_ALLOWED_KEYS: frozenset[str] = frozenset({
    "available_days", "unavailable_days"})

# A2 oracle_daily — s0_real_run.py: {"day_universe":..., "executable":...}.
_ORACLE_DAILY_CELL_ALLOWED_KEYS: frozenset[str] = frozenset({
    "day_universe", "executable"})
# study.py `build_study`'s per-theta `universe` dict — the FULL real
# day_universe shape (12 keys).
_DAY_UNIVERSE_ALLOWED_KEYS: frozenset[str] = frozenset({
    "theta", "n_directional_tradeable", "n_trade_constructible",
    "n_untradeable_disclosed", "n_tp", "n_fp", "n_tp_labelled",
    "n_fp_labelled", "tp_days", "fp_days", "conservation", "definition"})
# study.py: executable[engine][name] = {**_by_era_and_pooled(...),
# "worst_day_report": {...}} -> {"pooled", "by_era", "worst_day_report"}.
_EXECUTABLE_CELL_ALLOWED_KEYS: frozenset[str] = frozenset({
    "pooled", "by_era", "worst_day_report"})
# study.py's A2 (executable) worst_day_report block — NO estimator_status
# here (that field is an A4/e2_worst_days-only addition; see below).
_EXEC_WORST_DAY_REPORT_ALLOWED_KEYS: frozenset[str] = frozenset({
    "frozen_mandatory", "percentile_estimator", "pooled", "by_era"})
# study.py `_series_block` (both oracle_daily's "daily_pnl_usd" and
# theoretical_oracle's "daily_usd" variants — the value_key varies, the
# scalar-field set does not).
_SERIES_BLOCK_ALLOWED_KEYS: frozenset[str] = frozenset({
    "n", "sum_usd", "mean_usd", "min_usd", "max_usd",
    "worst_day_pnl_percentiles", "daily_pnl_usd", "daily_usd"})

# A3 theoretical_oracle — study.py: {"scenario", "note",
# **_by_era_and_pooled(...)}.
_THEORETICAL_ORACLE_CELL_ALLOWED_KEYS: frozenset[str] = frozenset({
    "scenario", "note", "pooled", "by_era"})

# A4 e2_worst_days — s0_real_run.py: {**worst_day_report,
# "estimator_status"} — the SAME 4 study.py worst_day_report keys PLUS the
# M6.1.3-S1 estimator-status addition (mission item 5).
_E2_WORST_DAYS_CELL_ALLOWED_KEYS: frozenset[str] = frozenset(
    _EXEC_WORST_DAY_REPORT_ALLOWED_KEYS | {"estimator_status"})
# frozen: S0 §7 table — DR-M6-H governs the P1/P5 estimator ruling; a
# formal payload must say the estimator question is RESOLVED to seal.
_ESTIMATOR_STATUS_RESOLVED = "resolved"

# A5 sizing_outputs — s0_real_run.py: {"rows", "coverage"}.
_SIZING_OUTPUTS_CELL_ALLOWED_KEYS: frozenset[str] = frozenset({
    "rows", "coverage"})
# study.py `_coverage()` (3 keys) and its `by_budget_usd[budget]` row.
_SIZING_COVERAGE_ALLOWED_KEYS: frozenset[str] = frozenset({
    "n_trades", "note", "by_budget_usd"})
_SIZING_COVERAGE_BUDGET_ROW_ALLOWED_KEYS: frozenset[str] = frozenset({
    "n_covered", "fraction"})

# A6 frequency — study.py `_frequency_block` (5 keys).
_FREQUENCY_CELL_ALLOWED_KEYS: frozenset[str] = frozenset({
    "denominator_definition", "note", "pooled", "by_era", "by_year"})

# A2b stability_views — stability.py `_engine_scenario_view` (5 keys), plus
# the DR-7 ruled `populations` block (Aaron 2026-08-10: BOTH the
# D_TP-conditional and the full-eligible population are reported). The key is
# validated when present (stability.check_populations); its PRESENCE on the
# production path is pinned by the entry-chain tests, not here, so
# pre-ruling-shaped synthetic payloads remain constructible in tests.
_STABILITY_ENGINE_SCENARIO_CELL_ALLOWED_KEYS: frozenset[str] = frozenset({
    "epochs", "by_year", "leave_one_year_out", "by_direction",
    "vol_terciles", "populations"})

# A7 bootstrap_ci — stats.py `bootstrap_mean_ci`'s real return shape, plus
# the DR-4 ruled-path disclosure keys emitted by `bootstrap_mean_ci_ruled`
# (Aaron 2026-08-10): the population/statistic/NA-drop accounting IS the A7
# statistic-definition annotation the decision packet mandated, so these are
# allowed by name, never as a wildcard.
_BOOTSTRAP_CELL_ALLOWED_KEYS: frozenset[str] = frozenset({
    "per_seed", "convergence", "quoted_seed", "quoted", "method",
    "quoted_seed_rule", "n_boot_per_seed", "n_boot_total", "theta",
    "theta_stream_key", "crn_scope", "crn_stream_entropy_by_seed",
    "population", "statistic", "na_day_rule", "n_days_in_sequence",
    "n_oracle_traded_days", "n_eligible_not_selected_days",
    "n_na_days_dropped", "na_dates"})
# stats.py per_seed[seed] entry (5 keys — "mean" was previously unchecked).
_BOOTSTRAP_SEED_ENTRY_ALLOWED_KEYS: frozenset[str] = frozenset({
    "mean", "ci_lo", "ci_hi", "n_boot", "block_len"})

# A8 feasibility_grid — one (q, r) grid point, BOTH the feasible and the
# infeasible_by_sample shape (gridmix.py `_grid_point`); the infeasible
# variant adds exactly one key ("infeasible_reason") on top of the same
# base 7.
_GRID_POINT_BASE_ALLOWED_KEYS: frozenset[str] = frozenset({
    "target_precision", "target_recall", "n_tp_target", "n_fp_target",
    "F_expected", "infeasible_by_sample", "per_seed"})
_GRID_POINT_ALLOWED_KEYS: frozenset[str] = frozenset(
    # DR-3/DR-5 (Aaron 2026-08-10): feasible points on the ruled grid path
    # carry the fp_allocation and repeats disclosure blocks; infeasible
    # points keep the base shape (producer-pinned in test_gridmix_rulings).
    _GRID_POINT_BASE_ALLOWED_KEYS | {"infeasible_reason", "fp_allocation",
                                     "repeats"})

# A9 mc_handoff_manifest — the TWO-CALL contract's union: pre-injection
# {"counts"} and post-injection {"counts", "files", "sealed_files",
# "self_excluded"} (validate_formal_payload must accept BOTH calls, see
# its docstring's two-call contract).
_MC_HANDOFF_MANIFEST_ALLOWED_KEYS: frozenset[str] = frozenset({
    "counts", "files", "sealed_files", "self_excluded"})
_MC_HANDOFF_COUNTS_CELL_ALLOWED_KEYS: frozenset[str] = frozenset({
    "n_records"})
_MC_HANDOFF_FILES_ENTRY_ALLOWED_KEYS: frozenset[str] = frozenset({
    "file", "n_records", "sha256"})
_MC_HANDOFF_SEALED_FILES_ENTRY_ALLOWED_KEYS: frozenset[str] = frozenset({
    "sha256", "bytes"})
# mission item 6 — sealed_files self-exclusion: the ONLY file this
# renderer is ever entitled to omit from `sealed_files` is the report
# itself (it carries the manifest, so it cannot hash itself; Stage F's
# chain seal covers it separately). A `self_excluded` list naming anything
# else is refused, never silently honoured as a bypass around the item-8
# completeness reconciliation.
_ALLOWED_SELF_EXCLUDED: frozenset[str] = frozenset({"S0_REPORT.json"})

# A10 era_axis — s0_real_run.py (2 keys).
_ERA_AXIS_ALLOWED_KEYS: frozenset[str] = frozenset({
    "axes", "counterfactual_disclosure"})

# A11 disclosures — s0_real_run.py build_full_study_result (5 keys).
_DISCLOSURES_ALLOWED_KEYS: frozenset[str] = frozenset({
    "na_conservation", "untradeable", "pending_method_decisions",
    "methods_test_only", "method_conventions"})
# s0_real_run.py `_na_conservation_block`'s real return (9 keys — the
# CONTRACT's minimal shape is only 2 of these; the rest is disclosed
# evidence this boundary ALLOWS but does not itself require).
_NA_CONSERVATION_ALLOWED_KEYS: frozenset[str] = frozenset({
    "per_table_total_na", "conservation_ok", "conserved",
    "reported_total_na", "itemized_reason_counts", "checker",
    "per_column_ok", "unregistered_reasons", "miscounted_columns"})

# A12 governance — RealChain.compute() / _expected_governance() (5 keys).
_GOVERNANCE_ALLOWED_KEYS: frozenset[str] = frozenset({
    "trial_id", "authorized_commit", "engineering_seed", "frozen_hashes",
    "registry_sequence_snapshot"})


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
        try:
            items = list(obj.items())
        except Exception:                                # noqa: BLE001
            problems.append(f"mapping_unwalkable:{path}")
            return
        for key, value in items:
            # M6.1.4-S1 (Codex crash class (c)): the str type-check comes
            # FIRST. `key == "dataset"` on a hostile key runs
            # `str.__eq__(key)` -> NotImplemented -> the REFLECTED
            # `key.__eq__("dataset")`, i.e. attacker code, inside the
            # validator. Comparing only after `isinstance(key, str)` makes
            # that unreachable.
            if not isinstance(key, str):
                problems.append(f"non_str_key:{path}:{_safe_repr(key)}")
                _walk_r8(value, f"{path}.<{_safe_repr(key)}>", problems)
                continue
            if key == "dataset":
                problems.append(f"dataset_key_present:{path}.{key}")
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
    _check_no_unknown_keys(block, _SERIES_BLOCK_ALLOWED_KEYS, path, problems,
                           code="series_block_unknown_key")
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
    _check_p1_le_p5(wpp, path, problems)


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
    _check_no_unknown_keys(cell, _EXECUTABLE_CELL_ALLOWED_KEYS, path,
                           problems, code="oracle_daily_executable_unknown_key")
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
    _check_no_unknown_keys(wdr, _EXEC_WORST_DAY_REPORT_ALLOWED_KEYS,
                           f"{path}|worst_day_report", problems,
                           code="oracle_daily_worst_day_report_unknown_key")
    pooled_pct = wdr.get("pooled")
    if not isinstance(pooled_pct, dict) or not {"P1", "P5"} <= set(pooled_pct):
        problems.append(f"oracle_daily_worst_day_report_pooled:{path}")
    else:
        _check_p1_le_p5(pooled_pct, f"{path}|worst_day_report|pooled",
                        problems)
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
            else:
                _check_p1_le_p5(
                    cell_pct, f"{path}|worst_day_report|by_era|{era}",
                    problems)


def _frequency_pooled_p(payload, tkey: str) -> float | None:
    """`payload["frequency"][tkey]["pooled"]["continuation_base_rate_p"]`,
    or None on ANY malformed shape along the way (never raises) — the same
    base rate `s0_real_run.py::build_full_study_result` feeds into
    `gridmix.build_grid` for this theta (mission item 3: F == p*r*N/q must
    be recomputed against the SAME p the real producer used, not a
    grid-cell's own self-reported number)."""
    freq = payload.get("frequency") if isinstance(payload, dict) else None
    tcell = freq.get(tkey) if isinstance(freq, dict) else None
    pooled = tcell.get("pooled") if isinstance(tcell, dict) else None
    p = pooled.get("continuation_base_rate_p") if isinstance(pooled, dict) \
        else None
    return p if _is_number(p) else None


def _check_feasibility_cell(cval, path: str, problems: list[str], *,
                            base_rate_p: float | None = None) -> None:
    """Deep leaf check for one `feasibility_grid.cells[theta|engine|scenario]`
    entry against the REAL gridmix.py `build_grid` return shape: the FULL
    frozen 63-point (q, r) grid (mission item 7) — not just the outer
    {grid, n_tp_available, n_fp_available, method} field set.

    M6.1.3-S1 (mission item 3): RECOMPUTE, not trust — n_tp_target/
    n_fp_target are re-derived from gridmix's OWN frozen arithmetic
    (`floor_n_tp`/`n_fp_for`) against the cell's own `n_tp_available`;
    `F_expected` is re-derived via `F == p*r*N/q` (gridmix's `f_expected`,
    frozen App-A formula) whenever `base_rate_p` is supplied (the caller
    reads it from `payload["frequency"][theta]["pooled"][
    "continuation_base_rate_p"]` — this function never trusts the grid
    cell's own reported precision/recall as its OWN base rate); every
    feasible point's `realized_precision`/`realized_recall`/n_tp_actual/
    n_fp_actual are re-derived from `len(tp_dates)`/`len(fp_dates)`, never
    read as given. `base_rate_p=None` (the base rate itself was unresolvable
    elsewhere) skips ONLY the F-formula recompute, never the rest.
    """
    if (not isinstance(cval, dict)
            or not set(_FEASIBILITY_CELL_FIELDS) <= set(cval)):
        problems.append(f"feasibility_grid_cell_incomplete:{path}")
        return
    _check_field_types(cval, _FEASIBILITY_CELL_FIELD_TYPES, path, problems)
    _check_no_unknown_keys(cval, _FEASIBILITY_CELL_FIELDS, path, problems,
                           code="feasibility_grid_cell_unknown_key")
    n_tp_avail = cval.get("n_tp_available")
    n_fp_avail = cval.get("n_fp_available")
    n_tp_avail_ok = _is_int(n_tp_avail) and n_tp_avail >= 0
    n_fp_avail_ok = _is_int(n_fp_avail) and n_fp_avail >= 0
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
        _check_no_unknown_keys(point, _GRID_POINT_ALLOWED_KEYS,
                               f"{path}:{k}", problems,
                               code="feasibility_grid_point_unknown_key")
        q_mil, r_mil = _FEASIBILITY_GRID_KEY_TO_MILLIS[k]
        q, r = q_mil / 1000.0, r_mil / 1000.0
        for field, expected in (("target_precision", q),
                                ("target_recall", r)):
            got = point.get(field)
            if _is_number(got) and not math.isclose(
                    got, expected, rel_tol=1e-9, abs_tol=1e-9):
                problems.append(
                    f"feasibility_grid_point_target_mismatch:{path}:{k}:"
                    f"{field}:{got}!={expected}")
        n_tp_target_expected = (gridmix.floor_n_tp(r_mil, n_tp_avail)
                                if n_tp_avail_ok else None)
        n_tp_target = point.get("n_tp_target")
        if (n_tp_target_expected is not None and _is_int(n_tp_target)
                and n_tp_target != n_tp_target_expected):
            problems.append(
                f"feasibility_grid_point_n_tp_target_mismatch:{path}:{k}:"
                f"{n_tp_target}!={n_tp_target_expected}")
        n_fp_target_expected = (
            gridmix.n_fp_for(n_tp_target_expected, q_mil)
            if n_tp_target_expected is not None else None)
        n_fp_target = point.get("n_fp_target")
        if (n_fp_target_expected is not None and _is_int(n_fp_target)
                and n_fp_target != n_fp_target_expected):
            problems.append(
                f"feasibility_grid_point_n_fp_target_mismatch:{path}:{k}:"
                f"{n_fp_target}!={n_fp_target_expected}")
        if base_rate_p is not None:
            f_expected_val = gridmix.f_expected(
                base_rate_p, r, q, gridmix.N_YEAR_TRADING_DAYS)
            f_got = point.get("F_expected")
            if (_is_number(f_got) and not math.isclose(
                    f_got, f_expected_val, rel_tol=1e-9, abs_tol=1e-9)):
                problems.append(
                    f"feasibility_grid_point_f_expected_mismatch:{path}:{k}:"
                    f"{f_got}!={f_expected_val}")
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
            # mission item 3 — "infeasible schema exact with NO selections":
            # the ONE extra key an infeasible point carries over the base 7
            # must itself be present (an infeasible point with no stated
            # reason is a disclosure gap, not a passable "extra field").
            if "infeasible_reason" not in point:
                problems.append(
                    f"feasibility_grid_infeasible_point_reason_missing:"
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
                continue
            _check_field_types(
                entry, _GRID_SEED_FIELD_TYPES, f"{path}:{k}:{seed}",
                problems)
            _check_no_unknown_keys(
                entry, _GRID_SEED_FIELDS, f"{path}:{k}:{seed}", problems,
                code="feasibility_grid_seed_entry_unknown_key")
            # mission item 3 — RECOMPUTE realized_precision/realized_recall
            # from the actual selection counts, never trust the reported
            # figure: n_tp_actual/n_fp_actual must equal the len() of the
            # entry's OWN tp_dates/fp_dates, and realized_precision/recall
            # are re-derived from those counts against n_tp_available.
            tp_dates, fp_dates = entry.get("tp_dates"), entry.get("fp_dates")
            n_tp_actual, n_fp_actual = (entry.get("n_tp_actual"),
                                        entry.get("n_fp_actual"))
            if (isinstance(tp_dates, list) and _is_int(n_tp_actual)
                    and n_tp_actual != len(tp_dates)):
                problems.append(
                    f"feasibility_grid_seed_n_tp_actual_mismatch:{path}:{k}:"
                    f"{seed}:{n_tp_actual}!={len(tp_dates)}")
            if (isinstance(fp_dates, list) and _is_int(n_fp_actual)
                    and n_fp_actual != len(fp_dates)):
                problems.append(
                    f"feasibility_grid_seed_n_fp_actual_mismatch:{path}:{k}:"
                    f"{seed}:{n_fp_actual}!={len(fp_dates)}")
            if isinstance(tp_dates, list) and isinstance(fp_dates, list):
                total = len(tp_dates) + len(fp_dates)
                expected_precision = (
                    (len(tp_dates) / total) if total else None)
                got_precision = entry.get("realized_precision")
                precision_ok = (
                    (expected_precision is None and got_precision is None)
                    or (expected_precision is not None
                        and _is_number(got_precision)
                        and math.isclose(got_precision, expected_precision,
                                         rel_tol=1e-9, abs_tol=1e-9)))
                if not precision_ok:
                    problems.append(
                        "feasibility_grid_seed_realized_precision_mismatch:"
                        f"{path}:{k}:{seed}:"
                        f"{got_precision}!={expected_precision}")
                if n_tp_avail_ok and n_tp_avail:
                    expected_recall = len(tp_dates) / n_tp_avail
                    got_recall = entry.get("realized_recall")
                    if (_is_number(got_recall) and not math.isclose(
                            got_recall, expected_recall, rel_tol=1e-9,
                            abs_tol=1e-9)):
                        problems.append(
                            "feasibility_grid_seed_realized_recall_mismatch:"
                            f"{path}:{k}:{seed}:"
                            f"{got_recall}!={expected_recall}")
            if base_rate_p is not None:
                f_expected_val = gridmix.f_expected(
                    base_rate_p, r, q, gridmix.N_YEAR_TRADING_DAYS)
                f_got = entry.get("F_expected")
                if (_is_number(f_got) and not math.isclose(
                        f_got, f_expected_val, rel_tol=1e-9, abs_tol=1e-9)):
                    problems.append(
                        "feasibility_grid_seed_f_expected_mismatch:"
                        f"{path}:{k}:{seed}:{f_got}!={f_expected_val}")


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

    M6.1.4-S1: the whole rule body runs under `_guarded`, so the
    "never raises" promise above is now STRUCTURAL rather than a
    per-rule discipline claim — arbitrary JSON-like input (mixed-type dict
    keys, hostile `__hash__`/`__eq__`/property objects, deeply aberrant
    mappings) yields a problem list, always. Every problem accumulated
    before an internal failure is still returned, plus a final
    `validator_internal_error:validate_formal_payload:<ExcType>`.
    """
    return _guarded(
        "validate_formal_payload",
        lambda acc: _validate_formal_payload_inner(
            payload, expected_governance, acc),
        [])


def _validate_formal_payload_inner(payload, expected_governance,
                                   problems: list[str]) -> list[str]:
    """`validate_formal_payload`'s rule body. Appends to (and returns) the
    caller's accumulator so a crash mid-way still surfaces every problem
    found up to that point."""
    if not isinstance(payload, dict):
        problems.append("payload_not_dict")
        return problems

    # R1 — every section present, non-empty, and a dict.
    for key in FORMAL_SECTIONS:
        if key not in payload:
            problems.append(f"missing_section:{key}")
        elif not isinstance(payload[key], dict):
            problems.append(f"wrong_type:{key}")
        elif not payload[key]:
            problems.append(f"empty_section:{key}")
    # mission item 1 — an UNDOCUMENTED top-level key (never a FORMAL_
    # SECTIONS member) previously sailed through this loop unnoticed: it
    # only ever iterated FORMAL_SECTIONS itself and never checked for an
    # extra.
    _check_no_unknown_keys(payload, FORMAL_SECTIONS, "$", problems,
                           code="unknown_top_level_section")
    if problems:
        # deeper rules assume every section exists and is a non-empty dict;
        # fail closed on the coarse defect rather than risk KeyError noise.
        return problems

    # frozen: S0 §7 L133 — the theta axis is EXACTLY {0.5, 0.3}, never a
    # subset (a single-theta payload), a superset, or a renamed key.
    tkeys = _safe_sorted(_safe_keys(payload["oracle_daily"]))
    if (_safe_set_diff(tkeys, _EXPECTED_THETA_KEYS)
            or _safe_set_diff(_EXPECTED_THETA_KEYS, tkeys)):
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
        tcell = _safe_get(payload["oracle_daily"], tkey)
        du = _safe_get(tcell, "day_universe") if isinstance(tcell, dict) \
            else None
        if not isinstance(du, dict):
            problems.append(f"day_universe_missing:{tkey}")
            continue
        _check_no_unknown_keys(du, _DAY_UNIVERSE_ALLOWED_KEYS,
                               f"oracle_daily.{tkey}.day_universe", problems,
                               code="day_universe_unknown_key")
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
        _check_no_unknown_keys(tcell, _ORACLE_DAILY_CELL_ALLOWED_KEYS,
                               f"oracle_daily.{tkey}", problems,
                               code="oracle_daily_cell_unknown_key")
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
    _check_no_unknown_keys(st, _STRUCTURAL_ALLOWED_KEYS, "structural",
                           problems, code="structural_unknown_key")
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
        _check_no_unknown_keys(nat, _NA_TABLE_ALLOWED_KEYS,
                               "structural.na_table", problems,
                               code="na_table_unknown_key")
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
                    _check_no_unknown_keys(
                        row, _NA_TABLE_FIELD_ROW_TYPES,
                        f"structural.na_table.per_field.{table}.{field}",
                        problems, code="na_table_row_unknown_key")
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
            elif isinstance(row, dict):
                _check_no_unknown_keys(
                    row, _LABEL_ANCHOR_ROW_ALLOWED_KEYS,
                    f"structural.label_anchor_availability.{label}",
                    problems, code="label_anchor_row_unknown_key")
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
    actual_ci = _safe_keys(payload["bootstrap_ci"])
    for k in _safe_sorted(_safe_set_diff(expected_ci, actual_ci)):
        problems.append(f"bootstrap_ci_missing:{k}")
    for k in _safe_sorted(_safe_set_diff(actual_ci, expected_ci)):
        problems.append(f"bootstrap_ci_extra:{_safe_repr(k)}"
                        if not isinstance(k, str) else f"bootstrap_ci_extra:{k}")
    present = [k for k in expected_ci if not _safe_not_in(actual_ci, k)]
    for key in _safe_sorted(present):
        blk = int(key.rsplit("block", 1)[1])
        cell = _safe_get(payload["bootstrap_ci"], key)
        if not isinstance(cell, dict):
            problems.append(f"bootstrap_ci_cell_type:{key}")
            continue
        _check_no_unknown_keys(cell, _BOOTSTRAP_CELL_ALLOWED_KEYS, key,
                               problems, code="bootstrap_ci_cell_unknown_key")
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
        seed_means: dict[int, object] = {}
        for seed in (7, 13, 31):
            entry = None
            if isinstance(per_seed, dict):
                entry = per_seed.get(seed, per_seed.get(str(seed)))
            if not isinstance(entry, dict):
                problems.append(f"bootstrap_ci_seed_entry:{key}:{seed}")
                continue
            _check_no_unknown_keys(
                entry, _BOOTSTRAP_SEED_ENTRY_ALLOWED_KEYS, f"{key}:{seed}",
                problems, code="bootstrap_ci_seed_entry_unknown_key")
            # mission item 3 — stats.py's "mean" is the SAMPLE mean of the
            # underlying series, computed ONCE and copied VERBATIM into
            # every seed's dict (`_bootstrap_mean_ci_unchecked`: `sample_
            # mean = float(values.mean())` outside the per-seed loop) —
            # previously entirely unchecked (not even leaf-typed). A
            # fabricated per-seed mean that silently DIFFERS from its
            # siblings is refused below, once every seed's entry has been
            # collected.
            mean_val = entry.get("mean")
            if not _is_number(mean_val):
                problems.append(f"bootstrap_ci_mean_invalid:{key}:{seed}")
            else:
                seed_means[seed] = mean_val
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
        # mission item 3 — cross-seed RECOMPUTE: all three seeds resample
        # the SAME input series, so their "mean" entries must be identical
        # (not merely each individually well-typed) — a per-seed value that
        # silently drifts from its siblings is exactly the "self-reported
        # number, never re-derived" defect class this closes.
        if len(seed_means) > 1:
            distinct = {round(v, 9) for v in seed_means.values()}
            if len(distinct) > 1:
                problems.append(
                    f"bootstrap_ci_mean_cross_seed_mismatch:{key}:"
                    f"{sorted(seed_means.items())}")
        quoted = cell.get("quoted")
        if quoted is not None:
            # mission item 3 — "quoted" restates per_seed[quoted_seed]
            # VERBATIM (stats.py: `"quoted": per_seed[quoted_seed]`); a
            # payload that carries a "quoted" block inconsistent with its
            # own per_seed[7] entry is refused, never merely leaf-typed.
            entry_7 = None
            if isinstance(per_seed, dict):
                entry_7 = per_seed.get(7, per_seed.get("7"))
            if (isinstance(quoted, dict) and isinstance(entry_7, dict)
                    and quoted != entry_7):
                problems.append(f"bootstrap_ci_quoted_mismatch:{key}")
        conv = cell.get("convergence")
        if (not isinstance(conv, dict)
                or not {"max_abs_ci_lo_diff", "max_abs_ci_hi_diff"}
                       <= set(conv)):
            problems.append(f"bootstrap_ci_convergence_missing:{key}")

    # R4 — oracle_daily / e2_worst_days / sizing_outputs / frequency /
    # theoretical_oracle.
    for section in ("oracle_daily", "e2_worst_days", "sizing_outputs",
                    "frequency", "theoretical_oracle"):
        if _safe_sorted(_safe_keys(payload[section])) != tkeys:
            problems.append(f"theta_keys_mismatch:{section}")

    # frozen: S0 §7 — theoretical_oracle per-theta shape (A3): Base scenario
    # only, pooled + by_era both eras, the SAME real study.py series-block
    # shape as oracle_daily's executable matrix (value_key "daily_usd").
    for tkey in tkeys:
        to_cell = payload["theoretical_oracle"].get(tkey)
        if not isinstance(to_cell, dict):
            problems.append(f"theoretical_oracle_missing:{tkey}")
            continue
        _check_no_unknown_keys(
            to_cell, _THEORETICAL_ORACLE_CELL_ALLOWED_KEYS,
            f"theoretical_oracle|{tkey}", problems,
            code="theoretical_oracle_unknown_key")
        if to_cell.get("scenario") != BASE_SCENARIO_NAME:
            problems.append(f"theoretical_oracle_scenario:{tkey}")
        # M6.1.3 fix-round (blind-audit A52): the ECONOMIC-UPPER-BOUND-ONLY
        # disclosure note is CONTENT, not decoration — a blanked/non-str
        # note silently drops the frozen §7 caveat and is refused.
        note = to_cell.get("note")
        if not isinstance(note, str) or not note.strip():
            problems.append(f"theoretical_oracle_note_invalid:{tkey}")
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
        _check_no_unknown_keys(freq, _FREQUENCY_CELL_ALLOWED_KEYS,
                               f"frequency|{tkey}", problems,
                               code="frequency_cell_unknown_key")
        pooled = freq.get("pooled")
        if (not isinstance(pooled, dict)
                or not set(_FREQUENCY_CELL_FIELDS) <= set(pooled)):
            problems.append(f"frequency_cell_incomplete:{tkey}|pooled")
        else:
            _check_field_types(pooled, _FREQUENCY_CELL_FIELD_TYPES,
                               f"frequency|{tkey}|pooled", problems)
            _check_no_unknown_keys(
                pooled, _FREQUENCY_CELL_FIELDS, f"frequency|{tkey}|pooled",
                problems, code="frequency_leaf_cell_unknown_key")
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
                    _check_no_unknown_keys(
                        cell, _FREQUENCY_CELL_FIELDS,
                        f"frequency|{tkey}|by_era|{era}", problems,
                        code="frequency_leaf_cell_unknown_key")
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
                    _check_no_unknown_keys(
                        cell, _FREQUENCY_CELL_FIELDS,
                        f"frequency|{tkey}|by_year|{y}", problems,
                        code="frequency_leaf_cell_unknown_key")

    for tkey in tkeys:
        for scn in _SCENARIOS:
            eng_block = payload["e2_worst_days"].get(tkey, {})
            cell = (eng_block.get(scn) if isinstance(eng_block, dict)
                    else None)
            if not isinstance(cell, dict):
                problems.append(f"e2_worst_days_missing:{tkey}|{scn}")
                continue
            _check_no_unknown_keys(
                cell, _E2_WORST_DAYS_CELL_ALLOWED_KEYS,
                f"e2_worst_days|{tkey}|{scn}", problems,
                code="e2_worst_days_unknown_key")
            pooled = cell.get("pooled")
            if (not isinstance(pooled, dict) or "P1" not in pooled
                    or "P5" not in pooled):
                problems.append(f"e2_worst_days_pooled:{tkey}|{scn}")
            else:
                _check_p1_le_p5(pooled, f"e2_worst_days|{tkey}|{scn}|pooled",
                                problems)
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
                    else:
                        _check_p1_le_p5(
                            era_cell,
                            f"e2_worst_days|{tkey}|{scn}|by_era|{era}",
                            problems)

            # mission item 5(b) — P1/P5 GOVERNANCE (M-1, mandatory): the
            # linear percentile estimator is the DR-8 RULED value (Aaron
            # 2026-08-10; frozen §7 mandates only THAT a P1/P5 report
            # exist, never which estimator computes it) — a formal report
            # must carry an
            # explicit `estimator_status` on every E2 worst-day cell, and
            # sealing REQUIRES it read EXACTLY "resolved". While DR-M6-H
            # pends, the producer emits "unresolved_DR-M6-H"
            # (scripts/s0_real_run.py build_full_study_result) and this
            # boundary fail-closes on it — never a silent pass, and never a
            # comment anywhere in this module describing "linear" as frozen
            # or approved.
            status = cell.get("estimator_status")
            if status is None and "estimator_status" not in cell:
                problems.append(
                    f"e2_worst_days_estimator_status_missing:{tkey}|{scn}")
            elif status != _ESTIMATOR_STATUS_RESOLVED:
                problems.append(
                    f"worst_day_estimator_unresolved:{tkey}|{scn}:{status!r}")

    for tkey in tkeys:
        cell = payload["sizing_outputs"].get(tkey, {})
        _check_no_unknown_keys(cell, _SIZING_OUTPUTS_CELL_ALLOWED_KEYS,
                               f"sizing_outputs|{tkey}", problems,
                               code="sizing_outputs_cell_unknown_key")
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
                                _check_no_unknown_keys(
                                    row, _SIZING_ROW_FIELDS,
                                    f"sizing_outputs|{tkey}|{eng}|{scn}|"
                                    f"rows[{i}]", problems,
                                    code="sizing_outputs_row_unknown_key")
                if isinstance(cov_block, dict):
                    eng_cov = cov_block.get(eng)
                    cov = (eng_cov.get(scn)
                          if isinstance(eng_cov, dict) else None)
                    if isinstance(cov, dict):
                        _check_no_unknown_keys(
                            cov, _SIZING_COVERAGE_ALLOWED_KEYS,
                            f"sizing_outputs|{tkey}|{eng}|{scn}|coverage",
                            problems,
                            code="sizing_outputs_coverage_unknown_key")
                        by_budget = cov.get("by_budget_usd")
                        if (not isinstance(by_budget, dict)
                                or not set(_COVERAGE_BUDGETS)
                                       <= set(by_budget)):
                            problems.append(
                                f"sizing_outputs_coverage_incomplete:"
                                f"{tkey}|{eng}|{scn}")
                        else:
                            for budget, row in by_budget.items():
                                _check_no_unknown_keys(
                                    row,
                                    _SIZING_COVERAGE_BUDGET_ROW_ALLOWED_KEYS,
                                    f"sizing_outputs|{tkey}|{eng}|{scn}|"
                                    f"coverage|by_budget_usd|{budget}",
                                    problems,
                                    code="sizing_outputs_coverage_budget_"
                                        "unknown_key")

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
                _check_no_unknown_keys(
                    cell, _STABILITY_ENGINE_SCENARIO_CELL_ALLOWED_KEYS,
                    f"stability_views|{tkey}|{eng}|{scn}", problems,
                    code="stability_views_cell_unknown_key")
                # DR-7 (Aaron 2026-08-10): a cell CARRYING a populations
                # block must satisfy the ruled both-populations shape; the
                # rule string is read from the single ruled source, never
                # from the payload under test.
                if isinstance(cell.get("populations"), dict):
                    from itsf.contracts import aaron_ruled_methods as _arm
                    from itsf.s0 import stability as _stab
                    for code in _stab.check_populations(
                            cell, _arm().stability_population):
                        problems.append(
                            f"stability_views_populations:{tkey}|{eng}|"
                            f"{scn}:{code}")
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
                    # tercile-name list (vocabulary-agnostic even though
                    # DR-2 is now ruled).
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
                            _check_no_unknown_keys(
                                bval, _STABILITY_CELL_FIELDS,
                                f"stability_views|{tkey}|{eng}|{scn}|"
                                f"{axis_name}|{bkey}", problems,
                                code="stability_views_cell_field_unknown_key")

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
    _check_no_unknown_keys(ea, _ERA_AXIS_ALLOWED_KEYS, "era_axis", problems,
                           code="era_axis_unknown_key")
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
    _check_no_unknown_keys(disclosures, _DISCLOSURES_ALLOWED_KEYS,
                           "disclosures", problems,
                           code="disclosures_unknown_key")
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
        _check_no_unknown_keys(nac, _NA_CONSERVATION_ALLOWED_KEYS,
                               "disclosures.na_conservation", problems,
                               code="na_conservation_unknown_key")
        totals = nac.get("per_table_total_na")
        totals_ok = (isinstance(totals, dict)
                    and set(_NA_CONSERVATION_TABLES) <= set(totals)
                    and all(_is_int(totals.get(k)) and totals.get(k) >= 0
                           for k in _NA_CONSERVATION_TABLES))
        if not totals_ok:
            problems.append("disclosures_na_conservation_totals_invalid")
        if nac.get("conservation_ok") is not True:
            problems.append("disclosures_na_conservation_flag_not_true")
        # M6.1.3 fix-round (blind-audit A56): the richer evidence keys,
        # WHEN PRESENT, must agree with the flag — conservation_ok=True
        # next to a non-empty unregistered_reasons / miscounted_columns
        # (or a false conserved / any false per_column_ok cell) is a
        # self-contradiction, never a pass.
        if nac.get("conservation_ok") is True:
            for key in ("unregistered_reasons", "miscounted_columns"):
                if key in nac and nac[key]:
                    problems.append(
                        "disclosures_na_conservation_contradiction:" + key)
            if "conserved" in nac and nac["conserved"] is not True:
                problems.append(
                    "disclosures_na_conservation_contradiction:conserved")
            pco = nac.get("per_column_ok")
            if pco is not None and (
                    not isinstance(pco, dict)
                    or any(v is not True for v in pco.values())):
                problems.append("disclosures_na_conservation_contradiction:"
                                "per_column_ok")

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
    _check_no_unknown_keys(gov, _GOVERNANCE_ALLOWED_KEYS, "governance",
                           problems, code="governance_unknown_key")
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
    _check_no_unknown_keys(
        payload["mc_handoff_manifest"], _MC_HANDOFF_MANIFEST_ALLOWED_KEYS,
        "mc_handoff_manifest", problems,
        code="mc_handoff_manifest_unknown_key")
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
                _check_no_unknown_keys(
                    cell, _MC_HANDOFF_COUNTS_CELL_ALLOWED_KEYS,
                    f"mc_handoff_manifest.counts.{eng}.{scn}", problems,
                    code="mc_handoff_manifest_counts_cell_unknown_key")

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
            # mission item 3 — F == p*r*N/q recompute needs the SAME theta's
            # continuation base rate; read defensively (a malformed/missing
            # frequency section is its own problem, reported elsewhere, and
            # never crashes this lookup — see `_frequency_pooled_p`).
            tkey_for_cell = k.split("|", 1)[0]
            _check_feasibility_cell(
                cells[k], k, problems,
                base_rate_p=_frequency_pooled_p(payload, tkey_for_cell))
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


def _derive_trade_date_universe(payload):
    """The sealed trade-date universe DERIVED from the payload's own
    `oracle_daily[<theta>].day_universe.tp_days/fp_days` — matrix CR-7's
    reducer (b). Returns None (never an empty set) when the payload cannot
    support that derivation at all (no `oracle_daily`, or not one theta
    cell carrying a usable day_universe), so a caller-supplied override for
    a deliberately narrow payload stays legal while an override against a
    FULL payload is cross-checked. Never raises."""
    if not isinstance(payload, dict):
        return None
    od = _safe_get(payload, "oracle_daily")
    if not isinstance(od, dict) or not od:
        return None
    derivable = False
    universe: set = set()
    for tcell in list(od.values()):
        if not isinstance(tcell, dict):
            continue
        du = _safe_get(tcell, "day_universe")
        if not isinstance(du, dict):
            continue
        for grp in ("tp_days", "fp_days"):
            days = _safe_get(du, grp)
            if isinstance(days, (list, tuple)):
                derivable = True
                for d in days:
                    # a NON-str date is kept (as its safe repr) rather than
                    # dropped: dropping it would SHRINK the universe a
                    # sealed file is compared against, i.e. weaken the gate.
                    try:
                        universe.add(d if isinstance(d, str) else _safe_repr(d))
                    except Exception:                    # noqa: BLE001
                        universe.add("<unhashable_trade_date>")
    return universe if derivable else None


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

    M6.1.4-S1 (matrix CR-7 — "the sealed trade-date universe"): an
    explicitly supplied `trade_date_universe` that DISAGREES with this
    function's own derivation from a payload that DOES carry a usable
    `oracle_daily` is now itself a hard problem
    (`sealed_file_universe_override_mismatch:...`). The production renderer
    passes `trade_date_universe=univ` computed from
    `formal["oracle_daily"][t]["day_universe"]`, which USED to make the
    validator's independent derivation dead code in production — two
    "independent" derivations that were structurally one. The override is
    still honoured (the documented narrow-payload use, where `oracle_daily`
    is absent/unusable, is untouched and raises no problem), but it can no
    longer MASK the independent derivation.

    M6.1.4-S1 also puts the whole body under `_guarded` and makes every key
    handling site type-safe: a NON-STRING manifest key
    (`{7: {...}}`) previously crashed `name.partition("|")` with an
    AttributeError instead of returning a problem.
    """
    return _guarded(
        "validate_sealed_files",
        lambda acc: _validate_sealed_files_inner(
            files, payload, trade_date_universe, acc),
        [])


def _validate_sealed_files_inner(files, payload, trade_date_universe,
                                 problems: list[str]) -> list[str]:
    """`validate_sealed_files`' body (see that function's docstring)."""
    manifest = (_safe_get(payload, "mc_handoff_manifest", {})
               if isinstance(payload, dict) else {})
    file_specs = _safe_get(manifest, "files") if isinstance(manifest, dict) \
        else None
    if not isinstance(file_specs, dict) or not file_specs:
        problems.append("mc_handoff_manifest_files_missing")
        return problems
    if not isinstance(files, Mapping):
        problems.append("sealed_files_argument_not_a_mapping")
        files = {}

    expected_keys = {f"{e}|{s}" for e in ENGINES for s in _SCENARIOS}
    got_keys = _safe_keys(file_specs)
    missing_keys = _safe_sorted(_safe_set_diff(expected_keys, got_keys))
    extra_keys = _safe_sorted(_safe_set_diff(got_keys, expected_keys))
    if missing_keys or extra_keys:
        problems.append(
            "mc_handoff_manifest_files_key_set_mismatch:"
            f"missing={_safe_list_text(missing_keys)}:"
            f"extra={_safe_list_text(extra_keys)}")

    derived_universe = _derive_trade_date_universe(payload)
    if trade_date_universe is None:
        universe = derived_universe if derived_universe is not None else set()
    else:
        try:
            universe = set(trade_date_universe)
        except Exception:                                # noqa: BLE001
            problems.append("sealed_file_universe_override_type")
            universe = derived_universe if derived_universe is not None else set()
        else:
            # CR-7: the caller's explicit set may never silently REPLACE the
            # payload-derived one when the payload can supply it.
            if derived_universe is not None and universe != derived_universe:
                problems.append(
                    "sealed_file_universe_override_mismatch:"
                    f"only_in_override={_safe_list_text(_safe_sorted(universe - derived_universe))}:"
                    f"only_in_payload={_safe_list_text(_safe_sorted(derived_universe - universe))}")

    counts = _safe_get(manifest, "counts", {}) if isinstance(manifest, dict) \
        else {}

    for name, spec in list(file_specs.items()):
        # M6.1.4-S1 (Codex crash class (b)): a NON-STRING manifest key
        # crashed `.partition` before it could ever be reported.
        if not isinstance(name, str):
            problems.append(f"sealed_file_spec_key_type:{_safe_repr(name)}")
            continue
        eng, sep, scn = name.partition("|")
        if not sep:
            problems.append(f"sealed_file_spec_key_format:{name}")
            eng = scn = None
        if not isinstance(spec, dict):
            problems.append(f"sealed_file_spec_type:{name}")
            continue
        fname = _safe_get(spec, "file")
        want_sha = _safe_get(spec, "sha256")
        want_n = _safe_get(spec, "n_records")
        if not _safe_in(files, fname):
            problems.append(
                f"sealed_file_missing:{name}:"
                f"{fname if isinstance(fname, str) else _safe_repr(fname)}")
            continue
        try:
            body = files[fname]
        except Exception:                                # noqa: BLE001
            problems.append(f"sealed_file_body_unreadable:{name}")
            continue
        if not isinstance(body, str):
            problems.append(f"sealed_file_body_type:{name}")
            continue
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
            got_fields, want_fields = _safe_key_set(rec), set(
                FORMAL_RECORD_FIELDS)
            if got_fields != want_fields:
                problems.append(
                    f"sealed_file_line_field_set_mismatch:{name}:{i}:"
                    f"missing={_safe_list_text(_safe_sorted(want_fields - got_fields))}:"
                    f"extra={_safe_list_text(_safe_sorted(got_fields - want_fields))}")
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
        missing = _safe_sorted(universe - file_dates)
        extra = _safe_sorted(file_dates - universe)
        if missing:
            problems.append(
                f"sealed_file_missing_trade_dates:{name}:"
                f"{_safe_list_text(missing)}")
        if extra:
            problems.append(
                f"sealed_file_extra_trade_dates:{name}:"
                f"{_safe_list_text(extra)}")

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
        # mission item 6 — self-exclusion is a MODULE-INTERNAL frozen
        # constant (`_ALLOWED_SELF_EXCLUDED`), never taken verbatim off the
        # payload: `set(manifest.get("self_excluded") or [])` on a
        # non-list value (e.g. a bare string) previously exploded into a
        # set of CHARACTERS rather than filenames, and — worse — ANY name
        # a payload chose to list here silently bypassed the completeness
        # reconciliation below (a planted "PLANTED.txt" entered into
        # self_excluded would never need a sealed_files entry at all). Both
        # are refused now: a non-list/non-str-elements self_excluded is
        # its own problem and contributes NO exclusions, and a self_
        # excluded name outside the one frozen allowance is refused
        # outright.
        self_excluded_raw = manifest.get("self_excluded")
        if self_excluded_raw is None:
            self_excluded_raw = []
        if (not isinstance(self_excluded_raw, list)
                or any(not isinstance(x, str) for x in self_excluded_raw)):
            problems.append("sealed_files_self_excluded_type")
            self_excluded: set[str] = set()
        else:
            self_excluded = set(self_excluded_raw)
            disallowed = _safe_sorted(self_excluded - _ALLOWED_SELF_EXCLUDED)
            if disallowed:
                problems.append(
                    "sealed_files_self_excluded_not_allowed:"
                    f"{_safe_list_text(disallowed)}")
                # fail closed: an illegally-named exclusion buys NO bypass
                # of the completeness reconciliation below.
                self_excluded = self_excluded & _ALLOWED_SELF_EXCLUDED
        for fname, spec in list(sealed_files.items()):
            if not _safe_in(files, fname):
                problems.append(
                    "sealed_files_manifest_entry_missing_file:"
                    f"{fname if isinstance(fname, str) else _safe_repr(fname)}")
                continue
            if not isinstance(spec, dict):
                problems.append(
                    "sealed_files_manifest_entry_type:"
                    f"{fname if isinstance(fname, str) else _safe_repr(fname)}")
                continue
            try:
                raw_body = files[fname]
            except Exception:                            # noqa: BLE001
                raw_body = None
            if not isinstance(raw_body, str):
                problems.append(f"sealed_files_manifest_entry_body_type:"
                                f"{fname if isinstance(fname, str) else _safe_repr(fname)}")
                continue
            body_bytes = raw_body.encode("utf-8")
            got_sha = hashlib.sha256(body_bytes).hexdigest()
            if _safe_get(spec, "sha256") != got_sha:
                problems.append(
                    f"sealed_files_manifest_sha256_mismatch:{fname}")
            if _safe_get(spec, "bytes") != len(body_bytes):
                problems.append(
                    f"sealed_files_manifest_bytes_mismatch:{fname}")
        uncovered = _safe_sorted(
            _safe_set_diff(_safe_set_diff(_safe_keys(files),
                                          _safe_keys(sealed_files)),
                           self_excluded))
        if uncovered:
            problems.append(
                "sealed_files_manifest_incomplete:"
                + ",".join(u if isinstance(u, str) else _safe_repr(u)
                           for u in uncovered))

    return problems


# ---------------------------------------------------------------------------
# 6. reconcile_with_internal — M6.1.3-S1 mission item 4: cross-check the
#    FORMAL payload against the INTERNAL producer envelope — the dict
#    scripts/s0_real_run.py::build_full_study_result actually RETURNS
#    (dataset/na_reason_counts/reported_total_na/records/study, PLUS every
#    FORMAL_SECTIONS key, all in ONE dict). `split_envelope`'s own
#    "internal" half additionally DROPS "study" (never a member of
#    `_INTERNAL_KEYS`, never a member of `FORMAL_SECTIONS` — it is simply
#    discarded by that function) — a caller wiring this in must pass the
#    RAW compute_result, or an equivalent dict that still carries "study",
#    never `split_envelope(...)`'s own "internal" output.
#
#    NOT wired into any sealing gate here (main-agent renderer work, see
#    this module's docstring). A pure function, always returns a problem
#    list, and NEVER raises on a malformed tree — the same fail-closed
#    discipline as validate_formal_payload/validate_sealed_files.
# ---------------------------------------------------------------------------
# The two internal-only keys whose ABSENCE is itself a problem (mission
# item 4: "require internal-only keys like records/study; their absence =
# problem" — so passing the FORMAL payload itself as `internal` can never
# vacuously succeed, since neither key is ever a FORMAL_SECTIONS member).
_RECONCILE_REQUIRED_INTERNAL_KEYS: tuple[str, ...] = ("study", "records")

# frozen: S0 §2 — the three stability epoch boundaries stability.py's
# EPOCHS tuple encodes (inclusive on both ends). Duplicated as DATA here
# rather than imported — stability.py's EPOCHS/ALL_EPOCH_LABELS are
# private module constants this boundary does not reach into — so the
# stability recompute below can bucket by year without trusting
# stability.py's own bucketing to be the thing under test.
_RECONCILE_EPOCH_RANGES: tuple[tuple[str, int, int], ...] = (
    ("2010-2013", 2010, 2013),
    ("2014-2017", 2014, 2017),
    ("2018-2021", 2018, 2021),
)
_RECONCILE_OUTSIDE_EPOCHS = "outside_epochs"
_RECONCILE_ALL_EPOCH_LABELS: tuple[str, ...] = tuple(
    label for label, _lo, _hi in _RECONCILE_EPOCH_RANGES
) + (_RECONCILE_OUTSIDE_EPOCHS,)
_RECONCILE_DIRECTION_KEY_OF: Mapping[int, str] = {1: "+1", -1: "-1"}


def _reconcile_epoch_of_year(year: int) -> str:
    for label, lo, hi in _RECONCILE_EPOCH_RANGES:
        if lo <= year <= hi:
            return label
    return _RECONCILE_OUTSIDE_EPOCHS


def _derive_day_meta_from_dataset(dataset_obj):
    """`internal["dataset"]` (a live S0Dataset-shaped object, or any duck-
    typed stand-in exposing the same `.records` shape) -> date -> {"year",
    "era", "d_open"}, EXACTLY as scripts/s0_real_run.py's
    build_full_study_result derives its own `day_meta` local (`{r.
    trade_date: {"year": r.year, "era": r.era, "d_open": int(r.labels.
    d_open or 0)} for r in ds.records}`) — this boundary never invents its
    own notion of what a "day" is. Returns None (never raises) on any
    malformed shape at any level."""
    records = getattr(dataset_obj, "records", None)
    if records is None:
        return None
    out: dict[str, dict[str, object]] = {}
    try:
        for r in records:
            trade_date = r.trade_date
            if not isinstance(trade_date, str):
                return None
            d_open = r.labels.d_open
            out[trade_date] = {
                "year": r.year, "era": r.era,
                "d_open": int(d_open) if d_open is not None else 0,
            }
    except (AttributeError, TypeError, ValueError):
        return None
    return out


def _recompute_cell_stats(pairs: list[tuple[str, float]]) -> dict[str, object]:
    """The n/sum_usd/mean_usd/best_day/worst_day/n_positive/n_negative/
    n_zero subset of stability.py's `_cell()` shape — deliberately EXCLUDES
    `worst_day_pnl_percentiles`: P1/P5 depend on the DR-8 RULED linear
    estimator (mission item 5), and
    recomputing those here (with the same estimator) would silently bake
    approval of that convention into a "recompute-not-trust" check rather
    than testing it — this reconciliation stays to the estimator-free
    fields."""
    vals = [v for _d, v in pairs]
    n = len(vals)
    total = sum(vals) if vals else 0.0
    return {
        "n": n, "sum_usd": total,
        "mean_usd": (total / n) if n else None,
        "best_day": max(vals) if vals else None,
        "worst_day": min(vals) if vals else None,
        "n_positive": sum(1 for v in vals if v > 0),
        "n_negative": sum(1 for v in vals if v < 0),
        "n_zero": sum(1 for v in vals if v == 0.0),
    }


def _reconcile_compare_bucket(expected: dict, actual, path: str,
                              problems: list[str]) -> None:
    if not isinstance(actual, dict):
        problems.append(f"reconcile_stability_bucket_missing:{path}")
        return
    for field in ("n", "n_positive", "n_negative", "n_zero"):
        if actual.get(field) != expected[field]:
            problems.append(
                f"reconcile_stability_value_mismatch:{path}.{field}:"
                f"{actual.get(field)}!={expected[field]}")
    for field in ("sum_usd", "mean_usd", "best_day", "worst_day"):
        exp_v, act_v = expected[field], actual.get(field)
        ok = ((exp_v is None and act_v is None)
              or (exp_v is not None and _is_number(act_v)
                  and math.isclose(act_v, exp_v, rel_tol=1e-9, abs_tol=1e-9)))
        if not ok:
            problems.append(
                f"reconcile_stability_value_mismatch:{path}.{field}:"
                f"{act_v}!={exp_v}")


def _reconcile_stability_cell(pnl_map, day_meta, cell_f, path: str,
                              problems: list[str]) -> None:
    """Bucket `pnl_map` (date -> usd — study.py's `per_theta[theta]["d_tp"]
    [engine][scenario]`) by epoch/year/direction using `day_meta`,
    RECOMPUTE each bucket's descriptive stats, and compare against the
    formal payload's OWN declared `stability_views` cell — the exact
    recompute `_check_series_block`'s docstring says the formal payload
    ALONE cannot support (it carries no per-bucket daily series), only
    possible here because `internal["study"]` + `internal["dataset"]`
    supply the raw materials the formal side never does. `leave_one_year_
    out`/`vol_terciles` are OUT of this function's scope: LOYO's cross-
    check already lives at the formal-only boundary (`stability_views_loyo_
    recompute_mismatch`) and vol_terciles' vocabulary/axis (DR-M6-B) is not
    derivable from `day_meta` alone."""
    if not isinstance(pnl_map, dict) or not isinstance(cell_f, dict):
        problems.append(f"reconcile_stability_missing:{path}")
        return
    epoch_buckets: dict[str, list[tuple[str, float]]] = {
        label: [] for label in _RECONCILE_ALL_EPOCH_LABELS}
    year_buckets: dict[str, list[tuple[str, float]]] = {}
    dir_buckets: dict[str, list[tuple[str, float]]] = {"+1": [], "-1": []}
    missing_meta: list[str] = []
    for d, v in pnl_map.items():
        meta = day_meta.get(d)
        if not isinstance(meta, dict) or not _is_number(v):
            missing_meta.append(d)
            continue
        try:
            year_int = int(meta["year"])
            d_open = int(meta["d_open"])
        except (KeyError, TypeError, ValueError):
            missing_meta.append(d)
            continue
        epoch_buckets[_reconcile_epoch_of_year(year_int)].append(
            (d, float(v)))
        year_buckets.setdefault(str(meta["year"]), []).append((d, float(v)))
        dkey = _RECONCILE_DIRECTION_KEY_OF.get(d_open)
        if dkey is not None:
            dir_buckets[dkey].append((d, float(v)))
    if missing_meta:
        # a PARTIAL recompute (some dates silently excluded) would be
        # worse than no recompute at all — it would give false confidence
        # that the remaining buckets are trustworthy while quietly
        # ignoring a day_meta gap; refuse the whole cell instead.
        problems.append(
            f"reconcile_stability_day_meta_missing:{path}:"
            f"{sorted(missing_meta)[:5]}")
        return

    epochs_f = cell_f.get("epochs")
    for epoch_label, pairs in epoch_buckets.items():
        _reconcile_compare_bucket(
            _recompute_cell_stats(pairs),
            epochs_f.get(epoch_label) if isinstance(epochs_f, dict) else None,
            f"{path}|epochs|{epoch_label}", problems)

    by_year_f = cell_f.get("by_year")
    for year_key, pairs in year_buckets.items():
        _reconcile_compare_bucket(
            _recompute_cell_stats(pairs),
            by_year_f.get(year_key) if isinstance(by_year_f, dict) else None,
            f"{path}|by_year|{year_key}", problems)

    by_dir_f = cell_f.get("by_direction")
    for dkey, pairs in dir_buckets.items():
        _reconcile_compare_bucket(
            _recompute_cell_stats(pairs),
            by_dir_f.get(dkey) if isinstance(by_dir_f, dict) else None,
            f"{path}|by_direction|{dkey}", problems)


def _reconcile_oracle_series(pnl_map, series_f, path: str,
                             problems: list[str]) -> None:
    """study.py's `d_tp[engine][scenario]` (date -> usd — EXACTLY the
    source dict `executable[engine][scenario]`'s pooled pairs are built
    from: `pairs = [(d, pnl[d]) for d in tp_days]` and `d_tp[engine][name]
    = {d: pnl[d] for d in tp_days}` share the identical pnl values,
    s0/study.py `build_study`) against the formal payload's OWN declared
    pooled (date, usd) series — a byte-identical POPULATION and VALUE
    cross-check against the internal source, never merely the schema/
    percentile-key check that already exists at the payload-only boundary
    (`_check_series_block`)."""
    if not isinstance(pnl_map, dict) or not isinstance(series_f, list):
        problems.append(f"reconcile_oracle_series_missing:{path}")
        return
    f_map: dict[str, float] = {}
    for pair in series_f:
        if (isinstance(pair, list) and len(pair) == 2
                and _is_date_str(pair[0]) and _is_number(pair[1])):
            f_map[pair[0]] = float(pair[1])
    if set(f_map) != set(pnl_map):
        problems.append(f"reconcile_oracle_series_date_set_mismatch:{path}")
        return
    for d, v in pnl_map.items():
        if not _is_number(v):
            continue
        fv = f_map.get(d)
        if fv is None or not math.isclose(fv, float(v), rel_tol=1e-9,
                                          abs_tol=1e-9):
            problems.append(
                f"reconcile_oracle_series_value_mismatch:{path}:{d}:"
                f"{fv}!={v}")


def reconcile_with_internal(internal, formal) -> list[str]:
    """Cross-check the FORMAL payload against the INTERNAL producer
    envelope — the dict `scripts/s0_real_run.py::build_full_study_result`
    actually returns (dataset/na_reason_counts/reported_total_na/records/
    study, plus every FORMAL_SECTIONS key, ALL in the same dict). Pass the
    RAW compute_result (or an equivalent superset) here, never the output
    of `split_envelope(...)`'s own "internal" half — that deliberately
    drops "study" (never a member of `_INTERNAL_KEYS`, never a member of
    `FORMAL_SECTIONS`), which several checks below need.

    `internal` MUST carry, at minimum:
      "study"   — the dict `itsf.s0.study.build_study(...)` returns (the
                  per-theta `d_tp` series this function recomputes from);
      "records" — {engine: {scenario: [TradePathRecord, ...]}}, the same
                  §10.1 atomic handoff the sealed JSONL files are built
                  from.
    Their absence is ITSELF a problem (`reconcile_missing_internal_key:
    <key>`), by design (mission item 4): passing the FORMAL payload as
    `internal` can NEVER vacuously succeed — the formal side never carries
    either key, so both problems fire immediately and every check that
    depends on them is skipped rather than silently "passing".

    `internal["dataset"]` (a live S0Dataset-shaped object exposing a
    `.records` tuple of day rows with `.trade_date`/`.year`/`.era`/
    `.labels.d_open`) and `internal["reported_total_na"]` are likewise
    flagged (same problem code) when absent — they unlock the stability-
    recompute and na_conservation checks respectively; when either is
    missing, only ITS OWN dependent check is skipped, never the others.

    Checks performed (mission item 4's "at minimum" list):
      1. stability_views per-bucket n/sum_usd/mean_usd/best_day/worst_day/
         n_positive/n_negative/n_zero, RECOMPUTED from `study["per_theta"]
         [theta]["d_tp"][engine][scenario]` bucketed by epoch/year/
         direction (day_meta derived from `internal["dataset"]`), compared
         against the formal `stability_views` cell;
      2. oracle_daily executable POOLED series values == study's own
         per-theta `d_tp[engine][scenario]` series — population AND value;
      3. mc_handoff_manifest record counts == len(records[engine]
         [scenario]);
      4. disclosures.na_conservation.per_table_total_na vs
         `internal["reported_total_na"]` summed by table prefix — the SAME
         Stage-D adapter counts the real `_na_conservation_block` itself
         reads, re-summed independently here rather than trusted.

    Never raises: every branch degrades to a problem string on a
    malformed/missing shape at any nesting level — the same fail-closed
    discipline as `validate_formal_payload`/`validate_sealed_files`. NOT
    wired into any sealing gate by this module (main-agent renderer work).

    M6.1.4-S1: the body now runs under `_guarded` too, so "never raises"
    holds for ARBITRARY input (hostile keys/objects included), not only
    for the malformed shapes this function's own branches anticipate.
    """
    return _guarded(
        "reconcile_with_internal",
        lambda acc: _reconcile_with_internal_inner(internal, formal, acc),
        [])


def _reconcile_with_internal_inner(internal, formal,
                                   problems: list[str]) -> list[str]:
    """`reconcile_with_internal`'s body (see that function's docstring)."""
    if not isinstance(internal, dict):
        problems.append("internal_not_dict")
        return problems
    if not isinstance(formal, dict):
        problems.append("formal_not_dict")
        return problems

    study = internal.get("study")
    if not isinstance(study, dict):
        problems.append("reconcile_missing_internal_key:study")
        study = None
    records = internal.get("records")
    if not isinstance(records, dict):
        problems.append("reconcile_missing_internal_key:records")
        records = None
    reported_total_na = internal.get("reported_total_na")
    if not isinstance(reported_total_na, dict):
        problems.append("reconcile_missing_internal_key:reported_total_na")
        reported_total_na = None
    dataset_obj = internal.get("dataset")
    if dataset_obj is None:
        problems.append("reconcile_missing_internal_key:dataset")
        day_meta = None
    else:
        day_meta = _derive_day_meta_from_dataset(dataset_obj)
        if day_meta is None:
            problems.append("reconcile_dataset_records_malformed")

    # --- 1 + 2: per-theta study cross-checks (oracle series + stability) --
    if study is not None:
        per_theta = study.get("per_theta")
        oracle_daily_f = formal.get("oracle_daily")
        stability_f = formal.get("stability_views")
        if isinstance(per_theta, dict):
            for tkey, tblock in per_theta.items():
                if not isinstance(tblock, dict):
                    continue
                d_tp = tblock.get("d_tp")
                if not isinstance(d_tp, dict):
                    continue
                tcell_f = (oracle_daily_f.get(tkey)
                          if isinstance(oracle_daily_f, dict) else None)
                ex_f = (tcell_f.get("executable")
                       if isinstance(tcell_f, dict) else None)
                stab_t_f = (stability_f.get(tkey)
                           if isinstance(stability_f, dict) else None)
                for eng, scn_map in d_tp.items():
                    if not isinstance(scn_map, dict):
                        continue
                    eng_f = ex_f.get(eng) if isinstance(ex_f, dict) else None
                    eng_stab_f = (stab_t_f.get(eng)
                                 if isinstance(stab_t_f, dict) else None)
                    for scn, pnl_map in scn_map.items():
                        cell_f = (eng_f.get(scn)
                                 if isinstance(eng_f, dict) else None)
                        pooled_f = (cell_f.get("pooled")
                                   if isinstance(cell_f, dict) else None)
                        series_f = (pooled_f.get("daily_pnl_usd")
                                   if isinstance(pooled_f, dict) else None)
                        _reconcile_oracle_series(
                            pnl_map, series_f,
                            f"oracle_daily|{tkey}|{eng}|{scn}", problems)

                        if day_meta is not None:
                            cell_stab_f = (
                                eng_stab_f.get(scn)
                                if isinstance(eng_stab_f, dict) else None)
                            _reconcile_stability_cell(
                                pnl_map, day_meta, cell_stab_f,
                                f"stability_views|{tkey}|{eng}|{scn}",
                                problems)

    # --- 3: record counts ---------------------------------------------------
    if records is not None:
        mh = formal.get("mc_handoff_manifest")
        counts = mh.get("counts") if isinstance(mh, dict) else None
        for eng, by_scn in records.items():
            if not isinstance(by_scn, dict):
                continue
            for scn, recs in by_scn.items():
                if not isinstance(recs, (list, tuple)):
                    continue
                actual_n = len(recs)
                eng_c = counts.get(eng) if isinstance(counts, dict) else None
                scn_c = eng_c.get(scn) if isinstance(eng_c, dict) else None
                reported = (scn_c.get("n_records")
                           if isinstance(scn_c, dict) else None)
                if reported != actual_n:
                    problems.append(
                        f"reconcile_record_count_mismatch:{eng}|{scn}:"
                        f"{reported}!={actual_n}")

    # --- 4: na_conservation vs the Stage-D adapter counts -------------------
    if reported_total_na is not None:
        per_table = {"features": 0, "labels": 0}
        for col, n in reported_total_na.items():
            if not isinstance(col, str) or "." not in col or not _is_int(n):
                continue
            table = col.split(".", 1)[0]
            if table in per_table:
                per_table[table] += n
        disclosures_f = formal.get("disclosures")
        nac_f = (disclosures_f.get("na_conservation")
                if isinstance(disclosures_f, dict) else None)
        totals_f = (nac_f.get("per_table_total_na")
                   if isinstance(nac_f, dict) else None)
        if not isinstance(totals_f, dict):
            problems.append("reconcile_na_conservation_missing")
        else:
            for table in ("features", "labels"):
                if totals_f.get(table) != per_table[table]:
                    problems.append(
                        f"reconcile_na_conservation_mismatch:{table}:"
                        f"{totals_f.get(table)}!={per_table[table]}")

    return problems
