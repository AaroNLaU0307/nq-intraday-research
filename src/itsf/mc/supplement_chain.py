"""Compose the three C_BUILD moments into one chain, and report where it got.

WHAT THIS IS AND IS NOT. Every mechanism it calls already existed --
`run_c_build`, `run_c_build_2`, `archive_sealed_run`, `run_c_build_3`,
`decide_after_seal`. Checkpoint 3 measured that and found no mechanism
missing; what was missing was the composition. This is that composition and
nothing else: it builds no input, opens no dataset, and creates no directory.

BY MOMENT, NEVER BY STAGE. `run_stage_gates("C_BUILD", ctx)` walks the whole
gate table in one call, so it always reaches `archive_policy_a` -- which is
ruled to Router B and therefore always refuses AS A GATE. A chain built on
stages could never complete no matter what the run did. `gates_at` selects
the gates belonging to each moment; the third moment consults Router B and
never touches that gate.

IT RECEIVES, IT DOES NOT PRODUCE -- the same split as the three assembly
layers before it. `universe`, `vol_method`, `flag_by_date` and
`event_na_mapping` arrive as arguments; the caller that fetches them from the
dataset is the caller that has to be authorized to. Building this is
engineering; running it is not.

ONE CASE HAS NO RULED TERMINAL and refuses by name -- see
`ARCHIVED_BYTES_DELETED_HAS_NO_RULED_TERMINAL`. BD-5 said otherwise and was
retracted on 2026-09-02 after a reviewing seat refuted its elimination.
"""
from __future__ import annotations

import dataclasses as _dc
from pathlib import Path

from . import day_strata_pipeline as _dsp
from . import supplement_contract as _sc
from . import supplement_runner as _sr

__all__ = ["ChainResult", "ChainRefusal", "run_supplement_chain",
           "run_supplement_gate_first", "refuse_to_create_run_directory",
           "ARCHIVE_SEAM", "ARCHIVED_BYTES_DELETED"]


#: THE CASE THAT LOOKED UNRULED, WAS RULED, AND IS UNRULED AGAIN.
#:
#: `run_c_build_3` can find `archived_bytes_deleted`: the local seal survived
#: the archive attempt, but bytes that were already in the archive are gone.
#: `archive_sealed_run` verifies the copy it just made and never looks at
#: bytes archived on an earlier run, so its report can say `archive_ok` while
#: R3 §1's C_BUILD_3 assertion (b) -- "无任何已归档字节被删除" -- is violated.
#:
#: It was first filed as owed to Aaron, then taken back as BD-5 on the
#: reasoning that a terminal-state mapping touches none of his six reserved
#: categories. That part still holds -- but BD-5's ELIMINATION did not, and a
#: builder deciding a question is no licence to decide it wrongly. The
#: refutation is recorded in full at the constant below.
ARCHIVED_BYTES_DELETED = "archived_bytes_deleted"

#: Why it refuses rather than reaching a terminal. Written out because the
#: last attempt to shortcut this reasoning produced BD-5, which was wrong.
ARCHIVED_BYTES_DELETED_HAS_NO_RULED_TERMINAL = (
    "the local seal survived but previously archived bytes did not, and no "
    "ratified terminal covers that. P3's successors are P4, A1, F2 and CR1; "
    "Policy A forbids P4; an A1 row requires an `archive_code` and this is "
    "not one of the five; and A2, A1's only exit, asserts only that THIS "
    "run's copy matches. Naming a terminal needs a ruling among four "
    "successors or an amendment to a ratified closed enum, and neither is "
    "a builder's to make.")

#: `local_seal_absent` and `local_seal_mutated` need no ruling: they say the
#: local seal did not survive, which is exactly `local_seal_ok=False`, and
#: Router B already answers that with `local_seal_failed`.
LOCAL_SEAL_LOST_CODES = frozenset({"local_seal_absent", "local_seal_mutated"})


def _sealed_path(out_dir):
    from pathlib import Path

    from . import day_strata_supplement as _ds
    return Path(out_dir) / _ds.SUPPLEMENT_FILENAME


def _archive(runs_dir, archive_root):
    """The one I/O step. Imported where it is used so importing this module
    never pulls the S0 run infrastructure in behind it."""
    from ..s0.runinfra import archive_sealed_run
    return archive_sealed_run(runs_dir, archive_root)


#: The archive step, as a module-level name so a test can substitute it
#: without reaching into another module's namespace. Resolved at call time.
ARCHIVE_SEAM = _archive


class ChainRefusal(Exception):
    """The chain stopped. `moment` says which of the three it stopped at."""

    def __init__(self, moment: str, code: str, detail: str = "") -> None:
        self.moment = moment
        self.code = code
        super().__init__("%s / %s%s" % (moment, code,
                                        ": " + detail if detail else ""))


@_dc.dataclass(frozen=True, slots=True)
class ChainResult:
    """Where the chain got, and what it produced on the way."""
    verdict: str                     # "P4" or "A1"
    rows: tuple = ()
    local_seal_sha256: str = ""
    archive_status: str = ""

    @property
    def sealed(self) -> bool:
        return self.verdict == "P4"


def _gates(ctx, outcome, checkpoint: str, moment: str) -> None:
    """Run one moment's gates over `outcome`. First refusal stops the chain."""
    at = _dc.replace(ctx, c_build_outcome=outcome)
    for name in _sc.gates_at(checkpoint):
        try:
            _sr.GATES[name](at)
        except _sr.SupplementRunnerError as exc:
            raise ChainRefusal(moment, getattr(exc, "code", "gate_refused"),
                               str(exc)) from exc


def run_supplement_chain(base_ctx, *, planned, authority, prepared, universe,
                         vol_method, flag_by_date, event_na_mapping: str,
                         incident_id: str,
                         archive_before, archive_after_reader):
    """Run the three moments in order and return where the chain got.

    `planned` IS A `PlannedPaths`, and taking one instead of three free paths
    is the H1 repair (engineering-safety HOLD, 2026-09-02). The first version
    took `out_dir`, `runs_dir` and `archive_root` independently, so a caller
    could seal into one tree and archive another: reproduced at P4 with
    `archive_ok` while the sealed supplement was not in the archive at all
    and an empty directory had been copied. Policy A's second copy was not
    guaranteed by anything.

    The binding is NOT a rule invented here. `plan_supplement_paths` is the
    ratified planner and already owns it -- `runs_target` is where the run
    writes and `archive_parent` is, in its own words, "what
    `archive_sealed_run` must be passed". Deriving both from one object makes
    unbinding them impossible rather than merely discouraged.

    `archive_before` is the archive inventory taken BEFORE the attempt and
    `archive_after_reader` is a zero-argument callable that takes it again
    afterwards. They are arguments rather than something this module
    computes, for the same reason everything else here is: the snapshot is
    of a real directory, and touching one is the caller's authorization to
    hold, not this module's.
    """
    from pathlib import Path as _Path

    out_dir = _Path(planned.runs_target)
    # --- moment 1: before the first write --------------------------------
    # `run_c_build` CLASSIFIES most failures into an outcome, but
    # `_assert_c_build_1` raises `DayStrataRowsError` straight out -- so a
    # producer refusal escaped this function as a bare exception while every
    # other stop arrived as a `ChainRefusal`. Found by the H1 repair: once
    # the seal landed in `runs_root`, a second run tripped
    # `c_build_1_not_empty` and it came out unnamed. Same shape as H2's
    # bare `FileNotFoundError`.
    try:
        outcome = _dsp.run_c_build(
            authority=authority, prepared=prepared, universe=universe,
            vol_method=vol_method, flag_by_date=flag_by_date,
            event_na_mapping=event_na_mapping,
            expected_day_set=authority.expected_day_set,
            runs_root=out_dir, archive_root=planned.archive_parent)
    except Exception as exc:                       # noqa: BLE001
        code = getattr(exc, "code", None)
        if code is None:
            raise
        raise ChainRefusal("C_BUILD_1", code, str(exc)) from exc
    _gates(base_ctx, outcome, _sc.CHECKPOINT_C_BUILD_1, "C_BUILD_1")

    # --- moment 2: during staging (writes `.partial` by construction) -----
    staging = _dsp.run_c_build_2(
        product=outcome.product, out_dir=out_dir, authority=authority,
        prepared=prepared, incident_id=incident_id)
    if staging.router_b_code:
        # BD-1: no gate names these, so asking the gates would report green
        # over a seal that did not happen. Router B owns it and refuses.
        try:
            _sr.decide_after_seal(local_seal_ok=False, archive_report=None)
        except _sr.SupplementRunnerError as exc:
            raise ChainRefusal("C_BUILD_2", staging.router_b_code,
                               str(exc)) from exc
        raise ChainRefusal(                       # pragma: no cover - guard
            "C_BUILD_2", staging.router_b_code,
            "Router B returned instead of refusing a failed seal")
    _gates(base_ctx, staging.outcome, _sc.CHECKPOINT_C_BUILD_2, "C_BUILD_2")

    # --- moment 3: after the archive attempt, via Router B ----------------
    # `archive_parent` by name -- the planner says so, and passing
    # `archive_root` here is how H1 archived the wrong tree.
    archive_report = ARCHIVE_SEAM(out_dir, planned.archive_parent)
    after = archive_after_reader()
    post = _dsp.run_c_build_3(
        sealed_path=_sealed_path(out_dir),
        local_seal_sha256=staging.local_seal_sha256,
        archive_before=tuple(archive_before), archive_after=tuple(after))

    local_seal_ok = True
    if post.failure is not None:
        code = post.failure.code
        if code in LOCAL_SEAL_LOST_CODES:
            local_seal_ok = False
        elif code == ARCHIVED_BYTES_DELETED:
            # BD-5 RETRACTED 2026-09-02. It routed this to A1 by an
            # elimination the reviewing seat refuted and that reproduces:
            # P3's ratified successors are P4, A1, F2 AND CR1, so the space
            # was never closed; an A1 row requires an `archive_code` and
            # this is not one of the five; and A2, A1's only exit, asserts
            # things about THIS run's copy, so it could not discharge the
            # defect even if the row could be written.
            #
            # Refusing by name again. Naming the terminal now needs a ruling
            # among four successors or an amendment to a ratified closed
            # enum -- neither is a builder's to make.
            raise ChainRefusal("C_BUILD_3", code,
                               ARCHIVED_BYTES_DELETED_HAS_NO_RULED_TERMINAL)
        else:
            # Anything added to C_BUILD_3 later. Fail-closed, the same rule
            # BD-1 applies to seal codes: a code nobody classified must not
            # quietly acquire a verdict.
            raise ChainRefusal("C_BUILD_3", code,
                               "no ruled verdict covers %r" % code)
    try:
        verdict = _sr.decide_after_seal(local_seal_ok=local_seal_ok,
                                        archive_report=archive_report)
    except _sr.SupplementRunnerError as exc:
        raise ChainRefusal("C_BUILD_3", getattr(exc, "code", "router_b"),
                           str(exc)) from exc
    return ChainResult(verdict, tuple(outcome.rows),
                       staging.local_seal_sha256,
                       getattr(archive_report, "status", ""))

# ===========================================================================
# The gate-first composition (H2 repair, 2026-09-02)
# ===========================================================================
#
# THE FINDING. `run_supplement_chain` runs the three C_BUILD moments and
# nothing else, so a caller could reach P4 without a single one of the 13
# A_PRECHECK or 5 B_DERIVE gates having passed. The precheck/derive/build
# modules only REPORT; `run_supplement_production` refuses unconditionally
# and never calls any of this. Components existed; a path did not -- the
# same shape as `ops/P2_WITHDRAWN_NO_EXECUTION_PATH_2026-08-31.md`.
#
# WHY BUILDING IT OPENS NOTHING. A_PRECHECK contains the live-authorization
# gates, and they refuse today for want of a P2. Composing the stages in
# order does not weaken that -- it makes the refusal happen at the first
# gate that should raise it, instead of never being asked.
#
# THE DIRECTORY STEP IS NOW OWNED. `<id>_<UTC>` had no owner: the planner
# refuses to create it, the chain assumed it, and nothing named the gap.
# `make_run_directory` is a REQUIRED callable with no default, so a caller
# must say who creates it. `refuse_to_create_run_directory` is what an
# unauthorized caller passes, and it refuses by name --
# `DIRECTORY_CREATION_AUTHORIZED=NO` stays true and becomes visible.


def refuse_to_create_run_directory(target) -> "NoReturn":
    """The default posture: naming the step without performing it."""
    raise ChainRefusal(
        "RUN_DIRECTORY", "directory_creation_not_authorized",
        "%s would have to be created, and ND1 says "
        "DIRECTORY_CREATION_AUTHORIZED=NO. Creating a directory under the "
        "governed roots is a separate authorization from Aaron; pass a "
        "callable that does it only once he has given one." % target)


def run_supplement_gate_first(base_ctx, *, planned, prepared, universe,
                              vol_method, flag_by_date,
                              event_na_mapping: str, incident_id: str,
                              archive_before, archive_after_reader,
                              make_run_directory):
    """A_PRECHECK, then B_DERIVE, then the run directory, then the chain.

    Every stop is a `ChainRefusal` naming the stage and gate. `prepared` and
    `make_run_directory` are required with no defaults, for the reason every
    layer below states: a default would let a caller omit one and leave this
    to find it."""
    from . import supplement_authority as _sa

    for name in _sc.GATE_TABLE["A_PRECHECK"]:
        try:
            _sr.GATES[name](base_ctx)
        except _sr.SupplementRunnerError as exc:
            raise ChainRefusal("A_PRECHECK", getattr(exc, "code", name),
                               str(exc)) from exc

    try:
        authority = _sa.derive_supplement_authority(
            prepared, supplement_id=base_ctx.supplement_id)
    except Exception as exc:                       # noqa: BLE001
        raise ChainRefusal("B_DERIVE", getattr(exc, "code", "authority_mint"),
                           str(exc)) from exc
    ctx = _dc.replace(base_ctx, authority=authority, prepared=prepared)
    for name in _sc.GATE_TABLE["B_DERIVE"]:
        try:
            _sr.GATES[name](ctx)
        except _sr.SupplementRunnerError as exc:
            raise ChainRefusal("B_DERIVE", getattr(exc, "code", name),
                               str(exc)) from exc

    make_run_directory(planned.runs_target)
    target = Path(planned.runs_target)
    if not target.is_dir():
        # NAMED, because a bare FileNotFoundError out of the sealer was one
        # of the things H2 reported.
        raise ChainRefusal("RUN_DIRECTORY", "run_directory_absent",
                           "%s does not exist after make_run_directory "
                           "returned" % target)

    return run_supplement_chain(
        ctx, planned=planned, authority=authority, prepared=prepared,
        universe=universe, vol_method=vol_method, flag_by_date=flag_by_date,
        event_na_mapping=event_na_mapping, incident_id=incident_id,
        archive_before=archive_before,
        archive_after_reader=archive_after_reader)
