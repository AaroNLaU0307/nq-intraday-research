"""Hand-computed checks for itsf.s0.study on SYNTHETIC days only.

No real market data is touched anywhere in this file (C:\\Users\\Aaron\\
quant-data is never opened); every session is generated in memory from the
tests/test_s0_context.py generator contract, and every asserted number is
derived from the fixture contract stated below.

FIXTURE CONTRACT (all hand calculations below rest on it)
---------------------------------------------------------
Background day `flat_pm_closes(base)` — 390 complete RTH bars:
    bar i covers minute 570+i ET; open_0 = base, open_i = closes[i-1],
    high = max(open, close) + 0.25, low = min(open, close) - 0.25.
    closes[i] = base + (i+1)   for i < 30      -> C0959 = O1000 = base + 30
    closes[i] = base + 30      for i >= 30     -> C1544 = base + 30
  therefore   RTH range = (base+30.25) - (base-0.25) = 30.5   (EXACT)
              Y_cont     = (C1544 - O1000)/ADR14 = 0          -> always D_FP
              d_open     = +1
  and, since every background day has the same range, ADR14 = 30.5 exactly
  for any day whose 14 prior COMPLETE days are background days.

Crafted day `crafted_closes(pm_delta, up, dip_to)` — 380 bars (minutes
15:50-15:59 dropped, which keeps the day OUT of `complete_390` so its own odd
range never enters any ADR14, while (390-380)/390 = 2.6% keeps it inside the
frozen L44 10% missing-bar limit):
    closes[i] = base + (i+1)*up          for i < 30   -> O1000 = base + 30*up
    optional five-bar dip to `dip_to`    for 30 <= i < 35
    closes[i] = O1000 + pm_delta         otherwise    -> C1544 = O1000+pm_delta
  therefore   d_open = sign(up)   and   Y_cont = d_open * pm_delta / 30.5
  (exact: 15.25/30.5 == 0.5, 30.5/30.5 == 1.0, 45.75/30.5 == 1.5).

Cost grid = costs.build_scenarios(0.5, 1.0, 1.5), fee $1.74 RT:
    per-side friction (points):  Base 0.50 | Conservative 1.00 |
                                 Stress 1.00 (Base x2) | Severe 1.50
"""
from __future__ import annotations

import inspect
import json
import re
from dataclasses import replace

import pandas as pd
import pytest

from test_s0_context import universe_of, weekdays, zero_open30_closes

from itsf.contracts import CostScenarioParams
from itsf.s0 import costs, study
from itsf.s0.context import build_day_context
from itsf.s0.dataset import ERA_ACTUAL, ERA_PROXY, build_s0_dataset
from itsf.s0.study import StudyDayInput, StudyInputError, build_study, theta_key

RTH_BARS = 390
BASE = 20000.0
ADR14 = 30.5                       # fixture contract (background RTH range)
DROP_TAIL = tuple(range(950, 960))  # keeps a crafted day out of complete_390
K05, K03 = theta_key(0.5), theta_key(0.3)


# ---------------------------------------------------------------------------
# synthetic session builders
# ---------------------------------------------------------------------------

def flat_pm_closes(base: float = BASE, n: int = RTH_BARS) -> list[float]:
    """Background day: opening drive up 30, flat afternoon -> Y_cont == 0."""
    return [base + (i + 1) if i < 30 else base + 30.0 for i in range(n)]


def crafted_closes(pm_delta: float, up: float = 1.0,
                   dip_to: float | None = None, base: float = BASE,
                   n: int = RTH_BARS) -> list[float]:
    """Session with an EXACT Y_cont = sign(up) * pm_delta / 30.5."""
    o1000 = base + 30.0 * up
    target = o1000 + pm_delta
    out: list[float] = []
    for i in range(n):
        if i < 30:
            out.append(base + (i + 1) * up)
        elif dip_to is not None and i < 35:
            out.append(o1000 + (dip_to - o1000) * (i - 29) / 5.0)
        else:
            out.append(target)
    return out


DATES = weekdays("2019-04-01", 34)
# Index map (frozen L109-115 micro era boundary 2019-05-06 falls at idx 25):
#   0..13  ADR14 warm-up      -> Y_cont NA, in NEITHER D_TP nor D_FP
#   14..19 background         -> D_FP (proxy era)
IDX_TP_BOUNDARY = 20     # 04-29 proxy: Y_cont EXACTLY 0.5
IDX_MID = 21             # 04-30 proxy: Y_cont 15/30.5 -> FP at 0.5, TP at 0.3
IDX_DIP = 22             # 05-01 proxy: E1 stops out, E2 rides to 15:44
IDX_ZERO_DIR = 23        # 05-02 proxy: d_open == 0 (frozen L82)
IDX_SHORT = 24           # 05-03 proxy: d_open == -1, Y_cont 1.0
IDX_TP_ACTUAL = 28       # 05-09 actual era: Y_cont 1.5
IDX_MID_ACTUAL = 30      # 05-13 actual era: FP at 0.5, TP at 0.3

DIP_TO = 19990.0         # below the opening-range low 19999.75 -> E1 stop


def _spec() -> dict:
    spec = {d: {"closes": flat_pm_closes()} for d in DATES}
    crafted = {
        IDX_TP_BOUNDARY: crafted_closes(15.25),
        IDX_MID: crafted_closes(15.0),
        IDX_DIP: crafted_closes(20.0, dip_to=DIP_TO),
        IDX_ZERO_DIR: zero_open30_closes(BASE),
        IDX_SHORT: crafted_closes(-30.5, up=-1.0),
        IDX_TP_ACTUAL: crafted_closes(45.75),
        IDX_MID_ACTUAL: crafted_closes(15.0),
    }
    for idx, cl in crafted.items():
        spec[DATES[idx]] = {"closes": cl, "skip_minutes": DROP_TAIL}
    return spec


def scenario_grid(adverse: dict | None = None) -> dict:
    """The frozen S0 §6 four-scenario grid on a hand-computable spread set."""
    return costs.build_scenarios(0.5, 1.0, 1.5, adverse_slippage_ticks=adverse)


SCENARIOS = scenario_grid()


def build_inputs(bars, uni, ds, mutate=None) -> dict:
    """The entrypoint-shaped day_inputs map: PM window + opening-range extremes.

    or_high/or_low come from the 09:30-09:59 observation window ONLY — no bar
    at or after 10:00 contributes (frozen §7 opening-range stop, no look-ahead).
    """
    mutate = mutate or {}
    out = {}
    for r in ds.records:
        if r.labels.d_open not in (1, -1) or r.labels.y_cont is None:
            continue
        ctx = build_day_context(r.trade_date, bars, uni)
        pm = ctx.pm_bars
        if r.trade_date in mutate:
            pm = mutate[r.trade_date](pm)
        out[r.trade_date] = StudyDayInput(
            trade_date=r.trade_date,
            pm_bars=pm,
            or_high=float(ctx.obs_bars["high"].max()),
            or_low=float(ctx.obs_bars["low"].min()),
            d_open=int(r.labels.d_open))
    return out


_CACHE: dict = {}


def market():
    if "market" not in _CACHE:
        bars, uni = universe_of(DATES, _spec())
        ds = build_s0_dataset(bars, uni)
        _CACHE["market"] = (bars, uni, ds)
    return _CACHE["market"]


def study_result():
    if "study" not in _CACHE:
        bars, uni, ds = market()
        _CACHE["study"] = build_study(ds, build_inputs(bars, uni, ds),
                                      SCENARIOS)
    return _CACHE["study"]


def y_cont_of(date: str) -> float | None:
    _bars, _uni, ds = market()
    return {r.trade_date: r.labels.y_cont for r in ds.records}[date]


# ---------------------------------------------------------------------------
# day universe: the Appendix-A D_TP / D_FP partition (frozen §7 L133, App A)
# ---------------------------------------------------------------------------

def test_theta_boundary_day_is_a_continuation_event():
    """frozen §7 L133 / App A: 延续事件 = Y_cont >= θ — the boundary is
    INCLUSIVE, so Y_cont == 0.5 is a D_TP day, never a D_FP day."""
    day = DATES[IDX_TP_BOUNDARY]
    assert y_cont_of(day) == 0.5            # fixture: 15.25 / 30.5, exact
    uni = study_result()["per_theta"][K05]["day_universe"]
    assert day in uni["tp_days"]
    assert day not in uni["fp_days"]


def test_partition_counts_at_both_frozen_thetas():
    """Hand count from the index map: 19 directional-tradeable days;
    θ=0.5 -> 4 TP / 15 FP, θ=0.3 -> 6 TP / 13 FP."""
    out = study_result()
    u05 = out["per_theta"][K05]["day_universe"]
    u03 = out["per_theta"][K03]["day_universe"]
    assert u05["n_directional_tradeable"] == 19
    assert (u05["n_tp"], u05["n_fp"]) == (4, 15)
    assert (u03["n_tp"], u03["n_fp"]) == (6, 13)
    # the secondary theta's event set STRICTLY contains the primary's
    assert set(u05["tp_days"]) < set(u03["tp_days"])
    for u in (u05, u03):
        assert all(u["conservation"].values())
        assert u["n_tp"] + u["n_fp"] == u["n_trade_constructible"] == 19


def test_zero_direction_and_missing_y_cont_days_are_in_neither_set():
    """frozen §5 L82 + the NA policy: a no-direction day and an ADR14 warm-up
    day (Y_cont NA) are counted, never traded, and appear in NO D_TP/D_FP set."""
    out = study_result()
    zero_dir = DATES[IDX_ZERO_DIR]
    warmup = DATES[3]
    _bars, _uni, ds = market()
    by_date = {r.trade_date: r for r in ds.records}
    assert by_date[zero_dir].labels.d_open == 0
    assert by_date[warmup].labels.y_cont is None
    for key in (K05, K03):
        u = out["per_theta"][key]["day_universe"]
        for day in (zero_dir, warmup):
            assert day not in u["tp_days"]
            assert day not in u["fp_days"]
    assert zero_dir not in out["day_universe"]["trade_constructible_days"]
    assert warmup not in out["day_universe"]["trade_constructible_days"]
    # ... and they were not disclosed either: they are simply not tradeable
    assert out["untradeable_disclosure"] == []


def test_era_split_is_exact_and_never_replaced_by_the_pooled_figure():
    """frozen §6 L109-115 — the counterfactual and actual-micro eras are
    reported on SEPARATE axes. θ=0.5 TP: 3 proxy-era days, 1 actual-era day."""
    out = study_result()
    block = out["per_theta"][K05]["executable"]["E2"]["Base"]
    assert block["by_era"][ERA_PROXY]["n"] == 3
    assert block["by_era"][ERA_ACTUAL]["n"] == 1
    assert block["pooled"]["n"] == 4
    proxy_days = [d for d, _p in block["by_era"][ERA_PROXY]["daily_pnl_usd"]]
    assert all(d < "2019-05-06" for d in proxy_days)     # frozen boundary
    actual_days = [d for d, _p in block["by_era"][ERA_ACTUAL]["daily_pnl_usd"]]
    assert all(d >= "2019-05-06" for d in actual_days)
    assert out["day_universe"]["by_era"][ERA_PROXY][
        "n_directional_tradeable"] == 10
    assert out["day_universe"]["by_era"][ERA_ACTUAL][
        "n_directional_tradeable"] == 9


def test_both_frozen_thetas_are_reported_with_their_roles():
    """frozen §7 L133 — θ 主 0.5、副 0.3, 完整报告, 不得事后升格."""
    out = study_result()
    assert out["thetas"] == [0.5, 0.3]
    assert out["theta_roles"] == {K05: "primary", K03: "secondary"}
    assert set(out["per_theta"]) == {K05, K03}
    assert out["per_theta"][K05]["theta_role"] == "primary"
    assert out["per_theta"][K03]["theta_role"] == "secondary"


def test_a_theta_outside_the_frozen_pair_is_refused():
    """frozen §11 禁止参数扫描 — `thetas` selects from the frozen pair and can
    never introduce a third threshold."""
    _bars, _uni, ds = market()
    inputs = build_inputs(*market())
    with pytest.raises(ValueError, match="not a frozen value"):
        build_study(ds, inputs, SCENARIOS, thetas=(0.4,))
    with pytest.raises(ValueError, match="duplicate theta"):
        build_study(ds, inputs, SCENARIOS, thetas=(0.5, 0.5))
    with pytest.raises(ValueError, match="must not be empty"):
        build_study(ds, inputs, SCENARIOS, thetas=())


# ---------------------------------------------------------------------------
# §10.1 atomic records: every engine x every scenario, TP and FP alike
# ---------------------------------------------------------------------------

def test_records_cover_every_engine_scenario_and_are_date_ordered():
    """frozen §10.1 — the atomic handoff is per engine x per cost scenario,
    over EVERY tradeable day (App A trades D_FP days under the same rules)."""
    out = study_result()
    expected_days = sorted(out["day_universe"]["trade_constructible_days"])
    assert set(out["records"]) == {"E1", "E2"}
    for engine in ("E1", "E2"):
        assert set(out["records"][engine]) == {"Base", "Conservative",
                                               "Stress", "Severe"}
        for name, recs in out["records"][engine].items():
            assert [r.trade_date for r in recs] == expected_days
            assert {r.engine for r in recs} == {engine}
            assert {r.cost_scenario for r in recs} == {name}
    assert out["scenarios_used"] == ["Base", "Conservative", "Stress", "Severe"]


def test_e1_stops_out_where_e2_rides_to_the_1544_close():
    """frozen §7 — E1 carries the opening-range opposite-extreme stop; E2 places
    no order and is forced out at the 15:44 close (frozen §3).

    Fixture: the dip day falls to 19990 while the opening-range low (E1's long
    stop) is 19999.75. The first bar whose low reaches the stop is the 10:03 bar
    (open 20006, close 19998, low 19997.75) -> intrabar touch, trigger_ref =
    min(stop, bar_open) = 19999.75, Base adverse friction 0.5 pt ->
    fill 19999.25; realized (19999.25 - 20030.5) x $2 = -62.5, minus the 1.74
    fee once = -64.24. E2 exits at 20050 -> 20049.5 -> +36.26.
    """
    out = study_result()
    day = DATES[IDX_DIP]
    e1 = [r for r in out["records"]["E1"]["Base"] if r.trade_date == day][0]
    e2 = [r for r in out["records"]["E2"]["Base"] if r.trade_date == day][0]
    assert e1.stop_triggered is True
    assert e1.actual_stop_fill == pytest.approx(19999.25)
    assert e1.final_pnl_per_contract == pytest.approx(-64.24)
    assert len(e1.mtm_close_pnl_1m) == 4            # truncated at the stop bar
    assert e1.exit_ts.endswith("10:03:00-04:00")
    assert e2.stop_triggered is False
    assert e2.planned_stop is None                  # E2 places no stop order
    assert len(e2.mtm_close_pnl_1m) == 345          # 10:00..15:44 inclusive
    assert e2.final_pnl_per_contract == pytest.approx(36.26)
    assert e2.exit_ts.endswith("15:44:00-04:00")
    # the counterfactual anchor is identical under both engines (frozen MC §3)
    assert e2.sizing_anchor_usd == pytest.approx(e1.sizing_anchor_usd)


def test_stress_friction_is_visible_in_the_pnl_ordering():
    """frozen §6 — Stress = Base market_friction x 2 (platform_fee 不翻倍).

    On an unstopped path the friction enters twice (entry + timed exit), so
    Base - Stress = 2 x 0.5 pt x $2 = $2.00 exactly; Severe is worse still.
    """
    out = study_result()
    day = DATES[IDX_TP_BOUNDARY]

    def pnl(scn):
        rec = [r for r in out["records"]["E2"][scn] if r.trade_date == day][0]
        return rec.final_pnl_per_contract

    assert pnl("Base") == pytest.approx(26.76)
    assert pnl("Base") - pnl("Stress") == pytest.approx(2.0)
    assert pnl("Stress") == pytest.approx(pnl("Conservative"))  # same friction
    assert pnl("Severe") < pnl("Stress") < pnl("Base")


def test_theoretical_oracle_is_an_upper_bound_on_the_executable_run():
    """frozen §7 — the theoretical Oracle is an ECONOMIC UPPER BOUND: 10:00
    entry, exit at the most favourable in-window price, Base costs. It must
    dominate the E2 timed exit on the same day and scenario."""
    out = study_result()
    theo = dict(out["per_theta"][K05]["theoretical_oracle"]["pooled"]["daily_usd"])
    e2 = dict(out["per_theta"][K05]["executable"]["E2"]["Base"][
        "pooled"]["daily_pnl_usd"])
    e1 = dict(out["per_theta"][K05]["executable"]["E1"]["Base"][
        "pooled"]["daily_pnl_usd"])
    assert set(theo) == set(e2) == set(e1)
    for day in theo:
        assert theo[day] >= e2[day]
        assert theo[day] >= e1[day]
    # hand value on the boundary day: favourable high 20045.5 -> exit 20045.0,
    # entry 20030.5 -> 14.5 x $2 - 1.74 = 27.26 (vs E2's 26.76)
    assert theo[DATES[IDX_TP_BOUNDARY]] == pytest.approx(27.26)


def test_theoretical_oracle_uses_base_costs_and_tp_days_only():
    """frozen §7 — Oracle 只在延续事件日交易, and the bound is defined net of
    BASE costs; the θ=0.3 set adds days, never removes any."""
    out = study_result()
    block05 = out["per_theta"][K05]["theoretical_oracle"]
    block03 = out["per_theta"][K03]["theoretical_oracle"]
    assert block05["scenario"] == "Base"
    days05 = {d for d, _v in block05["pooled"]["daily_usd"]}
    days03 = {d for d, _v in block03["pooled"]["daily_usd"]}
    assert days05 == set(out["per_theta"][K05]["day_universe"]["tp_days"])
    assert days05 < days03
    fp_days = set(out["per_theta"][K05]["day_universe"]["fp_days"])
    assert not (days05 & fp_days)


def test_the_base_scenario_is_required():
    """frozen §7 — without Base there is no defined theoretical upper bound."""
    _bars, _uni, ds = market()
    partial = {k: v for k, v in SCENARIOS.items() if k != "Base"}
    with pytest.raises(ValueError, match="'Base' scenario is required"):
        build_study(ds, build_inputs(*market()), partial)


# ---------------------------------------------------------------------------
# §8 integer-sizing outputs
# ---------------------------------------------------------------------------

def test_planned_risk_equals_the_record_sizing_anchor():
    """frozen §8 — risk_usd_per_1_MNQ_planned = 正常 stop 成交＋成本, i.e.
    exactly the record's sizing_anchor_usd (paths.sizing_anchor_usd).

    Base hand value: entry 20030.5, stop 19999.75, adverse friction 0.5 ->
    normal stop fill 19999.25; (20030.5-19999.25) x $2 + 1.74 = 64.24.
    """
    out = study_result()
    for engine in ("E1", "E2"):
        for name in SCENARIOS:
            rows = out["per_theta"][K05]["sizing_rows"][engine][name]
            recs = {r.trade_date: r for r in out["records"][engine][name]}
            assert len(rows) == 4          # one row per TP-day trade
            for row in rows:
                rec = recs[row["trade_date"]]
                assert row["risk_usd_per_1_MNQ_planned"] == pytest.approx(
                    rec.sizing_anchor_usd)
                assert row["minimum_1_contract_risk"] == pytest.approx(
                    rec.sizing_anchor_usd)
    base_rows = {r["trade_date"]: r
                 for r in out["per_theta"][K05]["sizing_rows"]["E1"]["Base"]}
    assert base_rows[DATES[IDX_TP_BOUNDARY]][
        "risk_usd_per_1_MNQ_planned"] == pytest.approx(64.24)


def test_realized_risk_is_populated_only_on_e1_stop_days():
    """frozen §8 — risk_usd_per_1_MNQ_realized 含 gap 穿越真实损失: only a trade
    that ACTUALLY exited on its stop realized a stop loss. E2 places no stop and
    an unstopped E1 day never realized its planned risk -> None (not 0)."""
    out = study_result()
    e1_rows = {r["trade_date"]: r
               for r in out["per_theta"][K05]["sizing_rows"]["E1"]["Base"]}
    e2_rows = {r["trade_date"]: r
               for r in out["per_theta"][K05]["sizing_rows"]["E2"]["Base"]}
    dip = DATES[IDX_DIP]
    assert e1_rows[dip]["stop_triggered"] is True
    # realized loss = -final_pnl = 64.24 (equals the planned anchor here
    # because the fixture stop is touched intrabar, with no gap-through)
    assert e1_rows[dip]["risk_usd_per_1_MNQ_realized"] == pytest.approx(64.24)
    assert e2_rows[dip]["risk_usd_per_1_MNQ_realized"] is None
    for day, row in e1_rows.items():
        if day != dip:
            assert row["stop_triggered"] is False
            assert row["risk_usd_per_1_MNQ_realized"] is None
    assert all(r["risk_usd_per_1_MNQ_realized"] is None
               for r in e2_rows.values())


def test_cost_and_cost_as_pct_of_r_math_including_the_stop_exit_side():
    """frozen §8 — cost_usd_per_1_MNQ / cost_as_pct_of_R; the stop-exit side is
    priced with ADVERSE slippage exactly on the days that exited on the stop.

    Grid used here overrides only Base's adverse slippage (3 ticks instead of
    1), so a stop exit costs 0.5 pt more per contract than a timed exit:
      timed  = (0.50 + 0.50) pt x $2 + 1.74 = $3.74
      stop   = (0.50 + 1.00) pt x $2 + 1.74 = $4.74
    """
    _bars, _uni, ds = market()
    grid = scenario_grid(adverse={"Base": 3.0})
    out = build_study(ds, build_inputs(*market()), grid)
    rows = {r["trade_date"]: r
            for r in out["per_theta"][K05]["sizing_rows"]["E1"]["Base"]}
    dip, flat = DATES[IDX_DIP], DATES[IDX_TP_BOUNDARY]
    assert rows[dip]["cost_usd_per_1_MNQ"] == pytest.approx(4.74)
    assert rows[flat]["cost_usd_per_1_MNQ"] == pytest.approx(3.74)
    for row in rows.values():
        assert row["cost_as_pct_of_R"] == pytest.approx(
            row["cost_usd_per_1_MNQ"] / row["risk_usd_per_1_MNQ_planned"])
        assert row["nonpositive_planned_risk"] is False


def test_stop_distance_uses_the_counterfactual_anchor_under_e2():
    """frozen §8 + MC §3 — E2 stores planned_stop = None (no order is placed),
    so the §8 stop distance is reconstructed from the same opening-range level
    `sizing_anchor_usd` was computed from, and is identical under both engines.

    Base hand value: |entry 20030.5 - opening-range low 19999.75| = 30.75 pt.
    """
    out = study_result()
    day = DATES[IDX_TP_BOUNDARY]
    e1 = {r["trade_date"]: r
          for r in out["per_theta"][K05]["sizing_rows"]["E1"]["Base"]}[day]
    e2 = {r["trade_date"]: r
          for r in out["per_theta"][K05]["sizing_rows"]["E2"]["Base"]}[day]
    assert e1["stop_distance_points"] == pytest.approx(30.75)
    assert e2["stop_distance_points"] == pytest.approx(30.75)
    assert e1["counterfactual_anchor"] is False
    assert e2["counterfactual_anchor"] is True
    assert e1["stop_level_points"] == e2["stop_level_points"] == 19999.75
    # short day: the stop is the OPPOSITE (high) extreme  # frozen: S0 §7
    short = {r["trade_date"]: r for r in
             out["per_theta"][K05]["sizing_rows"]["E1"]["Base"]}[DATES[IDX_SHORT]]
    assert short["direction"] == -1
    assert short["stop_level_points"] == pytest.approx(20000.25)


def test_budget_coverage_fractions_are_plain_arithmetic():
    """frozen §8 + §10.1 — {$50,$75,$100,$150} coverage is DESCRIPTIVE ONLY.
    Every TP-day trade carries a planned risk of $64.24 under Base, so the $50
    budget covers 0/4 and every larger budget covers 4/4."""
    out = study_result()
    cov = out["per_theta"][K05]["sizing_coverage"]["E1"]["Base"]
    rows = out["per_theta"][K05]["sizing_rows"]["E1"]["Base"]
    assert cov["n_trades"] == 4
    assert cov["by_budget_usd"]["50"] == {"n_covered": 0, "fraction": 0.0}
    for budget in ("75", "100", "150"):
        assert cov["by_budget_usd"][budget] == {"n_covered": 4,
                                                "fraction": 1.0}
    for budget in (50, 75, 100, 150):
        expected = sum(1 for r in rows
                       if r["risk_usd_per_1_MNQ_planned"] <= budget)
        assert cov["by_budget_usd"][str(budget)]["n_covered"] == expected


# ---------------------------------------------------------------------------
# §7 E2 mandatory worst-day report
# ---------------------------------------------------------------------------

def test_e2_worst_day_p1_p5_percentiles_are_reported_per_era_and_pooled():
    """frozen §7 table — E2 强制报告最差日 P1/P5.

    θ=0.5 E2 Base daily P&L = [26.76, 36.26, 57.26, 87.76] (sorted). With linear
    interpolation between order statistics: P1 = 26.76 + 0.03 x 9.5 = 27.045,
    P5 = 26.76 + 0.15 x 9.5 = 28.185.
    """
    out = study_result()
    block = out["per_theta"][K05]["executable"]["E2"]["Base"]
    values = sorted(p for _d, p in block["pooled"]["daily_pnl_usd"])
    assert values == pytest.approx([26.76, 36.26, 57.26, 87.76])
    report = block["worst_day_report"]
    assert report["frozen_mandatory"] is True
    assert report["pooled"]["P1"] == pytest.approx(27.045)
    assert report["pooled"]["P5"] == pytest.approx(28.185)
    assert set(report["by_era"]) == {ERA_PROXY, ERA_ACTUAL}
    assert report["by_era"][ERA_ACTUAL]["P1"] == pytest.approx(87.76)  # n == 1
    assert out["per_theta"][K05]["executable"]["E1"]["Base"][
        "worst_day_report"]["frozen_mandatory"] is False


# ---------------------------------------------------------------------------
# §10.5 frequency block
# ---------------------------------------------------------------------------

def test_frequency_block_arithmetic():
    """frozen §10.5 — 基础率 p, 每年可交易日数, Oracle 月均频率.

    Fixture: 19 directional-tradeable days, 4 continuation days at θ=0.5 and 6
    at θ=0.3; the sample spans 2019-04 and 2019-05 (2 months), the proxy era
    spans both and the actual-micro era only 2019-05.
    """
    out = study_result()
    freq = out["per_theta"][K05]["frequency"]
    pooled = freq[study.POOLED]
    assert pooled["n_days_in_sample"] == 34
    assert pooled["n_directional_tradeable"] == 19
    assert pooled["n_continuation_days_labelled"] == 4
    assert pooled["n_continuation_days_traded"] == 4
    assert pooled["continuation_base_rate_p"] == pytest.approx(4 / 19)
    assert pooled["n_months_in_slice"] == 2
    assert pooled["oracle_monthly_frequency"] == pytest.approx(2.0)
    assert freq["by_era"][ERA_PROXY]["n_directional_tradeable"] == 10
    assert freq["by_era"][ERA_PROXY]["oracle_monthly_frequency"] == (
        pytest.approx(1.5))                       # 3 TP days / 2 months
    assert freq["by_era"][ERA_ACTUAL]["oracle_monthly_frequency"] == (
        pytest.approx(1.0))                       # 1 TP day / 1 month
    assert set(freq["by_year"]) == {"2019"}
    assert freq["by_year"]["2019"]["n_directional_tradeable"] == 19
    # the secondary theta moves the numerator only
    freq03 = out["per_theta"][K03]["frequency"][study.POOLED]
    assert freq03["n_directional_tradeable"] == 19
    assert freq03["continuation_base_rate_p"] == pytest.approx(6 / 19)
    assert freq03["oracle_monthly_frequency"] == pytest.approx(3.0)


# ---------------------------------------------------------------------------
# Appendix A: D_TP / D_FP
# ---------------------------------------------------------------------------

def test_d_tp_and_d_fp_match_the_per_day_records_exactly():
    """frozen App A — D_TP and D_FP are the SAME rules and the SAME direction
    d_open, split only by the Y_cont threshold; every value must be the day's
    own final_pnl_per_contract."""
    out = study_result()
    for key in (K05, K03):
        block = out["per_theta"][key]
        tp_days = set(block["day_universe"]["tp_days"])
        fp_days = set(block["day_universe"]["fp_days"])
        assert not (tp_days & fp_days)
        for engine in ("E1", "E2"):
            for name in SCENARIOS:
                recs = {r.trade_date: r.final_pnl_per_contract
                        for r in out["records"][engine][name]}
                d_tp = block["d_tp"][engine][name]
                d_fp = block["d_fp"][engine][name]
                assert set(d_tp) == tp_days
                assert set(d_fp) == fp_days
                for day, value in {**d_tp, **d_fp}.items():
                    assert value == pytest.approx(recs[day])
                # the FP side really did trade in d_open, not flat
                assert all(r.direction in (1, -1)
                           for r in out["records"][engine][name])


# ---------------------------------------------------------------------------
# fail-safe disclosure (input-side defects are never silent)
# ---------------------------------------------------------------------------

def test_untradeable_disclosure_fires_and_conserves_the_day_counts():
    """A day the frozen definitions call tradeable, whose supplied frame has no
    10:00 entry bar, is DISCLOSED and excluded from both sets — never silently
    dropped. Counts must still conserve."""
    _bars, _uni, ds = market()
    victim = DATES[IDX_TP_BOUNDARY]
    inputs = build_inputs(*market(),
                          mutate={victim: lambda pm: pm.iloc[1:].reset_index(
                              drop=True)})
    out = build_study(ds, inputs, SCENARIOS)
    assert out["untradeable_disclosure"] == [{
        "trade_date": victim, "year": "2019", "era": ERA_PROXY,
        "d_open": 1, "y_cont": 0.5, "reason": study.REASON_NO_ENTRY_BAR}]
    u = out["per_theta"][K05]["day_universe"]
    assert u["n_directional_tradeable"] == 19
    assert u["n_trade_constructible"] == 18
    assert u["n_untradeable_disclosed"] == 1
    assert (u["n_tp"], u["n_fp"]) == (3, 15)
    assert u["n_tp_labelled"] == 4          # the label population is unchanged
    assert all(u["conservation"].values())
    assert victim not in u["tp_days"] and victim not in u["fp_days"]
    assert len(out["records"]["E1"]["Base"]) == 18
    # the frequency denominator is a LABEL population and does not shrink
    freq = out["per_theta"][K05]["frequency"][study.POOLED]
    assert freq["n_directional_tradeable"] == 19
    assert freq["n_continuation_days_labelled"] == 4
    assert freq["n_continuation_days_traded"] == 3


def test_a_missing_forced_exit_bar_is_disclosed_too():
    """frozen §3 — no 15:44 bar means no forced exit; IR-15 forbids
    substituting a neighbouring bar, so the day is disclosed."""
    _bars, _uni, ds = market()
    victim = DATES[IDX_SHORT]
    inputs = build_inputs(*market(),
                          mutate={victim: lambda pm: pm.iloc[:-1].reset_index(
                              drop=True)})
    out = build_study(ds, inputs, SCENARIOS)
    assert [d["trade_date"] for d in out["untradeable_disclosure"]] == [victim]
    assert out["untradeable_disclosure"][0]["reason"] == study.REASON_NO_EXIT_BAR
    # a day that is simply absent from the map is disclosed, not skipped
    dropped = {k: v for k, v in build_inputs(*market()).items() if k != victim}
    out2 = build_study(ds, dropped, SCENARIOS)
    assert out2["untradeable_disclosure"][0]["reason"] == (
        study.REASON_NO_DAY_INPUT)


def test_pm_bars_outside_the_frozen_window_are_refused():
    """No look-ahead by construction: study.py may only ever see the frozen §3
    [10:00, 15:44] window, so an observation-window bar in `pm_bars` — the one
    frame from which the opening-range stop could be recomputed — fails closed.
    """
    bars, uni, _ds = market()
    ctx = build_day_context(DATES[IDX_TP_BOUNDARY], bars, uni)
    leaky = pd.concat([ctx.obs_bars, ctx.pm_bars], ignore_index=True)
    with pytest.raises(StudyInputError, match="outside it"):
        StudyDayInput(trade_date=ctx.trade_date, pm_bars=leaky,
                      or_high=20030.25, or_low=19999.75, d_open=1)
    # a bar after the forced-exit minute is refused for the same reason
    tail = bars[ctx.trade_date]
    late = tail.loc[(tail["ts"].dt.hour * 60 + tail["ts"].dt.minute) >= 600]
    with pytest.raises(StudyInputError, match="outside it"):
        StudyDayInput(trade_date=ctx.trade_date, pm_bars=late.reset_index(
            drop=True), or_high=20030.25, or_low=19999.75, d_open=1)


def test_a_no_direction_day_can_never_enter_trade_construction():
    """frozen §5 — d_open == 0 is non-tradeable; the input type refuses it."""
    bars, uni, _ds = market()
    ctx = build_day_context(DATES[IDX_ZERO_DIR], bars, uni)
    with pytest.raises(StudyInputError, match="d_open must be"):
        StudyDayInput(trade_date=ctx.trade_date, pm_bars=ctx.pm_bars,
                      or_high=20015.25, or_low=19999.75, d_open=0)


def test_a_direction_disagreeing_with_the_dataset_fails_closed():
    """frozen §5 fixes ONE direction per day (sign(ret_open30)); two sources
    disagreeing is a defect, not a runtime choice."""
    _bars, _uni, ds = market()
    inputs = dict(build_inputs(*market()))
    day = DATES[IDX_TP_BOUNDARY]
    inputs[day] = replace(inputs[day], d_open=-1)
    with pytest.raises(StudyInputError, match="!= dataset d_open"):
        build_study(ds, inputs, SCENARIOS)


# ---------------------------------------------------------------------------
# determinism and the output contract
# ---------------------------------------------------------------------------

def test_two_builds_on_equal_inputs_are_equal():
    """The study layer is a pure deterministic function — no RNG lives here
    (frozen §9 bootstrap and the Appendix-A sampling are separate modules)."""
    _bars, _uni, ds = market()
    first = build_study(ds, build_inputs(*market()), SCENARIOS)
    second = build_study(ds, build_inputs(*market()), SCENARIOS)
    plain_a = {k: v for k, v in first.items() if k != "records"}
    plain_b = {k: v for k, v in second.items() if k != "records"}
    assert plain_a == plain_b
    assert json.dumps(plain_a, sort_keys=True) == json.dumps(plain_b,
                                                             sort_keys=True)
    for engine in ("E1", "E2"):
        for name in SCENARIOS:
            assert first["records"][engine][name] == second["records"][engine][
                name]


def test_the_plain_output_is_json_serializable_and_records_are_dataclasses():
    """frozen §10.1 — the atomic records stay dataclass instances for MC;
    everything else must survive a JSON round trip unchanged."""
    out = study_result()
    plain = {k: v for k, v in out.items() if k != "records"}
    assert json.loads(json.dumps(plain)) == plain
    assert set(out) >= {"thetas", "scenarios_used", "per_theta", "records",
                        "untradeable_disclosure", "determinism_note"}
    assert isinstance(out["determinism_note"], str)
    from itsf.contracts import TradePathRecord
    assert all(isinstance(r, TradePathRecord)
               for r in out["records"]["E1"]["Base"])
    with pytest.raises(TypeError):
        json.dumps(out["records"])


def test_the_study_module_holds_no_randomness_and_no_engineering_seed():
    """DR-02 isolation + the study layer's determinism guarantee: no research
    computation may reach the run-infra seed, and no RNG may live in this
    module (frozen §9 seeds {7,13,31} belong to the bootstrap layer)."""
    source = inspect.getsource(study)
    for token in ("engineering_seed", "20260731", "np.random", "numpy.random",
                  "default_rng", "RandomState", "import random", "shuffle(",
                  ".sample(", "getrandbits", "SeedSequence"):
        assert token not in source, f"{token!r} must not appear in study.py"
    assert not hasattr(study, "random")


def test_the_study_module_does_no_io_and_holds_no_mutable_state():
    """Purity discipline, mirroring tests/test_s0_context.py's PURE_MODULES
    checks (which are parametrized over context.py / dataset.py only)."""
    source = inspect.getsource(study)
    forbidden = (r"\bopen\s*\(", r"\bprint\s*\(", r"\bimport\s+os\b",
                 r"\bimport\s+io\b", r"\bimport\s+requests\b",
                 r"\bimport\s+socket\b", r"\bimport\s+subprocess\b",
                 r"\bfrom\s+pathlib\b", r"\bPath\s*\(", r"read_csv",
                 r"read_parquet", r"to_csv", r"quant-data")
    for pat in forbidden:
        hits = [ln for ln in source.splitlines()
                if re.search(pat, ln) and not ln.lstrip().startswith("#")]
        assert not hits, f"study.py: {pat} -> {hits[:3]}"
    mutable = [n for n, v in vars(study).items()
               if not n.startswith("__") and isinstance(v, (list, set, dict))]
    assert not mutable, f"mutable module-level state in study.py: {mutable}"


def test_no_parameter_can_override_a_frozen_constant():
    """The house denylist (tests/test_s0_context.py FROZEN_PARAM_DENYLIST),
    with theta handled by a STRONGER rule rather than a blanket ban.

    `theta`/`thetas` may appear only on the validated entry point
    `build_study` (which refuses anything outside the frozen pair — see
    test_a_theta_outside_the_frozen_pair_is_refused) and on `theta_key`, a
    pure str formatter that cannot reach a number. Every other callable that
    takes a theta must be module-private, i.e. it can only ever receive an
    already-validated value. That is the invariant frozen §7 L133 + §11
    (禁止参数扫描) actually need.
    """
    denylist = {"theta_primary", "theta_secondary", "adr_lookback",
                "decile_count", "era_boundary", "micro_era_boundary",
                "max_missing_fraction", "expected_rth_minutes",
                "platform_fee", "platform_fee_rt_usd", "tick", "tick_points",
                "point_value", "seed", "engineering_seed", "random_state",
                "rng", "entry_time", "forced_exit_bar_time", "budgets",
                "risk_budgets", "percentiles", "engines", "eras"}
    theta_param_allowed = {"build_study", "theta_key"}
    for name, obj in vars(study).items():
        members = []
        if inspect.isfunction(obj) and obj.__module__ == study.__name__:
            members = [(name, obj)]
        elif inspect.isclass(obj) and obj.__module__ == study.__name__:
            members = [(f"{name}.{m}", f) for m, f in vars(obj).items()
                       if inspect.isfunction(f)]
        for qual, fn in members:
            for pname in inspect.signature(fn).parameters:
                if pname.lower() in ("theta", "thetas"):
                    assert (qual in theta_param_allowed
                            or qual.startswith("_")), (
                        f"study.{qual} takes a theta but is neither the "
                        "validated entry point nor module-private")
                    continue
                assert pname.lower() not in denylist, (
                    f"study.{qual} exposes frozen constant parameter {pname}")
    default = inspect.signature(build_study).parameters["thetas"].default
    assert default is study.FROZEN_THETAS == (0.5, 0.3)
    assert isinstance(theta_key(0.5), str)      # formatter, never a number


def test_the_theta_key_helper_is_stable_and_json_safe():
    assert theta_key(0.5) == "theta_0.5"
    assert theta_key(0.3) == "theta_0.3"
    assert set(study_result()["per_theta"]) == {"theta_0.5", "theta_0.3"}


def test_frozen_constants_are_module_level_and_not_parameters():
    """The frozen grid values are constants with citations, never arguments:
    engines, era axis, budgets and the worst-day percentiles."""
    assert study.ENGINES == ("E1", "E2")
    assert study.FROZEN_THETAS == (0.5, 0.3)
    assert study.RISK_BUDGETS_USD == (50, 75, 100, 150)
    assert study.WORST_DAY_PERCENTILES == (1.0, 5.0)
    assert study.ERA_AXIS == (ERA_PROXY, ERA_ACTUAL)
    assert study.BASE_SCENARIO_NAME == "Base"
    names = set(inspect.signature(build_study).parameters)
    assert names == {"ds", "day_inputs", "scenarios", "thetas"}


def test_a_scenario_whose_key_disagrees_with_its_name_fails_closed():
    """A mislabelled scenario would silently attribute one cost regime's P&L to
    another scenario's column."""
    _bars, _uni, ds = market()
    bad = dict(SCENARIOS)
    bad["Base2"] = CostScenarioParams(name="Base", spread_points=0.5,
                                      slippage_ticks_per_side=1.0,
                                      adverse_slippage_ticks=1.0)
    with pytest.raises(ValueError, match="!= CostScenarioParams.name"):
        build_study(ds, build_inputs(*market()), bad)
