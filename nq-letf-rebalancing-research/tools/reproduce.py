"""R2 reproduce command -- re-derives the checkpoint evidence from the repository.

    python tools/reproduce.py

Offline. No network, no NQ archive, no fund values, no research calculation.
It:

  1. runs the offline test suite (pytest over tools/);
  2. runs the collector's --verify over every snapshot under data_forward_pit/;
  3. derives the forward-collection counts from logs/ and the snapshot
     manifests, using the capture-origin rule adopted under delegate decision
     D-R2-2026-10-01-02 (see NATURAL below);
  4. checks that every relative link in the project's *.md files resolves;
  5. compares the derived counts with the values written in PROJECT_STATE.md;

prints a summary, and exits non-zero on any failure.

Counts are taken AS OF the snapshot named by COUNTS_AS_OF_SNAPSHOT in
PROJECT_STATE.md, so captures the scheduled task makes after a checkpoint do
not break reproduction of that checkpoint. Later captures are reported as an
informational line only.

NATURAL (trigger-fired) capture = a JSONL row whose invocation has a
"==== task start" block in logs/forward_pit_task_stdout.log AND
capture_type == ROUTINE_FORWARD_COLLECTION AND scheduled_time >= the literal
StartBoundary 2026-09-21T11:00:00+08:00 adopted by D-R2-2026-10-01-02 AND it is
the only recorded invocation for its scheduled slot. Every other snapshot is
MANUAL. The boundary is pinned, not read from ops/R2_FORWARD_PIT_TASK.xml: the
installer rewrites that export on every registration, which would move the
counts without new evidence (CP-AUDIT-01 R2-G06). The export is still read, only
to print a labelled WARN when its StartBoundary differs from the pinned value.
Rows that are not COMPLETED (fault, skip) count as JSONL rows and in the
per-slot tally, never as NATURAL (R2-G05).
The raw "task start" block count is printed for information only: the .cmd
wrapper writes that block on every invocation, manual or scheduled, so it does
not separate the two.
"""

from __future__ import annotations

import datetime as _dt
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

PROJ = Path(__file__).resolve().parent.parent
TOOLS = PROJ / "tools"
SNAP_ROOT = PROJ / "data_forward_pit"
JSONL = PROJ / "logs" / "forward_pit_scheduler.jsonl"
STDOUT_LOG = PROJ / "logs" / "forward_pit_task_stdout.log"
TASK_XML = PROJ / "ops" / "R2_FORWARD_PIT_TASK.xml"
STATE = PROJ / "PROJECT_STATE.md"

ROUTINE = "ROUTINE_FORWARD_COLLECTION"
# D-R2-2026-10-01-02 (X2), pinned per D-R2-2026-10-02-01 R2-a.
NATURAL_BOUNDARY = _dt.datetime.fromisoformat("2026-09-21T11:00:00+08:00")
CATCH_UP_THRESHOLD_S = 300  # on-time firings start within seconds of the slot

# key in PROJECT_STATE.md -> key in the derived counts
STATE_KEYS = {
    "SNAPSHOTS": "snapshots",
    "JSONL_ROWS": "jsonl_rows",
    "NATURAL_CAPTURES": "natural",
    "MANUAL_CAPTURES": "manual",
    "CATCH_UPS": "catch_ups",
    "SNAPSHOTS_VERIFIED": "verified",
}


def _utc(value: str) -> _dt.datetime:
    return _dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def run_tests() -> tuple[bool, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", str(TOOLS), "-q", "-p", "no:cacheprovider"],
        cwd=PROJ, capture_output=True, text=True,
    )
    lines = [ln for ln in proc.stdout.strip().splitlines() if ln.strip()]
    tail = lines[-1] if lines else proc.stderr.strip()[-200:]
    return proc.returncode == 0, tail.strip("= ")


def snapshot_dirs() -> list[Path]:
    return sorted(p.parent for p in SNAP_ROOT.glob("*/*/MANIFEST.json"))


def snapshot_id(d: Path) -> str:
    return f"{d.parent.name}/{d.name}"


def verify_snapshots(dirs: list[Path]) -> tuple[int, list[str]]:
    failed = []
    for d in dirs:
        proc = subprocess.run(
            [sys.executable, str(TOOLS / "collect_forward_pit.py"), "--verify", str(d)],
            cwd=PROJ, capture_output=True, text=True,
        )
        if proc.returncode != 0 or "VERIFY PASS" not in proc.stdout:
            failed.append(snapshot_id(d))
    return len(dirs) - len(failed), failed


def task_start_invocations() -> tuple[int, set[str]]:
    """Invocation ids printed inside a '==== task start' block, and the block count."""
    blocks, ids, inside = 0, set(), False
    for line in STDOUT_LOG.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("==== task start"):
            blocks, inside = blocks + 1, True
        elif line.startswith("==== task end"):
            inside = False
        elif inside:
            m = re.match(r"\[([0-9a-f]{16})\] start ", line)
            if m:
                ids.add(m.group(1))
    return blocks, ids


def trigger_start_boundary() -> _dt.datetime:
    # The export declares UTF-16 but its bytes may be UTF-8 (with BOM): decode by
    # BOM, then drop the declaration so the parser does not re-apply it.
    raw = TASK_XML.read_bytes()
    text = raw.decode("utf-16") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8-sig")
    root = ET.fromstring(re.sub(r"^<\?xml[^>]*\?>", "", text.lstrip()))
    ns = {"t": "http://schemas.microsoft.com/windows/2004/02/mit/task"}
    node = root.find(".//t:Triggers/t:CalendarTrigger/t:StartBoundary", ns)
    if node is None or not node.text:
        raise ValueError("no CalendarTrigger StartBoundary in task XML")
    return _dt.datetime.fromisoformat(node.text)


def state_values() -> dict[str, str]:
    text = STATE.read_text(encoding="utf-8")
    keys = list(STATE_KEYS) + ["COUNTS_AS_OF_SNAPSHOT", "LAST_SNAPSHOT"]
    out = {}
    for key in keys:
        m = re.search(rf"\b{key}\s*=\s*(\S+)", text)
        if m:
            out[key] = m.group(1)
    return out


def derive(cutoff_id: str) -> dict:
    dirs = snapshot_dirs()
    manifests = {
        snapshot_id(d): json.loads((d / "MANIFEST.json").read_text(encoding="utf-8"))
        for d in dirs
    }
    if cutoff_id not in manifests:
        raise ValueError(f"COUNTS_AS_OF_SNAPSHOT {cutoff_id} has no manifest")
    cutoff = _utc(manifests[cutoff_id]["snapshot_finished_utc"])

    in_scope = [d for d in dirs if _utc(manifests[snapshot_id(d)]["snapshot_started_utc"]) <= cutoff]
    later = len(dirs) - len(in_scope)
    rows = [json.loads(ln) for ln in JSONL.read_text(encoding="utf-8").splitlines() if ln.strip()]
    rows_in = [r for r in rows if _utc(r["actual_start_utc"]) <= cutoff]

    blocks, block_ids = task_start_invocations()
    boundary = NATURAL_BOUNDARY
    try:
        export_boundary = trigger_start_boundary()
    except (OSError, ValueError, ET.ParseError) as exc:
        export_boundary = f"unreadable ({exc.__class__.__name__})"
    per_slot = Counter(r.get("scheduled_time") for r in rows_in)

    captures = []
    for r in rows_in:
        has_block = r.get("invocation_id") in block_ids
        slot = r.get("scheduled_time")
        natural = (
            has_block
            and r.get("snapshot_id") is not None
            and r.get("capture_type") == ROUTINE
            and slot is not None
            and _dt.datetime.fromisoformat(slot) >= boundary
            and per_slot[slot] == 1
        )
        late = r.get("late_by_seconds")
        captures.append({
            "snapshot_id": r.get("snapshot_id"),
            "slot": slot or "?",
            "late_by_seconds": late if isinstance(late, (int, float)) else float("nan"),
            "status": r.get("status", "?"),
            "funds_ok": r.get("funds_ok") or 0,
            "funds_failed": r.get("funds_failed") or 0,
            "snapshot_verified": r.get("snapshot_verified"),
            "capture_type": r.get("capture_type", "?"),
            "collector_version": r.get("collector_version", "?"),
            "task_start_block": has_block,
            "natural": natural,
            "catch_up": natural and isinstance(late, (int, float)) and late > CATCH_UP_THRESHOLD_S,
        })

    in_scope_ids = {snapshot_id(d) for d in in_scope}
    logged_ids = {c["snapshot_id"] for c in captures if c["snapshot_id"]}
    natural = [c for c in captures if c["natural"]]
    return {
        "dirs": in_scope,
        "snapshots": len(in_scope),
        "later_snapshots": later,
        "jsonl_rows": len(rows_in),
        "natural": len(natural),
        "manual": len(in_scope) - len(natural),
        "catch_ups": sum(c["catch_up"] for c in captures),
        "captures": captures,
        "snapshots_without_log_row": sorted(in_scope_ids - logged_ids),
        "log_rows_without_snapshot": sorted(i for i in logged_ids - in_scope_ids if i),
        "raw_blocks": blocks,
        "raw_with_block": sum(c["task_start_block"] for c in captures),
        "raw_without_block": len(in_scope) - sum(c["task_start_block"] for c in captures),
        "collector_versions": sorted({str(c["collector_version"]) for c in captures}),
        "schema_versions": dict(sorted(Counter(
            manifests[i]["manifest_schema_version"] for i in in_scope_ids).items())),
        "last_snapshot": max(in_scope_ids),
        "boundary": boundary.isoformat(),
        "export_boundary": export_boundary,
    }


_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")


def broken_links() -> tuple[int, list[str]]:
    checked, broken = 0, []
    for md in sorted(PROJ.rglob("*.md")):
        if ".git" in md.parts:
            continue
        in_fence = False
        for n, line in enumerate(md.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            for target in _LINK.findall(line):
                if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I) or target.startswith("#"):
                    continue
                checked += 1
                path = target.split("#", 1)[0]
                if not (md.parent / path).exists():
                    broken.append(f"{md.relative_to(PROJ).as_posix()}:{n} -> {target}")
    return checked, broken


def main() -> int:
    failures: list[str] = []

    tests_ok, tests_tail = run_tests()
    if not tests_ok:
        failures.append(f"test suite: {tests_tail}")

    state = state_values()
    cutoff_id = state.get("COUNTS_AS_OF_SNAPSHOT")
    if not cutoff_id:
        print("FAIL  PROJECT_STATE.md has no COUNTS_AS_OF_SNAPSHOT")
        return 1
    d = derive(cutoff_id)

    verified, verify_failed = verify_snapshots(d["dirs"])
    d["verified"] = verified
    if verify_failed:
        failures.append(f"snapshot verify FAIL: {', '.join(verify_failed)}")
    if d["log_rows_without_snapshot"]:
        failures.append(f"log rows naming a missing snapshot: {d['log_rows_without_snapshot']}")
    bad_natural = [c["snapshot_id"] for c in d["captures"] if c["natural"] and not (
        c["status"] == "COMPLETED" and c["funds_failed"] == 0 and c["snapshot_verified"])]
    # A failed natural capture is evidence, not a reproduction failure; report it.

    links_checked, links_broken = broken_links()
    failures += [f"broken link {b}" for b in links_broken]

    derived = {k: str(d[v]) for k, v in STATE_KEYS.items()}
    derived["SNAPSHOTS_VERIFIED"] = f"{verified}/{d['snapshots']}"
    derived["LAST_SNAPSHOT"] = d["last_snapshot"]
    for key, value in derived.items():
        written = state.get(key)
        if written is None:
            failures.append(f"PROJECT_STATE.md lacks {key}")
        elif written != value:
            failures.append(f"PROJECT_STATE.md {key} = {written}, derived {value}")

    print("R2 reproduce -- tools/reproduce.py")
    print(f"  tests            : {'PASS' if tests_ok else 'FAIL'} ({tests_tail})")
    print(f"  counts as of     : {cutoff_id}  (later snapshots, informational: {d['later_snapshots']})")
    print(f"  snapshots        : {d['snapshots']}   verified {verified}/{d['snapshots']}")
    print(f"  jsonl rows       : {d['jsonl_rows']}")
    print(f"  NATURAL          : {d['natural']}   (catch-ups > {CATCH_UP_THRESHOLD_S}s late: {d['catch_ups']})")
    print(f"  MANUAL           : {d['manual']}   (incl. no-log-row snapshots: {', '.join(d['snapshots_without_log_row']) or 'none'})")
    print(f"  NATURAL boundary : {d['boundary']}  (pinned, D-R2-2026-10-01-02)")
    exp = d["export_boundary"]
    if not isinstance(exp, _dt.datetime) or exp != NATURAL_BOUNDARY:
        shown = exp.isoformat() if isinstance(exp, _dt.datetime) else exp
        print(f"  WARN (info only) : task export StartBoundary {shown} differs from the pinned "
              "boundary; counts use the pinned value")
    print(f"  collector        : {', '.join(d['collector_versions'])}   manifest schema: {d['schema_versions']}")
    print(f"  last snapshot    : {d['last_snapshot']}")
    print(f"  natural not clean: {', '.join(bad_natural) or 'none'}")
    print(f"  info only        : raw 'task start' blocks = {d['raw_blocks']}; captures with block = "
          f"{d['raw_with_block']}, without = {d['raw_without_block']} (not an origin measure)")
    print(f"  md links         : {links_checked} relative links checked, {len(links_broken)} broken")
    print("  captures:")
    for c in d["captures"]:
        tag = "NATURAL" + (" catch-up" if c["catch_up"] else "") if c["natural"] else "manual"
        print(f"    {c['slot'][:16]}  {str(c['snapshot_id']):<20} late={c['late_by_seconds']:>9.1f}s "
              f"{c['status']} {c['funds_ok']}/{c['funds_ok'] + c['funds_failed']} "
              f"verified={c['snapshot_verified']} {c['capture_type']} block={'Y' if c['task_start_block'] else 'N'}  {tag}")
    for f in failures:
        print(f"FAIL  {f}")
    print(f"REPRODUCE {'PASS' if not failures else 'FAIL'}")
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
