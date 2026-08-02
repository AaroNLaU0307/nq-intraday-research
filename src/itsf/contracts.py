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

# IR DR-02 (Aaron 2026-08-01, Codex baseline audit): the ONLY seeds any
# research-path RNG may derive from.  # frozen: S0 §9 (Primary bootstrap
# seeds {7,13,31}), S0 Appendix A step 3, MC_METHOD_SPEC §(b) three master
# seeds. The engineering seed (RunConfig.engineering_seed) must NEVER reach
# a research computation.
RESEARCH_BOOTSTRAP_SEEDS: tuple[int, int, int] = (7, 13, 31)


@dataclass(frozen=True)
class ResolvedS0Methods:
    """M6.1 E1 — the SINGLE source of truth for post-freeze method rulings.

    One field per open ruling; None == still pending. The live pending list
    is DERIVED from the None fields (there is no second hand-written
    pending tuple anywhere). ready() and compute() must consume the same
    instance. No field may carry a hidden default value for an unruled
    method — a ruling lands ONLY by the main agent writing the approved
    value here together with its IR reference.
    """
    spread_scalar_rule: str | None = None          # DR-M6-A-v2
    adverse_slippage_final: object | None = None   # IR-7 final ticks vector
    volatility_regime: object | None = None        # DR-M6-B-v2 definition
    fp_allocation_basis: str | None = None         # DR-M6-C
    bootstrap_population: str | None = None        # DR-M6-D
    grid_repeat_policy: object | None = None       # DR-M6-E (K/RNG/conv)
    event_na_stratum_rule: str | None = None       # DR-M6-F

    def pending_fields(self) -> tuple[str, ...]:
        from dataclasses import fields as _fields
        return tuple(sorted(f.name for f in _fields(self)
                            if getattr(self, f.name) is None))

    @property
    def fully_resolved(self) -> bool:
        return not self.pending_fields()


@dataclass(frozen=True)
class StudyConfig:
    """M6.1 E1 — named injectable bundle for the full study chain.

    No positional tuples, no hidden defaults for unruled methods: a
    synthetic caller must supply every method-bearing field explicitly.
    Lives here (a real package module) rather than in the spec-loaded
    entrypoint so dataclass annotation resolution is well-defined.
    """
    spread_scalars: tuple[float, float, float]
    regime_of: object                       # Callable[[date_str], str]
    pending_decisions: tuple[str, ...]      # REQUIRED (O7): no default
    # DR-M6-B-v2: the ruled vol-tercile mapping (Callable[[date], str]).
    # None == unruled -> stability vol axis reports unresolved and formal
    # sealing fails (E4). Synthetic resolved-state tests must supply it.
    vol_axis_of: object | None = None


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
    max_favourable_pnl: float = 0.0    # diagnostic_only: true (IR-2) — never an
                                       # input to oracle labels, costs,
                                       # feasibility or the verdict table
    time_of_max_adverse: str = ""
    planned_stop: float | None = None
    actual_stop_fill: float | None = None
    stop_triggered: bool = False
    sizing_anchor_usd: float = 0.0     # E1: actual planned stop risk incl cost;
                                       # E2: counterfactual E1 anchor (frozen)
    ambiguous_stop_vs_floor: bool = False


@dataclass
class DayFeatures:
    """S0 §4. None == NA (day stays in sample; per-table NA counts mandatory).

    is_event_day (F10): frozen categories {CPI, NFP, FOMC, none}; ``None``
    == NA for multi-event days per IR-12 + IR-18 (primary conflict detected
    AFTER IR-13 eligibility; the multi-hot detail lives only in the
    diagnostic sidecar, never here). Added 2026-07-31 (M5-T0): the previous
    4-string closed set could not express the approved NA state.
    """
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
    is_event_day: str | None = "none"          # F10 CPI|NFP|FOMC|none|None=NA(IR-12/18)
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


# --- M5 runner shared contracts (MAIN-AGENT OWNED, added 2026-07-31) --------
# SA-4 / SA-5 depend on these EXACT names; interface change requests go to
# `unresolved`, never edited in place by a subagent.

from enum import Enum


class RunStage(str, Enum):
    """Authorization-packet §7 stages. Transition order is strict."""
    A_PRECHECK = "A_PRECHECK"                # mechanical gates (packet §9)
    B_LOAD_VALIDATE = "B_LOAD_VALIDATE"      # structural checks vs assertions
    C_COMPUTE = "C_COMPUTE"                  # exposure begins at entry (atomic)
    D_INTEGRITY = "D_INTEGRITY"              # NA conservation etc.
    E_REPORT = "E_REPORT"
    F_SEALED = "F_SEALED"


class TrialState(str, Enum):
    """Packet §0 state machine; transitions appended to ops/TRIAL_REGISTRY.md
    by the MAIN AGENT ONLY (append-only event chain)."""
    PACKET_DRAFTED = "PACKET_DRAFTED"
    PACKET_APPROVED = "PACKET_APPROVED"
    RUNNER_IMPLEMENTED = "RUNNER_IMPLEMENTED"
    READY_FOR_RUN_AUTHORIZATION = "READY_FOR_RUN_AUTHORIZATION"
    RUN_AUTHORIZED = "RUN_AUTHORIZED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# Approved NA reasons (frozen L44-45 + IR-12/15/17/18/19/20 + preflight
# taxonomy). Stage D conserves produced NA counts against EXACTLY this set;
# any NA/NaN with an unlisted reason is a hard failure (packet §7).
APPROVED_NA_REASONS = (
    "adr14_warmup",                      # F1/F2/F5/F7 normalisation warm-up
    "f4_lookback_warmup",                # IR-20 60-day basis warm-up
    "roll_transition_day_na",            # F5 on is_roll_transition (frozen L57)
    "prev_rth_close_anchor_missing",     # IR-19 (incl. early-close-bar-absent,
                                         #   vendor-degraded, first sample day)
    "anchor_missing",                    # exact anchor absent (frozen L44-45)
    "multi_event_day_f10_na",            # IR-12 + IR-18 (9 days)
    "zero_direction_day_l82",            # ret_open30 == 0 (frozen L82)
    "direction_undeterminable_na",       # ret_open30 NA -> d_open 0 (labels.py)
    "overnight_window_empty",            # F6/F7 no bars in span
    "overnight_range_zero",              # F6 0/0 (ruling R3)
    "path_zero",                         # F3 denominator (frozen L77 analogue)
    "degenerate_window",                 # F9 H == L
    "official_time_unavailable_in_archived_source",  # IR-17 (diagnostic col)
)


class RunGateError(RuntimeError):
    """A packet-§9 hard gate failed in Stage A/B (pre-exposure)."""


class InputDataDefectError(RuntimeError):
    """IR-22: a required input value is structurally defective (e.g.
    non-finite opening-window volume). Stage-B STOP — never a day-level NA
    the run may continue past."""


class NAConservationError(RuntimeError):
    """Stage D: produced NA does not conserve against APPROVED_NA_REASONS."""


class AssertionMismatchError(RuntimeError):
    """Independently computed value != expected_preflight_assertions entry.
    Assertions are compare-only; they must NEVER feed computation."""


class LogLeakError(RuntimeError):
    """Stage-C log guard: research vocabulary or non-whitelisted numeric."""


@dataclass(frozen=True)
class RunConfig:
    """Injected by the MAIN-AGENT entrypoint from approved artifacts at run
    time. Frozen dataclass: no runtime mutation; NO preflight observation
    numbers may be embedded here (they live in the assertions FILE and are
    compare-only)."""
    trial_id: str                         # e.g. S0-T001
    authorized_commit: str                # full 40-hex from Aaron's sentence
    # DR-02: run-infra provenance stamp ONLY (recorded in run metadata).
    # NEVER a research RNG seed — research randomness derives exclusively
    # from RESEARCH_BOOTSTRAP_SEEDS (7/13/31, frozen S0 §9/App A).
    engineering_seed: int
    attempts_dir: str                     # attempts/<trial>-A<seq>_<UTC>/
    runs_dir: str                         # runs/<trial>_<UTC>/ (Stage C entry)
    assertions_path: str                  # expected_preflight_assertions json


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
