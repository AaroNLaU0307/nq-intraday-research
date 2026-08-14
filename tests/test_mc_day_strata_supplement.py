"""GRID Option-B blind supplemental DAY_STRATA sealer — behavior battery
(R2.3 lane S2; synthetic fixtures ONLY, tmp_path ONLY).

Covers the day_strata_supplement contract end to end:

  * positive chain: build -> seal -> re-read equals -> digest stable ->
    idempotent reseal;
  * DEFAULT-REFUSE production entry (deterministic refusal + lookalike
    token named-and-refused, mirroring consumer.authorize_real_mc);
  * day-universe exactness against the sealed authority frozenset
    (few days / fake extra day / duplicate day / post-build drift);
  * DR-2/DR-6 ruled vocabularies (vol + event), year consistency, and
    the BLIND no-outcome guarantee (any extra row field refuses — a
    "pnl" can never ride along);
  * binding schema exactness + 40/64-hex malformation refusals;
  * seal integrity: synchronized row+digest tamper cannot replace a
    prior seal (conflict), mismatching `.partial` residue refuses,
    byte-identical `.partial` residue is promoted.

No sealed S0 content is read anywhere; every date/stratum below is
invented."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from itsf.mc import day_strata_supplement as dss

TRIAL = "S0-T001"
COMMIT = "a" * 40
DIGEST_A = "b" * 64
DIGEST_B = "c" * 64

# five synthetic days spanning two years and every-corner strata usage
_DAYS = (
    ("2024-03-11", 2024, "T1", "none"),
    ("2024-03-12", 2024, "T2", "CPI"),
    ("2024-06-14", 2024, "T3", "FOMC"),
    ("2025-01-10", 2025, "vol_na", "NFP"),
    ("2025-05-02", 2025, "T2", "NA_multi_event"),
)


def _rows() -> list[dict]:
    return [{"trade_date": d, "year": y, "vol_stratum": v,
             "event_stratum": e} for d, y, v, e in _DAYS]


def _expected(rows=None) -> frozenset:
    return frozenset(r["trade_date"] for r in (rows or _rows()))


def _binding() -> dict:
    return {"trial_id": TRIAL, "authorized_commit": COMMIT,
            "day_universe_digest": DIGEST_A,
            "method_version": "mc-freeze-v1",
            "source_input_sha256": DIGEST_B}


def _build(rows=None, expected=None, binding=None) -> dict:
    return dss.build_day_strata_supplement(
        rows if rows is not None else _rows(),
        expected_day_set=expected if expected is not None else _expected(),
        binding=binding if binding is not None else _binding())


# --- positive chain ---------------------------------------------------------

def test_build_seal_reread_roundtrip(tmp_path):
    sup = _build()
    assert sup["schema"] == dss.SUPPLEMENT_SCHEMA
    assert sup["supplement_id"] == dss.SUPPLEMENT_ID
    assert sup["n_rows"] == len(_DAYS)
    # rows come back SORTED by trade_date as a tuple of exact-4-key dicts
    dates = [r["trade_date"] for r in sup["rows"]]
    assert dates == sorted(dates)
    assert all(set(r) == set(dss.ROW_FIELDS) for r in sup["rows"])
    sha = dss.seal_supplement(sup, tmp_path)
    sealed = tmp_path / dss.SUPPLEMENT_FILENAME
    raw = sealed.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == sha
    back = json.loads(raw.decode("utf-8"))
    assert back["rows_digest"] == sup["rows_digest"]
    assert back["binding"] == _binding()
    assert [tuple(sorted(r.items())) for r in back["rows"]] == \
        [tuple(sorted(r.items())) for r in sup["rows"]]
    # no staging debris survives a successful seal
    assert not (tmp_path / (dss.SUPPLEMENT_FILENAME
                            + dss.PARTIAL_SUFFIX)).exists()


def test_digest_deterministic_and_input_order_independent():
    a = _build()
    b = _build(rows=list(reversed(_rows())))
    assert a["rows_digest"] == b["rows_digest"]
    assert a["rows"] == b["rows"]


def test_idempotent_reseal_noop(tmp_path):
    sup = _build()
    sha1 = dss.seal_supplement(sup, tmp_path)
    raw1 = (tmp_path / dss.SUPPLEMENT_FILENAME).read_bytes()
    sha2 = dss.seal_supplement(_build(), tmp_path)   # fresh equal object
    raw2 = (tmp_path / dss.SUPPLEMENT_FILENAME).read_bytes()
    assert sha1 == sha2
    assert raw1 == raw2


def test_build_copies_rows_defensively():
    rows = _rows()
    sup = _build(rows=rows)
    rows[0]["vol_stratum"] = "T3"          # mutate the CALLER's input
    rows[0]["pnl"] = 123.0
    fresh = _build()                        # untouched input
    assert sup["rows_digest"] == fresh["rows_digest"]
    assert sup["rows"][0]["vol_stratum"] == "T1"


# --- production entry: DEFAULT REFUSE ---------------------------------------

def test_production_entry_deterministic_refusal():
    msgs = []
    for _ in range(2):
        with pytest.raises(dss.SupplementNotAuthorized) as ei:
            dss.run_supplement_production()
        msgs.append(str(ei.value))
    assert msgs[0] == msgs[1]               # deterministic, twice
    # the refusal must name the missing vocabulary AND the future
    # binding: exact candidate commit + supplement id + output root
    assert dss.SUPPLEMENT_AUTHORIZATION_EVENT in msgs[0]
    assert dss.SUPPLEMENT_ID in msgs[0]
    assert "commit" in msgs[0]
    assert "output root" in msgs[0]


def test_lookalike_token_named_and_refused():
    planted = ("## event\n**SUPPLEMENT_EXECUTION_AUTHORIZED** "
               "commit=deadbeef root=X\n")
    with pytest.raises(dss.SupplementNotAuthorized) as ei:
        dss.authorize_supplement(planted)
    msg = str(ei.value)
    assert "lookalike" in msg
    assert dss.SUPPLEMENT_AUTHORIZATION_EVENT in msg
    # and without the token the refusal stands too, minus the naming
    with pytest.raises(dss.SupplementNotAuthorized) as ei2:
        dss.authorize_supplement("")
    assert "lookalike" not in str(ei2.value)


# --- day-universe exactness --------------------------------------------------

def test_missing_day_refuses():
    with pytest.raises(dss.SupplementError) as ei:
        _build(rows=_rows()[:-1])           # one sealed day absent
    assert ei.value.code == "supplement_day_set_incomplete"


def test_fake_extra_day_refuses():
    rows = _rows() + [{"trade_date": "2025-07-04", "year": 2025,
                       "vol_stratum": "T1", "event_stratum": "none"}]
    with pytest.raises(dss.SupplementError) as ei:
        _build(rows=rows)                   # invented day, valid shape
    assert ei.value.code == "supplement_day_set_extra"


def test_duplicate_day_refuses():
    rows = _rows() + [dict(_rows()[0])]
    with pytest.raises(dss.SupplementError) as ei:
        _build(rows=rows)
    assert ei.value.code == "supplement_duplicate_day"


def test_expected_day_set_drift_after_build_refuses():
    baseline = _build()                     # builds fine vs the authority
    assert baseline["n_rows"] == len(_DAYS)
    # the authority frozenset drifts AFTER that build (one day swapped);
    # a rebuild of the SAME rows must refuse — missing is checked first
    drifted = (_expected() - {"2024-03-11"}) | {"2024-03-13"}
    with pytest.raises(dss.SupplementError) as ei:
        _build(expected=drifted)
    assert ei.value.code == "supplement_day_set_incomplete"


# --- row vocabulary / schema -------------------------------------------------

def test_vol_vocabulary_refuses():
    rows = _rows()
    rows[1]["vol_stratum"] = "T4"           # outside the DR-2 ruled set
    with pytest.raises(dss.SupplementError) as ei:
        _build(rows=rows)
    assert ei.value.code == "supplement_vol_vocabulary"


def test_event_vocabulary_refuses():
    rows = _rows()
    rows[2]["event_stratum"] = "GDP"        # outside the DR-6 ruled set
    with pytest.raises(dss.SupplementError) as ei:
        _build(rows=rows)
    assert ei.value.code == "supplement_event_vocabulary"


def test_year_mismatch_refuses():
    rows = _rows()
    rows[0]["year"] = 2023                  # trade_date says 2024
    with pytest.raises(dss.SupplementError) as ei:
        _build(rows=rows)
    assert ei.value.code == "supplement_year_mismatch"


@pytest.mark.parametrize("field,value", [
    ("pnl", 1.0), ("return_final", -0.2),
    ("oracle_flag", True), ("report_note", "x")])
def test_forbidden_extra_field_refuses(field, value):
    """The BLIND no-outcome guarantee: any key beyond the four
    structural ones refuses, whatever it is called."""
    rows = _rows()
    rows[3][field] = value
    with pytest.raises(dss.SupplementError) as ei:
        _build(rows=rows)
    assert ei.value.code == "supplement_forbidden_field"


def test_missing_row_key_refuses():
    rows = _rows()
    del rows[4]["vol_stratum"]
    with pytest.raises(dss.SupplementError) as ei:
        _build(rows=rows)
    assert ei.value.code == "supplement_row_schema"


# --- binding ----------------------------------------------------------------

def test_binding_schema_refuses_missing_and_extra():
    missing = _binding()
    del missing["method_version"]
    with pytest.raises(dss.SupplementError) as ei:
        _build(binding=missing)
    assert ei.value.code == "supplement_binding_schema"
    extra = _binding()
    extra["note"] = "ride-along"
    with pytest.raises(dss.SupplementError) as ei2:
        _build(binding=extra)
    assert ei2.value.code == "supplement_binding_schema"


@pytest.mark.parametrize("field,bad", [
    ("authorized_commit", "a" * 39),        # not 40-hex
    ("authorized_commit", "Z" * 40),        # not hex at all
    ("day_universe_digest", "b" * 63),      # not 64-hex
    ("source_input_sha256", 123)])          # not even a string
def test_binding_malformed_refuses(field, bad):
    binding = _binding()
    binding[field] = bad
    with pytest.raises(dss.SupplementError) as ei:
        _build(binding=binding)
    assert ei.value.code == "supplement_binding_malformed"


# --- seal integrity ---------------------------------------------------------

def test_synchronized_tamper_refused_on_conflict(tmp_path):
    """Mutate a row to another VALID stratum AND recompute rows_digest by
    hand: the tampered object is internally consistent, so only the
    never-overwrite seal boundary can stop it — and does."""
    dss.seal_supplement(_build(), tmp_path)          # the honest seal
    tampered = _build()
    rows = [dict(r) for r in tampered["rows"]]
    rows[0]["vol_stratum"] = "T3"                    # valid vocab, wrong fact
    tampered["rows"] = tuple(rows)
    tampered["rows_digest"] = dss.canonical_rows_digest(rows)
    with pytest.raises(dss.SupplementError) as ei:
        dss.seal_supplement(tampered, tmp_path)
    assert ei.value.code == "supplement_seal_conflict"
    # the honest seal is untouched
    back = json.loads((tmp_path / dss.SUPPLEMENT_FILENAME)
                      .read_bytes().decode("utf-8"))
    assert back["rows"][0]["vol_stratum"] == "T1"


def test_inconsistent_digest_refused_before_any_write(tmp_path):
    sup = _build()
    sup["rows_digest"] = "0" * 64            # digest no longer matches rows
    with pytest.raises(dss.SupplementError) as ei:
        dss.seal_supplement(sup, tmp_path)
    assert ei.value.code == "supplement_digest_mismatch"
    assert not (tmp_path / dss.SUPPLEMENT_FILENAME).exists()


def test_partial_residue_mismatch_refused(tmp_path):
    sup = _build()
    partial = tmp_path / (dss.SUPPLEMENT_FILENAME + dss.PARTIAL_SUFFIX)
    partial.write_bytes(b'{"schema": "garbage from a crashed attempt"}')
    with pytest.raises(dss.SupplementError) as ei:
        dss.seal_supplement(sup, tmp_path)
    assert ei.value.code == "supplement_partial_residue"
    assert not (tmp_path / dss.SUPPLEMENT_FILENAME).exists()
    assert partial.exists()                  # debris disclosed, not clobbered


def test_partial_residue_matching_promoted(tmp_path):
    sup = _build()
    intended = dss.canonical_supplement_bytes(sup)
    partial = tmp_path / (dss.SUPPLEMENT_FILENAME + dss.PARTIAL_SUFFIX)
    partial.write_bytes(intended)            # crash happened pre-replace
    sha = dss.seal_supplement(sup, tmp_path)
    final = tmp_path / dss.SUPPLEMENT_FILENAME
    assert final.read_bytes() == intended
    assert hashlib.sha256(intended).hexdigest() == sha
    assert not partial.exists()              # promoted, not copied
