"""F10 official event-calendar extraction (M4-T1 / SA-1).

Deterministic, OFFLINE extraction of CPI / NFP (Employment Situation) / FOMC
event dates from the official BLS and Federal Reserve source files archived in
``raw/``.  Re-running this script against the same ``raw/`` bytes MUST produce a
byte-identical ``f10_events.csv``.

Sources (Level 1, official domains only -- *.bls.gov and *.federalreserve.gov):

  BLS
    raw/bls_schedule_<year>_home.htm        annual release schedule (date+time)
    raw/bls_newsrelease_archive_cpi.htm     archived CPI news releases
    raw/bls_newsrelease_archive_empsit.htm  archived Employment Situation releases
  Federal Reserve
    raw/fed_fomchistorical<year>.htm        FOMC historical materials, 2010-2020
    raw/fed_fomccalendars.htm               FOMC calendars, covers 2021
    raw/fed_statement_<yyyymmdd><s>.htm     individual FOMC statement press releases

The BLS annual schedule and the BLS news-release archive are treated as two
independent official witnesses and are cross-checked against each other; any
disagreement raises ``SourceConflict`` (a STOP condition for this task).

This script makes NO strategy computation and performs NO network access.

Scope note (frozen by the task spec, not by this script):
  * every event gets its own row -- no merging, no priority between event types
  * FOMC meeting days and FOMC statement-release days are BOTH recorded;
    ``is_fomc_statement_day`` is true only on the statement-release day.
    Which of the two enters F10 is decision D2 and is NOT decided here.
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import html
import os
import re
import sys

RAW_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw")
OUT_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "f10_events.csv")

WINDOW_START = dt.date(2010, 6, 6)
WINDOW_END = dt.date(2021, 12, 31)

FIELDNAMES = [
    "date_et",
    "event_type",
    "source_id",
    "source_sha256",
    "official_release_time_et",
    "is_fomc_statement_day",
    "is_cpi_release_day",
    "is_nfp_release_day",
]

# Sentinel used when the archived official source records a release but does not
# state its clock time.  Never guessed / never filled from memory.
NOT_ATTESTED = "NOT_ATTESTED_IN_OFFICIAL_SOURCE"

# FOMC calendar entries that the official page marks as cancelled: the meeting
# did not take place, so it is not an event day.  Listed in F10_SOURCE_LOG.md.
CANCELLED_MARKER = "(cancelled)"

MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11,
    "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}


class SourceConflict(RuntimeError):
    """Official sources disagree -- hard STOP for M4-T1 / SA-1."""


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

def sha256_of(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def read_raw(name: str) -> str:
    with open(os.path.join(RAW_DIR, name), "rb") as fh:
        return fh.read().decode("utf-8", "replace")


def strip_tags(fragment: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", fragment))).strip()


def to_24h(clock: str) -> str:
    """'2:00 p.m.' -> '14:00'.  Raises on anything unexpected."""
    m = re.match(r"^\s*(\d{1,2}):(\d{2})\s*([ap])\.?m\.?\s*$", clock.strip(), re.I)
    if not m:
        raise SourceConflict(f"unparseable clock time: {clock!r}")
    hour, minute, half = int(m.group(1)), int(m.group(2)), m.group(3).lower()
    if hour == 12:
        hour = 0
    if half == "p":
        hour += 12
    return f"{hour:02d}:{minute:02d}"


def in_window(day: dt.date) -> bool:
    return WINDOW_START <= day <= WINDOW_END


# --------------------------------------------------------------------------- #
# BLS
# --------------------------------------------------------------------------- #

# Release names are matched on the <strong> element exactly, so that
# "Employment Situation of Veterans" (an annual, unrelated release) can never be
# mistaken for the monthly "Employment Situation".
BLS_PROGRAMS = {"Consumer Price Index": "CPI", "Employment Situation": "NFP"}

_ROW_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)
_CELL_RE = re.compile(r"<td[^>]*>(.*?)</td>", re.S)
_STRONG_RE = re.compile(r"<strong>(.*?)</strong>", re.S)


def parse_bls_schedule(year: int):
    """-> {(date, kind): (time_24h, source_id)} from the annual schedule page."""
    name = f"bls_schedule_{year}_home.htm"
    doc = read_raw(name)
    source_id = name[:-4]
    out = {}
    for row in _ROW_RE.findall(doc):
        cells = _CELL_RE.findall(row)
        if len(cells) != 3:
            continue
        strong = _STRONG_RE.search(cells[2])
        if not strong:
            continue
        kind = BLS_PROGRAMS.get(strip_tags(strong.group(1)))
        if kind is None:
            continue
        day = dt.datetime.strptime(strip_tags(cells[0]), "%A, %B %d, %Y").date()
        if day.year != year:
            raise SourceConflict(f"{name}: row date {day} outside its own year")
        clock = to_24h(strip_tags(cells[1]))
        key = (day, kind)
        if key in out and out[key][0] != clock:
            raise SourceConflict(f"{name}: conflicting times for {key}")
        out[key] = (clock, source_id)
    return out


def parse_bls_archive(kind: str):
    """-> {date} of releases actually published, from the news-release archive."""
    name = {"CPI": "bls_newsrelease_archive_cpi.htm",
            "NFP": "bls_newsrelease_archive_empsit.htm"}[kind]
    prefix = {"CPI": "cpi", "NFP": "empsit"}[kind]
    doc = read_raw(name)
    pattern = re.compile(
        r"/news\.release/(?:archives|history)/" + prefix + r"_(\d{2})(\d{2})(\d{4})\.(?:htm|pdf|txt)"
    )
    days = set()
    for mm, dd, yyyy in pattern.findall(doc):
        days.add(dt.date(int(yyyy), int(mm), int(dd)))
    return days, name[:-4]


# --------------------------------------------------------------------------- #
# Federal Reserve
# --------------------------------------------------------------------------- #

_PANEL_SPLIT = re.compile(r'<div class="panel panel-default')
_H5_RE = re.compile(r"<h5[^>]*>(.*?)</h5>", re.S)
_STATEMENT_RE = re.compile(
    r'<a href="(/newsevents/press(?:releases)?/(?:monetary/)?(?:monetary)?(\d{8})([a-z]?)\.htm)"[^>]*>\s*Statement\s*</a>'
)


def parse_meeting_label(label: str):
    """'April/May 30-1 Meeting - 2013' -> ([2013-04-30, 2013-05-01], 'Meeting').

    Handles every heading form present in the archived pages:
      'March 16 Meeting - 2010'                single day
      'January 26-27 Meeting - 2010'           range within one month
      'July 31-August 1 Meeting - 2012'        explicit cross-month range
      'April/May 30-1 Meeting - 2013'          abbreviated cross-month range
      'May 9 Conference Call - 2010'           conference call
      'October 16 (unscheduled) - 2013'        unscheduled meeting
      'March 19 (notation vote) - 2020'        notation vote
      'March 17-18 (cancelled) Meeting - 2020' cancelled (caller must skip)
    """
    m = re.search(r"-\s*(\d{4})\s*$", label)
    if not m:
        raise SourceConflict(f"FOMC heading without year: {label!r}")
    year = int(m.group(1))
    head = label[: m.start()].strip().rstrip("-").strip()

    kind_bits = []
    for marker in ("Conference Call", "(unscheduled)", "(notation vote)",
                   "(cancelled)", "Meeting"):
        if marker in head:
            kind_bits.append(marker)
            head = head.replace(marker, " ")
    kind = " ".join(kind_bits) if kind_bits else "Meeting"
    head = re.sub(r"\s+", " ", head).strip()

    # 'July 31-August 1'
    m = re.match(r"^([A-Za-z]+)\s+(\d{1,2})\s*-\s*([A-Za-z]+)\s+(\d{1,2})$", head)
    if m:
        m1, d1, m2, d2 = m.group(1).lower(), int(m.group(2)), m.group(3).lower(), int(m.group(4))
        return [dt.date(year, MONTHS[m1], d1), dt.date(year, MONTHS[m2], d2)], kind

    # 'April/May 30-1'  /  'Jan/Feb 31-1'
    m = re.match(r"^([A-Za-z]+)\s*/\s*([A-Za-z]+)\s+(\d{1,2})\s*-\s*(\d{1,2})$", head)
    if m:
        m1, m2, d1, d2 = m.group(1).lower(), m.group(2).lower(), int(m.group(3)), int(m.group(4))
        return [dt.date(year, MONTHS[m1], d1), dt.date(year, MONTHS[m2], d2)], kind

    # 'January 26-27'
    m = re.match(r"^([A-Za-z]+)\s+(\d{1,2})\s*-\s*(\d{1,2})$", head)
    if m:
        mon, d1, d2 = MONTHS[m.group(1).lower()], int(m.group(2)), int(m.group(3))
        return [dt.date(year, mon, d1), dt.date(year, mon, d2)], kind

    # 'March 16'
    m = re.match(r"^([A-Za-z]+)\s+(\d{1,2})$", head)
    if m:
        return [dt.date(year, MONTHS[m.group(1).lower()], int(m.group(2)))], kind

    raise SourceConflict(f"unparseable FOMC heading: {label!r}")


def parse_fomc_historical(year: int):
    """-> list of dicts for one archived FOMC historical-materials year page."""
    name = f"fed_fomchistorical{year}.htm"
    doc = read_raw(name)
    source_id = name[:-4]
    entries = []
    for panel in _PANEL_SPLIT.split(doc)[1:]:
        h5 = _H5_RE.search(panel)
        if not h5:
            continue
        label = strip_tags(h5.group(1))
        days, kind = parse_meeting_label(label)
        stmts = _STATEMENT_RE.findall(panel)
        entries.append({
            "label": label,
            "kind": kind,
            "meeting_days": days,
            "statements": [(s[1], f"fed_statement_{s[1]}{s[2]}") for s in stmts],
            "source_id": source_id,
        })
    return entries


_CAL_YEAR_SPLIT = re.compile(r'<a id="\d+">(\d{4}) FOMC Meetings</a>')
_CAL_MEETING_SPLIT = re.compile(r'<div class="[^"]*fomc-meeting"')
_CAL_MONTH_RE = re.compile(r'fomc-meeting__month[^"]*"><strong>(.*?)</strong>', re.S)
_CAL_DATE_RE = re.compile(r'fomc-meeting__date[^"]*">(.*?)</div>', re.S)
# On the calendars page the statement is not an anchor labelled "Statement"; it
# is a "Statement:" block whose HTML link points at the press release.
_CAL_STATEMENT_RE = re.compile(
    r"<strong>Statement:</strong>.{0,400}?"
    r'<a href="/newsevents/pressreleases/monetary(\d{8})([a-z]?)\.htm">\s*HTML\s*</a>',
    re.S,
)


def parse_fomc_calendars(year: int):
    """-> list of dicts for `year` taken from the rolling FOMC calendars page."""
    name = "fed_fomccalendars.htm"
    doc = read_raw(name)
    source_id = name[:-4]

    parts = _CAL_YEAR_SPLIT.split(doc)
    block = None
    for i in range(1, len(parts), 2):
        if int(parts[i]) == year:
            block = parts[i + 1]
            break
    if block is None:
        raise SourceConflict(f"{name}: no block for {year}")

    entries = []
    for chunk in _CAL_MEETING_SPLIT.split(block)[1:]:
        mon = _CAL_MONTH_RE.search(chunk)
        day = _CAL_DATE_RE.search(chunk)
        if not mon or not day:
            continue
        label = f"{strip_tags(mon.group(1))} {strip_tags(day.group(1))} Meeting - {year}"
        # the calendar marks projection meetings with a trailing '*'
        label = label.replace("*", "")
        days, kind = parse_meeting_label(label)
        entries_stmts = [(stamp, f"fed_statement_{stamp}{suffix}")
                         for stamp, suffix in _CAL_STATEMENT_RE.findall(chunk)]
        entries.append({
            "label": label,
            "kind": kind,
            "meeting_days": days,
            "statements": entries_stmts,
            "source_id": source_id,
        })
    return entries


_RELEASE_TIME_RE = re.compile(
    r'<p class="releaseTime">\s*For release at\s*([0-9]{1,2}:[0-9]{2}\s*[ap]\.m\.)\s*(E[SD]T)', re.I
)
_ARTICLE_TIME_RE = re.compile(r'<p class="article__time">(.*?)</p>', re.S)


def parse_statement(source_id: str):
    """-> (statement_date, release_time_24h_or_sentinel) for one statement page."""
    doc = read_raw(source_id + ".htm")
    at = _ARTICLE_TIME_RE.search(doc)
    if not at:
        raise SourceConflict(f"{source_id}: no article date")
    day = dt.datetime.strptime(strip_tags(at.group(1)), "%B %d, %Y").date()

    stamped = re.search(r"(\d{8})[a-z]?$", source_id)
    if stamped:
        from_name = dt.datetime.strptime(stamped.group(1), "%Y%m%d").date()
        if from_name != day:
            raise SourceConflict(
                f"{source_id}: page date {day} != URL date {from_name}")

    rt = _RELEASE_TIME_RE.search(doc)
    clock = to_24h(rt.group(1)) if rt else NOT_ATTESTED
    return day, clock


# --------------------------------------------------------------------------- #
# assembly
# --------------------------------------------------------------------------- #

def build_rows():
    sha_cache = {}

    def sha(source_id):
        if source_id not in sha_cache:
            sha_cache[source_id] = sha256_of(os.path.join(RAW_DIR, source_id + ".htm"))
        return sha_cache[source_id]

    rows = []
    notes = {"fomc_entries": [], "conflicts": []}

    # ---- BLS: CPI and NFP ------------------------------------------------- #
    schedule = {}
    for year in range(2010, 2022):
        schedule.update(parse_bls_schedule(year))

    for kind in ("CPI", "NFP"):
        archive_days, archive_id = parse_bls_archive(kind)
        archive_days = {d for d in archive_days if 2010 <= d.year <= 2021}
        sched_days = {d for (d, k) in schedule if k == kind}
        if sched_days != archive_days:
            raise SourceConflict(
                f"{kind}: BLS annual schedule vs news-release archive disagree; "
                f"schedule-only={sorted(sched_days - archive_days)} "
                f"archive-only={sorted(archive_days - sched_days)}")

    for (day, kind), (clock, source_id) in sorted(schedule.items()):
        if not in_window(day):
            continue
        rows.append({
            "date_et": day.isoformat(),
            "event_type": kind,
            "source_id": source_id,
            "source_sha256": sha(source_id),
            "official_release_time_et": clock,
            "is_fomc_statement_day": "false",
            "is_cpi_release_day": "true" if kind == "CPI" else "false",
            "is_nfp_release_day": "true" if kind == "NFP" else "false",
        })

    # ---- Federal Reserve: FOMC ------------------------------------------- #
    entries = []
    for year in range(2010, 2021):
        entries.extend(parse_fomc_historical(year))
    entries.extend(parse_fomc_calendars(2021))

    # date -> (is_statement_day, source_id, release_time)
    fomc = {}
    for entry in entries:
        notes["fomc_entries"].append(entry)
        if CANCELLED_MARKER in entry["kind"]:
            continue  # meeting did not occur
        for day in entry["meeting_days"]:
            fomc.setdefault(day, {"stmt": False, "source_id": entry["source_id"],
                                  "time": ""})
        for stamp, stmt_id in entry["statements"]:
            stmt_day, clock = parse_statement(stmt_id)
            fomc[stmt_day] = {"stmt": True, "source_id": stmt_id, "time": clock}

    for day in sorted(fomc):
        if not in_window(day):
            continue
        rec = fomc[day]
        rows.append({
            "date_et": day.isoformat(),
            "event_type": "FOMC",
            "source_id": rec["source_id"],
            "source_sha256": sha(rec["source_id"]),
            "official_release_time_et": rec["time"],
            "is_fomc_statement_day": "true" if rec["stmt"] else "false",
            "is_cpi_release_day": "false",
            "is_nfp_release_day": "false",
        })

    rows.sort(key=lambda r: (r["date_et"], r["event_type"]))
    return rows, notes


def write_csv(rows, path=OUT_CSV):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    rows, _notes = build_rows()
    write_csv(rows)
    with open(OUT_CSV, "rb") as fh:
        digest = hashlib.sha256(fh.read()).hexdigest()
    print(f"rows={len(rows)}  csv_sha256={digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
