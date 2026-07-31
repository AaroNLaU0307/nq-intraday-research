"""S0_INPUT_PREFLIGHT — input-eligibility terminal check (M4-T4 / SA-3).

QA-only, strategy-number-free. This script decides NOTHING about research
outcomes: it verifies that the inputs S0 will consume exist, are eligible
under the FROZEN rules, and that every feature/label anchor is either present
or explicitly NA with a classified reason.

WHAT THIS SCRIPT MAY EMIT (frozen scope, SA-3 task spec section D/F):
  counts, booleans, reason classifications, status strings.
WHAT IT MUST NEVER EMIT:
  feature VALUES, distributions, means/quantiles, any relation between a
  feature and a label or a future price, strategy performance of any kind,
  cost-adjusted anything, expected-value figures, simulation output, or a
  GO/STOP judgment. Features F1-F11 ARE computed in memory (explicitly
  permitted, Aaron 2026-07-29 errata) solely to determine constructibility /
  NA status / NA reason / is-constant; the values are discarded.

FROZEN CITATIONS (STUDY_0_PREREGISTRATION.md, tag s0-freeze-v1):
  L41-43  ET timezone; RTH 09:30-16:00; observation window 09:30-09:59 bar;
          decision 10:00; entry = 10:00 bar open; forced exit = 15:44 bar
          close; overnight range = prior 18:00 -> 09:30; calendar =
          pandas-market-calendars CME_Equity.
  L44     Excluded days, ONLY three categories: half day (scheduled early
          close); no RTH trades; RTH bars missing > 10%.
  L45     NA policy: apart from excluded days no whole day may be deleted;
          an uncomputable feature is recorded NA and the day still enters the
          overall statistics; every table must report its NA count.
  L49     ADR14 = mean (RTH high - RTH low) over the prior 14 COMPLETE RTH
          trading days, current day excluded.
  L53-63  F1-F11 definitions (F4 needs the prior-60-trading-day same-window
          median; F5 is NA on is_roll_transition days; F10 event calendar;
          F11 roll flags).
  L86-91  Label table (Y_cont / Y1 need O1000 and C1544; Y2-Y5 per table).
  L30-32  is_roll_transition = the trading day the continuous mapping actually
          switches; is_roll_window = +-2 RTH trading days around it.

APPROVED IMPLEMENTATION RESOLUTIONS APPLIED VERBATIM (IMPLEMENTATION_
RESOLUTIONS.md, M4 batch, APPROVED_BY_AARON 2026-07-29):
  IR-12  multi-event day -> frozen single-category F10 is NA; the day is NOT
         deleted and still enters the overall statistics; the multi-hot detail
         stays in a diagnostic sidecar that feeds no judgment input; no
         invented event priority.
  IR-13  F10=FOMC only on officially SCHEDULED statement release days (92);
         the first day of a two-day meeting is not marked; the four
         non-scheduled actions 2019-10-11, 2020-03-03, 2020-03-15, 2020-03-23
         are `unscheduled_fomc_action`, diagnostic only.
  IR-14  postponed releases carry their ACTUAL official release date.
  IR-15  frozen whole-day exclusions FIRST; then, for surviving days only,
         path features difference the time-ordered ACTUALLY PRESENT close
         sequence; no synthetic bars, no forward fill, no interpolation, no
         neighbouring-bar substitution for an exact anchor; a missing exact
         anchor makes the dependent feature/label NA without deleting the day.
  IR-16  official symbology mapping gate1/symbology/nq_v0_mapping.csv is the
         cross-check reference for F11/roll coverage (verify + disclose only).
  IR-17  the 45 FOMC rows with no archived official release time keep
         official_release_time_et NA and release_time_status =
         official_time_unavailable_in_archived_source; the DATE-level F10
         encoding is unaffected and those rows must not delete a day nor make
         F10 NA.

Real data is read exclusively through DevelopmentSignalLoader (the approved
QA read path). Execution-cost-calibration and Internal-Validation paths are
never touched.

Outputs (both written by ONE invocation so the report and the JSON are
same-run by construction): S0_INPUT_PREFLIGHT.json, S0_INPUT_PREFLIGHT_REPORT.md
"""
from __future__ import annotations

import bisect
import hashlib
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from itsf.data.calendar import (                                    # noqa: E402
    ADR_LOOKBACK_DAYS,
    EXPECTED_RTH_MINUTES,
    MAX_MISSING_FRACTION,
    ROLL_WINDOW_TRADING_DAYS,
)
from itsf.data.dbn_loader import DevelopmentSignalLoader            # noqa: E402
from itsf.data.roles import ROLE_WINDOWS, DataRole                  # noqa: E402

A1_DIR = Path(r"C:\Users\Aaron\quant-data\databento-archive\intraday-trend"
              r"\development_signal\GLBX-20260727-DL3BEBCHJA")
F10_CSV = REPO / "gate1" / "f10_event_calendar" / "f10_events.csv"
# IR-17 approved bytes of the frozen event table (task spec startup gate).
F10_EXPECTED_SHA256 = (
    "5e92ad00737339c392ed2c0927736e196e076e185897c146c884d5f515bb5e8c")
SYMBOLOGY_CSV = REPO / "gate1" / "symbology" / "nq_v0_mapping.csv"
OUT_JSON = REPO / "S0_INPUT_PREFLIGHT.json"
OUT_MD = REPO / "S0_INPUT_PREFLIGHT_REPORT.md"

# Minute-of-day indices (ET). Bar "HH:MM" = the 1-minute bar STARTING at HH:MM.
M_0930, M_0959, M_1000, M_1544, M_1559 = 570, 599, 600, 944, 959
RTH_LO, RTH_HI = M_0930, M_1559          # 390 bars, frozen L41
W1_LO, W1_HI = M_0930, M_0959            # 30 bars, observation window
W2_LO, W2_HI = M_1000, M_1544            # 345 bars, PM window
EVENING_LO = 18 * 60                     # overnight range start, frozen L43
CAL_START, CAL_END = "2010-06-06", "2021-12-31"
F4_LOOKBACK_DAYS = 60                    # frozen L56

# IR-13: the four non-scheduled FOMC actions, enumerated verbatim.
UNSCHEDULED_FOMC = ("2019-10-11", "2020-03-03", "2020-03-15", "2020-03-23")

STAGE = "INPUT_PREFLIGHT_ONLY"
REAL_S0 = "NOT_RUN"
APPROVAL = "AWAITING_AARON_APPROVAL"


# --------------------------------------------------------------------------
# per-date structural extract
# --------------------------------------------------------------------------

class DayBars:
    """RTH minute grid plus the blocks needed for the overnight range.

    Arrays are indexed 0..389 == minutes 09:30..15:59 ET. NaN == that minute
    has no bar (trade-aggregated OHLCV: no trade in that minute). NOTHING is
    ever filled in: absence stays absence (IR-15).
    """
    __slots__ = ("o", "h", "l", "c", "v", "n_rth",
                 "eve_h", "eve_l", "eve_n", "early_h", "early_l", "early_n",
                 "day_h", "day_l", "day_n", "iids")

    def __init__(self) -> None:
        nan = np.full(EXPECTED_RTH_MINUTES, np.nan)
        self.o, self.h, self.l, self.c = (nan.copy() for _ in range(4))
        self.v = np.full(EXPECTED_RTH_MINUTES, np.nan)
        self.n_rth = 0
        self.eve_h = self.eve_l = np.nan      # bars 18:00-23:59 this ET date
        self.eve_n = 0
        self.early_h = self.early_l = np.nan  # bars 00:00-09:29 this ET date
        self.early_n = 0
        self.day_h = self.day_l = np.nan      # whole ET date (any minute)
        self.day_n = 0
        self.iids: set[int] = set()


def _mm(a: float, b: float, fn) -> float:
    if np.isnan(a):
        return b
    if np.isnan(b):
        return a
    return fn(a, b)


def extract_days(loader: DevelopmentSignalLoader,
                 files: list[str], verbose: bool = True) -> tuple[dict, Counter, list]:
    """One decode pass over the archive; accumulates per-ET-date structure.

    ET dates straddle the UTC monthly file split (an ET date's evening block
    lands in the NEXT UTC file), so every date is ACCUMULATED across files
    rather than computed per file.
    """
    days: dict[str, DayBars] = {}
    qa_totals: Counter = Counter()
    id_timeline: list[tuple[str, int]] = []   # (ts_et_iso, instrument_id) at changes
    prev_id = None

    for name in files:
        df, events = loader.load_real(name, source_format="dbn")
        for e in events:
            qa_totals[e.kind] += e.count
        et = df["ts"]
        dts = et.dt.strftime("%Y-%m-%d").to_numpy()
        mins = (et.dt.hour * 60 + et.dt.minute).to_numpy()
        o = df["open"].to_numpy(float)
        h = df["high"].to_numpy(float)
        lo = df["low"].to_numpy(float)
        c = df["close"].to_numpy(float)
        v = df["volume"].to_numpy(float)
        iid = df["instrument_id"].to_numpy()

        # instrument-id transitions (structural fact; cross-checked vs symbology)
        if len(iid):
            if prev_id is not None and iid[0] != prev_id:
                id_timeline.append((str(et.iloc[0]), int(iid[0])))
            chg = np.flatnonzero(iid[1:] != iid[:-1]) + 1
            for i in chg:
                id_timeline.append((str(et.iloc[i]), int(iid[i])))
            prev_id = iid[-1]

        # bars are time-ordered => each ET date is a contiguous slice
        uniq, starts = np.unique(dts, return_index=True)
        order = np.argsort(starts)
        uniq, starts = uniq[order], starts[order]
        bounds = list(starts) + [len(dts)]
        for k, d in enumerate(uniq):
            s, e = bounds[k], bounds[k + 1]
            db = days.setdefault(d, DayBars())
            m = mins[s:e]
            db.day_n += e - s
            db.day_h = _mm(db.day_h, float(np.max(h[s:e])), max)
            db.day_l = _mm(db.day_l, float(np.min(lo[s:e])), min)
            db.iids.update(int(x) for x in np.unique(iid[s:e]))

            rm = (m >= RTH_LO) & (m <= RTH_HI)
            if rm.any():
                idx = m[rm] - RTH_LO
                if len(np.unique(idx)) != len(idx):
                    raise RuntimeError(f"duplicate RTH minute on {d} — fail closed")
                db.o[idx] = o[s:e][rm]
                db.h[idx] = h[s:e][rm]
                db.l[idx] = lo[s:e][rm]
                db.c[idx] = c[s:e][rm]
                db.v[idx] = v[s:e][rm]
                db.n_rth += int(rm.sum())

            ev = m >= EVENING_LO
            if ev.any():
                db.eve_n += int(ev.sum())
                db.eve_h = _mm(db.eve_h, float(np.max(h[s:e][ev])), max)
                db.eve_l = _mm(db.eve_l, float(np.min(lo[s:e][ev])), min)
            er = m < RTH_LO
            if er.any():
                db.early_n += int(er.sum())
                db.early_h = _mm(db.early_h, float(np.max(h[s:e][er])), max)
                db.early_l = _mm(db.early_l, float(np.min(lo[s:e][er])), min)
        if verbose:
            print(f"  decoded {name}: {len(df)} bars", flush=True)
    return days, qa_totals, id_timeline


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def window_present(db: DayBars, lo: int, hi: int) -> int:
    return int(np.sum(~np.isnan(db.c[lo - RTH_LO:hi - RTH_LO + 1])))


def anchor_open(db: DayBars, minute: int) -> float:
    return float(db.o[minute - RTH_LO])


def anchor_close(db: DayBars, minute: int) -> float:
    return float(db.c[minute - RTH_LO])


def overnight_range(days: dict, all_dates: list[str],
                    prev_day: str, d: str) -> tuple[float, float, int]:
    """Overnight range = [prev trading day 18:00, d 09:30) — frozen L43.

    The span crosses non-trading ET dates (a Monday's overnight window holds
    the SUNDAY evening reopen bars), so every intermediate calendar date's
    whole-day block is included. No bar inside the span is ignored.
    """
    hi = lo = np.nan
    n = 0
    p = days.get(prev_day)
    if p is not None and p.eve_n:
        hi, lo, n = _mm(hi, p.eve_h, max), _mm(lo, p.eve_l, min), n + p.eve_n
    i0 = bisect.bisect_right(all_dates, prev_day)
    i1 = bisect.bisect_left(all_dates, d)
    for mid in all_dates[i0:i1]:
        m = days.get(mid)
        if m is not None and m.day_n:
            hi, lo, n = _mm(hi, m.day_h, max), _mm(lo, m.day_l, min), n + m.day_n
    cur = days.get(d)
    if cur is not None and cur.early_n:
        hi, lo, n = (_mm(hi, cur.early_h, max), _mm(lo, cur.early_l, min),
                     n + cur.early_n)
    return hi, lo, n


def path_length(closes: np.ndarray, first_ref: float) -> tuple[float, int]:
    """IR-15 path: |C_first - ref| + sum |dC| over the time-ordered ACTUALLY
    PRESENT close sequence. Absent minutes are skipped, never synthesised."""
    present = closes[~np.isnan(closes)]
    if present.size == 0 or np.isnan(first_ref):
        return np.nan, 0
    total = abs(present[0] - first_ref) + float(np.abs(np.diff(present)).sum())
    return total, present.size


def git_head() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                          capture_output=True, text=True,
                          check=True).stdout.strip()


# --------------------------------------------------------------------------
# forbidden-vocabulary guard (task spec section F)
# --------------------------------------------------------------------------

# Whole-word tokens only: substring matching would fire on legitimate
# structural vocabulary ("event", "development", "level", "evidence").
FORBIDDEN_TOKENS = (
    "return", "returns", "pnl", "ev", "sharpe", "hit", "hits", "hit_rate",
    "win", "wins", "win_rate", "winrate", "edge", "alpha_decay", "oracle",
    "profit", "profits", "roi", "drawdown_pct", "equity_curve", "backtest",
    "expectancy", "payoff",
)
_WORD_RE = None


def scan_forbidden(text: str) -> list[str]:
    """Return the forbidden strategy tokens present in `text` as whole words."""
    global _WORD_RE
    import re
    if _WORD_RE is None:
        _WORD_RE = re.compile(r"[A-Za-z_][A-Za-z_]*")
    seen = {w.lower() for w in _WORD_RE.findall(text)}
    return sorted(seen & set(FORBIDDEN_TOKENS))


def build_funnel(days: dict, close_min: dict) -> dict:
    """Pure eligibility funnel — frozen L44 order per the 2026-07-29 errata.

    scheduled
      -> minus zero-bar days                -> observed RTH days
      -> minus scheduled early-close days   -> regular full-session candidates
      -> minus RTH missing > 10% days       -> structurally eligible days
      -> minus ADR14 warm-up                -> final feature-construction dates

    `complete_390` is a SIDE DIAGNOSTIC, never a deduction stage; it is the
    lookback basis of the ADR14 warm-up test (frozen L49).
    """
    scheduled = sorted(close_min)
    early_close = {d for d, m in close_min.items() if m < 960}    # half day L44
    observed_rth = {d for d in scheduled if d in days and days[d].n_rth > 0}
    zero_bar = [d for d in scheduled if d not in observed_rth]

    removed_early = sorted(d for d in observed_rth if d in early_close)
    regular = sorted(observed_rth - set(removed_early))

    removed_missing = [
        d for d in regular
        if (EXPECTED_RTH_MINUTES - days[d].n_rth) / EXPECTED_RTH_MINUTES
        > MAX_MISSING_FRACTION]
    eligible = sorted(set(regular) - set(removed_missing))

    complete_390 = sorted(d for d in regular
                          if days[d].n_rth == EXPECTED_RTH_MINUTES)
    n_before = {d: i for i, d in enumerate(complete_390)}

    def prior_complete(d: str) -> int:
        i = n_before.get(d)
        return i if i is not None else int(np.searchsorted(complete_390, d))

    removed_warmup = [d for d in eligible
                      if prior_complete(d) < ADR_LOOKBACK_DAYS]
    final = sorted(set(eligible) - set(removed_warmup))

    checks = {
        "L0_minus_zero_bar_equals_L1":
            len(scheduled) - len(zero_bar) == len(observed_rth),
        "L1_minus_early_close_equals_L2":
            len(observed_rth) - len(removed_early) == len(regular),
        "L2_minus_missing_gt_10pct_equals_L3":
            len(regular) - len(removed_missing) == len(eligible),
        "L3_minus_adr14_warmup_equals_L4":
            len(eligible) - len(removed_warmup) == len(final),
        "removed_sets_mutually_disjoint": all(
            not (set(a) & set(b)) for a, b in
            [(zero_bar, removed_early), (zero_bar, removed_missing),
             (zero_bar, removed_warmup), (removed_early, removed_missing),
             (removed_early, removed_warmup), (removed_missing, removed_warmup)]),
        "no_date_vanishes_unaccounted":
            len(scheduled) == len(final) + len(zero_bar) + len(removed_early)
            + len(removed_missing) + len(removed_warmup),
        "no_rth_bars_on_unscheduled_days":
            not [d for d in days if days[d].n_rth > 0 and d not in close_min],
    }
    return {
        "scheduled": scheduled, "early_close": early_close,
        "observed_rth": observed_rth, "zero_bar": zero_bar,
        "removed_early": removed_early, "regular": regular,
        "removed_missing": removed_missing, "eligible": eligible,
        "complete_390": complete_390, "prior_complete": prior_complete,
        "removed_warmup": removed_warmup, "final": final, "checks": checks,
        "close_min": close_min,          # IR-19: scheduled close minute per day
    }


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def main() -> int:
    started = datetime.now(timezone.utc)
    print("S0_INPUT_PREFLIGHT — input eligibility only; real S0 NOT run.")

    # ---- startup preconditions (task spec: missing any one = STOP) -------
    dev_start, dev_end_excl = ROLE_WINDOWS[DataRole.DEVELOPMENT_SIGNAL]
    if dev_end_excl != "2022-01-01":
        raise RuntimeError(f"Development end boundary is {dev_end_excl}, "
                           "expected 2022-01-01 (M4-T2 regression) — STOP")
    f10_sha = hashlib.sha256(F10_CSV.read_bytes()).hexdigest()
    if f10_sha != F10_EXPECTED_SHA256:
        raise RuntimeError(f"f10_events.csv sha256 {f10_sha} != approved "
                           f"{F10_EXPECTED_SHA256} (IR-17 version) — STOP")
    f10_rows = sum(1 for _ in F10_CSV.open(encoding="utf-8")) - 1
    print(f"preconditions OK: dev end {dev_end_excl}; f10 sha256 verified "
          f"({f10_rows} rows)")

    loader = DevelopmentSignalLoader(A1_DIR)
    files = sorted(p.name for p in A1_DIR.glob("*.dbn.zst"))
    print(f"decoding {len(files)} A1 files via DevelopmentSignalLoader ...")
    days, qa_totals, id_timeline = extract_days(loader, files)

    # ---- frozen calendar -------------------------------------------------
    import pandas_market_calendars as mcal
    cal = mcal.get_calendar("CME_Equity")
    sched = cal.schedule(start_date=CAL_START, end_date=CAL_END)
    closes_et = sched["market_close"].dt.tz_convert("America/New_York")
    close_min = {str(pd.Timestamp(d).date()): c.hour * 60 + c.minute
                 for d, c in closes_et.items()}
    all_et_dates = sorted(days)

    # ================= A. ELIGIBILITY FUNNEL (frozen L44) =================
    fn = build_funnel(days, close_min)
    scheduled, early_close = fn["scheduled"], fn["early_close"]
    observed_rth, zero_bar = fn["observed_rth"], fn["zero_bar"]
    removed_early, regular_candidates = fn["removed_early"], fn["regular"]
    removed_missing = fn["removed_missing"]
    structurally_eligible = fn["eligible"]
    complete_390, prior_complete = fn["complete_390"], fn["prior_complete"]
    removed_warmup, final_dates = fn["removed_warmup"], fn["final"]
    funnel_checks = fn["checks"]
    if not all(funnel_checks.values()):
        raise RuntimeError(f"funnel conservation violated: {funnel_checks}")

    # ================= B. EXACT ANCHORS ==================================
    # Population = every day that clears the funnel's frozen exclusions
    # (structurally_eligible). ADR14 warm-up is a normalisation warm-up, not a
    # data defect, so anchors are also reported on the final set.
    obs_order = sorted(observed_rth)
    obs_index = {d: i for i, d in enumerate(obs_order)}

    # ---- IR-19 reference-session machinery -------------------------------
    # Reference day = the immediately previous ACTUAL CME RTH session,
    # independent of downstream sample eligibility. Distinguish two kinds of
    # zero-bar scheduled days: true market closures (no session existed —
    # walked THROUGH) vs vendor-degraded days (a session existed, data is
    # missing — they ARE the reference day and the anchor is NA; skipping
    # past them is prohibited).
    cond = json.loads((A1_DIR / "condition.json").read_text(encoding="utf-8"))
    degraded_dates = {r["date"] for r in cond if r["condition"] != "available"}
    vendor_zero_bar = set(zero_bar) & degraded_dates
    true_closures = set(zero_bar) - vendor_zero_bar
    sched_order = sorted(scheduled)
    sched_index = {d: i for i, d in enumerate(sched_order)}
    close_min = fn["close_min"]

    def prev_actual_session(d: str) -> str | None:
        """Walk back through the schedule; skip only TRUE closures."""
        i = sched_index.get(d)
        if i is None:
            i = bisect.bisect_left(sched_order, d)
        while i > 0:
            i -= 1
            p = sched_order[i]
            if p in true_closures:
                continue                    # no session ever happened
            return p                        # observed OR vendor-degraded
        return None

    anchors = {k: {"available": 0, "missing": 0, "missing_dates": [],
                   "missing_detail": [], "missing_reasons": Counter()}
               for k in ("O0930", "C0959", "O1000", "C1544", "prev_rth_close")}

    def classify_missing(d: str, minute: int) -> str:
        """Why is an exact anchor absent? Categories mirror DATA_QA_ADDENDUM
        section 4+5; nothing is substituted for the missing bar (IR-15)."""
        if d in ("2020-02-28", "2020-06-30"):
            return "vendor_degraded_gap"
        if d.startswith("2020-03"):
            return "market_halt_period"
        if d in early_close:
            return "scheduled_early_close_session"
        if d < "2014-01-01":
            return "no_trade_minutes_omitted_thin_era"
        return "missing_minute_unclassified"

    prev_close_val: dict[str, float] = {}
    prev_close_from_early_close: list[str] = []      # IR-19 sidecar flag
    for d in structurally_eligible:
        db = days[d]
        for key, minute, getter in (("O0930", M_0930, anchor_open),
                                    ("C0959", M_0959, anchor_close),
                                    ("O1000", M_1000, anchor_open),
                                    ("C1544", M_1544, anchor_close)):
            val = getter(db, minute)
            if np.isnan(val):
                why = classify_missing(d, minute)
                anchors[key]["missing"] += 1
                anchors[key]["missing_dates"].append(d)
                anchors[key]["missing_detail"].append({"date": d, "reason": why})
                anchors[key]["missing_reasons"][why] += 1
            else:
                anchors[key]["available"] += 1

        # IR-19 (revised Option B, APPROVED 2026-07-29): regular reference
        # day -> 15:59 bar close; scheduled early-close reference day -> the
        # final SCHEDULED RTH bar's close (that day's real official session
        # close — the anchor itself, not a substitute) + sidecar flag;
        # scheduled close bar itself absent -> NA; vendor-degraded reference
        # day -> NA (never skipped); first sample day -> NA. Never "last
        # available bar", never forward fill, never nearest-bar.
        p = prev_actual_session(d)
        pv = np.nan
        from_early_close = False
        if p is None:
            reason = "no_prior_rth_session_in_sample"
        elif p in vendor_zero_bar or p not in days or days[p].n_rth == 0:
            reason = "prev_day_vendor_degraded_zero_bar"
        else:
            sched_close_bar = (close_min[p] - 1 if p in early_close
                               else M_1559)
            pv = anchor_close(days[p], sched_close_bar)
            reason = ""
            from_early_close = p in early_close and not np.isnan(pv)
            if np.isnan(pv):
                reason = ("prev_day_early_close_final_scheduled_bar_absent"
                          if p in early_close
                          else "prev_day_1559_bar_absent")
        if np.isnan(pv):
            anchors["prev_rth_close"]["missing"] += 1
            anchors["prev_rth_close"]["missing_dates"].append(d)
            anchors["prev_rth_close"]["missing_detail"].append(
                {"date": d, "prev_rth_session": p, "reason": reason})
            anchors["prev_rth_close"]["missing_reasons"][reason] += 1
        else:
            anchors["prev_rth_close"]["available"] += 1
            prev_close_val[d] = pv
            if from_early_close:
                prev_close_from_early_close.append(d)

    # ================= C. NON-CRITICAL MISSING MINUTES (IR-15) ============
    # Frozen whole-day exclusions were applied ABOVE; the vendor-degraded
    # >10% days are therefore already gone and are NOT counted as retained.
    opening_path_affected, pm_path_affected = [], []
    for d in structurally_eligible:
        db = days[d]
        if window_present(db, W1_LO, W1_HI) < 30:
            opening_path_affected.append(d)
        if window_present(db, W2_LO, W2_HI) < 345:
            pm_path_affected.append(d)

    # ================= D. F1-F11 CONSTRUCTIBILITY ========================
    # Values computed in memory ONLY to classify NA/constructible. Discarded.
    f10 = load_f10(structurally_eligible)
    roll = load_roll(obs_order, structurally_eligible)

    feats = {f"F{i}": {"constructible": 0, "na": 0, "reasons": Counter()}
             for i in range(1, 12)}
    fvals: dict[str, list[float]] = {f"F{i}": [] for i in range(1, 12)}

    # ADR14 per day (mean prior-14 complete-RTH-day RTH range) — memory only.
    comp_range = {}
    for d in complete_390:
        db = days[d]
        comp_range[d] = float(np.nanmax(db.h) - np.nanmin(db.l))

    def adr14(d: str) -> float:
        i = prior_complete(d)
        if i < ADR_LOOKBACK_DAYS:
            return np.nan
        return float(np.mean([comp_range[x] for x in
                              complete_390[i - ADR_LOOKBACK_DAYS:i]]))

    # F4 reference: prior 60 observed RTH trading days with a complete 30-bar
    # observation window. The frozen text fixes the LENGTH (60 trading days)
    # and the window, not the day-set; the rule used here is disclosed and
    # raised as an open item (DECISION_PACKET_PREFLIGHT_F4_LOOKBACK_BASIS).
    obs_vol_hist: list[tuple[str, float]] = []
    for d in obs_order:
        db = days[d]
        if window_present(db, W1_LO, W1_HI) == 30:
            obs_vol_hist.append((d, float(np.nansum(db.v[W1_LO - RTH_LO:
                                                         W1_HI - RTH_LO + 1]))))
    vol_dates = [x[0] for x in obs_vol_hist]
    vol_vals = [x[1] for x in obs_vol_hist]

    zero_direction_days: list[str] = []

    def rec(name: str, ok: bool, reason: str, val: float = np.nan) -> None:
        if ok:
            feats[name]["constructible"] += 1
            fvals[name].append(val)
        else:
            feats[name]["na"] += 1
            feats[name]["reasons"][reason] += 1

    for d in structurally_eligible:
        db = days[d]
        a = adr14(d)
        adr_na = np.isnan(a)
        o930 = anchor_open(db, M_0930)
        c959 = anchor_close(db, M_0959)
        w1c = db.c[W1_LO - RTH_LO:W1_HI - RTH_LO + 1]
        w1h = db.h[W1_LO - RTH_LO:W1_HI - RTH_LO + 1]
        w1l = db.l[W1_LO - RTH_LO:W1_HI - RTH_LO + 1]

        # F1 ret_open30
        if np.isnan(o930) or np.isnan(c959):
            rec("F1", False, "anchor_missing")
        elif adr_na:
            rec("F1", False, "adr14_warmup")
        else:
            rec("F1", True, "", (c959 - o930) / a)

        # F2 or_width
        if np.all(np.isnan(w1h)):
            rec("F2", False, "window_empty")
        elif adr_na:
            rec("F2", False, "adr14_warmup")
        else:
            rec("F2", True, "", (np.nanmax(w1h) - np.nanmin(w1l)) / a)

        # F3 de_open30 (IR-15 present-close path)
        p, _n = path_length(w1c, o930)
        if np.isnan(o930) or np.isnan(c959):
            rec("F3", False, "anchor_missing")
        elif np.isnan(p) or p == 0:
            rec("F3", False, "path_zero_or_undefined")
        else:
            rec("F3", True, "", abs(c959 - o930) / p)

        # F4 rvol_open30
        j = int(np.searchsorted(vol_dates, d))
        if window_present(db, W1_LO, W1_HI) == 0:
            rec("F4", False, "window_empty")
        elif j < F4_LOOKBACK_DAYS:
            rec("F4", False, "f4_lookback_warmup")
        else:
            med = float(np.median(vol_vals[j - F4_LOOKBACK_DAYS:j]))
            cur = float(np.nansum(db.v[W1_LO - RTH_LO:W1_HI - RTH_LO + 1]))
            rec("F4", True, "", np.nan if med == 0 else cur / med)

        # F5 gap — NA on is_roll_transition (frozen L57)
        if d in roll["transition_dates"]:
            rec("F5", False, "roll_transition_day_na")
        elif np.isnan(o930):
            rec("F5", False, "anchor_missing")
        elif d not in prev_close_val:
            rec("F5", False, "prev_rth_close_anchor_missing")
        elif adr_na:
            rec("F5", False, "adr14_warmup")
        else:
            rec("F5", True, "", (o930 - prev_close_val[d]) / a)

        # F6 / F7 overnight — span starts at the previous ACTUAL session's
        # 18:00 (IR-19 session semantics); overnight_range itself tolerates
        # data-less reference days (n==0 -> NA, never substituted).
        p_day = prev_actual_session(d)
        on_h, on_l, on_n = (overnight_range(days, all_et_dates, p_day, d)
                            if p_day else (np.nan, np.nan, 0))
        if on_n == 0 or np.isnan(on_h):
            rec("F6", False, "overnight_window_empty")
            rec("F7", False, "overnight_window_empty")
        else:
            if np.isnan(o930):
                rec("F6", False, "anchor_missing")
            elif on_h == on_l:
                rec("F6", False, "overnight_range_zero")
            else:
                rec("F6", True, "", (o930 - on_l) / (on_h - on_l))
            if adr_na:
                rec("F7", False, "adr14_warmup")
            else:
                rec("F7", True, "", (on_h - on_l) / a)

        # F8 retrace_open30 (directional running-max drawdown, frozen L75-77)
        if np.isnan(o930) or np.isnan(c959):
            rec("F8", False, "anchor_missing")
        elif c959 == o930:
            # frozen L82: ret_open30 == 0 -> no direction, not tradeable,
            # counted and reported separately. Recorded here as a COUNT only.
            zero_direction_days.append(d)
            rec("F8", False, "zero_denominator_no_direction")
        else:
            dr = np.sign(c959 - o930)
            z = dr * (w1c[~np.isnan(w1c)] - o930)
            rec("F8", True, "", float(np.max(np.maximum.accumulate(z) - z))
                / abs(c959 - o930))

        # F9 close_pos_open30
        if np.isnan(c959) or np.all(np.isnan(w1h)):
            rec("F9", False, "anchor_missing")
        elif np.nanmax(w1h) == np.nanmin(w1l):
            rec("F9", False, "zero_range_denominator")
        else:
            rec("F9", True, "",
                (c959 - np.nanmin(w1l)) / (np.nanmax(w1h) - np.nanmin(w1l)))

        # F10 event category (IR-12 + IR-13). The numeric code exists ONLY so
        # the is_constant check is meaningful; it is never reported.
        cats = f10["per_date"].get(d, [])
        if len(cats) > 1:
            rec("F10", False, "multi_event_day_single_category_undetermined")
        else:
            code = {"CPI": 1.0, "NFP": 2.0, "FOMC": 3.0}.get(
                cats[0] if cats else "none", 0.0)
            rec("F10", True, "", code)

        # F11 roll flags — structural booleans, never NA
        rec("F11", True, "", 1.0 if d in roll["transition_dates"] else 0.0)

    for k in feats:
        vals = [x for x in fvals[k] if not np.isnan(x)]
        feats[k]["is_constant"] = bool(len(set(vals)) <= 1) if vals else None
        feats[k]["reasons"] = dict(feats[k]["reasons"])

    # ================= E. LABEL ANCHORS (existence only) =================
    adr_ok = {d for d in structurally_eligible if not np.isnan(adr14(d))}
    labels = label_anchor_availability(days, structurally_eligible, adr_ok)

    # ---- cross-check vs DATA_QA_ADDENDUM --------------------------------
    w1_complete = sum(1 for d in observed_rth
                      if window_present(days[d], W1_LO, W1_HI) == 30)
    w2_complete = sum(1 for d in regular_candidates
                      if window_present(days[d], W2_LO, W2_HI) == 345)
    xcheck = [
        ("scheduled trading days", len(scheduled), 2989),
        ("scheduled early closes", len(early_close), 97),
        ("observed RTH days", len(observed_rth), 2969),
        ("zero-bar scheduled days", len(zero_bar), 20),
        ("0930-1000 complete days", w1_complete, 2960),
        ("1000-1544 complete days", w2_complete, 2873),
        ("1000-1544 early-close excluded", len(removed_early), 85),
        ("complete 390-bar RTH days", len(complete_390), 2870),
        ("ADR14 warm-up days", len(removed_warmup), 14),
        ("roll transitions", roll["n_transitions"], 47),
    ]
    xcheck_rows = [{"item": a, "preflight": b, "addendum": c, "match": a_eq}
                   for a, b, c in xcheck for a_eq in (b == c,)]
    xcheck_all_match = all(r["match"] for r in xcheck_rows)

    payload = {
        "stage": STAGE,
        "real_s0": REAL_S0,
        "approval": APPROVAL,
        # Commit metadata scheme (Aaron 2026-07-29): historical facts +
        # render-time head; NO self-referential final-commit field.
        "input_commit": git_head(),
        "subagent_integration_commit":
            "a8faf31593cad152dd83c9da236c3e236c47b47d",
        "post_integration_fix_commit":
            "c557c3b4a84ef41890fbc2a1689623eac8ae0ed9",
        "report_rendered_from_head": git_head(),
        "generated_at_utc": started.isoformat(),
        "development_window": {"start_inclusive": dev_start,
                               "end_exclusive": dev_end_excl},
        "source": {"a1_job_dir": str(A1_DIR), "n_files": len(files),
                   "read_path": "DevelopmentSignalLoader.load_real",
                   "loader_qa_events": dict(qa_totals)},
        "funnel": {
            "L0_scheduled_trading_days": len(scheduled),
            "minus_zero_bar_days": len(zero_bar),
            "L1_observed_rth_days": len(observed_rth),
            "minus_scheduled_early_close_days": len(removed_early),
            "L2_regular_full_session_candidates": len(regular_candidates),
            "minus_rth_missing_gt_10pct_days": len(removed_missing),
            "L3_structurally_eligible_days": len(structurally_eligible),
            "minus_adr14_warmup_days": len(removed_warmup),
            "L4_final_feature_construction_dates": len(final_dates),
            "removed_sets": {
                "zero_bar_days": zero_bar,
                "scheduled_early_close_days": removed_early,
                "rth_missing_gt_10pct_days": removed_missing,
                "adr14_warmup_days": removed_warmup,
            },
            "conservation_checks": funnel_checks,
            "side_diagnostic_complete_390_bar_rth_days": len(complete_390),
            "first_final_date": final_dates[0] if final_dates else None,
            "last_final_date": final_dates[-1] if final_dates else None,
        },
        "anchors": {k: {"population": "L3_structurally_eligible_days",
                        "available": v["available"], "missing": v["missing"],
                        "missing_dates": v["missing_dates"],
                        "missing_detail": v["missing_detail"],
                        "missing_reasons": dict(v["missing_reasons"]),
                        "downstream": "field_na_day_retained"}
                    for k, v in anchors.items()},
        "prev_close_from_early_close_day_sidecar": {   # IR-19 diagnostic flag
            "count": len(prev_close_from_early_close),
            "dates": prev_close_from_early_close,
            "rule": ("IR-19 revised Option B: reference day = immediately "
                     "previous actual CME RTH session; early-close reference "
                     "day anchors at its final SCHEDULED RTH bar close; "
                     "vendor-degraded reference days are never skipped")},
        "zero_direction_days_frozen_L82": {
            "count": len(zero_direction_days),
            "dates": zero_direction_days,
            "note": ("ret_open30 == 0 exactly: frozen L82 requires these be "
                     "counted and reported separately as no-direction, "
                     "non-tradeable days. The day is NOT deleted."),
        },
        "na_reason_precedence": [
            "reasons are assigned by FIRST match in the documented order per "
            "feature; a day can satisfy several (e.g. an ADR14 warm-up day "
            "that is also a roll transition is counted once, under the "
            "earlier test), so reason counts sum to the NA total exactly",
            "F5 order: roll_transition_day_na, anchor_missing, "
            "prev_rth_close_anchor_missing, adr14_warmup",
        ],
        "path_features_ir15": {
            "opening_path_affected_days": len(opening_path_affected),
            "opening_path_affected_dates": opening_path_affected,
            "pm_path_affected_days": len(pm_path_affected),
            "pm_path_affected_dates": pm_path_affected,
            "excluded_before_this_layer_gt10pct": removed_missing,
        },
        "features": feats,
        "f4_lookback_rule_disclosure": {
            "rule_used": ("prior 60 OBSERVED RTH trading days that have a "
                          "complete 30-bar 09:30-10:00 window, strictly "
                          "preceding the day, scheduled early-close days "
                          "included (their morning window is a normal one)"),
            "frozen_text_fixes": "the LENGTH (60 trading days) and the window",
            "frozen_text_does_not_fix": "which day-set counts as the 60",
            "na_days_under_this_rule": feats["F4"]["na"],
            "OPEN_ITEM": ("affects only the F4 NA count at the start of the "
                          "sample; no day is deleted. See "
                          "DECISION_PACKET_PREFLIGHT_F4_LOOKBACK_BASIS.md"),
        },
        "startup_preconditions": {
            "roles_dev_end_exclusive_is_2022_01_01": dev_end_excl == "2022-01-01",
            "roles_module_constant_name": ("ROLE_WINDOWS[DataRole."
                                           "DEVELOPMENT_SIGNAL] — the task "
                                           "spec called it DEV_END_EXCLUSIVE; "
                                           "that name lives in dbn_loader.py "
                                           "which derives it from this map"),
            "f10_events_csv_sha256": f10_sha,
            "f10_events_csv_sha256_matches_ir17": f10_sha == F10_EXPECTED_SHA256,
            "f10_events_csv_rows": f10_rows,
        },
        "f10": f10["summary"],
        "f11_roll": roll["summary"],
        "labels": labels,
        "cross_check_vs_data_qa_addendum": {
            "all_match": xcheck_all_match, "rows": xcheck_rows},
    }

    OUT_JSON.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    OUT_MD.write_text(render_report(payload), encoding="utf-8")
    print(f"\nwrote {OUT_JSON.name} and {OUT_MD.name}")
    print(f"funnel final dates: {len(final_dates)} | "
          f"cross-check all_match={xcheck_all_match}")
    return 0


# --------------------------------------------------------------------------
# F10 / F11 inputs
# --------------------------------------------------------------------------

def load_f10(eligible: list[str]) -> dict:
    """Encode F10 per IR-13 (category membership) then IR-12 (multi -> NA)."""
    df = pd.read_csv(F10_CSV)
    cpi = set(df.loc[df.is_cpi_release_day, "date_et"])
    nfp = set(df.loc[df.is_nfp_release_day, "date_et"])
    stmt = set(df.loc[df.is_fomc_statement_day, "date_et"])
    unsched = stmt & set(UNSCHEDULED_FOMC)            # IR-13 diagnostic only
    fomc = stmt - unsched                             # the 92 scheduled days

    per_date: dict[str, list[str]] = {}
    for name, s in (("CPI", cpi), ("NFP", nfp), ("FOMC", fomc)):
        for d in s:
            per_date.setdefault(d, []).append(name)

    elig = set(eligible)
    multi = sorted(d for d, v in per_date.items() if len(v) > 1)
    # Diagnostic sidecar (IR-12): raw multi-event days over ALL rows of the
    # frozen table, i.e. BEFORE IR-13 narrows FOMC to scheduled statement days.
    raw_multi = sorted(df.groupby("date_et")["event_type"].nunique()
                       .pipe(lambda s: s[s > 1]).index)

    # Mutually-exclusive partition of the eligible population (Aaron report
    # fix 2026-07-29): single-category days by their category, multi ->
    # NA_multi_event, rest none; MUST sum exactly to the population.
    excl = {"CPI": len((cpi - nfp - fomc) & elig),
            "NFP": len((nfp - cpi - fomc) & elig),
            "FOMC": len((fomc - cpi - nfp) & elig),
            "none": len(elig - (cpi | nfp | fomc)),
            "NA_multi_event": len(set(multi) & elig)}
    excl_ok = sum(excl.values()) == len(elig)
    if not excl_ok:
        raise RuntimeError(f"F10 exclusive partition {excl} does not sum to "
                           f"population {len(elig)} — STOP")

    per_year = (df.assign(y=df.date_et.str[:4])
                  .groupby(["y", "event_type"]).size().unstack(fill_value=0))
    years_missing = [y for y in per_year.index
                     if int(per_year.loc[y].sum()) == 0]
    # FOMC rows above count every calendar entry (a two-day meeting is 2 rows);
    # the F10-relevant figure is the SCHEDULED STATEMENT day count per year.
    stmt_per_year = Counter(d[:4] for d in fomc)

    summary = {
        "encoding": "IR-13 category membership, then IR-12 multi-event -> NA",
        "category_day_counts": {
            "CPI": len(cpi), "NFP": len(nfp),
            "FOMC_scheduled_statement_days": len(fomc),
        },
        "fomc_statement_rows_in_table": len(stmt),
        "unscheduled_fomc_action_diagnostic": sorted(unsched),
        "intersection_with_eligible_days": {
            "CPI": len(cpi & elig), "NFP": len(nfp & elig),
            "FOMC": len(fomc & elig),
            "none": len(elig - (cpi | nfp | fomc)),
        },
        "multi_event_na_days_post_ir13": {
            "count": len(multi), "dates": multi,
            "count_intersecting_eligible": len(set(multi) & elig)},
        "raw_multi_event_days_pre_ir13_sidecar": {
            "count": len(raw_multi), "dates": list(raw_multi)},
        "ir18_resolution": ("APPROVED 2026-07-29: primary conflict detection "
                            "runs AFTER IR-13 eligibility; 19 = raw "
                            "diagnostic sidecar count, 9 = primary F10 NA "
                            "days; the 10 single-remaining-category days "
                            "encode as their unique CPI/NFP category."),
        # Aaron report-governance fix (2026-07-29): membership counts are
        # OVERLAPPING; the frozen single-category F10 field needs the
        # mutually-exclusive partition, asserted to sum to the population.
        "raw_category_membership_counts_eligible": {
            "CPI": len(cpi & elig), "NFP": len(nfp & elig),
            "FOMC": len(fomc & elig)},
        "final_mutually_exclusive_F10_counts_eligible": excl,
        "partition_assertion_sum_equals_population": excl_ok,
        "per_year_counts": json.loads(per_year.to_json(orient="index")),
        "per_year_fomc_scheduled_statement_days": dict(sorted(
            stmt_per_year.items())),
        "years_with_no_events": years_missing,
        "ir17_rows_without_official_time": int(
            (df.release_time_status
             == "official_time_unavailable_in_archived_source").sum()),
    }
    return {"per_date": per_date, "summary": summary}


def load_roll(obs_order: list[str], eligible: list[str]) -> dict:
    """F11 / F5 roll semantics (Aaron 2026-07-29 errata, mandatory).

    The mapping switches at 00:00 UTC == 19:00/20:00 ET the PRIOR evening,
    which is the pre-open of the NEXT CME session. is_roll_transition therefore
    maps to the first valid RTH session date on/after the official interval
    start d0 — never a Sunday ET calendar date, never a bare UTC/ET date cut.
    """
    m = pd.read_csv(SYMBOLOGY_CSV)
    obs = list(obs_order)
    obs_set = set(obs)
    idx = {d: i for i, d in enumerate(obs)}

    transitions = []
    for _, row in m.iloc[1:].iterrows():             # 48 intervals -> 47 switches
        d0 = row["start_date_utc"]
        rth = next((d for d in obs if d >= d0), None)
        transitions.append({
            "interval_start_utc": d0,
            "interval_end_utc_excl": row["end_date_utc_excl"],
            "raw_symbol": row["raw_symbol"],
            "instrument_id": int(row["instrument_id"]),
            "rth_session_date": rth,
            "weekday": (pd.Timestamp(rth).day_name() if rth else None),
            "inside_official_interval": bool(
                rth is not None and d0 <= rth < row["end_date_utc_excl"]),
        })
    tdates = {t["rth_session_date"] for t in transitions if t["rth_session_date"]}

    window: set[str] = set()
    for t in tdates:
        i = idx.get(t)
        if i is None:
            continue
        lo = max(0, i - ROLL_WINDOW_TRADING_DAYS)
        hi = min(len(obs) - 1, i + ROLL_WINDOW_TRADING_DAYS)
        window.update(obs[lo:hi + 1])

    asserts = {
        "n_transitions_is_47": len(transitions) == 47,
        "all_map_to_valid_rth_trading_day": all(
            t["rth_session_date"] in obs_set for t in transitions),
        "no_weekend_transition": all(
            t["weekday"] not in ("Saturday", "Sunday") for t in transitions),
        "all_inside_official_interval": all(
            t["inside_official_interval"] for t in transitions),
        "distinct_transition_dates": len(tdates) == len(transitions),
    }
    elig = set(eligible)
    return {
        "transition_dates": tdates,
        "n_transitions": len(transitions),
        "summary": {
            "source": "gate1/symbology/nq_v0_mapping.csv (IR-16, 48 intervals)",
            "semantics": ("transition instant 00:00 UTC = prior-evening ET "
                          "pre-open; mapped to the first valid RTH session "
                          "date on/after the official interval start"),
            "n_transitions": len(transitions),
            "assertions": asserts,
            "all_assertions_pass": all(asserts.values()),
            "addendum_section8_cross_check_47": len(transitions) == 47,
            "is_roll_transition_days_in_eligible": len(tdates & elig),
            "is_roll_window_days": len(window),
            "is_roll_window_days_in_eligible": len(window & elig),
            "transitions": transitions,
        },
    }


def label_anchor_availability(days: dict, eligible: list[str],
                              adr_ok: set[str]) -> dict:
    """Frozen L86-91 — ANCHOR EXISTENCE ONLY. No label value, no distribution,
    no relation to any future price is computed anywhere in this function.

    ADR14 is a REQUIRED input wherever the frozen formula normalises by it
    (Y_cont, Y1, Y4, Y5); Y2 and Y3 are pure ratios and need no ADR14.
    """
    spec = {
        "Y_cont": ["O1000", "C1544", "ADR14", "d_open(O0930,C0959)"],
        "Y1": ["O1000", "C1544", "ADR14"],
        "Y2": ["O1000", "C1544", "PM close path"],
        "Y3": ["C1544", "PM high", "PM low"],
        "Y4": ["O1000", "PM high", "PM low", "ADR14", "d_open(O0930,C0959)"],
        "Y5": ["O1000", "PM high", "PM low", "ADR14", "d_open(O0930,C0959)"],
    }
    out = {k: {"required_anchors": v, "available_days": 0, "unavailable_days": 0}
           for k, v in spec.items()}
    for d in eligible:
        db = days[d]
        o1000 = anchor_open(db, M_1000)
        c1544 = anchor_close(db, M_1544)
        o930 = anchor_open(db, M_0930)
        c959 = anchor_close(db, M_0959)
        pm_h = db.h[W2_LO - RTH_LO:W2_HI - RTH_LO + 1]
        pm_c = db.c[W2_LO - RTH_LO:W2_HI - RTH_LO + 1]
        pm_ok = not np.all(np.isnan(pm_h))
        d_ok = not (np.isnan(o930) or np.isnan(c959)) and c959 != o930
        a_ok = d in adr_ok
        ok = {
            "Y_cont": (not np.isnan(o1000) and not np.isnan(c1544)
                       and a_ok and d_ok),
            "Y1": not np.isnan(o1000) and not np.isnan(c1544) and a_ok,
            "Y2": (not np.isnan(o1000) and not np.isnan(c1544)
                   and np.sum(~np.isnan(pm_c)) > 0),
            "Y3": not np.isnan(c1544) and pm_ok,
            "Y4": not np.isnan(o1000) and pm_ok and a_ok and d_ok,
            "Y5": not np.isnan(o1000) and pm_ok and a_ok and d_ok,
        }
        for k, good in ok.items():
            out[k]["available_days" if good else "unavailable_days"] += 1
    for k in out:
        out[k]["note"] = ("anchor existence only; ADR14 availability is "
                          "reported by the funnel warm-up stage")
    return out


# --------------------------------------------------------------------------
# report rendering
# --------------------------------------------------------------------------

def render_report(p: dict) -> str:
    f = p["funnel"]
    L = []
    A = L.append
    A("# S0 INPUT PREFLIGHT REPORT")
    A("")
    A(f"- stage: `{p['stage']}`")
    A(f"- real_s0: `{p['real_s0']}`")
    A(f"- approval: `{p['approval']}`")
    A(f"- input_commit: `{p['input_commit']}`")
    A(f"- subagent_integration_commit: `{p['subagent_integration_commit']}`")
    A(f"- post_integration_fix_commit: `{p['post_integration_fix_commit']}`")
    A(f"- report_rendered_from_head: `{p['report_rendered_from_head']}`")
    A(f"- generated_at_utc: `{p['generated_at_utc']}`")
    A("")
    A("Input-eligibility verification only. This document contains counts, "
      "booleans, reason classifications and status fields exclusively. No "
      "feature value, no distribution, no label value, no cost figure, no "
      "simulation output and no judgment appears anywhere in it, by "
      "construction and by machine-checked guard (tests/test_preflight.py).")
    A("")
    A(f"Read path: `{p['source']['read_path']}` over "
      f"{p['source']['n_files']} archived A1 files. Development window "
      f"[{p['development_window']['start_inclusive']}, "
      f"{p['development_window']['end_exclusive']}). Loader QA events: "
      f"{p['source']['loader_qa_events'] or 'none'}.")
    A("")
    A("## 0. Startup preconditions")
    A("")
    sp = p["startup_preconditions"]
    A(f"- Development end-exclusive boundary is 2022-01-01: "
      f"**{sp['roles_dev_end_exclusive_is_2022_01_01']}**")
    A(f"- frozen event table sha256 matches the IR-17 approved bytes: "
      f"**{sp['f10_events_csv_sha256_matches_ir17']}** "
      f"(`{sp['f10_events_csv_sha256']}`, {sp['f10_events_csv_rows']} rows)")
    A(f"- naming note: {sp['roles_module_constant_name']}")
    A("")
    A("## 1. Date eligibility funnel")
    A("")
    A("Order per the 2026-07-29 errata. Each level is conserved "
      "(parent = child + removed) and all removed sets are mutually disjoint, "
      "so no date can vanish unaccounted for.")
    A("")
    A("| stage | operation | count |")
    A("|---|---|---|")
    A(f"| L0 | scheduled trading days | {f['L0_scheduled_trading_days']} |")
    A(f"| -- | minus zero-bar days | {f['minus_zero_bar_days']} |")
    A(f"| L1 | observed RTH days | {f['L1_observed_rth_days']} |")
    A(f"| -- | minus scheduled early-close days | "
      f"{f['minus_scheduled_early_close_days']} |")
    A(f"| L2 | regular full-session candidates | "
      f"{f['L2_regular_full_session_candidates']} |")
    A(f"| -- | minus RTH missing > 10% days | "
      f"{f['minus_rth_missing_gt_10pct_days']} |")
    A(f"| L3 | structurally eligible days | "
      f"{f['L3_structurally_eligible_days']} |")
    A(f"| -- | minus ADR14 warm-up | {f['minus_adr14_warmup_days']} |")
    A(f"| **L4** | **final feature-construction dates** | "
      f"**{f['L4_final_feature_construction_dates']}** |")
    A("")
    A(f"Final range: {f['first_final_date']} .. {f['last_final_date']}.")
    A("")
    A("Side diagnostic (NOT a funnel deduction stage; also the lookback basis "
      f"for the ADR14 warm-up test): complete 390-bar RTH days = "
      f"{f['side_diagnostic_complete_390_bar_rth_days']}.")
    A("")
    A("Conservation checks:")
    A("")
    for k, v in f["conservation_checks"].items():
        A(f"- `{k}`: **{v}**")
    A("")
    A(f"Removed — RTH missing > 10%: "
      f"{', '.join(f['removed_sets']['rth_missing_gt_10pct_days']) or 'none'}.")
    A(f"Removed — ADR14 warm-up: "
      f"{f['removed_sets']['adr14_warmup_days'][0]} .. "
      f"{f['removed_sets']['adr14_warmup_days'][-1]} "
      f"({len(f['removed_sets']['adr14_warmup_days'])} days).")
    A("")
    A("## 2. Exact anchors")
    A("")
    A("Population = L3 structurally eligible days. No forward fill, no "
      "next-bar substitution, no interpolation, no last-trade substitution, "
      "no implicit completion of any kind was applied (IR-15).")
    A("")
    A("| anchor | available | missing | missing reasons | downstream |")
    A("|---|---|---|---|---|")
    for k, v in p["anchors"].items():
        rs = ", ".join(f"{a}={b}" for a, b in v["missing_reasons"].items()) or "-"
        A(f"| {k} | {v['available']} | {v['missing']} | {rs} | "
          f"`{v['downstream']}` |")
    A("")
    for k, v in p["anchors"].items():
        if v["missing_dates"]:
            A(f"- {k} missing on: {', '.join(v['missing_dates'])}")
    A("")
    A("Downstream handling follows frozen L44-L45 only: a missing exact anchor "
      "makes the dependent field NA and the day is retained. The prior-day "
      "close anchor follows IR-19 (revised Option B, APPROVED 2026-07-29): "
      "reference day = immediately previous ACTUAL CME RTH session "
      "(independent of sample eligibility); early-close reference days anchor "
      "at their final SCHEDULED RTH bar close (their real official session "
      "close, flagged in the sidecar); vendor-degraded reference days are "
      "never skipped and yield NA; no substitute bar, no forward fill.")
    sc = p["prev_close_from_early_close_day_sidecar"]
    A("")
    A(f"IR-19 sidecar `prev_close_from_early_close_day`: {sc['count']} days.")
    A("")
    z = p["zero_direction_days_frozen_L82"]
    A(f"### Frozen L82 no-direction days: {z['count']}")
    A("")
    A(f"{z['note']}")
    A("")
    A(f"Dates: {', '.join(z['dates']) or 'none'}")
    A("")
    A("NA reason precedence:")
    A("")
    for line in p["na_reason_precedence"]:
        A(f"- {line}")
    A("")
    A("## 3. Non-critical missing minutes (IR-15)")
    A("")
    pf = p["path_features_ir15"]
    A(f"- days excluded BEFORE this layer by the frozen > 10% rule: "
      f"{', '.join(pf['excluded_before_this_layer_gt10pct']) or 'none'} "
      "(not counted as retained path-feature days)")
    A(f"- opening path (09:30-10:00) affected days: "
      f"{pf['opening_path_affected_days']}"
      + (f" — {', '.join(pf['opening_path_affected_dates'])}"
         if pf['opening_path_affected_dates'] else ""))
    A(f"- PM path (10:00-15:44) affected days: {pf['pm_path_affected_days']}"
      + (f" — {', '.join(pf['pm_path_affected_dates'])}"
         if pf['pm_path_affected_dates'] else ""))
    A("")
    A("## 4. F1-F11 constructibility")
    A("")
    A("Features were computed in memory solely to classify constructibility, "
      "NA status, NA reason and constancy. No value is reported.")
    A("")
    A("| feature | constructible days | NA days | is_constant | NA reasons |")
    A("|---|---|---|---|---|")
    for k, v in p["features"].items():
        rs = ", ".join(f"{a}={b}" for a, b in v["reasons"].items()) or "-"
        A(f"| {k} | {v['constructible']} | {v['na']} | {v['is_constant']} | {rs} |")
    A("")
    q = p["f4_lookback_rule_disclosure"]
    A("### F4 lookback basis (disclosed rule)")
    A("")
    A(f"- rule used: {q['rule_used']}")
    A(f"- the frozen text fixes: {q['frozen_text_fixes']}")
    A(f"- the frozen text does NOT fix: {q['frozen_text_does_not_fix']}")
    A(f"- NA days under this rule: {q['na_days_under_this_rule']}")
    A(f"- **OPEN ITEM**: {q['OPEN_ITEM']}")
    A("")
    A("### F10 event coverage")
    A("")
    s = p["f10"]
    A(f"- encoding: {s['encoding']}")
    A(f"- category day counts: {s['category_day_counts']}")
    A("- raw category MEMBERSHIP counts on eligible days (overlapping — "
      "multi-event days appear in every category they belong to): "
      f"{s['raw_category_membership_counts_eligible']}")
    ex = s["final_mutually_exclusive_F10_counts_eligible"]
    A(f"- **final mutually-exclusive F10 counts** (frozen single-category "
      f"field): {ex}")
    A(f"- partition assertion CPI+NFP+FOMC+none+NA_multi_event == population: "
      f"**{s['partition_assertion_sum_equals_population']}** "
      f"(sum = {sum(ex.values())})")
    A(f"- FOMC statement rows in the frozen table: "
      f"{s['fomc_statement_rows_in_table']}; minus the four IR-13 "
      f"`unscheduled_fomc_action` diagnostic dates "
      f"({', '.join(s['unscheduled_fomc_action_diagnostic'])}) = "
      f"{s['category_day_counts']['FOMC_scheduled_statement_days']} scheduled "
      "statement days")
    A(f"- multi-event NA days after IR-13: "
      f"{s['multi_event_na_days_post_ir13']['count']} — "
      f"{', '.join(s['multi_event_na_days_post_ir13']['dates'])}")
    A(f"- diagnostic sidecar, raw multi-event days before IR-13: "
      f"{s['raw_multi_event_days_pre_ir13_sidecar']['count']} — "
      f"{', '.join(s['raw_multi_event_days_pre_ir13_sidecar']['dates'])}")
    A(f"- IR-18 resolution: {s['ir18_resolution']}")
    A(f"- IR-17 rows carrying no official release time: "
      f"{s['ir17_rows_without_official_time']} (date-level encoding unaffected; "
      "no day deleted, F10 not made NA by this)")
    A(f"- years with no matching event in the Development window: "
      f"{s['years_with_no_events'] or 'none'}")
    A("")
    A("| year | CPI | NFP | FOMC rows (all calendar entries) | "
      "FOMC scheduled statement days (F10) |")
    A("|---|---|---|---|---|")
    for y, row in sorted(s["per_year_counts"].items()):
        A(f"| {y} | {row.get('CPI', 0)} | {row.get('NFP', 0)} | "
          f"{row.get('FOMC', 0)} | "
          f"{s['per_year_fomc_scheduled_statement_days'].get(y, 0)} |")
    A("")
    A("The `FOMC rows` column counts every official calendar entry (a two-day "
      "meeting contributes 2 rows, conference calls and notation votes are "
      "included as archived); only the last column feeds F10 under IR-13.")
    A("")
    A("### F11 / F5 roll session-date semantics")
    A("")
    r = p["f11_roll"]
    A(f"- source: {r['source']}")
    A(f"- semantics: {r['semantics']}")
    A(f"- transitions: {r['n_transitions']} "
      f"(DATA_QA_ADDENDUM section 8 cross-check 47: "
      f"{r['addendum_section8_cross_check_47']})")
    for k, v in r["assertions"].items():
        A(f"- `{k}`: **{v}**")
    A(f"- is_roll_transition days inside the eligible set: "
      f"{r['is_roll_transition_days_in_eligible']}")
    A(f"- is_roll_window days: {r['is_roll_window_days']} "
      f"(inside eligible set: {r['is_roll_window_days_in_eligible']})")
    A("")
    A("## 5. Label anchors (existence only)")
    A("")
    A("| label | required anchors | days with all anchors | days missing >=1 |")
    A("|---|---|---|---|")
    for k, v in p["labels"].items():
        A(f"| {k} | {', '.join(v['required_anchors'])} | "
          f"{v['available_days']} | {v['unavailable_days']} |")
    A("")
    A("No label value, distribution, mean, frequency or any forward-looking "
      "statistic was computed.")
    A("")
    A("## 6. Cross-check vs DATA_QA_ADDENDUM.md")
    A("")
    x = p["cross_check_vs_data_qa_addendum"]
    A("| item | preflight | addendum | match |")
    A("|---|---|---|---|")
    for row in x["rows"]:
        A(f"| {row['item']} | {row['preflight']} | {row['addendum']} | "
          f"{row['match']} |")
    A("")
    A(f"**All items match: {x['all_match']}**")
    A("")
    A("## 7. Status")
    A("")
    A(f"- `{p['stage']}`")
    A(f"- `REAL_S0_{p['real_s0']}`")
    A(f"- `{p['approval']}`")
    A("")
    A("Real S0 was not run. No strategy figure of any kind was produced.")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    sys.exit(main())
