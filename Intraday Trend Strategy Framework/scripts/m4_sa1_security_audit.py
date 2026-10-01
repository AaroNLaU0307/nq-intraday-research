"""M4 closure — SA-1 seven-item READ-ONLY security & governance audit
(Aaron checklist 2026-07-29). Prints structured results; writes nothing.

Items:
 1. no API key / cookie / browser-profile / request-header secret in Git
 2. all raw evidence SHA-256 recomputable vs registry fragment
 3. SOURCE_LOG / registry / csv chain unbroken
 4. multi-event days per IR-12+IR-18 (9 primary NA, 19 sidecar)
 5. multi-hot only in diagnostic sidecar (frozen F10 single-category)
 6. unscheduled FOMC actions not in frozen F10 (92 scheduled only)
 7. delayed releases coded as-released
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F10 = REPO / "gate1" / "f10_event_calendar"
RAW = F10 / "raw"

results: list[tuple[str, bool, str]] = []


def item(name: str, ok: bool, detail: str) -> None:
    results.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


# ---- 1. secret patterns in tracked f10/symbology content --------------------
tracked = subprocess.run(
    ["git", "-C", str(REPO), "ls-files", "gate1/f10_event_calendar",
     "gate1/symbology"], capture_output=True, text=True).stdout.split()
pat = re.compile(rb"db-[A-Za-z0-9]{10,}|(?i:set-cookie|authorization:)"
                 rb"|Basic [A-Za-z0-9+/=]{16,}|(?i:x-api-key)")
hits = []
for f in tracked:
    data = (REPO / f).read_bytes()
    m = pat.search(data)
    if m:
        hits.append((f, m.group(0)[:30]))
item("1_no_secrets_in_git", not hits,
     f"{len(tracked)} tracked evidence files scanned, hits: {hits or 'none'}")

# ---- 2. raw SHA-256 recomputable vs registry fragment -----------------------
frag = (F10 / "f10_evidence_registry_fragment.yaml").read_text(encoding="utf-8")
# Entry layout: "file: gate1/f10_event_calendar/raw/<name>" followed (a few
# lines later, non-greedy) by 'raw_sha256: "<hex>"'.
frag_hashes = dict(re.findall(
    r"file:\s*gate1/f10_event_calendar/raw/(\S+)[\s\S]*?"
    r"raw_sha256:\s*\"([0-9a-f]{64})\"", frag))
n_ok = n_bad = 0
bad = []
raw_files = sorted(p for p in RAW.iterdir() if p.is_file())
for p in raw_files:
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    want = frag_hashes.get(p.name) or frag_hashes.get(f"raw/{p.name}")
    if want is None:
        continue
    if h == want:
        n_ok += 1
    else:
        n_bad += 1
        bad.append(p.name)
item("2_raw_sha256_recomputable", n_bad == 0 and n_ok >= 130,
     f"{len(raw_files)} raw files on disk; {n_ok} matched fragment hashes, "
     f"{n_bad} mismatched {bad or ''} (fragment entries: {len(frag_hashes)})")

# ---- 3. chain: csv source ids resolve; every raw file registered ------------
import csv as _csv
with (F10 / "f10_events.csv").open(encoding="utf-8") as fh:
    rows = list(_csv.DictReader(fh))
missing_src = sorted({r["source_id"] for r in rows
                      if r["source_id"] not in frag
                      and r["source_id"] not in frag_hashes})
unregistered = [p.name for p in raw_files
                if p.name not in frag and p.name not in frag_hashes
                and not p.name.startswith("_fetch_manifest")]
item("3_chain_unbroken", not missing_src and not unregistered,
     f"csv rows {len(rows)}; source_ids missing from fragment: "
     f"{missing_src or 'none'}; unregistered raw files: "
     f"{unregistered or 'none'}")

# ---- 4/5/6: F10 governance vs the rerun preflight json ----------------------
pj = json.loads((REPO / "S0_INPUT_PREFLIGHT.json").read_text(encoding="utf-8"))
s = pj["f10"]
excl = s["final_mutually_exclusive_F10_counts_eligible"]
item("4_multi_event_ir12_ir18",
     s["multi_event_na_days_post_ir13"]["count"] == 9
     and s["raw_multi_event_days_pre_ir13_sidecar"]["count"] == 19
     and s["partition_assertion_sum_equals_population"] is True,
     f"primary NA=9, sidecar=19, partition {excl} sums "
     f"{sum(excl.values())} == population")
item("5_multihot_sidecar_only",
     set(excl) == {"CPI", "NFP", "FOMC", "none", "NA_multi_event"},
     "frozen F10 field is single-category + NA; multi-hot lives only in "
     "the diagnostic sidecar (csv bool columns are archived evidence, not "
     "a Primary input)")
unsched = set(s["unscheduled_fomc_action_diagnostic"])
item("6_unscheduled_fomc_excluded",
     unsched == {"2019-10-11", "2020-03-03", "2020-03-15", "2020-03-23"}
     and s["category_day_counts"]["FOMC_scheduled_statement_days"] == 92,
     f"diagnostic-only unscheduled set {sorted(unsched)}; frozen FOMC = 92")

# ---- 7. delayed releases as-released ----------------------------------------
nfp_shift = any(r["date_et"] == "2013-10-22" and r["event_type"] == "NFP"
                for r in rows)
cpi_shift = any(r["date_et"] == "2013-10-30" and r["event_type"] == "CPI"
                for r in rows)
no_sched_dates = not any(r["date_et"] in ("2013-10-04", "2013-10-16")
                         and r["event_type"] in ("NFP", "CPI") for r in rows)
item("7_as_released_coding", nfp_shift and cpi_shift and no_sched_dates,
     "2013-10-22 NFP + 2013-10-30 CPI present; originally-scheduled "
     "shutdown dates absent from the table")

ok = all(r[1] for r in results)
print("SA1_SECURITY_AUDIT:", "ALL_PASS" if ok else "FAILURES_PRESENT")
sys.exit(0 if ok else 1)
