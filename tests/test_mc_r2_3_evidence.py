"""DR-5 MC consumer R2.3 evidence battery (LANE S1; synthetic fixtures ONLY).

R2.3 contract under test:
  A. EpistemicResult deep canonicalization — list inputs are stored as
     plain-float tuples (aliasing fix), bool/NaN/str/length violations
     refuse with "epistemic_samples_invalid", identity fields must be
     positive non-bool ints ("epistemic_identity_invalid").
  B. FeasibilityObservation + FeasibilityEvidence rebuilt from an
     observation layer — every scalar is recomputed from the immutable
     observations tuple, so forged/out-of-range/synchronized-tampered
     scalars cannot exist.
  C. FeasibilityEvidence carries the run's binding identity and
     EpistemicResult cross-checks it ("feasibility_binding_mismatch").
  D. RunEvidence deep-freeze + per-entry revalidation inside
     convergence_from_evidence.

Written against the R2.3 contract while the main agent lands the API in
src/itsf/mc/consumer.py — expected to fail until integration."""
from __future__ import annotations

import dataclasses
import hashlib
import json

import pytest

from conftest import make_trade_path
from itsf.contracts import RESEARCH_BOOTSTRAP_SEEDS
from itsf.mc import consumer as mcc
from itsf.mc.orchestrator import TemplateDay

TRIAL = "S0-T001"
COMMIT = "876c1b74131b4ab1a89dce433ecce646ba481f8c"
TP_DAYS = ("2026-08-03", "2026-08-05", "2026-08-07")
FP_DAYS = ("2026-08-04", "2026-08-06")
ALL_DAYS = tuple(sorted(TP_DAYS + FP_DAYS))
PRIMARY = mcc.PRIMARY_THETA_CHANNEL          # 'theta_0.5'


# --- synthetic bundle fixtures (self-contained; pattern shared with
# --- tests/test_mc_consumer.py, deliberately NOT imported from it) ----------

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


def _bundle(pnl: float = 80.0) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    counts: dict = {}
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
    names = sorted(files)
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


def _epi(prepared, platform="topstep", engine="E1",
         scenario="Conservative", B=2, seed=7, channel=PRIMARY):
    return mcc.run_epistemic(prepared, platform=platform, engine=engine,
                             scenario=scenario, channel=channel, B=B,
                             master_seed=seed)


# --- feasibility-observation fixtures (R2.3 PHASE B) ------------------------

# binding identity shared by the hand-built feasibility fixtures; B=2, M=2
# so expected_n = B*M = 4 (matches the 2x2 observation grid below).
_BINDING = dict(prepared_digest="0" * 64, platform="topstep", engine="E1",
                scenario="Conservative", channel=PRIMARY, B=2, M=2,
                master_seed=7)


def _obs(world_index, phase_offset, *, offered=4, skips_n0=1,
         payout_realized=False, payout_count=0, winning_days=2,
         days_profit_ge_150=1, exhausted=False, ambiguous_days=0,
         contract_cap_hits=None, e2_over_budget_days=None):
    return mcc.FeasibilityObservation(
        world_index=world_index, phase_offset=phase_offset,
        offered=offered, skips_n0=skips_n0,
        payout_realized=payout_realized, payout_count=payout_count,
        winning_days=winning_days, days_profit_ge_150=days_profit_ge_150,
        exhausted=exhausted, ambiguous_days=ambiguous_days,
        contract_cap_hits=contract_cap_hits,
        e2_over_budget_days=e2_over_budget_days)


def _grid_obs(payout_worlds=(), exhausted_worlds=(), **kw):
    """The full B=2 x M=2 observation grid — unique (world, phase) pairs."""
    out = []
    for w in range(2):
        for p in range(2):
            paid = w in payout_worlds
            out.append(_obs(w, p, payout_realized=paid,
                            payout_count=1 if paid else 0,
                            exhausted=w in exhausted_worlds, **kw))
    return tuple(out)


def _feas_from_obs(observations, expected_n=4, **binding):
    """integration point: main agent aligns — binding identity is passed
    as keywords alongside the observations."""
    kw = dict(_BINDING)
    kw.update(binding)
    return mcc.FeasibilityEvidence.from_observations(
        observations, expected_n, **kw)


def _feas_direct(observations, **overrides):
    """integration point: main agent aligns exact field list — DIRECT
    construction with scalars locally re-derived from the observations,
    then `overrides` applied (the tamper vector under test)."""
    n = len(observations)
    offered = sum(o.offered for o in observations)
    kw = dict(
        observations=tuple(observations),
        expected_n=_BINDING["B"] * _BINDING["M"],
        n_paths=n,
        payout_realized_share=(sum(1 for o in observations
                                   if o.payout_realized) / n if n else 0.0),
        total_skips_n0=sum(o.skips_n0 for o in observations),
        total_offered=offered,
        exhausted_share=(sum(1 for o in observations if o.exhausted) / n
                         if n else 0.0),
        ambiguous_share=(sum(o.ambiguous_days for o in observations)
                         / offered if offered else 0.0),
        **_BINDING)
    kw.update(overrides)
    return mcc.FeasibilityEvidence(**kw)


# --- A. EpistemicResult deep canonicalization (R2.3 aliasing fix) -----------

def test_list_inputs_canonicalize_to_plain_float_tuples():
    """R2.3 A: constructing with world_means/within_world_ses as LISTS
    succeeds but the instance stores plain-float TUPLES — mutating the
    caller's original lists afterwards has NO effect on the instance."""
    res = _epi(_prepare())
    src_means = [float(x) for x in res.world_means]
    src_ses = [float(s) for s in res.within_world_ses]
    want_means = tuple(src_means)
    want_ses = tuple(src_ses)
    r = dataclasses.replace(res, world_means=src_means,
                            within_world_ses=src_ses)
    src_means[0] = 1e9
    src_means.append(-1.0)
    src_ses[0] = 999.0
    assert r.world_means == want_means
    assert r.within_world_ses == want_ses
    assert isinstance(r.world_means, tuple)
    assert isinstance(r.within_world_ses, tuple)
    assert all(type(x) is float
               for x in r.world_means + r.within_world_ses)


def test_bool_sample_entries_refused():
    """R2.3 A: bool is NOT a number here — a True/False smuggled into the
    raw samples refuses with the samples code, never a silent 1.0/0.0."""
    res = _epi(_prepare())
    with pytest.raises(mcc.MCInputError, match="epistemic_samples_invalid"):
        dataclasses.replace(res, world_means=(True, False))
    with pytest.raises(mcc.MCInputError, match="epistemic_samples_invalid"):
        dataclasses.replace(res, within_world_ses=(True,) * res.B)


def test_nonfinite_sample_entries_refused():
    """R2.3 A (carrying R2.1 PHASE D): NaN/inf world means are refusals —
    a quantile computed over garbage is not evidence."""
    res = _epi(_prepare())
    with pytest.raises(mcc.MCInputError, match="epistemic_samples_invalid"):
        dataclasses.replace(
            res, world_means=(float("nan"),) + res.world_means[1:])
    with pytest.raises(mcc.MCInputError, match="epistemic_samples_invalid"):
        dataclasses.replace(
            res, world_means=(float("inf"),) + res.world_means[1:])


def test_sample_length_mismatch_refused():
    """R2.3 A (carrying R2.2 PHASE C): one mean and one SE per world —
    len != B refuses for either vector, no truncation, no padding."""
    res = _epi(_prepare())
    with pytest.raises(mcc.MCInputError, match="epistemic_samples_invalid"):
        dataclasses.replace(res, world_means=res.world_means + (0.0,))
    with pytest.raises(mcc.MCInputError, match="epistemic_samples_invalid"):
        dataclasses.replace(res,
                            within_world_ses=res.within_world_ses[:-1])


def test_non_numeric_sample_entries_refused():
    """R2.3 A: a str entry in the raw samples refuses with the samples
    code (an MCInputError, never a bare numpy coercion error)."""
    res = _epi(_prepare())
    with pytest.raises(mcc.MCInputError, match="epistemic_samples_invalid"):
        dataclasses.replace(res,
                            world_means=("100.0",) + res.world_means[1:])


def test_identity_fields_must_be_positive_nonbool_ints():
    """R2.3 A: B/M/master_seed are positive non-bool ints — B=True, M=0
    and master_seed=-1 each refuse with the identity code."""
    res = _epi(_prepare())
    for field_name, forged in (("B", True), ("M", 0), ("master_seed", -1)):
        with pytest.raises(mcc.MCInputError,
                           match="epistemic_identity_invalid"):
            dataclasses.replace(res, **{field_name: forged})


def test_replace_of_derived_stats_still_refused_r2_2_regression():
    """R2.2 PHASE C regression kept under R2.3: dataclasses.replace of ANY
    derived statistic still refuses — the type re-derives from the raw
    samples on every construction."""
    res = _epi(_prepare())
    for field_name, forged in (("p5", 999.0), ("median", 999.0),
                               ("p95", 999.0),
                               ("mcse_ok", not res.mcse_ok),
                               ("between_world_sd", 123.0),
                               ("max_within_world_se",
                                res.max_within_world_se + 1.0)):
        with pytest.raises(mcc.MCInputError,
                           match="epistemic_derived_stats_mismatch"):
            dataclasses.replace(res, **{field_name: forged})


# --- B. FeasibilityObservation + FeasibilityEvidence rebuild ----------------

def test_observation_constructs_and_pending_engineering_is_none():
    """R2.3 B: a valid observation is frozen; contract_cap_hits /
    e2_over_budget_days accept None (PENDING_ENGINEERING) or an int>=0 —
    a negative count is refused once the field is engineered."""
    o = _obs(0, 1, payout_realized=True, payout_count=1)
    assert o.contract_cap_hits is None          # PENDING_ENGINEERING
    assert o.e2_over_budget_days is None        # PENDING_ENGINEERING
    with pytest.raises(dataclasses.FrozenInstanceError):
        o.offered = 9                            # type: ignore
    o2 = _obs(1, 0, contract_cap_hits=0, e2_over_budget_days=3)
    assert o2.contract_cap_hits == 0 and o2.e2_over_budget_days == 3
    with pytest.raises(mcc.MCInputError,
                       match="feasibility_observation_invalid"):
        _obs(0, 0, contract_cap_hits=-1)


def test_observation_invalid_fields_refused():
    """R2.3 B: negative counts, bool-typed ints, skips_n0 > offered and
    ambiguous_days > offered each refuse with the observation code."""
    with pytest.raises(mcc.MCInputError,
                       match="feasibility_observation_invalid"):
        _obs(0, 0, offered=-1)
    with pytest.raises(mcc.MCInputError,
                       match="feasibility_observation_invalid"):
        _obs(0, 0, offered=True)                 # bool is not an int here
    with pytest.raises(mcc.MCInputError,
                       match="feasibility_observation_invalid"):
        _obs(0, 0, skips_n0=5)                   # > offered=4
    with pytest.raises(mcc.MCInputError,
                       match="feasibility_observation_invalid"):
        _obs(0, 0, ambiguous_days=5)             # > offered=4
    with pytest.raises(mcc.MCInputError,
                       match="feasibility_observation_invalid"):
        _obs(-1, 0)                              # negative world_index


def test_from_observations_recomputes_every_scalar():
    """R2.3 B: FeasibilityEvidence is built ONLY from observations — every
    scalar comes from the recomputation, and the full observations tuple
    is stored immutably on the evidence."""
    grid = _grid_obs(payout_worlds=(0,), exhausted_worlds=(1,))
    fe = _feas_from_obs(grid)
    assert fe.n_paths == 4
    assert isinstance(fe.observations, tuple)
    assert len(fe.observations) == 4
    assert fe.payout_realized_share == 0.5       # world 0 pays, world 1 not
    assert fe.exhausted_share == 0.5             # world 1 exhausts
    assert fe.total_skips_n0 == 4                # 4 obs x skips_n0=1
    assert fe.total_offered == 16                # 4 obs x offered=4
    assert fe.ambiguous_share == 0.0


def test_direct_construction_contradictory_scalars_refused():
    """R2.3 B: direct construction with a scalar contradicting the
    observations (payout_realized_share=1.0 while NO observation realized
    a payout) refuses — __post_init__ re-derives."""
    with pytest.raises(mcc.MCInputError,
                       match="feasibility_derived_stats_mismatch"):
        _feas_direct(_grid_obs(), payout_realized_share=1.0)


def test_out_of_range_scalars_cannot_exist():
    """R2.3 B: negative/out-of-range scalars can no longer exist — they
    mismatch the derivation from the observations by construction."""
    with pytest.raises(mcc.MCInputError,
                       match="feasibility_derived_stats_mismatch"):
        _feas_direct(_grid_obs(), n_paths=-5)
    with pytest.raises(mcc.MCInputError,
                       match="feasibility_derived_stats_mismatch"):
        _feas_direct(_grid_obs(), ambiguous_share=3.7)


def test_missing_or_extra_observation_refused():
    """R2.3 B: the observation set must be COMPLETE — count == expected_n
    (= B*M); a removed or an extra observation refuses."""
    grid = _grid_obs()
    with pytest.raises(mcc.MCInputError,
                       match="feasibility_observations_incomplete"):
        _feas_from_obs(grid[:-1])                # one removed
    with pytest.raises(mcc.MCInputError,
                       match="feasibility_observations_incomplete"):
        _feas_from_obs(grid + (_obs(5, 0),))     # one extra


def test_duplicate_observation_pair_refused():
    """R2.3 B: (world_index, phase_offset) pairs must be UNIQUE — a
    duplicated observation (count still == expected_n) refuses with the
    duplicate code, not a silent double-count."""
    grid = _grid_obs()
    with pytest.raises(mcc.MCInputError,
                       match="feasibility_observations_duplicate"):
        _feas_from_obs(grid[:3] + (grid[0],))    # (0,0) twice, (1,1) gone


def test_synchronized_numerator_denominator_tamper_refused():
    """R2.3 B (the R2.2 counterexample closed): halving total_offered AND
    total_skips_n0 TOGETHER — internally consistent ratios — still
    refuses, because both are recomputed from the unchanged
    observations."""
    fe = _feas_from_obs(_grid_obs(skips_n0=2))   # skips=8, offered=16
    with pytest.raises(mcc.MCInputError,
                       match="feasibility_derived_stats_mismatch"):
        dataclasses.replace(fe, total_offered=fe.total_offered // 2,
                            total_skips_n0=fe.total_skips_n0 // 2)


def test_gate_status_decision_required_and_no_feasible_boolean():
    """R2.1 PHASE G held under R2.3: gate_status stays DECISION_REQUIRED
    and NO feasible boolean exists anywhere on the observation layer."""
    fe = _feas_from_obs(_grid_obs())
    assert fe.gate_status == "DECISION_REQUIRED"
    assert not hasattr(fe, "feasible")
    assert not hasattr(mcc.FeasibilityObservation, "feasible")
    assert mcc.FEASIBILITY_GATE_STATUS == "DECISION_REQUIRED"


# --- C. feasibility <-> epistemic binding (R2.3) ----------------------------

def test_run_epistemic_feasibility_carries_binding_and_full_observations():
    """R2.3 C: run_epistemic's feasibility is built from exactly B*M
    observations (one per world x start phase) and carries the run's OWN
    binding identity."""
    prepared = _prepare()
    res = _epi(prepared)                          # B=2, M=2 offsets
    fe = res.feasibility
    assert len(fe.observations) == res.B * res.M == 4
    assert {(o.world_index, o.phase_offset) for o in fe.observations} == \
        {(w, p) for w in range(res.B) for p in range(res.M)}
    assert (fe.platform, fe.engine, fe.scenario, fe.channel) == \
        ("topstep", "E1", "Conservative", PRIMARY)
    assert (fe.B, fe.M, fe.master_seed) == (res.B, res.M, res.master_seed)
    assert fe.prepared_digest == res.prepared_digest \
        == mcc.prepared_digest(prepared)


def test_foreign_feasibility_binding_refused():
    """R2.3 C: a feasibility re-labelled to a DIFFERENT combo passes its
    own scalar re-derivation (the observations did not change) but any
    EpistemicResult built with it refuses at the binding cross-check."""
    res = _epi(_prepare())
    foreign = dataclasses.replace(res.feasibility, platform="lucid")
    assert foreign.platform == "lucid"            # its own post_init passed
    with pytest.raises(mcc.MCInputError,
                       match="feasibility_binding_mismatch"):
        dataclasses.replace(res, feasibility=foreign)


# --- D. RunEvidence deep-freeze + per-entry revalidation --------------------

def _grid_results(prepared) -> dict:
    """The full Primary verdict grid as a PLAIN dict of cid -> [cons,
    stress] LISTS — the aliasing-prone caller shape R2.3 D canonicalizes."""
    out = {}
    for platform, policy in mcc.PRIMARY_COMBOS:
        for engine in mcc.ENGINES:
            cons = _epi(prepared, platform=platform, engine=engine)
            stress = _epi(prepared, platform=platform, engine=engine,
                          scenario="Stress")
            out[f"{platform}|{engine}|{policy}"] = [cons, stress]
    return out


def test_run_evidence_deep_freeze_and_source_isolation():
    """R2.3 D: RunEvidence built from a plain dict of LISTS stores an
    immutable mapping of (cons, stress) TUPLES; mutating the caller's
    dict/list afterwards has no effect and writing into evidence.results
    raises TypeError."""
    prepared = _prepare()
    raw = _grid_results(prepared)
    cid = sorted(raw)[0]
    cons0, stress0 = raw[cid]
    ev = mcc.RunEvidence(run_label="base", axis="base", B=2, M=2,
                         K=prepared.k_per_seed, master_seed=7,
                         prepared_digest=mcc.prepared_digest(prepared),
                         results=raw)
    raw[cid][0] = None                            # tamper the source list
    raw.clear()                                   # and the source dict
    assert set(ev.results) == set(mcc.PRIMARY_VERDICT_GRID)
    entry = ev.results[cid]
    assert isinstance(entry, tuple)
    assert entry == (cons0, stress0)
    with pytest.raises(TypeError):
        ev.results[cid] = (stress0, cons0)        # type: ignore
    ev.validate_inner_binding()                   # still a fully valid run


def test_outer_b_tamper_refused_on_every_convergence_call():
    """R2.3 D regression: convergence_from_evidence re-runs
    validate_inner_binding on EVERY entry on EVERY call — an
    outer-B-tampered run (outer B=4 over inner B=2 results) still refuses
    with the per-field code."""
    prepared = _prepare()
    raw = _grid_results(prepared)
    with pytest.raises(mcc.MCInputError,
                       match="run_evidence_inner_mismatch:B"):
        tampered = mcc.RunEvidence(
            run_label="base", axis="base", B=4, M=2,
            K=prepared.k_per_seed, master_seed=7,
            prepared_digest=mcc.prepared_digest(prepared), results=raw)
        mcc.convergence_from_evidence(tampered, doubled_by_axis={},
                                      seed_runs={})
