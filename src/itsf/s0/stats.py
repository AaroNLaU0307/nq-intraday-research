"""S0-level stationary-bootstrap confidence intervals.

# frozen: S0 §9 — "Primary：stationary bootstrap，期望块长 5 交易日，10,000 次，
seeds {7,13,31}，百分位法 95% CI；Sensitivity：块长 21."

Scope of THIS module: turn one ordered series of daily USD P&L into the frozen
§9 interval estimate of its MEAN. It computes no verdict, reads no file, holds
no global state and owns no threshold — the GO/STOP reading lives downstream in
the MC layer (frozen S0 §10.4), never here.

What is FROZEN and what is ENGINEERING
--------------------------------------
FROZEN (never a parameter, never re-derived here):
  * the resampling scheme — Politis–Romano stationary bootstrap, reused from
    `itsf.mc.bootstrap.stationary_bootstrap_indices` (geometric blocks,
    circular wrap) so the S0 CI and the MC epistemic layer resample by exactly
    the same code path;
  * the master seeds {7, 13, 31} — `contracts.RESEARCH_BOOTSTRAP_SEEDS` is the
    ONLY randomness source any research computation may derive from (IR DR-02).
    The run-infra provenance seed on `RunConfig` is not a research input and
    must never reach this module;
  * the interval method — PERCENTILE method on the distribution of the
    RESAMPLED MEANS (not BCa, not normal-approximation, not studentised);
  * B = 10,000 resamples and the 95% level as the Primary defaults;
  * the block length is a CALLER decision between the two frozen values
    (Primary 5 trading days, Sensitivity 21) — this module deliberately gives
    `block_len` no default so neither can be silently promoted.

ENGINEERING CONVENTION (disclosed, deterministic, not frozen text):
  * the per-(seed, block) sub-stream derivation
    `np.random.default_rng([master_seed, STATS_STREAM_TAG, block_stream_key])`
    (M6_DESIGN §4). The frozen text freezes the master seeds only; a study that
    quotes a block-5 and a block-21 interval must not have them share a stream,
    so the block length enters the SeedSequence entropy as an integer. The
    derivation is a pure function of its inputs: it does not depend on the
    order in which series/blocks/seeds are processed, on wall-clock time, or on
    any module-level RNG state.
  * the QUOTED interval = the FIRST frozen master seed (7) by fixed convention.
    This is selection-proof: the convention predates any data, and "best of
    three" is prohibited. All three intervals are returned in full and the
    report must show all three (M6_DESIGN §4).
  * `numpy.percentile` with `method="linear"` (its default): endpoints at
    virtual index (m-1)*p of the sorted resampled means, linearly interpolated
    between neighbouring order statistics.

Reading the convergence block: `max_abs_ci_lo_diff` / `max_abs_ci_hi_diff` are
the max-minus-min spread of the three seeds' endpoints, i.e. the S0-level
disclosure counterpart of MC_METHOD_SPEC §5 rule (b) (three independent master
seeds must agree). This module reports the spread; it applies no tolerance and
declares no convergence verdict.
"""
from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from itsf.contracts import RESEARCH_BOOTSTRAP_SEEDS
from itsf.mc.bootstrap import stationary_bootstrap_indices

# --- frozen constants (# frozen: S0 §9) -------------------------------------
PRIMARY_BLOCK_DAYS = 5.0          # frozen: S0 §9 Primary 期望块长 5 交易日
SENSITIVITY_BLOCK_DAYS = 21.0     # frozen: S0 §9 Sensitivity 块长 21
N_BOOT = 10_000                   # frozen: S0 §9 10,000 次
CI_LEVEL = 0.95                   # frozen: S0 §9 百分位法 95% CI
PERCENTILE_METHOD = "linear"      # engineering: numpy default, pinned + disclosed

# Engineering stream tag (M6_DESIGN §4). Arbitrary but FIXED and distinct from
# the appendix-A grid tag, so the CI sub-streams and the grid sub-streams can
# never collide inside one master seed. NOT a seed: the seeds are frozen.
STATS_STREAM_TAG = 9001


def _validated_series(series: Sequence[float]) -> np.ndarray:
    """Daily USD P&L in trading-day order -> float64 1-D array. Fail closed.

    The stationary bootstrap preserves LOCAL dependence, so the caller's order
    carries meaning: the series must arrive in trading-day order and must not
    be re-sorted here. Non-finite values are rejected rather than dropped —
    silently discarding a NaN day would change the sample the interval speaks
    about (frozen S0 §3 NA policy: NA is reported, never deleted).
    """
    values = np.asarray(series, dtype=float)
    if values.ndim != 1:
        raise ValueError(f"series must be 1-D, got shape {values.shape}")
    if values.size < 2:
        raise ValueError(
            f"series needs >= 2 observations for a bootstrap CI, got "
            f"{values.size} — fail closed (frozen: S0 §9)")
    if not np.all(np.isfinite(values)):
        n_bad = int(np.count_nonzero(~np.isfinite(values)))
        raise ValueError(
            f"series holds {n_bad} non-finite value(s); they are NEVER silently "
            "dropped — resolve upstream (frozen: S0 §3 NA policy)")
    return values


def _validated_block_len(block_len: float) -> float:
    block = float(block_len)
    if not np.isfinite(block) or block <= 0.0:
        raise ValueError(f"block_len must be finite and > 0, got {block_len!r}")
    return block


def _validated_n_boot(n_boot: int) -> int:
    if int(n_boot) != n_boot or int(n_boot) < 1:
        raise ValueError(f"n_boot must be a positive integer, got {n_boot!r}")
    return int(n_boot)


def _validated_ci_level(ci_level: float) -> float:
    level = float(ci_level)
    if not 0.0 < level < 1.0:
        raise ValueError(f"ci_level must lie in (0, 1), got {ci_level!r}")
    return level


def _validated_seeds(master_seeds: Sequence[int]) -> tuple[int, ...]:
    """Master seeds must be a non-empty sequence of DISTINCT integers.

    Research randomness derives exclusively from RESEARCH_BOOTSTRAP_SEEDS
    (IR DR-02, # frozen: S0 §9 / Appendix A / MC_METHOD_SPEC §5 (b)); the
    parameter exists so a test can run a cheap single-seed case, not so a run
    can invent seeds.
    """
    seeds = tuple(int(s) for s in master_seeds)
    if not seeds:
        raise ValueError("master_seeds must be non-empty (frozen: S0 §9)")
    if len(set(seeds)) != len(seeds):
        raise ValueError(f"master_seeds must be distinct, got {seeds}")
    return seeds


def block_stream_key(block_len: float) -> int:
    """Integer SeedSequence component for a block length (engineering).

    Millis of a trading day: 5.0 -> 5000, 21.0 -> 21000. Integer so the
    entropy is exact and platform-independent (a float would put binary
    rounding inside the seed).
    """
    return int(round(_validated_block_len(block_len) * 1000))


def percentile_ci(values: Sequence[float],
                  ci_level: float = CI_LEVEL) -> tuple[float, float]:
    """Two-sided percentile interval at ((1-c)/2, 1-(1-c)/2).

    # frozen: S0 §9 百分位法 95% CI. Linear interpolation between order
    statistics (numpy's default `method="linear"`), pinned explicitly so a
    future numpy default change cannot move a quoted endpoint.
    """
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        raise ValueError("percentile_ci needs at least one value")
    level = _validated_ci_level(ci_level)
    alpha = 1.0 - level
    lo = float(np.percentile(arr, 100.0 * (alpha / 2.0),
                             method=PERCENTILE_METHOD))
    hi = float(np.percentile(arr, 100.0 * (1.0 - alpha / 2.0),
                             method=PERCENTILE_METHOD))
    return lo, hi


def resample_means(series: Sequence[float], block_len: float, n_boot: int,
                   master_seed: int) -> np.ndarray:
    """The n_boot resampled MEANS for ONE master seed (frozen: S0 §9).

    One Generator per (master_seed, block_len) drives all n_boot resamples in
    sequence, so resample b is a pure function of (seed, block, b): doubling
    n_boot for the MC_METHOD_SPEC §5 (a) convergence re-run reproduces the
    first n_boot resamples byte-identically and only appends new ones.
    """
    values = _validated_series(series)
    block = _validated_block_len(block_len)
    count = _validated_n_boot(n_boot)
    rng = np.random.default_rng(
        [int(master_seed), STATS_STREAM_TAG, block_stream_key(block)])
    n = int(values.shape[0])
    means = np.empty(count, dtype=float)
    for b in range(count):
        idx = stationary_bootstrap_indices(n, block, rng=rng)
        means[b] = float(values[idx].mean())
    return means


def _method_string(block_len: float, n_boot: int, ci_level: float,
                   seeds: tuple[int, ...], quoted_seed: int) -> str:
    """Full method disclosure carried WITH the numbers (never reconstructed)."""
    return (
        "stationary bootstrap (Politis-Romano, geometric blocks, circular "
        f"wrap) on the daily USD P&L series in trading-day order; expected "
        f"block length {block_len:g} trading days "
        f"(frozen S0 §9: Primary {PRIMARY_BLOCK_DAYS:g}, Sensitivity "
        f"{SENSITIVITY_BLOCK_DAYS:g}); {n_boot} resamples; statistic = mean; "
        f"percentile method {ci_level:.0%} CI on the resampled means, numpy "
        f"percentile method='{PERCENTILE_METHOD}'; master seeds {list(seeds)} "
        "run INDEPENDENTLY and all reported (frozen S0 §9 seeds {7,13,31}, "
        "contracts.RESEARCH_BOOTSTRAP_SEEDS; the run-infra provenance seed is "
        "never a research input); per-seed stream = "
        "default_rng([master_seed, STATS_STREAM_TAG="
        f"{STATS_STREAM_TAG}, block_stream_key={block_stream_key(block_len)}]) "
        "(disclosed engineering convention, M6_DESIGN §4); quoted interval = "
        f"master seed {quoted_seed} by FIXED convention (first frozen seed; "
        "the convention predates any data, best-of-three is prohibited); "
        "convergence block reports the max absolute endpoint spread across "
        "seeds (MC_METHOD_SPEC §5 rule (b) counterpart) and applies no "
        "tolerance of its own")


def _bootstrap_mean_ci_unchecked(series: Sequence[float], block_len: float,
                                 n_boot: int = N_BOOT, ci_level: float = CI_LEVEL,
                                 master_seeds: Sequence[int] = RESEARCH_BOOTSTRAP_SEEDS,
                                 ) -> dict:
    """Frozen S0 §9 percentile CI for the MEAN daily USD P&L — INTERNAL.

    UNCHECKED: unlike the public `bootstrap_mean_ci`, this accepts ANY
    `master_seeds` sequence, including one that is not
    contracts.RESEARCH_BOOTSTRAP_SEEDS. It exists ONLY so tests can exercise a
    cheap single-seed run or the seed-ORDER-dependent "quoted = first seed"
    convention without paying for three full seeds; production/report code
    must go through the public `bootstrap_mean_ci`, which enforces IR DR-02
    (# frozen: S0 §9 seeds {7,13,31}) before delegating here.

    Parameters
    ----------
    series : daily USD P&L, in trading-day order (order is load-bearing: the
        stationary bootstrap preserves local dependence through it).
    block_len : expected block length in trading days. NO DEFAULT — the caller
        passes the frozen Primary 5 or the frozen Sensitivity 21 explicitly
        (frozen: S0 §9); this module never picks one.
    n_boot, ci_level : frozen Primary values as defaults.
    master_seeds : frozen {7, 13, 31}; each seed is run INDEPENDENTLY to the
        full n_boot and all three intervals are returned.

    Returns
    -------
    {"per_seed": {seed: {"mean", "ci_lo", "ci_hi", "n_boot", "block_len"}},
     "convergence": {"max_abs_ci_lo_diff", "max_abs_ci_hi_diff"},
     "quoted_seed": first master seed, "quoted": that seed's dict,
     "method": full disclosure string}

    "mean" is the SAMPLE mean of `series` (identical across seeds by
    construction — the resamples move the interval, never the point estimate).
    """
    values = _validated_series(series)
    block = _validated_block_len(block_len)
    count = _validated_n_boot(n_boot)
    level = _validated_ci_level(ci_level)
    seeds = _validated_seeds(master_seeds)

    sample_mean = float(values.mean())
    per_seed: dict[int, dict[str, float | int]] = {}
    for master_seed in seeds:
        means = resample_means(values, block, count, master_seed)
        ci_lo, ci_hi = percentile_ci(means, level)
        per_seed[master_seed] = {
            "mean": sample_mean,
            "ci_lo": ci_lo,
            "ci_hi": ci_hi,
            "n_boot": count,
            "block_len": block,
        }

    los = [d["ci_lo"] for d in per_seed.values()]
    his = [d["ci_hi"] for d in per_seed.values()]
    quoted_seed = seeds[0]                  # fixed convention, never best-of
    return {
        "per_seed": per_seed,
        "convergence": {
            "max_abs_ci_lo_diff": float(max(los) - min(los)),
            "max_abs_ci_hi_diff": float(max(his) - min(his)),
        },
        "quoted_seed": quoted_seed,
        "quoted": per_seed[quoted_seed],
        "method": _method_string(block, count, level, seeds, quoted_seed),
    }


def bootstrap_mean_ci(series: Sequence[float], block_len: float,
                      n_boot: int = N_BOOT, ci_level: float = CI_LEVEL,
                      master_seeds: Sequence[int] = RESEARCH_BOOTSTRAP_SEEDS,
                      ) -> dict:
    """Frozen S0 §9 percentile CI for the MEAN daily USD P&L — PUBLIC entry.

    IR DR-02 mutation guard: `master_seeds` MUST be exactly
    `contracts.RESEARCH_BOOTSTRAP_SEEDS` (the frozen {7, 13, 31}, in that
    order) — the only seeds any research-path RNG may derive from. Any other
    value is REFUSED with ValueError rather than silently honoured, so a
    caller cannot swap in an unregistered seed set through this entry point.
    Tests that need a cheap single-seed run, a reordered-seed run, or an
    invalid-seed run to exercise `_validated_seeds` call
    `_bootstrap_mean_ci_unchecked` directly — a private helper that ONLY
    tests may use.

    See `_bootstrap_mean_ci_unchecked` for parameters and the return shape;
    this function does nothing but validate `master_seeds` and delegate.
    """
    seeds = tuple(int(s) for s in master_seeds)
    if seeds != RESEARCH_BOOTSTRAP_SEEDS:
        raise ValueError(
            "master_seeds must be exactly contracts.RESEARCH_BOOTSTRAP_SEEDS "
            f"{RESEARCH_BOOTSTRAP_SEEDS} — IR DR-02: the only seeds any "
            f"research-path RNG may derive from; got {seeds}. A test that "
            "needs different seeds must call _bootstrap_mean_ci_unchecked "
            "directly instead of this public entry point.")
    return _bootstrap_mean_ci_unchecked(series, block_len, n_boot=n_boot,
                                        ci_level=ci_level, master_seeds=seeds)
