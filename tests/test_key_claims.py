"""Hermetic tests for the F-2 key-claims release gate (MAIN-AGENT OWNED).

All fixtures are synthetic; no real data, no repo artifacts, no registry.
"""
import json

import pytest

from itsf.contracts import RESEARCH_BOOTSTRAP_SEEDS, aaron_ruled_methods
from itsf.s0 import output_proof as op
from itsf.s0.report import _SCENARIOS, FROZEN_N_BOOT
from itsf.s0.study import ENGINES

L3 = 20
L4 = 18

FUNNEL = {
    "L0_scheduled_trading_days": 25,
    "L1_observed_rth_days": 24,
    "L2_regular_full_session_candidates": 22,
    "L3_structurally_eligible_days": L3,
    "L4_final_feature_construction_dates": L4,
    "side_diagnostic_complete_390_bar_rth_days": 21,
}


def assertions_bytes(funnel=None):
    return json.dumps({"funnel": dict(funnel or FUNNEL)}).encode("utf-8")


def sealed_names():
    names = {f"MC_HANDOFF_{e}_{s}.jsonl": {"sha256": "x", "bytes": 1}
             for e in ENGINES for s in _SCENARIOS}
    names["S0_REPORT.md"] = {"sha256": "x", "bytes": 1}
    names["HANDOFF_ADMISSION.json"] = {"sha256": "x", "bytes": 1}
    return names


def formal_payload():
    per_seed = {str(s): {"n_boot": FROZEN_N_BOOT}
                for s in RESEARCH_BOOTSTRAP_SEEDS}
    return {
        "structural": {
            "funnel_counts": dict(FUNNEL),
            "na_table": {
                "population": L3,
                "per_field": {
                    "features": {"f5": {"na": 4, "not_na": 16,
                                        "reasons": {"roll": 4}}},
                    "labels": {"y1": {"na": 2, "not_na": 18,
                                      "reasons": {"warmup": 2}}},
                },
            },
            "f10_counts": {"CPI": 3, "NFP": 3, "FOMC": 2, "none": 11,
                           "NA_multi_event": 1},
        },
        "bootstrap_ci": {"theta_0_5": {"E1|Base": {"per_seed": per_seed}}},
        "e2_worst_days": {
            "theta_0_5": {"Base": {
                "estimator_status": "resolved",
                "percentile_estimator":
                    "numpy.percentile(method='linear') — Aaron-ruled "
                    "DR-M6-H",
            }}},
        "mc_handoff_manifest": {"sealed_files": sealed_names()},
    }


def ctx(**over):
    base = dict(assertions_bytes=assertions_bytes(),
                ruled_methods=aaron_ruled_methods(),
                evidence_problems=["PARTIAL:replay:pending_dr"],
                disk_report=None)
    base.update(over)
    return op.ResearchClaimsContext(**base)


def run(formal=None, phase="pre_write", **ctx_over):
    return op.verify_key_claims(formal if formal is not None
                                else formal_payload(),
                                ctx(**ctx_over), phase=phase)


# --- happy paths -----------------------------------------------------------

def test_pre_write_all_pass_kc6_pending():
    rep = run()
    assert rep.verdicts["KC6_report_vs_disk"] == "PENDING"
    assert rep.sealable_pre_write is True
    assert rep.releasable_post_write is False


def test_post_write_release():
    rep = run(phase="post_write", disk_report={"ok": True, "detail": "d"})
    assert all(rep.verdicts[c] == "PASS" for c in op.KEY_CLAIM_IDS)
    assert rep.releasable_post_write is True


def test_report_refuses_bool():
    with pytest.raises(TypeError):
        bool(run())


def test_invalid_phase_fails_everything():
    rep = op.verify_key_claims(formal_payload(), ctx(), phase="nope")
    assert set(rep.verdicts.values()) == {"FAIL"}


# --- KC1 -------------------------------------------------------------------

def test_kc1_funnel_mismatch_fails():
    f = formal_payload()
    f["structural"]["funnel_counts"]["L3_structurally_eligible_days"] = L3 + 1
    rep = run(f)
    assert rep.verdicts["KC1_day_universe"] == "FAIL"
    assert rep.sealable_pre_write is False


def test_kc1_missing_level_uncovered():
    f = formal_payload()
    del f["structural"]["funnel_counts"]["L0_scheduled_trading_days"]
    assert run(f).verdicts["KC1_day_universe"] == "FAIL"


def test_kc1_unusable_assertions_fail_closed():
    rep = run(assertions_bytes=b"{not json")
    assert rep.verdicts["KC1_day_universe"] == "FAIL"
    assert rep.verdicts["KC2_label_na_counts"] == "FAIL"


# --- KC2 -------------------------------------------------------------------

def test_kc2_population_must_equal_locked_l3():
    f = formal_payload()
    f["structural"]["na_table"]["population"] = L3 + 5
    assert run(f).verdicts["KC2_label_na_counts"] == "FAIL"


def test_kc2_row_conservation_against_l3():
    f = formal_payload()
    f["structural"]["na_table"]["per_field"]["labels"]["y1"]["na"] = 3
    assert run(f).verdicts["KC2_label_na_counts"] == "FAIL"


def test_kc2_reasons_must_sum_to_na():
    f = formal_payload()
    f["structural"]["na_table"]["per_field"]["features"]["f5"][
        "reasons"] = {"roll": 1}
    assert run(f).verdicts["KC2_label_na_counts"] == "FAIL"


def test_kc2_f10_partition_bound_to_l3():
    f = formal_payload()
    f["structural"]["f10_counts"]["none"] = 99
    rep = run(f)
    assert rep.verdicts["KC2_label_na_counts"] == "FAIL"
    assert any("f10_partition_sum" in p for p in rep.problems)


# --- KC3 -------------------------------------------------------------------

def test_kc3_not_run_is_fail():
    assert run(evidence_problems=None).verdicts[
        "KC3_primary_oracle_vs_bytes"] == "FAIL"


def test_kc3_hard_problem_is_fail_partial_is_pass():
    assert run(evidence_problems=["oracle_daily_mean_mismatch"]).verdicts[
        "KC3_primary_oracle_vs_bytes"] == "FAIL"
    assert run(evidence_problems=["PARTIAL:x:y"]).verdicts[
        "KC3_primary_oracle_vs_bytes"] == "PASS"


# --- KC4 -------------------------------------------------------------------

def test_kc4_missing_handoff_name_fails():
    f = formal_payload()
    del f["mc_handoff_manifest"]["sealed_files"]["MC_HANDOFF_E1_Base.jsonl"]
    assert run(f).verdicts[
        "KC4_engine_scenario_axis_and_sealed_names"] == "FAIL"


def test_kc4_name_outside_frozen_matrix_fails():
    f = formal_payload()
    f["mc_handoff_manifest"]["sealed_files"]["EXTRA.bin"] = {}
    assert run(f).verdicts[
        "KC4_engine_scenario_axis_and_sealed_names"] == "FAIL"


def test_kc4_optional_admitted_names_allowed():
    f = formal_payload()
    f["mc_handoff_manifest"]["sealed_files"]["SEED_MANIFEST.json"] = {}
    assert run(f).verdicts[
        "KC4_engine_scenario_axis_and_sealed_names"] == "PASS"


def test_kc4_self_excluded_report_json_refused():
    f = formal_payload()
    f["mc_handoff_manifest"]["sealed_files"]["S0_REPORT.json"] = {}
    assert run(f).verdicts[
        "KC4_engine_scenario_axis_and_sealed_names"] == "FAIL"


# --- KC5 -------------------------------------------------------------------

def test_kc5_wrong_seed_set_fails():
    f = formal_payload()
    f["bootstrap_ci"]["theta_0_5"]["E1|Base"]["per_seed"] = {
        "7": {"n_boot": FROZEN_N_BOOT}, "13": {"n_boot": FROZEN_N_BOOT},
        "99": {"n_boot": FROZEN_N_BOOT}}
    assert run(f).verdicts["KC5_bootstrap_seeds_estimator"] == "FAIL"


def test_kc5_wrong_n_boot_fails():
    f = formal_payload()
    f["bootstrap_ci"]["theta_0_5"]["E1|Base"]["per_seed"]["7"][
        "n_boot"] = 9999
    assert run(f).verdicts["KC5_bootstrap_seeds_estimator"] == "FAIL"


def test_kc5_unresolved_estimator_status_fails():
    f = formal_payload()
    f["e2_worst_days"]["theta_0_5"]["Base"][
        "estimator_status"] = "unresolved_DR-M6-H"
    assert run(f).verdicts["KC5_bootstrap_seeds_estimator"] == "FAIL"


def test_kc5_disclosure_must_carry_ruled_estimator():
    f = formal_payload()
    f["e2_worst_days"]["theta_0_5"]["Base"][
        "percentile_estimator"] = "numpy.percentile(method='lower')"
    assert run(f).verdicts["KC5_bootstrap_seeds_estimator"] == "FAIL"


def test_kc5_no_coverage_fails():
    f = formal_payload()
    f["bootstrap_ci"] = {}
    assert run(f).verdicts["KC5_bootstrap_seeds_estimator"] == "FAIL"
    f = formal_payload()
    f["e2_worst_days"] = {}
    assert run(f).verdicts["KC5_bootstrap_seeds_estimator"] == "FAIL"


# --- KC6 -------------------------------------------------------------------

def test_kc6_disk_before_write_is_a_defect():
    rep = run(disk_report={"ok": True})
    assert rep.verdicts["KC6_report_vs_disk"] == "FAIL"


def test_kc6_post_write_not_ok_fails():
    rep = run(phase="post_write", disk_report={"ok": False, "detail": "x"})
    assert rep.verdicts["KC6_report_vs_disk"] == "FAIL"
    rep = run(phase="post_write", disk_report=None)
    assert rep.verdicts["KC6_report_vs_disk"] == "FAIL"


# --- never raises ----------------------------------------------------------

@pytest.mark.parametrize("garbage", [
    None, 42, "x", [], {"structural": None},
    {"structural": {"funnel_counts": "nope"}}])
def test_never_raises_on_garbage_payload(garbage):
    rep = op.verify_key_claims(garbage, ctx(), phase="pre_write")
    assert rep.sealable_pre_write is False


def test_never_raises_on_hostile_context():
    class Hostile:
        def __getattr__(self, name):
            raise RuntimeError("boom")
    rep = op.verify_key_claims(formal_payload(), Hostile(),
                               phase="pre_write")
    assert rep.sealable_pre_write is False
