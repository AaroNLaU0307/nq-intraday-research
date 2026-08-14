"""DR-5 MC consumer R2.1 battery — typed custody authority + calendar
identity (lane S2; synthetic fixtures ONLY, plus ONE read-only parse of
the real blind attestation).

Scope (R2.1 contract, written against the parallel consumer.py build):

  PHASE A — ``mcc.CustodyAuthority``: the external custody authority
    (R2 PHASE C) becomes a TYPED frozen object bound to its SOURCE
    document — the S0-T001 blind post-run attestation
    ``ops/S0_T001_POST_RUN_ATTESTATION.md``. That document records
    custody facts only (paths/bytes/sha256; ZERO research values —
    RESULT_VALUES_VIEWED=NO), so parsing it here is blind-safe and
    read-only. A ``test_only`` flag separates synthetic authorities from
    the real one: the PRODUCTION entry ``prepare_mc_input`` refuses
    ``test_only=True`` outright, the TEST_ONLY entry
    ``prepare_mc_input_for_tests`` accepts it.

  PHASE B — ``prepared_digest`` binds FULL calendar content (day_ids,
    cal_offsets, first_month_offsets) and full day-sequence content, not
    just lengths; the injected calendar is copied/tuple-ized on prepare
    and its parameter is renamed ``test_only_calendar`` (TEST_ONLY entry
    only — production builds the frozen MC SS4.1 window itself).

Every bundle fixture is hand-built bytes (self-contained copy of the R2
synthetic bundle builder; deliberately NOT imported from
test_mc_consumer.py) — no sealed S0 value is read anywhere."""
from __future__ import annotations

import dataclasses
import hashlib
import inspect
import json
import re
from pathlib import Path

import pytest

from conftest import make_trade_path
from itsf.contracts import RESEARCH_BOOTSTRAP_SEEDS
from itsf.mc import consumer as mcc
from itsf.mc.orchestrator import TemplateDay

REPO = Path(__file__).resolve().parents[1]
ATTESTATION_REL = "ops/S0_T001_POST_RUN_ATTESTATION.md"
ATTESTATION_PATH = REPO / "ops" / "S0_T001_POST_RUN_ATTESTATION.md"

TRIAL = "S0-T001"
COMMIT = "876c1b74131b4ab1a89dce433ecce646ba481f8c"
TP_DAYS = ("2026-08-03", "2026-08-05", "2026-08-07")
FP_DAYS = ("2026-08-04", "2026-08-06")
ALL_DAYS = tuple(sorted(TP_DAYS + FP_DAYS))
PRIMARY = mcc.PRIMARY_THETA_CHANNEL          # 'theta_0.5'
SECONDARY = mcc.SECONDARY_THETA_CHANNEL      # 'theta_0.3'

# one attestation-table row: | <name> | <bytes> | <64-hex sha256> |
_ATT_ROW = re.compile(
    r"^\|\s*([A-Za-z0-9_.]+)\s*\|\s*(\d+)\s*\|\s*([0-9a-f]{64})\s*\|",
    re.MULTILINE)


# --- self-contained synthetic bundle (R2 builder pattern) -------------------

def _record_row(date: str, engine: str, scn: str, pnl: float) -> dict:
    rec = make_trade_path([pnl / 2, pnl], date=date, engine=engine,
                          final=pnl)
    row = dataclasses.asdict(rec)
    row["cost_scenario"] = scn
    return row


def _refresh_manifest(bundle):
    names = [n for n in sorted(bundle) if n != "manifest.jsonl"]
    bundle["manifest.jsonl"] = "\n".join(
        json.dumps({"record_type": "file", "relative_path": n,
                    "file_sha256": hashlib.sha256(bundle[n]).hexdigest()},
                   sort_keys=True) for n in names).encode("utf-8")


def _bundle(*, pnl: float = 80.0, tp_days: tuple = TP_DAYS,
            fp_days: tuple = FP_DAYS) -> dict[str, bytes]:
    all_days = tuple(sorted(tp_days + fp_days))
    files: dict[str, bytes] = {}
    counts: dict = {}
    for e in mcc.ENGINES:
        counts[e] = {}
        for s in mcc.SCENARIOS:
            rows = [_record_row(d, e, s, pnl) for d in all_days]
            files[f"MC_HANDOFF_{e}_{s}.jsonl"] = "\n".join(
                json.dumps(r, sort_keys=True) for r in rows).encode("utf-8")
            counts[e][s] = {"n_records": len(rows)}
    report = {
        "governance": {"trial_id": TRIAL, "authorized_commit": COMMIT},
        "oracle_daily": {
            PRIMARY: {"day_universe": {
                "tp_days": list(tp_days), "fp_days": list(fp_days)}},
            # secondary channel: superset TP (theta_0.3 selects more days)
            SECONDARY: {"day_universe": {
                "tp_days": sorted(tp_days + (fp_days[0],)),
                "fp_days": [fp_days[1]]}},
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
    _refresh_manifest(files)
    return files


def _snapshot() -> dict:
    return {"trial_id": TRIAL, "authorized_commit": COMMIT,
            "event_sequence": 15}


def _calendar(n_days: int = 8, *, prefix: str = "T", offset_step: int = 1,
              offsets: tuple = (0, 1)) -> mcc.TemplateCalendar:
    days = tuple(TemplateDay(day_id=f"{prefix}{i:03d}",
                             cal_offset=i * offset_step)
                 for i in range(n_days))
    return mcc.TemplateCalendar(days=days,
                                first_month_offsets=tuple(offsets))


def _authority(bundle, **overrides):
    """TEST_ONLY typed authority (test_only=True) with digests computed
    from the bundle AS GIVEN; field overrides via dataclasses.replace.
    integration point: main agent aligns this call."""
    auth = mcc.CustodyAuthority.for_tests(bundle)
    return dataclasses.replace(auth, **overrides) if overrides else auth


def _prepare(bundle=None, authority=None, calendar=None):
    """TEST_ONLY prepare entry. Authority derived from the bundle AS
    GIVEN unless a (pre-tamper) authority is passed explicitly.
    integration point: main agent aligns this call."""
    b = bundle if bundle is not None else _bundle()
    return mcc.prepare_mc_input_for_tests(
        b, authorization_snapshot=_snapshot(),
        custody_authority=authority if authority is not None
        else _authority(b),
        test_only_calendar=calendar if calendar is not None
        else _calendar())


# --- R2.1 PHASE A: typed custody authority ----------------------------------

def test_load_custody_authority_from_real_attestation():
    """The loader parses the REAL blind attestation (read-only custody
    metadata, zero research values) into a production CustodyAuthority:
    S0-T001 identity, EXACTLY the 14 sealed digests of the attestation's
    markdown table, and a source pin equal to the sha256 of the
    attestation bytes themselves — the authority is bound to the
    document it came from, not merely to a floating digest map."""
    raw = ATTESTATION_PATH.read_bytes()
    table = {m.group(1): m.group(3)
             for m in _ATT_ROW.finditer(raw.decode("utf-8"))}
    assert len(table) == 14                    # independent parse
    auth = mcc.load_custody_authority_from_attestation()
    assert isinstance(auth, mcc.CustodyAuthority)
    assert auth.test_only is False
    assert auth.trial_id == TRIAL
    assert auth.authorized_commit == COMMIT
    assert auth.source_artifact_id == ATTESTATION_REL
    assert auth.source_artifact_sha256 == hashlib.sha256(raw).hexdigest()
    assert auth.source_artifact_sha256 == mcc.ATTESTATION_SHA256_PINNED
    assert dict(auth.file_sha256) == table
    assert set(auth.file_sha256) == set(mcc.BUNDLE_EXACT_SET)
    # spot-pins copied verbatim from the attestation table (guards the
    # independent parser itself against a silently-empty regex)
    assert auth.file_sha256["manifest.jsonl"] == (
        "4158696fd9fb4cda9cae7f04351e4f02e83f532e42b5fbaa953e4fcee53fa04c")
    assert auth.file_sha256["S0_REPORT.json"] == (
        "8b2db7dbb0f678a0c4ed4071303478c26ea5e23fa0db591719e646ba648a90e9")
    with pytest.raises(dataclasses.FrozenInstanceError):
        auth.trial_id = "X"                    # type: ignore


def test_no_caller_built_authority_crosses_either_entry():
    """R2.2 custody rooting: the PRODUCTION entry accepts NO authority
    object at all — its signature takes raw `attestation_bytes` and the
    authority is constructed internally against the code-pinned source.
    Symmetrically, the TEST entry refuses a hand-built test_only=False
    object, so non-test authorities exist ONLY via the internal
    attestation constructor."""
    sig_prod = inspect.signature(mcc.prepare_mc_input)
    assert "attestation_bytes" in sig_prod.parameters
    assert "custody_authority" not in sig_prod.parameters
    b = _bundle()
    prod_like = dataclasses.replace(mcc.CustodyAuthority.for_tests(b),
                                    test_only=False)
    with pytest.raises(
            mcc.MCInputError,
            match="custody_authority_production_object_in_test_entry"):
        _prepare(b, authority=prod_like)


def test_attestation_source_pins_refuse_tamper_and_wrong_path():
    """R2.2 PHASE E: the internal authority constructor is rooted TWICE
    in code — tampered attestation bytes fail the pinned document
    digest, and any source id other than the approved attestation path
    is refused before bytes are even read."""
    raw = ATTESTATION_PATH.read_bytes()
    with pytest.raises(mcc.MCInputError,
                       match="custody_authority_source_digest_mismatch"):
        mcc.load_custody_authority_from_attestation(
            attestation_bytes=b"x" + raw)
    with pytest.raises(mcc.MCInputError,
                       match="custody_authority_source_violation"):
        mcc.load_custody_authority_from_attestation(
            path="ops/SOME_OTHER_DOC.md")


def test_test_only_entry_accepts_test_authority():
    """The TEST_ONLY entry accepts a for_tests authority and yields the
    same prepared shape as R2 (positive control for this battery)."""
    assert _authority(_bundle()).test_only is True
    prepared = _prepare()
    assert prepared.trial_id == TRIAL
    assert prepared.day_sequences[PRIMARY] == ALL_DAYS
    assert set(prepared.file_sha256) == set(mcc.BUNDLE_EXACT_SET)


def test_authority_binding_violation_refused():
    """Authority identity must agree with the bundle's sealed
    REGISTRY_AFTER_RUN_STARTED snapshot on BOTH trial_id and
    authorized_commit — a digest map lifted from some other trial's
    attestation cannot certify this bundle."""
    b = _bundle()
    with pytest.raises(mcc.MCInputError,
                       match="custody_authority_binding_violation"):
        _prepare(b, authority=_authority(b, trial_id="S0-T999"))
    b2 = _bundle()
    with pytest.raises(mcc.MCInputError,
                       match="custody_authority_binding_violation"):
        _prepare(b2, authority=_authority(b2, authorized_commit="f" * 40))


def test_authority_keyset_violation_refused():
    """file_sha256 key set must equal the 14-name bundle exact-set
    INCLUDING manifest.jsonl — missing AND extra both refuse."""
    b = _bundle()
    auth = _authority(b)
    missing = dict(auth.file_sha256)
    del missing["S0_REPORT.md"]
    with pytest.raises(mcc.MCInputError,
                       match="custody_authority_keyset_violation"):
        _prepare(b, authority=dataclasses.replace(
            auth, file_sha256=missing))
    extra = dict(auth.file_sha256)
    extra["EXTRA.json"] = "0" * 64
    with pytest.raises(mcc.MCInputError,
                       match="custody_authority_keyset_violation"):
        _prepare(b, authority=dataclasses.replace(auth, file_sha256=extra))


def test_payload_plus_manifest_rewrite_fails_typed_authority():
    """THE attack the external authority exists for (R2 PHASE C, carried
    into the typed form): payload AND internal manifest rewritten
    consistently — internal dual-pin agrees, the pre-tamper typed
    authority still refuses on recomputed bundle bytes."""
    b = _bundle()
    auth = _authority(b)                       # custody BEFORE tamper
    b["S0_REPORT.md"] = b"# attacker rewrote and re-manifested"
    _refresh_manifest(b)                       # internal pins now agree
    with pytest.raises(mcc.MCInputError, match="bundle_hash_mismatch"):
        _prepare(b, authority=auth)


def test_authority_single_wrong_digest_refused():
    """ANY single digest disagreeing with recomputed bundle bytes
    refuses — well-formed but wrong is a mismatch, not a malform."""
    b = _bundle()
    auth = _authority(b)
    wrong = dict(auth.file_sha256)
    wrong["SEED_MANIFEST.json"] = "0" * 64     # valid hex, wrong bytes
    with pytest.raises(mcc.MCInputError, match="bundle_hash_mismatch"):
        _prepare(b, authority=dataclasses.replace(auth, file_sha256=wrong))


def test_authority_malformed_digest_refused():
    """A digest that is None or not 64-hex is a malformed AUTHORITY, not
    a byte mismatch — refused with its own reason code."""
    b = _bundle()
    auth = _authority(b)
    for bad in (None, "zz" * 32, "abc"):
        digests = dict(auth.file_sha256)
        digests["manifest.jsonl"] = bad
        with pytest.raises(mcc.MCInputError,
                           match="custody_authority_malformed"):
            _prepare(b, authority=dataclasses.replace(
                auth, file_sha256=digests))


# --- R2.1 PHASE B: calendar identity + deep immutability --------------------

def test_prepared_digest_binds_calendar_day_ids():
    """Two calendars of the SAME length whose day_ids differ must yield
    different prepared digests (a length-only digest would collide);
    identical inputs must reproduce the identical digest (determinism
    control, so the inequality below cannot pass by noise)."""
    d_a = mcc.prepared_digest(_prepare(calendar=_calendar()))
    d_a2 = mcc.prepared_digest(_prepare(calendar=_calendar()))
    d_b = mcc.prepared_digest(_prepare(calendar=_calendar(prefix="U")))
    assert d_a == d_a2
    assert d_a != d_b


def test_prepared_digest_binds_cal_offsets():
    """Same day_ids, different cal_offsets -> different digests: the
    30-day billing arithmetic runs on cal_offset (MC SS4.1), so offset
    content is identity-bearing."""
    d_a = mcc.prepared_digest(_prepare(calendar=_calendar(offset_step=1)))
    d_b = mcc.prepared_digest(_prepare(calendar=_calendar(offset_step=2)))
    assert d_a != d_b


def test_prepared_digest_binds_first_month_offsets():
    """Same days, same offset COUNT, different start-phase members
    (MC SS5 inner source 1) -> different digests."""
    d_a = mcc.prepared_digest(_prepare(calendar=_calendar(offsets=(0, 1))))
    d_b = mcc.prepared_digest(_prepare(calendar=_calendar(offsets=(0, 2))))
    assert d_a != d_b


def test_prepared_digest_binds_day_sequence_content():
    """Two bundles identical except ONE date string in the theta_0.5 day
    universe (and its records): every channel length is unchanged, so a
    per-channel-length digest would collide — the full-content digest
    must not."""
    d_a = mcc.prepared_digest(_prepare(_bundle()))
    d_b = mcc.prepared_digest(_prepare(_bundle(
        tp_days=("2026-08-03", "2026-08-05", "2026-08-08"))))
    assert d_a != d_b


def test_injected_calendar_is_copied_and_immune_to_caller_mutation():
    """R2 PHASE F deep immutability extended to the injected calendar:
    prepare copies/tuple-izes it, so post-prepare mutation of every
    structure the CALLER still holds changes neither prepared.calendar
    nor the prepared digest."""
    day_list = [TemplateDay(day_id=f"T{i:03d}", cal_offset=i)
                for i in range(8)]
    offset_list = [0, 1]
    try:                                       # list-built if permitted
        cal = mcc.TemplateCalendar(days=day_list,
                                   first_month_offsets=offset_list)
    except Exception:                          # tuple-only construction —
        cal = mcc.TemplateCalendar(            # mutate the source lists
            days=tuple(day_list),
            first_month_offsets=tuple(offset_list))
    prepared = _prepare(calendar=cal)
    d0 = mcc.prepared_digest(prepared)
    ids0 = tuple(d.day_id for d in prepared.calendar.days)
    # the caller now mutates everything it still holds
    day_list[0] = TemplateDay(day_id="9999-99-99", cal_offset=999)
    day_list.append(TemplateDay(day_id="9999-99-98", cal_offset=998))
    offset_list.append(99)
    assert isinstance(prepared.calendar.days, tuple)
    assert isinstance(prepared.calendar.first_month_offsets, tuple)
    assert tuple(d.day_id for d in prepared.calendar.days) == ids0
    assert len(prepared.calendar.days) == 8
    assert prepared.calendar.first_month_offsets == (0, 1)
    assert mcc.prepared_digest(prepared) == d0


def test_injected_calendar_parameter_is_test_only_named():
    """The injection surface is EXPLICITLY test-scoped: the TEST_ONLY
    entry takes `test_only_calendar` (the R2 `calendar` name is gone);
    the PRODUCTION entry has no calendar-injection parameter at all —
    with the parameter absent it can only build the frozen MC SS4.1
    window itself."""
    sig_tests = inspect.signature(mcc.prepare_mc_input_for_tests)
    assert "test_only_calendar" in sig_tests.parameters
    assert "calendar" not in sig_tests.parameters
    sig_prod = inspect.signature(mcc.prepare_mc_input)
    assert "test_only_calendar" not in sig_prod.parameters
    assert "calendar" not in sig_prod.parameters


def test_production_calendar_is_the_frozen_window():
    """MC SS4.1 frozen window sanity for the calendar production builds
    when nothing is injected (the ONE permitted build_template_calendar
    call in this battery): first trading day at the frozen 2026-08
    template origin, ~24 months of CME days, ~21 first-month start
    phases."""
    cal = mcc.build_template_calendar()
    assert isinstance(cal.days, tuple)
    first = cal.days[0].day_id
    assert "2026-08-01" <= first <= "2026-08-05"
    assert 460 <= len(cal.days) <= 540
    assert 19 <= len(cal.first_month_offsets) <= 23
