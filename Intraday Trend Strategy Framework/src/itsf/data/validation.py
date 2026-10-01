"""Bar-data QA (main-agent authored).

Every cleaning decision emits a QAEvent; NOTHING is silently dropped
(# frozen: charter — 所有清洗决定形成 QA 事件).
Logs/QA events must never contain research numbers (P&L, EV, feature values);
they carry counts, timestamps and structural facts only.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd

# frozen: platform_params / prereg — MNQ began trading 2019-05-06 (CME);
# any MNQ-role data before this date is structurally impossible.
MNQ_LAUNCH_DATE = date(2019, 5, 6)

REQUIRED_COLUMNS = ("ts", "open", "high", "low", "close", "volume")


@dataclass(frozen=True)
class QAEvent:
    kind: str          # duplicate_minute | missing_minute | bad_price |
                       # zero_volume | pre_launch_row | schema_gap
    detail: str        # structural description only — NO research numbers
    count: int = 1


class ValidationError(RuntimeError):
    pass


def check_schema(df: pd.DataFrame) -> None:
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValidationError(f"schema gap, missing columns: {missing}")


def qa_bars(df: pd.DataFrame, instrument_role: str = "development",
            expected_minutes: int | None = None) -> tuple[pd.DataFrame, list[QAEvent]]:
    """Structural QA. Returns (df with flag columns, events). Never mutates
    prices and never drops rows silently — downstream exclusion rules
    (frozen S0 SS3) decide what to do with flagged material."""
    check_schema(df)
    events: list[QAEvent] = []
    out = df.copy()

    dup_mask = out["ts"].duplicated(keep=False)
    if dup_mask.any():
        events.append(QAEvent("duplicate_minute",
                              f"{int(dup_mask.sum())} rows share a timestamp",
                              int(dup_mask.sum())))
    out["qa_duplicate"] = dup_mask

    bad = ~np.isfinite(out[["open", "high", "low", "close"]]).all(axis=1)
    bad |= (out[["open", "high", "low", "close"]] <= 0).any(axis=1)
    if bad.any():
        events.append(QAEvent("bad_price",
                              f"{int(bad.sum())} rows with NaN/inf/non-positive price",
                              int(bad.sum())))
    out["qa_bad_price"] = bad

    zv = out["volume"] <= 0
    if zv.any():
        events.append(QAEvent("zero_volume", f"{int(zv.sum())} zero-volume rows",
                              int(zv.sum())))
    out["qa_zero_volume"] = zv

    if instrument_role == "execution_cost_calibration":
        pre = out["ts"].dt.date < MNQ_LAUNCH_DATE
        if pre.any():
            raise ValidationError(
                f"{int(pre.sum())} rows before MNQ launch {MNQ_LAUNCH_DATE} "
                "in execution-cost data — structurally impossible, fail closed")

    if expected_minutes is not None:
        got = len(out)
        if got < expected_minutes:
            events.append(QAEvent("missing_minute",
                                  f"{expected_minutes - got} of {expected_minutes} "
                                  "expected minutes absent",
                                  expected_minutes - got))
    return out, events
