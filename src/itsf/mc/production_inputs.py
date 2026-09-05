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

#: The frozen symbology mapping S0-T001 ITSELF used (`load_real_roll_intervals`
#: reads exactly this file). NOT the live DBN metadata: the supplement is a
#: RECONSTRUCTION of the table S0-T001 stratified on, so its inputs have to be
#: S0-T001's inputs. Deriving them again from the vendor -- however correctly --
#: makes a second authority, and a second authority is how eight days ended up
#: with a different stratum than the run being reconstructed.
SYMBOLOGY_CSV = (Path(__file__).resolve().parents[3]
                 / "gate1" / "symbology" / "nq_v0_mapping.csv")

#: IR-13's enumerated unscheduled-FOMC dates, mirroring the constant
#: `scripts/s0_real_run.py` passes into `EventCalendar`. Duplicated here
#: DELIBERATELY and under protest: `src/` may not import `scripts/`, and the
#: formal extraction of the shared loaders is N09-v2 work. The duplication is
#: pinned by an AST drift test that reads the constant out of that script, so
#: the two cannot part company silently.
UNSCHEDULED_FOMC = ("2019-10-11", "2020-03-03", "2020-03-15", "2020-03-23")

#: Vendor per-day condition, in the authorized job dir. S0-T001 took its
#: `vendor_degraded_dates` from here; the supplement used to re-derive them as
#: "scheduled sessions with no bars", which is a DIFFERENT set.
CONDITION_JSON_NAME = "condition.json"


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
    """`EventCalendar` exactly as S0-T001 built it.

    ALL FIVE FIELDS, and the last two are the repair. They used to be left
    empty on the reasoning that "neither is a column in this table, and
    filling them by inference would put a derived set where the frozen source
    has none". That reasoning was wrong twice over: `unscheduled_fomc_dates`
    is not inferred at all -- it is IR-13's enumerated constant, which S0-T001
    passes verbatim -- and `raw_multi_event_dates` is not inferred either, it
    is read off the `event_type` column of this same frozen table.

    Leaving them empty is what made three unscheduled-FOMC days
    (independently found, not assumed here) carry a different event stratum
    than the run being reconstructed. The fix is to supply what S0 supplied,
    not to touch those days.
    """
    import csv

    from ..s0.context import EventCalendar

    cpi, nfp, fomc = set(), set(), set()
    kinds: dict = {}
    with open(csv_path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            date = row["date_et"]
            if row["is_cpi_release_day"] == "true":
                cpi.add(date)
            if row["is_nfp_release_day"] == "true":
                nfp.add(date)
            if row["is_fomc_statement_day"] == "true":
                fomc.add(date)
            kinds.setdefault(date, set()).add(row["event_type"])
    raw_multi = {d for d, k in kinds.items() if len(k) > 1}
    return EventCalendar(frozenset(cpi), frozenset(nfp), frozenset(fomc),
                         frozenset(UNSCHEDULED_FOMC), frozenset(raw_multi))


def build_session_schedule(start: str, end: str, *, bars_by_date=None,
                           job_dir=AUTHORIZED_JOB_DIR):
    """`SessionSchedule` exactly as S0-T001 built it. TWO repairs here.

    CLOSE MINUTE IS THE EXCHANGE'S, UNCAPPED. This used to cap at
    `RTH_CLOSE_MINUTE = 960` on the reasoning that a frozen L44 excluded day
    is keyed on the RTH close. S0-T001 does no such capping -- it writes the
    calendar's own `market_close` minute -- so the cap made the supplement's
    session table differ from the one being reconstructed. A cap that "can
    only ever mark MORE days early" is still a different input, and the
    supplement's job is to match, not to improve.

    DEGRADED COMES FROM THE VENDOR, NOT FROM ABSENT BARS. S0-T001 reads
    `condition.json` and takes every date whose `condition` is not
    "available". The supplement used to re-derive the set as "scheduled
    sessions carrying no bars at all", which is a different set with a
    different meaning: one is what the vendor SAYS about a day, the other is
    what our own file inventory happens to contain.

    `bars_by_date` is kept in the signature -- callers pass it -- but is no
    longer consulted for the degraded set, and the docstring says so rather
    than letting a live-looking parameter imply it still decides something.
    """
    import json

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
        close_minute[day.strftime("%Y-%m-%d")] = close.hour * 60 + close.minute

    root = verify_authorized_job_dir(job_dir)
    condition = json.loads(
        (root / CONDITION_JSON_NAME).read_text(encoding="utf-8"))
    degraded = frozenset(r["date"] for r in condition
                         if r["condition"] != "available")
    return SessionSchedule(close_minute=close_minute,
                           vendor_degraded_dates=degraded)


def build_roll_intervals(job_dir=AUTHORIZED_JOB_DIR):
    """`RollInterval`s from the FROZEN symbology mapping S0-T001 used.

    NOT re-derived from the vendor. The previous version read the DBN
    metadata live and `coalesce`d it, which is a defensible way to obtain
    roll intervals and the wrong thing to do here: the supplement
    reconstructs the table S0-T001 stratified on, and S0-T001 read
    `gate1/symbology/nq_v0_mapping.csv`. Two independently-correct
    derivations of "the rolls" are still two authorities, and roll
    transitions move vol20, which moves the tercile boundaries, which moves
    the label of any day sitting near one.

    `itsf.data.symbology` is untouched and still correct for its own purpose;
    it is simply not the supplement's source of truth.

    `job_dir` is kept in the signature because it is public API, and is no
    longer read -- the frozen CSV is a repository file.
    """
    import csv

    from ..s0.context import RollInterval

    with open(SYMBOLOGY_CSV, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("the frozen symbology mapping %s is empty"
                         % SYMBOLOGY_CSV)
    return tuple(RollInterval(r["start_date_utc"], r["end_date_utc_excl"],
                              r["raw_symbol"], int(r["instrument_id"]))
                 for r in rows)


def acquire_production_inputs(job_dir=AUTHORIZED_JOB_DIR, *,
                              source_format="dbn"):
    """The four inputs, acquired once. Returns
    `(bars_by_date, schedule, events, roll_intervals, qa_events)`."""
    bars, qa = load_bars_by_date(job_dir, source_format=source_format)
    days = sorted(bars)
    schedule = build_session_schedule(days[0], days[-1], bars_by_date=bars)
    return (bars, schedule, build_event_calendar(),
            build_roll_intervals(job_dir), qa)
