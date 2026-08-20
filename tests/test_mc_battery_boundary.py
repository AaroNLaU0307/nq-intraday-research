"""FACTORY BOUNDARY — a `PreparedMCInput` is seal-admissible ONLY if the
ten-check battery actually produced it (Codex synthetic reproduction;
baseline b3ac453).

The defect this file closes. B-PROV made the CUSTODY ROOT decisive: a
prepared input reaching the seal must carry the production attestation's
identity, and `_assert_seal_provenance` re-derives that attestation from
the code pins. What it could NOT prove is that the object in front of it
is the OUTPUT of `_prepare_mc_input_impl`. Every field is a public
dataclass parameter, so a caller who supplies a provenance triple and a
digest table consistent with the attestation gets a seal-admissible
object without the battery ever running — and may then choose the
battery-DERIVED fields freely:

    method_digest, seeds, k_per_seed, day_sequences, traded_day_sets,
    calendar, authorization_snapshot

Codex's reproduction, verbatim:

    direct_constructed=True
    battery_method_digest_changed=True
    seal_provenance_accepted=True
    full_seal_first_refusal=feasibility_gate_decision_required

"Stopped by the unrelated feasibility gate" is not a refusal.

Why the previous round's battery could not see this. Its forgeries were
certified by a TEST_ONLY authority over a SYNTHETIC bundle and then
claimed the REAL attestation's source strings, so they died at
`seal_custody_table_mismatch` — the synthetic bundle cannot reproduce the
real 14-file table. That is a true refusal but a WEAK test: it proves the
table check works, not that the battery ran. This file therefore builds a
PRODUCTION-LIKE authority — a synthetic attestation document whose
trial/commit, source id, source digest and complete 14-file table are
internally consistent with the synthetic bundle, loaded through the SAME
`load_custody_authority_from_attestation` constructor the production
prepare entry and the seal both use. Under it the provenance layer is
GENUINELY satisfied, and what remains is exactly the question "did the
battery run".

Synthetic fixtures only. No real market data, no registry or ledger
write, no real MC. The only real bytes read are the two FROZEN METHOD
files (MC_METHOD_SPEC.md, gate1/platform_params.yaml), copied into the
fixture root so the battery's method digest stays the production one;
both are method text with zero research values.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import shutil

import pytest

from conftest import make_trade_path
from itsf.contracts import RESEARCH_BOOTSTRAP_SEEDS
from itsf.mc import atoms as A
from itsf.mc import consumer as mcc
from itsf.mc.orchestrator import TemplateDay

TRIAL = "S0-T001"
COMMIT = "876c1b74131b4ab1a89dce433ecce646ba481f8c"
TP_DAYS = ("2026-08-03", "2026-08-05", "2026-08-07")
FP_DAYS = ("2026-08-04", "2026-08-06")
ALL_DAYS = tuple(sorted(TP_DAYS + FP_DAYS))
PRIMARY = mcc.PRIMARY_THETA_CHANNEL
# captured BEFORE any fixture patches the module constant
REAL_REPO_ROOT = mcc._REPO_ROOT
# the two files the battery's check (9) hashes against guards.FROZEN_HASHES
FROZEN_METHOD_FILES = ("MC_METHOD_SPEC.md", "gate1/platform_params.yaml")


# --- synthetic bundle -------------------------------------------------------

def _record_row(date, engine, scn, pnl):
    rec = make_trade_path([pnl / 2, pnl], date=date, engine=engine,
                          final=pnl)
    row = dataclasses.asdict(rec)
    row["cost_scenario"] = scn
    return row


def _calendar(n_days=8, n_offsets=2):
    return mcc.TemplateCalendar(
        days=tuple(TemplateDay(day_id=f"T{i:03d}", cal_offset=i)
                   for i in range(n_days)),
        first_month_offsets=tuple(range(n_offsets)))


def _bundle(pnl=80.0, *, trial=TRIAL, commit=COMMIT):
    files, counts = {}, {}
    for e in mcc.ENGINES:
        counts[e] = {}
        for s in mcc.SCENARIOS:
            rows = [_record_row(d, e, s, pnl) for d in ALL_DAYS]
            files[f"MC_HANDOFF_{e}_{s}.jsonl"] = "\n".join(
                json.dumps(r, sort_keys=True) for r in rows).encode("utf-8")
            counts[e][s] = {"n_records": len(rows)}
    files["S0_REPORT.json"] = json.dumps({
        "governance": {"trial_id": trial, "authorized_commit": commit},
        "oracle_daily": {PRIMARY: {"day_universe": {
            "tp_days": list(TP_DAYS), "fp_days": list(FP_DAYS)}}},
        "mc_handoff_manifest": {"counts": counts}}).encode("utf-8")
    files["S0_REPORT.md"] = b"# synthetic"
    files["HANDOFF_ADMISSION.json"] = json.dumps({"admitted": []}).encode()
    files["SEED_MANIFEST.json"] = json.dumps({
        "research_bootstrap_seeds": list(RESEARCH_BOOTSTRAP_SEEDS),
        "k_policy": "k_per_seed=200;k_start_index=0",
        "crn_scope": "shared_within_theta_engine_scenario"}).encode()
    files["REGISTRY_AFTER_RUN_STARTED.json"] = json.dumps({
        "snapshot_before": {"trial_id": trial,
                            "authorized_commit": commit}}).encode()
    files["manifest.jsonl"] = "\n".join(
        json.dumps({"record_type": "file", "relative_path": n,
                    "file_sha256": hashlib.sha256(files[n]).hexdigest()},
                   sort_keys=True) for n in sorted(files)).encode("utf-8")
    return files


# --- the PRODUCTION-LIKE custody authority (F3) -----------------------------

def _attestation_bytes(bundle, *, trial=TRIAL, commit=COMMIT) -> bytes:
    """A synthetic attestation document in the REAL grammar.

    `load_custody_authority_from_attestation` parses TRIAL_ID,
    AUTHORIZED_COMMIT and the `| name | bytes | sha256 |` rows. Emitting
    the table over THIS bundle is what makes the resulting authority
    production-like: `test_only=False`, the approved source id, and a
    14-file table the bundle genuinely reproduces — so the seal's five
    B-PROV checks all pass and only the battery question is left."""
    lines = ["# SYNTHETIC POST-RUN ATTESTATION (test fixture)", "",
             f"TRIAL_ID={trial}", f"AUTHORIZED_COMMIT={commit}", "",
             "| file | bytes | sha256 |", "| --- | --- | --- |"]
    for name in sorted(bundle):
        lines.append(f"| {name} | {len(bundle[name])} | "
                     f"{hashlib.sha256(bundle[name]).hexdigest()} |")
    return ("\n".join(lines) + "\n").encode("utf-8")


@pytest.fixture(scope="session")
def _fixture_root(tmp_path_factory):
    """A repo root the battery can read: the two FROZEN METHOD files
    copied verbatim (so check (9) yields the PRODUCTION method digest)
    plus an `ops/` directory for the synthetic attestation."""
    root = tmp_path_factory.mktemp("battery_boundary_root")
    (root / "ops").mkdir()
    (root / "gate1").mkdir()
    for rel in FROZEN_METHOD_FILES:
        shutil.copy2(REAL_REPO_ROOT / rel, root / rel)
    return root


@pytest.fixture()
def prod_like(_fixture_root, monkeypatch):
    """The GENUINE production-shaped battery product.

    Built through `prepare_mc_input` — the production entry — from raw
    attestation bytes, exactly as `real_input.prepare_real_mc_input`
    does. Three module constants are redirected so the whole production
    path can run against synthetic bytes:

      `_REPO_ROOT`                -> the fixture root (method files plus
                                     the synthetic attestation);
      `ATTESTATION_SHA256_PINNED` -> the synthetic document's digest, so
                                     the code pin is EXERCISED rather
                                     than bypassed;
      `build_template_calendar`   -> the small template calendar (the
                                     24-month CME build would make every
                                     lifecycle here ~60x longer and
                                     tests nothing about this boundary).

    Nothing about the BOUNDARY under test is patched: the authority is
    still constructed inside `load_custody_authority_from_attestation`,
    the battery still runs all ten checks, and the seal still re-derives
    the authority through the same constructor."""
    bundle = _bundle()
    att = _attestation_bytes(bundle)
    (_fixture_root / mcc.ATTESTATION_PATH).write_bytes(att)
    monkeypatch.setattr(mcc, "_REPO_ROOT", _fixture_root)
    monkeypatch.setattr(mcc, "ATTESTATION_SHA256_PINNED",
                        hashlib.sha256(att).hexdigest())
    monkeypatch.setattr(mcc, "build_template_calendar",
                        lambda *a, **k: _calendar())
    return mcc.prepare_mc_input(
        bundle, authorization_snapshot={"trial_id": TRIAL,
                                        "authorized_commit": COMMIT},
        attestation_bytes=att)


@pytest.fixture()
def test_prepared():
    """The TEST_ONLY entry's product — the honest test artifact."""
    b = _bundle()
    return mcc.prepare_mc_input_for_tests(
        b, authorization_snapshot={"trial_id": TRIAL,
                                   "authorized_commit": COMMIT},
        custody_authority=mcc.CustodyAuthority.for_tests(b),
        test_only_calendar=_calendar())


# --- evidence over whatever prepared input is handed in ---------------------

def _obs(prep, *, platform="topstep", engine="E1", scenario="Conservative",
         B=2, seed=7):
    return mcc.run_observation_set(
        prep, run_label="base", platform=platform, engine=engine,
        scenario=scenario, channel=PRIMARY, B=B, master_seed=seed)


def _evidence(prep, *, B=2, seed=7):
    results = {}
    for platform in ("lucid", "topstep"):
        for engine in ("E1", "E2"):
            cid = A.combo_label(platform, engine, "P2")
            results[cid] = (
                mcc.EpistemicResult.from_observations(_obs(
                    prep, platform=platform, engine=engine,
                    scenario="Conservative", B=B, seed=seed)),
                mcc.EpistemicResult.from_observations(_obs(
                    prep, platform=platform, engine=engine,
                    scenario="Stress", B=B, seed=seed)))
    return mcc.RunEvidence(
        run_label="base", axis="base", B=B,
        M=len(prep.calendar.first_month_offsets), K=200, master_seed=seed,
        prepared_digest=mcc.prepared_digest(prep), results=results)


def _seal(prep):
    return mcc.verdict_and_seal_from_evidence(
        prep, base=_evidence(prep), doubled_by_axis={}, seed_runs={})


def _seal_code(prep):
    with pytest.raises(mcc.MCInputError) as exc:
        _seal(prep)
    return exc.value.code


# --- the forgery routes -----------------------------------------------------

def _hand_built(prep, **claim):
    """Route 1 — the PUBLIC dataclass constructor. Every declared init
    field is copied off a genuine object and overridden with `claim`;
    the battery never runs."""
    names = {f.name for f in dataclasses.fields(prep) if f.init}
    kwargs = {n: getattr(prep, n) for n in names
              if n not in ("records", "records_digest")}
    kwargs.update({k: v for k, v in claim.items() if k in names})
    return mcc.PreparedMCInput(records=None, records_digest=None, **kwargs)


def _replaced(prep, **claim):
    """Route 2 — `dataclasses.replace`, which needs no field list at
    all: hand it a genuine battery product and name one field."""
    return dataclasses.replace(prep, **claim)


def _graft_receipt(target, donor):
    """Route 2b — the STOLEN receipt: a caller who cannot MAKE a receipt
    may still try to move a genuine one onto a mutated object."""
    receipt = getattr(donor, "battery_receipt", None)
    assert receipt is not None, (
        "the genuine battery product carries no receipt — the factory "
        "boundary does not exist")
    object.__setattr__(target, "battery_receipt", receipt)
    return target


# tamper values for every battery-constrained field (F4)
BATTERY_FIELDS = {
    "method_digest": lambda p: "f" * 64,
    "seeds": lambda p: tuple(reversed(p.seeds)),
    "k_per_seed": lambda p: p.k_per_seed * 2,
    "day_sequences": lambda p: {ch: seq[:-1]
                                for ch, seq in p.day_sequences.items()},
    "traded_day_sets": lambda p: {ch: frozenset(sorted(days)[:-1])
                                  for ch, days in p.traded_day_sets.items()},
    "calendar": lambda p: _calendar(n_days=6, n_offsets=3),
    "authorization_snapshot": lambda p: {"trial_id": TRIAL,
                                         "authorized_commit": COMMIT,
                                         "extra": "injected"},
}
# fields B-PROV already made decisive — re-pinned here so the matrix is
# COMPLETE and so a future reordering of the seal checks is visible
PROVENANCE_FIELDS = {
    "file_sha256": (lambda p: dict(p.file_sha256,
                                   **{"S0_REPORT.md": "a" * 64}),
                    "seal_custody_table_mismatch"),
    "trial_id": (lambda p: "S0-T999",
                 "seal_trial_commit_attestation_mismatch"),
    "authorized_commit": (lambda p: "1" * 40,
                          "seal_trial_commit_attestation_mismatch"),
    "source_artifact_id": (lambda p: "ops/NOT_THE_ATTESTATION.md",
                           "seal_provenance_source_violation"),
    "source_artifact_sha256": (lambda p: "0" * 64,
                               "seal_provenance_source_digest_violation"),
    "test_only": (lambda p: True, "seal_test_only_prepared_input"),
}
BATTERY_CODES = frozenset({"seal_prepared_not_battery_validated",
                           "seal_battery_receipt_mismatch"})


# ===========================================================================
# F3 — the fixture really is production-like (else everything below is weak)
# ===========================================================================

def test_the_fixture_authority_is_production_not_test_only(prod_like):
    """The prepared input is the PRODUCTION entry's product: a non-test
    authority, the approved source id, and the code-pinned source
    digest."""
    assert prod_like.test_only is False
    assert prod_like.source_artifact_id == mcc.ATTESTATION_PATH
    assert prod_like.source_artifact_sha256 == mcc.ATTESTATION_SHA256_PINNED


def test_the_five_bprov_provenance_checks_are_genuinely_satisfied(
        prod_like):
    """B-PROV's boundary ACCEPTS this object — test_only, source id,
    source digest, trial/commit and the full 14-file table all agree with
    the attestation re-derived at the seal. Nothing below can therefore
    be explained away as a table mismatch."""
    authority = mcc.load_custody_authority_from_attestation()
    assert authority.test_only is False
    assert (authority.trial_id, authority.authorized_commit) == (
        prod_like.trial_id, prod_like.authorized_commit)
    assert dict(authority.file_sha256) == dict(prod_like.file_sha256)
    assert len(dict(prod_like.file_sha256)) == len(mcc.BUNDLE_EXACT_SET) == 14
    # and the seal's own provenance layer raises nothing on it
    assert mcc._assert_seal_provenance(prod_like).test_only is False


# ===========================================================================
# F1 — the public constructor cannot mint a seal-admissible object
# ===========================================================================

def test_f1_public_constructor_product_is_refused_at_the_seal(prod_like):
    """THE finding. Copy a genuine production-shaped object field by
    field through `PreparedMCInput(...)` — the battery never runs — and
    change NOTHING. Provenance is satisfied by construction, so at the
    baseline the seal accepted it and stopped at the feasibility gate.
    It must now be refused as un-battery-validated."""
    forged = _hand_built(prod_like)
    assert mcc.prepared_digest(forged) == mcc.prepared_digest(prod_like)
    assert _seal_code(forged) == "seal_prepared_not_battery_validated"


def test_f1_public_constructor_product_carries_no_receipt(prod_like):
    """A hand-built object has no battery receipt to carry — and the
    field cannot be supplied through `__init__` at all."""
    assert getattr(_hand_built(prod_like), "battery_receipt", None) is None
    with pytest.raises(TypeError):
        mcc.PreparedMCInput(
            **{f.name: getattr(prod_like, f.name)
               for f in dataclasses.fields(prod_like) if f.init},
            battery_receipt=getattr(prod_like, "battery_receipt", None))


def test_f1_codex_reproduction_method_digest_swap_now_refuses(prod_like):
    """Codex's exact synthetic reproduction: direct construction plus a
    changed method digest. `seal_provenance_accepted=True` and
    `full_seal_first_refusal=feasibility_gate_decision_required` was the
    baseline behaviour; the refusal must now be the battery boundary."""
    forged = _hand_built(prod_like, method_digest="f" * 64)
    assert forged.method_digest != prod_like.method_digest
    code = _seal_code(forged)
    assert code != "feasibility_gate_decision_required"
    assert code in BATTERY_CODES


# ===========================================================================
# F2 — dataclasses.replace cannot launder a battery product
# ===========================================================================

@pytest.mark.parametrize("field", sorted(BATTERY_FIELDS))
def test_f2_replace_of_a_battery_field_loses_the_receipt(prod_like, field):
    """`dataclasses.replace` needs no field list and no forged
    provenance — it starts from the genuine article. Every
    battery-DERIVED field must therefore be unreplaceable in the only
    sense that matters: the product is not seal-admissible."""
    mutated = _replaced(prod_like, **{field: BATTERY_FIELDS[field](prod_like)})
    assert getattr(mutated, field) != getattr(prod_like, field)
    assert _seal_code(mutated) in BATTERY_CODES


@pytest.mark.parametrize("field", sorted(BATTERY_FIELDS))
def test_f2_a_stolen_receipt_does_not_revalidate_a_mutated_input(
        prod_like, field):
    """The receipt is UNFORGEABLE but not unmovable — so it must also be
    BOUND. Grafting the genuine receipt onto a mutated object must refuse
    under the mismatch code, not the absence code."""
    mutated = _graft_receipt(
        _replaced(prod_like, **{field: BATTERY_FIELDS[field](prod_like)}),
        prod_like)
    assert _seal_code(mutated) == "seal_battery_receipt_mismatch"


def test_f2_replace_that_changes_nothing_is_still_not_battery_validated(
        prod_like):
    """No-op replace included: `replace` is a CONSTRUCTOR call, and the
    boundary is about what constructed the object, not about whether the
    result happens to look identical."""
    same = _replaced(prod_like)
    assert mcc.prepared_digest(same) == mcc.prepared_digest(prod_like)
    assert _seal_code(same) == "seal_prepared_not_battery_validated"


def test_f2_a_receipt_cannot_be_rebuilt_by_replace(prod_like):
    """The receipt's own construction capability is consumed at build
    time, so `dataclasses.replace` cannot mint a re-pointed receipt
    either."""
    receipt = getattr(prod_like, "battery_receipt", None)
    assert receipt is not None
    with pytest.raises(mcc.MCInputError) as exc:
        dataclasses.replace(receipt, prepared_digest="f" * 64)
    assert exc.value.code == "battery_receipt_capability_required"


def test_f2_a_receipt_cannot_be_constructed_by_a_caller(prod_like):
    """Nor by calling the receipt type directly with every field copied
    from a genuine one — a genuine instance no longer holds the token."""
    receipt = getattr(prod_like, "battery_receipt", None)
    assert receipt is not None
    kwargs = {f.name: getattr(receipt, f.name)
              for f in dataclasses.fields(receipt) if f.init}
    assert kwargs.get("capability") is None, (
        "a genuine receipt still holds the construction capability — it "
        "must be dropped so no instance can hand it out")
    with pytest.raises(mcc.MCInputError) as exc:
        type(receipt)(**kwargs)
    assert exc.value.code == "battery_receipt_capability_required"


# ===========================================================================
# F4 — the complete field matrix, every field under its OWN code
# ===========================================================================

@pytest.mark.parametrize("field", sorted(BATTERY_FIELDS))
def test_f4_battery_field_matrix_refuses_before_feasibility(prod_like,
                                                            field):
    """Both forgery routes, every battery-constrained field: the refusal
    is a battery-boundary code and never the feasibility gate."""
    make = BATTERY_FIELDS[field]
    for forged in (_hand_built(prod_like, **{field: make(prod_like)}),
                   _replaced(prod_like, **{field: make(prod_like)})):
        code = _seal_code(forged)
        assert code in BATTERY_CODES, (field, code)


@pytest.mark.parametrize("field", sorted(PROVENANCE_FIELDS))
def test_f4_provenance_field_matrix_keeps_its_own_code(prod_like, field):
    """The B-PROV half of the matrix is unchanged by this round: each
    provenance field still refuses under its OWN specific code, ahead of
    the battery boundary, so the diagnostics do not collapse into one."""
    make, code = PROVENANCE_FIELDS[field]
    assert _seal_code(_replaced(prod_like, **{field: make(prod_like)})) == code


def test_f4_matrix_covers_every_declared_prepared_field(prod_like):
    """The matrix is COMPLETE against the dataclass, not against a hand
    list: every init field except the two DERIVED ones and the custody
    byte source (which `__post_init__` already pins bit for bit) is
    exercised above."""
    declared = {f.name for f in dataclasses.fields(prod_like) if f.init}
    derived = {"records", "records_digest"}
    byte_pinned = {"handoff_bytes"}
    assert declared - derived - byte_pinned == (
        set(BATTERY_FIELDS) | set(PROVENANCE_FIELDS))


# ===========================================================================
# F5 — positive paths: the boundary adds a refusal, it changes no semantics
# ===========================================================================

def test_f5_production_shaped_product_still_reaches_the_feasibility_gate(
        prod_like):
    """The genuine article passes the battery/receipt boundary and stops
    exactly where it stopped before — the honest missing decision."""
    assert _seal_code(prod_like) == "feasibility_gate_decision_required"
    assert mcc.FEASIBILITY_GATE_STATUS == "DECISION_REQUIRED"


def test_f5_test_prepared_still_computes_and_cold_replays(test_prepared):
    """A legal TEST prepared input keeps its full computational life:
    lifecycles run, and the unconditional cold replay is bitwise green."""
    receipt = mcc.cold_replay_evidence(test_prepared,
                                       [_evidence(test_prepared)])
    assert receipt["n_sets_replayed"] == 8
    for cmp in receipt["comparisons"].values():
        assert cmp["key_set_equal"] is True and cmp["mismatches"] == []


def test_f5_test_prepared_still_refuses_at_the_test_only_boundary(
        test_prepared):
    """And it is still refused by the PRODUCTION seal under the B-PROV
    code, not swallowed by the new one."""
    assert _seal_code(test_prepared) == "seal_test_only_prepared_input"


def test_f5_cold_replay_still_precedes_every_other_seal_refusal(prod_like):
    """N01 PHASE D3 invariant, re-pinned because this round edits the
    seal body again: a tampered trace surfaces `cold_replay_divergence`
    even when the input is ALSO un-battery-validated."""
    ev = _evidence(prod_like)
    cid = sorted(ev.results)[0]
    cons, stress = ev.results[cid]
    shifted = [dataclasses.replace(a, monthly_prop_operating_ev=-999.0)
               for a in cons.observations.atoms]
    tampered = A.ObservationSet.from_atoms(
        shifted, run_label=cons.observations.run_label,
        platform=cons.observations.platform,
        engine=cons.observations.engine,
        scenario=cons.observations.scenario,
        theta_channel=cons.observations.theta_channel,
        sizing_policy=cons.observations.sizing_policy,
        B=cons.observations.B, master_seed=cons.observations.master_seed,
        prepared_digest=cons.observations.prepared_digest,
        lifecycle_config_digest=cons.observations.lifecycle_config_digest,
        legal_phase_support=cons.observations.legal_phase_support)
    results = dict(ev.results)
    results[cid] = (mcc.EpistemicResult.from_observations(tampered), stress)
    bad = mcc.RunEvidence(run_label=ev.run_label, axis=ev.axis, B=ev.B,
                          M=ev.M, K=ev.K, master_seed=ev.master_seed,
                          prepared_digest=ev.prepared_digest,
                          results=results)
    with pytest.raises(mcc.MCInputError) as exc:
        mcc.verdict_and_seal_from_evidence(
            _hand_built(prod_like), base=bad, doubled_by_axis={},
            seed_runs={})
    assert exc.value.code == "cold_replay_divergence"


def test_f5_cold_replay_still_rebuilds_records_from_custody_bytes(
        prod_like):
    """The replay input is a NEW object parsed from the retained bytes —
    never the forward mapping — and it carries the SAME identity."""
    replay = mcc.replay_prepared_from_custody_bytes(prod_like)
    assert replay is not prod_like
    assert replay.records is not prod_like.records
    assert replay.records_digest == prod_like.records_digest
    assert mcc.prepared_digest(replay) == mcc.prepared_digest(prod_like)


def test_f5_cold_replay_carries_but_never_mints_a_receipt(prod_like):
    """E3. The replay rebuild carries a VALID receipt across (so the
    seal's own replay does not lose battery validation), and cannot
    create one for an input that never had it."""
    replay = mcc.replay_prepared_from_custody_bytes(prod_like)
    assert getattr(replay, "battery_receipt", None) is \
        getattr(prod_like, "battery_receipt", None)
    laundered = mcc.replay_prepared_from_custody_bytes(
        _hand_built(prod_like))
    assert getattr(laundered, "battery_receipt", None) is None
    assert _seal_code(laundered) == "seal_prepared_not_battery_validated"


# ===========================================================================
# E5 — one production constructor, and it is the battery's
# ===========================================================================

def test_e5_the_only_production_prepare_caller_is_real_input():
    """`real_input.prepare_real_mc_input` is the sole non-test caller of
    the production entry, and it reaches `PreparedMCInput` only through
    `prepare_mc_input` -> `_prepare_mc_input_impl`."""
    import inspect

    from itsf.mc import real_input
    src = inspect.getsource(real_input)
    assert "mcc.prepare_mc_input(" in src
    assert "PreparedMCInput(" not in src
    assert "PreparedMCInput(" in inspect.getsource(mcc._prepare_mc_input_impl)


def test_e5_seal_order_is_replay_then_boundary_then_reduction():
    """Ordering is a named invariant: unconditional cold replay first,
    then the battery/provenance boundary, then reduction (feasibility).
    Read off the seal body so a future reordering is loud."""
    import inspect
    body = inspect.getsource(mcc.verdict_and_seal_from_evidence)
    assert (body.index("cold_replay_evidence(")
            < body.index("_assert_seal_provenance(")
            < body.index("_reduce_primary_from_base("))
    assert "verify_battery_receipt(" in inspect.getsource(
        mcc._assert_seal_provenance)
