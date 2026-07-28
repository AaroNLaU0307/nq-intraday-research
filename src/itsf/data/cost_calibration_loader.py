"""Execution-cost calibration loader (main-agent authored, milestone 3).

The ONLY module allowed to touch raw A2 MNQ BBO data, and its ONLY public
output is the derived spread table. Raw BBO frames are never returned to any
caller — Alpha code cannot obtain them through this interface.
# frozen: charter 条款 14 数据角色隔离; S0 SS1 Execution Cost Calibration role;
# purchase_plan A2 isolation clause
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from itsf.data import manifests, validation
from itsf.guards import assert_real_run_allowed, G9_FLAG, SECOND_COPY_FLAG

ET = ZoneInfo("America/New_York")
ROLE_DIRNAME = "execution_cost_calibration"
EXPECTED_SYMBOL_ROOT = "MNQ"          # frozen: purchase_plan A2 MNQ.v.0

SPREAD_TABLE_COLUMNS = ("minute_of_day_et", "spread_median_points",
                        "spread_p90_points", "spread_p95_points", "n_obs")


class RoleError(RuntimeError):
    pass


@dataclass
class CostCalibrationLoader:
    job_dir: Path
    g9_flag: Path = G9_FLAG
    second_copy_flag: Path = SECOND_COPY_FLAG

    def __post_init__(self) -> None:
        self.job_dir = Path(self.job_dir)

    # -- the ONLY public product ----------------------------------------------

    def build_spread_table_real(self, filename: str, source_format: str = "dbn",
                                ) -> tuple[pd.DataFrame, list[validation.QAEvent]]:
        """Real entry: guard FIRST, then role/manifest checks, then decode.
        Returns ONLY the derived per-minute spread percentile table
        (S0 SS6 spread_cost_table) plus QA events — never raw BBO rows."""
        assert_real_run_allowed(self.g9_flag, self.second_copy_flag)
        self._check_role()
        path = self.job_dir / filename
        manifest = manifests.load_manifest(self.job_dir)
        manifests.verify_file_against_manifest(path, manifest)
        raw = self._decode(path, source_format)
        return self._spread_table(raw)

    @staticmethod
    def build_spread_table_synthetic(bbo: pd.DataFrame,
                                     ) -> tuple[pd.DataFrame, list[validation.QAEvent]]:
        """Synthetic entry (no guard, no files): same derivation pipeline."""
        return CostCalibrationLoader._spread_table(bbo)

    # -- internals (raw BBO never escapes) ------------------------------------

    def _check_role(self) -> None:
        if ROLE_DIRNAME not in str(self.job_dir):
            raise RoleError(
                f"cost-calibration loader pointed at non-cost path: "
                f"{self.job_dir} (frozen data-role isolation)")

    @staticmethod
    def _decode(path: Path, source_format: str) -> pd.DataFrame:
        if source_format == "synthetic_csv":
            df = pd.read_csv(path)
            df["ts"] = pd.to_datetime(df["ts"], utc=True)
            return df
        if source_format == "dbn":
            import databento as db
            store = db.DBNStore.from_file(path)
            df = store.to_df().reset_index().rename(columns={"ts_event": "ts"})
            # Databento bbo/mbp-1 to_df names top-of-book levels *_00
            df = df.rename(columns={"bid_px_00": "bid_px", "ask_px_00": "ask_px"})
            return df
        raise ValueError(f"unknown source_format {source_format!r}")

    @staticmethod
    def _spread_table(bbo: pd.DataFrame) -> pd.DataFrame:
        for col in ("ts", "bid_px", "ask_px"):
            if col not in bbo.columns:
                raise validation.ValidationError(
                    f"BBO schema gap: missing {col} (fail closed)")
        df = bbo.copy()
        ts = pd.to_datetime(df["ts"], utc=True).dt.tz_convert(ET)
        pre = ts.dt.date < validation.MNQ_LAUNCH_DATE
        if pre.any():
            raise validation.ValidationError(
                f"{int(pre.sum())} BBO rows before MNQ launch — fail closed")
        spread = df["ask_px"] - df["bid_px"]
        invalid = ~spread.ge(0)       # NaN or negative (crossed book)
        events: list[validation.QAEvent] = []
        n_bad = int(invalid.sum())
        if n_bad:
            frac = n_bad / len(df)
            # Transient crossed/one-sided snapshots are known 1-second BBO
            # microstructure (real A2 Jan-2025: 0.0198%). They cannot
            # contribute a spread and are EXCLUDED WITH A QA EVENT — never
            # silently. An abnormal fraction still fails closed.
            if frac > 0.01:
                raise validation.ValidationError(
                    f"{n_bad} invalid-spread rows = {frac:.2%} > 1% "
                    "abnormality threshold — fail closed, no repair")
            events.append(validation.QAEvent(
                "crossed_or_invalid_spread",
                f"{n_bad} of {len(df)} rows ({frac:.4%}) excluded from the "
                "spread table", n_bad))
        valid = ~invalid
        minute = (ts.dt.hour * 60 + ts.dt.minute)[valid]
        g = pd.DataFrame({"minute_of_day_et": minute, "spread": spread[valid]})
        tbl = (g.groupby("minute_of_day_et")["spread"]
                .agg(spread_median_points="median",
                     spread_p90_points=lambda s: s.quantile(0.90),
                     spread_p95_points=lambda s: s.quantile(0.95),
                     n_obs="count")
                .reset_index())
        return tbl[list(SPREAD_TABLE_COLUMNS)], events
