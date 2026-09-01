"""`run_c_build_2` — seal, stage, and classify what that produced.

WHAT WAS ACTUALLY MISSING. Not the sealing mechanism: it existed in full,
re-deriving from the authority and calling `resolve_partial` for staging.
What was missing was the layer that turns its refusal into an outcome a gate
can classify -- what `run_c_build` already is to the row builder.

THE TWO OWNERS. A seal refusal belongs to a gate (Router A) or to Router B,
and BD-1 ruled that two codes get no gate at all. The producer asks WHO owns
it before asking WHICH gate, and both orders are exercised here, because
asking for the gate first raises `ClassificationError` on a Router B code --
and a caller who swallowed that would hand a ruled no-gate code a gate.

THE GREEN-GATE TRAP IS EXECUTED, NOT WARNED ABOUT. When Router B owns the
refusal no gate names it, so all five C_BUILD gates go green over a seal that
did not happen. That is the ruled design, and the way to keep it from
becoming a surprise is a test that performs it.

REAL WHERE IT CAN BE. The clean path and the seal-conflict path drive the
genuine producer over a real directory. Only the Router B branch is reached
with a stubbed refusal, because the two codes that route there cannot be
provoked through the public factory -- and the thing under test there is the
routing, not the sealer.
"""

import hashlib
import unittest
from pathlib import Path
from unittest import mock

import pytest

from itsf.mc import day_strata_classify as dsc
from itsf.mc import day_strata_pipeline as pipe
from itsf.mc import day_strata_supplement as dss
from itsf.mc import supplement_production as sp
from itsf.mc import supplement_runner as sr

import test_mc_supplement_provenance_battery as fx

from _pytest.fixtures import FixtureFunctionDefinition as _FixtureDef

_REEXPORTED = []
for _name in dir(fx):
    _obj = getattr(fx, _name)
    if isinstance(_obj, _FixtureDef):
        globals()[_name] = _obj
        _REEXPORTED.append(_name)
assert "prod" in _REEXPORTED and "authority" in _REEXPORTED, (
    "the fixture re-export found %r; it is matching nothing" % (_REEXPORTED,))


def _seal(product, authority, prod, out):
    return pipe.run_c_build_2(product=product, out_dir=out,
                              authority=authority, prepared=prod,
                              incident_id=fx.INC)


def _product(authority, prod):
    return sp.build_supplement_from_authority(
        authority, prod, fx._rows(authority.expected_day_set))


def test_the_clean_path_seals_and_reports_ok(prod, authority, tmp_path):
    out = tmp_path / "seal"
    out.mkdir()
    result = _seal(_product(authority, prod), authority, prod, out)

    assert result.local_seal_ok is True
    assert result.router_b_code == ""
    assert result.outcome.failure is None
    sealed = out / dss.SUPPLEMENT_FILENAME
    assert hashlib.sha256(sealed.read_bytes()).hexdigest() == \
        result.local_seal_sha256
    assert sorted(p.name for p in out.iterdir()) == [dss.SUPPLEMENT_FILENAME]


def test_the_gate_classifies_the_clean_outcome(prod, authority, tmp_path):
    """The point of returning a `CBuildOutcome` at all."""
    out = tmp_path / "seal"
    out.mkdir()
    result = _seal(_product(authority, prod), authority, prod, out)
    ctx = sr.GateContext(supplement_id=fx.SID, head_commit="0" * 40,
                         registry_text="", runs_root=None, archive_root=None,
                         c_build_outcome=result.outcome)
    assert sr.GATES["seal_staging_partial"](ctx) is None


def test_a_seal_conflict_is_reported_under_its_own_gate(prod, authority,
                                                        tmp_path):
    """REAL, not stubbed: seal once, change the sealed bytes, seal again.
    A sealed supplement is never overwritten."""
    out = tmp_path / "seal"
    out.mkdir()
    product = _product(authority, prod)
    assert _seal(product, authority, prod, out).local_seal_ok is True
    sealed = out / dss.SUPPLEMENT_FILENAME
    sealed.write_bytes(sealed.read_bytes() + b" ")

    result = _seal(product, authority, prod, out)
    assert result.local_seal_ok is False
    assert result.router_b_code == ""
    failure = result.outcome.failure
    assert failure is not None
    assert failure.gate == "seal_staging_partial"
    assert failure.code == "supplement_seal_conflict"
    assert failure.stage == "C_BUILD"

    ctx = sr.GateContext(supplement_id=fx.SID, head_commit="0" * 40,
                         registry_text="", runs_root=None, archive_root=None,
                         c_build_outcome=result.outcome)
    with pytest.raises(sr.SupplementRunnerError) as caught:
        sr.GATES["seal_staging_partial"](ctx)
    assert "supplement_seal_conflict" in str(caught.value)


def test_the_conflict_destroyed_nothing(prod, authority, tmp_path):
    """`SILENT_DELETE_FORBIDDEN=YES`: a refusal must leave the bytes it
    refused about."""
    out = tmp_path / "seal"
    out.mkdir()
    product = _product(authority, prod)
    _seal(product, authority, prod, out)
    sealed = out / dss.SUPPLEMENT_FILENAME
    tampered = sealed.read_bytes() + b" "
    sealed.write_bytes(tampered)
    _seal(product, authority, prod, out)
    assert sealed.read_bytes() == tampered


class TestTheTwoOwners(unittest.TestCase):
    """Router A and Router B, and the order the producer asks in."""

    def _raise(self, code, out):
        exc = sp.SupplementProductionError(code, "stubbed")
        with mock.patch.object(sp, "seal_supplement_production",
                               side_effect=exc):
            return pipe.run_c_build_2(product=object(), out_dir=out,
                                      authority=object(), prepared=object(),
                                      incident_id=fx.INC)

    def test_a_router_b_refusal_leaves_the_gates_green(self):
        """THE TRAP, PERFORMED. No gate names these codes -- that is BD-1's
        ruling -- so the five gates pass over a seal that never happened.
        A caller reading only the gates has not read the answer, which is
        why `local_seal_ok` is returned beside them."""
        for code in dsc.ROUTER_B_SEAL_CODES:
            with self.subTest(code=code):
                result = self._raise(code, Path("."))
                self.assertFalse(result.local_seal_ok)
                self.assertEqual(code, result.router_b_code)
                self.assertIsNone(result.outcome.failure)

                ctx = sr.GateContext(
                    supplement_id=fx.SID, head_commit="0" * 40,
                    registry_text="", runs_root=None, archive_root=None,
                    c_build_outcome=result.outcome)
                for gate in ("row_schema_blind", "day_set_exact",
                             "rows_digest_recompute", "seal_staging_partial"):
                    self.assertIsNone(sr.GATES[gate](ctx), gate)

    def test_router_b_owns_what_router_b_answers(self):
        """And the answer is a refusal, so the green gates above are not the
        end of the story -- Router B is."""
        with self.assertRaises(sr.SupplementRunnerError) as caught:
            sr.decide_after_seal(local_seal_ok=False, archive_report=None)
        self.assertIn("nothing was sealed", str(caught.exception))

    def test_every_router_a_code_lands_on_the_gate_its_table_names(self):
        for code, (stage, gate) in dsc.STAGE_GATE_OF_SEAL_CODE.items():
            with self.subTest(code=code):
                result = self._raise(code, Path("."))
                self.assertFalse(result.local_seal_ok)
                self.assertEqual("", result.router_b_code)
                self.assertEqual(gate, result.outcome.failure.gate)
                self.assertEqual(stage, result.outcome.failure.stage)

    def test_an_unmapped_code_raises_rather_than_acquiring_a_router(self):
        """Fail-closed, and it is the whole point of BD-1: a code nobody
        classified must not quietly become somebody's."""
        with self.assertRaises(dsc.ClassificationError):
            self._raise("production_code_no_table_has_ever_seen", Path("."))

    def test_an_exception_with_no_code_is_not_swallowed(self):
        with mock.patch.object(sp, "seal_supplement_production",
                               side_effect=RuntimeError("boom")):
            with self.assertRaises(RuntimeError):
                pipe.run_c_build_2(product=object(), out_dir=Path("."),
                                   authority=object(), prepared=object(),
                                   incident_id=fx.INC)


if __name__ == "__main__":
    unittest.main()
