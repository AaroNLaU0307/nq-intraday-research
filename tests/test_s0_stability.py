"""Synthetic checks for itsf.s0.stability (frozen S0 §2 Development stability
views).

SA-18-style scope. Every series here is a hand-written dict of fabricated
dates/years/pnl: no real archive is touched, no clock is read, and this
module draws no randomness at all (it is a pure re-aggregation layer).
"""
from __future__ import annotations

import numpy as np
import pytest

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
    assert stability.VOL_NA_BUCKET not in vol
    assert vol["conservation_ok"] is True


def test_vol_label_collision_with_vol_na_is_rejected():
    pnl = {"2015-01-01": 1.0}
    meta = _meta({"2015-01-01": ("2015", ERA, 1)})
    vol_axis = {"2015-01-01": stability.VOL_NA_BUCKET}
    with pytest.raises(stability.StabilityInputError):
        stability.build_stability_views(_block(pnl), meta, vol_axis)


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
