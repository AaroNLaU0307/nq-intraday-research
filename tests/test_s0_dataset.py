"""Synthetic checks for itsf.s0.dataset (assembly layer).

Authored by the MAIN AGENT completing SA-4's scope after its spend-limit
termination (attribution recorded in the integration commit). No real market
data is touched; all sessions come from the generator contract documented in
tests/test_s0_context.py. Centerpiece: Aaron's 2026-07-31 mandatory
direction-semantics separation test (Case A true zero vs Case B missing
anchor) — the guard against reading missing data as "the market had no
direction".
"""
from __future__ import annotations

import numpy as np
import pytest

from test_s0_context import (
    linear_closes,
    universe_of,
    weekdays,
    zero_open30_closes,
)

from itsf.contracts import APPROVED_NA_REASONS
from itsf.s0.context import (
    MICRO_ERA_BOUNDARY,
    NA_ANCHOR_MISSING,
    NA_DIRECTION_UNDETERMINABLE,
    NA_ZERO_DIRECTION,
)
from itsf.s0.dataset import (
    DIRECTION_DIRECTIONAL,
    Y6_CONVENTIONS,
    Y6_QUANTILE_EDGES,
    Y6_RANK_EQUAL_COUNT,
    build_s0_dataset,
)

# Past the 14-day ADR warm-up in a 30-weekday universe starting 2020-01-02.
IDX_A, IDX_B, IDX_C = 20, 22, 24


def dataset_of(dates, spec=None, **kw):
    bars, uni = universe_of(dates, spec, **kw)
    return build_s0_dataset(bars, uni)


def record_for(ds, date):
    hits = [r for r in ds.records if r.trade_date == date]
    assert len(hits) == 1, f"expected exactly one record for {date}"
    return hits[0]


# ---------------------------------------------------------------------------
# Aaron 2026-07-31 mandatory hard test — direction semantics separation
# ---------------------------------------------------------------------------

def test_direction_case_a_true_zero_is_l82():
    """Case A: O09:30 and C09:59 both EXIST and are EQUAL -> frozen-L82 zero
    direction, non-tradeable, never an oracle candidate."""
    dates = weekdays("2020-01-02", 30)
    day = dates[IDX_A]
    ds = dataset_of(dates, {day: {"closes": zero_open30_closes(20000.0)}})
    r = record_for(ds, day)
    assert r.direction_status == NA_ZERO_DIRECTION
    assert r.direction_na_cause == ""            # a market fact, not an NA
    assert r.non_tradeable_no_direction is True
    assert r.tradeable_direction is False
    assert r.oracle_candidate is False
    assert r.labels.d_open == 0


def test_direction_case_b_missing_anchor_is_undeterminable_not_l82():
    """Case B: the 09:30 anchor bar is ABSENT -> direction undeterminable.
    Must NOT be classified as L82 zero direction and must NOT enter any
    tradeable/oracle candidate set."""
    dates = weekdays("2020-01-02", 30)
    day = dates[IDX_B]
    ds = dataset_of(dates, {day: {"skip_minutes": (570,)}})
    r = record_for(ds, day)
    assert r.direction_status == NA_DIRECTION_UNDETERMINABLE
    assert r.direction_status != NA_ZERO_DIRECTION
    assert r.direction_na_cause == NA_ANCHOR_MISSING
    assert r.non_tradeable_no_direction is True
    assert r.oracle_candidate is False
    # the day itself STAYS in the sample (frozen L45)
    assert r.trade_date == day


def test_case_a_and_case_b_never_merged_in_any_table():
    """The two classes must stay separate in the NA table, the day-status
    table and the frequency structure (Aaron ruling: no merging anywhere)."""
    dates = weekdays("2020-01-02", 30)
    a_day, b_day = dates[IDX_A], dates[IDX_B]
    ds = dataset_of(dates, {a_day: {"closes": zero_open30_closes(20000.0)},
                            b_day: {"skip_minutes": (570,)}})
    direction = ds.na_table["direction"]
    assert direction[NA_ZERO_DIRECTION] == 1
    # undeterminable = the missing-anchor day PLUS the 14 ADR-warm-up days
    # (ret_open30 NA -> direction undeterminable BY DESIGN, never L82 zero):
    assert direction[NA_DIRECTION_UNDETERMINABLE] == 15
    assert (direction[DIRECTION_DIRECTIONAL]
            + direction[NA_ZERO_DIRECTION]
            + direction[NA_DIRECTION_UNDETERMINABLE]) == len(ds.records)

    tbl = ds.day_status_table
    assert set(tbl.loc[tbl.trade_date == a_day,
                       "direction_status"]) == {NA_ZERO_DIRECTION}
    assert set(tbl.loc[tbl.trade_date == b_day,
                       "direction_status"]) == {NA_DIRECTION_UNDETERMINABLE}

    overall = ds.frequency["overall"]
    assert overall["zero_direction_days_l82"] == 1
    assert overall["direction_undeterminable_days"] == 15
    assert ds.na_table["checks"][
        "zero_direction_and_undeterminable_reported_separately"] is True


# ---------------------------------------------------------------------------
# assembly / assertion counts
# ---------------------------------------------------------------------------

def test_assembly_population_and_assertion_counts_shape():
    dates = weekdays("2020-01-02", 30)
    ds = dataset_of(dates)
    ac = ds.assertion_counts()
    assert set(ac) == {"funnel", "f10_final_mutually_exclusive", "n_records"}
    assert ac["n_records"] == len(ds.records) == ds.na_table["population"]
    # the mutually-exclusive F10 partition must sum to the record population
    assert sum(ac["f10_final_mutually_exclusive"].values()) == len(ds.records)
    # compare-only outputs: plain ints, json-serialisable
    assert all(isinstance(v, int)
               for v in ac["f10_final_mutually_exclusive"].values())


def test_features_and_labels_tables_align_with_records():
    dates = weekdays("2020-01-02", 30)
    ds = dataset_of(dates)
    assert len(ds.features_table) == len(ds.records)
    assert len(ds.labels_table) == len(ds.records)
    assert list(ds.features_table["trade_date"]) == [
        r.trade_date for r in ds.records]


# ---------------------------------------------------------------------------
# Y6 (frozen L91; binning convention pending Aaron - packet Y6_DECILE)
# ---------------------------------------------------------------------------

def test_y6_stays_pending_when_no_convention_named():
    dates = weekdays("2020-01-02", 30)
    ds = dataset_of(dates)
    assert ds.y6_convention is None
    assert ds.pending_decisions            # Y6 note present
    assert all(r.labels.y6_cont_decile is None for r in ds.records)


@pytest.mark.parametrize("convention", Y6_CONVENTIONS)
def test_y6_conventions_bounded_and_deterministic(convention):
    dates = weekdays("2020-01-02", 40)
    # distinct positive slopes -> distinct positive y_cont on directional days
    spec = {d: {"step": 0.5 + 0.05 * i} for i, d in enumerate(dates)}
    bars, uni = universe_of(dates, spec)
    ds1 = build_s0_dataset(bars, uni, y6_convention=convention)
    ds2 = build_s0_dataset(bars, uni, y6_convention=convention)
    got1 = [r.labels.y6_cont_decile for r in ds1.records]
    got2 = [r.labels.y6_cont_decile for r in ds2.records]
    assert got1 == got2                              # deterministic
    assigned = [g for g in got1 if g is not None]
    assert assigned and all(1 <= g <= 10 for g in assigned)
    # NA y_cont days (ADR warm-up era) keep Y6 = None
    for r in ds1.records:
        if r.labels.y_cont is None:
            assert r.labels.y6_cont_decile is None
    assert ds1.pending_decisions == ()               # no pending note


def test_y6_rank_equal_count_orders_min_to_max():
    dates = weekdays("2020-01-02", 40)
    spec = {d: {"step": 0.5 + 0.05 * i} for i, d in enumerate(dates)}
    bars, uni = universe_of(dates, spec)
    ds = build_s0_dataset(bars, uni, y6_convention=Y6_RANK_EQUAL_COUNT)
    scored = [(r.labels.y_cont, r.labels.y6_cont_decile)
              for r in ds.records if r.labels.y_cont is not None]
    scored.sort(key=lambda t: t[0])
    deciles = [d for _, d in scored]
    assert deciles == sorted(deciles)                # monotone in y_cont
    assert deciles[0] == 1 and deciles[-1] == 10


# ---------------------------------------------------------------------------
# NA table integrity (authorization packet section 7)
# ---------------------------------------------------------------------------

def test_na_table_reasons_all_approved_and_conserved():
    dates = weekdays("2020-01-02", 30)
    ds = dataset_of(dates, {dates[IDX_A]: {"closes": zero_open30_closes(20000.0)},
                            dates[IDX_B]: {"skip_minutes": (570,)},
                            dates[IDX_C]: {"skip_minutes": (944,)}})
    na = ds.na_table
    assert set(na["totals_by_reason"]) <= set(APPROVED_NA_REASONS)
    assert all(na["checks"].values())


def test_missing_1544_bar_is_never_substituted():
    """IR-15 / packet section 5: an absent 15:44 bar makes C1544-dependent
    labels NA — the 15:43 close must never be silently promoted."""
    dates = weekdays("2020-01-02", 30)
    day = dates[IDX_C]
    ds = dataset_of(dates, {day: {"skip_minutes": (944,)}})
    r = record_for(ds, day)
    assert r.labels.y_cont is None
    assert r.labels.y1 is None
    assert r.label_na_reasons["y_cont"] in APPROVED_NA_REASONS
    # the observation window is untouched by a pm-side gap
    assert r.features.ret_open30 is not None


# ---------------------------------------------------------------------------
# era split (frozen L109-115)
# ---------------------------------------------------------------------------

def test_era_boundary_2019_05_06_splits_records():
    dates = weekdays("2019-04-01", 40)               # spans the boundary
    ds = dataset_of(dates)
    for r in ds.records:
        if r.trade_date < MICRO_ERA_BOUNDARY:
            assert r.era == "counterfactual_micro_execution"
        else:
            assert r.era == "actual_micro_available_era"
    era_dates = set()
    for members in ds.eras.values():
        era_dates.update(members)
    assert era_dates == {r.trade_date for r in ds.records}


def test_frequency_by_year_and_month_partition_the_records():
    dates = weekdays("2020-01-02", 30)
    ds = dataset_of(dates)
    by_year = ds.frequency["by_year"]
    assert sum(c["days_in_sample"] for c in by_year.values()) == len(ds.records)
    by_month = ds.frequency["by_month"]
    assert sum(c["days_in_sample"] for c in by_month.values()) == len(ds.records)
    assert ds.frequency["thetas"] == {"primary": 0.5, "secondary": 0.3}


def test_no_real_data_paths_referenced_in_this_test_file():
    from pathlib import Path
    src = Path(__file__).read_text(encoding="utf-8")
    assert ("databento-" + "archive") not in src
    assert not np.any([False])
