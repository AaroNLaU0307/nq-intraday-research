"""TASK 2 -- the event universe loader.

The structural test reproduces PRE_SEAL_STRUCTURAL_N = 252 while computing NO
R_init, NO direction, NO return and NO P&L: nothing in this module imports
`r1.signal` or `r1.trade`.
"""
from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

from conftest import refresh_digest
from r1.errors import CalendarError, SealIdentityError
from r1.events import (ITSF_CALENDAR_PATH, build_universe, count_by_type,
                       era_of, load_calendar)
from r1.invariants import scan_no_release_time_inference

CALENDAR_PRESENT = ITSF_CALENDAR_PATH.exists()
requires_calendar = pytest.mark.skipif(
    not CALENDAR_PRESENT, reason="frozen F10 calendar not present on this machine")


@requires_calendar
def test_reproduces_the_sealed_structural_n(contract):
    u = build_universe(contract)
    assert u.n == contract.pre_seal_structural_n == 252
    assert count_by_type(u.events) == {"CPI": 118, "NFP": 134}


@requires_calendar
def test_funnel_is_conserved(contract):
    u = build_universe(contract)
    f = u.funnel
    assert f["E0_cpi_or_nfp_calendar_events"] == 277
    assert f["E1_minus_any_fomc_calendar_entry"] == 258
    assert f["E2_minus_exact_roll_transition_sessions"] == 258
    assert f["E3_minus_missing_required_structural_anchors"] == 252
    assert len(u.events) + len(u.excluded) == 277


@requires_calendar
def test_structural_path_computes_no_signal_and_no_pnl():
    """The loader must not even be able to reach the outcome path."""
    tree = ast.parse(Path("r1/events.py").read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
        elif isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
    assert not {".signal", ".trade", ".controls", "r1.signal", "r1.trade"} \
        & imported


@requires_calendar
def test_event_universe_digest_is_stable_and_order_independent(contract):
    a = build_universe(contract)
    b = build_universe(contract)
    assert a.digest() == b.digest()
    assert len(a.digest()) == 64


@requires_calendar
def test_l7_mask_is_invariant_under_outcome_permutation(contract):
    """L-7: the inclusion mask is a pure function of calendar + availability."""
    import random
    u = build_universe(contract)
    outcomes = [random.Random(i).random() for i in range(u.n)]
    random.Random(1).shuffle(outcomes)
    again = build_universe(contract)
    assert again.dates == u.dates          # outcomes cannot have touched it


@requires_calendar
def test_excluded_dates_carry_their_reason(contract):
    u = build_universe(contract)
    assert u.excluded["2010-06-17"].startswith("E3_adr14")
    assert u.excluded["2012-04-06"] == "E3_anchor_missing_O_0929"
    assert u.excluded["2017-04-14"] == "E3_no_bars_on_date"
    assert u.excluded["2013-09-17"] == "E1_fomc_coexistence"


@requires_calendar
def test_era_assignment(contract):
    u = build_universe(contract)
    eras = {era_of(contract, e) for e in u.events}
    assert eras == {"2010-2013", "2014-2017", "2018-2021"}


# ---------------------------------------------------------------- mutations
@requires_calendar
def test_l11_calendar_digest_mismatch_fails_closed(contract):
    bad = replace(contract, event_calendar_sha256="0" * 64)
    with pytest.raises(SealIdentityError, match="L-11"):
        load_calendar(bad)


def test_l2_unattested_release_time_is_refused(contract, tmp_path):
    """A BLS row whose time is not officially recorded is a refusal (L-2)."""
    csv_path = tmp_path / "f10_events.csv"
    csv_path.write_text(
        "date_et,event_type,release_time_status,is_cpi_release_day,"
        "is_nfp_release_day\n"
        "2015-01-02,CPI,inferred_from_convention,true,false\n",
        encoding="utf-8")
    digest = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    bad = replace(contract, event_calendar_sha256=digest)
    with pytest.raises(CalendarError, match="release_time_status"):
        load_calendar(bad, csv_path)


def test_l2_empty_time_column_raises_rather_than_defaulting(contract, tmp_path):
    csv_path = tmp_path / "f10_events.csv"
    csv_path.write_text(
        "date_et,event_type,release_time_status,is_cpi_release_day,"
        "is_nfp_release_day\n"
        "2015-01-02,NFP,,false,true\n", encoding="utf-8")
    digest = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    bad = replace(contract, event_calendar_sha256=digest)
    with pytest.raises(CalendarError):
        load_calendar(bad, csv_path)


def test_l3_no_release_time_literal_in_the_event_path():
    assert scan_no_release_time_inference() == ()


def test_l3_scan_can_fail(tmp_path):
    """The L-3 scan is demonstrated able to fail (fabricated fixture)."""
    poisoned = tmp_path / "poisoned_events.py"
    poisoned.write_text(
        'RELEASE = "08:30"\n'
        'def load(default_release_time="08:30"):\n'
        '    return default_release_time\n', encoding="utf-8")
    findings = scan_no_release_time_inference(paths=(poisoned,))
    assert findings, "the L-3 scan failed to catch a planted release-time default"


def test_missing_calendar_is_a_refusal(contract, tmp_path):
    with pytest.raises(CalendarError, match="not found"):
        load_calendar(contract, tmp_path / "does_not_exist.csv")


def test_empty_calendar_is_a_refusal(contract, tmp_path):
    csv_path = tmp_path / "empty.csv"
    csv_path.write_text("date_et,event_type,release_time_status,"
                        "is_cpi_release_day,is_nfp_release_day\n",
                        encoding="utf-8")
    bad = replace(contract,
                  event_calendar_sha256=hashlib.sha256(
                      csv_path.read_bytes()).hexdigest())
    with pytest.raises(CalendarError, match="empty"):
        load_calendar(bad, csv_path)


@requires_calendar
def test_mutating_the_sealed_exclusion_set_is_caught(contract, sealed_copy):
    """If the sealed E3 set is tampered with, n stops reproducing."""
    rel = "artifacts/PSMV_STRUCTURAL_REPORT.json"
    p = sealed_copy / rel
    data = json.loads(p.read_text(encoding="utf-8"))
    detail = data["event_funnel"]["E3_minus_missing_required_structural_anchors"]
    detail["removed_detail"] = detail["removed_detail"][:-1]
    detail["removed"] = 5
    p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    refresh_digest(sealed_copy, rel)
    from r1.contract import load_sealed_contract
    with pytest.raises(SealIdentityError):
        load_sealed_contract(sealed_copy)
