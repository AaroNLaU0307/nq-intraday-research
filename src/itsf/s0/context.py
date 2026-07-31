"""S0 per-day CONTEXT assembly — the inputs of features.py / labels.py.

M5-T1 gap #1 (SA-4). This module owns the *calendar / eligibility / lookback*
layer that the frozen formula modules deliberately do not do:

    bars + schedule + event table + roll mapping  ->  DayContext
    DayContext.feature_kwargs()  ->  features.compute_day_features(**kwargs)
    DayContext.o1000 / .pm_bars  ->  labels.compute_day_labels(...)

`features.py`, `labels.py`, `oracle.py`, `costs.py`, `paths.py` are KEEP /
REPLACE_PROHIBITED (M5_T0_INTERFACE_AUDIT.md): this module CONSUMES them and
never restates a frozen formula.

Discipline (task spec section C):
- PURE. Zero file/network I/O, zero global mutable state, zero print, zero
  randomness. Every input is injected by the caller; the same inputs always
  produce the same outputs.
- No real market data is read here. The caller (main-agent runner) is the only
  place a real archive is opened, behind ``itsf.guards.assert_real_run_allowed``.
- No parameter may override a frozen constant: lookback lengths, window
  boundaries, exclusion thresholds and the event/roll semantics are module
  constants with frozen citations (machine-checked in tests/test_s0_context.py).

Frozen sources (STUDY_0_PREREGISTRATION.md, tag s0-freeze-v1):
  L29      ts_event = bar START; "HH:MM bar" = the 1-min bar starting then.
  L30-32   is_roll_transition = the trading day the continuous mapping actually
           switches; is_roll_window = +-2 RTH trading days around it.
  L41-43   America/New_York; RTH 09:30-16:00; observation window 09:30-09:59;
           decision 10:00; entry = 10:00 bar open; forced exit = 15:44 bar
           close; overnight range = prior 18:00 -> 09:30; calendar =
           pandas-market-calendars CME_Equity.
  L44      excluded days, ONLY three: scheduled half day / no RTH trades /
           RTH bars missing > 10%.
  L45      NA policy: no other whole-day deletion; an uncomputable feature is
           NA, the day STAYS in the sample, every table reports its NA count.
  L49      ADR14 = mean (RTH high - RTH low) of the prior 14 COMPLETE RTH
           trading days, current day excluded.
  L53-63   F1-F11.

Approved Implementation Resolutions applied verbatim:
  IR-12/18 F10 multi-event -> NA. Conflict detection runs AFTER the IR-13
           eligibility filter; the multi-hot detail lives ONLY in the
           diagnostic sidecar; no invented event priority.
  IR-13    F10=FOMC only on officially SCHEDULED statement release days; the
           enumerated non-scheduled actions are diagnostic only.
  IR-15    frozen whole-day exclusions FIRST; then, for surviving days, path
           features difference the time-ordered ACTUALLY PRESENT close
           sequence; no synthetic bar, no forward fill, no interpolation, no
           neighbouring-bar substitution for an exact anchor; a missing exact
           anchor makes the dependent feature/label NA without deleting the day.
  IR-19    prev_rth_close = the immediately previous ACTUAL CME RTH session
           (independent of downstream eligibility); regular day -> 15:59 bar
           close; scheduled early-close day -> the final SCHEDULED RTH bar's
           close (+ sidecar flag); that bar absent -> NA; vendor-degraded
           previous session -> NA (never skipped); first sample day -> NA.
  IR-20    F4 reference set = the most recent 60 ACTUAL CME RTH trading days
           strictly before the day, each with a complete 30-bar 09:30-09:59
           window; scheduled early-close days included; downstream S0/ADR14
           eligibility NOT required; zero-bar and incomplete-morning days out.

Semantics are kept identical to the APPROVED scripts/s0_input_preflight.py
(the runner compares independently computed counts against
expected_preflight_assertions; assertions are compare-only and never feed
computation).
"""
from __future__ import annotations

import bisect
from dataclasses import dataclass
from typing import Iterator, Mapping, Sequence

import numpy as np
import pandas as pd

from itsf.contracts import APPROVED_NA_REASONS
from itsf.data.calendar import (
    ADR_LOOKBACK_DAYS,
    EXPECTED_RTH_MINUTES,
    MAX_MISSING_FRACTION,
    REASON_HALF_DAY,
    REASON_MISSING_GT_10PCT,
    REASON_ZERO_BARS,
    ROLL_WINDOW_TRADING_DAYS,
)

# --- frozen minute-of-day grid (bar START minute, ET) -----------------------
# frozen: S0 L29 (bar start convention) + L41-43 (session boundaries)
M_0930, M_0959, M_1000, M_1544, M_1559 = 570, 599, 600, 944, 959
RTH_LO_MINUTE, RTH_HI_MINUTE = M_0930, M_1559     # 390 bars, frozen L41
OBS_LO_MINUTE, OBS_HI_MINUTE = M_0930, M_0959     # 30 bars, frozen L41
PM_LO_MINUTE, PM_HI_MINUTE = M_1000, M_1544       # 345 bars, frozen L41-42
OVERNIGHT_START_MINUTE = 18 * 60                  # frozen L43
REGULAR_CLOSE_MINUTE = 16 * 60                    # frozen L41
OBS_WINDOW_BARS = 30
PM_WINDOW_BARS = 345
F4_LOOKBACK_DAYS = 60                             # frozen L56 (+ IR-20 basis)

# frozen L109-115 — MNQ started trading 2019-05-06; everything before that date
# is counterfactual micro execution on NQ paths and MUST be reported on a
# separate era axis. Defined here so context and dataset cannot drift apart.
MICRO_ERA_BOUNDARY = "2019-05-06"

# --- NA reason vocabulary (contracts.APPROVED_NA_REASONS is authoritative) --
NA_ADR14_WARMUP = "adr14_warmup"
NA_F4_LOOKBACK_WARMUP = "f4_lookback_warmup"
NA_ROLL_TRANSITION = "roll_transition_day_na"
NA_PREV_CLOSE_MISSING = "prev_rth_close_anchor_missing"
NA_ANCHOR_MISSING = "anchor_missing"
NA_MULTI_EVENT_F10 = "multi_event_day_f10_na"
NA_ZERO_DIRECTION = "zero_direction_day_l82"
NA_DIRECTION_UNDETERMINABLE = "direction_undeterminable_na"
NA_OVERNIGHT_EMPTY = "overnight_window_empty"
NA_OVERNIGHT_RANGE_ZERO = "overnight_range_zero"
NA_PATH_ZERO = "path_zero"
NA_DEGENERATE_WINDOW = "degenerate_window"

for _reason in (NA_ADR14_WARMUP, NA_F4_LOOKBACK_WARMUP, NA_ROLL_TRANSITION,
                NA_PREV_CLOSE_MISSING, NA_ANCHOR_MISSING, NA_MULTI_EVENT_F10,
                NA_ZERO_DIRECTION, NA_DIRECTION_UNDETERMINABLE,
                NA_OVERNIGHT_EMPTY, NA_OVERNIGHT_RANGE_ZERO, NA_PATH_ZERO,
                NA_DEGENERATE_WINDOW):
    if _reason not in APPROVED_NA_REASONS:          # import-time fail closed
        raise ImportError(f"NA reason {_reason!r} is not in "
                          "contracts.APPROVED_NA_REASONS")
del _reason

# DELIBERATELY OUTSIDE APPROVED_NA_REASONS. The frozen text has no NA class for
# "the F4 reference median is exactly 0" (it cannot occur on the approved input
# set: preflight F4 NA = 59, all f4_lookback_warmup). If it ever occurs the
# unapproved reason must reach the NA conservation checker and STOP the run
# rather than be silently folded into a neighbouring category.
NA_UNAPPROVED_F4_MEDIAN_ZERO = "f4_reference_median_zero"

# F10 category order is FIXED ONLY to make the multi-hot sidecar deterministic.
# It is NOT a priority: multi-category days are NA (IR-12/18), never ranked.
F10_CATEGORIES = ("CPI", "NFP", "FOMC")


# ===========================================================================
# injected structural inputs
# ===========================================================================

@dataclass(frozen=True)
class SessionSchedule:
    """Official CME_Equity RTH schedule + vendor availability. INJECTED.

    close_minute: scheduled session date (YYYY-MM-DD ET) -> the session's
        OFFICIAL RTH close minute-of-day ET (16:00 == 960). A scheduled early
        close is < 960 and is a frozen L44 excluded day.
    vendor_degraded_dates: scheduled sessions that DID take place but whose
        vendor data is missing/degraded. IR-19 forbids walking past them when
        looking for the previous session; they yield NA instead.
    """
    close_minute: Mapping[str, int]
    vendor_degraded_dates: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        object.__setattr__(self, "close_minute", dict(self.close_minute))
        object.__setattr__(self, "vendor_degraded_dates",
                           frozenset(self.vendor_degraded_dates))

    @property
    def scheduled_dates(self) -> tuple[str, ...]:
        return tuple(sorted(self.close_minute))

    def is_early_close(self, date: str) -> bool:
        """frozen L44 — scheduled half day."""
        return self.close_minute[date] < REGULAR_CLOSE_MINUTE

    def last_scheduled_rth_bar_minute(self, date: str) -> int:
        """IR-19 anchor bar: the final SCHEDULED RTH bar of that session.

        Regular session -> 15:59; scheduled early close -> (close - 1). This is
        the session's own official close bar, NOT a substitute for a missing
        15:59 bar ("last available bar" is explicitly forbidden by IR-19).
        """
        return min(self.close_minute[date] - 1, RTH_HI_MINUTE)


@dataclass(frozen=True)
class EventCalendar:
    """F10 inputs from the frozen event table. INJECTED (no file access here).

    fomc_statement_dates: every statement row of the table.
    unscheduled_fomc_dates: IR-13's enumerated non-scheduled actions — removed
        from the F10 FOMC set, kept as a diagnostic flag only.
    raw_multi_event_dates: IR-12 sidecar population (multi-event days BEFORE
        the IR-13 narrowing); disclosure only, never an input to encoding.
    """
    cpi_dates: frozenset[str] = frozenset()
    nfp_dates: frozenset[str] = frozenset()
    fomc_statement_dates: frozenset[str] = frozenset()
    unscheduled_fomc_dates: frozenset[str] = frozenset()
    raw_multi_event_dates: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        for f in ("cpi_dates", "nfp_dates", "fomc_statement_dates",
                  "unscheduled_fomc_dates", "raw_multi_event_dates"):
            object.__setattr__(self, f, frozenset(getattr(self, f)))

    @property
    def scheduled_fomc_dates(self) -> frozenset[str]:
        """IR-13: F10=FOMC only on officially SCHEDULED statement days."""
        return self.fomc_statement_dates - self.unscheduled_fomc_dates

    def categories(self, date: str) -> tuple[str, ...]:
        """IR-13 eligibility FIRST, then category membership (IR-18 order)."""
        fomc = self.scheduled_fomc_dates
        member = {"CPI": date in self.cpi_dates, "NFP": date in self.nfp_dates,
                  "FOMC": date in fomc}
        return tuple(c for c in F10_CATEGORIES if member[c])

    def encode_f10(self, date: str) -> str | None:
        """Frozen L62 single category, or None == NA on a conflict.

        IR-18 (approved): conflict detection runs AFTER IR-13, so a day whose
        only remaining category is CPI or NFP encodes as that category.
        IR-12: multi-category days are NA; the day is NOT deleted; no priority
        is invented.
        """
        cats = self.categories(date)
        if len(cats) > 1:
            return None
        return cats[0] if cats else "none"


@dataclass(frozen=True)
class RollInterval:
    """One row of the official symbology mapping (IR-16, verify/disclose only)."""
    start_date_utc: str
    end_date_utc_excl: str
    raw_symbol: str = ""
    instrument_id: int = 0


@dataclass(frozen=True)
class RollTransition:
    """A mapping switch resolved onto a real RTH session date (F11)."""
    interval_start_utc: str
    interval_end_utc_excl: str
    raw_symbol: str
    instrument_id: int
    rth_session_date: str | None
    inside_official_interval: bool


# ===========================================================================
# per-ET-date structural summary (single pass, no I/O)
# ===========================================================================

@dataclass(frozen=True)
class DaySummary:
    """Structural facts of one ET date. NaN == that minute simply has no bar;
    nothing is ever filled in (IR-15)."""
    date: str
    n_rth: int
    rth_high: float
    rth_low: float
    obs_present: int
    obs_volume: float
    pm_present: int
    official_close: float          # IR-19 anchor bar close of THIS session
    o0930: float
    c0959: float
    o1000: float
    c1544: float
    evening_n: int
    evening_high: float
    evening_low: float
    preopen_n: int
    preopen_high: float
    preopen_low: float
    all_n: int
    all_high: float
    all_low: float


def _minutes_of_day(bars: pd.DataFrame) -> np.ndarray:
    ts = bars["ts"]
    return (ts.dt.hour * 60 + ts.dt.minute).to_numpy(dtype=int)


def window_bars(bars: pd.DataFrame, lo_minute: int,
                hi_minute_inclusive: int) -> pd.DataFrame:
    """Bars whose START minute-of-day lies in [lo, hi] (frozen L29 convention).

    Returned time-sorted with a fresh RangeIndex; absent minutes stay absent.
    """
    if bars is None or len(bars) == 0:
        return _empty_bars(bars)
    m = _minutes_of_day(bars)
    sel = (m >= lo_minute) & (m <= hi_minute_inclusive)
    return bars.loc[sel].sort_values("ts").reset_index(drop=True)


def _empty_bars(like: pd.DataFrame | None) -> pd.DataFrame:
    if like is not None:
        return like.iloc[0:0].reset_index(drop=True)
    return pd.DataFrame(columns=["ts", "open", "high", "low", "close", "volume"])


def _nan_minmax(a: float, b: float, fn) -> float:
    if np.isnan(a):
        return b
    if np.isnan(b):
        return a
    return fn(a, b)


def summarise_day(date: str, bars: pd.DataFrame,
                  schedule: SessionSchedule) -> DaySummary:
    """One ET date -> DaySummary. Pure; duplicate RTH minutes fail closed."""
    nan = float("nan")
    if bars is None or len(bars) == 0:
        return DaySummary(date=date, n_rth=0, rth_high=nan, rth_low=nan,
                          obs_present=0, obs_volume=0.0, pm_present=0,
                          official_close=nan, o0930=nan, c0959=nan, o1000=nan,
                          c1544=nan, evening_n=0, evening_high=nan,
                          evening_low=nan, preopen_n=0, preopen_high=nan,
                          preopen_low=nan, all_n=0, all_high=nan, all_low=nan)

    m = _minutes_of_day(bars)
    o = bars["open"].to_numpy(dtype=float)
    h = bars["high"].to_numpy(dtype=float)
    lo = bars["low"].to_numpy(dtype=float)
    c = bars["close"].to_numpy(dtype=float)
    v = bars["volume"].to_numpy(dtype=float)

    rth = (m >= RTH_LO_MINUTE) & (m <= RTH_HI_MINUTE)
    rth_minutes = m[rth]
    if len(np.unique(rth_minutes)) != len(rth_minutes):
        raise ValueError(f"duplicate RTH minute on {date} — fail closed")
    by_minute = {int(mm): i for i, mm in enumerate(m) if rth[i]}

    def _open_at(minute: int) -> float:
        i = by_minute.get(minute)
        return float(o[i]) if i is not None else nan

    def _close_at(minute: int) -> float:
        i = by_minute.get(minute)
        return float(c[i]) if i is not None else nan

    obs = (m >= OBS_LO_MINUTE) & (m <= OBS_HI_MINUTE)
    pm = (m >= PM_LO_MINUTE) & (m <= PM_HI_MINUTE)
    eve = m >= OVERNIGHT_START_MINUTE
    pre = m < RTH_LO_MINUTE

    close_bar = (schedule.last_scheduled_rth_bar_minute(date)
                 if date in schedule.close_minute else RTH_HI_MINUTE)

    return DaySummary(
        date=date,
        n_rth=int(rth.sum()),
        rth_high=float(np.max(h[rth])) if rth.any() else nan,
        rth_low=float(np.min(lo[rth])) if rth.any() else nan,
        obs_present=int(obs.sum()),
        obs_volume=float(np.nansum(v[obs])) if obs.any() else 0.0,
        pm_present=int(pm.sum()),
        official_close=_close_at(close_bar),
        o0930=_open_at(M_0930), c0959=_close_at(M_0959),
        o1000=_open_at(M_1000), c1544=_close_at(M_1544),
        evening_n=int(eve.sum()),
        evening_high=float(np.max(h[eve])) if eve.any() else nan,
        evening_low=float(np.min(lo[eve])) if eve.any() else nan,
        preopen_n=int(pre.sum()),
        preopen_high=float(np.max(h[pre])) if pre.any() else nan,
        preopen_low=float(np.min(lo[pre])) if pre.any() else nan,
        all_n=int(len(m)),
        all_high=float(np.max(h)), all_low=float(np.min(lo)),
    )


# ===========================================================================
# eligibility funnel (frozen L44, order per the approved preflight)
# ===========================================================================

@dataclass(frozen=True, eq=False)
class EligibilityFunnel:
    """scheduled
         - zero-bar days                 -> observed RTH days
         - scheduled early-close days    -> regular full-session candidates
         - RTH missing > 10% days        -> structurally eligible days
         - ADR14 warm-up days            -> final feature-construction dates

    `complete_390` is a SIDE DIAGNOSTIC (the ADR14 lookback basis, frozen L49),
    never a deduction stage. Only the three frozen L44 categories delete a day.
    """
    scheduled: tuple[str, ...]
    zero_bar: tuple[str, ...]
    observed_rth: tuple[str, ...]
    removed_early_close: tuple[str, ...]
    regular: tuple[str, ...]
    removed_missing_gt_10pct: tuple[str, ...]
    structurally_eligible: tuple[str, ...]
    complete_390: tuple[str, ...]
    removed_adr14_warmup: tuple[str, ...]
    final_dates: tuple[str, ...]
    checks: Mapping[str, bool]
    exclusion_reason: Mapping[str, str]

    def counts(self) -> dict[str, int]:
        """The five funnel levels the runner compares against
        expected_preflight_assertions (compare-only, never an input)."""
        return {
            "L0_scheduled_trading_days": len(self.scheduled),
            "minus_zero_bar_days": len(self.zero_bar),
            "L1_observed_rth_days": len(self.observed_rth),
            "minus_scheduled_early_close_days": len(self.removed_early_close),
            "L2_regular_full_session_candidates": len(self.regular),
            "minus_rth_missing_gt_10pct_days":
                len(self.removed_missing_gt_10pct),
            "L3_structurally_eligible_days": len(self.structurally_eligible),
            "minus_adr14_warmup_days": len(self.removed_adr14_warmup),
            "L4_final_feature_construction_dates": len(self.final_dates),
            "side_diagnostic_complete_390_bar_rth_days":
                len(self.complete_390),
        }

    def prior_complete_count(self, date: str) -> int:
        """Number of COMPLETE RTH days strictly before `date` (frozen L49)."""
        return bisect.bisect_left(self.complete_390, date)


def build_funnel(summaries: Mapping[str, DaySummary],
                 schedule: SessionSchedule) -> EligibilityFunnel:
    """Frozen L44 exclusions in the approved order. Pure."""
    scheduled = sorted(schedule.close_minute)
    early_close = {d for d in scheduled if schedule.is_early_close(d)}

    observed = [d for d in scheduled
                if d in summaries and summaries[d].n_rth > 0]
    observed_set = set(observed)
    zero_bar = [d for d in scheduled if d not in observed_set]

    removed_early = sorted(d for d in observed if d in early_close)
    regular = sorted(observed_set - set(removed_early))

    removed_missing = [
        d for d in regular
        if (EXPECTED_RTH_MINUTES - summaries[d].n_rth) / EXPECTED_RTH_MINUTES
        > MAX_MISSING_FRACTION]
    eligible = sorted(set(regular) - set(removed_missing))

    complete_390 = tuple(d for d in regular
                         if summaries[d].n_rth == EXPECTED_RTH_MINUTES)

    removed_warmup = [d for d in eligible
                      if bisect.bisect_left(complete_390, d)
                      < ADR_LOOKBACK_DAYS]
    final = sorted(set(eligible) - set(removed_warmup))

    checks = {
        "L0_minus_zero_bar_equals_L1":
            len(scheduled) - len(zero_bar) == len(observed),
        "L1_minus_early_close_equals_L2":
            len(observed) - len(removed_early) == len(regular),
        "L2_minus_missing_gt_10pct_equals_L3":
            len(regular) - len(removed_missing) == len(eligible),
        "L3_minus_adr14_warmup_equals_L4":
            len(eligible) - len(removed_warmup) == len(final),
        "removed_sets_mutually_disjoint": all(
            not (set(a) & set(b)) for a, b in (
                (zero_bar, removed_early), (zero_bar, removed_missing),
                (zero_bar, removed_warmup), (removed_early, removed_missing),
                (removed_early, removed_warmup),
                (removed_missing, removed_warmup))),
        "no_date_vanishes_unaccounted":
            len(scheduled) == len(final) + len(zero_bar) + len(removed_early)
            + len(removed_missing) + len(removed_warmup),
        "no_rth_bars_on_unscheduled_days": not [
            d for d, s in summaries.items()
            if s.n_rth > 0 and d not in schedule.close_minute],
    }

    # frozen L44 — ONLY these three categories delete a day. ADR14 warm-up is a
    # normalisation warm-up, NOT an exclusion: those days stay in the sample
    # with NA features (frozen L45), so they are not listed here.
    reasons: dict[str, str] = {}
    for d in zero_bar:
        reasons[d] = REASON_ZERO_BARS
    for d in removed_early:
        reasons[d] = REASON_HALF_DAY
    for d in removed_missing:
        reasons[d] = REASON_MISSING_GT_10PCT

    return EligibilityFunnel(
        scheduled=tuple(scheduled), zero_bar=tuple(zero_bar),
        observed_rth=tuple(observed),
        removed_early_close=tuple(removed_early), regular=tuple(regular),
        removed_missing_gt_10pct=tuple(removed_missing),
        structurally_eligible=tuple(eligible), complete_390=complete_390,
        removed_adr14_warmup=tuple(removed_warmup), final_dates=tuple(final),
        checks=checks, exclusion_reason=reasons)


# ===========================================================================
# universe (all per-day lookbacks; every value uses data <= that day)
# ===========================================================================

@dataclass(frozen=True, eq=False)
class S0Universe:
    """Deterministic pre-computation shared by every day of the sample.

    NO LOOK-AHEAD BY CONSTRUCTION: adr14 / rvol_median60 / prev_rth_close /
    overnight_hl for day d only read days strictly before d (or, for the
    overnight span, the block ending at d 09:30). Roll flags come from the
    official mapping CALENDAR (IR-16), not from prices; is_roll_window is
    symmetric +-2 RTH days by frozen definition (L30-32).
    """
    funnel: EligibilityFunnel
    summaries: Mapping[str, DaySummary]
    all_dates: tuple[str, ...]
    adr14: Mapping[str, float | None]
    rvol_median60: Mapping[str, float | None]
    f4_basis_size: Mapping[str, int]
    prev_session: Mapping[str, str | None]
    prev_rth_close: Mapping[str, float | None]
    prev_rth_close_cause: Mapping[str, str]
    prev_close_from_early_close: frozenset[str]
    overnight_hl: Mapping[str, tuple[float, float] | None]
    overnight_bars: Mapping[str, int]
    roll_transitions: tuple[RollTransition, ...]
    roll_transition_dates: frozenset[str]
    roll_window_dates: frozenset[str]
    schedule: SessionSchedule
    events: EventCalendar

    def f10_exclusive_counts(self) -> dict[str, int]:
        """Mutually-exclusive F10 partition over the structurally eligible
        population (IR-18 + the approved report-governance fix). The partition
        MUST sum to the population — the runner compares this to
        expected_preflight_assertions."""
        counts = {"CPI": 0, "NFP": 0, "FOMC": 0, "none": 0, "NA_multi_event": 0}
        for d in self.funnel.structurally_eligible:
            flag = self.events.encode_f10(d)
            counts["NA_multi_event" if flag is None else flag] += 1
        total = sum(counts.values())
        if total != len(self.funnel.structurally_eligible):
            raise ValueError(f"F10 partition {counts} does not sum to "
                             f"{len(self.funnel.structurally_eligible)}")
        return counts


def _adr14_map(funnel: EligibilityFunnel,
               summaries: Mapping[str, DaySummary],
               dates: Sequence[str]) -> dict[str, float | None]:
    """frozen L49 — mean RTH (high-low) of the prior 14 COMPLETE RTH days."""
    complete = funnel.complete_390
    ranges = [summaries[d].rth_high - summaries[d].rth_low for d in complete]
    out: dict[str, float | None] = {}
    for d in dates:
        i = funnel.prior_complete_count(d)
        if i < ADR_LOOKBACK_DAYS:
            out[d] = None                       # NA_ADR14_WARMUP
        else:
            window = ranges[i - ADR_LOOKBACK_DAYS:i]
            out[d] = float(sum(window)) / ADR_LOOKBACK_DAYS
    return out


def _rvol_median_map(funnel: EligibilityFunnel,
                     summaries: Mapping[str, DaySummary],
                     dates: Sequence[str],
                     ) -> tuple[dict[str, float | None], dict[str, int]]:
    """IR-20 — the most recent 60 ACTUAL RTH sessions strictly before the day
    whose 09:30-09:59 window is complete (30 bars); early closes included;
    downstream eligibility NOT required."""
    basis = [d for d in funnel.observed_rth
             if summaries[d].obs_present == OBS_WINDOW_BARS]
    vols = [summaries[d].obs_volume for d in basis]
    median: dict[str, float | None] = {}
    size: dict[str, int] = {}
    for d in dates:
        j = bisect.bisect_left(basis, d)
        size[d] = j
        median[d] = (None if j < F4_LOOKBACK_DAYS
                     else float(np.median(vols[j - F4_LOOKBACK_DAYS:j])))
    return median, size


def _prev_session_map(funnel: EligibilityFunnel,
                      summaries: Mapping[str, DaySummary],
                      schedule: SessionSchedule,
                      dates: Sequence[str]) -> dict[str, str | None]:
    """IR-19 — the immediately previous ACTUAL CME RTH session.

    Walk back through the official schedule and skip ONLY true closures (a
    scheduled date with no session data that is NOT flagged vendor-degraded).
    Vendor-degraded sessions ARE the reference day (their anchor is NA);
    skipping past them, or past any day that merely fails downstream
    eligibility, is prohibited.
    """
    scheduled = funnel.scheduled
    true_closures = {d for d in funnel.zero_bar
                     if d not in schedule.vendor_degraded_dates}
    out: dict[str, str | None] = {}
    for d in dates:
        i = bisect.bisect_left(scheduled, d)
        prev: str | None = None
        while i > 0:
            i -= 1
            p = scheduled[i]
            if p in true_closures:
                continue                       # no session ever happened
            prev = p                           # observed OR vendor-degraded
            break
        out[d] = prev
    return out


def _prev_close_map(summaries: Mapping[str, DaySummary],
                    schedule: SessionSchedule,
                    prev_session: Mapping[str, str | None],
                    dates: Sequence[str],
                    ) -> tuple[dict[str, float | None], dict[str, str],
                               set[str]]:
    """IR-19 anchor value + fine-grained cause + early-close sidecar flag."""
    value: dict[str, float | None] = {}
    cause: dict[str, str] = {}
    from_early: set[str] = set()
    for d in dates:
        p = prev_session.get(d)
        if p is None:
            value[d], cause[d] = None, "no_prior_rth_session_in_sample"
            continue
        s = summaries.get(p)
        if (p in schedule.vendor_degraded_dates or s is None or s.n_rth == 0):
            value[d], cause[d] = None, "prev_day_vendor_degraded_zero_bar"
            continue
        anchor = s.official_close
        if np.isnan(anchor):
            value[d] = None
            cause[d] = ("prev_day_early_close_final_scheduled_bar_absent"
                        if schedule.is_early_close(p)
                        else "prev_day_1559_bar_absent")
            continue
        value[d], cause[d] = float(anchor), ""
        if schedule.is_early_close(p):
            from_early.add(d)                  # IR-19 sidecar flag
    return value, cause, from_early


def _overnight_map(summaries: Mapping[str, DaySummary],
                   all_dates: Sequence[str],
                   prev_session: Mapping[str, str | None],
                   dates: Sequence[str],
                   ) -> tuple[dict[str, tuple[float, float] | None],
                              dict[str, int]]:
    """frozen L43 — overnight range = previous ACTUAL session 18:00 -> d 09:30.

    The span crosses non-trading ET dates (a Monday's window holds the Sunday
    evening reopen), so every intermediate ET date's whole-day block counts.
    """
    hl: dict[str, tuple[float, float] | None] = {}
    n_bars: dict[str, int] = {}
    for d in dates:
        p = prev_session.get(d)
        if p is None:
            hl[d], n_bars[d] = None, 0
            continue
        hi = lo = float("nan")
        n = 0
        ps = summaries.get(p)
        if ps is not None and ps.evening_n:
            hi = _nan_minmax(hi, ps.evening_high, max)
            lo = _nan_minmax(lo, ps.evening_low, min)
            n += ps.evening_n
        i0 = bisect.bisect_right(all_dates, p)
        i1 = bisect.bisect_left(all_dates, d)
        for mid in all_dates[i0:i1]:
            ms = summaries.get(mid)
            if ms is not None and ms.all_n:
                hi = _nan_minmax(hi, ms.all_high, max)
                lo = _nan_minmax(lo, ms.all_low, min)
                n += ms.all_n
        cs = summaries.get(d)
        if cs is not None and cs.preopen_n:
            hi = _nan_minmax(hi, cs.preopen_high, max)
            lo = _nan_minmax(lo, cs.preopen_low, min)
            n += cs.preopen_n
        n_bars[d] = n
        hl[d] = None if (n == 0 or np.isnan(hi) or np.isnan(lo)) else (hi, lo)
    return hl, n_bars


def _roll_map(funnel: EligibilityFunnel,
              intervals: Sequence[RollInterval],
              ) -> tuple[tuple[RollTransition, ...], frozenset[str],
                         frozenset[str]]:
    """F11 (frozen L30-32) via the official mapping (IR-16).

    The mapping switches at 00:00 UTC == the PRIOR evening ET pre-open of the
    NEXT CME session, so a transition is booked on the first valid RTH session
    date on/after the official interval start — never a bare UTC/ET date cut,
    never a weekend date. is_roll_window = +-2 RTH trading days (frozen L30).
    """
    observed = funnel.observed_rth
    transitions: list[RollTransition] = []
    for iv in list(intervals)[1:]:            # N intervals -> N-1 switches
        i = bisect.bisect_left(observed, iv.start_date_utc)
        session = observed[i] if i < len(observed) else None
        transitions.append(RollTransition(
            interval_start_utc=iv.start_date_utc,
            interval_end_utc_excl=iv.end_date_utc_excl,
            raw_symbol=iv.raw_symbol, instrument_id=iv.instrument_id,
            rth_session_date=session,
            inside_official_interval=bool(
                session is not None
                and iv.start_date_utc <= session < iv.end_date_utc_excl)))

    tdates = {t.rth_session_date for t in transitions
              if t.rth_session_date is not None}
    window: set[str] = set()
    index = {d: i for i, d in enumerate(observed)}
    for t in tdates:
        i = index.get(t)
        if i is None:
            window.add(t)
            continue
        lo = max(0, i - ROLL_WINDOW_TRADING_DAYS)
        hi = min(len(observed) - 1, i + ROLL_WINDOW_TRADING_DAYS)
        window.update(observed[lo:hi + 1])
    return tuple(transitions), frozenset(tdates), frozenset(window)


def build_universe(bars_by_date: Mapping[str, pd.DataFrame],
                   schedule: SessionSchedule,
                   events: EventCalendar,
                   roll_intervals: Sequence[RollInterval] = (),
                   ) -> S0Universe:
    """Assemble every per-day lookback the frozen formulas need. Pure.

    bars_by_date: ET date (YYYY-MM-DD) -> ALL 1-minute bars of that ET date
    (tz-aware `ts`, plus open/high/low/close/volume). Non-trading ET dates may
    appear (their evening/pre-open blocks belong to overnight windows).
    """
    summaries = {d: summarise_day(d, df, schedule)
                 for d, df in bars_by_date.items()}
    funnel = build_funnel(summaries, schedule)
    dates = funnel.structurally_eligible
    all_dates = tuple(sorted(bars_by_date))

    adr14 = _adr14_map(funnel, summaries, dates)
    rvol, f4_size = _rvol_median_map(funnel, summaries, dates)
    prev_session = _prev_session_map(funnel, summaries, schedule, dates)
    prev_close, prev_cause, from_early = _prev_close_map(
        summaries, schedule, prev_session, dates)
    on_hl, on_bars = _overnight_map(summaries, all_dates, prev_session, dates)
    transitions, tdates, window = _roll_map(funnel, roll_intervals)

    return S0Universe(
        funnel=funnel, summaries=summaries, all_dates=all_dates, adr14=adr14,
        rvol_median60=rvol, f4_basis_size=f4_size, prev_session=prev_session,
        prev_rth_close=prev_close, prev_rth_close_cause=prev_cause,
        prev_close_from_early_close=frozenset(from_early), overnight_hl=on_hl,
        overnight_bars=on_bars, roll_transitions=transitions,
        roll_transition_dates=tdates, roll_window_dates=window,
        schedule=schedule, events=events)


# ===========================================================================
# per-day context
# ===========================================================================

@dataclass(frozen=True, eq=False)
class DayContext:
    """Everything day `trade_date` needs, and nothing computed from day > d.

    `context_na_reasons` holds the NA reasons that are decidable BEFORE the
    frozen formulas run (missing anchor / warm-up / roll transition / multi
    event / empty overnight window). Value-dependent reasons (path_zero,
    degenerate_window, zero_direction_day_l82, overnight_range_zero) are
    attributed by dataset.py after the formula modules return.
    """
    trade_date: str
    obs_bars: pd.DataFrame
    pm_bars: pd.DataFrame
    adr14: float | None
    prev_rth_close: float | None
    rvol_median60: float | None
    overnight_hl: tuple[float, float] | None
    event_flag: str | None
    is_roll_transition: bool
    is_roll_window: bool
    o0930: float | None
    c0959: float | None
    o1000: float | None
    c1544: float | None
    obs_window_empty: bool
    pm_window_empty: bool
    context_na_reasons: Mapping[str, str]
    sidecar: Mapping[str, object]

    # --- consumption helpers (the ONLY sanctioned call shapes) --------------

    def feature_kwargs(self) -> dict[str, object]:
        """Exact kwargs of features.compute_day_features (REPLACE_PROHIBITED).

        Only valid when ``obs_window_empty`` is False AND both opening-window
        anchors exist: features.py reads O0930/C0959 positionally
        (`open.iloc[0]` / `close.iloc[-1]`), which equals the exact frozen
        anchors precisely when the 09:30 and 09:59 bars are present. IR-15
        forbids neighbouring-bar substitution, so dataset.py masks the
        anchor-dependent fields to NA whenever an exact anchor is absent.
        """
        return {
            "obs_bars": self.obs_bars,
            "overnight_hl": self.overnight_hl,
            "adr14": self.adr14,
            "prior_rth_close": self.prev_rth_close,
            "rvol_median60": self.rvol_median60,
            "event_flag": self.event_flag,
            "is_roll_transition": self.is_roll_transition,
            "is_roll_window": self.is_roll_window,
        }

    @property
    def opening_anchors_present(self) -> bool:
        return self.o0930 is not None and self.c0959 is not None

    @property
    def features_computable(self) -> bool:
        """features.compute_day_features raises on an empty window."""
        return not self.obs_window_empty

    @property
    def labels_computable(self) -> bool:
        """labels.compute_day_labels needs a non-empty pm window and O1000."""
        return not self.pm_window_empty and self.o1000 is not None


def _f(x: float) -> float | None:
    return None if (x is None or np.isnan(x)) else float(x)


def build_day_context(date: str, bars_by_date: Mapping[str, pd.DataFrame],
                      universe: S0Universe) -> DayContext:
    """Assemble the context of one structurally eligible day. Pure."""
    if date not in universe.funnel.structurally_eligible:
        raise ValueError(
            f"{date} is not a structurally eligible day; excluded days "
            f"({REASON_HALF_DAY}/{REASON_ZERO_BARS}/{REASON_MISSING_GT_10PCT}) "
            "are handled by the exclusion table, frozen L44")

    bars = bars_by_date.get(date)
    obs = window_bars(bars, OBS_LO_MINUTE, OBS_HI_MINUTE)
    pm = window_bars(bars, PM_LO_MINUTE, PM_HI_MINUTE)
    s = universe.summaries[date]

    adr14 = universe.adr14[date]
    rvol = universe.rvol_median60[date]
    prev_close = universe.prev_rth_close[date]
    on_hl = universe.overnight_hl[date]
    flag = universe.events.encode_f10(date)
    is_transition = date in universe.roll_transition_dates
    is_window = date in universe.roll_window_dates

    o0930, c0959 = _f(s.o0930), _f(s.c0959)
    o1000, c1544 = _f(s.o1000), _f(s.c1544)
    obs_empty = len(obs) == 0
    pm_empty = len(pm) == 0
    anchors_ok = o0930 is not None and c0959 is not None

    # ---- NA reasons decidable from context alone (preflight precedence) ----
    r: dict[str, str] = {}
    if not anchors_ok:
        r["ret_open30"] = NA_ANCHOR_MISSING          # F1
    elif adr14 is None:
        r["ret_open30"] = NA_ADR14_WARMUP
    if obs_empty:
        r["or_width"] = NA_ANCHOR_MISSING            # F2
    elif adr14 is None:
        r["or_width"] = NA_ADR14_WARMUP
    if not anchors_ok:
        r["de_open30"] = NA_ANCHOR_MISSING           # F3 (path_zero later)
    if obs_empty:
        r["rvol_open30"] = NA_ANCHOR_MISSING         # F4
    elif rvol is None:
        r["rvol_open30"] = NA_F4_LOOKBACK_WARMUP
    elif rvol == 0:
        r["rvol_open30"] = NA_UNAPPROVED_F4_MEDIAN_ZERO   # fail closed
    if is_transition:
        r["gap"] = NA_ROLL_TRANSITION                # F5, frozen L57
    elif o0930 is None:
        r["gap"] = NA_ANCHOR_MISSING
    elif prev_close is None:
        r["gap"] = NA_PREV_CLOSE_MISSING             # IR-19
    elif adr14 is None:
        r["gap"] = NA_ADR14_WARMUP
    if on_hl is None:
        r["open_loc_on"] = NA_OVERNIGHT_EMPTY        # F6
        r["on_range"] = NA_OVERNIGHT_EMPTY           # F7
    else:
        if o0930 is None:
            r["open_loc_on"] = NA_ANCHOR_MISSING
        if adr14 is None:
            r["on_range"] = NA_ADR14_WARMUP
    if not anchors_ok:
        r["retrace_open30"] = NA_ANCHOR_MISSING      # F8 (zero-direction later)
    if c0959 is None or obs_empty:
        r["close_pos_open30"] = NA_ANCHOR_MISSING    # F9 (degenerate later)
    if flag is None:
        r["is_event_day"] = NA_MULTI_EVENT_F10       # F10, IR-12/18
    if obs_empty:
        # Unreachable on the approved input set (preflight: every structurally
        # eligible day has all four anchors). features.compute_day_features
        # raises on an empty window and restating a frozen formula outside
        # features.py is prohibited, so NO feature of that day is computable:
        # every measured field is NA, keeping the more specific reason where
        # one was already established. The day still stays in the sample
        # (frozen L45).
        for k in ("ret_open30", "or_width", "de_open30", "rvol_open30", "gap",
                  "open_loc_on", "on_range", "retrace_open30",
                  "close_pos_open30"):
            r.setdefault(k, NA_ANCHOR_MISSING)

    era = ("counterfactual_micro_execution" if date < MICRO_ERA_BOUNDARY
           else "actual_micro_available_era")
    sidecar = {
        # IR-12/18 diagnostic sidecar — multi-hot detail NEVER enters F10.
        "f10_categories": universe.events.categories(date),
        "f10_multi_event": len(universe.events.categories(date)) > 1,
        "f10_raw_multi_event_day":
            date in universe.events.raw_multi_event_dates,
        "unscheduled_fomc_action":                    # IR-13, diagnostic only
            date in universe.events.unscheduled_fomc_dates,
        # IR-19 diagnostics
        "prev_rth_session": universe.prev_session[date],
        "prev_rth_close_cause": universe.prev_rth_close_cause[date],
        "prev_close_from_early_close_day":
            date in universe.prev_close_from_early_close,
        # structural diagnostics
        "obs_bars_present": s.obs_present,
        "pm_bars_present": s.pm_present,
        "rth_bars_present": s.n_rth,
        "overnight_bars": universe.overnight_bars[date],
        "f4_basis_size": universe.f4_basis_size[date],
        "prior_complete_rth_days":
            universe.funnel.prior_complete_count(date),
        "era": era,                                   # frozen L109-115
    }

    return DayContext(
        trade_date=date, obs_bars=obs, pm_bars=pm, adr14=adr14,
        prev_rth_close=prev_close, rvol_median60=rvol, overnight_hl=on_hl,
        event_flag=flag, is_roll_transition=is_transition,
        is_roll_window=is_window, o0930=o0930, c0959=c0959, o1000=o1000,
        c1544=c1544, obs_window_empty=obs_empty, pm_window_empty=pm_empty,
        context_na_reasons=r, sidecar=sidecar)


def iter_day_contexts(bars_by_date: Mapping[str, pd.DataFrame],
                      universe: S0Universe) -> Iterator[DayContext]:
    """Contexts of every structurally eligible day, in date order.

    frozen L45: excluded days are the ONLY days that leave the sample; every
    other day appears here even when most of its features will be NA.
    """
    for d in universe.funnel.structurally_eligible:
        yield build_day_context(d, bars_by_date, universe)
