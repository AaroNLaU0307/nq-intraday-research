"""T-F06: owner hold, owner release, owner revocation (QROS-CF v2 §2.3;
DEC-0006 I2; DEC-0009 Condition B).

CONDITION B, ANSWERED HERE MECHANICALLY.

    OWNER_HOLD / OWNER_RELEASE   representable today as six-cell NUMBERED
                                 rows the two family grammars skip; read by
                                 `owner_control`, enforced by the
                                 `live_authorization_unique` gate and again
                                 by the P3 append on its fresh registry read.
    REVOKED                      representable as an owner-actor P2S with
                                 reason_code OWNER_REVOCATION and successor
                                 NONE -- the minimum grammar admission
                                 Condition B put inside I2. The chain state
                                 after it refuses every start.

THE ACCEPTANCE TEST, VERBATIM FROM AARON: authorize, revoke, identity
unchanged, attempt to start -- refused before any run write. Proved three
ways below: the gate, the append seam, and the resolved chain.

Every registry here is synthetic text from the shared `Reg` builder; the
one real-registry read is the tolerance test at the end, which parses and
never writes.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tests"))

import test_mc_supplement_registry as T           # noqa: E402
from itsf.mc import mc_registry as mreg           # noqa: E402
from itsf.mc import owner_control as oc           # noqa: E402
from itsf.mc import registry_boundary as rb       # noqa: E402
from itsf.mc import supplement_contract as sc     # noqa: E402
from itsf.mc import supplement_registry as sreg   # noqa: E402
from itsf.mc import supplement_runner as sr       # noqa: E402

SID, SID2 = T.SID, T.SID2
UTC = "2026-09-07T00:00:00+00:00"
C40 = "c" * 40


def _owner(seq, token, scope, body, actor="Aaron", commit=C40):
    return f"| {seq} | {UTC} | {token} | {commit} | {actor} | [{scope}] {body} |"


def _live_registry():
    """P1 + a live P2 for SID, authorizing commit C1."""
    reg = T.Reg()
    reg.add("P1")
    reg.add("P2")
    return reg


# ---------------------------------------------------------------------------
# parsing
# ---------------------------------------------------------------------------

def test_a_global_hold_and_its_release_parse():
    reg = _live_registry()
    reg.raw(_owner(3, "OWNER_HOLD", "GLOBAL", "reason: sync incident under review"))
    reg.raw(_owner(4, "OWNER_RELEASE", "GLOBAL",
                   "releases_event_sequence: 3; reason: incident closed"))
    rows = oc.parse_owner_rows(reg.text())
    assert [r.token for r in rows] == ["OWNER_HOLD", "OWNER_RELEASE"]
    assert rows[0].scope == "GLOBAL" and rows[1].releases == 3
    assert oc.active_holds(reg.text(), SID) == ()


def test_a_scoped_hold_applies_only_to_its_id():
    reg = _live_registry()
    reg.raw(_owner(3, "OWNER_HOLD", SID2, "reason: only S002 is suspended"))
    assert oc.active_holds(reg.text(), SID) == ()
    assert len(oc.active_holds(reg.text(), SID2)) == 1


@pytest.mark.parametrize("line,code", [
    (_owner(3, "OWNER_HOLD", "GLOBAL", "reason: x", actor="main agent"),
     "owner_control_actor_not_owner"),
    (_owner("+", "OWNER_HOLD", "GLOBAL", "reason: x"),
     "owner_control_row_malformed"),
    (_owner(3, "OWNER_HOLD", "GLOBAL", "note without a field"),
     "owner_control_row_malformed"),
    (_owner(3, "OWNER_HOLD", "GLOBAL", "reason: "),
     "owner_control_row_malformed"),
    (f"| 3 | {UTC} | OWNER_HOLD | {C40} | Aaron | no bracket; reason: x |",
     "owner_control_row_malformed"),
    (_owner(3, "OWNER_RELEASE", "GLOBAL", "releases_event_sequence: 2; reason: x"),
     "owner_control_release_without_hold"),
])
def test_a_malformed_owner_row_is_refused_not_ignored(line, code):
    reg = _live_registry()
    reg.raw(line)
    with pytest.raises(oc.OwnerControlRefusal) as caught:
        oc.parse_owner_rows(reg.text())
    assert caught.value.code == code


def test_a_release_must_match_the_holds_scope_and_may_not_repeat():
    reg = _live_registry()
    reg.raw(_owner(3, "OWNER_HOLD", "GLOBAL", "reason: x"))
    reg.raw(_owner(4, "OWNER_RELEASE", SID, "releases_event_sequence: 3; reason: y"))
    with pytest.raises(oc.OwnerControlRefusal) as caught:
        oc.parse_owner_rows(reg.text())
    assert caught.value.code == "owner_control_release_scope_mismatch"

    reg = _live_registry()
    reg.raw(_owner(3, "OWNER_HOLD", "GLOBAL", "reason: x"))
    reg.raw(_owner(4, "OWNER_RELEASE", "GLOBAL", "releases_event_sequence: 3; reason: y"))
    reg.raw(_owner(5, "OWNER_RELEASE", "GLOBAL", "releases_event_sequence: 3; reason: z"))
    with pytest.raises(oc.OwnerControlRefusal) as caught:
        oc.parse_owner_rows(reg.text())
    assert caught.value.code == "owner_control_release_twice"


# ---------------------------------------------------------------------------
# the gate: authorize, hold, identity unchanged, start -> refused
# ---------------------------------------------------------------------------

def _ctx(text):
    chain = sreg.resolve_supplement_chain(text, SID)
    assert not getattr(chain, "problem", ""), chain.problem
    return sr.GateContext(supplement_id=SID, head_commit=T.C1, registry_text=text,
                          runs_root=None, archive_root=None, frozen_hashes_ok=True,
                          chain=chain, environment_pinned=True,
                          environment_detail="pinned")


GATE = sr.GATES["live_authorization_unique"]


def test_the_gate_passes_with_one_live_p2_and_no_hold():
    GATE(_ctx(_live_registry().text()))


def test_the_gate_refuses_under_a_global_hold_with_the_identity_unchanged():
    reg = _live_registry()
    reg.raw(_owner(3, "OWNER_HOLD", "GLOBAL", "reason: Aaron suspended all starts"))
    ctx = _ctx(reg.text())
    assert len(ctx.chain.live_authorizations) == 1, "premise: the P2 is still live"
    with pytest.raises(sr.SupplementRunnerError) as caught:
        GATE(ctx)
    assert "OWNER_HOLD in force" in str(caught.value)
    assert "Aaron suspended all starts" in str(caught.value)


def test_the_gate_passes_again_after_the_release():
    reg = _live_registry()
    reg.raw(_owner(3, "OWNER_HOLD", "GLOBAL", "reason: x"))
    reg.raw(_owner(4, "OWNER_RELEASE", "GLOBAL", "releases_event_sequence: 3; reason: y"))
    GATE(_ctx(reg.text()))


def test_the_gate_refuses_when_an_owner_row_cannot_be_read():
    reg = _live_registry()
    reg.raw(_owner(3, "OWNER_HOLD", "GLOBAL", "reason: x", actor="main agent"))
    with pytest.raises(sr.SupplementRunnerError) as caught:
        GATE(_ctx(reg.text()))
    assert "unreadable" in str(caught.value)


# ---------------------------------------------------------------------------
# the append seam: a hold that lands after the precheck read is still seen
# ---------------------------------------------------------------------------

def _registry_file(tmp_path, reg) -> Path:
    path = tmp_path / "SYNTHETIC_REGISTRY.md"   # never the real filename
    path.write_text(reg.text(), encoding="utf-8")
    return path


def test_p3_is_refused_under_a_hold_before_any_write(tmp_path):
    reg = _live_registry()
    reg.raw(_owner(3, "OWNER_HOLD", "GLOBAL", "reason: hold"))
    path = _registry_file(tmp_path, reg)
    before = path.read_bytes()
    with pytest.raises(rb.AppendRefused) as caught:
        rb.append_run_started(SID, head_commit=T.C1, utc_stamp=UTC, path=path)
    assert caught.value.code == "p3_owner_hold_in_force"
    assert path.read_bytes() == before, "a refused append must write nothing"


def test_p3_appends_when_no_hold_applies(tmp_path):
    reg = _live_registry()
    reg.raw(_owner(3, "OWNER_HOLD", SID2, "reason: another id"))
    path = _registry_file(tmp_path, reg)
    row = rb.append_run_started(SID, head_commit=T.C1, utc_stamp=UTC, path=path)
    assert "SUPPLEMENT_RUN_STARTED" in row
    assert row in path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# REVOKED: the owner P2S
# ---------------------------------------------------------------------------

def _revocation_fields():
    return {"reason_code": sreg.OWNER_REVOCATION,
            "successor_authorized_commit": sreg.REVOCATION_NO_SUCCESSOR,
            "incident_id": T.INC, "same_id_reauthorization": "YES"}


def test_an_owner_revocation_resolves_and_leaves_no_live_authorization():
    reg = _live_registry()
    reg.add("P2S", fields=_revocation_fields(), actor=sc.ACTOR_AARON)
    chains = T.resolves(reg.text())
    chain = chains[SID]
    assert chain.live_authorizations == ()
    assert sc.chain_state_refusal("P2S") == "AWAITING_REAUTHORIZATION"
    with pytest.raises(sr.SupplementRunnerError):
        GATE(sr.GateContext(supplement_id=SID, head_commit=T.C1,
                            registry_text=reg.text(), runs_root=None,
                            archive_root=None, frozen_hashes_ok=True,
                            chain=chain, environment_pinned=True))


def test_after_a_revocation_aaron_may_re_authorize_any_commit():
    reg = _live_registry()
    reg.add("P2S", fields=_revocation_fields(), actor=sc.ACTOR_AARON)
    reg.add("P2", commit40=T.C3)
    chain = T.resolves(reg.text())[SID]
    assert len(chain.live_authorizations) == 1
    assert chain.live_authorizations[0].authorized_commit == T.C3


def test_a_main_agent_may_not_write_an_owner_revocation():
    reg = _live_registry()
    reg.add("P2S", fields=dict(_revocation_fields(),
                               aaron_ruling_doc="ops/SYNTHETIC_RULING.md"),
            actor="main agent（Aaron 批复 ops/SYNTHETIC_RULING.md）")
    T.refuse(reg.text(), "p2s_without_preceding_f1")


def test_none_as_successor_is_admitted_only_with_the_revocation_reason():
    reg = _live_registry()
    reg.add("P2S", fields={"reason_code": sreg.PRESTART_COMMIT_CHANGE,
                           "successor_authorized_commit": sreg.REVOCATION_NO_SUCCESSOR,
                           "incident_id": T.INC, "same_id_reauthorization": "YES"},
            actor=sc.ACTOR_AARON)
    T.refuse(reg.text(), "commit_field_not_40hex")


def test_a_revocation_carrying_a_real_successor_is_not_a_revocation():
    reg = _live_registry()
    reg.add("P2S", fields=dict(_revocation_fields(),
                               successor_authorized_commit=T.C2),
            actor=sc.ACTOR_AARON)
    T.refuse(reg.text(), "p2s_without_preceding_f1")


def test_a_revocation_after_the_start_is_still_p2s_after_p3():
    reg = _live_registry()
    reg.add("P3")
    reg.add("P2S", fields=_revocation_fields(), actor=sc.ACTOR_AARON)
    T.refuse(reg.text(), "p2s_after_p3")


# ---------------------------------------------------------------------------
# tolerance: every parser that reads the registry accepts owner rows
# ---------------------------------------------------------------------------

def _s0_parser():
    script = REPO / "scripts" / "s0_real_run.py"
    spec = importlib.util.spec_from_file_location("s0_real_run_for_owner_test", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.parse_registry_events


def test_all_three_registry_parsers_tolerate_owner_rows():
    reg = _live_registry()
    reg.raw(_owner(3, "OWNER_HOLD", "GLOBAL", "reason: x"))
    text = reg.text()
    chains, refusal = sreg.resolve_supplement_chains(text)
    assert refusal is None and SID in chains
    _events, mc_refusal = mreg.parse_mc_events(text)
    assert mc_refusal is None
    s0_rows = _s0_parser()(text)
    assert any(r["event"] == "OWNER_HOLD" for r in s0_rows)


def test_the_real_registry_carries_no_owner_row_yet_and_parses():
    """Read-only, THROUGH THE BOUNDARY (the one read path); nothing is
    written and the registry path is not constructed here."""
    text = rb.read_snapshot().text
    assert oc.parse_owner_rows(text) == ()
    assert oc.active_holds(text, "MC-DS-S004") == ()
