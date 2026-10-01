"""TASK 5 -- the trade / P&L engine. Synthetic price paths only."""
from __future__ import annotations

import pytest
import synth

from r1.bars import SyntheticBarSource
from r1.errors import AnchorError, LeakageError, R1Error
from r1.trade import execute_trade, mean_y_net, run_arm

DATE = "2015-01-02"


def _src(contract, **kw):
    return synth.source_with(contract, {DATE: synth.event_day_bars(contract, **kw)})


def _trade(contract, *, direction, entry, exit_price, **kw):
    src = _src(contract, pre_close=100.0, react_close=101.0,
               entry_open=entry, exit_open=exit_price, **kw)
    return execute_trade(src, DATE, direction, contract)


# ---------------------------------------------------------------- the six cases
def test_profitable_long(contract):
    t = _trade(contract, direction=1, entry=100.0, exit_price=110.0)
    assert t.gross_points == pytest.approx(10.0)
    assert t.y_net_usd == pytest.approx(10.0 * 2.0 - 3.99)
    assert t.y_net_usd > 0


def test_losing_long(contract):
    t = _trade(contract, direction=1, entry=100.0, exit_price=99.0)
    assert t.y_net_usd == pytest.approx(-1.0 * 2.0 - 3.99)
    assert t.y_net_usd < 0


def test_profitable_short(contract):
    t = _trade(contract, direction=-1, entry=100.0, exit_price=90.0)
    assert t.gross_points == pytest.approx(10.0)
    assert t.y_net_usd == pytest.approx(10.0 * 2.0 - 3.99)


def test_losing_short(contract):
    t = _trade(contract, direction=-1, entry=100.0, exit_price=101.0)
    assert t.y_net_usd == pytest.approx(-1.0 * 2.0 - 3.99)


def test_flat_path_is_exactly_the_round_turn_cost(contract):
    t = _trade(contract, direction=1, entry=100.0, exit_price=100.0)
    assert t.gross_points == 0.0
    assert t.y_net_usd == pytest.approx(-3.99)


def test_cost_only_loss_under_every_scenario(contract):
    src = _src(contract, pre_close=100.0, react_close=101.0, entry_open=100.0,
               exit_open=100.0)
    for name in contract.cost_scenarios:
        t = execute_trade(src, DATE, 1, contract, cost_scenario=name)
        assert t.y_net_usd == pytest.approx(
            -contract.round_turn_cost_usd(name))


def test_net_equals_gross_minus_round_turn_identity(contract):
    """Y_net computed through FILLS equals gross*point_value - round turn."""
    for d in (1, -1):
        for exit_price in (98.5, 100.0, 104.25):
            t = _trade(contract, direction=d, entry=100.0, exit_price=exit_price)
            expected = (t.gross_points * contract.point_value_usd
                        - contract.round_turn_cost_usd("Base"))
            assert t.y_net_usd == pytest.approx(expected)


# ---------------------------------------------------------------- anchors
def test_missing_entry_anchor_raises(contract):
    bars = [b for b in synth.event_day_bars(
        contract, pre_close=100.0, react_close=101.0, entry_open=101.0,
        exit_open=102.0) if b.minute != contract.entry_minute]
    src = synth.source_with(contract, {DATE: bars})
    with pytest.raises(AnchorError, match="missing"):
        execute_trade(src, DATE, 1, contract)


def test_missing_exit_anchor_raises(contract):
    bars = [b for b in synth.event_day_bars(
        contract, pre_close=100.0, react_close=101.0, entry_open=101.0,
        exit_open=102.0) if b.minute != contract.exit_minute]
    src = synth.source_with(contract, {DATE: bars})
    with pytest.raises(AnchorError):
        execute_trade(src, DATE, 1, contract)


def test_no_direction_is_refused(contract):
    src = _src(contract, pre_close=100.0, react_close=100.0, entry_open=100.0,
               exit_open=101.0)
    with pytest.raises(R1Error, match="E4"):
        execute_trade(src, DATE, 0, contract)


# ---------------------------------------------------------------- L-4
def test_l4_no_bar_before_0833_contributes(contract):
    """Perturb C(08:29), the release minute, C(08:31) and 08:32: Y_net is fixed."""
    a = execute_trade(_src(contract, pre_close=100.0, react_close=101.0,
                           entry_open=100.0, exit_open=103.0),
                      DATE, 1, contract)
    b = execute_trade(_src(contract, pre_close=17.0, react_close=4242.0,
                           entry_open=100.0, exit_open=103.0,
                           noise_after_signal=0.0),
                      DATE, 1, contract)
    assert a.y_net_usd == b.y_net_usd
    assert a.gross_points == b.gross_points


def test_l4_trade_window_refuses_a_pre_entry_read(contract):
    from r1.bars import TradeWindow
    src = _src(contract, pre_close=100.0, react_close=101.0, entry_open=101.0,
               exit_open=102.0)
    w = TradeWindow(src, DATE, contract)
    for minute in (contract.pre_release_anchor_minute,
                   contract.reaction_close_minute,
                   contract.signal_complete_minute):
        with pytest.raises(LeakageError, match="floor"):
            w.get(minute)


def test_l4_paths_never_include_a_pre_entry_minute(contract):
    t = execute_trade(_src(contract, pre_close=100.0, react_close=101.0,
                           entry_open=100.0, exit_open=101.0),
                      DATE, 1, contract)
    assert t.holding_minutes == contract.holding_minutes


# ---------------------------------------------------------------- prop paths
def test_adverse_excursion_before_a_profitable_exit(contract):
    """A trade that ends green can still have breached on the way (sealed R.2)."""
    span = contract.exit_minute - contract.entry_minute
    path = [100.0] * span
    path[10] = 80.0                      # a deep dip mid-hold
    src = synth.source_with(contract, {DATE: synth.event_day_bars(
        contract, pre_close=100.0, react_close=101.0, entry_open=100.0,
        exit_open=110.0, hold_path=path)})
    t = execute_trade(src, DATE, 1, contract)
    assert t.y_net_usd > 0                       # closes green
    assert t.mae_usd < -30.0                     # but the path went deeply red
    assert len(t.adverse_path_usd) == span


def test_short_adverse_path_uses_the_minute_high(contract):
    span = contract.exit_minute - contract.entry_minute
    path = [100.0] * span
    src = synth.source_with(contract, {DATE: synth.event_day_bars(
        contract, pre_close=100.0, react_close=99.0, entry_open=100.0,
        exit_open=95.0, hold_path=path, hold_high_offset=12.0)})
    t = execute_trade(src, DATE, -1, contract)
    assert t.mae_usd < 0
    assert t.y_net_usd > 0


def test_run_arm_and_mean(contract):
    dates = ["2015-01-02", "2015-02-06", "2015-03-06"]
    src = synth.simple_event_source(contract, dates, pre=100.0, react=101.0,
                                    entry=100.0, exit_price=102.0)
    results = run_arm(src, [(d, 1) for d in dates], contract)
    assert len(results) == 3
    assert mean_y_net(results) == pytest.approx(2.0 * 2.0 - 3.99)
    with pytest.raises(R1Error):
        mean_y_net([])


def test_real_bar_source_is_blocked_in_s2():
    from r1.bars import DevelopmentBarSource
    from r1.errors import AuthorityError
    with pytest.raises(AuthorityError, match="NOT authorized in S2"):
        DevelopmentBarSource("C:/anything")
    with pytest.raises(AuthorityError):
        DevelopmentBarSource("C:/anything", s3_authorization="please")


def test_synthetic_source_is_the_only_s2_source(contract):
    src = SyntheticBarSource()
    assert src.role == "synthetic"
