"""Acquire the four real inputs `build_universe` needs. Gate-first.

WHAT WAS MISSING. `supplement_inputs.assemble_chain_inputs` receives
`bars_by_date`, a `SessionSchedule`, an `EventCalendar` and `expected_day_set`
and never fetches any of them -- deliberately, so it stays pure. Nothing
fetched them either: `load_real` had no caller anywhere in the package, no
production code built a `SessionSchedule` or an `EventCalendar`, and
`roll_intervals` defaulted to `()`. This module is the one place that does.

ONE MODULE, NOT TWO. `data/` may not import `s0/` -- the dependency runs the
other way -- so a builder returning `SessionSchedule` cannot live there. `mc/`
already imports both, so the acquisition lives here rather than being split
across a layer boundary for its own sake.

THE AUTHORIZATION IS ENFORCED, NOT DOCUMENTED. `AUTHORIZED_JOB_DIR` and
`AUTHORIZED_MANIFEST_SHA256` pin Aaron's 2026-09-05 sentence: that directory,
and the files that manifest lists. A different job_dir or a changed manifest
refuses. Without those two checks the constants would be a comment, and
`_check_role` cannot help -- measured: the attested primary and an unattested
copy under OneDrive both pass it.

NOTHING HERE RUNS A SUPPLEMENT. It returns inputs. Execution still needs a
live P2, and `run_supplement_production` still refuses without one.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

__all__ = ["AUTHORIZED_JOB_DIR", "AUTHORIZED_MANIFEST_SHA256",
           "F10_EVENTS_CSV", "verify_authorized_job_dir",
           "load_bars_by_date", "build_event_calendar",
           "build_session_schedule", "build_roll_intervals",
           "acquire_production_inputs"]

#: Aaron's 2026-09-05 authorization, verbatim. Closed list, no wildcard.
AUTHORIZED_JOB_DIR = Path(
    r"C:\Users\Aaron\quant-data\databento-archive\intraday-trend"
    r"\development_signal\GLBX-20260727-DL3BEBCHJA")
AUTHORIZED_MANIFEST_SHA256 = (
    "d8d1edc7b549b441d691dda74331806c957a19946e746bd795978e01d73c3ae8")

#: The frozen F10 event table, in the repository since 2026-07-29.
F10_EVENTS_CSV = (Path(__file__).resolve().parents[3]
                  / "gate1" / "f10_event_calendar" / "f10_events.csv")

#: `SessionSchedule.close_minute` wants the OFFICIAL RTH close minute; the
#: exchange calendar reports the futures close (17:00 == 1020). Capping at
#: 16:00 gives 960 on a full session and the real early close on a half day
#: (13:00 == 780), which is what a frozen L44 excluded day is keyed on. The
#: cap can only ever mark MORE days early, never fewer, so it cannot include
#: a day that should have been excluded.
RTH_CLOSE_MINUTE = 960


def verify_authorized_job_dir(job_dir=AUTHORIZED_JOB_DIR) -> Path:
    """The authorization, checked rather than asserted. Refuses loudly."""
    root = Path(job_dir)
    if str(root) != str(AUTHORIZED_JOB_DIR):
        raise PermissionError(
            "job_dir %s is not the authorized directory %s — the "
            "authorization named one path with no wildcard"
            % (root, AUTHORIZED_JOB_DIR))
    manifest = root / "manifest.json"
    if not manifest.is_file():
        raise FileNotFoundError("no manifest.json under %s" % root)
    got = hashlib.sha256(manifest.read_bytes()).hexdigest()
    if got != AUTHORIZED_MANIFEST_SHA256:
        raise PermissionError(
            "manifest.json is %s, authorization pinned %s — the authorized "
            "file set is whatever THAT manifest listed"
            % (got, AUTHORIZED_MANIFEST_SHA256))
    return root


def _manifest_data_files(job_dir: Path) -> list:
    from ..data import manifests

    listed = manifests.load_manifest(job_dir)["files"]
    return sorted(n for n in listed if n.endswith(".dbn.zst"))


def load_bars_by_date(job_dir=AUTHORIZED_JOB_DIR, *, source_format="dbn"):
    """`{ET date: that date's 1-minute bars}` plus the QA events seen.

    Every file goes through `DevelopmentSignalLoader.load_real`, which is
    gate-first: `assert_real_run_allowed`, then the data-role check, then a
    per-file sha256 against the manifest, then the decode. Only files the
    AUTHORIZED manifest lists are read.
    """
    import pandas as pd

    from ..data.dbn_loader import DevelopmentSignalLoader

    root = verify_authorized_job_dir(job_dir)
    loader = DevelopmentSignalLoader(root)
    frames, qa = [], []
    for name in _manifest_data_files(root):
        df, events = loader.load_real(name, source_format)
        frames.append(df)
        qa.extend(events)
    if not frames:
        raise ValueError("the authorized manifest listed no .dbn.zst files")
    allbars = pd.concat(frames, ignore_index=True)
    # ET calendar date of each bar's start. `ts` is already tz-aware ET after
    # `_postprocess_static`, so no second conversion happens here.
    dates = allbars["ts"].dt.strftime("%Y-%m-%d")
    return ({d: g.reset_index(drop=True)
             for d, g in allbars.groupby(dates, sort=True)}, qa)


def build_event_calendar(csv_path=F10_EVENTS_CSV):
    """`EventCalendar` from the frozen F10 table.

    The three release flags map straight onto the three date sets. The other
    two fields are left EMPTY and that is deliberate: `unscheduled_fomc_dates`
    is IR-13's enumerated list and `raw_multi_event_dates` is IR-12's sidecar,
    and neither is a column in this table. Filling them by inference would put
    a derived set where the frozen source has none.
    """
    import csv

    from ..s0.context import EventCalendar

    cpi, nfp, fomc = set(), set(), set()
    with open(csv_path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            date = row["date_et"]
            if row["is_cpi_release_day"] == "true":
                cpi.add(date)
            if row["is_nfp_release_day"] == "true":
                nfp.add(date)
            if row["is_fomc_statement_day"] == "true":
                fomc.add(date)
    return EventCalendar(cpi_dates=frozenset(cpi), nfp_dates=frozenset(nfp),
                         fomc_statement_dates=frozenset(fomc))


def build_session_schedule(start: str, end: str, *, bars_by_date=None):
    """`SessionSchedule` from the official CME_Equity calendar.

    `vendor_degraded_dates` is the set of scheduled sessions for which the
    authorized files carry NO bars at all. Partially missing sessions are
    already handled elsewhere -- the funnel excludes a day missing more than
    `MAX_MISSING_FRACTION` -- so this covers the case IR-19 actually needs:
    a session that happened and about which we hold nothing.
    """
    import pandas_market_calendars as mcal

    from ..data.calendar import ET
    from ..s0.context import SessionSchedule

    schedule = mcal.get_calendar("CME_Equity").schedule(start_date=start,
                                                        end_date=end)
    if len(schedule) == 0:
        raise ValueError("no CME_Equity sessions in [%s, %s]" % (start, end))
    close_minute = {}
    for day, row in schedule.iterrows():
        close = row["market_close"].tz_convert(ET)
        close_minute[day.strftime("%Y-%m-%d")] = min(
            close.hour * 60 + close.minute, RTH_CLOSE_MINUTE)
    degraded = frozenset()
    if bars_by_date is not None:
        degraded = frozenset(d for d in close_minute if d not in bars_by_date)
    return SessionSchedule(close_minute=close_minute,
                           vendor_degraded_dates=degraded)


def build_roll_intervals(job_dir=AUTHORIZED_JOB_DIR):
    """`RollInterval`s from the vendor's official symbology mapping.

    Never from prices and never from the `symbol` column -- that column is
    the continuous symbol on every row of every file, including across a
    roll. See `itsf.data.symbology`.
    """
    from ..data import symbology
    from ..s0.context import RollInterval

    root = verify_authorized_job_dir(job_dir)
    merged = symbology.coalesce(symbology.read_vendor_intervals(root))
    return tuple(RollInterval(start_date_utc=start, end_date_utc_excl=end,
                              instrument_id=int(instrument))
                 for start, end, instrument in merged)


def acquire_production_inputs(job_dir=AUTHORIZED_JOB_DIR, *,
                              source_format="dbn"):
    """The four inputs, acquired once. Returns
    `(bars_by_date, schedule, events, roll_intervals, qa_events)`."""
    bars, qa = load_bars_by_date(job_dir, source_format=source_format)
    days = sorted(bars)
    schedule = build_session_schedule(days[0], days[-1], bars_by_date=bars)
    return (bars, schedule, build_event_calendar(),
            build_roll_intervals(job_dir), qa)
