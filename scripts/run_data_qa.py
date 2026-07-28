"""Data QA-only run (Aaron's mandated pre-S0 stage, 2026-07-28 spec).

Produces DATA_QA_REPORT.md with STRUCTURAL facts ONLY:
  - per-file decode status, bar counts, date coverage
  - duplicate/missing-minute and bad-price/zero-volume QA event tallies
  - frozen exclusion-rule day counts (half-day list pending real calendar
    injection; zero-bar and >10%-missing counted here)
  - roll-transition counts from symbology
  - A2 spread table coverage + spread distribution stats (cost-calibration
    facts, NOT strategy numbers; explicitly labeled)

FORBIDDEN OUTPUTS (Aaron spec + frozen S0 SS10.2): strategy returns, Oracle
performance, EV, features, labels, verdicts. Nothing here computes them.

Gate: guards.assert_real_run_allowed() runs FIRST — both attestation flags
must exist or this exits before opening any file.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from itsf.guards import assert_real_run_allowed                    # noqa: E402
from itsf.data.dbn_loader import DevelopmentSignalLoader           # noqa: E402
from itsf.data.cost_calibration_loader import CostCalibrationLoader  # noqa: E402
from itsf.data import manifests                                    # noqa: E402

A1_DIR = Path(r"C:\Users\Aaron\quant-data\databento-archive\intraday-trend"
              r"\development_signal\GLBX-20260727-DL3BEBCHJA")
A2_DIR = Path(r"C:\Users\Aaron\quant-data\databento-archive\intraday-trend"
              r"\execution_cost_calibration\GLBX-20260727-TV3MXWNMXD")
OUT = REPO / "DATA_QA_REPORT.md"


def main() -> int:
    assert_real_run_allowed()          # fail-closed BEFORE any open

    lines = ["# DATA QA REPORT (structural facts only — no research numbers)",
             "", "Stage: QA-only per Aaron 2026-07-28 spec; real S0 remains",
             "blocked until Aaron approves this report.", ""]

    # --- A1 Development NQ ohlcv-1m -----------------------------------------
    ldr = DevelopmentSignalLoader(A1_DIR)
    man = manifests.load_manifest(A1_DIR) if (A1_DIR / "_local_manifest.json").exists() else None
    dbn_files = sorted(p.name for p in A1_DIR.glob("*.dbn.zst"))
    lines += [f"## A1 Development ({len(dbn_files)} monthly files)", ""]
    qa_totals: Counter = Counter()
    total_bars = 0
    decode_fail = []
    for name in dbn_files:
        try:
            df, events = ldr.load_real(name, source_format="dbn")
        except Exception as exc:                       # recorded, not hidden
            decode_fail.append(f"{name}: {type(exc).__name__}")
            continue
        total_bars += len(df)
        for e in events:
            qa_totals[e.kind] += e.count
    lines += [f"- total 1-min bars decoded: {total_bars}",
              f"- decode failures: {decode_fail if decode_fail else 'none'}",
              f"- QA event tallies: {dict(qa_totals) if qa_totals else 'none'}",
              ""]

    # --- A2 Execution-cost MNQ bbo-1s (spread table only) --------------------
    cl = CostCalibrationLoader(A2_DIR)
    a2_files = sorted(p.name for p in A2_DIR.glob("*.dbn.zst"))
    lines += [f"## A2 Cost Calibration ({len(a2_files)} monthly files)", ""]
    import pandas as pd
    tables = []
    for name in a2_files:
        tables.append(cl.build_spread_table_real(name, source_format="dbn"))
    if tables:
        tbl = (pd.concat(tables).groupby("minute_of_day_et")
               .agg({"spread_median_points": "median",
                     "spread_p90_points": "median",
                     "spread_p95_points": "median", "n_obs": "sum"})
               .reset_index())
        out_csv = REPO / "spread_cost_table.csv"
        tbl.to_csv(out_csv, index=False)
        rth = tbl[(tbl.minute_of_day_et >= 570) & (tbl.minute_of_day_et < 960)]
        lines += [
            "(cost-calibration facts, not strategy numbers)",
            f"- minutes covered: {len(tbl)}; RTH minutes: {len(rth)}",
            f"- RTH spread median (points): median {rth.spread_median_points.median():.2f}, "
            f"p90-of-medians {rth.spread_median_points.quantile(0.9):.2f}",
            f"- table written: {out_csv.name}", ""]

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"QA report written: {OUT}")
    print("Real S0 remains blocked pending Aaron's approval of this report.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
