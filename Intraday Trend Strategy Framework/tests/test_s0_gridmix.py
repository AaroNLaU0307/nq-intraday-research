"""Synthetic checks for itsf.s0.gridmix (frozen S0 Appendix A grid).

SA-18 scope. Every population here is a hand-written dict of fabricated dates
and fabricated USD P&L: no real archive is touched, no clock is read, and the
only randomness comes out of the module under test, whose grid-point streams
derive exclusively from contracts.RESEARCH_BOOTSTRAP_SEEDS.

Centrepiece: `test_anti_ordering_permuting_pnl_leaves_selection_identical` —
the frozen Appendix A step 3 prohibition on letting any outcome (P&L, MFE,
|Y_cont|) touch day selection, which is what keeps the grid from degenerating
into a half-oracle.
"""
from __future__ import annotations

import inspect
import math

import pytest

from itsf import contracts
from itsf.s0 import gridmix

LOW = ("2010", "low", "none")
HIGH = ("2010", "high", "CPI")
LOW_KEY = "2010|low|none"
HIGH_KEY = "2010|high|CPI"


def make_populations(n_tp_low: int = 6, n_tp_high: int = 4,
                     n_fp_low: int = 12, n_fp_high: int = 8):
    """Fabricated D_TP / D_FP + the injected stratum mapping.

    TP days live in March, FP days in April, so a selected date's pool is
    visible on sight. P&L values are deterministic and deliberately ordered
    (TP ascending, FP descending) — nothing in the module may react to them.
    """
    d_tp: dict[str, float] = {}
    d_fp: dict[str, float] = {}
    strata: dict[str, tuple[str, str, str]] = {}
    for i in range(n_tp_low + n_tp_high):
        date = f"2010-03-{i + 1:02d}"
        d_tp[date] = 100.0 + 10.0 * i
        strata[date] = LOW if i < n_tp_low else HIGH
    for i in range(n_fp_low + n_fp_high):
        date = f"2010-04-{i + 1:02d}"
        d_fp[date] = -50.0 - 5.0 * i
        strata[date] = LOW if i < n_fp_low else HIGH
    return d_tp, d_fp, strata


# ---------------------------------------------------------------------------
# frozen grid axes and the seed mutation guard
# ---------------------------------------------------------------------------

def test_frozen_grid_axes_exact_no_float_drift():
    """# frozen: S0 Appendix A — q 0.35..0.75 step 0.05, r 0.20..0.80 step 0.10.

    Built from integer millis: naive float accumulation from 0.35 by 0.05 gets
    six of the nine q values wrong (0.39999999999999997, 0.7500000000000001,
    ...), which would then flow into a grid KEY and into n_fp.
    """
    assert gridmix.Q_GRID_MILLIS == (350, 400, 450, 500, 550, 600, 650, 700, 750)
    assert gridmix.R_GRID_MILLIS == (200, 300, 400, 500, 600, 700, 800)
    assert gridmix.N_YEAR_TRADING_DAYS == 252

    d_tp, d_fp, strata = make_populations()
    # single seed (7,) is cheaper than the frozen tuple and is not itself the
    # frozen tuple, so this goes through the private unchecked helper.
    out = gridmix._build_grid_unchecked(d_tp, d_fp, strata, base_rate_p=0.4,
                                        master_seeds=(7,))
    assert len(out["grid"]) == 9 * 7
    qs = sorted({p["target_precision"] for p in out["grid"].values()})
    rs = sorted({p["target_recall"] for p in out["grid"].values()})
    assert qs == [m / 1000 for m in gridmix.Q_GRID_MILLIS]
    assert rs == [m / 1000 for m in gridmix.R_GRID_MILLIS]

    naive, v = [], 0.35
    while v < 0.7501:
        naive.append(v)
        v += 0.05
    assert naive != qs                       # the drift this construction avoids
    assert "q0.75_r0.80" in out["grid"] and "q0.35_r0.20" in out["grid"]


def test_master_seed_default_is_the_contracts_constant():
    """Mutation guard. # frozen: S0 Appendix A step 3 seeds {7,13,31}."""
    params = inspect.signature(gridmix.build_grid).parameters
    assert params["master_seeds"].default is contracts.RESEARCH_BOOTSTRAP_SEEDS
    assert contracts.RESEARCH_BOOTSTRAP_SEEDS == (7, 13, 31)
    assert gridmix.GRID_STREAM_TAG != 0


def test_public_api_refuses_non_frozen_master_seeds():
    """# frozen: S0 Appendix A step 3 seeds {7,13,31}; IR DR-02 — the public
    `build_grid` refuses ANY other seed set, including a same-shape
    substitute like (1, 2, 3), rather than silently honouring it."""
    d_tp, d_fp, strata = make_populations()
    with pytest.raises(ValueError, match="DR-02"):
        gridmix.build_grid(d_tp, d_fp, strata, base_rate_p=0.4,
                           master_seeds=(1, 2, 3))


def test_public_api_accepts_the_frozen_seed_tuple():
    """The public `build_grid` still works normally for the frozen tuple,
    whether passed explicitly or left at its default."""
    d_tp, d_fp, strata = make_populations()
    explicit = gridmix.build_grid(
        d_tp, d_fp, strata, base_rate_p=0.4,
        master_seeds=contracts.RESEARCH_BOOTSTRAP_SEEDS,
        q_grid=[0.50], r_grid=[0.50])
    default = gridmix.build_grid(d_tp, d_fp, strata, base_rate_p=0.4,
                                 q_grid=[0.50], r_grid=[0.50])
    assert explicit["grid"] == default["grid"]
    assert set(explicit["grid"]["q0.50_r0.50"]["per_seed"]) == {7, 13, 31}


# ---------------------------------------------------------------------------
# frozen arithmetic: floor and ROUND_HALF_UP
# ---------------------------------------------------------------------------

def test_floor_n_tp_is_exact_where_float_multiplication_is_not():
    """# frozen: S0 Appendix A — n_tp = floor(r x N_TP_available).

    0.7 x 90 is exactly 63; in binary floats it is 62.99999999999999, so the
    naive expression loses a whole day.
    """
    assert gridmix.floor_n_tp(700, 90) == 63
    assert math.floor(0.7 * 90) == 62            # the trap being avoided
    assert gridmix.floor_n_tp(200, 10) == 2
    assert gridmix.floor_n_tp(300, 7) == 2       # floor(2.1)
    assert gridmix.floor_n_tp(800, 0) == 0


def test_round_half_up_is_not_bankers_rounding():
    """# frozen: S0 Appendix A — round_half_up, NOT python's round()."""
    assert gridmix.round_half_up(2.5) == 3 and round(2.5) == 2
    assert gridmix.round_half_up(0.5) == 1 and round(0.5) == 0
    assert gridmix.round_half_up(4.5) == 5 and round(4.5) == 4
    assert gridmix.round_half_up(1.4) == 1
    assert gridmix.round_half_up(3) == 3


def test_n_fp_half_boundary_cases_hand_computed():
    """# frozen: S0 Appendix A — n_fp = round_half_up(n_tp x (1-q)/q).

    q = 0.40, n_tp = 7 -> exactly 10.5 -> 11. Banker's rounding gives 10 and
    the float expression 3 x 0.6/0.4 = 4.499999999999999 gives 4 instead of 5,
    so both the decimal rule and the exact-rational evaluation are pinned here.
    """
    assert gridmix.n_fp_for(7, 400) == 11
    assert round(7 * (1 - 0.4) / 0.4) == 10                 # banker's trap
    assert gridmix.n_fp_for(3, 400) == 5
    assert round(3 * (1 - 0.4) / 0.4) == 4                  # float-drift trap
    assert gridmix.n_fp_for(10, 800) == 3                   # exactly 2.5 -> 3
    assert gridmix.n_fp_for(10, 500) == 10                  # q = 0.5 -> 1:1
    assert gridmix.n_fp_for(2, 350) == 4                    # 3.714... -> 4
    assert gridmix.n_fp_for(0, 350) == 0


# ---------------------------------------------------------------------------
# stratified allocation
# ---------------------------------------------------------------------------

def test_largest_remainder_shares_and_key_tie_break():
    """Proportional shares, largest remainder, ties by ascending stratum key
    (disclosed engineering convention)."""
    weights = {LOW_KEY: 6, HIGH_KEY: 4}
    assert gridmix.largest_remainder(5, weights) == {LOW_KEY: 3, HIGH_KEY: 2}
    # 3 x 6/10 = 1.8 and 3 x 4/10 = 1.2 -> bases 1/1, the leftover unit goes to
    # the larger remainder (0.8 > 0.2)
    assert gridmix.largest_remainder(3, weights) == {LOW_KEY: 2, HIGH_KEY: 1}
    # exact tie -> ascending key wins ("2010|high|CPI" < "2010|low|none")
    assert gridmix.largest_remainder(1, {LOW_KEY: 5, HIGH_KEY: 5}) == {
        HIGH_KEY: 1, LOW_KEY: 0}


def test_allocation_on_two_strata_exact_counts():
    """TP pool 6 low / 4 high, r = 0.50 -> n_tp = 5 -> exactly 3 low + 2 high,
    and the selected dates really come from those strata."""
    d_tp, d_fp, strata = make_populations()
    # single seed (7,) is not the frozen tuple -> private unchecked helper.
    out = gridmix._build_grid_unchecked(d_tp, d_fp, strata, base_rate_p=0.4,
                                        master_seeds=(7,), q_grid=[0.50],
                                        r_grid=[0.50])
    point = out["grid"]["q0.50_r0.50"]
    assert point["n_tp_target"] == 5 and point["n_fp_target"] == 5
    seed_block = point["per_seed"][7]
    assert seed_block["allocation_tp"] == {HIGH_KEY: 2, LOW_KEY: 3}
    assert seed_block["allocation_fp"] == {HIGH_KEY: 2, LOW_KEY: 3}
    low_tp = [d for d in seed_block["tp_dates"] if strata[d] == LOW]
    high_tp = [d for d in seed_block["tp_dates"] if strata[d] == HIGH]
    assert len(low_tp) == 3 and len(high_tp) == 2
    # allocation is seed-independent: only WHICH days move with the seed
    every = gridmix.build_grid(d_tp, d_fp, strata, base_rate_p=0.4,
                               q_grid=[0.50], r_grid=[0.50])["grid"][
                                   "q0.50_r0.50"]["per_seed"]
    assert {s: b["allocation_tp"] for s, b in every.items()} == {
        s: seed_block["allocation_tp"] for s in (7, 13, 31)}


def test_allocate_disjoint_weights_support_raises_not_short():
    """# hardening: `weights` keyed ENTIRELY off strata absent from
    `available` used to silently return every stratum at 0 (sum 0 !=
    required) — the initial weight-driven `active` set was empty from the
    start, so the redistribution loop never ran even once. Now this is a
    caller error (e.g. mismatched stratum keys between the two mappings) and
    must raise, never return a short allocation."""
    available = {"a": 5, "b": 5}
    with pytest.raises(ValueError):
        gridmix.allocate(6, available, weights={"x": 10, "y": 20})
    with pytest.raises(ValueError):
        gridmix.allocate(1, available, weights={"nonexistent_key": 999})
    # required == 0 is never ambiguous, even with fully-disjoint weights
    assert gridmix.allocate(0, available, weights={"x": 10}) == {
        "a": 0, "b": 0}


def test_allocate_guarantees_sum_equals_required():
    """# guarantee: `allocate` never returns sum(allocation) != required —
    either it equals required, or the call raised."""
    available = {"a": 2, "b": 5, "c": 5}
    alloc = gridmix.allocate(9, available, weights={"a": 1, "b": 1, "c": 1})
    assert sum(alloc.values()) == 9
    alloc_default = gridmix.allocate(7, available)
    assert sum(alloc_default.values()) == 7
    # a partial-overlap weights map (some strata weighted, others not) still
    # reaches the full requirement via the availability-based redistribution
    # fallback, not a raise — only FULLY disjoint support raises.
    alloc_partial = gridmix.allocate(10, available, weights={"a": 1})
    assert sum(alloc_partial.values()) == 10


def test_shortfall_redistributes_over_remaining_strata():
    """# frozen: S0 Appendix A — 缺额按其余层的可用日数比例重新分配.

    Availability 2/5/5 with a basis that asks the small stratum for 6 of 12:
    it is capped at its 2 available days and the 4-day shortfall is re-split
    over the remaining strata in proportion to THEIR available days (5:5).
    """
    available = {"a": 2, "b": 5, "c": 5}
    alloc = gridmix.allocate(12, available, weights={"a": 6, "b": 3, "c": 3})
    assert alloc == {"a": 2, "b": 5, "c": 5}
    alloc = gridmix.allocate(8, available, weights={"a": 6, "b": 3, "c": 3})
    assert alloc == {"a": 2, "b": 3, "c": 3}
    assert sum(alloc.values()) == 8
    for key, taken in alloc.items():
        assert taken <= available[key]
    with pytest.raises(ValueError):
        gridmix.allocate(13, available)      # total short -> caller marks it


def test_infeasible_by_sample_is_marked_and_still_reported():
    """# frozen: S0 Appendix A — 全部层合计仍不足时标记 infeasible_by_sample，
    跳过选择但完整报告."""
    d_tp, _d_fp, strata = make_populations()
    small_fp = {"2010-04-01": -10.0, "2010-04-02": -20.0}
    out = gridmix.build_grid(d_tp, small_fp, strata, base_rate_p=0.4,
                             q_grid=[0.35], r_grid=[0.80])
    point = out["grid"]["q0.35_r0.80"]
    assert point["n_tp_target"] == 8
    assert point["n_fp_target"] == 15            # round_half_up(8 x 0.65/0.35)
    assert point["infeasible_by_sample"] is True
    assert point["per_seed"] == {}               # selection skipped
    # still reported in full
    assert point["target_precision"] == 0.35 and point["target_recall"] == 0.80
    assert point["F_expected"] == pytest.approx(0.4 * 0.8 * 252 / 0.35)
    assert "infeasible_reason" in point
    assert out["n_fp_available"] == 2


# ---------------------------------------------------------------------------
# randomness: determinism, seed separation, and the anti-ordering rule
# ---------------------------------------------------------------------------

def test_determinism_per_seed_and_grid_point():
    d_tp, d_fp, strata = make_populations()
    kwargs = dict(base_rate_p=0.4, q_grid=[0.35, 0.50], r_grid=[0.30, 0.60])
    a = gridmix.build_grid(d_tp, d_fp, strata, **kwargs)
    b = gridmix.build_grid(d_tp, d_fp, strata, **kwargs)
    assert a["grid"] == b["grid"]
    # a grid point's stream depends on (seed, q_mil, r_mil) only, so the same
    # cell computed inside a DIFFERENT axis set is byte-identical
    single = gridmix.build_grid(d_tp, d_fp, strata, base_rate_p=0.4,
                                q_grid=[0.50], r_grid=[0.60])
    assert single["grid"]["q0.50_r0.60"] == a["grid"]["q0.50_r0.60"]


def test_different_seeds_select_different_days():
    d_tp, d_fp, strata = make_populations(n_tp_low=20, n_tp_high=20,
                                          n_fp_low=20, n_fp_high=20)
    point = gridmix.build_grid(d_tp, d_fp, strata, base_rate_p=0.4,
                               q_grid=[0.50], r_grid=[0.50],
                               )["grid"]["q0.50_r0.50"]
    picks = {seed: block["tp_dates"] for seed, block in point["per_seed"].items()}
    assert picks[7] != picks[13] and picks[7] != picks[31]
    assert picks[13] != picks[31]
    for dates in picks.values():             # same size, different membership
        assert len(dates) == point["n_tp_target"] == 20


def test_anti_ordering_permuting_pnl_leaves_selection_identical():
    """# frozen: S0 Appendix A step 3 — 禁止按未来 P&L / MFE / Y_cont 幅度
    或任何结果标签排序选择.

    Same dates, same strata, P&L values permuted (here: reversed, which swaps
    the best and worst day of each population). Every selected date must be
    unchanged for every seed and every grid point; only the descriptive
    mixture mean may move.
    """
    d_tp, d_fp, strata = make_populations()
    base = gridmix.build_grid(d_tp, d_fp, strata, base_rate_p=0.4)

    permuted_tp = dict(zip(d_tp.keys(), reversed(list(d_tp.values()))))
    permuted_fp = dict(zip(d_fp.keys(), reversed(list(d_fp.values()))))
    assert permuted_tp != d_tp and permuted_fp != d_fp
    shuffled = gridmix.build_grid(permuted_tp, permuted_fp, strata,
                                  base_rate_p=0.4)

    for key, point in base["grid"].items():
        other = shuffled["grid"][key]
        assert point["infeasible_by_sample"] == other["infeasible_by_sample"]
        for seed, block in point["per_seed"].items():
            assert block["tp_dates"] == other["per_seed"][seed]["tp_dates"], key
            assert block["fp_dates"] == other["per_seed"][seed]["fp_dates"], key
            assert block["day_markers"] == other["per_seed"][seed]["day_markers"]


# ---------------------------------------------------------------------------
# reporting contract
# ---------------------------------------------------------------------------

def test_target_and_realized_both_reported_on_a_rounding_mismatch():
    """# frozen: S0 Appendix A step 4 — 强制输出实际值; MC 使用 realized.

    7 TP days, q = 0.35, r = 0.30: n_tp = floor(2.1) = 2 and
    n_fp = round_half_up(2 x 0.65/0.35) = round_half_up(3.714) = 4, so the
    realized precision 2/6 = 0.3333 and realized recall 2/7 = 0.2857 both miss
    their targets and must be reported next to them.
    """
    d_tp, d_fp, strata = make_populations(n_tp_low=4, n_tp_high=3)
    point = gridmix.build_grid(d_tp, d_fp, strata, base_rate_p=0.4,
                               q_grid=[0.35], r_grid=[0.30],
                               )["grid"]["q0.35_r0.30"]
    assert point["n_tp_target"] == 2 and point["n_fp_target"] == 4
    for block in point["per_seed"].values():
        assert block["target_precision"] == 0.35
        assert block["target_recall"] == 0.30
        assert block["realized_precision"] == pytest.approx(2 / 6)
        assert block["realized_recall"] == pytest.approx(2 / 7)
        assert block["n_tp_actual"] == 2 and block["n_fp_actual"] == 4


def test_f_expected_formula_pinned():
    """# frozen: S0 Appendix A — F(q, r) = p x r x N / q, N ≈ 252."""
    d_tp, d_fp, strata = make_populations()
    out = gridmix.build_grid(d_tp, d_fp, strata, base_rate_p=0.4,
                             q_grid=[0.35], r_grid=[0.30])
    point = out["grid"]["q0.35_r0.30"]
    assert point["F_expected"] == pytest.approx(86.4)     # 0.4*0.3*252/0.35
    for block in point["per_seed"].values():
        assert block["F_expected"] == point["F_expected"]
    assert gridmix.f_expected(0.5, 0.8, 0.5, 252) == pytest.approx(201.6)


def test_selection_pools_markers_and_mixture_mean():
    """TP only from D_TP, FP only from D_FP, no repeats, markers chronological,
    and the descriptive mixture mean is the mean of the selected days."""
    d_tp, d_fp, strata = make_populations()
    point = gridmix.build_grid(d_tp, d_fp, strata, base_rate_p=0.4,
                               q_grid=[0.50], r_grid=[0.60],
                               )["grid"]["q0.50_r0.60"]
    for block in point["per_seed"].values():
        tp_dates, fp_dates = block["tp_dates"], block["fp_dates"]
        assert set(tp_dates) <= set(d_tp) and not set(tp_dates) & set(d_fp)
        assert set(fp_dates) <= set(d_fp) and not set(fp_dates) & set(d_tp)
        assert len(set(tp_dates)) == len(tp_dates)      # without replacement
        assert len(set(fp_dates)) == len(fp_dates)
        assert tp_dates == sorted(tp_dates) and fp_dates == sorted(fp_dates)

        markers = block["day_markers"]
        assert [d for d, _m in markers] == sorted(d for d, _m in markers)
        assert {d for d, m in markers if m == gridmix.MARK_TP} == set(tp_dates)
        assert {d for d, m in markers if m == gridmix.MARK_FP} == set(fp_dates)
        assert len(markers) == len(tp_dates) + len(fp_dates)

        selected = [d_tp[d] for d in tp_dates] + [d_fp[d] for d in fp_dates]
        assert block["mixture_mean_pnl"] == pytest.approx(
            sum(selected) / len(selected))


def test_missing_stratum_entry_fails_closed():
    """# frozen: S0 Appendix A step 3 — every selectable day must be
    stratifiable; a gap in the injected mapping is never a silent pass."""
    d_tp, d_fp, strata = make_populations()
    incomplete = {k: v for k, v in strata.items() if k != "2010-03-01"}
    with pytest.raises(ValueError):
        gridmix.build_grid(d_tp, d_fp, incomplete, base_rate_p=0.4)
    wrong_arity = dict(strata)
    wrong_arity["2010-03-01"] = ("2010", "low")
    with pytest.raises(ValueError):
        gridmix.build_grid(d_tp, d_fp, wrong_arity, base_rate_p=0.4)


def test_degenerate_inputs_fail_closed():
    d_tp, d_fp, strata = make_populations()
    with pytest.raises(ValueError):                     # empty D_TP
        gridmix.build_grid({}, d_fp, strata, base_rate_p=0.4)
    overlapping = dict(d_fp)
    overlapping["2010-03-01"] = -1.0                    # day in BOTH populations
    with pytest.raises(ValueError):
        gridmix.build_grid(d_tp, overlapping, strata, base_rate_p=0.4)
    bad_pnl = dict(d_tp)
    bad_pnl["2010-03-01"] = float("nan")
    with pytest.raises(ValueError):
        gridmix.build_grid(bad_pnl, d_fp, strata, base_rate_p=0.4)
    with pytest.raises(ValueError):
        gridmix.build_grid(d_tp, d_fp, strata, base_rate_p=1.4)
    with pytest.raises(ValueError):
        gridmix.build_grid(d_tp, d_fp, strata, base_rate_p=0.4, n_year=0)
    # empty seeds exercises _validated_seeds itself (private unchecked helper;
    # () is not the frozen tuple anyway, so the public entry would refuse it
    # for the WRONG reason first).
    with pytest.raises(ValueError):
        gridmix._build_grid_unchecked(d_tp, d_fp, strata, base_rate_p=0.4,
                                      master_seeds=())
    with pytest.raises(ValueError):
        gridmix.build_grid(d_tp, d_fp, strata, base_rate_p=0.4, q_grid=[1.5])


def test_method_string_discloses_the_whole_recipe():
    d_tp, d_fp, strata = make_populations()
    method = gridmix.build_grid(d_tp, d_fp, strata, base_rate_p=0.4,
                                q_grid=[0.50], r_grid=[0.50])["method"]
    for fragment in ("round_half_up", "banker", "largest-remainder",
                     "UNIFORM WITHOUT REPLACEMENT", "infeasible_by_sample",
                     "magnitude-", "[7, 13, 31]", "GRID_STREAM_TAG",
                     "RULED by DR-2", "realized", "N = 252",
                     "no H1 performance claim"):
        assert fragment in method, fragment
