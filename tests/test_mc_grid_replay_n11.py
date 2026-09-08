"""N11 — GRID/K replay wiring: GridReplayAuthority + KReplayEvidence.

The contract under test is the ratified N-D2 design (items M6-M10,
`RATIFIED_UNCHANGED` 2026-08-24) over the frozen MC SS5 convergence rules and
STUDY_0_PREREGISTRATION Appendix A v0.6. Every fixture here is SYNTHETIC:
nothing reads market data, the sealed S004 artifact, or the registry.

Two things this file deliberately proves as much as it proves acceptance:

  * that the pre-N11 block was REPLACED by a binding rather than removed —
    a K entry with no witness still refuses, with the same code it always
    did, because the reason ("no actual K-doubled evidence can exist") is
    what changed, not the prohibition on impersonation;
  * that the one case M8's text does not settle REFUSES instead of picking
    a reading (`grid_replay_boundary_band_multi_combo_unruled`).
"""
import dataclasses

import pytest

import test_mc_cold_replay as CR
from itsf.contracts import RESEARCH_BOOTSTRAP_SEEDS
from itsf.mc import consumer as mcc
from itsf.mc import day_strata_supplement as ds
from itsf.mc import grid_replay as gr
from itsf.mc import supplement_authority as sa


# ---------------------------------------------------------------------------
# synthetic fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def prepared():
    b = CR._bundle()
    return mcc.prepare_mc_input_for_tests(
        b, authorization_snapshot={"trial_id": CR.TRIAL,
                                   "authorized_commit": CR.COMMIT},
        custody_authority=mcc.CustodyAuthority.for_tests(b),
        test_only_calendar=CR._calendar())


def _day_rows(days):
    """One structural row per day, cycling the FROZEN stratum vocabularies."""
    rows = []
    for i, date in enumerate(sorted(days)):
        rows.append({"trade_date": date,
                     "year": int(str(date)[:4]),
                     "vol_stratum": ds.VOL_STRATA[i % len(ds.VOL_STRATA)],
                     "event_stratum": ds.EVENT_STRATA[i % len(ds.EVENT_STRATA)]})
    return rows


@pytest.fixture()
def supplement(prepared):
    authority = sa.derive_supplement_authority_for_tests(
        prepared, supplement_id=ds.SUPPLEMENT_ID)
    expected_days, binding = sa.supplement_build_inputs(authority, prepared)
    return ds.build_day_strata_supplement_test_only(
        _day_rows(expected_days), expected_day_set=expected_days,
        binding=binding, supplement_id=ds.SUPPLEMENT_ID)


def _sealed_sha(supplement):
    import hashlib
    return hashlib.sha256(
        ds.canonical_supplement_bytes(supplement)).hexdigest()


@pytest.fixture()
def authority(prepared, supplement):
    return gr.derive_grid_replay_authority_for_tests(
        prepared, supplement, sealed_artifact_sha256=_sealed_sha(supplement))


def _cell(p5, median, feasible=True, identity=None, combo="lucid|E1|P2"):
    return gr.CellStatistics(
        conservative_p5={combo: p5}, stress_median={combo: median},
        feasible={combo: feasible},
        identity=dict(identity or {"n_tp": 10, "n_fp": 5}))


def _grid(p5=100.0, median=50.0, **kw):
    """A full 63-cell Appendix-A grid, every cell identical."""
    return {key: _cell(p5, median, **kw) for key in gr.GRID_CELL_KEYS}


# ---------------------------------------------------------------------------
# GridReplayAuthority — what makes a sealed supplement sufficient
# ---------------------------------------------------------------------------

def test_a_sealed_supplement_covering_the_frozen_day_universe_licenses_replay(
        authority, prepared):
    """The positive path: this is the authority the R2 PHASE D audit named
    MISSING (`MISSING_AUTHORITY=EXACT_PER_DAY_DAY_STRATA`)."""
    gr.verify_grid_replay_authority(authority)
    assert authority.schema == gr.GRID_REPLAY_AUTHORITY_SCHEMA
    assert authority.stratum_axes == ("year", "vol_stratum", "event_stratum")
    assert authority.k_per_seed == mcc.K_PER_SEED_FROZEN
    assert authority.prepared_digest == mcc.prepared_digest(prepared)
    assert authority.test_only is True          # synthetic stays visible
    assert len(authority.sealed_artifact_sha256) == 64


def test_the_authority_is_factory_only(authority):
    """A hand-built certificate has no callable path — the same capability
    pattern `BatteryReceipt` and `SupplementAuthority` already use."""
    with pytest.raises(mcc.MCInputError) as ei:
        gr.GridReplayAuthority(
            capability=None, schema=gr.GRID_REPLAY_AUTHORITY_SCHEMA,
            supplement_id="MC-DS-S001", supplement_schema="x",
            sealed_artifact_sha256="0" * 64, rows_digest="0" * 64,
            day_universe_digest="0" * 64, n_days=1, stratum_axes=(),
            grid_stream_tag=1, k_per_seed=200, prepared_digest="0" * 64,
            test_only=True, authority_digest="0" * 64)
    assert ei.value.code == "grid_replay_authority_capability_required"
    # replace() is a constructor call and dies at the same gate
    with pytest.raises(mcc.MCInputError) as ei:
        dataclasses.replace(authority, n_days=2)
    assert ei.value.code == "grid_replay_authority_capability_required"


def test_a_mutated_authority_fails_its_own_digest(authority):
    forged = object.__new__(gr.GridReplayAuthority)
    for f in dataclasses.fields(authority):
        object.__setattr__(forged, f.name, getattr(authority, f.name))
    object.__setattr__(forged, "n_days", authority.n_days + 1)
    with pytest.raises(mcc.MCInputError) as ei:
        gr.verify_grid_replay_authority(forged)
    assert ei.value.code == "grid_replay_authority_digest_mismatch"


def test_pinning_one_artifact_and_handing_over_another_refuses(
        prepared, supplement):
    """The sealed sha is re-derived from the canonical bytes, so a caller
    cannot pin the sealed artifact and mint from a different table."""
    with pytest.raises(mcc.MCInputError) as ei:
        gr.derive_grid_replay_authority_for_tests(
            prepared, supplement, sealed_artifact_sha256="f" * 64)
    assert ei.value.code == "grid_replay_sealed_artifact_sha256_mismatch"


def test_a_supplement_missing_one_day_is_not_an_authority(prepared,
                                                          supplement):
    """THE audit's actual finding: stratified sampling needs the WHOLE pool
    assigned. A subset looks like a table and is not an authority."""
    short = dict(supplement)
    short["rows"] = list(supplement["rows"])[:-1]
    with pytest.raises(mcc.MCInputError) as ei:
        gr.derive_grid_replay_authority_for_tests(
            prepared, short, sealed_artifact_sha256=_sealed_sha(short))
    assert ei.value.code == "grid_replay_supplement_day_universe_incomplete"


def test_a_duplicated_day_refuses_with_its_own_code(prepared, supplement):
    dupe = dict(supplement)
    rows = list(supplement["rows"])
    dupe["rows"] = rows + [dict(rows[0])]
    with pytest.raises(mcc.MCInputError) as ei:
        gr.derive_grid_replay_authority_for_tests(
            prepared, dupe, sealed_artifact_sha256=_sealed_sha(dupe))
    assert ei.value.code == "grid_replay_supplement_duplicate_day"


def test_an_off_vocabulary_stratum_refuses(prepared, supplement):
    """DR-2 / DR-6 vocabularies are frozen; the authority re-validates them
    rather than inheriting the builder's earlier verdict."""
    bad = dict(supplement)
    rows = [dict(r) for r in supplement["rows"]]
    rows[0]["vol_stratum"] = "T9"
    bad["rows"] = rows
    with pytest.raises(mcc.MCInputError) as ei:
        gr.derive_grid_replay_authority_for_tests(
            prepared, bad, sealed_artifact_sha256=_sealed_sha(bad))
    assert ei.value.code == "grid_replay_supplement_vol_stratum_violation"


def test_a_wrong_day_universe_digest_refuses(prepared, supplement):
    """GRID identity: the supplement's own binding must name the same day
    universe the prepared input independently re-derives."""
    bad = dict(supplement)
    bad["binding"] = dict(supplement["binding"], day_universe_digest="0" * 64)
    with pytest.raises(mcc.MCInputError) as ei:
        gr.derive_grid_replay_authority_for_tests(
            prepared, bad, sealed_artifact_sha256=_sealed_sha(bad))
    assert ei.value.code == (
        "grid_replay_supplement_day_universe_digest_mismatch")


def test_a_non_canonical_supplement_id_refuses(prepared, supplement):
    bad = dict(supplement, supplement_id="GRID-1")
    bad["binding"] = dict(supplement["binding"])
    with pytest.raises(mcc.MCInputError) as ei:
        gr.derive_grid_replay_authority_for_tests(
            prepared, bad, sealed_artifact_sha256=_sealed_sha(bad))
    assert ei.value.code == "grid_replay_supplement_id_not_canonical"


def test_a_hand_built_prepared_input_cannot_mint_an_authority(supplement):
    with pytest.raises(mcc.MCInputError) as ei:
        gr.derive_grid_replay_authority_for_tests(
            {"not": "prepared"}, supplement, sealed_artifact_sha256="0" * 64)
    assert ei.value.code == "grid_replay_prepared_input_required"


def test_a_test_only_prepared_cannot_mint_a_production_authority(
        prepared, supplement):
    with pytest.raises(mcc.MCInputError) as ei:
        gr.derive_grid_replay_authority(
            prepared, supplement,
            sealed_artifact_sha256=_sealed_sha(supplement))
    assert ei.value.code == "grid_replay_authority_test_only_prepared"


def test_the_authority_digest_is_deterministic(prepared, supplement):
    a = gr.derive_grid_replay_authority_for_tests(
        prepared, supplement, sealed_artifact_sha256=_sealed_sha(supplement))
    b = gr.derive_grid_replay_authority_for_tests(
        prepared, supplement, sealed_artifact_sha256=_sealed_sha(supplement))
    assert a.authority_digest == b.authority_digest


# ---------------------------------------------------------------------------
# the two FROZEN region definitions (prereg Appendix A v0.6, L289-292)
# ---------------------------------------------------------------------------

def test_positive_ev_region_is_the_frozen_existential_over_combos():
    cell = gr.CellStatistics(
        conservative_p5={"a": -10.0, "b": 1.0},
        stress_median={"a": 0.0, "b": -500.0},
        feasible={"a": True, "b": True})
    # SOME combo has Conservative P5 > 0 -> in, regardless of Stress
    assert gr.cell_category(cell, gr.POSITIVE_EV_REGION) == gr.IN_REGION
    # ... and deployable needs the SAME combo to clear Stress too, which
    # neither does here (a fails P5, b fails the median)
    assert gr.cell_category(cell, gr.DEPLOYABLE_REGION) == gr.OUT_OF_REGION


def test_deployable_requires_the_same_combination_not_a_stitched_pair():
    """The prereg says "the SAME combination" — the anti-cherry-pick rule.
    Stitching combo a's P5 to combo b's median would make this cell IN."""
    cell = gr.CellStatistics(
        conservative_p5={"a": 5.0, "b": -5.0},
        stress_median={"a": -5.0, "b": 5.0},
        feasible={"a": True, "b": True})
    assert gr.cell_category(cell, gr.DEPLOYABLE_REGION) == gr.OUT_OF_REGION


def test_the_stress_median_boundary_is_inclusive_as_frozen():
    """`Stress median >= 0`, not > 0. The asymmetry with P5 is the
    prereg's, so it is pinned rather than tidied."""
    cell = _cell(1.0, 0.0)
    assert gr.cell_category(cell, gr.DEPLOYABLE_REGION) == gr.IN_REGION


def test_a_pending_feasibility_refuses_instead_of_guessing():
    """`qualifying_distribution_vs_payout_requirements` is still
    DECISION_REQUIRED. A combo that meets the EV evidence but has no
    feasibility verdict might be the existential witness, so answering
    either way would invent a verdict the gate has not issued."""
    cell = _cell(10.0, 10.0, feasible=None)
    with pytest.raises(mcc.MCInputError) as ei:
        gr.cell_category(cell, gr.DEPLOYABLE_REGION)
    assert ei.value.code == "deployable_region_feasibility_pending"
    # ... but a PENDING combo that fails the EV evidence cannot be the
    # witness, so it does not block the cell.
    ok = gr.CellStatistics(conservative_p5={"a": -1.0}, stress_median={"a": 0.0},
                           feasible={"a": None})
    assert gr.cell_category(ok, gr.DEPLOYABLE_REGION) == gr.OUT_OF_REGION


def test_a_partial_grid_is_not_a_region_map():
    cells = dict(_grid())
    cells.pop(gr.GRID_CELL_KEYS[0])
    with pytest.raises(mcc.MCInputError) as ei:
        gr.region_map(cells, gr.POSITIVE_EV_REGION)
    assert ei.value.code == "grid_replay_grid_incomplete"


def test_the_grid_is_the_frozen_appendix_a_grid():
    """Taken from `s0.gridmix`, not re-spelled here."""
    from itsf.s0 import gridmix
    assert len(gr.GRID_CELL_KEYS) == (len(gridmix.Q_GRID_MILLIS)
                                      * len(gridmix.R_GRID_MILLIS)) == 63


# ---------------------------------------------------------------------------
# M8 — equality with a boundary band
# ---------------------------------------------------------------------------

def test_identical_passes_converge(authority):
    ev = gr.derive_k_replay_evidence(
        authority, master_seed=7, cells_at_k=_grid(), cells_at_2k=_grid())
    assert ev.grid_converged is True
    assert ev.grid_seal_status == "CONVERGED"
    assert ev.may_support_h1_entry is True


def test_a_cell_hugging_zero_is_exempted_as_a_boundary_band_cell(authority):
    """M8: |value| <= max($25, 5%) at BOTH K and 2K and a drift within the
    same tolerance. Exact equality was rejected as non-terminating."""
    at_k, at_2k = _grid(), _grid()
    key = gr.GRID_CELL_KEYS[0]
    at_k[key] = _cell(3.0, 3.0)      # in region
    at_2k[key] = _cell(-2.0, -2.0)   # out of region: a flip, but hugging 0
    comparison = gr.compare_region_maps(
        gr.POSITIVE_EV_REGION, at_k, at_2k, k=200, k_doubled=400)
    assert comparison.converged is True
    assert comparison.boundary_band_cells == (key,)
    assert comparison.map_at_k[key] == gr.BOUNDARY_BAND
    assert comparison.map_at_2k[key] == gr.BOUNDARY_BAND


def test_a_decisive_flip_is_not_converged(authority):
    """Far from zero on both sides: a real instability, not MC noise.

    Note WHICH rule catches it. With one combination per cell, a class flip
    that survived (c) is arithmetically impossible outside the band: a flip
    means |v_k| + |v_2k| = |drift|, so surviving drift <= max($25, 5%)
    forces both values under $25, which is the band condition itself. So
    (c) is the binding constraint here and `flipped_cells` stays empty —
    the same "not converged, double K" consequence under (e), reached by
    the rule that actually fires."""
    at_k, at_2k = _grid(), _grid()
    key = gr.GRID_CELL_KEYS[0]
    at_k[key] = _cell(5000.0, 5000.0)
    at_2k[key] = _cell(-5000.0, -5000.0)
    comparison = gr.compare_region_maps(
        gr.POSITIVE_EV_REGION, at_k, at_2k, k=200, k_doubled=400)
    assert comparison.converged is False
    assert (key, "conservative_p5[lucid|E1|P2]") in comparison.drift_violations
    ev = gr.derive_k_replay_evidence(
        authority, master_seed=7, cells_at_k=at_k, cells_at_2k=at_2k)
    assert ev.grid_converged is False
    assert ev.grid_seal_status == "NON_CONVERGED"
    # M7: a non-converged grid withdraws deployable_region's H1 standing
    assert ev.may_support_h1_entry is False


def _mixed_cell(p5_a, p5_b, med_a=None, med_b=None):
    """A two-combination cell. `a` is the far/irrelevant one, `b` the one
    that can decide the existential."""
    return gr.CellStatistics(
        conservative_p5={"a": p5_a, "b": p5_b},
        stress_median={"a": p5_a if med_a is None else med_a,
                       "b": p5_b if med_b is None else med_b},
        feasible={"a": True, "b": True})


def test_b25_case1_a_non_decisive_combination_does_not_veto():
    """CASE 1 — AARON'S B-25 RULING, (ii), AND THE TEST THAT DISTINGUISHES
    IT FROM (i).

    Combo `a` is stably far negative (−$5000): it satisfies the region in
    NEITHER pass, so it never contributed to membership. Combo `b` is the
    existentially relevant candidate and moves +$3 → −$2, inside the frozen
    band. The cell's class flips because of `b` alone.

    Interpretation (i) — "every combination must sit in the band" — would
    see `a` at −$5000 outside the band and refuse the exemption, making the
    cell NOT converged and forcing a K doubling. Interpretation (ii), which
    Aaron ruled, is governed by `b`: the cell is boundary and converges.

    The assertion below is therefore a genuine discriminator: it FAILS under
    (i) and passes only under (ii).
    """
    at_k, at_2k = _grid(), _grid()
    key = gr.GRID_CELL_KEYS[0]
    at_k[key] = _mixed_cell(-5000.0, 3.0)
    at_2k[key] = _mixed_cell(-5000.0, -2.0)

    # the premises the ruling turns on, asserted rather than assumed
    assert gr.satisfying_combos(at_k[key], gr.POSITIVE_EV_REGION) == {"b"}
    assert gr.satisfying_combos(at_2k[key], gr.POSITIVE_EV_REGION) == set()
    assert gr.cell_category(at_k[key], gr.POSITIVE_EV_REGION) == gr.IN_REGION
    assert gr.cell_category(at_2k[key], gr.POSITIVE_EV_REGION) == gr.OUT_OF_REGION
    # `a` is outside the band at both passes — under (i) this is the veto
    assert not gr._in_band(-5000.0, -5000.0)

    comparison = gr.compare_region_maps(
        gr.POSITIVE_EV_REGION, at_k, at_2k, k=200, k_doubled=400)
    assert comparison.boundary_band_cells == (key,)
    assert comparison.flipped_cells == ()
    assert comparison.converged is True
    assert comparison.map_at_k[key] == gr.BOUNDARY_BAND


def test_b25_case2_a_stable_decisive_combination_is_not_relabelled():
    """CASE 2 — the decisive combination is clearly away from the boundary
    and its classification is stable, so the cell keeps its class. An
    irrelevant combination differing in magnitude does not drag it into the
    band."""
    at_k, at_2k = _grid(), _grid()
    key = gr.GRID_CELL_KEYS[0]
    #  b decides and is far positive at both passes; a differs in magnitude
    at_k[key] = _mixed_cell(-5000.0, 4000.0)
    at_2k[key] = _mixed_cell(-1.0, 4000.0)
    assert gr.satisfying_combos(at_k[key], gr.POSITIVE_EV_REGION) == {"b"}
    assert gr.satisfying_combos(at_2k[key], gr.POSITIVE_EV_REGION) == {"b"}

    comparison = gr.compare_region_maps(
        gr.POSITIVE_EV_REGION, at_k, at_2k, k=200, k_doubled=400)
    assert comparison.boundary_band_cells == ()      # NOT relabelled
    assert comparison.map_at_k[key] == gr.IN_REGION
    assert comparison.map_at_2k[key] == gr.IN_REGION
    # `a` moved -5000 -> -1, far beyond max($25, 5%): rule (c) still reports
    # it, because (c) governs drift per statistic and is untouched by B-25.
    assert (key, "conservative_p5[a]") in comparison.drift_violations


def test_b25_case3_a_decisive_combination_inside_the_band_keeps_m8():
    """CASE 3 — the decisive combination crosses within the frozen band:
    the already-ratified M8 behaviour applies unchanged, including the
    relabelling of BOTH maps to the third class and the re-comparison."""
    at_k, at_2k = _grid(), _grid()
    key = gr.GRID_CELL_KEYS[0]
    at_k[key] = _cell(5.0, 5.0)         # single combination, in region
    at_2k[key] = _cell(-4.0, -4.0)      # crosses, hugging zero
    comparison = gr.compare_region_maps(
        gr.POSITIVE_EV_REGION, at_k, at_2k, k=200, k_doubled=400)
    assert comparison.boundary_band_cells == (key,)
    assert comparison.map_at_k[key] == gr.BOUNDARY_BAND
    assert comparison.map_at_2k[key] == gr.BOUNDARY_BAND
    assert comparison.converged is True
    # and a decisive combination OUTSIDE the band is still not exempt
    at_2k[key] = _cell(-4000.0, -4000.0)
    hard = gr.compare_region_maps(
        gr.POSITIVE_EV_REGION, at_k, at_2k, k=200, k_doubled=400)
    assert hard.boundary_band_cells == ()
    assert hard.converged is False


def test_b25_case4_the_ruling_introduced_no_new_tolerance():
    """CASE 4 — the ruling narrowed WHICH combinations are consulted. It
    did not add an epsilon, threshold, percentage or second tolerance.

    Asserted mechanically rather than by reading: the band predicate and
    the comparison carry no numeric literal of their own, and the module's
    single tolerance is still (c)'s frozen pair, taken from `consumer`
    rather than re-spelled."""
    import ast
    import inspect

    for fn in (gr._in_band, gr.compare_region_maps):
        # both are module-level, so the source is already at column 0
        tree = ast.parse(inspect.getsource(fn))
        numbers = [n.value for n in ast.walk(tree)
                   if isinstance(n, ast.Constant)
                   and isinstance(n.value, (int, float))
                   and not isinstance(n.value, bool)]
        # only the doubling arithmetic `2 * k` may carry a literal
        assert set(numbers) <= {2}, (fn.__name__, numbers)

    assert gr.frozen_tolerance(0.0) == mcc.CONV_ABS_USD
    assert gr.frozen_tolerance(10_000.0) == mcc.CONV_REL * 10_000.0
    src = inspect.getsource(gr.frozen_tolerance)
    assert "_mcc.CONV_ABS_USD" in src and "_mcc.CONV_REL" in src, (
        "the tolerance must stay the frozen pair, not a local copy")
    # and no second tolerance-shaped constant entered the module
    module_numbers = {
        name: value for name, value in vars(gr).items()
        if isinstance(value, float) and not name.startswith("__")}
    assert module_numbers == {}, module_numbers


def _two_combo_grid(pa, pb):
    """A full grid whose every cell carries combination A at `pa` and B at
    `pb` — both the Conservative P5 and the Stress median."""
    return {key: gr.CellStatistics(conservative_p5={"A": pa, "B": pb},
                                   stress_median={"A": pa, "B": pb},
                                   feasible={"A": True, "B": True})
            for key in gr.GRID_CELL_KEYS}


def test_b25_caseA_witness_substitution_is_not_an_existential_crossing():
    """CASE A — THE DISCRIMINATOR FOR THE ACCEPTANCE CHECK.

    `satisfying(K) = {A}`, `satisfying(2K) = {B}`: the satisfying SET
    changed completely, and its symmetric difference is `{A, B}` — yet the
    cell is IN at both passes, because the existential only asks whether
    the set is non-empty. B-25 governs the CELL-LEVEL EXISTENTIAL REGION
    DECISION, so this is witness substitution, NOT a boundary crossing, and
    M8 must not fire.

    This distinguishes "the satisfying set changed" from "membership
    changed". An implementation that keyed M8 off a non-empty symmetric
    difference would relabel this cell; this one compares CLASSES first and
    never reaches the deciding-set computation.

    The instability is not waved through — it is simply not M8's business.
    Rule (c) sees both combinations move by $200 and reports the cell as
    non-converged on its own, which is asserted below so this test cannot
    be mistaken for "witness substitution is harmless".
    """
    at_k = _two_combo_grid(100.0, -100.0)      # A supports
    at_2k = _two_combo_grid(-100.0, 100.0)     # B supports
    key = gr.GRID_CELL_KEYS[0]
    kind = gr.POSITIVE_EV_REGION

    sat_k = gr.satisfying_combos(at_k[key], kind)
    sat_2k = gr.satisfying_combos(at_2k[key], kind)
    assert set(sat_k) == {"A"} and set(sat_2k) == {"B"}
    assert set(sat_k ^ sat_2k) == {"A", "B"}           # non-empty XOR
    assert gr.cell_category(at_k[key], kind) == gr.IN_REGION
    assert gr.cell_category(at_2k[key], kind) == gr.IN_REGION

    comparison = gr.compare_region_maps(kind, at_k, at_2k, k=200,
                                        k_doubled=400)
    # M8 did NOT fire, despite the fully-changed satisfying set
    assert comparison.boundary_band_cells == ()
    assert comparison.flipped_cells == ()
    assert comparison.map_at_k[key] == gr.IN_REGION
    assert comparison.map_at_2k[key] == gr.IN_REGION
    # ... and the existing convergence checks are still active
    assert (key, "conservative_p5[A]") in comparison.drift_violations
    assert (key, "conservative_p5[B]") in comparison.drift_violations
    assert comparison.converged is False


def test_b25_caseB_a_true_existential_crossing_uses_the_responsible_combo():
    """CASE B — `satisfying(K) = {B}`, `satisfying(2K) = {}`: membership
    genuinely changes IN -> OUT, so M8 applies, and it applies to the
    combination responsible for the transition.

    Proven by varying only that combination: when B's transition sits in
    the frozen band the cell is exempt, and when it does not the cell is
    a real flip. A's statistics are identical in both runs, so the
    difference can only come from B."""
    kind = gr.POSITIVE_EV_REGION
    key = gr.GRID_CELL_KEYS[0]

    at_k = _two_combo_grid(-5000.0, 3.0)       # B supports; A far negative
    in_band = _two_combo_grid(-5000.0, -2.0)   # B crosses inside the band
    assert set(gr.satisfying_combos(at_k[key], kind)) == {"B"}
    assert set(gr.satisfying_combos(in_band[key], kind)) == set()
    assert gr.cell_category(at_k[key], kind) == gr.IN_REGION
    assert gr.cell_category(in_band[key], kind) == gr.OUT_OF_REGION

    exempt = gr.compare_region_maps(kind, at_k, in_band, k=200, k_doubled=400)
    assert exempt.boundary_band_cells == tuple(gr.GRID_CELL_KEYS)
    assert exempt.flipped_cells == ()

    out_of_band = _two_combo_grid(-5000.0, -4000.0)   # B crosses decisively
    hard = gr.compare_region_maps(kind, at_k, out_of_band, k=200,
                                  k_doubled=400)
    assert hard.boundary_band_cells == ()
    assert key in hard.flipped_cells
    assert hard.converged is False


def test_b25_caseC_stable_membership_and_stable_support():
    """CASE C — `{A}` at both passes, IN -> IN: nothing crossed, so no
    boundary treatment and no flip."""
    kind = gr.POSITIVE_EV_REGION
    key = gr.GRID_CELL_KEYS[0]
    at_k = _two_combo_grid(100.0, -100.0)
    at_2k = _two_combo_grid(105.0, -100.0)    # A still supports, small move
    assert set(gr.satisfying_combos(at_k[key], kind)) == {"A"}
    assert set(gr.satisfying_combos(at_2k[key], kind)) == {"A"}

    comparison = gr.compare_region_maps(kind, at_k, at_2k, k=200,
                                        k_doubled=400)
    assert comparison.boundary_band_cells == ()
    assert comparison.flipped_cells == ()
    assert comparison.map_at_k[key] == gr.IN_REGION
    assert comparison.drift_violations == ()      # $5 is inside max($25, 5%)
    assert comparison.converged is True


def test_b25_caseD_out_to_out_with_combination_movement():
    """CASE D — both satisfying sets empty, statistics still moving. The
    cell is OUT at both passes, so no existential crossing and no M8; the
    frozen drift rule still reports the movement."""
    kind = gr.POSITIVE_EV_REGION
    key = gr.GRID_CELL_KEYS[0]
    at_k = _two_combo_grid(-100.0, -200.0)
    at_2k = _two_combo_grid(-5000.0, -6000.0)
    assert set(gr.satisfying_combos(at_k[key], kind)) == set()
    assert set(gr.satisfying_combos(at_2k[key], kind)) == set()
    assert gr.cell_category(at_k[key], kind) == gr.OUT_OF_REGION
    assert gr.cell_category(at_2k[key], kind) == gr.OUT_OF_REGION

    comparison = gr.compare_region_maps(kind, at_k, at_2k, k=200,
                                        k_doubled=400)
    assert comparison.boundary_band_cells == ()
    assert comparison.flipped_cells == ()
    assert (key, "conservative_p5[A]") in comparison.drift_violations
    assert comparison.converged is False


def test_b25_membership_not_witness_identity_gates_m8():
    """The rule itself, stated as one mechanical assertion over both
    directions: M8 is reached IFF the cell-level class changed — never
    because the supporting combination was substituted."""
    kind = gr.POSITIVE_EV_REGION
    key = gr.GRID_CELL_KEYS[0]
    cases = {
        "substitution {A}->{B}, IN->IN": (_two_combo_grid(100.0, -100.0),
                                          _two_combo_grid(-100.0, 100.0)),
        "stable {A}->{A}, IN->IN": (_two_combo_grid(100.0, -100.0),
                                    _two_combo_grid(105.0, -100.0)),
        "empty {}->{}, OUT->OUT": (_two_combo_grid(-100.0, -200.0),
                                   _two_combo_grid(-5000.0, -6000.0)),
        "crossing {B}->{}, IN->OUT": (_two_combo_grid(-5000.0, 3.0),
                                      _two_combo_grid(-5000.0, -2.0)),
    }
    for label, (at_k, at_2k) in cases.items():
        class_changed = (gr.cell_category(at_k[key], kind)
                         != gr.cell_category(at_2k[key], kind))
        comparison = gr.compare_region_maps(kind, at_k, at_2k, k=200,
                                            k_doubled=400)
        m8_fired = bool(comparison.boundary_band_cells
                        or comparison.flipped_cells)
        assert m8_fired == class_changed, label


def test_b25_decisive_set_is_exact_once_the_class_has_flipped():
    """WAS `test_b25_decisive_set_is_read_off_the_existential_itself`, whose
    wording implied a combination is decisive whenever its membership of the
    satisfying set differs. That is only true AFTER a class flip, and this
    test is the very case that shows why: `{A}` -> `{B}` differs in both
    directions while the class holds at IN.

    Given a flip, one of the two sets is empty, so the symmetric difference
    is exactly the combinations that entered or left. That is asserted here
    in both directions."""
    kind = gr.POSITIVE_EV_REGION
    key = gr.GRID_CELL_KEYS[0]

    # substitution: XOR is non-empty, yet the class never moved
    a_in = _two_combo_grid(100.0, -100.0)[key]
    b_in = _two_combo_grid(-100.0, 100.0)[key]
    assert (gr.satisfying_combos(a_in, kind)
            ^ gr.satisfying_combos(b_in, kind)) == {"A", "B"}
    assert gr.cell_category(a_in, kind) == gr.cell_category(b_in, kind)

    # a real flip: one side is empty, so the XOR names the responsible combo
    supported = _two_combo_grid(-5000.0, 3.0)[key]
    lost = _two_combo_grid(-5000.0, -2.0)[key]
    assert gr.satisfying_combos(lost, kind) == frozenset()
    assert (gr.satisfying_combos(supported, kind)
            ^ gr.satisfying_combos(lost, kind)) == {"B"}


def test_k_doubling_must_actually_double():
    with pytest.raises(mcc.MCInputError) as ei:
        gr.compare_region_maps(gr.POSITIVE_EV_REGION, _grid(), _grid(),
                               k=200, k_doubled=300)
    assert ei.value.code == "grid_replay_k_doubling_violation"


# ---------------------------------------------------------------------------
# M9 — rule (c) transplanted to the cell layer
# ---------------------------------------------------------------------------

def test_cell_drift_beyond_the_frozen_tolerance_is_non_convergence(authority):
    """(c) intercepts drift that has NOT yet flipped a class — the
    precursor to flipping. It REPORTS rather than raising: per (e) the
    consequence of a failed (c) is to double K and rerun, which is what a
    False convergence flag records, not a malformed-input refusal."""
    at_k = _grid(p5=1000.0, median=1000.0)
    at_2k = _grid(p5=1200.0, median=1000.0)     # +200 > max($25, 5% of 1000)
    violations = gr.cell_drift_violations(gr.POSITIVE_EV_REGION, at_k, at_2k)
    assert len(violations) == len(gr.GRID_CELL_KEYS)
    comparison = gr.compare_region_maps(gr.POSITIVE_EV_REGION, at_k, at_2k,
                                        k=200, k_doubled=400)
    assert comparison.converged is False        # (c) alone sinks it
    assert comparison.flipped_cells == ()       # ... with no class flip
    ev = gr.derive_k_replay_evidence(authority, master_seed=7,
                                     cells_at_k=at_k, cells_at_2k=at_2k)
    assert ev.grid_converged is False


def test_the_dollar_floor_applies_at_the_cell_layer(authority):
    """M9(b): cells are the same unit as SS4.4 (USD/month), so $25 applies
    directly. A $20 move on a near-zero cell is inside the floor."""
    assert gr.frozen_tolerance(0.0) == 25.0
    assert gr.cell_drift_violations(
        gr.POSITIVE_EV_REGION,
        _grid(p5=1.0, median=1.0), _grid(p5=21.0, median=1.0)) == ()


def test_non_usd_identity_keys_must_be_identical_not_merely_close():
    """M9: realized counts are configuration/identity, NOT statistics, so
    (c) does not govern them and a one-sample difference is a mismatch."""
    at_k = _grid(identity={"n_tp": 10})
    at_2k = _grid(identity={"n_tp": 11})
    with pytest.raises(mcc.MCInputError) as ei:
        gr.compare_region_maps(gr.POSITIVE_EV_REGION, at_k, at_2k,
                               k=200, k_doubled=400)
    assert ei.value.code == "grid_replay_cell_identity_mismatch"


# ---------------------------------------------------------------------------
# KReplayEvidence — the inner K witness
# ---------------------------------------------------------------------------

def test_the_evidence_is_factory_only_and_self_digested(authority):
    ev = gr.derive_k_replay_evidence(authority, master_seed=7,
                                     cells_at_k=_grid(), cells_at_2k=_grid())
    gr.verify_k_replay_evidence(ev)
    with pytest.raises(mcc.MCInputError) as ei:
        dataclasses.replace(ev, master_seed=13)
    assert ei.value.code == "k_replay_evidence_capability_required"
    forged = object.__new__(gr.KReplayEvidence)
    for f in dataclasses.fields(ev):
        object.__setattr__(forged, f.name, getattr(ev, f.name))
    object.__setattr__(forged, "master_seed", 13)
    with pytest.raises(mcc.MCInputError) as ei:
        gr.verify_k_replay_evidence(forged)
    assert ei.value.code == "k_replay_evidence_digest_mismatch"


def test_the_evidence_binds_to_its_authority_and_a_research_seed(authority):
    ev = gr.derive_k_replay_evidence(authority, master_seed=7,
                                     cells_at_k=_grid(), cells_at_2k=_grid())
    assert ev.authority_digest == authority.authority_digest
    assert ev.prepared_digest == authority.prepared_digest
    assert ev.k == mcc.K_PER_SEED_FROZEN and ev.k_doubled == 400
    with pytest.raises(mcc.MCInputError) as ei:
        gr.derive_k_replay_evidence(authority, master_seed=99,
                                    cells_at_k=_grid(), cells_at_2k=_grid())
    assert ei.value.code == "k_replay_evidence_seed_not_research_seed"


def test_an_off_frozen_k_refuses(authority):
    with pytest.raises(mcc.MCInputError) as ei:
        gr.derive_k_replay_evidence(authority, master_seed=7, k=100,
                                    cells_at_k=_grid(), cells_at_2k=_grid())
    assert ei.value.code == "grid_replay_k_per_seed_not_frozen"


def test_evidence_cannot_be_minted_without_a_real_authority():
    with pytest.raises(mcc.MCInputError) as ei:
        gr.derive_k_replay_evidence(object(), master_seed=7,
                                    cells_at_k=_grid(), cells_at_2k=_grid())
    assert ei.value.code == "grid_replay_authority_required"


# ---------------------------------------------------------------------------
# M10 — the published cross-seed region
# ---------------------------------------------------------------------------

def test_the_published_region_is_the_intersection_of_the_three_seeds():
    key = gr.GRID_CELL_KEYS[0]
    all_in = gr.region_map(_grid(), gr.POSITIVE_EV_REGION)
    dissenting = dict(all_in)
    dissenting[key] = gr.OUT_OF_REGION
    maps = {7: all_in, 13: dict(all_in), 31: dissenting}
    published = gr.publish_region(gr.POSITIVE_EV_REGION, maps)
    # the dissenting cell falls into the UNION band and is disclosed,
    # never resolved by majority
    assert published[key] == gr.BOUNDARY_BAND
    assert published[gr.GRID_CELL_KEYS[1]] == gr.IN_REGION


def test_publishing_needs_all_three_research_seeds():
    all_in = gr.region_map(_grid(), gr.POSITIVE_EV_REGION)
    with pytest.raises(mcc.MCInputError) as ei:
        gr.publish_region(gr.POSITIVE_EV_REGION, {7: all_in, 13: all_in})
    assert ei.value.code == "grid_replay_cross_seed_set_incomplete"
    assert set(RESEARCH_BOOTSTRAP_SEEDS) == {7, 13, 31}


# ---------------------------------------------------------------------------
# THE WIRING — outer K bound to the authorized inner witness
# ---------------------------------------------------------------------------

@pytest.fixture()
def small_scale(monkeypatch):
    """The synthetic runs are B=2; the frozen production scale is B=1000.
    The existing convergence tests relax it the same way."""
    monkeypatch.setattr(mcc, "B_WORLDS_FROZEN", 2)


def _k_case(prepared, authority, **kw):
    base = CR._evidence(prepared)
    k_run = CR._evidence(prepared, run_label="double_K", axis="K", K=400)
    witness = gr.derive_k_replay_evidence(
        authority, master_seed=7, cells_at_k=_grid(), cells_at_2k=_grid(),
        **kw)
    return base, {"B": CR._evidence(prepared, run_label="double_B", axis="B",
                                    B=4),
                  "K": k_run}, witness


def test_a_k_entry_without_its_witness_still_refuses(prepared, authority, small_scale):
    """The pre-N11 block was REPLACED BY A BINDING, not removed. The code
    is unchanged on purpose: the prohibition on impersonation never
    lapsed, only the claim that no honest evidence could exist."""
    base, doubled, _ = _k_case(prepared, authority)
    with pytest.raises(mcc.MCInputError) as ei:
        mcc.convergence_from_evidence(base, doubled, CR._seed_runs(prepared),
                                      prepared=prepared)
    assert ei.value.code == "k_axis_evidence_blocked_grid_replay"


def test_the_outer_k_must_match_the_witness(prepared, authority, small_scale):
    """A relabelled base run and a real K-doubled run must stop being
    indistinguishable — that was the whole point of the pre-N11 guard."""
    base, doubled, witness = _k_case(prepared, authority)
    liar = dict(doubled)
    liar["K"] = CR._evidence(prepared, run_label="double_K", axis="K", K=800)
    with pytest.raises(mcc.MCInputError) as ei:
        mcc.convergence_from_evidence(base, liar, CR._seed_runs(prepared),
                                      prepared=prepared, k_witness=witness)
    assert ei.value.code == "doubling_scale_violation"


def test_a_witness_from_another_seed_refuses(prepared, authority, small_scale):
    base, doubled, _ = _k_case(prepared, authority)
    other = gr.derive_k_replay_evidence(
        authority, master_seed=13, cells_at_k=_grid(), cells_at_2k=_grid())
    with pytest.raises(mcc.MCInputError) as ei:
        mcc.convergence_from_evidence(base, doubled, CR._seed_runs(prepared),
                                      prepared=prepared, k_witness=other)
    assert ei.value.code == "k_replay_inner_mismatch:master_seed"


def test_a_forged_witness_refuses(prepared, authority, small_scale):
    """A mutated witness fails its own digest.

    THIS TEST WAS GREEN FOR THE WRONG REASON until B-26 landed. The
    original mutation set `converged_by_kind` to all-True and `k_doubled`
    to 400 — both of which the honest witness ALREADY carried, so nothing
    was actually forged, the digest still verified, and the only reason an
    MCInputError appeared was the feasibility dead end further down.
    Removing that dead end exposed it. The mutation is now real.
    """
    base, doubled, witness = _k_case(prepared, authority)
    assert witness.grid_converged is True          # so flipping it is a lie
    forged = object.__new__(gr.KReplayEvidence)
    for f in dataclasses.fields(witness):
        object.__setattr__(forged, f.name, getattr(witness, f.name))
    object.__setattr__(forged, "master_seed", witness.master_seed + 6)
    with pytest.raises(mcc.MCInputError) as ei:
        mcc.convergence_from_evidence(base, doubled, CR._seed_runs(prepared),
                                      prepared=prepared, k_witness=forged)
    assert ei.value.code == "k_replay_evidence_digest_mismatch"


def test_a_k_pass_may_not_move_the_oracle_main_channel(prepared, authority, small_scale):
    """K is inner random source (2), "grid analysis ONLY", and M10 reruns
    the grid channel alone. A K run whose Checkpoint statistics moved
    either let K reach the main channel or is not the run it claims."""
    base, doubled, witness = _k_case(prepared, authority)
    moved = dict(doubled)
    moved["K"] = CR._evidence(prepared, run_label="double_K", axis="K",
                              K=400, seed=7, B=2)
    # perturb one inner result so the main channel differs
    cid = sorted(base.results)[0]
    cons, stress = moved["K"].results[cid]
    object.__setattr__(cons, "p5", cons.p5 + 1.0)
    with pytest.raises(mcc.MCInputError) as ei:
        mcc.convergence_from_evidence(base, moved, CR._seed_runs(prepared),
                                      prepared=prepared, k_witness=witness)
    assert ei.value.code == "k_axis_main_channel_not_invariant"


def test_the_k_axis_is_no_longer_the_blocker(prepared, authority,
                                            small_scale):
    """SYNTHETIC GRID -> K END TO END: sealed supplement -> authority ->
    two grid passes -> witness -> the K arm ADMITS -> rules (a)-(d) ->
    ConvergenceReport.

    When N11 closed, this test asserted that the path stopped one step
    later at `feasibility_gate_input_absent`, and it named that boundary
    so the next session would not re-diagnose it as a K problem. B-26 has
    since composed the feasibility evidence, so the path now completes and
    the assertion becomes the positive one.

    No MC is run: the arms are synthetic RunEvidence fixtures at B=2/M=2.
    """
    base, doubled, witness = _k_case(prepared, authority)
    report = mcc.convergence_from_evidence(
        base, doubled, CR._seed_runs(prepared), prepared=prepared,
        k_witness=witness)
    assert type(report) is mcc.ConvergenceReport
    assert set(report.drift_by_axis) == {"double_B", "double_K", "seed_7",
                                        "seed_13", "seed_31"}
    for flag in (report.category_stable_under_doubling,
                 report.category_same_across_seeds,
                 report.quantile_drift_ok, report.mcse_ok,
                 report.converged):
        assert isinstance(flag, bool)
    # the witness still has to be there: K is admitted on evidence, never
    # on outer metadata (N11), and B-26 did not relax that.
    with pytest.raises(mcc.MCInputError) as ei:
        mcc.convergence_from_evidence(base, doubled, CR._seed_runs(prepared),
                                      prepared=prepared)
    assert ei.value.code == "k_axis_evidence_blocked_grid_replay"
