"""Tests for itsf.mc.verdict — frozen table S0 SS10.4, scope MC1 SS0/SS2.5,
gate2_cost_guard downgrade (platform_params). Inputs are hand-built synthetic
statistics; no research numbers are produced."""
from __future__ import annotations

import pytest

from itsf.mc.verdict import VerdictInput, apply_verdict


def vi(engine="E1", platform="topstep", p5=-100.0, med_c=-50.0, med_s=-50.0,
       p95=-10.0, feasible=True) -> VerdictInput:
    return VerdictInput(p5_cons=p5, median_cons=med_c, median_stress=med_s,
                        p95_cons=p95, feasible=feasible,
                        platform=platform, engine=engine)


def test_clean_go():
    primary = {
        "ts_e1": vi("E1", "topstep", p5=10.0, med_c=40.0, med_s=5.0, p95=90.0),
        "ts_e2": vi("E2", "topstep"),
        "lu_e1": vi("E1", "lucid"),
        "lu_e2": vi("E2", "lucid"),
    }
    res = apply_verdict(primary)
    assert res.verdict == "GO"
    assert "ts_e1" in res.reason


def test_all_negative_stop():
    # STOP: ALL Primary combos (E1+E2) Conservative P95 <= 0 (row 1)
    primary = {
        "ts_e1": vi("E1", "topstep", p95=-5.0),
        "ts_e2": vi("E2", "topstep", p95=0.0),   # boundary: <= 0 counts
        "lu_e1": vi("E1", "lucid", p95=-1.0),
        "lu_e2": vi("E2", "lucid", p95=-20.0),
    }
    res = apply_verdict(primary)
    assert res.verdict == "STOP"


def test_formerly_undefined_cell_is_alpha():
    # p95 > 0 (not STOP), median <= 0, p5 <= 0 (not GO), E2 negative
    # (no beta arm) -> alpha fallback (row 4)
    primary = {
        "ts_e1": vi("E1", "topstep", p5=-40.0, med_c=-5.0, med_s=-5.0, p95=60.0),
        "ts_e2": vi("E2", "topstep", p5=-80.0, med_c=-30.0, med_s=-30.0, p95=-1.0),
        "lu_e1": vi("E1", "lucid", p5=-60.0, med_c=-10.0, med_s=-10.0, p95=30.0),
        "lu_e2": vi("E2", "lucid", p5=-90.0, med_c=-40.0, med_s=-40.0, p95=-2.0),
    }
    res = apply_verdict(primary)
    assert res.verdict == "alpha"


def test_e2_only_positive_is_beta():
    primary = {
        "ts_e1": vi("E1", "topstep", p5=-10.0, p95=20.0),
        "ts_e2": vi("E2", "topstep", p5=5.0, med_c=15.0, med_s=2.0, p95=40.0),
        "lu_e1": vi("E1", "lucid"),
        "lu_e2": vi("E2", "lucid"),
    }
    res = apply_verdict(primary)
    assert res.verdict == "beta"
    assert "ts_e2" in res.reason


def test_e1_ev_met_but_infeasible_is_beta():
    primary = {
        "ts_e1": vi("E1", "topstep", p5=10.0, med_c=30.0, med_s=5.0, p95=80.0,
                    feasible=False),
        "ts_e2": vi("E2", "topstep"),
        "lu_e1": vi("E1", "lucid"),
        "lu_e2": vi("E2", "lucid"),
    }
    res = apply_verdict(primary)
    assert res.verdict == "beta"
    assert "ts_e1" in res.reason


def test_go_only_via_lucid_downgrades_to_alpha_with_gate2_reason():
    # frozen: platform_params gate2_cost_guard — Lucid cannot independently
    # trigger GO; downgrade to boundary-zone alpha
    primary = {
        "ts_e1": vi("E1", "topstep", p5=-20.0, p95=10.0),
        "ts_e2": vi("E2", "topstep"),
        "lu_e1": vi("E1", "lucid", p5=15.0, med_c=40.0, med_s=8.0, p95=90.0),
        "lu_e2": vi("E2", "lucid"),
    }
    res = apply_verdict(primary)
    assert res.verdict == "alpha"
    assert "gate2" in res.reason.lower()
    assert "lu_e1" in res.reason


def test_go_via_both_platforms_is_not_downgraded():
    primary = {
        "ts_e1": vi("E1", "topstep", p5=5.0, med_s=1.0, p95=50.0),
        "lu_e1": vi("E1", "lucid", p5=15.0, med_s=8.0, p95=90.0),
        "ts_e2": vi("E2", "topstep"),
        "lu_e2": vi("E2", "lucid"),
    }
    res = apply_verdict(primary)
    assert res.verdict == "GO"


def test_stress_median_boundary_zero_counts_for_go():
    # Stress median >= 0 (frozen inequality) — exactly 0 passes
    primary = {
        "ts_e1": vi("E1", "topstep", p5=1.0, med_s=0.0, p95=50.0),
        "ts_e2": vi("E2", "topstep"),
    }
    assert apply_verdict(primary).verdict == "GO"


def test_e2_positive_does_not_block_e1_go():
    # order: GO is checked before beta; an E2-positive combo alongside a
    # qualifying E1 combo must still yield GO
    primary = {
        "ts_e1": vi("E1", "topstep", p5=5.0, med_s=1.0, p95=50.0),
        "ts_e2": vi("E2", "topstep", p5=9.0, med_s=3.0, p95=70.0),
    }
    assert apply_verdict(primary).verdict == "GO"


def test_empty_primary_rejected():
    with pytest.raises(ValueError):
        apply_verdict({})
