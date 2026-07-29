"""Loader milestone tests: guard matrix, role isolation, manifests, QA,
boundaries. Fabricated fixtures only — no production DBN is ever read.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import pytest

from itsf.data.cost_calibration_loader import CostCalibrationLoader
from itsf.data.cost_calibration_loader import RoleError as CostRoleError
from itsf.data.dbn_loader import DevelopmentSignalLoader, RoleError
from itsf.data.manifests import ManifestError, load_manifest, sha256_file
from itsf.data.validation import (MNQ_LAUNCH_DATE, QAEvent, ValidationError,
                                  qa_bars)
from itsf.guards import RunBlockedError

ET = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")


# --- fixture builders (fabricated; never production data) --------------------

def fab_bars_utc(day: str = "2021-06-15", minutes: int = 30,
                 start_hh: int = 14, start_mm: int = 30) -> pd.DataFrame:
    """Fabricated 1-min UTC bars (14:30 UTC == 09:30 ET on an EST day).
    Default day corrected to 2021-06-15 (M4-T2 / SA-2): it must sit inside
    the frozen Development window [2010-06-06, 2022-01-01) now that the
    boundary bug (previously 2025-07-01) is fixed — 2024-03-08 no longer
    qualifies. Callers that specifically exercise the boundary/DST pass an
    explicit `day=`."""
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
                 df: pd.DataFrame) -> Path:
    job = tmp_path / role / "JOB-TEST"
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


# --- guard matrix (inv: fail BEFORE open) ------------------------------------

@pytest.mark.parametrize("g9,copy", [(False, False), (True, False), (False, True)])
def test_guard_matrix_blocks_before_open(tmp_path, g9, copy):
    g, c = flags(tmp_path, g9, copy)
    ldr = DevelopmentSignalLoader(tmp_path / "development_signal" / "NOPE",
                                  g9_flag=g, second_copy_flag=c)
    # the target file does not even exist: RunBlockedError (not FileNotFound)
    # proves the guard fires BEFORE any open attempt.
    with pytest.raises(RunBlockedError):
        ldr.load_real("missing.csv", source_format="synthetic_csv")


def test_double_true_reads_synthetic_mounted_file(tmp_path):
    g, c = flags(tmp_path, True, True)
    df = fab_bars_utc()
    job = make_job_dir(tmp_path, "development_signal", "bars.csv", df)
    ldr = DevelopmentSignalLoader(job, g9_flag=g, second_copy_flag=c)
    out, events = ldr.load_real("bars.csv", source_format="synthetic_csv")
    assert len(out) == 30
    assert str(out["ts"].dt.tz) == "America/New_York"        # UTC -> ET


def test_synthetic_entry_never_guarded():
    out, events = DevelopmentSignalLoader.load_synthetic(fab_bars_utc())
    assert len(out) == 30 and isinstance(events, list)


# --- role isolation ----------------------------------------------------------

def test_development_loader_rejects_cost_directory(tmp_path):
    g, c = flags(tmp_path, True, True)
    df = fab_bars_utc()
    job = make_job_dir(tmp_path, "execution_cost_calibration", "bars.csv", df)
    ldr = DevelopmentSignalLoader(job, g9_flag=g, second_copy_flag=c)
    with pytest.raises(RoleError):
        ldr.load_real("bars.csv", source_format="synthetic_csv")


def test_cost_loader_rejects_development_directory(tmp_path):
    g, c = flags(tmp_path, True, True)
    job = make_job_dir(tmp_path, "development_signal", "bbo.csv", fab_bbo_utc())
    ldr = CostCalibrationLoader(job, g9_flag=g, second_copy_flag=c)
    with pytest.raises(CostRoleError):
        ldr.build_spread_table_real("bbo.csv", source_format="synthetic_csv")


def test_alpha_cannot_obtain_raw_bbo():
    # The ONLY public products of the cost loader are spread tables; no public
    # attribute or return value exposes raw BBO rows.
    public = [m for m in dir(CostCalibrationLoader)
              if not m.startswith("_")]
    assert set(public) <= {"build_spread_table_real",
                           "build_spread_table_synthetic", "job_dir",
                           "g9_flag", "second_copy_flag"}
    tbl, _ = CostCalibrationLoader.build_spread_table_synthetic(fab_bbo_utc())
    assert "bid_px" not in tbl.columns and "ask_px" not in tbl.columns


# --- manifest verification ---------------------------------------------------

def test_manifest_mismatch_fails_closed(tmp_path):
    g, c = flags(tmp_path, True, True)
    df = fab_bars_utc()
    job = make_job_dir(tmp_path, "development_signal", "bars.csv", df)
    # corrupt the data file AFTER manifest creation
    fp = job / "bars.csv"
    fp.write_bytes(fp.read_bytes() + b"tamper")
    ldr = DevelopmentSignalLoader(job, g9_flag=g, second_copy_flag=c)
    with pytest.raises(ManifestError):
        ldr.load_real("bars.csv", source_format="synthetic_csv")


def test_manifest_missing_entry_fails(tmp_path):
    g, c = flags(tmp_path, True, True)
    df = fab_bars_utc()
    job = make_job_dir(tmp_path, "development_signal", "bars.csv", df)
    other = job / "other.csv"
    other.write_text("ts,open,high,low,close,volume\n")
    ldr = DevelopmentSignalLoader(job, g9_flag=g, second_copy_flag=c)
    with pytest.raises(ManifestError):
        ldr.load_real("other.csv", source_format="synthetic_csv")


def test_official_databento_manifest_format_accepted(tmp_path):
    g, c = flags(tmp_path, True, True)
    df = fab_bars_utc()
    job = tmp_path / "development_signal" / "JOB-OFFICIAL"
    job.mkdir(parents=True)
    fp = job / "bars.csv"
    df_out = df.copy()
    df_out["ts"] = df_out["ts"].astype(str)
    df_out.to_csv(fp, index=False)
    official = {"job_id": "JOB-OFFICIAL",
                "files": [{"filename": "bars.csv", "size": fp.stat().st_size,
                           "hash": f"sha256:{sha256_file(fp)}"}]}
    (job / "manifest.json").write_text(json.dumps(official), encoding="utf-8")
    ldr = DevelopmentSignalLoader(job, g9_flag=g, second_copy_flag=c)
    out, _ = ldr.load_real("bars.csv", source_format="synthetic_csv")
    assert len(out) == 30


def test_raw_bytes_unchanged_by_loading(tmp_path):
    g, c = flags(tmp_path, True, True)
    df = fab_bars_utc()
    job = make_job_dir(tmp_path, "development_signal", "bars.csv", df)
    before = sha256_file(job / "bars.csv")
    ldr = DevelopmentSignalLoader(job, g9_flag=g, second_copy_flag=c)
    ldr.load_real("bars.csv", source_format="synthetic_csv")
    assert sha256_file(job / "bars.csv") == before


# --- QA events ---------------------------------------------------------------

def test_duplicate_and_missing_minutes_flagged_not_dropped():
    df = fab_bars_utc(minutes=10)
    df = pd.concat([df, df.iloc[[3]]], ignore_index=True)     # duplicate
    out, events = qa_bars(df, expected_minutes=12)
    kinds = {e.kind for e in events}
    assert "duplicate_minute" in kinds and "missing_minute" in kinds
    assert len(out) == 11                                     # nothing dropped


def test_bad_prices_and_zero_volume_flagged():
    df = fab_bars_utc(minutes=5)
    df.loc[1, "close"] = np.nan
    df.loc[2, "low"] = -5.0
    df.loc[3, "volume"] = 0
    out, events = qa_bars(df)
    kinds = {e.kind for e in events}
    assert "bad_price" in kinds and "zero_volume" in kinds
    assert out["qa_bad_price"].sum() == 2 and out["qa_zero_volume"].sum() == 1


def test_qa_events_contain_no_research_numbers():
    df = fab_bars_utc(minutes=5)
    df.loc[1, "close"] = np.nan
    _, events = qa_bars(df)
    for e in events:
        assert "pnl" not in e.detail.lower()
        assert "$" not in e.detail and "ev" not in e.detail.lower()


# --- boundaries --------------------------------------------------------------

def test_mnq_launch_boundary_fails_closed():
    bbo = fab_bbo_utc(day="2019-05-03")                       # before launch
    with pytest.raises(ValidationError):
        CostCalibrationLoader.build_spread_table_synthetic(bbo)
    assert MNQ_LAUNCH_DATE.isoformat() == "2019-05-06"


def test_crossed_forensics_summary_is_bounded_and_structural():
    bbo = fab_bbo_utc(rows=60)
    bbo.loc[7, "ask_px"] = bbo.loc[7, "bid_px"] - 0.25     # 1-tick crossed
    bbo.loc[20, "ask_px"] = bbo.loc[20, "bid_px"]          # locked (ask==bid)
    bbo.loc[33, "ask_px"] = float("nan")                   # NaN spread
    out = CostCalibrationLoader._forensics_from_frame(
        bbo, "fab.dbn.zst", seed=20260729, k=5)
    assert out["n_rows"] == 60
    assert out["n_crossed_ask_lt_bid"] == 1
    assert out["n_locked_ask_eq_bid"] == 1
    assert out["n_nan_spread"] == 1
    assert len(out["samples"]) == 1
    s = out["samples"][0]
    assert s["abs_crossed_ticks"] == pytest.approx(1.0)
    assert s["mid_over_neighbor_mid"] == pytest.approx(1.0, abs=1e-4)
    # bounded structural dict only — no DataFrame may escape
    assert not any(isinstance(v, pd.DataFrame) for v in out.values())


def test_tiny_crossed_fraction_excluded_with_event():
    bbo = fab_bbo_utc(rows=400)
    bbo.loc[0, "ask_px"] = bbo.loc[0, "bid_px"] - 1.0         # 1/400 = 0.25%
    tbl, events = CostCalibrationLoader.build_spread_table_synthetic(bbo)
    kinds = [e.kind for e in events]
    assert kinds == ["crossed_or_invalid_spread"] and events[0].count == 1
    assert int(tbl["n_obs"].sum()) == 399                     # excluded, counted


def test_nat_timestamp_valid_spread_excluded_with_event():
    bbo = fab_bbo_utc(rows=400)
    bbo.loc[5, "ts"] = pd.NaT                  # undefined ts_event, spread OK
    tbl, events = CostCalibrationLoader.build_spread_table_synthetic(bbo)
    kinds = [e.kind for e in events]
    assert kinds == ["nat_timestamp_excluded"] and events[0].count == 1
    assert int(tbl["n_obs"].sum()) == 399      # excluded with event, not silently


def test_development_window_end_boundary_rejected(tmp_path):
    # frozen dev-window end is 2022-01-01 (exclusive) — STUDY_0_PREREGISTRATION
    # .md 行 24 + purchase_plan A1 end. (Corrected M4-T2 / SA-2: this test
    # previously used "2025-07-01", which mis-tested the Internal-Validation
    # end date instead of the actual Development boundary.)
    g, c = flags(tmp_path, True, True)
    df = fab_bars_utc(day="2022-01-01")                       # >= dev end
    job = make_job_dir(tmp_path, "development_signal", "bars.csv", df)
    ldr = DevelopmentSignalLoader(job, g9_flag=g, second_copy_flag=c)
    with pytest.raises(ValidationError):
        ldr.load_real("bars.csv", source_format="synthetic_csv")


def test_development_window_last_allowed_day(tmp_path):
    # 2021-12-31 is the last day inside the frozen Development window and
    # must load cleanly (other boundary direction of the fix above).
    g, c = flags(tmp_path, True, True)
    df = fab_bars_utc(day="2021-12-31")
    job = make_job_dir(tmp_path, "development_signal", "bars.csv", df)
    ldr = DevelopmentSignalLoader(job, g9_flag=g, second_copy_flag=c)
    out, _ = ldr.load_real("bars.csv", source_format="synthetic_csv")
    assert len(out) == 30


def test_symbol_mismatch_fails(tmp_path):
    g, c = flags(tmp_path, True, True)
    df = fab_bars_utc()
    df["symbol"] = "GCQ4"                                     # wrong instrument
    job = make_job_dir(tmp_path, "development_signal", "bars.csv", df)
    ldr = DevelopmentSignalLoader(job, g9_flag=g, second_copy_flag=c)
    with pytest.raises(ValidationError):
        ldr.load_real("bars.csv", source_format="synthetic_csv")


def test_dst_conversion_spring_and_fall():
    # Dates moved inside the frozen Development window [2010-06-06,
    # 2022-01-01) (M4-T2 / SA-2 boundary fix); 2021 spring-forward was
    # 2021-03-14, same Fri-before/Mon-after shape as the original 2024 dates.
    # 2021-03-12 is EST (UTC-5): 14:30 UTC -> 09:30 ET
    est = DevelopmentSignalLoader.load_synthetic(fab_bars_utc("2021-03-12"))[0]
    assert est["ts"].iloc[0].hour == 9 and est["ts"].iloc[0].minute == 30
    # 2021-03-15 is EDT (UTC-4): 13:30 UTC -> 09:30 ET
    edt = DevelopmentSignalLoader.load_synthetic(
        fab_bars_utc("2021-03-15", start_hh=13))[0]
    assert edt["ts"].iloc[0].hour == 9 and edt["ts"].iloc[0].minute == 30


def test_spread_table_schema_and_abnormal_fraction_fails():
    tbl, events = CostCalibrationLoader.build_spread_table_synthetic(fab_bbo_utc())
    assert list(tbl.columns) == ["minute_of_day_et", "spread_median_points",
                                 "spread_p90_points", "spread_p95_points",
                                 "n_obs"]
    assert tbl["spread_median_points"].tolist() == pytest.approx([0.5] * len(tbl))
    assert events == []
    bad = fab_bbo_utc(rows=40)
    bad.loc[0, "ask_px"] = bad.loc[0, "bid_px"] - 1.0         # 1/40 = 2.5% > 1%
    with pytest.raises(ValidationError):
        CostCalibrationLoader.build_spread_table_synthetic(bad)
