"""S1 - INDEPENDENT ADVERSARIAL NEGATIVE BATTERY against the N06
supplement provenance boundary.

WRITTEN BY A LANE THAT DID NOT WRITE THE CODE. Everything here is an
attack. The three defects measured at `617f7c3` on the public boundary
were:

  * a hand-made six-field `FakeAuthority` passed ALL of `B_DERIVE`;
  * a genuine-shaped authority was REFUSED, because the gate read
    `file_sha256_digest` while a real `SupplementAuthority` exposes
    `bundle_table_digest` - forgeries in, real objects out;
  * a hand-assembled `(expected_day_set, binding)` pair BUILT AND
    SEALED a supplement.

Discipline, mirrored from `tests/test_mc_supplement_authority.py`: a
negative is only worth something if the near-miss is genuinely NEAR.
Wherever it is possible, the forgery is first asserted to PASS the
checks it is supposed to pass, so the refusal is attributable to the one
thing that was changed. Every refusal asserts an exact `.code`; there is
no bare `pytest.raises(Exception)` here, and no muted test of any kind -
`test_mc_supplement_integration.test_no_supplement_test_is_muted` scans
this file and would fail on one.

FIXTURES ARE SYNTHETIC, EXCLUSIVELY. No Development data is read; the
only real bytes are the two FROZEN METHOD files copied into a tmp root
(the technique `tests/test_mc_battery_boundary.py` and
`tests/test_mc_supplement_authority.py` already use), which carry no
research values. Nothing is created under the ruled output roots, no
`supplements` subtree is created anywhere, and nothing is appended to
`ops/TRIAL_REGISTRY.md` or `EXPOSURE_LEDGER.md`.

DISCLOSED FORGERY ROUTES.

  `consumer._issue_battery_receipt` (module-private, deliberately reached
      for) - lets a hand-built prepared input genuinely PASS the factory
      boundary, so the supplement layer's own re-derivation is what is
      under test rather than the battery's earlier verdict. The same
      reach `tests/test_mc_supplement_authority.py` documents.
  `__new__` + `object.__setattr__` (NOTHING private) - walks around
      `__post_init__` on every frozen slots dataclass in the chain:
      `SupplementAuthority` (section Y) and `ProductionReceipt`
      (section X). This is how the seal's second line of defence gets
      exercised at all, and it is the headline finding of this battery.
  `supplement_production._CAPABILITY` (module-private) - the lesser hole,
      recorded for completeness; it is the only route to
      `production_receipt_incomplete`.

REPAIR STATUS. Four findings from the first pass of this battery were
repaired in production code; those tests have been FLIPPED from
"records the defect" to "proves the refusal", and each keeps its
near-miss so the refusal stays attributable:

  F3 the production seal did not re-validate the supplement object, so a
     payload whose rows carried `"pnl"` was refused by the test-only
     seal and SEALED by the production one -> now
     `production_supplement_object_invalid`.
  F4 the runner gates used `isinstance` while verification used
     `type(...) is`, so a `__new__` SUBCLASS cleared the typed gate ->
     now refused by `_require_real_authority`.
  F5 three B_DERIVE gates were type-blind, so a field-for-field mirror
     was accepted by each individually -> now all five gates refuse it.
  F6 an authority for `MC-DS-S002` built a payload stamped `MC-DS-S001`,
     and it VERIFIED -> now `production_supplement_id_divergence`.

DISCLOSED RESIDUALS, pinned exactly as measured and NOT repaired:

  F1/F2 `__new__` + `object.__setattr__` walks around both capability
     checks and the receipt components are public arithmetic.
     RETRACTED AT ROUND 3: this entry used to argue that the boundary
     which actually holds is RE-DERIVATION rather than the capability,
     so a forged authority could only restate the truth. That is false.
     Round 2 showed re-derivation holds only when the derived-from and
     the used bytes are ONE snapshot; round 3 showed that even one
     snapshot is not enough while the snapshot can carry a hostile
     scalar subclass -- a `str` whose `__eq__` returns True passes the
     re-derived digest comparison and JSON then writes its real value.
     F1/F2 is therefore NOT benign: composed with the scalar-freeze
     defect it yields sealed bytes whose declared digest does not
     describe their rows. The attack needs only PUBLIC `__new__` and
     `object.__setattr__`; module privacy was never the question.
  F7 `production_day_universe_drift` is shadowed by
     `production_binding_drift`.
  (F7b and F4b below were REPAIRED in the same round that found them;
  they are kept here as history, and the tests that pin them now
  assert the repaired behaviour. They are NOT open residuals.)

  F7b `production_forbidden_row_field`, added by the F3 repair, was
     shadowed by `production_supplement_object_invalid` - same class,
     found in the repair itself.
  F8 `resolve_partial` is public and writes the sealed artifact name.
  F9 `SupplementProduct` wraps a SHALLOW copy, so rows and binding stay
     mutable inside the "immutable" proxy.
  F10 there is no named `production_prepared_test_only`; a test_only
     prepared input is blocked as a consequence of the provenance
     comparison, not by its own check.
  F4b `build_supplement_from_authority` still uses `isinstance`, so a
     subclass clears the BUILDER's type check and is stopped one layer
     down under an authority-layer code.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import shutil
from pathlib import Path

import pytest

from conftest import make_trade_path
from itsf.contracts import RESEARCH_BOOTSTRAP_SEEDS
from itsf.mc import consumer as mcc
from itsf.mc import day_strata_supplement as dss
from itsf.mc import supplement_authority as sa
from itsf.mc import supplement_contract as sc
from itsf.mc import supplement_production as sp
from itsf.mc import supplement_runner as run
from itsf.mc.orchestrator import TemplateDay
from itsf.s0.report import record_to_formal_dict

#: The governed subtrees AS THEY ARE when this file is imported. Every
#: assertion about them below is a comparison against this, never
#: against a fixed expected value: an authorized run legitimately puts
#: artifacts there, and a battery still may not touch them.
import _governed_subtrees as _gs                      # noqa: E402
_SUBTREES_AT_IMPORT = _gs.snapshot()

TRIAL = "S0-T001"
COMMIT = "876c1b74131b4ab1a89dce433ecce646ba481f8c"
OTHER_COMMIT = "b" * 40
SID = dss.SUPPLEMENT_ID                      # 'MC-DS-S001'
OTHER_SID = "MC-DS-S002"
INC = "INC-0123456789ab"
PRIMARY = mcc.PRIMARY_THETA_CHANNEL
SECONDARY = mcc.SECONDARY_THETA_CHANNEL

ALL_DAYS = ("2026-08-03", "2026-08-04", "2026-08-05", "2026-08-06",
            "2026-08-07")
#: same COUNT, one day substituted - the day-universe digest moves while
#: `n_days` does not, so the two branches of `day_universe_identity` stay
#: separately attributable
SUBSTITUTED_DAYS = ("2026-08-03", "2026-08-04", "2026-08-05", "2026-08-06",
                    "2026-08-11")
#: one day MORE - the count branch
SIX_DAYS = ALL_DAYS + ("2026-08-10",)

REAL_REPO_ROOT = mcc._REPO_ROOT
FROZEN_METHOD_FILES = ("MC_METHOD_SPEC.md", "gate1/platform_params.yaml")


# ===========================================================================
# synthetic bundle / attestation / prepared inputs
# (technique reused from tests/test_mc_supplement_authority.py)
# ===========================================================================

def _tp_fp(days):
    """A legal §D.2.2 split: both channels span the SAME population."""
    days = tuple(days)
    return ({PRIMARY: days[0::2], SECONDARY: days[:-1]},
            {PRIMARY: days[1::2], SECONDARY: days[-1:]})


def _record_row(date, engine, scn, pnl):
    rec = make_trade_path([pnl / 2, pnl], date=date, engine=engine,
                          final=pnl)
    # S0's OWN publisher, not `asdict`: a sealed line carries the
    # PUBLISHED §10.1 names (entry_timestamp/exit_timestamp), and a
    # fixture that emits the internal ones is producing something S0
    # would never seal. Measured 2026-09-05 -- that gap is exactly
    # what let `record_schema_violation` reach the first real run.
    row = record_to_formal_dict(rec)
    row["cost_scenario"] = scn
    return row


def _calendar(n_days=8, n_offsets=2):
    return mcc.TemplateCalendar(
        days=tuple(TemplateDay(day_id=f"T{i:03d}", cal_offset=i)
                   for i in range(n_days)),
        first_month_offsets=tuple(range(n_offsets)))


def _oracle(days):
    tp, fp = _tp_fp(days)
    return {ch: {"day_universe": {"tp_days": list(tp[ch]),
                                  "fp_days": list(fp[ch])}}
            for ch in (PRIMARY, SECONDARY)}


def _bundle(pnl=80.0, *, days=ALL_DAYS, trial=TRIAL, commit=COMMIT):
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
        "oracle_daily": _oracle(days),
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
    lines = ["# SYNTHETIC POST-RUN ATTESTATION (test fixture)", "",
             f"TRIAL_ID={trial}", f"AUTHORIZED_COMMIT={commit}", "",
             "| file | bytes | sha256 |", "| --- | --- | --- |"]
    for name in sorted(bundle):
        lines.append(f"| {name} | {len(bundle[name])} | "
                     f"{hashlib.sha256(bundle[name]).hexdigest()} |")
    return ("\n".join(lines) + "\n").encode("utf-8")


@pytest.fixture(scope="session")
def _fixture_root(tmp_path_factory):
    root = tmp_path_factory.mktemp("supplement_provenance_battery_root")
    (root / "ops").mkdir()
    (root / "gate1").mkdir()
    for rel in FROZEN_METHOD_FILES:
        shutil.copy2(REAL_REPO_ROOT / rel, root / rel)
    return root


@pytest.fixture()
def make_prod(_fixture_root, monkeypatch):
    """Factory for PRODUCTION-shaped battery products (test_only=False,
    the approved custody source id, and a code pin REPOINTED at the
    synthetic attestation - repointed, never bypassed)."""
    def _make(bundle):
        att = _attestation_bytes(bundle)
        (_fixture_root / mcc.ATTESTATION_PATH).write_bytes(att)
        monkeypatch.setattr(mcc, "_REPO_ROOT", _fixture_root)
        monkeypatch.setattr(mcc, "ATTESTATION_SHA256_PINNED",
                            hashlib.sha256(att).hexdigest())
        monkeypatch.setattr(mcc, "build_template_calendar",
                            lambda *a, **k: _calendar())
        return mcc.prepare_mc_input(
            bundle,
            authorization_snapshot={"trial_id": TRIAL,
                                    "authorized_commit": COMMIT},
            attestation_bytes=att)
    return _make


@pytest.fixture()
def prod(make_prod):
    return make_prod(_bundle())


@pytest.fixture()
def authority(prod):
    return sa.derive_supplement_authority(prod)


def _prepare_for_tests(bundle, *, custody=None):
    return mcc.prepare_mc_input_for_tests(
        bundle,
        authorization_snapshot={"trial_id": TRIAL,
                                "authorized_commit": COMMIT},
        custody_authority=custody or mcc.CustodyAuthority.for_tests(bundle),
        test_only_calendar=_calendar())


@pytest.fixture()
def test_prepared():
    return _prepare_for_tests(_bundle())


@pytest.fixture()
def test_authority(test_prepared):
    return sa.derive_supplement_authority_for_tests(test_prepared)


# ===========================================================================
# forgery routes
# ===========================================================================

def _hand_built(prep, **claim):
    """The PUBLIC `PreparedMCInput` constructor, every declared init
    field copied off a genuine object, `claim` overriding."""
    names = {f.name for f in dataclasses.fields(prep) if f.init}
    kwargs = {n: getattr(prep, n) for n in names
              if n not in ("records", "records_digest")}
    kwargs.update({k: v for k, v in claim.items() if k in names})
    return mcc.PreparedMCInput(records=None, records_digest=None, **kwargs)


def _mint_battery_receipt_over(prep):
    """Mint a GENUINE battery receipt over a forged prepared input, using
    a custody authority that mirrors the object's own provenance claim,
    so `verify_battery_receipt` really accepts it.

    This is the only way to ask the question the supplement layer has to
    answer on its own: if the factory boundary WERE satisfied, does the
    supplement path still refuse drift it has never re-derived?"""
    authority = mcc.CustodyAuthority(
        trial_id=prep.trial_id, authorized_commit=prep.authorized_commit,
        source_artifact_id=prep.source_artifact_id,
        source_artifact_sha256=prep.source_artifact_sha256,
        file_sha256=prep.file_sha256, test_only=prep.test_only)
    mcc._issue_battery_receipt(prep, authority)
    assert mcc.verify_battery_receipt(prep) is not None, (
        "the forged prepared input was supposed to PASS the factory "
        "boundary - otherwise the supplement-layer check below is never "
        "reached and the negative proves nothing")
    return prep


def _forged_prepared(prep, **claim):
    return _mint_battery_receipt_over(_hand_built(prep, **claim))


@dataclasses.dataclass(frozen=True)
class SixFieldAuthority:
    """The EXACT object that passed all of B_DERIVE at 617f7c3."""
    test_only: bool = False
    authorized_commit: str = COMMIT
    supplement_id: str = SID
    file_sha256_digest: str = "b" * 64
    day_universe_digest: str = "c" * 64
    method_version: str = "mc_day_strata_supplement.v1"


def _mirror_authority(auth):
    """A stand-in shaped EXACTLY like the real authority: every field
    name, every field VALUE, including the self-digest."""
    fields = tuple(f.name for f in dataclasses.fields(auth))
    mirror_cls = dataclasses.make_dataclass(
        "MirrorAuthority", [(n, object) for n in fields], frozen=True)
    mirror = mirror_cls(**{n: getattr(auth, n) for n in fields})
    for name in fields:
        assert getattr(mirror, name) == getattr(auth, name), name
    assert not isinstance(mirror, sa.SupplementAuthority)
    return mirror


# ===========================================================================
# runner gate plumbing
# ===========================================================================

@dataclasses.dataclass
class FakeP2:
    actor: str = "Aaron"
    authorized_commit: str = COMMIT
    output_root: str = r"C:\Users\Aaron\quant-data\itsf-runs"


@dataclasses.dataclass
class FakeChain:
    live_authorizations: tuple = ()
    problem: str = ""
    retired: bool = False


def _ctx(**over) -> run.GateContext:
    base = dict(supplement_id=SID, head_commit=COMMIT, registry_text="",
                runs_root=None, archive_root=None, repo_dirty_paths=(),
                g9_flag=None, second_copy_flag=None, frozen_hashes_ok=True,
                chain=FakeChain(live_authorizations=(FakeP2(),)),
                authority=None, prepared=None, utc_stamp="")
    base.update(over)
    return run.GateContext(**base)


def _gate_refusal(name, ctx):
    """Return `(code, message)` for a gate that MUST refuse."""
    with pytest.raises(run.SupplementRunnerError) as ei:
        run.GATES[name](ctx)
    assert ei.value.code == f"gate_refused:{name}"
    return ei.value.code, str(ei.value)


def _stage_refusal(stage, ctx):
    with pytest.raises(run.SupplementRunnerError) as ei:
        run.run_stage_gates(stage, ctx)
    return ei.value.code, str(ei.value)


def _rows(days):
    return [{"trade_date": d, "year": int(d[:4]),
             "vol_stratum": "T1", "event_stratum": "none"}
            for d in sorted(days)]


def _listing(path):
    return sorted(str(p.relative_to(path)) for p in Path(path).rglob("*"))


def _seal_refusal(product, out, *, authority, prepared, incident=INC):
    """Seal MUST refuse AND MUST write nothing. Returns the code."""
    before = _listing(out)
    with pytest.raises(sp.SupplementProductionError) as ei:
        sp.seal_supplement_production(product, out, authority=authority,
                                      prepared=prepared,
                                      incident_id=incident)
    assert _listing(out) == before, (
        f"a refused seal ({ei.value.code}) left bytes behind: "
        f"{sorted(set(_listing(out)) - set(before))}")
    return ei.value.code


# ===========================================================================
# 0. the fixture itself is genuinely production-shaped
# ===========================================================================

def test_p0_the_fixture_is_a_real_battery_product_not_a_stand_in(prod):
    assert isinstance(prod, mcc.PreparedMCInput)
    assert prod.test_only is False
    assert prod.source_artifact_id == mcc.ATTESTATION_PATH
    assert prod.source_artifact_sha256 == mcc.ATTESTATION_SHA256_PINNED
    assert len(dict(prod.file_sha256)) == len(mcc.BUNDLE_EXACT_SET) == 14
    assert mcc.verify_battery_receipt(prod) is not None
    assert mcc._assert_seal_provenance(prod).test_only is False


# ===========================================================================
# 1. POSITIVE - a real authority + its OWN prepared input passes B_DERIVE
# ===========================================================================

def test_p1_real_authority_and_its_own_prepared_input_pass_all_of_b_derive(
        prod, authority):
    """The exact pairing that was REFUSED at 617f7c3 (the gate read
    `file_sha256_digest`, which no real authority has). It must now pass
    the complete stage, or every negative below is vacuous."""
    assert type(authority) is sa.SupplementAuthority
    assert authority.test_only is False
    assert authority.supplement_id == SID
    assert authority.authorized_commit == COMMIT
    assert authority.day_universe == ALL_DAYS
    assert authority.method_version == sa.SUPPLEMENT_METHOD_VERSION
    assert sa.verify_supplement_authority(authority, prod) is authority

    ctx = _ctx(authority=authority, prepared=prod)
    assert run.run_stage_gates("B_DERIVE", ctx) is None
    for gate in sc.GATE_TABLE["B_DERIVE"]:
        assert run.GATES[gate](ctx) is None, gate


# ===========================================================================
# 2. POSITIVE - the factory builds a verifying product, and it seals
# ===========================================================================

def test_p2_the_factory_builds_a_verifying_product_and_seals_it(
        prod, authority, tmp_path):
    rows = _rows(authority.expected_day_set)
    product = sp.build_supplement_from_authority(authority, prod, rows)

    assert type(product) is sp.SupplementProduct
    assert product.supplement_id == SID
    assert product.payload["binding"] == authority.supplement_binding()
    assert frozenset(r["trade_date"] for r in product.payload["rows"]) == \
        authority.expected_day_set
    receipt = product.receipt
    assert type(receipt) is sp.ProductionReceipt
    assert receipt.schema == sp.PRODUCTION_RECEIPT_SCHEMA
    assert receipt.capability is None, (
        "a minted receipt must not retain the capability token, or "
        "holding one would let a caller mint a second")
    assert set(receipt.components) == set(sp.RECEIPT_COMPONENTS)
    assert sp.verify_production_receipt(product, authority, prod) is receipt

    out = tmp_path / "seal"
    out.mkdir()
    action, sha = sp.seal_supplement_production(
        product, out, authority=authority, prepared=prod, incident_id=INC)
    assert action.action == "promote"
    sealed = out / dss.SUPPLEMENT_FILENAME
    assert sealed.exists()
    assert hashlib.sha256(sealed.read_bytes()).hexdigest() == sha
    assert sealed.read_bytes() == dss.canonical_supplement_bytes(
        product.payload)
    assert _listing(out) == [dss.SUPPLEMENT_FILENAME]


# ===========================================================================
# 3. duck-typed / field-compatible stand-ins at B_DERIVE
# ===========================================================================

def test_n3_the_617f7c3_six_field_forgery_is_refused_by_every_b_derive_gate(
        prod):
    """The measured 617f7c3 defect, inverted. This object passed ALL five
    gates then; now not one of them may accept it."""
    ctx = _ctx(authority=SixFieldAuthority(), prepared=prod)
    for gate in sc.GATE_TABLE["B_DERIVE"]:
        outcome = None
        try:
            run.GATES[gate](ctx)
        except run.SupplementRunnerError as exc:
            outcome = exc.code
        except AttributeError as exc:                        # noqa: BLE001
            outcome = f"AttributeError:{exc}"
        assert outcome is not None, (
            f"B_DERIVE gate {gate!r} ACCEPTED the six-field stand-in - "
            "this is the 617f7c3 defect, unrepaired")
    code, _ = _gate_refusal("custody_authority_production", ctx)
    assert code == "gate_refused:custody_authority_production"
    assert _stage_refusal("B_DERIVE", ctx)[0] == \
        "gate_refused:custody_authority_production"


def test_n3_a_perfect_mirror_of_the_real_authority_is_still_refused(
        prod, authority):
    """A stand-in with EVERY field name and EVERY field value of the
    genuine authority, self-digest included. It is refused on TYPE.

    F5, REPAIRED AND NOW PINNED. This test previously recorded a measured
    defect: only the first two B_DERIVE gates were typed, so
    `source_bundle_digest`, `day_universe_identity` and
    `method_version_pinned` each ACCEPTED the mirror when called in
    isolation - a mirror carries the right values, and those three gates
    compared values only. Stage order hid it. `_require_real_authority`
    is now called by ALL FIVE gates, so each refuses INDIVIDUALLY and the
    property is the strong one: no B_DERIVE gate can be satisfied by a
    stand-in, whatever order it is reached in."""
    mirror = _mirror_authority(authority)
    ctx = _ctx(authority=mirror, prepared=prod)

    # the near-miss: the genuine authority passes every one of them
    genuine_ctx = _ctx(authority=authority, prepared=prod)
    for gate in sc.GATE_TABLE["B_DERIVE"]:
        assert run.GATES[gate](genuine_ctx) is None, gate

    for gate in sc.GATE_TABLE["B_DERIVE"]:
        _, msg = _gate_refusal(gate, ctx)
        assert "not exactly SupplementAuthority" in msg, (
            f"{gate} refused the mirror, but not on TYPE - re-read it")
    assert _stage_refusal("B_DERIVE", ctx)[0] == \
        "gate_refused:custody_authority_production"

    # the same holds for the six-field forgery at every gate
    six_ctx = _ctx(authority=SixFieldAuthority(), prepared=prod)
    for gate in sc.GATE_TABLE["B_DERIVE"]:
        _gate_refusal(gate, six_ctx)


def test_n3_a_stand_in_cannot_reach_the_production_builder_either(
        prod, authority):
    """The runner is not the only door. `build_supplement_from_authority`
    must refuse the same two stand-ins on TYPE."""
    rows = _rows(authority.expected_day_set)
    for stand_in in (SixFieldAuthority(), _mirror_authority(authority),
                     dict(supplement_id=SID), None):
        with pytest.raises(sp.SupplementProductionError) as ei:
            sp.build_supplement_from_authority(stand_in, prod, rows)
        assert ei.value.code == "production_authority_type"


def test_n3_verify_production_receipt_refuses_a_stand_in_authority(
        prod, authority):
    """A GENUINE product re-verified against a stand-in authority: the
    product is real, so the refusal is attributable to the authority."""
    product = sp.build_supplement_from_authority(
        authority, prod, _rows(authority.expected_day_set))
    assert sp.verify_production_receipt(product, authority, prod) is \
        product.receipt                                    # the near-miss
    with pytest.raises(sp.SupplementProductionError) as ei:
        sp.verify_production_receipt(product, _mirror_authority(authority),
                                     prod)
    assert ei.value.code == "production_authority_type"


# ===========================================================================
# 4. an authority paired with a DIFFERENT prepared input
# ===========================================================================

def test_n4_a_different_prepared_input_is_refused_though_every_printed_fact_agrees(
        prod, authority, make_prod):
    """Bundle B differs from bundle A ONLY in the record VALUES. The two
    prepared inputs therefore agree on every fact the B_DERIVE gates
    print - day universe, day count, trial, commit, method digest,
    method version, supplement id - and disagree only in custody bytes.

    Asserted in that order: first the agreement (so the pairing really is
    a near-miss), then the refusal."""
    other = make_prod(_bundle(pnl=41.5))
    other_auth = sa.derive_supplement_authority(other)

    # --- the near-miss is genuinely near -------------------------------
    assert other is not prod
    assert other.trial_id == prod.trial_id
    assert other.authorized_commit == prod.authorized_commit
    assert other.method_digest == prod.method_digest
    assert other.test_only is prod.test_only is False
    assert other.source_artifact_id == prod.source_artifact_id
    ident_a = sa.enforce_day_universe_identity(prod)
    ident_b = sa.enforce_day_universe_identity(other)
    assert ident_a.day_universe == ident_b.day_universe == ALL_DAYS
    assert ident_a.day_universe_digest == ident_b.day_universe_digest
    assert ident_a.n_days == ident_b.n_days
    assert other_auth.day_universe_digest == authority.day_universe_digest
    assert other_auth.method_version == authority.method_version
    assert other_auth.supplement_id == authority.supplement_id
    # ... and the two DO differ in custody bytes
    assert other.records_digest != prod.records_digest
    assert other.source_artifact_sha256 != prod.source_artifact_sha256
    assert sa.bundle_table_digest(other.file_sha256) != \
        sa.bundle_table_digest(prod.file_sha256)

    # --- the refusal ---------------------------------------------------
    with pytest.raises(sa.SupplementError) as ei:
        sa.verify_supplement_authority(authority, other)
    assert ei.value.code == \
        "supplement_authority_source_artifact_sha256_mismatch"

    code, msg = _gate_refusal("custody_authority_binding",
                              _ctx(authority=authority, prepared=other))
    assert "supplement_authority_source_artifact_sha256_mismatch" in msg
    assert _stage_refusal("B_DERIVE",
                          _ctx(authority=authority, prepared=other))[0] == \
        "gate_refused:custody_authority_binding"

    # each authority still verifies against its OWN input
    assert sa.verify_supplement_authority(other_auth, other) is other_auth


def test_n4_the_production_builder_refuses_a_foreign_prepared_input(
        prod, authority, make_prod):
    other = make_prod(_bundle(pnl=41.5))
    rows = _rows(authority.expected_day_set)
    assert sp.build_supplement_from_authority(
        authority, prod, rows) is not None                 # the near-miss
    with pytest.raises(sa.SupplementError) as ei:
        sp.build_supplement_from_authority(authority, other, rows)
    assert ei.value.code == \
        "supplement_authority_source_artifact_sha256_mismatch"


# ===========================================================================
# 5. drift in each bound fact, each under its OWN gate
# ===========================================================================

def test_n5_bundle_digest_drift_refuses_at_source_bundle_digest(
        prod, authority):
    """Only `S0_REPORT.md`'s pinned digest moves - a file whose BYTES the
    prepared input does not retain, so custody link 1 still passes and
    the object is otherwise perfect. A battery receipt is minted over it,
    so the factory boundary is genuinely satisfied."""
    forged = _forged_prepared(
        prod, file_sha256={**dict(prod.file_sha256),
                           "S0_REPORT.md": "a" * 64})
    ctx = _ctx(authority=authority, prepared=forged)

    # --- the near-miss passes everything except the one thing moved ----
    assert run.GATES["custody_authority_production"](ctx) is None
    assert run.GATES["day_universe_identity"](ctx) is None
    assert run.GATES["method_version_pinned"](ctx) is None
    assert sa.enforce_day_universe_identity(forged).day_universe_digest == \
        authority.day_universe_digest

    # --- and refuses under its own gate --------------------------------
    _gate_refusal("source_bundle_digest", ctx)
    with pytest.raises(sa.SupplementError) as ei:
        sa.verify_supplement_authority(authority, forged)
    assert ei.value.code == "supplement_authority_bundle_table_mismatch"


def test_n5_day_universe_drift_refuses_at_day_universe_identity(
        prod, authority, make_prod):
    """A SUBSTITUTED day: same count, one different date. The digest
    branch must fire while the count branch cannot."""
    substituted = make_prod(_bundle(days=SUBSTITUTED_DAYS))
    ident = sa.enforce_day_universe_identity(substituted)

    # --- near-miss: the substituted universe is itself perfectly legal --
    assert ident.n_days == authority.n_days == 5
    assert ident.day_universe == SUBSTITUTED_DAYS
    assert ident.day_universe_digest != authority.day_universe_digest
    sub_auth = sa.derive_supplement_authority(substituted)
    assert sa.verify_supplement_authority(sub_auth, substituted) is sub_auth

    ctx = _ctx(authority=authority, prepared=substituted)
    _, msg = _gate_refusal("day_universe_identity", ctx)
    assert "!= authority" in msg


def test_n5_day_count_drift_refuses_at_day_universe_identity(
        prod, authority, make_prod):
    six = make_prod(_bundle(days=SIX_DAYS))
    ident = sa.enforce_day_universe_identity(six)
    assert ident.n_days == 6 != authority.n_days
    ctx = _ctx(authority=authority, prepared=six)
    _gate_refusal("day_universe_identity", ctx)
    # and the same pair dies at the earlier binding gate in stage order
    assert _stage_refusal("B_DERIVE", ctx)[0] == \
        "gate_refused:custody_authority_binding"


def test_n5_a_broken_day_universe_refuses_at_day_universe_identity(
        prod, authority):
    """Not merely a DIFFERENT universe - a structurally invalid one. The
    gate must surface the §D.2.2 code, not a generic mismatch."""
    seqs = {ch: tuple(prod.day_sequences[ch]) for ch in prod.day_sequences}
    tps = {ch: frozenset(prod.traded_day_sets[ch])
           for ch in prod.traded_day_sets}
    broken = dict(seqs)
    broken[PRIMARY] = tuple(reversed(seqs[PRIMARY]))
    forged = _forged_prepared(prod, day_sequences=broken,
                              traded_day_sets=tps)
    with pytest.raises(sa.MCInputError) as ei:
        sa.enforce_day_universe_identity(forged)
    assert ei.value.code == "day_sequence_not_ascending"
    _, msg = _gate_refusal("day_universe_identity",
                           _ctx(authority=authority, prepared=forged))
    assert "day_sequence_not_ascending" in msg


def test_n5_method_digest_drift_refuses_at_custody_authority_binding(
        prod, authority):
    forged = _forged_prepared(prod, method_digest="f" * 64)
    ctx = _ctx(authority=authority, prepared=forged)

    # --- near-miss: every OTHER B_DERIVE gate still accepts this object -
    assert run.GATES["custody_authority_production"](ctx) is None
    assert run.GATES["source_bundle_digest"](ctx) is None
    assert run.GATES["day_universe_identity"](ctx) is None
    assert run.GATES["method_version_pinned"](ctx) is None

    _, msg = _gate_refusal("custody_authority_binding", ctx)
    assert "supplement_authority_method_digest_mismatch" in msg


def test_n5_method_version_drift_refuses_at_method_version_pinned(
        prod, authority, monkeypatch):
    """The frozen method token is REPINNED after the authority was
    minted - exactly what a method-version bump would look like to an
    authority carried across it."""
    ctx = _ctx(authority=authority, prepared=prod)
    assert run.GATES["method_version_pinned"](ctx) is None   # near-miss

    monkeypatch.setattr(sa, "SUPPLEMENT_METHOD_VERSION", "mc-freeze-v2")
    assert authority.method_version == "mc-freeze-v1"
    _gate_refusal("method_version_pinned", ctx)
    _, msg = _gate_refusal("custody_authority_binding", ctx)
    assert "supplement_authority_method_version_mismatch" in msg
    with pytest.raises(sa.SupplementError) as ei:
        sa.verify_supplement_authority(authority, prod)
    assert ei.value.code == "supplement_authority_method_version_mismatch"


def test_n5_supplement_id_drift_refuses_at_custody_authority_binding(
        prod, authority):
    """`MC-DS-S002` is a LEGAL id - it passes the A_PRECHECK pattern gate
    - so the refusal below is about the binding, not the grammar."""
    ctx = _ctx(authority=authority, prepared=prod, supplement_id=OTHER_SID)
    assert sc.SUPPLEMENT_ID_PATTERN.match(OTHER_SID)
    assert run.GATES["supplement_id_pattern"](ctx) is None   # near-miss
    _, msg = _gate_refusal("custody_authority_binding", ctx)
    assert "supplement_authority_supplement_id_mismatch" in msg


def test_n5_the_execution_commit_is_not_this_gates_business(prod, authority):
    """REWRITTEN 2026-09-05 (Aaron's ruling). This used to assert that a P2
    commit or a HEAD differing from the AUTHORITY's commit each produced
    their own refusal here. That encoded a confusion: the authority carries
    the SOURCE commit -- the one that sealed the bundle -- and demanding it
    equal the execution commit is unsatisfiable, because the supplement
    always runs at a later commit than the trial it consumes. The first run
    ever to reach B_DERIVE died on it.

    Both of those are now legal at this gate, and the SOURCE binding it
    exists for is untouched -- `test_n5_a_prepared_input_whose_commit_moved`
    below still refuses a bundle whose commit does not match the authority.
    The execution side is asserted in section S.
    """
    exec_ctx = _ctx(authority=authority, prepared=prod,
                    head_commit="c" * 40,
                    chain=FakeChain(live_authorizations=(
                        FakeP2(authorized_commit="c" * 40),)))
    assert run.GATES["custody_authority_binding"](exec_ctx) is None
    assert authority.authorized_commit != "c" * 40


def test_n5_a_prepared_input_whose_commit_moved_is_refused(prod, authority):
    forged = _forged_prepared(prod, authorized_commit=OTHER_COMMIT)
    _, msg = _gate_refusal("custody_authority_binding",
                           _ctx(authority=authority, prepared=forged))
    assert "supplement_authority_commit_mismatch" in msg


def test_n5_a_prepared_input_whose_trial_moved_is_refused(prod, authority):
    forged = _forged_prepared(prod, trial_id="S0-T999")
    _, msg = _gate_refusal("custody_authority_binding",
                           _ctx(authority=authority, prepared=forged))
    assert "supplement_authority_trial_mismatch" in msg


# ===========================================================================
# 6. test_only never reaches production, in EITHER order
# ===========================================================================

def test_n6_a_test_only_authority_never_enters_the_production_path(
        prod, test_prepared, test_authority):
    assert type(test_authority) is sa.SupplementAuthority   # a REAL one
    assert test_authority.test_only is True
    assert sa.verify_supplement_authority(
        test_authority, test_prepared) is test_authority     # near-miss

    _gate_refusal("custody_authority_production",
                  _ctx(authority=test_authority, prepared=prod))
    with pytest.raises(sp.SupplementProductionError) as ei:
        sp.build_supplement_from_authority(
            test_authority, test_prepared,
            _rows(test_authority.expected_day_set))
    assert ei.value.code == "production_authority_test_only"


def test_n6_a_test_only_prepared_input_never_enters_the_production_path(
        prod, authority, test_prepared):
    _, msg = _gate_refusal("custody_authority_production",
                           _ctx(authority=authority, prepared=test_prepared))
    assert "test_only prepared input" in msg
    with pytest.raises(sa.SupplementError) as ei:
        sp.build_supplement_from_authority(
            authority, test_prepared, _rows(authority.expected_day_set))
    assert ei.value.code == \
        "supplement_authority_source_artifact_id_mismatch"


def test_n6_a_test_only_input_wearing_the_production_custody_source_fails(
        prod, authority):
    """The sharpest version: a TEST_ONLY prepared input that CLAIMS the
    approved attestation path AND the code-pinned digest, so the
    provenance strings the earlier checks compare all agree."""
    bundle = _bundle()
    disguised = _prepare_for_tests(bundle, custody=mcc.CustodyAuthority(
        trial_id=TRIAL, authorized_commit=COMMIT,
        source_artifact_id=mcc.ATTESTATION_PATH,
        source_artifact_sha256=prod.source_artifact_sha256,
        file_sha256={n: hashlib.sha256(b).hexdigest()
                     for n, b in bundle.items()},
        test_only=True))

    # --- near-miss: it really does wear the production custody source ---
    assert disguised.test_only is True
    assert disguised.source_artifact_id == prod.source_artifact_id
    assert disguised.source_artifact_sha256 == prod.source_artifact_sha256
    assert sa.bundle_table_digest(disguised.file_sha256) == \
        authority.bundle_table_digest
    assert sa.enforce_day_universe_identity(disguised).day_universe_digest \
        == authority.day_universe_digest
    assert mcc.verify_battery_receipt(disguised) is not None

    # --- the provenance bytes still separate them ----------------------
    with pytest.raises(sa.SupplementError) as ei:
        sa.verify_supplement_authority(authority, disguised)
    assert ei.value.code == "supplement_authority_source_input_mismatch"
    _gate_refusal("custody_authority_production",
                  _ctx(authority=authority, prepared=disguised))
    with pytest.raises(sa.SupplementError) as ei:
        sp.build_supplement_from_authority(
            authority, disguised, _rows(authority.expected_day_set))
    assert ei.value.code == "supplement_authority_source_input_mismatch"


def test_n6_the_two_derivation_entries_partition_the_world(prod,
                                                           test_prepared):
    """Neither entry may accept the other's object, in either order -
    otherwise `test_only` is a label rather than a boundary."""
    assert sa.derive_supplement_authority(prod).test_only is False
    assert sa.derive_supplement_authority_for_tests(
        test_prepared).test_only is True                     # near-miss

    with pytest.raises(sa.SupplementError) as ei:
        sa.derive_supplement_authority(test_prepared)
    assert ei.value.code == "supplement_authority_test_only_in_production"
    with pytest.raises(sa.SupplementError) as ei:
        sa.derive_supplement_authority_for_tests(prod)
    assert ei.value.code == \
        "supplement_authority_production_object_in_test_entry"


def test_n6_the_production_entry_pins_the_custody_source_and_its_bytes(
        prod):
    """The custody-source leg, attacked one field at a time. Neither
    forgery needs a battery receipt: both checks fire BEFORE the factory
    boundary, which is the fail-closed ordering."""
    assert sa.derive_supplement_authority(prod) is not None  # near-miss

    wrong_id = _hand_built(prod, source_artifact_id="TEST_ONLY_SYNTHETIC")
    with pytest.raises(sa.SupplementError) as ei:
        sa.derive_supplement_authority(wrong_id)
    assert ei.value.code == "supplement_authority_source_violation"

    wrong_bytes = _hand_built(prod, source_artifact_sha256="9" * 64)
    with pytest.raises(sa.SupplementError) as ei:
        sa.derive_supplement_authority(wrong_bytes)
    assert ei.value.code == "supplement_authority_source_digest_violation"


def test_n6_neither_entry_accepts_a_non_prepared_object_or_a_bad_id(
        prod, authority):
    for bad in (None, {"trial_id": TRIAL}, "prepared"):
        with pytest.raises(sa.SupplementError) as ei:
            sa.derive_supplement_authority(bad)
        assert ei.value.code == \
            "supplement_authority_prepared_input_required"
        with pytest.raises(sa.SupplementError) as ei:
            sa.verify_supplement_authority(authority, bad)
        assert ei.value.code == \
            "supplement_authority_prepared_input_required"
    with pytest.raises(sa.SupplementError) as ei:
        sa.derive_supplement_authority(prod, supplement_id="MC-DS-9")
    assert ei.value.code == "supplement_authority_supplement_id_pattern"


def test_n6_an_authority_cannot_be_constructed_or_replaced_by_a_caller(
        authority):
    """The N03 factory boundary, re-asserted from a lane that did not
    write it - section Y measures how far `__new__` gets around it."""
    kwargs = {f.name: getattr(authority, f.name)
              for f in dataclasses.fields(authority) if f.init}
    assert kwargs["capability"] is None
    with pytest.raises(sa.SupplementError) as ei:
        sa.SupplementAuthority(**kwargs)
    assert ei.value.code == "supplement_authority_capability_required"
    for over in ({}, {"n_days": 4}):
        with pytest.raises(sa.SupplementError) as ei:
            dataclasses.replace(authority, **over)
        assert ei.value.code == "supplement_authority_capability_required"


# ===========================================================================
# 7. hand-built / replaced / grafted products
# ===========================================================================

@pytest.fixture()
def genuine(prod, authority):
    return sp.build_supplement_from_authority(
        authority, prod, _rows(authority.expected_day_set))


def test_n7_a_mapping_is_not_a_production_product(prod, authority, genuine,
                                                  tmp_path):
    out = tmp_path / "seal"
    out.mkdir()
    payload = dict(genuine.payload)
    with pytest.raises(sp.SupplementProductionError) as ei:
        sp.verify_production_receipt(payload, authority, prod)
    assert ei.value.code == "production_product_type"
    assert _seal_refusal(payload, out, authority=authority,
                         prepared=prod) == "production_product_type"


def test_n7_a_hand_built_product_carries_no_receipt(prod, authority,
                                                    genuine, tmp_path):
    out = tmp_path / "seal"
    out.mkdir()
    hand = sp.SupplementProduct(payload=dict(genuine.payload))
    assert hand.payload == genuine.payload                   # near-miss
    assert hand.supplement_id == genuine.supplement_id
    assert hand.receipt is None
    with pytest.raises(sp.SupplementProductionError) as ei:
        sp.verify_production_receipt(hand, authority, prod)
    assert ei.value.code == "production_not_factory_built"
    assert _seal_refusal(hand, out, authority=authority, prepared=prod) == \
        "production_not_factory_built"


def test_n7_dataclasses_replace_drops_the_receipt(prod, authority, genuine,
                                                  tmp_path):
    out = tmp_path / "seal"
    out.mkdir()
    for kwargs in ({}, {"payload": dict(genuine.payload)}):
        replaced = dataclasses.replace(genuine, **kwargs)
        assert replaced.payload == genuine.payload           # near-miss
        assert replaced.receipt is None, (
            "`dataclasses.replace` must not carry an init=False receipt "
            "across, or a replaced product would seal")
        assert _seal_refusal(replaced, out, authority=authority,
                             prepared=prod) == "production_not_factory_built"


def test_n7_a_grafted_receipt_does_not_describe_another_payload(
        prod, authority, genuine, tmp_path):
    """The receipt is unforgeable but MOVABLE, so it must also be BOUND."""
    out = tmp_path / "seal"
    out.mkdir()
    other_rows = _rows(authority.expected_day_set)
    other_rows[0] = {**other_rows[0], "vol_stratum": "T3"}
    other = sp.build_supplement_from_authority(authority, prod, other_rows)
    assert other.payload != genuine.payload
    assert sp.verify_production_receipt(other, authority, prod) is \
        other.receipt                                        # near-miss

    victim = sp.SupplementProduct(payload=dict(other.payload))
    object.__setattr__(victim, "receipt", genuine.receipt)
    assert victim.receipt is genuine.receipt
    with pytest.raises(sp.SupplementProductionError) as ei:
        sp.verify_production_receipt(victim, authority, prod)
    assert ei.value.code == "production_receipt_mismatch"
    assert _seal_refusal(victim, out, authority=authority, prepared=prod) \
        == "production_receipt_mismatch"


def test_n7_a_receipt_cannot_be_constructed_or_replaced_by_a_caller(
        genuine):
    fields = {f.name: getattr(genuine.receipt, f.name)
              for f in dataclasses.fields(genuine.receipt) if f.init}
    assert fields["capability"] is None
    with pytest.raises(sp.SupplementProductionError) as ei:
        sp.ProductionReceipt(**fields)
    assert ei.value.code == "production_receipt_capability_required"
    for kwargs in ({}, {"trial_id": "S0-T999"}):
        with pytest.raises(sp.SupplementProductionError) as ei:
            dataclasses.replace(genuine.receipt, **kwargs)
        assert ei.value.code == "production_receipt_capability_required"


def test_n7_a_non_mapping_payload_is_refused_at_construction(genuine):
    for bad in ([dict(r) for r in genuine.payload["rows"]], "payload", 7):
        with pytest.raises(sp.SupplementProductionError) as ei:
            sp.SupplementProduct(payload=bad)
        assert ei.value.code == "production_payload_type"


# ===========================================================================
# 8. the two decisive arguments are UNSUPPLIABLE
# ===========================================================================

def test_n8_the_decisive_arguments_are_refused_not_ignored(prod, authority):
    """The 617f7c3 defect verbatim: a hand-assembled
    `(expected_day_set, binding)` pair built and sealed a supplement.
    Supplying either must be a REFUSAL, not a silently ignored keyword."""
    rows = _rows(authority.expected_day_set)
    assert sp.build_supplement_from_authority(authority, prod, rows) \
        is not None                                          # near-miss

    hand_binding = {"trial_id": TRIAL, "authorized_commit": COMMIT,
                    "day_universe_digest": "d" * 64,
                    "method_version": "mc-freeze-v1",
                    "source_input_sha256": "e" * 64}
    for kwargs in ({"expected_day_set": frozenset(ALL_DAYS)},
                   {"binding": hand_binding},
                   {"expected_day_set": frozenset(ALL_DAYS),
                    "binding": hand_binding}):
        with pytest.raises(sp.SupplementProductionError) as ei:
            sp.build_supplement_from_authority(authority, prod, rows,
                                               **kwargs)
        assert ei.value.code == "production_decisive_argument_supplied"

    with pytest.raises(sp.SupplementProductionError) as ei:
        sp.build_supplement_from_authority(authority, prod, rows,
                                           day_universe_digest="d" * 64)
    assert ei.value.code == "production_unknown_argument"


# ===========================================================================
# 9. a TEST_ONLY hermetic payload cannot reach the production seal
# ===========================================================================

def test_n9_a_hermetic_payload_seals_test_only_and_never_production(
        prod, authority, tmp_path):
    """The 617f7c3 route end to end. The payload is built from a
    HAND-ASSEMBLED day set and binding, and is genuinely well formed -
    `seal_supplement_test_only` accepts it. Only the production seal
    refuses it, and it refuses because there is no receipt."""
    hand_binding = {"trial_id": TRIAL, "authorized_commit": COMMIT,
                    "day_universe_digest": "d" * 64,
                    "method_version": "mc-freeze-v1",
                    "source_input_sha256": "e" * 64}
    payload = dss.build_day_strata_supplement_test_only(
        _rows(ALL_DAYS), expected_day_set=frozenset(ALL_DAYS),
        binding=hand_binding)

    # --- near-miss: the hermetic core really does seal it --------------
    hermetic = tmp_path / "hermetic"
    sha = dss.seal_supplement_test_only(payload, hermetic)
    assert (hermetic / dss.SUPPLEMENT_FILENAME).exists()
    assert len(sha) == 64

    # --- and the production seal refuses it, twice over ----------------
    out = tmp_path / "seal"
    out.mkdir()
    assert _seal_refusal(payload, out, authority=authority, prepared=prod) \
        == "production_product_type"
    wrapped = sp.SupplementProduct(payload=payload)
    assert wrapped.receipt is None
    assert _seal_refusal(wrapped, out, authority=authority, prepared=prod) \
        == "production_not_factory_built"


def test_n9_the_hermetic_names_are_the_only_hermetic_entry_points():
    """The rename is the disclosure. If a bare `build_day_strata_
    supplement` / `seal_supplement` ever reappears, a call site can drift
    back onto the unbound core without saying so."""
    assert not hasattr(dss, "build_day_strata_supplement")
    assert not hasattr(dss, "seal_supplement")
    assert callable(dss.build_day_strata_supplement_test_only)
    assert callable(dss.seal_supplement_test_only)


# ===========================================================================
# 10. mutation of a genuine product AFTER minting
# ===========================================================================

def test_n10_in_place_row_mutation_through_the_shallow_proxy_is_caught(
        prod, authority, genuine, tmp_path):
    """`SupplementProduct.__post_init__` wraps a SHALLOW dict copy, so
    the row dicts and the binding dict inside the proxy are STILL
    MUTABLE. This is the attack that shallow immutability invites."""
    out = tmp_path / "seal"
    out.mkdir()
    assert sp.verify_production_receipt(genuine, authority, prod) is \
        genuine.receipt                                      # near-miss

    row = genuine.payload["rows"][0]
    assert isinstance(row, dict), (
        "if rows ever become immutable this probe is obsolete - but a "
        "mutable row must be caught, not assumed away")
    row["vol_stratum"] = "T3"
    with pytest.raises(sp.SupplementProductionError) as ei:
        sp.verify_production_receipt(genuine, authority, prod)
    assert ei.value.code == "production_receipt_mismatch"
    assert _seal_refusal(genuine, out, authority=authority, prepared=prod) \
        == "production_receipt_mismatch"


def test_n10_in_place_binding_mutation_is_caught(prod, authority, genuine,
                                                 tmp_path):
    out = tmp_path / "seal"
    out.mkdir()
    binding = genuine.payload["binding"]
    assert isinstance(binding, dict)
    binding["trial_id"] = "S0-T999"
    assert _seal_refusal(genuine, out, authority=authority, prepared=prod) \
        == "production_receipt_mismatch"


def test_n10_a_swapped_payload_is_caught(prod, authority, genuine,
                                         tmp_path):
    """Every field of the payload replaced through `object.__setattr__`,
    each variant internally CONSISTENT so nothing but the receipt can
    notice."""
    out = tmp_path / "seal"
    out.mkdir()
    base = dict(genuine.payload)
    rows = tuple(dict(r) for r in base["rows"])

    short = rows[:-1]
    variants = {
        "rows_and_digest": {**base, "rows": short, "n_rows": len(short),
                            "rows_digest": dss.canonical_rows_digest(short)},
        "rows_digest_only": {**base, "rows_digest": "0" * 64},
        "binding": {**base,
                    "binding": {**dict(base["binding"]),
                                "authorized_commit": OTHER_COMMIT}},
        "supplement_id": {**base, "supplement_id": OTHER_SID},
    }
    for label, payload in variants.items():
        victim = sp.SupplementProduct(payload=dict(genuine.payload))
        object.__setattr__(victim, "receipt", genuine.receipt)
        object.__setattr__(victim, "payload", payload)
        with pytest.raises(sp.SupplementProductionError) as ei:
            sp.verify_production_receipt(victim, authority, prod)
        assert ei.value.code == "production_receipt_mismatch", label
        assert _seal_refusal(victim, out, authority=authority,
                             prepared=prod) == "production_receipt_mismatch"


# ===========================================================================
# 11. a refused seal writes NOTHING
#     (asserted inline by `_seal_refusal` above; this is the aggregate)
# ===========================================================================

def test_n11_no_refusal_anywhere_leaves_a_byte_in_the_output_directory(
        prod, authority, genuine, tmp_path):
    """One directory, every refusal route in sequence, one listing
    assertion after each. A `.partial` left behind by a refused seal
    would be exactly the residue the ratified discipline forbids."""
    out = tmp_path / "seal"
    out.mkdir()
    assert _listing(out) == []

    hand = sp.SupplementProduct(payload=dict(genuine.payload))
    replaced = dataclasses.replace(genuine)
    grafted = sp.SupplementProduct(payload={**dict(genuine.payload),
                                            "n_rows": 99})
    object.__setattr__(grafted, "receipt", genuine.receipt)

    codes = [
        _seal_refusal(dict(genuine.payload), out, authority=authority,
                      prepared=prod),
        _seal_refusal(hand, out, authority=authority, prepared=prod),
        _seal_refusal(replaced, out, authority=authority, prepared=prod),
        _seal_refusal(grafted, out, authority=authority, prepared=prod),
        _seal_refusal(genuine, out, authority=_mirror_authority(authority),
                      prepared=prod),
    ]
    assert codes == ["production_product_type",
                     "production_not_factory_built",
                     "production_not_factory_built",
                     "production_receipt_mismatch",
                     "production_authority_type"]
    assert _listing(out) == []

    # the genuine product still seals into the SAME directory afterwards,
    # so the refusals did not poison it
    action, _ = sp.seal_supplement_production(
        genuine, out, authority=authority, prepared=prod, incident_id=INC)
    assert action.action == "promote"
    assert _listing(out) == [dss.SUPPLEMENT_FILENAME]


# ===========================================================================
# X. DISCLOSED: the production receipt is forgeable with NO private access
#
# `ProductionReceipt` is a frozen slots dataclass, so `__new__` plus
# `object.__setattr__` produces one WITHOUT ever entering
# `__post_init__` - the capability is never asked for. The forger needs
# nothing module-private: the six component digests are all recomputable
# from the public API (`_components_locally` below is asserted equal to
# the module's own).
#
# This is the same hole as section Y, one layer down. It used to say
# re-derivation was the thing that actually holds; rounds 2, 3 and 4
# each refuted that. Re-derivation holds only where the re-derived
# value cannot answer the comparison itself -- which is why the exact
# built-in rule now applies at all three sites (payload freeze, builder
# rows, authority day universe).
# ===========================================================================

def _components_locally(authority, prepared, payload):
    """`supplement_production._components`, rebuilt from PUBLIC API only.

    The point of writing it out is that a forger needs no private
    handle; `test_x_*_needs_nothing_private` asserts this reproduction is
    faithful, using the module's own function purely as an ORACLE."""
    return {
        "authority": authority.authority_digest,
        "prepared": mcc.prepared_digest(prepared),
        "binding": hashlib.sha256(
            dss.canonical_json(dict(payload["binding"]))
            .encode("utf-8")).hexdigest(),
        "day_universe": authority.day_universe_digest,
        "rows": payload["rows_digest"],
        "payload": hashlib.sha256(
            dss.canonical_supplement_bytes(payload)).hexdigest(),
    }


def _forged_receipt(authority, prepared, payload, **over):
    """A receipt the minter never made. `__new__` skips `__post_init__`,
    so `production_receipt_capability_required` is never evaluated."""
    fields = dict(capability=None, schema=sp.PRODUCTION_RECEIPT_SCHEMA,
                  supplement_id=authority.supplement_id,
                  trial_id=authority.trial_id,
                  authorized_commit=authority.authorized_commit,
                  components=_components_locally(authority, prepared,
                                                 payload))
    fields.update(over)
    receipt = sp.ProductionReceipt.__new__(sp.ProductionReceipt)
    for name, value in fields.items():
        object.__setattr__(receipt, name, value)
    return receipt


def _forged_product(authority, prepared, payload, **over):
    product = sp.SupplementProduct(payload=payload)
    object.__setattr__(
        product, "receipt",
        _forged_receipt(authority, prepared, product.payload, **over))
    return product


def test_x_forging_a_receipt_needs_nothing_private(prod, authority,
                                                   genuine):
    """FINDING: `production_receipt_capability_required` guards
    `__init__` and `dataclasses.replace` (section 7 proves both), and
    nothing else. `__new__` walks around it, and every component digest
    is public arithmetic - so a receipt indistinguishable from the
    factory's can be attached to any payload."""
    payload = dict(genuine.payload)
    assert _components_locally(authority, prod, genuine.payload) == \
        sp._components(authority, prod, genuine.payload), (
        "the public reproduction of the component table drifted from the "
        "module's - re-derive it before trusting the tests below")

    forged = _forged_product(authority, prod, payload)
    assert type(forged.receipt) is sp.ProductionReceipt
    assert forged.receipt is not genuine.receipt
    assert sp.verify_production_receipt(forged, authority, prod) is \
        forged.receipt, (
        "if this refuses now, the receipt grew a check `__new__` cannot "
        "skip - delete the finding")


def test_x_the_module_private_capability_is_also_one_getattr_away(
        prod, authority, genuine):
    """The lesser hole, recorded for completeness: `_CAPABILITY` is a
    module attribute, and it is the ONLY route to
    `production_receipt_incomplete`."""
    receipt = sp.ProductionReceipt(
        capability=sp._CAPABILITY, schema=sp.PRODUCTION_RECEIPT_SCHEMA,
        supplement_id=authority.supplement_id,
        trial_id=authority.trial_id,
        authorized_commit=authority.authorized_commit,
        components=sp._components(authority, prod, genuine.payload))
    assert receipt.capability is None
    product = sp.SupplementProduct(payload=dict(genuine.payload))
    object.__setattr__(product, "receipt", receipt)
    assert sp.verify_production_receipt(product, authority, prod) is receipt

    with pytest.raises(sp.SupplementProductionError) as ei:
        sp.ProductionReceipt(
            capability=sp._CAPABILITY, schema=sp.PRODUCTION_RECEIPT_SCHEMA,
            supplement_id=authority.supplement_id,
            trial_id=authority.trial_id,
            authorized_commit=authority.authorized_commit,
            components={"authority": "x"})
    assert ei.value.code == "production_receipt_incomplete"


def test_x_receipt_trial_and_commit_are_re_checked_against_the_authority(
        prod, authority, genuine, tmp_path):
    out = tmp_path / "seal"
    out.mkdir()
    payload = dict(genuine.payload)
    for over, code in (({"trial_id": "S0-T999"},
                        "production_receipt_trial_mismatch"),
                       ({"authorized_commit": OTHER_COMMIT},
                        "production_receipt_commit_mismatch")):
        forged = _forged_product(authority, prod, payload, **over)
        with pytest.raises(sp.SupplementProductionError) as ei:
            sp.verify_production_receipt(forged, authority, prod)
        assert ei.value.code == code
        assert _seal_refusal(forged, out, authority=authority,
                             prepared=prod) == code


def test_x_the_seals_second_line_of_defence_catches_binding_drift(
        prod, authority, genuine, tmp_path):
    """A receipt that HONESTLY describes a drifted payload: verification
    passes, and only the seal's re-derivation from the authority
    refuses."""
    out = tmp_path / "seal"
    out.mkdir()
    drifted = {**dict(genuine.payload),
               "binding": {**dict(genuine.payload["binding"]),
                           "trial_id": "S0-T999"}}
    forged = _forged_product(authority, prod, drifted)
    assert sp.verify_production_receipt(forged, authority, prod) is \
        forged.receipt                                       # near-miss
    assert _seal_refusal(forged, out, authority=authority, prepared=prod) \
        == "production_binding_drift"


def test_x_day_universe_drift_is_shadowed_by_binding_drift(
        prod, authority, genuine, tmp_path):
    """FINDING: `production_day_universe_drift` is STRUCTURALLY
    UNREACHABLE. The seal compares the whole binding against the one the
    authority derives first, and `day_universe_digest` is a member of
    that binding - so any payload that could trip the day-universe branch
    has already tripped `production_binding_drift`."""
    out = tmp_path / "seal"
    out.mkdir()
    drifted = {**dict(genuine.payload),
               "binding": {**dict(genuine.payload["binding"]),
                           "day_universe_digest": "d" * 64}}
    forged = _forged_product(authority, prod, drifted)
    assert drifted["binding"]["day_universe_digest"] != \
        authority.day_universe_digest
    assert _seal_refusal(forged, out, authority=authority, prepared=prod) \
        == "production_binding_drift"
    assert "production_day_universe_drift" in \
        Path(sp.__file__).read_text(encoding="utf-8")


def test_x_the_seal_recomputes_the_day_set_and_the_rows_digest(
        prod, authority, genuine, tmp_path):
    out = tmp_path / "seal"
    out.mkdir()
    rows = tuple(dict(r) for r in genuine.payload["rows"])[:-1]
    short = {**dict(genuine.payload), "rows": rows, "n_rows": len(rows),
             "rows_digest": dss.canonical_rows_digest(rows)}
    forged = _forged_product(authority, prod, short)
    assert sp.verify_production_receipt(forged, authority, prod) is \
        forged.receipt                                       # near-miss
    assert _seal_refusal(forged, out, authority=authority, prepared=prod) \
        == "production_day_set_drift"

    lying = {**dict(genuine.payload), "rows_digest": "0" * 64}
    forged = _forged_product(authority, prod, lying)
    assert sp.verify_production_receipt(forged, authority, prod) is \
        forged.receipt                                       # near-miss
    assert _seal_refusal(forged, out, authority=authority, prepared=prod) \
        == "production_rows_digest_drift"


def test_x_the_production_seal_now_re_validates_the_supplement_object(
        prod, authority, genuine, tmp_path):
    """F3, REPAIRED AND NOW PINNED - the blind no-outcome guarantee.

    `seal_supplement_test_only` re-runs `_validate_supplement_object` at
    the seal boundary, and row field-set exactness IS the blind
    guarantee. `seal_supplement_production` USED NOT TO: it trusted the
    receipt for the payload's SHAPE and re-derived only the binding, the
    day set and the rows digest, so a payload whose every row carried
    `"pnl": 12.5` was refused by the TEST_ONLY seal and SEALED by the
    production one - reachable with no module-private access at all,
    since the receipt below is forged through `__new__`.

    Both seals now refuse it, and the production seal writes nothing.

    F7b, ALSO REPAIRED: the first cut of this repair added two codes but
    only one could fire - `_validate_supplement_object` refuses an extra
    row key itself and ran FIRST, shadowing the specific code. The order
    is now reversed, so a forbidden row field keeps its own name
    (`production_forbidden_row_field`) and the generic object validation
    stays as the backstop behind it."""
    rows = tuple({**dict(r), "pnl": 12.5}
                 for r in genuine.payload["rows"])
    tainted = {**dict(genuine.payload), "rows": rows, "n_rows": len(rows),
               "rows_digest": dss.canonical_rows_digest(rows)}

    # --- near-miss: the tainted payload is otherwise perfectly bound ---
    forged = _forged_product(authority, prod, tainted)
    assert sp.verify_production_receipt(forged, authority, prod) is \
        forged.receipt
    assert dict(tainted["binding"]) == authority.supplement_binding()
    assert frozenset(r["trade_date"] for r in rows) == \
        authority.expected_day_set
    assert tainted["rows_digest"] == dss.canonical_rows_digest(rows)

    # --- the TEST_ONLY seal refuses under the blind-guarantee code -----
    with pytest.raises(dss.SupplementError) as ei:
        dss.seal_supplement_test_only(tainted, tmp_path / "hermetic")
    assert ei.value.code == "supplement_forbidden_field"
    assert not (tmp_path / "hermetic" / dss.SUPPLEMENT_FILENAME).exists()

    # --- and so, now, does the PRODUCTION seal -------------------------
    out = tmp_path / "seal"
    out.mkdir()
    assert _seal_refusal(forged, out, authority=authority, prepared=prod) \
        == "production_forbidden_row_field"
    assert not (out / dss.SUPPLEMENT_FILENAME).exists()

    # the detail NAMES the hermetic code, so triage is not lost in the
    # re-wrapping
    with pytest.raises(sp.SupplementProductionError) as ei:
        sp.seal_supplement_production(forged, out, authority=authority,
                                      prepared=prod, incident_id=INC)
    # triage is not lost: with the SPECIFIC check first, the detail now
    # names the offending row index and key, which is sharper than the
    # hermetic code it used to be re-wrapped in.
    assert "row 0" in str(ei.value) and "pnl" in str(ei.value)


def test_x_a_malformed_payload_shape_also_refuses_at_the_production_seal(
        prod, authority, genuine, tmp_path):
    """The F3 repair is not only about rows: an extra TOP-LEVEL key is a
    supplement-object schema violation, and the production seal must
    refuse it under the same code rather than serialising it."""
    out = tmp_path / "seal"
    out.mkdir()
    misshapen = {**dict(genuine.payload), "oracle_note": "TP-heavy"}
    forged = _forged_product(authority, prod, misshapen)
    assert sp.verify_production_receipt(forged, authority, prod) is \
        forged.receipt                                       # near-miss
    assert _seal_refusal(forged, out, authority=authority, prepared=prod) \
        == "production_supplement_object_invalid"


def test_x_production_forbidden_row_field_is_reachable_and_named(
        prod, authority, genuine, tmp_path):
    """F7b, REPAIRED AND NOW PINNED.

    The first cut of the F3 repair added two codes and only one could
    fire: `_validate_supplement_object` walks every row through
    `_validate_row`, which already refuses an extra key, and it ran
    BEFORE the explicit per-row loop - so the SPECIFIC code was dead, the
    same shadowing class as `production_day_universe_drift`. The order is
    now reversed, because a forbidden row field IS the blind-guarantee
    violation and deserves its own name rather than arriving wrapped in a
    generic 'object invalid'."""
    src = Path(sp.__file__).read_text(encoding="utf-8")
    body = src[src.index("def seal_supplement_production"):]
    assert body.index(chr(34) + "production_forbidden_row_field" + chr(34)) < \
        body.index("_ds._validate_supplement_object(rebuilt)"), (
        "the specific blind-guarantee check must run FIRST or it is dead")

    out = tmp_path / "seal"
    out.mkdir()
    for extra in ({"pnl": 1.0}, {"oracle_class": "TP"}, {"note": ""}):
        rows = tuple({**dict(r), **extra} for r in genuine.payload["rows"])
        tainted = {**dict(genuine.payload), "rows": rows,
                   "n_rows": len(rows),
                   "rows_digest": dss.canonical_rows_digest(rows)}
        forged = _forged_product(authority, prod, tainted)
        assert _seal_refusal(forged, out, authority=authority,
                             prepared=prod) == \
            "production_forbidden_row_field", extra
    assert sorted(p.name for p in out.iterdir()) == []


def _new_forged_authority(auth, **claim):
    """An exact-type `SupplementAuthority` that the minter never made."""
    forged = sa.SupplementAuthority.__new__(sa.SupplementAuthority)
    for f in dataclasses.fields(auth):
        object.__setattr__(forged, f.name,
                           claim.get(f.name, getattr(auth, f.name)))
    assert type(forged) is sa.SupplementAuthority
    return forged


def test_y_new_walks_around_the_capability_and_clears_all_of_b_derive(
        prod, authority, tmp_path):
    """FINDING, reported not repaired: `__new__` bypasses the minting
    capability, and a clone carrying only GENUINE facts passes the whole
    of `B_DERIVE`, builds a product and SEALS it.

    THIS clone buys nothing, because every field it carries is a
    genuine one. That is a fact about this clone, NOT a general
    property: round 4 built the same kind of clone with a lying day
    universe and it sealed rows dated 2099. See
    `test_r4_a_lying_day_universe_cannot_reach_the_seal`."""
    clone = _new_forged_authority(authority)
    assert clone is not authority
    assert sa.verify_supplement_authority(clone, prod) is clone

    ctx = _ctx(authority=clone, prepared=prod)
    assert run.run_stage_gates("B_DERIVE", ctx) is None, (
        "if this ever refuses, the factory boundary grew a check this "
        "finding says it lacks - delete the finding")

    rows = _rows(authority.expected_day_set)
    forged_product = sp.build_supplement_from_authority(clone, prod, rows)
    genuine_product = sp.build_supplement_from_authority(authority, prod,
                                                        rows)
    out = tmp_path / "seal"
    out.mkdir()
    action, sha = sp.seal_supplement_production(
        forged_product, out, authority=clone, prepared=prod,
        incident_id=INC)
    assert action.action == "promote"
    # the bytes are the factory's, fact for fact
    assert dss.canonical_supplement_bytes(forged_product.payload) == \
        dss.canonical_supplement_bytes(genuine_product.payload)
    assert sha == hashlib.sha256(
        dss.canonical_supplement_bytes(genuine_product.payload)).hexdigest()


FALSIFIED_FIELD_CODES = (
    ("supplement_id", OTHER_SID,
     "supplement_authority_supplement_id_mismatch"),
    ("method_version", "mc-freeze-v2",
     "supplement_authority_method_version_mismatch"),
    ("trial_id", "S0-T999", "supplement_authority_trial_mismatch"),
    ("authorized_commit", OTHER_COMMIT,
     "supplement_authority_commit_mismatch"),
    ("method_digest", "f" * 64,
     "supplement_authority_method_digest_mismatch"),
    ("source_artifact_id", "TEST_ONLY_SYNTHETIC",
     "supplement_authority_source_artifact_id_mismatch"),
    ("source_artifact_sha256", "1" * 64,
     "supplement_authority_source_artifact_sha256_mismatch"),
    ("bundle_table_digest", "2" * 64,
     "supplement_authority_bundle_table_mismatch"),
    ("source_input_sha256", "3" * 64,
     "supplement_authority_source_input_mismatch"),
    ("day_universe_digest", "4" * 64,
     "supplement_authority_day_universe_digest_mismatch"),
    ("day_universe", SUBSTITUTED_DAYS,
     "supplement_authority_day_universe_mismatch"),
    ("theta_channels", (PRIMARY,),
     "supplement_authority_theta_channels_mismatch"),
    ("n_days", 4, "supplement_authority_day_count_mismatch"),
    ("test_only", True, "supplement_authority_test_only_mismatch"),
    ("schema", "mc_supplement_authority.v2",
     "supplement_authority_schema"),
    ("authority_digest", "5" * 64,
     "supplement_authority_self_digest_mismatch"),
)


@pytest.mark.parametrize("field,value,code", FALSIFIED_FIELD_CODES,
                         ids=[f[0] for f in FALSIFIED_FIELD_CODES])
def test_y_every_falsified_fact_refuses_under_its_own_code(
        prod, authority, field, value, code):
    """One field at a time, on an authority the minter never made. Each
    lie has to surface under ITS OWN code - a collapsed
    'authority mismatch' would tell an operator nothing about which
    binding moved.

    The clone is asserted to verify FIRST, so the refusal is
    attributable to the single field that was changed."""
    assert sa.verify_supplement_authority(
        _new_forged_authority(authority), prod) is not None  # near-miss
    forged = _new_forged_authority(authority, **{field: value})
    assert getattr(forged, field) != getattr(authority, field)
    with pytest.raises(sa.SupplementError) as ei:
        sa.verify_supplement_authority(forged, prod)
    assert ei.value.code == code
    # ... and the same lie cannot reach the production builder
    with pytest.raises((sa.SupplementError, sp.SupplementProductionError)):
        sp.build_supplement_from_authority(
            forged, prod, _rows(authority.expected_day_set))


def test_y_a_subclass_instance_is_refused_by_the_typed_gate(prod,
                                                            authority):
    """F4, REPAIRED AND NOW PINNED.

    The type seam WAS inconsistent: the runner gates used `isinstance`
    while `verify_supplement_authority` used `type(...) is`, so a
    `__new__`-built SUBCLASS cleared the gate whose stated job is 'type,
    not shape' and died one gate later. `_require_real_authority` now
    demands the EXACT type at every B_DERIVE gate.

    F4b, ALSO REPAIRED: the first cut landed the exact-type rule in the
    runner but left `build_supplement_from_authority` on `isinstance`, so
    the subclass cleared the BUILDER's own guard and was stopped one layer
    down under an authority-layer code. One seam, one rule - the builder
    now refuses it under `production_authority_type`."""
    class _Sub(sa.SupplementAuthority):
        pass

    sub = _Sub.__new__(_Sub)
    for f in dataclasses.fields(authority):
        object.__setattr__(sub, f.name, getattr(authority, f.name))
    assert isinstance(sub, sa.SupplementAuthority)
    assert type(sub) is not sa.SupplementAuthority
    # the near-miss: every VALUE it carries is the genuine authority's
    for f in dataclasses.fields(authority):
        assert getattr(sub, f.name) == getattr(authority, f.name)

    ctx = _ctx(authority=sub, prepared=prod)
    for gate in sc.GATE_TABLE["B_DERIVE"]:
        _, msg = _gate_refusal(gate, ctx)
        assert "not exactly SupplementAuthority" in msg, gate
    assert _stage_refusal("B_DERIVE", ctx)[0] == \
        "gate_refused:custody_authority_production"

    with pytest.raises(sp.SupplementProductionError) as ei:
        sp.build_supplement_from_authority(
            sub, prod, _rows(authority.expected_day_set))
    assert ei.value.code == "production_authority_type", (
        "the builder still admits a subclass past its own isinstance "
        "check - this is the pinned residual, not a pass")


def test_y_an_authority_for_another_id_is_refused_at_build(prod, authority,
                                                           tmp_path):
    """F6, REPAIRED AND NOW PINNED.

    The hermetic core hardcodes `supplement_id = MC-DS-S001`, which need
    not be the id the authority was minted for. An authority for
    `MC-DS-S002` therefore USED TO produce a product whose PAYLOAD said
    S001 while its RECEIPT said S002 - and `verify_production_receipt`
    ACCEPTED it; only the seal noticed. One object may not carry two
    identities, and the builder now refuses to mint one.

    The seal's backstop is kept under test below, through a forged
    receipt, because a defence that is only ever exercised by the bug it
    was written for is not exercised at all."""
    auth2 = sa.derive_supplement_authority(prod, supplement_id=OTHER_SID)
    assert auth2.supplement_id == OTHER_SID
    assert sa.verify_supplement_authority(
        auth2, prod, supplement_id=OTHER_SID) is auth2       # near-miss
    assert sp.build_supplement_from_authority(
        authority, prod, _rows(authority.expected_day_set)) is not None

    with pytest.raises(sp.SupplementProductionError) as ei:
        sp.build_supplement_from_authority(
            auth2, prod, _rows(auth2.expected_day_set))
    assert ei.value.code == "production_supplement_id_divergence"
    assert repr(SID) in str(ei.value) and repr(OTHER_SID) in str(ei.value)

    # --- the seal is still the backstop, reached with a forged receipt --
    out = tmp_path / "seal"
    out.mkdir()
    day_set, binding = sa.supplement_build_inputs(auth2, prod,
                                                  supplement_id=OTHER_SID)
    two_identities = dss.build_day_strata_supplement_test_only(
        _rows(day_set), expected_day_set=day_set, binding=binding)
    assert two_identities["supplement_id"] == SID
    forged = _forged_product(auth2, prod, two_identities,
                             supplement_id=OTHER_SID)
    assert sp.verify_production_receipt(forged, auth2, prod) is \
        forged.receipt                                       # near-miss
    before = _listing(out)
    with pytest.raises(sa.SupplementError) as ei:
        sp.seal_supplement_production(forged, out, authority=auth2,
                                      prepared=prod, incident_id=INC)
    assert ei.value.code == "supplement_authority_supplement_id_mismatch"
    assert _listing(out) == before


def test_y_the_sealed_artifact_name_is_not_owned_by_the_production_seal(
        tmp_path):
    """FINDING: `supplement_runner.resolve_partial` is PUBLIC and takes
    raw bytes. It writes `DAY_STRATA_SUPPLEMENT.json` with no authority,
    no prepared input, no receipt and no validation of any kind.

    Not reachable in an authorized run today - nothing in this build is
    authorized to run, and reaching a governed root still needs the whole
    of A_PRECHECK plus a separate directory-creation authorization - but
    the claim 'the ONLY production path to a sealed supplement' is a
    property of the CALL GRAPH, not of the artifact name."""
    out = tmp_path / "unbound"
    out.mkdir()
    forged = b'{"forged":true}'
    action = run.resolve_partial(out, dss.SUPPLEMENT_FILENAME, forged,
                                 incident_id=INC)
    assert action.action == "promote"
    assert (out / dss.SUPPLEMENT_FILENAME).read_bytes() == forged
    assert _listing(out) == [dss.SUPPLEMENT_FILENAME]


# ===========================================================================
# Z. standing invariants of this battery
# ===========================================================================

def test_z_nothing_here_authorizes_anything():
    assert "NOT authorization" in \
        sp.SUPPLEMENT_PRODUCTION_IS_NOT_AUTHORIZATION or \
        "not permission" in sp.SUPPLEMENT_PRODUCTION_IS_NOT_AUTHORIZATION
    assert "ENGINEERING capability" in \
        sp.SUPPLEMENT_PRODUCTION_IS_NOT_AUTHORIZATION
    with pytest.raises(dss.SupplementNotAuthorized):
        dss.authorize_supplement("")


def test_z_nothing_in_this_battery_touched_a_governed_subtree():
    """The subtrees exist by Aaron's verbatim 2026-08-29 grant, and since
    2026-09-05 they hold a sealed supplement from the first authorized N09
    run. So neither ABSENCE nor EMPTINESS is the property any more -- both
    were proxies for "no battery wrote here", and both stopped being true
    for reasons that have nothing to do with this battery.

    The property compared against the snapshot taken at import survives
    whatever an authorized run legitimately leaves behind."""
    from _governed_subtrees import (
        assert_governed_subtrees_exist_under_the_grant,
        assert_governed_subtrees_untouched)
    assert_governed_subtrees_exist_under_the_grant(
        Path(__file__).resolve().parents[1])
    assert_governed_subtrees_untouched(_SUBTREES_AT_IMPORT, "this battery")


# ===========================================================================
# N06 round 2 — TOCTOU: check-and-serialize must read ONE frozen snapshot
# ===========================================================================


class _StatefulRows(tuple):
    """A rows view that changes AFTER the checks have read it.

    Not a mock of the defect — the defect is that the seal reads
    `payload["rows"]` more than once, so anything whose reads differ
    exposes it. `tuple` is subclassed so every isinstance/iteration the
    production code performs behaves normally.
    """


class _StatefulPayload(dict):
    """Outer mapping whose `rows` key flips after N reads.

    Reachable with NOTHING private: `SupplementProduct.__new__` plus
    `object.__setattr__` installs it past `__post_init__`'s
    `MappingProxyType(dict(...))` copy, and the type stays EXACT so the
    exact-type guard cannot see it.
    """

    def __init__(self, base, poisoned_rows, flip_after):
        super().__init__(base)
        self._poisoned = poisoned_rows
        self._flip_after = flip_after
        self.rows_reads = 0

    def _rows_view(self):
        self.rows_reads += 1
        if self.rows_reads > self._flip_after:
            return self._poisoned
        return super().__getitem__("rows")

    def __getitem__(self, key):
        if key == "rows":
            return self._rows_view()
        return super().__getitem__(key)

    def items(self):
        # The freeze reads through `items()`, not `__getitem__`, so a
        # mapping that only overrode the latter would never fire and the
        # test would pass for the wrong reason. Attack the real path.
        return [(k, self._rows_view() if k == "rows" else v)
                for k, v in super().items()]


def _capture_intended(monkeypatch):
    """Capture the bytes the seal WOULD write, without writing them.

    The governed roots are never touched: `resolve_partial` is replaced,
    so nothing reaches a filesystem the batteries are forbidden to write.
    """
    seen = {}

    def _fake(out_dir, filename, intended, *, incident_id):
        seen["intended"] = intended
        return sp._run.PartialAction("promote", detail="captured")

    monkeypatch.setattr(sp._run, "resolve_partial", _fake)
    return seen


def test_z_a_stateful_payload_can_never_seal_bytes_the_checks_never_saw(
        prod, authority, genuine, monkeypatch, tmp_path):
    """N06 ROUND 2, High — time-of-check vs time-of-use.

    Before the repair every check passed on ONE view of the rows while
    the canonical serialization read ANOTHER. Measured then:

        SEAL_RETURNED=YES
        ROWS_READS=4
        FORBIDDEN_PNL_SERIALIZED=True
        DECLARED_ROWS_DIGEST_MATCH=False

    The required post-repair behaviour is a DISJUNCTION, not a refusal:
    a stateful mapping must either be refused before anything is written,
    or produce a STABLE snapshot with no forbidden field whose declared
    `rows_digest` matches its own rows. Both branches are asserted here,
    and the flip point selects which one is exercised — proving the
    freeze takes a real view rather than always finding a clean one.
    """
    clean = tuple(dict(r) for r in genuine.payload["rows"])
    poisoned = _StatefulRows(dict(r, pnl=12.5) for r in clean)

    for flip_after, branch in ((3, "late"), (0, "immediate")):
        payload = _StatefulPayload(dict(genuine.payload), poisoned,
                                   flip_after=flip_after)
        product = sp.SupplementProduct.__new__(sp.SupplementProduct)
        object.__setattr__(product, "payload", payload)
        object.__setattr__(product, "receipt", genuine.receipt)
        # the exact-type guard cannot see this, which is the point
        assert type(product) is sp.SupplementProduct

        seen = _capture_intended(monkeypatch)
        out = tmp_path / f"seal_{branch}"
        out.mkdir()
        try:
            sp.seal_supplement_production(product, out, authority=authority,
                                          prepared=prod, incident_id=INC)
        except sp.SupplementProductionError as exc:
            # branch (a): refused, and NOTHING was serialized or written
            assert "intended" not in seen, (
                f"{branch}: bytes were serialized despite the refusal")
            assert _listing(out) == [], f"{branch}: the seal wrote something"
            assert exc.code in ("production_forbidden_row_field",
                                "production_receipt_mismatch",
                                "production_rows_digest_drift"), exc.code
            continue

        # branch (b): sealed — then the bytes must be the stable, clean view
        body = seen["intended"]
        assert b"pnl" not in body, (
            f"{branch}: the forbidden field reached the sealed bytes")
        payload_out = json.loads(body.decode("utf-8"))
        assert payload_out["rows_digest"] == \
            dss.canonical_rows_digest(payload_out["rows"]), (
            f"{branch}: the declared digest does not describe the sealed rows")


def test_z_the_freeze_takes_the_real_view_not_a_convenient_one(
        prod, authority, genuine, monkeypatch, tmp_path):
    """If the payload is poisoned from its FIRST read, the freeze must
    capture the poison and the blind guarantee must refuse it. Otherwise
    the previous test would pass for the wrong reason."""
    clean = tuple(dict(r) for r in genuine.payload["rows"])
    poisoned = _StatefulRows(dict(r, pnl=12.5) for r in clean)
    payload = _StatefulPayload(dict(genuine.payload), poisoned, flip_after=0)
    product = sp.SupplementProduct.__new__(sp.SupplementProduct)
    object.__setattr__(product, "payload", payload)
    object.__setattr__(product, "receipt", genuine.receipt)

    seen = _capture_intended(monkeypatch)
    out = tmp_path / "seal"
    out.mkdir()
    with pytest.raises(sp.SupplementProductionError) as ei:
        sp.seal_supplement_production(product, out, authority=authority,
                                      prepared=prod, incident_id=INC)
    assert ei.value.code in ("production_forbidden_row_field",
                             "production_receipt_mismatch")
    assert "intended" not in seen
    assert _listing(out) == []


def test_z_the_seal_reads_the_payload_exactly_once(prod, authority, genuine,
                                                   monkeypatch, tmp_path):
    """The structural fix, stated as a property rather than a diff: the
    caller's mapping is consumed ONCE, so no later read can differ from
    the one the checks used."""
    counter = _StatefulPayload(dict(genuine.payload),
                               genuine.payload["rows"], flip_after=10**6)
    product = sp.SupplementProduct.__new__(sp.SupplementProduct)
    object.__setattr__(product, "payload", counter)
    object.__setattr__(product, "receipt", genuine.receipt)

    _capture_intended(monkeypatch)
    out = tmp_path / "seal"
    out.mkdir()
    sp.seal_supplement_production(product, out, authority=authority,
                                  prepared=prod, incident_id=INC)
    assert counter.rows_reads <= 1, (
        f"the seal read the caller's rows {counter.rows_reads} times; every "
        "read past the first is a window for the value to change")


def test_z_a_stable_payload_still_seals_normally(prod, authority, genuine,
                                                 monkeypatch, tmp_path):
    """The freeze must not break the legitimate path."""
    seen = _capture_intended(monkeypatch)
    out = tmp_path / "seal"
    out.mkdir()
    action, sha = sp.seal_supplement_production(
        genuine, out, authority=authority, prepared=prod, incident_id=INC)
    assert action.action == "promote"
    assert len(sha) == 64
    assert b"pnl" not in seen["intended"]
    payload = json.loads(seen["intended"].decode("utf-8"))
    assert payload["rows_digest"] == dss.canonical_rows_digest(payload["rows"])


# ---------------------------------------------------------------------------
# N06 ROUND 3, High — a hostile scalar subclass inside the frozen snapshot,
# and the redesign that makes the declared payload non-load-bearing.
# ---------------------------------------------------------------------------

class _LyingStr(str):
    """Equal to everything it is compared with; serialises as itself.

    The exact object the round-3 reviewer used. `isinstance(v, str)` is
    True, so the old freeze returned it BY REFERENCE and every comparison
    downstream asked IT whether it matched."""

    def __eq__(self, other):
        return True

    def __ne__(self, other):
        return False

    __hash__ = str.__hash__


def _forged_exact(authority, prepared, payload):
    """A product and receipt of EXACT type, built without either __init__.

    Public API only: `__new__` plus `object.__setattr__`, and receipt
    components that are public arithmetic (F1/F2)."""
    product = sp.SupplementProduct.__new__(sp.SupplementProduct)
    object.__setattr__(product, "payload", payload)
    object.__setattr__(product, "receipt",
                       _forged_receipt(authority, prepared, payload))
    assert type(product) is sp.SupplementProduct
    return product


def test_r3_a_lying_digest_subclass_cannot_seal_bytes(
        prod, authority, genuine, monkeypatch, tmp_path):
    """MEASURED BEFORE THE REPAIR, on 2a7374f:

        SEAL_RETURNED=True
        DECLARED_ROWS_DIGEST=0000...0000  (64 zeros)
        ACTUAL_ROWS_DIGEST=792d1297a4c08a039472504298ebce7bf9db2a4241b98e
                           8eeb0b6f730863dd8f
        DECLARED_MATCH=False

    The seal RETURNED and the bytes it staged declared a digest that
    described nothing. Two things now stop it: the freeze refuses a
    subclass outright, and even if one got through, the bytes written are
    rebuilt by the seal rather than taken from the caller."""
    payload = dict(genuine.payload)
    payload["rows"] = tuple(dict(r) for r in genuine.payload["rows"])
    payload["rows_digest"] = _LyingStr("0" * 64)

    seen = _capture_intended(monkeypatch)
    out = tmp_path / "seal"
    out.mkdir()
    with pytest.raises(sp.SupplementProductionError) as ei:
        sp.seal_supplement_production(
            _forged_exact(authority, prod, payload), out,
            authority=authority, prepared=prod, incident_id=INC)
    assert ei.value.code == "production_payload_unsupported_type"
    assert "_LyingStr" in str(ei.value)
    assert "intended" not in seen, "bytes were staged despite the refusal"
    assert _listing(out) == []


@pytest.mark.parametrize("field", ["vol_stratum", "event_stratum",
                                   "trade_date"])
def test_r3_a_lying_scalar_inside_a_row_cannot_seal_bytes(
        prod, authority, genuine, monkeypatch, tmp_path, field):
    """The same subclass one layer down. `_validate_row` returns
    `trade_date` BY REFERENCE and runs `str()` over the two strata, so a
    hostile value there would clear the vocabulary check by `__eq__` and
    then be re-encoded by the attacker's own `__str__`."""
    rows = tuple(dict(r) for r in genuine.payload["rows"])
    for row in rows:
        row[field] = _LyingStr(row[field])
    payload = dict(genuine.payload)
    payload["rows"] = rows

    seen = _capture_intended(monkeypatch)
    out = tmp_path / "seal"
    out.mkdir()
    with pytest.raises(sp.SupplementProductionError) as ei:
        sp.seal_supplement_production(
            _forged_exact(authority, prod, payload), out,
            authority=authority, prepared=prod, incident_id=INC)
    assert ei.value.code == "production_payload_unsupported_type"
    assert "intended" not in seen
    assert _listing(out) == []


def test_r3_a_subclass_KEY_cannot_seal_bytes(
        prod, authority, genuine, monkeypatch, tmp_path):
    """Keys were normalised with `str(k)` — which calls a key subclass's
    own `__str__`. Refused by exact type instead, so no attacker method
    is ever invoked during the freeze."""
    payload = {_LyingStr(k) if k == "n_rows" else k: v
               for k, v in dict(genuine.payload).items()}
    # The receipt is minted over the CLEAN payload: a lying key breaks
    # `json.dumps(sort_keys=True)` in the receipt helper itself, and the
    # freeze runs before receipt verification anyway, so the refusal must
    # not depend on the receipt matching.
    product = sp.SupplementProduct.__new__(sp.SupplementProduct)
    object.__setattr__(product, "payload", payload)
    object.__setattr__(product, "receipt",
                       _forged_receipt(authority, prod,
                                       dict(genuine.payload)))

    seen = _capture_intended(monkeypatch)
    out = tmp_path / "seal"
    out.mkdir()
    with pytest.raises(sp.SupplementProductionError) as ei:
        sp.seal_supplement_production(
            product, out, authority=authority, prepared=prod,
            incident_id=INC)
    assert ei.value.code == "production_payload_unsupported_type"
    assert "not exactly str" in str(ei.value)
    assert "intended" not in seen


def test_r3_the_seal_serialises_what_it_rebuilt_not_what_was_declared(
        prod, authority, genuine, monkeypatch, tmp_path):
    """The structural property behind the round-3 redesign.

    Three rounds found one shape: a caller-supplied value taking part in
    a comparison that decided whether to write. The category closes only
    when the DECLARATION stops being load-bearing — so the bytes staged
    must equal an independent rebuild from the authority and the rows,
    computed here without touching the production module."""
    seen = _capture_intended(monkeypatch)
    out = tmp_path / "seal"
    out.mkdir()
    sp.seal_supplement_production(genuine, out, authority=authority,
                                  prepared=prod, incident_id=INC)

    expected_days, binding = sa.supplement_build_inputs(
        authority, prod, supplement_id=authority.supplement_id)
    independent = dss.build_day_strata_supplement_test_only(
        [dict(r) for r in genuine.payload["rows"]],
        expected_day_set=expected_days, binding=binding)
    assert seen["intended"] == dss.canonical_supplement_bytes(independent)


def test_r3_the_written_object_is_the_rebuilt_one(prod):
    """Guard the rename itself: `canonical_supplement_bytes` must be
    handed the REBUILT object. Serialising `declared` again would restore
    the whole round-3 attack surface while every other test still passed."""
    src = Path(sp.__file__).read_text(encoding="utf-8")
    body = src[src.index("def seal_supplement_production"):]
    assert "canonical_supplement_bytes(rebuilt)" in body
    assert "canonical_supplement_bytes(declared)" not in body
    assert "canonical_supplement_bytes(payload)" not in body


def test_r3b_the_builder_refuses_a_hostile_scalar_too(prod, authority):
    """N06 ROUND 3, second instance — builder side, found by probing.

    `_validate_row` checks the ruled vocabularies with `in` and then
    re-encodes with `str()`. A subclass that lies in `__eq__` cleared the
    check and was written as whatever `__str__` returned. Measured on the
    tree that had already repaired the SEAL:

        BUILT_VOL='2099-12-31'   IN_VOCAB=False

    The seal caught it (`production_rebuild_refused`) because it rebuilds,
    so nothing could ever be written -- but a builder that produces what
    the seal must reject is two implementations of one rule, which is
    exactly what caused rounds 2 and 3."""
    class _Lying(str):
        def __eq__(self, other):
            return True

        def __ne__(self, other):
            return False

        def __str__(self):
            return "2099-12-31"

        __hash__ = str.__hash__

    rows = [dict(r) for r in _rows(authority.expected_day_set)]
    rows[0]["vol_stratum"] = _Lying(rows[0]["vol_stratum"])
    with pytest.raises(sp.SupplementProductionError) as ei:
        sp.build_supplement_from_authority(authority, prod, rows)
    assert ei.value.code == "production_payload_unsupported_type"
    assert "_Lying" in str(ei.value)


def test_r4_a_lying_day_universe_cannot_reach_the_seal(
        prod, authority, monkeypatch, tmp_path):
    """N06 ROUND 4, High — the poison is in the AUTHORITY, not the rows.

    Every comparison in `verify_supplement_authority` asks the authority's
    own values whether they match, and a `str` subclass with a lying
    `__eq__` answers yes to all of them. The rows stay plain strings, so
    the builder's normalisation never sees anything wrong. Measured before
    the repair, on 8b16118:

        VERIFY_RETURNED=True   BUILDER_RETURNED=True   SEAL_RETURNED=True
        SEALED_DAYS=2099-01-03..2099-01-07
        BOUND_DIGEST=49352d441d195b69cae265ec...   (the real 2026 universe)
        ACTUAL_DIGEST=435fd9b45e515710e96acf6e...  (the 2099 rows)
        BOUND_DIGEST_MATCH=False

    i.e. sealed bytes whose binding describes a different day universe
    than their own rows."""
    class _LyingDate(str):
        def __eq__(self, other):
            return True

        def __ne__(self, other):
            return False

        __hash__ = str.__hash__

    bad = tuple(_LyingDate(f"2099-01-{d:02d}") for d in range(3, 8))
    forged = sa.SupplementAuthority.__new__(sa.SupplementAuthority)
    for field in dataclasses.fields(authority):
        value = bad if field.name == "day_universe" else getattr(
            authority, field.name)
        object.__setattr__(forged, field.name, value)
    object.__setattr__(forged, "authority_digest",
                       sa._digest(sa.AUTHORITY_DIGEST_SCHEMA,
                                  sa._authority_payload(forged)))
    assert type(forged) is sa.SupplementAuthority     # the guard cannot see it

    with pytest.raises(dss.SupplementError) as ei:
        sa.verify_supplement_authority(forged, prod)
    assert ei.value.code == "supplement_authority_day_universe_type"

    # and nothing downstream can be reached with it
    plain = tuple(str.__str__(d) for d in bad)
    seen = _capture_intended(monkeypatch)
    out = tmp_path / "seal"
    out.mkdir()
    with pytest.raises((dss.SupplementError, sp.SupplementProductionError)):
        sp.build_supplement_from_authority(forged, prod, _rows(plain))
    assert "intended" not in seen
    assert _listing(out) == []


def test_r4_a_day_universe_digest_must_describe_its_own_universe(
        prod, authority):
    """The second half of the same repair: the verifier used to check only
    that the authority's OVERALL self-digest was consistent, which a forger
    simply recomputes. The day-universe digest is now re-derived from the
    universe the authority actually carries."""
    forged = sa.SupplementAuthority.__new__(sa.SupplementAuthority)
    for field in dataclasses.fields(authority):
        object.__setattr__(forged, field.name, getattr(authority, field.name))
    object.__setattr__(forged, "day_universe",
                       tuple(f"2099-01-{d:02d}" for d in range(3, 8)))
    object.__setattr__(forged, "authority_digest",
                       sa._digest(sa.AUTHORITY_DIGEST_SCHEMA,
                                  sa._authority_payload(forged)))
    with pytest.raises(dss.SupplementError) as ei:
        sa.verify_supplement_authority(forged, prod)
    assert ei.value.code in ("supplement_authority_day_universe_mismatch",
                             "supplement_authority_day_universe_digest_unbacked")


# ===========================================================================
# S — the two commits are DIFFERENT things (Aaron's ruling, 2026-09-05)
# ===========================================================================
#
# SOURCE / CUSTODY commit     the commit that produced and sealed the S0
#                             bundle this supplement consumes
# SUPPLEMENT EXECUTION commit the framework HEAD the live P2 authorizes
#                             this run at
#
# They are allowed and EXPECTED to differ: the supplement necessarily runs
# at a later commit than the trial whose output it reads, and the N09 path
# did not exist at the S0 commit at all. `custody_authority_binding` used to
# require `authority.authorized_commit == live_P2.authorized_commit == HEAD`
# and the first run ever to reach B_DERIVE refused on it -- measured,
# 876c1b74131b (S0-T001) vs af297eaa0987 (that day's HEAD).
#
# EVERY FIXTURE ABOVE USES ONE COMMIT FOR BOTH, which is why none of them
# could witness the confusion. These use two.

EXEC_COMMIT = "e" * 40                      # NOT the bundle's COMMIT


def test_s1_source_and_execution_commits_may_differ(prod, authority):
    """Case 1: each side correct, the two commits different -> PASS."""
    assert authority.authorized_commit == COMMIT          # source
    assert EXEC_COMMIT != COMMIT                          # execution
    ctx = _ctx(authority=authority, prepared=prod,
               head_commit=EXEC_COMMIT,
               chain=FakeChain(live_authorizations=(
                   FakeP2(authorized_commit=EXEC_COMMIT),)))
    run.GATES["custody_authority_binding"](ctx)           # must not raise


def test_s2_the_whole_B_DERIVE_stage_passes_with_two_commits(prod, authority):
    """Not just the one gate: the stage the gate belongs to."""
    ctx = _ctx(authority=authority, prepared=prod,
               head_commit=EXEC_COMMIT,
               chain=FakeChain(live_authorizations=(
                   FakeP2(authorized_commit=EXEC_COMMIT),)))
    run.run_stage_gates("B_DERIVE", ctx)                  # must not raise


def test_s3_a_source_commit_that_is_not_the_bundles_still_refuses(
        prod, authority):
    """Case 2, and the one that proves the repair is a re-aim rather than a
    removal: with the EXECUTION commit correct on both sides, a SOURCE
    commit that does not match the sealed bundle still refuses."""
    forged = _forged_prepared(prod, authorized_commit=OTHER_COMMIT)
    _, msg = _gate_refusal(
        "custody_authority_binding",
        _ctx(authority=authority, prepared=forged,
             head_commit=EXEC_COMMIT,
             chain=FakeChain(live_authorizations=(
                 FakeP2(authorized_commit=EXEC_COMMIT),))))
    assert "supplement_authority_commit_mismatch" in msg


def test_s4_the_execution_side_is_still_guarded_by_A_PRECHECK(prod, authority):
    """Case 3. Moving the check off B_DERIVE did not leave the execution
    commit unbound -- A_PRECHECK owns it, and still refuses."""
    ctx = _ctx(authority=authority, prepared=prod,
               head_commit=EXEC_COMMIT,
               chain=FakeChain(live_authorizations=(
                   FakeP2(authorized_commit=COMMIT),)))   # P2 != HEAD
    _, msg = _gate_refusal("authorized_commit_matches_head", ctx)
    assert "HEAD" in msg


def test_s5_it_cannot_go_green_by_dropping_the_custody_check(prod, authority):
    """Case 4. The repair moved WHICH commit is compared; it did not delete
    the custody binding. Asserted two ways, because the structural half
    alone would pass over a call that had been neutered."""
    import inspect
    body = inspect.getsource(run._g_custody_authority_binding)
    assert "verify_supplement_authority" in body
    assert "_require_real_authority" in body
    # and behaviourally: a type-mirror of a real authority is still refused
    mirror = dataclasses.make_dataclass(
        "MirrorAuthority",
        [(f.name, object) for f in dataclasses.fields(authority)],
        frozen=True)(**{f.name: getattr(authority, f.name)
                        for f in dataclasses.fields(authority)})
    _gate_refusal("custody_authority_binding",
                  _ctx(authority=mirror, prepared=prod,
                       head_commit=EXEC_COMMIT,
                       chain=FakeChain(live_authorizations=(
                           FakeP2(authorized_commit=EXEC_COMMIT),))))
