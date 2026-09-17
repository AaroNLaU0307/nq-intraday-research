"""TASK 11 -- OD-3 power-gate machinery, and the proof that it is isolated."""
from __future__ import annotations

import inspect
from math import sqrt

import pytest

from r1 import power_gate
from r1.errors import AuthorityError, R1Error
from r1.power_gate import (PARK, PROCEED, Z_50, Z_80, build_packet,
                           prove_gate_independence, refuse_real_gate)


def test_packet_arithmetic_matches_sealed_i3(contract):
    p = build_packet(s_hat=80.0, n_final=252, contract=contract)
    se = 80.0 / sqrt(252)
    assert p.se_hat == pytest.approx(se)
    assert p.mde_50 == pytest.approx(contract.materiality_m_usd + Z_50 * se)
    assert p.mde_80 == pytest.approx(contract.materiality_m_usd + Z_80 * se)
    assert p.materiality_m_usd == contract.materiality_m_usd
    assert p.n_final == 252


def test_packet_flags_an_unresolving_design(contract):
    tight = build_packet(s_hat=1.0, n_final=252, contract=contract)
    assert tight.ci_half_width_would_exceed_m is False
    wide = build_packet(s_hat=500.0, n_final=252, contract=contract)
    assert wide.ci_half_width_would_exceed_m is True


def test_owner_decision_is_not_made_by_the_machinery(contract):
    p = build_packet(s_hat=80.0, n_final=252, contract=contract)
    assert p.owner_decision is None
    assert p.with_owner_decision(PROCEED).owner_decision == PROCEED
    assert p.with_owner_decision(PARK).owner_decision == PARK
    with pytest.raises(R1Error, match="owner decision"):
        p.with_owner_decision("MAYBE")
    assert p.owner_decision is None                    # original untouched


def test_gate_refuses_an_outcome_object(contract):
    class FakeTradeResult:
        y_net_usd = 4.2

    with pytest.raises(R1Error, match="never an outcome object"):
        build_packet(FakeTradeResult(), 252, contract)   # type: ignore[arg-type]


def test_gate_refuses_degenerate_inputs(contract):
    with pytest.raises(R1Error, match="positive"):
        build_packet(0.0, 252, contract)
    with pytest.raises(R1Error, match="at least 2"):
        build_packet(80.0, 1, contract)


def test_real_gate_is_refused_in_s2():
    with pytest.raises(AuthorityError, match="S2 BUILD authorizes neither"):
        refuse_real_gate()


# ------------------------------------------------- the independence proof
def test_dependency_graph_has_no_route_to_a_primary_result():
    proof = prove_gate_independence()
    assert proof["independent"] is True, proof["findings"]
    for banned in ("r1.trade", "r1.verdict", "r1.signal", ".trade", ".verdict",
                   ".signal", ".events", ".controls"):
        assert banned not in proof["imports"]


def test_no_gate_function_accepts_an_outcome_type():
    for name, fn in vars(power_gate).items():
        if not callable(fn) or getattr(fn, "__module__", "") != power_gate.__name__:
            continue
        try:
            sig = inspect.signature(fn)
        except (TypeError, ValueError):
            continue
        for param in sig.parameters.values():
            ann = str(param.annotation)
            assert "TradeResult" not in ann and "Verdict" not in ann


def test_independence_proof_can_fail(tmp_path):
    """The proof is demonstrated able to fail (fabricated poisoned module)."""
    poisoned = tmp_path / "poisoned_gate.py"
    poisoned.write_text(
        "from r1.trade import TradeResult\n"
        "def gate(x: TradeResult):\n"
        "    return x.y_net_usd\n", encoding="utf-8")
    proof = prove_gate_independence([poisoned])
    assert proof["independent"] is False
    assert proof["findings"]


def test_packet_carries_the_outcome_blind_note(contract):
    p = build_packet(s_hat=80.0, n_final=252, contract=contract)
    assert "outcome-blind" in p.note
    assert "control C2" in p.note


def test_gate_input_comes_from_control_dispersion_only(contract):
    """End to end on SYNTHETIC control data: dispersion -> packet, no event arm."""
    import synth
    from r1.controls import c2_dispersion, run_c2

    dates = ["2015-01-05", "2015-01-06", "2015-01-07", "2015-01-08"]
    src = synth.source_with(contract, {
        d: synth.event_day_bars(contract, pre_close=100.0, react_close=101.0,
                                entry_open=100.0, exit_open=100.0 + i)
        for i, d in enumerate(dates)})
    arm = run_c2(src, dates, contract, vol_states=["mid"] * len(dates))
    s_hat = c2_dispersion(arm)
    packet = build_packet(s_hat, len(dates), contract)
    assert packet.s_hat == pytest.approx(s_hat)
    assert packet.owner_decision is None
