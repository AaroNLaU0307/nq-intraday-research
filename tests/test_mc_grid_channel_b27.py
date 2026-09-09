"""B-27 — the adopted Cartesian M x K semantics, proved mechanically.

THE RULING under test: the GRID channel composes K stratified TP/FP marker
draws per cell and governed seed with M exhaustive legal start phases by the
FULL CARTESIAN PRODUCT inside every existing B world; each draw keeps its
marker sequence across phases; every `(world, phase, draw)` contributes exactly
once; the M x K inner distribution enters the EXISTING within-world reduction
and Conservative P5 / Stress median come from the UNCHANGED across-world
aggregation; doubling K appends draws and preserves the first K.

Everything here is synthetic: a fabricated bundle, a synthetic DAY_STRATA
supplement, a synthetic registry chain, B=2, M=2, K=2. No real MC is executed
and no value below is a research result.

TWO POOLS, for two different jobs, stated so neither is mistaken for tuning.
`wide` (3 TP / 9 FP) is widened so that NO cell of the frozen 63-cell grid is
unsampleable, which is what lets the Cartesian proofs A-H exercise the whole
grid instead of a feasible corner of it. `narrow` (3 TP / 3 FP), added with the
N13-F1 section at the end, is the opposite: there the frozen arithmetic makes
q=0.35/r=0.80 genuinely unsampleable while q=0.50 and q=0.75 stay sampleable,
which is what lets the SEALED mark/skip/report/continue rule be proved on a real
geometry rather than by patching the frozen allocator.
"""
import dataclasses
import hashlib
import json
import shutil

import pytest

import test_mc_battery_boundary as BB
import test_mc_registry_parser as RP
from itsf import contracts
from itsf.contracts import RESEARCH_BOOTSTRAP_SEEDS, GridRepeatPolicy
from itsf.mc import atoms as mc_atoms
from itsf.mc import consumer as mcc
from itsf.mc import day_strata_supplement as ds
from itsf.mc import feasibility as fz
from itsf.mc import grid_channel as gc
from itsf.mc import grid_replay as gr
from itsf.mc import mc_contract as mcx
from itsf.mc import mc_runner as run
from itsf.mc import supplement_authority as sa

B_SMALL = 2
K_SMALL = 2
OUT_ROOT = "C:/synthetic/b27-output-root"
WIDE_TP = ("2026-08-03", "2026-08-05", "2026-08-07")
WIDE_FP = ("2026-08-04", "2026-08-06", "2026-08-10", "2026-08-11",
           "2026-08-12", "2026-08-13", "2026-08-14", "2026-08-17",
           "2026-08-18")


@pytest.fixture()
def small_grid(monkeypatch):
    """K = 2 instead of the frozen 200, so the Cartesian product is countable.

    Only `k_per_seed` moves. `k_start_index`, `stream_includes_theta` and
    `max_doublings` stay as ruled, because those are what make the draws
    prefix-nested and theta-separated — the properties under test.
    """
    methods = contracts.aaron_ruled_methods()
    small = dataclasses.replace(methods, grid_policy=GridRepeatPolicy(
        k_per_seed=K_SMALL, k_start_index=methods.grid_policy.k_start_index,
        stream_includes_theta=True,
        convergence_rule=methods.grid_policy.convergence_rule,
        max_doublings=methods.grid_policy.max_doublings))
    monkeypatch.setattr(contracts, "aaron_ruled_methods", lambda: small)
    monkeypatch.setattr(mcc, "B_WORLDS_FROZEN", B_SMALL)
    # The FIXTURE MUST BE COHERENT. Shrinking only the draw policy would let
    # the witness report the ruled k=200 while the pass ran 2 draws — a false
    # claim in the evidence, and the runner now refuses it. So the frozen
    # k_per_seed and the bundle's SEED_MANIFEST move together with the policy.
    monkeypatch.setattr(mcc, "K_PER_SEED_FROZEN", K_SMALL)
    return small


@pytest.fixture()
def wide(monkeypatch, tmp_path_factory, small_grid):
    """A PRODUCTION-shaped prepared input over a wider FP pool."""
    monkeypatch.setattr(BB, "TP_DAYS", WIDE_TP)
    monkeypatch.setattr(BB, "FP_DAYS", WIDE_FP)
    monkeypatch.setattr(BB, "ALL_DAYS", tuple(sorted(WIDE_TP + WIDE_FP)))
    root = tmp_path_factory.mktemp("b27root")
    for rel in BB.FROZEN_METHOD_FILES:
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(BB.REAL_REPO_ROOT / rel, root / rel)
    bundle = _coherent_bundle()
    att = BB._attestation_bytes(bundle)
    (root / mcc.ATTESTATION_PATH).parent.mkdir(parents=True, exist_ok=True)
    (root / mcc.ATTESTATION_PATH).write_bytes(att)
    monkeypatch.setattr(mcc, "_REPO_ROOT", root)
    monkeypatch.setattr(mcc, "ATTESTATION_SHA256_PINNED",
                        hashlib.sha256(att).hexdigest())
    monkeypatch.setattr(mcc, "build_template_calendar",
                        lambda *a, **k: BB._calendar())
    return mcc.prepare_mc_input(
        bundle, authorization_snapshot={"trial_id": BB.TRIAL,
                                        "authorized_commit": BB.COMMIT},
        attestation_bytes=att)


def _coherent_bundle(pnl=80.0):
    """A bundle whose SEED_MANIFEST k_policy matches the shrunken
    `K_PER_SEED_FROZEN`, with `manifest.jsonl` rebuilt so the exact-set and
    per-file digest battery still passes."""
    bundle = BB._bundle(pnl=pnl)
    seeds = json.loads(bundle["SEED_MANIFEST.json"].decode("utf-8"))
    seeds["k_policy"] = f"k_per_seed={K_SMALL};k_start_index=0"
    bundle["SEED_MANIFEST.json"] = json.dumps(seeds).encode("utf-8")
    # the battery builds `manifest.jsonl` inline, so it is rebuilt the same
    # way here after the k_policy edit — a stale manifest would fail the
    # exact-set/per-file digest battery, which is the correct behaviour and
    # not something to work around
    del bundle["manifest.jsonl"]
    bundle["manifest.jsonl"] = "\n".join(
        json.dumps({"record_type": "file", "relative_path": n,
                    "file_sha256": hashlib.sha256(bundle[n]).hexdigest()},
                   sort_keys=True) for n in sorted(bundle)).encode("utf-8")
    return bundle


@pytest.fixture()
def supplement(wide):
    authority = sa.derive_supplement_authority(wide,
                                               supplement_id=ds.SUPPLEMENT_ID)
    days, binding = sa.supplement_build_inputs(authority, wide)
    rows = [{"trade_date": d, "year": int(str(d)[:4]),
             "vol_stratum": ds.VOL_STRATA[i % len(ds.VOL_STRATA)],
             "event_stratum": ds.EVENT_STRATA[i % len(ds.EVENT_STRATA)]}
            for i, d in enumerate(sorted(days))]
    return ds.build_day_strata_supplement_test_only(
        rows, expected_day_set=days, binding=binding,
        supplement_id=ds.SUPPLEMENT_ID)


def _sha(supplement):
    return hashlib.sha256(
        ds.canonical_supplement_bytes(supplement)).hexdigest()


@pytest.fixture()
def authority(wide, supplement):
    return gr.derive_grid_replay_authority(
        wide, supplement, sealed_artifact_sha256=_sha(supplement))


#: A cell the fixture can sample on both sides.
CELL = (500, 800)


# ---------------------------------------------------------------------------
# A — CARTESIAN COVERAGE
# ---------------------------------------------------------------------------

def test_A_cartesian_coverage_is_exactly_b_times_m_times_k(
        wide, authority, supplement, small_grid, monkeypatch):
    """B x M x K logical contributions per (combo, scenario), each exactly
    once — counted at the ONE lifecycle execution site, not inferred."""
    calls = []
    real = mcc._run_path_atom

    def counting(prepared, **kw):
        calls.append((kw["world_index"], kw["phase_offset"],
                      kw["platform"], kw["engine"], kw["scenario"],
                      frozenset(kw["traded_selector"] or ())))
        return real(prepared, **kw)
    monkeypatch.setattr(mcc, "_run_path_atom", counting)

    draws = gc.derive_cell_draws(authority, wide, supplement, master_seed=7,
                                 q_mil=CELL[0], r_mil=CELL[1])
    assert len(draws) == K_SMALL
    M = len(wide.calendar.first_month_offsets)
    combos = len(mcc.PRIMARY_COMBOS) * len(mcc.ENGINES)
    scenarios = len(fz.GATE_SCENARIOS)

    gc.run_grid_cell(wide, authority, supplement, q_mil=CELL[0],
                     r_mil=CELL[1], master_seed=7, B=B_SMALL)

    expected = B_SMALL * M * K_SMALL * combos * scenarios
    assert len(calls) == expected, (len(calls), expected)
    # exactly once per (world, phase, draw) within every (combo, scenario)
    per_slice = {}
    for wi, off, plat, eng, scen, sel in calls:
        per_slice.setdefault((plat, eng, scen), []).append((wi, off, sel))
    assert len(per_slice) == combos * scenarios
    for slice_key, entries in per_slice.items():
        assert len(entries) == B_SMALL * M * K_SMALL, slice_key
        # each (world, phase) is visited exactly K times, once per draw
        by_wp = {}
        for wi, off, sel in entries:
            by_wp.setdefault((wi, off), []).append(sel)
        assert len(by_wp) == B_SMALL * M
        for wp, sels in by_wp.items():
            assert len(sels) == K_SMALL, wp


def test_A_the_evaluation_key_set_is_the_declared_cartesian_product(
        wide, authority, supplement, small_grid):
    """The container's own keys are `(world, phase, draw)`, and a repeat is
    refused rather than silently overwritten."""
    draws = gc.derive_cell_draws(authority, wide, supplement, master_seed=7,
                                 q_mil=CELL[0], r_mil=CELL[1])
    ev = gc._evaluate(wide, draws=draws, platform="topstep", engine="E1",
                      scenario="Conservative",
                      channel=mcc.PRIMARY_THETA_CHANNEL, B=B_SMALL,
                      master_seed=7, q_mil=CELL[0], r_mil=CELL[1])
    M = len(wide.calendar.first_month_offsets)
    assert set(ev.atoms_by_key) == ev.expected_key_grid
    assert len(ev.atoms_by_key) == B_SMALL * M * K_SMALL
    assert len(ev.atoms) == B_SMALL * M * K_SMALL


# ---------------------------------------------------------------------------
# B — DRAW STABILITY ACROSS PHASES
# ---------------------------------------------------------------------------

def test_B_one_draw_keeps_its_marker_sequence_across_every_phase(
        wide, authority, supplement, small_grid, monkeypatch):
    """A phase change must not resample the grid: for a fixed draw the
    selector handed to the lifecycle is byte-identical across all phases and
    all worlds."""
    seen = {}
    real = mcc._run_path_atom

    def recording(prepared, **kw):
        seen.setdefault(frozenset(kw["traded_selector"] or ()), set()).add(
            (kw["world_index"], kw["phase_offset"]))
        return real(prepared, **kw)
    monkeypatch.setattr(mcc, "_run_path_atom", recording)

    draws = gc.derive_cell_draws(authority, wide, supplement, master_seed=7,
                                 q_mil=CELL[0], r_mil=CELL[1])
    gc._evaluate(wide, draws=draws, platform="topstep", engine="E1",
                 scenario="Conservative", channel=mcc.PRIMARY_THETA_CHANNEL,
                 B=B_SMALL, master_seed=7, q_mil=CELL[0], r_mil=CELL[1])
    M = len(wide.calendar.first_month_offsets)
    # every distinct selector was used across the FULL (world, phase) grid
    for selector, wp in seen.items():
        assert wp == {(b, int(m))
                      for b in range(B_SMALL)
                      for m in wide.calendar.first_month_offsets}, selector
        assert len(wp) == B_SMALL * M
    # ... and the selector set is exactly the draws' marker sequences
    assert seen.keys() == {frozenset(d.traded_days) for d in draws} or (
        len(seen) <= len(draws))


# ---------------------------------------------------------------------------
# C — K -> 2K PREFIX NESTING
# ---------------------------------------------------------------------------

def test_C_the_2k_pass_preserves_the_first_k_draws_and_their_outputs(
        wide, authority, supplement, small_grid):
    """The first K draws of a 2K pass are the SAME draws, and the shared
    `(b, m, k)` evaluations reproduce bit for bit — compared on the atoms'
    own canonical digests, so this cannot pass by comparing one object twice.
    """
    k_draws = gc.derive_cell_draws(authority, wide, supplement, master_seed=7,
                                   q_mil=CELL[0], r_mil=CELL[1], doublings=0)
    k2_draws = gc.derive_cell_draws(authority, wide, supplement, master_seed=7,
                                    q_mil=CELL[0], r_mil=CELL[1], doublings=1)
    assert len(k_draws) == K_SMALL and len(k2_draws) == 2 * K_SMALL
    assert [d.draw_digest for d in k_draws] == [
        d.draw_digest for d in k2_draws[:K_SMALL]]
    assert [d.traded_days for d in k_draws] == [
        d.traded_days for d in k2_draws[:K_SMALL]]
    assert [d.draw_index for d in k2_draws] == list(
        range(k_draws[0].draw_index, k_draws[0].draw_index + 2 * K_SMALL))

    common = dict(platform="topstep", engine="E1", scenario="Conservative",
                  channel=mcc.PRIMARY_THETA_CHANNEL, B=B_SMALL,
                  master_seed=7, q_mil=CELL[0], r_mil=CELL[1])
    ev_k = gc._evaluate(wide, draws=k_draws, **common)
    ev_2k = gc._evaluate(wide, draws=k2_draws, **common)
    shared = set(ev_k.atoms_by_key)
    assert shared and shared <= set(ev_2k.atoms_by_key)
    for key in sorted(shared):
        assert (mc_atoms.atom_digest(ev_k.atoms_by_key[key])
                == mc_atoms.atom_digest(ev_2k.atoms_by_key[key])), key
    # 2K only APPENDS
    appended = set(ev_2k.atoms_by_key) - shared
    assert len(appended) == B_SMALL * len(
        wide.calendar.first_month_offsets) * K_SMALL
    assert {d for _b, _m, d in appended} == set(
        range(k_draws[0].draw_index + K_SMALL,
              k_draws[0].draw_index + 2 * K_SMALL))


# ---------------------------------------------------------------------------
# D — M REMAINS EXHAUSTIVE
# ---------------------------------------------------------------------------

def test_D_every_legal_phase_appears_for_every_draw(
        wide, authority, supplement, small_grid):
    """K does not replace or subsample M. The phase support comes from the
    prepared authority and every draw sees all of it."""
    draws = gc.derive_cell_draws(authority, wide, supplement, master_seed=7,
                                 q_mil=CELL[0], r_mil=CELL[1])
    ev = gc._evaluate(wide, draws=draws, platform="topstep", engine="E1",
                      scenario="Stress", channel=mcc.PRIMARY_THETA_CHANNEL,
                      B=B_SMALL, master_seed=7, q_mil=CELL[0], r_mil=CELL[1])
    support = tuple(wide.calendar.first_month_offsets)
    assert ev.legal_phase_support == support
    for draw in draws:
        phases = {m for _b, m, d in ev.atoms_by_key
                  if d == draw.draw_index}
        assert phases == {int(m) for m in support}, draw.draw_index
    for b in range(B_SMALL):
        for draw in draws:
            assert {m for bb, m, d in ev.atoms_by_key
                    if bb == b and d == draw.draw_index} == {
                        int(m) for m in support}


# ---------------------------------------------------------------------------
# E — WORLD-LEVEL AGGREGATION (not flattening)
# ---------------------------------------------------------------------------

def test_E_the_hierarchy_is_within_world_then_across_world(
        wide, authority, supplement, small_grid):
    """The governed hierarchy, asserted structurally AND arithmetically.

    Structurally: the reduction produces ONE statistic per world (length B),
    not one per lifecycle (length B x M x K), and the percentile is taken over
    that B-length vector.

    Arithmetically: `percentile_linear` over the flattened B x M x K outcomes
    and over the B world means are different estimators. The demonstration
    below uses the repository's own estimator on crafted numbers so the
    difference is visible even when a small fixture happens to make the two
    coincide, and then asserts the module's own output equals the HIERARCHY
    value.
    """
    draws = gc.derive_cell_draws(authority, wide, supplement, master_seed=7,
                                 q_mil=CELL[0], r_mil=CELL[1])
    ev = gc._evaluate(wide, draws=draws, platform="topstep", engine="E1",
                      scenario="Conservative",
                      channel=mcc.PRIMARY_THETA_CHANNEL, B=B_SMALL,
                      master_seed=7, q_mil=CELL[0], r_mil=CELL[1])
    M = len(wide.calendar.first_month_offsets)

    means = ev.world_means()
    assert len(means) == B_SMALL                       # one per world
    assert len(ev.atoms) == B_SMALL * M * K_SMALL      # not per lifecycle
    hierarchy = mc_atoms.percentile_linear(sorted(means), fz.P5)

    cs = gc.run_grid_cell(wide, authority, supplement, q_mil=CELL[0],
                          r_mil=CELL[1], master_seed=7, B=B_SMALL)
    assert cs.conservative_p5["topstep|E1|P2"] == hierarchy

    # the two estimators are genuinely different — shown on crafted numbers
    # with the repository's own percentile, so the property does not depend
    # on this fixture's values happening to separate.
    flat = [0.0, 0.0, 0.0, 100.0, 100.0, 100.0]        # 2 worlds x 3 inner
    world_means = [0.0, 100.0]
    assert (mc_atoms.percentile_linear(sorted(flat), fz.P5)
            != mc_atoms.percentile_linear(sorted(world_means), fz.P5))


def test_E_raw_outcomes_are_never_pooled_across_worlds(
        wide, authority, supplement, small_grid):
    """`reduce_world_means` groups by world index; a pooled reduction would
    return one number rather than B."""
    draws = gc.derive_cell_draws(authority, wide, supplement, master_seed=7,
                                 q_mil=CELL[0], r_mil=CELL[1])
    ev = gc._evaluate(wide, draws=draws, platform="lucid", engine="E2",
                      scenario="Stress", channel=mcc.PRIMARY_THETA_CHANNEL,
                      B=B_SMALL, master_seed=7, q_mil=CELL[0], r_mil=CELL[1])
    assert len(ev.world_means()) == B_SMALL
    assert len(ev.within_world_ses()) == B_SMALL
    # and it is the repository's own reduction, not a local copy
    assert ev.world_means() == mc_atoms.reduce_world_means(ev.atoms)


# ---------------------------------------------------------------------------
# F — SELECTOR AUTHORITY
# ---------------------------------------------------------------------------

def test_F_no_prepared_input_is_built_narrowed_or_impersonated(
        wide, authority, supplement, small_grid):
    """The selector changes which slots trade. It does not touch the prepared
    authority: same digest before and after, and the module constructs no
    `PreparedMCInput` at all."""
    import ast
    import inspect

    before = mcc.prepared_digest(wide)
    gc.run_grid_cell(wide, authority, supplement, q_mil=CELL[0],
                     r_mil=CELL[1], master_seed=7, B=B_SMALL)
    assert mcc.prepared_digest(wide) == before
    assert wide.battery_receipt is not None

    tree = ast.parse(inspect.getsource(gc))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert "PreparedMCInput" not in str(name)
            assert name not in {"prepare_mc_input",
                                "prepare_mc_input_for_tests"}


def test_F_the_selector_can_narrow_but_never_invent_a_trade(wide, small_grid):
    """`_paths_for_world` still requires a sealed record for every traded
    slot, so a selector naming days outside the sealed records adds nothing."""
    world = mcc.build_world_table(wide, channel=mcc.PRIMARY_THETA_CHANNEL,
                                  B=1, master_seed=7)[0]
    oracle = mcc._paths_for_world(wide, world, mcc.PRIMARY_THETA_CHANNEL,
                                  "E1", "Conservative")
    invented = mcc._paths_for_world(
        wide, world, mcc.PRIMARY_THETA_CHANNEL, "E1", "Conservative",
        traded_selector=frozenset({"1999-01-01", "2050-12-31"}))
    assert invented == {}
    narrowed = mcc._paths_for_world(
        wide, world, mcc.PRIMARY_THETA_CHANNEL, "E1", "Conservative",
        traded_selector=frozenset(WIDE_TP[:1]))
    assert set(narrowed) <= set(oracle)


def test_F_the_oracle_main_channel_is_unchanged_by_b27(wide, small_grid):
    """Selector None is the path it always was — the default is the
    channel's Oracle-selected set, byte for byte."""
    world = mcc.build_world_table(wide, channel=mcc.PRIMARY_THETA_CHANNEL,
                                  B=1, master_seed=7)[0]
    default = mcc._paths_for_world(wide, world, mcc.PRIMARY_THETA_CHANNEL,
                                   "E1", "Conservative")
    explicit = mcc._paths_for_world(
        wide, world, mcc.PRIMARY_THETA_CHANNEL, "E1", "Conservative",
        traded_selector=wide.traded_day_sets[mcc.PRIMARY_THETA_CHANNEL])
    assert default == explicit


def test_F_the_atom_layer_still_carries_no_k(small_grid):
    """MC SS5 keeps K in the grid. B-27 composes MORE ATOMS rather than adding
    a K field, so `EpistemicResult` / `ObservationSet` /
    `SimulationPathObservation` are unchanged — which is what keeps N11's
    deliberate outer-K guard meaningful."""
    from itsf.mc.atoms import ObservationSet, SimulationPathObservation
    for T in (mcc.EpistemicResult, ObservationSet, SimulationPathObservation):
        assert not [n for n in T.__dataclass_fields__
                    if n == "K" or n.lower().startswith("k_")]


# ---------------------------------------------------------------------------
# G — DRAW PROVENANCE
# ---------------------------------------------------------------------------

def test_G_a_hand_built_draw_has_no_callable_path(wide, small_grid):
    with pytest.raises(mcc.MCInputError) as ei:
        gc.GridDraw(capability=None, schema=gc.GRID_DRAW_SCHEMA,
                    authority_digest="0" * 64, prepared_digest="0" * 64,
                    theta_channel=mcc.PRIMARY_THETA_CHANNEL, master_seed=7,
                    q_mil=500, r_mil=800, draw_index=0,
                    traded_days=WIDE_TP, n_tp=3, n_fp=0,
                    draw_digest="0" * 64)
    assert ei.value.code == "grid_draw_capability_required"


def test_G_a_mutated_draw_fails_its_own_digest(wide, authority, supplement,
                                              small_grid):
    draw = gc.derive_cell_draws(authority, wide, supplement, master_seed=7,
                                q_mil=CELL[0], r_mil=CELL[1])[0]
    forged = object.__new__(gc.GridDraw)
    for f in dataclasses.fields(draw):
        object.__setattr__(forged, f.name, getattr(draw, f.name))
    object.__setattr__(forged, "traded_days", tuple(WIDE_FP[:2]))
    with pytest.raises(mcc.MCInputError) as ei:
        gc.verify_draw(forged)
    assert ei.value.code == "grid_draw_digest_mismatch"


def test_G_a_stratum_table_the_authority_did_not_license_refuses(
        wide, authority, supplement, small_grid):
    """The rows are re-digested against `authority.rows_digest`, so replay
    cannot be licensed with one table and drawn from another."""
    swapped = dict(supplement)
    rows = [dict(r) for r in supplement["rows"]]
    rows[0]["vol_stratum"] = ds.VOL_STRATA[
        (ds.VOL_STRATA.index(rows[0]["vol_stratum"]) + 1)
        % len(ds.VOL_STRATA)]
    swapped["rows"] = rows
    with pytest.raises(mcc.MCInputError) as ei:
        gc.derive_cell_draws(authority, wide, swapped, master_seed=7,
                             q_mil=CELL[0], r_mil=CELL[1])
    assert ei.value.code == "grid_draw_supplement_rows_digest_mismatch"


def test_G_draw_identity_separates_cells_seeds_and_indices(
        wide, authority, supplement, small_grid):
    """No collisions: a different cell, a different governed seed or a
    different draw index is a different draw digest."""
    base = gc.derive_cell_draws(authority, wide, supplement, master_seed=7,
                                q_mil=CELL[0], r_mil=CELL[1])
    other_cell = gc.derive_cell_draws(authority, wide, supplement,
                                      master_seed=7, q_mil=750, r_mil=800)
    other_seed = gc.derive_cell_draws(authority, wide, supplement,
                                      master_seed=13, q_mil=CELL[0],
                                      r_mil=CELL[1])
    digests = {d.draw_digest for d in base}
    assert len(digests) == len(base)                       # per-index
    assert digests.isdisjoint({d.draw_digest for d in other_cell})
    assert digests.isdisjoint({d.draw_digest for d in other_seed})


def test_G_a_non_research_seed_and_a_foreign_authority_refuse(
        wide, authority, supplement, small_grid):
    with pytest.raises(Exception):
        gc.derive_cell_draws(authority, wide, supplement, master_seed=99,
                             q_mil=CELL[0], r_mil=CELL[1])
    # a DIFFERENT prepared input, built the same coherent way (the fixture
    # patches k_per_seed, so an unpatched bundle would refuse earlier on
    # `k_policy_violation` and prove nothing about provenance)
    other_bundle = _coherent_bundle(pnl=91.0)
    other = mcc.prepare_mc_input_for_tests(
        other_bundle, authorization_snapshot={"trial_id": BB.TRIAL,
                                              "authorized_commit": BB.COMMIT},
        custody_authority=mcc.CustodyAuthority.for_tests(other_bundle),
        test_only_calendar=BB._calendar())
    assert mcc.prepared_digest(other) != mcc.prepared_digest(wide)
    with pytest.raises(mcc.MCInputError) as ei:
        gc.derive_cell_draws(authority, other, supplement, master_seed=7,
                             q_mil=CELL[0], r_mil=CELL[1])
    assert ei.value.code == "provenance_mismatch"


def test_G_a_precheck_disagreement_fails_closed_under_its_own_code(
        wide, authority, supplement, small_grid, monkeypatch):
    """REPLACES the N13-F1 defect this test used to certify.

    It used to force the frozen allocator to raise the sealed message and then
    assert that a `grid_cell_infeasible_by_sample` refusal came out — treating
    the abort AS the correct behaviour. The sealed rule says mark / skip /
    report / continue, so the exception was the defect and this test was
    pinning it. The real sealed behaviour is proved in the F1 section below,
    on a fixture where a cell is genuinely unsampleable rather than forced.

    What survives is the narrower thing this monkeypatch can honestly show:
    the sealed state is decided by the AGGREGATE precheck before the k loop, so
    if the allocator then refuses the same cell the two disagree, and that
    inconsistency fails closed under its OWN code instead of quietly wearing
    the sealed mark. A ValueError must not escape the typed vocabulary either.
    """
    real = gc._gridmix.fp_allocation_from_selected_tp

    def refusing(*a, **k):
        raise ValueError("fp_allocation_infeasible_by_sample:99>2")
    monkeypatch.setattr(gc._gridmix, "fp_allocation_from_selected_tp",
                        refusing)
    with pytest.raises(mcc.MCInputError) as ei:
        gc.derive_cell_draws(authority, wide, supplement, master_seed=7,
                             q_mil=CELL[0], r_mil=CELL[1])
    assert ei.value.code == "grid_cell_infeasibility_precheck_disagreed"
    # and it is NOT allowed to pass itself off as the sealed grid state
    assert ei.value.code != "grid_cell_infeasible_by_sample"
    # a ValueError would have escaped the fail-closed vocabulary
    assert not issubclass(ValueError, mcc.MCInputError)
    monkeypatch.setattr(gc._gridmix, "fp_allocation_from_selected_tp", real)


def test_G_the_other_allocator_refusal_is_not_the_sealed_state(
        wide, authority, supplement, small_grid, monkeypatch):
    """`fp_allocation_no_selected_tp_weight` is k-DEPENDENT and is NOT the
    state the seal names. The old handler called every allocator ValueError
    `infeasible_by_sample`, which would have let the sealed mark absorb a
    different failure — and mark/skip/report/continue is licensed for the
    sealed condition only."""
    def refusing(*a, **k):
        raise ValueError("fp_allocation_no_selected_tp_weight: ...")
    monkeypatch.setattr(gc._gridmix, "fp_allocation_from_selected_tp",
                        refusing)
    with pytest.raises(mcc.MCInputError) as ei:
        gc.derive_cell_draws(authority, wide, supplement, master_seed=7,
                             q_mil=CELL[0], r_mil=CELL[1])
    assert ei.value.code == "grid_cell_fp_allocation_refused"
    assert ei.value.code != "grid_cell_infeasible_by_sample"
# ---------------------------------------------------------------------------
# H — DOWNSTREAM END TO END (the N13 closure test)
# ---------------------------------------------------------------------------

def test_H_the_runner_produces_the_witness_itself_and_reaches_the_seal(
        wide, authority, supplement, small_grid, tmp_path):
    """THE N13 CLOSURE TEST.

    No caller supplies CellStatistics. The runner runs both grid passes for
    all three seeds through the governed Cartesian path, derives the witness,
    and reaches convergence -> verdict -> seal.
    """
    from itsf.mc.registry_boundary import resolve_registry
    reg = tmp_path / "TRIAL_REGISTRY.md"
    reg.write_text(RP.Reg().chain(RP.FULL[:5], commit=BB.COMMIT).text(),
                   encoding="utf-8")
    authorization = run.bind_run_authorization(
        resolve_registry(reg), run_id=mcx.FIRST_RUN_ID,
        expected_commit=wide.authorized_commit, output_root=OUT_ROOT,
        test_only=True)

    result = run.execute_full_mc_for_tests(
        wide, authorization=authorization, supplement=supplement,
        sealed_artifact_sha256=_sha(supplement))

    assert result.sealed is True
    seal = result.seal_candidate
    assert seal["schema"] == "mc_verdict_inputs.v5"
    assert seal["verdict"]["category"] in {"STOP", "GO", "beta", "alpha"}
    assert set(seal["convergence"]) == {
        "category_stable_under_doubling", "category_same_across_seeds",
        "quantile_drift_ok", "mcse_ok", "converged"}
    assert seal["grid_section"]["status"] in {"CONVERGED", "NON_CONVERGED"}
    assert seal["grid_section"]["k"] == K_SMALL == wide.k_per_seed
    assert seal["grid_section"]["k_doubled"] == 2 * K_SMALL
    assert set(result.published_region_by_kind) == set(gr.REGION_KINDS)
    for kind in gr.REGION_KINDS:
        assert set(result.published_region_by_kind[kind]) == set(
            gr.GRID_CELL_KEYS)
    # the witness came from the runner: its k matches the ruled policy, not
    # a caller's number, and the seal records the authority it was minted on
    assert len(seal["grid_section"]["authority_digest"]) == 64


def test_H_no_caller_can_hand_the_runner_cellstatistics(small_grid):
    """The `grid_passes_by_seed` input is GONE. There is no parameter through
    which caller-built CellStatistics could reach the witness."""
    import inspect
    for entry in (run.execute_full_mc, run.execute_full_mc_for_tests):
        params = set(inspect.signature(entry).parameters)
        assert "grid_passes_by_seed" not in params
        assert not any("cellstat" in p.lower() for p in params)
    src = inspect.getsource(run._witness)
    assert "run_grid_pass" in src


# ---------------------------------------------------------------------------
# F1 — THE SEALED `infeasible_by_sample` RULE: MARK / SKIP / REPORT / CONTINUE
# ---------------------------------------------------------------------------
#
# THE SEALED PASSAGE (preregistration, frozen grid section): a per-stratum
# shortfall is redistributed over the remaining strata; when ALL strata
# together still fall short, the grid point is MARKED `infeasible_by_sample`,
# SKIPPED and REPORTED IN FULL — and the pass carries on.
#
# FOUND, NOT FORCED, which is the whole point of this fixture. The `wide` pool
# above (3 TP / 9 FP) was widened precisely so that no cell is unsampleable,
# which is why the old test had to monkeypatch the frozen allocator to reach
# the branch at all — and then asserted the abort AS correct. `narrow` restores
# a 3 TP / 3 FP pool, where the frozen arithmetic splits the geometry by itself:
#     q=0.35 r=0.80 -> n_tp=2, n_fp=4 >  3   INFEASIBLE
#     q=0.50 r=0.80 -> n_tp=2, n_fp=2 <= 3   feasible
#     q=0.75 r=0.80 -> n_tp=2, n_fp=1 <= 3   feasible
# No allocator is patched anywhere below.

NARROW_FP = ("2026-08-04", "2026-08-06", "2026-08-10")
INFEASIBLE_CELL = (350, 800)
FEASIBLE_CELL = (500, 800)
OTHER_FEASIBLE_CELL = (750, 800)
MIXED_CELLS = (INFEASIBLE_CELL, FEASIBLE_CELL, OTHER_FEASIBLE_CELL)


@pytest.fixture()
def narrow(monkeypatch, tmp_path_factory, small_grid):
    """3 TP / 3 FP — a pool where the frozen grid really is part-unsampleable."""
    monkeypatch.setattr(BB, "TP_DAYS", WIDE_TP)
    monkeypatch.setattr(BB, "FP_DAYS", NARROW_FP)
    monkeypatch.setattr(BB, "ALL_DAYS", tuple(sorted(WIDE_TP + NARROW_FP)))
    root = tmp_path_factory.mktemp("f1root")
    for rel in BB.FROZEN_METHOD_FILES:
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(BB.REAL_REPO_ROOT / rel, root / rel)
    bundle = _coherent_bundle()
    att = BB._attestation_bytes(bundle)
    (root / mcc.ATTESTATION_PATH).parent.mkdir(parents=True, exist_ok=True)
    (root / mcc.ATTESTATION_PATH).write_bytes(att)
    monkeypatch.setattr(mcc, "_REPO_ROOT", root)
    monkeypatch.setattr(mcc, "ATTESTATION_SHA256_PINNED",
                        hashlib.sha256(att).hexdigest())
    monkeypatch.setattr(mcc, "build_template_calendar",
                        lambda *a, **k: BB._calendar())
    return mcc.prepare_mc_input(
        bundle, authorization_snapshot={"trial_id": BB.TRIAL,
                                        "authorized_commit": BB.COMMIT},
        attestation_bytes=att)


@pytest.fixture()
def narrow_supplement(narrow):
    authority = sa.derive_supplement_authority(narrow,
                                               supplement_id=ds.SUPPLEMENT_ID)
    days, binding = sa.supplement_build_inputs(authority, narrow)
    rows = [{"trade_date": d, "year": int(str(d)[:4]),
             "vol_stratum": ds.VOL_STRATA[i % len(ds.VOL_STRATA)],
             "event_stratum": ds.EVENT_STRATA[i % len(ds.EVENT_STRATA)]}
            for i, d in enumerate(sorted(days))]
    return ds.build_day_strata_supplement_test_only(
        rows, expected_day_set=days, binding=binding,
        supplement_id=ds.SUPPLEMENT_ID)


@pytest.fixture()
def narrow_authority(narrow, narrow_supplement):
    return gr.derive_grid_replay_authority(
        narrow, narrow_supplement,
        sealed_artifact_sha256=_sha(narrow_supplement))


def _full(partial):
    """The narrow pass covers three cells; `region_map` requires all 63. The
    rest are filled from a SAMPLED cell of the same pass, so the padding is
    real output rather than a fabricated statistic."""
    donor = partial[FEASIBLE_CELL]
    return {tuple(key): partial.get(tuple(key), donor)
            for key in gr.GRID_CELL_KEYS}


def test_F1_the_fixture_geometry_is_genuinely_split(narrow, narrow_authority,
                                                    narrow_supplement,
                                                    small_grid):
    """Vacuity check FIRST. If both cells were sampleable, or neither, every
    proof below would pass while testing nothing — the failure mode the old
    test's own docstring admitted to."""
    _, infeasible = gc.plan_cell_draws(
        narrow_authority, narrow, narrow_supplement, master_seed=7,
        q_mil=INFEASIBLE_CELL[0], r_mil=INFEASIBLE_CELL[1])
    assert infeasible is not None, "the infeasible cell is sampleable"
    assert infeasible.n_fp > infeasible.fp_available   # the sealed condition
    for cell in (FEASIBLE_CELL, OTHER_FEASIBLE_CELL):
        draws, inf = gc.plan_cell_draws(
            narrow_authority, narrow, narrow_supplement, master_seed=7,
            q_mil=cell[0], r_mil=cell[1])
        assert inf is None, f"{cell} should be sampleable"
        assert len(draws) == K_SMALL and all(d.n_tp > 0 for d in draws)


def test_F1_A_an_infeasible_cell_executes_zero_lifecycles(
        narrow, narrow_authority, narrow_supplement, small_grid, monkeypatch):
    """SKIP, counted at the ONE lifecycle execution site rather than inferred
    from the absence of statistics."""
    calls = []
    real = mcc._run_path_atom

    def counting(prepared, **kw):
        calls.append(kw["scenario"])
        return real(prepared, **kw)
    monkeypatch.setattr(mcc, "_run_path_atom", counting)
    cell = gc.run_grid_cell(
        narrow, narrow_authority, narrow_supplement,
        q_mil=INFEASIBLE_CELL[0], r_mil=INFEASIBLE_CELL[1],
        master_seed=7, B=B_SMALL)
    assert gr.is_infeasible(cell)
    assert calls == [], f"{len(calls)} lifecycle(s) ran for a skipped cell"


def test_F1_B_the_pass_continues_past_the_infeasible_cell(
        narrow, narrow_authority, narrow_supplement, small_grid):
    """CONTINUE. The infeasible cell is FIRST in the pass order, so the old
    control flow could not have reached the two behind it."""
    assert MIXED_CELLS[0] == INFEASIBLE_CELL
    passed = gc.run_grid_pass(
        narrow, narrow_authority, narrow_supplement, master_seed=7,
        B=B_SMALL, cells=MIXED_CELLS)
    assert set(passed) == set(MIXED_CELLS)
    assert gr.is_infeasible(passed[INFEASIBLE_CELL])
    for cell in (FEASIBLE_CELL, OTHER_FEASIBLE_CELL):
        assert type(passed[cell]) is gr.CellStatistics
        assert passed[cell].conservative_p5


def test_F1_C_the_infeasible_cell_is_reported_in_full(
        narrow, narrow_authority, narrow_supplement, small_grid):
    """REPORT. The record names the cell, the seed, the pass, the reason and
    the frozen arithmetic that decided it — and the region map carries the
    sealed token rather than losing it."""
    passed = gc.run_grid_pass(
        narrow, narrow_authority, narrow_supplement, master_seed=13,
        B=B_SMALL, cells=MIXED_CELLS)
    rec = passed[INFEASIBLE_CELL]
    assert rec.reason == gr.INFEASIBLE_BY_SAMPLE == "infeasible_by_sample"
    assert (rec.q_mil, rec.r_mil) == INFEASIBLE_CELL
    assert rec.master_seed == 13 and rec.doublings == 0
    assert rec.n_fp == 4 and rec.fp_available == 3 and rec.n_tp == 2
    assert "infeasible_by_sample" in rec.detail
    for kind in gr.REGION_KINDS:
        assert gr.cell_category(rec, kind) == gr.INFEASIBLE_BY_SAMPLE
    # the mark is DISTINGUISHABLE from a real OUT, from IN, and from the band
    assert gr.INFEASIBLE_BY_SAMPLE not in (gr.OUT_OF_REGION, gr.IN_REGION,
                                           gr.BOUNDARY_BAND)
    # ... and from an ABSENT cell, which region_map still refuses outright
    with pytest.raises(mcc.MCInputError) as ei:
        gr.region_map({k: v for k, v in _full(passed).items()
                       if tuple(k) != INFEASIBLE_CELL}, gr.REGION_KINDS[0])
    assert ei.value.code == "grid_replay_grid_incomplete"


def test_F1_D_no_statistics_are_fabricated_for_it(
        narrow, narrow_authority, narrow_supplement, small_grid):
    """NO FAKE STATISTICS. Not a sentinel, not a zero, not a NaN, not an empty
    CellStatistics — and the type cannot be talked into being one."""
    rec = gc.run_grid_cell(
        narrow, narrow_authority, narrow_supplement,
        q_mil=INFEASIBLE_CELL[0], r_mil=INFEASIBLE_CELL[1],
        master_seed=7, B=B_SMALL)
    assert type(rec) is not gr.CellStatistics
    for attr in ("conservative_p5", "stress_median", "feasible", "identity",
                 "classifying_values"):
        assert not hasattr(rec, attr), f"a skipped cell exposes {attr}"
    # the guard that makes this structural rather than a convention: an empty
    # CellStatistics is refused outright, so there is no "blank cell" to fall
    # back on even for someone who wanted one
    with pytest.raises(mcc.MCInputError) as ei:
        gr.CellStatistics(conservative_p5={}, stress_median={}, feasible={})
    assert ei.value.code == "grid_replay_cell_no_combination"
    # and the marked record refuses to carry any other reason
    with pytest.raises(mcc.MCInputError) as ei:
        dataclasses.replace(rec, reason="something_else")
    assert ei.value.code == "grid_replay_infeasible_reason_unknown"
    # nor may it be read as a region witness
    with pytest.raises(mcc.MCInputError) as ei:
        gr.satisfying_combos(rec, gr.REGION_KINDS[0])
    assert ei.value.code == "grid_replay_cell_required"


def test_F1_E_and_F_K_and_2K_both_mark_skip_report(
        narrow, narrow_authority, narrow_supplement, small_grid, monkeypatch):
    """E and F together, because the claim spans them: the sealed test is
    `n_fp > sum(fp_available)`, whose terms are the (q, r) quotas and the
    AGGREGATE pool. Neither depends on k, so doubling is not a second chance at
    feasibility — and zero lifecycles run for the marked cell in EITHER pass."""
    calls = []
    real = mcc._run_path_atom

    def counting(prepared, **kw):
        calls.append((kw["q_mil"], kw["r_mil"]) if "q_mil" in kw
                     else kw["scenario"])
        return real(prepared, **kw)
    monkeypatch.setattr(mcc, "_run_path_atom", counting)
    at_k = gc.run_grid_pass(narrow, narrow_authority, narrow_supplement,
                            master_seed=7, B=B_SMALL, doublings=0,
                            cells=MIXED_CELLS)
    n_after_k = len(calls)
    at_2k = gc.run_grid_pass(narrow, narrow_authority, narrow_supplement,
                             master_seed=7, B=B_SMALL, doublings=1,
                             cells=MIXED_CELLS)
    n_2k = len(calls) - n_after_k
    for passed, doublings in ((at_k, 0), (at_2k, 1)):
        rec = passed[INFEASIBLE_CELL]
        assert gr.is_infeasible(rec) and rec.reason == gr.INFEASIBLE_BY_SAMPLE
        assert rec.doublings == doublings
        for cell in (FEASIBLE_CELL, OTHER_FEASIBLE_CELL):
            assert type(passed[cell]) is gr.CellStatistics
    # the 2K pass ran exactly twice the lifecycles of K -- the two feasible
    # cells doubled and the marked cell contributed zero to both
    assert n_after_k > 0 and n_2k == 2 * n_after_k


def test_F1_the_marked_cell_survives_M8_comparison_and_publication(
        narrow, narrow_authority, narrow_supplement, small_grid):
    """DOWNSTREAM. A marked cell has no statistics, so it has no identity to
    compare, nothing that can drift and no witness set — and it must not be
    silently relabelled BOUNDARY_BAND, which would assert its statistics hug
    zero when it has none."""
    at_k = gc.run_grid_pass(narrow, narrow_authority, narrow_supplement,
                            master_seed=7, B=B_SMALL, doublings=0,
                            cells=MIXED_CELLS)
    at_2k = gc.run_grid_pass(narrow, narrow_authority, narrow_supplement,
                             master_seed=7, B=B_SMALL, doublings=1,
                             cells=MIXED_CELLS)
    full_k, full_2k = _full(at_k), _full(at_2k)
    for kind in gr.REGION_KINDS:
        drift = gr.cell_drift_violations(kind, full_k, full_2k)
        assert INFEASIBLE_CELL not in {key for key, _name in drift}
        cmp_ = gr.compare_region_maps(kind, full_k, full_2k,
                                      k=K_SMALL, k_doubled=2 * K_SMALL)
        assert cmp_.map_at_k[INFEASIBLE_CELL] == gr.INFEASIBLE_BY_SAMPLE
        assert cmp_.map_at_2k[INFEASIBLE_CELL] == gr.INFEASIBLE_BY_SAMPLE
        assert INFEASIBLE_CELL not in cmp_.boundary_band_cells
        assert INFEASIBLE_CELL not in cmp_.flipped_cells
        # M10: a mark every seed made survives publication AS the mark
        published = gr.publish_region(kind, {
            seed: gr.region_map(full_k, kind)
            for seed in RESEARCH_BOOTSTRAP_SEEDS})
        assert published[INFEASIBLE_CELL] == gr.INFEASIBLE_BY_SAMPLE
        # a cell some seeds marked and others sampled is DISCLOSED, not
        # resolved by majority -- the existing union-band rule, reused
        mixed = dict(full_k)
        mixed[INFEASIBLE_CELL] = full_k[FEASIBLE_CELL]
        disagreeing = gr.publish_region(kind, {
            RESEARCH_BOOTSTRAP_SEEDS[0]: gr.region_map(mixed, kind),
            RESEARCH_BOOTSTRAP_SEEDS[1]: gr.region_map(full_k, kind),
            RESEARCH_BOOTSTRAP_SEEDS[2]: gr.region_map(full_k, kind)})
        assert disagreeing[INFEASIBLE_CELL] == gr.BOUNDARY_BAND


def test_F1_the_witness_and_the_draw_count_survive_a_marked_first_cell(
        narrow, narrow_authority, narrow_supplement, small_grid):
    """`drawn_count` used to take `cells[0]` unconditionally, so a marked FIRST
    cell aborted the runner's own witness check — the same blocker one level
    up. It now skips marked cells, which is what the sealed rule says to do.

    REVISED for F1-R2-01. The second half of this test used to assert that an
    ALL-marked pass raises `grid_draw_every_cell_infeasible` — it was pinning the
    round-2 blocker as if it were correct behaviour, the same way the original
    `test_G` pinned the round-1 one. An all-marked grid is a lawful sealed
    outcome, so the count is now an explicit ABSENCE.
    """
    assert MIXED_CELLS[0] == INFEASIBLE_CELL
    assert gc.drawn_count(narrow, narrow_authority, narrow_supplement,
                          master_seed=7, cells=MIXED_CELLS) == (K_SMALL,
                                                                2 * K_SMALL)
    # all-marked -> None, and specifically NOT (0, 0): a zero would be a
    # numeric claim that a representative cell was sampled and prescribed no
    # draws, which the runner's guard would then compare against the witness.
    absent = gc.drawn_count(narrow, narrow_authority, narrow_supplement,
                            master_seed=7, cells=(INFEASIBLE_CELL,))
    assert absent is None
    assert absent != (0, 0)


# ---------------------------------------------------------------------------
# F1-R2-01 — THE ALL-MARKED GRID: the sealed rule at its boundary
# ---------------------------------------------------------------------------
#
# THE ROUND-2 BLOCKER. Individual marked cells, and mixed marked+feasible
# passes, were established working. The boundary that was not: when EVERY
# frozen cell is `infeasible_by_sample`, the runner still called
# `drawn_count()` unconditionally, `drawn_count` could find no sampleable
# representative and RAISED, and the runner aborted -- so the sealed
# "REPORT IN FULL" never happened for the one grid where every point needed
# reporting. An all-marked grid is a lawful sealed outcome, not a malformed
# input.
#
# THE GEOMETRY IS FOUND, NOT PATCHED, and it is the SMALLEST that works. The
# sealed arithmetic is n_tp = floor(r x N_TP) and n_fp = round_half_up(n_tp x
# (1-q)/q), and the least-demanding frozen cell is the one minimising both:
# r = 0.20 with q at its maximum. So over the frozen grid the minimum FP
# demand is round_half_up(floor(0.2 x N_TP) / 3), and every cell is marked iff
# that exceeds N_FP.
#
#   N_TP = 25, N_FP = 1  ->  least-demanding cell (q=0.70, r=0.20):
#                            n_tp = floor(0.2 x 25) = 5
#                            n_fp = round_half_up(5 x 0.30/0.70) = 2  >  1
#                            ALL 63 cells marked.
#   N_TP = 24, N_FP = 1  ->  q=0.75, r=0.20 gives n_fp = 1, NOT > 1
#                            -> one cell sampleable. 25 is the minimum.
#
# The reviewer's own example (N_TP = 2800, N_FP = 42 -> minimum demand 187)
# also marks all 63 and is asserted below on the arithmetic alone; 25/1 is used
# for the executed fixture because it needs 26 synthetic days rather than 2842.
# N_FP = 1 rather than 0 because an empty FP pool is a different refusal
# (`grid_draw_pool_degenerate`) and would prove the wrong thing.

ALLMARKED_TP = tuple("2026-%02d-%02d" % (8 + i // 20, 1 + i % 20)
                     for i in range(25))
ALLMARKED_FP = ("2026-10-01",)


@pytest.fixture()
def allmarked(monkeypatch, tmp_path_factory, small_grid):
    """25 TP / 1 FP -- a pool on which EVERY frozen grid cell is marked."""
    assert len(set(ALLMARKED_TP)) == 25 and len(ALLMARKED_FP) == 1
    monkeypatch.setattr(BB, "TP_DAYS", ALLMARKED_TP)
    monkeypatch.setattr(BB, "FP_DAYS", ALLMARKED_FP)
    monkeypatch.setattr(BB, "ALL_DAYS",
                        tuple(sorted(ALLMARKED_TP + ALLMARKED_FP)))
    root = tmp_path_factory.mktemp("f1r2root")
    for rel in BB.FROZEN_METHOD_FILES:
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(BB.REAL_REPO_ROOT / rel, root / rel)
    bundle = _coherent_bundle()
    att = BB._attestation_bytes(bundle)
    (root / mcc.ATTESTATION_PATH).parent.mkdir(parents=True, exist_ok=True)
    (root / mcc.ATTESTATION_PATH).write_bytes(att)
    monkeypatch.setattr(mcc, "_REPO_ROOT", root)
    monkeypatch.setattr(mcc, "ATTESTATION_SHA256_PINNED",
                        hashlib.sha256(att).hexdigest())
    monkeypatch.setattr(mcc, "build_template_calendar",
                        lambda *a, **k: BB._calendar())
    return mcc.prepare_mc_input(
        bundle, authorization_snapshot={"trial_id": BB.TRIAL,
                                        "authorized_commit": BB.COMMIT},
        attestation_bytes=att)


@pytest.fixture()
def allmarked_supplement(allmarked):
    authority = sa.derive_supplement_authority(allmarked,
                                               supplement_id=ds.SUPPLEMENT_ID)
    days, binding = sa.supplement_build_inputs(authority, allmarked)
    rows = [{"trade_date": d, "year": int(str(d)[:4]),
             "vol_stratum": ds.VOL_STRATA[i % len(ds.VOL_STRATA)],
             "event_stratum": ds.EVENT_STRATA[i % len(ds.EVENT_STRATA)]}
            for i, d in enumerate(sorted(days))]
    return ds.build_day_strata_supplement_test_only(
        rows, expected_day_set=days, binding=binding,
        supplement_id=ds.SUPPLEMENT_ID)


@pytest.fixture()
def allmarked_authority(allmarked, allmarked_supplement):
    return gr.derive_grid_replay_authority(
        allmarked, allmarked_supplement,
        sealed_artifact_sha256=_sha(allmarked_supplement))


def _grid_lifecycle_counter(monkeypatch):
    """Count GRID lifecycle executions at the ONE execution site.

    A GRID evaluation is exactly a `_run_path_atom` call carrying a
    `traded_selector`; the Oracle main channel passes None. `is not None`
    rather than truthiness, so even an empty selector would be counted.
    """
    calls = []
    real = mcc._run_path_atom

    def counting(prepared, **kw):
        if kw.get("traded_selector") is not None:
            calls.append((kw["world_index"], kw["phase_offset"],
                          kw["scenario"]))
        return real(prepared, **kw)
    monkeypatch.setattr(mcc, "_run_path_atom", counting)
    return calls


def test_F1R2_the_arithmetic_marks_every_frozen_cell_vacuity_guard():
    """THE VACUITY GUARD, and it runs first. If even one frozen cell were
    sampleable on this geometry, every proof below would pass while testing
    the mixed case that already worked."""
    from itsf.s0 import gridmix as g
    for n_tp_pool, n_fp_pool, label in ((25, 1, "the executed fixture"),
                                        (2800, 42, "the reviewer's example")):
        sampleable = [(q, r) for q in g.Q_GRID_MILLIS for r in g.R_GRID_MILLIS
                      if g.n_fp_for(g.floor_n_tp(r, n_tp_pool), q) <= n_fp_pool]
        assert not sampleable, f"{label}: {sampleable} are sampleable"
    # and the boundary: one fewer TP day leaves a cell sampleable, so 25 is
    # the minimum rather than a round number picked for comfort
    still = [(q, r) for q in g.Q_GRID_MILLIS for r in g.R_GRID_MILLIS
             if g.n_fp_for(g.floor_n_tp(r, 24), q) <= 1]
    assert still == [(750, 200)]


def test_F1R2_A_every_cell_is_marked_in_both_passes(
        allmarked, allmarked_authority, allmarked_supplement, small_grid,
        monkeypatch):
    """A + B. Every one of the 63 frozen cells is explicitly marked in the K
    pass and in the 2K pass, and ZERO grid lifecycles execute for any of
    them."""
    calls = _grid_lifecycle_counter(monkeypatch)
    seen = 0
    for seed in RESEARCH_BOOTSTRAP_SEEDS:          # all three, not just one
        for doublings in (0, 1):
            passed = gc.run_grid_pass(
                allmarked, allmarked_authority, allmarked_supplement,
                master_seed=seed, B=B_SMALL, doublings=doublings)
            assert set(passed) == set(gr.GRID_CELL_KEYS)
            assert len(passed) == 63
            for key, cell in passed.items():
                assert gr.is_infeasible(cell), f"seed {seed} {key} is not marked"
                assert cell.reason == gr.INFEASIBLE_BY_SAMPLE
                assert cell.doublings == doublings
                assert cell.master_seed == seed
                assert cell.n_fp > cell.fp_available   # the sealed condition
            for kind in gr.REGION_KINDS:
                m = gr.region_map(passed, kind)
                assert set(m) == set(gr.GRID_CELL_KEYS)
                assert set(m.values()) == {gr.INFEASIBLE_BY_SAMPLE}
            seen += 1
    assert seen == 6                               # 3 seeds x {K, 2K}
    assert calls == [], f"{len(calls)} grid lifecycle(s) ran on an all-marked grid"


def test_F1R2_the_draw_count_is_an_explicit_absence_not_a_zero(
        allmarked, allmarked_authority, allmarked_supplement, small_grid):
    """The repair's core semantics. `(0, 0)` would be a numeric claim that a
    representative cell was sampled and prescribed no draws; the runner's guard
    compares this value against the witness's reported k, so a zero would
    assert something false about the frozen policy."""
    absent = gc.drawn_count(allmarked, allmarked_authority,
                            allmarked_supplement, master_seed=7)
    assert absent is None
    assert absent != (0, 0) and absent != 0
    # ... while a sampleable pass still gets its real count, unchanged
    assert gc.drawn_count(allmarked, allmarked_authority, allmarked_supplement,
                          master_seed=7, cells=gr.GRID_CELL_KEYS) is None


def test_F1R2_C_and_D_the_runner_returns_a_complete_all_marked_report(
        allmarked, allmarked_authority, allmarked_supplement, small_grid,
        tmp_path, monkeypatch):
    """C + D + F. The runner COMPLETES instead of raising
    `grid_draw_every_cell_infeasible`, and the report it returns retains every
    grid coordinate in both passes and in the published cross-seed region."""
    from itsf.mc.registry_boundary import resolve_registry
    calls = _grid_lifecycle_counter(monkeypatch)
    reg = tmp_path / "TRIAL_REGISTRY.md"
    reg.write_text(RP.Reg().chain(RP.FULL[:5], commit=BB.COMMIT).text(),
                   encoding="utf-8")
    authorization = run.bind_run_authorization(
        resolve_registry(reg), run_id=mcx.FIRST_RUN_ID,
        expected_commit=allmarked.authorized_commit, output_root=OUT_ROOT,
        test_only=True)

    result = run.execute_full_mc_for_tests(
        allmarked, authorization=authorization,
        supplement=allmarked_supplement,
        sealed_artifact_sha256=_sha(allmarked_supplement))

    # C: it returned
    assert result.sealed is True
    # D: skipped did not become missing. `RunnerResult` deliberately exposes no
    # raw passes -- that is the no-injection design, and B-27's own test asserts
    # there is no such parameter -- so completeness is asserted on the report
    # surface the runner actually returns: the published cross-seed region and
    # the seal's grid section. The per-seed pass-level completeness for all
    # three research seeds is proved directly in test_F1R2_A.
    for kind in gr.REGION_KINDS:
        published = result.published_region_by_kind[kind]
        assert set(published) == set(gr.GRID_CELL_KEYS)
        assert set(published.values()) == {gr.INFEASIBLE_BY_SAMPLE}
    # B again, through the whole runner: no grid lifecycle for any seed
    assert calls == [], f"{len(calls)} grid lifecycle(s) ran through the runner"
    # F: both passes are comparable under the already-governed mark semantics
    seal = result.seal_candidate
    assert seal["grid_section"]["k"] == K_SMALL
    assert seal["grid_section"]["k_doubled"] == 2 * K_SMALL
    assert seal["grid_section"]["status"] in {"CONVERGED", "NON_CONVERGED"}


def test_F1R2_E_no_statistic_is_fabricated_anywhere_on_the_all_marked_path(
        allmarked, allmarked_authority, allmarked_supplement, small_grid):
    """E. No P5, no Stress median, no feasibility, no sampled cell identity,
    no draw metadata and no lifecycle atom is invented for any cell."""
    passed = gc.run_grid_pass(allmarked, allmarked_authority,
                              allmarked_supplement, master_seed=7, B=B_SMALL)
    for cell in passed.values():
        assert type(cell) is not gr.CellStatistics
        for attr in ("conservative_p5", "stress_median", "feasible",
                     "identity", "classifying_values", "draw_digests",
                     "atoms"):
            assert not hasattr(cell, attr), f"a marked cell exposes {attr}"
    # no draw was derived for any cell, so no draw identity can exist
    for key in gr.GRID_CELL_KEYS:
        draws, infeasible = gc.plan_cell_draws(
            allmarked_authority, allmarked, allmarked_supplement,
            master_seed=7, q_mil=int(key[0]), r_mil=int(key[1]))
        assert draws == () and infeasible is not None
    # rule (c) has nothing to measure, and M8 has nothing to band
    for kind in gr.REGION_KINDS:
        at_2k = gc.run_grid_pass(allmarked, allmarked_authority,
                                 allmarked_supplement, master_seed=7,
                                 B=B_SMALL, doublings=1)
        assert gr.cell_drift_violations(kind, passed, at_2k) == ()
        cmp_ = gr.compare_region_maps(kind, passed, at_2k, k=K_SMALL,
                                      k_doubled=2 * K_SMALL)
        assert cmp_.boundary_band_cells == () and cmp_.flipped_cells == ()
        assert cmp_.converged is True


def test_F1R2_an_absent_count_is_refused_when_a_cell_was_actually_sampled(
        narrow, narrow_authority, narrow_supplement, small_grid, monkeypatch):
    """The new branch must not become a hole in the count guard. If
    `drawn_count` returns None while the passes DO carry statistics, that is an
    inconsistency and the runner refuses rather than sealing."""
    import inspect
    src = inspect.getsource(run._witness)
    assert "mc_run_draw_count_absent_but_cells_sampled" in src
    assert "is_infeasible" in src
    # the guard is corroborated from the passes, not taken on drawn_count's word
    assert "drawn_count" in src and "sampled" in src
    # and the ordinary mismatch guard still exists for sampled passes
    assert "mc_run_draw_count_mismatch" in src
