"""TASK 10 -- the sealed verdict semantics, tested across the full matrix."""
from __future__ import annotations

import inspect

import pytest

from r1.bootstrap import Interval
from r1.errors import R1Error
from r1.verdict import (ESTABLISHED, EXCLUDED, NOT_ESTABLISHED, PARKED,
                        SUPPORTED, UNRESOLVED, PrimaryEvidence, axis1_verdict,
                        axis2_verdict, decide, render_verdict, validate_language)

M = 3.99


def ci(lower, upper, point=None):
    return Interval(lower=lower, upper=upper,
                    point=point if point is not None else (lower + upper) / 2,
                    level=0.95, method="percentile", block_events=5,
                    resamples=10_000, seeds=(7, 13, 31))


def evidence(**kw):
    base = dict(base_interval=ci(5.0, 9.0), conservative_point_estimate=1.0,
                c1_clears_m=False, a1_sign_holds=True, materiality_m=M)
    base.update(kw)
    return PrimaryEvidence(**base)


# ---------------------------------------------------------------- axis 1
def test_supported_requires_every_guard():
    assert axis1_verdict(evidence()) == SUPPORTED


def test_c1_clearing_m_is_a_bar_to_support():
    assert axis1_verdict(evidence(c1_clears_m=True)) == UNRESOLVED


def test_a1_failing_in_sign_blocks_support():
    assert axis1_verdict(evidence(a1_sign_holds=False)) == UNRESOLVED


def test_conservative_cost_positivity_is_required():
    assert axis1_verdict(
        evidence(conservative_point_estimate=-0.01)) == UNRESOLVED


def test_interval_spanning_m_is_unresolved():
    assert axis1_verdict(evidence(base_interval=ci(1.0, 9.0))) == UNRESOLVED


def test_exclusion_requires_upper_below_m_and_half_width_below_m():
    assert axis1_verdict(evidence(base_interval=ci(-1.0, 2.0))) == EXCLUDED
    # upper < M but the interval is far too wide to have resolved anything
    wide = ci(-100.0, 3.0)
    assert wide.half_width > M
    assert axis1_verdict(evidence(base_interval=wide)) == UNRESOLVED


def test_power_gate_failure_forces_unresolved():
    assert axis1_verdict(evidence(power_gate_resolves_m=False)) == UNRESOLVED
    assert axis1_verdict(evidence(base_interval=ci(-1.0, 2.0),
                                  power_gate_resolves_m=False)) == UNRESOLVED


def test_material_sample_shrinkage_forces_unresolved():
    assert axis1_verdict(evidence(n_shrunk_materially=True)) == UNRESOLVED


def test_parked_overrides_everything():
    assert axis1_verdict(evidence(parked_reason="OD-1 declined")) == PARKED


def test_low_power_is_not_exclusion():
    """Sealed M.3: low power -> UNRESOLVED, never EXCLUDED."""
    v = axis1_verdict(evidence(base_interval=ci(-50.0, 2.0)))
    assert v == UNRESOLVED and v != EXCLUDED


# ---------------------------------------------------------------- axis 2
def test_axis2_established_iff_lower_bound_of_d_exceeds_zero():
    assert axis2_verdict(ci(0.5, 4.0)) == ESTABLISHED
    assert axis2_verdict(ci(0.0, 4.0)) == NOT_ESTABLISHED
    assert axis2_verdict(ci(-2.0, 4.0)) == NOT_ESTABLISHED


def test_axis2_cannot_reach_axis1():
    """Structural: Axis 1's signature has no Axis-2 parameter."""
    sig = inspect.signature(axis1_verdict)
    assert list(sig.parameters) == ["evidence"]
    fields = set(PrimaryEvidence.__dataclass_fields__)
    assert not {f for f in fields if "specificity" in f or "d_interval" in f
                or "c2" in f}


def test_axis2_established_with_axis1_unresolved_is_not_support():
    v = decide(evidence(base_interval=ci(1.0, 9.0)), ci(1.0, 5.0))
    assert v.axis1 == UNRESOLVED
    assert v.axis2 == ESTABLISHED
    assert "SUPPORTED" not in v.conclusion


# ---------------------------------------------------------------- matrix
@pytest.mark.parametrize("a1", [SUPPORTED, EXCLUDED, UNRESOLVED, PARKED])
@pytest.mark.parametrize("a2", [ESTABLISHED, NOT_ESTABLISHED])
def test_every_cell_of_the_matrix_renders(a1, a2):
    v = render_verdict(a1, a2)
    assert v.conclusion and v.forbidden
    assert v.kb_status in {"supported", "falsified", "unresolved",
                           "not_promoted"}


def test_kb_status_has_no_insufficient_evidence_term():
    assert render_verdict(UNRESOLVED, ESTABLISHED).kb_status == "unresolved"


def test_supported_without_specificity_says_no_evidence_for_diffusion():
    v = render_verdict(SUPPORTED, NOT_ESTABLISHED)
    assert "NO EVIDENCE FOR INFORMATION DIFFUSION" in v.conclusion
    assert "not distinguishable" in v.conclusion.lower()


def test_supported_with_specificity_says_consistent_with_not_caused():
    v = render_verdict(SUPPORTED, ESTABLISHED)
    assert "CONSISTENT WITH" in v.conclusion
    for word in ("demonstrated", "caused", "confirmed"):
        assert word not in v.conclusion.lower()


def test_unknown_cell_is_a_refusal():
    with pytest.raises(R1Error, match="no sealed language"):
        render_verdict("MADE_UP", ESTABLISHED)


# ---------------------------------------------------------------- language
def test_causal_language_is_refused():
    v = render_verdict(SUPPORTED, ESTABLISHED)
    validate_language(v.conclusion, v)                 # the sealed text passes
    for bad in ("information diffusion demonstrated",
                "the release caused the drift",
                "this confirms delayed incorporation"):
        with pytest.raises(R1Error, match="causal language"):
            validate_language(bad, v)


def test_diffusion_claim_is_refused_when_specificity_not_established():
    v = render_verdict(SUPPORTED, NOT_ESTABLISHED)
    with pytest.raises(R1Error, match="not be a supported finding|may not appear"):
        validate_language("evidence of information diffusion on release days", v)
    validate_language(v.conclusion, v)                 # the sealed wording is fine


def test_excluded_may_not_be_written_as_no_effect():
    v = render_verdict(EXCLUDED, NOT_ESTABLISHED)
    with pytest.raises(R1Error, match="OF SIZE"):
        validate_language("R1 finds no effect", v)
    validate_language("no effect of size >= M was found", v)


def test_parked_may_not_be_written_as_a_negative_result():
    v = render_verdict(PARKED, NOT_ESTABLISHED)
    with pytest.raises(R1Error, match="not a negative result"):
        validate_language("a negative result: the study was parked", v)
