"""N01 lane S1' — identity / replay / numeric boundary repairs.

Synthetic fixtures ONLY. Nothing here reads real data, real results, or
any repository artifact beyond the already-frozen constant tables.

Coverage map:
  C1. RECORDS CUSTODY — the prepared identity binds the parsed records,
      the cold replay re-parses them from custody-checked raw bytes, and
      the four-link chain (raw bytes -> parsed digest -> prepared
      identity -> the mapping the lifecycle reads) is verified on every
      execution. Six named regressions, one per attack shape, plus the
      positive that guards against over-tightening.
  C6. DAY-UNIVERSE ENGINEERING EQUALITY — per θ, tp ∪ fp == the record
      day set, in BOTH directions, and one population across θ.
  C4. the lane-S2' authoritative fact-verification wiring.

BASELINE COUNTEREXAMPLE (measured on the R2.3 code, reproduced verbatim
in `test_c1_identity_copy_records_swap_attack_is_dead`): a hand-built
`PreparedMCInput` that copied every identity field and swapped only the
`records` mapping produced a BIT-IDENTICAL `prepared_digest`, and the
forged trace passed the cold replay all green
(`key_set_equal=True, mismatches=0`) because the replay was handed the
same live object.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import pathlib

import pytest

from conftest import make_trade_path
from itsf.contracts import RESEARCH_BOOTSTRAP_SEEDS
from itsf.mc import atoms as A
from itsf.mc import consumer as mcc
from itsf.mc import orchestrator as orch
from itsf.mc.orchestrator import TemplateDay
from itsf.s0.report import record_to_formal_dict

REPO = pathlib.Path(__file__).resolve().parents[1]
TRIAL = "S0-T001"
COMMIT = "876c1b74131b4ab1a89dce433ecce646ba481f8c"
TP_DAYS = ("2026-08-03", "2026-08-05", "2026-08-07")
FP_DAYS = ("2026-08-04", "2026-08-06")
ALL_DAYS = tuple(sorted(TP_DAYS + FP_DAYS))
PRIMARY = mcc.PRIMARY_THETA_CHANNEL
SECONDARY = mcc.SECONDARY_THETA_CHANNEL


# --- synthetic bundle ------------------------------------------------------

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


def _refresh_manifest(bundle):
    names = [n for n in sorted(bundle) if n != "manifest.jsonl"]
    bundle["manifest.jsonl"] = "\n".join(
        json.dumps({"record_type": "file", "relative_path": n,
                    "file_sha256": hashlib.sha256(bundle[n]).hexdigest()},
                   sort_keys=True) for n in names).encode("utf-8")


def _bundle(pnl=80.0, *, record_days=None, primary=None, secondary=None):
    """`record_days` / `primary` / `secondary` exist so the C6 negatives
    can break ONE equality at a time while every other check stays
    satisfied."""
    record_days = tuple(record_days if record_days is not None else ALL_DAYS)
    primary = primary if primary is not None else (TP_DAYS, FP_DAYS)
    secondary = secondary if secondary is not None else (
        tuple(sorted(TP_DAYS + (FP_DAYS[0],))), (FP_DAYS[1],))
    files = {}
    counts = {}
    for e in mcc.ENGINES:
        counts[e] = {}
        for s in mcc.SCENARIOS:
            rows = [_record_row(d, e, s, pnl) for d in record_days]
            files[f"MC_HANDOFF_{e}_{s}.jsonl"] = "\n".join(
                json.dumps(r, sort_keys=True) for r in rows).encode("utf-8")
            counts[e][s] = {"n_records": len(rows)}
    report = {
        "governance": {"trial_id": TRIAL, "authorized_commit": COMMIT},
        "oracle_daily": {
            PRIMARY: {"day_universe": {"tp_days": list(primary[0]),
                                       "fp_days": list(primary[1])}},
            SECONDARY: {"day_universe": {"tp_days": list(secondary[0]),
                                         "fp_days": list(secondary[1])}}},
        "mc_handoff_manifest": {"counts": counts}}
    files["S0_REPORT.json"] = json.dumps(report).encode("utf-8")
    files["S0_REPORT.md"] = b"# synthetic"
    files["HANDOFF_ADMISSION.json"] = json.dumps({"admitted": []}).encode()
    files["SEED_MANIFEST.json"] = json.dumps({
        "research_bootstrap_seeds": list(RESEARCH_BOOTSTRAP_SEEDS),
        "k_policy": "k_per_seed=200;k_start_index=0",
        "crn_scope": "shared_within_theta_engine_scenario"}).encode()
    files["REGISTRY_AFTER_RUN_STARTED.json"] = json.dumps({
        "snapshot_before": {"trial_id": TRIAL,
                            "authorized_commit": COMMIT}}).encode()
    _refresh_manifest(files)
    return files


def _calendar(n_days=8, n_offsets=2):
    return mcc.TemplateCalendar(
        days=tuple(TemplateDay(day_id=f"T{i:03d}", cal_offset=i)
                   for i in range(n_days)),
        first_month_offsets=tuple(range(n_offsets)))


def _prepare(bundle=None):
    b = bundle if bundle is not None else _bundle()
    return mcc.prepare_mc_input_for_tests(
        b, authorization_snapshot={"trial_id": TRIAL,
                                   "authorized_commit": COMMIT},
        custody_authority=mcc.CustodyAuthority.for_tests(b),
        test_only_calendar=_calendar())


@pytest.fixture()
def prepared():
    return _prepare()


def _prov(prepared):
    """B-PROV: the three custody-provenance fields are MANDATORY on
    `PreparedMCInput` — a prepared input with no declared custody source
    is not constructible. The hand-built inputs below are probing OTHER
    refusal codes, so they carry the fixture's own (test_only) provenance
    verbatim and nothing about what they test changes."""
    return {"source_artifact_id": prepared.source_artifact_id,
            "source_artifact_sha256": prepared.source_artifact_sha256,
            "test_only": prepared.test_only}


def _obs(prepared, **over):
    kw = dict(run_label="base", platform="topstep", engine="E1",
              scenario="Conservative", channel=PRIMARY, B=2, master_seed=7)
    kw.update(over)
    return mcc.run_observation_set(prepared, **kw)


class _LifecycleSpy:
    """Counts lifecycle executions so a test can prove a refusal happened
    BEFORE any simulation ran."""

    def __init__(self, monkeypatch):
        self.calls = 0
        real = orch.run_lifecycle

        def spy(*args, **kwargs):
            self.calls += 1
            return real(*args, **kwargs)

        monkeypatch.setattr(mcc.orch, "run_lifecycle", spy)


def _forge_live_records(prepared, forged):
    """Install a foreign record mapping on an ALREADY CONSTRUCTED prepared
    input, bypassing __post_init__ entirely.

    This is the strongest attacker available: someone who reaches past
    every constructor gate. It exists so the runtime chain check — not
    just the constructor — is what the regressions exercise."""
    object.__setattr__(prepared, "records", forged)
    return prepared


# ===========================================================================
# C1 — the six named regressions
# ===========================================================================

def test_c1_regression_1_record_content_change_moves_the_identity():
    """REGRESSION 1/6: records content -> prepared identity.

    Same file NAMES, same day universe, same calendar, same governance —
    one changed P&L number. The identity must move. Under R2.3 the
    preimage carried only the FILE digests, so a prepared object built
    around different records could share a digest bit for bit."""
    a = _prepare(_bundle(pnl=80.0))
    b = _prepare(_bundle(pnl=80.5))
    assert a.records_digest != b.records_digest
    assert mcc.prepared_digest(a) != mcc.prepared_digest(b)
    assert mcc.prepared_identity_bytes(a) != mcc.prepared_identity_bytes(b)
    # and the digest is a FUNCTION of the content: same bytes -> same id
    assert mcc.prepared_digest(_prepare(_bundle(pnl=80.0))) == \
        mcc.prepared_digest(a)
    # the identity preimage names the records explicitly
    raw = mcc.prepared_identity_bytes(a)
    ident = json.loads(raw.decode("utf-8"))
    assert ident["records_digest"] == a.records_digest
    assert set(ident["record_keys"]) == {
        f"{e}|{s}" for e in mcc.ENGINES for s in mcc.SCENARIOS}
    assert ident["record_keys"]["E1|Base"] == list(ALL_DAYS)
    # BOTH identity constructions must carry them. The preimage and the
    # digest are written out twice ON PURPOSE (so a drift is detectable);
    # this is the assertion that makes the duplication safe — drop the
    # records binding from EITHER copy and the two stop agreeing.
    assert hashlib.sha256(raw).hexdigest() == mcc.prepared_digest(a)
    assert hashlib.sha256(mcc.prepared_identity_bytes(b)).hexdigest() == \
        mcc.prepared_digest(b)
    # the two record fields are LOAD-BEARING in the preimage: rewrite
    # either one alone and the identity moves, with everything else —
    # file digests included — held fixed.
    for field, value in (("records_digest", b.records_digest),
                         ("record_keys", records_key_shifted(ident))):
        mutated = dict(ident)
        mutated[field] = value
        assert hashlib.sha256(
            json.dumps(mutated, sort_keys=True).encode("utf-8")
        ).hexdigest() != mcc.prepared_digest(a)


def records_key_shifted(ident):
    """The record key index with ONE date dropped — used to show the key
    set is load-bearing in the identity preimage."""
    keys = {k: list(v) for k, v in ident["record_keys"].items()}
    keys["E1|Base"] = keys["E1|Base"][:-1]
    return keys


def test_c1_regression_1b_every_record_field_is_covered(prepared):
    """Field-level: a single field of a single record moves the digest,
    for EVERY field of the frozen schema. A digest over a subset would
    leave a substitution surface on the uncovered fields."""
    base = mcc.records_canonical_digest(prepared.records)
    fields = tuple(dataclasses.fields(mcc.FrozenTradePath))
    assert len(fields) == 19
    moved = []
    for f in fields:
        rows = dict(prepared.records[("E1", "Base")])
        first = sorted(rows)[0]
        rec = rows[first]
        current = getattr(rec, f.name)
        if isinstance(current, bool):
            new = not current
        elif isinstance(current, float):
            new = current + 1.0
        elif isinstance(current, int):
            new = current + 1
        elif isinstance(current, str):
            new = current + "_MUTANT"
        elif isinstance(current, tuple):
            new = current + (1.0,)
        elif current is None:
            new = 1.0
        else:                                        # pragma: no cover
            pytest.fail(f"unhandled field type for {f.name}")
        rows[first] = dataclasses.replace(rec, **{f.name: new})
        mutated = dict(prepared.records)
        mutated[("E1", "Base")] = rows
        if mcc.records_canonical_digest(mutated) != base:
            moved.append(f.name)
    assert sorted(moved) == sorted(f.name for f in fields)


def test_c1_regression_2_swapped_live_records_refuse_before_any_lifecycle(
        prepared, monkeypatch):
    """REGRESSION 2/6: ONLY the live records mapping is replaced (the
    handoff bytes, the file digests and every identity field stay
    genuine). The replay must refuse BEFORE a single lifecycle runs."""
    forged = _prepare(_bundle(pnl=5000.0)).records
    spec = mcc.ReplaySpec.from_observations(
        _obs(prepared), records_digest=prepared.records_digest)
    spy = _LifecycleSpy(monkeypatch)
    _forge_live_records(prepared, forged)
    with pytest.raises(mcc.MCInputError) as exc:
        mcc.cold_replay_observation_set(prepared, spec)
    assert exc.value.code == "records_custody_content_mismatch"
    assert spy.calls == 0, "a lifecycle ran before the custody refusal"


def test_c1_regression_3_forged_records_plus_forged_caller_snapshot(
        prepared, monkeypatch):
    """REGRESSION 3/6: the attacker replaces the live records AND the
    caller-derived records snapshot on the ReplaySpec, while every
    EXTERNAL file digest stays untouched. Still refused — the replay's
    source of truth is the bytes, and a declared snapshot is only ever a
    binding to check."""
    other = _prepare(_bundle(pnl=5000.0))
    obs = _obs(prepared)
    spec = mcc.ReplaySpec.from_observations(
        obs, records_digest=other.records_digest)      # forged snapshot
    spy = _LifecycleSpy(monkeypatch)
    _forge_live_records(prepared, other.records)       # forged live map
    # the external evidence is untouched
    assert dict(prepared.file_sha256) == dict(_prepare().file_sha256)
    with pytest.raises(mcc.MCInputError) as exc:
        mcc.cold_replay_observation_set(prepared, spec)
    assert exc.value.code == "records_custody_content_mismatch"
    assert spy.calls == 0


def test_c1_regression_3b_a_forged_spec_snapshot_alone_is_refused(prepared):
    """The spec's declared records digest is a BINDING, never a source:
    on an otherwise genuine input a rewritten declaration still refuses,
    so the field can never become an alternative authority."""
    obs = _obs(prepared)
    spec = mcc.ReplaySpec.from_observations(obs, records_digest="f" * 64)
    with pytest.raises(mcc.MCInputError) as exc:
        mcc.cold_replay_observation_set(prepared, spec)
    assert exc.value.code == "cold_replay_records_digest_mismatch"


def test_c1_regression_4_altered_handoff_bytes_hit_the_custody_gate(
        prepared, monkeypatch):
    """REGRESSION 4/6: the RAW source bytes are altered while the pinned
    per-file digests are left alone — the custody gate refuses, at
    construction and at replay."""
    other = _bundle(pnl=5000.0)
    swapped = dict(prepared.handoff_bytes)
    swapped["MC_HANDOFF_E1_Base.jsonl"] = other["MC_HANDOFF_E1_Base.jsonl"]
    # (a) construction
    with pytest.raises(mcc.MCInputError) as exc:
        mcc.PreparedMCInput(
            **_prov(prepared),
            trial_id=prepared.trial_id,
            authorized_commit=prepared.authorized_commit,
            file_sha256=prepared.file_sha256,
            handoff_bytes=swapped,
            day_sequences=prepared.day_sequences,
            traded_day_sets=prepared.traded_day_sets,
            seeds=prepared.seeds, k_per_seed=prepared.k_per_seed,
            method_digest=prepared.method_digest,
            authorization_snapshot=prepared.authorization_snapshot,
            calendar=prepared.calendar)
    assert exc.value.code == "records_custody_bytes_mismatch"
    # (b) post-construction tampering, caught before any lifecycle
    spec = mcc.ReplaySpec.from_observations(_obs(prepared))
    spy = _LifecycleSpy(monkeypatch)
    object.__setattr__(prepared, "handoff_bytes", swapped)
    with pytest.raises(mcc.MCInputError) as exc:
        mcc.cold_replay_observation_set(prepared, spec)
    assert exc.value.code == "records_custody_bytes_mismatch"
    assert spy.calls == 0
    # (c) a bundle whose bytes were edited never reaches a prepared input
    edited = _bundle()
    edited["MC_HANDOFF_E1_Base.jsonl"] = other["MC_HANDOFF_E1_Base.jsonl"]
    with pytest.raises(mcc.MCInputError) as exc:
        _prepare(edited)                 # manifest/custody digests stale
    assert exc.value.code == "bundle_hash_mismatch"


def test_c1_regression_5_forward_and_replay_cannot_share_one_forgery(
        prepared, monkeypatch):
    """REGRESSION 5/6: hand the SAME content-swapped live object to the
    forward run and to the replay. Under R2.3 that was the winning
    attack — both sides consumed the forgery, agreed perfectly, and the
    receipt came back all green. Now NEITHER side can execute."""
    forged = _prepare(_bundle(pnl=5000.0)).records
    spec = mcc.ReplaySpec.from_observations(_obs(prepared))
    spy = _LifecycleSpy(monkeypatch)
    _forge_live_records(prepared, forged)
    with pytest.raises(mcc.MCInputError) as exc_fwd:
        _obs(prepared)                                  # forward
    assert exc_fwd.value.code == "records_custody_content_mismatch"
    with pytest.raises(mcc.MCInputError) as exc_rep:
        mcc.cold_replay_observation_set(prepared, spec)  # replay
    assert exc_rep.value.code == "records_custody_content_mismatch"
    assert spy.calls == 0


def test_c1_regression_6_positive_forward_and_replay_agree_per_atom(
        prepared):
    """REGRESSION 6/6 (POSITIVE, anti over-tightening): an honest bundle
    still replays to bitwise agreement, atom by atom, through the whole
    custody machinery."""
    obs = _obs(prepared)
    spec = mcc.ReplaySpec.from_observations(
        obs, records_digest=prepared.records_digest)
    replayed = mcc.cold_replay_observation_set(prepared, spec)
    cmp = mcc.compare_atom_tables(obs, replayed)
    assert cmp["key_set_equal"] is True
    assert cmp["mismatches"] == []
    assert cmp["produced_set_digest"] == cmp["replayed_set_digest"]
    assert len(cmp["produced_atom_digests"]) == obs.B * obs.M == 4
    # and the seal-level entry still produces a full green receipt
    receipt = mcc.cold_replay_evidence(prepared, [])
    assert receipt["records_custody_chain"]["records_digest"] == \
        prepared.records_digest


# ===========================================================================
# C1 — the four-link chain itself
# ===========================================================================

def test_the_custody_chain_links_bytes_digest_identity_and_atom_input(
        prepared):
    chain = mcc.verify_records_custody_chain(prepared)
    # link 1: raw bytes -> pinned per-file digests
    for name, digest in chain["handoff_sha256"].items():
        assert hashlib.sha256(
            prepared.handoff_bytes[name]).hexdigest() == digest
        assert prepared.file_sha256[name] == digest
    # link 2 -> link 3: parsed content digest is INSIDE the identity
    assert chain["records_digest"] == \
        chain["prepared_identity_records_digest"]
    # link 3: the identity bytes hash to the prepared digest
    assert chain["prepared_digest"] == mcc.prepared_digest(prepared)
    assert hashlib.sha256(mcc.prepared_identity_bytes(
        prepared)).hexdigest() == chain["prepared_digest"]
    # link 4: what the lifecycle reads is that same content
    assert chain["atom_records_digest"] == chain["records_digest"]


def test_the_replay_input_is_reparsed_not_aliased(prepared):
    replay = mcc.replay_prepared_from_custody_bytes(prepared)
    assert replay is not prepared
    assert replay.records is not prepared.records
    for key in prepared.records:
        assert replay.records[key] is not prepared.records[key]
    # ... and yet identical in content and identity
    assert replay.records_digest == prepared.records_digest
    assert mcc.prepared_digest(replay) == mcc.prepared_digest(prepared)
    assert replay.handoff_bytes.keys() == prepared.handoff_bytes.keys()


def test_the_replay_executes_on_the_rebuilt_input_not_the_callers_object(
        prepared, monkeypatch):
    """The lifecycles of a cold replay must consume the RE-PARSED input.
    The R2.3 code passed the caller's own object straight through to
    `run_observation_set`, which is why a forged trace replayed against
    its own forgery; this spy makes that substitution visible."""
    obs = _obs(prepared)
    spec = mcc.ReplaySpec.from_observations(obs)
    seen = {}
    real = mcc.run_observation_set

    def spy(prep, **kw):
        seen["input"] = prep
        seen["records"] = prep.records
        return real(prep, **kw)

    monkeypatch.setattr(mcc, "run_observation_set", spy)
    mcc.cold_replay_observation_set(prepared, spec)
    assert seen["input"] is not prepared, (
        "the replay executed on the caller's live object")
    assert seen["records"] is not prepared.records
    assert seen["input"].records_digest == prepared.records_digest


def test_records_have_no_caller_supplied_construction_path(prepared):
    """The mapping the lifecycle reads is DERIVED from the custody bytes
    on every construction. A caller may hand one over only as a
    declaration, and a wrong declaration refuses."""
    forged = _prepare(_bundle(pnl=5000.0)).records
    with pytest.raises(mcc.MCInputError) as exc:
        dataclasses.replace(prepared, records=forged)
    assert exc.value.code == "records_custody_content_mismatch"
    with pytest.raises(mcc.MCInputError) as exc:
        dataclasses.replace(prepared, records_digest="f" * 64)
    assert exc.value.code == "records_custody_digest_mismatch"
    # the honest declaration still passes (declare-and-verify)
    same = dataclasses.replace(prepared, records=prepared.records)
    assert same.records_digest == prepared.records_digest
    assert same.records is not forged


def test_c1_identity_copy_records_swap_attack_is_dead(prepared):
    """THE measured baseline counterexample, reproduced verbatim: copy
    every identity field, swap only `records`, keep the genuine
    `records_digest`. R2.3 produced a bit-identical digest and replayed
    green; this must now be unconstructible."""
    forged = _prepare(_bundle(pnl=5000.0)).records
    with pytest.raises(mcc.MCInputError) as exc:
        mcc.PreparedMCInput(
            **_prov(prepared),
            trial_id=prepared.trial_id,
            authorized_commit=prepared.authorized_commit,
            file_sha256=prepared.file_sha256,
            handoff_bytes=prepared.handoff_bytes,
            day_sequences=prepared.day_sequences,
            traded_day_sets=prepared.traded_day_sets,
            seeds=prepared.seeds, k_per_seed=prepared.k_per_seed,
            method_digest=prepared.method_digest,
            authorization_snapshot=prepared.authorization_snapshot,
            calendar=prepared.calendar,
            records=forged, records_digest=prepared.records_digest)
    assert exc.value.code == "records_custody_content_mismatch"


@pytest.mark.parametrize("mutate,code", [
    (lambda hb: {k: v for k, v in list(hb.items())[:-1]},
     "records_custody_source_keyset"),
    (lambda hb: dict(hb, EXTRA=b"{}"), "records_custody_source_keyset"),
    (lambda hb: dict(hb, **{"MC_HANDOFF_E1_Base.jsonl": "not bytes"}),
     "records_custody_source_not_bytes"),
])
def test_handoff_source_shape_violations_each_have_a_code(prepared, mutate,
                                                          code):
    with pytest.raises(mcc.MCInputError) as exc:
        mcc.PreparedMCInput(
            **_prov(prepared),
            trial_id=prepared.trial_id,
            authorized_commit=prepared.authorized_commit,
            file_sha256=prepared.file_sha256,
            handoff_bytes=mutate(dict(prepared.handoff_bytes)),
            day_sequences=prepared.day_sequences,
            traded_day_sets=prepared.traded_day_sets,
            seeds=prepared.seeds, k_per_seed=prepared.k_per_seed,
            method_digest=prepared.method_digest,
            authorization_snapshot=prepared.authorization_snapshot,
            calendar=prepared.calendar)
    assert exc.value.code == code


def test_unpinned_source_bytes_refuse(prepared):
    """A handoff file the identity does not pin cannot be the records
    source: the chain's first link would be missing."""
    sha = dict(prepared.file_sha256)
    sha["MC_HANDOFF_E1_Base.jsonl"] = None
    with pytest.raises(mcc.MCInputError) as exc:
        mcc.PreparedMCInput(
            **_prov(prepared),
            trial_id=prepared.trial_id,
            authorized_commit=prepared.authorized_commit,
            file_sha256=sha, handoff_bytes=prepared.handoff_bytes,
            day_sequences=prepared.day_sequences,
            traded_day_sets=prepared.traded_day_sets,
            seeds=prepared.seeds, k_per_seed=prepared.k_per_seed,
            method_digest=prepared.method_digest,
            authorization_snapshot=prepared.authorization_snapshot,
            calendar=prepared.calendar)
    assert exc.value.code == "records_custody_bytes_unpinned"


def test_prepared_input_retains_only_the_record_bytes(prepared):
    """FOOTPRINT PIN: the prepared input keeps the eight MC_HANDOFF_*
    blobs and NOTHING else. S0_REPORT.json alone is ~349 MB against
    ~92 MB for all eight handoff files at production scale, and its
    content is already pinned by `file_sha256`, so retaining it would
    multiply the footprint ~4.8x to re-prove what the digest proves."""
    assert set(prepared.handoff_bytes) == set(mcc.HANDOFF_FILES)
    assert len(mcc.HANDOFF_FILES) == 8
    assert "S0_REPORT.json" not in prepared.handoff_bytes
    assert all(isinstance(v, bytes)
               for v in prepared.handoff_bytes.values())
    # ... while every bundle member is still pinned by the identity
    assert set(prepared.file_sha256) == set(mcc.BUNDLE_EXACT_SET)


def test_the_records_source_is_immutable_from_outside(prepared):
    with pytest.raises(TypeError):
        prepared.handoff_bytes["MC_HANDOFF_E1_Base.jsonl"] = b"x"
    with pytest.raises(TypeError):
        prepared.records[("E1", "Base")]["2026-08-03"] = None
    caller_view = dict(prepared.handoff_bytes)
    caller_view["MC_HANDOFF_E1_Base.jsonl"] = b"mutated"
    assert prepared.handoff_bytes["MC_HANDOFF_E1_Base.jsonl"] != b"mutated"


def test_one_parser_serves_the_forward_run_and_the_replay():
    """A second parser would let the two sides disagree about records
    without either being 'wrong'."""
    src = (REPO / "src" / "itsf" / "mc" / "consumer.py").read_text(
        encoding="utf-8")
    assert src.count("def _parse_handoff_file") == 1
    assert src.count("def records_from_handoff_bytes") == 1
    assert src.count("def records_canonical_digest") == 1
    assert src.count("def _parse_record") == 1


def test_replay_refuses_a_non_prepared_authority():
    with pytest.raises(mcc.MCInputError) as exc:
        mcc.replay_prepared_from_custody_bytes({"records": {}})
    assert exc.value.code == "prepared_authority_missing"


# ===========================================================================
# C6 — day-universe engineering equality
# ===========================================================================

def test_c6_positive_the_production_shaped_bundle_satisfies_the_equality():
    """POSITIVE (anti over-tightening): the θ channels legitimately
    DISAGREE about which days are TP and which are FP — θ_0.3 promotes
    one FP day of θ_0.5 — while their UNION is one and the same
    population, exactly equal to the record day set."""
    prepared = _prepare()
    assert prepared.day_sequences[PRIMARY] == ALL_DAYS
    assert prepared.day_sequences[SECONDARY] == ALL_DAYS
    assert prepared.traded_day_sets[PRIMARY] != \
        prepared.traded_day_sets[SECONDARY]
    assert set(prepared.records[("E1", "Base")]) == set(ALL_DAYS)


def test_c6_negative_1_fp_day_without_a_record():
    """An FP day the record files do not carry. It was never checked: it
    silently becomes a no-trade day in every world that draws it."""
    days = tuple(d for d in ALL_DAYS if d != FP_DAYS[1])
    with pytest.raises(mcc.MCInputError) as exc:
        _prepare(_bundle(record_days=days,
                         secondary=(tuple(sorted(TP_DAYS + (FP_DAYS[0],))),
                                    ())))
    assert exc.value.code == "fp_day_without_record"
    assert FP_DAYS[1] in str(exc.value)


def test_c6_negative_2_record_day_in_no_oracle_class():
    """A record day classified by NO θ channel: the producer's exhaustive
    TP/FP partition did not hold for that day."""
    extra = "2026-08-10"
    with pytest.raises(mcc.MCInputError) as exc:
        _prepare(_bundle(record_days=tuple(sorted(ALL_DAYS + (extra,)))))
    assert exc.value.code == "record_without_oracle_class"
    assert extra in str(exc.value)


def test_c6_negative_3_theta_population_drift():
    """Two θ channels disagreeing about the day POPULATION (not about the
    TP/FP split, which is legitimate). Both are subsets of the record
    days, so only the cross-θ identity can see it."""
    with pytest.raises(mcc.MCInputError) as exc:
        _prepare(_bundle(
            secondary=(tuple(sorted(TP_DAYS + (FP_DAYS[0],))), ())))
    assert exc.value.code == "theta_population_drift"


def test_c6_negative_4_tp_day_without_a_record_keeps_its_own_code():
    """The pre-existing half of the equality keeps its own stable code —
    the new checks must not swallow it."""
    days = tuple(d for d in ALL_DAYS if d != TP_DAYS[0])
    with pytest.raises(mcc.MCInputError) as exc:
        _prepare(_bundle(
            record_days=days,
            secondary=(tuple(sorted(TP_DAYS[1:] + (FP_DAYS[0],))),
                       (FP_DAYS[1],))))
    assert exc.value.code == "tp_day_without_record"
    assert TP_DAYS[0] in str(exc.value)


def test_c6_messages_carry_counts_and_at_most_three_samples():
    """A sealed-input integrity failure must be diagnosable without
    dumping the whole universe into the log."""
    extra = tuple(f"2026-09-{i:02d}" for i in range(1, 9))
    with pytest.raises(mcc.MCInputError) as exc:
        _prepare(_bundle(record_days=tuple(sorted(ALL_DAYS + extra))))
    assert exc.value.code == "record_without_oracle_class"
    text = str(exc.value)
    assert "8 of 13" in text
    assert sum(1 for d in extra if d in text) == 3


def test_c6_refuses_in_the_prepare_battery_before_anything_runs():
    """The failure is a SEALED-INPUT INTEGRITY failure: it happens inside
    the prepare battery, so no prepared object, no exposure, no
    supplement and no research output can exist downstream of it."""
    import inspect
    src = inspect.getsource(mcc._prepare_mc_input_impl)
    for code in ("fp_day_without_record", "record_without_oracle_class",
                 "theta_population_drift"):
        assert code in src, code
    # the eight-file exact-key-set check is untouched and still there
    assert "record_set_drift_across_files" in src


def test_c6_record_set_drift_across_files_still_refuses():
    """PIN: the pre-existing cross-file record-set check keeps working
    (the new equalities are ADDITIONAL, not a replacement)."""
    b = _bundle()
    short = _bundle(record_days=ALL_DAYS[:-1])
    b["MC_HANDOFF_E2_Stress.jsonl"] = short["MC_HANDOFF_E2_Stress.jsonl"]
    _refresh_manifest(b)
    with pytest.raises(mcc.MCInputError) as exc:
        _prepare(b)
    assert exc.value.code == "record_set_drift_across_files"


# ===========================================================================
# C4 — the lane-S2' authoritative fact-verification wiring
# ===========================================================================

def test_c4_verifier_is_called_unconditionally_per_lifecycle(prepared,
                                                             monkeypatch):
    """The consumer calls lane S2's ONE fact-verification entry after
    every lifecycle and before any fact is reduced — once per (world,
    start-phase) atom, with the atom's own engine/platform."""
    from itsf.mc.platforms import authoritative as auth
    seen = []

    def fake_verify(events, *, engine, platform):
        seen.append((len(list(events)), engine, platform))
        return None

    monkeypatch.setattr(auth, mcc.AUTHORITATIVE_VERIFIER_NAME, fake_verify,
                        raising=False)
    obs = _obs(prepared, engine="E2", platform="lucid")
    assert len(seen) == obs.B * obs.M == 4
    assert {(e, p) for _n, e, p in seen} == {("E2", "lucid")}
    assert all(n > 0 for n, _e, _p in seen)


def test_c4_a_verifier_refusal_stops_the_atom(prepared, monkeypatch):
    """The verifier's own exception propagates untouched — the consumer
    neither swallows nor re-wraps lane S2's vocabulary, so WHICH fact
    failed stays visible."""
    from itsf.mc.platforms import authoritative as auth

    class _FactError(Exception):
        pass

    def fake_verify(events, *, engine, platform):
        raise _FactError("day_net_cross_check_violation")

    monkeypatch.setattr(auth, mcc.AUTHORITATIVE_VERIFIER_NAME, fake_verify,
                        raising=False)
    with pytest.raises(_FactError):
        _obs(prepared)


def test_c4_call_site_is_between_run_lifecycle_and_the_fact_reduction():
    """AST PIN of the ORDER: the verification happens after the lifecycle
    produced the stream and before `path_facts_from_events` reduces it."""
    import ast
    import inspect
    import textwrap
    src = textwrap.dedent(inspect.getsource(mcc._run_path_atom))
    calls = []
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Call):
            name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            if name in ("run_lifecycle", "_verify_event_stream",
                        "path_facts_from_events"):
                calls.append((node.lineno, name))
    order = [n for _l, n in sorted(calls)]
    assert order[:3] == ["run_lifecycle", "_verify_event_stream",
                         "path_facts_from_events"], order
    # no flag, cache or caller conclusion guards the call
    assert "if " not in inspect.getsource(mcc._run_path_atom).split(
        "_verify_event_stream")[0].splitlines()[-1]


def test_c4_the_join_is_closed_and_an_absent_verifier_refuses(prepared,
                                                              monkeypatch):
    """CROSS-LANE JOIN, CLOSED. Lane S2' owns `verify_event_stream` under
    the pinned name and signature; the consumer ships no stand-in. With
    the entry landed the requirement is ON, so a verifier that vanishes
    is a fail-closed refusal, never a silent skip."""
    from itsf.mc.platforms import authoritative as auth
    assert mcc.AUTHORITATIVE_VERIFIER_NAME == "verify_event_stream"
    assert mcc.AUTHORITATIVE_VERIFIER_REQUIRED is True
    monkeypatch.delattr(auth, mcc.AUTHORITATIVE_VERIFIER_NAME,
                        raising=False)
    with pytest.raises(mcc.MCInputError) as exc:
        _obs(prepared)
    assert exc.value.code == "authoritative_verifier_absent"


def test_c4_the_landed_verifier_has_the_pinned_contract():
    """The interface the main agent pinned: name, keyword-only engine and
    platform, returns None, first violation raises with a `.code`."""
    import inspect

    from itsf.mc.platforms import authoritative as auth
    verify = getattr(auth, mcc.AUTHORITATIVE_VERIFIER_NAME)
    sig = inspect.signature(verify)
    assert list(sig.parameters) == ["events", "engine", "platform"]
    for name in ("engine", "platform"):
        assert sig.parameters[name].kind is inspect.Parameter.KEYWORD_ONLY


def test_c4_the_real_verifier_runs_on_every_production_stream(prepared,
                                                              monkeypatch):
    """Not a fake: the LANDED verifier is what runs, and its refusal
    (lane S2's own typed error, with its stable code) propagates out of
    the consumer untouched."""
    from itsf.contracts import AuthoritativeFactError
    from itsf.mc.platforms import authoritative as auth
    calls = []
    real = auth.verify_event_stream

    def spy(events, *, engine, platform):
        calls.append((engine, platform))
        return real(events, engine=engine, platform=platform)

    monkeypatch.setattr(auth, "verify_event_stream", spy)
    obs = _obs(prepared)                       # honest stream: no raise
    assert len(calls) == obs.B * obs.M

    def refuser(events, *, engine, platform):
        raise AuthoritativeFactError(auth.AUTH_DAY_NET_INVARIANT, "probe")

    monkeypatch.setattr(auth, "verify_event_stream", refuser)
    with pytest.raises(AuthoritativeFactError) as exc:
        _obs(prepared)
    assert exc.value.code == auth.AUTH_DAY_NET_INVARIANT


def test_c4_the_consumer_ships_no_substitute_verifier():
    """The consumer must not grow its own copy of the producer's fact
    rules: it resolves the entry by name from the S2' module."""
    src = (REPO / "src" / "itsf" / "mc" / "consumer.py").read_text(
        encoding="utf-8")
    assert "def verify_event_stream" not in src
    assert "from itsf.mc.platforms import authoritative" in src
