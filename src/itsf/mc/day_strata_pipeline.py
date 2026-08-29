"""C_BUILD's work, in one place the gates can classify.

WHY A SEPARATE MODULE. The gates live in `supplement_runner.py`, which is
currently held by a fresh-Sol review (`c-build-2-wording-r3`), so its bytes
must not move. But that constraint produced the better structure anyway:
the runner stays thin — a gate names a failure, it does not perform the
work — and the work lives here where it can be tested on its own.

Once the freeze lifts, each C_BUILD gate becomes one line: does this
outcome's failure belong to me?

WHAT THIS IS NOT. It runs no supplement. `assert_real_run_allowed`, the
directory-creation authorization, the registry append and P2 all still
refuse, and none of them is called from here. This module takes an already
assembled universe and an already minted authority as arguments; it opens
no Development data and creates no directory.

C_BUILD_1's ASSERTION, from R3 §1, is enforced here rather than described:

    输出根下 supplement 字节的精确文件集合在门前门后逐字节相同，且为空；
    零 archive 尝试

An exact-set snapshot is taken before the three C_BUILD_1 gates' work and
again after. The universe of that snapshot is the DIRECTORY, not a declared
list — the same shape `output_proof._verify_sealed_set` uses, and for the
same reason: a snapshot whose domain comes from a manifest can be emptied
by emptying the manifest.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Mapping, NamedTuple, Sequence

from . import day_strata_classify as dsc
from . import day_strata_rows as dsr
from . import day_strata_supplement as ds

__all__ = ["CBuildFailure", "CBuildOutcome", "run_c_build",
           "supplement_bytes_snapshot"]


class CBuildFailure(NamedTuple):
    """A refusal, already carrying the gate that names it."""
    gate: str
    code: str
    detail: str


class CBuildOutcome(NamedTuple):
    """What C_BUILD produced, or why it refused. Never both."""
    rows: tuple
    product: object | None
    failure: CBuildFailure | None

    def belongs_to(self, gate: str) -> CBuildFailure | None:
        """The failure this gate must report, or None.

        The whole of a gate's body, once the runner's freeze lifts."""
        if self.failure is not None and self.failure.gate == gate:
            return self.failure
        return None


def supplement_bytes_snapshot(root: Path | None) -> tuple:
    """The exact set of supplement bytes under `root`: (name, size, sha256).

    The DIRECTORY is the universe. Nothing is declared and then looked for;
    everything present is recorded, so a byte that should not be there
    changes the snapshot instead of being invisible to it.

    A root that does not exist snapshots as empty — which is the state
    C_BUILD_1 requires, and is not the same as an unreadable root: that
    raises, because "I could not look" must never read as "nothing is
    there". (The sister repository spent five review rounds on exactly that
    collapse.)"""
    if root is None:
        return ()
    path = Path(root)
    if not path.exists():
        return ()
    if not path.is_dir():
        raise dsr.DayStrataRowsError(
            "snapshot_root_not_a_directory", str(path))
    out = []
    for entry in sorted(path.rglob("*")):
        if not entry.is_file():
            continue
        raw = entry.read_bytes()
        out.append((entry.relative_to(path).as_posix(), len(raw),
                    hashlib.sha256(raw).hexdigest()))
    return tuple(out)


def run_c_build(*, authority, prepared, universe, vol_method: str,
                flag_by_date: Mapping, event_na_mapping: str,
                expected_day_set: frozenset,
                runs_root: Path | None = None,
                archive_root: Path | None = None) -> CBuildOutcome:
    """Derive the rows, build the product, and hold C_BUILD_1's assertion.

    Returns an outcome rather than raising, because a GATE reports the
    refusal and the gate needs to know which one it is. Raising here would
    make every C_BUILD failure arrive as whatever exception escaped, and
    the F1/F2 event would carry the wrong gate name.
    """
    before_runs = supplement_bytes_snapshot(runs_root)
    before_archive = supplement_bytes_snapshot(archive_root)

    try:
        rows = dsr.derive_day_strata_rows(
            universe=universe, vol_method=vol_method,
            flag_by_date=flag_by_date, event_na_mapping=event_na_mapping,
            expected_day_set=expected_day_set)
    except dsr.DayStrataRowsError as exc:
        return CBuildOutcome(
            (), None,
            CBuildFailure(dsc.classify_producer_failure(exc), exc.code,
                          exc.detail))

    from . import supplement_production as sp
    try:
        product = sp.build_supplement_from_authority(authority, prepared, rows)
    except Exception as exc:                                   # noqa: BLE001
        # The builder's own refusals are row-schema refusals by
        # construction: it validates the rows it was handed. Its code is
        # carried verbatim so the detail is not lost behind a rename.
        return CBuildOutcome(
            tuple(rows), None,
            CBuildFailure("row_schema_blind",
                          getattr(exc, "code", type(exc).__name__), str(exc)))

    declared = _declared_digest(product)
    recomputed = ds.canonical_rows_digest(rows)
    if declared != recomputed:
        return CBuildOutcome(
            tuple(rows), None,
            CBuildFailure("rows_digest_recompute", "rows_digest_mismatch",
                          f"declared {declared!r} != recomputed "
                          f"{recomputed!r}"))

    _assert_c_build_1(before_runs, supplement_bytes_snapshot(runs_root),
                      "runs_root")
    _assert_c_build_1(before_archive, supplement_bytes_snapshot(archive_root),
                      "archive_root")

    return CBuildOutcome(tuple(rows), product, None)


def _declared_digest(product) -> str:
    """The product's own `rows_digest`, however it carries it."""
    for getter in (lambda p: p["rows_digest"],
                   lambda p: getattr(p, "rows_digest")):
        try:
            value = getter(product)
        except (KeyError, TypeError, AttributeError):
            continue
        if isinstance(value, str) and value:
            return value
    raise dsr.DayStrataRowsError(
        "product_carries_no_rows_digest", type(product).__name__)


def _assert_c_build_1(before: tuple, after: tuple, label: str) -> None:
    """R3 §1's C_BUILD_1: byte-identical across the gates, AND empty.

    Both halves, and they are different claims. "Unchanged" alone would
    hold over a root that already had supplement bytes in it; "empty" alone
    would hold over a root something wrote to and then cleaned up."""
    if before != after:
        raise dsr.DayStrataRowsError(
            "c_build_1_bytes_moved",
            f"{label}: the supplement byte set changed during C_BUILD_1 "
            f"(before {len(before)} file(s), after {len(after)})")
    if after:
        raise dsr.DayStrataRowsError(
            "c_build_1_not_empty",
            f"{label}: {len(after)} supplement file(s) present before the "
            "first write; C_BUILD_1 requires the set to be empty")


# ===========================================================================
# C_BUILD_3 — after the archive attempt
# ===========================================================================
#
# R3 §1's third checkpoint, and it asserts something DIFFERENT from the
# first two. Not "no archive attempt" — the attempt has already happened.
#
#     (a) 本地 seal 不可变：重算其 sha256 等于 seal 时记录的 local_seal_sha256
#     (b) 无任何已归档字节被删除
#
# Both are recomputations, not flag reads. §11.3 records why: a field
# named `local_seal_immutable` proves nothing on its own, and reading it
# instead of recomputing is exactly how a false claim survives.


def run_c_build_3(*, sealed_path, local_seal_sha256: str,
                  archive_before: tuple,
                  archive_after: tuple) -> CBuildOutcome:
    """Classify what the archive attempt left behind.

    `local_seal_sha256` is what `seal_supplement_production` returned — the
    digest of the bytes it intended to write. Recomputing the file and
    comparing to that is the immutability claim; trusting a boolean would
    be the flag read §11.3 warns about.

    Returns an outcome for the same reason `run_c_build` does: the gate has
    to be the thing that names the refusal."""
    path = Path(sealed_path)
    if not path.is_file():
        return CBuildOutcome(
            (), None,
            CBuildFailure("archive_policy_a", "local_seal_absent",
                          f"{path} is not a file after the archive attempt; "
                          "the local seal must survive it"))

    recomputed = hashlib.sha256(path.read_bytes()).hexdigest()
    if recomputed != local_seal_sha256:
        return CBuildOutcome(
            (), None,
            CBuildFailure("archive_policy_a", "local_seal_mutated",
                          f"recomputed {recomputed!r} != recorded "
                          f"{local_seal_sha256!r}"))

    lost = _archived_bytes_lost(archive_before, archive_after)
    if lost:
        return CBuildOutcome(
            (), None,
            CBuildFailure("archive_policy_a", "archived_bytes_deleted",
                          f"{len(lost)} archived file(s) no longer present "
                          f"or no longer identical, first {lost[:3]}"))
    return CBuildOutcome((), None, None)


def _archived_bytes_lost(before: tuple, after: tuple) -> list:
    """Names present before and missing-or-changed after.

    ADDED bytes are fine — archiving adds. What C_BUILD_3 forbids is
    LOSING what was already archived, so this is a one-directional check
    and saying so matters: a symmetric comparison would refuse every
    successful archive."""
    now = {name: (size, digest) for name, size, digest in after}
    return sorted(name for name, size, digest in before
                  if now.get(name) != (size, digest))
