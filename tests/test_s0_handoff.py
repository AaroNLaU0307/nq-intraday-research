"""Synthetic checks for itsf.s0.handoff (E6 S0 -> MC handoff schema skeleton).

SA-18-style scope. Every population here is a hand-written dict of fabricated
dates/values: no real archive is touched, no clock is read. The replay
determinism test draws randomness only through `itsf.s0.gridmix`, whose
streams derive exclusively from contracts.RESEARCH_BOOTSTRAP_SEEDS.
"""
from __future__ import annotations

import json

import numpy as np
import pytest

from itsf import contracts
from itsf.s0 import gridmix, handoff, stability

ERA_ACTUAL = "actual_micro_available_era"
ERA_PROXY = "counterfactual_micro_execution"
EPOCH = "2018-2021"


def _day_row(**overrides) -> dict[str, object]:
    row = {
        "micro_execution_era": ERA_ACTUAL,
        "stability_epoch": EPOCH,
        "year": "2019",
        "d_open": 1,
        "event_flag_final": "none",
        "vol_status": "resolved",
        "tp_fp_class": {"theta_0.5": "TP"},
    }
    row.update(overrides)
    return row


# ---------------------------------------------------------------------------
# schema version / sentinel
# ---------------------------------------------------------------------------

def test_schema_version_constant():
    assert handoff.SCHEMA_VERSION == "m6.1-draft-1"


def test_unresolved_sentinel_identity_and_string_equality():
    assert handoff.UNRESOLVED == "UNRESOLVED"
    assert handoff.UNRESOLVED is handoff.UNRESOLVED
    # a second construction is the SAME singleton object
    from itsf.s0.handoff import _UnresolvedSentinel
    assert _UnresolvedSentinel() is handoff.UNRESOLVED


# ---------------------------------------------------------------------------
# build_day_strata
# ---------------------------------------------------------------------------

def test_build_day_strata_canonical_sorted_ordering():
    day_rows = {
        "2019-06-03": _day_row(),
        "2019-01-02": _day_row(),
        "2019-03-15": _day_row(),
    }
    out = handoff.build_day_strata(day_rows, thetas=[0.5])
    assert out["schema_version"] == handoff.SCHEMA_VERSION
    assert out["ordering"] == "sorted-by-date"
    assert list(out["days"]) == sorted(day_rows)


def test_micro_era_and_stability_epoch_conflation_rejected():
    day_rows = {"2019-06-03": _day_row(stability_epoch=ERA_ACTUAL)}
    with pytest.raises(ValueError):
        handoff.build_day_strata(day_rows, thetas=[0.5])
    day_rows2 = {"2019-06-03": _day_row(micro_execution_era=EPOCH)}
    with pytest.raises(ValueError):
        handoff.build_day_strata(day_rows2, thetas=[0.5])


def test_micro_era_and_stability_epoch_distinct_values_pass():
    day_rows = {"2019-06-03": _day_row()}
    out = handoff.build_day_strata(day_rows, thetas=[0.5])
    row = out["days"]["2019-06-03"]
    assert row["micro_execution_era"] == ERA_ACTUAL
    assert row["stability_epoch"] == EPOCH
    assert row["micro_execution_era"] != row["stability_epoch"]


def test_tp_fp_class_must_match_requested_thetas_exactly():
    day_rows = {"2019-06-03": _day_row(
        tp_fp_class={"theta_0.5": "TP", "theta_0.3": "FP"})}
    with pytest.raises(ValueError):
        handoff.build_day_strata(day_rows, thetas=[0.5])   # extra key 0.3
    out = handoff.build_day_strata(day_rows, thetas=[0.5, 0.3])
    assert out["days"]["2019-06-03"]["tp_fp_class"] == {
        "theta_0.5": "TP", "theta_0.3": "FP"}


def test_tp_fp_class_bad_value_rejected():
    day_rows = {"2019-06-03": _day_row(
        tp_fp_class={"theta_0.5": "maybe"})}
    with pytest.raises(ValueError):
        handoff.build_day_strata(day_rows, thetas=[0.5])


def test_event_na_flag_and_event_flag_final_preserved():
    day_rows = {
        "2019-06-03": _day_row(event_flag_final=None),
        "2019-06-04": _day_row(event_flag_final="CPI"),
    }
    out = handoff.build_day_strata(day_rows, thetas=[0.5])
    na_row = out["days"]["2019-06-03"]
    assert na_row["event_flag_final"] is None
    assert na_row["event_na"] is True
    concrete_row = out["days"]["2019-06-04"]
    assert concrete_row["event_flag_final"] == "CPI"
    assert concrete_row["event_na"] is False


def test_event_stratum_is_always_the_unresolved_marker():
    day_rows = {
        "2019-06-03": _day_row(event_flag_final=None),
        "2019-06-04": _day_row(event_flag_final="FOMC"),
    }
    out = handoff.build_day_strata(day_rows, thetas=[0.5])
    for row in out["days"].values():
        assert row["event_stratum"] == "UNRESOLVED_DR-M6-F"


def test_caller_supplied_event_stratum_is_rejected():
    day_rows = {"2019-06-03": _day_row()}
    day_rows["2019-06-03"]["event_stratum"] = "some_concrete_bucket"
    with pytest.raises(ValueError):
        handoff.build_day_strata(day_rows, thetas=[0.5])


def test_missing_required_key_in_day_row_raises():
    row = _day_row()
    del row["vol_status"]
    with pytest.raises(ValueError):
        handoff.build_day_strata({"2019-06-03": row}, thetas=[0.5])


def test_invalid_d_open_in_day_row_raises():
    day_rows = {"2019-06-03": _day_row(d_open=2)}
    with pytest.raises(ValueError):
        handoff.build_day_strata(day_rows, thetas=[0.5])


def test_duplicate_or_empty_thetas_rejected():
    day_rows = {"2019-06-03": _day_row()}
    with pytest.raises(ValueError):
        handoff.build_day_strata(day_rows, thetas=[])
    with pytest.raises(ValueError):
        handoff.build_day_strata(day_rows, thetas=[0.5, 0.5])


# ---------------------------------------------------------------------------
# build_seed_manifest
# ---------------------------------------------------------------------------

def test_build_seed_manifest_shape_and_identity():
    manifest = handoff.build_seed_manifest()
    assert manifest["schema_version"] == handoff.SCHEMA_VERSION
    assert manifest["research_bootstrap_seeds"] == [7, 13, 31]
    assert manifest["stream_tags"] == {
        "stats_stream_tag": 9001, "grid_stream_tag": 9002}
    assert manifest["k_policy"] == "UNRESOLVED_DR-M6-E"
    assert manifest["crn_scope"] == "UNRESOLVED"
    assert "run-infra provenance only" in manifest["engineering_seed_note"]
    assert "FIRST frozen master seed" in manifest["quoted_seed_convention"]


# ---------------------------------------------------------------------------
# build_grid_samples + replay determinism
# ---------------------------------------------------------------------------

def _fabricated_grid_populations():
    low, high = ("2010", "low", "none"), ("2010", "high", "CPI")
    d_tp: dict[str, float] = {}
    d_fp: dict[str, float] = {}
    strata: dict[str, tuple[str, str, str]] = {}
    for i in range(10):
        date = f"2010-03-{i + 1:02d}"
        d_tp[date] = 100.0 + i
        strata[date] = low if i < 6 else high
    for i in range(20):
        date = f"2010-04-{i + 1:02d}"
        d_fp[date] = -50.0 - i
        strata[date] = low if i < 12 else high
    return d_tp, d_fp, strata


def test_build_grid_samples_shape_and_infeasible_passthrough():
    d_tp, d_fp, strata = _fabricated_grid_populations()
    grid_output = gridmix.build_grid(d_tp, d_fp, strata, base_rate_p=0.4,
                                     q_grid=[0.50], r_grid=[0.50])
    samples = handoff.build_grid_samples(grid_output,
                                         run_meta={"theta": 0.5, "engine": "E1"})
    assert samples["schema_version"] == handoff.SCHEMA_VERSION
    assert samples["run_meta"] == {"theta": 0.5, "engine": "E1"}
    cell = samples["cells"]["q0.50_r0.50"]
    assert cell["infeasible_by_sample"] is False
    assert cell["q_mil"] == 500 and cell["r_mil"] == 500
    for seed in (7, 13, 31):
        block = cell["per_seed"][seed]
        assert set(block) == {"tp_dates", "fp_dates", "markers",
                              "realized_precision", "realized_recall",
                              "target_precision", "target_recall"}
    assert samples["replay"]["grid_stream_tag"] == gridmix.GRID_STREAM_TAG
    assert samples["replay"]["k_policy"] == "UNRESOLVED_DR-M6-E"
    assert samples["replay"]["crn_scope"] == "UNRESOLVED"


def test_build_grid_samples_reports_infeasible_cells():
    d_tp, _d_fp, strata = _fabricated_grid_populations()
    small_fp = {"2010-04-01": -10.0, "2010-04-02": -20.0}
    grid_output = gridmix.build_grid(d_tp, small_fp, strata, base_rate_p=0.4,
                                     q_grid=[0.35], r_grid=[0.80])
    samples = handoff.build_grid_samples(grid_output, run_meta={})
    cell = samples["cells"]["q0.35_r0.80"]
    assert cell["infeasible_by_sample"] is True
    assert cell["per_seed"] == {}


def test_grid_replay_reproduces_the_selection():
    """Independent recomputation using ONLY public gridmix functions
    (floor_n_tp, allocate) plus the DISCLOSED replay recipe: the same
    stratified-pools-then-rng.choice algorithm the gridmix module docstring
    describes, rebuilt here from scratch rather than by reaching into
    gridmix's private `_select`/`_pools` helpers."""
    d_tp, d_fp, strata = _fabricated_grid_populations()
    grid_output = gridmix.build_grid(d_tp, d_fp, strata, base_rate_p=0.4,
                                     q_grid=[0.50], r_grid=[0.50])
    samples = handoff.build_grid_samples(grid_output, run_meta={})
    cell = samples["cells"]["q0.50_r0.50"]
    seed = 7
    expected_tp = cell["per_seed"][seed]["tp_dates"]

    tag = samples["replay"]["grid_stream_tag"]
    q_mil, r_mil = cell["q_mil"], cell["r_mil"]
    assert tag == gridmix.GRID_STREAM_TAG

    tp_pools_raw: dict[str, list[str]] = {}
    for date in d_tp:
        tp_pools_raw.setdefault("|".join(strata[date]), []).append(date)
    tp_pools = {k: tuple(sorted(v)) for k, v in sorted(tp_pools_raw.items())}
    tp_avail = {k: len(v) for k, v in tp_pools.items()}
    n_tp = gridmix.floor_n_tp(r_mil, len(d_tp))
    tp_alloc = gridmix.allocate(n_tp, tp_avail)

    rng = np.random.default_rng([seed, tag, q_mil, r_mil])
    picked: list[str] = []
    for key in sorted(tp_alloc):
        k = tp_alloc[key]
        if k <= 0:
            continue
        pool = tp_pools[key]
        idx = rng.choice(len(pool), size=k, replace=False)
        picked.extend(pool[int(i)] for i in idx)
    assert sorted(picked) == expected_tp


# ---------------------------------------------------------------------------
# build_handoff_manifest
# ---------------------------------------------------------------------------

def test_build_handoff_manifest_sha256_bytes_line_count(tmp_path):
    jsonl_path = tmp_path / "records.jsonl"
    content = b'{"a": 1}\n{"b": 2}\n{"c": 3}\n'
    jsonl_path.write_bytes(content)
    plain_path = tmp_path / "notes.txt"
    plain_path.write_bytes(b"hello world")

    manifest = handoff.build_handoff_manifest({
        "records": str(jsonl_path), "notes": str(plain_path)})
    assert manifest["schema_version"] == handoff.SCHEMA_VERSION

    import hashlib
    expected_jsonl_sha = hashlib.sha256(content).hexdigest()
    entry = manifest["files"]["records"]
    assert entry["sha256"] == expected_jsonl_sha
    assert entry["bytes"] == len(content)
    assert entry["line_count"] == 3

    plain_entry = manifest["files"]["notes"]
    assert plain_entry["sha256"] == hashlib.sha256(b"hello world").hexdigest()
    assert plain_entry["bytes"] == 11
    assert "line_count" not in plain_entry


# ---------------------------------------------------------------------------
# verify_handoff_conservation
# ---------------------------------------------------------------------------

def _day_strata_with(dates_classes: dict[str, str]) -> dict[str, object]:
    """dates_classes: date -> "TP"|"FP"|"non_tradeable" for theta_0.5."""
    day_rows = {d: _day_row(tp_fp_class={"theta_0.5": cls})
               for d, cls in dates_classes.items()}
    return handoff.build_day_strata(day_rows, thetas=[0.5])


def test_conservation_positive_case_no_problems():
    day_strata = _day_strata_with({
        "2019-06-01": "TP", "2019-06-02": "FP", "2019-06-03": "non_tradeable"})
    grid_samples = {"cells": {"q0.50_r0.50": {"per_seed": {
        7: {"tp_dates": ["2019-06-01"], "fp_dates": ["2019-06-02"]}}}}}
    records = {"E1": {"Base": ["2019-06-01", "2019-06-02"]}}
    problems = handoff.verify_handoff_conservation(day_strata, grid_samples,
                                                    records)
    assert problems == []


def test_conservation_grid_date_missing_from_day_strata():
    day_strata = _day_strata_with({"2019-06-01": "TP"})
    grid_samples = {"cells": {"q0.50_r0.50": {"per_seed": {
        7: {"tp_dates": ["2019-06-01", "2099-01-01"], "fp_dates": []}}}}}
    records = {"E1": {"Base": ["2019-06-01"]}}
    problems = handoff.verify_handoff_conservation(day_strata, grid_samples,
                                                    records)
    assert any("2099-01-01" in p and "grid sample" in p for p in problems)


def test_conservation_record_date_missing_from_day_strata():
    day_strata = _day_strata_with({"2019-06-01": "TP"})
    grid_samples = {"cells": {}}
    records = {"E1": {"Base": ["2019-06-01", "2099-02-02"]}}
    problems = handoff.verify_handoff_conservation(day_strata, grid_samples,
                                                    records)
    assert any("2099-02-02" in p and "absent from day_strata" in p
              for p in problems)


def test_conservation_classified_date_missing_a_record():
    day_strata = _day_strata_with({"2019-06-01": "TP", "2019-06-02": "FP"})
    grid_samples = {"cells": {}}
    # 2019-06-02 has no record for E1/Base at all
    records = {"E1": {"Base": ["2019-06-01"]}}
    problems = handoff.verify_handoff_conservation(day_strata, grid_samples,
                                                    records)
    assert any("2019-06-02" in p and "missing a record" in p for p in problems)


def test_conservation_record_without_classification():
    day_strata = _day_strata_with({
        "2019-06-01": "TP", "2019-06-02": "non_tradeable"})
    grid_samples = {"cells": {}}
    # 2019-06-02 has a record even though it is non_tradeable (not TP/FP)
    records = {"E1": {"Base": ["2019-06-01", "2019-06-02"]}}
    problems = handoff.verify_handoff_conservation(day_strata, grid_samples,
                                                    records)
    assert any("2019-06-02" in p and "not TP/FP-classed" in p
              for p in problems)


# ---------------------------------------------------------------------------
# dumps_canonical
# ---------------------------------------------------------------------------

def test_dumps_canonical_sorts_keys_and_is_stable():
    out1 = handoff.dumps_canonical({"b": 1, "a": 2})
    out2 = handoff.dumps_canonical({"a": 2, "b": 1})
    assert out1 == out2
    assert json.loads(out1) == {"a": 2, "b": 1}
    assert out1.index('"a"') < out1.index('"b"')


def test_dumps_canonical_rejects_nan():
    with pytest.raises(ValueError):
        handoff.dumps_canonical({"x": float("nan")})
    with pytest.raises(ValueError):
        handoff.dumps_canonical({"x": float("inf")})
