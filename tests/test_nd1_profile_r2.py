"""`ND1_RECOMMENDED_PROFILE_R2` — the correction-only proposal.

Separate module on purpose: these assert facts about decision-packet
§D.11, which lands in the PROPOSAL commit, while the engineering-repair
commit must be independently green on its own tree.

R2 exists because R1's §D.3.2 P3 contract contradicts its own §D.3.3
state diagram twice. The code implements the diagram reading; no
ratified profile covers it literally. Until Aaron ratifies R2 that gap
is real and stated, not papered over — which is why every assertion here
is about the PROPOSAL's shape, and none of them claims it is in force.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

from itsf.mc import supplement_contract as sc

REPO = Path(__file__).resolve().parents[1]
PACKET = REPO / "ops" / "DECISION_PACKET_N00_AND_ND1.md"
RATIFICATION = REPO / "ops" / "ND1_PROFILE_RATIFICATION.md"

APPROVED_PROFILE_SHA256 = (
    "0a08319a408f068ce4c92f93c2c4c39e409937dddfd0ef9f7af43618c70b50a5")


def _packet() -> str:
    return PACKET.read_bytes().decode("utf-8")


# ===========================================================================
# 8. the correction-only R2 proposal
# ===========================================================================

R2_PROFILE_ID = "ND1_RECOMMENDED_PROFILE_R2"


def _profile_body(tag: str) -> str:
    text = _packet()
    b, e = f"BEGIN_{tag}\n", f"END_{tag}\n"
    return text[text.index(b) + len(b):text.index(e)]


def test_r2_is_correction_only_against_r1_line_by_line():
    """R2 claims to inherit R1 verbatim except for the P3 correction.
    That is checked by DIFFING the two canonical bodies, not by reading
    the claim."""
    r1 = _profile_body("ND1_RECOMMENDED_PROFILE_R1").splitlines()
    r2 = _profile_body(R2_PROFILE_ID).splitlines()
    removed = [l for l in r1 if l not in r2]
    added = [l for l in r2 if l not in r1]
    assert removed == [
        "PROFILE_ID=ND1_RECOMMENDED_PROFILE_R1",
        "RECOMMENDED_GRAMMAR_P3=ADOPT_AS_WRITTEN",
    ], removed
    assert added == [
        "PROFILE_ID=ND1_RECOMMENDED_PROFILE_R2",
        "RECOMMENDED_GRAMMAR_P3=ADOPT_AS_CORRECTED_BY_R2",
        "RECOMMENDED_P3_PERMITTED_PREDECESSOR=P2|F1",
        "RECOMMENDED_P3_PERMITTED_SUCCESSOR=P4|A1|F2",
    ], added
    assert len([l for l in r2 if l in r1]) == 47


def test_r2_digest_recomputes_from_the_document():
    body = _profile_body(R2_PROFILE_ID)
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    assert f"PROFILE_SHA256={digest}" in _packet()


def test_the_packet_still_carries_r2_as_a_proposal_and_spares_r1():
    """RATIFIED 2026-08-23, and the DOCUMENT deliberately still reads
    `PROPOSED_NOT_EFFECTIVE`.

    That is not staleness. `APPROVAL_BINDS_DOC_HEAD` binds the commit that
    CARRIES the profile bytes; editing this document would move that commit
    and void the binding the approval was just made against. So the
    ratification lives in `ND1_PROFILE_RATIFICATION.md` §8 and the packet
    keeps the proposal shape — exactly as R1's §D.10.1 block still reads
    UNRESOLVED while R1 is in force."""
    text = _packet()
    assert "PROFILE_ID=ND1_RECOMMENDED_PROFILE_R2\nSTATUS=PROPOSED_NOT_EFFECTIVE" \
        in text.replace("\r", "")
    assert "R1_STATUS=RATIFIED_AND_STILL_EFFECTIVE" in text
    assert "R1_SUPERSEDED=NO" in text
    assert "R1_INVALIDATED=NO" in text
    # the R1 block itself is untouched
    r1_digest = hashlib.sha256(
        _profile_body("ND1_RECOMMENDED_PROFILE_R1").encode("utf-8")).hexdigest()
    assert r1_digest == APPROVED_PROFILE_SHA256


def test_r2_corrects_exactly_the_two_p3_contradictions_the_code_implements():
    """R2 exists to make the DOCUMENT say what the code already does. The
    two must agree, or R2 is correcting the wrong thing.

    SUPERSEDED FOR THE SUCCESSOR LIST, 2026-08-27. R3 was ratified and adds
    CR1 to P3's successors. R2's correction was not wrong — it was complete
    for its time, and R3 EXTENDS it. So the assertion below is written as
    "R2's three, plus whatever later ratified revisions added", rather than
    being edited to a new literal that would erase the distinction between
    a correction and a supersession.

    The R2 profile block itself still says `P4|A1|F2` and must: it is
    approved by digest and nothing may edit it.
    """
    body = _profile_body(R2_PROFILE_ID)
    assert "RECOMMENDED_P3_PERMITTED_PREDECESSOR=P2|F1" in body
    assert "RECOMMENDED_P3_PERMITTED_SUCCESSOR=P4|A1|F2" in body
    assert sc.EVENTS["P3"].predecessors == ("P2", "F1")
    successors = sc.EVENTS["P3"].successors
    assert successors[:3] == ("P4", "A1", "F2"), (
        "R2's three P3 successors must still lead the tuple in order; a "
        "later revision may extend the list, never rewrite it")
    assert set(successors) - {"P4", "A1", "F2"} <= {"CR1"}, (
        "P3 gained a successor no ratified revision declares: %r"
        % (sorted(set(successors) - {"P4", "A1", "F2", "CR1"}),))


def test_both_profiles_are_ratified_and_the_record_names_the_bytes():
    """R2 was ratified 2026-08-23. Both approvals must be findable BY
    DIGEST in the record, because a ratification that does not name bytes
    covers nothing."""
    text = _packet()
    assert text.count("AARON_ND1_PROFILE_RATIFICATION_V1") >= 1
    assert text.count("AARON_ND1_PROFILE_RATIFICATION_V2\n"
                      "STATUS=PROPOSED_NOT_EFFECTIVE") == 1
    ratified = RATIFICATION.read_bytes().decode("utf-8")
    assert f"APPROVED_PROFILE_SHA256={APPROVED_PROFILE_SHA256}" in ratified
    r2_digest = hashlib.sha256(
        _profile_body(R2_PROFILE_ID).encode("utf-8")).hexdigest()
    assert f"APPROVED_PROFILE_SHA256={r2_digest}" in ratified, \
        "the R2 approval does not name the bytes it approved"
    assert "ND1_PROFILE_R2_RATIFICATION=VALID" in ratified
    assert "APPROVAL_BINDS_DOC_HEAD=c56286b684b03d7544db9db16b59b5443182f9e6" \
        in ratified


def test_the_r2_record_discloses_that_aaron_did_not_send_the_three_lines():
    """Aaron replied "批准 R2" — two words, not the three-line block. The
    id/digest/head values were the builder's, put to him and approved by
    reference. A reader must be able to see that distinction, or the record
    would imply he typed bytes he never typed."""
    ratified = RATIFICATION.read_bytes().decode("utf-8")
    assert "批准 R2" in ratified
    assert "不是**三行块本身" in ratified or "不是三行块本身" in ratified


def test_every_open_field_in_the_packet_is_unresolved():
    text = _packet()
    fields = re.findall(r"^(APPROVED_[A-Z0-9_]+|APPROVAL_[A-Z0-9_]+)=(.+)$",
                        text, re.M)
    assert len(fields) == 6, fields          # 3 consumed V1 + 3 open V2
    for name, value in fields:
        assert value.split("#")[0].strip() == "UNRESOLVED", (name, value)
