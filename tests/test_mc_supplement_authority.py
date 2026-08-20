"""N03 — supplement authority / custody binding (lane S1).

Every fixture here is SYNTHETIC. No Development data is read, no sealed
S0 result value is touched, no directory is created under the ruled
output roots, no registry row is appended, no supplement is executed or
sealed. The only real bytes read are the two FROZEN METHOD files
(MC_METHOD_SPEC.md, gate1/platform_params.yaml) copied into a tmp fixture
root so the prepare battery's method digest stays the production one —
method text with zero research values, exactly as
`tests/test_mc_battery_boundary.py` already does.

What this file has to prove, in the order the acceptance list asks it:

  1  an authority is constructible ONLY from an approved custody source —
     the module-private capability plus a VERIFIED battery receipt;
  2  a TEST_ONLY prepared input has no production entry;
  3  every bound fact refuses under its OWN code, never a collapsed one;
  4  ref_dates, the per-θ population and each θ's TP∪FP are ONE set;
  5  TP∩FP is empty;
  6  cross-θ population identity;
  7  missing / duplicate / extra / SUBSTITUTED (same count!) / drifted
     days each refuse under their own code;
  8  a SYNCHRONIZED rewrite — bundle, manifest and attestation all
     regenerated together, internally consistent at every custody layer —
     still cannot get a broken day universe onto the supplement path;
  9  no outcome value is read or emitted;
 10  completing N03 authorizes nothing.

Negative fixtures follow the house discipline: first assert the near-miss
is GENUINELY near (the forgery passes the checks it is supposed to pass),
only then assert the refusal. A negative test that dies for the wrong
reason proves nothing.
"""
from __future__ import annotations

import dataclasses
import hashlib
import inspect
import json
import re
import shutil
from types import MappingProxyType

import pytest

from conftest import make_trade_path
from itsf.contracts import RESEARCH_BOOTSTRAP_SEEDS, TradePathRecord
from itsf.mc import consumer as mcc
from itsf.mc import day_strata_supplement as dss
from itsf.mc import supplement_authority as sa
from itsf.mc import supplement_contract as sc
from itsf.mc.orchestrator import TemplateDay

TRIAL = "S0-T001"
COMMIT = "876c1b74131b4ab1a89dce433ecce646ba481f8c"
PRIMARY = mcc.PRIMARY_THETA_CHANNEL          # 'theta_0.5'
SECONDARY = mcc.SECONDARY_THETA_CHANNEL      # 'theta_0.3'

# five synthetic trade days, split differently by the two θ channels but
# spanning the SAME population — which is exactly what §D.2.2 requires
ALL_DAYS = ("2026-08-03", "2026-08-04", "2026-08-05", "2026-08-06",
            "2026-08-07")
TP_BY_CHANNEL = {PRIMARY: ("2026-08-03", "2026-08-05", "2026-08-07"),
                 SECONDARY: ("2026-08-03", "2026-08-04", "2026-08-05",
                             "2026-08-07")}
FP_BY_CHANNEL = {PRIMARY: ("2026-08-04", "2026-08-06"),
                 SECONDARY: ("2026-08-06",)}
# a day that exists in NO handoff file — the "invented day" probe
UNRECORDED_DAY = "2026-08-10"

REAL_REPO_ROOT = mcc._REPO_ROOT
FROZEN_METHOD_FILES = ("MC_METHOD_SPEC.md", "gate1/platform_params.yaml")


# ===========================================================================
# synthetic bundle / attestation / prepared inputs
# ===========================================================================

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


def _default_oracle():
    return {ch: {"day_universe": {"tp_days": list(TP_BY_CHANNEL[ch]),
                                  "fp_days": list(FP_BY_CHANNEL[ch])}}
            for ch in (PRIMARY, SECONDARY)}


def _bundle(pnl=80.0, *, trial=TRIAL, commit=COMMIT, oracle=None,
            days=ALL_DAYS):
    files, counts = {}, {}
    for e in mcc.ENGINES:
        counts[e] = {}
        for s in mcc.SCENARIOS:
            rows = [_record_row(d, e, s, pnl) for d in days]
            files[f"MC_HANDOFF_{e}_{s}.jsonl"] = "\n".join(
                json.dumps(r, sort_keys=True) for r in rows).encode("utf-8")
            counts[e][s] = {"n_records": len(rows)}
    files["S0_REPORT.json"] = json.dumps({
        "governance": {"trial_id": trial, "authorized_commit": commit},
        "oracle_daily": oracle if oracle is not None else _default_oracle(),
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


def _attestation_bytes(bundle, *, trial=TRIAL, commit=COMMIT) -> bytes:
    """A synthetic attestation in the REAL grammar (same technique as
    `tests/test_mc_battery_boundary.py`): trial/commit lines plus the
    `| name | bytes | sha256 |` table over THIS bundle, so the resulting
    authority is production-like — `test_only=False`, the approved source
    id, and a 14-file table the bundle genuinely reproduces."""
    lines = ["# SYNTHETIC POST-RUN ATTESTATION (test fixture)", "",
             f"TRIAL_ID={trial}", f"AUTHORIZED_COMMIT={commit}", "",
             "| file | bytes | sha256 |", "| --- | --- | --- |"]
    for name in sorted(bundle):
        lines.append(f"| {name} | {len(bundle[name])} | "
                     f"{hashlib.sha256(bundle[name]).hexdigest()} |")
    return ("\n".join(lines) + "\n").encode("utf-8")


@pytest.fixture(scope="session")
def _fixture_root(tmp_path_factory):
    root = tmp_path_factory.mktemp("supplement_authority_root")
    (root / "ops").mkdir()
    (root / "gate1").mkdir()
    for rel in FROZEN_METHOD_FILES:
        shutil.copy2(REAL_REPO_ROOT / rel, root / rel)
    return root


def _prepare_production(bundle, root, monkeypatch):
    """Run the PRODUCTION prepare entry over a synthetic bundle.

    The three redirections are the ones `test_mc_battery_boundary` already
    uses; none of them touches the boundary under test. The code pin is
    REPOINTED at the synthetic document, never bypassed."""
    att = _attestation_bytes(bundle)
    (root / mcc.ATTESTATION_PATH).write_bytes(att)
    monkeypatch.setattr(mcc, "_REPO_ROOT", root)
    monkeypatch.setattr(mcc, "ATTESTATION_SHA256_PINNED",
                        hashlib.sha256(att).hexdigest())
    monkeypatch.setattr(mcc, "build_template_calendar",
                        lambda *a, **k: _calendar())
    return mcc.prepare_mc_input(
        bundle, authorization_snapshot={"trial_id": TRIAL,
                                        "authorized_commit": COMMIT},
        attestation_bytes=att)


@pytest.fixture()
def prod_like(_fixture_root, monkeypatch):
    """The GENUINE production-shaped battery product."""
    return _prepare_production(_bundle(), _fixture_root, monkeypatch)


def _prepare_for_tests(bundle):
    return mcc.prepare_mc_input_for_tests(
        bundle, authorization_snapshot={"trial_id": TRIAL,
                                        "authorized_commit": COMMIT},
        custody_authority=mcc.CustodyAuthority.for_tests(bundle),
        test_only_calendar=_calendar())


@pytest.fixture()
def test_bundle():
    return _bundle()


@pytest.fixture()
def test_prepared(test_bundle):
    """The TEST_ONLY entry's product — the honest synthetic artifact."""
    return _prepare_for_tests(test_bundle)


@pytest.fixture()
def authority(test_prepared):
    return sa.derive_supplement_authority_for_tests(test_prepared)


# ===========================================================================
# forgery routes (mirrors of the ones in test_mc_battery_boundary.py)
# ===========================================================================

def _hand_built(prep, **claim):
    """The PUBLIC dataclass constructor: every declared init field copied
    off a genuine object, `claim` overriding. The battery never runs, so
    the product carries no receipt."""
    names = {f.name for f in dataclasses.fields(prep) if f.init}
    kwargs = {n: getattr(prep, n) for n in names
              if n not in ("records", "records_digest")}
    kwargs.update({k: v for k, v in claim.items() if k in names})
    return mcc.PreparedMCInput(records=None, records_digest=None, **kwargs)


def _with_minted_receipt(prep, bundle):
    """A forged prepared input that a receipt has been MINTED OVER, so
    `consumer.verify_battery_receipt` genuinely accepts it.

    This deliberately reaches for `consumer._issue_battery_receipt`. It is
    the only way to ask the question N03 actually has to answer: if the
    factory boundary were satisfied — today by construction, tomorrow
    perhaps because the battery's own identity checks were changed — does
    the SUPPLEMENT path still refuse a broken day universe on its own?
    An authority that merely inherited the battery's verdict would not."""
    mcc._issue_battery_receipt(prep, mcc.CustodyAuthority.for_tests(bundle))
    assert mcc.verify_battery_receipt(prep) is not None, (
        "the forged object was supposed to PASS the factory boundary — "
        "otherwise the identity check below is never reached")
    return prep


def _forged_universe(prep, bundle, *, seqs, tps):
    return _with_minted_receipt(
        _hand_built(prep, day_sequences=seqs, traded_day_sets=tps), bundle)


def _genuine_universe(prep):
    return ({ch: tuple(prep.day_sequences[ch]) for ch in prep.day_sequences},
            {ch: frozenset(prep.traded_day_sets[ch])
             for ch in prep.traded_day_sets})


def _identity_code(prep):
    with pytest.raises(sa.MCInputError) as exc:
        sa.enforce_day_universe_identity(prep)
    return exc.value.code


def _derive_code(prep):
    with pytest.raises((sa.MCInputError, sa.SupplementError)) as exc:
        sa.derive_supplement_authority_for_tests(prep)
    return exc.value.code


# ===========================================================================
# A1 — constructible only from an approved custody source
# ===========================================================================

def test_a1_the_positive_chain_mints_and_verifies(test_prepared, authority):
    """The honest path first, so every refusal below is a refusal of
    something the module otherwise accepts."""
    assert isinstance(authority, sa.SupplementAuthority)
    assert authority.schema == sa.SUPPLEMENT_AUTHORITY_SCHEMA
    assert authority.supplement_id == sa.DEFAULT_SUPPLEMENT_ID
    assert sc.SUPPLEMENT_ID_PATTERN.match(authority.supplement_id)
    assert authority.trial_id == test_prepared.trial_id
    assert authority.authorized_commit == test_prepared.authorized_commit
    assert authority.day_universe == ALL_DAYS
    assert authority.theta_channels == tuple(sorted((PRIMARY, SECONDARY)))
    assert authority.n_days == len(ALL_DAYS)
    assert sa.verify_supplement_authority(
        authority, test_prepared) is authority


def test_a1_direct_construction_is_impossible(authority):
    """Hand the type every field a genuine authority carries: refused,
    because the construction capability is not one of them."""
    kwargs = {f.name: getattr(authority, f.name)
              for f in dataclasses.fields(authority) if f.init}
    assert kwargs.get("capability") is None, (
        "a genuine authority still holds the construction capability — it "
        "must be dropped so no instance can hand it out")
    with pytest.raises(sa.SupplementError) as exc:
        sa.SupplementAuthority(**kwargs)
    assert exc.value.code == "supplement_authority_capability_required"


def test_a1_dataclasses_replace_is_impossible(authority):
    """`replace` is a constructor call, so it dies at the same gate — a
    no-op replace included."""
    for kwargs in ({}, {"trial_id": "S0-T999"}, {"n_days": 1}):
        with pytest.raises(sa.SupplementError) as exc:
            dataclasses.replace(authority, **kwargs)
        assert exc.value.code == "supplement_authority_capability_required"


def test_a1_the_capability_token_is_not_reachable_from_an_instance(
        authority):
    """Nothing on a genuine instance is the token, so no instance can mint
    a second authority."""
    values = [getattr(authority, f.name)
              for f in dataclasses.fields(authority)]
    assert all(v is not sa._AUTHORITY_CAPABILITY for v in values)
    assert authority.capability is None


def test_a1_a_hand_built_prepared_input_has_no_authority(test_prepared):
    """Route 1 into the minter: the public `PreparedMCInput` constructor.
    The object is otherwise perfect — the identity digest is unchanged —
    and it is refused because the battery never ran."""
    forged = _hand_built(test_prepared)
    assert mcc.prepared_digest(forged) == mcc.prepared_digest(test_prepared)
    assert _derive_code(forged) == "seal_prepared_not_battery_validated"


def test_a1_a_replaced_prepared_input_has_no_authority(test_prepared):
    """Route 2: `dataclasses.replace` of the genuine battery product."""
    mutated = dataclasses.replace(test_prepared,
                                  method_digest="f" * 64)
    assert mutated.method_digest != test_prepared.method_digest
    assert _derive_code(mutated) == "seal_prepared_not_battery_validated"


def test_a1_a_stolen_receipt_does_not_buy_an_authority(test_prepared):
    """Route 2b: the receipt is unforgeable but movable, so it must also
    be BOUND. Grafting a genuine receipt onto a mutated object refuses
    under the MISMATCH code, not the absence code."""
    mutated = dataclasses.replace(test_prepared, k_per_seed=400)
    object.__setattr__(mutated, "battery_receipt",
                       test_prepared.battery_receipt)
    assert mutated.battery_receipt is test_prepared.battery_receipt
    assert _derive_code(mutated) == "seal_battery_receipt_mismatch"


def test_a1_a_non_prepared_object_is_refused_by_type(test_prepared):
    for entry in (sa.derive_supplement_authority,
                  sa.derive_supplement_authority_for_tests):
        with pytest.raises(sa.SupplementError) as exc:
            entry({"trial_id": TRIAL})
        assert exc.value.code == \
            "supplement_authority_prepared_input_required"


def test_a1_an_out_of_pattern_supplement_id_never_mints(test_prepared):
    with pytest.raises(sa.SupplementError) as exc:
        sa.derive_supplement_authority_for_tests(test_prepared,
                                                 supplement_id="MC-DS-1")
    assert exc.value.code == "supplement_authority_supplement_id_pattern"


# ===========================================================================
# A2 — the production entry refuses test-only authorities
# ===========================================================================

def test_a2_production_entry_refuses_a_test_only_prepared_input(
        test_prepared):
    """The honest TEST artifact — nothing wrong with it — has no business
    at the production derivation, however internally consistent it is."""
    assert test_prepared.test_only is True
    assert mcc.verify_battery_receipt(test_prepared) is not None
    with pytest.raises(sa.SupplementError) as exc:
        sa.derive_supplement_authority(test_prepared)
    assert exc.value.code == "supplement_authority_test_only_in_production"


def test_a2_test_entry_refuses_a_production_prepared_input(prod_like):
    """The mirror, so the two entries PARTITION the world rather than
    overlapping (`consumer.prepare_mc_input_for_tests` discipline)."""
    assert prod_like.test_only is False
    with pytest.raises(sa.SupplementError) as exc:
        sa.derive_supplement_authority_for_tests(prod_like)
    assert exc.value.code == \
        "supplement_authority_production_object_in_test_entry"


def test_a2_the_production_fixture_is_genuinely_production_shaped(
        prod_like):
    """Otherwise everything on the production path here is a weak test."""
    assert prod_like.test_only is False
    assert prod_like.source_artifact_id == mcc.ATTESTATION_PATH
    assert prod_like.source_artifact_sha256 == mcc.ATTESTATION_SHA256_PINNED
    assert len(dict(prod_like.file_sha256)) == len(mcc.BUNDLE_EXACT_SET) == 14
    assert mcc._assert_seal_provenance(prod_like).test_only is False


def test_a2_production_entry_mints_for_the_production_product(prod_like):
    auth = sa.derive_supplement_authority(prod_like)
    assert auth.test_only is False
    assert auth.source_artifact_id == mcc.ATTESTATION_PATH
    assert sa.verify_supplement_authority(auth, prod_like) is auth


def test_a2_production_entry_refuses_an_unapproved_custody_source(
        prod_like):
    """The string half of B-PROV, done without any repository read: the
    custody source id must be the approved attestation path."""
    forged = _hand_built(prod_like,
                         source_artifact_id="ops/NOT_THE_ATTESTATION.md")
    assert forged.source_artifact_sha256 == prod_like.source_artifact_sha256
    assert forged.test_only is False
    with pytest.raises(sa.SupplementError) as exc:
        sa.derive_supplement_authority(forged)
    assert exc.value.code == "supplement_authority_source_violation"


def test_a2_production_entry_refuses_unpinned_custody_source_bytes(
        prod_like):
    forged = _hand_built(prod_like, source_artifact_sha256="0" * 64)
    assert forged.source_artifact_id == mcc.ATTESTATION_PATH
    with pytest.raises(sa.SupplementError) as exc:
        sa.derive_supplement_authority(forged)
    assert exc.value.code == "supplement_authority_source_digest_violation"


# ===========================================================================
# A3 — every bound fact under its OWN refusal code
# ===========================================================================

MUTATIONS = {
    "schema": ("mc_supplement_authority.v2",
               "supplement_authority_schema"),
    "supplement_id": ("MC-DS-S002",
                      "supplement_authority_supplement_id_mismatch"),
    "trial_id": ("S0-T999", "supplement_authority_trial_mismatch"),
    "authorized_commit": ("1" * 40,
                          "supplement_authority_commit_mismatch"),
    "method_version": ("mc-freeze-v2",
                       "supplement_authority_method_version_mismatch"),
    "method_digest": ("f" * 64,
                      "supplement_authority_method_digest_mismatch"),
    "source_artifact_id": ("ops/NOT_THE_ATTESTATION.md",
                           "supplement_authority_source_artifact_id_mismatch"),
    "source_artifact_sha256":
        ("e" * 64, "supplement_authority_source_artifact_sha256_mismatch"),
    "test_only": (False, "supplement_authority_test_only_mismatch"),
    "bundle_table_digest": ("d" * 64,
                            "supplement_authority_bundle_table_mismatch"),
    "theta_channels": ((PRIMARY,),
                       "supplement_authority_theta_channels_mismatch"),
    "day_universe": (ALL_DAYS[:-1],
                     "supplement_authority_day_universe_mismatch"),
    "day_universe_digest":
        ("c" * 64, "supplement_authority_day_universe_digest_mismatch"),
    "n_days": (99, "supplement_authority_day_count_mismatch"),
    "source_input_sha256": ("b" * 64,
                            "supplement_authority_source_input_mismatch"),
    "authority_digest": ("a" * 64,
                         "supplement_authority_self_digest_mismatch"),
}


@pytest.mark.parametrize("field", sorted(MUTATIONS))
def test_a3_every_bound_field_refuses_under_its_own_code(
        authority, test_prepared, field):
    """One field at a time, mutated in place on a GENUINE authority (the
    only way past a factory-only constructor), then re-verified. A
    collapsed "authority mismatch" would tell an operator nothing about
    which binding moved, so each difference must keep its own name."""
    value, code = MUTATIONS[field]
    assert sa.verify_supplement_authority(authority, test_prepared) is \
        authority, "the near-miss must start from an authority that VERIFIES"
    object.__setattr__(authority, field, value)
    with pytest.raises(sa.SupplementError) as exc:
        sa.verify_supplement_authority(authority, test_prepared)
    assert exc.value.code == code


def test_a3_the_mutation_matrix_covers_every_declared_field(authority):
    """COMPLETE against the dataclass, not against a hand list: every
    field except the dropped capability is exercised above."""
    declared = {f.name for f in dataclasses.fields(authority)}
    assert declared - {"capability"} == set(MUTATIONS)
    assert set(sa.AUTHORITY_PAYLOAD_FIELDS) | {"authority_digest"} == \
        set(MUTATIONS)


def test_a3_the_self_digest_is_the_catch_all_underneath(authority,
                                                        test_prepared):
    """A mutated field ALSO breaks the self-digest — the specific code
    wins because it is checked first, which is the consumer's own
    ordering discipline at the seal boundary."""
    object.__setattr__(authority, "trial_id", "S0-T999")
    recomputed = sa._digest(sa.AUTHORITY_DIGEST_SCHEMA,
                            sa._authority_payload(authority))
    assert recomputed != authority.authority_digest
    with pytest.raises(sa.SupplementError) as exc:
        sa.verify_supplement_authority(authority, test_prepared)
    assert exc.value.code == "supplement_authority_trial_mismatch"


def test_a3_an_authority_from_another_prepared_input_is_refused(
        authority, test_prepared):
    """The binding is to ONE sealed input: an authority minted over a
    bundle with different bytes cannot certify this one. The day universe
    is IDENTICAL in both, so the refusal has to come from the custody
    binding, not from the dates."""
    other_prepared = _prepare_for_tests(_bundle(pnl=125.0))
    other = sa.derive_supplement_authority_for_tests(other_prepared)
    assert other.day_universe == authority.day_universe
    assert other.day_universe_digest == authority.day_universe_digest
    with pytest.raises(sa.SupplementError) as exc:
        sa.verify_supplement_authority(other, test_prepared)
    assert exc.value.code == "supplement_authority_bundle_table_mismatch"


def test_a3_verify_requires_a_battery_validated_prepared_input(
        authority, test_prepared):
    """Re-verification is not a softer boundary than derivation."""
    forged = _hand_built(test_prepared)
    with pytest.raises(sa.MCInputError) as exc:
        sa.verify_supplement_authority(authority, forged)
    assert exc.value.code == "seal_prepared_not_battery_validated"


def test_a3_verify_refuses_a_non_authority(test_prepared):
    with pytest.raises(sa.SupplementError) as exc:
        sa.verify_supplement_authority({"trial_id": TRIAL}, test_prepared)
    assert exc.value.code == "supplement_authority_required"


# ===========================================================================
# A4/A5/A6 — the §D.2.2 structural identity
# ===========================================================================

def test_a4_ref_dates_population_and_each_theta_union_are_one_set(
        test_prepared):
    """The identity, spelled out over the genuine object: the record key
    set of every engine x scenario file, each θ's declared population and
    each θ's TP∪FP all name the SAME set."""
    identity = sa.enforce_day_universe_identity(test_prepared)
    ref_dates = frozenset(test_prepared.records[("E1", "Base")])
    assert len(test_prepared.records) == 8
    for key, rows in test_prepared.records.items():
        assert frozenset(rows) == ref_dates, key
    assert frozenset(identity.day_universe) == ref_dates
    for ch in (PRIMARY, SECONDARY):
        population = frozenset(test_prepared.day_sequences[ch])
        tp = frozenset(test_prepared.traded_day_sets[ch])
        fp = population - tp
        assert tp | fp == ref_dates
        assert ref_dates == tp | fp                 # both directions
        assert tp == frozenset(TP_BY_CHANNEL[ch])
        assert fp == frozenset(FP_BY_CHANNEL[ch])


def test_a5_tp_and_fp_are_disjoint_and_no_overlap_reaches_a_prepared_input(
        _fixture_root, monkeypatch):
    """TP∩FP == EMPTY, tested where an overlap can actually be expressed:
    the sealed bundle. The oracle below is INTERNALLY CONSISTENT in every
    other respect — every day has a record, both channels agree about the
    population, the lists are ascending — and it still refuses, so no
    prepared input and therefore no authority exists for it."""
    oracle = _default_oracle()
    overlap_day = FP_BY_CHANNEL[PRIMARY][0]
    oracle[PRIMARY]["day_universe"]["tp_days"] = sorted(
        set(TP_BY_CHANNEL[PRIMARY]) | {overlap_day})
    bundle = _bundle(oracle=oracle)
    # near-miss: the overlapping day is a real, recorded day
    assert overlap_day in ALL_DAYS
    assert set(oracle[PRIMARY]["day_universe"]["tp_days"]) & \
        set(oracle[PRIMARY]["day_universe"]["fp_days"]) == {overlap_day}
    with pytest.raises(mcc.MCInputError) as exc:
        _prepare_production(bundle, _fixture_root, monkeypatch)
    assert exc.value.code == "tp_fp_overlap"


def test_a5_the_disjointness_check_is_retained_in_the_supplement_path():
    """In the prepared input's PROJECTION `fp` is a complement, so an
    overlap is unrepresentable and the check above cannot fire here. The
    check is kept anyway — this pins it, so a future derivation change
    that makes overlap representable does not find the requirement quietly
    gone."""
    body = inspect.getsource(sa.enforce_day_universe_identity)
    assert "fp = population - tp" in body
    assert "overlap = tp & fp" in body
    assert '"tp_fp_overlap"' in body


def test_a6_cross_theta_population_identity(test_prepared, test_bundle):
    """Two θ channels that split TP/FP differently must still name ONE
    population. The near-miss: each channel is internally FINE — every
    one of its days has a record — so only the cross-θ comparison can
    catch the drift, and it must do so under its own code rather than as
    one channel's unclassified records."""
    seqs, tps = _genuine_universe(test_prepared)
    dropped = ALL_DAYS[-1]
    seqs[SECONDARY] = tuple(d for d in seqs[SECONDARY] if d != dropped)
    tps[SECONDARY] = frozenset(d for d in tps[SECONDARY] if d != dropped)
    ref_dates = frozenset(test_prepared.records[("E1", "Base")])
    assert frozenset(seqs[SECONDARY]) < ref_dates
    assert tps[SECONDARY] <= frozenset(seqs[SECONDARY])
    forged = _forged_universe(test_prepared, test_bundle, seqs=seqs, tps=tps)
    assert _identity_code(forged) == "theta_population_drift"
    assert _derive_code(forged) == "theta_population_drift"


# ===========================================================================
# A7 — missing / duplicate / extra / SUBSTITUTED / drifted days
# ===========================================================================

def _both(seqs, tps, *, drop=(), add_fp=(), add_tp=()):
    for ch in list(seqs):
        seq = [d for d in seqs[ch] if d not in drop]
        seq += [d for d in add_fp if d not in seq]
        seq += [d for d in add_tp if d not in seq]
        seqs[ch] = tuple(sorted(seq))
        tp = {d for d in tps[ch] if d not in drop} | set(add_tp)
        tps[ch] = frozenset(tp)
    return seqs, tps


def test_a7_a_missing_day_refuses_as_an_unclassified_record(
        test_prepared, test_bundle):
    """A record day the day universe never accounts for."""
    seqs, tps = _both(*_genuine_universe(test_prepared), drop=(ALL_DAYS[-1],))
    forged = _forged_universe(test_prepared, test_bundle, seqs=seqs, tps=tps)
    assert len(seqs[PRIMARY]) == len(ALL_DAYS) - 1
    assert _identity_code(forged) == "record_without_oracle_class"


def test_a7_an_invented_fp_day_refuses(test_prepared, test_bundle):
    """A day universe day with no record: silently a no-trade day in every
    world that draws it."""
    seqs, tps = _both(*_genuine_universe(test_prepared),
                      add_fp=(UNRECORDED_DAY,))
    forged = _forged_universe(test_prepared, test_bundle, seqs=seqs, tps=tps)
    assert _identity_code(forged) == "fp_day_without_record"


def test_a7_an_invented_tp_day_refuses_under_the_tp_code(
        test_prepared, test_bundle):
    seqs, tps = _both(*_genuine_universe(test_prepared),
                      add_tp=(UNRECORDED_DAY,))
    forged = _forged_universe(test_prepared, test_bundle, seqs=seqs, tps=tps)
    assert _identity_code(forged) == "tp_day_without_record"


def test_a7_a_duplicate_day_refuses_under_the_duplicate_code(
        test_prepared, test_bundle):
    """In the merged projection a duplicate is necessarily ADJACENT, so an
    ascending-first check order would report it as `not_ascending` and
    leave `day_sequence_duplicates` unreachable. The order is deliberately
    swapped; this pins it."""
    seqs, tps = _genuine_universe(test_prepared)
    seqs[PRIMARY] = seqs[PRIMARY][:2] + (seqs[PRIMARY][1],) + seqs[PRIMARY][2:]
    assert len(seqs[PRIMARY]) == len(ALL_DAYS) + 1
    forged = _forged_universe(test_prepared, test_bundle, seqs=seqs, tps=tps)
    assert _identity_code(forged) == "day_sequence_duplicates"


def test_a7_a_non_ascending_day_sequence_refuses(test_prepared,
                                                 test_bundle):
    """Unique days, wrong order — a REFUSAL, never a repair: a repaired
    order would silently hide producer drift."""
    seqs, tps = _genuine_universe(test_prepared)
    seqs[PRIMARY] = tuple(reversed(seqs[PRIMARY]))
    assert len(set(seqs[PRIMARY])) == len(seqs[PRIMARY])
    forged = _forged_universe(test_prepared, test_bundle, seqs=seqs, tps=tps)
    assert _identity_code(forged) == "day_sequence_not_ascending"


def test_a7_a_substituted_day_at_the_SAME_COUNT_still_refuses(
        test_prepared, test_bundle):
    """THE count-only attack. One sealed day is swapped for an invented
    one, so |day universe| == |records| exactly and every count
    reconciliation still balances. Near-miss asserted first: the counts
    really are equal, and the population really is a same-size set."""
    seqs, tps = _both(*_genuine_universe(test_prepared),
                      drop=(ALL_DAYS[-1],), add_fp=(UNRECORDED_DAY,))
    ref_dates = frozenset(test_prepared.records[("E1", "Base")])
    assert len(seqs[PRIMARY]) == len(ref_dates)
    assert len(seqs[SECONDARY]) == len(ref_dates)
    assert frozenset(seqs[PRIMARY]) != ref_dates
    forged = _forged_universe(test_prepared, test_bundle, seqs=seqs, tps=tps)
    assert _identity_code(forged) == "fp_day_without_record"
    assert _derive_code(forged) == "fp_day_without_record"


def test_a7_a_traded_day_outside_the_day_universe_refuses(
        test_prepared, test_bundle):
    """The one code with no counterpart in the prepare battery: there the
    population IS `tp + fp`, so this is unrepresentable; here the two
    arrive as separate fields and a drifted object can claim a traded day
    the universe never lists."""
    seqs, tps = _genuine_universe(test_prepared)
    tps[PRIMARY] = tps[PRIMARY] | {UNRECORDED_DAY}
    assert UNRECORDED_DAY not in seqs[PRIMARY]
    forged = _forged_universe(test_prepared, test_bundle, seqs=seqs, tps=tps)
    assert _identity_code(forged) == "supplement_traded_day_outside_universe"


def test_a7_a_channel_present_in_only_one_projection_refuses(
        test_prepared, test_bundle):
    seqs, tps = _genuine_universe(test_prepared)
    tps.pop(SECONDARY)
    forged = _forged_universe(test_prepared, test_bundle, seqs=seqs, tps=tps)
    assert _identity_code(forged) == "day_universe_missing"


def test_a7_an_empty_day_universe_refuses(test_prepared, test_bundle):
    forged = _forged_universe(test_prepared, test_bundle, seqs={}, tps={})
    assert _identity_code(forged) == "day_universe_missing"


def test_a7_record_set_drift_across_files_refuses(test_prepared):
    """§D.2.2's `FOR_EACH_ENGINE_SCENARIO: ref_dates == traded_set` half.
    A scenario-selective omission silently becomes a no-trade day
    downstream, so it refuses here under the battery's own code — and the
    same mutation ALSO breaks the battery receipt, which is the layering
    this module is supposed to have."""
    recs = dict(test_prepared.records)
    key = ("E2", "Stress")
    recs[key] = MappingProxyType({d: r for d, r in recs[key].items()
                                  if d != ALL_DAYS[0]})
    object.__setattr__(test_prepared, "records", MappingProxyType(recs))
    with pytest.raises(sa.MCInputError) as exc:
        sa.enforce_day_universe_identity(test_prepared)
    assert exc.value.code == "record_set_drift_across_files"
    assert _derive_code(test_prepared) == "seal_battery_receipt_mismatch"


def test_a7_the_identity_codes_are_literally_the_prepare_batterys(
        test_prepared):
    """The reuse is MECHANICAL, not aspirational: every code this module
    raises for a §D.2.2 violation is a string that literally appears in
    `consumer._prepare_mc_input_impl`, and the one supplement-specific
    code genuinely does not."""
    body = inspect.getsource(mcc._prepare_mc_input_impl)
    for code in sa.IDENTITY_REFUSAL_CODES:
        assert f'"{code}"' in body, code
    assert f'"{sa.RECORD_SET_REFUSAL_CODE}"' in body
    for code in sa.SUPPLEMENT_SPECIFIC_IDENTITY_CODES:
        assert code not in body, code
    assert len(sa.IDENTITY_REFUSAL_CODES) == 8


def test_a7_no_refusal_code_is_invented_outside_the_declared_sets():
    """Every code raised anywhere in the module is either one of the eight
    reused ones, the record-set code, the one declared new identity code,
    or a `supplement_authority_*` lifecycle code. Nothing else."""
    src = inspect.getsource(sa)
    raised = set(re.findall(
        r"raise (?:SupplementError|MCInputError)\(\s*\n?\s*\"([a-z0-9_]+)\"",
        src))
    allowed = (set(sa.IDENTITY_REFUSAL_CODES)
               | set(sa.SUPPLEMENT_SPECIFIC_IDENTITY_CODES)
               | {sa.RECORD_SET_REFUSAL_CODE})
    unexpected = {c for c in raised - allowed
                  if not c.startswith("supplement_authority_")}
    assert unexpected == set(), unexpected
    # and the reuse is not decorative: all eight are actually raised
    assert set(sa.IDENTITY_REFUSAL_CODES) <= raised


# ===========================================================================
# A8 — the SYNCHRONIZED rewrite
# ===========================================================================

def test_a8_a_synchronized_bundle_rewrite_cannot_seat_a_broken_universe(
        _fixture_root, monkeypatch):
    """THE important one. Bundle, internal manifest and the external
    attestation are all regenerated TOGETHER over a day universe that
    claims a day no handoff file carries. Every custody layer is
    internally consistent — this is not a table-mismatch test.

    Near-miss, asserted before the refusal:
      * the attestation parses through the PRODUCTION constructor;
      * its 14-file table reproduces the bundle's actual bytes exactly;
      * the internal manifest covers every non-manifest file;
      * trial/commit agree everywhere.

    Only the §D.2.2 identity is broken, and that is enough: the prepare
    battery refuses, so no `PreparedMCInput` exists, so no
    `SupplementAuthority` can be minted and `build_day_strata_supplement`
    has no sanctioned source for its two arguments."""
    oracle = _default_oracle()
    for ch in oracle:
        oracle[ch]["day_universe"]["fp_days"] = sorted(
            set(FP_BY_CHANNEL[ch]) | {UNRECORDED_DAY})
    bundle = _bundle(oracle=oracle)
    att = _attestation_bytes(bundle)
    (_fixture_root / mcc.ATTESTATION_PATH).write_bytes(att)
    monkeypatch.setattr(mcc, "_REPO_ROOT", _fixture_root)
    monkeypatch.setattr(mcc, "ATTESTATION_SHA256_PINNED",
                        hashlib.sha256(att).hexdigest())
    monkeypatch.setattr(mcc, "build_template_calendar",
                        lambda *a, **k: _calendar())

    forged_authority = mcc.load_custody_authority_from_attestation()
    assert forged_authority.test_only is False
    assert forged_authority.source_artifact_id == mcc.ATTESTATION_PATH
    assert dict(forged_authority.file_sha256) == {
        n: hashlib.sha256(b).hexdigest() for n, b in bundle.items()}
    assert set(forged_authority.file_sha256) == mcc.BUNDLE_EXACT_SET
    declared = {json.loads(line)["relative_path"]: json.loads(line)[
        "file_sha256"] for line in
        bundle["manifest.jsonl"].decode("utf-8").splitlines() if line.strip()}
    for name in sorted(set(bundle) - {"manifest.jsonl"}):
        assert declared[name] == hashlib.sha256(bundle[name]).hexdigest()
    assert forged_authority.trial_id == TRIAL
    assert forged_authority.authorized_commit == COMMIT

    with pytest.raises(mcc.MCInputError) as exc:
        mcc.prepare_mc_input(
            bundle,
            authorization_snapshot={"trial_id": TRIAL,
                                    "authorized_commit": COMMIT},
            attestation_bytes=att)
    assert exc.value.code == "fp_day_without_record"


def test_a8_a_synchronized_object_rewrite_cannot_seat_a_broken_universe(
        test_prepared, test_bundle):
    """The same attack one layer up, where the synchronization is TOTAL:
    the forged object carries a battery receipt MINTED OVER ITSELF, so
    `consumer.verify_battery_receipt` accepts it and every component
    digest agrees. Nothing upstream objects.

    The supplement path must still refuse, because it re-derives §D.2.2
    itself rather than inheriting the battery's earlier verdict. If this
    test ever goes green by accident, N03 has become a comment."""
    seqs, tps = _both(*_genuine_universe(test_prepared),
                      add_fp=(UNRECORDED_DAY,))
    forged = _forged_universe(test_prepared, test_bundle, seqs=seqs, tps=tps)
    # near-miss: the factory boundary is GENUINELY satisfied
    receipt = mcc.verify_battery_receipt(forged)
    assert receipt is forged.battery_receipt
    assert receipt.prepared_digest == mcc.prepared_digest(forged)
    assert _derive_code(forged) == "fp_day_without_record"


def test_a8_the_broken_object_cannot_reach_the_builder_arguments(
        test_prepared, test_bundle, authority):
    """And the consequence that actually matters: `supplement_build_inputs`
    — the only sanctioned source of `expected_day_set` and `binding` —
    refuses the same way, so a broken universe never reaches
    `build_day_strata_supplement`."""
    seqs, tps = _both(*_genuine_universe(test_prepared),
                      add_fp=(UNRECORDED_DAY,))
    forged = _forged_universe(test_prepared, test_bundle, seqs=seqs, tps=tps)
    with pytest.raises(sa.MCInputError) as exc:
        sa.supplement_build_inputs(authority, forged)
    assert exc.value.code == "fp_day_without_record"


# ===========================================================================
# A9 — no outcome value is read or emitted
# ===========================================================================

OUTCOME_TOKENS = ("pnl", "return", "profit", "oracle", "report", "verdict",
                  "payout", "equity", "drawdown", "ev_", "tp_", "fp_")
#: the three STRUCTURAL keys of a TradePathRecord; every other field is an
#: outcome or an execution detail this module must never touch
STRUCTURAL_RECORD_FIELDS = frozenset({"trade_date", "engine",
                                      "cost_scenario"})


def test_a9_no_public_field_is_named_after_an_outcome(authority):
    names = [f.name for f in dataclasses.fields(authority)]
    names += [n for n in dir(authority) if not n.startswith("_")]
    for name in names:
        for token in OUTCOME_TOKENS:
            assert token not in name.lower(), (name, token)


def test_a9_every_exposed_value_is_structural(authority):
    """Dates, digests, identifiers, counts and flags — and never a float,
    which is what every P&L value in this system is."""
    def check(value, where):
        assert not isinstance(value, float), where
        if isinstance(value, bool):
            return
        if isinstance(value, (int, str)):
            return
        if isinstance(value, (tuple, frozenset, list, set)):
            for i, item in enumerate(value):
                check(item, f"{where}[{i}]")
            return
        if isinstance(value, dict):
            for k, v in value.items():
                check(k, f"{where}.{k}")
                check(v, f"{where}.{k}")
            return
        assert value is None, (where, type(value).__name__)

    for f in dataclasses.fields(authority):
        check(getattr(authority, f.name), f.name)
    check(authority.expected_day_set, "expected_day_set")
    check(authority.supplement_binding(), "supplement_binding")
    for day in authority.day_universe:
        assert re.match(r"^\d{4}-\d{2}-\d{2}$", day)


def test_a9_the_module_never_reads_an_outcome_record_field():
    """Mechanically derived from `TradePathRecord`, not hand-listed: there
    is no attribute access, no string key and no subscript anywhere in the
    module that could reach an outcome field. (Bare-substring matching is
    deliberately NOT used — `direction` is also an English word, and a
    test that fails on prose teaches a reader to weaken it.)"""
    src = inspect.getsource(sa)
    outcome_fields = (set(TradePathRecord.__dataclass_fields__)
                      - STRUCTURAL_RECORD_FIELDS)
    assert len(outcome_fields) == 16
    for field in sorted(outcome_fields):
        for access in (f".{field}", f'"{field}"', f"'{field}'",
                       f"[{field}]", f"({field})", f"{field}="):
            assert access not in src, (field, access)


def test_a9_outcome_values_do_not_change_the_day_universe(test_prepared):
    """BEHAVIOURAL blindness. Two bundles whose ONLY difference is the
    P&L carried by every record: the custody binding must move (different
    bytes) while the day universe and its digest must not (same days)."""
    other = _prepare_for_tests(_bundle(pnl=999.5))
    a = sa.derive_supplement_authority_for_tests(test_prepared)
    b = sa.derive_supplement_authority_for_tests(other)
    assert a.day_universe == b.day_universe
    assert a.day_universe_digest == b.day_universe_digest
    assert a.expected_day_set == b.expected_day_set
    assert a.source_input_sha256 != b.source_input_sha256
    assert a.bundle_table_digest != b.bundle_table_digest
    assert a.authority_digest != b.authority_digest


def test_a9_the_day_universe_digest_is_order_independent_but_deterministic():
    assert sa.day_universe_digest(ALL_DAYS) == \
        sa.day_universe_digest(tuple(reversed(ALL_DAYS)))
    assert sa.day_universe_digest(ALL_DAYS) != \
        sa.day_universe_digest(ALL_DAYS[:-1])


# ===========================================================================
# A10 — completing N03 is not supplement authorization
# ===========================================================================

def test_a10_the_module_states_that_it_authorizes_nothing():
    text = sa.SUPPLEMENT_AUTHORITY_IS_NOT_AUTHORIZATION
    assert "NOT supplement authorization" in text
    assert "grants nothing" in text
    assert "NOTHING HERE AUTHORIZES ANYTHING" in sa.__doc__


def test_a10_holding_an_authority_does_not_authorize_a_supplement(
        authority, test_prepared):
    """An authority in hand, fully verified — and the supplement
    authorization gate is exactly as closed as it was before."""
    assert sa.verify_supplement_authority(
        authority, test_prepared) is authority
    with pytest.raises(dss.SupplementNotAuthorized):
        dss.authorize_supplement("")
    with pytest.raises(dss.SupplementNotAuthorized):
        dss.authorize_supplement(
            "| 14 | x | SUPPLEMENT_EXECUTION_AUTHORIZED | " + COMMIT +
            " | Aaron | planted lookalike |")
    with pytest.raises(dss.SupplementNotAuthorized):
        dss.run_supplement_production()


def test_a10_nothing_public_reads_as_permission():
    """No exported name is permission-shaped, and the authority carries no
    boolean anyone could mistake for a grant — `test_only` is the only
    bool, and it is a restriction."""
    permission = re.compile(r"authoriz|approv|permit|grant|allow|enable",
                            re.IGNORECASE)
    for name in dir(sa):
        if name.startswith("_"):
            continue
        if name == "SUPPLEMENT_AUTHORITY_IS_NOT_AUTHORIZATION":
            continue
        assert not permission.search(name), name
    bools = [f.name for f in dataclasses.fields(sa.SupplementAuthority)
             if f.type in ("bool", bool)]
    assert bools == ["test_only"]


def test_a10_the_module_emits_no_registry_vocabulary():
    """N03 is engineering with no data face: it appends no registry row,
    so it does not even NAME a ratified supplement event token."""
    src = inspect.getsource(sa)
    for token in sc.EVENT_TOKENS + sc.ND3_DEFERRED_TOKENS:
        assert token not in src, token


def test_a10_the_module_touches_no_filesystem_and_no_registry():
    """Structurally, not by promise: the module imports no path/IO helper
    and never opens anything."""
    src = inspect.getsource(sa)
    for forbidden in ("open(", "Path(", "read_bytes", "read_text",
                      "write_bytes", "write_text", "mkdir", "os.",
                      "TRIAL_REGISTRY", "EXPOSURE_LEDGER", "quant-data"):
        assert forbidden not in src, forbidden


# ===========================================================================
# the interface actually fits the builder it exists to feed
# ===========================================================================

def test_the_authority_feeds_build_day_strata_supplement(authority,
                                                         test_prepared):
    """The point of the whole module: `expected_day_set` and `binding`
    come from ONE place, and the builder accepts them unchanged. Rows are
    invented structural rows — no sealed content is read to make them."""
    expected, binding = sa.supplement_build_inputs(authority, test_prepared)
    assert expected == frozenset(ALL_DAYS)
    assert set(binding) == set(dss.BINDING_FIELDS)
    rows = [{"trade_date": d, "year": int(d[:4]),
             "vol_stratum": dss.VOL_STRATA[i % len(dss.VOL_STRATA)],
             "event_stratum": dss.EVENT_STRATA[i % len(dss.EVENT_STRATA)]}
            for i, d in enumerate(sorted(expected))]
    supplement = dss.build_day_strata_supplement(
        rows, expected_day_set=expected, binding=binding)
    assert supplement["n_rows"] == len(ALL_DAYS)
    assert supplement["binding"] == binding
    assert supplement["binding"]["day_universe_digest"] == \
        authority.day_universe_digest
    assert supplement["binding"]["source_input_sha256"] == \
        authority.source_input_sha256
    assert supplement["supplement_id"] == authority.supplement_id


def test_the_binding_field_set_is_read_from_the_builder(authority):
    """Not re-spelled here: if `day_strata_supplement.BINDING_FIELDS`
    changes, this refuses instead of quietly producing a binding the
    builder will reject."""
    assert set(authority.supplement_binding()) == set(dss.BINDING_FIELDS)
    assert len(dss.BINDING_FIELDS) == 5


def test_build_inputs_requires_the_matching_prepared_input(authority):
    """The two arguments are re-derived at USE time, not trusted from mint
    time — the object can cross a process boundary in between."""
    other = _prepare_for_tests(_bundle(pnl=42.0))
    with pytest.raises(sa.SupplementError) as exc:
        sa.supplement_build_inputs(authority, other)
    assert exc.value.code == "supplement_authority_bundle_table_mismatch"
