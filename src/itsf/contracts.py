"""Shared typed contracts for the ITSF S0/MC engine.

MAIN-AGENT OWNED. Subagents treat this file as READ-ONLY; interface change
requests go into their `unresolved` report for main-agent adjudication.
Field semantics mirror frozen S0 §10.1 / MC spec — do not reinterpret.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# --- MNQ instrument constants (CME) ----------------------------------------
MNQ_POINT_VALUE_USD = 2.0      # $2 per index point
MNQ_TICK_POINTS = 0.25
MNQ_TICK_VALUE_USD = 0.5

# Frozen s0_cost_handoff primary (platform_params.execution_costs)
S0_PLATFORM_FEE_RT_USD = 1.74


@dataclass
class CostScenarioParams:
    """Market-friction scenario (S0 §6). spread values are FULL bid-ask width
    in index points; each side pays spread/2 (frozen)."""
    name: str                          # Base | Conservative | Stress | Severe
    spread_points: float               # full width for the applicable minute
    slippage_ticks_per_side: float
    adverse_slippage_ticks: float      # extra for stop fills
    friction_multiplier: float = 1.0   # Stress = Base market friction x2
    platform_fee_rt_usd: float = S0_PLATFORM_FEE_RT_USD


@dataclass
class TradePathRecord:
    """Atomic per-contract intraday trade path (S0 §10.1, frozen schema)."""
    trade_date: str                    # YYYY-MM-DD (template/trading day id)
    engine: str                        # 'E1' | 'E2'
    cost_scenario: str
    direction: int                     # +1 long / -1 short (== d_open)
    entry_ts: str
    exit_ts: str
    entry_fill: float
    exit_fill: float
    final_pnl_per_contract: float      # USD, all trading costs deducted ONCE here
    mtm_close_pnl_1m: list[float] = field(default_factory=list)
    mtm_adverse_pnl_1m: list[float] = field(default_factory=list)
    max_adverse_pnl: float = 0.0
    max_favourable_pnl: float = 0.0
    time_of_max_adverse: str = ""
    planned_stop: float | None = None
    actual_stop_fill: float | None = None
    stop_triggered: bool = False
    sizing_anchor_usd: float = 0.0     # E1: actual planned stop risk incl cost;
                                       # E2: counterfactual E1 anchor (frozen)
    ambiguous_stop_vs_floor: bool = False


@dataclass
class DayFeatures:
    """S0 §4. None == NA (day stays in sample; per-table NA counts mandatory)."""
    trade_date: str
    ret_open30: float | None = None            # F1  (C0959-O0930)/ADR14
    or_width: float | None = None              # F2
    de_open30: float | None = None             # F3  close-path only
    rvol_open30: float | None = None           # F4
    gap: float | None = None                   # F5  NA on roll transition
    open_loc_on: float | None = None           # F6
    on_range: float | None = None              # F7
    retrace_open30: float | None = None        # F8  directional running-max
    close_pos_open30: float | None = None      # F9
    is_event_day: str = "none"                 # F10 CPI|NFP|FOMC|none
    is_roll_transition: bool = False           # F11
    is_roll_window: bool = False
    adr14: float | None = None
    excluded_day: bool = False                 # half-day / no-trade / >10% missing
    exclusion_reason: str = ""


@dataclass
class DayLabels:
    """S0 §5. d_open == 0 -> no-direction day (counted, not tradeable)."""
    trade_date: str
    d_open: int = 0                            # sign(ret_open30); 0 = no direction
    y_cont: float | None = None                # d_open*(C1544-O1000)/ADR14  (primary)
    y1: float | None = None                    # descriptive only
    y2_de_pm: float | None = None              # close-path
    y3_close_pos_pm: float | None = None
    y4_mfe: float | None = None                # relative to d_open from O1000
    y5_mae: float | None = None
    y6_cont_decile: int | None = None


@dataclass
class AccountEvent:
    """Emitted by platform lifecycles per simulated day."""
    day: str
    phase: str                 # evaluation | funded | combine | xfa | dead | done
    balance: float
    floor: float
    breached: bool = False
    payout_gross: float = 0.0
    payout_cash: float = 0.0   # gross*split - rail fee (payout_accounting, frozen)
    fees_usd: float = 0.0      # platform fees charged today (subs/reset/activation/...)
    notes: str = ""
