"""DR-5 MC consumer behaviour battery (synthetic fixtures ONLY; R2).

Every fixture is hand-built bytes — no sealed S0 value is read anywhere.
R2 additions: theta hard binding (S0 §7 L133), MANDATORY external custody
authority, evidence-computed convergence/feasibility (no caller-declared
booleans), deep immutability, fixed-world conditional aleatoric.

The M-doubling fixtures below exercise the convergence MACHINERY only —
the production semantics of "doubling an exhaustively enumerated M" is
DECISION_REQUIRED_M_AXIS and no production caller can assemble it."""
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
            # secondary channel: superset TP (theta_0.3 selects more days)
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


def _authority(bundle) -> dict:
    """External custody authority: per-file digests INCLUDING manifest.
    In production this comes from the blind attestation / archive
    inventory, never from the directory under review."""
    return {n: hashlib.sha256(b).hexdigest() for n, b in bundle.items()}


def _snapshot() -> dict:
    return {"trial_id": TRIAL, "authorized_commit": COMMIT,
            "event_sequence": 15, "nested": {"list": [1, 2]}}


def _prepare(bundle=None, authority=None, calendar=None):
    """Deep-check convenience: authority derived from the bundle AS GIVEN
    (custody passes; the deeper battery is what is under test). Custody
    tests pass a pre-tamper authority explicitly."""
    b = bundle if bundle is not None else _bundle()
    return mcc.prepare_mc_input(
        b, authorization_snapshot=_snapshot(),
        expected_file_sha256=authority if authority is not None
        else _authority(b),
        calendar=calendar if calendar is not None else _calendar())


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
    auth = _authority(b)
    del b["MC_HANDOFF_E1_Base.jsonl"]
    with pytest.raises(mcc.MCInputError, match="bundle_exact_set"):
        _prepare(b, authority=auth)


def test_extra_file_refused_including_a_planted_grid_samples():
    b = _bundle()
    b["GRID_SAMPLES.json"] = b"{}"
    with pytest.raises(mcc.MCInputError, match="bundle_exact_set"):
        _prepare(b, authority=_authority(_bundle()))


def test_type_swapped_file_refused():
    b = _bundle()
    auth = _authority(b)                       # pre-tamper custody
    b["SEED_MANIFEST.json"] = b"not json at all"
    _refresh_manifest(b)
    with pytest.raises(mcc.MCInputError, match="bundle_hash_mismatch"):
        _prepare(b, authority=auth)


def test_internal_manifest_mismatch_refused():
    b = _bundle()
    b["S0_REPORT.md"] = b"# tampered after manifest"   # manifest stale
    with pytest.raises(mcc.MCInputError, match="bundle_hash_mismatch"):
        _prepare(b, authority=_authority(b))


# --- R2 PHASE C: external custody authority ---------------------------------

def test_payload_plus_internal_manifest_rewrite_fails_external_custody():
    """THE attack the external authority exists for: payload AND internal
    manifest rewritten consistently — internal dual-pin passes, the
    external authority refuses."""
    b = _bundle()
    auth = _authority(b)                       # custody BEFORE tamper
    b["S0_REPORT.md"] = b"# attacker rewrote and re-manifested"
    _refresh_manifest(b)                       # internal pins now agree
    with pytest.raises(mcc.MCInputError, match="bundle_hash_mismatch"):
        _prepare(b, authority=auth)


def test_missing_external_digest_refused():
    b = _bundle()
    auth = _authority(b)
    del auth["S0_REPORT.md"]
    with pytest.raises(mcc.MCInputError,
                       match="custody_authority_keyset"):
        _prepare(b, authority=auth)


def test_extra_external_digest_refused():
    b = _bundle()
    auth = _authority(b)
    auth["EXTRA.json"] = "0" * 64
    with pytest.raises(mcc.MCInputError,
                       match="custody_authority_keyset"):
        _prepare(b, authority=auth)


def test_unpinned_manifest_in_authority_refused():
    b = _bundle()
    auth = _authority(b)
    auth["manifest.jsonl"] = None              # manifest must be pinned too
    with pytest.raises(mcc.MCInputError,
                       match="custody_authority_malformed"):
        _prepare(b, authority=auth)


def test_authority_is_mandatory():
    with pytest.raises(TypeError):
        mcc.prepare_mc_input(_bundle(), authorization_snapshot=_snapshot(),
                             calendar=_calendar())   # type: ignore


# --- deeper battery (unchanged classes, R2-consistent) ----------------------

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
        mcc.prepare_mc_input(b, authorization_snapshot={},
                             expected_file_sha256=_authority(b),
                             calendar=_calendar())


def test_structurally_invalid_calendar_refused():
    days = (TemplateDay(day_id="T0", cal_offset=0),
            TemplateDay(day_id="T0", cal_offset=1))
    bad = mcc.TemplateCalendar(days=days, first_month_offsets=(0,))
    with pytest.raises(mcc.MCInputError, match="calendar_invalid"):
        _prepare(calendar=bad)


# --- R2 PHASE F: deep immutability ------------------------------------------

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
    prepared = mcc.prepare_mc_input(bundle, authorization_snapshot=snap,
                                    expected_file_sha256=_authority(bundle),
                                    calendar=_calendar())
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


def test_epistemic_crn_and_actual_sample_mcse():
    prepared = _prepare()
    a = _epi(prepared)
    b = _epi(prepared)
    assert a.world_means == b.world_means      # CRN by construction
    assert a.p5 <= a.median <= a.p95
    assert a.B == 2 and a.master_seed == 7
    assert a.prepared_digest == mcc.prepared_digest(prepared)
    assert isinstance(a.max_within_world_se, float)
    assert isinstance(a.feasibility, mcc.FeasibilityEvidence)


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


# --- R2 PHASE B: theta hard binding -----------------------------------------

def test_secondary_theta_refused_even_when_all_green():
    """S0 §7 L133 (不得事后升格): theta_0.3 results — same machinery,
    everything green — must be deterministically refused from the
    Checkpoint-0 gate."""
    prepared = _prepare()
    cons = _epi(prepared, channel=SECONDARY)
    stress = _epi(prepared, scenario="Stress", channel=SECONDARY)
    assert cons.p5 <= cons.p95                 # the run itself is healthy
    with pytest.raises(mcc.MCInputError, match="theta_channel_not_primary"):
        mcc.epistemic_go_gate_input(cons, stress)


def test_primary_theta_same_input_enters_the_gate():
    prepared = _prepare()
    vi = mcc.epistemic_go_gate_input(
        _epi(prepared, channel=PRIMARY),
        _epi(prepared, scenario="Stress", channel=PRIMARY))
    assert vi.channel == PRIMARY


def test_verdict_gate_rechecks_channel(monkeypatch):
    """Defense in depth: even a VerdictInput hand-built with a secondary
    channel is refused at verdict_or_refuse."""
    from itsf.mc.verdict import VerdictInput
    prepared = _prepare()
    grid = {}
    for platform, policy in mcc.PRIMARY_COMBOS:
        for engine in mcc.ENGINES:
            grid[f"{platform}|{engine}|{policy}"] = VerdictInput(
                p5_cons=1.0, median_cons=2.0, median_stress=1.0,
                p95_cons=3.0, feasible=True, platform=platform,
                engine=engine, channel=SECONDARY)
    conv = _machinery_convergence(prepared)
    with pytest.raises(mcc.MCInputError, match="theta_channel_not_primary"):
        mcc.verdict_or_refuse(grid, conv)


# --- R2 PHASE E: evidence-computed convergence ------------------------------

def _run_evidence(prepared, *, label="base", axis="base", B=2, seed=7,
                  calendar=None, K=None):
    """Build RunEvidence from ACTUAL runs of the full Primary grid."""
    target = prepared if calendar is None else dataclasses.replace(
        prepared, calendar=calendar)
    results = {}
    for platform, policy in mcc.PRIMARY_COMBOS:
        for engine in mcc.ENGINES:
            cons = mcc.run_epistemic(target, platform=platform,
                                     engine=engine,
                                     scenario="Conservative",
                                     channel=PRIMARY, B=B,
                                     master_seed=seed)
            stress = mcc.run_epistemic(target, platform=platform,
                                       engine=engine, scenario="Stress",
                                       channel=PRIMARY, B=B,
                                       master_seed=seed)
            results[f"{platform}|{engine}|{policy}"] = (cons, stress)
    return mcc.RunEvidence(
        run_label=label, axis=axis, B=B,
        M=len(target.calendar.first_month_offsets),
        K=K if K is not None else target.k_per_seed,
        master_seed=seed,
        prepared_digest=mcc.prepared_digest(target), results=results)


def _machinery_convergence(prepared):
    """Full convergence evidence. The M-doubled run is a MACHINERY-ONLY
    fixture (doubled synthetic offset count); production cannot assemble
    it — DECISION_REQUIRED_M_AXIS."""
    base = _run_evidence(prepared)
    doubled = {
        "B": _run_evidence(prepared, label="double_B", axis="B", B=4),
        "M": _run_evidence(prepared, label="double_M", axis="M",
                           calendar=_calendar(n_days=8, n_offsets=4)),
        "K": _run_evidence(prepared, label="double_K", axis="K",
                           K=2 * prepared.k_per_seed),
    }
    seeds = {s: _run_evidence(prepared, label=f"seed_{s}", axis="seed",
                              seed=s) for s in RESEARCH_BOOTSTRAP_SEEDS}
    return mcc.convergence_from_evidence(base, doubled, seeds)


def test_convergence_computed_from_evidence_end_to_end():
    prepared = _prepare()
    rep = _machinery_convergence(prepared)
    assert set(rep.drift_by_axis) == {"B", "M", "K"}
    for axis, drift in rep.drift_by_axis.items():
        assert drift, axis                       # per-axis map, non-empty
    assert rep.category_same_across_seeds
    assert rep.mcse_ok in (True, False)          # computed, not declared


def test_m_axis_missing_refuses_convergence():
    """PRODUCTION reality: no legal M-doubled run exists
    (DECISION_REQUIRED_M_AXIS) — convergence must refuse without it."""
    prepared = _prepare()
    base = _run_evidence(prepared)
    doubled = {
        "B": _run_evidence(prepared, label="double_B", axis="B", B=4),
        "K": _run_evidence(prepared, label="double_K", axis="K",
                           K=2 * prepared.k_per_seed),
    }
    seeds = {s: _run_evidence(prepared, label=f"seed_{s}", axis="seed",
                              seed=s) for s in RESEARCH_BOOTSTRAP_SEEDS}
    with pytest.raises(mcc.MCInputError, match="doubling_axes_violation"):
        mcc.convergence_from_evidence(base, doubled, seeds)
    assert mcc.M_AXIS_DOUBLING_STATUS == "DECISION_REQUIRED_M_AXIS"


def test_provenance_mismatch_refused():
    prepared = _prepare()
    other = _prepare(_bundle(pnl=90.0))        # different bytes -> digest
    base = _run_evidence(prepared)
    doubled = {
        "B": _run_evidence(other, label="double_B", axis="B", B=4),
        "M": _run_evidence(prepared, label="double_M", axis="M",
                           calendar=_calendar(n_days=8, n_offsets=4)),
        "K": _run_evidence(prepared, label="double_K", axis="K",
                           K=2 * prepared.k_per_seed),
    }
    seeds = {s: _run_evidence(prepared, label=f"seed_{s}", axis="seed",
                              seed=s) for s in RESEARCH_BOOTSTRAP_SEEDS}
    with pytest.raises(mcc.MCInputError, match="provenance_mismatch"):
        mcc.convergence_from_evidence(base, doubled, seeds)


def test_doubling_scale_violation_refused():
    prepared = _prepare()
    base = _run_evidence(prepared)
    doubled = {
        "B": _run_evidence(prepared, label="double_B", axis="B", B=3),
        "M": _run_evidence(prepared, label="double_M", axis="M",
                           calendar=_calendar(n_days=8, n_offsets=4)),
        "K": _run_evidence(prepared, label="double_K", axis="K",
                           K=2 * prepared.k_per_seed),
    }
    seeds = {s: _run_evidence(prepared, label=f"seed_{s}", axis="seed",
                              seed=s) for s in RESEARCH_BOOTSTRAP_SEEDS}
    with pytest.raises(mcc.MCInputError, match="doubling_scale_violation"):
        mcc.convergence_from_evidence(base, doubled, seeds)


def test_axis_identity_swap_refused():
    prepared = _prepare()
    base = _run_evidence(prepared)
    b_run = _run_evidence(prepared, label="double_B", axis="B", B=4)
    k_run = _run_evidence(prepared, label="double_K", axis="K",
                          K=2 * prepared.k_per_seed)
    m_run = _run_evidence(prepared, label="double_M", axis="M",
                          calendar=_calendar(n_days=8, n_offsets=4))
    seeds = {s: _run_evidence(prepared, label=f"seed_{s}", axis="seed",
                              seed=s) for s in RESEARCH_BOOTSTRAP_SEEDS}
    with pytest.raises(mcc.MCInputError, match="axis_identity_mismatch"):
        mcc.convergence_from_evidence(
            base, {"B": k_run, "K": b_run, "M": m_run}, seeds)


def test_seed_identity_mismatch_refused():
    prepared = _prepare()
    base = _run_evidence(prepared)
    doubled = {
        "B": _run_evidence(prepared, label="double_B", axis="B", B=4),
        "M": _run_evidence(prepared, label="double_M", axis="M",
                           calendar=_calendar(n_days=8, n_offsets=4)),
        "K": _run_evidence(prepared, label="double_K", axis="K",
                           K=2 * prepared.k_per_seed),
    }
    seeds = {s: _run_evidence(prepared, label=f"seed_{s}", axis="seed",
                              seed=7)          # every run actually seed 7
             for s in RESEARCH_BOOTSTRAP_SEEDS}
    with pytest.raises(mcc.MCInputError, match="axis_identity_mismatch"):
        mcc.convergence_from_evidence(base, doubled, seeds)


def test_feasibility_is_computed_not_declared():
    """No public surface accepts a feasibility boolean any more: the gate
    signature has no such parameter and the value rides on evidence."""
    import inspect
    sig = inspect.signature(mcc.epistemic_go_gate_input)
    assert "feasible" not in sig.parameters
    prepared = _prepare()
    vi = mcc.epistemic_go_gate_input(
        _epi(prepared), _epi(prepared, scenario="Stress"))
    assert isinstance(vi.feasible, bool)       # derived from evidence


# --- verdict gate -----------------------------------------------------------

def test_partial_primary_grid_refused():
    prepared = _prepare()
    base = _run_evidence(prepared)
    grid = {cid: mcc.epistemic_go_gate_input(c, s)
            for cid, (c, s) in base.results.items()}
    del grid["topstep|E2|P2"]
    with pytest.raises(mcc.MCInputError, match="primary_grid_coverage"):
        mcc.verdict_or_refuse(grid, _machinery_convergence(prepared))


def test_public_real_runner_refuses_deterministically():
    with pytest.raises(McConsumerAbsent, match="NOT authorized"):
        mcc.run_real_mc()


def test_lookalike_registry_token_cannot_open_the_gate():
    text = "| 99 | 2026-01-01 | **MC_RUN_AUTHORIZED** | " + "a" * 40 + \
        " | Aaron | fake |"
    with pytest.raises(McConsumerAbsent, match="refusal stands"):
        mcc.authorize_real_mc(text)


# --- full synthetic chain (machinery-complete; production M stays blocked) --

def test_full_synthetic_production_path():
    prepared = _prepare()
    base = _run_evidence(prepared)
    grid = {cid: mcc.epistemic_go_gate_input(c, s)
            for cid, (c, s) in base.results.items()}
    conv = _machinery_convergence(prepared)
    worlds = mb.build_worlds(prepared.day_sequences[PRIMARY], 1, 7,
                             length=len(prepared.calendar.days))
    al = mcc.run_conditional_aleatoric(
        prepared, world=worlds[0], platform="topstep", engine="E1",
        scenario="Conservative", channel=PRIMARY)
    assert al.attempt_monthly_evs
    if not conv.converged:
        with pytest.raises(mcc.MCNotConverged):
            mcc.render_verdict_inputs(prepared, grid, conv)
        return
    candidate = mcc.render_verdict_inputs(prepared, grid, conv)
    assert candidate["schema"] == "mc_verdict_inputs.v2"
    assert candidate["primary_theta_channel"] == PRIMARY
    assert candidate["prepared_digest"] == mcc.prepared_digest(prepared)
    assert set(candidate["primary"]) == set(mcc.PRIMARY_VERDICT_GRID)
    for cell in candidate["primary"].values():
        assert cell["channel"] == PRIMARY
    assert candidate["verdict"]["category"] in ("STOP", "GO", "beta",
                                                "alpha")
