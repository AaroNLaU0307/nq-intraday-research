"""Tests for the F10 official event calendar (M4-T1 / SA-1).

Offline only: these tests read the archived raw/ files and f10_events.csv.
A socket guard asserts that the extraction path performs no network access.
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import importlib.util
import os
import re
import socket

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F10_DIR = os.path.join(REPO, "gate1", "f10_event_calendar")
RAW_DIR = os.path.join(F10_DIR, "raw")
CSV_PATH = os.path.join(F10_DIR, "f10_events.csv")
LOG_PATH = os.path.join(F10_DIR, "F10_SOURCE_LOG.md")
FRAGMENT_PATH = os.path.join(F10_DIR, "f10_evidence_registry_fragment.yaml")

EXPECTED_FIELDS = [
    "date_et",
    "event_type",
    "source_id",
    "source_sha256",
    "official_release_time_et",
    "release_time_status",     # D4a / IR-17 (approved 2026-07-29)
    "is_fomc_statement_day",
    "is_cpi_release_day",
    "is_nfp_release_day",
]

RELEASE_TIME_STATUSES = {
    "official_time_recorded",
    "official_time_unavailable_in_archived_source",
    "not_applicable_no_statement",
}

WINDOW_START = dt.date(2010, 6, 6)
WINDOW_END = dt.date(2021, 12, 31)

# Baselines from the task spec: 12 CPI and 12 NFP releases per calendar year,
# 8 FOMC statement days per calendar year.  2010 is a partial year (the frozen
# development window opens 2010-06-06), and 2019/2020 carry unscheduled FOMC
# actions.  Every deviation must also be written up in F10_SOURCE_LOG.md --
# test_deviations_are_documented enforces that.
EXPECTED_CPI = {2010: 7, **{y: 12 for y in range(2011, 2022)}}
EXPECTED_NFP = {2010: 6, **{y: 12 for y in range(2011, 2022)}}
EXPECTED_FOMC_STATEMENTS = {
    2010: 5,   # partial year (window opens 2010-06-06)
    2019: 9,   # + 2019-10-11, statement from the 2019-10-04 unscheduled meeting
    2020: 10,  # 7 scheduled (2020-03-17/18 cancelled) + 03-03, 03-15, 03-23
    **{y: 8 for y in (2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2021)},
}

# Dates that deviate from the plain 8:30 ET / 8-meetings-a-year baseline and
# therefore must be named explicitly in the source log.
DOCUMENTED_DEVIATIONS = [
    "2013-10-22",  # September Employment Situation, delayed by the shutdown
    "2013-10-30",  # September CPI, delayed by the shutdown
    "2019-10-11",  # statement from the 2019-10-04 unscheduled meeting
    "2020-03-03",  # unscheduled meeting 2020-03-02
    "2020-03-15",  # unscheduled Sunday meeting and statement
    "2020-03-23",  # notation vote
    "2020-03-17",  # cancelled meeting -- excluded from the table
    "2020-03-18",  # cancelled meeting -- excluded from the table
]

NOT_ATTESTED = "NOT_ATTESTED_IN_OFFICIAL_SOURCE"


def _load_extraction():
    spec = importlib.util.spec_from_file_location(
        "f10_extraction", os.path.join(F10_DIR, "f10_extraction.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def rows():
    with open(CSV_PATH, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


# --------------------------------------------------------------------------- #
# schema
# --------------------------------------------------------------------------- #

def test_schema_is_the_frozen_interface():
    with open(CSV_PATH, encoding="utf-8", newline="") as fh:
        header = next(csv.reader(fh))
    assert header == EXPECTED_FIELDS


def test_value_domains(rows):
    assert rows, "f10_events.csv is empty"
    for r in rows:
        day = dt.date.fromisoformat(r["date_et"])
        assert WINDOW_START <= day <= WINDOW_END, f"{day} outside frozen window"
        assert r["event_type"] in {"CPI", "NFP", "FOMC"}
        for flag in ("is_fomc_statement_day", "is_cpi_release_day", "is_nfp_release_day"):
            assert r[flag] in {"true", "false"}, f"{flag}={r[flag]!r}"
        assert re.fullmatch(r"[0-9a-f]{64}", r["source_sha256"])
        time_field = r["official_release_time_et"]
        # D4a / IR-17: the in-band sentinel is GONE — time is either a clock
        # value or NA (empty), with the gap carried by release_time_status.
        assert time_field == "" or \
            re.fullmatch(r"[0-2][0-9]:[0-5][0-9]", time_field), time_field
        status = r["release_time_status"]
        assert status in RELEASE_TIME_STATUSES, status
        if status == "official_time_recorded":
            assert time_field != ""
        else:
            assert time_field == ""


def test_d4a_unavailable_time_rows(rows):
    """IR-17: exactly the 45 FOMC 2010-2015 statement rows carry the
    official_time_unavailable status; they all keep source id + hash, and
    none of them loses its date-level FOMC identity."""
    unav = [r for r in rows
            if r["release_time_status"] ==
            "official_time_unavailable_in_archived_source"]
    assert len(unav) == 45
    for r in unav:
        assert r["event_type"] == "FOMC"
        assert r["is_fomc_statement_day"] == "true"
        assert "2010" <= r["date_et"][:4] <= "2015"
        assert r["source_id"] and re.fullmatch(r"[0-9a-f]{64}",
                                               r["source_sha256"])


def test_flags_agree_with_event_type(rows):
    for r in rows:
        kind = r["event_type"]
        assert r["is_cpi_release_day"] == ("true" if kind == "CPI" else "false")
        assert r["is_nfp_release_day"] == ("true" if kind == "NFP" else "false")
        if kind != "FOMC":
            assert r["is_fomc_statement_day"] == "false"
            # BLS releases always carry an officially stated clock time
            assert re.fullmatch(r"[0-2][0-9]:[0-5][0-9]", r["official_release_time_et"])
        else:
            # a non-statement FOMC meeting day has no release, hence no time
            if r["is_fomc_statement_day"] == "false":
                assert r["official_release_time_et"] == ""


def test_one_row_per_event_no_merging(rows):
    keys = [(r["date_et"], r["event_type"]) for r in rows]
    assert len(keys) == len(set(keys)), "duplicate (date_et, event_type) rows"


def test_rows_are_sorted(rows):
    keys = [(r["date_et"], r["event_type"]) for r in rows]
    assert keys == sorted(keys)


def test_multi_event_days_are_kept_separate(rows):
    """Same-day events must stay on separate rows (encoding is decision D1)."""
    by_day = {}
    for r in rows:
        by_day.setdefault(r["date_et"], []).append(r["event_type"])
    shared = {d: k for d, k in by_day.items() if len(k) > 1}
    assert shared, "expected at least one day carrying two event types"
    for day, kinds in shared.items():
        assert len(kinds) == len(set(kinds)), day


# --------------------------------------------------------------------------- #
# per-year counts
# --------------------------------------------------------------------------- #

def _counts(rows, predicate):
    out = {y: 0 for y in range(2010, 2022)}
    for r in rows:
        if predicate(r):
            out[int(r["date_et"][:4])] += 1
    return out


def test_cpi_counts_per_year(rows):
    assert _counts(rows, lambda r: r["event_type"] == "CPI") == EXPECTED_CPI


def test_nfp_counts_per_year(rows):
    assert _counts(rows, lambda r: r["event_type"] == "NFP") == EXPECTED_NFP


def test_fomc_statement_counts_per_year(rows):
    got = _counts(rows, lambda r: r["is_fomc_statement_day"] == "true")
    assert got == EXPECTED_FOMC_STATEMENTS


def test_deviations_are_documented():
    log = open(LOG_PATH, encoding="utf-8").read()
    for day in DOCUMENTED_DEVIATIONS:
        assert day in log, f"{day} deviates from baseline but is not in F10_SOURCE_LOG.md"


def test_cancelled_meeting_is_absent(rows):
    """The 2020-03-17/18 meeting was cancelled: it is not an event day."""
    days = {r["date_et"] for r in rows if r["event_type"] == "FOMC"}
    assert "2020-03-17" not in days
    assert "2020-03-18" not in days


# --------------------------------------------------------------------------- #
# evidence integrity
# --------------------------------------------------------------------------- #

def test_source_sha256_matches_archived_file(rows):
    cache = {}
    for r in rows:
        sid = r["source_id"]
        if sid not in cache:
            path = os.path.join(RAW_DIR, sid + ".htm")
            assert os.path.exists(path), f"missing raw file for {sid}"
            with open(path, "rb") as fh:
                cache[sid] = hashlib.sha256(fh.read()).hexdigest()
        assert r["source_sha256"] == cache[sid], sid


def test_every_source_is_in_the_registry_fragment(rows):
    fragment = open(FRAGMENT_PATH, encoding="utf-8").read()
    for sid in {r["source_id"] for r in rows}:
        assert f"  f10_{sid}:" in fragment, f"{sid} missing from registry fragment"


def test_all_sources_are_on_the_official_whitelist():
    fragment = open(FRAGMENT_PATH, encoding="utf-8").read()
    urls = re.findall(r'url:\s*"([^"]+)"', fragment)
    assert urls
    for url in urls:
        host = re.sub(r"^https?://", "", url).split("/")[0].lower()
        assert host.endswith("bls.gov") or host.endswith("federalreserve.gov"), url


# --------------------------------------------------------------------------- #
# determinism + offline
# --------------------------------------------------------------------------- #

def test_extraction_is_deterministic_and_offline(tmp_path, monkeypatch):
    """Re-running extraction on the same raw/ bytes reproduces the CSV exactly."""

    def _blocked(*args, **kwargs):
        raise AssertionError("f10_extraction attempted network access")

    monkeypatch.setattr(socket, "socket", _blocked)
    monkeypatch.setattr(socket, "create_connection", _blocked)

    module = _load_extraction()
    first, _ = module.build_rows()
    second, _ = module.build_rows()
    assert first == second

    out = tmp_path / "f10_events.csv"
    module.write_csv(first, str(out))
    assert out.read_bytes() == open(CSV_PATH, "rb").read()


def test_bls_witnesses_agree():
    """The annual schedule and the news-release archive must not disagree."""
    module = _load_extraction()
    schedule = {}
    for year in range(2010, 2022):
        schedule.update(module.parse_bls_schedule(year))
    for kind in ("CPI", "NFP"):
        archive, _ = module.parse_bls_archive(kind)
        archive = {d for d in archive if 2010 <= d.year <= 2021}
        sched = {d for (d, k) in schedule if k == kind}
        assert sched == archive, f"{kind}: official sources disagree"
