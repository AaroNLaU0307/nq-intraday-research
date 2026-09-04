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

ONE CASE LOOKED UNRULED AND WAS NOT, see `ARCHIVED_BYTES_DELETED` and BD-5 in
`decide_after_seal`.
"""
from __future__ import annotations

import dataclasses as _dc

from . import day_strata_pipeline as _dsp
from . import supplement_contract as _sc
from . import supplement_runner as _sr

__all__ = ["ChainResult", "ChainRefusal", "run_supplement_chain",
           "ARCHIVE_SEAM", "ARCHIVED_BYTES_DELETED"]


#: THE CASE THAT LOOKED UNRULED, AND WAS NOT (BD-5, 2026-09-02).
#:
#: `run_c_build_3` can find `archived_bytes_deleted`: the local seal survived
#: the archive attempt, but bytes that were already in the archive are gone.
#: `archive_sealed_run` verifies the copy it just made and never looks at
#: bytes archived on an earlier run, so its report can say `archive_ok` while
#: R3 §1's C_BUILD_3 assertion (b) -- "无任何已归档字节被删除" -- is violated.
#:
#: This was first filed as a decision owed to Aaron. That was an
#: OVER-ESCALATION: his reserved categories are cost, the Primary metric,
#: sample splitting, when real data is touched, promotion/falsification, and
#: creating quant-data directories. A terminal-state mapping is none of them,
#: so it is the builder's, and it is settled in `decide_after_seal` by
#: elimination over a CLOSED answer space rather than by preference.
ARCHIVED_BYTES_DELETED = "archived_bytes_deleted"

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


def run_supplement_chain(base_ctx, *, authority, prepared, universe,
                         vol_method, flag_by_date, event_na_mapping: str,
                         out_dir, runs_dir, archive_root, incident_id: str,
                         archive_before, archive_after_reader):
    """Run the three moments in order and return where the chain got.

    `archive_before` is the archive inventory taken BEFORE the attempt and
    `archive_after_reader` is a zero-argument callable that takes it again
    afterwards. They are arguments rather than something this module
    computes, for the same reason everything else here is: the snapshot is
    of a real directory, and touching one is the caller's authorization to
    hold, not this module's.
    """
    # --- moment 1: before the first write --------------------------------
    outcome = _dsp.run_c_build(
        authority=authority, prepared=prepared, universe=universe,
        vol_method=vol_method, flag_by_date=flag_by_date,
        event_na_mapping=event_na_mapping,
        expected_day_set=authority.expected_day_set,
        runs_root=runs_dir, archive_root=archive_root)
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
    archive_report = ARCHIVE_SEAM(runs_dir, archive_root)
    after = archive_after_reader()
    post = _dsp.run_c_build_3(
        sealed_path=_sealed_path(out_dir),
        local_seal_sha256=staging.local_seal_sha256,
        archive_before=tuple(archive_before), archive_after=tuple(after))

    local_seal_ok = True
    post_archive_ok = True
    if post.failure is not None:
        code = post.failure.code
        if code in LOCAL_SEAL_LOST_CODES:
            local_seal_ok = False
        elif code == ARCHIVED_BYTES_DELETED:
            # BD-5. The checkpoint refutes a report that says archive_ok, and
            # Router B is TOLD that rather than handed a synthesized failing
            # report -- see `decide_after_seal` for why A1 is the ratified
            # enum's remainder rather than a preference.
            post_archive_ok = False
        else:
            # Anything added to C_BUILD_3 later. Fail-closed, the same rule
            # BD-1 applies to seal codes: a code nobody classified must not
            # quietly acquire a verdict.
            raise ChainRefusal("C_BUILD_3", code,
                               "no ruled verdict covers %r" % code)
    try:
        verdict = _sr.decide_after_seal(local_seal_ok=local_seal_ok,
                                        archive_report=archive_report,
                                        post_archive_ok=post_archive_ok)
    except _sr.SupplementRunnerError as exc:
        raise ChainRefusal("C_BUILD_3", getattr(exc, "code", "router_b"),
                           str(exc)) from exc
    return ChainResult(verdict, tuple(outcome.rows),
                       staging.local_seal_sha256,
                       getattr(archive_report, "status", ""))
