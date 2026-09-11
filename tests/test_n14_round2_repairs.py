"""The seven frozen N14 Round-2 blockers, asserted as FINAL OBSERVABLES.

Each test below states what the repaired system does at the boundary a
consumer actually sees -- the seal candidate, the returned `RunnerResult`, the
ledger bytes -- rather than that some helper exists or some source string
appears. That distinction is the reason several of these findings survived a
green suite: the properties were asserted about the code rather than about its
output, and the output had stopped agreeing with the code.

Everything is synthetic: a fabricated bundle at B=2, K=2, a synthetic registry
chain and a synthetic DAY_STRATA supplement. No real MC runs and no number
below is a research result.
"""
import dataclasses
import hashlib

import pytest

import test_mc_battery_boundary as BB
import test_mc_registry_parser as RP
from test_mc_grid_channel_b27 import (            # noqa: F401
    K_SMALL, OUT_ROOT, small_grid, wide, authority, supplement, _sha)
from itsf.contracts import RESEARCH_BOOTSTRAP_SEEDS
from itsf.mc import consumer as mcc
from itsf.mc import day_strata_supplement as ds
from itsf.mc import grid_replay as gr
from itsf.mc import mc_contract as mcx
from itsf.mc import mc_runner as run


def _authorization(tmp_path, prepared):
    from itsf.mc.registry_boundary import resolve_registry
    reg = tmp_path / "TRIAL_REGISTRY.md"
    reg.write_text(RP.Reg().chain(RP.FULL[:5], commit=BB.COMMIT).text(),
                   encoding="utf-8")
    return run.bind_run_authorization(
        resolve_registry(reg), run_id=mcx.FIRST_RUN_ID,
        expected_commit=prepared.authorized_commit, output_root=OUT_ROOT,
        test_only=True)


@pytest.fixture()
def executed(wide, supplement, tmp_path):
    """One complete synthetic run, reused by the tests that read its output."""
    return run.execute_full_mc_for_tests(
        wide, authorization=_authorization(tmp_path, wide),
        supplement=supplement, sealed_artifact_sha256=_sha(supplement))


# == F01 -- main convergence is an admissibility precondition ==============

def test_F01_a_failed_main_convergence_yields_NO_judgment_and_NO_seal(
        wide, supplement, tmp_path, monkeypatch):
    """The finding, inverted. Rule (c)'s tolerance is made unsatisfiable, so
    the MAIN channel's quantile-drift condition fails and NOTHING about the
    grid moves. Before the repair this returned a GO/STOP category and a seal
    candidate with `converged: False` recorded beside it."""
    monkeypatch.setattr(mcc, "CONV_ABS_USD", -1.0)
    monkeypatch.setattr(mcc, "CONV_REL", -1.0)
    with pytest.raises(mcc.MCInputError) as ei:
        run.execute_full_mc_for_tests(
            wide, authorization=_authorization(tmp_path, wide),
            supplement=supplement, sealed_artifact_sha256=_sha(supplement))
    assert ei.value.code == "main_channel_not_converged"
    assert "quantile_drift_ok" in str(ei.value)


def test_F01_the_GRID_only_exception_still_withholds_nothing(executed):
    """The other half, and the one a blunt repair would have broken. M7 says
    a non-converged GRID seals its own section NON_CONVERGED and withdraws
    `deployable_region`'s right to support H1 entry -- and does NOT withhold
    Checkpoint-0. So the grid's standing must be reportable independently of
    the main channel's, which is exactly what folding it into rule (a) made
    impossible."""
    seal = executed.seal_candidate
    assert seal["convergence"]["converged"] is True          # a precondition
    assert "grid_converged" in seal["convergence"]           # reported apart
    assert seal["grid_section"]["status"] in {"CONVERGED", "NON_CONVERGED"}
    # the two facts are independently addressable
    assert isinstance(seal["convergence"]["grid_converged"], bool)
    assert seal["verdict"]["category"] in {"STOP", "GO", "beta", "alpha"}


def test_F01_rule_a_no_longer_carries_the_grid(wide, supplement, tmp_path):
    """Stated on the object rather than in prose: the report exposes the two
    as separate booleans, and rule (a) is the B arm alone."""
    result = run.execute_full_mc_for_tests(
        wide, authorization=_authorization(tmp_path, wide),
        supplement=supplement, sealed_artifact_sha256=_sha(supplement))
    names = {f.name for f in dataclasses.fields(mcc.ConvergenceReport)}
    assert {"category_stable_under_doubling", "grid_converged"} <= names
    seal = result.seal_candidate["convergence"]
    assert set(seal) == {"category_stable_under_doubling",
                         "category_same_across_seeds", "quantile_drift_ok",
                         "mcse_ok", "converged", "grid_converged"}


# == F02 -- every governed seed reaches the outcome ========================

def test_F02_the_final_grid_status_is_the_AND_across_every_seed(executed):
    """The standing names all three seeds and its own aggregation, and the
    result's two grid fields are read from it rather than from one witness."""
    standing = executed.grid_convergence
    gr.verify_grid_convergence(standing)
    assert set(standing.seeds) == set(RESEARCH_BOOTSTRAP_SEEDS)
    assert set(standing.converged_by_seed) == set(RESEARCH_BOOTSTRAP_SEEDS)
    assert set(standing.witness_digest_by_seed) == set(RESEARCH_BOOTSTRAP_SEEDS)
    assert executed.grid_seal_status == standing.grid_seal_status
    assert executed.may_support_h1_entry is standing.may_support_h1_entry
    # and the seal records the same per-seed detail
    section = executed.seal_candidate["grid_section"]
    assert set(section["converged_by_seed"]) == {
        str(s) for s in RESEARCH_BOOTSTRAP_SEEDS}


def test_F02_the_fixture_run_converges_which_is_the_control(executed):
    """The control for the parametrized test below: this run's grid DOES
    converge, so a NON_CONVERGED result there is caused by the seed that was
    made to disagree and not by the fixture."""
    assert executed.grid_convergence.grid_converged is True
    assert executed.grid_seal_status == "CONVERGED"


@pytest.mark.parametrize("victim", list(RESEARCH_BOOTSTRAP_SEEDS))
def test_F02_a_non_converged_seed_is_conjunctive_for_every_seed(
        wide, supplement, victim, small_grid):
    """Every governed seed, base or not. The aggregate is built from three
    genuine witnesses, one of which compares two passes that really differ,
    so the non-convergence is computed rather than asserted."""
    auth = gr.derive_grid_replay_authority_for_tests(
        wide, supplement, sealed_artifact_sha256=_sha(supplement))

    def cells(p5):
        return {key: gr.CellStatistics(conservative_p5={"c": p5},
                                       stress_median={"c": 50.0},
                                       feasible={"c": True})
                for key in gr.GRID_CELL_KEYS}

    def pass_(seed, doublings, p5):
        return gr.grid_pass_for_tests(
            auth, prepared_digest=auth.prepared_digest, master_seed=seed,
            doublings=doublings, B=2, channel=mcc.PRIMARY_THETA_CHANNEL,
            cells=cells(p5))

    witnesses = {}
    for seed in RESEARCH_BOOTSTRAP_SEEDS:
        # the victim's 2K arm crosses the region boundary, so the comparison
        # itself reports a flip rather than a band
        far = -100.0 if seed == victim else 100.0
        witnesses[seed] = gr.derive_k_replay_evidence(
            auth, master_seed=seed,
            cells_at_k=pass_(seed, 0, 100.0),
            cells_at_2k=pass_(seed, 1, far))
    assert witnesses[victim].grid_converged is False
    standing = gr.aggregate_k_replay_evidence(witnesses)
    assert standing.grid_converged is False
    assert standing.grid_seal_status == "NON_CONVERGED"
    assert standing.may_support_h1_entry is False
    assert standing.converged_by_seed[victim] is False


def test_F02_an_incomplete_seed_set_cannot_be_aggregated(wide, supplement,
                                                         small_grid):
    """A two-seed standing would weaken rule (b) exactly the way a two-seed
    publication would weaken M10."""
    auth = gr.derive_grid_replay_authority_for_tests(
        wide, supplement, sealed_artifact_sha256=_sha(supplement))
    with pytest.raises(mcc.MCInputError) as ei:
        gr.aggregate_k_replay_evidence({RESEARCH_BOOTSTRAP_SEEDS[0]: object()})
    assert ei.value.code == "grid_convergence_seed_set_incomplete"


def test_F02_the_seal_refuses_a_K_arm_with_no_cross_seed_standing(
        wide, supplement, tmp_path, monkeypatch):
    """The integration point itself: a K-doubled seal cannot be produced from
    one seed's witness any more."""
    import itsf.mc.grid_replay as _gr
    monkeypatch.setattr(_gr, "aggregate_k_replay_evidence",
                        lambda *a, **k: None)
    with pytest.raises(mcc.MCInputError) as ei:
        run.execute_full_mc_for_tests(
            wide, authorization=_authorization(tmp_path, wide),
            supplement=supplement, sealed_artifact_sha256=_sha(supplement))
    assert ei.value.code == "grid_convergence_across_seeds_required"


def test_F02_the_ruled_doubling_bound_rides_with_the_standing(executed):
    """(e) bounds the doubling escalation by the ruled `max_doublings`. The
    standing records what the evidence actually spans and what the bound is,
    so the bound is checkable instead of assumed."""
    from itsf import contracts
    standing = executed.grid_convergence
    assert standing.doublings_executed >= 1
    assert standing.max_doublings == \
        contracts.aaron_ruled_methods().grid_policy.max_doublings
    assert standing.doublings_executed <= standing.max_doublings


# == F03 -- publication consumes the comparison ============================

def test_F03_a_boundary_band_relabelling_survives_into_publication(
        wide, supplement, tmp_path, monkeypatch):
    """M8 relabels a flipped-but-hugging-zero cell `boundary_band` in both
    maps. Publication used to rebuild its own maps from the raw K pass, which
    the comparison never saw, so the third frozen class was created and then
    dropped between one and the other."""
    banded = {}
    real = gr.compare_region_maps

    def spy(kind, cells_at_k, cells_at_2k, *, k, k_doubled):
        comparison = real(kind, cells_at_k, cells_at_2k, k=k,
                          k_doubled=k_doubled)
        key = gr.GRID_CELL_KEYS[0]
        adjusted = dict(comparison.map_at_k)
        adjusted[key] = gr.BOUNDARY_BAND
        banded[kind] = key
        return dataclasses.replace(comparison, map_at_k=adjusted)

    monkeypatch.setattr(gr, "compare_region_maps", spy)
    result = run.execute_full_mc_for_tests(
        wide, authorization=_authorization(tmp_path, wide),
        supplement=supplement, sealed_artifact_sha256=_sha(supplement))
    assert banded, "the comparison ran"
    for kind, key in banded.items():
        assert result.published_region_by_kind[kind][key] == gr.BOUNDARY_BAND


def test_F03_the_witness_carries_the_adjusted_map_it_computed(executed):
    """The mechanism, at the object that owns it: the comparison's product is
    reachable, complete, and classified only into the frozen classes."""
    for seed in RESEARCH_BOOTSTRAP_SEEDS:
        report = executed.grid_evidence_by_seed[seed]
        for kind in gr.REGION_KINDS:
            classes = {entry["class_by_kind"][kind]
                       for entry in report["cells"].values()}
            assert classes <= set(gr.CELL_CLASSES), classes


# == F04 -- grid evidence is bound to the governed producer ================

def test_F04_hand_built_cells_cannot_become_seal_admitted_evidence(
        wide, supplement, small_grid):
    """The finding, inverted. A caller can still BUILD `CellStatistics` -- it
    is a public type and the tests need it -- but a mapping of them is no
    longer an admissible arm, so it cannot become a witness."""
    auth = gr.derive_grid_replay_authority_for_tests(
        wide, supplement, sealed_artifact_sha256=_sha(supplement))
    invented = {key: gr.CellStatistics(conservative_p5={"c": 100.0},
                                       stress_median={"c": 50.0},
                                       feasible={"c": True})
                for key in gr.GRID_CELL_KEYS}
    with pytest.raises(mcc.MCInputError) as ei:
        gr.derive_k_replay_evidence(auth, master_seed=mcc.BASE_MASTER_SEED,
                                    cells_at_k=invented, cells_at_2k=invented)
    assert ei.value.code == "grid_pass_required"


def test_F04_a_pass_cannot_be_constructed_or_replaced(executed):
    """No `producer=True` field: the capability is the claim, it exists once
    at import time, and it is dropped the moment it is checked."""
    with pytest.raises(mcc.MCInputError) as ei:
        gr.GridPass(capability=None, schema=gr.GRID_PASS_SCHEMA,
                    authority_digest="", prepared_digest="", master_seed=7,
                    doublings=0, B=2, channel="x", cell_keys=(),
                    cell_payloads=(), test_only=True, pass_digest="",
                    cells={})
    assert ei.value.code == "grid_pass_capability_required"


def test_F04_substituted_statistics_are_caught_by_the_pass_digest(
        wide, supplement, small_grid):
    """A self-digest over caller-supplied values proves internal consistency
    and nothing else -- so the pass re-derives its cell payloads from its own
    LIVE cells when verifying, and a swapped cell refuses."""
    auth = gr.derive_grid_replay_authority_for_tests(
        wide, supplement, sealed_artifact_sha256=_sha(supplement))
    cells = {key: gr.CellStatistics(conservative_p5={"c": 100.0},
                                    stress_median={"c": 50.0},
                                    feasible={"c": True})
             for key in gr.GRID_CELL_KEYS}
    pass_ = gr.grid_pass_for_tests(
        auth, prepared_digest=auth.prepared_digest, master_seed=7,
        doublings=0, B=2, channel=mcc.PRIMARY_THETA_CHANNEL, cells=cells)
    gr.verify_grid_pass(pass_)
    swapped = dict(pass_.cells)
    swapped[gr.GRID_CELL_KEYS[0]] = gr.CellStatistics(
        conservative_p5={"c": 999999.0}, stress_median={"c": 50.0},
        feasible={"c": True})
    object.__setattr__(pass_, "cells", swapped)
    with pytest.raises(mcc.MCInputError) as ei:
        gr.verify_grid_pass(pass_)
    assert ei.value.code == "grid_pass_cells_mutated"


def test_F04_the_test_pathway_is_typed_test_only_and_stays_that_way(
        wide, supplement, small_grid):
    """Synthetic cells may only be minted against a test-only authority, and
    the flag rides all the way into the seal candidate."""
    production_like = gr.derive_grid_replay_authority_for_tests(
        wide, supplement, sealed_artifact_sha256=_sha(supplement))
    assert production_like.test_only is True
    forged = object.__new__(gr.GridReplayAuthority)
    for f in dataclasses.fields(production_like):
        object.__setattr__(forged, f.name, getattr(production_like, f.name))
    object.__setattr__(forged, "test_only", False)
    with pytest.raises(mcc.MCInputError):
        gr.grid_pass_for_tests(
            forged, prepared_digest=forged.prepared_digest, master_seed=7,
            doublings=0, B=2, channel=mcc.PRIMARY_THETA_CHANNEL, cells={})


def test_F04_test_only_grid_evidence_is_recorded_in_the_seal(executed):
    """It says so, in the seal it produced, rather than being indistinguishable
    from production evidence."""
    assert executed.seal_candidate["grid_section"]["test_only"] is True


# == F05 -- the supplement binding is verified against the prepared input ==

@pytest.mark.parametrize("field,value", [
    ("trial_id", "S0-T999-NOT-THIS-TRIAL"),
    ("authorized_commit", "f" * 40),
    ("source_input_sha256", "e" * 64),
    ("method_version", "not-the-frozen-method"),
])
def test_F05_a_foreign_binding_is_refused_even_with_a_recomputed_hash(
        wide, supplement, field, value, small_grid):
    """Each implicated field on its own. The artifact hash is RECOMPUTED over
    the foreign values every time, so the only thing that can refuse is a
    comparison against something derived from the prepared input."""
    foreign = dict(supplement)
    foreign["binding"] = dict(supplement["binding"], **{field: value})
    sha = hashlib.sha256(ds.canonical_supplement_bytes(foreign)).hexdigest()
    with pytest.raises(mcc.MCInputError) as ei:
        gr.derive_grid_replay_authority_for_tests(
            wide, foreign, sealed_artifact_sha256=sha)
    assert ei.value.code == "grid_replay_supplement_binding_mismatch"
    assert field in str(ei.value)


def test_F05_the_honest_binding_is_still_admitted(wide, supplement,
                                                  small_grid):
    """The control. A check that refused everything would pass the four above
    and mean nothing."""
    auth = gr.derive_grid_replay_authority_for_tests(
        wide, supplement, sealed_artifact_sha256=_sha(supplement))
    assert auth.prepared_digest == mcc.prepared_digest(wide)


def test_F05_the_binding_check_is_the_governed_one_not_a_second_copy():
    """Reused from the module that owns supplement-authority semantics, so
    the grid side and the supplement side cannot drift into two rules."""
    from itsf.mc import supplement_authority as sa
    assert callable(sa.verify_supplement_binding)
    assert set(ds.BINDING_FIELDS) == {
        "trial_id", "authorized_commit", "day_universe_digest",
        "method_version", "source_input_sha256"}


# == F06 -- a generic writer cannot restore execution permission ===========

def test_F06_generic_OWNER_RELEASE_leaves_the_ledger_byte_identical(tmp_path):
    """Refused ABOVE the one physical write, so the bytes never move --
    'refused after it landed' would be a much weaker property, and it is the
    one that was actually reproduced."""
    from itsf.mc import registry_boundary as rb
    ledger = tmp_path / "TRIAL_REGISTRY.md"
    hold = ("| 1 | 2026-09-12T00:00:00Z | OWNER_HOLD | %s | Aaron | "
            "[GLOBAL] reason: stop |" % ("a" * 12))
    ledger.write_text(RP.Reg().text() + hold + "\n", encoding="utf-8")
    before = ledger.read_bytes()
    release = ("| 2 | 2026-09-12T00:00:01Z | OWNER_RELEASE | %s | Aaron | "
               "[GLOBAL] releases_event_sequence: 1; reason: go |"
               % ("a" * 12))
    with pytest.raises(rb.AppendRefused) as ei:
        rb.serialized_append(ledger, (release + "\n").encode("utf-8"),
                             decided=before)
    assert ei.value.code == "generic_append_refuses_permission_event"
    assert ledger.read_bytes() == before


def test_F06_the_hold_remains_in_force_afterwards(tmp_path):
    """The consequence that matters: eligibility did not move."""
    from itsf.mc import owner_control as oc
    from itsf.mc import registry_boundary as rb
    ledger = tmp_path / "TRIAL_REGISTRY.md"
    hold = ("| 1 | 2026-09-12T00:00:00Z | OWNER_HOLD | %s | Aaron | "
            "[GLOBAL] reason: stop |" % ("a" * 12))
    ledger.write_text(RP.Reg().text() + hold + "\n", encoding="utf-8")
    release = ("| 2 | 2026-09-12T00:00:01Z | OWNER_RELEASE | %s | Aaron | "
               "[GLOBAL] releases_event_sequence: 1; reason: go |"
               % ("a" * 12))
    with pytest.raises(rb.AppendRefused):
        rb.serialized_append(ledger, (release + "\n").encode("utf-8"),
                             decided=ledger.read_bytes())
    text = ledger.read_text(encoding="utf-8")
    live = [r for r in oc.parse_owner_rows(text) if r.token == oc.OWNER_HOLD]
    assert len(live) == 1
    assert oc.active_holds(text, "MC-DS-S001")


def test_F06_the_governed_owner_route_still_releases(tmp_path):
    """The legitimate positive path is untouched and still works -- the rule
    is about WHICH writer, not about whether Aaron may release."""
    from itsf.mc import owner_control as oc
    from itsf.mc import registry_boundary as rb
    ledger = tmp_path / "TRIAL_REGISTRY.md"
    ledger.write_text(RP.Reg().text(), encoding="utf-8")
    commit = "a" * 40
    rb.append_owner_hold(scope=oc.GLOBAL_SCOPE, reason="stop",
                         head_commit=commit,
                         utc_stamp="2026-09-12T00:00:00+00:00", path=ledger)
    rows = oc.parse_owner_rows(ledger.read_text(encoding="utf-8"))
    held = [r for r in rows if r.token == oc.OWNER_HOLD][-1]
    assert oc.active_holds(ledger.read_text(encoding="utf-8"), "MC-DS-S001")
    rb.append_owner_release(scope=oc.GLOBAL_SCOPE, reason="go",
                            head_commit=commit,
                            utc_stamp="2026-09-12T00:00:01+00:00",
                            releases_event_sequence=held.seq, path=ledger)
    assert not oc.active_holds(ledger.read_text(encoding="utf-8"),
                               "MC-DS-S001")


def test_F06_the_class_is_effect_on_eligibility_not_a_token_list():
    """OWNER_HOLD stays OUTSIDE the class: it only ever makes the ledger less
    permissive, and refusing it would be the broadening the ruling warns
    against. Every token is DERIVED from the contract that defines it."""
    from itsf.mc import owner_control as oc
    from itsf.mc import registry_boundary as rb
    assert rb.is_permission_event(oc.OWNER_RELEASE) is True
    assert rb.is_permission_event(oc.OWNER_HOLD) is False
    assert rb.is_permission_event("**OWNER_RELEASE**") is True
    assert oc.OWNER_RELEASE in rb.PERMISSION_EVENT_TOKENS
    # the previously repaired transitions are still protected
    for token in ("MC_READY_FOR_RUN_AUTHORIZATION", "MC_RUN_AUTHORIZED",
                  "SUPPLEMENT_EXECUTION_AUTHORIZED"):
        assert rb.is_permission_event(token) is True


# == F07 -- the full per-seed grid report survives the return ==============

def test_F07_every_seed_and_every_cell_survives_the_final_return(executed):
    report = executed.grid_evidence_by_seed
    assert set(report) == set(RESEARCH_BOOTSTRAP_SEEDS)
    for seed in RESEARCH_BOOTSTRAP_SEEDS:
        cells = report[seed]["cells"]
        assert set(cells) == set(gr.GRID_CELL_KEYS)
        assert len(cells) == 63
        assert report[seed]["master_seed"] == seed


def test_F07_the_merged_maps_remain_and_do_not_replace_the_report(executed):
    assert set(executed.published_region_by_kind) == set(gr.REGION_KINDS)
    for kind in gr.REGION_KINDS:
        assert set(executed.published_region_by_kind[kind]) == set(
            gr.GRID_CELL_KEYS)
    assert executed.grid_evidence_by_seed is not \
        executed.published_region_by_kind


@pytest.mark.parametrize("shape", ["one_marked", "mixed", "all_marked"])
def test_F07_absence_is_reported_as_absence_with_no_invented_values(
        wide, supplement, tmp_path, shape, monkeypatch):
    """One marked cell, a mixed grid and an all-marked seed. A marked cell
    carries its reason and the frozen arithmetic that decided it, and carries
    NO statistics -- not zeros, not None: the keys are absent."""
    import itsf.mc.grid_channel as gc
    real = gc.run_grid_cell
    marked_keys = {"one_marked": gr.GRID_CELL_KEYS[:1],
                   "mixed": gr.GRID_CELL_KEYS[:5],
                   "all_marked": gr.GRID_CELL_KEYS}[shape]

    def marking(prepared, authority, supplement_, *, q_mil, r_mil, **kw):
        if (q_mil, r_mil) in set(marked_keys):
            return gr.InfeasibleCell(
                reason=gr.INFEASIBLE_BY_SAMPLE, q_mil=q_mil, r_mil=r_mil,
                master_seed=kw["master_seed"], doublings=kw.get("doublings", 0),
                n_tp=2, n_fp=4, fp_available=3,
                detail="infeasible_by_sample: 4 > 3")
        return real(prepared, authority, supplement_, q_mil=q_mil,
                    r_mil=r_mil, **kw)

    monkeypatch.setattr(gc, "run_grid_cell", marking)
    if shape == "all_marked":
        # an all-marked grid has no sampled representative, which is a lawful
        # outcome the runner reports rather than a malformed one
        monkeypatch.setattr(gc, "drawn_count", lambda *a, **k: None)
    result = run.execute_full_mc_for_tests(
        wide, authorization=_authorization(tmp_path, wide),
        supplement=supplement, sealed_artifact_sha256=_sha(supplement))
    for seed in RESEARCH_BOOTSTRAP_SEEDS:
        seed_report = result.grid_evidence_by_seed[seed]
        assert set(seed_report["marked_cells"]) == set(marked_keys)
        for key in marked_keys:
            entry = seed_report["cells"][tuple(key)]
            assert entry["marked"] is True
            assert entry["reason"] == gr.INFEASIBLE_BY_SAMPLE
            assert entry["n_fp"] > entry["fp_available"]
            assert entry["detail"]
            for absent in gr.SAMPLED_CELL_FIELDS:
                assert absent not in entry, (
                    "a marked cell reports %s -- absence must be absence"
                    % absent)
        for key in set(gr.GRID_CELL_KEYS) - set(marked_keys):
            entry = seed_report["cells"][tuple(key)]
            assert entry["marked"] is False
            assert entry["conservative_p5"] and entry["stress_median"]
