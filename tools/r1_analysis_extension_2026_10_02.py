"""R1 ANALYSIS_EXTENSION 2026-10-02 -- descriptive only (delegate decision D-R2-2026-10-02-01 R1-c).

    python tools/r1_analysis_extension_2026_10_02.py

Bounded and descriptive. Reads ONLY:
  * the sealed, already-revealed bundle runs/R1-S3B-001/sealed_r1_outcome.json
    (per-record date_et, direction, y_net_usd);
  * the sealed contract (eras, cost scenario, C1 draws, bootstrap seeds, M);
  * the L-11-pinned F10 event calendar, digest-checked by r1.events.load_calendar.
No market data, no NQ archive, no network. No verdict change, no trial consumed,
no re-bootstrap of the Primary, no block-10 interval.

Computes:
  1. the sealed H.2 / I.2 / D.3 / J descriptive splits -- era, micro-era (its own
     axis, D.3) and event type (no CPI / NFP promotion, D.2): n, mean, sd (ddof=1);
  2. the C1 replay (R1-G12): the sealed run_c1 sign draws (random.Random(seed),
     rng.choice((1, -1)) per event per draw), evaluated arithmetically from the
     records, then the sealed bootstrap_interval over the draw means and clears(M).
     The C1 seed and draw count used at S3-B were not recorded; the default is
     seed = bootstrap_seeds[0] = 7 and draws = c1_draws. Seeds 13 and 31 are shown
     for disclosure. The trade has no stop and symmetric frictions (r1/costs.py), so
     y(s) = s * G - C with G = d * (y + C) and C the base round-turn cost; the replay
     first checks that this reproduces every sealed y_net_usd.
"""
from __future__ import annotations

import datetime as _dt
import json
import random
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from r1.bootstrap import bootstrap_interval  # noqa: E402
from r1.contract import load_sealed_contract  # noqa: E402
from r1.costs import round_turn_cost_usd  # noqa: E402
from r1.events import load_calendar  # noqa: E402

BUNDLE = ROOT / "runs" / "R1-S3B-001" / "sealed_r1_outcome.json"
MICRO_START = _dt.date(2019, 5, 6)  # sealed D.3: MNQ began trading 2019-05-06


def describe(values: list[float]) -> dict:
    return {"n": len(values),
            "mean": round(statistics.fmean(values), 4),
            "sd": round(statistics.stdev(values), 4) if len(values) > 1 else None}


def main() -> int:
    contract = load_sealed_contract(ROOT)
    records = json.loads(BUNDLE.read_text(encoding="utf-8"))["payload"]["records"]
    y = {r["date_et"]: r["y_net_usd"] for r in records}
    d = {r["date_et"]: r["direction"] for r in records}
    dates = [r["date_et"] for r in records]

    # event type from the pinned calendar (L-11 digest enforced by load_calendar)
    types: dict[str, set[str]] = {}
    for row in load_calendar(contract):
        if row["event_type"] in contract.event_family:
            types.setdefault(row["date_et"], set()).add(row["event_type"])
    unmapped = [t for t in dates if len(types.get(t, ())) != 1]
    if unmapped:
        raise SystemExit(f"dates without a unique CPI/NFP calendar type: {unmapped}")

    splits: dict[str, dict] = {"pooled": describe([y[t] for t in dates])}
    for name, lo, hi in contract.eras:
        splits[f"era {name}"] = describe(
            [y[t] for t in dates if lo <= int(t[:4]) <= hi])
    splits["micro-era counterfactual (< 2019-05-06)"] = describe(
        [y[t] for t in dates if _dt.date.fromisoformat(t) < MICRO_START])
    splits["micro-era actual (>= 2019-05-06)"] = describe(
        [y[t] for t in dates if _dt.date.fromisoformat(t) >= MICRO_START])
    for ev in sorted(contract.event_family):
        splits[f"event type {ev}"] = describe(
            [y[t] for t in dates if types[t] == {ev}])

    # C1 replay
    cost = round_turn_cost_usd(contract, contract.primary_cost_scenario)
    gross = {t: d[t] * (y[t] + cost) for t in dates}
    max_err = max(abs((d[t] * gross[t] - cost) - y[t]) for t in dates)
    if max_err > 1e-9:
        raise SystemExit(f"y(s) = s*G - C does not reproduce the records (max err {max_err})")
    c1 = {}
    for seed in (contract.bootstrap_seeds[0], 13, 31):
        rng = random.Random(seed)
        means = []
        for _ in range(contract.c1_draws):
            draw = [rng.choice((1, -1)) * gross[t] - cost for t in dates]
            means.append(sum(draw) / len(draw))
        ci = bootstrap_interval(means, contract)
        c1[str(seed)] = {
            "mean_of_draw_means": round(statistics.fmean(means), 4),
            "interval": [round(ci.lower, 4), round(ci.upper, 4)],
            "half_width": round(ci.half_width, 4),
            "clears_M": ci.clears(contract.materiality_m_usd),
        }

    up = sum(1 for t in dates if gross[t] > 0)
    flat = sum(1 for t in dates if gross[t] == 0)
    out = {
        "n_records": len(dates),
        "base_round_turn_cost_usd": cost,
        "M_usd": contract.materiality_m_usd,
        "replay_max_abs_error_usd": max_err,
        "splits": splits,
        "c1_draws": contract.c1_draws,
        "c1_by_seed": c1,
        "signal_directions": {"long": sum(1 for t in dates if d[t] == 1),
                              "short": sum(1 for t in dates if d[t] == -1)},
        # G = long-side gross USD move per event (direction removed)
        "undirected_moves": {"up": up, "zero": flat, "down": len(dates) - up - flat,
                             "mean_usd": round(statistics.fmean(
                                 gross[t] for t in dates), 4)},
    }
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
