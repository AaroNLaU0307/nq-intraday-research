"""M11's fixed-world rule, and the guard that used to forbid it.

The interesting test in this file is the last one. Until 2026-08-24 the
repository carried `test_no_fixed_world_selection_rule_was_invented`,
asserting that NO selection rule existed anywhere. M11 ratified one. A
guard left asserting the old thing would keep passing while protecting
nothing -- the exact failure M11's own dependency list warned about.
"""
from __future__ import annotations

import math

import pytest

from itsf.mc import fixed_world as fw


def test_the_three_positions_are_the_ratified_ones():
    assert fw.FIXED_WORLD_QUANTILES == (0.05, 0.50, 0.95)
    assert fw.FIXED_WORLD_RULING == "M11_RATIFIED_2026-08-24"


def test_production_b_lands_on_the_50th_500th_and_950th():
    """B=1000, means strictly increasing with index, so the order statistic
    positions and the world indices coincide and the arithmetic is
    readable: 1-indexed 50/500/950 are 0-indexed 49/499/949."""
    means = [float(i) for i in range(1000)]
    assert fw.select_fixed_worlds(means) == (49, 499, 949)


def test_the_rule_orders_by_mean_not_by_world_index():
    """The whole point. World 0 is the best world here, so it must land in
    the HIGH slot -- a rule that read index order would return (0, ...)."""
    means = [100.0, -50.0, 0.0, 25.0, -10.0]
    low, mid, high = fw.select_fixed_worlds(means)
    assert means[low] < means[mid] < means[high]
    assert high == 0


def test_ties_resolve_to_the_lower_world_index():
    """Without this the rule is not total, and two runs over identical
    data could report different worlds."""
    means = [7.0] * 10
    assert fw.select_fixed_worlds(means) == (0, 4, 9)


def test_small_b_never_indexes_outside_the_set():
    for b in range(1, 12):
        picked = fw.select_fixed_worlds([float(i) for i in range(b)])
        assert len(picked) == 3
        for w in picked:
            assert 0 <= w < b, (b, picked)


def test_an_empty_world_set_is_refused_not_defaulted():
    with pytest.raises(fw.FixedWorldError) as ei:
        fw.select_fixed_worlds([])
    assert ei.value.code == "fixed_world_no_worlds"


def test_the_positions_are_ceil_one_indexed():
    """ceil, not floor and not round. At B=1000 floor(0.05*1000) is also
    50, so a coarse fixture cannot tell them apart; B=7 can."""
    means = [float(i) for i in range(7)]
    picked = fw.select_fixed_worlds(means)
    expect = tuple(min(max(math.ceil(q * 7), 1), 7) - 1
                   for q in (0.05, 0.50, 0.95))
    assert picked == expect
    assert expect == (0, 3, 6)


# ---------------------------------------------------------------------------
# The guard, inverted
# ---------------------------------------------------------------------------

def test_the_old_guard_would_now_be_protecting_nothing():
    """REPLACES `test_no_fixed_world_selection_rule_was_invented`.

    That test scanned the CONSUMER module for a name containing both
    "world" and "select". M11's rule lives in its own module, so the old
    scan would still pass -- forever, while a ratified rule sat one import
    away. Guarding "no rule exists" after a rule was ratified is worse than
    no guard, because it reads like coverage.

    What is actually worth protecting now is the pair: the rule exists HERE
    and is exactly the ratified one, and the consumer boundary still
    refuses to choose, so a world index always arrives explicitly."""
    from itsf.mc import consumer as mcc

    # 1. the ratified rule exists, in one place, and is callable
    assert callable(fw.select_fixed_worlds)
    assert fw.FIXED_WORLD_QUANTILES == (0.05, 0.50, 0.95)

    # 2. the consumer still names no world of its own
    for name in dir(mcc):
        low = name.lower()
        if "world" in low:
            assert "select" not in low and "choose" not in low, (
                f"{name}: the consumer must keep refusing to choose; "
                "selection is M11's and travels as an explicit index")

    # 3. and it still refuses an absent one
    from itsf.mc.consumer import MCInputError
    with pytest.raises(MCInputError) as ei:
        mcc.run_conditional_aleatoric({"not": "a set"}, world_index=0)
    assert ei.value.code == "aleatoric_source_invalid"


def test_selection_returns_indices_the_consumer_can_be_handed():
    """The rule returns world INDICES, not order positions. Handing a
    position to `world_index=` would silently report the wrong world
    whenever the means are not already sorted by index."""
    means = [100.0, -50.0, 0.0]
    low, mid, high = fw.select_fixed_worlds(means)
    assert (low, mid, high) == (1, 2, 0)


# ---------------------------------------------------------------------------
# M11 dependency 8: the selection reaches the report
# ---------------------------------------------------------------------------

def test_the_three_reports_are_the_three_selected_worlds():
    """The rule is only worth having if the report actually uses it. This
    pins the join: whatever `select_fixed_worlds` returns is exactly what
    gets reported, in that order."""
    from itsf.mc import consumer as mcc
    from test_mc_consumer import _prepare, PRIMARY

    prepared = _prepare()
    obs = mcc.run_observation_set(prepared, run_label="base",
                                  platform="topstep", engine="E1",
                                  scenario="Conservative", channel=PRIMARY,
                                  B=4, master_seed=7)
    expected = fw.select_fixed_worlds(obs.world_means())
    reports = mcc.fixed_world_reports(obs)
    assert len(reports) == 3
    assert tuple(r.world_index for r in reports) == expected


def test_the_reports_are_ordered_low_mid_high_by_world_mean():
    from itsf.mc import consumer as mcc
    from test_mc_consumer import _prepare, PRIMARY

    prepared = _prepare()
    obs = mcc.run_observation_set(prepared, run_label="base",
                                  platform="topstep", engine="E1",
                                  scenario="Conservative", channel=PRIMARY,
                                  B=8, master_seed=13)
    means = obs.world_means()
    lo, mid, hi = mcc.fixed_world_reports(obs)
    assert means[lo.world_index] <= means[mid.world_index] \
        <= means[hi.world_index]


def test_the_consumer_still_owns_no_selection_of_its_own():
    """`fixed_world_reports` carries indices; it does not choose them. If
    this module ever grows its own chooser the rule has two homes, which
    is the shape that produced four Highs in the supplement path."""
    import inspect
    from itsf.mc import consumer as mcc

    src = inspect.getsource(mcc.fixed_world_reports)
    assert "select_fixed_worlds(" in src
    assert "ceil" not in src and "sorted(" not in src, (
        "the consumer is re-deriving an order statistic instead of "
        "importing the one M11 ratified")
