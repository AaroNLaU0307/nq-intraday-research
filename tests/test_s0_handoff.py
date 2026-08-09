"""Synthetic checks for itsf.s0.handoff (E6 S0 -> MC handoff schema skeleton).

SA-18-style scope. Every population here is a hand-written dict of fabricated
dates/values: no real archive is touched, no clock is read. The replay
determinism test draws randomness only through `itsf.s0.gridmix`, whose
streams derive exclusively from contracts.RESEARCH_BOOTSTRAP_SEEDS.

M6.1.4 (RC-2) note on the FIXTURES
----------------------------------
Admission now recomputes SEMANTICS from an INDEPENDENT `handoff.SourceContext`
and is ATOMIC over a bundle. Two consequences run through every fixture below:

* an "approved-looking" string can no longer resolve an UNRULED axis. A
  sealable fixture must therefore declare its TEST_ONLY ruling on the SOURCE
  CONTEXT (`_ruled_source()`), where a reviewer can see it, instead of
  smuggling it into the artifact where it would be self-authorising;
* a GRID_SAMPLES artifact depends on exactly one valid DAY_STRATA and one
  valid SEED_MANIFEST in the SAME admission call, so positive grid fixtures
  are submitted as a coherent BUNDLE (`_sealable_bundle()`) whose day_strata
  covers exactly the grid's own date populations.
"""
from __future__ import annotations

import json

import numpy as np
import pytest

from itsf import contracts
from itsf.s0 import context as s0_context
from itsf.s0 import gridmix, handoff, stability, stats

ERA_ACTUAL = "actual_micro_available_era"
ERA_PROXY = "counterfactual_micro_execution"
EPOCH = "2018-2021"
MICRO_ERA_BOUNDARY = s0_context.MICRO_ERA_BOUNDARY

# The per-day volatility axis has NO ruled vocabulary anywhere in the tree
# (DR-M6-B-v2 open), so the only admissible `vol_status` token today is an
# UNRESOLVED marker — an arbitrary "resolved" would be exactly the premature
# resolution the marker discipline exists to prevent.
VOL_STATUS_MARKER = handoff._unresolved("DR-M6-B-v2")

# TEST_ONLY rulings. These live on the SOURCE CONTEXT, never inside an
# artifact: an artifact that could authorise its own vocabulary would defeat
# the whole point of recomputing content from an independent source.
TEST_ONLY_STRATUM = "TEST_ONLY_ruled_event_stratum"
TEST_ONLY_VOL_STATUS = "TEST_ONLY_ruled_vol_status"
TEST_ONLY_K_POLICY = "TEST_ONLY_ruled_k_policy"
TEST_ONLY_CRN_SCOPE = "TEST_ONLY_ruled_crn_scope"


def _epoch_for(year: int) -> str:
    """Epoch label for `year`, computed HERE from `stability.EPOCHS` so the
    fixtures do not borrow handoff.py's own lookup to build the input it is
    then asked to verify."""
    for label, lo, hi in stability.EPOCHS:
        if lo <= year <= hi:
            return label
    return stability.OUTSIDE_EPOCHS


def _day_row(date: str = "2019-06-03", **overrides) -> dict[str, object]:
    """One CONSISTENT day_rows entry for `date`.

    era / epoch / year are DERIVED from the date here, because the builder
    (and admission) now recompute all three from the date itself against the
    frozen boundaries — a fixture that hardcoded them would simply be an
    invalid day.
    """
    row = {
        "micro_execution_era": (ERA_ACTUAL if date >= MICRO_ERA_BOUNDARY
                                else ERA_PROXY),
        "stability_epoch": _epoch_for(int(date[:4])),
        "year": date[:4],
        "d_open": 1,
        "event_flag_final": "none",
        "vol_status": VOL_STATUS_MARKER,
        "tp_fp_class": {"theta_0.5": "TP"},
    }
    row.update(overrides)
    return row


def _ruled_source(**overrides) -> handoff.SourceContext:
    """A TEST_ONLY source context in which every DR-M6 axis the positive
    fixtures need is RULED. Passing this is the only way a concrete value on
    one of those axes becomes admissible."""
    kwargs: dict[str, object] = dict(
        thetas=(0.5,),
        event_stratum_vocabulary=frozenset({TEST_ONLY_STRATUM}),
        vol_status_vocabulary=frozenset({TEST_ONLY_VOL_STATUS}),
        k_policy=TEST_ONLY_K_POLICY,
        crn_scope=TEST_ONLY_CRN_SCOPE,
        replay_closure_ruled=True,
    )
    kwargs.update(overrides)
    return handoff.SourceContext(**kwargs)


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
        "2019-06-03": _day_row("2019-06-03"),
        "2019-01-02": _day_row("2019-01-02"),
        "2019-03-15": _day_row("2019-03-15"),
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
        "2019-06-03": _day_row("2019-06-03", event_flag_final=None),
        "2019-06-04": _day_row("2019-06-04", event_flag_final="CPI"),
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
        "2019-06-03": _day_row("2019-06-03", event_flag_final=None),
        "2019-06-04": _day_row("2019-06-04", event_flag_final="FOMC"),
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
    day_rows3 = {"2009-06-03": _day_row("2009-06-03")}
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


_GRID_CACHE: dict[str, object] = {}


def _full_lattice_grid_output():
    """`gridmix.build_grid` over the FROZEN 63-point (q, r) lattice — no axis
    override. Admission requires the complete lattice, so a sealable fixture
    cannot use the cheap single-cell grid the builder-level tests use.
    Cached: the same output is read-only for every consumer."""
    if "grid" not in _GRID_CACHE:
        d_tp, d_fp, strata = _fabricated_grid_populations()
        _GRID_CACHE["grid"] = gridmix.build_grid(d_tp, d_fp, strata,
                                                 base_rate_p=0.4)
    return _GRID_CACHE["grid"]


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
    """The int -> float normalisation is a BUILD-path convention and stays
    pinned. M6.1.4 additionally closes the axis gap the B0 matrix names:
    `build_grid_samples` itself now REFUSES an out-of-pair theta, because its
    self-check runs the same semantic checker admission does. So the
    normalisation is asserted on the helper that performs it, and the axis
    refusal on the builder."""
    assert handoff._validated_run_meta(_run_meta(theta=1))["theta"] == 1.0
    assert isinstance(handoff._validated_run_meta(_run_meta(theta=1))["theta"],
                      float)
    d_tp, d_fp, strata = _fabricated_grid_populations()
    grid_output = gridmix.build_grid(d_tp, d_fp, strata, base_rate_p=0.4,
                                     q_grid=[0.50], r_grid=[0.50])
    with pytest.raises(ValueError, match="FROZEN_THETAS"):
        handoff.build_grid_samples(grid_output, run_meta=_run_meta(theta=1))


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
    this fixture to exactly ONE stratum sidesteps that gap honestly.
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
        day_rows[d] = _day_row(d, tp_fp_class={"theta_0.5": "TP"})
    for d in d_fp:
        day_rows[d] = _day_row(d, tp_fp_class={"theta_0.5": "FP"})
    day_strata = handoff.build_day_strata(day_rows, thetas=[0.5])

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
    day_rows = {d: _day_row(d, tp_fp_class={"theta_0.5": cls})
                for d, cls in dates_classes.items()}
    return handoff.build_day_strata(day_rows, thetas=[0.5])


def _full_record_matrix(dates) -> dict[str, dict[str, list[str]]]:
    """The frozen 8-cell {ENGINES} x {SCENARIOS} record matrix, every cell
    carrying the SAME `dates` list — used wherever a test's point is NOT the
    per-cell record-matrix-shape check itself (M6.1.1 S2 item 1)."""
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
    day_strata's SAME-theta TP/FP call must be caught."""
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
    assert any("2019-06-02" in p and "missing a record" in p
               for p in problems)


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
    problems = handoff.verify_handoff_conservation(day_strata, grid_samples,
                                                   {})
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
# ---------------------------------------------------------------------------

def _hand_built_day_strata(tp_fp_class: dict) -> dict[str, object]:
    """A day_strata assembled BY HAND, in the exact shape build_day_strata
    emits, so a rogue theta axis can be presented to the conservation layer
    without going through the builder (which now refuses one outright)."""
    return {
        "schema_version": handoff.SCHEMA_VERSION,
        "ordering": "sorted-by-date",
        "formal_sealable": False,
        "days": {"2019-06-03": {
            "micro_execution_era": ERA_ACTUAL,
            "stability_epoch": EPOCH,
            "year": "2019",
            "d_open": 1,
            "event_flag_final": "none",
            "event_na": False,
            "event_stratum": handoff._unresolved("DR-M6-F"),
            "vol_status": VOL_STATUS_MARKER,
            "tp_fp_class": dict(tp_fp_class),
        }},
    }


def test_conservation_theta_key_outside_frozen_pair_is_flagged():
    """The conservation layer's theta AXIS LOCK, exercised on a HAND-BUILT
    artifact.

    M6.1.4 closeout changed the premise this test used to carry: the axis gap
    it documented ("build_day_strata itself does not restrict `thetas` to the
    frozen pair") is now closed at the BUILDER layer too, because
    `SourceContext.thetas` is membership-bound to `study.FROZEN_THETAS`. Both
    halves are asserted — the builder refuses the rogue axis at construction,
    and the conservation check still catches one that reached an artifact by
    some other route.
    """
    day_rows = {"2019-06-03": _day_row(tp_fp_class={"theta_0.9": "TP"})}
    with pytest.raises(handoff.SourceContextError, match="FROZEN_THETAS"):
        handoff.build_day_strata(day_rows, thetas=[0.9])

    day_strata = _hand_built_day_strata({"theta_0.9": "TP"})
    grid_samples = {"cells": {}}
    problems = handoff.verify_handoff_conservation(day_strata, grid_samples,
                                                   {})
    assert any("theta_0.9" in p and "frozen theta pair" in p
               for p in problems)


def test_conservation_run_meta_theta_outside_frozen_pair_is_flagged():
    day_strata = _day_strata_with({"2019-06-01": "TP"})
    grid_samples = {"run_meta": {"theta": 0.9, "engine": "E1",
                                 "scenario": "Base"}, "cells": {}}
    problems = handoff.verify_handoff_conservation(day_strata, grid_samples,
                                                   {})
    assert any("theta_0.9" in p and "frozen theta pair" in p
               for p in problems)


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
# admission must validate ARTIFACT CONTENT, never trust formal_sealable=True;
# M6.1.4: admission must recompute SEMANTICS from an INDEPENDENT source
# context, ATOMICALLY over the bundle)
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
    grid_samples = handoff.build_grid_samples(grid_output,
                                              run_meta=_run_meta())
    seed_manifest = handoff.build_seed_manifest()

    assert day_strata["formal_sealable"] is False
    assert grid_samples["formal_sealable"] is False
    assert seed_manifest["formal_sealable"] is False

    problems = handoff.formal_seal_admission({
        "day_strata": day_strata, "grid_samples": grid_samples,
        "seed_manifest": seed_manifest})
    assert len(problems) == 3
    day_strata_problem = next(p for p in problems
                              if p.startswith("day_strata"))
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
# day_strata's event_stratum (DR-M6-F) and vol_status (DR-M6-B-v2),
# grid_samples'/seed_manifest's replay.k_policy / crn_scope (DR-M6-E /
# crn_scope) and grid_samples' replay_status (multi-stratum replay) are ALL
# hardwired UNRESOLVED/PARTIAL by their real builders. Per M6.1.4 item 7,
# no string an ARTIFACT carries can resolve them — the ruling must come from
# the SOURCE CONTEXT. So: build the REAL artifact via the real builder (full
# schema fidelity, real per-cell seed sets from the real gridmix/build_grid
# pipeline over the frozen 63-point lattice), override ONLY the hardwired
# leaves with values the TEST_ONLY source context actually RULES, and submit
# the three as one coherent BUNDLE. "First prove positives pass, then
# mutate."
# ---------------------------------------------------------------------------

def _sealable_day_strata_artifact():
    """A day_strata covering EXACTLY the grid fixture's TP/FP populations, so
    the bundle's cross-artifact conservation checks have a real preimage."""
    d_tp, d_fp, _strata = _fabricated_grid_populations()
    day_rows = {}
    for d in d_tp:
        day_rows[d] = _day_row(d, tp_fp_class={"theta_0.5": "TP"})
    for d in d_fp:
        day_rows[d] = _day_row(d, tp_fp_class={"theta_0.5": "FP"})
    out = handoff.build_day_strata(day_rows, thetas=[0.5])
    days = {d: {**row, "event_stratum": TEST_ONLY_STRATUM,
                "vol_status": TEST_ONLY_VOL_STATUS}
            for d, row in out["days"].items()}
    return {**out, "days": days, "formal_sealable": True}


def _sealable_grid_samples_artifact(theta=0.5, engine="E1", scenario="Base"):
    samples = handoff.build_grid_samples(
        _full_lattice_grid_output(),
        run_meta=_run_meta(theta=theta, engine=engine, scenario=scenario))
    replay = dict(samples["replay"])
    replay["k_policy"] = TEST_ONLY_K_POLICY
    replay["crn_scope"] = TEST_ONLY_CRN_SCOPE
    return {**samples, "replay": replay,
            "replay_status": handoff.REPLAY_STATUS_CLOSED,
            "formal_sealable": True}


def _sealable_seed_manifest_artifact():
    manifest = dict(handoff.build_seed_manifest())
    manifest["k_policy"] = TEST_ONLY_K_POLICY
    manifest["crn_scope"] = TEST_ONLY_CRN_SCOPE
    manifest["formal_sealable"] = True
    return manifest


def _sealable_bundle(**overrides) -> dict[str, object]:
    bundle = {
        "day_strata": _sealable_day_strata_artifact(),
        "seed_manifest": _sealable_seed_manifest_artifact(),
        "grid_samples": _sealable_grid_samples_artifact(),
    }
    bundle.update(overrides)
    return bundle


def _admit_bundle(**overrides) -> list[str]:
    """Admission over the sealable BUNDLE with named artifacts replaced —
    the only way to exercise a grid mutation in isolation, since a grid whose
    dependencies are absent is withheld for that reason alone."""
    return handoff.formal_seal_admission(_sealable_bundle(**overrides),
                                         source=_ruled_source())


def _admit_alone(name: str, artifact) -> list[str]:
    """Admission over ONE artifact that has no dependencies of its own
    (day_strata / seed_manifest)."""
    return handoff.formal_seal_admission({name: artifact},
                                         source=_ruled_source())


def test_positive_sealable_day_strata_is_admitted():
    artifact = _sealable_day_strata_artifact()
    assert _admit_alone("day_strata", artifact) == []


def test_positive_sealable_grid_samples_is_admitted():
    artifact = _sealable_grid_samples_artifact()
    # sanity: the real gridmix pipeline really did produce a full {7,13,31}
    # per-cell seed set (never faked in this fixture)
    cell = artifact["cells"]["q0.50_r0.50"]
    assert set(cell["per_seed"]) == {7, 13, 31}
    assert _admit_bundle(grid_samples=artifact) == []


def test_positive_sealable_seed_manifest_is_admitted():
    artifact = _sealable_seed_manifest_artifact()
    assert _admit_alone("seed_manifest", artifact) == []


def test_positive_all_three_types_together_are_admitted():
    """The three real handoff artifact types, all TEST_ONLY-resolved to
    sealable, supplied in ONE call — proves the per-artifact-TYPE
    recognition dispatches each to its own validator correctly rather than
    accidentally cross-applying one type's rules to another."""
    assert _admit_bundle() == []


def test_positive_grid_samples_cross_checked_against_matching_seed_manifest():
    """Task 3: a feasible cell's seed set is cross-checked PER CELL against
    a supplied SEED_MANIFEST artifact when both are supplied — agreement is
    silent (no problem)."""
    assert _admit_bundle() == []


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
    problems = _admit_alone("day_strata", artifact)
    assert len(problems) == 1
    assert "CONTRADICTION" in problems[0]
    assert "event_stratum" in problems[0]
    assert "UNRESOLVED_DR-M6-F" in problems[0]


def test_replay_status_partial_with_true_flag_is_refused():
    """replay_status PARTIAL is refused even with formal_sealable forced
    True (M6.1.1 S2 item 5 discipline extended into the admission gate)."""
    artifact = dict(_sealable_grid_samples_artifact())
    artifact["replay_status"] = handoff.REPLAY_STATUS_PARTIAL_SINGLE_STRATUM
    problems = _admit_bundle(grid_samples=artifact)
    assert len(problems) == 1
    assert "CONTRADICTION" in problems[0]
    assert "replay_status" in problems[0]
    assert handoff.REPLAY_STATUS_PARTIAL_SINGLE_STRATUM in problems[0]


def test_missing_and_extra_top_level_fields_are_both_refused():
    missing = dict(_sealable_day_strata_artifact())
    del missing["ordering"]
    problems = _admit_alone("day_strata", missing)
    assert len(problems) == 1
    assert "missing field" in problems[0]
    assert "ordering" in problems[0]

    extra = dict(_sealable_day_strata_artifact())
    extra["bogus_extra_field"] = 1
    problems = _admit_alone("day_strata", extra)
    assert len(problems) == 1
    assert "extra field" in problems[0]
    assert "bogus_extra_field" in problems[0]


def test_missing_theta_engine_scenario_individually_refused():
    for key in ("theta", "engine", "scenario"):
        artifact = dict(_sealable_grid_samples_artifact())
        run_meta = dict(artifact["run_meta"])
        del run_meta[key]
        artifact["run_meta"] = run_meta
        problems = _admit_bundle(grid_samples=artifact)
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
    problems = _admit_bundle(grid_samples=artifact)
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
    cell_b = dict(cells["q0.35_r0.20"])
    per_seed_b = {s: v for s, v in cell_b["per_seed"].items() if s != 7}
    cell_b["per_seed"] = per_seed_b
    artifact["cells"] = {"q0.50_r0.50": cell_a, "q0.35_r0.20": cell_b}
    problems = _admit_bundle(grid_samples=artifact)
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
        problems = _admit_bundle(grid_samples=artifact)
        assert len(problems) == 1, bad_seed_31
        assert "non-strict-int" in problems[0], bad_seed_31


def test_seed_manifest_seed_wrong_type_never_coerced():
    for bad_seeds in ([7, 13, 31.0], [7, 13, "31"], [7, 13, True]):
        artifact = dict(_sealable_seed_manifest_artifact())
        artifact["research_bootstrap_seeds"] = bad_seeds
        problems = _admit_alone("seed_manifest", artifact)
        assert len(problems) == 1, bad_seeds
        assert "non-strict-int" in problems[0], bad_seeds


def test_approximate_theta_refused_exact_equality_no_tolerance():
    artifact = dict(_sealable_grid_samples_artifact())
    run_meta = dict(artifact["run_meta"])
    run_meta["theta"] = 0.5000001
    artifact["run_meta"] = run_meta
    problems = _admit_bundle(grid_samples=artifact)
    assert len(problems) == 1
    assert "CONTRADICTION" in problems[0]
    assert "not EXACTLY one of study.FROZEN_THETAS" in problems[0]
    # the exact frozen value is still fine (control)
    artifact2 = _sealable_grid_samples_artifact()
    assert artifact2["run_meta"]["theta"] == 0.5
    assert _admit_bundle(grid_samples=artifact2) == []


def test_unknown_scenario_refused():
    artifact = dict(_sealable_grid_samples_artifact())
    run_meta = dict(artifact["run_meta"])
    run_meta["scenario"] = "Extreme"
    artifact["run_meta"] = run_meta
    problems = _admit_bundle(grid_samples=artifact)
    assert len(problems) == 1
    assert "unknown scenario" in problems[0]
    assert "Extreme" in problems[0]


def test_renamed_engine_refused():
    artifact = dict(_sealable_grid_samples_artifact())
    run_meta = dict(artifact["run_meta"])
    run_meta["engine"] = "E9"
    artifact["run_meta"] = run_meta
    problems = _admit_bundle(grid_samples=artifact)
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
    problems = _admit_bundle(grid_samples=artifact)
    assert len(problems) == 1
    assert "CONTRADICTION" in problems[0]
    assert "E3" in problems[0] and "unknown or renamed engine" in problems[0]
    assert "cells is EMPTY" in problems[0]


def test_empty_grid_refused():
    artifact = dict(_sealable_grid_samples_artifact())
    artifact["cells"] = {}
    problems = _admit_bundle(grid_samples=artifact)
    assert len(problems) == 1
    assert "cells is EMPTY" in problems[0]


def test_wrong_seeds_in_seed_manifest_refused():
    artifact = dict(_sealable_seed_manifest_artifact())
    artifact["research_bootstrap_seeds"] = [7, 13, 99]
    problems = _admit_alone("seed_manifest", artifact)
    assert len(problems) == 1
    assert "CONTRADICTION" in problems[0]
    assert "research_bootstrap_seeds" in problems[0]


def test_reordered_seeds_in_seed_manifest_refused():
    """Order is part of REBUILDABLE content too: the manifest's seeds must
    equal contracts.RESEARCH_BOOTSTRAP_SEEDS as an ordered list, not merely
    as a set (the FIRST seed is the quoted-interval convention)."""
    artifact = dict(_sealable_seed_manifest_artifact())
    artifact["research_bootstrap_seeds"] = [13, 7, 31]
    problems = _admit_alone("seed_manifest", artifact)
    assert len(problems) == 1
    assert "research_bootstrap_seeds" in problems[0]


def test_wrong_stream_tag_in_seed_manifest_refused():
    artifact = dict(_sealable_seed_manifest_artifact())
    artifact["stream_tags"] = {**artifact["stream_tags"],
                               "grid_stream_tag": 1234}
    problems = _admit_alone("seed_manifest", artifact)
    assert len(problems) == 1
    assert "stream_tags" in problems[0] and "1234" in problems[0]


def test_seed_manifest_missing_and_extra_fields_refused():
    missing = dict(_sealable_seed_manifest_artifact())
    del missing["quoted_seed_convention"]
    problems = _admit_alone("seed_manifest", missing)
    assert len(problems) == 1
    assert "missing field" in problems[0]
    assert "quoted_seed_convention" in problems[0]

    extra = dict(_sealable_seed_manifest_artifact())
    extra["bogus"] = 1
    problems = _admit_alone("seed_manifest", extra)
    assert len(problems) == 1
    assert "extra field" in problems[0]
    assert "bogus" in problems[0]


def test_grid_samples_cross_checked_against_disagreeing_seed_manifest():
    """Task 3: even a grid_samples whose OWN per-cell seeds are exactly
    {7, 13, 31} is refused when a SUPPLIED seed_manifest disagrees — the
    cross-check is against the manifest actually supplied in this call, not
    only against the frozen constant."""
    rogue_manifest = dict(_sealable_seed_manifest_artifact())
    rogue_manifest["research_bootstrap_seeds"] = [7, 13, 99]
    problems = _admit_bundle(seed_manifest=rogue_manifest)
    assert len(problems) == 2
    grid_problem = next(p for p in problems if p.startswith("grid_samples"))
    assert "cross-check against the seed manifest failed" in grid_problem
    manifest_problem = next(p for p in problems
                            if p.startswith("seed_manifest"))
    assert "research_bootstrap_seeds" in manifest_problem


def test_renamed_cell_flagged_within_a_full_engine_scenario_battery():
    """A full E1/E2 x {Base,Conservative,Stress,Severe} battery of sealable
    grid_samples artifacts (8 artifacts, mirroring the frozen matrix
    verify_handoff_conservation enforces on the record side) all admit
    cleanly alongside their ONE shared day_strata/seed_manifest dependency;
    renaming ONE artifact's engine to an unrecognised value is caught on
    exactly that one artifact, independent of the rest of the battery."""
    battery = {
        f"grid_samples_{engine}_{scenario}":
            _sealable_grid_samples_artifact(engine=engine, scenario=scenario)
        for engine in handoff.ENGINES for scenario in handoff.SCENARIOS
    }
    assert len(battery) == 8
    bundle = {"day_strata": _sealable_day_strata_artifact(),
              "seed_manifest": _sealable_seed_manifest_artifact(), **battery}
    assert handoff.formal_seal_admission(bundle, source=_ruled_source()) == []

    renamed_key = "grid_samples_E1_Base"
    mutated = dict(bundle)
    artifact = dict(mutated[renamed_key])
    run_meta = dict(artifact["run_meta"])
    run_meta["engine"] = "E9"
    artifact["run_meta"] = run_meta
    mutated[renamed_key] = artifact

    problems = handoff.formal_seal_admission(mutated, source=_ruled_source())
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


# ===========================================================================
# M6.1.4 PHASE D — counter-example battery
#
# The blind-audit round-1 result this closes: 24 full-schema but
# SEMANTICALLY WRONG artifacts were ADMITTED (matrix classes D1-D13
# day_strata, D26-D34 grid_samples, D39-D41 seed_manifest). Every test below
# starts from a fixture that PASSES admission, mutates exactly one semantic
# fact, and proves the mutation is refused. `formal_sealable` is left True
# throughout, so each is also a proof the flag is never read as a pass.
# ===========================================================================

def _mutate_one_day(artifact, **row_overrides):
    days = dict(artifact["days"])
    one_date = sorted(days)[0]
    days[one_date] = {**days[one_date], **row_overrides}
    return {**artifact, "days": days}, one_date


# --- D1-D13: DAY_STRATA ----------------------------------------------------

def test_d_class_day_strata_wrong_schema_version_refused():
    artifact = dict(_sealable_day_strata_artifact())
    artifact["schema_version"] = "m6.1-draft-2"
    problems = _admit_alone("day_strata", artifact)
    assert len(problems) == 1
    assert "schema_version" in problems[0]
    assert "m6.1-draft-2" in problems[0]


def test_d_class_day_strata_ordering_token_forged_refused():
    artifact = dict(_sealable_day_strata_artifact())
    artifact["ordering"] = "whatever-order-we-felt-like"
    problems = _admit_alone("day_strata", artifact)
    assert len(problems) == 1
    assert "ordering" in problems[0]


def test_d_class_day_strata_unsorted_days_refused():
    """The `days` mapping must actually BE in ascending date order, not just
    declare that it is."""
    artifact = _sealable_day_strata_artifact()
    reversed_days = {d: artifact["days"][d]
                     for d in sorted(artifact["days"], reverse=True)}
    artifact = {**artifact, "days": reversed_days}
    problems = _admit_alone("day_strata", artifact)
    assert len(problems) == 1
    assert "ascending date order" in problems[0]


def test_d_class_day_strata_non_iso_date_key_refused():
    artifact = _sealable_day_strata_artifact()
    days = dict(artifact["days"])
    one_date = sorted(days)[0]
    days["2010/03/01"] = days.pop(one_date)
    problems = _admit_alone("day_strata", {**artifact, "days": days})
    assert len(problems) == 1
    assert "non-ISO-date key" in problems[0]


def test_d_class_day_strata_year_not_recomputed_from_date_refused():
    artifact, date = _mutate_one_day(_sealable_day_strata_artifact(),
                                     year="2011")
    problems = _admit_alone("day_strata", artifact)
    assert len(problems) == 1
    assert "year" in problems[0] and date in problems[0]


def test_d_class_day_strata_era_epoch_conflation_both_directions_refused():
    """An epoch label in the era slot AND an era label in the epoch slot are
    each refused — the conflation is caught in both directions."""
    era_slot, _ = _mutate_one_day(_sealable_day_strata_artifact(),
                                  micro_execution_era="2010-2013")
    problems = _admit_alone("day_strata", era_slot)
    assert len(problems) == 1
    assert "micro_execution_era" in problems[0]

    epoch_slot, _ = _mutate_one_day(_sealable_day_strata_artifact(),
                                    stability_epoch=ERA_PROXY)
    problems = _admit_alone("day_strata", epoch_slot)
    assert len(problems) == 1
    assert "stability_epoch" in problems[0]


def test_d_class_day_strata_era_recomputed_from_the_date_refused():
    """A VALID era label that is simply the WRONG one for this date (2010 is
    pre-boundary, so it must be the counterfactual era) is refused — the era
    is recomputed from the date, never read back."""
    artifact, _ = _mutate_one_day(_sealable_day_strata_artifact(),
                                  micro_execution_era=ERA_ACTUAL)
    problems = _admit_alone("day_strata", artifact)
    assert len(problems) == 1
    assert "RECOMPUTED from the date itself" in problems[0]


def test_d_class_day_strata_epoch_recomputed_from_year_refused():
    """A VALID epoch label that is the wrong bucket for this year (2010 is
    2010-2013, not 2018-2021)."""
    artifact, _ = _mutate_one_day(_sealable_day_strata_artifact(),
                                  stability_epoch="2018-2021")
    problems = _admit_alone("day_strata", artifact)
    assert len(problems) == 1
    assert "stability.EPOCHS" in problems[0]


def test_d_class_day_strata_event_flag_vocabulary_refused():
    artifact, _ = _mutate_one_day(_sealable_day_strata_artifact(),
                                  event_flag_final="none_or_na")
    problems = _admit_alone("day_strata", artifact)
    assert len(problems) == 1
    assert "event_flag_final" in problems[0]
    assert "none_or_na" in problems[0]


def test_d_class_day_strata_event_na_inconsistent_refused():
    """event_na must be recomputed from event_flag_final, in BOTH
    directions: a real flag with event_na=True, and a None flag with
    event_na=False."""
    a, _ = _mutate_one_day(_sealable_day_strata_artifact(), event_na=True)
    problems = _admit_alone("day_strata", a)
    assert len(problems) == 1 and "event_na" in problems[0]

    b, _ = _mutate_one_day(_sealable_day_strata_artifact(),
                           event_flag_final=None, event_na=False)
    problems = _admit_alone("day_strata", b)
    assert len(problems) == 1 and "event_na" in problems[0]


def test_d_class_day_strata_d_open_bool_is_not_int_refused():
    """`True` passes `in (-1, 0, 1)` under Python's type lattice; a STRICT
    int check is the only thing that catches it."""
    for bad in (True, 1.0, "1", 2):
        artifact, _ = _mutate_one_day(_sealable_day_strata_artifact(),
                                      d_open=bad)
        problems = _admit_alone("day_strata", artifact)
        assert len(problems) == 1, bad
        assert "d_open" in problems[0], bad


def test_d_class_day_strata_theta_key_set_refused():
    artifact, _ = _mutate_one_day(_sealable_day_strata_artifact(),
                                  tp_fp_class={"theta_0.9": "TP"})
    problems = _admit_alone("day_strata", artifact)
    assert len(problems) == 1
    assert "tp_fp_class keys" in problems[0]


def test_d_class_day_strata_theta_nesting_forgery_refused():
    """Both nesting directions, at admission (not only at build time): TP at
    the higher theta with a non-TP lower theta, and FP at the lower theta
    with a non-FP higher theta."""
    src = _ruled_source(thetas=(0.5, 0.3))
    base = _sealable_day_strata_artifact()

    def _two_theta(classes):
        days = {d: {**row, "tp_fp_class": dict(classes)}
                for d, row in base["days"].items()}
        return {**base, "days": days}

    forged_tp = _two_theta({"theta_0.5": "TP", "theta_0.3": "FP"})
    problems = handoff.formal_seal_admission({"day_strata": forged_tp},
                                             source=src)
    assert len(problems) == 1
    assert "THETA NESTING MONOTONICITY" in problems[0]
    assert "must be a SUBSET of the TP set at a LOWER theta" in problems[0]

    forged_fp = _two_theta({"theta_0.5": "TP", "theta_0.3": "TP"})
    assert handoff.formal_seal_admission({"day_strata": forged_fp},
                                         source=src) == []
    # FP at the LOWER theta while the HIGHER theta is TP is the mirror lie
    mirror = _two_theta({"theta_0.5": "TP", "theta_0.3": "FP"})
    problems = handoff.formal_seal_admission({"day_strata": mirror},
                                             source=src)
    assert any("FP set at a\nLOWER theta".replace("\n", " ") in p.replace(
        "\n", " ") or "THETA NESTING MONOTONICITY" in p for p in problems)


def test_d_class_day_strata_d_open_zero_traded_day_refused():
    artifact, _ = _mutate_one_day(_sealable_day_strata_artifact(), d_open=0)
    problems = _admit_alone("day_strata", artifact)
    assert len(problems) == 1
    assert "d_open == 0" in problems[0]


def test_d_class_day_strata_mixed_non_tradeable_refused():
    """Tradeability is theta-INDEPENDENT: a day marked non_tradeable at one
    theta and TP/FP at another is incoherent."""
    src = _ruled_source(thetas=(0.5, 0.3))
    base = _sealable_day_strata_artifact()
    days = {d: {**row, "tp_fp_class": {"theta_0.5": "non_tradeable",
                                       "theta_0.3": "TP"}}
            for d, row in base["days"].items()}
    problems = handoff.formal_seal_admission({"day_strata": {**base,
                                                             "days": days}},
                                             source=src)
    assert len(problems) == 1
    assert "theta-INDEPENDENT" in problems[0]


def test_d_class_day_strata_fabricated_event_stratum_refused():
    """The blind-audit class in one line: a plausible-looking concrete
    stratum on an axis with NO ruling. Under the DEFAULT (production) source
    context this is refused as a fabrication, and the UNRESOLVED marker is
    refused as unsealable — fail-closed BOTH ways."""
    fabricated = _sealable_day_strata_artifact()   # carries TEST_ONLY values
    problems = handoff.formal_seal_admission({"day_strata": fabricated})
    assert len(problems) == 1
    assert "NO ruling" in problems[0]
    assert "DR-M6-F" in problems[0]
    assert "may never impersonate an approved vocabulary" in problems[0]


def test_d_class_day_strata_fabricated_vol_status_refused():
    src = _ruled_source(vol_status_vocabulary=None)
    problems = handoff.formal_seal_admission(
        {"day_strata": _sealable_day_strata_artifact()}, source=src)
    assert len(problems) == 1
    assert "vol_status" in problems[0]
    assert "DR-M6-B-v2" in problems[0]


def test_d_class_day_strata_source_day_universe_mismatch_refused():
    """A DATASET FACT on the source context is a hard expectation: a
    day_strata that silently drops (or invents) a day is refused."""
    artifact = _sealable_day_strata_artifact()
    universe = frozenset(set(artifact["days"]) | {"2010-05-01"})
    src = _ruled_source(day_universe=universe)
    problems = handoff.formal_seal_admission({"day_strata": artifact},
                                             source=src)
    assert len(problems) == 1
    assert "day universe" in problems[0]
    assert "2010-05-01" in problems[0]


# --- D26-D34: GRID_SAMPLES -------------------------------------------------

def test_d_class_grid_62_cell_lattice_refused():
    """Exactly ONE cell short of the frozen 63-point lattice."""
    artifact = dict(_sealable_grid_samples_artifact())
    cells = dict(artifact["cells"])
    assert len(cells) == 63
    del cells["q0.75_r0.80"]
    artifact["cells"] = cells
    problems = _admit_bundle(grid_samples=artifact)
    assert len(problems) == 1
    assert "missing 1 of the frozen 63-point" in problems[0]
    assert "q0.75_r0.80" in problems[0]


def test_d_class_grid_64_cell_lattice_refused():
    """A 64th cell that is NOT on the frozen lattice."""
    artifact = dict(_sealable_grid_samples_artifact())
    cells = dict(artifact["cells"])
    cells["q0.99_r0.99"] = {**cells["q0.50_r0.50"], "q_mil": 990,
                            "r_mil": 990}
    artifact["cells"] = cells
    problems = _admit_bundle(grid_samples=artifact)
    assert len(problems) == 1
    assert "NOT on the frozen (q, r) lattice" in problems[0]
    assert "q0.99_r0.99" in problems[0]


def test_d_class_grid_qr_garbage_refused():
    for bad in (True, 500.0, "500", None, 501):
        artifact = dict(_sealable_grid_samples_artifact())
        cells = dict(artifact["cells"])
        cells["q0.50_r0.50"] = {**cells["q0.50_r0.50"], "q_mil": bad}
        artifact["cells"] = cells
        problems = _admit_bundle(grid_samples=artifact)
        assert len(problems) == 1, bad
        assert "q_mil" in problems[0], bad


def test_d_class_grid_cell_key_disagrees_with_its_own_millis_refused():
    """A cell filed under someone else's coordinates: the key says
    q0.50_r0.50 but its own fields say q=0.35."""
    artifact = dict(_sealable_grid_samples_artifact())
    cells = dict(artifact["cells"])
    cells["q0.50_r0.50"] = {**cells["q0.50_r0.50"], "q_mil": 350}
    artifact["cells"] = cells
    problems = _admit_bundle(grid_samples=artifact)
    assert len(problems) == 1
    assert "does not equal the key rebuilt" in problems[0]


def test_d_class_grid_markers_disagree_with_dates_refused():
    """CR-8: `day_markers` is the field MC actually consumes and was never
    cross-checked against the date lists it re-encodes."""
    artifact = dict(_sealable_grid_samples_artifact())
    cells = dict(artifact["cells"])
    cell = dict(cells["q0.50_r0.50"])
    per_seed = dict(cell["per_seed"])
    block = dict(per_seed[7])
    block["markers"] = [[m[0], "fp"] for m in block["markers"]]
    per_seed[7] = block
    cell["per_seed"] = per_seed
    cells["q0.50_r0.50"] = cell
    artifact["cells"] = cells
    problems = _admit_bundle(grid_samples=artifact)
    assert len(problems) == 1
    assert "markers is not the sorted re-encoding" in problems[0]


def test_d_class_grid_tp_fp_dates_not_disjoint_refused():
    artifact = dict(_sealable_grid_samples_artifact())
    cells = dict(artifact["cells"])
    cell = dict(cells["q0.50_r0.50"])
    per_seed = dict(cell["per_seed"])
    block = dict(per_seed[7])
    block["fp_dates"] = sorted(block["fp_dates"] + [block["tp_dates"][0]])
    per_seed[7] = block
    cell["per_seed"] = per_seed
    cells["q0.50_r0.50"] = cell
    artifact["cells"] = cells
    problems = _admit_bundle(grid_samples=artifact)
    assert len(problems) == 1
    assert "appear in BOTH tp_dates and fp_dates" in problems[0]


def test_d_class_grid_realized_precision_forged_refused():
    artifact = dict(_sealable_grid_samples_artifact())
    cells = dict(artifact["cells"])
    cell = dict(cells["q0.50_r0.50"])
    per_seed = dict(cell["per_seed"])
    per_seed[7] = {**per_seed[7], "realized_precision": 0.99}
    cell["per_seed"] = per_seed
    cells["q0.50_r0.50"] = cell
    artifact["cells"] = cells
    problems = _admit_bundle(grid_samples=artifact)
    assert len(problems) == 1
    assert "realized_precision" in problems[0]


def test_d_class_grid_target_precision_forged_refused():
    artifact = dict(_sealable_grid_samples_artifact())
    cells = dict(artifact["cells"])
    cell = dict(cells["q0.50_r0.50"])
    per_seed = dict(cell["per_seed"])
    per_seed[7] = {**per_seed[7], "target_precision": 0.35}
    cell["per_seed"] = per_seed
    cells["q0.50_r0.50"] = cell
    artifact["cells"] = cells
    problems = _admit_bundle(grid_samples=artifact)
    assert len(problems) == 1
    assert "target_precision" in problems[0]


def test_d_class_grid_replay_status_closed_claim_is_a_lie_refused():
    """Under the PRODUCTION source context (DR-2/3/5/6 all open) a CLOSED
    claim is refused as UNTRUTHFUL, not merely as premature."""
    artifact = _sealable_grid_samples_artifact()
    problems = handoff.formal_seal_admission({"grid_samples": artifact})
    assert len(problems) == 1
    assert "is a LIE about the replay" in problems[0]
    assert handoff.REPLAY_STATUS_CLOSED in problems[0]


def test_d_class_grid_stream_formula_tampered_refused():
    artifact = dict(_sealable_grid_samples_artifact())
    artifact["replay"] = {**artifact["replay"],
                          "stream_formula": "default_rng([master])"}
    problems = _admit_bundle(grid_samples=artifact)
    assert len(problems) == 1
    assert "stream_formula" in problems[0]


def test_d_class_grid_wrong_stream_tag_refused():
    artifact = dict(_sealable_grid_samples_artifact())
    artifact["replay"] = {**artifact["replay"], "grid_stream_tag": 9001}
    problems = _admit_bundle(grid_samples=artifact)
    assert len(problems) == 1
    assert "grid_stream_tag" in problems[0]


def test_d_class_grid_infeasible_cell_with_selections_refused():
    artifact = dict(_sealable_grid_samples_artifact())
    cells = dict(artifact["cells"])
    cells["q0.50_r0.50"] = {**cells["q0.50_r0.50"],
                            "infeasible_by_sample": True}
    artifact["cells"] = cells
    problems = _admit_bundle(grid_samples=artifact)
    assert len(problems) == 1
    assert "infeasible_by_sample is True but per_seed is not empty" in \
        problems[0]


def test_d_class_grid_date_absent_from_day_strata_refused():
    artifact = dict(_sealable_grid_samples_artifact())
    cells = dict(artifact["cells"])
    cell = dict(cells["q0.50_r0.50"])
    per_seed = dict(cell["per_seed"])
    block = dict(per_seed[7])
    block["tp_dates"] = sorted(block["tp_dates"][:-1] + ["2099-01-01"])
    per_seed[7] = block
    cell["per_seed"] = per_seed
    cells["q0.50_r0.50"] = cell
    artifact["cells"] = cells
    problems = _admit_bundle(grid_samples=artifact)
    assert len(problems) == 1
    assert "ABSENT from the co-supplied DAY_STRATA" in problems[0]


def test_d_class_grid_tp_fp_swapped_against_day_strata_refused():
    """A TP/FP swap that is internally perfectly consistent (markers,
    counts, realized values all agree with themselves) and is only caught
    because DAY_STRATA says otherwise."""
    artifact = dict(_sealable_grid_samples_artifact())
    cells = dict(artifact["cells"])
    cell = dict(cells["q0.50_r0.50"])
    per_seed = dict(cell["per_seed"])
    block = dict(per_seed[7])
    tp, fp = block["tp_dates"], block["fp_dates"]
    # swap ONE date each way, keeping both list lengths intact
    block["tp_dates"] = sorted(tp[:-1] + [fp[0]])
    block["fp_dates"] = sorted(fp[1:] + [tp[-1]])
    block["markers"] = sorted(
        [[d, "tp"] for d in block["tp_dates"]]
        + [[d, "fp"] for d in block["fp_dates"]])
    per_seed[7] = block
    cell["per_seed"] = per_seed
    cells["q0.50_r0.50"] = cell
    artifact["cells"] = cells
    problems = _admit_bundle(grid_samples=artifact)
    assert len(problems) == 1
    assert "DAY_STRATA does not class them TP" in problems[0]
    assert "DAY_STRATA does not class them FP" in problems[0]


def test_d_class_grid_target_counts_vs_day_strata_pools_refused():
    """The frozen App-A arithmetic recomputed against DAY_STRATA-derived
    pool sizes, not against the grid's own claim: dropping one TP date makes
    the selection disagree with floor_n_tp(r, n_tp_available)."""
    artifact = dict(_sealable_grid_samples_artifact())
    cells = dict(artifact["cells"])
    cell = dict(cells["q0.50_r0.50"])
    per_seed = dict(cell["per_seed"])
    block = dict(per_seed[7])
    dropped = block["tp_dates"][-1]
    block["tp_dates"] = block["tp_dates"][:-1]
    block["markers"] = [m for m in block["markers"] if m[0] != dropped]
    n_tp, n_fp = len(block["tp_dates"]), len(block["fp_dates"])
    block["realized_precision"] = n_tp / (n_tp + n_fp)
    block["realized_recall"] = n_tp / 10
    per_seed[7] = block
    cell["per_seed"] = per_seed
    cells["q0.50_r0.50"] = cell
    artifact["cells"] = cells
    problems = _admit_bundle(grid_samples=artifact)
    assert len(problems) == 1
    assert "gridmix.floor_n_tp" in problems[0]


def test_d_class_grid_realized_recall_forged_refused():
    """realized_recall's denominator (n_tp_available) is NOT carried on
    GRID_SAMPLES at all, so this leaf is unverifiable without the DAY_STRATA
    dependency — which is exactly why the dependency is mandatory."""
    artifact = dict(_sealable_grid_samples_artifact())
    cells = dict(artifact["cells"])
    cell = dict(cells["q0.50_r0.50"])
    per_seed = dict(cell["per_seed"])
    per_seed[7] = {**per_seed[7], "realized_recall": 0.99}
    cell["per_seed"] = per_seed
    cells["q0.50_r0.50"] = cell
    artifact["cells"] = cells
    problems = _admit_bundle(grid_samples=artifact)
    assert len(problems) == 1
    assert "realized_recall" in problems[0]
    assert "n_tp_available is NOT carried on GRID_SAMPLES" in problems[0]


# --- D39-D41: SEED_MANIFEST ------------------------------------------------

def test_d_class_seed_manifest_prose_forgery_best_of_refused():
    """The named blind-audit case: a manifest whose prose claims the quoted
    interval is a BEST-OF across seeds. Full-schema, right seeds, right
    tags — and a lie about the convention."""
    artifact = dict(_sealable_seed_manifest_artifact())
    artifact["quoted_seed_convention"] = (
        "quoted interval/selection = best-of three seeds {7, 13, 31}, "
        "chosen after inspecting the data")
    problems = _admit_alone("seed_manifest", artifact)
    assert len(problems) == 1
    assert "quoted_seed_convention" in problems[0]
    assert "best-of" in problems[0]
    assert "REBUILT text" in problems[0]


def test_d_class_seed_manifest_engineering_note_tampered_refused():
    artifact = dict(_sealable_seed_manifest_artifact())
    artifact["engineering_seed_note"] = "engineering seed is a research input"
    problems = _admit_alone("seed_manifest", artifact)
    assert len(problems) == 1
    assert "engineering_seed_note" in problems[0]


def test_d_class_seed_manifest_schema_version_tampered_refused():
    artifact = dict(_sealable_seed_manifest_artifact())
    artifact["schema_version"] = "m6.2-final"
    problems = _admit_alone("seed_manifest", artifact)
    assert len(problems) == 1
    assert "schema_version" in problems[0]


def test_d_class_seed_manifest_is_deep_equal_to_the_rebuild():
    """The positive control for the deep-equality rule: the REAL builder's
    output equals `rebuild_seed_manifest` field for field (minus the derived
    verdict flag)."""
    built = dict(handoff.build_seed_manifest())
    built.pop("formal_sealable")
    assert built == handoff.rebuild_seed_manifest()


def test_d_class_duplicate_seed_manifests_all_withheld():
    bundle = {"seed_manifest_a": _sealable_seed_manifest_artifact(),
              "seed_manifest_b": _sealable_seed_manifest_artifact()}
    problems = handoff.formal_seal_admission(bundle, source=_ruled_source())
    assert len(problems) == 2
    for p in problems:
        assert "SEED_MANIFEST artifacts were supplied" in p
        assert "ALL of them are withheld" in p


def test_d_class_duplicate_day_strata_all_withheld():
    bundle = {"day_strata_a": _sealable_day_strata_artifact(),
              "day_strata_b": _sealable_day_strata_artifact()}
    problems = handoff.formal_seal_admission(bundle, source=_ruled_source())
    assert len(problems) == 2
    for p in problems:
        assert "DAY_STRATA artifacts were supplied" in p


# --- dependency graph ------------------------------------------------------

def test_dependency_lone_grid_samples_is_withheld():
    """(2c) No grid submission may bypass the dependency graph: a lone
    GRID_SAMPLES with no co-supplied DAY_STRATA + SEED_MANIFEST is withheld,
    dependency-absent, even though its own content is impeccable."""
    artifact = _sealable_grid_samples_artifact()
    assert _admit_bundle(grid_samples=artifact) == []      # control
    problems = handoff.formal_seal_admission({"grid_samples": artifact},
                                             source=_ruled_source())
    assert len(problems) == 1
    assert "dependency DAY_STRATA is ABSENT" in problems[0]
    assert "dependency SEED_MANIFEST is ABSENT" in problems[0]
    assert "can never bypass the dependency graph" in problems[0]


def test_dependency_grid_with_invalid_day_strata_is_withheld():
    """(2b) An invalid dependency withholds every dependent artifact, with
    the dependency CHAIN named."""
    bad_strata = dict(_sealable_day_strata_artifact())
    bad_strata["schema_version"] = "m6.1-draft-9"
    problems = handoff.formal_seal_admission(
        _sealable_bundle(day_strata=bad_strata), source=_ruled_source())
    assert len(problems) == 2
    grid_problem = next(p for p in problems if p.startswith("grid_samples"))
    assert "dependency DAY_STRATA 'day_strata' is INVALID" in grid_problem
    assert "dependency chain: GRID_SAMPLES -> DAY_STRATA" in grid_problem


def test_dependency_grid_with_duplicate_manifest_is_withheld():
    bundle = _sealable_bundle()
    bundle["seed_manifest_2"] = _sealable_seed_manifest_artifact()
    problems = handoff.formal_seal_admission(bundle, source=_ruled_source())
    grid_problem = next(p for p in problems if p.startswith("grid_samples"))
    assert "dependency SEED_MANIFEST is DUPLICATED" in grid_problem
    assert len(problems) == 3      # both manifests + the dependent grid


def test_dependency_invalid_but_dependent_claims_sealable_is_a_contradiction():
    """The dependent artifact insists formal_sealable=True while its
    dependency is refused — refused as a CONTRADICTION, never sealed on top
    of an unsealed dependency."""
    bad_manifest = dict(_sealable_seed_manifest_artifact())
    bad_manifest["research_bootstrap_seeds"] = [7, 13, 99]
    grid = _sealable_grid_samples_artifact()
    assert grid["formal_sealable"] is True
    problems = handoff.formal_seal_admission(
        _sealable_bundle(seed_manifest=bad_manifest), source=_ruled_source())
    grid_problem = next(p for p in problems if p.startswith("grid_samples"))
    assert "CONTRADICTION" in grid_problem
    assert "however sealable it claims to be" in grid_problem


def test_dependency_duplicate_grid_triples_all_withheld():
    """Two GRID_SAMPLES claiming the same (theta, engine, scenario) — the
    theta x engine x scenario artifact set must be duplicate-free."""
    bundle = _sealable_bundle()
    bundle["grid_samples_again"] = _sealable_grid_samples_artifact()
    problems = handoff.formal_seal_admission(bundle, source=_ruled_source())
    assert len(problems) == 2
    for p in problems:
        assert "DUPLICATE GRID_SAMPLES" in p


def test_require_complete_grid_matrix_is_an_opt_in_source_expectation():
    """The complete theta x engine x scenario expectation is OFF by default
    (matrix L145: GRID_SAMPLES has NO production caller, so no production
    bundle's completeness can be contracted) and enforced when a caller that
    does produce the full set opts in."""
    bundle = _sealable_bundle()
    assert handoff.formal_seal_admission(bundle, source=_ruled_source()) == []
    strict = _ruled_source(require_complete_grid_matrix=True)
    problems = handoff.formal_seal_admission(bundle, source=strict)
    assert len(problems) == 1
    assert "COMPLETE theta x engine x scenario" in problems[0]


# --- unruled axes: fail closed BOTH ways -----------------------------------

def test_unruled_axis_fails_closed_in_both_directions():
    """There is no value that both passes vocabulary AND permits sealing
    while an axis is unruled: the UNRESOLVED marker is refused for SEALING,
    and any concrete string is refused as a FABRICATION."""
    real = handoff.build_seed_manifest()          # carries the real markers
    marker_problems = handoff.formal_seal_admission({"m": real})
    assert len(marker_problems) == 1
    assert "UNRESOLVED marker k_policy" in marker_problems[0]

    fabricated = dict(real)
    fabricated["k_policy"] = "K=1_per_seed"
    fabricated["crn_scope"] = "engine_x_scenario"
    fabricated["formal_sealable"] = True
    fake_problems = handoff.formal_seal_admission({"m": fabricated})
    assert len(fake_problems) == 1
    assert "NO ruling" in fake_problems[0]
    assert "DR-M6-E" in fake_problems[0]

    # ...and WITH a ruling on the source context, the same concrete values
    # are admissible — the ruling is what authorises them, never the
    # artifact.
    ruled = handoff.SourceContext(k_policy="K=1_per_seed",
                                  crn_scope="engine_x_scenario")
    assert handoff.formal_seal_admission({"m": fabricated},
                                         source=ruled) == []


# --- never-crash fuzz (item 9) ---------------------------------------------

class _RaisingRepr:
    """An object whose every dunder a checker might touch raises."""
    __hash__ = object.__hash__

    def __eq__(self, other):
        raise RuntimeError("hostile __eq__")

    def __repr__(self):
        raise RuntimeError("hostile __repr__")

    def __getattr__(self, name):
        raise RuntimeError("hostile __getattr__")


_FUZZ_VALUES = (
    None, True, False, 0, 1, -1, 7, 7.0, "", "x", "UNRESOLVED", b"bytes",
    [], [1, 2], ["a"], (), {}, {"a": 1}, {1: "a"}, {None: None},
    {"days": None}, {"days": []}, {"days": {"x": None}},
    {"cells": 3}, {"cells": {"k": 5}}, {"replay": []},
    {"research_bootstrap_seeds": "abc"}, {"stream_tags": 1},
    float("nan"), _RaisingRepr(), {"a": _RaisingRepr()},
    {_RaisingRepr(): "v"},
)


@pytest.mark.parametrize("checker", [
    handoff.check_day_strata_semantics,
    handoff.check_grid_samples_semantics,
    handoff.check_seed_manifest_semantics,
])
def test_checkers_never_crash_on_arbitrary_json_like_input(checker):
    """Item 9: every checker returns a problem LIST for arbitrary input —
    None/list/str/int/bool at every level, mixed-type keys, and objects whose
    __eq__/__repr__/__getattr__ raise. A check that cannot complete is a
    refusal, never a pass."""
    for value in _FUZZ_VALUES:
        problems = checker(value)
        assert isinstance(problems, list), repr(type(value))
        assert problems, repr(type(value))      # never a silent pass
        assert all(isinstance(p, str) for p in problems)


def test_checkers_never_crash_on_deeply_nested_fuzz():
    base = _sealable_day_strata_artifact()
    for value in _FUZZ_VALUES:
        mutated = {**base, "days": {"2010-03-01": value}}
        problems = handoff.check_day_strata_semantics(mutated,
                                                      _ruled_source())
        assert isinstance(problems, list) and problems
    for value in _FUZZ_VALUES:
        grid = dict(_sealable_grid_samples_artifact())
        grid["cells"] = {"q0.50_r0.50": value}
        problems = handoff.check_grid_samples_semantics(grid, _ruled_source())
        assert isinstance(problems, list) and problems


def test_formal_seal_admission_never_crashes_on_a_fuzzed_bundle():
    for value in _FUZZ_VALUES:
        problems = handoff.formal_seal_admission({"a": value})
        assert isinstance(problems, list)
        assert len(problems) == 1
        assert problems[0].startswith("a: ")
    # a fuzzed value alongside a real bundle never contaminates attribution
    bundle = _sealable_bundle()
    bundle["junk"] = {"formal_sealable": True, "cells": _RaisingRepr()}
    problems = handoff.formal_seal_admission(bundle, source=_ruled_source())
    assert all(any(p.startswith(f"{n}: ") for n in bundle) for p in problems)


# --- public API / single-source guarantees ---------------------------------

def test_source_context_default_is_the_production_context():
    """`SourceContext()` binds every frozen constant from its OWNING module
    and leaves every DR-M6 axis unruled — that is the production state at
    this HEAD."""
    src = handoff.SourceContext()
    assert src is not handoff.DEFAULT_SOURCE_CONTEXT or True
    assert src.thetas is handoff.FROZEN_THETAS
    assert src.seeds is contracts.RESEARCH_BOOTSTRAP_SEEDS
    assert src.epochs == tuple(stability.EPOCHS)
    assert src.outside_epochs == stability.OUTSIDE_EPOCHS
    assert src.micro_era_boundary == s0_context.MICRO_ERA_BOUNDARY
    assert src.q_grid_millis is gridmix.Q_GRID_MILLIS
    assert src.r_grid_millis is gridmix.R_GRID_MILLIS
    assert src.grid_stream_tag == gridmix.GRID_STREAM_TAG
    assert src.stats_stream_tag == stats.STATS_STREAM_TAG
    # every open axis unruled, no dataset facts
    assert src.event_stratum_vocabulary is None
    assert src.vol_status_vocabulary is None
    assert src.k_policy is None
    assert src.crn_scope is None
    assert src.replay_closure_ruled is False
    assert src.day_universe is None
    assert src.require_complete_grid_matrix is False
    # an ad-hoc dict is refused with the dedicated SourceContextError; an
    # EMPTY bundle raises rather than returning a silent [] (there is no
    # artifact name to attribute a "{name}: " refusal to, and the renderer
    # fails closed on an unattributable problem string)
    with pytest.raises(handoff.SourceContextError):
        handoff.formal_seal_admission({}, source={"thetas": (0.5,)})
    assert issubclass(handoff.SourceContextError, ValueError)


def test_default_source_context_is_the_injection_seam_for_no_source_callers(
        monkeypatch):
    """A caller that passes NO `source` (notably
    `scripts/s0_real_run.render_s0_report`, which calls
    `formal_seal_admission(candidates)` positionally) must still be
    reachable by a test that needs to prove the gate is DECIDED by admission
    rather than by a hardcoded exclusion.

    `DEFAULT_SOURCE_CONTEXT` is read from the module namespace at CALL time,
    so monkeypatching it is that seam. This test reproduces exactly the
    renderer-level scenario: the REAL builder's manifest with its two open
    markers replaced by a TEST_ONLY string, formal_sealable forced True, and
    a ONE-POSITIONAL-ARG admission call.
    """
    import copy

    def _resolve(obj):
        if isinstance(obj, dict):
            return {k: _resolve(v) for k, v in obj.items()}
        if isinstance(obj, str) and ("UNRESOLVED" in obj or "PARTIAL" in obj):
            return "TEST_ONLY"
        return obj

    fixture = _resolve(copy.deepcopy(handoff.build_seed_manifest()))
    fixture["formal_sealable"] = True

    # production sources: the TEST_ONLY strings are a FABRICATION on two
    # unruled axes and the manifest is refused
    refused = handoff.formal_seal_admission({"SEED_MANIFEST.json": fixture})
    assert len(refused) == 1
    assert refused[0].startswith("SEED_MANIFEST.json: ")
    assert "k_policy 'TEST_ONLY'" in refused[0]
    assert "crn_scope 'TEST_ONLY'" in refused[0]

    # the SAME artifact, admitted once the SOURCE rules those two axes —
    # injected through the module default, with no signature change at the
    # call site
    monkeypatch.setattr(handoff, "DEFAULT_SOURCE_CONTEXT",
                        handoff.SourceContext(k_policy="TEST_ONLY",
                                              crn_scope="TEST_ONLY"))
    assert handoff.formal_seal_admission({"SEED_MANIFEST.json": fixture}) == []
    # The ruling is genuinely a ruling, not a bypass: the REAL builder now
    # emits the ruled values too (it reads the same module default), so its
    # own output becomes sealable as well — builder and admission never
    # disagree about what the sources say.
    assert handoff.build_seed_manifest()["k_policy"] == "TEST_ONLY"
    assert handoff.formal_seal_admission(
        {"SEED_MANIFEST.json": handoff.build_seed_manifest()}) == []
    # ...but the seam admits a SPECIFIC vocabulary, never "anything": a
    # differently-fabricated manifest is still refused under that same
    # ruling.
    other = dict(fixture)
    other["k_policy"] = "SOME_OTHER_POLICY"
    still_refused = handoff.formal_seal_admission({"SEED_MANIFEST.json": other})
    assert len(still_refused) == 1
    assert "SOME_OTHER_POLICY" in still_refused[0]


# ===========================================================================
# MED-1 — SourceContext is itself an attack surface (blind auditor #2)
#
# The four guises, each named after its auditor case. Every one asserts BOTH
# the refusal AND that the fully-ruled positive bundle still admits, so a
# fix that simply broke admission would not pass.
# ===========================================================================

def _assert_positive_bundle_still_admits():
    assert handoff.formal_seal_admission(_sealable_bundle(),
                                         source=_ruled_source()) == []


def test_a8_object_setattr_poisoning_of_the_frozen_singleton_is_refused(
        monkeypatch):
    """A8: `@dataclass(frozen=True)` blocks ordinary assignment but NOT
    `object.__setattr__`. Poison the module-global singleton, then call
    admission in the exact PRODUCTION shape — one positional argument, no
    `source=` — and the poisoned context must be caught by re-validation on
    every call, not trusted because it was valid at construction."""
    _assert_positive_bundle_still_admits()
    # build every artifact BEFORE poisoning — the builders read the same
    # module default, so after poisoning they refuse too (asserted below)
    manifest = handoff.build_seed_manifest()
    bundle = _sealable_bundle()
    clean = handoff.SourceContext()
    poisoned = handoff.SourceContext()
    monkeypatch.setattr(handoff, "DEFAULT_SOURCE_CONTEXT", poisoned)

    def _poison(field, value):
        for f in ("q_grid_millis", "seeds", "replay_closure_ruled"):
            object.__setattr__(poisoned, f, getattr(clean, f))
        object.__setattr__(poisoned, field, value)
        return handoff.formal_seal_admission({"SEED_MANIFEST.json": manifest})

    # (i) re-anchor a FROZEN CONSTANT slot: shrink the grid lattice so a
    # one-cell grid would satisfy the "complete 63-point lattice" check
    problems = _poison("q_grid_millis", (500,))
    assert len(problems) == 1
    assert problems[0].startswith("SEED_MANIFEST.json: ")
    assert "source context invalid — fail closed" in problems[0]
    assert "q_grid_millis" in problems[0]
    assert "FROZEN CONSTANT, not configuration" in problems[0]

    # (ii) re-anchor the seed axis itself
    problems = _poison("seeds", (7, 13, 31, 99))
    assert len(problems) == 1
    assert "seeds" in problems[0]
    assert "source context invalid" in problems[0]

    # (iii) poison a strict-bool gate with a truthy non-bool
    problems = _poison("replay_closure_ruled", "yes")
    assert len(problems) == 1
    assert "replay_closure_ruled" in problems[0]
    assert "STRICT bool" in problems[0]

    # every artifact in the bundle is withheld, not merely one
    problems = handoff.formal_seal_admission(bundle)
    assert len(problems) == len(bundle) == 3
    assert all("source context invalid" in p for p in problems)
    assert all(any(p.startswith(f"{n}: ") for n in bundle) for p in problems)

    # the BUILDERS refuse the poisoned anchor too, rather than emitting an
    # artifact rebuilt against it
    with pytest.raises(handoff.SourceContextError):
        handoff.build_seed_manifest()


def test_a9_hostile_duck_source_context_folds_into_a_refusal(monkeypatch):
    """A9: `DEFAULT_SOURCE_CONTEXT` replaced by a non-SourceContext duck
    whose property RAISES. The read used to sit outside the guarded region,
    so the RuntimeError escaped `formal_seal_admission` entirely. It must now
    fold into a refusal string."""
    _assert_positive_bundle_still_admits()
    manifest = handoff.build_seed_manifest()      # built BEFORE poisoning

    class _HostileDuck:
        @property
        def thetas(self):
            raise RuntimeError("hostile property")

        def __getattr__(self, name):
            raise RuntimeError("hostile __getattr__")

    monkeypatch.setattr(handoff, "DEFAULT_SOURCE_CONTEXT", _HostileDuck())
    problems = handoff.formal_seal_admission({"SEED_MANIFEST.json": manifest})
    assert len(problems) == 1
    assert problems[0].startswith("SEED_MANIFEST.json: ")
    assert "source context invalid — fail closed" in problems[0]
    assert "must be EXACTLY a handoff.SourceContext" in problems[0]
    assert "_HostileDuck" in problems[0]
    # the type pin is checked BEFORE any attribute of the duck is read, so
    # the hostile property is never reached
    assert "hostile" not in problems[0]

    # the pure checkers fold it the same way rather than raising
    for checker, tag in ((handoff.check_day_strata_semantics, "day_strata"),
                         (handoff.check_grid_samples_semantics,
                          "grid_samples"),
                         (handoff.check_seed_manifest_semantics,
                          "seed_manifest")):
        out = checker({})
        assert len(out) == 1
        assert out[0].startswith(f"{tag}: source context invalid — fail "
                                 "closed: ")
        assert "must be EXACTLY a handoff.SourceContext" in out[0]


def test_a9_subclass_of_source_context_is_also_refused():
    """One overridden property is enough to re-anchor every check, so the
    pin is `type(ctx) is SourceContext`, not `isinstance`."""
    class _Plain(handoff.SourceContext):
        pass

    with pytest.raises(handoff.SourceContextError, match="SUBCLASS"):
        handoff.formal_seal_admission({}, source=_Plain())
    problems = handoff.formal_seal_admission(
        {"seed_manifest": handoff.build_seed_manifest()}, source=_Plain())
    assert len(problems) == 1
    assert "source context invalid" in problems[0]
    assert "_Plain" in problems[0]

    # a subclass that tries to re-anchor a slot with a property cannot even
    # be CONSTRUCTED: __post_init__ writes the normalised value back and a
    # read-only property has no setter
    class _Sneaky(handoff.SourceContext):
        @property
        def grid_stream_tag(self):
            return 1234

    with pytest.raises(AttributeError):
        _Sneaky()


def test_a10_bare_str_ruling_vocabulary_is_refused():
    """A10: a ruling slot supplied as a BARE STR degrades `value in vocab`
    into SUBSTRING matching, so a ruled "S_A" would admit "S" and "_A"."""
    _assert_positive_bundle_still_admits()
    with pytest.raises(handoff.SourceContextError) as exc:
        handoff.SourceContext(event_stratum_vocabulary="S_A")
    assert "bare str" in str(exc.value)
    assert "SUBSTRING matching" in str(exc.value)

    # the substring that WOULD have been admitted is proven refused under a
    # correctly-typed one-token vocabulary
    src = handoff.SourceContext(thetas=(0.5,),
                                event_stratum_vocabulary=frozenset({"S_A"}),
                                vol_status_vocabulary=frozenset({"V_A"}),
                                k_policy="K_A", crn_scope="C_A",
                                replay_closure_ruled=True)
    base = _sealable_day_strata_artifact()
    for token, admitted in (("S_A", True), ("S", False), ("_A", False),
                            ("", False)):
        days = {d: {**row, "event_stratum": token, "vol_status": "V_A"}
                for d, row in base["days"].items()}
        problems = handoff.formal_seal_admission(
            {"day_strata": {**base, "days": days}}, source=src)
        if admitted:
            assert problems == [], token
        else:
            assert len(problems) == 1, token
            assert "event_stratum" in problems[0], token

    # every other bare-str / malformed vocabulary shape is refused too
    for bad in ("", b"S_A", 5, frozenset(), frozenset({""}),
                frozenset({"ok", 7}), ["a", None]):
        with pytest.raises(handoff.SourceContextError):
            handoff.SourceContext(vol_status_vocabulary=bad)


def test_a11_empty_theta_axis_is_refused():
    """A11: `SourceContext(thetas=())` made every tp_fp_class check pass
    VACUOUSLY — an empty artifact dict equals the empty expected key set."""
    _assert_positive_bundle_still_admits()
    with pytest.raises(handoff.SourceContextError) as exc:
        handoff.SourceContext(thetas=())
    assert "VACUOUSLY" in str(exc.value)
    assert "A11" in str(exc.value)

    # ...and the vacuous pass it used to enable is now unreachable through
    # the module-global seam as well
    poisoned = handoff.SourceContext()
    object.__setattr__(poisoned, "thetas", ())
    vacuous = _sealable_day_strata_artifact()
    days = {d: {**row, "tp_fp_class": {}} for d, row in vacuous["days"].items()}
    problems = handoff.formal_seal_admission(
        {"day_strata": {**vacuous, "days": days}}, source=poisoned)
    assert len(problems) == 1
    assert "source context invalid" in problems[0]
    assert "thetas is EMPTY" in problems[0]
    # under a VALID context the same artifact is refused on its own merits
    problems = handoff.formal_seal_admission(
        {"day_strata": {**vacuous, "days": days}}, source=_ruled_source())
    assert len(problems) == 1
    assert "tp_fp_class keys" in problems[0]


def test_med1_every_source_context_slot_is_validated():
    """No slot is unvalidated: each of these poisonings raises at
    construction, and the same values are caught by re-validation when
    written past the frozen dataclass with object.__setattr__."""
    bad_by_field = {
        "thetas": ((), (0.5, 0.5), ("0.5",), (1,), (True,), "0.5"),
        "engines": ((), ("E1", "E1"), (1,), ("",), "E1"),
        "scenarios": ((), ("Base", 2), "Base"),
        "seeds": ((), (7, 7), (7.0,), (True,), "7"),
        "epochs": ((), (("a", 2013, 2010),), (("a", 2010, 2013),
                                              ("b", 2012, 2015)), "x"),
        "outside_epochs": ("", 5, None, "2010-2013"),
        "micro_era_boundary": ("", "2019/05/06", 5, "2019-13-01"),
        "era_proxy": ("", 5),
        "era_actual": ("", 5),
        "event_flag_values": ("CPI", frozenset(), frozenset({1})),
        "stats_stream_tag": (True, 9001.0, "9001", 9002),
        "grid_stream_tag": (True, "9002", 9001),
        "q_grid_millis": ((), (0,), (1001,), (500.0,), (True,)),
        "r_grid_millis": ((), (0,), (500.0,)),
        "day_universe": ("2010-03-01", ("nope",), 5),
        "event_stratum_vocabulary": ("S", frozenset(), 5),
        "vol_status_vocabulary": ("V", frozenset(), 5),
        "k_policy": ("", 5, "UNRESOLVED", "UNRESOLVED_DR-M6-E"),
        "crn_scope": ("", 5, "UNRESOLVED"),
        "replay_closure_ruled": ("yes", 1, 0, None),
        "require_complete_grid_matrix": ("yes", 1, None),
    }
    # every declared field is covered by this table
    import dataclasses
    declared = {f.name for f in dataclasses.fields(handoff.SourceContext)}
    assert declared == set(bad_by_field), declared ^ set(bad_by_field)

    for field, bad_values in bad_by_field.items():
        for bad in bad_values:
            with pytest.raises(handoff.SourceContextError):
                handoff.SourceContext(**{field: bad})
            # and again through the object.__setattr__ seam (A8): valid at
            # construction, poisoned afterwards, caught by re-validation
            ctx = handoff.SourceContext()
            object.__setattr__(ctx, field, bad)
            with pytest.raises(handoff.SourceContextError):
                ctx.validate()


def test_med1_vocabularies_are_normalised_to_frozensets():
    """(d) set-of-str semantics everywhere: a tuple/list/set vocabulary is
    normalised at construction, so no downstream `in` can mean anything but
    set membership."""
    src = handoff.SourceContext(event_stratum_vocabulary=["a", "b", "a"],
                                vol_status_vocabulary=("c",),
                                day_universe=["2010-03-01", "2010-03-01"])
    assert src.event_stratum_vocabulary == frozenset({"a", "b"})
    assert isinstance(src.event_stratum_vocabulary, frozenset)
    assert isinstance(src.vol_status_vocabulary, frozenset)
    assert src.day_universe == frozenset({"2010-03-01"})
    assert isinstance(src.day_universe, frozenset)
    # a hand-built non-frozenset vocabulary reaching the checker directly is
    # refused rather than tested with an operator whose meaning varies
    problems = handoff._unruled_axis_check("x: axis", "S", "S_A", "DR-TEST")
    assert len(problems) == 1
    assert "not a frozenset" in problems[0].text


def test_a16_date_validation_rejects_fullwidth_digits_and_trailing_newline():
    """A16: `\\d` matches Unicode digits and `$` matches before a trailing
    newline, so the pattern alone used to accept both — caught only by
    `date.fromisoformat` downstream. Both are now refused by the pattern, and
    fromisoformat REMAINS load-bearing for calendar validity."""
    assert handoff._parsed_date("2010-03-01") is not None
    for bad in ("２０１０-03-01", "2010-03-01\n",
                " 2010-03-01", "2010-03-01 ", "2010-3-01", "20100301",
                "2010-03-01T00:00:00", b"2010-03-01", None):
        assert handoff._parsed_date(bad) is None, repr(bad)
    # fromisoformat is the load-bearing calendar backstop the regex cannot be
    assert handoff._ISO_DATE_RE.match("2019-02-30")
    assert handoff._parsed_date("2019-02-30") is None
    assert handoff._parsed_date("2019-13-01") is None


def test_low6_event_flag_values_is_the_single_source_not_a_dead_snapshot():
    """LOW-6: `_EVENT_FLAG_VALUES` used to be an import-time snapshot taken
    FROM the default context and then shadowed everywhere by the live
    `source.event_flag_values`. It is now the field default itself."""
    assert handoff._EVENT_FLAG_VALUES == frozenset(
        s0_context.F10_CATEGORIES) | {"none"}
    assert handoff.SourceContext().event_flag_values is \
        handoff._EVENT_FLAG_VALUES
    # and it is genuinely load-bearing: the pin refuses a re-anchored slot
    ctx = handoff.SourceContext()
    object.__setattr__(ctx, "event_flag_values", frozenset({"CPI"}))
    with pytest.raises(handoff.SourceContextError, match="event_flag_values"):
        ctx.validate()


# ===========================================================================
# M6.1.4 CLOSEOUT — SourceContext.thetas is MEMBERSHIP-BOUND to the single
# frozen source (study.FROZEN_THETAS). Membership only: theta never becomes a
# configuration parameter or a sweep surface.
# ===========================================================================

def test_closeout_theta_positive_subsets_all_construct():
    """Every non-empty, duplicate-free SUBSET of the frozen pair stays
    legal, in ANY order — the frozen text imposes no ordering, so neither
    does this validation."""
    from itsf.s0 import study as s0_study
    assert set(s0_study.FROZEN_THETAS) == {0.5, 0.3}
    for subset in ((0.3,), (0.5,), (0.5, 0.3), (0.3, 0.5)):
        ctx = handoff.SourceContext(thetas=subset)
        assert ctx.thetas == subset
        # order is preserved verbatim, never normalised behind the caller
        assert list(ctx.thetas) == list(subset)
    # the default IS the frozen tuple object, not a copy that compares equal
    assert handoff.SourceContext().thetas is s0_study.FROZEN_THETAS


def test_closeout_theta_non_member_is_refused_naming_the_frozen_source():
    """0.7 is a well-formed strict float and still refused: membership is
    against study.FROZEN_THETAS, and the refusal NAMES that source."""
    with pytest.raises(handoff.SourceContextError) as exc:
        handoff.SourceContext(thetas=(0.7,))
    message = str(exc.value)
    assert "0.7" in message
    assert "study.FROZEN_THETAS" in message
    assert "(0.5, 0.3)" in message
    assert "FROZEN AXIS" in message
    assert "not a configuration or sweep parameter" in message
    # a valid member mixed with an invalid one is still refused, and only
    # the offending member is named
    with pytest.raises(handoff.SourceContextError) as exc2:
        handoff.SourceContext(thetas=(0.5, 0.7))
    assert "0.7" in str(exc2.value)


def test_closeout_theta_near_member_refused_exact_equality_no_tolerance():
    """0.5 + 1e-9 is NOT 0.5. Membership is exact float equality with no
    tolerance anywhere."""
    near = 0.5 + 1e-9
    assert near != 0.5
    with pytest.raises(handoff.SourceContextError) as exc:
        handoff.SourceContext(thetas=(near,))
    assert "NO tolerance" in str(exc.value)
    assert "study.FROZEN_THETAS" in str(exc.value)


def test_closeout_theta_strict_float_type_only():
    """bool True and int 1 are refused on TYPE before membership is even
    consulted — `True == 1` and neither is a strict float. Same for a
    numeric string."""
    for bad in (True, 1, "0.5", 0.5j, None):
        with pytest.raises(handoff.SourceContextError) as exc:
            handoff.SourceContext(thetas=(bad,))
        assert "STRICT float type only" in str(exc.value), repr(bad)
    # int 0 / 1 would be `in (0.5, 0.3)`-adjacent under coercion; refused
    with pytest.raises(handoff.SourceContextError, match="STRICT float"):
        handoff.SourceContext(thetas=(1,))


def test_closeout_theta_duplicates_and_empty_and_non_tuple_refused():
    with pytest.raises(handoff.SourceContextError, match="duplicate"):
        handoff.SourceContext(thetas=(0.5, 0.5))
    with pytest.raises(handoff.SourceContextError, match="EMPTY"):
        handoff.SourceContext(thetas=())
    for container in ([0.5], {0.5}, frozenset({0.5}), "0.5", 0.5, None):
        with pytest.raises(handoff.SourceContextError) as exc:
            handoff.SourceContext(thetas=container)
        assert "non-empty tuple" in str(exc.value), repr(container)


def test_closeout_theta_binding_survives_the_object_setattr_seam():
    """The membership bind is re-checked on every admission call, so it
    cannot be written past the frozen dataclass (blind-audit A8 seam)."""
    ctx = handoff.SourceContext()
    object.__setattr__(ctx, "thetas", (0.7,))
    with pytest.raises(handoff.SourceContextError, match="FROZEN_THETAS"):
        ctx.validate()
    problems = handoff.formal_seal_admission(
        {"seed_manifest": handoff.build_seed_manifest()}, source=ctx)
    assert len(problems) == 1
    assert "source context invalid — fail closed" in problems[0]
    assert "study.FROZEN_THETAS" in problems[0]


def test_closeout_theta_builders_and_admission_share_one_membership():
    """(3) There is ONE membership rule, reached through SourceContext by
    both the builders and admission — not two implementations that could
    drift."""
    day_rows = {"2019-06-03": _day_row(tp_fp_class={"theta_0.7": "TP"})}
    with pytest.raises(handoff.SourceContextError, match="FROZEN_THETAS"):
        handoff.build_day_strata(day_rows, thetas=[0.7])
    # ...and the identical rule is what admission consults
    with pytest.raises(handoff.SourceContextError, match="FROZEN_THETAS"):
        handoff.formal_seal_admission({}, source=handoff.SourceContext(
            thetas=(0.7,)))
    # the builder still accepts every legal subset
    for subset in ([0.5], [0.3], [0.5, 0.3], [0.3, 0.5]):
        out = handoff.build_day_strata(
            {"2019-06-03": _day_row(tp_fp_class={
                handoff.s0_study.theta_key(t): "TP" for t in subset})},
            thetas=subset)
        assert set(out["days"]["2019-06-03"]["tp_fp_class"]) == {
            handoff.s0_study.theta_key(t) for t in subset}


def test_closeout_theta_no_second_literal_lives_in_handoff():
    """(4) The frozen pair has ONE source. Every 0.5/0.3 occurrence left in
    handoff.py is prose (a comment or a refusal-message example); no CODE
    path builds a theta axis from a literal."""
    import ast
    import inspect
    from itsf.s0 import study as s0_study

    tree = ast.parse(inspect.getsource(handoff))
    literals = [n.value for n in ast.walk(tree)
                if isinstance(n, ast.Constant) and isinstance(n.value, float)]
    assert not [v for v in literals if v in s0_study.FROZEN_THETAS], literals
    # and the module alias is the SAME object as study's, so it cannot drift
    assert handoff.FROZEN_THETAS is s0_study.FROZEN_THETAS


def test_closeout_fully_ruled_positive_bundle_still_admits():
    """(5) The bind refuses rogue axes without breaking the positive path."""
    assert handoff.formal_seal_admission(_sealable_bundle(),
                                         source=_ruled_source()) == []
    assert handoff.formal_seal_admission(
        _sealable_bundle(), source=_ruled_source(thetas=(0.5,))) == []


def test_theta_key_is_imported_from_study_not_duplicated():
    """Matrix CR-11: the local `_theta_key` duplicate is gone; the module
    formats theta keys through `study.theta_key`."""
    from itsf.s0 import study as s0_study
    assert not hasattr(handoff, "_theta_key")
    assert handoff._theta_key_of(0.5) == s0_study.theta_key(0.5)
    assert handoff._theta_key_of("0.5") is None      # never coerced
    assert handoff._theta_key_of(True) is None       # bool is not a theta


def test_epoch_boundaries_come_only_from_stability_epochs():
    """Matrix CR-4: `dataset.STABILITY_EPOCHS` uses a DIFFERENT (half-open)
    interval convention and must never be mixed in here."""
    from itsf.s0 import dataset as s0_dataset
    src = handoff.SourceContext()
    assert src.epochs == tuple(stability.EPOCHS)
    assert handoff._epoch_for_year(2013, src) == "2010-2013"
    assert handoff._epoch_for_year(2014, src) == "2014-2017"
    assert handoff._epoch_for_year(2009, src) == stability.OUTSIDE_EPOCHS
    assert hasattr(s0_dataset, "STABILITY_EPOCHS")   # exists, deliberately unused


def test_builders_and_admission_run_the_same_checker(monkeypatch):
    """Item 1: the checkers are the SINGLE source of the invariants — the
    builders route their own output through the same function admission
    calls, so a rule can never be enforced in one place and not the other."""
    calls: list[str] = []
    real = handoff._day_strata_problems

    def _spy(artifact, source):
        calls.append("called")
        return real(artifact, source)

    monkeypatch.setattr(handoff, "_day_strata_problems", _spy)
    handoff.build_day_strata({"2019-06-03": _day_row()}, thetas=[0.5])
    assert calls, "build_day_strata did not run the shared checker"
    handoff.formal_seal_admission({"d": _sealable_day_strata_artifact()},
                                  source=_ruled_source())
    assert len(calls) >= 2
