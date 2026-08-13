"""R5.1 B3 — governance-document STRUCTURE tests.

Codex's r5 finding was that the governance docs had drifted structurally:
IMPLEMENTATION_RESOLUTIONS.md carried TWO sections titled as the current
IR-28 definition, and EXPOSURE_LEDGER.md's incident cross-reference row sat
OUTSIDE the markdown table, after the cumulative line. These tests pin the
repaired structure so the drift class cannot recur silently:

* exactly ONE current IR-28 definition; every other IR-28 header must be
  explicitly marked HISTORICAL_SUPERSEDED, and the current one must appear
  BEFORE any historical one;
* the exposure ledger's table is contiguous (a row outside the table is a
  structural failure), the incident cross-reference row is INSIDE it with
  quantity 0, and the cumulative-exposure line still reads 0 and is the
  document's final statement.

These are READ-ONLY doc checks — no research data, no registry access.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RESOLUTIONS = REPO / "IMPLEMENTATION_RESOLUTIONS.md"
LEDGER = REPO / "EXPOSURE_LEDGER.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# IR-28: one current definition, everything else HISTORICAL_SUPERSEDED
# ---------------------------------------------------------------------------

def _ir28_headers() -> list[str]:
    return [line for line in _read(RESOLUTIONS).splitlines()
            if line.startswith("### IR-28")]


def test_ir28_has_exactly_one_current_definition():
    headers = _ir28_headers()
    current = [h for h in headers if "HISTORICAL_SUPERSEDED" not in h]
    assert len(current) == 1, headers
    assert "DECIDED_BY_EXPLICIT_FABLE_DELEGATION" in current[0]


def test_ir28_every_other_header_is_marked_superseded():
    headers = _ir28_headers()
    assert len(headers) >= 2, "the archived R2/R3 proposal section vanished"
    for h in headers:
        assert ("DECIDED_BY_EXPLICIT_FABLE_DELEGATION" in h
                or "HISTORICAL_SUPERSEDED" in h), h


def test_ir28_current_definition_precedes_the_historical_archive():
    text = _read(RESOLUTIONS)
    current = text.index("DECIDED_BY_EXPLICIT_FABLE_DELEGATION")
    historical = text.index("HISTORICAL_SUPERSEDED")
    assert current < historical


def test_ir28_historical_header_disclaims_its_own_stale_wording():
    superseded = [h for h in _ir28_headers() if "HISTORICAL_SUPERSEDED" in h]
    assert superseded, "no archived IR-28 section found"
    for h in superseded:
        assert "R5" in h, h          # points the reader at the current ruling


# ---------------------------------------------------------------------------
# EXPOSURE_LEDGER: contiguous table, incident row inside, cumulative 0 last
# ---------------------------------------------------------------------------

def _ledger_lines() -> list[str]:
    return _read(LEDGER).splitlines()


def _table_block() -> list[str]:
    """The ONE contiguous run of `|`-rows. A second run is a structural
    failure — that is exactly the drift Codex caught (a row appended after
    the cumulative line, outside the table)."""
    lines = _ledger_lines()
    runs: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if line.lstrip().startswith("|"):
            current.append(line)
        elif current:
            runs.append(current)
            current = []
    if current:
        runs.append(current)
    assert len(runs) == 1, (
        f"expected ONE contiguous markdown table, found {len(runs)} runs")
    return runs[0]


def test_ledger_table_is_one_contiguous_block_with_header():
    table = _table_block()
    assert table[0].startswith("| 日期 |")
    assert re.match(r"^\|[-| ]+\|$", table[1].replace("—", "-"))
    assert len(table) >= 4          # header + separator + >=2 data rows


def test_ledger_incident_row_is_inside_the_table_with_quantity_zero():
    table = _table_block()
    incident = [r for r in table if "INCIDENT_STRUCTURAL_TEST_LOAD" in r]
    assert len(incident) == 1, table
    cells = [c.strip() for c in incident[0].split("|")]
    # | 日期 | 研究 | 查看内容 | 数量 | 备注 | -> quantity is cell 4
    assert cells[4] == "0", cells
    assert "outcome_seen=NO" in incident[0]
    assert "IR-28d" in incident[0]


def test_ledger_cumulative_exposure_is_zero_and_final():
    lines = [ln for ln in _ledger_lines() if ln.strip()]
    assert lines[-1].strip() == "累计 exposure：0"


def test_ledger_incident_row_precedes_the_cumulative_line():
    text = _read(LEDGER)
    assert text.index("INCIDENT_STRUCTURAL_TEST_LOAD") \
        < text.index("累计 exposure：0")
