"""Hand-computed checks for itsf.s0.labels on conftest synthetic days.

All bars come from the conftest generators only (no real market data).
PM window [10:00, 15:45) = 345 bars; final close = the 15:44 bar close.
trend_up pm bars (base 20000): bar i open=20000+i, close=20001+i,
high=close+0.25, low=open-0.25 -> C1000=20001, C1544=20345.
"""
from datetime import datetime

import pytest
from conftest import ET, make_minute_bars

from itsf.s0.labels import compute_day_labels, d_open_from_ret_open30

DATE = "2026-08-03"


def pm(pattern="trend_up", base=20000.0):
    return make_minute_bars(DATE, pattern, start="10:00", end="15:45",
                            base_price=base)


def test_trend_up_long_hand_computed():
    lab = compute_day_labels(pm("trend_up"), o1000=20000.0, adr14=100.0,
                             d_open=1)
    assert lab.trade_date == DATE
    assert lab.d_open == 1
    # Y_cont = +1 * (20345 - 20000) / 100              # frozen: S0 SS5 Y_cont
    assert lab.y_cont == pytest.approx(3.45)
    # Y1 = (20345 - 20000) / 100                       # frozen: S0 SS5 Y1
    assert lab.y1 == pytest.approx(3.45)
    # Y2: path_pm = |20001-20000| + 344*1 = 345; |345|/345 = 1
    #                                                  # frozen: S0 SS5 Y2
    assert lab.y2_de_pm == pytest.approx(1.0)
    # Y3: H=20345.25, L=19999.75 -> (20345 - 19999.75)/345.5
    assert lab.y3_close_pos_pm == pytest.approx(345.25 / 345.5)
    # Y4 MFE (extremes, long -> minute highs): (20345.25 - 20000)/100
    #                                                  # frozen: S0 SS5 Y4
    assert lab.y4_mfe == pytest.approx(3.4525)
    # Y5 MAE (extremes, long -> minute lows): (19999.75 - 20000)/100
    #                                                  # frozen: S0 SS5 Y5
    assert lab.y5_mae == pytest.approx(-0.0025)
    # Y6 assigned at dataset level only               # frozen: S0 SS5 Y6
    assert lab.y6_cont_decile is None


def test_trend_down_short_mirror():
    lab = compute_day_labels(pm("trend_down"), o1000=20000.0, adr14=100.0,
                             d_open=-1)
    # C1544 = 20000 - 345 = 19655
    assert lab.y1 == pytest.approx(-3.45)
    # Y_cont = -1 * (19655 - 20000)/100 = +3.45 (continuation in direction)
    assert lab.y_cont == pytest.approx(3.45)
    assert lab.y2_de_pm == pytest.approx(1.0)
    # short favourable = minute lows: min low = 19654.75
    assert lab.y4_mfe == pytest.approx(3.4525)
    # short adverse = minute highs: max high = 20000.25 (first bar)
    assert lab.y5_mae == pytest.approx(-0.0025)


def test_chop_low_pm_efficiency():
    lab = compute_day_labels(pm("chop"), o1000=20000.0, adr14=100.0, d_open=1)
    # chop closes alternate; 345 bars end at 20001 -> path 345, |1|/345
    assert lab.y2_de_pm == pytest.approx(1.0 / 345.0)
    assert lab.y1 == pytest.approx(0.01)
    assert lab.y_cont == pytest.approx(0.01)


def test_spike_day_mae_uses_minute_extremes():
    # spike_down: full-session generator puts a deep intraminute low at
    # minute 61 (10:31 bar): low = 20061 - 40 = 20021. Slice pm window.
    full = make_minute_bars(DATE, "spike_down", start="09:30", end="16:00")
    t10 = datetime(2026, 8, 3, 10, 0, tzinfo=ET)
    t1545 = datetime(2026, 8, 3, 15, 45, tzinfo=ET)
    bars = full[(full["ts"] >= t10) & (full["ts"] < t1545)]
    assert len(bars) == 345
    o1000 = float(bars["open"].iloc[0])   # 20030
    lab = compute_day_labels(bars, o1000=o1000, adr14=100.0, d_open=1)
    # Y5 from minute LOW extreme: (20021 - 20030)/100 = -0.09; the close
    # path never dips below o1000, so a close-based MAE would be +0.01 -
    # this pins the extreme-based reading.  # frozen: S0 SS5 Y5
    assert lab.y5_mae == pytest.approx(-0.09)
    assert lab.y5_mae < 0
    # Y4 from minute HIGH extreme: (20375.25 - 20030)/100
    assert lab.y4_mfe == pytest.approx(3.4525)
    # Y_cont uses closes only: (20375 - 20030)/100    # frozen: S0 SS5 Y_cont
    assert lab.y_cont == pytest.approx(3.45)


# ---------------------------------------------------------------------------
# IR-23 (APPROVED_BY_AARON 2026-08-01) — per-label independence.
# There is no "d_open == 0 -> whole row NA" early exit any more: Y1/Y2/Y3 do
# not depend on the direction and must be computed on a no-direction day;
# Y_cont/Y4/Y5 keep the direction dependency.
# ---------------------------------------------------------------------------

def test_ir23_no_direction_day_still_computes_y1_y2_y3():
    lab = compute_day_labels(pm("trend_up"), o1000=20000.0, adr14=100.0,
                             d_open=0)
    assert lab.trade_date == DATE
    assert lab.d_open == 0
    # direction-FREE labels, hand-computed exactly as in the directional case
    assert lab.y1 == pytest.approx(3.45)                 # (20345-20000)/100
    assert lab.y2_de_pm == pytest.approx(1.0)            # |345|/345
    assert lab.y3_close_pos_pm == pytest.approx(345.25 / 345.5)
    # direction-DEPENDENT labels stay NA (frozen L82 day: not tradeable)
    assert lab.y_cont is None
    assert lab.y4_mfe is None
    assert lab.y5_mae is None
    assert lab.y6_cont_decile is None                    # dataset-level pass


def test_ir23_no_direction_and_no_adr14_still_computes_y2_y3():
    """The warm-up shape: ADR14 missing AND no direction. Y2/Y3 need neither,
    so they are computable; Y1 needs ADR14 and is NA for THAT reason."""
    lab = compute_day_labels(pm("trend_up"), o1000=20000.0, adr14=None,
                             d_open=0)
    assert lab.y2_de_pm == pytest.approx(1.0)
    assert lab.y3_close_pos_pm == pytest.approx(345.25 / 345.5)
    assert lab.y1 is None                                # /ADR14
    assert lab.y_cont is None and lab.y4_mfe is None and lab.y5_mae is None


def test_ir23_availability_is_decided_per_label_by_its_own_inputs():
    """Mechanical dependency table (IR-23), asserted over the whole grid
    instead of a hand-written coverage number."""
    needs_adr = {"y_cont": True, "y1": True, "y2_de_pm": False,
                 "y3_close_pos_pm": False, "y4_mfe": True, "y5_mae": True}
    needs_dir = {"y_cont": True, "y1": False, "y2_de_pm": False,
                 "y3_close_pos_pm": False, "y4_mfe": True, "y5_mae": True}
    for d_open in (-1, 0, 1):
        for adr in (100.0, None):
            lab = compute_day_labels(pm("trend_up"), o1000=20000.0, adr14=adr,
                                     d_open=d_open)
            for name in needs_adr:
                expected = ((adr is not None or not needs_adr[name])
                            and (d_open != 0 or not needs_dir[name]))
                assert (getattr(lab, name) is not None) is expected, (
                    name, d_open, adr)


def test_ir23_direction_free_labels_are_invariant_to_d_open():
    """Strongest form of "Y1/Y2/Y3 do not depend on the direction": the same
    pm window must give the same three values for every d_open."""
    got = {d_open: compute_day_labels(pm("trend_up"), o1000=20000.0,
                                      adr14=100.0, d_open=d_open)
           for d_open in (-1, 0, 1)}
    for name in ("y1", "y2_de_pm", "y3_close_pos_pm"):
        values = {getattr(lab, name) for lab in got.values()}
        assert len(values) == 1, (name, values)


def test_ir23_no_whole_row_early_exit_remains_in_the_source():
    """Anti-regression on the exact construct IR-23 deleted: a d_open == 0
    branch that returns a bare DayLabels before any label is computed."""
    import ast
    import inspect
    from itsf.s0 import labels as labels_mod
    src = inspect.getsource(labels_mod.compute_day_labels)
    fn = ast.parse(src).body[0]
    for node in ast.walk(fn):
        if isinstance(node, ast.If):
            body = ast.dump(node)
            if "'d_open'" in body and "Return" in body:
                # a d_open test that RETURNS is exactly the deleted early exit
                assert "DayLabels" not in body, (
                    "d_open == 0 whole-row early exit is forbidden (IR-23)")


def test_missing_adr14_na_policy():
    # frozen: S0 SS3 - /ADR14 labels record NA; ADR14-free labels remain.
    lab = compute_day_labels(pm("trend_up"), o1000=20000.0, adr14=None,
                             d_open=1)
    assert lab.y_cont is None
    assert lab.y1 is None
    assert lab.y4_mfe is None
    assert lab.y5_mae is None
    assert lab.y2_de_pm == pytest.approx(1.0)
    assert lab.y3_close_pos_pm is not None


def test_d_open_helper_sign():
    # frozen: S0 SS5 - d_open = sign(ret_open30)
    assert d_open_from_ret_open30(0.3) == 1
    assert d_open_from_ret_open30(-0.2) == -1
    assert d_open_from_ret_open30(0.0) == 0
    assert d_open_from_ret_open30(None) == 0


def test_invalid_d_open_rejected():
    with pytest.raises(ValueError):
        compute_day_labels(pm(), o1000=20000.0, adr14=100.0, d_open=2)
