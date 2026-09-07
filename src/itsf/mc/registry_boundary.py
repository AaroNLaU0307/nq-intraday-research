"""The single production validation boundary for `ops/TRIAL_REGISTRY.md`.

RULED, NOT CHOSEN. `MC-REG-COLLISION-001`, C2 as modified and ratified by a
fresh Codex GPT-5.6 Sol session on 2026-08-25 (`DELEGATED=YES`), over a
Fable 5 proposal. Sol replaced Fable's C2 outright; this module exists
because of what it replaced it with.

WHAT FABLE'S C2 MISSED. It required every production reader to be covered,
and stopped there — each reader could still take its OWN read of a MUTABLE
shared file. So MC validation could succeed against one version of
`ops/TRIAL_REGISTRY.md` while supplement resolution acted on another.
Measured before the ruling: FOUR independent `read_text` calls on that path
lived in `consumer`, `day_strata_supplement`, `real_input` and
`supplement_runner`. The loophole was reachable, not theoretical.

THE INVARIANT THIS MODULE IS. One read. Both lifecycles against the
identical immutable snapshot. A refusal from EITHER yields no usable result
and no downstream action.

That last clause is the part worth reading twice: a supplement chain that
resolves perfectly is still UNUSABLE if MC resolution refused over the same
bytes, because the file's governance record is broken and neither lifecycle
gets to act on a broken record. `supplement_chain()` carries an MC refusal
out as the chain's own `problem`, so the existing A_PRECHECK gate
`registry_chain_resolvable` enforces the coupling with no gate change —
`ANY_CHAIN_DEFECT=REFUSE_WHOLE_RESOLUTION` already meant exactly this, one
lifecycle wider.

NO BYPASS. Production code may not read that path or call either resolver
directly. The only exceptions C2 allows are unconditional-refusal stubs —
functions incapable of returning authorization, readiness or a usable chain
— and those are enumerated and BEHAVIOURALLY proved to refuse in
`tests/test_registry_boundary.py`, not merely declared.
"""
from __future__ import annotations

import dataclasses as _dc
import hashlib
import re
from pathlib import Path
from types import MappingProxyType

__all__ = ["RegistrySnapshot", "MediatedResolution", "BoundaryError",
           "REGISTRY_PATH", "REGISTRY_REPO_ROOT", "BOUNDARY_RULING",
           "read_snapshot", "mediate",
           "resolve_registry", "supplement_chain", "resolve_for_supplement",
           "RUN_STARTED_TOKEN", "AppendRefused", "append_run_started",
           "append_owner_hold", "append_owner_release", "serialized_append",
           "serialized_start_append", "START_EQUIVALENT_TOKENS",
           "is_start_equivalent"]

BOUNDARY_RULING = "MC_REG_COLLISION_001_C2_AS_MODIFIED_2026-08-25"
BOUNDARY_RULING_DELEGATED = True

#: The one governed path. Relative to the repo root.
REGISTRY_PATH = "ops/TRIAL_REGISTRY.md"

#: THE REGISTRY'S REPOSITORY ROOT, frozen as an exact string.
#:
#: Repointed 2026-08-31 by migration Route A, step S6. It used to be
#: `Path(__file__).resolve().parents[3]` -- this repository -- and this
#: repository's path runs through OneDrive, because the Desktop known folder
#: is redirected there. That was measured, not assumed, and a sync agent
#: that is dormant today can be woken while a redirection does not
#: un-redirect itself.
#:
#: FROZEN AND NOT OVERRIDABLE FROM THE ENVIRONMENT, as the route requires. A
#: governed path that a variable can move is a governed path in name only;
#: whoever changes it should have to change bytes a reviewer can see.
#:
#: `ops/TRIAL_REGISTRY.md` stays the relative path on purpose -- the approved
#: CR1 block names it verbatim, so those sentences remain literally true.
REGISTRY_REPO_ROOT = Path(r"C:\Users\Aaron\quant-data\itsf-registry")


class BoundaryError(RuntimeError):
    """The boundary itself could not produce a snapshot. Never a warning."""


@_dc.dataclass(frozen=True)
class RegistrySnapshot:
    """The bytes, read once. Everything downstream reasons about THESE.

    Carries its own digest so evidence can record WHICH registry state a
    decision was taken against, rather than a claim that one was read."""
    text: str
    sha256: str
    source: str

    @property
    def n_bytes(self) -> int:
        return len(self.text.encode("utf-8"))


@_dc.dataclass(frozen=True)
class MediatedResolution:
    """Both lifecycles, one snapshot.

    `refusal` non-empty means NOTHING here is usable — and the constructor
    enforces that rather than trusting callers to check, because "the
    caller will check" is how a refused resolution becomes a permitted
    action."""
    snapshot: RegistrySnapshot
    supplement_chains: object = _dc.field(default_factory=dict)
    mc_chains: object = _dc.field(default_factory=dict)
    refusal: str = ""
    refusing_lifecycle: str = ""          # "" | "supplement" | "mc"
    ruling: str = BOUNDARY_RULING
    delegated: bool = BOUNDARY_RULING_DELEGATED

    def __post_init__(self) -> None:
        if self.refusal:
            if self.supplement_chains or self.mc_chains:
                raise BoundaryError(
                    "a refused resolution carries chains; a refusal from "
                    "either lifecycle must leave NOTHING usable "
                    f"({self.refusing_lifecycle}: {self.refusal})")
            if self.refusing_lifecycle not in ("supplement", "mc"):
                raise BoundaryError(
                    f"refusing_lifecycle={self.refusing_lifecycle!r} names "
                    "no lifecycle; a refusal nobody owns cannot be acted on")
        elif self.refusing_lifecycle:
            raise BoundaryError(
                "refusing_lifecycle is set with no refusal")

    @property
    def usable(self) -> bool:
        return not self.refusal


# ---------------------------------------------------------------------------
# The read
# ---------------------------------------------------------------------------

#: A tombstone is what the OLD path holds after a migration: a file that
#: exists, is deliberately not a registry, and names where the real one
#: went. It must be REFUSED LOUDLY and by its own name.
#:
#: The review of the migration plan found why. `_read_text` refuses an
#: ABSENT file; a tombstone is PRESENT, so it read as a 97-byte snapshot and
#: the downstream refusal was the same string a missing registry produces —
#: "no supplement event chain exists for this id". A deliberate marker that
#: reads as "nothing has been authorised yet" is the defect the absence
#: check was added to close, wearing a different costume.
#:
#: Deliberately NOT "reject anything unparseable": a truncated or rolled-back
#: registry is a different incident, and the anti-rollback witness is its
#: designed detector. Widening this to cover that case would hide a real
#: incident behind a path error.
REGISTRY_TOMBSTONE_MARKER = "REGISTRY_MOVED_NOT_A_REGISTRY"


def _assert_not_a_tombstone(path: Path, text: str) -> None:
    if REGISTRY_TOMBSTONE_MARKER in text:
        first = next((ln for ln in text.splitlines()
                      if REGISTRY_TOMBSTONE_MARKER in ln), "")
        raise BoundaryError(
            "%s is a migration tombstone, not the registry: %r. The "
            "canonical registry moved; this path must not be read as an "
            "empty or unauthorised one." % (path, first.strip()[:160]))


def _read_text(path: Path, *, _bytes: bytes | None = None) -> str:
    """THE production read of the governed registry path.

    Deliberately one tiny function: the no-bypass test asserts that no
    other production module reads this path, and the behavioural test
    counts calls HERE to prove one mediation performs exactly one read.

    A MISSING FILE REFUSES; it does not read as an empty registry.

    Ruling invariant 8 of dec-registry-migration-2026-08-27 found this,
    and the consequence measured out exactly as the seat described:

        missing file        -> "no supplement event chain exists for this
                               id - NOT AUTHORIZED"
        real registry, no
        chain for that id   -> the SAME string, indistinguishable

    So a path typo looked precisely like "not authorized yet". That is the
    same defect shape as calling a crash "unauthorised" - a failure the
    system cannot see, wearing the costume of a refusal it understands. It
    matters most exactly when the path is about to change: after a
    migration, one un-updated construction site would refuse quietly and
    correctly-looking, forever.

    Refusing loudly is safe here BECAUSE the empty string was never a
    legitimate state: the governed registry has existed and been appended
    to since the first trial, and an append-only file does not become
    empty."""
    if not path.exists():
        raise BoundaryError(
            "the governed registry is absent at %s. This is a refusal, not "
            "an empty registry: an append-only file does not become empty, "
            "so absence means the path is wrong or the file was lost - "
            "never that nothing has been authorised yet." % path)
    # `_bytes` lets ONE caller -- `append_run_started`'s compare-and-swap --
    # decode the exact bytes it will append to, instead of taking a second
    # read of a file that can change between them (QROS-CF F06). It is not a
    # second read path: absence still refuses above, the tombstone check
    # still runs, and every other caller reads the file here as before.
    text = (path.read_text(encoding="utf-8") if _bytes is None
            else _bytes.decode("utf-8"))
    _assert_not_a_tombstone(path, text)
    return text


def read_snapshot(path: str | Path | None = None) -> RegistrySnapshot:
    """Read the registry ONCE and freeze what was read."""
    target = (Path(path) if path is not None
              else REGISTRY_REPO_ROOT / REGISTRY_PATH)
    text = _read_text(target)
    return RegistrySnapshot(
        text=text,
        sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        source=str(target))


# ---------------------------------------------------------------------------
# The mediation
# ---------------------------------------------------------------------------

def mediate(snapshot: RegistrySnapshot) -> MediatedResolution:
    """Run BOTH lifecycles against the identical snapshot.

    Order is not significance: whichever refuses first wins, and either
    refusal is total. A resolver that blows up is converted to a refusal
    rather than allowed to propagate — an exception a caller might catch
    and read as "no problem found" is the failure this whole subsystem
    exists to prevent.
    """
    from . import mc_registry as _mc
    from . import supplement_registry as _sup

    try:
        sup_chains, sup_refusal = _sup.resolve_supplement_chains(
            snapshot.text)
    except Exception as exc:                                  # noqa: BLE001
        return MediatedResolution(
            snapshot=snapshot,
            refusal=f"supplement_resolver_internal_error: {exc!r}",
            refusing_lifecycle="supplement")
    if sup_refusal:
        return MediatedResolution(snapshot=snapshot, refusal=str(sup_refusal),
                                  refusing_lifecycle="supplement")

    try:
        mc_chains, mc_refusal = _mc.resolve_mc_chains(snapshot.text)
    except Exception as exc:                                  # noqa: BLE001
        return MediatedResolution(
            snapshot=snapshot,
            refusal=f"mc_resolver_internal_error: {exc!r}",
            refusing_lifecycle="mc")
    if mc_refusal:
        return MediatedResolution(snapshot=snapshot, refusal=str(mc_refusal),
                                  refusing_lifecycle="mc")

    return MediatedResolution(
        snapshot=snapshot,
        supplement_chains=MappingProxyType(dict(sup_chains)),
        mc_chains=MappingProxyType(dict(mc_chains)))


def resolve_registry(path: str | Path | None = None) -> MediatedResolution:
    """One read, both lifecycles. THE production entry."""
    return mediate(read_snapshot(path))


# ---------------------------------------------------------------------------
# Per-lifecycle accessors — the only way out of the boundary
# ---------------------------------------------------------------------------

def supplement_chain(resolution: MediatedResolution, supplement_id: str):
    """One supplement id's chain, poisoned by an MC refusal.

    Returns the same `ChainResolution` shape `supplement_registry` does, so
    the A_PRECHECK gates consume it unchanged. When MC resolution refused,
    the chain comes back with that refusal as its own `problem` — which is
    how the cross-lifecycle coupling reaches gates that were written before
    MC rows existed, without touching a single gate.
    """
    from .supplement_registry import (NOT_AUTHORIZED_NO_CHAIN,
                                      ChainResolution)

    if resolution.refusal:
        return ChainResolution(
            supplement_id,
            problem=f"[{resolution.refusing_lifecycle}] {resolution.refusal}",
            detail=("whole resolution refused over registry snapshot "
                    f"{resolution.snapshot.sha256[:12]}; a refusal from "
                    "either lifecycle leaves nothing usable (C2)"))
    chain = resolution.supplement_chains.get(supplement_id)
    if chain is None:
        return ChainResolution(supplement_id, detail=NOT_AUTHORIZED_NO_CHAIN)
    return chain


def resolve_for_supplement(supplement_id: str,
                           path: str | Path | None = None):
    """`(snapshot, ChainResolution)` from ONE read. The runner's entry."""
    resolution = resolve_registry(path)
    return (resolution.snapshot, supplement_chain(resolution, supplement_id))


# ---------------------------------------------------------------------------
# The ONE write: P3, and nothing else
# ---------------------------------------------------------------------------
#
# WHY A WRITE EXISTS HERE AT ALL. `SUPPLEMENT_RUN_STARTED` is the ratified
# pre-start/post-start boundary, and §D.3.2 gives it to the RUNNER
# (`ACTOR=main agent (mc_ds_runner)`). Until now no production code could
# append anything, so the first real N09 would have written supplement bytes
# with no P3 in the ledger -- and the failure vocabulary cannot describe
# that: F2 requires P3 as its predecessor, and the only reachable event, F1,
# asserts "nothing consumed" about a run that had consumed everything.
#
# APPENDING P3 BY HAND BEFORE THE RUN DOES NOT WORK, measured 2026-09-05:
# `_walk_chain` marks the P2 `consumed_by_p3`, so a P3 already in the ledger
# takes the live authorization to ZERO and five A_PRECHECK gates refuse. One
# P2 authorizes one start, and P3 spends it. That is coherent -- it just
# means P3 has to be appended DURING the run, after A_PRECHECK has read the
# live P2 and before the first side effect.
#
# THE SEAM IS DELIBERATELY NARROW. Aaron authorized a P3-only append, not a
# registry writer. Everything below is a refusal except one exact shape:
# this token, an id with a live P2, the running tree's own commit, the
# ratified note fields, and once. There is no parameter for the event type,
# because a parameter is how "P3-only" becomes "whatever the caller passes".

#: The only token this module will ever write.
RUN_STARTED_TOKEN = "SUPPLEMENT_RUN_STARTED"

#: The UTC cell shape every supplement row in the real ledger uses.
#: NOT `supplement_runner.UTC_STAMP_RE` -- that one is the DIRECTORY
#: stamp (`YYYYMMDDTHHMMSSZ`) and the two are different formats for
#: different places. Reusing it here would refuse every legal row.
#: The parser itself does not validate this cell, so the seam does.
_REGISTRY_UTC_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+00:00\Z")


class AppendRefused(BoundaryError):
    """A P3 append that was refused. Carries a machine-readable `code`."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__("%s: %s" % (code, detail) if detail else code)


def _p3_note(supplement_id: str) -> str:
    """The ratified §D.3.2 P3 note, in the FIELD form the parser requires.

    §D.3.2's `NOTE_SHAPE` renders as prose ("atomic start; structural access
    begins") and that is a description of meaning, not the literal bytes:
    §D.3.5 requires machine-readable `key: value` segments so an unknown,
    duplicate or missing field is detectable. Copying the prose verbatim is
    exactly how the first P1 attempt was refused with
    `note_segment_not_field`, and it is written out here so the next reader
    does not have to rediscover it.
    """
    return ("[%s] supplement_id: %s; atomic_start_marker: YES"
            % (supplement_id, supplement_id))


#: The lock file that serializes the compare-and-swap. Beside the registry,
#: never inside it. `O_CREAT | O_EXCL` is the primitive: on both platforms
#: this project runs on, exactly one creator wins.
LOCK_SUFFIX = ".append.lock"

#: How long a waiter will try before refusing. A start that cannot take the
#: lock REFUSES -- it never proceeds unserialized.
LOCK_TIMEOUT_SECONDS = 10.0


class _AppendLock:
    """Minimum serialization for one append. Refuses rather than waiting
    forever, and refuses rather than proceeding unlocked."""

    def __init__(self, target: Path) -> None:
        self.path = target.with_name(target.name + LOCK_SUFFIX)
        self._fd = None

    def __enter__(self):
        import os
        import time
        deadline = time.monotonic() + LOCK_TIMEOUT_SECONDS
        while True:
            try:
                self._fd = os.open(str(self.path),
                                   os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                return self
            except FileExistsError:
                if time.monotonic() >= deadline:
                    raise AppendRefused(
                        "p3_append_lock_unavailable",
                        "another append holds %s; this start refuses rather "
                        "than writing unserialized" % self.path) from None
                time.sleep(0.02)

    def __exit__(self, *exc):
        import os
        if self._fd is not None:
            os.close(self._fd)
            try:
                os.unlink(str(self.path))
            except OSError:                                    # pragma: no cover
                pass
        return False


#: Events whose commit means GOVERNED EXECUTION HAS STARTED, across all three
#: families. A hold applicable at the commit must refuse every one of them.
#:
#: `MC_RUN_STARTED` has no production writer today (N-D3 deferred) and is listed
#: anyway: naming it here is what makes a future writer inherit the refusal
#: instead of having to remember it.
START_EQUIVALENT_TOKENS = ("SUPPLEMENT_RUN_STARTED", "RUN_STARTED",
                           "MC_RUN_STARTED")


def is_start_equivalent(event: str) -> bool:
    """Does committing `event` mean governed execution has started?

    Bold-marked (`**TOKEN**`) and whitespace-padded spellings resolve to the
    same answer, because the row grammar admits both and a start that hid
    behind an asterisk would be exactly the bypass this exists to stop."""
    return (event or "").strip().strip("*").strip() in START_EQUIVALENT_TOKENS


def serialized_start_append(target: Path, addition: bytes, *, run_id: str,
                            decided: bytes | None = None) -> None:
    """Commit a START-EQUIVALENT event: the decisive owner-control decision and
    the physical append share ONE serialized decision.

    QROS-CF F06-OWNER-SEMANTICS. The final certification reproduced this
    supported ordering:

        1. a start-equivalent transition performs its final owner/control check
        2. an applicable unreleased OWNER_HOLD commits
        3. the in-progress transition appends RUN_STARTED
        4. the transition returns successfully

    Serialization was working; the SEMANTICS at the commit boundary were wrong.
    Two separate reasons, both real:

      * the S0 start path performed no owner-control check at all, anywhere,
        and appended with no `decided` snapshot -- so nothing could notice;
      * the supplement path did check, but on bytes read BEFORE the lock. Its
        compare-and-swap made that safe in effect, and "safe because a second
        mechanism happens to catch it" is not the contract. The contract wants
        the decision taken against the bytes being committed.

    So the check moved INSIDE. `validate` runs under the lock, on the
    authoritative current bytes, immediately before the write; a refusal there
    means no start row is written at all.

    NOT A NEW MECHANISM: same `_AppendLock`, same single physical write, same
    parsers, same canonical grammar, same applicability logic. Generic ordered
    appends are untouched -- only start-equivalent commits carry this refusal,
    which is why this is a separate entry rather than a flag on the generic one.
    """
    from . import owner_control as _oc

    def _decide(now: bytes) -> None:
        try:
            _oc.assert_no_hold_blocks_start(
                now.decode("utf-8", errors="replace"), run_id)
        except _oc.OwnerControlRefusal as exc:
            raise AppendRefused(
                "start_refused_owner_hold_in_force"
                if exc.code == "owner_hold_in_force"
                else "start_refused_owner_control_unreadable",
                "%s: %s" % (exc.code, exc.detail)) from exc

    serialized_append(target, addition, decided=decided, validate=_decide)


def serialized_append(target: Path, addition: bytes, *,
                      decided: bytes | None = None,
                      validate=None) -> None:
    """THE ONE serialization boundary for the governed registry.

    QROS-CF F06, PRE-CERT REPAIR. The final-cert writer inventory found a
    WORKFLOW-SUPPORTED writer that could not participate in serialization even
    in principle: `itsf.s0.runner.append_registry_event_line` receives the
    registry path as a PARAMETER and did `open(..., "a")` + `write(...)`.
    `scripts/s0_real_run.py` passes it the governed REGISTRY built from this
    module's own frozen constants, so it is a real supported path. Reproduced
    two ways: it wrote while `_AppendLock` was HELD by another writer, and --
    because it read nothing at all -- an OWNER_HOLD that landed first was
    invisible to it and its row went on top.

    ROOT CAUSE WAS LOCATION, NOT INTENT. The lock and the physical write lived
    only inside a private function of this module, so a supported writer in
    another module had nothing to call. Protecting STARTED and HOLD while a
    third supported writer mutated the same bytes outside serialization is not
    the F06 invariant, it is three quarters of it.

    So the boundary is exposed here, and it is deliberately MECHANISM ONLY: it
    takes bytes and knows no event vocabulary. That is why its callers are a
    REGISTERED set rather than an open door -- `test_n09_scaffold_criteria`
    pins who may call it, and `tests/test_qros_cf_f06_writer_completeness.py`
    pins that every supported governed-registry mutation path does.

    `decided` is the compare-and-swap half and stays OPTIONAL, because the two
    supported writer shapes genuinely differ:

      * a writer that made decisions on a snapshot passes it, and any
        intervening change refuses (`p3_registry_changed_under_decision`);
      * a writer that appends an event unconditionally passes none, and is
        still SERIALIZED -- it reads and writes under the same lock, so it
        cannot lose an update or interleave a half-written row.

    Serialization is what both need. Only the first needs the comparison, and
    requiring a snapshot from a writer that has none would have meant either
    inventing a fake one or leaving it outside -- which is the defect.
    """
    with _AppendLock(target):
        now = target.read_bytes()
        # THE AUTHORITATIVE SERIALIZED COMMIT DECISION (F06-OWNER-SEMANTICS).
        # `validate` is handed the bytes about to be committed against, under
        # the lock, so a decision made here cannot be stale by the time the
        # write happens. That is the whole difference between this and a check
        # performed before the lock and trusted afterwards.
        if validate is not None:
            validate(now)
        if decided is not None and now != decided:
            raise AppendRefused(
                "p3_registry_changed_under_decision",
                "the registry moved between the read every check was decided "
                "on (%d bytes, sha %s) and this append (%d bytes, sha %s); a "
                "start decided on stale state is never written"
                % (len(decided), hashlib.sha256(decided).hexdigest()[:12],
                   len(now), hashlib.sha256(now).hexdigest()[:12]))
        if now and not now.endswith(b"\n"):
            raise AppendRefused(
                "registry_tail_is_not_a_line",
                "the registry does not end in a newline, so appending would "
                "join two rows into one")
        target.write_bytes(now + addition)


def _compare_and_append(target: Path, decided: bytes, addition: bytes) -> None:
    """The compare-and-swap half, kept as the name the event writers call.

    QROS-CF F06 (first round). Append `addition` ONLY IF the file is still
    byte-identical to the version every check was decided on.

    THE CHECK AND THE WRITE MUST SHARE A VERSION. Re-reading and appending to
    whatever is there now is what let an OWNER_HOLD land between the hold
    check and the write: the hold was preserved by the second read and the P3
    went on top of it, so the committed order was HOLD then STARTED while the
    start had been authorized against pre-hold state. Comparing to `decided`
    makes that impossible -- any intervening commit, hold or otherwise,
    changes the bytes and this refuses.

    The two legal serialized orders both survive:
      * a hold commits first  -> bytes differ -> refuse, no P3 written;
      * this append wins      -> P3 committed, a later hold is ordered after
                                 it and does not retroactively unauthorize a
                                 start that was already legal.

    It performs no write of its own any more: the lock and the physical write
    moved into `serialized_append` so a supported writer in another module can
    reach them. Same lock, same single write.
    """
    serialized_append(target, addition, decided=decided)


def _next_global_sequence(rows) -> int:
    """The next value of the GLOBAL registry sequence.

    `SEQUENCE_NAMESPACE=GLOBAL` and
    `supplement_registry._check_global_sequence` already enforce "the NEXT
    value, not merely a larger one" -- a supplement row landing at 99 after a
    highest of 13 leaves 85 phantom slots and is refused. This derives the
    same number from the same rows rather than letting a caller pass one in:
    an owner filing a hold under pressure is the last person who should be
    hand-typing a sequence number, and a hand-typed one that is merely larger
    would wedge the sequence for every later row.
    """
    highest = None
    for row in rows:
        if not getattr(row, "numbered", False):
            continue
        seq = (getattr(row, "seq", "") or "").strip()
        if not re.fullmatch(r"[0-9]+", seq):
            continue
        value = int(seq)
        highest = value if highest is None else max(highest, value)
    return 1 if highest is None else highest + 1


def _append_owner_row(token: str, *, scope: str, reason: str,
                      head_commit: str, utc_stamp: str,
                      releases_event_sequence: int | None = None,
                      path=None) -> str:
    """Append Aaron's OWNER_HOLD / OWNER_RELEASE row. Returns the line.

    PRIVATE, AND THE TWO PUBLIC ENTRIES BELOW ARE WHY.
    `test_n09_scaffold_criteria` requires that no exported registry writer
    take its event as a caller-supplied value -- "a writer that took the token
    as a PARAMETER would be a general registry writer wearing a narrow name".
    That guard is right, and it caught this function's first shape. The fix was
    to match it rather than to relax it, so `token` never crosses the public
    surface and each exported entry names exactly one event.

    QROS-CF F06, SECOND ROUND. The first repair put the P3 append behind a
    sidecar lock and a compare-and-swap, and the re-review named exactly what
    that leaves standing: a lock protects a file only if every writer takes
    it, and there was NO SANCTIONED APPEND PATH FOR OWNER CONTROL AT ALL.
    Measured on the repaired tree: `owner_control` exposes no append function
    and writes nothing -- it is handed text and returns rows -- so the only
    way to file a hold was to edit the file by hand or by ad hoc script,
    which takes no lock and reads no `decided` snapshot. The serialization
    was one-sided: P3 was serialized against other P3s and against nothing
    else, which is the same as saying it was not serialized.

    So this is the missing half, and it is deliberately the SAME primitive
    rather than a second one. Both writers now take `_AppendLock` and both
    compare against the bytes their own checks were decided on, which is what
    leaves only the two legal orders:

      * the hold lands first -> P3's compare-and-swap sees changed bytes and
        refuses, so no start is written under a live hold;
      * P3 lands first       -> this append sees changed bytes and refuses;
        the owner re-reads and re-files against the state that now includes
        the start, so a hold is never applied to a stale snapshot.

    NOT A NEW GOVERNANCE LAYER, and no new artifact kind: the row shape,
    actor, scope grammar and field order are `owner_control`'s existing
    contract, the sequence rule is `supplement_registry`'s, and the
    post-write check asks `owner_control` itself whether the row it just
    wrote does what it claims. This function adds serialization and nothing
    else.
    """
    from . import owner_control as _oc
    from . import supplement_contract as _sc
    from . import supplement_registry as _sr

    if token not in _oc.OWNER_TOKENS:
        raise AppendRefused("owner_append_token_unknown", repr(token))
    if scope != _oc.GLOBAL_SCOPE and _oc.canonical_run_id_family(scope) is None:
        raise AppendRefused(
            "owner_append_scope_unrecognized",
            "%r is neither %s nor a run id of any authoritative family"
            % (scope, _oc.GLOBAL_SCOPE))
    if not _sc.HEX40_RE.match(head_commit or ""):
        raise AppendRefused("owner_append_commit_not_40hex", repr(head_commit))
    if not _REGISTRY_UTC_RE.match(utc_stamp or ""):
        raise AppendRefused("owner_append_utc_malformed", repr(utc_stamp))
    reason = (reason or "").strip()
    if not reason:
        raise AppendRefused("owner_append_reason_empty",
                            "an owner row carries a reason")
    # The note is a single six-cell field list. A `|` would forge a cell
    # boundary and a `;` a field boundary, so neither may ride inside the
    # reason text -- refused here rather than discovered by the parser after
    # the bytes are already in the ledger.
    for bad in ("|", ";", "\n", "\r"):
        if bad in reason:
            raise AppendRefused(
                "owner_append_reason_breaks_the_row",
                "reason may not contain %r; it would forge a cell or field "
                "boundary" % bad)
    if token == _oc.OWNER_RELEASE and releases_event_sequence is None:
        raise AppendRefused("owner_append_release_names_no_hold",
                            "OWNER_RELEASE must name releases_event_sequence")
    if token == _oc.OWNER_HOLD and releases_event_sequence is not None:
        raise AppendRefused("owner_append_hold_names_a_release",
                            "OWNER_HOLD releases nothing")

    target = (Path(path) if path is not None
              else REGISTRY_REPO_ROOT / REGISTRY_PATH)
    # ONE READ DECIDES, AND THAT READ IS WHAT GETS APPENDED TO -- the same
    # discipline as `append_run_started`, for the same reason.
    decided = target.read_bytes()
    text = _read_text(target, _bytes=decided)
    rows, refusal = _sr.parse_registry_rows(text)
    if refusal is not None:
        raise AppendRefused(
            "owner_append_registry_unparseable",
            "%s: %s" % (refusal.code, getattr(refusal, "detail", "")))
    # Every existing owner row must already be legal. Appending a release
    # onto a ledger whose holds cannot be read would decide nothing.
    try:
        _oc.parse_owner_rows(text)
    except _oc.OwnerControlRefusal as exc:
        raise AppendRefused("owner_append_existing_rows_unreadable",
                            "%s: %s" % (exc.code, exc.detail)) from exc
    seq = _next_global_sequence(rows)
    note = "[%s] " % scope
    if token == _oc.OWNER_RELEASE:
        note += "releases_event_sequence: %d; " % int(releases_event_sequence)
    note += "reason: %s" % reason
    row = ("| %d | %s | %s | %s | %s | %s |"
           % (seq, utc_stamp, token,
              head_commit[:_sc.COMMIT_WIDTH[_sc.NUMBERED]],
              _oc.OWNER_ACTOR, note))

    if not decided.endswith(b"\n"):
        raise AppendRefused("owner_append_registry_tail_is_not_a_line",
                            "the registry does not end in a newline")
    _compare_and_append(target, decided, (row + "\n").encode("utf-8"))

    # THE ROW MUST DO WHAT IT CLAIMS, asked of `owner_control` itself rather
    # than assumed -- the same post-write discipline `append_run_started`
    # uses, and the reason a malformed hold cannot land silently.
    after = _read_text(target)
    try:
        written = _oc.parse_owner_rows(after)
    except _oc.OwnerControlRefusal as exc:
        raise AppendRefused("owner_append_written_but_unreadable",
                            "%s: %s" % (exc.code, exc.detail)) from exc
    if not any(r.seq == seq and r.token == token for r in written):
        raise AppendRefused("owner_append_written_but_absent",
                            "seq %d is not an owner row of the ledger" % seq)
    probe = scope if scope != _oc.GLOBAL_SCOPE else _sc.FIRST_SUPPLEMENT_ID
    if token == _oc.OWNER_HOLD:
        if not any(h.seq == seq for h in _oc.active_holds(after, probe)):
            raise AppendRefused(
                "owner_append_hold_written_but_not_in_force",
                "OWNER_HOLD %d landed and is not an active hold for %s"
                % (seq, probe))
    else:
        released = int(releases_event_sequence)
        if any(h.seq == released for h in _oc.active_holds(after, probe)):
            raise AppendRefused(
                "owner_append_release_written_but_hold_still_active",
                "OWNER_RELEASE %d landed and hold %d is still in force"
                % (seq, released))
    return row


def append_owner_hold(*, scope: str, reason: str, head_commit: str,
                      utc_stamp: str, path=None) -> str:
    """File Aaron's OWNER_HOLD. One event, never a caller-supplied token."""
    from . import owner_control as _oc
    return _append_owner_row(_oc.OWNER_HOLD, scope=scope, reason=reason,
                             head_commit=head_commit, utc_stamp=utc_stamp,
                             path=path)


def append_owner_release(*, scope: str, reason: str, head_commit: str,
                         utc_stamp: str, releases_event_sequence: int,
                         path=None) -> str:
    """Release the OWNER_HOLD at `releases_event_sequence`. One event."""
    from . import owner_control as _oc
    return _append_owner_row(
        _oc.OWNER_RELEASE, scope=scope, reason=reason,
        head_commit=head_commit, utc_stamp=utc_stamp,
        releases_event_sequence=releases_event_sequence, path=path)


def append_run_started(supplement_id: str, *, head_commit: str,
                       utc_stamp: str, path=None) -> str:
    """Append THIS run's P3 row. Returns the line appended.

    Refuses, fail-closed, unless every one of these holds:

      * the id is a legal supplement id and its chain resolves cleanly;
      * that chain carries EXACTLY ONE live P2 -- the same authorization
        A_PRECHECK read -- so a run whose authorization is spent, absent or
        doubled cannot start;
      * the live P2's `authorized_commit` equals `head_commit`, the running
        tree's own commit, so P3 cannot be filed against a different build;
      * the chain carries NO P3 yet (exactly-once);
      * the row this function builds re-parses, lands on the id it names,
        and moves the chain to `started=True` with the P2 consumed.

    The last one is the load-bearing check: the file is re-read and
    re-resolved AFTER the write, so a row that would poison the chain is
    caught here rather than by the next reader. Nothing is written twice --
    on a post-write refusal the caller must stop, because the row IS in the
    ledger and only a person may decide what follows.

    RAISES rather than returning a status, and the caller places the call
    immediately before its first side effect: a refusal must leave no
    directory and no supplement byte behind.
    """
    from . import supplement_contract as _sc
    from . import supplement_registry as _sr

    if not _sc.SUPPLEMENT_ID_PATTERN.match(supplement_id or ""):
        raise AppendRefused("p3_supplement_id_pattern", repr(supplement_id))
    if not _sc.HEX40_RE.match(head_commit or ""):
        raise AppendRefused("p3_head_commit_not_40hex", repr(head_commit))
    if not _REGISTRY_UTC_RE.match(utc_stamp or ""):
        raise AppendRefused("p3_utc_stamp_malformed", repr(utc_stamp))

    target = (Path(path) if path is not None
              else REGISTRY_REPO_ROOT / REGISTRY_PATH)
    # ONE READ DECIDES, AND THAT READ IS WHAT GETS APPENDED TO (QROS-CF F06).
    # This function used to read the file twice: `text` for every check, then
    # a separate `before = target.read_bytes()` for the write. An OWNER_HOLD
    # committed between the two was invisible to the hold check AND present in
    # `before`, so the P3 was appended AFTER the hold using pre-hold state --
    # exactly the ordering the owner path must never produce. Reproduced
    # 2026-09-07 at that boundary. `decided` is now the single version: every
    # check below reads it, and the append is a compare-and-swap against it.
    decided = target.read_bytes()
    text = _read_text(target, _bytes=decided)
    chain = _sr.resolve_supplement_chain(text, supplement_id)
    problem = getattr(chain, "problem", "")
    if problem:
        raise AppendRefused("p3_chain_does_not_resolve", problem)
    if "P3" in tuple(getattr(chain, "short_ids", ())):
        raise AppendRefused(
            "p3_already_present",
            "%s already carries a %s row; one P2 authorizes one start"
            % (supplement_id, RUN_STARTED_TOKEN))
    live = getattr(chain, "live_authorizations", ())
    if len(live) != 1:
        raise AppendRefused(
            "p3_without_exactly_one_live_p2",
            "%d live %s row(s)" % (len(live), _sc.EVENTS["P2"].token))
    # QROS-CF I2: an owner hold appended after A_PRECHECK read its snapshot
    # is seen HERE, on the fresh read this append takes, before the write.
    from . import owner_control as _oc
    try:
        _oc.assert_no_owner_hold(text, supplement_id)
    except _oc.OwnerControlRefusal as exc:
        raise AppendRefused("p3_owner_hold_in_force"
                            if exc.code == "owner_hold_in_force"
                            else "p3_owner_control_row_unreadable",
                            "%s: %s" % (exc.code, exc.detail)) from exc
    authorized = getattr(live[0], "authorized_commit", "") or ""
    if authorized != head_commit:
        raise AppendRefused(
            "p3_commit_is_not_the_authorized_one",
            "authorized %s != running tree %s"
            % (authorized[:12], head_commit[:12]))

    row = ("| %s | %s | %s | %s | %s | %s |"
           % (_sc.UNNUMBERED_SEQ_TOKEN, utc_stamp, RUN_STARTED_TOKEN,
              head_commit[:_sc.COMMIT_WIDTH[_sc.UNNUMBERED]],
              _sc.ACTOR_RUNNER, _p3_note(supplement_id)))

    if not decided.endswith(b"\n"):
        raise AppendRefused("p3_registry_tail_is_not_a_line",
                            "the registry does not end in a newline")
    # F06-OWNER-SEMANTICS: the decisive hold check happens INSIDE the lock, on
    # the bytes being appended to. The pre-lock check above stays as a cheap
    # early refusal with its own code, but it is no longer what makes this safe.
    serialized_start_append(target, (row + "\n").encode("utf-8"),
                            run_id=supplement_id, decided=decided)

    after = _read_text(target)
    verified = _sr.resolve_supplement_chain(after, supplement_id)
    trouble = getattr(verified, "problem", "")
    if trouble:
        raise AppendRefused("p3_written_but_chain_now_refuses", trouble)
    if not getattr(verified, "started", False):
        raise AppendRefused("p3_written_but_not_started",
                            "the row landed and `started` is still False")
    if "P3" not in tuple(getattr(verified, "short_ids", ())):
        raise AppendRefused("p3_written_but_absent_from_the_chain",
                            str(getattr(verified, "short_ids", ())))
    return row
