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
import importlib.util
import json
import types
from collections.abc import Mapping
from pathlib import Path

import pytest
from conftest import make_trade_path
from test_s0_context import universe_of, weekdays

from itsf.contracts import TradePathRecord
from itsf.s0 import context as ctx_mod
from itsf.s0 import costs, report
from itsf.s0 import gridmix as m_gridmix
from itsf.s0.dataset import ERA_ACTUAL, ERA_PROXY, build_s0_dataset
from itsf.s0.stability import build_stability_views
from itsf.s0.study import (
    ENGINES,
    FROZEN_THETAS,
    StudyDayInput,
    build_study,
    theta_key,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

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


def _vol_axis_with_terciles_and_na(day_meta: dict) -> dict[str, str]:
    """A vol_axis covering MOST (not all) of `day_meta`'s dates, spread over
    THREE opaque tercile labels — so `build_stability_views`'s resolved
    `vol_terciles` view carries the full mission-item-6 stratum set (three
    terciles + the reserved `vol_na` bucket for the dates deliberately left
    out here) against the REAL D_TP population, not a single-bucket fake.
    `mod=5, rem=0` is a verified split (see the M6.1.2-S1 fixture-derivation
    note in this module's docstring) that lands >=1 vol_na day and all
    three labels inside BOTH frozen thetas' 16-day D_TP set for this
    module's fixed synthetic market."""
    labels = ("vol_lo", "vol_mid", "vol_hi")
    out: dict[str, str] = {}
    for i, d in enumerate(sorted(day_meta)):
        if i % 5 == 0:
            continue                      # left out on purpose -> vol_na
        out[d] = labels[i % 3]
    return out


def _real_pieces() -> dict:
    """Build ONE small synthetic S0Dataset + study + stability_views +
    feasibility_grid via the REAL production functions, cached for the
    whole test session.

    This is what makes oracle_daily/structural/frequency/sizing_outputs/
    stability_views/feasibility_grid ACTUAL producer shapes rather than an
    invented approximation (M6.1 finding: the old fixture faked A2 with a
    pooled/by_era-only shape no real payload has ever produced; M6.1.2-S1
    finding: feasibility_grid was a single hand-written fake cell that bore
    no relation to gridmix.py's real 63-point grid, and vol_terciles was
    built from a single constant label so it could never carry the real
    three-tercile-plus-vol_na stratum set).
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
        vol_axis = _vol_axis_with_terciles_and_na(day_meta)
        stability_views = {
            t: build_stability_views(
                study["per_theta"][t], day_meta, vol_axis=vol_axis)
            for t in study["per_theta"]}

        # feasibility_grid: PRODUCER-DERIVED (mission item 7) — call
        # gridmix.build_grid on the REAL per-theta D_TP/D_FP populations
        # (mirrors scripts/s0_real_run.py::build_full_study_result's own
        # per-theta/engine/scenario loop, read-only reference), never a
        # hand-written single-cell fake.
        feasibility_grid: dict[str, dict] = {}
        for t, tblock in study["per_theta"].items():
            p = tblock["frequency"]["pooled"]["continuation_base_rate_p"]
            for eng in ENGINES:
                for scn in SCENARIOS:
                    d_tp = tblock["d_tp"][eng][scn]
                    d_fp = tblock["d_fp"][eng][scn]
                    strata = {d: (d[:4], "R", "none")
                             for d in {**d_tp, **d_fp}}
                    feasibility_grid[f"{t}|{eng}|{scn}"] = m_gridmix.build_grid(
                        d_tp, d_fp, strata, p)

        _REAL_CACHE["ds"] = ds
        _REAL_CACHE["study"] = study
        _REAL_CACHE["stability_views"] = stability_views
        _REAL_CACHE["feasibility_grid"] = feasibility_grid
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
# hand-crafted cell builders — bootstrap_ci shape is fully pinned by
# stats.py's own docstring; a real 10,000-resample run per cell would cost
# real compute for no extra fixture fidelity, so this mirrors the documented
# shape instead of calling in. feasibility_grid is PRODUCER-DERIVED instead
# (via gridmix.build_grid in `_real_pieces()`, mission item 7) — no
# hand-written single-cell fake.
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


def _strkeys(obj):
    """Recursively stringify non-str dict keys — mirrors scripts/
    s0_real_run.py's own `_strkeys` (read-only reference): gridmix.py's
    real `per_seed` dict is keyed by INT master seeds (7, 13, 31), and the
    formal payload boundary (report._clean / to_formal_json) hard-rejects a
    non-str dict key, so the REAL renderer always stringifies before a grid
    ever reaches the formal side. Reproduced locally (never imported from
    the main-agent-owned script) so this fixture matches what actually gets
    sealed."""
    if isinstance(obj, dict):
        return {str(k): _strkeys(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_strkeys(v) for v in obj]
    return obj


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
        t: {scn: {
                **copy.deepcopy(
                    study["per_theta"][t]["executable"]["E2"][scn]
                    ["worst_day_report"]),
                # mission item 5 (P1/P5 GOVERNANCE): DR-M6-H (the P1/P5
                # estimator ruling) is still OPEN — no current producer
                # module resolves it. scripts/s0_real_run.py's real
                # build_full_study_result already emits this field
                # conditioned on `config.methods.worst_day_estimator`; this
                # TEST_ONLY "resolved" is a FIXTURE-ONLY stand-in so the
                # valid baseline payload can seal, never a claim that DR-M6-H
                # is actually ruled. See test_worst_day_estimator_unresolved_
                # is_flagged for the fail-closed refusal path this same
                # fixture proves.
                "estimator_status": "resolved",  # TEST_ONLY
            }
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
        "cells": {k: _strkeys(copy.deepcopy(v))
                 for k, v in real["feasibility_grid"].items()},
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
        # A11 na_conservation restatement (mission item 8). NO current
        # producer populates this key — see report.py's docstring and this
        # file's module docstring for the hand-off note; this fixture-only
        # block exists purely so the VALID baseline payload can seal.
        "na_conservation": {
            "per_table_total_na": {
                table: sum(row["na"] for row in fields.values())
                for table, fields in ds.na_table["per_field"].items()},
            "conservation_ok": True,
        },
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


def _sealed_files_manifest(files: dict[str, str]) -> dict[str, object]:
    """mission M6.1.2-S3 item 8: the `mc_handoff_manifest["sealed_files"]`
    shape the real renderer stamps (scripts/s0_real_run.py::
    render_s0_report) — {filename: {"sha256": <64hex>, "bytes": <int>}} for
    every file in `files`, computed FROM those same bytes."""
    return {name: {"sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
                   "bytes": len(body.encode("utf-8"))}
           for name, body in files.items()}


def _sealed_fixture():
    """(files, payload): a REAL 8-file MC_HANDOFF bundle whose n_records,
    line count and sha256 all agree with `payload["mc_handoff_manifest"]
    ["counts"]`, and whose trade_date set on every file is EXACTLY the
    payload's own TP ∪ FP day universe (built from `record_to_formal_dict`
    output, `cost_scenario` overridden to match each file). Also carries the
    `sealed_files`/`self_excluded` sub-keys (mission item 8) covering these
    8 files — `self_excluded` names S0_REPORT.json, which this synthetic
    fixture never builds, mirroring the real renderer's own shape."""
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
    payload["mc_handoff_manifest"] = {
        "counts": counts, "files": manifest_files,
        "sealed_files": _sealed_files_manifest(files),
        "self_excluded": ["S0_REPORT.json"]}
    return files, payload


def _rewrite_sealed_file(files, payload, eng, scn, records, *,
                        sync_counts=True, sync_sealed_files=True):
    """Rewrite one sealed MC_HANDOFF_<eng>_<scn>.jsonl body to hold exactly
    `records` (a list of already-formal-dict trade records) and refresh its
    manifest spec (n_records/sha256) to match the NEW body byte-for-byte.

    `sync_counts=True` (default) also updates
    `payload["mc_handoff_manifest"]["counts"][eng][scn]["n_records"]` to the
    new count, so a test isolates exactly ONE corruption at a time; a test
    that wants to deliberately create a counts-vs-lines conflict passes
    `sync_counts=False` (or mutates counts itself). `sync_sealed_files=True`
    (default) likewise refreshes `mc_handoff_manifest["sealed_files"]`
    (mission item 8) so an UNRELATED mutation (e.g. a line-level corruption)
    never also trips the item-8 reconciliation as incidental noise; a test
    targeting item 8 itself passes `sync_sealed_files=False`."""
    name = f"MC_HANDOFF_{eng}_{scn}.jsonl"
    body = "\n".join(json.dumps(r, sort_keys=True) for r in records)
    files[name] = body
    spec = payload["mc_handoff_manifest"]["files"][f"{eng}|{scn}"]
    spec["n_records"] = len(records)
    spec["sha256"] = hashlib.sha256(body.encode("utf-8")).hexdigest()
    if sync_counts:
        payload["mc_handoff_manifest"]["counts"][eng][scn]["n_records"] = \
            len(records)
    if sync_sealed_files:
        sealed = payload["mc_handoff_manifest"].get("sealed_files")
        if isinstance(sealed, dict) and name in sealed:
            body_bytes = body.encode("utf-8")
            sealed[name] = {
                "sha256": hashlib.sha256(body_bytes).hexdigest(),
                "bytes": len(body_bytes)}


# ===========================================================================
# M6.1.2-S1 — third refusal level: the REAL production renderer
# (scripts/s0_real_run.py::render_s0_report), loaded read-only via
# importlib.util.spec_from_file_location (the tests/test_s0_runner.py::
# real_run_module idiom, replicated locally per this module's exclusive
# file-scope boundary — never imported from another test module).
# ===========================================================================
_SCRIPT_CACHE: dict = {}


def real_run_module():
    """Import scripts/s0_real_run.py once (READ-ONLY: never written to by
    this file). Mirrors tests/test_s0_runner.py::real_run_module exactly."""
    if "mod" not in _SCRIPT_CACHE:
        script = REPO_ROOT / "scripts" / "s0_real_run.py"
        spec = importlib.util.spec_from_file_location("s0_real_run", script)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _SCRIPT_CACHE["mod"] = mod
    return _SCRIPT_CACHE["mod"]


def _mc_records_for_universe(universe: list[str]) -> dict[str, dict[str, list]]:
    """dict[engine][scenario] -> list[TradePathRecord], one record per date
    in `universe`, engine/cost_scenario set to match the file bucket EXACTLY
    (render_s0_report's own validate_sealed_files call checks per-line
    engine/cost_scenario identity, so a record built via
    conftest.make_trade_path — which hardcodes cost_scenario="Conservative"
    — would fail that check under any other scenario bucket)."""
    out: dict[str, dict[str, list]] = {}
    for eng in ENGINES:
        out[eng] = {}
        for scn in SCENARIOS:
            out[eng][scn] = [
                TradePathRecord(
                    trade_date=d, engine=eng, cost_scenario=scn, direction=1,
                    entry_ts=f"{d}T10:00:00-04:00",
                    exit_ts=f"{d}T15:44:00-04:00",
                    entry_fill=20000.0, exit_fill=20001.0,
                    final_pnl_per_contract=1.0, sizing_anchor_usd=100.0,
                    # mission M6.1.2-S3 item 2: mtm_close_pnl_1m/
                    # mtm_adverse_pnl_1m are frozen §10.1 per-minute mark
                    # series of an ACTUAL trade path and must be NON-EMPTY
                    # (report._is_nonempty_number_list) — a bare
                    # TradePathRecord() default (`[]`) is not a realistic
                    # sealed line.
                    mtm_close_pnl_1m=[1.0, 1.0], mtm_adverse_pnl_1m=[0.0, 0.0])
                for d in universe]
    return out


def _real_render_result() -> dict:
    """M6.1.3 integration: the renderer now RECONCILES the formal payload
    against the internal producer envelope, so this fixture must BE a real
    producer result — formal sections deep-copied (per-test mutation
    isolation), internal envelope shared read-only. A hand-built formal-
    only dict can no longer seal (that is the point of the wiring)."""
    import copy
    from test_m6_chain import _payload
    src = _payload()
    shared = ("dataset", "study", "na_reason_counts",
              "reported_total_na")            # read-only sharing
    out = {k: (v if k in shared else copy.deepcopy(v))
           for k, v in src.items() if k != "records"}
    # records are mutable dataclass instances (no DataFrames): per-test
    # deepcopy so a mutation test can never contaminate the shared cache.
    out["records"] = copy.deepcopy(src["records"])
    return out


def _assert_real_renderer_refuses(result: dict) -> None:
    with pytest.raises(ValueError):
        real_run_module().render_s0_report(
            result, expected_governance=result["governance"])


# ---------------------------------------------------------------------------
# dotted-path get/set — navigates dict keys AND list indices identically, so
# one mutation function can target e.g. ("sizing_outputs", theta, "rows",
# "E1", "Base", 0) (a list element) exactly like a plain dict path.
# ---------------------------------------------------------------------------
def _get_path(d, path):
    for key in path:
        d = d[key]
    return d


def _set_path(d, path, value) -> None:
    for key in path[:-1]:
        d = d[key]
    d[path[-1]] = value


def _assert_leaf_family_refused(path: tuple, expected_prefix: str,
                                mutated_value) -> None:
    """One mutation class for one required-leaf FAMILY (mission items 2 + 9):
    apply `mutated_value` at `path` on a fresh valid payload AND a fresh
    real-render result, and prove refusal at BOTH the validator level
    (a problem starting with `expected_prefix`) and the real production
    renderer level (render_s0_report raises ValueError)."""
    payload = _valid_payload()
    _set_path(payload, path, mutated_value)
    problems = _validate(payload)
    assert any(p.startswith(expected_prefix) for p in problems), (
        path, mutated_value, problems)

    result = _real_render_result()
    _set_path(result, path, mutated_value)
    _assert_real_renderer_refuses(result)


def _assert_mutation_refused(mutate_fn, expected_prefix: str) -> list[str]:
    """General-purpose two-level refusal proof (mission item 9) for a
    mutation that is NOT a single dotted-path leaf swap (day-universe
    invariants, sealed-file-only checks, feasibility-grid inner-point
    surgery, ...): `mutate_fn(d)` mutates `d` IN PLACE. Applied once to a
    fresh `_valid_payload()` (asserting a problem starting with
    `expected_prefix`) and once to a fresh `_real_render_result()`
    (asserting the real production renderer raises). Returns the
    payload-level problems for any additional caller assertions."""
    payload = _valid_payload()
    mutate_fn(payload)
    problems = _validate(payload)
    assert any(p.startswith(expected_prefix) for p in problems), problems

    result = _real_render_result()
    mutate_fn(result)
    _assert_real_renderer_refuses(result)
    return problems


# Every required-leaf FAMILY exercised with the mission's three mutation
# classes (None / wrong-type / opaque-garbage-dict). `T0` is THETAS[0]
# ("theta_0.3") — any frozen theta works identically since both are fully
# reported; a fixed representative keeps the parametrize grid readable.
T0 = THETAS[0]
_WRONG_TYPE = ["wrong", "type"]                 # a list where a mapping/str
                                                # is expected — cheap, generic
_GARBAGE_DICT = {"junk": 1}                     # structurally-plausible-
                                                # looking but content-empty

_LEAF_FAMILIES = [
    ("structural_funnel_counts",
     ("structural", "funnel_counts"), "structural_funnel_counts_incomplete"),
    ("structural_na_table",
     ("structural", "na_table"), "structural_na_table_incomplete"),
    ("structural_label_anchor_availability",
     ("structural", "label_anchor_availability"),
     "structural_label_anchor_availability_incomplete"),
    ("structural_eras",
     ("structural", "eras"), "structural_eras_incomplete"),
    ("structural_groups",
     ("structural", "groups"), "structural_groups_incomplete"),
    ("day_universe",
     ("oracle_daily", T0, "day_universe"), "day_universe_"),
    ("oracle_daily_executable_cell",
     ("oracle_daily", T0, "executable", "E1", "Base"),
     "oracle_daily_executable"),
    ("theoretical_oracle_cell",
     ("theoretical_oracle", T0), "theoretical_oracle"),
    ("e2_worst_days_cell",
     ("e2_worst_days", T0, "Base"), "e2_worst_days_"),
    ("frequency_pooled_cell",
     ("frequency", T0, "pooled"), "frequency_cell_incomplete"),
    ("sizing_row",
     ("sizing_outputs", T0, "rows", "E1", "Base", 0),
     "sizing_outputs_row_incomplete"),
    ("stability_epoch_cell",
     ("stability_views", T0, "E1", "Base", "epochs", "2010-2013"),
     "stability_views_cell_incomplete"),
    ("stability_vol_terciles_block",
     ("stability_views", T0, "E1", "Base", "vol_terciles"),
     "stability_views_vol"),
    ("feasibility_cell",
     ("feasibility_grid", "cells", f"{T0}|E1|Base"),
     "feasibility_grid_cell_incomplete"),
    ("bootstrap_cell",
     ("bootstrap_ci", f"{T0}|E1|Base|block5"), "bootstrap_ci"),
    ("governance_frozen_hashes",
     ("governance", "frozen_hashes"), "governance_frozen_hash"),
    ("mc_handoff_counts_cell",
     ("mc_handoff_manifest", "counts", "E1", "Base"),
     "mc_handoff_manifest_counts"),
    ("disclosures_na_conservation",
     ("disclosures", "na_conservation"), "disclosures_na_conservation"),
    ("era_axis_axes",
     ("era_axis", "axes"), "era_axis_axes_incomplete"),
]


@pytest.mark.parametrize("name,path,prefix", _LEAF_FAMILIES,
                         ids=[f"{n}_none" for n, _p, _pf in _LEAF_FAMILIES])
def test_leaf_family_set_to_none_is_refused(name, path, prefix):
    _assert_leaf_family_refused(path, prefix, None)


@pytest.mark.parametrize("name,path,prefix", _LEAF_FAMILIES,
                         ids=[f"{n}_wrong_type" for n, _p, _pf
                             in _LEAF_FAMILIES])
def test_leaf_family_wrong_type_is_refused(name, path, prefix):
    _assert_leaf_family_refused(path, prefix, _WRONG_TYPE)


@pytest.mark.parametrize("name,path,prefix", _LEAF_FAMILIES,
                         ids=[f"{n}_garbage_dict" for n, _p, _pf
                             in _LEAF_FAMILIES])
def test_leaf_family_garbage_dict_is_refused(name, path, prefix):
    _assert_leaf_family_refused(path, prefix, dict(_GARBAGE_DICT))


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


def test_real_render_result_seals_via_the_real_production_renderer():
    """Sanity anchor for every mutation test's THIRD refusal level (mission
    item 9): the UNMUTATED `_real_render_result()` fixture must actually
    seal end-to-end through scripts/s0_real_run.py's real `render_s0_report`
    (full split_envelope -> validate_formal_payload (x2) -> JSONL
    serialization -> validate_sealed_files chain) — proving every mutation
    test's "the real renderer refuses" assertion is meaningful and not
    vacuously true because the baseline never sealed in the first place."""
    result = _real_render_result()
    files = real_run_module().render_s0_report(
        result, expected_governance=result["governance"])
    assert "S0_REPORT.json" in files
    assert sum(1 for n in files if n.startswith("MC_HANDOFF_")) == 8


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


# --- A2 day_universe HARD invariants (mission item 3): n_tp/n_fp COUNT
# identity, no duplicate day in either list, the TP/FP partition disjoint,
# and cross-theta population identity — each a DISTINCT problem code, each
# proven refused at both the validator AND the real-renderer level.
T1 = THETAS[1]


def test_day_universe_n_tp_count_mismatch_is_flagged():
    def _mutate(d):
        d["oracle_daily"][T0]["day_universe"]["n_tp"] += 1
    _assert_mutation_refused(_mutate, f"day_universe_count_mismatch:{T0}:n_tp")


def test_day_universe_n_fp_count_mismatch_is_flagged():
    def _mutate(d):
        d["oracle_daily"][T0]["day_universe"]["n_fp"] += 1
    _assert_mutation_refused(_mutate, f"day_universe_count_mismatch:{T0}:n_fp")


def test_day_universe_tp_days_duplicate_is_flagged():
    def _mutate(d):
        du = d["oracle_daily"][T0]["day_universe"]
        du["tp_days"].append(du["tp_days"][0])
        du["n_tp"] += 1                       # isolate: count identity holds
    _assert_mutation_refused(
        _mutate, f"day_universe_duplicate_days:{T0}:tp_days")


def test_day_universe_fp_days_duplicate_is_flagged():
    def _mutate(d):
        du = d["oracle_daily"][T0]["day_universe"]
        du["fp_days"].append(du["fp_days"][0])
        du["n_fp"] += 1
    _assert_mutation_refused(
        _mutate, f"day_universe_duplicate_days:{T0}:fp_days")


def test_day_universe_tp_fp_overlap_is_flagged():
    def _mutate(d):
        du = d["oracle_daily"][T0]["day_universe"]
        du["fp_days"].append(du["tp_days"][0])
        du["n_fp"] += 1
    _assert_mutation_refused(_mutate, f"day_universe_tp_fp_overlap:{T0}")


def test_day_universe_cross_theta_population_mismatch_is_flagged():
    """The union tp∪fp must be IDENTICAL across the two frozen thetas — only
    the partition may move. Adding a day to ONE theta's population (not
    merely re-partitioning it) breaks that identity."""
    def _mutate(d):
        du = d["oracle_daily"][T0]["day_universe"]
        du["tp_days"] = du["tp_days"] + ["1999-01-04"]
        du["n_tp"] += 1
    _assert_mutation_refused(
        _mutate, "day_universe_cross_theta_population_mismatch")


def test_day_universe_date_format_invalid_is_flagged():
    def _mutate(d):
        du = d["oracle_daily"][T0]["day_universe"]
        du["tp_days"] = [du["tp_days"][0].replace("-", "/")] + du["tp_days"][1:]
    _assert_mutation_refused(
        _mutate, f"day_universe_date_format_invalid:{T0}:tp_days")


# --- A2 executable matrix: E1/E2 x 4 scenarios, UNCONDITIONAL ---------------
def test_oracle_daily_executable_cell_missing_is_flagged():
    payload = _valid_payload()
    tkey = next(iter(payload["oracle_daily"]))
    del payload["oracle_daily"][tkey]["executable"]["E1"]["Base"]
    problems = _validate(payload)
    assert f"oracle_daily_executable_missing:{tkey}|E1|Base" in problems


# --- A2 ORACLE EXECUTABLE deep real structure (mission item 5): pooled +
# by_era{PROXY,ACTUAL} + per-day (date, USD) pairs, against the REAL
# study.py `_series_block`/`_by_era_and_pooled` shape.
def test_oracle_daily_executable_drop_pooled_is_flagged():
    def _mutate(d):
        del d["oracle_daily"][T0]["executable"]["E1"]["Base"]["pooled"]
    _assert_mutation_refused(_mutate, f"series_block_missing:{T0}|E1|Base|pooled")


def test_oracle_daily_executable_drop_one_era_is_flagged():
    def _mutate(d):
        del d["oracle_daily"][T0]["executable"]["E1"]["Base"]["by_era"][
            ERA_PROXY]
    _assert_mutation_refused(
        _mutate, f"oracle_daily_executable_by_era_missing:{T0}|E1|Base")


def test_oracle_daily_executable_corrupt_daily_date_key_is_flagged():
    def _mutate(d):
        series = d["oracle_daily"][T0]["executable"]["E1"]["Base"]["pooled"][
            "daily_pnl_usd"]
        series[0] = ["not-a-date", series[0][1]]
    _assert_mutation_refused(
        _mutate, f"series_block_date_invalid:{T0}|E1|Base|pooled")


def test_oracle_daily_executable_corrupt_daily_value_is_flagged():
    def _mutate(d):
        series = d["oracle_daily"][T0]["executable"]["E1"]["Base"]["pooled"][
            "daily_pnl_usd"]
        series[0] = [series[0][0], "not-a-number"]
    _assert_mutation_refused(
        _mutate, f"series_block_value_invalid:{T0}|E1|Base|pooled")


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


# --- R5/A2b: conservation_ok must be LITERALLY True on every partitioning
# axis (mission item 6) — previously only the axis's KEY SET was checked,
# never the flag's own value.
_STABILITY_AXES_FOR_CONSERVATION = (
    "epochs", "by_year", "leave_one_year_out", "by_direction", "vol_terciles")


@pytest.mark.parametrize("axis", _STABILITY_AXES_FOR_CONSERVATION)
def test_stability_conservation_ok_false_is_flagged(axis):
    def _mutate(d):
        d["stability_views"][T0]["E1"]["Base"][axis]["conservation_ok"] = False
    _assert_mutation_refused(
        _mutate, f"stability_views_conservation_not_true:{T0}|E1|Base|{axis}")


# --- A2b vol_terciles RESOLVED shape: the three opaque-vocabulary terciles
# PLUS the reserved vol_na bucket, each a full _cell (mission item 6).
def test_stability_vol_terciles_missing_stratum_is_flagged():
    def _mutate(d):
        vol = d["stability_views"][T0]["E1"]["Base"]["vol_terciles"]
        tercile_keys = sorted(set(vol) - {"vol_na", "conservation_ok"})
        del vol[tercile_keys[0]]
    _assert_mutation_refused(
        _mutate, f"stability_views_vol_tercile_count:{T0}|E1|Base")


def test_stability_vol_tercile_bucket_missing_cell_field_is_flagged():
    def _mutate(d):
        vol = d["stability_views"][T0]["E1"]["Base"]["vol_terciles"]
        tercile_keys = sorted(set(vol) - {"vol_na", "conservation_ok"})
        del vol[tercile_keys[0]]["n_positive"]
    _assert_mutation_refused(
        _mutate, f"stability_views_cell_incomplete:{T0}|E1|Base|vol_terciles")


def test_stability_vol_na_bucket_missing_is_flagged():
    def _mutate(d):
        vol = d["stability_views"][T0]["E1"]["Base"]["vol_terciles"]
        del vol["vol_na"]
    _assert_mutation_refused(_mutate, f"stability_views_vol_na_missing:{T0}|E1|Base")


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
# Appendix A FEASIBILITY GRID — the FULL frozen 63-point (q, r) grid inside
# every cells[...]["grid"] (mission item 7), not just the outer
# {grid, n_tp_available, n_fp_available, method} field set.
# ===========================================================================
def _feasible_point_key(cell: dict) -> str:
    """First (q, r) grid-point key in `cell["grid"]` that is NOT
    infeasible_by_sample — one that actually carries a real per_seed
    selection (an infeasible point legitimately has none)."""
    for k, v in cell["grid"].items():
        if not v["infeasible_by_sample"]:
            return k
    raise AssertionError("fixture has no feasible grid point")


def test_feasibility_grid_62_cells_is_flagged():
    """Dropping ONE of the 63 frozen (q, r) grid points must be caught —
    the OUTER {grid, n_tp_available, ...} field set alone would miss this."""
    def _mutate(d):
        cell = d["feasibility_grid"]["cells"][f"{T0}|E1|Base"]
        del cell["grid"][_feasible_point_key(cell)]
    _assert_mutation_refused(
        _mutate, f"feasibility_grid_point_missing:{T0}|E1|Base:")


def test_feasibility_grid_cell_missing_a_seed_is_flagged():
    def _mutate(d):
        cell = d["feasibility_grid"]["cells"][f"{T0}|E1|Base"]
        pk = _feasible_point_key(cell)
        del cell["grid"][pk]["per_seed"]["13"]
    _assert_mutation_refused(
        _mutate, f"feasibility_grid_point_seeds:{T0}|E1|Base:")


def test_feasibility_grid_seed_entry_missing_realized_is_flagged():
    def _mutate(d):
        cell = d["feasibility_grid"]["cells"][f"{T0}|E1|Base"]
        pk = _feasible_point_key(cell)
        del cell["grid"][pk]["per_seed"]["7"]["realized_precision"]
    _assert_mutation_refused(
        _mutate, f"feasibility_grid_seed_entry_incomplete:{T0}|E1|Base:")


def test_feasibility_grid_infeasible_flag_absent_is_flagged():
    def _mutate(d):
        cell = d["feasibility_grid"]["cells"][f"{T0}|E1|Base"]
        pk = _feasible_point_key(cell)
        del cell["grid"][pk]["infeasible_by_sample"]
    _assert_mutation_refused(
        _mutate,
        f"feasibility_grid_point_infeasible_flag_missing:{T0}|E1|Base:")


# ===========================================================================
# A11 disclosures.na_conservation (mission item 8): the contract's "NA 守恒
# 复述". NOT populated by any current producer — see this module's docstring
# / the final hand-off note for the exact producer change needed.
# ===========================================================================
def test_disclosures_na_conservation_missing_is_flagged():
    def _mutate(d):
        del d["disclosures"]["na_conservation"]
    _assert_mutation_refused(_mutate, "disclosures_na_conservation_missing")


def test_disclosures_na_conservation_totals_invalid_is_flagged():
    def _mutate(d):
        d["disclosures"]["na_conservation"]["per_table_total_na"] = {
            "features": "not-a-number"}
    _assert_mutation_refused(
        _mutate, "disclosures_na_conservation_totals_invalid")


def test_disclosures_na_conservation_flag_not_true_is_flagged():
    def _mutate(d):
        d["disclosures"]["na_conservation"]["conservation_ok"] = False
    _assert_mutation_refused(
        _mutate, "disclosures_na_conservation_flag_not_true")


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


def test_validate_sealed_files_empty_universe_with_nonempty_file_is_flagged():
    """Mission item 4: the per-file date-set comparison is UNCONDITIONAL —
    even when the payload's day universe is EMPTY (every theta's tp_days/
    fp_days lists empty), a file that still carries a date must be flagged,
    never silently skipped by a stale `if universe:` short-circuit."""
    payload = _valid_payload()
    for tcell in payload["oracle_daily"].values():
        tcell["day_universe"]["tp_days"] = []
        tcell["day_universe"]["fp_days"] = []
        tcell["day_universe"]["n_tp"] = 0
        tcell["day_universe"]["n_fp"] = 0

    line = json.dumps(dict(report.record_to_formal_dict(
        make_trade_path([1.0, 2.0], date="2020-01-02", engine="E1")),
        cost_scenario="Base"), sort_keys=True)
    name = "MC_HANDOFF_E1_Base.jsonl"
    files = {name: line}
    payload["mc_handoff_manifest"] = {
        "counts": payload["mc_handoff_manifest"]["counts"],
        "files": {"E1|Base": {
            "file": name, "n_records": 1,
            "sha256": hashlib.sha256(line.encode("utf-8")).hexdigest()}},
    }
    problems = report.validate_sealed_files(files, payload)
    assert any(p.startswith("sealed_file_extra_trade_dates:E1|Base:")
              and "2020-01-02" in p for p in problems)


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


# ===========================================================================
# M6.1.2-S3 — closing the "presence + type + self-reported boolean, never
# RE-DERIVED" defect class the adversarial audit found in the seal gate.
# Every mutation below is proven refused at the validator level AND at the
# real production renderer level (scripts/s0_real_run.py::render_s0_report,
# loaded read-only via `real_run_module()`), per `_assert_mutation_refused`
# / the item-2/item-8 analogues defined alongside their tests.
# ===========================================================================

# ---------------------------------------------------------------------------
# item 1 — STABILITY CONSERVATION RE-DERIVED, never merely read off the
# axis's own self-reported "conservation_ok" flag (stability.py slices ONE
# theta's D_TP series; sum(cell["n"]) over every REAL bucket of epochs/
# by_direction/vol_terciles(resolved)/by_year must equal that theta's
# day_universe["n_tp"], and leave_one_year_out must satisfy loyo[y]["n"] ==
# n_tp - by_year[y]["n"] for every year — see report.py's new docstring).
# ---------------------------------------------------------------------------
def _real_stability_bucket_key(axis: dict) -> str:
    """First non-bookkeeping (real) bucket key in a stability_views axis."""
    for k in axis:
        if k not in ("conservation_ok", "status", "reason"):
            return k
    raise AssertionError(f"axis has no real bucket: {axis}")


def test_stability_conservation_inflated_cell_n_is_flagged():
    """Mutation: inflated cell n — conservation_ok stays True (self-
    reported); only a RE-DERIVED sum catches this."""
    def _mutate(d):
        epochs = d["stability_views"][T0]["E1"]["Base"]["epochs"]
        bucket = _real_stability_bucket_key(epochs)
        epochs[bucket]["n"] += 1
    _assert_mutation_refused(
        _mutate,
        f"stability_views_conservation_recompute_mismatch:{T0}|E1|Base|"
        "epochs")


def test_stability_conservation_all_cells_zeroed_is_flagged():
    """Mutation: all cells n=0 (with a non-empty universe) — conservation_ok
    stays True."""
    def _mutate(d):
        by_dir = d["stability_views"][T0]["E1"]["Base"]["by_direction"]
        for k, v in by_dir.items():
            if k != "conservation_ok":
                v["n"] = 0
    _assert_mutation_refused(
        _mutate,
        f"stability_views_conservation_recompute_mismatch:{T0}|E1|Base|"
        "by_direction")


def test_stability_conservation_deleted_bucket_is_flagged():
    """Mutation: deleted bucket — by_year's own real bucket removed."""
    def _mutate(d):
        by_year = d["stability_views"][T0]["E1"]["Base"]["by_year"]
        bucket = _real_stability_bucket_key(by_year)
        del by_year[bucket]
    _assert_mutation_refused(
        _mutate,
        f"stability_views_conservation_recompute_mismatch:{T0}|E1|Base|"
        "by_year")


def test_stability_conservation_axis_reduced_to_flag_only_is_flagged():
    """Mutation: axis reduced to only the conservation_ok flag — refused
    even though the flag itself says True."""
    def _mutate(d):
        d["stability_views"][T0]["E1"]["Base"]["vol_terciles"] = {
            "conservation_ok": True}
    _assert_mutation_refused(
        _mutate,
        f"stability_views_conservation_recompute_mismatch:{T0}|E1|Base|"
        "vol_terciles")


def test_stability_loyo_recompute_mismatch_is_flagged():
    """leave_one_year_out is NOT a partition — its own re-derived identity
    (loyo[y]["n"] == n_tp - by_year[y]["n"]) is checked independently of the
    partitioning axes above."""
    def _mutate(d):
        loyo = d["stability_views"][T0]["E1"]["Base"]["leave_one_year_out"]
        year = _real_stability_bucket_key(loyo)
        loyo[year]["n"] += 1
    _assert_mutation_refused(
        _mutate, f"stability_views_loyo_recompute_mismatch:{T0}|E1|Base|")


# ---------------------------------------------------------------------------
# item 2 — SEALED-RECORD LEAF TYPES: validate_sealed_files previously
# checked the per-line field SET only; a numeric string ("20000.0", "1")
# now must be refused. Proven at both `validate_sealed_files` (a sealed
# JSONL line, via `_sealed_fixture()`) AND the real renderer (mutating the
# raw TradePathRecord BEFORE `record_to_formal_dict`/`json.dumps` — the
# exact path the real renderer always takes, so the corruption is
# introduced the way the real renderer would produce it, never by
# hand-editing a payload dict section).
# ---------------------------------------------------------------------------
def _assert_sealed_line_mutation_refused(mutate_line_fn, mutate_record_fn,
                                         expected_prefix: str) -> list[str]:
    files, payload = _sealed_fixture()
    name = "MC_HANDOFF_E1_Base.jsonl"
    lines = [json.loads(l) for l in files[name].splitlines()]
    mutate_line_fn(lines[0])
    _rewrite_sealed_file(files, payload, "E1", "Base", lines)
    problems = report.validate_sealed_files(files, payload)
    assert any(p.startswith(expected_prefix) for p in problems), problems

    result = _real_render_result()
    mutate_record_fn(result["records"]["E1"]["Base"][0])
    _assert_real_renderer_refuses(result)
    return problems


def test_sealed_file_line_numeric_string_entry_fill_is_flagged():
    _assert_sealed_line_mutation_refused(
        lambda line: line.__setitem__("entry_fill", "20000.0"),
        lambda rec: setattr(rec, "entry_fill", "20000.0"),
        "sealed_file_line_field_type_invalid:E1|Base:0:entry_fill")


def test_sealed_file_line_numeric_string_direction_is_flagged():
    _assert_sealed_line_mutation_refused(
        lambda line: line.__setitem__("direction", "1"),
        lambda rec: setattr(rec, "direction", "1"),
        "sealed_file_line_field_type_invalid:E1|Base:0:direction")


def test_sealed_file_line_direction_out_of_range_is_flagged():
    _assert_sealed_line_mutation_refused(
        lambda line: line.__setitem__("direction", 0),
        lambda rec: setattr(rec, "direction", 0),
        "sealed_file_line_field_type_invalid:E1|Base:0:direction")


def test_sealed_file_line_empty_mtm_list_is_flagged():
    _assert_sealed_line_mutation_refused(
        lambda line: line.__setitem__("mtm_close_pnl_1m", []),
        lambda rec: setattr(rec, "mtm_close_pnl_1m", []),
        "sealed_file_line_field_type_invalid:E1|Base:0:mtm_close_pnl_1m")


def test_sealed_file_line_bool_field_wrong_type_is_flagged():
    _assert_sealed_line_mutation_refused(
        lambda line: line.__setitem__("stop_triggered", "true"),
        lambda rec: setattr(rec, "stop_triggered", "true"),
        "sealed_file_line_field_type_invalid:E1|Base:0:stop_triggered")


# ---------------------------------------------------------------------------
# item 3 — THETA NESTING: D_TP(theta_0.5) must be a SUBSET of D_TP(theta_
# 0.3) over the SAME day population (frozen App A / S0 §7 L133 — raising
# theta can only shrink the continuation-event set). Mutation: swap one
# day's class between thetas (moved from theta_0.3's tp_days into its
# fp_days) while its OWN counts/disjointness stay self-consistent — only the
# CROSS-theta nesting property breaks.
# ---------------------------------------------------------------------------
def test_day_universe_theta_nesting_violation_is_flagged():
    def _mutate(day):
        du_hi = day["oracle_daily"][T1]["day_universe"]     # theta_0.5
        du_lo = day["oracle_daily"][T0]["day_universe"]      # theta_0.3
        victim = du_hi["tp_days"][0]
        du_lo["tp_days"] = [d for d in du_lo["tp_days"] if d != victim]
        du_lo["fp_days"] = du_lo["fp_days"] + [victim]
        du_lo["n_tp"] -= 1
        du_lo["n_fp"] += 1
    _assert_mutation_refused(_mutate, "day_universe_theta_nesting_violation")


# ---------------------------------------------------------------------------
# item 4 — A11 RECONCILIATION: disclosures.na_conservation.per_table_
# total_na[t] must equal the ACTUAL sum derivable from structural.na_table's
# per_field na counts, never merely be a well-typed non-negative int on its
# own.
# ---------------------------------------------------------------------------
def test_disclosures_na_conservation_total_mismatch_is_flagged():
    def _mutate(d):
        totals = d["disclosures"]["na_conservation"]["per_table_total_na"]
        totals["features"] = totals["features"] + 1
    _assert_mutation_refused(
        _mutate, "disclosures_na_conservation_total_mismatch:features")


# ---------------------------------------------------------------------------
# item 5 — SERIES-BLOCK SELF-CONSISTENCY for every series block (oracle_
# daily executable pooled/by-era, theoretical_oracle): set(series dates) is
# a subset of the theta's TP UNION FP; n == len(series); sum_usd/mean_usd
# match the ACTUAL pair values.
# ---------------------------------------------------------------------------
def test_oracle_daily_series_block_ghost_date_is_flagged():
    def _mutate(d):
        series = d["oracle_daily"][T0]["executable"]["E1"]["Base"]["pooled"][
            "daily_pnl_usd"]
        series.append(["1999-01-04", 1.0])
    _assert_mutation_refused(
        _mutate, f"series_block_ghost_date:{T0}|E1|Base|pooled:1999-01-04")


def test_oracle_daily_series_block_n_mismatch_is_flagged():
    def _mutate(d):
        block = d["oracle_daily"][T0]["executable"]["E1"]["Base"]["pooled"]
        block["n"] = block["n"] + 1
    _assert_mutation_refused(
        _mutate, f"series_block_n_mismatch:{T0}|E1|Base|pooled")


def test_oracle_daily_series_block_sum_usd_mismatch_is_flagged():
    def _mutate(d):
        block = d["oracle_daily"][T0]["executable"]["E1"]["Base"]["pooled"]
        block["sum_usd"] = block["sum_usd"] + 12345.0
    _assert_mutation_refused(
        _mutate, f"series_block_sum_usd_mismatch:{T0}|E1|Base|pooled")


def test_oracle_daily_series_block_mean_usd_mismatch_is_flagged():
    def _mutate(d):
        block = d["oracle_daily"][T0]["executable"]["E1"]["Base"]["pooled"]
        block["mean_usd"] = (block["mean_usd"] or 0.0) + 999.0
    _assert_mutation_refused(
        _mutate, f"series_block_mean_usd_mismatch:{T0}|E1|Base|pooled")


def test_theoretical_oracle_series_block_ghost_date_is_flagged():
    def _mutate(d):
        series = d["theoretical_oracle"][T0]["pooled"]["daily_usd"]
        series.append(["1999-01-04", 1.0])
    _assert_mutation_refused(
        _mutate,
        f"series_block_ghost_date:theoretical_oracle|{T0}|pooled:1999-01-04")


def test_theoretical_oracle_blanked_note_is_flagged():
    """M6.1.3 fix-round (blind-audit A52): the ECONOMIC-UPPER-BOUND-ONLY
    note is content — blanking it silently drops the frozen §7 caveat."""
    def _mutate(d):
        d["theoretical_oracle"][T0]["note"] = "   "
    _assert_mutation_refused(
        _mutate, f"theoretical_oracle_note_invalid:{T0}")


def test_na_conservation_flag_contradicting_evidence_is_flagged():
    """M6.1.3 fix-round (blind-audit A56): conservation_ok=True next to a
    non-empty unregistered_reasons is a self-contradiction, never a pass."""
    def _mutate(d):
        nac = d["disclosures"]["na_conservation"]
        nac["unregistered_reasons"] = ["F5_gap::mystery_reason"]
    _assert_mutation_refused(
        _mutate,
        "disclosures_na_conservation_contradiction:unregistered_reasons")


# ---------------------------------------------------------------------------
# item 6 — EMPTY-STUDY FLOOR + SIZING NON-EMPTINESS.
# ---------------------------------------------------------------------------
def test_day_universe_empty_universe_never_seals():
    """Mutation: zeroed universe — n_tp == n_fp == 0 with empty lists."""
    def _mutate(d):
        du = d["oracle_daily"][T0]["day_universe"]
        du["tp_days"] = []
        du["fp_days"] = []
        du["n_tp"] = 0
        du["n_fp"] = 0
    _assert_mutation_refused(_mutate, f"day_universe_empty_universe:{T0}")


def test_sizing_outputs_rows_emptied_is_flagged():
    """Mutation: emptied rows — study.py's real producer relation is ONE row
    per TP-day trade for that theta (len(rows[eng][scn]) == n_tp); an
    emptied list breaks that identity even though n_tp itself is untouched."""
    def _mutate(d):
        d["sizing_outputs"][T0]["rows"]["E1"]["Base"] = []
    _assert_mutation_refused(
        _mutate, f"sizing_outputs_rows_count_mismatch:{T0}|E1|Base")


# ---------------------------------------------------------------------------
# item 7 — INFEASIBLE GRID POINTS: when infeasible_by_sample is True,
# per_seed must be absent or empty (gridmix.py's `_grid_point` never
# populates one once a point is marked infeasible).
# ---------------------------------------------------------------------------
def test_feasibility_grid_infeasible_point_with_fabricated_per_seed_is_flagged():
    def _mutate(d):
        cell = d["feasibility_grid"]["cells"][f"{T0}|E1|Base"]
        pk = _feasible_point_key(cell)
        point = cell["grid"][pk]
        point["infeasible_by_sample"] = True
        fabricated = copy.deepcopy(point["per_seed"]["7"])
        point["per_seed"] = {"7": fabricated}
    _assert_mutation_refused(
        _mutate,
        f"feasibility_grid_infeasible_point_has_per_seed:{T0}|E1|Base:")


# ---------------------------------------------------------------------------
# item 8 — SEALED-FILE COMPLETENESS: mc_handoff_manifest["sealed_files"]
# (every written file except the self-excluded S0_REPORT.json) must
# reconcile against the ACTUAL `files` bytes.
# ---------------------------------------------------------------------------
def test_sealed_files_manifest_missing_key_is_flagged():
    files, payload = _sealed_fixture()
    del payload["mc_handoff_manifest"]["sealed_files"]
    problems = report.validate_sealed_files(files, payload)
    assert "sealed_files_manifest_missing" in problems


def test_sealed_files_manifest_sha256_mismatch_is_flagged():
    files, payload = _sealed_fixture()
    name = "MC_HANDOFF_E1_Base.jsonl"
    payload["mc_handoff_manifest"]["sealed_files"][name]["sha256"] = "f" * 64
    problems = report.validate_sealed_files(files, payload)
    assert any(p.startswith(f"sealed_files_manifest_sha256_mismatch:{name}")
              for p in problems)


def test_sealed_files_manifest_bytes_mismatch_is_flagged():
    files, payload = _sealed_fixture()
    name = "MC_HANDOFF_E1_Base.jsonl"
    payload["mc_handoff_manifest"]["sealed_files"][name]["bytes"] += 1
    problems = report.validate_sealed_files(files, payload)
    assert any(p.startswith(f"sealed_files_manifest_bytes_mismatch:{name}")
              for p in problems)


def test_sealed_files_manifest_entry_missing_file_is_flagged():
    files, payload = _sealed_fixture()
    payload["mc_handoff_manifest"]["sealed_files"]["GHOST.json"] = {
        "sha256": "a" * 64, "bytes": 1}
    problems = report.validate_sealed_files(files, payload)
    assert any(p.startswith(
        "sealed_files_manifest_entry_missing_file:GHOST.json")
              for p in problems)


def test_sealed_files_manifest_extra_planted_file_is_flagged():
    """An un-hashed / un-registered file sitting in `files` (never routed
    through the manifest at all) is refused — not just files the OLD
    8-key {engine}|{scenario} manifest already knew to look at."""
    files, payload = _sealed_fixture()
    files["PLANTED.json"] = "{}"
    problems = report.validate_sealed_files(files, payload)
    assert any(p.startswith("sealed_files_manifest_incomplete:")
              and "PLANTED.json" in p for p in problems)


def test_sealed_files_manifest_corruption_on_real_renderer_output_is_flagged():
    """The 'real renderer refuses' proof for item 8: `sealed_files` is
    COMPUTED BY the renderer from the exact bytes it seals (scripts/
    s0_real_run.py::render_s0_report), so it is self-consistent by
    construction and cannot be driven wrong through any caller-supplied
    INPUT — there is no payload mutation that reaches the renderer's own
    internal sealed_files computation. The faithful equivalent instead
    renders for REAL, then corrupts ONE entry of the manifest's
    `sealed_files` the renderer itself just computed (the same tampering an
    attacker would attempt on the sealed artifact), and confirms
    `validate_sealed_files` refuses it — using the REAL renderer's actual
    production output as the base, a strictly stronger anchor than the
    synthetic `_sealed_fixture()` alone."""
    result = _real_render_result()
    files = real_run_module().render_s0_report(
        result, expected_governance=result["governance"])
    payload = json.loads(files["S0_REPORT.json"])
    assert report.validate_sealed_files(files, payload) == []      # sanity

    name = next(iter(payload["mc_handoff_manifest"]["sealed_files"]))
    payload["mc_handoff_manifest"]["sealed_files"][name]["sha256"] = "f" * 64
    problems = report.validate_sealed_files(files, payload)
    assert any(p.startswith(f"sealed_files_manifest_sha256_mismatch:{name}")
              for p in problems)


# ===========================================================================
# NON-BLOCKING hardening (cheap): funnel monotonicity, era_axis duplicate
# rejection, bootstrap n_boot/block_len strict-int typing.
# ===========================================================================
def test_structural_funnel_counts_non_monotonic_is_flagged():
    def _mutate(d):
        fc = d["structural"]["funnel_counts"]
        fc["L2_regular_full_session_candidates"] = \
            fc["L1_observed_rth_days"] + 1
    _assert_mutation_refused(_mutate, "structural_funnel_counts_not_monotonic")


def test_era_axis_axes_duplicate_is_flagged():
    def _mutate(d):
        axes = d["era_axis"]["axes"]
        d["era_axis"]["axes"] = list(axes) + [axes[0]]
    _assert_mutation_refused(_mutate, "era_axis_axes_duplicate")


def test_bootstrap_ci_n_boot_float_type_is_flagged():
    def _mutate(d):
        key = next(iter(d["bootstrap_ci"]))
        d["bootstrap_ci"][key]["per_seed"]["7"]["n_boot"] = float(
            report.FROZEN_N_BOOT)
    _assert_mutation_refused(_mutate, "bootstrap_ci_n_boot:")


def test_bootstrap_ci_block_len_float_type_is_flagged():
    def _mutate(d):
        key = next(k for k in d["bootstrap_ci"] if k.endswith("block5"))
        d["bootstrap_ci"][key]["per_seed"]["7"]["block_len"] = 5.0
    _assert_mutation_refused(_mutate, "bootstrap_ci_block_len:")


# ===========================================================================
# M6.1.3-S1 mission item 1 — SCHEMA MATRIX: an UNKNOWN key inside any A1-A12
# section (or a well-known nested cell) must be refused, with the allowance
# ALWAYS a documented superset of the REAL producer shape (`_valid_payload`
# already IS that real shape for every producer-derived section, so adding
# one smuggled key on top of an otherwise-valid payload is a clean, isolated
# mutation — the positive baseline is already proven clean by
# `test_valid_payload_has_no_problems`).
# ===========================================================================
_GHOST_KEY = "__ghost_unknown_key__"


def _add_ghost_key(path):
    def _mutate(d):
        _get_path(d, path)[_GHOST_KEY] = "smuggled"
    return _mutate


_UNKNOWN_KEY_FAMILIES = [
    ("structural", ("structural",), "structural_unknown_key"),
    ("na_table", ("structural", "na_table"), "na_table_unknown_key"),
    ("label_anchor_row",
     ("structural", "label_anchor_availability", "y_cont"),
     "label_anchor_row_unknown_key"),
    ("day_universe", ("oracle_daily", T0, "day_universe"),
     "day_universe_unknown_key"),
    ("oracle_daily_cell", ("oracle_daily", T0),
     "oracle_daily_cell_unknown_key"),
    ("oracle_daily_executable_cell",
     ("oracle_daily", T0, "executable", "E1", "Base"),
     "oracle_daily_executable_unknown_key"),
    ("series_block",
     ("oracle_daily", T0, "executable", "E1", "Base", "pooled"),
     "series_block_unknown_key"),
    ("oracle_daily_worst_day_report",
     ("oracle_daily", T0, "executable", "E1", "Base", "worst_day_report"),
     "oracle_daily_worst_day_report_unknown_key"),
    ("theoretical_oracle_cell", ("theoretical_oracle", T0),
     "theoretical_oracle_unknown_key"),
    ("e2_worst_days_cell", ("e2_worst_days", T0, "Base"),
     "e2_worst_days_unknown_key"),
    ("sizing_outputs_cell", ("sizing_outputs", T0),
     "sizing_outputs_cell_unknown_key"),
    ("sizing_row", ("sizing_outputs", T0, "rows", "E1", "Base", 0),
     "sizing_outputs_row_unknown_key"),
    ("sizing_coverage", ("sizing_outputs", T0, "coverage", "E1", "Base"),
     "sizing_outputs_coverage_unknown_key"),
    ("sizing_coverage_budget_row",
     ("sizing_outputs", T0, "coverage", "E1", "Base", "by_budget_usd", "50"),
     "sizing_outputs_coverage_budget_unknown_key"),
    ("frequency_cell", ("frequency", T0), "frequency_cell_unknown_key"),
    ("frequency_pooled_leaf", ("frequency", T0, "pooled"),
     "frequency_leaf_cell_unknown_key"),
    ("frequency_by_era_leaf", ("frequency", T0, "by_era", ERA_PROXY),
     "frequency_leaf_cell_unknown_key"),
    ("stability_views_cell", ("stability_views", T0, "E1", "Base"),
     "stability_views_cell_unknown_key"),
    ("stability_views_cell_field",
     ("stability_views", T0, "E1", "Base", "epochs", "2010-2013"),
     "stability_views_cell_field_unknown_key"),
    ("bootstrap_ci_cell", ("bootstrap_ci", f"{T0}|E1|Base|block5"),
     "bootstrap_ci_cell_unknown_key"),
    ("feasibility_grid_cell",
     ("feasibility_grid", "cells", f"{T0}|E1|Base"),
     "feasibility_grid_cell_unknown_key"),
    ("era_axis", ("era_axis",), "era_axis_unknown_key"),
    ("disclosures", ("disclosures",), "disclosures_unknown_key"),
    ("na_conservation", ("disclosures", "na_conservation"),
     "na_conservation_unknown_key"),
    ("governance", ("governance",), "governance_unknown_key"),
    ("mc_handoff_manifest", ("mc_handoff_manifest",),
     "mc_handoff_manifest_unknown_key"),
    ("mc_handoff_counts_cell",
     ("mc_handoff_manifest", "counts", "E1", "Base"),
     "mc_handoff_manifest_counts_cell_unknown_key"),
]


@pytest.mark.parametrize("name,path,code", _UNKNOWN_KEY_FAMILIES,
                         ids=[n for n, _p, _c in _UNKNOWN_KEY_FAMILIES])
def test_unknown_key_family_is_refused(name, path, code):
    problems = _assert_mutation_refused(_add_ghost_key(path), f"{code}:")
    assert any(_GHOST_KEY in p for p in problems), (name, problems)


def test_top_level_unknown_section_is_flagged():
    """`split_envelope` filters the real renderer's input down to
    FORMAL_SECTIONS before it ever reaches `validate_formal_payload`, so an
    extra TOP-LEVEL key can never survive to be exercised through the real-
    renderer path — this is a validator-only proof, unlike every other
    unknown-key family above."""
    payload = _valid_payload()
    payload["ghost_section"] = {"x": 1}
    problems = _validate(payload)
    assert any(p.startswith("unknown_top_level_section:") for p in problems)


def test_bootstrap_ci_seed_entry_unknown_key_is_flagged():
    def _mutate(d):
        key = f"{T0}|E1|Base|block5"
        d["bootstrap_ci"][key]["per_seed"]["7"][_GHOST_KEY] = 1
    _assert_mutation_refused(_mutate, "bootstrap_ci_seed_entry_unknown_key:")


def test_feasibility_grid_point_unknown_key_is_flagged():
    def _mutate(d):
        cell = d["feasibility_grid"]["cells"][f"{T0}|E1|Base"]
        pk = _feasible_point_key(cell)
        cell["grid"][pk][_GHOST_KEY] = 1
    _assert_mutation_refused(_mutate, "feasibility_grid_point_unknown_key:")


def test_feasibility_grid_seed_entry_unknown_key_is_flagged():
    def _mutate(d):
        cell = d["feasibility_grid"]["cells"][f"{T0}|E1|Base"]
        pk = _feasible_point_key(cell)
        cell["grid"][pk]["per_seed"]["7"][_GHOST_KEY] = 1
    _assert_mutation_refused(
        _mutate, "feasibility_grid_seed_entry_unknown_key:")


# ===========================================================================
# mission item 3 — RECOMPUTE-NOT-TRUST extensions.
# ===========================================================================
def test_feasibility_grid_point_n_tp_target_mismatch_is_flagged():
    def _mutate(d):
        cell = d["feasibility_grid"]["cells"][f"{T0}|E1|Base"]
        pk = _feasible_point_key(cell)
        cell["grid"][pk]["n_tp_target"] += 1
    _assert_mutation_refused(
        _mutate, f"feasibility_grid_point_n_tp_target_mismatch:{T0}|E1|Base:")


def test_feasibility_grid_point_n_fp_target_mismatch_is_flagged():
    def _mutate(d):
        cell = d["feasibility_grid"]["cells"][f"{T0}|E1|Base"]
        pk = _feasible_point_key(cell)
        cell["grid"][pk]["n_fp_target"] += 1
    _assert_mutation_refused(
        _mutate, f"feasibility_grid_point_n_fp_target_mismatch:{T0}|E1|Base:")


def test_feasibility_grid_point_f_expected_mismatch_is_flagged():
    def _mutate(d):
        cell = d["feasibility_grid"]["cells"][f"{T0}|E1|Base"]
        pk = _feasible_point_key(cell)
        cell["grid"][pk]["F_expected"] += 1000.0
    _assert_mutation_refused(
        _mutate, f"feasibility_grid_point_f_expected_mismatch:{T0}|E1|Base:")


def test_feasibility_grid_point_target_precision_mismatch_is_flagged():
    def _mutate(d):
        cell = d["feasibility_grid"]["cells"][f"{T0}|E1|Base"]
        pk = _feasible_point_key(cell)
        cell["grid"][pk]["target_precision"] += 0.5
    _assert_mutation_refused(
        _mutate, f"feasibility_grid_point_target_mismatch:{T0}|E1|Base:")


def test_feasibility_grid_seed_realized_precision_mismatch_is_flagged():
    def _mutate(d):
        cell = d["feasibility_grid"]["cells"][f"{T0}|E1|Base"]
        pk = _feasible_point_key(cell)
        cell["grid"][pk]["per_seed"]["7"]["realized_precision"] = 0.123456
    _assert_mutation_refused(
        _mutate,
        f"feasibility_grid_seed_realized_precision_mismatch:{T0}|E1|Base:")


def test_feasibility_grid_seed_realized_recall_mismatch_is_flagged():
    def _mutate(d):
        cell = d["feasibility_grid"]["cells"][f"{T0}|E1|Base"]
        pk = _feasible_point_key(cell)
        cell["grid"][pk]["per_seed"]["7"]["realized_recall"] = 0.123456
    _assert_mutation_refused(
        _mutate,
        f"feasibility_grid_seed_realized_recall_mismatch:{T0}|E1|Base:")


def test_feasibility_grid_seed_n_tp_actual_mismatch_is_flagged():
    def _mutate(d):
        cell = d["feasibility_grid"]["cells"][f"{T0}|E1|Base"]
        pk = _feasible_point_key(cell)
        cell["grid"][pk]["per_seed"]["7"]["n_tp_actual"] += 1
    _assert_mutation_refused(
        _mutate, f"feasibility_grid_seed_n_tp_actual_mismatch:{T0}|E1|Base:")


def test_feasibility_grid_seed_f_expected_mismatch_is_flagged():
    def _mutate(d):
        cell = d["feasibility_grid"]["cells"][f"{T0}|E1|Base"]
        pk = _feasible_point_key(cell)
        cell["grid"][pk]["per_seed"]["7"]["F_expected"] += 1000.0
    _assert_mutation_refused(
        _mutate, f"feasibility_grid_seed_f_expected_mismatch:{T0}|E1|Base:")


def test_feasibility_grid_infeasible_point_reason_missing_is_flagged():
    """"infeasible schema exact with NO selections" (mission item 3): the
    ONE extra key an infeasible point carries over the base 7 must itself
    be present — flipping a feasible point to infeasible_by_sample=True
    with per_seed cleared but no `infeasible_reason` is a disclosure gap,
    not a passable shape (mirrors the existing "fabricated per_seed on an
    infeasible point" test's technique, the opposite direction)."""
    def _mutate(d):
        cell = d["feasibility_grid"]["cells"][f"{T0}|E1|Base"]
        pk = _feasible_point_key(cell)
        point = cell["grid"][pk]
        point["infeasible_by_sample"] = True
        point["per_seed"] = {}
    _assert_mutation_refused(
        _mutate,
        f"feasibility_grid_infeasible_point_reason_missing:{T0}|E1|Base:")


def test_percentile_p1_gt_p5_in_series_block_is_flagged():
    """mission item 5(c): P1 <= P5 is a numeric-ordering sanity invariant,
    independent of the (unapproved) percentile ESTIMATOR itself."""
    def _mutate(d):
        pooled = d["oracle_daily"][T0]["executable"]["E1"]["Base"]["pooled"]
        pooled["worst_day_pnl_percentiles"] = {"P1": 10.0, "P5": -5.0}
    _assert_mutation_refused(
        _mutate, f"percentile_p1_gt_p5:{T0}|E1|Base|pooled")


def test_percentile_p1_gt_p5_in_e2_worst_days_is_flagged():
    def _mutate(d):
        d["e2_worst_days"][T0]["Base"]["pooled"] = {"P1": 10.0, "P5": -5.0}
    _assert_mutation_refused(
        _mutate, f"percentile_p1_gt_p5:e2_worst_days|{T0}|Base|pooled")


def test_bootstrap_ci_mean_invalid_type_is_flagged():
    def _mutate(d):
        key = next(iter(d["bootstrap_ci"]))
        d["bootstrap_ci"][key]["per_seed"]["7"]["mean"] = "not-a-number"
    _assert_mutation_refused(_mutate, "bootstrap_ci_mean_invalid:")


def test_bootstrap_ci_mean_cross_seed_mismatch_is_flagged():
    """stats.py's "mean" is the SAMPLE mean of the underlying series,
    computed ONCE and copied VERBATIM into every seed's dict — three seeds
    resampling the SAME series can never disagree on it."""
    def _mutate(d):
        key = next(iter(d["bootstrap_ci"]))
        d["bootstrap_ci"][key]["per_seed"]["13"]["mean"] = 999.0
    _assert_mutation_refused(_mutate, "bootstrap_ci_mean_cross_seed_mismatch:")


def test_bootstrap_ci_quoted_mismatch_is_flagged():
    def _mutate(d):
        key = next(iter(d["bootstrap_ci"]))
        d["bootstrap_ci"][key]["quoted"] = {
            "mean": 999.0, "ci_lo": 0.0, "ci_hi": 1.0,
            "n_boot": report.FROZEN_N_BOOT, "block_len": 5}
    _assert_mutation_refused(_mutate, "bootstrap_ci_quoted_mismatch:")


# ===========================================================================
# mission item 5 — P1/P5 GOVERNANCE: estimator_status must exist and read
# EXACTLY "resolved" to seal; DR-M6-H pending -> the real producer's own
# "unresolved_DR-M6-H" fail-closes here, never a silent pass.
# ===========================================================================
def test_worst_day_estimator_status_missing_is_flagged():
    def _mutate(d):
        del d["e2_worst_days"][T0]["Base"]["estimator_status"]
    _assert_mutation_refused(
        _mutate, f"e2_worst_days_estimator_status_missing:{T0}|Base")


def test_worst_day_estimator_unresolved_is_flagged():
    """The REAL producer's DEFAULT posture, not a hypothetical: scripts/
    s0_real_run.py build_full_study_result emits exactly this string
    ("unresolved_DR-M6-H") whenever `config.methods.worst_day_estimator`
    is None — which it is by default (contracts.ResolvedS0Methods) until
    Aaron rules DR-M6-H. Sealing must fail-closed on it."""
    def _mutate(d):
        d["e2_worst_days"][T0]["Base"]["estimator_status"] = \
            "unresolved_DR-M6-H"
    problems = _assert_mutation_refused(
        _mutate, f"worst_day_estimator_unresolved:{T0}|Base:")
    assert (f"worst_day_estimator_unresolved:{T0}|Base:"
           "'unresolved_DR-M6-H'") in problems


# ===========================================================================
# mission item 6 — sealed_files self-exclusion: the ONLY allowed name is
# the module-internal frozen constant ("S0_REPORT.json",).
# ===========================================================================
def test_self_excluded_disallowed_name_is_flagged():
    files, payload = _sealed_fixture()
    payload["mc_handoff_manifest"]["self_excluded"] = [
        "S0_REPORT.json", "PLANTED.txt"]
    files["PLANTED.txt"] = "{}"
    problems = report.validate_sealed_files(files, payload)
    assert any(p.startswith("sealed_files_self_excluded_not_allowed:")
              and "PLANTED.txt" in p for p in problems)
    # the disallowed name buys NO bypass: PLANTED.txt still needs its own
    # sealed_files integrity entry, which it never got here.
    assert any(p.startswith("sealed_files_manifest_incomplete:")
              and "PLANTED.txt" in p for p in problems)


def test_self_excluded_wrong_type_is_flagged():
    files, payload = _sealed_fixture()
    payload["mc_handoff_manifest"]["self_excluded"] = "S0_REPORT.json"
    problems = report.validate_sealed_files(files, payload)
    assert "sealed_files_self_excluded_type" in problems


# ===========================================================================
# mission item 2 — NEVER-CRASH: validate_formal_payload / validate_sealed_
# files / reconcile_with_internal must degrade to a problem-string list on
# ANY malformed JSON-like tree, at EVERY level (None/str/list/int where a
# dict is expected) — never an AttributeError/KeyError/TypeError escaping.
# ===========================================================================
_MALFORMED_TREES = [
    None,
    "a bare string",
    123,
    12.5,
    True,
    [],
    ["a", "list", "not", "a", "dict"],
    {},
    {"structural": None},
    {"structural": "not a dict"},
    {"structural": []},
    {"structural": {"funnel_counts": None}},
    {"structural": {"funnel_counts": "x"}},
    {"structural": {"na_table": {"per_field": "x"}}},
    {"oracle_daily": None},
    {"oracle_daily": {"theta_0.5": None}},
    {"oracle_daily": {"theta_0.5": "x"}},
    {"oracle_daily": {"theta_0.5": {"day_universe": "x", "executable": []}}},
    {"oracle_daily": {"theta_0.5": {"day_universe": {"tp_days": "x",
                                                      "fp_days": None}}}},
    {"stability_views": {"theta_0.5": {"E1": {"Base": {"epochs": "x"}}}}},
    {"bootstrap_ci": {"k": None}},
    {"bootstrap_ci": {"k": {"per_seed": "x"}}},
    {"bootstrap_ci": {"k": {"per_seed": {"7": "x"}, "quoted_seed": 7}}},
    {"feasibility_grid": {"cells": {"k": {"grid": "x"}}}},
    {"feasibility_grid": {"cells": {"k": {"grid": {"q0.35_r0.20": "x"}}}}},
    {"feasibility_grid": {"cells": {"k": {
        "grid": {"q0.35_r0.20": {"per_seed": {"7": "x"}}}}}}},
    {"mc_handoff_manifest": {"counts": "x"}},
    {"mc_handoff_manifest": {"counts": {"E1": None}}},
    {"mc_handoff_manifest": {"self_excluded": "S0_REPORT.json"}},
    {"mc_handoff_manifest": {"sealed_files": "not a dict"}},
    {"disclosures": {"na_conservation": "x"}},
    {"governance": []},
    {"era_axis": {"axes": "x"}},
    {k: [1, 2, {"nested": {"deep": [None, "x", 1.0]}}]
     for k in report.FORMAL_SECTIONS},
]


@pytest.mark.parametrize(
    "tree", _MALFORMED_TREES,
    ids=[f"tree_{i}" for i in range(len(_MALFORMED_TREES))])
def test_validate_formal_payload_never_crashes(tree):
    problems = report.validate_formal_payload(copy.deepcopy(tree))
    assert isinstance(problems, list)
    assert all(isinstance(p, str) for p in problems)


@pytest.mark.parametrize(
    "tree", _MALFORMED_TREES,
    ids=[f"tree_{i}" for i in range(len(_MALFORMED_TREES))])
def test_validate_sealed_files_never_crashes(tree):
    problems = report.validate_sealed_files({"a.jsonl": "not json"},
                                            copy.deepcopy(tree))
    assert isinstance(problems, list)
    assert all(isinstance(p, str) for p in problems)


@pytest.mark.parametrize(
    "tree", _MALFORMED_TREES,
    ids=[f"tree_{i}" for i in range(len(_MALFORMED_TREES))])
def test_reconcile_with_internal_never_crashes(tree):
    problems = report.reconcile_with_internal(copy.deepcopy(tree),
                                              copy.deepcopy(tree))
    assert isinstance(problems, list)
    assert all(isinstance(p, str) for p in problems)


_RECONCILE_MALFORMED_TREES = [
    {"study": "not a dict"},
    {"study": {"per_theta": "not a dict"}},
    {"study": {"per_theta": {"theta_0.5": None}}},
    {"study": {"per_theta": {"theta_0.5": {"d_tp": "x"}}}},
    {"study": {"per_theta": {"theta_0.5": {"d_tp": {"E1": "x"}}}}},
    {"records": "not a dict"},
    {"records": {"E1": None}},
    {"records": {"E1": {"Base": "not a list"}}},
    {"reported_total_na": "not a dict"},
    {"reported_total_na": {"features.f1": "not an int"}},
    {"dataset": object()},
    {"dataset": "not an object"},
]


@pytest.mark.parametrize(
    "tree", _RECONCILE_MALFORMED_TREES,
    ids=[f"reconcile_tree_{i}" for i in range(len(_RECONCILE_MALFORMED_TREES))])
def test_reconcile_with_internal_malformed_internal_never_crashes(tree):
    problems = report.reconcile_with_internal(tree, _valid_payload())
    assert isinstance(problems, list)
    assert all(isinstance(p, str) for p in problems)


# ===========================================================================
# M6.1.3-S1 mission item 4 — reconcile_with_internal(internal, formal): the
# NEW pure function that cross-checks the FORMAL payload against the raw
# INTERNAL producer envelope (dataset/records/study — the dict scripts/
# s0_real_run.py::build_full_study_result actually returns, never split_
# envelope's own "internal" half, which drops "study").
# ===========================================================================
def _internal_envelope() -> dict:
    """The RAW internal producer envelope reconcile_with_internal expects,
    built from the SAME cached `_real_pieces()` ds/study that
    `_valid_payload()`'s formal side is derived from — so a FRESH
    (internal, formal) pair reconciles cleanly by construction (mission
    item 7's "prove the unmutated positive passes first" discipline)."""
    real = _real_pieces()
    ds, study = real["ds"], real["study"]
    reported_total_na = {
        f"{table}.{field}": row["na"]
        for table, fields in ds.na_table["per_field"].items()
        for field, row in fields.items()}
    return {"dataset": ds, "study": study, "records": study["records"],
           "reported_total_na": reported_total_na}


def test_reconcile_with_internal_valid_pair_has_no_problems():
    internal = _internal_envelope()
    formal = _valid_payload()
    assert _validate(formal) == []          # positive-first (mission item 7)
    assert report.reconcile_with_internal(internal, formal) == []


def test_reconcile_with_internal_rejects_non_dict_internal():
    assert report.reconcile_with_internal(["not", "a", "dict"], {}) == \
        ["internal_not_dict"]


def test_reconcile_with_internal_rejects_non_dict_formal():
    assert report.reconcile_with_internal({}, ["not", "a", "dict"]) == \
        ["formal_not_dict"]


def test_reconcile_with_internal_formal_as_internal_cannot_vacuously_succeed():
    """mission item 4: passing the FORMAL payload itself as `internal` must
    NEVER vacuously succeed — "study"/"records"/"reported_total_na"/
    "dataset" are never FORMAL_SECTIONS members, so all four are reported
    missing immediately."""
    formal = _valid_payload()
    problems = report.reconcile_with_internal(formal, formal)
    assert "reconcile_missing_internal_key:study" in problems
    assert "reconcile_missing_internal_key:records" in problems
    assert "reconcile_missing_internal_key:reported_total_na" in problems
    assert "reconcile_missing_internal_key:dataset" in problems


def test_reconcile_with_internal_missing_study_is_flagged():
    internal = _internal_envelope()
    del internal["study"]
    problems = report.reconcile_with_internal(internal, _valid_payload())
    assert "reconcile_missing_internal_key:study" in problems


def test_reconcile_with_internal_missing_records_is_flagged():
    internal = _internal_envelope()
    del internal["records"]
    problems = report.reconcile_with_internal(internal, _valid_payload())
    assert "reconcile_missing_internal_key:records" in problems


def test_reconcile_with_internal_missing_reported_total_na_is_flagged():
    internal = _internal_envelope()
    del internal["reported_total_na"]
    problems = report.reconcile_with_internal(internal, _valid_payload())
    assert "reconcile_missing_internal_key:reported_total_na" in problems


def test_reconcile_with_internal_missing_dataset_is_flagged():
    internal = _internal_envelope()
    del internal["dataset"]
    problems = report.reconcile_with_internal(internal, _valid_payload())
    assert "reconcile_missing_internal_key:dataset" in problems


def test_reconcile_dataset_records_malformed_is_flagged():
    internal = _internal_envelope()
    internal["dataset"] = types.SimpleNamespace(records=[object()])
    problems = report.reconcile_with_internal(internal, _valid_payload())
    assert "reconcile_dataset_records_malformed" in problems


def test_reconcile_oracle_series_value_mismatch_is_flagged():
    internal = _internal_envelope()
    formal = _valid_payload()
    series = formal["oracle_daily"][T0]["executable"]["E1"]["Base"]["pooled"][
        "daily_pnl_usd"]
    series[0] = [series[0][0], series[0][1] + 999.0]
    problems = report.reconcile_with_internal(internal, formal)
    assert any(p.startswith(
        f"reconcile_oracle_series_value_mismatch:oracle_daily|{T0}|E1|Base")
        for p in problems)


def test_reconcile_oracle_series_date_set_mismatch_is_flagged():
    internal = _internal_envelope()
    formal = _valid_payload()
    series = formal["oracle_daily"][T0]["executable"]["E1"]["Base"]["pooled"][
        "daily_pnl_usd"]
    series.pop()
    problems = report.reconcile_with_internal(internal, formal)
    assert any(p.startswith(
        "reconcile_oracle_series_date_set_mismatch:"
        f"oracle_daily|{T0}|E1|Base") for p in problems)


def test_reconcile_stability_value_mismatch_is_flagged():
    internal = _internal_envelope()
    formal = _valid_payload()
    epochs = formal["stability_views"][T0]["E1"]["Base"]["epochs"]
    epoch_label = next(k for k in epochs if k != "conservation_ok")
    epochs[epoch_label]["sum_usd"] = epochs[epoch_label]["sum_usd"] + 12345.0
    problems = report.reconcile_with_internal(internal, formal)
    assert any(p.startswith(
        "reconcile_stability_value_mismatch:"
        f"stability_views|{T0}|E1|Base|epochs|{epoch_label}.sum_usd")
        for p in problems)


def test_reconcile_stability_day_meta_missing_is_flagged():
    internal = _internal_envelope()
    victim_date = next(iter(
        internal["study"]["per_theta"][T0]["d_tp"]["E1"]["Base"]))
    ds = internal["dataset"]
    internal["dataset"] = types.SimpleNamespace(
        records=[r for r in ds.records if r.trade_date != victim_date])
    formal = _valid_payload()
    problems = report.reconcile_with_internal(internal, formal)
    assert any(p.startswith("reconcile_stability_day_meta_missing:")
              for p in problems)


def test_reconcile_record_count_mismatch_is_flagged():
    # NOTE: `_real_pieces()`/`_internal_envelope()`'s "records" is the
    # SHARED, session-cached `study["records"]` object (`_valid_payload()`
    # itself reads `len(study["records"][e][s])` to build mc_handoff_
    # manifest.counts) — mutating it IN PLACE would corrupt every other
    # test's baseline for the rest of the session. Build fresh per-engine/
    # scenario LIST copies (never touching the cached list objects
    # themselves) before appending the duplicate record, and capture
    # `formal` BEFORE constructing the mutated copy so its counts reflect
    # the untouched cache.
    formal = _valid_payload()
    internal = _internal_envelope()
    internal["records"] = {
        eng: {scn: list(recs) for scn, recs in by_scn.items()}
        for eng, by_scn in internal["records"].items()}
    internal["records"]["E1"]["Base"].append(
        internal["records"]["E1"]["Base"][0])
    problems = report.reconcile_with_internal(internal, formal)
    assert any(p.startswith("reconcile_record_count_mismatch:E1|Base:")
              for p in problems)


def test_reconcile_na_conservation_mismatch_is_flagged():
    internal = _internal_envelope()
    formal = _valid_payload()
    formal["disclosures"]["na_conservation"]["per_table_total_na"][
        "features"] += 1
    problems = report.reconcile_with_internal(internal, formal)
    assert any(p.startswith("reconcile_na_conservation_mismatch:features:")
              for p in problems)


def test_reconcile_na_conservation_missing_when_block_absent_is_flagged():
    internal = _internal_envelope()
    formal = _valid_payload()
    del formal["disclosures"]["na_conservation"]
    problems = report.reconcile_with_internal(internal, formal)
    assert "reconcile_na_conservation_missing" in problems


# ---------------------------------------------------------------------------
# mission item 7 — CROSS-FIELD synchronized tampering: a mutation that
# keeps the FORMAL payload internally self-consistent (validate_formal_
# payload sees no contradiction) by updating every dependent field
# together, so ONLY a comparison against the INTERNAL source of truth
# (reconcile_with_internal) can catch it. Proven positive-first (mission
# item 7): the unmutated payload passes validate_formal_payload BEFORE and
# AFTER the synchronized edit.
# ---------------------------------------------------------------------------
def test_reconcile_catches_cross_field_synchronized_value_tampering():
    internal = _internal_envelope()
    formal = _valid_payload()
    assert _validate(formal) == []          # positive-first

    delta = 4321.0
    for eng in ENGINES:
        for scn in SCENARIOS:
            exec_cell = formal["oracle_daily"][T0]["executable"][eng][scn]
            pooled = exec_cell["pooled"]
            victim_date = pooled["daily_pnl_usd"][0][0]
            for block in (pooled, *exec_cell["by_era"].values()):
                # the victim date belongs to exactly ONE era bucket (plus
                # pooled, which holds every date) — only touch sum_usd/
                # mean_usd for a block that ACTUALLY carries the date, so
                # an unrelated (possibly empty, n==0) era bucket is left
                # untouched rather than divided by zero.
                found = False
                for pair in block["daily_pnl_usd"]:
                    if pair[0] == victim_date:
                        pair[1] = pair[1] + delta
                        found = True
                if found:
                    block["sum_usd"] = block["sum_usd"] + delta
                    block["mean_usd"] = block["sum_usd"] / block["n"]

    # the FORMAL payload alone is still internally self-consistent (n/sum/
    # mean recomputed together, the tampered value stays inside the
    # payload's own claimed day population) — validate_formal_payload
    # cannot see this by construction.
    assert _validate(formal) == []

    # ...but reconcile_with_internal compares the payload's claim against
    # internal["study"]'s own d_tp series — the actual source of truth —
    # and sees the discrepancy immediately.
    problems = report.reconcile_with_internal(internal, formal)
    assert any(p.startswith(
        f"reconcile_oracle_series_value_mismatch:oracle_daily|{T0}|")
        for p in problems)
