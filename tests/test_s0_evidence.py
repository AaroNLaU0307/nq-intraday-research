"""Tests for itsf.s0.evidence — the atom-anchored half of the S0 seal
boundary (M6.1.4-S1, Codex-ordered RC-1 fix).

Hermetic and synthetic throughout: ONE small S0Dataset is built from
in-memory synthetic bars (tests/test_s0_context.py's generators — no real
archive, no clock, no researcher exposure) and driven through the REAL
production functions (`dataset.build_s0_dataset`, `study.build_study`,
`stability.build_stability_views`, `gridmix.build_grid`). The formal payload
and the eight MC_HANDOFF JSONL bodies are then assembled EXACTLY the way
`scripts/s0_real_run.py::build_full_study_result`/`render_s0_report` assemble
them (read-only reference; never imported — that script is main-agent owned).

The whole point of this module is that the fixture's evidence is captured
from the SAME atoms the producer saw, so:
  * every `reducers[...]` output must equal the real producer subtree
    BYTE-FOR-BYTE (this is what pins the two prose literals evidence.py has
    to duplicate, since study.py emits them as inline strings);
  * a clean payload must yield ZERO hard problems and a DETERMINISTIC
    PARTIAL marker list;
  * every counter-example below must be caught by an anchor the tamper
    could not also move.

`bootstrap_ci` cells are hand-assembled with the REAL series mean (a real
10,000-resample run per cell x 32 cells buys no extra fixture fidelity and
costs real compute); everything else is producer-derived.
"""
from __future__ import annotations

import copy
import json
import math
import random
from dataclasses import replace as dataclasses_replace
from collections.abc import Mapping

import numpy as np
import pytest
from test_s0_context import universe_of, weekdays

import itsf.contracts as C
from itsf.s0 import context as ctx_mod
from itsf.s0 import costs, evidence as ev
from itsf.s0 import gridmix as m_gridmix
from itsf.s0 import report as rep
from itsf.s0 import stability as m_stability
from itsf.s0 import stats as m_stats
from itsf.s0 import study as m_study
from itsf.s0.dataset import build_s0_dataset
from itsf.s0.stability import build_stability_views
from itsf.s0.study import ENGINES, StudyDayInput, build_study

SCENARIOS = ("Base", "Conservative", "Stress", "Severe")
BLOCKS = (5, 21)


# ===========================================================================
# fixture builders (producer-derived; cached for the session)
# ===========================================================================
_CACHE: dict = {}


def _fp_then_recover_closes(base: float) -> list[float]:
    """Morning rises (d_open=+1) then gives it all back — a D_FP day under
    both frozen thetas. Mirrors tests/test_s0_report.py's own market."""
    out = []
    for i in range(390):
        out.append(base + i * 1.0 if i < 30 else base + 29.0 - (i - 29) * 0.05)
    return out


def _make_day_inputs(ds, bars_by_date):
    """StudyDayInput per directional record day — mirrors (never imports)
    scripts/s0_real_run.py::make_day_inputs."""
    out: dict = {}
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


def _test_methods(**over) -> C.ResolvedS0Methods:
    """Fully-populated TEST_ONLY methods (mirrors tests/test_m6_chain.py's
    own `_test_methods`). Every value is an explicitly-marked synthetic
    stand-in, never a silently-adopted ruling."""
    base = dict(
        spread_cost=C.SpreadCostMethod(
            scalar_rule="TEST_ONLY", adverse_slippage_ticks={"Base": 1.0},
            adverse_semantics="replaces_per_side"),
        volatility_regime=C.VolatilityRegimeMethod(
            close_source="TEST_ONLY", return_basis="simple", ddof=1,
            roll_crossing_rule="TEST_ONLY", tercile_reference="TEST_ONLY",
            na_rule="vol_na"),
        fp_allocation=C.FpAllocationMethod(
            basis="A", weight_source="self_pool",
            shortfall_rule="proportional"),
        bootstrap_method=C.BootstrapMethod(
            population="TEST_ONLY", na_day_rule="TEST_ONLY", statistic="mean",
            n_boot_per_seed=True, quoted_seed_rule="first_seed",
            percentile_interpolation="linear", crn_scope="TEST_ONLY"),
        grid_policy=C.GridRepeatPolicy(
            k_per_seed=1, k_start_index=0, stream_includes_theta=False,
            convergence_rule="TEST_ONLY", max_doublings=0),
        event_na_mapping="five_stratum", stability_population="TEST_ONLY",
        worst_day_estimator="TEST_ONLY", test_only=True)
    base.update(over)
    return C.ResolvedS0Methods(**base)


def _test_config() -> C.StudyConfig:
    return C.derive_study_config(
        _test_methods(), spread_scalars=(0.5, 0.75, 0.9),
        regime_of=lambda d: "R",
        vol_axis_of=lambda d: ("T1", "T2", "T3")[int(d.replace("-", "")) % 3])


def _strkeys(obj):
    """Mirrors scripts/s0_real_run.py's own `_strkeys` (read-only
    reference): gridmix's per_seed dict is keyed by INT seeds and the formal
    boundary hard-rejects a non-str dict key."""
    if isinstance(obj, dict):
        return {str(k): _strkeys(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_strkeys(v) for v in obj]
    return obj


def _plain(obj):
    if isinstance(obj, Mapping):
        return {str(k): _plain(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_plain(v) for v in obj]
    return obj


_GOV = {
    "trial_id": "S0-T001",
    "authorized_commit": "a" * 40,
    "engineering_seed": 20260731,
    "frozen_hashes": {f"FILE_{i}.md": "c" * 64 for i in range(7)},
    "registry_sequence_snapshot": 5,
}


def _real_pieces() -> dict:
    """Build ONE synthetic dataset + study + views + grid via the REAL
    producers, and capture the evidence from the SAME atoms."""
    if "e" in _CACHE:
        return _CACHE
    dates = weekdays("2020-01-02", 46)
    spec = {d: {"closes": _fp_then_recover_closes(20000.0)}
            for i, d in enumerate(dates) if i >= 14 and i % 2 == 1}
    bars, uni = universe_of(dates, spec)
    ds = build_s0_dataset(bars, uni)
    scenarios = costs.build_scenarios(0.5, 0.75, 0.9)
    study = build_study(ds, _make_day_inputs(ds, bars), scenarios)
    cfg = _test_config()
    compute_result = {"records": study["records"], "study": study}
    evidence = ev.capture_evidence(ds, bars, compute_result, cfg,
                                   scenarios=scenarios, universe=uni)

    day_meta = {r.trade_date: {"year": r.year, "era": r.era,
                               "d_open": int(r.labels.d_open or 0)}
                for r in ds.records}
    vol_axis = {d: str(cfg.vol_axis_of(d)) for d in day_meta}
    stability_views = {t: build_stability_views(study["per_theta"][t],
                                                day_meta, vol_axis=vol_axis)
                       for t in study["per_theta"]}

    # A8 + A7 built from the SAME stratum vocabulary evidence captured, so
    # the fixture is internally consistent for the clean-payload assertion.
    event_of = {s.trade_date: s.event_stratum for s in evidence.day_strata}
    vol_of = {s.trade_date: s.volatility_regime_label
              for s in evidence.day_strata}
    feasibility: dict = {}
    bootstrap_ci: dict = {}
    # DR-4 (Aaron 2026-08-10): the published per-seed mean is the RULED
    # full-eligible-sequence statistic — zero-filled sat-out days add
    # nothing to the sum, NA days drop with a disclosed count — and the
    # cell carries the sequence accounting the reconciler cross-pins.
    n_eligible = len(ds.records)
    n_ruled = sum(1 for r in ds.records
                  if r.labels.y_cont is not None
                  and int(r.labels.d_open or 0) != 0)
    n_na_dropped = n_eligible - n_ruled
    for t, tblock in study["per_theta"].items():
        p = tblock["frequency"]["pooled"]["continuation_base_rate_p"]
        for eng in ENGINES:
            for scn in SCENARIOS:
                d_tp = tblock["d_tp"][eng][scn]
                d_fp = tblock["d_fp"][eng][scn]
                series = [d_tp[d] for d in sorted(d_tp)]
                mean = (float(sum(series)) / n_ruled) if n_ruled else 0.0
                for blk in BLOCKS:
                    bootstrap_ci[f"{t}|{eng}|{scn}|block{blk}"] = {
                        "per_seed": {
                            str(s): {"mean": mean, "ci_lo": mean - 1.0,
                                     "ci_hi": mean + 1.0, "n_boot": 10000,
                                     "block_len": blk}
                            for s in (7, 13, 31)},
                        "quoted_seed": 7,
                        "n_days_in_sequence": n_ruled,
                        "n_oracle_traded_days": len(series),
                        "n_na_days_dropped": n_na_dropped,
                        "convergence": {"max_abs_ci_lo_diff": 0.0,
                                        "max_abs_ci_hi_diff": 0.0}}
                strata = {d: (d[:4], vol_of[d], event_of[d])
                          for d in {**d_tp, **d_fp}}
                feasibility[f"{t}|{eng}|{scn}"] = m_gridmix.build_grid(
                    d_tp, d_fp, strata, p)

    reported_total_na = {
        f"{table}.{field}": int(row["na"])
        for table, fields in ds.na_table["per_field"].items()
        for field, row in fields.items()}

    _CACHE.update({"ds": ds, "bars": bars, "uni": uni, "study": study,
                   "cfg": cfg, "e": evidence, "scenarios": scenarios,
                   "stability_views": stability_views,
                   "feasibility": feasibility, "bootstrap_ci": bootstrap_ci,
                   "reported_total_na": reported_total_na})
    return _CACHE


def _formal_payload() -> dict:
    """A FRESH formal payload each call (deep-copied), assembled exactly as
    build_full_study_result assembles it."""
    r = _real_pieces()
    ds, study = r["ds"], r["study"]
    per_table = {"features": 0, "labels": 0}
    for col, n in r["reported_total_na"].items():
        table = col.split(".", 1)[0]
        if table in per_table:
            per_table[table] += n
    return copy.deepcopy({
        "structural": {
            "funnel_counts": _plain(dict(ds.funnel_counts)),
            "f10_counts": _plain(dict(ds.f10_counts)),
            "f10_raw_membership_counts":
                _plain(dict(ds.f10_raw_membership_counts)),
            "na_table": _plain(ds.na_table),
            "label_anchor_availability": _plain(ds.label_anchor_availability),
            "eras": {k: list(v) for k, v in ds.eras.items()},
            "groups": {g: {k: list(v) for k, v in m.items()}
                       for g, m in ds.groups.items()},
        },
        "oracle_daily": {
            t: {"day_universe": study["per_theta"][t]["day_universe"],
                "executable": study["per_theta"][t]["executable"]}
            for t in study["per_theta"]},
        "theoretical_oracle": {t: study["per_theta"][t]["theoretical_oracle"]
                               for t in study["per_theta"]},
        "e2_worst_days": {
            t: {scn: {**study["per_theta"][t]["executable"]["E2"][scn]
                      ["worst_day_report"],
                      "estimator_status": "resolved"}
                for scn in SCENARIOS}
            for t in study["per_theta"]},
        "sizing_outputs": {
            t: {"rows": study["per_theta"][t]["sizing_rows"],
                "coverage": study["per_theta"][t]["sizing_coverage"]}
            for t in study["per_theta"]},
        "frequency": {t: study["per_theta"][t]["frequency"]
                      for t in study["per_theta"]},
        "stability_views": r["stability_views"],
        "bootstrap_ci": r["bootstrap_ci"],
        "feasibility_grid": {"cells": _strkeys(r["feasibility"]),
                             "regions": {"status": "pending_mc"}},
        "mc_handoff_manifest": {"counts": {
            e: {s: {"n_records": len(study["records"][e][s])}
                for s in SCENARIOS} for e in ENGINES}},
        "era_axis": {"axes": list(ds.eras),
                     "counterfactual_disclosure": "counterfactual disclosure"},
        "disclosures": {
            "na_conservation": {"per_table_total_na": per_table,
                                "conservation_ok": True},
            "untradeable": study["untradeable_disclosure"],
            "pending_method_decisions": [],
            "methods_test_only": True,
            "method_conventions": {
                "quoted_seed_convention": "first frozen seed (7)",
                "stream_tags": "stats 9001 / gridmix 9002 (SeedSequence array "
                               "derivation, disclosed engineering convention)",
                "spread_scalars_used": list(r["cfg"].spread_scalars)}},
        "governance": copy.deepcopy(_GOV),
    })


def _sealed_files() -> dict:
    """The eight MC_HANDOFF bodies, serialized exactly as render_s0_report
    serializes them."""
    study = _real_pieces()["study"]
    out: dict = {}
    for eng in ENGINES:
        for scn in SCENARIOS:
            out[f"MC_HANDOFF_{eng}_{scn}.jsonl"] = "\n".join(
                json.dumps(rep.record_to_formal_dict(rec), sort_keys=True,
                           allow_nan=False)
                for rec in study["records"][eng][scn])
    return out


def _fixture():
    """(evidence, formal, files) — evidence is the SHARED frozen object (it
    is immutable by construction, which is exactly what the identity tests
    assert), formal/files are fresh mutable copies per test."""
    return _real_pieces()["e"], _formal_payload(), _sealed_files()


def _hard(evidence, formal, files) -> list[str]:
    return ev.split_problems(
        ev.reconcile_with_evidence(evidence, formal, files))[0]


def _rewrite(files, eng, scn, rows) -> None:
    files[f"MC_HANDOFF_{eng}_{scn}.jsonl"] = "\n".join(
        json.dumps(r, sort_keys=True, allow_nan=False) for r in rows)


def _rows_of(files, eng, scn) -> list[dict]:
    body = files[f"MC_HANDOFF_{eng}_{scn}.jsonl"]
    return [json.loads(line) for line in body.splitlines()]


# ===========================================================================
# A. capture — the 13 evidence objects
# ===========================================================================
def test_capture_populates_every_ev_object():
    e = _real_pieces()["e"]
    assert e.schema_version == ev.SCHEMA_VERSION
    for name in ("day_facts", "theoretical_paths", "opening_ranges",
                 "cost_scenarios", "day_strata", "grid_pools",
                 "bootstrap_inputs", "na_observations", "f10_memberships",
                 "label_availability"):
        assert len(getattr(e, name)) > 0, name
    assert isinstance(e.funnel, ev.FunnelFact)
    assert isinstance(e.estimator_identity, ev.EstimatorIdentityFact)
    assert isinstance(e.frozen_hash_observation, ev.FrozenHashObservationFact)
    for ev_id in [f"EV-{i}" for i in range(1, 14)]:
        assert ev_id in e.provenance, ev_id


def test_ev1_covers_every_structurally_eligible_day_not_just_traded():
    r = _real_pieces()
    e, ds = r["e"], r["ds"]
    assert {f.trade_date for f in e.day_facts} == {rec.trade_date
                                                   for rec in ds.records}
    n_constructible = sum(1 for f in e.day_facts if f.trade_constructible)
    assert 0 < n_constructible < len(e.day_facts)


def test_ev1_rederived_era_and_oracle_candidate_agree_with_the_producer():
    """EV-1 re-derives `era`/`oracle_candidate` instead of copying the
    DayRecord's claim, so this is a real cross-path agreement check."""
    for f in _real_pieces()["e"].day_facts:
        assert f.era == f.record_era
        assert f.year == f.record_year
        assert f.oracle_candidate == f.record_oracle_candidate


def test_ev2_present_for_every_theoretical_union_day_and_agrees_with_oracle():
    r = _real_pieces()
    e, study = r["e"], r["study"]
    union = set()
    for t in study["per_theta"]:
        union.update(study["per_theta"][t]["day_universe"]["tp_days"])
    assert {p.trade_date for p in e.theoretical_paths} == union
    assert e.provenance["EV-2_oracle_cross_check"] == "agrees"
    for p in e.theoretical_paths:
        assert p.scenario_name == m_study.BASE_SCENARIO_NAME
        assert p.direction in (1, -1)
        assert math.isfinite(p.pnl_per_contract)


def test_ev3_anchor_stop_is_the_opposite_opening_range_extreme():
    for o in _real_pieces()["e"].opening_ranges:
        want = o.or_low if o.d_open == 1 else o.or_high
        assert o.anchor_stop == want
        assert o.n_obs_bars > 0


def test_ev4_snapshots_the_four_scenario_objects_that_never_enter_the_payload():
    r = _real_pieces()
    snaps = {s.name: s for s in r["e"].cost_scenarios}
    assert set(snaps) == set(SCENARIOS)
    for name, scn in r["scenarios"].items():
        s = snaps[name]
        assert s.spread_points == scn.spread_points
        assert s.slippage_ticks_per_side == scn.slippage_ticks_per_side
        assert s.adverse_slippage_ticks == scn.adverse_slippage_ticks
        assert s.friction_multiplier == scn.friction_multiplier
        assert s.platform_fee_rt_usd == scn.platform_fee_rt_usd


def test_ev5_dr_gated_axes_keep_their_unresolved_labels():
    """Mandate: capture the evidence anyway with HONEST provenance —
    an UNRESOLVED axis label stays UNRESOLVED, and no vocabulary is
    invented for an unruled DR."""
    r = _real_pieces()

    class _PendingConfig:
        methods = C.ResolvedS0Methods()      # every field None == pending
        spread_scalars = (0.5, 0.75, 0.9)

        @staticmethod
        def vol_axis_of(_d):
            raise AssertionError("no approved vol axis exists while DR-2 pends")

    e = ev.capture_evidence(r["ds"], r["bars"],
                            {"records": r["study"]["records"]},
                            _PendingConfig(), scenarios=r["scenarios"])
    assert e.provenance["EV-5_dr2_status"] == ev.STATUS_UNRESOLVED
    assert e.provenance["EV-5_dr6_status"] == ev.STATUS_UNRESOLVED
    assert e.provenance["EV-4_dr1_status"] == ev.STATUS_UNRESOLVED
    assert {s.volatility_regime_label for s in e.day_strata} == {
        ev.UNRESOLVED_VOL}
    assert all(s.reduction_rule_id == ev.UNRESOLVED_SPREAD_RULE
               for s in e.cost_scenarios)
    # an event-NA day (if any) may never borrow the IR-12/18 vocabulary
    for s in e.day_strata:
        if s.event_na:
            assert s.event_stratum == ev.UNRESOLVED_EVENT_STRATUM
    # ... and the estimator status mirrors the (pending) config, never a
    # silent "resolved".
    assert e.estimator_identity.estimator_status_expected == \
        "unresolved_DR-M6-H"


def test_ev5_tp_fp_class_uses_only_the_frozen_three_value_vocabulary():
    e = _real_pieces()["e"]
    seen = {v for s in e.day_strata for v in s.tp_fp_class.values()}
    assert seen <= {ev.TP_CLASS, ev.FP_CLASS, ev.NON_TRADEABLE_CLASS}
    for s in e.day_strata:
        assert set(s.tp_fp_class) == set(e.theta_keys())
        # theta nesting: TP at 0.5 implies TP at 0.3
        if s.tp_fp_class["theta_0.5"] == ev.TP_CLASS:
            assert s.tp_fp_class["theta_0.3"] == ev.TP_CLASS


def test_ev6_pools_partition_the_tp_and_fp_populations_exactly():
    r = _real_pieces()
    e, study = r["e"], r["study"]
    for g in e.grid_pools:
        du = study["per_theta"][g.theta_key]["day_universe"]
        assert sorted(d for pool in g.tp_pools.values() for d in pool) == \
            sorted(du["tp_days"])
        assert sorted(d for pool in g.fp_pools.values() for d in pool) == \
            sorted(du["fp_days"])
        assert g.n_tp_available == du["n_tp"]
        assert g.grid_stream_tag == m_gridmix.GRID_STREAM_TAG


def test_ev7_digest_is_deterministic_and_series_sensitive():
    r = _real_pieces()
    e = r["e"]
    again = ev.capture_evidence(r["ds"], r["bars"],
                                {"records": r["study"]["records"]}, r["cfg"],
                                scenarios=r["scenarios"], universe=r["uni"])
    a = {f.cell_key: f.series_sha256 for f in e.bootstrap_inputs}
    b = {f.cell_key: f.series_sha256 for f in again.bootstrap_inputs}
    assert a == b and len(a) == 32
    # the digest must MOVE when the series does
    fact = e.bootstrap_inputs[0]
    assert fact.series_sha256 != ev._series_digest([("2020-01-02", 1.0)])
    assert fact.stats_stream_tag == m_stats.STATS_STREAM_TAG
    assert fact.block_stream_key == m_stats.block_stream_key(
        float(fact.block_len))


def test_ev8_is_a_structurally_different_na_observation():
    """CR-1: today FIVE 'independent' NA recomputes trace to one preimage."""
    obs = _real_pieces()["e"].na_observations
    assert obs
    for o in obs:
        assert o.table in ("features", "labels")
        assert "DayRecord" in o.observation_method_id
        assert o.n_null >= 0 and o.n_not_null >= 0


def test_ev11_dependency_booleans_reproduce_the_producer_availability_counts():
    """The strongest cross-path check in this module: EV-11 re-derives the
    five IR-23 dependency booleans from the BARS, while
    `dataset._label_anchor_availability` reads them off S0Universe.summaries.
    Their aggregate must agree."""
    r = _real_pieces()
    counts: dict = {}
    for fact in r["e"].label_availability:
        for label, ok in fact.available.items():
            row = counts.setdefault(label, {"available_days": 0,
                                            "unavailable_days": 0})
            row["available_days" if ok else "unavailable_days"] += 1
    assert counts == _plain(r["ds"].label_anchor_availability)


def test_ev12_binds_all_three_percentile_constants_cr5():
    e = _real_pieces()["e"]
    ident = e.estimator_identity
    assert ident.study_percentile_method == m_study.PERCENTILE_METHOD
    assert ident.stability_percentile_method == m_stability.PERCENTILE_METHOD
    assert ident.stats_percentile_method == m_stats.PERCENTILE_METHOD
    assert ident.all_three_agree is True


def test_ev13_absent_by_default_and_captured_when_supplied():
    r = _real_pieces()
    assert r["e"].frozen_hash_observation.provenance == ev.PROV_NOT_SUPPLIED
    e2 = ev.capture_evidence(r["ds"], r["bars"],
                             {"records": r["study"]["records"]}, r["cfg"],
                             scenarios=r["scenarios"],
                             frozen_hash_observations={"x.md": "d" * 64})
    assert e2.frozen_hash_observation.observed["x.md"] == "d" * 64


def test_ev9_ev10_degrade_honestly_without_a_universe():
    r = _real_pieces()
    e = ev.capture_evidence(r["ds"], r["bars"],
                            {"records": r["study"]["records"]}, r["cfg"],
                            scenarios=r["scenarios"])
    assert e.funnel.provenance == ev.PROV_NOT_SUPPLIED
    assert all(m.raw_provenance == ev.PROV_NOT_SUPPLIED
               for m in e.f10_memberships)
    markers = ev.split_problems(
        ev.reconcile_with_evidence(e, _formal_payload(), _sealed_files()))[1]
    assert any(m.startswith("PARTIAL:structural.funnel_counts:")
               for m in markers)
    # EV-10's raw multi-hot sets need the EventCalendar, so the f10 check
    # cannot run in full and the marker stays up (one marker now covers the
    # exclusive partition and the raw membership together).
    assert any(m.startswith("PARTIAL:structural.f10_counts:")
               for m in markers)


# ===========================================================================
# B. immutability + identity separation (mandate item 3)
# ===========================================================================
@pytest.mark.parametrize("name", [
    "CanonicalDayFact", "TheoreticalPathRecord", "OpeningRangeFact",
    "CostScenarioSnapshot", "DayStratumFact", "GridPoolFact",
    "BootstrapInputFact", "NAObservationFact", "FunnelFact",
    "F10MembershipFact", "LabelAvailabilityFact", "EstimatorIdentityFact",
    "FrozenHashObservationFact", "CanonicalS0Evidence"])
def test_every_evidence_dataclass_is_frozen(name):
    from dataclasses import FrozenInstanceError
    e = _real_pieces()["e"]
    obj = e if name == "CanonicalS0Evidence" else {
        "CanonicalDayFact": e.day_facts[0],
        "TheoreticalPathRecord": e.theoretical_paths[0],
        "OpeningRangeFact": e.opening_ranges[0],
        "CostScenarioSnapshot": e.cost_scenarios[0],
        "DayStratumFact": e.day_strata[0],
        "GridPoolFact": e.grid_pools[0],
        "BootstrapInputFact": e.bootstrap_inputs[0],
        "NAObservationFact": e.na_observations[0],
        "FunnelFact": e.funnel,
        "F10MembershipFact": e.f10_memberships[0],
        "LabelAvailabilityFact": e.label_availability[0],
        "EstimatorIdentityFact": e.estimator_identity,
        "FrozenHashObservationFact": e.frozen_hash_observation,
    }[name]
    field0 = type(obj).__dataclass_fields__
    with pytest.raises(FrozenInstanceError):
        setattr(obj, next(iter(field0)), None)


def _mutable_ids(obj, acc=None, seen=None):
    """Every id() of a MUTABLE container (dict / list / set) reachable in a
    tree. MappingProxyType and tuple are NOT dict/list instances, so a
    correctly deep-frozen evidence tree contributes none."""
    acc = set() if acc is None else acc
    seen = set() if seen is None else seen
    if id(obj) in seen:
        return acc
    seen.add(id(obj))
    if isinstance(obj, (dict, list, set)):
        acc.add(id(obj))
    if isinstance(obj, Mapping):
        for v in obj.values():
            _mutable_ids(v, acc, seen)
    elif isinstance(obj, (list, tuple, set, frozenset)):
        for v in obj:
            _mutable_ids(v, acc, seen)
    elif hasattr(obj, "__dataclass_fields__"):
        for f in type(obj).__dataclass_fields__:
            _mutable_ids(getattr(obj, f), acc, seen)
    return acc


def test_evidence_holds_no_mutable_container_at_all():
    """Deep-freeze: nothing reachable from CanonicalS0Evidence is a dict,
    list or set — so there is nothing a later mutation could reach."""
    assert _mutable_ids(_real_pieces()["e"]) == set()


def test_evidence_and_formal_payload_share_zero_mutable_identity():
    e, formal, files = _fixture()
    assert _mutable_ids(e) & _mutable_ids(formal) == set()
    assert _mutable_ids(e) & _mutable_ids(files) == set()


def test_to_plain_returns_fresh_containers_every_call():
    e = _real_pieces()["e"]
    a, b = ev.to_plain(e.record_pnl), ev.to_plain(e.record_pnl)
    assert a == b
    assert _mutable_ids(a) & _mutable_ids(b) == set()
    a["E1|Base"]["ZZZ"] = 1.0            # mutating the copy is inert
    assert "ZZZ" not in ev.to_plain(e.record_pnl)["E1|Base"]


def test_mutating_the_formal_tree_after_capture_cannot_change_what_reconcile_sees():
    """Mandate item 3's second half. The tamper below is applied to the
    SAME nested objects the compute tree handed the renderer; if evidence
    aliased any of them, the 'expected' side would move with the tamper and
    the mismatch would be invisible."""
    e, formal, files = _fixture()
    assert _hard(e, formal, files) == []
    tkey = e.theta_keys()[0]
    du = formal["oracle_daily"][tkey]["day_universe"]
    du["tp_days"].append("2099-12-31")     # in-place mutation, post-capture
    du["n_tp"] = du["n_tp"] + 1
    problems = _hard(e, formal, files)
    assert any(p.startswith("evidence_subtree_") or
               p.startswith("evidence_leaf_mismatch") for p in problems)
    # and the evidence itself is unchanged
    assert len(e.partition(0.5)[0]) + len(e.partition(0.5)[1]) > 0
    assert "2099-12-31" not in e.partition(0.5)[0]


# ===========================================================================
# C. reducers — byte/shape compatibility with the real producer
# ===========================================================================
def test_reducer_day_universe_equals_the_real_producer_subtree():
    r = _real_pieces()
    rebuilt = ev.reducers["oracle_daily.day_universe"](r["e"])
    for t, block in r["study"]["per_theta"].items():
        assert rebuilt[t] == block["day_universe"]


def test_reducer_frequency_equals_the_real_producer_subtree():
    r = _real_pieces()
    rebuilt = ev.reducers["frequency"](r["e"])
    for t, block in r["study"]["per_theta"].items():
        assert rebuilt[t] == block["frequency"]


def test_reducer_theoretical_oracle_equals_the_real_producer_subtree():
    r = _real_pieces()
    rebuilt = ev.reducers["theoretical_oracle"](r["e"])
    for t, block in r["study"]["per_theta"].items():
        assert rebuilt[t] == block["theoretical_oracle"]


def test_reducer_structural_subtrees_equal_the_real_dataset_attributes():
    r = _real_pieces()
    ds = r["ds"]
    assert ev.reducers["structural.eras"](r["e"]) == {
        k: list(v) for k, v in ds.eras.items()}
    assert ev.reducers["structural.groups"](r["e"]) == {
        g: {k: list(v) for k, v in m.items()} for g, m in ds.groups.items()}
    assert ev.reducers["era_axis.axes"](r["e"]) == list(ds.eras)


def test_reducer_outputs_still_seal_through_validate_formal_payload():
    """The shape contract: a payload whose reducer-owned subtrees came from
    EVIDENCE instead of from the compute tree must still pass every
    existing report.py rule (this is the wiring the main agent performs)."""
    e, formal, _files = _fixture()
    formal["oracle_daily"] = {
        t: {"day_universe": ev.reducers["oracle_daily.day_universe"](e)[t],
            "executable": formal["oracle_daily"][t]["executable"]}
        for t in formal["oracle_daily"]}
    formal["frequency"] = ev.reducers["frequency"](e)
    formal["theoretical_oracle"] = ev.reducers["theoretical_oracle"](e)
    formal["structural"]["eras"] = ev.reducers["structural.eras"](e)
    formal["structural"]["groups"] = ev.reducers["structural.groups"](e)
    formal["era_axis"]["axes"] = ev.reducers["era_axis.axes"](e)
    problems = rep.validate_formal_payload(
        formal, expected_governance=formal["governance"])
    assert problems == []
    assert rep.to_formal_json(formal)


def test_reducers_never_raise_on_a_hostile_evidence_stand_in():
    class _Fake:
        day_facts = ()
        thetas = ()
        eras = ()
        theoretical_paths = ()

        def partition(self, theta):
            return ((), ())

        def labelled_partition(self, theta):
            return ((), ())
    for name, fn in ev.reducers.items():
        fn(_Fake())              # must not raise


# ===========================================================================
# D. reconcile — the clean baseline
# ===========================================================================
def test_clean_payload_has_zero_hard_problems():
    e, formal, files = _fixture()
    assert _hard(e, formal, files) == []


def test_partial_markers_are_deterministic_sorted_and_prefixed():
    e, formal, files = _fixture()
    first = ev.reconcile_with_evidence(e, formal, files)
    second = ev.reconcile_with_evidence(e, formal, dict(files))
    assert first == second
    _hard_p, partial = ev.split_problems(first)
    assert partial == sorted(partial)
    assert partial and all(p.startswith(ev.PARTIAL_PREFIX) for p in partial)


def test_partial_markers_cover_every_matrix_s6_impossibility():
    """Matrix §S6 lists the three items engineering CANNOT close. Each must
    appear as an explicit PARTIAL, never as silent coverage."""
    e, formal, files = _fixture()
    partial = ev.split_problems(ev.reconcile_with_evidence(e, formal, files))[1]
    text = "\n".join(partial)
    assert "PARTIAL:stability_views:" in text and "DR-7" in text
    assert "PARTIAL:feasibility_grid.per_seed:" in text
    assert "PARTIAL:usd_layer:" in text and "DR-1" in text
    assert "PARTIAL:oracle_daily.worst_day_pnl_percentiles:" in text


def test_reconcile_rebuilds_d_tp_from_bytes_not_from_the_formal_day_universe():
    """Mandate item 5(b). Deleting the payload's OWN day lists must not
    weaken the record-population check: membership comes from EV-1."""
    e, formal, files = _fixture()
    for t in formal["oracle_daily"]:
        formal["oracle_daily"][t]["day_universe"]["tp_days"] = []
        formal["oracle_daily"][t]["day_universe"]["fp_days"] = []
    problems = _hard(e, formal, files)
    assert any(p.startswith("evidence_subtree_length:"
                            "oracle_daily.day_universe") or
               p.startswith("evidence_leaf_mismatch:oracle_daily.day_universe")
               for p in problems)
    # the record population is STILL measured against the full EV-1 universe
    assert not any(p.startswith("evidence_record_population_mismatch")
                   for p in problems)


# ===========================================================================
# E. counter-examples (PHASE D subset)
# ===========================================================================
def test_record_pnl_vs_formal_mismatch_is_caught_from_the_bytes():
    """The formal tree alone is tampered; the sealed BYTES still hold the
    truth, and the comparison is made against them."""
    e, formal, files = _fixture()
    tkey = e.theta_keys()[0]
    series = formal["oracle_daily"][tkey]["executable"]["E1"]["Base"][
        "pooled"]["daily_pnl_usd"]
    series[0][1] = float(series[0][1]) + 1234.5
    problems = _hard(e, formal, files)
    assert any(p.startswith("evidence_series_pair_mismatch:"
                            f"oracle_daily|{tkey}|E1|Base|pooled")
               for p in problems)


def test_formal_and_d_tp_synchronized_forgery_is_caught_via_evidence():
    """The RC-1 guise F1: the formal payload AND the producer aggregate
    `study[...]["d_tp"]` are moved TOGETHER. `reconcile_with_internal`
    anchors on that aggregate, so its oracle-series check is satisfied by
    the forgery; the evidence path anchors on the sealed BYTES and is not."""
    r = _real_pieces()
    e, formal, files = _fixture()
    tkey = e.theta_keys()[0]
    victim = formal["oracle_daily"][tkey]["executable"]["E1"]["Base"][
        "pooled"]["daily_pnl_usd"][0]
    date, bogus = victim[0], float(victim[1]) + 999.0
    victim[1] = bogus
    internal_study = copy.deepcopy(r["study"])
    internal_study["per_theta"][tkey]["d_tp"]["E1"]["Base"][date] = bogus
    internal = {"study": internal_study, "records": r["study"]["records"],
                "dataset": r["ds"],
                "reported_total_na": r["reported_total_na"]}
    internal_problems = rep.reconcile_with_internal(internal, formal)
    assert not any(p.startswith("reconcile_oracle_series_value_mismatch:"
                                f"oracle_daily|{tkey}|E1|Base")
                   for p in internal_problems)
    assert any(p.startswith("evidence_series_pair_mismatch")
               for p in _hard(e, formal, files))


def test_record_and_jsonl_synchronized_rewrite_is_caught_by_the_ev7_digest():
    """RC-1 guise B8/C4: the sealed BYTES and the formal tree are rewritten
    TOGETHER, so every payload-internal and bytes-vs-payload check agrees.
    EV-7's input-series digest and the line-internal P&L recompute were
    frozen BEFORE the rewrite and are not moved by it."""
    e, formal, files = _fixture()
    tkey = e.theta_keys()[0]
    rows = _rows_of(files, "E1", "Base")
    target = formal["oracle_daily"][tkey]["executable"]["E1"]["Base"][
        "pooled"]["daily_pnl_usd"][0]
    date = target[0]
    delta = 42.0
    for row in rows:
        if row["trade_date"] == date:
            row["final_pnl_per_contract"] = float(
                row["final_pnl_per_contract"]) + delta
    _rewrite(files, "E1", "Base", rows)
    target[1] = float(target[1]) + delta
    problems = _hard(e, formal, files)
    assert any(p.startswith("evidence_bootstrap_series_digest_mismatch")
               for p in problems)
    assert any(p.startswith("evidence_record_final_pnl_recompute")
               for p in problems)


def test_evidence_formal_shared_identity_violation_is_caught():
    """If a future wiring ever let the formal payload ALIAS an evidence
    container, this assertion fires — the guard is the identity walk, and
    the demonstration below shows what a violation looks like."""
    e, formal, _files = _fixture()
    assert _mutable_ids(e) & _mutable_ids(formal) == set()
    aliased = {"leaked": ev.to_plain(e.record_pnl)}
    aliased["also"] = aliased["leaked"]           # a genuine alias
    assert _mutable_ids(aliased) & _mutable_ids(aliased["leaked"]) != set()


def test_day_universe_forgery_of_an_extra_tp_day_is_caught():
    e, formal, files = _fixture()
    tkey = e.theta_keys()[0]
    du = formal["oracle_daily"][tkey]["day_universe"]
    du["tp_days"] = list(du["tp_days"]) + ["2020-02-28"]
    du["n_tp"] = du["n_tp"] + 1
    assert _hard(e, formal, files)


def test_cr2_bootstrap_mean_tamper_is_caught():
    """CR-2 — `oracle_daily...pooled.mean_usd` and `bootstrap_ci...per_seed.
    mean` are the same statistic over the same series by two different
    reducers, and are NEVER compared today."""
    e, formal, files = _fixture()
    key = sorted(formal["bootstrap_ci"])[0]
    for seed in ("7", "13", "31"):
        formal["bootstrap_ci"][key]["per_seed"][seed]["mean"] = 12345.0
    problems = _hard(e, formal, files)
    assert any(p.startswith("evidence_cr2_bootstrap_mean_vs_series")
               for p in problems)


def test_cr2_oracle_mean_tamper_is_caught():
    e, formal, files = _fixture()
    tkey = e.theta_keys()[0]
    formal["oracle_daily"][tkey]["executable"]["E1"]["Base"]["pooled"][
        "mean_usd"] = 999.0
    problems = _hard(e, formal, files)
    assert any(p.startswith("evidence_cr2_oracle_mean_vs_series")
               for p in problems)


def test_cr3_four_way_partition_size_identity_is_enforced():
    """CR-3 — four leaves, four reducers, ONE identity; only two of the six
    pairs are asserted anywhere today."""
    e, formal, files = _fixture()
    tkey = e.theta_keys()[0]
    formal["feasibility_grid"]["cells"][f"{tkey}|E1|Base"][
        "n_tp_available"] += 1
    formal["sizing_outputs"][tkey]["coverage"]["E2"]["Stress"][
        "n_trades"] += 1
    problems = _hard(e, formal, files)
    assert any(p.startswith("evidence_cr3_grid_n_tp_available")
               for p in problems)
    assert any(p.startswith("evidence_cr3_coverage_n_trades")
               for p in problems)


def test_cr6_three_e2_percentile_paths_must_agree():
    """CR-6 — the same two numbers live at THREE payload paths and
    validate_formal_payload checks P1<=P5 at each independently while never
    checking that they agree.

    IN PROCESS the three paths are the SAME dict object (build_full_study_
    result spreads `{**worst_day_report}`, a shallow copy, and
    `worst_day_report["pooled"]` is itself `block["pooled"]
    ["worst_day_pnl_percentiles"]`), which is exactly why the disagreement
    can only be introduced — and can only matter — at the SERIALIZED layer.
    Rebinding the key here is the byte-level tamper an editor of
    S0_REPORT.json would make."""
    e, formal, files = _fixture()
    tkey = e.theta_keys()[0]
    original = formal["e2_worst_days"][tkey]["Base"]["pooled"]
    formal["e2_worst_days"][tkey]["Base"]["pooled"] = {
        "P1": -99999.0, "P5": original["P5"]}
    problems = _hard(e, formal, files)
    assert any(p.startswith("evidence_cr6_e2_percentile_disagreement")
               for p in problems)


def test_cr9_stream_tag_prose_drift_is_caught():
    """CR-9 — `disclosures.method_conventions.stream_tags` is a HAND-WRITTEN
    duplicate of two module constants with no rebuild and no check."""
    e, formal, files = _fixture()
    formal["disclosures"]["method_conventions"]["stream_tags"] = (
        "stats 9001 / gridmix 8888")
    problems = _hard(e, formal, files)
    assert any(p == "evidence_cr9_stream_tag_prose_drift:gridmix:9002"
               for p in problems)


def test_cr12_minimum_1_contract_risk_identity_is_asserted():
    """CR-12 — two leaves, one value, identity never asserted today."""
    e, formal, files = _fixture()
    tkey = e.theta_keys()[0]
    row = formal["sizing_outputs"][tkey]["rows"]["E1"]["Base"][0]
    row["minimum_1_contract_risk"] = float(
        row["minimum_1_contract_risk"]) + 1.0
    problems = _hard(e, formal, files)
    assert any(p.startswith("evidence_cr12_minimum_risk_identity")
               for p in problems)


def test_e2_sizing_anchor_is_checked_against_ev3_not_the_payload():
    """E2 stores `planned_stop = None`, so the opening-range level reaches
    NO sealed artifact (matrix EV-3/L048). Only EV-3 can catch this."""
    e, formal, files = _fixture()
    tkey = e.theta_keys()[0]
    row = formal["sizing_outputs"][tkey]["rows"]["E2"]["Base"][0]
    row["stop_level_points"] = float(row["stop_level_points"]) + 5.0
    problems = _hard(e, formal, files)
    assert any(p.endswith(".stop_level_points") for p in problems)


def test_estimator_status_contradiction_is_caught():
    e, formal, files = _fixture()
    tkey = e.theta_keys()[0]
    formal["e2_worst_days"][tkey]["Base"]["estimator_status"] = "resolved_ish"
    assert any(p.startswith("evidence_estimator_status_mismatch")
               for p in _hard(e, formal, files))


def test_duplicate_record_line_is_caught():
    e, formal, files = _fixture()
    rows = _rows_of(files, "E1", "Base")
    _rewrite(files, "E1", "Base", rows + [rows[0]])
    assert any(p.startswith("evidence_duplicate_record")
               for p in _hard(e, formal, files))


def test_non_finite_leaf_on_a_sealed_line_is_caught():
    e, formal, files = _fixture()
    rows = _rows_of(files, "E1", "Base")
    body_rows = [dict(r) for r in rows]
    body_rows[0]["entry_fill"] = "20000.0"          # numeric STRING
    files["MC_HANDOFF_E1_Base.jsonl"] = "\n".join(
        json.dumps(r, sort_keys=True) for r in body_rows)
    assert any(p.startswith("evidence_line_nonfinite_or_illtyped")
               for p in _hard(e, formal, files))


def test_missing_sealed_file_is_caught():
    e, formal, files = _fixture()
    del files["MC_HANDOFF_E2_Severe.jsonl"]
    assert any(p == "evidence_sealed_file_missing:MC_HANDOFF_E2_Severe.jsonl"
               for p in _hard(e, formal, files))


def test_line_belonging_to_the_wrong_file_is_caught():
    e, formal, files = _fixture()
    rows = _rows_of(files, "E1", "Base")
    rows[0] = {**rows[0], "cost_scenario": "Severe"}
    _rewrite(files, "E1", "Base", rows)
    assert any(p.startswith("evidence_line_identity")
               for p in _hard(e, formal, files))


def test_manifest_count_is_measured_against_the_actual_parsed_lines():
    e, formal, files = _fixture()
    formal["mc_handoff_manifest"]["counts"]["E1"]["Base"]["n_records"] += 3
    assert any(p.startswith("evidence_manifest_count_mismatch:E1|Base")
               for p in _hard(e, formal, files))


def test_stability_bucket_tamper_is_caught_against_the_bytes():
    e, formal, files = _fixture()
    tkey = e.theta_keys()[0]
    cell = formal["stability_views"][tkey]["E1"]["Base"]["by_year"]
    year = next(k for k in cell if k != "conservation_ok")
    cell[year]["sum_usd"] = float(cell[year]["sum_usd"]) + 7.0
    assert any(p.startswith("evidence_stability_mismatch")
               for p in _hard(e, formal, files))


def test_frozen_hash_observation_catches_a_fabricated_governance_digest():
    r = _real_pieces()
    e = ev.capture_evidence(r["ds"], r["bars"],
                            {"records": r["study"]["records"]}, r["cfg"],
                            scenarios=r["scenarios"], universe=r["uni"],
                            frozen_hash_observations={"FILE_0.md": "e" * 64})
    formal, files = _formal_payload(), _sealed_files()
    assert any(p == "evidence_frozen_hash_mismatch:FILE_0.md"
               for p in _hard(e, formal, files))


# ===========================================================================
# F. reconcile_with_evidence must never raise (mandate item 7)
# ===========================================================================
class _EqBomb:
    """A dict KEY whose `__eq__` raises on any hash-bucket collision."""

    def __hash__(self):
        return hash("structural")

    def __eq__(self, other):
        raise RuntimeError("hostile __eq__")


class _PropertyBomb:
    """A value whose every attribute access raises."""

    def __getattr__(self, name):
        raise RuntimeError(f"hostile attribute {name}")

    def __repr__(self):
        raise RuntimeError("hostile __repr__")


_HOSTILE_PAYLOADS = [
    None, 0, "x", [], {}, {"structural": None},
    {"oracle_daily": {7: {}, "theta_0.5": {}}},
    {"structural": {True: 1, (1, 2): 2, 3: 3}},
    {"bootstrap_ci": {_EqBomb(): 1}},
    {"disclosures": _PropertyBomb()},
    {"governance": {"frozen_hashes": _PropertyBomb()}},
]


@pytest.mark.parametrize("payload", _HOSTILE_PAYLOADS)
def test_reconcile_with_evidence_never_raises(payload):
    e = _real_pieces()["e"]
    out = ev.reconcile_with_evidence(e, payload, payload)
    assert isinstance(out, list)
    assert all(isinstance(p, str) for p in out)


def test_reconcile_with_evidence_rejects_a_non_evidence_first_argument():
    assert ev.reconcile_with_evidence({"day_facts": []}, {}, {}) == [
        "evidence_not_canonical"]


def test_split_problems_never_raises_on_junk():
    assert ev.split_problems(None) == (["split_problems_input_not_iterable"],
                                       [])
    hard, partial = ev.split_problems([1, "PARTIAL:a:b", "z"])
    assert partial == ["PARTIAL:a:b"] and len(hard) == 2


def _random_json_tree(rng, depth=0):
    kinds = ["int", "float", "str", "bool", "none", "list", "dict"]
    if depth >= 3:
        kinds = kinds[:5]
    kind = rng.choice(kinds)
    if kind == "int":
        return rng.randint(-9, 9)
    if kind == "float":
        return rng.choice([1.5, -0.25, float("nan"), float("inf")])
    if kind == "str":
        return rng.choice(["", "x", "2020-01-02", "object at 0x7f"])
    if kind == "bool":
        return rng.choice([True, False])
    if kind == "none":
        return None
    if kind == "list":
        return [_random_json_tree(rng, depth + 1) for _ in range(rng.randint(0, 3))]
    keys = ["structural", "oracle_daily", "pooled", 7, True, (1, 2), "n_tp"]
    return {rng.choice(keys): _random_json_tree(rng, depth + 1)
            for _ in range(rng.randint(0, 4))}


@pytest.mark.parametrize("seed", range(25))
def test_fuzz_reconcile_with_evidence_never_raises(seed):
    rng = random.Random(seed)
    e = _real_pieces()["e"]
    out = ev.reconcile_with_evidence(e, _random_json_tree(rng),
                                     _random_json_tree(rng))
    assert isinstance(out, list) and all(isinstance(p, str) for p in out)


def test_capture_evidence_docstring_names_the_production_call_site():
    """The signature is shaped for exactly one call site; the module
    docstring must keep saying which, since the main agent wires it."""
    doc = ev.__doc__ or ""
    assert "build_full_study_result" in doc
    assert "capture_evidence(ds, bars_by_date, result, config)" in doc
    assert "reconcile_with_evidence(evd, formal, files)" in doc


# ===========================================================================
# H. PHASE D class 4 — grid DRAW CONTENTS are anchored (fix-round 1)
# ===========================================================================
def _first_draw(formal):
    cells = formal["feasibility_grid"]["cells"]
    for ckey in sorted(cells):
        cell = cells[ckey]
        for pkey in sorted(cell.get("grid", {})):
            point = cell["grid"][pkey]
            for skey in sorted(point.get("per_seed", {}), key=str):
                rowd = point["per_seed"][skey]
                if rowd.get("tp_dates"):
                    return ckey, rowd
    raise AssertionError("no drawn per-seed row in the fixture")


def test_grid_draw_checks_pass_on_the_honest_fixture():
    e, formal, files = _fixture()
    assert [p for p in _hard(e, formal, files)
            if p.startswith("evidence_grid_draw")] == []


def test_grid_draw_swapped_class_date_is_caught_despite_repaired_totals():
    """PHASE D class 4 variant 1: one drawn TP day replaced by an FP-class
    day, with counts, markers AND the mixture mean all repaired
    consistently — draw MEMBERSHIP against the EV-1 partition refuses it
    regardless of how coherent the totals look."""
    import numpy as np
    e, formal, files = _fixture()
    ckey, rowd = _first_draw(formal)
    tkey, eng, scn = ckey.split("|")
    du = formal["oracle_daily"][tkey]["day_universe"]
    swap_in = next(d for d in du["fp_days"]
                   if d not in rowd["tp_dates"]
                   and d not in rowd["fp_dates"])
    rowd["tp_dates"] = [swap_in] + list(rowd["tp_dates"][1:])
    rowd["day_markers"] = sorted(
        [[d, "tp"] for d in rowd["tp_dates"]]
        + [[d, "fp"] for d in rowd["fp_dates"]])
    rows = {r["trade_date"]: r for r in _rows_of(files, eng, scn)}
    drawn = list(rowd["tp_dates"]) + list(rowd["fp_dates"])
    rowd["mixture_mean_pnl"] = float(np.mean(
        [rows[d]["final_pnl_per_contract"] for d in drawn]))
    hard = _hard(e, formal, files)
    assert any(p.startswith("evidence_grid_draw_membership_tp:")
               for p in hard), hard


def test_grid_draw_out_of_universe_date_is_caught():
    """PHASE D class 4 variant 3: a date in NO S0 universe (1999-01-04)
    substituted into tp_dates sealed on both old candidates — now refused
    by membership AND by the missing sealed-byte P&L row."""
    e, formal, files = _fixture()
    ckey, rowd = _first_draw(formal)
    rowd["tp_dates"] = ["1999-01-04"] + list(rowd["tp_dates"][1:])
    rowd["day_markers"] = sorted(
        [[d, "tp"] for d in rowd["tp_dates"]]
        + [[d, "fp"] for d in rowd["fp_dates"]])
    hard = _hard(e, formal, files)
    assert any(p.startswith("evidence_grid_draw_membership_tp:")
               for p in hard), hard
    assert any(p.startswith("evidence_grid_draw_pnl_rows_missing:")
               for p in hard), hard


def test_grid_draw_marker_desync_is_caught():
    """CR-8: day_markers is the field MC actually consumes — it can no
    longer drift from tp_dates/fp_dates."""
    e, formal, files = _fixture()
    _, rowd = _first_draw(formal)
    marks = [list(m) for m in rowd["day_markers"]]
    for m in marks:
        if m[1] == "tp":
            m[1] = "fp"
            break
    rowd["day_markers"] = marks
    hard = _hard(e, formal, files)
    assert any(p.startswith("evidence_grid_draw_markers:")
               for p in hard), hard


def test_grid_draw_mixture_mean_tamper_is_caught():
    e, formal, files = _fixture()
    _, rowd = _first_draw(formal)
    rowd["mixture_mean_pnl"] = float(rowd["mixture_mean_pnl"]) + 1.0
    hard = _hard(e, formal, files)
    assert any(p.startswith("evidence_grid_draw_mixture_mean:")
               for p in hard), hard


# ===========================================================================
# G. PHASE-E blind-audit fix round 1 — counter-examples named after the
#    auditor's case ids. Each one SEALED before this round: the tamper was
#    applied and every existing check (payload-internal, bytes-vs-manifest,
#    reconcile_with_internal, and reconcile_with_evidence as it then stood)
#    still returned clean. Every test proves BOTH halves: the honest fixture
#    stays at zero hard problems, and the tampered one is refused.
# ===========================================================================
def _hard_codes(problems) -> set:
    return {p.split(":", 1)[0] for p in problems}


def test_honest_fixture_is_still_clean_after_the_fix_round():
    """Positive-first: none of the new invariants fires on real output."""
    e, formal, files = _fixture()
    assert _hard(e, formal, files) == []


# --- HIGH-1: the record_fields field-for-field binding ---------------------
def test_c32_pnl_preserving_fill_shift_is_refused():
    """C32 — entry_fill and exit_fill shifted by the SAME +3.25 (so
    final_pnl is unchanged), sizing_anchor_usd repaired to the new entry,
    and the A5 rows repaired to match. Every P&L-derived aggregate still
    reconciles; only the field-for-field binding to `record_fields` sees
    it."""
    e, formal, files = _fixture()
    shift = 3.25
    rows = _rows_of(files, "E1", "Base")
    victim = rows[0]["trade_date"]
    for row in rows:
        if row["trade_date"] != victim:
            continue
        row["entry_fill"] = float(row["entry_fill"]) + shift
        row["exit_fill"] = float(row["exit_fill"]) + shift
        row["sizing_anchor_usd"] = float(row["sizing_anchor_usd"]) + \
            shift * 2.0
    _rewrite(files, "E1", "Base", rows)
    tkey = e.theta_keys()[0]
    for t in formal["sizing_outputs"]:
        for r in formal["sizing_outputs"][t]["rows"]["E1"]["Base"]:
            if r["trade_date"] == victim:
                r["risk_usd_per_1_MNQ_planned"] = \
                    float(r["risk_usd_per_1_MNQ_planned"]) + shift * 2.0
                r["minimum_1_contract_risk"] = \
                    r["risk_usd_per_1_MNQ_planned"]
    problems = _hard(e, formal, files)
    assert any(p.startswith(
        "evidence_record_fields_mismatch:MC_HANDOFF_E1_Base.jsonl:"
        f"{victim}:entry_fill") for p in problems)
    assert any(p.startswith("evidence_record_fields_mismatch")
               and p.endswith(":exit_fill") for p in problems)
    del tkey


def test_c1_fp_day_exit_and_pnl_rewrite_across_all_files_is_refused():
    """C1 — an FP-day rewrite of exit_fill + final_pnl_per_contract across
    ALL EIGHT JSONL, with the grid mixture repaired. FP days sit OUTSIDE the
    TP-only EV-7 digest support, so the bootstrap digest cannot see them."""
    e, formal, files = _fixture()
    tkey = e.theta_keys()[0]
    fp_days = e.partition(float(tkey.split("_")[1]))[1]
    assert fp_days, "fixture must carry at least one FP day"
    victim = fp_days[0]
    for eng in ENGINES:
        for scn in SCENARIOS:
            rows = _rows_of(files, eng, scn)
            for row in rows:
                if row["trade_date"] == victim:
                    row["exit_fill"] = float(row["exit_fill"]) + 10.0
                    row["final_pnl_per_contract"] = float(
                        row["final_pnl_per_contract"]) + 20.0
            _rewrite(files, eng, scn, rows)
    problems = _hard(e, formal, files)
    assert any(p.startswith("evidence_record_fields_mismatch")
               and victim in p for p in problems)
    # the EV-7 digest is TP-only and therefore silent here — stated so the
    # test documents WHY the field binding is the load-bearing invariant.
    assert not any(p.startswith("evidence_bootstrap_series_digest_mismatch")
                   for p in problems)


def test_c7_mtm_array_rewrite_with_repaired_extremes_is_refused():
    """C7 — both mark arrays rewritten, `max_adverse_pnl = min(...)`
    repaired so the line-internal recompute passes, `max_favourable_pnl`
    set to 12345."""
    e, formal, files = _fixture()
    rows = _rows_of(files, "E2", "Stress")
    victim = rows[0]["trade_date"]
    for row in rows:
        if row["trade_date"] != victim:
            continue
        row["mtm_close_pnl_1m"] = [1.0] * len(row["mtm_close_pnl_1m"])
        row["mtm_adverse_pnl_1m"] = [-2.0] * len(row["mtm_adverse_pnl_1m"])
        row["max_adverse_pnl"] = -2.0          # repaired to min(...)
        row["max_favourable_pnl"] = 12345.0
    _rewrite(files, "E2", "Stress", rows)
    problems = _hard(e, formal, files)
    assert any(p.startswith("evidence_record_fields_mismatch")
               and p.endswith(":mtm_close_pnl_1m") for p in problems)
    assert any(p.startswith("evidence_record_fields_mismatch")
               and p.endswith(":max_favourable_pnl") for p in problems)


def test_c8_exit_timestamp_before_entry_timestamp_is_refused():
    """C8 — the frozen §3 entry/exit-time invariant is never asserted on a
    sealed line (matrix L130)."""
    e, formal, files = _fixture()
    rows = _rows_of(files, "E1", "Severe")
    victim = rows[0]["trade_date"]
    rows[0]["exit_timestamp"] = "1999-01-01T00:00:00-05:00"
    _rewrite(files, "E1", "Severe", rows)
    problems = _hard(e, formal, files)
    assert any(p.startswith(
        f"evidence_record_timestamp_order:MC_HANDOFF_E1_Severe.jsonl:{victim}")
        for p in problems)


@pytest.mark.parametrize("value", [1e308, -0.0, 5e-324, float(10 ** 16 + 1)])
def test_c29_absurd_but_finite_max_favourable_is_refused(value):
    """C29 — `math.isfinite` is not a range check: 1e308, -0.0, 5e-324 and
    10**16+1 all sealed as `max_favourable_pnl`."""
    e, formal, files = _fixture()
    rows = _rows_of(files, "E1", "Base")
    rows[0]["max_favourable_pnl"] = value
    _rewrite(files, "E1", "Base", rows)
    problems = _hard(e, formal, files)
    assert any(p.startswith("evidence_record_fields_mismatch")
               or p.startswith("evidence_record_value_out_of_range")
               or p.startswith(
                   "evidence_record_max_favourable_below_close_path")
               for p in problems)


def test_entry_fill_is_anchored_to_ev2_bar_reference_on_tp_days():
    """The ONE fill with a captured bar preimage. Stated narrowly: TP days
    only (EV-2's support), entry side only."""
    e, formal, files = _fixture()
    tkey = e.theta_keys()[0]
    tp_days = e.partition(float(tkey.split("_")[1]))[0]
    victim = tp_days[0]
    # tamper the row AND the capture-side twin, so the field binding is
    # satisfied and ONLY the bar anchor can object.
    rows = _rows_of(files, "E1", "Base")
    for row in rows:
        if row["trade_date"] == victim:
            row["entry_fill"] = float(row["entry_fill"]) + 1.0
    _rewrite(files, "E1", "Base", rows)
    problems = _hard(e, formal, files)
    assert any(p.startswith("evidence_record_entry_fill_vs_ev2:"
                            f"MC_HANDOFF_E1_Base.jsonl:{victim}")
               for p in problems)
    del formal


def test_records_executable_fills_partial_marker_is_permanent():
    """HIGH-1's honest residue: the bar preimage under exit fills is NOT
    closed and must be disclosed on EVERY reconcile, clean or not."""
    e, formal, files = _fixture()
    markers = ev.split_problems(
        ev.reconcile_with_evidence(e, formal, files))[1]
    hit = [m for m in markers
           if m.startswith("PARTIAL:records.executable_fills:")]
    assert len(hit) == 1
    assert "BAR DATA" in hit[0] and "EXIT fills" in hit[0]


# --- HIGH-2: the five never-consumed EV objects ---------------------------
def test_c20_funnel_counts_fabrication_is_refused():
    """C20 — `funnel_counts` + 500 sealed silently AND undisclosed once a
    universe was supplied, because EV-9 was captured and never read."""
    e, formal, files = _fixture()
    formal["structural"]["funnel_counts"]["L0_scheduled_trading_days"] += 500
    problems = _hard(e, formal, files)
    assert any(p.startswith(
        "evidence_funnel_count_mismatch:L0_scheduled_trading_days")
        for p in problems)


def test_c21_f10_raw_membership_fabrication_is_refused():
    """C21 — `f10_raw_membership_counts` + 77. Matrix L003 has NO verifier
    of any kind in the tree today."""
    e, formal, files = _fixture()
    formal["structural"]["f10_raw_membership_counts"]["none"] += 77
    problems = _hard(e, formal, files)
    assert any(p.startswith("evidence_f10_raw_membership_mismatch:none")
               for p in problems)


def test_c21b_f10_exclusive_partition_fabrication_is_refused():
    e, formal, files = _fixture()
    formal["structural"]["f10_counts"]["CPI"] += 3
    assert any(p.startswith("evidence_f10_count_mismatch:CPI")
               for p in _hard(e, formal, files))


def test_c22_na_table_and_na_conservation_moved_together_are_refused():
    """C22 — the whole point of CR-1: `structural.na_table` and
    `disclosures.na_conservation` both descend from ONE preimage, so moving
    them together satisfies VF-8, VF-11(d) and VF-13 at once. EV-8's null
    scan is a different code path and does not move with them."""
    e, formal, files = _fixture()
    per_field = formal["structural"]["na_table"]["per_field"]
    table, field = "features", sorted(per_field["features"])[0]
    row = per_field[table][field]
    row["na"] = int(row["na"]) + 9
    row["not_na"] = int(row["not_na"]) - 9
    formal["disclosures"]["na_conservation"]["per_table_total_na"][
        "features"] += 9
    problems = _hard(e, formal, files)
    assert any(p.startswith(f"evidence_na_count_mismatch:{table}.{field}.na")
               for p in problems)
    assert any(p.startswith(
        "evidence_na_conservation_vs_second_observation:features")
        for p in problems)


def test_c23_label_anchor_availability_fabrication_is_refused():
    """C23 — `label_anchor_availability` + 13 (matrix L012)."""
    e, formal, files = _fixture()
    formal["structural"]["label_anchor_availability"]["y_cont"][
        "available_days"] += 13
    assert any(p.startswith("evidence_label_anchor_mismatch:y_cont")
               for p in _hard(e, formal, files))


def test_c27_duck_typed_universe_no_longer_earns_a_dropped_marker():
    """C27 — any object exposing `.funnel`/`.events` used to earn the
    atom_S0Universe provenance and DROP the PARTIAL markers with nothing
    verified. Markers are now gated on a CHECK having run."""
    r = _real_pieces()

    class _DuckFunnel:
        scheduled = observed_rth = regular = ()
        structurally_eligible = final_dates = complete_390 = ()
        exclusion_reason = {}

    class _DuckEvents:
        @staticmethod
        def categories(_d):
            return ()

        @staticmethod
        def encode_f10(_d):
            return "none"

    class _DuckUniverse:
        funnel = _DuckFunnel()
        events = _DuckEvents()

    e = ev.capture_evidence(r["ds"], r["bars"],
                            {"records": r["study"]["records"]}, r["cfg"],
                            scenarios=r["scenarios"], universe=_DuckUniverse())
    problems = ev.reconcile_with_evidence(e, _formal_payload(),
                                          _sealed_files())
    hard, markers = ev.split_problems(problems)
    # the duck funnel claims every level is empty -> the comparison RUNS and
    # REFUSES, rather than quietly dropping the marker.
    assert any(p.startswith("evidence_funnel_count_mismatch") for p in hard)
    del markers


def test_high2_marker_is_gated_on_the_check_not_on_provenance():
    """The invariant itself: strip the payload section a check needs and the
    marker must COME BACK, even though capture provenance is unchanged."""
    e, formal, files = _fixture()
    clean = ev.split_problems(ev.reconcile_with_evidence(e, formal, files))[1]
    assert not any(
        m.startswith("PARTIAL:structural.label_anchor_availability:")
        for m in clean)
    del formal["structural"]["label_anchor_availability"]
    markers = ev.split_problems(
        ev.reconcile_with_evidence(e, formal, files))[1]
    assert any(m.startswith("PARTIAL:structural.label_anchor_availability")
               for m in markers)


# NOTE (M6.1.4-ARCH): the former `test_dead_evidence_tripwire_every_field_
# is_consumed` lived here. It is not deleted — it is RENAMED to
# `test_every_field_name_appears_in_a_consumer_function_source` (section J)
# so that it can never again be cited as evidence of consumption: it passed
# unchanged on the implementation the reviewer broke, because a field NAME
# appearing inside a consumer function says nothing about whether the
# consumption compared anything. `schema_version` is no longer exempted
# there, because it is now a bound identity check rather than free metadata.


# --- MEDIUM ---------------------------------------------------------------
def test_c5_zeroed_coverage_by_budget_is_refused():
    """C5 — `coverage.by_budget_usd` is fully AF2-derivable (count of
    sizing_anchor_usd <= budget) and had no verifier, so zeroing sealed."""
    e, formal, files = _fixture()
    tkey = e.theta_keys()[0]
    cov = formal["sizing_outputs"][tkey]["coverage"]["E1"]["Base"][
        "by_budget_usd"]
    for budget in cov:
        cov[budget]["n_covered"] = 0
        cov[budget]["fraction"] = 0.0
    problems = _hard(e, formal, files)
    assert any(p.startswith("evidence_coverage_n_covered_mismatch")
               for p in problems)


def test_c6_fabricated_untradeable_row_is_refused():
    """C6 — `disclosures.untradeable` rows were never validated at all
    (matrix L119: no shape, count or vocabulary check whatsoever)."""
    e, formal, files = _fixture()
    formal["disclosures"]["untradeable"] = [
        {"trade_date": "2020-02-14", "year": "2020", "era": "x",
         "d_open": 1, "y_cont": 0.9, "reason": "invented"}]
    problems = _hard(e, formal, files)
    assert any(p.startswith("evidence_untradeable_row_fabricated")
               for p in problems)


def test_c6_untradeable_non_list_keeps_the_marker_up():
    e, formal, files = _fixture()
    formal["disclosures"]["untradeable"] = {"note": "n/a"}
    hard, markers = ev.split_problems(
        ev.reconcile_with_evidence(e, formal, files))
    assert "evidence_untradeable_not_a_list" in hard
    assert any(m.startswith("PARTIAL:disclosures.untradeable:")
               for m in markers)


# --- LOW ------------------------------------------------------------------
def test_c12b_reduced_scenario_axis_is_refused_at_capture():
    """C12b — a narrowed `scenarios` map silently shrank `evidence.scenarios`
    and `_parse_sealed_rows` then SKIPPED the files outside it."""
    r = _real_pieces()
    narrowed = {k: v for k, v in r["scenarios"].items() if k == "Base"}
    with pytest.raises(ValueError, match="frozen"):
        ev.capture_evidence(r["ds"], r["bars"],
                            {"records": r["study"]["records"]}, r["cfg"],
                            scenarios=narrowed)


def test_c10b_strict_types_reject_bool_for_int_and_int_for_float():
    """C10b — `_compare_tree`'s bool branch and the series `n` used `!=`,
    so `True == 1` and `32 == 32.0` passed."""
    assert not ev._strict_equal(True, 1)
    assert not ev._strict_equal(1, True)
    assert not ev._strict_equal(32, 32.0)
    assert not ev._strict_equal(32.0, 32)
    assert ev._strict_equal(32, 32)
    assert ev._strict_equal(True, True)
    assert ev._strict_equal(1.5, 1.5)
    assert ev._strict_equal(None, None)
    assert not ev._strict_equal(None, 0)


def test_c10b_bool_leaf_smuggled_as_int_is_refused_by_compare_tree():
    e, formal, files = _fixture()
    tkey = e.theta_keys()[0]
    cons = formal["oracle_daily"][tkey]["day_universe"]["conservation"]
    key = sorted(cons)[0]
    cons[key] = 1                      # True smuggled as 1
    assert any(p.startswith("evidence_leaf_mismatch")
               for p in _hard(e, formal, files))


def test_c10b_series_n_as_float_is_refused():
    e, formal, files = _fixture()
    tkey = e.theta_keys()[0]
    block = formal["oracle_daily"][tkey]["executable"]["E1"]["Base"]["pooled"]
    block["n"] = float(block["n"])
    assert any(p.startswith("evidence_series_n") for p in _hard(e, formal,
                                                                files))


def test_c4_ev13_caller_attestation_boundary_is_documented():
    """C4 — a caller feeding the DECLARED dict back as "observations" is
    indistinguishable from an honest re-hash at this layer. The boundary is
    documented rather than papered over."""
    doc = ev.__doc__ or ""
    assert "CALLER-ATTESTATION BOUNDARY" in doc
    assert "INDISTINGUISHABLE" in doc
    r = _real_pieces()
    formal = _formal_payload()
    fed_back = dict(formal["governance"]["frozen_hashes"])
    e = ev.capture_evidence(r["ds"], r["bars"],
                            {"records": r["study"]["records"]}, r["cfg"],
                            scenarios=r["scenarios"], universe=r["uni"],
                            frozen_hash_observations=fed_back)
    # honest-looking by construction — this is the documented limit, and the
    # marker is correctly ABSENT because something WAS supplied.
    hard, markers = ev.split_problems(
        ev.reconcile_with_evidence(e, formal, _sealed_files()))
    assert not any(p.startswith("evidence_frozen_hash_mismatch") for p in hard)
    assert not any(m.startswith("PARTIAL:governance.frozen_hashes")
                   for m in markers)


def test_cr4_epoch_convention_cross_check_actually_runs():
    """The `_epoch_of_year` docstring promises a CR-4 cross-check between
    the dataset half-open string convention and `stability._epoch_of`'s
    inclusive integer one; this proves the branch exists and bites."""
    e, formal, files = _fixture()
    assert _hard(e, formal, files) == []
    victim = e.day_strata[0]
    poisoned = ev.CanonicalS0Evidence(**{
        **{f.name: getattr(e, f.name)
           for f in __import__("dataclasses").fields(e)},
        "day_strata": (dataclasses_replace(victim,
                                           stability_epoch="1999-2000"),)
        + tuple(e.day_strata[1:])})
    assert any(p.startswith("evidence_cr4_epoch_convention_disagreement")
               for p in _hard(poisoned, formal, files))


def test_marker_list_is_stable_and_every_marker_names_a_reason():
    e, formal, files = _fixture()
    markers = ev.split_problems(
        ev.reconcile_with_evidence(e, formal, files))[1]
    assert markers == sorted(markers)
    for m in markers:
        body = m[len(ev.PARTIAL_PREFIX):]
        section, _, reason = body.partition(":")
        assert section and reason, m


# ===========================================================================
# I. CLOSEOUT — EV-13 completeness gating + the F10 vocabulary refusal
# ===========================================================================
# Completeness is measured against the payload's OWN declared governance
# block, the only place the expected path set is visible to this module. In
# production that declared set is itself pinned to `guards.FROZEN_HASHES` by
# validate_formal_payload's expected-governance comparison, so
# observed == declared == FROZEN_HASHES transitively.

def _capture_with(obs):
    r = _real_pieces()
    return ev.capture_evidence(r["ds"], r["bars"],
                               {"records": r["study"]["records"]}, r["cfg"],
                               scenarios=r["scenarios"], universe=r["uni"],
                               frozen_hash_observations=obs)


def _fh_markers_and_hard(e, formal, files):
    hard, markers = ev.split_problems(
        ev.reconcile_with_evidence(e, formal, files))
    return hard, [m for m in markers
                  if m.startswith("PARTIAL:governance.frozen_hashes")]


def test_ev13_empty_observation_is_refused_at_capture():
    """An empty mapping must never earn the byte-anchored provenance while
    comparing nothing — a caller error, not a silent pass (C3)."""
    with pytest.raises(ValueError, match="EMPTY"):
        _capture_with({})


def test_ev13_complete_observation_drops_the_marker():
    formal, files = _formal_payload(), _sealed_files()
    e = _capture_with(dict(formal["governance"]["frozen_hashes"]))
    hard, fh_markers = _fh_markers_and_hard(e, formal, files)
    assert not any(p.startswith("evidence_frozen_hash") for p in hard)
    assert fh_markers == []


def test_ev13_partial_key_set_is_refused_and_keeps_the_marker():
    formal, files = _formal_payload(), _sealed_files()
    full = dict(formal["governance"]["frozen_hashes"])
    dropped = sorted(full)[0]
    e = _capture_with({k: v for k, v in full.items() if k != dropped})
    hard, fh_markers = _fh_markers_and_hard(e, formal, files)
    assert any(p.startswith("evidence_frozen_hash_key_set_mismatch:")
               and dropped in p for p in hard), hard
    assert fh_markers != []


def test_ev13_extra_key_is_refused_and_keeps_the_marker():
    formal, files = _formal_payload(), _sealed_files()
    obs = dict(formal["governance"]["frozen_hashes"])
    obs["NOT_DECLARED.md"] = "f" * 64
    e = _capture_with(obs)
    hard, fh_markers = _fh_markers_and_hard(e, formal, files)
    assert any(p.startswith("evidence_frozen_hash_key_set_mismatch:")
               and "NOT_DECLARED.md" in p for p in hard), hard
    assert fh_markers != []


def test_ev13_wrong_digest_is_not_masked_by_an_incomplete_key_set():
    formal, files = _formal_payload(), _sealed_files()
    victim = sorted(formal["governance"]["frozen_hashes"])[0]
    e = _capture_with({victim: "e" * 64})
    hard = _hard(e, formal, files)
    assert f"evidence_frozen_hash_mismatch:{victim}" in hard, hard


def test_ev13_not_supplied_keeps_the_honest_partial():
    r = _real_pieces()
    e = ev.capture_evidence(r["ds"], r["bars"],
                            {"records": r["study"]["records"]}, r["cfg"],
                            scenarios=r["scenarios"], universe=r["uni"])
    _hard_, fh_markers = _fh_markers_and_hard(e, _formal_payload(),
                                              _sealed_files())
    assert fh_markers != []


def test_f10_out_of_vocabulary_category_is_a_hard_problem():
    """A calendar returning a category outside the frozen IR-12/18 set
    disagrees with the frozen vocabulary — a refusal, never a silent skip."""
    import dataclasses
    e, formal, files = _fixture()
    assert _hard(e, formal, files) == []
    victim = e.f10_memberships[0]
    poisoned = ev.CanonicalS0Evidence(**{
        **{f.name: getattr(e, f.name) for f in dataclasses.fields(e)},
        "f10_memberships": (dataclasses_replace(
            victim, raw_categories=("NOT_A_FROZEN_CATEGORY",)),)
        + tuple(e.f10_memberships[1:])})
    assert any(p.startswith("evidence_f10_out_of_vocabulary_category:")
               for p in _hard(poisoned, formal, files))


# ===========================================================================
# J. M6.1.4-ARCH — the DISPOSITION REGISTRY and the behavioural consumption
#    proof (finding F-2, a MEDIUM that RECURRED).
#
# An independent reviewer proved a STRIPPED evidence object sealed through
# the real renderer with hard_problems == [], the SAME 11 PARTIAL markers as
# the honest run, and BYTE-IDENTICAL sealed files. Design-phase measurement
# added three facts the finding did not name: `record_pnl` with every inner
# row dict emptied was equally silent; `estimator_identity` with three blank
# method strings was equally silent; and — decisively — PARTIAL strips were
# silent too (EV-3 at 1 of 32 rows, EV-7 at 1 of 32 cells, EV-5 at 23 of 46).
#
# That last class is why `ran = compared_count > 0` is NOT the fix and is
# not what these tests assert. THE GATE IS COMPLETENESS against a population
# that never reads the field it guards. Every case below is generated FROM
# `ev.FIELD_REGISTRY`, and every assertion checks the REGISTRY-DECLARED code
# or marker section — never merely "some string appeared".
# ===========================================================================
import dataclasses as _dc                                       # noqa: E402
import hashlib                                                  # noqa: E402

_EV_FIELDS = tuple(sorted(f.name for f in
                          _dc.fields(ev.CanonicalS0Evidence)))
_TUPLE_FIELDS = ("blocks", "bootstrap_inputs", "cost_scenarios", "day_facts",
                 "day_strata", "engines", "eras", "f10_memberships",
                 "grid_pools", "label_availability", "na_observations",
                 "opening_ranges", "scenarios", "theoretical_paths",
                 "thetas")
_ABSENT = object()
_XCHECK = "EV-2_oracle_cross_check"


def _empty_value_for(field: str):
    """The EMPTY value of a field, in its own declared shape. Note
    `estimator_identity` is emptied to a well-typed but VACUOUS fact (three
    blank constants, `all_three_agree` still claiming True) rather than to
    None: that is the harder case, and it is exactly the one that used to
    seal."""
    if field == "schema_version":
        return ""
    if field == "funnel":
        return ev.FunnelFact(level_dates=ev.freeze({}),
                             exclusion_reason=ev.freeze({}),
                             provenance=ev.PROV_NOT_SUPPLIED)
    if field == "estimator_identity":
        return ev.EstimatorIdentityFact(
            study_percentile_method="", stability_percentile_method="",
            stats_percentile_method="", all_three_agree=True,
            worst_day_estimator_ruling=None, estimator_status_expected="")
    if field == "frozen_hash_observation":
        return ev.FrozenHashObservationFact(observed=ev.freeze({}),
                                            provenance=ev.PROV_NOT_SUPPLIED)
    if field in ("record_pnl", "record_fields", "provenance"):
        return ev.freeze({})
    return ()


def _variant(base, **over):
    return ev.CanonicalS0Evidence(**{
        **{f.name: getattr(base, f.name) for f in _dc.fields(base)}, **over})


def _split(evidence):
    return ev.split_problems(
        ev.reconcile_with_evidence(evidence, _formal_payload(),
                                   _sealed_files()))


def _baseline():
    if "arch_base" not in _CACHE:
        _CACHE["arch_base"] = _split(_real_pieces()["e"])
    return _CACHE["arch_base"]


# A field whose HONEST state in the shared fixture is ALREADY empty cannot
# be measured by emptying it, so its baseline is a capture that populated
# it. Membership here is not a judgement call: it is derived from the honest
# outcomes and asserted by
# `test_populated_baselines_cover_exactly_the_already_empty_fields`.
_POPULATED_BASELINES = {
    "frozen_hash_observation": lambda: _capture_with(
        dict(_formal_payload()["governance"]["frozen_hashes"])),
}


def _honest_baseline_for(field):
    builder = _POPULATED_BASELINES.get(field)
    if builder is None:
        return _real_pieces()["e"]
    key = "populated_baseline:" + field
    if key not in _CACHE:
        _CACHE[key] = builder()
    return _CACHE[key]


def test_populated_baselines_cover_exactly_the_already_empty_fields():
    """FIXTURE CORRECTION, not an exemption — and a self-maintaining one: a
    field whose every check already compares 0 of N on the honest fixture
    MUST have a populated baseline, and no other field may have one."""
    e, formal, files = _fixture()
    outcomes = ev.reconcile_outcomes(e, formal, files)
    already_empty = {
        field for field, spec in ev.FIELD_REGISTRY.items()
        if all(outcomes[c].applicable > 0 and outcomes[c].compared_count == 0
               for c in spec.checks)}
    assert already_empty == set(_POPULATED_BASELINES)
    for field in _POPULATED_BASELINES:
        base = _honest_baseline_for(field)
        assert getattr(base, field) != getattr(e, field), (
            f"{field}: the populated baseline must actually populate it")


def _assert_registered_difference(field, hard, partial, baseline=None) -> None:
    """The difference from the honest baseline must be the REGISTRY-declared
    hard code, the registry-declared dedicated PARTIAL section, or an
    explicit NOT_APPLICABLE marker — never merely "some string appeared"."""
    spec = ev.FIELD_REGISTRY[field]
    base_h, base_p = baseline if baseline is not None else _baseline()
    new_hard = set(hard) - set(base_h)
    new_part = set(partial) - set(base_p)
    assert new_hard or new_part, f"{field}: output did not differ at all"
    for code in spec.empty_hard_codes:
        assert any(h.startswith(code) for h in new_hard), (
            f"{field}: registry declares hard code {code!r}, absent from "
            f"{sorted(new_hard)[:6]}")
    for section in spec.empty_partial_sections:
        assert any(m.startswith(ev.PARTIAL_PREFIX + section + ":")
                   for m in new_part), (
            f"{field}: registry declares PARTIAL section {section!r}, "
            f"absent from {sorted(new_part)[:6]}")
    if not spec.empty_hard_codes and not spec.empty_partial_sections:
        pytest.fail(f"{field} has no registered empty signature")


# --- registry completeness (the SPEC-level tests) --------------------------
def test_field_registry_covers_every_canonical_evidence_field():
    """Adding a field to `CanonicalS0Evidence` without registering exactly
    one disposition for it must FAIL here."""
    assert set(ev.FIELD_REGISTRY) == set(_EV_FIELDS)
    for name, spec in ev.FIELD_REGISTRY.items():
        assert spec.disposition in {
            ev.REQUIRED_COMPARED, ev.CONDITIONAL, ev.EXPLICIT_PARTIAL,
            ev.PURE_METADATA, ev.EXPLICIT_NOT_APPLICABLE}, name
        assert spec.checks, f"{name} owns no check"
        assert spec.population_source and spec.legitimately_empty, name
        assert spec.empty_hard_codes or spec.empty_partial_sections, name


def test_every_registered_check_is_owned_or_is_a_declared_byte_rail():
    owned = {c for d in ev.FIELD_REGISTRY.values() for c in d.checks}
    unowned = {k for k, v in ev.CHECK_REGISTRY.items() if v.field is None}
    assert owned | unowned == set(ev.CHECK_REGISTRY)
    assert not (owned & unowned)
    for check_id in owned:
        spec = ev.CHECK_REGISTRY[check_id]
        assert spec.field in ev.FIELD_REGISTRY, check_id
        assert check_id in ev.FIELD_REGISTRY[spec.field].checks


def test_pure_metadata_and_not_applicable_are_honestly_empty_at_top_level():
    """Reported, not filled. Every top-level field is load-bearing, so a
    static free pass would be the same failure mode as a blanket "empty
    means fine". PURE_METADATA has members only at the provenance-KEY level;
    EXPLICIT_NOT_APPLICABLE is only ever a runtime outcome."""
    dispositions = {d.disposition for d in ev.FIELD_REGISTRY.values()}
    assert ev.PURE_METADATA not in dispositions
    assert ev.EXPLICIT_NOT_APPLICABLE not in dispositions
    assert any(s.disposition == ev.PURE_METADATA
               for s in ev.PROVENANCE_REGISTRY.values())


def test_every_registered_check_produces_an_outcome_on_the_honest_fixture():
    e, formal, files = _fixture()
    outcomes = ev.reconcile_outcomes(e, formal, files)
    assert set(outcomes) == set(ev.CHECK_REGISTRY)
    for check_id, outcome in outcomes.items():
        assert outcome.check == check_id
        assert outcome.field == ev.CHECK_REGISTRY[check_id].field


def test_honest_run_every_check_is_complete_except_the_disclosed_ev13():
    """EV-13 is the ONE incomplete check on an honest fixture, because no
    frozen-hash observation was supplied — and that is DISCLOSED by its
    dedicated PARTIAL rather than passing silently."""
    e, formal, files = _fixture()
    outcomes = ev.reconcile_outcomes(e, formal, files)
    incomplete = sorted(k for k, o in outcomes.items() if not o.complete)
    assert incomplete == ["EV-13.frozen_hashes"]
    assert outcomes["EV-13.frozen_hashes"].compared_count == 0
    assert outcomes["EV-13.frozen_hashes"].applicable > 0


def test_ran_is_not_the_gate_completeness_is():
    """The headline correction of this round: `compared_count > 0` passes on
    a 1-of-32 strip. `complete` is what the seal is gated on."""
    thin = ev.CheckOutcome(check="x", field="opening_ranges", applicable=32,
                           compared_count=1)
    assert thin.ran is True
    assert thin.complete is False
    assert thin.not_applicable is False
    assert ev.CheckOutcome("x", None, 0, 0).not_applicable is True
    assert ev.CheckOutcome("x", None, 32, 32).complete is True


def test_registered_hard_codes_are_each_actually_emitted_somewhere():
    """Anti-circularity: a registry entry naming a code that no check emits
    would make the generated tests vacuous, so every declared code must be
    produced by its own field's empty variant."""
    base = _real_pieces()["e"]
    for field, spec in ev.FIELD_REGISTRY.items():
        if not spec.empty_hard_codes:
            continue
        hard, _p = _split(_variant(base, **{field: _empty_value_for(field)}))
        for code in spec.empty_hard_codes:
            assert any(h.startswith(code) for h in hard), (field, code)


# --- THE population property the whole mechanism rests on ------------------
def test_population_callables_never_read_the_field_they_guard():
    """`applicable` must not shrink when the guarded field is emptied — that
    is the property that stops a stripped field from shrinking its own
    expectation into vacuous satisfaction."""
    base = _real_pieces()["e"]
    formal = _formal_payload()
    parsed = ev._parse_sealed_rows(_sealed_files(), base.engines,
                                   base.scenarios, [])
    honest = ev._authoritative_populations(base, formal, parsed)
    for field, spec in ev.FIELD_REGISTRY.items():
        stripped = _variant(base, **{field: _empty_value_for(field)})
        got = ev._authoritative_populations(stripped, formal, parsed)
        for check_id in spec.checks:
            key = ev.CHECK_REGISTRY[check_id].population
            assert got[key] == honest[key], (
                f"{field}: emptying it changed its OWN population {key} "
                f"({honest[key]} -> {got[key]})")


# --- the behavioural acceptance, generated FROM the registry ---------------
@pytest.mark.parametrize("field", _EV_FIELDS)
def test_emptying_any_evidence_field_changes_the_reconcile_outcome(field):
    """One case per `CanonicalS0Evidence` field — the four the reviewer
    named (opening_ranges / day_strata / bootstrap_inputs / provenance) and
    EVERY other field in turn. The baseline is per-field (see
    `_POPULATED_BASELINES`), so a field whose honest fixture state is
    already empty is still measured against a populated one."""
    base = _honest_baseline_for(field)
    baseline = (_baseline() if field not in _POPULATED_BASELINES
                else _split(base))
    hard, partial = _split(_variant(base, **{field: _empty_value_for(field)}))
    _assert_registered_difference(field, hard, partial, baseline)


@pytest.mark.parametrize("keep", ["half", "one"])
@pytest.mark.parametrize("field", _TUPLE_FIELDS)
def test_partially_stripping_a_collection_field_is_refused(field, keep):
    """The class the finding did NOT name, and that a non-emptiness fix
    would have shipped straight past: before this round EV-3 at 1 of 32
    rows, EV-7 at 1 of 32 cells and EV-5 at 23 of 46 rows each produced
    hard == [] and the identical marker list."""
    base = _real_pieces()["e"]
    whole = getattr(base, field)
    assert whole, f"{field} is empty in the honest fixture"
    # A single-element collection has no proper partial strip, so the
    # strictest available strip is the empty one — asserted, never skipped.
    kept = () if len(whole) < 2 else (
        whole[:max(1, len(whole) // 2)] if keep == "half" else whole[:1])
    hard, partial = _split(_variant(base, **{field: kept}))
    _assert_registered_difference(field, hard, partial)


def test_the_four_at_once_strip_is_refused_with_every_registered_code():
    """The reviewer's exact counterexample: `dataclasses.replace(evidence,
    opening_ranges=(), day_strata=(), bootstrap_inputs=(),
    provenance=freeze({}))` used to yield hard_problems == [], the same 11
    markers, and byte-identical sealed files."""
    base = _real_pieces()["e"]
    stripped = _variant(base, opening_ranges=(), day_strata=(),
                        bootstrap_inputs=(), provenance=ev.freeze({}))
    hard, partial = _split(stripped)
    assert hard != []
    for field in ("opening_ranges", "day_strata", "bootstrap_inputs",
                  "provenance"):
        _assert_registered_difference(field, hard, partial)


# --- the two vacuous fields found during design, by name -------------------
def test_record_pnl_with_every_inner_row_emptied_is_refused():
    """Found while designing this round: all eight (engine|scenario) keys
    present, every inner row dict emptied. The `ran` flag lived INSIDE the
    date-intersection loop and no marker was registered, so this produced
    zero problems, zero markers and byte-identical sealed files."""
    base = _real_pieces()["e"]
    hollow = _variant(base,
                      record_pnl=ev.freeze({k: {} for k in base.record_pnl}))
    hard, _partial = _split(hollow)
    assert any(h.startswith("evidence_record_pnl_missing_row:") for h in hard)
    assert "evidence_check_incomplete:AF2.record_pnl:0!=256" in hard


def test_estimator_identity_with_blank_constants_is_refused():
    """Found while designing this round: reconcile TRUSTED the captured
    `all_three_agree` boolean, so three blank method strings still claiming
    agreement sealed cleanly. The three strings are now bound to the LIVE
    module constants and agreement is RE-DERIVED."""
    base = _real_pieces()["e"]
    blank = _variant(
        base, estimator_identity=_empty_value_for("estimator_identity"))
    hard, _partial = _split(blank)
    for label in ("study", "stability", "stats"):
        assert any(h.startswith("evidence_percentile_constant_drift:" + label)
                   for h in hard)


def test_estimator_agreement_is_rederived_not_taken_from_capture():
    """A fact claiming `all_three_agree=True` while its own three strings
    disagree is a capture defect, and is now named as one."""
    base = _real_pieces()["e"]
    lying = _variant(base, estimator_identity=dataclasses_replace(
        base.estimator_identity, stats_percentile_method="higher",
        all_three_agree=True))
    hard, _p = _split(lying)
    assert any(h.startswith("evidence_estimator_agreement_not_rederivable:")
               for h in hard)
    assert any(h.startswith("evidence_percentile_constant_drift:stats:")
               for h in hard)


# --- provenance: FOUR distinct deterministic dispositions ------------------
def _prov(**over):
    base = _real_pieces()["e"]
    prov = dict(base.provenance)
    for key, value in over.items():
        if value is _ABSENT:
            prov.pop(key, None)
        else:
            prov[key] = value
    return _variant(base, provenance=ev.freeze(prov))


def test_provenance_absent_key_is_never_read_as_agrees():
    """Disposition 1 of 4. ABSENT must have its OWN deterministic code — the
    silent pass on a missing key is half of finding F-2."""
    hard, _p = _split(_prov(**{_XCHECK: _ABSENT}))
    assert "evidence_provenance_key_absent:" + _XCHECK in hard
    assert "evidence_check_incomplete:provenance.registry:20!=21" in hard
    assert not any(h.startswith("evidence_theoretical_oracle_cross_check")
                   for h in hard)


def test_provenance_wrong_type_is_its_own_disposition():
    """Disposition 2 of 4."""
    hard, _p = _split(_prov(**{_XCHECK: 0}))
    assert "evidence_provenance_key_type:" + _XCHECK + ":int" in hard


def test_provenance_out_of_vocabulary_is_its_own_disposition():
    """Disposition 3 of 4 — only the EXACT literal "agrees" is a pass."""
    hard, _p = _split(_prov(**{_XCHECK: "whatever"}))
    assert ("evidence_provenance_key_vocabulary:" + _XCHECK
            + ":'whatever'") in hard


def test_provenance_explicit_disagreement_keeps_its_existing_code():
    """Disposition 4 of 4, with the pre-existing problem code preserved."""
    hard, _p = _split(_prov(**{_XCHECK: "DISAGREEMENT:2020-01-02"}))
    assert ("evidence_theoretical_oracle_cross_check:"
            "DISAGREEMENT:2020-01-02") in hard


def test_the_four_provenance_dispositions_are_pairwise_distinct():
    seen = []
    for value in (_ABSENT, 0, "whatever", "DISAGREEMENT:x"):
        hard, _p = _split(_prov(**{_XCHECK: value}))
        seen.append(tuple(sorted(h for h in hard if _XCHECK in h
                                 or "oracle_cross_check" in h)))
    assert all(seen), seen
    assert len(set(seen)) == 4, seen


def test_provenance_dr_status_vocabulary_is_bound():
    hard, _p = _split(_prov(**{"EV-5_dr2_status": "probably_fine"}))
    assert ("evidence_provenance_key_vocabulary:EV-5_dr2_status:"
            "'probably_fine'") in hard


def test_provenance_bound_keys_must_match_the_field_they_label():
    hard, _p = _split(_prov(**{"EV-9": ev.PROV_NOT_SUPPLIED}))
    assert any(h.startswith("evidence_provenance_binding:EV-9:") for h in hard)


# --- marker derivation is structural, not hand-assembled -------------------
def test_honest_run_marker_text_is_byte_stable():
    """HARD REQUIREMENT of this round: the refactor must not move a single
    byte of an honest run's disclosure, because `HANDOFF_ADMISSION.json`
    seals `partial_coverage` verbatim. The two literals below are
    transcribed from the PRE-REFACTOR implementation."""
    e, formal, files = _fixture()
    markers = ev.split_problems(
        ev.reconcile_with_evidence(e, formal, files))[1]
    assert len(markers) == 17
    assert markers == sorted(markers)
    assert {m[len(ev.PARTIAL_PREFIX):].split(":", 1)[0] for m in markers} == {
        "oracle_daily.worst_day_pnl_percentiles",
        "theoretical_oracle.worst_day_pnl_percentiles", "stability_views",
        "stability_views.vol_terciles", "bootstrap_ci.ci_lo_ci_hi",
        "feasibility_grid.per_seed", "sizing_outputs.cost_layer",
        "usd_layer", "structural.na_table.reasons", "day_strata",
        "records.executable_fills", "governance.frozen_hashes",
        # M6.1.4-R2 leaf lineage: five NEW disclosure sections, each naming
        # one leaf path with no independent authority. The sealed
        # HANDOFF_ADMISSION.json digest changes BY DESIGN and by enumeration
        # (matrix S7) — `bf7628a4b42985fb` is no longer an anchor.
        "theoretical_oracle.favourable_extreme_ts",
        "sizing_outputs.opening_range_non_anchor_extreme",
        "structural.label_anchor_availability.dependency_booleans",
        "structural.label_anchor_availability.per_day_values",
        "structural.f10_raw_membership.per_date"}
    assert set(ev.PERMANENT_MARKERS) <= set(markers)
    assert ("PARTIAL:governance.frozen_hashes:EV-13 comparison did not run "
            "over a non-empty observed set — the seal-boundary equality "
            "stays tautological (matrix L127)") in markers
    # S0 closeout (2026-08-10): the marker was rewritten for the RULED
    # posture (conformance F6.1) — the pin moves with the correction.
    assert ("PARTIAL:usd_layer:USD figures inherit the DR-1 RULED cost "
            "input; the ruling closed the definition gap — the residual "
            "is that this module re-verifies fills against EV-4 "
            "snapshots, not against the raw cost table "
            "(matrix L132/S6.3)") in markers


def test_a_check_that_never_ran_is_reported_by_the_registry():
    """The `checks["day_strata"]` bug, inverted: markers are derived by
    iterating CHECK_REGISTRY, so an outcome nobody wrote still speaks."""
    partial_only = {k: v for k, v in ev.CHECK_REGISTRY.items()
                    if v.partial_section is not None}
    assert partial_only
    markers = ev._markers_from_registry({})
    for spec in partial_only.values():
        assert any(m.startswith(ev.PARTIAL_PREFIX + spec.partial_section + ":")
                   for m in markers), spec.partial_section
    assert set(ev.PERMANENT_MARKERS) <= markers


def test_an_internal_error_no_longer_empties_the_partial_list():
    """C-13 disclosure-integrity note: before the try/finally, an exception
    inside the check sequence wiped every PARTIAL from the returned list,
    because `_partial_markers` was only reached at the very end."""
    base = _real_pieces()["e"]
    broken = _variant(base, estimator_identity=None)
    hard, partial = _split(broken)
    assert len(partial) == 17
    assert any(h.startswith("evidence_field_type:estimator_identity:")
               for h in hard)


def test_markers_from_registry_never_raises_on_junk():
    for junk in (None, 0, "x", [], {"nope": object()}):
        assert isinstance(ev._markers_from_registry(junk), set)


@pytest.mark.parametrize("field", ["opening_ranges", "bootstrap_inputs",
                                   "provenance", "day_strata"])
def test_counters_and_problem_order_do_not_depend_on_iteration_order(field):
    """`applicable` / `compared_count` must be pure counts and the problem
    LIST must be order-stable, so neither can vary with PYTHONHASHSEED.

    Every counter is incremented inside a loop over a frozen tuple, a
    registry mapping, or an explicitly `sorted(...)` sequence; the sets that
    do appear (`covered`, `missing_ev3`, `unanchored`, the frozen-hash key
    sets) are used only for membership, de-duplication or `len()`, never as
    an iteration source for a counter."""
    base = _real_pieces()["e"]
    stripped = _variant(base, **{field: _empty_value_for(field)})
    runs = []
    for _ in range(3):
        problems = ev.reconcile_with_evidence(stripped, _formal_payload(),
                                              _sealed_files())
        outcomes = ev.reconcile_outcomes(stripped, _formal_payload(),
                                         _sealed_files())
        runs.append((tuple(problems),
                     tuple(sorted((k, o.applicable, o.compared_count)
                                  for k, o in outcomes.items()))))
    assert len(set(runs)) == 1, "reconcile output varied between runs"


# --- the AST test, RENAMED so it can never again be cited as consumption ---
def test_every_field_name_appears_in_a_consumer_function_source():
    """SOURCE-TOKEN test only. RENAMED from the former "dead evidence
    tripwire": it passed unchanged on the implementation the reviewer broke,
    because it asserts only that each field NAME appears inside a consumer
    function — it cannot detect VACUOUS consumption. Kept as a secondary
    aid; the primary evidence of consumption is behavioural (section J)."""
    import ast
    import inspect

    tree = ast.parse(inspect.getsource(ev))
    consumers = {"_reconcile_inner", "_reconcile_checks",
                 "_authoritative_populations", "_preflight_field_shapes"}
    referenced = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        if not (node.name in consumers
                or node.name.startswith("_reconcile_")
                or node.name.startswith("_compare_")
                or node.name.startswith("rebuild_")
                or node.name.startswith("_check_")):
            continue
        for sub in ast.walk(node):
            if isinstance(sub, ast.Attribute):
                referenced.add(sub.attr)
    unread = set(_EV_FIELDS) - referenced
    assert unread == set(), f"field name never referenced: {unread}"


# ===========================================================================
# K. PRODUCTION-SHAPED: the REAL renderer (scripts/s0_real_run.py::
#    render_s0_report), loaded read-only via the tests/test_s0_runner.py
#    `real_run_module` idiom replicated locally per this module's exclusive
#    file-scope boundary. The script is CALLED, never edited.
# ===========================================================================
def _real_run_module():
    if "real_run" not in _CACHE:
        import importlib.util
        import pathlib
        script = (pathlib.Path(__file__).resolve().parents[1] / "scripts"
                  / "s0_real_run.py")
        spec = importlib.util.spec_from_file_location("s0_real_run", script)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _CACHE["real_run"] = mod
    return _CACHE["real_run"]


def _render_result(evidence):
    """The compute-result tree `render_s0_report` consumes, assembled from
    this module's own producer-derived fixture."""
    r = _real_pieces()
    result = dict(_formal_payload())
    result["records"] = copy.deepcopy(r["study"]["records"])
    result["study"] = r["study"]
    result["dataset"] = r["ds"]
    result["reported_total_na"] = r["reported_total_na"]
    result["na_reason_counts"] = {}
    result["evidence"] = evidence
    return result


def _render(evidence):
    return _real_run_module().render_s0_report(
        _render_result(evidence), expected_governance=copy.deepcopy(_GOV))


def _seal(evidence):
    """(digests, evidence_reconciliation) for one full production render."""
    files = _render(evidence)
    digests = {k: hashlib.sha256(v.encode("utf-8")).hexdigest()
               for k, v in files.items()}
    rec = json.loads(
        files["HANDOFF_ADMISSION.json"])["evidence_reconciliation"]
    return digests, rec


def _seal_honest(field):
    """The honest seal against which `field`'s removal is measured, cached
    per baseline."""
    key = "seal:" + ("populated" if field in _POPULATED_BASELINES
                     else "shared")
    if key not in _CACHE:
        _CACHE[key] = _seal(_honest_baseline_for(field))
    return _CACHE[key]


def _disclosure_variant(base, field):
    """The evidence an HONEST REDUCED CAPTURE would produce: the field is
    absent AND the provenance key BOUND to it says so.

    Which provenance key that is comes from `ev.PROVENANCE_REGISTRY`
    (`bound_to`), never from a hardcoded name — so a field registered as a
    disclosure in future is handled without touching this helper. Without
    this, an evidence object claiming `EV-9 == atom_S0Universe` while
    carrying no funnel is an INCONSISTENT capture and is correctly refused
    by the binding check; that is a different fact from the disclosure
    path, and conflating the two would make this test prove neither."""
    prov = dict(base.provenance)
    for key, spec in ev.PROVENANCE_REGISTRY.items():
        if (spec.kind == ev._PROV_BOUND
                and spec.bound_to.split(".")[0] == field):
            prov[key] = ev.PROV_NOT_SUPPLIED
    return _variant(base, provenance=ev.freeze(prov),
                    **{field: _empty_value_for(field)})


def test_the_honest_fixture_seals_through_the_real_renderer():
    digests, rec = _seal_honest("day_facts")
    assert "S0_REPORT.json" in digests
    assert "HANDOFF_ADMISSION.json" in digests
    assert rec["hard_problems"] == []
    assert len(rec["partial_coverage"]) == 17


@pytest.mark.parametrize("field", _EV_FIELDS)
def test_removing_any_evidence_field_changes_the_production_seal(field):
    """The production-shaped proof, one case per field, NO skips.

    Before this round the four-field strip rendered to a BYTE-IDENTICAL
    sealed set. Now every field's removal changes the production outcome,
    and WHICH way it changes is dictated by the field's registered
    disposition, not by a name list:

      * a field with registered hard codes takes the REFUSAL path —
        `render_s0_report` raises and no file is produced at all, so
        byte-identity is unreachable rather than merely unlikely;
      * a field registered as a DISCLOSURE takes the positive path — the
        renderer SUCCEEDS (the refusal path is correctly NOT taken), the
        full sealed set is still produced, and the sealed
        `partial_coverage` gains exactly the registered marker section, so
        `HANDOFF_ADMISSION.json` is NOT byte-identical to the honest run.

    SCOPE, stated narrowly on purpose: this covers EVIDENCE-SIDE removal. It
    says nothing about a producer poisoned BEFORE compute — that poisons
    capture and seal together, stays out of reach, and stays disclosed as
    `PARTIAL:records.executable_fills:` (packet P-1/P-2)."""
    spec = ev.FIELD_REGISTRY[field]
    base = _honest_baseline_for(field)
    honest_digests, honest_rec = _seal_honest(field)

    if spec.empty_hard_codes:                      # --- REFUSAL path ---
        stripped = _variant(base, **{field: _empty_value_for(field)})
        with pytest.raises(ValueError) as excinfo:
            produced, _rec = _seal(stripped)
            assert produced != honest_digests, (
                f"{field}: a stripped evidence object produced a "
                "BYTE-IDENTICAL sealed set — this is finding F-2")
        assert "evidence" in str(excinfo.value)
        return

    # --- DISCLOSURE path: assert the POSITIVE fact -----------------------
    assert spec.empty_partial_sections, (
        f"{field} is registered {spec.disposition} but declares neither a "
        "hard code nor a PARTIAL section — it would be untestable")
    digests, rec = _seal(_disclosure_variant(base, field))
    assert set(digests) == set(honest_digests), (
        f"{field}: the full sealed set must still be produced")
    assert rec["hard_problems"] == [], (
        f"{field}: registered as a disclosure, so the refusal path must NOT "
        f"be taken; got {rec['hard_problems'][:4]}")
    gained = set(rec["partial_coverage"]) - set(honest_rec["partial_coverage"])
    for section in spec.empty_partial_sections:
        assert any(m.startswith(ev.PARTIAL_PREFIX + section + ":")
                   for m in gained), (
            f"{field}: registry declares PARTIAL section {section!r}; sealed "
            f"partial_coverage gained {sorted(gained)}")
    assert (digests["HANDOFF_ADMISSION.json"]
            != honest_digests["HANDOFF_ADMISSION.json"]), (
        f"{field}: the disclosure must reach the sealed bytes — an identical "
        "HANDOFF_ADMISSION.json would mean the removal was silent")


def test_the_reviewers_four_field_strip_is_refused_by_the_real_renderer():
    """The exact counterexample, at the production seal boundary."""
    stripped = _variant(_real_pieces()["e"], opening_ranges=(),
                        day_strata=(), bootstrap_inputs=(),
                        provenance=ev.freeze({}))
    with pytest.raises(ValueError, match="evidence reconciliation failed"):
        _render(stripped)


# ===========================================================================
# L. M6.1.4-R2 — LEAF LINEAGE. The registry, the entity axes and the token
#    completeness criterion, one level BELOW FIELD_REGISTRY.
#
#    Expectations come from M6_1_4_LEAF_LINEAGE_MATRIX.md, never from the
#    implementation's own reflection. Reflection is used for exactly one
#    thing: asserting the registry COVERS every captured dataclass field.
# ===========================================================================
import collections as _collections                               # noqa: E402
import pathlib as _pathlib                                       # noqa: E402

_MATRIX_PATH = (_pathlib.Path(__file__).resolve().parents[1]
                / "M6_1_4_LEAF_LINEAGE_MATRIX.md")
_FENCE = "```" + "leafregistry"


def _matrix_rows():
    """Parse the fenced leafregistry block of the matrix document."""
    if "matrix_rows" in _CACHE:
        return _CACHE["matrix_rows"]
    text = _MATRIX_PATH.read_text(encoding="utf-8")
    start = text.index(_FENCE) + len(_FENCE)
    body = text[start:text.index("```", start)]
    rows = {}
    for line in body.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        assert len(parts) == 6, "matrix row must have 6 columns: " + repr(line)
        fam, leaf, disp, axis, vocab, section = (p.strip() for p in parts)
        key = fam + "." + leaf
        assert key not in rows, "duplicate matrix row " + key
        rows[key] = {"family": fam, "leaf": leaf, "disposition": disp,
                     "entity_axis": axis,
                     "key_vocab_axis": "" if vocab == "-" else vocab,
                     "marker_section": "" if section == "-" else section}
    _CACHE["matrix_rows"] = rows
    return rows


def test_leaf_registry_matches_the_lineage_matrix_document():
    """BOTH directions. The matrix is the oracle; the registry may not add,
    drop or re-dispose a leaf without the document saying so."""
    want = _matrix_rows()
    got = ev.LEAF_REGISTRY
    assert set(got) == set(want), (
        "registry-only=%s matrix-only=%s"
        % (sorted(set(got) - set(want))[:8], sorted(set(want) - set(got))[:8]))
    for key, row in sorted(want.items()):
        spec = got[key]
        assert spec.family == row["family"], key
        assert spec.leaf == row["leaf"], key
        assert spec.disposition == row["disposition"], key
        assert spec.entity_axis == row["entity_axis"], key
        assert spec.key_vocab_axis == row["key_vocab_axis"], key
        assert spec.marker_section == row["marker_section"], key


def test_the_matrix_declares_exactly_121_leaf_rows():
    assert len(_matrix_rows()) == 121


def test_leaf_registry_covers_every_captured_dataclass_field():
    """Reflection used ONLY as a coverage assertion (never to generate the
    expectations): every field of every captured dataclass must map to at
    least one registered leaf row."""
    families = {
        "EV-1": ev.CanonicalDayFact, "EV-2": ev.TheoreticalPathRecord,
        "EV-3": ev.OpeningRangeFact, "EV-4": ev.CostScenarioSnapshot,
        "EV-5": ev.DayStratumFact, "EV-6": ev.GridPoolFact,
        "EV-7": ev.BootstrapInputFact, "EV-8": ev.NAObservationFact,
        "EV-9": ev.FunnelFact, "EV-10": ev.F10MembershipFact,
        "EV-11": ev.LabelAvailabilityFact, "EV-12": ev.EstimatorIdentityFact,
        "EV-13": ev.FrozenHashObservationFact,
    }
    n_fields = 0
    for fam, cls in families.items():
        for f in _dc.fields(cls):
            n_fields += 1
            covered = [k for k, s in ev.LEAF_REGISTRY.items()
                       if s.family == fam
                       and (s.leaf == f.name
                            or s.leaf.startswith(f.name + ".")
                            or s.leaf.startswith(f.name + "@"))]
            assert covered, fam + "." + f.name + " has no LEAF_REGISTRY row"
    assert n_fields == 107, n_fields
    for name in ("schema_version", "thetas", "engines", "scenarios", "eras",
                 "blocks", "record_pnl", "record_fields", "provenance"):
        assert "TOP." + name in ev.LEAF_REGISTRY, name


def test_every_leaf_entity_axis_is_a_registered_axis():
    axes = set(ev.ENTITY_AXIS_AUTHORITIES)
    for key, spec in ev.LEAF_REGISTRY.items():
        assert spec.entity_axis in axes, key + ": " + spec.entity_axis
        if spec.key_vocab_axis:
            assert spec.key_vocab_axis in ev.KEY_VOCAB_AXES, key


def test_every_leaf_entity_axis_authority_never_reads_its_own_leaf():
    """The F-2 invariant, one level down: an axis may not be sized by the
    family it guards. Enforced from the documented authority table, so a
    future axis that reads its own family fails here rather than in review."""
    for key, spec in sorted(ev.LEAF_REGISTRY.items()):
        reads = ev.ENTITY_AXIS_AUTHORITIES[spec.entity_axis].reads
        assert key not in reads, (
            "%s: axis %r is sized by %s, which includes the guarded leaf"
            % (key, spec.entity_axis, reads))
        for read in reads:
            assert read in ev.LEAF_REGISTRY, (key, read)


def test_disclosure_and_dr_leaves_all_declare_a_marker_section():
    for key, spec in sorted(ev.LEAF_REGISTRY.items()):
        if spec.disposition in (ev.DISCLOSURE_UNVERIFIED, ev.DR_PARTIAL):
            assert spec.marker_section, key + " discloses nothing"
        else:
            assert not spec.marker_section, key + " must not carry a marker"


def test_the_disposition_tally_is_exactly_the_documented_one():
    tally = _collections.Counter(s.disposition
                                 for s in ev.LEAF_REGISTRY.values())
    assert dict(tally) == {
        ev.INDEPENDENT_BOUND: 75, ev.DERIVED_REDUNDANT: 30,
        ev.DISCLOSURE_UNVERIFIED: 10, ev.DR_PARTIAL: 6}


def test_leaf_checks_never_iterate_a_mapping_they_guard():
    """`for k in <obj>.<mapping>` inside a leaf check is the exact
    anti-pattern that made the EV-11 key deletion invisible."""
    import ast
    import inspect
    tree = ast.parse(inspect.getsource(ev))
    offenders = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        if not node.name.startswith("_leaves_"):
            continue
        for sub in ast.walk(node):
            if not (isinstance(sub, ast.For)
                    and isinstance(sub.iter, ast.Attribute)):
                continue
            recv = sub.iter.value
            module_alias = (isinstance(recv, ast.Name)
                            and recv.id.startswith("_"))
            if not module_alias:            # an EVIDENCE object's own mapping
                offenders.append("%s:%d" % (node.name, sub.lineno))
    assert offenders == [], offenders


# --- the token completeness criterion --------------------------------------
def _leaf_outcomes(evidence):
    return ev.reconcile_leaf_outcomes(evidence, _formal_payload(),
                                      _sealed_files())


def test_the_honest_fixture_has_every_leaf_complete():
    outs = _leaf_outcomes(_real_pieces()["e"])
    assert set(outs) == set(ev.LEAF_REGISTRY)
    incomplete = {k: (o.missing[:2], o.extra[:2], o.duplicate[:2])
                  for k, o in outs.items() if not o.complete}
    assert incomplete == {}, incomplete


def test_token_completeness_reports_missing_extra_duplicate_separately():
    exp = frozenset({"a", "b", "c"})
    o = ev._leaf_outcome_from("X.y", exp,
                              _collections.Counter(["a", "b", "b", "z"]))
    assert o.missing == ("c",)
    assert o.extra == ("z",)
    assert o.duplicate == ("b",)
    assert not o.complete
    ok = ev._leaf_outcome_from("X.y", exp,
                               _collections.Counter(["a", "b", "c"]))
    assert ok.complete and ok.missing == () and ok.extra == ()


def test_compared_count_ge_applicable_is_no_longer_a_completion_criterion():
    """The RIGHT NUMBER of WRONG tokens must not read as complete. That is
    precisely what `compared_count >= applicable` could never see."""
    exp = frozenset({"2020-01-02", "2020-01-03", "2020-01-06"})
    same_size_wrong_dates = _collections.Counter(
        ["2020-01-02", "1999-01-01", "1999-01-02"])
    o = ev._leaf_outcome_from("X.y", exp, same_size_wrong_dates)
    assert o.expected == 3 and o.actual == 3
    assert not o.complete, "equal counts must NOT satisfy completeness"
    assert set(o.missing) == {"2020-01-03", "2020-01-06"}
    assert set(o.extra) == {"1999-01-01", "1999-01-02"}


def test_check_outcome_complete_is_multiset_equality_not_a_count_compare():
    out = ev.CheckOutcome(check="c", field=None, applicable=3,
                          compared_count=3,
                          expected_tokens=frozenset({"a", "b", "c"}),
                          actual_tokens=("a", "b", "z"))
    assert not out.complete
    assert out.applicable == 3 and out.compared_count == 3


# --- EV-11: the assigned hole ----------------------------------------------
def _ev11_variant(base, fn):
    return _variant(base, label_availability=tuple(
        fn(f) for f in base.label_availability))


def _drop_label(base, label):
    return _ev11_variant(base, lambda f: _dc.replace(f, available=ev.freeze(
        {k: v for k, v in f.available.items() if k != label})))


@pytest.mark.parametrize("label", ["y_cont", "y1", "y2_de_pm",
                                   "y3_close_pos_pm", "y4_mfe", "y5_mae"])
def test_ev11_available_key_deletion_on_every_day_is_refused(label):
    """THE measured hole. Deleting one required label key from EVERY row
    used to produce hard=0 and a byte-identical PARTIAL list, dropping
    EV-11's dedicated marker while nothing was compared for that label."""
    hard, _p = _split(_drop_label(_real_pieces()["e"], label))
    assert any(h.startswith("evidence_ev11_available_key_set:") for h in hard),\
        hard[:6]


def test_ev11_available_extra_key_on_every_day_is_refused():
    e = _ev11_variant(_real_pieces()["e"], lambda f: _dc.replace(
        f, available=ev.freeze(dict(dict(f.available), y99_fake=True))))
    hard, _p = _split(e)
    assert any("y99_fake" in h for h in hard), hard[:6]


def test_ev11_available_aggregate_preserving_pair_swap_is_disclosed():
    """A swap preserving every per-label TOTAL is invisible to the aggregate
    check and stays invisible: the per-day value has no independent
    authority (the IR-23 reducer fence, matrix S3). What must NOT happen is
    silence — the dedicated PARTIAL is permanent and says exactly that."""
    base = _real_pieces()["e"]
    rows = list(base.label_availability)
    lab = "y1"
    i = next(k for k, f in enumerate(rows) if f.available[lab])
    j = next(k for k, f in enumerate(rows) if not f.available[lab])
    for k, v in ((i, False), (j, True)):
        rows[k] = _dc.replace(rows[k], available=ev.freeze(
            dict(dict(rows[k].available), **{lab: v})))
    hard, partial = _split(_variant(base, label_availability=tuple(rows)))
    assert hard == []
    assert any(m.startswith(ev.PARTIAL_PREFIX + "structural."
                            "label_anchor_availability.per_day_values:")
               for m in partial)


def test_ev11_dependency_booleans_are_disclosed_as_unverified():
    _hard, partial = _baseline()
    assert any(m.startswith(ev.PARTIAL_PREFIX + "structural."
                            "label_anchor_availability.dependency_booleans:")
               for m in partial)
    for leaf in ("o1000", "c1544", "pm_ok", "adr_ok"):
        spec = ev.LEAF_REGISTRY["EV-11." + leaf]
        assert spec.disposition == ev.DISCLOSURE_UNVERIFIED
    assert (ev.LEAF_REGISTRY["EV-11.dir_ok"].disposition
            == ev.INDEPENDENT_BOUND)


def test_ev11_dir_ok_flip_on_every_day_is_refused():
    """`dir_ok` alone IS closable without touching the fenced reducer:
    dataset.py:307-308 + 687 give dir_ok <=> EV-1.d_open != 0."""
    e = _ev11_variant(_real_pieces()["e"],
                      lambda f: _dc.replace(f, dir_ok=not f.dir_ok))
    hard, _p = _split(e)
    assert any(h.startswith("evidence_ev11_dir_ok_vs_d_open:") for h in hard)


def test_ev11_adr_ok_population_total_is_bound_to_ev8():
    e = _ev11_variant(_real_pieces()["e"],
                      lambda f: _dc.replace(f, adr_ok=not f.adr_ok))
    hard, _p = _split(e)
    assert any(h.startswith("evidence_ev11_adr_ok_total_vs_ev8:")
               for h in hard), hard[:6]


def test_ev11_five_boolean_flip_on_every_day_is_no_longer_wholly_silent():
    """The reviewer's most decisive case. Two of the five now bind; three
    stay disclosed. What must never recur is a flip that leaves NO trace."""
    e = _ev11_variant(_real_pieces()["e"], lambda f: _dc.replace(
        f, o1000=not f.o1000, c1544=not f.c1544, pm_ok=not f.pm_ok,
        adr_ok=not f.adr_ok, dir_ok=not f.dir_ok))
    hard, _p = _split(e)
    assert hard != [], "the all-five flip is still wholly silent"


# --- EV-1 producer mirrors and the event flag ------------------------------
@pytest.mark.parametrize("leaf", ["record_year", "record_era",
                                   "record_oracle_candidate",
                                   "tradeable_direction", "y_cont_available"])
def test_day_fact_producer_mirror_drift_is_refused(leaf):
    base = _real_pieces()["e"]

    def bump(f):
        v = getattr(f, leaf)
        return _dc.replace(f, **{leaf: (not v if isinstance(v, bool)
                                        else "ZZZ")})
    hard, _p = _split(_variant(base, day_facts=tuple(
        bump(f) for f in base.day_facts)))
    assert any(h.startswith("evidence_ev1_mirror_drift:" + leaf + ":")
               for h in hard), hard[:6]


def test_day_fact_direction_status_rewrite_on_every_day_is_refused():
    base = _real_pieces()["e"]
    facts = tuple(_dc.replace(f, direction_status="ZZZ")
                  for f in base.day_facts)
    hard, _p = _split(_variant(base, day_facts=facts))
    assert any(h.startswith("evidence_ev1_direction_status") for h in hard)


def test_day_fact_is_event_day_rewrite_on_every_day_is_refused():
    base = _real_pieces()["e"]
    facts = tuple(_dc.replace(f, is_event_day="ZZZ") for f in base.day_facts)
    hard, _p = _split(_variant(base, day_facts=facts))
    assert any(h.startswith("evidence_ev1_is_event_day") for h in hard)


# --- EV-2 / EV-3 -----------------------------------------------------------
@pytest.mark.parametrize("leaf", ["direction", "scenario_name", "entry_fill",
                                   "exit_fill", "favourable_extreme_price",
                                   "platform_fee_rt_usd"])
def test_theoretical_path_derived_leaves_are_rederived(leaf):
    base = _real_pieces()["e"]

    def bump(p):
        v = getattr(p, leaf)
        if isinstance(v, str):
            new = "ZZZ"
        elif isinstance(v, bool):
            new = not v
        else:
            new = v + 7
        return _dc.replace(p, **{leaf: new})
    hard, _p = _split(_variant(base, theoretical_paths=tuple(
        bump(p) for p in base.theoretical_paths)))
    assert any(h.startswith("evidence_ev2_leaf:" + leaf + ":")
               for h in hard), hard[:6]


def test_theoretical_path_timestamp_rail_rejects_an_out_of_window_ts():
    base = _real_pieces()["e"]
    paths = tuple(_dc.replace(p, favourable_extreme_ts="1999-01-01T03:00:00")
                  for p in base.theoretical_paths)
    hard, _p = _split(_variant(base, theoretical_paths=paths))
    assert any(h.startswith("evidence_ev2_favourable_extreme_ts:")
               for h in hard)


def test_theoretical_path_favourable_extreme_ts_stays_disclosed():
    _hard, partial = _baseline()
    assert any(m.startswith(ev.PARTIAL_PREFIX
                            + "theoretical_oracle.favourable_extreme_ts:")
               for m in partial)


def test_opening_range_anchor_side_is_bound_and_non_anchor_is_disclosed():
    base = _real_pieces()["e"]

    def poison_anchor(o):
        return (_dc.replace(o, or_low=o.or_low + 7.0) if o.d_open == 1
                else _dc.replace(o, or_high=o.or_high + 7.0))
    hard, _p = _split(_variant(base, opening_ranges=tuple(
        poison_anchor(o) for o in base.opening_ranges)))
    assert any(h.startswith("evidence_ev3_anchor_side:") for h in hard)
    _h, partial = _baseline()
    assert any(m.startswith(ev.PARTIAL_PREFIX + "sizing_outputs."
                            "opening_range_non_anchor_extreme:")
               for m in partial)


def test_ev3_d_open_flip_on_every_row_is_refused():
    base = _real_pieces()["e"]
    hard, _p = _split(_variant(base, opening_ranges=tuple(
        _dc.replace(o, d_open=-o.d_open) for o in base.opening_ranges)))
    assert any(h.startswith("evidence_ev3_d_open_vs_ev1:") for h in hard)


def test_ev3_n_obs_bars_out_of_range_is_refused():
    base = _real_pieces()["e"]
    hard, _p = _split(_variant(base, opening_ranges=tuple(
        _dc.replace(o, n_obs_bars=0) for o in base.opening_ranges)))
    assert any(h.startswith("evidence_ev3_n_obs_bars_range:") for h in hard)


# --- EV-4 / EV-5 -----------------------------------------------------------
def test_cost_scenario_spread_scalars_rebuild_the_four_snapshots():
    base = _real_pieces()["e"]
    hard, _p = _split(_variant(base, cost_scenarios=tuple(
        _dc.replace(s, spread_scalars=(9.0, 9.0, 9.0))
        for s in base.cost_scenarios)))
    assert any(h.startswith("evidence_ev4_spread_scalars:") for h in hard)


def test_cost_scenario_dr1_tokens_agree_with_the_provenance_status():
    """The DR-1 VALUES are unruled and unbindable — what IS bindable is the
    iff: a snapshot may claim a ruled reduction rule only when the recorded
    `EV-4_dr1_status` is not `unresolved`. Both directions are attacked."""
    base = _real_pieces()["e"]
    prov = dict(base.provenance)
    prov["EV-4_dr1_status"] = ev.STATUS_UNRESOLVED     # claims unresolved...
    hard, _p = _split(_variant(base, provenance=ev.freeze(prov)))
    assert any(h.startswith("evidence_ev4_dr1_token:") for h in hard), hard[:6]
    hard2, _p2 = _split(_variant(base, cost_scenarios=tuple(   # ...and back
        _dc.replace(s, reduction_rule_id=ev.UNRESOLVED_SPREAD_RULE)
        for s in base.cost_scenarios)))
    assert any(h.startswith("evidence_ev4_dr1_token:") for h in hard2),         hard2[:6]


@pytest.mark.parametrize("leaf", ["d_open", "event_flag_final", "event_na",
                                   "micro_execution_era"])
def test_day_stratum_mirror_leaves_track_ev1(leaf):
    base = _real_pieces()["e"]

    def bump(s):
        v = getattr(s, leaf)
        if isinstance(v, bool):
            new = not v
        elif isinstance(v, str):
            new = "ZZZ"
        else:
            new = v + 7
        return _dc.replace(s, **{leaf: new})
    hard, _p = _split(_variant(base, day_strata=tuple(
        bump(s) for s in base.day_strata)))
    assert any(h.startswith("evidence_ev5_mirror:")
               or h.startswith("evidence_day_stratum_era_mismatch:")
               for h in hard), hard[:6]


def test_day_stratum_year_corruption_is_refused_not_swallowed():
    """D5: the bare `except` around int(s.year) silently disabled the CR-4
    epoch cross-check for the corrupted row."""
    base = _real_pieces()["e"]
    hard, _p = _split(_variant(base, day_strata=tuple(
        _dc.replace(s, year="ZZZ") for s in base.day_strata)))
    assert any(h.startswith("evidence_ev5_mirror:year:")
               or h.startswith("evidence_cr4_epoch_unparseable_year:")
               for h in hard), hard[:6]


def test_day_stratum_vol_status_must_match_the_provenance_key():
    base = _real_pieces()["e"]
    hard, _p = _split(_variant(base, day_strata=tuple(
        _dc.replace(s, vol_status="resolved") for s in base.day_strata)))
    assert any(h.startswith("evidence_ev5_vol_status") for h in hard)


# --- EV-6 / EV-7 -----------------------------------------------------------
def test_grid_pool_contents_poisoned_with_counts_preserved_is_refused():
    base = _real_pieces()["e"]
    pools = tuple(_dc.replace(g, tp_pools=ev.freeze(
        dict((k, tuple("1999-01-01" for _ in v))
             for k, v in g.tp_pools.items())))
        for g in base.grid_pools)
    hard, _p = _split(_variant(base, grid_pools=pools))
    assert any(h.startswith("evidence_ev6_pool_union:") for h in hard)


@pytest.mark.parametrize("leaf,bad", [("grid_stream_tag", 0),
                                       ("stratum_axes", ()),
                                       ("n_tp_available", 999),
                                       ("n_fp_available", 999)])
def test_grid_pool_scalar_leaves_are_bound(leaf, bad):
    base = _real_pieces()["e"]
    hard, _p = _split(_variant(base, grid_pools=tuple(
        _dc.replace(g, **{leaf: bad}) for g in base.grid_pools)))
    assert any(h.startswith("evidence_ev6_leaf:" + leaf + ":")
               for h in hard), hard[:6]


def test_bootstrap_seeds_emptied_is_refused():
    """`seeds -> ()` was silent: the per-seed loop simply did nothing."""
    base = _real_pieces()["e"]
    hard, _p = _split(_variant(base, bootstrap_inputs=tuple(
        _dc.replace(b, seeds=()) for b in base.bootstrap_inputs)))
    assert any(h.startswith("evidence_ev7_leaf:seeds:") for h in hard), \
        hard[:6]


@pytest.mark.parametrize("leaf,bad", [
    ("stats_stream_tag", 0), ("block_stream_key", 0), ("ci_level", 0.5),
    ("percentile_method_id", "ZZZ"), ("n", 999), ("series_sum", 999.0),
    ("first_date", "1999-01-01"), ("last_date", "1999-01-01")])
def test_bootstrap_scalar_leaves_are_bound(leaf, bad):
    base = _real_pieces()["e"]
    hard, _p = _split(_variant(base, bootstrap_inputs=tuple(
        _dc.replace(b, **{leaf: bad}) for b in base.bootstrap_inputs)))
    assert any(h.startswith("evidence_ev7_leaf:" + leaf + ":")
               for h in hard), hard[:6]


# --- EV-8 / EV-9 / EV-10 ---------------------------------------------------
def test_na_observation_method_id_is_bound_to_the_frozen_literal():
    base = _real_pieces()["e"]
    hard, _p = _split(_variant(base, na_observations=tuple(
        _dc.replace(o, observation_method_id="hand_typed")
        for o in base.na_observations)))
    assert any(h.startswith("evidence_ev8_leaf:observation_method_id:")
               for h in hard)


def test_funnel_exclusion_reason_is_rebuilt_from_the_level_differences():
    base = _real_pieces()["e"]
    poisoned = _dc.replace(base.funnel,
                           exclusion_reason=ev.freeze({"1999-01-01": "ZZZ"}))
    hard, _p = _split(_variant(base, funnel=poisoned))
    assert any(h.startswith("evidence_ev9_exclusion_reason") for h in hard)


def test_f10_membership_trade_date_collapse_is_refused():
    base = _real_pieces()["e"]
    hard, _p = _split(_variant(base, f10_memberships=tuple(
        _dc.replace(m, trade_date="ZZZ") for m in base.f10_memberships)))
    assert any(h.startswith("evidence_leaf_incomplete:EV-10.trade_date")
               for h in hard), hard[:6]


def test_f10_final_category_is_bound_per_date_to_ev1():
    base = _real_pieces()["e"]
    hard, _p = _split(_variant(base, f10_memberships=tuple(
        _dc.replace(m, final_category="FOMC") for m in base.f10_memberships)))
    assert any(h.startswith("evidence_ev10_final_category_vs_ev1:")
               for h in hard)


def test_f10_raw_categories_per_date_stays_disclosed():
    _hard, partial = _baseline()
    assert any(m.startswith(ev.PARTIAL_PREFIX
                            + "structural.f10_raw_membership.per_date:")
               for m in partial)


# --- EV-12 / top level -----------------------------------------------------
def test_estimator_ruling_and_status_must_agree():
    base = _real_pieces()["e"]
    ident = _dc.replace(base.estimator_identity,
                        worst_day_estimator_ruling=None)
    hard, _p = _split(_variant(base, estimator_identity=ident))
    assert any(h.startswith("evidence_ev12_ruling_vs_status:") for h in hard)


def test_record_pnl_extra_captured_date_is_refused():
    base = _real_pieces()["e"]
    rp = dict((k, dict(v)) for k, v in base.record_pnl.items())
    for k in rp:
        rp[k]["1999-01-01"] = 12345.0
    hard, _p = _split(_variant(base, record_pnl=ev.freeze(rp)))
    assert any(h.startswith("evidence_record_pnl_extra_row:") for h in hard)


def test_provenance_extra_unregistered_key_is_refused():
    base = _real_pieces()["e"]
    pv = dict(base.provenance)
    pv["EV-99_bogus"] = "totally_made_up"
    hard, _p = _split(_variant(base, provenance=ev.freeze(pv)))
    assert any(h.startswith("evidence_provenance_key_extra:") for h in hard)


# --- the af1_days entity axis fails closed without a universe --------------
def test_af1_entity_axis_without_a_universe_emits_a_partial_not_completeness():
    """D3: when the universe IS supplied, EV-9.L3 is the authority. When it
    is NOT, the axis has NO authority and must say so — it must never fall
    back to sizing itself from the guarded family."""
    r = _real_pieces()
    reduced = ev.capture_evidence(r["ds"], r["bars"],
                                  {"records": r["study"]["records"],
                                   "study": r["study"]}, r["cfg"],
                                  scenarios=r["scenarios"])       # no universe
    hard, partial = _split(reduced)
    assert any(m.startswith(ev.PARTIAL_PREFIX
                            + "evidence.entity_axis.af1_days:")
               for m in partial), partial
    assert not any(h.startswith("evidence_leaf_incomplete:EV-1.")
                   for h in hard), (
        "an unauthoritative axis must SKIP completeness, not fake it")


def test_af1_entity_axis_authority_is_the_funnel_l3_when_supplied():
    e = _real_pieces()["e"]
    axes = ev.entity_axes_for(e, _formal_payload(), {})
    assert axes["af1_days"] == frozenset(
        e.funnel.level_dates["L3_structurally_eligible_days"])
    assert axes["af1_days"] == frozenset(f.trade_date for f in e.day_facts)


# --- PHASE D: the two headline claims at the REAL renderer boundary --------
def test_ev11_key_deletion_is_refused_by_the_real_renderer():
    """PHASE D. The headline claim at the production seal boundary: the
    variant that previously sealed BYTE-IDENTICALLY must now be unable to
    produce a sealed set at all."""
    stripped = _drop_label(_real_pieces()["e"], "y1")
    with pytest.raises(ValueError, match="evidence reconciliation failed"):
        _render(stripped)


def test_ev11_pair_swap_seals_but_carries_the_disclosure_at_the_renderer():
    """PHASE D. The aggregate-preserving swap has no independent authority,
    so it SEALS — but the sealed HANDOFF_ADMISSION.json must positively
    carry the per-day-values PARTIAL rather than claim coverage."""
    base = _real_pieces()["e"]
    rows = list(base.label_availability)
    lab = "y1"
    i = next(k for k, f in enumerate(rows) if f.available[lab])
    j = next(k for k, f in enumerate(rows) if not f.available[lab])
    for k, v in ((i, False), (j, True)):
        rows[k] = _dc.replace(rows[k], available=ev.freeze(
            dict(dict(rows[k].available), **{lab: v})))
    _digests, rec = _seal(_variant(base, label_availability=tuple(rows)))
    assert rec["hard_problems"] == []
    assert any(m.startswith(ev.PARTIAL_PREFIX + "structural."
                            "label_anchor_availability.per_day_values:")
               for m in rec["partial_coverage"])


def test_the_five_boolean_flip_is_refused_by_the_real_renderer():
    flipped = _ev11_variant(_real_pieces()["e"], lambda f: _dc.replace(
        f, o1000=not f.o1000, c1544=not f.c1544, pm_ok=not f.pm_ok,
        adr_ok=not f.adr_ok, dir_ok=not f.dir_ok))
    with pytest.raises(ValueError, match="evidence reconciliation failed"):
        _render(flipped)
