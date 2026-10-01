"""TASK 13 -- L-1 ... L-12, each with a positive test AND a mutation test.

A guard that has never been shown to fail is not a guard, so every static scan
here is also pointed at a deliberately poisoned fixture and must catch it. The
fixtures are fabricated files in tmp_path; no R1 module is ever poisoned.
"""
from __future__ import annotations

import pytest
import synth

from r1.errors import (AnchorError, AuthorityError, CalendarError, LeakageError,
                       RoleError, SealIdentityError)
from r1.invariants import (INVARIANTS, scan_no_duplicated_constants,
                           scan_no_parameter_scan, scan_no_raw_decoder_import,
                           scan_no_release_time_inference,
                           verify_l13_still_holds)

DATE = "2015-01-02"


def test_every_sealed_invariant_l1_to_l12_is_present():
    ids = [i.id for i in INVARIANTS]
    assert ids == [f"L-{n}" for n in range(1, 13)]
    for inv in INVARIANTS:
        assert inv.title and inv.enforced_by
        assert inv.kind in {"structural", "runtime", "static"}


def test_static_invariants_pass_on_the_live_package():
    for inv in INVARIANTS:
        if inv.check is not None:
            assert inv.check() is True, inv.id


# ------------------------------------------------------------ L-1 / L-4 / L-5
def test_l1_future_bar_leakage_is_impossible(contract):
    from r1.signal import build_signal
    a = build_signal(synth.simple_event_source(contract, [DATE]), DATE, contract)
    b = build_signal(synth.simple_event_source(contract, [DATE],
                                               noise_after_signal=500.0),
                     DATE, contract)
    assert (a.r_init, a.d_event) == (b.r_init, b.d_event)


def test_l1_mutation_the_window_can_refuse(contract):
    from r1.bars import SignalWindow
    w = SignalWindow(synth.simple_event_source(contract, [DATE]), DATE, contract)
    with pytest.raises(LeakageError):
        w.get(contract.signal_complete_minute)


def test_l4_pnl_before_entry_is_impossible(contract):
    from r1.bars import TradeWindow
    w = TradeWindow(synth.simple_event_source(contract, [DATE]), DATE, contract)
    with pytest.raises(LeakageError):
        w.get(contract.entry_minute - 1)


def test_l5_trailing_only(contract):
    from r1.bars import TrailingHistory
    hist = TrailingHistory(synth.simple_event_source(contract, [DATE]), DATE,
                           [DATE, "2014-12-31"])
    assert hist.dates == ("2014-12-31",)
    with pytest.raises(LeakageError):
        hist.bars_for(DATE)


# ------------------------------------------------------------ L-2 / L-3 / L-11
def test_l2_and_l11_are_enforced_at_load(contract, tmp_path):
    import hashlib
    from dataclasses import replace

    from r1.events import load_calendar
    csv_path = tmp_path / "cal.csv"
    csv_path.write_text("date_et,event_type,release_time_status,"
                        "is_cpi_release_day,is_nfp_release_day\n"
                        "2015-01-02,CPI,estimated,true,false\n",
                        encoding="utf-8")
    with pytest.raises(SealIdentityError):                       # L-11 first
        load_calendar(contract, csv_path)
    ok_digest = replace(contract, event_calendar_sha256=hashlib.sha256(
        csv_path.read_bytes()).hexdigest())
    with pytest.raises(CalendarError):                           # then L-2
        load_calendar(ok_digest, csv_path)


def test_l3_scan_positive_and_mutation(tmp_path):
    assert scan_no_release_time_inference() == ()
    poisoned = tmp_path / "p.py"
    poisoned.write_text('T = "08:30"\n', encoding="utf-8")
    assert scan_no_release_time_inference(paths=(poisoned,))


# ------------------------------------------------------------ L-6 / L-7
def test_l6_event_set_frozen(contract):
    from r1.run_identity import assert_event_set_frozen, build_run_identity
    ident = build_run_identity(contract, run_label="synthetic",
                               code_commit="deadbeef",
                               data_manifest_sha256="0" * 64,
                               event_universe_digest="abc")
    assert_event_set_frozen(ident, "abc")
    with pytest.raises(SealIdentityError, match="L-6"):
        assert_event_set_frozen(ident, "def")


def test_l7_inclusion_mask_ignores_outcomes(contract):
    """The mask is built before any outcome exists and never sees one."""
    import ast
    import inspect

    from r1 import events
    tree = ast.parse(inspect.getsource(events.build_universe))
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    assert not {"y_net", "y_net_usd", "outcome", "pnl", "returns"} & names


# ------------------------------------------------------------ L-8
def test_l8_no_parameter_scan_positive_and_mutation(tmp_path):
    assert scan_no_parameter_scan() == ()
    poisoned = tmp_path / "p.py"
    poisoned.write_text(
        "def primary():\n"
        "    for entry_minute in candidate_entry_times:\n"
        "        yield entry_minute\n"
        "k = 2\n", encoding="utf-8")
    findings = scan_no_parameter_scan(paths=(poisoned,))
    assert any("iterates over" in f for f in findings)
    assert any("assigns k" in f for f in findings)


def test_l8_constants_live_only_in_the_contract(tmp_path):
    assert scan_no_duplicated_constants() == ()
    poisoned = tmp_path / "p.py"
    poisoned.write_text("ENTRY = 513\nM = 3.99\n", encoding="utf-8")
    assert len(scan_no_duplicated_constants(paths=(poisoned,))) == 2


# ------------------------------------------------------------ L-9 / L-10
def test_l9_role_boundary(contract):
    from r1.roles import DataRole, check_role
    assert check_role(DataRole.DEVELOPMENT_SIGNAL) is DataRole.DEVELOPMENT_SIGNAL
    with pytest.raises(RoleError):
        check_role(DataRole.INTERNAL_VALIDATION_SIGNAL)
    with pytest.raises(RoleError):
        check_role(DataRole.PHYSICAL_LOCKBOX)


def test_l10_no_raw_decoder_import_positive_and_mutation(tmp_path):
    assert scan_no_raw_decoder_import() == ()
    poisoned = tmp_path / "p.py"
    poisoned.write_text("import databento as dbn\n", encoding="utf-8")
    assert scan_no_raw_decoder_import(paths=(poisoned,))


def test_l10_no_raw_bbo_path_exists():
    """R1 reads the DERIVED spread table; raw BBO has no code path at all."""
    import ast
    from pathlib import Path
    for p in Path("r1").glob("*.py"):
        tree = ast.parse(p.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                assert "bbo-1s" not in node.value, p.name


# ------------------------------------------------------------ L-12
def test_l12_missing_anchor_is_na_never_substituted(contract):
    from r1.bars import TradeWindow
    bars = [b for b in synth.event_day_bars(
        contract, pre_close=100.0, react_close=101.0, entry_open=101.0,
        exit_open=102.0) if b.minute != contract.exit_minute]
    w = TradeWindow(synth.source_with(contract, {DATE: bars}), DATE, contract)
    with pytest.raises(AnchorError, match="No forward fill"):
        w.require(contract.exit_minute)


# ------------------------------------------------------------ L-13 (historical)
def test_l13_psmv_purity_still_holds():
    assert verify_l13_still_holds() == ()


# ------------------------------------------------------------ authority
def test_no_real_data_path_is_reachable():
    from r1.bars import DevelopmentBarSource
    with pytest.raises(AuthorityError):
        DevelopmentBarSource("anything")


def test_iv_and_lockbox_raise_before_any_file_read(monkeypatch):
    """The refusal is on the ROLE, so no forbidden path is ever constructed."""
    import builtins

    from r1.roles import DataRole, resolve_window
    opened: list = []
    real_open = builtins.open
    monkeypatch.setattr(builtins, "open",
                        lambda *a, **k: (opened.append(a), real_open(*a, **k))[1])
    for role in (DataRole.INTERNAL_VALIDATION_SIGNAL, DataRole.PHYSICAL_LOCKBOX):
        with pytest.raises(RoleError):
            resolve_window(role)
    assert opened == []
