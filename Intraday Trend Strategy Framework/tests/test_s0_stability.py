"""Synthetic checks for itsf.s0.stability (frozen S0 §2 Development stability
views).

SA-18-style scope. Every series here is a hand-written dict of fabricated
dates/years/pnl: no real archive is touched, no clock is read, and this
module draws no randomness at all (it is a pure re-aggregation layer).
"""
from __future__ import annotations

import numpy as np
import pytest

from itsf.contracts import aaron_ruled_methods
from itsf.s0 import stability


def _meta(entries: dict[str, tuple[str, str, int]]) -> dict[str, dict[str, object]]:
    """date -> (year, era, d_open) tuples -> the day_meta shape stability.py
    wants."""
    return {d: {"year": y, "era": e, "d_open": o}
            for d, (y, e, o) in entries.items()}


def _block(pnl: dict[str, float], engine: str = "E1",
          scenario: str = "Base") -> dict[str, object]:
    """Minimal per_theta_block fixture: only 'executable' (key enumeration)
    and 'd_tp' (the actual series) matter to stability.py."""
    return {
        "executable": {engine: {scenario: {}}},
        "d_tp": {engine: {scenario: dict(pnl)}},
    }


ERA = "actual_micro_available_era"


def _one_engine_scenario(pnl, day_meta, vol_axis=None, engine="E1",
                         scenario="Base"):
    out = stability.build_stability_views(_block(pnl, engine, scenario),
                                          day_meta, vol_axis)
    return out[engine][scenario]


# ---------------------------------------------------------------------------
# epochs: inclusive boundaries
# ---------------------------------------------------------------------------

def test_epoch_boundaries_inclusive():
    # frozen: S0 §2 时代切片 2010-2013 / 2014-2017 / 2018-2021
    dates_years = {
        "2009-06-01": "2009", "2010-06-01": "2010", "2013-06-01": "2013",
        "2014-06-01": "2014", "2017-06-01": "2017", "2018-06-01": "2018",
        "2021-06-01": "2021", "2022-06-01": "2022",
    }
    pnl = {d: 1.0 for d in dates_years}
    meta = _meta({d: (y, ERA, 1) for d, y in dates_years.items()})
    epochs = _one_engine_scenario(pnl, meta)["epochs"]

    # per-date epoch assertions via a fresh single-day series each — the
    # least ambiguous way to pin each boundary independently.
    for date, year, expected_label in [
        ("2009-06-01", "2009", stability.OUTSIDE_EPOCHS),
        ("2010-06-01", "2010", "2010-2013"),
        ("2013-06-01", "2013", "2010-2013"),
        ("2014-06-01", "2014", "2014-2017"),
        ("2017-06-01", "2017", "2014-2017"),
        ("2018-06-01", "2018", "2018-2021"),
        ("2021-06-01", "2021", "2018-2021"),
        ("2022-06-01", "2022", stability.OUTSIDE_EPOCHS),
    ]:
        single_pnl = {date: 5.0}
        single_meta = _meta({date: (year, ERA, 1)})
        single_view = _one_engine_scenario(single_pnl, single_meta)
        for label, cell in single_view["epochs"].items():
            if label == "conservation_ok":
                continue
            if label == expected_label:
                assert cell["n"] == 1, (date, label)
            else:
                assert cell["n"] == 0, (date, label)
    assert epochs["conservation_ok"] is True


def test_epoch_conservation_ok_and_disjoint_counts():
    dates_years = {f"2010-01-{i:02d}": "2010" for i in range(1, 4)}
    dates_years.update({f"2015-01-{i:02d}": "2015" for i in range(1, 3)})
    dates_years["2009-01-01"] = "2009"
    pnl = {d: float(i) for i, d in enumerate(dates_years)}
    meta = _meta({d: (y, ERA, 1) for d, y in dates_years.items()})
    view = _one_engine_scenario(pnl, meta)
    epochs = view["epochs"]
    assert epochs["conservation_ok"] is True
    total = sum(c["n"] for label, c in epochs.items() if label != "conservation_ok")
    assert total == len(pnl)
    assert epochs["2010-2013"]["n"] == 3
    assert epochs["2014-2017"]["n"] == 2
    assert epochs[stability.OUTSIDE_EPOCHS]["n"] == 1


# ---------------------------------------------------------------------------
# by_year (mandatory) and leave-one-year-out
# ---------------------------------------------------------------------------

def test_by_year_every_year_present_mandatory():
    dates_years = {f"2011-0{m}-01": "2011" for m in range(1, 4)}
    dates_years.update({f"2016-0{m}-01": "2016" for m in range(1, 3)})
    pnl = {d: 10.0 for d in dates_years}
    meta = _meta({d: (y, ERA, 1) for d, y in dates_years.items()})
    view = _one_engine_scenario(pnl, meta)
    by_year = view["by_year"]
    assert set(by_year) == {"2011", "2016", "conservation_ok"}
    assert by_year["2011"]["n"] == 3
    assert by_year["2016"]["n"] == 2
    assert by_year["conservation_ok"] is True


def test_loyo_n_arithmetic_matches_total_minus_by_year():
    # frozen: S0 §2 leave-one-year-out — loyo[y].n == total - by_year[y].n
    dates_years = {f"2012-0{m}-01": "2012" for m in range(1, 5)}
    dates_years.update({f"2013-0{m}-01": "2013" for m in range(1, 3)})
    dates_years.update({f"2019-0{m}-01": "2019" for m in range(1, 4)})
    pnl = {d: float(i + 1) for i, d in enumerate(dates_years)}
    meta = _meta({d: (y, ERA, 1) for d, y in dates_years.items()})
    view = _one_engine_scenario(pnl, meta)
    by_year, loyo = view["by_year"], view["leave_one_year_out"]
    total = len(pnl)
    for year in ("2012", "2013", "2019"):
        assert loyo[year]["n"] == total - by_year[year]["n"]
    assert loyo["conservation_ok"] is True


def test_loyo_reflects_only_pnl_and_year_no_theta_or_label_inputs():
    """Structural guard: the LOYO builder receives ONLY pnl + meta (frozen
    §2 — no refitting of any threshold). Two series with identical
    dates/years but different pnl VALUES must give identical loyo `n`s (the
    arithmetic depends only on membership, never on the values)."""
    dates_years = {f"2012-0{m}-01": "2012" for m in range(1, 3)}
    dates_years["2013-01-01"] = "2013"
    meta = _meta({d: (y, ERA, 1) for d, y in dates_years.items()})
    pnl_a = {d: 1.0 for d in dates_years}
    pnl_b = {d: -999.0 for d in dates_years}
    loyo_a = _one_engine_scenario(pnl_a, meta)["leave_one_year_out"]
    loyo_b = _one_engine_scenario(pnl_b, meta)["leave_one_year_out"]
    assert {y: c["n"] for y, c in loyo_a.items() if y != "conservation_ok"} == {
        y: c["n"] for y, c in loyo_b.items() if y != "conservation_ok"}


# ---------------------------------------------------------------------------
# by_direction
# ---------------------------------------------------------------------------

def test_direction_split_conservation():
    # frozen: S0 §2 多空分开
    dates = [f"2015-01-{i:02d}" for i in range(1, 8)]
    directions = [1, -1, 1, 1, -1, -1, 1]
    pnl = {d: float(i) for i, d in enumerate(dates)}
    meta = _meta({d: ("2015", ERA, o) for d, o in zip(dates, directions)})
    view = _one_engine_scenario(pnl, meta)
    by_dir = view["by_direction"]
    assert by_dir["+1"]["n"] == directions.count(1)
    assert by_dir["-1"]["n"] == directions.count(-1)
    assert by_dir["conservation_ok"] is True
    assert by_dir["+1"]["n"] + by_dir["-1"]["n"] == len(pnl)


# ---------------------------------------------------------------------------
# vol_terciles
# ---------------------------------------------------------------------------

def test_vol_unresolved_marker_when_axis_none():
    pnl = {"2015-01-01": 1.0}
    meta = _meta({"2015-01-01": ("2015", ERA, 1)})
    view = _one_engine_scenario(pnl, meta, vol_axis=None)
    assert view["vol_terciles"] == {
        "status": "unresolved", "reason": "DR-M6-B-v2 pending"}


def test_vol_na_bucket_for_dates_missing_from_axis():
    dates = [f"2015-01-{i:02d}" for i in range(1, 5)]
    pnl = {d: 1.0 for d in dates}
    meta = _meta({d: ("2015", ERA, 1) for d in dates})
    vol_axis = {dates[0]: "low", dates[1]: "high"}   # dates[2], dates[3] absent
    view = _one_engine_scenario(pnl, meta, vol_axis=vol_axis)
    vol = view["vol_terciles"]
    assert vol["low"]["n"] == 1
    assert vol["high"]["n"] == 1
    assert vol[stability.VOL_NA_BUCKET]["n"] == 2
    assert vol["conservation_ok"] is True


def test_vol_resolved_conservation_ok_with_full_axis():
    dates = [f"2015-01-{i:02d}" for i in range(1, 7)]
    pnl = {d: float(i) for i, d in enumerate(dates)}
    meta = _meta({d: ("2015", ERA, 1) for d in dates})
    vol_axis = {d: ("low" if i % 2 == 0 else "high") for i, d in enumerate(dates)}
    view = _one_engine_scenario(pnl, meta, vol_axis=vol_axis)
    vol = view["vol_terciles"]
    assert vol["low"]["n"] == 3 and vol["high"]["n"] == 3
    # M6.1.2: the NA bucket is part of the STABLE stratum shape — present
    # but EMPTY when every date carries a label (the payload key set must
    # not change with the data).
    assert vol[stability.VOL_NA_BUCKET]["n"] == 0
    assert vol["conservation_ok"] is True


def test_explicit_ruled_vol_na_label_is_accepted_and_merges_with_absent_days():
    """DR-2 (2026-08-10) makes `vol_na` a RULED first-class fourth stratum.

    The pre-ruling collision guard (which REFUSED an explicit `vol_na`
    because the label was reserved for "date absent from vol_axis") is gone
    on purpose: the ruled fourth stratum and the §2 NA bucket are the SAME
    set, so an explicit label and an absent date land in the same bucket.
    """
    dates = ["2015-01-01", "2015-01-02", "2015-01-03"]
    pnl = {d: 1.0 for d in dates}
    meta = _meta({d: ("2015", ERA, 1) for d in dates})
    vol_axis = {dates[0]: stability.VOL_NA_BUCKET, dates[1]: "T1"}
    view = _one_engine_scenario(pnl, meta, vol_axis=vol_axis)
    vol = view["vol_terciles"]
    assert vol[stability.VOL_NA_BUCKET]["n"] == 2      # explicit + absent
    assert vol["T1"]["n"] == 1
    assert vol["conservation_ok"] is True


def test_vol_terciles_key_set_is_not_widened_by_the_dr2_change():
    """report.py counts `set(vol) - {"vol_na","conservation_ok"}` and demands
    exactly 3. Any bookkeeping key added inside this axis would break the
    sealed-payload validator, so the absent-date disclosure lives on the
    population block instead."""
    dates = [f"2015-01-{i:02d}" for i in range(1, 7)]
    pnl = {d: float(i) for i, d in enumerate(dates)}
    meta = _meta({d: ("2015", ERA, 1) for d in dates})
    vol_axis = {d: ("T1", "T2", "T3")[i % 3] for i, d in enumerate(dates)}
    vol = _one_engine_scenario(pnl, meta, vol_axis=vol_axis)["vol_terciles"]
    assert set(vol) == {"T1", "T2", "T3", stability.VOL_NA_BUCKET,
                        "conservation_ok"}


# ---------------------------------------------------------------------------
# the one shared cell shape
# ---------------------------------------------------------------------------

def test_cell_shape_identical_across_every_axis_and_bucket():
    dates = [f"2015-01-{i:02d}" for i in range(1, 9)]
    pnl = {d: (float(i) - 4.0) for i, d in enumerate(dates)}
    meta = _meta({d: ("2015", ERA, 1 if i % 2 == 0 else -1)
                 for i, d in enumerate(dates)})
    vol_axis = {d: "low" for d in dates}
    view = _one_engine_scenario(pnl, meta, vol_axis=vol_axis)
    for axis_name in ("epochs", "by_year", "leave_one_year_out",
                      "by_direction", "vol_terciles"):
        axis = view[axis_name]
        for key, cell in axis.items():
            if key == "conservation_ok":
                continue
            assert set(cell) == stability.CELL_KEYS, (axis_name, key)


def test_hand_computed_p1_p5_on_a_tiny_series():
    """values 0..100 (101 points): numpy linear percentile virtual index is
    (n-1)*p, so P1 -> index 1.0 -> value 1.0 and P5 -> index 5.0 -> value 5.0
    EXACTLY — the same estimator convention as s0/study.py's worst-day report.
    """
    pairs = [(f"d{i}", float(i)) for i in range(101)]
    cell = stability._cell(pairs)
    assert cell["worst_day_pnl_percentiles"]["P1"] == pytest.approx(1.0)
    assert cell["worst_day_pnl_percentiles"]["P5"] == pytest.approx(5.0)
    assert cell["n"] == 101
    assert cell["best_day"] == 100.0
    assert cell["worst_day"] == 0.0


def test_best_worst_and_n_pos_neg_zero_counts():
    pairs = [("d1", 5.0), ("d2", -3.0), ("d3", 0.0), ("d4", 10.0), ("d5", -1.0)]
    cell = stability._cell(pairs)
    assert cell["best_day"] == 10.0
    assert cell["worst_day"] == -3.0
    assert cell["n_positive"] == 2
    assert cell["n_negative"] == 2
    assert cell["n_zero"] == 1
    assert cell["sum_usd"] == pytest.approx(11.0)
    assert cell["mean_usd"] == pytest.approx(11.0 / 5)


def test_empty_cell_reports_the_full_shape_with_nones():
    cell = stability._cell([])
    assert cell["n"] == 0
    assert cell["mean_usd"] is None
    assert cell["best_day"] is None and cell["worst_day"] is None
    assert cell["n_positive"] == cell["n_negative"] == cell["n_zero"] == 0
    assert cell["worst_day_pnl_percentiles"] == {"P1": None, "P5": None}


# ---------------------------------------------------------------------------
# fail-closed input validation
# ---------------------------------------------------------------------------

def test_missing_day_meta_entry_fails_closed():
    pnl = {"2015-01-01": 1.0, "2015-01-02": 2.0}
    meta = _meta({"2015-01-01": ("2015", ERA, 1)})   # 01-02 missing
    with pytest.raises(stability.StabilityInputError):
        stability.build_stability_views(_block(pnl), meta)


def test_day_meta_missing_required_key_fails_closed():
    pnl = {"2015-01-01": 1.0}
    meta = {"2015-01-01": {"year": "2015", "d_open": 1}}   # era missing
    with pytest.raises(stability.StabilityInputError):
        stability.build_stability_views(_block(pnl), meta)


def test_invalid_d_open_fails_closed():
    pnl = {"2015-01-01": 1.0}
    meta = _meta({"2015-01-01": ("2015", ERA, 0)})   # 0 is not tradeable
    with pytest.raises(stability.StabilityInputError):
        stability.build_stability_views(_block(pnl), meta)


def test_malformed_per_theta_block_fails_closed():
    meta = _meta({"2015-01-01": ("2015", ERA, 1)})
    with pytest.raises(stability.StabilityInputError):
        stability.build_stability_views({"executable": {}}, meta)
    with pytest.raises(stability.StabilityInputError):
        stability.build_stability_views({"d_tp": {}}, meta)


# ---------------------------------------------------------------------------
# DR-7 — BOTH populations (Aaron 2026-08-10)
# ---------------------------------------------------------------------------

RULED_POP = aaron_ruled_methods().stability_population


def _dr7_fixture():
    """4 structurally eligible days; 2 of them are the D_TP (oracle) days.

    conditional  : {d1: +10, d3: -4}          -> n = 2, sum = +6
    full_eligible: {d1:+10, d2:0, d3:-4, d4:0} -> n = 4, sum = +6
    d2 is a no-direction day (d_open == 0): legal ONLY in the full-eligible
    population, and it must get its own bucket rather than a side.
    """
    d1, d2, d3, d4 = ("2015-03-02", "2015-03-03", "2016-03-04", "2016-03-05")
    pnl = {d1: 10.0, d3: -4.0}
    meta = _meta({d1: ("2015", ERA, 1), d2: ("2015", ERA, 0),
                  d3: ("2016", ERA, -1), d4: ("2016", ERA, 1)})
    vol_axis = {d1: "T1", d2: "T2", d3: "T3", d4: stability.VOL_NA_BUCKET}
    return pnl, meta, vol_axis, (d1, d2, d3, d4)


def test_ruled_population_string_is_read_from_the_single_ruled_source():
    assert stability.RULED_STABILITY_POPULATION == RULED_POP


def test_unruled_population_string_raises():
    pnl, meta, vol_axis, _d = _dr7_fixture()
    for bad in ("conditional_only", "both", "", "FULL_ELIGIBLE"):
        with pytest.raises(ValueError) as exc:
            stability.build_stability_views(_block(pnl), meta, vol_axis,
                                            stability_population=bad)
        assert f"stability_population_not_ruled:{bad}" in str(exc.value)


def test_none_population_keeps_the_pre_ruling_shape_byte_for_byte():
    pnl, meta, vol_axis, _d = _dr7_fixture()
    legacy = _one_engine_scenario(pnl, meta, vol_axis=vol_axis)
    assert "populations" not in legacy
    ruled = stability.build_stability_views(
        _block(pnl), meta, vol_axis,
        stability_population=RULED_POP)["E1"]["Base"]
    # the five legacy axes are IDENTICAL under the ruled call — the ruling
    # ADDS a population block, it never silently redefines the old one.
    for axis in ("epochs", "by_year", "leave_one_year_out", "by_direction",
                 "vol_terciles"):
        assert ruled[axis] == legacy[axis], axis


def test_both_populations_present_with_correct_per_population_values():
    pnl, meta, vol_axis, days = _dr7_fixture()
    d1, d2, d3, d4 = days
    cell = stability.build_stability_views(
        _block(pnl), meta, vol_axis,
        stability_population=RULED_POP)["E1"]["Base"]
    pops = cell["populations"]
    assert pops["rule"] == RULED_POP
    assert set(pops) == {"rule", "conditional", "full_eligible"}

    cond, full = pops["conditional"], pops["full_eligible"]
    assert cond["population"] == "conditional" and cond["n_days"] == 2
    assert full["population"] == "full_eligible" and full["n_days"] == 4
    assert full["n_zero_filled_non_oracle_days"] == 2

    # P&L-type view: the two non-oracle days contribute 0, so the SUM is the
    # same while the COUNT is not — the exact DR-7 semantics.
    assert cond["epochs"]["2014-2017"]["sum_usd"] == pytest.approx(6.0)
    assert full["epochs"]["2014-2017"]["sum_usd"] == pytest.approx(6.0)
    assert cond["epochs"]["2014-2017"]["n"] == 2
    assert full["epochs"]["2014-2017"]["n"] == 4
    assert full["epochs"]["2014-2017"]["n_zero"] == 2

    # count-type view: every structurally eligible year appears
    assert set(cond["by_year"]) == {"2015", "2016", "conservation_ok"}
    assert full["by_year"]["2015"]["n"] == 2 and full["by_year"]["2016"]["n"] == 2

    # direction: the no-direction day gets its OWN bucket, only in the
    # full-eligible population (多空分开 stays literally two-sided).
    assert set(cond["by_direction"]) == {"+1", "-1", "conservation_ok"}
    assert set(full["by_direction"]) == {"+1", "-1",
                                         stability.DIRECTION_NONE_KEY,
                                         "conservation_ok"}
    assert full["by_direction"][stability.DIRECTION_NONE_KEY]["n"] == 1
    assert full["by_direction"]["+1"]["n"] == 2       # d1 (+10) and d4 (0)

    # vol axis, both populations, conservation on each
    assert full["vol_terciles"]["T2"]["n"] == 1       # d2, a non-oracle day
    assert cond["vol_terciles"]["T2"]["n"] == 0
    for block in (cond, full):
        for axis in ("epochs", "by_year", "leave_one_year_out",
                     "by_direction", "vol_terciles"):
            assert block[axis]["conservation_ok"] is True, axis
    del d1, d2, d3, d4


def test_loyo_is_a_pure_reaggregation_in_both_populations():
    pnl, meta, vol_axis, _d = _dr7_fixture()
    pops = stability.build_stability_views(
        _block(pnl), meta, vol_axis,
        stability_population=RULED_POP)["E1"]["Base"]["populations"]
    for key in ("conditional", "full_eligible"):
        block = pops[key]
        n = block["n_days"]
        for year, cell in block["by_year"].items():
            if year == "conservation_ok":
                continue
            assert block["leave_one_year_out"][year]["n"] == n - cell["n"]


def test_single_population_output_for_a_ruled_both_is_refused():
    """The mutation test: drop one population from a ruled cell and the
    DR-7 checker must go red. A renderer that accepted it would show one
    population while claiming the ruled two."""
    pnl, meta, vol_axis, _d = _dr7_fixture()
    cell = stability.build_stability_views(
        _block(pnl), meta, vol_axis,
        stability_population=RULED_POP)["E1"]["Base"]
    assert stability.check_populations(cell, RULED_POP) == []

    dropped = {k: (dict(v) if k == "populations" else v)
               for k, v in cell.items()}
    dropped["populations"].pop("full_eligible")
    assert "stability_population_missing:full_eligible" in \
        stability.check_populations(dropped, RULED_POP)

    no_pops = {k: v for k, v in cell.items() if k != "populations"}
    assert "stability_populations_missing" in \
        stability.check_populations(no_pops, RULED_POP)

    mislabelled = {k: (dict(v) if k == "populations" else v)
                   for k, v in cell.items()}
    mislabelled["populations"] = dict(mislabelled["populations"])
    mislabelled["populations"]["conditional"] = dict(
        mislabelled["populations"]["conditional"], population="full_eligible")
    assert "stability_population_mislabelled:conditional" in \
        stability.check_populations(mislabelled, RULED_POP)


def test_no_direction_day_still_fails_closed_in_the_conditional_population():
    """d_open == 0 is legal ONLY in the full-eligible population. An Oracle
    (D_TP) day with no direction is still a defect."""
    pnl = {"2015-01-01": 1.0}
    meta = _meta({"2015-01-01": ("2015", ERA, 0)})
    with pytest.raises(stability.StabilityInputError):
        stability.build_stability_views(_block(pnl), meta,
                                        stability_population=RULED_POP)


def test_engine_scenario_iteration_matches_executable_keys():
    block = {
        "executable": {"E1": {"Base": {}, "Stress": {}}, "E2": {"Base": {}}},
        "d_tp": {
            "E1": {"Base": {"2015-01-01": 1.0}, "Stress": {"2015-01-01": 2.0}},
            "E2": {"Base": {"2015-01-01": 3.0}},
        },
    }
    meta = _meta({"2015-01-01": ("2015", ERA, 1)})
    out = stability.build_stability_views(block, meta)
    assert set(out) == {"E1", "E2"}
    assert set(out["E1"]) == {"Base", "Stress"}
    assert set(out["E2"]) == {"Base"}
