"""S0 STUDY-RECORD layer — the frozen §7/§8/§10.1/Appendix-A day sets.

M6 gap "无日集选择/编排层" (M6_DESIGN §1). This module SELECTS the day sets the
frozen text defines and DRIVES the already-frozen per-day functions over them;
it computes no frozen formula of its own. `oracle.py` / `paths.py` / `costs.py`
are KEEP / REPLACE_PROHIBITED and are only CONSUMED here, exactly as
`dataset.py` consumes `features.py` / `labels.py`.

    S0Dataset.records  +  {trade_date: StudyDayInput}  +  cost scenarios
        -> build_study(...) -> one plain dict + the §10.1 TradePathRecord set

What this layer owns (and nothing else):
  §7   dual Oracle over the continuation-event day set, θ 0.5 primary AND
       θ 0.3 secondary, BOTH fully reported, never promoted after the fact.
  §7   E1/E2 × the four §6 cost scenarios; E2's mandatory worst-day P1/P5.
  §8   the per-day integer-sizing row and the descriptive {50,75,100,150}
       coverage report.
  §10.1 the atomic per-contract TradePathRecord handoff to MC (kept as
       dataclass instances, never flattened into the JSON-side output).
  §10.5 the mandatory frequency block (base rate p, tradeable days per year,
       Oracle monthly frequency), split by the §6 era axis and pooled.
  App A D_TP / D_FP — the two empirical USD P&L distributions.

Discipline
----------
- PURE and FULLY DETERMINISTIC. Zero I/O, zero global mutable state, zero
  print, and — deliberately — ZERO randomness: the stationary bootstrap
  (frozen §9) and the Appendix-A (q, r) stratified sampling live in OTHER
  modules (`s0/stats.py`, `s0/gridmix.py`, M6_DESIGN §1). Nothing in this file
  may draw, shuffle or sample; the same inputs always produce byte-identical
  plain output and equal records.
- No parameter may override a frozen constant. `thetas` is a parameter only so
  the caller can name the frozen PAIR explicitly; it is validated to be a
  subset of {0.5, 0.3} (frozen §7 L133), because an open theta parameter would
  be exactly the "参数扫描" prohibited by frozen §11.
- No judgment. Counts, mechanical ratios and empirical distributions only; the
  GO / STOP / 边界区 reading is MC's (frozen §10.4) and never happens here.
- NO LOOK-AHEAD BY CONSTRUCTION: the only price frame this module ever sees is
  the caller's PM window [10:00, 15:44] (fail-closed in StudyDayInput), so no
  observation-window or post-exit bar can reach a trade, and the opening-range
  stop levels must be supplied by the caller (computed from the 09:30-09:59
  window alone — see `StudyDayInput.or_high` / `.or_low`).

Frozen sources (STUDY_0_PREREGISTRATION.md, tag s0-freeze-v1):
  §3     session/times: entry = 10:00 bar open, forced exit = 15:44 bar close.
  §5     d_open = sign(ret_open30); d_open == 0 -> non-tradeable, counted
         separately; Y_cont is the Oracle-deciding label.
  §6     the four cost scenarios and the two mandatory era axes.
  §7     dual Oracle, θ 0.5 primary / 0.3 secondary both fully reported;
         E1 = opening-range opposite-extreme stop, E2 = no stop + timed exit
         with a MANDATORY worst-day P1/P5 report.
  §8     the per-day integer-sizing outputs and the non-decisional
         {$50, $75, $100, $150} coverage report.
  §10.1  the atomic per-contract intraday path record (MC handoff) and the
         dual-path rules; the {$50-$150} budgets are DESCRIPTIVE ONLY.
  §10.5  mandatory frequency output.
  App A  D_TP = 交易 Y_cont >= θ 的日子; D_FP = Y_cont < θ 的日子按 SAME rules,
         direction d_open.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import time as dtime
from types import MappingProxyType
from typing import Mapping, Sequence

import numpy as np
import pandas as pd

from itsf.contracts import CostScenarioParams, TradePathRecord
from itsf.s0 import costs, oracle, paths
from itsf.s0.context import (
    PM_HI_MINUTE,
    PM_LO_MINUTE,
    require_et_timestamps,
)
from itsf.s0.dataset import (
    ERA_ACTUAL,
    ERA_PROXY,
    THETA_PRIMARY,
    THETA_SECONDARY,
    DayRecord,
    S0Dataset,
)

# --- frozen constants (never parameters) ------------------------------------
ENGINES = ("E1", "E2")                     # frozen: S0 §7 (E3 已删除)
FROZEN_THETAS = (THETA_PRIMARY, THETA_SECONDARY)   # frozen: S0 §7 L133
# MappingProxyType: immutable view, keeps the module namespace free of mutable
# containers (same discipline as dataset._LABEL_DEPS). The roles are frozen —
# 0.5 主 / 0.3 副 — and "不得事后升格" means neither may be relabelled.
THETA_ROLES = MappingProxyType({THETA_PRIMARY: "primary",
                                THETA_SECONDARY: "secondary"})
# frozen: S0 §7 — 理论 Oracle "减 Base 成本": the economic upper bound is
# defined against the Base scenario ONLY, so this name is not a parameter.
BASE_SCENARIO_NAME = "Base"
ERA_AXIS = (ERA_PROXY, ERA_ACTUAL)         # frozen: S0 §6 L109-115
POOLED = "pooled"
# frozen: S0 §8 — 非决策性风险预算 {$50, $75, $100, $150}; 不从中挑选,
# 仅供 MC (frozen: S0 §10.1 "仅保留为描述性覆盖率报告").
RISK_BUDGETS_USD = (50, 75, 100, 150)
# frozen: S0 §7 table — E2 强制报告最差日 P1/P5.
WORST_DAY_PERCENTILES = (1.0, 5.0)
# numpy's default; stated because the frozen text mandates the P1/P5 report
# without fixing an estimator. Linear interpolation between order statistics
# (numpy `method="linear"`, the historical default) is the engineering
# convention of this layer, disclosed here and in the output block.
PERCENTILE_METHOD = "linear"

DETERMINISM_NOTE = (
    "study.py is a pure deterministic function of (dataset records, day "
    "inputs, cost scenarios, thetas): no RNG, no sampling, no shuffling and "
    "no wall-clock/order dependence. Frozen §9 bootstrap resampling and the "
    "frozen Appendix-A (q, r) stratified selection are NOT performed here — "
    "they consume this output in separate modules. Repeated calls on equal "
    "inputs yield equal output."
)

# --- untradeable-disclosure reasons -----------------------------------------
# A day that the frozen definitions call tradeable but whose supplied price
# frame cannot carry the frozen §3 trade. The approved preflight reports all
# four anchors present on every structurally eligible day, so these are
# UNREACHABLE on the approved input set; they exist so that an input-side
# defect is DISCLOSED instead of silently shrinking the Oracle day set.
REASON_NO_DAY_INPUT = "day_input_not_supplied"
REASON_NO_ENTRY_BAR = "entry_1000_bar_absent"
REASON_NO_EXIT_BAR = "forced_exit_1544_bar_absent"
REASON_EXIT_BEFORE_ENTRY = "forced_exit_bar_precedes_entry_bar"
REASON_OR_LEVEL_UNUSABLE = "opening_range_extreme_unusable"

UNTRADEABLE_REASONS = (REASON_NO_DAY_INPUT, REASON_NO_ENTRY_BAR,
                       REASON_NO_EXIT_BAR, REASON_EXIT_BEFORE_ENTRY,
                       REASON_OR_LEVEL_UNUSABLE)


class StudyInputError(ValueError):
    """A study input contradicts the dataset or the frozen §3 trade shape."""


# ===========================================================================
# per-day trade construction input
# ===========================================================================

@dataclass(frozen=True, eq=False)
class StudyDayInput:
    """Everything ONE day's trade construction needs, and nothing else.

    Keeping this dataclass — rather than a loader handle — as the input keeps
    study.py pure and makes the no-look-ahead boundary structural:

    pm_bars : the caller's PM window, i.e. every 1-minute bar whose START
        minute lies in [10:00, 15:44] (frozen §3 entry bar through forced-exit
        bar; the exact shape of `DayContext.pm_bars`). Bars outside that span
        are REFUSED, so no observation-window bar and no post-exit bar can
        reach a fill, a mark or a stop test. Absent minutes stay absent
        (IR-15): a missing 10:00 or 15:44 bar is disclosed, never substituted.
    or_high / or_low : the 09:30-09:59 opening-range extremes — E1's live
        initial stop is the OPPOSITE extreme (frozen §7), and the same level
        is E2's counterfactual sizing anchor (frozen MC §3). They are supplied
        by the caller BECAUSE they must be computed from the observation
        window alone; this module never sees a pre-10:00 bar and therefore
        cannot derive (or accidentally contaminate) them.
    d_open : the frozen §5 direction of the day. Cross-checked against the
        dataset's own label in build_study — two sources disagreeing about a
        frozen definition is a defect, not something to resolve at runtime.
    """
    trade_date: str
    pm_bars: pd.DataFrame
    or_high: float
    or_low: float
    d_open: int

    def __post_init__(self) -> None:
        if self.d_open not in (1, -1):
            # frozen: S0 §5 — d_open == 0 is a non-tradeable no-direction day
            # and never reaches trade construction.
            raise StudyInputError(
                f"{self.trade_date}: d_open must be +1 or -1 (frozen §5 "
                f"no-direction days are not tradeable), got {self.d_open!r}")
        bars = self.pm_bars
        if bars is None:
            raise StudyInputError(f"{self.trade_date}: pm_bars is required")
        if len(bars) > 0:
            # frozen: S0 §3 L41-43 — every minute-of-day window in this study
            # is read off a tz-aware America/New_York stamp; a UTC frame would
            # silently relabel 10:00 and still produce a full record set.
            require_et_timestamps(bars)
            minutes = (bars["ts"].dt.hour * 60
                       + bars["ts"].dt.minute).to_numpy(dtype=int)
            outside = minutes[(minutes < PM_LO_MINUTE)
                              | (minutes > PM_HI_MINUTE)]
            if len(outside):
                raise StudyInputError(
                    f"{self.trade_date}: pm_bars must hold ONLY the frozen §3 "
                    f"[10:00, 15:44] window; {len(outside)} bar(s) outside it "
                    f"(first offending minute-of-day {int(outside[0])}) — "
                    "fail closed (no-look-ahead boundary)")
            object.__setattr__(self, "pm_bars",
                               bars.sort_values("ts").reset_index(drop=True))

    # --- structural usability (never a silent skip) ------------------------

    def bar_times(self) -> set[dtime]:
        if len(self.pm_bars) == 0:
            return set()
        return {ts.time() for ts in self.pm_bars["ts"]}

    def defect_reason(self) -> str | None:
        """The disclosure reason, or None when the frozen §3 trade is buildable."""
        times = self.bar_times()
        if paths.ENTRY_TIME not in times:
            return REASON_NO_ENTRY_BAR
        if paths.FORCED_EXIT_BAR_TIME not in times:
            return REASON_NO_EXIT_BAR
        if (paths.bar_index_at(self.pm_bars, paths.FORCED_EXIT_BAR_TIME)
                < paths.bar_index_at(self.pm_bars, paths.ENTRY_TIME)):
            return REASON_EXIT_BEFORE_ENTRY
        if not (np.isfinite(self.or_high) and np.isfinite(self.or_low)):
            return REASON_OR_LEVEL_UNUSABLE
        if self.or_high < self.or_low:
            return REASON_OR_LEVEL_UNUSABLE
        return None

    @property
    def anchor_stop(self) -> float:
        """E1's live stop / E2's counterfactual anchor: the OPPOSITE opening-
        range extreme (frozen: S0 §7; MC §3 — same level under both engines)."""
        return float(self.or_low) if self.d_open == 1 else float(self.or_high)


# ===========================================================================
# small deterministic helpers
# ===========================================================================

def theta_key(theta: float) -> str:
    """Stable JSON-safe key for a frozen theta ("theta_0.5" / "theta_0.3")."""
    return f"theta_{theta:g}"


def _percentile(values: Sequence[float], q: float) -> float | None:
    if not len(values):
        return None
    return float(np.percentile(np.asarray(values, dtype=float), q,
                               method=PERCENTILE_METHOD))


def _worst_day_percentiles(values: Sequence[float]) -> dict[str, float | None]:
    """frozen: S0 §7 table — 强制报告最差日 P1/P5 (E2)."""
    return {f"P{q:g}": _percentile(values, q) for q in WORST_DAY_PERCENTILES}


def _series_block(pairs: Sequence[tuple[str, float]],
                  value_key: str = "daily_pnl_usd") -> dict[str, object]:
    """(trade_date, USD) pairs -> a plain, JSON-safe descriptive block."""
    vals = [float(v) for _d, v in pairs]
    total = float(sum(vals)) if vals else 0.0
    return {
        "n": len(pairs),
        value_key: [[d, float(v)] for d, v in pairs],
        "sum_usd": total,
        "mean_usd": (total / len(vals)) if vals else None,
        "min_usd": min(vals) if vals else None,
        "max_usd": max(vals) if vals else None,
        "worst_day_pnl_percentiles": _worst_day_percentiles(vals),
    }


def _by_era_and_pooled(pairs_by_date: Sequence[tuple[str, float]],
                       era_of: Mapping[str, str],
                       value_key: str = "daily_pnl_usd",
                       ) -> dict[str, object]:
    """frozen: S0 §6 L109-115 — the two era axes are reported SEPARATELY, and
    the pooled figure never replaces them."""
    out: dict[str, object] = {
        POOLED: _series_block(pairs_by_date, value_key),
        "by_era": {era: _series_block(
            [(d, v) for d, v in pairs_by_date if era_of[d] == era], value_key)
            for era in ERA_AXIS},
    }
    return out


# ===========================================================================
# day universe (frozen §5 direction + Appendix A D_TP / D_FP definitions)
# ===========================================================================

def is_direction_tradeable(record: DayRecord) -> bool:
    """frozen: S0 §5 + App A — a day can carry an Oracle trade iff it has a
    direction (d_open in {+1,-1}) AND its deciding label Y_cont exists.

    Identical to `DayRecord.oracle_candidate`; written out because these two
    conditions are the Appendix-A population definition and must be readable
    at the place that uses them.
    """
    return record.labels.d_open in (1, -1) and record.labels.y_cont is not None


def _partition(records: Sequence[DayRecord], theta: float,
               ) -> tuple[list[str], list[str]]:
    """frozen: App A — D_TP days = Y_cont >= θ, D_FP days = Y_cont < θ.

    The boundary is INCLUSIVE on the TP side: 延续事件 = Y_cont >= θ
    (frozen §7 L133), so Y_cont == θ is a continuation event.
    """
    tp = [r.trade_date for r in records if float(r.labels.y_cont) >= theta]
    fp = [r.trade_date for r in records if float(r.labels.y_cont) < theta]
    return tp, fp


# ===========================================================================
# §8 per-day integer-sizing row
# ===========================================================================

def _sizing_row(rec: TradePathRecord, inp: StudyDayInput,
                day: DayRecord, scenario: CostScenarioParams,
                ) -> dict[str, object]:
    """frozen: S0 §8 — 逐日输出 stop_distance_points / risk planned / risk
    realized / cost / cost_as_pct_of_R / minimum_1_contract_risk.

    stop_distance_points
        |entry_fill - stop level| in index points. The stop level is E1's live
        stop and, under E2, the SAME opening-range level read as the
        counterfactual anchor (frozen MC §3) — E2 stores `planned_stop = None`
        because it places no order, so the level is reconstructed from the very
        input `sizing_anchor_usd` was computed from, never re-derived from a
        price path.
    risk_usd_per_1_MNQ_planned
        = record.sizing_anchor_usd (normal stop touch + adverse exit friction +
        the platform fee once). Frozen §8 "正常 stop 成交＋成本".
    risk_usd_per_1_MNQ_realized
        Frozen §8 "含 gap 穿越真实损失" — only a trade that ACTUALLY exited on
        its stop has a realized stop loss, so this is populated exactly on E1
        days with stop_triggered and is the realized per-contract loss
        (-final_pnl_per_contract, gap-through and the fee included). It is
        None everywhere else: E2 places no stop, and an unstopped E1 day never
        realized its planned risk. None here means "not applicable", never 0.
    cost_usd_per_1_MNQ
        costs.round_turn_cost_usd for the scenario, priced with the ADVERSE
        exit side exactly when the trade exited on its stop.
    cost_as_pct_of_R
        cost / risk_usd_per_1_MNQ_planned. A non-positive planned risk cannot
        occur while the opening-range extreme lies on the far side of the entry
        fill; if it ever does, the ratio is None and the row is flagged rather
        than dividing (the frozen text defines no value there).
    minimum_1_contract_risk
        the 1-contract floor = the planned per-contract risk (frozen §8; the
        sizing decision itself belongs to MC, frozen §10.1 仓位逻辑归属).
    """
    stop_level = inp.anchor_stop
    if rec.engine == "E1" and rec.planned_stop is not None:
        if float(rec.planned_stop) != stop_level:
            raise StudyInputError(
                f"{rec.trade_date}: E1 planned_stop {rec.planned_stop} does "
                f"not match the opening-range opposite extreme {stop_level} "
                "— fail closed (frozen §7 stop definition)")
    planned = float(rec.sizing_anchor_usd)
    stop_exit = bool(rec.stop_triggered)
    cost = float(costs.round_turn_cost_usd(scenario, stop_exit=stop_exit))
    realized = (-float(rec.final_pnl_per_contract)
                if (rec.engine == "E1" and stop_exit) else None)
    nonpositive = planned <= 0.0
    return {
        "trade_date": rec.trade_date,
        "engine": rec.engine,
        "cost_scenario": rec.cost_scenario,
        "direction": int(rec.direction),
        "era": day.era,
        "year": day.year,
        "stop_level_points": stop_level,
        "counterfactual_anchor": rec.engine == "E2",   # frozen: MC §3
        "stop_distance_points": abs(float(rec.entry_fill) - stop_level),
        "risk_usd_per_1_MNQ_planned": planned,
        "risk_usd_per_1_MNQ_realized": realized,
        "cost_usd_per_1_MNQ": cost,
        "cost_as_pct_of_R": (None if nonpositive else cost / planned),
        "minimum_1_contract_risk": planned,
        "stop_triggered": stop_exit,
        "nonpositive_planned_risk": nonpositive,
    }


def _coverage(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    """frozen: S0 §8 + §10.1 — DESCRIPTIVE coverage under the non-decisional
    {$50, $75, $100, $150} budgets. No budget is selected here and none feeds
    any computation; S0 no longer pre-generates fixed position vectors
    (frozen §10.1 仓位逻辑归属)."""
    n = len(rows)
    out: dict[str, object] = {
        "n_trades": n,
        "note": ("descriptive only (frozen §8 '不从中挑选,仅供 MC' + §10.1 "
                 "'仅保留为描述性覆盖率报告'); never an input to sizing, "
                 "feasibility or any verdict"),
        "by_budget_usd": {},
    }
    for budget in RISK_BUDGETS_USD:
        covered = sum(1 for r in rows
                      if float(r["risk_usd_per_1_MNQ_planned"]) <= budget)
        out["by_budget_usd"][str(budget)] = {
            "n_covered": covered,
            "fraction": (covered / n) if n else None,
        }
    return out


# ===========================================================================
# §10.5 frequency block
# ===========================================================================

def _frequency_cell(slice_records: Sequence[DayRecord],
                    tradeable: frozenset[str], traded: frozenset[str],
                    tp_labelled: frozenset[str], tp_traded: frozenset[str],
                    ) -> dict[str, object]:
    """frozen: S0 §10.5 — 延续事件基础率 p, 每年可交易日数, Oracle 月均频率.

    DENOMINATOR (stated precisely, per frozen §5 + §10.5): p = N_TP /
    N_directional_tradeable, where N_directional_tradeable counts the days of
    this slice that have BOTH a direction (d_open in {+1,-1}, frozen §5 — the
    d_open == 0 and undeterminable classes are excluded and reported
    separately by dataset.py) AND a computable Y_cont. It is a LABEL
    population: input-side defects (the untradeable disclosure) do not shrink
    it, because the continuation base rate is a property of the label
    distribution, not of one archive's bar availability.

    Numerator, both readings reported because the frozen text does not
    contemplate a labelled day whose price frame cannot carry the trade:
      n_continuation_days_labelled  — every tradeable day with Y_cont >= θ;
      n_continuation_days_traded    — those that actually produced a trade.
    They are EQUAL whenever the untradeable disclosure is empty, which the
    approved preflight guarantees on the real archive.
    """
    dates = {r.trade_date for r in slice_records}
    months = sorted({r.trade_date[:7] for r in slice_records})
    n_dir = len(dates & tradeable)
    n_lab = len(dates & tp_labelled)
    n_trd = len(dates & tp_traded)
    n_traded_days = len(dates & traded)
    return {
        "n_days_in_sample": len(dates),
        "n_directional_tradeable": n_dir,
        "n_trade_constructible": n_traded_days,
        "n_continuation_days_labelled": n_lab,
        "n_continuation_days_traded": n_trd,
        "continuation_base_rate_p": (n_lab / n_dir) if n_dir else None,
        "continuation_base_rate_p_traded_only": (
            (n_trd / n_dir) if n_dir else None),
        "n_months_in_slice": len(months),
        "oracle_monthly_frequency": (n_trd / len(months)) if months else None,
        "oracle_monthly_frequency_labelled": (
            (n_lab / len(months)) if months else None),
    }


def _frequency_block(records: Sequence[DayRecord], tradeable: frozenset[str],
                     traded: frozenset[str], tp_labelled: frozenset[str],
                     tp_traded: frozenset[str]) -> dict[str, object]:
    by_year: dict[str, list[DayRecord]] = {}
    for r in records:
        by_year.setdefault(r.year, []).append(r)

    def cell(rows: Sequence[DayRecord]) -> dict[str, object]:
        return _frequency_cell(rows, tradeable, traded, tp_labelled, tp_traded)

    return {
        "denominator_definition": (
            "N_directional_tradeable = days with d_open in {+1,-1} (frozen §5) "
            "AND a computable Y_cont (frozen §5 label table); equals "
            "DayRecord.oracle_candidate. Input-side untradeable disclosures "
            "stay IN this denominator."),
        "note": ("frozen §10.5 mandatory frequency output: 基础率 p, 每年可交易"
                 "日数 (by_year.n_directional_tradeable), Oracle 月均频率. "
                 "Appendix-A grid trade counts F(q,r) are produced downstream."),
        POOLED: cell(records),
        "by_era": {era: cell([r for r in records if r.era == era])
                   for era in ERA_AXIS},
        "by_year": {y: cell(rows) for y, rows in sorted(by_year.items())},
    }


# ===========================================================================
# entry point
# ===========================================================================

def _validate_thetas(thetas: Sequence[float]) -> tuple[float, ...]:
    """frozen: S0 §7 L133 + §11 — θ 主 0.5、副 0.3, both fully reported.

    `thetas` selects from the frozen PAIR and can never introduce a third
    threshold: an open theta parameter would be a 参数扫描 surface, which
    frozen §11 prohibits outright.
    """
    values = tuple(float(t) for t in thetas)
    if not values:
        raise ValueError("thetas must not be empty (frozen §7 reports both)")
    if len(set(values)) != len(values):
        raise ValueError(f"duplicate theta in {values}")
    unknown = [t for t in values if t not in FROZEN_THETAS]
    if unknown:
        raise ValueError(
            f"theta {unknown} is not a frozen value; the frozen pair is "
            f"{FROZEN_THETAS} (S0 §7 L133) and §11 prohibits parameter scans")
    return values


def _validate_scenarios(scenarios: Mapping[str, CostScenarioParams]) -> None:
    """frozen: S0 §6 scenario grid + §7 (理论 Oracle 减 Base 成本)."""
    if not scenarios:
        raise ValueError("at least one cost scenario is required (frozen §6)")
    for name, scn in scenarios.items():
        if not isinstance(scn, CostScenarioParams):
            raise TypeError(f"scenario {name!r} is not a CostScenarioParams")
        if scn.name != name:
            raise ValueError(
                f"scenario key {name!r} != CostScenarioParams.name {scn.name!r}")
    if BASE_SCENARIO_NAME not in scenarios:
        raise ValueError(
            f"the {BASE_SCENARIO_NAME!r} scenario is required: frozen §7 "
            "defines the theoretical Oracle upper bound net of BASE costs")


def _collect_day_inputs(records: Sequence[DayRecord],
                        day_inputs: Mapping[str, StudyDayInput],
                        ) -> tuple[list[tuple[DayRecord, StudyDayInput]],
                                   list[dict[str, object]]]:
    """Split the frozen-tradeable population into constructible trades and the
    DISCLOSED remainder. A tradeable day is never silently skipped."""
    usable: list[tuple[DayRecord, StudyDayInput]] = []
    disclosure: list[dict[str, object]] = []
    for day in records:
        inp = day_inputs.get(day.trade_date)
        if inp is None:
            reason: str | None = REASON_NO_DAY_INPUT
        else:
            if inp.trade_date != day.trade_date:
                raise StudyInputError(
                    f"day_inputs[{day.trade_date!r}].trade_date is "
                    f"{inp.trade_date!r} — fail closed")
            if inp.d_open != day.labels.d_open:
                # frozen §5 fixes ONE direction per day; two sources
                # disagreeing is a defect, never a runtime choice.
                raise StudyInputError(
                    f"{day.trade_date}: day_input d_open {inp.d_open} != "
                    f"dataset d_open {day.labels.d_open} (frozen §5 "
                    "d_open = sign(ret_open30)) — fail closed")
            reason = inp.defect_reason()
        if reason is None:
            usable.append((day, inp))
        else:
            disclosure.append({
                "trade_date": day.trade_date,
                "year": day.year,
                "era": day.era,
                "d_open": int(day.labels.d_open),
                "y_cont": float(day.labels.y_cont),
                "reason": reason,
            })
    return usable, disclosure


def build_study(ds: S0Dataset,
                day_inputs: Mapping[str, StudyDayInput],
                scenarios: Mapping[str, CostScenarioParams],
                thetas: Sequence[float] = FROZEN_THETAS,
                ) -> dict[str, object]:
    """Build the S0 study record. Pure, deterministic, judgment-free.

    Parameters
    ----------
    ds
        The assembled S0Dataset; only `ds.records` is read (trade_date / year /
        era / labels.d_open / labels.y_cont).
    day_inputs
        trade_date -> StudyDayInput for every frozen-tradeable day. Days that
        are tradeable by the frozen definitions but whose input cannot carry
        the frozen §3 trade are DISCLOSED (never dropped) and excluded from
        both the D_TP and D_FP sets.
    scenarios
        name -> CostScenarioParams, the frozen §6 grid (Base required).
    thetas
        A subset of the frozen pair (0.5 primary, 0.3 secondary); both are
        reported in full and neither is ever promoted after the fact.

    Returns
    -------
    A plain JSON-serializable dict EXCEPT for `["records"]`, which holds the
    frozen §10.1 TradePathRecord dataclass instances for the MC handoff.
    """
    _validate_scenarios(scenarios)
    theta_values = _validate_thetas(thetas)
    scenario_names = tuple(scenarios)

    records_sorted = sorted(ds.records, key=lambda r: r.trade_date)
    tradeable_days = [r for r in records_sorted if is_direction_tradeable(r)]
    usable, disclosure = _collect_day_inputs(tradeable_days, day_inputs)

    era_of = {r.trade_date: r.era for r in records_sorted}
    day_of = {d.trade_date: d for d, _i in usable}
    input_of = {d.trade_date: i for d, i in usable}
    tradeable_set = frozenset(r.trade_date for r in tradeable_days)
    traded_set = frozenset(day_of)

    # --- frozen §10.1 atomic records: EVERY constructible day, both engines,
    # every scenario (TP and FP alike — Appendix A trades D_FP days under the
    # SAME rules and the same d_open).
    trade_records: dict[str, dict[str, list[TradePathRecord]]] = {}
    pnl_of: dict[tuple[str, str], dict[str, float]] = {}
    for engine in ENGINES:
        trade_records[engine] = {}
        for name in scenario_names:
            scn = scenarios[name]
            built: list[TradePathRecord] = []
            pnl: dict[str, float] = {}
            for day, inp in usable:
                rec = oracle.executable_run(inp.pm_bars, inp.d_open, engine,
                                            scn, inp.or_high, inp.or_low)
                built.append(rec)
                pnl[day.trade_date] = float(rec.final_pnl_per_contract)
            trade_records[engine][name] = built
            pnl_of[(engine, name)] = pnl

    # --- frozen §7 theoretical Oracle: Base scenario only, and ONLY on
    # continuation-event days (Oracle 只在延续事件日交易) — the union of the
    # requested thetas' TP sets, computed once because it depends on neither
    # the engine nor the scenario grid.
    base_scn = scenarios[BASE_SCENARIO_NAME]
    tp_by_theta = {t: _partition(tradeable_days, t) for t in theta_values}
    theoretical_union = {d for tp, _fp in tp_by_theta.values() for d in tp
                         if d in traded_set}
    theoretical_usd = {
        d: float(oracle.theoretical_oracle(input_of[d].pm_bars,
                                           input_of[d].d_open, base_scn))
        for d in sorted(theoretical_union)}

    per_theta: dict[str, object] = {}
    for theta in theta_values:
        tp_all, fp_all = tp_by_theta[theta]
        tp_days = [d for d in tp_all if d in traded_set]
        fp_days = [d for d in fp_all if d in traded_set]
        tp_set = frozenset(tp_days)

        universe = {
            "theta": theta,
            "n_directional_tradeable": len(tradeable_days),
            "n_trade_constructible": len(usable),
            "n_untradeable_disclosed": len(disclosure),
            "n_tp": len(tp_days),
            "n_fp": len(fp_days),
            "n_tp_labelled": len(tp_all),
            "n_fp_labelled": len(fp_all),
            "tp_days": list(tp_days),
            "fp_days": list(fp_days),
            "conservation": {
                # nothing is silently dropped, under either reading
                "tradeable_equals_constructible_plus_disclosed":
                    len(tradeable_days) == len(usable) + len(disclosure),
                "constructible_equals_tp_plus_fp":
                    len(usable) == len(tp_days) + len(fp_days),
                "tradeable_equals_tp_plus_fp_plus_disclosed":
                    len(tradeable_days) == (len(tp_days) + len(fp_days)
                                            + len(disclosure)),
                "labelled_equals_tp_plus_fp":
                    len(tradeable_days) == len(tp_all) + len(fp_all),
            },
            "definition": (
                "frozen App A / §7 L133: D_TP = tradeable days with "
                "Y_cont >= θ (boundary inclusive — Y_cont == θ IS a "
                "continuation event); D_FP = tradeable days with Y_cont < θ, "
                "traded under the SAME rules in direction d_open."),
        }

        # --- §7 theoretical Oracle over the TP days, Base costs only
        theo_pairs = [(d, theoretical_usd[d]) for d in tp_days]
        theoretical = {
            "scenario": BASE_SCENARIO_NAME,
            "note": ("frozen §7 — ECONOMIC UPPER BOUND ONLY: 10:00 entry, exit "
                     "at the most favourable in-window price, minus BASE "
                     "costs. Never an executable result and never compared to "
                     "a strategy claim."),
            **_by_era_and_pooled(theo_pairs, era_of, "daily_usd"),
        }

        executable: dict[str, dict[str, object]] = {}
        sizing_rows: dict[str, dict[str, list[dict[str, object]]]] = {}
        coverage: dict[str, dict[str, object]] = {}
        d_tp: dict[str, dict[str, dict[str, float]]] = {}
        d_fp: dict[str, dict[str, dict[str, float]]] = {}
        for engine in ENGINES:
            executable[engine] = {}
            sizing_rows[engine] = {}
            coverage[engine] = {}
            d_tp[engine] = {}
            d_fp[engine] = {}
            for name in scenario_names:
                pnl = pnl_of[(engine, name)]
                pairs = [(d, pnl[d]) for d in tp_days]
                block = _by_era_and_pooled(pairs, era_of)
                block["worst_day_report"] = {
                    # frozen: S0 §7 table — the P1/P5 worst-day report is
                    # MANDATORY for E2 (no stop); the same statistic is shown
                    # for E1 as a symmetric descriptive, not as a frozen
                    # requirement.
                    "frozen_mandatory": engine == "E2",
                    "percentile_estimator": (
                        f"numpy.percentile(method={PERCENTILE_METHOD!r}) — "
                        "linear interpolation between order statistics; the "
                        "frozen text mandates the P1/P5 report without fixing "
                        "an estimator, so this choice is disclosed."),
                    POOLED: block[POOLED]["worst_day_pnl_percentiles"],
                    "by_era": {era: block["by_era"][era][
                        "worst_day_pnl_percentiles"] for era in ERA_AXIS},
                }
                executable[engine][name] = block

                rows = [_sizing_row(rec, input_of[rec.trade_date],
                                    day_of[rec.trade_date], scenarios[name])
                        for rec in trade_records[engine][name]
                        if rec.trade_date in tp_set]
                sizing_rows[engine][name] = rows
                coverage[engine][name] = _coverage(rows)

                # frozen App A — the two empirical USD P&L distributions
                d_tp[engine][name] = {d: pnl[d] for d in tp_days}
                d_fp[engine][name] = {d: pnl[d] for d in fp_days}

        per_theta[theta_key(theta)] = {
            "theta": theta,
            "theta_role": THETA_ROLES.get(theta, "unlisted"),
            "day_universe": universe,
            "theoretical_oracle": theoretical,
            "executable": executable,
            "sizing_rows": sizing_rows,
            "sizing_coverage": coverage,
            "frequency": _frequency_block(
                records_sorted, tradeable_set, traded_set,
                frozenset(tp_all), frozenset(tp_days)),
            "d_tp": d_tp,
            "d_fp": d_fp,
        }

    return {
        "thetas": [float(t) for t in theta_values],
        "theta_roles": {theta_key(t): THETA_ROLES.get(t, "unlisted")
                        for t in theta_values},
        "scenarios_used": list(scenario_names),
        "engines": list(ENGINES),
        "eras": list(ERA_AXIS),
        "day_universe": {
            "n_records": len(records_sorted),
            "n_directional_tradeable": len(tradeable_days),
            "n_trade_constructible": len(usable),
            "n_untradeable_disclosed": len(disclosure),
            "trade_constructible_days": [d.trade_date for d, _i in usable],
            "by_era": {era: {
                "n_records": sum(1 for r in records_sorted if r.era == era),
                "n_directional_tradeable": sum(
                    1 for r in tradeable_days if r.era == era),
                "n_trade_constructible": sum(
                    1 for d, _i in usable if d.era == era),
            } for era in ERA_AXIS},
        },
        # frozen §10.1 — the ATOMIC MC handoff, kept as dataclass instances on
        # purpose: flattening the two 1-minute arrays into the plain report
        # would lose the record identity MC consumes.
        "records": trade_records,
        "untradeable_disclosure": disclosure,
        "per_theta": per_theta,
        "determinism_note": DETERMINISM_NOTE,
    }
