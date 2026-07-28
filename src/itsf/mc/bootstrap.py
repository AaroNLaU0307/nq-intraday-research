"""Stationary bootstrap world construction for the MC epistemic layer.

Scope (frozen: MC1 SS5):
  - B stationary-bootstrap worlds over the template trading-day list;
    expected block length = 5 trading days, geometric block lengths,
    circular wrap.
  - Randomness: numpy PCG64 via SeedSequence spawning from a master seed;
    frozen master seeds for the three-seed convergence check are 7 / 13 / 31.
  - Common random numbers (CRN): the SAME worlds list is reused across all
    configs/policies/platforms by construction — callers build worlds ONCE
    per (day_ids, B, master_seed) and feed the identical day-id sequences
    to every config (frozen: MC1 SS5 CRN).
  - The synthetic template calendar itself is injected as an ordered day
    list; bootstrap only decides which historical day outcome is placed on
    each template slot, never the calendar (frozen: MC1 SS4.1).

Synthetic-only at this stage: no real market data may flow through here
until the guards in itsf.guards clear (G9 + second-copy attestations).
"""
from __future__ import annotations

from collections.abc import Sequence

import numpy as np

# frozen: MC1 SS5 convergence rule (b) — three independent master seeds
MASTER_SEEDS = (7, 13, 31)

# frozen: MC1 SS5 — 认知层 block 长 5 交易日（S0 SS9 一致）
EXPECTED_BLOCK_DAYS = 5.0


def stationary_bootstrap_indices(n: int, expected_block: float = EXPECTED_BLOCK_DAYS,
                                 *, rng: np.random.Generator) -> np.ndarray:
    """Politis–Romano stationary bootstrap index sequence of length n.

    Geometric block lengths with mean `expected_block`: at each step a new
    block starts with probability p = 1/expected_block at a uniform random
    index; otherwise the previous index advances by one with CIRCULAR wrap
    (index n-1 continues to 0).  # frozen: MC1 SS5 stationary bootstrap
    """
    if n < 0:
        raise ValueError("n must be >= 0")
    if expected_block <= 0:
        raise ValueError("expected_block must be > 0")
    if n == 0:
        return np.empty(0, dtype=np.int64)
    p = 1.0 / float(expected_block)
    out = np.empty(n, dtype=np.int64)
    current = int(rng.integers(0, n))          # first block starts uniform
    out[0] = current
    for t in range(1, n):
        if rng.random() < p:                   # geometric restart
            current = int(rng.integers(0, n))
        else:
            current = (current + 1) % n        # circular wrap
        out[t] = current
    return out


def build_worlds(day_ids: Sequence[str], B: int, master_seed: int,
                 expected_block: float = EXPECTED_BLOCK_DAYS) -> list[list[str]]:
    """Build B bootstrap worlds as day-id sequences (each of length len(day_ids)).

    Child seeds are derived via SeedSequence(master_seed).spawn(B); world b
    uses Generator(PCG64(child_b)).  # frozen: MC1 SS5 seed derivation, PCG64
    Deterministic in (day_ids, B, master_seed, expected_block): every config
    that calls with the same arguments receives byte-identical worlds — this
    is how CRN across configs is guaranteed by construction. Callers MUST
    reuse one returned list across all configs of a comparison, never
    re-draw per config.  # frozen: MC1 SS5 common random numbers
    """
    if B <= 0:
        raise ValueError("B must be >= 1")
    if len(day_ids) == 0:
        raise ValueError("day_ids must be non-empty")
    days = list(day_ids)
    n = len(days)
    children = np.random.SeedSequence(master_seed).spawn(B)
    worlds: list[list[str]] = []
    for child in children:
        rng = np.random.Generator(np.random.PCG64(child))
        idx = stationary_bootstrap_indices(n, expected_block, rng=rng)
        worlds.append([days[i] for i in idx])
    return worlds
