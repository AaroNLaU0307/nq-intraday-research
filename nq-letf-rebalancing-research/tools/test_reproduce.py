#!/usr/bin/env python3
"""Regression tests for tools/reproduce.py (CP-AUDIT-01 R2-G06, R2-G05).

Offline. They read the committed logs and manifests and write only to a temp dir.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import reproduce as R  # noqa: E402

CUTOFF = "2026-09-30/144521_ET"


class ReproduceRegressionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="r2-reproduce-test-"))
        self.saved = (R.TASK_XML, R.JSONL)

    def tearDown(self) -> None:
        R.TASK_XML, R.JSONL = self.saved
        shutil.rmtree(self.tmp, ignore_errors=True)

    @staticmethod
    def counts(d: dict) -> tuple:
        return d["snapshots"], d["jsonl_rows"], d["natural"], d["manual"], d["catch_ups"]

    def test_counts_do_not_depend_on_the_task_export(self) -> None:
        base = R.derive(CUTOFF)
        moved = self.tmp / "task.xml"
        text = R.TASK_XML.read_bytes().decode("utf-8-sig")
        self.assertIn("2026-09-21T11:00:00+08:00", text)
        moved.write_text(text.replace("2026-09-21T11:00:00+08:00", "2026-10-10T11:00:00+08:00"),
                         encoding="utf-8")
        R.TASK_XML = moved
        after = R.derive(CUTOFF)
        self.assertEqual(self.counts(after), self.counts(base))
        self.assertEqual(after["boundary"], "2026-09-21T11:00:00+08:00")
        self.assertNotEqual(after["export_boundary"], R.NATURAL_BOUNDARY)

    def test_missing_task_export_does_not_change_counts(self) -> None:
        base = R.derive(CUTOFF)
        R.TASK_XML = self.tmp / "absent.xml"
        self.assertEqual(self.counts(R.derive(CUTOFF)), self.counts(base))

    def test_non_completed_row_is_tolerated_and_never_natural(self) -> None:
        base = R.derive(CUTOFF)
        rows = R.JSONL.read_text(encoding="utf-8")
        fault = {
            "actual_start_utc": "2026-09-29T05:00:00.000000Z",
            "capture_type": "ROUTINE_FORWARD_COLLECTION",
            "collector_exit_code": 4,
            "error_summary": "synthetic collector fault",
            "invocation_id": "ffffffffffffffff",
            "late_by_seconds": 7200.0,
            "scheduled_time": "2026-09-29T11:00:00+08:00",
            "snapshot_id": None,
            "status": "COLLECTOR_ERROR",
        }
        copy = self.tmp / "scheduler.jsonl"
        copy.write_text(rows + json.dumps(fault) + "\n", encoding="utf-8")
        R.JSONL = copy
        after = R.derive(CUTOFF)
        self.assertEqual(after["jsonl_rows"], base["jsonl_rows"] + 1)
        self.assertEqual(after["snapshots"], base["snapshots"])
        fault_rows = [c for c in after["captures"] if c["status"] == "COLLECTOR_ERROR"]
        self.assertEqual(len(fault_rows), 1)
        self.assertFalse(fault_rows[0]["natural"])
        # D-R2-2026-10-01-02 counts every recorded invocation per slot, so the
        # 2026-09-29 slot is no longer a sole invocation: one NATURAL becomes MANUAL.
        self.assertEqual(after["natural"], base["natural"] - 1)
        self.assertEqual(after["manual"], base["manual"] + 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
