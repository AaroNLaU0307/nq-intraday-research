"""B-27 — the GRID channel: K marker draws x M phases, inside every B world.

THE ADOPTED OWNER RULING this implements, verbatim in substance: the GRID
channel composes K stratified TP/FP marker draws per cell and governed seed
with M exhaustive legal start phases by the FULL CARTESIAN PRODUCT within every
existing B/world. Each draw keeps its marker sequence across phase evaluations.
Every `(world, phase, draw)` contributes exactly once through the governed
lifecycle, on the unchanged prepared population and calendar. The M x K inner
empirical distribution enters the EXISTING within-world reduction, and
Conservative P5 / Stress median come from the UNCHANGED epistemic aggregation
across B worlds -- raw lifecycle outcomes are never pooled across worlds to
redefine those percentiles. Doubling K appends draws and preserves the first K.

WHY NOTHING IN THE ATOM LAYER CHANGED. The reductions are the repository's own
and they take a plain atom sequence: `atoms.reduce_world_means` groups by world
index and averages, and `feasibility._by_world` reads `.atoms`. So the GRID
channel does not add a K FIELD to `SimulationPathObservation` -- it composes
MORE ATOMS (B x M x K instead of B x M) and hands them to the same functions.
MC SS5 keeps K in the grid, `EpistemicResult` / `ObservationSet` /
`SimulationPathObservation` keep no K of their own, and the Oracle main channel
is byte-for-byte the path it always was.

Draw identity therefore lives HERE rather than on the atom: this module keys
every evaluation by `(world_index, phase_offset, draw_index)` and binds the
draw set by digest, which is what makes a lifecycle output attributable to the
draw that produced it.

ONE LIFECYCLE EXECUTION SITE. Every evaluation goes through
`consumer._run_path_atom`, whose docstring is the reason: "THE only place a
lifecycle is executed. The forward run and the cold replay both call this, so a
divergence between them can only come from the inputs." A GRID cell is a
different INPUT -- one `traded_selector` -- and not a different code path.

A DRAW IS A SELECTOR, NOT AN AUTHORITY. `GridDraw` carries the authorized
marker sequence and nothing else that decides anything. No `PreparedMCInput` is
built, copied, narrowed or impersonated; the prepared digest, custody/battery
receipt, day population, calendar, records, world construction and non-GRID
randomness are all untouched, and a selector can only narrow which slots trade
-- `_paths_for_world` still requires a sealed record for every traded slot.

PREFIX NESTING IS THE FROZEN MACHINERY'S, NOT MINE. `gridmix.repeat_k_indices`
grows the k range from a fixed start and `gridmix.repeat_stream_entropy` gives
every k its own stream, which its own docstring says is "what makes the repeat
set prefix-nested under doubling and makes the result independent of the order
in which repeats are visited". This module reuses both rather than re-deriving
either, so K -> 2K nesting is a property of the frozen streams.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from dataclasses import fields as _dc_fields
from types import MappingProxyType
from typing import Mapping

from itsf import contracts as _contracts
from itsf.mc import atoms as _atoms
from itsf.mc import consumer as _mcc
from itsf.mc import day_strata_supplement as _ds
from itsf.mc import feasibility as _fz
from itsf.mc import grid_replay as _gr
from itsf.mc.atoms import MCInputError
from itsf.s0 import gridmix as _gridmix
from itsf.s0 import study as _study

__all__ = ("GRID_DRAW_SCHEMA", "GridDraw", "derive_cell_draws",
           "drawn_count",
           "GridCellEvaluation", "run_grid_cell", "run_grid_pass")

GRID_DRAW_SCHEMA = "mc_grid_draw.v1"
_DRAW_DIGEST_SCHEMA = "mc_grid_draw_digest.v1"

#: Frozen: only the Primary theta channel reaches Checkpoint-0, and the grid's
#: repeat stream includes theta (`gridmix.repeat_stream_entropy`).
PRIMARY_THETA = _study.THETA_PRIMARY


class _DrawCapability:
    """Module-private construction capability — the pattern `BatteryReceipt`,
    `SupplementAuthority` and `KReplayEvidence` already use. A draw a caller
    assembled is not a draw the frozen streams prescribed."""
    __slots__ = ()


_DRAW_CAPABILITY = _DrawCapability()

DRAW_PAYLOAD_FIELDS = ("schema", "authority_digest", "prepared_digest",
                       "theta_channel", "master_seed", "q_mil", "r_mil",
                       "draw_index", "traded_days", "n_tp", "n_fp")


@dataclass(frozen=True, slots=True)
class GridDraw:
    """ONE prescribed marker draw: the trade-slot selector for one
    `(seed, cell, k)`, bound to the authority that licensed grid replay.

    `traded_days` IS the marker sequence -- the selected TP days plus the
    allocated FP days, as sealed-population dates. It is consumed only as
    `_paths_for_world`'s `traded_selector`.

    The draw index is deliberately NOT qualified by which pass produced it.
    The ruling requires the first K draws of a 2K pass to be identical to the
    K pass, so a pass-qualified identity would make shared draws differ and
    break the property it was meant to record. The pass lives on the cell
    evaluation (`n_draws`), where it belongs.
    """
    capability: object
    schema: str
    authority_digest: str
    prepared_digest: str
    theta_channel: str
    master_seed: int
    q_mil: int
    r_mil: int
    draw_index: int
    traded_days: tuple
    n_tp: int
    n_fp: int
    draw_digest: str

    def __post_init__(self):
        if self.capability is not _DRAW_CAPABILITY:
            raise MCInputError(
                "grid_draw_capability_required",
                "GridDraw is factory-only — use derive_cell_draws(); a "
                "hand-built selector is not a prescribed draw")
        object.__setattr__(self, "capability", None)

    @property
    def cell(self) -> tuple:
        return (self.q_mil, self.r_mil)


def _digest(schema: str, payload) -> str:
    return hashlib.sha256(
        _atoms.canonical_json({"schema": schema, "payload": payload})
        .encode("ascii")).hexdigest()


def _draw_payload(draw) -> dict:
    declared = {f.name for f in _dc_fields(draw)} - {"capability",
                                                     "draw_digest"}
    if declared != set(DRAW_PAYLOAD_FIELDS):
        raise MCInputError("grid_draw_payload_field_drift",
                           f"{sorted(declared ^ set(DRAW_PAYLOAD_FIELDS))}")
    out = {}
    for name in DRAW_PAYLOAD_FIELDS:
        value = getattr(draw, name)
        out[name] = list(value) if isinstance(value, tuple) else value
    return out


def verify_draw(draw) -> GridDraw:
    """Re-check a draw's self-digest, so a mutated selector refuses."""
    if type(draw) is not GridDraw:
        raise MCInputError("grid_draw_required",
                           f"{type(draw).__name__} is not a GridDraw")
    expect = _digest(_DRAW_DIGEST_SCHEMA, _draw_payload(draw))
    if draw.draw_digest != expect:
        raise MCInputError(
            "grid_draw_digest_mismatch",
            f"carries {draw.draw_digest[:12]}, its own fields hash to "
            f"{expect[:12]}")
    return draw


# ---------------------------------------------------------------------------
# reconstructing the prescribed draws with the FROZEN gridmix machinery
# ---------------------------------------------------------------------------

def _strata_from_supplement(authority, supplement: Mapping) -> dict:
    """`{date: (year, vol, event)}` from the SEALED supplement, re-bound to
    the authority that licensed it.

    The rows are re-digested and compared with `authority.rows_digest`, so a
    caller cannot license replay with one stratum table and then draw from
    another. This is the only place the supplement's CONTENT is read, and it
    is read for dates and stratum labels — never for an outcome value.
    """
    _gr.verify_grid_replay_authority(authority)
    rows = supplement.get("rows")
    if not isinstance(rows, (list, tuple)) or not rows:
        raise MCInputError("grid_draw_supplement_rows_absent",
                           "the sealed supplement carries no rows")
    if _ds.canonical_rows_digest(rows) != authority.rows_digest:
        raise MCInputError(
            "grid_draw_supplement_rows_digest_mismatch",
            "the supplied stratum table is not the one the authority "
            "licensed — its rows hash to a different digest")
    out = {}
    for row in rows:
        out[str(row["trade_date"])] = (str(row["year"]),
                                       str(row["vol_stratum"]),
                                       str(row["event_stratum"]))
    return out


def plan_cell_draws(authority, prepared, supplement: Mapping, *,
                    master_seed: int, q_mil: int, r_mil: int,
                    doublings: int = 0,
                    channel: str = _mcc.PRIMARY_THETA_CHANNEL) -> tuple:
    """`(draws, None)`, or `((), InfeasibleCell)` for a cell the SEALED rule
    marks and skips. N13-F1.

    THE SEALED RULE, verbatim from the preregistration's frozen grid section:
    「某分层的可用日不足时，缺额按其余层的可用日数比例重新分配；全部层合计仍
    不足时，该网格点标记 `infeasible_by_sample` 跳过并完整报告」— a per-stratum
    shortfall is redistributed; when ALL strata together still fall short, the
    grid point is MARKED, SKIPPED and REPORTED IN FULL.

    So the test is `n_fp > sum(fp_available)`, and it is made HERE, before the
    k loop and before any selection, which is exactly where
    `s0.gridmix._grid_point` makes it one layer down (`if n_fp >
    n_fp_available:` → set the flag, add a reason, return the point). Two
    consequences worth stating because the old code depended on neither:

      * ZERO draws are derived and therefore zero lifecycles can run.
      * The test's terms are the (q, r) quotas and the AGGREGATE pool. Neither
        depends on k, so a cell marked at K is marked at 2K by construction.
        Doubling is not a second chance at feasibility.

    NOT the same thing, and no longer conflated with it: the allocator's other
    fail-closed exit, `fp_allocation_no_selected_tp_weight`, fires when no
    stratum holds a selected TP day. That IS k-dependent, it is not the state
    the seal names, and it keeps a typed refusal. The old handler caught both
    ValueErrors and called them both `infeasible_by_sample`, which would have
    let the sealed mark absorb a genuinely different failure.

    The TP side needs no such test: `floor_n_tp` is `(r_mil * N) // 1000` with
    `r_mil <= 800`, so `n_tp <= N = sum(tp_available)` always. Asserting an
    unreachable branch would only make the reachable one harder to read.
    """
    draws, infeasible = _plan(authority, prepared, supplement,
                              master_seed=master_seed, q_mil=q_mil,
                              r_mil=r_mil, doublings=doublings,
                              channel=channel)
    return (draws, infeasible)


def derive_cell_draws(authority, prepared, supplement: Mapping, *,
                      master_seed: int, q_mil: int, r_mil: int,
                      doublings: int = 0,
                      channel: str = _mcc.PRIMARY_THETA_CHANNEL) -> tuple:
    """The prescribed draws for one `(seed, cell)`, in frozen k order.

    `doublings=0` gives draws k = start .. start+K-1; `doublings=1` gives
    start .. start+2K-1, whose first K entries are the SAME draws, because
    `repeat_k_indices` only grows the range and each k has its own stream.
    Nothing here re-derives that property; it is inherited.

    The selection sequence is `gridmix`'s own, in its order: TP quotas from
    the frozen allocator, TP dates drawn on this k's stream, the DR-3 FP
    allocation from the SELECTED TP composition, then FP dates on the same
    stream. Reproducing that order matters — the two `_select` calls share
    one Generator, so re-ordering them would change every draw.

    STRICT: an unsampleable cell raises here rather than returning zero draws,
    so a direct caller cannot mistake "the seal skipped this cell" for "this
    cell has no draws". The mark/skip/report path is `plan_cell_draws`, and
    `run_grid_cell` is what takes it.
    """
    draws, infeasible = _plan(authority, prepared, supplement,
                              master_seed=master_seed, q_mil=q_mil,
                              r_mil=r_mil, doublings=doublings,
                              channel=channel)
    if infeasible is not None:
        raise MCInputError("grid_cell_infeasible_by_sample", infeasible.detail)
    return draws


def _plan(authority, prepared, supplement: Mapping, *,
          master_seed: int, q_mil: int, r_mil: int, doublings: int,
          channel: str) -> tuple:
    """The one implementation behind `plan_cell_draws` and
    `derive_cell_draws`, so the two cannot disagree about a cell."""
    if not isinstance(prepared, _mcc.PreparedMCInput):
        raise MCInputError("grid_draw_prepared_input_required",
                           f"{type(prepared).__name__} is not a "
                           "PreparedMCInput")
    if authority.prepared_digest != _mcc.prepared_digest(prepared):
        raise MCInputError(
            "provenance_mismatch",
            "the grid authority was minted over a different prepared input")
    methods = _contracts.aaron_ruled_methods()
    policy, fp_allocation = methods.grid_policy, methods.fp_allocation
    strata = _strata_from_supplement(authority, supplement)

    population = tuple(prepared.day_sequences[channel])
    oracle_tp = set(prepared.traded_day_sets[channel])
    missing = [d for d in population if d not in strata]
    if missing:
        raise MCInputError(
            "grid_draw_stratum_absent",
            f"{len(missing)} population day(s) have no stratum in the sealed "
            f"table: {missing[:3]}")
    tp_days = {d: 0.0 for d in population if d in oracle_tp}
    fp_days = {d: 0.0 for d in population if d not in oracle_tp}
    if not tp_days or not fp_days:
        raise MCInputError(
            "grid_draw_pool_degenerate",
            f"TP pool {len(tp_days)}, FP pool {len(fp_days)} — a cell draw "
            "needs both, and an empty side is a sealed-input problem rather "
            "than something to sample around")

    tp_pools = _gridmix._pools(tp_days, strata)
    fp_pools = _gridmix._pools(fp_days, strata)
    tp_avail = {k: len(v) for k, v in tp_pools.items()}
    fp_avail = {k: len(v) for k, v in fp_pools.items()}
    n_tp = _gridmix.floor_n_tp(int(r_mil), len(tp_days))
    n_fp = _gridmix.n_fp_for(n_tp, int(q_mil))

    # THE SEALED TEST — 「全部层合计仍不足时」. Before the k loop, before any
    # allocation, before any selection: mark, skip, report. See this function's
    # sibling docstring for why it belongs here and why it is k-independent.
    fp_total = sum(fp_avail.values())
    if n_fp > fp_total:
        return (), _gr.InfeasibleCell(
            reason=_gr.INFEASIBLE_BY_SAMPLE,
            q_mil=int(q_mil), r_mil=int(r_mil),
            master_seed=int(master_seed), doublings=int(doublings),
            n_tp=int(n_tp), n_fp=int(n_fp), fp_available=int(fp_total),
            detail=(f"cell (q_mil={q_mil}, r_mil={r_mil}) seed {master_seed}: "
                    f"n_fp target {n_fp} exceeds D_FP availability "
                    f"{fp_total} across all strata — marked "
                    f"{_gr.INFEASIBLE_BY_SAMPLE}, skipped and reported per "
                    "the sealed grid rule"))

    tp_alloc = _gridmix.allocate(n_tp, tp_avail)
    tp_keys = tuple(sorted(tp_pools))
    # `_selected_tp_composition` takes a MAPPING date -> stratum key
    stratum_of_date = {d: _gridmix._stratum_key(strata[d]) for d in population}

    draws = []
    for k in _gridmix.repeat_k_indices(policy, doublings=int(doublings)):
        rng = _gridmix.repeat_rng(int(master_seed), PRIMARY_THETA,
                                  int(q_mil), int(r_mil), k, policy)
        tp_dates = _gridmix._select(tp_pools, tp_alloc, rng)
        selected_tp = _gridmix._selected_tp_composition(
            tp_dates, stratum_of_date, tp_keys)
        try:
            fp_block = _gridmix.fp_allocation_from_selected_tp(
                n_fp, selected_tp, fp_avail, fp_allocation)
        except ValueError as exc:
            # N13-F1 separated two failures the old handler merged.
            #
            # The sealed `infeasible_by_sample` state is decided ABOVE, before
            # this loop, so reaching it here means the aggregate precheck and
            # the allocator disagree about the same cell. That is an internal
            # inconsistency, not a grid state, and it fails closed under its
            # own code rather than quietly wearing the sealed mark.
            if "infeasible_by_sample" in str(exc):
                raise MCInputError(
                    "grid_cell_infeasibility_precheck_disagreed",
                    f"cell (q_mil={q_mil}, r_mil={r_mil}) seed {master_seed} "
                    f"draw {k}: the aggregate precheck admitted this cell and "
                    f"the frozen allocator refused it: {exc}") from exc
            # Everything else — notably `fp_allocation_no_selected_tp_weight`,
            # which is k-DEPENDENT — is not the state the seal names and keeps
            # a typed refusal. Mark/skip/report is licensed for the sealed
            # condition only.
            raise MCInputError(
                "grid_cell_fp_allocation_refused",
                f"cell (q_mil={q_mil}, r_mil={r_mil}) seed {master_seed} "
                f"draw {k}: {exc}") from exc
        fp_dates = _gridmix._select(fp_pools, fp_block["fp_alloc"], rng)
        marker = tuple(sorted(set(tp_dates) | set(fp_dates)))
        payload = {
            "schema": GRID_DRAW_SCHEMA,
            "authority_digest": authority.authority_digest,
            "prepared_digest": authority.prepared_digest,
            "theta_channel": str(channel),
            "master_seed": int(master_seed),
            "q_mil": int(q_mil), "r_mil": int(r_mil), "draw_index": int(k),
            "traded_days": list(marker),
            "n_tp": len(tp_dates), "n_fp": len(fp_dates),
        }
        draws.append(GridDraw(
            capability=_DRAW_CAPABILITY,
            draw_digest=_digest(_DRAW_DIGEST_SCHEMA, payload),
            **{key: (tuple(val) if key == "traded_days" else val)
               for key, val in payload.items()}))
    return tuple(draws), None


# ---------------------------------------------------------------------------
# the Cartesian evaluation
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class GridCellEvaluation:
    """One `(cell, seed, pass, combo, scenario)` evaluation.

    `atoms_by_key` is keyed `(world_index, phase_offset, draw_index)` — the
    Cartesian support, with the draw identity that produced each atom. That
    key set is what makes "exactly once" checkable and what stops a lifecycle
    output being replayed under another draw's identity.

    `atoms` exists so the repository's own reductions can consume this object
    unchanged (`atoms.reduce_world_means`, `feasibility._by_world`).
    """
    q_mil: int
    r_mil: int
    master_seed: int
    n_draws: int
    platform: str
    engine: str
    scenario: str
    theta_channel: str
    B: int
    legal_phase_support: tuple
    draw_digests: tuple
    atoms_by_key: Mapping

    @property
    def atoms(self) -> tuple:
        """Ordered by the Cartesian key, so the reduction is order-stable."""
        return tuple(self.atoms_by_key[k] for k in sorted(self.atoms_by_key))

    @property
    def expected_key_grid(self) -> frozenset:
        return frozenset(
            (b, int(m), d)
            for b in range(self.B)
            for m in self.legal_phase_support
            for d in range(self.n_draws_start,
                           self.n_draws_start + self.n_draws))

    @property
    def n_draws_start(self) -> int:
        return _contracts.aaron_ruled_methods().grid_policy.k_start_index

    def world_means(self) -> tuple:
        """The EXISTING within-world reduction, over the M x K support."""
        return _atoms.reduce_world_means(self.atoms)

    def within_world_ses(self) -> tuple:
        return _atoms.reduce_within_world_ses(self.atoms)


def _evaluate(prepared, *, draws: tuple, platform: str, engine: str,
              scenario: str, channel: str, B: int, master_seed: int,
              q_mil: int, r_mil: int) -> GridCellEvaluation:
    """B x M x K, every combination exactly once, one lifecycle site."""
    support = tuple(prepared.calendar.first_month_offsets)
    worlds = _mcc.build_world_table(prepared, channel=channel, B=B,
                                    master_seed=master_seed)
    pdig = _mcc.prepared_digest(prepared)
    cfg_digest = _atoms.lifecycle_config_digest_for(
        _mcc.lifecycle_config_for(platform), engine=engine, scenario=scenario,
        theta_channel=channel)
    by_key = {}
    for wi, world in enumerate(worlds):
        for off in support:
            for draw in draws:
                # the draw's marker sequence is held FIXED across phases:
                # the phase loop is inside the draw's identity, so changing
                # m never resamples the grid.
                key = (wi, int(off), int(draw.draw_index))
                if key in by_key:
                    raise MCInputError(
                        "grid_cell_key_collision",
                        f"{key} evaluated twice — the Cartesian support must "
                        "contribute each (world, phase, draw) exactly once")
                by_key[key] = _mcc._run_path_atom(
                    prepared, platform=platform, engine=engine,
                    scenario=scenario, channel=channel, world=world,
                    world_index=wi, phase_offset=int(off),
                    lifecycle_config_digest=cfg_digest,
                    master_seed=master_seed, prepared_digest_value=pdig,
                    traded_selector=frozenset(draw.traded_days))
    return GridCellEvaluation(
        q_mil=int(q_mil), r_mil=int(r_mil), master_seed=int(master_seed),
        n_draws=len(draws), platform=platform, engine=engine,
        scenario=scenario, theta_channel=channel, B=int(B),
        legal_phase_support=support,
        draw_digests=tuple(d.draw_digest for d in draws),
        atoms_by_key=MappingProxyType(by_key))


def run_grid_cell(prepared, authority, supplement: Mapping, *,
                  q_mil: int, r_mil: int, master_seed: int, B: int,
                  doublings: int = 0,
                  channel: str = _mcc.PRIMARY_THETA_CHANNEL):
    """ONE cell's `CellStatistics`, through the governed hierarchy.

    Per combo: evaluate B x M x K in Conservative and in Stress, reduce
    WITHIN each world over that M x K support, then take Conservative P5 and
    Stress median ACROSS the B world-level statistics with the frozen
    type-7 estimator `EpistemicResult` uses. Raw outcomes are never pooled
    across worlds.

    Feasibility is the ruled producer, unchanged, over the SEALED day
    population — not the cell's marker set. The selector changes trading
    behaviour; it does not redefine the feasibility population (B-26).

    N13-F1: returns a `grid_replay.InfeasibleCell` instead, for a cell the
    SEALED rule marks and skips. The return happens BEFORE the combo loop, so
    zero lifecycles execute for it — the "skip" is structural rather than a
    promise. Nothing is fabricated: no P5, no median, no feasibility verdict,
    no `CellStatistics`. The caller's pass keeps going, which is the "continue"
    half of the sealed rule and the half the old code lost.
    """
    draws, infeasible = plan_cell_draws(
        authority, prepared, supplement, master_seed=master_seed,
        q_mil=q_mil, r_mil=r_mil, doublings=doublings, channel=channel)
    if infeasible is not None:
        return infeasible
    for draw in draws:
        verify_draw(draw)
    day_universe = prepared.day_sequences[channel]
    cons_p5, stress_med, feasible = {}, {}, {}
    for platform, policy in _mcc.PRIMARY_COMBOS:
        for engine in _mcc.ENGINES:
            cid = f"{platform}|{engine}|{policy}"
            evals = {}
            for scenario in _fz.GATE_SCENARIOS:
                evals[scenario] = _evaluate(
                    prepared, draws=draws, platform=platform, engine=engine,
                    scenario=scenario, channel=channel, B=B,
                    master_seed=master_seed, q_mil=q_mil, r_mil=r_mil)
            # ACROSS worlds, on the world-level statistics only.
            cons_means = sorted(evals["Conservative"].world_means())
            stress_means = sorted(evals["Stress"].world_means())
            cons_p5[cid] = _atoms.percentile_linear(cons_means, _fz.P5)
            stress_med[cid] = _atoms.percentile_linear(stress_means, 50.0)
            combo = _fz.combo_feasibility(
                {s: evals[s] for s in _fz.GATE_SCENARIOS}, day_universe)
            feasible[cid] = bool(combo.feasible)
    # `identity` STAYS EMPTY, and that is a correction rather than an
    # omission. M9 governs a cell's non-USD keys as CONFIGURATION that must
    # be bit-identical K -> 2K; the draw count and the draw-set digest are
    # precisely what doubling changes, so carrying them here made every cell
    # report `grid_replay_cell_identity_mismatch` on a correct 2K pass. The
    # draw-set provenance belongs on the SURROUNDING governed evidence, which
    # is already the architecture: `KReplayEvidence` carries `k`,
    # `k_doubled`, the authority digest and the region-map digests, and this
    # module's `GridCellEvaluation.draw_digests` carries the per-draw
    # identity within the run. Nothing K-varying is smuggled into a field
    # whose contract is invariance.
    return _gr.CellStatistics(
        conservative_p5=cons_p5, stress_median=stress_med, feasible=feasible)


def run_grid_pass(prepared, authority, supplement: Mapping, *,
                  master_seed: int, B: int, doublings: int = 0,
                  cells: tuple = _gr.GRID_CELL_KEYS,
                  channel: str = _mcc.PRIMARY_THETA_CHANNEL) -> dict:
    """One seed's grid pass: `{(q_mil, r_mil): CellStatistics | InfeasibleCell}`.

    `cells` defaults to the frozen Appendix-A grid; a caller may narrow it
    only for a bounded exercise, and `grid_replay.region_map` still requires
    the complete grid before a region can be formed, so a narrowed pass
    cannot become a published region by accident.

    N13-F1: an unsampleable cell contributes an `InfeasibleCell` and the
    comprehension carries on to the next cell. One marked cell no longer
    aborts the seed, the K pass, the 2K pass or the runner. And because the
    marked cell still occupies its key, `region_map`'s all-63-cells
    completeness check keeps doing the work the seal's "report in full" asks
    of it: a skipped cell cannot quietly become a missing one.
    """
    return {tuple(cell): run_grid_cell(
        prepared, authority, supplement, q_mil=int(cell[0]),
        r_mil=int(cell[1]), master_seed=master_seed, B=B,
        doublings=doublings, channel=channel) for cell in cells}


def drawn_count(prepared, authority, supplement: Mapping, *,
                master_seed: int, cells: tuple = _gr.GRID_CELL_KEYS,
                channel: str = _mcc.PRIMARY_THETA_CHANNEL) -> tuple:
    """`(n_draws_at_K, n_draws_at_2K)` for a representative cell.

    Exists so a caller can check a witness's reported pass sizes against the
    draws the frozen policy actually prescribes, instead of taking the
    witness's word for it. Every cell of a pass shares the same k range —
    `repeat_k_indices` depends on the policy and the doubling count, not on
    (q, r) — so one cell answers for the pass.

    N13-F1: the representative cell must be a SAMPLEABLE one. Taking `cells[0]`
    unconditionally made the runner abort whenever the frozen grid's first cell
    happened to be marked — the same blocker one level up, and the reason this
    scans instead. A marked cell prescribes no draws, so it cannot answer for
    the pass; it is skipped, exactly as the sealed rule says.
    """
    if not cells:
        raise MCInputError("grid_draw_no_cells",
                           "a pass over zero cells has no draw count")
    for cell in cells:
        q_mil, r_mil = int(cell[0]), int(cell[1])
        at_k, infeasible = plan_cell_draws(
            authority, prepared, supplement, master_seed=master_seed,
            q_mil=q_mil, r_mil=r_mil, doublings=0, channel=channel)
        if infeasible is not None:
            continue
        at_2k, _ = plan_cell_draws(
            authority, prepared, supplement, master_seed=master_seed,
            q_mil=q_mil, r_mil=r_mil, doublings=1, channel=channel)
        return (len(at_k), len(at_2k))
    raise MCInputError(
        "grid_draw_every_cell_infeasible",
        f"all {len(cells)} cell(s) of this pass are marked "
        f"{_gr.INFEASIBLE_BY_SAMPLE}, so the pass prescribes no draws at all "
        "and there is no count to check a witness against")

