"""DR-5 MC consumer behaviour battery (synthetic fixtures ONLY; R2.1).

Bundle battery, theta hard binding, gate honesty (feasibility
DECISION_REQUIRED), fixed-world aleatoric, real-runner refusals.
Convergence-provenance and MCSE tests live in
tests/test_mc_convergence_provenance.py; custody/calendar tests in
tests/test_mc_custody_calendar.py."""
from __future__ import annotations

import dataclasses
import hashlib
import inspect
import json
import pathlib

import pytest

from conftest import make_trade_path
from itsf.contracts import RESEARCH_BOOTSTRAP_SEEDS
from itsf.mc import atoms as A
from itsf.mc import bootstrap as mb
from itsf.mc import consumer as mcc
from itsf.mc.orchestrator import TemplateDay
from itsf.s0.handoff import McConsumerAbsent

REPO = pathlib.Path(__file__).resolve().parents[1]
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
    """MIGRATED TO N01 AND STRENGTHENED.

    The historical CRN assertion compared the `world_means` of two
    IDENTICAL calls, which any deterministic function passes. Under N01
    every atom carries its world's CONTENT DIGEST, so the frozen MC SS5
    CRN claim — the SAME worlds are reused across every
    (platform, engine, scenario) evaluated at the same
    (channel, B, master_seed) — is checkable directly, and is asserted at
    content level here. The feasibility scalars moved under `.metrics`
    (they are reduced from the same atoms as every other statistic)."""
    prepared = _prepare()
    a = _epi(prepared)
    b = _epi(prepared)
    assert a.world_means == b.world_means      # deterministic
    assert a.observations.observations_digest == \
        b.observations.observations_digest
    assert a.p5 <= a.median <= a.p95
    assert (a.B, a.M, a.master_seed) == (2, 2, 7)
    assert a.prepared_digest == mcc.prepared_digest(prepared)
    # CRN AT CONTENT LEVEL: identical world tables across the whole grid
    want = mcc.build_world_table(prepared, channel=PRIMARY, B=2,
                                 master_seed=7)
    want_digests = tuple(hashlib.sha256("|".join(w).encode("utf-8"))
                         .hexdigest() for w in want)
    assert a.observations.world_digests() == want_digests
    for platform in mcc.PLATFORMS:
        for engine in mcc.ENGINES:
            for scenario in ("Conservative", "Stress"):
                other = _epi(prepared, platform=platform, engine=engine,
                             scenario=scenario)
                assert other.observations.world_digests() == want_digests
    # a DIFFERENT seed must not reproduce them (CRN is seed-scoped)
    assert _epi(prepared, seed=13).observations.world_digests() != \
        want_digests
    fe = a.feasibility
    assert fe.gate_status == "RULED_ND2_ND3_2026-08-24"
    assert not hasattr(fe, "feasible")         # the R2 boolean is GONE
    assert "feasible" not in fe.metrics
    assert 0.0 <= fe.metrics["ambiguous_share"] <= 1.0
    assert fe.metrics["n_paths"] == a.B * a.M


def test_non_frozen_master_seed_refused():
    with pytest.raises(ValueError, match="master_seed"):
        _epi(_prepare(), seed=42)


def test_platform_variant_missing_refused():
    with pytest.raises(mcc.MCInputError, match="axis_violation"):
        _epi(_prepare(), platform="ftmo")


def test_conditional_aleatoric_binds_one_fixed_world():
    """MIGRATED: the conditional-aleatoric slice is now REDUCED from the
    same atom trace as the epistemic layer (it no longer re-executes
    lifecycles from a caller-handed world), so the caller NAMES a world
    index instead of supplying world content. The world-identity formula
    is still pinned to the exact sha256 of the drawn day sequence, and the
    slice must be the M attempts of THAT world."""
    prepared = _prepare()
    worlds = mb.build_worlds(prepared.day_sequences[PRIMARY], 2, 7,
                             length=len(prepared.calendar.days))
    obs = mcc.run_observation_set(
        prepared, run_label="base", platform="topstep", engine="E1",
        scenario="Conservative", channel=PRIMARY, B=2, master_seed=7)
    al = mcc.run_conditional_aleatoric(obs, world_index=0)
    assert len(al.attempt_monthly_evs) == \
        len(prepared.calendar.first_month_offsets) == obs.M
    assert al.world_digest == hashlib.sha256(
        "|".join(worlds[0]).encode("utf-8")).hexdigest()
    # the slice IS the trace's world-0 atoms, in phase order — not a
    # parallel re-execution that merely resembles them
    assert al.attempt_monthly_evs == tuple(
        a.monthly_prop_operating_ev
        for a in sorted(obs.atoms, key=lambda x: x.key)
        if a.world_index == 0)
    assert al.observations_digest == obs.observations_digest
    other = mcc.run_conditional_aleatoric(obs, world_index=1)
    assert other.world_digest == hashlib.sha256(
        "|".join(worlds[1]).encode("utf-8")).hexdigest()
    assert other.world_digest != al.world_digest


def test_aleatoric_refuses_partial_or_foreign_worlds(monkeypatch):
    """OBSOLETE BY CONSTRUCTION — the entry these counterexamples attacked
    is gone; the same defects are now unreachable by construction and the
    surviving guards are proven live.

    HISTORICAL COUNTEREXAMPLES (kept on the record): the R2.3
    `run_conditional_aleatoric(prepared, world=..., ...)` accepted world
    CONTENT from the caller and ran its OWN lifecycles over it — a parallel
    simulation nothing forced to agree with the epistemic run. Two attacks
    were closed there: a PARTIAL world (`world_length_mismatch`) and a
    FOREIGN world of days outside the channel pool (`world_membership`).

    N01 PHASE D1 deleted the parameter: worlds are built ONLY by
    `build_world_table` from (prepared, channel, B, master_seed), so
    neither a partial nor a foreign world has any way in — `world_membership`
    no longer exists as a code anywhere in the module. What replaces them:

      * `world_length_mismatch` survives inside `build_world_table` and is
        proven LIVE here by fault-injecting the world builder;
      * the foreign-content attack is answered one layer deeper and more
        strongly by `world_content_binding_mismatch`: every atom carries
        its world's CONTENT digest and it must equal the cold-rebuilt
        world table's entry, so a trace that claims world b while carrying
        another world's content refuses;
      * naming a world the trace does not contain refuses
        (`aleatoric_world_absent`), and handing over anything that is not
        an ObservationSet refuses (`aleatoric_source_invalid`)."""
    prepared = _prepare()
    sig = inspect.signature(mcc.run_conditional_aleatoric)
    assert list(sig.parameters) == ["observations", "world_index"]
    assert "world" not in sig.parameters and "prepared" not in sig.parameters
    src = (REPO / "src" / "itsf" / "mc" / "consumer.py").read_text(
        encoding="utf-8")
    assert "world_membership" not in src

    obs = mcc.run_observation_set(
        prepared, run_label="base", platform="topstep", engine="E1",
        scenario="Conservative", channel=PRIMARY, B=2, master_seed=7)
    with pytest.raises(mcc.MCInputError) as ei:
        mcc.run_conditional_aleatoric(obs, world_index=99)
    assert ei.value.code == "aleatoric_world_absent"
    with pytest.raises(mcc.MCInputError) as ei:
        mcc.run_conditional_aleatoric(list(ALL_DAYS), world_index=0)
    assert ei.value.code == "aleatoric_source_invalid"

    # foreign world CONTENT — the successor of `world_membership`
    forged = A.ObservationSet.from_atoms(
        [dataclasses.replace(a, world_digest="e" * 64) for a in obs.atoms],
        run_label=obs.run_label, platform=obs.platform, engine=obs.engine,
        scenario=obs.scenario, theta_channel=obs.theta_channel,
        sizing_policy=obs.sizing_policy, B=obs.B,
        master_seed=obs.master_seed, prepared_digest=obs.prepared_digest,
        lifecycle_config_digest=obs.lifecycle_config_digest,
        legal_phase_support=obs.legal_phase_support)
    worlds = mcc.build_world_table(prepared, channel=PRIMARY, B=2,
                                   master_seed=7)
    with pytest.raises(mcc.MCInputError) as ei:
        mcc._bind_world_content(forged, worlds)
    assert ei.value.code == "world_content_binding_mismatch"

    # PARTIAL world — the guard survives inside the world builder; fault
    # injection (test process only, auto-restored) proves it is live code
    monkeypatch.setattr(mcc.mc_bootstrap, "build_worlds",
                        lambda *a, **k: [list(ALL_DAYS)])
    with pytest.raises(mcc.MCInputError) as ei:
        mcc.build_world_table(prepared, channel=PRIMARY, B=1,
                              master_seed=7)
    assert ei.value.code == "world_length_mismatch"


def test_aleatoric_result_cannot_enter_go_gate():
    prepared = _prepare()
    obs = mcc.run_observation_set(
        prepared, run_label="base", platform="topstep", engine="E1",
        scenario="Conservative", channel=PRIMARY, B=1, master_seed=7)
    al = mcc.run_conditional_aleatoric(obs, world_index=0)
    stress = _epi(prepared, scenario="Stress")
    with pytest.raises(mcc.MCInputError, match="aleatoric_leak"):
        mcc.epistemic_go_gate_input(al, stress)      # type: ignore
    with pytest.raises(mcc.MCInputError, match="aleatoric_leak"):
        mcc.epistemic_go_gate_input(stress, al)      # type: ignore
    total = mcc.run_total_predictive(obs)
    with pytest.raises(mcc.MCInputError, match="aleatoric_leak"):
        mcc.epistemic_go_gate_input(total, stress)   # type: ignore


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
                       match="feasibility_gate_input_absent"):
        mcc.epistemic_go_gate_input(
            _epi(prepared), _epi(prepared, scenario="Stress"))


def test_no_public_surface_accepts_a_feasibility_boolean():
    import inspect
    sig = inspect.signature(mcc.epistemic_go_gate_input)
    # No parameter named `feasible` -- the gate takes composed EVIDENCE.
    # A bare boolean is refused at runtime too
    # (test_mc_feasibility_composition), because `True` carries no gate
    # outcomes and lets a caller assert what nothing measured.
    assert "feasible" not in sig.parameters
    assert "feasibility" in sig.parameters
    assert mcc.FEASIBILITY_GATE_STATUS == "RULED_ND2_ND3_2026-08-24"


def test_hand_built_verdict_inputs_have_no_callable_entry():
    """R2.2 PHASE D (Codex counterexample): a hand-made positive
    VerdictInput grid has NO entry into the consumer's verdict/seal path —
    the old primary_inputs surfaces are gone and no public consumer
    function accepts VerdictInput objects.

    MIGRATED AND STRENGTHENED. N01 PHASE D4 removed the LAST caller-built
    evidence object on this path: `m_support_certificate` was a parameter
    of both the seal entry and `convergence_from_evidence`, so a
    hand-assembled 'complete support' proof could be handed in. The
    certificate is now DERIVED from the atom trace inside convergence, and
    neither entry accepts one — so the seal signature is exactly the four
    real inputs and nothing else."""
    import inspect
    assert not hasattr(mcc, "verdict_or_refuse")
    assert not hasattr(mcc, "render_verdict_inputs")
    for name, fn in vars(mcc).items():
        if name.startswith("_") or not callable(fn) \
                or not getattr(fn, "__module__", "").endswith("consumer"):
            continue
        try:
            params = inspect.signature(fn).parameters
        except (TypeError, ValueError):
            continue
        assert "primary_inputs" not in params, name
        # no consumer entry accepts a caller-built support certificate
        assert "m_support_certificate" not in params, name
        assert "certificate" not in params, name
    sig = inspect.signature(mcc.verdict_and_seal_from_evidence)
    assert set(sig.parameters) == {"prepared", "base", "doubled_by_axis",
                                   "seed_runs"}
    conv = inspect.signature(mcc.convergence_from_evidence)
    assert set(conv.parameters) == {"base", "doubled_by_axis", "seed_runs",
                                    "prepared"}
    assert conv.parameters["prepared"].default is inspect.Parameter.empty
    # the certificate type still exists, but ONLY as the derivation's
    # output — its sole producer is derive_support_certificate(base,
    # prepared), which takes the real trace and the prepared authority
    assert list(inspect.signature(
        mcc.derive_support_certificate).parameters) == ["base", "prepared"]


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
                       match="feasibility_gate_input_absent"):
        mcc.epistemic_go_gate_input(res, _epi(prepared, scenario="Stress"))
