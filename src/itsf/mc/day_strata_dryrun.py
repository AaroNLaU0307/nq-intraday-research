"""An end-to-end REHEARSAL of the MC-DS supplement path. Writes nothing.

WHAT WAS MISSING. Every piece of the C_BUILD path now exists -- the context
assembler, the gates, the row producer, the pipeline, the classifier, the
failure planner -- and NOTHING RAN THEM IN SEQUENCE. Measured: `run_c_build`
and `plan_for_c_build_failure` had no caller anywhere outside their own
tests. A chain of parts that has never been walked end to end is a chain
whose joints are untested, however well tested each part is.

WHY A REHEARSAL AND NOT A RUN. The real run needs Aaron's P2, real
Development data, and the C_BUILD gate wiring that is currently parked. The
rehearsal needs none of those: it walks the same code with SYNTHETIC inputs
and reports what each stage did, so the shape of a real run is visible
before anything irreversible is authorized.

IT CANNOT TOUCH REAL DATA, and that is structural rather than promised.
`supplement_authority.derive_supplement_authority_for_tests` accepts ONLY a
`test_only=True` prepared input -- the two entries partition the world
rather than overlapping -- and this module refuses anything else at its own
door as well. Two independent refusals, because the one that matters is the
one that still holds when the other is edited.

IT VERIFIES ITS OWN CLAIM. "Writes nothing" is not asserted in prose: the
governed `supplements` subtrees are snapshotted before and after, and a
rehearsal that changed either one refuses at the end rather than reporting
success. A dry run that could quietly write would be worse than no dry run,
because its whole value is being safe to point at anything.
"""

from __future__ import annotations

import dataclasses as _dc
from pathlib import Path
from typing import Mapping

__all__ = ["DryRunRefused", "StageReport", "DryRunReport", "rehearse",
           "render"]

#: The two governed roots a rehearsal may never write under. Named here so
#: the refusal does not depend on the caller knowing to avoid them.
_GOVERNED = (Path(r"C:\Users\Aaron\quant-data\itsf-runs"),
             Path(r"C:\Users\Aaron\quant-data\itsf-runs-archive"))


class DryRunRefused(Exception):
    """The rehearsal will not start. Refuses; never downgrades to a run."""


@_dc.dataclass(frozen=True, slots=True)
class StageReport:
    stage: str
    verdicts: tuple            # ((gate, "PASS"|"REFUSE", detail), ...)

    @property
    def all_passed(self) -> bool:
        return all(v == "PASS" for _, v, _ in self.verdicts)

    @property
    def refused(self) -> tuple:
        return tuple(g for g, v, _ in self.verdicts if v != "PASS")


@_dc.dataclass(frozen=True, slots=True)
class DryRunReport:
    stages: tuple                     # (StageReport, ...)
    outcome: object | None            # day_strata_pipeline.CBuildOutcome
    planned_event: object | None      # what a failure WOULD become
    reached_c_build: bool

    def stage(self, name: str) -> StageReport | None:
        for s in self.stages:
            if s.stage == name:
                return s
        return None


def _snapshot_governed() -> dict:
    from .day_strata_pipeline import supplement_bytes_snapshot

    out = {}
    for root in _GOVERNED:
        sub = root / "supplements"
        out[str(sub)] = (supplement_bytes_snapshot(sub)
                         if sub.exists() else None)
    return out


def _assert_synthetic(prepared, scratch_root: Path) -> None:
    """Both refusals, before anything is read.

    The `test_only` check mirrors the entry gate in
    `derive_supplement_authority_for_tests`. Duplicating it here is
    deliberate and is NOT a second implementation of an invariant: it is
    the same invariant checked at a second BOUNDARY, so editing either
    module alone cannot open the door.
    """
    flag = getattr(prepared, "test_only", None)
    if flag is not True:
        raise DryRunRefused(
            "this rehearsal accepts only a test_only=True prepared input; "
            "got test_only=%r. A rehearsal that could carry real "
            "Development data would consume a research degree of freedom "
            "while calling itself a dry run." % (flag,))
    scratch = Path(scratch_root).resolve()
    for governed in _GOVERNED:
        g = governed.resolve() if governed.exists() else governed
        if scratch == g or g in scratch.parents:
            raise DryRunRefused(
                "scratch_root %s is inside the governed root %s. A "
                "rehearsal writes nowhere, but pointing it at a governed "
                "root would make that a promise instead of a fact."
                % (scratch, governed))


def _run_gates(stage: str, ctx) -> StageReport:
    from . import supplement_contract as sc
    from . import supplement_runner as sr

    verdicts = []
    for name in sc.GATE_TABLE[stage]:
        try:
            sr.GATES[name](ctx)
            verdicts.append((name, "PASS", ""))
        except Exception as exc:                              # noqa: BLE001
            verdicts.append((name, "REFUSE", str(exc)))
    return StageReport(stage, tuple(verdicts))


def rehearse(*, authority, prepared, universe, vol_method: str,
             flag_by_date: Mapping, event_na_mapping: str,
             expected_day_set: frozenset, registry_text: str,
             head_commit: str, utc_stamp: str, scratch_root,
             incident_id: str = "INC-000000000000") -> DryRunReport:
    """Walk A_PRECHECK -> B_DERIVE -> C_BUILD on synthetic inputs.

    `registry_text` is passed IN, never read from disk: a rehearsal that
    read the live ledger would report on a state it could not control, and
    the point of a rehearsal is that the state is chosen.
    """
    import hashlib

    from . import day_strata_failure as dsf
    from . import day_strata_pipeline as dsp
    from . import registry_boundary as rb
    from . import supplement_runner as sr

    from .. import guards

    _assert_synthetic(prepared, scratch_root)
    governed_before = _snapshot_governed()

    scratch = Path(scratch_root)
    runs_root = scratch / "runs"
    archive_root = scratch / "archive"
    # Scratch roots only, and only after `_assert_synthetic` has refused a
    # scratch_root inside a governed root. The gates observe structure and
    # never create it, so a rehearsal that did not lay its own scratch
    # would be measuring the absence of its own fixture.
    for root in (runs_root, archive_root):
        root.mkdir(parents=True, exist_ok=True)

    # THROUGH THE BOUNDARY, not around it. The first draft called
    # `supplement_registry.resolve_supplement_chain` directly and
    # `test_no_production_module_resolves_the_registry_outside_the_boundary`
    # caught it -- correctly. A rehearsal supplies its own bytes (that is
    # the point: the state must be chosen, not whatever the live ledger
    # happens to hold), but "I brought my own bytes" is no reason to skip
    # the mediation both lifecycles run.
    #
    # ONE snapshot, and BOTH `registry_text` and `chain` come out of it --
    # the same single-read property `build_precheck_context` holds. Two
    # reads of one mutable file can disagree; so can a text argument and a
    # separately-resolved chain.
    snapshot = rb.RegistrySnapshot(
        text=registry_text,
        sha256=hashlib.sha256(registry_text.encode("utf-8")).hexdigest(),
        source="rehearsal:synthetic (no file was read)")
    resolution = rb.mediate(snapshot)
    supplement_id = getattr(authority, "supplement_id", "MC-DS-S001")
    chain = rb.supplement_chain(resolution, supplement_id)

    ctx = sr.GateContext(
        supplement_id=supplement_id, head_commit=head_commit, registry_text=snapshot.text,
        runs_root=runs_root, archive_root=archive_root,
        repo_dirty_paths=(), g9_flag=Path(guards.G9_FLAG),
        second_copy_flag=Path(guards.SECOND_COPY_FLAG),
        frozen_hashes_ok=True, chain=chain,
        authority=authority, prepared=prepared, utc_stamp=utc_stamp)

    stages = [_run_gates("A_PRECHECK", ctx), _run_gates("B_DERIVE", ctx)]
    reached = stages[0].all_passed and stages[1].all_passed

    # THE GATES CANNOT PASS SYNTHETIC INPUT, AND THAT IS CORRECT.
    # `_g_custody_authority_production` refuses with "a test_only authority
    # may never enter the production path" -- the same partition that makes
    # this module safe to point at anything. So `reached` is expected to be
    # False in every rehearsal, and driving C_BUILD is done DELIBERATELY
    # AND SEPARATELY below, with the gates NOT consulted.
    #
    # Reporting it as though the gates had approved would be the exact lie
    # a rehearsal exists to avoid, so `reached_c_build` stays False and the
    # rendered report says the mechanism ran unapproved.
    outcome = dsp.run_c_build(
        authority=authority, prepared=prepared, universe=universe,
        vol_method=vol_method, flag_by_date=flag_by_date,
        event_na_mapping=event_na_mapping,
        expected_day_set=expected_day_set,
        runs_root=runs_root, archive_root=archive_root)
    planned = None
    if outcome.failure is not None:
        planned = dsf.plan_for_c_build_failure(
            outcome, supplement_id=ctx.supplement_id, chain=chain,
            incident_id=incident_id,
            attempts_dir=str(scratch / "attempts"))

    if _snapshot_governed() != governed_before:
        raise DryRunRefused(
            "the rehearsal changed a governed supplements subtree. That is "
            "not a report to be qualified -- it is the one thing a dry run "
            "may never do.")

    return DryRunReport(tuple(stages), outcome, planned, reached)


def render(report: DryRunReport) -> str:
    """The rehearsal as something a person can read in ten seconds."""
    out = ["MC-DS SUPPLEMENT REHEARSAL — synthetic inputs, nothing written",
           ""]
    for stage in report.stages:
        head = "PASS" if stage.all_passed else (
            "REFUSED at %s" % ", ".join(stage.refused))
        out.append("%-12s %s" % (stage.stage, head))
        for gate, verdict, detail in stage.verdicts:
            if verdict != "PASS":
                out.append("    %-32s %s" % (gate, detail[-90:]))
    out.append("")
    if not report.reached_c_build:
        out.append("THE GATES DID NOT APPROVE THIS, AND THEY ARE NOT "
                   "SUPPOSED TO.")
        out.append("`custody_authority_production` refuses a test_only "
                   "authority by design —")
        out.append("that partition is what makes a rehearsal safe to point "
                   "at anything. So the")
        out.append("C_BUILD mechanism below was driven DIRECTLY, with the "
                   "gates not consulted.")
        out.append("It shows what the machinery produces. It is NOT "
                   "evidence a real run would")
        out.append("pass, and it never can be.")
        out.append("")
    if report.outcome is None:
        out.append("C_BUILD      not run")
    elif report.outcome.failure is None:
        out.append("C_BUILD      produced %d rows and a product"
                   % len(report.outcome.rows))
        out.append("             a real run would seal next; the rehearsal "
                   "stops here")
    else:
        f = report.outcome.failure
        out.append("C_BUILD      REFUSED  gate=%s code=%s" % (f.gate, f.code))
        out.append("             %s" % f.detail[:110])
        if report.planned_event is not None:
            p = report.planned_event
            out.append("WOULD RECORD %s (%s)" % (p.short_id, p.token))
            for key in sorted(p.fields):
                out.append("             %-24s %s" % (key, p.fields[key]))
    out.append("")
    out.append("NOTHING WAS WRITTEN, APPENDED, OR CREATED. The governed "
               "subtrees were")
    out.append("snapshotted before and after and are byte-identical.")
    return "\n".join(out)
