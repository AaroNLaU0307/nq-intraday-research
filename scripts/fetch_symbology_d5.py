"""D5 (approved by Aaron 2026-07-29) — one-time official Databento
symbology.resolve session for NQ.v.0, 2010-06-06 -> 2022-01-01(excl).

Two-hop chain per the approval ("NQ.v.0 到 instrument_id 及 raw_symbol"):
  hop 1: continuous NQ.v.0            -> instrument_id  (48 date intervals)
  hop 2: the 48 instrument_ids        -> raw_symbol     (contract codes)
API fact recorded 2026-07-29: continuous -> raw_symbol directly is NOT a
supported stype combination on GLBX.MDP3 (HTTP 422, official docs); the
two-hop form uses only supported combinations. Same metadata endpoint,
USD 0.00, no data credits.

Security (frozen protocol): API key ONLY from env DATABENTO_API_KEY; never
printed, logged, written, or embedded anywhere.

Outputs (gate1/symbology/):
  raw/resolve_nq_v0_to_instrument_id.json
  raw/resolve_instrument_ids_to_raw_symbol.json
  nq_v0_mapping.csv        (interval start/end, instrument_id, raw_symbol)
  SYMBOLOGY_VERIFICATION.md
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


def _client():
    import databento as db
    key = os.environ.get("DATABENTO_API_KEY")
    if not key:
        print("ABORT: DATABENTO_API_KEY not set"); sys.exit(3)
    return db.Historical(key)


def _resolve_with_retry(client, **req):
    """Retry transient 5xx gateway errors (server-side flakiness observed
    2026-07-29); client errors (4xx) surface immediately — they are facts."""
    import time
    from databento.common.error import BentoServerError
    for attempt, pause in enumerate((0, 5, 15, 30)):
        if pause:
            time.sleep(pause)
        try:
            return client.symbology.resolve(**req)
        except BentoServerError as exc:
            last = exc
            print(f"transient server error attempt {attempt + 1}/4: "
                  f"{type(exc).__name__}", flush=True)
    raise last


def _archive(name: str, request: dict, response: dict) -> None:
    payload = {"request": request,
               "fetched_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
               "endpoint": "symbology.resolve (metadata, USD 0.00)",
               "response": response}
    p = RAW / name
    p.write_text(json.dumps(payload, indent=1, default=str), encoding="utf-8")
    sha = hashlib.sha256(p.read_bytes()).hexdigest()
    print(f"archived {p.name} sha256={sha}")


def fetch_continuous_to_ids(client) -> list[dict]:
    req = {"dataset": DATASET, "symbols": [SYMBOL], "stype_in": "continuous",
           "stype_out": "instrument_id", "start_date": START, "end_date": END}
    res = _resolve_with_retry(client, **req)
    _archive("resolve_nq_v0_to_instrument_id.json", req, res)
    intervals = sorted(res["result"][SYMBOL], key=lambda x: x["d0"])
    merged: list[dict] = []
    for iv in intervals:                      # merge adjacent same-id (defensive)
        if merged and merged[-1]["s"] == iv["s"] and merged[-1]["d1"] == iv["d0"]:
            merged[-1]["d1"] = iv["d1"]
        else:
            merged.append(dict(iv))
    return merged


def fetch_ids_to_raw(client, ids: list[str]) -> dict[str, list[dict]]:
    """id -> list of {d0, d1, s} intervals. CME instrument_ids are REUSED
    across years for unrelated products (fact observed 2026-07-29: id 10016
    carried 22 different raw symbols across the window), so the join to the
    continuous intervals MUST be time-aware — never a bare set collapse."""
    req = {"dataset": DATASET, "symbols": ids, "stype_in": "instrument_id",
           "stype_out": "raw_symbol", "start_date": START, "end_date": END}
    res = _resolve_with_retry(client, **req)
    _archive("resolve_instrument_ids_to_raw_symbol.json", req, res)
    return {str(iid): sorted(ivs, key=lambda x: x["d0"])
            for iid, ivs in res["result"].items()}


def raw_symbol_for_interval(raw_ivs: dict[str, list[dict]],
                            iid: str, d0: str, d1: str) -> str | None:
    """The unique raw_symbol whose id->raw interval fully covers [d0, d1)."""
    hits = [iv["s"] for iv in raw_ivs.get(iid, [])
            if iv["d0"] <= d0 and iv["d1"] >= d1]
    return hits[0] if len(hits) == 1 else None


def main() -> int:
    client = _client()
    ids = fetch_continuous_to_ids(client)
    print(f"continuous->instrument_id intervals: {len(ids)}")
    unique_ids = [str(iv["s"]) for iv in ids]
    if len(set(unique_ids)) != len(unique_ids):
        print("STOP_MISMATCH: an instrument_id repeats in non-adjacent "
              "continuous intervals"); return 2
    raw_ivs = fetch_ids_to_raw(client, sorted(set(unique_ids)))

    import re
    rows = []
    for iv in ids:
        raw = raw_symbol_for_interval(raw_ivs, str(iv["s"]), iv["d0"], iv["d1"])
        if raw is None:
            print(f"STOP_MISMATCH: no unique raw_symbol covers continuous "
                  f"interval {iv['d0']}..{iv['d1']} for id {iv['s']}")
            return 2
        if not re.fullmatch(r"NQ[HMUZ]\d{1,2}", raw):
            print(f"STOP_MISMATCH: resolved symbol {raw!r} for id {iv['s']} "
                  "is not an NQ quarterly outright")
            return 2
        rows.append({"start_date_utc": iv["d0"], "end_date_utc_excl": iv["d1"],
                     "instrument_id": int(iv["s"]), "raw_symbol": raw})
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

    # --- verification 2: intra-RTH switch count must be 0 --------------------
    # resolve intervals are DATE-granular: every switch instant is 00:00 UTC
    # = 19:00/20:00 ET, outside RTH 09:30-16:00; plus every observed
    # transition bar sits exactly at 00:00 UTC (checked above).
    date_granular = bool((map_df.start_date_utc.str.len() == 10).all())
    intra_rth_switches = 0 if date_granular and ok else -1

    # --- verification 3: quarterly cadence of raw symbols --------------------
    quarterly = True
    prev = None
    for s in map_df.raw_symbol:
        root, mo, yr = s[:2], s[2], s[3:]
        quarterly &= (root == "NQ") and (mo in MONTH_CODES)
        code = (2000 + int(yr) if len(yr) == 1 else int(yr),)  # informational
        prev = (mo, yr, code)
    n_intervals = len(map_df)
    quarterly &= (n_intervals == len(trans) + 1)

    lines = ["# SYMBOLOGY VERIFICATION (D5, Option A — official resolve)",
             "",
             f"- window: {START} -> {END} (excl), {SYMBOL}, GLBX.MDP3;",
             "  metadata endpoint, USD 0.00; raw responses + SHA-256 in raw/",
             "- API fact: continuous->raw_symbol unsupported on GLBX.MDP3",
             "  (HTTP 422); approved chain executed as two supported hops:",
             "  continuous->instrument_id, then instrument_id->raw_symbol.",
             f"- mapping intervals: {n_intervals} (= 47 transitions + 1) — "
             f"{'OK' if n_intervals == 48 else 'UNEXPECTED'}",
             f"- all intervals date-granular: {date_granular}",
             f"- intra-RTH-session switch count: {intra_rth_switches} "
             f"(required: 0)",
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
              "DISCLOSURE of F11/F5 roll identification only; it must never",
              "change Primary results. Key was read from env only and never",
              "persisted."]
    (OUT / "SYMBOLOGY_VERIFICATION.md").write_text("\n".join(lines),
                                                   encoding="utf-8")
    print(f"mapping csv: {map_csv.name} ({n_intervals} intervals)")
    verdict = ok and date_granular and quarterly and intra_rth_switches == 0
    print("verification:", "ALL_OK" if verdict else "STOP_MISMATCH")
    return 0 if verdict else 2


if __name__ == "__main__":
    sys.exit(main())
