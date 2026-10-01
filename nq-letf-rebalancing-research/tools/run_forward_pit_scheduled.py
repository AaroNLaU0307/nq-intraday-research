#!/usr/bin/env python3
"""Scheduled wrapper around the R2 forward PIT collector.

Task Scheduler invokes THIS, not the collector directly. It adds the three things
an unattended run needs and a manual run does not:

1. a single-instance lock, so two invocations can never write at once;
2. an append-only operational log (`logs/forward_pit_scheduler.jsonl`);
3. an honest record of scheduled time versus real start time.

HONESTY RULES (both deliberate, both load-bearing)
--------------------------------------------------
* A late or catch-up run is recorded at its REAL wall-clock time. The nominal
  scheduled time is recorded alongside it, never in place of it. A run that
  happened at 16:40 because the machine was asleep at 11:00 is recorded as
  having happened at 16:40.
* A missed day is NOT reconstructed. There is no catch-up, no backfill and no
  synthesised snapshot. A day with no capture is simply MISSING_FORWARD_CAPTURE,
  and that absence is itself accurate evidence.

The operational log carries no fund values and no research calculation -- only
invocation identity, timing, exit status and snapshot identity.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import platform
import socket
import sys
import traceback
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import collect_forward_pit as C  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LOG_DIR = PROJECT_ROOT / "logs"
LOCK_NAME = ".forward_pit.lock"
CAPTURE_ONCE_NAME = ".capture_type_once"
CAPTURE_ONCE_MAX_AGE = _dt.timedelta(hours=1)
STALE_LOCK_AFTER = _dt.timedelta(hours=6)

STATUS_COMPLETED = "COMPLETED"
STATUS_COMPLETED_WITH_FAILURES = "COMPLETED_WITH_FUND_FAILURES"
STATUS_SKIPPED = "SKIPPED_ALREADY_RUNNING"
STATUS_REFUSED = "REFUSED_SNAPSHOT_EXISTS"
STATUS_ERROR = "COLLECTOR_ERROR"

EXIT_OK = 0
EXIT_FUND_FAILURE = 1
EXIT_SNAPSHOT_EXISTS = 2
EXIT_COLLECTOR_ERROR = 4


# --------------------------------------------------------------------------- #
# single-instance lock
# --------------------------------------------------------------------------- #


def _process_alive(pid: int) -> bool:
    """True if `pid` looks alive. Never signals or terminates anything."""
    if pid <= 0:
        return False
    if os.name == "nt":
        import ctypes

        # PROCESS_QUERY_LIMITED_INFORMATION; no rights that could affect the process.
        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
        if not handle:
            return False
        try:
            exit_code = ctypes.c_ulong()
            if ctypes.windll.kernel32.GetExitCodeProcess(
                handle, ctypes.byref(exit_code)
            ):
                return exit_code.value == 259  # STILL_ACTIVE
            return True
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)  # POSIX only: signal 0 tests existence without delivering
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


class LockBusy(Exception):
    """Another invocation holds the lock and is genuinely running."""

    def __init__(self, holder: dict) -> None:
        super().__init__(f"lock held by pid {holder.get('pid')}")
        self.holder = holder


class SingleInstanceLock:
    """Bounded lock. A crashed run must never block collection forever."""

    def __init__(self, path: Path, stale_after: _dt.timedelta = STALE_LOCK_AFTER):
        self.path = path
        self.stale_after = stale_after
        self.acquired = False
        self.broke_stale_lock: dict | None = None

    def __enter__(self) -> "SingleInstanceLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            {
                "pid": os.getpid(),
                "host": socket.gethostname(),
                "acquired_utc": _dt.datetime.now(_dt.timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
            }
        ).encode("utf-8")

        for _ in range(2):
            try:
                handle = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                holder = self._read_holder()
                if self._is_stale(holder):
                    self.broke_stale_lock = holder
                    try:
                        self.path.unlink()
                    except OSError:
                        pass
                    continue
                raise LockBusy(holder)
            with os.fdopen(handle, "wb") as fh:
                fh.write(payload)
            self.acquired = True
            return self
        raise LockBusy(self._read_holder())

    def __exit__(self, *exc_info) -> None:
        if self.acquired:
            try:
                self.path.unlink()
            except OSError:
                pass

    def _read_holder(self) -> dict:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

    def _is_stale(self, holder: dict) -> bool:
        pid = holder.get("pid")
        if not isinstance(pid, int) or not _process_alive(pid):
            return True
        acquired = holder.get("acquired_utc")
        if not acquired:
            return True
        try:
            when = _dt.datetime.fromisoformat(str(acquired).replace("Z", "+00:00"))
        except ValueError:
            return True
        return _dt.datetime.now(_dt.timezone.utc) - when > self.stale_after


# --------------------------------------------------------------------------- #
# scheduled-time reconstruction
# --------------------------------------------------------------------------- #


def most_recent_scheduled(now_local: _dt.datetime, hhmm: str) -> _dt.datetime:
    """The latest occurrence of `hhmm` local at or before `now_local`.

    Used only to LABEL the nominal schedule. It never alters the recorded real
    start time, and a catch-up run is never presented as punctual.
    """
    hour, _, minute = hhmm.partition(":")
    candidate = now_local.replace(
        hour=int(hour), minute=int(minute), second=0, microsecond=0
    )
    if candidate > now_local:
        candidate -= _dt.timedelta(days=1)
    return candidate


# --------------------------------------------------------------------------- #
# logging
# --------------------------------------------------------------------------- #


def append_log(log_path: Path, record: dict) -> None:
    """Append one JSON object. Never rewrites or truncates prior lines."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n"
    with open(log_path, "a", encoding="utf-8") as fh:
        fh.write(line)
        fh.flush()
        os.fsync(fh.fileno())



def consume_capture_type_once(log_dir: Path, default: str) -> str:
    """Read and DELETE a one-shot capture-type marker, if a fresh one exists.

    The installer drops this marker immediately before starting the registered
    task, so that a validation run launched through Task Scheduler is labelled
    UNATTENDED_SCHEDULER_VALIDATION rather than routine collection. It is
    one-shot by construction: the file is deleted on read, whether or not it is
    honoured, and a stale marker is ignored. A mislabelled routine capture would
    be worse than no label at all.
    """
    marker = log_dir / CAPTURE_ONCE_NAME
    if not marker.exists():
        return default
    try:
        # utf-8-sig: Windows PowerShell 5.1 `Set-Content -Encoding utf8` writes a
        # BOM, which plain utf-8 + json.loads rejects (BL-R2-01).
        payload = json.loads(marker.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        payload = {}
    finally:
        try:
            marker.unlink()
        except OSError:
            pass

    written = payload.get("written_utc")
    label = payload.get("capture_type")
    if not label or not written:
        return default
    try:
        when = _dt.datetime.fromisoformat(str(written).replace("Z", "+00:00"))
    except ValueError:
        return default
    if _dt.datetime.now(_dt.timezone.utc) - when > CAPTURE_ONCE_MAX_AGE:
        return default
    return str(label)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scheduled wrapper for the R2 forward PIT collector."
    )
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT / "data_forward_pit")
    parser.add_argument("--log-dir", type=Path, default=DEFAULT_LOG_DIR)
    parser.add_argument("--scheduled-local-time", default="11:00")
    parser.add_argument("--capture-type", default="ROUTINE_FORWARD_COLLECTION")
    parser.add_argument("--note", default=None)
    parser.add_argument("--timeout", type=float, default=C.DEFAULT_TIMEOUT)
    args = parser.parse_args(argv)

    capture_type = consume_capture_type_once(args.log_dir, args.capture_type)
    invocation_id = uuid.uuid4().hex[:16]
    started_local = _dt.datetime.now().astimezone()
    scheduled_local = most_recent_scheduled(started_local, args.scheduled_local_time)
    log_path = args.log_dir / "forward_pit_scheduler.jsonl"
    console_path = args.log_dir / "forward_pit_console.log"

    record: dict = {
        "invocation_id": invocation_id,
        "collector_version": C.COLLECTOR_VERSION,
        "wrapper": "run_forward_pit_scheduled.py",
        "host": socket.gethostname(),
        "host_timezone": str(started_local.tzinfo),
        "host_utc_offset": started_local.strftime("%z"),
        "python": platform.python_version(),
        "python_executable": sys.executable,
        "scheduled_time": scheduled_local.isoformat(),
        "scheduled_local_time_setting": args.scheduled_local_time,
        "actual_start_time": started_local.isoformat(),
        "actual_start_utc": started_local.astimezone(_dt.timezone.utc)
        .isoformat()
        .replace("+00:00", "Z"),
        "late_by_seconds": round(
            (started_local - scheduled_local).total_seconds(), 3
        ),
        "capture_type": capture_type,
        "status": None,
        "collector_exit_code": None,
        "snapshot_id": None,
        "manifest_sha256": None,
        "error_summary": None,
    }

    lines: list[str] = []

    def say(message: str) -> None:
        lines.append(message)
        print(message)

    say(f"[{invocation_id}] start {started_local.isoformat()} "
        f"(scheduled {scheduled_local.isoformat()})")

    exit_code = EXIT_OK
    try:
        with SingleInstanceLock(args.log_dir / LOCK_NAME) as lock:
            if lock.broke_stale_lock is not None:
                record["broke_stale_lock"] = lock.broke_stale_lock
                say(f"[{invocation_id}] cleared a stale lock: {lock.broke_stale_lock}")

            snapshot_dir, manifest = C.collect(
                root=args.root,
                timeout=args.timeout,
                capture_type=capture_type,
                note=args.note,
                invocation_id=invocation_id,
                scheduled_time_local=scheduled_local.isoformat(),
            )
            record["snapshot_id"] = manifest["snapshot_id"]
            record["manifest_sha256"] = C.sha256_bytes(
                (snapshot_dir / "MANIFEST.json").read_bytes()
            )
            record["funds_ok"] = manifest["summary"]["funds_ok"]
            record["funds_failed"] = manifest["summary"]["funds_failed"]
            record["schema_change"] = manifest["schema_monitor"]["schema_change"]
            record["lagging_fund_count"] = len(manifest["summary"]["lagging_funds"])
            record["trading_day_status"] = manifest["trading_day_status"]

            verified, problems = C.verify(snapshot_dir)
            record["snapshot_verified"] = verified
            if not verified:
                record["error_summary"] = "; ".join(problems[:5])

            if manifest["summary"]["all_funds_ok"] and verified:
                record["status"] = STATUS_COMPLETED
                exit_code = EXIT_OK
            else:
                record["status"] = STATUS_COMPLETED_WITH_FAILURES
                exit_code = EXIT_FUND_FAILURE
                if record["error_summary"] is None:
                    record["error_summary"] = (
                        f"{manifest['summary']['funds_failed']} fund(s) not captured "
                        "cleanly; evidence preserved in the snapshot"
                    )
            say(f"[{invocation_id}] snapshot {manifest['snapshot_id']} "
                f"funds_ok={record['funds_ok']}/5 verified={verified}")

    except LockBusy as busy:
        record["status"] = STATUS_SKIPPED
        record["error_summary"] = str(busy)
        record["lock_holder"] = busy.holder
        exit_code = EXIT_OK  # a correct skip is not a failure
        say(f"[{invocation_id}] {STATUS_SKIPPED}: {busy}")
    except FileExistsError as exc:
        record["status"] = STATUS_REFUSED
        record["error_summary"] = str(exc)
        exit_code = EXIT_SNAPSHOT_EXISTS
        say(f"[{invocation_id}] {STATUS_REFUSED}: {exc}")
    except Exception as exc:  # any collector fault must be visible, never silent
        record["status"] = STATUS_ERROR
        record["error_summary"] = f"{type(exc).__name__}: {exc}"
        record["traceback"] = traceback.format_exc(limit=8)
        exit_code = EXIT_COLLECTOR_ERROR
        say(f"[{invocation_id}] {STATUS_ERROR}: {type(exc).__name__}: {exc}")
        print(traceback.format_exc(), file=sys.stderr)

    record["collector_exit_code"] = exit_code
    record["finished_time"] = _dt.datetime.now().astimezone().isoformat()
    append_log(log_path, record)

    try:
        console_path.parent.mkdir(parents=True, exist_ok=True)
        with open(console_path, "a", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
    except OSError:
        pass

    say(f"[{invocation_id}] status={record['status']} exit={exit_code}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
