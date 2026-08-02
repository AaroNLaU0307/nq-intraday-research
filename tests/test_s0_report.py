"""Tests for itsf.s0.report — the S0 formal-report boundary (M6.1.1-S1).

Hermetic and synthetic throughout: `_real_pieces()` builds ONE small S0Dataset
from in-memory synthetic bars (via tests/test_s0_context.py's generators —
no real archive is ever touched, no clock is read, nothing here consumes
researcher exposure) and runs it through the REAL production functions
(`itsf.s0.dataset.build_s0_dataset`, `itsf.s0.study.build_study`,
`itsf.s0.stability.build_stability_views`). `_valid_payload()` assembles a
formal payload from that REAL output for `oracle_daily` / `structural` /
`frequency` / `sizing_outputs` / `stability_views` — the M6.1 finding was
that the OLD fixture faked these with an invented pooled/by_era-only shape
that no real producer has ever emitted; this fixture is instead DERIVED from
reading study.py / stability.py / dataset.py and calling them for real.

`bootstrap_ci` and `feasibility_grid` stay HAND-CRAFTED: their shapes are
fully pinned by stats.py / gridmix.py's docstrings and would otherwise cost
a real n_boot=10,000 stationary-bootstrap run per cell (32 cells) for no
extra fixture fidelity.

`_valid_payload()` is sealable end-to-end: it passes every
S0_REPORT_CONTENT_CONTRACT.md §B rule via `validate_formal_payload` (when
given a matching `expected_governance`, see `_validate` below) AND
serializes cleanly through `to_formal_json`. Every test starts from a fresh
`_valid_payload()`/`_sealed_fixture()` call (real pieces are cached at
module level for speed; the assembled payload is a fresh nested structure
each time via `copy.deepcopy`) and breaks exactly one thing.
"""
from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping

import pytest
from conftest import make_trade_path
from test_s0_context import universe_of, weekdays

from itsf.s0 import context as ctx_mod
from itsf.s0 import costs, report
from itsf.s0.dataset import ERA_ACTUAL, ERA_PROXY, build_s0_dataset
from itsf.s0.stability import build_stability_views
from itsf.s0.study import (
    ENGINES,
    FROZEN_THETAS,
    StudyDayInput,
    build_study,
    theta_key,
)

SCENARIOS = ("Base", "Conservative", "Stress", "Severe")
BLOCKS = (5, 21)
ERAS = (ERA_PROXY, ERA_ACTUAL)
THETAS = tuple(sorted(theta_key(t) for t in FROZEN_THETAS))   # ("theta_0.3", "theta_0.5")


# ===========================================================================
# real-data fixture builders (hermetic — synthetic bars only, no archive)
# ===========================================================================
_REAL_CACHE: dict = {}


def _fp_then_recover_closes(base: float) -> list[float]:
    """Morning rises (d_open=+1) then gives it back all afternoon — a D_FP
    day under both frozen thetas (Y_cont well below 0.3). Mirrors the
    pattern tests/test_m6_chain.py uses for its own synthetic market."""
    closes = []
    for i in range(390):
        if i < 30:
            closes.append(base + i * 1.0)
        else:
            closes.append(base + 29.0 - (i - 29) * 0.05)
    return closes


def _make_day_inputs(ds, bars_by_date):
    """StudyDayInput per directional record day. Mirrors (but does not
    import — report.py's exclusive file scope forbids depending on the
    actively-developed scripts/s0_real_run.py entrypoint) that script's own
    `make_day_inputs`."""
    out: dict[str, object] = {}
    for r in ds.records:
        if r.labels.d_open not in (1, -1):
            continue
        bars = bars_by_date.get(r.trade_date)
        if bars is None:
            continue
        obs = ctx_mod.window_bars(bars, ctx_mod.OBS_LO_MINUTE,
                                  ctx_mod.OBS_HI_MINUTE)
        pm = ctx_mod.window_bars(bars, ctx_mod.PM_LO_MINUTE,
                                 ctx_mod.PM_HI_MINUTE)
        if not len(obs) or not len(pm):
            continue
        out[r.trade_date] = StudyDayInput(
            trade_date=r.trade_date, pm_bars=pm,
            or_high=float(obs["high"].max()), or_low=float(obs["low"].min()),
            d_open=int(r.labels.d_open))
    return out


def _plain(obj):
    """Recursively convert tuple -> list (S0Dataset's Mapping/tuple
    attributes are not yet JSON-shaped) so a value pulled straight off a
    real S0Dataset is safe to embed in a hand-assembled formal payload."""
    if isinstance(obj, Mapping):
        return {str(k): _plain(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_plain(v) for v in obj]
    return obj


def _real_pieces() -> dict:
    """Build ONE small synthetic S0Dataset + study + stability_views via the
    REAL production functions, cached for the whole test session.

    This is what makes oracle_daily/structural/frequency/sizing_outputs/
    stability_views ACTUAL producer shapes rather than an invented
    approximation (M6.1 finding: the old fixture faked A2 with a
    pooled/by_era-only shape no real payload has ever produced).
    """
    if "study" not in _REAL_CACHE:
        dates = weekdays("2020-01-02", 46)
        spec = {d: {"closes": _fp_then_recover_closes(20000.0)}
                for i, d in enumerate(dates) if i >= 14 and i % 2 == 1}
        bars, uni = universe_of(dates, spec)
        ds = build_s0_dataset(bars, uni)
        day_inputs = _make_day_inputs(ds, bars)
        scenarios = costs.build_scenarios(0.5, 0.75, 0.9)
        study = build_study(ds, day_inputs, scenarios)
        day_meta = {r.trade_date: {"year": r.year, "era": r.era,
                                   "d_open": int(r.labels.d_open or 0)}
                    for r in ds.records}
        stability_views = {
            t: build_stability_views(
                study["per_theta"][t], day_meta,
                vol_axis={d: "T2" for d in day_meta})
            for t in study["per_theta"]}
        _REAL_CACHE["ds"] = ds
        _REAL_CACHE["study"] = study
        _REAL_CACHE["stability_views"] = stability_views
    return _REAL_CACHE


def _structural_from_ds(ds) -> dict:
    """A1 structural section, pulled directly off the real S0Dataset
    attributes (S0_REPORT_CONTENT_CONTRACT.md A1: funnel + F10 dual report +
    na_table + label_anchor_availability + eras + groups)."""
    return {
        "funnel_counts": _plain(dict(ds.funnel_counts)),
        "f10_counts": _plain(dict(ds.f10_counts)),
        "f10_raw_membership_counts": _plain(dict(ds.f10_raw_membership_counts)),
        "na_table": _plain(ds.na_table),
        "label_anchor_availability": _plain(ds.label_anchor_availability),
        "eras": _plain(dict(ds.eras)),
        "groups": _plain(dict(ds.groups)),
    }


# ---------------------------------------------------------------------------
# hand-crafted cell builders — bootstrap_ci / feasibility_grid shapes are
# fully pinned by stats.py / gridmix.py's own docstrings; a real 10,000-
# resample run per cell would cost real compute for no extra fixture
# fidelity, so these mirror the documented shape instead of calling in.
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


def _feasibility_cell() -> dict:
    return {
        "grid": {"q0.5|r0.5": {"seed7": {"n_selected": 4}}},
        "n_tp_available": 16,
        "n_fp_available": 16,
        "method": "stratified (q,r) grid — frozen Appendix A, synthetic fixture",
    }


_GOV = {
    "trial_id": "S0-T001",
    "authorized_commit": "a" * 40,
    "engineering_seed": 20260731,
    "frozen_hashes": {f"FILE_{i}.md": "c" * 64 for i in range(7)},
    "registry_sequence_snapshot": 5,
}


def _valid_payload() -> dict:
    real = _real_pieces()
    ds, study = real["ds"], real["study"]
    tkeys = sorted(study["per_theta"])
    assert tkeys == list(THETAS), tkeys      # sanity: fixture matches frozen pair

    oracle_daily = {
        t: {"day_universe": copy.deepcopy(study["per_theta"][t]["day_universe"]),
           "executable": copy.deepcopy(study["per_theta"][t]["executable"])}
        for t in tkeys
    }
    theoretical_oracle = {
        t: copy.deepcopy(study["per_theta"][t]["theoretical_oracle"])
        for t in tkeys
    }
    e2_worst_days = {
        t: {scn: copy.deepcopy(study["per_theta"][t]["executable"]["E2"][scn]
                              ["worst_day_report"])
           for scn in SCENARIOS}
        for t in tkeys
    }
    sizing_outputs = {
        t: {"rows": copy.deepcopy(study["per_theta"][t]["sizing_rows"]),
           "coverage": copy.deepcopy(study["per_theta"][t]["sizing_coverage"])}
        for t in tkeys
    }
    frequency = {t: copy.deepcopy(study["per_theta"][t]["frequency"])
                for t in tkeys}
    stability_views = copy.deepcopy(real["stability_views"])
    structural = _structural_from_ds(ds)
    bootstrap_ci = {
        f"{t}|{e}|{s}|block{b}": _bootstrap_cell(b)
        for t in tkeys for e in ENGINES for s in SCENARIOS for b in BLOCKS
    }
    feasibility_grid = {
        "cells": {f"{t}|{e}|{s}": _feasibility_cell()
                 for t in tkeys for e in ENGINES for s in SCENARIOS},
        "regions": {"status": "pending_mc"},
    }
    mc_handoff_manifest = {
        "counts": {e: {s: {"n_records": len(study["records"][e][s])}
                      for s in SCENARIOS}
                  for e in ENGINES},
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
    governance = copy.deepcopy(_GOV)

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


def _validate(payload):
    """validate_formal_payload wrapper that defaults `expected_governance`
    to the payload's OWN governance block, so tests that are not
    specifically about the governance CONTEXT cross-check never see
    `governance_context_not_supplied` / `governance_mismatch` as noise
    (self-referential expected_governance can never itself disagree with
    the payload). Tests exercising that gate call
    `report.validate_formal_payload` directly with an explicit, DIFFERENT
    `expected_governance`."""
    gov = payload.get("governance") if isinstance(payload, dict) else None
    return report.validate_formal_payload(payload, expected_governance=gov)


def _sealed_fixture():
    """(files, payload): a REAL 8-file MC_HANDOFF bundle whose n_records,
    line count and sha256 all agree with `payload["mc_handoff_manifest"]
    ["counts"]`, and whose trade_date set on every file is EXACTLY the
    payload's own TP ∪ FP day universe (built from `record_to_formal_dict`
    output, `cost_scenario` overridden to match each file)."""
    payload = _valid_payload()
    universe = sorted({
        d for tcell in payload["oracle_daily"].values()
        for d in (*tcell["day_universe"]["tp_days"],
                 *tcell["day_universe"]["fp_days"])})
    counts = payload["mc_handoff_manifest"]["counts"]
    files: dict[str, str] = {}
    manifest_files: dict[str, object] = {}
    for eng in ENGINES:
        for scn in SCENARIOS:
            n = counts[eng][scn]["n_records"]
            assert n == len(universe), (eng, scn, n, len(universe))
            recs = [dict(report.record_to_formal_dict(
                        make_trade_path([1.0, 2.0], date=d, engine=eng)),
                       cost_scenario=scn)
                   for d in universe]
            name = f"MC_HANDOFF_{eng}_{scn}.jsonl"
            body = "\n".join(json.dumps(r, sort_keys=True) for r in recs)
            files[name] = body
            manifest_files[f"{eng}|{scn}"] = {
                "file": name, "n_records": n,
                "sha256": hashlib.sha256(body.encode("utf-8")).hexdigest()}
    payload["mc_handoff_manifest"] = {"counts": counts, "files": manifest_files}
    return files, payload


def _rewrite_sealed_file(files, payload, eng, scn, records, *,
                        sync_counts=True):
    """Rewrite one sealed MC_HANDOFF_<eng>_<scn>.jsonl body to hold exactly
    `records` (a list of already-formal-dict trade records) and refresh its
    manifest spec (n_records/sha256) to match the NEW body byte-for-byte.

    `sync_counts=True` (default) also updates
    `payload["mc_handoff_manifest"]["counts"][eng][scn]["n_records"]` to the
    new count, so a test isolates exactly ONE corruption at a time; a test
    that wants to deliberately create a counts-vs-lines conflict passes
    `sync_counts=False` (or mutates counts itself)."""
    name = f"MC_HANDOFF_{eng}_{scn}.jsonl"
    body = "\n".join(json.dumps(r, sort_keys=True) for r in records)
    files[name] = body
    spec = payload["mc_handoff_manifest"]["files"][f"{eng}|{scn}"]
    spec["n_records"] = len(records)
    spec["sha256"] = hashlib.sha256(body.encode("utf-8")).hexdigest()
    if sync_counts:
        payload["mc_handoff_manifest"]["counts"][eng][scn]["n_records"] = \
            len(records)


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
    assert _validate(formal) == []


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
    assert _validate(_valid_payload()) == []


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


# --- theta axis: EXACTLY the frozen pair -------------------------------------
def test_single_theta_payload_is_flagged():
    payload = _valid_payload()
    tkey = next(iter(payload["oracle_daily"]))
    del payload["oracle_daily"][tkey]
    problems = _validate(payload)
    assert any(p.startswith("theta_axis_mismatch") for p in problems)


# --- A2 day_universe: n_tp/n_fp/tp_days/fp_days + conservation flags --------
def test_day_universe_conservation_flag_false_is_flagged():
    payload = _valid_payload()
    tkey = next(iter(payload["oracle_daily"]))
    cons = payload["oracle_daily"][tkey]["day_universe"]["conservation"]
    flag = next(iter(cons))
    cons[flag] = False
    problems = _validate(payload)
    assert f"day_universe_conservation_false:{tkey}:{flag}" in problems


def test_day_universe_missing_is_flagged():
    payload = _valid_payload()
    tkey = next(iter(payload["oracle_daily"]))
    del payload["oracle_daily"][tkey]["day_universe"]
    problems = _validate(payload)
    assert f"day_universe_missing:{tkey}" in problems


# --- A2 executable matrix: E1/E2 x 4 scenarios, UNCONDITIONAL ---------------
def test_oracle_daily_executable_cell_missing_is_flagged():
    payload = _valid_payload()
    tkey = next(iter(payload["oracle_daily"]))
    del payload["oracle_daily"][tkey]["executable"]["E1"]["Base"]
    problems = _validate(payload)
    assert f"oracle_daily_executable_missing:{tkey}|E1|Base" in problems


# --- A1 structural: funnel + F10 dual + na_table + label anchors + eras/groups
def test_structural_missing_key_is_flagged():
    payload = _valid_payload()
    del payload["structural"]["eras"]
    problems = _validate(payload)
    assert "structural_missing:eras" in problems


def test_structural_label_anchor_availability_incomplete_is_flagged():
    payload = _valid_payload()
    del payload["structural"]["label_anchor_availability"]["y_cont"]
    problems = _validate(payload)
    assert "structural_label_anchor_availability_incomplete" in problems


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


def test_bootstrap_ci_missing_convergence_is_flagged():
    payload = _valid_payload()
    key = next(iter(payload["bootstrap_ci"]))
    del payload["bootstrap_ci"][key]["convergence"]
    problems = report.validate_formal_payload(payload)
    assert f"bootstrap_ci_convergence_missing:{key}" in problems


# --- R6: disclosures ---------------------------------------------------------
def test_pending_method_decisions_nonempty_is_flagged():
    payload = _valid_payload()
    payload["disclosures"]["pending_method_decisions"] = ["DR-M6-A_v2"]
    problems = report.validate_formal_payload(payload)
    assert "pending_method_decisions_unresolved" in problems


def test_pending_method_decisions_missing_key_is_flagged():
    payload = _valid_payload()
    del payload["disclosures"]["pending_method_decisions"]
    problems = _validate(payload)
    assert "pending_method_decisions_missing" in problems
    assert "pending_method_decisions_unresolved" not in problems


# --- R5: stability_views vol axis -------------------------------------------
def test_vol_terciles_unresolved_is_flagged():
    payload = _valid_payload()
    tkey = next(iter(payload["oracle_daily"]))
    payload["stability_views"][tkey]["E1"]["Base"]["vol_terciles"][
        "status"] = "unresolved"
    problems = report.validate_formal_payload(payload)
    assert "vol_axis_unresolved" in problems


def test_stability_views_cell_incomplete_is_flagged():
    payload = _valid_payload()
    tkey = next(iter(payload["oracle_daily"]))
    epochs = payload["stability_views"][tkey]["E1"]["Base"]["epochs"]
    bucket = next(k for k in epochs if k != "conservation_ok")
    del epochs[bucket]["n_positive"]
    problems = _validate(payload)
    assert any(p.startswith("stability_views_cell_incomplete:"
                            f"{tkey}|E1|Base|epochs|{bucket}")
              for p in problems)


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


def test_governance_context_not_supplied_is_flagged_by_default():
    payload = _valid_payload()
    problems = report.validate_formal_payload(payload)
    assert "governance_context_not_supplied" in problems


def test_governance_context_matching_expected_has_no_mismatch_problems():
    payload = _valid_payload()
    problems = _validate(payload)
    assert "governance_context_not_supplied" not in problems
    assert not any(p.startswith("governance_mismatch") for p in problems)


@pytest.mark.parametrize("field,new_value", [
    ("trial_id", "OTHER-TRIAL"),
    ("authorized_commit", "b" * 40),
    ("engineering_seed", 1),
    ("registry_sequence_snapshot", 999),
])
def test_governance_mismatch_is_flagged(field, new_value):
    payload = _valid_payload()
    expected = copy.deepcopy(payload["governance"])
    payload["governance"][field] = new_value
    problems = report.validate_formal_payload(
        payload, expected_governance=expected)
    assert f"governance_mismatch:{field}" in problems


def test_governance_fake_frozen_hash_is_flagged():
    payload = _valid_payload()
    expected = copy.deepcopy(payload["governance"])
    k = next(iter(payload["governance"]["frozen_hashes"]))
    payload["governance"]["frozen_hashes"][k] = "f" * 64
    problems = report.validate_formal_payload(
        payload, expected_governance=expected)
    assert "governance_mismatch:frozen_hashes" in problems


# --- R8: whole-payload walk --------------------------------------------------
def test_r8_flags_nan_smuggled_in_a_nested_list():
    payload = _valid_payload()
    tkey = next(iter(payload["oracle_daily"]))
    payload["oracle_daily"][tkey]["day_universe"]["extra"] = [1.0, float("nan")]
    problems = report.validate_formal_payload(payload)
    assert any(p.startswith("non_finite_float:") for p in problems)


def test_r8_flags_inf():
    payload = _valid_payload()
    tkey = next(iter(payload["oracle_daily"]))
    payload["oracle_daily"][tkey]["day_universe"]["extra"] = float("inf")
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


def test_validate_sealed_files_only_one_manifest_file_is_flagged():
    files, payload = _sealed_fixture()
    only_key = "E1|Base"
    payload["mc_handoff_manifest"]["files"] = {
        only_key: payload["mc_handoff_manifest"]["files"][only_key]}
    problems = report.validate_sealed_files(files, payload)
    assert any(p.startswith("mc_handoff_manifest_files_key_set_mismatch")
              for p in problems)


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


def test_validate_sealed_files_counts_vs_lines_conflict_is_flagged():
    files, payload = _sealed_fixture()
    payload["mc_handoff_manifest"]["counts"]["E1"]["Base"]["n_records"] += 1
    problems = report.validate_sealed_files(files, payload)
    assert any(p.startswith("sealed_file_counts_mismatch:E1|Base")
              for p in problems)
    # the manifest and the actual bytes still agree with EACH OTHER — only
    # the formal payload's own counts section drifted, proving the triple
    # equality catches a defect a manifest-vs-bytes-only check would miss.
    assert not any(p.startswith("sealed_file_line_count_mismatch:E1|Base")
                  for p in problems)


def test_validate_sealed_files_wrong_line_engine_is_flagged():
    files, payload = _sealed_fixture()
    name = "MC_HANDOFF_E1_Base.jsonl"
    lines = [json.loads(l) for l in files[name].splitlines()]
    lines[0]["engine"] = "E2"
    _rewrite_sealed_file(files, payload, "E1", "Base", lines)
    problems = report.validate_sealed_files(files, payload)
    assert any(p.startswith("sealed_file_line_engine_mismatch:E1|Base:0:")
              for p in problems)


def test_validate_sealed_files_wrong_line_scenario_is_flagged():
    files, payload = _sealed_fixture()
    name = "MC_HANDOFF_E1_Base.jsonl"
    lines = [json.loads(l) for l in files[name].splitlines()]
    lines[0]["cost_scenario"] = "Severe"
    _rewrite_sealed_file(files, payload, "E1", "Base", lines)
    problems = report.validate_sealed_files(files, payload)
    assert any(p.startswith("sealed_file_line_scenario_mismatch:E1|Base:0:")
              for p in problems)


def test_validate_sealed_files_duplicate_trade_date_is_flagged():
    files, payload = _sealed_fixture()
    name = "MC_HANDOFF_E1_Base.jsonl"
    lines = [json.loads(l) for l in files[name].splitlines()]
    lines[1]["trade_date"] = lines[0]["trade_date"]
    _rewrite_sealed_file(files, payload, "E1", "Base", lines)
    problems = report.validate_sealed_files(files, payload)
    assert any(p.startswith("sealed_file_duplicate_trade_date:E1|Base:")
              for p in problems)


def test_validate_sealed_files_missing_trade_date_is_flagged():
    files, payload = _sealed_fixture()
    name = "MC_HANDOFF_E1_Base.jsonl"
    lines = [json.loads(l) for l in files[name].splitlines()]
    dropped = lines.pop()
    _rewrite_sealed_file(files, payload, "E1", "Base", lines)
    problems = report.validate_sealed_files(files, payload)
    assert any(p.startswith("sealed_file_missing_trade_dates:E1|Base:")
              and dropped["trade_date"] in p for p in problems)


def test_validate_sealed_files_extra_trade_date_is_flagged():
    files, payload = _sealed_fixture()
    name = "MC_HANDOFF_E1_Base.jsonl"
    lines = [json.loads(l) for l in files[name].splitlines()]
    extra = dict(report.record_to_formal_dict(
        make_trade_path([1.0, 2.0], date="1999-01-04", engine="E1")),
        cost_scenario="Base")
    lines.append(extra)
    _rewrite_sealed_file(files, payload, "E1", "Base", lines)
    problems = report.validate_sealed_files(files, payload)
    assert any(p.startswith("sealed_file_extra_trade_dates:E1|Base:")
              and "1999-01-04" in p for p in problems)


def test_validate_sealed_files_replaced_trade_date_same_count_is_flagged():
    """Same total record count, one trade_date swapped for another — a
    count-only check (manifest n_records == line count == payload counts)
    would see NOTHING wrong here; the per-file exact date-SET check is what
    catches it."""
    files, payload = _sealed_fixture()
    name = "MC_HANDOFF_E1_Base.jsonl"
    lines = [json.loads(l) for l in files[name].splitlines()]
    original_date = lines[0]["trade_date"]
    lines[0]["trade_date"] = "1999-01-04"
    _rewrite_sealed_file(files, payload, "E1", "Base", lines)
    problems = report.validate_sealed_files(files, payload)
    assert not any(p.startswith("sealed_file_line_count_mismatch:E1|Base")
                  for p in problems)
    assert not any(p.startswith("sealed_file_counts_mismatch:E1|Base")
                  for p in problems)
    assert any(p.startswith("sealed_file_missing_trade_dates:E1|Base:")
              and original_date in p for p in problems)
    assert any(p.startswith("sealed_file_extra_trade_dates:E1|Base:")
              and "1999-01-04" in p for p in problems)


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


def test_validate_sealed_files_no_trailing_newline_line_count_is_exact():
    """Pin: a sealed body built with NO trailing newline (the real
    render_s0_report body is `"\\n".join(...)`, never `... + "\\n"`) is
    counted correctly by `str.splitlines()` — no phantom empty final line,
    unlike the classic `str.split("\\n")` off-by-one."""
    files, payload = _sealed_fixture()
    name = "MC_HANDOFF_E1_Base.jsonl"
    body = files[name]
    assert not body.endswith("\n")
    n_expected = payload["mc_handoff_manifest"]["files"]["E1|Base"]["n_records"]
    assert len(body.splitlines()) == n_expected
    assert report.validate_sealed_files(files, payload) == []


def test_post_injection_corruption_caught_by_second_validate_call():
    """M6.1 item 4 worked example: `validate_formal_payload` alone cannot
    see the sealed JSONL bytes — they do not exist until the renderer
    serializes them AFTER this payload is judged sealable — so a payload
    that is sealable on the FIRST call can still carry a corruption that
    only shows up once the mc_handoff_manifest "files" sub-key is injected.
    The renderer must call `validate_formal_payload` a SECOND time
    post-injection (see that function's docstring), but that second call is
    not sufficient BY ITSELF either: it never opens `files`, so a
    counts-vs-actual-bytes conflict is invisible to it and is caught only by
    `validate_sealed_files` on the same post-injection payload.
    """
    files, payload = _sealed_fixture()

    # FIRST call (pre-injection, as today): sealable.
    pre_problems = _validate(payload)
    assert pre_problems == []

    # A corruption that ONLY exists once the manifest "files" sub-key is
    # injected — e.g. the injected per-file spec's n_records silently
    # drifting from the counts section it is supposed to mirror.
    # `validate_formal_payload` never reads "files" at all (only "counts"),
    # so this is INVISIBLE to a payload-only check even on a second call.
    payload["mc_handoff_manifest"]["files"]["E1|Base"]["n_records"] += 1

    # SECOND call (post-injection, per the mandatory two-call contract):
    # still reports nothing — proving the second call alone is not enough.
    post_problems = _validate(payload)
    assert post_problems == []

    # validate_sealed_files (against the SAME post-injection payload) is
    # what actually catches it — it is the only one of the two that ever
    # opens `files` and counts the real lines.
    sealed_problems = report.validate_sealed_files(files, payload)
    assert any(p.startswith("sealed_file_line_count_mismatch:E1|Base")
              for p in sealed_problems)
    assert any(p.startswith("sealed_file_counts_mismatch:E1|Base")
              for p in sealed_problems)
