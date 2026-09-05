"""R2.2 integration battery (MAIN-AGENT OWNED; synthetic fixtures only).

The three Codex counterexamples of the self-authenticating-evidence round,
proven closed end-to-end, plus the single-source verdict path and the
rooted custody chain."""
from __future__ import annotations

import dataclasses
import hashlib
import json

import pytest

from conftest import make_trade_path
from itsf.contracts import RESEARCH_BOOTSTRAP_SEEDS
from itsf.mc import consumer as mcc
from itsf.mc.orchestrator import TemplateDay
from itsf.s0.report import record_to_formal_dict

TRIAL = "S0-T001"
COMMIT = "876c1b74131b4ab1a89dce433ecce646ba481f8c"
TP_DAYS = ("2026-08-03", "2026-08-05", "2026-08-07")
FP_DAYS = ("2026-08-04", "2026-08-06")
ALL_DAYS = tuple(sorted(TP_DAYS + FP_DAYS))
PRIMARY = mcc.PRIMARY_THETA_CHANNEL


def _record_row(date, engine, scn, pnl):
    rec = make_trade_path([pnl / 2, pnl], date=date, engine=engine,
                          final=pnl)
    # S0's OWN publisher, not `asdict`: a sealed line carries the
    # PUBLISHED §10.1 names (entry_timestamp/exit_timestamp), and a
    # fixture that emits the internal ones is producing something S0
    # would never seal. Measured 2026-09-05 -- that gap is exactly
    # what let `record_schema_violation` reach the first real run.
    row = record_to_formal_dict(rec)
    row["cost_scenario"] = scn
    return row


def _calendar(n_days=8, n_offsets=2):
    days = tuple(TemplateDay(day_id=f"T{i:03d}", cal_offset=i)
                 for i in range(n_days))
    return mcc.TemplateCalendar(days=days,
                                first_month_offsets=tuple(range(n_offsets)))


def _bundle(pnl=80.0):
    files, counts = {}, {}
    for e in mcc.ENGINES:
        counts[e] = {}
        for s in mcc.SCENARIOS:
            rows = [_record_row(d, e, s, pnl) for d in ALL_DAYS]
            files[f"MC_HANDOFF_{e}_{s}.jsonl"] = "\n".join(
                json.dumps(r, sort_keys=True) for r in rows).encode("utf-8")
            counts[e][s] = {"n_records": len(rows)}
    files["S0_REPORT.json"] = json.dumps({
        "governance": {"trial_id": TRIAL, "authorized_commit": COMMIT},
        "oracle_daily": {PRIMARY: {"day_universe": {
            "tp_days": list(TP_DAYS), "fp_days": list(FP_DAYS)}}},
        "mc_handoff_manifest": {"counts": counts}}).encode("utf-8")
    files["S0_REPORT.md"] = b"# synthetic"
    files["HANDOFF_ADMISSION.json"] = b'{"admitted": ["SEED_MANIFEST.json"]}'
    files["SEED_MANIFEST.json"] = json.dumps({
        "research_bootstrap_seeds": list(RESEARCH_BOOTSTRAP_SEEDS),
        "k_policy": "k_per_seed=200;k_start_index=0",
        "crn_scope": "shared_within_theta_engine_scenario"}).encode("utf-8")
    files["REGISTRY_AFTER_RUN_STARTED.json"] = json.dumps({
        "snapshot_before": {"trial_id": TRIAL,
                            "authorized_commit": COMMIT}}).encode("utf-8")
    names = [n for n in sorted(files)]
    files["manifest.jsonl"] = "\n".join(
        json.dumps({"record_type": "file", "relative_path": n,
                    "file_sha256": hashlib.sha256(files[n]).hexdigest()},
                   sort_keys=True) for n in names).encode("utf-8")
    return files


def _prepare():
    b = _bundle()
    return mcc.prepare_mc_input_for_tests(
        b, authorization_snapshot={"trial_id": TRIAL,
                                   "authorized_commit": COMMIT,
                                   "event_sequence": 15},
        custody_authority=mcc.CustodyAuthority.for_tests(b),
        test_only_calendar=_calendar())


# --- Codex counterexample 1: forged epistemic statistics --------------------

def test_codex_ce1_forged_stats_refused_at_construction():
    """world_means=[-100]*B with declared p5/median/p95=+999 and
    mcse_ok=True must fail BEFORE any RunEvidence/convergence step —
    the type itself refuses (R2.2 PHASE C).

    MIGRATED TO N01 AND STRENGTHENED. R2.2/R2.3 forged a COHERENT triple
    (samples + quantiles + feasibility that agreed with each other) and
    the type had to notice the internal contradiction. Under N01 the type
    has exactly ONE input — the atom trace — and re-derives EVERY declared
    field from it, so both halves of the attack die independently:

      (a) the R2.2 counterexample verbatim (forged samples AND forged
          quantiles) refuses;
      (b) the strictly harder version — HONEST samples with ONLY the
          decision quantiles and mcse_ok forged, which no
          internal-consistency check could ever catch — refuses too.

    Both with the same code, at construction, before any RunEvidence
    exists."""
    prepared = _prepare()
    B = 4
    obs = mcc.run_observation_set(
        prepared, run_label="base", platform="topstep", engine="E1",
        scenario="Conservative", channel=PRIMARY, B=B, master_seed=7)
    feas = mcc.FeasibilityEvidence.from_observations(obs)
    honest = mcc._epistemic_derived(obs)
    assert len(honest["world_means"]) == B

    # (a) the R2.2 counterexample verbatim
    with pytest.raises(mcc.MCInputError,
                       match="epistemic_derived_stats_mismatch"):
        mcc.EpistemicResult(
            observations=obs, feasibility=feas,
            world_means=(-100.0,) * B, within_world_ses=(0.0,) * B,
            p5=999.0, median=999.0, p95=999.0, mcse_ok=True,
            max_within_world_se=0.0, between_world_sd=0.0)

    # (b) honest samples, forged decision quantiles only
    forged = dict(honest)
    forged.update(p5=999.0, median=999.0, p95=999.0, mcse_ok=True)
    with pytest.raises(mcc.MCInputError,
                       match="epistemic_derived_stats_mismatch"):
        mcc.EpistemicResult(observations=obs, feasibility=feas, **forged)

    # the honest construction is the ONLY one that survives
    good = mcc.EpistemicResult(observations=obs, feasibility=feas,
                               **honest)
    assert good.p5 <= good.median <= good.p95


def test_codex_ce1_replace_of_any_derived_stat_refused():
    prepared = _prepare()
    res = mcc.run_epistemic(prepared, platform="topstep", engine="E1",
                            scenario="Conservative", channel=PRIMARY,
                            B=2, master_seed=7)
    for field_name, forged in (("p5", 999.0), ("median", 999.0),
                               ("p95", 999.0), ("mcse_ok", not res.mcse_ok),
                               ("between_world_sd", 123.0),
                               ("max_within_world_se", -1.0)):
        with pytest.raises(mcc.MCInputError):
            dataclasses.replace(res, **{field_name: forged})


def test_epistemic_carries_complete_within_world_ses():
    prepared = _prepare()
    res = mcc.run_epistemic(prepared, platform="topstep", engine="E1",
                            scenario="Conservative", channel=PRIMARY,
                            B=3, master_seed=7)
    assert len(res.within_world_ses) == res.B == 3
    assert res.max_within_world_se == max(res.within_world_ses)


# --- Codex counterexample 2: hand-made VerdictInputs have no entry ----------

def test_codex_ce2_verdict_path_is_single_source():
    """The seal/verdict path derives Primary quantiles EXCLUSIVELY from
    base.results; the reduction refuses at the unruled feasibility gate
    today (CHECKPOINT0_VERDICT_REACHABLE=NO) — and there is no other
    callable path (surface scan lives in test_mc_consumer).

    B-PROV: the SEAL entry now refuses this TEST_ONLY-certified prepared
    input at the custody boundary before it can reduce anything, so the
    single-source reduction claim is asserted directly on
    `_reduce_primary_from_base` — which is where the feasibility gate
    always lived. Both refusals are checked; neither is a change to the
    feasibility rule."""
    prepared = _prepare()
    results = {}
    for platform, policy in mcc.PRIMARY_COMBOS:
        for engine in mcc.ENGINES:
            cons = mcc.run_epistemic(prepared, platform=platform,
                                     engine=engine,
                                     scenario="Conservative",
                                     channel=PRIMARY, B=2, master_seed=7)
            stress = mcc.run_epistemic(prepared, platform=platform,
                                       engine=engine, scenario="Stress",
                                       channel=PRIMARY, B=2, master_seed=7)
            results[f"{platform}|{engine}|{policy}"] = (cons, stress)
    base = mcc.RunEvidence(run_label="base", axis="base", B=2, M=2,
                           K=prepared.k_per_seed, master_seed=7,
                           prepared_digest=mcc.prepared_digest(prepared),
                           results=results)
    with pytest.raises(mcc.MCInputError,
                       match="seal_test_only_prepared_input"):
        mcc.verdict_and_seal_from_evidence(
            prepared, base=base, doubled_by_axis={}, seed_runs={})
    with pytest.raises(mcc.MCInputError,
                       match="feasibility_gate_input_absent"):
        mcc._reduce_primary_from_base(base)


def test_codex_ce2_foreign_base_evidence_refused():
    prepared = _prepare()
    other = mcc.RunEvidence(run_label="base", axis="base", B=2, M=2,
                            K=200, master_seed=7,
                            prepared_digest="f" * 64, results={})
    with pytest.raises(mcc.MCInputError, match="provenance_mismatch"):
        mcc.verdict_and_seal_from_evidence(
            prepared, base=other, doubled_by_axis={}, seed_runs={})


# --- Codex counterexample 3: custody chain rooted ---------------------------

def test_codex_ce3_manual_production_authority_refused_everywhere():
    """A hand-built CustodyAuthority(test_only=False) has NO entry: the
    production prepare takes raw bytes only; the test entry refuses
    non-test authorities."""
    import inspect
    sig = inspect.signature(mcc.prepare_mc_input)
    assert "attestation_bytes" in sig.parameters
    assert "custody_authority" not in sig.parameters
    b = _bundle()
    forged = dataclasses.replace(mcc.CustodyAuthority.for_tests(b),
                                 test_only=False)
    with pytest.raises(mcc.MCInputError,
                       match="custody_authority_production_object"):
        mcc.prepare_mc_input_for_tests(
            b, authorization_snapshot={"trial_id": TRIAL,
                                       "authorized_commit": COMMIT},
            custody_authority=forged, test_only_calendar=_calendar())


def test_codex_ce3_synchronized_rewrite_fails_the_code_pin():
    """Rewriting attestation + bundle + manifest together still fails:
    the attestation digest is pinned in CODE (commit-bound)."""
    fake_attestation = (
        "TRIAL_ID=S0-T001\nAUTHORIZED_COMMIT=" + COMMIT + "\n"
        + "\n".join(f"| {n} | 1 | {'0' * 64} |"
                    for n in sorted(mcc.BUNDLE_EXACT_SET))).encode("utf-8")
    with pytest.raises(mcc.MCInputError,
                       match="custody_authority_source_digest_mismatch"):
        mcc.load_custody_authority_from_attestation(
            attestation_bytes=fake_attestation)
    with pytest.raises(mcc.MCInputError,
                       match="custody_authority_source_violation"):
        mcc.load_custody_authority_from_attestation(
            path="ops/SOMEWHERE_ELSE.md")


def test_codex_ce3_real_attestation_still_loads():
    auth = mcc.load_custody_authority_from_attestation()
    assert auth.test_only is False
    assert auth.trial_id == TRIAL
    assert auth.authorized_commit == COMMIT
    assert set(auth.file_sha256) == set(mcc.BUNDLE_EXACT_SET)
    assert auth.source_artifact_sha256 == mcc.ATTESTATION_SHA256_PINNED
