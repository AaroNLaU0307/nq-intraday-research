"""S0 -> MC handoff schema skeleton (E6). SCHEMA_VERSION = "m6.1-draft-1".

Scope of THIS module: package the day-level classification, the Appendix-A
grid samples, and the frozen seed/stream provenance into a byte-stable JSON
shape MC can consume and REPLAY, WITHOUT deciding any method question itself.
This module DECIDES nothing. It either READS a ruling that already exists in
the single ruled source (`contracts.aaron_ruled_methods()`, threaded in by the
caller as `methods=`), or it emits a disclosed, greppable UNRESOLVED marker —
the same discipline `dataset.py` uses for the ruled DR-2/DR-6 vocabularies and
`gridmix.py` uses for the ruled DR-3/DR-5 dispatch keys.

POST-RULING STATE (Aaron ruled all eight method decisions on 2026-08-10)
------------------------------------------------------------------------
Each of the three builders takes a keyword-only `methods=None`:

  * `methods=None` — the LEGACY default — reproduces the pre-ruling output
    BIT FOR BIT: every axis that carried an UNRESOLVED marker still carries
    exactly that marker, and the `DEFAULT_SOURCE_CONTEXT` injection seam is
    untouched. No existing caller changes meaning.
  * a FULLY-RESOLVED `ResolvedS0Methods` makes every axis whose ruling now
    exists emit the RULED value, read STRUCTURALLY off `methods` (no ruled
    literal is ever restated in this file), and the matching problem entry
    disappears, so `formal_sealable = not problems` re-evaluates honestly.
    Nothing is forced: the conditions decide, and the axes that are genuinely
    still open keep blocking.

Threading the rulings is the ENTRY POINT's job: no function here reaches for
`contracts.aaron_ruled_methods()` on its own, because a module that silently
adopted the rulings would hide WHICH context sealed an artifact from the call
site that must disclose it. `source_context_for_methods` is the one adapter.

PRODUCTION-REACHABILITY STATUS: PARTIAL (do not read this module as a
production pipeline)
---------------------------------------------------------------------------
`build_seed_manifest` is the ONLY builder here with a production caller
(`scripts/s0_real_run.render_s0_report` puts `SEED_MANIFEST.json` into the
admission candidate set). POST-INTEGRATION POSTURE (S0 closeout,
2026-08-10): that caller now passes BOTH `methods=` (the validated config's
rulings) AND `source=source_context_for_methods(methods)` — so with a
fully-resolved non-test_only ruling set the produced SEED_MANIFEST carries
ruled k_policy/crn_scope values, is sealable, and is ADMITTED; with
TEST_ONLY methods it stays withheld (both outcomes are chain-tested). `build_day_strata` / `build_grid_samples`
have NO production caller at this HEAD — B0 source-lineage rows **L144 and
L145 are `NOT PRODUCED`**. Everything the day_strata / grid_samples semantic
checkers below achieve is therefore a guard against *fabricated* artifacts
and a contract for a future producer; it is NOT evidence that any real
DAY_STRATA or GRID_SAMPLES artifact exists, is reachable, or has ever been
sealed. No claim of production reachability is made anywhere in this module.

RC-2: admission recomputes SEMANTICS, from an INDEPENDENT source context
---------------------------------------------------------------------------
Before M6.1.4 `formal_seal_admission` recomputed semantics for exactly ONE
field family (SEED_MANIFEST seeds + stream tags, matrix VF-12) and schema
only for everything else — which is why a blind audit could get 24
full-schema-but-semantically-wrong artifacts ADMITTED (matrix classes D1-D13
day_strata, D26-D34 grid_samples, D39-D41 seed_manifest). The fix has three
parts:

1. **One pure spec-driven checker per artifact type** —
   `check_day_strata_semantics` / `check_grid_samples_semantics` /
   `check_seed_manifest_semantics`. These are the single source of the
   invariants: the builders call them to guarantee their own output and
   admission calls them too.
2. **An explicit SOURCE CONTEXT.** A checker that sees only the artifact can
   never prove more than internal consistency ("builder and admission both
   ran the same checker over the same self-reported object" is not
   independent proof). Every checker therefore takes a `SourceContext`: the
   frozen constants (`study.FROZEN_THETAS`, `study.ENGINES`,
   `contracts.RESEARCH_BOOTSTRAP_SEEDS`, `stability.EPOCHS`,
   `context.MICRO_ERA_BOUNDARY`, `context.F10_CATEGORIES`,
   `gridmix.Q_GRID_MILLIS`/`R_GRID_MILLIS`/`GRID_STREAM_TAG`,
   `stats.STATS_STREAM_TAG`), plus optional dataset facts, plus one explicit
   RULING SLOT per method axis, `None` by default — `None` meaning "this
   context was handed no ruling there", which since 2026-08-10 is a statement
   about the CALL, not about the decision. Expected content is REBUILT from
   that context and compared; the artifact's own self-report is never the
   basis of its own verification.
3. **Bundle-level ATOMIC admission.** A GRID_SAMPLES artifact depends on
   exactly ONE valid DAY_STRATA and exactly ONE valid SEED_MANIFEST supplied
   in the SAME call. Absent / duplicated / invalid dependency ⇒ the dependent
   artifact is withheld too, with the dependency chain named in its problem
   string. A lone GRID_SAMPLES can never bypass the graph.

THE INJECTION SEAM (how a test makes an artifact admissible)
-------------------------------------------------------------
Because admission REBUILDS expected content, no string an artifact carries
can make it sealable on an unruled axis. A test that needs admission to
ADMIT must therefore change the SOURCE, not the artifact. Two seams exist,
both defaulting to the production sources:

1. `formal_seal_admission(artifacts, source=SourceContext(...))` — the
   keyword-only parameter, for any caller that can pass one.
2. `handoff.DEFAULT_SOURCE_CONTEXT` — read from the module namespace at CALL
   time, so `monkeypatch.setattr(handoff, "DEFAULT_SOURCE_CONTEXT", ...)`
   reaches callers that pass no `source` at all (notably
   `scripts/s0_real_run.render_s0_report`, which calls
   `formal_seal_admission(candidates)` positionally). This is the seam a
   renderer-level test must use to prove the gate is DECIDED by admission
   rather than by a hardcoded exclusion.

A PRODUCTION caller uses neither: it passes the ruled method set
(`source=source_context_for_methods(methods)`), which fills exactly the ruled
slots and nothing else. None of the three seams lets an artifact authorise
itself — the ruling is visible in the source context a reviewer reads, never
buried in the bytes being sealed.

The context is TYPE-PINNED (`type(ctx) is SourceContext` — a duck type and a
subclass are both refused) and its FIELD VALUES are RE-VALIDATED on every
admission call, because `@dataclass(frozen=True)` blocks ordinary assignment
but not `object.__setattr__`. HONEST BOUNDARY, stated rather than implied:
that catches a context mutated to GARBAGE (a re-anchored frozen constant, a
bare-str vocabulary, an empty theta axis, a truthy non-bool gate). It does
NOT catch a context mutated to a PLAUSIBLE ruling — in-process, a
well-formed `k_policy` written past the frozen dataclass is indistinguishable
from a caller who legitimately passed it. Validation can check
well-formedness and pinning, never intent. The config gate carries exactly
the same documented boundary; the defence against in-process writes to module
globals is the frozen-file hash gate, not this module.

FAIL-CLOSED BOTH WAYS on an unruled axis
-----------------------------------------
For an axis with no ruling (`SourceContext` slot is `None`):
  * the ONLY admissible value is one of THIS module's UNRESOLVED markers —
    an arbitrary "approved-looking" string (`"TEST_ONLY_resolved_stratum"`,
    `"resolved"`, `"CLOSED_multi_stratum"`, …) is REFUSED because it matches
    no ruled vocabulary; and
  * the UNRESOLVED marker itself makes the artifact NOT SEALABLE.
There is no value that both passes vocabulary and permits sealing while the
axis is unruled. That is the point.

What is FROZEN, what is RULED, and what is STILL OPEN
-----------------------------------------------------
FROZEN:
  * contracts.RESEARCH_BOOTSTRAP_SEEDS {7, 13, 31} is the only source of
    research randomness (IR DR-02) — `build_seed_manifest` asserts this by
    identity rather than by value, so a future local copy anywhere upstream
    would be caught here too.
  * the quoted-seed convention (first frozen seed, never best-of) and the
    stats/grid stream tags are read FROM those modules' own constants, never
    restated as a second copy.
  * the epoch boundaries come from `stability.EPOCHS` ONLY (matrix CR-4:
    `dataset.STABILITY_EPOCHS` uses a different, half-open interval
    convention — this module must never introduce a third).
  * the theta key format comes from `study.theta_key` (matrix CR-11: the
    former local `_theta_key` duplicate is deleted).

RULED 2026-08-10 (emitted ONLY when `methods` is supplied; the marker below
is what `methods=None` still emits, and it is then a TRUE disclosure of what
that particular call was given, not a claim that the DR is open):
  * DR-6 (was "DR-M6-F") — `event_flag_final` -> Appendix-A event stratum.
    With `methods`, `build_day_strata` DERIVES each day's `event_stratum`
    from the day's OWN `event_flag_final` through `dataset.event_stratum_of`
    — the owner of that gate — over the five-stratum `dataset.EVENT_STRATA`
    vocabulary. `build_day_strata` still REFUSES a day_row carrying its own
    `"event_stratum"` key on BOTH paths: the value is DERIVED from the ruled
    mapping or it is a marker, never a caller-supplied vocabulary.
  * DR-2 (was "DR-M6-B-v2") — the 20-day realized-volatility axis. The
    per-day LABELS still come from the caller's day rows exactly as before
    (this module never computes vol20); what the ruling supplies is the
    VOCABULARY — `dataset.VOL_ALL_LABELS`, the three terciles plus the ruled
    `vol_na` fourth stratum — so a real label becomes admissible and an
    UNRESOLVED marker stops being admissible on that axis.
  * DR-5 (was "DR-M6-E") — the replay `k_policy`, encoded by `ruled_k_policy`
    from `methods.grid_policy`'s own fields (K per seed, k start index, theta
    in the stream, max doublings, convergence rule).
  * DR-4.7 — `crn_scope`, read from `methods.bootstrap_method.crn_scope` and
    pinned against the scope `stats.py` actually implements. This is the
    S0-side scope only; the MC cross-platform CRN was already frozen in
    MC_METHOD_SPEC §5 and is not this module's axis.

STILL OPEN — and the blocker is MC WIRING, not a pending ruling:
  * MULTI-STRATUM REPLAY CLOSURE. `replay_status` stays
    `PARTIAL_single_stratum_only` on BOTH paths and `REPLAY_STATUS_CLOSED`
    stays deliberately unreachable here. What is missing is no longer a
    vocabulary — with `methods`, DAY_STRATA carries the full
    (year, vol_status, event_stratum) Appendix-A key — it is the REPLAY
    ITSELF: `build_grid_samples` carries ONE repeat per (seed, cell), namely
    gridmix's headline `k = k_start_index` row, and the frozen cell schema
    has no `repeats` block, while DR-5 rules K repeats per seed with theta in
    the stream; and the MC_METHOD_SPEC §5 four-rule convergence battery and
    its doubling loop run AT THE MC WIRING and supply `mc_converged`, which
    no S0-side artifact can assert. A replayer cannot rebuild the ruled
    repeat set from these bytes, so CLOSED would be a lie.
  * TEST_ONLY rulings. `methods.test_only=True` travels onto the source
    context as `rulings_are_test_only` and keeps EVERY artifact resolved from
    it not-sealable — the same fail-closed discipline
    `dataset.event_stratum_of` and `study.py`'s quantile-estimator gate
    already apply to a TEST_ONLY value on a production path.

Ownership note: `src/itsf/s0/report.py` and `tests/test_s0_report.py` are
owned by a PARALLEL agent in this same round; this module deliberately does
NOT import anything from `report.py` (nor does it duplicate report.py's own
canonical-JSON helper by reference — `dumps_canonical` here is a separate,
self-contained implementation of the identical
`json.dumps(..., allow_nan=False, sort_keys=True)` recipe). The main agent is
expected to unify the two canonical-JSON helpers later (matrix CR-10); until
then this module must not create a cross-import dependency on the other
agent's in-flight file.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import NamedTuple

from itsf import contracts
from itsf.s0 import context as s0_context
from itsf.s0 import dataset as s0_dataset
from itsf.s0 import gridmix as s0_gridmix
from itsf.s0 import stability as s0_stability
from itsf.s0 import stats as s0_stats
from itsf.s0 import study as s0_study

SCHEMA_VERSION = "m6.1-draft-1"


# ===========================================================================
# frozen axis locks (M6.1.1 S2 item 2 — Codex finding (b): "the θ/engine/
# scenario/seed axes are not locked nor cross-checked against SEED_MANIFEST")
# ===========================================================================
# Every constant below is READ from its single-sourced owner rather than
# retyped here, so this module cannot silently drift from the value the rest
# of the codebase actually uses (the same discipline `build_seed_manifest`
# already applies, by identity, to the seed tuple).
ENGINES = s0_study.ENGINES              # frozen: S0 §7 (import study.ENGINES,
                                        # never a local ("E1", "E2") copy)
FROZEN_THETAS = s0_study.FROZEN_THETAS  # frozen: S0 §7 L133 (import
                                        # study.FROZEN_THETAS, never a local
                                        # (0.5, 0.3) copy)
# frozen: S0 §6 cost-scenario grid (itsf.s0.costs.build_scenarios / frozen S0
# SS6 "Base / Conservative / Stress / Severe"). No single importable tuple
# constant exists upstream for this axis today (costs.build_scenarios returns
# a name-keyed dict built from the same four literals) — this is the ONE
# place it is spelled out, with its frozen citation, rather than re-typed at
# every call site in this module.
SCENARIOS = ("Base", "Conservative", "Stress", "Severe")
# frozen: S0 §9 / Appendix A step 3 seeds {7,13,31}; identical object to
# contracts.RESEARCH_BOOTSTRAP_SEEDS (never a local copy — IR DR-02).
FROZEN_SEEDS = contracts.RESEARCH_BOOTSTRAP_SEEDS

# ===========================================================================
# REPLAY STATUS honesty (M6.1.1 S2 item 5 — Codex finding (e): "multi-stratum
# replay must stay PARTIAL, never claimed CLOSED")
# ===========================================================================
# `build_grid_samples` reconstructs a replay from day_strata's TP/FP
# classification and the per-cell selected dates. POST-RULING (2026-08-10) the
# STRATUM VOCABULARY is no longer what blocks closure — with `methods`,
# day_strata carries the real `(year, vol_status, event_stratum)` Appendix-A
# key on the ruled DR-2/DR-6 vocabularies. What blocks closure now is the
# REPLAY ITSELF, and it is MC-side:
#   * DR-5 rules K repeats per seed per cell with theta in the stream, but a
#     GRID_SAMPLES cell carries only gridmix's HEADLINE repeat row
#     (k = k_start_index) per seed — the frozen cell schema has no `repeats`
#     block, and SCHEMA_VERSION is frozen, so the repeat set is simply not in
#     these bytes; and
#   * the MC_METHOD_SPEC §5 four-rule convergence battery and its doubling
#     loop are OWNED AT THE MC WIRING (gridmix runs doublings=0 and declares
#     no verdict), so no S0-side artifact can assert `mc_converged`.
# That gap must be MACHINE-VISIBLE, not just a docstring sentence a reader
# might not reach: `build_grid_samples` output always carries
# `"replay_status"`, and `REPLAY_STATUS_CLOSED` below is a target this module
# is not yet able to emit (deliberately unreachable, on BOTH the legacy and
# the ruled path) — never write "CLOSED" as a status literally produced
# anywhere in this file while that remains true.
REPLAY_STATUS_PARTIAL_SINGLE_STRATUM = "PARTIAL_single_stratum_only"
REPLAY_STATUS_CLOSED = "CLOSED_multi_stratum"

# The disclosed grid-point stream recipe (gridmix `_grid_point`:
# `default_rng([master_seed, GRID_STREAM_TAG, q_mil, r_mil])`). Restated ONCE
# here, as a named constant, so `build_grid_samples` writes it and the
# semantic checker REBUILDS it from the same constant rather than from the
# artifact's own copy (a tampered stream_formula is otherwise invisible).
REPLAY_STREAM_FORMULA = "default_rng([master, GRID_STREAM_TAG, q_mil, r_mil])"

# The frozen SEED_MANIFEST prose. Named constants, not inline literals, for
# exactly one reason: admission REBUILDS the whole manifest from these and
# requires deep equality, so a manifest whose prose has been rewritten (e.g.
# to claim "quoted = best-of three seeds") is refused as content, not merely
# unread. # frozen: S0 §9 quoted-seed convention; IR DR-02 engineering seed.
QUOTED_SEED_CONVENTION = (
    "quoted interval/selection = the FIRST frozen master seed, by "
    "fixed convention that predates any data (never best-of); all "
    "seeds are independently run and always reported in full")
ENGINEERING_SEED_NOTE = (
    "run-infra provenance only; value recorded in governance "
    "metadata, not here")


# ===========================================================================
# UNRESOLVED sentinel
# ===========================================================================

class _UnresolvedSentinel(str):
    """Singleton sentinel for a field this call has no ruling for.

    WHAT IT MEANS SHIFTED ON 2026-08-10, and the shift matters: before the
    rulings it meant "the method decision is open"; now it means "no ruling
    was handed to THIS call" (`methods=None` / an unruled `SourceContext`
    slot). Both are true statements about the call that emitted it — what it
    never means is "a value exists and was withheld". A marker on an axis
    whose ruling WAS handed in is a false disclosure, and the checkers refuse
    it (see `_unruled_axis_check`).

    Subclasses `str` with the literal value "UNRESOLVED" so it survives plain
    JSON serialization and any `== "UNRESOLVED"` check downstream unchanged,
    while remaining identity-comparable (`is UNRESOLVED`) so a caller can
    still distinguish "genuinely blocked, marked by this module" from a field
    that merely happens to hold that literal string for an unrelated reason.
    """
    _instance: "_UnresolvedSentinel | None" = None

    def __new__(cls) -> "_UnresolvedSentinel":
        if cls._instance is None:
            cls._instance = super().__new__(cls, "UNRESOLVED")
        return cls._instance

    def __repr__(self) -> str:
        return "UNRESOLVED"


UNRESOLVED = _UnresolvedSentinel()


def _unresolved(decision_id: str) -> str:
    """A disclosed, greppable stand-in for a value this call carries no
    ruling for, tagged with the decision record that governs the axis (e.g.
    "DR-M6-F" -> "UNRESOLVED_DR-M6-F"). Never silently resolved by picking a
    vocabulary — the ruling is READ from `methods`, or the marker stands. The
    tags keep their historical DR-M6-* spelling because they are already in
    sealed bytes; the module docstring maps each one to the DR that rules it.
    """
    return f"UNRESOLVED_{decision_id}"


def _is_unresolved(value: object) -> bool:
    """True iff `value` is one of THIS module's own UNRESOLVED markers (the
    bare sentinel, or a decision-tagged "UNRESOLVED_..." string). Used only
    to DERIVE `formal_sealable` below — it never changes what a field's
    value actually is, and it never resolves anything itself."""
    return value is UNRESOLVED or (isinstance(value, str)
                                   and value.startswith("UNRESOLVED"))


# ===========================================================================
# canonical JSON
# ===========================================================================

def dumps_canonical(obj: object) -> str:
    """The ONE canonical serialization this module uses for anything destined
    for a byte-stable handoff artifact: `sort_keys=True` for reproducible
    byte output, `allow_nan=False` so a NaN/Infinity raises loudly instead of
    silently emitting non-standard JSON (frozen S0 §3 NA policy: NA is
    reported through explicit sentinels — None, "UNRESOLVED_*", explicit NA
    reason strings — never a JSON NaN literal)."""
    return json.dumps(obj, allow_nan=False, sort_keys=True)


# ===========================================================================
# STRICT type predicates
# ===========================================================================
# M6.1.4 item 3: seeds / theta / counts / flags must be EXACT types. `bool` is
# not `int` here even though it is in Python's type lattice, `7.0` is not `7`,
# and `"7"` is nothing at all. NO `int()` / `float()` / `str()` coercion is
# applied to any artifact value anywhere in a validation path in this module —
# a wrongly-typed value is a refusal, never silently normalised into the type
# it should have been. (The only surviving coercions are in BUILD paths and
# are individually justified at their call sites.)

def _is_strict_int(value: object) -> bool:
    """True iff `value` is a genuine `int` — never `bool` (which subclasses
    `int`), `float` (not even 7.0), or a numeric string."""
    return type(value) is int


def _is_strict_float(value: object) -> bool:
    """True iff `value` is a genuine `float` — never `int`, never `bool`."""
    return type(value) is float


def _is_strict_str(value: object) -> bool:
    """True iff `value` is a genuine `str` — never a `str` SUBCLASS (which is
    how `_UnresolvedSentinel` sneaks through an `isinstance` check), never
    bytes."""
    return type(value) is str


def _is_strict_bool(value: object) -> bool:
    return type(value) is bool


def _sorted_items(mapping: Mapping) -> list:
    """`mapping.items()` in a deterministic order that survives MIXED-TYPE
    keys (`sorted()` alone raises `TypeError` on `{1: …, "a": …}`, which a
    fuzzed artifact will absolutely contain). Falls back to insertion order
    if even the repr-based key raises."""
    try:
        return sorted(mapping.items(),
                      key=lambda kv: (type(kv[0]).__name__, repr(kv[0])))
    except Exception:                       # pragma: no cover - paranoia
        try:
            return list(mapping.items())
        except Exception:                   # pragma: no cover - paranoia
            return []


# ===========================================================================
# safe rendering (a hostile value's own __repr__/__str__ may raise)
# ===========================================================================

def _safe_repr(value: object) -> str:
    """`repr(value)` that cannot itself raise. Used anywhere a refusal string
    has to name a value that may be adversarial — a message this module
    cannot even CONSTRUCT would turn a refusal into an escaping exception."""
    try:
        return repr(value)
    except Exception:
        try:
            return f"<unrenderable {type(value).__name__}>"
        except Exception:                   # pragma: no cover - paranoia
            return "<unrenderable>"


def _safe_reason(exc: BaseException) -> str:
    """An exception rendered for a refusal string, without trusting its own
    `__str__`."""
    try:
        text = str(exc)
    except Exception:                       # pragma: no cover - paranoia
        text = "(unrenderable message)"
    return f"{type(exc).__name__}: {text}"


# ===========================================================================
# ISO date parsing
# ===========================================================================
# `[0-9]` (NOT `\d`) and `\A…\Z` (NOT `^…$`) are BOTH load-bearing:
#   * Python's `\d` matches every Unicode decimal digit, so `\d{4}` happily
#     accepts fullwidth "２０１９";
#   * `$` matches immediately BEFORE a trailing newline, so `^…$` accepts
#     "2019-06-03\n".
# Both used to be caught only downstream (blind-audit A16). They are now
# refused by the pattern itself, and `date.fromisoformat` REMAINS
# LOAD-BEARING as the calendar backstop: the regex cannot know that
# 2019-02-30 or 2019-13-01 is not a day. Neither check is redundant — do not
# delete either one, and never `.strip()` the input (a value that needs
# stripping is not a sealed date).
_ISO_DATE_RE = re.compile(r"\A[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")


def _parsed_date(value: object) -> "_dt.date | None":
    """`value` as a real calendar date, or None when it is not a strict
    `str` in exactly `YYYY-MM-DD` ASCII form naming a real day."""
    if not _is_strict_str(value) or not _ISO_DATE_RE.match(value):
        return None
    try:
        return _dt.date.fromisoformat(value)     # load-bearing, see above
    except ValueError:
        return None


# Frozen F10 vocabulary (IR-12/18): a concrete category from the SAME
# single-sourced `s0_context.F10_CATEGORIES` tuple, or the literal "none"
# (zero-category day), or None (NA on a multi-category conflict — see
# `s0_context.EventCalendar.encode_f10`). "none_or_na" or any other spelling
# is NOT part of this vocabulary and is rejected below.
#
# blind-audit LOW-6: this used to be a DEAD import-time snapshot taken from
# `DEFAULT_SOURCE_CONTEXT` and shadowed by the live `source.event_flag_values`
# everywhere it mattered. It is now the SINGLE source: `SourceContext`'s field
# default IS this constant, and the field is pinned back to it on every
# validation.
_EVENT_FLAG_VALUES = frozenset(s0_context.F10_CATEGORIES) | {"none"}


# ===========================================================================
# SOURCE CONTEXT — what admission rebuilds expected content FROM
# ===========================================================================

class SourceContextError(ValueError):
    """The SOURCE CONTEXT itself is invalid.

    Distinct from an artifact problem on purpose: an artifact defect is a
    refusal to seal THAT artifact, while this says the independent anchor a
    recomputation would be measured against cannot be trusted, so NOTHING in
    the bundle may be admitted.
    """


_VOCABULARY_CONTAINERS = (frozenset, set, tuple, list)


def _validated_vocabulary(field: str, value: object) -> "frozenset[str] | None":
    """A ruling-slot VOCABULARY, normalised to `frozenset[str]`.

    Blind-audit A10: a BARE STR is refused. `value in "S_A"` is SUBSTRING
    matching, so a vocabulary supplied as the string "S_A" would silently
    admit "S", "_A", "S_", and "" — every substring of the intended single
    token. Membership must be set-of-str semantics everywhere, which is
    enforced HERE (at the type level) rather than at each call site.
    """
    if value is None:
        return None
    if isinstance(value, (str, bytes, bytearray)):
        raise SourceContextError(
            f"SourceContext.{field} = {_safe_repr(value)} is a bare "
            "str/bytes — a ruling vocabulary must be a set/frozenset/tuple/"
            "list of non-empty str. A bare str degrades the membership test "
            "into SUBSTRING matching (a ruled 'S_A' would admit 'S', '_A' "
            "and ''), which is not a vocabulary")
    if not isinstance(value, _VOCABULARY_CONTAINERS):
        raise SourceContextError(
            f"SourceContext.{field} = {_safe_repr(value)} must be None or a "
            f"set/frozenset/tuple/list of non-empty str, got "
            f"{type(value).__name__}")
    items = list(value)
    if not items:
        raise SourceContextError(
            f"SourceContext.{field} is an EMPTY vocabulary — an axis is "
            "either UNRULED (None, so only an UNRESOLVED marker is "
            "admissible) or ruled to at least one token; an empty set would "
            "silently refuse every value including the marker")
    bad = [v for v in items if not _is_strict_str(v) or not v]
    if bad:
        raise SourceContextError(
            f"SourceContext.{field} has non-str or empty member(s) "
            f"{sorted(_safe_repr(v) for v in bad)} — every token must be a "
            "non-empty strict str")
    # identity-preserving when it is ALREADY the right shape, so a pinned
    # slot keeps pointing at its owning module's object rather than at a
    # copy that merely compares equal
    return value if type(value) is frozenset else frozenset(items)


def _validated_ruling(field: str, value: object) -> "str | None":
    """A single-token ruling slot (`k_policy` / `crn_scope`)."""
    if value is None:
        return None
    if not _is_strict_str(value) or not value:
        raise SourceContextError(
            f"SourceContext.{field} = {_safe_repr(value)} must be None "
            "(UNRULED) or a non-empty strict str naming the ruled value")
    if _is_unresolved(value):
        raise SourceContextError(
            f"SourceContext.{field} = {_safe_repr(value)} is an UNRESOLVED "
            "marker — 'the ruling is that it is unresolved' is not a ruling. "
            "Leave the slot None; that is what UNRULED means, and it is what "
            "makes the marker the only admissible artifact value")
    return value


def _validated_str_tuple(field: str, value: object) -> tuple:
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(
            value, (tuple, list)):
        raise SourceContextError(
            f"SourceContext.{field} must be a non-empty tuple of non-empty "
            f"str, got {_safe_repr(value)}")
    items = tuple(value)
    if not items:
        raise SourceContextError(f"SourceContext.{field} must not be empty")
    bad = [v for v in items if not _is_strict_str(v) or not v]
    if bad:
        raise SourceContextError(
            f"SourceContext.{field} has non-str or empty member(s) "
            f"{sorted(_safe_repr(v) for v in bad)}")
    if len(set(items)) != len(items):
        raise SourceContextError(
            f"SourceContext.{field} has duplicate member(s): "
            f"{_safe_repr(items)}")
    return items


def _validated_int_tuple(field: str, value: object, lo: int, hi: int) -> tuple:
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(
            value, (tuple, list)):
        raise SourceContextError(
            f"SourceContext.{field} must be a non-empty tuple of strict int, "
            f"got {_safe_repr(value)}")
    items = tuple(value)
    if not items:
        raise SourceContextError(f"SourceContext.{field} must not be empty")
    bad = [v for v in items
           if not _is_strict_int(v) or not lo <= v <= hi]
    if bad:
        raise SourceContextError(
            f"SourceContext.{field} has member(s) that are not strict int in "
            f"[{lo}, {hi}]: {sorted(_safe_repr(v) for v in bad)} (bool is "
            "not int here)")
    if len(set(items)) != len(items):
        raise SourceContextError(
            f"SourceContext.{field} has duplicate member(s): "
            f"{_safe_repr(items)}")
    return items


def _validated_epochs(value: object) -> tuple:
    """`stability.EPOCHS`-shaped: `(label, lo_year, hi_year)` triples,
    inclusive on both ends, non-overlapping, unique labels."""
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(
            value, (tuple, list)):
        raise SourceContextError(
            f"SourceContext.epochs must be a non-empty tuple of "
            f"(label, lo, hi) triples, got {_safe_repr(value)}")
    rows = tuple(tuple(r) if isinstance(r, (tuple, list)) else r
                 for r in value)
    if not rows:
        raise SourceContextError("SourceContext.epochs must not be empty")
    for row in rows:
        if (not isinstance(row, tuple) or len(row) != 3
                or not _is_strict_str(row[0]) or not row[0]
                or not _is_strict_int(row[1]) or not _is_strict_int(row[2])
                or row[1] > row[2]):
            raise SourceContextError(
                f"SourceContext.epochs row {_safe_repr(row)} is malformed — "
                "every row must be (non-empty str label, strict int lo, "
                "strict int hi) with lo <= hi")
    labels = [r[0] for r in rows]
    if len(set(labels)) != len(labels):
        raise SourceContextError(
            f"SourceContext.epochs has duplicate label(s): {sorted(labels)}")
    ordered = sorted(rows, key=lambda r: (r[1], r[2]))
    for a, b in zip(ordered, ordered[1:]):
        if b[1] <= a[2]:
            raise SourceContextError(
                f"SourceContext.epochs ranges OVERLAP: {_safe_repr(a)} and "
                f"{_safe_repr(b)} — a year would fall in two epochs and the "
                "first match would silently win")
    return rows


# Slots that are FROZEN CONSTANTS, not configuration: each must equal its
# owning module's current value. This is what makes an `object.__setattr__`
# poisoning of the frozen singleton (blind-audit A8) a refusal rather than a
# silent re-anchoring of every recomputation in the module. Read through a
# callable so the comparison uses the module's value AT VALIDATION TIME.
_PINNED_SLOTS: dict = {
    "engines": lambda: s0_study.ENGINES,
    "scenarios": lambda: SCENARIOS,
    "seeds": lambda: tuple(contracts.RESEARCH_BOOTSTRAP_SEEDS),
    "epochs": lambda: tuple(s0_stability.EPOCHS),
    "outside_epochs": lambda: s0_stability.OUTSIDE_EPOCHS,
    "micro_era_boundary": lambda: s0_context.MICRO_ERA_BOUNDARY,
    "era_proxy": lambda: s0_dataset.ERA_PROXY,
    "era_actual": lambda: s0_dataset.ERA_ACTUAL,
    "event_flag_values": lambda: _EVENT_FLAG_VALUES,
    "stats_stream_tag": lambda: s0_stats.STATS_STREAM_TAG,
    "grid_stream_tag": lambda: s0_gridmix.GRID_STREAM_TAG,
    "q_grid_millis": lambda: s0_gridmix.Q_GRID_MILLIS,
    "r_grid_millis": lambda: s0_gridmix.R_GRID_MILLIS,
}


def _validate_source_context(ctx: "SourceContext") -> dict:
    """Validate EVERY slot and return the NORMALISED field values.

    Called from `__post_init__` (construction) AND again from
    `_resolve_source` on EVERY admission call, because `@dataclass(frozen=…)`
    only blocks ordinary attribute assignment: `object.__setattr__` writes
    straight past it (blind-audit A8), and the module-global singleton is a
    standing target.
    """
    out: dict = {}

    # --- the reported theta axis: a SUBSET of the frozen pair -----------
    thetas = ctx.thetas
    if type(thetas) is not tuple:
        raise SourceContextError(
            f"SourceContext.thetas must be a non-empty tuple of strict "
            f"float, got {_safe_repr(thetas)} "
            f"({type(thetas).__name__}) — a non-tuple container is refused: "
            "a set has no defined order and a list is not the frozen axis's "
            "shape")
    if not thetas:
        raise SourceContextError(
            "SourceContext.thetas is EMPTY — with no theta axis every "
            "tp_fp_class check passes VACUOUSLY (an empty dict equals the "
            "empty expected key set), which silently disables the entire "
            "DAY_STRATA classification family (blind-audit A11)")
    bad_thetas = [t for t in thetas if not _is_strict_float(t)]
    if bad_thetas:
        raise SourceContextError(
            f"SourceContext.thetas has non-strict-float member(s) "
            f"{sorted(_safe_repr(t) for t in bad_thetas)} — STRICT float type "
            "only: bool/int/str are refused and never coerced (True and 1 are "
            "not 1.0 here)")
    if len(set(thetas)) != len(thetas):
        raise SourceContextError(
            f"SourceContext.thetas has duplicate member(s): "
            f"{_safe_repr(thetas)} — the reported theta axis is a "
            "duplicate-free subset")
    # M6.1.4 CLOSEOUT: MEMBERSHIP against the ONE frozen source. Read live
    # from `study.FROZEN_THETAS` (never a second (0.5, 0.3) literal anywhere
    # in this module — matrix CR-11's sibling defect). This is a membership
    # bind, NOT a configuration or sweep surface: `thetas` selects which
    # non-empty subset of the frozen pair THIS handoff round reports, in any
    # order, and can never introduce a theta the frozen text does not have.
    frozen = tuple(s0_study.FROZEN_THETAS)
    non_members = [t for t in thetas if t not in frozen]
    if non_members:
        raise SourceContextError(
            f"SourceContext.thetas has member(s) "
            f"{sorted(_safe_repr(t) for t in non_members)} that are NOT in "
            f"the frozen theta set study.FROZEN_THETAS {frozen} — theta is a "
            "FROZEN AXIS (S0 §7 L133), not a configuration or sweep "
            "parameter: `thetas` may only select a non-empty, duplicate-free "
            "SUBSET of that pair, in any order. Membership is EXACT float "
            "equality with NO tolerance, so a near-member such as 0.5 + 1e-9 "
            "is refused too")
    out["thetas"] = thetas

    # --- pinned frozen constants ---------------------------------------
    out["engines"] = _validated_str_tuple("engines", ctx.engines)
    out["scenarios"] = _validated_str_tuple("scenarios", ctx.scenarios)
    out["seeds"] = _validated_int_tuple("seeds", ctx.seeds, 0, 2 ** 31)
    out["epochs"] = _validated_epochs(ctx.epochs)
    out["q_grid_millis"] = _validated_int_tuple(
        "q_grid_millis", ctx.q_grid_millis, 1, 1000)
    out["r_grid_millis"] = _validated_int_tuple(
        "r_grid_millis", ctx.r_grid_millis, 1, 1000)
    for field in ("outside_epochs", "micro_era_boundary", "era_proxy",
                  "era_actual"):
        value = getattr(ctx, field)
        if not _is_strict_str(value) or not value:
            raise SourceContextError(
                f"SourceContext.{field} must be a non-empty strict str, got "
                f"{_safe_repr(value)}")
        out[field] = value
    if _parsed_date(ctx.micro_era_boundary) is None:
        raise SourceContextError(
            f"SourceContext.micro_era_boundary "
            f"{_safe_repr(ctx.micro_era_boundary)} is not an ISO YYYY-MM-DD "
            "date — the frozen §6 era boundary is compared against ISO date "
            "strings and a malformed boundary silently mis-eras every day")
    if ctx.era_proxy == ctx.era_actual:
        raise SourceContextError(
            "SourceContext.era_proxy and .era_actual are the SAME label — "
            "the frozen §6 axis has two distinct eras and a collapsed axis "
            "makes every era check vacuous")
    epoch_labels = {r[0] for r in out["epochs"]}
    if out["outside_epochs"] in epoch_labels:
        raise SourceContextError(
            f"SourceContext.outside_epochs "
            f"{_safe_repr(out['outside_epochs'])} collides with a real epoch "
            "label — the out-of-range bucket must be distinguishable")
    for field in ("stats_stream_tag", "grid_stream_tag"):
        value = getattr(ctx, field)
        if not _is_strict_int(value):
            raise SourceContextError(
                f"SourceContext.{field} must be a strict int, got "
                f"{_safe_repr(value)}")
        out[field] = value
    if out["stats_stream_tag"] == out["grid_stream_tag"]:
        raise SourceContextError(
            "SourceContext.stats_stream_tag == .grid_stream_tag — the two "
            "tags exist precisely so a bootstrap sub-stream and a grid "
            "sub-stream can never coincide inside one master seed")
    out["event_flag_values"] = _validated_vocabulary(
        "event_flag_values", ctx.event_flag_values)

    for field, owner in _PINNED_SLOTS.items():
        expected = owner()
        if out.get(field, getattr(ctx, field)) != expected:
            raise SourceContextError(
                f"SourceContext.{field} = "
                f"{_safe_repr(out.get(field, getattr(ctx, field)))} != its "
                f"owning module's value {_safe_repr(expected)}. This slot is "
                "a FROZEN CONSTANT, not configuration: re-anchoring it would "
                "silently move what every recomputation is measured against")

    # --- dataset facts ---------------------------------------------------
    universe = ctx.day_universe
    if universe is None:
        out["day_universe"] = None
    else:
        if isinstance(universe, (str, bytes, bytearray)) or not isinstance(
                universe, _VOCABULARY_CONTAINERS):
            raise SourceContextError(
                "SourceContext.day_universe must be None or a "
                "set/frozenset/tuple/list of ISO YYYY-MM-DD date str, got "
                f"{_safe_repr(universe)}")
        dates = list(universe)
        bad_dates = [d for d in dates if _parsed_date(d) is None]
        if bad_dates:
            raise SourceContextError(
                "SourceContext.day_universe has non-ISO-date member(s) "
                f"{sorted(_safe_repr(d) for d in bad_dates)[:5]}")
        out["day_universe"] = frozenset(dates)

    # --- ruling slots ----------------------------------------------------
    out["event_stratum_vocabulary"] = _validated_vocabulary(
        "event_stratum_vocabulary", ctx.event_stratum_vocabulary)
    out["vol_status_vocabulary"] = _validated_vocabulary(
        "vol_status_vocabulary", ctx.vol_status_vocabulary)
    out["k_policy"] = _validated_ruling("k_policy", ctx.k_policy)
    out["crn_scope"] = _validated_ruling("crn_scope", ctx.crn_scope)

    # --- strict booleans -------------------------------------------------
    for field in ("replay_closure_ruled", "require_complete_grid_matrix",
                  "rulings_are_test_only"):
        value = getattr(ctx, field)
        if not _is_strict_bool(value):
            raise SourceContextError(
                f"SourceContext.{field} must be a STRICT bool, got "
                f"{_safe_repr(value)} — a truthy non-bool ('no', 0.0, []) "
                "would silently flip a gate")
        out[field] = value
    return out


@dataclass(frozen=True)
class SourceContext:
    """The INDEPENDENT sources a semantic checker rebuilds expected artifact
    content from. Passing this explicitly is the whole point of the M6.1.4
    RC-2 fix: without it a checker can only ever confirm that an artifact
    agrees with itself.

    Three kinds of field:

    A. FROZEN CONSTANTS — read from their single-sourced owning module. These
       are genuinely independent of any artifact (matrix VF-12 is the one
       pre-existing example of this anchor class).
    B. DATASET FACTS — optional (`None` = "not available to this admission
       call"). Where a fact IS supplied it becomes a hard expectation; where
       it is absent the checker says so rather than pretending.
    C. RULING SLOTS — `None` by default. A `None` slot means: THIS context
       carries no ruling on that axis, so the ONLY admissible value there is
       one of this module's UNRESOLVED markers, AND that marker blocks
       sealing. Supplying a ruling here is the ONLY way an artifact may carry
       a concrete value on such an axis; a value the artifact simply asserts
       is never self-authorising. Since 2026-08-10 the rulings EXIST — but
       they still have to be HANDED to this module (`source_context_for_
       methods`), because "which context sealed this artifact" must stay
       visible at the call site rather than being adopted behind its back.

    `SourceContext()` with no arguments is the LEGACY / unruled context:
    every frozen constant bound, no dataset facts, no ruling on any axis.
    It is what a caller that passes no `methods` and no `source` gets, and it
    is bit-identical to the pre-ruling production default.
    """

    # --- A. frozen constants -------------------------------------------
    thetas: tuple[float, ...] = FROZEN_THETAS
    engines: tuple[str, ...] = ENGINES
    scenarios: tuple[str, ...] = SCENARIOS
    seeds: tuple[int, ...] = FROZEN_SEEDS
    # matrix CR-4: `stability.EPOCHS` is THE authoritative epoch boundary
    # source for this module. `dataset.STABILITY_EPOCHS` uses a half-open
    # string-range convention and must never be mixed in here.
    epochs: tuple[tuple[str, int, int], ...] = tuple(s0_stability.EPOCHS)
    outside_epochs: str = s0_stability.OUTSIDE_EPOCHS
    micro_era_boundary: str = s0_context.MICRO_ERA_BOUNDARY
    era_proxy: str = s0_dataset.ERA_PROXY
    era_actual: str = s0_dataset.ERA_ACTUAL
    # frozen F10 vocabulary (IR-12/18) from context.F10_CATEGORIES plus the
    # literal "none" (zero-category day); None is the NA state and is handled
    # separately (never a member of this set).
    event_flag_values: frozenset[str] = _EVENT_FLAG_VALUES
    stats_stream_tag: int = s0_stats.STATS_STREAM_TAG
    grid_stream_tag: int = s0_gridmix.GRID_STREAM_TAG
    q_grid_millis: tuple[int, ...] = s0_gridmix.Q_GRID_MILLIS
    r_grid_millis: tuple[int, ...] = s0_gridmix.R_GRID_MILLIS

    # --- B. dataset facts (None = not available to this call) ----------
    #   day_universe: the exact date set DAY_STRATA must carry.
    day_universe: frozenset[str] | None = None

    # --- C. ruling slots (None = not ruled ON THIS CONTEXT; marker only) --
    #   DR-6 (was DR-M6-F) — event -> Appendix-A stratum mapping. RULED;
    #   `source_context_for_methods` fills this from dataset.EVENT_STRATA.
    event_stratum_vocabulary: frozenset[str] | None = None
    #   DR-2 (was DR-M6-B-v2) — per-day vol status. RULED; filled from
    #   dataset.VOL_ALL_LABELS (terciles + the ruled vol_na fourth stratum).
    vol_status_vocabulary: frozenset[str] | None = None
    #   DR-5 (was DR-M6-E) — grid K-repeat policy. RULED; filled by
    #   `ruled_k_policy` from methods.grid_policy's own fields.
    k_policy: str | None = None
    #   DR-4.7 — S0-side engine x scenario CRN scope. RULED; filled from
    #   methods.bootstrap_method.crn_scope.
    crn_scope: str | None = None
    #   MULTI-STRATUM REPLAY CLOSURE — NOT a DR slot and NOT set by
    #   `source_context_for_methods`: the remaining blocker is MC wiring (the
    #   DR-5 repeat set is absent from the frozen cell schema and the §5
    #   convergence verdict is MC-side), so closure is a claim only an MC-side
    #   caller could ever make. While this is False,
    #   PARTIAL_single_stratum_only is the only TRUTHFUL status and a CLOSED
    #   claim is refused as a LIE (and PARTIAL is refused for SEALING, because
    #   it is not closed — fail-closed both ways).
    replay_closure_ruled: bool = False
    #   TEST_ONLY provenance of the rulings above (mirrors
    #   `ResolvedS0Methods.test_only`). True keeps every artifact validated
    #   against this context NOT sealable, however well-formed it is — the
    #   same fail-closed rule `dataset.event_stratum_of` and `study.py`'s
    #   estimator gate apply to a TEST_ONLY value on a production path.
    rulings_are_test_only: bool = False

    # --- bundle expectations -------------------------------------------
    #   Off by default: no production caller builds GRID_SAMPLES at all
    #   (matrix L145 NOT PRODUCED), so there is no production bundle whose
    #   completeness could be contracted. A caller that DOES produce the full
    #   theta x engine x scenario set opts in here.
    require_complete_grid_matrix: bool = False

    def __post_init__(self) -> None:
        # Validate EVERY slot at construction and write back the NORMALISED
        # values (vocabularies become frozensets, sequences become tuples),
        # so no downstream membership test can be handed a shape whose `in`
        # means something other than set membership.
        for field, value in _validate_source_context(self).items():
            object.__setattr__(self, field, value)

    def validate(self) -> None:
        """Re-check this context's CURRENT field values; raises
        `SourceContextError`. `@dataclass(frozen=True)` only blocks ordinary
        assignment — `object.__setattr__` writes straight past it — so the
        construction-time check is not a standing guarantee and admission
        re-runs this on every call."""
        _validate_source_context(self)


DEFAULT_SOURCE_CONTEXT = SourceContext()


def _resolve_source(source: "SourceContext | None") -> SourceContext:
    """Resolve, TYPE-PIN and RE-VALIDATE the source context.

    Closes blind-audit MED-1:

    * A8 — `object.__setattr__` poisoning of the frozen module-global
      singleton: the type pin passes, so the FIELD VALUES are re-validated on
      every call and a poisoned slot is refused.
    * A9 — `DEFAULT_SOURCE_CONTEXT` replaced by a non-SourceContext duck
      whose property raises: the pin is `type(ctx) is SourceContext`, checked
      BEFORE any attribute of `ctx` is read, so a hostile property is never
      reached. A subclass is refused too — overriding one property is enough
      to re-anchor everything.
    * A10/A11 — a bare-str vocabulary and an empty theta axis are refused by
      `_validate_source_context`.

    HONEST BOUNDARY, stated rather than implied: this catches a singleton
    mutated to GARBAGE. A singleton mutated to a PLAUSIBLE ruling (e.g.
    `k_policy` set to a well-formed string) is, in-process, indistinguishable
    from a caller who legitimately passed that ruling — validation can check
    well-formedness and pinning, never intent. The config gate carries the
    same documented boundary; an attacker with in-process write access to
    module globals has already won, and the defence there is the frozen-file
    hash gate, not this function.
    """
    ctx = DEFAULT_SOURCE_CONTEXT if source is None else source
    if type(ctx) is not SourceContext:
        raise SourceContextError(
            "source context must be EXACTLY a handoff.SourceContext (the "
            "INDEPENDENT source facts expected content is rebuilt from), got "
            f"{type(ctx).__name__} — an ad-hoc dict, a duck type or even a "
            "SUBCLASS is refused: a context whose attribute reads are not "
            "pinned cannot anchor a recomputation, and one property override "
            "would silently re-anchor every check in this module")
    ctx.validate()
    return ctx


# ===========================================================================
# RULED METHODS -> handoff axes (Aaron's 2026-08-10 rulings)
# ===========================================================================
# The ONE adapter between `contracts.ResolvedS0Methods` (the single ruled
# source) and this module's `SourceContext` ruling slots. Three disciplines
# hold here and each one is load-bearing:
#
# 1. NO RULED LITERAL IS RESTATED. Every value below is either read straight
#    off the `methods` object or read from the owning module's own constant
#    (`dataset.EVENT_STRATA`, `dataset.VOL_ALL_LABELS`,
#    `stats.BOOTSTRAP_CRN_SCOPE`, `gridmix.GRID_CONVERGENCE_RULE`), which are
#    themselves that module's disclosed reads of the ruled source. A ruled
#    string typed into this file would be a second source of truth.
# 2. CROSS-MODULE PINNING, not blind pass-through. Where another module
#    already implements a ruled value as a DISPATCH KEY, the value carried by
#    `methods` is checked to BE that key. A `methods` object that says one
#    thing while the module that executes it implements another is a defect,
#    and disclosing the methods' version would misdescribe what actually ran.
# 3. FAIL CLOSED. Anything unrecognised raises `RulingError` — never a silent
#    fallback to the UNRESOLVED marker, which would turn a real defect into
#    a disclosure that looks routine.


class RulingError(ValueError):
    """A `methods` object cannot be read as a ruling this module may emit.

    Distinct from `SourceContextError` (the independent ANCHOR is untrusted)
    and from an artifact problem (this artifact is not sealable): it says the
    RULING INPUT is unusable, so no ruled value may be emitted at all.
    """


def _validated_methods(methods: object) -> "contracts.ResolvedS0Methods":
    """`methods`, type-pinned and proven FULLY RESOLVED and STRUCTURALLY
    VALID, or `RulingError`.

    The pending/structural rules are NOT restated here: they are
    `ResolvedS0Methods.pending_fields()` and `.structural_problems()`, the
    same two gates `derive_study_config` uses. The type pin is
    `type(...) is ResolvedS0Methods` for the same reason `_resolve_source`
    pins its context: one overridden property on a subclass or duck would
    silently re-anchor every ruled value this module emits.
    """
    if type(methods) is not contracts.ResolvedS0Methods:
        raise RulingError(
            "methods must be EXACTLY a contracts.ResolvedS0Methods (the "
            "single ruled source; `contracts.aaron_ruled_methods()` returns "
            f"one), got {type(methods).__name__} — a duck type or a SUBCLASS "
            "is refused: one property override would re-anchor every ruled "
            "value emitted from it")
    pending = methods.pending_fields()
    if pending:
        raise RulingError(
            f"methods is only PARTIALLY resolved — pending: {list(pending)}. "
            "A partially-resolved method set may not resolve any handoff "
            "axis: leave `methods=None` and keep the UNRESOLVED markers, "
            "which is the truthful disclosure for that state")
    problems = methods.structural_problems()
    if problems:
        raise RulingError(
            "methods is STRUCTURALLY invalid and may not resolve any handoff "
            f"axis: {sorted(problems)}")
    return methods


def ruled_event_stratum_vocabulary(methods: object) -> frozenset:
    """The DR-6 event-stratum vocabulary this `methods` licenses.

    The admissibility gate for the mapping string is NOT re-implemented here:
    `dataset.event_stratum_of` OWNS it (the ruled mapping, or the TEST_ONLY
    synthetic mapping only under `test_only`) and raises for anything else.
    Calling it with the NA flag runs exactly that gate — a probe, not a second
    copy of the rule — and the vocabulary itself is `dataset.EVENT_STRATA`.
    """
    m = _validated_methods(methods)
    try:
        s0_dataset.event_stratum_of(None, m.event_na_mapping, m.test_only)
    except ValueError as exc:
        raise RulingError(
            f"methods.event_na_mapping {m.event_na_mapping!r} is not a "
            "mapping dataset.event_stratum_of accepts for this caller "
            f"(test_only={m.test_only!r}): {_safe_reason(exc)}") from exc
    return frozenset(s0_dataset.EVENT_STRATA)


def ruled_vol_status_vocabulary(methods: object) -> frozenset:
    """The DR-2 per-day vol-status vocabulary this `methods` licenses.

    This module never COMPUTES vol20 — the per-day labels keep coming from
    the caller's day rows. What the ruling supplies is which labels are
    admissible: `dataset.VOL_ALL_LABELS` (the three terciles plus the ruled
    `vol_na` fourth stratum). Both ruled sub-decisions that create that
    vocabulary are pinned against `dataset`'s own reads of the ruled source.
    """
    m = _validated_methods(methods)
    vol = m.volatility_regime
    if vol.na_rule != s0_dataset.RULED_VOL_NA_RULE:
        raise RulingError(
            f"methods.volatility_regime.na_rule {vol.na_rule!r} is not the "
            f"rule dataset.py implements ({s0_dataset.RULED_VOL_NA_RULE!r}) "
            "— the fourth-stratum vocabulary this function would hand out is "
            "produced by THAT rule, so emitting it for another one would "
            "misdescribe what produced the labels")
    if vol.mapping_scope != s0_dataset.RULED_VOL_MAPPING_SCOPE:
        raise RulingError(
            f"methods.volatility_regime.mapping_scope {vol.mapping_scope!r} "
            "is not the scope dataset.py implements "
            f"({s0_dataset.RULED_VOL_MAPPING_SCOPE!r}) — the handoff's "
            "per-day vol_status is the Appendix-A half of a SHARED mapping; "
            "an unshared scope would make this field a different axis")
    return frozenset(s0_dataset.VOL_ALL_LABELS)


#: The `k_policy` encoding: every DR-5 sub-decision that a replayer needs, in
#: one byte-stable token, each value read off `methods.grid_policy` itself.
#: The field ORDER here is part of the token and must not be reshuffled (it
#: is compared for exact equality on both sides of the seal).
_K_POLICY_FIELDS = ("k_per_seed", "k_start_index", "stream_includes_theta",
                    "max_doublings", "convergence_rule")


def ruled_k_policy(methods: object) -> str:
    """The DR-5 replay `k_policy` token, built from `methods.grid_policy`.

    Structural, not prose: `"k_per_seed=200;k_start_index=0;..."`, so the
    checker can compare it for exact equality and a reader can see every
    sub-decision. The values are `grid_policy`'s own; only the FORMAT belongs
    to this module.
    """
    m = _validated_methods(methods)
    g = m.grid_policy
    if g.convergence_rule != s0_gridmix.GRID_CONVERGENCE_RULE:
        raise RulingError(
            f"methods.grid_policy.convergence_rule {g.convergence_rule!r} is "
            "not the dispatch key gridmix.py implements "
            f"({s0_gridmix.GRID_CONVERGENCE_RULE!r}) — the k_policy this "
            "handoff discloses must name the convergence rule that actually "
            "ran, not a different one")
    return ";".join(f"{name}={getattr(g, name)!r}"
                    for name in _K_POLICY_FIELDS)


def ruled_crn_scope(methods: object) -> str:
    """The DR-4.7 S0-side CRN scope, from `methods.bootstrap_method`.

    Pinned against `stats.BOOTSTRAP_CRN_SCOPE`, the scope the bootstrap layer
    actually implements (`stats._require_crn_scope` refuses any other), so
    the seal cannot disclose a scope no stream was ever keyed by. The MC
    cross-platform CRN is a separate, already-frozen decision
    (MC_METHOD_SPEC §5) and is not this axis.
    """
    m = _validated_methods(methods)
    scope = m.bootstrap_method.crn_scope
    if scope != s0_stats.BOOTSTRAP_CRN_SCOPE:
        raise RulingError(
            f"methods.bootstrap_method.crn_scope {scope!r} is not the scope "
            f"stats.py implements ({s0_stats.BOOTSTRAP_CRN_SCOPE!r}) — "
            "stats._require_crn_scope refuses any other value, so this "
            "handoff would be disclosing a scope no resample stream was "
            "keyed by")
    return scope


#: The slots `source_context_for_methods` DERIVES. A caller may not override
#: one: laundering a different vocabulary through the methods seam would make
#: `methods` look like the authority for a value it did not carry.
_METHODS_DERIVED_SLOTS = ("event_stratum_vocabulary", "vol_status_vocabulary",
                          "k_policy", "crn_scope", "rulings_are_test_only")


def source_context_for_methods(methods: object, **overrides) -> SourceContext:
    """The `SourceContext` a FULLY-RULED `methods` licenses.

    Fills exactly the axes whose ruling now exists, and NOTHING ELSE:

    * `event_stratum_vocabulary` / `vol_status_vocabulary` / `k_policy` /
      `crn_scope` — the four ruled axes;
    * `rulings_are_test_only` — carried straight from `methods.test_only`, so
      a TEST_ONLY method set can be threaded through every code path a real
      one can, and still never produces a sealable artifact.

    `replay_closure_ruled` is deliberately NOT set: multi-stratum replay
    closure is not a method ruling. The remaining blocker is MC wiring (the
    DR-5 repeat set is not in the frozen cell schema and the §5 convergence
    verdict is MC-side), so only an MC-side caller could ever make that claim
    — and it must do so explicitly.

    Other slots (`thetas`, `day_universe`, `require_complete_grid_matrix`, …)
    may be passed through `**overrides`; the five derived slots may not.
    """
    m = _validated_methods(methods)
    clash = sorted(set(overrides) & set(_METHODS_DERIVED_SLOTS))
    if clash:
        raise RulingError(
            f"{clash} may not be overridden on a methods-derived source "
            "context — those slots ARE the ruling, and overriding one would "
            "make `methods` look like the authority for a value it does not "
            "carry. Build a SourceContext directly if that is what you mean")
    kwargs: dict = {
        "event_stratum_vocabulary": ruled_event_stratum_vocabulary(m),
        "vol_status_vocabulary": ruled_vol_status_vocabulary(m),
        "k_policy": ruled_k_policy(m),
        "crn_scope": ruled_crn_scope(m),
        "rulings_are_test_only": bool(m.test_only),
    }
    kwargs.update(overrides)
    return SourceContext(**kwargs)


# ===========================================================================
# problem records
# ===========================================================================

class _Problem(NamedTuple):
    """One refusal reason.

    `code` classifies the reason so the BUILDERS can tell "you constructed
    this wrong" (raise) apart from "this is correctly built and correctly not
    sealable yet" (return the artifact, flag False). `text` is the
    human-readable string that reaches `formal_seal_admission`'s output.
    """
    code: str
    text: str


# codes a BUILDER tolerates in its own output: these describe an artifact
# that is correct BUT not sealable. That is what every builder emits when it
# was handed no `methods` (all four axes marked), and what `build_grid_
# samples` still emits WITH `methods` (PENDING: the MC-side replay). A
# builder that emits none of them produces a sealable artifact — no code path
# forces the verdict either way.
_BUILDER_TOLERATED_CODES = frozenset({
    "EMPTY",              # a zero-day / zero-cell artifact is never sealable
    "UNRESOLVED_MARKER",  # a disclosed DR-M6-* marker
    "PENDING",            # replay_status PARTIAL while MC wiring is open
    "TEST_ONLY",          # correctly built from TEST_ONLY synthetic rulings
})
# codes that are ADMISSION-level bundle contracts, not construction
# invariants: `gridmix.build_grid` legitimately accepts q_grid/r_grid axis
# overrides for tests and sensitivity runs, so a grid_output need not carry
# the frozen 63-point lattice at BUILD time; it must at SEAL time.
_GRID_BUILDER_TOLERATED_CODES = _BUILDER_TOLERATED_CODES | frozenset({
    "LATTICE", "DEPENDENCY", "CROSS"})


def _p(code: str, text: str) -> _Problem:
    return _Problem(code, text)


def _source_refusal(type_name: str, exc: BaseException) -> str:
    """The refusal a checker returns when the SOURCE CONTEXT — not the
    artifact — is untrustworthy. Fail closed: with no trustworthy anchor
    there is nothing to recompute against, so nothing is sealable."""
    return (f"{type_name}: source context invalid — fail closed: "
            f"{_safe_reason(exc)}")


def _guarded(fn, type_name: str, artifact: object,
             source: SourceContext) -> list[_Problem]:
    """Run a checker so it can NEVER crash on arbitrary JSON-like input
    (item 9). A checker that raises is itself a refusal — fail closed: a
    verification that could not complete never yields admission. The
    exception TYPE is named but its `repr` is not rendered (a hostile
    object's `__repr__` can raise too)."""
    try:
        return list(fn(artifact, source))
    except Exception as exc:                # noqa: BLE001 - deliberate net
        return [_p("INTERNAL",
                   f"{type_name}: the semantic checker raised "
                   f"{type(exc).__name__} while reading this artifact — "
                   "refused (a check that cannot complete is never a pass)")]


# ===========================================================================
# shared vocabulary constants
# ===========================================================================

_TP_FP_VALUES = frozenset({"TP", "FP", "non_tradeable"})
_NON_TRADEABLE = "non_tradeable"

# matrix CR-11 CLOSED: the theta key format is `study.theta_key`, imported,
# never a local `_theta_key` duplicate. A `:g` drift between the two copies
# was a live defect class (M6.1.3 evidence matrix D6a).
_FROZEN_THETA_KEYS = frozenset(s0_study.theta_key(t) for t in FROZEN_THETAS)


def _epoch_for_year(year: int, source: SourceContext) -> str:
    """Epoch label for `year`, from the SINGLE authoritative boundary source
    `stability.EPOCHS` (carried on the source context). Matrix CR-4: this
    module must never grow a second interval convention."""
    for label, lo, hi in source.epochs:
        if lo <= year <= hi:
            return label
    return source.outside_epochs


def _epoch_labels(source: SourceContext) -> frozenset[str]:
    return frozenset([label for label, _lo, _hi in source.epochs]
                     + [source.outside_epochs])


def _era_for_date(date: str, source: SourceContext) -> str:
    """The frozen §6 two-era axis as a pure function of the DATE (ISO strings
    sort chronologically), from `context.MICRO_ERA_BOUNDARY` and
    `dataset.ERA_PROXY`/`ERA_ACTUAL` — never from the artifact's own claim."""
    return (source.era_proxy if date < source.micro_era_boundary
            else source.era_actual)


def _grid_cell_key(q_mil: int, r_mil: int) -> str:
    """The grid cell key format `gridmix._build_grid_unchecked` writes
    (`f"q{q_mil / 1000:.2f}_r{r_mil / 1000:.2f}"`). Restated here — with its
    citation — because the gridmix side is private; this is the ONE copy, and
    it is used both to rebuild the expected 63-key lattice AND to check that
    each cell's own key agrees with its own q_mil/r_mil fields."""
    return f"q{q_mil / 1000:.2f}_r{r_mil / 1000:.2f}"


def _schema_check(label: str, mapping: object,
                  required_keys: frozenset[str]) -> list[_Problem]:
    """Full schema fidelity: `mapping`'s key SET must be EXACTLY
    `required_keys` — missing and extra fields are DISTINCT, both-named
    problems, never folded into one generic "shape is wrong" message (same
    discipline `_check_record_matrix_shape` already applies to the engine ×
    scenario matrix)."""
    if not isinstance(mapping, Mapping):
        return [_p("SCHEMA", f"{label}: expected a mapping, got "
                             f"{type(mapping).__name__}")]
    try:
        actual = set(mapping)
    except Exception:                       # pragma: no cover - paranoia
        return [_p("SCHEMA", f"{label}: key set is not enumerable — refused")]
    strkeys = {k for k in actual if _is_strict_str(k)}
    nonstr = sorted((repr(k) for k in actual - strkeys))
    missing = sorted(required_keys - strkeys)
    extra = sorted(strkeys - required_keys)
    problems: list[_Problem] = []
    if missing:
        problems.append(_p("SCHEMA", f"{label}: missing field(s) {missing}"))
    if extra:
        problems.append(
            _p("SCHEMA", f"{label}: unexpected extra field(s) {extra}"))
    if nonstr:
        problems.append(
            _p("SCHEMA", f"{label}: non-string field name(s) {nonstr} — a "
                         "JSON object key is always a string"))
    return problems


def _schema_version_check(label: str, artifact: Mapping) -> list[_Problem]:
    if "schema_version" not in artifact:
        return []
    value = artifact["schema_version"]
    if not _is_strict_str(value) or value != SCHEMA_VERSION:
        return [_p("RECOMPUTE",
                   f"{label}.schema_version {value!r} != the recomputed "
                   f"module token {SCHEMA_VERSION!r} (strict str equality; "
                   "a renamed or absent version token is never sealable)")]
    return []


def _unruled_axis_check(label: str, value: object,
                        vocabulary: "frozenset[str] | None",
                        decision_id: str) -> list[_Problem]:
    """The fail-closed-both-ways rule for an axis THIS SOURCE CONTEXT does
    not rule.

    * `vocabulary is None` (no ruling ON THIS CONTEXT — what a caller that
      passes no `methods` gets): the ONLY admissible value is one of this
      module's UNRESOLVED markers. Anything else — including an arbitrary
      "approved-looking" non-empty string — is refused, because it matches no
      ruled vocabulary and no artifact may authorise its own value. (The
      marker itself still blocks sealing; that problem is raised separately
      by `_marker_problems`, so this function stays silent on a
      correctly-marked field.)
    * a vocabulary IS supplied (the ruling was handed to this context, e.g.
      via `source_context_for_methods`): the value must be a strict `str`
      inside it, and an UNRESOLVED marker is now itself out of vocabulary —
      a marker on a ruled axis is a FALSE disclosure, not a safe default.
    """
    if vocabulary is not None and not isinstance(vocabulary, frozenset):
        # Defence in depth for blind-audit A10. `SourceContext.__post_init__`
        # already normalises every vocabulary to a frozenset and refuses a
        # bare str, so reaching this branch means a caller hand-built a
        # vocabulary argument; `in` on a non-set may not be set membership
        # (on a str it is SUBSTRING matching), so refuse rather than test.
        return [_p("UNRULED",
                   f"{label}: the ruling vocabulary for {decision_id} is a "
                   f"{type(vocabulary).__name__}, not a frozenset — "
                   "membership must be set-of-str semantics; refused rather "
                   "than tested with an operator whose meaning depends on "
                   "the container type")]
    if vocabulary is None:
        if _is_unresolved(value):
            return []
        return [_p("UNRULED",
                   f"{label} {value!r} claims a concrete value on an axis "
                   f"this SOURCE CONTEXT carries NO ruling for (the "
                   f"{decision_id} slot is None) — the only admissible token "
                   "here is an UNRESOLVED marker; an arbitrary non-empty "
                   "string may never impersonate an approved vocabulary. If "
                   "the ruling exists, HAND IT to the context "
                   "(`source_context_for_methods`); an artifact never "
                   "authorises its own vocabulary")]
    if not _is_strict_str(value) or value not in vocabulary:
        return [_p("VOCAB",
                   f"{label} {value!r} is not one of the RULED "
                   f"{decision_id} vocabulary {sorted(vocabulary)} "
                   "(strict str membership; the ruling comes from the "
                   "source context, never from the artifact)")]
    return []


# ===========================================================================
# UNRESOLVED-marker discovery
# ===========================================================================

def _find_unresolved_markers(artifact: object) -> dict[str, int]:
    """Every DISTINCT `"key=value"` UNRESOLVED-marker leaf found anywhere
    inside `artifact`, mapped to how many times it recurs (e.g. `days` holds
    one `event_stratum` marker per date, but the message names it ONCE with
    a multiplicity rather than repeating one line per date).

    Recurses into nested Mappings only (the day/cell keyed dicts this module
    builds); a list/tuple is walked element-wise so a marker inside one is
    still found, but its own index never becomes part of the label. The
    top-level `formal_sealable` key itself is skipped — it is the VERDICT
    this function is deriving evidence for, not evidence of its own.
    """
    counts: dict[str, int] = {}

    def _walk(node: object) -> None:
        if isinstance(node, Mapping):
            for key, value in _sorted_items(node):
                if key == "formal_sealable":
                    continue
                if _is_unresolved(value):
                    label = f"{key}={value!r}"
                    counts[label] = counts.get(label, 0) + 1
                else:
                    _walk(value)
        elif isinstance(node, (list, tuple)):
            for item in node:
                _walk(item)

    _walk(artifact)
    return counts


def _marker_problems(type_name: str, artifact: object) -> list[_Problem]:
    """`_find_unresolved_markers`'s findings, formatted as admission-message
    fragments prefixed by the RECOGNIZED artifact type (never the caller's
    own artifact NAME, which `formal_seal_admission` already prefixes onto
    the final message — this keeps a marker fragment identical regardless of
    which name a caller happens to register the same artifact shape under)."""
    problems: list[_Problem] = []
    for label, count in sorted(_find_unresolved_markers(artifact).items()):
        suffix = f" (x{count})" if count > 1 else ""
        problems.append(_p("UNRESOLVED_MARKER",
                           f"{type_name}: UNRESOLVED marker {label}{suffix}"))
    return problems


def _test_only_problems(type_name: str,
                        source: SourceContext) -> list[_Problem]:
    """The TEST_ONLY refusal: an artifact resolved from SYNTHETIC rulings is
    correctly BUILT and correctly NOT SEALABLE.

    This is the existing `ResolvedS0Methods.test_only` discipline, applied at
    the one place it matters here — `dataset.event_stratum_of` refuses the
    TEST_ONLY mapping on a production path and `study.py` refuses a TEST_ONLY
    quantile estimator the same way; a handoff artifact whose vocabulary came
    from a `test_only=True` method set must likewise never enter a real run's
    sealed set. It is a problem, not a forced flag: `formal_sealable` is still
    `not problems`, and it is this condition that decides.
    """
    if not source.rulings_are_test_only:
        return []
    return [_p("TEST_ONLY",
               f"{type_name}: this source context's rulings are TEST_ONLY "
               "synthetic values (methods.test_only is True) — an artifact "
               "resolved from them is correctly built but must never reach a "
               "real run's sealed set (same fail-closed rule as "
               "dataset.event_stratum_of and study.py's estimator gate)")]


# ===========================================================================
# E6a — DAY_STRATA semantics
# ===========================================================================

_DAY_STRATA_TOP_FIELDS = frozenset(
    {"schema_version", "ordering", "formal_sealable", "days"})
_DAY_ROW_FIELDS = frozenset(
    {"micro_execution_era", "stability_epoch", "year", "d_open",
     "event_flag_final", "event_na", "event_stratum", "vol_status",
     "tp_fp_class"})
_ORDERING_SENTINEL = "sorted-by-date"


def _day_strata_problems(artifact: object,
                         source: SourceContext) -> list[_Problem]:
    """The DAY_STRATA invariants, recomputed from `source` (matrix D1-D13).

    Nothing here trusts a self-reported field: the era, the epoch, the year
    and the whole theta key set are REBUILT — from the date itself against
    `context.MICRO_ERA_BOUNDARY`, from the year against `stability.EPOCHS`,
    and from `study.FROZEN_THETAS` via `study.theta_key` — and compared.
    """
    problems: list[_Problem] = []
    problems += _test_only_problems("day_strata", source)
    problems += _schema_check("day_strata", artifact, _DAY_STRATA_TOP_FIELDS)
    if not isinstance(artifact, Mapping):
        return problems
    problems += _schema_version_check("day_strata", artifact)

    if "ordering" in artifact:
        ordering = artifact["ordering"]
        if not _is_strict_str(ordering) or ordering != _ORDERING_SENTINEL:
            problems.append(_p(
                "RECOMPUTE",
                f"day_strata.ordering {ordering!r} != the recomputed "
                f"{_ORDERING_SENTINEL!r}"))

    days = artifact.get("days")
    if not isinstance(days, Mapping):
        problems.append(_p("SCHEMA",
                           "day_strata.days: expected a mapping, got "
                           f"{type(days).__name__}"))
        problems += _marker_problems("day_strata", artifact)
        return problems

    if not days:
        problems.append(_p(
            "EMPTY",
            "day_strata.days is EMPTY — an empty artifact is never "
            "sealable (vacuous truth refused)"))

    keys = list(days)
    bad_keys = sorted(repr(k) for k in keys if _parsed_date(k) is None)
    if bad_keys:
        problems.append(_p(
            "RECOMPUTE",
            f"day_strata.days has non-ISO-date key(s) {bad_keys} — every key "
            "must be a strict str in exactly YYYY-MM-DD form naming a real "
            "calendar day"))
    else:
        if keys != sorted(keys):
            problems.append(_p(
                "RECOMPUTE",
                "day_strata.days is NOT in ascending date order — the "
                f"artifact declares ordering {_ORDERING_SENTINEL!r} but its own "
                "key sequence contradicts it"))
        if source.day_universe is not None and set(keys) != set(
                source.day_universe):
            missing = sorted(set(source.day_universe) - set(keys))
            extra = sorted(set(keys) - set(source.day_universe))
            problems.append(_p(
                "RECOMPUTE",
                "day_strata.days does not equal the source-context day "
                f"universe — missing {missing[:5]} (n={len(missing)}), "
                f"unexpected {extra[:5]} (n={len(extra)})"))

    theta_keys = tuple(s0_study.theta_key(t) for t in source.thetas)
    theta_key_set = set(theta_keys)
    theta_keys_desc = tuple(s0_study.theta_key(t)
                            for t in sorted(source.thetas, reverse=True))

    for date, row in _sorted_items(days):
        label = f"day_strata.days[{date!r}]"
        problems += _schema_check(label, row, _DAY_ROW_FIELDS)
        if not isinstance(row, Mapping):
            continue
        parsed = _parsed_date(date)

        # --- era: recomputed from the DATE, never read back ------------
        if "micro_execution_era" in row:
            era = row["micro_execution_era"]
            if parsed is None:
                if not _is_strict_str(era) or era not in (source.era_proxy,
                                                          source.era_actual):
                    problems.append(_p(
                        "VOCAB",
                        f"{label}: micro_execution_era {era!r} is not one of "
                        f"{sorted((source.era_proxy, source.era_actual))} "
                        "(frozen S0 §6 two-era axis) — a stability_epoch "
                        "label in this slot would be a conflation"))
            else:
                expected_era = _era_for_date(date, source)
                if not _is_strict_str(era) or era != expected_era:
                    problems.append(_p(
                        "RECOMPUTE",
                        f"{label}: micro_execution_era {era!r} != the era "
                        f"RECOMPUTED from the date itself ({expected_era!r}, "
                        f"frozen S0 §6 boundary "
                        f"{source.micro_era_boundary!r}) — an epoch label in "
                        "this slot is a conflation, and a wrong era label is "
                        "not repairable by the artifact asserting it"))

        # --- epoch: recomputed from the YEAR via stability.EPOCHS ------
        epoch_labels = _epoch_labels(source)
        if "stability_epoch" in row:
            epoch = row["stability_epoch"]
            if parsed is None:
                if not _is_strict_str(epoch) or epoch not in epoch_labels:
                    problems.append(_p(
                        "VOCAB",
                        f"{label}: stability_epoch {epoch!r} is not one of "
                        f"{sorted(epoch_labels)} (frozen S0 §2 epoch labels) "
                        "— a micro_execution_era label in this slot would be "
                        "a conflation"))
            else:
                expected_epoch = _epoch_for_year(parsed.year, source)
                if not _is_strict_str(epoch) or epoch != expected_epoch:
                    problems.append(_p(
                        "RECOMPUTE",
                        f"{label}: stability_epoch {epoch!r} != the epoch "
                        f"RECOMPUTED from year {parsed.year} "
                        f"({expected_epoch!r}) via the SINGLE authoritative "
                        "boundary source stability.EPOCHS "
                        "(2010-2013/2014-2017/2018-2021, else "
                        f"{source.outside_epochs!r}) — era/epoch conflation "
                        "and year/epoch drift are both caught here"))

        # --- year: recomputed from the parsed date ---------------------
        if "year" in row:
            year_value = row["year"]
            if parsed is not None:
                expected_year = f"{parsed.year:04d}"
                if not _is_strict_str(year_value) or year_value != expected_year:
                    problems.append(_p(
                        "RECOMPUTE",
                        f"{label}: year {year_value!r} != the year of the "
                        f"parsed date itself ({expected_year!r}, strict str) "
                        "— date/year consistency violated"))
            elif not _is_strict_str(year_value):
                problems.append(_p(
                    "TYPE", f"{label}: year {year_value!r} must be a strict "
                            "str"))

        # --- d_open: strict int, frozen domain -------------------------
        d_open = row.get("d_open")
        if "d_open" in row and (not _is_strict_int(d_open)
                                or d_open not in (-1, 0, 1)):
            problems.append(_p(
                "TYPE",
                f"{label}: d_open {d_open!r} must be a STRICT int in "
                "(-1, 0, 1) — bool is not int here (True is not +1), and no "
                "int() coercion is applied"))

        # --- event flag / event_na consistency -------------------------
        event_flag = row.get("event_flag_final", ...)
        if "event_flag_final" in row:
            if event_flag is not None and (
                    not _is_strict_str(event_flag)
                    or event_flag not in source.event_flag_values):
                problems.append(_p(
                    "VOCAB",
                    f"{label}: event_flag_final {event_flag!r} is not one of "
                    f"{sorted(source.event_flag_values)} or None (frozen F10 "
                    "vocabulary, IR-12/18 via context.F10_CATEGORIES) — e.g. "
                    "'none_or_na' is NOT a valid value; NA is represented by "
                    "None only"))
        if "event_na" in row and "event_flag_final" in row:
            event_na = row["event_na"]
            expected_na = event_flag is None
            if not _is_strict_bool(event_na) or event_na is not expected_na:
                problems.append(_p(
                    "RECOMPUTE",
                    f"{label}: event_na {event_na!r} != the flag RECOMPUTED "
                    f"from event_flag_final {event_flag!r} ({expected_na!r}) "
                    "— event_na is True if and only if the day carries no "
                    "real event flag; a strict bool, never 0/1"))

        # --- unruled axes ----------------------------------------------
        if "event_stratum" in row:
            problems += _unruled_axis_check(
                f"{label}: event_stratum", row["event_stratum"],
                source.event_stratum_vocabulary, "DR-M6-F")
        if "vol_status" in row:
            problems += _unruled_axis_check(
                f"{label}: vol_status", row["vol_status"],
                source.vol_status_vocabulary, "DR-M6-B-v2")

        # --- tp_fp_class: frozen theta key set + class semantics -------
        if "tp_fp_class" not in row:
            continue
        tp_fp = row["tp_fp_class"]
        if not isinstance(tp_fp, Mapping):
            problems.append(_p("SCHEMA",
                               f"{label}: tp_fp_class must be a mapping, got "
                               f"{type(tp_fp).__name__}"))
            continue
        actual_keys = set(tp_fp)
        if actual_keys != theta_key_set:
            problems.append(_p(
                "RECOMPUTE",
                f"{label}: tp_fp_class keys "
                f"{sorted(repr(k) for k in actual_keys)} != the theta key set "
                f"REBUILT from study.FROZEN_THETAS via study.theta_key "
                f"{sorted(theta_key_set)}"))
        bad_values = {k: v for k, v in _sorted_items(tp_fp)
                      if not _is_strict_str(v) or v not in _TP_FP_VALUES}
        if bad_values:
            problems.append(_p(
                "VOCAB",
                f"{label}: tp_fp_class has non-TP/FP/non_tradeable value(s) "
                f"{bad_values}"))
            continue
        if actual_keys != theta_key_set:
            continue

        if d_open == 0:
            not_non_tradeable = {k: v for k, v in _sorted_items(tp_fp)
                                 if v != _NON_TRADEABLE}
            if not_non_tradeable:
                problems.append(_p(
                    "RECOMPUTE",
                    f"{label}: d_open == 0 (no direction) requires "
                    f"tp_fp_class == 'non_tradeable' for EVERY theta, got "
                    f"{not_non_tradeable} — frozen S0 §5 no-direction days "
                    "are not Oracle days and can never be TP"))
        n_nt = sum(1 for v in tp_fp.values() if v == _NON_TRADEABLE)
        if 0 < n_nt < len(theta_key_set):
            problems.append(_p(
                "RECOMPUTE",
                f"{label}: tradeability is theta-INDEPENDENT but tp_fp_class "
                f"marks {n_nt} of {len(theta_key_set)} thetas "
                f"'non_tradeable' — a day is non-tradeable for every theta "
                "or for none"))

        for hi_key, lo_key in zip(theta_keys_desc, theta_keys_desc[1:]):
            hi_v, lo_v = tp_fp[hi_key], tp_fp[lo_key]
            if hi_v == "TP" and lo_v != "TP":
                problems.append(_p(
                    "RECOMPUTE",
                    f"{label}: THETA NESTING MONOTONICITY violated — "
                    f"tp_fp_class[{hi_key!r}] == 'TP' but "
                    f"tp_fp_class[{lo_key!r}] == {lo_v!r}; the TP set at a "
                    "HIGHER theta must be a SUBSET of the TP set at a LOWER "
                    "theta (Y_cont >= hi implies Y_cont >= lo)"))
            if lo_v == "FP" and hi_v != "FP":
                problems.append(_p(
                    "RECOMPUTE",
                    f"{label}: THETA NESTING MONOTONICITY violated — "
                    f"tp_fp_class[{lo_key!r}] == 'FP' but "
                    f"tp_fp_class[{hi_key!r}] == {hi_v!r}; the FP set at a "
                    "LOWER theta must be a SUBSET of the FP set at a HIGHER "
                    "theta (Y_cont < lo implies Y_cont < hi)"))

    problems += _marker_problems("day_strata", artifact)
    return problems


def check_day_strata_semantics(artifact: object,
                               source: "SourceContext | None" = None,
                               ) -> list[str]:
    """PURE spec-driven DAY_STRATA semantic checker — the single source of
    the DAY_STRATA invariants, used by BOTH `build_day_strata` (to guarantee
    its own output) and `formal_seal_admission` (which additionally rebuilds
    expected content from `source`).

    Returns a list of problem strings; EMPTY means the artifact is
    semantically sealable under `source`. Never raises, for any input.
    """
    try:
        src = _resolve_source(source)
    except Exception as exc:                # noqa: BLE001 - deliberate net
        return [_source_refusal("day_strata", exc)]
    return [pr.text for pr in _guarded(_day_strata_problems, "day_strata",
                                       artifact, src)]


# ===========================================================================
# E6a — build_day_strata
# ===========================================================================

_REQUIRED_DAY_ROW_KEYS = ("micro_execution_era", "stability_epoch", "year",
                          "d_open", "event_flag_final", "vol_status",
                          "tp_fp_class")


def _day_event_stratum(date: str, row: Mapping[str, object],
                       ruled: object) -> str:
    """One day's `event_stratum`: the ruled DR-6 derivation, or the marker.

    `ruled is None` (no `methods` handed to this build) -> the marker, which
    is a TRUE statement about THIS call. Otherwise the value is derived from
    the day's own `event_flag_final` by `dataset.event_stratum_of`, the owner
    of the mapping — this module holds no copy of it and no fallback: a flag
    that module refuses is a `ValueError` here, never a quiet marker (a
    silent downgrade would hide a real defect behind a routine-looking
    disclosure).
    """
    if ruled is None:
        return _unresolved("DR-M6-F")
    flag = row["event_flag_final"]
    try:
        return s0_dataset.event_stratum_of(flag, ruled.event_na_mapping,
                                           ruled.test_only)
    except ValueError as exc:
        raise ValueError(
            f"{date}: event_flag_final {flag!r} has no DR-6 event stratum "
            f"under the ruled mapping: {_safe_reason(exc)}") from exc


def build_day_strata(day_rows: Mapping[str, Mapping[str, object]],
                     thetas: Sequence[float], *,
                     methods: object = None) -> dict[str, object]:
    """Wrap the per-day classification into the frozen handoff shape.

    Parameters
    ----------
    day_rows
        date -> {"micro_execution_era", "stability_epoch", "year", "d_open",
        "event_flag_final", "vol_status", "tp_fp_class"}. See module
        docstring for the event_stratum discipline and the
        micro_execution_era / stability_epoch distinctness rule.
    thetas
        the frozen theta values this handoff round reports (subset of the
        frozen {0.5, 0.3} pair) — used only to validate each day's
        `tp_fp_class` covers exactly this set of theta keys.
    methods
        keyword-only; a FULLY-RESOLVED `contracts.ResolvedS0Methods`, or
        `None`.

        * `None` (LEGACY) — bit-identical to the pre-ruling behaviour: every
          day's `event_stratum` is the "UNRESOLVED_DR-M6-F" marker and the
          caller's `vol_status` may only BE a marker, so the artifact is
          never sealable.
        * supplied — `event_stratum` is DERIVED per day from that day's own
          `event_flag_final` through `dataset.event_stratum_of` (DR-6), and
          the caller's per-day `vol_status` labels are checked against the
          ruled `dataset.VOL_ALL_LABELS` vocabulary (DR-2). The vol labels
          themselves still come from `day_rows` — this module does not
          compute vol20 — and a leftover UNRESOLVED marker in that slot is
          now REFUSED as a false disclosure, not tolerated.

        A `test_only=True` method set is accepted (so every path a real one
        takes is testable) but travels onto the source context, which keeps
        the artifact NOT sealable.

    Returns
    -------
    {"schema_version", "ordering": "sorted-by-date", "formal_sealable",
     "days": {date: row}} with `days` built in canonical (sorted) date order.

    The assembled artifact is then handed to `check_day_strata_semantics`
    with a source context built from `thetas` (and from `methods`, when
    supplied) — the SAME checker admission runs — and any problem that is not
    a disclosed non-sealability (`EMPTY` / `UNRESOLVED_MARKER` / `TEST_ONLY`)
    becomes a `ValueError`. There is exactly one implementation of the
    invariants.
    """
    ruled = None if methods is None else _validated_methods(methods)
    theta_keys = tuple(s0_study.theta_key(t) for t in thetas)
    if not theta_keys:
        raise ValueError("thetas must not be empty")
    if len(set(theta_keys)) != len(theta_keys):
        raise ValueError(f"duplicate theta in {thetas}")

    bad_date_keys = sorted(repr(d) for d in day_rows if not _is_strict_str(d))
    if bad_date_keys:
        raise ValueError(
            f"day_rows keys must be ISO date strings, got {bad_date_keys}")

    days: dict[str, object] = {}
    for date in sorted(day_rows):
        row = day_rows[date]
        if not isinstance(row, Mapping):
            raise ValueError(f"{date}: day_rows entry must be a mapping, got "
                             f"{type(row).__name__}")
        if "event_stratum" in row:
            raise ValueError(
                f"{date}: day_rows must not carry 'event_stratum' — this "
                "module DERIVES it (from the day's own event_flag_final "
                "through the ruled DR-6 mapping when `methods` is supplied, "
                "and as an UNRESOLVED marker otherwise) and refuses a "
                "caller-supplied vocabulary on BOTH paths: an artifact whose "
                "stratum came from its own producer is self-authorising")
        missing = [k for k in _REQUIRED_DAY_ROW_KEYS if k not in row]
        if missing:
            raise ValueError(f"{date}: day_rows entry missing {missing}")
        tp_fp_class = row["tp_fp_class"]
        if not isinstance(tp_fp_class, Mapping):
            raise ValueError(f"{date}: tp_fp_class must be a mapping, got "
                             f"{type(tp_fp_class).__name__}")

        # NO coercion: every value is carried through EXACTLY as supplied, so
        # a wrongly-typed caller value reaches the checker as the wrong type
        # and is refused there rather than being silently normalised into the
        # type it should have been (item 3).
        days[date] = {
            "micro_execution_era": row["micro_execution_era"],
            "stability_epoch": row["stability_epoch"],
            "year": row["year"],
            "d_open": row["d_open"],
            "event_flag_final": row["event_flag_final"],
            "event_na": row["event_flag_final"] is None,
            # DR-6: DERIVED from this day's own event_flag_final by the module
            # that owns the ruled mapping. With no `methods` the mapping was
            # never handed to this call, and the marker is the truthful
            # disclosure of that — for EVERY day, NA branch or not.
            "event_stratum": _day_event_stratum(date, row, ruled),
            # DR-2: the LABEL is the caller's (this module never computes
            # vol20); `methods` only decides which labels are admissible.
            "vol_status": row["vol_status"],
            "tp_fp_class": {k: tp_fp_class[k] for k in theta_keys
                            if k in tp_fp_class},
        }
        extra_theta = sorted(set(tp_fp_class) - set(theta_keys))
        if extra_theta or len(days[date]["tp_fp_class"]) != len(theta_keys):
            raise ValueError(
                f"{date}: tp_fp_class keys "
                f"{sorted(repr(k) for k in tp_fp_class)} != the requested "
                f"thetas {sorted(theta_keys)}")

    artifact = {
        "schema_version": SCHEMA_VERSION,
        "ordering": _ORDERING_SENTINEL,
        "formal_sealable": False,
        "days": days,
    }
    # The builder's OWN source context: the frozen constants plus exactly the
    # thetas it was asked for, and — only when `methods` was supplied — the
    # rulings that method set carries. With no `methods` every axis stays
    # unruled, which is what keeps `event_stratum` / `vol_status`
    # UNRESOLVED-only on the legacy path.
    src = (SourceContext(thetas=tuple(thetas)) if ruled is None
           else source_context_for_methods(ruled, thetas=tuple(thetas)))
    problems = _guarded(_day_strata_problems, "day_strata", artifact, src)
    defects = [pr for pr in problems
               if pr.code not in _BUILDER_TOLERATED_CODES]
    if defects:
        raise ValueError("; ".join(pr.text for pr in defects))
    # formal_sealable: False whenever ANY problem remains. On the LEGACY path
    # that is always true (the event_stratum + vol_status markers, and LOW-3's
    # rule that an EMPTY artifact is never sealable). On the RULED path the
    # markers are gone, so this re-evaluates HONESTLY — a non-empty,
    # fully-recomputable day_strata built from a non-test_only method set does
    # become sealable, and nothing here forces either verdict: the conditions
    # decide, and they are the same conditions admission re-runs.
    artifact["formal_sealable"] = not problems
    return artifact


# ===========================================================================
# E6b — GRID_SAMPLES semantics
# ===========================================================================

_GRID_SAMPLES_TOP_FIELDS = frozenset(
    {"schema_version", "formal_sealable", "replay_status", "cells",
     "run_meta", "replay"})
_GRID_CELL_FIELDS = frozenset(
    {"per_seed", "infeasible_by_sample", "q_mil", "r_mil"})
_GRID_PER_SEED_FIELDS = frozenset(
    {"tp_dates", "fp_dates", "markers", "realized_precision",
     "realized_recall", "target_precision", "target_recall"})
_GRID_RUN_META_FIELDS = frozenset({"theta", "engine", "scenario"})
_GRID_REPLAY_FIELDS = frozenset(
    {"stream_formula", "grid_stream_tag", "k_policy", "crn_scope"})


def _strict_date_list(value: object) -> "list[str] | None":
    """`value` as a list of strict ISO date strings, or None when it is not
    one (a tuple is accepted; a str/bytes never is)."""
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        return None
    out: list[str] = []
    for item in value:
        if _parsed_date(item) is None:
            return None
        out.append(item)
    return out


def _grid_samples_problems(artifact: object,
                           source: SourceContext) -> list[_Problem]:
    """The GRID_SAMPLES invariants, recomputed from `source` (matrix
    D26-D34). Cross-artifact checks against DAY_STRATA / SEED_MANIFEST live
    in `_grid_cross_problems` and are added by the bundle admission gate."""
    problems: list[_Problem] = []
    problems += _test_only_problems("grid_samples", source)
    problems += _schema_check("grid_samples", artifact,
                              _GRID_SAMPLES_TOP_FIELDS)
    if not isinstance(artifact, Mapping):
        return problems
    problems += _schema_version_check("grid_samples", artifact)

    # --- replay_status: truthful AND sealable, or refused ---------------
    if "replay_status" in artifact:
        replay_status = artifact["replay_status"]
        if source.replay_closure_ruled:
            if not _is_strict_str(replay_status) or (
                    replay_status != REPLAY_STATUS_CLOSED):
                problems.append(_p(
                    "RECOMPUTE",
                    f"grid_samples.replay_status {replay_status!r} != "
                    f"{REPLAY_STATUS_CLOSED!r} — the source context declares "
                    "multi-stratum replay closure RULED, so nothing short of "
                    "CLOSED is sealable"))
        elif _is_strict_str(replay_status) and (
                replay_status == REPLAY_STATUS_PARTIAL_SINGLE_STRATUM):
            problems.append(_p(
                "PENDING",
                f"grid_samples.replay_status {replay_status!r} is the only "
                "TRUTHFUL status while the MC-SIDE REPLAY WIRING is open, "
                "and a PARTIAL replay is not sealable — fail-closed both "
                "ways, regardless of the artifact's own formal_sealable "
                "flag. What is missing is NOT a pending ruling (DR-2/DR-3/"
                "DR-5/DR-6 are ruled, and with `methods` DAY_STRATA carries "
                "the full (year, vol_status, event_stratum) key): it is that "
                "this artifact carries only gridmix's HEADLINE repeat row "
                "(k = k_start_index) per (seed, cell) and no repeats block, "
                "while DR-5 rules K repeats per seed, and the MC_METHOD_SPEC "
                "§5 convergence battery and its doubling loop run at the MC "
                "wiring and supply `mc_converged`, which no S0-side artifact "
                "can assert"))
        else:
            problems.append(_p(
                "UNRULED",
                f"grid_samples.replay_status {replay_status!r} is refused: "
                "this SOURCE CONTEXT does not declare multi-stratum replay "
                "closure (`replay_closure_ruled` is False — the blocker is "
                "MC wiring: the DR-5 repeat set is absent from the frozen "
                "cell schema and the §5 convergence verdict is MC-side), so "
                f"{REPLAY_STATUS_PARTIAL_SINGLE_STRATUM!r} is the only "
                f"truthful value — a {REPLAY_STATUS_CLOSED!r} (or any other) "
                "claim is a LIE about the replay, not merely a premature "
                "seal"))

    # --- run_meta axis lock --------------------------------------------
    run_meta = artifact.get("run_meta")
    if "run_meta" in artifact:
        problems += _schema_check("grid_samples.run_meta", run_meta,
                                  _GRID_RUN_META_FIELDS)
        if isinstance(run_meta, Mapping):
            if "theta" in run_meta:
                theta_value = run_meta["theta"]
                if not _is_strict_float(theta_value) or (
                        theta_value not in source.thetas):
                    problems.append(_p(
                        "RECOMPUTE",
                        f"grid_samples.run_meta.theta {theta_value!r} is "
                        "not EXACTLY one of study.FROZEN_THETAS "
                        f"{tuple(source.thetas)} (strict float, exact "
                        "equality against the frozen values — no tolerance; "
                        "e.g. 0.5000001 is refused, and an int/bool/str is "
                        "refused rather than coerced)"))
            if "engine" in run_meta:
                engine = run_meta["engine"]
                if not _is_strict_str(engine) or engine not in source.engines:
                    problems.append(_p(
                        "VOCAB",
                        f"grid_samples.run_meta.engine {engine!r} is not one "
                        f"of the frozen {tuple(source.engines)} — unknown or "
                        "renamed engine"))
            if "scenario" in run_meta:
                scenario = run_meta["scenario"]
                if not _is_strict_str(scenario) or (
                        scenario not in source.scenarios):
                    problems.append(_p(
                        "VOCAB",
                        f"grid_samples.run_meta.scenario {scenario!r} is not "
                        f"one of the frozen {tuple(source.scenarios)} — "
                        "unknown scenario"))

    # --- replay provenance ----------------------------------------------
    replay = artifact.get("replay")
    if "replay" in artifact:
        problems += _schema_check("grid_samples.replay", replay,
                                  _GRID_REPLAY_FIELDS)
        if isinstance(replay, Mapping):
            if "grid_stream_tag" in replay:
                tag = replay["grid_stream_tag"]
                if not _is_strict_int(tag) or tag != source.grid_stream_tag:
                    problems.append(_p(
                        "RECOMPUTE",
                        f"grid_samples.replay.grid_stream_tag {tag!r} != the "
                        "recomputed gridmix.GRID_STREAM_TAG "
                        f"{source.grid_stream_tag!r} (strict int)"))
            if "stream_formula" in replay:
                formula = replay["stream_formula"]
                if not _is_strict_str(formula) or (
                        formula != REPLAY_STREAM_FORMULA):
                    problems.append(_p(
                        "RECOMPUTE",
                        f"grid_samples.replay.stream_formula {formula!r} != "
                        f"the rebuilt {REPLAY_STREAM_FORMULA!r} — the replay "
                        "recipe is provenance, not free text"))
            if "k_policy" in replay:
                problems += _unruled_axis_check(
                    "grid_samples.replay.k_policy", replay["k_policy"],
                    None if source.k_policy is None
                    else frozenset({source.k_policy}), "DR-M6-E")
            if "crn_scope" in replay:
                problems += _unruled_axis_check(
                    "grid_samples.replay.crn_scope", replay["crn_scope"],
                    None if source.crn_scope is None
                    else frozenset({source.crn_scope}), "DR-4.7 crn_scope")

    # --- cells -----------------------------------------------------------
    cells = artifact.get("cells")
    if "cells" in artifact:
        if not isinstance(cells, Mapping):
            problems.append(_p("SCHEMA",
                               "grid_samples.cells: expected a mapping, got "
                               f"{type(cells).__name__}"))
        else:
            problems += _grid_cell_problems(cells, source)

    problems += _marker_problems("grid_samples", artifact)
    return problems


def _grid_cell_problems(cells: Mapping,
                        source: SourceContext) -> list[_Problem]:
    problems: list[_Problem] = []
    if not cells:
        problems.append(_p(
            "EMPTY",
            "grid_samples.cells is EMPTY — an empty grid is never sealable"))

    # The expected cell-key set is REBUILT from gridmix's own frozen millis
    # axes, never read off the artifact (matrix D26: a 62- or 64-cell grid
    # used to pass full-schema admission).
    expected_keys = {_grid_cell_key(q, r) for q in source.q_grid_millis
                     for r in source.r_grid_millis}
    actual_keys = {k for k in cells if _is_strict_str(k)}
    if cells:
        missing = sorted(expected_keys - actual_keys)
        extra = sorted(actual_keys - expected_keys)
        if missing:
            problems.append(_p(
                "LATTICE",
                f"grid_samples.cells is missing {len(missing)} of the frozen "
                f"{len(expected_keys)}-point (q, r) lattice REBUILT from "
                f"gridmix.Q_GRID_MILLIS x R_GRID_MILLIS, e.g. {missing[:5]}"))
        if extra:
            problems.append(_p(
                "LATTICE",
                f"grid_samples.cells carries {len(extra)} key(s) that are "
                "NOT on the frozen (q, r) lattice rebuilt from "
                f"gridmix.Q_GRID_MILLIS x R_GRID_MILLIS: {extra[:5]}"))

    frozen_seed_set = set(source.seeds)
    for cell_key, cell in _sorted_items(cells):
        label = f"grid_samples.cells[{cell_key!r}]"
        problems += _schema_check(label, cell, _GRID_CELL_FIELDS)
        if not isinstance(cell, Mapping):
            continue

        q_mil = cell.get("q_mil")
        r_mil = cell.get("r_mil")
        millis_ok = True
        for millis_key, millis_value, axis in (
                ("q_mil", q_mil, source.q_grid_millis),
                ("r_mil", r_mil, source.r_grid_millis)):
            if millis_key not in cell:
                millis_ok = False
                continue
            if not _is_strict_int(millis_value):
                millis_ok = False
                problems.append(_p(
                    "TYPE",
                    f"{label}.{millis_key} must be a strict int, got "
                    f"{millis_value!r} — never coerced"))
            elif millis_value not in axis:
                millis_ok = False
                problems.append(_p(
                    "RECOMPUTE",
                    f"{label}.{millis_key} {millis_value!r} is not on the "
                    f"frozen axis {axis} (gridmix integer millis)"))
        if millis_ok:
            rebuilt_key = _grid_cell_key(q_mil, r_mil)
            if not _is_strict_str(cell_key) or cell_key != rebuilt_key:
                problems.append(_p(
                    "RECOMPUTE",
                    f"{label}: the cell KEY does not equal the key rebuilt "
                    f"from its own q_mil/r_mil fields ({rebuilt_key!r}) — a "
                    "cell filed under someone else's coordinates"))

        infeasible = cell.get("infeasible_by_sample")
        if "infeasible_by_sample" in cell and not _is_strict_bool(infeasible):
            problems.append(_p(
                "TYPE",
                f"{label}.infeasible_by_sample must be a strict bool, got "
                f"{infeasible!r}"))

        if "per_seed" not in cell:
            continue
        per_seed = cell["per_seed"]
        if not isinstance(per_seed, Mapping):
            problems.append(_p("SCHEMA",
                               f"{label}.per_seed: expected a mapping, got "
                               f"{type(per_seed).__name__}"))
            continue
        if infeasible is True:
            if per_seed:
                problems.append(_p(
                    "RECOMPUTE",
                    f"{label}: infeasible_by_sample is True but per_seed is "
                    "not empty — an infeasible point performs no selection"))
            continue

        seed_keys = list(per_seed)
        bad_seeds = [s for s in seed_keys if not _is_strict_int(s)]
        if bad_seeds:
            problems.append(_p(
                "TYPE",
                f"{label}.per_seed has non-strict-int seed key(s) "
                f"{sorted(repr(s) for s in bad_seeds)} — bool/float/"
                "numeric-string seeds are refused, never coerced with int()"))
        else:
            seed_set = set(seed_keys)
            if seed_set != frozen_seed_set:
                problems.append(_p(
                    "RECOMPUTE",
                    f"{label}.per_seed keys {sorted(seed_set)} != the frozen "
                    f"seed set {sorted(frozen_seed_set)} — THIS cell's own "
                    "seed set is incomplete (checked per cell, never merely "
                    "the union across cells)"))

        for seed, block in _sorted_items(per_seed):
            problems += _grid_seed_block_problems(
                f"{label}.per_seed[{seed!r}]", block, q_mil, r_mil,
                millis_ok)
    return problems


def _grid_seed_block_problems(label: str, block: object, q_mil: object,
                              r_mil: object, millis_ok: bool,
                              ) -> list[_Problem]:
    problems = _schema_check(label, block, _GRID_PER_SEED_FIELDS)
    if not isinstance(block, Mapping):
        return problems

    tp_dates = _strict_date_list(block.get("tp_dates"))
    fp_dates = _strict_date_list(block.get("fp_dates"))
    for name, dates in (("tp_dates", tp_dates), ("fp_dates", fp_dates)):
        if name not in block:
            continue
        if dates is None:
            problems.append(_p(
                "TYPE",
                f"{label}.{name} must be a list of strict ISO date strings, "
                f"got {block[name]!r}"))
        elif len(set(dates)) != len(dates):
            problems.append(_p(
                "RECOMPUTE",
                f"{label}.{name} contains duplicate date(s) — a selection is "
                "without replacement"))
        elif dates != sorted(dates):
            problems.append(_p(
                "RECOMPUTE",
                f"{label}.{name} is not in ascending date order (gridmix "
                "`_select` returns a sorted list)"))
    if tp_dates is not None and fp_dates is not None:
        both = sorted(set(tp_dates) & set(fp_dates))
        if both:
            problems.append(_p(
                "RECOMPUTE",
                f"{label}: {len(both)} date(s) appear in BOTH tp_dates and "
                f"fp_dates, e.g. {both[:5]} — D_TP and D_FP are mutually "
                "exclusive populations"))

    # --- day_markers is a pure re-encoding of the two date lists (CR-8) --
    if "markers" in block and tp_dates is not None and fp_dates is not None:
        expected = sorted([(d, s0_gridmix.MARK_TP) for d in tp_dates]
                          + [(d, s0_gridmix.MARK_FP) for d in fp_dates])
        markers = block["markers"]
        rebuilt: "list[tuple[str, str]] | None" = []
        if isinstance(markers, (str, bytes)) or not isinstance(markers,
                                                               Sequence):
            rebuilt = None
        else:
            for item in markers:
                if (isinstance(item, (str, bytes))
                        or not isinstance(item, Sequence)
                        or len(item) != 2
                        or not all(_is_strict_str(x) for x in item)):
                    rebuilt = None
                    break
                rebuilt.append((item[0], item[1]))
        if rebuilt is None:
            problems.append(_p(
                "TYPE",
                f"{label}.markers must be a list of [date, 'tp'|'fp'] string "
                f"pairs, got {markers!r}"))
        elif rebuilt != expected:
            problems.append(_p(
                "RECOMPUTE",
                f"{label}.markers is not the sorted re-encoding of this "
                "block's own tp_dates/fp_dates — the day-marker sequence is "
                "the field MC actually consumes (frozen App A step 4) and it "
                "must not disagree with the date lists it claims to encode"))

    # --- target precision/recall rebuilt from the cell's own millis ------
    if millis_ok:
        for field_name, millis in (("target_precision", q_mil),
                                   ("target_recall", r_mil)):
            if field_name not in block:
                continue
            value = block[field_name]
            expected_value = millis / 1000.0
            if not _is_strict_float(value) or value != expected_value:
                problems.append(_p(
                    "RECOMPUTE",
                    f"{label}.{field_name} {value!r} != the value REBUILT "
                    f"from the cell's own integer millis "
                    f"({expected_value!r}) — gridmix materialises q/r only "
                    "as `millis / 1000.0`"))

    # --- realized precision rebuilt from this block's own date lists -----
    if ("realized_precision" in block and tp_dates is not None
            and fp_dates is not None):
        n_tp, n_fp = len(tp_dates), len(fp_dates)
        n_total = n_tp + n_fp
        expected_precision = (n_tp / n_total) if n_total else None
        value = block["realized_precision"]
        if expected_precision is None:
            if value is not None:
                problems.append(_p(
                    "RECOMPUTE",
                    f"{label}.realized_precision {value!r} != the recomputed "
                    "None (an empty mixture has no precision)"))
        elif not _is_strict_float(value) or value != expected_precision:
            problems.append(_p(
                "RECOMPUTE",
                f"{label}.realized_precision {value!r} != "
                f"n_tp/(n_tp+n_fp) recomputed from this block's OWN date "
                f"lists ({expected_precision!r})"))
    return problems


def check_grid_samples_semantics(artifact: object,
                                 source: "SourceContext | None" = None,
                                 ) -> list[str]:
    """PURE spec-driven GRID_SAMPLES semantic checker (single-artifact
    scope). The cross-artifact conservation checks against DAY_STRATA and
    SEED_MANIFEST are bundle-level and live in `formal_seal_admission`;
    calling THIS function alone therefore proves LESS than admission does,
    by construction. Never raises, for any input."""
    try:
        src = _resolve_source(source)
    except Exception as exc:                # noqa: BLE001 - deliberate net
        return [_source_refusal("grid_samples", exc)]
    return [pr.text for pr in _guarded(_grid_samples_problems, "grid_samples",
                                       artifact, src)]


# ===========================================================================
# E6b — build_grid_samples
# ===========================================================================

# run_meta is no longer an opaque passthrough: it is exactly which
# theta/engine/scenario this ONE grid belongs to (build_grid is always
# called for ONE engine x cost-scenario x theta), and `verify_handoff_
# conservation` now reads `run_meta["theta"]` to check the PER-THETA TP/FP
# classification, so its shape must be pinned rather than caller-defined.
_REQUIRED_RUN_META: dict[str, tuple[type, ...]] = {
    "theta": (int, float),
    "engine": (str,),
    "scenario": (str,),
}


def _validated_run_meta(run_meta: Mapping[str, object]) -> dict[str, object]:
    unknown = sorted(set(run_meta) - set(_REQUIRED_RUN_META))
    if unknown:
        raise ValueError(
            f"run_meta has unknown key(s) {unknown} — only "
            f"{sorted(_REQUIRED_RUN_META)} are recognised (unknown keys are "
            "rejected rather than silently passed through)")
    missing = [k for k in _REQUIRED_RUN_META if k not in run_meta]
    if missing:
        raise ValueError(f"run_meta is missing required key(s) {missing} "
                         f"(needs {sorted(_REQUIRED_RUN_META)})")
    out: dict[str, object] = {}
    for key, types in _REQUIRED_RUN_META.items():
        value = run_meta[key]
        if isinstance(value, bool) or not isinstance(value, types):
            raise ValueError(
                f"run_meta[{key!r}] must be one of {types}, got {value!r} "
                f"({type(value).__name__})")
        # JUSTIFIED COERCION (build path, not a validation path): theta is
        # NORMALISED to float exactly once, here, so the sealed artifact
        # carries one JSON number type on that axis. The validation path
        # (`_grid_samples_problems`) then requires a STRICT float and exact
        # membership in FROZEN_THETAS — it never coerces.
        out[key] = float(value) if key == "theta" else value
    return out


def _exact_millis(value: object, name: str) -> int:
    """Recover gridmix's ORIGINAL integer millis from the float it published
    as `millis / 1000.0`, and PROVE the round-trip. JUSTIFIED COERCION (build
    path): `int(round(...))` runs only after the value is confirmed a strict
    float, and the result is verified to reproduce the input exactly, so this
    can never silently accept a value that was not a real lattice coordinate.
    """
    if not _is_strict_float(value):
        raise ValueError(f"{name} must be a float published by gridmix as "
                         f"`millis / 1000.0`, got {value!r} "
                         f"({type(value).__name__})")
    millis = int(round(value * 1000))
    if millis / 1000.0 != value:
        raise ValueError(
            f"{name} {value!r} does not round-trip through integer millis "
            f"({millis} -> {millis / 1000.0!r}) — it was not produced by "
            "gridmix's integer q/r axes")
    return millis


def build_grid_samples(grid_output: Mapping[str, object],
                       run_meta: Mapping[str, object], *,
                       methods: object = None) -> dict[str, object]:
    """Wrap one `gridmix.build_grid(...)` output into the MC handoff shape.

    Parameters
    ----------
    grid_output
        the return value of `gridmix.build_grid` (or `_build_grid_unchecked`
        in a test) for ONE engine x cost-scenario x theta.
    run_meta
        provenance for which theta/engine/scenario this grid belongs to.
        Required keys, validated and normalised (unknown keys rejected):
        `"theta"` (int or float, stored as float), `"engine"` (str),
        `"scenario"` (str).
    methods
        keyword-only; a FULLY-RESOLVED `contracts.ResolvedS0Methods`, or
        `None`. `None` (LEGACY) emits `replay.k_policy` as
        "UNRESOLVED_DR-M6-E" and `replay.crn_scope` as the bare UNRESOLVED
        sentinel, bit-identical to the pre-ruling output. Supplied, they
        become the RULED values — `ruled_k_policy(methods)` (DR-5, built from
        `methods.grid_policy`'s own fields) and
        `methods.bootstrap_method.crn_scope` (DR-4.7).

    Returns
    -------
    {"schema_version", "formal_sealable", "replay_status", "cells":
        {cell_key: {"per_seed": {seed: {...}}, "infeasible_by_sample",
                   "q_mil", "r_mil"}},
     "run_meta", "replay": {"stream_formula", "grid_stream_tag", "k_policy",
                           "crn_scope"}}

    `replay_status` is ALWAYS `REPLAY_STATUS_PARTIAL_SINGLE_STRATUM`, on the
    ruled path too (M6.1.1 S2 item 5), and that is a HONEST refusal to
    upgrade rather than a stale marker. The pre-ruling reason has genuinely
    gone away — with `methods`, DAY_STRATA carries the real
    `(year, vol_status, event_stratum)` Appendix-A key — but two MC-side gaps
    remain, and either one alone makes CLOSED a lie:

    * this artifact carries only gridmix's HEADLINE repeat row
      (`k = k_start_index`) per (seed, cell); the frozen cell schema has no
      `repeats` block, so the DR-5 K-repeat set cannot be rebuilt from these
      bytes; and
    * the MC_METHOD_SPEC §5 four-rule convergence battery and its doubling
      loop run at the MC WIRING and supply `mc_converged` — gridmix runs
      `doublings=0` and declares no verdict, so no S0-side artifact can
      assert convergence.

    The gap is disclosed as DATA, not only as a docstring sentence.

    SELF-CHECK SCOPE (deliberate, disclosed): the assembled artifact is run
    through `_grid_samples_problems`, but the `LATTICE` / `CROSS` /
    `DEPENDENCY` problem classes are TOLERATED here, because
    `gridmix.build_grid` legitimately accepts `q_grid` / `r_grid` axis
    overrides for tests and sensitivity runs — "carries the full frozen
    63-point lattice" and "agrees with a co-supplied DAY_STRATA" are
    ADMISSION-level contracts on what may be SEALED, not construction
    invariants. Everything a builder actually controls (schema, types,
    vocabularies, per-cell recomputation) does raise here.
    """
    ruled = None if methods is None else _validated_methods(methods)
    validated_run_meta = _validated_run_meta(run_meta)
    grid = grid_output["grid"]
    cells: dict[str, object] = {}
    for cell_key, point in grid.items():
        per_seed: dict[object, object] = {}
        for seed, block in point.get("per_seed", {}).items():
            per_seed[seed] = {
                "tp_dates": list(block["tp_dates"]),
                "fp_dates": list(block["fp_dates"]),
                "markers": [list(m) for m in block["day_markers"]],
                "realized_precision": block["realized_precision"],
                "realized_recall": block["realized_recall"],
                "target_precision": block["target_precision"],
                "target_recall": block["target_recall"],
            }
        infeasible = point["infeasible_by_sample"]
        if not _is_strict_bool(infeasible):
            # was `bool(...)` — a coercion. gridmix always writes a real
            # bool here, so anything else is a defect in the grid_output,
            # and truthiness-coercing it would launder that defect into the
            # sealed artifact (item 3: no coercion, anywhere).
            raise ValueError(
                f"{cell_key}.infeasible_by_sample must be a strict bool, got "
                f"{infeasible!r} ({type(infeasible).__name__})")
        cells[cell_key] = {
            "per_seed": per_seed,
            "infeasible_by_sample": infeasible,
            "q_mil": _exact_millis(point["target_precision"],
                                   f"{cell_key}.target_precision"),
            "r_mil": _exact_millis(point["target_recall"],
                                   f"{cell_key}.target_recall"),
        }

    replay = {
        "stream_formula": REPLAY_STREAM_FORMULA,
        "grid_stream_tag": s0_gridmix.GRID_STREAM_TAG,
        # DR-5 / DR-4.7: the RULED values when a method set was handed to this
        # call, the marker otherwise — the marker being a true statement about
        # THIS call, not a claim that the decision is open.
        "k_policy": (_unresolved("DR-M6-E") if ruled is None
                     else ruled_k_policy(ruled)),
        "crn_scope": (str(UNRESOLVED) if ruled is None
                      else ruled_crn_scope(ruled)),
    }
    artifact = {
        "schema_version": SCHEMA_VERSION,
        "formal_sealable": False,
        "replay_status": REPLAY_STATUS_PARTIAL_SINGLE_STRATUM,
        "cells": cells,
        "run_meta": validated_run_meta,
        "replay": replay,
    }
    src = (SourceContext(thetas=FROZEN_THETAS) if ruled is None
           else source_context_for_methods(ruled, thetas=FROZEN_THETAS))
    problems = _guarded(_grid_samples_problems, "grid_samples", artifact, src)
    defects = [pr for pr in problems
               if pr.code not in _GRID_BUILDER_TOLERATED_CODES]
    if defects:
        raise ValueError("; ".join(pr.text for pr in defects))
    # Still False on the ruled path — not because a ruling is missing, but
    # because `replay_status` is truthfully PARTIAL while the MC-side replay
    # wiring is open (see the docstring above). The two DR axes this artifact
    # DOES carry (k_policy, crn_scope) stop contributing problems, so the
    # remaining refusal names the real blocker instead of a ruled DR.
    artifact["formal_sealable"] = not problems
    return artifact


# ===========================================================================
# E6c — SEED_MANIFEST semantics
# ===========================================================================

_SEED_MANIFEST_TOP_FIELDS = frozenset(
    {"schema_version", "formal_sealable", "research_bootstrap_seeds",
     "quoted_seed_convention", "stream_tags", "k_policy", "crn_scope",
     "engineering_seed_note"})
_STREAM_TAGS_FIELDS = frozenset({"stats_stream_tag", "grid_stream_tag"})


def rebuild_seed_manifest(source: "SourceContext | None" = None, *,
                          methods: object = None) -> dict[str, object]:
    """The ENTIRE expected SEED_MANIFEST, rebuilt from the source context —
    every field, not just the seeds and stream tags: the schema version
    token, the quoted-seed convention PROSE, the engineering-seed note, the
    stream tags and the two decision slots (`k_policy` / `crn_scope`), which
    carry the RULED value when the context rules them and the UNRESOLVED
    marker when it does not.

    `methods` is a convenience seam for a caller holding the ruled method set
    rather than a context: it is turned into one by
    `source_context_for_methods`. Passing BOTH is refused — two anchors with
    no rule for choosing between them is exactly the ambiguity every other
    dependency gate in this module fails closed on.

    `build_seed_manifest` emits exactly this plus the derived
    `formal_sealable` verdict, and `check_seed_manifest_semantics` requires
    DEEP EQUALITY against it. That is what makes a manifest whose prose has
    been rewritten (e.g. to claim "quoted = best-of three seeds") a REFUSAL
    rather than an unread string.
    """
    if methods is not None:
        if source is not None:
            raise RulingError(
                "rebuild_seed_manifest takes `source` OR `methods`, never "
                "both — there is no rule for choosing which one anchors the "
                "rebuild, so it fails closed. Pass `methods` and let "
                "`source_context_for_methods` derive the context, or build "
                "the context yourself and pass `source`")
        source = source_context_for_methods(methods)
    src = _resolve_source(source)
    return {
        "schema_version": SCHEMA_VERSION,
        "research_bootstrap_seeds": list(contracts.RESEARCH_BOOTSTRAP_SEEDS),
        "quoted_seed_convention": QUOTED_SEED_CONVENTION,
        "stream_tags": {"stats_stream_tag": src.stats_stream_tag,
                        "grid_stream_tag": src.grid_stream_tag},
        "k_policy": (_unresolved("DR-M6-E") if src.k_policy is None
                     else src.k_policy),
        "crn_scope": (str(UNRESOLVED) if src.crn_scope is None
                      else src.crn_scope),
        "engineering_seed_note": ENGINEERING_SEED_NOTE,
    }


def _seed_manifest_problems(artifact: object,
                            source: SourceContext) -> list[_Problem]:
    """SEED_MANIFEST must be REBUILDABLE, in full, from formal content
    (matrix D39-D41). The seeds come from `contracts.RESEARCH_BOOTSTRAP_SEEDS`
    and the stream tags from `stats.STATS_STREAM_TAG` / `gridmix.
    GRID_STREAM_TAG` — the exact single-sourced constants
    `build_seed_manifest` itself reads — and EVERY OTHER FIELD is compared
    against the rebuilt manifest too."""
    problems: list[_Problem] = []
    problems += _test_only_problems("seed_manifest", source)
    problems += _schema_check("seed_manifest", artifact,
                              _SEED_MANIFEST_TOP_FIELDS)
    if not isinstance(artifact, Mapping):
        return problems

    expected = rebuild_seed_manifest(source)

    # --- seeds: strict ints, exact ORDERED equality --------------------
    if "research_bootstrap_seeds" in artifact:
        seeds = artifact["research_bootstrap_seeds"]
        if isinstance(seeds, (str, bytes)) or not isinstance(seeds, Sequence):
            problems.append(_p(
                "TYPE",
                "seed_manifest.research_bootstrap_seeds must be a sequence, "
                f"got {type(seeds).__name__}"))
        else:
            bad_seeds = [s for s in seeds if not _is_strict_int(s)]
            if bad_seeds:
                problems.append(_p(
                    "TYPE",
                    "seed_manifest.research_bootstrap_seeds has non-strict-"
                    f"int entrie(s) {sorted(repr(s) for s in bad_seeds)} — "
                    "bool/float/numeric-string seeds are refused, never "
                    "coerced with int()"))
            elif list(seeds) != expected["research_bootstrap_seeds"]:
                problems.append(_p(
                    "RECOMPUTE",
                    f"seed_manifest.research_bootstrap_seeds {list(seeds)} "
                    "!= the recomputed contracts.RESEARCH_BOOTSTRAP_SEEDS "
                    f"{expected['research_bootstrap_seeds']} — REBUILT from "
                    "the single source of truth, never trusted verbatim "
                    "(ORDER is part of the content: the FIRST seed is the "
                    "quoted-interval convention)"))

    # --- stream tags: strict ints, rebuilt from the owning modules -----
    if "stream_tags" in artifact:
        stream_tags = artifact["stream_tags"]
        problems += _schema_check("seed_manifest.stream_tags", stream_tags,
                                  _STREAM_TAGS_FIELDS)
        if isinstance(stream_tags, Mapping):
            for key, want in expected["stream_tags"].items():
                if key not in stream_tags:
                    continue
                got = stream_tags[key]
                if not _is_strict_int(got) or got != want:
                    problems.append(_p(
                        "RECOMPUTE",
                        f"seed_manifest.stream_tags[{key!r}] {got!r} != the "
                        f"recomputed {want!r} (strict int, single-sourced "
                        "from its owning module's constant)"))

    # --- every remaining field: deep equality against the rebuild -------
    for key in ("schema_version", "quoted_seed_convention",
                "engineering_seed_note"):
        if key not in artifact:
            continue
        got = artifact[key]
        want = expected[key]
        if not _is_strict_str(got) or got != want:
            problems.append(_p(
                "RECOMPUTE",
                f"seed_manifest.{key} does not equal the REBUILT text — got "
                f"{got!r}, rebuilt {want!r}. The whole manifest is rebuilt "
                "from frozen constants and compared field by field, so prose "
                "that misstates the convention (e.g. claiming the quoted "
                "value is a best-of across seeds) is a refusal, not an "
                "unread string"))

    # --- unruled axes ---------------------------------------------------
    if "k_policy" in artifact:
        problems += _unruled_axis_check(
            "seed_manifest.k_policy", artifact["k_policy"],
            None if source.k_policy is None
            else frozenset({source.k_policy}), "DR-M6-E")
    if "crn_scope" in artifact:
        problems += _unruled_axis_check(
            "seed_manifest.crn_scope", artifact["crn_scope"],
            None if source.crn_scope is None
            else frozenset({source.crn_scope}), "DR-4.7 crn_scope")

    problems += _marker_problems("seed_manifest", artifact)
    return problems


def check_seed_manifest_semantics(artifact: object,
                                  source: "SourceContext | None" = None,
                                  ) -> list[str]:
    """PURE spec-driven SEED_MANIFEST semantic checker: DEEP equality against
    `rebuild_seed_manifest(source)`. Never raises, for any input."""
    try:
        src = _resolve_source(source)
    except Exception as exc:                # noqa: BLE001 - deliberate net
        return [_source_refusal("seed_manifest", exc)]
    return [pr.text for pr in _guarded(_seed_manifest_problems,
                                       "seed_manifest", artifact, src)]


def build_seed_manifest(*, methods: object = None) -> dict[str, object]:
    """The frozen seed/stream provenance MC needs to replay S0's randomness,
    read from the modules that own each constant (never a second copy).

    `methods` is keyword-only and defaults to `None`, which reproduces the
    pre-ruling artifact BIT FOR BIT — including the `DEFAULT_SOURCE_CONTEXT`
    read at CALL time, the injection seam a renderer-level test monkeypatches.
    With a fully-resolved, non-test_only method set the two decision slots
    carry their RULED values (DR-5 `k_policy`, DR-4.7 `crn_scope`), no
    UNRESOLVED marker is left anywhere in the artifact, and — SEED_MANIFEST
    having no other open axis and no bundle dependency — `formal_sealable`
    honestly evaluates to True. This is the only one of the three artifact
    types with a production caller today
    (`scripts/s0_real_run.render_s0_report`).
    """
    # IR DR-02 single-source guard: stats.py / gridmix.py must be
    # re-exporting the SAME object as contracts.RESEARCH_BOOTSTRAP_SEEDS, not
    # a local copy that could silently drift. A production governance gate
    # must be a real `raise`, never a bare `assert` — `python -O` strips
    # `assert` statements, which would silently disable this exact check.
    if s0_stats.RESEARCH_BOOTSTRAP_SEEDS is not contracts.RESEARCH_BOOTSTRAP_SEEDS:
        raise AssertionError(
            "itsf.s0.stats.RESEARCH_BOOTSTRAP_SEEDS is not the SAME object "
            "as contracts.RESEARCH_BOOTSTRAP_SEEDS — IR DR-02 single-source "
            "mutation guard tripped (a local copy would silently drift from "
            "the one research-seed source of truth)")
    if s0_gridmix.RESEARCH_BOOTSTRAP_SEEDS is not contracts.RESEARCH_BOOTSTRAP_SEEDS:
        raise AssertionError(
            "itsf.s0.gridmix.RESEARCH_BOOTSTRAP_SEEDS is not the SAME "
            "object as contracts.RESEARCH_BOOTSTRAP_SEEDS — IR DR-02 "
            "single-source mutation guard tripped")

    # LEGACY path: `DEFAULT_SOURCE_CONTEXT` is read from the module namespace
    # HERE, at call time, so `monkeypatch.setattr(handoff,
    # "DEFAULT_SOURCE_CONTEXT", ...)` still reaches this builder unchanged.
    src = (DEFAULT_SOURCE_CONTEXT if methods is None
           else source_context_for_methods(methods))
    artifact = dict(rebuild_seed_manifest(src))
    artifact["formal_sealable"] = False
    problems = _guarded(_seed_manifest_problems, "seed_manifest", artifact,
                        src)
    defects = [pr for pr in problems
               if pr.code not in _BUILDER_TOLERATED_CODES]
    if defects:                              # pragma: no cover - unreachable
        raise ValueError("; ".join(pr.text for pr in defects))
    artifact["formal_sealable"] = not problems
    return artifact


# ===========================================================================
# E6d — build_handoff_manifest
# ===========================================================================

def build_handoff_manifest(files: Mapping[str, str]) -> dict[str, object]:
    """name -> {sha256, bytes, line_count (.jsonl only)} manifest of the
    files being handed off to MC. Each file is read exactly once, streamed
    through the hash so a large .jsonl handoff never needs two full passes.

    `line_count` counts LINES, not `\\n` bytes: for a well-formed JSONL body
    (every line, including the last, ends with `\\n`) those are the same
    number, but a body with NO trailing newline has one more line than it
    has `\\n` bytes (the final, unterminated line still counts), and a
    completely empty body has zero lines even though "ends with `\\n`" is
    vacuously false for it. Both edges are pinned: empty body -> 0; N lines
    with no trailing newline -> N.
    """
    manifest: dict[str, object] = {}
    for name, path in files.items():
        digest = hashlib.sha256()
        n_bytes = 0
        n_newlines = 0
        last_byte = b""
        is_jsonl = str(path).endswith(".jsonl")
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                digest.update(chunk)
                n_bytes += len(chunk)
                if is_jsonl:
                    n_newlines += chunk.count(b"\n")
                    last_byte = chunk[-1:]
        entry: dict[str, object] = {"sha256": digest.hexdigest(),
                                    "bytes": n_bytes}
        if is_jsonl:
            if n_bytes == 0:
                n_lines = 0
            elif last_byte == b"\n":
                n_lines = n_newlines
            else:
                n_lines = n_newlines + 1        # trailing unterminated line
            entry["line_count"] = n_lines
        manifest[name] = entry
    return {"schema_version": SCHEMA_VERSION, "files": manifest}


# ===========================================================================
# per-artifact-TYPE schema recognition
# ===========================================================================
# Distinguishing top-level keys for each of the three real builder shapes
# (`build_day_strata` / `build_grid_samples` / `build_seed_manifest` — read
# directly off those functions' own `return {...}` literals above, never
# retyped as a second, driftable copy). A bare shell like
# `{"formal_sealable": True}` matches NONE of these marker sets and is
# therefore UNRECOGNIZED — the "bare shell" refusal case falls out of type
# recognition itself rather than needing its own special-cased branch.
TYPE_DAY_STRATA = "day_strata"
TYPE_GRID_SAMPLES = "grid_samples"
TYPE_SEED_MANIFEST = "seed_manifest"

_TYPE_MARKER_KEYS: dict[str, frozenset[str]] = {
    TYPE_DAY_STRATA: frozenset({"days", "ordering"}),
    TYPE_GRID_SAMPLES: frozenset({"cells", "replay", "replay_status"}),
    TYPE_SEED_MANIFEST: frozenset({"research_bootstrap_seeds", "stream_tags",
                                   "quoted_seed_convention",
                                   "engineering_seed_note"}),
}


def _recognize_artifact_type(artifact: object) -> "str | None":
    """Which of the three real handoff shapes `artifact` LOOKS LIKE, by
    top-level key overlap with `_TYPE_MARKER_KEYS` — or `None` when it
    matches none (or ties between two), which the caller treats as an
    unrecognized/unadmittable schema regardless of any flag it carries."""
    if not isinstance(artifact, Mapping):
        return None
    try:
        keys = {k for k in artifact if _is_strict_str(k)}
    except Exception:                       # pragma: no cover - paranoia
        return None
    scores = {t: len(keys & markers)
              for t, markers in _TYPE_MARKER_KEYS.items()}
    best = max(scores.values())
    if best == 0:
        return None
    winners = [t for t, s in scores.items() if s == best]
    if len(winners) != 1:
        return None
    return winners[0]


# ===========================================================================
# cross-artifact conservation (bundle level)
# ===========================================================================

def _day_strata_class_index(day_strata: object, theta_key: str,
                            ) -> "tuple[set[str], set[str], set[str]]":
    """(TP dates, FP dates, all dates) that DAY_STRATA declares for
    `theta_key`. Tolerant of a malformed artifact — that artifact carries its
    own refusal already; this is only the preimage a grid is checked
    against."""
    tp: set[str] = set()
    fp: set[str] = set()
    every: set[str] = set()
    if not isinstance(day_strata, Mapping):
        return tp, fp, every
    days = day_strata.get("days")
    if not isinstance(days, Mapping):
        return tp, fp, every
    for date, row in _sorted_items(days):
        if not _is_strict_str(date):
            continue
        every.add(date)
        if not isinstance(row, Mapping):
            continue
        classes = row.get("tp_fp_class")
        if not isinstance(classes, Mapping):
            continue
        value = classes.get(theta_key)
        if _is_strict_str(value):
            if value == "TP":
                tp.add(date)
            elif value == "FP":
                fp.add(date)
    return tp, fp, every


def _manifest_seed_list(manifest: object) -> "list[int] | None":
    """The manifest's OWN declared seed list, or `None` when it is not a
    cleanly strict-int sequence (in which case the manifest already carries
    its own defect and there is nothing usable to cross-check against)."""
    if not isinstance(manifest, Mapping):
        return None
    raw = manifest.get("research_bootstrap_seeds")
    if (isinstance(raw, Sequence) and not isinstance(raw, (str, bytes))
            and all(_is_strict_int(s) for s in raw)):
        return list(raw)
    return None


def _grid_cross_problems(grid: Mapping, day_strata: "Mapping | None",
                         seed_manifest: "Mapping | None",
                         source: SourceContext) -> list[_Problem]:
    """The cross-artifact conservation checks that run whenever the
    dependency is PRESENT (matrix item 2d): grid seeds vs the manifest's own
    seeds, grid dates vs DAY_STRATA membership and per-theta class, and the
    frozen App-A target arithmetic recomputed against DAY_STRATA-derived pool
    sizes."""
    problems: list[_Problem] = []

    if seed_manifest is not None:
        manifest_seeds = _manifest_seed_list(seed_manifest)
        cells = grid.get("cells")
        if manifest_seeds is not None and isinstance(cells, Mapping):
            want = set(manifest_seeds)
            for cell_key, cell in _sorted_items(cells):
                if not isinstance(cell, Mapping):
                    continue
                if cell.get("infeasible_by_sample") is True:
                    continue
                per_seed = cell.get("per_seed")
                if not isinstance(per_seed, Mapping):
                    continue
                got = {s for s in per_seed if _is_strict_int(s)}
                if len(got) != len(list(per_seed)):
                    continue                # non-strict-int already refused
                if got != want:
                    problems.append(_p(
                        "CROSS",
                        f"grid_samples.cells[{cell_key!r}].per_seed keys "
                        f"{sorted(got)} != the supplied SEED_MANIFEST "
                        f"artifact's research_bootstrap_seeds "
                        f"{sorted(want)} — per-cell cross-check against the "
                        "seed manifest failed"))

    if day_strata is None:
        return problems

    run_meta = grid.get("run_meta")
    theta = run_meta.get("theta") if isinstance(run_meta, Mapping) else None
    if not _is_strict_float(theta) or theta not in source.thetas:
        problems.append(_p(
            "CROSS",
            "grid_samples.run_meta.theta is not a frozen theta, so the "
            "per-theta DAY_STRATA cross-check cannot run — fail closed "
            "rather than silently skip it"))
        return problems
    theta_key = s0_study.theta_key(theta)
    tp_pool, fp_pool, every = _day_strata_class_index(day_strata, theta_key)
    n_tp_available, n_fp_available = len(tp_pool), len(fp_pool)

    cells = grid.get("cells")
    if not isinstance(cells, Mapping):
        return problems
    for cell_key, cell in _sorted_items(cells):
        label = f"grid_samples.cells[{cell_key!r}]"
        if not isinstance(cell, Mapping):
            continue
        q_mil, r_mil = cell.get("q_mil"), cell.get("r_mil")
        targets_ok = _is_strict_int(q_mil) and _is_strict_int(r_mil)
        expected_n_tp = expected_n_fp = None
        if targets_ok and q_mil in source.q_grid_millis and (
                r_mil in source.r_grid_millis):
            expected_n_tp = s0_gridmix.floor_n_tp(r_mil, n_tp_available)
            expected_n_fp = s0_gridmix.n_fp_for(expected_n_tp, q_mil)
            expected_infeasible = expected_n_fp > n_fp_available
            if cell.get("infeasible_by_sample") is not expected_infeasible:
                problems.append(_p(
                    "CROSS",
                    f"{label}.infeasible_by_sample "
                    f"{cell.get('infeasible_by_sample')!r} != the predicate "
                    f"RECOMPUTED from DAY_STRATA-derived pool sizes "
                    f"(n_fp_target {expected_n_fp} > n_fp_available "
                    f"{n_fp_available} is {expected_infeasible})"))
        if cell.get("infeasible_by_sample") is True:
            continue
        per_seed = cell.get("per_seed")
        if not isinstance(per_seed, Mapping):
            continue
        for seed, block in _sorted_items(per_seed):
            block_label = f"{label}.per_seed[{seed!r}]"
            if not isinstance(block, Mapping):
                continue
            tp_dates = _strict_date_list(block.get("tp_dates"))
            fp_dates = _strict_date_list(block.get("fp_dates"))
            if tp_dates is None or fp_dates is None:
                continue
            absent = sorted((set(tp_dates) | set(fp_dates)) - every)
            if absent:
                problems.append(_p(
                    "CROSS",
                    f"{block_label}: {len(absent)} selected date(s) are "
                    f"ABSENT from the co-supplied DAY_STRATA, e.g. "
                    f"{absent[:5]}"))
            mis_tp = sorted(set(tp_dates) - tp_pool - _absent_set(absent))
            if mis_tp:
                problems.append(_p(
                    "CROSS",
                    f"{block_label}: {len(mis_tp)} date(s) are marked TP for "
                    f"{theta_key} but DAY_STRATA does not class them TP for "
                    f"that SAME theta, e.g. {mis_tp[:5]} (a swapped TP/FP "
                    "marker pair is caught here)"))
            mis_fp = sorted(set(fp_dates) - fp_pool - _absent_set(absent))
            if mis_fp:
                problems.append(_p(
                    "CROSS",
                    f"{block_label}: {len(mis_fp)} date(s) are marked FP for "
                    f"{theta_key} but DAY_STRATA does not class them FP for "
                    f"that SAME theta, e.g. {mis_fp[:5]}"))
            if expected_n_tp is not None:
                if len(tp_dates) != expected_n_tp:
                    problems.append(_p(
                        "CROSS",
                        f"{block_label}: {len(tp_dates)} TP date(s) != "
                        f"gridmix.floor_n_tp(r_mil={r_mil}, "
                        f"n_tp_available={n_tp_available}) = "
                        f"{expected_n_tp}, recomputed from the DAY_STRATA "
                        "pool rather than from the grid's own claim"))
                if len(fp_dates) != expected_n_fp:
                    problems.append(_p(
                        "CROSS",
                        f"{block_label}: {len(fp_dates)} FP date(s) != "
                        f"gridmix.n_fp_for(n_tp={expected_n_tp}, "
                        f"q_mil={q_mil}) = {expected_n_fp}, recomputed from "
                        "the DAY_STRATA pool"))
            if "realized_recall" in block and n_tp_available:
                expected_recall = len(tp_dates) / n_tp_available
                value = block["realized_recall"]
                if not _is_strict_float(value) or value != expected_recall:
                    problems.append(_p(
                        "CROSS",
                        f"{block_label}.realized_recall {value!r} != "
                        "n_tp_actual / n_tp_available recomputed from the "
                        f"DAY_STRATA pool ({expected_recall!r}) — "
                        "n_tp_available is NOT carried on GRID_SAMPLES, so "
                        "this leaf is unverifiable without the dependency"))
    return problems


def _absent_set(absent: Sequence[str]) -> set:
    """Small helper so a date already reported as ABSENT from DAY_STRATA is
    not ALSO reported as mis-classified (one defect, one message)."""
    return set(absent)


# ===========================================================================
# formal_seal_admission — BUNDLE-LEVEL ATOMIC admission
# ===========================================================================

def formal_seal_admission(artifacts: Mapping[str, Mapping], *,
                          source: "SourceContext | None" = None,
                          ) -> list[str]:
    """The CONSUMER `formal_sealable` lacked (M6.1.1 audit finding (c)) — a
    per-artifact-TYPE SEMANTIC validator that RECOMPUTES sealability from
    CONTENT plus an INDEPENDENT `SourceContext`, and never trusts the
    artifact's own `formal_sealable` flag.

    Returns a (sorted, deterministic) list of problem descriptions, at most
    one per artifact that is NOT admissible; an empty list means every
    supplied artifact is admissible. Every string begins with `"{name}: "` —
    the attribution format `scripts/s0_real_run._partition_admission` parses.

    This function does not itself hold or mutate any "sealed set" — it is
    the GATE the main agent's Stage-E renderer must call before admitting an
    artifact: a name that appears in this function's non-empty return value
    must NOT be added to whatever the renderer treats as sealed.

    Parameters
    ----------
    artifacts
        artifact name -> the artifact's own dict (e.g. the outputs of
        `build_day_strata` / `build_grid_samples` / `build_seed_manifest`).
    source
        keyword-only; the INDEPENDENT source facts expected content is
        rebuilt from. Defaults to `DEFAULT_SOURCE_CONTEXT` — the LEGACY
        context: every frozen constant bound, no dataset facts, no ruling on
        any axis, so only UNRESOLVED markers are admissible there and nothing
        carrying one is sealable. A caller holding the ruled method set
        passes `source=source_context_for_methods(methods)`; the ruling is
        then visible in the context a reviewer reads, never in the bytes
        being sealed.

    BUNDLE SEMANTICS (M6.1.4 item 2 — admission is ATOMIC over the bundle)
    ---------------------------------------------------------------------
    * a GRID_SAMPLES artifact DEPENDS ON exactly ONE valid DAY_STRATA and
      exactly ONE valid SEED_MANIFEST supplied in the SAME call;
    * if a dependency is ABSENT, DUPLICATED or INVALID, every dependent
      artifact is withheld too, with the dependency chain named in its own
      problem string. A lone GRID_SAMPLES therefore can never bypass the
      graph — "nothing to cross-check against" is a refusal, not a pass;
    * duplicate DAY_STRATA or duplicate SEED_MANIFEST artifacts in one
      bundle: ALL of them are withheld (there is no rule for choosing);
    * two GRID_SAMPLES artifacts claiming the same (theta, engine, scenario)
      triple: all colliding artifacts are withheld;
    * the cross-artifact conservation checks (grid seeds vs manifest, grid
      dates vs DAY_STRATA membership and per-theta class, App-A target
      arithmetic vs DAY_STRATA-derived pool sizes) run whenever the
      dependency is present — including when it is present but invalid — and
      are part of the same atomic verdict.

    Admission rule, per artifact
    -----------------------------
    1. `"formal_sealable"` absent entirely (or the artifact is not a mapping)
       -> a problem; a missing flag is NEVER a silent pass.
    2. The artifact's TYPE is recognized from its own top-level key shape. A
       shape matching none of the three real schemas — including a bare
       `{"formal_sealable": True}` shell — is UNRECOGNIZED and is its own
       content problem, independent of the flag.
    3. The recognized type's full content is validated by its semantic
       checker, then the bundle-level dependency and cross-artifact problems
       are added. This yields a RECOMPUTED verdict (sealable iff zero
       problems) compared against the artifact's OWN flag:
       * flag `True` + recomputed sealable -> admitted, no problem;
       * flag `True` + not sealable -> a CONTRADICTION problem naming every
         problem found;
       * flag anything other than `True` -> refused, naming every problem
         found (or a generic refusal when recomputation independently found
         none).
    """
    if not isinstance(artifacts, Mapping):
        raise TypeError(
            "formal_seal_admission takes a Mapping of artifact name -> "
            f"artifact, got {type(artifacts).__name__}")

    names = [n for n, _ in _sorted_items(artifacts)]
    # The source context is resolved, type-pinned and RE-VALIDATED INSIDE the
    # guarded region (blind-audit A9): a hostile read while resolving it must
    # fold into a refusal string, not escape this function as an exception.
    # Every artifact in the bundle is withheld — an untrustworthy anchor
    # invalidates every recomputation measured against it, not just one.
    try:
        src = _resolve_source(source)
    except Exception as exc:                # noqa: BLE001 - deliberate net
        if not names:
            # nothing to attribute a "{name}: " problem to, and the renderer
            # fails closed on an unattributable string — so a broken config
            # with an empty bundle raises rather than returning a silent [].
            raise
        reason = _safe_reason(exc)
        return sorted(f"{name}: source context invalid — fail closed: "
                      f"{reason}" for name in names)
    recognized: dict[object, "str | None"] = {}
    own: dict[object, list[_Problem]] = {}
    flagless: set[object] = set()

    for name in names:
        artifact = artifacts[name]
        if not isinstance(artifact, Mapping) or (
                "formal_sealable" not in artifact):
            flagless.add(name)
            recognized[name] = _recognize_artifact_type(artifact)
            own[name] = []
            continue
        artifact_type = _recognize_artifact_type(artifact)
        recognized[name] = artifact_type
        if artifact_type == TYPE_DAY_STRATA:
            own[name] = _guarded(_day_strata_problems, TYPE_DAY_STRATA,
                                 artifact, src)
        elif artifact_type == TYPE_GRID_SAMPLES:
            own[name] = _guarded(_grid_samples_problems, TYPE_GRID_SAMPLES,
                                 artifact, src)
        elif artifact_type == TYPE_SEED_MANIFEST:
            own[name] = _guarded(_seed_manifest_problems, TYPE_SEED_MANIFEST,
                                 artifact, src)
        else:
            own[name] = [_p(
                "SCHEMA",
                "does not match any recognized artifact schema (day_strata "
                "/ grid_samples / seed_manifest) — a formal_sealable flag "
                "with no matching content shape is never, on its own, "
                "evidence of sealability")]

    strata_names = [n for n in names if recognized[n] == TYPE_DAY_STRATA]
    manifest_names = [n for n in names if recognized[n] == TYPE_SEED_MANIFEST]
    grid_names = [n for n in names if recognized[n] == TYPE_GRID_SAMPLES]

    bundle: dict[object, list[_Problem]] = {n: [] for n in names}

    # --- singleton dependencies must not be duplicated ------------------
    for dep_label, dep_names in (("DAY_STRATA", strata_names),
                                 ("SEED_MANIFEST", manifest_names)):
        if len(dep_names) > 1:
            listed = sorted(repr(n) for n in dep_names)
            for n in dep_names:
                bundle[n].append(_p(
                    "DEPENDENCY",
                    f"{len(dep_names)} {dep_label} artifacts were supplied "
                    f"in ONE admission bundle ({listed}) — a bundle carries "
                    f"at most ONE {dep_label}; there is no rule for choosing "
                    "between them, so ALL of them are withheld"))

    # --- one grid per (theta, engine, scenario) -------------------------
    triples: dict[tuple, list[object]] = {}
    for n in grid_names:
        run_meta = artifacts[n].get("run_meta")
        if isinstance(run_meta, Mapping):
            key = (repr(run_meta.get("theta")), repr(run_meta.get("engine")),
                   repr(run_meta.get("scenario")))
            triples.setdefault(key, []).append(n)
    for key, owners in sorted(triples.items()):
        if len(owners) > 1:
            bundle_note = sorted(repr(o) for o in owners)
            for n in owners:
                bundle[n].append(_p(
                    "DEPENDENCY",
                    f"DUPLICATE GRID_SAMPLES: {len(owners)} artifacts "
                    f"({bundle_note}) claim the same (theta, engine, "
                    f"scenario) = {key} — the theta x engine x scenario "
                    "artifact set must be duplicate-free; all colliding "
                    "artifacts are withheld"))

    if src.require_complete_grid_matrix and grid_names:
        expected_triples = {(repr(float(t)), repr(e), repr(s))
                            for t in src.thetas for e in src.engines
                            for s in src.scenarios}
        missing_triples = sorted(expected_triples - set(triples))
        if missing_triples:
            for n in grid_names:
                bundle[n].append(_p(
                    "DEPENDENCY",
                    "the source context requires the COMPLETE theta x engine "
                    f"x scenario GRID_SAMPLES set ({len(expected_triples)} "
                    f"artifacts); {len(missing_triples)} are missing, e.g. "
                    f"{missing_triples[:3]} — an incomplete bundle is "
                    "withheld in full"))

    # --- resolve each grid's dependencies -------------------------------
    def _is_valid(n: object) -> bool:
        return (n not in flagless and not own[n] and not bundle[n]
                and artifacts[n].get("formal_sealable") is True)

    for n in grid_names:
        for dep_label, dep_names in (("DAY_STRATA", strata_names),
                                     ("SEED_MANIFEST", manifest_names)):
            if not dep_names:
                bundle[n].append(_p(
                    "DEPENDENCY",
                    f"dependency {dep_label} is ABSENT from this admission "
                    "bundle — a GRID_SAMPLES artifact depends on exactly ONE "
                    f"valid {dep_label} co-supplied in the SAME call "
                    f"(dependency chain: GRID_SAMPLES -> {dep_label}); a "
                    "lone grid submission can never bypass the dependency "
                    "graph, because there is nothing to conserve against"))
            elif len(dep_names) > 1:
                bundle[n].append(_p(
                    "DEPENDENCY",
                    f"dependency {dep_label} is DUPLICATED in this bundle "
                    f"({sorted(repr(d) for d in dep_names)}) — dependency "
                    f"chain: GRID_SAMPLES -> {dep_label}; the dependent "
                    "artifact is withheld with its dependency"))
            elif not _is_valid(dep_names[0]):
                bundle[n].append(_p(
                    "DEPENDENCY",
                    f"dependency {dep_label} {dep_names[0]!r} is INVALID or "
                    "WITHHELD (it is itself refused admission) — dependency "
                    f"chain: GRID_SAMPLES -> {dep_label} "
                    f"{dep_names[0]!r}; a dependent artifact is never sealed "
                    "on top of an unsealed dependency, however sealable it "
                    "claims to be"))
        day_strata = artifacts[strata_names[0]] if len(
            strata_names) == 1 else None
        manifest = artifacts[manifest_names[0]] if len(
            manifest_names) == 1 else None
        if (day_strata is not None or manifest is not None) and isinstance(
                artifacts[n], Mapping):
            bundle[n].extend(_guarded(
                lambda a, s: _grid_cross_problems(a, day_strata, manifest, s),
                TYPE_GRID_SAMPLES, artifacts[n], src))

    # --- render ---------------------------------------------------------
    problems: list[str] = []
    for name in names:
        if name in flagless:
            problems.append(
                f"{name}: missing the 'formal_sealable' flag entirely — an "
                "artifact with no flag at all cannot be admitted to the "
                "sealed set (a dead/absent flag is never read as a pass)")
            continue
        content_problems = [pr.text for pr in own[name] + bundle[name]]
        sealable = artifacts[name]["formal_sealable"]
        if sealable is True:
            if content_problems:
                joined = "; ".join(content_problems)
                problems.append(
                    f"{name}: formal_sealable=True but the content, "
                    f"recomputed independently, is NOT sealable — "
                    f"CONTRADICTION: {joined}")
        elif content_problems:
            joined = "; ".join(content_problems)
            problems.append(
                f"{name}: formal_sealable={sealable!r} (not True) — "
                f"blocked by: {joined} — refused admission to the "
                "sealed set")
        else:
            problems.append(
                f"{name}: formal_sealable={sealable!r} (not True) — "
                "refused admission to the sealed set (recomputing the "
                "content independently found no defect either, but a "
                "flag that is not exactly True is never read as a "
                "pass)")
    return sorted(problems)


# ===========================================================================
# E6e — verify_handoff_conservation
# ===========================================================================

# frozen: the record matrix's keys must be EXACTLY {ENGINES} x {SCENARIOS}
# (M6.1.1 S2 item 1, Codex finding (a)); built once, from the single-sourced
# ENGINES/SCENARIOS constants above, never re-typed at each check site.
_REQUIRED_ENGINE_SCENARIO_CELLS = tuple(
    (engine, scenario) for engine in ENGINES for scenario in SCENARIOS)


def _theta_key_of(value: object) -> "str | None":
    """`study.theta_key(value)` when `value` is a STRICT numeric theta, else
    None. No float()/int() coercion: a str/bool theta has no key, it has a
    defect."""
    if _is_strict_float(value) or _is_strict_int(value):
        return s0_study.theta_key(value)
    return None


def _check_theta_axis_lock(day_strata: Mapping[str, object],
                           grid_samples: Mapping[str, object]) -> list[str]:
    """THETA AXIS LOCK (M6.1.1 S2 item 2): every `tp_fp_class` key actually
    present in `day_strata` and `grid_samples["run_meta"]["theta"]` (when
    supplied) must lie within the frozen `FROZEN_THETAS` pair. Unconditional
    — independent of whether a `seed_manifest` is supplied to
    `verify_handoff_conservation` — because a rogue theta axis value is a
    defect in its own right."""
    problems: list[str] = []
    days = day_strata.get("days", {}) if isinstance(day_strata,
                                                    Mapping) else {}
    if isinstance(days, Mapping):
        for date, row in _sorted_items(days):
            classes = row.get("tp_fp_class", {}) if isinstance(
                row, Mapping) else {}
            if not isinstance(classes, Mapping):
                continue
            rogue = sorted(repr(k) for k in classes
                           if not (_is_strict_str(k)
                                   and k in _FROZEN_THETA_KEYS))
            for key in rogue:
                problems.append(
                    f"{date}: day_strata tp_fp_class key {key} is not one of "
                    f"the frozen theta pair {sorted(_FROZEN_THETA_KEYS)} "
                    "(study.FROZEN_THETAS) — theta AXIS LOCK violated")
    run_meta = grid_samples.get("run_meta") if isinstance(
        grid_samples, Mapping) else None
    if isinstance(run_meta, Mapping) and "theta" in run_meta:
        key = _theta_key_of(run_meta["theta"])
        if key is None or key not in _FROZEN_THETA_KEYS:
            problems.append(
                f"grid_samples run_meta theta {run_meta['theta']!r} (key "
                f"{key!r}) is not one of the frozen theta pair "
                f"{sorted(_FROZEN_THETA_KEYS)} (study.FROZEN_THETAS) — theta "
                "AXIS LOCK violated")
    return problems


def _check_record_matrix_shape(
        record_dates_by_engine_scenario: Mapping[
            str, Mapping[str, Sequence[str]]]) -> list[str]:
    """The record matrix's KEYS must be EXACTLY the frozen {ENGINES} x
    {SCENARIOS} 8 cells (M6.1.1 S2 item 1, Codex finding (a): "an empty or
    partial record matrix passes" today). An empty matrix, a missing cell
    and an extra/renamed cell are DISTINCT problems, each named explicitly —
    never folded into one generic "matrix is wrong" message."""
    if not record_dates_by_engine_scenario:
        return [
            "record matrix is EMPTY: the frozen matrix requires exactly "
            f"the {len(_REQUIRED_ENGINE_SCENARIO_CELLS)} cells "
            f"{_REQUIRED_ENGINE_SCENARIO_CELLS} ({ENGINES} x {SCENARIOS}) "
            "and none were supplied"]
    problems: list[str] = []
    actual_cells = {(engine, scenario)
                    for engine, scenarios in
                    record_dates_by_engine_scenario.items()
                    for scenario in scenarios}
    required_cells = set(_REQUIRED_ENGINE_SCENARIO_CELLS)
    for engine, scenario in sorted(required_cells - actual_cells):
        problems.append(
            f"record matrix missing required cell {engine}/{scenario} "
            f"(the frozen matrix is {ENGINES} x {SCENARIOS})")
    for engine, scenario in sorted(actual_cells - required_cells):
        problems.append(
            f"record matrix has an unrecognised cell {engine}/{scenario} — "
            f"not one of the frozen {ENGINES} x {SCENARIOS} (an extra or "
            "renamed engine/scenario is not accepted)")
    return problems


def _check_seed_axis_lock(grid_samples: Mapping[str, object],
                          seed_manifest: Mapping[str, object]) -> list[str]:
    """SEED_MANIFEST cross-verification (M6.1.1 S2 item 2): the seeds
    `grid_samples`' per_seed maps actually carry, `seed_manifest`'s own
    recorded research seeds, and the frozen seed tuple must ALL agree
    exactly. Only invoked when the caller supplies a manifest."""
    problems: list[str] = []
    frozen_seeds = set(FROZEN_SEEDS)
    observed_seeds: set = set()
    cells = grid_samples.get("cells", {}) if isinstance(grid_samples,
                                                        Mapping) else {}
    if isinstance(cells, Mapping):
        for cell in cells.values():
            if isinstance(cell, Mapping) and isinstance(
                    cell.get("per_seed"), Mapping):
                observed_seeds.update(cell["per_seed"].keys())
    raw_manifest_seeds = seed_manifest.get(
        "research_bootstrap_seeds", ()) if isinstance(seed_manifest,
                                                      Mapping) else ()
    if isinstance(raw_manifest_seeds, (str, bytes)) or not isinstance(
            raw_manifest_seeds, Sequence):
        raw_manifest_seeds = ()
    # NO int() coercion: a non-strict-int seed is its own defect, never
    # normalised into the seed it merely resembles.
    non_strict = sorted(repr(s) for s in raw_manifest_seeds
                        if not _is_strict_int(s))
    if non_strict:
        problems.append(
            f"seed_manifest['research_bootstrap_seeds'] has non-strict-int "
            f"entrie(s) {non_strict} — seed AXIS LOCK violated (bool/float/"
            "numeric-string seeds are refused, never coerced with int())")
    manifest_seeds = {s for s in raw_manifest_seeds if _is_strict_int(s)}
    if manifest_seeds != frozen_seeds:
        problems.append(
            f"seed_manifest['research_bootstrap_seeds'] "
            f"{sorted(manifest_seeds)} != the frozen seed tuple "
            f"{sorted(frozen_seeds)} (contracts.RESEARCH_BOOTSTRAP_SEEDS) — "
            "seed AXIS LOCK violated")
    if observed_seeds and observed_seeds != frozen_seeds:
        problems.append(
            f"grid_samples per_seed keys "
            f"{sorted(observed_seeds, key=repr)} != the "
            f"frozen seed tuple {sorted(frozen_seeds)} (contracts."
            "RESEARCH_BOOTSTRAP_SEEDS) — seed AXIS LOCK violated")
    if observed_seeds and manifest_seeds and observed_seeds != manifest_seeds:
        problems.append(
            f"grid_samples per_seed keys "
            f"{sorted(observed_seeds, key=repr)} != "
            f"seed_manifest['research_bootstrap_seeds'] "
            f"{sorted(manifest_seeds)} — the grid samples and the seed "
            "manifest disagree about which seeds were run")
    return problems


def verify_handoff_conservation(
        day_strata: Mapping[str, object], grid_samples: Mapping[str, object],
        record_dates_by_engine_scenario: Mapping[str, Mapping[str, Sequence[str]]],
        seed_manifest: Mapping[str, object] | None = None,
        ) -> list[str]:
    """Cross-check the three handoff artifacts against each other. Returns a
    (sorted, deterministic) list of problem descriptions — empty means
    conservation holds.

    Checks
    ------
    0. THETA AXIS LOCK (unconditional — see `_check_theta_axis_lock`).
    1. every date appearing in a grid sample (any cell, any seed, TP or FP)
       is present in `day_strata`;
    1b. PER-THETA marker agreement: `grid_samples["run_meta"]["theta"]`
       names which theta this grid_samples bundle is FOR; every date a grid
       sample marks a tp-marker must be classed "TP" in day_strata for THAT
       theta, and every fp-marker date "FP" for that SAME theta.
    2. every date appearing in `record_dates_by_engine_scenario` is present
       in `day_strata`;
    3. RECORD MATRIX SHAPE: the matrix's keys must be EXACTLY the frozen
       {ENGINES} x {SCENARIOS} 8 cells.
    4. BIDIRECTIONAL TP/FP <-> record coverage, checked against the FROZEN 8
       cells rather than merely whatever appears in the caller's matrix.
    5. SEED_MANIFEST cross-verification (only when supplied).
    """
    problems: list[str] = []
    days = day_strata.get("days", {}) if isinstance(day_strata,
                                                    Mapping) else {}
    if not isinstance(days, Mapping):
        days = {}

    problems.extend(_check_theta_axis_lock(day_strata, grid_samples))

    cells = grid_samples.get("cells", {}) if isinstance(grid_samples,
                                                        Mapping) else {}
    if not isinstance(cells, Mapping):
        cells = {}
    grid_dates: set = set()
    for cell in cells.values():
        per_seed = cell.get("per_seed", {}) if isinstance(cell,
                                                          Mapping) else {}
        if not isinstance(per_seed, Mapping):
            continue
        for block in per_seed.values():
            if not isinstance(block, Mapping):
                continue
            grid_dates.update(block.get("tp_dates", ()) or ())
            grid_dates.update(block.get("fp_dates", ()) or ())
    for date in sorted(grid_dates, key=repr):
        if date not in days:
            problems.append(
                f"{date}: appears in a grid sample but is absent from "
                "day_strata")

    if grid_dates:
        run_meta = grid_samples.get("run_meta") if isinstance(
            grid_samples, Mapping) else None
        if not isinstance(run_meta, Mapping) or "theta" not in run_meta:
            raise ValueError(
                "grid_samples['run_meta']['theta'] is required to check "
                "PER-THETA TP/FP conservation (build_grid_samples always "
                "attaches it); a grid_samples without it cannot be "
                "cross-checked against day_strata's per-theta tp_fp_class "
                "— fail closed rather than silently skip the check")
        theta_key = _theta_key_of(run_meta["theta"])
        if theta_key is None:
            raise ValueError(
                f"grid_samples['run_meta']['theta'] {run_meta['theta']!r} is "
                "not a strict int/float, so no theta key can be computed "
                "from it — fail closed rather than coerce it into one")
        for cell in cells.values():
            per_seed = cell.get("per_seed", {}) if isinstance(
                cell, Mapping) else {}
            if not isinstance(per_seed, Mapping):
                continue
            for block in per_seed.values():
                if not isinstance(block, Mapping):
                    continue
                for date in block.get("tp_dates", ()) or ():
                    row = days.get(date)
                    if row is None or not isinstance(row, Mapping):
                        continue          # already reported above (check 1)
                    classes = row.get("tp_fp_class", {})
                    actual = classes.get(theta_key) if isinstance(
                        classes, Mapping) else None
                    if actual != "TP":
                        problems.append(
                            f"{date}: grid sample marks it a TP date for "
                            f"{theta_key} but day_strata classifies it "
                            f"{actual!r} for {theta_key}")
                for date in block.get("fp_dates", ()) or ():
                    row = days.get(date)
                    if row is None or not isinstance(row, Mapping):
                        continue
                    classes = row.get("tp_fp_class", {})
                    actual = classes.get(theta_key) if isinstance(
                        classes, Mapping) else None
                    if actual != "FP":
                        problems.append(
                            f"{date}: grid sample marks it an FP date for "
                            f"{theta_key} but day_strata classifies it "
                            f"{actual!r} for {theta_key}")

    record_dates: set = set()
    for engine, scenarios in record_dates_by_engine_scenario.items():
        for scenario, dates in scenarios.items():
            record_dates.update(dates)
    for date in sorted(record_dates, key=repr):
        if date not in days:
            problems.append(
                f"{date}: has a record but is absent from day_strata")

    problems.extend(
        _check_record_matrix_shape(record_dates_by_engine_scenario))

    classified_dates = set()
    for date, row in _sorted_items(days):
        classes = row.get("tp_fp_class", {}) if isinstance(row,
                                                           Mapping) else {}
        if isinstance(classes, Mapping) and any(
                v in ("TP", "FP") for v in classes.values()):
            classified_dates.add(date)

    # Checked against the FROZEN 8 cells, never the caller's own keys (see
    # check 4 docstring above / Codex finding (a)).
    for date in sorted(classified_dates, key=repr):
        for engine, scenario in _REQUIRED_ENGINE_SCENARIO_CELLS:
            engine_dates = record_dates_by_engine_scenario.get(engine, {})
            scenario_dates = set(engine_dates.get(scenario, ()))
            if date not in scenario_dates:
                problems.append(
                    f"{date}: TP/FP-classed but missing a record for "
                    f"{engine}/{scenario}")

    for engine, scenarios in record_dates_by_engine_scenario.items():
        for scenario, dates in scenarios.items():
            for date in sorted(dates, key=repr):
                if date in days and date not in classified_dates:
                    problems.append(
                        f"{date}: has a record for {engine}/{scenario} but "
                        "is not TP/FP-classed in day_strata")

    if seed_manifest is not None:
        problems.extend(_check_seed_axis_lock(grid_samples, seed_manifest))

    return sorted(set(problems))
