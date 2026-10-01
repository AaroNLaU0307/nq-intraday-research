"""Measure what one MC pass costs, so N16's total stops being unknown.

WHY THIS EXISTS. The N16 compute total (master plan SS14.4) has the shape
`18 x (unmeasured per-pass cost) + custody 15-42h + 9 grid units`. The
first term has no observation anywhere in this repository: every logical
test runs at B=2 / M=2, and the R2.3 "production scale" fixture was a
forged summary built by a since-deleted API. So nobody can say how long
N16 takes, and the doubling and seed quantifiers (M10) cannot be judged
against a budget that does not exist.

WHAT THIS IS. A synthetic scaling probe. It runs the REAL epistemic
pipeline on generated data at several small sizes, fits the scaling, and
extrapolates. Nothing else.

WHAT THIS IS NOT.
  * NOT the E3 production-scale smoke run. That is a separate, ruled
    artefact with seven mechanical PASS criteria, it runs at B=1000/2000,
    and it needs Aaron's own execution authorization. This probe stays
    deliberately far below production size and asserts no PASS criteria.
  * NOT an MC execution. No real Development bytes, no sealed values, no
    governed directory, no registry or exposure event, no output root.
    Everything it touches is generated in-process from a fixed seed.
  * NOT a substitute for E3. An extrapolation is a model. Effects that
    only appear at production scale -- float accumulation order,
    type-7 percentile boundaries, memory cliffs -- are exactly what a
    fitted line cannot see. That is the argument FOR E3, and this probe
    strengthens it rather than replacing it.

READ THE OUTPUT AS A LOWER BOUND. It measures one (combo x scenario)
cell of the primary channel. A full pass covers many cells, and the
grid channel and the alpha branch are additional.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
import tracemalloc
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tests"))

from itsf.mc import consumer as mcc                       # noqa: E402
from itsf.mc.orchestrator import TemplateDay              # noqa: E402

import test_mc_consumer as fx                             # noqa: E402


def _calendar(n_days: int, n_offsets: int):
    days = tuple(TemplateDay(day_id=f"T{i:03d}", cal_offset=i)
                 for i in range(n_days))
    return mcc.TemplateCalendar(days=days,
                                first_month_offsets=tuple(range(n_offsets)))


def _prepared(n_days: int, n_offsets: int):
    bundle = fx._bundle()
    return mcc.prepare_mc_input_for_tests(
        bundle, authorization_snapshot=fx._snapshot(),
        custody_authority=mcc.CustodyAuthority.for_tests(bundle),
        test_only_calendar=_calendar(n_days, n_offsets))


def _one(prepared, B: int, repeats: int) -> tuple[float, float]:
    """(median seconds, peak MiB) for one epistemic pass."""
    times = []
    tracemalloc.start()
    for _ in range(repeats):
        t0 = time.perf_counter()
        mcc.run_epistemic(prepared, platform="topstep", engine="E1",
                          scenario="Conservative", channel=fx.PRIMARY,
                          B=B, master_seed=7)
        times.append(time.perf_counter() - t0)
    peak = tracemalloc.get_traced_memory()[1] / (1024 * 1024)
    tracemalloc.stop()
    return statistics.median(times), peak


def _fit(xs, ys):
    """Least-squares slope/intercept; xs is the work measure."""
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    denom = sum((x - mx) ** 2 for x in xs)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / denom
    return slope, my - slope * mx


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--b-values", default="2,5,10,20,40")
    ap.add_argument("--days", type=int, default=8)
    ap.add_argument("--offsets", type=int, default=4, help="M axis")
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    b_values = [int(v) for v in args.b_values.split(",")]
    prepared = _prepared(args.days, args.offsets)
    M = args.offsets

    print(f"synthetic only | days={args.days} M={M} "
          f"repeats={args.repeats}\n")
    print(f"{'B':>6} {'paths':>9} {'sec':>10} {'sec/path':>12} {'peakMiB':>10}")
    rows = []
    for B in b_values:
        secs, peak = _one(prepared, B, args.repeats)
        paths = B * M
        rows.append({"B": B, "M": M, "paths": paths, "seconds": secs,
                     "peak_mib": peak})
        print(f"{B:>6} {paths:>9} {secs:>10.4f} "
              f"{secs / paths:>12.6f} {peak:>10.2f}")

    slope, intercept = _fit([r["paths"] for r in rows],
                            [r["seconds"] for r in rows])
    mslope, mint = _fit([r["paths"] for r in rows],
                        [r["peak_mib"] for r in rows])
    print(f"\nfit: seconds = {slope:.6f} * paths + {intercept:.4f}")
    print(f"     peakMiB = {mslope:.6f} * paths + {mint:.2f}")

    # linearity check -- an r^2 far from 1 means the extrapolation below
    # is not trustworthy and should be reported as such, not quietly used
    ys = [r["seconds"] for r in rows]
    my = sum(ys) / len(ys)
    ss_res = sum((r["seconds"] - (slope * r["paths"] + intercept)) ** 2
                 for r in rows)
    ss_tot = sum((y - my) ** 2 for y in ys)
    r2 = 1 - ss_res / ss_tot if ss_tot else float("nan")
    print(f"     r^2 = {r2:.5f}"
          + ("" if r2 > 0.98 else "   <-- NOT LINEAR, do not extrapolate"))

    print(f"\nextrapolation to production, ONE cell, days={args.days}")
    print("(the real day universe is larger; scale by days accordingly)")
    for B, M_prod, label in ((1000, 21, "base B=1000"),
                             (2000, 21, "doubled B=2000")):
        paths = B * M_prod
        sec = slope * paths + intercept
        print(f"  {label:<16} paths={paths:>7}  "
              f"{sec:>9.1f} s = {sec / 60:>6.1f} min")

    # --- day scaling -----------------------------------------------------
    # The fixture calendar is 8 days; production is 24 months of trading
    # days. Cost is linear in calendar length too, so fit that separately
    # and compose, rather than pretending the 8-day number transfers.
    print("\n--- calendar-length sweep (per-path seconds vs days) ---")
    per_path = []
    for d in (25, 60, 125, 250):
        prep_d = _prepared(d, M)
        s, _ = _one(prep_d, 20, args.repeats)
        per_path.append((d, s / (20 * M)))
        print(f"  days={d:>4}  sec/path={per_path[-1][1]:.6f}")
    dslope, dint = _fit([d for d, _ in per_path], [v for _, v in per_path])
    print(f"  fit: sec/path = {dslope:.3e} * days + {dint:.3e}")

    PROD_DAYS = 24 * 21          # 24 months x ~21 trading days
    CELLS_PRIMARY = 16           # 2 lifecycles x P2 x {E1,E2} x 4 scenarios
    sec_path_prod = dslope * PROD_DAYS + dint
    be_cell_min = (1000 * 21) * sec_path_prod / 60
    be_primary_h = be_cell_min * CELLS_PRIMARY / 60

    print(f"\n=== composed estimate (LOWER BOUND) ===")
    print(f"production calendar        {PROD_DAYS} trading days")
    print(f"sec/path at that length    {sec_path_prod:.5f}")
    print(f"one cell, B=1000 M=21      {be_cell_min:.1f} min")
    print(f"one BE, {CELLS_PRIMARY} primary cells  {be_primary_h:.1f} h")
    print(f"18 BE (SS14.4 multiplier)     {18 * be_primary_h:.0f} h "
          f"= {18 * be_primary_h / 24:.1f} days")
    print(f"  + theta_0.3 channel (O1 rules it isomorphic)  x2 "
          f"-> {2 * 18 * be_primary_h / 24:.1f} days")
    print("  + secondary sensitivity combos (SS2.5; count not enumerable")
    print("    from the frozen text) -- a further multiple, NOT included")
    print("  + grid channel, custody 15-42 h, I/O -- NOT included")
    print("\nWHY THIS IS A LOWER BOUND: the fixture oracle universe is 5")
    print("days against a 500-day calendar, so almost every simulated day")
    print("carries no signal and costs less than a production day will.")
    print("Single machine, single process, no contention.")

    if args.out:
        Path(args.out).write_text(json.dumps(
            {"synthetic_only": True, "days": args.days, "M": M,
             "rows": rows, "seconds_per_path": slope,
             "seconds_intercept": intercept, "r2": r2,
             "day_scaling": {"slope": dslope, "intercept": dint,
                             "samples": per_path},
             "prod_days": PROD_DAYS, "cells_primary": CELLS_PRIMARY,
             "one_cell_minutes": be_cell_min,
             "one_be_hours_primary": be_primary_h,
             "eighteen_be_days": 18 * be_primary_h / 24}, indent=2),
        encoding="utf-8")
        print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
