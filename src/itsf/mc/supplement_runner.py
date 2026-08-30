"""N04 — supplement production runner. DEFAULT REFUSE.

MAIN-AGENT OWNED (lane leases: N03 authority = `supplement_authority.py`,
N05 registry = `supplement_registry.py`; this file and the integration
tests are the main agent's).

WHAT THIS IS. The runner that WOULD execute the MC-DS day-strata
supplement once Aaron issues an execution authorization, built under the
ratified `ND1_RECOMMENDED_PROFILE_R1` (sha256 0a08319a…, bound to doc
head 803d991…; see `ops/ND1_PROFILE_RATIFICATION.md`). It is shipped in
the state the ratification requires: **the production entry refuses
deterministically before touching anything**, because
`SUPPLEMENT_EXECUTION_AUTHORIZED=NO` and no live P2 exists in
`ops/TRIAL_REGISTRY.md`.

WHY IT IS SPLIT IN TWO. Everything that decides "what event does this
outcome become" is a PURE PLANNER over the ratified state machine — no
I/O, no clock, no data. The production entry is a thin gate-first shell
on top. That split is what makes the whole state machine testable at
full negative coverage with synthetic inputs while the real path stays
structurally unreachable. The planner NEVER appends a registry row; it
returns a `PlannedEvent` describing the row that a future authorized run
would append. Nothing in this module writes to `ops/TRIAL_REGISTRY.md`
or `EXPOSURE_LEDGER.md`.

THREE THINGS THIS ROUND DELIBERATELY DOES NOT DO, each because the
ratified profile says NO:

  * `ND1_WRITE_PROBE_AUTHORIZED=NO` — so the output-root gate is
    READ-ONLY. It deliberately does NOT call
    `runinfra.validate_output_roots_operational`, which writes and
    deletes a probe file in each root. Structure is observed; nothing is
    written.
  * `DIRECTORY_CREATION_AUTHORIZED=NO` — the `supplements\\` subtree gate
    OBSERVES absence and refuses; it never creates the subtree. Directory
    creation is a separate authorization
    (`SEPARATE_DIRECTORY_CREATION_AUTHORIZATION_STILL_REQUIRED=YES`).
  * `REAL_DATA_READ_AUTHORIZED=NO` — the only repository file this module
    reads is `ops/TRIAL_REGISTRY.md`, and that read happens on the
    production entry whose very next call is the refusal (the same
    discipline as `day_strata_supplement.run_supplement_production` and
    `consumer.run_real_mc`).
"""
from __future__ import annotations

import dataclasses as _dc
import os
import re
from pathlib import Path
from types import MappingProxyType
from typing import Callable, Mapping, NoReturn, Sequence

from . import supplement_authority as sa
from . import supplement_contract as sc

_REPO_ROOT = Path(__file__).resolve().parents[3]
#: Re-exported, not re-declared. The governed path is defined once, in
#: `registry_boundary`, which is the only module allowed to read it. This
#: module still NAMES it — the dirty-allowlist gate compares against it —
#: but naming and reading are now separated by construction rather than by
#: everyone remembering which is which.
from .registry_boundary import REGISTRY_PATH        # noqa: E402  (re-export)


class SupplementRunnerError(ValueError):
    """Fail-closed refusal from the runner. `code` is machine-readable
    (mirrors `consumer.MCInputError` / `day_strata_supplement
    .SupplementError` / `supplement_contract.SupplementGrammarError`)."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(f"{code}: {detail}" if detail else code)


class SupplementRunNotAuthorized(RuntimeError):
    """No live supplement execution authorization. The production entry
    raises this BEFORE any data access, directory creation or append."""


# ===========================================================================
# Gate table — the closure of `F1_GATE_NAME_ENUM`
# ===========================================================================
#
# `supplement_contract.GATE_TABLE` is the DECLARATION; the callables below
# are the IMPLEMENTATION. `tests/test_mc_supplement_runner.py` asserts the
# two agree exactly and in order, which is what makes the ratified enum
# "mechanically derived from the actual runner gates" rather than an
# aspirational list. A gate name with no callable, or a callable with no
# declared name, is a test failure — not a silently tolerated drift.


@_dc.dataclass(frozen=True, slots=True)
class GateContext:
    """Everything a gate may look at. Deliberately NARROW: a gate cannot
    reach the filesystem except through the paths named here, and cannot
    reach the registry except through `registry_text`."""
    supplement_id: str
    head_commit: str                    # 40-hex, the tree being run
    registry_text: str
    runs_root: Path | None
    archive_root: Path | None
    repo_dirty_paths: tuple = ()        # `git status --porcelain` paths
    g9_flag: Path | None = None
    second_copy_flag: Path | None = None
    frozen_hashes_ok: bool | None = None
    chain: object | None = None         # resolved chain (see RESOLVER_SEAM)
    authority: object | None = None     # SupplementAuthority (N03), or None
    # N06 repair: the authority alone proves nothing — every fact it
    # carries has to be re-derivable from the SAME prepared input it was
    # minted off. Without this field the B_DERIVE gates could only read
    # the authority's own self-report, which is how a hand-made stand-in
    # passed all of them at 617f7c3.
    prepared: object | None = None      # PreparedMCInput, or None
    utc_stamp: str = ""                 # run stamp for the path planner
    # The C_BUILD_1 outcome the three first-checkpoint gates CLASSIFY.
    # A `day_strata_pipeline.CBuildOutcome`, or None. None is refused by
    # those gates rather than passed: see `_classify_c_build_1`.
    c_build_outcome: object | None = None


@_dc.dataclass(frozen=True, slots=True)
class GateFailure:
    """A gate refusal, in the shape the F1/F2 planners consume."""
    stage: str
    gate_name: str
    error_class: str
    detail: str = ""


def _fail(stage: str, gate: str, error_class: str, detail: str = "") -> NoReturn:
    raise SupplementRunnerError(
        f"gate_refused:{gate}",
        f"stage {stage} gate '{gate}': {error_class}"
        + (f" ({detail})" if detail else ""))


# ===========================================================================
# Output-root path planner (PHASE E) - PURE, creates nothing
# ===========================================================================
#
# Ratified, and therefore not this module's to choose:
#   ND1_OUTPUT_ROOT_OPTION=A
#   ND1_SUPPLEMENT_DIRECTORY_NAME=2_ID_UNDERSCORE_UTC
#   ND1_FUTURE_DIRECTORY_POLICY=REUSE_EXISTING_ROOTS_WITH_supplements_SUBTREE
#
# The archive side is DERIVED from the governed archive root, never from
# the P2 authorization string - otherwise one authorization field could
# silently redirect where the second copy of the evidence lands.

SUPPLEMENTS_SUBDIR = "supplements"
UTC_STAMP_RE = re.compile(r"^\d{8}T\d{6}Z\Z")


def _norm(p) -> str:
    """Canonical form for PATH EQUALITY on this platform: absolute, with
    separators and case normalised. Deliberately NOT `resolve()`, which
    would follow a junction and hide the very substitution the reparse
    check below exists to catch."""
    return os.path.normcase(os.path.abspath(str(p)))


def _is_reparse(p: Path) -> bool:
    try:
        from itsf.s0.runinfra import _is_reparse_or_symlink
        return bool(_is_reparse_or_symlink(p))
    except Exception:                                         # noqa: BLE001
        return p.is_symlink()


def _strictly_under(child: Path, ancestor: Path) -> bool:
    """Depth-independent containment, the same predicate `runinfra` uses."""
    c, a = Path(_norm(child)), Path(_norm(ancestor))
    return c != a and a in c.parents


@_dc.dataclass(frozen=True, slots=True)
class PlannedPaths:
    """Where a future authorized run WOULD write. Planning is not
    creating: nothing in this module makes a directory."""
    supplement_id: str
    utc_stamp: str
    dir_name: str
    runs_target: Path
    archive_target: Path
    archive_parent: Path      # what `archive_sealed_run` must be passed


def plan_supplement_paths(*, runs_root, archive_root, supplement_id: str,
                          utc_stamp: str) -> PlannedPaths:
    """Derive and VALIDATE both targets. Refuses; never creates."""
    if not sc.SUPPLEMENT_ID_PATTERN.match(supplement_id or ""):
        raise SupplementRunnerError("plan_supplement_id_pattern",
                                    repr(supplement_id))
    if not UTC_STAMP_RE.match(utc_stamp or ""):
        raise SupplementRunnerError(
            "plan_utc_stamp_malformed",
            f"{utc_stamp!r} is not YYYYMMDDTHHMMSSZ")
    for label, root in (("runs_root", runs_root),
                        ("archive_root", archive_root)):
        if root is None or str(root) == "":
            raise SupplementRunnerError("plan_root_missing", label)
        p = Path(root)
        if not p.is_absolute():
            raise SupplementRunnerError("plan_root_not_absolute",
                                        f"{label}: {root}")
        if not p.exists():
            raise SupplementRunnerError("plan_root_absent", f"{label}: {root}")
        if not p.is_dir():
            raise SupplementRunnerError("plan_root_not_a_directory", label)
        if _is_reparse(p):
            raise SupplementRunnerError("plan_root_is_reparse_point", label)

    dir_name = f"{supplement_id}_{utc_stamp}"
    runs_parent = Path(runs_root) / SUPPLEMENTS_SUBDIR
    archive_parent = Path(archive_root) / SUPPLEMENTS_SUBDIR
    runs_target = runs_parent / dir_name
    archive_target = archive_parent / dir_name

    if not _strictly_under(runs_target, Path(runs_root)):
        raise SupplementRunnerError("plan_target_escapes_root", "runs")
    if not _strictly_under(archive_target, Path(archive_root)):
        raise SupplementRunnerError("plan_target_escapes_root", "archive")
    if runs_target.name != archive_target.name:
        raise SupplementRunnerError(
            "plan_basename_divergence",
            f"{runs_target.name} != {archive_target.name}")
    if _norm(runs_target) == _norm(archive_target):
        raise SupplementRunnerError("plan_targets_collide",
                                    "runs and archive resolve to one path")
    for label, target in (("runs", runs_target), ("archive", archive_target)):
        if target.exists():
            raise SupplementRunnerError("plan_target_exists",
                                        f"{label}: {target}")
        parent = target.parent
        if parent.exists() and _is_reparse(parent):
            raise SupplementRunnerError("plan_parent_is_reparse_point",
                                        f"{label}: {parent}")
    return PlannedPaths(supplement_id=supplement_id, utc_stamp=utc_stamp,
                        dir_name=dir_name, runs_target=runs_target,
                        archive_target=archive_target,
                        archive_parent=archive_parent)


# --- A_PRECHECK ------------------------------------------------------------

def _g_g9_hard_blocker(ctx: GateContext) -> None:
    flag = ctx.g9_flag
    if flag is None or not Path(flag).exists():
        _fail("A_PRECHECK", "g9_hard_blocker", "RunBlockedError",
              "G9 CME fee component unconfirmed; flag absent")


def _g_second_copy_attested(ctx: GateContext) -> None:
    flag = ctx.second_copy_flag
    if flag is None or not Path(flag).exists():
        _fail("A_PRECHECK", "second_copy_attested", "RunBlockedError",
              "charter second-copy attestation flag absent")


def _g_frozen_hashes(ctx: GateContext) -> None:
    if ctx.frozen_hashes_ok is not True:
        _fail("A_PRECHECK", "frozen_hashes", "FrozenTamperError",
              "frozen-file hash verification did not pass")


def _g_git_clean(ctx: GateContext) -> None:
    # The registry is append-only BY DESIGN, so an uncommitted registry
    # append does not dirty the tree for this gate (same allowlist the S0
    # runner uses). Everything else does.
    dirty = [p for p in ctx.repo_dirty_paths if p != REGISTRY_PATH]
    if dirty:
        _fail("A_PRECHECK", "git_clean", "RunGateError",
              f"{len(dirty)} unexpected dirty path(s): {sorted(dirty)[:3]}")


def _g_supplement_id_pattern(ctx: GateContext) -> None:
    if not sc.SUPPLEMENT_ID_PATTERN.match(ctx.supplement_id or ""):
        _fail("A_PRECHECK", "supplement_id_pattern", "SupplementRunnerError",
              f"{ctx.supplement_id!r} does not match "
              f"{sc.SUPPLEMENT_ID_PATTERN.pattern}")


def _g_registry_chain_resolvable(ctx: GateContext) -> None:
    chain = ctx.chain
    if chain is None:
        _fail("A_PRECHECK", "registry_chain_resolvable", "SupplementRunnerError",
              "no resolved chain was supplied")
    problem = getattr(chain, "problem", None)
    if problem:
        # §D.3.5 ANY_CHAIN_DEFECT=REFUSE_WHOLE_RESOLUTION — a defective
        # chain never degrades to "ignore the bad row and continue".
        _fail("A_PRECHECK", "registry_chain_resolvable", "SupplementRunnerError",
              str(problem))


def _live_p2(chain) -> object | None:
    live = getattr(chain, "live_authorizations", None)
    if live is None:
        return None
    return live[0] if len(live) == 1 else None


def _g_live_authorization_unique(ctx: GateContext) -> None:
    live = getattr(ctx.chain, "live_authorizations", ())
    if len(live) == 0:
        _fail("A_PRECHECK", "live_authorization_unique",
              "SupplementRunNotAuthorized",
              f"no live {sc.EVENTS['P2'].token} row for {ctx.supplement_id}")
    if len(live) > 1:
        _fail("A_PRECHECK", "live_authorization_unique", "SupplementRunnerError",
              f"{len(live)} live authorizations — at most one is legal")


def _g_authorization_actor(ctx: GateContext) -> None:
    row = _live_p2(ctx.chain)
    actor = (getattr(row, "actor", "") or "").strip()
    if sc.ACTOR_AARON not in actor:
        _fail("A_PRECHECK", "authorization_actor", "SupplementRunnerError",
              f"authorization actor {actor!r} is not {sc.ACTOR_AARON}")


def _g_authorized_commit_matches_head(ctx: GateContext) -> None:
    row = _live_p2(ctx.chain)
    commit = (getattr(row, "authorized_commit", "") or "")
    if not sc.HEX40_RE.match(commit):
        _fail("A_PRECHECK", "authorized_commit_matches_head",
              "SupplementRunnerError", "authorized commit is not 40-hex")
    if commit != ctx.head_commit:
        _fail("A_PRECHECK", "authorized_commit_matches_head",
              "SupplementRunnerError",
              f"authorized {commit[:12]} != HEAD {ctx.head_commit[:12]}")


def _g_output_root_declared(ctx: GateContext) -> None:
    row = _live_p2(ctx.chain)
    root = getattr(row, "output_root", None)
    if not root:
        _fail("A_PRECHECK", "output_root_declared", "SupplementRunnerError",
              "the authorization names no output root")


def _g_output_root_structure(ctx: GateContext) -> None:
    """READ-ONLY, and now BINDING.

    `ND1_WRITE_PROBE_AUTHORIZED=NO`, so this gate still writes nothing -
    no probe, no directory. What changed at the N06 repair is that the
    `output_root` Aaron authorized in P2 must be the SAME PATH the runner
    is actually about to use. At 617f7c3 the gate only asked whether the
    field was non-empty, so an authorization naming a completely
    different root - or a relative path - was accepted while the run used
    the governed root regardless."""
    for label, root in (("runs_root", ctx.runs_root),
                        ("archive_root", ctx.archive_root)):
        if root is None:
            _fail("A_PRECHECK", "output_root_structure", "RunGateError",
                  f"{label} was not supplied")
        p = Path(root)
        if not p.is_absolute():
            _fail("A_PRECHECK", "output_root_structure", "RunGateError",
                  f"{label} is not an absolute path")
        if not p.exists():
            _fail("A_PRECHECK", "output_root_structure", "RunGateError",
                  f"{label} does not exist - this gate never creates it")
        if not p.is_dir():
            _fail("A_PRECHECK", "output_root_structure", "RunGateError",
                  f"{label} is not a directory")
        if _is_reparse(p):
            _fail("A_PRECHECK", "output_root_structure", "RunGateError",
                  f"{label} is a symlink/junction/reparse point")

    declared = getattr(_live_p2(ctx.chain), "output_root", "")
    if not str(declared).strip():
        _fail("A_PRECHECK", "output_root_structure", "RunGateError",
              "the authorization names no output root")
    if not Path(str(declared)).is_absolute():
        _fail("A_PRECHECK", "output_root_structure", "RunGateError",
              f"authorized output_root {declared!r} is not absolute")
    if _norm(declared) != _norm(ctx.runs_root):
        _fail("A_PRECHECK", "output_root_structure", "RunGateError",
              f"authorized output_root {declared!r} is not the runs_root "
              f"this run would use ({ctx.runs_root})")


def _g_supplement_subtree_absent(ctx: GateContext) -> None:
    """OBSERVES the EXACT planned targets; never creates anything.

    At 617f7c3 this gate looked for a bare `supplements/<id>` path, which
    is not the ratified directory name - `ND1_SUPPLEMENT_DIRECTORY_NAME=
    2_ID_UNDERSCORE_UTC` makes it `<id>_<UTC>` - so the check could never
    have seen a real collision. It now plans the actual pair and lets the
    planner refuse an existing target, a reparse point or an escape."""
    if not ctx.utc_stamp:
        _fail("A_PRECHECK", "supplement_subtree_absent", "RunGateError",
              "no UTC stamp supplied; the target directory name is "
              "<supplement_id>_<UTC> and cannot be planned without it")
    try:
        plan_supplement_paths(runs_root=ctx.runs_root,
                              archive_root=ctx.archive_root,
                              supplement_id=ctx.supplement_id,
                              utc_stamp=ctx.utc_stamp)
    except SupplementRunnerError as exc:
        _fail("A_PRECHECK", "supplement_subtree_absent", "RunGateError",
              f"{exc.code}: {exc}")


def _g_id_not_retired(ctx: GateContext) -> None:
    if getattr(ctx.chain, "retired", False):
        _fail("A_PRECHECK", "id_not_retired", "SupplementRunnerError",
              f"{ctx.supplement_id} was retired (F3/AX); "
              "ID_REUSE_POLICY=NEVER_AFTER_START")


# --- B_DERIVE --------------------------------------------------------------

def _require_real_authority(gate: str, ctx: GateContext):
    """F4/F5 (adversarial battery). Every B_DERIVE gate re-asserts the
    EXACT type, not just the first one.

    F4: the gate used `isinstance` while `verify_supplement_authority`
    uses `type(...) is`, so a `__new__`-built SUBCLASS cleared the gate
    whose stated job is "type, not shape" and died one gate later.
    F5: three gates read attributes without any type check at all, so a
    field-for-field mirror of a real authority was accepted by each of
    them individually. Stage order hid it; a test that claimed otherwise
    was overclaiming, which is worse than the hole."""
    auth = ctx.authority
    if type(auth) is not sa.SupplementAuthority:
        _fail("B_DERIVE", gate, "SupplementRunnerError",
              f"{type(auth).__name__} is not exactly SupplementAuthority — "
              "a subclass or a field-compatible mirror is not an authority")
    if ctx.prepared is None:
        _fail("B_DERIVE", gate, "SupplementRunnerError",
              "no prepared input supplied — nothing can be re-derived")
    return auth


def _g_custody_authority_production(ctx: GateContext) -> None:
    """Type, not shape. A field-compatible stand-in is NOT an authority.

    At 617f7c3 this gate read attributes off whatever object it was
    handed, so a six-field dataclass passed the whole of B_DERIVE while a
    genuine `SupplementAuthority` was REFUSED (it exposes
    `bundle_table_digest`, the gate asked for `file_sha256_digest`). The
    seam was inverted: forgeries in, real objects out."""
    auth = ctx.authority
    if auth is None:
        _fail("B_DERIVE", "custody_authority_production",
              "SupplementRunnerError", "no supplement authority supplied")
    _require_real_authority("custody_authority_production", ctx)
    if auth.test_only:
        _fail("B_DERIVE", "custody_authority_production",
              "SupplementRunnerError",
              "a test_only authority may never enter the production path")
    prepared = ctx.prepared
    if prepared is None:
        _fail("B_DERIVE", "custody_authority_production",
              "SupplementRunnerError",
              "no prepared input supplied — the authority cannot be "
              "re-verified against its own source")
    if getattr(prepared, "test_only", True):
        _fail("B_DERIVE", "custody_authority_production",
              "SupplementRunnerError",
              "a test_only prepared input may never enter production")


def _g_custody_authority_binding(ctx: GateContext) -> None:
    """Re-verify the authority against the prepared input it claims, and
    tie both to the authorization row and the running tree."""
    _require_real_authority("custody_authority_binding", ctx)
    auth, prepared = ctx.authority, ctx.prepared
    try:
        sa.verify_supplement_authority(auth, prepared,
                                       supplement_id=ctx.supplement_id)
    except Exception as exc:                                  # noqa: BLE001
        _fail("B_DERIVE", "custody_authority_binding",
              type(exc).__name__, str(getattr(exc, "code", exc))[:80])
    row = _live_p2(ctx.chain)
    want = getattr(row, "authorized_commit", None)
    if want and auth.authorized_commit != want:
        _fail("B_DERIVE", "custody_authority_binding", "SupplementRunnerError",
              f"authority commit {auth.authorized_commit[:12]} != authorized "
              f"{str(want)[:12]}")
    if auth.authorized_commit != ctx.head_commit:
        _fail("B_DERIVE", "custody_authority_binding", "SupplementRunnerError",
              f"authority commit {auth.authorized_commit[:12]} != HEAD "
              f"{ctx.head_commit[:12]}")
    if auth.supplement_id != ctx.supplement_id:
        _fail("B_DERIVE", "custody_authority_binding", "SupplementRunnerError",
              "authority supplement id differs from the run's")


def _g_source_bundle_digest(ctx: GateContext) -> None:
    """RECOMPUTE from the prepared input; never read the self-report."""
    _require_real_authority("source_bundle_digest", ctx)
    auth, prepared = ctx.authority, ctx.prepared
    got = sa.bundle_table_digest(prepared.file_sha256)
    if got != auth.bundle_table_digest:
        _fail("B_DERIVE", "source_bundle_digest", "SupplementRunnerError",
              f"recomputed {got[:12]} != authority {auth.bundle_table_digest[:12]}")


def _g_day_universe_identity(ctx: GateContext) -> None:
    """Re-run the §D.2.2 enforcement over the prepared input and compare
    the digest. The authority carrying A digest is not evidence that it
    carries THIS one."""
    _require_real_authority("day_universe_identity", ctx)
    auth, prepared = ctx.authority, ctx.prepared
    try:
        identity = sa.enforce_day_universe_identity(prepared)
    except Exception as exc:                                  # noqa: BLE001
        _fail("B_DERIVE", "day_universe_identity",
              type(exc).__name__, str(getattr(exc, "code", exc))[:80])
    if identity.day_universe_digest != auth.day_universe_digest:
        _fail("B_DERIVE", "day_universe_identity", "SupplementRunnerError",
              f"recomputed {identity.day_universe_digest[:12]} != authority "
              f"{auth.day_universe_digest[:12]}")
    if identity.n_days != auth.n_days:
        _fail("B_DERIVE", "day_universe_identity", "SupplementRunnerError",
              f"day count {identity.n_days} != authority {auth.n_days}")


def _g_method_version_pinned(ctx: GateContext) -> None:
    _require_real_authority("method_version_pinned", ctx)
    auth = ctx.authority
    if auth.method_version != sa.SUPPLEMENT_METHOD_VERSION:
        _fail("B_DERIVE", "method_version_pinned", "SupplementRunnerError",
              f"{auth.method_version!r} != pinned "
              f"{sa.SUPPLEMENT_METHOD_VERSION!r}")
    if not auth.method_digest:
        _fail("B_DERIVE", "method_version_pinned", "SupplementRunnerError",
              "authority carries no method digest")


# --- C_BUILD ---------------------------------------------------------------

def _classify_c_build_1(ctx: GateContext, gate: str) -> None:
    """The whole body of a C_BUILD_1 gate: CLASSIFY the producer's outcome.

    Gate doctrine, R3 §3: a gate classifies the outcome of a call. It does
    not observe inside the call and does not implement a second copy of the
    invariant. `day_strata_rows` enforces the invariant and refuses with a
    code; `day_strata_classify` maps that code to exactly one gate; this
    reports it in the F1/F2 vocabulary. Re-checking the rows HERE would be
    the R2 defect in a new place — two implementations of one invariant,
    drifting apart at the first change to either.

    ABSENCE IS A REFUSAL, NEVER A PASS. With no outcome attached, this gate
    has classified nothing, and passing would put "no defect found" on
    record about a build that never ran. That is the same false direction
    `day_strata_failure.p3_boundary` refuses, and it is reached without
    doing anything wrong — just by leaving a field unset.
    """
    from .day_strata_failure import ERROR_CLASS_OF_PRODUCER_REFUSAL

    outcome = ctx.c_build_outcome
    if outcome is None:
        _fail("C_BUILD", gate, "SupplementRunnerError",
              "no C_BUILD outcome is attached to this context, so this gate "
              "classified nothing; a pass would report 'no defect' about a "
              "build that never ran")
    failure = outcome.belongs_to(gate)
    if failure is not None:
        _fail("C_BUILD", gate, ERROR_CLASS_OF_PRODUCER_REFUSAL,
              "%s: %s" % (failure.code, failure.detail))


def _g_row_schema_blind(ctx: GateContext) -> None:
    # The blind guarantee is enforced row-by-row by
    # `day_strata_supplement._validate_row`; this gate exists so the
    # failure has a NAMED stage/gate in the F1/F2 vocabulary.
    _classify_c_build_1(ctx, "row_schema_blind")


def _g_day_set_exact(ctx: GateContext) -> None:
    _classify_c_build_1(ctx, "day_set_exact")


def _g_rows_digest_recompute(ctx: GateContext) -> None:
    _classify_c_build_1(ctx, "rows_digest_recompute")


def _g_seal_staging_partial(ctx: GateContext) -> None:
    # C_BUILD_2, and DELIBERATELY still refusing while the three C_BUILD_1
    # gates above have been wired. Two reasons, neither of them "not got
    # to it yet":
    #
    #   1. Nothing is ever sealed on this path — `assert_real_run_allowed`,
    #      directory creation and P2 all still refuse, so there is no
    #      staging outcome for this gate to classify.
    #   2. WAS "its wording is out for review". THAT IS NO LONGER TRUE and
    #      the comment said otherwise for five rounds -- it still cited
    #      ROUND3 and pin d34ce7c, a review that returned on 2026-08-30 and
    #      was followed by four more. A comment asserting a review is in
    #      progress, months after it closed, is the same defect this whole
    #      review kept finding in my own claims: a sentence that was true
    #      when written and false when read.
    #
    #      Where the wording actually stands: eight rounds, all HOLD, all
    #      findings reproduced and closed, capped by Aaron's OD-1 and
    #      delivered at `ops/DELIVERY_C_BUILD_2_WORDING_AT_CAP_2026-08-30.md`
    #      with its residuals marked ACCEPTED_BY_CAP. The specification is
    #      settled; reason 1 is what still makes this gate unreachable, and
    #      reason 1 alone is enough.
    _fail("C_BUILD", "seal_staging_partial", "SupplementRunnerError",
          "unreachable in this build: nothing is ever sealed (and the "
          "C_BUILD_2 wording is out for review)")


def _g_archive_policy_a(ctx: GateContext) -> None:
    # C_BUILD_3, and this one must NOT become an ordinary classifier at all.
    # `ROUTER_OF` gives its outcome to Router B (`decide_after_seal`),
    # because routing it as an ordinary gate sends a refusal through
    # Router A to F2 while ratified `ND1_ARCHIVE_FAILURE_POLICY=A` requires
    # A1. That contradiction is executed by
    # `test_routing_it_as_an_ordinary_gate_contradicts_policy_a` — measured,
    # not hypothetical. Wiring it here would re-create it.
    _fail("C_BUILD", "archive_policy_a", "SupplementRunnerError",
          "unreachable in this build: nothing is ever archived, and Router B "
          "owns this gate's outcome (ROUTER_OF) — see decide_after_seal")


GATES: Mapping[str, Callable[[GateContext], None]] = MappingProxyType({
    "g9_hard_blocker": _g_g9_hard_blocker,
    "second_copy_attested": _g_second_copy_attested,
    "frozen_hashes": _g_frozen_hashes,
    "git_clean": _g_git_clean,
    "supplement_id_pattern": _g_supplement_id_pattern,
    "registry_chain_resolvable": _g_registry_chain_resolvable,
    "live_authorization_unique": _g_live_authorization_unique,
    "authorization_actor": _g_authorization_actor,
    "authorized_commit_matches_head": _g_authorized_commit_matches_head,
    "output_root_declared": _g_output_root_declared,
    "output_root_structure": _g_output_root_structure,
    "supplement_subtree_absent": _g_supplement_subtree_absent,
    "id_not_retired": _g_id_not_retired,
    "custody_authority_production": _g_custody_authority_production,
    "custody_authority_binding": _g_custody_authority_binding,
    "source_bundle_digest": _g_source_bundle_digest,
    "day_universe_identity": _g_day_universe_identity,
    "method_version_pinned": _g_method_version_pinned,
    "row_schema_blind": _g_row_schema_blind,
    "day_set_exact": _g_day_set_exact,
    "rows_digest_recompute": _g_rows_digest_recompute,
    "seal_staging_partial": _g_seal_staging_partial,
    "archive_policy_a": _g_archive_policy_a,
})


def run_stage_gates(stage: str, ctx: GateContext) -> None:
    """Run one stage's gates IN DECLARED ORDER, first refusal wins. The
    order is the contract's, not this module's — so the reported gate is
    reproducible from the governance text."""
    if stage not in sc.STAGE_ENUM:
        raise SupplementRunnerError("stage_outside_closed_enum", stage)
    for name in sc.GATE_TABLE[stage]:
        GATES[name](ctx)


# ===========================================================================
# Pure planner over the ratified state machine
# ===========================================================================


@_dc.dataclass(frozen=True, slots=True)
class PlannedEvent:
    """A registry row a future AUTHORIZED run would append. Constructing
    one appends nothing: this object is a description, and the runner has
    no code path that writes a registry file."""
    short_id: str
    token: str
    row_class: str
    actor: str
    fields: Mapping

    def __post_init__(self) -> None:
        spec = sc.spec_for_short_id(self.short_id)
        if self.token != spec.token:
            raise SupplementRunnerError("planned_event_token_mismatch",
                                        f"{self.token} != {spec.token}")
        if self.row_class != spec.row_class:
            raise SupplementRunnerError("planned_event_row_class_mismatch",
                                        self.row_class)
        missing = [f for f in spec.required_fields if f not in self.fields]
        if missing:
            raise SupplementRunnerError("planned_event_missing_field",
                                        f"{self.short_id}: {missing}")
        extra = [f for f in self.fields if f not in spec.required_fields]
        if extra:
            raise SupplementRunnerError("planned_event_unknown_field",
                                        f"{self.short_id}: {sorted(extra)}")
        if spec.incident_required:
            inc = str(self.fields.get("incident_id", ""))
            if not sc.INCIDENT_RE.match(inc):
                raise SupplementRunnerError("planned_event_incident_malformed",
                                            f"{self.short_id}: {inc!r}")
        object.__setattr__(self, "fields", MappingProxyType(dict(self.fields)))


def _check_stage_and_gate(stage: str, gate_name: str) -> None:
    if stage not in sc.STAGE_ENUM:
        raise SupplementRunnerError("stage_outside_closed_enum", stage)
    if gate_name not in sc.GATE_NAME_ENUM:
        # §D.3.2 F1: "GATE_NAME_ENUM=CLOSED … 未定义即不得发射".
        raise SupplementRunnerError("gate_outside_closed_enum", gate_name)
    if gate_name not in sc.GATE_TABLE[stage]:
        raise SupplementRunnerError("gate_not_in_stage",
                                    f"{gate_name} is not a {stage} gate")


def plan_failure_event(failure: GateFailure, *, supplement_id: str,
                       incident_id: str, has_p3: bool,
                       attempts_dir: str = "", residue_path: str = ""
                       ) -> PlannedEvent:
    """F1 vs F2 is decided by the P3 BOUNDARY, never by the stage name
    (§D.3.2 P3: `BOUNDARY=P3 是 pre-start / post-start 的唯一分界`)."""
    _check_stage_and_gate(failure.stage, failure.gate_name)
    if not sc.SUPPLEMENT_ID_PATTERN.match(supplement_id):
        raise SupplementRunnerError("supplement_id_pattern", supplement_id)
    if has_p3:
        if not residue_path:
            raise SupplementRunnerError(
                "post_start_residue_path_required",
                "F2 must name the preserved residue; RESIDUE=NEVER_DELETED")
        return PlannedEvent(
            "F2", sc.EVENTS["F2"].token, sc.UNNUMBERED, sc.ACTOR_RUNNER,
            {"supplement_id": supplement_id, "stage": failure.stage,
             "error_class": failure.error_class, "incident_id": incident_id,
             "residue_path": residue_path, "residue_preserved": "YES"})
    if not attempts_dir:
        raise SupplementRunnerError("pre_start_attempts_dir_required",
                                    "F1 must name the attempts directory")
    return PlannedEvent(
        "F1", sc.EVENTS["F1"].token, sc.UNNUMBERED, sc.ACTOR_RUNNER,
        {"supplement_id": supplement_id, "stage": failure.stage,
         "gate_name": failure.gate_name, "error_class": failure.error_class,
         "incident_id": incident_id,
         "consumption_statement": "nothing consumed",
         "attempts_dir": attempts_dir})


def plan_next_short_id(from_short_id: str, *, outcome: str,
                       commit_changed: bool | None = None) -> str:
    """The ratified transition function. `outcome` is a discriminant, not
    a free string: an unknown one refuses rather than defaulting."""
    spec = sc.spec_for_short_id(from_short_id)

    if from_short_id == "F1":
        # §D.3.2 F1 successors, under the ratified
        # PRESTART_COMMIT_CHANGE_REAUTH=YES.
        if outcome == "abandon":
            nxt = "F3"
        elif outcome == "retry":
            if commit_changed is None:
                raise SupplementRunnerError(
                    "prestart_commit_change_undeclared",
                    "a pre-start retry must declare whether the commit moved")
            nxt = "P2S" if commit_changed else "P3"
        else:
            raise SupplementRunnerError("unknown_outcome",
                                        f"F1/{outcome!r}")
    elif from_short_id == "P3":
        # R3, ratified 2026-08-27: a crash with no terminal event is
        # adjudicated by CR1. Note this is the ONLY new outcome — a crash
        # does not become a seal, a failure, or an archive problem, and
        # FORBIDDEN_EDGES states the three it may not become.
        nxt = {"sealed_archive_ok": "P4",
               "sealed_archive_failed": "A1",
               "post_start_failure": "F2",
               "crash_resolved": "CR1"}.get(outcome, "")
    elif from_short_id == "CR1":
        # Retirement is the only way out. The run is not revived — that is
        # what ("CR1","P3") in FORBIDDEN_EDGES says positively.
        nxt = "F3" if outcome == "retire" else ""
    elif from_short_id == "A1":
        nxt = {"recovered": "A2", "permanent": "AX"}.get(outcome, "")
    elif from_short_id == "P4":
        nxt = {"verified": "P5", "verification_failed": "F2v"}.get(outcome, "")
    elif from_short_id == "A2":
        nxt = "P5" if outcome == "verified" else ""
    elif from_short_id == "AX":
        nxt = "F3" if outcome == "retire" else ""
    elif from_short_id in ("F2", "F2v"):
        nxt = "F3" if outcome == "retire" else ""
    elif from_short_id == "F3":
        nxt = "T1" if outcome == "successor" else ""
    elif from_short_id in ("P1", "T1"):
        nxt = {"authorize": "P2", "abandon": "F3"}.get(outcome, "")
        if from_short_id == "T1" and outcome == "abandon":
            nxt = ""
    elif from_short_id == "P2S":
        nxt = "P2" if outcome == "reauthorize" else ""
    elif from_short_id == "P2":
        nxt = {"start": "P3", "pre_start_failure": "F1",
               "abandon": "F3"}.get(outcome, "")
    else:
        nxt = ""

    if not nxt:
        raise SupplementRunnerError("unknown_outcome",
                                    f"{from_short_id}/{outcome!r}")
    if sc.is_forbidden_edge(from_short_id, nxt):
        raise SupplementRunnerError("forbidden_edge",
                                    f"{from_short_id} -> {nxt}")
    if nxt not in spec.successors:
        raise SupplementRunnerError("illegal_transition",
                                    f"{from_short_id} -> {nxt}")
    return nxt


def assert_chain_closed(short_ids: Sequence[str]) -> str:
    """A chain is closed only at P5 or F3 (§D.3.3). A1 and AX are traps:
    stopping at either is an UNCLOSED chain, not a terminal."""
    if not short_ids:
        raise SupplementRunnerError("empty_chain", "no events")
    last = short_ids[-1]
    if last in sc.NON_TERMINAL_TRAPS:
        # DERIVED FROM THE SUCCESSOR DATA, not a hardcoded table. The
        # previous form was a two-branch ternary naming AX and A1, and
        # adding CR1 to the traps made it tell a CR1 chain that "A1 must be
        # followed by A2 or AX" — measured, 2026-08-27. That is the third
        # time an event was added and a hand-maintained string went stale;
        # the ratified successors already say what may follow, so they are
        # what the message reads from.
        successors = sc.EVENTS[last].successors
        allowed = (" or ".join(successors) if successors
                   else "nothing (its successor list is empty)")
        raise SupplementRunnerError(
            "chain_stops_at_non_terminal",
            f"{last} is not a terminal; {last} must be followed by {allowed}")
    if last not in sc.TERMINAL_SHORT_IDS:
        raise SupplementRunnerError("chain_not_closed", last)
    return last


# ===========================================================================
# Archive policy A
# ===========================================================================


def classify_archive_report(report) -> str:
    """Map an `ArchiveReport` onto the CLOSED `ARCHIVE_CODES` enum using
    STRUCTURE only — never the free-text `errors` prose, which is not a
    contract. Bucketing is TOTAL: an `archive_failed` report that matches
    nothing raises `archive_report_unclassified` rather than landing in a
    catch-all, so an archive failure nobody modelled stops the chain."""
    status = getattr(report, "status", None)
    if status == "archive_ok":
        raise SupplementRunnerError("archive_ok_has_no_code",
                                    "a successful archive carries no code")
    if status != "archive_failed":
        raise SupplementRunnerError("archive_status_unknown", repr(status))
    inventory = getattr(report, "inventory", None)
    if inventory is None:
        return "inventory_unavailable"
    files = tuple(getattr(report, "files", ()) or ())
    if any(f.source_sha256 is None or f.dest_sha256 is None for f in files):
        return "file_unreadable"
    if any(f.match is False for f in files):
        return "file_digest_mismatch"
    verdicts = (inventory.source_stable, inventory.staging_matches_source,
                inventory.dest_matches_source,
                inventory.source_stable_after_verify)
    if any(v is False for v in verdicts):
        return "set_equality_refused"
    if any(v is None for v in verdicts):
        return "set_equality_unreached"
    raise SupplementRunnerError(sc.ARCHIVE_UNCLASSIFIED_CODE,
                                "archive_failed but no structural cause found")


def decide_after_seal(*, local_seal_ok: bool, archive_report) -> str:
    """Policy A (`ND1_ARCHIVE_FAILURE_POLICY=A`, ratified):
    `P4_SUPPLEMENT_SEALED_REQUIRES=local_seal_ok AND archive_ok`. A local
    seal that succeeded while the archive failed does NOT become a P4 —
    it becomes A1, and P5 stays unreachable until A2."""
    if not local_seal_ok:
        raise SupplementRunnerError("local_seal_failed",
                                    "no P4 and no A1: nothing was sealed")
    if getattr(archive_report, "status", None) == "archive_ok":
        return "P4"
    classify_archive_report(archive_report)      # validates / may refuse
    return "A1"


# ===========================================================================
# `.partial` recovery — the ratified MODIFY rule
# ===========================================================================
#
# `ND1_PARTIAL_RECOVERY_RULE=MODIFY`, text:
#   BRANCH_E_RENAME_TO_.partial.divergent.<incident_id>;
#   BRANCH_C_RENAME_THEN_ALLOW_RETRY
# and the derived `SILENT_DELETE_FORBIDDEN=YES`. Nothing below unlinks a
# byte it did not just prove is a duplicate of something it keeps.


@_dc.dataclass(frozen=True, slots=True)
class PartialAction:
    """What `resolve_partial` did / decided. `preserved_as` is non-empty
    whenever bytes were moved aside instead of destroyed."""
    action: str            # already_sealed | promote | retry_permitted
    preserved_as: str = ""
    detail: str = ""


def _divergent_name(base: str, incident_id: str) -> str:
    if not sc.INCIDENT_RE.match(incident_id or ""):
        raise SupplementRunnerError("incident_id_malformed", repr(incident_id))
    return base + sc.DIVERGENT_PARTIAL_TEMPLATE.format(incident_id=incident_id)


def _preserve(path: Path, incident_id: str) -> str:
    """Move bytes aside instead of destroying them. The name is
    `<filename>.partial.divergent.<incident_id>` exactly as ratified."""
    base = path.name.removesuffix(sc.PARTIAL_SUFFIX)
    target = path.parent / _divergent_name(base, incident_id)
    # never clobber a prior incident's preserved evidence
    if target.exists():
        raise SupplementRunnerError(
            "divergent_partial_exists",
            f"{target.name} already exists — a second incident may not "
            "overwrite the first one's preserved bytes")
    os.replace(path, target)
    return target.name


#: Characters that cannot appear in a plain file name. Not a list I
#: invented: these are the separators plus the NTFS stream marker.
_FORBIDDEN_IN_A_NAME = ("/", "\\", ":")


def _require_plain_name(filename: str) -> str:
    """REFUSE anything that is not a bare file name.

    ADDED 2026-08-30 after round 7 DISPROVED this function's own docstring.
    It claimed "Every write this function performs lands under `out_dir`",
    and `resolve_partial(out, "../escaped.json", ...)` promoted a file into
    out_dir's PARENT. Nothing validated `filename`; `out / filename` simply
    resolved wherever it was pointed, and an absolute path would have
    replaced `out` entirely.

    The claim was in the docstring for months. What makes this worth saying
    is that the claim was never the defect -- the MISSING CHECK was, and the
    claim is what made nobody look for it.

    A NAME, not a path. So the refusal is stated over the argument's own
    vocabulary rather than over mechanisms:

      * empty, or not equal to its own basename -- catches "..", "a/b",
        "/abs", "C:/abs" (whose basename is "abs" on Windows)
      * containing a separator or a colon -- catches the NTFS alternate
        data stream form "x.json:evidence", whose basename IS itself and
        which writes bytes that a directory listing never shows. Round 7
        found that stream class separately; this is the half of it that
        belongs to the production path.
    """
    # `.` and `..` are named explicitly because pathlib does NOT strip
    # them: `Path("..").name` is `".."`, so the basename comparison below
    # holds and `out / ".."` walks to the parent. Measured, not assumed --
    # the first version of this check let `..` straight through and the
    # call died on a PermissionError reading a directory.
    if (not filename or filename in (".", "..")
            or filename != Path(filename).name):
        raise SupplementRunnerError(
            "filename_not_a_plain_name",
            f"{filename!r} is not a bare file name; every write must land "
            "directly under out_dir")
    for ch in _FORBIDDEN_IN_A_NAME:
        if ch in filename:
            raise SupplementRunnerError(
                "filename_not_a_plain_name",
                f"{filename!r} contains {ch!r}")
    return filename


def resolve_partial(out_dir: Path, filename: str, intended: bytes, *,
                    incident_id: str) -> PartialAction:
    """Stage `intended` into `<filename>.partial` and decide what happens.

    Branches, and what each does with existing bytes:

      final == intended              -> already_sealed   (nothing written)
      final != intended              -> REFUSE `supplement_seal_conflict`
                                        (a sealed supplement is never
                                        overwritten; nothing deleted)
      C: stale partial == intended   -> promote          (completes a crash)
      C: stale partial != intended   -> RENAME the debris to
                                        `.partial.divergent.<incident>` and
                                        return `retry_permitted` — the
                                        evidence survives AND the path is
                                        unblocked, which is the whole point
                                        of the ratified MODIFY
      E: written, re-read != intended-> RENAME the unreliable bytes aside
                                        and REFUSE `supplement_partial_verify`
                                        (the previous implementation
                                        UNLINKED them; silent delete is now
                                        forbidden)

    Every write this function performs lands under `out_dir` — and since
    round 7 that is CHECKED rather than asserted. `_require_plain_name`
    refuses anything that is not a bare file name; before it, this
    sentence was simply false for `../escaped.json`.
    """
    out = Path(out_dir)
    _require_plain_name(filename)
    final = out / filename
    partial = out / (filename + sc.PARTIAL_SUFFIX)

    if final.exists():
        existing = final.read_bytes()
        if existing == intended:
            return PartialAction("already_sealed", detail="byte-identical")
        raise SupplementRunnerError(
            "supplement_seal_conflict",
            f"{final.name} already sealed with different bytes — a sealed "
            "supplement is never overwritten")

    if partial.exists():
        residue = partial.read_bytes()
        if residue != intended:
            preserved = _preserve(partial, incident_id)          # branch C
            return PartialAction("retry_permitted", preserved_as=preserved,
                                 detail="divergent residue moved aside")
        # byte-identical residue: a prior attempt crashed after the
        # verified write; promotion below completes it.
    else:
        partial.write_bytes(intended)

    if partial.read_bytes() != intended:                          # branch E
        preserved = _preserve(partial, incident_id)
        raise SupplementRunnerError(
            "supplement_partial_verify",
            f"staged bytes re-read differently; preserved as {preserved} "
            "(SILENT_DELETE_FORBIDDEN)")
    os.replace(partial, final)
    if final.read_bytes() != intended:
        raise SupplementRunnerError(
            "supplement_post_promotion_verify",
            "post-promotion re-read diverged from the verified staging bytes")
    return PartialAction("promote", detail="staged, verified, promoted")


# ===========================================================================
# Production entry — gate-first, deterministic refusal
# ===========================================================================

#: The N05 seam. Injected in tests; in production it resolves through
#: `supplement_registry`. If that module is missing or does not expose the
#: resolver, the runner REFUSES rather than proceeding without a chain.
RESOLVER_SEAM = "itsf.mc.supplement_registry"


def _default_resolver(registry_text: str, supplement_id: str):
    try:
        from . import supplement_registry as _sr
    except Exception as exc:                                  # noqa: BLE001
        raise SupplementRunNotAuthorized(
            f"supplement registry resolver unavailable ({type(exc).__name__})"
            " — no chain can be resolved, so no authorization can exist"
        ) from exc
    for name in ("resolve_supplement_chain", "resolve_chain", "resolve"):
        fn = getattr(_sr, name, None)
        if callable(fn):
            return fn(registry_text, supplement_id)
    raise SupplementRunNotAuthorized(
        f"{RESOLVER_SEAM} exposes no chain resolver — refusing")


def run_supplement_production(supplement_id: str = sc.FIRST_SUPPLEMENT_ID,
                              *, resolver: Callable | None = None,
                              **_ignored) -> NoReturn:
    """PRODUCTION entry. Gate-first, exactly like
    `real_input.prepare_real_mc_input` and
    `day_strata_supplement.run_supplement_production`.

    The ONLY repository file read here is `ops/TRIAL_REGISTRY.md`, and the
    very next thing that happens is the refusal. No Development data is
    opened, no output root is touched, no directory is created, no probe
    is written, nothing is appended. Everything past the authorization
    gate is unreachable while `SUPPLEMENT_EXECUTION_AUTHORIZED=NO`.

    THAT READ NOW GOES THROUGH THE BOUNDARY (C2 as ratified, 2026-08-25).
    It used to be a direct `read_text` here plus a direct resolver call —
    one of four independent reads of the same mutable file across the
    package. `registry_boundary.resolve_for_supplement` reads once and
    runs BOTH lifecycles against that one snapshot, so an MC refusal
    arrives as this chain's own `problem` and the existing A_PRECHECK gate
    refuses on it without any gate being changed.
    """
    from itsf.guards import G9_FLAG, SECOND_COPY_FLAG, assert_real_run_allowed
    assert_real_run_allowed(G9_FLAG, SECOND_COPY_FLAG)

    from . import registry_boundary as _rb
    if resolver is None:
        _snapshot, chain = _rb.resolve_for_supplement(supplement_id)
    else:
        # TEST SEAM. It swaps the RESOLVER only — never the read. An
        # injected resolver still receives the boundary's single snapshot,
        # so this function has exactly one read path whether or not a test
        # is driving it. Giving the seam its own `read_text` would put a
        # second read of a mutable file back into production code, which
        # is the loophole C2 was rewritten to close.
        snapshot = _rb.read_snapshot()
        chain = resolver(snapshot.text, supplement_id)

    problem = getattr(chain, "problem", None)
    if problem:
        raise SupplementRunNotAuthorized(
            f"supplement chain for {supplement_id} does not resolve: "
            f"{problem} (ANY_CHAIN_DEFECT=REFUSE_WHOLE_RESOLUTION)")
    live = getattr(chain, "live_authorizations", ())
    if len(live) != 1:
        raise SupplementRunNotAuthorized(
            f"{supplement_id}: {len(live)} live "
            f"{sc.EVENTS['P2'].token} row(s) — exactly one is required; "
            "execution requires Aaron's exact authorization sentence "
            "binding the supplement id, the full 40-hex commit and the "
            "output root (ratified profile: "
            "ND1_SUPPLEMENT_EXECUTION_AUTHORIZED=NO)")
    raise SupplementRunNotAuthorized(
        f"{supplement_id}: a live authorization row exists but this build "
        "carries no execution path — N04 ships DEFAULT-REFUSE and the "
        "ratification authorizes grammar, not execution")
