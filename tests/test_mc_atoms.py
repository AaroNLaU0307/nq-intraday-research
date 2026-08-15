"""N01 / PHASE D1-D2-D4-D6 — the unified atom layer (lane S1).

Synthetic fixtures ONLY. Nothing here reads real data, real results, or
any repository artifact beyond the already-frozen constant tables.

Coverage map (PHASE G):
  A. atom construction: positive, one negative PER cross-invariant code,
     boundary cases at every inequality edge;
  B. typed absence: three distinct "None"s, raw None refused, 0 never
     impersonating an absence, distinct render tokens;
  C. the S2-seam adapter: the ONLY reader of platform-authoritative day
     facts, refuses absence rather than falling back to balance deltas;
  D. lifecycle_config_digest: mechanical enumeration + mechanical
     constant harvest + per-field mutation battery + exact preimage
     field set;
  E. key grid: four independent refusal codes including substitution;
  F. reductions + canonical serialisation round-trip + two-level digests;
  G. BASELINE COUNTEREXAMPLES — the defects this node removed must stay
     un-reintroducible.
"""
from __future__ import annotations

import ast
import dataclasses
import json
import math
import pathlib

import pytest

from itsf.mc import atoms as A
from itsf.mc import orchestrator as orch

REPO = pathlib.Path(__file__).resolve().parents[1]

D64 = "a" * 64
D64B = "b" * 64
D64C = "c" * 64


# --- helpers ---------------------------------------------------------------

def _atom(**over):
    """A VALID atom; each test perturbs exactly one thing."""
    kw = dict(
        prepared_digest=D64, lifecycle_config_digest=D64B,
        world_index=0, world_digest=D64C, phase_offset=3,
        platform="topstep", engine="E1", scenario="Conservative",
        theta_channel="theta_0.5", master_seed=7,
        monthly_prop_operating_ev=12.5,
        days_in_window=20, offered_days=10, executed_trade_days=6,
        skips_n0=2, payout_count=1, winning_days=4,
        days_profit_ge_150=2, qualifying_days=3, exhausted=False,
        ambiguous_days=1, attempts_used=1, b2f_used=0,
        contract_cap_hits=1, e2_over_budget_days=A.NOT_APPLICABLE)
    kw.update(over)
    return A.SimulationPathObservation(**kw)


class _StubEvent:
    """Duck-typed AccountEvent stand-in. Only the attributes explicitly
    passed exist — that is how "the field has not landed" is expressed."""

    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


def _status_for(engine: str, traded_n: int) -> str:
    """INDEPENDENT ORACLE of the legal `over_budget_status` token, written
    out here from the frozen scope rather than imported from production:

      no position          -> NOT_APPLICABLE_NO_TRADE (no referent)
      E1 with a position   -> NOT_APPLICABLE (MC SS3 scopes the
                              over-budget disclosure to E2)
      E2 with a position   -> PENDING_RULING (defined, predicate unruled)
    """
    if not isinstance(traded_n, int) or traded_n <= 0:
        return "NOT_APPLICABLE_NO_TRADE"
    return "NOT_APPLICABLE" if engine == "E1" else "PENDING_RULING"


def _stub(*, engine="E1", **over):
    """A stub event that is LEGAL for `engine`. `phase` defaults to
    'evaluation' (a phase with no qualifying-day concept), so
    `qualifying_day=None` is the correct fact there."""
    traded = over.get("traded_n", 1)
    kw = dict(day_net_usd=10.0, phase="evaluation", account_generation=0,
              requested_n=1, traded_n=1, cap_applied=False,
              payout_gross=0.0, qualifying_day=None, over_budget=None,
              over_budget_status=_status_for(engine, traded))
    kw.update(over)
    return _StubEvent(**kw)


def _grid_atoms(B=2, support=(0, 1), **over):
    return [_atom(world_index=w, phase_offset=p,
                  monthly_prop_operating_ev=float(w * 10 + p), **over)
            for w in range(B) for p in support]


def _obs_set(B=2, support=(0, 1), atoms=None, **over):
    kw = dict(run_label="base", platform="topstep", engine="E1",
              scenario="Conservative", theta_channel="theta_0.5",
              sizing_policy="P2", B=B, master_seed=7,
              prepared_digest=D64, lifecycle_config_digest=D64B,
              legal_phase_support=support)
    kw.update(over)
    return A.ObservationSet.from_atoms(
        _grid_atoms(B, support) if atoms is None else atoms, **kw)


# ===========================================================================
# A. atom construction
# ===========================================================================

def test_positive_atom_constructs_and_exposes_its_key():
    a = _atom()
    assert a.key == (0, 3)
    assert a.monthly_prop_operating_ev == 12.5
    assert isinstance(a.monthly_prop_operating_ev, float)


@pytest.mark.parametrize("over,code", [
    ({"prepared_digest": "short"}, "atom_identity_digest_invalid"),
    ({"lifecycle_config_digest": 7}, "atom_identity_digest_invalid"),
    ({"world_digest": None}, "atom_identity_digest_invalid"),
    ({"world_index": -1}, "atom_field_type_violation"),
    ({"phase_offset": True}, "atom_field_type_violation"),
    ({"platform": "ftmo"}, "atom_axis_violation"),
    ({"engine": "E3"}, "atom_axis_violation"),
    ({"scenario": "Nightmare"}, "atom_axis_violation"),
    ({"theta_channel": "0.5"}, "atom_axis_violation"),
    ({"master_seed": "7"}, "atom_field_type_violation"),
    ({"monthly_prop_operating_ev": float("nan")}, "atom_ev_non_finite"),
    ({"monthly_prop_operating_ev": float("inf")}, "atom_ev_non_finite"),
    ({"exhausted": 1}, "atom_field_type_violation"),
    ({"offered_days": 21}, "atom_offered_exceeds_window"),
    ({"skips_n0": 5, "executed_trade_days": 6, "offered_days": 10},
     "atom_skip_execution_partition_violation"),
    ({"winning_days": 7}, "atom_monotone_chain_violation"),
    ({"days_profit_ge_150": 5}, "atom_monotone_chain_violation"),
    ({"executed_trade_days": 11}, "atom_monotone_chain_violation"),
    ({"payout_count": 21}, "atom_payout_count_exceeds_window"),
    ({"qualifying_days": 21}, "atom_qualifying_days_exceed_window"),
    ({"ambiguous_days": 11}, "atom_ambiguous_exceeds_offered"),
    ({"contract_cap_hits": 7}, "atom_contract_cap_exceeds_executed"),
    ({"attempts_used": 0}, "atom_attempts_range_violation"),
    ({"attempts_used": 7}, "atom_attempts_range_violation"),
    ({"exhausted": True, "attempts_used": 2},
     "atom_exhaustion_attempts_inconsistent"),
    ({"platform": "lucid", "b2f_used": 1}, "atom_b2f_platform_violation"),
    ({"engine": "E1", "e2_over_budget_days": 0},
     "atom_e2_field_engine_semantics"),
    ({"engine": "E2", "e2_over_budget_days": A.NOT_APPLICABLE},
     "atom_e2_field_engine_semantics"),
])
def test_each_cross_invariant_has_its_own_refusal_code(over, code):
    with pytest.raises(A.MCInputError) as exc:
        _atom(**over)
    assert exc.value.code == code


@pytest.mark.parametrize("over", [
    {"offered_days": 20},                       # == days_in_window
    {"skips_n0": 4, "executed_trade_days": 6},  # sum == offered_days
    {"winning_days": 6},                        # == executed_trade_days
    {"days_profit_ge_150": 4},                  # == winning_days
    {"payout_count": 20},                       # == days_in_window
    {"qualifying_days": 20},                    # == days_in_window
    {"ambiguous_days": 10},                     # == offered_days
    {"contract_cap_hits": 6},                   # == executed_trade_days
    {"attempts_used": 1},                       # lower bound
    {"exhausted": True,
     "attempts_used": orch.MAX_EVALUATION_STARTS},   # upper bound
    {"monthly_prop_operating_ev": 0.0},
    {"monthly_prop_operating_ev": -1e9},
])
def test_boundary_values_are_accepted(over):
    assert _atom(**over) is not None


def test_exhaustion_upper_bound_is_the_frozen_constant_not_a_literal():
    """PROBE: the attempts ceiling tracks orchestrator.MAX_EVALUATION_
    STARTS mechanically — a hand-copied 6 would silently drift."""
    with pytest.raises(A.MCInputError) as exc:
        _atom(attempts_used=orch.MAX_EVALUATION_STARTS + 1)
    assert exc.value.code == "atom_attempts_range_violation"
    assert str(orch.MAX_EVALUATION_STARTS) in str(exc.value)


# ===========================================================================
# B. typed absence — three distinct "None"s
# ===========================================================================

def test_the_absence_tokens_are_distinct_objects_and_render_distinctly():
    tokens = {A.NOT_APPLICABLE, A.NOT_APPLICABLE_NO_TRADE,
              A.PENDING_RULING, A.PENDING_ENGINEERING}
    assert len(tokens) == 4
    rendered = {str(t) for t in tokens}
    assert rendered == {"NOT_APPLICABLE", "NOT_APPLICABLE_NO_TRADE",
                        "PENDING_RULING", "PENDING_ENGINEERING"}
    assert A.NOT_APPLICABLE != A.PENDING_RULING
    for t in tokens:
        assert t != 0 and t is not None


@pytest.mark.parametrize("field", ["contract_cap_hits",
                                   "e2_over_budget_days"])
def test_raw_none_is_refused_because_it_cannot_say_why(field):
    over = {field: None}
    if field == "e2_over_budget_days":
        over["engine"] = "E2"
    with pytest.raises(A.MCInputError) as exc:
        _atom(**over)
    assert exc.value.code == "atom_untyped_none"


def test_e1_and_e2_absences_are_type_level_distinguishable_in_the_seal():
    e1 = _atom(engine="E1", e2_over_budget_days=A.NOT_APPLICABLE)
    e2 = _atom(engine="E2", e2_over_budget_days=A.PENDING_RULING)
    r1 = A.atom_canonical_dict(e1)["e2_over_budget_days"]
    r2 = A.atom_canonical_dict(e2)["e2_over_budget_days"]
    assert r1 == "NOT_APPLICABLE" and r2 == "PENDING_RULING"
    assert r1 != r2
    # and neither is ever 0 or null
    assert r1 not in (0, None) and r2 not in (0, None)


def test_zero_and_absence_produce_different_atom_digests():
    """A forged 0 can never impersonate an unruled quantity."""
    zero = _atom(engine="E2", e2_over_budget_days=0)
    absent = _atom(engine="E2", e2_over_budget_days=A.PENDING_RULING)
    assert A.atom_digest(zero) != A.atom_digest(absent)


def test_mixed_absence_semantics_in_one_set_refuse():
    atoms = [_atom(world_index=0, phase_offset=0, engine="E2",
                   e2_over_budget_days=A.PENDING_RULING),
             _atom(world_index=0, phase_offset=1, engine="E2",
                   e2_over_budget_days=A.NOT_APPLICABLE_NO_TRADE)]
    with pytest.raises(A.MCInputError) as exc:
        A.reduce_feasibility_counts(atoms)
    assert exc.value.code == "feasibility_absent_semantics_mixed"


# ===========================================================================
# C. the S2-seam adapter
# ===========================================================================

def test_adapter_positive_counts_from_authoritative_fields_only():
    events = [
        _stub(day_net_usd=200.0, traded_n=2, requested_n=2,
              qualifying_day=None),
        _stub(day_net_usd=-50.0, traded_n=1, requested_n=3,
              cap_applied=True),
        _stub(day_net_usd=0.0, traded_n=0, requested_n=0),
        _stub(day_net_usd=160.0, traded_n=1, requested_n=1,
              phase="funded", qualifying_day=True, payout_gross=500.0),
    ]
    facts = A.path_facts_from_events(events, engine="E1",
                                     platform="topstep")
    assert facts["event_days"] == 4
    assert facts["executed_trade_days"] == 3
    assert facts["winning_days"] == 2            # 200, 160
    assert facts["days_profit_ge_150"] == 2
    assert facts["qualifying_days"] == 1         # PLATFORM's own counter
    assert facts["contract_cap_hits"] == 1
    assert facts["payout_count"] == 1
    assert facts["e2_over_budget_days"] is A.NOT_APPLICABLE


def test_qualifying_days_is_not_a_rederived_threshold_count():
    """Lane S2's documented trap: a Topstep XFA payout-request day can
    clear $150 and still NOT be a qualifying day. The adapter must take
    the platform's own flag, so the two counts legitimately differ."""
    events = [_stub(day_net_usd=900.0, phase="xfa", qualifying_day=False,
                    payout_gross=800.0)]
    facts = A.path_facts_from_events(events, engine="E1",
                                     platform="topstep")
    assert facts["days_profit_ge_150"] == 1      # literal threshold
    assert facts["qualifying_days"] == 0         # platform says no


@pytest.mark.parametrize("field", A.SEAM_REQUIRED_FIELDS)
def test_absent_platform_fact_refuses_and_never_falls_back(field):
    kw = {"day_net_usd": 10.0, "phase": "evaluation",
          "account_generation": 0, "requested_n": 1, "traded_n": 1,
          "cap_applied": False, "payout_gross": 0.0,
          "over_budget_status": "NOT_APPLICABLE"}
    kw.pop(field)
    with pytest.raises(A.MCInputError) as exc:
        A.path_facts_from_events([_StubEvent(**kw)], engine="E1",
                                 platform="topstep")
    assert exc.value.code == "platform_facts_absent"


@pytest.mark.parametrize("field", A.SEAM_REQUIRED_FIELDS)
def test_none_valued_platform_fact_refuses_too(field):
    with pytest.raises(A.MCInputError) as exc:
        A.path_facts_from_events([_stub(**{field: None})], engine="E1",
                                 platform="topstep")
    assert exc.value.code == "platform_facts_absent"


@pytest.mark.parametrize("over,code", [
    ({"day_net_usd": "x"}, "platform_facts_malformed"),
    ({"day_net_usd": float("nan")}, "platform_facts_malformed"),
    ({"account_generation": -1}, "platform_facts_malformed"),
    ({"requested_n": True}, "platform_facts_malformed"),
    ({"cap_applied": 1}, "platform_facts_malformed"),
    ({"qualifying_day": "yes"}, "platform_facts_malformed"),
    ({"traded_n": 5, "requested_n": 2},
     "platform_facts_sizing_incoherent"),
    ({"payout_gross": "500"}, "platform_facts_malformed"),
    ({"over_budget_status": "SOMETHING_ELSE"},
     "platform_facts_malformed"),
])
def test_malformed_platform_facts_refuse(over, code):
    with pytest.raises(A.MCInputError) as exc:
        A.path_facts_from_events([_stub(**over)], engine="E1",
                                 platform="topstep")
    assert exc.value.code == code


def test_generation_must_be_monotone_non_decreasing():
    events = [_stub(account_generation=1), _stub(account_generation=0)]
    with pytest.raises(A.MCInputError) as exc:
        A.path_facts_from_events(events, engine="E1", platform="topstep")
    assert exc.value.code == "platform_facts_generation_not_monotone"


def test_e1_carrying_an_over_budget_boolean_refuses():
    with pytest.raises(A.MCInputError) as exc:
        A.path_facts_from_events([_stub(over_budget=False)], engine="E1",
                                 platform="topstep")
    assert exc.value.code == "platform_facts_engine_semantics"


def test_e2_without_a_ruled_predicate_yields_pending_never_zero():
    facts = A.path_facts_from_events(
        [_stub(engine="E2", over_budget=None,
               over_budget_status="PENDING_RULING")],
        engine="E2", platform="topstep")
    assert facts["e2_over_budget_days"] is A.PENDING_RULING
    assert facts["e2_over_budget_days"] != 0


# --- C3: the E2 over_budget boundary, gated at the ADAPTER ----------------

def test_e2_boolean_over_budget_never_reaches_a_formal_count():
    """C3 BASELINE COUNTEREXAMPLE (measured before this node): a legally
    constructed event stream whose `over_budget` was set to True after
    construction — `AccountEvent` is a MUTABLE dataclass — produced
    `e2_over_budget_days = 2` as a FORMAL COUNT, walking straight past
    PENDING_RULING. The producer's construction-time refusal cannot see
    a post-construction mutation; the consumer now refuses on its own."""
    events = [_stub(engine="E2", over_budget=True,
                    over_budget_status="PENDING_RULING"),
              _stub(engine="E2", over_budget=True,
                    over_budget_status="PENDING_RULING")]
    with pytest.raises(A.MCInputError) as exc:
        A.path_facts_from_events(events, engine="E2", platform="topstep")
    assert exc.value.code == "platform_facts_e2_over_budget_boolean_unruled"


def test_a_real_account_event_mutated_after_construction_is_refused():
    """The exact attack shape: build a LEGAL production AccountEvent (the
    producer's own type, its own __post_init__), then flip the field."""
    from itsf.contracts import AccountEvent, OverBudgetStatus
    ev = AccountEvent(day="2026-08-03", phase="evaluation", balance=50000.0,
                      floor=48000.0, day_net_usd=10.0,
                      account_generation=0, requested_n=1, traded_n=1,
                      over_budget_status=OverBudgetStatus.PENDING_RULING)
    # legal today
    facts = A.path_facts_from_events([ev], engine="E2", platform="topstep")
    assert facts["e2_over_budget_days"] is A.PENDING_RULING
    ev.over_budget = True                      # the mutation the type allows
    with pytest.raises(A.MCInputError) as exc:
        A.path_facts_from_events([ev], engine="E2", platform="topstep")
    assert exc.value.code == "platform_facts_e2_over_budget_boolean_unruled"


@pytest.mark.parametrize("value", [True, False])
def test_duck_typed_e2_boolean_is_refused_in_both_polarities(value):
    """A False is refused as loudly as a True: 'measured, never exceeded'
    is exactly the reading PENDING_RULING exists to forbid."""
    with pytest.raises(A.MCInputError) as exc:
        A.path_facts_from_events(
            [_stub(engine="E2", over_budget=value,
                   over_budget_status="PENDING_RULING")],
            engine="E2", platform="topstep")
    assert exc.value.code == "platform_facts_e2_over_budget_boolean_unruled"


@pytest.mark.parametrize("engine,over,code", [
    # status says "no position" while the event traded
    ("E2", {"traded_n": 1, "requested_n": 1,
            "over_budget_status": "NOT_APPLICABLE_NO_TRADE"},
     "platform_facts_over_budget_status_inconsistent"),
    # E2 traded day claiming the permanent E1 absence
    ("E2", {"traded_n": 1, "over_budget_status": "NOT_APPLICABLE"},
     "platform_facts_over_budget_status_inconsistent"),
    # no-trade day claiming the unruled predicate
    ("E2", {"traded_n": 0, "requested_n": 0,
            "over_budget_status": "PENDING_RULING"},
     "platform_facts_over_budget_status_inconsistent"),
    # E1 traded day claiming the E2 unruled state
    ("E1", {"traded_n": 1, "over_budget_status": "PENDING_RULING"},
     "platform_facts_over_budget_status_inconsistent"),
    # the typed status is mandatory, not optional
    ("E2", {"over_budget_status": None},
     "platform_facts_over_budget_status_absent"),
])
def test_status_value_combination_is_checked_independently(engine, over,
                                                           code):
    with pytest.raises(A.MCInputError) as exc:
        A.path_facts_from_events([_stub(engine=engine, **over)],
                                 engine=engine, platform="topstep")
    assert exc.value.code == code


def test_missing_over_budget_status_attribute_refuses_too():
    kw = {"day_net_usd": 10.0, "phase": "evaluation",
          "account_generation": 0, "requested_n": 1, "traded_n": 1,
          "cap_applied": False, "payout_gross": 0.0}
    with pytest.raises(A.MCInputError) as exc:
        A.path_facts_from_events([_StubEvent(**kw)], engine="E2",
                                 platform="topstep")
    assert exc.value.code == "platform_facts_over_budget_status_absent"


def test_a_flipped_ruling_does_not_silently_start_accepting_booleans(
        monkeypatch):
    """FORWARD RED LINE. If Aaron flips OVER_BUDGET_PREDICATE_RULED, this
    adapter must REFUSE until a new explicit predicate implementation
    lands — it may never inherit a boolean meaning nobody wrote down."""
    from itsf import contracts
    monkeypatch.setattr(contracts, "OVER_BUDGET_PREDICATE_RULED", True)
    with pytest.raises(A.MCInputError) as exc:
        A.path_facts_from_events(
            [_stub(engine="E2", over_budget=True,
                   over_budget_status="PENDING_RULING")],
            engine="E2", platform="topstep")
    assert exc.value.code == "platform_facts_over_budget_ruling_changed"
    # ... and even an honest UNRULED-shaped stream refuses under the flip,
    # because the pinned consumption rule below it is stale by definition
    with pytest.raises(A.MCInputError) as exc:
        A.path_facts_from_events(
            [_stub(engine="E2", over_budget_status="PENDING_RULING")],
            engine="E2", platform="topstep")
    assert exc.value.code == "platform_facts_over_budget_ruling_changed"
    # E1 is untouched: its absence is permanent, not ruling-dependent
    assert A.path_facts_from_events(
        [_stub(engine="E1")], engine="E1",
        platform="topstep")["e2_over_budget_days"] is A.NOT_APPLICABLE


def test_the_pinned_ruling_constant_is_still_false():
    """PIN: this whole consumption rule is written for the UNRULED state.
    If this assertion ever fails, the adapter's E2 branch must be
    re-implemented deliberately, not adjusted."""
    from itsf import contracts
    assert contracts.OVER_BUDGET_PREDICATE_RULED is False
    assert A.expected_over_budget_token("E2", 1) == "PENDING_RULING"
    assert A.expected_over_budget_token("E2", 0) == "NOT_APPLICABLE_NO_TRADE"
    assert A.expected_over_budget_token("E1", 1) == "NOT_APPLICABLE"
    assert A.expected_over_budget_token("E1", 0) == "NOT_APPLICABLE_NO_TRADE"


def test_an_empty_e2_stream_is_pending_not_a_measured_zero():
    """An accumulator initialised to 0 would report "measured, never
    exceeded" for a path that observed nothing at all."""
    facts = A.path_facts_from_events([], engine="E2", platform="topstep")
    assert facts["e2_over_budget_days"] is A.PENDING_RULING
    assert facts["event_days"] == 0


# --- C2 layer 4: the adapter reads the PHASE ------------------------------

@pytest.mark.parametrize("phase", ["funded", "xfa"])
@pytest.mark.parametrize("qual", [None, "__absent__"])
def test_qualifying_day_absent_on_a_qualifying_phase_refuses(phase, qual):
    """C2-L4 BASELINE COUNTEREXAMPLE (measured before this node): an xfa
    day with day_net_usd=10.0 and qualifying_day=None was silently
    skipped and reduced to `qualifying_days = 0` — a hard zero
    manufactured from a missing fact."""
    over = {"phase": phase, "day_net_usd": 10.0}
    if qual is None:
        over["qualifying_day"] = None
        ev = _stub(**over)
    else:
        ev = _stub(**over)
        del ev.qualifying_day
    with pytest.raises(A.MCInputError) as exc:
        A.path_facts_from_events([ev], engine="E1", platform="topstep")
    assert exc.value.code == "platform_facts_qualifying_absent"


@pytest.mark.parametrize("phase", ["evaluation", "combine", "dead", "done"])
@pytest.mark.parametrize("value", [True, False])
def test_qualifying_day_on_a_non_qualifying_phase_refuses(phase, value):
    """Both polarities: a True invents a qualifying day, a False disguises
    "the ruleset has no such concept" as "measured, did not qualify"."""
    with pytest.raises(A.MCInputError) as exc:
        A.path_facts_from_events([_stub(phase=phase, qualifying_day=value)],
                                 engine="E1", platform="topstep")
    assert exc.value.code == "platform_facts_qualifying_phase_mismatch"


def test_qualifying_phases_come_from_the_frozen_contract_not_a_literal():
    from itsf import contracts
    assert contracts.QUALIFYING_PHASES == frozenset({"funded", "xfa"})
    # the adapter follows the frozen set: shrink it and the previously
    # legal funded day becomes a phase-mismatch, not a silent skip.
    facts = A.path_facts_from_events(
        [_stub(phase="funded", qualifying_day=True)], engine="E1",
        platform="topstep")
    assert facts["qualifying_days"] == 1


def test_phase_is_a_required_seam_field():
    assert "phase" in A.SEAM_REQUIRED_FIELDS
    with pytest.raises(A.MCInputError) as exc:
        A.path_facts_from_events([_stub(phase=None)], engine="E1",
                                 platform="topstep")
    assert exc.value.code == "platform_facts_absent"
    with pytest.raises(A.MCInputError) as exc:
        A.path_facts_from_events([_stub(phase=7)], engine="E1",
                                 platform="topstep")
    assert exc.value.code == "platform_facts_malformed"


def test_qualifying_days_positive_path_still_counts_the_platform_counter():
    """POSITIVE (anti over-tightening): a legal mixed stream still
    counts exactly the platform's own increments."""
    events = [_stub(phase="evaluation", qualifying_day=None),
              _stub(phase="funded", day_net_usd=400.0, qualifying_day=True),
              _stub(phase="funded", day_net_usd=20.0, qualifying_day=False),
              _stub(phase="xfa", day_net_usd=900.0, qualifying_day=True,
                    payout_gross=100.0),
              _stub(phase="dead", traded_n=0, requested_n=0,
                    day_net_usd=0.0, qualifying_day=None)]
    facts = A.path_facts_from_events(events, engine="E1",
                                     platform="topstep")
    assert facts["qualifying_days"] == 2
    assert facts["days_profit_ge_150"] == 2      # 400 and 900
    assert facts["event_days"] == 5


def test_adapter_refuses_unknown_axes():
    for kw, in [({"engine": "E9", "platform": "topstep"},),
                ({"engine": "E1", "platform": "ftmo"},)]:
        with pytest.raises(A.MCInputError) as exc:
            A.path_facts_from_events([_stub()], **kw)
        assert exc.value.code == "atom_axis_violation"


# The EXEMPT set, with a reason each. Everything else in itsf.mc is a
# CONSUMER and must go through `atoms.path_facts_from_events`.
SEAM_EXEMPT = {
    "atoms.py": "the single consumer-side adapter itself",
    "orchestrator.py": "producer: assembles the emitted event stream",
    "account.py": "producer: sizing/limit state the facts describe",
    # N01 C4: lane S2' owns the production fact-verification entry
    # (`verify_event_stream`). It is the PRODUCER-SIDE fact OWNER, so its
    # reads are definitions, not a second interpretation — without this
    # exemption the pin would fire on the verifier itself.
    "authoritative.py": "producer: lane S2' fact owner / verifier",
}


def test_only_the_adapter_reads_platform_authoritative_fields():
    """AST PIN: no module outside `atoms.path_facts_from_events` may
    touch the seam fields — a second reader is a second (divergent)
    interpretation of the platform's facts."""
    seam = set(A.SEAM_REQUIRED_FIELDS) | set(A.SEAM_TRISTATE_FIELDS)
    offenders = []
    for path in (REPO / "src" / "itsf" / "mc").rglob("*.py"):
        if path.name in SEAM_EXEMPT or "platforms" in path.parts:
            continue                      # producer lane S2 + the adapter
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr in seam:
                offenders.append(f"{path.name}:{node.lineno}:{node.attr}")
    assert offenders == [], (
        "platform-authoritative day facts read outside the single "
        f"adapter: {offenders}")


def test_the_seam_exemption_set_is_justified_and_closed():
    """The exemption list is PINNED: every entry names a producer-side
    fact owner (or the adapter itself) and carries a reason. Adding one
    is a reviewed change — an exemption is how a second interpretation
    would sneak back in."""
    assert set(SEAM_EXEMPT) == {"atoms.py", "orchestrator.py",
                                "account.py", "authoritative.py"}
    for name, reason in SEAM_EXEMPT.items():
        assert isinstance(reason, str) and len(reason) > 15, name
    # the S2' fact owner exists and lives on the producer side
    auth = REPO / "src" / "itsf" / "mc" / "platforms" / "authoritative.py"
    assert auth.exists()


# ===========================================================================
# D. lifecycle_config_digest
# ===========================================================================

def _preimage(cfg=None, **over):
    cfg = cfg or orch.LifecycleConfig(platform="topstep",
                                      sizing_policy="P2")
    kw = dict(engine="E1", scenario="Conservative",
              theta_channel="theta_0.5")
    kw.update(over)
    return A.lifecycle_config_preimage(cfg, **kw)


def test_preimage_enumerates_lifecycle_config_fields_mechanically():
    pre = _preimage()
    want = {f.name for f in dataclasses.fields(orch.LifecycleConfig)}
    assert set(pre["lifecycle_config_fields"]) == want
    # a hand-written whitelist would not survive this: the assertion is
    # generated from the dataclass itself.
    assert want, "LifecycleConfig has no fields?"


def test_harvest_contains_every_required_frozen_constant():
    got = A.harvest_frozen_constants()
    missing = [k for k in A.REQUIRED_HARVESTED_CONSTANTS if k not in got]
    assert missing == []


def test_harvest_is_mechanical_a_new_constant_enters_automatically(
        monkeypatch):
    monkeypatch.setattr(orch, "BRAND_NEW_FROZEN_KNOB_USD", 42.0,
                        raising=False)
    got = A.harvest_frozen_constants()
    assert got["itsf.mc.orchestrator:BRAND_NEW_FROZEN_KNOB_USD"] == 42.0


def test_a_new_constant_changes_the_digest(monkeypatch):
    before = A.lifecycle_config_digest(_preimage())
    monkeypatch.setattr(orch, "BRAND_NEW_FROZEN_KNOB_USD", 42.0,
                        raising=False)
    assert A.lifecycle_config_digest(_preimage()) != before


def test_unharvestable_constant_refuses_instead_of_being_skipped(
        monkeypatch):
    monkeypatch.setattr(orch, "WEIRD_CONSTANT", pathlib.Path("/tmp"),
                        raising=False)
    with pytest.raises(A.MCInputError) as exc:
        A.harvest_frozen_constants()
    assert exc.value.code == "lifecycle_config_unharvestable_constant"


def test_frozen_constant_exclusions_are_justified():
    """The exclusion set is PINNED: every entry must carry a reason, and
    the set is empty today. Adding one is a reviewed change."""
    assert dict(A.FROZEN_CONSTANT_EXCLUSIONS) == {}
    for key, reason in A.FROZEN_CONSTANT_EXCLUSIONS.items():
        assert isinstance(reason, str) and len(reason) > 20, key
        assert ":" in key


@pytest.mark.parametrize("name", sorted(A.harvest_frozen_constants()))
def test_mutating_any_harvested_constant_changes_the_digest(name,
                                                            monkeypatch):
    """MUTATION BATTERY: one byte of any result-relevant frozen constant
    must move the identity digest."""
    modname, attr = name.rsplit(":", 1)
    import importlib
    mod = importlib.import_module(modname)
    before = A.lifecycle_config_digest(_preimage())
    current = getattr(mod, attr)
    if isinstance(current, bool):
        new = not current
    elif isinstance(current, (int, float)):
        new = type(current)(current + 1)
    elif isinstance(current, str):
        new = current + "_MUTANT"
    elif isinstance(current, tuple):
        new = current + ("MUTANT",)
    elif isinstance(current, (set, frozenset)):
        new = type(current)(set(current) | {"MUTANT"})
    else:                                        # pragma: no cover
        pytest.fail(f"unhandled constant type for {name}")
    monkeypatch.setattr(mod, attr, new)
    assert A.lifecycle_config_digest(_preimage()) != before, name


@pytest.mark.parametrize("field,value", [
    ("platform", "lucid"),
    ("sizing_policy", "P3"),
    ("research_costs_usd", 1.0),
    ("decision_role", "sensitivity"),
    ("b2f_consumes_attempt", True),
])
def test_mutating_any_lifecycle_config_field_changes_the_digest(field,
                                                                value):
    base = orch.LifecycleConfig(platform="topstep", sizing_policy="P2")
    mutant = dataclasses.replace(base, **{field: value})
    assert (A.lifecycle_config_digest(_preimage(mutant))
            != A.lifecycle_config_digest(_preimage(base)))


@pytest.mark.parametrize("field,value", [
    ("engine", "E2"),
    ("scenario", "Stress"),
    ("theta_channel", "theta_0.3"),
])
def test_mutating_any_axis_changes_the_digest(field, value):
    assert (A.lifecycle_config_digest(_preimage(**{field: value}))
            != A.lifecycle_config_digest(_preimage()))


@pytest.mark.parametrize("name", ["PAYOUT_PATH_ID", "RNG_SPEC",
                                  "METHOD_VERSION",
                                  "ORCHESTRATOR_ALGO_VERSION",
                                  "REPLAY_ALGO_VERSION"])
def test_mutating_any_version_or_path_anchor_changes_the_digest(
        name, monkeypatch):
    before = A.lifecycle_config_digest(_preimage())
    monkeypatch.setattr(A, name, getattr(A, name) + "_MUTANT")
    assert A.lifecycle_config_digest(_preimage()) != before


def test_snapshot_anchors_are_the_already_frozen_hashes_not_new_values():
    from itsf import guards as g
    pre = _preimage()
    assert (pre["platform_params_snapshot_sha256"]
            == g.FROZEN_HASHES["gate1/platform_params.yaml"])
    assert (pre["snapshot_manifest_sha256"] == g.FROZEN_HASHES[
        "gate1/snapshots/2026-07-28/snapshot_manifest_v5.json"])
    assert pre["method_spec_sha256"] == g.FROZEN_HASHES[
        "MC_METHOD_SPEC.md"]


def test_preimage_missing_extra_and_schema_each_have_their_own_code():
    pre = _preimage()
    short = {k: v for k, v in pre.items() if k != "rng_spec"}
    with pytest.raises(A.MCInputError) as exc:
        A.lifecycle_config_digest(short)
    assert exc.value.code == "lifecycle_config_preimage_missing_field"

    wide = dict(pre)
    wide["surprise"] = 1
    with pytest.raises(A.MCInputError) as exc:
        A.lifecycle_config_digest(wide)
    assert exc.value.code == "lifecycle_config_preimage_extra_field"

    odd = dict(pre)
    odd[7] = "non-string key"
    with pytest.raises(A.MCInputError) as exc:
        A.lifecycle_config_digest(odd)
    assert exc.value.code == "lifecycle_config_preimage_unknown_field"

    bad = dict(pre)
    bad["schema"] = "something.else.v9"
    with pytest.raises(A.MCInputError) as exc:
        A.lifecycle_config_digest(bad)
    assert exc.value.code == "lifecycle_config_preimage_schema"


def test_preimage_refuses_a_non_lifecycle_config():
    with pytest.raises(A.MCInputError) as exc:
        A.lifecycle_config_preimage({"platform": "topstep"}, engine="E1",
                                    scenario="Base",
                                    theta_channel="theta_0.5")
    assert exc.value.code == "lifecycle_config_type_violation"


def test_non_finite_frozen_constant_is_tokenised_not_dropped():
    """lucid.FUNDED_TIERS carries an inf upper bound; JSON has no
    Infinity, and dropping it would silently un-bind a real parameter."""
    pre = _preimage()
    tiers = pre["frozen_constants"]["itsf.mc.platforms.lucid:FUNDED_TIERS"]
    assert "__inf__" in json.dumps(tiers)


def test_combo_string_is_a_rendered_label_not_an_authority():
    assert A.combo_label("lucid", "E2", "P2") == "lucid|E2|P2"
    # the label is a pure function of the authoritative fields, so it can
    # always be recomputed and compared — never parsed for authority.
    assert A.combo_label("lucid", "E2", "P2") != A.combo_label(
        "topstep", "E2", "P2")


# ===========================================================================
# E. key grid — four independent refusal codes
# ===========================================================================

def test_expected_grid_is_the_full_cartesian_product():
    grid = A.expected_key_grid(3, (0, 5, 9))
    assert len(grid) == 9
    assert (2, 9) in grid and (3, 0) not in grid


def test_key_grid_positive():
    reduced = A.check_key_grid(_grid_atoms(2, (0, 1)), B=2,
                               legal_phase_support=(0, 1))
    assert reduced["actual_phase_keys_by_world"] == {0: (0, 1), 1: (0, 1)}


def test_key_grid_duplicate():
    atoms = _grid_atoms(2, (0, 1))
    atoms.append(_atom(world_index=0, phase_offset=1))
    with pytest.raises(A.MCInputError) as exc:
        A.check_key_grid(atoms, B=2, legal_phase_support=(0, 1))
    assert exc.value.code == "key_grid_duplicate"


def test_key_grid_missing():
    atoms = _grid_atoms(2, (0, 1))[:-1]
    with pytest.raises(A.MCInputError) as exc:
        A.check_key_grid(atoms, B=2, legal_phase_support=(0, 1))
    assert exc.value.code == "key_grid_missing"


def test_key_grid_extra():
    atoms = _grid_atoms(2, (0, 1)) + [_atom(world_index=2, phase_offset=0)]
    with pytest.raises(A.MCInputError) as exc:
        A.check_key_grid(atoms, B=2, legal_phase_support=(0, 1))
    assert exc.value.code == "key_grid_extra"


def test_key_grid_substitution_is_its_own_code_not_a_count_pass():
    """A swapped key keeps |atoms| == B*M — the exact failure a count
    check cannot see."""
    atoms = _grid_atoms(2, (0, 1))
    atoms[-1] = _atom(world_index=5, phase_offset=9)
    assert len(atoms) == 4
    with pytest.raises(A.MCInputError) as exc:
        A.check_key_grid(atoms, B=2, legal_phase_support=(0, 1))
    assert exc.value.code == "key_grid_substitution"


@pytest.mark.parametrize("B,support,code", [
    (0, (0, 1), "key_grid_scale_invalid"),
    (True, (0, 1), "key_grid_scale_invalid"),
    (2, (), "key_grid_support_empty"),
    (2, (0, -1), "key_grid_support_invalid"),
    (2, (0, 0), "key_grid_support_duplicate"),
])
def test_expected_grid_input_validation(B, support, code):
    with pytest.raises(A.MCInputError) as exc:
        A.expected_key_grid(B, support)
    assert exc.value.code == code


def test_c1_and_c2_share_one_helper():
    """The container check and the certificate reduction must call the
    SAME implementation — two parallel checks drift."""
    src = (REPO / "src" / "itsf" / "mc" / "atoms.py").read_text(
        encoding="utf-8")
    assert src.count("def check_key_grid") == 1
    assert src.count("def expected_key_grid") == 1
    assert src.count("def reduce_actual_keys") == 1
    consumer = (REPO / "src" / "itsf" / "mc" / "consumer.py").read_text(
        encoding="utf-8")
    for banned in ("def expected_key_grid", "def reduce_actual_keys",
                   "def check_key_grid"):
        assert banned not in consumer, (
            "the consumer must reuse the atom layer's key-grid helper, "
            "never define a parallel one")


# ===========================================================================
# F. reductions, serialisation, two-level digests
# ===========================================================================

def test_observation_set_positive_and_derived_views():
    obs = _obs_set(B=2, support=(0, 1))
    assert obs.M == 2
    assert obs.combo == "topstep|E1|P2"
    assert obs.set_key == "base/topstep|E1|P2/Conservative"
    assert obs.world_means() == (0.5, 10.5)
    assert len(obs.within_world_ses()) == 2
    assert obs.total_predictive_evs() == (0.0, 1.0, 10.0, 11.0)
    assert obs.conditional_aleatoric_evs(1) == (10.0, 11.0)


def test_observation_set_declared_digest_is_recomputed_and_refused():
    obs = _obs_set()
    with pytest.raises(A.MCInputError) as exc:
        dataclasses.replace(obs, observations_digest="f" * 64)
    assert exc.value.code == "observation_set_digest_mismatch"


def test_observation_set_refuses_atoms_bound_to_another_run():
    atoms = _grid_atoms(2, (0, 1))
    atoms[0] = _atom(world_index=0, phase_offset=0, master_seed=13)
    with pytest.raises(A.MCInputError) as exc:
        _obs_set(atoms=atoms)
    assert exc.value.code == "atom_binding_mismatch"


def test_observation_set_refuses_a_foreign_lifecycle_config_digest():
    atoms = _grid_atoms(2, (0, 1))
    atoms[0] = _atom(world_index=0, phase_offset=0,
                     lifecycle_config_digest="d" * 64)
    with pytest.raises(A.MCInputError) as exc:
        _obs_set(atoms=atoms)
    assert exc.value.code == "lifecycle_config_digest_mismatch:atom"


def test_world_digest_disagreement_within_one_world_refuses():
    atoms = [_atom(world_index=0, phase_offset=0, world_digest=D64C),
             _atom(world_index=0, phase_offset=1, world_digest="e" * 64)]
    obs = _obs_set(B=1, support=(0, 1), atoms=atoms)
    with pytest.raises(A.MCInputError) as exc:
        obs.world_digests()
    assert exc.value.code == "world_content_binding_mismatch"


def test_jsonl_round_trip_is_byte_stable_and_lossless():
    obs = _obs_set()
    text = obs.to_jsonl()
    back = A.atoms_from_jsonl(text)
    assert back == obs.atoms
    assert A.atoms_to_jsonl(back) == text
    assert A.observations_digest(back) == obs.observations_digest
    assert "\n" in text and not text.endswith("\n")


def test_jsonl_row_field_set_is_exact():
    obs = _obs_set()
    row = json.loads(obs.to_jsonl().split("\n")[0])
    row["surprise"] = 1
    with pytest.raises(A.MCInputError) as exc:
        A.atom_from_canonical_dict(row)
    assert exc.value.code == "atom_row_extra_field"

    row.pop("surprise")
    row.pop("winning_days")
    with pytest.raises(A.MCInputError) as exc:
        A.atom_from_canonical_dict(row)
    assert exc.value.code == "atom_row_missing_field"


def test_one_flipped_byte_in_the_trace_changes_the_level1_digest():
    """PROBE: the flat digest is computed over the canonical bytes."""
    obs = _obs_set()
    tampered = list(obs.atoms)
    tampered[0] = _atom(world_index=0, phase_offset=0,
                        monthly_prop_operating_ev=0.000001)
    assert A.observations_digest(tampered) != obs.observations_digest


def test_two_level_digest_of_digests():
    a = _obs_set(run_label="base")
    b = _obs_set(run_label="double_B", B=2)
    table = {a.set_key: a.observations_digest,
             b.set_key: b.observations_digest}
    top = A.digest_of_digests(table)
    assert len(top) == 64
    table[b.set_key] = "f" * 64
    assert A.digest_of_digests(table) != top


def test_digest_of_digests_refuses_a_malformed_entry():
    with pytest.raises(A.MCInputError) as exc:
        A.digest_of_digests({"k": "not-a-digest"})
    assert exc.value.code == "atom_identity_digest_invalid"


# --- independent oracle for the reduction formulas -------------------------

def test_reductions_match_a_hand_computed_oracle():
    """INDEPENDENT ORACLE: expectations are written out by hand from the
    specification, NOT generated by calling the production reducer."""
    atoms = [_atom(world_index=0, phase_offset=0,
                   monthly_prop_operating_ev=1.0),
             _atom(world_index=0, phase_offset=1,
                   monthly_prop_operating_ev=3.0),
             _atom(world_index=1, phase_offset=0,
                   monthly_prop_operating_ev=10.0),
             _atom(world_index=1, phase_offset=1,
                   monthly_prop_operating_ev=20.0)]
    # world 0: mean (1+3)/2 = 2.0 ; world 1: mean (10+20)/2 = 15.0
    assert A.reduce_world_means(atoms) == (2.0, 15.0)
    # world 0 SE: sd = sqrt(((1-2)^2+(3-2)^2)/1) = sqrt(2) ; /sqrt(2) = 1.0
    ses = A.reduce_within_world_ses(atoms)
    assert ses[0] == pytest.approx(1.0, abs=1e-12)
    # world 1 SE: sd = sqrt(((10-15)^2+(20-15)^2)/1) = sqrt(50) ; /sqrt(2)
    assert ses[1] == pytest.approx(math.sqrt(50.0) / math.sqrt(2), abs=1e-12)
    # between-world sample sd of (2, 15) = sqrt(((2-8.5)^2+(15-8.5)^2)/1)
    assert A.sample_sd((2.0, 15.0)) == pytest.approx(
        math.sqrt(2 * 6.5 ** 2), abs=1e-12)


@pytest.mark.parametrize("values,q,want", [
    ((1.0, 2.0, 3.0, 4.0), 50, 2.5),          # h = 1.5 -> 2 + 0.5*(3-2)
    ((1.0, 2.0, 3.0, 4.0), 0, 1.0),
    ((1.0, 2.0, 3.0, 4.0), 100, 4.0),
    ((5.0,), 5, 5.0),                          # single sample
    ((0.0, 10.0), 5, 0.5),                     # h = 0.05
    ((0.0, 10.0), 95, 9.5),
])
def test_percentile_matches_the_type7_specification(values, q, want):
    """INDEPENDENT ORACLE: values computed by hand from
    `a + (b - a) * t` with `h = (n-1) * q/100`."""
    assert A.percentile_linear(list(values), q) == pytest.approx(
        want, abs=1e-12)


# --- C5: percentile numerical compatibility (independent numpy oracle) ----

def _numpy_percentile(values, q):
    """INDEPENDENT ORACLE: numpy's own type-7 'linear' implementation.
    Nothing here calls the production reducer to build an expectation."""
    import numpy as np
    return float(np.percentile(np.asarray(values, dtype=float), q,
                               method="linear"))


@pytest.mark.parametrize("q", [5, 50, 95])
@pytest.mark.parametrize("values", [
    (5.0,),                                        # n == 1
    (1.0, 2.0),                                    # even, tiny
    (1.0, 2.0, 3.0),                               # odd
    (-4.0, -1.0, 0.0, 3.5),                        # signed
    (-1e9, -1.0, 0.0, 1.0, 1e9),                   # magnitudes
    (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7),           # odd, binary-inexact
    (1e-9, 2e-9, 3.0000001e-9, 4e-9, 5e-9, 6e-9,   # even, subnormal-ish
     7e-9, 8e-9),
    tuple(float(i) * 1.0000000001 for i in range(101)),   # large n
])
def test_percentile_is_bitwise_equal_to_numpy(values, q):
    """C5: `==` on floats, NOT approx. The claim being made about the two
    reducers is BITWISE agreement, so the estimator must reproduce
    numpy's evaluation order exactly, including the t >= 0.5 branch."""
    got = A.percentile_linear(sorted(values), q)
    assert got == _numpy_percentile(sorted(values), q)


def test_percentile_is_bitwise_equal_to_numpy_on_random_samples():
    """Randomised sweep over n, sign and magnitude — every case bitwise."""
    import random
    rnd = random.Random(20260815)
    mismatches = []
    for _ in range(600):
        n = rnd.choice([1, 2, 3, 4, 5, 7, 8, 13, 40, 101])
        scale = rnd.choice([1e-6, 1.0, 1e3, 1e7])
        vals = sorted(rnd.uniform(-scale, scale) for _ in range(n))
        for q in (5, 50, 95):
            if A.percentile_linear(vals, q) != _numpy_percentile(vals, q):
                mismatches.append((n, q, vals[:3]))
    assert mismatches == []


def test_the_single_expression_form_is_the_measured_defect():
    """PROBE / MUTATION: turn the second branch OFF (the R2.3 form) and
    the numpy agreement must BREAK — otherwise this test proves nothing
    and the branch could be deleted unnoticed. The measured failure lies
    ENTIRELY in the t >= 0.5 half."""
    import math
    import random

    def single_expression(sorted_values, q):
        n = len(sorted_values)
        if n == 1:
            return float(sorted_values[0])
        h = (n - 1) * (float(q) / 100.0)
        lo, hi = math.floor(h), math.ceil(h)
        if lo == hi:
            return float(sorted_values[int(h)])
        t = h - lo
        a, b = float(sorted_values[lo]), float(sorted_values[hi])
        return a + (b - a) * t                     # <- the deleted defect

    rnd = random.Random(4242)
    broken_lo = broken_hi = seen_hi = 0
    for _ in range(400):
        n = rnd.choice([2, 3, 4, 5, 7, 8, 13, 40, 101])
        vals = sorted(rnd.uniform(-1e4, 1e4) for _ in range(n))
        for q in (5, 50, 95):
            h = (n - 1) * (q / 100.0)
            lo, hi = math.floor(h), math.ceil(h)
            if lo == hi:
                continue
            t = h - lo
            want = _numpy_percentile(vals, q)
            bad = single_expression(vals, q) != want
            if t >= 0.5:
                seen_hi += 1
                broken_lo += 0
                broken_hi += int(bad)
            else:
                broken_lo += int(bad)
            assert A.percentile_linear(vals, q) == want
    assert seen_hi > 0
    assert broken_hi > 0, "the mutation must break numpy agreement"
    assert broken_lo == 0, "the defect is confined to the t >= 0.5 branch"


def test_hot_and_cold_percentiles_are_bitwise_equal_but_not_shared_code():
    """The two reducers agree BITWISE while sharing no helper: the cold
    reducer imports nothing from itsf (pinned in
    tests/test_mc_cold_replay.py::test_cold_reducer_imports_nothing_from
    _itsf), so equality here is agreement about a SPECIFICATION."""
    import random

    from itsf.mc import cold_reducer as CR
    rnd = random.Random(99)
    for _ in range(200):
        n = rnd.choice([1, 2, 3, 6, 9, 25])
        vals = sorted(rnd.uniform(-1e5, 1e5) for _ in range(n))
        for q in (5, 50, 95):
            assert A.percentile_linear(vals, q) == \
                CR._quantile_linear(list(vals), q)
    assert A.percentile_linear is not CR._quantile_linear


def test_mean_sd_se_carry_the_pending_n_d2_provenance_note():
    """The numpy->pure-float migration changed ULP-level behaviour of
    these three estimators. This node does NOT re-change them; the note
    must stay until Aaron ratifies (master plan N-D2)."""
    for fn in (A.mean_of, A.sample_sd, A.stderr_of):
        doc = fn.__doc__ or ""
        assert "N-D2" in doc, fn.__name__
        assert "ratification" in doc, fn.__name__


@pytest.mark.parametrize("got,expected,ok", [
    (1.0, 1.0, True),
    (True, 1.0, False),                 # bool impersonating a float
    (1, 1.0, False),                    # int impersonating a float
    (1.0, 1, False),
    (False, 0.0, False),
    (True, True, True),
    (0, 0, True),
    (2.0, 1.0, False),                  # ordinary value mismatch
    ("1.0", 1.0, False),
])
def test_strict_scalar_equal_is_type_exact(got, expected, ok):
    """`True == 1.0` and `1 == 1.0` are true in Python; a declared-vs-
    derived check that used `!=` would accept both."""
    assert A.strict_scalar_equal(got, expected) is ok
    if ok:
        assert got == expected                     # ... and still equal


@pytest.mark.parametrize("got,expected,ok", [
    ((1.0, 0.0), (1.0, 0.0), True),
    ((True, False), (1.0, 0.0), False),            # the D-1 impersonation
    ((1, 0), (1.0, 0.0), False),
    ((1.0,), (1.0, 0.0), False),                   # length
    ([1.0, 0.0], (1.0, 0.0), False),               # not a tuple
    ((1.0, 2.0), (1.0, 0.0), False),               # value
])
def test_strict_float_sequence_equal_is_element_type_exact(got, expected,
                                                           ok):
    assert A.strict_float_sequence_equal(got, expected) is ok


def test_stderr_of_and_sample_sd_distinguish_empty_from_single():
    """D-2: the empty set has UNDEFINED dispersion — answering 0.0 would
    hand MC SS5 rule (d) a free pass. A single observation genuinely has
    zero ddof-1 dispersion and keeps 0.0."""
    for reducer in (A.stderr_of, A.sample_sd):
        with pytest.raises(A.MCInputError) as exc:
            reducer(())
        assert exc.value.code == "epistemic_samples_invalid"
        assert "not zero" in str(exc.value)
        assert reducer((5.0,)) == 0.0              # n == 1 is a real 0.0
    # ... and the asymmetry with mean_of is gone
    with pytest.raises(A.MCInputError) as exc:
        A.mean_of(())
    assert exc.value.code == "epistemic_samples_invalid"


def test_feasibility_counts_are_raw_with_no_gate_or_boolean():
    obs = _obs_set()
    counts = obs.feasibility_counts()
    assert "feasible" not in counts
    assert not any(isinstance(v, bool) for v in counts.values())
    assert counts["n_paths"] == 4
    assert counts["total_offered"] == 40           # 4 paths x 10 offered
    assert counts["ambiguous_share"] == pytest.approx(4 / 40)


# ===========================================================================
# G. BASELINE COUNTEREXAMPLES — the removed defects stay removed
# ===========================================================================

def test_payout_realized_field_is_gone():
    """It was derivable (`payout_count > 0`) and therefore a permanent
    forgery surface."""
    assert "payout_realized" not in A.ATOM_FIELDS
    with pytest.raises(TypeError):
        _atom(payout_realized=True)


def test_no_atom_field_is_a_caller_supplied_conclusion():
    banned = {"match", "matched", "verified", "replay_verified",
              "cold_replay_ok", "seal_ok", "feasible", "converged",
              "valid", "passed", "confirmed"}
    assert not (set(A.ATOM_FIELDS) & banned)
    for f in dataclasses.fields(A.ObservationSet):
        assert f.name not in banned


def test_the_atom_dataclass_is_deeply_frozen():
    a = _atom()
    with pytest.raises(dataclasses.FrozenInstanceError):
        a.winning_days = 999
    obs = _obs_set()
    with pytest.raises(dataclasses.FrozenInstanceError):
        obs.atoms = ()
    assert isinstance(obs.atoms, tuple)
    assert isinstance(obs.legal_phase_support, tuple)


def test_observation_set_shares_no_container_with_its_caller():
    atoms = _grid_atoms(2, (0, 1))
    support = [0, 1]
    obs = _obs_set(atoms=atoms, support=support)
    atoms.clear()
    support.append(99)
    assert len(obs.atoms) == 4
    assert obs.legal_phase_support == (0, 1)
