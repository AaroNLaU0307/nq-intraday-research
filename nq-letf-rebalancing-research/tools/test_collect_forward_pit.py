#!/usr/bin/env python3
"""Tests for the R2 forward PIT collector.

Every test uses a synthetic fetcher. Nothing here touches the network, and no
test reads or writes anything outside its own temporary directory.

The point of these tests is not that the happy path works. It is that each
failure mode the collector exists to preserve -- a 404, a timeout, a missing
header, a schema change, a lagging fund, malformed CSV -- is recorded as
evidence rather than swallowed.

Run:  python -m unittest discover -s tools -p "test_*.py" -v
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import shutil
import stat
import tempfile
import unittest
from pathlib import Path
from zoneinfo import ZoneInfo

import collect_forward_pit as C

UTC = _dt.timezone.utc
ET = ZoneInfo("America/New_York")

HEADER = (
    "Date,ProShares Name,Ticker,NAV,Prior NAV,NAV Change (%),NAV Change ($),"
    "Shares Outstanding (000),Assets Under Management"
)


def csv_body(ticker: str, dates: list[str], header: str = HEADER) -> bytes:
    rows = [header]
    for index, date in enumerate(dates):
        rows.append(
            f"{date},ProShares {ticker},{ticker},10.{index:04d},10.0000,"
            f"0.10,0.01,1000,10000000"
        )
    return ("\n".join(rows) + "\n").encode("utf-8")


def ok_response(
    url: str,
    body: bytes,
    *,
    last_modified: str | None = "Fri, 19 Sep 2026 01:01:01 GMT",
    etag: str | None = '"63e10-65bcb8cf5bdb5"',
    content_length: bool = True,
    http_date: str | None = "Sat, 20 Sep 2026 13:05:03 GMT",
) -> C.FetchResult:
    headers: list[tuple[str, str]] = [("Server", "Apache/2.4.37")]
    if http_date:
        headers.insert(0, ("Date", http_date))
    if last_modified:
        headers.append(("Last-Modified", last_modified))
    if etag:
        headers.append(("ETag", etag))
    if content_length:
        headers.append(("Content-Length", str(len(body))))
    headers.append(("Content-Type", "text/csv"))
    now = _dt.datetime.now(UTC)
    return C.FetchResult(
        url=url,
        attempted_utc=now,
        completed_utc=now,
        http_status=200,
        reason="OK",
        headers=headers,
        body=body,
    )


def chmod_writable(root: Path) -> None:
    for path in root.rglob("*"):
        if path.is_file():
            os.chmod(path, os.stat(path).st_mode | stat.S_IWRITE)


class CollectorTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="r2_fwd_pit_"))
        self.root = self.tmp / "data_forward_pit"

    def tearDown(self) -> None:
        chmod_writable(self.tmp)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def entries(self, manifest: dict) -> dict[str, dict]:
        return {entry["ticker"]: entry for entry in manifest["funds"]}

    # ------------------------------------------------------------------ #

    def test_happy_path_captures_everything_required(self) -> None:
        def fetcher(url: str, timeout: float) -> C.FetchResult:
            ticker = url.split("/")[-1].split("-")[0]
            return ok_response(url, csv_body(ticker, ["09/18/2026", "09/17/2026"]))

        snapshot_dir, manifest = collect_dir = C.collect(
            root=self.root, fetcher=fetcher, capture_type="TEST", set_readonly=False
        )
        del collect_dir

        self.assertTrue(manifest["summary"]["all_funds_ok"])
        self.assertEqual(manifest["summary"]["funds_attempted"], 5)

        for ticker, entry in self.entries(manifest).items():
            with self.subTest(ticker=ticker):
                # all 14 required facts present
                self.assertIsNotNone(entry["body_path"], "raw bytes")
                self.assertIsNotNone(entry["headers_path"], "raw headers")
                self.assertIsNotNone(entry["retrieved_utc"], "UTC timestamp")
                self.assertIsNotNone(entry["retrieved_et"], "ET timestamp")
                self.assertIsNotNone(entry["http_date"], "HTTP Date")
                self.assertIsNotNone(entry["last_modified"], "Last-Modified")
                self.assertIsNotNone(entry["etag"], "ETag")
                self.assertIsNotNone(entry["content_length"], "Content-Length")
                self.assertEqual(entry["latest_row_date"], "2026-09-18")
                self.assertEqual(entry["data_row_count"], 2)
                self.assertIsNotNone(entry["body_sha256"], "body hash")
                self.assertIsNotNone(entry["headers_sha256"], "headers hash")
                self.assertTrue(entry["url"].endswith(f"{ticker}-historical_nav.csv"))
                self.assertEqual(entry["http_status"], 200)
                self.assertTrue(entry["content_length_matches_body"])
                self.assertEqual(entry["parse_status"], C.PARSE_OK)
                self.assertEqual(entry["column_count"], 9)
                self.assertTrue((snapshot_dir / entry["body_path"]).exists())
                self.assertTrue((snapshot_dir / entry["headers_path"]).exists())

        ok, problems = C.verify(snapshot_dir)
        self.assertTrue(ok, problems)

    def test_http_404_is_preserved_not_swallowed(self) -> None:
        def fetcher(url: str, timeout: float) -> C.FetchResult:
            ticker = url.split("/")[-1].split("-")[0]
            if ticker == "SQQQ":
                now = _dt.datetime.now(UTC)
                return C.FetchResult(
                    url=url,
                    attempted_utc=now,
                    completed_utc=now,
                    http_status=404,
                    reason="Not Found",
                    headers=[("Date", "Sat, 20 Sep 2026 13:05:03 GMT")],
                    body=b"<html>404</html>",
                )
            return ok_response(url, csv_body(ticker, ["09/18/2026"]))

        snapshot_dir, manifest = C.collect(
            root=self.root, fetcher=fetcher, set_readonly=False
        )
        entry = self.entries(manifest)["SQQQ"]

        self.assertEqual(entry["status"], C.STATUS_HTTP_ERROR)
        self.assertEqual(entry["http_status"], 404)
        self.assertIsNotNone(entry["body_path"], "the 404 body is still evidence")
        self.assertIsNotNone(entry["headers_path"])
        self.assertFalse(manifest["summary"]["all_funds_ok"])
        self.assertEqual(manifest["summary"]["funds_failed"], 1)
        self.assertTrue(C.verify(snapshot_dir)[0])

    def test_timeout_is_recorded_as_transport_error(self) -> None:
        def fetcher(url: str, timeout: float) -> C.FetchResult:
            ticker = url.split("/")[-1].split("-")[0]
            if ticker == "QLD":
                now = _dt.datetime.now(UTC)
                return C.FetchResult(
                    url=url,
                    attempted_utc=now,
                    completed_utc=now,
                    error="ConnectTimeout: timed out after 30.0s",
                )
            return ok_response(url, csv_body(ticker, ["09/18/2026"]))

        snapshot_dir, manifest = C.collect(
            root=self.root, fetcher=fetcher, set_readonly=False
        )
        entry = self.entries(manifest)["QLD"]

        self.assertEqual(entry["status"], C.STATUS_TRANSPORT_ERROR)
        self.assertIn("ConnectTimeout", entry["transport_error"])
        self.assertIsNone(entry["http_status"])
        self.assertTrue((snapshot_dir / "QLD" / "QLD-error.txt").exists())
        self.assertFalse(manifest["summary"]["all_funds_ok"])
        self.assertTrue(C.verify(snapshot_dir)[0])

    def test_missing_last_modified_is_flagged(self) -> None:
        def fetcher(url: str, timeout: float) -> C.FetchResult:
            ticker = url.split("/")[-1].split("-")[0]
            return ok_response(
                url,
                csv_body(ticker, ["09/18/2026"]),
                last_modified=None if ticker == "PSQ" else "Fri, 19 Sep 2026 01:01:01 GMT",
            )

        _, manifest = C.collect(root=self.root, fetcher=fetcher, set_readonly=False)
        entry = self.entries(manifest)["PSQ"]

        self.assertIn("Last-Modified", entry["missing_headers"])
        self.assertIsNone(entry["last_modified_et"])
        self.assertIn("PSQ", manifest["summary"]["funds_with_missing_headers"])
        # A missing header is evidence, not a capture failure.
        self.assertEqual(entry["status"], C.STATUS_OK)

    def test_missing_etag_is_flagged(self) -> None:
        def fetcher(url: str, timeout: float) -> C.FetchResult:
            ticker = url.split("/")[-1].split("-")[0]
            return ok_response(
                url, csv_body(ticker, ["09/18/2026"]), etag=None if ticker == "QID" else '"x"'
            )

        _, manifest = C.collect(root=self.root, fetcher=fetcher, set_readonly=False)
        entry = self.entries(manifest)["QID"]
        self.assertIn("ETag", entry["missing_headers"])
        self.assertIsNone(entry["etag"])

    def test_one_lagging_fund_is_detected(self) -> None:
        def fetcher(url: str, timeout: float) -> C.FetchResult:
            ticker = url.split("/")[-1].split("-")[0]
            dates = (
                ["09/17/2026", "09/16/2026"]
                if ticker == "TQQQ"
                else ["09/18/2026", "09/17/2026"]
            )
            return ok_response(url, csv_body(ticker, dates))

        _, manifest = C.collect(root=self.root, fetcher=fetcher, set_readonly=False)

        self.assertEqual(manifest["summary"]["lagging_funds"], ["TQQQ"])
        self.assertEqual(manifest["summary"]["latest_row_date_max"], "2026-09-18")
        self.assertTrue(
            any("lags the snapshot maximum" in n for n in self.entries(manifest)["TQQQ"]["notes"])
        )

    def test_malformed_csv_is_recorded_not_rejected(self) -> None:
        broken = (
            HEADER
            + "\n09/18/2026,ProShares QLD,QLD,10.0,10.0,0.1,0.01,1000,10000000\n"
            + "this,is,not,a,valid,row\n"
            + "13/45/2026,ProShares QLD,QLD,10.0,10.0,0.1,0.01,1000,10000000\n"
        ).encode("utf-8")

        def fetcher(url: str, timeout: float) -> C.FetchResult:
            ticker = url.split("/")[-1].split("-")[0]
            if ticker == "QLD":
                return ok_response(url, broken)
            return ok_response(url, csv_body(ticker, ["09/18/2026"]))

        snapshot_dir, manifest = C.collect(
            root=self.root, fetcher=fetcher, set_readonly=False
        )
        entry = self.entries(manifest)["QLD"]

        self.assertEqual(entry["parse_status"], C.PARSE_MALFORMED)
        self.assertEqual(entry["unparsable_row_count"], 2)
        self.assertEqual(entry["latest_row_date"], "2026-09-18")
        self.assertIn("QLD", manifest["summary"]["funds_with_parse_problems"])
        # the raw bytes survive untouched
        self.assertEqual((snapshot_dir / entry["body_path"]).read_bytes(), broken)

    def test_schema_change_between_snapshots(self) -> None:
        base = _dt.datetime(2026, 9, 20, 12, 0, 0, tzinfo=UTC)

        def fetcher_v1(url: str, timeout: float) -> C.FetchResult:
            ticker = url.split("/")[-1].split("-")[0]
            return ok_response(url, csv_body(ticker, ["09/18/2026"]))

        _, first = C.collect(
            root=self.root, fetcher=fetcher_v1, now=base, set_readonly=False
        )
        self.assertEqual(first["schema_monitor"]["schema_change"], "NO_BASELINE")

        new_header = HEADER + ",Total Net Assets"

        def fetcher_v2(url: str, timeout: float) -> C.FetchResult:
            ticker = url.split("/")[-1].split("-")[0]
            body = csv_body(ticker, [], header=new_header) + (
                f"09/21/2026,ProShares {ticker},{ticker},10.0,10.0,0.1,0.01,"
                f"1000,10000000,10000000\n".encode("utf-8")
            )
            return ok_response(url, body)

        snapshot_dir, second = C.collect(
            root=self.root,
            fetcher=fetcher_v2,
            now=base + _dt.timedelta(days=1),
            set_readonly=False,
        )

        monitor = second["schema_monitor"]
        self.assertEqual(monitor["schema_change"], "YES")
        self.assertEqual(sorted(monitor["changed_funds"]), sorted(C.R2_FUNDS))
        self.assertEqual(monitor["compared_against"], first["snapshot_id"])
        self.assertEqual(self.entries(second)["QLD"]["column_count"], 10)
        # both versions preserved
        self.assertTrue((self.root / "2026-09-20").exists())
        self.assertTrue((self.root / "2026-09-21").exists())
        self.assertTrue(C.verify(snapshot_dir)[0])

    def test_same_snapshot_id_is_refused_and_prior_snapshot_untouched(self) -> None:
        base = _dt.datetime(2026, 9, 20, 12, 0, 0, tzinfo=UTC)

        def fetcher(url: str, timeout: float) -> C.FetchResult:
            ticker = url.split("/")[-1].split("-")[0]
            return ok_response(url, csv_body(ticker, ["09/18/2026"]))

        snapshot_dir, _ = C.collect(
            root=self.root, fetcher=fetcher, now=base, set_readonly=False
        )
        before = {
            p: p.read_bytes() for p in snapshot_dir.rglob("*") if p.is_file()
        }

        with self.assertRaises(FileExistsError):
            C.collect(root=self.root, fetcher=fetcher, now=base, set_readonly=False)

        after = {p: p.read_bytes() for p in snapshot_dir.rglob("*") if p.is_file()}
        self.assertEqual(before, after, "a refused re-run must not alter the snapshot")
        self.assertTrue(C.verify(snapshot_dir)[0])

    def test_rerun_at_a_new_time_leaves_earlier_snapshot_intact(self) -> None:
        base = _dt.datetime(2026, 9, 20, 12, 0, 0, tzinfo=UTC)

        def fetcher(url: str, timeout: float) -> C.FetchResult:
            ticker = url.split("/")[-1].split("-")[0]
            return ok_response(url, csv_body(ticker, ["09/18/2026"]))

        first_dir, _ = C.collect(
            root=self.root, fetcher=fetcher, now=base, set_readonly=False
        )
        digest_before = C.sha256_bytes((first_dir / "MANIFEST.sha256").read_bytes())

        second_dir, _ = C.collect(
            root=self.root,
            fetcher=fetcher,
            now=base + _dt.timedelta(hours=1),
            set_readonly=False,
        )

        self.assertNotEqual(first_dir, second_dir)
        self.assertEqual(
            digest_before, C.sha256_bytes((first_dir / "MANIFEST.sha256").read_bytes())
        )
        self.assertTrue(C.verify(first_dir)[0])
        self.assertTrue(C.verify(second_dir)[0])

    def test_verify_detects_tampering(self) -> None:
        def fetcher(url: str, timeout: float) -> C.FetchResult:
            ticker = url.split("/")[-1].split("-")[0]
            return ok_response(url, csv_body(ticker, ["09/18/2026"]))

        snapshot_dir, manifest = C.collect(
            root=self.root, fetcher=fetcher, set_readonly=False
        )
        self.assertTrue(C.verify(snapshot_dir)[0])

        target = snapshot_dir / self.entries(manifest)["QLD"]["body_path"]
        target.write_bytes(target.read_bytes() + b"tampered\n")

        ok, problems = C.verify(snapshot_dir)
        self.assertFalse(ok)
        self.assertTrue(any("hash mismatch" in p or "sha256" in p for p in problems))

    def test_timezone_conversion_is_correct_across_dst(self) -> None:
        # 2026-01-15 is EST (-05:00); 2026-07-15 is EDT (-04:00).
        for moment, expected_offset in (
            (_dt.datetime(2026, 1, 15, 18, 0, tzinfo=UTC), -5),
            (_dt.datetime(2026, 7, 15, 18, 0, tzinfo=UTC), -4),
        ):
            with self.subTest(moment=moment):
                et_iso = C.iso_et(moment)
                parsed = _dt.datetime.fromisoformat(et_iso)
                self.assertEqual(parsed.utcoffset(), _dt.timedelta(hours=expected_offset))
                self.assertEqual(parsed, moment)

    def test_retries_record_every_attempt(self) -> None:
        calls = {"n": 0}

        def fetcher(url: str, timeout: float) -> C.FetchResult:
            ticker = url.split("/")[-1].split("-")[0]
            if ticker == "PSQ":
                calls["n"] += 1
                if calls["n"] == 1:
                    now = _dt.datetime.now(UTC)
                    return C.FetchResult(
                        url=url,
                        attempted_utc=now,
                        completed_utc=now,
                        error="ConnectionError: reset",
                    )
            return ok_response(url, csv_body(ticker, ["09/18/2026"]))

        _, manifest = C.collect(
            root=self.root, fetcher=fetcher, retries=1, set_readonly=False
        )
        entry = self.entries(manifest)["PSQ"]

        self.assertEqual(entry["attempt_count"], 2)
        self.assertIn("ConnectionError", entry["attempts"][0]["error"])
        self.assertIsNone(entry["attempts"][1]["error"])
        self.assertEqual(entry["status"], C.STATUS_OK)

    def test_manifest_is_deterministic_and_sorted(self) -> None:
        def fetcher(url: str, timeout: float) -> C.FetchResult:
            ticker = url.split("/")[-1].split("-")[0]
            return ok_response(url, csv_body(ticker, ["09/18/2026"]))

        snapshot_dir, manifest = C.collect(
            root=self.root,
            fetcher=fetcher,
            funds=["TQQQ", "QLD", "PSQ", "SQQQ", "QID"],
            set_readonly=False,
        )
        self.assertEqual(
            [e["ticker"] for e in manifest["funds"]], sorted(C.R2_FUNDS)
        )
        raw = (snapshot_dir / "MANIFEST.json").read_text(encoding="utf-8")
        self.assertEqual(
            raw,
            json.dumps(json.loads(raw), indent=2, sort_keys=True, ensure_ascii=False)
            + "\n",
        )
        lines = (snapshot_dir / "MANIFEST.sha256").read_text().splitlines()
        self.assertEqual(lines, sorted(lines))

    def test_no_nq_or_research_artifacts_are_produced(self) -> None:
        def fetcher(url: str, timeout: float) -> C.FetchResult:
            ticker = url.split("/")[-1].split("-")[0]
            return ok_response(url, csv_body(ticker, ["09/18/2026"]))

        snapshot_dir, manifest = C.collect(
            root=self.root, fetcher=fetcher, set_readonly=False
        )
        blob = json.dumps(manifest).lower()
        for forbidden in ("nq", "sharpe", "pnl", "return_series", "k_t", "l_t", "tau"):
            self.assertNotIn(f'"{forbidden}"', blob)
        self.assertEqual(manifest["authority"]["R2_S1_AUTHORIZED"], "NO")
        self.assertEqual(manifest["authority"]["POST_2022_SAMPLE_TIER"], "UNASSIGNED")
        names = {p.name for p in snapshot_dir.rglob("*") if p.is_file()}
        self.assertTrue(all("nq" not in n.lower() for n in names))


if __name__ == "__main__":
    unittest.main(verbosity=2)
