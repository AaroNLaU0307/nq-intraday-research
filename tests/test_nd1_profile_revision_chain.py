"""The profile revision chain, mechanised — because it never was.

FOUND BY A FRESH SOL, 2026-08-27, reviewing the R3 amendment proposal.
`ops/DECISION_PACKET_N00_AND_ND1.md` §D.11.3 states, in as many words:

    `tests/test_mc_supplement_integration.py` 逐行比对 R1 与 R2 并断言差异
    恰为这四行，所以「其余逐字继承」是可复算的事实，不是本节的自述。

Measured: that test file contains the string "R2" ZERO times, and no test
anywhere in the repository diffs R1 against R2. The sentence claiming the
correction-only property is "a computable fact, not this section's own
self-report" was itself a self-report.

Worse, and beyond what the reviewer said: that file pins
`APPROVED_PROFILE_ID = "ND1_RECOMMENDED_PROFILE_R1"` and has done since
before R2 was ratified on 2026-08-23. A superseded profile has been
asserted as the approved one, green the whole time.

This file closes both. It does NOT edit the older file's R1 assertions —
R1's record stands unaltered by ruling (`R1_STATUS=
SUPERSEDED_BY_R2_FOR_P3_ONLY`, "R1 记录本身仍在，未改写、未宣称无效"), and an
integrity check on R1's bytes remains correct. What was missing is
everything about R2, and the diff that makes "correction-only" checkable.

THE R3 TEST CHECKS A PROPOSAL, NOT A RATIFIED PROFILE. R3 is not approved
and this file must never imply that it is. What it asserts is narrower and
still worth having: the block in the proposal really is derived from R2's
bytes by exactly the edits the proposal claims. A proposal whose own
arithmetic is wrong should not reach a reviewer, and four of the five
deliveries so far failed for reasons a machine could have caught.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PACKET = REPO / "ops" / "DECISION_PACKET_N00_AND_ND1.md"
RATIFICATION = REPO / "ops" / "ND1_PROFILE_RATIFICATION.md"
PROPOSAL = REPO / "ops" / "PREP_ITEM6_ND1_R3_AMENDMENT_PROPOSAL.md"

R1_SHA256 = "0a08319a408f068ce4c92f93c2c4c39e409937dddfd0ef9f7af43618c70b50a5"
R2_SHA256 = "a3d40b7ce218294b75265622306bb91fc01081f98a0bacce8f8e86a3d3d8741d"
#: PROPOSED, not approved. Named so nobody mistakes it for a ratified value.
R3_PROPOSED_SHA256 = (
    "d40ad864571ec4773d68cdd4049b0eb8423da4cdf3fee7a145705f29c65f0d1d")

#: §D.11.3's claim, now checkable.
R2_EXPECTED_EDITS = 4
#: The R3 proposal's own claim, likewise.
R3_PROPOSED_EXPECTED_EDITS = 13


def _canonical(text, revision):
    """The bytes a profile's SHA-256 is taken over, exactly as the block
    itself specifies: the lines between the delimiters, excluding them,
    LF-terminated, UTF-8, verbatim."""
    b = f"BEGIN_ND1_RECOMMENDED_PROFILE_{revision}\n"
    e = f"END_ND1_RECOMMENDED_PROFILE_{revision}\n"
    assert b in text, f"no {revision} block"
    assert e in text, f"no {revision} terminator"
    return text[text.index(b) + len(b):text.index(e)]


def _lines(text, revision):
    return _canonical(text, revision).splitlines()


def _digest(text, revision):
    return hashlib.sha256(
        _canonical(text, revision).encode("utf-8")).hexdigest()


def _edit_count(before, after):
    """Lines present in one and not the other, counted as edits the way
    §D.11.3 counts them: a changed line is one edit, an added line is one
    edit. Order is irrelevant — the profile is a set of assignments."""
    changed = [ln for ln in after if ln not in before]
    removed = [ln for ln in before if ln not in after]
    # a "changed" line shows up as one removal plus one addition; the pairs
    # collapse to a single edit each, and unmatched additions stand alone.
    return len(changed), len(removed)


# ===========================================================================
# 1 — the ratified chain: R1 and R2
# ===========================================================================

def test_r1_bytes_still_hash_to_the_value_aaron_approved():
    assert _digest(PACKET.read_text(encoding="utf-8"), "R1") == R1_SHA256


def test_r2_bytes_still_hash_to_the_value_aaron_approved():
    """The gap: nothing checked this. R2 was ratified 2026-08-23 and its
    digest lived only in prose until now."""
    assert _digest(PACKET.read_text(encoding="utf-8"), "R2") == R2_SHA256, (
        "the R2 profile bytes changed; Aaron's 2026-08-23 approval no "
        "longer covers this document")


def test_the_ratification_record_carries_the_r2_approval():
    text = RATIFICATION.read_text(encoding="utf-8")
    for line in ("APPROVED_PROFILE_ID=ND1_RECOMMENDED_PROFILE_R2",
                 f"APPROVED_PROFILE_SHA256={R2_SHA256}",
                 "ND1_PROFILE_R2_RATIFICATION=VALID"):
        assert line in text, f"ratification record lost {line}"


def test_r1_is_recorded_as_superseded_rather_than_deleted():
    """The record is append-only by ruling: R2 supersedes R1 for P3 and
    R1's own record stays. If either half stops being true, the chain has
    been rewritten instead of extended."""
    text = RATIFICATION.read_text(encoding="utf-8")
    assert "R1_STATUS=SUPERSEDED_BY_R2_FOR_P3_ONLY" in text
    assert "APPROVED_PROFILE_ID=ND1_RECOMMENDED_PROFILE_R1" in text


def test_r2_is_correction_only_against_r1_by_exactly_four_edits():
    """§D.11.3's claim, mechanised for the first time.

    Until now the decision packet asserted this was "a computable fact,
    not this section's own self-report" while nothing computed it.
    """
    text = PACKET.read_text(encoding="utf-8")
    r1, r2 = _lines(text, "R1"), _lines(text, "R2")
    added, removed = _edit_count(r1, r2)
    assert added == R2_EXPECTED_EDITS, (
        f"R2 adds/changes {added} lines against R1; §D.11.3 says "
        f"{R2_EXPECTED_EDITS}. Either the profile moved or the claim is "
        "wrong — both are reportable, neither is fixed by editing this "
        "number.")
    inherited = sum(1 for ln in r2 if ln in r1)
    assert inherited == len(r2) - added
    # R2 changed two lines and added two; nothing was dropped outright.
    assert removed == 2, (
        f"{removed} R1 lines are absent from R2; the correction-only claim "
        "allows changed lines, not deletions beyond the two it names")


# ===========================================================================
# 2 — the PROPOSED R3, checked as a proposal
# ===========================================================================

def test_the_proposal_r3_block_hashes_to_what_the_proposal_declares():
    """A proposal whose own hash does not match its own bytes must never
    reach a reviewer. Four of the first five deliveries of this proposal
    failed for reasons a machine could have caught first."""
    assert _digest(PROPOSAL.read_text(encoding="utf-8"),
                   "R3") == R3_PROPOSED_SHA256
    assert R3_PROPOSED_SHA256 in PROPOSAL.read_text(encoding="utf-8"), (
        "the proposal does not state the digest its own block produces")


def test_the_proposed_r3_is_correction_only_against_r2():
    """The R2 -> R3 canonical diff test the reviewer asked for."""
    r2 = _lines(PACKET.read_text(encoding="utf-8"), "R2")
    r3 = _lines(PROPOSAL.read_text(encoding="utf-8"), "R3")
    added, _removed = _edit_count(r2, r3)
    assert added == R3_PROPOSED_EXPECTED_EDITS, (
        f"the proposed R3 adds/changes {added} lines against R2; the "
        f"proposal claims {R3_PROPOSED_EXPECTED_EDITS}")
    inherited = sum(1 for ln in r3 if ln in r2)
    assert inherited == len(r3) - added, (
        "inherited + edited must account for every line of R3")


def test_the_proposed_r3_declares_the_cr1_edges_in_both_directions():
    """The defect that produced the fourth delivery's HOLD, pinned.

    R3 gave CR1 a successor of F3 while leaving F3's predecessors alone,
    which the graph-symmetry invariant in
    test_mc_supplement_integration.py would have rejected the moment the
    profile was transcribed into code. Asserted here against the PROFILE
    text so the contradiction is caught before a reviewer sees it, not
    after.
    """
    prof = dict(ln.split("=", 1) for ln
                in _lines(PROPOSAL.read_text(encoding="utf-8"), "R3")
                if "=" in ln)
    assert "CR1" in prof["RECOMMENDED_P3_PERMITTED_SUCCESSOR"].split("|"), (
        "CR1 is unreachable: P3 does not list it as a successor")
    assert prof["RECOMMENDED_CR1_PERMITTED_PREDECESSOR"] == "P3"
    assert prof["RECOMMENDED_CR1_PERMITTED_SUCCESSOR"] == "F3"
    assert "CR1" in prof["RECOMMENDED_F3_PERMITTED_PREDECESSOR"].split("|"), (
        "CR1 -> F3 is declared in one direction only. This is exactly what "
        "the fourth delivery was HELD for.")


CR1_GRAMMAR_SHA256 = (
    "c251335f8d8c4dc89bce4ff7fb445f862d29a04b676bb3a90f6ef5ce5d5e3483")


def _cr1_grammar(text):
    b, e = "BEGIN_ND1_CR1_GRAMMAR_R3\n", "END_ND1_CR1_GRAMMAR_R3\n"
    assert b in text and e in text, "no CR1 grammar block"
    return text[text.index(b) + len(b):text.index(e)]


def test_the_cr1_grammar_block_is_bound_by_a_hash_inside_the_profile():
    """Finding 3's answer, checked rather than asserted.

    The R3 profile hash covers 59 profile lines; row class, actor, fields,
    terminal and incident_required live outside it. The binding is a line
    INSIDE the profile carrying the grammar block's own digest — so the
    profile hash covers the binding, while the grammar block never contains
    its own hash. A construction nobody checks is a claim, so this checks
    it.
    """
    import hashlib
    text = PROPOSAL.read_text(encoding="utf-8")
    got = hashlib.sha256(_cr1_grammar(text).encode("utf-8")).hexdigest()
    assert got == CR1_GRAMMAR_SHA256, (
        "the CR1 grammar bytes changed but the digest bound in the profile "
        "did not; the binding no longer covers the grammar")
    prof = dict(ln.split("=", 1) for ln in _lines(text, "R3") if "=" in ln)
    assert prof["RECOMMENDED_CR1_GRAMMAR_SHA256"] == CR1_GRAMMAR_SHA256, (
        "the profile binds a different digest than the grammar block "
        "produces — the two halves of the binding disagree")


def test_the_registry_intact_preimage_is_not_self_referential():
    """The objection that HELD the fifth delivery.

    A digest over the registry AFTER the CR1 row is appended would contain
    its own value in its preimage — unsatisfiable. The grammar must say
    BEFORE, and must say which bytes.
    """
    grammar = _cr1_grammar(PROPOSAL.read_text(encoding="utf-8"))
    line = next(ln for ln in grammar.splitlines()
                if ln.startswith("CR1_REGISTRY_INTACT_PREIMAGE="))
    assert "BEFORE" in line, (
        "the preimage does not say the registry is read BEFORE the row is "
        "appended; as written the field would be inside its own preimage")
    for required in ("ops/TRIAL_REGISTRY.md", "complete", "no normalization"):
        assert required in line, (
            f"the preimage definition does not pin {required!r}; "
            "'like a 64-hex string' is not a proof of intactness")


def test_the_proposed_r3_still_authorizes_nothing():
    """Every revision inherits the boundary lines unchanged. A profile
    revision that quietly flipped one of these would be widening its own
    mandate under cover of a grammar fix."""
    prof = dict(ln.split("=", 1) for ln
                in _lines(PROPOSAL.read_text(encoding="utf-8"), "R3")
                if "=" in ln)
    assert prof["PROFILE_STATUS"] == "PROPOSED_NOT_EFFECTIVE"
    assert prof["RECOMMENDED_ND1_WRITE_PROBE_AUTHORIZED"] == "NO"
    assert prof["RECOMMENDED_ND1_SUPPLEMENT_EXECUTION_AUTHORIZED"] == "NO"
    assert prof["PROFILE_CONTAINS_NO_EXECUTION_AUTHORIZATION"] == "YES"
    assert prof["PROFILE_CREATES_NO_DIRECTORY"] == "YES"
    assert prof["PROFILE_APPENDS_NO_REGISTRY_OR_EXPOSURE_EVENT"] == "YES"
