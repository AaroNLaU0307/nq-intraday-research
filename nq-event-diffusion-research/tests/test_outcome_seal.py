"""TASK 12 -- outcome sealing. Synthetic bundles only; no real outcome exists."""
from __future__ import annotations

import json

import pytest

from r1.errors import AuthorityError, OutcomeExposureError
from r1.outcome_seal import (BUILD_OUTPUT, OWNER_AUTHORIZED_REVEAL,
                             POWER_GATE_OUTPUT, SEALED_R1_OUTCOME,
                             read_power_gate_output, reveal, seal_outcome)

PAYLOAD = {"records": [{"date_et": "2015-01-02", "y_net_usd": 4.2}],
           "mean_y_net_usd": 4.2}          # fabricated


def test_the_four_output_classes_are_distinct(tmp_path):
    handles = {cls: seal_outcome(PAYLOAD, tmp_path / cls, output_class=cls)
               for cls in (BUILD_OUTPUT, POWER_GATE_OUTPUT, SEALED_R1_OUTCOME)}
    assert {h.output_class for h in handles.values()} == {
        BUILD_OUTPUT, POWER_GATE_OUTPUT, SEALED_R1_OUTCOME}
    for h in handles.values():
        assert h.path.exists()


def test_the_handle_never_carries_a_value(tmp_path):
    h = seal_outcome(PAYLOAD, tmp_path, output_class=SEALED_R1_OUTCOME)
    text = repr(h) + str(h)
    assert "4.2" not in text
    assert "y_net" not in text
    assert "values withheld" in text
    assert h.sha256 and h.n_records == 1


def test_sealed_outcome_is_written_not_returned(tmp_path):
    h = seal_outcome(PAYLOAD, tmp_path, output_class=SEALED_R1_OUTCOME)
    on_disk = json.loads(h.path.read_text(encoding="utf-8"))
    assert on_disk["payload"]["mean_y_net_usd"] == 4.2     # it IS persisted
    assert not hasattr(h, "payload")                        # but not handed back


def test_reveal_requires_an_owner_token(tmp_path):
    h = seal_outcome(PAYLOAD, tmp_path, output_class=SEALED_R1_OUTCOME)
    with pytest.raises(OutcomeExposureError, match="explicit Aaron"):
        reveal(h)
    with pytest.raises(OutcomeExposureError):
        reveal(h, owner_authorization="please")
    data = reveal(h, owner_authorization="REVEAL_AUTHORIZED_BY_AARON:2026-09-17")
    assert data["output_class"] == OWNER_AUTHORIZED_REVEAL
    assert data["payload"]["mean_y_net_usd"] == 4.2


def test_power_gate_output_is_readable_before_any_reveal(tmp_path):
    h = seal_outcome({"s_hat": 80.0, "mde_80": 16.5}, tmp_path,
                     output_class=POWER_GATE_OUTPUT)
    data = read_power_gate_output(h)
    assert data["payload"]["s_hat"] == 80.0
    assert reveal(h)["payload"]["mde_80"] == 16.5          # no token needed


def test_a_sealed_outcome_is_not_readable_through_the_gate_door(tmp_path):
    h = seal_outcome(PAYLOAD, tmp_path, output_class=SEALED_R1_OUTCOME)
    with pytest.raises(OutcomeExposureError, match="not readable"):
        read_power_gate_output(h)


def test_a_real_outcome_needs_s3_authorization(tmp_path):
    with pytest.raises(AuthorityError, match="S3 authorization"):
        seal_outcome(PAYLOAD, tmp_path, output_class=SEALED_R1_OUTCOME,
                     synthetic=False)
    h = seal_outcome(PAYLOAD, tmp_path, output_class=SEALED_R1_OUTCOME,
                     synthetic=False,
                     s3_authorization="S3_RUN_AUTHORIZED_BY_AARON:test")
    assert h.synthetic is False


def test_unknown_output_class_is_refused(tmp_path):
    with pytest.raises(OutcomeExposureError, match="unknown output class"):
        seal_outcome(PAYLOAD, tmp_path, output_class="WHATEVER")


def test_nothing_is_printed_by_sealing(tmp_path, capsys):
    seal_outcome(PAYLOAD, tmp_path, output_class=SEALED_R1_OUTCOME)
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err == ""


def test_bundle_records_its_exposure_note(tmp_path):
    h = seal_outcome(PAYLOAD, tmp_path, output_class=SEALED_R1_OUTCOME)
    data = json.loads(h.path.read_text(encoding="utf-8"))
    assert "Owner-authorized reveal" in data["exposure_note"]
    assert data["synthetic"] is True
