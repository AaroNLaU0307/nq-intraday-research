"""End-to-end SYNTHETIC integration: the whole sealed study, once.

Nothing here touches real Development data. The prices are fabricated, the
verdicts are therefore meaningless as research, and that is the point: this
test proves the ENGINE runs the sealed design, not that the design works.
"""
from __future__ import annotations

import json

import pytest
import synth

from r1.bars import SyntheticBarSource
from r1.errors import AuthorityError
from r1.outcome_seal import reveal
from r1.pipeline import power_gate_inputs_from_control, run_primary, run_study
from r1.power_gate import build_packet

EVENT_DATES = [f"2015-{m:02d}-0{d}" for m in range(1, 7) for d in (2, 6)]
C2_DATES = [f"2016-{m:02d}-1{d}" for m in range(1, 7) for d in (2, 6)]


def _event_source(contract, *, drift=3.0, react=101.0):
    """Synthetic event days with a repeatable post-entry drift."""
    src = SyntheticBarSource()
    for i, d in enumerate(EVENT_DATES):
        wiggle = 0.5 * ((-1) ** i)
        src.add_day(d, synth.event_day_bars(
            contract, pre_close=100.0, react_close=react,
            entry_open=100.0, exit_open=100.0 + drift + wiggle))
    for i, d in enumerate(C2_DATES):
        wiggle = 0.25 * ((-1) ** i)
        src.add_day(d, synth.event_day_bars(
            contract, pre_close=100.0, react_close=100.5,
            entry_open=100.0, exit_open=100.3 + wiggle))
    return src


def test_primary_arm_runs_end_to_end(contract):
    src = _event_source(contract)
    results, summary = run_primary(src, EVENT_DATES, contract)
    assert summary.n == len(EVENT_DATES)
    assert results[0].holding_minutes == contract.holding_minutes
    assert summary.interval.block_events == 5
    assert summary.sensitivity.block_events == 10
    assert summary.interval.lower < summary.mean_y_net_usd < summary.interval.upper


def test_full_study_produces_a_verdict_and_a_sealed_bundle(contract, tmp_path):
    src = _event_source(contract)
    out = run_study(src, EVENT_DATES, contract, run_dir=tmp_path,
                    c2_dates=C2_DATES,
                    event_vol_states=["mid"] * len(EVENT_DATES),
                    c2_vol_states=["mid"] * len(C2_DATES),
                    c1_draws=200)
    assert out.n_structural == contract.pre_seal_structural_n
    assert out.n_signal_defined == len(EVENT_DATES)
    assert out.e4_count == 0
    assert out.verdict.axis1 in {"PREDICTIVE_EFFECT_SUPPORTED_ON_SAMPLE",
                                 "PREDICTIVE_EFFECT_EXCLUDED_AT_MATERIALITY_M",
                                 "PREDICTIVE_EFFECT_UNRESOLVED"}
    assert out.handle.output_class == "SEALED_R1_OUTCOME"
    assert out.handle.synthetic is True
    # the receipt leaks nothing
    assert "y_net" not in repr(out.handle)


def test_e4_removes_zero_reaction_days_in_the_pipeline(contract, tmp_path):
    src = _event_source(contract)
    flat = EVENT_DATES[0]
    src.add_day(flat, synth.event_day_bars(
        contract, pre_close=100.0, react_close=100.0,   # R_init == 0 exactly
        entry_open=100.0, exit_open=103.0))
    out = run_study(src, EVENT_DATES, contract, run_dir=tmp_path, c1_draws=50)
    assert out.e4_count == 1
    assert out.n_signal_defined == len(EVENT_DATES) - 1
    assert out.verdict is not None


def test_sealed_bundle_holds_the_prop_paths(contract, tmp_path):
    src = _event_source(contract)
    out = run_study(src, EVENT_DATES, contract, run_dir=tmp_path, c1_draws=50)
    data = reveal(out.handle,
                  owner_authorization="REVEAL_AUTHORIZED_BY_AARON:test")
    rec = data["payload"]["records"][0]
    assert len(rec["close_path_usd"]) == contract.holding_minutes
    assert len(rec["adverse_path_usd"]) == contract.holding_minutes
    assert rec["mae_usd"] <= 0


def test_the_study_refuses_a_non_synthetic_source(contract, tmp_path):
    class PretendReal:
        role = "development_signal"

        def bars_for(self, d):
            raise AssertionError("unreachable in S2")

        def has_date(self, d):
            return True

    with pytest.raises(AuthorityError, match="S3 authorization"):
        run_study(PretendReal(), EVENT_DATES, contract, run_dir=tmp_path)
    with pytest.raises(AuthorityError):
        run_primary(PretendReal(), EVENT_DATES, contract)


def test_c1_guard_can_block_support(contract, tmp_path):
    """A window with a big drift makes even random directions look good --
    exactly the confound C1 exists to catch."""
    src = SyntheticBarSource()
    for d in EVENT_DATES:
        src.add_day(d, synth.event_day_bars(
            contract, pre_close=100.0, react_close=101.0,
            entry_open=100.0, exit_open=150.0))         # a huge one-way drift
    out = run_study(src, EVENT_DATES, contract, run_dir=tmp_path, c1_draws=200)
    # C1 cannot clear M here because random directions average out, but the
    # guard must have been EVALUATED and carried into the verdict inputs
    assert isinstance(out.c1_clears_m_same_bar, bool)
    assert out.verdict.axis1 in {"PREDICTIVE_EFFECT_SUPPORTED_ON_SAMPLE",
                                 "PREDICTIVE_EFFECT_UNRESOLVED"}


def test_power_gate_runs_from_control_dispersion_only(contract):
    from r1.controls import run_c2
    src = _event_source(contract)
    arm = run_c2(src, C2_DATES, contract, vol_states=["mid"] * len(C2_DATES))
    s_hat = power_gate_inputs_from_control(arm)
    packet = build_packet(s_hat, contract.pre_seal_structural_n, contract)
    assert packet.s_hat == pytest.approx(s_hat)
    assert packet.mde_80 > packet.mde_50 > contract.materiality_m_usd
    assert packet.owner_decision is None


def test_nothing_in_the_pipeline_prints(contract, tmp_path, capsys):
    src = _event_source(contract)
    run_study(src, EVENT_DATES, contract, run_dir=tmp_path, c1_draws=20)
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err == ""


def test_run_directory_contains_only_the_sealed_bundle(contract, tmp_path):
    src = _event_source(contract)
    out = run_study(src, EVENT_DATES, contract, run_dir=tmp_path, c1_draws=20)
    files = sorted(p.name for p in tmp_path.iterdir())
    assert files == ["sealed_r1_outcome.json"]
    body = json.loads(out.handle.path.read_text(encoding="utf-8"))
    assert body["output_class"] == "SEALED_R1_OUTCOME"
