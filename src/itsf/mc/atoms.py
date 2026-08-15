"""THE unified MC atom layer (N01 / PHASE D1-D2-D4-D6, lane S1).

ONE atom per (world, start-phase). Every downstream quantity — world
means, P5/median/P95, within-world SEs, raw feasibility metrics, the M
exhaustive-support certificate, verdict inputs, the sealed report, the
conditional aleatoric slice and the total-predictive mixture — is
REDUCED FROM THE SAME atom set. There is no parallel caller-supplied
summary anywhere: a caller can hand over atoms (which carry their own
cross-invariants and identity bindings) or nothing at all.

What this module deliberately does NOT contain (decision isolation D7):
no feasibility gate/threshold, no K-dependent kill rule, no fixed-world
selection rule, no strategy parameter, no eligibility rule, no NA rule.
It establishes RAW FACTS and MECHANICAL CAPABILITY only. Every threshold
that appears here (`QUALIFYING_DAY_MIN_PROFIT_USD`, the platform
constants) is transcribed from an ALREADY-FROZEN source and is a raw
metric definition, never a gate.

Layout:
  1. axes, frozen versions and the RNG spec
  2. fail-closed error type + canonical JSON
  3. typed absent-quantity sentinels (three DISTINCT "None"s)
  4. `SimulationPathObservation` — the atom, with cross-invariants
  5. canonical serialisation (JSONL) + per-atom / two-level digests
  6. `path_facts_from_events` — the ONE narrow S2-seam adapter
  7. `lifecycle_config_digest` — mechanical identity of everything that
     can change a result
  8. key-grid helpers (`expected_key_grid` / `reduce_actual_keys`) —
     the SINGLE implementation both C1 and C2 call
  9. `ObservationSet` — declare-and-verify container with two-level
     flat digests and the in-type reducer
"""
from __future__ import annotations

import dataclasses
import hashlib
import importlib
import json
import math
import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable, Mapping, Sequence

from itsf import contracts as _contracts
from itsf.mc import orchestrator as _orch

# --- 1. frozen axes / versions ---------------------------------------------

# frozen: MC SS2.5 / SS4.1 — the complete evaluated axes.
ENGINES = ("E1", "E2")
SCENARIOS = ("Base", "Conservative", "Stress", "Severe")
PLATFORMS = ("lucid", "topstep")

# frozen: platform_params lucidflex_50k payouts.qualifying_day_min_profit_usd
# = 150 (also topstep XFA_QUALIFYING_DAY_MIN_NET_USD). RAW METRIC ONLY —
# `days_profit_ge_150` counts days at or above this frozen floor; it is
# NOT a feasibility gate and MUST NOT be read as a frequency proxy
# (master plan N-D2 explicitly forbids that reading).
QUALIFYING_DAY_MIN_PROFIT_USD = 150.0

# frozen: MC SS7 freeze tag — the method identity every atom binds to.
METHOD_VERSION = "mc-freeze-v1"

# Algorithm versions. BUMP DELIBERATELY (reviewed change) whenever the
# lifecycle execution semantics or the replay procedure change in a way
# that can move a number; they enter `lifecycle_config_digest`, so a bump
# invalidates every previously produced atom by construction.
ORCHESTRATOR_ALGO_VERSION = "itsf.mc.orchestrator.run_lifecycle.v1"
REPLAY_ALGO_VERSION = "itsf.mc.consumer.cold_replay.v1"

# frozen: MC SS5 — the complete randomness specification of the epistemic
# layer. A one-byte change here changes every lifecycle_config_digest.
RNG_SPEC = ("numpy.random.SeedSequence(master_seed).spawn(B); world b = "
            "Generator(PCG64(child_b)); Politis-Romano stationary "
            "bootstrap, geometric blocks p=1/5.0, circular wrap; "
            "start-phase support = exhaustive enumeration of the "
            "prepared calendar first_month_offsets (IR-29a)")

# frozen: MC SS4.2 payout_policy_primary. A LABEL of the already-frozen
# policy — not a new decision, and not derivable from the `combo` string.
PAYOUT_PATH_ID = ("payout_policy_primary:first_eligible_session|"
                  "maximum_allowed")

# The modules whose UPPER_CASE frozen constants can change a result and
# are therefore harvested MECHANICALLY into every config digest.
HARVESTED_CONSTANT_MODULES = (
    "itsf.mc.orchestrator",
    "itsf.mc.platforms.lucid",
    "itsf.mc.platforms.topstep",
    "itsf.mc.account",
)

# EXPLICIT exclusion set: "module:NAME" -> reason. Anything harvested is
# in the digest by DEFAULT; a new constant enters automatically. Removing
# one requires an entry here WITH a reason, and the reason is pinned by
# `tests/test_mc_atoms.py::test_frozen_constant_exclusions_are_justified`.
# EMPTY TODAY — no result-relevant constant is exempt.
FROZEN_CONSTANT_EXCLUSIONS: Mapping[str, str] = MappingProxyType({})

# Constants the harvest MUST contain (regression pin — the mechanical
# sweep is allowed to grow, never to silently lose one of these).
REQUIRED_HARVESTED_CONSTANTS = (
    "itsf.mc.orchestrator:MAX_EVALUATION_STARTS",
    "itsf.mc.orchestrator:B2F_MAX_PER_XFA",
    "itsf.mc.orchestrator:B2F_WINDOW_DAYS",
    "itsf.mc.orchestrator:API_FEE_USD",
    "itsf.mc.orchestrator:API_INTERVAL_DAYS",
    "itsf.mc.orchestrator:LUCID_PROCESSING_HALT_DAYS",
    "itsf.mc.orchestrator:LUCID_FIRST_PURCHASE_USD",
    "itsf.mc.orchestrator:LUCID_RESET_USD",
    "itsf.mc.orchestrator:LUCID_REPURCHASE_USD",
    "itsf.mc.orchestrator:HORIZON_MONTHS",
    "itsf.mc.orchestrator:RETENTIONS",
    "itsf.mc.platforms.lucid:TRADER_SPLIT",
    "itsf.mc.platforms.lucid:PAYOUT_RAIL_FEE_USD",
    "itsf.mc.platforms.lucid:FUNDED_TIERS",
    "itsf.mc.platforms.topstep:B2F_FEE_USD",
    "itsf.mc.platforms.topstep:TRADER_SPLIT",
    "itsf.mc.account:PRIMARY_POLICY",
    "itsf.mc.account:LUCID_ABSOLUTE_MAX_MICROS",
    "itsf.mc.account:TOPSTEP_ABSOLUTE_MAX_MICROS",
)

_UPPER_CONST = re.compile(r"^[A-Z][A-Z0-9_]*$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")

# The EXACT lifecycle-config preimage key set (D2: unknown / missing /
# extra all refuse, each with its own code).
LIFECYCLE_CONFIG_PREIMAGE_FIELDS = (
    "schema",
    "lifecycle_config_fields",
    "frozen_constants",
    "engine",
    "scenario",
    "theta_channel",
    "payout_path_id",
    "platform_params_snapshot_sha256",
    "snapshot_manifest_sha256",
    "method_spec_sha256",
    "orchestrator_algo_version",
    "replay_algo_version",
    "method_version",
    "rng_spec",
)
LIFECYCLE_CONFIG_SCHEMA = "mc_lifecycle_config.v1"

ATOM_SCHEMA = "mc_simulation_path_observation.v1"
OBSERVATION_SET_SCHEMA = "mc_observation_set.v1"


# --- 2. errors + canonical JSON --------------------------------------------

class MCInputError(ValueError):
    """Fail-closed refusal. `code` is the machine-readable reason.

    Defined HERE (not in consumer.py) so the atom layer and the consumer
    raise ONE exception type without an import cycle; `itsf.mc.consumer`
    re-exports it under the historical name."""

    def __init__(self, code: str, detail: str = ""):
        self.code = code
        super().__init__(f"{code}: {detail}" if detail else code)


def canonical_json(obj) -> str:
    """THE canonical JSON form for every digest in the MC atom layer:
    sorted keys, compact separators, ASCII, NaN/Infinity rejected (they
    are pre-encoded as tokens by `jsonable`). Same discipline as
    `day_strata_supplement.canonical_json`."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=True,
                      separators=(",", ":"), allow_nan=False)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def jsonable(value):
    """Canonicalise a frozen-constant value for the digest preimage.

    Non-finite floats become explicit tokens (JSON has no Infinity, and
    `lucid.FUNDED_TIERS` carries one) — never dropped, never coerced to a
    number that would collide with a real value."""
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if math.isnan(value):
            return "__nan__"
        if value == math.inf:
            return "__inf__"
        if value == -math.inf:
            return "__-inf__"
        return value
    if isinstance(value, str):
        return value
    if isinstance(value, (tuple, list)):
        return [jsonable(v) for v in value]
    if isinstance(value, (set, frozenset)):
        return ["__set__"] + sorted(canonical_json(jsonable(v)) for v in value)
    if isinstance(value, Mapping):
        return {str(k): jsonable(v) for k, v in value.items()}
    raise MCInputError(
        "lifecycle_config_unharvestable_constant",
        f"value of type {type(value).__name__} has no canonical form — "
        "add it to FROZEN_CONSTANT_EXCLUSIONS with a reason, or give it "
        "a canonical encoding; it may NOT be silently dropped")


def world_digest(world: Sequence[str]) -> str:
    """Content digest of ONE bootstrap world (the drawn day-id sequence).
    This exact formula is the world's identity everywhere."""
    return _sha256_text("|".join(str(d) for d in world))


# --- 3. typed absent quantities (three DISTINCT "None"s) --------------------

@dataclass(frozen=True, slots=True)
class AbsentQuantity:
    """A quantity that is NOT a number, carrying WHY it is not a number.

    Three distinct instances exist and they are never interchangeable:

      NOT_APPLICABLE      the quantity is permanently undefined for this
                          configuration (E1 has no E2 sizing budget);
      PENDING_RULING      the quantity is defined but its rule/observation
                          awaits Aaron (E2 over-budget days);
      PENDING_ENGINEERING the quantity is defined and ruled but the
                          platform-event plumbing has not landed yet.

    A raw `None` is REFUSED by the atom constructor: an untyped None is
    exactly the ambiguity this type exists to destroy, and 0 may never
    impersonate any of them."""
    token: str
    reason: str

    def __str__(self) -> str:                       # report rendering
        return self.token


NOT_APPLICABLE = AbsentQuantity(
    "NOT_APPLICABLE",
    "permanently undefined for this engine/platform configuration")
NOT_APPLICABLE_NO_TRADE = AbsentQuantity(
    "NOT_APPLICABLE_NO_TRADE",
    "no position was taken, so the quantity has no referent")
PENDING_RULING = AbsentQuantity(
    "PENDING_RULING",
    "defined but the rule or its observation awaits Aaron's ruling")
PENDING_ENGINEERING = AbsentQuantity(
    "PENDING_ENGINEERING",
    "defined and ruled, but the emitting plumbing has not landed")

# The token vocabulary is deliberately IDENTICAL to lane S2's
# `contracts.OverBudgetStatus` values, so a per-day platform status maps
# onto a per-path atom absence without a translation table inventing
# semantics. The two lanes agree by SPECIFICATION, not by import.
ABSENT_BY_TOKEN: Mapping[str, AbsentQuantity] = MappingProxyType({
    a.token: a for a in (NOT_APPLICABLE, NOT_APPLICABLE_NO_TRADE,
                         PENDING_RULING, PENDING_ENGINEERING)})


def _absent_or_nonneg_int(value, *, field: str):
    """Accept a non-negative int OR a typed AbsentQuantity. A raw None,
    a bool, a float or a negative int all refuse."""
    if isinstance(value, AbsentQuantity):
        if value.token not in ABSENT_BY_TOKEN:
            raise MCInputError("atom_absent_token_unknown",
                               f"{field}: {value.token!r}")
        return value
    if value is None:
        raise MCInputError(
            "atom_untyped_none",
            f"{field}: a bare None cannot say WHY the quantity is "
            "absent — use NOT_APPLICABLE / PENDING_RULING / "
            "PENDING_ENGINEERING")
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise MCInputError("atom_field_type_violation",
                           f"{field}={value!r} is not a non-negative int")
    return value


def _nonneg_int(value, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise MCInputError("atom_field_type_violation",
                           f"{field}={value!r} is not a non-negative int")
    return value


def _bool(value, *, field: str) -> bool:
    if not isinstance(value, bool):
        raise MCInputError("atom_field_type_violation",
                           f"{field}={value!r} is not a bool")
    return value


def _hex64(value, *, field: str) -> str:
    if not isinstance(value, str) or not _HEX64.match(value):
        raise MCInputError("atom_identity_digest_invalid",
                           f"{field} is not a 64-hex digest")
    return value


# --- 4. the atom ------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class SimulationPathObservation:
    """ONE simulated account path: one bootstrap world x one start phase.

    Every field is a RAW OBSERVED FACT or an identity binding. There is
    no derived-and-storable field (the R2.3 `payout_realized` boolean was
    DELETED — it is `payout_count > 0`, and a derivable field is a
    permanent forgery surface). Counting is EVENT-CALIBRE throughout:
    `payout_count` counts payout events, never cash.

    Cross-invariants are enforced at CONSTRUCTION, each with its own
    refusal code, so an impossible atom cannot exist even transiently."""

    # --- identity bindings ---
    prepared_digest: str
    lifecycle_config_digest: str
    world_index: int
    world_digest: str
    phase_offset: int
    platform: str
    engine: str
    scenario: str
    theta_channel: str
    master_seed: int
    # --- the observed result ---
    monthly_prop_operating_ev: float
    # --- raw day facts ---
    days_in_window: int
    offered_days: int
    executed_trade_days: int
    skips_n0: int
    payout_count: int
    winning_days: int
    # LITERAL threshold count: days whose AUTHORITATIVE net was at or above
    # the frozen $150 floor. This is NOT the platform's qualifying-day
    # counter (see `qualifying_days`) — Topstep excludes a payout-request
    # day from its own count even when the net clears $150, so the two are
    # genuinely different facts and are never conflated. Neither is a
    # frequency proxy (master plan N-D2 forbids that reading).
    days_profit_ge_150: int
    # The PLATFORM'S OWN qualifying-day counter increments, counted from
    # lane S2's tri-state `qualifying_day` flag. Phases with no qualifying
    # concept (evaluation / combine / dead / done) emit None and simply do
    # not increment; that is a real zero, not an unknown.
    qualifying_days: int
    exhausted: bool
    ambiguous_days: int
    attempts_used: int
    b2f_used: int
    contract_cap_hits: object            # int | AbsentQuantity
    e2_over_budget_days: object          # int | AbsentQuantity

    def __post_init__(self):
        _hex64(self.prepared_digest, field="prepared_digest")
        _hex64(self.lifecycle_config_digest,
               field="lifecycle_config_digest")
        _hex64(self.world_digest, field="world_digest")
        _nonneg_int(self.world_index, field="world_index")
        _nonneg_int(self.phase_offset, field="phase_offset")
        if self.platform not in PLATFORMS:
            raise MCInputError("atom_axis_violation",
                               f"platform={self.platform!r}")
        if self.engine not in ENGINES:
            raise MCInputError("atom_axis_violation",
                               f"engine={self.engine!r}")
        if self.scenario not in SCENARIOS:
            raise MCInputError("atom_axis_violation",
                               f"scenario={self.scenario!r}")
        if not isinstance(self.theta_channel, str) or \
                not self.theta_channel.startswith("theta_"):
            raise MCInputError("atom_axis_violation",
                               f"theta_channel={self.theta_channel!r}")
        if isinstance(self.master_seed, bool) or \
                not isinstance(self.master_seed, int):
            raise MCInputError("atom_field_type_violation",
                               f"master_seed={self.master_seed!r}")
        if isinstance(self.monthly_prop_operating_ev, bool) or \
                not isinstance(self.monthly_prop_operating_ev,
                               (int, float)) or \
                not math.isfinite(float(self.monthly_prop_operating_ev)):
            raise MCInputError(
                "atom_ev_non_finite",
                f"monthly_prop_operating_ev="
                f"{self.monthly_prop_operating_ev!r}")
        object.__setattr__(self, "monthly_prop_operating_ev",
                           float(self.monthly_prop_operating_ev))
        for name in ("days_in_window", "offered_days",
                     "executed_trade_days", "skips_n0", "payout_count",
                     "winning_days", "days_profit_ge_150",
                     "qualifying_days", "ambiguous_days", "attempts_used",
                     "b2f_used"):
            _nonneg_int(getattr(self, name), field=name)
        _bool(self.exhausted, field="exhausted")
        object.__setattr__(
            self, "contract_cap_hits",
            _absent_or_nonneg_int(self.contract_cap_hits,
                                  field="contract_cap_hits"))
        object.__setattr__(
            self, "e2_over_budget_days",
            _absent_or_nonneg_int(self.e2_over_budget_days,
                                  field="e2_over_budget_days"))

        # --- cross invariants, one code each ---
        if self.offered_days > self.days_in_window:
            raise MCInputError(
                "atom_offered_exceeds_window",
                f"offered_days={self.offered_days} > "
                f"days_in_window={self.days_in_window}")
        # ORDER MATTERS: the monotone chain is checked BEFORE the
        # skip/execution partition. `executed_trade_days > offered_days`
        # would otherwise always surface as a partition violation, and
        # the chain link would have no independently reachable code.
        chain = (("days_profit_ge_150", self.days_profit_ge_150),
                 ("winning_days", self.winning_days),
                 ("executed_trade_days", self.executed_trade_days),
                 ("offered_days", self.offered_days))
        for (lo_name, lo), (hi_name, hi) in zip(chain, chain[1:]):
            if lo > hi:
                raise MCInputError(
                    "atom_monotone_chain_violation",
                    f"{lo_name}={lo} > {hi_name}={hi} (frozen chain "
                    "days_profit_ge_150 <= winning_days <= "
                    "executed_trade_days <= offered_days)")
        if self.skips_n0 + self.executed_trade_days > self.offered_days:
            raise MCInputError(
                "atom_skip_execution_partition_violation",
                f"skips_n0={self.skips_n0} + executed_trade_days="
                f"{self.executed_trade_days} > offered_days="
                f"{self.offered_days}")
        if self.payout_count > self.days_in_window:
            raise MCInputError(
                "atom_payout_count_exceeds_window",
                f"payout_count={self.payout_count} > days_in_window="
                f"{self.days_in_window}")
        if self.qualifying_days > self.days_in_window:
            raise MCInputError(
                "atom_qualifying_days_exceed_window",
                f"qualifying_days={self.qualifying_days} > "
                f"days_in_window={self.days_in_window}")
        if self.ambiguous_days > self.offered_days:
            raise MCInputError(
                "atom_ambiguous_exceeds_offered",
                f"ambiguous_days={self.ambiguous_days} > offered_days="
                f"{self.offered_days}")
        if isinstance(self.contract_cap_hits, int) and \
                self.contract_cap_hits > self.executed_trade_days:
            raise MCInputError(
                "atom_contract_cap_exceeds_executed",
                f"contract_cap_hits={self.contract_cap_hits} > "
                f"executed_trade_days={self.executed_trade_days}")
        if not (1 <= self.attempts_used <= _orch.MAX_EVALUATION_STARTS):
            raise MCInputError(
                "atom_attempts_range_violation",
                f"attempts_used={self.attempts_used} outside "
                f"[1, {_orch.MAX_EVALUATION_STARTS}] (frozen MC SS4.3)")
        if self.exhausted and \
                self.attempts_used != _orch.MAX_EVALUATION_STARTS:
            raise MCInputError(
                "atom_exhaustion_attempts_inconsistent",
                f"exhausted=True but attempts_used="
                f"{self.attempts_used} != "
                f"{_orch.MAX_EVALUATION_STARTS}")
        if self.platform == "lucid" and self.b2f_used != 0:
            raise MCInputError(
                "atom_b2f_platform_violation",
                f"lucid has no Back2Funded action; b2f_used="
                f"{self.b2f_used}")
        # engine-conditional semantics of the E2 budget field
        if self.engine == "E1":
            if self.e2_over_budget_days is not NOT_APPLICABLE:
                raise MCInputError(
                    "atom_e2_field_engine_semantics",
                    "E1 has no sizing budget: e2_over_budget_days must "
                    "be NOT_APPLICABLE (permanently), got "
                    f"{self.e2_over_budget_days!r}")
        else:                                        # E2
            if self.e2_over_budget_days is NOT_APPLICABLE:
                raise MCInputError(
                    "atom_e2_field_engine_semantics",
                    "E2 DOES have a sizing budget: NOT_APPLICABLE is "
                    "wrong; use an int or PENDING_RULING")

    # --- identity helpers ---
    @property
    def key(self) -> tuple:
        """The (world, phase) Cartesian key this atom occupies."""
        return (self.world_index, self.phase_offset)


# --- 5. canonical serialisation + digests ----------------------------------

ATOM_FIELDS = tuple(f.name for f in
                    dataclasses.fields(SimulationPathObservation))


def atom_canonical_dict(atom: SimulationPathObservation) -> dict:
    """The atom's canonical JSON-shaped mapping. AbsentQuantity values
    render as their TOKEN — never `null`, never `0`, and the three
    tokens are distinguishable in the sealed bytes."""
    if type(atom) is not SimulationPathObservation:
        raise MCInputError("atom_type_violation",
                           f"{type(atom).__name__} is not an atom")
    out = {"schema": ATOM_SCHEMA}
    for name in ATOM_FIELDS:
        v = getattr(atom, name)
        out[name] = v.token if isinstance(v, AbsentQuantity) else v
    return out


def atom_from_canonical_dict(row: Mapping) -> SimulationPathObservation:
    """Inverse of `atom_canonical_dict` (used by the cold replay to load
    a sealed trace). Field-set exactness is enforced: an unknown key, a
    missing key or an extra key all refuse."""
    if not isinstance(row, Mapping):
        raise MCInputError("atom_row_schema_violation",
                           f"{type(row).__name__} is not a mapping")
    want = set(ATOM_FIELDS) | {"schema"}
    got = set(row)
    if got - want:
        raise MCInputError("atom_row_extra_field",
                           f"{sorted(got - want)}")
    if want - got:
        raise MCInputError("atom_row_missing_field",
                           f"{sorted(want - got)}")
    if row["schema"] != ATOM_SCHEMA:
        raise MCInputError("atom_row_schema_violation",
                           f"schema={row['schema']!r}")
    kwargs = {}
    for name in ATOM_FIELDS:
        v = row[name]
        if name in ("contract_cap_hits", "e2_over_budget_days") and \
                isinstance(v, str):
            if v not in ABSENT_BY_TOKEN:
                raise MCInputError("atom_absent_token_unknown",
                                   f"{name}={v!r}")
            v = ABSENT_BY_TOKEN[v]
        kwargs[name] = v
    return SimulationPathObservation(**kwargs)


def atom_digest(atom: SimulationPathObservation) -> str:
    """Per-atom canonical digest — the unit the cold replay compares."""
    return _sha256_text(canonical_json(atom_canonical_dict(atom)))


def atoms_to_jsonl(atoms: Iterable[SimulationPathObservation]) -> str:
    """The sealable raw-trace form: one canonical JSON object per line,
    newline separated, NO trailing newline. Digests are computed over
    these UNCOMPRESSED canonical bytes (D6)."""
    return "\n".join(canonical_json(atom_canonical_dict(a)) for a in atoms)


def atoms_from_jsonl(text: str) -> tuple:
    out = []
    for i, line in enumerate(text.split("\n")):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except ValueError as exc:                       # noqa: PERF203
            raise MCInputError("atom_row_schema_violation",
                               f"line {i}: {exc}") from exc
        out.append(atom_from_canonical_dict(row))
    return tuple(out)


def observations_digest(atoms: Sequence[SimulationPathObservation]) -> str:
    """LEVEL-1 flat digest: sha256 over the UNCOMPRESSED canonical JSONL
    bytes of ONE (run_label, combo, scenario) observation set."""
    return _sha256_text(atoms_to_jsonl(atoms))


def digest_of_digests(table: Mapping[str, str]) -> str:
    """LEVEL-2 container digest: sha256 over the canonical JSON of the
    {set_key -> level-1 digest} table."""
    for k, v in table.items():
        _hex64(v, field=f"trace_digests[{k}]")
    return _sha256_text(canonical_json(dict(table)))


# --- 6. the ONE narrow S2-seam adapter --------------------------------------

# The platform-authoritative day fields lane S2 emits on AccountEvent.
# NOTHING outside this adapter may read them (import-graph/AST pinned in
# tests/test_mc_atoms.py; the PRODUCER side — the platform state machines,
# the orchestrator, the account layer and platforms/authoritative.py — owns
# the facts and is exempt).
#
# N01 C2 LAYER 4: `phase` joined the required set. The adapter reads the
# phase because the qualifying-day tri-state is only meaningful RELATIVE to
# it: on a phase whose frozen ruleset HAS a qualifying-day concept
# (contracts.QUALIFYING_PHASES = {funded, xfa}) a `None` is not "no
# qualifying day", it is a MISSING FACT, and silently counting it as 0 is
# exactly the defect this layer closes.
SEAM_REQUIRED_FIELDS = ("day_net_usd", "phase", "account_generation",
                        "requested_n", "traded_n", "cap_applied")
# `qualifying_day` and `over_budget` are TRI-STATE by lane S2's design
# (None means "this ruleset has no such concept" / "the predicate is
# unruled"), so their absence is never a blanket refusal — it is a fact
# with a typed meaning, and WHICH None is legal depends on the phase
# (qualifying_day) and on the engine + traded state + the frozen ruling
# constant (over_budget). `over_budget_status` carries WHICH kind of None.
SEAM_TRISTATE_FIELDS = ("qualifying_day", "over_budget",
                        "over_budget_status")

# --- C3: the CONSUMER-SIDE E2 over-budget gate (independent second gate) ---
#
# Producer side (lane S2, contracts.AccountEvent.__post_init__) already
# refuses an emitted boolean while `contracts.OVER_BUDGET_PREDICATE_RULED`
# is False. That check lives at CONSTRUCTION time and a duck-typed event —
# or a legally constructed `AccountEvent` mutated afterwards, which is
# trivially possible because the dataclass is NOT frozen — walks straight
# past it. This adapter therefore re-derives the whole combination
# (ruling constant x engine x traded state x status token x value) from
# scratch, per event, and NEVER trusts construction.
#
# The pinned consumption rule while the predicate is UNRULED:
#   E2 + traded     -> over_budget is None      AND status == PENDING_RULING
#   E2 + no trade   -> over_budget is None      AND status ==
#                                                  NOT_APPLICABLE_NO_TRADE
#   E1 + traded     -> over_budget is None      AND status == NOT_APPLICABLE
#   E1 + no trade   -> over_budget is None      AND status ==
#                                                  NOT_APPLICABLE_NO_TRADE
#   ANY E2 boolean  -> REFUSED. It may never enter a formal count.
#
# FUTURE RULING (read this before touching the branch below): if Aaron ever
# flips OVER_BUDGET_PREDICATE_RULED to True, this adapter must NOT start
# accepting booleans by itself — the flip refuses with
# `platform_facts_over_budget_ruling_changed` until a NEW, EXPLICIT
# predicate implementation lands here together with its own tests. A ruling
# says the quantity is now defined; it does not say what THIS adapter
# should count, and inheriting a boolean silently would reopen exactly the
# forgery surface the typed absence was built to close.
E2_UNRULED_TOKEN = "PENDING_RULING"
NO_TRADE_TOKEN = "NOT_APPLICABLE_NO_TRADE"
E1_TRADED_TOKEN = "NOT_APPLICABLE"

_MISSING = object()


def _seam_get(event, name: str):
    return getattr(event, name, _MISSING)


def expected_over_budget_token(engine: str, traded_n: int) -> str:
    """The ONLY legal `over_budget_status` token for (engine, traded state)
    while the predicate is unruled.

    Transcribed from the frozen scope (MC SS3 scopes the over-budget
    disclosure to E2; a day with no position has no referent at all), NOT
    imported from the producer's mapping — the two lanes must agree by
    SPECIFICATION, so a producer-side drift is DETECTABLE here instead of
    being inherited."""
    if traded_n <= 0:
        return NO_TRADE_TOKEN
    return E1_TRADED_TOKEN if engine == "E1" else E2_UNRULED_TOKEN


def path_facts_from_events(events: Sequence, *, engine: str,
                           platform: str) -> Mapping:
    """THE ONLY reader of platform-authoritative day facts (D1-seam).

    Balance-difference derivation is FORBIDDEN here and everywhere else:
    it carries two confirmed defects (payout-day debits pollute the
    delta, and a cross-generation balance reset produces a phantom jump).
    When the authoritative fields are absent this adapter REFUSES
    deterministically (`platform_facts_absent`) — it never falls back.

    Until lane S2 (node N02) lands those fields, EVERY atom-producing
    path in the consumer therefore refuses. That is the intended
    fail-closed state, not a gap.

    `qualifying_day` is counted STRAIGHT from the platform's own tri-state
    flag — never re-derived as `day_net_usd >= 150`, which lane S2
    documents as wrong (a Topstep XFA payout-request day clearing $150 is
    NOT a qualifying day under frozen MC SS4.2). The separate
    `days_profit_ge_150` metric is the literal threshold count and is
    never presented as the qualifying-day count.

    N01 C2 LAYER 4 — the adapter reads the PHASE. On a phase whose frozen
    ruleset defines qualifying days at all (contracts.QUALIFYING_PHASES),
    a non-boolean `qualifying_day` is a MISSING FACT and refuses
    (`platform_facts_qualifying_absent`); on every other phase a value
    would invent a concept the ruleset does not have
    (`platform_facts_qualifying_phase_mismatch`). The R2.3 adapter did
    neither: it skipped a `None` silently, so a funded/xfa day with a real
    $10 net and an unemitted flag was counted as a hard zero.

    N01 C3 — the E2 over-budget combination is re-derived here per event
    (see the module block above `expected_over_budget_token`): no boolean
    may enter a formal count while the predicate is unruled, and the
    ruling constant itself is checked rather than assumed."""
    if engine not in ENGINES:
        raise MCInputError("atom_axis_violation", f"engine={engine!r}")
    if platform not in PLATFORMS:
        raise MCInputError("atom_axis_violation",
                           f"platform={platform!r}")
    # C3 gate 1 — the RULING CONSTANT, read LIVE from the frozen source of
    # truth (never copied into a literal here, which could drift out of
    # agreement in the dangerous direction). While it is False no boolean
    # is consumable; when it flips, THIS code is stale by construction and
    # says so instead of quietly inheriting a meaning nobody wrote down.
    ruled = _contracts.OVER_BUDGET_PREDICATE_RULED
    if not isinstance(ruled, bool):
        raise MCInputError(
            "platform_facts_over_budget_ruling_malformed",
            f"contracts.OVER_BUDGET_PREDICATE_RULED={ruled!r} is not a "
            "bool — the consumption rule cannot be evaluated")
    if ruled and engine == "E2":
        raise MCInputError(
            "platform_facts_over_budget_ruling_changed",
            "OVER_BUDGET_PREDICATE_RULED flipped to True: the E2 "
            "over-budget consumption rule pinned in this adapter was "
            "written for the UNRULED state and may not be extended by "
            "default. A new explicit predicate implementation plus its "
            "own tests must land here before any boolean is counted")
    qualifying_phases = _contracts.QUALIFYING_PHASES

    executed = 0
    payouts = 0
    winning = 0
    ge150 = 0
    qualifying = 0
    cap_hits = 0
    # C3: kept ONLY as a tripwire (see the tail of this function). Nothing
    # can increment it while the predicate is unruled.
    over_budget_days = 0
    prev_generation = None

    for i, ev in enumerate(events):
        for name in SEAM_REQUIRED_FIELDS:
            v = _seam_get(ev, name)
            if v is _MISSING or v is None:
                raise MCInputError(
                    "platform_facts_absent",
                    f"event {i}: {name} is "
                    f"{'absent' if v is _MISSING else 'None'} — the "
                    "platform-authoritative day facts (lane S2 / node "
                    "N02) have not landed; balance-difference "
                    "derivation is forbidden")

        net = _seam_get(ev, "day_net_usd")
        if isinstance(net, bool) or not isinstance(net, (int, float)) \
                or not math.isfinite(float(net)):
            raise MCInputError("platform_facts_malformed",
                               f"event {i}: day_net_usd={net!r}")
        net = float(net)

        gen = _seam_get(ev, "account_generation")
        if isinstance(gen, bool) or not isinstance(gen, int) or gen < 0:
            raise MCInputError("platform_facts_malformed",
                               f"event {i}: account_generation={gen!r}")
        if prev_generation is not None and gen < prev_generation:
            raise MCInputError(
                "platform_facts_generation_not_monotone",
                f"event {i}: account_generation {gen} < previous "
                f"{prev_generation} — generations only ever increment "
                "at a balance-reset boundary")
        prev_generation = gen

        req = _seam_get(ev, "requested_n")
        trd = _seam_get(ev, "traded_n")
        for nm, val in (("requested_n", req), ("traded_n", trd)):
            if isinstance(val, bool) or not isinstance(val, int) or \
                    val < 0:
                raise MCInputError("platform_facts_malformed",
                                   f"event {i}: {nm}={val!r}")
        if trd > req:
            raise MCInputError(
                "platform_facts_sizing_incoherent",
                f"event {i}: traded_n={trd} > requested_n={req}")

        cap = _seam_get(ev, "cap_applied")
        if not isinstance(cap, bool):
            raise MCInputError("platform_facts_malformed",
                               f"event {i}: cap_applied={cap!r}")

        phase = _seam_get(ev, "phase")
        if not isinstance(phase, str) or not phase:
            raise MCInputError("platform_facts_malformed",
                               f"event {i}: phase={phase!r}")

        # C2 LAYER 4 — the qualifying-day tri-state is judged AGAINST the
        # phase, never skipped. `None` on a funded/xfa day is a missing
        # fact, not a zero; a value on any other phase invents a concept.
        qual = _seam_get(ev, "qualifying_day")
        qual_present = qual is not _MISSING and qual is not None
        if qual_present and not isinstance(qual, bool):
            raise MCInputError("platform_facts_malformed",
                               f"event {i}: qualifying_day={qual!r}")
        if phase in qualifying_phases:
            if not isinstance(qual, bool):
                raise MCInputError(
                    "platform_facts_qualifying_absent",
                    f"event {i}: phase={phase!r} has a frozen "
                    f"qualifying-day rule but qualifying_day="
                    f"{'absent' if qual is _MISSING else repr(qual)} is "
                    "not a bool — a non-boolean here is a MISSING FACT "
                    "and counting it as 0 would understate the "
                    "platform's own counter")
            if qual:
                qualifying += 1
        elif qual_present:
            raise MCInputError(
                "platform_facts_qualifying_phase_mismatch",
                f"event {i}: phase={phase!r} has no frozen qualifying-day "
                f"concept (frozen set {sorted(qualifying_phases)}) yet "
                f"carries qualifying_day={qual!r}; both True and False "
                "would manufacture a fact the ruleset does not define")

        # --- C3: the E2 over-budget combination, re-derived per event ---
        ob = _seam_get(ev, "over_budget")
        status = _seam_get(ev, "over_budget_status")
        status_token = (None if status is _MISSING or status is None
                        else str(getattr(status, "value", status)))
        if status_token is not None and status_token not in ABSENT_BY_TOKEN:
            raise MCInputError(
                "platform_facts_malformed",
                f"event {i}: over_budget_status={status_token!r} is not "
                f"a known absence token {sorted(ABSENT_BY_TOKEN)}")
        # gate 2 — the TYPED status is mandatory, on every event of every
        # engine. Without it there is no statement about WHY the boolean
        # is absent, and "absent" would be indistinguishable from
        # "measured, never exceeded".
        if status_token is None:
            raise MCInputError(
                "platform_facts_over_budget_status_absent",
                f"event {i}: over_budget_status is "
                f"{'absent' if status is _MISSING else 'None'} — the "
                "typed E2 over-budget state is mandatory (engine="
                f"{engine}, traded_n={trd})")
        # gate 3 — the status must be the one the (engine, traded state)
        # combination allows. An event that says PENDING_RULING on a
        # no-trade day, or NOT_APPLICABLE on an E2 traded day, is
        # incoherent evidence whichever side produced it.
        want_token = expected_over_budget_token(engine, trd)
        if status_token != want_token:
            raise MCInputError(
                "platform_facts_over_budget_status_inconsistent",
                f"event {i}: engine={engine} traded_n={trd} requires "
                f"over_budget_status={want_token!r}, got "
                f"{status_token!r}")
        # gate 4 — the VALUE. No engine may carry a boolean today; the E1
        # and E2 refusals keep their distinct codes because they say
        # different things (E1: permanently out of scope; E2: defined but
        # unruled).
        if ob is not _MISSING and ob is not None:
            if engine == "E1":
                raise MCInputError(
                    "platform_facts_engine_semantics",
                    f"event {i}: E1 carries over_budget={ob!r}; the "
                    "frozen MC SS3 over-budget disclosure is E2-scoped, "
                    "so an E1 boolean would manufacture evidence")
            raise MCInputError(
                "platform_facts_e2_over_budget_boolean_unruled",
                f"event {i}: E2 carries over_budget={ob!r} while "
                "OVER_BUDGET_PREDICATE_RULED is False. MC SS3 mandates "
                "the disclosure but defines no predicate, so a boolean "
                "has no agreed meaning and MUST NOT enter a formal "
                f"count (status={status_token!r} says PENDING_RULING)")

        gross = getattr(ev, "payout_gross", 0.0)
        if isinstance(gross, bool) or not isinstance(gross, (int, float)):
            raise MCInputError("platform_facts_malformed",
                               f"event {i}: payout_gross={gross!r}")
        if float(gross) > 0.0:
            payouts += 1

        if trd > 0:
            executed += 1
        if net > 0.0:
            winning += 1
        if net >= QUALIFYING_DAY_MIN_PROFIT_USD:
            ge150 += 1
        if cap:
            cap_hits += 1

    # C3 — the per-path quantity. E1 has no budget concept at all; E2 has
    # one but no predicate, so the count is TYPED-ABSENT unconditionally.
    # It is NOT derived from an accumulator: an accumulator initialised to
    # 0 turns an EMPTY E2 event stream into a formal "0 over-budget days"
    # (measured, never exceeded) without a single observation, which is
    # the same forgery in a different disguise.
    if engine == "E1":
        e2_days = NOT_APPLICABLE
    else:
        e2_days = PENDING_RULING
    if over_budget_days:                                  # pragma: no cover
        # unreachable: gate 4 refuses every boolean, so nothing can
        # increment the accumulator. Kept as a tripwire — if a future
        # ruled-predicate implementation starts counting, it must ALSO
        # revisit the typed-absence decision above rather than leaving a
        # counted value stranded here.
        raise MCInputError(
            "platform_facts_over_budget_count_stranded",
            f"{over_budget_days} counted over-budget day(s) were formed "
            "while the quantity is reported as typed-absent")

    return MappingProxyType({
        "event_days": len(events),
        "executed_trade_days": executed,
        "payout_count": payouts,
        "winning_days": winning,
        "days_profit_ge_150": ge150,
        "qualifying_days": qualifying,
        "contract_cap_hits": cap_hits,
        "e2_over_budget_days": e2_days,
    })


# --- 7. lifecycle_config_digest --------------------------------------------

def harvest_frozen_constants() -> dict:
    """MECHANICALLY sweep the result-relevant modules for UPPER_CASE
    frozen constants. NO hand-written whitelist exists: a constant added
    to any harvested module enters the digest AUTOMATICALLY. A value with
    no canonical encoding REFUSES rather than being silently skipped."""
    out: dict = {}
    for modname in HARVESTED_CONSTANT_MODULES:
        mod = importlib.import_module(modname)
        for name, value in vars(mod).items():
            if not _UPPER_CONST.match(name):
                continue
            key = f"{modname}:{name}"
            if key in FROZEN_CONSTANT_EXCLUSIONS:
                continue
            out[key] = jsonable(value)
    return out


def _frozen_hash(rel: str) -> str:
    from itsf import guards as g
    try:
        return g.FROZEN_HASHES[rel]
    except KeyError as exc:                             # pragma: no cover
        raise MCInputError("lifecycle_config_anchor_missing",
                           f"{rel} not registered in guards."
                           "FROZEN_HASHES") from exc


def lifecycle_config_preimage(cfg, *, engine: str, scenario: str,
                              theta_channel: str) -> dict:
    """The COMPLETE preimage of `lifecycle_config_digest`.

    `LifecycleConfig` fields are enumerated with `dataclasses.fields()` —
    NEVER a hand-written list — so a field added by lane S2 enters the
    digest automatically. Frozen module constants are harvested the same
    way. The platform-parameter anchors are the ALREADY-FROZEN
    `guards.FROZEN_HASHES` entries (nothing new is invented)."""
    if not isinstance(cfg, _orch.LifecycleConfig):
        raise MCInputError("lifecycle_config_type_violation",
                           f"{type(cfg).__name__} is not a "
                           "LifecycleConfig")
    if engine not in ENGINES:
        raise MCInputError("atom_axis_violation", f"engine={engine!r}")
    if scenario not in SCENARIOS:
        raise MCInputError("atom_axis_violation",
                           f"scenario={scenario!r}")
    fields = {f.name: jsonable(getattr(cfg, f.name))
              for f in dataclasses.fields(cfg)}
    return {
        "schema": LIFECYCLE_CONFIG_SCHEMA,
        "lifecycle_config_fields": fields,
        "frozen_constants": harvest_frozen_constants(),
        "engine": engine,
        "scenario": scenario,
        "theta_channel": theta_channel,
        "payout_path_id": PAYOUT_PATH_ID,
        "platform_params_snapshot_sha256":
            _frozen_hash("gate1/platform_params.yaml"),
        "snapshot_manifest_sha256":
            _frozen_hash("gate1/snapshots/2026-07-28/"
                         "snapshot_manifest_v5.json"),
        "method_spec_sha256": _frozen_hash("MC_METHOD_SPEC.md"),
        "orchestrator_algo_version": ORCHESTRATOR_ALGO_VERSION,
        "replay_algo_version": REPLAY_ALGO_VERSION,
        "method_version": METHOD_VERSION,
        "rng_spec": RNG_SPEC,
    }


def validate_lifecycle_config_preimage(preimage: Mapping) -> dict:
    """Exact-field-set validation. Unknown, missing and extra keys each
    refuse with their OWN code (D2)."""
    if not isinstance(preimage, Mapping):
        raise MCInputError("lifecycle_config_preimage_schema",
                           f"{type(preimage).__name__} is not a mapping")
    want = set(LIFECYCLE_CONFIG_PREIMAGE_FIELDS)
    got = set(preimage)
    unknown = sorted(k for k in got - want if not isinstance(k, str))
    if unknown:
        raise MCInputError("lifecycle_config_preimage_unknown_field",
                           f"non-string keys {unknown}")
    missing = sorted(want - got)
    if missing:
        raise MCInputError("lifecycle_config_preimage_missing_field",
                           f"{missing}")
    extra = sorted(got - want)
    if extra:
        raise MCInputError("lifecycle_config_preimage_extra_field",
                           f"{extra}")
    if preimage["schema"] != LIFECYCLE_CONFIG_SCHEMA:
        raise MCInputError("lifecycle_config_preimage_schema",
                           f"schema={preimage['schema']!r}")
    return dict(preimage)


def lifecycle_config_digest(preimage: Mapping) -> str:
    return _sha256_text(canonical_json(
        validate_lifecycle_config_preimage(preimage)))


def lifecycle_config_digest_for(cfg, *, engine: str, scenario: str,
                                theta_channel: str) -> str:
    return lifecycle_config_digest(
        lifecycle_config_preimage(cfg, engine=engine, scenario=scenario,
                                  theta_channel=theta_channel))


def combo_label(platform: str, engine: str, sizing_policy: str) -> str:
    """The `combo` string is a DISPLAY LABEL ONLY (D2). It is rendered
    FROM the authoritative fields and is never parsed back into them."""
    return f"{platform}|{engine}|{sizing_policy}"


def observation_set_key(run_label: str, combo: str, scenario: str) -> str:
    """The level-1 trace key: one observation set per
    (run_label, combo, scenario)."""
    return f"{run_label}/{combo}/{scenario}"


# --- 8. key-grid helpers (the SINGLE implementation C1 and C2 share) -------

def expected_key_grid(B: int, legal_phase_support: Sequence[int]) -> frozenset:
    """The COMPLETE Cartesian key set: range(B) x legal_phase_support.

    `legal_phase_support` may come ONLY from the prepared authority
    (`prepared.calendar.first_month_offsets`). No caller may supply an
    `expected_n` scalar — the count is a CONSEQUENCE of this grid."""
    if isinstance(B, bool) or not isinstance(B, int) or B <= 0:
        raise MCInputError("key_grid_scale_invalid", f"B={B!r}")
    support = tuple(legal_phase_support)
    if not support:
        raise MCInputError("key_grid_support_empty",
                           "legal_phase_support is empty")
    for p in support:
        if isinstance(p, bool) or not isinstance(p, int) or p < 0:
            raise MCInputError("key_grid_support_invalid", f"{p!r}")
    if len(set(support)) != len(support):
        raise MCInputError("key_grid_support_duplicate", f"{support}")
    return frozenset((w, p) for w in range(B) for p in support)


def reduce_actual_keys(atoms: Sequence[SimulationPathObservation]) -> dict:
    """Reduce the ACTUAL execution trace to its key structure.

    Returns `counts` (key -> occurrences) and `actual_phase_keys_by_world`
    (world_index -> ordered tuple of executed phase offsets). The M
    exhaustive-support certificate is reduced from THIS — never from a
    declared M scalar."""
    counts: dict = {}
    by_world: dict = {}
    for a in atoms:
        if type(a) is not SimulationPathObservation:
            raise MCInputError("atom_type_violation",
                               f"{type(a).__name__} is not an atom")
        counts[a.key] = counts.get(a.key, 0) + 1
        by_world.setdefault(a.world_index, []).append(a.phase_offset)
    return {
        "counts": counts,
        "actual_phase_keys_by_world": {
            w: tuple(ps) for w, ps in sorted(by_world.items())},
    }


def check_key_grid(atoms: Sequence[SimulationPathObservation], *, B: int,
                   legal_phase_support: Sequence[int],
                   where: str = "") -> dict:
    """C1/C2 SHARED check. Four independent refusal codes:

      key_grid_duplicate     a key occurs more than once;
      key_grid_substitution  missing AND extra keys co-occur (a swap —
                             a count-only check would miss it);
      key_grid_missing       keys absent with nothing extra;
      key_grid_extra         keys present outside the legal grid.
    """
    expected = expected_key_grid(B, legal_phase_support)
    reduced = reduce_actual_keys(atoms)
    counts = reduced["counts"]
    dupes = sorted(k for k, n in counts.items() if n > 1)
    if dupes:
        raise MCInputError("key_grid_duplicate",
                           f"{where}{dupes[:3]} occur more than once")
    actual = frozenset(counts)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing and extra:
        raise MCInputError(
            "key_grid_substitution",
            f"{where}missing={missing[:3]} extra={extra[:3]} — a "
            "substituted key keeps the count intact and must never pass")
    if missing:
        raise MCInputError("key_grid_missing",
                           f"{where}{len(missing)} absent: {missing[:3]}")
    if extra:
        raise MCInputError("key_grid_extra",
                           f"{where}{len(extra)} outside the legal grid: "
                           f"{extra[:3]}")
    return reduced


# --- 9. reductions (THE single derivation of every downstream number) ------

def percentile_linear(sorted_values: Sequence[float], q: float) -> float:
    """Type-7 / numpy-'linear' quantile, in numpy's EVALUATION ORDER.

    Written in plain float arithmetic (not numpy) ON PURPOSE: the
    independent cold reducer implements the SAME specification without
    sharing a line of code, and the two must agree BITWISE.

    N01 C5 — the estimator was always type-7; what moved is the
    FLOATING-POINT EVALUATION ORDER, which is part of the specification
    the moment "bitwise" is claimed. numpy's `_lerp` is a two-branch
    function:

        t <  0.5 :  a + (b - a) * t
        t >= 0.5 :  b - (b - a) * (1 - t)

    (the second branch keeps the result monotone and exact at t == 1).
    The R2.3 single-expression form disagreed with `numpy.percentile(...,
    method="linear")` in the last ULP on EVERY t >= 0.5 sample — the
    measured failure mode, reproduced in
    tests/test_mc_atoms.py::test_percentile_is_bitwise_equal_to_numpy.
    Both branches are transcribed here from that specification; the cold
    reducer transcribes the same two branches independently, and the two
    implementations still share no helper (double-reducer independence
    contract, unchanged)."""
    n = len(sorted_values)
    if n == 0:
        raise MCInputError("epistemic_samples_invalid", "empty sample")
    if n == 1:
        return float(sorted_values[0])
    h = (n - 1) * (float(q) / 100.0)
    lo = math.floor(h)
    hi = math.ceil(h)
    if lo == hi:
        return float(sorted_values[int(h)])
    t = h - lo
    a = float(sorted_values[lo])
    b = float(sorted_values[hi])
    if t < 0.5:
        return a + (b - a) * t
    return b - (b - a) * (1.0 - t)


def mean_of(values: Sequence[float]) -> float:
    """Arithmetic mean, summed in the GIVEN order (the order is part of
    the spec so the two reducers agree bitwise).

    NUMERICAL PROVENANCE (N-D2, pending Aaron's ratification): the R2.3
    implementation delegated to `numpy.mean` (pairwise summation); this
    is a canonicalised pure-float sequential sum. The ESTIMATOR FAMILY is
    unchanged — same quantity, same definition — but the ULP-level result
    can differ from the numpy era (measured on synthetic samples: 27-48%
    not bit-identical to `numpy.mean`, the rate depending on the sample
    family, the discrepancy always at ULP magnitude). Not re-litigated in
    this node: the implementation stays as-is and the behaviour change is
    logged for Aaron's retrospective ratification (master plan N-D2)."""
    n = len(values)
    if n == 0:
        raise MCInputError("epistemic_samples_invalid", "empty sample")
    total = 0.0
    for v in values:
        total += float(v)
    return total / n


def stderr_of(values: Sequence[float]) -> float:
    """Within-set standard error: sqrt(sum((x-mean)^2)/(n-1))/sqrt(n),
    accumulated in the GIVEN order.

    TWO DIFFERENT DEGENERATE CASES, deliberately answered differently
    (N01 fix D-2):

      n == 0  UNDEFINED -> refuses, exactly like `mean_of`. The empty set
              has no dispersion to report, and answering 0.0 would let MC
              SS5 rule (d) (`MCSE <= 10% of between-world SD`) pass for
              free on a sample that does not exist. An empty world domain
              is already unreachable through the key grid; this is the
              honest answer at the primitive, not a reachability claim.
      n == 1  ZERO by definition of the ddof-1 estimator: a single
              observation has no within-set variation to estimate. This
              is a real measured value, not an absence, and it stays 0.0.

    NUMERICAL PROVENANCE (N-D2, pending Aaron's ratification): same story
    as `mean_of` — the numerical implementation moved from numpy to a
    canonicalised pure float accumulation at R2.3/N01, the estimator
    family did not change, and the ULP-level behaviour change (measured
    on synthetic samples: 16-31% not bit-identical to `numpy.std(ddof=1)
    / sqrt(n)`, rate sample-family dependent, always at ULP magnitude)
    awaits Aaron's retrospective ratification. NOT silently re-changed in
    this node.
    """
    n = len(values)
    if n == 0:
        raise MCInputError(
            "epistemic_samples_invalid",
            "standard error of an empty sample is undefined, not zero")
    if n == 1:
        return 0.0
    m = mean_of(values)
    acc = 0.0
    for v in values:
        d = float(v) - m
        acc += d * d
    return math.sqrt(acc / (n - 1)) / math.sqrt(n)


def sample_sd(values: Sequence[float]) -> float:
    """Sample SD (ddof=1) in the GIVEN order.

    Same two-case discipline as `stderr_of`: n == 0 is UNDEFINED and
    refuses (a zero between-world SD is the numerator of rule (d) and
    must never be manufactured from nothing); n == 1 is a genuine 0.0.

    NUMERICAL PROVENANCE (N-D2, pending Aaron's ratification): the
    numerical implementation moved from numpy to a canonicalised pure
    float accumulation at R2.3/N01; the estimator family (ddof=1 sample
    SD) is unchanged and the ULP-level behaviour change (measured on
    synthetic samples: 18-33% not bit-identical to `numpy.std(ddof=1)`,
    rate sample-family dependent, always at ULP magnitude) awaits
    Aaron's retrospective ratification. NOT silently re-changed in this
    node."""
    n = len(values)
    if n == 0:
        raise MCInputError(
            "epistemic_samples_invalid",
            "sample SD of an empty sample is undefined, not zero")
    if n == 1:
        return 0.0
    m = mean_of(values)
    acc = 0.0
    for v in values:
        d = float(v) - m
        acc += d * d
    return math.sqrt(acc / (n - 1))


# --- declare-and-verify comparison (N01 fix D-1) ---------------------------

def strict_scalar_equal(got, expected) -> bool:
    """Type-EXACT value equality for a declared-vs-derived scalar.

    `True == 1.0` and `1 == 1.0` are both TRUE in Python, so a plain `!=`
    check lets a bool or an int impersonate a derived float whenever the
    derived value happens to be 1.0 / 0.0. `bool` is a subclass of `int`,
    so `isinstance` cannot separate them either — the only reliable
    discriminator is `type(...) is type(...)`.

    "bool smuggled in as a number" is a failure class this project has
    closed repeatedly (R2.3 `epistemic_samples_invalid`); it must not
    reopen just because the samples became derived rather than
    caller-supplied."""
    return type(got) is type(expected) and got == expected


def strict_float_sequence_equal(got, expected) -> bool:
    """Element-wise type-exact comparison for derived sample vectors.

    Both sides must be tuples of the same length, and EVERY element on
    both sides must be a plain `float` — a `True`/`1` in the declared
    vector is refused even where it compares equal."""
    if type(got) is not tuple or type(expected) is not tuple:
        return False
    if len(got) != len(expected):
        return False
    for g, e in zip(got, expected):
        if type(g) is not float or type(e) is not float:
            return False
        if g != e:
            return False
    return True


def reduce_world_evs(atoms: Sequence[SimulationPathObservation]) -> dict:
    """world_index -> the ordered per-phase EV list (phase ascending)."""
    by_world: dict = {}
    for a in atoms:
        by_world.setdefault(a.world_index, []).append(
            (a.phase_offset, a.monthly_prop_operating_ev))
    return {w: [ev for _p, ev in sorted(rows)]
            for w, rows in sorted(by_world.items())}


def reduce_world_means(atoms: Sequence[SimulationPathObservation]) -> tuple:
    """Per-world MEAN monthly prop_operating EV, ordered by world index."""
    evs = reduce_world_evs(atoms)
    return tuple(mean_of(evs[w]) for w in sorted(evs))


def reduce_within_world_ses(atoms: Sequence[SimulationPathObservation]
                            ) -> tuple:
    evs = reduce_world_evs(atoms)
    return tuple(stderr_of(evs[w]) for w in sorted(evs))


def reduce_feasibility_counts(atoms: Sequence[SimulationPathObservation]
                              ) -> dict:
    """RAW feasibility metrics — counts and shares only. NO boolean, NO
    threshold, NO gate (D7: the metric->verdict reduction rule is
    Aaron's). Quantities whose observation is absent stay TYPED absent
    and are reported as their token, never as 0."""
    n = len(atoms)
    if n == 0:
        raise MCInputError("feasibility_observations_incomplete",
                           "no observations")
    offered = sum(a.offered_days for a in atoms)

    def _sum_or_absent(name: str):
        vals = [getattr(a, name) for a in atoms]
        absent = [v for v in vals if isinstance(v, AbsentQuantity)]
        if absent:
            tokens = sorted({v.token for v in absent})
            if len(tokens) > 1:
                raise MCInputError(
                    "feasibility_absent_semantics_mixed",
                    f"{name}: mixed absence semantics {tokens} in one "
                    "observation set")
            return ABSENT_BY_TOKEN[tokens[0]]
        return sum(vals)

    return {
        "n_paths": n,
        "payout_event_paths": sum(1 for a in atoms if a.payout_count > 0),
        "total_payout_events": sum(a.payout_count for a in atoms),
        "total_skips_n0": sum(a.skips_n0 for a in atoms),
        "total_offered": offered,
        "total_executed_trade_days":
            sum(a.executed_trade_days for a in atoms),
        "total_winning_days": sum(a.winning_days for a in atoms),
        "total_days_profit_ge_150":
            sum(a.days_profit_ge_150 for a in atoms),
        "total_qualifying_days": sum(a.qualifying_days for a in atoms),
        "total_ambiguous_days": sum(a.ambiguous_days for a in atoms),
        "exhausted_paths": sum(1 for a in atoms if a.exhausted),
        "total_b2f_used": sum(a.b2f_used for a in atoms),
        "total_contract_cap_hits": _sum_or_absent("contract_cap_hits"),
        "total_e2_over_budget_days": _sum_or_absent("e2_over_budget_days"),
        "payout_event_path_share": sum(
            1 for a in atoms if a.payout_count > 0) / n,
        "exhausted_share": sum(1 for a in atoms if a.exhausted) / n,
        "ambiguous_share": (sum(a.ambiguous_days for a in atoms) / offered
                            if offered else 0.0),
    }


# --- 9b. the container ------------------------------------------------------

@dataclass(frozen=True)
class ObservationSet:
    """ALL atoms of ONE (run_label, combo, scenario), declare-and-verify.

    `__post_init__` is the in-type reducer: it recomputes the level-1
    digest and the complete key grid from the atoms themselves and
    refuses any disagreement, so a tampered/declared digest cannot
    travel. Identity fields are cross-checked against EVERY atom."""
    run_label: str
    platform: str
    engine: str
    scenario: str
    theta_channel: str
    sizing_policy: str
    B: int
    master_seed: int
    prepared_digest: str
    lifecycle_config_digest: str
    legal_phase_support: tuple
    atoms: tuple
    observations_digest: str

    def __post_init__(self):
        object.__setattr__(self, "atoms", tuple(self.atoms))
        object.__setattr__(self, "legal_phase_support",
                           tuple(int(p) for p in self.legal_phase_support))
        for a in self.atoms:
            if type(a) is not SimulationPathObservation:
                raise MCInputError("atom_type_violation",
                                   f"{type(a).__name__} in observation "
                                   "set")
        if isinstance(self.B, bool) or not isinstance(self.B, int) \
                or self.B <= 0:
            raise MCInputError("key_grid_scale_invalid", f"B={self.B!r}")
        _hex64(self.prepared_digest, field="prepared_digest")
        _hex64(self.lifecycle_config_digest,
               field="lifecycle_config_digest")
        # identity binding: every atom must carry THIS set's identity
        for a in self.atoms:
            mismatch = []
            if a.prepared_digest != self.prepared_digest:
                mismatch.append("prepared_digest")
            if a.platform != self.platform:
                mismatch.append("platform")
            if a.engine != self.engine:
                mismatch.append("engine")
            if a.scenario != self.scenario:
                mismatch.append("scenario")
            if a.theta_channel != self.theta_channel:
                mismatch.append("theta_channel")
            if a.master_seed != self.master_seed:
                mismatch.append("master_seed")
            if mismatch:
                raise MCInputError(
                    "atom_binding_mismatch",
                    f"{self.run_label}/{self.scenario} atom "
                    f"{a.key}: {mismatch}")
            if a.lifecycle_config_digest != self.lifecycle_config_digest:
                raise MCInputError(
                    "lifecycle_config_digest_mismatch:atom",
                    f"{self.run_label}/{self.scenario} atom {a.key} "
                    f"carries {a.lifecycle_config_digest[:12]} != set "
                    f"{self.lifecycle_config_digest[:12]}")
        # C1: complete Cartesian key grid (SAME helper C2 uses)
        check_key_grid(self.atoms, B=self.B,
                       legal_phase_support=self.legal_phase_support,
                       where=f"{self.run_label}/{self.scenario}: ")
        # in-type reducer: recompute the declared digest
        want = observations_digest(self.atoms)
        if self.observations_digest != want:
            raise MCInputError(
                "observation_set_digest_mismatch",
                f"declared {str(self.observations_digest)[:12]} != "
                f"recomputed {want[:12]}")

    # --- derived views (the ONLY source downstream may read) ---
    @property
    def M(self) -> int:
        """Start-phase count ACTUALLY executed — a CONSEQUENCE of the
        legal support, never a caller-declared scalar."""
        return len(self.legal_phase_support)

    @property
    def combo(self) -> str:
        return combo_label(self.platform, self.engine, self.sizing_policy)

    @property
    def set_key(self) -> str:
        return observation_set_key(self.run_label, self.combo,
                                   self.scenario)

    def world_digests(self) -> tuple:
        """Ordered per-world content digests (one per world index)."""
        seen: dict = {}
        for a in self.atoms:
            prev = seen.setdefault(a.world_index, a.world_digest)
            if prev != a.world_digest:
                raise MCInputError(
                    "world_content_binding_mismatch",
                    f"world {a.world_index} carries two digests "
                    f"{prev[:12]} / {a.world_digest[:12]}")
        return tuple(seen[w] for w in sorted(seen))

    def to_jsonl(self) -> str:
        return atoms_to_jsonl(self.atoms)

    def world_means(self) -> tuple:
        return reduce_world_means(self.atoms)

    def within_world_ses(self) -> tuple:
        return reduce_within_world_ses(self.atoms)

    def feasibility_counts(self) -> dict:
        return reduce_feasibility_counts(self.atoms)

    def actual_phase_keys_by_world(self) -> dict:
        return reduce_actual_keys(self.atoms)["actual_phase_keys_by_world"]

    def atom_digest_table(self) -> dict:
        """key -> per-atom canonical digest (the cold-replay unit)."""
        return {a.key: atom_digest(a) for a in self.atoms}

    def conditional_aleatoric_evs(self, world_index: int) -> tuple:
        """The M attempt EVs INSIDE one fixed world (MC SS5 conditional
        aleatoric), reduced from the SAME atoms.

        NOTE (D7): this slices a world the CALLER names. No fixed-world
        SELECTION rule exists here — that ruling is Aaron's (master plan
        N-D2) and inventing one would be a decision leak."""
        evs = reduce_world_evs(self.atoms)
        if world_index not in evs:
            raise MCInputError("aleatoric_world_absent",
                               f"world {world_index!r} not in trace")
        return tuple(evs[world_index])

    def total_predictive_evs(self) -> tuple:
        """The B x M mixture (MC SS5 total_predictive), reduced from the
        SAME atoms, ordered (world, phase)."""
        return tuple(a.monthly_prop_operating_ev
                     for a in sorted(self.atoms, key=lambda x: x.key))

    @staticmethod
    def from_atoms(atoms, *, run_label, platform, engine, scenario,
                   theta_channel, sizing_policy, B, master_seed,
                   prepared_digest, lifecycle_config_digest,
                   legal_phase_support) -> "ObservationSet":
        """The ONLY constructor helper. The digest is COMPUTED here, so
        no caller ever supplies one; `__post_init__` recomputes it again
        anyway (declare-and-verify holds for this path too)."""
        atoms = tuple(atoms)
        return ObservationSet(
            run_label=run_label, platform=platform, engine=engine,
            scenario=scenario, theta_channel=theta_channel,
            sizing_policy=sizing_policy, B=int(B),
            master_seed=int(master_seed),
            prepared_digest=prepared_digest,
            lifecycle_config_digest=lifecycle_config_digest,
            legal_phase_support=tuple(legal_phase_support), atoms=atoms,
            observations_digest=observations_digest(atoms))
