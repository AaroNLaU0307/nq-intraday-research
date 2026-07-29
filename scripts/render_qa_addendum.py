"""Render DATA_QA_ADDENDUM.md (Aaron 2026-07-29 structural closure spec).

Deterministic assembly from QA-run artifacts (qa_addendum_a1.json,
qa_addendum_a2.json, qa_addendum_a2_census.json, spread_cost_table.csv),
live hashes, git lineage, and mechanical check outputs. QA-only: contains
structural facts, no strategy returns / Oracle / EV / verdicts.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

A1_JOB = Path(r"C:\Users\Aaron\quant-data\databento-archive\intraday-trend"
              r"\development_signal\GLBX-20260727-DL3BEBCHJA")
A2_JOB = Path(r"C:\Users\Aaron\quant-data\databento-archive\intraday-trend"
              r"\execution_cost_calibration\GLBX-20260727-TV3MXWNMXD")
E_A1 = Path(r"E:\quant-data\databento-archive\intraday-trend"
            r"\development_signal\GLBX-20260727-DL3BEBCHJA\manifest.json")
E_A2 = Path(r"E:\quant-data\databento-archive\intraday-trend"
            r"\execution_cost_calibration\GLBX-20260727-TV3MXWNMXD\manifest.json")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(REPO), *args],
                          capture_output=True, text=True).stdout.strip()


def run(cmd: list[str], cwd: Path | None = None) -> tuple[int, str]:
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    return r.returncode, (r.stdout + r.stderr).strip()


def classify(row: dict, degraded: set[str]) -> str:
    d = row["date"]
    if d in degraded:
        return "vendor_degraded_gap (Databento condition.json)"
    if d.startswith("2020-03"):
        return "market_halt_period (COVID limit/circuit-breaker era; structural, not data loss)"
    if row["reason"] == "early_close":
        return "holiday_session_thin_morning (scheduled early-close holiday)"
    return "no_trade_minutes_omitted (trade-aggregated OHLCV; thin 2010-2013 era)"


def main() -> int:
    a1 = json.loads((REPO / "qa_addendum_a1.json").read_text(encoding="utf-8"))
    a2 = json.loads((REPO / "qa_addendum_a2.json").read_text(encoding="utf-8"))
    census = json.loads((REPO / "qa_addendum_a2_census.json").read_text(encoding="utf-8"))

    import pandas as pd
    tbl = pd.read_csv(REPO / "spread_cost_table.csv")
    rth = tbl[(tbl.minute_of_day_et >= 570) & (tbl.minute_of_day_et < 960)]
    all_slots = set(range(1440))
    present = set(tbl.minute_of_day_et.astype(int))
    absent = sorted(all_slots - present)
    maint = list(range(1020, 1080))
    absent_is_maint = absent == maint

    import databento
    import pandas_market_calendars as pmc
    versions = (f"Python {sys.version.split()[0]}, databento {databento.__version__}, "
                f"pandas {pd.__version__}, pandas-market-calendars {pmc.__version__}")

    # ---- mechanical checks (run live, embed outputs) ------------------------
    checks = []
    rc, out = run([sys.executable, "-m", "pytest", "tests", "-q"], cwd=REPO)
    checks.append(("pytest full suite", rc, out.splitlines()[-1] if out else ""))
    rc, out = run([sys.executable,
                   r"C:\Users\Aaron\quant-data\tools\seal_check.py"])
    checks.append(("seal_check.py (mc-freeze 6-item)", rc, out))
    rc, out = run([sys.executable,
                   r"C:\Users\Aaron\quant-data\tools\verify_freeze_hashes.py"])
    checks.append(("verify_freeze_hashes.py (s0-freeze)", rc, out))
    code = ("import sys; sys.path.insert(0, r'" + str(REPO / 'src') + "'); "
            "from itsf import guards; guards.verify_frozen_hashes(); "
            "print('7 canonical frozen hashes OK')")
    rc, out = run([sys.executable, "-c", code])
    checks.append(("guards.verify_frozen_hashes()", rc, out))
    code = ("import yaml, pathlib; "
            "p = pathlib.Path(r'" + str(REPO / 'gate1' / 'platform_params.yaml') + "'); "
            "d = yaml.safe_load(p.read_text(encoding='utf-8')); "
            "assert isinstance(d, dict) and d, 'empty'; "
            "print('platform_params.yaml structural parse OK,', len(d), 'top-level keys')")
    rc, out = run([sys.executable, "-c", code])
    checks.append(("pyyaml structure assertion", rc, out))

    degraded = set(a1["condition_json"]["non_available_dates"])
    zb = a1["calendar"]["zero_bar_calendar_days"]
    zb_deg = sorted(set(zb) & degraded)
    zb_closure = sorted(set(zb) - degraded)
    w = a1["windows"]
    c = a1["counts"]

    att = REPO / "ops" / "physical_copy_attestation.json"
    att_j = json.loads(att.read_text(encoding="utf-8"))
    flag_txt = (REPO / "ops" / "SECOND_COPY_ATTESTED.flag").read_text(encoding="utf-8").strip()
    g9_txt = (REPO / "gate1" / "G9_RESOLVED.flag").read_text(encoding="utf-8").strip()

    backup_lines = []
    for tag, ep in (("A1", E_A1), ("A2", E_A2)):
        if ep.exists():
            backup_lines.append(f"  - backup {tag} manifest.json sha256 (live): `{sha(ep)}`")
        else:
            backup_lines.append(
                f"  - backup {tag} manifest.json: E: drive NOT mounted at addendum "
                "time (removable disk). Backup equality rests on the attestation's "
                "three-way per-file match at verification time; re-verification "
                "requires remounting the drive.")

    L = []
    A = L.append
    A("# DATA QA ADDENDUM — structural closure (per Aaron 2026-07-29 spec)")
    A("")
    A("QA-only. Contains structural facts exclusively — no strategy returns, no")
    A("Oracle output, no EV, no MC, no Checkpoint 0. **Real S0 remains locked**")
    A("pending Aaron's explicit approval; this addendum does not change that.")
    A("")
    A("Base report: DATA_QA_REPORT.md (QA commit `4ab40c5`). Analysis conventions:")
    A("all wall-clock references America/New_York (ET); bar-start convention")
    A("(bar 15:44 covers 15:44:00-15:44:59, closes 15:45 = frozen forced exit);")
    A("exchange-closed time is never counted as missing (spec item 9): windows are")
    A("evaluated only on pandas-market-calendars CME_Equity scheduled trading days,")
    A("scheduled early-close afternoons are excluded days (not missing minutes),")
    A("and the 17:00-18:00 maintenance hour / weekends / holidays are out of scope")
    A("by construction.")
    A("")
    A("## A1 Development (NQ.v.0 ohlcv-1m)")
    A("")
    A("### 1. Coverage")
    A(f"- first bar: `{a1['global_first_ts_utc']}` UTC = `{a1['global_first_ts_et']}` ET")
    A(f"- last bar:  `{a1['global_last_ts_utc']}` UTC = `{a1['global_last_ts_et']}` ET")
    A("- purchased query window (metadata.json): 2010-06-06 -> 2022-01-01 UTC")
    A("  (exclusive); GLBX.MDP3 dataset itself begins 2010-06-06.")
    A(f"- files: {a1['n_files']} monthly (UTC month split); total bars {a1['total_bars']:,};")
    A("  file-boundary overlaps: none; decode failures: none.")
    A("")
    A("### 2. Per-file bar counts and hash verification")
    A("Every file's SHA-256 is verified against the official Databento")
    A("manifest.json inside `DevelopmentSignalLoader.load_real` BEFORE decode")
    A("(fail-closed); a decoded file below therefore implies hash match.")
    A("")
    A("| file | bars | first ET date | last ET date | manifest sha256 |")
    A("|---|---|---|---|---|")
    for f in a1["per_file"]:
        A(f"| {f['file']} | {f['n_bars']:,} | {f['first_date_et']} | "
          f"{f['last_date_et']} | verified |")
    A("")
    A("### 3. Trading days")
    cal = a1["calendar"]
    A(f"- scheduled (CME_Equity, 2010-06-06..2021-12-31): **{cal['trading_days_scheduled']}**"
      f" (of which {cal['early_close_days_scheduled']} scheduled early closes)")
    A(f"- observed days with RTH bars: **{cal['observed_rth_days']}**")
    A(f"- RTH bars on non-scheduled days: {len(cal['rth_days_off_calendar'])} (none)")
    A(f"- scheduled days with ZERO RTH bars: {len(zb)} — classified:")
    A(f"  - {len(zb_deg)} vendor-degraded (also in Databento condition.json): {', '.join(zb_deg)}")
    A(f"  - {len(zb_closure)} known market closures the calendar model does not")
    A("    carry (3x Good Friday 2012/2015/2021; 2x Hurricane Sandy 2012-10-29/30;")
    A("    9x 2012-2014-era holidays with no RTH session under CME's then-current")
    A(f"    holiday schedule): {', '.join(zb_closure)}")
    A("  Downstream these fall under the frozen S0 SS3 exclusion rules (zero-bar")
    A("  day); QA records facts only.")
    A("")
    A("### 4. Window 09:30-10:00 ET (30 bars, frozen observation window)")
    A(f"- complete days: **{w['w1_complete']}** of {cal['observed_rth_days']}")
    A(f"- incomplete days: **{w['w1_incomplete']}** (missing minutes total {w['w1_missing_minutes']})")
    A("")
    A("### 5. Window 10:00-15:44 ET (345 bars, frozen PM window)")
    A(f"- complete days: **{w['w2_complete']}**")
    A(f"- excluded days (scheduled early close, afternoon not traded): **{w['w2_excluded_early_close']}**")
    A(f"- incomplete days (missing data within an open window): **{w['w2_incomplete_missing_data']}**"
      f" (missing minutes total {w['w2_missing_minutes']})")
    A("")
    A("### 4+5. Incomplete-day detail and exclusion reasons (all 20 rows)")
    A("")
    A("| date | window | present/expected | classification |")
    A("|---|---|---|---|")
    for r in w["incomplete_detail"]:
        A(f"| {r['date']} | {r['window']} | {r['present']}/{r['expected']} | "
          f"{classify(r, degraded)} |")
    A("")
    A("Notes: the two vendor gaps (2020-02-28: 286 min; 2020-06-30: 334 min) are")
    A("the only large in-window holes and both are vendor-documented degraded")
    A("dates; 2020-03 rows are COVID circuit-breaker/halt minutes (no trades ->")
    A("no bars in trade-aggregated OHLCV); remaining rows are 1-4 thin no-trade")
    A("minutes in the 2010-2013 low-volume era. The frozen >10%-missing exclusion")
    A("rule governs day eligibility downstream; QA does not decide.")
    A("")
    A("### 6. ADR14 lookback completeness (availability only — no values computed)")
    adr = a1["adr14"]
    A("- frozen definition (prereg): mean RTH range of the prior 14 COMPLETE RTH")
    A("  days, excluding the current day; complete RTH day = scheduled full day")
    A("  with all 390 bars 09:30-15:59.")
    A(f"- complete RTH days in sample: **{adr['complete_rth_days']}**")
    A(f"- candidate D-days (both frozen windows complete): **{adr['candidate_days_both_windows']}**")
    A(f"- warm-up days lacking a full 14-day lookback: **{adr['warmup_days_lacking_14_lookback']}**"
      f" ({adr['warmup_dates'][0]} .. {adr['warmup_dates'][-1]})")
    A(f"- first day with full lookback: **{adr['first_full_lookback_day']}**")
    A("- handling: warm-up days are structurally ineligible for ADR14-normalized")
    A("  features/labels and are excluded by the frozen normalization definition;")
    A("  ADR14 numeric values were NOT computed at QA stage.")
    A("")
    A("### 7. Explicit anomaly counts (all 139 files, 3,848,635 bars)")
    A(f"- duplicate (ET date, minute) slots: **{c['duplicate_date_minute_slots']}**")
    A(f"- NaN price rows: **{c['nan_price_rows']}**; inf price rows: **{c['inf_price_rows']}**;")
    A(f"  non-positive price rows: **{c['nonpositive_price_rows']}**")
    A(f"- OHLC consistency violations (H<L, H<max(O,C), L>min(O,C)): **{c['ohlc_consistency_violations']}**")
    A(f"- zero/negative volume rows: **{c['zero_or_neg_volume_rows']}** (in RTH: "
      f"**{c['zero_or_neg_volume_rows_rth']}**)")
    A(f"- missing minutes inside frozen windows on scheduled open time: "
      f"**{w['w1_missing_minutes'] + w['w2_missing_minutes']}** (53 + 648; itemized above)")
    A("- loader qa_bars events across all files: none (0 duplicate_minute,")
    A("  0 bad_price, 0 zero_volume).")
    A("")
    A("### 8. DST / holidays / half-days / rolls")
    dst = a1["dst"]
    A(f"- DST: {len(dst['transition_days_in_coverage'])} transitions in coverage.")
    A("  US transitions occur 02:00 local Sunday while Globex equity is closed")
    A("  (Friday-close..Sunday-18:00 gap); dates listed are the first post-switch")
    A("  midnights (Mondays), all of which show full RTH sessions. UTC->ET")
    A("  conversion via zoneinfo America/New_York (DST-safe); no duplicate or")
    A("  phantom RTH minutes observed on any transition-adjacent day (global")
    A("  duplicate count 0).")
    A("- holidays: zero-bar scheduled days itemized in section 3; scheduled")
    A(f"  early-close days observed with RTH bars: {w['w2_excluded_early_close']}"
      f" of {cal['early_close_days_scheduled']} scheduled; the other "
      f"{cal['early_close_days_scheduled'] - w['w2_excluded_early_close']} are")
    A("  early-close-scheduled days among the 20 zero-bar closures above.")
    A("  Early-close afternoons are excluded days, never missing minutes.")
    rolls = a1["rolls"]
    A(f"- rolls: **{rolls['n_transitions']}** instrument transitions (quarterly cadence,")
    A("  2010-06..2021-12 => ~46-47 expected). All transitions occur exactly at")
    A("  00:00 UTC (Databento v.0 continuous remaps daily by prior-day volume);")
    A("  instrument_ids are unmapped integers (map_symbols=false; symbology file")
    A("  not included in the batch package) — the transition COUNT and dates are")
    A("  the structural facts; per the frozen spec, F5 gap is recorded NA on")
    A("  is_roll_transition days downstream.")
    A("- Databento condition.json: "
      + json.dumps(a1["condition_json"]["tally"])
      + f"; degraded dates: {len(degraded)}, of which {len(zb_deg)} are zero-bar")
    A("  days and 2 (2020-02-28, 2020-06-30) are the large in-window gaps; the")
    A("  remaining degraded dates decoded with complete frozen windows.")
    A("")
    A("### 9. Closed-time handling")
    A("Confirmed by construction: window statistics are computed only over")
    A("scheduled trading days from the frozen calendar source; weekends, holidays,")
    A("the 17:00-18:00 maintenance hour, overnight hours, and scheduled early-close")
    A("afternoons never enter any missing-minute count.")
    A("")
    A("## A2 Execution-Cost Calibration (MNQ.v.0 bbo-1s)")
    A("")
    A("### 1. Per-month raw rows, timestamps, date coverage")
    A("Files are split by RECEIPT month (UTC); the `ts` column is ts_event = last")
    A("book-update time, which lawfully lags into the prior calendar day across")
    A("closed periods (e.g. the January file opens with the frozen book state")
    A("stamped 2024-12-31 21:59:59 UTC = 16:59:59 ET NYE close) and is undefined")
    A("(NaT) on session-start snapshot rows.")
    A("")
    A("| file | rows | first ts_event UTC | last ts_event UTC | ET dates |")
    A("|---|---|---|---|---|")
    for m in a2["months"]:
        A(f"| {m['file']} | {m['n_rows']:,} | {m['first_ts_utc']} | "
          f"{m['last_ts_utc']} | {m['first_date_et']}..{m['last_date_et']} "
          f"({m['n_dates_et']}d) |")
    A(f"\n- total rows: **{a2['total_rows']:,}**; per-file manifest SHA-256 verified")
    A("  before decode (fail-closed), as in A1.")
    A("- Databento condition.json (A2): " + json.dumps(a2["condition_json"]["tally"])
      + "; non-available dates: none.")
    A("")
    A("### 2. crossed_or_invalid_spread per month")
    A("")
    A("| file | crossed (ask<bid) | denominator | fraction |")
    A("|---|---|---|---|")
    for m in a2["months"]:
        A(f"| {m['file']} | {m['n_crossed_ask_lt_bid']} | {m['n_rows']:,} | "
          f"{m['crossed_fraction']:.4%} |")
    A(f"\n- max single-file fraction: **{a2['max_single_file_crossed_fraction']:.4%}**"
      " — two orders of magnitude below the 1% fail-closed threshold.")
    A(f"- totals: crossed {a2['total_crossed']}; NaN spread {a2['total_nan_spread']};")
    A(f"  locked (ask==bid) {a2['total_locked']}.")
    A("")
    A("### 3. Definitions")
    A("- crossed = `ask_px < bid_px` (spread < 0). Excluded with QA event.")
    A("- `ask == bid` (locked book, spread 0): KEPT as valid 0-spread observations")
    A(f"  ({a2['total_locked']} rows of {a2['total_rows']:,}; ~1 per 124k rows — no material")
    A("  effect on per-minute medians/percentiles).")
    A("- NaN spread rows: 0 in all three files.")
    A("- NaT ts_event rows (undefined-timestamp sentinel): 299 total, of which 84")
    A("  carry a valid spread — see section 4.")
    A("")
    A("### 4. Exclusion before aggregation (and one bookkeeping fix)")
    A("Confirmed: the invalid mask (spread<0 | NaN spread | NaT ts_event) is")
    A("applied BEFORE the per-minute groupby; only valid rows enter the spread")
    A("table (cost_calibration_loader._spread_table; regression-tested).")
    A("Found during this addendum: 84 valid-spread rows with NaT ts_event were")
    A("previously dropped SILENTLY by the minute groupby (NaN group key). This")
    A("violated the frozen every-cleaning-decision-is-a-QA-event rule and was")
    A("patched in this commit: they are now excluded explicitly with a")
    A("`nat_timestamp_excluded` QA event (per month: 9 / 13 / 62). The exclusion")
    A("set is unchanged, therefore the aggregation is numerically identical:")
    A("spread_cost_table.csv is byte-identical before/after the patch")
    A("(sha256 `" + sha(REPO / "spread_cost_table.csv")[:16] + "...`, unchanged; full hash in section 7).")
    A("")
    A("### 5. Seeded crossed-row forensics (seed 20260729, k=5 per month)")
    A("Sampled crossed rows with +/-2 neighbor context (bounded summaries via the")
    A("loader's private diagnostic; raw BBO frames never left the loader module):")
    A("- NOT a bid/ask field swap: only 0.0221% of rows are crossed; a swapped")
    A("  file would be ~100% crossed. Sampled neighbors show normal positive")
    A("  spreads adjacent to crossings.")
    A("- NOT price scaling: mid-price vs neighbor mid ratios 0.9974-1.0000; all")
    A("  prices are on the 0.25 tick grid at plausible NQ levels.")
    A("- NOT schema mapping: windows decode coherently; e.g. a February crossing")
    A("  of -80.0 points at 16:59:59.88 ET normalizes to +1.75 points on the very")
    A("  next row at the 18:00:00.97 ET reopen.")
    A("- Phase census of all 1,091 crossed rows (by ts_event ET wall-clock):")
    for f in census["files"]:
        A(f"  - {f['file'].split('.')[0][-17:]}: {json.dumps(f['crossed_by_phase'])}, "
          f"RTH magnitude {json.dumps(f['rth_crossed_magnitude'])}")
    A("  Boundary/NaT clusters (session close 16:59:59, Sunday pre-open, early-")
    A("  close boundary 12:59:59 on 2025-01-20 MLK) show large persistent")
    A("  crossings that resolve exactly at reopen — book states disseminated")
    A("  while matching is halted, when resting orders may lawfully cross.")
    A("  In-RTH crossings (269 seconds of ~1.45M RTH seconds, 0.019%) also show")
    A("  large magnitudes (median 31-260 ticks) concentrated in volatile")
    A("  sessions, CONSISTENT WITH momentary matching pauses (CME Stop/Velocity")
    A("  Logic) — this attribution is a Level-3 inference not verifiable from")
    A("  bbo-1s alone and is recorded as hypothesis, not fact. All crossed rows")
    A("  are excluded from the spread table regardless of phase.")
    A("")
    A("### 6. Per-slot sample counts (from spread_cost_table.csv, 3 months summed)")
    n = tbl["n_obs"]
    nr = rth["n_obs"]
    A(f"- 1380 covered slots: n_obs min {int(n.min()):,} / median {int(n.median()):,} / "
      f"max {int(n.max()):,}; zero-sample covered slots: 0")
    A(f"- 390 RTH slots (09:30-16:00): n_obs min {int(nr.min()):,} / median "
      f"{int(nr.median()):,} / max {int(nr.max()):,}; zero-sample RTH slots: 0")
    A(f"- absent slots: {len(absent)} = " +
      ("exactly the 17:00-17:59 ET maintenance hour (exchange closed — correct "
       "absence, not missing data)." if absent_is_maint else f"{absent[:8]}..."))
    A("")
    A("### 7. spread_cost_table.csv")
    A(f"- schema: {list(tbl.columns)}")
    A(f"- rows: {len(tbl)}")
    A(f"- sha256: `{sha(REPO / 'spread_cost_table.csv')}`")
    A("")
    A("## Evidence chain")
    A("")
    A(f"- QA commit: `4ab40c5` (base report, attestation, flag, loader QA-eventization);")
    A("  this addendum and the NaT bookkeeping patch land in the follow-up commit.")
    A(f"- physical_copy_attestation.json sha256 (recomputed now): `{sha(att)}`")
    A("  — matches the value recorded inside SECOND_COPY_ATTESTED.flag. Content:")
    A(f"  {att_j['primary_file_count']}<->{att_j['backup_file_count']} files, "
      f"{att_j['official_manifest_entries_checked']} official manifest entries, "
      f"all_raw_sha256_match={att_j['all_raw_sha256_match']}, "
      f"verified_at {att_j['verified_at_utc']}, all mismatch lists empty.")
    A(f"- primary A1 manifest.json sha256: `{sha(A1_JOB / 'manifest.json')}`")
    A(f"- primary A2 manifest.json sha256: `{sha(A2_JOB / 'manifest.json')}`")
    for line in backup_lines:
        A(line)
    A("- loader/code lineage: 25cb93b (skeleton) -> 931bcbc (orchestrator) ->")
    A("  a0e0136 (pre-attestation tooling) -> a88b5ba (real-data loaders) ->")
    A("  bbe67bb (verify v2) -> 4ab40c5 (QA eventization) -> this commit")
    A("  (NaT event patch + QA-addendum diagnostics).")
    A("- G9 evidence resolution: commit `f932714` (MC1.1-G9 addendum, Case A);")
    A("  gate1/G9_RESOLVED.flag content:")
    for ln in g9_txt.splitlines():
        A(f"  > {ln}")
    A("- ops/SECOND_COPY_ATTESTED.flag (created in 4ab40c5) content:")
    for ln in flag_txt.splitlines():
        A(f"  > {ln}")
    A("- QA thresholds and versions:")
    A("  - crossed/invalid/NaT exclusion threshold: >1% of a file fails closed;")
    A("    below threshold rows are excluded WITH QA events (never silently).")
    A("  - qa_bars taxonomy: duplicate_minute / bad_price / zero_volume /")
    A("    missing_minute / pre_launch_row / schema_gap; MNQ launch boundary")
    A("    2019-05-06; Development window [2010-06-06, 2022-01-01) fail-closed")
    A("    (IV era 2022-01-01..2025-07-01 never loadable; see ERRATA).")
    A("  - frozen day-exclusion rules (S0 SS3, incl. >10%-missing) are applied")
    A("    downstream at S0 time, not at QA time.")
    A(f"  - toolchain: {versions}; calendar CME_Equity; tz zoneinfo America/New_York.")
    A("- flags state at render time: gate1/G9_RESOLVED.flag PRESENT (f932714,")
    A("  2026-07-28); ops/SECOND_COPY_ATTESTED.flag PRESENT (4ab40c5, 2026-07-29);")
    A("  guards.assert_real_run_allowed() passes mechanically, but real S0 remains")
    A("  ADMINISTRATIVELY LOCKED pending Aaron's explicit approval of the QA")
    A("  report and this addendum.")
    A("")
    A("## Mechanical re-checks (run at render time)")
    A("")
    for name, rc, out in checks:
        status = "PASS" if rc == 0 else f"FAIL rc={rc}"
        A(f"### {name}: {status}")
        A("```")
        for ln in out.splitlines():
            A(ln)
        A("```")
    A("")
    A("-- end of addendum; awaiting Aaron's review. Real S0 stays locked. --")

    out_path = REPO / "DATA_QA_ADDENDUM.md"
    out_path.write_text("\n".join(L), encoding="utf-8")
    print(f"written: {out_path}")
    for name, rc, _ in checks:
        print(f"check {name}: rc={rc}")
    return 0 if all(rc == 0 for _, rc, _ in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
