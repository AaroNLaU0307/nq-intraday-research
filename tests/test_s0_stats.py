"""Synthetic checks for itsf.s0.stats (frozen S0 §9 bootstrap CI layer).

SA-18 scope. Every series here is built by a deterministic RNG-free generator:
no real archive is read, no clock or module-level random state is touched, and
the only randomness in the whole file comes out of the module under test, whose
streams derive exclusively from contracts.RESEARCH_BOOTSTRAP_SEEDS.
"""
from __future__ import annotations

import inspect

import numpy as np
import pytest

from itsf import contracts
from itsf.mc.bootstrap import stationary_bootstrap_indices
from itsf.s0 import stats


def synthetic_pnl(n: int = 120, mean: float = 25.0,
                  scale: float = 4.0) -> list[float]:
    """Deterministic daily USD P&L, no RNG involved.

    `(i * 37) % 101` walks the residues 0..100 in a fixed order, so the series
    has real dispersion and no trend while staying byte-reproducible.
    """
    return [mean + (((i * 37) % 101) - 50) * scale for i in range(n)]


# ---------------------------------------------------------------------------
# frozen constants and the seed mutation guard
# ---------------------------------------------------------------------------

def test_frozen_constants():
    # frozen: S0 §9 — block 5 primary / 21 sensitivity, 10,000 resamples,
    # percentile 95% CI
    assert stats.PRIMARY_BLOCK_DAYS == 5.0
    assert stats.SENSITIVITY_BLOCK_DAYS == 21.0
    assert stats.N_BOOT == 10_000
    assert stats.CI_LEVEL == 0.95
    assert stats.PERCENTILE_METHOD == "linear"


def test_master_seed_default_is_the_contracts_constant():
    """Mutation guard: the default must BE contracts.RESEARCH_BOOTSTRAP_SEEDS.

    # frozen: S0 §9 seeds {7,13,31} (IR DR-02: the only research randomness
    source). A local copy of the tuple would let the constant be changed
    without this module following it.
    """
    params = inspect.signature(stats.bootstrap_mean_ci).parameters
    assert params["master_seeds"].default is contracts.RESEARCH_BOOTSTRAP_SEEDS
    assert contracts.RESEARCH_BOOTSTRAP_SEEDS == (7, 13, 31)
    # block_len has NO default: neither frozen block length may be silently
    # promoted by this layer (# frozen: S0 §9 Primary 5 / Sensitivity 21).
    assert params["block_len"].default is inspect.Parameter.empty


# ---------------------------------------------------------------------------
# percentile method
# ---------------------------------------------------------------------------

def test_percentile_ci_hand_computed_linear_interpolation():
    """# frozen: S0 §9 百分位法 — endpoints at (1-c)/2 and 1-(1-c)/2.

    101 values 0..100: the virtual index is (n-1)*p = 100*0.025 = 2.5, so
    linear interpolation gives exactly 2.5 and 97.5. `approx` covers the last
    ulp only — (1 - 0.95)/2 is not exact in binary, which perturbs the virtual
    index by ~1e-15 and is a property of the frozen formula, not of the data.
    """
    values = np.arange(0.0, 101.0)
    assert stats.percentile_ci(values, 0.95) == pytest.approx((2.5, 97.5))
    assert stats.percentile_ci(values, 0.80) == pytest.approx((10.0, 90.0))
    # 4 values, 50% CI: index 3*0.25 = 0.75 -> 1 + 0.75*(2-1) = 1.75;
    # index 3*0.75 = 2.25 -> 3 + 0.25*(4-3) = 3.25
    assert stats.percentile_ci([1.0, 2.0, 3.0, 4.0], 0.50) == pytest.approx(
        (1.75, 3.25))


def test_percentile_endpoints_match_independent_recomputation():
    """The quoted endpoints are the percentile of the resampled MEANS.

    Rebuild the stream from the documented derivation
    default_rng([seed, STATS_STREAM_TAG, block millis]) and the SAME
    mc.bootstrap index generator, then compare byte-for-byte.
    """
    series = synthetic_pnl(40)
    n_boot = 25
    out = stats.bootstrap_mean_ci(series, block_len=5.0, n_boot=n_boot,
                                  ci_level=0.90, master_seeds=(7,))
    rng = np.random.default_rng([7, stats.STATS_STREAM_TAG, 5000])
    values = np.asarray(series, dtype=float)
    means = np.asarray([values[stationary_bootstrap_indices(
        len(values), 5.0, rng=rng)].mean() for _ in range(n_boot)])
    assert out["per_seed"][7]["ci_lo"] == float(
        np.percentile(means, 5.0, method="linear"))
    assert out["per_seed"][7]["ci_hi"] == float(
        np.percentile(means, 95.0, method="linear"))


def test_constant_series_gives_a_point_interval():
    """Hand-computable exactness: every resample of a constant series has the
    same mean, so both percentile endpoints equal that constant exactly."""
    out = stats.bootstrap_mean_ci([12.5] * 30, block_len=5.0, n_boot=20)
    for seed_block in out["per_seed"].values():
        assert seed_block["mean"] == 12.5
        assert seed_block["ci_lo"] == 12.5 and seed_block["ci_hi"] == 12.5
    assert out["convergence"] == {"max_abs_ci_lo_diff": 0.0,
                                  "max_abs_ci_hi_diff": 0.0}


# ---------------------------------------------------------------------------
# the interval itself
# ---------------------------------------------------------------------------

def test_ci_brackets_the_mean_of_the_series():
    """A percentile bootstrap CI of the mean must contain the sample mean —
    which for a synthetic population IS the true mean of that population."""
    series = synthetic_pnl(120)
    true_mean = float(np.mean(series))
    out = stats.bootstrap_mean_ci(series, block_len=5.0, n_boot=200)
    for seed, block in out["per_seed"].items():
        assert block["mean"] == pytest.approx(true_mean)
        assert block["ci_lo"] < true_mean < block["ci_hi"], seed


def test_determinism_same_call_twice():
    series = synthetic_pnl(60)
    a = stats.bootstrap_mean_ci(series, block_len=5.0, n_boot=50)
    b = stats.bootstrap_mean_ci(series, block_len=5.0, n_boot=50)
    assert a["per_seed"] == b["per_seed"]
    assert a["convergence"] == b["convergence"]


def test_seeds_give_different_resamples_but_close_intervals():
    """# frozen: S0 §9 three independent master seeds; MC_METHOD_SPEC §5 (b)
    wants them to agree. Different streams, similar answers."""
    series = synthetic_pnl(120)
    means_7 = stats.resample_means(series, 5.0, 100, 7)
    means_13 = stats.resample_means(series, 5.0, 100, 13)
    means_31 = stats.resample_means(series, 5.0, 100, 31)
    assert not np.array_equal(means_7, means_13)
    assert not np.array_equal(means_7, means_31)
    assert not np.array_equal(means_13, means_31)

    out = stats.bootstrap_mean_ci(series, block_len=5.0, n_boot=400)
    width = out["quoted"]["ci_hi"] - out["quoted"]["ci_lo"]
    assert width > 0
    assert out["convergence"]["max_abs_ci_lo_diff"] < 0.5 * width
    assert out["convergence"]["max_abs_ci_hi_diff"] < 0.5 * width


def test_convergence_block_is_the_actual_max_endpoint_spread():
    out = stats.bootstrap_mean_ci(synthetic_pnl(80), block_len=5.0, n_boot=60)
    los = [b["ci_lo"] for b in out["per_seed"].values()]
    his = [b["ci_hi"] for b in out["per_seed"].values()]
    assert out["convergence"]["max_abs_ci_lo_diff"] == max(los) - min(los)
    assert out["convergence"]["max_abs_ci_hi_diff"] == max(his) - min(his)
    assert len(out["per_seed"]) == 3


def test_block_len_flows_through_primary_and_sensitivity():
    """# frozen: S0 §9 Primary block 5, Sensitivity block 21 — both valid, and
    the block length reaches both the stream derivation and the report."""
    series = synthetic_pnl(120)
    primary = stats.bootstrap_mean_ci(series, block_len=stats.PRIMARY_BLOCK_DAYS,
                                      n_boot=100)
    sens = stats.bootstrap_mean_ci(series,
                                   block_len=stats.SENSITIVITY_BLOCK_DAYS,
                                   n_boot=100)
    assert primary["quoted"]["block_len"] == 5.0
    assert sens["quoted"]["block_len"] == 21.0
    assert stats.block_stream_key(5.0) == 5000
    assert stats.block_stream_key(21.0) == 21000
    assert primary["quoted"]["ci_lo"] != sens["quoted"]["ci_lo"]
    for out in (primary, sens):
        assert out["quoted"]["ci_lo"] < out["quoted"]["mean"] < out["quoted"]["ci_hi"]


def test_quoted_is_the_first_seed_by_fixed_convention_never_best_of():
    """Quoted = FIRST master seed, always. Feed the seeds in a different order
    and the quote follows the convention, not the most flattering interval."""
    series = synthetic_pnl(80)
    out = stats.bootstrap_mean_ci(series, block_len=5.0, n_boot=60)
    assert out["quoted_seed"] == contracts.RESEARCH_BOOTSTRAP_SEEDS[0] == 7
    assert out["quoted"] == out["per_seed"][7]

    shuffled = stats.bootstrap_mean_ci(series, block_len=5.0, n_boot=60,
                                       master_seeds=(13, 7, 31))
    assert shuffled["quoted_seed"] == 13
    assert shuffled["quoted"] == shuffled["per_seed"][13]
    # same three seeds, same per-seed results — only the convention moved
    assert shuffled["per_seed"] == out["per_seed"]
    best_lo = max(b["ci_lo"] for b in out["per_seed"].values())
    assert out["quoted"]["ci_lo"] <= best_lo   # never selected for being best


def test_doubling_n_boot_keeps_the_earlier_resamples():
    """MC_METHOD_SPEC §5 (a) doubles the resample count and re-runs; the
    stream is sequential, so the first B resamples are reproduced exactly."""
    series = synthetic_pnl(50)
    short = stats.resample_means(series, 5.0, 10, 7)
    long = stats.resample_means(series, 5.0, 20, 7)
    assert np.array_equal(short, long[:10])


# ---------------------------------------------------------------------------
# fail-closed edges
# ---------------------------------------------------------------------------

def test_empty_or_too_short_series_rejected():
    with pytest.raises(ValueError):
        stats.bootstrap_mean_ci([], block_len=5.0, n_boot=10)
    with pytest.raises(ValueError):
        stats.bootstrap_mean_ci([1.0], block_len=5.0, n_boot=10)


def test_non_finite_values_rejected_never_dropped():
    with pytest.raises(ValueError):
        stats.bootstrap_mean_ci([1.0, float("nan"), 3.0], block_len=5.0,
                                n_boot=10)
    with pytest.raises(ValueError):
        stats.bootstrap_mean_ci([1.0, float("inf"), 3.0], block_len=5.0,
                                n_boot=10)


def test_invalid_parameters_rejected():
    series = synthetic_pnl(20)
    with pytest.raises(ValueError):
        stats.bootstrap_mean_ci(series, block_len=0.0, n_boot=10)
    with pytest.raises(ValueError):
        stats.bootstrap_mean_ci(series, block_len=5.0, n_boot=0)
    with pytest.raises(ValueError):
        stats.bootstrap_mean_ci(series, block_len=5.0, n_boot=10, ci_level=1.0)
    with pytest.raises(ValueError):
        stats.bootstrap_mean_ci(series, block_len=5.0, n_boot=10,
                                master_seeds=())
    with pytest.raises(ValueError):
        stats.bootstrap_mean_ci(series, block_len=5.0, n_boot=10,
                                master_seeds=(7, 7))


def test_method_string_discloses_the_whole_recipe():
    out = stats.bootstrap_mean_ci(synthetic_pnl(20), block_len=5.0, n_boot=10)
    method = out["method"]
    for fragment in ("stationary bootstrap", "percentile", "95%",
                     "[7, 13, 31]", "STATS_STREAM_TAG", "master seed 7",
                     "10 resamples", "block length 5 trading days"):
        assert fragment in method, fragment
