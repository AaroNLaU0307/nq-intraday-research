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


# --- R5.1.1 (C2): each IR has exactly ONE current section; the only extra
# IR header the file may carry is the ONE explicitly-archived IR-28. -------

def _headers(prefix: str) -> list[str]:
    return [line for line in _read(RESOLUTIONS).splitlines()
            if line.startswith(prefix)]


def test_each_ir_number_has_exactly_one_current_section():
    assert len(_headers("### IR-25")) == 1
    assert len(_headers("### IR-26")) == 1
    assert len(_headers("### IR-27")) == 1
    ir28 = _headers("### IR-28")
    current = [h for h in ir28 if "HISTORICAL_SUPERSEDED" not in h]
    historical = [h for h in ir28 if "HISTORICAL_SUPERSEDED" in h]
    assert len(current) == 1, ir28
    assert len(historical) == 1, ir28


def test_resolutions_has_no_duplicated_content_window():
    """The R5-era python-splice edits twice left byte-identical duplicate
    blocks behind (IR-26/27 sections; the orphaned P1/P2+IR-25-erratum
    table). This guard fails on ANY repeated 20-line window of substance,
    so the whole drift class is caught structurally rather than by header
    greps alone."""
    lines = _read(RESOLUTIONS).splitlines()
    seen: dict[str, int] = {}
    for i in range(len(lines) - 19):
        window = "\n".join(lines[i:i + 20])
        if len(window.strip()) <= 200:
            continue
        assert window not in seen, (
            f"lines {seen[window] + 1} and {i + 1} start identical "
            "20-line blocks — an accidental duplication survived")
        seen[window] = i


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


def test_ledger_cumulative_exposure_matches_the_reveal_and_is_final():
    """Updated at S0-T001 reveal (2026-08-14): the cumulative line now
    carries the conservative reveal count from the outcome-blind manifest
    — the pin tracks the TRUE current state, it is never relaxed."""
    lines = [ln for ln in _ledger_lines() if ln.strip()]
    assert lines[-1].strip().startswith("累计 exposure：1575")


def test_ledger_incident_row_precedes_the_cumulative_line():
    text = _read(LEDGER)
    assert text.index("INCIDENT_STRUCTURAL_TEST_LOAD") \
        < text.index("累计 exposure：0")


# ---------------------------------------------------------------------------
# Output-roots attestation round (2026-08-14): the persisted evidence docs
# ---------------------------------------------------------------------------
PACKET = REPO / "CODEX_REVIEW_PACKET_S0_CLOSEOUT_FINAL.md"
OPS_DECISION = REPO / "ops" / "S0_OUTPUT_ROOTS_OPERATIONS_DECISION.md"
CHECKLIST = REPO / "ops" / "OUTPUT_ROOTS_READINESS_CHECKLIST.md"
AUTH_PACKET = REPO / "S0_REAL_RUN_AUTHORIZATION_PACKET.md"

_FROZEN_WORDING = (
    "FROZEN_RUNTIME_CANONICAL_SET_COUNT=7",
    "APPROVAL_PROVENANCE_ORIGINALS={gate1/G9_EVIDENCE_RESOLUTION.md,"
    "IR_APPROVAL_PACKET.md}",
    "APPROVAL_PROVENANCE_BINDING=AUTHORIZED_COMMIT_PLUS_GIT_CLEAN",
    "APPROVAL_PROVENANCE_IN_A12_DIRECT_HASH_SET=NO",
)


def test_ops_decision_doc_carries_rulings_and_frozen_wording():
    text = _read(OPS_DECISION)
    assert ("SAME_VOLUME_FOR_S0_T001="
            "ACCEPTED_WITH_DISCLOSED_COMMON_MODE_RISK") in text
    assert "ARCHIVE_ROLE=INTEGRITY_REVIEW_COPY_NOT_BACKUP" in text
    for line in _FROZEN_WORDING:
        assert line in text, line


def test_checklist_carries_the_attestation_record():
    text = _read(CHECKLIST)
    assert "START_S0_OUTPUT_ROOTS_ATTESTATION_AFTER_PROMPT_AUDIT" in text
    assert "validate_output_roots_operational" in text
    assert "SYNC_ATTESTATION=PASS" in text
    assert "DISK_HEALTH_ATTESTATION=PASS" in text
    # every checklist checkbox is checked (the attestation completed them)
    assert "- [ ]" not in text


def test_packet_has_exactly_one_current_facts_table():
    text = _read(PACKET)
    assert text.count("## 现势事实表") == 1
    assert ("CODEX_TESTED_HEAD="
            "408e9085e1482c542a58fd6dee6652c9b8bff7e4") in text
    # the current-facts table precedes every historical section
    assert text.index("## 现势事实表") < text.index("【HISTORICAL】")


def test_auth_packet_keeps_history_and_carries_the_attestation_layer():
    """The authorization packet is a LAYERED living document — its own
    convention is dated annotations over preserved originals. Both the
    original 2026-07-31 header and the 2026-08-14 attestation layer must
    coexist (an overwrite that drops history fails here)."""
    text = _read(AUTH_PACKET)
    assert "packet_approval_status:   PACKET_APPROVED" in text
    assert "drafted_at_utc: 2026-07-31" in text
    assert "唯一有效授权语句" in text          # original §10 survives
    assert "OUTPUT_ROOTS_CREATED=YES" in text  # new attestation layer
    assert "REAL_S0_NOT_AUTHORIZED" in text


# ---------------------------------------------------------------------------
# S0-T001 blind post-run closeout (2026-08-14)
# ---------------------------------------------------------------------------
POST_RUN = REPO / "ops" / "S0_T001_POST_RUN_ATTESTATION.md"


def test_post_run_attestation_is_blind_and_complete():
    text = _read(POST_RUN)
    assert "RESULT_VALUES_VIEWED=NO" in text
    assert "RESEARCH_CONCLUSION=SEALED_NOT_REVEALED" in text
    assert "RUN_ARCHIVE_INVENTORY_EQUAL=YES" in text
    assert "CHAIN_VALID=YES" in text
    assert "validate_formal_payload problems=0" in text
    assert "MC_READY_GATE=REFUSED_AS_DESIGNED" in text
    assert "876c1b74131b4ab1a89dce433ecce646ba481f8c" in text


def test_ledger_blind_closeout_row_generated_not_seen():
    """The 2026-08-14 row must say outcomes WERE generated and were NOT
    seen — never 'zero outcomes generated' (that wording belongs to the
    2026-08-10 incident row alone) — and cumulative stays 0."""
    table = _table_block()
    rows = [r for r in table if "盲式收口" in r]
    assert len(rows) == 1, table
    row = rows[0]
    assert "outcome_generated=YES" in row
    assert "outcome_seen=NO" in row
    assert "raw_viewed_relation_count=0" in row
    cells = [c.strip() for c in row.split("|")]
    assert cells[4] == "0", cells


def test_ledger_reveal_row_carries_manifest_binding():
    """The RESULT_REVEAL_STARTED row must bind the conservative count to
    the outcome-blind manifest (sha) and was committed BEFORE any research
    value entered the model context."""
    table = _table_block()
    rows = [r for r in table if "RESULT_REVEAL_STARTED" in r]
    assert len(rows) == 1, table
    row = rows[0]
    assert "raw exposure count=1575" in row
    assert ("02381b025316548994b6c2862abd40d8dca37722a6826b3fd6209189"
            "de0d1e16") in row
    cells = [c.strip() for c in row.split("|")]
    assert cells[4] == "1575", cells
    manifest = REPO / "ops" / "S0_T001_REVEAL_EXPOSURE_MANIFEST.jsonl"
    body = manifest.read_bytes()
    import hashlib
    assert hashlib.sha256(body).hexdigest() == (
        "02381b025316548994b6c2862abd40d8dca37722a6826b3fd6209189de0d1e16")
    assert len(body.decode("utf-8").splitlines()) == 1575


def test_auth_packet_records_the_completed_lifecycle():
    text = _read(AUTH_PACKET)
    assert "SEALED_NOT_REVEALED" in text
    assert "S0-T001_20260813T170432Z" in text
    # the reveal passphrase is recorded but the packet still says it only
    # works when Aaron sends it
    assert ("START_S0_T001_RESULT_REVEAL_AND_DECISION_COUNCIL_"
            "AFTER_BLIND_CLOSEOUT") in text
