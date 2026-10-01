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
from itsf.data.roles import DataRole
from itsf.guards import assert_real_run_allowed, G9_FLAG, SECOND_COPY_FLAG

ET = ZoneInfo("America/New_York")
# frozen: purchase_plan A2 data_role / STUDY_0_PREREGISTRATION.md 行 26 —
# sourced from the shared DataRole enum (itsf.data.roles), not a bare literal.
ROLE_DIRNAME = DataRole.EXECUTION_COST_CALIBRATION.value
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

    # -- QA-stage diagnostic (private; NOT part of the Alpha-facing API) ------

    def _qa_crossed_forensics(self, filename: str, *, seed: int = 20260729,
                              k: int = 5) -> dict:
        """Structural forensics for the QA addendum ONLY. Guard-first like the
        real entry. Returns a bounded summary (counts, ts extremes, up to `k`
        sampled crossed rows with +/-2 neighbor context) — never a frame."""
        assert_real_run_allowed(self.g9_flag, self.second_copy_flag)
        self._check_role()
        path = self.job_dir / filename
        manifest = manifests.load_manifest(self.job_dir)
        manifests.verify_file_against_manifest(path, manifest)
        return self._forensics_from_frame(self._decode(path, "dbn"),
                                          filename, seed=seed, k=k)

    @staticmethod
    def _forensics_from_frame(df: pd.DataFrame, filename: str, *,
                              seed: int, k: int) -> dict:
        import numpy as np
        ts = pd.to_datetime(df["ts"], utc=True)
        spread = df["ask_px"] - df["bid_px"]
        crossed = spread < 0
        idx = list(df.index[crossed])
        rng = np.random.default_rng(seed)
        take = (sorted(rng.choice(idx, size=min(k, len(idx)),
                                  replace=False).tolist()) if idx else [])
        samples = []
        for i in take:
            lo, hi = max(0, i - 2), min(len(df) - 1, i + 2)
            window = [{"rel": j - i, "ts_utc": ts.iloc[j].isoformat(),
                       "bid_px": float(df["bid_px"].iloc[j]),
                       "ask_px": float(df["ask_px"].iloc[j]),
                       "spread": (float(spread.iloc[j])
                                  if pd.notna(spread.iloc[j]) else None)}
                      for j in range(lo, hi + 1)]
            neigh = [j for j in range(lo, hi + 1)
                     if j != i and pd.notna(spread.iloc[j]) and spread.iloc[j] >= 0]
            neigh_mid = (sum(float(df["bid_px"].iloc[j] + df["ask_px"].iloc[j])
                             for j in neigh) / (2 * len(neigh)) if neigh else None)
            mid_i = float(df["bid_px"].iloc[i] + df["ask_px"].iloc[i]) / 2
            samples.append({
                "row": int(i), "window": window,
                "abs_crossed_ticks": float(abs(spread.iloc[i]) / 0.25),
                "mid_over_neighbor_mid": (mid_i / neigh_mid if neigh_mid else None)})
        et = ts.dt.tz_convert(ET)
        return {"file": filename, "n_rows": int(len(df)),
                "first_ts_utc": ts.min().isoformat(),
                "last_ts_utc": ts.max().isoformat(),
                "first_date_et": et.min().date().isoformat(),
                "last_date_et": et.max().date().isoformat(),
                "n_dates_et": int(et.dt.date.nunique()),
                "n_crossed_ask_lt_bid": int(crossed.sum()),
                "n_nan_spread": int(spread.isna().sum()),
                "n_locked_ask_eq_bid": int((spread == 0).sum()),
                "samples": samples}

    def _qa_ts_phase_census(self, filename: str) -> dict:
        """QA-addendum diagnostic: NaT-timestamp census + crossed-row counts
        by ET session phase. Bounded counts only — never a frame."""
        assert_real_run_allowed(self.g9_flag, self.second_copy_flag)
        self._check_role()
        path = self.job_dir / filename
        manifest = manifests.load_manifest(self.job_dir)
        manifests.verify_file_against_manifest(path, manifest)
        df = self._decode(path, "dbn")
        ts = pd.to_datetime(df["ts"], utc=True)
        spread = df["ask_px"] - df["bid_px"]
        nat = ts.isna()
        minute = ts.dt.tz_convert(ET).dt.hour * 60 + ts.dt.tz_convert(ET).dt.minute
        crossed = spread < 0

        def phase(m):
            if pd.isna(m):
                return "nat_ts"
            m = int(m)
            if 570 <= m < 960:
                return "rth_0930_1600"
            if 1020 <= m < 1080:
                return "maintenance_1700_1800"
            return "other_open"

        cr_phase = minute[crossed].map(phase).value_counts().to_dict()
        cr_phase.setdefault("nat_ts", int((crossed & nat).sum()))
        rth_cross = (crossed & (minute >= 570) & (minute < 960))
        ticks = (spread[rth_cross].abs() / 0.25)
        rth_mag = ({"n": int(rth_cross.sum()),
                    "ticks_median": float(ticks.median()),
                    "ticks_p95": float(ticks.quantile(0.95)),
                    "ticks_max": float(ticks.max())}
                   if rth_cross.any() else {"n": 0})
        return {"file": filename, "n_rows": int(len(df)),
                "n_nat_ts": int(nat.sum()),
                "n_nat_ts_valid_spread": int((nat & spread.ge(0)).sum()),
                "crossed_by_phase": cr_phase,
                "rth_crossed_magnitude": rth_mag}

    # -- internals (raw BBO never escapes) ------------------------------------

    def _check_role(self) -> None:
        path_str = str(self.job_dir)
        if ROLE_DIRNAME not in path_str:
            raise RoleError(
                f"cost-calibration loader pointed at non-cost path: "
                f"{self.job_dir} (frozen data-role isolation)")
        # Reject mixed-role paths too (own-role substring present is
        # necessary but not sufficient — no OTHER role's marker may also
        # appear in the path; frozen data-role isolation, fail closed).
        foreign = [r.value for r in DataRole
                   if r.value != ROLE_DIRNAME and r.value in path_str]
        if foreign:
            raise RoleError(
                f"cost-calibration loader path also carries foreign "
                f"data-role marker(s) {foreign}: {self.job_dir} (mixed-role "
                "path rejected, frozen data-role isolation)")

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
        bad_spread = ~spread.ge(0)    # NaN or negative (crossed book)
        nat_ts = ts.isna()            # undefined ts_event sentinel (Databento)
        invalid = bad_spread | nat_ts
        events: list[validation.QAEvent] = []
        n_bad = int(bad_spread.sum())
        n_nat_valid = int((nat_ts & ~bad_spread).sum())
        frac = int(invalid.sum()) / len(df) if len(df) else 0.0
        # Crossed/one-sided/NaT snapshots are known 1-second BBO artifacts
        # (real A2 2025Q1: 0.022% crossed, 0.0017% NaT-ts). They cannot be
        # assigned a (minute, spread) observation and are EXCLUDED WITH A QA
        # EVENT — never silently. An abnormal fraction still fails closed.
        if frac > 0.01:
            raise validation.ValidationError(
                f"{int(invalid.sum())} invalid rows = {frac:.2%} > 1% "
                "abnormality threshold — fail closed, no repair")
        if n_bad:
            events.append(validation.QAEvent(
                "crossed_or_invalid_spread",
                f"{n_bad} of {len(df)} rows excluded from the spread table",
                n_bad))
        if n_nat_valid:
            events.append(validation.QAEvent(
                "nat_timestamp_excluded",
                f"{n_nat_valid} valid-spread rows with undefined ts_event "
                "excluded (cannot be assigned a minute slot)", n_nat_valid))
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
