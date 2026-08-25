"""The MC registry vocabulary, pinned to G1-G8 as RATIFIED.

Two tests here matter more than the rest. One pins the G1 modification --
the authorization sentence binds a branch POLICY, never the branch hashes,
because those do not exist when the sentence is written. The other pins the
namespace split from the supplement grammar, which the ruling asked for in
as many words: follow the shape, do not assume identity.
"""
from __future__ import annotations

import re

import pytest

from itsf.mc import mc_contract as mc


def test_the_event_vocabulary_is_the_ratified_sixteen():
    assert len(mc.EVENTS) == 16
    assert len(set(mc.EVENTS)) == 16
    for name in ("MC_PACKET_DRAFTED", "MC_RUN_AUTHORIZED",
                 "MC_BRANCH_SEALED", "MC_RUN_STARTED",
                 "MC_PRE_RUN_ATTEMPT_FAILURE",
                 "MC_RUN_AUTHORIZATION_SUPERSEDED",
                 "MC_RUN_FAILED_POSTSTART", "MC_PRIMARY_REVEALED",
                 "MC_BRANCH_REVEALED", "MC_BRANCH_RETIRED_SEALED",
                 "MC_RUN_CLOSED", "MC_ERRATUM"):
        assert name in mc.EVENTS, name


def test_every_event_names_its_own_conditional_fields():
    """A row cannot be validated without knowing what that event owes."""
    assert set(mc.CONDITIONAL_FIELDS) == set(mc.EVENTS)
    assert mc.CONDITIONAL_FIELDS["MC_BRANCH_SEALED"] == (
        "branch", "payload_sha256", "byte_length")
    assert mc.CONDITIONAL_FIELDS["MC_RUN_STARTED"] == ("exposure_seq",)
    assert mc.CONDITIONAL_FIELDS["MC_PRE_RUN_ATTEMPT_FAILURE"] == (
        "incident_id",)
    assert mc.CONDITIONAL_FIELDS["MC_PACKET_DRAFTED"] == ()


# --- the G1 modification ----------------------------------------------------

def test_the_authorization_sentence_binds_a_policy_not_branch_hashes():
    """G1 AS MODIFIED, and the contradiction it resolves.

    The proposal bound alpha and beta payload hashes into the sentence.
    Those hashes do not exist when the sentence is written -- the payloads
    are produced BY the authorized run -- so G1 as proposed and M14/G7
    could not both be satisfied. The sentence binds the branch POLICY; the
    hashes are bound afterwards, by MC_BRANCH_SEALED."""
    s = mc.authorization_sentence("MC-R001", "a" * 40, "SMOKE-001")
    assert mc.BRANCH_POLICY_TOKEN in s
    assert "分支政策" in s
    assert "alpha=" not in s and "beta=" not in s
    assert not re.search(r"[0-9a-f]{64}", s), (
        "a 64-hex string in the authorization sentence is a payload hash, "
        "and payload hashes cannot exist before the run that produces them")


def test_the_rendered_sentence_equals_the_ruling_character_for_character():
    """The ruling fixed the grammar verbatim. Aaron types this string.

    G1 AS MODIFIED, quoted from `ops/DELEGATED_RULINGS_2026-08-24.md` §2.1:
    «固定文法改为：`启动第一次真实MC，授权run_id: MC-R001，使用commit:
    <40位小写hex>，分支政策: PRECOMPUTE_BOTH_BLIND_SEAL_AFTER_COMPLETION，
    smoke: SMOKE-001=PASS`».

    Drift in either direction is a real failure: a renderer that produces
    something else makes Aaron's verbatim sentence unrecognisable, and a
    validator that accepts something else accepts an authorization he did
    not write. Both halves come from this one constant."""
    ruled = ("启动第一次真实MC，授权run_id: MC-R001，使用commit: "
             + "a" * 40
             + "，分支政策: PRECOMPUTE_BOTH_BLIND_SEAL_AFTER_COMPLETION"
               "，smoke: SMOKE-001=PASS")
    assert mc.authorization_sentence("MC-R001", "a" * 40,
                                     "SMOKE-001") == ruled


def test_the_branch_hash_lives_on_the_post_run_event_instead():
    assert "payload_sha256" in mc.CONDITIONAL_FIELDS["MC_BRANCH_SEALED"]
    assert "byte_length" in mc.CONDITIONAL_FIELDS["MC_BRANCH_SEALED"]


@pytest.mark.parametrize("run_id,commit,smoke,code", [
    ("R001", "a" * 40, "SMOKE-001", "mc_run_id_malformed"),
    ("MC-R1", "a" * 40, "SMOKE-001", "mc_run_id_malformed"),
    ("MC-R001", "a" * 7, "SMOKE-001", "mc_commit_malformed"),
    ("MC-R001", "A" * 40, "SMOKE-001", "mc_commit_malformed"),
    ("MC-R001", "a" * 40, "SMOKE1", "mc_smoke_ref_malformed"),
    ("MC-R001", "a" * 40, "", "mc_smoke_ref_malformed"),
])
def test_a_malformed_sentence_is_refused_not_rendered(run_id, commit,
                                                      smoke, code):
    """Rendering a broken sentence would put a string in front of a human
    that LOOKS like the thing that authorizes a real run."""
    with pytest.raises(mc.MCGrammarError) as ei:
        mc.authorization_sentence(run_id, commit, smoke)
    assert ei.value.code == code


# --- transitions ------------------------------------------------------------

def test_the_two_failure_loops_s0_actually_exercised_are_legal():
    """Both were reached on the real S0 run -- two pre-run failures -- so
    they are recorded history, not defensive speculation."""
    assert ("MC_RUN_AUTHORIZED", "MC_PRE_RUN_ATTEMPT_FAILURE") \
        in mc.LEGAL_TRANSITIONS
    assert ("MC_PRE_RUN_ATTEMPT_FAILURE",
            "MC_RUN_AUTHORIZATION_SUPERSEDED") in mc.LEGAL_TRANSITIONS
    assert ("MC_RUN_AUTHORIZATION_SUPERSEDED",
            "MC_READY_FOR_RUN_AUTHORIZATION") in mc.LEGAL_TRANSITIONS
    assert ("MC_RUN_STARTED", "MC_RUN_FAILED_POSTSTART") \
        in mc.LEGAL_TRANSITIONS


def test_a_branch_cannot_be_sealed_before_the_run_completes():
    """G7's ordering. Sealing before completion would mean a hash for a
    payload that does not exist yet -- the same impossibility the G1
    modification removed from the sentence."""
    for src in ("MC_RUN_AUTHORIZED", "MC_RUN_STARTED",
                "MC_READY_FOR_RUN_AUTHORIZATION"):
        assert (src, "MC_BRANCH_SEALED") not in mc.LEGAL_TRANSITIONS, src
    assert ("MC_RUN_COMPLETED", "MC_BRANCH_SEALED") in mc.LEGAL_TRANSITIONS


def test_a_reveal_cannot_precede_the_seal():
    assert ("MC_RUN_COMPLETED", "MC_BRANCH_REVEALED") \
        not in mc.LEGAL_TRANSITIONS
    assert ("MC_PRIMARY_REVEALED", "MC_BRANCH_REVEALED") \
        in mc.LEGAL_TRANSITIONS


def test_there_is_no_edge_that_skips_authorization():
    for src in mc.EVENTS:
        assert (src, "MC_RUN_STARTED") not in mc.LEGAL_TRANSITIONS \
            or src == "MC_RUN_AUTHORIZED", src


# --- the namespace split ----------------------------------------------------

def test_no_token_is_legal_in_both_vocabularies():
    """"Follow the shape, do not assume identity" -- the ruling's words.

    The invariant is not "these two files never say the same string". It is
    that no token is LEGAL in both grammars, so a row can never be valid
    under the wrong lifecycle. The two lifecycles genuinely differ: MC seals
    branches and has a reveal, a supplement has neither."""
    from itsf.mc import supplement_contract as sc

    overlap = set(mc.EVENTS) & set(sc.EVENT_TOKENS)
    assert not overlap, f"legal in both grammars: {sorted(overlap)}"


def test_the_two_names_that_appear_in_both_are_the_discharged_pair():
    """Where the strings coincide, that was the handoff — and the handoff
    has now happened.

    `supplement_contract` named four MC tokens in `ND3_DEFERRED_TOKENS`
    before N-D3 was ruled, so its parser would refuse them BY NAME rather
    than ignore them. Two of those four became real MC events, and those
    two are exactly the pair C3 discharged. The other two were never
    created and stay refused."""
    from itsf.mc import supplement_contract as sc

    shared = set(mc.EVENTS) & set(sc.ND3_DEFERRED_TOKENS)
    assert shared == {"MC_RUN_AUTHORIZED", "MC_RUN_STARTED"}
    assert set(sc.ND3_DEFERRAL_DISCHARGED) == shared, (
        "the discharged pair must be exactly the names that turned out to "
        "be real MC events — no more, no less")


def test_the_ruling_did_not_create_two_of_the_four_anticipated_names():
    """A recorded divergence, not an oversight.

    `ND3_DEFERRED_TOKENS` anticipated `MC_RUN_SEALED` and `MC_RUN_FAILED`.
    The ruling created neither: sealing is BRANCH-scoped because both
    branches are precomputed, and failure is SPLIT because G4 turns on
    whether the exposure slot was already consumed.

    So the supplement's by-name list names two events that will never be
    emitted, and does not name the two that replaced them. Measured, not
    assumed: the replacements are SKIPPED by the supplement parser as rows
    belonging to another lifecycle -- which is the behaviour the shared
    registry file requires, and the behaviour the two colliding names do
    NOT get. See `test_a_ratified_mc_row_breaks_supplement_resolution`."""
    from itsf.mc import supplement_contract as sc
    from itsf.mc import supplement_registry as sr
    from test_mc_supplement_registry import C1, Reg, SID, UTC

    assert "MC_RUN_SEALED" not in mc.EVENTS
    assert "MC_RUN_FAILED" not in mc.EVENTS
    assert "MC_BRANCH_SEALED" in mc.EVENTS
    assert "MC_RUN_FAILED_POSTSTART" in mc.EVENTS

    for token in ("MC_BRANCH_SEALED", "MC_RUN_FAILED_POSTSTART"):
        assert token not in sc.ND3_DEFERRED_TOKENS, token
        reg = Reg().chain(("P1", "P2", "P3", "P4", "P5"))
        reg.raw(f"| 4 | {UTC} | **{token}** | {C1} | main agent "
                f"| [{SID}] schema: x |")
        chains, refusal = sr.resolve_supplement_chains(reg.text())
        assert refusal is None, (token, refusal)
        assert chains, "the supplement chain must still resolve"


def test_a_ratified_mc_row_no_longer_breaks_supplement_resolution():
    """WAS the reproduction of MC-REG-COLLISION-001. Now the pin that it
    is fixed, and the record of what it used to prove.

    Until 2026-08-25 this test asserted the opposite: an `MC_RUN_AUTHORIZED`
    row in `ops/TRIAL_REGISTRY.md` refused the WHOLE supplement resolution
    with `token_deferred_to_nd3`, and since the day-strata supplement is an
    INPUT to the MC run, the first real MC run would have broken the
    mechanism proving its own input was authorized. Two ratified artifacts
    that could not both be implemented.

    Resolved as R2 with modifications — Fable proposed, a fresh Sol
    ratified, Aaron adjudicated. `DELEGATED=YES`. §D.3.4's deferral carried
    its own discharge condition ("before the N-D3 ruling") and its own
    reason (incomplete lifecycle definitions); N-D3 supplied the
    definitions, so the guard was discharged on its own terms rather than
    weakened.
    """
    from itsf.mc import consumer as mcc
    from itsf.mc import supplement_registry as sr
    from test_mc_supplement_registry import C1, Reg, SID, UTC

    assert mcc.MC_AUTHORIZATION_EVENT == "MC_RUN_AUTHORIZED"

    for token in ("MC_RUN_AUTHORIZED", "MC_RUN_STARTED"):
        assert token in mc.EVENTS, token
        reg = Reg().chain(("P1", "P2", "P3", "P4", "P5"))
        reg.raw(f"| 4 | {UTC} | **{token}** | {C1} | Aaron "
                f"| [MC-R001] run_id: MC-R001 |")
        chains, refusal = sr.resolve_supplement_chains(reg.text())
        assert refusal is None, (token, refusal)
        assert chains, "the supplement chain must resolve alongside MC rows"


def test_what_replaced_the_refusal_is_stricter_than_it_was():
    """The discharge did not leave those rows unguarded — it moved them to
    a grammar that demands far more.

    The old by-name guard refused the token unconditionally. `mc_registry`
    accepts it only as part of a chain that starts at MC_PACKET_DRAFTED,
    takes the next global sequence value, carries a 40-hex commit, names
    Aaron as actor, and carries the authorization sentence rebuilt from its
    own run id, commit and smoke ref. A row that merely says AUTHORIZED is
    still refused — by the owner, and for better reasons."""
    from itsf.mc import mc_registry as mr
    from test_mc_supplement_registry import C1, Reg, SID, UTC

    reg = Reg().chain(("P1", "P2", "P3", "P4", "P5"))
    reg.raw(f"| 4 | {UTC} | **MC_RUN_AUTHORIZED** | {C1} | Aaron "
            f"| [MC-R001] run_id: MC-R001 |")
    _, refusal = mr.resolve_mc_chains(reg.text())
    assert refusal is not None, "the MC grammar must own and judge this row"
    assert refusal.code in mr.REFUSAL_CODES


# --- the anchors ------------------------------------------------------------

def test_patterns_use_the_end_of_string_anchor():
    """`$` also matches before a trailing newline, which is how a value
    carrying a newline passes a pattern that looks strict. A fresh review
    found exactly that in the supplement grammar (N06 round 1)."""
    for name, pattern in (("run id", mc.RUN_ID_RE),
                          ("commit", mc.COMMIT_RE),
                          ("incident", mc.INCIDENT_RE),
                          ("sha256", mc.SHA256_RE),
                          ("reason code", mc.REASON_CODE_RE)):
        assert r"\Z" in pattern.pattern, name
        assert not pattern.pattern.endswith("$"), name

    assert not mc.COMMIT_RE.match("a" * 40 + "\n")
    assert not mc.RUN_ID_RE.match("MC-R001\n")
    assert not mc.INCIDENT_RE.match("INC-0123456789ab\n")


def test_g5_and_g6_are_recorded_as_constants_not_only_prose():
    assert mc.POSTSTART_FAILURE_REQUIRES_NEW_ID is True
    assert mc.ID_REUSE_FORBIDDEN is True
