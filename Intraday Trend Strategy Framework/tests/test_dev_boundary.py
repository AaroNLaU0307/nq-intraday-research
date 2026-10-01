"""M4-T2 / SA-2: Development data hard-boundary + DataRole enum tests.

Fabricated fixtures only — no production DBN/BBO file is ever read, and
nothing under C:\\Users\\Aaron\\quant-data is touched. Covers the eight
boundary cases Aaron named plus the three additional hardening cases
(parameter-widening guard, IV role fail-closed, cost<->development
directory swap), eleven named tests total, per
ops/M4_TASKBOARD/SA2_DEV_BOUNDARY.md REQUIRED TESTS.
"""
from __future__ import annotations

import inspect
import json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from itsf.data.cost_calibration_loader import CostCalibrationLoader
from itsf.data.cost_calibration_loader import RoleError as CostRoleError
from itsf.data.dbn_loader import DevelopmentSignalLoader, RoleError
from itsf.data.manifests import sha256_file
from itsf.data.roles import DataRole, ROLE_WINDOWS
from itsf.data.validation import ValidationError

ET = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")


# --- fixture builders (fabricated; never production data) --------------------

def fab_bars_utc(day: str = "2024-03-08", minutes: int = 30,
                 start_hh: int = 14, start_mm: int = 30) -> pd.DataFrame:
    """Fabricated 1-min UTC bars (14:30 UTC == 09:30/10:30 ET depending on
    DST). Mirrors tests/test_loader.py's fixture builder exactly."""
    t0 = datetime.fromisoformat(day).replace(hour=start_hh, minute=start_mm,
                                             tzinfo=UTC)
    rows = [{"ts": t0 + timedelta(minutes=i), "open": 100.0 + i,
             "high": 100.5 + i, "low": 99.5 + i, "close": 100.25 + i,
             "volume": 10, "symbol": "NQM4"} for i in range(minutes)]
    return pd.DataFrame(rows)


def fab_bbo_utc(day: str = "2025-01-06", rows: int = 40) -> pd.DataFrame:
    t0 = datetime.fromisoformat(day).replace(hour=14, minute=30, tzinfo=UTC)
    return pd.DataFrame([{"ts": t0 + timedelta(seconds=30 * i),
                          "bid_px": 20000.0, "ask_px": 20000.5,
                          "symbol": "MNQH5"} for i in range(rows)])


def make_job_dir(tmp_path: Path, role: str, filename: str,
                 df: pd.DataFrame, job_name: str = "JOB-TEST") -> Path:
    job = tmp_path / role / job_name
    job.mkdir(parents=True)
    fp = job / filename
    df_out = df.copy()
    df_out["ts"] = df_out["ts"].astype(str)
    df_out.to_csv(fp, index=False)
    manifest = {"files": {filename: {"sha256": sha256_file(fp)}}}
    (job / "_local_manifest.json").write_text(json.dumps(manifest),
                                              encoding="utf-8")
    return job


def flags(tmp_path: Path, g9: bool, copy: bool) -> tuple[Path, Path]:
    g = tmp_path / "G9.flag"
    c = tmp_path / "COPY.flag"
    if g9:
        g.write_text("x")
    if copy:
        c.write_text("x")
    return g, c


# --- 1/2/3: exact frozen boundary, both directions + exact reject day -------

def test_1_dev_start_day_allowed(tmp_path):
    """2010-06-06 (frozen DEV_START, inclusive) loads cleanly."""
    g, c = flags(tmp_path, True, True)
    df = fab_bars_utc(day="2010-06-06")
    job = make_job_dir(tmp_path, "development_signal", "bars.csv", df)
    ldr = DevelopmentSignalLoader(job, g9_flag=g, second_copy_flag=c)
    out, _ = ldr.load_real("bars.csv", source_format="synthetic_csv")
    assert len(out) == 30


def test_2_dev_end_minus_one_day_allowed(tmp_path):
    """2021-12-31, the last day inside the window, loads cleanly."""
    g, c = flags(tmp_path, True, True)
    df = fab_bars_utc(day="2021-12-31")
    job = make_job_dir(tmp_path, "development_signal", "bars.csv", df)
    ldr = DevelopmentSignalLoader(job, g9_flag=g, second_copy_flag=c)
    out, _ = ldr.load_real("bars.csv", source_format="synthetic_csv")
    assert len(out) == 30


def test_3_dev_end_exact_day_rejected(tmp_path):
    """2022-01-01 (frozen DEV_END_EXCLUSIVE) is rejected whole-file."""
    g, c = flags(tmp_path, True, True)
    df = fab_bars_utc(day="2022-01-01")
    job = make_job_dir(tmp_path, "development_signal", "bars.csv", df)
    ldr = DevelopmentSignalLoader(job, g9_flag=g, second_copy_flag=c)
    with pytest.raises(ValidationError):
        ldr.load_real("bars.csv", source_format="synthetic_csv")


# --- 4: any 2025 file rejected -----------------------------------------------

def test_4_year_2025_timestamp_file_rejected(tmp_path):
    g, c = flags(tmp_path, True, True)
    df = fab_bars_utc(day="2025-03-15")
    job = make_job_dir(tmp_path, "development_signal", "bars.csv", df)
    ldr = DevelopmentSignalLoader(job, g9_flag=g, second_copy_flag=c)
    with pytest.raises(ValidationError):
        ldr.load_real("bars.csv", source_format="synthetic_csv")


# --- 5: correct hash does not exempt a wrong role directory -----------------

def test_5_manifest_hash_correct_but_role_wrong_still_role_error(tmp_path):
    """make_job_dir always writes a byte-correct sha256 manifest entry. Put
    that correctly-hashed file under the WRONG role directory and confirm the
    failure is RoleError, not (e.g.) a pass-through or ManifestError — role
    check runs before manifest check in the frozen fail-closed order, so a
    correct hash never exempts a wrong role."""
    g, c = flags(tmp_path, True, True)
    df = fab_bars_utc()
    job = make_job_dir(tmp_path, "execution_cost_calibration", "bars.csv", df)
    ldr = DevelopmentSignalLoader(job, g9_flag=g, second_copy_flag=c)
    with pytest.raises(RoleError):
        ldr.load_real("bars.csv", source_format="synthetic_csv")


# --- 6: development-labeled directory, IV-era timestamps inside ------------

def test_6_development_dir_disguise_with_iv_era_timestamps_rejected(tmp_path):
    """Directory/filename claims development_signal, but the bars inside are
    deep in the Internal-Validation era (2023) rather than right at the
    boundary — the path label grants no exemption from the timestamp check."""
    g, c = flags(tmp_path, True, True)
    df = fab_bars_utc(day="2023-06-15")
    job = make_job_dir(tmp_path, "development_signal", "bars.csv", df)
    ldr = DevelopmentSignalLoader(job, g9_flag=g, second_copy_flag=c)
    with pytest.raises(ValidationError):
        ldr.load_real("bars.csv", source_format="synthetic_csv")


# --- 7: cross-boundary single file rejected whole-file, no truncation ------

def test_7_cross_boundary_single_file_rejected_no_truncated_rows(tmp_path):
    """One file straddling the boundary (some rows ET 2021-12-31, some ET
    2022-01-01) must be rejected in its entirety — never truncated/filtered
    to keep only the in-window rows."""
    g, c = flags(tmp_path, True, True)
    # UTC 2022-01-01 04:58..05:03 -> ET (UTC-5, standard time) 2021-12-31
    # 23:58/23:59 then 2022-01-01 00:00/00:01/00:02/00:03: 2 rows pre-boundary,
    # 4 rows at/after the frozen end date, all in one file.
    df = fab_bars_utc(day="2022-01-01", start_hh=4, start_mm=58, minutes=6)
    job = make_job_dir(tmp_path, "development_signal", "bars.csv", df)
    ldr = DevelopmentSignalLoader(job, g9_flag=g, second_copy_flag=c)
    returned = {"value": None}
    with pytest.raises(ValidationError):
        out, events = ldr.load_real("bars.csv", source_format="synthetic_csv")
        returned["value"] = out          # unreachable if fail-closed holds
    assert returned["value"] is None, (
        "loader must reject the whole file, not return a truncated/filtered "
        "subset of in-window rows")


# --- 8: synthetic entry is bounded by the same window check -----------------

def test_8_synthetic_entry_still_bounded_by_dev_window():
    """load_synthetic() skips guard/role/manifest by design (frozen,
    synthetic-only phase) but MUST still run the same range check — it calls
    the identical _postprocess_static pipeline as the real entry."""
    bad = fab_bars_utc(day="2022-06-15")             # deep inside IV era
    with pytest.raises(ValidationError):
        DevelopmentSignalLoader.load_synthetic(bad)
    good = fab_bars_utc(day="2021-12-31")
    out, events = DevelopmentSignalLoader.load_synthetic(good)
    assert len(out) == 30 and isinstance(events, list)


# --- 9: no constructor/method parameter can widen the boundary -------------

def test_9_no_signature_parameter_can_widen_boundary():
    """Boundaries are frozen module-level constants. Confirm no constructor
    or public loading method accepts ANY parameter (start/end/window/dev_end/
    override/etc.) that could relax them — only the documented, unchanged
    public signatures exist."""
    dev_ctor = set(inspect.signature(DevelopmentSignalLoader.__init__)
                   .parameters) - {"self"}
    assert dev_ctor == {"job_dir", "g9_flag", "second_copy_flag"}

    dev_load_real = set(inspect.signature(DevelopmentSignalLoader.load_real)
                        .parameters) - {"self"}
    assert dev_load_real == {"filename", "source_format"}

    dev_load_synth = set(inspect.signature(
        DevelopmentSignalLoader.load_synthetic).parameters)
    assert dev_load_synth == {"df"}

    cost_ctor = set(inspect.signature(CostCalibrationLoader.__init__)
                    .parameters) - {"self"}
    assert cost_ctor == {"job_dir", "g9_flag", "second_copy_flag"}

    cost_build_real = set(inspect.signature(
        CostCalibrationLoader.build_spread_table_real).parameters) - {"self"}
    assert cost_build_real == {"filename", "source_format"}

    cost_build_synth = set(inspect.signature(
        CostCalibrationLoader.build_spread_table_synthetic).parameters)
    assert cost_build_synth == {"bbo"}


# --- 10: INTERNAL_VALIDATION_SIGNAL never loadable, on any path -------------

def test_10_internal_validation_role_never_loadable(tmp_path):
    """IV is deliberately absent from ROLE_WINDOWS, and any attempt to point
    either concrete loader at a path carrying ONLY the IV role marker fails
    closed as a named RoleError — never a bare KeyError, never a silent
    open."""
    assert DataRole.INTERNAL_VALIDATION_SIGNAL not in ROLE_WINDOWS
    with pytest.raises(KeyError):
        _ = ROLE_WINDOWS[DataRole.INTERNAL_VALIDATION_SIGNAL]

    g, c = flags(tmp_path, True, True)
    dev_job = make_job_dir(tmp_path, "internal_validation_signal", "bars.csv",
                           fab_bars_utc())
    dev_ldr = DevelopmentSignalLoader(dev_job, g9_flag=g, second_copy_flag=c)
    with pytest.raises(RoleError):
        dev_ldr.load_real("bars.csv", source_format="synthetic_csv")

    cost_job = make_job_dir(tmp_path, "internal_validation_signal", "bbo.csv",
                            fab_bbo_utc(), job_name="JOB-TEST-COST")
    cost_ldr = CostCalibrationLoader(cost_job, g9_flag=g, second_copy_flag=c)
    with pytest.raises(CostRoleError):
        cost_ldr.build_spread_table_real("bbo.csv", source_format="synthetic_csv")


# --- 11: development <-> cost directory swap rejected both ways ------------

def test_11a_development_loader_rejects_cost_directory(tmp_path):
    g, c = flags(tmp_path, True, True)
    job = make_job_dir(tmp_path, "execution_cost_calibration", "bars.csv",
                       fab_bars_utc())
    ldr = DevelopmentSignalLoader(job, g9_flag=g, second_copy_flag=c)
    with pytest.raises(RoleError):
        ldr.load_real("bars.csv", source_format="synthetic_csv")


def test_11b_cost_loader_rejects_development_directory(tmp_path):
    g, c = flags(tmp_path, True, True)
    job = make_job_dir(tmp_path, "development_signal", "bbo.csv",
                       fab_bbo_utc())
    ldr = CostCalibrationLoader(job, g9_flag=g, second_copy_flag=c)
    with pytest.raises(CostRoleError):
        ldr.build_spread_table_real("bbo.csv", source_format="synthetic_csv")


# --- supplementary: mixed-role path (both markers present) rejected --------

def test_mixed_role_path_rejected_even_with_own_role_present(tmp_path):
    """A path that contains BOTH the loader's own role marker and a foreign
    role marker (e.g. a disguised/concatenated path) must still fail closed,
    per INTERFACES: 'job_dir 路径必须包含本 loader 的 DataRole.value 且不得
    包含其他任何 DataRole.value'."""
    g, c = flags(tmp_path, True, True)
    df = fab_bars_utc()
    job_name = "JOB-development_signal-and-internal_validation_signal-mixed"
    job = make_job_dir(tmp_path, "development_signal", "bars.csv", df,
                       job_name=job_name)
    ldr = DevelopmentSignalLoader(job, g9_flag=g, second_copy_flag=c)
    with pytest.raises(RoleError):
        ldr.load_real("bars.csv", source_format="synthetic_csv")
