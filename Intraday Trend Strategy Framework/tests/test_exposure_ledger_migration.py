"""The conformant exposure carrier: a frozen transcription prefix, then
forward rows only (OD-CF-4, DEC-0004; QROS-CF v2 §10.1).

Until 2026-09-07 the carrier at ops/EXPOSURE_LEDGER.md had to be row-for-row
identical to the historical five-column ledger at the repository root, and
"exactly one row carries REVEALED_TARGET_METRIC" was pinned. Aaron froze the
root ledger as history (OD-CF-4): forward research-axis rows go ONLY to the
carrier. The invariants therefore become:

  * PREFIX IDENTITY -- the carrier's first N rows (N = the root ledger's
    event rows) still transcribe the root ledger in order; history is not
    rewritten;
  * FORWARD ONLY -- every carrier row beyond the prefix is dated on or after
    the freeze date;
  * VOCABULARY -- every row uses the runtime's closed scope / classification
    vocabulary;
  * MONOTONE -- the number of REVEALED_TARGET_METRIC rows never falls below
    the prefix's, and the stated cumulative count never falls below the
    root's;
  * the root ledger receives no row after the freeze.

No exact count is pinned: a second reveal is a legitimate future event and
must not require editing a test to record it (snapshot-coupling ban).
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LEGACY = REPO / "EXPOSURE_LEDGER.md"
CARRIER = REPO / "ops" / "EXPOSURE_LEDGER.md"
FREEZE_DATE = "2026-09-07"                 # DEC-0004

_SEP = re.compile(r"^\|[-\s|]+\|$")

LEGAL_SCOPES = {"HISTORICAL_CUMULATIVE", "CURRENT_REVIEW_SCOPE"}
LEGAL_CLASSES = {"NO_OUTCOME", "GENERATED_NOT_SEEN",
                 "REVEALED_AGGREGATE", "REVEALED_TARGET_METRIC"}


def _rows(path):
    out = []
    for line in path.read_text(encoding="utf-8").split("\n"):
        s = line.strip()
        if s.startswith("|") and s.endswith("|") and not _SEP.match(s):
            out.append([c.strip() for c in s[1:-1].split("|")])
    return out[1:]          # drop the column header


def _legacy_events():
    return [r for r in _rows(LEGACY) if r[0] != "—"]


def test_the_carrier_still_transcribes_the_root_ledger_as_its_prefix():
    legacy = _legacy_events()
    carrier = _rows(CARRIER)
    assert len(legacy) >= 6, "premise: the root ledger records the S0 history"
    assert len(carrier) >= len(legacy), (
        f"carrier has {len(carrier)} rows, fewer than the {len(legacy)} root "
        "events it transcribes -- history was lost")
    assert [r[0] for r in carrier[:len(legacy)]] == [r[0] for r in legacy], (
        "the transcription prefix no longer matches the root ledger in order")


def test_rows_beyond_the_prefix_are_forward_only():
    legacy = _legacy_events()
    for row in _rows(CARRIER)[len(legacy):]:
        assert row[0] >= FREEZE_DATE, (
            f"carrier row dated {row[0]} lies beyond the transcription prefix "
            f"but before the freeze date {FREEZE_DATE}")


def test_the_root_ledger_received_no_row_after_the_freeze():
    for row in _legacy_events():
        assert row[0] < FREEZE_DATE, (
            f"the root ledger gained a row dated {row[0]}; forward rows go "
            "only to ops/EXPOSURE_LEDGER.md (OD-CF-4)")


def test_the_carrier_uses_only_runtime_vocabulary():
    bad = []
    for row in _rows(CARRIER):
        if row[1] not in LEGAL_SCOPES:
            bad.append(f"scope {row[1]!r} (legal: {sorted(LEGAL_SCOPES)})")
        if row[2] not in LEGAL_CLASSES:
            bad.append(f"classification {row[2]!r} "
                       f"(legal: {sorted(LEGAL_CLASSES)})")
    assert not bad, "carrier uses non-runtime vocabulary:\n  " + "\n  ".join(bad)


def test_target_metric_reveals_never_decrease():
    legacy_n = sum(1 for r in _legacy_events()
                   if any("TARGET_METRIC" in cell for cell in r))
    carrier_n = sum(1 for r in _rows(CARRIER) if r[2] == "REVEALED_TARGET_METRIC")
    assert carrier_n >= 1, "the one recorded reveal must still be there"
    assert carrier_n >= legacy_n


def test_the_stated_cumulative_count_never_falls_below_the_prefix_total():
    """The carrier's own 累计 line versus the total its transcription prefix
    records (`legacy 数量=<n>` in the prefix rows' notes). Self-contained: the
    frozen root ledger is not parsed for a number."""
    text = CARRIER.read_text(encoding="utf-8")
    stated = re.search(r"累计 researcher_exposure_count[：:]\s*([0-9]+)", text)
    assert stated, "the carrier states no cumulative count on its 累计 line"
    prefix = _rows(CARRIER)[:len(_legacy_events())]
    legacy_totals = [int(m) for r in prefix
                     for m in re.findall(r"legacy 数量=([0-9]+)", " ".join(r))]
    assert legacy_totals, "premise: the prefix records its legacy quantities"
    assert int(stated.group(1)) >= max(legacy_totals)
