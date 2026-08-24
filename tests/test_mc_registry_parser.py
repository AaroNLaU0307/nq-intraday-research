"""The MC registry parser, validator and chain resolver.

The test that matters most here is `test_an_unknown_mc_token_is_refused`.
Everything else checks that a well-formed thing parses and a malformed thing
refuses; that one checks the property the design rests on — inside the `MC_`
prefix there is no such thing as a row nobody owns.
"""
from __future__ import annotations

import pytest

from itsf.mc import mc_contract as mc
from itsf.mc import mc_registry as mr

C1 = "a" * 40
C2 = "b" * 40
UTC = "2026-08-25T00:00:00Z"
RID = "MC-R001"
D64 = "c" * 64
INC = "INC-0123456789ab"


class Reg:
    """Builds synthetic MC registry markdown one row at a time."""

    HEADER = ("| # | utc | event | commit | actor | note |\n"
              "|---|-----|-------|--------|-------|------|\n")

    def __init__(self) -> None:
        self.lines: list = []
        self.seq = 1

    def raw(self, line: str) -> "Reg":
        self.lines.append(line)
        return self

    def row(self, token: str, *, run_id: str = RID, fields=None,
            commit: str = C1, actor: str = "Aaron", utc: str = UTC,
            seq=None) -> "Reg":
        fields = dict(fields or {})
        if token == "MC_RUN_AUTHORIZED" and not (
                {"smoke_ref", "authorization_sentence"} & set(fields)):
            # The sentence binds this row's own run id, commit and smoke
            # ref, so it has to be built here rather than kept as a
            # constant — a constant would only ever match one commit.
            # A caller who names EITHER field is being explicit about the
            # authorization and gets exactly what they asked for, so a test
            # can still build a row with the sentence missing.
            fields["smoke_ref"] = "SMOKE-001"
            fields["authorization_sentence"] = mc.authorization_sentence(
                run_id, commit, fields["smoke_ref"])
        parts = "; ".join(f"{k}: {v}" for k, v in (fields or {}).items())
        note = f"[{run_id}]" + (f" {parts}" if parts else "")
        n = self.seq if seq is None else seq
        if seq is None:
            self.seq += 1
        self.lines.append(
            f"| {n} | {utc} | **{token}** | {commit} | {actor} | {note} |")
        return self

    def defaults(self, token: str) -> dict:
        return {
            "MC_RUNNER_READYCHECKED": {"smoke_ref": "SMOKE-001"},
            "MC_BRANCH_SEALED": {"branch": "alpha", "payload_sha256": D64,
                                 "byte_length": "4096"},
            "MC_RUN_STARTED": {"exposure_seq": "7"},
            "MC_PRE_RUN_ATTEMPT_FAILURE": {"incident_id": INC},
            "MC_RUN_FAILED_POSTSTART": {"incident_id": INC},
            "MC_BRANCH_REVEALED": {"branch": "alpha"},
            "MC_BRANCH_RETIRED_SEALED": {"branch": "beta"},
            "MC_ERRATUM": {"supersedes_event_sequence": "1"},
        }.get(token, {})

    def chain(self, tokens, **kw) -> "Reg":
        for token in tokens:
            self.row(token, fields=self.defaults(token), **kw)
        return self

    def text(self) -> str:
        return self.HEADER + "\n".join(self.lines) + "\n"


FULL = ("MC_PACKET_DRAFTED", "MC_PACKET_APPROVED", "MC_RUNNER_READYCHECKED",
        "MC_READY_FOR_RUN_AUTHORIZATION", "MC_RUN_AUTHORIZED",
        "MC_RUN_STARTED", "MC_RUN_COMPLETED")


def refuse(text: str, code: str | None = None) -> mr.McRefusal:
    chains, refusal = mr.resolve_mc_chains(text)
    assert refusal is not None, "expected a refusal, resolution succeeded"
    assert chains == {}, "a refused resolution must yield NO chains"
    assert refusal.code in mr.REFUSAL_CODES, refusal.code
    if code is not None:
        assert refusal.code == code, f"{refusal.code} != {code} ({refusal})"
    return refusal


def resolves(text: str) -> dict:
    chains, refusal = mr.resolve_mc_chains(text)
    assert refusal is None, f"unexpected refusal: {refusal}"
    return chains


# ===========================================================================
# 1 — the happy path
# ===========================================================================

def test_a_full_chain_resolves_and_carries_one_live_authorization():
    chains = resolves(Reg().chain(FULL).text())
    assert set(chains) == {RID}
    chain = chains[RID]
    assert tuple(e.token for e in chain.events) == FULL
    assert len(chain.live_authorizations) == 1
    assert chain.live_authorizations[0].commit == C1

    event, commit, detail = mr.find_live_mc_authorization(
        Reg().chain(FULL).text(), RID)
    assert detail == "ok" and commit == C1
    assert event.token == "MC_RUN_AUTHORIZED"


def test_the_whole_sealed_and_revealed_tail_resolves():
    reg = Reg().chain(FULL)
    reg.row("MC_BRANCH_SEALED", fields={"branch": "alpha",
                                        "payload_sha256": D64,
                                        "byte_length": "4096"})
    reg.row("MC_BRANCH_SEALED", fields={"branch": "beta",
                                        "payload_sha256": D64,
                                        "byte_length": "2048"})
    reg.row("MC_PRIMARY_REVEALED")
    reg.row("MC_BRANCH_REVEALED", fields={"branch": "alpha"})
    reg.row("MC_BRANCH_RETIRED_SEALED", fields={"branch": "beta"})
    reg.row("MC_RUN_CLOSED")
    assert len(resolves(reg.text())[RID].events) == 13


# ===========================================================================
# 2 — prefix ownership
# ===========================================================================

@pytest.mark.parametrize("token", [
    "MC_RUN_AUTHORIZEDD",          # a typo, the case this exists for
    "MC_RUN_SEALED",               # anticipated by N05, never ruled
    "MC_RUN_FAILED",               # same
    "MC_ANYTHING_AT_ALL",
])
def test_an_unknown_mc_token_is_refused(token):
    """THE PROPERTY THE DESIGN RESTS ON.

    A parser that owns only the tokens it recognises leaves everything else
    belonging to nobody, and a row belonging to nobody is a row that passes.
    Ownership is by prefix, so an unknown token inside `MC_` refuses."""
    reg = Reg().chain(FULL)
    reg.row(token)
    detail = refuse(reg.text(), "mc_unknown_event_token").detail
    assert token in detail


def test_rows_of_other_lifecycles_are_skipped_not_refused():
    """One registry file carries every lifecycle. Refusing a foreign row
    would mean no lifecycle could ever append to it again."""
    reg = Reg().chain(FULL)
    reg.raw(f"| 90 | {UTC} | **RUN_AUTHORIZED** | {C1} | Aaron "
            f"| [ITSF-S0] not an MC row |")
    reg.raw(f"| 91 | {UTC} | **SUPPLEMENT_PROPOSED** | {C1} | main agent "
            f"| [SUP-001] schema: x |")
    chains = resolves(reg.text())
    assert tuple(e.token for e in chains[RID].events) == FULL


def test_an_empty_registry_yields_no_chains_and_no_refusal():
    assert resolves("") == {}
    assert resolves(Reg().text()) == {}


def test_a_missing_chain_is_not_authorized_rather_than_unobjectionable():
    event, commit, detail = mr.find_live_mc_authorization("", "MC-R042")
    assert event is None and commit == ""
    assert detail == mr.NOT_AUTHORIZED_NO_CHAIN
    assert "NOT AUTHORIZED" in detail


# ===========================================================================
# 3 — stage 1, malformed rows
# ===========================================================================

def test_a_row_shaped_line_carrying_an_mc_token_must_be_a_legal_row():
    reg = Reg().chain(FULL)
    reg.raw(f"| 90 | {UTC} | **MC_BRANCH_SEALED** | {C1} |")   # five cells
    detail = refuse(reg.text(), "mc_row_malformed").detail
    assert "MC_BRANCH_SEALED" in detail


def test_the_shared_scan_does_not_reach_the_whole_prefix_and_this_one_does():
    """`MC_BRANCH_*` postdates the shared stage-1 scan, which covers only
    `SUPPLEMENT_*` and `MC_RUN_*`. Without the prefix-wide check a broken
    `MC_BRANCH_SEALED` line is dropped in silence."""
    from itsf.mc import supplement_registry as sr

    broken = f"| 90 | {UTC} | **MC_BRANCH_SEALED** | {C1} |"
    rows, refusal = sr.parse_registry_rows(Reg().chain(FULL).text() + broken)
    assert refusal is None, "the shared scan does not see this line"
    assert not any(r.event == "MC_BRANCH_SEALED" for r in rows)

    refuse(Reg().chain(FULL).text() + broken + "\n", "mc_row_malformed")


def test_a_row_shaped_line_inside_a_fence_is_documentation():
    reg = Reg().chain(FULL)
    reg.raw("```")
    reg.raw(f"| 90 | {UTC} | **MC_BRANCH_SEALED** | {C1} |")
    reg.raw("```")
    assert tuple(e.token for e in resolves(reg.text())[RID].events) == FULL


def test_prose_that_mentions_a_token_is_never_an_event():
    reg = Reg().chain(FULL)
    reg.raw("A future run will append MC_RUN_AUTHORIZED once Aaron issues "
            "the sentence.")
    assert tuple(e.token for e in resolves(reg.text())[RID].events) == FULL


# ===========================================================================
# 4 — stage 2, the note
# ===========================================================================

def test_a_row_without_a_run_id_bracket_belongs_to_no_run():
    reg = Reg().chain(FULL)
    reg.raw(f"| 90 | {UTC} | **MC_RUN_CLOSED** | {C1} | Aaron | done |")
    refuse(reg.text(), "mc_note_bracket_missing")


@pytest.mark.parametrize("run_id", ["R001", "MC-R1", "MC-R0001", "mc-r001",
                                    "MC-R001x"])
def test_a_malformed_run_id_is_refused(run_id):
    # A run id carrying a newline never reaches this check — it splits the
    # markdown row in two and stage 1 refuses it first. The `\\Z` anchor that
    # would catch it is pinned directly in
    # `test_mc_registry_contract.test_patterns_use_the_end_of_string_anchor`.
    reg = Reg()
    reg.row("MC_PACKET_DRAFTED", run_id=run_id)
    refuse(reg.text(), "mc_run_id_malformed")


def test_whitespace_inside_the_bracket_is_normalised_not_refused():
    """The bracket shape is the shared FILE FORMAT, and trimming is what it
    does — `[ MC-R001 ]` names the same run as `[MC-R001]`. Refusing it
    would be this grammar overriding the format layer for no gain."""
    reg = Reg()
    reg.row("MC_PACKET_DRAFTED", run_id=" MC-R001 ")
    assert set(resolves(reg.text())) == {RID}


def test_a_note_segment_that_is_not_a_field_is_refused():
    reg = Reg()
    reg.raw(f"| 1 | {UTC} | **MC_PACKET_DRAFTED** | {C1} | Aaron "
            f"| [{RID}] just some prose |")
    refuse(reg.text(), "mc_note_segment_not_field")


def test_a_duplicate_or_empty_field_is_refused():
    reg = Reg()
    reg.raw(f"| 1 | {UTC} | **MC_PACKET_DRAFTED** | {C1} | Aaron "
            f"| [{RID}] doc: a; doc: b |")
    refuse(reg.text(), "mc_duplicate_field_in_note")

    reg = Reg()
    reg.raw(f"| 1 | {UTC} | **MC_PACKET_DRAFTED** | {C1} | Aaron "
            f"| [{RID}] doc: |")
    refuse(reg.text(), "mc_field_value_empty")


@pytest.mark.parametrize("token,drop", [
    ("MC_RUNNER_READYCHECKED", "smoke_ref"),
    ("MC_RUN_STARTED", "exposure_seq"),
    ("MC_BRANCH_SEALED", "payload_sha256"),
    ("MC_BRANCH_SEALED", "byte_length"),
    ("MC_BRANCH_SEALED", "branch"),
])
def test_a_missing_conditional_field_is_refused(token, drop):
    reg = Reg()
    fields = dict(Reg().defaults(token))
    fields.pop(drop)
    reg.row("MC_PACKET_DRAFTED")
    reg.row(token, fields=fields)
    detail = refuse(reg.text(), "mc_missing_conditional_field").detail
    assert drop in detail


def test_an_unvalidated_field_is_a_field_nobody_checked():
    reg = Reg()
    reg.row("MC_PACKET_DRAFTED", fields={"whatever": "x"})
    detail = refuse(reg.text(), "mc_unknown_field_in_note").detail
    assert "whatever" in detail


@pytest.mark.parametrize("commit", ["a" * 7, "A" * 40, "a" * 39, "",
                                    "a" * 40 + "x"])
def test_an_abbreviated_or_uppercase_commit_binds_nothing(commit):
    reg = Reg()
    reg.row("MC_PACKET_DRAFTED", commit=commit)
    refuse(reg.text(), "mc_commit_malformed")


@pytest.mark.parametrize("utc", ["2026-08-25", "2026-08-25T00:00:00",
                                 "2026-08-25 00:00:00Z", "yesterday"])
def test_a_malformed_timestamp_is_refused(utc):
    reg = Reg()
    reg.row("MC_PACKET_DRAFTED", utc=utc)
    refuse(reg.text(), "mc_utc_malformed")


def test_only_aaron_authorizes_a_run():
    """G1 reuses S0-T001's actual history, and in it the RUN_AUTHORIZED
    actor is Aaron. That is the one actor rule the ruling supplies."""
    reg = Reg().chain(FULL[:4])
    reg.row("MC_RUN_AUTHORIZED", actor="main agent")
    refuse(reg.text(), "mc_actor_not_aaron")

    assert mc.AARON_ONLY_EVENTS == ("MC_RUN_AUTHORIZED",)
    reg = Reg().chain(FULL[:1])
    reg.row("MC_PACKET_APPROVED", actor="main agent")
    resolves(reg.text())        # unruled actors are left unconstrained


# ===========================================================================
# 4b — the authorization sentence is REBUILT, never trusted
# ===========================================================================

def _authorized(**over):
    """A chain whose MC_RUN_AUTHORIZED row can be perturbed one field at a
    time. Everything else about it is well-formed."""
    reg = Reg().chain(FULL[:4])
    reg.row("MC_RUN_AUTHORIZED", **over)
    return reg.text()


def test_a_row_that_merely_says_authorized_is_not_an_authorization():
    """The N06 round-3 lesson applied to governance text. Comparing a
    transported string to itself proves nothing; the sentence is rebuilt
    from the run id in the bracket, the commit in the commit cell and
    smoke_ref in the note, and only the sentence those three produce
    passes."""
    bad = "启动第一次真实MC，授权run_id: MC-R001，一切就绪"
    refuse(_authorized(fields={"smoke_ref": "SMOKE-001",
                               "authorization_sentence": bad}),
           "mc_authorization_sentence_mismatch")


def test_a_sentence_naming_a_different_commit_than_the_row_is_refused():
    """The attack this exists for: a real sentence, correctly formed, for a
    DIFFERENT commit — pasted into a row whose commit cell says something
    else. Both halves look right in isolation."""
    sentence = mc.authorization_sentence(RID, C2, "SMOKE-001")
    refuse(_authorized(commit=C1,
                       fields={"smoke_ref": "SMOKE-001",
                               "authorization_sentence": sentence}),
           "mc_authorization_sentence_mismatch")


def test_a_sentence_naming_a_different_run_id_than_the_bracket_is_refused():
    sentence = mc.authorization_sentence("MC-R002", C1, "SMOKE-001")
    refuse(_authorized(fields={"smoke_ref": "SMOKE-001",
                               "authorization_sentence": sentence}),
           "mc_authorization_sentence_mismatch")


def test_a_sentence_naming_a_different_smoke_ref_than_the_row_is_refused():
    sentence = mc.authorization_sentence(RID, C1, "SMOKE-002")
    refuse(_authorized(fields={"smoke_ref": "SMOKE-001",
                               "authorization_sentence": sentence}),
           "mc_authorization_sentence_mismatch")


def test_the_sentence_binds_the_branch_policy_and_not_branch_hashes():
    """G1 AS MODIFIED. The payloads are produced BY the authorized run, so
    their hashes cannot be in the sentence that authorizes it."""
    reg = Reg().chain(FULL[:5])
    row = [ln for ln in reg.lines if "MC_RUN_AUTHORIZED" in ln][0]
    assert mc.BRANCH_POLICY_TOKEN in row
    import re
    assert not re.search(r"[0-9a-f]{64}", row)
    resolves(reg.text())


def test_an_authorized_row_without_the_sentence_is_refused():
    detail = refuse(_authorized(fields={"smoke_ref": "SMOKE-001"}),
                    "mc_missing_conditional_field").detail
    assert "authorization_sentence" in detail


def test_a_malformed_smoke_ref_refuses_under_its_own_code():
    refuse(_authorized(fields={"smoke_ref": "SMOKE1",
                               "authorization_sentence": "x"}),
           "mc_smoke_ref_malformed")


# ===========================================================================
# 5 — stage 3, the chain
# ===========================================================================

def test_a_chain_that_starts_mid_lifecycle_has_no_evidence_for_the_rest():
    reg = Reg().chain(FULL[1:])
    refuse(reg.text(), "mc_chain_starts_mid_lifecycle")


def test_a_reveal_before_any_seal_is_the_ordering_g7_exists_to_forbid():
    reg = Reg().chain(FULL)
    reg.row("MC_PRIMARY_REVEALED")
    detail = refuse(reg.text(), "mc_illegal_transition").detail
    assert "MC_RUN_COMPLETED -> MC_PRIMARY_REVEALED" in detail


def test_a_run_cannot_close_leaving_the_untriggered_branch_dangling():
    reg = Reg().chain(FULL)
    reg.row("MC_BRANCH_SEALED", fields=Reg().defaults("MC_BRANCH_SEALED"))
    reg.row("MC_PRIMARY_REVEALED")
    reg.row("MC_RUN_CLOSED")
    refuse(reg.text(), "mc_illegal_transition")


def test_no_edge_skips_authorization():
    reg = Reg().chain(FULL[:3])
    reg.row("MC_RUN_STARTED", fields={"exposure_seq": "7"})
    refuse(reg.text(), "mc_illegal_transition")


def test_the_pre_start_failure_loop_resolves():
    """Reached twice on the real S0 run; recorded history, not speculation."""
    reg = Reg().chain(FULL[:5])
    reg.row("MC_PRE_RUN_ATTEMPT_FAILURE", fields={"incident_id": INC})
    reg.row("MC_RUN_AUTHORIZATION_SUPERSEDED",
            fields={"supersedes_event_sequence": "5",
                    "superseded_commit": C1,
                    "reason_code": "PRESTART_FIX", "incident_id": INC})
    reg.row("MC_READY_FOR_RUN_AUTHORIZATION")
    reg.row("MC_RUN_AUTHORIZED", commit=C2)
    reg.row("MC_RUN_STARTED", fields={"exposure_seq": "7"}, commit=C2)
    chain = resolves(reg.text())[RID]
    assert len(chain.live_authorizations) == 1
    assert chain.live_authorizations[0].commit == C2


def test_a_post_start_failure_burns_the_id():
    reg = Reg().chain(FULL[:6])
    reg.row("MC_RUN_FAILED_POSTSTART", fields={"incident_id": INC})
    reg.row("MC_RUN_CLOSED")
    resolves(reg.text())

    reg = Reg().chain(FULL[:6])
    reg.row("MC_RUN_FAILED_POSTSTART", fields={"incident_id": INC})
    reg.row("MC_READY_FOR_RUN_AUTHORIZATION")
    reg.row("MC_RUN_AUTHORIZED", commit=C2)
    refuse(reg.text(), "mc_illegal_transition")


def test_an_erratum_corrects_a_row_without_being_a_lifecycle_step():
    reg = Reg().chain(FULL)
    reg.row("MC_ERRATUM", fields={"supersedes_event_sequence": "2"})
    reg.row("MC_BRANCH_SEALED", fields=Reg().defaults("MC_BRANCH_SEALED"))
    chain = resolves(reg.text())[RID]
    assert "MC_ERRATUM" in [e.token for e in chain.events]
    assert mc.OUT_OF_CHAIN == ("MC_ERRATUM",)


def test_two_run_ids_are_two_independent_chains():
    reg = Reg().chain(FULL)
    reg.chain(FULL, run_id="MC-R002")
    chains = resolves(reg.text())
    assert set(chains) == {RID, "MC-R002"}
    assert all(len(c.live_authorizations) == 1 for c in chains.values())


# ===========================================================================
# 6 — supersession, verbatim from S0-T001's shape
# ===========================================================================

def _superseded(**overrides):
    reg = Reg().chain(FULL[:5])
    reg.row("MC_PRE_RUN_ATTEMPT_FAILURE", fields={"incident_id": INC})
    fields = {"supersedes_event_sequence": "5", "superseded_commit": C1,
              "reason_code": "PRESTART_FIX", "incident_id": INC}
    fields.update(overrides)
    reg.row("MC_RUN_AUTHORIZATION_SUPERSEDED", fields=fields)
    reg.row("MC_READY_FOR_RUN_AUTHORIZATION")
    reg.row("MC_RUN_AUTHORIZED", commit=C2)
    return reg.text()


def test_a_supersede_naming_a_different_commit_has_identified_nothing():
    refuse(_superseded(superseded_commit=C2), "mc_supersede_commit_mismatch")


def test_a_supersede_of_a_nonexistent_row_fails_closed():
    refuse(_superseded(supersedes_event_sequence="99"),
           "mc_supersede_target_missing")


def test_a_forward_supersede_is_refused():
    """A supersede must appear AFTER the row it retires. Naming a row that
    has not happened yet would let the file retire an authorization before
    it was issued."""
    reg = Reg().chain(FULL[:5])
    reg.row("MC_PRE_RUN_ATTEMPT_FAILURE", fields={"incident_id": INC})
    reg.row("MC_RUN_AUTHORIZATION_SUPERSEDED",
            fields={"supersedes_event_sequence": "9",
                    "superseded_commit": C2,
                    "reason_code": "PRESTART_FIX", "incident_id": INC})
    reg.row("MC_READY_FOR_RUN_AUTHORIZATION")
    reg.row("MC_RUN_AUTHORIZED", commit=C2)
    refuse(reg.text(), "mc_supersede_forward_reference")


def test_a_duplicate_supersede_has_no_live_row_left_to_act_on():
    reg = Reg().chain(FULL[:5])
    reg.row("MC_PRE_RUN_ATTEMPT_FAILURE", fields={"incident_id": INC})
    for _ in range(2):
        reg.row("MC_RUN_AUTHORIZATION_SUPERSEDED",
                fields={"supersedes_event_sequence": "5",
                        "superseded_commit": C1,
                        "reason_code": "PRESTART_FIX", "incident_id": INC})
        reg.row("MC_READY_FOR_RUN_AUTHORIZATION")
        reg.row("MC_RUN_AUTHORIZED", commit=C2)
        reg.row("MC_PRE_RUN_ATTEMPT_FAILURE", fields={"incident_id": INC})
    refuse(reg.text(), "mc_supersede_duplicate")


def test_zero_live_authorizations_means_not_authorized():
    reg = Reg().chain(FULL[:5])
    reg.row("MC_PRE_RUN_ATTEMPT_FAILURE", fields={"incident_id": INC})
    reg.row("MC_RUN_AUTHORIZATION_SUPERSEDED",
            fields={"supersedes_event_sequence": "5",
                    "superseded_commit": C1,
                    "reason_code": "PRESTART_FIX", "incident_id": INC})
    reg.row("MC_READY_FOR_RUN_AUTHORIZATION")
    event, commit, detail = mr.find_live_mc_authorization(reg.text(), RID)
    assert event is None and commit == ""
    assert "no live MC_RUN_AUTHORIZED row" in detail


def test_two_live_authorizations_are_refused_rather_than_broken():
    """Not "the newer one wins". Two live rows mean the registry does not
    say which run is authorized, and guessing is how the wrong commit gets
    a real run."""
    reg = Reg().chain(FULL[:5])
    reg.row("MC_PRE_RUN_ATTEMPT_FAILURE", fields={"incident_id": INC})
    reg.row("MC_RUN_AUTHORIZED", commit=C2)
    event, commit, detail = mr.find_live_mc_authorization(reg.text(), RID)
    assert event is None and commit == ""
    assert "2 live MC_RUN_AUTHORIZED rows" in detail


def test_a_refused_resolution_never_reports_an_authorization():
    reg = Reg().chain(FULL)
    reg.row("MC_ANYTHING_AT_ALL")
    event, commit, detail = mr.find_live_mc_authorization(reg.text(), RID)
    assert event is None and commit == ""
    assert "mc_unknown_event_token" in detail


# ===========================================================================
# 7 — what is deliberately NOT checked
# ===========================================================================

def test_an_mc_row_takes_the_next_value_of_the_global_sequence():
    """`SEQUENCE_NAMESPACE=GLOBAL` — a property of the FILE, not of either
    grammar, and already ratified. It reads the same whether MC rows share
    `ops/TRIAL_REGISTRY.md` or get their own file, so enforcing it here
    presumes nothing about how MC-REG-COLLISION-001 is resolved."""
    reg = Reg().chain(FULL[:2])
    reg.row("MC_RUNNER_READYCHECKED", fields={"smoke_ref": "SMOKE-001"},
            seq=9)
    detail = refuse(reg.text(), "mc_seq_not_next_value").detail
    assert "expected 3" in detail

    reg = Reg().chain(FULL[:2])
    reg.row("MC_RUNNER_READYCHECKED", fields={"smoke_ref": "SMOKE-001"},
            seq=2)
    refuse(reg.text(), "mc_seq_duplicate")

    reg = Reg().chain(FULL[:2])
    reg.row("MC_RUNNER_READYCHECKED", fields={"smoke_ref": "SMOKE-001"},
            seq="+")
    refuse(reg.text(), "mc_seq_not_integer")


def test_a_gappy_mc_sequence_would_wedge_every_other_lifecycle():
    """WHY THE RULE IS NOT COSMETIC. Measured 2026-08-25.

    The supplement grammar computes "highest so far" over ALL numbered rows
    in the file, foreign ones included, and then demands the NEXT value. So
    an MC row that jumps to 99 does not merely look untidy — it makes the
    next numbered supplement row illegal, with
    `supplement_seq_not_next_value`, forever.

    This test states the coupling in both directions: the supplement
    grammar really does refuse, and this grammar really does prevent the
    row that would cause it."""
    import sys
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
    from test_mc_supplement_registry import Reg as SupReg
    from itsf.mc import supplement_registry as sr

    sup = SupReg().chain(("P1", "P2", "P3", "P4", "P5"))
    sup.raw(f"| 99 | 2026-08-20T00:00:00+00:00 | **MC_BRANCH_SEALED** "
            f"| {'0' * 40} | Aaron | [MC-R001] branch: alpha |")
    sup.chain(("P1", "P2", "P3", "P4", "P5"), sid="MC-DS-S002")
    _, refusal = sr.resolve_supplement_chains(sup.text())
    assert refusal is not None
    assert refusal.code == "supplement_seq_not_next_value"

    reg = Reg().chain(FULL[:2])
    reg.row("MC_RUNNER_READYCHECKED", fields={"smoke_ref": "SMOKE-001"},
            seq=99)
    refuse(reg.text(), "mc_seq_not_next_value")


def test_the_registry_grammar_does_not_authorize_anything_by_itself():
    """Parsing a row that says AUTHORIZED is not authorization. The
    execution gate is `consumer.authorize_real_mc`, which still refuses."""
    from itsf.mc import consumer as mcc
    from itsf.s0.handoff import McConsumerAbsent

    with pytest.raises(McConsumerAbsent):
        mcc.authorize_real_mc(Reg().chain(FULL).text())
