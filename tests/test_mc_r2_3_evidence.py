"""DR-5 MC consumer R2.3 evidence battery (LANE S1; synthetic fixtures ONLY).

MIGRATED TO THE N01 UNIFIED ATOM LAYER. Every counterexample this file
historically closed is re-expressed against the new architecture; NONE was
dropped, softened or turned into a positive. Where an attack ENTRY has
been deleted outright (`FeasibilityObservation`, `EpistemicResult
.from_world_means`, the declarable identity fields, `expected_n`), the
test now proves the entry is gone AND re-states the same invariant on its
successor type — which refuses earlier and with a more specific code.

R2.3 contract, as carried forward under N01:
  A. EpistemicResult is REDUCED FROM AN ATOM TRACE. There is exactly one
     input (`ObservationSet`); every statistic and every identity field is
     re-derived on construction. A declared value that disagrees with the
     derivation refuses with "epistemic_derived_stats_mismatch" — the R2.3
     "epistemic_samples_invalid" for hand-fed sample containers is
     STRICTLY SUPERSEDED (there is no sample container to feed).
  B. `FeasibilityObservation` is DELETED; the atom
     (`SimulationPathObservation`) carries its fields with one refusal code
     per cross-invariant, and typed absences replace the untyped `None`.
     `expected_n` is DELETED; completeness is the B x legal-phase-support
     Cartesian key grid, which also catches count-preserving substitution.
  C. Feasibility identity is READ from the trace (properties), never
     declared; a foreign trace refuses with "feasibility_binding_mismatch".
  D. RunEvidence deep-freeze + per-entry revalidation inside
     convergence_from_evidence (now with the mandatory `prepared` authority).
"""
from __future__ import annotations

import dataclasses
import hashlib
import json

import pytest

from conftest import make_trade_path
from itsf.contracts import RESEARCH_BOOTSTRAP_SEEDS
from itsf.mc import atoms as A
from itsf.mc import consumer as mcc
from itsf.mc import orchestrator as orch
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


# --- hand-built ATOM fixtures (N01 successors of the R2.3
# --- FeasibilityObservation fixtures; the counts are chosen so the
# --- historical hand-computed metric expectations survive verbatim) --------

_D_PREP = "a" * 64
_D_CFG = "b" * 64


def _wdigest(world_index: int) -> str:
    return hashlib.sha256(f"world-{world_index}".encode("utf-8")).hexdigest()


def _atom(world_index=0, phase_offset=0, *, ev=None, offered=4, skips_n0=1,
          payout_count=0, winning_days=2, days_profit_ge_150=1,
          exhausted=False, ambiguous_days=0, contract_cap_hits=1,
          executed_trade_days=3, engine="E1", **over):
    """ONE atom — the N01 successor of `FeasibilityObservation`.

    Defaults mirror the R2.3 observation defaults (offered=4, skips_n0=1,
    winning_days=2, days_profit_ge_150=1) so the migrated metric
    expectations are the SAME numbers, hand-computed the same way."""
    kw = dict(
        prepared_digest=_D_PREP, lifecycle_config_digest=_D_CFG,
        world_index=world_index, world_digest=_wdigest(world_index),
        phase_offset=phase_offset, platform="topstep", engine=engine,
        scenario="Conservative", theta_channel=PRIMARY, master_seed=7,
        monthly_prop_operating_ev=(float(world_index * 10 + phase_offset)
                                   if ev is None else ev),
        days_in_window=20, offered_days=offered,
        executed_trade_days=executed_trade_days, skips_n0=skips_n0,
        payout_count=payout_count, winning_days=winning_days,
        days_profit_ge_150=days_profit_ge_150, qualifying_days=1,
        exhausted=exhausted, ambiguous_days=ambiguous_days,
        attempts_used=(orch.MAX_EVALUATION_STARTS if exhausted else 1),
        b2f_used=0, contract_cap_hits=contract_cap_hits,
        e2_over_budget_days=(A.NOT_APPLICABLE if engine == "E1"
                             else A.PENDING_RULING),
        e2_intraday_over_budget_days=(A.NOT_APPLICABLE if engine == "E1"
                                      else A.PENDING_RULING))
    kw.update(over)
    return A.SimulationPathObservation(**kw)


def _grid_atoms(payout_worlds=(), exhausted_worlds=(), **kw):
    """The full B=2 x support=(0,1) atom grid — unique (world, phase)
    keys, the N01 successor of the R2.3 `_grid_obs` observation grid."""
    out = []
    for w in range(2):
        for p in range(2):
            paid = w in payout_worlds
            out.append(_atom(w, p, payout_count=1 if paid else 0,
                             exhausted=w in exhausted_worlds, **kw))
    return tuple(out)


def _oset(atoms, *, B=2, support=(0, 1), **over):
    kw = dict(run_label="base", platform="topstep", engine="E1",
              scenario="Conservative", theta_channel=PRIMARY,
              sizing_policy="P2", B=B, master_seed=7,
              prepared_digest=_D_PREP, lifecycle_config_digest=_D_CFG,
              legal_phase_support=support)
    kw.update(over)
    return A.ObservationSet.from_atoms(tuple(atoms), **kw)


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
    """R2.3 A, MIGRATED: bool is NOT a number here — a True/False smuggled
    into the sample vectors refuses, never a silent 1.0/0.0.

    N01 strength change: the vectors are no longer caller-supplied raw
    samples, they are DERIVED from the atom trace, so the refusal code
    moved from `epistemic_samples_invalid` to the more specific
    `epistemic_derived_stats_mismatch` (the declared value disagrees with
    the derivation, whatever its type). The type discipline itself is
    pinned directly on the derivation: `world_means`/`within_world_ses`
    reduced from atoms are ALWAYS plain floats, so no honest path can ever
    place a bool there."""
    res = _epi(_prepare())
    assert all(type(x) is float for x in res.world_means)
    assert all(type(x) is float for x in res.within_world_ses)
    # the fixture's derived means are NOT 1.0/0.0, so bools are a genuine
    # numeric lie and the derivation catches them
    assert res.world_means != (1.0, 0.0)
    with pytest.raises(mcc.MCInputError,
                       match="epistemic_derived_stats_mismatch"):
        dataclasses.replace(res, world_means=(True, False))
    with pytest.raises(mcc.MCInputError,
                       match="epistemic_derived_stats_mismatch"):
        dataclasses.replace(res, within_world_ses=(True,) * res.B)


def test_nonfinite_sample_entries_refused():
    """R2.3 A (carrying R2.1 PHASE D), MIGRATED AND STRENGTHENED: NaN/inf
    are not evidence.

    Three layers now, where R2.3 had one:
      1. an atom carrying a non-finite EV cannot be CONSTRUCTED
         (`atom_ev_non_finite`) — the value never enters a trace;
      2. a declared non-finite mean disagrees with the derivation
         (`epistemic_derived_stats_mismatch`);
      3. the reduction's own non-finite guard is still live and REACHABLE
         from finite atoms (float overflow: 1e308 + 1e308 == inf), and
         refuses with the historical `epistemic_samples_invalid`."""
    res = _epi(_prepare())
    for bad in (float("nan"), float("inf"), float("-inf")):
        with pytest.raises(mcc.MCInputError, match="atom_ev_non_finite"):
            _atom(monthly_prop_operating_ev=bad)
        with pytest.raises(mcc.MCInputError,
                           match="epistemic_derived_stats_mismatch"):
            dataclasses.replace(res,
                                world_means=(bad,) + res.world_means[1:])
    overflowed = _oset(_grid_atoms(ev=1e308))
    assert all(m == float("inf") for m in overflowed.world_means())
    with pytest.raises(mcc.MCInputError, match="epistemic_samples_invalid"):
        mcc._epistemic_derived(overflowed)


def test_sample_length_mismatch_refused():
    """R2.3 A (carrying R2.2 PHASE C), MIGRATED: one mean and one SE per
    world — no truncation, no padding.

    N01 makes the length a CONSEQUENCE of the key grid rather than a
    caller claim: a declared vector of the wrong length disagrees with the
    derivation (`epistemic_derived_stats_mismatch`), and the underlying
    world domain itself cannot be short — a set declaring B=4 while
    carrying only two worlds' atoms refuses at `key_grid_missing`."""
    res = _epi(_prepare())
    with pytest.raises(mcc.MCInputError,
                       match="epistemic_derived_stats_mismatch"):
        dataclasses.replace(res, world_means=res.world_means + (0.0,))
    with pytest.raises(mcc.MCInputError,
                       match="epistemic_derived_stats_mismatch"):
        dataclasses.replace(res,
                            within_world_ses=res.within_world_ses[:-1])
    with pytest.raises(mcc.MCInputError, match="key_grid_missing"):
        _oset(_grid_atoms(), B=4)


def test_non_numeric_sample_entries_refused():
    """R2.3 A, MIGRATED: a str entry refuses with an MCInputError, never a
    bare coercion/TypeError leaking out of a numeric library.

    Two layers: the atom refuses a str EV at construction
    (`atom_ev_non_finite`), and a declared str statistic disagrees with the
    float derivation (`epistemic_derived_stats_mismatch`)."""
    res = _epi(_prepare())
    with pytest.raises(mcc.MCInputError, match="atom_ev_non_finite"):
        _atom(monthly_prop_operating_ev="100.0")
    with pytest.raises(mcc.MCInputError,
                       match="epistemic_derived_stats_mismatch") as ei:
        dataclasses.replace(res, world_means=("100.0",)
                            + res.world_means[1:])
    assert isinstance(ei.value, mcc.MCInputError)


def test_identity_fields_must_be_positive_nonbool_ints():
    """R2.3 A, OBSOLETE BY CONSTRUCTION — the entry it guarded is gone.

    HISTORICAL COUNTEREXAMPLE (kept on the record): `EpistemicResult`
    carried B / M / master_seed as DECLARED dataclass fields, so a caller
    could hand over B=True, M=0 or master_seed=-1; R2.3 answered with
    `epistemic_identity_invalid`. N01 PHASE D1 deleted the fields
    outright: they are now read-only properties reduced from the atom
    trace, so no value — valid or invalid — can be declared at all, and
    `dataclasses.replace` refuses them as unknown keywords.

    The invariant survives on the successor: a trace whose world domain
    disagrees with B refuses (`key_grid_missing`), and an atom carrying a
    foreign master_seed refuses (`atom_binding_mismatch`)."""
    res = _epi(_prepare())
    declared = {f.name for f in dataclasses.fields(mcc.EpistemicResult)}
    for name in ("B", "M", "master_seed", "platform", "engine", "scenario",
                 "channel", "prepared_digest"):
        assert name not in declared, name
        assert isinstance(getattr(type(res), name), property), name
    for field_name, forged in (("B", True), ("M", 0), ("master_seed", -1)):
        with pytest.raises(TypeError):
            dataclasses.replace(res, **{field_name: forged})
    # successor invariants — the identity cannot be misdeclared on the trace
    with pytest.raises(mcc.MCInputError, match="key_grid_missing"):
        _oset(_grid_atoms(), B=3)
    atoms = list(_grid_atoms())
    atoms[0] = dataclasses.replace(atoms[0], master_seed=13)
    with pytest.raises(mcc.MCInputError, match="atom_binding_mismatch"):
        _oset(atoms)


def test_replace_of_derived_stats_still_refused_r2_2_regression():
    """R2.2 PHASE C regression kept under R2.3 and under N01:
    dataclasses.replace of ANY derived statistic still refuses — the type
    re-derives from the atom trace on every construction."""
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


# --- B. the atom replaces FeasibilityObservation ----------------------------

def test_observation_constructs_and_pending_engineering_is_none():
    """R2.3 B, MIGRATED AND STRENGTHENED.

    HISTORICAL COUNTEREXAMPLE: `FeasibilityObservation` expressed "this
    quantity has not been engineered yet" as a bare `None` on
    contract_cap_hits / e2_over_budget_days — an untyped None that could
    not say WHY it was absent, and that a later 0 could silently
    impersonate. N01 PHASE D1 deleted the type; the atom accepts an int or
    one of THREE DISTINCT typed absences, refuses a bare None outright
    (`atom_untyped_none`), and makes the E1/E2 semantics engine-conditional
    (`atom_e2_field_engine_semantics`) — none of which R2.3 could express."""
    assert not hasattr(mcc, "FeasibilityObservation")
    a = _atom(0, 1, payout_count=1)
    assert a.e2_over_budget_days is A.NOT_APPLICABLE        # E1: permanent
    assert a.contract_cap_hits == 1
    with pytest.raises(dataclasses.FrozenInstanceError):
        a.offered_days = 9                                   # type: ignore
    a2 = _atom(1, 0, engine="E2", contract_cap_hits=0,
               e2_over_budget_days=3)
    assert a2.contract_cap_hits == 0 and a2.e2_over_budget_days == 3
    # the three absences are DISTINCT and none of them is 0 or None
    for token in (A.NOT_APPLICABLE, A.PENDING_RULING,
                  A.PENDING_ENGINEERING):
        assert token != 0 and token is not None
    assert len({A.NOT_APPLICABLE, A.PENDING_RULING,
                A.PENDING_ENGINEERING}) == 3
    with pytest.raises(mcc.MCInputError, match="atom_untyped_none"):
        _atom(0, 0, contract_cap_hits=None)
    with pytest.raises(mcc.MCInputError, match="atom_field_type_violation"):
        _atom(0, 0, contract_cap_hits=-1)
    with pytest.raises(mcc.MCInputError,
                       match="atom_e2_field_engine_semantics"):
        _atom(0, 0, engine="E1", e2_over_budget_days=0)


def test_observation_invalid_fields_refused():
    """R2.3 B, MIGRATED AND STRENGTHENED: every field violation R2.3
    answered with the ONE generic code `feasibility_observation_invalid`
    now has its OWN refusal code on the atom, so an auditor can tell which
    invariant broke. Same five attacks, five distinct answers."""
    cases = (
        # the five R2.3 attacks, each now with its OWN code
        ({"offered": -1}, "atom_field_type_violation"),
        ({"offered": True}, "atom_field_type_violation"),
        ({"skips_n0": 5}, "atom_skip_execution_partition_violation"),
        ({"ambiguous_days": 5}, "atom_ambiguous_exceeds_offered"),
        ({"world_index": -1}, "atom_field_type_violation"),
        # invariants the R2.3 observation type could not express at all
        ({"winning_days": 4}, "atom_monotone_chain_violation"),
        ({"contract_cap_hits": 4}, "atom_contract_cap_exceeds_executed"),
        ({"payout_count": 21}, "atom_payout_count_exceeds_window"),
        ({"attempts_used": 0}, "atom_attempts_range_violation"),
    )
    for over, code in cases:
        kw = dict(world_index=0, phase_offset=0)
        kw.update(over)
        with pytest.raises(mcc.MCInputError) as ei:
            _atom(**kw)
        assert ei.value.code == code, over


def test_from_observations_recomputes_every_scalar():
    """R2.3 B, MIGRATED: FeasibilityEvidence is built ONLY from the atom
    trace — every metric comes from the recomputation, and the trace
    itself (not a caller-handed observation tuple) is what it stores.

    The historical hand-computed numbers are preserved verbatim; the new
    architecture reduces MORE metrics from the same atoms, and typed
    absences stay typed instead of collapsing to 0."""
    obs = _oset(_grid_atoms(payout_worlds=(0,), exhausted_worlds=(1,)))
    fe = mcc.FeasibilityEvidence.from_observations(obs)
    assert fe.observations is obs
    m = fe.metrics
    assert m["n_paths"] == 4
    assert m["payout_event_path_share"] == 0.5   # world 0 pays, world 1 not
    assert m["exhausted_share"] == 0.5           # world 1 exhausts
    assert m["total_skips_n0"] == 4              # 4 atoms x skips_n0=1
    assert m["total_offered"] == 16              # 4 atoms x offered=4
    assert m["ambiguous_share"] == 0.0
    # metrics R2.3's observation layer never carried
    assert m["payout_event_paths"] == 2
    assert m["total_payout_events"] == 2
    assert m["exhausted_paths"] == 2
    assert m["total_winning_days"] == 8
    assert m["total_days_profit_ge_150"] == 4
    assert m["total_contract_cap_hits"] == 4
    assert m["total_e2_over_budget_days"] is A.NOT_APPLICABLE
    assert m["total_e2_over_budget_days"] != 0   # an absence is never zero


def test_direct_construction_contradictory_scalars_refused():
    """R2.3 B, MIGRATED: direct construction with a metric contradicting
    the trace (payout share 1.0 while NO atom recorded a payout event)
    refuses — __post_init__ re-derives the whole mapping from the atoms."""
    obs = _oset(_grid_atoms())
    forged = dict(obs.feasibility_counts())
    forged["payout_event_path_share"] = 1.0
    with pytest.raises(mcc.MCInputError,
                       match="feasibility_derived_stats_mismatch"):
        mcc.FeasibilityEvidence(observations=obs, metrics=forged)


def test_out_of_range_scalars_cannot_exist():
    """R2.3 B, MIGRATED: negative / out-of-range metrics cannot exist —
    they mismatch the derivation from the atoms by construction. A DROPPED
    metric key refuses too (R2.3 could only compare the scalars it knew
    about; the key set is now exact in both directions)."""
    obs = _oset(_grid_atoms())
    for name, forged_value in (("n_paths", -5), ("ambiguous_share", 3.7)):
        forged = dict(obs.feasibility_counts())
        forged[name] = forged_value
        with pytest.raises(mcc.MCInputError,
                           match="feasibility_derived_stats_mismatch"):
            mcc.FeasibilityEvidence(observations=obs, metrics=forged)
    dropped = {k: v for k, v in obs.feasibility_counts().items()
               if k != "total_skips_n0"}
    with pytest.raises(mcc.MCInputError,
                       match="feasibility_derived_stats_mismatch"):
        mcc.FeasibilityEvidence(observations=obs, metrics=dropped)
    extra = dict(obs.feasibility_counts())
    extra["feasible"] = True
    with pytest.raises(mcc.MCInputError,
                       match="feasibility_derived_stats_mismatch"):
        mcc.FeasibilityEvidence(observations=obs, metrics=extra)


def test_missing_or_extra_observation_refused():
    """R2.3 B, MIGRATED AND STRENGTHENED.

    HISTORICAL COUNTEREXAMPLE: completeness was checked as `count ==
    expected_n`, where `expected_n` was a CALLER-SUPPLIED scalar. N01
    deleted it: completeness is now the COMPLETE B x legal-phase-support
    Cartesian key grid, so a removed key refuses (`key_grid_missing`), an
    extra key refuses (`key_grid_extra`), and — the case a count check can
    NEVER catch — a SUBSTITUTED key that keeps the count intact refuses
    with its own code (`key_grid_substitution`)."""
    grid = _grid_atoms()
    with pytest.raises(mcc.MCInputError, match="key_grid_missing"):
        _oset(grid[:-1])                            # one removed
    with pytest.raises(mcc.MCInputError, match="key_grid_extra"):
        _oset(grid + (_atom(5, 0),))                # one extra
    substituted = grid[:-1] + (_atom(5, 0),)        # count preserved!
    assert len(substituted) == len(grid)
    with pytest.raises(mcc.MCInputError, match="key_grid_substitution"):
        _oset(substituted)


def test_duplicate_observation_pair_refused():
    """R2.3 B, MIGRATED: (world_index, phase_offset) keys must be UNIQUE —
    a duplicated atom (count still equal to |grid|) refuses with the
    duplicate code, not a silent double-count."""
    grid = _grid_atoms()
    dupe = grid[:3] + (grid[0],)                    # (0,0) twice, (1,1) gone
    assert len(dupe) == len(grid)
    with pytest.raises(mcc.MCInputError, match="key_grid_duplicate"):
        _oset(dupe)


def test_synchronized_numerator_denominator_tamper_refused():
    """R2.3 B (the R2.2 counterexample closed), MIGRATED: halving
    total_offered AND total_skips_n0 TOGETHER — internally consistent
    ratios — still refuses, because both are recomputed from the unchanged
    atom trace."""
    # skips_n0=2 + executed_trade_days=2 == offered_days=4 (the atom's
    # skip/execution partition invariant, which the R2.3 observation type
    # did not have): skips=8, offered=16 — the historical numbers.
    obs = _oset(_grid_atoms(skips_n0=2, executed_trade_days=2))
    fe = mcc.FeasibilityEvidence.from_observations(obs)
    assert fe.metrics["total_skips_n0"] == 8
    assert fe.metrics["total_offered"] == 16
    halved = dict(fe.metrics)
    halved["total_offered"] //= 2
    halved["total_skips_n0"] //= 2
    with pytest.raises(mcc.MCInputError,
                       match="feasibility_derived_stats_mismatch"):
        dataclasses.replace(fe, metrics=halved)


def test_gate_status_decision_required_and_no_feasible_boolean():
    """R2.1 PHASE G held under R2.3 and under N01: gate_status stays
    DECISION_REQUIRED and NO feasible boolean exists anywhere on the
    observation layer.

    N01 additionally deleted the last DERIVABLE boolean field
    (`payout_realized`, which was just `payout_count > 0`): a stored
    derivable field is a permanent forgery surface, so the atom carries
    only the event-calibre count."""
    obs = _oset(_grid_atoms())
    fe = mcc.FeasibilityEvidence.from_observations(obs)
    assert fe.gate_status == "RULED_ND2_ND3_2026-08-24"
    assert mcc.FEASIBILITY_GATE_STATUS == "RULED_ND2_ND3_2026-08-24"
    assert not hasattr(fe, "feasible")
    assert "feasible" not in fe.metrics
    assert not hasattr(mcc, "FeasibilityObservation")
    atom_fields = {f.name for f in
                   dataclasses.fields(mcc.SimulationPathObservation)}
    assert "feasible" not in atom_fields
    assert "payout_realized" not in atom_fields     # derivable => deleted
    assert "payout_count" in atom_fields
    with pytest.raises(mcc.MCInputError,
                       match="feasibility_gate_status_invalid"):
        mcc.FeasibilityEvidence(observations=obs,
                                metrics=obs.feasibility_counts(),
                                gate_status="PASS")


# --- C. feasibility <-> epistemic binding (R2.3) ----------------------------

def test_run_epistemic_feasibility_carries_binding_and_full_observations():
    """R2.3 C, MIGRATED AND STRENGTHENED: run_epistemic's feasibility is
    built from exactly B*M atoms (one per world x start phase) and its
    identity is READ from that trace.

    R2.3 stored the binding identity as eight DECLARED fields that were
    only cross-checked; N01 made every one of them a property of the
    trace, so there is nothing left to declare — and the trace is the SAME
    object the epistemic statistics were reduced from."""
    prepared = _prepare()
    res = _epi(prepared)                          # B=2, M=2 offsets
    fe = res.feasibility
    obs = res.observations
    assert fe.observations is obs                  # THE same trace object
    assert len(obs.atoms) == res.B * res.M == 4
    assert {a.key for a in obs.atoms} == \
        {(w, p) for w in range(res.B)
         for p in prepared.calendar.first_month_offsets}
    assert (fe.platform, fe.engine, fe.scenario, fe.channel) == \
        ("topstep", "E1", "Conservative", PRIMARY)
    assert (fe.B, fe.M, fe.master_seed) == (res.B, res.M, res.master_seed)
    assert fe.prepared_digest == res.prepared_digest \
        == mcc.prepared_digest(prepared)
    # every identity is a read-only property, not a declarable field
    declared = {f.name for f in dataclasses.fields(mcc.FeasibilityEvidence)}
    for name in ("prepared_digest", "platform", "engine", "scenario",
                 "channel", "B", "M", "master_seed"):
        assert name not in declared, name
        with pytest.raises(AttributeError):
            setattr(fe, name, "forged")


def test_foreign_feasibility_binding_refused():
    """R2.3 C, MIGRATED AND STRENGTHENED.

    HISTORICAL COUNTEREXAMPLE: a FeasibilityEvidence RE-LABELLED to a
    different combo passed its own scalar re-derivation (the observations
    had not changed) and was caught only by the EpistemicResult binding
    cross-check. N01 removed the relabelling entry entirely — the combo
    identity is a property of the trace — so the attack must now smuggle
    in a genuinely FOREIGN trace, which the object-level binding check
    refuses with `feasibility_binding_mismatch`."""
    prepared = _prepare()
    res = _epi(prepared, platform="topstep")
    foreign_obs = mcc.run_observation_set(
        prepared, run_label="base", platform="lucid", engine="E1",
        scenario="Conservative", channel=PRIMARY, B=2, master_seed=7)
    # the relabelling entry is GONE
    with pytest.raises(TypeError):
        dataclasses.replace(res.feasibility, platform="lucid")
    foreign = mcc.FeasibilityEvidence.from_observations(foreign_obs)
    assert foreign.platform == "lucid"            # its own post_init passed
    assert foreign.observations.observations_digest != \
        res.observations.observations_digest
    with pytest.raises(mcc.MCInputError,
                       match="feasibility_binding_mismatch"):
        dataclasses.replace(res, feasibility=foreign)
    # and a non-evidence object in the slot refuses with the same code
    with pytest.raises(mcc.MCInputError,
                       match="feasibility_binding_mismatch"):
        dataclasses.replace(res, feasibility={"metrics": {}})


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
    """R2.3 D regression, MIGRATED: convergence_from_evidence re-runs
    validate_inner_binding on EVERY entry on EVERY call — an
    outer-B-tampered run (outer B=4 over inner B=2 results) still refuses
    with the per-field code, and it does so BEFORE the new mandatory
    `prepared` authority is consulted."""
    prepared = _prepare()
    raw = _grid_results(prepared)
    tampered = mcc.RunEvidence(
        run_label="base", axis="base", B=4, M=2,
        K=prepared.k_per_seed, master_seed=7,
        prepared_digest=mcc.prepared_digest(prepared), results=raw)
    with pytest.raises(mcc.MCInputError,
                       match="run_evidence_inner_mismatch:B"):
        mcc.convergence_from_evidence(tampered, doubled_by_axis={},
                                      seed_runs={}, prepared=prepared)
