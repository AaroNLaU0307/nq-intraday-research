"""Synthetic checks for itsf.s0.handoff (E6 S0 -> MC handoff schema skeleton).

SA-18-style scope. Every population here is a hand-written dict of fabricated
dates/values: no real archive is touched, no clock is read. The replay
determinism test draws randomness only through `itsf.s0.gridmix`, whose
streams derive exclusively from contracts.RESEARCH_BOOTSTRAP_SEEDS.
"""
from __future__ import annotations

import json

import numpy as np
import pytest

from itsf import contracts
from itsf.s0 import gridmix, handoff, stability, stats

ERA_ACTUAL = "actual_micro_available_era"
ERA_PROXY = "counterfactual_micro_execution"
EPOCH = "2018-2021"


def _day_row(**overrides) -> dict[str, object]:
    row = {
        "micro_execution_era": ERA_ACTUAL,
        "stability_epoch": EPOCH,
        "year": "2019",
        "d_open": 1,
        "event_flag_final": "none",
        "vol_status": "resolved",
        "tp_fp_class": {"theta_0.5": "TP"},
    }
    row.update(overrides)
    return row


# ---------------------------------------------------------------------------
# schema version / sentinel
# ---------------------------------------------------------------------------

def test_schema_version_constant():
    assert handoff.SCHEMA_VERSION == "m6.1-draft-1"


def test_unresolved_sentinel_identity_and_string_equality():
    assert handoff.UNRESOLVED == "UNRESOLVED"
    assert handoff.UNRESOLVED is handoff.UNRESOLVED
    # a second construction is the SAME singleton object
    from itsf.s0.handoff import _UnresolvedSentinel
    assert _UnresolvedSentinel() is handoff.UNRESOLVED


# ---------------------------------------------------------------------------
# build_day_strata
# ---------------------------------------------------------------------------

def test_build_day_strata_canonical_sorted_ordering():
    day_rows = {
        "2019-06-03": _day_row(),
        "2019-01-02": _day_row(),
        "2019-03-15": _day_row(),
    }
    out = handoff.build_day_strata(day_rows, thetas=[0.5])
    assert out["schema_version"] == handoff.SCHEMA_VERSION
    assert out["ordering"] == "sorted-by-date"
    assert list(out["days"]) == sorted(day_rows)


def test_micro_era_and_stability_epoch_conflation_rejected():
    day_rows = {"2019-06-03": _day_row(stability_epoch=ERA_ACTUAL)}
    with pytest.raises(ValueError):
        handoff.build_day_strata(day_rows, thetas=[0.5])
    day_rows2 = {"2019-06-03": _day_row(micro_execution_era=EPOCH)}
    with pytest.raises(ValueError):
        handoff.build_day_strata(day_rows2, thetas=[0.5])


def test_micro_era_and_stability_epoch_distinct_values_pass():
    day_rows = {"2019-06-03": _day_row()}
    out = handoff.build_day_strata(day_rows, thetas=[0.5])
    row = out["days"]["2019-06-03"]
    assert row["micro_execution_era"] == ERA_ACTUAL
    assert row["stability_epoch"] == EPOCH
    assert row["micro_execution_era"] != row["stability_epoch"]


def test_tp_fp_class_must_match_requested_thetas_exactly():
    # theta_0.5=FP / theta_0.3=TP is THETA-NESTING-MONOTONE (Y_cont between
    # 0.3 and 0.5: continues past the lower bar, not past the higher one),
    # unlike the reverse pairing, which is now rejected elsewhere (see
    # test_theta_nesting_monotonicity_violation_rejected below).
    day_rows = {"2019-06-03": _day_row(
        tp_fp_class={"theta_0.5": "FP", "theta_0.3": "TP"})}
    with pytest.raises(ValueError):
        handoff.build_day_strata(day_rows, thetas=[0.5])   # extra key 0.3
    out = handoff.build_day_strata(day_rows, thetas=[0.5, 0.3])
    assert out["days"]["2019-06-03"]["tp_fp_class"] == {
        "theta_0.5": "FP", "theta_0.3": "TP"}


def test_tp_fp_class_bad_value_rejected():
    day_rows = {"2019-06-03": _day_row(
        tp_fp_class={"theta_0.5": "maybe"})}
    with pytest.raises(ValueError):
        handoff.build_day_strata(day_rows, thetas=[0.5])


def test_event_na_flag_and_event_flag_final_preserved():
    day_rows = {
        "2019-06-03": _day_row(event_flag_final=None),
        "2019-06-04": _day_row(event_flag_final="CPI"),
    }
    out = handoff.build_day_strata(day_rows, thetas=[0.5])
    na_row = out["days"]["2019-06-03"]
    assert na_row["event_flag_final"] is None
    assert na_row["event_na"] is True
    concrete_row = out["days"]["2019-06-04"]
    assert concrete_row["event_flag_final"] == "CPI"
    assert concrete_row["event_na"] is False


def test_event_stratum_is_always_the_unresolved_marker():
    day_rows = {
        "2019-06-03": _day_row(event_flag_final=None),
        "2019-06-04": _day_row(event_flag_final="FOMC"),
    }
    out = handoff.build_day_strata(day_rows, thetas=[0.5])
    for row in out["days"].values():
        assert row["event_stratum"] == "UNRESOLVED_DR-M6-F"


def test_caller_supplied_event_stratum_is_rejected():
    day_rows = {"2019-06-03": _day_row()}
    day_rows["2019-06-03"]["event_stratum"] = "some_concrete_bucket"
    with pytest.raises(ValueError):
        handoff.build_day_strata(day_rows, thetas=[0.5])


def test_missing_required_key_in_day_row_raises():
    row = _day_row()
    del row["vol_status"]
    with pytest.raises(ValueError):
        handoff.build_day_strata({"2019-06-03": row}, thetas=[0.5])


def test_invalid_d_open_in_day_row_raises():
    day_rows = {"2019-06-03": _day_row(d_open=2)}
    with pytest.raises(ValueError):
        handoff.build_day_strata(day_rows, thetas=[0.5])


def test_duplicate_or_empty_thetas_rejected():
    day_rows = {"2019-06-03": _day_row()}
    with pytest.raises(ValueError):
        handoff.build_day_strata(day_rows, thetas=[])
    with pytest.raises(ValueError):
        handoff.build_day_strata(day_rows, thetas=[0.5, 0.5])


# ---------------------------------------------------------------------------
# build_day_strata hardening (M6.1.1 S2 item 1)
# ---------------------------------------------------------------------------

def test_event_flag_final_frozen_f10_vocabulary_enforced():
    """# frozen F10 vocabulary, IR-12/18: only "CPI"/"NFP"/"FOMC"/"none" or
    None. "none_or_na" (and any other spelling) is rejected, not silently
    treated as NA."""
    for bad in ("none_or_na", "cpi", "NA", "unknown"):
        day_rows = {"2019-06-03": _day_row(event_flag_final=bad)}
        with pytest.raises(ValueError):
            handoff.build_day_strata(day_rows, thetas=[0.5])
    # every concrete category and the "none"/None pair still pass
    for good in ("CPI", "NFP", "FOMC", "none", None):
        day_rows = {"2019-06-03": _day_row(event_flag_final=good)}
        out = handoff.build_day_strata(day_rows, thetas=[0.5])
        assert out["days"]["2019-06-03"]["event_flag_final"] == good


def test_year_must_match_the_date_itself():
    day_rows = {"2019-06-03": _day_row(year="2020")}
    with pytest.raises(ValueError):
        handoff.build_day_strata(day_rows, thetas=[0.5])


def test_stability_epoch_must_match_the_year_computed_epoch():
    # 2019 falls in 2018-2021, not 2014-2017 — inconsistent pairing rejected.
    day_rows = {"2019-06-03": _day_row(stability_epoch="2014-2017")}
    with pytest.raises(ValueError):
        handoff.build_day_strata(day_rows, thetas=[0.5])
    # "outside_epochs" is a valid label, but ONLY for a year outside every
    # frozen bucket (e.g. 2009); 2019 paired with it is still inconsistent.
    day_rows2 = {"2019-06-03": _day_row(stability_epoch="outside_epochs")}
    with pytest.raises(ValueError):
        handoff.build_day_strata(day_rows2, thetas=[0.5])
    # a year genuinely outside every bucket correctly pairs with
    # "outside_epochs"
    day_rows3 = {"2009-06-03": _day_row(year="2009",
                                        stability_epoch="outside_epochs")}
    out = handoff.build_day_strata(day_rows3, thetas=[0.5])
    assert out["days"]["2009-06-03"]["stability_epoch"] == "outside_epochs"


def test_d_open_zero_requires_non_tradeable_for_every_theta():
    day_rows = {"2019-06-03": _day_row(
        d_open=0, tp_fp_class={"theta_0.5": "TP", "theta_0.3": "TP"})}
    with pytest.raises(ValueError):
        handoff.build_day_strata(day_rows, thetas=[0.5, 0.3])
    # the correct all-non_tradeable pairing passes
    ok_rows = {"2019-06-03": _day_row(
        d_open=0,
        tp_fp_class={"theta_0.5": "non_tradeable",
                    "theta_0.3": "non_tradeable"})}
    out = handoff.build_day_strata(ok_rows, thetas=[0.5, 0.3])
    assert out["days"]["2019-06-03"]["tp_fp_class"] == {
        "theta_0.5": "non_tradeable", "theta_0.3": "non_tradeable"}
    # ONE non-non_tradeable theta among several is still a violation
    partial_rows = {"2019-06-03": _day_row(
        d_open=0,
        tp_fp_class={"theta_0.5": "non_tradeable", "theta_0.3": "FP"})}
    with pytest.raises(ValueError):
        handoff.build_day_strata(partial_rows, thetas=[0.5, 0.3])


def test_theta_nesting_monotonicity_violation_rejected():
    """A day TP at theta=0.5 (the HIGHER bar) must also be TP at theta=0.3
    (the LOWER bar): Y_cont >= 0.5 implies Y_cont >= 0.3. FP at 0.3 while TP
    at 0.5 is impossible under that semantics and must raise."""
    day_rows = {"2019-06-03": _day_row(
        tp_fp_class={"theta_0.5": "TP", "theta_0.3": "FP"})}
    with pytest.raises(ValueError):
        handoff.build_day_strata(day_rows, thetas=[0.5, 0.3])
    # the reverse (FP at the higher theta, TP at the lower) is fine
    ok_rows = {"2019-06-03": _day_row(
        tp_fp_class={"theta_0.5": "FP", "theta_0.3": "TP"})}
    handoff.build_day_strata(ok_rows, thetas=[0.5, 0.3])   # does not raise
    # both TP, or both FP, at every theta are trivially monotone
    both_tp = {"2019-06-03": _day_row(
        tp_fp_class={"theta_0.5": "TP", "theta_0.3": "TP"})}
    handoff.build_day_strata(both_tp, thetas=[0.5, 0.3])
    both_fp = {"2019-06-03": _day_row(
        tp_fp_class={"theta_0.5": "FP", "theta_0.3": "FP"})}
    handoff.build_day_strata(both_fp, thetas=[0.5, 0.3])


def test_build_day_strata_formal_sealable_is_false_while_dr_m6_f_is_open():
    day_rows = {"2019-06-03": _day_row()}
    out = handoff.build_day_strata(day_rows, thetas=[0.5])
    assert out["formal_sealable"] is False


def test_build_seed_manifest_guards_are_real_raises_not_bare_asserts(
        monkeypatch):
    """A production governance gate must be a real `raise`, not a bare
    `assert` (stripped under `python -O`). Break the IR DR-02 identity guard
    via monkeypatch — a same-VALUE, different-OBJECT tuple — and confirm it
    still fires for BOTH single-sourced constants."""
    # tuple(some_tuple) is a CPython no-op that returns the SAME object, so
    # a genuinely different object needs to round-trip through a list first.
    same_values_new_object = tuple(
        [int(s) for s in contracts.RESEARCH_BOOTSTRAP_SEEDS])
    assert same_values_new_object is not contracts.RESEARCH_BOOTSTRAP_SEEDS
    assert same_values_new_object == contracts.RESEARCH_BOOTSTRAP_SEEDS
    monkeypatch.setattr(stats, "RESEARCH_BOOTSTRAP_SEEDS",
                        same_values_new_object)
    with pytest.raises(AssertionError):
        handoff.build_seed_manifest()
    monkeypatch.setattr(stats, "RESEARCH_BOOTSTRAP_SEEDS",
                        contracts.RESEARCH_BOOTSTRAP_SEEDS)
    monkeypatch.setattr(gridmix, "RESEARCH_BOOTSTRAP_SEEDS",
                        same_values_new_object)
    with pytest.raises(AssertionError):
        handoff.build_seed_manifest()


# ---------------------------------------------------------------------------
# build_seed_manifest
# ---------------------------------------------------------------------------

def test_build_seed_manifest_shape_and_identity():
    manifest = handoff.build_seed_manifest()
    assert manifest["schema_version"] == handoff.SCHEMA_VERSION
    assert manifest["research_bootstrap_seeds"] == [7, 13, 31]
    assert manifest["stream_tags"] == {
        "stats_stream_tag": 9001, "grid_stream_tag": 9002}
    assert manifest["k_policy"] == "UNRESOLVED_DR-M6-E"
    assert manifest["crn_scope"] == "UNRESOLVED"
    assert manifest["formal_sealable"] is False
    assert "run-infra provenance only" in manifest["engineering_seed_note"]
    assert "FIRST frozen master seed" in manifest["quoted_seed_convention"]


# ---------------------------------------------------------------------------
# build_grid_samples + replay determinism
# ---------------------------------------------------------------------------

def _fabricated_grid_populations():
    low, high = ("2010", "low", "none"), ("2010", "high", "CPI")
    d_tp: dict[str, float] = {}
    d_fp: dict[str, float] = {}
    strata: dict[str, tuple[str, str, str]] = {}
    for i in range(10):
        date = f"2010-03-{i + 1:02d}"
        d_tp[date] = 100.0 + i
        strata[date] = low if i < 6 else high
    for i in range(20):
        date = f"2010-04-{i + 1:02d}"
        d_fp[date] = -50.0 - i
        strata[date] = low if i < 12 else high
    return d_tp, d_fp, strata


def _run_meta(**overrides) -> dict[str, object]:
    meta = {"theta": 0.5, "engine": "E1", "scenario": "Base"}
    meta.update(overrides)
    return meta


def test_build_grid_samples_shape_and_infeasible_passthrough():
    d_tp, d_fp, strata = _fabricated_grid_populations()
    grid_output = gridmix.build_grid(d_tp, d_fp, strata, base_rate_p=0.4,
                                     q_grid=[0.50], r_grid=[0.50])
    samples = handoff.build_grid_samples(grid_output, run_meta=_run_meta())
    assert samples["schema_version"] == handoff.SCHEMA_VERSION
    assert samples["formal_sealable"] is False
    assert samples["run_meta"] == {"theta": 0.5, "engine": "E1",
                                   "scenario": "Base"}
    cell = samples["cells"]["q0.50_r0.50"]
    assert cell["infeasible_by_sample"] is False
    assert cell["q_mil"] == 500 and cell["r_mil"] == 500
    for seed in (7, 13, 31):
        block = cell["per_seed"][seed]
        assert set(block) == {"tp_dates", "fp_dates", "markers",
                              "realized_precision", "realized_recall",
                              "target_precision", "target_recall"}
    assert samples["replay"]["grid_stream_tag"] == gridmix.GRID_STREAM_TAG
    assert samples["replay"]["k_policy"] == "UNRESOLVED_DR-M6-E"
    assert samples["replay"]["crn_scope"] == "UNRESOLVED"


def test_build_grid_samples_reports_infeasible_cells():
    d_tp, _d_fp, strata = _fabricated_grid_populations()
    small_fp = {"2010-04-01": -10.0, "2010-04-02": -20.0}
    grid_output = gridmix.build_grid(d_tp, small_fp, strata, base_rate_p=0.4,
                                     q_grid=[0.35], r_grid=[0.80])
    samples = handoff.build_grid_samples(grid_output, run_meta=_run_meta())
    cell = samples["cells"]["q0.35_r0.80"]
    assert cell["infeasible_by_sample"] is True
    assert cell["per_seed"] == {}


# ---------------------------------------------------------------------------
# build_grid_samples replay_status honesty (M6.1.1 S2 item 5)
# ---------------------------------------------------------------------------

def test_build_grid_samples_replay_status_is_partial_today():
    """The multi-stratum replay is NOT implemented (day_strata carries no
    real stratum key while DR-M6-B/DR-M6-F pend): `replay_status` must be
    PARTIAL, machine-visible, and never "CLOSED" — and that PARTIAL status
    must, on its own, keep the artifact out of `formal_seal_admission`'s
    admitted set even in a hypothetical future where k_policy/crn_scope
    resolve but the replay itself stays single-stratum."""
    d_tp, d_fp, strata = _fabricated_grid_populations()
    grid_output = gridmix.build_grid(d_tp, d_fp, strata, base_rate_p=0.4,
                                     q_grid=[0.50], r_grid=[0.50])
    samples = handoff.build_grid_samples(grid_output, run_meta=_run_meta())
    assert samples["replay_status"] == "PARTIAL_single_stratum_only"
    assert samples["replay_status"] == handoff.REPLAY_STATUS_PARTIAL_SINGLE_STRATUM
    assert samples["replay_status"] != handoff.REPLAY_STATUS_CLOSED
    assert samples["formal_sealable"] is False
    problems = handoff.formal_seal_admission({"grid_samples": samples})
    assert len(problems) == 1
    assert "grid_samples" in problems[0]


# ---------------------------------------------------------------------------
# build_grid_samples run_meta validation (M6.1.1 S2 item 3)
# ---------------------------------------------------------------------------

def test_run_meta_missing_required_key_rejected():
    d_tp, d_fp, strata = _fabricated_grid_populations()
    grid_output = gridmix.build_grid(d_tp, d_fp, strata, base_rate_p=0.4,
                                     q_grid=[0.50], r_grid=[0.50])
    for key in ("theta", "engine", "scenario"):
        incomplete = _run_meta()
        del incomplete[key]
        with pytest.raises(ValueError):
            handoff.build_grid_samples(grid_output, run_meta=incomplete)
    with pytest.raises(ValueError):
        handoff.build_grid_samples(grid_output, run_meta={})


def test_run_meta_unknown_key_rejected():
    d_tp, d_fp, strata = _fabricated_grid_populations()
    grid_output = gridmix.build_grid(d_tp, d_fp, strata, base_rate_p=0.4,
                                     q_grid=[0.50], r_grid=[0.50])
    with pytest.raises(ValueError):
        handoff.build_grid_samples(
            grid_output, run_meta=_run_meta(cost_scenario="extra_key"))


def test_run_meta_wrong_type_rejected():
    d_tp, d_fp, strata = _fabricated_grid_populations()
    grid_output = gridmix.build_grid(d_tp, d_fp, strata, base_rate_p=0.4,
                                     q_grid=[0.50], r_grid=[0.50])
    with pytest.raises(ValueError):
        handoff.build_grid_samples(grid_output,
                                   run_meta=_run_meta(theta="0.5"))
    with pytest.raises(ValueError):
        handoff.build_grid_samples(grid_output, run_meta=_run_meta(engine=1))
    with pytest.raises(ValueError):
        handoff.build_grid_samples(grid_output,
                                   run_meta=_run_meta(theta=True))  # bool trap


def test_run_meta_theta_normalised_to_float():
    d_tp, d_fp, strata = _fabricated_grid_populations()
    grid_output = gridmix.build_grid(d_tp, d_fp, strata, base_rate_p=0.4,
                                     q_grid=[0.50], r_grid=[0.50])
    samples = handoff.build_grid_samples(
        grid_output, run_meta=_run_meta(theta=1))     # int in, float out
    assert samples["run_meta"]["theta"] == 1.0
    assert isinstance(samples["run_meta"]["theta"], float)


def test_grid_replay_reproduces_the_selection():
    """Independent recomputation using ONLY public gridmix functions
    (floor_n_tp, allocate) plus the DISCLOSED replay recipe: the same
    stratified-pools-then-rng.choice algorithm the gridmix module docstring
    describes, rebuilt here from scratch rather than by reaching into
    gridmix's private `_select`/`_pools` helpers."""
    d_tp, d_fp, strata = _fabricated_grid_populations()
    grid_output = gridmix.build_grid(d_tp, d_fp, strata, base_rate_p=0.4,
                                     q_grid=[0.50], r_grid=[0.50])
    samples = handoff.build_grid_samples(grid_output, run_meta=_run_meta())
    cell = samples["cells"]["q0.50_r0.50"]
    seed = 7
    expected_tp = cell["per_seed"][seed]["tp_dates"]

    tag = samples["replay"]["grid_stream_tag"]
    q_mil, r_mil = cell["q_mil"], cell["r_mil"]
    assert tag == gridmix.GRID_STREAM_TAG

    tp_pools_raw: dict[str, list[str]] = {}
    for date in d_tp:
        tp_pools_raw.setdefault("|".join(strata[date]), []).append(date)
    tp_pools = {k: tuple(sorted(v)) for k, v in sorted(tp_pools_raw.items())}
    tp_avail = {k: len(v) for k, v in tp_pools.items()}
    n_tp = gridmix.floor_n_tp(r_mil, len(d_tp))
    tp_alloc = gridmix.allocate(n_tp, tp_avail)

    rng = np.random.default_rng([seed, tag, q_mil, r_mil])
    picked: list[str] = []
    for key in sorted(tp_alloc):
        k = tp_alloc[key]
        if k <= 0:
            continue
        pool = tp_pools[key]
        idx = rng.choice(len(pool), size=k, replace=False)
        picked.extend(pool[int(i)] for i in idx)
    assert sorted(picked) == expected_tp


# ---------------------------------------------------------------------------
# REPLAY-COMPLETENESS from the three handoff artifacts ALONE
# (M6.1.1 S2 item 3 — DAY_STRATA + GRID_SAMPLES + SEED_MANIFEST, no access to
# the raw d_tp/d_fp/strata test fixtures and no gridmix internals beyond the
# public `floor_n_tp`/`allocate` and the disclosed stream formula)
# ---------------------------------------------------------------------------

def test_replay_completeness_from_artifacts_alone():
    """Reconstruct a cell's exact TP and FP selections using ONLY the three
    handoff artifacts (day_strata, grid_samples, seed_manifest) — never the
    original d_tp/d_fp/strata fixtures, and never gridmix's private
    `_select`/`_pools` helpers.

    Deliberate single-stratum construction: gridmix's actual stratum key is
    `(year, volatility_regime, event_flag)`, and day_strata does NOT carry
    that same key today (`event_stratum` is UNRESOLVED_DR-M6-F and there is
    no `volatility_regime` field at all — DR-M6-B is also open). A test that
    pretended to reconstruct a MULTI-stratum pool split from day_strata alone
    would be fabricating a resolution to those open decisions. Restricting
    this fixture to exactly ONE stratum sidesteps that gap honestly: the
    "available" pool for a population is then simply every date day_strata
    classifies TP (or FP) for the relevant theta, which day_strata DOES
    already carry today, closed-book.
    """
    d_tp, d_fp, strata = _fabricated_grid_populations()
    single_stratum = {d: ("2010", "flat", "none") for d in strata}

    grid_output = gridmix.build_grid(d_tp, d_fp, single_stratum,
                                     base_rate_p=0.4, q_grid=[0.50],
                                     r_grid=[0.50])
    grid_samples = handoff.build_grid_samples(grid_output,
                                              run_meta=_run_meta(theta=0.5))
    seed_manifest = handoff.build_seed_manifest()

    day_rows = {}
    for d in d_tp:
        day_rows[d] = _day_row(year="2010", stability_epoch="2010-2013",
                               tp_fp_class={"theta_0.5": "TP"})
    for d in d_fp:
        day_rows[d] = _day_row(year="2010", stability_epoch="2010-2013",
                               tp_fp_class={"theta_0.5": "FP"})
    day_strata = handoff.build_day_strata(day_rows, thetas=[0.5])

    # Conservation holds for this fixture (sanity, not the point of THIS
    # test — test_conservation_* covers it directly). The record matrix must
    # now be the full frozen 8-cell {ENGINES} x {SCENARIOS} shape (M6.1.1 S2
    # item 1) — every classified date recorded in every cell — rather than
    # `{}`, which the OLD (pre-item-1) conservation check let pass silently.
    classified = sorted(
        d for d, row in day_strata["days"].items()
        if any(v in ("TP", "FP") for v in row["tp_fp_class"].values()))
    records = _full_record_matrix(classified)
    assert handoff.verify_handoff_conservation(
        day_strata, grid_samples, records) == []

    cell = grid_samples["cells"]["q0.50_r0.50"]
    q_mil, r_mil = cell["q_mil"], cell["r_mil"]
    tag = grid_samples["replay"]["grid_stream_tag"]
    assert tag == seed_manifest["stream_tags"]["grid_stream_tag"]

    theta_key = "theta_0.5"
    tp_pool = tuple(sorted(
        d for d, row in day_strata["days"].items()
        if row["tp_fp_class"][theta_key] == "TP"))
    fp_pool = tuple(sorted(
        d for d, row in day_strata["days"].items()
        if row["tp_fp_class"][theta_key] == "FP"))
    STRATUM = "S"

    n_tp = gridmix.floor_n_tp(r_mil, len(tp_pool))          # PUBLIC
    n_fp = gridmix.n_fp_for(n_tp, q_mil)                    # PUBLIC
    tp_alloc = gridmix.allocate(n_tp, {STRATUM: len(tp_pool)})   # PUBLIC
    fp_alloc = gridmix.allocate(n_fp, {STRATUM: len(fp_pool)})   # PUBLIC

    for seed in seed_manifest["research_bootstrap_seeds"]:
        # disclosed PUBLIC stream formula, from the artifacts alone
        rng = np.random.default_rng([seed, tag, q_mil, r_mil])
        idx_tp = rng.choice(len(tp_pool), size=tp_alloc[STRATUM],
                            replace=False)
        replayed_tp = sorted(tp_pool[int(i)] for i in idx_tp)
        idx_fp = rng.choice(len(fp_pool), size=fp_alloc[STRATUM],
                            replace=False)
        replayed_fp = sorted(fp_pool[int(i)] for i in idx_fp)

        recorded = cell["per_seed"][seed]
        assert replayed_tp == recorded["tp_dates"]
        assert replayed_fp == recorded["fp_dates"]


# ---------------------------------------------------------------------------
# build_handoff_manifest
# ---------------------------------------------------------------------------

def test_build_handoff_manifest_sha256_bytes_line_count(tmp_path):
    jsonl_path = tmp_path / "records.jsonl"
    content = b'{"a": 1}\n{"b": 2}\n{"c": 3}\n'
    jsonl_path.write_bytes(content)
    plain_path = tmp_path / "notes.txt"
    plain_path.write_bytes(b"hello world")

    manifest = handoff.build_handoff_manifest({
        "records": str(jsonl_path), "notes": str(plain_path)})
    assert manifest["schema_version"] == handoff.SCHEMA_VERSION

    import hashlib
    expected_jsonl_sha = hashlib.sha256(content).hexdigest()
    entry = manifest["files"]["records"]
    assert entry["sha256"] == expected_jsonl_sha
    assert entry["bytes"] == len(content)
    assert entry["line_count"] == 3

    plain_entry = manifest["files"]["notes"]
    assert plain_entry["sha256"] == hashlib.sha256(b"hello world").hexdigest()
    assert plain_entry["bytes"] == 11
    assert "line_count" not in plain_entry


def test_jsonl_line_count_empty_body_is_zero(tmp_path):
    """# hardening: an empty .jsonl body has ZERO lines — not 1 from a naive
    '"\\n" count + 1' fix that forgets the empty-file edge."""
    p = tmp_path / "empty.jsonl"
    p.write_bytes(b"")
    manifest = handoff.build_handoff_manifest({"e": str(p)})
    entry = manifest["files"]["e"]
    assert entry["bytes"] == 0
    assert entry["line_count"] == 0


def test_jsonl_line_count_no_trailing_newline_counts_the_last_line(tmp_path):
    """# hardening: N records joined by "\\n" with NO trailing newline has
    only N-1 "\\n" bytes; the OLD counting logic (`chunk.count(b"\\n")`)
    undercounted by exactly 1 in this case. Pinned: N lines, no trailing
    newline -> N."""
    p = tmp_path / "notrail.jsonl"
    content = b'{"a": 1}\n{"b": 2}\n{"c": 3}'          # 3 records, no trailing \n
    p.write_bytes(content)
    manifest = handoff.build_handoff_manifest({"e": str(p)})
    entry = manifest["files"]["e"]
    assert entry["bytes"] == len(content)
    assert entry["line_count"] == 3


def test_jsonl_line_count_single_line_no_trailing_newline(tmp_path):
    """The single-record degenerate case of the same bug: 0 "\\n" bytes but
    1 real (unterminated) line — the old logic reported 0."""
    p = tmp_path / "one.jsonl"
    p.write_bytes(b'{"only": true}')
    manifest = handoff.build_handoff_manifest({"e": str(p)})
    assert manifest["files"]["e"]["line_count"] == 1


# ---------------------------------------------------------------------------
# verify_handoff_conservation
# ---------------------------------------------------------------------------

def _day_strata_with(dates_classes: dict[str, str]) -> dict[str, object]:
    """dates_classes: date -> "TP"|"FP"|"non_tradeable" for theta_0.5."""
    day_rows = {d: _day_row(tp_fp_class={"theta_0.5": cls})
               for d, cls in dates_classes.items()}
    return handoff.build_day_strata(day_rows, thetas=[0.5])


def _full_record_matrix(dates) -> dict[str, dict[str, list[str]]]:
    """The frozen 8-cell {ENGINES} x {SCENARIOS} record matrix, every cell
    carrying the SAME `dates` list — used wherever a test's point is NOT the
    per-cell record-matrix-shape check itself (M6.1.1 S2 item 1), so an
    otherwise-conserving fixture does not incidentally trip the now-mandatory
    8-cell shape requirement."""
    return {engine: {scenario: list(dates) for scenario in handoff.SCENARIOS}
           for engine in handoff.ENGINES}


def test_conservation_positive_case_no_problems():
    day_strata = _day_strata_with({
        "2019-06-01": "TP", "2019-06-02": "FP", "2019-06-03": "non_tradeable"})
    grid_samples = {
        "run_meta": {"theta": 0.5, "engine": "E1", "scenario": "Base"},
        "cells": {"q0.50_r0.50": {"per_seed": {
            7: {"tp_dates": ["2019-06-01"], "fp_dates": ["2019-06-02"]}}}}}
    records = _full_record_matrix(["2019-06-01", "2019-06-02"])
    problems = handoff.verify_handoff_conservation(day_strata, grid_samples,
                                                    records)
    assert problems == []


def test_conservation_grid_date_missing_from_day_strata():
    day_strata = _day_strata_with({"2019-06-01": "TP"})
    grid_samples = {
        "run_meta": {"theta": 0.5, "engine": "E1", "scenario": "Base"},
        "cells": {"q0.50_r0.50": {"per_seed": {
            7: {"tp_dates": ["2019-06-01", "2099-01-01"], "fp_dates": []}}}}}
    records = {"E1": {"Base": ["2019-06-01"]}}
    problems = handoff.verify_handoff_conservation(day_strata, grid_samples,
                                                    records)
    assert any("2099-01-01" in p and "grid sample" in p for p in problems)


def test_conservation_swapped_tp_fp_marker_is_flagged():
    """# per-theta hardening: a grid sample marker that disagrees with
    day_strata's SAME-theta TP/FP call must be caught. Before this check
    existed, only "TP/FP-classed for ANY theta" was verified, which a
    swapped TP<->FP marker pair could pass right through."""
    day_strata = _day_strata_with({
        "2019-06-01": "TP", "2019-06-02": "FP"})
    # marker pair SWAPPED relative to day_strata's theta_0.5 call
    grid_samples = {
        "run_meta": {"theta": 0.5, "engine": "E1", "scenario": "Base"},
        "cells": {"q0.50_r0.50": {"per_seed": {
            7: {"tp_dates": ["2019-06-02"], "fp_dates": ["2019-06-01"]}}}}}
    records = {"E1": {"Base": ["2019-06-01", "2019-06-02"]}}
    problems = handoff.verify_handoff_conservation(day_strata, grid_samples,
                                                    records)
    assert any("2019-06-01" in p and "TP" in p for p in problems)
    assert any("2019-06-02" in p and "FP" in p for p in problems)


def test_conservation_requires_run_meta_theta_when_grid_has_dates():
    """A grid_samples bundle with dates but no run_meta/theta cannot be
    per-theta checked and must fail closed, not silently skip the check."""
    day_strata = _day_strata_with({"2019-06-01": "TP"})
    grid_samples = {"cells": {"q0.50_r0.50": {"per_seed": {
        7: {"tp_dates": ["2019-06-01"], "fp_dates": []}}}}}
    with pytest.raises(ValueError):
        handoff.verify_handoff_conservation(day_strata, grid_samples, {})


def test_conservation_record_date_missing_from_day_strata():
    day_strata = _day_strata_with({"2019-06-01": "TP"})
    grid_samples = {"cells": {}}
    records = {"E1": {"Base": ["2019-06-01", "2099-02-02"]}}
    problems = handoff.verify_handoff_conservation(day_strata, grid_samples,
                                                    records)
    assert any("2099-02-02" in p and "absent from day_strata" in p
              for p in problems)


def test_conservation_classified_date_missing_a_record():
    day_strata = _day_strata_with({"2019-06-01": "TP", "2019-06-02": "FP"})
    grid_samples = {"cells": {}}
    # 2019-06-02 has no record for E1/Base at all
    records = {"E1": {"Base": ["2019-06-01"]}}
    problems = handoff.verify_handoff_conservation(day_strata, grid_samples,
                                                    records)
    assert any("2019-06-02" in p and "missing a record" in p for p in problems)


def test_conservation_record_without_classification():
    day_strata = _day_strata_with({
        "2019-06-01": "TP", "2019-06-02": "non_tradeable"})
    grid_samples = {"cells": {}}
    # 2019-06-02 has a record even though it is non_tradeable (not TP/FP)
    records = {"E1": {"Base": ["2019-06-01", "2019-06-02"]}}
    problems = handoff.verify_handoff_conservation(day_strata, grid_samples,
                                                    records)
    assert any("2019-06-02" in p and "not TP/FP-classed" in p
              for p in problems)


# ---------------------------------------------------------------------------
# verify_handoff_conservation — record matrix SHAPE enforcement
# (M6.1.1 S2 item 1, Codex finding (a): "an empty or partial record matrix
# passes" today; the fix requires the matrix's keys to be EXACTLY the frozen
# {ENGINES} x {SCENARIOS} 8 cells, with an empty matrix, a missing cell and
# an extra/renamed cell reported as DISTINCT problems)
# ---------------------------------------------------------------------------

def test_engines_and_scenarios_are_the_frozen_eight_cells():
    assert handoff.ENGINES == ("E1", "E2")
    assert handoff.SCENARIOS == ("Base", "Conservative", "Stress", "Severe")
    assert handoff.FROZEN_THETAS == (0.5, 0.3)
    assert handoff.FROZEN_SEEDS == (7, 13, 31)
    assert handoff.FROZEN_SEEDS is contracts.RESEARCH_BOOTSTRAP_SEEDS
    # single-sourced from study.py, never a local re-typed copy
    from itsf.s0 import study as s0_study
    assert handoff.ENGINES is s0_study.ENGINES
    assert handoff.FROZEN_THETAS is s0_study.FROZEN_THETAS


def test_conservation_empty_record_matrix_is_rejected():
    day_strata = _day_strata_with({"2019-06-01": "TP"})
    grid_samples = {"cells": {}}
    problems = handoff.verify_handoff_conservation(day_strata, grid_samples, {})
    assert any("EMPTY" in p for p in problems)


def test_conservation_seven_cell_partial_matrix_is_rejected():
    """Dropping exactly ONE of the frozen 8 cells must be flagged — a
    partial matrix is not "close enough"."""
    day_strata = _day_strata_with({"2019-06-01": "TP"})
    grid_samples = {"cells": {}}
    records = _full_record_matrix(["2019-06-01"])
    del records["E2"]["Severe"]                  # 8 -> 7 cells
    problems = handoff.verify_handoff_conservation(day_strata, grid_samples,
                                                    records)
    assert any("E2/Severe" in p and "missing" in p for p in problems)


def test_conservation_renamed_engine_is_rejected():
    """A renamed engine key produces BOTH a "missing" problem for the real
    frozen engine it silently replaced and an "unrecognised" problem for the
    bogus key — a renamed cell is never mistaken for the real one."""
    day_strata = _day_strata_with({"2019-06-01": "TP"})
    grid_samples = {"cells": {}}
    records = _full_record_matrix(["2019-06-01"])
    records["E9"] = records.pop("E1")
    problems = handoff.verify_handoff_conservation(day_strata, grid_samples,
                                                    records)
    assert any("E9" in p and "unrecognised" in p for p in problems)
    assert any("E1/Base" in p and "missing" in p for p in problems)


def test_conservation_correct_eight_cell_matrix_control_passes():
    day_strata = _day_strata_with({"2019-06-01": "TP"})
    grid_samples = {"cells": {}}
    records = _full_record_matrix(["2019-06-01"])
    problems = handoff.verify_handoff_conservation(day_strata, grid_samples,
                                                    records)
    assert problems == []


# ---------------------------------------------------------------------------
# verify_handoff_conservation — AXIS LOCKS + SEED_MANIFEST cross-verification
# (M6.1.1 S2 item 2, Codex finding (b))
# ---------------------------------------------------------------------------

def test_conservation_theta_key_outside_frozen_pair_is_flagged():
    """day_strata built from an out-of-pair theta (build_day_strata itself
    does not restrict `thetas` to the frozen pair — that is exactly the axis
    gap this closes at the conservation-check layer)."""
    day_rows = {"2019-06-03": _day_row(tp_fp_class={"theta_0.9": "TP"})}
    day_strata = handoff.build_day_strata(day_rows, thetas=[0.9])
    grid_samples = {"cells": {}}
    problems = handoff.verify_handoff_conservation(day_strata, grid_samples, {})
    assert any("theta_0.9" in p and "frozen theta pair" in p for p in problems)


def test_conservation_run_meta_theta_outside_frozen_pair_is_flagged():
    day_strata = _day_strata_with({"2019-06-01": "TP"})
    grid_samples = {"run_meta": {"theta": 0.9, "engine": "E1",
                                 "scenario": "Base"}, "cells": {}}
    problems = handoff.verify_handoff_conservation(day_strata, grid_samples, {})
    assert any("theta_0.9" in p and "frozen theta pair" in p for p in problems)


def _seeded_grid_samples(seeds) -> dict[str, object]:
    return {
        "run_meta": {"theta": 0.5, "engine": "E1", "scenario": "Base"},
        "cells": {"q0.50_r0.50": {"per_seed": {
            seed: {"tp_dates": ["2019-06-01"], "fp_dates": []}
            for seed in seeds}}}}


def test_conservation_seed_manifest_rogue_seed_is_flagged():
    day_strata = _day_strata_with({"2019-06-01": "TP"})
    grid_samples = _seeded_grid_samples((7, 13, 31))
    records = _full_record_matrix(["2019-06-01"])
    rogue_manifest = dict(handoff.build_seed_manifest())
    rogue_manifest["research_bootstrap_seeds"] = [7, 13, 99]
    problems = handoff.verify_handoff_conservation(
        day_strata, grid_samples, records, seed_manifest=rogue_manifest)
    assert any("research_bootstrap_seeds" in p and "99" in p
              for p in problems)


def test_conservation_fourth_seed_in_grid_samples_is_flagged():
    day_strata = _day_strata_with({"2019-06-01": "TP"})
    grid_samples = _seeded_grid_samples((7, 13, 31, 99))
    records = _full_record_matrix(["2019-06-01"])
    manifest = handoff.build_seed_manifest()
    problems = handoff.verify_handoff_conservation(
        day_strata, grid_samples, records, seed_manifest=manifest)
    assert any("99" in p and "seed AXIS LOCK" in p for p in problems)


def test_conservation_seed_manifest_not_supplied_skips_seed_axis_check():
    """`seed_manifest` is OPTIONAL: a grid_samples carrying a rogue 4th seed
    is not flagged for the seed axis when no manifest is supplied to compare
    against (there is nothing to cross-check) — the caller must opt in."""
    day_strata = _day_strata_with({"2019-06-01": "TP"})
    grid_samples = _seeded_grid_samples((7, 13, 31, 99))
    records = _full_record_matrix(["2019-06-01"])
    problems = handoff.verify_handoff_conservation(day_strata, grid_samples,
                                                    records)
    assert not any("seed AXIS LOCK" in p for p in problems)


def test_conservation_matching_seed_manifest_adds_no_problems():
    day_strata = _day_strata_with({"2019-06-01": "TP"})
    grid_samples = _seeded_grid_samples((7, 13, 31))
    records = _full_record_matrix(["2019-06-01"])
    manifest = handoff.build_seed_manifest()
    problems = handoff.verify_handoff_conservation(
        day_strata, grid_samples, records, seed_manifest=manifest)
    assert problems == []


# ---------------------------------------------------------------------------
# formal_seal_admission (M6.1.1 S2 item 3, Codex finding (c): a dead
# `formal_sealable` flag with no consumer — this IS the consumer; M6.1.3 S2:
# admission must validate ARTIFACT CONTENT, never trust formal_sealable=True)
# ---------------------------------------------------------------------------

def test_formal_seal_admission_missing_flag_entirely_is_a_problem():
    problems = handoff.formal_seal_admission({"no_flag": {"some_key": 1}})
    assert len(problems) == 1
    assert "no_flag" in problems[0]
    assert "missing" in problems[0]


def test_formal_seal_admission_todays_real_builders_all_refused():
    """The three real M6.1 handoff builders are ALL formal_sealable=False
    today (DR-M6-E / DR-M6-F / crn_scope all open) — exactly three problems,
    each naming its own blocking UNRESOLVED marker(s)."""
    day_rows = {"2019-06-03": _day_row()}
    day_strata = handoff.build_day_strata(day_rows, thetas=[0.5])
    d_tp, d_fp, strata = _fabricated_grid_populations()
    grid_output = gridmix.build_grid(d_tp, d_fp, strata, base_rate_p=0.4,
                                     q_grid=[0.50], r_grid=[0.50])
    grid_samples = handoff.build_grid_samples(grid_output, run_meta=_run_meta())
    seed_manifest = handoff.build_seed_manifest()

    assert day_strata["formal_sealable"] is False
    assert grid_samples["formal_sealable"] is False
    assert seed_manifest["formal_sealable"] is False

    problems = handoff.formal_seal_admission({
        "day_strata": day_strata, "grid_samples": grid_samples,
        "seed_manifest": seed_manifest})
    assert len(problems) == 3
    day_strata_problem = next(p for p in problems if p.startswith("day_strata"))
    assert "event_stratum" in day_strata_problem
    assert "UNRESOLVED_DR-M6-F" in day_strata_problem
    grid_samples_problem = next(p for p in problems
                                if p.startswith("grid_samples"))
    assert "k_policy" in grid_samples_problem
    assert "UNRESOLVED_DR-M6-E" in grid_samples_problem
    assert "crn_scope" in grid_samples_problem
    # replay_status is ALSO always PARTIAL today (M6.1.1 S2 item 5) — the
    # content-recomputed refusal names it too, not only the k_policy/
    # crn_scope markers.
    assert "replay_status" in grid_samples_problem
    assert handoff.REPLAY_STATUS_PARTIAL_SINGLE_STRATUM in grid_samples_problem
    seed_manifest_problem = next(p for p in problems
                                 if p.startswith("seed_manifest"))
    assert "k_policy" in seed_manifest_problem
    assert "crn_scope" in seed_manifest_problem


def test_formal_seal_admission_empty_day_strata_is_refused():
    """An EMPTY day_strata (LOW-3: `bool(days) and ...`) is formal_sealable
    =False; the content-recomputed refusal now names the CONCRETE reason
    (days is empty) rather than falling back to a marker-less generic
    message."""
    empty_day_strata = handoff.build_day_strata({}, thetas=[0.5])
    assert empty_day_strata["formal_sealable"] is False
    problems = handoff.formal_seal_admission({"day_strata": empty_day_strata})
    assert len(problems) == 1
    assert "day_strata" in problems[0]
    assert "not True" in problems[0]
    assert "EMPTY" in problems[0]


def test_formal_seal_admission_sorted_and_deterministic():
    artifacts = {
        "z_artifact": {"formal_sealable": False},
        "a_artifact": {},
    }
    problems = handoff.formal_seal_admission(artifacts)
    assert problems == sorted(problems)
    assert len(problems) == 2


# ---------------------------------------------------------------------------
# formal_seal_admission — TEST_ONLY positive (sealable) fixtures
#
# day_strata's event_stratum (DR-M6-F), grid_samples'/seed_manifest's
# replay.k_policy / crn_scope (DR-M6-E / crn_scope) and grid_samples'
# replay_status (multi-stratum replay) are ALL hardwired UNRESOLVED/PARTIAL
# by their real builders, with NO supported parameter to resolve them (see
# handoff.py's module docstring). Per the M6.1.3 S2 brief: build the REAL
# artifact via the real builder (full schema fidelity, real per-cell seed
# sets from the real gridmix/build_grid pipeline) and then override ONLY
# those hardwired leaves to an explicit, clearly-named TEST_ONLY-resolved
# value — never a minimal/fake shape. "First prove positives pass, then
# mutate."
# ---------------------------------------------------------------------------

def _sealable_day_strata_artifact():
    day_rows = {
        "2019-06-03": _day_row(),
        "2019-06-04": _day_row(event_flag_final="CPI"),
    }
    out = handoff.build_day_strata(day_rows, thetas=[0.5])
    days = {d: dict(row) for d, row in out["days"].items()}
    for row in days.values():
        row["event_stratum"] = "TEST_ONLY_resolved_stratum"   # not UNRESOLVED*
    return {**out, "days": days, "formal_sealable": True}


def _sealable_grid_samples_artifact(theta=0.5, engine="E1", scenario="Base"):
    d_tp, d_fp, strata = _fabricated_grid_populations()
    grid_output = gridmix.build_grid(d_tp, d_fp, strata, base_rate_p=0.4,
                                     q_grid=[0.50], r_grid=[0.50])
    samples = handoff.build_grid_samples(
        grid_output,
        run_meta=_run_meta(theta=theta, engine=engine, scenario=scenario))
    replay = dict(samples["replay"])
    replay["k_policy"] = "TEST_ONLY_resolved_k_policy"
    replay["crn_scope"] = "TEST_ONLY_resolved_crn_scope"
    return {**samples, "replay": replay,
           "replay_status": handoff.REPLAY_STATUS_CLOSED,
           "formal_sealable": True}


def _sealable_seed_manifest_artifact():
    manifest = dict(handoff.build_seed_manifest())
    manifest["k_policy"] = "TEST_ONLY_resolved_k_policy"
    manifest["crn_scope"] = "TEST_ONLY_resolved_crn_scope"
    manifest["formal_sealable"] = True
    return manifest


def test_positive_sealable_day_strata_is_admitted():
    artifact = _sealable_day_strata_artifact()
    assert handoff.formal_seal_admission({"day_strata": artifact}) == []


def test_positive_sealable_grid_samples_is_admitted():
    artifact = _sealable_grid_samples_artifact()
    # sanity: the real gridmix pipeline really did produce a full {7,13,31}
    # per-cell seed set (never faked in this fixture)
    cell = artifact["cells"]["q0.50_r0.50"]
    assert set(cell["per_seed"]) == {7, 13, 31}
    assert handoff.formal_seal_admission({"grid_samples": artifact}) == []


def test_positive_sealable_seed_manifest_is_admitted():
    artifact = _sealable_seed_manifest_artifact()
    assert handoff.formal_seal_admission({"seed_manifest": artifact}) == []


def test_positive_all_three_types_together_are_admitted():
    """The three real handoff artifact types, all TEST_ONLY-resolved to
    sealable, supplied in ONE call — proves the per-artifact-TYPE
    recognition dispatches each to its own validator correctly rather than
    accidentally cross-applying one type's rules to another."""
    artifacts = {
        "day_strata": _sealable_day_strata_artifact(),
        "grid_samples": _sealable_grid_samples_artifact(),
        "seed_manifest": _sealable_seed_manifest_artifact(),
    }
    assert handoff.formal_seal_admission(artifacts) == []


def test_positive_grid_samples_cross_checked_against_matching_seed_manifest():
    """Task 3: a feasible cell's seed set is cross-checked PER CELL against
    a supplied SEED_MANIFEST artifact when both are supplied — agreement is
    silent (no problem)."""
    artifacts = {
        "grid_samples": _sealable_grid_samples_artifact(),
        "seed_manifest": _sealable_seed_manifest_artifact(),
    }
    assert handoff.formal_seal_admission(artifacts) == []


# ---------------------------------------------------------------------------
# formal_seal_admission — mutation battery (every refusal the M6.1.3 S2
# brief names explicitly, each proven REFUSED even though formal_sealable
# is (mutated to) True — CONTRADICTION path)
# ---------------------------------------------------------------------------

def test_bare_shell_with_true_flag_is_a_contradiction():
    """A bare `{"formal_sealable": True}` shell (and one with an arbitrary
    extra "nested" key) matches NONE of the three real artifact schemas —
    refused as a CONTRADICTION, never trusted just because the flag says
    True."""
    artifacts = {
        "a": {"formal_sealable": True},
        "b": {"formal_sealable": True, "nested": {"x": 1}},
    }
    problems = handoff.formal_seal_admission(artifacts)
    assert len(problems) == 2
    for p in problems:
        assert "CONTRADICTION" in p
        assert "does not match any recognized artifact schema" in p


def test_unresolved_marker_with_true_flag_is_a_contradiction():
    """A sealable-shaped day_strata mutated to re-introduce ONE real
    UNRESOLVED marker (even with formal_sealable forced True) is refused —
    "any UNRESOLVED marker anywhere" is checked regardless of the flag."""
    artifact = _sealable_day_strata_artifact()
    days = dict(artifact["days"])
    one_date = next(iter(days))
    mutated_row = dict(days[one_date])
    mutated_row["event_stratum"] = handoff._unresolved("DR-M6-F")
    days[one_date] = mutated_row
    artifact = {**artifact, "days": days}
    problems = handoff.formal_seal_admission({"day_strata": artifact})
    assert len(problems) == 1
    assert "CONTRADICTION" in problems[0]
    assert "event_stratum" in problems[0]
    assert "UNRESOLVED_DR-M6-F" in problems[0]


def test_replay_status_partial_with_true_flag_is_refused():
    """replay_status PARTIAL is refused even with formal_sealable forced
    True (M6.1.1 S2 item 5 discipline extended into the admission gate)."""
    artifact = dict(_sealable_grid_samples_artifact())
    artifact["replay_status"] = handoff.REPLAY_STATUS_PARTIAL_SINGLE_STRATUM
    problems = handoff.formal_seal_admission({"grid_samples": artifact})
    assert len(problems) == 1
    assert "CONTRADICTION" in problems[0]
    assert "replay_status" in problems[0]
    assert handoff.REPLAY_STATUS_PARTIAL_SINGLE_STRATUM in problems[0]


def test_missing_and_extra_top_level_fields_are_both_refused():
    missing = dict(_sealable_day_strata_artifact())
    del missing["ordering"]
    problems = handoff.formal_seal_admission({"day_strata": missing})
    assert len(problems) == 1
    assert "missing field" in problems[0]
    assert "ordering" in problems[0]

    extra = dict(_sealable_day_strata_artifact())
    extra["bogus_extra_field"] = 1
    problems = handoff.formal_seal_admission({"day_strata": extra})
    assert len(problems) == 1
    assert "extra field" in problems[0]
    assert "bogus_extra_field" in problems[0]


def test_missing_theta_engine_scenario_individually_refused():
    for key in ("theta", "engine", "scenario"):
        artifact = dict(_sealable_grid_samples_artifact())
        run_meta = dict(artifact["run_meta"])
        del run_meta[key]
        artifact["run_meta"] = run_meta
        problems = handoff.formal_seal_admission({"grid_samples": artifact})
        assert len(problems) == 1, key
        assert "run_meta" in problems[0] and "missing field" in problems[0]
        assert key in problems[0]


def test_wrong_seeds_missing_one_seed_in_a_cell_refused():
    artifact = dict(_sealable_grid_samples_artifact())
    cells = dict(artifact["cells"])
    cell = dict(cells["q0.50_r0.50"])
    per_seed = dict(cell["per_seed"])
    del per_seed[31]
    cell["per_seed"] = per_seed
    cells["q0.50_r0.50"] = cell
    artifact["cells"] = cells
    problems = handoff.formal_seal_admission({"grid_samples": artifact})
    assert len(problems) == 1
    assert "CONTRADICTION" in problems[0]
    assert "seed set is incomplete" in problems[0]


def test_per_cell_seed_sets_incomplete_even_though_union_is_complete():
    """Two feasible cells whose UNION of per-seed keys is exactly
    {7, 13, 31}, but each cell INDIVIDUALLY is missing one — refused,
    because the check is per cell, never the union."""
    artifact = dict(_sealable_grid_samples_artifact())
    cells = dict(artifact["cells"])
    base_cell = cells["q0.50_r0.50"]
    cell_a = dict(base_cell)
    per_seed_a = {s: v for s, v in base_cell["per_seed"].items() if s != 31}
    cell_a["per_seed"] = per_seed_a
    cell_b = dict(base_cell)
    per_seed_b = {s: v for s, v in base_cell["per_seed"].items() if s != 7}
    cell_b["per_seed"] = per_seed_b
    artifact["cells"] = {"q0.50_r0.50": cell_a, "q0.35_r0.20": cell_b}
    problems = handoff.formal_seal_admission({"grid_samples": artifact})
    assert len(problems) == 1
    assert problems[0].count("seed set is incomplete") == 2


def test_seed_keys_wrong_type_never_coerced():
    """bool / float / numeric-string seed keys are refused outright — never
    silently coerced through int() into the seed they merely resemble."""
    for bad_seed_31 in (31.0, "31", True):
        artifact = dict(_sealable_grid_samples_artifact())
        cells = dict(artifact["cells"])
        cell = dict(cells["q0.50_r0.50"])
        per_seed = {s: v for s, v in cell["per_seed"].items() if s != 31}
        per_seed[bad_seed_31] = cell["per_seed"][31]
        cell["per_seed"] = per_seed
        cells["q0.50_r0.50"] = cell
        artifact["cells"] = cells
        problems = handoff.formal_seal_admission({"grid_samples": artifact})
        assert len(problems) == 1, bad_seed_31
        assert "non-strict-int" in problems[0], bad_seed_31


def test_seed_manifest_seed_wrong_type_never_coerced():
    for bad_seeds in ([7, 13, 31.0], [7, 13, "31"], [7, 13, True]):
        artifact = dict(_sealable_seed_manifest_artifact())
        artifact["research_bootstrap_seeds"] = bad_seeds
        problems = handoff.formal_seal_admission({"seed_manifest": artifact})
        assert len(problems) == 1, bad_seeds
        assert "non-strict-int" in problems[0], bad_seeds


def test_approximate_theta_refused_exact_equality_no_tolerance():
    artifact = dict(_sealable_grid_samples_artifact())
    run_meta = dict(artifact["run_meta"])
    run_meta["theta"] = 0.5000001
    artifact["run_meta"] = run_meta
    problems = handoff.formal_seal_admission({"grid_samples": artifact})
    assert len(problems) == 1
    assert "CONTRADICTION" in problems[0]
    assert "not EXACTLY one of study.FROZEN_THETAS" in problems[0]
    # the exact frozen value is still fine (control)
    artifact2 = dict(_sealable_grid_samples_artifact())
    assert artifact2["run_meta"]["theta"] == 0.5
    assert handoff.formal_seal_admission({"grid_samples": artifact2}) == []


def test_unknown_scenario_refused():
    artifact = dict(_sealable_grid_samples_artifact())
    run_meta = dict(artifact["run_meta"])
    run_meta["scenario"] = "Extreme"
    artifact["run_meta"] = run_meta
    problems = handoff.formal_seal_admission({"grid_samples": artifact})
    assert len(problems) == 1
    assert "unknown scenario" in problems[0]
    assert "Extreme" in problems[0]


def test_renamed_engine_refused():
    artifact = dict(_sealable_grid_samples_artifact())
    run_meta = dict(artifact["run_meta"])
    run_meta["engine"] = "E9"
    artifact["run_meta"] = run_meta
    problems = handoff.formal_seal_admission({"grid_samples": artifact})
    assert len(problems) == 1
    assert "unknown or renamed engine" in problems[0]
    assert "E9" in problems[0]


def test_extra_empty_engine_and_empty_grid_both_named():
    """A grid_samples claiming the already-deleted third engine ("E3" —
    study.py: "ENGINES = (E1, E2)  # frozen: S0 SS7 (E3 deleted)") with no
    cells at all: both the unknown-engine axis violation AND the empty-grid
    violation are named in the same refusal."""
    artifact = dict(_sealable_grid_samples_artifact())
    run_meta = dict(artifact["run_meta"])
    run_meta["engine"] = "E3"
    artifact["run_meta"] = run_meta
    artifact["cells"] = {}
    problems = handoff.formal_seal_admission({"grid_samples": artifact})
    assert len(problems) == 1
    assert "CONTRADICTION" in problems[0]
    assert "E3" in problems[0] and "unknown or renamed engine" in problems[0]
    assert "cells is EMPTY" in problems[0]


def test_empty_grid_refused():
    artifact = dict(_sealable_grid_samples_artifact())
    artifact["cells"] = {}
    problems = handoff.formal_seal_admission({"grid_samples": artifact})
    assert len(problems) == 1
    assert "cells is EMPTY" in problems[0]


def test_wrong_seeds_in_seed_manifest_refused():
    artifact = dict(_sealable_seed_manifest_artifact())
    artifact["research_bootstrap_seeds"] = [7, 13, 99]
    problems = handoff.formal_seal_admission({"seed_manifest": artifact})
    assert len(problems) == 1
    assert "CONTRADICTION" in problems[0]
    assert "research_bootstrap_seeds" in problems[0]


def test_reordered_seeds_in_seed_manifest_refused():
    """Order is part of REBUILDABLE content too: the manifest's seeds must
    equal contracts.RESEARCH_BOOTSTRAP_SEEDS as an ordered list, not merely
    as a set (the FIRST seed is the quoted-interval convention)."""
    artifact = dict(_sealable_seed_manifest_artifact())
    artifact["research_bootstrap_seeds"] = [13, 7, 31]
    problems = handoff.formal_seal_admission({"seed_manifest": artifact})
    assert len(problems) == 1
    assert "research_bootstrap_seeds" in problems[0]


def test_wrong_stream_tag_in_seed_manifest_refused():
    artifact = dict(_sealable_seed_manifest_artifact())
    artifact["stream_tags"] = {**artifact["stream_tags"],
                               "grid_stream_tag": 1234}
    problems = handoff.formal_seal_admission({"seed_manifest": artifact})
    assert len(problems) == 1
    assert "stream_tags" in problems[0] and "1234" in problems[0]


def test_seed_manifest_missing_and_extra_fields_refused():
    missing = dict(_sealable_seed_manifest_artifact())
    del missing["quoted_seed_convention"]
    problems = handoff.formal_seal_admission({"seed_manifest": missing})
    assert len(problems) == 1
    assert "missing field" in problems[0]
    assert "quoted_seed_convention" in problems[0]

    extra = dict(_sealable_seed_manifest_artifact())
    extra["bogus"] = 1
    problems = handoff.formal_seal_admission({"seed_manifest": extra})
    assert len(problems) == 1
    assert "extra field" in problems[0]
    assert "bogus" in problems[0]


def test_grid_samples_cross_checked_against_disagreeing_seed_manifest():
    """Task 3: even a grid_samples whose OWN per-cell seeds are exactly
    {7, 13, 31} is refused when a SUPPLIED seed_manifest disagrees — the
    cross-check is against the manifest actually supplied in this call, not
    only against the frozen constant."""
    grid_samples = _sealable_grid_samples_artifact()
    rogue_manifest = dict(_sealable_seed_manifest_artifact())
    rogue_manifest["research_bootstrap_seeds"] = [7, 13, 99]
    problems = handoff.formal_seal_admission({
        "grid_samples": grid_samples, "seed_manifest": rogue_manifest})
    assert len(problems) == 2
    grid_problem = next(p for p in problems if p.startswith("grid_samples"))
    assert "cross-check against the seed manifest failed" in grid_problem
    manifest_problem = next(p for p in problems if p.startswith("seed_manifest"))
    assert "research_bootstrap_seeds" in manifest_problem


def test_renamed_cell_flagged_within_a_full_engine_scenario_battery():
    """A full E1/E2 x {Base,Conservative,Stress,Severe} battery of sealable
    grid_samples artifacts (8 cells, mirroring the frozen matrix
    verify_handoff_conservation enforces on the record side) all admit
    cleanly; renaming ONE artifact's engine to an unrecognised value is
    caught on exactly that one artifact, independent of the rest of the
    battery."""
    battery = {
        f"grid_samples_{engine}_{scenario}":
            _sealable_grid_samples_artifact(engine=engine, scenario=scenario)
        for engine in handoff.ENGINES for scenario in handoff.SCENARIOS
    }
    assert len(battery) == 8
    assert handoff.formal_seal_admission(battery) == []

    renamed_key = "grid_samples_E1_Base"
    mutated = dict(battery)
    artifact = dict(mutated[renamed_key])
    run_meta = dict(artifact["run_meta"])
    run_meta["engine"] = "E9"
    artifact["run_meta"] = run_meta
    mutated[renamed_key] = artifact

    problems = handoff.formal_seal_admission(mutated)
    assert len(problems) == 1
    assert problems[0].startswith(renamed_key)
    assert "E9" in problems[0]


# ---------------------------------------------------------------------------
# dumps_canonical
# ---------------------------------------------------------------------------

def test_dumps_canonical_sorts_keys_and_is_stable():
    out1 = handoff.dumps_canonical({"b": 1, "a": 2})
    out2 = handoff.dumps_canonical({"a": 2, "b": 1})
    assert out1 == out2
    assert json.loads(out1) == {"a": 2, "b": 1}
    assert out1.index('"a"') < out1.index('"b"')


def test_dumps_canonical_rejects_nan():
    with pytest.raises(ValueError):
        handoff.dumps_canonical({"x": float("nan")})
    with pytest.raises(ValueError):
        handoff.dumps_canonical({"x": float("inf")})
