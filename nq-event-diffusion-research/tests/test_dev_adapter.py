"""The Development-data adapter: every fail-closed branch, on fixtures and mocks.

**No real R1 event price is read anywhere in this file.** The archive is a
handful of tiny JSONL records with fabricated prices, under a fake manifest;
the DBN branch is exercised through a monkeypatched decoder.
"""
from __future__ import annotations

import hashlib
import json

import pytest

from r1 import dev_adapter
from r1.dev_adapter import (FIXED_PRICE_SCALE, DevelopmentDataAdapter,
                            RawRecord, decode_jsonl_fixture)
from r1.errors import AuthorityError, R1Error, RoleError, SealIdentityError
from r1.roles import DataRole

# 2015-06-05 08:29 ET == 12:29 UTC (EDT, UTC-4)
NS = 1_000_000_000
BASE_NS = 1_433_507_340 * NS          # 2015-06-05T12:29:00Z


def _rec(offset_min: int, price: float, volume: int = 5) -> dict:
    p = int(price * FIXED_PRICE_SCALE)
    return {"ts_event": BASE_NS + offset_min * 60 * NS, "open": p,
            "high": p + FIXED_PRICE_SCALE, "low": p - FIXED_PRICE_SCALE,
            "close": p, "volume": volume}


def _archive(tmp_path, records, *, filename="NQ.ohlcv-1m.jsonl",
             break_manifest_hash=False, extra_file=False):
    job = tmp_path / "job"
    job.mkdir()
    data = job / filename
    data.write_text("\n".join(json.dumps(r) for r in records) + "\n",
                    encoding="utf-8")
    digest = hashlib.sha256(data.read_bytes()).hexdigest()
    if break_manifest_hash:
        digest = "0" * 64
    files = [{"filename": data.name, "hash": f"sha256:{digest}"}]
    if extra_file:
        stray = job / "stray.ohlcv-1m.jsonl"
        stray.write_text("\n", encoding="utf-8")
    manifest = job / "manifest.json"
    manifest.write_text(json.dumps({"files": files}, indent=2), encoding="utf-8")
    return job, hashlib.sha256(manifest.read_bytes()).hexdigest()


def _adapter(job, manifest_sha, **kw):
    kw.setdefault("glob", "*.ohlcv-1m.jsonl")
    return DevelopmentDataAdapter(job, expected_manifest_sha256=manifest_sha,
                                  **kw)


# ---------------------------------------------------------------- happy path
def test_adapter_decodes_a_tiny_fixture_archive(tmp_path):
    job, man = _archive(tmp_path, [_rec(0, 100.0), _rec(2, 101.0),
                                   _rec(4, 100.5)])
    a = _adapter(job, man)
    bars = a.bars_for("2015-06-05")
    assert sorted(bars) == [8 * 60 + 29, 8 * 60 + 31, 8 * 60 + 33]
    assert bars[8 * 60 + 29].close == pytest.approx(100.0)
    assert bars[8 * 60 + 31].close == pytest.approx(101.0)
    assert bars[8 * 60 + 33].open == pytest.approx(100.5)
    assert bars[8 * 60 + 29].volume == 5


def test_adapter_reports_its_identity_without_prices(tmp_path):
    job, man = _archive(tmp_path, [_rec(0, 100.0)])
    ident = _adapter(job, man).identity()
    assert ident["role"] == "development_signal"
    assert ident["n_files"] == 1
    assert len(ident["files_digest_rollup_sha256"]) == 64
    assert ident["window_start"] == "2010-06-06"
    assert "price" not in json.dumps(ident).lower()


def test_adapter_satisfies_the_bar_source_contract(tmp_path, contract):
    from r1.bars import SignalWindow
    job, man = _archive(tmp_path, [_rec(0, 100.0), _rec(2, 101.0)])
    a = _adapter(job, man)
    w = SignalWindow(a, "2015-06-05", contract)
    assert w.require(contract.pre_release_anchor_minute).close == \
        pytest.approx(100.0)
    assert a.has_date("2015-06-05")
    assert a.dates == ("2015-06-05",)


# ---------------------------------------------------------------- fail closed
def test_wrong_role_refuses_before_any_file_is_opened(tmp_path, monkeypatch):
    import builtins
    opened: list = []
    real_open = builtins.open
    monkeypatch.setattr(builtins, "open",
                        lambda *a, **k: (opened.append(a), real_open(*a, **k))[1])
    for role in (DataRole.INTERNAL_VALIDATION_SIGNAL, DataRole.PHYSICAL_LOCKBOX):
        with pytest.raises(RoleError):
            DevelopmentDataAdapter(tmp_path, expected_manifest_sha256="x",
                                   data_role=role)
    assert opened == []


def test_cost_calibration_role_is_not_the_development_source(tmp_path):
    with pytest.raises(AuthorityError, match="Development signal role"):
        DevelopmentDataAdapter(tmp_path, expected_manifest_sha256="x",
                               data_role=DataRole.EXECUTION_COST_CALIBRATION)


def test_unknown_role_fails_closed(tmp_path):
    with pytest.raises(RoleError, match="unknown data role"):
        DevelopmentDataAdapter(tmp_path, expected_manifest_sha256="x",
                               data_role="final_evaluation")


def test_wrong_manifest_identity_refuses(tmp_path):
    job, man = _archive(tmp_path, [_rec(0, 100.0)])
    with pytest.raises(SealIdentityError, match="manifest identity"):
        _adapter(job, "f" * 64)


def test_missing_directory_and_missing_manifest_refuse(tmp_path):
    with pytest.raises(R1Error, match="data directory not found"):
        _adapter(tmp_path / "nope", "0" * 64)
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(R1Error, match="vendor manifest not found"):
        _adapter(empty, "0" * 64)


def test_file_hash_mismatch_refuses(tmp_path):
    job, man = _archive(tmp_path, [_rec(0, 100.0)], break_manifest_hash=True)
    with pytest.raises(SealIdentityError, match="digest mismatch"):
        _adapter(job, man)


def test_file_absent_from_the_manifest_refuses(tmp_path):
    job, man = _archive(tmp_path, [_rec(0, 100.0)], extra_file=True)
    with pytest.raises(SealIdentityError, match="absent from the vendor manifest"):
        _adapter(job, man)


def test_no_data_files_refuses(tmp_path):
    job = tmp_path / "job"
    job.mkdir()
    (job / "manifest.json").write_text(json.dumps({"files": []}),
                                       encoding="utf-8")
    man = hashlib.sha256((job / "manifest.json").read_bytes()).hexdigest()
    with pytest.raises(R1Error, match="no data files"):
        _adapter(job, man)


def test_malformed_manifest_refuses(tmp_path):
    job = tmp_path / "job"
    job.mkdir()
    (job / "x.ohlcv-1m.jsonl").write_text("\n", encoding="utf-8")
    (job / "manifest.json").write_text(json.dumps({"entries": []}),
                                       encoding="utf-8")
    man = hashlib.sha256((job / "manifest.json").read_bytes()).hexdigest()
    with pytest.raises(R1Error, match="malformed"):
        _adapter(job, man)


def test_malformed_schema_refuses(tmp_path):
    bad = _rec(0, 100.0)
    bad.pop("volume")
    job, man = _archive(tmp_path, [bad])
    with pytest.raises(R1Error, match="malformed schema"):
        _adapter(job, man).bars_for("2015-06-05")


def test_malformed_record_line_refuses(tmp_path):
    job = tmp_path / "job"
    job.mkdir()
    data = job / "x.ohlcv-1m.jsonl"
    data.write_text("{not json}\n", encoding="utf-8")
    digest = hashlib.sha256(data.read_bytes()).hexdigest()
    (job / "manifest.json").write_text(
        json.dumps({"files": [{"filename": data.name,
                               "hash": f"sha256:{digest}"}]}), encoding="utf-8")
    man = hashlib.sha256((job / "manifest.json").read_bytes()).hexdigest()
    with pytest.raises(R1Error, match="malformed record"):
        _adapter(job, man).bars_for("2015-06-05")


def test_duplicate_timestamp_refuses(tmp_path):
    job, man = _archive(tmp_path, [_rec(0, 100.0), _rec(0, 100.5)])
    with pytest.raises(R1Error, match="duplicate record"):
        _adapter(job, man).bars_for("2015-06-05")


def test_timestamp_outside_the_role_window_refuses(tmp_path):
    """A record past the grant window poisons the whole archive, not just its
    own date: the adapter refuses rather than quietly dropping it."""
    outside = _rec(0, 100.0)
    outside["ts_event"] = 1_735_000_000 * NS          # 2024-12-24, past the window
    job, man = _archive(tmp_path, [_rec(0, 100.0), outside])
    with pytest.raises(AuthorityError, match="outside the development_signal"):
        _adapter(job, man).bars_for("2015-06-05")


def test_requesting_a_date_outside_the_window_refuses(tmp_path):
    job, man = _archive(tmp_path, [_rec(0, 100.0)])
    a = _adapter(job, man)
    with pytest.raises(AuthorityError, match="outside the authorized"):
        a.bars_for("2024-01-02")
    with pytest.raises(AuthorityError):
        a.bars_for("2009-01-02")


def test_unsupported_file_format_refuses(tmp_path):
    job = tmp_path / "job"
    job.mkdir()
    data = job / "x.ohlcv-1m.parquet"
    data.write_bytes(b"\x00")
    digest = hashlib.sha256(data.read_bytes()).hexdigest()
    (job / "manifest.json").write_text(
        json.dumps({"files": [{"filename": data.name,
                               "hash": f"sha256:{digest}"}]}), encoding="utf-8")
    man = hashlib.sha256((job / "manifest.json").read_bytes()).hexdigest()
    with pytest.raises(R1Error, match="unsupported data format"):
        _adapter(job, man, glob="*.ohlcv-1m.parquet").bars_for("2015-06-05")


# ---------------------------------------------------------------- DBN branch
def test_dbn_branch_plumbing_via_a_mocked_decoder(tmp_path, monkeypatch):
    """The real branch's validation is exercised with a mock, not real data."""
    job = tmp_path / "job"
    job.mkdir()
    data = job / "NQ.ohlcv-1m.dbn.zst"
    data.write_bytes(b"not-a-real-dbn-file")
    digest = hashlib.sha256(data.read_bytes()).hexdigest()
    (job / "manifest.json").write_text(
        json.dumps({"files": [{"filename": data.name,
                               "hash": f"sha256:{digest}"}]}), encoding="utf-8")
    man = hashlib.sha256((job / "manifest.json").read_bytes()).hexdigest()

    fabricated = [RawRecord(BASE_NS, 100 * FIXED_PRICE_SCALE,
                            101 * FIXED_PRICE_SCALE, 99 * FIXED_PRICE_SCALE,
                            100 * FIXED_PRICE_SCALE, 7)]
    monkeypatch.setattr(dev_adapter, "decode_dbn", lambda p: iter(fabricated))
    a = DevelopmentDataAdapter(job, expected_manifest_sha256=man,
                               glob="*.ohlcv-1m.dbn.zst")
    bars = a.bars_for("2015-06-05")
    assert bars[8 * 60 + 29].close == pytest.approx(100.0)
    assert bars[8 * 60 + 29].volume == 7


def test_the_decoder_is_imported_lazily():
    """A machine without `databento` can still load, test and audit R1."""
    import ast
    import inspect
    tree = ast.parse(inspect.getsource(dev_adapter))
    top_level = {n.names[0].name for n in tree.body if isinstance(n, ast.Import)}
    assert "databento" not in top_level
    assert "pandas" not in top_level


def test_fixture_decoder_skips_blank_lines(tmp_path):
    p = tmp_path / "x.jsonl"
    p.write_text("\n" + json.dumps(_rec(0, 100.0)) + "\n\n", encoding="utf-8")
    assert len(list(decode_jsonl_fixture(p))) == 1


def test_real_bar_source_gate_still_blocks_s2(tmp_path):
    from r1.bars import DevelopmentBarSource
    job, man = _archive(tmp_path, [_rec(0, 100.0)])
    with pytest.raises(AuthorityError, match="NOT authorized in S2"):
        DevelopmentBarSource(job, expected_manifest_sha256=man)
    with pytest.raises(AuthorityError, match="manifest identity"):
        DevelopmentBarSource(job, s3_authorization="S3_RUN_AUTHORIZED_BY_AARON:x")


def test_the_adapter_cannot_reach_the_outcome_path(tmp_path, contract):
    """Implemented, and still unable to produce an R1 outcome in S2."""
    from r1.pipeline import run_study
    from r1.signal import apply_e4
    job, man = _archive(tmp_path, [_rec(0, 100.0), _rec(2, 101.0),
                                   _rec(4, 100.5), _rec(60, 103.0)])
    a = _adapter(job, man)
    with pytest.raises(AuthorityError, match="S2 BUILD"):
        apply_e4(a, ["2015-06-05"], contract)
    with pytest.raises(AuthorityError, match="S3 authorization"):
        run_study(a, ["2015-06-05"], contract, run_dir=tmp_path / "run")
