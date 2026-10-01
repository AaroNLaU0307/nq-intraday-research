"""TASK 9 -- the sealed stationary block bootstrap.

    expected block length   5 events   (sensitivity: 10, reported, NOT primary)
    resamples               10,000
    seeds                   {7, 13, 31}
    interval                percentile, 95 %

Blocks are drawn in EVENT ORDER because 252 releases are not 252 independent
pieces of evidence: consecutive prints share a macro regime, and an expected
block of 5 keeps that dependence inside the resampled blocks (sealed I.1). The
convention is reused verbatim from ITSF's frozen S0 SS9 rather than
re-invented, so it cannot be tuned to R1 -- and nothing in this module takes a
tuning parameter that is not read off the sealed contract.

Two readings of the sealed text had to be made concrete, and neither changes a
sealed rule. Both are recorded in the S2 build report:

  * The interval is TWO-SIDED percentile 95 % (2.5 / 97.5). The sealed exclusion
    rule speaks of a "CI half-width", which only exists for a two-sided
    interval, and sealed C.2's "95 % lower bound" is then its lower endpoint.
    The test itself stays one-sided, as declared.
  * The three sealed seeds are run as a STABILITY SET: the primary interval is
    computed from the pooled 30,000 resample means, and the per-seed intervals
    are reported beside it. No seed is ever selected after seeing a result.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .contract import SealedContract
from .errors import R1Error


@dataclass(frozen=True)
class Interval:
    lower: float
    upper: float
    point: float
    level: float
    method: str
    block_events: int
    resamples: int
    seeds: tuple[int, ...]

    @property
    def half_width(self) -> float:
        return (self.upper - self.lower) / 2.0

    def excludes_below(self, threshold: float) -> bool:
        """Sealed C.2 exclusion: upper < M AND half-width < M."""
        return self.upper < threshold and self.half_width < threshold

    def clears(self, threshold: float) -> bool:
        """Sealed C.2 support side: the 95 % LOWER bound exceeds M."""
        return self.lower > threshold

    def spans(self, threshold: float) -> bool:
        return self.lower <= threshold <= self.upper


def _validate(values: np.ndarray, contract: SealedContract) -> None:
    if values.ndim != 1:
        raise R1Error("bootstrap input must be one-dimensional")
    if values.size == 0:
        raise R1Error("bootstrap on an empty sample -- refuse, do not return 0")
    if values.size == 1:
        raise R1Error(
            "bootstrap on a single event cannot produce an interval: every "
            "resample is that event. Refuse rather than emit a zero-width "
            "interval that looks like precision.")
    if not np.all(np.isfinite(values)):
        raise R1Error("bootstrap input contains NaN/inf -- missing data must be "
                      "excluded and counted upstream, never resampled")


def resample_means(values, block_events: int, resamples: int,
                   seed: int) -> np.ndarray:
    """Stationary (Politis-Romano) bootstrap means, in event order.

    Block lengths are geometric with mean `block_events`; indices wrap around
    the event sequence, which is what makes the scheme stationary.
    """
    v = np.asarray(values, dtype=float)
    n = v.size
    if block_events < 1:
        raise R1Error("expected block length must be >= 1 event")
    p = 1.0 / float(block_events)
    rng = np.random.default_rng(seed)

    new_block = rng.random((resamples, n)) < p
    new_block[:, 0] = True
    starts = rng.integers(0, n, size=(resamples, n))

    idx = np.empty((resamples, n), dtype=np.int64)
    idx[:, 0] = starts[:, 0]
    for i in range(1, n):
        idx[:, i] = np.where(new_block[:, i], starts[:, i],
                             (idx[:, i - 1] + 1) % n)
    return v[idx].mean(axis=1)


def bootstrap_interval(values, contract: SealedContract, *,
                       block_events: int | None = None,
                       seeds: tuple[int, ...] | None = None) -> Interval:
    """The sealed interval: pooled over the three declared seeds."""
    v = np.asarray(values, dtype=float)
    _validate(v, contract)
    block = block_events if block_events is not None \
        else contract.bootstrap_block_events
    seed_set = tuple(seeds) if seeds is not None else contract.bootstrap_seeds

    pooled = np.concatenate([
        resample_means(v, block, contract.bootstrap_resamples, s)
        for s in seed_set])
    alpha = (1.0 - contract.bootstrap_interval_level) / 2.0
    lo, hi = np.quantile(pooled, [alpha, 1.0 - alpha])
    return Interval(lower=float(lo), upper=float(hi), point=float(v.mean()),
                    level=contract.bootstrap_interval_level,
                    method=contract.bootstrap_interval_method,
                    block_events=block, resamples=contract.bootstrap_resamples,
                    seeds=seed_set)


def per_seed_intervals(values, contract: SealedContract, *,
                       block_events: int | None = None) -> dict[int, Interval]:
    """Reported beside the primary interval as a STABILITY check, never chosen."""
    return {s: bootstrap_interval(values, contract, block_events=block_events,
                                  seeds=(s,))
            for s in contract.bootstrap_seeds}


def sensitivity_interval(values, contract: SealedContract) -> Interval:
    """Sealed sensitivity: expected block 10. Reported, NEVER primary."""
    return bootstrap_interval(
        values, contract, block_events=contract.bootstrap_sensitivity_block_events)
