"""Authoritative day-fact helpers for the platform state machines (N02/D5).

Two jobs, both deliberately thin:

1. `over_budget_status_for` — the single place that maps a day's traded
   position onto the typed E2 over-budget state (frozen text mandates the
   E2 disclosure and defines no predicate; see contracts.OverBudgetStatus).

2. `verify_event_stream` — THE production-chain fact gate. It VERIFIES an
   emitted event stream and never returns a value, a statistic, or a
   derived quantity. The MC consumer calls it in `_run_path_atom` BEFORE
   any atom reduction, so a malformed stream can never reach a reducer.
   `check_event_facts` is the older violation-COLLECTING form of the same
   rules, retained for tests that want the whole list; production semantics
   are `verify_event_stream`'s.

WHY A SEPARATE STREAM VERIFIER AT ALL. `contracts.AccountEvent` is a
MUTABLE dataclass and is mutated after construction by design (the
orchestrator relabels `ev.day` to the template-calendar id and appends to
`ev.notes`). Construction-time validation is therefore necessary but NOT
sufficient: any post-construction assignment bypasses it. This module
re-derives every rule from the object as the consumer will actually see
it, assuming nothing about how it was built.

THE day-net/balance/payout IDENTITY — SCOPE (frozen scope, N02/D5-4):

        day_net_usd == balance - prev_balance + payout_gross

is a HARD rule with an explicitly bounded domain, never a warning and
never optional. It applies to a PAIR of adjacent events and is SKIPPED
only under these enumerated, individually justified conditions:

  (S1) STREAM HEAD — `prev is None`. The first event has no predecessor,
       and the account's opening balance is a platform constant that no
       event carries; there is nothing to difference against. Anything
       inside that day is still checked by the per-event rules.
  (S2) GENERATION CHANGE — `prev.account_generation != ev.account_generation`.
       Every generation bump marks a BALANCE-RESET boundary: the balance
       was REPLACED (evaluation->funded, Combine reset, Combine pass->XFA,
       Back2Funded, new Combine), so `balance - prev_balance` is a phantom
       with no relation to any day's trading. This is precisely why the
       generation field exists — it makes the break DETECTABLE instead of
       silent, and the adjacent rules (monotone, jump <= 1, and the
       no-omission battery in tests) keep it from being abusable as an
       escape hatch: a stream cannot dodge the identity without also
       claiming a reset, and a claimed reset that did not happen is caught
       by the battery's converse test.
  (S3) LEGACY / MIGRATION EVENT on either side — `day_net_usd is None`
       (see contracts.fact_layer_active). Under `verify_event_stream` this
       case is unreachable: such an event is rejected outright by
       AUTH_FACTS_MISSING before the pair is ever formed. It exists only
       for `check_event_facts(require_facts=False)`, the mixed-stream
       inspection form.

NO OTHER SKIP EXISTS, and that is a checkable claim rather than a hope:
the identity's domain is exactly "the balance moved for a reason the day
itself explains". Every balance mutation site in lucid.py / topstep.py is
either (a) a trading settlement folded into `day_net_usd` (including the
R1 breach settlement, which is a same-day, same-generation move), (b) the
payout gross deduction carried by `payout_gross`, or (c) a reset to a
start constant, which bumps the generation. Fees never touch a sim
balance on either platform. tests/test_platform_authoritative_events.py
pins that inventory structurally, so a NEW mutation site turns red before
it can quietly widen the skip set.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterator, Sequence

from itsf import contracts
from itsf.mc import over_budget as _over_budget
from itsf.contracts import (QUALIFYING_PHASES, AccountEvent,
                            AuthoritativeFactError, OverBudgetStatus,
                            TradePathRecord, fact_layer_active)

# --- stream vocabulary ------------------------------------------------------
# Kept as literals here on purpose: importing itsf.mc.atoms would make the
# platform layer depend on the consumer lane it is supposed to feed. The
# cross-lane equality (ENGINES / PLATFORMS) is pinned by a test instead.
ENGINES = ("E1", "E2")
PLATFORMS = ("lucid", "topstep")
ALLOWED_PHASES = frozenset(
    {"evaluation", "funded", "combine", "xfa", "dead", "done"})
# Which phases each platform's state machines can actually emit. Lucid runs
# evaluation -> funded (-> dead); Topstep runs combine -> done -> xfa
# (-> dead). A Lucid event claiming "xfa" is a wiring error, not a fact.
PLATFORM_PHASES = {
    "lucid": frozenset({"evaluation", "funded", "dead"}),
    "topstep": frozenset({"combine", "done", "xfa", "dead"}),
}

# --- STABLE verification rejection codes ------------------------------------
# These strings are a cross-lane contract: lane S1' asserts on them by value.
# Renaming one is a breaking change and must fail a test first.

# 1. day-net presence / finiteness
AUTH_FACTS_MISSING = "authoritative_facts_missing"
AUTH_DAY_NET_NOT_FINITE = "day_net_usd_not_finite"
# 2. generation presence / wellformedness / motion
AUTH_GENERATION_MISSING = "account_generation_missing"
AUTH_GENERATION_MALFORMED = "account_generation_malformed"
AUTH_GENERATION_NOT_MONOTONE = "account_generation_not_monotone"
AUTH_GENERATION_JUMP = "account_generation_jump_gt_1"
# 3. qualifying_day biconditional (C2)
AUTH_QUALIFYING_TRISTATE = "qualifying_day_tristate_violation"
AUTH_QUALIFYING_MISSING = "qualifying_day_absent_on_qualifying_phase"
AUTH_QUALIFYING_NOT_BOOL = "qualifying_day_not_bool"
# 4. requested / traded / cap coherence
AUTH_CONTRACT_COUNT_MALFORMED = "contract_count_malformed"
AUTH_TRADED_EXCEEDS_REQUESTED = "traded_n_exceeds_requested_n"
AUTH_CAP_FLAG = "cap_applied_inconsistent"
# 5. typed over-budget state
AUTH_OVER_BUDGET_VALUE_UNRULED = "over_budget_value_without_ruling"
AUTH_OVER_BUDGET_VALUE_NOT_BOOL = "over_budget_value_not_bool"
AUTH_OVER_BUDGET_STATUS_MISSING = "over_budget_status_missing"
AUTH_OVER_BUDGET_STATUS_TYPE = "over_budget_status_not_typed"
AUTH_OVER_BUDGET_STATUS_MISMATCH = "over_budget_status_inconsistent"
# D1 (2026-08-24). The type refuses these at construction; the stream
# verifier exists to catch the same shapes after a MUTATION, which is
# what __post_init__ can never see.
AUTH_OVER_BUDGET_VALUE_UNDER_ABSENCE = "over_budget_value_under_absence"
AUTH_OVER_BUDGET_RULED_WITHOUT_VALUES = "over_budget_ruled_without_values"
# 6. the bounded day-net / balance / payout identity
AUTH_DAY_NET_INVARIANT = "day_net_cross_check_violation"
# 7. stream-level labelling
AUTH_PHASE_UNKNOWN = "phase_not_in_allowed_set"
AUTH_PHASE_PLATFORM_MISMATCH = "phase_not_valid_for_platform"
AUTH_ENGINE_UNKNOWN = "engine_label_unknown"
AUTH_PLATFORM_UNKNOWN = "platform_label_unknown"

AUTH_REJECTION_CODES = frozenset({
    AUTH_FACTS_MISSING, AUTH_DAY_NET_NOT_FINITE,
    AUTH_GENERATION_MISSING, AUTH_GENERATION_MALFORMED,
    AUTH_GENERATION_NOT_MONOTONE, AUTH_GENERATION_JUMP,
    AUTH_QUALIFYING_TRISTATE, AUTH_QUALIFYING_MISSING,
    AUTH_QUALIFYING_NOT_BOOL,
    AUTH_CONTRACT_COUNT_MALFORMED, AUTH_TRADED_EXCEEDS_REQUESTED,
    AUTH_CAP_FLAG,
    AUTH_OVER_BUDGET_VALUE_UNRULED, AUTH_OVER_BUDGET_VALUE_NOT_BOOL,
    AUTH_OVER_BUDGET_STATUS_MISSING, AUTH_OVER_BUDGET_STATUS_TYPE,
    AUTH_OVER_BUDGET_STATUS_MISMATCH,
    AUTH_OVER_BUDGET_VALUE_UNDER_ABSENCE,
    AUTH_OVER_BUDGET_RULED_WITHOUT_VALUES,
    AUTH_DAY_NET_INVARIANT,
    AUTH_PHASE_UNKNOWN, AUTH_PHASE_PLATFORM_MISMATCH,
    AUTH_ENGINE_UNKNOWN, AUTH_PLATFORM_UNKNOWN,
})

# Money tolerance for the identity: platform arithmetic is plain float
# addition of USD amounts, so only representation error is expected.
CROSS_CHECK_TOL_USD = 1e-6


class AuthoritativeStreamError(AssertionError):
    """Raised by `check_event_facts(..., strict=True)`; carries `.violations`.

    `verify_event_stream` deliberately raises `AuthoritativeFactError`
    instead (a ValueError carrying a single stable `.code`): a production
    gate refuses on the FIRST violation and hands the caller one code, not
    a report.
    """

    def __init__(self, violations: list["FactViolation"]):
        self.violations = list(violations)
        head = "; ".join(f"{v.code}@{v.index}({v.day}) {v.detail}"
                         for v in self.violations[:5])
        more = "" if len(self.violations) <= 5 else f" (+{len(self.violations) - 5} more)"
        super().__init__(f"{len(self.violations)} day-fact violation(s): {head}{more}")


@dataclass(frozen=True)
class FactViolation:
    code: str
    index: int
    day: str
    detail: str = ""


def over_budget_status_for(path: TradePathRecord | None,
                           traded_n: int) -> OverBudgetStatus:
    """Typed E2 over-budget state for a day (never a fabricated boolean).

    Engine attribution comes from the day's TradePathRecord.engine (frozen
    S0 SS10.1 schema: 'E1' | 'E2'); an unknown engine is a hard failure
    rather than a silent default.
    """
    if path is None or traded_n <= 0:
        return OverBudgetStatus.NOT_APPLICABLE_NO_TRADE
    engine = path.engine
    if engine == "E1":
        # frozen: MC SS3 scopes the over-budget disclosure to E2 ("E2 强制
        # 报告") — the obligation does not reach E1 days.
        return OverBudgetStatus.NOT_APPLICABLE
    if engine == "E2":
        # D1 (2026-08-24) defined the predicate, so an E2 day that
        # held a position carries real booleans and this token
        # points at them. The PENDING_RULING branch is NOT dead:
        # the constant is the switch, and a future retraction must
        # return to saying so rather than leaving a stale RULED
        # label standing over absent values.
        return (OverBudgetStatus.RULED
                if contracts.OVER_BUDGET_PREDICATE_RULED
                else OverBudgetStatus.PENDING_RULING)
    raise ValueError(f"unknown engine {engine!r} (frozen set: E1 | E2)")


def over_budget_facts(path: TradePathRecord | None, traded_n: int,
                      budget: float) -> dict:
    """The over-budget fact fragment for one day: status, and the two
    booleans exactly when the predicate applies.

    ONE RULE, ONE PLACE. Both platforms call this rather than each
    computing the predicate for itself. Two implementations of one rule is
    the shape that produced four separate Highs in the supplement path,
    every one of them a case where the second copy was subtly weaker than
    the first.

    The booleans appear if and only if the status is RULED, which is what
    `AccountEvent` independently enforces -- so a drift between this
    helper and the fact type fails loudly instead of emitting a value
    under a label that says there is none.
    """
    status = over_budget_status_for(path, traded_n)
    if status is not OverBudgetStatus.RULED:
        return {"over_budget_status": status}
    if not budget > 0.0:
        # Unreachable on a real traded day: n_micros(budget, ...) returns 0
        # for a non-positive budget, which makes traded_n 0 and the status
        # NOT_APPLICABLE_NO_TRADE. Kept because "unreachable" is a claim
        # about today's call sites, and a fabricated comparison against a
        # zero budget would read as a measured breach on every losing day.
        raise ValueError(
            f"over_budget_bad_budget: traded_n={traded_n} with "
            f"budget={budget!r}; the predicate cannot judge a loss "
            "against a non-positive budget")
    verdict = _over_budget.evaluate(
        final_pnl_per_contract=path.final_pnl_per_contract,
        max_adverse_pnl=path.max_adverse_pnl,
        traded_n=traded_n, budget=budget)
    return {"over_budget_status": status,
            "over_budget": verdict.realised_over_budget,
            "intraday_over_budget": verdict.intraday_adverse_over_budget}


def expected_over_budget_status(engine: str,
                                traded_n: int) -> OverBudgetStatus:
    """The status a day MUST carry, from the run engine and traded size.

    Stated in terms of the two facts the event itself already reports, so
    the verifier does not have to trust (or re-call) the emission-side
    helper. Applicability conditions, all three exhaustive and disjoint:

      * traded_n == 0                -> NOT_APPLICABLE_NO_TRADE. No position
        was taken, so there is no realized loss and no budget draw to
        compare — this covers no-path days, n == 0 skips, payout halts,
        processing halts and dead-inert days alike.
      * traded_n > 0 and engine E1   -> NOT_APPLICABLE. frozen MC SS3 scopes
        the over-budget disclosure to E2; an E1 day owes no such fact.
      * traded_n > 0 and engine E2   -> RULED while the predicate is
        ruled, else PENDING_RULING. Frozen MC SS3 mandates the
        disclosure; D1 (2026-08-24) supplied the predicate.
    """
    if traded_n <= 0:
        return OverBudgetStatus.NOT_APPLICABLE_NO_TRADE
    if engine == "E1":
        return OverBudgetStatus.NOT_APPLICABLE
    if engine == "E2":
        return (OverBudgetStatus.RULED
                if contracts.OVER_BUDGET_PREDICATE_RULED
                else OverBudgetStatus.PENDING_RULING)
    raise ValueError(f"unknown engine {engine!r} (frozen set: E1 | E2)")


def day_net_identity_applies(prev: AccountEvent | None,
                             ev: AccountEvent) -> bool:
    """Does the day-net/balance/payout identity apply to this PAIR?

    The enumerated skip conditions S1/S2/S3 of the module docstring, in one
    place so the verifier and its tests cannot drift apart. Returns False
    ONLY for: no predecessor (S1), a generation change (S2), or a legacy
    event on either side (S3).
    """
    if prev is None:
        return False                                          # S1 stream head
    if not fact_layer_active(ev.day_net_usd, ev.account_generation):
        return False                                          # S3 legacy (ev)
    if not fact_layer_active(prev.day_net_usd, prev.account_generation):
        return False                                        # S3 legacy (prev)
    return ev.account_generation == prev.account_generation   # S2 boundary


def day_net_cross_check(prev: AccountEvent, ev: AccountEvent) -> float | None:
    """Signed residual of the identity, or None when it does not apply.

    Returns `day_net_usd - (balance - prev.balance + payout_gross)`.
    """
    if not day_net_identity_applies(prev, ev):
        return None
    return ev.day_net_usd - ((ev.balance - prev.balance) + ev.payout_gross)


# --- the rules --------------------------------------------------------------

def _is_real_number(v) -> bool:
    return not isinstance(v, bool) and isinstance(v, (int, float))


def _is_count(v) -> bool:
    return not isinstance(v, bool) and isinstance(v, int) and v >= 0


def _iter_violations(events: Sequence, *, engine: str | None,
                     platform: str | None,
                     require_facts: bool) -> Iterator[FactViolation]:
    """Yield every violation, in a DETERMINISTIC order.

    Per event the order is: phase -> day_net -> generation -> qualifying ->
    sizing -> over-budget; then the pairwise generation-motion and identity
    rules against the previous event. `verify_event_stream` takes the first
    one yielded, so this order IS the production refusal order.
    """
    if engine is not None and engine not in ENGINES:
        yield FactViolation(AUTH_ENGINE_UNKNOWN, -1, "",
                            f"engine={engine!r} not in {list(ENGINES)}")
        return
    if platform is not None and platform not in PLATFORMS:
        yield FactViolation(AUTH_PLATFORM_UNKNOWN, -1, "",
                            f"platform={platform!r} not in {list(PLATFORMS)}")
        return

    prev: AccountEvent | None = None
    for i, ev in enumerate(events):
        day = getattr(ev, "day", "")

        # -- phase ----------------------------------------------------------
        if ev.phase not in ALLOWED_PHASES:
            yield FactViolation(AUTH_PHASE_UNKNOWN, i, day,
                                f"phase={ev.phase!r}")
        elif platform is not None and ev.phase not in PLATFORM_PHASES[platform]:
            yield FactViolation(
                AUTH_PHASE_PLATFORM_MISMATCH, i, day,
                f"platform={platform!r} cannot emit phase={ev.phase!r} "
                f"(its state machines emit "
                f"{sorted(PLATFORM_PHASES[platform])})")

        # -- rule 1: day_net present and finite ------------------------------
        if ev.day_net_usd is None:
            if require_facts:
                yield FactViolation(AUTH_FACTS_MISSING, i, day,
                                    "day_net_usd is None")
            prev = ev
            continue
        if not _is_real_number(ev.day_net_usd) or \
                not math.isfinite(float(ev.day_net_usd)):
            yield FactViolation(AUTH_DAY_NET_NOT_FINITE, i, day,
                                f"day_net_usd={ev.day_net_usd!r}")

        # -- rule 2: generation present and wellformed -----------------------
        if ev.account_generation is None:
            yield FactViolation(AUTH_GENERATION_MISSING, i, day,
                                "day_net_usd is present but "
                                "account_generation is None")
        elif not _is_count(ev.account_generation):
            yield FactViolation(AUTH_GENERATION_MALFORMED, i, day,
                                f"account_generation="
                                f"{ev.account_generation!r}")

        # -- rule 3: qualifying_day, BOTH directions (C2) --------------------
        qual = ev.qualifying_day
        live = fact_layer_active(ev.day_net_usd, ev.account_generation)
        if qual is not None and not isinstance(qual, bool):
            yield FactViolation(
                AUTH_QUALIFYING_NOT_BOOL, i, day,
                f"qualifying_day={qual!r} (type {type(qual).__name__}); "
                "the tri-state is None | True | False")
        elif qual is not None and ev.phase not in QUALIFYING_PHASES:
            yield FactViolation(
                AUTH_QUALIFYING_TRISTATE, i, day,
                f"phase={ev.phase!r} carries qualifying_day={qual!r}; "
                "non-qualifying phases emit None")
        elif qual is None and ev.phase in QUALIFYING_PHASES and live:
            yield FactViolation(
                AUTH_QUALIFYING_MISSING, i, day,
                f"phase={ev.phase!r} has a qualifying-day ruleset and the "
                "fact layer is live; None deletes the day from every "
                "qualifying count instead of reporting a measured False")

        # -- rule 4: requested / traded / cap --------------------------------
        req, trd, cap = ev.requested_n, ev.traded_n, ev.cap_applied
        if not _is_count(req) or not _is_count(trd):
            yield FactViolation(AUTH_CONTRACT_COUNT_MALFORMED, i, day,
                                f"requested_n={req!r} traded_n={trd!r}")
        elif trd > req:
            yield FactViolation(
                AUTH_TRADED_EXCEEDS_REQUESTED, i, day,
                f"traded_n={trd} > requested_n={req}: the platform cannot "
                "trade more than was asked for")
        elif not isinstance(cap, bool):
            yield FactViolation(AUTH_CAP_FLAG, i, day,
                                f"cap_applied={cap!r} is not a bool")
        elif cap != (trd < req):
            # BICONDITIONAL. `=>` alone let a clamped day report no cap hit;
            # `<=` alone let an unclamped day claim one.
            yield FactViolation(
                AUTH_CAP_FLAG, i, day,
                f"cap_applied={cap!r} but traded_n={trd} requested_n={req} "
                f"(traded_n < requested_n is {trd < req})")

        # -- rule 5: typed over-budget state ---------------------------------
        ob, status = ev.over_budget, ev.over_budget_status
        intraday = getattr(ev, "intraday_over_budget", None)
        if ob is not None and not contracts.OVER_BUDGET_PREDICATE_RULED:
            # Unconditional and engine-INDEPENDENT: frozen MC SS3 mandates
            # the E2 disclosure and defines no predicate, so ANY boolean is
            # fabricated evidence — a False would read downstream as
            # "measured, never exceeded budget".
            yield FactViolation(
                AUTH_OVER_BUDGET_VALUE_UNRULED, i, day,
                f"over_budget={ob!r} while OVER_BUDGET_PREDICATE_RULED is "
                "False; emit over_budget_status instead")
        elif ob is not None and not isinstance(ob, bool):
            yield FactViolation(AUTH_OVER_BUDGET_VALUE_NOT_BOOL, i, day,
                                f"over_budget={ob!r}")
        if status is None:
            # `over_budget is None` must say WHICH kind of None it is; an
            # untyped absence is indistinguishable from "not measured yet".
            yield FactViolation(AUTH_OVER_BUDGET_STATUS_MISSING, i, day,
                                f"over_budget={ob!r} carries no "
                                "over_budget_status")
        elif not isinstance(status, OverBudgetStatus):
            yield FactViolation(
                AUTH_OVER_BUDGET_STATUS_TYPE, i, day,
                f"over_budget_status={status!r} is not an OverBudgetStatus; "
                "a look-alike with the right .value token would seal a "
                "report whose meaning no enum pins")
        elif engine is not None and _is_count(trd):
            want = expected_over_budget_status(engine, trd)
            if status is not want:
                yield FactViolation(
                    AUTH_OVER_BUDGET_STATUS_MISMATCH, i, day,
                    f"engine={engine} traded_n={trd} requires "
                    f"{want.value!r}, event carries {status.value!r}")

        # D1: the label and the values must agree. This runs AFTER the
        # label checks above on purpose -- if the status itself is
        # wrong for this (engine, traded) day, that is the root cause
        # and a value mismatch is only its consequence. Reporting the
        # consequence first would send a reader to the wrong field.
        # It runs here rather than only at construction because the
        # failure that matters is a field flipped after a legal event
        # was built, which __post_init__ can never see.
        if status is OverBudgetStatus.RULED:
            for _name, _v in (("over_budget", ob),
                              ("intraday_over_budget", intraday)):
                if not isinstance(_v, bool):
                    yield FactViolation(
                        AUTH_OVER_BUDGET_RULED_WITHOUT_VALUES, i, day,
                        f"status=RULED but {_name}={_v!r}; MC SS3 mandates "
                        "BOTH probabilities, so one value answers neither")
        elif status is not None:
            for _name, _v in (("over_budget", ob),
                              ("intraday_over_budget", intraday)):
                if _v is not None:
                    yield FactViolation(
                        AUTH_OVER_BUDGET_VALUE_UNDER_ABSENCE, i, day,
                        f"status={status.value} declares the quantity "
                        f"absent yet {_name}={_v!r} rides along")

        # -- pairwise: rule 2 motion + rule 6 identity -----------------------
        if prev is not None and _is_count(prev.account_generation) \
                and _is_count(ev.account_generation):
            delta = ev.account_generation - prev.account_generation
            if delta < 0:
                yield FactViolation(
                    AUTH_GENERATION_NOT_MONOTONE, i, day,
                    f"{prev.account_generation} -> {ev.account_generation}: "
                    "generations only ever increment")
            elif delta > 1:
                yield FactViolation(
                    AUTH_GENERATION_JUMP, i, day,
                    f"{prev.account_generation} -> {ev.account_generation}: "
                    "each balance-reset boundary moves it by exactly 1, so "
                    "a jump means a boundary emitted no event")
        if prev is not None and _is_real_number(ev.day_net_usd) \
                and _is_real_number(ev.payout_gross):
            resid = day_net_cross_check(prev, ev)
            if resid is not None and abs(resid) > CROSS_CHECK_TOL_USD:
                yield FactViolation(
                    AUTH_DAY_NET_INVARIANT, i, day,
                    f"day_net={ev.day_net_usd!r} balance_delta="
                    f"{ev.balance - prev.balance!r} payout_gross="
                    f"{ev.payout_gross!r} residual={resid!r}")
        prev = ev


def verify_event_stream(events: Sequence, *, engine: str,
                        platform: str) -> None:
    """THE production-chain fact gate. Returns None, or raises on violation.

    Called by the MC consumer in `_run_path_atom` BEFORE atom reduction.
    Raises `contracts.AuthoritativeFactError(code, detail)` on the FIRST
    violation, where `code` is one of `AUTH_REJECTION_CODES` (stable
    strings; lane S1' asserts on them by value).

    NEVER returns a value and NEVER computes a research statistic: it
    reads the emitted facts, checks them against structural rules, and
    either refuses or gets out of the way. Verified rules, in refusal
    order per event:

      1. day_net_usd present (AUTH_FACTS_MISSING) and a finite real
         (AUTH_DAY_NET_NOT_FINITE);
      2. account_generation present (AUTH_GENERATION_MISSING), a
         non-negative int (AUTH_GENERATION_MALFORMED), never regressing
         (AUTH_GENERATION_NOT_MONOTONE) and moving by at most 1
         (AUTH_GENERATION_JUMP) — every legal boundary is exactly +1;
      3. the qualifying_day BICONDITIONAL: on a live fact layer,
         `phase in {funded, xfa}` <=> `qualifying_day is a bool`
         (AUTH_QUALIFYING_TRISTATE / AUTH_QUALIFYING_MISSING /
         AUTH_QUALIFYING_NOT_BOOL);
      4. `traded_n <= requested_n` (AUTH_TRADED_EXCEEDS_REQUESTED) and
         `cap_applied <=> traded_n < requested_n` (AUTH_CAP_FLAG), both
         counts being non-negative ints (AUTH_CONTRACT_COUNT_MALFORMED);
      5. the typed over-budget state: no boolean while the predicate is
         unruled (AUTH_OVER_BUDGET_VALUE_UNRULED, engine-independent), a
         typed status always present (AUTH_OVER_BUDGET_STATUS_MISSING /
         AUTH_OVER_BUDGET_STATUS_TYPE) and consistent with the engine and
         the traded size (AUTH_OVER_BUDGET_STATUS_MISMATCH — see
         `expected_over_budget_status` for the three applicability
         conditions);
      6. the day-net/balance/payout identity within one generation
         (AUTH_DAY_NET_INVARIANT), skipped ONLY under the enumerated
         conditions in `day_net_identity_applies` / the module docstring;
      plus the stream labels themselves: phase in the allowed set and
      emittable by this platform (AUTH_PHASE_UNKNOWN /
      AUTH_PHASE_PLATFORM_MISMATCH) and the engine/platform arguments in
      the frozen vocabularies (AUTH_ENGINE_UNKNOWN / AUTH_PLATFORM_UNKNOWN).
    """
    for v in _iter_violations(events, engine=engine, platform=platform,
                              require_facts=True):
        raise AuthoritativeFactError(
            v.code,
            f"event {v.index} ({v.day!r}) on {platform}/{engine}: {v.detail}"
            if v.index >= 0 else v.detail)
    return None


def check_event_facts(events, *, require_facts: bool = True,
                      strict: bool = False, engine: str | None = None,
                      platform: str | None = None) -> list[FactViolation]:
    """Violation-COLLECTING form of `verify_event_stream`'s rules.

    Kept for tests that want the whole list rather than the first refusal,
    and for pointing the verifier at a MIXED stream: `require_facts=False`
    tolerates legacy events (`day_net_usd is None`) while every other check
    still runs on the events that DO carry facts.

    `engine` / `platform` default to None, which SKIPS exactly the two
    label-scoped rules (over-budget status applicability, and the
    platform's emittable phase set). Production semantics are
    `verify_event_stream`'s, where both are mandatory.
    """
    out = list(_iter_violations(events, engine=engine, platform=platform,
                                require_facts=require_facts))
    if strict and out:
        raise AuthoritativeStreamError(out)
    return out
