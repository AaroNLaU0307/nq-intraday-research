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
the caller. The `volatility_regime` axis is used but never DEFINED by the
frozen text (open decision DR-M6-B, pending an owner ruling), so this module
treats stratum tuples as OPAQUE keys: it groups, allocates and sorts by them
and attaches no meaning to their contents. Whatever the ruling picks, only the
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

from collections.abc import Mapping, Sequence
from decimal import ROUND_HALF_UP, Decimal

import numpy as np

from itsf.contracts import RESEARCH_BOOTSTRAP_SEEDS

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
    step 3. Its CONTENTS are opaque here (volatility_regime is DR-M6-B,
    pending): only the arity is structural.
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

def _method_string(seeds: tuple[int, ...], n_year: int) -> str:
    return (
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
        "volatility_regime definition is open decision DR-M6-B), per-stratum "
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


def build_grid(d_tp: Mapping[str, float], d_fp: Mapping[str, float],
               strata: Mapping[str, Sequence[object]], base_rate_p: float,
               master_seeds: Sequence[int] = RESEARCH_BOOTSTRAP_SEEDS,
               q_grid: Sequence[float] | None = None,
               r_grid: Sequence[float] | None = None,
               n_year: int = N_YEAR_TRADING_DAYS) -> dict:
    """Build the frozen Appendix A (q, r) grid for ONE engine × scenario.

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

    Returns
    -------
    {"grid": {"q0.35_r0.20": {... "per_seed": {seed: {...}},
                              "infeasible_by_sample": bool ...}},
     "n_tp_available": int, "n_fp_available": int, "method": str}
    """
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
                fp_avail, n_tp_available, n_fp_available, seeds, p, n_year)

    return {"grid": grid,
            "n_tp_available": n_tp_available,
            "n_fp_available": n_fp_available,
            "method": _method_string(seeds, n_year)}


def _grid_point(q_mil: int, r_mil: int, tp_pnl: Mapping[str, float],
                fp_pnl: Mapping[str, float],
                tp_pools: Mapping[str, tuple[str, ...]],
                fp_pools: Mapping[str, tuple[str, ...]],
                tp_avail: Mapping[str, int], fp_avail: Mapping[str, int],
                n_tp_available: int, n_fp_available: int,
                seeds: tuple[int, ...], base_rate_p: float,
                n_year: int) -> dict:
    """One (q, r) cell across all master seeds."""
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

    # allocation is seed-INDEPENDENT (frozen totals + availability only); the
    # seed decides WHICH days inside each stratum, never how many.
    tp_alloc = allocate(n_tp, tp_avail)
    fp_alloc = allocate(n_fp, fp_avail)
    for master_seed in seeds:
        rng = np.random.default_rng(
            [int(master_seed), GRID_STREAM_TAG, int(q_mil), int(r_mil)])
        tp_dates = _select(tp_pools, tp_alloc, rng)   # TP consumes the stream
        fp_dates = _select(fp_pools, fp_alloc, rng)   # ... then FP
        point["per_seed"][master_seed] = _seed_report(
            q, r, tp_dates, fp_dates, tp_alloc, fp_alloc, tp_pnl, fp_pnl,
            n_tp_available, base_rate_p, n_year)
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
