"""D5 (approved by Aaron 2026-07-29): one-time official Databento
symbology.resolve session for NQ.v.0, 2010-06-06 -> 2022-01-01(excl).

Security (frozen protocol): API key ONLY from env DATABENTO_API_KEY; the key
is never printed, logged, written, or embedded anywhere. Metadata endpoint —
USD 0.00, no data credits consumed.

Outputs (gate1/symbology/):
  raw/resolve_nq_v0_to_instrument_id.json   (verbatim response + fetch meta)
  raw/resolve_nq_v0_to_raw_symbol.json
  nq_v0_mapping.csv        (interval start/end, instrument_id, raw_symbol)
  SYMBOLOGY_VERIFICATION.md (structural verification vs the 47 observed
                             transitions; mapping is verification/disclosure
                             ONLY — it must never alter Primary)
Any mismatch prints STOP_MISMATCH and exits 2 (new decision packet required;
falling back to Option B is NOT permitted without Aaron).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "gate1" / "symbology"
RAW = OUT / "raw"
RAW.mkdir(parents=True, exist_ok=True)

DATASET, SYMBOL = "GLBX.MDP3", "NQ.v.0"
START, END = "2010-06-06", "2022-01-01"
MONTH_CODES = {"H": 3, "M": 6, "U": 9, "Z": 12}


def fetch(stype_out: str) -> list[dict]:
    import databento as db
    key = os.environ.get("DATABENTO_API_KEY")
    if not key:
        print("ABORT: DATABENTO_API_KEY not set"); sys.exit(3)
    client = db.Historical(key)
    fetched_at = dt.datetime.now(dt.timezone.utc).isoformat()
    res = client.symbology.resolve(
        dataset=DATASET, symbols=[SYMBOL], stype_in="continuous",
        stype_out=stype_out, start_date=START, end_date=END)
    payload = {"request": {"dataset": DATASET, "symbols": [SYMBOL],
                           "stype_in": "continuous", "stype_out": stype_out,
                           "start_date": START, "end_date": END},
               "fetched_at_utc": fetched_at,
               "endpoint": "symbology.resolve (metadata, USD 0.00)",
               "response": res}
    raw_path = RAW / f"resolve_nq_v0_to_{stype_out}.json"
    raw_path.write_text(json.dumps(payload, indent=1, default=str),
                        encoding="utf-8")
    sha = hashlib.sha256(raw_path.read_bytes()).hexdigest()
    print(f"archived {raw_path.name} sha256={sha} rows="
          f"{len(res.get('result', {}).get(SYMBOL, []))}")
    intervals = res["result"][SYMBOL]
    # merge adjacent intervals with identical resolved symbol (defensive)
    merged: list[dict] = []
    for iv in sorted(intervals, key=lambda x: x["d0"]):
        if merged and merged[-1]["s"] == iv["s"] and merged[-1]["d1"] == iv["d0"]:
            merged[-1]["d1"] = iv["d1"]
        else:
            merged.append(dict(iv))
    return merged


def main() -> int:
    ids = fetch("instrument_id")
    raws = fetch("raw_symbol")
    if len(ids) != len(raws):
        print(f"STOP_MISMATCH: interval count id={len(ids)} raw={len(raws)}")
        return 2
    rows = []
    for a, b in zip(ids, raws):
        if (a["d0"], a["d1"]) != (b["d0"], b["d1"]):
            print(f"STOP_MISMATCH: interval boundaries differ {a} vs {b}")
            return 2
        rows.append({"start_date_utc": a["d0"], "end_date_utc_excl": a["d1"],
                     "instrument_id": int(a["s"]), "raw_symbol": b["s"]})
    map_df = pd.DataFrame(rows)
    map_csv = OUT / "nq_v0_mapping.csv"
    map_df.to_csv(map_csv, index=False)

    # --- verification 1: the 47 observed transitions, one by one -------------
    qa = json.loads((REPO / "qa_addendum_a1.json").read_text(encoding="utf-8"))
    trans = qa["rolls"]["transitions"]
    checks = []
    ok = True
    for t in trans:
        ts_utc = pd.Timestamp(t["ts_et"]).tz_convert("UTC")
        boundary = ts_utc.date().isoformat()
        exact = ts_utc == ts_utc.normalize()
        old_iv = map_df[map_df.instrument_id == t["old"]]
        new_iv = map_df[map_df.instrument_id == t["new"]]
        c_old = (not old_iv.empty) and (old_iv.iloc[-1].end_date_utc_excl == boundary)
        c_new = (not new_iv.empty) and (new_iv.iloc[0].start_date_utc == boundary)
        good = bool(c_old and c_new and exact)
        ok &= good
        checks.append({"boundary_utc": boundary, "old": t["old"],
                       "new": t["new"], "bar_at_0000utc": exact,
                       "old_interval_ends_here": bool(c_old),
                       "new_interval_starts_here": bool(c_new), "ok": good})

    # --- verification 2: no intra-RTH switching ------------------------------
    # resolve intervals are DATE-granular: every switch instant is 00:00 UTC
    # = 19:00/20:00 ET, outside RTH 09:30-16:00 by construction; plus every
    # observed transition bar sits exactly at 00:00 UTC (checked above).
    date_granular = bool((map_df.start_date_utc.str.len() == 10).all())

    # --- verification 3: quarterly cadence of raw symbols --------------------
    quarterly = True
    seq = []
    for s in map_df.raw_symbol:
        root, mo, yr = s[:2], s[2], s[3:]
        quarterly &= (root == "NQ") and (mo in MONTH_CODES)
        seq.append((mo, yr))
    n_intervals = len(map_df)
    quarterly &= (n_intervals == len(trans) + 1)

    lines = ["# SYMBOLOGY VERIFICATION (D5, Option A — official resolve)",
             "",
             f"- fetched: {START} -> {END} (excl), {SYMBOL}, GLBX.MDP3,",
             "  metadata endpoint, USD 0.00; raw responses + SHA-256 in raw/",
             f"- mapping intervals: {n_intervals} (= 47 transitions + 1) — "
             f"{'OK' if n_intervals == 48 else 'UNEXPECTED'}",
             f"- all intervals date-granular (switches only at 00:00 UTC, "
             f"outside RTH): {date_granular}",
             f"- quarterly contract cadence (NQ + H/M/U/Z): {quarterly}",
             f"- 47/47 transition cross-check vs qa_addendum_a1.json: "
             f"{'ALL MATCH' if ok else 'MISMATCH — STOP'}",
             "", "| boundary UTC | old id | new id | old ends | new starts | ok |",
             "|---|---|---|---|---|---|"]
    for c in checks:
        lines.append(f"| {c['boundary_utc']} | {c['old']} | {c['new']} | "
                     f"{c['old_interval_ends_here']} | "
                     f"{c['new_interval_starts_here']} | {c['ok']} |")
    lines += ["", "Contract sequence: " +
              ", ".join(map_df.raw_symbol.tolist()), "",
              "Scope (frozen by D5 approval): mapping is for VERIFICATION and",
              "DISCLOSURE only; it must never change Primary results. Key was",
              "read from env only and never persisted."]
    (OUT / "SYMBOLOGY_VERIFICATION.md").write_text("\n".join(lines),
                                                   encoding="utf-8")
    print(f"mapping csv: {map_csv.name} ({n_intervals} intervals)")
    print("verification:", "ALL_OK" if (ok and date_granular and quarterly)
          else "STOP_MISMATCH")
    return 0 if (ok and date_granular and quarterly) else 2


if __name__ == "__main__":
    sys.exit(main())
