"""Assemble a C_BUILD context, and report what those five gates say.

THE THIRD AND LAST STAGE, built the same way as the other two: this module
RECEIVES a `CBuildOutcome` and never produces one. `day_strata_pipeline
.run_c_build` is what produces it, and it takes the universe, the method and
the day set as arguments -- so producing an outcome is a caller's decision
with a caller's inputs, not something this module can do on its own.

WHAT THE FIVE GATES ACTUALLY DO. All five route through
`supplement_runner._classify_c_build_1`, which CLASSIFIES the producer's
outcome rather than re-checking it. The invariant lives in
`day_strata_rows`; the mapping from its refusal code to exactly one gate
lives in `day_strata_classify`; the gate reports it in the F1/F2 vocabulary.
A second implementation of the invariant here is the defect that doctrine
exists to prevent.

ABSENCE IS A REFUSAL. With no outcome attached, a gate has classified
nothing, and passing would put "no defect found" on record about a build that
never ran. That is why this module has no default outcome and no way to
proceed without one -- the same reason `supplement_derive` refuses to invent
a prepared input.

ONLY FOUR OF THE FIVE ARE CLASSIFIERS -- measured, and the count has already
moved once. `row_schema_blind`, `day_set_exact`, `rows_digest_recompute`
(C_BUILD_1) and, since 2026-09-01, `seal_staging_partial` (C_BUILD_2) route
through the classifier and pass once an outcome is attached. Only
`archive_policy_a` (C_BUILD_3) calls `_fail` UNCONDITIONALLY, and that is a
RULING rather than unfinished work: `ROUTER_OF` gives its outcome to Router B,
because routing it as an ordinary gate sends a refusal to F2 while ratified
`ND1_ARCHIVE_FAILURE_POLICY=A` requires A1.

That distinction is the whole reason this reports rather than runs. "Refused"
is one word for two different situations, and only one of them is answered by
attaching an outcome.

WHAT PASSING HERE WOULD AND WOULD NOT MEAN. Green C_BUILD_1 gates over an
outcome built from synthetic inputs say the CLASSIFICATION machinery works.
They say nothing about a real run, because the outcome would have been built
from synthetic rows. The rehearsal makes the same disclaimer for the same
reason.
"""
from __future__ import annotations

import dataclasses as _dc

from . import supplement_contract as sc
from . import supplement_runner as sr

__all__ = ["BuildReport", "assemble_build_context", "run_build_gates"]


@_dc.dataclass(frozen=True, slots=True)
class BuildReport:
    """What the five C_BUILD gates said, in the contract's own order."""
    results: tuple                       # ((gate_name, None|str), ...)
    outcome_attached: bool
    producer_failure: str = ""           # the outcome's own refusal, if any

    @property
    def passed(self) -> bool:
        return self.outcome_attached and all(
            detail is None for _name, detail in self.results)

    @property
    def first_refusal(self):
        for name, detail in self.results:
            if detail is not None:
                return (name, detail)
        return None


def assemble_build_context(derive_ctx, outcome):
    """Attach a `CBuildOutcome` to a B_DERIVE context.

    `outcome` is REQUIRED and has no default. A default would let a caller
    omit it and leave the gates classifying nothing, which they refuse --
    correctly, but the refusal would then be about this module's convenience
    rather than about the build."""
    return _dc.replace(derive_ctx, c_build_outcome=outcome)


def run_build_gates(derive_ctx, outcome) -> BuildReport:
    """Run the five C_BUILD gates and report EVERY result."""
    ctx = assemble_build_context(derive_ctx, outcome)
    failure = getattr(outcome, "failure", None)
    detail = ""
    if failure is not None:
        # Read the fields DIRECTLY. `getattr(f, "stage", "?")` would render a
        # renamed field as "?" and keep going -- a check that matches nothing
        # looking exactly like one that matched the right thing, which is the
        # failure shape this repository keeps meeting. An AttributeError here
        # is the correct outcome of a rename.
        detail = "%s/%s: %s" % (failure.stage, failure.gate, failure.code)
    results = []
    for name in sc.GATE_TABLE["C_BUILD"]:
        try:
            sr.GATES[name](ctx)
            results.append((name, None))
        except Exception as exc:                 # noqa: BLE001
            results.append((name, "%s: %s" % (type(exc).__name__, exc)))
    return BuildReport(tuple(results), outcome is not None, detail)
