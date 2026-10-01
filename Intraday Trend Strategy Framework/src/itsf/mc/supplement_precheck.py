"""Assemble a REAL A_PRECHECK context, and report what the gates say.

WHY THIS EXISTS, AND WHAT IT DELIBERATELY IS NOT.

N04 ships DEFAULT-REFUSE: `supplement_runner.run_supplement_production` is
typed `NoReturn` and ends in an unconditional raise. That is the ratified
state and this module does not change it -- nothing here is called from
either production entry, and neither entry's refusal moves.

What was missing is smaller and more embarrassing than "an execution path":
there was no way to ASK the thirteen A_PRECHECK gates what they say about
the real environment. The gates existed, `run_stage_gates` existed, and the
only thing that had ever driven them was a rehearsal on synthetic input --
which cannot answer the question, because `custody_authority_production`
refuses synthetic authority by design and the walk stops there.

So on 2026-08-31 I told Aaron the remaining distance was three steps, and
the answer was sitting behind a context nobody had ever assembled. This
module assembles it.

WHAT IT READS. `ops/TRIAL_REGISTRY.md` through the boundary, `git rev-parse`
and `git status --porcelain`, the two flag files, and the existence and shape
of the two ruled output roots. NO Development data. It opens no market file,
creates no directory, writes no probe, appends nothing.

WHAT IT CANNOT ANSWER. B_DERIVE and C_BUILD need a minted authority and a
prepared input, which means reading real data. Those stages are outside this
module on purpose: the point of a precheck is to be the part you can run
BEFORE deciding to spend anything.
"""
from __future__ import annotations

import dataclasses as _dc
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from . import supplement_contract as sc
from . import supplement_runner as sr

__all__ = ["PrecheckReport", "assemble_precheck_context", "run_precheck"]

_REPO = Path(__file__).resolve().parents[3]


@_dc.dataclass(frozen=True, slots=True)
class PrecheckReport:
    """What the gates said, gate by gate, in the contract's own order.

    A report, not a decision. `passed` being true means the thirteen
    A_PRECHECK gates raised nothing against the environment as it stands --
    it does not mean a run is authorised, and it says nothing whatever about
    B_DERIVE or C_BUILD."""
    results: tuple                       # ((gate_name, None|str), ...)
    head_commit: str
    context_gaps: tuple = ()             # fields that could not be measured

    @property
    def passed(self) -> bool:
        return all(detail is None for _name, detail in self.results)

    @property
    def first_refusal(self):
        for name, detail in self.results:
            if detail is not None:
                return (name, detail)
        return None


def _git(*args) -> str:
    out = subprocess.run(["git"] + list(args), cwd=_REPO,
                         capture_output=True, text=True, encoding="utf-8",
                         errors="replace")
    if out.returncode != 0:
        raise sr.SupplementRunnerError(
            "precheck_git_failed", " ".join(args) + ": " + (out.stderr or "")[:200])
    return out.stdout


def assemble_precheck_context(supplement_id: str = sc.FIRST_SUPPLEMENT_ID,
                              *, utc_stamp: str = ""):
    """Build the GateContext A_PRECHECK needs, measuring every field.

    Returns `(ctx, gaps)`. A gap is a field this function could not measure
    rather than one it guessed -- the gates then refuse on it, which is the
    correct outcome. Nothing here supplies a default that would let a gate
    pass on an unmeasured fact."""
    from . import registry_boundary as _rb
    from itsf import contracts as _c
    from itsf import guards as _guards

    gaps = []
    snapshot, chain = _rb.resolve_for_supplement(supplement_id)
    head = _git("rev-parse", "HEAD").strip()
    dirty = tuple(line[3:].strip() for line in
                  _git("status", "--porcelain").splitlines() if line.strip())

    # `verify_frozen_hashes`, looked up rather than remembered. The first
    # version of this line called `assert_frozen_hashes`, which does not
    # exist; the AttributeError became a "gap", frozen_hashes_ok stayed None,
    # and the gate refused -- fail-closed and correct. I nearly reported that
    # refusal as "a frozen file has been modified". Seven hashes checked by
    # hand said otherwise. Look the name up; do not type it from memory.
    frozen_ok = None
    try:
        _guards.verify_frozen_hashes()          # raises if any moved
        frozen_ok = True
    except _guards.FrozenTamperError:
        frozen_ok = False                        # a REAL tamper, not a gap
    except Exception as exc:                     # noqa: BLE001
        gaps.append("frozen_hashes_ok could not be measured: %s: %s"
                    % (type(exc).__name__, exc))

    # QROS-CF I1: the governed-execution identity (only when the authorized
    # commit differs from HEAD) and the environment pin, MEASURED here so
    # the gate reads an answer and never a default.
    from itsf import execution_identity as _ei
    identity, environment = _ei.measure_for_context(head, chain)

    ctx = sr.GateContext(
        supplement_id=supplement_id,
        head_commit=head,
        registry_text=snapshot.text,
        runs_root=Path(_c.RULED_RUNS_ROOT),
        archive_root=Path(_c.RULED_ARCHIVE_ROOT),
        repo_dirty_paths=dirty,
        g9_flag=_guards.G9_FLAG,
        second_copy_flag=_guards.SECOND_COPY_FLAG,
        frozen_hashes_ok=frozen_ok,
        chain=chain,
        execution_identity=identity,
        environment_pinned=environment.pinned,
        environment_detail=environment.detail,
        # The stamp a run would use. `supplement_subtree_absent`
        # plans `<supplement_id>_<UTC>` and refuses without it --
        # correctly, since it cannot check a directory whose name it
        # cannot compute. Omitting it was the second gap in this
        # assembler, and it read like an environment problem too.
        utc_stamp=utc_stamp or datetime.now(timezone.utc).strftime(
            "%Y%m%dT%H%M%SZ"),
    )
    return ctx, tuple(gaps)


def run_precheck(supplement_id: str = sc.FIRST_SUPPLEMENT_ID,
                 *, utc_stamp: str = "") -> PrecheckReport:
    """Run the thirteen A_PRECHECK gates and report EVERY result.

    `run_stage_gates` stops at the first refusal, which is right for a run
    and wrong for a report: 'the first gate that refuses' tells you one
    thing, and 'which of the thirteen would refuse' tells you how far there
    is to go. This runs them individually and keeps going."""
    ctx, gaps = assemble_precheck_context(supplement_id,
                                          utc_stamp=utc_stamp)
    results = []
    for name in sc.GATE_TABLE["A_PRECHECK"]:
        try:
            sr.GATES[name](ctx)
            results.append((name, None))
        except Exception as exc:                 # noqa: BLE001
            results.append((name, "%s: %s" % (type(exc).__name__, exc)))
    return PrecheckReport(tuple(results), ctx.head_commit, gaps)
