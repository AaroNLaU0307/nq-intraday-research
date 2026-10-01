#!/usr/bin/env python3
"""Regression tests for the Task Scheduler action quoting.

These exist to stop ONE specific bug coming back: a project path containing a
space ("Quant trade") silently breaking the scheduled action, so the task
reports failure while producing no output at all.

The tests run real cmd.exe against a real script at a path with spaces, so they
assert the actual operating-system behaviour rather than a belief about it. A
negative control proves the OLD form genuinely fails -- a regression test that
only checks the good path would not have caught this.

Run:  python -m unittest discover -s tools -p "test_*.py" -v
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from task_action import (  # noqa: E402
    build_action_arguments,
    split_action_arguments,
    validate_action_arguments,
)

WINDOWS_ONLY = sys.platform != "win32"

PROBE_CMD = "@echo off\r\necho PROBE_OK arg1=%~1\r\nexit /b 0\r\n"


class ActionArgumentStringTestCase(unittest.TestCase):
    """Pure-string behaviour of the canonical builder and validator."""

    SCRIPT = r"C:\Users\Aaron\OneDrive\Desktop\Quant trade\proj\tools\run.cmd"
    PYTHON = r"C:\Users\Aaron\AppData\Local\Programs\Python\Python314\python.exe"

    def test_builder_produces_the_tested_shape(self) -> None:
        built = build_action_arguments(self.SCRIPT, self.PYTHON)
        self.assertEqual(
            built, f'/d /s /c ""{self.SCRIPT}" "{self.PYTHON}""'
        )
        self.assertTrue(built.startswith("/d /s /c "))
        self.assertTrue(built.endswith('""'))

    def test_validator_accepts_the_canonical_form(self) -> None:
        ok, reason = validate_action_arguments(
            build_action_arguments(self.SCRIPT, self.PYTHON)
        )
        self.assertTrue(ok, reason)

    def test_validator_rejects_the_old_broken_form(self) -> None:
        """NEGATIVE CONTROL: the exact string that shipped and failed."""
        old = f'/c "{self.SCRIPT}" "{self.PYTHON}"'
        ok, reason = validate_action_arguments(old)
        self.assertFalse(ok, "the old /c form must be rejected outright")
        self.assertIn("/d /s /c", reason)

    def test_validator_rejects_near_misses(self) -> None:
        for bad, label in (
            (f'/d /s /c "{self.SCRIPT}" "{self.PYTHON}"', "single outer quotes"),
            (f'/s /c ""{self.SCRIPT}" "{self.PYTHON}""', "missing /d"),
            (f'/d /c ""{self.SCRIPT}" "{self.PYTHON}""', "missing /s"),
            (f'/d /s /c ""{self.SCRIPT}" "{self.PYTHON}"', "unbalanced closing"),
            ("", "empty"),
        ):
            with self.subTest(label=label):
                ok, _ = validate_action_arguments(bad)
                self.assertFalse(ok, f"{label} must be rejected")

    def test_round_trip_recovers_both_paths(self) -> None:
        script, python = split_action_arguments(
            build_action_arguments(self.SCRIPT, self.PYTHON)
        )
        self.assertEqual(script, self.SCRIPT)
        self.assertEqual(python, self.PYTHON)

    def test_builder_refuses_paths_containing_quotes(self) -> None:
        with self.assertRaises(ValueError):
            build_action_arguments('C:\\bad"path\\run.cmd', self.PYTHON)


@unittest.skipIf(WINDOWS_ONLY, "cmd.exe quoting behaviour is Windows-specific")
class RealCmdExecutionTestCase(unittest.TestCase):
    """Execute real cmd.exe against a real path containing spaces."""

    def setUp(self) -> None:
        # The space in the directory name is the entire point.
        self.tmp = Path(tempfile.mkdtemp(prefix="r2 quoting test "))
        self.probe = self.tmp / "sub dir" / "probe.cmd"
        self.probe.parent.mkdir(parents=True, exist_ok=True)
        self.probe.write_text(PROBE_CMD, encoding="ascii")
        self.payload = sys.executable

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run(self, arguments: str) -> subprocess.CompletedProcess:
        # The argument string is passed to cmd.exe verbatim, exactly as Task
        # Scheduler stores and passes it.
        return subprocess.run(
            f'cmd.exe {arguments}',
            shell=False,
            capture_output=True,
            text=True,
            timeout=60,
        )

    def test_canonical_form_executes_a_spaced_path(self) -> None:
        args = build_action_arguments(str(self.probe), self.payload)
        result = self._run(args)
        self.assertEqual(
            result.returncode, 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"
        )
        self.assertIn("PROBE_OK", result.stdout)
        self.assertIn(self.payload, result.stdout, "the argument must survive intact")

    def test_old_form_fails_on_a_spaced_path(self) -> None:
        """NEGATIVE CONTROL: reproduces the shipped defect."""
        old = f'/c "{self.probe}" "{self.payload}"'
        result = self._run(old)
        self.assertNotEqual(
            result.returncode, 0, "the old form must fail on a path containing spaces"
        )
        self.assertNotIn("PROBE_OK", result.stdout)
        combined = (result.stdout + result.stderr).lower()
        self.assertIn("is not recognized", combined)

    def test_registered_task_action_is_canonical_if_task_exists(self) -> None:
        """If the live task is registered, its stored Arguments must be canonical."""
        probe = subprocess.run(
            [
                "powershell", "-NoProfile", "-Command",
                "$t = Get-ScheduledTask -TaskName 'QuantTrade-R2-ForwardPIT' "
                "-ErrorAction SilentlyContinue; "
                "if ($t) { $t.Actions[0].Arguments } else { '' }",
            ],
            capture_output=True, text=True, timeout=120,
        )
        stored = probe.stdout.strip()
        if not stored:
            self.skipTest("QuantTrade-R2-ForwardPIT is not registered on this machine")
        ok, reason = validate_action_arguments(stored)
        self.assertTrue(ok, f"registered task action is not canonical: {reason}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
