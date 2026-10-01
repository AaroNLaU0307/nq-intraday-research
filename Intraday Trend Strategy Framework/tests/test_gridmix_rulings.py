"""DR-3 + DR-5 (Aaron 2026-08-10) rulings, as consumed by itsf.s0.gridmix.

The ruled instances are IMPORTED from `itsf.contracts.aaron_ruled_methods()`;
no ruling literal is restated in this file. Every stratum map, count and value
below is fabricated — no archive is read, no clock is touched, and the only
randomness comes out of the module under test, whose streams derive
exclusively from contracts.RESEARCH_BOOTSTRAP_SEEDS.

Sibling file: tests/test_s0_gridmix.py covers the frozen Appendix-A grid
itself (axes, rounding, anti-ordering). This file covers ONLY the two 2026-08-10
rulings the module newly consumes.
"""
from __future__ import annotations

import dataclasses
import inspect

import numpy as np
import pytest

from itsf import contracts
from itsf.contracts import aaron_ruled_methods
from itsf.s0 import gridmix

RULED = aaron_ruled_methods()
FP_METHOD = RULED.fp_allocation
GRID_POLICY = RULED.grid_policy

THETA_PRIMARY = 0.5
THETA_SECONDARY = 0.3
Q_MIL = 350
R_MIL = 200


# ===========================================================================
# DR-3 — FP allocation follows the SELECTED TP composition (Hamilton)
# ===========================================================================

def test_dr3_hamilton_exact_split_on_the_selected_tp_composition():
    """n_fp = 7 over selected TP {A:5, B:3, C:2} (n_tp = 10), ample FP supply.

    base   = floor(7*w/10) = A 3.5->3, B 2.1->2, C 1.4->1  (sum 6)
    remainders 5, 1, 4 -> the single leftover unit goes to A.
    """
    out = gridmix.fp_allocation_from_selected_tp(
        7, {"A": 5, "B": 3, "C": 2}, {"A": 10, "B": 10, "C": 10}, FP_METHOD)
    assert out["fp_alloc"] == {"A": 4, "B": 2, "C": 1}
    assert out["n_tp_selected"] == 10
    assert out["shortfall_redistributed"] == 0
    assert sum(out["fp_alloc"].values()) == 7


def test_dr3_weights_are_the_selected_tp_not_the_full_tp_pool():
    """MUTATION GUARD: the full-pool composition gives a DIFFERENT split.

    Selected TP is {A:5, B:3, C:2} while the full D_TP pool is {A:2, B:3,
    C:15}; apportioning n_fp on the pool would return {A:1, B:1, C:5}.
    """
    selected = {"A": 5, "B": 3, "C": 2}
    full_pool = {"A": 2, "B": 3, "C": 15}
    avail = {"A": 10, "B": 10, "C": 10}
    ruled = gridmix.fp_allocation_from_selected_tp(7, selected, avail,
                                                   FP_METHOD)
    on_pool = gridmix.fp_allocation_from_selected_tp(7, full_pool, avail,
                                                     FP_METHOD)
    assert ruled["fp_alloc"] == {"A": 4, "B": 2, "C": 1}
    assert on_pool["fp_alloc"] == {"A": 1, "B": 1, "C": 5}
    assert ruled["fp_alloc"] != on_pool["fp_alloc"]


def test_dr3_tie_break_is_ascending_stratum_key():
    """Equal remainders: n_fp = 2 over {A:1, B:1, C:1} -> A and B, never C."""
    out = gridmix.fp_allocation_from_selected_tp(
        2, {"A": 1, "B": 1, "C": 1}, {"A": 5, "B": 5, "C": 5}, FP_METHOD)
    assert out["fp_alloc"] == {"A": 1, "B": 1, "C": 0}
    # MUTATION GUARD: a descending tie-break would produce {B:1, C:1}
    assert out["fp_alloc"] != {"A": 0, "B": 1, "C": 1}


def test_dr3_fp_only_strata_carry_weight_zero():
    """A stratum with FP days but no SELECTED TP day gets nothing."""
    out = gridmix.fp_allocation_from_selected_tp(
        3, {"A": 4}, {"A": 10, "Z": 10}, FP_METHOD)
    assert out["fp_alloc"] == {"A": 3, "Z": 0}
    assert out["weights_selected_tp"] == {"A": 4, "Z": 0}
    assert out["deviations"]["Z"]["target_tp_share"] == 0.0
    assert out["deviations"]["Z"]["realized_fp_share"] == 0.0


def test_dr3_shortfall_redistributes_over_remaining_strata_by_fp_availability():
    """The frozen-literal rule, now reachable under basis 'B'.

    n_fp = 10, selected TP {A:5, B:3, C:2} (shares 5/3/2), FP availability
    {A:20, B:0, C:20}. B can supply nothing, so its 3 units are re-split over
    A and C in proportion to THEIR FP availability (20:20) -> 2 and 1 after
    the ascending-key tie-break on equal remainders.
    """
    out = gridmix.fp_allocation_from_selected_tp(
        10, {"A": 5, "B": 3, "C": 2}, {"A": 20, "B": 0, "C": 20}, FP_METHOD)
    assert out["fp_alloc"] == {"A": 7, "B": 0, "C": 3}
    assert out["shortfall_redistributed"] == 3
    assert sum(out["fp_alloc"].values()) == 10


def test_dr3_deviations_are_reported_for_disclosure():
    out = gridmix.fp_allocation_from_selected_tp(
        10, {"A": 5, "B": 3, "C": 2}, {"A": 20, "B": 0, "C": 20}, FP_METHOD)
    dev = out["deviations"]
    assert dev["A"]["target_tp_share"] == pytest.approx(0.5)
    assert dev["A"]["realized_fp_share"] == pytest.approx(0.7)
    assert dev["A"]["deviation"] == pytest.approx(0.2)
    assert dev["B"]["deviation"] == pytest.approx(-0.3)
    assert dev["C"]["deviation"] == pytest.approx(0.1)
    assert out["max_abs_deviation"] == pytest.approx(0.3)
    assert dev["B"]["fp_available"] == 0 and dev["B"]["fp_allocated"] == 0


def test_dr3_partial_shortfall_when_a_stratum_is_merely_short():
    """A stratum that can supply SOME of its share is capped at what it has.

    n_fp = 10, shares 5/3/2, availability {A:20, B:1, C:20}. Pass 1 places
    A 5, B 1 (capped), C 2 -> 2 units short. Pass 2 re-splits those 2 over the
    strata that still have room (A and C) in proportion to their FP
    availability 20:20 -> one each.
    """
    out = gridmix.fp_allocation_from_selected_tp(
        10, {"A": 5, "B": 3, "C": 2}, {"A": 20, "B": 1, "C": 20}, FP_METHOD)
    assert out["fp_alloc"] == {"A": 6, "B": 1, "C": 3}
    assert out["shortfall_redistributed"] == 2
    assert sum(out["fp_alloc"].values()) == 10


def test_dr3_conservation_holds_across_a_sweep_and_is_hard_asserted():
    avail = {"A": 6, "B": 0, "C": 4, "D": 9}
    weights = {"A": 5, "B": 3, "C": 2, "E": 7}
    for n_fp in range(0, sum(avail.values()) + 1):
        out = gridmix.fp_allocation_from_selected_tp(n_fp, weights, avail,
                                                     FP_METHOD)
        assert sum(out["fp_alloc"].values()) == n_fp, n_fp
        for key, taken in out["fp_alloc"].items():
            assert 0 <= taken <= avail.get(key, 0), (n_fp, key)
    with pytest.raises(RuntimeError, match="conservation_violated"):
        gridmix.assert_fp_conservation({"A": 3, "B": 0}, 4)


def test_dr3_total_shortage_is_infeasible_by_sample_before_any_allocation():
    with pytest.raises(ValueError,
                       match=r"fp_allocation_infeasible_by_sample:5>3"):
        gridmix.fp_allocation_from_selected_tp(
            5, {"A": 1, "B": 1}, {"A": 2, "B": 1}, FP_METHOD)


def test_dr3_zero_n_fp_is_a_legal_all_zero_allocation():
    out = gridmix.fp_allocation_from_selected_tp(
        0, {"A": 5}, {"A": 3, "B": 2}, FP_METHOD)
    assert out["fp_alloc"] == {"A": 0, "B": 0}
    assert out["max_abs_deviation"] is None


def test_dr3_no_selected_tp_weight_fails_closed():
    with pytest.raises(ValueError, match="fp_allocation_no_selected_tp_weight"):
        gridmix.fp_allocation_from_selected_tp(3, {}, {"A": 5}, FP_METHOD)


def test_dr3_unruled_basis_a_or_c_is_refused():
    for basis in ("A", "C", "", "b"):
        method = dataclasses.replace(FP_METHOD, basis=basis)
        with pytest.raises(ValueError,
                           match=f"fp_allocation_basis_not_ruled:{basis}"):
            gridmix.fp_allocation_from_selected_tp(
                1, {"A": 1}, {"A": 1}, method)


def test_dr3_unruled_weight_source_or_shortfall_rule_is_refused():
    bad_weight = dataclasses.replace(FP_METHOD,
                                     weight_source="full_tp_pool_composition")
    with pytest.raises(ValueError, match="fp_allocation_weight_source_not_ruled"):
        gridmix.fp_allocation_from_selected_tp(1, {"A": 1}, {"A": 1},
                                               bad_weight)
    bad_shortfall = dataclasses.replace(FP_METHOD,
                                        shortfall_rule="drop_the_shortfall")
    with pytest.raises(ValueError,
                       match="fp_allocation_shortfall_rule_not_ruled"):
        gridmix.fp_allocation_from_selected_tp(1, {"A": 1}, {"A": 1},
                                               bad_shortfall)


def test_dr3_method_object_and_count_types_are_pinned():
    with pytest.raises(ValueError, match="not_a_FpAllocationMethod"):
        gridmix.fp_allocation_from_selected_tp(1, {"A": 1}, {"A": 1}, object())
    with pytest.raises(ValueError, match="selected_tp_value_not_an_int"):
        gridmix.fp_allocation_from_selected_tp(1, {"A": 1.5}, {"A": 1},
                                               FP_METHOD)
    with pytest.raises(ValueError, match="fp_available_value_negative"):
        gridmix.fp_allocation_from_selected_tp(1, {"A": 1}, {"A": -1},
                                               FP_METHOD)
    with pytest.raises(ValueError, match="fp_allocation_n_fp_negative"):
        gridmix.fp_allocation_from_selected_tp(-1, {"A": 1}, {"A": 1},
                                               FP_METHOD)


def test_dr3_dispatch_keys_match_the_contracts_ruling():
    assert gridmix.FP_ALLOCATION_BASIS_B == FP_METHOD.basis
    assert gridmix.FP_ALLOCATION_WEIGHT_SOURCE == FP_METHOD.weight_source
    assert gridmix.FP_ALLOCATION_SHORTFALL_RULE == FP_METHOD.shortfall_rule


# ===========================================================================
# DR-5 — per-cell repeats: K per seed, theta in the stream, doubling cap
# ===========================================================================

def _small_policy(**overrides):
    """The ruled policy with a cheap K, so a doubling test stays fast."""
    return dataclasses.replace(GRID_POLICY, k_per_seed=4, **overrides)


def _draws(rng, n=3):
    return rng.random(n).tolist()


def test_dr5_k_indices_start_at_the_policy_start_index():
    ks = gridmix.repeat_k_indices(GRID_POLICY)
    assert len(ks) == GRID_POLICY.k_per_seed
    assert ks[0] == GRID_POLICY.k_start_index
    assert ks == tuple(range(GRID_POLICY.k_start_index,
                             GRID_POLICY.k_start_index
                             + GRID_POLICY.k_per_seed))


def test_dr5_doubling_grows_the_k_range_and_the_cap_is_enforced():
    doubled = gridmix.repeat_k_indices(GRID_POLICY, doublings=1)
    assert len(doubled) == 2 * GRID_POLICY.k_per_seed
    capped = gridmix.repeat_k_indices(GRID_POLICY,
                                      doublings=GRID_POLICY.max_doublings)
    assert len(capped) == GRID_POLICY.k_per_seed * 2 ** GRID_POLICY.max_doublings
    with pytest.raises(ValueError, match="grid_doublings_exceed_max"):
        gridmix.repeat_k_indices(GRID_POLICY,
                                 doublings=GRID_POLICY.max_doublings + 1)


def test_dr5_repeat_streams_are_prefix_nested_under_doubling():
    """K -> 2K keeps the FIRST K repeats byte-identical (per-k streams)."""
    policy = _small_policy()
    first = {k: _draws(rng) for k, rng in gridmix.repeat_rngs(
        7, THETA_PRIMARY, Q_MIL, R_MIL, policy).items()}
    doubled = {k: _draws(rng) for k, rng in gridmix.repeat_rngs(
        7, THETA_PRIMARY, Q_MIL, R_MIL, policy, doublings=1).items()}
    assert len(first) == 4 and len(doubled) == 8
    for k, values in first.items():
        assert doubled[k] == values, k
    assert set(doubled) - set(first) == {4, 5, 6, 7}


def test_dr5_theta_is_in_the_stream():
    """Two thetas, everything else identical -> DIFFERENT draws."""
    policy = _small_policy()
    a = gridmix.repeat_rng(7, THETA_PRIMARY, Q_MIL, R_MIL, 0, policy)
    b = gridmix.repeat_rng(7, THETA_SECONDARY, Q_MIL, R_MIL, 0, policy)
    assert _draws(a) != _draws(b)
    # ... and the same theta reproduces exactly
    c = gridmix.repeat_rng(7, THETA_PRIMARY, Q_MIL, R_MIL, 0, policy)
    d = gridmix.repeat_rng(7, THETA_PRIMARY, Q_MIL, R_MIL, 0, policy)
    assert _draws(c) == _draws(d)


def test_dr5_mutation_dropping_theta_would_collapse_the_two_thetas():
    """MUTATION GUARD, shown: without the theta component the two thetas draw
    the IDENTICAL repeat, so the per-theta grids stop being independent."""
    policy = _small_policy()
    ruled_a = gridmix.repeat_stream_entropy(7, THETA_PRIMARY, Q_MIL, R_MIL, 0,
                                            policy)
    ruled_b = gridmix.repeat_stream_entropy(7, THETA_SECONDARY, Q_MIL, R_MIL,
                                            0, policy)
    assert ruled_a != ruled_b
    without_theta_a = [x for i, x in enumerate(ruled_a) if i != 2]
    without_theta_b = [x for i, x in enumerate(ruled_b) if i != 2]
    assert without_theta_a == without_theta_b
    mutated_a = np.random.default_rng(np.random.SeedSequence(without_theta_a))
    mutated_b = np.random.default_rng(np.random.SeedSequence(without_theta_b))
    assert _draws(mutated_a) == _draws(mutated_b)


def test_dr5_stream_entropy_is_exactly_the_ruled_tuple():
    entropy = gridmix.repeat_stream_entropy(7, THETA_PRIMARY, Q_MIL, R_MIL, 0,
                                            GRID_POLICY)
    assert entropy == [7, gridmix.GRID_STREAM_TAG, 500, Q_MIL, R_MIL, 0]
    # every component moves the stream
    for changed in ([13, gridmix.GRID_STREAM_TAG, 500, Q_MIL, R_MIL, 0],
                    [7, gridmix.GRID_STREAM_TAG, 300, Q_MIL, R_MIL, 0],
                    [7, gridmix.GRID_STREAM_TAG, 500, 400, R_MIL, 0],
                    [7, gridmix.GRID_STREAM_TAG, 500, Q_MIL, 300, 0],
                    [7, gridmix.GRID_STREAM_TAG, 500, Q_MIL, R_MIL, 1]):
        assert changed != entropy


def test_dr5_stream_includes_theta_false_is_refused():
    policy = dataclasses.replace(GRID_POLICY, stream_includes_theta=False)
    with pytest.raises(ValueError,
                       match="grid_stream_includes_theta_not_ruled:False"):
        gridmix.repeat_k_indices(policy)
    with pytest.raises(ValueError,
                       match="grid_stream_includes_theta_not_ruled:False"):
        gridmix.repeat_stream_entropy(7, THETA_PRIMARY, Q_MIL, R_MIL, 0,
                                      policy)


def test_dr5_unruled_convergence_rule_and_bad_policy_values_are_refused():
    bad_rule = dataclasses.replace(GRID_POLICY,
                                   convergence_rule="mc_spec_s5_here")
    with pytest.raises(ValueError, match="grid_convergence_rule_not_ruled"):
        gridmix.repeat_k_indices(bad_rule)
    with pytest.raises(ValueError, match="not_a_GridRepeatPolicy"):
        gridmix.repeat_k_indices(object())
    with pytest.raises(ValueError, match="grid_master_seed_not_a_research_seed"):
        gridmix.repeat_stream_entropy(5, THETA_PRIMARY, Q_MIL, R_MIL, 0,
                                      GRID_POLICY)
    with pytest.raises(ValueError, match="grid_q_mil_out_of_range"):
        gridmix.repeat_stream_entropy(7, THETA_PRIMARY, 0, R_MIL, 0,
                                      GRID_POLICY)
    with pytest.raises(ValueError, match="grid_k_below_start_index"):
        gridmix.repeat_stream_entropy(7, THETA_PRIMARY, Q_MIL, R_MIL, -1,
                                      GRID_POLICY)


def test_dr5_repeat_api_takes_the_policy_explicitly():
    for fn in (gridmix.repeat_k_indices, gridmix.repeat_stream_entropy,
               gridmix.repeat_rng, gridmix.repeat_rngs,
               gridmix.repeat_convergence_marker):
        assert "policy" in inspect.signature(fn).parameters, fn.__name__


def test_dr5_cross_k_dispersion_reports_realized_spread_only():
    disp = gridmix.cross_k_dispersion({0: 1.0, 1: 3.0, 2: 2.0})
    assert disp == {"n_k": 3, "k_min": 0, "k_max": 2, "min": 1.0, "max": 3.0,
                    "spread": 2.0, "mean": 2.0,
                    "values_by_k": {0: 1.0, 1: 3.0, 2: 2.0}}
    # no verdict, no tolerance, no marker anywhere in the payload
    assert gridmix.MARK_INFEASIBLE_BY_CONVERGENCE not in disp
    assert "converged" not in disp
    with pytest.raises(ValueError, match="non_empty_mapping"):
        gridmix.cross_k_dispersion({})
    with pytest.raises(ValueError, match="cross_k_dispersion_non_finite"):
        gridmix.cross_k_dispersion({0: float("nan")})


def test_dr5_convergence_marker_fails_closed_at_the_doubling_cap():
    cap = GRID_POLICY.max_doublings
    converged = gridmix.repeat_convergence_marker(GRID_POLICY,
                                                  doublings_used=cap,
                                                  mc_converged=True)
    assert converged[gridmix.MARK_INFEASIBLE_BY_CONVERGENCE] is False
    assert converged["must_double_again"] is False
    assert converged["reason"] is None

    unconverged = gridmix.repeat_convergence_marker(GRID_POLICY,
                                                    doublings_used=cap,
                                                    mc_converged=False)
    assert unconverged[gridmix.MARK_INFEASIBLE_BY_CONVERGENCE] is True
    assert unconverged["must_double_again"] is False

    # a MISSING verdict is treated exactly like "not converged"
    no_verdict = gridmix.repeat_convergence_marker(GRID_POLICY,
                                                   doublings_used=cap,
                                                   mc_converged=None)
    assert no_verdict[gridmix.MARK_INFEASIBLE_BY_CONVERGENCE] is True

    below_cap = gridmix.repeat_convergence_marker(GRID_POLICY,
                                                  doublings_used=cap - 1,
                                                  mc_converged=False)
    assert below_cap[gridmix.MARK_INFEASIBLE_BY_CONVERGENCE] is False
    assert below_cap["must_double_again"] is True
    assert below_cap["k_per_seed_realized"] == (
        GRID_POLICY.k_per_seed * 2 ** (cap - 1))


def test_dr5_convergence_marker_rejects_out_of_range_and_bad_verdicts():
    with pytest.raises(ValueError, match="grid_doublings_exceed_max"):
        gridmix.repeat_convergence_marker(
            GRID_POLICY, doublings_used=GRID_POLICY.max_doublings + 1,
            mc_converged=True)
    with pytest.raises(ValueError, match="grid_doublings_negative"):
        gridmix.repeat_convergence_marker(GRID_POLICY, doublings_used=-1,
                                          mc_converged=True)
    with pytest.raises(ValueError, match="grid_mc_converged_not_a_bool_or_none"):
        gridmix.repeat_convergence_marker(GRID_POLICY, doublings_used=0,
                                          mc_converged="yes")


def test_dr5_this_module_declares_no_mc_verdict():
    """The MC §5 four-rule battery lives at the MC wiring, not here."""
    marker = gridmix.repeat_convergence_marker(
        GRID_POLICY, doublings_used=0, mc_converged=None)
    assert marker["convergence_rule"] == GRID_POLICY.convergence_rule
    assert "at the MC wiring" in marker["note"]
    src = inspect.getsource(gridmix.repeat_convergence_marker)
    for banned in ("tolerance", "rel_tol", "abs_tol"):
        assert banned not in src, banned


def test_dr5_theta_encoding_is_single_sourced_with_the_bootstrap_streams():
    from itsf.s0 import stats as s0_stats
    assert gridmix.theta_stream_key is s0_stats.theta_stream_key
    assert gridmix.theta_stream_key(THETA_PRIMARY) == 500


def test_research_seeds_are_the_only_seeds_either_ruling_may_use():
    assert contracts.RESEARCH_BOOTSTRAP_SEEDS == (7, 13, 31)
    for seed in contracts.RESEARCH_BOOTSTRAP_SEEDS:
        entropy = gridmix.repeat_stream_entropy(seed, THETA_PRIMARY, Q_MIL,
                                                R_MIL, 0, GRID_POLICY)
        assert entropy[0] == seed


# ===========================================================================
# ON THE PRODUCTION PATH — `build_grid` as the CONSUMER of both rulings
#
# Everything above tests the primitives standing alone. This section tests
# that the primitives are actually WIRED into the grid `s0_real_run.py`
# builds, that the legacy (no-kwargs) call is untouched, and that the ruled
# path can be told apart from the legacy one by its OUTPUT, not by trust.
# ===========================================================================

LOW = ("2010", "low", "none")
HIGH = ("2010", "high", "CPI")
LOW_KEY = "2010|low|none"
HIGH_KEY = "2010|high|CPI"


def _populations(n_tp_low: int, n_tp_high: int, n_fp_low: int, n_fp_high: int):
    """Fabricated D_TP / D_FP + the injected stratum mapping.

    TP days live in March, FP days in April; every P&L value is a
    deterministic fabricated number. No archive, no clock.
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


def _skewed():
    """THE CRAFTED FLIP FIXTURE: TP is low-heavy (8:2) while FP is high-heavy
    (2:18), so the availability basis and the selected-TP basis cannot agree.

    At q = r = 0.50: n_tp = 5, n_fp = 5.
      * availability basis (legacy)  -> shares over FP supply 2:18
      * selected-TP basis (DR-3)     -> shares over the drawn TP mix 4:1,
        LOW capped at its 2 FP days, the 2-unit shortfall redistributed over
        HIGH (the frozen literal, now reachable).
    """
    return _populations(n_tp_low=8, n_tp_high=2, n_fp_low=2, n_fp_high=18)


def _small_grid_policy(k_per_seed: int = 3):
    """The ruled policy with a cheap K. `GridRepeatPolicy` is a plain frozen
    dataclass with no gate on `k_per_seed`, so a test may shrink K; production
    K = 200 correctness is STRUCTURAL (the k range comes from the policy
    object), never enumerated here."""
    return dataclasses.replace(GRID_POLICY, k_per_seed=k_per_seed)


def _ruled_kwargs(k_per_seed: int = 3, theta: float = THETA_PRIMARY):
    return dict(fp_allocation=FP_METHOD,
                grid_policy=_small_grid_policy(k_per_seed), theta=theta)


#: The EXACT keys the ruled path adds to a feasible grid point. Anything else
#: appearing here is an undeclared output-shape change and the report
#: validator (report.py `_GRID_POINT_ALLOWED_KEYS`) would refuse the payload.
RULED_POINT_KEYS = {"fp_allocation", "repeats"}


# --- the legacy path is untouched -------------------------------------------

def test_onpath_legacy_call_is_unchanged_and_none_is_not_a_third_mode():
    """No kwargs == both kwargs explicitly None == today's grid.

    The 22 pinned tests in tests/test_s0_gridmix.py are the real bit-identity
    evidence (they exercise axes, rounding, allocation, anti-ordering,
    determinism and the method string through the SAME no-kwargs call, and
    that file is UNCHANGED by the DR-3/DR-5 wiring); this
    one adds that an explicit `None` is not quietly a third behaviour and that
    the legacy point carries NONE of the ruled sub-dicts.
    """
    d_tp, d_fp, strata = _populations(6, 4, 12, 8)
    implicit = gridmix.build_grid(d_tp, d_fp, strata, base_rate_p=0.4,
                                  q_grid=[0.50], r_grid=[0.50])
    explicit = gridmix.build_grid(d_tp, d_fp, strata, base_rate_p=0.4,
                                  q_grid=[0.50], r_grid=[0.50],
                                  fp_allocation=None, grid_policy=None,
                                  theta=None)
    assert implicit == explicit
    point = implicit["grid"]["q0.50_r0.50"]
    assert not (set(point) & RULED_POINT_KEYS)
    assert "DR-3/DR-5 RULED PATH" not in implicit["method"]


def test_onpath_kwargs_are_keyword_only_so_no_positional_caller_shifts():
    params = inspect.signature(gridmix.build_grid).parameters
    for name in ("fp_allocation", "grid_policy", "theta"):
        assert params[name].kind is inspect.Parameter.KEYWORD_ONLY, name
        assert params[name].default is None, name
    # the positional prefix every existing caller relies on is unchanged
    positional = [n for n, p in params.items()
                  if p.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD]
    assert positional == ["d_tp", "d_fp", "strata", "base_rate_p",
                          "master_seeds", "q_grid", "r_grid", "n_year"]


# --- the coherent-pair / theta gates ----------------------------------------

def test_onpath_half_a_ruling_is_refused():
    d_tp, d_fp, strata = _populations(6, 4, 12, 8)
    common = dict(base_rate_p=0.4, q_grid=[0.50], r_grid=[0.50])
    with pytest.raises(ValueError, match="grid_ruled_pair_incomplete"):
        gridmix.build_grid(d_tp, d_fp, strata, **common,
                           fp_allocation=FP_METHOD, theta=THETA_PRIMARY)
    with pytest.raises(ValueError, match="grid_ruled_pair_incomplete"):
        gridmix.build_grid(d_tp, d_fp, strata, **common,
                           grid_policy=_small_grid_policy(),
                           theta=THETA_PRIMARY)


def test_onpath_theta_is_required_with_the_policy_and_refused_without_it():
    d_tp, d_fp, strata = _populations(6, 4, 12, 8)
    common = dict(base_rate_p=0.4, q_grid=[0.50], r_grid=[0.50])
    with pytest.raises(ValueError,
                       match="grid_theta_required_with_grid_policy"):
        gridmix.build_grid(d_tp, d_fp, strata, **common,
                           fp_allocation=FP_METHOD,
                           grid_policy=_small_grid_policy())
    with pytest.raises(ValueError, match="grid_theta_without_ruled_methods"):
        gridmix.build_grid(d_tp, d_fp, strata, **common, theta=THETA_PRIMARY)
    for bad in ("0.5", True, float("nan")):
        with pytest.raises(ValueError):
            gridmix.build_grid(d_tp, d_fp, strata, **common,
                               fp_allocation=FP_METHOD,
                               grid_policy=_small_grid_policy(), theta=bad)


def test_onpath_unruled_method_values_are_refused_by_the_primitives_guards():
    """`build_grid` states no ruled literal of its own — it delegates."""
    d_tp, d_fp, strata = _populations(6, 4, 12, 8)
    common = dict(base_rate_p=0.4, q_grid=[0.50], r_grid=[0.50],
                  theta=THETA_PRIMARY)
    with pytest.raises(ValueError, match="fp_allocation_basis_not_ruled:A"):
        gridmix.build_grid(d_tp, d_fp, strata, **common,
                           fp_allocation=dataclasses.replace(FP_METHOD,
                                                             basis="A"),
                           grid_policy=_small_grid_policy())
    with pytest.raises(ValueError,
                       match="grid_stream_includes_theta_not_ruled:False"):
        gridmix.build_grid(
            d_tp, d_fp, strata, **common, fp_allocation=FP_METHOD,
            grid_policy=dataclasses.replace(_small_grid_policy(),
                                            stream_includes_theta=False))
    with pytest.raises(ValueError, match="grid_convergence_rule_not_ruled"):
        gridmix.build_grid(
            d_tp, d_fp, strata, **common, fp_allocation=FP_METHOD,
            grid_policy=dataclasses.replace(_small_grid_policy(),
                                            convergence_rule="decided_here"))


# --- DR-3 ON THE PATH -------------------------------------------------------

def test_onpath_dr3_flip_selected_tp_basis_beats_availability_basis():
    """MUTATION EVIDENCE on the crafted fixture: the two bases disagree.

    Legacy apportions n_fp = 5 over FP availability 2:18 -> all 5 to HIGH
    (the exact remainder tie goes to the ascending key). The ruling apportions
    it over the SELECTED TP mix 4:1 -> LOW 4 capped at its 2 available FP
    days, and the 2-unit shortfall is redistributed over HIGH.
    """
    d_tp, d_fp, strata = _skewed()
    common = dict(base_rate_p=0.4, q_grid=[0.50], r_grid=[0.50])
    legacy = gridmix.build_grid(d_tp, d_fp, strata, **common)[
        "grid"]["q0.50_r0.50"]
    ruled = gridmix.build_grid(d_tp, d_fp, strata, **common,
                               **_ruled_kwargs())["grid"]["q0.50_r0.50"]
    assert ruled["n_tp_target"] == 5 and ruled["n_fp_target"] == 5
    legacy_fp = legacy["per_seed"][7]["allocation_fp"]
    ruled_fp = ruled["fp_allocation"]["fp_alloc"]
    assert legacy_fp == {HIGH_KEY: 5, LOW_KEY: 0}
    assert ruled_fp == {HIGH_KEY: 3, LOW_KEY: 2}
    assert ruled_fp != legacy_fp
    # the ruled split is the one actually USED for the draw, not a side note
    for block in ruled["per_seed"].values():
        assert block["allocation_fp"] == ruled_fp
        assert len([d for d in block["fp_dates"]
                    if strata[d] == LOW]) == 2
        assert len([d for d in block["fp_dates"]
                    if strata[d] == HIGH]) == 3
    # ... and the frozen-literal shortfall really fired on the path
    assert ruled["fp_allocation"]["shortfall_redistributed"] == 2


def test_onpath_dr3_block_discloses_deviations_and_stability():
    d_tp, d_fp, strata = _skewed()
    point = gridmix.build_grid(d_tp, d_fp, strata, base_rate_p=0.4,
                               q_grid=[0.50], r_grid=[0.50],
                               **_ruled_kwargs())["grid"]["q0.50_r0.50"]
    block = point["fp_allocation"]
    assert block["seed_stable"] is True
    assert block["checked_seeds"] == [7, 13, 31]
    assert block["checked_repeats_per_seed"] == 3
    assert block["weights_selected_tp"] == {HIGH_KEY: 1, LOW_KEY: 4}
    assert block["basis"] == FP_METHOD.basis
    assert block["weight_source"] == FP_METHOD.weight_source
    assert block["shortfall_rule"] == FP_METHOD.shortfall_rule
    dev = block["deviations"]
    assert dev[LOW_KEY]["target_tp_share"] == pytest.approx(0.8)
    assert dev[LOW_KEY]["realized_fp_share"] == pytest.approx(0.4)
    assert dev[LOW_KEY]["deviation"] == pytest.approx(-0.4)
    assert block["max_abs_deviation"] == pytest.approx(0.4)


def test_onpath_dr3_selected_tp_composition_is_identical_across_seeds():
    """The stability the single per-cell `fp_allocation` block RESTS on:
    every seed (and every repeat) draws the SAME per-stratum TP counts, only
    different days."""
    d_tp, d_fp, strata = _skewed()
    point = gridmix.build_grid(d_tp, d_fp, strata, base_rate_p=0.4,
                               q_grid=[0.50], r_grid=[0.50],
                               **_ruled_kwargs())["grid"]["q0.50_r0.50"]
    per_seed = point["per_seed"]
    assert set(per_seed) == {7, 13, 31}
    compositions = set()
    for block in per_seed.values():
        counts = (len([d for d in block["tp_dates"] if strata[d] == LOW]),
                  len([d for d in block["tp_dates"] if strata[d] == HIGH]))
        compositions.add(counts)
        assert block["allocation_fp"] == point["fp_allocation"]["fp_alloc"]
    assert compositions == {(4, 1)}
    # the DAYS still move with the seed — stability is about counts only
    assert len({tuple(b["tp_dates"]) for b in per_seed.values()}) == 3


def test_onpath_dr3_conservation_gate_is_armed_on_the_ruled_path(monkeypatch):
    """The hard gate is REACHED per repeat, and a violation PROPAGATES.

    Part 1 spies on the real gate (delegating, so the grid is unchanged) and
    counts the calls: 3 seeds x 3 repeats. Part 2 makes the gate raise and
    shows `build_grid` does not swallow it.
    """
    d_tp, d_fp, strata = _skewed()
    common = dict(base_rate_p=0.4, q_grid=[0.50], r_grid=[0.50])
    real = gridmix.assert_fp_conservation
    seen: list[tuple[int, int]] = []

    def spy(fp_alloc, n_fp):
        seen.append((sum(fp_alloc.values()), n_fp))
        return real(fp_alloc, n_fp)

    monkeypatch.setattr(gridmix, "assert_fp_conservation", spy)
    gridmix.build_grid(d_tp, d_fp, strata, **common, **_ruled_kwargs())
    assert len(seen) == 3 * 3
    assert set(seen) == {(5, 5)}

    def boom(fp_alloc, n_fp):
        raise RuntimeError("fp_allocation_conservation_violated: injected")

    monkeypatch.setattr(gridmix, "assert_fp_conservation", boom)
    with pytest.raises(RuntimeError, match="conservation_violated"):
        gridmix.build_grid(d_tp, d_fp, strata, **common, **_ruled_kwargs())


def test_onpath_dr3_seed_instability_fails_closed(monkeypatch):
    """If the selected-TP composition ever stopped being seed-stable, the
    cell's single `fp_allocation` block would be a false disclosure — so the
    build refuses rather than quoting one repeat's split as the cell's."""
    d_tp, d_fp, strata = _skewed()
    real = gridmix.fp_allocation_from_selected_tp
    calls = {"n": 0}

    def drifting(n_fp, selected_tp, fp_available, method):
        calls["n"] += 1
        if calls["n"] > 1:                       # 2nd repeat drifts
            selected_tp = {k: v + 1 for k, v in selected_tp.items()}
        return real(n_fp, selected_tp, fp_available, method)

    monkeypatch.setattr(gridmix, "fp_allocation_from_selected_tp", drifting)
    with pytest.raises(RuntimeError, match="fp_allocation_not_seed_stable"):
        gridmix.build_grid(d_tp, d_fp, strata, base_rate_p=0.4,
                           q_grid=[0.50], r_grid=[0.50], **_ruled_kwargs())


# --- DR-5 ON THE PATH -------------------------------------------------------

def test_onpath_dr5_repeats_block_shape_and_real_k_variation():
    d_tp, d_fp, strata = _skewed()
    point = gridmix.build_grid(d_tp, d_fp, strata, base_rate_p=0.4,
                               q_grid=[0.50], r_grid=[0.50],
                               **_ruled_kwargs(k_per_seed=4)
                               )["grid"]["q0.50_r0.50"]
    rep = point["repeats"]
    assert rep["k_per_seed"] == 4
    assert rep["k_start_index"] == GRID_POLICY.k_start_index == 0
    assert rep["n_repeats_per_seed"] == 4
    assert rep["doublings_used"] == 0
    assert rep["headline_k"] == 0
    assert rep["theta"] == THETA_PRIMARY
    assert rep["theta_stream_key"] == gridmix.theta_stream_key(THETA_PRIMARY)
    assert set(rep["per_seed"]) == {7, 13, 31}
    for seed, block in rep["per_seed"].items():
        digests = block["digests_by_k"]
        assert sorted(digests) == [0, 1, 2, 3]
        # THE POINT of the repeats: k really moves the draw
        assert len(set(digests.values())) == 4, seed
        assert block["digest_of_digests"] == gridmix._digest_of_digests(
            digests)
    # ... and different seeds draw different repeat sets
    assert len({b["digest_of_digests"]
                for b in rep["per_seed"].values()}) == 3


def test_onpath_dr5_dispersion_is_realized_only_and_names_what_moved():
    """Realized precision/recall/selection-count CANNOT move across repeats
    (the frozen totals and the conserved allocation fix them); what moves is
    WHICH days were drawn, so the mixture mean is the statistic with real
    spread. Both are reported — a zero spread is a finding, not a filler."""
    d_tp, d_fp, strata = _skewed()
    point = gridmix.build_grid(d_tp, d_fp, strata, base_rate_p=0.4,
                               q_grid=[0.50], r_grid=[0.50],
                               **_ruled_kwargs(k_per_seed=4)
                               )["grid"]["q0.50_r0.50"]
    disp = point["repeats"]["per_seed"][7]["dispersion"]
    assert set(disp) == {"realized_precision", "realized_recall",
                         "n_selected", "mixture_mean_pnl"}
    for name in ("realized_precision", "realized_recall", "n_selected"):
        assert disp[name]["spread"] == 0.0, name
        assert disp[name]["n_k"] == 4
    assert disp["mixture_mean_pnl"]["spread"] > 0.0
    assert sorted(disp["mixture_mean_pnl"]["values_by_k"]) == [0, 1, 2, 3]
    # no verdict, no tolerance anywhere in the dispersion payload
    for name, block in disp.items():
        assert gridmix.MARK_INFEASIBLE_BY_CONVERGENCE not in block, name


def test_onpath_dr5_convergence_marker_is_pending_not_a_verdict():
    d_tp, d_fp, strata = _skewed()
    point = gridmix.build_grid(d_tp, d_fp, strata, base_rate_p=0.4,
                               q_grid=[0.50], r_grid=[0.50],
                               **_ruled_kwargs())["grid"]["q0.50_r0.50"]
    marker = point["repeats"]["convergence"]
    assert marker["mc_converged"] is None            # S0 side has no verdict
    assert marker["doublings_used"] == 0
    assert marker["must_double_again"] is True
    assert marker[gridmix.MARK_INFEASIBLE_BY_CONVERGENCE] is False
    assert marker["max_doublings"] == GRID_POLICY.max_doublings
    assert marker["convergence_rule"] == GRID_POLICY.convergence_rule
    assert "at the MC wiring" in marker["note"]


def test_onpath_dr5_prefix_nesting_k_to_2k_on_a_real_cell():
    """K -> 2K reproduces the FIRST K repeats' draw digests EXACTLY, for every
    seed of every cell, and merely appends the new ones."""
    d_tp, d_fp, strata = _skewed()
    common = dict(base_rate_p=0.4, q_grid=[0.50, 0.60], r_grid=[0.50])
    small = gridmix.build_grid(d_tp, d_fp, strata, **common,
                               **_ruled_kwargs(k_per_seed=3))["grid"]
    doubled = gridmix.build_grid(d_tp, d_fp, strata, **common,
                                 **_ruled_kwargs(k_per_seed=6))["grid"]
    assert set(small) == set(doubled) == {"q0.50_r0.50", "q0.60_r0.50"}
    for key, point in small.items():
        for seed, block in point["repeats"]["per_seed"].items():
            big = doubled[key]["repeats"]["per_seed"][seed]["digests_by_k"]
            assert sorted(big) == [0, 1, 2, 3, 4, 5], (key, seed)
            for k, digest in block["digests_by_k"].items():
                assert big[k] == digest, (key, seed, k)
    # the headline row is repeat k_start_index, so it too is prefix-stable
    for key, point in small.items():
        for seed, row in point["per_seed"].items():
            big_row = doubled[key]["per_seed"][seed]
            assert row["tp_dates"] == big_row["tp_dates"]


def test_onpath_dr5_theta_moves_every_cell_draw():
    """MUTATION EVIDENCE: the ONLY difference is theta, and every digest
    changes — which is what `stream_includes_theta=True` buys."""
    d_tp, d_fp, strata = _skewed()
    common = dict(base_rate_p=0.4, q_grid=[0.50], r_grid=[0.50])
    primary = gridmix.build_grid(d_tp, d_fp, strata, **common,
                                 **_ruled_kwargs(theta=THETA_PRIMARY))
    secondary = gridmix.build_grid(d_tp, d_fp, strata, **common,
                                   **_ruled_kwargs(theta=THETA_SECONDARY))
    a = primary["grid"]["q0.50_r0.50"]["repeats"]["per_seed"]
    b = secondary["grid"]["q0.50_r0.50"]["repeats"]["per_seed"]
    for seed in (7, 13, 31):
        assert a[seed]["digest_of_digests"] != b[seed]["digest_of_digests"]
        for k, digest in a[seed]["digests_by_k"].items():
            assert b[seed]["digests_by_k"][k] != digest, (seed, k)
    # the DR-3 allocation is theta-independent (same populations) — only the
    # DAYS moved, so the disclosure block still matches
    assert (primary["grid"]["q0.50_r0.50"]["fp_allocation"]["fp_alloc"]
            == secondary["grid"]["q0.50_r0.50"]["fp_allocation"]["fp_alloc"])


def test_onpath_dr5_headline_row_is_repeat_k_start_index_not_a_fresh_draw():
    """The reported per-seed row must be a MEMBER of the repeat set (the old
    4-component stream carries no theta and would be un-nested)."""
    d_tp, d_fp, strata = _skewed()
    point = gridmix.build_grid(d_tp, d_fp, strata, base_rate_p=0.4,
                               q_grid=[0.50], r_grid=[0.50],
                               **_ruled_kwargs())["grid"]["q0.50_r0.50"]
    for seed, row in point["per_seed"].items():
        digest = gridmix.repeat_draw_digest(row["tp_dates"], row["fp_dates"])
        assert digest == point["repeats"]["per_seed"][seed]["digests_by_k"][0]
    # and it is NOT the legacy 4-component draw
    legacy = gridmix.build_grid(d_tp, d_fp, strata, base_rate_p=0.4,
                                q_grid=[0.50], r_grid=[0.50])[
                                    "grid"]["q0.50_r0.50"]
    assert (point["per_seed"][7]["tp_dates"]
            != legacy["per_seed"][7]["tp_dates"])


def test_onpath_production_k_and_start_are_read_from_the_policy_object():
    """K = 200 / k from 0 is STRUCTURAL: the k range comes from the ruled
    object, so the cheap-K tests above cover the production value too."""
    assert gridmix.repeat_k_indices(GRID_POLICY) == tuple(range(200))
    small = _small_grid_policy(3)
    assert gridmix.repeat_k_indices(small) == (0, 1, 2)
    assert small.k_start_index == GRID_POLICY.k_start_index
    assert small.max_doublings == GRID_POLICY.max_doublings


# --- output-shape discipline ------------------------------------------------

def test_onpath_ruled_cell_adds_exactly_two_keys_and_no_per_seed_key():
    """OUTPUT-SHAPE PIN. report.py refuses unknown keys, so the ruled path may
    add ONLY these — one sub-dict per concern, and the 13-key per-seed row is
    untouched (its `allocation_fp` simply now holds the ruled split)."""
    d_tp, d_fp, strata = _skewed()
    common = dict(base_rate_p=0.4, q_grid=[0.50], r_grid=[0.50])
    legacy = gridmix.build_grid(d_tp, d_fp, strata, **common)[
        "grid"]["q0.50_r0.50"]
    ruled = gridmix.build_grid(d_tp, d_fp, strata, **common,
                               **_ruled_kwargs())["grid"]["q0.50_r0.50"]
    assert set(ruled) - set(legacy) == RULED_POINT_KEYS
    assert set(legacy) - set(ruled) == set()
    for seed in (7, 13, 31):
        assert set(ruled["per_seed"][seed]) == set(legacy["per_seed"][seed])
    assert set(ruled["fp_allocation"]) == {
        "fp_alloc", "n_fp", "n_tp_selected", "n_fp_available",
        "weights_selected_tp", "shortfall_redistributed", "deviations",
        "max_abs_deviation", "basis", "weight_source", "shortfall_rule",
        "method", "seed_stable", "checked_seeds", "checked_repeats_per_seed"}
    assert set(ruled["repeats"]) == {
        "k_per_seed", "k_start_index", "n_repeats_per_seed", "doublings_used",
        "headline_k", "theta", "theta_stream_key", "per_seed", "convergence",
        "method"}
    assert set(ruled["repeats"]["per_seed"][7]) == {
        "digests_by_k", "digest_of_digests", "dispersion"}


def test_onpath_top_level_cell_shape_is_unchanged():
    """No new TOP-level key, so report.py's `_FEASIBILITY_CELL_FIELDS` (grid /
    n_tp_available / n_fp_available / method) needs no change — the ruled-path
    disclosure travels in the `method` string."""
    d_tp, d_fp, strata = _skewed()
    common = dict(base_rate_p=0.4, q_grid=[0.50], r_grid=[0.50])
    legacy = gridmix.build_grid(d_tp, d_fp, strata, **common)
    ruled = gridmix.build_grid(d_tp, d_fp, strata, **common,
                               **_ruled_kwargs())
    assert set(ruled) == set(legacy) == {"grid", "n_tp_available",
                                         "n_fp_available", "method"}
    assert "DR-3/DR-5 RULED PATH" in ruled["method"]
    for fragment in (FP_METHOD.basis, FP_METHOD.weight_source,
                     FP_METHOD.shortfall_rule, GRID_POLICY.convergence_rule,
                     "THETA IS IN THE STREAM", "prefix-nested",
                     gridmix.MARK_INFEASIBLE_BY_CONVERGENCE):
        assert fragment in ruled["method"], fragment


def test_onpath_infeasible_point_carries_neither_ruled_block():
    """# frozen: S0 Appendix A — an infeasible_by_sample point skips selection
    and is still reported in full; there is no allocation and no repeat to
    disclose, so neither ruled sub-dict may appear."""
    d_tp, _d_fp, strata = _skewed()
    small_fp = {"2010-04-01": -10.0, "2010-04-02": -20.0}
    strata = {**strata, "2010-04-01": LOW, "2010-04-02": LOW}
    point = gridmix.build_grid(d_tp, small_fp, strata, base_rate_p=0.4,
                               q_grid=[0.35], r_grid=[0.80],
                               **_ruled_kwargs())["grid"]["q0.35_r0.80"]
    assert point["infeasible_by_sample"] is True
    assert point["per_seed"] == {}
    assert not (set(point) & RULED_POINT_KEYS)
    assert "infeasible_reason" in point


def test_onpath_empty_selection_reports_none_dispersion_not_a_fake_zero():
    """n_tp = floor(0.20 x 4) = 0 -> n_fp = 0: a FEASIBLE point with nothing
    selected. `realized_precision` and `mixture_mean_pnl` are undefined there,
    so their dispersion is None — `cross_k_dispersion` owns no missing-value
    convention and must never be handed a fabricated 0.0."""
    d_tp, d_fp, strata = _populations(3, 1, 4, 4)
    point = gridmix.build_grid(d_tp, d_fp, strata, base_rate_p=0.4,
                               q_grid=[0.50], r_grid=[0.20],
                               **_ruled_kwargs())["grid"]["q0.50_r0.20"]
    assert point["infeasible_by_sample"] is False
    assert point["n_tp_target"] == 0 and point["n_fp_target"] == 0
    assert point["fp_allocation"]["max_abs_deviation"] is None
    assert sum(point["fp_allocation"]["fp_alloc"].values()) == 0
    disp = point["repeats"]["per_seed"][7]["dispersion"]
    assert disp["realized_precision"] is None
    assert disp["mixture_mean_pnl"] is None
    assert disp["realized_recall"]["spread"] == 0.0     # 0/4, defined
    assert disp["n_selected"]["max"] == 0.0
    # every repeat drew the same (empty) selection, so the digests coincide —
    # k-variation is a property of the DRAW, never faked by mixing k in
    digests = point["repeats"]["per_seed"][7]["digests_by_k"]
    assert len(set(digests.values())) == 1


def test_onpath_determinism_and_the_cheap_single_seed_helper():
    """Two identical ruled builds are equal, and `_build_grid_unchecked` takes
    the same kwargs so a single-seed grid stays available to tests."""
    d_tp, d_fp, strata = _skewed()
    common = dict(base_rate_p=0.4, q_grid=[0.50], r_grid=[0.50])
    a = gridmix.build_grid(d_tp, d_fp, strata, **common, **_ruled_kwargs())
    b = gridmix.build_grid(d_tp, d_fp, strata, **common, **_ruled_kwargs())
    assert a == b
    single = gridmix._build_grid_unchecked(d_tp, d_fp, strata, **common,
                                           master_seeds=(7,),
                                           **_ruled_kwargs())
    assert set(single["grid"]["q0.50_r0.50"]["per_seed"]) == {7}
    assert (single["grid"]["q0.50_r0.50"]["repeats"]["per_seed"][7]
            == a["grid"]["q0.50_r0.50"]["repeats"]["per_seed"][7])
    assert single["grid"]["q0.50_r0.50"]["fp_allocation"][
        "checked_seeds"] == [7]


def test_onpath_anti_ordering_still_holds_on_the_ruled_path():
    """# frozen: S0 Appendix A step 3 — no outcome may touch the selection.

    The DR-3 weights are per-stratum COUNTS of already-chosen TP days, so
    permuting the P&L must leave every drawn date (and every digest) alone.
    """
    d_tp, d_fp, strata = _skewed()
    common = dict(base_rate_p=0.4, q_grid=[0.50], r_grid=[0.50])
    base = gridmix.build_grid(d_tp, d_fp, strata, **common, **_ruled_kwargs())
    permuted_tp = dict(zip(d_tp.keys(), reversed(list(d_tp.values()))))
    permuted_fp = dict(zip(d_fp.keys(), reversed(list(d_fp.values()))))
    assert permuted_tp != d_tp and permuted_fp != d_fp
    other = gridmix.build_grid(permuted_tp, permuted_fp, strata, **common,
                               **_ruled_kwargs())
    a = base["grid"]["q0.50_r0.50"]
    b = other["grid"]["q0.50_r0.50"]
    assert a["fp_allocation"] == b["fp_allocation"]
    for seed in (7, 13, 31):
        assert a["per_seed"][seed]["tp_dates"] == b["per_seed"][seed][
            "tp_dates"]
        assert a["per_seed"][seed]["fp_dates"] == b["per_seed"][seed][
            "fp_dates"]
        assert (a["repeats"]["per_seed"][seed]["digests_by_k"]
                == b["repeats"]["per_seed"][seed]["digests_by_k"])
    # only the DESCRIPTIVE mixture mean may move
    assert (a["repeats"]["per_seed"][7]["dispersion"]["mixture_mean_pnl"]
            != b["repeats"]["per_seed"][7]["dispersion"]["mixture_mean_pnl"])


def test_onpath_full_frozen_grid_runs_end_to_end_on_the_ruled_path():
    """All 63 frozen points, 3 seeds, ruled kwargs — every feasible point
    carries both blocks and every infeasible one carries neither.

    FP supply is deliberately tight (10 days against a 15-day n_fp target at
    the q = 0.35 / r = 0.80 corner) so the sweep straddles BOTH branches.
    """
    d_tp, d_fp, strata = _populations(8, 2, 2, 8)
    out = gridmix.build_grid(d_tp, d_fp, strata, base_rate_p=0.4,
                             **_ruled_kwargs(k_per_seed=2))
    assert len(out["grid"]) == 63
    feasible = infeasible = 0
    for key, point in out["grid"].items():
        if point["infeasible_by_sample"]:
            infeasible += 1
            assert not (set(point) & RULED_POINT_KEYS), key
            continue
        feasible += 1
        assert set(point) & RULED_POINT_KEYS == RULED_POINT_KEYS, key
        assert sum(point["fp_allocation"]["fp_alloc"].values()) == \
            point["n_fp_target"], key
        assert set(point["repeats"]["per_seed"]) == {7, 13, 31}, key
    assert feasible > 0 and infeasible > 0
