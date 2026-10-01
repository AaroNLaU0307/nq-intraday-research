"""Synthetic-fixture tests for src/itsf/s0/runinfra.py (SA-5, M5-T2).

No real data, no network, no directory creation by the module under test —
every I/O test uses pytest's `tmp_path` (already-existing temp directories),
matching runinfra's contract that it never creates attempt/run roots.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from itsf.contracts import (
    APPROVED_NA_REASONS,
    AssertionMismatchError,
    LogLeakError,
    NAConservationError,
    RunConfig,
    RunGateError,
    RunStage,
    TrialState,
)
from itsf.s0 import runinfra as ri


# ===========================================================================
# helpers
# ===========================================================================


def _file_record(stage: str, relative_path: str, data: bytes, previous_hash: str,
                  manifest_relative_path: str = "manifest.jsonl") -> dict:
    payload = {
        "record_type": "file",
        "stage": stage,
        "relative_path": relative_path,
        "file_sha256": hashlib.sha256(data).hexdigest(),
        "previous_record_hash": previous_hash,
    }
    canonical = ri.canonicalize_manifest_record(
        payload, manifest_relative_path=manifest_relative_path
    )
    return {**payload, "record_hash": ri.compute_record_hash(canonical)}


def _seal_record(stage: str, previous_hash: str,
                  manifest_relative_path: str = "manifest.jsonl") -> dict:
    payload = {
        "record_type": "stage_seal",
        "stage": stage,
        "sealed_record_hash": previous_hash,
        "previous_record_hash": previous_hash,
    }
    canonical = ri.canonicalize_manifest_record(
        payload, manifest_relative_path=manifest_relative_path
    )
    return {**payload, "record_hash": ri.compute_record_hash(canonical)}


def _read_manifest(path: Path) -> list[dict]:
    lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    return [json.loads(ln) for ln in lines]


def _run_config() -> RunConfig:
    return RunConfig(
        trial_id="S0-T001",
        authorized_commit="0" * 40,
        engineering_seed=20260731,
        attempts_dir="attempts/S0-T001-A1_20260731T000000Z",
        runs_dir="runs/S0-T001_20260731T000000Z",
        assertions_path="expected_preflight_assertions.json",
    )


# ===========================================================================
# 0. canonicalization / hashing primitives
# ===========================================================================


def test_canonicalize_manifest_record_is_compact_and_key_sorted():
    payload = {
        "record_type": "file",
        "stage": "A_PRECHECK",
        "relative_path": "logs/z.log",
        "file_sha256": "a" * 64,
        "previous_record_hash": ri.GENESIS_PREVIOUS_HASH,
    }
    canonical = ri.canonicalize_manifest_record(payload)
    assert " " not in canonical
    assert canonical.index('"file_sha256"') < canonical.index('"previous_record_hash"')
    assert canonical.index('"previous_record_hash"') < canonical.index('"record_type"')
    assert canonical.index('"record_type"') < canonical.index('"relative_path"')
    assert canonical.index('"relative_path"') < canonical.index('"stage"')


def test_compute_record_hash_matches_manual_sha256():
    canonical = '{"a":1}'
    assert ri.compute_record_hash(canonical) == hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()


def test_canonicalize_rejects_wrong_keys_and_bad_record_type():
    with pytest.raises(ri.ManifestIntegrityError):
        ri.canonicalize_manifest_record({"record_type": "not_a_type"})
    with pytest.raises(ri.ManifestIntegrityError):
        ri.canonicalize_manifest_record({
            "record_type": "file",
            "stage": "A_PRECHECK",
            "relative_path": "x.log",
            "file_sha256": "a" * 64,
            "previous_record_hash": ri.GENESIS_PREVIOUS_HASH,
            "unexpected_extra_field": 1,
        })


# ===========================================================================
# 1. manifest hash chain — append / replay / tamper detection
# ===========================================================================


def test_chain_append_replay_roundtrip(tmp_path):
    manifest = tmp_path / "manifest.jsonl"

    r1 = _file_record("A_PRECHECK", "logs/a1.log", b"hello-a1", ri.GENESIS_PREVIOUS_HASH)
    p1 = ri.append_manifest_record(manifest, {**r1, "finalized": True})

    seal_a = _seal_record("A_PRECHECK", p1["record_hash"])
    p2 = ri.append_manifest_record(manifest, {**seal_a, "finalized": True})

    r2 = _file_record("B_LOAD_VALIDATE", "logs/b1.log", b"hello-b1", p2["record_hash"])
    p3 = ri.append_manifest_record(manifest, {**r2, "finalized": True})

    seal_b = _seal_record("B_LOAD_VALIDATE", p3["record_hash"])
    ri.append_manifest_record(manifest, {**seal_b, "finalized": True})

    records = _read_manifest(manifest)
    assert len(records) == 4

    result = ri.verify_chain_records(records)
    assert result.valid, result.errors
    assert result.n_records == 4
    assert set(result.sealed_stages) == {"A_PRECHECK", "B_LOAD_VALIDATE"}


def test_chain_tamper_on_field_detected(tmp_path):
    manifest = tmp_path / "manifest.jsonl"
    r1 = _file_record("A_PRECHECK", "logs/a1.log", b"hello-a1", ri.GENESIS_PREVIOUS_HASH)
    ri.append_manifest_record(manifest, {**r1, "finalized": True})

    records = _read_manifest(manifest)
    records[0]["file_sha256"] = "1" * 64  # tamper without recomputing record_hash

    result = ri.verify_chain_records(records)
    assert not result.valid
    assert any("mismatch" in e for e in result.errors)


def test_chain_tamper_on_hash_breaks_linkage(tmp_path):
    manifest = tmp_path / "manifest.jsonl"
    r1 = _file_record("A_PRECHECK", "logs/a1.log", b"hello-a1", ri.GENESIS_PREVIOUS_HASH)
    p1 = ri.append_manifest_record(manifest, {**r1, "finalized": True})
    seal_a = _seal_record("A_PRECHECK", p1["record_hash"])
    ri.append_manifest_record(manifest, {**seal_a, "finalized": True})

    records = _read_manifest(manifest)
    records[0]["record_hash"] = "2" * 64  # forge a different (still well-formed) hash

    result = ri.verify_chain_records(records)
    assert not result.valid
    joined = " ".join(result.errors)
    assert "mismatch" in joined or "chain break" in joined


def test_genesis_previous_hash_enforced(tmp_path):
    manifest = tmp_path / "manifest.jsonl"
    bad = _file_record("A_PRECHECK", "logs/a1.log", b"x", "1" * 64)  # not genesis zeros

    with pytest.raises(ri.ManifestIntegrityError):
        ri.append_manifest_record(manifest, {**bad, "finalized": True})

    result = ri.verify_chain_records([bad])
    assert not result.valid
    assert any("genesis" in e for e in result.errors)


def test_manifest_self_exclusion_rejected():
    with pytest.raises(ri.ManifestIntegrityError, match="self-reference"):
        ri.canonicalize_manifest_record(
            {
                "record_type": "file",
                "stage": "A_PRECHECK",
                "relative_path": "manifest.jsonl",
                "file_sha256": "0" * 64,
                "previous_record_hash": ri.GENESIS_PREVIOUS_HASH,
            },
            manifest_relative_path="manifest.jsonl",
        )


@pytest.mark.parametrize("bad_path", [
    "/abs/path.log",
    "C:/windows/path.log",
    "../escape.log",
    "logs/../../escape.log",
    "logs\\backslash.log",
    "",
])
def test_relative_path_traversal_and_absolute_rejected(bad_path):
    with pytest.raises(ri.ManifestIntegrityError):
        ri.canonicalize_manifest_record({
            "record_type": "file",
            "stage": "A_PRECHECK",
            "relative_path": bad_path,
            "file_sha256": "0" * 64,
            "previous_record_hash": ri.GENESIS_PREVIOUS_HASH,
        })


def test_finalized_gate_rejects_unfinalized(tmp_path):
    manifest = tmp_path / "manifest.jsonl"
    r1 = _file_record("A_PRECHECK", "logs/a1.log", b"x", ri.GENESIS_PREVIOUS_HASH)

    with pytest.raises(ValueError):
        ri.append_manifest_record(manifest, {**r1, "finalized": False})
    with pytest.raises(ValueError):
        ri.append_manifest_record(manifest, r1)  # no 'finalized' key at all

    assert not manifest.exists()


def test_append_rejects_missing_parent_dir(tmp_path):
    missing = tmp_path / "does_not_exist" / "manifest.jsonl"
    r1 = _file_record("A_PRECHECK", "logs/a1.log", b"x", ri.GENESIS_PREVIOUS_HASH)
    with pytest.raises(FileNotFoundError):
        ri.append_manifest_record(missing, {**r1, "finalized": True})


def test_append_rejects_corrupt_supplied_hash(tmp_path):
    manifest = tmp_path / "manifest.jsonl"
    r1 = _file_record("A_PRECHECK", "logs/a1.log", b"x", ri.GENESIS_PREVIOUS_HASH)
    r1["record_hash"] = "f" * 64  # deliberately wrong
    with pytest.raises(ri.ManifestIntegrityError):
        ri.append_manifest_record(manifest, {**r1, "finalized": True})


def test_stage_reopened_after_seal_detected_by_verify(tmp_path):
    manifest = tmp_path / "manifest.jsonl"
    r1 = _file_record("A_PRECHECK", "logs/a1.log", b"x", ri.GENESIS_PREVIOUS_HASH)
    p1 = ri.append_manifest_record(manifest, {**r1, "finalized": True})
    seal_a = _seal_record("A_PRECHECK", p1["record_hash"])
    p2 = ri.append_manifest_record(manifest, {**seal_a, "finalized": True})
    r2 = _file_record("A_PRECHECK", "logs/a2.log", b"y", p2["record_hash"])
    ri.append_manifest_record(manifest, {**r2, "finalized": True})  # illegal, but append() only checks local linkage

    result = ri.verify_chain_records(_read_manifest(manifest))
    assert not result.valid
    assert any("already sealed" in e for e in result.errors)


def test_stage_seal_must_reference_previous_hash():
    r1 = _file_record("A_PRECHECK", "logs/a1.log", b"x", ri.GENESIS_PREVIOUS_HASH)
    payload = {
        "record_type": "stage_seal",
        "stage": "A_PRECHECK",
        "sealed_record_hash": "9" * 64,  # deliberately does not match previous_record_hash
        "previous_record_hash": r1["record_hash"],
    }
    canonical = ri.canonicalize_manifest_record(payload)
    seal = {**payload, "record_hash": ri.compute_record_hash(canonical)}

    result = ri.verify_chain_records([r1, seal])
    assert not result.valid
    assert any("sealed_record_hash" in e for e in result.errors)


def test_file_hash_provider_mismatch_detected():
    r1 = _file_record("A_PRECHECK", "logs/a1.log", b"real-bytes", ri.GENESIS_PREVIOUS_HASH)
    result = ri.verify_chain_records([r1], file_hash_provider=lambda rel: "0" * 64)
    assert not result.valid
    assert any("file_sha256 mismatch" in e for e in result.errors)


def test_file_hash_provider_match_passes():
    data = b"real-bytes"
    r1 = _file_record("A_PRECHECK", "logs/a1.log", data, ri.GENESIS_PREVIOUS_HASH)
    seal = _seal_record("A_PRECHECK", r1["record_hash"])
    result = ri.verify_chain_records(
        [r1, seal], file_hash_provider=lambda rel: hashlib.sha256(data).hexdigest()
    )
    assert result.valid, result.errors


# --- F-26: seal discipline + corrupt tail ----------------------------------


def test_unsealed_stage_is_chain_invalid():
    """A stage with records but no stage_seal (truncated tail) must not
    replay as a valid chain."""
    r1 = _file_record("A_PRECHECK", "logs/a1.log", b"x", ri.GENESIS_PREVIOUS_HASH)
    result = ri.verify_chain_records([r1])
    assert not result.valid
    assert any("no stage_seal" in e for e in result.errors)


def test_stage_seal_without_any_record_is_chain_invalid():
    seal = _seal_record("A_PRECHECK", ri.GENESIS_PREVIOUS_HASH)
    result = ri.verify_chain_records([seal])
    assert not result.valid
    assert any("seals no records" in e for e in result.errors)


def test_last_stage_unsealed_detected_after_valid_earlier_stage():
    r1 = _file_record("A_PRECHECK", "logs/a1.log", b"x", ri.GENESIS_PREVIOUS_HASH)
    seal_a = _seal_record("A_PRECHECK", r1["record_hash"])
    r2 = _file_record("E_REPORT", "S0_REPORT.md", b"y", seal_a["record_hash"])
    result = ri.verify_chain_records([r1, seal_a, r2])
    assert not result.valid
    assert any("E_REPORT" in e and "no stage_seal" in e for e in result.errors)


def test_append_rejects_corrupt_tail_line(tmp_path):
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text("{not json at all\n", encoding="utf-8")
    rec = _file_record("A_PRECHECK", "logs/a1.log", b"x", ri.GENESIS_PREVIOUS_HASH)
    with pytest.raises(ri.ManifestIntegrityError, match="not valid JSON"):
        ri.append_manifest_record(manifest, {**rec, "finalized": True})


def test_append_rejects_tail_without_record_hash(tmp_path):
    """Previously the missing field silently fell back to the genesis hash,
    letting a damaged manifest be re-forked from scratch."""
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(json.dumps({"record_type": "file"}) + "\n", encoding="utf-8")
    rec = _file_record("A_PRECHECK", "logs/a1.log", b"x", ri.GENESIS_PREVIOUS_HASH)
    with pytest.raises(ri.ManifestIntegrityError, match="no valid"):
        ri.append_manifest_record(manifest, {**rec, "finalized": True})


# ===========================================================================
# 2. Stage-C log guard
# ===========================================================================


def test_log_guard_whitelist_messages_pass():
    ri.validate_log_event("stage=C_COMPUTE status=pass")
    ri.validate_log_event("stage=C_COMPUTE status=start")
    ri.validate_log_event("heartbeat stage=C_COMPUTE ts=2026-07-31T10:15:00Z")
    ri.validate_log_event(
        "file=runs/S0-T001_20260731T100000Z/logs/stage_c.log sha256=" + "a" * 64
    )
    ri.validate_log_event("stage=C_COMPUTE complete records=1200")


@pytest.mark.parametrize("word", [
    "oracle", "label", "e1", "e2", "annual", "frequency", "distribution",
])
def test_log_guard_blocks_research_vocabulary(word):
    with pytest.raises(LogLeakError):
        ri.validate_log_event(f"stage=C_COMPUTE status=pass {word}_leak")


def test_log_guard_blocks_vocab_embedded_in_otherwise_whitelisted_path():
    # Schema-shape alone would accept this (it's a valid file=/sha256= line);
    # the vocabulary layer must still catch it (defense in depth).
    msg = "file=runs/oracle_ceiling_summary.log sha256=" + "b" * 64
    with pytest.raises(LogLeakError):
        ri.validate_log_event(msg)


def test_log_guard_blocks_bare_float_embedded_in_otherwise_whitelisted_path():
    # Schema-shape alone would accept this too; the float scanner must catch it.
    msg = "file=runs/report_v0.5.log sha256=" + "c" * 64
    with pytest.raises(LogLeakError):
        ri.validate_log_event(msg)


def test_log_guard_blocks_bare_float_free_text():
    with pytest.raises(LogLeakError):
        ri.validate_log_event("mean value observed 0.4213")


def test_log_guard_rejects_unknown_schema_message():
    with pytest.raises(LogLeakError):
        ri.validate_log_event("totally unstructured free text with no schema")


def test_log_guard_rejects_non_str_message():
    with pytest.raises(LogLeakError):
        ri.validate_log_event(12345)  # type: ignore[arg-type]


def test_log_guard_explicit_schema_restricts_match():
    with pytest.raises(LogLeakError):
        ri.validate_log_event("stage=C_COMPUTE status=pass", schema="heartbeat")
    ri.validate_log_event("stage=C_COMPUTE status=pass", schema="stage_status")


def test_log_guard_counts_and_hashes_pass_numeric_whitelist():
    ri.validate_log_event("stage=D_INTEGRITY complete records=2868")
    ri.validate_log_event("file=manifest_check.log sha256=" + "0" * 64)


# --- F-20: vocabulary + underscore-as-decimal-point smuggling -------------


@pytest.mark.parametrize("word", [
    "theta", "base_rate", "cont", "adr", "adr14", "rvol", "gap", "retrace",
    "warmup", "funnel", "na",
])
def test_log_guard_blocks_s0_feature_vocabulary(word):
    with pytest.raises(LogLeakError):
        ri.validate_log_event(f"stage=C_COMPUTE status=pass {word}")


def test_log_guard_blocks_vocabulary_inside_file_path():
    with pytest.raises(LogLeakError):
        ri.validate_log_event("file=runs/base_rate_summary.log sha256=" + "a" * 64)


def test_log_guard_blocks_underscore_encoded_decimal_in_filename():
    """`base_rate_0_63.log` encodes 0.63 without ever writing a '.'."""
    with pytest.raises(LogLeakError):
        ri.validate_log_event("file=runs/theta_0_63.log sha256=" + "a" * 64)
    with pytest.raises(LogLeakError, match="underscores"):
        ri.validate_log_event("file=runs/summary_0_63.log sha256=" + "a" * 64)


def test_log_guard_still_allows_utc_stamped_run_directories():
    """The narrow rule must not break legitimate run-directory names."""
    ri.validate_log_event(
        "file=runs/S0-T001_20260731T100000Z/logs/stage_c.log sha256=" + "a" * 64)


# ===========================================================================
# 3b. preflight -> contracts translation layer (F-14)
# ===========================================================================


def _mini_preflight() -> dict:
    return {
        "funnel": {
            "L0_scheduled_trading_days": 2989,
            "minus_zero_bar_days": 20,
            "L1_observed_rth_days": 2969,
            "minus_scheduled_early_close_days": 85,
            "L2_regular_full_session_candidates": 2884,
            "minus_rth_missing_gt_10pct_days": 2,
            "L3_structurally_eligible_days": 2882,
            "minus_adr14_warmup_days": 14,
            "L4_final_feature_construction_dates": 2868,
            "side_diagnostic_complete_390_bar_rth_days": 2870,
        },
        "f10": {"final_mutually_exclusive_F10_counts_eligible": {
            "CPI": 128, "NFP": 134, "FOMC": 83, "none": 2528,
            "NA_multi_event": 9}},
        "features": {
            "F8": {"constructible": 2856, "na": 26,
                   "reasons": {"zero_denominator_no_direction": 26}},
            "F10": {"constructible": 2873, "na": 9,
                    "reasons": {"multi_event_day_single_category_undetermined": 9}},
        },
        "anchors": {"prev_rth_close": {
            "available": 2864, "missing": 18,
            "missing_reasons": {"no_prior_rth_session_in_sample": 1,
                                "prev_day_early_close_final_scheduled_bar_absent": 12,
                                "prev_day_vendor_degraded_zero_bar": 3,
                                "prev_day_1559_bar_absent": 2}}},
        "labels": {"Y_cont": {"available_days": 2842, "unavailable_days": 40}},
    }


def test_translate_emits_five_number_funnel_chain_only():
    out = ri.translate_preflight_assertions(_mini_preflight())
    funnel_keys = sorted(k for k in out if k.startswith("funnel."))
    assert len(funnel_keys) == 5
    assert [out[k] for k in funnel_keys] == [2989, 2969, 2884, 2882, 2868]
    # the four delta rows (incl. the adr14 row) and the side diagnostic are
    # dropped: a delta is not an independently computed quantity
    assert not [k for k in out if "minus_" in k or "side_diagnostic" in k]
    assert "funnel.minus_adr14_warmup_days" not in out


def test_translate_maps_reason_words_onto_contracts_vocabulary():
    out = ri.translate_preflight_assertions(_mini_preflight())
    assert out["na_reason.F8.zero_direction_day_l82"] == 26
    assert out["na_reason.F10.multi_event_day_f10_na"] == 9
    # the four IR-19 sub-reasons collapse onto one approved reason, summed
    assert out["na_reason.anchor.prev_rth_close.prev_rth_close_anchor_missing"] == 18
    for key in out:
        if key.startswith("na_reason."):
            assert key.rsplit(".", 1)[1] in APPROVED_NA_REASONS


def test_translate_preserves_every_value_verbatim():
    """Semantics must not move: each translated value equals its source."""
    src = _mini_preflight()
    out = ri.translate_preflight_assertions(src)
    assert out["f10.CPI"] == src["f10"]["final_mutually_exclusive_F10_counts_eligible"]["CPI"]
    assert out["feature.F8.na"] == src["features"]["F8"]["na"]
    assert out["feature.F8.constructible"] == src["features"]["F8"]["constructible"]
    assert out["anchor.prev_rth_close.missing"] == src["anchors"]["prev_rth_close"]["missing"]
    assert out["label.Y_cont.unavailable"] == src["labels"]["Y_cont"]["unavailable_days"]


def test_translate_drops_any_adr14_feature_row():
    src = _mini_preflight()
    src["features"]["adr14"] = {"constructible": 2868, "na": 14, "reasons": {}}
    out = ri.translate_preflight_assertions(src)
    assert "feature.adr14.na" not in out
    assert "feature.adr14.constructible" not in out


def test_translate_refuses_unknown_reason_word():
    src = _mini_preflight()
    src["features"]["F8"]["reasons"] = {"a_brand_new_reason": 26}
    with pytest.raises(ValueError, match="refusing to guess"):
        ri.translate_preflight_assertions(src)


def test_translate_refuses_missing_section():
    src = _mini_preflight()
    del src["f10"]
    with pytest.raises(ValueError):
        ri.translate_preflight_assertions(src)


def test_translate_output_is_directly_comparable():
    """The whole point of F-14: translated output plugs straight into the
    comparator with a matching key set."""
    expected = ri.translate_preflight_assertions(_mini_preflight())
    actual = dict(expected)
    assert ri.compare_preflight_assertions(expected, actual).all_pass
    actual["funnel.L4_final_feature_construction_dates"] += 1
    result = ri.compare_preflight_assertions(expected, actual)
    assert not result.all_pass
    assert result.shape_ok
    assert result.mismatched_keys == ("funnel.L4_final_feature_construction_dates",)


def test_translate_of_the_real_preflight_document_is_shape_stable():
    """Read-only structural translation of the repo's own (hash-locked)
    preflight JSON — no market data is touched."""
    path = Path(__file__).resolve().parents[1] / "S0_INPUT_PREFLIGHT.json"
    out = ri.translate_preflight_assertions(json.loads(path.read_text("utf-8")))
    assert out["funnel.L0_scheduled_trading_days"] == 2989
    assert out["funnel.L4_final_feature_construction_dates"] == 2868
    assert [out[f"f10.{c}"] for c in ("CPI", "NFP", "FOMC", "none", "NA_multi_event")] \
        == [128, 134, 83, 2528, 9]
    assert all(isinstance(v, int) for v in out.values())


# ===========================================================================
# 3. NA conservation checker
# ===========================================================================


def test_na_conservation_passes_when_itemized_sums_match():
    na_table = {"F5_gap": {"roll_transition_day_na": 3, "adr14_warmup": 14}}
    result = ri.check_na_conservation(na_table, reported_total_na={"F5_gap": 17})
    assert result.ok, result.errors
    assert result.unregistered_reasons == ()
    assert result.miscounted_columns == ()


def test_na_conservation_rejects_unregistered_reason():
    na_table = {"F5_gap": {"mystery_reason_not_approved": 3}}
    result = ri.check_na_conservation(na_table, reported_total_na={"F5_gap": 3})
    assert not result.ok
    assert "F5_gap::mystery_reason_not_approved" in result.unregistered_reasons


def test_na_conservation_rejects_overcount():
    na_table = {"F5_gap": {"roll_transition_day_na": 20}}
    result = ri.check_na_conservation(na_table, reported_total_na={"F5_gap": 17})
    assert not result.ok
    assert "F5_gap" in result.miscounted_columns


def test_na_conservation_rejects_undercount():
    na_table = {"F5_gap": {"roll_transition_day_na": 10}}
    result = ri.check_na_conservation(na_table, reported_total_na={"F5_gap": 17})
    assert not result.ok
    assert "F5_gap" in result.miscounted_columns


def test_na_conservation_uses_real_approved_reasons_by_default():
    na_table = {"Y_cont": {r: 1 for r in APPROVED_NA_REASONS[:3]}}
    result = ri.check_na_conservation(na_table, reported_total_na={"Y_cont": 3})
    assert result.ok, result.errors


# --- F-13: the checker can no longer be half-disabled at the call site -----


def test_na_conservation_rejects_caller_supplied_reason_table():
    """The approved-reason set is not a parameter any more: a caller cannot
    widen it to bless its own unregistered reason."""
    with pytest.raises(TypeError):
        ri.check_na_conservation(
            {"F5_gap": {"my_own_reason": 1}},
            reported_total_na={"F5_gap": 1},
            approved_reasons=("my_own_reason",),           # type: ignore[call-arg]
        )
    result = ri.check_na_conservation(
        {"F5_gap": {"my_own_reason": 1}}, reported_total_na={"F5_gap": 1})
    assert not result.ok
    assert "F5_gap::my_own_reason" in result.unregistered_reasons


def test_na_conservation_requires_reported_totals():
    with pytest.raises(TypeError):
        ri.check_na_conservation({"F5_gap": {"roll_transition_day_na": 3}})  # type: ignore[call-arg]


def test_na_conservation_flags_column_without_observed_total():
    """Half-checks are gone: an itemized column with no independently
    observed total is a conservation failure, not a silent pass."""
    result = ri.check_na_conservation(
        {"F5_gap": {"roll_transition_day_na": 3}, "F7_on_range": {"adr14_warmup": 1}},
        reported_total_na={"F5_gap": 3})
    assert not result.ok
    assert "F7_on_range" in result.miscounted_columns


# ===========================================================================
# 4. expected_preflight_assertions comparator
# ===========================================================================


def test_assertions_all_pass():
    expected = {"L0": 2989, "L1": 2969, "F10_CPI": 128}
    result = ri.compare_preflight_assertions(expected, dict(expected))
    assert result.all_pass
    assert result.shape_ok
    assert result.mismatched_keys == ()


def test_assertions_single_item_mismatch():
    expected = {"L0": 2989, "L1": 2969}
    actual = {"L0": 2989, "L1": 2970}
    result = ri.compare_preflight_assertions(expected, actual)
    assert not result.all_pass
    assert result.shape_ok
    assert result.mismatched_keys == ("L1",)


def test_assertions_shape_mismatch_missing_and_extra():
    expected = {"L0": 2989, "L1": 2969}
    actual = {"L0": 2989, "L2": 2884}
    result = ri.compare_preflight_assertions(expected, actual)
    assert not result.all_pass
    assert not result.shape_ok
    assert result.missing_keys == ("L1",)
    assert result.extra_keys == ("L2",)


def test_assertions_bool_int_not_aliased():
    result = ri.compare_preflight_assertions({"flag": True}, {"flag": 1})
    assert not result.all_pass
    assert result.mismatched_keys == ("flag",)


def test_assertions_never_reads_preflight_file(monkeypatch):
    """Regression guard for the 2026-07-31 ruling: this comparator must
    never touch the filesystem; expected/actual are always caller-supplied."""
    import builtins

    original_open = builtins.open

    def _blow_up(*a, **kw):
        raise AssertionError("compare_preflight_assertions must not open files")

    monkeypatch.setattr(builtins, "open", _blow_up)
    try:
        result = ri.compare_preflight_assertions({"a": 1}, {"a": 1})
        assert result.all_pass
    finally:
        monkeypatch.setattr(builtins, "open", original_open)


# ===========================================================================
# 5. failure report render + write
# ===========================================================================


def test_render_failure_report_field_completeness():
    rendered = ri.render_failure_report(
        report_type="PRE_RUN_ATTEMPT_FAILURE",
        run_config=_run_config(),
        stage=RunStage.B_LOAD_VALIDATE,
        trial_state=TrialState.PACKET_APPROVED,
        failure_reason="structure assertion mismatch on F10 funnel",
        exception_type=AssertionMismatchError.__name__,
        released_information=["stage=B pass/fail only", "structural counts only"],
        chain_status={"n_records": 3, "valid": True},
        generated_at_utc="2026-07-31T12:00:00Z",
    )
    assert "PRE_RUN_ATTEMPT_FAILURE" in rendered.markdown
    assert "S0-T001" in rendered.markdown
    assert "Failure point" in rendered.markdown
    assert "structure assertion mismatch on F10 funnel" in rendered.markdown
    assert "Released information" in rendered.markdown
    assert "stage=B pass/fail only" in rendered.markdown
    assert "Chain status" in rendered.markdown

    payload = rendered.json_payload
    for key in ("report_type", "trial_id", "authorized_commit", "stage",
                "trial_state", "failure_reason", "exception_type",
                "released_information", "chain_status", "generated_at_utc"):
        assert key in payload


def test_render_failure_report_rejects_invalid_exception_type():
    with pytest.raises(ValueError):
        ri.render_failure_report(
            report_type="RUN_FAILURE_REPORT",
            run_config=_run_config(),
            stage=RunStage.C_COMPUTE,
            trial_state=TrialState.RUNNING,
            failure_reason="x",
            exception_type="MadeUpError",
            released_information=[],
            chain_status={},
            generated_at_utc="2026-07-31T12:00:00Z",
        )


def test_render_failure_report_rejects_invalid_report_type():
    with pytest.raises(ValueError):
        ri.render_failure_report(
            report_type="NOT_A_REAL_REPORT",
            run_config=_run_config(),
            stage=RunStage.C_COMPUTE,
            trial_state=TrialState.RUNNING,
            failure_reason="x",
            exception_type="Unknown",
            released_information=[],
            chain_status={},
            generated_at_utc="2026-07-31T12:00:00Z",
        )


def test_write_failure_report_writes_both_files(tmp_path):
    rendered = ri.render_failure_report(
        report_type="RUN_FAILURE_REPORT",
        run_config=_run_config(),
        stage=RunStage.D_INTEGRITY,
        trial_state=TrialState.RUNNING,
        failure_reason="NA conservation violated",
        exception_type=NAConservationError.__name__,
        released_information=["stage D pass/fail only"],
        chain_status={"valid": False},
        generated_at_utc="2026-07-31T13:00:00Z",
    )
    paths = ri.write_failure_report(tmp_path, rendered)
    assert paths["markdown"].read_text(encoding="utf-8") == rendered.markdown
    written_json = json.loads(paths["json"].read_text(encoding="utf-8"))
    assert written_json["exception_type"] == NAConservationError.__name__


def test_write_failure_report_refuses_missing_directory(tmp_path):
    rendered = ri.render_failure_report(
        report_type="RUN_FAILURE_REPORT",
        run_config=_run_config(),
        stage=RunStage.C_COMPUTE,
        trial_state=TrialState.RUNNING,
        failure_reason="x",
        exception_type=RunGateError.__name__,
        released_information=[],
        chain_status={},
        generated_at_utc="2026-07-31T13:00:00Z",
    )
    missing = tmp_path / "does_not_exist"
    with pytest.raises(FileNotFoundError):
        ri.write_failure_report(missing, rendered)
