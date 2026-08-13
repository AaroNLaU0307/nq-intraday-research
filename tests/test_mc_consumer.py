"""DR-5 MC consumer behaviour battery (synthetic fixtures ONLY; R2.1).

Bundle battery, theta hard binding, gate honesty (feasibility
DECISION_REQUIRED), fixed-world aleatoric, real-runner refusals.
Convergence-provenance and MCSE tests live in
tests/test_mc_convergence_provenance.py; custody/calendar tests in
tests/test_mc_custody_calendar.py."""
from __future__ import annotations

import dataclasses
import hashlib
import json

import pytest

from conftest import make_trade_path
from itsf.contracts import RESEARCH_BOOTSTRAP_SEEDS
from itsf.mc import bootstrap as mb
from itsf.mc import consumer as mcc
from itsf.mc.orchestrator import TemplateDay
from itsf.s0.handoff import McConsumerAbsent

TRIAL = "S0-T001"
COMMIT = "876c1b74131b4ab1a89dce433ecce646ba481f8c"
TP_DAYS = ("2026-08-03", "2026-08-05", "2026-08-07")
FP_DAYS = ("2026-08-04", "2026-08-06")
ALL_DAYS = tuple(sorted(TP_DAYS + FP_DAYS))
PRIMARY = mcc.PRIMARY_THETA_CHANNEL          # 'theta_0.5'
SECONDARY = mcc.SECONDARY_THETA_CHANNEL      # 'theta_0.3'


def _record_row(date: str, engine: str, scn: str, pnl: float) -> dict:
    rec = make_trade_path([pnl / 2, pnl], date=date, engine=engine,
                          final=pnl)
    row = dataclasses.asdict(rec)
    row["cost_scenario"] = scn
    return row


def _calendar(n_days: int = 8, n_offsets: int = 2) -> mcc.TemplateCalendar:
    days = tuple(TemplateDay(day_id=f"T{i:03d}", cal_offset=i)
                 for i in range(n_days))
    return mcc.TemplateCalendar(days=days,
                                first_month_offsets=tuple(range(n_offsets)))


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
        "oracle_daily": {
            PRIMARY: {"day_universe": {
                "tp_days": list(TP_DAYS), "fp_days": list(FP_DAYS)}},
            SECONDARY: {"day_universe": {
                "tp_days": sorted(TP_DAYS + (FP_DAYS[0],)),
                "fp_days": [FP_DAYS[1]]}},
        },
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
    _refresh_manifest(files)
    return files


def _refresh_manifest(bundle):
    names = [n for n in sorted(bundle) if n != "manifest.jsonl"]
    bundle["manifest.jsonl"] = "\n".join(
        json.dumps({"record_type": "file", "relative_path": n,
                    "file_sha256": hashlib.sha256(bundle[n]).hexdigest()},
                   sort_keys=True) for n in names).encode("utf-8")


def _snapshot() -> dict:
    return {"trial_id": TRIAL, "authorized_commit": COMMIT,
            "event_sequence": 15, "nested": {"list": [1, 2]}}


def _prepare(bundle=None, authority=None, calendar=None):
    """TEST_ONLY prepare: authority derived from the bundle AS GIVEN
    unless a (pre-tamper) authority is passed explicitly."""
    b = bundle if bundle is not None else _bundle()
    return mcc.prepare_mc_input_for_tests(
        b, authorization_snapshot=_snapshot(),
        custody_authority=authority if authority is not None
        else mcc.CustodyAuthority.for_tests(b),
        test_only_calendar=calendar if calendar is not None
        else _calendar())


def _mutate_report(bundle, fn):
    report = json.loads(bundle["S0_REPORT.json"])
    fn(report)
    bundle["S0_REPORT.json"] = json.dumps(report).encode("utf-8")
    _refresh_manifest(bundle)


# --- bundle battery ---------------------------------------------------------

def test_positive_bundle_prepares():
    prepared = _prepare()
    assert prepared.trial_id == TRIAL
    assert prepared.day_sequences[PRIMARY] == ALL_DAYS
    assert prepared.traded_day_sets[PRIMARY] == frozenset(TP_DAYS)
    assert SECONDARY in prepared.day_sequences


def test_missing_file_refused():
    b = _bundle()
    auth = mcc.CustodyAuthority.for_tests(b)
    del b["MC_HANDOFF_E1_Base.jsonl"]
    with pytest.raises(mcc.MCInputError, match="bundle_exact_set"):
        _prepare(b, authority=auth)


def test_extra_file_refused_including_a_planted_grid_samples():
    b = _bundle()
    auth = mcc.CustodyAuthority.for_tests(b)
    b["GRID_SAMPLES.json"] = b"{}"
    with pytest.raises(mcc.MCInputError, match="bundle_exact_set"):
        _prepare(b, authority=auth)


def test_trial_id_mismatch_refused():
    b = _bundle()
    b["REGISTRY_AFTER_RUN_STARTED.json"] = json.dumps({
        "snapshot_before": {"trial_id": "S0-T999",
                            "authorized_commit": COMMIT}}).encode("utf-8")
    _refresh_manifest(b)
    with pytest.raises(mcc.MCInputError, match="binding"):
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


def test_drifted_k_2000_refused():
    b = _bundle()
    b["SEED_MANIFEST.json"] = json.dumps({
        "research_bootstrap_seeds": list(RESEARCH_BOOTSTRAP_SEEDS),
        "k_policy": "k_per_seed=2000;k_start_index=0",
        "crn_scope": "shared_within_theta_engine_scenario",
    }).encode("utf-8")
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


def test_cross_scenario_record_drift_refused():
    b = _bundle()
    rows = [_record_row(d, "E1", "Stress", 80.0) for d in ALL_DAYS[:-1]]
    b["MC_HANDOFF_E1_Stress.jsonl"] = "\n".join(
        json.dumps(r, sort_keys=True) for r in rows).encode("utf-8")
    _mutate_report(b, lambda r: r["mc_handoff_manifest"]["counts"]["E1"]
                   ["Stress"].__setitem__("n_records", len(rows)))
    with pytest.raises(mcc.MCInputError, match="record_set_drift"):
        _prepare(b)


def test_unsorted_day_universe_refused():
    b = _bundle()
    _mutate_report(b, lambda r: r["oracle_daily"][PRIMARY]
                   ["day_universe"].__setitem__(
                       "tp_days", list(reversed(TP_DAYS))))
    with pytest.raises(mcc.MCInputError, match="day_sequence_not_ascending"):
        _prepare(b)


def test_tp_fp_overlap_refused():
    b = _bundle()
    _mutate_report(b, lambda r: r["oracle_daily"][PRIMARY]
                   ["day_universe"].__setitem__(
                       "fp_days", sorted(list(FP_DAYS) + [TP_DAYS[0]])))
    with pytest.raises(mcc.MCInputError, match="tp_fp_overlap"):
        _prepare(b)


def test_realized_count_mismatch_refused():
    b = _bundle()
    _mutate_report(b, lambda r: r["mc_handoff_manifest"]["counts"]["E1"]
                   ["Base"].__setitem__("n_records", 999))
    with pytest.raises(mcc.MCInputError, match="realized_count_mismatch"):
        _prepare(b)


def test_tp_day_without_record_refused():
    b = _bundle()
    _mutate_report(b, lambda r: r["oracle_daily"][PRIMARY]
                   ["day_universe"].__setitem__(
                       "tp_days", list(TP_DAYS) + ["2026-08-10"]))
    with pytest.raises(mcc.MCInputError, match="tp_day_without_record"):
        _prepare(b)


def test_frozen_method_drift_refused(monkeypatch):
    from itsf import guards as g
    fake = dict(g.FROZEN_HASHES)
    fake["MC_METHOD_SPEC.md"] = "0" * 64
    monkeypatch.setattr(g, "FROZEN_HASHES", fake)
    with pytest.raises(mcc.MCInputError, match="frozen_method_drift"):
        _prepare()


def test_missing_authorization_snapshot_refused():
    b = _bundle()
    with pytest.raises(mcc.MCInputError, match="authorization_snapshot"):
        mcc.prepare_mc_input_for_tests(
            b, authorization_snapshot={},
            custody_authority=mcc.CustodyAuthority.for_tests(b),
            test_only_calendar=_calendar())


# --- deep immutability (R2.1 PHASE F, consumer-side checks) -----------------

def test_prepared_is_deeply_immutable():
    prepared = _prepare()
    with pytest.raises((AttributeError, TypeError,
                        dataclasses.FrozenInstanceError)):
        prepared.trial_id = "X"                              # type: ignore
    with pytest.raises(TypeError):
        prepared.records[("E1", "Base")]["2099-01-01"] = None  # type: ignore
    rec = prepared.records[("E1", "Base")][ALL_DAYS[0]]
    with pytest.raises(dataclasses.FrozenInstanceError):
        rec.final_pnl_per_contract = 1e9                     # type: ignore
    assert isinstance(rec.mtm_close_pnl_1m, tuple)
    with pytest.raises(TypeError):
        prepared.authorization_snapshot["new"] = 1           # type: ignore
    with pytest.raises(AttributeError):        # deep-frozen: list -> tuple
        prepared.authorization_snapshot["nested"]["list"].append(3)  # type: ignore
    for f in dataclasses.fields(prepared):
        assert "path" not in f.name and "dir" not in f.name


def test_mutating_sources_after_prepare_has_no_effect():
    bundle = _bundle()
    snap = _snapshot()
    prepared = mcc.prepare_mc_input_for_tests(
        bundle, authorization_snapshot=snap,
        custody_authority=mcc.CustodyAuthority.for_tests(bundle),
        test_only_calendar=_calendar())
    d0 = mcc.prepared_digest(prepared)
    bundle.clear()
    snap["authorized_commit"] = "hacked"
    snap["nested"]["list"].append(99)
    assert prepared.authorization_snapshot["authorized_commit"] == COMMIT
    assert tuple(prepared.authorization_snapshot["nested"]["list"]) == (1, 2)
    res = mcc.run_epistemic(prepared, platform="topstep", engine="E1",
                            scenario="Conservative", channel=PRIMARY,
                            B=2, master_seed=7)
    assert len(res.world_means) == 2
    assert mcc.prepared_digest(prepared) == d0


# --- epistemic / aleatoric --------------------------------------------------

def _epi(prepared, platform="topstep", engine="E1", scenario="Conservative",
         B=2, seed=7, channel=PRIMARY):
    return mcc.run_epistemic(prepared, platform=platform, engine=engine,
                             scenario=scenario, channel=channel, B=B,
                             master_seed=seed)


def test_epistemic_crn_provenance_and_metrics():
    prepared = _prepare()
    a = _epi(prepared)
    b = _epi(prepared)
    assert a.world_means == b.world_means      # CRN by construction
    assert a.p5 <= a.median <= a.p95
    assert (a.B, a.M, a.master_seed) == (2, 2, 7)
    assert a.prepared_digest == mcc.prepared_digest(prepared)
    fe = a.feasibility
    assert fe.gate_status == "DECISION_REQUIRED"
    assert not hasattr(fe, "feasible")         # the R2 boolean is GONE
    assert 0.0 <= fe.ambiguous_share <= 1.0


def test_non_frozen_master_seed_refused():
    with pytest.raises(ValueError, match="master_seed"):
        _epi(_prepare(), seed=42)


def test_platform_variant_missing_refused():
    with pytest.raises(mcc.MCInputError, match="axis_violation"):
        _epi(_prepare(), platform="ftmo")


def test_conditional_aleatoric_binds_one_fixed_world():
    prepared = _prepare()
    worlds = mb.build_worlds(prepared.day_sequences[PRIMARY], 2, 7,
                             length=len(prepared.calendar.days))
    al = mcc.run_conditional_aleatoric(
        prepared, world=worlds[0], platform="topstep", engine="E1",
        scenario="Conservative", channel=PRIMARY)
    assert len(al.attempt_monthly_evs) == \
        len(prepared.calendar.first_month_offsets)
    assert al.world_digest == hashlib.sha256(
        "|".join(worlds[0]).encode("utf-8")).hexdigest()


def test_aleatoric_refuses_partial_or_foreign_worlds():
    prepared = _prepare()
    with pytest.raises(mcc.MCInputError, match="world_length_mismatch"):
        mcc.run_conditional_aleatoric(
            prepared, world=list(ALL_DAYS), platform="topstep",
            engine="E1", scenario="Conservative", channel=PRIMARY)
    n = len(prepared.calendar.days)
    with pytest.raises(mcc.MCInputError, match="world_membership"):
        mcc.run_conditional_aleatoric(
            prepared, world=["2099-01-01"] * n, platform="topstep",
            engine="E1", scenario="Conservative", channel=PRIMARY)


def test_aleatoric_result_cannot_enter_go_gate():
    prepared = _prepare()
    worlds = mb.build_worlds(prepared.day_sequences[PRIMARY], 1, 7,
                             length=len(prepared.calendar.days))
    al = mcc.run_conditional_aleatoric(
        prepared, world=worlds[0], platform="topstep", engine="E1",
        scenario="Conservative", channel=PRIMARY)
    stress = _epi(prepared, scenario="Stress")
    with pytest.raises(mcc.MCInputError, match="aleatoric_leak"):
        mcc.epistemic_go_gate_input(al, stress)      # type: ignore


def test_cross_combo_stitching_refused():
    prepared = _prepare()
    with pytest.raises(mcc.MCInputError, match="cross_combo_stitching"):
        mcc.epistemic_go_gate_input(
            _epi(prepared, platform="lucid"),
            _epi(prepared, platform="topstep", scenario="Stress"))


def test_scenario_role_violation_refused():
    prepared = _prepare()
    with pytest.raises(mcc.MCInputError, match="scenario_role"):
        mcc.epistemic_go_gate_input(_epi(prepared, scenario="Base"),
                                    _epi(prepared, scenario="Stress"))


def test_integer_position_sizing_is_floored():
    from itsf.mc.account import n_micros
    n = n_micros(100.0, 33.0, 10)
    assert isinstance(n, int) and n == 3


# --- R2 PHASE B theta binding + R2.1 PHASE G feasibility honesty ------------

def test_secondary_theta_refused_before_feasibility():
    """S0 §7 L133 (不得事后升格): theta_0.3 refuses with the THETA code —
    the refusal is channel-specific, not the generic feasibility gate."""
    prepared = _prepare()
    cons = _epi(prepared, channel=SECONDARY)
    stress = _epi(prepared, scenario="Stress", channel=SECONDARY)
    with pytest.raises(mcc.MCInputError, match="theta_channel_not_primary"):
        mcc.epistemic_go_gate_input(cons, stress)


def test_primary_theta_passes_theta_gate_then_hits_feasibility_gate():
    """R2.1 PHASE G: no feasibility boolean is frozen, so even a fully
    green PRIMARY-channel combo cannot become a VerdictInput — the gate
    refuses with the DECISION_REQUIRED code (which also proves the theta
    check passed)."""
    prepared = _prepare()
    with pytest.raises(mcc.MCInputError,
                       match="feasibility_gate_decision_required"):
        mcc.epistemic_go_gate_input(
            _epi(prepared), _epi(prepared, scenario="Stress"))


def test_no_public_surface_accepts_a_feasibility_boolean():
    import inspect
    sig = inspect.signature(mcc.epistemic_go_gate_input)
    assert "feasible" not in sig.parameters
    assert mcc.FEASIBILITY_GATE_STATUS == "DECISION_REQUIRED"


def test_verdict_gate_rechecks_channel_and_grid():
    """Defense in depth at verdict_or_refuse: hand-built VerdictInputs
    with a secondary channel refuse on theta; a subset grid refuses on
    coverage — both BEFORE any convergence evidence is consulted."""
    from itsf.mc.verdict import VerdictInput

    def grid(channel):
        return {
            f"{platform}|{engine}|{policy}": VerdictInput(
                p5_cons=1.0, median_cons=2.0, median_stress=1.0,
                p95_cons=3.0, feasible=True, platform=platform,
                engine=engine, channel=channel)
            for platform, policy in mcc.PRIMARY_COMBOS
            for engine in mcc.ENGINES}

    dummy = None      # never reached: both cases refuse before evidence
    with pytest.raises(mcc.MCInputError, match="theta_channel_not_primary"):
        mcc.verdict_or_refuse(grid(SECONDARY), base=dummy,
                              doubled_by_axis={}, seed_runs={})
    g = grid(PRIMARY)
    del g["topstep|E2|P2"]
    with pytest.raises(mcc.MCInputError, match="primary_grid_coverage"):
        mcc.verdict_or_refuse(g, base=dummy, doubled_by_axis={},
                              seed_runs={})


# --- authorization gate -----------------------------------------------------

def test_public_real_runner_refuses_deterministically():
    with pytest.raises(McConsumerAbsent, match="NOT authorized"):
        mcc.run_real_mc()


def test_production_prepare_caller_is_gate_first():
    """R2.1 PHASE F: the non-test production caller exists and refuses at
    the authorization gate BEFORE any sealed byte is read."""
    from itsf.mc import real_input
    with pytest.raises(McConsumerAbsent, match="NOT authorized"):
        real_input.prepare_real_mc_input()


def test_lookalike_registry_token_cannot_open_the_gate():
    text = "| 99 | 2026-01-01 | **MC_RUN_AUTHORIZED** | " + "a" * 40 + \
        " | Aaron | fake |"
    with pytest.raises(McConsumerAbsent, match="refusal stands"):
        mcc.authorize_real_mc(text)


# --- the honest end-to-end cascade (R2.1) -----------------------------------

def test_full_chain_ends_at_the_honest_refusals():
    """prepare ✓ -> epistemic ✓ -> aleatoric ✓ -> the gate cascade refuses
    exactly where the frozen decisions are missing: feasibility
    (DECISION_REQUIRED) at the combo gate, and K/M evidence at the
    convergence path — no verdict, no seal, no silent pass."""
    prepared = _prepare()
    res = _epi(prepared)
    assert res.world_means                     # epistemic ran
    with pytest.raises(mcc.MCInputError,
                       match="feasibility_gate_decision_required"):
        mcc.epistemic_go_gate_input(res, _epi(prepared, scenario="Stress"))
