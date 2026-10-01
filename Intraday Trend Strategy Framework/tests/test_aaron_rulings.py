"""Pin tests for the 2026-08-10 Aaron S0-closeout rulings (MAIN-AGENT OWNED).

Every ruled value is pinned EXACTLY. A drive-by edit of any ruling literal in
contracts.py turns at least one of these red — that is their entire job.
These tests never read real data and never touch the registry/exposure files.
"""
from types import MappingProxyType

import pytest

from itsf.contracts import (
    AARON_RULED_ADVERSE_TICKS_PRIMARY,
    AARON_RULED_ADVERSE_TICKS_SENSITIVITY,
    RULED_ARCHIVE_ROOT,
    RULED_RUNS_ROOT,
    RunConfig,
    aaron_ruled_methods,
)


@pytest.fixture(scope="module")
def ruled():
    return aaron_ruled_methods()


def test_fully_resolved_and_structurally_clean(ruled):
    assert ruled.pending_fields() == ()
    assert ruled.fully_resolved is True
    assert ruled.structural_problems() == []
    assert ruled.test_only is False


def test_dr1_spread_cost_pins(ruled):
    sc = ruled.spread_cost
    assert sc.scalar_rule == "B_i_trading_window_q50med_q50p90_q50p95"
    assert sc.adverse_semantics == "replaces_per_side"
    assert dict(sc.adverse_slippage_ticks) == {
        "Base": 1.0, "Conservative": 2.0, "Stress": 2.0, "Severe": 3.0}
    # canonicalized to a read-only mapping at construction
    assert type(sc.adverse_slippage_ticks) is MappingProxyType
    with pytest.raises(TypeError):
        sc.adverse_slippage_ticks["Base"] = 9.0


def test_ir7_option_ii_is_sensitivity_only():
    assert dict(AARON_RULED_ADVERSE_TICKS_SENSITIVITY) == {
        "Base": 2.0, "Conservative": 3.0, "Stress": 3.0, "Severe": 4.0}
    assert dict(AARON_RULED_ADVERSE_TICKS_PRIMARY) != dict(
        AARON_RULED_ADVERSE_TICKS_SENSITIVITY)


def test_dr2_volatility_regime_pins(ruled):
    v = ruled.volatility_regime
    assert v.close_source == "exact_scheduled_last_1m_close"
    assert v.return_basis == "simple"
    assert v.ddof == 1
    assert v.roll_crossing_rule == "r1_drop_and_extend"
    assert v.tercile_reference == "full_development_expost"
    assert v.na_rule == "vol_na_fourth_stratum"
    assert v.mapping_scope == "shared_s2_and_appendixA"


def test_dr3_fp_allocation_pins(ruled):
    f = ruled.fp_allocation
    assert f.basis == "B"
    assert f.weight_source == "selected_tp_composition"
    assert f.shortfall_rule == "frozen_literal_redistribute_remaining_fp"


def test_dr4_bootstrap_pins(ruled):
    b = ruled.bootstrap_method
    assert b.population == "full_eligible_trading_day_sequence"
    assert b.na_day_rule == "n1_drop_from_sequence_disclose_count"
    assert b.statistic == "per_trading_day_mean_usd"
    assert b.n_boot_per_seed is True
    assert b.n_boot_applies_per_seed is True
    assert b.quoted_seed_rule == "fixed_seed_7"
    assert b.percentile_interpolation == "linear"
    assert b.crn_scope == "shared_within_theta_engine_scenario"


def test_dr5_grid_policy_pins(ruled):
    g = ruled.grid_policy
    assert g.k_per_seed == 200
    assert g.k_start_index == 0
    assert g.stream_includes_theta is True
    assert g.convergence_rule == "mc_spec_s5_four_rules_at_mc_wiring"
    assert g.max_doublings == 2


def test_dr6_dr7_dr8_string_pins(ruled):
    assert ruled.event_na_mapping == "F1_five_stratum_ir12_18_vocab"
    assert ruled.stability_population == "both_conditional_and_full_eligible"
    assert ruled.worst_day_estimator == "linear"


def test_l5_roots_are_outside_the_repo_tree():
    assert RULED_RUNS_ROOT == r"C:\Users\Aaron\quant-data\itsf-runs"
    assert RULED_ARCHIVE_ROOT == r"C:\Users\Aaron\quant-data\itsf-runs-archive"
    for root in (RULED_RUNS_ROOT, RULED_ARCHIVE_ROOT):
        assert "OneDrive" not in root
        assert "Intraday Trend Strategy Framework" not in root


def test_runconfig_carries_ruled_roots_by_default():
    cfg = RunConfig(trial_id="S0-T001", authorized_commit="0" * 40,
                    engineering_seed=1, attempts_dir="a", runs_dir="r",
                    assertions_path="p")
    assert cfg.runs_root == RULED_RUNS_ROOT
    assert cfg.archive_root == RULED_ARCHIVE_ROOT


def test_ruled_instance_is_reconstructed_not_cached():
    # The gateway derives freshness guarantees from calling the source anew;
    # the factory must build a NEW instance each call (no module singleton
    # that a test could mutate via object.__setattr__ and poison later calls).
    a, b = aaron_ruled_methods(), aaron_ruled_methods()
    assert a is not b
    assert a == b
