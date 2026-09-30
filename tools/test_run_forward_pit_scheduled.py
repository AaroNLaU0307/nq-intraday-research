#!/usr/bin/env python3
"""Tests for the scheduled wrapper.

All synthetic. No network, no Task Scheduler, no writes outside a temp dir.

These test the properties that make an unattended run trustworthy: that two
invocations cannot write at once, that a crashed run cannot block collection
forever, that a late run is recorded at its real time, and that the operational
log carries no fund values.

Run:  python -m unittest discover -s tools -p "test_*.py" -v
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import shutil
import stat
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import collect_forward_pit as C  # noqa: E402
import run_forward_pit_scheduled as W  # noqa: E402

UTC = _dt.timezone.utc

HEADER = (
    "Date,ProShares Name,Ticker,NAV,Prior NAV,NAV Change (%),NAV Change ($),"
    "Shares Outstanding (000),Assets Under Management"
)


def csv_body(ticker: str) -> bytes:
    return (
        HEADER
        + f"\n09/18/2026,ProShares {ticker},{ticker},10.0,10.0,0.1,0.01,1000,10000000\n"
    ).encode("utf-8")


def fake_fetch(url: str, timeout: float) -> C.FetchResult:
    ticker = url.split("/")[-1].split("-")[0]
    body = csv_body(ticker)
    now = _dt.datetime.now(UTC)
    return C.FetchResult(
        url=url,
        attempted_utc=now,
        completed_utc=now,
        http_status=200,
        reason="OK",
        headers=[
            ("Date", "Sat, 19 Sep 2026 16:51:51 GMT"),
            ("Last-Modified", "Fri, 18 Sep 2026 01:01:01 GMT"),
            ("ETag", '"abc-123"'),
            ("Content-Length", str(len(body))),
        ],
        body=body,
    )


def chmod_writable(root: Path) -> None:
    for path in root.rglob("*"):
        if path.is_file():
            os.chmod(path, os.stat(path).st_mode | stat.S_IWRITE)


class ScheduledWrapperTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="r2_sched_"))
        self.log_dir = self.tmp / "logs"
        self.root = self.tmp / "data_forward_pit"
        self._real_fetch = C.http_fetch
        C.http_fetch = fake_fetch  # the wrapper calls C.collect, which defaults to this

    def tearDown(self) -> None:
        C.http_fetch = self._real_fetch
        chmod_writable(self.tmp)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_wrapper(self, *extra: str) -> int:
        return W.main(
            [
                "--root", str(self.root),
                "--log-dir", str(self.log_dir),
                "--capture-type", "TEST",
                *extra,
            ]
        )

    def log_records(self) -> list[dict]:
        path = self.log_dir / "forward_pit_scheduler.jsonl"
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    # ------------------------------------------------------------------ #

    def test_successful_run_logs_required_fields(self) -> None:
        self.assertEqual(self.run_wrapper(), W.EXIT_OK)
        records = self.log_records()
        self.assertEqual(len(records), 1)
        record = records[0]

        for required in (
            "invocation_id",
            "scheduled_time",
            "actual_start_time",
            "collector_exit_code",
            "snapshot_id",
            "manifest_sha256",
            "error_summary",
            "host_timezone",
            "collector_version",
        ):
            self.assertIn(required, record, required)

        self.assertEqual(record["status"], W.STATUS_COMPLETED)
        self.assertEqual(record["collector_exit_code"], 0)
        self.assertIsNotNone(record["snapshot_id"])
        self.assertEqual(len(record["manifest_sha256"]), 64)
        self.assertTrue(record["snapshot_verified"])

    def test_log_contains_no_fund_values(self) -> None:
        self.run_wrapper()
        blob = (self.log_dir / "forward_pit_scheduler.jsonl").read_text(encoding="utf-8")
        for forbidden in ("10000000", "nav", "shares_outstanding", "assets_under"):
            self.assertNotIn(forbidden, blob.lower(), forbidden)

    def test_log_is_append_only_across_invocations(self) -> None:
        self.run_wrapper()
        first = (self.log_dir / "forward_pit_scheduler.jsonl").read_text(encoding="utf-8")
        self.run_wrapper()
        second = (self.log_dir / "forward_pit_scheduler.jsonl").read_text(encoding="utf-8")
        self.assertTrue(second.startswith(first), "earlier lines must be untouched")
        self.assertEqual(len(self.log_records()), 2)

    def test_second_invocation_is_skipped_while_lock_is_held(self) -> None:
        lock_path = self.log_dir / W.LOCK_NAME
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        # A live holder: this very process.
        lock_path.write_text(
            json.dumps(
                {
                    "pid": os.getpid(),
                    "host": "test",
                    "acquired_utc": _dt.datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                }
            ),
            encoding="utf-8",
        )

        exit_code = self.run_wrapper()
        record = self.log_records()[-1]

        self.assertEqual(record["status"], W.STATUS_SKIPPED)
        self.assertEqual(exit_code, W.EXIT_OK, "a correct skip is not a failure")
        self.assertIsNone(record["snapshot_id"], "nothing was written")
        self.assertFalse(self.root.exists(), "no snapshot directory was created")
        self.assertTrue(lock_path.exists(), "someone else's live lock is left alone")

    def test_stale_lock_from_a_dead_process_is_broken(self) -> None:
        lock_path = self.log_dir / W.LOCK_NAME
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_path.write_text(
            json.dumps(
                {
                    "pid": 999_999_999,  # not a live pid
                    "host": "test",
                    "acquired_utc": (
                        _dt.datetime.now(UTC) - _dt.timedelta(days=2)
                    ).isoformat().replace("+00:00", "Z"),
                }
            ),
            encoding="utf-8",
        )

        self.assertEqual(self.run_wrapper(), W.EXIT_OK)
        record = self.log_records()[-1]
        self.assertEqual(record["status"], W.STATUS_COMPLETED)
        self.assertIn("broke_stale_lock", record)
        self.assertFalse(lock_path.exists(), "lock released after the run")

    def test_lock_is_released_even_when_the_collector_raises(self) -> None:
        def boom(url: str, timeout: float) -> C.FetchResult:
            raise RuntimeError("synthetic collector fault")

        C.http_fetch = boom
        exit_code = self.run_wrapper()

        self.assertEqual(exit_code, W.EXIT_COLLECTOR_ERROR)
        record = self.log_records()[-1]
        self.assertEqual(record["status"], W.STATUS_ERROR)
        self.assertIn("synthetic collector fault", record["error_summary"])
        self.assertIn("traceback", record)
        self.assertFalse(
            (self.log_dir / W.LOCK_NAME).exists(), "no permanently stale lock"
        )

    def test_fund_failure_produces_nonzero_exit_and_keeps_the_snapshot(self) -> None:
        def one_404(url: str, timeout: float) -> C.FetchResult:
            if "SQQQ" in url:
                now = _dt.datetime.now(UTC)
                return C.FetchResult(
                    url=url,
                    attempted_utc=now,
                    completed_utc=now,
                    http_status=404,
                    reason="Not Found",
                    headers=[("Date", "Sat, 19 Sep 2026 16:51:51 GMT")],
                    body=b"404",
                )
            return fake_fetch(url, timeout)

        C.http_fetch = one_404
        exit_code = self.run_wrapper()

        self.assertEqual(exit_code, W.EXIT_FUND_FAILURE, "failure must be visible")
        record = self.log_records()[-1]
        self.assertEqual(record["status"], W.STATUS_COMPLETED_WITH_FAILURES)
        self.assertEqual(record["funds_failed"], 1)
        self.assertIsNotNone(record["snapshot_id"], "evidence is still preserved")

    def test_late_run_is_recorded_at_its_real_time(self) -> None:
        self.run_wrapper("--scheduled-local-time", "11:00")
        record = self.log_records()[-1]

        scheduled = _dt.datetime.fromisoformat(record["scheduled_time"])
        actual = _dt.datetime.fromisoformat(record["actual_start_time"])

        self.assertEqual((scheduled.hour, scheduled.minute), (11, 0))
        self.assertGreaterEqual(actual, scheduled, "scheduled time is at or before start")
        self.assertAlmostEqual(
            record["late_by_seconds"], (actual - scheduled).total_seconds(), places=1
        )
        # the real start is never replaced by the nominal schedule
        self.assertNotEqual(record["actual_start_time"], record["scheduled_time"])

    def test_most_recent_scheduled_rolls_back_a_day_before_the_hour(self) -> None:
        tz = _dt.timezone(_dt.timedelta(hours=8))
        before = _dt.datetime(2026, 9, 20, 9, 30, tzinfo=tz)
        after = _dt.datetime(2026, 9, 20, 15, 30, tzinfo=tz)

        self.assertEqual(
            W.most_recent_scheduled(before, "11:00"),
            _dt.datetime(2026, 9, 19, 11, 0, tzinfo=tz),
        )
        self.assertEqual(
            W.most_recent_scheduled(after, "11:00"),
            _dt.datetime(2026, 9, 20, 11, 0, tzinfo=tz),
        )

    def test_no_catch_up_snapshot_is_ever_fabricated(self) -> None:
        """One invocation produces exactly one snapshot, whatever the delay."""
        self.run_wrapper()
        snapshots = [p.parent for p in self.root.rglob("MANIFEST.json")]
        self.assertEqual(len(snapshots), 1)
        # and nothing is dated other than now
        manifest = json.loads((snapshots[0] / "MANIFEST.json").read_text(encoding="utf-8"))
        started = _dt.datetime.fromisoformat(
            manifest["snapshot_started_utc"].replace("Z", "+00:00")
        )
        self.assertLess(
            abs((_dt.datetime.now(UTC) - started).total_seconds()),
            120,
            "the snapshot is stamped now, never backdated to a missed day",
        )

    def test_manifest_records_schedule_and_trading_day_status(self) -> None:
        self.run_wrapper("--scheduled-local-time", "11:00")
        snapshot = [p.parent for p in self.root.rglob("MANIFEST.json")][0]
        manifest = json.loads((snapshot / "MANIFEST.json").read_text(encoding="utf-8"))

        self.assertEqual(manifest["manifest_schema_version"], 2)
        self.assertIn(manifest["trading_day_status"], ("WEEKEND", "UNKNOWN"))
        self.assertNotEqual(
            manifest["trading_day_status"],
            "TRADING_DAY",
            "TRADING_DAY is never asserted without a market calendar",
        )
        invocation = manifest["invocation"]
        self.assertIsNotNone(invocation["invocation_id"])
        self.assertIsNotNone(invocation["scheduled_time_local"])
        self.assertIsNotNone(invocation["actual_start_local"])
        self.assertIsNotNone(manifest["host_timezone"])

    def test_trading_day_status_rule(self) -> None:
        saturday = _dt.datetime(2026, 9, 19, 16, 0, tzinfo=UTC)  # Sat in ET
        monday = _dt.datetime(2026, 9, 21, 16, 0, tzinfo=UTC)  # Mon in ET
        self.assertEqual(C.trading_day_status(saturday), "WEEKEND")
        self.assertEqual(C.trading_day_status(monday), "UNKNOWN")


    # ------------------------------------------------------------------ #
    # one-shot capture label (used by the installer's validation run)
    # ------------------------------------------------------------------ #

    def _write_marker(self, label: str, age: _dt.timedelta = _dt.timedelta(0)) -> Path:
        self.log_dir.mkdir(parents=True, exist_ok=True)
        marker = self.log_dir / W.CAPTURE_ONCE_NAME
        written = (_dt.datetime.now(UTC) - age).isoformat().replace("+00:00", "Z")
        marker.write_text(
            json.dumps({"capture_type": label, "written_utc": written}), encoding="utf-8"
        )
        return marker

    def test_fresh_capture_marker_is_honoured_then_deleted(self) -> None:
        marker = self._write_marker("UNATTENDED_SCHEDULER_VALIDATION")
        self.assertEqual(self.run_wrapper(), W.EXIT_OK)

        record = self.log_records()[-1]
        self.assertEqual(record["capture_type"], "UNATTENDED_SCHEDULER_VALIDATION")
        self.assertFalse(marker.exists(), "the marker must be consumed exactly once")

        snapshot = [q.parent for q in self.root.rglob("MANIFEST.json")][0]
        manifest = json.loads((snapshot / "MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["capture_type"], "UNATTENDED_SCHEDULER_VALIDATION")

    def test_marker_is_not_reused_by_a_later_run(self) -> None:
        self._write_marker("UNATTENDED_SCHEDULER_VALIDATION")
        self.run_wrapper()
        self.run_wrapper()
        records = self.log_records()
        self.assertEqual(records[0]["capture_type"], "UNATTENDED_SCHEDULER_VALIDATION")
        self.assertEqual(
            records[1]["capture_type"],
            "TEST",
            "the second run must fall back to the ordinary capture type",
        )

    def test_stale_marker_is_ignored_and_removed(self) -> None:
        marker = self._write_marker(
            "UNATTENDED_SCHEDULER_VALIDATION", age=_dt.timedelta(hours=9)
        )
        self.assertEqual(self.run_wrapper(), W.EXIT_OK)
        record = self.log_records()[-1]
        self.assertEqual(
            record["capture_type"], "TEST", "a stale label must never be applied"
        )
        self.assertFalse(marker.exists())

    def test_corrupt_marker_is_ignored_and_removed(self) -> None:
        self.log_dir.mkdir(parents=True, exist_ok=True)
        marker = self.log_dir / W.CAPTURE_ONCE_NAME
        marker.write_text("{not json", encoding="utf-8")
        self.assertEqual(self.run_wrapper(), W.EXIT_OK)
        self.assertEqual(self.log_records()[-1]["capture_type"], "TEST")
        self.assertFalse(marker.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
