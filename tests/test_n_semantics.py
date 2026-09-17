"""Two different n's, and two different failure modes.

    PRE_SEAL_STRUCTURAL_N = 252      fixed by PSMV before the seal. Execution
                                     must reproduce it EXACTLY. Failing to is a
                                     RUN_INTEGRITY_FAILURE -- a broken run, not
                                     a researcher judgement that the sample
                                     "materially shrank" and not an UNRESOLVED
                                     verdict with a smaller n.

    POST_SEAL_SIGNAL_DEFINED_N       = 252 - E4_COUNT. E4 removes exact-zero
                                     reactions; it is prespecified, it happens
                                     AFTER structural eligibility, and it is
                                     not structural-data shrinkage.
"""
from __future__ import annotations

import inspect
from dataclasses import replace

import pytest
import synth

from r1.errors import RunIntegrityError
from r1.events import ITSF_CALENDAR_PATH, build_universe
from r1.signal import apply_e4

requires_calendar = pytest.mark.skipif(
    not ITSF_CALENDAR_PATH.exists(),
    reason="frozen F10 calendar not present on this machine")


@requires_calendar
def test_structural_universe_reproduces_exactly(contract):
    assert build_universe(contract).n == contract.pre_seal_structural_n == 252


@requires_calendar
def test_failing_to_reproduce_the_sealed_universe_is_a_run_integrity_failure(
        contract):
    """Not a smaller sample -- a broken run."""
    drifted = replace(contract, pre_seal_structural_n=251)
    with pytest.raises(RunIntegrityError, match="RUN_INTEGRITY_FAILURE"):
        build_universe(drifted)


@requires_calendar
def test_the_integrity_message_names_the_distinction(contract):
    drifted = replace(contract, pre_seal_structural_n=999)
    with pytest.raises(RunIntegrityError) as exc:
        build_universe(drifted)
    text = str(exc.value)
    assert "reproduce EXACTLY" in text
    assert "POST_SEAL_SIGNAL_DEFINED_N" in text
    assert "not structural shrinkage" in text


def test_e4_is_a_separate_prespecified_stage(contract):
    """E4 subtracts from the structural n; it never redefines it."""
    dates = [f"2015-0{i}-02" for i in range(1, 5)]
    src = synth.source_with(contract, {
        dates[0]: synth.event_day_bars(contract, pre_close=100.0,
                                       react_close=101.0, entry_open=100.0,
                                       exit_open=101.0),
        dates[1]: synth.event_day_bars(contract, pre_close=100.0,
                                       react_close=100.0, entry_open=100.0,
                                       exit_open=101.0),   # exact zero -> E4
        dates[2]: synth.event_day_bars(contract, pre_close=100.0,
                                       react_close=99.0, entry_open=100.0,
                                       exit_open=101.0),
        dates[3]: synth.event_day_bars(contract, pre_close=100.0,
                                       react_close=100.0, entry_open=100.0,
                                       exit_open=101.0)})  # exact zero -> E4
    res = apply_e4(src, dates, contract,
                   structural_n=contract.pre_seal_structural_n)
    assert res.pre_seal_structural_n == 252          # structural n is untouched
    assert res.e4_count == 2
    assert res.post_seal_signal_defined_n == 252 - 2
    assert len(res.signals) == 2


def test_no_numerical_threshold_for_shrinkage_exists_anywhere():
    """The review's rule: never invent a 'materially shrank n' constant."""
    from r1 import events, pipeline, verdict
    for module in (events, pipeline):
        src = inspect.getsource(module)
        assert "shrink" not in src.lower() or "shrunk" in src.lower()
        for banned in ("0.9", "0.95 * n", "min_n", "n_floor", "shrink_pct"):
            assert banned not in src, (module.__name__, banned)
    # the verdict engine keeps the sealed M.1 CONDITION as an explicit input,
    # with no threshold attached and the non-excusing default
    field = verdict.PrimaryEvidence.__dataclass_fields__["n_shrunk_materially"]
    assert field.default is False


def test_the_pipeline_never_passes_a_shrinkage_judgement(contract, tmp_path):
    from r1.pipeline import run_study
    assert "n_shrunk_materially" not in inspect.signature(run_study).parameters
    assert "n_shrunk_materially=False" in inspect.getsource(run_study)
