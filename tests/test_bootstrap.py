"""Tests for itsf.mc.bootstrap and itsf.mc.account.

Account/sizing tests live here (not in a separate file) because the
subagent ownership list is exactly test_bootstrap.py + test_verdict.py.
All paths are SYNTHETIC (tests/conftest.py generators) — no real data.
"""
from __future__ import annotations

import importlib.util
import shutil
import subprocess

import numpy as np
import pytest

from conftest import REPO, make_trade_path
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

_fcs_spec = importlib.util.spec_from_file_location(
    "final_candidate_scans", REPO / "scripts" / "final_candidate_scans.py")
fcs = importlib.util.module_from_spec(_fcs_spec)
_fcs_spec.loader.exec_module(fcs)

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


def test_build_worlds_rejects_non_frozen_master_seed():
    """# hardening: `build_worlds` is a PUBLIC research-RNG entry point that
    used to accept ANY `master_seed` with zero validation. IR DR-02: only
    contracts.RESEARCH_BOOTSTRAP_SEEDS (7/13/31) may seed a research-path
    RNG; every other value — including the forbidden marker 20260731 — is
    refused rather than silently honoured."""
    with pytest.raises(ValueError, match="DR-02"):
        build_worlds(DAY_IDS, B=4, master_seed=20260731)
    with pytest.raises(ValueError, match="DR-02"):
        build_worlds(DAY_IDS, B=4, master_seed=999)
    # the frozen seeds still work normally
    for seed in mc_bootstrap.MASTER_SEEDS:
        worlds = build_worlds(DAY_IDS, B=2, master_seed=seed)
        assert len(worlds) == 2


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
# scripts/final_candidate_scans.py: import-closure-derived E4 scope
# (M6.1.1 S2 item 7 — this belongs here because it is fundamentally about
# mc/bootstrap.py's own reachability from scripts/s0_real_run.py, the same
# reason mc/account.py's tests already live in this file per its own
# docstring rather than a separate file.)
# ---------------------------------------------------------------------------

def _make_scratch_repo(tmp_path):
    """Copy scripts/s0_real_run.py + the full src/itsf/** tree into a fresh
    scratch git repo, so `production_import_closure` and `git ls-files` both
    behave exactly as they do at the real repo root. Nothing outside
    `tmp_path` is touched: no commit, no staged change, no mutation of the
    real repo's git state."""
    scratch = tmp_path / "scratch_repo"
    (scratch / "scripts").mkdir(parents=True)
    shutil.copy2(REPO / "scripts" / "s0_real_run.py",
                scratch / "scripts" / "s0_real_run.py")
    shutil.copytree(REPO / "src" / "itsf", scratch / "src" / "itsf",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    subprocess.run(["git", "init", "-q"], cwd=scratch, check=True)
    return scratch


def _plant_marker(path):
    # Assembled from two halves, never spelled out contiguously in THIS
    # file's own source: the final_candidate_scans scan of forbidden-word
    # lines covers tests/ too (only the separate skip-marker check is
    # tests/-restricted), so writing the word out whole here would be a
    # correct finding against test_bootstrap.py itself, not only against the
    # scratch file this helper injects it into.
    marker = "TO" + "DO" + ": planted marker"
    path.write_text(
        path.read_text(encoding="utf-8") + f"\n# {marker}\n",
        encoding="utf-8")


def test_import_closure_includes_bootstrap_excludes_account_and_orchestrator(
        tmp_path):
    """itsf.s0.stats imports itsf.mc.bootstrap.stationary_bootstrap_indices
    (stats.py's own import line), so mc/bootstrap.py IS reachable from
    scripts/s0_real_run.py; mc/account.py and mc/orchestrator.py are not
    imported anywhere on that path (a repo-wide grep for "itsf.mc" during
    M6.1.1 found it only in stats.py, account.py, orchestrator.py, and the
    platforms/ modules — and only stats.py sits on the s0_real_run.py import
    path) and stay OUTSIDE the closure."""
    scratch = _make_scratch_repo(tmp_path)
    closure = fcs.production_import_closure(
        scratch / "scripts" / "s0_real_run.py", scratch / "src")
    closure_files = {p.relative_to(scratch).as_posix()
                     for p in closure.values()}
    assert "src/itsf/mc/bootstrap.py" in closure_files
    assert "src/itsf/mc/account.py" not in closure_files
    assert "src/itsf/mc/orchestrator.py" not in closure_files


def test_scanner_flags_reachable_marker_but_exempts_deferred_stub(
        tmp_path, capsys):
    """The E4 exemption is now import-closure-derived, not a blanket
    src/itsf/mc/ prefix exclusion: a forbidden marker planted in
    bootstrap.py (IN the closure) must be flagged; the SAME marker planted
    in account.py (a deliberately-deferred stub, NOT in the closure) must
    stay exempt — proving the scan scope tracks real reachability rather
    than a path prefix."""
    scratch = _make_scratch_repo(tmp_path)
    _plant_marker(scratch / "src" / "itsf" / "mc" / "bootstrap.py")
    _plant_marker(scratch / "src" / "itsf" / "mc" / "account.py")
    exit_code = fcs.main(scratch)
    out = capsys.readouterr().out
    assert exit_code == 1
    assert "src/itsf/mc/bootstrap.py" in out
    assert "src/itsf/mc/account.py" not in out


def test_import_closure_includes_parent_package_init_files(tmp_path):
    """M6.1.1 S2 item 4 (Codex finding (d)): importing itsf.mc.bootstrap
    EXECUTES itsf/__init__.py and itsf/mc/__init__.py as a side effect of
    CPython's import machinery — even though no import statement anywhere
    on the scripts/s0_real_run.py path ever spells out "itsf" or "itsf.mc"
    as a bare name (itsf.s0.stats says
    `from itsf.mc.bootstrap import stationary_bootstrap_indices`, which
    names only "itsf.mc.bootstrap"). Both ancestor package files must be IN
    the closure now, alongside bootstrap.py itself."""
    scratch = _make_scratch_repo(tmp_path)
    closure = fcs.production_import_closure(
        scratch / "scripts" / "s0_real_run.py", scratch / "src")
    closure_files = {p.relative_to(scratch).as_posix()
                     for p in closure.values()}
    assert "src/itsf/mc/bootstrap.py" in closure_files
    assert "src/itsf/__init__.py" in closure_files
    assert "src/itsf/mc/__init__.py" in closure_files


def test_scanner_flags_marker_in_parent_package_init_but_still_excludes_stubs(
        tmp_path, capsys):
    """ISOLATED mutation test (scratch git repo under tmp_path, never the
    real repo — same discipline as
    `test_scanner_flags_reachable_marker_but_exempts_deferred_stub` above):
    a forbidden marker planted in itsf/mc/__init__.py — a parent PACKAGE
    file, not a leaf module anything explicitly imports — must still turn
    the scanner RED (exit 1), proving finding (d)'s fix actually reaches
    parent-package files rather than only the leaf modules literal import
    statements name. mc/account.py and mc/orchestrator.py (still genuinely
    unreached from scripts/s0_real_run.py) stay exempt even though this test
    plants the SAME marker in them too."""
    scratch = _make_scratch_repo(tmp_path)
    _plant_marker(scratch / "src" / "itsf" / "mc" / "__init__.py")
    _plant_marker(scratch / "src" / "itsf" / "mc" / "account.py")
    _plant_marker(scratch / "src" / "itsf" / "mc" / "orchestrator.py")

    closure = fcs.production_import_closure(
        scratch / "scripts" / "s0_real_run.py", scratch / "src")
    closure_files = {p.relative_to(scratch).as_posix()
                     for p in closure.values()}
    assert "src/itsf/mc/__init__.py" in closure_files
    assert "src/itsf/mc/account.py" not in closure_files
    assert "src/itsf/mc/orchestrator.py" not in closure_files

    exit_code = fcs.main(scratch)
    out = capsys.readouterr().out
    assert exit_code == 1
    assert "src/itsf/mc/__init__.py" in out
    assert "src/itsf/mc/account.py" not in out
    assert "src/itsf/mc/orchestrator.py" not in out


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


# ===========================================================================
# DR-4 (Aaron 2026-08-10) — itsf.s0.stats as the production consumer of the
# ruled `contracts.BootstrapMethod`. The ruled instance is IMPORTED from
# contracts; no ruling literal is restated here. Every day sequence below is
# fabricated — no archive, no clock, no module-level RNG state.
# ===========================================================================
import dataclasses as _dc
import inspect as _inspect

from itsf.contracts import aaron_ruled_methods as _ruled_methods
from itsf.s0 import stats as s0_stats

RULED_BOOT = _ruled_methods().bootstrap_method

# 10 structurally-eligible trading days: 5 traded, 3 sat out, 2 NA.
# Traded P&L sums to 500.0, so the two candidate statistics are far apart:
#   per-TRADING-day mean (ruled) = 500 / 8 = 62.5
#   per-ORACLE-day mean (not ruled) = 500 / 5 = 100.0
DAY_STATES = [
    ("2026-01-02", "oracle_traded", 100.0),
    ("2026-01-05", "eligible_not_selected", None),
    ("2026-01-06", "oracle_traded", 200.0),
    ("2026-01-07", "na", None),
    ("2026-01-08", "eligible_not_selected", 0.0),
    ("2026-01-09", "oracle_traded", -50.0),
    ("2026-01-12", "na", None),
    ("2026-01-13", "oracle_traded", 150.0),
    ("2026-01-14", "eligible_not_selected", None),
    ("2026-01-15", "oracle_traded", 100.0),
]
THETA_PRIMARY = 0.5
THETA_SECONDARY = 0.3


def _sequence(states=None, method=None):
    return s0_stats.build_bootstrap_day_sequence(
        DAY_STATES if states is None else states,
        RULED_BOOT if method is None else method)


# --- the ruled POPULATION ---------------------------------------------------

def test_dr4_sequence_zero_fills_sat_out_days_and_drops_na_with_a_count():
    seq = _sequence()
    assert seq["dates"] == ("2026-01-02", "2026-01-05", "2026-01-06",
                            "2026-01-08", "2026-01-09", "2026-01-13",
                            "2026-01-14", "2026-01-15")
    assert seq["series"] == (100.0, 0.0, 200.0, 0.0, -50.0, 150.0, 0.0, 100.0)
    assert seq["n_days_in_sequence"] == 8
    assert seq["n_oracle_traded_days"] == 5
    assert seq["n_eligible_not_selected_days"] == 3
    # rule n1: NA days DROPPED, count disclosed and never silently discarded
    assert seq["n_na_days_dropped"] == 2
    assert seq["na_dates"] == ("2026-01-07", "2026-01-12")
    assert "2026-01-07" not in seq["dates"]
    assert seq["population"] == RULED_BOOT.population
    assert seq["na_day_rule"] == RULED_BOOT.na_day_rule
    assert seq["statistic"] == RULED_BOOT.statistic


def test_dr4_statistic_is_the_per_trading_day_mean_not_the_per_oracle_day_mean():
    """MUTATION GUARD: the two candidate statistics differ on this fixture."""
    seq = _sequence()
    per_trading_day = sum(seq["series"]) / len(seq["series"])
    traded = [v for v in seq["series"] if v != 0.0]
    per_oracle_day = sum(traded) / len(traded)
    assert per_trading_day == pytest.approx(62.5)
    assert per_oracle_day == pytest.approx(100.0)
    out = s0_stats.bootstrap_mean_ci_ruled(seq, theta=THETA_PRIMARY,
                                           method=RULED_BOOT, block_len=5.0,
                                           n_boot=30)
    assert out["quoted"]["mean"] == pytest.approx(per_trading_day)
    assert out["quoted"]["mean"] != pytest.approx(per_oracle_day)


def test_dr4_sequence_rejects_unruled_states_and_disordered_dates():
    with pytest.raises(ValueError, match="bootstrap_day_state_not_ruled:frozen_excluded"):
        _sequence([("2026-01-02", "frozen_excluded", None)])
    with pytest.raises(ValueError, match="not_in_ascending_date_order"):
        _sequence([("2026-01-06", "oracle_traded", 1.0),
                   ("2026-01-02", "oracle_traded", 1.0)])
    with pytest.raises(ValueError, match="duplicate_trade_date"):
        _sequence([("2026-01-02", "oracle_traded", 1.0),
                   ("2026-01-02", "oracle_traded", 1.0)])
    with pytest.raises(ValueError, match="oracle_traded_day_missing_pnl"):
        _sequence([("2026-01-02", "oracle_traded", None)])
    with pytest.raises(ValueError, match="eligible_not_selected_day_carries_pnl"):
        _sequence([("2026-01-02", "eligible_not_selected", 12.0)])


def test_dr4_unruled_population_na_or_statistic_strings_are_refused():
    for field, value, code in (
            ("population", "oracle_traded_days_only",
             "bootstrap_population_not_ruled:oracle_traded_days_only"),
            ("na_day_rule", "n2_zero_fill",
             "bootstrap_na_day_rule_not_ruled:n2_zero_fill"),
            ("statistic", "per_oracle_day_mean_usd",
             "bootstrap_statistic_not_ruled:per_oracle_day_mean_usd")):
        method = _dc.replace(RULED_BOOT, **{field: value})
        with pytest.raises(ValueError, match=code):
            _sequence(method=method)


def test_dr4_ruled_entry_refuses_a_bare_series():
    """A plain list is the PRE-ruling population and is invisible as such."""
    for bogus in ([100.0, 200.0, -50.0], {"series": [1.0, 2.0]}, None):
        with pytest.raises(
                ValueError,
                match="bootstrap_population_not_from_ruled_sequence_builder"):
            s0_stats.bootstrap_mean_ci_ruled(bogus, theta=THETA_PRIMARY,
                                             method=RULED_BOOT, block_len=5.0,
                                             n_boot=10)


def test_dr4_na_count_travels_all_the_way_into_the_result():
    out = s0_stats.bootstrap_mean_ci_ruled(_sequence(), theta=THETA_PRIMARY,
                                           method=RULED_BOOT, block_len=5.0,
                                           n_boot=20)
    assert out["n_na_days_dropped"] == 2
    assert out["na_dates"] == ["2026-01-07", "2026-01-12"]
    assert out["n_days_in_sequence"] == 8
    assert "n_na_days_dropped = 2" in out["method"]


# --- CRN scope: shared within theta across engine x scenario ----------------

def test_dr4_crn_streams_are_identical_across_engine_and_scenario():
    """The E1/Base call and the E2/Severe call ARE these two calls: engine and
    scenario are not parameters, so they cannot key the stream."""
    kw = dict(theta=THETA_PRIMARY, master_seed=7, block_len=5.0, n_boot=12,
              method=RULED_BOOT)
    e1_base = s0_stats.crn_resample_indices(8, **kw)
    e2_severe = s0_stats.crn_resample_indices(8, **kw)
    assert np.array_equal(e1_base, e2_severe)
    assert e1_base.shape == (12, 8)


def test_dr4_crn_signature_cannot_take_an_engine_or_a_scenario():
    for fn in (s0_stats.crn_stream_entropy, s0_stats.crn_resample_indices,
               s0_stats.resample_means_crn):
        params = {p.lower() for p in _inspect.signature(fn).parameters}
        assert not (params & {"engine", "eng", "scenario", "scn",
                              "cost_scenario"}), fn.__name__


def test_dr4_crn_streams_differ_across_theta_and_across_seed():
    base = s0_stats.crn_resample_indices(8, theta=THETA_PRIMARY, master_seed=7,
                                         block_len=5.0, n_boot=12,
                                         method=RULED_BOOT)
    other_theta = s0_stats.crn_resample_indices(
        8, theta=THETA_SECONDARY, master_seed=7, block_len=5.0, n_boot=12,
        method=RULED_BOOT)
    other_seed = s0_stats.crn_resample_indices(
        8, theta=THETA_PRIMARY, master_seed=13, block_len=5.0, n_boot=12,
        method=RULED_BOOT)
    other_block = s0_stats.crn_resample_indices(
        8, theta=THETA_PRIMARY, master_seed=7, block_len=21.0, n_boot=12,
        method=RULED_BOOT)
    assert not np.array_equal(base, other_theta)
    assert not np.array_equal(base, other_seed)
    assert not np.array_equal(base, other_block)


def test_dr4_crn_entropy_is_exactly_theta_seed_and_block():
    entropy = s0_stats.crn_stream_entropy(THETA_PRIMARY, 7, 5.0, RULED_BOOT)
    assert entropy == [7, s0_stats.STATS_STREAM_TAG,
                       s0_stats.theta_stream_key(THETA_PRIMARY),
                       s0_stats.block_stream_key(5.0)]
    assert s0_stats.theta_stream_key(THETA_PRIMARY) == 500
    assert s0_stats.theta_stream_key(THETA_SECONDARY) == 300


def test_dr4_mutation_keying_the_stream_on_the_engine_would_break_crn():
    """MUTATION GUARD, shown rather than asserted in prose: adding the engine
    to the entropy makes E1 and E2 draw DIFFERENT day-index sequences, which
    is exactly what `shared_within_theta_engine_scenario` forbids."""
    ruled = s0_stats.crn_stream_entropy(THETA_PRIMARY, 7, 5.0, RULED_BOOT)
    with_e1 = ruled + [1]
    with_e2 = ruled + [2]

    def draws(entropy):
        rng = np.random.default_rng(entropy)
        return np.stack([stationary_bootstrap_indices(8, 5.0, rng=rng)
                         for _ in range(12)])

    assert not np.array_equal(draws(with_e1), draws(with_e2))
    assert np.array_equal(draws(ruled), draws(ruled))


def test_dr4_resample_streams_are_prefix_nested_under_doubling():
    kw = dict(theta=THETA_PRIMARY, master_seed=7, block_len=5.0,
              method=RULED_BOOT)
    short = s0_stats.crn_resample_indices(8, n_boot=10, **kw)
    long = s0_stats.crn_resample_indices(8, n_boot=20, **kw)
    assert np.array_equal(long[:10], short)


def test_dr4_resample_means_use_the_same_stream_as_the_index_view():
    seq = _sequence()
    values = np.asarray(seq["series"], dtype=float)
    idx = s0_stats.crn_resample_indices(len(values), theta=THETA_PRIMARY,
                                        master_seed=7, block_len=5.0,
                                        n_boot=15, method=RULED_BOOT)
    means = s0_stats.resample_means_crn(values, theta=THETA_PRIMARY,
                                        master_seed=7, block_len=5.0,
                                        n_boot=15, method=RULED_BOOT)
    assert np.allclose(means, values[idx].mean(axis=1))


def test_dr4_unruled_crn_scope_is_refused():
    method = _dc.replace(RULED_BOOT, crn_scope="shared_within_engine")
    with pytest.raises(ValueError,
                       match="bootstrap_crn_scope_not_ruled:shared_within_engine"):
        s0_stats.crn_stream_entropy(THETA_PRIMARY, 7, 5.0, method)


# --- per-seed budget, quoted seed, percentile interpolation -----------------

def test_dr4_n_boot_is_per_seed_and_the_total_is_three_times_it():
    out = s0_stats.bootstrap_mean_ci_ruled(_sequence(), theta=THETA_PRIMARY,
                                           method=RULED_BOOT, block_len=5.0,
                                           n_boot=40)
    assert set(out["per_seed"]) == set(contracts.RESEARCH_BOOTSTRAP_SEEDS)
    for seed, row in out["per_seed"].items():
        assert row["n_boot"] == 40, seed
    assert out["n_boot_per_seed"] is True
    assert out["n_boot_total"] == 40 * len(contracts.RESEARCH_BOOTSTRAP_SEEDS)
    assert "resamples PER SEED" in out["method"]


def test_dr4_n_boot_per_seed_false_is_refused():
    method = _dc.replace(RULED_BOOT, n_boot_per_seed=False)
    with pytest.raises(ValueError,
                       match="bootstrap_n_boot_per_seed_not_ruled:False"):
        s0_stats.bootstrap_mean_ci_ruled(_sequence(), theta=THETA_PRIMARY,
                                         method=method, block_len=5.0,
                                         n_boot=10)


def test_dr4_quoted_seed_is_parsed_from_the_rule_not_restated():
    assert s0_stats.ruled_quoted_seed(RULED_BOOT) == 7
    out = s0_stats.bootstrap_mean_ci_ruled(_sequence(), theta=THETA_PRIMARY,
                                           method=RULED_BOOT, block_len=5.0,
                                           n_boot=20)
    assert out["quoted_seed"] == 7
    assert out["quoted"] is out["per_seed"][7]
    # the rule really drives the selection: point it at another frozen seed
    alt = _dc.replace(RULED_BOOT, quoted_seed_rule="fixed_seed_31")
    assert s0_stats.ruled_quoted_seed(alt) == 31
    out_alt = s0_stats.bootstrap_mean_ci_ruled(_sequence(),
                                               theta=THETA_PRIMARY,
                                               method=alt, block_len=5.0,
                                               n_boot=20)
    assert out_alt["quoted_seed"] == 31
    assert out_alt["quoted"] is out_alt["per_seed"][31]
    assert out_alt["per_seed"][7] == out["per_seed"][7]      # CRN unchanged


def test_dr4_unruled_quoted_seed_rules_are_refused():
    for rule, code in (("best_of_three", "bootstrap_quoted_seed_rule_not_ruled"),
                       ("fixed_seed_", "bootstrap_quoted_seed_rule_not_ruled"),
                       ("fixed_seed_99",
                        "bootstrap_quoted_seed_not_a_research_seed:99")):
        with pytest.raises(ValueError, match=code):
            s0_stats.ruled_quoted_seed(
                _dc.replace(RULED_BOOT, quoted_seed_rule=rule))


def test_dr4_unruled_percentile_interpolation_is_refused():
    method = _dc.replace(RULED_BOOT, percentile_interpolation="nearest")
    with pytest.raises(
            ValueError,
            match="bootstrap_percentile_interpolation_not_ruled:nearest"):
        s0_stats.bootstrap_mean_ci_ruled(_sequence(), theta=THETA_PRIMARY,
                                         method=method, block_len=5.0,
                                         n_boot=10)


def test_dr4_only_the_frozen_research_seeds_may_run():
    with pytest.raises(ValueError, match="RESEARCH_BOOTSTRAP_SEEDS"):
        s0_stats.bootstrap_mean_ci_ruled(_sequence(), theta=THETA_PRIMARY,
                                         method=RULED_BOOT, block_len=5.0,
                                         n_boot=10, master_seeds=(7,))
    with pytest.raises(ValueError, match="not_a_research_seed"):
        s0_stats.crn_stream_entropy(THETA_PRIMARY, 5, 5.0, RULED_BOOT)


def test_dr4_theta_must_be_seedable():
    for bad in (float("nan"), -0.5):
        with pytest.raises(ValueError):
            s0_stats.theta_stream_key(bad)


def test_dr4_result_carries_the_full_disclosure():
    out = s0_stats.bootstrap_mean_ci_ruled(_sequence(), theta=THETA_PRIMARY,
                                           method=RULED_BOOT, block_len=5.0,
                                           n_boot=20)
    assert out["population"] == RULED_BOOT.population
    assert out["statistic"] == RULED_BOOT.statistic
    assert out["crn_scope"] == RULED_BOOT.crn_scope
    assert out["theta"] == THETA_PRIMARY
    assert out["theta_stream_key"] == 500
    assert out["crn_stream_entropy_by_seed"][7] == (
        s0_stats.crn_stream_entropy(THETA_PRIMARY, 7, 5.0, RULED_BOOT))
    for token in (RULED_BOOT.population, RULED_BOOT.statistic,
                  RULED_BOOT.crn_scope, RULED_BOOT.na_day_rule,
                  RULED_BOOT.quoted_seed_rule):
        assert token in out["method"], token
    assert out["convergence"]["max_abs_ci_lo_diff"] >= 0.0
