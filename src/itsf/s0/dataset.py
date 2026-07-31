"""S0 DATASET assembly — per-day contexts -> feature/label tables + structure.

M5-T1 gap #2 (SA-4). This module drives the frozen formula modules over the
sample and lays the results out; it computes NO frozen formula of its own and
makes NO summary judgment. `features.py` / `labels.py` / `oracle.py` /
`costs.py` / `paths.py` are KEEP / REPLACE_PROHIBITED and are only CONSUMED.

    context.build_universe(...)  ->  build_s0_dataset(...)  ->  S0Dataset
        .features_table / .labels_table / .day_status_table
        .na_table            (every NA carries an APPROVED_NA_REASONS reason)
        .groups              (by year, leave-one-year-out, frozen L36 epochs)
        .eras                (proxy vs actual-micro axis, frozen L109-115)
        .frequency           (frozen L236 frequency output structure)
        .assertion_counts()  (funnel + F10 double report, compare-only)

Discipline (task spec section C): pure, zero I/O, zero global state, zero
print, no randomness, and no parameter that can override a frozen constant
(theta, decile count, era boundary and window lengths are module constants
with frozen citations; machine-checked in tests/test_s0_dataset.py).

Frozen sources (STUDY_0_PREREGISTRATION.md, tag s0-freeze-v1):
  L36        by-year table (mandatory) + leave-one-year-out; era slices
             2010-2013 / 2014-2017 / 2018-2021.
  L45        NA policy: every table reports its NA count; no day is deleted
             outside the three L44 exclusions.
  L82        d_open = sign(ret_open30); ret_open30 == 0 -> no direction, NOT
             tradeable, counted and reported SEPARATELY.
  L86-91     label table; Y6 = decile of Y_cont within each Development YEAR.
  L109-115   MNQ from 2019-05-06: `counterfactual_micro_execution` and
             `actual_micro_available_era` must be reported on separate axes.
  L133       continuation event = Y_cont >= theta; theta primary 0.5,
             secondary 0.3 (both reported, never promoted after the fact).
  L236       mandatory frequency output: continuation base rate p, tradeable
             days per year, Oracle monthly frequency.

DIRECTION SEMANTICS (Aaron 2026-07-31, mandatory separation)
------------------------------------------------------------
`labels.d_open_from_ret_open30` necessarily returns 0 both for a genuine
zero-direction day and for an undeterminable one, so THIS layer separates them
and they are never merged in any table, count or eligibility set:

  zero_direction_day_l82        O0930 and C0959 both EXIST and are EQUAL —
                                the market had no direction (frozen L82).
  direction_undeterminable_na   ret_open30 is NA — most importantly when
                                O0930 or C0959 is MISSING. Missing data is
                                NOT evidence of a directionless market: such a
                                day is not tradeable and never enters an
                                Oracle candidate set, but it is counted apart
                                from the frozen L82 population.

Precedence when both could apply (an ADR14 warm-up day whose two anchors exist
and are equal): the anchor-based L82 reading wins, because the market fact is
observed. That intersection is empty on the approved input set; it is stated
here so the rule is deterministic rather than incidental.
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import asdict, dataclass, replace
from typing import Mapping, Sequence

import numpy as np
import pandas as pd

from itsf.contracts import (
    APPROVED_NA_REASONS,
    DayFeatures,
    DayLabels,
    NAConservationError,
)
from itsf.data.roles import ROLE_WINDOWS as _ROLE_WINDOWS_IMPORT, DataRole
from itsf.s0 import features as features_mod
from itsf.s0 import labels as labels_mod
from itsf.s0.context import (
    MICRO_ERA_BOUNDARY,
    NA_ADR14_WARMUP,
    NA_ANCHOR_MISSING,
    NA_DEGENERATE_WINDOW,
    NA_DIRECTION_UNDETERMINABLE,
    NA_OVERNIGHT_RANGE_ZERO,
    NA_PATH_ZERO,
    NA_ZERO_DIRECTION,
    DayContext,
    S0Universe,
    iter_day_contexts,
)

# --- frozen constants (never parameters) ------------------------------------
THETA_PRIMARY = 0.5          # frozen L133 — continuation event Y_cont >= theta
THETA_SECONDARY = 0.3        # frozen L133 — reported alongside, never promoted
DECILE_COUNT = 10            # frozen L91 — Y6 within-year deciles
# frozen L24 data-role window; ENFORCED in build_s0_dataset (SA-6 F-18: these
# two names used to be imported and never read, which made the module LOOK
# range-guarded while any date could flow through).
DEV_START, DEV_END_EXCL = _ROLE_WINDOWS_IMPORT[DataRole.DEVELOPMENT_SIGNAL]
del _ROLE_WINDOWS_IMPORT     # keep module namespace free of mutable containers
ERA_PROXY = "counterfactual_micro_execution"          # frozen L109-115
ERA_ACTUAL = "actual_micro_available_era"             # frozen L109-115
STABILITY_EPOCHS = (("2010-2013", "2010", "2014"),    # frozen L36
                    ("2014-2017", "2014", "2018"),
                    ("2018-2021", "2018", "2022"))

DIRECTION_DIRECTIONAL = "directional"

# Y6 binning rule — IR-21 (APPROVED_BY_AARON 2026-07-31, resolves
# DECISION_PACKET_S0CORE_Y6_DECILE.md). THE single rule; the former runtime
# convention parameter is removed entirely (no override surface):
#   per calendar year, over that year's non-NA Y_cont days only;
#   average rank for ties (equal Y_cont ALWAYS shares a decile; splitting
#   ties by date/row order/index is prohibited);
#   percentile_rank = (average_rank - 1) / (n_year - 1);
#   decile = clip(1 + floor(10 * percentile_rank), 1, 10);
#   mechanical limit n_year == 1 -> percentile_rank = 0 -> decile 1
#   (disclosed); Y_cont NA -> Y6 NA inheriting the underlying reason.
# Descriptive-only: never enters features/Oracle/Primary/eligibility/costs.
Y6_RULE = "IR21_per_year_average_rank_decile"

# Feature fields that may be NA (frozen L45). Roll flags are structural
# booleans and are never NA; trade_date/excluded_day/exclusion_reason are not
# measurements.
FEATURE_NA_FIELDS = (
    "ret_open30", "or_width", "de_open30", "rvol_open30", "gap",
    "open_loc_on", "on_range", "retrace_open30", "close_pos_open30",
    "is_event_day", "adr14",
)
PRE_Y6_LABEL_NA_FIELDS = ("y_cont", "y1", "y2_de_pm", "y3_close_pos_pm",
                          "y4_mfe", "y5_mae")
LABEL_NA_FIELDS = PRE_Y6_LABEL_NA_FIELDS + (
    "y6_cont_decile",)                           # y6: IR-21, inherits y_cont

# Per-label frozen dependencies (L86-91), used for NA attribution and for the
# preflight-comparable label ANCHOR-availability table. MappingProxyType:
# immutable view, keeps the module namespace free of mutable containers.
from types import MappingProxyType as _MappingProxyType

_LABEL_DEPS = _MappingProxyType({
    #            O1000  C1544  ADR14  d_open   value-level reason
    "y_cont":   (True,  True,  True,  True,   ""),
    "y1":       (True,  True,  True,  False,  ""),
    "y2_de_pm": (True,  True,  False, False,  NA_PATH_ZERO),
    "y3_close_pos_pm": (False, True, False, False, NA_DEGENERATE_WINDOW),
    "y4_mfe":   (True,  False, True,  True,   ""),
    "y5_mae":   (True,  False, True,  True,   ""),
})


# ===========================================================================
# per-day record
# ===========================================================================

@dataclass(frozen=True, eq=False)
class DayRecord:
    """One structurally eligible day: frozen features + labels + status."""
    trade_date: str
    year: str
    era: str
    features: DayFeatures
    labels: DayLabels
    direction_status: str            # directional | zero_direction_day_l82 |
                                     # direction_undeterminable_na
    direction_na_cause: str          # underlying feature-level cause, if any
    non_tradeable_no_direction: bool
    tradeable_direction: bool
    oracle_candidate: bool           # direction AND Y_cont available
    feature_na_reasons: Mapping[str, str]
    label_na_reasons: Mapping[str, str]
    sidecar: Mapping[str, object]


def _year(date: str) -> str:
    return date[:4]


def _era(date: str) -> str:
    return ERA_PROXY if date < MICRO_ERA_BOUNDARY else ERA_ACTUAL


def _all_na_features(ctx: DayContext) -> DayFeatures:
    """Fallback used only when the opening window holds no bar at all.

    features.compute_day_features raises on an empty window and restating a
    frozen formula outside features.py is prohibited, so every measured field
    is NA (frozen L45: the day still stays in the sample). Unreachable on the
    approved input set — preflight reports all four anchors present on all
    2882 structurally eligible days.
    """
    return DayFeatures(
        trade_date=ctx.trade_date, is_event_day=ctx.event_flag,
        is_roll_transition=ctx.is_roll_transition,
        is_roll_window=ctx.is_roll_window, adr14=ctx.adr14)


def compute_day(ctx: DayContext) -> DayRecord:
    """Run the frozen modules for one day and attribute every NA. Pure."""
    if ctx.features_computable:
        f = features_mod.compute_day_features(**ctx.feature_kwargs())
        f = _mask_features(f, ctx)
    else:
        f = _all_na_features(ctx)

    d_open = labels_mod.d_open_from_ret_open30(f.ret_open30)
    status, cause = _direction_status(ctx, f, d_open)

    if ctx.labels_computable:
        lb = labels_mod.compute_day_labels(ctx.pm_bars, ctx.o1000, ctx.adr14,
                                           d_open)
        lb = _mask_labels(lb, ctx)
    else:
        lb = DayLabels(trade_date=ctx.trade_date, d_open=d_open)

    f_na = _attribute_feature_na(f, ctx)
    l_na = _attribute_label_na(lb, ctx, status)

    sidecar = dict(ctx.sidecar)
    sidecar["direction_status"] = status
    sidecar["direction_na_cause"] = cause

    return DayRecord(
        trade_date=ctx.trade_date, year=_year(ctx.trade_date),
        era=_era(ctx.trade_date), features=f, labels=lb,
        direction_status=status, direction_na_cause=cause,
        non_tradeable_no_direction=(d_open == 0),
        tradeable_direction=(d_open != 0),
        oracle_candidate=(d_open != 0 and lb.y_cont is not None),
        feature_na_reasons=f_na, label_na_reasons=l_na, sidecar=sidecar)


def _mask_features(f: DayFeatures, ctx: DayContext) -> DayFeatures:
    """IR-15: a missing EXACT anchor makes the dependent field NA.

    features.py reads O0930/C0959 positionally from the sliced window, which
    silently promotes a neighbouring bar when the exact anchor bar is absent.
    That substitution is forbidden, so any field the context already knows to
    be NA is forced to NA here. When both anchors are present the mask is a
    no-op, because the first/last bars of [09:30, 10:00) then ARE the anchors.
    """
    updates = {k: None for k in ctx.context_na_reasons
               if k in FEATURE_NA_FIELDS and getattr(f, k) is not None}
    return replace(f, **updates) if updates else f


def _mask_labels(lb: DayLabels, ctx: DayContext) -> DayLabels:
    """IR-15 for the pm window: labels.py takes C1544 as the last pm bar's
    close, so an absent 15:44 bar must not be substituted by its neighbour."""
    if ctx.c1544 is not None:
        return lb
    updates = {k: None for k, (_o, needs_c1544, _a, _d, _v) in _LABEL_DEPS.items()
               if needs_c1544 and getattr(lb, k) is not None}
    return replace(lb, **updates) if updates else lb


def _direction_status(ctx: DayContext, f: DayFeatures,
                      d_open: int) -> tuple[str, str]:
    """Separate frozen-L82 zero direction from undeterminable direction."""
    if d_open != 0:
        return DIRECTION_DIRECTIONAL, ""
    if ctx.o0930 is None or ctx.c0959 is None:
        # Case B: missing data is NEVER read as "the market had no direction".
        return NA_DIRECTION_UNDETERMINABLE, NA_ANCHOR_MISSING
    if ctx.c0959 == ctx.o0930:
        return NA_ZERO_DIRECTION, ""              # Case A, frozen L82
    return (NA_DIRECTION_UNDETERMINABLE,
            ctx.context_na_reasons.get("ret_open30", NA_ANCHOR_MISSING))


def _attribute_feature_na(f: DayFeatures, ctx: DayContext) -> dict[str, str]:
    """Every NA feature gets exactly one APPROVED_NA_REASONS reason.

    Context reasons (anchor / warm-up / roll transition / multi-event / empty
    overnight window) take precedence, matching the approved preflight's
    first-match ordering; value-level reasons fill the rest.
    """
    out = {k: v for k, v in ctx.context_na_reasons.items()
           if k in FEATURE_NA_FIELDS}
    if f.de_open30 is None and "de_open30" not in out:
        out["de_open30"] = NA_PATH_ZERO                   # F3, path == 0
    if f.retrace_open30 is None and "retrace_open30" not in out:
        out["retrace_open30"] = NA_ZERO_DIRECTION         # F8, |C0959-O0930|==0
    if f.close_pos_open30 is None and "close_pos_open30" not in out:
        out["close_pos_open30"] = NA_DEGENERATE_WINDOW    # F9, H == L
    if f.open_loc_on is None and "open_loc_on" not in out:
        out["open_loc_on"] = NA_OVERNIGHT_RANGE_ZERO      # F6, ruling R3
    if f.adr14 is None and "adr14" not in out:
        out["adr14"] = NA_ADR14_WARMUP
    _check_reason_coverage(f, FEATURE_NA_FIELDS, out, "features")
    return out


def _attribute_label_na(lb: DayLabels, ctx: DayContext,
                        direction_status: str) -> dict[str, str]:
    """Label NA attribution, precedence: anchor -> ADR14 -> direction -> value.

    The direction level catches every label on a d_open == 0 day because
    labels.py (REPLACE_PROHIBITED) returns bare labels there; the reason is the
    day's own direction class, so the frozen-L82 and undeterminable
    populations stay separated in the NA table too.
    """
    out: dict[str, str] = {}
    for name, (needs_o1000, needs_c1544, needs_adr,
               _needs_dir, value_reason) in _LABEL_DEPS.items():
        if getattr(lb, name) is not None:
            continue
        if (ctx.pm_window_empty
                or (needs_o1000 and ctx.o1000 is None)
                or (needs_c1544 and ctx.c1544 is None)):
            out[name] = NA_ANCHOR_MISSING
        elif needs_adr and ctx.adr14 is None:
            out[name] = NA_ADR14_WARMUP
        elif direction_status != DIRECTION_DIRECTIONAL:
            out[name] = direction_status
        elif value_reason:
            out[name] = value_reason
    # y6 is assigned AFTER the per-day pass (IR-21 within-year rank), so the
    # record-time bijection check runs on the pre-Y6 fields; build_s0_dataset
    # re-checks y6 coverage after the decile pass (fail-closed there too).
    _check_reason_coverage(lb, PRE_Y6_LABEL_NA_FIELDS, out, "labels")
    return out


def _check_reason_coverage(row: object, na_fields: Sequence[str],
                           reasons: Mapping[str, str], table: str) -> None:
    """Fail closed: NA <-> reason must be a bijection over `na_fields`."""
    for name in na_fields:
        is_na = getattr(row, name) is None
        has_reason = name in reasons
        if is_na and not has_reason:
            raise NAConservationError(
                f"{table}.{name} is NA on "
                f"{getattr(row, 'trade_date', '?')} with no reason")
        if has_reason and not is_na:
            raise NAConservationError(
                f"{table}.{name} carries reason {reasons[name]!r} on "
                f"{getattr(row, 'trade_date', '?')} but is not NA")


# ===========================================================================
# Y6 — within-year decile pass (frozen L91); rule fixed by IR-21
# ===========================================================================

def assign_y6_deciles(rows: Sequence[DayLabels]) -> tuple[DayLabels, ...]:
    """frozen L91 + IR-21 — Y6 = per-year average-rank decile of Y_cont.

    labels.py leaves y6_cont_decile None by design (the within-year
    cross-sectional rank can only exist once every day of the year exists).
    IR-21 (APPROVED 2026-07-31) fixes the binning rule — see Y6_RULE above.
    Value-only ranking: equal Y_cont always shares one decile; the input
    order, trade_date and index play NO role in the result.
    """
    by_year: dict[str, list[int]] = {}
    for i, r in enumerate(rows):
        if r.y_cont is not None:
            by_year.setdefault(_year(r.trade_date), []).append(i)

    deciles: dict[int, int] = {}
    for _year_key, idx in by_year.items():
        vals = np.asarray([float(rows[i].y_cont) for i in idx], dtype=float)
        n = len(vals)
        order = np.argsort(vals, kind="stable")
        # average rank (1-based) per tie-group of EQUAL values
        avg_rank = np.empty(n, dtype=float)
        pos = 0
        while pos < n:
            end = pos
            while end + 1 < n and vals[order[end + 1]] == vals[order[pos]]:
                end += 1
            avg = (pos + 1 + end + 1) / 2.0
            for j in range(pos, end + 1):
                avg_rank[order[j]] = avg
            pos = end + 1
        for k, i in enumerate(idx):
            pr = 0.0 if n == 1 else (avg_rank[k] - 1.0) / (n - 1.0)
            deciles[i] = int(min(DECILE_COUNT,
                                 max(1, 1 + math.floor(DECILE_COUNT * pr))))
    return tuple(replace(r, y6_cont_decile=deciles[i]) if i in deciles else r
                 for i, r in enumerate(rows))


# ===========================================================================
# dataset
# ===========================================================================

@dataclass(frozen=True, eq=False)
class S0Dataset:
    """Structures and tables only — no summary statistic is judged here."""
    records: tuple[DayRecord, ...]
    features_table: pd.DataFrame
    labels_table: pd.DataFrame
    day_status_table: pd.DataFrame
    exclusions_table: pd.DataFrame
    na_table: Mapping[str, object]
    label_anchor_availability: Mapping[str, Mapping[str, int]]
    groups: Mapping[str, Mapping[str, tuple[str, ...]]]
    eras: Mapping[str, tuple[str, ...]]
    frequency: Mapping[str, object]
    funnel_counts: Mapping[str, int]
    f10_counts: Mapping[str, int]
    f10_raw_membership_counts: Mapping[str, int]
    sidecar_table: pd.DataFrame
    y6_rule: str                     # always Y6_RULE (IR-21; no options)
    pending_decisions: tuple[str, ...]

    def assertion_counts(self) -> dict[str, object]:
        """Independently computed structural counts for the runner to COMPARE
        against expected_preflight_assertions. Compare-only: these numbers are
        outputs, never inputs (authorization packet S5).

        F10 is reported TWICE — raw category membership and the final
        mutually-exclusive partition (approved report governance (1); SA-6
        F-12). Both are preflight-comparable
        (f10.raw_category_membership_counts_eligible and
        f10.final_mutually_exclusive_F10_counts_eligible)."""
        return {"funnel": dict(self.funnel_counts),
                "f10_raw_category_membership":
                    dict(self.f10_raw_membership_counts),
                "f10_final_mutually_exclusive": dict(self.f10_counts),
                "n_records": len(self.records)}


def build_s0_dataset(bars_by_date: Mapping[str, pd.DataFrame],
                     universe: S0Universe) -> S0Dataset:
    """Assemble the S0 dataset. Pure; no I/O, no randomness, no judgment.

    Y6 is ALWAYS assigned per IR-21 (the sole rule; the former runtime
    convention parameter is deliberately removed — no override surface).
    Y6 NA inherits the underlying y_cont NA reason (IR-21: no new reason
    is ever invented), applied AFTER the decile pass so the attribution
    reflects final labels.
    """
    records = [compute_day(ctx)
               for ctx in iter_day_contexts(bars_by_date, universe)]
    _assert_development_window(records)

    pending: list[str] = []
    assigned = assign_y6_deciles([r.labels for r in records])
    post: list[DayRecord] = []
    for r, lb in zip(records, assigned):
        lna = dict(r.label_na_reasons)
        if lb.y6_cont_decile is None:
            reason = lna.get("y_cont")
            if reason:                       # inherit; never invent (IR-21)
                lna["y6_cont_decile"] = reason
        # post-assignment fail-closed bijection check over ALL label fields
        _check_reason_coverage(lb, LABEL_NA_FIELDS, lna, "labels")
        post.append(replace(r, labels=lb, label_na_reasons=lna))
    records = post

    features_table = _table([asdict(r.features) for r in records])
    labels_table = _labels_table(records)
    day_status_table = _table([{
        "trade_date": r.trade_date, "year": r.year, "era": r.era,
        "d_open": r.labels.d_open, "direction_status": r.direction_status,
        "direction_na_cause": r.direction_na_cause,
        "non_tradeable_no_direction": r.non_tradeable_no_direction,
        "tradeable_direction": r.tradeable_direction,
        "oracle_candidate": r.oracle_candidate,
        "is_roll_transition": r.features.is_roll_transition,
        "is_roll_window": r.features.is_roll_window,
    } for r in records])
    sidecar_table = _table([dict(r.sidecar, trade_date=r.trade_date)
                            for r in records])

    funnel = universe.funnel
    exclusions_table = _table([
        {"trade_date": d, "exclusion_reason": funnel.exclusion_reason[d]}
        for d in sorted(funnel.exclusion_reason)])

    return S0Dataset(
        records=tuple(records),
        features_table=features_table,
        labels_table=labels_table,
        day_status_table=day_status_table,
        exclusions_table=exclusions_table,
        na_table=build_na_table(records),
        label_anchor_availability=_label_anchor_availability(
            universe, records),
        groups=_groups(records),
        eras=_eras(records),
        frequency=build_frequency_structure(records),
        funnel_counts=funnel.counts(),
        f10_counts=universe.f10_exclusive_counts(),
        f10_raw_membership_counts=universe.raw_category_membership_counts(),
        sidecar_table=sidecar_table,
        y6_rule=Y6_RULE,
        pending_decisions=tuple(pending))


def _table(rows: Sequence[Mapping[str, object]]) -> pd.DataFrame:
    return pd.DataFrame(list(rows))


def _labels_table(records: Sequence[DayRecord]) -> pd.DataFrame:
    """Label table with Y6 kept an ORDINAL nullable integer (SA-6 F-28).

    `pd.DataFrame` infers float64 for an int column holding NA, which turns
    decile 3 into `3.0` and NA into `NaN`: a bin index then reads as a
    continuous score in every downstream table, and NA silently joins the
    float NaN family instead of the reported NA population. Int64 keeps the
    frozen L91 decile an integer 1..10 with a distinct pd.NA.
    """
    table = _table([asdict(r.labels) for r in records])
    if "y6_cont_decile" in table.columns:
        table["y6_cont_decile"] = table["y6_cont_decile"].astype("Int64")
    return table


def _assert_development_window(records: Sequence[DayRecord]) -> None:
    """Every record date must lie in [DEV_START, DEV_END_EXCL) — fail closed.

    frozen L24 data-role window + PROJECT_CHARTER clause 14 (role isolation).
    SA-6 F-18: the two constants were imported and never read, so the module
    advertised a boundary it did not check; an Internal-Validation-era date
    would have assembled into an S0 table without a word. Real check, on the
    dates that actually became records.
    """
    outside = [r.trade_date for r in records
               if not (DEV_START <= r.trade_date < DEV_END_EXCL)]
    if outside:
        raise ValueError(
            f"{len(outside)} record date(s) outside the frozen Development "
            f"window [{DEV_START}, {DEV_END_EXCL}): {outside[:5]} — fail "
            "closed (frozen L24 data-role window, charter clause 14)")


# --- NA table (frozen L45) --------------------------------------------------

def build_na_table(records: Sequence[DayRecord]) -> dict[str, object]:
    """Per-field NA counts by reason, plus conservation checks.

    Every reason must be in contracts.APPROVED_NA_REASONS — an unapproved
    reason raises NAConservationError here rather than surviving into a report
    (authorization packet S7 NA integrity). zero_direction_day_l82 and
    direction_undeterminable_na are separate rows and are never summed.
    """
    n = len(records)
    per_field: dict[str, dict[str, dict[str, int]]] = {
        "features": {}, "labels": {}}
    for table, fields, attr in (("features", FEATURE_NA_FIELDS,
                                 "feature_na_reasons"),
                                ("labels", LABEL_NA_FIELDS,
                                 "label_na_reasons")):
        for field in fields:
            counter: Counter = Counter()
            for r in records:
                reason = getattr(r, attr).get(field)
                if reason:
                    counter[reason] += 1
            per_field[table][field] = {
                "na": int(sum(counter.values())),
                "not_na": n - int(sum(counter.values())),
                "reasons": dict(sorted(counter.items())),
            }

    direction = Counter(r.direction_status for r in records)
    totals: Counter = Counter()
    for r in records:
        totals.update(r.feature_na_reasons.values())
        totals.update(r.label_na_reasons.values())

    unapproved = sorted(set(totals) - set(APPROVED_NA_REASONS))
    if unapproved:
        raise NAConservationError(
            f"NA reasons outside APPROVED_NA_REASONS: {unapproved}")

    checks = {
        "every_reason_approved": True,
        "per_field_na_plus_not_na_equals_population": all(
            v["na"] + v["not_na"] == n
            for t in per_field.values() for v in t.values()),
        "per_field_reason_counts_sum_to_na": all(
            sum(v["reasons"].values()) == v["na"]
            for t in per_field.values() for v in t.values()),
        "direction_classes_sum_to_population":
            sum(direction.values()) == n,
        "zero_direction_and_undeterminable_reported_separately":
            NA_ZERO_DIRECTION != NA_DIRECTION_UNDETERMINABLE,
    }
    return {
        "population": n,
        "per_field": per_field,
        "direction": {
            DIRECTION_DIRECTIONAL: direction[DIRECTION_DIRECTIONAL],
            NA_ZERO_DIRECTION: direction[NA_ZERO_DIRECTION],
            NA_DIRECTION_UNDETERMINABLE: direction[NA_DIRECTION_UNDETERMINABLE],
        },
        "totals_by_reason": dict(sorted(totals.items())),
        "checks": checks,
    }


def _label_anchor_availability(universe: S0Universe,
                               records: Sequence[DayRecord],
                               ) -> dict[str, dict[str, int]]:
    """Label ANCHOR existence (frozen L86-91), preflight-comparable.

    Distinct from the label NA counts: labels.py (REPLACE_PROHIBITED) returns
    bare labels on every d_open == 0 day, so the descriptive Y1/Y2/Y3 are NA
    there even though their anchors exist. This table reports anchor existence
    exactly as the approved preflight does, so the runner compares like with
    like; the divergence is disclosed in the SA-4 report.
    """
    out = {k: {"available_days": 0, "unavailable_days": 0}
           for k in _LABEL_DEPS}
    for r in records:
        d = r.trade_date
        s = universe.summaries[d]
        o1000 = not np.isnan(s.o1000)
        c1544 = not np.isnan(s.c1544)
        pm_ok = s.pm_present > 0
        adr_ok = universe.adr14[d] is not None
        dir_ok = r.direction_status == DIRECTION_DIRECTIONAL
        ok = {
            "y_cont": o1000 and c1544 and adr_ok and dir_ok,
            "y1": o1000 and c1544 and adr_ok,
            "y2_de_pm": o1000 and c1544 and pm_ok,
            "y3_close_pos_pm": c1544 and pm_ok,
            "y4_mfe": o1000 and pm_ok and adr_ok and dir_ok,
            "y5_mae": o1000 and pm_ok and adr_ok and dir_ok,
        }
        for k, good in ok.items():
            out[k]["available_days" if good else "unavailable_days"] += 1
    return out


# --- groupings (frozen L36 / L109-115) --------------------------------------

def _groups(records: Sequence[DayRecord]
            ) -> dict[str, dict[str, tuple[str, ...]]]:
    by_year: dict[str, list[str]] = {}
    for r in records:
        by_year.setdefault(r.year, []).append(r.trade_date)
    years = {y: tuple(v) for y, v in sorted(by_year.items())}
    loyo = {y: tuple(r.trade_date for r in records if r.year != y)
            for y in years}
    epochs = {name: tuple(r.trade_date for r in records
                          if lo <= r.year < hi)
              for name, lo, hi in STABILITY_EPOCHS}
    return {"by_year": years, "leave_one_year_out": loyo,
            "stability_epochs": epochs}


def _eras(records: Sequence[DayRecord]) -> dict[str, tuple[str, ...]]:
    return {
        ERA_PROXY: tuple(r.trade_date for r in records if r.era == ERA_PROXY),
        ERA_ACTUAL: tuple(r.trade_date for r in records if r.era == ERA_ACTUAL),
    }


# --- frequency output structure (frozen L236) -------------------------------

def _frequency_cell(rows: Sequence[DayRecord]) -> dict[str, object]:
    y_cont = [r.labels.y_cont for r in rows if r.labels.y_cont is not None]
    cont_primary = sum(1 for v in y_cont if v >= THETA_PRIMARY)
    cont_secondary = sum(1 for v in y_cont if v >= THETA_SECONDARY)
    return {
        "days_in_sample": len(rows),
        "tradeable_days": sum(1 for r in rows if r.tradeable_direction),
        "zero_direction_days_l82": sum(
            1 for r in rows if r.direction_status == NA_ZERO_DIRECTION),
        "direction_undeterminable_days": sum(
            1 for r in rows
            if r.direction_status == NA_DIRECTION_UNDETERMINABLE),
        "y_cont_available_days": len(y_cont),
        "continuation_days_theta_primary": cont_primary,
        "continuation_days_theta_secondary": cont_secondary,
        "continuation_base_rate_theta_primary":
            (cont_primary / len(y_cont)) if y_cont else None,
        "continuation_base_rate_theta_secondary":
            (cont_secondary / len(y_cont)) if y_cont else None,
    }


def build_frequency_structure(records: Sequence[DayRecord]
                              ) -> dict[str, object]:
    """frozen L236 — continuation base rate p, tradeable days per year and the
    monthly frequency, as a STRUCTURE. Counts and their mechanical ratios only:
    no threshold is judged and no verdict is formed here (thetas are the frozen
    L133 pair, both always reported)."""
    by_year: dict[str, list[DayRecord]] = {}
    by_month: dict[str, list[DayRecord]] = {}
    for r in records:
        by_year.setdefault(r.year, []).append(r)
        by_month.setdefault(r.trade_date[:7], []).append(r)

    months = sorted(by_month)
    overall = _frequency_cell(records)
    overall["n_months_in_sample"] = len(months)
    for key in ("primary", "secondary"):
        overall[f"oracle_monthly_frequency_theta_{key}"] = (
            overall[f"continuation_days_theta_{key}"] / len(months)
            if months else None)

    return {
        "thetas": {"primary": THETA_PRIMARY, "secondary": THETA_SECONDARY},
        "by_year": {y: _frequency_cell(v) for y, v in sorted(by_year.items())},
        "by_month": {m: _frequency_cell(by_month[m]) for m in months},
        "by_era": {era: _frequency_cell([r for r in records if r.era == era])
                   for era in (ERA_PROXY, ERA_ACTUAL)},
        "overall": overall,
        "note": ("structure only; appendix-A grid expectations and any GO/STOP "
                 "reading are downstream of S0"),
    }
