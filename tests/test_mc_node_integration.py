"""N01 x N02 cross-lane integration (MAIN AGENT owned).

Neither lane could verify these properties alone: lane S1 (unified atom
layer) tested its seam adapter against duck-typed stubs, and lane S2
(platform-authoritative events) tested emission without the consumer's
reduction layer. Everything here runs the REAL production path — real
`AccountEvent`s from real lifecycles into real atoms — and pins the
cross-lane agreements that would otherwise drift silently.

  A. VOCABULARY CROSS-PIN — the two lanes agreed a typed-absence token
     vocabulary BY SPECIFICATION, deliberately without importing each
     other. Nothing but this file notices if they drift apart.
  B. CROSS-LANE INVARIANT REACHABILITY — lane S1's atom refuses
     `contract_cap_hits > executed_trade_days`; lane S2's event permits
     `cap_applied=True` with `traded_n == 0` in principle. This pins that
     the production path never produces that combination, so the atom
     invariant is a guard on an unreachable state rather than a live
     contradiction between the lanes.
  C. DEFECT SCOPING — lane S2 confirmed a real defect in the FROZEN
     layer-1 accounting (`strategy_account_EV` understates a Lucid
     lifecycle that passes evaluation by the discarded evaluation
     profit). This pins the fact that decides how urgent it is: the
     Checkpoint-0 statistic (`prop_operating_EV`, S0 SS10.5 L233) is not a
     function of layer 1, so the defect cannot reach the verdict. The
     defect itself is Aaron's to rule on (master plan N-D2) and is NOT
     fixed here.
  D. END-TO-END SINGLE-SOURCE REDUCTION — the D1 contract, verified with
     real platform events rather than stubs: every reported quantity
     reduces from ONE atom set.
  E. FAIL-CLOSED — a factless event stream refuses; it never falls back
     to the deleted balance-delta derivation.
"""
from __future__ import annotations

import ast
import dataclasses
import hashlib
import json
import pathlib

import pytest

from conftest import make_trade_path
from itsf import contracts as C
from itsf.contracts import RESEARCH_BOOTSTRAP_SEEDS
from itsf.mc import atoms as A
from itsf.mc import consumer as mcc
from itsf.mc import orchestrator as orch
from itsf.mc.orchestrator import TemplateDay

TRIAL = "S0-T001"
COMMIT = "876c1b74131b4ab1a89dce433ecce646ba481f8c"
TP_DAYS = ("2026-08-03", "2026-08-05", "2026-08-07")
FP_DAYS = ("2026-08-04", "2026-08-06")
ALL_DAYS = tuple(sorted(TP_DAYS + FP_DAYS))
PRIMARY = mcc.PRIMARY_THETA_CHANNEL


# --- bundle fixtures (self-contained; deliberately not imported from the
# batteries the migration touches) -------------------------------------------

def _record_row(date: str, engine: str, scn: str, pnl: float) -> dict:
    rec = make_trade_path([pnl / 2, pnl], date=date, engine=engine,
                          final=pnl)
    row = dataclasses.asdict(rec)
    row["cost_scenario"] = scn
    return row


def _calendar(n_days: int = 8, n_offsets: int = 2) -> mcc.TemplateCalendar:
    days = tuple(TemplateDay(day_id=f"T{i:03d}", cal_offset=i)
                 for i in range(n_days))
    return mcc.TemplateCalendar(days=days,
                                first_month_offsets=tuple(range(n_offsets)))


def _bundle(*, pnl: float = 80.0) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    counts: dict = {}
    for e in mcc.ENGINES:
        counts[e] = {}
        for s in mcc.SCENARIOS:
            rows = [_record_row(d, e, s, pnl) for d in ALL_DAYS]
            files[f"MC_HANDOFF_{e}_{s}.jsonl"] = "\n".join(
                json.dumps(r, sort_keys=True) for r in rows).encode("utf-8")
            counts[e][s] = {"n_records": len(rows)}
    report = {
        "governance": {"trial_id": TRIAL, "authorized_commit": COMMIT},
        "oracle_daily": {
            PRIMARY: {"day_universe": {
                "tp_days": list(TP_DAYS), "fp_days": list(FP_DAYS)}},
            mcc.SECONDARY_THETA_CHANNEL: {"day_universe": {
                "tp_days": sorted(TP_DAYS + (FP_DAYS[0],)),
                "fp_days": [FP_DAYS[1]]}},
        },
        "mc_handoff_manifest": {"counts": counts},
    }
    files["S0_REPORT.json"] = json.dumps(report).encode("utf-8")
    files["S0_REPORT.md"] = b"# synthetic"
    files["HANDOFF_ADMISSION.json"] = json.dumps(
        {"admitted": ["SEED_MANIFEST.json"]}).encode("utf-8")
    files["SEED_MANIFEST.json"] = json.dumps({
        "research_bootstrap_seeds": list(RESEARCH_BOOTSTRAP_SEEDS),
        "k_policy": "k_per_seed=200;k_start_index=0",
        "crn_scope": "shared_within_theta_engine_scenario",
    }).encode("utf-8")
    files["REGISTRY_AFTER_RUN_STARTED.json"] = json.dumps({
        "snapshot_before": {"trial_id": TRIAL,
                            "authorized_commit": COMMIT}}).encode("utf-8")
    names = [n for n in sorted(files) if n != "manifest.jsonl"]
    files["manifest.jsonl"] = "\n".join(
        json.dumps({"record_type": "file", "relative_path": n,
                    "file_sha256": hashlib.sha256(files[n]).hexdigest()},
                   sort_keys=True) for n in names).encode("utf-8")
    return files


def _prepare(*, pnl: float = 80.0, n_days: int = 8, n_offsets: int = 2):
    b = _bundle(pnl=pnl)
    return mcc.prepare_mc_input_for_tests(
        b,
        authorization_snapshot={"trial_id": TRIAL,
                                "authorized_commit": COMMIT,
                                "event_sequence": 15},
        custody_authority=mcc.CustodyAuthority.for_tests(b),
        test_only_calendar=_calendar(n_days=n_days, n_offsets=n_offsets))


def _template_days(n: int = 40) -> list[TemplateDay]:
    return [TemplateDay(day_id=f"D{i:03d}", cal_offset=i) for i in range(n)]


def _paths(days, pnl: float, engine: str = "E1") -> dict:
    return {td.day_id: make_trade_path([pnl / 2, pnl], date=td.day_id,
                                       engine=engine, final=pnl)
            for td in days}


# =============================================================================
# A. Vocabulary cross-pin
# =============================================================================

def test_absence_token_vocabularies_agree_across_lanes():
    """The two lanes each define a typed-absence vocabulary and agreed on
    the token STRINGS by specification, NOT by importing one another
    (deliberate: neither module may depend on the other's layer). That
    agreement therefore has exactly one mechanical guard, and this is it.

    Every `OverBudgetStatus` lane S2 can emit must correspond to an
    `AbsentQuantity` lane S1 can carry, with a byte-identical token — a
    silent rename on either side changes what a sealed report MEANS while
    every other test stays green."""
    s2_tokens = {s.value for s in C.OverBudgetStatus}
    s1_tokens = {q.token for q in (A.NOT_APPLICABLE,
                                   A.NOT_APPLICABLE_NO_TRADE,
                                   A.PENDING_RULING,
                                   A.PENDING_ENGINEERING)}
    assert s2_tokens <= s1_tokens, (
        f"lane S2 can emit {sorted(s2_tokens - s1_tokens)} which lane S1 "
        "cannot represent")
    # and the shared ones must be spelled identically, not merely present
    for status in C.OverBudgetStatus:
        matching = [q for q in (A.NOT_APPLICABLE, A.NOT_APPLICABLE_NO_TRADE,
                                A.PENDING_RULING, A.PENDING_ENGINEERING)
                    if q.token == status.value]
        assert len(matching) == 1, status


def test_over_budget_predicate_stays_unruled_and_boolean_is_refused():
    """MC SS3 MANDATES the E2 over-budget disclosure but never DEFINES the
    predicate (which loss, which basis, which budget). Until Aaron rules
    (master plan N-D2), no lane may emit a boolean — a False would read
    downstream as a measured "did not exceed budget"."""
    assert C.OVER_BUDGET_PREDICATE_RULED is False
    with pytest.raises(C.AuthoritativeFactError):
        C.AccountEvent(day="D000", phase="xfa", balance=0.0, floor=0.0,
                       day_net_usd=0.0, account_generation=0,
                       requested_n=0, traded_n=0, cap_applied=False,
                       qualifying_day=False, over_budget=True)


def test_qualifying_phase_vocabulary_is_a_subset_of_emitted_phases():
    """Lane S2's `QUALIFYING_PHASES` names the phases whose frozen ruleset
    defines a qualifying day at all. A phase named there that no platform
    can emit would make the tri-state unreachable and silently turn every
    day into "no such concept"."""
    assert C.QUALIFYING_PHASES <= orch._ALLOWED_PHASES
    assert C.QUALIFYING_PHASES == frozenset({"funded", "xfa"})


# =============================================================================
# B. Cross-lane invariant reachability
# =============================================================================

@pytest.mark.parametrize("platform", ["lucid", "topstep"])
@pytest.mark.parametrize("pnl", [900.0, 150.0, 0.0, -400.0, -3000.0])
def test_cap_applied_never_true_with_zero_traded_size(platform, pnl):
    """Lane S1's atom refuses `contract_cap_hits > executed_trade_days`;
    lane S2's event type permits `cap_applied=True` with `traded_n == 0`
    (its own rule is only `cap_applied => traded_n < requested_n`). If the
    production path could ever produce that pair, a cap-forced-zero day
    would be counted as a cap hit on a day with no execution and the atom
    would refuse a legitimate run.

    It cannot: Lucid never computes a request while its cap is 0 (the
    orchestrator's `micros > 0` guard runs first, so a halt/dead day
    reports `requested_n == 0`), and Topstep's caps are the frozen
    scaling tiers {20, 30, 50} and COMBINE_MAX_MICROS=50 — never 0. This
    sweeps evaluation passes, funded trading, payout halts, breaches and
    restarts to hold that mechanically rather than by reading."""
    days = _template_days(40)
    cfg = orch.LifecycleConfig(platform=platform)
    res = orch.run_lifecycle(cfg, days, _paths(days, pnl))
    assert res.events, "no events emitted"
    for ev in res.events:
        if ev.cap_applied:
            assert ev.traded_n > 0, (
                f"{platform}/{pnl}: day {ev.day} reports a cap hit with "
                f"traded_n={ev.traded_n} (requested {ev.requested_n}) — "
                "lane S1's atom invariant would refuse this run")
        assert ev.traded_n <= ev.requested_n


@pytest.mark.parametrize("platform", ["lucid", "topstep"])
@pytest.mark.parametrize("pnl", [900.0, 150.0, -400.0])
def test_every_production_event_carries_the_authoritative_facts(platform,
                                                                pnl):
    """The seam is only fail-closed if the production producer actually
    fills it. A `None` here would make every atom refuse at run time
    rather than at test time."""
    days = _template_days(40)
    res = orch.run_lifecycle(orch.LifecycleConfig(platform=platform),
                             days, _paths(days, pnl))
    for ev in res.events:
        assert ev.day_net_usd is not None, ev.day
        assert ev.account_generation is not None, ev.day
        assert isinstance(ev.requested_n, int)
        assert isinstance(ev.traded_n, int)
        assert isinstance(ev.cap_applied, bool)


# =============================================================================
# C. Defect scoping — the layer-1 accounting defect cannot reach the verdict
# =============================================================================

def test_checkpoint0_statistic_is_insulated_from_layer1_accounting():
    """Lane S2 confirmed a REAL defect in frozen layer 1: for a Lucid
    lifecycle that passes evaluation, `strategy_account_ev_total`
    discards the evaluation profit (reported 0.0 where the authoritative
    sum is +3000.0 on two +1500 days).

    This pins the fact that bounds its blast radius: S0 SS10.5 L233 makes
    `prop_operating_EV` the Checkpoint-0 statistic, and the frozen chain
    computes it as payout_cash + terminal_cash - fees — layer 1 is NOT an
    input. So the defect is confined to an informational layer and cannot
    move a verdict.

    This test does NOT fix or bless the defect: correcting a frozen
    layer's number is Aaron's ruling (master plan N-D2)."""
    led = orch.Ledgers()
    led.payout_cash = 1234.5
    led.terminal_cash = 678.9
    led.book_fee("lucid_purchase", 98.0)
    baseline = led.report(0.0)

    for injected in (0.0, 3000.0, -50_000.0):
        led.strategy_account_pnl = injected
        report = led.report(0.0)
        assert report["prop_operating_ev_total"] == \
            baseline["prop_operating_ev_total"]
        assert report["net_business_ev_after_rd_total"] == \
            baseline["net_business_ev_after_rd_total"]
        assert report["risk_haircut_ev_total"] == \
            baseline["risk_haircut_ev_total"]
        # ... and layer 1 itself DOES move, so the pin above is a real
        # insulation result rather than a frozen-report artefact.
        assert report["strategy_account_ev_total"] == injected


def test_layer1_defect_is_recorded_not_silently_repaired():
    """The authoritative layer-1 accumulator exists alongside the legacy
    one precisely so the discrepancy is measurable; it must NOT have been
    quietly substituted into the frozen `ledger_report` (that would change
    a frozen number without a ruling)."""
    led = orch.Ledgers()
    led.strategy_account_pnl = 10.0
    led.strategy_account_pnl_authoritative = 3010.0
    report = led.report(0.0)
    assert report["strategy_account_ev_total"] == 10.0
    assert "authoritative" not in json.dumps(report)


# =============================================================================
# D. End-to-end single-source reduction (real events, not stubs)
# =============================================================================

def test_production_path_reduces_every_report_from_one_atom_set():
    """D1, verified end-to-end: one `ObservationSet` produced from REAL
    platform events, and every downstream report object carrying that same
    set's digest. Three caller-supplied summaries used to exist here
    (world means, within-world SEs, feasibility); if any reappears, its
    digest cannot match."""
    prepared = _prepare()
    obs = mcc.run_observation_set(
        prepared, run_label="base", platform="topstep", engine="E1",
        scenario="Conservative", channel=PRIMARY, B=2, master_seed=7)
    digest = obs.observations_digest

    epi = mcc.EpistemicResult.from_observations(obs)
    feas = mcc.FeasibilityEvidence.from_observations(obs)
    aleatoric = mcc.run_conditional_aleatoric(obs, world_index=0)
    total = mcc.run_total_predictive(obs)

    assert epi.observations_digest == digest
    assert feas.observations.observations_digest == digest
    assert aleatoric.observations_digest == digest
    assert total.observations_digest == digest
    # the atom count IS the grid, never a caller-declared expectation
    assert len(obs.atoms) == obs.B * len(prepared.calendar.first_month_offsets)


def test_atoms_carry_platform_authoritative_counts_not_balance_deltas():
    """The counts in an atom must come from lane S2's emitted facts. A
    payout day debits the balance, so any surviving balance-delta
    derivation would show up as a winning-day undercount — the exact
    defect lane S2's baseline counterexamples measured."""
    prepared = _prepare(pnl=900.0)
    obs = mcc.run_observation_set(
        prepared, run_label="base", platform="topstep", engine="E1",
        scenario="Conservative", channel=PRIMARY, B=1, master_seed=7)
    for atom in obs.atoms:
        assert atom.winning_days <= atom.executed_trade_days
        assert atom.days_profit_ge_150 <= atom.winning_days
        assert atom.executed_trade_days <= atom.offered_days


# =============================================================================
# E. Fail-closed — factless streams refuse, never fall back
# =============================================================================

def test_factless_event_stream_refuses_rather_than_falling_back():
    """The deleted balance-delta path must not come back as a fallback:
    an event stream without the authoritative fields REFUSES."""
    ev = C.AccountEvent(day="D000", phase="xfa", balance=100.0, floor=0.0)
    assert ev.day_net_usd is None
    with pytest.raises(mcc.MCInputError, match="platform_facts_absent"):
        A.path_facts_from_events([ev], engine="E1", platform="topstep")


def test_account_module_emits_factless_events_by_construction():
    """`itsf.mc.account.run_account` is a pre-N02 simulator that lane S2
    deliberately did not migrate (it is not on the production atom path).
    Pinned two ways so the fail-closed property is measured rather than
    assumed: it never sets a seam field (so everything it emits is
    factless BY CONSTRUCTION), and the production atom producer never
    calls it.

    Combined with `test_factless_event_stream_refuses_rather_than_falling
    _back`, that makes any future attempt to route it into the atom layer
    a refusal, never a silently fabricated fact."""
    src = (pathlib.Path(__file__).resolve().parents[1]
           / "src" / "itsf" / "mc" / "account.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    seam = {"day_net_usd", "account_generation", "requested_n", "traded_n",
            "cap_applied", "qualifying_day", "over_budget"}
    assigned = {kw.arg for node in ast.walk(tree)
                if isinstance(node, ast.Call)
                for kw in node.keywords if kw.arg}
    assert not (assigned & seam), (
        f"account.py now sets seam fields {sorted(assigned & seam)} — it "
        "was pinned as a factless legacy simulator")
    consumer_src = (pathlib.Path(__file__).resolve().parents[1] / "src"
                    / "itsf" / "mc" / "consumer.py").read_text(
                        encoding="utf-8")
    assert "run_account" not in consumer_src, (
        "the production atom producer must not route through the legacy "
        "factless simulator")


# =============================================================================
# F. Cross-lane surface pins (boundary-repair round)
#
# Lane S2' explicitly asked the main agent to own the ENGINES/PLATFORMS pin:
# the platform layer deliberately does NOT import `atoms` (that would make the
# producer depend on the consumer it feeds), so the two vocabularies agree by
# specification with nothing but this file watching them.
# =============================================================================

def test_engine_and_platform_vocabularies_agree_across_lanes():
    """`authoritative.verify_event_stream` takes engine/platform labels and
    refuses unknown ones; `atoms.path_facts_from_events` does the same with
    its OWN copies of those tuples. A rename or reordering on either side
    would silently split the two layers' idea of what a valid axis is."""
    from itsf.mc.platforms import authoritative as auth
    assert tuple(auth.ENGINES) == tuple(A.ENGINES)
    assert tuple(auth.PLATFORMS) == tuple(A.PLATFORMS)
    # ... and neither is empty, so the assertion above cannot pass vacuously
    assert auth.ENGINES and auth.PLATFORMS


def test_defence_in_depth_code_overlap_is_exactly_the_pinned_set():
    """Five invariants are enforced at BOTH the AccountEvent type and the
    stream verifier, deliberately sharing a code string: the code names the
    VIOLATED INVARIANT, not the layer that caught it. That is defence in
    depth, not a collision — but it has a cost worth pinning: a shared code
    (raised as the same `AuthoritativeFactError` from both layers) means a
    refusal alone cannot prove WHICH layer held. Lane S1' therefore proves
    the verifier is on the production path structurally (an AST pin on the
    call site plus a spy asserting one call per lifecycle), never by
    observing a code.

    This pins the overlap SET so a future code reused for a DIFFERENT rule
    at the other layer — a real collision — shows up as a diff here."""
    from itsf.mc.platforms import authoritative as auth
    type_codes = set(C.DAY_FACT_REJECTION_CODES)
    stream_codes = set(auth.AUTH_REJECTION_CODES)
    assert type_codes and stream_codes, "a code vocabulary is empty"
    assert type_codes & stream_codes == {
        "day_net_usd_not_finite",
        "over_budget_status_not_typed",
        "qualifying_day_absent_on_qualifying_phase",
        "qualifying_day_not_bool",
        "traded_n_exceeds_requested_n",
    }, sorted(type_codes & stream_codes)
    # the adapter layer keeps its own namespace: no atom/seam code may
    # collide with either of the two above (a third layer sharing a string
    # would make "the adapter refused" unprovable the same way).
    adapter_codes = {c for c in dir(A) if c.startswith("platform_facts_")}
    assert not (adapter_codes & (type_codes | stream_codes))


def test_verify_event_stream_matches_the_declared_cross_lane_interface():
    """The main agent pinned this signature before either lane started; S1'
    calls it and S2' implements it. It must stay a GATE — returning a value
    would let a caller treat its output as evidence."""
    import inspect
    from itsf.mc.platforms import authoritative as auth
    sig = inspect.signature(auth.verify_event_stream)
    assert list(sig.parameters) == ["events", "engine", "platform"]
    assert sig.parameters["engine"].kind is inspect.Parameter.KEYWORD_ONLY
    assert sig.parameters["platform"].kind is inspect.Parameter.KEYWORD_ONLY
    assert sig.return_annotation in (None, "None")


# =============================================================================
# G. The join — both lanes' REAL code on one production path
#
# Each lane proved its own half: S1' spied the verifier call and AST-pinned
# the call site; S2' proved the verifier's rules in isolation. Only here do
# a real platform stream, the real verifier and the real atom reduction run
# as one unit, so a seam that type-checks but disagrees semantically fails.
# =============================================================================

def test_the_production_join_refuses_a_tampered_fact_end_to_end():
    """Mutate ONE authoritative fact on the events a real lifecycle emits,
    exactly where the production path would consume them, and the run must
    refuse — never reduce the tampered stream into atoms.

    `AccountEvent` is a mutable dataclass (the orchestrator relabels
    `ev.day` by design), so construction-time validation cannot be the last
    word; this is the property that makes the stream verifier load-bearing
    rather than decorative."""
    from itsf.mc.platforms import authoritative as auth
    days = _template_days(40)
    res = orch.run_lifecycle(orch.LifecycleConfig(platform="topstep"),
                             days, _paths(days, 900.0))
    # the untampered stream is accepted — so the refusals below are caused
    # by the tamper, not by an unrelated defect in the fixture
    auth.verify_event_stream(res.events, engine="E1", platform="topstep")

    qualifying = [e for e in res.events if e.qualifying_day is not None]
    assert qualifying, "fixture produced no qualifying-phase event to tamper"
    original = qualifying[0].qualifying_day
    qualifying[0].qualifying_day = None          # C2: silent-zero attempt
    with pytest.raises(C.AuthoritativeFactError):
        auth.verify_event_stream(res.events, engine="E1", platform="topstep")
    with pytest.raises(mcc.MCInputError):
        A.path_facts_from_events(res.events, engine="E1", platform="topstep")
    qualifying[0].qualifying_day = original

    traded = [e for e in res.events if e.traded_n > 0]
    assert traded, "fixture produced no traded day to tamper"
    traded[0].over_budget = True                 # C3: unruled predicate
    with pytest.raises(C.AuthoritativeFactError):
        auth.verify_event_stream(res.events, engine="E2", platform="topstep")
    with pytest.raises(mcc.MCInputError):
        A.path_facts_from_events(res.events, engine="E2", platform="topstep")


def test_day_universe_equality_codes_exist_and_the_fixture_satisfies_them():
    """C6 landed three refusal codes for the sealed-input integrity
    equality. This pins that they are reachable names AND that this file's
    own production-shaped bundle satisfies the equality — if the fixture
    ever drifted out of the producer's own construction, every other test
    in this file would be exercising an impossible sealed input."""
    prepared = _prepare()
    ref = frozenset(prepared.records[("E1", "Base")])
    unions = set()
    for channel, seq in prepared.day_sequences.items():
        assert frozenset(seq) == ref, channel
        unions.add(frozenset(seq))
    assert len(unions) == 1, "theta channels disagree on the day universe"
    src = (pathlib.Path(__file__).resolve().parents[1] / "src" / "itsf"
           / "mc" / "consumer.py").read_text(encoding="utf-8")
    for code in ("fp_day_without_record", "theta_population_drift",
                 "record_without_oracle_class"):
        assert code in src, code
