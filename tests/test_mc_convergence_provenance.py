"""R2.1 MC convergence provenance battery (synthetic fixtures ONLY).

Behaviour tests for the R2.1 contract on
`itsf.mc.consumer.convergence_from_evidence` and the MCSE computing seam
`EpistemicResult.from_world_means`:

  A. INNER/OUTER BINDING — a RunEvidence's OUTER metadata (B, M,
     master_seed, prepared_digest, plus the combo-id keys) must agree
     with its INNER EpistemicResults; every disagreement refuses with
     `run_evidence_inner_mismatch:<field>`. Metadata can never
     reclassify actual runs (the flagship counterexample: real B=2 runs
     wrapped in production-claiming outer fields).
  B. FROZEN PRODUCTION SCALES — after binding passes, the BASE run must
     carry the frozen scales (MC SS5: B=1000 worlds; SEED_MANIFEST
     k_per_seed=200; first frozen seed 7; theta_0.5) or refuse with
     `frozen_scale_violation`; a doubled-B run must be an ACTUAL 2x.
  C. AXIS REALITY — production convergence is STRUCTURALLY unsatisfiable
     today and the refusals are honest: the M axis is RESOLVED by IR-29
     (finite-support exhaustive enumeration — doubling it is FORBIDDEN,
     `m_axis_doubling_forbidden_by_ir29`; coverage is instead witnessed
     by an ExhaustiveSupportCertificate validated against the prepared
     input), the K axis has no grid-replay evidence
     (`k_axis_evidence_blocked_grid_replay`, source matrix R12), and
     binding / scale / seed-identity violations surface with their OWN
     codes BEFORE the M/K refusals.
  D. MCSE STRICTNESS — zero between-world SD with positive within-world
     SE is NOT convergence (MC SS5 rule (d) is unsatisfiable at SD == 0
     with real noise); non-finite / negative / empty samples refuse with
     `epistemic_samples_invalid`.

Fixture pattern copied from tests/test_mc_consumer.py — deliberately NOT
imported (that file is being edited in parallel). These tests are written
against the R2.1 CONTRACT and are expected to fail at runtime until the
consumer lands the checks; the contract, not current code, is the referee.
"""
from __future__ import annotations

import dataclasses
import hashlib
import inspect
import json
from types import SimpleNamespace

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
SECONDARY = mcc.SECONDARY_THETA_CHANNEL      # 'theta_0.3'

# frozen production scales (MC SS5; SEED_MANIFEST k_policy; IR DR-02)
PROD_B = 1000
PROD_K = 200
PROD_M = 21          # first-template-month start phases, ~21 ("非 200")
FIRST_SEED = 7

_PROD_DIGEST = hashlib.sha256(b"r2.1-synthetic-production-prepared").hexdigest()


# --- bundle fixtures (pattern copied from tests/test_mc_consumer.py) --------

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


def _authority(bundle) -> dict:
    return {n: hashlib.sha256(b).hexdigest() for n, b in bundle.items()}


def _snapshot() -> dict:
    return {"trial_id": TRIAL, "authorized_commit": COMMIT,
            "event_sequence": 15, "nested": {"list": [1, 2]}}


def _prepare(bundle=None, calendar=None):
    # integration point: main agent aligns this call — prefer the new
    # test-only prepare entry when it lands; fall back to the current one.
    b = bundle if bundle is not None else _bundle()
    cal = calendar if calendar is not None else _calendar()
    return mcc.prepare_mc_input_for_tests(
        b, authorization_snapshot=_snapshot(),
        custody_authority=mcc.CustodyAuthority.for_tests(b),
        test_only_calendar=cal)


# --- RunEvidence builders ----------------------------------------------------

def _grid_results(prepared, *, B, seed):
    """Full Primary-grid results from REAL small run_epistemic calls
    (build_worlds admits only the frozen seeds 7/13/31 — IR DR-02)."""
    results = {}
    for platform, policy in mcc.PRIMARY_COMBOS:
        for engine in mcc.ENGINES:
            cons = mcc.run_epistemic(prepared, platform=platform,
                                     engine=engine,
                                     scenario="Conservative",
                                     channel=PRIMARY, B=B, master_seed=seed)
            stress = mcc.run_epistemic(prepared, platform=platform,
                                       engine=engine, scenario="Stress",
                                       channel=PRIMARY, B=B,
                                       master_seed=seed)
            results[f"{platform}|{engine}|{policy}"] = (cons, stress)
    return results


def _inner_cons(results):
    return next(iter(results.values()))[0]


def _inner_M(results, fallback=2):
    return getattr(_inner_cons(results), "M", fallback)


def _evidence(results, *, label="base", axis="base", B=2, M=None, K=200,
              seed=7, digest=None):
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
    """Real small runs, built once: B=2/3/4 grids at the frozen seeds."""
    prepared = _prepare()
    return SimpleNamespace(
        prepared=prepared,
        base=_grid_results(prepared, B=2, seed=7),
        b3=_grid_results(prepared, B=3, seed=7),
        b4=_grid_results(prepared, B=4, seed=7),
        s13=_grid_results(prepared, B=2, seed=13),
        s31=_grid_results(prepared, B=2, seed=31),
    )


def _small_fixture(env):
    """FULLY COHERENT small-scale evidence: binding clean, the IR-29
    doubling axes {B, K} exactly doubled (B 2->4, K 200->400), seed set
    exactly {7,13,31}. Its ONLY sin is scale — the frozen-scale seal
    must be what refuses it."""
    base = _evidence(env.base)
    doubled = {
        "B": _evidence(env.b4, label="double_B", axis="B", B=4),
        "K": _evidence(env.base, label="double_K", axis="K", K=400),
    }
    seeds = {
        7: _evidence(env.base, label="seed_7", axis="seed"),
        13: _evidence(env.s13, label="seed_13", axis="seed", seed=13),
        31: _evidence(env.s31, label="seed_31", axis="seed", seed=31),
    }
    return base, doubled, seeds


# --- synthetic production-scale evidence (no real 1000-world runs) ----------

def _feas_for(*, B, M, digest, platform, engine, scenario, channel,
              seed) -> mcc.FeasibilityEvidence:
    """R2.3-aligned: feasibility evidence built from B*M synthetic raw
    observations with the binding octuple matching the result it rides
    on (EpistemicResult.__post_init__ cross-checks it)."""
    obs = [mcc.FeasibilityObservation(
        world_index=w, phase_offset=p, offered=2, skips_n0=0,
        payout_realized=True, payout_count=1, winning_days=1,
        days_profit_ge_150=0, exhausted=False, ambiguous_days=0)
        for w in range(B) for p in range(M)]
    return mcc.FeasibilityEvidence.from_observations(
        obs, expected_n=B * M, prepared_digest=digest, platform=platform,
        engine=engine, scenario=scenario, channel=channel, B=B, M=M,
        master_seed=seed)


def _from_world_means(world_means, ses, *, platform="topstep", engine="E1",
                      scenario="Conservative", channel=PRIMARY, B=None,
                      seed=FIRST_SEED, M=2, digest=None,
                      feasibility=None):
    """Direct call into the MCSE computing seam (R2.3-aligned: the
    feasibility evidence is built per call with a matching binding;
    `digest` resolves the module global at CALL time so the real
    prod-prepared digest is picked up once built)."""
    digest = digest if digest is not None else _PROD_DIGEST
    b = len(world_means) if B is None else B
    if feasibility is None and b > 0:
        feasibility = _feas_for(B=b, M=M, digest=digest,
                                platform=platform, engine=engine,
                                scenario=scenario, channel=channel,
                                seed=seed)
    return mcc.EpistemicResult.from_world_means(
        platform, engine, scenario, channel, tuple(world_means),
        within_world_ses=tuple(ses), B=b, M=M, master_seed=seed,
        prepared_digest_value=digest, feasibility=feasibility)


_PROD_PREPARED = None


def _prod_prepared():
    """Module-scoped REAL prepared input whose calendar enumerates
    exactly PROD_M start phases — the digest and the IR-29 support
    certificate for the synthetic production-scale evidence both bind to
    it (R2.3: a fabricated digest can no longer reach the K refusal)."""
    global _PROD_PREPARED, _PROD_DIGEST
    if _PROD_PREPARED is None:
        _PROD_PREPARED = _prepare(calendar=_calendar(n_days=25,
                                                     n_offsets=PROD_M))
        _PROD_DIGEST = mcc.prepared_digest(_PROD_PREPARED)
    return _PROD_PREPARED


def _prod_certificate():
    prepared = _prod_prepared()
    return mcc.ExhaustiveSupportCertificate(
        prepared_digest=mcc.prepared_digest(prepared),
        support=tuple(prepared.calendar.first_month_offsets))


def _prod_result(platform, engine, scenario, *, B=PROD_B, seed=FIRST_SEED,
                 M=PROD_M):
    _prod_prepared()                 # ensure _PROD_DIGEST is the real one
    means = tuple(100.0 + float(i % 13) for i in range(B))
    ses = tuple(0.01 for _ in range(B))
    return _from_world_means(means, ses, platform=platform, engine=engine,
                             scenario=scenario, B=B, seed=seed, M=M)


def _prod_grid(*, B=PROD_B, seed=FIRST_SEED, M=PROD_M):
    results = {}
    for platform, policy in mcc.PRIMARY_COMBOS:
        for engine in mcc.ENGINES:
            results[f"{platform}|{engine}|{policy}"] = (
                _prod_result(platform, engine, "Conservative", B=B,
                             seed=seed, M=M),
                _prod_result(platform, engine, "Stress", B=B, seed=seed,
                             M=M))
    return results


def _prod_fixture(*, base_seed=FIRST_SEED, base_K=PROD_K):
    """Frozen-scale-clean synthetic evidence (B=1000, M=21, K=200 unless a
    test tampers a knob), doubled on EXACTLY the IR-29 axes {B, K}. Every
    outer field is coherent with its inner results, so the only refusal
    left is the structural K one — unless a test breaks exactly one thing
    on purpose (an M entry is now itself a violation, IR-29)."""
    base = _evidence(_prod_grid(seed=base_seed), label="base", axis="base",
                     B=PROD_B, M=PROD_M, K=base_K, seed=base_seed)
    doubled = {
        "B": _evidence(_prod_grid(seed=base_seed, B=2 * PROD_B),
                       label="double_B", axis="B", B=2 * PROD_B, M=PROD_M,
                       K=base_K, seed=base_seed),
        "K": _evidence(_prod_grid(seed=base_seed), label="double_K",
                       axis="K", B=PROD_B, M=PROD_M, K=2 * base_K,
                       seed=base_seed),
    }
    seeds = {s: _evidence(_prod_grid(seed=s), label=f"seed_{s}",
                          axis="seed", B=PROD_B, M=PROD_M, K=base_K,
                          seed=s)
             for s in RESEARCH_BOOTSTRAP_SEEDS}
    return base, doubled, seeds


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
    scale code (metadata alone cannot make small runs production runs)."""
    base, doubled, seeds = _small_fixture(env)
    tampered = dataclasses.replace(base, **{field: value})
    with pytest.raises(mcc.MCInputError, match=code) as ei:
        mcc.convergence_from_evidence(tampered, doubled, seeds)
    assert ei.value.code.startswith("run_evidence_inner_mismatch")


def test_flagship_outer_K_claim_cannot_pass(env):
    """Flagship, K arm: RunEvidence.K has NO inner witness (EpistemicResult
    carries no grid-replay evidence — the harness does not exist, source
    matrix R12), so a tampered outer K cannot be caught by inner binding.
    It cannot PASS either: the K axis is refused wholesale
    (k_axis_evidence_blocked_grid_replay) and the frozen-scale seal pins
    base K == 200 — the deterministic production-scale pin is
    test_frozen_scale_seals_K_and_master_seed_at_production_scale."""
    base, doubled, seeds = _small_fixture(env)
    tampered = dataclasses.replace(base, K=999)
    with pytest.raises(mcc.MCInputError) as ei:
        mcc.convergence_from_evidence(tampered, doubled, seeds)
    # refused structurally, not misattributed to an inner-binding field
    assert not ei.value.code.startswith("run_evidence_inner_mismatch")


def test_relabelled_inner_B_refused_at_construction(env):
    """R2.1 A / R2.2 self-authentication: relabelling a REAL B=2 result's
    `.B` to 4 while its world_means tuples still hold 2 entries. R2.2
    moved this refusal UPSTREAM from the convergence check into the type
    constructor itself: EpistemicResult.__post_init__ re-derives every
    statistic from the raw samples and refuses the sample-count lie at
    CONSTRUCTION (len(world_means) != B -> epistemic_samples_invalid),
    dataclasses.replace included — the relabelled object can never even
    exist to become RunEvidence input. The ARRAY LENGTH is the witness,
    not the label."""
    cons = _inner_cons(env.base)
    with pytest.raises(mcc.MCInputError, match="epistemic_samples_invalid"):
        dataclasses.replace(cons, B=4)


def test_inner_prepared_digest_disagreement_refused(env):
    """R2.1 A, refusal moved UPSTREAM by R2.3: an inner result relabelled
    with a foreign prepared_digest can no longer even be CONSTRUCTED —
    its FeasibilityEvidence carries the original digest in the binding
    octuple and EpistemicResult.__post_init__ cross-checks it, so
    dataclasses.replace refuses at construction. The tampered object
    never exists to be laundered into RunEvidence, and the convergence-
    level inner/outer digest check remains as defense in depth."""
    c, _ = env.base["topstep|E1|P2"]
    with pytest.raises(mcc.MCInputError,
                       match="feasibility_binding_mismatch"):
        dataclasses.replace(c, prepared_digest="0" * 64)


def test_secondary_channel_inner_results_refused(env):
    """R2.1 A, refusal moved UPSTREAM by R2.3: convergence evidence is
    theta_0.5 ONLY (S0 §7 L133 — the secondary channel is report-only,
    不得事后升格). Relabelling an inner result theta_0.3 refuses at
    CONSTRUCTION: the feasibility binding octuple still says theta_0.5,
    so the upgraded-channel object can never exist."""
    c, _ = env.base["topstep|E1|P2"]
    with pytest.raises(mcc.MCInputError,
                       match="feasibility_binding_mismatch"):
        dataclasses.replace(c, channel=SECONDARY)


def test_combo_key_platform_swap_refused(env):
    """R2.1 A: the combo-id key is a claim about its inner results —
    topstep results filed under the lucid key refuse with the combo
    binding code (no cross-combo relabelling)."""
    _, doubled, seeds = _small_fixture(env)
    results = dict(env.base)
    results["lucid|E1|P2"] = env.base["topstep|E1|P2"]
    base = _evidence(results)
    with pytest.raises(mcc.MCInputError,
                       match="run_evidence_inner_mismatch:combo"):
        mcc.convergence_from_evidence(base, doubled, seeds)


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
        mcc.convergence_from_evidence(base, doubled, seeds)


# =============================================================================
# B. Frozen production scales
# =============================================================================

def test_frozen_scale_refuses_coherent_small_runs(env):
    """R2.1 B: a FULLY COHERENT small fixture — binding clean, doubling
    exact, seed set exact — must still refuse: Checkpoint-0 convergence
    evidence carries the frozen production scales (MC SS5 B=1000;
    SEED_MANIFEST k_per_seed=200; base seed = first frozen seed 7) or it
    is not Checkpoint-0 evidence at all."""
    assert mcc.B_WORLDS_FROZEN == PROD_B == 1000
    assert mcc.K_PER_SEED_FROZEN == PROD_K == 200
    assert tuple(RESEARCH_BOOTSTRAP_SEEDS) == (7, 13, 31)
    base, doubled, seeds = _small_fixture(env)
    with pytest.raises(mcc.MCInputError, match="frozen_scale_violation"):
        mcc.convergence_from_evidence(base, doubled, seeds)


def test_frozen_scale_seals_K_and_master_seed_at_production_scale():
    """R2.1 B: at production scale with binding clean and doubling
    coherent, the frozen-scale seal is what pins the fields no inner
    evidence can witness — base K != 200 (K-run kept at an exact 2x of
    the tampered claim so ONLY the seal can object), and a base seed that
    is a frozen seed but not the FIRST one (7)."""
    base, doubled, seeds = _prod_fixture(base_K=999)
    with pytest.raises(mcc.MCInputError, match="frozen_scale_violation"):
        mcc.convergence_from_evidence(base, doubled, seeds)
    base13, doubled13, seeds13 = _prod_fixture(base_seed=13)
    with pytest.raises(mcc.MCInputError, match="frozen_scale_violation"):
        mcc.convergence_from_evidence(base13, doubled13, seeds13)


def test_doubled_B_metadata_2x_without_2x_arrays_refused(env):
    """R2.1 B: the doubled-B run must be an ACTUAL 2x — outer B=4 wrapped
    around inner B=2 arrays is caught by the binding check (A) on the
    doubled run itself, before any scale arithmetic."""
    base, doubled, seeds = _small_fixture(env)
    doubled = dict(doubled)
    doubled["B"] = _evidence(env.base, label="double_B", axis="B", B=4)
    with pytest.raises(mcc.MCInputError,
                       match="run_evidence_inner_mismatch:B"):
        mcc.convergence_from_evidence(base, doubled, seeds)


def test_non_double_B_scale_refused(env):
    """R2.1 B: a coherent (outer == inner == 3) B-axis run over a B=2 base
    is not a doubling — refused with the doubling-scale code, its OWN
    code, before the M/K structural refusals."""
    base, doubled, seeds = _small_fixture(env)
    doubled = dict(doubled)
    doubled["B"] = _evidence(env.b3, label="double_B", axis="B", B=3)
    with pytest.raises(mcc.MCInputError, match="doubling_scale_violation"):
        mcc.convergence_from_evidence(base, doubled, seeds)


# =============================================================================
# C. Axis reality — production convergence is structurally unsatisfiable
# =============================================================================

def test_missing_doubling_axes_refused():
    """R2.1 C: convergence rule (a) doubles B, M AND K each (MC SS5) — a
    doubled_by_axis missing the M and K axes refuses on the axis set."""
    base, doubled, seeds = _prod_fixture()
    for subset in ({}, {"B": doubled["B"]}):
        with pytest.raises(mcc.MCInputError,
                           match="doubling_axes_violation"):
            mcc.convergence_from_evidence(
                base, subset, seeds,
                m_support_certificate=_prod_certificate(),
                prepared=_prod_prepared())


def test_m_axis_entry_refused_by_ir29():
    """R2.1 C, re-ruled by IR-29 (R2.3 named prompt): M is the
    EXHAUSTIVELY ENUMERATED start-phase set (MC SS5, first template
    month, "非 200") — a finite fully-enumerated support has no
    convergence question, so doubling it is FORBIDDEN outright and its
    coverage is witnessed by the ExhaustiveSupportCertificate instead.
    ANY M entry in doubled_by_axis refuses with the IR-29 code, before
    the certificate is even consulted."""
    assert (mcc.M_AXIS_DOUBLING_STATUS
            == "RESOLVED_BY_IR29_EXHAUSTIVE_SUPPORT_CERTIFICATE")
    assert mcc.DOUBLING_AXES == frozenset({"B", "K"})
    base, doubled, seeds = _prod_fixture()
    doubled = dict(doubled)
    doubled["M"] = _evidence(
        _prod_grid(M=2 * PROD_M), label="double_M", axis="M", B=PROD_B,
        M=2 * PROD_M, K=PROD_K, seed=FIRST_SEED)
    with pytest.raises(mcc.MCInputError,
                       match="m_axis_doubling_forbidden_by_ir29"):
        mcc.convergence_from_evidence(base, doubled, seeds)


def test_k_axis_entry_refused_no_grid_replay_evidence():
    """R2.1 C: no grid-replay harness exists (source matrix R12; GRID
    Option B supplement MC-DS-S001 is BUILT but not executed) — a K entry
    is metadata impersonating evidence and refuses in its own right. With
    a VALID IR-29 support certificate presented, this is the terminal
    refusal: production convergence stays structurally unsatisfiable
    until the day-strata supplement is actually sealed."""
    base, doubled, seeds = _prod_fixture()
    with pytest.raises(mcc.MCInputError,
                       match="k_axis_evidence_blocked_grid_replay"):
        mcc.convergence_from_evidence(
            base, doubled, seeds,
            m_support_certificate=_prod_certificate(),
            prepared=_prod_prepared())


def test_seed_set_must_be_exactly_the_frozen_three():
    """R2.1 C: convergence rule (b) runs EXACTLY the frozen seeds 7/13/31
    (IR DR-02) — a missing seed and a smuggled extra one both refuse with
    the seed-set code, before the M/K structural refusals."""
    base, doubled, seeds = _prod_fixture()
    missing = {k: v for k, v in seeds.items() if k != 31}
    with pytest.raises(mcc.MCInputError, match="seed_set_violation"):
        mcc.convergence_from_evidence(base, doubled, missing)
    extra = dict(seeds)
    extra[99] = _evidence(_prod_grid(seed=99), label="seed_99",
                          axis="seed", B=PROD_B, M=PROD_M, K=PROD_K,
                          seed=99)
    with pytest.raises(mcc.MCInputError, match="seed_set_violation"):
        mcc.convergence_from_evidence(base, doubled, extra)


def test_seed_run_inner_seed_must_match_its_key():
    """R2.1 C: a seed run filed under key 13 whose ACTUAL (inner == outer)
    master seed is 7 refuses with the master_seed binding code — the dict
    key is a claim about the run, not a label."""
    base, doubled, seeds = _prod_fixture()
    seeds = dict(seeds)
    seeds[13] = _evidence(_prod_grid(seed=7), label="seed_13", axis="seed",
                          B=PROD_B, M=PROD_M, K=PROD_K, seed=7)
    with pytest.raises(mcc.MCInputError,
                       match="run_evidence_inner_mismatch:master_seed"):
        mcc.convergence_from_evidence(base, doubled, seeds)


# =============================================================================
# D. MCSE strictness (EpistemicResult.from_world_means, called directly)
# =============================================================================

def test_zero_between_world_sd_with_real_noise_is_not_converged():
    """R2.1 D: MC SS5 rule (d) bounds within-world MCSE by 10% of the
    between-world SD — at SD == 0 with max SE > 0 that bound is
    UNSATISFIABLE, so mcse_ok must be False (degenerate spread is not a
    convergence free pass)."""
    r = _from_world_means((5.0, 5.0, 5.0), (0.5, 0.4, 0.0))
    assert r.between_world_sd == 0.0
    assert r.max_within_world_se > 0.0
    assert r.mcse_ok is False


def test_genuinely_noise_free_degenerate_result_is_converged():
    """R2.1 D: SD == 0 AND max SE == 0 — a genuinely noise-free result —
    satisfies rule (d) trivially; mcse_ok True."""
    r = _from_world_means((5.0, 5.0, 5.0), (0.0, 0.0, 0.0))
    assert r.between_world_sd == 0.0 and r.max_within_world_se == 0.0
    assert r.mcse_ok is True


@pytest.mark.parametrize("means,ses", [
    ((float("nan"), 1.0, 2.0), (0.0, 0.0, 0.0)),
    ((float("inf"), 1.0, 2.0), (0.0, 0.0, 0.0)),
    ((1.0, 2.0, 3.0), (-0.1, 0.0, 0.0)),
    ((1.0, 2.0, 3.0), (float("nan"), 0.0, 0.0)),
    ((), ()),
], ids=["nan-mean", "inf-mean", "negative-se", "nan-se", "empty"])
def test_invalid_epistemic_samples_refused(means, ses):
    """R2.1 D: NaN/inf world means, negative or NaN within-world SEs, and
    an empty sample set are not statistics — they refuse with
    epistemic_samples_invalid rather than flowing into quantiles."""
    with pytest.raises(mcc.MCInputError, match="epistemic_samples_invalid"):
        _from_world_means(means, ses)
