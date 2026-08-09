"""Appendix A precision–recall feasibility grid (empirical-mixture method).

# frozen: S0 Appendix A — for one engine × cost scenario, mix the two
empirical daily-USD-P&L populations
    D_TP : days with Y_cont >= theta, traded by the real E1/E2 rules;
    D_FP : days with Y_cont <  theta, traded the same way in direction d_open;
over the frozen (q, r) grid, and report what each mixture would have been.

Frozen rules implemented here, verbatim in force
------------------------------------------------
* GRID: q ∈ {0.35, 0.40, …, 0.75} (step 0.05); r ∈ {0.20, 0.30, …, 0.80}
  (step 0.10). Built from INTEGER millis, never by float accumulation.
* ROUNDING: `n_tp = floor(r × N_TP_available)`;
  `n_fp = round_half_up(n_tp × (1−q)/q)`. Both are evaluated in EXACT integer /
  decimal arithmetic (see `floor_n_tp` / `n_fp_for`): Python's built-in
  `round()` is banker's rounding and is WRONG for the frozen rule, and binary
  floats turn the exact half-integer 4.5 into 4.499999999999999.
* SELECTION: TP days may come ONLY from D_TP and FP days ONLY from D_FP,
  stratified by year × volatility_regime × event_flag, UNIFORM AT RANDOM WITHIN
  each stratum, using the pre-registered seeds {7, 13, 31}.
  **Ordering by any outcome is FORBIDDEN** — future P&L, MFE, |Y_cont| or any
  outcome label must not touch the selection, or the grid degenerates into a
  half-oracle that also knows which TP days pay best. This module therefore
  reads the P&L VALUES only AFTER the dates are chosen, purely to describe the
  resulting mixture. Uniform sampling is a MAGNITUDE-NEUTRAL feasibility
  benchmark and is neither an optimistic nor a conservative bound.
* SHORTFALL: when a stratum cannot supply its share, the shortfall is
  redistributed over the REMAINING strata in proportion to their available
  days (缺额按其余层的可用日数比例重新分配). When the strata TOGETHER still
  cannot supply the requirement, the grid point is marked
  `infeasible_by_sample`, selection is skipped, and the point is still
  REPORTED IN FULL.
* REALIZED VALUES: rounding makes the achieved precision/recall drift from the
  target, so `target_precision / realized_precision / target_recall /
  realized_recall` are all reported and the MC layer consumes the REALIZED
  ones and the actual trade count, never the theoretical grid values.
* F(q, r) = p · r · N / q with N ≈ 252 is reported alongside every grid point.
* GRID STATUS: a feasibility boundary only. It supports no H1 performance
  claim, and the time-selection pattern of a pretty cell must never be fed
  back into classifier design.

Injected, NOT decided here
--------------------------
`strata` is a date -> (year, volatility_regime, event_flag) mapping supplied by
the caller. The `volatility_regime` axis is RULED (DR-2, Aaron 2026-08-10:
vol20 terciles + vol_na, produced by dataset.build_vol20_regime_mapping); this
module still treats stratum tuples as OPAQUE keys by design — it groups,
allocates and sorts by them and attaches no meaning to their contents. Only the
injected mapping changes.

Engineering conventions (disclosed, deterministic, not frozen text)
-------------------------------------------------------------------
* Grid-point stream: `np.random.default_rng([master_seed, GRID_STREAM_TAG,
  q_mil, r_mil])` (M6_DESIGN §4). Each (seed, q, r) draws from its own
  sub-stream, so the result does not depend on the order in which grid points
  are visited, on wall-clock time, or on any module-level RNG state. The
  frozen text freezes the master seeds only.
* Per-stratum allocation of the frozen totals: proportional shares with
  LARGEST-REMAINDER assignment (Hamilton), computed in integer arithmetic;
  ties in the remainder are broken by ascending stratum key. The frozen text
  fixes stratification and within-stratum uniformity, not the integer split of
  a total across strata, so this is a disclosed convention.
* Within one grid point the stream is consumed TP first, then FP, visiting
  strata in ascending stratum-key order.
* Dates are ISO `YYYY-MM-DD` strings, so lexical sorting IS chronological
  ordering; output date lists and the day-marker sequence are sorted for
  stability.
"""
from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from decimal import ROUND_HALF_UP, Decimal

import numpy as np

from itsf.contracts import (
    RESEARCH_BOOTSTRAP_SEEDS,
    FpAllocationMethod,
    GridRepeatPolicy,
)
# Single source for the theta -> SeedSequence-component encoding, so the DR-4
# bootstrap streams and the DR-5 grid streams can never encode one theta two
# different ways. Import direction is s0.gridmix -> s0.stats only (stats does
# not know gridmix exists), so no cycle is introduced.
from itsf.s0.stats import theta_stream_key

# --- frozen grid axes, built from integer millis (# frozen: S0 Appendix A) ---
Q_GRID_MILLIS = tuple(range(350, 751, 50))     # 0.35 … 0.75 step 0.05
R_GRID_MILLIS = tuple(range(200, 801, 100))    # 0.20 … 0.80 step 0.10
N_YEAR_TRADING_DAYS = 252                      # frozen: F(q,r) = p·r·N/q, N ≈ 252

MARK_TP = "tp"
MARK_FP = "fp"

# Engineering stream tag (M6_DESIGN §4); fixed, and deliberately distinct from
# itsf.s0.stats.STATS_STREAM_TAG so a bootstrap sub-stream and a grid
# sub-stream can never coincide inside one master seed. NOT a seed.
GRID_STREAM_TAG = 9002


# ===========================================================================
# frozen arithmetic
# ===========================================================================

def round_half_up(value: Decimal | float | int) -> int:
    """Decimal ROUND_HALF_UP.  # frozen: S0 Appendix A 取整

    Python's built-in `round()` is banker's rounding (round-half-to-EVEN):
    `round(4.5) == 4`, while the frozen rule demands 5. Floats are converted
    through `str()` so a literal 4.5 stays 4.5.
    """
    dec = value if isinstance(value, Decimal) else Decimal(str(value))
    return int(dec.quantize(Decimal(1), rounding=ROUND_HALF_UP))


def floor_n_tp(r_mil: int, n_tp_available: int) -> int:
    """`n_tp = floor(r × N_TP_available)`.  # frozen: S0 Appendix A 取整

    Integer arithmetic on the recall millis: `r` is never materialised as a
    binary float, so no accumulation error can push the product across an
    integer boundary.
    """
    if r_mil <= 0:
        raise ValueError(f"r_mil must be > 0, got {r_mil}")
    if n_tp_available < 0:
        raise ValueError(f"n_tp_available must be >= 0, got {n_tp_available}")
    return (r_mil * n_tp_available) // 1000


def n_fp_for(n_tp: int, q_mil: int) -> int:
    """`n_fp = round_half_up(n_tp × (1−q)/q)`.  # frozen: S0 Appendix A 取整

    Evaluated as the single exact quotient
    `Decimal(n_tp × (1000 − q_mil)) / Decimal(q_mil)`, so a mathematically
    exact half-integer really lands on `.5` and ROUND_HALF_UP can see it.
    (In binary floats, n_tp=3 and q=0.40 gives 4.499999999999999, which would
    round DOWN to 4 instead of the frozen 5.)
    """
    if not 0 < q_mil <= 1000:
        raise ValueError(f"q_mil must lie in (0, 1000], got {q_mil}")
    if n_tp < 0:
        raise ValueError(f"n_tp must be >= 0, got {n_tp}")
    return round_half_up(Decimal(n_tp * (1000 - q_mil)) / Decimal(q_mil))


def f_expected(base_rate_p: float, r: float, q: float, n_year: int) -> float:
    """F(q, r) = p · r · N / q, N ≈ 252.  # frozen: S0 Appendix A 年交易数"""
    return float(base_rate_p) * float(r) * float(n_year) / float(q)


# ===========================================================================
# validation (fail closed everywhere)
# ===========================================================================

def _validated_pnl(name: str, pnl: Mapping[str, float]) -> dict[str, float]:
    out: dict[str, float] = {}
    for date, value in pnl.items():
        if not isinstance(date, str):
            raise ValueError(f"{name} keys must be ISO date strings, got "
                             f"{date!r}")
        v = float(value)
        if not np.isfinite(v):
            raise ValueError(f"{name}[{date}] is non-finite ({value!r}); "
                             "never silently dropped — fail closed")
        out[date] = v
    return out


def _validated_strata(strata: Mapping[str, Sequence[object]],
                      dates: Sequence[str]) -> dict[str, tuple[str, ...]]:
    """Every selectable date needs a stratum tuple; missing -> ValueError.

    The tuple is `(year, volatility_regime, event_flag)` per frozen Appendix A
    step 3. Its CONTENTS are opaque here by design (the DR-2-ruled vocabulary
    is produced and validated upstream in dataset.py): only the arity is
    structural.
    """
    out: dict[str, tuple[str, ...]] = {}
    missing = [d for d in dates if d not in strata]
    if missing:
        raise ValueError(
            f"{len(missing)} date(s) have no stratum entry, e.g. "
            f"{sorted(missing)[:5]} — the frozen year × volatility_regime × "
            "event_flag stratification cannot be applied; fail closed "
            "(frozen: S0 Appendix A step 3)")
    for date in dates:
        value = strata[date]
        if isinstance(value, str) or not isinstance(value, (tuple, list)):
            raise ValueError(
                f"strata[{date}] must be a (year, volatility_regime, "
                f"event_flag) tuple, got {value!r}")
        if len(value) != 3:
            raise ValueError(
                f"strata[{date}] must have exactly 3 axes (year × "
                f"volatility_regime × event_flag), got {len(value)}")
        out[date] = tuple(str(x) for x in value)
    return out


def _validated_seeds(master_seeds: Sequence[int]) -> tuple[int, ...]:
    seeds = tuple(int(s) for s in master_seeds)
    if not seeds:
        raise ValueError("master_seeds must be non-empty "
                         "(frozen: S0 Appendix A step 3 seeds {7,13,31})")
    if len(set(seeds)) != len(seeds):
        raise ValueError(f"master_seeds must be distinct, got {seeds}")
    return seeds


def _validated_axis(name: str, values: Sequence[float] | None,
                    frozen_millis: tuple[int, ...]) -> tuple[int, ...]:
    """Grid axis as integer millis; the frozen axis is the default."""
    if values is None:
        return frozen_millis
    millis: list[int] = []
    for v in values:
        m = int(round(float(v) * 1000))
        if not 0 < m <= 1000:
            raise ValueError(f"{name} values must lie in (0, 1], got {v!r}")
        millis.append(m)
    if len(set(millis)) != len(millis):
        raise ValueError(f"{name} holds duplicate values: {list(values)}")
    return tuple(millis)


def _stratum_key(stratum: tuple[str, ...]) -> str:
    return "|".join(stratum)


def _pools(pnl: Mapping[str, float],
           strata: Mapping[str, tuple[str, ...]]) -> dict[str, tuple[str, ...]]:
    """stratum key -> sorted tuple of its dates (selection order is stable)."""
    grouped: dict[str, list[str]] = {}
    for date in pnl:
        grouped.setdefault(_stratum_key(strata[date]), []).append(date)
    return {k: tuple(sorted(v)) for k, v in sorted(grouped.items())}


# ===========================================================================
# stratified allocation (engineering convention, disclosed)
# ===========================================================================

def largest_remainder(required: int, weights: Mapping[str, int]
                      ) -> dict[str, int]:
    """Proportional integer split with largest-remainder assignment.

    Integer arithmetic only (`required × w_k` divided by the weight total), so
    the shares carry no float error; leftover units go to the largest
    remainders, ties broken by ASCENDING stratum key. Disclosed engineering
    convention — the frozen text fixes stratification, not the integer split.
    """
    keys = sorted(weights)
    total = sum(int(weights[k]) for k in keys)
    if total <= 0:
        raise ValueError("largest_remainder needs a positive weight total")
    base = {k: (required * int(weights[k])) // total for k in keys}
    leftover = required - sum(base.values())
    order = sorted(keys,
                   key=lambda k: (-((required * int(weights[k])) % total), k))
    for k in order[:leftover]:
        base[k] += 1
    return base


def allocate(required: int, available: Mapping[str, int],
             weights: Mapping[str, int] | None = None) -> dict[str, int]:
    """Allocate `required` days across strata, honouring per-stratum supply.

    Shares are proportional to `weights` (default: stratum AVAILABILITY, which
    is what `build_grid` always passes). A stratum that cannot supply its share
    is capped at its availability and the shortfall is redistributed over the
    REMAINING strata in proportion to THEIR available days
    (# frozen: S0 Appendix A 缺额按其余层的可用日数比例重新分配), repeated
    until the requirement is met. Raises when the strata together cannot meet
    it — the caller marks that grid point `infeasible_by_sample` instead
    (frozen: 全部层合计仍不足时).

    NOTE, disclosed: with the availability-proportional basis `build_grid`
    uses, the per-stratum shortfall branch is provably UNREACHABLE — the
    largest-remainder share of a stratum can exceed its availability only when
    `required > sum(available)`, which is exactly the infeasible_by_sample
    case. The redistribution is implemented and unit-tested anyway because the
    frozen text mandates it and because a different allocation basis (e.g. a
    ruling that the FP mixture must copy the TP stratum composition) would make
    it live immediately; `weights` is that hook, and no `build_grid` parameter
    exposes it.

    GUARANTEE: `sum(allocate(...).values()) == required` on every successful
    return, or this function raises — it never returns a silently-short
    allocation. Two failure modes are distinguished: `required > total`
    (available) is the frozen infeasible_by_sample signal, raised immediately
    below; a `weights` map whose support is DISJOINT from `available`'s
    support (every available stratum has zero weight — e.g. mismatched
    stratum keys between the two mappings) is a caller error, not a
    legitimate shortfall, and is ALSO raised rather than silently returning
    every stratum at 0 (which the naive weight-driven loop would otherwise do,
    since it would never find a positive-weight stratum to start from).
    """
    avail = {k: int(v) for k, v in available.items()}
    basis = dict(avail) if weights is None else {k: int(weights.get(k, 0))
                                                for k in avail}
    total = sum(avail.values())
    if required < 0:
        raise ValueError(f"required must be >= 0, got {required}")
    if required > total:
        raise ValueError(f"required {required} exceeds total availability "
                         f"{total} — infeasible_by_sample")
    if required > 0 and sum(basis.values()) == 0:
        raise ValueError(
            f"allocate: `weights` support is disjoint from `available`'s "
            f"support — every available stratum has zero weight, so a "
            f"required={required} allocation cannot be split on this basis "
            "(caller error, e.g. mismatched stratum keys between `weights` "
            "and `available`; NOT the same as the required > total "
            "infeasible_by_sample case above, and never silently short)")
    alloc = {k: 0 for k in avail}
    remaining = required
    active = {k: basis[k] for k in avail if avail[k] > 0 and basis[k] > 0}
    while remaining > 0 and active:
        for k, share in largest_remainder(remaining, active).items():
            room = avail[k] - alloc[k]
            take = min(share, room)
            alloc[k] += take
            remaining -= take
        # Frozen redistribution: every stratum whose share exceeded its room is
        # now saturated; what is left is re-split over the strata that STILL
        # have room, in proportion to THEIR available days. Each pass either
        # finishes or saturates at least one stratum, so this terminates.
        active = {k: avail[k] for k in avail if alloc[k] < avail[k]}
    if sum(alloc.values()) != required:
        raise RuntimeError(
            f"allocate: internal invariant violated — required {required} "
            f"but produced sum(allocation)={sum(alloc.values())}; this is a "
            "bug in the redistribution logic, never a legitimate shortfall "
            "(a legitimate shortfall is the required > total ValueError "
            "raised above, which the caller reads as infeasible_by_sample)")
    return alloc


def _select(pools: Mapping[str, tuple[str, ...]], alloc: Mapping[str, int],
            rng: np.random.Generator) -> list[str]:
    """Uniform WITHOUT replacement inside each stratum (# frozen: App A step 3).

    Only dates and stratum keys are visible here: no P&L, MFE or label value
    reaches this function, which is what keeps the grid magnitude-neutral.
    """
    picked: list[str] = []
    for key in sorted(alloc):
        k = int(alloc[key])
        if k <= 0:
            continue
        pool = pools[key]
        idx = rng.choice(len(pool), size=k, replace=False)
        picked.extend(pool[int(i)] for i in idx)
    return sorted(picked)


# ===========================================================================
# grid
# ===========================================================================

def _method_string(seeds: tuple[int, ...], n_year: int,
                   fp_allocation: FpAllocationMethod | None = None,
                   grid_policy: GridRepeatPolicy | None = None,
                   theta: float | None = None) -> str:
    """The disclosed recipe.

    With `fp_allocation`/`grid_policy` at None this returns the LEGACY string
    verbatim (the pre-DR-3/DR-5 grid, unchanged byte for byte). On the ruled
    path a suffix is appended that CORRECTS the two clauses the rulings
    supersede — the FP per-stratum basis and the single-draw-per-(seed, cell)
    convention — rather than leaving a stale description in force.
    """
    base = (
        "Appendix A empirical-mixture feasibility grid: q from "
        f"{Q_GRID_MILLIS[0] / 1000:.2f} to {Q_GRID_MILLIS[-1] / 1000:.2f} step "
        "0.05, r from "
        f"{R_GRID_MILLIS[0] / 1000:.2f} to {R_GRID_MILLIS[-1] / 1000:.2f} step "
        "0.10 (frozen S0 Appendix A; axes built from integer millis, never "
        "float accumulation); n_tp = floor(r × N_TP_available), n_fp = "
        "round_half_up(n_tp × (1−q)/q) in exact integer/decimal arithmetic "
        "(decimal ROUND_HALF_UP — python round() is banker's and is wrong "
        "here); TP drawn ONLY from D_TP and FP ONLY from D_FP, stratified by "
        "year × volatility_regime × event_flag (injected mapping, opaque keys; "
        "volatility_regime vocabulary RULED by DR-2 2026-08-10, produced "
        "upstream in dataset.py), per-stratum "
        "shares proportional to availability with largest-remainder assignment "
        "and ascending-stratum-key tie-break (disclosed engineering "
        "convention), UNIFORM WITHOUT REPLACEMENT within each stratum; a "
        "stratum short of its share has the shortfall redistributed over the "
        "remaining strata in proportion to their available days; when the "
        "strata together fall short the point is marked infeasible_by_sample, "
        "selection is skipped and the point is still reported; NO outcome "
        "(P&L, MFE, |Y_cont|, any label) touches the selection — magnitude-"
        "neutral benchmark, neither an optimistic nor a conservative bound, "
        "P&L is read only after the dates are fixed to describe the mixture; "
        f"master seeds {list(seeds)} run independently (frozen S0 Appendix A "
        "step 3 seeds {7,13,31}, contracts.RESEARCH_BOOTSTRAP_SEEDS; the "
        "run-infra provenance seed is never a research input); "
        "grid-point stream = "
        f"default_rng([master_seed, GRID_STREAM_TAG={GRID_STREAM_TAG}, q_mil, "
        "r_mil]) (disclosed engineering convention, M6_DESIGN §4), TP drawn "
        "before FP with strata visited in ascending key order; target AND "
        "realized precision/recall both reported, MC consumes the REALIZED "
        f"values and the actual counts; F(q,r) = p·r·N/q with N = {n_year}; "
        "feasibility boundary only — supports no H1 performance claim")
    if fp_allocation is None and grid_policy is None:
        return base
    return base + (
        " || DR-3/DR-5 RULED PATH (Aaron 2026-08-10), which SUPERSEDES two "
        "clauses above: (1) FP per-stratum shares are NO LONGER proportional "
        f"to FP availability — basis '{fp_allocation.basis}', weight source "
        f"'{fp_allocation.weight_source}': n_fp is apportioned by "
        "largest-remainder over the composition of the TP days ACTUALLY "
        "SELECTED at this grid point, with the frozen-literal shortfall "
        f"redistribution ('{fp_allocation.shortfall_rule}') over the "
        "remaining strata in proportion to THEIR FP availability; "
        "sum(fp_alloc) == n_fp is hard-asserted and the per-stratum "
        "realized-FP vs selected-TP deviations are reported under the cell's "
        "`fp_allocation` block. The selected-TP composition is invariant "
        "across master seeds and across repeats (the TP per-stratum quotas "
        "are fixed by availability and the frozen totals; the stream moves "
        "only WHICH day inside a stratum is taken), and that invariance is "
        "ASSERTED at build time, so one `fp_allocation` block describes the "
        "whole cell. (2) a cell is no longer ONE draw per (seed, q, r): each "
        f"(seed, q, r) runs K = {grid_policy.k_per_seed} repeats, k from "
        f"{grid_policy.k_start_index}, each k on its OWN stream "
        f"default_rng([master_seed, GRID_STREAM_TAG={GRID_STREAM_TAG}, "
        "theta_milli, q_mil, r_mil, k]) — THETA IS IN THE STREAM, so two "
        "thetas can never share a repeat, and the repeat set is prefix-nested "
        "under doubling (K -> 2K reproduces the first K repeats exactly). The "
        "per-seed row reported above is repeat "
        f"k = {grid_policy.k_start_index} of that set (a member of the repeat "
        "distribution, NOT a separate un-nested draw); every repeat's "
        "draw-content digest and the realized cross-K dispersion live under "
        "the cell's `repeats` block. This module runs doublings=0 and "
        "declares NO convergence verdict: the MC_METHOD_SPEC §5 four-rule "
        f"battery ('{grid_policy.convergence_rule}') is applied at the MC "
        "wiring and supplies `mc_converged`; a missing verdict is carried as "
        f"NOT converged, and after the maximum {grid_policy.max_doublings} "
        f"doubling(s) an unconverged cell is marked "
        f"`{MARK_INFEASIBLE_BY_CONVERGENCE}` (fail closed). theta on this "
        f"call = {theta!r}.")


def _build_grid_unchecked(d_tp: Mapping[str, float], d_fp: Mapping[str, float],
                          strata: Mapping[str, Sequence[object]],
                          base_rate_p: float,
                          master_seeds: Sequence[int] = RESEARCH_BOOTSTRAP_SEEDS,
                          q_grid: Sequence[float] | None = None,
                          r_grid: Sequence[float] | None = None,
                          n_year: int = N_YEAR_TRADING_DAYS, *,
                          fp_allocation: FpAllocationMethod | None = None,
                          grid_policy: GridRepeatPolicy | None = None,
                          theta: float | None = None) -> dict:
    """Build the frozen Appendix A (q, r) grid for ONE engine × scenario —
    INTERNAL.

    UNCHECKED: unlike the public `build_grid`, this accepts ANY `master_seeds`
    sequence, including one that is not contracts.RESEARCH_BOOTSTRAP_SEEDS. It
    exists ONLY so tests can exercise a cheap single-seed grid or the
    `_validated_seeds` failure modes (empty / duplicate) without paying for
    three full seeds; production/report code must go through the public
    `build_grid`, which enforces IR DR-02 (# frozen: S0 Appendix A step 3
    seeds {7,13,31}) before delegating here.

    Parameters
    ----------
    d_tp, d_fp : date -> daily USD P&L for the continuation (Y_cont >= theta)
        and non-continuation populations of a single engine × cost scenario.
        The caller loops engines/scenarios; mixing two of them in one call is
        the caller's error to avoid.
    strata : date -> (year, volatility_regime, event_flag). Must cover every
        date in `d_tp` and `d_fp` (missing -> ValueError). Opaque keys.
    base_rate_p : continuation base rate p, used ONLY for the reported
        F(q, r) = p·r·N/q.
    master_seeds : frozen {7, 13, 31}; each seed draws its own selection.
    q_grid, r_grid : override axes for tests/sensitivity; None = frozen axes.
    n_year : N in F(q, r); frozen N ≈ 252.
    fp_allocation, grid_policy, theta : the DR-3/DR-5 RULED path — see
        `build_grid` for the full contract. BOTH None (the default) keeps the
        legacy pre-ruling behaviour bit-identical.

    Returns
    -------
    {"grid": {"q0.35_r0.20": {... "per_seed": {seed: {...}},
                              "infeasible_by_sample": bool ...}},
     "n_tp_available": int, "n_fp_available": int, "method": str}

    On the ruled path every FEASIBLE grid point additionally carries the two
    disclosure sub-dicts `fp_allocation` (DR-3) and `repeats` (DR-5).
    """
    fp_allocation, grid_policy, theta = _validated_ruled_grid_inputs(
        fp_allocation, grid_policy, theta)
    tp_pnl = _validated_pnl("d_tp", d_tp)
    fp_pnl = _validated_pnl("d_fp", d_fp)
    if not tp_pnl:
        raise ValueError("d_tp is empty: recall has no denominator and the "
                         "grid is undefined — fail closed")
    overlap = sorted(set(tp_pnl) & set(fp_pnl))
    if overlap:
        raise ValueError(
            f"{len(overlap)} date(s) appear in BOTH D_TP and D_FP, e.g. "
            f"{overlap[:5]} — the frozen populations are Y_cont >= theta and "
            "Y_cont < theta and are mutually exclusive; fail closed")
    all_dates = sorted(set(tp_pnl) | set(fp_pnl))
    stratum_of = _validated_strata(strata, all_dates)
    seeds = _validated_seeds(master_seeds)
    q_millis = _validated_axis("q_grid", q_grid, Q_GRID_MILLIS)
    r_millis = _validated_axis("r_grid", r_grid, R_GRID_MILLIS)
    p = float(base_rate_p)
    if not 0.0 <= p <= 1.0 or not np.isfinite(p):
        raise ValueError(f"base_rate_p must lie in [0, 1], got {base_rate_p!r}")
    if int(n_year) != n_year or int(n_year) <= 0:
        raise ValueError(f"n_year must be a positive integer, got {n_year!r}")
    n_year = int(n_year)

    tp_pools = _pools(tp_pnl, stratum_of)
    fp_pools = _pools(fp_pnl, stratum_of)
    tp_avail = {k: len(v) for k, v in tp_pools.items()}
    fp_avail = {k: len(v) for k, v in fp_pools.items()}
    n_tp_available = len(tp_pnl)
    n_fp_available = len(fp_pnl)

    grid: dict[str, dict] = {}
    for q_mil in q_millis:
        for r_mil in r_millis:
            key = f"q{q_mil / 1000:.2f}_r{r_mil / 1000:.2f}"
            if key in grid:
                raise ValueError(
                    f"grid key collision on {key!r}: the axes are not "
                    "distinguishable at 2 decimals — fail closed")
            grid[key] = _grid_point(
                q_mil, r_mil, tp_pnl, fp_pnl, tp_pools, fp_pools, tp_avail,
                fp_avail, n_tp_available, n_fp_available, seeds, p, n_year,
                fp_allocation=fp_allocation, grid_policy=grid_policy,
                theta=theta)

    return {"grid": grid,
            "n_tp_available": n_tp_available,
            "n_fp_available": n_fp_available,
            "method": _method_string(seeds, n_year, fp_allocation,
                                     grid_policy, theta)}


def build_grid(d_tp: Mapping[str, float], d_fp: Mapping[str, float],
               strata: Mapping[str, Sequence[object]], base_rate_p: float,
               master_seeds: Sequence[int] = RESEARCH_BOOTSTRAP_SEEDS,
               q_grid: Sequence[float] | None = None,
               r_grid: Sequence[float] | None = None,
               n_year: int = N_YEAR_TRADING_DAYS, *,
               fp_allocation: FpAllocationMethod | None = None,
               grid_policy: GridRepeatPolicy | None = None,
               theta: float | None = None) -> dict:
    """Build the frozen Appendix A (q, r) grid for ONE engine × scenario —
    PUBLIC entry.

    IR DR-02 mutation guard: `master_seeds` MUST be exactly
    `contracts.RESEARCH_BOOTSTRAP_SEEDS` (the frozen {7, 13, 31}, in that
    order) — the only seeds any research-path RNG may derive from. Any other
    value is REFUSED with ValueError rather than silently honoured. Tests that
    need a cheap single-seed grid or an invalid-seed case call
    `_build_grid_unchecked` directly — a private helper that ONLY tests may
    use.

    THE DR-3 / DR-5 RULED PATH (keyword-only, Aaron 2026-08-10)
    ----------------------------------------------------------
    `fp_allocation` (`contracts.FpAllocationMethod`) and `grid_policy`
    (`contracts.GridRepeatPolicy`) are read STRUCTURALLY — this module never
    selects a ruled value on its own, and an un-ruled field value is refused
    by the primitives' own dispatch guards (`fp_allocation_basis_not_ruled:…`,
    `grid_convergence_rule_not_ruled:…`, …). The production caller passes
    `config.methods.fp_allocation` / `config.methods.grid_policy`.

    * BOTH None (the default) -> the LEGACY pre-ruling grid, bit-identical to
      what this module produced before the rulings landed. Legacy and
      synthetic callers therefore need no change.
    * ONE of the two None -> ValueError. The two were ruled as a COHERENT PAIR
      for the production path (DR-5's repeats redraw the TP selection, and
      DR-3's FP allocation is a function of that selection), so a half-ruled
      grid is neither the legacy artefact nor the ruled one, and this module
      refuses to invent the missing half.
    * `theta` is REQUIRED whenever `grid_policy` is given, because theta is a
      COMPONENT OF THE RNG STREAM (DR-5 `stream_includes_theta=True`): a
      silently-missing theta would let two thetas share every repeat. Passing
      `theta` WITHOUT the ruled pair is also refused rather than ignored.

    See `_build_grid_unchecked` for the remaining parameter and return-shape
    documentation.
    """
    seeds = tuple(int(s) for s in master_seeds)
    if seeds != RESEARCH_BOOTSTRAP_SEEDS:
        raise ValueError(
            "master_seeds must be exactly contracts.RESEARCH_BOOTSTRAP_SEEDS "
            f"{RESEARCH_BOOTSTRAP_SEEDS} — IR DR-02: the only seeds any "
            f"research-path RNG may derive from; got {seeds}. A test that "
            "needs different seeds must call _build_grid_unchecked directly "
            "instead of this public entry point.")
    return _build_grid_unchecked(d_tp, d_fp, strata, base_rate_p,
                                 master_seeds=seeds, q_grid=q_grid,
                                 r_grid=r_grid, n_year=n_year,
                                 fp_allocation=fp_allocation,
                                 grid_policy=grid_policy, theta=theta)


def _grid_point(q_mil: int, r_mil: int, tp_pnl: Mapping[str, float],
                fp_pnl: Mapping[str, float],
                tp_pools: Mapping[str, tuple[str, ...]],
                fp_pools: Mapping[str, tuple[str, ...]],
                tp_avail: Mapping[str, int], fp_avail: Mapping[str, int],
                n_tp_available: int, n_fp_available: int,
                seeds: tuple[int, ...], base_rate_p: float,
                n_year: int, *,
                fp_allocation: FpAllocationMethod | None = None,
                grid_policy: GridRepeatPolicy | None = None,
                theta: float | None = None) -> dict:
    """One (q, r) cell across all master seeds.

    Two paths, chosen ONLY by whether the caller supplied the ruled pair (the
    pair is validated together at the entry point, so here they are either
    both present or both None):

    * LEGACY (both None) — one draw per (seed, q, r) off the 4-component
      stream, FP allocated by availability. Byte-for-byte what this function
      did before DR-3/DR-5 landed.
    * RULED — `_ruled_cell` below.
    """
    q = q_mil / 1000.0
    r = r_mil / 1000.0
    n_tp = floor_n_tp(r_mil, n_tp_available)          # frozen: App A 取整
    n_fp = n_fp_for(n_tp, q_mil)                      # frozen: App A 取整
    point: dict = {
        "target_precision": q,
        "target_recall": r,
        "n_tp_target": n_tp,
        "n_fp_target": n_fp,
        "F_expected": f_expected(base_rate_p, r, q, n_year),
        "infeasible_by_sample": False,
        "per_seed": {},
    }
    if n_fp > n_fp_available:
        # frozen: 全部层合计仍不足 -> 标记 infeasible_by_sample 跳过并完整报告
        point["infeasible_by_sample"] = True
        point["infeasible_reason"] = (
            f"n_fp target {n_fp} exceeds D_FP availability {n_fp_available}")
        return point

    # TP allocation is seed-INDEPENDENT (frozen totals + availability only);
    # the seed decides WHICH days inside each stratum, never how many. This
    # holds on BOTH paths — it is the reason the DR-3 selected-TP composition
    # is seed-stable, which `_ruled_cell` asserts rather than assumes.
    tp_alloc = allocate(n_tp, tp_avail)
    if fp_allocation is None:
        fp_alloc = allocate(n_fp, fp_avail)
        for master_seed in seeds:
            rng = np.random.default_rng(
                [int(master_seed), GRID_STREAM_TAG, int(q_mil), int(r_mil)])
            tp_dates = _select(tp_pools, tp_alloc, rng)  # TP consumes stream
            fp_dates = _select(fp_pools, fp_alloc, rng)  # ... then FP
            point["per_seed"][master_seed] = _seed_report(
                q, r, tp_dates, fp_dates, tp_alloc, fp_alloc, tp_pnl, fp_pnl,
                n_tp_available, base_rate_p, n_year)
        return point
    _ruled_cell(point, q_mil, r_mil, n_fp, tp_pnl, fp_pnl, tp_pools, fp_pools,
                tp_alloc, fp_avail, n_tp_available, seeds, base_rate_p, n_year,
                fp_allocation, grid_policy, theta)
    return point


def _seed_report(q: float, r: float, tp_dates: Sequence[str],
                 fp_dates: Sequence[str], tp_alloc: Mapping[str, int],
                 fp_alloc: Mapping[str, int], tp_pnl: Mapping[str, float],
                 fp_pnl: Mapping[str, float], n_tp_available: int,
                 base_rate_p: float, n_year: int) -> dict:
    """Post-selection description of ONE mixture.

    The ONLY place P&L values are read, and the dates are already fixed by
    then (# frozen: S0 Appendix A anti-ordering rule).
    """
    n_tp_actual = len(tp_dates)
    n_fp_actual = len(fp_dates)
    n_total = n_tp_actual + n_fp_actual
    selected = [tp_pnl[d] for d in tp_dates] + [fp_pnl[d] for d in fp_dates]
    markers = sorted([(d, MARK_TP) for d in tp_dates]
                     + [(d, MARK_FP) for d in fp_dates])
    return {
        "tp_dates": list(tp_dates),
        "fp_dates": list(fp_dates),
        "n_tp_actual": n_tp_actual,
        "n_fp_actual": n_fp_actual,
        # frozen: target AND realized must both be reported; MC uses realized
        "target_precision": q,
        "target_recall": r,
        "realized_precision": (n_tp_actual / n_total) if n_total else None,
        "realized_recall": n_tp_actual / n_tp_available,
        "day_markers": markers,
        # seed-invariant by construction (F depends on p, q, r, N only);
        # repeated here so a per-seed row is never quoted without it
        "F_expected": f_expected(base_rate_p, r, q, n_year),
        "mixture_mean_pnl": (float(np.mean(selected)) if selected else None),
        "allocation_tp": dict(sorted(tp_alloc.items())),
        "allocation_fp": dict(sorted(fp_alloc.items())),
    }


# ===========================================================================
# DR-3 + DR-5 (Aaron 2026-08-10) — this module is the production CONSUMER of
# the ruled `contracts.FpAllocationMethod` and `contracts.GridRepeatPolicy`.
#
# Every function below takes the method/policy dataclass as an EXPLICIT
# parameter and dispatches on its fields. The ruled STRINGS that appear here
# are DISPATCH KEYS — the exact rule ids this module implements — and nothing
# selects them on its own: an un-ruled value raises with a precise code (fail
# closed), never a silent default.
# ===========================================================================

#: DISPATCH KEYS — the exact ruled `FpAllocationMethod` field values.
FP_ALLOCATION_BASIS_B = "B"
FP_ALLOCATION_WEIGHT_SOURCE = "selected_tp_composition"
FP_ALLOCATION_SHORTFALL_RULE = "frozen_literal_redistribute_remaining_fp"

#: DISPATCH KEY — the exact ruled `GridRepeatPolicy.convergence_rule`. The MC
#: §5 four-rule battery itself lives at the MC wiring; this module reports
#: realized cross-K dispersion and raises the fail-closed marker, and declares
#: no convergence VERDICT of its own.
GRID_CONVERGENCE_RULE = "mc_spec_s5_four_rules_at_mc_wiring"

#: The fail-closed marker a cell carries when it is still unconverged after
#: the doubling cap. Distinct from the frozen `infeasible_by_sample` marker:
#: that one says the strata cannot supply the days, this one says the repeats
#: could not settle.
MARK_INFEASIBLE_BY_CONVERGENCE = "infeasible_by_convergence"


def _require_fp_allocation_method(method) -> FpAllocationMethod:
    if not isinstance(method, FpAllocationMethod):
        raise ValueError("fp_allocation_method_not_a_FpAllocationMethod:"
                         f"{type(method).__name__}")
    if method.basis != FP_ALLOCATION_BASIS_B:
        raise ValueError(f"fp_allocation_basis_not_ruled:{method.basis}")
    if method.weight_source != FP_ALLOCATION_WEIGHT_SOURCE:
        raise ValueError(
            f"fp_allocation_weight_source_not_ruled:{method.weight_source}")
    if method.shortfall_rule != FP_ALLOCATION_SHORTFALL_RULE:
        raise ValueError(
            f"fp_allocation_shortfall_rule_not_ruled:{method.shortfall_rule}")
    return method


def _counts(name: str, mapping) -> dict[str, int]:
    """A stratum-key -> non-negative-int count map. Fail closed."""
    if not isinstance(mapping, Mapping):
        raise ValueError(f"{name}_not_a_mapping:{type(mapping).__name__}")
    out: dict[str, int] = {}
    for key, value in mapping.items():
        if not isinstance(key, str):
            raise ValueError(f"{name}_key_not_a_str:{key!r}")
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{name}_value_not_an_int:{key}")
        if value < 0:
            raise ValueError(f"{name}_value_negative:{key}")
        out[key] = int(value)
    return out


def assert_fp_conservation(fp_alloc: Mapping[str, int], n_fp: int) -> None:
    """HARD conservation gate: ``sum(fp_alloc) == n_fp``, or RuntimeError.

    Separate, callable and tested on its own: a silently-short FP allocation
    would change the realized precision of a grid cell without changing any
    reported target, which is exactly the class of drift the Appendix-A cell
    report cannot see. This never returns a "close enough" verdict.
    """
    total = sum(int(v) for v in fp_alloc.values())
    if total != int(n_fp):
        raise RuntimeError(
            f"fp_allocation_conservation_violated: sum(fp_alloc)={total} != "
            f"n_fp={int(n_fp)} — this is a bug in the allocation, never a "
            "legitimate shortfall (a legitimate shortfall is the "
            "infeasible_by_sample ValueError raised before any allocation)")


def fp_allocation_from_selected_tp(n_fp: int,
                                   selected_tp: Mapping[str, int],
                                   fp_available: Mapping[str, int],
                                   method: FpAllocationMethod) -> dict:
    """The ruled DR-3 basis-"B" per-stratum FP allocation.

    THE RULING. The FP mixture follows the composition of the TP days that
    were ACTUALLY SELECTED at this grid point — `selected_tp_s / n_tp` — not
    the composition of the full D_TP pool and not the target quotas. So the
    Hamilton (largest-remainder) weights here are the SELECTED TP counts per
    stratum; dividing every weight by `n_tp` scales numerator and denominator
    of every share identically, so the integer counts give the exact same
    apportionment as the shares do, without a float ever entering.

    THE FOUR BEHAVIOURS THIS FUNCTION IS ANSWERABLE FOR.
      1. FP-ONLY STRATA GET WEIGHT 0. A stratum with FP days but no selected
         TP day contributes nothing to the TP composition, so it receives no
         share in the first pass. It can still receive redistribution (2).
      2. SHORTFALL. A stratum with TP support but insufficient FP
         AVAILABILITY (zero, or merely less than its share) is capped at what
         it has, and the shortfall is redistributed over the REMAINING strata
         IN PROPORTION TO THEIR FP AVAILABILITY — the frozen-literal rule
         (缺额按其余层的可用日数比例重新分配), which basis "B" finally makes
         reachable: under the old availability-proportional basis a stratum's
         share could only exceed its availability when the whole requirement
         did. Note the redistribution basis is FP AVAILABILITY, not the TP
         composition: the first pass follows the ruling, the shortfall pass
         follows the frozen text.
      3. TIE-BREAK. Equal remainders resolve by ASCENDING STRATUM KEY
         (inherited from `largest_remainder`), so the split is a pure function
         of the inputs and never of dict insertion order.
      4. CONSERVATION. `sum(fp_alloc) == n_fp` is asserted before returning
         (`assert_fp_conservation`). When the strata TOGETHER cannot supply
         `n_fp`, a ValueError is raised BEFORE any allocation and the caller
         marks the point `infeasible_by_sample` (frozen).

    Also returns the per-stratum realized-FP-vs-selected-TP composition
    DEVIATIONS, which rounding makes unavoidable and which must therefore be
    disclosed rather than discovered.
    """
    _require_fp_allocation_method(method)
    if isinstance(n_fp, bool) or not isinstance(n_fp, int):
        raise ValueError(
            f"fp_allocation_n_fp_not_an_int:{type(n_fp).__name__}")
    if n_fp < 0:
        raise ValueError(f"fp_allocation_n_fp_negative:{n_fp}")

    weights = _counts("selected_tp", selected_tp)
    avail = _counts("fp_available", fp_available)
    keys = sorted(set(weights) | set(avail))
    weights = {k: weights.get(k, 0) for k in keys}
    avail = {k: avail.get(k, 0) for k in keys}
    n_tp_selected = sum(weights.values())
    total_avail = sum(avail.values())

    alloc = {k: 0 for k in keys}
    shortfall_redistributed = 0
    if n_fp > 0:
        if n_tp_selected == 0:
            raise ValueError(
                "fp_allocation_no_selected_tp_weight: basis 'B' apportions "
                "n_fp by the SELECTED TP composition, and no stratum holds a "
                "selected TP day — there is no composition to follow "
                "(fail closed)")
        if n_fp > total_avail:
            raise ValueError(
                f"fp_allocation_infeasible_by_sample:{n_fp}>{total_avail}")

        remaining = n_fp
        # Pass 1 — the RULED basis: shares proportional to the SELECTED TP
        # composition, over every stratum that holds a selected TP day
        # INCLUDING one whose FP availability is zero. Including it is what
        # generates the shortfall the frozen rule then redistributes.
        first = {k: w for k, w in weights.items() if w > 0}
        for key, share in sorted(largest_remainder(remaining, first).items()):
            take = min(int(share), avail[key] - alloc[key])
            alloc[key] += take
            remaining -= take
        shortfall_redistributed = remaining

        # Pass 2+ — the FROZEN literal: what is left is re-split over the
        # strata that STILL have room, in proportion to THEIR available days.
        # Each pass saturates at least one stratum or finishes, so this
        # terminates; the guard below refuses to spin either way.
        while remaining > 0:
            active = {k: avail[k] for k in keys if alloc[k] < avail[k]}
            if not active:
                break
            before = remaining
            for key, share in sorted(largest_remainder(remaining,
                                                       active).items()):
                take = min(int(share), avail[key] - alloc[key])
                alloc[key] += take
                remaining -= take
            if remaining == before:
                raise RuntimeError(
                    "fp_allocation_redistribution_made_no_progress: "
                    f"{remaining} unit(s) unplaced with room available — bug")

    assert_fp_conservation(alloc, n_fp)

    deviations: dict[str, dict[str, float | int | None]] = {}
    for key in keys:
        tp_share = (weights[key] / n_tp_selected) if n_tp_selected else None
        fp_share = (alloc[key] / n_fp) if n_fp else None
        deviation = (None if (tp_share is None or fp_share is None)
                     else fp_share - tp_share)
        deviations[key] = {
            "selected_tp": weights[key],
            "fp_available": avail[key],
            "fp_allocated": alloc[key],
            "target_tp_share": tp_share,
            "realized_fp_share": fp_share,
            "deviation": deviation,
        }
    devs = [abs(d["deviation"]) for d in deviations.values()
            if d["deviation"] is not None]
    return {
        "fp_alloc": dict(alloc),
        "n_fp": int(n_fp),
        "n_tp_selected": n_tp_selected,
        "n_fp_available": total_avail,
        "weights_selected_tp": dict(weights),
        "shortfall_redistributed": int(shortfall_redistributed),
        "deviations": deviations,
        "max_abs_deviation": (max(devs) if devs else None),
        "basis": method.basis,
        "weight_source": method.weight_source,
        "shortfall_rule": method.shortfall_rule,
        "method": (
            "DR-3 basis 'B': n_fp apportioned by largest-remainder (Hamilton) "
            "over the SELECTED TP composition per stratum (selected_tp_s / "
            "n_tp — not the full D_TP pool, not the target quotas), integer "
            "arithmetic throughout, ties on equal remainders broken by "
            "ascending stratum key; FP-only strata carry weight 0; a stratum "
            "whose FP availability cannot meet its share is capped and the "
            "shortfall is redistributed over the remaining strata in "
            "proportion to their FP availability (frozen literal); "
            "sum(fp_alloc) == n_fp is asserted, and n_fp > total FP "
            "availability raises before any allocation so the caller marks "
            "the point infeasible_by_sample; per-stratum realized-FP vs "
            "selected-TP composition deviations are reported because "
            "integer rounding makes them unavoidable"),
    }


# --- DR-5: per-cell repeats, RNG streams, cross-K dispersion ----------------

def _require_grid_policy(policy) -> GridRepeatPolicy:
    if not isinstance(policy, GridRepeatPolicy):
        raise ValueError("grid_repeat_policy_not_a_GridRepeatPolicy:"
                         f"{type(policy).__name__}")
    if policy.stream_includes_theta is not True:
        raise ValueError("grid_stream_includes_theta_not_ruled:"
                         f"{policy.stream_includes_theta}")
    if policy.convergence_rule != GRID_CONVERGENCE_RULE:
        raise ValueError(
            f"grid_convergence_rule_not_ruled:{policy.convergence_rule}")
    if isinstance(policy.k_per_seed, bool) or not isinstance(
            policy.k_per_seed, int) or policy.k_per_seed < 1:
        raise ValueError(f"grid_k_per_seed_invalid:{policy.k_per_seed}")
    if isinstance(policy.k_start_index, bool) or not isinstance(
            policy.k_start_index, int) or policy.k_start_index < 0:
        raise ValueError(f"grid_k_start_index_invalid:{policy.k_start_index}")
    if isinstance(policy.max_doublings, bool) or not isinstance(
            policy.max_doublings, int) or policy.max_doublings < 0:
        raise ValueError(f"grid_max_doublings_invalid:{policy.max_doublings}")
    return policy


def repeat_k_indices(policy: GridRepeatPolicy, *,
                     doublings: int = 0) -> tuple[int, ...]:
    """The repeat indices k for one (seed, cell) — K per seed per cell.

    K comes from `policy.k_per_seed` and k starts at `policy.k_start_index`;
    `doublings` is the MC §5 convergence re-run counter, so the k range is
    ``[start, start + K * 2**doublings)``. Because the range only GROWS from
    the same start, and because each k drives its OWN independent stream (see
    `repeat_stream_entropy`), a doubled run reproduces the first K repeats
    exactly and merely appends new ones — the prefix-nesting property.
    """
    _require_grid_policy(policy)
    if isinstance(doublings, bool) or not isinstance(doublings, int):
        raise ValueError(f"grid_doublings_not_an_int:{doublings!r}")
    if doublings < 0:
        raise ValueError(f"grid_doublings_negative:{doublings}")
    if doublings > policy.max_doublings:
        raise ValueError(
            f"grid_doublings_exceed_max:{doublings}>{policy.max_doublings}")
    start = policy.k_start_index
    return tuple(range(start, start + policy.k_per_seed * (2 ** doublings)))


def _validated_axis_milli(name: str, value) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"grid_{name}_not_an_int:{value!r}")
    if not 0 < value <= 1000:
        raise ValueError(f"grid_{name}_out_of_range:{value}")
    return int(value)


def repeat_stream_entropy(master_seed: int, theta: float, q_mil: int,
                          r_mil: int, k: int,
                          policy: GridRepeatPolicy) -> list[int]:
    """SeedSequence entropy of ONE repeat's stream (DR-5).

    ``[master_seed, GRID_STREAM_TAG, theta_milli, q_milli, r_milli, k]`` —
    THETA IS IN THE STREAM (ruled `stream_includes_theta=True`; a policy that
    says False is REFUSED here, it is not an option this module implements).
    Without theta, two thetas sharing a (seed, q, r, k) would draw the SAME
    repeat, and the per-theta grids would stop being independent replicates.

    Every k gets its own independent stream, which is what makes the repeat
    set prefix-nested under doubling and makes the result independent of the
    order in which repeats are visited.
    """
    _require_grid_policy(policy)
    seed = int(master_seed)
    if seed not in RESEARCH_BOOTSTRAP_SEEDS:
        raise ValueError(
            f"grid_master_seed_not_a_research_seed:{seed} "
            f"(IR DR-02: {RESEARCH_BOOTSTRAP_SEEDS})")
    if isinstance(k, bool) or not isinstance(k, int):
        raise ValueError(f"grid_k_not_an_int:{k!r}")
    if k < policy.k_start_index:
        raise ValueError(
            f"grid_k_below_start_index:{k}<{policy.k_start_index}")
    return [seed, GRID_STREAM_TAG, theta_stream_key(theta),
            _validated_axis_milli("q_mil", q_mil),
            _validated_axis_milli("r_mil", r_mil), int(k)]


def repeat_rng(master_seed: int, theta: float, q_mil: int, r_mil: int, k: int,
               policy: GridRepeatPolicy) -> np.random.Generator:
    """The Generator for ONE repeat k of one (seed, theta, q, r) cell."""
    return np.random.default_rng(np.random.SeedSequence(
        repeat_stream_entropy(master_seed, theta, q_mil, r_mil, k, policy)))


def repeat_rngs(master_seed: int, theta: float, q_mil: int, r_mil: int,
                policy: GridRepeatPolicy, *, doublings: int = 0
                ) -> dict[int, np.random.Generator]:
    """`{k: Generator}` for the whole repeat set of one (seed, theta, cell)."""
    return {k: repeat_rng(master_seed, theta, q_mil, r_mil, k, policy)
            for k in repeat_k_indices(policy, doublings=doublings)}


def cross_k_dispersion(values_by_k: Mapping[int, float]) -> dict:
    """REALIZED dispersion of one statistic across the repeats. No verdict.

    Reports the spread the repeats actually produced (min / max / max-min /
    mean) so the MC §5 four-rule battery at the MC wiring has a number to
    apply its tolerances to. This function owns no tolerance and declares no
    convergence: it is the measurement, not the ruling.
    """
    if not isinstance(values_by_k, Mapping) or not values_by_k:
        raise ValueError("cross_k_dispersion_needs_a_non_empty_mapping")
    values: dict[int, float] = {}
    for k, v in values_by_k.items():
        if isinstance(k, bool) or not isinstance(k, int):
            raise ValueError(f"cross_k_dispersion_k_not_an_int:{k!r}")
        value = float(v)
        if not np.isfinite(value):
            raise ValueError(f"cross_k_dispersion_non_finite:{k}")
        values[int(k)] = value
    arr = np.asarray([values[k] for k in sorted(values)], dtype=float)
    return {
        "n_k": int(arr.size),
        "k_min": min(values),
        "k_max": max(values),
        "min": float(arr.min()),
        "max": float(arr.max()),
        "spread": float(arr.max() - arr.min()),
        "mean": float(arr.mean()),
        "values_by_k": {k: values[k] for k in sorted(values)},
    }


def repeat_convergence_marker(policy: GridRepeatPolicy, *,
                              doublings_used: int,
                              mc_converged: bool | None) -> dict:
    """The DR-5 fail-closed `infeasible_by_convergence` marker path.

    `mc_converged` is the MC §5 four-rule battery's verdict, supplied BY THE
    MC WIRING — this module does not compute it and must not be read as
    having done so. ``None`` means "no verdict available" and is treated
    EXACTLY like "not converged": the fail-closed direction is the only one a
    missing verdict may take.

    A cell that is still unconverged once `doublings_used` has reached
    `policy.max_doublings` is marked `infeasible_by_convergence`; below the
    cap it is not yet infeasible, it simply owes another doubling
    (`must_double_again`).
    """
    _require_grid_policy(policy)
    if isinstance(doublings_used, bool) or not isinstance(doublings_used, int):
        raise ValueError(f"grid_doublings_not_an_int:{doublings_used!r}")
    if doublings_used < 0:
        raise ValueError(f"grid_doublings_negative:{doublings_used}")
    if doublings_used > policy.max_doublings:
        raise ValueError("grid_doublings_exceed_max:"
                         f"{doublings_used}>{policy.max_doublings}")
    if mc_converged is not None and not isinstance(mc_converged, bool):
        raise ValueError(
            f"grid_mc_converged_not_a_bool_or_none:{mc_converged!r}")
    converged = mc_converged is True
    at_cap = doublings_used >= policy.max_doublings
    infeasible = (not converged) and at_cap
    return {
        "mc_converged": mc_converged,
        "doublings_used": int(doublings_used),
        "max_doublings": int(policy.max_doublings),
        "k_per_seed_realized": policy.k_per_seed * (2 ** int(doublings_used)),
        "must_double_again": (not converged) and not at_cap,
        MARK_INFEASIBLE_BY_CONVERGENCE: infeasible,
        "convergence_rule": policy.convergence_rule,
        "reason": (
            None if converged else
            ("still unconverged after the maximum "
             f"{policy.max_doublings} doubling(s) — fail closed"
             if at_cap else
             f"unconverged at doubling {doublings_used} of "
             f"{policy.max_doublings}; another doubling is owed")),
        "note": (
            "the MC_METHOD_SPEC §5 four-rule battery is applied at the MC "
            "wiring and supplies `mc_converged`; this module reports realized "
            "cross-K dispersion and raises the fail-closed marker only — it "
            "declares no convergence verdict of its own, and a missing "
            "verdict (None) is treated as NOT converged"),
    }


# ===========================================================================
# DR-3 + DR-5 ON THE PRODUCTION PATH — `build_grid`'s ruled branch.
#
# Everything above this line is either the legacy grid or a standalone ruled
# PRIMITIVE. This section is the part that puts the primitives ON the path
# `scripts/s0_real_run.py` actually walks, and it adds NO ruling of its own:
# every ruled value it uses is read off the passed-in dataclasses.
#
# The one CONVENTION this section introduces (disclosed, not ruled, and stated
# in the method string): the per-seed row a cell reports is repeat
# k = `policy.k_start_index` — a MEMBER of the repeat set rather than a
# separate draw off the old 4-component stream. Keeping the old stream for the
# headline row would reintroduce exactly the defect DR-5 closes (that stream
# has no theta component, so the two frozen thetas would share every headline
# selection).
# ===========================================================================

#: Length of the per-repeat draw-content digest (hex chars of a SHA-256).
#: Long enough that a collision across a 63-point × 3-seed × K=200 grid is
#: not a practical concern, short enough that the digests do not dominate the
#: report payload.
REPEAT_DIGEST_HEX_LEN = 16


def _validated_ruled_grid_inputs(fp_allocation, grid_policy, theta):
    """The DR-3/DR-5 coherent-pair gate. Returns the triple, or raises.

    Refuses, in this order: a theta with no ruled pair (silently ignoring it
    would hide a caller error), a half-supplied pair, an un-ruled field value
    (delegated to the primitives' OWN dispatch guards, so there is exactly one
    place where a ruled string is checked), a missing theta, and a theta that
    is not a stream-encodable number (delegated to `theta_stream_key`, the
    single theta encoder shared with the DR-4 bootstrap streams).
    """
    if fp_allocation is None and grid_policy is None:
        if theta is not None:
            raise ValueError(
                f"grid_theta_without_ruled_methods:{theta!r} — theta is a "
                "component of the DR-5 repeat stream and has no meaning on "
                "the legacy path; pass fp_allocation AND grid_policy, or "
                "drop theta (never silently ignored)")
        return None, None, None
    if fp_allocation is None or grid_policy is None:
        raise ValueError(
            "grid_ruled_pair_incomplete:"
            f"fp_allocation={'set' if fp_allocation is not None else 'None'},"
            f"grid_policy={'set' if grid_policy is not None else 'None'} — "
            "DR-3 and DR-5 were ruled as a coherent pair for the production "
            "path (DR-5's repeats redraw the TP selection and DR-3's FP "
            "allocation is a function of that selection); a half-ruled grid "
            "is neither the legacy artefact nor the ruled one — fail closed")
    _require_fp_allocation_method(fp_allocation)
    _require_grid_policy(grid_policy)
    if theta is None:
        raise ValueError(
            "grid_theta_required_with_grid_policy — DR-5 rules "
            "stream_includes_theta=True, so a missing theta would let the two "
            "frozen thetas share every repeat; fail closed rather than "
            "defaulting")
    if isinstance(theta, bool) or not isinstance(theta, (int, float)):
        raise ValueError(f"grid_theta_not_a_number:{theta!r}")
    theta_stream_key(theta)          # exactness gate, shared with DR-4
    return fp_allocation, grid_policy, float(theta)


def repeat_draw_digest(tp_dates: Sequence[str],
                       fp_dates: Sequence[str]) -> str:
    """Digest of ONE repeat's DRAW CONTENT — the selected dates, nothing else.

    k is deliberately NOT part of the preimage. A digest that mixed k in would
    differ across repeats even when the two repeats drew the identical days,
    which would fake the very k-variation the digests exist to evidence (and
    would make the prefix-nesting check vacuous).
    """
    payload = "|".join((",".join(tp_dates), ",".join(fp_dates)))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[
        :REPEAT_DIGEST_HEX_LEN]


def _digest_of_digests(digests_by_k: Mapping[int, str]) -> str:
    """One-line identity of a whole repeat SET (k IS in this preimage)."""
    payload = ";".join(f"{k}:{digests_by_k[k]}" for k in sorted(digests_by_k))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[
        :REPEAT_DIGEST_HEX_LEN]


def _dispersion_or_none(values_by_k: Mapping[int, float | None]):
    """`cross_k_dispersion`, or None when the statistic is undefined.

    `realized_precision` and `mixture_mean_pnl` are None for an empty
    selection (n_tp = n_fp = 0 at the small end of the grid). Reporting None
    for the whole dispersion is the honest answer: `cross_k_dispersion` owns
    no missing-value convention and must not be handed a fabricated 0.0.
    """
    if not values_by_k or any(v is None for v in values_by_k.values()):
        return None
    return cross_k_dispersion(values_by_k)


def _selected_tp_composition(tp_dates: Sequence[str],
                             stratum_of_date: Mapping[str, str],
                             all_keys: Sequence[str]) -> dict[str, int]:
    """Per-stratum counts of the TP days ACTUALLY SELECTED in one repeat.

    Counted from the DATES, not read back off `tp_alloc`. The two are equal by
    construction — which is precisely the invariant `_ruled_cell` asserts, and
    an assertion that read its own answer off the thing it is checking would
    assert nothing.
    """
    counts = {key: 0 for key in all_keys}
    for date in tp_dates:
        counts[stratum_of_date[date]] += 1
    return counts


def _ruled_cell(point: dict, q_mil: int, r_mil: int, n_fp: int,
                tp_pnl: Mapping[str, float], fp_pnl: Mapping[str, float],
                tp_pools: Mapping[str, tuple[str, ...]],
                fp_pools: Mapping[str, tuple[str, ...]],
                tp_alloc: Mapping[str, int], fp_avail: Mapping[str, int],
                n_tp_available: int, seeds: tuple[int, ...],
                base_rate_p: float, n_year: int,
                fp_allocation: FpAllocationMethod,
                grid_policy: GridRepeatPolicy, theta: float) -> None:
    """The DR-3 + DR-5 cell: K repeats per seed, FP by selected-TP composition.

    Mutates `point` in place, adding the per-seed rows plus the two disclosure
    sub-dicts `fp_allocation` and `repeats`.

    Order of stream consumption inside one repeat is the frozen convention,
    unchanged: TP first, then FP, strata in ascending key order — but the
    FP allocation now sits BETWEEN the two, because it is a function of the TP
    days this repeat just drew.

    S0 runs `doublings = 0`. Doubling is an MC-side re-run driven by the §5
    verdict this module does not compute, so the marker this cell carries says
    "no verdict, another doubling owed" rather than claiming convergence.
    """
    q = q_mil / 1000.0
    r = r_mil / 1000.0
    stratum_of_date = {date: key for key, dates in tp_pools.items()
                       for date in dates}
    tp_keys = sorted(tp_pools)
    k_indices = repeat_k_indices(grid_policy, doublings=0)
    headline_k = k_indices[0]

    reference: dict | None = None
    reference_at: tuple[int, int] | None = None
    repeats_per_seed: dict[int, dict] = {}

    for master_seed in seeds:
        digests_by_k: dict[int, str] = {}
        stats_by_k: dict[str, dict[int, float | None]] = {
            "realized_precision": {}, "realized_recall": {},
            "n_selected": {}, "mixture_mean_pnl": {}}
        for k in k_indices:
            rng = repeat_rng(master_seed, theta, q_mil, r_mil, k, grid_policy)
            tp_dates = _select(tp_pools, tp_alloc, rng)
            selected_tp = _selected_tp_composition(tp_dates, stratum_of_date,
                                                   tp_keys)
            fp_block = fp_allocation_from_selected_tp(
                n_fp, selected_tp, fp_avail, fp_allocation)
            if reference is None:
                reference, reference_at = fp_block, (master_seed, k)
            elif (fp_block["fp_alloc"] != reference["fp_alloc"]
                    or fp_block["weights_selected_tp"]
                    != reference["weights_selected_tp"]):
                raise RuntimeError(
                    "fp_allocation_not_seed_stable: the selected-TP "
                    f"composition at (seed={master_seed}, k={k}) is "
                    f"{fp_block['weights_selected_tp']} -> FP "
                    f"{fp_block['fp_alloc']}, but at (seed="
                    f"{reference_at[0]}, k={reference_at[1]}) it was "
                    f"{reference['weights_selected_tp']} -> FP "
                    f"{reference['fp_alloc']}. The DR-3 basis is only "
                    "reportable once per cell BECAUSE the TP per-stratum "
                    "quotas are fixed by availability and the frozen totals "
                    "while the stream moves only WHICH day inside a stratum "
                    "is taken; if that no longer holds, the cell's single "
                    "`fp_allocation` block is a false disclosure — fail "
                    "closed rather than quoting one repeat's split as the "
                    "cell's")
            fp_dates = _select(fp_pools, fp_block["fp_alloc"], rng)
            row = _seed_report(q, r, tp_dates, fp_dates, tp_alloc,
                               fp_block["fp_alloc"], tp_pnl, fp_pnl,
                               n_tp_available, base_rate_p, n_year)
            if k == headline_k:
                point["per_seed"][master_seed] = row
            digests_by_k[k] = repeat_draw_digest(tp_dates, fp_dates)
            stats_by_k["realized_precision"][k] = row["realized_precision"]
            stats_by_k["realized_recall"][k] = row["realized_recall"]
            stats_by_k["n_selected"][k] = row["n_tp_actual"] + \
                row["n_fp_actual"]
            stats_by_k["mixture_mean_pnl"][k] = row["mixture_mean_pnl"]
        repeats_per_seed[master_seed] = {
            "digests_by_k": digests_by_k,
            "digest_of_digests": _digest_of_digests(digests_by_k),
            "dispersion": {name: _dispersion_or_none(values)
                           for name, values in stats_by_k.items()},
        }

    point["fp_allocation"] = {
        **reference,
        # the invariant was CHECKED, not assumed — these three fields say over
        # what it was checked, so "seed_stable: True" is a measurement.
        "seed_stable": True,
        "checked_seeds": [int(s) for s in seeds],
        "checked_repeats_per_seed": len(k_indices),
    }
    point["repeats"] = {
        "k_per_seed": int(grid_policy.k_per_seed),
        "k_start_index": int(grid_policy.k_start_index),
        "n_repeats_per_seed": len(k_indices),
        "doublings_used": 0,
        "headline_k": int(headline_k),
        "theta": float(theta),
        "theta_stream_key": theta_stream_key(theta),
        "per_seed": repeats_per_seed,
        "convergence": repeat_convergence_marker(
            grid_policy, doublings_used=0, mc_converged=None),
        "method": (
            "DR-5: K = "
            f"{grid_policy.k_per_seed} repeats per master seed per (q, r) "
            f"cell, k from {grid_policy.k_start_index}, each k on its OWN "
            "stream default_rng(SeedSequence([master_seed, GRID_STREAM_TAG, "
            "theta_milli, q_mil, r_mil, k])) — theta IS in the stream, so the "
            "two frozen thetas never share a repeat, and the set is "
            "prefix-nested under doubling (K -> 2K reproduces the first K "
            "repeats exactly). Per repeat: the TP selection is redrawn, the "
            "DR-3 FP allocation is recomputed from THAT repeat's selected-TP "
            "composition, then FP is drawn off the same stream (TP-then-FP, "
            "ascending stratum key — the frozen order). `digests_by_k` is a "
            "SHA-256 over the drawn dates ONLY (k is not in the preimage, so "
            "the digests evidence real k-variation); dispersion is the "
            "REALIZED cross-K spread with no tolerance and no verdict. This "
            "module runs doublings=0 and declares NO convergence verdict — "
            "the MC_METHOD_SPEC §5 four-rule battery at the MC wiring "
            "supplies `mc_converged`, a missing verdict counts as NOT "
            "converged, and an unconverged cell at the doubling cap is "
            f"marked `{MARK_INFEASIBLE_BY_CONVERGENCE}`."),
    }
