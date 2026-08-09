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

import math
from collections.abc import Mapping, Sequence

import numpy as np

from itsf.contracts import RESEARCH_BOOTSTRAP_SEEDS, BootstrapMethod
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

    IR DR-02 frozen-seed guard: unlike `_bootstrap_mean_ci_unchecked`, this
    function IS public (it is `bootstrap_mean_ci`'s per-seed inner loop, not
    a test-only helper), so it cannot simply trust an arbitrary caller-passed
    `master_seed` the way an underscore-prefixed helper could. `master_seed`
    must be one of `contracts.RESEARCH_BOOTSTRAP_SEEDS` (7, 13, or 31) —
    membership, not the full-tuple equality `bootstrap_mean_ci` enforces,
    because this entry point takes ONE seed at a time, not all three.
    """
    seed = int(master_seed)
    if seed not in RESEARCH_BOOTSTRAP_SEEDS:
        raise ValueError(
            f"master_seed must be one of contracts.RESEARCH_BOOTSTRAP_SEEDS "
            f"{RESEARCH_BOOTSTRAP_SEEDS} — IR DR-02: the only seeds any "
            f"research-path RNG may derive from; got {seed}")
    values = _validated_series(series)
    block = _validated_block_len(block_len)
    count = _validated_n_boot(n_boot)
    rng = np.random.default_rng(
        [seed, STATS_STREAM_TAG, block_stream_key(block)])
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
            "block_len": int(block) if block == int(block) else block,
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
    # M6.1.2 N9: a resample COUNT is integral by nature — refuse floats so
    # 10000.0 can never masquerade as the frozen 10,000. The expected block
    # LENGTH stays numeric (it parameterises a geometric distribution and
    # stationary_bootstrap_indices accepts float by design); the payload
    # gate separately pins the frozen values 5/21.
    if isinstance(n_boot, bool) or not isinstance(n_boot, int):
        raise ValueError("n_boot must be an int (frozen S0 sec.9: 10,000); "
                         f"got {type(n_boot).__name__}")
    return _bootstrap_mean_ci_unchecked(series, block_len, n_boot=n_boot,
                                        ci_level=ci_level, master_seeds=seeds)


# ===========================================================================
# DR-4 (Aaron 2026-08-10) — this module is the production CONSUMER of the
# ruled `contracts.BootstrapMethod`.
#
# Every function below takes the method dataclass as an EXPLICIT parameter and
# dispatches on its fields. The ruled STRINGS that appear here are DISPATCH
# KEYS — the exact rule ids this module implements — and nothing selects them
# on its own: an un-ruled value is a ValueError with a precise code (fail
# closed), never a silent default.
#
# WHAT IS BEING WIRED, AND WHAT IS NOT. The sampler is untouched: the
# Politis-Romano stationary bootstrap core (`stationary_bootstrap_indices`,
# expected block length 5 trading days, circular wrap) stays exactly as it is.
# What DR-4 fixes is the POPULATION the sampler resamples, the STATISTIC taken
# on each resample, the per-seed resample BUDGET, the QUOTED seed and the CRN
# SCOPE.
# ===========================================================================

#: DISPATCH KEYS — the exact ruled `BootstrapMethod` field values implemented.
BOOTSTRAP_POPULATION_RULE = "full_eligible_trading_day_sequence"
BOOTSTRAP_NA_DAY_RULE = "n1_drop_from_sequence_disclose_count"
BOOTSTRAP_STATISTIC = "per_trading_day_mean_usd"
BOOTSTRAP_QUOTED_SEED_RULE_PREFIX = "fixed_seed_"
BOOTSTRAP_CRN_SCOPE = "shared_within_theta_engine_scenario"

#: Day states of the ruled population (DR-4.1/4.2).
#:  * `oracle_traded`         — the oracle traded this day AT THIS THETA;
#:                              it contributes its daily USD P&L;
#:  * `eligible_not_selected` — a structurally eligible trading day the oracle
#:                              did NOT select; it contributes EXACTLY 0.0 and
#:                              is IN the sequence (this is the whole point of
#:                              "full eligible trading-day sequence": a day the
#:                              strategy sat out is a real 0, not a missing
#:                              observation);
#:  * `na`                    — direction undeterminable / Y_cont NA. DROPPED
#:                              from the sequence, and the dropped COUNT is
#:                              returned and must be disclosed (rule n1).
#: Whole-day FROZEN exclusions (half day / no-trade / >10% missing) are not
#: day states at all: they never enter `day_states` in the first place.
DAY_STATE_ORACLE_TRADED = "oracle_traded"
DAY_STATE_ELIGIBLE_NOT_SELECTED = "eligible_not_selected"
DAY_STATE_NA = "na"
DAY_STATES = (DAY_STATE_ORACLE_TRADED, DAY_STATE_ELIGIBLE_NOT_SELECTED,
              DAY_STATE_NA)

#: Marker key of a sequence built by `build_bootstrap_day_sequence`. The ruled
#: entry point accepts NOTHING else — a bare list of oracle-day P&L (the
#: pre-ruling population) is refused rather than silently resampled.
DAY_SEQUENCE_KIND = "s0_bootstrap_day_sequence_v1"


def _require_bootstrap_method(method) -> BootstrapMethod:
    if not isinstance(method, BootstrapMethod):
        raise ValueError(
            f"bootstrap_method_not_a_BootstrapMethod:{type(method).__name__}")
    return method


def _require_population_rules(method: BootstrapMethod) -> None:
    """Population + NA + statistic rule ids, all three or nothing."""
    if method.population != BOOTSTRAP_POPULATION_RULE:
        raise ValueError(f"bootstrap_population_not_ruled:{method.population}")
    if method.na_day_rule != BOOTSTRAP_NA_DAY_RULE:
        raise ValueError(
            f"bootstrap_na_day_rule_not_ruled:{method.na_day_rule}")
    if method.statistic != BOOTSTRAP_STATISTIC:
        raise ValueError(f"bootstrap_statistic_not_ruled:{method.statistic}")


def ruled_quoted_seed(method: BootstrapMethod) -> int:
    """The seed whose interval is QUOTED, read off `quoted_seed_rule`.

    The rule id CARRIES the seed (`fixed_seed_<n>`); the number is parsed, not
    restated, and must be one of `contracts.RESEARCH_BOOTSTRAP_SEEDS`. All
    seeds' intervals are still computed and returned — "quoted" selects which
    one the report leads with, by a convention that predates any data.
    """
    _require_bootstrap_method(method)
    rule = method.quoted_seed_rule
    if not isinstance(rule, str) or not rule.startswith(
            BOOTSTRAP_QUOTED_SEED_RULE_PREFIX):
        raise ValueError(f"bootstrap_quoted_seed_rule_not_ruled:{rule}")
    try:
        seed = int(rule[len(BOOTSTRAP_QUOTED_SEED_RULE_PREFIX):])
    except ValueError:
        raise ValueError(
            f"bootstrap_quoted_seed_rule_not_ruled:{rule}") from None
    if seed not in RESEARCH_BOOTSTRAP_SEEDS:
        raise ValueError(f"bootstrap_quoted_seed_not_a_research_seed:{seed}")
    return seed


def theta_stream_key(theta: float) -> int:
    """Integer SeedSequence component for a theta (engineering, exact).

    Millis of the continuation threshold: 0.5 -> 500, 0.3 -> 300. Integer so
    the entropy is exact and platform-independent (a float would put binary
    rounding inside the seed) and NON-NEGATIVE, which `np.random.SeedSequence`
    requires. Shared with `itsf.s0.gridmix` so the two consumers can never
    encode the same theta two different ways.
    """
    value = float(theta)
    if not math.isfinite(value):
        raise ValueError(f"theta_not_finite:{theta!r}")
    millis = round(value * 1000.0)
    if abs(value * 1000.0 - millis) > 1e-6:
        raise ValueError(f"theta_not_representable_in_millis:{theta!r}")
    if millis < 0:
        raise ValueError(f"theta_negative_cannot_seed:{theta!r}")
    return int(millis)


def _normalized_day_row(row, index: int) -> tuple[str, str, object]:
    """One day-state row -> (trade_date, state, value). Fail closed."""
    if isinstance(row, Mapping):
        try:
            date = row["trade_date"]
            state = row["state"]
        except KeyError as exc:
            raise ValueError(
                f"day_state_row_missing_key:{index}:{exc.args[0]}") from None
        value = row.get("daily_pnl_usd")
    elif isinstance(row, Sequence) and not isinstance(row, (str, bytes)):
        items = tuple(row)
        if len(items) == 2:
            date, state = items
            value = None
        elif len(items) == 3:
            date, state, value = items
        else:
            raise ValueError(f"day_state_row_wrong_arity:{index}:{len(items)}")
    else:
        raise ValueError(
            f"day_state_row_unsupported:{index}:{type(row).__name__}")
    if not isinstance(date, str) or not date:
        raise ValueError(f"day_state_trade_date_not_a_str:{index}")
    if state not in DAY_STATES:
        raise ValueError(f"bootstrap_day_state_not_ruled:{state}")
    return date, state, value


def build_bootstrap_day_sequence(day_states, method: BootstrapMethod) -> dict:
    """The ruled DR-4 bootstrap POPULATION: one ordered daily-USD sequence.

    `day_states` is the FULL structurally-eligible trading-day list for ONE
    (theta, engine, cost scenario), in DATE ORDER — each row a
    ``(trade_date, state)`` / ``(trade_date, state, daily_pnl_usd)`` tuple or a
    Mapping with those keys. `state` is one of `DAY_STATES`:

      * `oracle_traded`         -> the day's daily USD P&L enters the sequence;
      * `eligible_not_selected` -> 0.0 enters the sequence (a sat-out day is a
                                   real zero, never a hole). A non-zero P&L on
                                   such a row is a caller bug and is REFUSED;
      * `na`                    -> the day is DROPPED and counted (rule n1).

    Order is load-bearing (the stationary bootstrap resamples local
    dependence), so the dates must be STRICTLY ASCENDING; unsorted or
    duplicated input is refused rather than silently sorted.

    The dropped-NA count travels ON the returned object and the ruled entry
    point only accepts that object, so an NA count cannot be lost between the
    two calls — "disclose the count" is enforced by construction, not by
    convention.
    """
    _require_bootstrap_method(method)
    _require_population_rules(method)

    dates: list[str] = []
    series: list[float] = []
    na_dates: list[str] = []
    n_traded = 0
    n_not_selected = 0
    seen: set[str] = set()
    previous: str | None = None

    for index, row in enumerate(day_states):
        date, state, value = _normalized_day_row(row, index)
        if date in seen:
            raise ValueError(f"day_state_duplicate_trade_date:{date}")
        if previous is not None and date <= previous:
            raise ValueError(
                f"day_state_sequence_not_in_ascending_date_order:{date}")
        seen.add(date)
        previous = date

        if state == DAY_STATE_NA:
            na_dates.append(date)
            continue
        if state == DAY_STATE_ELIGIBLE_NOT_SELECTED:
            if value is not None and float(value) != 0.0:
                raise ValueError(
                    f"eligible_not_selected_day_carries_pnl:{date}")
            pnl = 0.0
            n_not_selected += 1
        else:
            if value is None:
                raise ValueError(f"oracle_traded_day_missing_pnl:{date}")
            pnl = float(value)
            if not math.isfinite(pnl):
                raise ValueError(f"oracle_traded_day_pnl_non_finite:{date}")
            n_traded += 1
        dates.append(date)
        series.append(pnl)

    return {
        "kind": DAY_SEQUENCE_KIND,
        "dates": tuple(dates),
        "series": tuple(series),
        "n_days_in_sequence": len(series),
        "n_oracle_traded_days": n_traded,
        "n_eligible_not_selected_days": n_not_selected,
        "n_na_days_dropped": len(na_dates),
        "na_dates": tuple(na_dates),
        "population": method.population,
        "na_day_rule": method.na_day_rule,
        "statistic": method.statistic,
    }


def _require_day_sequence(day_sequence) -> dict:
    if not isinstance(day_sequence, Mapping):
        raise ValueError(
            "bootstrap_population_not_from_ruled_sequence_builder:"
            f"{type(day_sequence).__name__}")
    if day_sequence.get("kind") != DAY_SEQUENCE_KIND:
        raise ValueError(
            "bootstrap_population_not_from_ruled_sequence_builder:"
            f"{day_sequence.get('kind')!r}")
    return dict(day_sequence)


def _require_crn_scope(method: BootstrapMethod) -> None:
    if method.crn_scope != BOOTSTRAP_CRN_SCOPE:
        raise ValueError(f"bootstrap_crn_scope_not_ruled:{method.crn_scope}")


def crn_stream_entropy(theta: float, master_seed: int, block_len: float,
                       method: BootstrapMethod) -> list[int]:
    """SeedSequence entropy of the CRN resample-index stream (DR-4.7).

    KEYED BY (theta, master_seed) AND NOTHING ABOUT THE COMPARISON. Engine and
    cost scenario are not parameters of this function and cannot be — that is
    how ``shared_within_theta_engine_scenario`` is guaranteed BY CONSTRUCTION
    rather than by discipline: E1/Base and E2/Severe at one theta and one seed
    receive IDENTICAL resampled day-index sequences, so their intervals differ
    only through the day VALUES, never through the draws.

    `block_stream_key` is the ONE further component, and it is not a scope
    widening: frozen S0 §9 quotes a Primary block-5 AND a Sensitivity block-21
    interval from the same days, the block length parameterises the sampler
    itself, and the pre-existing M6_DESIGN §4 convention keeps those two from
    sharing a stream. It is disclosed in the method string.
    """
    _require_bootstrap_method(method)
    _require_crn_scope(method)
    seed = int(master_seed)
    if seed not in RESEARCH_BOOTSTRAP_SEEDS:
        raise ValueError(
            f"bootstrap_master_seed_not_a_research_seed:{seed} "
            f"(IR DR-02: {RESEARCH_BOOTSTRAP_SEEDS})")
    return [seed, STATS_STREAM_TAG, theta_stream_key(theta),
            block_stream_key(block_len)]


def crn_resample_indices(n_days: int, *, theta: float, master_seed: int,
                         block_len: float, n_boot: int,
                         method: BootstrapMethod) -> np.ndarray:
    """The `(n_boot, n_days)` CRN resample-INDEX stream for one (theta, seed).

    Materialises the streams; `resample_means_crn` consumes the identical
    sequence lazily (both drive one Generator through the same loop), so this
    is the observable form of what the interval computation actually used.
    Callers with the frozen n_boot of 10,000 and ~1,000 days should prefer the
    lazy path — this one is for verification and disclosure.
    """
    entropy = crn_stream_entropy(theta, master_seed, block_len, method)
    block = _validated_block_len(block_len)
    count = _validated_n_boot(n_boot)
    if int(n_days) < 1:
        raise ValueError(f"n_days must be >= 1, got {n_days!r}")
    rng = np.random.default_rng(entropy)
    out = np.empty((count, int(n_days)), dtype=np.int64)
    for b in range(count):
        out[b] = stationary_bootstrap_indices(int(n_days), block, rng=rng)
    return out


def resample_means_crn(series: Sequence[float], *, theta: float,
                       master_seed: int, block_len: float, n_boot: int,
                       method: BootstrapMethod) -> np.ndarray:
    """The n_boot resampled per-trading-day MEANS for ONE (theta, seed).

    Statistic = the MEAN over the resampled SEQUENCE (ruled
    `per_trading_day_mean_usd`): the sequence already carries a 0.0 for every
    eligible day the oracle sat out, so this is a per-TRADING-day mean, not a
    per-ORACLE-day mean. Feeding a traded-days-only series here would compute
    the un-ruled statistic — which is why the public entry point refuses
    anything but a `build_bootstrap_day_sequence` object.

    Draw b is a pure function of (theta, seed, block, b): one Generator drives
    all n_boot resamples in order, so doubling n_boot reproduces the first
    n_boot resamples byte-identically and only appends new ones.
    """
    _require_population_rules(_require_bootstrap_method(method))
    entropy = crn_stream_entropy(theta, master_seed, block_len, method)
    values = _validated_series(series)
    block = _validated_block_len(block_len)
    count = _validated_n_boot(n_boot)
    rng = np.random.default_rng(entropy)
    n = int(values.shape[0])
    means = np.empty(count, dtype=float)
    for b in range(count):
        idx = stationary_bootstrap_indices(n, block, rng=rng)
        means[b] = float(values[idx].mean())
    return means


def _ruled_method_string(method: BootstrapMethod, block_len: float,
                         n_boot: int, ci_level: float, seeds: tuple[int, ...],
                         quoted_seed: int, sequence: Mapping) -> str:
    """Full DR-4 disclosure carried WITH the numbers (never reconstructed)."""
    return (
        "stationary bootstrap (Politis-Romano, geometric blocks, circular "
        f"wrap), expected block length {block_len:g} trading days (frozen S0 "
        f"§9: Primary {PRIMARY_BLOCK_DAYS:g}, Sensitivity "
        f"{SENSITIVITY_BLOCK_DAYS:g}); POPULATION = {method.population} — the "
        "full structurally-eligible trading-day sequence in date order, an "
        "oracle-traded day contributing its daily USD P&L and an "
        "eligible-but-not-selected day contributing exactly 0.0 "
        f"({sequence['n_oracle_traded_days']} traded, "
        f"{sequence['n_eligible_not_selected_days']} sat out, "
        f"{sequence['n_days_in_sequence']} in the sequence); NA days "
        "(direction undeterminable / Y_cont NA) DROPPED per "
        f"{method.na_day_rule} with the count disclosed: n_na_days_dropped = "
        f"{sequence['n_na_days_dropped']}; whole-day frozen exclusions are "
        f"not in the sequence at all; STATISTIC = {method.statistic} (mean "
        f"over the resampled sequence); {n_boot} resamples PER SEED "
        "(n_boot_per_seed=True) for each of the master seeds "
        f"{list(seeds)} (frozen S0 §9 seeds 7/13/31, "
        "contracts.RESEARCH_BOOTSTRAP_SEEDS; the run-infra provenance seed is "
        f"never a research input), {n_boot * len(seeds)} draws in total; "
        f"percentile method {ci_level:.0%} CI on the resampled means with "
        f"numpy percentile method='{method.percentile_interpolation}'; quoted "
        f"interval = master seed {quoted_seed} per {method.quoted_seed_rule} "
        "(fixed convention predating any data; best-of-three is prohibited); "
        f"CRN scope {method.crn_scope} — the resample-index streams are keyed "
        "by (theta, master_seed) and by NOTHING about the comparison, so one "
        "theta's engine x scenario cells reuse identical resampled day-index "
        "sequences (block length also enters the stream so the frozen §9 "
        "Primary and Sensitivity intervals do not share one; disclosed "
        "engineering convention, M6_DESIGN §4); convergence block reports the "
        "max absolute endpoint spread across seeds (MC_METHOD_SPEC §5 rule "
        "(b) counterpart) and applies no tolerance of its own")


def bootstrap_mean_ci_ruled(day_sequence: Mapping, *, theta: float,
                            method: BootstrapMethod, block_len: float,
                            n_boot: int = N_BOOT, ci_level: float = CI_LEVEL,
                            master_seeds: Sequence[int]
                            = RESEARCH_BOOTSTRAP_SEEDS) -> dict:
    """The ruled DR-4 percentile CI for the per-TRADING-DAY mean USD P&L.

    `day_sequence` MUST be a `build_bootstrap_day_sequence` object — a bare
    series is refused, because the difference between the ruled population and
    the pre-ruling one (oracle-traded days only) is invisible in a plain list
    of floats and would silently change the statistic.

    Every DR-4 sub-decision is read off `method` and validated before a single
    draw: population / NA rule / statistic (via the sequence builder),
    `n_boot_per_seed` (must be True — the budget is PER seed, so three seeds
    cost 3 x n_boot draws), `quoted_seed_rule`, `percentile_interpolation` and
    `crn_scope`. Any un-ruled value raises with a precise code.

    Returns `_bootstrap_mean_ci_unchecked`'s shape plus the DR-4 disclosure
    fields (`n_na_days_dropped`, the population counts, `theta`,
    `n_boot_total`, `crn_stream_entropy_by_seed`).
    """
    _require_bootstrap_method(method)
    _require_population_rules(method)
    _require_crn_scope(method)
    sequence = _require_day_sequence(day_sequence)

    if method.n_boot_applies_per_seed is not True:
        raise ValueError(
            f"bootstrap_n_boot_per_seed_not_ruled:{method.n_boot_per_seed}")
    if method.percentile_interpolation != PERCENTILE_METHOD:
        raise ValueError("bootstrap_percentile_interpolation_not_ruled:"
                         f"{method.percentile_interpolation}")
    quoted_seed = ruled_quoted_seed(method)

    seeds = tuple(int(s) for s in master_seeds)
    if seeds != RESEARCH_BOOTSTRAP_SEEDS:
        raise ValueError(
            "master_seeds must be exactly contracts.RESEARCH_BOOTSTRAP_SEEDS "
            f"{RESEARCH_BOOTSTRAP_SEEDS} — IR DR-02: the only seeds any "
            f"research-path RNG may derive from; got {seeds}")
    if quoted_seed not in seeds:
        raise ValueError(f"bootstrap_quoted_seed_not_run:{quoted_seed}")
    if isinstance(n_boot, bool) or not isinstance(n_boot, int):
        raise ValueError("n_boot must be an int (frozen S0 sec.9: 10,000); "
                         f"got {type(n_boot).__name__}")

    values = _validated_series(sequence["series"])
    block = _validated_block_len(block_len)
    count = _validated_n_boot(n_boot)
    level = _validated_ci_level(ci_level)

    sample_mean = float(values.mean())
    per_seed: dict[int, dict[str, float | int]] = {}
    entropy_by_seed: dict[int, list[int]] = {}
    for master_seed in seeds:
        entropy_by_seed[master_seed] = crn_stream_entropy(
            theta, master_seed, block, method)
        means = resample_means_crn(values, theta=theta,
                                   master_seed=master_seed, block_len=block,
                                   n_boot=count, method=method)
        ci_lo, ci_hi = percentile_ci(means, level)
        per_seed[master_seed] = {
            "mean": sample_mean,
            "ci_lo": ci_lo,
            "ci_hi": ci_hi,
            "n_boot": count,
            "block_len": int(block) if block == int(block) else block,
        }

    los = [d["ci_lo"] for d in per_seed.values()]
    his = [d["ci_hi"] for d in per_seed.values()]
    return {
        "per_seed": per_seed,
        "convergence": {
            "max_abs_ci_lo_diff": float(max(los) - min(los)),
            "max_abs_ci_hi_diff": float(max(his) - min(his)),
        },
        "quoted_seed": quoted_seed,
        "quoted": per_seed[quoted_seed],
        "quoted_seed_rule": method.quoted_seed_rule,
        "n_boot_per_seed": True,
        "n_boot_total": count * len(seeds),
        "theta": float(theta),
        "theta_stream_key": theta_stream_key(theta),
        "crn_scope": method.crn_scope,
        "crn_stream_entropy_by_seed": entropy_by_seed,
        "population": sequence["population"],
        "statistic": sequence["statistic"],
        "na_day_rule": sequence["na_day_rule"],
        "n_days_in_sequence": sequence["n_days_in_sequence"],
        "n_oracle_traded_days": sequence["n_oracle_traded_days"],
        "n_eligible_not_selected_days":
            sequence["n_eligible_not_selected_days"],
        "n_na_days_dropped": sequence["n_na_days_dropped"],
        "na_dates": list(sequence["na_dates"]),
        "method": _ruled_method_string(method, block, count, level, seeds,
                                       quoted_seed, sequence),
    }
