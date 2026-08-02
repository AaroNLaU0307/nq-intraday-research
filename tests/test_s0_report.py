"""Tests for itsf.s0.report — the S0 formal-report boundary (M6.1 E2+E3).

Hermetic and synthetic throughout: every payload here is a small hand-built
dict of fabricated numbers (2 thetas x 2 engines x 4 scenarios x 2 blocks,
no research meaning whatsoever) — no real archive is touched, no clock is
read, and nothing here consumes researcher exposure.

`_valid_payload()` builds a payload that is sealable end-to-end: it passes
every S0_REPORT_CONTENT_CONTRACT.md §B rule (R1-R10, via
`validate_formal_payload`) AND serializes cleanly through `to_formal_json`.
That requires ONE deliberate normalisation, documented where it happens
below: `bootstrap_ci` per-seed dict keys are the JSON-safe strings "7" /
"13" / "31" (not the int keys `stats.bootstrap_mean_ci` natively returns),
because `to_formal_json` hard-rejects any non-str dict key. Every other
test starts from a deep-ish fresh copy of that fixture and breaks exactly
one thing.
"""
from __future__ import annotations

import hashlib
import json
import math

import pytest
from conftest import make_trade_path

from itsf.s0 import report
from itsf.s0.dataset import ERA_ACTUAL, ERA_PROXY
from itsf.s0.study import ENGINES

SCENARIOS = ("Base", "Conservative", "Stress", "Severe")
BLOCKS = (5, 21)
ERAS = (ERA_PROXY, ERA_ACTUAL)
EPOCHS = ("2010-2013", "2014-2017", "2018-2021")
DIRECTIONS = ("+1", "-1")
THETAS = ("theta_0.3", "theta_0.5")


# ---------------------------------------------------------------------------
# fixture builders — every call returns FRESH nested objects (comprehensions
# only), so mutating one test's payload can never bleed into another's.
# ---------------------------------------------------------------------------
def _bootstrap_cell(block_len: int) -> dict:
    return {
        "per_seed": {
            "7": {"mean": 1.0, "ci_lo": 0.10, "ci_hi": 2.00,
                 "n_boot": report.FROZEN_N_BOOT, "block_len": block_len},
            "13": {"mean": 1.0, "ci_lo": 0.05, "ci_hi": 2.10,
                  "n_boot": report.FROZEN_N_BOOT, "block_len": block_len},
            "31": {"mean": 1.0, "ci_lo": 0.08, "ci_hi": 1.90,
                  "n_boot": report.FROZEN_N_BOOT, "block_len": block_len},
        },
        "quoted_seed": 7,
        "convergence": {"max_abs_ci_lo_diff": 0.05,
                        "max_abs_ci_hi_diff": 0.20},
    }


def _worst_day_cell() -> dict:
    return {
        "pooled": {"P1": -50.0, "P5": -20.0},
        "by_era": {era: {"P1": -55.0, "P5": -22.0} for era in ERAS},
    }


def _stability_cell() -> dict:
    return {
        "epochs": {e: {"mean_daily_usd": 1.0} for e in EPOCHS},
        "by_year": {"2020": {"mean_daily_usd": 1.0}},
        "leave_one_year_out": {"2020": {"mean_daily_usd": 1.0}},
        "by_direction": {"+1": {"mean_daily_usd": 1.5},
                         "-1": {"mean_daily_usd": -0.5}},
        "vol_terciles": {"status": "resolved", "low": {}, "mid": {},
                         "high": {}, "vol_na": {}},
    }


def _valid_payload() -> dict:
    oracle_daily = {
        t: {"pooled": {"2020-01-02": 10.0, "2020-01-03": -2.0},
           "by_era": {era: {"2020-01-02": 10.0} for era in ERAS}}
        for t in THETAS
    }
    theoretical_oracle = {
        t: {"scenario": "Base", "pooled": {"2020-01-02": 12.0}}
        for t in THETAS
    }
    e2_worst_days = {
        t: {s: _worst_day_cell() for s in SCENARIOS} for t in THETAS
    }
    sizing_outputs = {
        t: {"rows": {e: {s: [] for s in SCENARIOS} for e in ENGINES},
           "coverage": {e: {s: {"50": 1.0, "75": 1.0, "100": 1.0,
                                "150": 1.0} for s in SCENARIOS}
                       for e in ENGINES}}
        for t in THETAS
    }
    frequency = {
        t: {"p": 0.4, "trading_days_per_year": 250,
           "monthly_frequency": 8.0}
        for t in THETAS
    }
    stability_views = {
        t: {e: {s: _stability_cell() for s in SCENARIOS} for e in ENGINES}
        for t in THETAS
    }
    bootstrap_ci = {
        f"{t}|{e}|{s}|block{b}": _bootstrap_cell(b)
        for t in THETAS for e in ENGINES for s in SCENARIOS for b in BLOCKS
    }
    feasibility_grid = {
        "cells": {f"{t}|{e}|{s}": {"realized_precision": 0.5,
                                   "realized_recall": 0.5}
                 for t in THETAS for e in ENGINES for s in SCENARIOS},
        "regions": {"status": "pending_mc"},
    }
    mc_handoff_manifest = {
        "counts": {e: {s: {"n_records": 10} for s in SCENARIOS}
                  for e in ENGINES},
        "files": {
            f"{e}|{s}": {"file": f"MC_HANDOFF_{e}_{s}.jsonl",
                        "n_records": 0, "sha256": "0" * 64}
            for e in ENGINES for s in SCENARIOS
        },
    }
    era_axis = {
        "axes": list(ERAS),
        "counterfactual_disclosure": (
            "counterfactual_micro_execution results are NQ price paths "
            "under MNQ multiplier + friction — not a tradeable MNQ "
            "history (frozen S0 §6)."),
    }
    disclosures = {
        "untradeable": {"note": "n/a for this fixture"},
        "pending_method_decisions": [],
        "method_conventions": {
            "quoted_seed_convention": "first frozen seed (7)"},
    }
    governance = {
        "trial_id": "S0-T001",
        "authorized_commit": "a" * 40,
        "engineering_seed": 20260731,
        "frozen_hashes": {f"FILE_{i}.md": "c" * 64 for i in range(7)},
        "registry_sequence_snapshot": 5,
    }
    structural = {"funnel_counts": {"L0_scheduled_trading_days": 10}}

    return {
        "structural": structural,
        "oracle_daily": oracle_daily,
        "theoretical_oracle": theoretical_oracle,
        "e2_worst_days": e2_worst_days,
        "sizing_outputs": sizing_outputs,
        "frequency": frequency,
        "stability_views": stability_views,
        "bootstrap_ci": bootstrap_ci,
        "feasibility_grid": feasibility_grid,
        "mc_handoff_manifest": mc_handoff_manifest,
        "era_axis": era_axis,
        "disclosures": disclosures,
        "governance": governance,
    }


def _sealed_fixture():
    """(files, payload) with a real MC_HANDOFF_*.jsonl body per engine x
    scenario, sha256/n_records matching, built from actual
    `record_to_formal_dict` output."""
    payload = _valid_payload()
    rec1 = report.record_to_formal_dict(
        make_trade_path([1.0, 2.0], date="2020-01-02"))
    rec2 = report.record_to_formal_dict(
        make_trade_path([1.0, 2.0], date="2020-01-03"))
    files: dict[str, str] = {}
    manifest_files: dict[str, object] = {}
    for eng in ENGINES:
        for scn in SCENARIOS:
            name = f"MC_HANDOFF_{eng}_{scn}.jsonl"
            body = "\n".join(json.dumps(r, sort_keys=True)
                             for r in (rec1, rec2))
            files[name] = body
            manifest_files[f"{eng}|{scn}"] = {
                "file": name, "n_records": 2,
                "sha256": hashlib.sha256(body.encode("utf-8")).hexdigest()}
    payload["mc_handoff_manifest"] = {
        "counts": payload["mc_handoff_manifest"]["counts"],
        "files": manifest_files,
    }
    return files, payload


# ===========================================================================
# record_to_formal_dict
# ===========================================================================
def test_record_to_formal_dict_renames_timestamps_and_pins_field_set():
    rec = make_trade_path([1.0, 2.0, 3.0], date="2020-01-02")
    d = report.record_to_formal_dict(rec)
    assert "entry_timestamp" in d and "exit_timestamp" in d
    assert "entry_ts" not in d and "exit_ts" not in d
    assert set(d) == set(report.FORMAL_RECORD_FIELDS)
    assert list(d) == sorted(d)                    # deterministic key order


def test_record_to_formal_dict_round_trips_through_to_formal_json():
    rec = make_trade_path([1.0, 2.0, 3.0], date="2020-01-02")
    d = report.record_to_formal_dict(rec)
    text = report.to_formal_json(d)
    assert json.loads(text) == d


def test_record_to_formal_dict_rejects_non_record_type():
    with pytest.raises(TypeError):
        report.record_to_formal_dict(["not", "a", "record"])


def test_record_to_formal_dict_rejects_field_set_mismatch():
    with pytest.raises(ValueError):
        report.record_to_formal_dict({"trade_date": "2020-01-02"})


# ===========================================================================
# to_formal_json — strict serializer
# ===========================================================================
def test_to_formal_json_accepts_plain_payload():
    text = report.to_formal_json({"a": 1, "b": [1, 2, 3], "c": None,
                                  "d": True, "e": 1.5})
    assert json.loads(text) == {"a": 1, "b": [1, 2, 3], "c": None,
                                "d": True, "e": 1.5}


def test_to_formal_json_converts_tuple_to_list():
    text = report.to_formal_json({"t": (1, 2, 3)})
    assert json.loads(text) == {"t": [1, 2, 3]}


def test_to_formal_json_rejects_nan():
    with pytest.raises((TypeError, ValueError)):
        report.to_formal_json({"x": [1.0, float("nan"), 2.0]})


def test_to_formal_json_rejects_inf():
    with pytest.raises((TypeError, ValueError)):
        report.to_formal_json({"x": float("inf")})


def test_to_formal_json_rejects_non_str_dict_key():
    with pytest.raises(TypeError):
        report.to_formal_json({1: "leak"})


def test_to_formal_json_rejects_unknown_object_type():
    class _Blob:
        pass

    with pytest.raises(TypeError):
        report.to_formal_json({"x": _Blob()})


def test_to_formal_json_never_falls_back_to_str():
    class _Blob:
        def __str__(self):
            return "safe string, never seen"

    with pytest.raises(TypeError):
        report.to_formal_json({"x": _Blob()})


# ===========================================================================
# split_envelope
# ===========================================================================
def test_split_envelope_separates_internal_and_formal_keys():
    payload = _valid_payload()
    compute_result = dict(payload)
    compute_result["dataset"] = object()
    compute_result["na_reason_counts"] = {"features.f1": {"warmup": 2}}
    compute_result["reported_total_na"] = {"features.f1": 2}
    compute_result["records"] = [object()]

    internal, formal = report.split_envelope(compute_result)

    assert set(internal) == {"dataset", "na_reason_counts",
                             "reported_total_na", "records"}
    assert set(formal) == set(report.FORMAL_SECTIONS)
    assert "dataset" not in formal
    assert report.validate_formal_payload(formal) == []


def test_split_envelope_missing_sections_stay_absent():
    payload = _valid_payload()
    del payload["governance"]
    _internal, formal = report.split_envelope(payload)
    assert "governance" not in formal
    assert set(formal) == set(report.FORMAL_SECTIONS) - {"governance"}


def test_split_envelope_refuses_a_formal_section_containing_an_object():
    payload = _valid_payload()
    payload["structural"]["leaked_record"] = make_trade_path(
        [1.0], date="2020-01-02")
    with pytest.raises(TypeError):
        report.split_envelope(payload)


def test_split_envelope_rejects_non_dict_input():
    with pytest.raises(TypeError):
        report.split_envelope(["not", "a", "dict"])


# ===========================================================================
# validate_formal_payload — the valid fixture
# ===========================================================================
def test_valid_payload_has_no_problems():
    assert report.validate_formal_payload(_valid_payload()) == []


def test_valid_payload_serializes_through_to_formal_json():
    payload = _valid_payload()
    text = report.to_formal_json(payload)
    assert json.loads(text) == payload


def test_validate_formal_payload_rejects_non_dict():
    assert report.validate_formal_payload(["not", "a", "dict"]) == \
        ["payload_not_dict"]


# --- R1: delete each FORMAL_SECTION (13 parametrized cases) -----------------
@pytest.mark.parametrize("section", report.FORMAL_SECTIONS)
def test_deleting_any_formal_section_is_flagged(section):
    payload = _valid_payload()
    del payload[section]
    problems = report.validate_formal_payload(payload)
    assert f"missing_section:{section}" in problems


@pytest.mark.parametrize("section", report.FORMAL_SECTIONS)
def test_emptying_any_formal_section_is_flagged(section):
    payload = _valid_payload()
    payload[section] = {}
    problems = report.validate_formal_payload(payload)
    assert f"empty_section:{section}" in problems


# --- R2/R3: bootstrap_ci grid + per-cell shape ------------------------------
def test_bootstrap_ci_missing_key_is_flagged():
    payload = _valid_payload()
    key = next(iter(payload["bootstrap_ci"]))
    del payload["bootstrap_ci"][key]
    problems = report.validate_formal_payload(payload)
    assert f"bootstrap_ci_missing:{key}" in problems


def test_bootstrap_ci_extra_key_is_flagged():
    payload = _valid_payload()
    tkey = next(iter(payload["oracle_daily"]))
    template = next(iter(payload["bootstrap_ci"].values()))
    extra_key = f"{tkey}|E1|Base|block999"
    payload["bootstrap_ci"][extra_key] = template
    problems = report.validate_formal_payload(payload)
    assert f"bootstrap_ci_extra:{extra_key}" in problems


def test_bootstrap_ci_wrong_seed_set_is_flagged():
    payload = _valid_payload()
    key = next(iter(payload["bootstrap_ci"]))
    per_seed = payload["bootstrap_ci"][key]["per_seed"]
    per_seed["99"] = per_seed.pop("13")
    problems = report.validate_formal_payload(payload)
    assert any(p.startswith(f"bootstrap_ci_seeds:{key}") for p in problems)


def test_bootstrap_ci_quoted_seed_not_seven_is_flagged():
    payload = _valid_payload()
    key = next(iter(payload["bootstrap_ci"]))
    payload["bootstrap_ci"][key]["quoted_seed"] = 13
    problems = report.validate_formal_payload(payload)
    assert f"bootstrap_ci_quoted_seed:{key}" in problems


def test_bootstrap_ci_wrong_n_boot_is_flagged():
    payload = _valid_payload()
    key = next(iter(payload["bootstrap_ci"]))
    payload["bootstrap_ci"][key]["per_seed"]["7"]["n_boot"] = 40
    problems = report.validate_formal_payload(payload)
    assert f"bootstrap_ci_n_boot:{key}:7" in problems


def test_bootstrap_ci_wrong_block_len_is_flagged():
    payload = _valid_payload()
    key = next(k for k in payload["bootstrap_ci"] if k.endswith("block5"))
    payload["bootstrap_ci"][key]["per_seed"]["7"]["block_len"] = 7
    problems = report.validate_formal_payload(payload)
    assert f"bootstrap_ci_block_len:{key}:7" in problems


def test_bootstrap_ci_non_finite_bound_is_flagged():
    payload = _valid_payload()
    key = next(iter(payload["bootstrap_ci"]))
    payload["bootstrap_ci"][key]["per_seed"]["7"]["ci_hi"] = float("inf")
    problems = report.validate_formal_payload(payload)
    assert any(p.startswith(f"bootstrap_ci_bounds:{key}:7")
              for p in problems)


# --- R6: disclosures ---------------------------------------------------------
def test_pending_method_decisions_nonempty_is_flagged():
    payload = _valid_payload()
    payload["disclosures"]["pending_method_decisions"] = ["DR-M6-A_v2"]
    problems = report.validate_formal_payload(payload)
    assert "pending_method_decisions_unresolved" in problems


# --- R5: stability_views vol axis -------------------------------------------
def test_vol_terciles_unresolved_is_flagged():
    payload = _valid_payload()
    tkey = next(iter(payload["oracle_daily"]))
    payload["stability_views"][tkey]["E1"]["Base"]["vol_terciles"][
        "status"] = "unresolved"
    problems = report.validate_formal_payload(payload)
    assert "vol_axis_unresolved" in problems


# --- R7: governance ----------------------------------------------------------
def test_governance_short_commit_is_flagged():
    payload = _valid_payload()
    payload["governance"]["authorized_commit"] = "abc123"
    problems = report.validate_formal_payload(payload)
    assert "governance_authorized_commit" in problems


def test_governance_six_hashes_is_flagged():
    payload = _valid_payload()
    hashes = payload["governance"]["frozen_hashes"]
    del hashes[next(iter(hashes))]
    problems = report.validate_formal_payload(payload)
    assert "governance_frozen_hashes_count" in problems


def test_governance_missing_engineering_seed_is_flagged():
    payload = _valid_payload()
    del payload["governance"]["engineering_seed"]
    problems = report.validate_formal_payload(payload)
    assert "governance_engineering_seed" in problems


# --- R8: whole-payload walk --------------------------------------------------
def test_r8_flags_nan_smuggled_in_a_nested_list():
    payload = _valid_payload()
    tkey = next(iter(payload["oracle_daily"]))
    payload["oracle_daily"][tkey]["pooled"]["extra"] = [1.0, float("nan")]
    problems = report.validate_formal_payload(payload)
    assert any(p.startswith("non_finite_float:") for p in problems)


def test_r8_flags_inf():
    payload = _valid_payload()
    tkey = next(iter(payload["oracle_daily"]))
    payload["oracle_daily"][tkey]["pooled"]["extra"] = float("inf")
    problems = report.validate_formal_payload(payload)
    assert any(p.startswith("non_finite_float:") for p in problems)


def test_r8_flags_non_str_key():
    payload = _valid_payload()
    tkey = next(iter(payload["oracle_daily"]))
    payload["oracle_daily"][tkey][123] = "leak"
    problems = report.validate_formal_payload(payload)
    assert any(p.startswith("non_str_key:") for p in problems)


def test_r8_flags_object_repr_string():
    payload = _valid_payload()
    payload["disclosures"]["leak"] = "<itsf.s0.dataset.Foo object at 0x7f0>"
    problems = report.validate_formal_payload(payload)
    assert any(p.startswith("object_repr_leak:") for p in problems)


def test_r8_flags_dataset_key_anywhere_in_the_tree():
    payload = _valid_payload()
    payload["structural"]["dataset"] = {"leaked": True}
    problems = report.validate_formal_payload(payload)
    assert any(p.startswith("dataset_key_present:") for p in problems)


# ===========================================================================
# validate_sealed_files
# ===========================================================================
def test_validate_sealed_files_accepts_a_valid_bundle():
    files, payload = _sealed_fixture()
    assert report.validate_sealed_files(files, payload) == []


def test_validate_sealed_files_manifest_missing_is_flagged():
    payload = _valid_payload()
    payload["mc_handoff_manifest"] = {
        "counts": payload["mc_handoff_manifest"]["counts"]}
    assert report.validate_sealed_files({}, payload) == \
        ["mc_handoff_manifest_files_missing"]


def test_validate_sealed_files_hash_mismatch_is_flagged():
    files, payload = _sealed_fixture()
    name = "MC_HANDOFF_E1_Base.jsonl"
    files[name] = files[name] + "\n"      # bytes change, line count doesn't
    problems = report.validate_sealed_files(files, payload)
    assert any(p.startswith("sealed_file_sha256_mismatch:") for p in problems)


def test_validate_sealed_files_line_count_mismatch_is_flagged():
    files, payload = _sealed_fixture()
    payload["mc_handoff_manifest"]["files"]["E1|Base"]["n_records"] = 999
    problems = report.validate_sealed_files(files, payload)
    assert any(p.startswith("sealed_file_line_count_mismatch:E1|Base")
              for p in problems)


def test_validate_sealed_files_internal_ts_name_leak_is_caught():
    line = json.dumps({"entry_ts": "x", "exit_ts": "y",
                       "trade_date": "2020-01-02"}, sort_keys=True)
    name = "MC_HANDOFF_E1_Base.jsonl"
    files = {name: line}
    payload = _valid_payload()
    payload["mc_handoff_manifest"] = {
        "counts": payload["mc_handoff_manifest"]["counts"],
        "files": {"E1|Base": {
            "file": name, "n_records": 1,
            "sha256": hashlib.sha256(line.encode("utf-8")).hexdigest()}},
    }
    problems = report.validate_sealed_files(files, payload)
    assert any(p.startswith("sealed_file_line_missing_field:E1|Base:0:"
                            "entry_timestamp") for p in problems)
    assert any(p.startswith("sealed_file_line_missing_field:E1|Base:0:"
                            "exit_timestamp") for p in problems)
    assert any(p.startswith("sealed_file_line_internal_name_leak:")
              for p in problems)


def test_validate_sealed_files_trade_date_outside_universe_is_flagged():
    files, payload = _sealed_fixture()
    problems = report.validate_sealed_files(
        files, payload, trade_date_universe={"2020-01-02"})
    assert any(p == "trade_date_outside_universe:2020-01-03"
              for p in problems)


def test_validate_sealed_files_no_universe_arg_skips_that_check():
    files, payload = _sealed_fixture()
    # No trade_date_universe supplied: the containment sub-check is skipped
    # entirely, so an otherwise-valid bundle still reports zero problems.
    assert report.validate_sealed_files(files, payload) == []
