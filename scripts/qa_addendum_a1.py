"""QA Addendum — A1 structural sweep (Aaron 2026-07-29 spec, QA-only).

Emits ONLY structural facts to a JSON intermediate:
per-file bar counts / ts extremes / manifest verification, per-date minute
occupancy vs the frozen calendar (pandas-market-calendars CME Equity, per
STUDY_0_PREREGISTRATION SS "日历"), window completeness for 09:30-10:00 and
10:00-15:44 ET, ADR14 lookback AVAILABILITY (no ADR values computed),
explicit anomaly counts, DST/holiday/half-day/roll handling.

FORBIDDEN: strategy returns, Oracle, EV, features, labels, verdicts.
Exchange-closed time is never counted as missing (Aaron item 9).
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from itsf.guards import assert_real_run_allowed                    # noqa: E402
from itsf.data.dbn_loader import DevelopmentSignalLoader           # noqa: E402

A1_DIR = Path(r"C:\Users\Aaron\quant-data\databento-archive\intraday-trend"
              r"\development_signal\GLBX-20260727-DL3BEBCHJA")
OUT_JSON = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "qa_addendum_a1.json"

# Frozen S0 windows (STUDY_0_PREREGISTRATION lines 41-42):
# 观察窗 09:30-09:59 bar; 决策 10:00; 强制退出以 15:44 bar 收盘价 (15:45 exit)
W1_LO, W1_HI = 570, 599        # 09:30..09:59 inclusive -> 30 bars
W2_LO, W2_HI = 600, 944        # 10:00..15:44 inclusive -> 345 bars
RTH_LO, RTH_HI = 570, 959      # 09:30..15:59 -> 390 bars (ADR14 完整 RTH 日)
CAL_START, CAL_END = "2010-06-06", "2021-12-31"


def main() -> int:
    assert_real_run_allowed()                     # fail-closed BEFORE any open

    ldr = DevelopmentSignalLoader(A1_DIR)
    files = sorted(p.name for p in A1_DIR.glob("*.dbn.zst"))

    per_file = []
    qa_totals: Counter = Counter()
    occ: dict[str, np.ndarray] = {}               # ET date -> 1440 minute counts
    n_nan = n_inf = n_nonpos = n_ohlc_viol = n_zero_vol = n_zero_vol_rth = 0
    global_min_utc = global_max_utc = None
    rolls = []                                    # instrument_id transitions
    prev_id = None
    prev_file_last_utc = None
    file_overlap = []

    for name in files:
        df, events = ldr.load_real(name, source_format="dbn")
        for e in events:
            qa_totals[e.kind] += e.count
        et = df["ts"]                             # tz-aware ET from loader
        utc = et.dt.tz_convert("UTC")
        lo_u, hi_u = utc.min(), utc.max()
        global_min_utc = lo_u if global_min_utc is None else min(global_min_utc, lo_u)
        global_max_utc = hi_u if global_max_utc is None else max(global_max_utc, hi_u)
        if prev_file_last_utc is not None and lo_u <= prev_file_last_utc:
            file_overlap.append(name)
        prev_file_last_utc = hi_u

        dates = et.dt.date.astype(str)
        minutes = (et.dt.hour * 60 + et.dt.minute).to_numpy()
        for (d, m), c in df.groupby([dates, minutes]).size().items():
            occ.setdefault(d, np.zeros(1440, np.uint32))[m] += c

        ohlc = df[["open", "high", "low", "close"]]
        arr = ohlc.to_numpy(float)
        n_nan += int(np.isnan(arr).any(axis=1).sum())
        n_inf += int(np.isinf(arr).any(axis=1).sum())
        n_nonpos += int((np.nan_to_num(arr, nan=1.0) <= 0).any(axis=1).sum())
        viol = ((df["high"] < df["low"])
                | (df["high"] < ohlc[["open", "close"]].max(axis=1))
                | (df["low"] > ohlc[["open", "close"]].min(axis=1)))
        n_ohlc_viol += int(viol.sum())
        zv = df["volume"] <= 0
        n_zero_vol += int(zv.sum())
        rth_mask = (minutes >= RTH_LO) & (minutes <= RTH_HI)
        n_zero_vol_rth += int((zv.to_numpy() & rth_mask).sum())

        if "instrument_id" in df.columns:
            ids = df["instrument_id"].to_numpy()
            if prev_id is not None and len(ids) and ids[0] != prev_id:
                rolls.append({"ts_et": str(et.iloc[0]), "old": int(prev_id),
                              "new": int(ids[0])})
            chg = np.flatnonzero(ids[1:] != ids[:-1]) + 1
            for i in chg:
                rolls.append({"ts_et": str(et.iloc[i]), "old": int(ids[i - 1]),
                              "new": int(ids[i])})
            if len(ids):
                prev_id = ids[-1]

        per_file.append({"file": name, "n_bars": int(len(df)),
                         "first_ts_utc": str(lo_u), "last_ts_utc": str(hi_u),
                         "first_date_et": str(et.dt.date.min()),
                         "last_date_et": str(et.dt.date.max()),
                         "manifest_sha256_verified": True,
                         "qa_events": {e.kind: e.count for e in events}})
        print(f"done {name}: {len(df)} bars", flush=True)

    # --- frozen calendar (prereg: pandas-market-calendars CME Equity) --------
    import pandas_market_calendars as mcal
    cal = mcal.get_calendar("CME_Equity")
    sched = cal.schedule(start_date=CAL_START, end_date=CAL_END)
    closes_et = sched["market_close"].dt.tz_convert("America/New_York")
    cal_days = {}                                 # date iso -> close minute
    for d, c in closes_et.items():
        cal_days[str(pd.Timestamp(d).date())] = c.hour * 60 + c.minute
    early_close_days = {d for d, m in cal_days.items() if m < 960}

    def win_count(v: np.ndarray, lo: int, hi: int) -> int:
        return int((v[lo:hi + 1] > 0).sum())

    w1_complete = w1_incomplete_full = 0
    w2_complete = 0
    w2_excl_early = w2_incomplete_full = 0
    w1_missing_minutes = w2_missing_minutes = 0
    incomplete_detail = []
    complete_rth_days = []                        # for ADR14 availability
    candidate_days = []                           # both windows complete
    obs_rth_days = set()
    dup_minutes_global = 0
    for d in sorted(occ):
        v = occ[d]
        dup_minutes_global += int((v > 1).sum())
        if win_count(v, RTH_LO, RTH_HI) == 0:
            continue                              # no RTH bars: not an RTH day
        obs_rth_days.add(d)
        c1 = win_count(v, W1_LO, W1_HI)
        if c1 == 30:
            w1_complete += 1
        else:
            w1_incomplete_full += 1
            w1_missing_minutes += 30 - c1
            incomplete_detail.append({"date": d, "window": "0930-1000",
                                      "present": c1, "expected": 30,
                                      "reason": ("early_close" if d in early_close_days
                                                 else "missing_data")})
        if d in early_close_days:
            w2_excl_early += 1                    # afternoon closed: excluded,
            continue                              # NOT missing minutes (item 9)
        c2 = win_count(v, W2_LO, W2_HI)
        if c2 == 345:
            w2_complete += 1
        else:
            w2_incomplete_full += 1
            w2_missing_minutes += 345 - c2
            incomplete_detail.append({"date": d, "window": "1000-1544",
                                      "present": c2, "expected": 345,
                                      "reason": "missing_data"})
        if d not in early_close_days and win_count(v, RTH_LO, RTH_HI) == 390:
            complete_rth_days.append(d)
        if c1 == 30 and c2 == 345:
            candidate_days.append(d)

    # ADR14 lookback AVAILABILITY (no values computed): a candidate day has a
    # full lookback iff >=14 complete-RTH days strictly precede it.
    complete_sorted = sorted(complete_rth_days)
    n_before = {d: i for i, d in enumerate(complete_sorted)}
    warmup, first_full = [], None
    for d in sorted(candidate_days):
        prior = n_before.get(d, sum(1 for x in complete_sorted if x < d))
        if prior < 14:
            warmup.append(d)
        elif first_full is None:
            first_full = d

    cal_set = set(cal_days)
    zero_bar_cal_days = sorted(cal_set - obs_rth_days)      # scheduled, no RTH bars
    rth_on_noncal = sorted(obs_rth_days - cal_set)          # RTH bars off-calendar

    # DST transitions inside coverage
    days_idx = pd.date_range(CAL_START, CAL_END, freq="D", tz="America/New_York")
    offs = [t.utcoffset() for t in days_idx]
    dst_days = [str(days_idx[i].date()) for i in range(1, len(days_idx))
                if offs[i] != offs[i - 1]]
    dst_with_rth = [d for d in dst_days if d in obs_rth_days]

    cond = json.loads((A1_DIR / "condition.json").read_text(encoding="utf-8"))
    cond_tally = Counter(r["condition"] for r in cond)
    cond_bad = [r["date"] for r in cond if r["condition"] != "available"]

    OUT_JSON.write_text(json.dumps({
        "per_file": per_file, "qa_event_totals": dict(qa_totals),
        "n_files": len(files), "total_bars": sum(f["n_bars"] for f in per_file),
        "global_first_ts_utc": str(global_min_utc),
        "global_last_ts_utc": str(global_max_utc),
        "global_first_ts_et": str(global_min_utc.tz_convert("America/New_York")),
        "global_last_ts_et": str(global_max_utc.tz_convert("America/New_York")),
        "file_boundary_overlaps": file_overlap,
        "counts": {"nan_price_rows": n_nan, "inf_price_rows": n_inf,
                   "nonpositive_price_rows": n_nonpos,
                   "ohlc_consistency_violations": n_ohlc_viol,
                   "zero_or_neg_volume_rows": n_zero_vol,
                   "zero_or_neg_volume_rows_rth": n_zero_vol_rth,
                   "duplicate_date_minute_slots": dup_minutes_global},
        "calendar": {"lib": "pandas-market-calendars CME_Equity",
                     "trading_days_scheduled": len(cal_days),
                     "early_close_days_scheduled": len(early_close_days),
                     "observed_rth_days": len(obs_rth_days),
                     "zero_bar_calendar_days": zero_bar_cal_days,
                     "rth_days_off_calendar": rth_on_noncal},
        "windows": {"w1_complete": w1_complete,
                    "w1_incomplete": w1_incomplete_full,
                    "w1_missing_minutes": w1_missing_minutes,
                    "w2_complete": w2_complete,
                    "w2_excluded_early_close": w2_excl_early,
                    "w2_incomplete_missing_data": w2_incomplete_full,
                    "w2_missing_minutes": w2_missing_minutes,
                    "incomplete_detail": incomplete_detail},
        "adr14": {"complete_rth_days": len(complete_sorted),
                  "candidate_days_both_windows": len(candidate_days),
                  "warmup_days_lacking_14_lookback": len(warmup),
                  "warmup_dates": warmup, "first_full_lookback_day": first_full},
        "dst": {"transition_days_in_coverage": dst_days,
                "transition_days_with_rth_bars": dst_with_rth},
        "rolls": {"n_transitions": len(rolls), "transitions": rolls},
        "condition_json": {"tally": dict(cond_tally),
                           "non_available_dates": cond_bad},
    }, indent=1), encoding="utf-8")
    print(f"A1 addendum JSON written: {OUT_JSON}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
