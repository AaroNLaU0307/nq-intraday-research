"""N01 / PHASE D3-D4-D6 — cold replay, dual reducers, M support, seal.

Synthetic fixtures ONLY (the same shape the DR-5 batteries use). No real
data, no real results, no registry or ledger writes.

Coverage map (PHASE G):
  A. the B-doubling world-prefix property is VERIFIED EMPIRICALLY against
     this repository's bootstrap before anything relies on it;
  B. positive end-to-end: prepared input -> atom trace -> cold replay ->
     bitwise agreement, plus the two-level digest tables;
  C. cold-replay negatives: divergence refuses the seal, and no caller
     conclusion (receipt / match / verified) can skip the replay;
  D. the two reducers are structurally independent (import-graph pin) and
     any disagreement refuses;
  E. M exhaustive-support certificate DERIVED from the trace, with a
     negative for every IR-29 refusal code;
  F. four-layer lifecycle_config_digest equality;
  G. REGRESSION RED LINES that must not move;
  H. BASELINE COUNTEREXAMPLES — the pre-N01 defects must stay dead.
"""
from __future__ import annotations

import ast
import dataclasses
import hashlib
import inspect
import json
import pathlib

import numpy as np
import pytest

from conftest import make_trade_path
from itsf.contracts import RESEARCH_BOOTSTRAP_SEEDS
from itsf.mc import atoms as A
from itsf.mc import bootstrap as mb
from itsf.mc import cold_reducer as CR
from itsf.mc import consumer as mcc
from itsf.mc.orchestrator import TemplateDay
from itsf.s0.handoff import McConsumerAbsent
from itsf.s0.report import record_to_formal_dict

REPO = pathlib.Path(__file__).resolve().parents[1]
TRIAL = "S0-T001"
COMMIT = "876c1b74131b4ab1a89dce433ecce646ba481f8c"
TP_DAYS = ("2026-08-03", "2026-08-05", "2026-08-07")
FP_DAYS = ("2026-08-04", "2026-08-06")
ALL_DAYS = tuple(sorted(TP_DAYS + FP_DAYS))
PRIMARY = mcc.PRIMARY_THETA_CHANNEL
SECONDARY = mcc.SECONDARY_THETA_CHANNEL


# --- synthetic bundle / prepared input -------------------------------------

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
    return mcc.TemplateCalendar(
        days=tuple(TemplateDay(day_id=f"T{i:03d}", cal_offset=i)
                   for i in range(n_days)),
        first_month_offsets=tuple(range(n_offsets)))


def _refresh_manifest(bundle):
    names = [n for n in sorted(bundle) if n != "manifest.jsonl"]
    bundle["manifest.jsonl"] = "\n".join(
        json.dumps({"record_type": "file", "relative_path": n,
                    "file_sha256": hashlib.sha256(bundle[n]).hexdigest()},
                   sort_keys=True) for n in names).encode("utf-8")


def _bundle(pnl=80.0):
    files = {}
    counts = {}
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
            PRIMARY: {"day_universe": {"tp_days": list(TP_DAYS),
                                       "fp_days": list(FP_DAYS)}},
            SECONDARY: {"day_universe": {
                "tp_days": sorted(TP_DAYS + (FP_DAYS[0],)),
                "fp_days": [FP_DAYS[1]]}}},
        "mc_handoff_manifest": {"counts": counts}}
    files["S0_REPORT.json"] = json.dumps(report).encode("utf-8")
    files["S0_REPORT.md"] = b"# synthetic"
    files["HANDOFF_ADMISSION.json"] = json.dumps({"admitted": []}).encode()
    files["SEED_MANIFEST.json"] = json.dumps({
        "research_bootstrap_seeds": list(RESEARCH_BOOTSTRAP_SEEDS),
        "k_policy": "k_per_seed=200;k_start_index=0",
        "crn_scope": "shared_within_theta_engine_scenario"}).encode()
    files["REGISTRY_AFTER_RUN_STARTED.json"] = json.dumps({
        "snapshot_before": {"trial_id": TRIAL,
                            "authorized_commit": COMMIT}}).encode()
    _refresh_manifest(files)
    return files


@pytest.fixture()
def prepared():
    b = _bundle()
    return mcc.prepare_mc_input_for_tests(
        b, authorization_snapshot={"trial_id": TRIAL,
                                   "authorized_commit": COMMIT},
        custody_authority=mcc.CustodyAuthority.for_tests(b),
        test_only_calendar=_calendar())


def _obs(prepared, *, run_label="base", platform="topstep", engine="E1",
         scenario="Conservative", B=2, seed=7):
    return mcc.run_observation_set(
        prepared, run_label=run_label, platform=platform, engine=engine,
        scenario=scenario, channel=PRIMARY, B=B, master_seed=seed)


def _evidence(prepared, *, run_label="base", axis="base", B=2, seed=7,
              K=200):
    results = {}
    for platform in ("lucid", "topstep"):
        for engine in ("E1", "E2"):
            cid = A.combo_label(platform, engine, "P2")
            cons = mcc.EpistemicResult.from_observations(_obs(
                prepared, run_label=run_label, platform=platform,
                engine=engine, scenario="Conservative", B=B, seed=seed))
            stress = mcc.EpistemicResult.from_observations(_obs(
                prepared, run_label=run_label, platform=platform,
                engine=engine, scenario="Stress", B=B, seed=seed))
            results[cid] = (cons, stress)
    return mcc.RunEvidence(run_label=run_label, axis=axis, B=B, M=2, K=K,
                           master_seed=seed,
                           prepared_digest=mcc.prepared_digest(prepared),
                           results=results)


def _retrace(observations, atoms):
    """Rebuild an ObservationSet around a modified atom list, keeping the
    declared digest honest (so the ONLY thing that can catch the change
    is an independent replay, not the container's own reducer)."""
    return A.ObservationSet.from_atoms(
        atoms, run_label=observations.run_label,
        platform=observations.platform, engine=observations.engine,
        scenario=observations.scenario,
        theta_channel=observations.theta_channel,
        sizing_policy=observations.sizing_policy, B=observations.B,
        master_seed=observations.master_seed,
        prepared_digest=observations.prepared_digest,
        lifecycle_config_digest=observations.lifecycle_config_digest,
        legal_phase_support=observations.legal_phase_support)


# ===========================================================================
# A. the B-doubling prefix property — VERIFIED, not assumed
# ===========================================================================

def test_seedsequence_spawn_prefix_property_holds_in_this_repo():
    """The `b_doubling_world_prefix_violation` witness is only sound if
    `SeedSequence(seed).spawn(2B)[:B] == spawn(B)` under THIS repo's
    `bootstrap.build_worlds`. Verified directly, at three scales."""
    days = [f"D{i:03d}" for i in range(30)]
    for B in (1, 2, 5):
        base = mb.build_worlds(days, B, 7, length=12)
        doubled = mb.build_worlds(days, 2 * B, 7, length=12)
        assert doubled[:B] == base, f"prefix property fails at B={B}"
        assert len(doubled) == 2 * B
    children_b = np.random.SeedSequence(7).spawn(4)
    children_2b = np.random.SeedSequence(7).spawn(8)
    for a, b in zip(children_b, children_2b):
        assert (a.entropy, a.spawn_key) == (b.entropy, b.spawn_key)


def test_prefix_property_is_seed_specific():
    """A DIFFERENT seed must NOT reproduce the prefix — otherwise the
    witness would pass a re-seeded impostor."""
    days = [f"D{i:03d}" for i in range(30)]
    assert (mb.build_worlds(days, 4, 13, length=12)[:2]
            != mb.build_worlds(days, 2, 7, length=12))


# ===========================================================================
# B. positive end-to-end
# ===========================================================================

def test_positive_forward_run_and_cold_replay_agree_bitwise(prepared):
    obs = _obs(prepared)
    assert len(obs.atoms) == obs.B * obs.M == 4
    spec = mcc.ReplaySpec.from_observations(obs)
    replayed = mcc.cold_replay_observation_set(prepared, spec)
    cmp = mcc.compare_atom_tables(obs, replayed)
    assert cmp["key_set_equal"] is True
    assert cmp["mismatches"] == []
    assert cmp["produced_set_digest"] == cmp["replayed_set_digest"]
    # the two-sided digest tables are BOTH present in the audit record
    assert len(cmp["produced_atom_digests"]) == 4
    assert len(cmp["replayed_atom_digests"]) == 4


def test_every_downstream_number_comes_from_the_same_atoms(prepared):
    obs = _obs(prepared)
    epi = mcc.EpistemicResult.from_observations(obs)
    alea = mcc.run_conditional_aleatoric(obs, world_index=0)
    total = mcc.run_total_predictive(obs)
    assert epi.observations is obs
    assert epi.feasibility.observations is obs
    assert alea.observations_digest == obs.observations_digest
    assert total.observations_digest == obs.observations_digest
    assert len(total.mixture_monthly_evs) == obs.B * obs.M
    assert len(alea.attempt_monthly_evs) == obs.M
    assert alea.world_digest == obs.world_digests()[0]


def test_world_digests_bind_to_the_cold_rebuilt_world_table(prepared):
    obs = _obs(prepared)
    worlds = mcc.build_world_table(prepared, channel=PRIMARY, B=2,
                                   master_seed=7)
    assert obs.world_digests() == tuple(A.world_digest(w) for w in worlds)


def test_world_content_binding_mismatch_is_detected(prepared):
    obs = _obs(prepared)
    fake = [dataclasses.replace(a, world_digest="e" * 64)
            for a in obs.atoms]
    tampered = _retrace(obs, fake)
    worlds = mcc.build_world_table(prepared, channel=PRIMARY, B=2,
                                   master_seed=7)
    with pytest.raises(mcc.MCInputError) as exc:
        mcc._bind_world_content(tampered, worlds)
    assert exc.value.code == "world_content_binding_mismatch"


def test_run_evidence_exposes_two_level_trace_digests(prepared):
    ev = _evidence(prepared)
    ev.validate_inner_binding()
    flat = ev.trace_digests()
    assert len(flat) == 8                       # 4 combos x 2 scenarios
    assert all(len(d) == 64 for d in flat.values())
    top = ev.trace_digest_of_digests()
    assert top == A.digest_of_digests(flat)
    # one changed leaf changes the container digest
    mutated = dict(flat)
    mutated[sorted(mutated)[0]] = "f" * 64
    assert A.digest_of_digests(mutated) != top


# ===========================================================================
# C. cold-replay negatives
# ===========================================================================

def test_cold_replay_divergence_refuses_the_seal(prepared):
    ev = _evidence(prepared)
    cid = sorted(ev.results)[0]
    cons, stress = ev.results[cid]
    bumped = list(cons.observations.atoms)
    bumped[0] = dataclasses.replace(
        bumped[0],
        monthly_prop_operating_ev=bumped[0].monthly_prop_operating_ev
        + 1e-9)
    tampered_set = _retrace(cons.observations, bumped)
    tampered = mcc.EpistemicResult.from_observations(tampered_set)
    results = dict(ev.results)
    results[cid] = (tampered, stress)
    bad = mcc.RunEvidence(run_label=ev.run_label, axis=ev.axis, B=ev.B,
                          M=ev.M, K=ev.K, master_seed=ev.master_seed,
                          prepared_digest=ev.prepared_digest,
                          results=results)
    with pytest.raises(mcc.MCInputError) as exc:
        mcc.verdict_and_seal_from_evidence(
            prepared, base=bad, doubled_by_axis={}, seed_runs={})
    assert exc.value.code == "cold_replay_divergence"


def test_the_cold_replay_runs_before_any_other_refusal(prepared):
    """A tampered trace surfaces `cold_replay_divergence`, NOT the
    feasibility gate — proving the replay is unconditional and first."""
    ev = _evidence(prepared)
    cid = sorted(ev.results)[0]
    cons, stress = ev.results[cid]
    shifted = [dataclasses.replace(a, monthly_prop_operating_ev=-999.0)
               for a in cons.observations.atoms]
    results = dict(ev.results)
    results[cid] = (mcc.EpistemicResult.from_observations(
        _retrace(cons.observations, shifted)), stress)
    bad = mcc.RunEvidence(run_label="base", axis="base", B=ev.B, M=ev.M,
                          K=ev.K, master_seed=ev.master_seed,
                          prepared_digest=ev.prepared_digest,
                          results=results)
    with pytest.raises(mcc.MCInputError) as exc:
        mcc.verdict_and_seal_from_evidence(
            prepared, base=bad, doubled_by_axis={}, seed_runs={})
    assert exc.value.code == "cold_replay_divergence"


def test_seal_entry_accepts_no_caller_conclusion(prepared):
    """No parameter may carry a receipt, a match flag or any verdict-
    shaped conclusion: the replay must be unskippable by construction."""
    sig = inspect.signature(mcc.verdict_and_seal_from_evidence)
    banned = ("receipt", "match", "verified", "replay", "skip", "cached",
              "trusted", "certificate")
    for name in sig.parameters:
        assert not any(b in name.lower() for b in banned), name


def test_an_all_green_receipt_cannot_bypass_the_replay(prepared):
    """PROBE: hand a forged, fully-green receipt to the seal entry — it
    is not even accepted as an argument, and the same evidence still
    refuses."""
    ev = _evidence(prepared)
    forged = {"schema": "mc_cold_replay_receipt.v1", "n_sets_replayed": 8,
              "comparisons": {}, "all_green": True, "match": True,
              "verified": True}
    with pytest.raises(TypeError):
        mcc.verdict_and_seal_from_evidence(
            prepared, base=ev, doubled_by_axis={}, seed_runs={},
            cold_replay_receipt=forged)          # type: ignore[call-arg]
    # B-PROV: the honest call now refuses at the CUSTODY boundary — this
    # fixture's prepared input came from the TEST_ONLY prepare entry, and
    # the seal accepts only the production attestation's product. It used
    # to walk straight past that question into the feasibility gate,
    # which is the Fable V2 finding. The frozen feasibility refusal is
    # unchanged and is asserted one layer down, on the reduction.
    with pytest.raises(mcc.MCInputError) as exc:
        mcc.verdict_and_seal_from_evidence(
            prepared, base=ev, doubled_by_axis={}, seed_runs={})
    assert exc.value.code == "seal_test_only_prepared_input"
    with pytest.raises(mcc.MCInputError) as exc:
        mcc._reduce_primary_from_base(ev)
    assert exc.value.code == "feasibility_gate_input_absent"


def test_replay_receipt_is_an_audit_description_only(prepared):
    ev = _evidence(prepared)
    receipt = mcc.cold_replay_evidence(prepared, [ev])
    assert receipt["schema"] == "mc_cold_replay_receipt.v1"
    assert receipt["n_sets_replayed"] == 8
    for cmp in receipt["comparisons"].values():
        assert cmp["mismatches"] == []
    # it carries NO boolean conclusion field a consumer could trust
    assert "verified" not in receipt and "match" not in receipt
    assert not any(isinstance(v, bool) for v in receipt.values())
    # it DOES carry the full cold-start binding for an auditor
    assert receipt["rng_spec"] == A.RNG_SPEC
    assert receipt["method_version"] == A.METHOD_VERSION
    assert receipt["prepared_identity_bytes_sha256"] == \
        mcc.prepared_digest(prepared)
    assert receipt["legal_phase_support"] == list(
        prepared.calendar.first_month_offsets)
    assert len(receipt["lifecycle_config_digests"]) == 8


def test_forged_legal_support_is_named_not_merely_divergent(prepared):
    """D4: the start-phase support comes from the prepared authority. A
    trace declaring its own support gets its OWN code."""
    ev = _evidence(prepared)
    cid = sorted(ev.results)[0]
    cons, stress = ev.results[cid]
    obs = cons.observations
    narrowed = [a for a in obs.atoms if a.phase_offset == 0]
    forged = A.ObservationSet.from_atoms(
        narrowed, run_label=obs.run_label, platform=obs.platform,
        engine=obs.engine, scenario=obs.scenario,
        theta_channel=obs.theta_channel,
        sizing_policy=obs.sizing_policy, B=obs.B,
        master_seed=obs.master_seed, prepared_digest=obs.prepared_digest,
        lifecycle_config_digest=obs.lifecycle_config_digest,
        legal_phase_support=(0,))
    results = dict(ev.results)
    results[cid] = (mcc.EpistemicResult.from_observations(forged), stress)
    bad = mcc.RunEvidence(run_label="base", axis="base", B=ev.B, M=1,
                          K=ev.K, master_seed=ev.master_seed,
                          prepared_digest=ev.prepared_digest,
                          results=results)
    with pytest.raises(mcc.MCInputError) as exc:
        mcc.cold_replay_evidence(prepared, [bad])
    assert exc.value.code == "legal_phase_support_not_from_prepared"


@pytest.mark.parametrize("field,value,code", [
    ("prepared_digest", "0" * 64,
     "cold_replay_prepared_binding_mismatch"),
    ("rng_spec", "some other rng", "cold_replay_rng_spec_mismatch"),
    ("method_version", "mc-freeze-v9",
     "cold_replay_method_version_mismatch"),
    ("lifecycle_config_digest", "0" * 64,
     "lifecycle_config_digest_mismatch:cold_replay"),
])
def test_cold_start_binding_negatives(prepared, field, value, code):
    spec = mcc.ReplaySpec.from_observations(_obs(prepared))
    with pytest.raises(mcc.MCInputError) as exc:
        mcc.cold_replay_observation_set(
            prepared, dataclasses.replace(spec, **{field: value}))
    assert exc.value.code == code


def test_cold_replay_refuses_a_non_spec(prepared):
    with pytest.raises(mcc.MCInputError) as exc:
        mcc.cold_replay_observation_set(prepared, {"run_label": "base"})
    assert exc.value.code == "cold_replay_spec_invalid"


def test_pinned_prepared_bytes_reproduce_the_prepared_digest(prepared):
    raw = mcc.prepared_identity_bytes(prepared)
    assert hashlib.sha256(raw).hexdigest() == mcc.prepared_digest(prepared)
    assert isinstance(raw, bytes) and len(raw) > 100


def test_compare_atom_tables_reports_all_three_mismatch_kinds(prepared):
    wide = _obs(prepared, B=2)                       # worlds 0 and 1
    narrow = _obs(prepared, B=1)                     # world 0 only
    cmp = mcc.compare_atom_tables(wide, narrow)
    assert cmp["key_set_equal"] is False
    assert {m["kind"] for m in cmp["mismatches"]} == {"missing_in_replay"}
    back = mcc.compare_atom_tables(narrow, wide)
    assert {m["kind"] for m in back["mismatches"]} == {"extra_in_replay"}
    flipped = _retrace(wide, [dataclasses.replace(
        a, monthly_prop_operating_ev=a.monthly_prop_operating_ev + 1.0)
        for a in wide.atoms])
    cmp2 = mcc.compare_atom_tables(wide, flipped)
    assert cmp2["key_set_equal"] is True
    assert {m["kind"] for m in cmp2["mismatches"]} == {"digest_differs"}
    assert len(cmp2["mismatches"]) == 4


# ===========================================================================
# D. the two reducers are structurally independent
# ===========================================================================

def test_cold_reducer_imports_nothing_from_itsf():
    """IMPORT-GRAPH PIN: the independent reducer may not share a single
    expectation-generating helper with production."""
    path = REPO / "src" / "itsf" / "mc" / "cold_reducer.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")
    assert imported, "no imports parsed — check the AST walk"
    for name in imported:
        assert not name.startswith("itsf"), (
            f"cold_reducer imports {name!r} — it must reduce from the "
            "SERIALISED form using stdlib only")
    assert set(imported) <= {"__future__", "hashlib", "json", "math"}


def test_cold_reducer_agrees_with_production_on_a_real_trace(prepared):
    obs = _obs(prepared)
    cold = mcc._dual_reducer_check(obs)
    assert cold["cold_reducer_version"] == CR.COLD_REDUCER_VERSION
    assert cold["observations_digest"] == obs.observations_digest
    assert cold["world_means"] == obs.world_means()
    assert cold["n_atoms"] == len(obs.atoms)


def test_reducer_disagreement_refuses(prepared, monkeypatch):
    """Break ONE production formula and the independent reducer catches
    it — the whole point of two implementations."""
    obs = _obs(prepared)
    monkeypatch.setattr(A, "percentile_linear",
                        lambda values, q: 123456.0)
    with pytest.raises(mcc.MCInputError) as exc:
        mcc._dual_reducer_check(obs)
    assert exc.value.code == "reducer_disagreement"


def test_cold_reducer_refuses_a_corrupted_trace():
    with pytest.raises(CR.ColdReducerError) as exc:
        CR.reduce_trace("not json at all")
    assert exc.value.code == "cold_trace_unparseable"
    with pytest.raises(CR.ColdReducerError) as exc:
        CR.reduce_trace("")
    assert exc.value.code == "cold_trace_empty"
    with pytest.raises(CR.ColdReducerError) as exc:
        CR.reduce_trace(json.dumps({"schema": "wrong.v1"}))
    assert exc.value.code == "cold_trace_schema"


def test_cold_reducer_independent_oracle_on_a_hand_written_trace():
    """INDEPENDENT ORACLE: the trace and the expected values are written
    by hand here; nothing calls the production reducer to build them."""
    rows = []
    for w, phases in ((0, ((0, 1.0), (1, 3.0))),
                      (1, ((0, 10.0), (1, 20.0)))):
        for p, ev in phases:
            rows.append({
                "schema": "mc_simulation_path_observation.v1",
                "prepared_digest": "a" * 64,
                "lifecycle_config_digest": "b" * 64,
                "world_index": w, "world_digest": "c" * 64,
                "phase_offset": p, "platform": "topstep", "engine": "E1",
                "scenario": "Conservative", "theta_channel": "theta_0.5",
                "master_seed": 7, "monthly_prop_operating_ev": ev,
                "days_in_window": 20, "offered_days": 10,
                "executed_trade_days": 6, "skips_n0": 2,
                "payout_count": 1, "winning_days": 4,
                "days_profit_ge_150": 2, "qualifying_days": 3,
                "exhausted": False, "ambiguous_days": 1,
                "attempts_used": 1, "b2f_used": 0,
                "contract_cap_hits": 1,
                "e2_over_budget_days": "NOT_APPLICABLE"})
    text = "\n".join(json.dumps(r, sort_keys=True, ensure_ascii=True,
                                separators=(",", ":")) for r in rows)
    out = CR.reduce_trace(text)
    assert out["world_means"] == (2.0, 15.0)     # hand-computed
    assert out["median"] == pytest.approx(8.5)   # (2 + 15) / 2
    assert out["p5"] == pytest.approx(2.0 + (15.0 - 2.0) * 0.05)
    assert out["feasibility"]["n_paths"] == 4
    assert out["feasibility"]["total_offered"] == 40
    assert out["feasibility"]["total_e2_over_budget_days"] == \
        "NOT_APPLICABLE"
    assert out["actual_phase_keys_by_world"] == {0: (0, 1), 1: (0, 1)}


def test_cold_reducer_never_turns_an_absence_into_zero():
    row = {"schema": "mc_simulation_path_observation.v1",
           "prepared_digest": "a" * 64, "lifecycle_config_digest": "b" * 64,
           "world_index": 0, "world_digest": "c" * 64, "phase_offset": 0,
           "platform": "topstep", "engine": "E2",
           "scenario": "Conservative", "theta_channel": "theta_0.5",
           "master_seed": 7, "monthly_prop_operating_ev": 1.0,
           "days_in_window": 5, "offered_days": 2,
           "executed_trade_days": 1, "skips_n0": 0, "payout_count": 0,
           "winning_days": 1, "days_profit_ge_150": 0,
           "qualifying_days": 0, "exhausted": False, "ambiguous_days": 0,
           "attempts_used": 1, "b2f_used": 0, "contract_cap_hits": 0,
           "e2_over_budget_days": "PENDING_RULING"}
    out = CR.reduce_trace(json.dumps(row, sort_keys=True,
                                     separators=(",", ":")))
    assert out["feasibility"]["total_e2_over_budget_days"] == \
        "PENDING_RULING"
    assert out["feasibility"]["total_e2_over_budget_days"] != 0


# ===========================================================================
# E. M exhaustive-support certificate, DERIVED from the trace
# ===========================================================================

def test_support_certificate_is_derived_from_the_actual_trace(prepared):
    ev = _evidence(prepared)
    ev.validate_inner_binding()
    cert = mcc.derive_support_certificate(ev, prepared)
    assert cert.support == tuple(prepared.calendar.first_month_offsets)
    assert cert.prepared_digest == mcc.prepared_digest(prepared)
    assert set(cert.trace_digests) == set(ev.trace_digests())
    assert cert.trace_digest_of_digests == ev.trace_digest_of_digests()


def test_certificate_digest_is_declare_and_verify():
    with pytest.raises(mcc.MCInputError) as exc:
        mcc.ExhaustiveSupportCertificate(
            prepared_digest="a" * 64, support=(0, 1),
            trace_digests={"k": "b" * 64},
            trace_digest_of_digests="c" * 64)
    assert exc.value.code == "m_support_trace_digest_mismatch"


def test_certificate_refuses_a_foreign_prepared_input(prepared):
    ev = _evidence(prepared)
    other = mcc.prepare_mc_input_for_tests(
        _bundle(pnl=95.0),
        authorization_snapshot={"trial_id": TRIAL,
                                "authorized_commit": COMMIT},
        custody_authority=mcc.CustodyAuthority.for_tests(_bundle(95.0)),
        test_only_calendar=_calendar())
    with pytest.raises(mcc.MCInputError) as exc:
        mcc.derive_support_certificate(ev, other)
    assert exc.value.code == "m_support_wrong_calendar"


@pytest.mark.parametrize("support,code", [
    ((0,), "m_support_incomplete"),
    ((0, 1, 4), "m_support_extra"),
    ((1, 0), "m_support_order_violation"),
])
def test_support_shape_violations_keep_their_ir29_codes(prepared, support,
                                                        code):
    ev = _evidence(prepared)
    cid = sorted(ev.results)[0]
    cons, stress = ev.results[cid]
    obs = cons.observations
    # build a set whose LEGAL SUPPORT claim is wrong while the atoms are
    # consistent with that claim (so only the prepared authority can
    # expose it)
    atoms = [a for a in obs.atoms if a.phase_offset in support] or \
        list(obs.atoms)
    if len(support) > len(obs.legal_phase_support):
        atoms = list(obs.atoms) + [
            dataclasses.replace(a, phase_offset=4) for a in obs.atoms
            if a.phase_offset == 0]
    forged = A.ObservationSet.from_atoms(
        atoms, run_label=obs.run_label, platform=obs.platform,
        engine=obs.engine, scenario=obs.scenario,
        theta_channel=obs.theta_channel,
        sizing_policy=obs.sizing_policy, B=obs.B,
        master_seed=obs.master_seed, prepared_digest=obs.prepared_digest,
        lifecycle_config_digest=obs.lifecycle_config_digest,
        legal_phase_support=support)
    results = dict(ev.results)
    results[cid] = (mcc.EpistemicResult.from_observations(forged), stress)
    bad = mcc.RunEvidence(run_label="base", axis="base", B=ev.B,
                          M=len(support), K=ev.K,
                          master_seed=ev.master_seed,
                          prepared_digest=ev.prepared_digest,
                          results=results)
    with pytest.raises(mcc.MCInputError) as exc:
        mcc.derive_support_certificate(bad, prepared)
    assert exc.value.code == code


def test_a_declared_m_scalar_cannot_substitute_for_the_trace(prepared):
    """BASELINE COUNTEREXAMPLE: the R2.3 certificate proved `base.M ==
    |support|`. A run that executes the WRONG phases while reporting the
    right COUNT must now fail."""
    ev = _evidence(prepared)
    cid = sorted(ev.results)[0]
    cons, stress = ev.results[cid]
    obs = cons.observations
    # same count (M=2 per world), wrong phases: (0, 1) -> (0, 0) is a
    # duplicate; use (0, 1) -> (0, 7) which keeps |phases| == 2.
    wrong = [dataclasses.replace(a, phase_offset=7)
             if a.phase_offset == 1 else a for a in obs.atoms]
    forged = A.ObservationSet.from_atoms(
        wrong, run_label=obs.run_label, platform=obs.platform,
        engine=obs.engine, scenario=obs.scenario,
        theta_channel=obs.theta_channel,
        sizing_policy=obs.sizing_policy, B=obs.B,
        master_seed=obs.master_seed, prepared_digest=obs.prepared_digest,
        lifecycle_config_digest=obs.lifecycle_config_digest,
        legal_phase_support=(0, 7))
    results = dict(ev.results)
    results[cid] = (mcc.EpistemicResult.from_observations(forged), stress)
    bad = mcc.RunEvidence(run_label="base", axis="base", B=ev.B, M=2,
                          K=ev.K, master_seed=ev.master_seed,
                          prepared_digest=ev.prepared_digest,
                          results=results)
    assert bad.M == 2 == len(prepared.calendar.first_month_offsets)
    with pytest.raises(mcc.MCInputError) as exc:
        mcc.derive_support_certificate(bad, prepared)
    assert exc.value.code in ("m_support_extra", "m_support_incomplete",
                              "m_support_order_violation")


def test_convergence_takes_no_caller_certificate():
    sig = inspect.signature(mcc.convergence_from_evidence)
    assert "m_support_certificate" not in sig.parameters
    assert sig.parameters["prepared"].default is inspect.Parameter.empty


def test_convergence_refuses_without_the_prepared_authority(prepared):
    ev = _evidence(prepared)
    with pytest.raises(mcc.MCInputError) as exc:
        mcc.convergence_from_evidence(ev, {}, {}, prepared=None)
    assert exc.value.code == "prepared_authority_missing"


# --- B doubling, content level ---------------------------------------------

def test_b_doubling_world_prefix_positive(prepared):
    base = _evidence(prepared, B=2)
    doubled = _evidence(prepared, run_label="double_B", axis="B", B=4)
    base.validate_inner_binding()
    doubled.validate_inner_binding()
    mcc._check_b_doubling_world_prefix(base, doubled)      # no raise


def test_b_doubling_with_a_redrawn_world_table_refuses(prepared):
    base = _evidence(prepared, B=2, seed=7)
    # a "double" produced from a DIFFERENT seed: same scale, wrong worlds
    impostor = _evidence(prepared, run_label="double_B", axis="B", B=4,
                         seed=13)
    base.validate_inner_binding()
    impostor.validate_inner_binding()
    with pytest.raises(mcc.MCInputError) as exc:
        mcc._check_b_doubling_world_prefix(base, impostor)
    assert exc.value.code == "b_doubling_world_prefix_violation"


# ===========================================================================
# F. four-layer lifecycle_config_digest
# ===========================================================================

def test_atom_layer_and_container_layer_agree(prepared):
    obs = _obs(prepared)
    want = A.lifecycle_config_digest_for(
        mcc.lifecycle_config_for("topstep"), engine="E1",
        scenario="Conservative", theta_channel=PRIMARY)
    assert obs.lifecycle_config_digest == want
    assert all(a.lifecycle_config_digest == want for a in obs.atoms)
    epi = mcc.EpistemicResult.from_observations(obs)
    assert mcc._assert_config_digest(epi, layer="container") == want


@pytest.mark.parametrize("layer", ["container", "cold_replay", "seal"])
def test_each_layer_has_its_own_refusal_code(prepared, layer,
                                             monkeypatch):
    obs = _obs(prepared)
    epi = mcc.EpistemicResult.from_observations(obs)
    monkeypatch.setattr(A, "PAYOUT_PATH_ID", "mutated_payout_path")
    if layer == "cold_replay":
        spec = mcc.ReplaySpec.from_observations(obs)
        with pytest.raises(mcc.MCInputError) as exc:
            mcc.cold_replay_observation_set(prepared, spec)
    else:
        with pytest.raises(mcc.MCInputError) as exc:
            mcc._assert_config_digest(epi, layer=layer)
    assert exc.value.code == f"lifecycle_config_digest_mismatch:{layer}"


def test_unknown_layer_name_refuses(prepared):
    epi = mcc.EpistemicResult.from_observations(_obs(prepared))
    with pytest.raises(mcc.MCInputError) as exc:
        mcc._assert_config_digest(epi, layer="whatever")
    assert exc.value.code == "lifecycle_config_layer_unknown"


def test_combo_label_is_verified_not_parsed(prepared):
    ev = _evidence(prepared)
    results = dict(ev.results)
    cid = sorted(results)[0]
    results["lucid|E1|P9"] = results.pop(cid)     # label lies about policy
    bad = mcc.RunEvidence(run_label="base", axis="base", B=ev.B, M=ev.M,
                          K=ev.K, master_seed=ev.master_seed,
                          prepared_digest=ev.prepared_digest,
                          results=results)
    with pytest.raises(mcc.MCInputError) as exc:
        bad.validate_inner_binding()
    assert exc.value.code == "combo_label_not_authoritative"


# ===========================================================================
# G. REGRESSION RED LINES
# ===========================================================================

def test_feasibility_gate_stays_decision_required(prepared):
    obs = _obs(prepared)
    fe = mcc.FeasibilityEvidence.from_observations(obs)
    # RULED 2026-08-24 (M1-M5). The status names WHICH ruling, so evidence
    # carrying an older one is rejected rather than reinterpreted under a
    # rule it was never evaluated against.
    assert fe.gate_status == "RULED_ND2_ND3_2026-08-24"
    # ...and the boolean still does not live here. That property survived
    # the ruling and matters more now: the reduction exists, so the only
    # thing keeping evidence from being mistaken for a verdict is that the
    # boolean lives one layer up, in a type carrying what produced it.
    assert not hasattr(fe, "feasible")
    assert "feasible" not in fe.metrics
    epi = mcc.EpistemicResult.from_observations(obs)
    with pytest.raises(mcc.MCInputError) as exc:
        mcc.epistemic_go_gate_input(epi, epi)
    assert exc.value.code in ("scenario_role_violation",
                              "feasibility_gate_input_absent")


def test_forged_gate_status_refuses(prepared):
    obs = _obs(prepared)
    with pytest.raises(mcc.MCInputError) as exc:
        mcc.FeasibilityEvidence(observations=obs,
                                metrics=obs.feasibility_counts(),
                                gate_status="PASS")
    assert exc.value.code == "feasibility_gate_status_invalid"


def _seed_runs(prepared, B=2):
    return {s: _evidence(prepared, run_label=f"seed_{s}", axis="seed",
                         B=B, seed=s) for s in RESEARCH_BOOTSTRAP_SEEDS}


def test_frozen_scale_violation_still_guards_small_runs(prepared):
    """The production scale seal is unmoved: B=1000 / K=200 / seed 7."""
    assert mcc.B_WORLDS_FROZEN == 1000
    assert mcc.K_PER_SEED_FROZEN == 200
    assert mcc.BASE_MASTER_SEED == 7
    with pytest.raises(mcc.MCInputError) as exc:
        mcc.convergence_from_evidence(
            _evidence(prepared),
            {"B": _evidence(prepared, run_label="double_B", axis="B",
                            B=4)},
            _seed_runs(prepared), prepared=prepared)
    assert exc.value.code == "frozen_scale_violation"


def test_k_axis_evidence_stays_terminally_blocked(prepared, monkeypatch):
    """With the base scale seal satisfied (scaled down hermetically) and
    a DERIVED M certificate in hand, K is the terminal refusal: no
    grid-replay authority exists, so no actual K-doubled evidence can."""
    monkeypatch.setattr(mcc, "B_WORLDS_FROZEN", 2)
    with pytest.raises(mcc.MCInputError) as exc:
        mcc.convergence_from_evidence(
            _evidence(prepared),
            {"B": _evidence(prepared, run_label="double_B", axis="B",
                            B=4),
             "K": _evidence(prepared, run_label="double_K", axis="K",
                            K=400)},
            _seed_runs(prepared), prepared=prepared)
    assert exc.value.code == "k_axis_evidence_blocked_grid_replay"


def test_m_axis_doubling_stays_forbidden(prepared, monkeypatch):
    monkeypatch.setattr(mcc, "B_WORLDS_FROZEN", 2)
    with pytest.raises(mcc.MCInputError) as exc:
        mcc.convergence_from_evidence(
            _evidence(prepared),
            {"B": _evidence(prepared, run_label="double_B", axis="B",
                            B=4),
             "M": _evidence(prepared, run_label="double_M", axis="M")},
            _seed_runs(prepared), prepared=prepared)
    assert exc.value.code == "m_axis_doubling_forbidden_by_ir29"


def test_seed_set_must_stay_exactly_the_frozen_three(prepared,
                                                     monkeypatch):
    monkeypatch.setattr(mcc, "B_WORLDS_FROZEN", 2)
    runs = _seed_runs(prepared)
    partial = {k: v for k, v in runs.items() if k != 31}
    with pytest.raises(mcc.MCInputError) as exc:
        mcc.convergence_from_evidence(
            _evidence(prepared),
            {"B": _evidence(prepared, run_label="double_B", axis="B",
                            B=4)},
            partial, prepared=prepared)
    assert exc.value.code == "seed_set_violation"


def test_doubling_axes_and_ir29_tokens_unchanged():
    assert mcc.DOUBLING_AXES == frozenset({"B", "K"})
    assert mcc.M_AXIS_DOUBLING_STATUS == \
        "RESOLVED_BY_IR29_EXHAUSTIVE_SUPPORT_CERTIFICATE"
    assert "EXEMPT_FROM_" in mcc.M_AXIS_RULING


def test_authorize_real_mc_refuses_unconditionally():
    with pytest.raises(McConsumerAbsent):
        mcc.authorize_real_mc("")
    with pytest.raises(McConsumerAbsent):
        mcc.authorize_real_mc("**MC_RUN_AUTHORIZED**")


def test_custody_pin_and_bundle_set_unchanged():
    assert mcc.ATTESTATION_SHA256_PINNED == (
        "d839b965a35e749f0a9052cc3fb85f9b4032ed5d412043f36ac3349779941805")
    assert len(mcc.BUNDLE_EXACT_SET) == 14
    assert "manifest.jsonl" in mcc.BUNDLE_EXACT_SET


def test_theta_hard_binding_unchanged(prepared):
    assert mcc.PRIMARY_THETA_CHANNEL == "theta_0.5"
    cons = mcc.EpistemicResult.from_observations(mcc.run_observation_set(
        prepared, run_label="base", platform="topstep", engine="E1",
        scenario="Conservative", channel=SECONDARY, B=2, master_seed=7))
    stress = mcc.EpistemicResult.from_observations(mcc.run_observation_set(
        prepared, run_label="base", platform="topstep", engine="E1",
        scenario="Stress", channel=SECONDARY, B=2, master_seed=7))
    with pytest.raises(mcc.MCInputError) as exc:
        mcc.epistemic_go_gate_input(cons, stress)
    assert exc.value.code == "theta_channel_not_primary"


def test_prepared_input_stays_deeply_immutable(prepared):
    with pytest.raises((AttributeError, TypeError,
                        dataclasses.FrozenInstanceError)):
        prepared.trial_id = "X"                  # type: ignore
    with pytest.raises(TypeError):
        prepared.records[("E1", "Base")]["x"] = None   # type: ignore


# ===========================================================================
# H. BASELINE COUNTEREXAMPLES
# ===========================================================================

def test_from_world_means_is_gone(prepared):
    """The three-independent-caller-input constructor could describe a
    run that never happened."""
    assert not hasattr(mcc.EpistemicResult, "from_world_means")
    assert not hasattr(mcc, "FeasibilityObservation")
    sig = inspect.signature(mcc.EpistemicResult.from_observations)
    assert list(sig.parameters) == ["observations"]


def test_caller_cannot_supply_expected_n_anywhere():
    """`expected_n` let a caller declare how many observations SHOULD
    exist; the count is now a consequence of the B x support grid."""
    assert "expected_n" not in {f.name for f in
                                dataclasses.fields(mcc.FeasibilityEvidence)}
    for fn in (mcc.FeasibilityEvidence.from_observations,
               mcc.run_observation_set, mcc.run_epistemic,
               mcc.EpistemicResult.from_observations):
        assert "expected_n" not in inspect.signature(fn).parameters
    # AST PIN: no identifier, argument or attribute named `expected_n`
    # survives anywhere in the consumer or the atom layer (prose in
    # docstrings explaining WHY it is gone is fine).
    for rel in ("consumer.py", "atoms.py", "cold_reducer.py"):
        tree = ast.parse((REPO / "src" / "itsf" / "mc" / rel).read_text(
            encoding="utf-8"))
        for node in ast.walk(tree):
            assert getattr(node, "id", None) != "expected_n", rel
            assert getattr(node, "arg", None) != "expected_n", rel
            assert getattr(node, "attr", None) != "expected_n", rel


# --- D-1: declare-vs-derive is NUMERIC *and* TYPE equality ----------------

_D_PREP = "a" * 64
_D_CFG = "b" * 64


def _synthetic_atom(world, phase, ev):
    return A.SimulationPathObservation(
        prepared_digest=_D_PREP, lifecycle_config_digest=_D_CFG,
        world_index=world, world_digest="c" * 64, phase_offset=phase,
        platform="topstep", engine="E1", scenario="Conservative",
        theta_channel="theta_0.5", master_seed=7,
        monthly_prop_operating_ev=ev, days_in_window=20, offered_days=1,
        executed_trade_days=1, skips_n0=0, payout_count=0,
        winning_days=1, days_profit_ge_150=0, qualifying_days=0,
        exhausted=False, ambiguous_days=0, attempts_used=1, b2f_used=0,
        contract_cap_hits=1, e2_over_budget_days=A.NOT_APPLICABLE,
        e2_intraday_over_budget_days=A.NOT_APPLICABLE)


def _synthetic_set(world_evs):
    """An ObservationSet with EXACTLY the per-world EVs given, so the
    derived statistics can be steered onto the adversarial values
    (1.0 / 0.0 / 1) where a bool or an int compares EQUAL to a float."""
    support = tuple(range(len(world_evs[0])))
    atoms = [_synthetic_atom(w, p, ev)
             for w, evs in enumerate(world_evs)
             for p, ev in zip(support, evs)]
    return A.ObservationSet.from_atoms(
        atoms, run_label="base", platform="topstep", engine="E1",
        scenario="Conservative", theta_channel="theta_0.5",
        sizing_policy="P2", B=len(world_evs), master_seed=7,
        prepared_digest=_D_PREP, lifecycle_config_digest=_D_CFG,
        legal_phase_support=support)


def test_bool_cannot_impersonate_a_derived_float_world_mean():
    """D-1 IMPERSONATION 1. The derivation yields EXACTLY (1.0, 0.0), so
    `(True, False) == (1.0, 0.0)` is True in Python — a `!=` comparison
    would ACCEPT the bools and store them. Type-exact comparison refuses.
    """
    obs = _synthetic_set([(1.0, 1.0), (0.0, 0.0)])
    epi = mcc.EpistemicResult.from_observations(obs)
    assert epi.world_means == (1.0, 0.0)
    assert (True, False) == epi.world_means      # the numeric trap itself
    with pytest.raises(mcc.MCInputError) as exc:
        dataclasses.replace(epi, world_means=(True, False))
    assert exc.value.code == "epistemic_derived_stats_mismatch"
    assert "bool" in str(exc.value)
    with pytest.raises(mcc.MCInputError) as exc:
        dataclasses.replace(epi, within_world_ses=(False, False))
    assert exc.value.code == "epistemic_derived_stats_mismatch"
    # the honest instance still holds plain floats
    assert all(type(x) is float for x in epi.world_means)
    assert all(type(x) is float for x in epi.within_world_ses)


def test_int_cannot_impersonate_a_derived_float_quantile():
    """D-1 IMPERSONATION 2. A degenerate trace makes p5 == median ==
    p95 == 1.0, so `p5=1` (int) compares EQUAL. Refused on type."""
    obs = _synthetic_set([(1.0, 1.0), (1.0, 1.0)])
    epi = mcc.EpistemicResult.from_observations(obs)
    assert (epi.p5, epi.median, epi.p95) == (1.0, 1.0, 1.0)
    for field in ("p5", "median", "p95"):
        assert 1 == getattr(epi, field)          # the numeric trap itself
        with pytest.raises(mcc.MCInputError) as exc:
            dataclasses.replace(epi, **{field: 1})
        assert exc.value.code == "epistemic_derived_stats_mismatch"
        assert "int" in str(exc.value)
    # and an int may not impersonate the derived bool either
    assert epi.mcse_ok is True and epi.between_world_sd == 0.0
    with pytest.raises(mcc.MCInputError) as exc:
        dataclasses.replace(epi, mcse_ok=1)
    assert exc.value.code == "epistemic_derived_stats_mismatch"
    with pytest.raises(mcc.MCInputError) as exc:
        dataclasses.replace(epi, between_world_sd=0)
    assert exc.value.code == "epistemic_derived_stats_mismatch"


def test_bool_cannot_impersonate_a_derived_feasibility_count():
    """D-1 IMPERSONATION 3. A single-atom trace derives `n_paths == 1`,
    so `n_paths=True` compares EQUAL. Refused on type."""
    obs = _synthetic_set([(1.0,)])
    metrics = dict(obs.feasibility_counts())
    assert metrics["n_paths"] == 1 and type(metrics["n_paths"]) is int
    forged = dict(metrics)
    forged["n_paths"] = True
    assert forged["n_paths"] == metrics["n_paths"]   # the numeric trap
    with pytest.raises(mcc.MCInputError) as exc:
        mcc.FeasibilityEvidence(observations=obs, metrics=forged)
    assert exc.value.code == "feasibility_derived_stats_mismatch"
    assert "bool" in str(exc.value)
    # a float impersonating a derived int count is refused too
    other = dict(metrics)
    other["total_offered"] = float(metrics["total_offered"])
    with pytest.raises(mcc.MCInputError) as exc:
        mcc.FeasibilityEvidence(observations=obs, metrics=other)
    assert exc.value.code == "feasibility_derived_stats_mismatch"
    # ... and an absence still cannot be impersonated by 0
    absent = dict(metrics)
    assert absent["total_e2_over_budget_days"] is A.NOT_APPLICABLE
    absent["total_e2_over_budget_days"] = 0
    with pytest.raises(mcc.MCInputError) as exc:
        mcc.FeasibilityEvidence(observations=obs, metrics=absent)
    assert exc.value.code == "feasibility_derived_stats_mismatch"


def test_honest_declared_values_still_pass_after_the_type_tightening():
    """The tightening must not break the honest path: a list-valued
    caller container still canonicalises to a float tuple."""
    obs = _synthetic_set([(1.0, 3.0), (2.0, 4.0)])
    epi = mcc.EpistemicResult.from_observations(obs)
    round_tripped = dataclasses.replace(
        epi, world_means=list(epi.world_means),
        within_world_ses=list(epi.within_world_ses))
    assert round_tripped.world_means == epi.world_means
    assert type(round_tripped.world_means) is tuple
    assert all(type(x) is float for x in round_tripped.world_means)


# --- D-4: the unreachable arm is a fail-closed refusal, not an assert ------

def test_convergence_fallthrough_is_an_mcinputerror_not_an_assertion(
        prepared, monkeypatch):
    """D-4: the terminal arm was `AssertionError`, which is only correct
    while DOUBLING_AXES permanently contains "K". Simulate the K axis
    being unblocked: the fall-through must stay inside the fail-closed
    vocabulary so a caller's MCInputError handling still catches it."""
    monkeypatch.setattr(mcc, "B_WORLDS_FROZEN", 2)
    monkeypatch.setattr(mcc, "DOUBLING_AXES", frozenset({"B"}))
    try:
        mcc.convergence_from_evidence(
            _evidence(prepared),
            {"B": _evidence(prepared, run_label="double_B", axis="B",
                            B=4)},
            _seed_runs(prepared), prepared=prepared)
    except mcc.MCInputError as exc:
        assert exc.code == "convergence_unreachable_state"
        assert "no verdict may be produced" in str(exc)
    except AssertionError:                        # pragma: no cover
        pytest.fail("the fall-through escaped the fail-closed vocabulary")
    else:                                         # pragma: no cover
        pytest.fail("convergence returned instead of refusing")


def test_forged_epistemic_statistics_are_refused(prepared):
    obs = _obs(prepared)
    epi = mcc.EpistemicResult.from_observations(obs)
    for field in ("p5", "median", "p95", "between_world_sd",
                  "max_within_world_se"):
        with pytest.raises(mcc.MCInputError) as exc:
            dataclasses.replace(epi, **{field: 999.0})
        assert exc.value.code == "epistemic_derived_stats_mismatch"
    with pytest.raises(mcc.MCInputError):
        dataclasses.replace(epi, mcse_ok=not epi.mcse_ok)


def test_forged_feasibility_metrics_are_refused(prepared):
    obs = _obs(prepared)
    fe = mcc.FeasibilityEvidence.from_observations(obs)
    forged = dict(fe.metrics)
    forged["total_winning_days"] = 999999
    with pytest.raises(mcc.MCInputError) as exc:
        mcc.FeasibilityEvidence(observations=obs, metrics=forged)
    assert exc.value.code == "feasibility_derived_stats_mismatch"
    short = {k: v for k, v in fe.metrics.items()
             if k != "total_skips_n0"}
    with pytest.raises(mcc.MCInputError) as exc:
        mcc.FeasibilityEvidence(observations=obs, metrics=short)
    assert exc.value.code == "feasibility_derived_stats_mismatch"


def test_feasibility_from_a_foreign_trace_is_refused(prepared):
    a = _obs(prepared, platform="topstep")
    b = _obs(prepared, platform="lucid")
    with pytest.raises(mcc.MCInputError) as exc:
        mcc.EpistemicResult(
            observations=a, feasibility=mcc.FeasibilityEvidence
            .from_observations(b),
            **{k: v for k, v in mcc._epistemic_derived(a).items()})
    assert exc.value.code == "feasibility_binding_mismatch"


def test_aleatoric_no_longer_re_executes_a_caller_supplied_world():
    """The R2.3 conditional-aleatoric entry ran its OWN lifecycles from a
    caller-handed world — a parallel simulation nothing forced to agree
    with the epistemic run."""
    sig = inspect.signature(mcc.run_conditional_aleatoric)
    assert list(sig.parameters) == ["observations", "world_index"]
    assert "prepared" not in sig.parameters


def test_aleatoric_cannot_leak_into_the_go_gate(prepared):
    obs = _obs(prepared)
    alea = mcc.run_conditional_aleatoric(obs, world_index=0)
    with pytest.raises(mcc.MCInputError) as exc:
        mcc.epistemic_go_gate_input(alea, alea)      # type: ignore[arg-type]
    assert exc.value.code == "aleatoric_leak_into_go_gate"


def test_the_consumer_still_names_no_world_of_its_own(prepared):
    """WAS `test_no_fixed_world_selection_rule_was_invented`, until M11
    ratified a rule on 2026-08-24 and made that name a false claim.

    The half that survives: selection is NOT the consumer's. It lives in
    `itsf.mc.fixed_world`, and a world index always arrives here
    explicitly. The half that had to go: "no rule exists anywhere" would
    now pass forever while protecting nothing, which reads like coverage
    and is worse than no guard. The ratified rule is pinned in
    tests/test_mc_fixed_world_selection.py."""
    for name in dir(mcc):
        low = name.lower()
        if "world" in low:
            assert "select" not in low and "choose" not in low, name
        assert "fixed_world" not in low or "select" not in low, name
    obs = _obs(prepared, B=2)
    with pytest.raises(mcc.MCInputError) as exc:
        mcc.run_conditional_aleatoric(obs, world_index=99)
    assert exc.value.code == "aleatoric_world_absent"
    with pytest.raises(mcc.MCInputError) as exc:
        mcc.run_conditional_aleatoric({"not": "a set"}, world_index=0)
    assert exc.value.code == "aleatoric_source_invalid"


# ===========================================================================
# The E2 aggregation's two refusal codes — Fable V2 Medium, closed 2026-08-26
# ===========================================================================

def _e2_rows(*values):
    """Minimal cold-trace rows carrying only the summed field."""
    return [{"e2_over_budget_days": v} for v in values]


def test_mixing_two_absence_reasons_in_one_sum_is_refused():
    """`cold_trace_absent_mixed` had NO test. It is the code that stops a
    set of atoms disagreeing about WHY a quantity is absent from
    collapsing into one confident-looking answer — 'not applicable' and
    'pending ruling' are different claims and their union is neither."""
    from itsf.mc import atoms as A
    from itsf.mc import cold_reducer as cr

    rows = _e2_rows(A.NOT_APPLICABLE.token, A.PENDING_RULING.token)
    with pytest.raises(cr.ColdReducerError) as exc:
        cr._absent_aware_sum(rows, "e2_over_budget_days")
    assert exc.value.code == "cold_trace_absent_mixed"
    assert "e2_over_budget_days" in str(exc.value)


def test_an_unknown_absence_token_in_a_sum_is_refused():
    """`cold_trace_absent_token` had NO test either. A string that is not
    a ratified absence token is not a weaker absence; it is not one."""
    from itsf.mc import cold_reducer as cr

    with pytest.raises(cr.ColdReducerError) as exc:
        cr._absent_aware_sum(_e2_rows(3, "absent_because_i_said_so"),
                             "e2_over_budget_days")
    assert exc.value.code == "cold_trace_absent_token"


def test_one_absence_among_real_counts_makes_the_whole_sum_absent():
    """The positive statement of the same rule, measured rather than
    assumed: a partial sum would read downstream as a complete count."""
    from itsf.mc import atoms as A
    from itsf.mc import cold_reducer as cr

    assert cr._absent_aware_sum(_e2_rows(1, 2, 3),
                                "e2_over_budget_days") == 6
    out = cr._absent_aware_sum(_e2_rows(1, 2, A.NOT_APPLICABLE.token),
                               "e2_over_budget_days")
    assert out == A.NOT_APPLICABLE.token, out
    assert out != 3 and out != 0
