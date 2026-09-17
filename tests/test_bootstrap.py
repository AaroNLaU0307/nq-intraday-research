"""TASK 9 -- the sealed stationary block bootstrap. No real outcomes are resampled."""
from __future__ import annotations

import numpy as np
import pytest

from r1.bootstrap import (bootstrap_interval, per_seed_intervals, resample_means,
                          sensitivity_interval)
from r1.errors import R1Error

RNG = np.random.default_rng(12345)
SYNTH = RNG.normal(2.0, 10.0, size=120)      # fabricated, not an R1 outcome


def test_seed_reproducibility(contract):
    a = resample_means(SYNTH, 5, 500, seed=7)
    b = resample_means(SYNTH, 5, 500, seed=7)
    c = resample_means(SYNTH, 5, 500, seed=13)
    assert np.array_equal(a, b)
    assert not np.array_equal(a, c)


def test_interval_is_deterministic(contract):
    small = contract  # sealed resample count is used; keep the sample small
    a = bootstrap_interval(SYNTH, small, seeds=(7,))
    b = bootstrap_interval(SYNTH, small, seeds=(7,))
    assert (a.lower, a.upper, a.point) == (b.lower, b.upper, b.point)


def test_block_structure_produces_runs_of_consecutive_indices():
    """A stationary bootstrap must actually draw BLOCKS, not iid points."""
    values = np.arange(50, dtype=float)
    means = resample_means(values, block_events=10, resamples=200, seed=7)
    iid = resample_means(values, block_events=1, resamples=200, seed=7)
    # blocked resampling of a trending series has WIDER mean dispersion
    assert means.std() > iid.std()


def test_interval_brackets_the_point_estimate(contract):
    ci = bootstrap_interval(SYNTH, contract, seeds=(7,))
    assert ci.lower < ci.point < ci.upper
    assert ci.level == 0.95
    assert ci.method == "percentile"
    assert ci.half_width > 0


def test_sealed_grammar_is_used(contract):
    ci = bootstrap_interval(SYNTH, contract)
    assert ci.block_events == 5
    assert ci.resamples == 10_000
    assert ci.seeds == (7, 13, 31)


def test_sensitivity_is_block_ten_and_is_not_primary(contract):
    ci = sensitivity_interval(SYNTH, contract)
    assert ci.block_events == 10
    primary = bootstrap_interval(SYNTH, contract)
    assert primary.block_events == 5


def test_per_seed_intervals_are_reported_for_stability(contract):
    out = per_seed_intervals(SYNTH, contract)
    assert set(out) == {7, 13, 31}
    for seed, ci in out.items():
        assert ci.seeds == (seed,)


def test_degenerate_empty_sample_is_refused(contract):
    with pytest.raises(R1Error, match="empty"):
        bootstrap_interval(np.array([]), contract)


def test_one_event_sample_is_refused(contract):
    with pytest.raises(R1Error, match="single event"):
        bootstrap_interval(np.array([1.0]), contract)


def test_missing_data_is_refused(contract):
    with pytest.raises(R1Error, match="NaN"):
        bootstrap_interval(np.array([1.0, np.nan, 3.0]), contract)
    with pytest.raises(R1Error):
        bootstrap_interval(np.array([1.0, np.inf, 3.0]), contract)


def test_two_dimensional_input_is_refused(contract):
    with pytest.raises(R1Error, match="one-dimensional"):
        bootstrap_interval(np.ones((3, 3)), contract)


def test_block_length_must_be_at_least_one():
    with pytest.raises(R1Error, match="block length"):
        resample_means(SYNTH, block_events=0, resamples=10, seed=7)


def test_interval_decision_helpers(contract):
    ci = bootstrap_interval(SYNTH, contract, seeds=(7,))
    assert ci.clears(ci.lower - 1.0)
    assert not ci.clears(ci.upper + 1.0)
    assert ci.spans((ci.lower + ci.upper) / 2)
    huge = ci.upper + 10 * ci.half_width
    assert ci.excludes_below(huge)


def test_no_tuning_parameter_leaks_into_the_primary_call(contract):
    """Every knob is read off the sealed contract, not passed by a caller."""
    import inspect
    sig = inspect.signature(bootstrap_interval)
    assert set(sig.parameters) == {"values", "contract", "block_events", "seeds"}
    assert sig.parameters["block_events"].default is None
    assert sig.parameters["seeds"].default is None
