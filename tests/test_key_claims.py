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

DAYS = [f"2020-01-{d:02d}" for d in range(1, L3 + 1)]
REMOVED = ["2019-12-30", "2019-12-31"]

FUNNEL = {
    "L0_scheduled_trading_days": 25,
    "L1_observed_rth_days": 24,
    "L2_regular_full_session_candidates": 22,
    "L3_structurally_eligible_days": L3,
    "L4_final_feature_construction_dates": L4,
    "side_diagnostic_complete_390_bar_rth_days": 21,
    "removed_sets": {"zero_bar_days": list(REMOVED)},
}

_FEATURE_MAP = (("F1", "ret_open30"), ("F2", "or_width"),
                ("F3", "de_open30"), ("F4", "rvol_open30"), ("F5", "gap"),
                ("F6", "open_loc_on"), ("F7", "on_range"),
                ("F8", "retrace_open30"), ("F9", "close_pos_open30"),
                ("F10", "is_event_day"))
_LABEL_MAP = (("Y_cont", "y_cont"), ("Y1", "y1"), ("Y2", "y2_de_pm"),
              ("Y3", "y3_close_pos_pm"), ("Y4", "y4_mfe"), ("Y5", "y5_mae"))


def assertions_bytes(funnel=None):
    locked = {
        "funnel": dict(funnel or FUNNEL),
        "features": {fk: {"constructible": L3 - 1, "na": 1,
                          "reasons": {"anchor_missing": 1}}
                     for fk, _ in _FEATURE_MAP},
        "labels": {yk: {"available_days": L3 - 2, "unavailable_days": 2}
                   for yk, _ in _LABEL_MAP},
    }
    return json.dumps(locked).encode("utf-8")


def sealed_names():
    names = {f"MC_HANDOFF_{e}_{s}.jsonl": {"sha256": "x", "bytes": 1}
             for e in ENGINES for s in _SCENARIOS}
    names["S0_REPORT.md"] = {"sha256": "x", "bytes": 1}
    names["HANDOFF_ADMISSION.json"] = {"sha256": "x", "bytes": 1}
    return names


def formal_payload():
    per_seed = {str(s): {"n_boot": FROZEN_N_BOOT}
                for s in RESEARCH_BOOTSTRAP_SEEDS}
    funnel_pub = {k: v for k, v in FUNNEL.items() if k != "removed_sets"}
    return {
        "structural": {
            "funnel_counts": funnel_pub,
            "eras": {"era_a": DAYS[:10], "era_b": DAYS[10:]},
            "na_table": {
                "population": L3,
                "per_field": {
                    "features": {pub: {"na": 1, "not_na": L3 - 1,
                                       "reasons": {"anchor_missing": 1}}
                                 for _, pub in _FEATURE_MAP},
                    "labels": {pub: {"na": 2, "not_na": L3 - 2,
                                     "reasons": {"warmup": 2}}
                               for _, pub in _LABEL_MAP},
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
    f["structural"]["na_table"]["per_field"]["features"]["gap"][
        "reasons"] = {"roll": 99}
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


# --- Codex fix-round strengthening (KC1 date sets, KC2 locked counts) ------

def test_kc1_era_union_must_equal_locked_l4():
    f = formal_payload()
    f["structural"]["eras"]["era_b"] = f["structural"]["eras"]["era_b"][:-1]
    rep = run(f)
    assert rep.verdicts["KC1_day_universe"] == "FAIL"
    assert any("era_union_size" in p for p in rep.problems)


def test_kc1_removed_day_republished_fails():
    f = formal_payload()
    f["structural"]["eras"]["era_a"] = (
        f["structural"]["eras"]["era_a"][:-1] + [REMOVED[0]])
    rep = run(f)
    assert rep.verdicts["KC1_day_universe"] == "FAIL"
    assert any("removed_day_republished" in p for p in rep.problems)


def test_kc1_same_counts_swapped_dates_caught():
    """The exact Codex counter-example: identical counts, one date swapped
    for a removed one — KC1 must now refuse."""
    f = formal_payload()
    era = f["structural"]["eras"]["era_a"]
    era[0] = REMOVED[1]
    rep = run(f)
    assert rep.verdicts["KC1_day_universe"] == "FAIL"


def test_kc2_feature_na_bound_to_locked_value():
    f = formal_payload()
    row = f["structural"]["na_table"]["per_field"]["features"]["gap"]
    row["na"], row["not_na"] = 2, L3 - 2         # conserves, but != locked
    rep = run(f)
    assert rep.verdicts["KC2_label_na_counts"] == "FAIL"
    assert any("feature_na_not_locked:F5" in p for p in rep.problems)


def test_kc2_label_counts_bound_to_locked_value():
    f = formal_payload()
    row = f["structural"]["na_table"]["per_field"]["labels"]["y4_mfe"]
    row["na"], row["not_na"] = 3, L3 - 3         # conserves, but != locked
    rep = run(f)
    assert rep.verdicts["KC2_label_na_counts"] == "FAIL"
    assert any("label_counts_not_locked:Y4" in p for p in rep.problems)


def test_kc2_missing_mapped_field_is_uncovered_fail():
    f = formal_payload()
    del f["structural"]["na_table"]["per_field"]["features"]["on_range"]
    rep = run(f)
    assert rep.verdicts["KC2_label_na_counts"] == "FAIL"
    assert any("feature_uncovered:F7" in p for p in rep.problems)
