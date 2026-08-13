"""DR-5 MC consumer behaviour battery (synthetic fixtures ONLY).

Every fixture below is hand-built bytes — no sealed S0 value is read
anywhere in this file. The battery covers the named negative classes of
the DR-5 engineering prompt plus the full synthetic positive path
(prepare -> bundle validation -> epistemic -> aleatoric -> verdict ->
seal candidate)."""
from __future__ import annotations

import dataclasses
import hashlib
import json

import pytest

from conftest import make_trade_path
from itsf.contracts import RESEARCH_BOOTSTRAP_SEEDS
from itsf.mc import consumer as mcc
from itsf.mc.orchestrator import TemplateDay
from itsf.s0.handoff import McConsumerAbsent

TRIAL = "S0-T001"
COMMIT = "876c1b74131b4ab1a89dce433ecce646ba481f8c"
TP_DAYS = ("2026-08-03", "2026-08-05", "2026-08-07")
FP_DAYS = ("2026-08-04", "2026-08-06")
ALL_DAYS = tuple(sorted(TP_DAYS + FP_DAYS))


def _record_row(date: str, engine: str, scn: str, pnl: float) -> dict:
    rec = make_trade_path([pnl / 2, pnl], date=date, engine=engine,
                          final=pnl)
    row = dataclasses.asdict(rec)
    row["cost_scenario"] = scn
    return row


def _calendar(n_days: int = 8) -> mcc.TemplateCalendar:
    days = tuple(TemplateDay(day_id=f"T{i:03d}", cal_offset=i)
                 for i in range(n_days))
    return mcc.TemplateCalendar(days=days, first_month_offsets=(0, 1))


def _bundle(*, pnl: float = 80.0) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    counts: dict = {}
    for e in mcc.ENGINES:
        counts[e] = {}
        for s in mcc.SCENARIOS:
            rows = [_record_row(d, e, s, pnl) for d in ALL_DAYS]
            files[f"MC_HANDOFF_{e}_{s}.jsonl"] = "\n".join(
                json.dumps(r, sort_keys=True) for r in rows).encode("utf-8")
            counts[e][s] = {"n_records": len(rows)}
    report = {
        "governance": {"trial_id": TRIAL, "authorized_commit": COMMIT},
        "oracle_daily": {"theta_0.5": {"day_universe": {
            "tp_days": list(TP_DAYS), "fp_days": list(FP_DAYS)}}},
        "mc_handoff_manifest": {"counts": counts},
    }
    files["S0_REPORT.json"] = json.dumps(report).encode("utf-8")
    files["S0_REPORT.md"] = b"# synthetic"
    files["HANDOFF_ADMISSION.json"] = json.dumps(
        {"admitted": ["SEED_MANIFEST.json"]}).encode("utf-8")
    files["SEED_MANIFEST.json"] = json.dumps({
        "research_bootstrap_seeds": list(RESEARCH_BOOTSTRAP_SEEDS),
        "k_policy": "k_per_seed=200;k_start_index=0",
        "crn_scope": "shared_within_theta_engine_scenario",
    }).encode("utf-8")
    files["REGISTRY_AFTER_RUN_STARTED.json"] = json.dumps({
        "snapshot_before": {"trial_id": TRIAL,
                            "authorized_commit": COMMIT}}).encode("utf-8")
    manifest_lines = [
        json.dumps({"record_type": "file", "relative_path": n,
                    "file_sha256": hashlib.sha256(files[n]).hexdigest()},
                   sort_keys=True)
        for n in sorted(files)]
    files["manifest.jsonl"] = "\n".join(manifest_lines).encode("utf-8")
    return files


def _snapshot() -> dict:
    return {"trial_id": TRIAL, "authorized_commit": COMMIT,
            "event_sequence": 15}


def _prepare(bundle=None, **kw):
    return mcc.prepare_mc_input(bundle if bundle is not None else _bundle(),
                                authorization_snapshot=_snapshot(),
                                calendar=_calendar(), **kw)


def _mutate_report(bundle, fn):
    report = json.loads(bundle["S0_REPORT.json"])
    fn(report)
    bundle["S0_REPORT.json"] = json.dumps(report).encode("utf-8")
    _refresh_manifest(bundle)


def _refresh_manifest(bundle):
    names = [n for n in sorted(bundle) if n != "manifest.jsonl"]
    bundle["manifest.jsonl"] = "\n".join(
        json.dumps({"record_type": "file", "relative_path": n,
                    "file_sha256": hashlib.sha256(bundle[n]).hexdigest()},
                   sort_keys=True) for n in names).encode("utf-8")


# --- bundle battery (matrix R13 checks 1-8) --------------------------------

def test_positive_bundle_prepares():
    prepared = _prepare()
    assert prepared.trial_id == TRIAL
    assert prepared.authorized_commit == COMMIT
    assert prepared.day_sequences["theta_0.5"] == ALL_DAYS
    assert prepared.traded_day_sets["theta_0.5"] == frozenset(TP_DAYS)


def test_missing_file_refused():
    b = _bundle()
    del b["MC_HANDOFF_E1_Base.jsonl"]
    with pytest.raises(mcc.MCInputError, match="bundle_exact_set"):
        _prepare(b)


def test_extra_file_refused_including_a_planted_grid_samples():
    b = _bundle()
    b["GRID_SAMPLES.json"] = b"{}"     # withheld artifact cannot self-admit
    with pytest.raises(mcc.MCInputError, match="bundle_exact_set"):
        _prepare(b)


def test_type_swapped_file_refused():
    b = _bundle()
    b["SEED_MANIFEST.json"] = b"not json at all"
    _refresh_manifest(b)
    with pytest.raises(Exception):     # json decode failure is a refusal
        _prepare(b)


def test_hash_mismatch_refused():
    b = _bundle()
    b["S0_REPORT.md"] = b"# tampered after manifest"
    with pytest.raises(mcc.MCInputError, match="bundle_hash_mismatch"):
        _prepare(b)


def test_independent_hash_expectation_refused_on_mismatch():
    with pytest.raises(mcc.MCInputError, match="bundle_hash_mismatch"):
        _prepare(expected_file_sha256={"S0_REPORT.md": "0" * 64})


def test_trial_id_mismatch_refused():
    b = _bundle()
    b["REGISTRY_AFTER_RUN_STARTED.json"] = json.dumps({
        "snapshot_before": {"trial_id": "S0-T999",
                            "authorized_commit": COMMIT}}).encode("utf-8")
    _refresh_manifest(b)
    with pytest.raises(mcc.MCInputError, match="trial_commit_binding"):
        _prepare(b)


def test_governance_commit_mismatch_refused():
    b = _bundle()
    _mutate_report(b, lambda r: r["governance"].__setitem__(
        "authorized_commit", "f" * 40))
    with pytest.raises(mcc.MCInputError, match="trial_commit_binding"):
        _prepare(b)


def test_axis_violation_refused():
    b = _bundle()
    rows = [_record_row(d, "E1", "Base", 50.0) for d in ALL_DAYS]
    rows[0]["engine"] = "E9"
    b["MC_HANDOFF_E1_Base.jsonl"] = "\n".join(
        json.dumps(r, sort_keys=True) for r in rows).encode("utf-8")
    _refresh_manifest(b)
    _mutate_report(b, lambda r: None)  # keep counts as-is; axis fails first
    with pytest.raises(mcc.MCInputError, match="axis_violation"):
        _prepare(b)


def test_seed_axis_violation_refused():
    b = _bundle()
    b["SEED_MANIFEST.json"] = json.dumps({
        "research_bootstrap_seeds": [7, 13, 99],
        "k_policy": "k_per_seed=200", "crn_scope":
        "shared_within_theta_engine_scenario"}).encode("utf-8")
    _refresh_manifest(b)
    with pytest.raises(mcc.MCInputError, match="seed_axis_violation"):
        _prepare(b)


def test_k_policy_violation_refused():
    b = _bundle()
    b["SEED_MANIFEST.json"] = json.dumps({
        "research_bootstrap_seeds": list(RESEARCH_BOOTSTRAP_SEEDS),
        "k_policy": "k_per_seed=100", "crn_scope":
        "shared_within_theta_engine_scenario"}).encode("utf-8")
    _refresh_manifest(b)
    with pytest.raises(mcc.MCInputError, match="k_policy_violation"):
        _prepare(b)


def test_duplicate_record_date_refused():
    b = _bundle()
    rows = [_record_row(ALL_DAYS[0], "E1", "Base", 50.0)] * 2
    b["MC_HANDOFF_E1_Base.jsonl"] = "\n".join(
        json.dumps(r, sort_keys=True) for r in rows).encode("utf-8")
    _refresh_manifest(b)
    with pytest.raises(mcc.MCInputError, match="duplicate_record_date"):
        _prepare(b)


def test_tp_fp_overlap_refused():
    b = _bundle()
    # ascending fp list that overlaps tp on 2026-08-03
    _mutate_report(b, lambda r: r["oracle_daily"]["theta_0.5"]
                   ["day_universe"].__setitem__(
                       "fp_days", sorted(list(FP_DAYS) + [TP_DAYS[0]])))
    with pytest.raises(mcc.MCInputError, match="tp_fp_overlap"):
        _prepare(b)


def test_within_list_duplicate_refused_by_strict_ascending():
    """A duplicated day violates STRICT ascending first (review H3: order
    violations refuse, never repair)."""
    b = _bundle()
    _mutate_report(b, lambda r: r["oracle_daily"]["theta_0.5"]
                   ["day_universe"].__setitem__(
                       "tp_days", sorted(list(TP_DAYS) + [TP_DAYS[0]])))
    with pytest.raises(mcc.MCInputError, match="day_sequence_not_ascending"):
        _prepare(b)


def test_realized_count_mismatch_refused():
    b = _bundle()
    _mutate_report(b, lambda r: r["mc_handoff_manifest"]["counts"]["E1"]
                   ["Base"].__setitem__("n_records", 999))
    with pytest.raises(mcc.MCInputError, match="realized_count_mismatch"):
        _prepare(b)


def test_frozen_method_drift_refused(monkeypatch):
    from itsf import guards as g
    fake = dict(g.FROZEN_HASHES)
    fake["MC_METHOD_SPEC.md"] = "0" * 64
    monkeypatch.setattr(g, "FROZEN_HASHES", fake)
    with pytest.raises(mcc.MCInputError, match="frozen_method_drift"):
        _prepare()


def test_missing_authorization_snapshot_refused():
    with pytest.raises(mcc.MCInputError, match="authorization_snapshot"):
        mcc.prepare_mc_input(_bundle(), authorization_snapshot={},
                             calendar=_calendar())


# --- exposure freeze (R14) --------------------------------------------------

def test_prepared_input_is_immutable_and_source_free():
    prepared = _prepare()
    with pytest.raises((AttributeError, TypeError, dataclasses.FrozenInstanceError)):
        prepared.trial_id = "X"                       # type: ignore
    with pytest.raises(TypeError):
        prepared.records[("E1", "Base")]["2099-01-01"] = None  # type: ignore
    # no repository path or handle travels on the prepared object
    for f in dataclasses.fields(prepared):
        assert "path" not in f.name and "dir" not in f.name


def test_computation_never_rereads_the_bundle_after_prepare():
    bundle = _bundle()
    prepared = mcc.prepare_mc_input(bundle,
                                    authorization_snapshot=_snapshot(),
                                    calendar=_calendar())
    bundle.clear()                    # the source is GONE post-exposure
    res = mcc.run_epistemic(prepared, platform="topstep", engine="E1",
                            scenario="Conservative", channel="theta_0.5",
                            B=2, master_seed=7)
    assert len(res.world_means) == 2  # ran entirely off the prepared object


# --- epistemic / aleatoric separation (R9) ----------------------------------

def _epi(prepared, platform="topstep", engine="E1", scenario="Conservative",
         B=3, seed=7):
    return mcc.run_epistemic(prepared, platform=platform, engine=engine,
                             scenario=scenario, channel="theta_0.5", B=B,
                             master_seed=seed)


def test_epistemic_uses_world_level_means_and_crn():
    prepared = _prepare()
    a = _epi(prepared)
    b = _epi(prepared)                       # same args -> identical worlds
    assert a.world_means == b.world_means    # CRN by construction
    assert a.p5 <= a.median <= a.p95


def test_non_frozen_master_seed_refused():
    prepared = _prepare()
    with pytest.raises(ValueError, match="master_seed"):
        _epi(prepared, seed=42)


def test_platform_variant_missing_refused():
    prepared = _prepare()
    with pytest.raises(mcc.MCInputError, match="axis_violation"):
        _epi(prepared, platform="ftmo")


def test_aleatoric_is_reported_separately_and_cannot_enter_go_gate():
    prepared = _prepare()
    al = mcc.run_aleatoric(prepared, platform="topstep", engine="E1",
                           scenario="Conservative", channel="theta_0.5")
    assert len(al.attempt_monthly_evs) == \
        len(prepared.calendar.first_month_offsets)
    stress = _epi(prepared, scenario="Stress")
    with pytest.raises(mcc.MCInputError, match="aleatoric_leak"):
        mcc.epistemic_go_gate_input(al, stress, feasible=True)  # type: ignore


def test_cross_combo_stitching_refused():
    prepared = _prepare()
    cons_lucid = _epi(prepared, platform="lucid")
    stress_topstep = _epi(prepared, platform="topstep", scenario="Stress")
    with pytest.raises(mcc.MCInputError, match="cross_combo_stitching"):
        mcc.epistemic_go_gate_input(cons_lucid, stress_topstep,
                                    feasible=True)


def test_scenario_role_violation_refused():
    prepared = _prepare()
    base = _epi(prepared, scenario="Base")
    stress = _epi(prepared, scenario="Stress")
    with pytest.raises(mcc.MCInputError, match="scenario_role"):
        mcc.epistemic_go_gate_input(base, stress, feasible=True)


def test_integer_position_sizing_is_floored():
    from itsf.mc.account import n_micros
    n = n_micros(100.0, 33.0, 10)
    assert isinstance(n, int) and n == 3   # floor(100/33), never fractional


# --- convergence + verdict (R10 / R7) ---------------------------------------

def _conv(ok=True):
    doubled = {"B": "GO", "M": "GO", "K": "GO" if ok else "STOP"}
    return mcc.convergence_check(
        verdict_base="GO", verdicts_doubled=doubled,
        verdicts_by_seed={7: "GO", 13: "GO", 31: "GO"},
        quantiles_base={"p5": 10.0}, quantiles_doubled={"p5": 12.0},
        mcse_ok=True)


def _full_grid(prepared, feasible=True):
    primary = {}
    for platform, policy in mcc.PRIMARY_COMBOS:
        for engine in mcc.ENGINES:
            cons = _epi(prepared, platform=platform, engine=engine)
            stress = _epi(prepared, platform=platform, engine=engine,
                          scenario="Stress")
            primary[f"{platform}|{engine}|{policy}"] = \
                mcc.epistemic_go_gate_input(cons, stress, feasible=feasible)
    return primary


def test_unconverged_input_refuses_verdict():
    prepared = _prepare()
    with pytest.raises(mcc.MCNotConverged):
        mcc.verdict_or_refuse(_full_grid(prepared), _conv(ok=False))


def test_partial_primary_grid_refused():
    """Review H2: an E1-only (or any subset) grid can never reach the
    verdict table — STOP's universal and beta's first arm need E2."""
    prepared = _prepare()
    grid = _full_grid(prepared)
    del grid["topstep|E2|P2"]
    with pytest.raises(mcc.MCInputError, match="primary_grid_coverage"):
        mcc.verdict_or_refuse(grid, _conv())


def test_mislabelled_grid_entry_refused():
    prepared = _prepare()
    grid = _full_grid(prepared)
    grid["lucid|E1|P2"], grid["topstep|E1|P2"] = \
        grid["topstep|E1|P2"], grid["lucid|E1|P2"]
    with pytest.raises(mcc.MCInputError, match="primary_grid_label"):
        mcc.verdict_or_refuse(grid, _conv())


def test_quantile_drift_tolerance_is_max_25usd_or_5pct():
    doubled = {"B": "GO", "M": "GO", "K": "GO"}
    seeds = {7: "GO", 13: "GO", 31: "GO"}
    rep = mcc.convergence_check(
        verdict_base="GO", verdicts_doubled=doubled,
        verdicts_by_seed=seeds,
        quantiles_base={"p5": 1000.0}, quantiles_doubled={"p5": 1049.0},
        mcse_ok=True)
    assert rep.quantile_drift_ok           # 49 < max(25, 50)
    rep2 = mcc.convergence_check(
        verdict_base="GO", verdicts_doubled=doubled,
        verdicts_by_seed=seeds, quantiles_base={"p5": 100.0},
        quantiles_doubled={"p5": 140.0}, mcse_ok=True)
    assert not rep2.quantile_drift_ok      # 40 > max(25, 5)


def test_seed_category_disagreement_blocks_convergence():
    rep = mcc.convergence_check(
        verdict_base="GO",
        verdicts_doubled={"B": "GO", "M": "GO", "K": "GO"},
        verdicts_by_seed={7: "GO", 13: "STOP", 31: "GO"},
        quantiles_base={"p5": 1.0}, quantiles_doubled={"p5": 1.0},
        mcse_ok=True)
    assert not rep.converged


def test_single_seed_run_cannot_claim_seed_agreement():
    """Review M1: rule (b) needs EXACTLY the frozen 7/13/31 set."""
    with pytest.raises(mcc.MCInputError, match="seed_set_violation"):
        mcc.convergence_check(
            verdict_base="GO",
            verdicts_doubled={"B": "GO", "M": "GO", "K": "GO"},
            verdicts_by_seed={7: "GO"},
            quantiles_base={"p5": 1.0}, quantiles_doubled={"p5": 1.0},
            mcse_ok=True)


def test_missing_doubling_axis_refused():
    """Review M1: rule (a) doubles B, M and K EACH — a B-only doubling
    cannot claim rule (a)."""
    with pytest.raises(mcc.MCInputError, match="doubling_axes_violation"):
        mcc.convergence_check(
            verdict_base="GO", verdicts_doubled={"B": "GO"},
            verdicts_by_seed={7: "GO", 13: "GO", 31: "GO"},
            quantiles_base={"p5": 1.0}, quantiles_doubled={"p5": 1.0},
            mcse_ok=True)


def test_empty_quantile_comparison_refused():
    """Review M1: rule (c) may never pass vacuously."""
    with pytest.raises(mcc.MCInputError, match="quantile_comparison_empty"):
        mcc.convergence_check(
            verdict_base="GO",
            verdicts_doubled={"B": "GO", "M": "GO", "K": "GO"},
            verdicts_by_seed={7: "GO", 13: "GO", 31: "GO"},
            quantiles_base={}, quantiles_doubled={}, mcse_ok=True)


def test_invalid_verdict_category_refused():
    with pytest.raises(mcc.MCInputError, match="verdict_category_invalid"):
        mcc.convergence_check(
            verdict_base="MAYBE",
            verdicts_doubled={"B": "MAYBE", "M": "MAYBE", "K": "MAYBE"},
            verdicts_by_seed={7: "MAYBE", 13: "MAYBE", 31: "MAYBE"},
            quantiles_base={"p5": 1.0}, quantiles_doubled={"p5": 1.0},
            mcse_ok=True)


# --- review H1/H3/M2/M3/M5 regression negatives -----------------------------

def test_worlds_fill_every_template_slot():
    """Review H1: with a template longer than the day pool, every slot
    must still be fillable — no structurally dead tail."""
    prepared = mcc.prepare_mc_input(_bundle(),
                                    authorization_snapshot=_snapshot(),
                                    calendar=_calendar(n_days=17))
    from itsf.mc import bootstrap as mb
    worlds = mb.build_worlds(prepared.day_sequences["theta_0.5"], 4, 7,
                             length=len(prepared.calendar.days))
    pool = set(prepared.day_sequences["theta_0.5"])
    tail_draws = {w[-1] for w in worlds} | {w[10] for w in worlds}
    assert all(len(w) == 17 for w in worlds)
    assert tail_draws <= pool and tail_draws   # tail slots really draw


def test_unsorted_day_universe_refused():
    b = _bundle()
    _mutate_report(b, lambda r: r["oracle_daily"]["theta_0.5"]
                   ["day_universe"].__setitem__(
                       "tp_days", list(reversed(TP_DAYS))))
    with pytest.raises(mcc.MCInputError, match="day_sequence_not_ascending"):
        _prepare(b)


def test_cross_scenario_record_drift_refused():
    """Review H3: a scenario-selective record omission (with counts and
    manifest regenerated consistently) must refuse at the record-set
    consistency check, never become silent no-trade days."""
    b = _bundle()
    rows = [_record_row(d, "E1", "Stress", 80.0) for d in ALL_DAYS[:-1]]
    b["MC_HANDOFF_E1_Stress.jsonl"] = "\n".join(
        json.dumps(r, sort_keys=True) for r in rows).encode("utf-8")
    _mutate_report(b, lambda r: r["mc_handoff_manifest"]["counts"]["E1"]
                   ["Stress"].__setitem__("n_records", len(rows)))
    with pytest.raises(mcc.MCInputError, match="record_set_drift"):
        _prepare(b)


def test_manifest_missing_coverage_refused():
    """Review M2: a manifest that silently omits a file's digest is a
    refusal, not a vacuous pass."""
    b = _bundle()
    lines = [json.loads(l) for l in
             b["manifest.jsonl"].decode("utf-8").splitlines()]
    lines = [l for l in lines if l["relative_path"] != "S0_REPORT.md"]
    b["manifest.jsonl"] = "\n".join(
        json.dumps(l, sort_keys=True) for l in lines).encode("utf-8")
    with pytest.raises(mcc.MCInputError, match="bundle_manifest_coverage"):
        _prepare(b)


def test_drifted_k_2000_refused():
    """Review M3: substring matching admitted k_per_seed=2000."""
    b = _bundle()
    b["SEED_MANIFEST.json"] = json.dumps({
        "research_bootstrap_seeds": list(RESEARCH_BOOTSTRAP_SEEDS),
        "k_policy": "k_per_seed=2000;k_start_index=0",
        "crn_scope": "shared_within_theta_engine_scenario",
    }).encode("utf-8")
    _refresh_manifest(b)
    with pytest.raises(mcc.MCInputError, match="k_policy_violation"):
        _prepare(b)


def test_tp_day_without_record_refused():
    b = _bundle()
    _mutate_report(b, lambda r: r["oracle_daily"]["theta_0.5"]
                   ["day_universe"].__setitem__(
                       "tp_days", list(TP_DAYS) + ["2026-08-10"]))
    with pytest.raises(mcc.MCInputError, match="tp_day_without_record"):
        _prepare(b)


def test_structurally_invalid_calendar_refused():
    days = (TemplateDay(day_id="T0", cal_offset=0),
            TemplateDay(day_id="T0", cal_offset=1))     # duplicate id
    bad = mcc.TemplateCalendar(days=days, first_month_offsets=(0,))
    with pytest.raises(mcc.MCInputError, match="calendar_invalid"):
        mcc.prepare_mc_input(_bundle(), authorization_snapshot=_snapshot(),
                             calendar=bad)


def test_record_leaf_sequences_are_immutable():
    """Review M4: mtm arrays become tuples on the prepared object."""
    prepared = _prepare()
    rec = prepared.records[("E1", "Base")][ALL_DAYS[0]]
    assert isinstance(rec.mtm_close_pnl_1m, tuple)
    assert isinstance(rec.mtm_adverse_pnl_1m, tuple)


# --- authorization gate (R13) -----------------------------------------------

def test_public_real_runner_refuses_deterministically():
    with pytest.raises(McConsumerAbsent, match="NOT authorized"):
        mcc.run_real_mc()


def test_lookalike_registry_token_cannot_open_the_gate():
    text = "| 99 | 2026-01-01 | **MC_RUN_AUTHORIZED** | " + "a" * 40 + \
        " | Aaron | fake |"
    with pytest.raises(McConsumerAbsent, match="refusal stands"):
        mcc.authorize_real_mc(text)


# --- full synthetic positive path (prompt PHASE E final case) ---------------

def test_full_synthetic_production_path():
    prepared = _prepare()
    primary = _full_grid(prepared)         # the FULL frozen verdict grid
    al = mcc.run_aleatoric(prepared, platform="topstep", engine="E1",
                           scenario="Conservative", channel="theta_0.5")
    assert al.attempt_monthly_evs          # aleatoric reported separately
    candidate = mcc.render_verdict_inputs(prepared, primary, _conv(ok=True))
    assert candidate["schema"] == "mc_verdict_inputs.v1"
    assert candidate["trial_id"] == TRIAL
    assert candidate["verdict"]["category"] in ("STOP", "GO", "beta",
                                                "alpha")
    assert set(candidate["primary"]) == set(mcc.PRIMARY_VERDICT_GRID)
    assert candidate["convergence"]["a_category_stable_under_doubling"]
    assert set(candidate["bundle_file_sha256"]) == set(mcc.BUNDLE_EXACT_SET)
    assert candidate["seeds"] == list(RESEARCH_BOOTSTRAP_SEEDS)
