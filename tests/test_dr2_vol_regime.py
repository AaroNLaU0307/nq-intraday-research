"""DR-2 — the ruled vol20 volatility-regime producer (Aaron 2026-08-10).

SYNTHETIC ONLY. No real market data is touched anywhere in this file
(C:\\Users\\Aaron\\quant-data is never opened): every close series below is a
hand-written list, and the two universe-level tests build their sessions in
memory from the tests/test_s0_context.py generator contract.

HAND-ARITHMETIC FIXTURE (every exact pin in this file rests on it)
------------------------------------------------------------------
`alt_closes(c0, n)` multiplies alternately by 1.5 and 0.5 starting from
c0 = 100.0. Both factors and 100.0 are dyadic, so every close is an EXACT
binary float and every simple return is exact:

    C_0 = 100, C_1 = 150, C_2 = 75, C_3 = 112.5, C_4 = 56.25, ...
    r_odd  = (150 - 100)/100 = +0.5     (exactly)
    r_even = (75 - 150)/150  = -0.5     (exactly)

Over 21 closes -> 20 returns, ten +0.5 and ten -0.5, therefore

    mean      = 0
    sum(r^2)  = 20 * 0.25 = 5
    vol20     = sqrt(5/19)  with the RULED ddof=1   ~= 0.5129891760425771
    (ddof=0 would give sqrt(5/20) = 0.5 EXACTLY — the mutation pin below)
"""
from __future__ import annotations

import math
from dataclasses import replace

import numpy as np
import pytest

from test_s0_context import universe_of, weekdays

from itsf.contracts import VolatilityRegimeMethod, aaron_ruled_methods
from itsf.s0 import dataset as ds_mod
from itsf.s0.dataset import (
    VOL_NA_LABEL,
    VOL_TERCILE_LABELS,
    Vol20InputError,
    VolConservationError,
    assert_vol_conservation,
    build_vol20_regime_mapping,
    build_vol20_regime_mapping_from_universe,
    qualifying_rth_closes,
    vol_tercile_label,
    vol_tercile_thresholds,
)

RULED = aaron_ruled_methods().volatility_regime

#: vol20 of the alternating +-0.5 series, ddof=1 (see the module docstring).
VOL20_ALT_DDOF1 = math.sqrt(5.0 / 19.0)
VOL20_ALT_DDOF0 = 0.5


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------

def alt_closes(n: int, c0: float = 100.0) -> list[float]:
    """n closes, alternating x1.5 / x0.5 (exact binary floats)."""
    out = [c0]
    for i in range(n - 1):
        out.append(out[-1] * (1.5 if i % 2 == 0 else 0.5))
    return out


def varied_closes(n: int, c0: float = 100.0) -> list[float]:
    """n closes whose successive returns are all DIFFERENT.

    `alt_closes` is deliberately symmetric (ten +0.5 and ten -0.5), which
    makes it perfect for the exact vol20 pin and USELESS for the r1 test:
    dropping one return and extending by one swaps a +0.5 for a +0.5 and the
    std does not move. This series has no such symmetry, so a window that
    failed to extend — or that kept the roll-crossing return — produces a
    visibly different number.
    """
    factors = (1.5, 0.5, 1.25, 0.8, 1.1, 0.7, 1.9, 0.6)
    out = [c0]
    for i in range(n - 1):
        out.append(out[-1] * factors[i % len(factors)])
    return out


def simple_returns(closes) -> list[float]:
    return [(closes[i + 1] - closes[i]) / closes[i]
            for i in range(len(closes) - 1)]


def seq(dates, closes):
    return tuple(zip(dates, [float(c) for c in closes]))


def days(n: int, start: str = "2015-01-01") -> list[str]:
    """n consecutive ISO dates (calendar days; only the ORDER matters here —
    this producer indexes a supplied qualifying sequence, it never derives a
    calendar of its own)."""
    import datetime as _dt
    d0 = _dt.date.fromisoformat(start)
    return [(d0 + _dt.timedelta(days=i)).isoformat() for i in range(n)]


# ---------------------------------------------------------------------------
# 1. ruled-method dispatch (fail closed on any un-ruled string)
# ---------------------------------------------------------------------------

def test_ruled_strings_are_read_from_the_single_ruled_source():
    assert ds_mod.RULED_VOL_CLOSE_SOURCE == RULED.close_source
    assert ds_mod.RULED_VOL_RETURN_BASIS == RULED.return_basis
    assert ds_mod.RULED_VOL_ROLL_CROSSING_RULE == RULED.roll_crossing_rule
    assert ds_mod.RULED_VOL_TERCILE_REFERENCE == RULED.tercile_reference
    assert ds_mod.RULED_VOL_NA_RULE == RULED.na_rule
    assert ds_mod.RULED_VOL_MAPPING_SCOPE == RULED.mapping_scope


@pytest.mark.parametrize("field", ["close_source", "return_basis",
                                   "roll_crossing_rule", "tercile_reference",
                                   "na_rule", "mapping_scope"])
def test_unruled_method_string_raises(field):
    bad = replace(RULED, **{field: "SOMETHING_ELSE"})
    with pytest.raises(ValueError) as exc:
        build_vol20_regime_mapping(days=["2015-02-01"], qualifying_closes=(),
                                   roll_transition_dates=(), method=bad)
    assert f"volatility_regime.{field}_not_ruled:SOMETHING_ELSE" in str(exc.value)


@pytest.mark.parametrize("bad_ddof", [-1, "1", None, True, 1.0])
def test_invalid_ddof_raises(bad_ddof):
    bad = replace(RULED, ddof=bad_ddof)
    with pytest.raises(ValueError, match="ddof_invalid"):
        build_vol20_regime_mapping(days=["2015-02-01"], qualifying_closes=(),
                                   roll_transition_dates=(), method=bad)


def test_a_test_only_method_object_is_still_dispatched_on_the_ruled_strings():
    """A TEST_ONLY VolatilityRegimeMethod that keeps every ruled string is
    accepted (nothing here reads `test_only`); one that changes a ruled
    string is not. The dispatch is on the VALUES, never on a trust flag."""
    ok = VolatilityRegimeMethod(
        close_source=RULED.close_source, return_basis=RULED.return_basis,
        ddof=RULED.ddof, roll_crossing_rule=RULED.roll_crossing_rule,
        tercile_reference=RULED.tercile_reference, na_rule=RULED.na_rule,
        mapping_scope=RULED.mapping_scope)
    out = build_vol20_regime_mapping(days=["2015-02-01"],
                                     qualifying_closes=(),
                                     roll_transition_dates=(), method=ok)
    assert out.counts[VOL_NA_LABEL] == 1


# ---------------------------------------------------------------------------
# 2. vol20 — EXACT hand-computed pins
# ---------------------------------------------------------------------------

def test_vol20_exact_value_on_the_alternating_series():
    d = days(22)
    closes = alt_closes(21)
    out = build_vol20_regime_mapping(
        days=[d[21]], qualifying_closes=seq(d[:21], closes),
        roll_transition_dates=(), method=RULED)
    assert out.vol20[d[21]] == pytest.approx(VOL20_ALT_DDOF1, rel=0, abs=1e-15)
    assert out.na_cause == {}


def test_ddof_mutation_goes_red():
    """ddof=0 must NOT reproduce the ruled number: sqrt(5/20) = 0.5 exactly
    vs the ruled sqrt(5/19). If these ever coincide the ddof is dead."""
    d = days(22)
    closes = alt_closes(21)
    ruled = build_vol20_regime_mapping(
        days=[d[21]], qualifying_closes=seq(d[:21], closes),
        roll_transition_dates=(), method=RULED).vol20[d[21]]
    mutated = build_vol20_regime_mapping(
        days=[d[21]], qualifying_closes=seq(d[:21], closes),
        roll_transition_dates=(), method=replace(RULED, ddof=0)).vol20[d[21]]
    assert mutated == pytest.approx(VOL20_ALT_DDOF0, abs=1e-15)
    assert ruled != pytest.approx(mutated, abs=1e-9)


def test_log_return_basis_would_give_a_different_number():
    """SIMPLE returns are ruled. The log-return statistic on the same closes
    is a different number, so a silent basis swap cannot hide."""
    d = days(22)
    closes = alt_closes(21)
    ruled = build_vol20_regime_mapping(
        days=[d[21]], qualifying_closes=seq(d[:21], closes),
        roll_transition_dates=(), method=RULED).vol20[d[21]]
    log_rets = [math.log(closes[i + 1] / closes[i]) for i in range(20)]
    log_vol = float(np.std(np.asarray(log_rets), ddof=RULED.ddof))
    assert ruled != pytest.approx(log_vol, abs=1e-9)


def test_uses_exactly_the_nearest_21_closes_not_more():
    """A 22nd, older close is present but must not enter the window: the
    value is identical to the 21-close case."""
    d = days(30)
    closes = alt_closes(25)
    full = build_vol20_regime_mapping(
        days=[d[25]], qualifying_closes=seq(d[:25], closes),
        roll_transition_dates=(), method=RULED).vol20[d[25]]
    assert full == pytest.approx(VOL20_ALT_DDOF1, abs=1e-15)


# ---------------------------------------------------------------------------
# 3. no look-ahead (lag endpoint d-1)
# ---------------------------------------------------------------------------

def test_mutating_day_d_own_close_does_not_move_day_d_vol20():
    """d IS itself a qualifying session here, so its own close sits in the
    sequence. Changing it must leave d's own vol20 bit-identical."""
    d = days(23)
    closes = alt_closes(22)
    base_seq = seq(d[:22], closes)
    target = d[21]                                  # the last close IS d's own
    before = build_vol20_regime_mapping(
        days=[target], qualifying_closes=base_seq,
        roll_transition_dates=(), method=RULED).vol20[target]

    tampered = list(closes)
    tampered[21] = 999999.0                         # d's OWN close, mutated
    after = build_vol20_regime_mapping(
        days=[target], qualifying_closes=seq(d[:22], tampered),
        roll_transition_dates=(), method=RULED).vol20[target]
    assert before == after == pytest.approx(VOL20_ALT_DDOF1, abs=1e-15)


def test_a_later_days_close_never_enters_an_earlier_days_window():
    d = days(30)
    closes = alt_closes(26)
    target = d[21]
    a = build_vol20_regime_mapping(
        days=[target], qualifying_closes=seq(d[:26], closes),
        roll_transition_dates=(), method=RULED).vol20[target]
    tampered = list(closes)
    for i in range(22, 26):                          # every FUTURE close
        tampered[i] = 5.0
    b = build_vol20_regime_mapping(
        days=[target], qualifying_closes=seq(d[:26], tampered),
        roll_transition_dates=(), method=RULED).vol20[target]
    assert a == b


# ---------------------------------------------------------------------------
# 4. rule r1 — drop the roll-crossing return AND extend
# ---------------------------------------------------------------------------

def test_roll_crossing_return_is_dropped_and_the_window_extends():
    """22 closes -> return indices 0..20. A roll transition on close index 11
    makes return index 10 (the pair 10 -> 11) straddle it.

    r1 (RULED): drop return 10 and EXTEND, so the used set is
    {0..20} \\ {10} — exactly 20 returns, reaching one day further back.
    r2 (the rejected alternative): keep it, i.e. the nearest 20 = {1..20}.
    Both expected values are computed here from the closes by an independent
    formula, so this pins WHICH returns were used, not merely that the number
    changed.
    """
    d = days(30)
    closes = varied_closes(22)
    rets = simple_returns(closes)
    target = d[22]

    r1_expected = float(np.std(
        np.asarray([r for k, r in enumerate(rets) if k != 10]),
        ddof=RULED.ddof))
    r2_expected = float(np.std(np.asarray(rets[1:]), ddof=RULED.ddof))
    assert r1_expected != pytest.approx(r2_expected, abs=1e-12)

    with_roll = build_vol20_regime_mapping(
        days=[target], qualifying_closes=seq(d[:22], closes),
        roll_transition_dates=(d[11],), method=RULED)
    assert with_roll.n_roll_crossing_returns_dropped == 1
    assert with_roll.vol20[target] == pytest.approx(r1_expected, abs=1e-12)
    # and NOT the r2 (keep-the-return) value
    assert with_roll.vol20[target] != pytest.approx(r2_expected, abs=1e-12)

    no_roll = build_vol20_regime_mapping(
        days=[target], qualifying_closes=seq(d[:22], closes),
        roll_transition_dates=(), method=RULED)
    assert no_roll.vol20[target] == pytest.approx(r2_expected, abs=1e-12)
    assert no_roll.n_roll_crossing_returns_dropped == 0


def test_roll_crossing_without_enough_history_becomes_vol_na():
    """Exactly 21 closes and one crossing return -> only 19 usable returns
    remain and the window cannot extend: the day is the ruled 4th stratum,
    never a 19-return vol20."""
    d = days(30)
    closes = alt_closes(21)
    target = d[21]
    out = build_vol20_regime_mapping(
        days=[target], qualifying_closes=seq(d[:21], closes),
        roll_transition_dates=(d[5],), method=RULED)
    assert out.vol20[target] is None
    assert out.label_of[target] == VOL_NA_LABEL
    assert out.na_cause[target] == ds_mod.VOL_NA_INSUFFICIENT_HISTORY


def test_straddle_boundary_convention_is_older_lt_t_le_newer():
    """A transition ON the newer close's own session straddles; a transition
    ON the older close's session does not (it already applied to that close).
    """
    d = days(6)
    assert ds_mod._straddles_roll(d[0], d[1], (d[1],)) is True
    assert ds_mod._straddles_roll(d[0], d[1], (d[0],)) is False
    # a skipped (non-qualifying) session between the two also straddles
    assert ds_mod._straddles_roll(d[0], d[3], (d[2],)) is True
    assert ds_mod._straddles_roll(d[0], d[1], (d[4],)) is False


# ---------------------------------------------------------------------------
# 5. NA — the ruled FOURTH stratum (day kept, never dropped)
# ---------------------------------------------------------------------------

def test_fewer_than_21_qualifying_closes_is_vol_na_not_a_dropped_day():
    d = days(30)
    closes = alt_closes(20)                       # 20 closes -> 19 returns
    target = d[20]
    out = build_vol20_regime_mapping(
        days=[target], qualifying_closes=seq(d[:20], closes),
        roll_transition_dates=(), method=RULED)
    assert out.vol20[target] is None
    assert out.label_of[target] == VOL_NA_LABEL
    assert out.na_cause[target] == ds_mod.VOL_NA_INSUFFICIENT_HISTORY
    assert target in out.days                     # kept, never deleted
    assert out.counts[VOL_NA_LABEL] == 1


def test_a_zero_close_component_is_vol_na_not_a_division_error():
    d = days(30)
    closes = alt_closes(22)
    closes[10] = 0.0                              # unusable denominator
    target = d[22]
    out = build_vol20_regime_mapping(
        days=[target], qualifying_closes=seq(d[:22], closes),
        roll_transition_dates=(), method=RULED)
    assert out.vol20[target] is None
    assert out.na_cause[target] == ds_mod.VOL_NA_COMPONENT_UNUSABLE


def test_vol_na_days_never_enter_a_tercile():
    d = days(60)
    closes = alt_closes(40)
    labelled = list(d[:45])
    out = build_vol20_regime_mapping(
        days=labelled, qualifying_closes=seq(d[:40], closes),
        roll_transition_dates=(), method=RULED)
    for day in labelled:
        if out.vol20[day] is None:
            assert out.label_of[day] == VOL_NA_LABEL
        else:
            assert out.label_of[day] in VOL_TERCILE_LABELS
    assert out.counts[VOL_NA_LABEL] == sum(
        1 for v in out.vol20.values() if v is None)


# ---------------------------------------------------------------------------
# 6. ex-post terciles — threshold and boundary-side pins
# ---------------------------------------------------------------------------

def test_tercile_thresholds_are_the_numpy_linear_1_3_and_2_3_quantiles():
    """values 1..9: numpy linear virtual index is (n-1)*p, so
    q1 -> index 8/3 = 2.6667 -> 3 + 0.6667*(4-3) = 11/3
    q2 -> index 16/3 = 5.3333 -> 6 + 0.3333*(7-6) = 19/3."""
    q1, q2 = vol_tercile_thresholds([float(v) for v in range(1, 10)])
    assert q1 == pytest.approx(11.0 / 3.0)
    assert q2 == pytest.approx(19.0 / 3.0)


def test_tercile_boundary_is_lower_inclusive():
    th = (11.0 / 3.0, 19.0 / 3.0)
    assert vol_tercile_label(th[0], th) == VOL_TERCILE_LABELS[0]     # == q1
    assert vol_tercile_label(th[0] + 1e-9, th) == VOL_TERCILE_LABELS[1]
    assert vol_tercile_label(th[1], th) == VOL_TERCILE_LABELS[1]     # == q2
    assert vol_tercile_label(th[1] + 1e-9, th) == VOL_TERCILE_LABELS[2]
    assert vol_tercile_label(None, th) == VOL_NA_LABEL
    assert vol_tercile_label(1.0, None) == VOL_NA_LABEL


def test_thresholds_come_from_the_full_sample_once_not_per_slice():
    """The SAME thresholds label every day: computing them on a sub-sample
    would move at least one boundary. `mapping_scope` says the §2 axis and
    the Appendix-A stratum key read ONE mapping, so there is exactly one
    threshold pair in the produced structure."""
    d = days(80)
    closes = alt_closes(60)
    labelled = list(d[:65])
    out = build_vol20_regime_mapping(
        days=labelled, qualifying_closes=seq(d[:60], closes),
        roll_transition_dates=(), method=RULED)
    defined = [v for v in out.vol20.values() if v is not None]
    assert out.thresholds == vol_tercile_thresholds(defined)
    assert out.method_disclosure["tercile_reference_is_ex_post"] is True
    assert out.ex_post is True
    assert "EX-POST" in out.method_disclosure["tercile_reference_note"].upper()


def test_no_defined_vol20_means_no_thresholds_and_an_all_na_mapping():
    out = build_vol20_regime_mapping(
        days=["2015-01-01", "2015-01-02"], qualifying_closes=(),
        roll_transition_dates=(), method=RULED)
    assert out.thresholds is None
    assert set(out.label_of.values()) == {VOL_NA_LABEL}
    assert out.counts == {VOL_TERCILE_LABELS[0]: 0, VOL_TERCILE_LABELS[1]: 0,
                          VOL_TERCILE_LABELS[2]: 0, VOL_NA_LABEL: 2}


# ---------------------------------------------------------------------------
# 7. conservation — machine-asserted in the producer
# ---------------------------------------------------------------------------

def test_conservation_holds_on_a_produced_mapping():
    d = days(80)
    out = build_vol20_regime_mapping(
        days=list(d[:65]), qualifying_closes=seq(d[:60], alt_closes(60)),
        roll_transition_dates=(), method=RULED)
    assert all(out.conservation.values())
    assert sum(out.counts.values()) == len(out.days) == 65


def test_conservation_raises_on_a_missing_day():
    labels = {"2015-01-01": VOL_TERCILE_LABELS[0]}
    with pytest.raises(VolConservationError) as exc:
        assert_vol_conservation(["2015-01-01", "2015-01-02"], labels,
                                {"2015-01-01": 1.0, "2015-01-02": 2.0})
    assert "strata_union_equals_day_set=False" in str(exc.value)


def test_conservation_raises_on_a_label_outside_the_four_strata():
    labels = {"2015-01-01": "T4"}
    with pytest.raises(VolConservationError) as exc:
        assert_vol_conservation(["2015-01-01"], labels, {"2015-01-01": 1.0})
    assert "T4" in str(exc.value)


def test_conservation_raises_when_vol_na_count_disagrees_with_undefined():
    """A day with an undefined vol20 that was nevertheless given a tercile —
    the exact defect the fourth-stratum rule exists to prevent."""
    labels = {"2015-01-01": VOL_TERCILE_LABELS[0]}
    with pytest.raises(VolConservationError) as exc:
        assert_vol_conservation(["2015-01-01"], labels, {"2015-01-01": None})
    assert "vol_na_count_equals_undefined_vol20=False" in str(exc.value)


def test_duplicate_days_and_unsorted_closes_fail_closed():
    with pytest.raises(Vol20InputError, match="duplicates"):
        build_vol20_regime_mapping(days=["2015-01-01", "2015-01-01"],
                                   qualifying_closes=(),
                                   roll_transition_dates=(), method=RULED)
    with pytest.raises(Vol20InputError, match="date-ascending"):
        build_vol20_regime_mapping(
            days=["2015-02-01"],
            qualifying_closes=(("2015-01-02", 1.0), ("2015-01-01", 2.0)),
            roll_transition_dates=(), method=RULED)


# ---------------------------------------------------------------------------
# 8. the anchor adapter — reuses IR-19/26, never re-derives it
# ---------------------------------------------------------------------------

def test_qualifying_closes_are_the_exact_scheduled_last_1m_rth_closes():
    """Generator contract: closes[i] = base + (i+1)*step, so the 15:59 bar
    (index 389) closes at base + 390*step. Regular sessions only."""
    dates = weekdays("2020-01-02", 5)
    bars, uni = universe_of(dates)
    got = dict(qualifying_rth_closes(uni))
    assert set(got) == set(dates)
    for d in dates:
        assert got[d] == 20000.0 + 390 * 1.0
        assert got[d] == uni.summaries[d].official_close      # the SAME value
    del bars


def test_an_early_close_day_qualifies_at_its_own_final_scheduled_bar():
    """IR-19: a scheduled early close's anchor is its OWN last scheduled bar,
    not 15:59. The early-close day is a frozen-L44 feature-construction
    exclusion, which says nothing about whether the session had a close."""
    dates = weekdays("2020-01-02", 5)
    half = dates[2]
    bars, uni = universe_of(
        dates, spec={half: {"close_minute": 780, "n_bars": 210}})
    got = dict(qualifying_rth_closes(uni))
    assert half in got                                # early close QUALIFIES
    assert got[half] == uni.summaries[half].official_close
    assert half not in uni.funnel.structurally_eligible   # ...but not eligible
    del bars


def test_a_zero_bar_session_is_not_a_qualifying_close():
    dates = weekdays("2020-01-02", 5)
    dark = dates[2]
    bars, uni = universe_of(dates, spec={dark: {"no_bars": True}},
                            degraded=(dark,))
    got = dict(qualifying_rth_closes(uni))
    assert dark not in got
    assert set(got) == set(dates) - {dark}
    del bars


def test_from_universe_wiring_labels_every_structurally_eligible_day():
    dates = weekdays("2020-01-02", 40)
    bars, uni = universe_of(dates)
    out = build_vol20_regime_mapping_from_universe(uni, RULED)
    assert set(out.days) == set(uni.funnel.structurally_eligible)
    assert all(out.conservation.values())
    # every session here is identical, so every return is 0 -> vol20 == 0 for
    # the days that have 21 prior closes, and vol_na for the warm-up days.
    for day, v in out.vol20.items():
        assert v is None or v == pytest.approx(0.0, abs=1e-12)
    assert out.n_qualifying_closes == len(dates)
    del bars
