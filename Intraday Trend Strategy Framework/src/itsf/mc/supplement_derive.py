"""Assemble a B_DERIVE context, and report what those five gates say.

THE SPLIT THIS MODULE EXISTS TO MAKE, and it is cleaner than I expected
before measuring it.

The five B_DERIVE gates read exactly two fields A_PRECHECK does not:
`authority` and `prepared`. Of those:

    derive_supplement_authority(prepared)   PURE given a prepared input --
                                            its own docstring says "without
                                            any repository read"
    prepare_real_mc_input()                 the ONLY thing here that touches
                                            real data, and it is gate-first:
                                            `authorize_real_mc` raises today,
                                            so it is unreachable

So this module takes `prepared` as an ARGUMENT and never produces one. That
is the whole design: assembly can be tested, reviewed and reasoned about
against synthetic inputs, while the single step that spends anything stays
behind the gate that already blocks it. Nothing here calls
`prepare_real_mc_input`, and nothing here can reach Development data.

WHY REPORT RATHER THAN RUN. Same reason as `supplement_precheck`:
`run_stage_gates` stops at the first refusal, which is right for a run and
useless for answering "how far is there to go". These run all five and keep
going.

WHAT THIS DOES NOT DO. It does not change either production entry, it does
not mint anything for production, and passing all five gates here proves
nothing about a real run -- a synthetic prepared input is refused by
`custody_authority_production` by design, which is exactly what makes it safe
to point this at anything.
"""
from __future__ import annotations

import dataclasses as _dc

from . import supplement_contract as sc
from . import supplement_runner as sr

__all__ = ["DeriveReport", "assemble_derive_context", "run_derive_gates"]


@_dc.dataclass(frozen=True, slots=True)
class DeriveReport:
    """What the five B_DERIVE gates said, in the contract's own order."""
    results: tuple                       # ((gate_name, None|str), ...)
    authority_minted: bool
    mint_refusal: str = ""

    @property
    def passed(self) -> bool:
        return self.authority_minted and all(
            detail is None for _name, detail in self.results)

    @property
    def first_refusal(self):
        for name, detail in self.results:
            if detail is not None:
                return (name, detail)
        return None


def assemble_derive_context(precheck_ctx, prepared):
    """Add `authority` and `prepared` to an A_PRECHECK context.

    Returns `(ctx, mint_refusal)`. The authority is DERIVED from the prepared
    input handed in -- this function does not read a repository, does not
    open market data, and does not create the prepared input. If deriving
    refuses, the context still comes back with `authority=None` so the gates
    can refuse on it rather than this function deciding on their behalf.
    """
    from . import supplement_authority as sa

    authority, refusal = None, ""
    try:
        authority = sa.derive_supplement_authority(
            prepared, supplement_id=precheck_ctx.supplement_id)
    except Exception as exc:                     # noqa: BLE001
        refusal = "%s: %s" % (type(exc).__name__, exc)

    ctx = _dc.replace(precheck_ctx, authority=authority, prepared=prepared)
    return ctx, refusal


def run_derive_gates(precheck_ctx, prepared) -> DeriveReport:
    """Run the five B_DERIVE gates and report EVERY result."""
    ctx, refusal = assemble_derive_context(precheck_ctx, prepared)
    results = []
    for name in sc.GATE_TABLE["B_DERIVE"]:
        try:
            sr.GATES[name](ctx)
            results.append((name, None))
        except Exception as exc:                 # noqa: BLE001
            results.append((name, "%s: %s" % (type(exc).__name__, exc)))
    return DeriveReport(tuple(results), ctx.authority is not None, refusal)
