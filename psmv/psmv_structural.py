"""R1 — S1 PRE-SEAL MECHANICAL VALIDATION (PSMV), structural only.

AUTHORITY
    OD-1_DATA_AUTHORITY = GRANT (delegated Owner ruling, 2026-09-17):
    existing NQ Development OHLCV + frozen F10 CPI/NFP calendar + derived
    spread-cost table, for R1 only. NOT Internal Validation, NOT Lockbox,
    NOT protected ITSF outcome artifacts.

    This module is authorized for the PRE-SEAL structural read ONLY. It is not
    the R1 outcome engine, it computes no signal and no return, and running it
    neither seals S1 nor starts S2.

PURITY CONTRACT (invariant L-13)
    This module reads EXACTLY ONE field from every decoded record: `ts_event`.
    It never names, selects, dereferences or persists `open`, `high`, `low`,
    `close`, `volume` or any quantity derived from them. Consequently it CANNOT
    emit a price, a price difference, a return, a signal sign, a P&L, a
    dispersion or any outcome statistic -- not by policy, but because those
    values never enter a variable.

    ADR14 is resolved as AVAILABILITY ONLY. The frozen ADR14 rule needs the
    mean RTH (high-low) of the prior 14 COMPLETE RTH days; whether it EXISTS
    depends only on how many complete-390-bar days precede the date, which is
    a BAR COUNT. PSMV computes the count and never the value.

REUSED FROZEN LOGIC (by transcription against a pinned digest, not by import:
    the parked ITSF repository is never loaded, executed or modified)
    - eligibility funnel order and thresholds   ITSF s0/context.build_funnel
    - complete_390 / ADR14 warm-up rule         ITSF s0/context._adr14_map
    - roll-transition session mapping           ITSF s0/context._roll_map
    - roll window = transition +- 2 RTH days    ITSF data/calendar (S0 SS1)
    - CME_Equity schedule, 2010-06-06..2021-12-31, close-minute < 960 = early
      close                                     ITSF scripts/s0_input_preflight

OUTPUT
    artifacts/PSMV_STRUCTURAL_REPORT.json  -- counts, booleans, dates, reason
                                              codes and digests only
"""
from __future__ import annotations

import bisect
import csv
import hashlib
import json
import sys
from collections import Counter
from datetime import date as _date
from pathlib import Path

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------
# Pinned inputs. Every one is verified by digest before it is used.
# --------------------------------------------------------------------------
WORKSPACE = Path(r"C:\Users\Aaron\OneDrive\Desktop\Quant trade")
ITSF = WORKSPACE / "Intraday Trend Strategy Framework"
PROJECT = WORKSPACE / "nq-event-diffusion-research"

JOB_DIR = Path(r"C:\Users\Aaron\quant-data\databento-archive"
               r"\intraday-trend\development_signal\GLBX-20260727-DL3BEBCHJA")

EVENT_CSV = ITSF / "gate1" / "f10_event_calendar" / "f10_events.csv"
EVENT_CSV_SHA256 = ("5e92ad00737339c392ed2c0927736e196e076e18"
                    "5897c146c884d5f515bb5e8c")          # IR-17, L-11
SYMBOLOGY_CSV = ITSF / "gate1" / "symbology" / "nq_v0_mapping.csv"

OUT_JSON = PROJECT / "artifacts" / "PSMV_STRUCTURAL_REPORT.json"

# --------------------------------------------------------------------------
# Frozen constants (ITSF S0 SS1/SS3/SS4; transcribed, not re-derived)
# --------------------------------------------------------------------------
ET = "America/New_York"
CAL_START, CAL_END = "2010-06-06", "2021-12-31"
RTH_LO_MINUTE, RTH_HI_MINUTE = 9 * 60 + 30, 15 * 60 + 59   # 570 .. 959
EXPECTED_RTH_MINUTES = 390
MAX_MISSING_FRACTION = 0.10
REGULAR_CLOSE_MINUTE = 16 * 60
ADR_LOOKBACK_DAYS = 14
ROLL_WINDOW_TRADING_DAYS = 2

# R1 required structural anchors (P-2 = OPTION A, delegated ruling 2026-09-17).
# These name BAR LOCATIONS whose EXISTENCE is tested. No value is read.
ANCHORS = {
    "C_0829": 8 * 60 + 29,    # 509  last bar starting strictly before 08:30
    "C_0831": 8 * 60 + 31,    # 511  second post-release bar
    "O_0833": 8 * 60 + 33,    # 513  primary entry bar
    "O_0929": 9 * 60 + 29,    # 569  timed exit bar
}
MINUTES_PER_DAY = 1440


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# --------------------------------------------------------------------------
# 1. Data identity
# --------------------------------------------------------------------------
def verify_and_list_data_files() -> tuple[list[Path], str]:
    """Verify every ohlcv-1m file against the vendor manifest. Fail closed."""
    manifest = json.loads((JOB_DIR / "manifest.json").read_text(encoding="utf-8"))
    expected = {e["filename"]: e["hash"].split(":", 1)[1] for e in manifest["files"]}
    files = sorted(JOB_DIR.glob("*.ohlcv-1m.dbn.zst"))
    if not files:
        raise SystemExit("PSMV: no ohlcv-1m files found -- fail closed")
    digests = []
    for p in files:
        want = expected.get(p.name)
        if want is None:
            raise SystemExit(f"PSMV: {p.name} absent from vendor manifest -- fail closed")
        got = sha256_file(p)
        if got != want:
            raise SystemExit(f"PSMV: digest mismatch on {p.name} -- fail closed")
        digests.append(got)
    roll_up = hashlib.sha256("\n".join(sorted(digests)).encode()).hexdigest()
    return files, roll_up


# --------------------------------------------------------------------------
# 2. Structural decode -- ts_event ONLY
# --------------------------------------------------------------------------
def scan_bar_structure(files: list[Path]) -> tuple[dict[str, np.ndarray], int]:
    """date_et -> uint16[1440] count of bars starting in each ET minute.

    The ONLY record field named anywhere in this function is 'ts_event'.
    """
    import databento as dbn

    per_day: dict[str, np.ndarray] = {}
    total = 0
    for p in files:
        arr = dbn.DBNStore.from_file(p).to_ndarray()
        ts = arr["ts_event"]                      # <-- the only field ever read
        del arr
        if len(ts) == 0:
            continue
        total += len(ts)
        idx = pd.DatetimeIndex(pd.to_datetime(np.asarray(ts, dtype="int64"),
                                              utc=True)).tz_convert(ET)
        minute = (idx.hour * 60 + idx.minute).to_numpy(dtype=np.int32)
        daykey = idx.strftime("%Y-%m-%d").to_numpy()
        uniq, inverse = np.unique(daykey, return_inverse=True)
        for i, d in enumerate(uniq):
            counts = per_day.get(d)
            if counts is None:
                counts = np.zeros(MINUTES_PER_DAY, dtype=np.uint16)
                per_day[d] = counts
            np.add.at(counts, minute[inverse == i], 1)
    return per_day, total


# --------------------------------------------------------------------------
# 3. CME_Equity schedule
# --------------------------------------------------------------------------
def build_close_minutes() -> dict[str, int]:
    import pandas_market_calendars as mcal

    sched = mcal.get_calendar("CME_Equity").schedule(start_date=CAL_START,
                                                     end_date=CAL_END)
    closes = sched["market_close"].dt.tz_convert(ET)
    return {str(pd.Timestamp(d).date()): int(c.hour) * 60 + int(c.minute)
            for d, c in zip(sched.index, closes)}


# --------------------------------------------------------------------------
# 4. Frozen eligibility funnel (transcribed from ITSF build_funnel)
# --------------------------------------------------------------------------
def build_funnel(n_rth: dict[str, int], close_min: dict[str, int]) -> dict:
    scheduled = sorted(close_min)
    early_close = {d for d, m in close_min.items() if m < REGULAR_CLOSE_MINUTE}
    observed_rth = sorted(d for d in scheduled if n_rth.get(d, 0) > 0)
    obs_set = set(observed_rth)
    zero_bar = [d for d in scheduled if d not in obs_set]
    removed_early = sorted(d for d in observed_rth if d in early_close)
    regular = sorted(obs_set - set(removed_early))
    removed_missing = [d for d in regular
                       if (EXPECTED_RTH_MINUTES - n_rth[d]) / EXPECTED_RTH_MINUTES
                       > MAX_MISSING_FRACTION]
    eligible = sorted(set(regular) - set(removed_missing))
    complete_390 = sorted(d for d in regular if n_rth[d] == EXPECTED_RTH_MINUTES)
    removed_warmup = [d for d in eligible
                      if bisect.bisect_left(complete_390, d) < ADR_LOOKBACK_DAYS]
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
        "no_date_vanishes_unaccounted":
            len(scheduled) == len(final) + len(zero_bar) + len(removed_early)
            + len(removed_missing) + len(removed_warmup),
        "no_rth_bars_on_unscheduled_days":
            not [d for d in n_rth if n_rth[d] > 0 and d not in close_min],
    }
    return {"scheduled": scheduled, "observed_rth": observed_rth,
            "zero_bar": zero_bar, "early_close": sorted(early_close),
            "removed_early": removed_early, "regular": regular,
            "removed_missing": removed_missing, "eligible": eligible,
            "complete_390": complete_390, "removed_warmup": removed_warmup,
            "final": final, "checks": checks}


def adr14_available(funnel: dict, d: str) -> bool:
    """AVAILABILITY only: >= 14 complete-390 RTH days strictly before d."""
    return bisect.bisect_left(funnel["complete_390"], d) >= ADR_LOOKBACK_DAYS


# --------------------------------------------------------------------------
# 5. Frozen roll mapping (transcribed from ITSF _roll_map)
# --------------------------------------------------------------------------
def roll_flags(funnel: dict) -> tuple[list[str], list[str], list[dict]]:
    observed = funnel["observed_rth"]
    rows = list(csv.DictReader(SYMBOLOGY_CSV.open(encoding="utf-8")))
    detail, tdates = [], set()
    for iv in rows[1:]:                       # N intervals -> N-1 switches
        start, end_excl = iv["start_date_utc"], iv["end_date_utc_excl"]
        i = bisect.bisect_left(observed, start)
        session = observed[i] if i < len(observed) else None
        inside = bool(session is not None and start <= session < end_excl)
        if not inside:
            raise SystemExit(
                f"PSMV: roll interval [{start}, {end_excl}) {iv['raw_symbol']} "
                f"resolved to session {session!r}, outside the official "
                "interval -- fail closed (ITSF f11_roll assertions)")
        detail.append({"interval_start_utc": start, "raw_symbol": iv["raw_symbol"],
                       "rth_session_date": session,
                       "inside_official_interval": inside})
        tdates.add(session)
    index = {d: i for i, d in enumerate(observed)}
    window: set[str] = set()
    for t in tdates:
        i = index[t]
        lo = max(0, i - ROLL_WINDOW_TRADING_DAYS)
        hi = min(len(observed) - 1, i + ROLL_WINDOW_TRADING_DAYS)
        window.update(observed[lo:hi + 1])
    return sorted(tdates), sorted(window), detail


# --------------------------------------------------------------------------
# 6. Event universe
# --------------------------------------------------------------------------
def load_events() -> dict:
    got = sha256_file(EVENT_CSV)
    if got != EVENT_CSV_SHA256:
        raise SystemExit("PSMV: f10_events.csv digest mismatch -- fail closed (L-11)")
    rows = list(csv.DictReader(EVENT_CSV.open(encoding="utf-8")))
    for r in rows:
        if r["event_type"] in ("CPI", "NFP") and \
                r["release_time_status"] != "official_time_recorded":
            raise SystemExit("PSMV: a BLS row lacks an attested release time "
                             "-- fail closed (L-2/L-3)")
    cpi = {r["date_et"] for r in rows if r["is_cpi_release_day"] == "true"}
    nfp = {r["date_et"] for r in rows if r["is_nfp_release_day"] == "true"}
    fomc_any = {r["date_et"] for r in rows if r["event_type"] == "FOMC"}
    return {"cpi": cpi, "nfp": nfp, "fomc_any": fomc_any, "sha256": got}


# --------------------------------------------------------------------------
# 7. Main
# --------------------------------------------------------------------------
def main() -> int:
    print("PSMV: verifying data identity ...", flush=True)
    files, files_rollup = verify_and_list_data_files()
    print(f"PSMV: {len(files)} ohlcv-1m files verified", flush=True)

    print("PSMV: structural decode (ts_event only) ...", flush=True)
    per_day, total_bars = scan_bar_structure(files)
    n_rth = {d: int(c[RTH_LO_MINUTE:RTH_HI_MINUTE + 1].sum())
             for d, c in per_day.items()}
    distinct_rth = {d: int((c[RTH_LO_MINUTE:RTH_HI_MINUTE + 1] > 0).sum())
                    for d, c in per_day.items()}
    dup_days = sorted(d for d in n_rth if n_rth[d] != distinct_rth[d])
    print(f"PSMV: {total_bars} bars, {len(per_day)} ET dates", flush=True)

    close_min = build_close_minutes()
    funnel = build_funnel(n_rth, close_min)
    trans, rwindow, roll_detail = roll_flags(funnel)
    ev = load_events()

    # ---- E0 .. E3, conserved ------------------------------------------
    e0 = sorted(ev["cpi"] | ev["nfp"])
    r_fomc = sorted(d for d in e0 if d in ev["fomc_any"])
    e1 = sorted(set(e0) - set(r_fomc))
    tset = set(trans)
    r_roll = sorted(d for d in e1 if d in tset)
    e2 = sorted(set(e1) - set(r_roll))

    anchor_missing: dict[str, list[str]] = {k: [] for k in ANCHORS}
    reason: Counter = Counter()
    per_event_reason: dict[str, str] = {}
    e3 = []
    for d in e2:
        counts = per_day.get(d)
        reasons = []
        if counts is None:
            reasons.append("no_bars_on_date")
            for k in ANCHORS:
                anchor_missing[k].append(d)
        else:
            for k, m in ANCHORS.items():
                if counts[m] == 0:
                    anchor_missing[k].append(d)
                    reasons.append(f"anchor_missing_{k}")
        if not adr14_available(funnel, d):
            reasons.append("adr14_warmup_insufficient_prior_complete_days")
        if reasons:
            # first-match precedence, ITSF NA-reason convention
            per_event_reason[d] = reasons[0]
            reason[reasons[0]] += 1
        else:
            e3.append(d)
    e3 = sorted(e3)

    # Structural characterisation of every E3 removal: weekday, schedule
    # membership, bar count and first/last bar MINUTE. Timestamps and counts
    # only -- no value of any bar is read.
    e3_detail = []
    for d in sorted(per_event_reason):
        counts = per_day.get(d)
        nz = [] if counts is None else [i for i, v in enumerate(counts) if v > 0]
        fmt = lambda m: "%02d:%02d" % (m // 60, m % 60)   # noqa: E731
        e3_detail.append({
            "date_et": d,
            "event_type": "CPI" if d in ev["cpi"] else "NFP",
            "weekday": _date.fromisoformat(d).strftime("%A"),
            "cme_equity_scheduled": d in close_min,
            "bars_on_et_date": 0 if counts is None else int(counts.sum()),
            "first_bar_minute_et": fmt(nz[0]) if nz else None,
            "last_bar_minute_et": fmt(nz[-1]) if nz else None,
            "n_rth_bars": int(n_rth.get(d, 0)),
            "prior_complete_390_days": bisect.bisect_left(
                funnel["complete_390"], d),
            "reason": per_event_reason[d],
        })

    conservation = {
        "E0_minus_fomc_equals_E1": len(e0) - len(r_fomc) == len(e1),
        "E1_minus_roll_transition_equals_E2": len(e1) - len(r_roll) == len(e2),
        "E2_minus_anchor_or_adr14_equals_E3":
            len(e2) - len(per_event_reason) == len(e3),
        "removed_sets_mutually_disjoint": all(
            not (set(a) & set(b)) for a, b in
            ((r_fomc, r_roll), (r_fomc, per_event_reason),
             (r_roll, per_event_reason))),
        "no_event_vanishes_unaccounted":
            len(e0) == len(e3) + len(r_fomc) + len(r_roll) + len(per_event_reason),
        "cpi_and_nfp_never_coincide": not (ev["cpi"] & ev["nfp"]),
    }

    def split(dates):
        y = Counter(d[:4] for d in dates)
        ep = Counter("2010-2013" if int(d[:4]) <= 2013 else
                     "2014-2017" if int(d[:4]) <= 2017 else "2018-2021"
                     for d in dates)
        micro = Counter("counterfactual_micro_execution" if d < "2019-05-06"
                        else "actual_micro_available_era" for d in dates)
        typ = Counter("CPI" if d in ev["cpi"] else "NFP" for d in dates)
        return {"per_year": dict(sorted(y.items())), "per_epoch": dict(ep),
                "per_micro_era": dict(micro), "per_event_type": dict(typ)}

    report = {
        "artifact": "R1_PSMV_STRUCTURAL_REPORT",
        "schema": "r1_psmv_structural.v1",
        "stage": "S1_PRE_SEAL_MECHANICAL_VALIDATION",
        "purity_contract": "L-13: counts, booleans, dates, reason codes and "
                           "digests only. The decoder read field 'ts_event' "
                           "and no other. No price, return, sign, P&L, "
                           "dispersion or outcome statistic exists in this "
                           "artifact or in the process that produced it.",
        "authority": {
            "OD_1_DATA_AUTHORITY": "GRANT (R1 scope only)",
            "INTERNAL_VALIDATION": "NOT GRANTED / NOT ACCESSED",
            "LOCKBOX": "NOT GRANTED / NOT ACCESSED",
            "PROTECTED_ITSF_OUTCOMES": "NOT GRANTED / NOT ACCESSED",
            "S1_SEALED": False, "S2_AUTHORIZED": False,
        },
        "inputs": {
            "job_dir": str(JOB_DIR),
            "ohlcv_1m_files_verified": len(files),
            "files_digest_rollup_sha256": files_rollup,
            "event_calendar_sha256": ev["sha256"],
            "symbology_csv_sha256": sha256_file(SYMBOLOGY_CSV),
            "calendar_source": "pandas_market_calendars CME_Equity",
            "calendar_span": [CAL_START, CAL_END],
        },
        "bar_structure": {
            "total_bars_decoded": total_bars,
            "et_dates_with_bars": len(per_day),
            "duplicate_rth_minute_days": dup_days,
        },
        "session_funnel": {
            "L0_scheduled_trading_days": len(funnel["scheduled"]),
            "minus_zero_bar_days": len(funnel["zero_bar"]),
            "L1_observed_rth_days": len(funnel["observed_rth"]),
            "minus_scheduled_early_close_days": len(funnel["removed_early"]),
            "L2_regular_full_session_candidates": len(funnel["regular"]),
            "minus_rth_missing_gt_10pct_days": len(funnel["removed_missing"]),
            "L3_structurally_eligible_days": len(funnel["eligible"]),
            "minus_adr14_warmup_days": len(funnel["removed_warmup"]),
            "L4_final_feature_construction_dates": len(funnel["final"]),
            "side_diagnostic_complete_390_bar_rth_days":
                len(funnel["complete_390"]),
            "checks": funnel["checks"],
        },
        "roll": {
            "n_intervals_in_mapping": len(roll_detail) + 1,
            "n_transitions": len(roll_detail),
            "n_distinct_transition_sessions": len(trans),
            "all_map_to_valid_rth_trading_day": True,
            "all_inside_official_interval": True,
            "is_roll_window_days_total": len(rwindow),
            "transition_sessions": trans,
        },
        "event_funnel": {
            "E0_cpi_or_nfp_calendar_events": len(e0),
            "E1_minus_any_fomc_calendar_entry": {
                "removed": len(r_fomc), "remaining": len(e1),
                "removed_dates": r_fomc},
            "E2_minus_exact_roll_transition_sessions": {
                "removed": len(r_roll), "remaining": len(e2),
                "removed_dates": r_roll},
            "E3_minus_missing_required_structural_anchors": {
                "removed": len(per_event_reason), "remaining": len(e3),
                "removed_by_reason": dict(reason),
                "removed_dates": sorted(per_event_reason),
                "removed_detail": e3_detail},
            "E4_r_init_zero_no_direction": {
                "status": "DEFERRED_TO_S2",
                "why": "R_init == 0 is a comparison of two bar CLOSE PRICES. "
                       "Evaluating it pre-seal would require inspecting market "
                       "values, which invariant L-13 forbids. PSMV therefore "
                       "stops at E3, the deepest structurally decidable point."},
            "conservation_checks": conservation,
        },
        "anchor_availability": {
            "required_anchors": {k: f"minute_of_day_et={v}"
                                 for k, v in ANCHORS.items()},
            "note": "presence/absence of the named BAR LOCATION only; no value "
                    "of any anchor bar was read",
            "population": "E2 (post-FOMC-exclusion, post-roll-exclusion)",
            "population_size": len(e2),
            "present": {k: len(e2) - len(v) for k, v in anchor_missing.items()},
            "missing": {k: len(v) for k, v in anchor_missing.items()},
            "missing_dates": {k: v for k, v in anchor_missing.items()},
            "adr14_availability": {
                "rule": "ADR14 exists iff >= 14 complete-390-bar RTH days "
                        "precede the event date (value never computed)",
                "unavailable": sum(1 for d in e2 if not adr14_available(funnel, d)),
                "unavailable_dates": [d for d in e2
                                      if not adr14_available(funnel, d)],
            },
        },
        "pre_seal_structural_n": len(e3),
        "post_seal_signal_defined_n": None,
        "balance_at_pre_seal_structural_n": split(e3),
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=False) + "\n",
                        encoding="utf-8")
    print(f"PSMV: wrote {OUT_JSON}", flush=True)
    print(f"PSMV: PRE_SEAL_STRUCTURAL_N = {len(e3)}", flush=True)
    bad = [k for k, v in {**funnel["checks"], **conservation}.items() if not v]
    if bad:
        print("PSMV: FAILED CHECKS -> " + ", ".join(bad), flush=True)
        return 1
    print("PSMV: all conservation and funnel checks PASS", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
