"""Tests for itsf.mc.bootstrap and itsf.mc.account.

Account/sizing tests live here (not in a separate file) because the
subagent ownership list is exactly test_bootstrap.py + test_verdict.py.
All paths are SYNTHETIC (tests/conftest.py generators) — no real data.
"""
from __future__ import annotations

import numpy as np
import pytest

from conftest import make_trade_path
from itsf import contracts
from itsf.guards import RunBlockedError
from itsf.mc import bootstrap as mc_bootstrap
from itsf.mc.account import (LUCID_ABSOLUTE_MAX_MICROS,
                             TOPSTEP_ABSOLUTE_MAX_MICROS, PRIMARY_POLICY,
                             buffer_at_entry, n_micros, risk_budget_usd,
                             run_account, run_real_study)
from itsf.mc.bootstrap import (EXPECTED_BLOCK_DAYS, MASTER_SEEDS,
                               build_worlds, stationary_bootstrap_indices)
from itsf.mc.platforms.base import TrailingFloorEngine

DAY_IDS = [f"2026-08-{i:02d}" for i in range(1, 61)]  # synthetic template ids


def _rng(seed=7):
    return np.random.Generator(np.random.PCG64(np.random.SeedSequence(seed)))


# ---------------------------------------------------------------------------
# bootstrap: seeds / determinism / CRN
# ---------------------------------------------------------------------------

def test_frozen_master_seeds():
    # frozen: MC1 SS5 convergence rule (b)
    assert MASTER_SEEDS == (7, 13, 31)
    assert EXPECTED_BLOCK_DAYS == 5.0


def test_master_seeds_is_single_sourced_from_contracts():
    """# IR DR-02 mutation guard: itsf.mc.bootstrap.MASTER_SEEDS must BE
    contracts.RESEARCH_BOOTSTRAP_SEEDS (same object), not a local copy that
    could drift from the one research-seed source of truth."""
    assert mc_bootstrap.MASTER_SEEDS is contracts.RESEARCH_BOOTSTRAP_SEEDS


def test_same_master_seed_identical_worlds():
    w1 = build_worlds(DAY_IDS, B=16, master_seed=7)
    w2 = build_worlds(DAY_IDS, B=16, master_seed=7)
    assert w1 == w2                      # CRN across configs by construction


def test_different_master_seeds_differ():
    w7 = build_worlds(DAY_IDS, B=16, master_seed=7)
    w13 = build_worlds(DAY_IDS, B=16, master_seed=13)
    w31 = build_worlds(DAY_IDS, B=16, master_seed=31)
    assert w7 != w13 and w7 != w31 and w13 != w31


def test_worlds_shape_and_membership():
    B = 8
    worlds = build_worlds(DAY_IDS, B=B, master_seed=7)
    assert len(worlds) == B
    pool = set(DAY_IDS)
    for w in worlds:
        assert len(w) == len(DAY_IDS)
        assert set(w) <= pool
    # inner worlds are not all identical (child streams independent)
    assert any(worlds[0] != w for w in worlds[1:])


def test_build_worlds_rejects_degenerate_inputs():
    with pytest.raises(ValueError):
        build_worlds(DAY_IDS, B=0, master_seed=7)
    with pytest.raises(ValueError):
        build_worlds([], B=4, master_seed=7)


# ---------------------------------------------------------------------------
# bootstrap: block geometry
# ---------------------------------------------------------------------------

def test_indices_in_range():
    idx = stationary_bootstrap_indices(500, rng=_rng())
    assert idx.shape == (500,)
    assert idx.min() >= 0 and idx.max() < 500


def test_expected_block_length_within_tolerance():
    # frozen: MC1 SS5 — geometric blocks, mean 5 trading days
    rng = _rng(7)
    n = 2000
    runs: list[int] = []
    for _ in range(50):
        idx = stationary_bootstrap_indices(n, expected_block=5.0, rng=rng)
        length = 1
        for t in range(1, n):
            if idx[t] == (idx[t - 1] + 1) % n:
                length += 1
            else:
                runs.append(length)
                length = 1
        # final run censored — dropped
    mean = sum(runs) / len(runs)
    assert 4.5 < mean < 5.5, f"observed mean block length {mean:.3f}"


def test_circular_wrap():
    # expected_block astronomically large -> one continuous run that must
    # wrap n-1 -> 0 (frozen: MC1 SS5 circular wrap)
    n = 20
    idx = stationary_bootstrap_indices(n, expected_block=1e12, rng=_rng(31))
    start = idx[0]
    assert all(idx[t] == (start + t) % n for t in range(n))
    if start != 0:
        assert 0 in idx[1:]              # the wrap actually occurred


# ---------------------------------------------------------------------------
# account: sizing policies and integer caps
# ---------------------------------------------------------------------------

def test_primary_policy_is_p2():
    # frozen: MC1 SS2.5 Primary sizing = P2 $100
    assert PRIMARY_POLICY == "P2"
    assert risk_budget_usd("P2", buffer=0.0) == 100.0


def test_policy_budgets():
    # frozen: MC1 SS3 P1 $75 / P2 $100 / P3 4% buffer / P4 ladder
    assert risk_budget_usd("P1", 5000.0) == 75.0
    assert risk_budget_usd("P2", 5000.0) == 100.0
    assert risk_budget_usd("P3", 2000.0) == pytest.approx(80.0)
    assert risk_budget_usd("P4", 1600.0) == 100.0   # >1500
    assert risk_budget_usd("P4", 1500.0) == 75.0    # 800–1500 band
    assert risk_budget_usd("P4", 800.0) == 75.0
    assert risk_budget_usd("P4", 799.0) == 50.0     # <800
    with pytest.raises(ValueError):
        risk_budget_usd("P9", 100.0)


def test_buffer_is_mll_anchored():
    # frozen: MC1 SS3 buffer_at_entry = pre-entry equity - current MLL floor
    assert buffer_at_entry(50500.0, 48000.0) == 2500.0


def test_integer_floor():
    assert n_micros(100.0, 30.0, scaling_cap_micros=40) == 3


def test_scaling_cap_binds():
    # raw floor = 100 but tier cap 20 binds (frozen: MC1 SS3 min-triple)
    assert n_micros(10000.0, 100.0, scaling_cap_micros=20) == 20


def test_absolute_max_binds():
    # Ruling R2: per-platform absolute caps; platform scaling cap embeds its
    # own absolute max, n_micros clips extra only when explicitly passed.
    # frozen: platform_params lucidflex_50k (40) / topstep_50k (50)
    assert LUCID_ABSOLUTE_MAX_MICROS == 40
    assert TOPSTEP_ABSOLUTE_MAX_MICROS == 50
    assert n_micros(100000.0, 10.0, scaling_cap_micros=999,
                    absolute_max_micros=LUCID_ABSOLUTE_MAX_MICROS) == 40
    assert n_micros(100000.0, 10.0, scaling_cap_micros=999,
                    absolute_max_micros=TOPSTEP_ABSOLUTE_MAX_MICROS) == 50
    assert n_micros(100000.0, 10.0, scaling_cap_micros=30) == 30


def test_anchor_bigger_than_budget_gives_zero():
    assert n_micros(100.0, 150.0, scaling_cap_micros=40) == 0


def test_nonpositive_budget_gives_zero():
    assert n_micros(0.0, 100.0, scaling_cap_micros=40) == 0
    assert n_micros(-25.0, 100.0, scaling_cap_micros=40) == 0


# ---------------------------------------------------------------------------
# account: run_account day loop (synthetic paths only)
# ---------------------------------------------------------------------------

class _StubPlatform:
    """Minimal PlatformLike for the day loop (lifecycle owned elsewhere)."""

    def __init__(self, balance=50000.0, floor=48000.0, cap=40):
        self.balance = balance
        self.engine = TrailingFloorEngine(floor=floor, trail_distance=2000.0,
                                          lock_at=50100.0)
        self.phase = "funded"
        self._cap = cap

    def max_contracts_today(self) -> int:
        return self._cap


def test_skip_counted_when_anchor_exceeds_budget():
    # frozen: MC1 SS3 n=0 -> skip and count
    day = "2026-08-03"
    path = make_trade_path([10.0, 20.0], date=day)
    path.sizing_anchor_usd = 150.0       # > P2 budget of 100
    plat = _StubPlatform()
    events, summary = run_account([day], plat, {day: path}, policy="P2")
    assert summary["skips"] == 1
    assert summary["trades"] == 0
    assert plat.balance == 50000.0
    assert events[0].notes == "skip_n0"


def test_normal_day_settles_close_path_and_updates_floor():
    day = "2026-08-03"
    path = make_trade_path([100.0, 200.0], date=day, final=200.0)
    path.sizing_anchor_usd = 50.0        # budget 100 -> n = 2
    plat = _StubPlatform()
    events, summary = run_account([day], plat, {day: path}, policy="P2")
    assert summary["trades"] == 1 and not summary["breached"]
    assert plat.balance == pytest.approx(50000.0 + 2 * 200.0)
    # eod_update: min(50100, max(48000, 50400-2000)) = 48400
    assert plat.engine.floor == pytest.approx(48400.0)
    assert events[0].breached is False


def test_breach_kills_account_on_adverse_path():
    # adverse mtm dip of -110/contract at minute 2; n = 20 -> -2200 <= -2000
    days = ["2026-08-03", "2026-08-04"]
    path = make_trade_path([-50.0, -110.0, 0.0], date=days[0], final=0.0)
    path.sizing_anchor_usd = 5.0         # budget 100 -> raw 20, cap 40 -> n 20
    plat = _StubPlatform()
    events, summary = run_account(days, plat, {days[0]: path}, policy="P2")
    assert summary["breached"] is True
    assert len(events) == 1              # death stops the loop
    assert events[0].breached is True and events[0].phase == "dead"
    # Ruling R1 settlement: min(floor 48000, eq 47800) - n*$1 = 47780
    assert plat.balance == pytest.approx(47780.0)


def test_start_offset_is_start_phase_only():
    # frozen: MC1 SS5 inner randomness source (1) = start-phase offset
    days = [f"2026-08-{i:02d}" for i in range(3, 8)]
    plat = _StubPlatform()
    events, summary = run_account(days, plat, {}, policy="P2", start_offset=2)
    assert summary["days"] == 3
    assert [e.day for e in events] == days[2:]
    assert summary["no_path_days"] == 3


def test_run_real_study_blocked_without_flags(tmp_path):
    # frozen: platform_params s0_cost_handoff.hard_run_blocker + second copy.
    # Hermetic: inject absent flag paths (production flags now legitimately
    # exist since 2026-07-29, so the default path proceeds past the gate).
    with pytest.raises(RunBlockedError):
        run_real_study(g9_flag=tmp_path / "no_g9.flag",
                       second_copy_flag=tmp_path / "no_copy.flag")
