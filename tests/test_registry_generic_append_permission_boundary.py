"""The generic serialized writer cannot create or advance authorization state.

THE DEFECT THIS CLOSES, measured before it was closed.
`registry_boundary.serialized_append` -- the exported GENERIC entry -- refused
start-equivalent rows and nothing else, so a caller could append
`MC_READY_FOR_RUN_AUTHORIZATION` or `MC_RUN_AUTHORIZED` through it: accepted,
physically appended, and returned by `mc_registry.parse_mc_events` with no
refusal. The sibling lifecycle had the same hole -- a supplement `P2`
authorization row went through the same entry.

THE RULE. `serialized_append` is a generic serialized WRITER and is not an
authorization writer, so it refuses any event whose semantic effect is to
create or advance permission state, consistently across both affected families.

WHY THIS IS NOT AN ACTOR RULE, which is the distinction that matters most.
`mc_contract.AARON_ONLY_EVENTS` is a parse-time check that the actor CELL says
Aaron. It cannot serve as this class: it names one of the two MC events, and a
row saying `actor: Aaron` satisfied it and was accepted anyway. The two rules
answer different questions and both remain.

Every ledger here is synthetic and lives in `tmp_path`. Nothing in this file
can reach the governed registry: no test names its path, and the boundary's own
frozen root is never used.
"""
from __future__ import annotations

import pytest

from itsf.mc import mc_contract as mcc
from itsf.mc import mc_registry as mr
from itsf.mc import registry_boundary as rb
from itsf.mc import supplement_contract as sc
from itsf.mc import supplement_registry as sr

C40 = "a" * 40
MC_UTC = "2026-08-25T00:00:00Z"
SUP_UTC = "2026-08-20T00:00:00+00:00"
RID = "MC-R001"
SID = "MC-DS-S001"
SYNTH_ROOT = "C:\\synthetic\\never-created"
INC = "INC-0123456789ab"
HEADER = ("| # | utc | event | commit | actor | note |\n"
          "|---|-----|-------|--------|-------|------|\n")


def _mc_row(token, seq, fields=None, actor="Aaron"):
    """One contract-shaped MC row. `MC_RUN_AUTHORIZED` gets a sentence
    REBUILT from this row's own run id, commit and smoke ref, because a
    constant would only ever match one commit -- and because a row that
    merely SAYS authorized is not what the validator accepts."""
    fields = dict(fields or {})
    if token == "MC_RUN_AUTHORIZED":
        fields.setdefault("smoke_ref", "SMOKE-001")
        fields.setdefault("authorization_sentence",
                          mcc.authorization_sentence(RID, C40,
                                                     fields["smoke_ref"]))
    parts = "; ".join("%s: %s" % kv for kv in fields.items())
    note = "[%s]%s" % (RID, (" " + parts) if parts else "")
    return ("| %d | %s | **%s** | %s | %s | %s |"
            % (seq, MC_UTC, token, C40, actor, note))


def _sup_row(short, seq, fields, actor, head=False):
    body = "; ".join("%s: %s" % kv for kv in fields.items())
    lead = (sr.execution_sentence_header(SID) + " ") if head else ""
    return ("| %s | %s | **%s** | %s | %s | [%s] %s%s |"
            % (seq, SUP_UTC, sc.EVENTS[short].token, C40, actor, SID,
               lead, body))


P2_FIELDS = {"supplement_id": SID, "authorized_commit": C40,
             "output_root": SYNTH_ROOT}


@pytest.fixture
def ledger(tmp_path):
    """A scratch ledger already carrying the lawful prerequisites, so the
    permission row under test is the only thing in question."""
    path = tmp_path / "SCRATCH_LEDGER.md"
    path.write_bytes((HEADER + "\n".join([
        _mc_row("MC_PACKET_DRAFTED", 1),
        _mc_row("MC_PACKET_APPROVED", 2),
        _mc_row("MC_RUNNER_READYCHECKED", 3, {"smoke_ref": "SMOKE-001"}),
    ]) + "\n").encode("utf-8"))
    return path


def _append(path, line):
    rb.serialized_append(path, ("\n" + line + "\n").encode("utf-8"))


# ---------------------------------------------------------------------------
# 1-5: the permission rows are refused, before any byte moves
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("token", ["MC_READY_FOR_RUN_AUTHORIZATION",
                                   "MC_RUN_AUTHORIZED"])
def test_an_mc_permission_row_is_refused_and_writes_nothing(ledger, token):
    before = ledger.read_bytes()
    with pytest.raises(rb.AppendRefused) as ei:
        _append(ledger, _mc_row(token, 4))
    assert ei.value.code == "generic_append_refuses_permission_event"
    assert token in str(ei.value)
    # REFUSED BEFORE WRITE, not detected afterwards. Byte identity is the
    # only form of that claim worth making: "refused after the bytes landed"
    # is a different and much weaker property.
    assert ledger.read_bytes() == before
    # And the downstream parser cannot observe what was never committed.
    events, refusal = mr.parse_mc_events(ledger.read_text(encoding="utf-8"))
    assert refusal is None
    assert not any(e.token == token for e in events)


def test_the_supplement_authorization_row_is_refused_and_writes_nothing(
        tmp_path):
    """The same rule, the other family. Its token is read off
    `supplement_contract` rather than typed, which is also how the boundary
    itself derives it."""
    path = tmp_path / "SCRATCH_SUPPLEMENT.md"
    path.write_bytes((HEADER + _sup_row(
        "P1", 1, {"ir_basis": "IR-29b Option B",
                  "schema": "mc_day_strata_supplement.v1",
                  "non_authorization_disclaimer":
                      "this row is not an authorization"},
        "main agent") + "\n").encode("utf-8"))
    before = path.read_bytes()

    with pytest.raises(rb.AppendRefused) as ei:
        _append(path, _sup_row("P2", 2, P2_FIELDS, "Aaron", head=True))
    assert ei.value.code == "generic_append_refuses_permission_event"
    assert sc.EVENTS["P2"].token in str(ei.value)
    assert path.read_bytes() == before

    events, refusal = sr.parse_supplement_events(path.read_text(
        encoding="utf-8"))
    assert refusal is None
    assert not any(e.short_id == "P2" for e in events)


def test_the_refusal_survives_bold_and_padded_spellings(ledger):
    """The row grammar admits `**TOKEN**` and whitespace padding, so a
    permission row that hid behind an asterisk would be exactly the bypass
    this boundary exists to stop."""
    before = ledger.read_bytes()
    for spelling in ("MC_RUN_AUTHORIZED", "**MC_RUN_AUTHORIZED**",
                     "  MC_RUN_AUTHORIZED  "):
        assert rb.is_permission_event(spelling) is True
    row = ("| 4 | %s | MC_RUN_AUTHORIZED | %s | Aaron | [%s] smoke_ref: "
           "SMOKE-001; authorization_sentence: %s |"
           % (MC_UTC, C40, RID,
              mcc.authorization_sentence(RID, C40, "SMOKE-001")))
    with pytest.raises(rb.AppendRefused):
        _append(ledger, row)
    assert ledger.read_bytes() == before


def test_a_permission_row_hidden_in_a_multi_row_addition_is_refused(ledger):
    """One legal row plus one permission row is still refused, and the legal
    row does not land either -- the addition is one commit or none."""
    before = ledger.read_bytes()
    addition = "\n".join([_mc_row("MC_PACKET_DRAFTED", 4),
                          _mc_row("MC_RUN_AUTHORIZED", 5)])
    with pytest.raises(rb.AppendRefused) as ei:
        _append(ledger, addition)
    assert ei.value.code == "generic_append_refuses_permission_event"
    assert ledger.read_bytes() == before


# ---------------------------------------------------------------------------
# 6-8: everything that must NOT have changed
# ---------------------------------------------------------------------------

def test_an_ordinary_non_permission_append_still_works(ledger):
    """The rule is about authorization, not about sensitivity. An ordinary
    governance row commits exactly as before."""
    before = ledger.read_bytes()
    _append(ledger, _mc_row("MC_PRE_RUN_ATTEMPT_FAILURE", 4,
                            {"incident_id": INC}))
    after = ledger.read_bytes()
    assert after != before
    events, refusal = mr.parse_mc_events(after.decode("utf-8"))
    assert refusal is None
    assert any(e.token == "MC_PRE_RUN_ATTEMPT_FAILURE" for e in events)


def test_an_ordinary_supplement_append_still_works(tmp_path):
    path = tmp_path / "SCRATCH_SUPPLEMENT_OK.md"
    path.write_bytes(HEADER.encode("utf-8"))
    _append(path, _sup_row(
        "P1", 1, {"ir_basis": "IR-29b Option B",
                  "schema": "mc_day_strata_supplement.v1",
                  "non_authorization_disclaimer":
                      "this row is not an authorization"},
        "main agent"))
    events, refusal = sr.parse_supplement_events(path.read_text(
        encoding="utf-8"))
    assert refusal is None
    assert [e.short_id for e in events] == ["P1"]


def test_the_start_boundary_is_unchanged(ledger):
    """The pre-existing start refusal still fires, with its own code. The
    new rule is added beside it, not in place of it."""
    before = ledger.read_bytes()
    with pytest.raises(rb.AppendRefused) as ei:
        _append(ledger, _mc_row("MC_RUN_STARTED", 4, {"exposure_seq": "7"}))
    assert ei.value.code == "generic_append_refuses_start_equivalent"
    assert ledger.read_bytes() == before


def test_supersession_events_are_deliberately_not_in_the_class():
    """The criterion is CREATE OR ADVANCE. A supersession retires an
    authorization and cannot mint one -- measured: a P1/P2/P2S chain resolves
    to zero live authorizations -- so refusing it here
    would broaden the rule past its own criterion."""
    for token in ("MC_RUN_AUTHORIZATION_SUPERSEDED",
                  sc.EVENTS["P2S"].token):
        assert rb.is_permission_event(token) is False


def test_the_parser_actor_rule_is_untouched():
    """`AARON_ONLY_EVENTS` still refuses a non-Aaron authorization row at
    PARSE time, and still names exactly what it named. The writer boundary
    did not absorb it, replace it, or widen it."""
    assert mcc.AARON_ONLY_EVENTS == ("MC_RUN_AUTHORIZED",)
    text = HEADER + "\n".join([
        _mc_row("MC_PACKET_DRAFTED", 1),
        _mc_row("MC_PACKET_APPROVED", 2),
        _mc_row("MC_RUNNER_READYCHECKED", 3, {"smoke_ref": "SMOKE-001"}),
        _mc_row("MC_READY_FOR_RUN_AUTHORIZATION", 4),
        _mc_row("MC_RUN_AUTHORIZED", 5, actor="main agent"),
    ]) + "\n"
    _events, refusal = mr.parse_mc_events(text)
    assert refusal is not None
    assert refusal.code == "mc_actor_not_aaron"


# ---------------------------------------------------------------------------
# The canonical rule itself
# ---------------------------------------------------------------------------

def test_the_forbidden_set_is_derived_from_the_contracts_not_typed_twice():
    """One canonical rule. The MC names must exist in `mc_contract.EVENTS`
    and the supplement token is read off `supplement_contract`, so a rename
    in either contract breaks the boundary loudly instead of quietly
    disarming it."""
    assert rb.PERMISSION_EVENT_TOKENS == (
        "MC_READY_FOR_RUN_AUTHORIZATION", "MC_RUN_AUTHORIZED",
        sc.EVENTS["P2"].token)
    for name in ("MC_READY_FOR_RUN_AUTHORIZATION", "MC_RUN_AUTHORIZED"):
        assert name in mcc.EVENTS
    # The set is disjoint from the start class: two boundaries, two reasons.
    assert not (set(rb.PERMISSION_EVENT_TOKENS)
                & set(rb.START_EQUIVALENT_TOKENS))


def test_a_renamed_contract_event_breaks_the_boundary_loudly(monkeypatch):
    """The property above is only worth having if it actually fires. Drop the
    supplement short id the boundary derives from and rebuilding must raise,
    not silently produce a shorter tuple."""
    monkeypatch.setattr(rb, "_PERMISSION_SUPPLEMENT_SHORTS", ("P2_RENAMED",))
    with pytest.raises(rb.BoundaryError) as ei:
        rb._permission_event_tokens()
    assert "permission_event_not_in_supplement_contract" in str(ei.value)

    monkeypatch.setattr(rb, "_PERMISSION_MC_EVENTS", ("MC_NOT_AN_EVENT",))
    monkeypatch.setattr(rb, "_PERMISSION_SUPPLEMENT_SHORTS", ("P2",))
    with pytest.raises(rb.BoundaryError) as ei:
        rb._permission_event_tokens()
    assert "permission_event_not_in_mc_contract" in str(ei.value)
