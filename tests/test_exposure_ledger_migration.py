"""The conformant exposure carrier must never drift from its original.

Ratified SS10.1 fixes six columns at ops/EXPOSURE_LEDGER.md. ITSF's ledger has
five at the repository root and is append-only -- "rows never edited or
reordered". Rewriting it to conform would break the one discipline that makes
an append-only record worth anything, so the historical ledger stays canonical
and byte-frozen and ops/EXPOSURE_LEDGER.md transcribes it.

Two files recording one fact is a drift risk, so it is held mechanically: same
number of event rows, same total, and the carrier's rows in the same order.
A carrier that quietly gains or loses a row would misreport OUTCOME_EXPOSURE
for the whole project, which holds eight of twelve transitions.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LEGACY = REPO / "EXPOSURE_LEDGER.md"
CARRIER = REPO / "ops" / "EXPOSURE_LEDGER.md"

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


def test_the_carrier_has_one_row_per_real_legacy_event():
    """The legacy table opens with a placeholder em-dash row that records
    no event; everything after it is an event."""
    legacy = [r for r in _rows(LEGACY) if r[0] != "—"]
    carrier = _rows(CARRIER)
    assert len(carrier) == len(legacy), (
        f"carrier has {len(carrier)} rows, legacy has {len(legacy)} events -- "
        "a carrier that gains or loses a row misreports OUTCOME_EXPOSURE for "
        "the whole project")


def test_the_dates_line_up_in_order():
    legacy = [r[0] for r in _rows(LEGACY) if r[0] != "—"]
    carrier = [r[0] for r in _rows(CARRIER)]
    assert carrier == legacy, (
        f"carrier dates {carrier} do not match legacy {legacy} in order")


def test_the_carrier_uses_only_runtime_vocabulary():
    """The first transcription used the study name as scope and the SS1 axis
    tokens as classification. Both are wrong and both parsed as prose, so
    only the runtime caught it. This catches it here instead."""
    bad = []
    for row in _rows(CARRIER):
        if row[1] not in LEGAL_SCOPES:
            bad.append(f"scope {row[1]!r} (legal: {sorted(LEGAL_SCOPES)})")
        if row[2] not in LEGAL_CLASSES:
            bad.append(f"classification {row[2]!r} "
                       f"(legal: {sorted(LEGAL_CLASSES)})")
    assert not bad, "carrier uses non-runtime vocabulary:\n  " + "\n  ".join(bad)


def test_exactly_one_row_carries_the_target_metric_exposure():
    """1575 relationship cells were revealed once. If a second row ever
    claims REVEALED_TARGET_METRIC, either a real second reveal happened and
    the totals must move, or the carrier drifted."""
    revealed = [r for r in _rows(CARRIER)
                if r[2] == "REVEALED_TARGET_METRIC"]
    assert len(revealed) == 1, (
        f"{len(revealed)} rows claim REVEALED_TARGET_METRIC; the ledger "
        "records exactly one reveal")


def test_both_files_state_the_same_total():
    for path in (LEGACY, CARRIER):
        assert "1575" in path.read_text(encoding="utf-8"), (
            f"{path.name} no longer states the cumulative total")
