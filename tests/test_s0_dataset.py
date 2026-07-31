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
import pandas as pd
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
    EventCalendar,
    RollInterval,
)
from itsf.s0.dataset import (
    DEV_END_EXCL,
    DEV_START,
    DIRECTION_DIRECTIONAL,
    Y6_RULE,
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
    assert set(ac) == {"funnel", "f10_raw_category_membership",
                       "f10_final_mutually_exclusive", "n_records"}
    assert ac["n_records"] == len(ds.records) == ds.na_table["population"]
    # the mutually-exclusive F10 partition must sum to the record population
    assert sum(ac["f10_final_mutually_exclusive"].values()) == len(ds.records)
    # compare-only outputs: plain ints, json-serialisable
    for key in ("f10_final_mutually_exclusive", "f10_raw_category_membership"):
        assert all(isinstance(v, int) for v in ac[key].values())


def test_f10_is_double_reported_raw_membership_and_exclusive_partition():
    """Approved report governance (1) / SA-6 F-12: the mutually-exclusive
    partition alone hides how many days a category actually touched, because a
    two-category day leaves CPI and NFP and reappears as NA_multi_event. Both
    reports must be produced, and they must reconcile."""
    dates = weekdays("2020-01-02", 30)
    cpi_only, both, nfp_only = dates[10], dates[12], dates[14]
    unscheduled = dates[16]
    events = EventCalendar(
        cpi_dates=frozenset({cpi_only, both}),
        nfp_dates=frozenset({both, nfp_only}),
        fomc_statement_dates=frozenset({unscheduled}),
        unscheduled_fomc_dates=frozenset({unscheduled}),
        raw_multi_event_dates=frozenset({both}))
    ds = dataset_of(dates, events=events)
    raw, exclusive = ds.f10_raw_membership_counts, ds.f10_counts

    # multi-hot: the two-category day is counted under BOTH categories ...
    assert raw["CPI"] == 2 and raw["NFP"] == 2
    # ... while the partition drops it into its own NA class
    assert exclusive["CPI"] == 1 and exclusive["NFP"] == 1
    assert exclusive["NA_multi_event"] == 1
    # IR-13 first: an unscheduled FOMC action is not an F10 FOMC day anywhere
    assert raw["FOMC"] == 0 and exclusive["FOMC"] == 0
    # the reconciliation identities of the double report
    for category in ("CPI", "NFP", "FOMC", "none"):
        assert raw[category] >= exclusive[category], category
    assert raw["multi_category"] == exclusive["NA_multi_event"]
    assert raw["none"] == exclusive["none"] == 30 - 3
    assert sum(exclusive.values()) == len(ds.records)
    # raw membership does NOT partition the population, by construction
    assert raw["CPI"] + raw["NFP"] + raw["FOMC"] + raw["none"] > len(ds.records)
    assert ds.assertion_counts()["f10_raw_category_membership"] == raw


def test_records_outside_the_development_window_fail_closed():
    """SA-6 F-18: DEV_START/DEV_END_EXCL were imported and never read, so the
    module advertised a boundary it never checked. Real range assertion now
    (frozen L24 data-role window, charter clause 14 role isolation)."""
    assert (DEV_START, DEV_END_EXCL) == ("2010-06-06", "2022-01-01")
    inside = weekdays("2021-11-01", 30)
    assert all(DEV_START <= d < DEV_END_EXCL for d in inside)
    assert len(dataset_of(inside).records) == 30           # in-window: fine

    outside = weekdays("2022-01-03", 30)                   # IV era dates
    bars, uni = universe_of(outside)
    assert len(uni.funnel.structurally_eligible) == 30     # the days exist ...
    with pytest.raises(ValueError, match="Development window"):
        build_s0_dataset(bars, uni)                        # ... and are refused

    straddling = weekdays("2021-12-20", 20)                # crosses 2022-01-01
    bars2, uni2 = universe_of(straddling)
    with pytest.raises(ValueError, match=r"record date\(s\) outside"):
        build_s0_dataset(bars2, uni2)


def test_features_and_labels_tables_align_with_records():
    dates = weekdays("2020-01-02", 30)
    ds = dataset_of(dates)
    assert len(ds.features_table) == len(ds.records)
    assert len(ds.labels_table) == len(ds.records)
    assert list(ds.features_table["trade_date"]) == [
        r.trade_date for r in ds.records]


# ---------------------------------------------------------------------------
# Y6 — IR-21 (APPROVED 2026-07-31): per-year average-rank decile
# ---------------------------------------------------------------------------

def _y6_universe(dates, extra_spec=None):
    spec = {d: {"step": 0.5 + 0.05 * i} for i, d in enumerate(dates)}
    spec.update(extra_spec or {})
    return universe_of(dates, spec)


def test_y6_always_assigned_min_1_max_10_and_rule_recorded():
    dates = weekdays("2020-01-02", 40)
    bars, uni = _y6_universe(dates)
    ds = build_s0_dataset(bars, uni)
    assert ds.y6_rule == Y6_RULE
    assert ds.pending_decisions == ()
    scored = [(r.labels.y_cont, r.labels.y6_cont_decile)
              for r in ds.records if r.labels.y_cont is not None]
    scored.sort(key=lambda t: t[0])
    deciles = [d for _, d in scored]
    assert deciles == sorted(deciles)                # monotone in y_cont
    assert deciles[0] == 1 and deciles[-1] == 10     # lowest=1, highest=10


def test_y6_equal_y_cont_always_shares_a_decile():
    """IR-21 tie rule: identical Y_cont must NEVER be split across deciles."""
    dates = weekdays("2020-01-02", 40)
    same = dates[20:30]                              # 10 identical-step days
    bars, uni = _y6_universe(dates, {d: {"step": 2.0} for d in same})
    ds = build_s0_dataset(bars, uni)
    by_val: dict[float, set[int]] = {}
    for r in ds.records:
        if r.labels.y_cont is not None:
            by_val.setdefault(round(r.labels.y_cont, 9), set()).add(
                r.labels.y6_cont_decile)
    assert all(len(s) == 1 for s in by_val.values())


def test_y6_input_row_order_never_changes_the_result():
    dates = weekdays("2020-01-02", 40)
    bars, uni = _y6_universe(dates)
    ds_fwd = build_s0_dataset(dict(bars), uni)
    ds_rev = build_s0_dataset(dict(reversed(list(bars.items()))), uni)
    fwd = {r.trade_date: r.labels.y6_cont_decile for r in ds_fwd.records}
    rev = {r.trade_date: r.labels.y6_cont_decile for r in ds_rev.records}
    assert fwd == rev


def test_y6_years_rank_independently():
    """Cross-year independence: a huge-Y_cont year must not compress another
    year's deciles."""
    dates = weekdays("2020-12-01", 44)               # spans 2020 -> 2021
    spec = {}
    for i, d in enumerate(dates):
        spec[d] = {"step": (0.5 + 0.05 * i) * (10.0 if d < "2021" else 1.0)}
    bars, uni = universe_of(dates, spec)
    ds = build_s0_dataset(bars, uni)
    for year in ("2020", "2021"):
        year_deciles = [r.labels.y6_cont_decile for r in ds.records
                        if r.year == year and r.labels.y_cont is not None]
        if len(year_deciles) > 1:
            assert min(year_deciles) == 1            # each year owns its scale
            assert max(year_deciles) == 10


def test_y6_na_propagates_and_inherits_the_underlying_reason():
    dates = weekdays("2020-01-02", 30)
    bars, uni = _y6_universe(
        dates, {dates[IDX_A]: {"closes": zero_open30_closes(20000.0)}})
    ds = build_s0_dataset(bars, uni)
    for r in ds.records:
        if r.labels.y_cont is None:
            assert r.labels.y6_cont_decile is None
            # IR-21: inherit the y_cont reason, never invent a new one
            assert (r.label_na_reasons.get("y6_cont_decile")
                    == r.label_na_reasons.get("y_cont"))
        else:
            assert r.labels.y6_cont_decile is not None


def test_labels_table_keeps_y6_a_nullable_integer_decile():
    """SA-6 F-28: pandas infers float64 for an int column holding NA, so the
    frozen L91 decile arrived downstream as 3.0 with NaN for NA — an ordinal
    bin reading as a continuous score, and an NA merged into the float NaN
    family instead of the reported NA population."""
    dates = weekdays("2020-01-02", 30)
    bars, uni = _y6_universe(
        dates, {dates[IDX_A]: {"closes": zero_open30_closes(20000.0)}})
    ds = build_s0_dataset(bars, uni)
    col = ds.labels_table["y6_cont_decile"]
    assert str(col.dtype) == "Int64"                 # nullable INT, not float
    assert col.isna().any()                          # the fixture holds NAs
    values = col.dropna().tolist()
    assert values
    assert all(isinstance(v, (int, np.integer)) and not isinstance(v, bool)
               for v in values)
    assert all(1 <= v <= 10 for v in values)
    # the table agrees with the records it is built from
    from_records = [r.labels.y6_cont_decile for r in ds.records]
    assert [None if v is pd.NA else int(v) for v in col.tolist()] == from_records


def test_y6_partial_calendar_year_ranks_on_its_own_days():
    """An incomplete year (like 2010 starting 2010-06-06) still ranks over
    whatever Development days it has."""
    dates = weekdays("2020-06-01", 30)               # second-half year only
    bars, uni = _y6_universe(dates)
    ds = build_s0_dataset(bars, uni)
    got = [r.labels.y6_cont_decile for r in ds.records
           if r.labels.y_cont is not None]
    assert got and min(got) == 1 and max(got) == 10


def test_y6_cannot_enter_oracle_or_candidate_paths():
    """IR-21 use_restriction, machine-checked: no oracle/costs/paths/features
    callable accepts labels or y6; oracle_candidate never reads y6."""
    import inspect
    from itsf.s0 import costs, oracle, paths
    from itsf.s0 import features as f_mod
    for mod in (oracle, costs, paths, f_mod):
        for name, fn in inspect.getmembers(mod, inspect.isfunction):
            params = set(inspect.signature(fn).parameters)
            assert not params & {"y6", "y6_cont_decile", "labels",
                                 "day_labels"}, (mod.__name__, name)
        src = inspect.getsource(mod)
        assert "y6" not in src.lower(), mod.__name__
    # dataset-side: candidate flag is direction+y_cont only, independent of y6
    dates = weekdays("2020-01-02", 30)
    bars, uni = _y6_universe(dates)
    ds = build_s0_dataset(bars, uni)
    for r in ds.records:
        assert r.oracle_candidate == (
            r.labels.d_open != 0 and r.labels.y_cont is not None)


def test_y6_no_date_or_index_tiebreak_in_source():
    """IR-21 forbids breaking a Y_cont tie by date, row order or index.

    SA-6 test-effectiveness finding: the second assertion used to end in
    `or True`, so it could not fail whatever the source said. Real check now —
    the function is parsed and the RANKING pass must not mention a date or an
    index at all, while the year-GROUPING pass legitimately may (the year key
    comes from the trade date). Behaviour stays pinned by the two tests above.
    """
    import ast
    import inspect
    import textwrap
    from itsf.s0 import dataset as ds_mod
    src = inspect.getsource(ds_mod.assign_y6_deciles)
    assert 'method="first"' not in src and "method='first'" not in src

    fn = ast.parse(textwrap.dedent(src)).body[0]
    loops = [n for n in fn.body if isinstance(n, ast.For)]
    assert len(loops) == 2, "expected one grouping pass and one ranking pass"
    grouping, ranking = loops
    assert "trade_date" in ast.dump(grouping)     # the year key, legitimately
    dumped = ast.dump(ranking)
    for banned in ("trade_date", "date", "index", "sort_values", "sort_index"):
        assert banned not in dumped, f"ranking pass reads {banned!r}"
    # the ordering is derived from the VALUES and from nothing else
    sorts = [n for n in ast.walk(ranking)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
             and "sort" in n.func.attr]
    assert len(sorts) == 1, "exactly one ordering call expected"
    assert [a.id for a in sorts[0].args if isinstance(a, ast.Name)] == ["vals"]


def _s0_module_sources(exclude: tuple[str, ...] = ("dataset",)) -> dict:
    """{module stem: source} for every module under itsf.s0 except `exclude`.

    Read from disk, never imported: the check must cover every module in the
    package — including ones owned by other agents — without executing them.
    """
    from pathlib import Path
    import itsf.s0
    pkg_dir = Path(itsf.s0.__file__).resolve().parent
    return {p.stem: p.read_text(encoding="utf-8")
            for p in sorted(pkg_dir.glob("*.py"))
            if p.stem != "__init__" and p.stem not in exclude}


Y6_NAMES = {"y6", "y6_cont_decile"}


def test_y6_is_never_read_by_any_other_module_under_itsf_s0():
    """IR-21 use_restriction over the WHOLE package (SA-6 F-22).

    The original isolation test named four modules by hand, so every other
    module of the package — context, labels, runner, runinfra and anything
    added later — was a blind spot. Y6 is descriptive-only: outside dataset.py
    no module may READ a y6 value, as a parameter, an attribute, a bare name
    or a table key. labels.py may only WRITE the literal None (the field
    exists there; a value never does).
    """
    import ast
    sources = _s0_module_sources()
    assert {"context", "labels", "features", "oracle", "costs",
            "paths"} <= set(sources), sorted(sources)
    for name, src in sources.items():
        try:
            tree = ast.parse(src, filename=f"{name}.py")
        except (SyntaxError, ValueError):
            # A module that cannot be parsed is NEVER skipped (that would
            # recreate the blind spot this test exists to close): it falls
            # back to the strictly stronger text rule instead.
            assert "y6" not in src.lower(), name
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args = node.args
                params = [*args.posonlyargs, *args.args, *args.kwonlyargs]
                params += [a for a in (args.vararg, args.kwarg) if a]
                assert not {p.arg.lower() for p in params} & Y6_NAMES, (
                    name, node.name)
            elif isinstance(node, ast.Attribute) and isinstance(node.ctx,
                                                                ast.Load):
                assert node.attr.lower() not in Y6_NAMES, (name, node.attr)
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                assert node.id.lower() not in Y6_NAMES, (name, node.id)
            elif (isinstance(node, ast.Subscript)
                  and isinstance(node.slice, ast.Constant)
                  and isinstance(node.slice.value, str)):
                assert "y6" not in node.slice.value.lower(), (name,
                                                              node.slice.value)
            elif isinstance(node, ast.keyword) and node.arg in Y6_NAMES:
                assert (isinstance(node.value, ast.Constant)
                        and node.value.value is None), (name, node.arg)


ROLL_NAMES = {"is_roll_window", "is_roll_transition", "roll_window",
              "roll_transition", "roll_intervals", "roll_transitions", "roll"}


def test_roll_window_cannot_enter_oracle_paths():
    """F11 roll flags are DESCRIPTIVE calendar facts (frozen L30-32): the
    Oracle / cost / path layers must never read them and no eligibility set
    may be gated on them. Counterpart of the Y6 isolation test (SA-6 F-21).
    features.py is deliberately absent from the module list — F11 IS a feature.
    """
    import inspect
    from itsf.s0 import costs, oracle, paths
    for mod in (oracle, costs, paths):
        for name, fn in inspect.getmembers(mod, inspect.isfunction):
            params = {p.lower() for p in inspect.signature(fn).parameters}
            assert not params & ROLL_NAMES, (mod.__name__, name)
        src = inspect.getsource(mod)
        for token in ("roll_window", "roll_transition", "is_roll"):
            assert token not in src, (mod.__name__, token)

    # behavioural: a roll TRANSITION day loses F5 (frozen L57) and nothing
    # else — it stays in the sample (frozen L45) and stays an oracle candidate.
    dates = weekdays("2020-01-02", 40)
    switch = dates[20]
    intervals = (RollInterval("2019-12-01", switch, "NQZ9", 1),
                 RollInterval(switch, "2020-06-01", "NQH0", 2))
    bars, uni = universe_of(dates, roll_intervals=intervals)
    ds = build_s0_dataset(bars, uni)
    window_days = set(uni.roll_window_dates)
    assert switch in window_days and len(window_days) == 5     # +-2 RTH days
    assert window_days <= {r.trade_date for r in ds.records}
    r = record_for(ds, switch)
    assert r.features.is_roll_transition is True
    assert r.features.gap is None
    assert r.feature_na_reasons["gap"] == "roll_transition_day_na"
    assert r.labels.y_cont is not None
    assert r.oracle_candidate is True
    for rec in ds.records:
        assert rec.oracle_candidate == (rec.labels.d_open != 0
                                        and rec.labels.y_cont is not None)


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
