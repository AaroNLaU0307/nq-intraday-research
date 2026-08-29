"""From a C_BUILD refusal to the registry row it WOULD become.

WHAT WAS MISSING. `day_strata_rows` refuses, `day_strata_pipeline` carries
the refusal, `day_strata_classify` names its gate, and
`supplement_runner.plan_failure_event` turns a `GateFailure` into an F1 or
an F2. Nothing joined the last two. A failure could be classified and then
had nothing to become.

NOTHING HERE APPENDS. `PlannedEvent` is a description of a row an
authorized run would write; forming one writes nothing, and this module
has no filesystem access at all. The eight authorization fields are NO, so
the row cannot legitimately be appended today -- which is exactly why the
DESCRIPTION is worth having now: it makes the frozen state auditable, and
when authorization arrives the append is the only new thing.

THE ONE FIELD THAT CAN CARRY A LIE. `plan_failure_event` decides F1 vs F2
by the P3 boundary, and F1's payload contains the literal
`consumption_statement="nothing consumed"`. Get the boundary wrong in the
False direction and the registry records, in its own words, that a run
which may have consumed its authorization consumed nothing. The contract
saw this coming -- `decide_evidence_write_failure` takes `has_p3` as an
ARGUMENT precisely so no component can set a flag it then trusts -- but
nothing ever derived it. `p3_boundary` is that derivation, and it refuses
where it cannot prove.

WHY `chain.problem` MUST REFUSE RATHER THAN READ FALSE. A poisoned
resolution comes back with `started=False` because that is the dataclass
default, not because anybody looked. Reading it as "no P3" is the false
direction above, reached by doing nothing wrong -- just by trusting a
default. Unknown is not not-started.

`error_class` IS THE EXCEPTION CLASS NAME. Measured against every existing
`_fail` site: they pass `RunGateError`, `SupplementRunnerError`,
`FrozenTamperError`. The producer's failure CODE is a different
vocabulary and goes in `detail`. Putting the code in `error_class` would
write a word into the registry that no other failure event uses, and the
field would silently mean two things.
"""

from __future__ import annotations

__all__ = ["FailurePlanError", "p3_boundary", "plan_for_c_build_failure",
           "ERROR_CLASS_OF_PRODUCER_REFUSAL"]

#: What a producer refusal IS, in the vocabulary every other failure event
#: uses: the exception class name. Not the code -- see the module docstring.
#:
#: DERIVED from the class rather than spelled, so renaming the exception
#: cannot leave the registry recording a class name that no longer exists.
#: This project produced five stale hand-written mirrors in one day.
from .day_strata_rows import DayStrataRowsError as _ProducerRefusal

ERROR_CLASS_OF_PRODUCER_REFUSAL = _ProducerRefusal.__name__

_C_BUILD = "C_BUILD"


class FailurePlanError(Exception):
    """The row cannot be described. Refuses; never guesses a boundary."""


def p3_boundary(chain) -> bool:
    """Whether this supplement has crossed P3. PROVEN, never declared.

    Refuses on anything short of proof, because the two answers are not
    symmetric: a wrong True asks for a residue path a pre-start run has
    none of and stops, while a wrong False writes "nothing consumed" into
    the registry about a run that may have consumed everything. Only one
    of those is recoverable by reading the row.
    """
    if chain is None:
        raise FailurePlanError(
            "no chain resolution was supplied, so the P3 boundary is "
            "unknown. It is not False: an absent resolution is a thing "
            "nobody looked at, and F1 would claim nothing was consumed.")
    problem = getattr(chain, "problem", "")
    if problem:
        raise FailurePlanError(
            "the registry resolution is poisoned (%s), so `started` is the "
            "dataclass default rather than an observation. Reading it as "
            "'no P3' would let F1 record 'nothing consumed' about a run "
            "whose consumption nobody can see. Resolve the registry first."
            % problem)
    started = bool(getattr(chain, "started", False))
    witness = "P3" in tuple(getattr(chain, "short_ids", ()))
    if started != witness:
        raise FailurePlanError(
            "the chain says started=%r but its events %s the P3 row. These "
            "are two derivations of one fact and they disagree, so neither "
            "can be used to choose between F1 and F2."
            % (started, "carry" if witness else "do not carry"))
    return started


def plan_for_c_build_failure(outcome, *, supplement_id: str, chain,
                             incident_id: str, attempts_dir: str = "",
                             residue_path: str = ""):
    """The F1 or F2 row a C_BUILD refusal would become. Appends nothing.

    `outcome` is a `day_strata_pipeline.CBuildOutcome`. A SUCCEEDING
    outcome refuses here rather than producing an empty failure row: a
    failure event describing a run that did not fail is a false record,
    and it is the direction a caller reaches by forgetting to check.
    """
    from .supplement_runner import GateFailure, plan_failure_event

    failure = getattr(outcome, "failure", None)
    if failure is None:
        raise FailurePlanError(
            "this outcome carries no failure, so there is no failure event "
            "to describe. A row saying a successful build failed is worse "
            "than no row.")
    if not getattr(failure, "gate", ""):
        raise FailurePlanError(
            "the failure names no gate, and the gate name is half of what "
            "an F1 row carries.")

    has_p3 = p3_boundary(chain)
    gate_failure = GateFailure(
        stage=_C_BUILD,
        gate_name=failure.gate,
        error_class=ERROR_CLASS_OF_PRODUCER_REFUSAL,
        detail="%s: %s" % (failure.code, failure.detail))
    return plan_failure_event(
        gate_failure, supplement_id=supplement_id, incident_id=incident_id,
        has_p3=has_p3, attempts_dir=attempts_dir, residue_path=residue_path)
