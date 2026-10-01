"""TASK 10 -- the sealed verdict semantics, as pure functions.

Two axes, and the whole point of the sealed REPAIR 3 is that they cannot leak
into each other:

    AXIS 1  PRIMARY_PREDICTIVE_VERDICT      confirmatory; the ONLY axis that
                                            can be supported or excluded
    AXIS 2  MECHANISM_SPECIFICITY_ASSESSMENT non-confirmatory; language only

`axis1_verdict()` has no parameter through which an Axis-2 result could reach
it. That is not a convention -- `tests/test_verdict.py` inspects the signature,
so an attempt to wire specificity into the Primary breaks the build.

Every guard of sealed M.1 is implemented: the C1 bar, the A1 sign requirement,
Conservative-cost positivity, the CI relative to M, and the half-width
falsification requirement. Every forbidden collapse of M.3 is a test.

Two inputs are deliberately NOT computed here, because the sealed text does not
define a constant for them and inventing one would be design freedom:
`power_gate_resolves_m` (the OD-3 Owner gate) and `n_shrunk_materially` (a
data-availability judgement). They are explicit inputs, and both default to the
non-excusing value.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from .bootstrap import Interval
from .errors import R1Error

SUPPORTED: Final = "PREDICTIVE_EFFECT_SUPPORTED_ON_SAMPLE"
EXCLUDED: Final = "PREDICTIVE_EFFECT_EXCLUDED_AT_MATERIALITY_M"
UNRESOLVED: Final = "PREDICTIVE_EFFECT_UNRESOLVED"
PARKED: Final = "PARKED"

ESTABLISHED: Final = "MECHANISM_SPECIFICITY_ESTABLISHED"
NOT_ESTABLISHED: Final = "MECHANISM_SPECIFICITY_NOT_ESTABLISHED"

KB_STATUS = {
    SUPPORTED: "supported",
    EXCLUDED: "falsified",
    UNRESOLVED: "unresolved",     # KB has no `insufficient_evidence` term
    PARKED: "not_promoted",
}

FORBIDDEN_CAUSAL_WORDS = ("demonstrated", "demonstrates", "confirmed",
                          "confirms", "caused", "causes", "causal", "proves",
                          "proven", "because of the release")


@dataclass(frozen=True)
class PrimaryEvidence:
    """Everything Axis 1 is allowed to see. Note what is absent: Axis 2."""
    base_interval: Interval
    conservative_point_estimate: float
    c1_clears_m: bool
    a1_sign_holds: bool
    materiality_m: float
    power_gate_resolves_m: bool = True     # OD-3; False => UNRESOLVED
    n_shrunk_materially: bool = False      # data availability => UNRESOLVED
    parked_reason: str | None = None


def axis1_verdict(evidence: PrimaryEvidence) -> str:
    """Sealed M.1. The ONLY function that may return SUPPORTED or EXCLUDED."""
    if evidence.parked_reason:
        return PARKED
    ci, m = evidence.base_interval, evidence.materiality_m

    if ci.clears(m) and not evidence.c1_clears_m and evidence.a1_sign_holds \
            and evidence.conservative_point_estimate > 0 \
            and evidence.power_gate_resolves_m \
            and not evidence.n_shrunk_materially:
        return SUPPORTED

    if ci.excludes_below(m) and evidence.power_gate_resolves_m \
            and not evidence.n_shrunk_materially:
        return EXCLUDED

    return UNRESOLVED


def axis2_verdict(d_interval: Interval) -> str:
    """Sealed K.2 / M.1: established iff the 95 % lower bound of D exceeds 0."""
    return ESTABLISHED if d_interval.lower > 0 else NOT_ESTABLISHED


@dataclass(frozen=True)
class Verdict:
    axis1: str
    axis2: str
    kb_status: str
    conclusion: str
    forbidden: tuple[str, ...]


_LANGUAGE = {
    (SUPPORTED, ESTABLISHED): (
        "PREDICTIVE_EFFECT_SUPPORTED_ON_SAMPLE + "
        "MECHANISM_SPECIFICITY_CONSISTENT_WITH_INFORMATION_DIFFUSION: the "
        "effect is materially larger on scheduled-release days than on matched "
        "non-release days, which is CONSISTENT WITH delayed information "
        "incorporation.",
        ("information diffusion demonstrated / confirmed / caused",
         "any causal claim -- causality is never claimed, even here")),
    (SUPPORTED, NOT_ESTABLISHED): (
        "PREDICTIVE_EFFECT_SUPPORTED_ON_SAMPLE + "
        "MECHANISM_SPECIFICITY_NOT_ESTABLISHED: a cost-surviving short-horizon "
        "continuation effect is present on release days at an executable "
        "decision point; it is NOT DISTINGUISHABLE from the same rule applied "
        "at the same clock minutes on non-release days. R1 provides NO "
        "EVIDENCE FOR INFORMATION DIFFUSION.",
        ("any sentence carrying 'information diffusion' as a supported finding",
         "describing R1 as an event-driven edge",
         "a KB Finding attributing the result to a release mechanism")),
    (EXCLUDED, ESTABLISHED): (
        "PREDICTIVE_EFFECT_EXCLUDED_AT_MATERIALITY_M. Axis 2 is REPORTED BUT "
        "NOT INTERPRETED: there is no effect whose specificity could matter.",
        ("'no effect' -- the claim is no effect of size >= M",
         "any extrapolation to FOMC, other instruments or other horizons")),
    (UNRESOLVED, ESTABLISHED): (
        "INSUFFICIENT_EVIDENCE (KB: unresolved). Axis 2 is reported as a "
        "descriptive number only.",
        ("treating a large point estimate as a near-miss",
         "using Axis 2 to argue the mechanism is 'probably there'")),
    (PARKED, ESTABLISHED): (
        "PARKED -- a data-integrity, authority or feasibility blocker prevented "
        "the test.",
        ("describing PARKED as a negative result",)),
}
_LANGUAGE[(EXCLUDED, NOT_ESTABLISHED)] = _LANGUAGE[(EXCLUDED, ESTABLISHED)]
_LANGUAGE[(UNRESOLVED, NOT_ESTABLISHED)] = _LANGUAGE[(UNRESOLVED, ESTABLISHED)]
_LANGUAGE[(PARKED, NOT_ESTABLISHED)] = _LANGUAGE[(PARKED, ESTABLISHED)]


def render_verdict(axis1: str, axis2: str) -> Verdict:
    """Sealed M.2: the matrix, and the exact allowed conclusion language."""
    try:
        conclusion, forbidden = _LANGUAGE[(axis1, axis2)]
    except KeyError as exc:
        raise R1Error(f"no sealed language for ({axis1}, {axis2})") from exc
    return Verdict(axis1=axis1, axis2=axis2, kb_status=KB_STATUS[axis1],
                   conclusion=conclusion, forbidden=forbidden)


def decide(evidence: PrimaryEvidence, d_interval: Interval | None) -> Verdict:
    """Both axes. Axis 2 is computed AFTER Axis 1 and cannot reach into it."""
    a1 = axis1_verdict(evidence)
    a2 = NOT_ESTABLISHED if d_interval is None else axis2_verdict(d_interval)
    return render_verdict(a1, a2)


def validate_language(text: str, verdict: Verdict) -> None:
    """Sealed M.3: mechanism language may never become causal language."""
    low = text.lower()
    for word in FORBIDDEN_CAUSAL_WORDS:
        if word in low:
            raise R1Error(
                f"forbidden causal language {word!r}: R1 may say CONSISTENT "
                f"WITH, never that a mechanism is demonstrated or causal "
                f"(sealed K.2, M.2, M.3).")
    if verdict.axis2 == NOT_ESTABLISHED and "information diffusion" in low \
            and "no evidence" not in low:
        raise R1Error(
            "MECHANISM_SPECIFICITY_NOT_ESTABLISHED: 'information diffusion' "
            "may not appear as a supported finding (sealed M.2).")
    if verdict.axis1 == EXCLUDED and "no effect" in low \
            and ">= m" not in low and "of size" not in low:
        raise R1Error("EXCLUDED means no effect OF SIZE >= M, not 'no effect'.")
    if verdict.axis1 == PARKED and "negative result" in low:
        raise R1Error("PARKED is not a negative result (sealed M.2).")
