"""Shared typed contracts for the ITSF S0/MC engine.

MAIN-AGENT OWNED. Subagents treat this file as READ-ONLY; interface change
requests go into their `unresolved` report for main-agent adjudication.
Field semantics mirror frozen S0 §10.1 / MC spec — do not reinterpret.
"""
from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from numbers import Real as _Real
from types import MappingProxyType

# --- MNQ instrument constants (CME) ----------------------------------------
MNQ_POINT_VALUE_USD = 2.0      # $2 per index point
MNQ_TICK_POINTS = 0.25
MNQ_TICK_VALUE_USD = 0.5

# Frozen s0_cost_handoff primary (platform_params.execution_costs)
S0_PLATFORM_FEE_RT_USD = 1.74

# IR DR-02 (Aaron 2026-08-01, Codex baseline audit): the ONLY seeds any
# research-path RNG may derive from.  # frozen: S0 §9 (Primary bootstrap
# seeds {7,13,31}), S0 Appendix A step 3, MC_METHOD_SPEC §(b) three master
# seeds. The engineering seed (RunConfig.engineering_seed) must NEVER reach
# a research computation.
RESEARCH_BOOTSTRAP_SEEDS: tuple[int, int, int] = (7, 13, 31)


# --- M6.1.4 (S3): CANONICAL FORM helpers -----------------------------------
# Config equality is the load-bearing gate on the production path
# (`s0_real_run`'s config gateway compares a cached config against a FRESH
# derivation). Equality is only meaningful if both sides are in one canonical
# form, so every numeric injectable is reduced to a plain Python float at
# construction. None of this adopts, ranks or narrows any unruled research
# choice: it is representation only (DR-1 was later ruled 2026-08-10;
# this layer still adopts nothing).

#: The EXACT key set a `_approved_injectables()` source must return. Exact,
#: not minimal: an extra key is a defect, not a harmless addition, because
#: `derive_study_config(**inj)` would either explode or silently ignore it.
INJECTABLE_KEYS: frozenset[str] = frozenset(
    {"spread_scalars", "regime_of", "vol_axis_of"})


def _canonical_scalar(value):
    """`float(value)` for a finite, non-negative REAL number; else ``None``.

    Canonicalization decisions (documented, not ruled):
      * ``bool`` is REFUSED — ``True`` is an ``int`` in Python and would
        silently canonicalize to ``1.0``, turning a flag into a price.
      * numpy scalars (``np.float32``/``np.float64``/``np.int64``/...) are
        ACCEPTED and canonicalized to plain floats: they register as
        ``numbers.Real``. ``np.bool_`` does NOT register as ``numbers.Real``
        and is therefore refused exactly like ``bool``.
      * ``int`` is accepted and widened to ``float`` so that ``(0, 1, 1)``
        and ``(0.0, 1.0, 1.0)`` compare EQUAL after canonicalization.
      * ``str``/``Decimal``/``None``/objects are refused (not ``Real``).
      * NEGATIVE ZERO IS COLLAPSED TO ``+0.0`` (M6.1.4 Phase-E LOW-2).
        ``-0.0`` passes the non-negative test (``-0.0 >= 0.0`` is ``True``)
        and ``-0.0 == 0.0`` is ``True``, so two configs carrying different
        zero signs are canonical-EQUAL while their SEALED BYTES differ:
        ``disclosures.method_conventions.spread_scalars_used`` serializes
        ``-0.0`` and ``0.0`` as different JSON tokens. Equality-based gates
        would pass a pair the seal digest separates. Collapsing the sign bit
        here makes canonical equality and byte identity agree.
    Never raises for any input.
    """
    try:
        if isinstance(value, bool) or not isinstance(value, _Real):
            return None
        out = float(value)
    except Exception:
        return None
    if not math.isfinite(out) or out < 0.0:
        return None
    if out == 0.0:                 # collapses -0.0 (and +0.0) to +0.0
        out = 0.0
    return out


def canonical_spread_scalars(scalars):
    """Canonical ``(median, P90, P95)`` triple of plain floats, or ``None``.

    ``None`` means "not a legal triple" — wrong container, wrong length, a
    non-canonicalizable element, or an out-of-order triple. The ordering
    invariant ``0 <= median <= P90 <= P95`` is a TYPE-level invariant (see
    the proof chain in `StudyConfig.__post_init__`), not an approval of any
    DR-1 reduction rule. Never raises for any input.
    """
    if not isinstance(scalars, tuple):
        return None
    try:
        if len(scalars) != 3:
            return None
        out = []
        for v in scalars:
            f = _canonical_scalar(v)
            if f is None:
                return None
            out.append(f)
    except Exception:
        return None
    m, p90, p95 = out
    if not (0.0 <= m <= p90 <= p95):
        return None
    return (m, p90, p95)


def is_canonical_spread_scalars(scalars) -> bool:
    """True iff `scalars` IS ALREADY EXACTLY what `canonical_spread_scalars`
    would produce for it — REPRESENTATION, not value (M6.1.4-R2, F-1).

    TWO SEPARATE OBLIGATIONS, and the reason this predicate exists.
    `canonical_spread_scalars` answers EQUIVALENCE ("do these carry the same
    values?"); it deliberately CANNOT answer REPRESENTATION ("is this object
    itself in canonical form?"), because `_canonical_scalar` widens ``int``
    to ``float`` precisely so ``(0, 1, 1)`` and ``(0.0, 1.0, 1.0)`` compare
    EQUAL, and collapses ``-0.0`` to ``+0.0``. Both erasures are correct for
    equivalence and fatal for anything that decides INTERCHANGEABILITY on
    values alone: `disclosures.method_conventions.spread_scalars_used`
    serializes the triple verbatim, so ``[0, 1, 1]`` and ``[-0.0, ...]``
    reach the SEALED BYTES while comparing equal to the canonical form.

    ONE RULE, NOT TWO. Only the two properties ``==`` provably cannot see
    are stated here — the exact element TYPE and the ZERO SIGN BIT. Container
    shape, finiteness, non-negativity and the ordering invariant are
    DELEGATED to `canonical_spread_scalars`, so this predicate can never
    drift into a second, differently-worded canonical form.

    NEVER RAISES, and never executes foreign code. Ordering is load-bearing:
    every element is pinned to EXACTLY ``float`` BEFORE the delegated call,
    so no user ``__float__`` / ``__index__`` / ``__eq__`` can run (a ``float``
    SUBCLASS may override ``__eq__``, hence `type(v) is float`, not
    isinstance). Returns a plain ``bool``.
    """
    if type(scalars) is not tuple or len(scalars) != 3:
        return False
    for v in scalars:
        if type(v) is not float:
            return False
        if math.copysign(1.0, v) < 0.0:      # -0.0 (and any negative) refused
            return False
    return canonical_spread_scalars(scalars) == scalars


def _canonical_ticks(ticks):
    """Immutable canonical form of a per-scenario adverse-slippage mapping.

    A `Mapping` becomes a `MappingProxyType` over a shallow copy, so a
    validated config's method values cannot be mutated in place afterwards
    (mutate-after-validate would otherwise only be caught by the NEXT
    revalidation). Anything that is not a Mapping — or a Mapping whose
    iteration raises — is returned UNCHANGED so that
    `ResolvedS0Methods.structural_problems()` can report it as a problem
    rather than this helper raising inside a constructor. Never raises.
    """
    if isinstance(ticks, MappingProxyType):
        return ticks
    if isinstance(ticks, Mapping):
        try:
            return MappingProxyType(dict(ticks))
        except Exception:
            return ticks
    return ticks


def is_canonical_ticks(ticks) -> bool:
    """True iff `ticks` IS the read-only container `_canonical_ticks`
    produces — REPRESENTATION, not value (M6.1.4-R2, F-1).

    WHY VALUE EQUIVALENCE CANNOT ANSWER THIS. A `MappingProxyType` compares
    EQUAL to the plain dict it wraps (that equality is relied on elsewhere,
    see `SpreadCostMethod`), and any normalization to a sorted key/value
    sequence maps both to the same thing. So a MUTABLE mapping and the
    canonical read-only one are indistinguishable by value, while only one of
    them keeps the promise `SpreadCostMethod` makes in its docstring.

    SCOPE OF THE GUARANTEE, stated exactly and not to be widened. True means
    the object exposes NO MUTATION SURFACE OF ITS OWN — ``ticks["Base"] = 9``
    raises ``TypeError``. It does NOT mean the mapping is immutable: a
    mappingproxy is a LIVE VIEW, and whoever holds the wrapped object can
    still mutate it. For a legitimately constructed `SpreadCostMethod` that
    holder cannot exist (`_canonical_ticks` wraps a SHALLOW COPY the caller
    never sees), but for a config assembled by BYPASS the wrapper's author
    keeps the reference. Mutation through such a reference is caught only by
    the config gateway's revalidate-on-every-call invariant — ACROSS calls,
    never within one. It also cannot say what type the wrapped mapping is:
    CPython exposes no API to reach the object behind a mappingproxy.

    Never raises, never iterates, never calls ``keys()``/``items()``: a type
    pin plus the producer's own idempotence. That second conjunct is the
    BINDING — it turns false if `_canonical_ticks` ever stops returning a
    mappingproxy unchanged, so the two cannot drift apart.
    """
    return type(ticks) is MappingProxyType and _canonical_ticks(ticks) is ticks


# --- M6.1.1: structured method sub-items (one dataclass per DR family; no
#     coarse strings hiding several sub-decisions). Every field is set ONLY
#     when Aaron's ruling lands with its IR reference. ----------------------

@dataclass(frozen=True)
class SpreadCostMethod:                    # DR-M6-A-v2 + IR-7
    """M6.1.4 (S3): `adverse_slippage_ticks` is CANONICALIZED at construction
    to a `MappingProxyType` over a shallow copy, so the mapping a validated
    config carries is READ-ONLY (`cfg.methods.spread_cost
    .adverse_slippage_ticks["Base"] = 9` raises `TypeError`). The read access
    pattern is unchanged — `MappingProxyType` is a `collections.abc.Mapping`
    and compares equal to the plain dict it wraps, so equality-based gates and
    `dataclasses.replace()` are unaffected. A NON-Mapping value is left
    untouched so `structural_problems()` still reports it."""
    scalar_rule: str                       # ruled 2026-08-10: B-i (see
                                           # aaron_ruled_methods)
    adverse_slippage_ticks: object         # Mapping[str, float] per scenario
    adverse_semantics: str                 # "replaces_per_side" (documented)

    def __post_init__(self):
        canon = _canonical_ticks(self.adverse_slippage_ticks)
        if canon is not self.adverse_slippage_ticks:
            object.__setattr__(self, "adverse_slippage_ticks", canon)


@dataclass(frozen=True)
class VolatilityRegimeMethod:              # DR-M6-B-v2
    close_source: str
    return_basis: str
    ddof: int
    roll_crossing_rule: str
    tercile_reference: str
    na_rule: str
    # DR-2 ruling (2026-08-10): the SAME vol20 mapping feeds both the S0 §2
    # descriptive stability axis and the Appendix-A sampling stratum key.
    # Default IS the ruled value (not an unruled fallback); TEST_ONLY
    # construction sites inherit it unless they explicitly override.
    mapping_scope: str = "shared_s2_and_appendixA"


@dataclass(frozen=True)
class FpAllocationMethod:                  # DR-M6-C
    basis: str                             # "A" | "B" | "C"
    weight_source: str
    shortfall_rule: str


@dataclass(frozen=True)
class BootstrapMethod:                     # DR-M6-D
    """DR-M6-D sub-decisions, one structured field each.

    `n_boot_per_seed` IS A FLAG, NEVER A RESAMPLE COUNT (M6.1.4 S3 naming
    audit). It carries DR-4.4 — the *attribution* of the frozen S0 §9
    budget of 10,000 stationary-bootstrap resamples:

        True  -> the 10,000 resamples are drawn PER SEED
                 (3 seeds x 10,000 = 30,000 draws in total)
        False -> the 10,000 are the TOTAL across the three seeds

    The count itself is frozen elsewhere and is NOT this field's business:
    it lives in `s0_real_run.FROZEN_N_BOOT = 10_000` (frozen S0 §9) and is
    pinned by the formal validator as `bootstrap_ci.<cell>.per_seed.<seed>
    .n_boot == 10000` (B0 matrix L083). Setting this field to `10000` is the
    misread this docstring exists to prevent; `structural_problems()`
    refuses any non-`bool` value AND emits a dedicated
    `n_boot_per_seed_is_a_flag_not_a_resample_count` problem for a numeric
    one, so such a value can never reach a `StudyConfig`.

    This field does NOT rule DR-4.4 — it only carries Aaron's ruling once it
    lands. `n_boot_applies_per_seed` is the unambiguous read alias; the field
    name is retained so existing construction sites keep working.
    """
    population: str
    na_day_rule: str
    statistic: str
    n_boot_per_seed: bool                  # DR-4.4 FLAG — not a count
    quoted_seed_rule: str
    percentile_interpolation: str
    crn_scope: str

    @property
    def n_boot_applies_per_seed(self) -> bool:
        """Unambiguous read alias for `n_boot_per_seed` (see class docstring).

        Prefer this name at every consumer site: it cannot be misread as a
        resample count. The underlying field name is kept as the canonical
        CONSTRUCTION key so no existing caller breaks; a full rename is a
        main-agent step (the identifier appears in main-agent-owned test
        files) and must keep this alias until those sites migrate.
        """
        return self.n_boot_per_seed


@dataclass(frozen=True)
class GridRepeatPolicy:                    # DR-M6-E
    k_per_seed: int
    k_start_index: int
    stream_includes_theta: bool
    convergence_rule: str
    max_doublings: int


@dataclass(frozen=True)
class ResolvedS0Methods:
    """M6.1.1 — the SINGLE source of truth for post-freeze method rulings.

    One structured field per DR family; None == pending. The pending list
    is DERIVED (no second hand-written tuple anywhere). StudyConfig can
    ONLY be built from a fully-resolved instance via derive_study_config.
    `test_only=True` marks synthetic values that must never reach a real
    run (the entrypoint refuses a test_only config outside tests).
    """
    spread_cost: SpreadCostMethod | None = None        # DR-M6-A-v2+IR-7
    volatility_regime: VolatilityRegimeMethod | None = None  # DR-M6-B-v2
    fp_allocation: FpAllocationMethod | None = None    # DR-M6-C
    bootstrap_method: BootstrapMethod | None = None    # DR-M6-D
    grid_policy: GridRepeatPolicy | None = None        # DR-M6-E
    event_na_mapping: str | None = None                # DR-M6-F
    stability_population: str | None = None            # DR-M6-G
    # DR-M6-H (M6.1.3 M-1): frozen §7 mandates the E2 worst-day P1/P5
    # REPORT but names no sample-quantile estimator; numpy linear is an
    # UNAPPROVED engineering convention (verified: no frozen text or
    # approved IR names an estimator). None == pending -> formal sealing
    # fail-closes on worst_day_estimator_unresolved.
    worst_day_estimator: str | None = None             # DR-M6-H
    test_only: bool = False

    def pending_fields(self) -> tuple[str, ...]:
        from dataclasses import fields as _fields
        return tuple(sorted(f.name for f in _fields(self)
                            if f.name != "test_only"
                            and getattr(self, f.name) is None))

    @property
    def fully_resolved(self) -> bool:
        return not self.pending_fields()

    def structural_problems(self) -> list[str]:
        """M6.1.2 — TYPE + BASIC-INVARIANT validation of the resolved
        values. This NEVER adopts, ranks or narrows an unruled research
        choice: it only rejects values that are the wrong TYPE or are
        structurally impossible (empty rule name, negative repeat count,
        non-finite slippage, ...). A structurally invalid config must be
        unable to make RealChain.ready() true.
        """
        import math as _math
        problems: list[str] = []

        def _str(owner: str, name: str, value) -> None:
            if not isinstance(value, str) or not value.strip():
                problems.append(f"{owner}.{name}_not_a_nonempty_str")

        def _int(owner: str, name: str, value, *, minimum: int) -> None:
            if isinstance(value, bool) or not isinstance(value, int):
                problems.append(f"{owner}.{name}_not_an_int")
            elif value < minimum:
                problems.append(f"{owner}.{name}_below_{minimum}")

        def _bool(owner: str, name: str, value) -> None:
            if not isinstance(value, bool):
                problems.append(f"{owner}.{name}_not_a_bool")

        expected = {
            "spread_cost": SpreadCostMethod,
            "volatility_regime": VolatilityRegimeMethod,
            "fp_allocation": FpAllocationMethod,
            "bootstrap_method": BootstrapMethod,
            "grid_policy": GridRepeatPolicy,
        }
        for name, cls in expected.items():
            value = getattr(self, name)
            if value is not None and not isinstance(value, cls):
                problems.append(f"{name}_not_a_{cls.__name__}")

        if isinstance(self.spread_cost, SpreadCostMethod):
            _str("spread_cost", "scalar_rule", self.spread_cost.scalar_rule)
            _str("spread_cost", "adverse_semantics",
                 self.spread_cost.adverse_semantics)
            ticks = self.spread_cost.adverse_slippage_ticks
            if not isinstance(ticks, Mapping) or not ticks:
                problems.append("spread_cost.adverse_slippage_ticks_not_a_"
                                "nonempty_mapping")
            else:
                for key, val in ticks.items():
                    if not isinstance(key, str):
                        problems.append("spread_cost.adverse_slippage_ticks_"
                                        "key_not_a_str")
                    if (isinstance(val, bool)
                            or not isinstance(val, (int, float))
                            or not _math.isfinite(float(val))
                            or float(val) < 0.0):
                        problems.append("spread_cost.adverse_slippage_ticks_"
                                        f"value_invalid:{key}")

        if isinstance(self.volatility_regime, VolatilityRegimeMethod):
            v = self.volatility_regime
            for name in ("close_source", "return_basis", "roll_crossing_rule",
                         "tercile_reference", "na_rule", "mapping_scope"):
                _str("volatility_regime", name, getattr(v, name))
            _int("volatility_regime", "ddof", v.ddof, minimum=0)

        if isinstance(self.fp_allocation, FpAllocationMethod):
            for name in ("basis", "weight_source", "shortfall_rule"):
                _str("fp_allocation", name, getattr(self.fp_allocation, name))

        if isinstance(self.bootstrap_method, BootstrapMethod):
            b = self.bootstrap_method
            for name in ("population", "na_day_rule", "statistic",
                         "quoted_seed_rule", "percentile_interpolation",
                         "crn_scope"):
                _str("bootstrap_method", name, getattr(b, name))
            _bool("bootstrap_method", "n_boot_per_seed", b.n_boot_per_seed)
            # M6.1.4 (S3) naming audit: the ONE misread this field invites is
            # "number of resamples per seed". A numeric value therefore gets
            # its own decisive problem code on top of the generic bool check,
            # so `n_boot_per_seed=10_000` can never reach a StudyConfig.
            if (not isinstance(b.n_boot_per_seed, bool)
                    and isinstance(b.n_boot_per_seed, _Real)):
                problems.append("bootstrap_method.n_boot_per_seed_is_a_flag_"
                                "not_a_resample_count")

        if isinstance(self.grid_policy, GridRepeatPolicy):
            g = self.grid_policy
            _int("grid_policy", "k_per_seed", g.k_per_seed, minimum=1)
            _int("grid_policy", "k_start_index", g.k_start_index, minimum=0)
            _int("grid_policy", "max_doublings", g.max_doublings, minimum=0)
            _bool("grid_policy", "stream_includes_theta",
                  g.stream_includes_theta)
            _str("grid_policy", "convergence_rule", g.convergence_rule)

        if self.event_na_mapping is not None:
            _str("methods", "event_na_mapping", self.event_na_mapping)
        if self.stability_population is not None:
            _str("methods", "stability_population", self.stability_population)
        # M6.1.3 fix-round (blind-audit F4): the 8th field gets the SAME
        # structural gate as the other string rulings — '' / 42 / {} are
        # refused here, while the VALUE semantics stay pending DR-M6-H.
        if self.worst_day_estimator is not None:
            _str("methods", "worst_day_estimator", self.worst_day_estimator)
        if not isinstance(self.test_only, bool):
            problems.append("methods.test_only_not_a_bool")
        return problems


# --- AARON S0-CLOSEOUT RULINGS (2026-08-10) ---------------------------------
# Ruling record: AARON_S0_CLOSEOUT_DECISION_FORM_V1 was delivered in chat with
# one recommended option per item; Aaron ruled "逐项裁决全跟你推荐的方式做即可"
# (2026-08-10, S0-closeout mainline session). The exact-phrase PHASE-C trigger
# was waived by its own author; the waiver is disclosed in the final Codex
# packet. IR-27 (IMPLEMENTATION_RESOLUTIONS.md) carries the item-by-item map.
# THESE VALUES ARE THE SINGLE RULED SOURCE — consumers read them structurally
# from `aaron_ruled_methods()`; no consumer may re-state a ruled literal.

#: IR-7 Option i (Primary): per-scenario adverse-slippage ticks, EFFECTIVE
#: values. Stress carries the already-multiplied 2.0 (Base 1 x2) — consumers
#: must NOT apply friction_multiplier to adverse ticks again. Option ii
#: (+1 tick) is a SENSITIVITY channel, never Primary.
AARON_RULED_ADVERSE_TICKS_PRIMARY: Mapping[str, float] = MappingProxyType({
    "Base": 1.0, "Conservative": 2.0, "Stress": 2.0, "Severe": 3.0})
AARON_RULED_ADVERSE_TICKS_SENSITIVITY: Mapping[str, float] = MappingProxyType({
    "Base": 2.0, "Conservative": 3.0, "Stress": 3.0, "Severe": 4.0})


def aaron_ruled_methods() -> "ResolvedS0Methods":
    """The fully-resolved method set per Aaron's 2026-08-10 rulings.

    DR-1  spread reduction B-i (trading-window slots [600,944]; the triple is
          (Q50(med_s), Q50(p90_s), Q50(p95_s)) — equal-weight slots, numpy
          linear interpolation, no rounding) + IR-7 Option i Primary adverse
          vector, semantics = REPLACE the regular per-side slip (wording fix
          of the old "extra" comment; the implementation always replaced).
    DR-2  vol20: simple returns, ddof=1, close = exact scheduled last 1-minute
          RTH bar close (IR-19/26 anchor point), roll-crossing return dropped
          and window extended (r1), terciles bounded on the FULL Development
          sample (ex-post descriptive), shared mapping (§2 + Appendix A),
          <21 qualifying closes -> vol_na fourth stratum (day kept).
    DR-3  FP allocation follows the SELECTED TP composition (Hamilton), with
          the frozen-literal shortfall redistribution over remaining strata.
    DR-4  bootstrap: full eligible trading-day sequence; NA days dropped from
          the sequence with disclosed count (n1); statistic = per-trading-day
          mean USD; 10,000 resamples PER seed; quoted seed 7; percentile
          interpolation linear; CRN shared within theta across
          engine x scenario.
    DR-5  grid: K=200 per seed per cell, k from 0, theta in the RNG stream,
          max 2 doublings, unconverged -> infeasible_by_convergence
          (fail-closed marker); full MC §5 four-rule battery applies at the
          MC wiring (cross-reference, not restated here).
    DR-6  event NA mapping F1: five strata {CPI, NFP, FOMC, none,
          NA_multi_event} — IR-12/18 vocabulary, zero new vocabulary.
    DR-7  stability views: BOTH populations reported (D_TP-conditional and
          full structurally-eligible sequence).
    DR-8  E2 worst-day P1/P5 sample-quantile estimator: linear.
    """
    return ResolvedS0Methods(
        spread_cost=SpreadCostMethod(
            scalar_rule="B_i_trading_window_q50med_q50p90_q50p95",
            adverse_slippage_ticks=AARON_RULED_ADVERSE_TICKS_PRIMARY,
            adverse_semantics="replaces_per_side"),
        volatility_regime=VolatilityRegimeMethod(
            close_source="exact_scheduled_last_1m_close",
            return_basis="simple",
            ddof=1,
            roll_crossing_rule="r1_drop_and_extend",
            tercile_reference="full_development_expost",
            na_rule="vol_na_fourth_stratum",
            mapping_scope="shared_s2_and_appendixA"),
        fp_allocation=FpAllocationMethod(
            basis="B",
            weight_source="selected_tp_composition",
            shortfall_rule="frozen_literal_redistribute_remaining_fp"),
        bootstrap_method=BootstrapMethod(
            population="full_eligible_trading_day_sequence",
            na_day_rule="n1_drop_from_sequence_disclose_count",
            statistic="per_trading_day_mean_usd",
            n_boot_per_seed=True,
            quoted_seed_rule="fixed_seed_7",
            percentile_interpolation="linear",
            crn_scope="shared_within_theta_engine_scenario"),
        grid_policy=GridRepeatPolicy(
            k_per_seed=200,
            k_start_index=0,
            stream_includes_theta=True,
            convergence_rule="mc_spec_s5_four_rules_at_mc_wiring",
            max_doublings=2),
        event_na_mapping="F1_five_stratum_ir12_18_vocab",
        stability_population="both_conditional_and_full_eligible",
        worst_day_estimator="linear",
        test_only=False)


# --- L-5 ruling (2026-08-10): dedicated LOCAL, NON-CLOUD-SYNCED output
# roots. The repo lives inside an actively-syncing OneDrive tree; the
# M6.1.7 exact-set disk invariant makes any sync droppings
# (desktop.ini/*.tmp) a seal-refusal that burns a trial. Ruled values —
# not unruled defaults. attempts/ migrates to the SAME root (ruled);
# archive copies get per-file SHA-256 recheck. Zero-whitelist stays.
RULED_RUNS_ROOT = r"C:\Users\Aaron\quant-data\itsf-runs"
RULED_ARCHIVE_ROOT = r"C:\Users\Aaron\quant-data\itsf-runs-archive"


@dataclass(frozen=True)
class StudyConfig:
    """M6.1.1 — DERIVED bundle; never hand-built in production.

    The ONLY constructor is derive_study_config(methods, ...), which
    refuses a partially-resolved ResolvedS0Methods — so there is no
    second pending-truth-source: disclosures/pending come from
    `methods.pending_fields()` alone, and every method sub-item travels
    structurally on `methods` for its consumer to read.
    """
    methods: ResolvedS0Methods
    spread_scalars: tuple[float, float, float]
    regime_of: object                       # Callable[[date_str], str]
    vol_axis_of: object                     # Callable[[date_str], str]

    def __post_init__(self):
        # LOW-1 (M6.1.1 audit): the "derived-only" claim is ENFORCED —
        # direct construction with pending methods raises exactly like
        # derive_study_config would. M6.1.2: a STRUCTURALLY invalid set of
        # resolved values is refused here too, so no illegal config can
        # exist anywhere (and therefore cannot make ready() true).
        pend = self.methods.pending_fields()
        if pend:
            raise ValueError("StudyConfig: pending method rulings: "
                             + ", ".join(pend))
        bad = self.methods.structural_problems()
        if bad:
            raise ValueError("StudyConfig: structurally invalid methods: "
                             + ", ".join(bad))
        for name in ("regime_of", "vol_axis_of"):
            if not callable(getattr(self, name)):
                raise ValueError(f"StudyConfig: {name} must be callable")
        scal = self.spread_scalars
        if (not isinstance(scal, tuple) or len(scal) != 3
                or any(_canonical_scalar(v) is None for v in scal)):
            raise ValueError("StudyConfig: spread_scalars must be 3 finite "
                             "non-negative numbers")
        # M6.1.3 M-2 ordering constraint — PROOF CHAIN (this is a TYPE-level
        # invariant, NOT an approval of any A/B/C, RTH/trade-window,
        # cross-slot reduction or fill-minute scheme; Stress is outside this
        # triple):
        #   frozen S0 §6 field semantics: Base uses the period MEDIAN
        #   spread, Conservative uses P90, Severe uses P95 of the SAME
        #   legal spread population
        #   -> StudyConfig tuple positional semantics: (median, p90, p95)
        #      (consumed positionally by costs.build_scenarios)
        #   -> quantiles of one population are monotone: Q50 <= Q90 <= Q95
        #   -> every candidate reduction under DR-1 (A-i/A-ii/B-i/B-ii/C)
        #      preserves that pointwise order.
        canon = canonical_spread_scalars(scal)
        if canon is None:
            raise ValueError("StudyConfig: spread_scalars must satisfy "
                             "0 <= median <= P90 <= P95 (frozen §6 quantile "
                             "semantics; see proof chain in source)")
        # M6.1.4 (S3) CANONICAL FORM: store plain floats, never numpy scalars
        # and never a mixed int/float triple, so that two configs derived
        # from EQUAL inputs compare EQUAL — the property the production
        # cache gate (the config gateway) depends on. Representation only:
        # no DR-1 reduction rule is adopted, ranked or narrowed here.
        object.__setattr__(self, "spread_scalars", canon)


def derive_study_config(methods: ResolvedS0Methods, *,
                        spread_scalars, regime_of,
                        vol_axis_of) -> StudyConfig:
    """Build a StudyConfig from a FULLY-resolved ResolvedS0Methods.

    Raises ValueError while any ruling pends (fail closed — the caller
    reports the pending list instead). The concrete injectables
    (spread_scalars per the ruled reduction rule, the ruled regime/vol
    mappings) are supplied by the caller that read them from locked
    artifacts — or, in tests, from TEST_ONLY synthetic values on a
    methods instance with test_only=True.
    """
    pend = methods.pending_fields()
    if pend:
        raise ValueError("derive_study_config: pending method rulings: "
                         + ", ".join(pend))
    bad = methods.structural_problems()
    if bad:
        raise ValueError("derive_study_config: structurally invalid "
                         "methods: " + ", ".join(bad))
    return StudyConfig(methods=methods, spread_scalars=tuple(spread_scalars),
                       regime_of=regime_of, vol_axis_of=vol_axis_of)


class _Unreadable:
    """Sentinel: a key whose value could not be read (see
    `validate_injectables`). Deliberately inert — no `__eq__`, no
    `__getattr__`."""

    __slots__ = ()


_UNREADABLE = _Unreadable()


def validate_injectables(inj) -> list[str]:
    """M6.1.4 (S3) — EXACT-KEY schema gate for an `_approved_injectables()`
    payload. Returns a deterministic (sorted, de-duplicated) list of problem
    codes; an EMPTY list means the mapping is structurally admissible as
    ``derive_study_config(methods, **inj)`` keyword arguments.

    THIS FUNCTION NEVER RAISES, for any input whatsoever — that is its whole
    point. It sits in front of the production config gate, where a
    `TypeError` escaping the check would be a fail-OPEN by exception
    (blind-audit N4c class). Bools, strings, lists, ``None``, objects with a
    raising ``__getattr__``/``__eq__``/``keys()``, and Mappings whose
    ``__getitem__`` detonates all come back as problem codes.

    BOUNDARY — the callables are checked with `callable()` and are NEVER
    CALLED here. Invoking attacker-supplied code inside a validation gate is
    the N3 defect class this codebase already fixed once (see
    the config gateway's type-pin-before-any-read ordering in s0_real_run).
    Whether `regime_of("2020-01-02")` actually returns a legal regime label
    is a CALL-TIME concern and belongs to the compute path's own
    ``try/except`` — never to this gate.

    This function validates STRUCTURE only. It never adopts, ranks or
    narrows any unruled research choice: DR-1 (the spread reduction rule
    that produces the triple) and DR-2 (the volatility/regime mappings) stay
    open, and a structurally admissible payload is not an approved one.

    Problem codes (all prefixed ``injectables.``):
      ``not_a_mapping`` · ``empty`` · ``keys_unreadable`` ·
      ``missing_key:<name>`` · ``extra_key:<name>`` · ``unreadable:<name>`` ·
      ``spread_scalars_not_a_tuple`` · ``spread_scalars_wrong_length:<n>`` ·
      ``spread_scalars_value_invalid:<index>`` ·
      ``spread_scalars_not_ordered_median_le_p90_le_p95`` ·
      ``regime_of_not_callable`` · ``vol_axis_of_not_callable`` ·
      ``validation_raised``
    """
    problems: list[str] = []

    def _emit(code: str) -> None:
        problems.append("injectables." + code)

    def _name(key) -> str:
        try:
            return key if isinstance(key, str) else repr(key)
        except BaseException:
            return "<unreprable_key>"

    try:
        # A Mapping is required. `bool`/`str`/`list`/`tuple`/`None`/arbitrary
        # objects are refused WITHOUT touching a single attribute on them.
        if not isinstance(inj, Mapping):
            _emit("not_a_mapping")
            return sorted(set(problems))

        try:
            keys = list(inj.keys())
        except BaseException:
            _emit("keys_unreadable")
            return sorted(set(problems))

        if not keys:
            _emit("empty")

        seen: set[str] = set()
        for key in keys:
            if isinstance(key, str) and key in INJECTABLE_KEYS:
                seen.add(key)
            else:
                _emit("extra_key:" + _name(key))
        for want in sorted(INJECTABLE_KEYS):
            if want not in seen:
                _emit("missing_key:" + want)

        def _read(key):
            """Value at `key`, or the `_UNREADABLE` sentinel."""
            try:
                return inj[key]
            except BaseException:
                _emit("unreadable:" + key)
                return _UNREADABLE

        if "spread_scalars" in seen:
            scal = _read("spread_scalars")
            if scal is not _UNREADABLE:
                if not isinstance(scal, tuple):
                    _emit("spread_scalars_not_a_tuple")
                else:
                    try:
                        length = len(scal)
                    except BaseException:
                        length = -1
                    if length != 3:
                        _emit(f"spread_scalars_wrong_length:{length}")
                    else:
                        vals = []
                        for i, v in enumerate(scal):
                            f = _canonical_scalar(v)
                            if f is None:
                                _emit(f"spread_scalars_value_invalid:{i}")
                            vals.append(f)
                        if all(v is not None for v in vals):
                            m, p90, p95 = vals
                            if not (0.0 <= m <= p90 <= p95):
                                _emit("spread_scalars_not_ordered_median_le_"
                                      "p90_le_p95")

        for name in ("regime_of", "vol_axis_of"):
            if name in seen:
                fn = _read(name)
                if fn is not _UNREADABLE and not callable(fn):
                    _emit(name + "_not_callable")
    except BaseException:
        # Last line of defence. A gate that raises is a gate that fails open;
        # BaseException is deliberate (a hostile __getattr__ may raise
        # anything at all, including a non-Exception).
        _emit("validation_raised")
    return sorted(set(problems))


def canonical_config(cfg: StudyConfig) -> StudyConfig:
    """M6.1.4 (S3) — return `cfg` in canonical form (idempotent).

    Every `StudyConfig` built through `__init__`/`derive_study_config` is
    ALREADY canonical: `__post_init__` rewrites `spread_scalars` to a tuple
    of plain floats and `SpreadCostMethod.__post_init__` freezes the adverse
    -slippage mapping. This helper exists for configs assembled by BYPASS
    (`object.__new__` + `object.__setattr__`, the route the M6.1.2/M6.1.3
    defence-in-depth tests exercise) and for callers that want the guarantee
    explicitly. It re-runs the full `__post_init__` validation, so an
    invalid config raises `ValueError` here rather than propagating.

    NOT A SECURITY GATE. It reads `cfg.methods` and therefore must run
    AFTER the caller's type pin (`type(cfg.methods) is ResolvedS0Methods`),
    never before it — reading attributes off an unpinned object can execute
    foreign code (blind-audit N3).
    """
    if not isinstance(cfg, StudyConfig):
        raise TypeError("canonical_config: not a StudyConfig instance")
    return StudyConfig(methods=cfg.methods,
                       spread_scalars=cfg.spread_scalars,
                       regime_of=cfg.regime_of,
                       vol_axis_of=cfg.vol_axis_of)


@dataclass
class CostScenarioParams:
    """Market-friction scenario (S0 §6). spread values are FULL bid-ask width
    in index points; each side pays spread/2 (frozen)."""
    name: str                          # Base | Conservative | Stress | Severe
    spread_points: float               # full width for the applicable minute
    slippage_ticks_per_side: float
    adverse_slippage_ticks: float      # ticks REPLACING the per-side slip on
                                       # stop fills, PRE-friction_multiplier
                                       # (IR-7 ruled 2026-08-10; the old
                                       # "extra" wording was wrong — the
                                       # implementation always replaced)
    friction_multiplier: float = 1.0   # Stress = Base market friction x2
    platform_fee_rt_usd: float = S0_PLATFORM_FEE_RT_USD


@dataclass
class TradePathRecord:
    """Atomic per-contract intraday trade path (S0 §10.1, frozen schema)."""
    trade_date: str                    # YYYY-MM-DD (template/trading day id)
    engine: str                        # 'E1' | 'E2'
    cost_scenario: str
    direction: int                     # +1 long / -1 short (== d_open)
    entry_ts: str
    exit_ts: str
    entry_fill: float
    exit_fill: float
    final_pnl_per_contract: float      # USD, all trading costs deducted ONCE here
    mtm_close_pnl_1m: list[float] = field(default_factory=list)
    mtm_adverse_pnl_1m: list[float] = field(default_factory=list)
    max_adverse_pnl: float = 0.0
    max_favourable_pnl: float = 0.0    # diagnostic_only: true (IR-2) — never an
                                       # input to oracle labels, costs,
                                       # feasibility or the verdict table
    time_of_max_adverse: str = ""
    planned_stop: float | None = None
    actual_stop_fill: float | None = None
    stop_triggered: bool = False
    sizing_anchor_usd: float = 0.0     # E1: actual planned stop risk incl cost;
                                       # E2: counterfactual E1 anchor (frozen)
    ambiguous_stop_vs_floor: bool = False


@dataclass
class DayFeatures:
    """S0 §4. None == NA (day stays in sample; per-table NA counts mandatory).

    is_event_day (F10): frozen categories {CPI, NFP, FOMC, none}; ``None``
    == NA for multi-event days per IR-12 + IR-18 (primary conflict detected
    AFTER IR-13 eligibility; the multi-hot detail lives only in the
    diagnostic sidecar, never here). Added 2026-07-31 (M5-T0): the previous
    4-string closed set could not express the approved NA state.
    """
    trade_date: str
    ret_open30: float | None = None            # F1  (C0959-O0930)/ADR14
    or_width: float | None = None              # F2
    de_open30: float | None = None             # F3  close-path only
    rvol_open30: float | None = None           # F4
    gap: float | None = None                   # F5  NA on roll transition
    open_loc_on: float | None = None           # F6
    on_range: float | None = None              # F7
    retrace_open30: float | None = None        # F8  directional running-max
    close_pos_open30: float | None = None      # F9
    is_event_day: str | None = "none"          # F10 CPI|NFP|FOMC|none|None=NA(IR-12/18)
    is_roll_transition: bool = False           # F11
    is_roll_window: bool = False
    adr14: float | None = None
    excluded_day: bool = False                 # half-day / no-trade / >10% missing
    exclusion_reason: str = ""


@dataclass
class DayLabels:
    """S0 §5. d_open == 0 -> no-direction day (counted, not tradeable)."""
    trade_date: str
    d_open: int = 0                            # sign(ret_open30); 0 = no direction
    y_cont: float | None = None                # d_open*(C1544-O1000)/ADR14  (primary)
    y1: float | None = None                    # descriptive only
    y2_de_pm: float | None = None              # close-path
    y3_close_pos_pm: float | None = None
    y4_mfe: float | None = None                # relative to d_open from O1000
    y5_mae: float | None = None
    y6_cont_decile: int | None = None


# --- M5 runner shared contracts (MAIN-AGENT OWNED, added 2026-07-31) --------
# SA-4 / SA-5 depend on these EXACT names; interface change requests go to
# `unresolved`, never edited in place by a subagent.

from enum import Enum


class RunStage(str, Enum):
    """Authorization-packet §7 stages. Transition order is strict."""
    A_PRECHECK = "A_PRECHECK"                # mechanical gates (packet §9)
    B_LOAD_VALIDATE = "B_LOAD_VALIDATE"      # structural checks vs assertions
    C_COMPUTE = "C_COMPUTE"                  # exposure begins at entry (atomic)
    D_INTEGRITY = "D_INTEGRITY"              # NA conservation etc.
    E_REPORT = "E_REPORT"
    F_SEALED = "F_SEALED"


class TrialState(str, Enum):
    """Packet §0 state machine; transitions appended to ops/TRIAL_REGISTRY.md
    by the MAIN AGENT ONLY (append-only event chain)."""
    PACKET_DRAFTED = "PACKET_DRAFTED"
    PACKET_APPROVED = "PACKET_APPROVED"
    RUNNER_IMPLEMENTED = "RUNNER_IMPLEMENTED"
    READY_FOR_RUN_AUTHORIZATION = "READY_FOR_RUN_AUTHORIZATION"
    RUN_AUTHORIZED = "RUN_AUTHORIZED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# Approved NA reasons (frozen L44-45 + IR-12/15/17/18/19/20 + preflight
# taxonomy). Stage D conserves produced NA counts against EXACTLY this set;
# any NA/NaN with an unlisted reason is a hard failure (packet §7).
APPROVED_NA_REASONS = (
    "adr14_warmup",                      # F1/F2/F5/F7 normalisation warm-up
    "f4_lookback_warmup",                # IR-20 60-day basis warm-up
    "roll_transition_day_na",            # F5 on is_roll_transition (frozen L57)
    "prev_rth_close_anchor_missing",     # IR-19 (incl. early-close-bar-absent,
                                         #   vendor-degraded, first sample day)
    "anchor_missing",                    # exact anchor absent (frozen L44-45)
    "multi_event_day_f10_na",            # IR-12 + IR-18 (9 days)
    "zero_direction_day_l82",            # ret_open30 == 0 (frozen L82)
    "direction_undeterminable_na",       # ret_open30 NA -> d_open 0 (labels.py)
    "overnight_window_empty",            # F6/F7 no bars in span
    "overnight_range_zero",              # F6 0/0 (ruling R3)
    "path_zero",                         # F3 denominator (frozen L77 analogue)
    "degenerate_window",                 # F9 H == L
    "official_time_unavailable_in_archived_source",  # IR-17 (diagnostic col)
)


class RunGateError(RuntimeError):
    """A packet-§9 hard gate failed in Stage A/B (pre-exposure)."""


class InputDataDefectError(RuntimeError):
    """IR-22: a required input value is structurally defective (e.g.
    non-finite opening-window volume). Stage-B STOP — never a day-level NA
    the run may continue past."""


class NAConservationError(RuntimeError):
    """Stage D: produced NA does not conserve against APPROVED_NA_REASONS."""


class AssertionMismatchError(RuntimeError):
    """Independently computed value != expected_preflight_assertions entry.
    Assertions are compare-only; they must NEVER feed computation."""


class LogLeakError(RuntimeError):
    """Stage-C log guard: research vocabulary or non-whitelisted numeric."""


@dataclass(frozen=True)
class RunConfig:
    """Injected by the MAIN-AGENT entrypoint from approved artifacts at run
    time. Frozen dataclass: no runtime mutation; NO preflight observation
    numbers may be embedded here (they live in the assertions FILE and are
    compare-only)."""
    trial_id: str                         # e.g. S0-T001
    authorized_commit: str                # full 40-hex from Aaron's sentence
    # DR-02: run-infra provenance stamp ONLY (recorded in run metadata).
    # NEVER a research RNG seed — research randomness derives exclusively
    # from RESEARCH_BOOTSTRAP_SEEDS (7/13/31, frozen S0 §9/App A).
    engineering_seed: int
    attempts_dir: str                     # <runs_root>/attempts/<trial>-A<seq>/
    runs_dir: str                         # <runs_root>/runs/<trial>_<UTC>/
    assertions_path: str                  # expected_preflight_assertions json
    # L-5 ruling (2026-08-10): the governed output roots. Defaults ARE the
    # ruled values (RULED_RUNS_ROOT / RULED_ARCHIVE_ROOT), not unruled
    # fallbacks. Both enter the environment lock; runs_dir/attempts_dir must
    # resolve UNDER runs_root, and runs_root must NOT be inside the repo
    # tree (enforced by the runner stack, tested in test_s0_runner).
    runs_root: str = RULED_RUNS_ROOT
    archive_root: str = RULED_ARCHIVE_ROOT


@dataclass
class AccountEvent:
    """Emitted by platform lifecycles per simulated day."""
    day: str
    phase: str                 # evaluation | funded | combine | xfa | dead | done
    balance: float
    floor: float
    breached: bool = False
    payout_gross: float = 0.0
    payout_cash: float = 0.0   # gross*split - rail fee (payout_accounting, frozen)
    fees_usd: float = 0.0      # platform fees charged today (subs/reset/activation/...)
    notes: str = ""
