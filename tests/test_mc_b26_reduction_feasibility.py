"""B-26 — the ruled feasibility evidence composed into the verdict reduction.

The gates, their thresholds, the M4 composition and all three fail-closed
refusals already existed (M1-M5, ruled 2026-08-24). What was missing was that
nothing passed `combo_feasibility`'s product into
`_reduce_primary_from_base`, so `epistemic_go_gate_input` refused
`feasibility_gate_input_absent` and no Checkpoint-0 category was reachable.

These tests pin the WIRING and its identity binding. They do not re-test the
gate methodology — `test_mc_feasibility_gates.py` and
`test_mc_feasibility_composition.py` own that, and nothing here changes it.

Every fixture is synthetic. Any category or `feasible` value produced below is
an artifact of a fabricated 8-day bundle at B=2/M=2 and is NOT a research
result about the strategy.
"""
import dataclasses
import inspect

import pytest

import test_mc_cold_replay as CR
from itsf.mc import consumer as mcc
from itsf.mc import feasibility as fz


def _prepared(bundle=None, calendar=None):
    b = bundle if bundle is not None else CR._bundle()
    return mcc.prepare_mc_input_for_tests(
        b, authorization_snapshot={"trial_id": CR.TRIAL,
                                   "authorized_commit": CR.COMMIT},
        custody_authority=mcc.CustodyAuthority.for_tests(b),
        test_only_calendar=calendar or CR._calendar())


@pytest.fixture()
def prepared():
    return _prepared()


# ---------------------------------------------------------------------------
# CASE 1 — the valid path
# ---------------------------------------------------------------------------

def test_case1_the_reduction_composes_feasibility_and_reaches_a_category(
        prepared):
    """The B-26 dead end is gone: the reduction returns one VerdictInput per
    Primary combo and the category logic is reachable."""
    base = CR._evidence(prepared)
    reduction = mcc._reduce_primary_from_base(base, prepared=prepared)

    assert set(reduction) == set(base.results)
    from itsf.mc.verdict import VerdictInput, apply_verdict
    for cid, vi in reduction.items():
        assert type(vi) is VerdictInput
        assert isinstance(vi.feasible, bool)
    # ... and a category is produced. WHICH category is a synthetic-fixture
    # artifact and is deliberately not asserted as a value.
    assert apply_verdict(dict(reduction)).verdict in {"STOP", "GO", "beta",
                                                     "alpha"}


def test_case1_the_composed_evidence_carries_the_ruling_it_was_gated_under(
        prepared):
    """Composition goes through `combo_feasibility`, so the evidence carries
    the gate outcomes and the ruling id rather than a bare boolean."""
    base = CR._evidence(prepared)
    cid = sorted(base.results)[0]
    cons, stress = base.results[cid]
    evidence = fz.combo_feasibility(
        {cons.scenario: cons.observations, stress.scenario: stress.observations},
        prepared.day_sequences[mcc.PRIMARY_THETA_CHANNEL])
    assert type(evidence) is fz.ComboFeasibility
    assert evidence.ruling == fz.FEASIBILITY_RULING
    assert evidence.delegated is True            # DELEGATED=YES travels
    assert evidence.post_freeze_definition is True
    assert {o.gate for o in evidence.outcomes} == {"frequency", "payout",
                                                   "integer_position"}
    assert evidence.scenarios == fz.GATE_SCENARIOS


# ---------------------------------------------------------------------------
# CASE 2 — absent feasibility still fails closed
# ---------------------------------------------------------------------------

def test_case2_the_gate_still_refuses_when_no_evidence_is_supplied(prepared):
    """B-26 did NOT relax the gate. Called without evidence,
    `epistemic_go_gate_input` refuses exactly as before — the wiring added a
    producer, it did not add a default."""
    base = CR._evidence(prepared)
    cons, stress = base.results[sorted(base.results)[0]]
    with pytest.raises(mcc.MCInputError) as ei:
        mcc.epistemic_go_gate_input(cons, stress)
    assert ei.value.code == "feasibility_gate_input_absent"
    with pytest.raises(mcc.MCInputError) as ei:
        mcc.epistemic_go_gate_input(cons, stress, feasibility=None)
    assert ei.value.code == "feasibility_gate_input_absent"


def test_case2_a_mis_roled_pair_refuses_rather_than_gating_on_one_scenario(
        prepared):
    """M5 wants the path-shaped gates in BOTH scenarios. The reduction keys
    the evidence by each result's OWN scenario, so a pair carrying the same
    role twice collapses to one key and `combo_feasibility` refuses instead
    of evaluating the conjunction over whichever scenario turned up — which
    would weaken it permissively every time."""
    base = CR._evidence(prepared)
    cid = sorted(base.results)[0]
    cons, _stress = base.results[cid]
    forged = dict(base.results)
    forged[cid] = (cons, cons)                   # Conservative twice
    twisted = object.__new__(mcc.RunEvidence)
    for f in dataclasses.fields(base):
        object.__setattr__(twisted, f.name, getattr(base, f.name))
    object.__setattr__(twisted, "results", forged)
    with pytest.raises(mcc.MCInputError) as ei:
        mcc._reduce_primary_from_base(twisted, prepared=prepared)
    # MEASURED, not assumed: `validate_inner_binding` catches the role
    # violation BEFORE composition is even attempted, which is a stronger
    # guarantee than the feasibility refusal I first expected here. So
    # `feasibility_scenario_missing` is unreachable through the reduction,
    # and M5's conjunction can never be evaluated over one scenario.
    assert ei.value.code == "run_evidence_inner_mismatch:scenario"


def test_case2_a_feasibility_gate_error_is_translated_not_leaked(prepared,
                                                                monkeypatch):
    """`FeasibilityGateError` is a ValueError but NOT an `MCInputError`, so
    letting one escape the reduction would be the D-4 defect: a caller's
    refusal handling would not catch it and the code would be lost.

    The reduction translates it, preserving the code. Exercised by forcing
    the producer to raise, because the run-evidence binding makes the real
    path unreachable (see the test above)."""
    from itsf.mc import feasibility as real_fz
    assert not issubclass(real_fz.FeasibilityGateError, mcc.MCInputError)

    def _boom(*_a, **_k):
        raise real_fz.FeasibilityGateError("feasibility_scenario_missing",
                                          "forced")
    monkeypatch.setattr(real_fz, "combo_feasibility", _boom)
    base = CR._evidence(prepared)
    with pytest.raises(mcc.MCInputError) as ei:
        mcc._reduce_primary_from_base(base, prepared=prepared)
    assert ei.value.code == "feasibility_scenario_missing"


# ---------------------------------------------------------------------------
# CASE 3 — wrong identity
# ---------------------------------------------------------------------------

def test_case3_a_different_prepared_input_is_rejected(prepared):
    """The gates may not be evaluated over a different sealed input than the
    one the epistemic results came from. The second prepared input differs
    only in its records, which is enough to move `prepared_digest`."""
    other = _prepared(bundle=CR._bundle(pnl=90.0))
    assert mcc.prepared_digest(other) != mcc.prepared_digest(prepared)
    base = CR._evidence(prepared)                # internally consistent
    with pytest.raises(mcc.MCInputError) as ei:
        mcc._reduce_primary_from_base(base, prepared=other)
    assert ei.value.code == "provenance_mismatch"


def test_case3_a_wrong_day_universe_cannot_slip_past_the_digest(prepared):
    """WHY one identity check suffices for the day universe too.

    `prepared_digest` binds the complete day sequences per channel, so a
    prepared input carrying a different universe cannot carry a matching
    digest — and the reduction's digest check therefore rejects it. Proven
    by moving the universe on a copy and watching the digest move, rather
    than by reading the digest's docstring."""
    channel = mcc.PRIMARY_THETA_CHANNEL
    shifted = object.__new__(mcc.PreparedMCInput)
    for f in dataclasses.fields(prepared):
        object.__setattr__(shifted, f.name, getattr(prepared, f.name))
    universe = dict(prepared.day_sequences)
    universe[channel] = tuple(prepared.day_sequences[channel])[:-1]
    object.__setattr__(shifted, "day_sequences", universe)

    assert (shifted.day_sequences[channel]
            != prepared.day_sequences[channel])
    assert mcc.prepared_digest(shifted) != mcc.prepared_digest(prepared), (
        "prepared_digest must bind the day sequences, or a wrong universe "
        "could reach the frequency gate under a matching identity")

    base = CR._evidence(prepared)
    with pytest.raises(mcc.MCInputError) as ei:
        mcc._reduce_primary_from_base(base, prepared=shifted)
    assert ei.value.code == "provenance_mismatch"


def test_case3_a_non_prepared_object_is_rejected(prepared):
    base = CR._evidence(prepared)
    for bogus in ({"day_sequences": {}}, None, object()):
        with pytest.raises(mcc.MCInputError) as ei:
            mcc._reduce_primary_from_base(base, prepared=bogus)
        assert ei.value.code == "prepared_authority_missing"


# ---------------------------------------------------------------------------
# CASE 4 — no impersonation
# ---------------------------------------------------------------------------

def test_case4_the_reduction_takes_no_caller_feasibility_at_all(prepared):
    """THE structural point. The reduction has no `feasibility` parameter:
    it COMPOSES the evidence from the run's own observations, so there is no
    signature through which a caller could inject one. That is stronger than
    validating a supplied object."""
    params = set(inspect.signature(mcc._reduce_primary_from_base).parameters)
    assert params == {"base", "prepared"}
    assert "feasibility" not in params
    # nor does any public consumer entry accept one
    import types
    for name, fn in vars(mcc).items():
        if name.startswith("_") or not isinstance(fn, types.FunctionType):
            continue          # dataclasses carry their own fields; only
                              # FUNCTION entry points matter here
        if not getattr(fn, "__module__", "").endswith("consumer"):
            continue
        try:
            sig = inspect.signature(fn)
        except (TypeError, ValueError):
            continue
        if name == "epistemic_go_gate_input":
            continue          # the ONE typed seam, guarded below
        assert "feasibility" not in sig.parameters, name


def test_case4_a_bare_boolean_cannot_impersonate_the_evidence(prepared):
    """`True` carries no gate outcomes, no scenario set and no ruling id."""
    base = CR._evidence(prepared)
    cons, stress = base.results[sorted(base.results)[0]]
    for impostor in (True, 1, "feasible", {"feasible": True}):
        with pytest.raises(mcc.MCInputError) as ei:
            mcc.epistemic_go_gate_input(cons, stress, feasibility=impostor)
        assert ei.value.code == "feasibility_not_composed_evidence"


def test_case4_a_lookalike_object_is_refused_by_type(prepared):
    """Duck-typing is not enough: the gate requires the real
    `ComboFeasibility`, so a convenience object carrying the same field
    names has no path in."""
    @dataclasses.dataclass(frozen=True)
    class NotComboFeasibility:
        feasible: bool = True
        outcomes: tuple = ()
        scenarios: tuple = fz.GATE_SCENARIOS
        ruling: str = fz.FEASIBILITY_RULING

    base = CR._evidence(prepared)
    cons, stress = base.results[sorted(base.results)[0]]
    with pytest.raises(mcc.MCInputError) as ei:
        mcc.epistemic_go_gate_input(cons, stress,
                                    feasibility=NotComboFeasibility())
    assert ei.value.code == "feasibility_not_composed_evidence"


def test_case4_evidence_from_another_ruling_is_refused(prepared):
    """Stale evidence: a verdict must not be assembled from gates evaluated
    under a ruling this build does not carry."""
    base = CR._evidence(prepared)
    cons, stress = base.results[sorted(base.results)[0]]
    stale = fz.ComboFeasibility(feasible=True, outcomes=(),
                                scenarios=fz.GATE_SCENARIOS,
                                ruling="SOME_EARLIER_RULING")
    with pytest.raises(mcc.MCInputError) as ei:
        mcc.epistemic_go_gate_input(cons, stress, feasibility=stale)
    assert ei.value.code == "feasibility_ruling_mismatch"


def test_case4_the_frequency_gate_reads_dates_not_the_oracle_selection(
        prepared):
    """NO OUTCOME-DERIVED VALUE constructs the evidence. The frequency gate
    is fed `day_sequences` — the sealed day POPULATION — and never
    `traded_day_sets`, which is the ORACLE-SELECTED (TP) subset and would
    make a feasibility gate consume the oracle classification.

    Proven by measurement rather than by reading the source: the composed
    outcome matches the population and does NOT match what the TP subset
    would produce."""
    channel = mcc.PRIMARY_THETA_CHANNEL
    population = prepared.day_sequences[channel]
    tp_only = sorted(prepared.traded_day_sets[channel])
    assert len(tp_only) < len(population), (
        "fixture must have a strict TP subset for this test to discriminate")

    from_population = fz.frequency_gate(population)
    from_tp = fz.frequency_gate(tp_only)
    assert from_population.measured != from_tp.measured

    base = CR._evidence(prepared)
    cid = sorted(base.results)[0]
    cons, stress = base.results[cid]
    composed = fz.combo_feasibility(
        {cons.scenario: cons.observations,
         stress.scenario: stress.observations}, population)
    freq = [o for o in composed.outcomes if o.gate == "frequency"]
    assert len(freq) == 1
    assert freq[0].measured == from_population.measured
    assert freq[0].measured != from_tp.measured
    # and the reduction reads the same field the assertion above used.
    # The DOCSTRING is stripped first: it names `traded_day_sets` precisely
    # to explain why that set is not used, and a naive source scan would
    # match the explanation instead of the code.
    import ast
    tree = ast.parse(inspect.getsource(mcc._reduce_primary_from_base))
    fn = tree.body[0]
    if (fn.body and isinstance(fn.body[0], ast.Expr)
            and isinstance(fn.body[0].value, ast.Constant)):
        fn.body = fn.body[1:]
    code_only = ast.unparse(fn)
    assert "day_sequences[PRIMARY_THETA_CHANNEL]" in code_only
    assert "traded_day_sets" not in code_only


def test_case4_the_gate_methodology_is_untouched():
    """B-26 threaded existing evidence; it introduced no threshold and no
    decision rule. The three ruled constants are asserted by value so a
    later edit to them cannot pass as wiring."""
    assert fz.PAYOUT_WORLD_SHARE_P5_MIN == 0.50
    assert fz.FREQUENCY_ORACLE_DAYS_PER_MONTH_MIN == 5.0
    assert fz.SKIP_RATE_P95_MAX == 0.25
    assert fz.FEASIBILITY_RULING == (
        "ND2_ND3_RATIFIED_WITH_MODIFICATIONS_2026-08-24")
    assert fz.GATE_SCENARIOS == ("Conservative", "Stress")


# ---------------------------------------------------------------------------
# CASE 5 — end-to-end, pre-N13
# ---------------------------------------------------------------------------

def test_case5_the_convergence_report_is_now_reachable(prepared, monkeypatch):
    """END TO END, SYNTHETIC: reduction -> category -> rules (a)-(d) ->
    ConvergenceReport. This is what the B-26 dead end used to block; rules
    (a) and (b) both need a Checkpoint category, and no category was
    reachable.

    No MC is run and no N13 work happens: the runs are synthetic
    RunEvidence fixtures at B=2/M=2 and the K witness is the synthetic N11
    one."""
    import hashlib

    from itsf.mc import day_strata_supplement as ds
    from itsf.mc import grid_replay as gr
    from itsf.mc import supplement_authority as sa

    monkeypatch.setattr(mcc, "B_WORLDS_FROZEN", 2)

    seed_authority = sa.derive_supplement_authority_for_tests(
        prepared, supplement_id=ds.SUPPLEMENT_ID)
    days, binding = sa.supplement_build_inputs(seed_authority, prepared)
    rows = [{"trade_date": d, "year": int(str(d)[:4]),
             "vol_stratum": ds.VOL_STRATA[i % len(ds.VOL_STRATA)],
             "event_stratum": ds.EVENT_STRATA[i % len(ds.EVENT_STRATA)]}
            for i, d in enumerate(sorted(days))]
    supplement = ds.build_day_strata_supplement_test_only(
        rows, expected_day_set=days, binding=binding,
        supplement_id=ds.SUPPLEMENT_ID)
    authority = gr.derive_grid_replay_authority_for_tests(
        prepared, supplement, sealed_artifact_sha256=hashlib.sha256(
            ds.canonical_supplement_bytes(supplement)).hexdigest())
    grid = {key: gr.CellStatistics(conservative_p5={"c": 100.0},
                                   stress_median={"c": 50.0},
                                   feasible={"c": True})
            for key in gr.GRID_CELL_KEYS}
    witness = gr.derive_k_replay_evidence(authority, master_seed=7,
                                          cells_at_k=grid, cells_at_2k=grid)

    base = CR._evidence(prepared)
    doubled = {"B": CR._evidence(prepared, run_label="double_B", axis="B",
                                 B=4),
               "K": CR._evidence(prepared, run_label="double_K", axis="K",
                                 K=400)}
    report = mcc.convergence_from_evidence(
        base, doubled, CR._seed_runs(prepared), prepared=prepared,
        k_replay=witness)

    assert type(report) is mcc.ConvergenceReport
    for flag in (report.category_stable_under_doubling,
                 report.category_same_across_seeds,
                 report.quantile_drift_ok, report.mcse_ok):
        assert isinstance(flag, bool)
    assert set(report.drift_by_axis) == {"double_B", "double_K", "seed_7",
                                         "seed_13", "seed_31"}
    assert isinstance(report.converged, bool)


def test_case5_the_seal_path_is_no_longer_blocked_by_feasibility(prepared):
    """The seal still refuses a synthetic prepared input — deliberately, and
    that guard is not B-26's business. What matters is that the refusal is
    NOT a feasibility code any more, and that the reduction the seal calls
    now succeeds for the same prepared input."""
    base = CR._evidence(prepared)
    with pytest.raises(mcc.MCInputError) as ei:
        mcc.verdict_and_seal_from_evidence(
            prepared=prepared, base=base,
            doubled_by_axis={"B": CR._evidence(prepared,
                                               run_label="double_B",
                                               axis="B", B=4)},
            seed_runs=CR._seed_runs(prepared))
    assert ei.value.code == "seal_test_only_prepared_input"
    assert "feasibility" not in ei.value.code
    # the same reduction the seal calls, on the same prepared input, works
    assert mcc._reduce_primary_from_base(base, prepared=prepared)


def test_the_seal_path_still_cannot_complete_a_full_axes_convergence(
        prepared, monkeypatch):
    """WHAT B-26 DID NOT FIX, pinned so it is not rediscovered by accident.

    `verdict_and_seal_from_evidence` calls `convergence_from_evidence`
    WITHOUT a `k_replay` witness, and `DOUBLING_AXES` is {B, K}. So the
    seal path has two exits and no third:

      * a `doubled_by_axis` WITHOUT K  -> `doubling_axes_violation`
      * a `doubled_by_axis` WITH K but no witness
                                      -> `k_axis_evidence_blocked_grid_replay`

    Both are asserted below on the convergence entry the seal uses, plus
    the source fact that the seal supplies no witness. Threading one
    through means widening the seal signature, which
    `test_hand_built_verdict_inputs_have_no_callable_entry` deliberately
    pins at four inputs — so it is the N13 runner's call, not B-26's.
    """
    monkeypatch.setattr(mcc, "B_WORLDS_FROZEN", 2)
    base = CR._evidence(prepared)
    b_only = {"B": CR._evidence(prepared, run_label="double_B", axis="B",
                                B=4)}
    with pytest.raises(mcc.MCInputError) as ei:
        mcc.convergence_from_evidence(base, b_only, CR._seed_runs(prepared),
                                      prepared=prepared)
    assert ei.value.code == "doubling_axes_violation"

    with_k = dict(b_only,
                  K=CR._evidence(prepared, run_label="double_K", axis="K",
                                 K=400))
    with pytest.raises(mcc.MCInputError) as ei:
        mcc.convergence_from_evidence(base, with_k, CR._seed_runs(prepared),
                                      prepared=prepared)
    assert ei.value.code == "k_axis_evidence_blocked_grid_replay"

    # and the seal genuinely supplies no witness
    seal_src = inspect.getsource(mcc.verdict_and_seal_from_evidence)
    assert "convergence_from_evidence(" in seal_src
    assert "k_replay" not in seal_src

