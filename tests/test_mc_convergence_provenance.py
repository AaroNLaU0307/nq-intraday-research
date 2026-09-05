"""R2.1 MC convergence provenance battery (synthetic fixtures ONLY).

MIGRATED TO THE N01 UNIFIED ATOM LAYER. Every counterexample this file
historically closed is re-expressed against the new architecture; none was
dropped or softened. Where an attack ENTRY was deleted outright
(`EpistemicResult.from_world_means`, the declarable identity fields, the
caller-supplied `m_support_certificate`), the test proves the entry is gone
AND re-states the same invariant on its successor, which refuses earlier
and at CONTENT level rather than at label level.

  A. INNER/OUTER BINDING — a RunEvidence's OUTER metadata (B, M,
     master_seed, prepared_digest, plus the combo-id keys) must agree with
     its INNER EpistemicResults; every disagreement refuses with
     `run_evidence_inner_mismatch:<field>`. Metadata can never reclassify
     actual runs (the flagship counterexample: real B=2 runs wrapped in
     production-claiming outer fields). Under N01 the inner results
     themselves are no longer LABELLED at all — every identity is reduced
     from the atom trace — so the relabelling attacks now die one layer
     lower, inside `ObservationSet`.
  B. FROZEN PRODUCTION SCALES — after binding passes, the BASE run must
     carry the frozen scales (MC SS5: B=1000 worlds; SEED_MANIFEST
     k_per_seed=200; first frozen seed 7; theta_0.5) or refuse with
     `frozen_scale_violation`; a doubled-B run must be an ACTUAL 2x, and
     under N01 also a CONTENT-level 2x (world-table prefix witness).
  C. AXIS REALITY — production convergence is STRUCTURALLY unsatisfiable
     today and the refusals are honest: the M axis is RESOLVED by IR-29
     (doubling FORBIDDEN, `m_axis_doubling_forbidden_by_ir29`; coverage
     witnessed by an ExhaustiveSupportCertificate that N01 now DERIVES
     from the real atom trace instead of accepting from the caller), the
     K axis has no grid-replay evidence
     (`k_axis_evidence_blocked_grid_replay`, source matrix R12), and
     binding / scale / seed-identity violations surface with their OWN
     codes BEFORE the M/K refusals.
  D. MCSE STRICTNESS — zero between-world SD with positive within-world
     SE is NOT convergence (MC SS5 rule (d) is unsatisfiable at SD == 0
     with real noise); non-finite / negative / empty samples refuse.

SCALE DISCIPLINE (main-agent ruling, N01 migration round). Production-
scale fixtures are no longer buildable: one production RunEvidence is
B=1000 x M=21 x 8 sets ~= 168k atoms and a convergence fixture ~1M
objects. The frozen scale CONSTANTS are therefore pinned by ONE dedicated
value test — `test_frozen_scale_constants_are_pinned_at_production_values`
— and the LOGIC tests that must reach past the frozen-scale seal
monkeypatch `itsf.mc.consumer.B_WORLDS_FROZEN` down (pytest's
`monkeypatch` fixture, auto-restored, module attribute only, never a
global rewrite). `K_PER_SEED_FROZEN` and `BASE_MASTER_SEED` are
deliberately NOT patched anywhere: K is a pure scalar and the seed is a
pure identity, so the fixtures carry their REAL production values (200 and
7) and the seal is tested against the genuine constants. Every
monkeypatching test names the pin test in its docstring.
"""
from __future__ import annotations

import dataclasses
import hashlib
import inspect
import json
import math
from types import SimpleNamespace

import pytest

from conftest import make_trade_path
from itsf.contracts import RESEARCH_BOOTSTRAP_SEEDS
from itsf.mc import atoms as A
from itsf.mc import consumer as mcc
from itsf.mc.orchestrator import TemplateDay
from itsf.s0.report import record_to_formal_dict

TRIAL = "S0-T001"
COMMIT = "876c1b74131b4ab1a89dce433ecce646ba481f8c"
TP_DAYS = ("2026-08-03", "2026-08-05", "2026-08-07")
FP_DAYS = ("2026-08-04", "2026-08-06")
ALL_DAYS = tuple(sorted(TP_DAYS + FP_DAYS))
PRIMARY = mcc.PRIMARY_THETA_CHANNEL          # 'theta_0.5'
SECONDARY = mcc.SECONDARY_THETA_CHANNEL      # 'theta_0.3'

# frozen production scales (MC SS5; SEED_MANIFEST k_policy; IR DR-02).
# These names are the VALUES the pin test asserts; the logic tests below
# run at a monkeypatched-down B so the deep decision points are reachable.
PROD_B = 1000
PROD_K = 200
PROD_M = 21          # first-template-month start phases, ~21 ("非 200")
FIRST_SEED = 7

# hermetic small scale used by the logic tests
SMALL_B = 2
SMALL_M = 2


# --- bundle fixtures (pattern copied from tests/test_mc_consumer.py) --------

def _record_row(date: str, engine: str, scn: str, pnl: float) -> dict:
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


def _prepare(bundle=None, calendar=None):
    b = bundle if bundle is not None else _bundle()
    cal = calendar if calendar is not None else _calendar()
    return mcc.prepare_mc_input_for_tests(
        b, authorization_snapshot=_snapshot(),
        custody_authority=mcc.CustodyAuthority.for_tests(b),
        test_only_calendar=cal)


# --- RunEvidence builders ----------------------------------------------------

def _grid_results(prepared, *, B, seed, run_label="base"):
    """Full Primary-grid results from REAL small runs (build_worlds admits
    only the frozen seeds 7/13/31 — IR DR-02).

    N01: the run label is threaded into `run_observation_set` so each
    ObservationSet's `set_key` genuinely names the run it belongs to — the
    B-doubling world-prefix witness matches base and doubled sets by that
    key, so a mislabelled trace cannot be laundered through it."""
    results = {}
    for platform, policy in mcc.PRIMARY_COMBOS:
        for engine in mcc.ENGINES:
            cons = mcc.EpistemicResult.from_observations(
                mcc.run_observation_set(
                    prepared, run_label=run_label, platform=platform,
                    engine=engine, scenario="Conservative",
                    channel=PRIMARY, B=B, master_seed=seed))
            stress = mcc.EpistemicResult.from_observations(
                mcc.run_observation_set(
                    prepared, run_label=run_label, platform=platform,
                    engine=engine, scenario="Stress", channel=PRIMARY,
                    B=B, master_seed=seed))
            results[f"{platform}|{engine}|{policy}"] = (cons, stress)
    return results


def _inner_cons(results):
    return next(iter(results.values()))[0]


def _inner_M(results, fallback=SMALL_M):
    return getattr(_inner_cons(results), "M", fallback)


def _evidence(results, *, label="base", axis="base", B=SMALL_B, M=None,
              K=PROD_K, seed=FIRST_SEED, digest=None):
    """RunEvidence wrapper; outer fields default to COHERENT values read
    from the inner results, so tests tamper exactly one thing at a time."""
    return mcc.RunEvidence(
        run_label=label, axis=axis, B=B,
        M=M if M is not None else _inner_M(results),
        K=K, master_seed=seed,
        prepared_digest=(digest if digest is not None
                         else _inner_cons(results).prepared_digest),
        results=dict(results))


@pytest.fixture(scope="module")
def env():
    """Real small runs, built once. Labels match the run each grid plays,
    so `set_key`s are honest."""
    prepared = _prepare()
    return SimpleNamespace(
        prepared=prepared,
        base=_grid_results(prepared, B=2, seed=7, run_label="base"),
        b3=_grid_results(prepared, B=3, seed=7, run_label="double_B"),
        b4=_grid_results(prepared, B=4, seed=7, run_label="double_B"),
        b4s13=_grid_results(prepared, B=4, seed=13, run_label="double_B"),
        dk=_grid_results(prepared, B=2, seed=7, run_label="double_K"),
        s7=_grid_results(prepared, B=2, seed=7, run_label="seed_7"),
        s13=_grid_results(prepared, B=2, seed=13, run_label="seed_13"),
        s31=_grid_results(prepared, B=2, seed=31, run_label="seed_31"),
        base13=_grid_results(prepared, B=2, seed=13, run_label="base"),
    )


def _small_fixture(env, *, base_seed=FIRST_SEED, base_K=PROD_K):
    """FULLY COHERENT evidence: binding clean, the IR-29 doubling axes
    {B, K} exactly doubled (B 2->4, K 200->400), seed set exactly
    {7,13,31}, and the doubled-B run a genuine content-level extension of
    the base world table. Its ONLY sin is scale — the frozen-scale seal
    must be what refuses it (unless a test tampers exactly one knob)."""
    if base_seed == FIRST_SEED:
        base_grid, b4_grid = env.base, env.b4
    else:
        base_grid, b4_grid = env.base13, env.b4s13
    base = _evidence(base_grid, K=base_K, seed=base_seed)
    doubled = {
        "B": _evidence(b4_grid, label="double_B", axis="B", B=4,
                       K=base_K, seed=base_seed),
        "K": _evidence(env.dk, label="double_K", axis="K",
                       K=2 * base_K, seed=FIRST_SEED)
        if base_seed == FIRST_SEED else
        _evidence(env.base13, label="double_K", axis="K", K=2 * base_K,
                  seed=base_seed),
    }
    seeds = {
        7: _evidence(env.s7, label="seed_7", axis="seed"),
        13: _evidence(env.s13, label="seed_13", axis="seed", seed=13),
        31: _evidence(env.s31, label="seed_31", axis="seed", seed=31),
    }
    return base, doubled, seeds


# --- hand-built atom traces (the N01 successor of the deleted
# --- `EpistemicResult.from_world_means` seam: to obtain an intended
# --- statistic you must now build the TRACE that produces it) --------------

_D_PREP = "a" * 64
_D_CFG = "b" * 64


def _atom(world_index, phase_offset, ev, **over):
    kw = dict(
        prepared_digest=_D_PREP, lifecycle_config_digest=_D_CFG,
        world_index=world_index,
        world_digest=hashlib.sha256(
            f"world-{world_index}".encode("utf-8")).hexdigest(),
        phase_offset=phase_offset, platform="topstep", engine="E1",
        scenario="Conservative", theta_channel=PRIMARY, master_seed=7,
        monthly_prop_operating_ev=ev, days_in_window=20, offered_days=4,
        executed_trade_days=3, skips_n0=1, payout_count=0, winning_days=2,
        days_profit_ge_150=1, qualifying_days=1, exhausted=False,
        ambiguous_days=0, attempts_used=1, b2f_used=0,
        contract_cap_hits=1, e2_over_budget_days=A.NOT_APPLICABLE,
        e2_intraday_over_budget_days=A.NOT_APPLICABLE)
    kw.update(over)
    return A.SimulationPathObservation(**kw)


def _trace_with_world_evs(per_world_evs, **over):
    """An ObservationSet whose per-world MEANS and within-world SEs are
    exactly the ones the caller intends — expressed the only way N01
    allows: by choosing the per-(world, phase) atom EVs they reduce from."""
    support = tuple(range(len(per_world_evs[0])))
    atoms = [_atom(w, p, float(ev))
             for w, evs in enumerate(per_world_evs)
             for p, ev in zip(support, evs)]
    kw = dict(run_label="base", platform="topstep", engine="E1",
              scenario="Conservative", theta_channel=PRIMARY,
              sizing_policy="P2", B=len(per_world_evs), master_seed=7,
              prepared_digest=_D_PREP, lifecycle_config_digest=_D_CFG,
              legal_phase_support=support)
    kw.update(over)
    return A.ObservationSet.from_atoms(atoms, **kw)


def _epi_with_world_evs(per_world_evs, **over):
    return mcc.EpistemicResult.from_observations(
        _trace_with_world_evs(per_world_evs, **over))


def _retrace(obs, atoms, **over):
    """Rebuild an ObservationSet around a modified atom list, keeping its
    declared digest honest, so ONLY a real invariant can catch the edit."""
    kw = dict(run_label=obs.run_label, platform=obs.platform,
              engine=obs.engine, scenario=obs.scenario,
              theta_channel=obs.theta_channel,
              sizing_policy=obs.sizing_policy, B=obs.B,
              master_seed=obs.master_seed,
              prepared_digest=obs.prepared_digest,
              lifecycle_config_digest=obs.lifecycle_config_digest,
              legal_phase_support=obs.legal_phase_support)
    kw.update(over)
    return A.ObservationSet.from_atoms(atoms, **kw)


# =============================================================================
# THE CONSTANT PIN (main-agent ruling): frozen values live here and ONLY
# here, so the logic tests below may scale down without weakening anything.
# =============================================================================

def test_frozen_scale_constants_are_pinned_at_production_values():
    """VALUE PIN — the frozen Checkpoint-0 scales, asserted directly and
    independently of any fixture.

    Every test in this file (and in tests/test_mc_cold_replay.py) that
    monkeypatches `mcc.B_WORLDS_FROZEN` down names THIS test: the constant
    truth is nailed here, the decision LOGIC is exercised there. A drift in
    either constant fails here loudly, whatever the logic tests do."""
    assert mcc.B_WORLDS_FROZEN == PROD_B == 1000
    assert mcc.K_PER_SEED_FROZEN == PROD_K == 200
    assert mcc.BASE_MASTER_SEED == FIRST_SEED == 7
    assert tuple(RESEARCH_BOOTSTRAP_SEEDS) == (7, 13, 31)
    assert mcc.DOUBLING_AXES == frozenset({"B", "K"})
    assert mcc.M_AXIS_DOUBLING_STATUS == \
        "RESOLVED_BY_IR29_EXHAUSTIVE_SUPPORT_CERTIFICATE"
    assert mcc.PRIMARY_THETA_CHANNEL == "theta_0.5"
    assert mcc.CRN_SCOPE_FROZEN == "shared_within_theta_engine_scenario"
    # the base seed is the FIRST frozen seed, not merely a frozen one
    assert mcc.BASE_MASTER_SEED == RESEARCH_BOOTSTRAP_SEEDS[0]


# =============================================================================
# A. Inner/outer binding — outer metadata must agree with inner results
# =============================================================================

@pytest.mark.parametrize("field,value,code", [
    ("B", PROD_B, "run_evidence_inner_mismatch:B"),
    ("M", PROD_M, "run_evidence_inner_mismatch:M"),
    ("master_seed", 13, "run_evidence_inner_mismatch:master_seed"),
], ids=["outer-B-claims-1000", "outer-M-claims-21",
        "outer-seed-claims-13"])
def test_flagship_outer_claims_cannot_reclassify_real_runs(
        env, field, value, code):
    """THE FLAGSHIP COUNTEREXAMPLE (R2.1 A): every inner result is a REAL
    run at B=2 / master_seed=7; the RunEvidence wrapper then CLAIMS the
    production scale (B=1000, M=21) or a different seed on its outer
    fields. Binding fires BEFORE any scale/axis check — the specific
    binding code, deterministically, never a pass and never the frozen-
    scale code (metadata alone cannot make small runs production runs).

    N01: the inner B and M are no longer inner LABELS either — B is the
    world domain of the atom key grid and M is |legal_phase_support|, both
    consequences of the trace — so the outer claim is now checked against
    executed content, not against another declaration."""
    base, doubled, seeds = _small_fixture(env)
    tampered = dataclasses.replace(base, **{field: value})
    with pytest.raises(mcc.MCInputError, match=code) as ei:
        mcc.convergence_from_evidence(tampered, doubled, seeds,
                                      prepared=env.prepared)
    assert ei.value.code.startswith("run_evidence_inner_mismatch")
    inner = _inner_cons(env.base)
    assert (inner.B, inner.M) == (SMALL_B, SMALL_M)
    assert inner.B == inner.observations.B == len(inner.world_means)
    assert inner.M == len(inner.observations.legal_phase_support)


def test_flagship_outer_K_claim_cannot_pass(env):
    """Flagship, K arm: RunEvidence.K has NO inner witness (EpistemicResult
    carries no grid-replay evidence — the harness does not exist, source
    matrix R12), so a tampered outer K cannot be caught by inner binding.
    It cannot PASS either: the K-axis cross-field invariant on the
    B-doubling run ("K moved on a B-doubling run") catches it first, the
    frozen-scale seal pins base K == 200 behind that, and the K axis is
    refused wholesale (k_axis_evidence_blocked_grid_replay) behind that
    again. The deterministic K pin is
    test_frozen_scale_seals_K_and_master_seed_at_production_scale."""
    base, doubled, seeds = _small_fixture(env)
    tampered = dataclasses.replace(base, K=999)
    with pytest.raises(mcc.MCInputError) as ei:
        mcc.convergence_from_evidence(tampered, doubled, seeds,
                                      prepared=env.prepared)
    # refused structurally, not misattributed to an inner-binding field
    assert not ei.value.code.startswith("run_evidence_inner_mismatch")
    # the B-doubling run's cross-field invariant sees K move under it
    assert ei.value.code == "doubling_scale_violation"
    assert "K moved on a B-doubling run" in str(ei.value)
    # ... and with the doubled runs' K moved in step, so the cross-field
    # invariant has nothing to say, the frozen-scale seal is what refuses
    lone = dict(doubled)
    lone["B"] = dataclasses.replace(doubled["B"], K=999)
    lone["K"] = dataclasses.replace(doubled["K"], K=2 * 999)
    with pytest.raises(mcc.MCInputError) as ei:
        mcc.convergence_from_evidence(tampered, lone, seeds,
                                      prepared=env.prepared)
    assert ei.value.code == "frozen_scale_violation"
    assert "K=999" in str(ei.value)
    # K really has no inner witness — no inner object exposes it at all
    assert not hasattr(_inner_cons(env.base), "K")


def test_relabelled_inner_B_refused_at_construction(env):
    """R2.1 A / R2.2 self-authentication, MIGRATED AND STRENGTHENED.

    HISTORICAL COUNTEREXAMPLE: relabelling a REAL B=2 result's `.B` to 4
    while its world_means tuple still held 2 entries. R2.2 answered at the
    EpistemicResult constructor (`epistemic_samples_invalid`, the array
    length being the witness).

    N01 deleted the declarable `.B` field entirely — B is a property of the
    atom trace — so `dataclasses.replace(cons, B=4)` is not even a legal
    call. The counterexample moves one layer down and gets STRONGER: the
    witness is no longer the length of a summary array but the COMPLETE
    Cartesian key grid, so a set claiming B=4 while carrying two worlds'
    atoms refuses with `key_grid_missing`, and (the case an array-length
    check could never see) a set that pads to the right COUNT with
    duplicate or out-of-domain world keys refuses with its own code."""
    cons = _inner_cons(env.base)
    assert "B" not in {f.name for f in
                       dataclasses.fields(mcc.EpistemicResult)}
    assert isinstance(type(cons).B, property)
    with pytest.raises(TypeError):
        dataclasses.replace(cons, B=4)
    obs = cons.observations
    with pytest.raises(mcc.MCInputError) as ei:
        _retrace(obs, list(obs.atoms), B=4)
    assert ei.value.code == "key_grid_missing"
    # padding to the right COUNT does not help: 8 atoms, but worlds 0..1
    # duplicated instead of worlds 0..3
    padded = list(obs.atoms) + list(obs.atoms)
    with pytest.raises(mcc.MCInputError) as ei:
        _retrace(obs, padded, B=4)
    assert ei.value.code == "key_grid_duplicate"


def test_inner_prepared_digest_disagreement_refused(env):
    """R2.1 A, MIGRATED AND STRENGTHENED.

    HISTORICAL COUNTEREXAMPLE: an inner result relabelled with a foreign
    `prepared_digest`. R2.3 caught it because the FeasibilityEvidence
    carried the original digest in its declared binding octuple.

    N01 binds the prepared digest into EVERY ATOM, so the attack must now
    rewrite the whole trace: relabelling only the container refuses with
    `atom_binding_mismatch`, and rewriting every atom too still leaves the
    RunEvidence outer/inner digest check
    (`run_evidence_inner_mismatch:prepared_digest`) — defence in depth, one
    named code per layer."""
    cons, _ = env.base["topstep|E1|P2"]
    assert "prepared_digest" not in {f.name for f in
                                     dataclasses.fields(
                                         mcc.EpistemicResult)}
    with pytest.raises(TypeError):
        dataclasses.replace(cons, prepared_digest="0" * 64)
    obs = cons.observations
    # (1) container relabelled, atoms untouched
    with pytest.raises(mcc.MCInputError) as ei:
        _retrace(obs, list(obs.atoms), prepared_digest="0" * 64)
    assert ei.value.code == "atom_binding_mismatch"
    # (2) whole trace rewritten — coherent, and still refused upstream
    rewritten = _retrace(
        obs, [dataclasses.replace(a, prepared_digest="0" * 64)
              for a in obs.atoms], prepared_digest="0" * 64)
    results = dict(env.base)
    results["topstep|E1|P2"] = (
        mcc.EpistemicResult.from_observations(rewritten),
        env.base["topstep|E1|P2"][1])
    bad = _evidence(results)
    with pytest.raises(mcc.MCInputError) as ei:
        bad.validate_inner_binding()
    assert ei.value.code == "run_evidence_inner_mismatch:prepared_digest"


def test_secondary_channel_inner_results_refused(env):
    """R2.1 A, MIGRATED AND STRENGTHENED: convergence evidence is theta_0.5
    ONLY (S0 §7 L133 — the secondary channel is report-only, 不得事后升格).

    HISTORICAL COUNTEREXAMPLE: relabelling an inner result theta_0.3.
    N01 removes the label: `channel` is a property of the trace. Upgrading
    the channel now requires rewriting the atoms, and there are two
    independent walls behind that — the container/atom binding
    (`atom_binding_mismatch`) and, for a genuine theta_0.3 run, the
    RunEvidence channel check (`run_evidence_inner_mismatch:channel`). The
    theta channel is ALSO inside `lifecycle_config_digest`, so a rewritten
    trace additionally fails the four-layer config equality."""
    cons, stress = env.base["topstep|E1|P2"]
    assert "channel" not in {f.name for f in
                             dataclasses.fields(mcc.EpistemicResult)}
    with pytest.raises(TypeError):
        dataclasses.replace(cons, channel=SECONDARY)
    obs = cons.observations
    with pytest.raises(mcc.MCInputError) as ei:
        _retrace(obs, list(obs.atoms), theta_channel=SECONDARY)
    assert ei.value.code == "atom_binding_mismatch"
    # a GENUINE theta_0.3 run is refused by the container check
    sec = mcc.EpistemicResult.from_observations(mcc.run_observation_set(
        env.prepared, run_label="base", platform="topstep", engine="E1",
        scenario="Conservative", channel=SECONDARY, B=2, master_seed=7))
    results = dict(env.base)
    results["topstep|E1|P2"] = (sec, stress)
    with pytest.raises(mcc.MCInputError) as ei:
        _evidence(results).validate_inner_binding()
    assert ei.value.code == "run_evidence_inner_mismatch:channel"
    # the channel is part of the lifecycle config identity, so the two
    # channels can never share a config digest either
    assert sec.lifecycle_config_digest != cons.lifecycle_config_digest


def test_combo_key_platform_swap_refused(env):
    """R2.1 A, MIGRATED AND STRENGTHENED: the combo-id key is a claim about
    its inner results — topstep results filed under the lucid key refuse.

    N01 PHASE D2 changed HOW: the `combo` string is a DISPLAY LABEL that is
    RENDERED from the inner authoritative fields and compared, never split
    back into platform/engine/policy. The refusal is therefore
    `combo_label_not_authoritative` — the label lost its authority, which
    is a stronger statement than "the label disagreed"."""
    _, doubled, seeds = _small_fixture(env)
    results = dict(env.base)
    results["lucid|E1|P2"] = env.base["topstep|E1|P2"]
    base = _evidence(results)
    with pytest.raises(mcc.MCInputError) as ei:
        mcc.convergence_from_evidence(base, doubled, seeds,
                                      prepared=env.prepared)
    assert ei.value.code == "combo_label_not_authoritative"
    cons = results["lucid|E1|P2"][0]
    assert A.combo_label(cons.platform, cons.engine,
                         cons.observations.sizing_policy) == "topstep|E1|P2"


def test_scenario_role_swap_refused(env):
    """R2.1 A: the (cons, stress) tuple positions are role claims — a
    Stress result in the Conservative slot refuses with the scenario
    binding code (S0 SS10.4 scenario roles are not permutable)."""
    _, doubled, seeds = _small_fixture(env)
    results = dict(env.base)
    c, s = results["topstep|E2|P2"]
    results["topstep|E2|P2"] = (s, c)          # roles swapped
    base = _evidence(results)
    with pytest.raises(mcc.MCInputError,
                       match="run_evidence_inner_mismatch:scenario"):
        mcc.convergence_from_evidence(base, doubled, seeds,
                                      prepared=env.prepared)


# =============================================================================
# B. Frozen production scales
# =============================================================================

def test_frozen_scale_refuses_coherent_small_runs(env):
    """R2.1 B: a FULLY COHERENT small fixture — binding clean, doubling
    exact (label, scale AND world content), seed set exact — must still
    refuse: Checkpoint-0 convergence evidence carries the frozen production
    scales (MC SS5 B=1000; SEED_MANIFEST k_per_seed=200; base seed = first
    frozen seed 7) or it is not Checkpoint-0 evidence at all.

    NO monkeypatch here: this test runs against the REAL constants, which
    is precisely what makes it the small-scale seal."""
    base, doubled, seeds = _small_fixture(env)
    with pytest.raises(mcc.MCInputError) as ei:
        mcc.convergence_from_evidence(base, doubled, seeds,
                                      prepared=env.prepared)
    assert ei.value.code == "frozen_scale_violation"
    assert str(mcc.B_WORLDS_FROZEN) in str(ei.value)


def test_frozen_scale_seals_K_and_master_seed_at_production_scale(
        env, monkeypatch):
    """R2.1 B: with binding clean and doubling coherent, the frozen-scale
    seal is what pins the fields no inner evidence can witness — base
    K != 200 (the K-run kept at an exact 2x of the tampered claim so ONLY
    the seal can object), and a base seed that is a frozen seed but not the
    FIRST one (7).

    SCALE: `B_WORLDS_FROZEN` is monkeypatched down to the fixture's real
    B so the B arm of the seal passes and the K / seed arms become the
    reachable ones. `K_PER_SEED_FROZEN` and `BASE_MASTER_SEED` are NOT
    patched — the fixture is sealed against their REAL production values.
    The constant truth is pinned independently by
    `test_frozen_scale_constants_are_pinned_at_production_values`."""
    monkeypatch.setattr(mcc, "B_WORLDS_FROZEN", SMALL_B)
    assert mcc.K_PER_SEED_FROZEN == PROD_K      # unpatched, real value
    assert mcc.BASE_MASTER_SEED == FIRST_SEED   # unpatched, real value

    base, doubled, seeds = _small_fixture(env, base_K=999)
    with pytest.raises(mcc.MCInputError) as ei:
        mcc.convergence_from_evidence(base, doubled, seeds,
                                      prepared=env.prepared)
    assert ei.value.code == "frozen_scale_violation"
    assert "K=999" in str(ei.value)

    base13, doubled13, seeds13 = _small_fixture(env, base_seed=13)
    with pytest.raises(mcc.MCInputError) as ei:
        mcc.convergence_from_evidence(base13, doubled13, seeds13,
                                      prepared=env.prepared)
    assert ei.value.code == "frozen_scale_violation"
    assert "seed=13" in str(ei.value)


def test_doubled_B_metadata_2x_without_2x_arrays_refused(env):
    """R2.1 B: the doubled-B run must be an ACTUAL 2x — outer B=4 wrapped
    around inner B=2 traces is caught by the binding check (A) on the
    doubled run itself, before any scale arithmetic."""
    base, doubled, seeds = _small_fixture(env)
    doubled = dict(doubled)
    doubled["B"] = _evidence(env.base, label="double_B", axis="B", B=4)
    with pytest.raises(mcc.MCInputError,
                       match="run_evidence_inner_mismatch:B"):
        mcc.convergence_from_evidence(base, doubled, seeds,
                                      prepared=env.prepared)


def test_non_double_B_scale_refused(env):
    """R2.1 B: a coherent (outer == inner == 3) B-axis run over a B=2 base
    is not a doubling — refused with the doubling-scale code, its OWN code,
    before the M/K structural refusals.

    N01 adds a CONTENT-level companion the R2.1 arithmetic could not do: a
    same-scale "double" whose world table was REDRAWN under a different
    seed refuses with `b_doubling_world_prefix_violation`, because a
    genuine B doubling EXTENDS the base world table rather than redrawing
    it."""
    base, doubled, seeds = _small_fixture(env)
    wrong_scale = dict(doubled)
    wrong_scale["B"] = _evidence(env.b3, label="double_B", axis="B", B=3)
    with pytest.raises(mcc.MCInputError,
                       match="doubling_scale_violation"):
        mcc.convergence_from_evidence(base, wrong_scale, seeds,
                                      prepared=env.prepared)
    redrawn = dict(doubled)
    redrawn["B"] = _evidence(env.b4s13, label="double_B", axis="B", B=4,
                             seed=13)
    with pytest.raises(mcc.MCInputError) as ei:
        mcc.convergence_from_evidence(base, redrawn, seeds,
                                      prepared=env.prepared)
    assert ei.value.code == "b_doubling_world_prefix_violation"
    assert "does not redraw it" in str(ei.value)


# =============================================================================
# C. Axis reality — production convergence is structurally unsatisfiable
# =============================================================================

def test_missing_doubling_axes_refused(env, monkeypatch):
    """R2.1 C: convergence rule (a) as amended by IR-29 owes exactly the
    axes {B, K} — a doubled_by_axis missing one refuses on the axis set.

    N01 makes this a DEEPER pass than R2.1's: `doubling_axes_violation` is
    the LAST refusal in the function, reachable only after the M
    exhaustive-support certificate has been successfully DERIVED from the
    real atom trace. Passing this test therefore also proves the base run
    covered its legal start-phase enumeration exactly once per world.

    SCALE: `B_WORLDS_FROZEN` monkeypatched down so the frozen-scale seal
    (which fires earlier) does not mask the axis-set check; the constants
    are pinned by
    `test_frozen_scale_constants_are_pinned_at_production_values`."""
    monkeypatch.setattr(mcc, "B_WORLDS_FROZEN", SMALL_B)
    base, doubled, seeds = _small_fixture(env)
    for subset in ({}, {"B": doubled["B"]}):
        with pytest.raises(mcc.MCInputError) as ei:
            mcc.convergence_from_evidence(base, subset, seeds,
                                          prepared=env.prepared)
        assert ei.value.code == "doubling_axes_violation"
    # the certificate really was derived on that path
    cert = mcc.derive_support_certificate(base, env.prepared)
    assert cert.support == tuple(env.prepared.calendar.first_month_offsets)


def test_m_axis_entry_refused_by_ir29(env, monkeypatch):
    """R2.1 C, re-ruled by IR-29 (R2.3 named prompt): M is the EXHAUSTIVELY
    ENUMERATED start-phase set (MC SS5, first template month, "非 200") — a
    finite fully-enumerated support has no convergence question, so
    doubling it is FORBIDDEN outright and its coverage is witnessed by the
    ExhaustiveSupportCertificate instead. ANY M entry in doubled_by_axis
    refuses with the IR-29 code, BEFORE the certificate is derived.

    SCALE: `B_WORLDS_FROZEN` monkeypatched down so the frozen-scale seal
    does not mask the IR-29 refusal; constants pinned by
    `test_frozen_scale_constants_are_pinned_at_production_values`."""
    monkeypatch.setattr(mcc, "B_WORLDS_FROZEN", SMALL_B)
    assert (mcc.M_AXIS_DOUBLING_STATUS
            == "RESOLVED_BY_IR29_EXHAUSTIVE_SUPPORT_CERTIFICATE")
    assert mcc.DOUBLING_AXES == frozenset({"B", "K"})
    assert "M" not in mcc.DOUBLING_AXES
    base, doubled, seeds = _small_fixture(env)
    doubled = dict(doubled)
    doubled["M"] = _evidence(env.base, label="double_M", axis="M")
    with pytest.raises(mcc.MCInputError,
                       match="m_axis_doubling_forbidden_by_ir29"):
        mcc.convergence_from_evidence(base, doubled, seeds,
                                      prepared=env.prepared)


def test_k_axis_entry_refused_no_grid_replay_evidence(env, monkeypatch):
    """R2.1 C, MIGRATED AND STRENGTHENED: no grid-replay harness exists
    (source matrix R12; GRID Option B supplement MC-DS-S001 is BUILT but
    not executed) — a K entry is metadata impersonating evidence and
    refuses in its own right. This is the TERMINAL refusal: production
    convergence stays structurally unsatisfiable until the day-strata
    supplement is actually sealed.

    STRENGTH: R2.1/R2.3 reached this point by handing convergence a
    HAND-BUILT `m_support_certificate`. N01 deleted that parameter — the
    certificate is DERIVED inside convergence from the real atom trace —
    so reaching the K refusal now proves the base run genuinely executed
    the exhaustive start-phase support. The second half of this test proves
    the derivation is load-bearing rather than decorative: break the
    executed phases and the M code, not the K code, comes out.

    SCALE: `B_WORLDS_FROZEN` monkeypatched down; constants pinned by
    `test_frozen_scale_constants_are_pinned_at_production_values`."""
    monkeypatch.setattr(mcc, "B_WORLDS_FROZEN", SMALL_B)
    assert "m_support_certificate" not in inspect.signature(
        mcc.convergence_from_evidence).parameters
    base, doubled, seeds = _small_fixture(env)
    with pytest.raises(mcc.MCInputError,
                       match="k_axis_evidence_blocked_grid_replay"):
        mcc.convergence_from_evidence(base, doubled, seeds,
                                      prepared=env.prepared)

    # the derived certificate is on that path: execute the WRONG phases
    # (same count, so no scalar check could notice) and the M code wins
    cid = "topstep|E1|P2"
    cons, stress = env.base[cid]
    obs = cons.observations
    wrong = [dataclasses.replace(a, phase_offset=7) if a.phase_offset == 1
             else a for a in obs.atoms]
    forged = _retrace(obs, wrong, legal_phase_support=(0, 7))
    results = dict(env.base)
    results[cid] = (mcc.EpistemicResult.from_observations(forged), stress)
    bad_base = _evidence(results)
    assert bad_base.M == SMALL_M                     # the COUNT still lies
    with pytest.raises(mcc.MCInputError) as ei:
        mcc.convergence_from_evidence(bad_base, doubled, seeds,
                                      prepared=env.prepared)
    assert ei.value.code.startswith("m_support_")


def test_seed_set_must_be_exactly_the_frozen_three(env):
    """R2.1 C: convergence rule (b) runs EXACTLY the frozen seeds 7/13/31
    (IR DR-02) — a missing seed and a smuggled extra one both refuse with
    the seed-set code, before the frozen-scale and M/K structural refusals.

    The extra-seed arm gives the attacker maximum power: seed 99 is not
    admissible to `bootstrap.build_worlds` at all, so the run is FABRICATED
    from a real seed-7 trace with every atom re-stamped to master_seed=99 —
    fully self-consistent, correct digests, correct lifecycle-config
    digest. It is still refused on identity alone."""
    base, doubled, seeds = _small_fixture(env)
    missing = {k: v for k, v in seeds.items() if k != 31}
    with pytest.raises(mcc.MCInputError, match="seed_set_violation"):
        mcc.convergence_from_evidence(base, doubled, missing,
                                      prepared=env.prepared)
    with pytest.raises(ValueError, match="master_seed"):
        mcc.run_observation_set(
            env.prepared, run_label="seed_99", platform="topstep",
            engine="E1", scenario="Conservative", channel=PRIMARY, B=2,
            master_seed=99)
    fabricated = {}
    for cid, (c, s) in env.s7.items():
        fabricated[cid] = tuple(
            mcc.EpistemicResult.from_observations(_retrace(
                r.observations,
                [dataclasses.replace(a, master_seed=99)
                 for a in r.observations.atoms],
                run_label="seed_99", master_seed=99))
            for r in (c, s))
    extra = dict(seeds)
    extra[99] = _evidence(fabricated, label="seed_99", axis="seed",
                          seed=99)
    extra[99].validate_inner_binding()          # fully self-consistent
    with pytest.raises(mcc.MCInputError, match="seed_set_violation"):
        mcc.convergence_from_evidence(base, doubled, extra,
                                      prepared=env.prepared)


def test_seed_run_inner_seed_must_match_its_key(env):
    """R2.1 C: a seed run filed under key 13 whose ACTUAL (inner == outer)
    master seed is 7 refuses with the master_seed binding code — the dict
    key is a claim about the run, not a label. Under N01 the inner seed is
    stamped on every atom, so the claim is checked against executed
    content."""
    base, doubled, seeds = _small_fixture(env)
    seeds = dict(seeds)
    seeds[13] = _evidence(env.s7, label="seed_13", axis="seed", seed=7)
    with pytest.raises(mcc.MCInputError,
                       match="run_evidence_inner_mismatch:master_seed"):
        mcc.convergence_from_evidence(base, doubled, seeds,
                                      prepared=env.prepared)
    inner = _inner_cons(env.s7)
    assert {a.master_seed for a in inner.observations.atoms} == {7}


# =============================================================================
# D. MCSE strictness
#
# MIGRATED: `EpistemicResult.from_world_means(world_means=..., ses=...,
# feasibility=...)` is DELETED (it took THREE independent caller inputs
# that were only cross-checked against each other, so a coherent triple
# could describe a run that never happened). To obtain an intended
# statistic the test must now build the ATOM TRACE that reduces to it —
# which is strictly more constrained: the trace also has to satisfy every
# atom cross-invariant and the complete key grid.
# =============================================================================

def test_from_world_means_seam_is_gone(env):
    """The deleted seam, pinned: no caller may hand `EpistemicResult` a
    summary vector under any name. Kept as an explicit red line because the
    four tests below are the migrated users of that seam."""
    assert not hasattr(mcc.EpistemicResult, "from_world_means")
    assert list(inspect.signature(
        mcc.EpistemicResult.from_observations).parameters) == \
        ["observations"]
    declared = {f.name for f in dataclasses.fields(mcc.EpistemicResult)}
    assert "observations" in declared
    for fn in (mcc.run_epistemic, mcc.run_observation_set):
        params = inspect.signature(fn).parameters
        assert "world_means" not in params
        assert "within_world_ses" not in params
        assert "feasibility" not in params


def test_zero_between_world_sd_with_real_noise_is_not_converged():
    """R2.1 D: MC SS5 rule (d) bounds within-world MCSE by 10% of the
    between-world SD — at SD == 0 with max SE > 0 that bound is
    UNSATISFIABLE, so mcse_ok must be False (degenerate spread is not a
    convergence free pass).

    MIGRATED: the degenerate spread is now produced by a REAL atom trace
    (three worlds whose per-phase EVs differ but whose means coincide),
    not by a declared pair of vectors."""
    r = _epi_with_world_evs([(4.5, 5.5), (4.0, 6.0), (4.75, 5.25)])
    assert r.world_means == (5.0, 5.0, 5.0)
    assert r.between_world_sd == 0.0
    assert r.max_within_world_se > 0.0
    assert r.mcse_ok is False


def test_genuinely_noise_free_degenerate_result_is_converged():
    """R2.1 D: SD == 0 AND max SE == 0 — a genuinely noise-free result —
    satisfies rule (d) trivially; mcse_ok True."""
    r = _epi_with_world_evs([(5.0, 5.0), (5.0, 5.0), (5.0, 5.0)])
    assert r.world_means == (5.0, 5.0, 5.0)
    assert r.between_world_sd == 0.0 and r.max_within_world_se == 0.0
    assert r.mcse_ok is True


@pytest.mark.parametrize("arm", ["nan-mean", "inf-mean", "negative-se",
                                 "nan-se", "empty"])
def test_invalid_epistemic_samples_refused(arm, monkeypatch):
    """R2.1 D, MIGRATED: NaN/inf world means, negative or NaN within-world
    SEs, and an empty sample set are not statistics — they never flow into
    quantiles.

    Under N01 there is no caller-supplied sample container, so each arm is
    re-expressed against the layer that can actually produce the value:

      nan-mean / inf-mean  the atom refuses a non-finite EV outright
                           (`atom_ev_non_finite`), AND the reduction's own
                           guard stays reachable from FINITE atoms via
                           float overflow, still refusing with the
                           historical `epistemic_samples_invalid`;
      negative-se / nan-se `stderr_of` cannot emit these from real atoms,
                           so (i) a declared SE vector that disagrees with
                           the derivation refuses
                           (`epistemic_derived_stats_mismatch`) and (ii)
                           the guard is proven LIVE by fault-injecting the
                           reducer inside this test process — it still
                           answers `epistemic_samples_invalid`;
      empty                an empty world domain cannot be declared
                           (`key_grid_scale_invalid`) nor left unfilled
                           (`key_grid_missing`), and the reduction
                           primitives still refuse an empty sample."""
    if arm in ("nan-mean", "inf-mean"):
        bad = float("nan") if arm == "nan-mean" else float("inf")
        with pytest.raises(mcc.MCInputError) as ei:
            _atom(0, 0, bad)
        assert ei.value.code == "atom_ev_non_finite"
        overflow = _trace_with_world_evs([(1e308, 1e308), (1.0, 2.0)])
        assert math.isinf(overflow.world_means()[0])
        with pytest.raises(mcc.MCInputError) as ei:
            mcc._epistemic_derived(overflow)
        assert ei.value.code == "epistemic_samples_invalid"
    elif arm in ("negative-se", "nan-se"):
        forged = -0.1 if arm == "negative-se" else float("nan")
        obs = _trace_with_world_evs([(1.0, 3.0), (2.0, 4.0), (3.0, 9.0)])
        res = mcc.EpistemicResult.from_observations(obs)
        assert all(s >= 0.0 and math.isfinite(s)
                   for s in res.within_world_ses)
        with pytest.raises(mcc.MCInputError) as ei:
            dataclasses.replace(
                res, within_world_ses=(forged,) + res.within_world_ses[1:])
        assert ei.value.code == "epistemic_derived_stats_mismatch"
        # FAULT INJECTION (test process only, auto-restored): prove the
        # non-finite / negative SE guard inside the reduction is live code
        monkeypatch.setattr(A, "stderr_of", lambda values: forged)
        with pytest.raises(mcc.MCInputError) as ei:
            mcc._epistemic_derived(obs)
        assert ei.value.code == "epistemic_samples_invalid"
    else:                                                   # empty
        with pytest.raises(mcc.MCInputError) as ei:
            _trace_with_world_evs([(1.0, 2.0)], B=0)
        assert ei.value.code == "key_grid_scale_invalid"
        with pytest.raises(mcc.MCInputError) as ei:
            A.ObservationSet.from_atoms(
                (), run_label="base", platform="topstep", engine="E1",
                scenario="Conservative", theta_channel=PRIMARY,
                sizing_policy="P2", B=1, master_seed=7,
                prepared_digest=_D_PREP, lifecycle_config_digest=_D_CFG,
                legal_phase_support=(0,))
        assert ei.value.code == "key_grid_missing"
        # N01 fix round (D-2): an EMPTY sample set is UNDEFINED, never
        # "zero noise". `stderr_of(())`/`sample_sd(())` used to return
        # 0.0, which would have handed MC SS5 rule (d) a free pass (an
        # MCSE of 0 is <= 10% of any SD). All three reducers now refuse
        # n == 0 alike; n == 1 keeps its genuine ddof-1 zero.
        for reducer in (A.mean_of, A.stderr_of, A.sample_sd):
            with pytest.raises(mcc.MCInputError) as ei:
                reducer(())
            assert ei.value.code == "epistemic_samples_invalid"
        assert A.stderr_of((5.0,)) == 0.0        # n == 1: a real zero
        with pytest.raises(mcc.MCInputError) as ei:
            A.percentile_linear((), 5)
        assert ei.value.code == "epistemic_samples_invalid"
        with pytest.raises(mcc.MCInputError) as ei:
            A.reduce_feasibility_counts(())
        assert ei.value.code == "feasibility_observations_incomplete"


# ===========================================================================
# The outer K has no inner witness — Fable V2 Medium, dispositioned 2026-08-26
# ===========================================================================

def test_run_evidence_binds_b_m_and_seed_to_every_inner_result():
    """What IS bound, so the next test's absence is legible as a gap."""
    import inspect

    # The binding lives in `validate_inner_binding`, NOT `__post_init__`
    # (which only deep-freezes the results mapping). The first draft of
    # this test read __post_init__, found none of the three, and failed —
    # a reminder to check what a lookup returns before asserting on it.
    src = inspect.getsource(mcc.RunEvidence.validate_inner_binding)
    for field in ("B", "M", "master_seed"):
        assert f"self.{field}" in src, (
            f"{field} is no longer cross-checked against inner results")


def test_the_outer_k_has_no_inner_witness_and_that_is_deliberate():
    """A GUARD THAT MUST INVERT, not one that must keep passing.

    `RunEvidence.__post_init__` binds outer B, M and master_seed to every
    inner `EpistemicResult`. It does NOT bind K — and it cannot: K appears
    nowhere in the atom layer. Not on `EpistemicResult`, not on
    `ObservationSet`, not on `SimulationPathObservation`. The epistemic
    layer is B worlds x M start phases and does not consume K at all, so
    the outer K is a caller-declared integer with nothing to check it
    against.

    That is exactly the impersonation N-D2 forbids — a K-non-consuming
    category called twice, wearing outer metadata that says `double_K`.
    It is unreachable TODAY because the consuming layer refuses the K axis
    outright (`k_axis_evidence_blocked_grid_replay`, pinned elsewhere in
    this file), and the source says so in as many words: "outer metadata
    may not impersonate it".

    WHEN THE K AXIS UNBLOCKS — GRID-B supplement sealed and
    `KReplayEvidence` wired (N11) — this test will fail, and the correct
    response is NOT to delete it. It is to bind the outer K to whatever
    inner witness then exists, exactly as B, M and master_seed are bound.
    Without that, a real K-doubled run and a relabelled base run stay
    indistinguishable.
    """
    import inspect

    from itsf.mc.atoms import ObservationSet, SimulationPathObservation

    witnesses = []
    for T in (mcc.EpistemicResult, ObservationSet, SimulationPathObservation):
        witnesses += [n for n in T.__dataclass_fields__
                      if n == "K" or n.lower().startswith("k_")]
    assert not witnesses, (
        f"an inner K witness now exists ({witnesses}) — bind the outer "
        "RunEvidence.K to it in __post_init__, the way B, M and "
        "master_seed are bound, and then update this test rather than "
        "deleting it")

    src = inspect.getsource(mcc.RunEvidence.validate_inner_binding)
    assert "self.K" not in src, (
        "K is now cross-checked but no inner witness was found — one of "
        "these two facts is stale")
