"""B-PROV — custody PROVENANCE must survive the prepare battery and be
RE-VERIFIED at the seal (Fable V2 blocking finding; baseline 54ab7f2).

The defect, exactly. `CustodyAuthority` carries three provenance facts —
`test_only`, `source_artifact_id`, `source_artifact_sha256` — and
`_prepare_mc_input_impl` consumed the authority's DIGEST TABLE and then
dropped all three on the floor. Nothing downstream could tell a
TEST_ONLY_SYNTHETIC authority from the code-pinned production
attestation, `prepared_digest` did not bind the difference, and
`verdict_and_seal_from_evidence` never asked. Four separate ways of
producing a prepared input therefore walked the whole seal path and were
stopped only by the UNRELATED feasibility gate:

  path 1  the TEST_ONLY prepare entry's own product;
  path 2  a hand-constructed PreparedMCInput that never ran the battery;
  path 3  an identity pinning only the 8 handoff files instead of the
          full 14-file BUNDLE_EXACT_SET;
  path 4  a forged source string that does not match the code pin.

"Stopped by an unrelated gate" is not a refusal. Every path below must
refuse under its OWN code, and the forward path must be untouched.

Synthetic fixtures only. No real data, no registry or ledger writes; the
one real byte source read here is the blind post-run attestation, which
is custody metadata with zero research values (the same document
`test_mc_custody_calendar` already reads).
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
from types import MappingProxyType

import pytest

from conftest import make_trade_path
from itsf.contracts import RESEARCH_BOOTSTRAP_SEEDS
from itsf.mc import atoms as A
from itsf.mc import consumer as mcc
from itsf.mc.orchestrator import TemplateDay

TRIAL = "S0-T001"
COMMIT = "876c1b74131b4ab1a89dce433ecce646ba481f8c"
FOREIGN_TRIAL = "S0-T999"
FOREIGN_COMMIT = "1" * 40
TP_DAYS = ("2026-08-03", "2026-08-05", "2026-08-07")
FP_DAYS = ("2026-08-04", "2026-08-06")
ALL_DAYS = tuple(sorted(TP_DAYS + FP_DAYS))
PRIMARY = mcc.PRIMARY_THETA_CHANNEL


# --- synthetic bundle / prepared input (same shape as the DR-5 batteries) ---

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
    names = [n for n in sorted(files)]
    files["manifest.jsonl"] = "\n".join(
        json.dumps({"record_type": "file", "relative_path": n,
                    "file_sha256": hashlib.sha256(files[n]).hexdigest()},
                   sort_keys=True) for n in names).encode("utf-8")
    return files


def _prepare(bundle=None, *, trial=TRIAL, commit=COMMIT):
    b = _bundle(trial=trial, commit=commit) if bundle is None else bundle
    return mcc.prepare_mc_input_for_tests(
        b, authorization_snapshot={"trial_id": trial,
                                   "authorized_commit": commit},
        custody_authority=mcc.CustodyAuthority.for_tests(b),
        test_only_calendar=_calendar())


@pytest.fixture()
def prepared():
    return _prepare()


def _obs(prep, *, platform="topstep", engine="E1",
         scenario="Conservative", B=2, seed=7):
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
    return mcc.RunEvidence(run_label="base", axis="base", B=B, M=2, K=200,
                           master_seed=seed,
                           prepared_digest=mcc.prepared_digest(prep),
                           results=results)


def _seal(prep, base):
    return mcc.verdict_and_seal_from_evidence(
        prep, base=base, doubled_by_axis={}, seed_runs={})


# --- the forgery helper -----------------------------------------------------

def _rebuild(prep, **claim):
    """Hand-construct a PreparedMCInput out of `prep`'s CURRENT fields,
    overriding with `claim`.

    Claim keys the dataclass does not declare are DROPPED. That is
    deliberate and is what makes this battery red at the baseline for
    the RIGHT reason: at 54ab7f2 the three provenance fields do not
    exist, so every forgery below degenerates into an honest copy and
    the seal path lets it through to the feasibility gate — which is
    precisely the finding.

    `init=False` fields are excluded: `battery_receipt` (the factory
    boundary) is not a constructor parameter at all, which is the whole
    point of it — see `test_mc_battery_boundary`. Every forgery below
    therefore arrives at the seal receipt-less, and is refused by the
    B-PROV check that fires FIRST for its particular claim."""
    names = {f.name for f in dataclasses.fields(prep) if f.init}
    kwargs = {n: getattr(prep, n) for n in names
              if n not in ("records", "records_digest")}
    kwargs.update({k: v for k, v in claim.items() if k in names})
    return mcc.PreparedMCInput(records=None, records_digest=None, **kwargs)


_PRODUCTION_CLAIM = {
    "test_only": False,
    "source_artifact_id": mcc.ATTESTATION_PATH,
    "source_artifact_sha256": mcc.ATTESTATION_SHA256_PINNED,
}


# ===========================================================================
# A. the three provenance facts survive the battery and enter the identity
# ===========================================================================

def test_bprov_battery_retains_the_authority_provenance(prepared):
    """The prepared input must carry WHICH authority certified it."""
    assert prepared.test_only is True
    assert prepared.source_artifact_id == "TEST_ONLY_SYNTHETIC"
    assert prepared.source_artifact_sha256 == "0" * 64


def test_bprov_provenance_is_bound_into_the_prepared_digest(prepared):
    """Retaining is not enough: two prepared inputs that disagree about
    their custody source must not share one identity."""
    d0 = mcc.prepared_digest(prepared)
    for claim in ({"test_only": False},
                  {"source_artifact_id": "ops/SOMETHING_ELSE.md"},
                  {"source_artifact_sha256": "1" * 64}):
        assert mcc.prepared_digest(_rebuild(prepared, **claim)) != d0, claim


def test_bprov_provenance_is_inside_the_pinned_identity_preimage(prepared):
    """The cold replay starts from `prepared_identity_bytes`, so the
    provenance has to be IN those bytes, not only on the live object."""
    ident = json.loads(
        mcc.prepared_identity_bytes(prepared).decode("utf-8"))
    assert ident["provenance"] == {
        "source_artifact_id": prepared.source_artifact_id,
        "source_artifact_sha256": prepared.source_artifact_sha256,
        "test_only": prepared.test_only}


def test_bprov_cold_replay_rebuild_carries_the_provenance(prepared):
    """The replay input is rebuilt field by field; a dropped provenance
    field would either change the digest or silently launder the claim."""
    replay = mcc.replay_prepared_from_custody_bytes(prepared)
    assert replay.test_only is prepared.test_only
    assert replay.source_artifact_id == prepared.source_artifact_id
    assert replay.source_artifact_sha256 == prepared.source_artifact_sha256
    assert mcc.prepared_digest(replay) == mcc.prepared_digest(prepared)


# ===========================================================================
# B. the four Fable paths — each refuses under its OWN code
# ===========================================================================

def test_bprov_path1_test_entry_artifact_cannot_reach_the_seal(prepared):
    """PATH 1. The TEST_ONLY prepare entry's own product reached the
    seal's decision layer and was stopped only by the feasibility gate.
    It must now be refused as what it is."""
    with pytest.raises(mcc.MCInputError) as exc:
        _seal(prepared, _evidence(prepared))
    assert exc.value.code == "seal_test_only_prepared_input"


def test_bprov_path2_direct_construction_cannot_reach_the_seal(prepared):
    """PATH 2. A PreparedMCInput assembled by hand — the ten-check
    battery never ran — claiming the production attestation verbatim.
    The claim is now checked against the attestation's OWN digest table,
    which a synthetic bundle cannot reproduce."""
    forged = _rebuild(prepared, **_PRODUCTION_CLAIM)
    with pytest.raises(mcc.MCInputError) as exc:
        _seal(forged, _evidence(forged))
    assert exc.value.code == "seal_custody_table_mismatch"


def test_bprov_path3_eight_of_fourteen_coverage_is_unconstructible(
        prepared):
    """PATH 3. `__post_init__` pinned only the 8 MC_HANDOFF_* files, so
    an identity covering 8 of the 14 sealed bundle members was legal —
    and the seal's `bundle_file_sha256` table inherited the hole."""
    partial = {n: prepared.file_sha256[n]
               for n in sorted(mcc.HANDOFF_FILE_SET)}
    assert len(partial) == 8 and len(mcc.BUNDLE_EXACT_SET) == 14
    with pytest.raises(mcc.MCInputError) as exc:
        _rebuild(prepared, file_sha256=MappingProxyType(partial))
    assert exc.value.code == "prepared_bundle_coverage_violation"


@pytest.mark.parametrize("claim,code", [
    ({"test_only": False,
      "source_artifact_id": "ops/NOT_THE_ATTESTATION.md",
      "source_artifact_sha256": mcc.ATTESTATION_SHA256_PINNED},
     "seal_provenance_source_violation"),
    ({"test_only": False,
      "source_artifact_id": mcc.ATTESTATION_PATH,
      "source_artifact_sha256": "0" * 64},
     "seal_provenance_source_digest_violation"),
])
def test_bprov_path4_forged_source_strings_lose_to_the_code_pin(
        prepared, claim, code):
    """PATH 4. A source string is a claim, not a proof: it must be
    re-checked at the seal against ATTESTATION_PATH /
    ATTESTATION_SHA256_PINNED, which live in reviewed code."""
    forged = _rebuild(prepared, **claim)
    with pytest.raises(mcc.MCInputError) as exc:
        _seal(forged, _evidence(forged))
    assert exc.value.code == code


def test_bprov_seal_trial_commit_must_equal_the_attestation_parse():
    """The seal binds the prepared input to the trial the attestation
    actually attests: a bundle sealed under another trial cannot borrow
    S0-T001's custody root even with the source pins copied."""
    foreign = _prepare(trial=FOREIGN_TRIAL, commit=FOREIGN_COMMIT)
    assert foreign.trial_id == FOREIGN_TRIAL
    forged = _rebuild(foreign, **_PRODUCTION_CLAIM)
    with pytest.raises(mcc.MCInputError) as exc:
        _seal(forged, _evidence(forged))
    assert exc.value.code == "seal_trial_commit_attestation_mismatch"


# ===========================================================================
# C. FORWARD PATH — the fix adds a boundary, it changes no semantics
# ===========================================================================

def test_bprov_forward_path_still_reaches_the_feasibility_refusal(prepared):
    """A genuine battery product still reduces all the way to the frozen
    DECISION_REQUIRED refusal. The feasibility rule is untouched: it is
    still the missing decision, and it is still the thing that stops
    Checkpoint-0."""
    with pytest.raises(mcc.MCInputError) as exc:
        mcc._reduce_primary_from_base(_evidence(prepared))
    assert exc.value.code == "feasibility_gate_decision_required"
    assert mcc.FEASIBILITY_GATE_STATUS == "DECISION_REQUIRED"


def test_bprov_forward_path_cold_replay_receipt_is_still_green(prepared):
    """The unconditional cold replay is unaffected — same eight sets,
    same bitwise agreement."""
    receipt = mcc.cold_replay_evidence(prepared, [_evidence(prepared)])
    assert receipt["n_sets_replayed"] == 8
    for cmp in receipt["comparisons"].values():
        assert cmp["key_set_equal"] is True
        assert cmp["mismatches"] == []


def test_bprov_check_does_not_pre_empt_the_unconditional_cold_replay(
        prepared):
    """N01 PHASE D3 invariant, re-pinned because this round edits the
    seal body: the replay runs FIRST and unconditionally, so a tampered
    trace still surfaces `cold_replay_divergence` — never the new
    provenance code."""
    ev = _evidence(prepared)
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
        _seal(prepared, bad)
    assert exc.value.code == "cold_replay_divergence"
