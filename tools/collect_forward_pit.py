#!/usr/bin/env python3
"""R2 forward point-in-time collector.

Captures the public ProShares/ProFunds per-fund historical NAV files for the five
R2 universe funds, preserving raw bytes, raw HTTP headers and retrieval timestamps
as immutable dated snapshots.

WHAT THIS IS
------------
Evidence infrastructure for FORWARD dates only. Each snapshot records what the
public endpoint served, and when we saw it, producing
DIRECT_CONTEMPORANEOUS_PIT_CAPTURE_EVIDENCE for future dates -- an observation
made at the time, rather than an inference drawn from an archive afterwards.

Evidence integrity rests on the immutable-snapshot convention, the manifest, the
SHA-256 digests, and the preserved raw bytes and raw headers. Filesystem
read-only attributes are an operational safeguard only; they are not, and must
not be described as, cryptographic immutability.

WHAT THIS IS NOT
----------------
It does NOT repair 2010-2021. It does NOT assign a sample tier. It is not a
research calculation, it touches no NQ data, and it computes nothing about
returns, liquidity or performance. Collection only.

DESIGN RULES (all deliberate)
-----------------------------
* Fail loudly. A fund that could not be captured is recorded as such and the
  process exits non-zero -- after the manifest is written, because preserving the
  failure IS the point.
* No silent retry. Retries default to 0; when enabled, every attempt is recorded
  so the original failure state survives.
* Never mutate a past snapshot. A snapshot id that already carries a manifest is
  refused outright.
* Atomic writes. Everything lands via a temp file plus os.replace.
* Deterministic manifest. Sorted keys, sorted fund order, stable schema version.
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import hashlib
import io
import json
import os
import platform
import stat
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Sequence
from zoneinfo import ZoneInfo

COLLECTOR_NAME = "collect_forward_pit.py"
COLLECTOR_VERSION = "1.1.0"
MANIFEST_SCHEMA_VERSION = 2

# R2 universe, per OD-2 = NDX_BENCHMARKED_DAILY_RESET_ETFS_ONLY.
R2_FUNDS: tuple[str, ...] = ("PSQ", "QID", "QLD", "SQQQ", "TQQQ")

DEFAULT_URL_TEMPLATE = (
    "https://accounts.profunds.com/etfdata/ByFund/{ticker}-historical_nav.csv"
)
DEFAULT_TIMEOUT = 30.0
USER_AGENT = f"R2-forward-pit-collector/{COLLECTOR_VERSION} (research; collection only)"

ET = ZoneInfo("America/New_York")
UTC = _dt.timezone.utc

# The nine-column schema observed since 2014. Recorded, never enforced: a change
# is evidence to preserve, not an error to correct.
EXPECTED_COLUMNS: tuple[str, ...] = (
    "Date",
    "ProShares Name",
    "Ticker",
    "NAV",
    "Prior NAV",
    "NAV Change (%)",
    "NAV Change ($)",
    "Shares Outstanding (000)",
    "Assets Under Management",
)

STATUS_OK = "OK"
STATUS_HTTP_ERROR = "HTTP_ERROR"
STATUS_TRANSPORT_ERROR = "TRANSPORT_ERROR"

PARSE_OK = "OK"
PARSE_MALFORMED = "MALFORMED"
PARSE_EMPTY = "EMPTY"
PARSE_NOT_ATTEMPTED = "NOT_ATTEMPTED"


# --------------------------------------------------------------------------- #
# transport
# --------------------------------------------------------------------------- #


@dataclass
class FetchResult:
    """One HTTP attempt. `error` set means no response was obtained at all."""

    url: str
    attempted_utc: _dt.datetime
    completed_utc: _dt.datetime
    http_status: int | None = None
    reason: str | None = None
    http_version: str = "HTTP/1.1"
    headers: list[tuple[str, str]] = field(default_factory=list)
    body: bytes | None = None
    error: str | None = None

    def header(self, name: str) -> str | None:
        lowered = name.lower()
        for key, value in self.headers:
            if key.lower() == lowered:
                return value
        return None


def http_fetch(url: str, timeout: float, session=None) -> FetchResult:
    """Real transport, standard library only.

    Deliberately `urllib` rather than `requests`: this collector runs unattended
    from Task Scheduler, and the only interpreter on this machine carrying
    `requests` is a zero-length Windows Store app-execution alias (a reparse
    point), which is not a dependable target for a scheduled task. A stdlib-only
    transport runs under any interpreter and needs no environment changes.

    An HTTP error response is NOT an exception here -- it is evidence, so its
    status, headers and body are captured exactly like a success.
    """
    import urllib.error
    import urllib.request

    del session  # kept for signature compatibility with injected test fetchers

    started = _dt.datetime.now(UTC)
    request = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "text/csv, */*"}
    )
    try:
        response = urllib.request.urlopen(request, timeout=timeout)
    except urllib.error.HTTPError as exc:
        response = exc  # HTTPError is itself a readable response object
    except Exception as exc:  # deliberately broad: any transport failure is evidence
        return FetchResult(
            url=url,
            attempted_utc=started,
            completed_utc=_dt.datetime.now(UTC),
            error=f"{type(exc).__name__}: {exc}",
        )

    try:
        body = response.read()
    except Exception as exc:
        return FetchResult(
            url=url,
            attempted_utc=started,
            completed_utc=_dt.datetime.now(UTC),
            http_status=getattr(response, "status", None),
            error=f"body read failed: {type(exc).__name__}: {exc}",
        )
    finally:
        try:
            response.close()
        except Exception:
            pass

    http_version = {10: "HTTP/1.0", 11: "HTTP/1.1"}.get(
        getattr(response, "version", 11), "HTTP/1.1"
    )
    return FetchResult(
        url=url,
        attempted_utc=started,
        completed_utc=_dt.datetime.now(UTC),
        http_status=getattr(response, "status", None),
        reason=getattr(response, "reason", "") or "",
        http_version=http_version,
        headers=list(response.headers.items()),
        body=body,
    )


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def render_headers(result: FetchResult) -> bytes:
    """Reconstruct the raw response head, matching the project's prior probes."""
    lines = [f"{result.http_version} {result.http_status} {result.reason or ''}".rstrip()]
    lines.extend(f"{key}: {value}" for key, value in result.headers)
    return ("\r\n".join(lines) + "\r\n\r\n").encode("utf-8")


def parse_http_date(value: str | None) -> _dt.datetime | None:
    """RFC 7231 IMF-fixdate -> aware UTC datetime. None on anything unexpected."""
    if not value:
        return None
    for fmt in ("%a, %d %b %Y %H:%M:%S %Z", "%a, %d %b %Y %H:%M:%S"):
        try:
            parsed = _dt.datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
        return parsed.replace(tzinfo=UTC)
    return None


def iso_utc(moment: _dt.datetime | None) -> str | None:
    if moment is None:
        return None
    return moment.astimezone(UTC).isoformat().replace("+00:00", "Z")


def iso_et(moment: _dt.datetime | None) -> str | None:
    if moment is None:
        return None
    return moment.astimezone(ET).isoformat()


def parse_csv_body(body: bytes) -> dict:
    """Extract schema and date-extent facts. Never raises on malformed input."""
    out: dict = {
        "columns": None,
        "column_count": None,
        "data_row_count": None,
        "latest_row_date": None,
        "oldest_row_date": None,
        "unparsable_row_count": None,
        "parse_status": PARSE_NOT_ATTEMPTED,
        "parse_notes": [],
    }
    if body is None:
        return out

    try:
        text = body.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = body.decode("latin-1")
        out["parse_notes"].append("body was not valid UTF-8; decoded as latin-1")

    rows = list(csv.reader(io.StringIO(text)))
    rows = [row for row in rows if any(cell.strip() for cell in row)]
    if not rows:
        out["parse_status"] = PARSE_EMPTY
        out["parse_notes"].append("no non-empty rows")
        return out

    header = [cell.strip() for cell in rows[0]]
    out["columns"] = header
    out["column_count"] = len(header)

    data_rows = rows[1:]
    out["data_row_count"] = len(data_rows)

    dates: list[_dt.date] = []
    unparsable = 0
    for row in data_rows:
        if len(row) != len(header):
            unparsable += 1
            continue
        try:
            dates.append(_dt.datetime.strptime(row[0].strip(), "%m/%d/%Y").date())
        except ValueError:
            unparsable += 1

    out["unparsable_row_count"] = unparsable
    if dates:
        out["latest_row_date"] = max(dates).isoformat()
        out["oldest_row_date"] = min(dates).isoformat()

    if not data_rows:
        out["parse_status"] = PARSE_EMPTY
        out["parse_notes"].append("header present, no data rows")
    elif unparsable:
        out["parse_status"] = PARSE_MALFORMED
        out["parse_notes"].append(f"{unparsable} row(s) unparsable")
    else:
        out["parse_status"] = PARSE_OK

    if header != list(EXPECTED_COLUMNS):
        out["parse_notes"].append("columns differ from the recorded 9-column schema")
    return out


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def make_readonly(path: Path) -> bool:
    """Best-effort immutability marker. Hash verification is the real check."""
    try:
        mode = os.stat(path).st_mode
        os.chmod(path, mode & ~stat.S_IWRITE & ~stat.S_IWGRP & ~stat.S_IWOTH)
        return True
    except OSError:
        return False


def iter_snapshot_files(snapshot_dir: Path) -> Iterable[Path]:
    for path in sorted(snapshot_dir.rglob("*")):
        if path.is_file() and path.name != "MANIFEST.sha256":
            yield path


# --------------------------------------------------------------------------- #
# schema comparison against the previous snapshot
# --------------------------------------------------------------------------- #


def find_previous_snapshot(root: Path, current: Path) -> Path | None:
    """Most recent snapshot directory before `current`, by sorted path order."""
    candidates = sorted(
        p.parent for p in root.rglob("MANIFEST.json") if p.parent != current
    )
    prior = [p for p in candidates if str(p) < str(current)]
    return prior[-1] if prior else (candidates[-1] if candidates else None)


def compare_schema(previous_manifest: dict | None, funds: Sequence[dict]) -> dict:
    result: dict = {
        "schema_change": "NO",
        "compared_against": None,
        "changed_funds": [],
        "detail": [],
    }
    if not previous_manifest:
        result["schema_change"] = "NO_BASELINE"
        result["detail"].append("no earlier snapshot to compare against")
        return result

    result["compared_against"] = previous_manifest.get("snapshot_id")
    prior_cols = {
        entry["ticker"]: entry.get("columns")
        for entry in previous_manifest.get("funds", [])
    }
    for entry in funds:
        ticker = entry["ticker"]
        before, after = prior_cols.get(ticker), entry.get("columns")
        if before is None or after is None:
            continue
        if before != after:
            result["changed_funds"].append(ticker)
            result["detail"].append(
                f"{ticker}: columns changed from {before} to {after}"
            )
    if result["changed_funds"]:
        result["schema_change"] = "YES"
    return result



# --------------------------------------------------------------------------- #
# trading-day status -- deliberately conservative
# --------------------------------------------------------------------------- #

TRADING_DAY_RULE = (
    "WEEKEND when the US Eastern date is Saturday or Sunday; otherwise UNKNOWN. "
    "A weekday may still be a US market holiday, and this collector takes no "
    "market-calendar dependency -- inability to identify a holiday must never "
    "prevent or qualify a capture. TRADING_DAY is therefore never asserted here."
)


def trading_day_status(moment: _dt.datetime) -> str:
    """Only what can be determined safely without a market calendar."""
    return "WEEKEND" if moment.astimezone(ET).weekday() >= 5 else "UNKNOWN"


# --------------------------------------------------------------------------- #
# collection
# --------------------------------------------------------------------------- #


def collect(
    root: Path,
    funds: Sequence[str] = R2_FUNDS,
    url_template: str = DEFAULT_URL_TEMPLATE,
    timeout: float = DEFAULT_TIMEOUT,
    retries: int = 0,
    capture_type: str = "ROUTINE_FORWARD_COLLECTION",
    note: str | None = None,
    fetcher: Callable[..., FetchResult] | None = None,
    now: _dt.datetime | None = None,
    set_readonly: bool = True,
    invocation_id: str | None = None,
    scheduled_time_local: str | None = None,
) -> tuple[Path, dict]:
    """Take one snapshot. Returns (snapshot_dir, manifest).

    `fetcher` is resolved HERE rather than bound as a default argument, so that
    the transport is looked up on the module at call time. A default-argument
    binding would silently ignore an injected or patched fetcher and send a test
    to the live endpoint.
    """
    fetch = fetcher if fetcher is not None else http_fetch
    started = (now or _dt.datetime.now(UTC)).astimezone(UTC)
    started_et = started.astimezone(ET)
    snapshot_id = f"{started_et:%Y-%m-%d}/{started_et:%H%M%S}_ET"
    snapshot_dir = root / f"{started_et:%Y-%m-%d}" / f"{started_et:%H%M%S}_ET"

    if (snapshot_dir / "MANIFEST.json").exists():
        raise FileExistsError(
            f"snapshot {snapshot_id} already has a MANIFEST.json; "
            "past snapshots are never mutated"
        )

    fund_entries: list[dict] = []
    for ticker in sorted(funds):
        url = url_template.format(ticker=ticker)
        attempts: list[dict] = []
        result: FetchResult | None = None
        for attempt_index in range(retries + 1):
            result = fetch(url, timeout)
            attempts.append(
                {
                    "attempt": attempt_index + 1,
                    "attempted_utc": iso_utc(result.attempted_utc),
                    "completed_utc": iso_utc(result.completed_utc),
                    "http_status": result.http_status,
                    "error": result.error,
                }
            )
            if result.error is None and result.http_status == 200:
                break

        assert result is not None
        fund_dir = snapshot_dir / ticker
        entry: dict = {
            "ticker": ticker,
            "url": url,
            "attempts": attempts,
            "attempt_count": len(attempts),
            "retrieved_utc": iso_utc(result.completed_utc),
            "retrieved_et": iso_et(result.completed_utc),
            "http_status": result.http_status,
            "transport_error": result.error,
            "body_path": None,
            "body_bytes": None,
            "body_sha256": None,
            "headers_path": None,
            "headers_sha256": None,
            "http_date": None,
            "http_date_utc": None,
            "http_date_et": None,
            "last_modified": None,
            "last_modified_utc": None,
            "last_modified_et": None,
            "etag": None,
            "content_length": None,
            "content_length_matches_body": None,
            "columns": None,
            "column_count": None,
            "data_row_count": None,
            "latest_row_date": None,
            "oldest_row_date": None,
            "unparsable_row_count": None,
            "parse_status": PARSE_NOT_ATTEMPTED,
            "parse_notes": [],
            "missing_headers": [],
            "status": STATUS_OK,
            "notes": [],
        }

        if result.error is not None:
            entry["status"] = STATUS_TRANSPORT_ERROR
            entry["notes"].append("no HTTP response obtained; transport failed")
            atomic_write(fund_dir / f"{ticker}-error.txt", result.error.encode("utf-8"))
        else:
            headers_blob = render_headers(result)
            headers_path = fund_dir / f"{ticker}-http-response-headers.txt"
            atomic_write(headers_path, headers_blob)
            entry["headers_path"] = str(headers_path.relative_to(snapshot_dir)).replace(
                "\\", "/"
            )
            entry["headers_sha256"] = sha256_bytes(headers_blob)

            entry["http_date"] = result.header("Date")
            entry["last_modified"] = result.header("Last-Modified")
            entry["etag"] = result.header("ETag")
            raw_length = result.header("Content-Length")
            entry["content_length"] = int(raw_length) if raw_length else None

            http_date = parse_http_date(entry["http_date"])
            entry["http_date_utc"] = iso_utc(http_date)
            entry["http_date_et"] = iso_et(http_date)
            last_modified = parse_http_date(entry["last_modified"])
            entry["last_modified_utc"] = iso_utc(last_modified)
            entry["last_modified_et"] = iso_et(last_modified)

            for header_name, value in (
                ("Date", entry["http_date"]),
                ("Last-Modified", entry["last_modified"]),
                ("ETag", entry["etag"]),
                ("Content-Length", entry["content_length"]),
            ):
                if value is None:
                    entry["missing_headers"].append(header_name)

            if result.body is not None:
                body_path = fund_dir / f"{ticker}-historical_nav.csv"
                atomic_write(body_path, result.body)
                entry["body_path"] = str(
                    body_path.relative_to(snapshot_dir)
                ).replace("\\", "/")
                entry["body_bytes"] = len(result.body)
                entry["body_sha256"] = sha256_bytes(result.body)
                if entry["content_length"] is not None:
                    entry["content_length_matches_body"] = entry[
                        "content_length"
                    ] == len(result.body)

            if result.http_status != 200:
                entry["status"] = STATUS_HTTP_ERROR
                entry["notes"].append(
                    f"non-200 response preserved (HTTP {result.http_status})"
                )
            elif result.body is not None:
                entry.update(parse_csv_body(result.body))

            if entry["missing_headers"]:
                entry["notes"].append(
                    "missing response header(s): "
                    + ", ".join(entry["missing_headers"])
                )

        fund_entries.append(entry)

    # Lagging-fund detection: a collection-side evidence flag, not a calculation.
    latest_dates = [
        entry["latest_row_date"] for entry in fund_entries if entry["latest_row_date"]
    ]
    newest = max(latest_dates) if latest_dates else None
    lagging = sorted(
        entry["ticker"]
        for entry in fund_entries
        if entry["latest_row_date"] and newest and entry["latest_row_date"] < newest
    )
    for entry in fund_entries:
        if entry["ticker"] in lagging:
            entry["notes"].append(
                f"latest_row_date {entry['latest_row_date']} lags the snapshot "
                f"maximum {newest}"
            )

    previous_dir = find_previous_snapshot(root, snapshot_dir)
    previous_manifest = None
    if previous_dir is not None:
        try:
            previous_manifest = json.loads(
                (previous_dir / "MANIFEST.json").read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError):
            previous_manifest = None

    ok_count = sum(1 for e in fund_entries if e["status"] == STATUS_OK)
    finished = _dt.datetime.now(UTC) if now is None else started

    manifest = {
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "lineage": "R2",
        "project": "nq-letf-rebalancing-research",
        "snapshot_id": snapshot_id,
        "capture_type": capture_type,
        "note": note,
        "purpose": (
            "Forward point-in-time evidence collection. Records what the public "
            "ProShares endpoint served and when we saw it. Does NOT repair "
            "2010-2021, does NOT assign a sample tier, is NOT a research "
            "observation."
        ),
        "authority": {
            "OD-2": "NDX_BENCHMARKED_DAILY_RESET_ETFS_ONLY",
            "OD-5": "PATH_A_TRUE_PIT_DAILY",
            "OD-6": "PROVEN_PUBLICATION_ONLY_ZERO_CARRY",
            "R2_S1_AUTHORIZED": "NO",
            "POST_2022_SAMPLE_TIER": "UNASSIGNED",
        },
        "collector": {
            "name": COLLECTOR_NAME,
            "version": COLLECTOR_VERSION,
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "endpoint_url_template": url_template,
        "timeout_seconds": timeout,
        "retries_configured": retries,
        "snapshot_started_utc": iso_utc(started),
        "snapshot_started_et": iso_et(started),
        "snapshot_started_local": started.astimezone().isoformat(),
        "snapshot_finished_utc": iso_utc(finished),
        "host_timezone": str(_dt.datetime.now().astimezone().tzinfo),
        "host_utc_offset": started.astimezone().strftime("%z"),
        "trading_day_status": trading_day_status(started),
        "trading_day_status_rule": TRADING_DAY_RULE,
        "invocation": {
            "invocation_id": invocation_id,
            "scheduled_time_local": scheduled_time_local,
            "actual_start_local": started.astimezone().isoformat(),
            "actual_start_utc": iso_utc(started),
            "note": (
                "actual_start is the real wall clock at which this run began. A "
                "late or catch-up run is recorded at its true time and is never "
                "presented as having occurred at the scheduled time."
            ),
        },
        "expected_columns": list(EXPECTED_COLUMNS),
        "funds": fund_entries,
        "schema_monitor": compare_schema(previous_manifest, fund_entries),
        "summary": {
            "funds_attempted": len(fund_entries),
            "funds_ok": ok_count,
            "funds_failed": len(fund_entries) - ok_count,
            "all_funds_ok": ok_count == len(fund_entries),
            "latest_row_date_max": newest,
            "lagging_funds": lagging,
            "funds_with_missing_headers": sorted(
                e["ticker"] for e in fund_entries if e["missing_headers"]
            ),
            "funds_with_parse_problems": sorted(
                e["ticker"]
                for e in fund_entries
                if e["parse_status"] in (PARSE_MALFORMED, PARSE_EMPTY)
            ),
        },
    }

    manifest_blob = (
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")
    atomic_write(snapshot_dir / "MANIFEST.json", manifest_blob)

    checksum_lines = []
    for path in iter_snapshot_files(snapshot_dir):
        rel = str(path.relative_to(snapshot_dir)).replace("\\", "/")
        checksum_lines.append(f"{sha256_bytes(path.read_bytes())}  {rel}")
    atomic_write(
        snapshot_dir / "MANIFEST.sha256",
        ("\n".join(sorted(checksum_lines)) + "\n").encode("utf-8"),
    )

    if set_readonly:
        for path in sorted(snapshot_dir.rglob("*")):
            if path.is_file():
                make_readonly(path)

    return snapshot_dir, manifest


# --------------------------------------------------------------------------- #
# verification
# --------------------------------------------------------------------------- #


def verify(snapshot_dir: Path) -> tuple[bool, list[str]]:
    """Re-derive every hash and cross-check the manifest against the files."""
    problems: list[str] = []
    manifest_path = snapshot_dir / "MANIFEST.json"
    checksum_path = snapshot_dir / "MANIFEST.sha256"

    if not manifest_path.exists():
        return False, [f"missing {manifest_path}"]
    if not checksum_path.exists():
        return False, [f"missing {checksum_path}"]

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    recorded: dict[str, str] = {}
    for line in checksum_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, _, rel = line.partition("  ")
        recorded[rel] = digest

    on_disk = {
        str(p.relative_to(snapshot_dir)).replace("\\", "/")
        for p in iter_snapshot_files(snapshot_dir)
    }
    for missing in sorted(on_disk - set(recorded)):
        problems.append(f"file present but absent from MANIFEST.sha256: {missing}")
    for vanished in sorted(set(recorded) - on_disk):
        problems.append(f"MANIFEST.sha256 references a missing file: {vanished}")

    for rel, digest in sorted(recorded.items()):
        path = snapshot_dir / rel
        if not path.exists():
            continue
        actual = sha256_bytes(path.read_bytes())
        if actual != digest:
            problems.append(f"hash mismatch for {rel}: {actual} != {digest}")

    for entry in manifest.get("funds", []):
        ticker = entry["ticker"]
        for kind, rel_key, hash_key in (
            ("body", "body_path", "body_sha256"),
            ("headers", "headers_path", "headers_sha256"),
        ):
            rel = entry.get(rel_key)
            if rel is None:
                continue
            path = snapshot_dir / rel
            if not path.exists():
                problems.append(f"{ticker}: manifest {kind} path missing on disk: {rel}")
                continue
            actual = sha256_bytes(path.read_bytes())
            if actual != entry.get(hash_key):
                problems.append(f"{ticker}: {kind} sha256 does not reproduce")

        for key in ("retrieved_utc", "retrieved_et"):
            value = entry.get(key)
            if value is None:
                problems.append(f"{ticker}: {key} is null")
                continue
            try:
                parsed = _dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                problems.append(f"{ticker}: {key} does not parse: {value!r}")
                continue
            if parsed.tzinfo is None:
                problems.append(f"{ticker}: {key} is not timezone-aware")

        utc_value, et_value = entry.get("retrieved_utc"), entry.get("retrieved_et")
        if utc_value and et_value:
            utc_moment = _dt.datetime.fromisoformat(utc_value.replace("Z", "+00:00"))
            et_moment = _dt.datetime.fromisoformat(et_value)
            if utc_moment != et_moment:
                problems.append(f"{ticker}: UTC and ET timestamps are not the same instant")
            if et_moment.utcoffset() != utc_moment.astimezone(ET).utcoffset():
                problems.append(f"{ticker}: ET offset is wrong for that date")

    return (not problems), problems


# --------------------------------------------------------------------------- #
# cli
# --------------------------------------------------------------------------- #


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="R2 forward point-in-time collector (collection only; no research).",
    )
    default_root = Path(__file__).resolve().parent.parent / "data_forward_pit"
    parser.add_argument("--root", type=Path, default=default_root)
    parser.add_argument("--funds", nargs="+", default=list(R2_FUNDS))
    parser.add_argument("--url-template", default=DEFAULT_URL_TEMPLATE)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument(
        "--retries",
        type=int,
        default=0,
        help="extra attempts per fund; default 0 so an original failure is never hidden",
    )
    parser.add_argument("--capture-type", default="ROUTINE_FORWARD_COLLECTION")
    parser.add_argument("--note", default=None)
    parser.add_argument("--invocation-id", default=None)
    parser.add_argument(
        "--scheduled-time-local",
        default=None,
        help="nominal scheduled wall-clock time; recorded alongside the REAL start",
    )
    parser.add_argument("--no-readonly", action="store_true")
    parser.add_argument(
        "--verify",
        type=Path,
        default=None,
        metavar="SNAPSHOT_DIR",
        help="verify an existing snapshot instead of collecting",
    )
    args = parser.parse_args(argv)

    if args.verify is not None:
        ok, problems = verify(args.verify)
        for problem in problems:
            print(f"FAIL  {problem}")
        print(f"VERIFY {'PASS' if ok else 'FAIL'}  {args.verify}")
        return 0 if ok else 1

    try:
        snapshot_dir, manifest = collect(
            root=args.root,
            funds=args.funds,
            url_template=args.url_template,
            timeout=args.timeout,
            retries=args.retries,
            capture_type=args.capture_type,
            note=args.note,
            set_readonly=not args.no_readonly,
            invocation_id=args.invocation_id,
            scheduled_time_local=args.scheduled_time_local,
        )
    except FileExistsError as exc:
        print(f"REFUSED  {exc}")
        return 2

    summary = manifest["summary"]
    print(f"SNAPSHOT   {manifest['snapshot_id']}")
    print(f"DIRECTORY  {snapshot_dir}")
    print(f"CAPTURE    {manifest['capture_type']}")
    for entry in manifest["funds"]:
        print(
            f"  {entry['ticker']:<5} {entry['status']:<16} "
            f"http={entry['http_status']} rows={entry['data_row_count']} "
            f"latest={entry['latest_row_date']} "
            f"last_modified_et={entry['last_modified_et']}"
        )
    print(f"SCHEMA_CHANGE = {manifest['schema_monitor']['schema_change']}")
    print(f"LAGGING_FUNDS = {summary['lagging_funds'] or 'none'}")
    print(f"FUNDS_OK      = {summary['funds_ok']}/{summary['funds_attempted']}")

    ok, problems = verify(snapshot_dir)
    for problem in problems:
        print(f"VERIFY_FAIL  {problem}")
    print(f"VERIFY        {'PASS' if ok else 'FAIL'}")

    if not summary["all_funds_ok"]:
        print("EXIT 1: at least one fund was not captured cleanly (evidence preserved)")
        return 1
    if not ok:
        print("EXIT 1: snapshot failed self-verification")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
