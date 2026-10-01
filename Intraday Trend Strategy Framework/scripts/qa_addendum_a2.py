"""QA Addendum — A2 structural sweep (Aaron 2026-07-29 spec, QA-only).

Per-month raw row counts / ts extremes / crossed-locked-NaN taxonomy plus
seeded crossed-row forensics (bid/ask swap, price-scaling, schema-mapping
checks) via CostCalibrationLoader._qa_crossed_forensics — bounded structural
summaries only, raw BBO never leaves the loader module boundary.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from itsf.guards import assert_real_run_allowed                      # noqa: E402
from itsf.data.cost_calibration_loader import CostCalibrationLoader  # noqa: E402

A2_DIR = Path(r"C:\Users\Aaron\quant-data\databento-archive\intraday-trend"
              r"\execution_cost_calibration\GLBX-20260727-TV3MXWNMXD")
OUT_JSON = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "qa_addendum_a2.json"
SEED = 20260729


def main() -> int:
    assert_real_run_allowed()

    cl = CostCalibrationLoader(A2_DIR)
    files = sorted(p.name for p in A2_DIR.glob("*.dbn.zst"))
    months = []
    for name in files:
        f = cl._qa_crossed_forensics(name, seed=SEED, k=5)
        f["crossed_fraction"] = f["n_crossed_ask_lt_bid"] / f["n_rows"]
        months.append(f)
        print(f"done {name}: {f['n_rows']} rows, "
              f"{f['n_crossed_ask_lt_bid']} crossed", flush=True)

    cond = json.loads((A2_DIR / "condition.json").read_text(encoding="utf-8"))
    cond_tally = Counter(r["condition"] for r in cond)

    OUT_JSON.write_text(json.dumps({
        "seed": SEED, "months": months,
        "max_single_file_crossed_fraction": max(m["crossed_fraction"]
                                                for m in months),
        "total_rows": sum(m["n_rows"] for m in months),
        "total_crossed": sum(m["n_crossed_ask_lt_bid"] for m in months),
        "total_nan_spread": sum(m["n_nan_spread"] for m in months),
        "total_locked": sum(m["n_locked_ask_eq_bid"] for m in months),
        "condition_json": {"tally": dict(cond_tally),
                           "non_available_dates": [r["date"] for r in cond
                                                   if r["condition"] != "available"]},
    }, indent=1), encoding="utf-8")
    print(f"A2 addendum JSON written: {OUT_JSON}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
