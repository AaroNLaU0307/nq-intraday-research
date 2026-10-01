"""Development-signal loader (main-agent authored, milestone 3).

The ONLY entry to real Development NQ data. Fail-closed order, frozen:
  1. guards.assert_real_run_allowed()   — BEFORE any file is opened
  2. role check                          — path must live under development_signal/
  3. manifest SHA-256                    — mismatch = hard fail, no auto-repair
  4. decode + schema + range/symbol checks
Alpha code consumes ONLY this loader; it can never see execution-cost BBO
(role check makes cross-role reads fail closed).
# frozen: charter 数据角色隔离; platform_params s0_cost_handoff (guards);
# S0 SS1 data roles
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from itsf.data import manifests, validation
from itsf.data.roles import DataRole, ROLE_WINDOWS
from itsf.guards import assert_real_run_allowed, G9_FLAG, SECOND_COPY_FLAG

ET = ZoneInfo("America/New_York")
ROLE_DIRNAME = DataRole.DEVELOPMENT_SIGNAL.value
EXPECTED_SYMBOL_ROOT = "NQ"           # frozen: purchase_plan A1 NQ.v.0
# frozen: STUDY_0_PREREGISTRATION.md 行 24 (Development row) + purchase_plan
# A1 (end: "2022-01-01", exclusive). CORRECTED 2026-07-29 (M4-T2 / SA-2): this
# constant previously read "2025-07-01", mis-citing purchase_plan A1 — that
# date is actually the Internal-Validation end (purchase_plan A3 /
# prereg IV row), which this loader must NEVER accept. Local A1 archive only
# ever held 2010-06..2021-12 files, so the bug had not caused an actual
# out-of-window read; boundary is hardened here regardless. Sourced from the
# frozen module-level roles.ROLE_WINDOWS mapping — single source of truth
# shared with cost_calibration_loader.py, not overridable at runtime.
DEV_START, DEV_END_EXCLUSIVE = ROLE_WINDOWS[DataRole.DEVELOPMENT_SIGNAL]


class RoleError(RuntimeError):
    pass


@dataclass
class DevelopmentSignalLoader:
    """Loads 1-minute Development bars into the canonical frame schema
    (ts tz-aware ET, open, high, low, close, volume + qa flags)."""
    job_dir: Path
    g9_flag: Path = G9_FLAG
    second_copy_flag: Path = SECOND_COPY_FLAG

    def __post_init__(self) -> None:
        self.job_dir = Path(self.job_dir)

    # -- real entry -----------------------------------------------------------

    def load_real(self, filename: str,
                  source_format: str = "dbn") -> tuple[pd.DataFrame, list]:
        """Real-file entry. Guard FIRST — before open, before existence checks
        beyond the guard itself (frozen fail-closed order)."""
        assert_real_run_allowed(self.g9_flag, self.second_copy_flag)   # step 1
        self._check_role()                                             # step 2
        path = self.job_dir / filename
        manifest = manifests.load_manifest(self.job_dir)               # step 3
        manifests.verify_file_against_manifest(path, manifest)
        raw = self._decode(path, source_format)                        # step 4
        return self._postprocess(raw)

    # -- synthetic entry (guard-free by design; frozen: synthetic-only phase) --

    @staticmethod
    def load_synthetic(df: pd.DataFrame) -> tuple[pd.DataFrame, list]:
        """Test/synthetic entry: same validation pipeline, no guard, no files."""
        return DevelopmentSignalLoader._postprocess_static(df)

    # -- internals ------------------------------------------------------------

    def _check_role(self) -> None:
        path_str = str(self.job_dir)
        if ROLE_DIRNAME not in path_str:
            raise RoleError(
                f"development loader pointed at non-development path: "
                f"{self.job_dir} (frozen data-role isolation)")
        # Reject mixed-role paths too, e.g. "development_signal/../
        # internal_validation_signal/JOB" — own-role substring present is
        # necessary but not sufficient; no OTHER role's marker may also be
        # present (frozen data-role isolation, fail closed).
        foreign = [r.value for r in DataRole
                   if r.value != ROLE_DIRNAME and r.value in path_str]
        if foreign:
            raise RoleError(
                f"development loader path also carries foreign data-role "
                f"marker(s) {foreign}: {self.job_dir} (mixed-role path "
                "rejected, frozen data-role isolation)")

    @staticmethod
    def _decode(path: Path, source_format: str) -> pd.DataFrame:
        if source_format == "synthetic_csv":
            df = pd.read_csv(path)
            df["ts"] = pd.to_datetime(df["ts"], utc=True)
            return df
        if source_format == "dbn":
            import databento as db                       # real decode path
            store = db.DBNStore.from_file(path)
            df = store.to_df().reset_index()
            df = df.rename(columns={"ts_event": "ts"})
            return df
        raise ValueError(f"unknown source_format {source_format!r}")

    def _postprocess(self, raw: pd.DataFrame) -> tuple[pd.DataFrame, list]:
        return self._postprocess_static(raw)

    @staticmethod
    def _postprocess_static(raw: pd.DataFrame) -> tuple[pd.DataFrame, list]:
        validation.check_schema(raw)
        df = raw.copy()
        ts = pd.to_datetime(df["ts"], utc=True)
        df["ts"] = ts.dt.tz_convert(ET)          # UTC -> America/New_York (DST-safe)
        lo, hi = df["ts"].min(), df["ts"].max()
        if lo.date().isoformat() < DEV_START or hi.date().isoformat() >= DEV_END_EXCLUSIVE:
            raise validation.ValidationError(
                f"bars outside the Development window [{DEV_START}, "
                f"{DEV_END_EXCLUSIVE}): {lo.date()}..{hi.date()} (fail closed)")
        if "symbol" in df.columns:
            bad = ~df["symbol"].astype(str).str.startswith(EXPECTED_SYMBOL_ROOT)
            if bad.any():
                raise validation.ValidationError(
                    f"{int(bad.sum())} rows with unexpected symbol root "
                    f"(want {EXPECTED_SYMBOL_ROOT}*) — instrument mismatch")
        return validation.qa_bars(df, instrument_role="development")
