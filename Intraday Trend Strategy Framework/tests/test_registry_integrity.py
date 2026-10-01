"""T-F13 and T-F15: registry integrity split into a current-dependency
check (tier B) and a history health check (tier C).

QROS-CF v2 §2.6 (DEC-0006 I3; converged F13, F15a).

T-F13 -- forged-but-legal rows are refused by name, not by grammar: a P5
whose attestation belongs to another run; an attestation that never
restates the sealed sha256 it claims to have verified; a witness that
names a different id; a verification row with no witness; a P3 after an
owner revocation; an F3 referencing a stale sequence.

T-F15 -- a defect in an OLD chain's evidence is reported by the history
check and does not make the current chain's check fail.

The two live-registry tests read through the boundary and write nothing.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tests"))

import test_mc_supplement_registry as T           # noqa: E402
from itsf.mc import registry_boundary as rb       # noqa: E402
from itsf.mc import registry_integrity as ri      # noqa: E402
from itsf.mc import supplement_contract as sc     # noqa: E402
from itsf.mc import supplement_registry as sreg   # noqa: E402

SID, SID2 = T.SID, T.SID2
UTC = "2026-09-07T00:00:00+00:00"
SEALED = "5" * 64


def _attestation(tmp_path, name, sid=SID, sealed=SEALED) -> tuple:
    root = tmp_path / "review" / f"{sid.lower()}-verifier"
    root.mkdir(parents=True, exist_ok=True)
    p = root / name
    p.write_text(f"# attestation\nSUPPLEMENT_ID={sid}\nsealed sha256 {sealed}\n"
                 "FORMAL_VERDICT=PASS\n", encoding="utf-8")
    return p, hashlib.sha256(p.read_bytes()).hexdigest()


def _witness(tmp_path, name, *, seq, sha, sid=SID, path=None, sealed=SEALED,
             previous=None, previous_sha=None, own_sha="a" * 64):
    d = tmp_path / "witness"
    d.mkdir(exist_ok=True)
    data = {"witness_of": "ops/SYNTHETIC_REGISTRY.md", "sha256": own_sha,
            "last_line": f"| {seq} | {UTC} | SUPPLEMENT_INDEPENDENTLY_VERIFIED "
                         f"| x | verifier | [{sid}] ... |",
            "attestation_sha256": sha, "supplement_id": sid,
            "sealed_sha256": sealed}
    if path is not None:
        data["attestation"] = str(path)
    if previous is not None:
        data["previous_witness"] = previous
        data["previous_sha256"] = previous_sha
    (d / name).write_text(json.dumps(data), encoding="utf-8")
    return d


def _chain_with_p5(sha, sid=SID, sealed=SEALED, reg=None):
    """P1 P2 P3 P4 P5 for `sid`; returns (reg, seq of the P5 row). The seq
    is READ BACK from the builder: only NUMBERED rows take a number."""
    reg = reg if reg is not None else T.Reg()
    for short in ("P1", "P2", "P3"):
        reg.add(short, sid)
    reg.add("P4", sid, fields={"sealed_sha256": sealed})
    reg.add("P5", sid, fields={"attestation_sha256": sha})
    return reg, int(reg.last_numbered[sid][0])


def _check(tmp_path, text, sid, wd):
    return ri.current_dependency_check(text, sid, witness_dir=wd,
                                       roots=(tmp_path / "review",))


# ---------------------------------------------------------------------------
# T-F13: bound, then forged one way at a time
# ---------------------------------------------------------------------------

def test_a_bound_verification_row_passes_the_current_check(tmp_path):
    att, sha = _attestation(tmp_path, "P5_ATTESTATION.md")
    reg, seq = _chain_with_p5(sha)
    wd = _witness(tmp_path, "W_P5.json", seq=seq, sha=sha, path=att)
    rep = _check(tmp_path, reg.text(), SID, wd)
    assert rep.ok, rep.problems
    assert any("binding of P5" in c for c in rep.checked)


def test_an_attestation_for_another_run_is_refused_by_name(tmp_path):
    att, sha = _attestation(tmp_path, "P5_ATTESTATION.md", sid=SID2)
    reg, seq = _chain_with_p5(sha)
    wd = _witness(tmp_path, "W_P5.json", seq=seq, sha=sha, path=att, sid=SID2)
    rep = _check(tmp_path, reg.text(), SID, wd)
    assert not rep.ok
    codes = {p.code for p in rep.problems}
    assert "attestation_supplement_id_mismatch" in codes, codes
    assert "witness_supplement_id_mismatch" in codes, codes


def test_an_attestation_that_never_restates_the_sealed_sha_is_refused(tmp_path):
    att, sha = _attestation(tmp_path, "P5_ATTESTATION.md", sealed="9" * 64)
    reg, seq = _chain_with_p5(sha)
    wd = _witness(tmp_path, "W_P5.json", seq=seq, sha=sha, path=att, sealed="9" * 64)
    rep = _check(tmp_path, reg.text(), SID, wd)
    codes = {p.code for p in rep.problems}
    assert "attestation_sealed_sha_mismatch" in codes, codes
    assert "witness_sealed_sha_mismatch" in codes, codes


def test_a_verification_row_without_a_witness_is_refused(tmp_path):
    _att, sha = _attestation(tmp_path, "P5_ATTESTATION.md")
    wd = tmp_path / "witness"
    wd.mkdir()
    reg, _seq = _chain_with_p5(sha)
    rep = _check(tmp_path, reg.text(), SID, wd)
    assert {p.code for p in rep.problems} == {"verification_witness_missing"}


def test_a_witness_for_a_different_row_does_not_bind(tmp_path):
    att, sha = _attestation(tmp_path, "P5_ATTESTATION.md")
    reg, _seq = _chain_with_p5(sha)
    wd = _witness(tmp_path, "W_P5.json", seq=99, sha=sha, path=att)
    rep = _check(tmp_path, reg.text(), SID, wd)
    assert "verification_witness_missing" in {p.code for p in rep.problems}


def test_an_attestation_whose_bytes_changed_is_refused(tmp_path):
    att, sha = _attestation(tmp_path, "P5_ATTESTATION.md")
    reg, seq = _chain_with_p5(sha)
    wd = _witness(tmp_path, "W_P5.json", seq=seq, sha=sha, path=att)
    att.write_text(att.read_text(encoding="utf-8") + "edited\n", encoding="utf-8")
    rep = _check(tmp_path, reg.text(), SID, wd)
    assert "attestation_file_missing_or_sha_mismatch" in {p.code for p in rep.problems}


def test_an_attestation_is_found_by_hash_when_the_witness_records_no_path(tmp_path):
    _att, sha = _attestation(tmp_path, "S001_P5_ATTESTATION.md")
    reg, seq = _chain_with_p5(sha)
    wd = _witness(tmp_path, "W_P5.json", seq=seq, sha=sha, path=None)
    rep = _check(tmp_path, reg.text(), SID, wd)
    assert rep.ok, rep.problems


def test_a_stale_f3_reference_is_a_chain_refusal(tmp_path):
    reg = T.Reg()
    reg.add("P1")
    reg.add("P2")
    reg.add("F3", fields={"supersedes_event_sequence": "77"})
    rep = ri.current_dependency_check(reg.text(), SID, witness_dir=tmp_path,
                                      roots=())
    assert not rep.ok and rep.problems[0].code == "chain_unresolvable"
    assert "f3_no_target_row" in rep.problems[0].detail


def test_a_start_after_an_owner_revocation_is_a_chain_refusal(tmp_path):
    reg = T.Reg()
    reg.add("P1")
    reg.add("P2")
    reg.add("P2S", fields={"reason_code": sreg.OWNER_REVOCATION,
                           "successor_authorized_commit": sreg.REVOCATION_NO_SUCCESSOR,
                           "incident_id": T.INC, "same_id_reauthorization": "YES"},
            actor=sc.ACTOR_AARON)
    reg.add("P3")
    rep = ri.current_dependency_check(reg.text(), SID, witness_dir=tmp_path,
                                      roots=())
    assert "p2s_to_p3_without_new_p2" in rep.problems[0].detail


def test_an_owner_hold_is_a_current_problem(tmp_path):
    reg = T.Reg()
    reg.add("P1")
    reg.add("P2")
    reg.raw(f"| 3 | {UTC} | OWNER_HOLD | {'c' * 40} | Aaron | [GLOBAL] reason: hold |")
    rep = ri.current_dependency_check(reg.text(), SID, witness_dir=tmp_path,
                                      roots=())
    assert {p.code for p in rep.problems} == {"owner_hold_in_force"}


# ---------------------------------------------------------------------------
# T-F15: history is reported, the current chain is not held by it
# ---------------------------------------------------------------------------

def test_a_gap_in_an_old_chains_evidence_does_not_hold_the_current_chain(tmp_path):
    old_att, old_sha = _attestation(tmp_path, "OLD_ATTESTATION.md", sid=SID)
    new_att, new_sha = _attestation(tmp_path, "NEW_ATTESTATION.md", sid=SID2)
    # the OLD chain (SID) has NO witness; the NEW chain (SID2) is bound
    reg, _old_seq = _chain_with_p5(old_sha, sid=SID)
    reg, new_seq = _chain_with_p5(new_sha, sid=SID2, reg=reg)
    wd = _witness(tmp_path, "W_NEW.json", seq=new_seq, sha=new_sha, sid=SID2,
                  path=new_att)
    text = reg.text()
    current = _check(tmp_path, text, SID2, wd)
    assert current.ok, current.problems
    history = ri.history_health(text, witness_dir=wd, roots=(tmp_path / "review",))
    assert not history.ok
    assert any(p.code == "verification_witness_missing" and p.supplement_id == SID
               for p in history.problems)


def test_the_witness_hash_chain_is_judged_by_content_then_by_name(tmp_path):
    wd = _witness(tmp_path, "W_A.json", seq=1, sha="a" * 64, own_sha="1" * 64)
    _witness(tmp_path, "W_B.json", seq=2, sha="b" * 64, previous="W_A.json",
             previous_sha="1" * 64, own_sha="2" * 64)
    assert ri.witness_chain_problems(wd) == ()
    # an uncertified append: the hash matches no witness at all
    _witness(tmp_path, "W_C.json", seq=3, sha="c" * 64, previous="W_B.json",
             previous_sha="0" * 64, own_sha="3" * 64)
    assert [p.code for p in ri.witness_chain_problems(wd)] == ["witness_chain_mismatch"]
    # a filing defect: the hash is W_B's but the name says W_A
    _witness(tmp_path, "W_D.json", seq=4, sha="d" * 64, previous="W_A.json",
             previous_sha="2" * 64, own_sha="4" * 64)
    codes = {p.code for p in ri.witness_chain_problems(wd)}
    assert "witness_previous_name_mismatch" in codes
    # a named predecessor that does not exist
    _witness(tmp_path, "W_E.json", seq=5, sha="e" * 64, previous="W_GONE.json",
             previous_sha="3" * 64, own_sha="5" * 64)
    assert "witness_chain_gap" in {p.code for p in ri.witness_chain_problems(wd)}


# ---------------------------------------------------------------------------
# the live registry, through the boundary, read-only
# ---------------------------------------------------------------------------

def test_the_latest_real_chain_is_bound_to_its_evidence():
    """Tier B on the live ledger: MC-DS-S004's P5 binds to a witness, to an
    attestation that hashes right, names the id and restates the sealed
    sha256 of the P4 it verified."""
    text = rb.read_snapshot().text
    rep = ri.current_dependency_check(text, "MC-DS-S004")
    assert rep.ok, rep.problems
    assert any("binding of P5" in c for c in rep.checked), rep.checked


@pytest.mark.governance
def test_every_real_verification_row_is_bound_and_the_hash_chain_is_intact():
    """Tier C on the live ledger. Two things MUST hold: every P5/F2v in the
    history binds to its witness and attestation, and every witness's
    previous_sha256 is the sha256 of some witness (no uncertified append).
    A failure here is a backlog row, never a hold on a run."""
    text = rb.read_snapshot().text
    rep = ri.history_health(text)
    assert len(rep.checked) >= 4, rep.checked
    integrity = [p for p in rep.problems
                 if p.code != "witness_previous_name_mismatch"]
    assert integrity == [], integrity


@pytest.mark.governance
@pytest.mark.xfail(strict=True, reason=(
    "BACKLOG B-20 (2026-09-07): WITNESS_T1_APPENDED_2026-09-05.json names "
    "WITNESS_P4_APPENDED_2026-09-05.json as its predecessor while its "
    "previous_sha256 is the post-F3 registry hash certified by "
    "WITNESS_F3_APPENDED_2026-09-05.json. Hash chain intact; the name pointer "
    "is a filing defect in an append-only witness that only Aaron may correct "
    "by a new witness. When corrected, this test XPASSes strictly and the "
    "marker is removed with the backlog row."))
def test_the_real_witness_name_pointers_all_match_their_hashes():
    rep = ri.witness_chain_problems()
    names = [p for p in rep if p.code == "witness_previous_name_mismatch"]
    assert names == [], names
