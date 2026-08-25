"""N05 — supplement registry parser / chain resolver.

EVERY registry text in this file is SYNTHETIC and built in memory. No
test writes `ops/TRIAL_REGISTRY.md` or `EXPOSURE_LEDGER.md`, reads real
data, creates a directory or executes anything. The one real file any
test touches is `ops/TRIAL_REGISTRY.md`, READ-ONLY, to assert that the
actual registry authorizes nothing.

NOTHING HERE IS AN AUTHORIZATION. The fixtures contain §13.5-shaped
sentences because the parser must be able to recognise one; every commit
in them is a synthetic constant that is not any commit of this
repository, and `ND1_SUPPLEMENT_EXECUTION_AUTHORIZED=NO` regardless.

TEST SHAPE. Negative tests mutate exactly ONE thing away from a chain
whose positive variant is asserted to resolve, so a red test proves the
specific defect rather than a broken fixture.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from itsf.mc import supplement_contract as sc
from itsf.mc import supplement_registry as sr

# --- synthetic constants ---------------------------------------------------

SID = "MC-DS-S001"
SID2 = "MC-DS-S002"
SID3 = "MC-DS-S003"
C1 = "0123456789abcdef0123456789abcdef01234567"
C2 = "89abcdef0123456789abcdef0123456789abcdef"
C3 = "fedcba9876543210fedcba9876543210fedcba98"
D64 = "ab" * 32
INC = "INC-0123456789ab"
# A genuinely ABSOLUTE path on this platform that is never created.
# The previous POSIX-style "/synthetic/..." is NOT absolute under
# Python 3.13's ntpath (a rooted path with no drive stopped counting
# as absolute), which the N06 output_root check correctly caught.
ROOT = r"C:\synthetic\never-created\output-root"
UTC = "2026-08-20T00:00:00+00:00"
# archive codes are CONTRACT-OWNED and have already been revised
# once under this lane; never hardcode them in a fixture.
ARCHIVE_CODE_A = sc.ARCHIVE_CODES[0]
ARCHIVE_CODE_B = sc.ARCHIVE_CODES[-1]

HEADER = ["| # | utc | event | commit | actor | 原因/备注 |",
          "|---|---|---|---|---|---|"]

ACTORS = {
    sc.ACTOR_MAIN_AGENT: "main agent（Aaron 批复 ops/SYNTHETIC_RULING.md）",
    sc.ACTOR_AARON: sc.ACTOR_AARON,
    sc.ACTOR_AARON_OR_MAIN_AGENT: sc.ACTOR_AARON,
    sc.ACTOR_RUNNER: sc.ACTOR_RUNNER,
    sc.ACTOR_VERIFIER: "fresh Sol verifier",
}


class Reg:
    """Builds synthetic registry markdown one ratified row at a time."""

    def __init__(self, first_seq: int = 1) -> None:
        self.lines: list = []
        self.next_seq = first_seq
        self.commit: dict = {}
        self.p2: dict = {}
        self.f3: dict = {}
        self.last_numbered: dict = {}

    # -- defaults --------------------------------------------------------
    def _defaults(self, short: str, sid: str) -> dict:
        cur = self.commit[sid]
        p2_seq, p2_commit = self.p2.get(sid, ("0", C1))
        target_seq, target_commit = self.p2.get(
            sid, self.last_numbered.get(sid, ("0", C1)))
        return {
            "P1": {"ir_basis": "IR-29b Option B",
                   "schema": "mc_day_strata_supplement.v1",
                   "non_authorization_disclaimer": "this row is not an "
                                                   "authorization"},
            "P2": {"supplement_id": sid, "authorized_commit": cur,
                   "output_root": ROOT},
            "P2S": {"supersedes_event_sequence": p2_seq,
                    "superseded_authorized_commit": p2_commit,
                    "reason_code": "PRESTART_FIX", "incident_id": INC,
                    "successor_authorized_commit": C2,
                    "same_id_reauthorization": "YES"},
            "P3": {"atomic_start_marker": "YES"},
            "P4": {"sealed_sha256": D64, "rows_digest": D64,
                   "day_universe_digest": D64, "source_input_sha256": D64,
                   "method_version": "mc_day_strata_supplement.v1",
                   "n_rows": "1234", "archive": sr.ARCHIVE_OK},
            "A1": {"local_seal_sha256": D64,
                   "archive_code": ARCHIVE_CODE_A,
                   "incident_id": INC, "local_seal_immutable": "YES",
                   "archive_root_attempted": "/synthetic/archive-root"},
            "A2": {"recovery_authorization_doc": "ops/SYNTHETIC_RECOVERY.md",
                   "source_and_archive_exact_inventory_match": "YES",
                   "per_file_sha256_match": "YES", "n_files": "3",
                   "local_seal_sha256_unchanged": "YES", "incident_id": INC},
            "AX": {"archive_code": ARCHIVE_CODE_B,
                   "attempts_count": "3", "incident_id": INC,
                   "aaron_ruling_doc": "ops/SYNTHETIC_RULING.md",
                   "local_seal_sha256": D64, "local_seal_immutable": "YES"},
            "P5": {"rederivation_reproduced": "YES",
                   "headline_replay_identity": "PASS", "n_cells": "42",
                   "attestation_sha256": D64},
            "F1": {"stage": "A_PRECHECK", "gate_name": "git_clean",
                   "error_class": "RunGateError", "incident_id": INC,
                   "consumption_statement": "nothing consumed",
                   "attempts_dir": f"{sid}-A20260820T000000Z"},
            "F2": {"stage": "C_BUILD", "error_class": "SupplementError",
                   "incident_id": INC,
                   "residue_path": "/synthetic/residue",
                   "residue_preserved": "YES"},
            "F2v": {"failure_code": "rederivation_mismatch",
                    "detail": "synthetic", "sealed_artifact_deleted": "NO",
                    "supersession_required": "YES"},
            "F3": {"supersedes_event_sequence": target_seq,
                   "superseded_supplement_id": sid,
                   "superseded_commit": target_commit,
                   "reason_code": "POST_START_FAILURE", "incident_id": INC,
                   "successor_supplement_id": SID2},
            "T1": {"successor_supplement_id": sid,
                   "predecessor_supplement_id": SID,
                   "superseded_at_event": self.f3.get(SID, ("0",))[0],
                   "reason_code": "POST_START_FAILURE",
                   "schema": "mc_day_strata_supplement.v1",
                   "non_authorization_disclaimer": "this row is not an "
                                                   "authorization"},
        }[short]

    # -- construction ----------------------------------------------------
    def add(self, short: str, sid: str = SID, *, commit40=None, fields=None,
            drop=(), commit=None, actor=None, seq=None, note=None, raw=None,
            token=None, utc=UTC):
        spec = sc.EVENTS[short]
        numbered = spec.row_class == sc.NUMBERED
        if commit40:
            self.commit[sid] = commit40
        cur = self.commit.setdefault(sid, C1)
        if seq is None:
            seq = str(self.next_seq) if numbered else sc.UNNUMBERED_SEQ_TOKEN
            if numbered:
                self.next_seq += 1
        cell = commit if commit is not None else (cur if numbered
                                                  else cur[:7])
        values = self._defaults(short, sid)
        if fields:
            values.update(fields)
        for key in drop:
            values.pop(key, None)
        if note is None:
            body = "; ".join(f"{k}: {v}" for k, v in values.items())
            head = (sr.execution_sentence_header(sid) + " ") if short == "P2" \
                else ""
            note = f"[{sid}] {head}{body}"
        if raw is None:
            raw = (f"| {seq} | {utc} | **{token or spec.token}** | {cell} "
                   f"| {actor or ACTORS[spec.actor]} | {note} |")
        self.lines.append(raw)
        if numbered:
            self.last_numbered[sid] = (seq, cell)
            if short == "P2":
                self.p2[sid] = (seq, cell)
            if short == "F3":
                self.f3[sid] = (seq, cell)
        return self

    def raw(self, line: str):
        self.lines.append(line)
        return self

    def chain(self, shorts, sid=SID):
        for short in shorts:
            self.add(short, sid)
        return self

    def text(self) -> str:
        return "\n".join(["# synthetic registry (NOT the real one)", "",
                          *HEADER, *self.lines, ""])


# --- assertions ------------------------------------------------------------

def refuse(text: str, code: str | None = None) -> sr.Refusal:
    chains, refusal = sr.resolve_supplement_chains(text)
    assert refusal is not None, "expected a refusal, resolution succeeded"
    assert chains == {}, "a refused resolution must yield NO chains"
    assert refusal.code in sr.REFUSAL_CODES, refusal.code
    if code is not None:
        assert refusal.code == code, f"{refusal.code} != {code} ({refusal})"
    return refusal


def resolves(text: str) -> dict:
    chains, refusal = sr.resolve_supplement_chains(text)
    assert refusal is None, f"unexpected refusal: {refusal}"
    return chains


def happy(shorts=("P1", "P2", "P3", "P4", "P5")) -> Reg:
    return Reg().chain(shorts)


# ===========================================================================
# 1 — six-cell row contract
# ===========================================================================

def test_minimal_success_chain_resolves():
    chains = resolves(happy().text())
    assert chains[SID].short_ids == ("P1", "P2", "P3", "P4", "P5")
    assert chains[SID].terminal == "P5"
    assert chains[SID].closed is True


def test_bold_and_bare_event_cells_are_equivalent():
    bold = happy().text()
    bare = bold.replace("**", "")
    assert resolves(bare)[SID].short_ids == resolves(bold)[SID].short_ids


def test_header_and_separator_rows_are_not_events():
    rows, refusal = sr.parse_registry_rows("\n".join(HEADER))
    assert refusal is None
    assert rows == ()


def test_prose_mention_is_never_an_event():
    reg = happy()
    text = reg.text() + "\nThe token SUPPLEMENT_SEALED is mentioned in prose "\
                        "and is not a row.\n"
    assert resolves(text)[SID].short_ids == ("P1", "P2", "P3", "P4", "P5")


def test_fenced_row_shaped_line_is_documentation_not_an_event():
    reg = happy(("P1", "P2"))
    fenced = ("```\n"
              f"| 9 | {UTC} | **{sc.EVENTS['P5'].token}** | {C1} | verifier "
              f"| [{SID}] documentation only |\n"
              "```\n")
    chains = resolves(reg.text() + "\n" + fenced)
    assert chains[SID].short_ids == ("P1", "P2")


def test_fenced_malformed_row_is_not_refused():
    reg = happy(("P1", "P2"))
    fenced = "```\n| 9 | oops | **SUPPLEMENT_SEALED** |\n```\n"
    assert resolves(reg.text() + "\n" + fenced)[SID].short_ids == ("P1", "P2")


# ===========================================================================
# 2 — malformed-row policy B (ratified: refuse, never silently drop)
# ===========================================================================

def test_malformed_supplement_row_refuses_instead_of_vanishing():
    reg = happy(("P1", "P2", "P3"))
    reg.raw(f"| + | {UTC} | **{sc.EVENTS['P4'].token}** | {C1[:7]} "
            f"| {sc.ACTOR_RUNNER} | [{SID}] n_rows: 3 | extra |")
    refusal = refuse(reg.text(), "supplement_row_malformed")
    assert "SUPPLEMENT_SEALED" in refusal.detail


def test_malformed_row_missing_trailing_pipe_refuses():
    reg = happy(("P1", "P2", "P3"))
    reg.raw(f"| + | {UTC} | **{sc.EVENTS['P4'].token}** | {C1[:7]} "
            f"| {sc.ACTOR_RUNNER} | [{SID}] truncated")
    refuse(reg.text(), "supplement_row_malformed")


def test_malformed_row_without_supplement_token_keeps_s0_behaviour():
    """The S0 parser silently ignores non-six-cell lines; policy B narrows
    that ONLY for supplement-family rows, so unrelated table junk must
    still not refuse."""
    reg = happy()
    reg.raw("| 99 | just | three |")
    assert resolves(reg.text())[SID].closed is True


def test_deferred_mc_family_malformed_row_also_refuses():
    reg = happy(("P1", "P2"))
    reg.raw(f"| + | {UTC} | **MC_RUN_STARTED** | {C1[:7]} |")
    refuse(reg.text(), "supplement_row_malformed")


# ===========================================================================
# 3 — numbered vs unnumbered, GLOBAL sequence
# ===========================================================================

def test_plus_rows_consume_no_sequence_number():
    reg = happy(("P1", "P2", "P3", "P4", "P5"))
    chains = resolves(reg.text())
    seqs = [e.seq for e in chains[SID].events]
    assert seqs == ["1", "2", "+", "+", "3"]


def test_numbered_row_with_plus_seq_refused():
    reg = Reg().chain(("P1", "P2", "P3", "P4"))
    reg.add("P5", seq="+")
    refuse(reg.text(), "numbered_row_with_plus_seq")


def test_unnumbered_row_with_integer_seq_refused():
    reg = Reg().chain(("P1", "P2"))
    reg.add("P3", seq="7")
    refuse(reg.text(), "unnumbered_row_with_integer_seq")


def test_numbered_row_with_non_integer_seq_refused():
    reg = Reg().chain(("P1", "P2", "P3", "P4"))
    reg.add("P5", seq="7a")
    refuse(reg.text(), "supplement_seq_not_integer")


def test_supplement_row_must_continue_the_global_sequence():
    reg = Reg(first_seq=5).chain(("P1",))
    reg.add("P2", seq="4")
    refuse(reg.text(), "supplement_seq_not_next_value")


def test_supplement_row_may_not_duplicate_an_existing_sequence():
    reg = Reg()
    reg.raw(f"| 1 | 2026-07-31 | TRIAL_REGISTERED | 79d7ca3 | main agent "
            f"| pre-existing S0 row |")
    reg.next_seq = 1
    reg.chain(("P1",))                    # also numbered 1 -> collision
    refuse(reg.text(), "supplement_seq_duplicate")


def test_numbered_supplement_row_follows_existing_s0_rows():
    """GLOBAL namespace: the supplement chain simply continues 1..13."""
    reg = Reg(first_seq=14)
    reg.raw(f"| 13 | 2026-08-14 | **RUN_AUTHORIZED** | {C3} | Aaron "
            f"| pre-existing S0 row |")
    reg.chain(("P1", "P2", "P3", "P4", "P5"))
    assert [e.seq for e in resolves(reg.text())[SID].events] == \
        ["14", "15", "+", "+", "16"]


# ===========================================================================
# 4 — commit width by row class
# ===========================================================================

def test_numbered_row_requires_40hex_commit():
    reg = Reg().chain(("P1",))
    reg.add("P2", commit=C1[:7])
    refuse(reg.text(), "commit_width_mismatch_for_row_class")


def test_unnumbered_row_requires_7hex_commit():
    reg = Reg().chain(("P1", "P2"))
    reg.add("P3", commit=C1)
    refuse(reg.text(), "commit_width_mismatch_for_row_class")


# ===========================================================================
# 5 — note fields
# ===========================================================================

def test_unknown_field_refused():
    reg = Reg()
    reg.add("P1", fields={"unexpected_key": "x"})
    refuse(reg.text(), "unknown_field_in_note")


def test_missing_required_field_refused():
    reg = Reg()
    reg.add("P1", drop=("schema",))
    refusal = refuse(reg.text(), "missing_required_field")
    assert "schema" in refusal.detail


def test_duplicate_field_refused():
    reg = Reg()
    reg.add("P1", note=f"[{SID}] ir_basis: a; ir_basis: b; "
                       "schema: s; non_authorization_disclaimer: d")
    refuse(reg.text(), "duplicate_field_in_note")


def test_note_segment_that_is_not_a_field_refused():
    reg = Reg()
    reg.add("P1", note=f"[{SID}] ir_basis: a; free prose; schema: s; "
                       "non_authorization_disclaimer: d")
    refuse(reg.text(), "note_segment_not_field")


def test_note_without_supplement_id_bracket_refused():
    reg = Reg()
    reg.add("P1", note="ir_basis: a; schema: s; "
                       "non_authorization_disclaimer: d")
    refuse(reg.text(), "note_missing_supplement_id_bracket")


def test_note_bracket_must_match_the_id_pattern():
    reg = Reg()
    reg.add("P1", note="[MC-DS-1] ir_basis: a; schema: s; "
                       "non_authorization_disclaimer: d")
    refuse(reg.text(), "supplement_id_pattern_violation")


def test_supplement_id_field_must_equal_the_bracket():
    reg = Reg().chain(("P1",))
    reg.add("P2", fields={"supplement_id": SID2})
    refuse(reg.text(), "supplement_id_bracket_field_mismatch")


def test_empty_field_value_refused():
    reg = Reg()
    reg.add("P1", fields={"schema": ""})
    refuse(reg.text(), "field_value_empty")


@pytest.mark.parametrize("short,field,value,code", [
    ("P4", "sealed_sha256", "abc", "digest_field_not_64hex"),
    ("P4", "n_rows", "many", "integer_field_not_integer"),
    ("F1", "stage", "Z_UNKNOWN", "stage_outside_closed_enum"),
    ("F1", "gate_name", "no_such_gate", "gate_name_outside_closed_enum"),
    ("F1", "incident_id", "INC-xyz", "incident_id_malformed"),
    ("F2", "residue_preserved", "NO", "yes_field_not_yes"),
    ("F2v", "failure_code", "made_up", "failure_code_outside_closed_enum"),
    ("F2v", "sealed_artifact_deleted", "YES", "no_field_not_no"),
    ("A1", "archive_code", "disk_gremlins",
     "a1_archive_code_outside_closed_enum"),
    ("P5", "headline_replay_identity", "MAYBE",
     "enum_field_outside_closed_enum"),
])
def test_closed_value_vocabularies(short, field, value, code):
    prefix = {"P4": ("P1", "P2", "P3"), "F1": ("P1", "P2"),
              "F2": ("P1", "P2", "P3"), "F2v": ("P1", "P2", "P3", "P4"),
              "A1": ("P1", "P2", "P3"), "P5": ("P1", "P2", "P3", "P4")}[short]
    ok = Reg().chain(prefix)
    ok.add(short)
    resolves(ok.text())                                   # positive control
    reg = Reg().chain(prefix)
    reg.add(short, fields={field: value})
    refuse(reg.text(), code)


def test_f3_reason_code_must_be_a_closed_token():
    reg = Reg().chain(("P1", "P2"))
    reg.add("F3", fields={"reason_code": "lower case"})
    refuse(reg.text(), "reason_code_malformed")


# ===========================================================================
# 6 — P2 actor and verbatim §13.5 sentence
# ===========================================================================

def test_p2_actor_must_be_aaron():
    reg = Reg().chain(("P1",))
    reg.add("P2", actor="main agent")
    refuse(reg.text(), "p2_actor_not_aaron")


def test_p2_requires_the_verbatim_sentence_header():
    reg = Reg().chain(("P1",))
    reg.add("P2", note=f"[{SID}] supplement_id: {SID}; "
                       f"authorized_commit: {C1}; output_root: {ROOT}")
    refuse(reg.text(), "p2_missing_verbatim_authorization_sentence")


@pytest.mark.parametrize("missing",
                         ["supplement_id", "authorized_commit", "output_root"])
def test_p2_sentence_missing_any_of_three_fields_refused(missing):
    reg = Reg().chain(("P1",))
    reg.add("P2", drop=(missing,))
    refuse(reg.text(), "p2_missing_verbatim_authorization_sentence")


def test_p2_row_commit_cell_must_equal_the_sentence_commit():
    """IR-25 fixture 7, mirrored."""
    reg = Reg().chain(("P1",))
    reg.add("P2", commit=C2)              # cell C2, sentence still C1
    refuse(reg.text(), "p2_row_commit_cell_ne_sentence_commit")


def test_p2_sentence_commit_must_be_40hex():
    reg = Reg().chain(("P1",))
    reg.add("P2", fields={"authorized_commit": C1[:7]})
    refuse(reg.text(), "commit_field_not_40hex")


def test_p2_header_is_bound_to_the_supplement_id():
    header = sr.execution_sentence_header(SID2)
    assert header == "START_MC_DS_S002_DAY_STRATA_SUPPLEMENT_EXECUTION"


# ===========================================================================
# 7 — the eleven P2S refusal codes
# ===========================================================================

def p2s_happy() -> Reg:
    reg = Reg().chain(("P1", "P2", "F1"))
    reg.add("P2S")
    reg.add("P2", commit40=C2)
    reg.add("P3")
    return reg


def test_p2s_reauthorization_chain_resolves():
    chains = resolves(p2s_happy().text())
    assert chains[SID].short_ids == ("P1", "P2", "F1", "P2S", "P2", "P3")
    assert chains[SID].started is True


def test_p2s_code_names_mirror_the_packet():
    assert [c.upper() for c in sr.P2S_REFUSAL_CODES] == [
        "P2S_NO_TARGET_P2", "P2S_TARGET_NOT_LIVE", "P2S_TARGET_AMBIGUOUS",
        "P2S_FORWARD_REFERENCE", "P2S_COMMIT_MISMATCH",
        "P2S_SUPPLEMENT_ID_MISMATCH", "P2S_DUPLICATE_SUPERSEDE",
        "P2S_SUCCESSOR_EQUALS_SUPERSEDED", "P2S_WITHOUT_PRECEDING_F1",
        "P2S_AFTER_P3", "MULTIPLE_LIVE_P2_AFTER_P2S"]
    assert set(sr.P2S_REFUSAL_CODES) <= sr.REFUSAL_CODES


def test_p2s_no_target_p2():
    reg = Reg().chain(("P1", "P2", "F1"))
    reg.add("P2S", fields={"supersedes_event_sequence": "1"})   # the P1 row
    refuse(reg.text(), "p2s_no_target_p2")


def test_p2s_target_not_live():
    reg = Reg().chain(("P1", "P2", "F1"))
    reg.add("F3")                                     # retires the id first
    reg.add("P2S")
    refuse(reg.text(), "p2s_target_not_live")


def test_p2s_target_ambiguous():
    reg = Reg().chain(("P1", "P2", "F1"))
    reg.add("P1", SID2, seq="2")                      # second row numbered 2
    reg.add("P2S")
    refuse(reg.text(), "p2s_target_ambiguous")


def test_p2s_forward_reference():
    reg = Reg().chain(("P1",))
    reg.add("P2S", fields={"supersedes_event_sequence": "3",
                           "superseded_authorized_commit": C1})
    reg.add("P2")
    refuse(reg.text(), "p2s_forward_reference")


def test_p2s_commit_mismatch():
    reg = Reg().chain(("P1", "P2", "F1"))
    reg.add("P2S", fields={"superseded_authorized_commit": C3})
    refuse(reg.text(), "p2s_commit_mismatch")


def test_p2s_supplement_id_mismatch():
    reg = Reg().chain(("P1", "P2", "F1"))
    reg.add("P1", SID2)
    reg.add("P2S", SID2, fields={"supersedes_event_sequence": "2",
                                 "superseded_authorized_commit": C1})
    refuse(reg.text(), "p2s_supplement_id_mismatch")


def test_p2s_duplicate_supersede():
    reg = Reg().chain(("P1", "P2", "F1"))
    reg.add("P2S")
    reg.add("P2", commit40=C2)
    reg.add("F1")
    reg.add("P2S", fields={"supersedes_event_sequence": "2",
                           "superseded_authorized_commit": C1})
    refuse(reg.text(), "p2s_duplicate_supersede")


def test_p2s_successor_equals_superseded():
    reg = Reg().chain(("P1", "P2", "F1"))
    reg.add("P2S", fields={"successor_authorized_commit": C1})
    refuse(reg.text(), "p2s_successor_equals_superseded")


def test_p2s_without_preceding_f1():
    reg = Reg().chain(("P1", "P2"))
    reg.add("P2S")
    refuse(reg.text(), "p2s_without_preceding_f1")


def test_p2s_after_p3():
    reg = Reg().chain(("P1", "P2", "P3"))
    reg.add("P2S")
    refuse(reg.text(), "p2s_after_p3")


def test_multiple_live_p2_after_p2s_is_guarded():
    """Post-condition guard. Two live P2s are unreachable through registry
    text because the incoming-P2 check refuses first, so this asserts the
    guard itself rather than pretending to reach it."""
    assert sr._check_live_p2_uniqueness(1, after_p2s=True) is None
    assert sr._check_live_p2_uniqueness(2, after_p2s=True) == \
        "multiple_live_p2_after_p2s"
    assert sr._check_live_p2_uniqueness(2, after_p2s=False) == \
        "multiple_live_p2_for_one_id"


def test_p2s_main_agent_must_cite_aarons_ruling():
    ok = Reg().chain(("P1", "P2", "F1"))
    ok.add("P2S", actor="main agent",
           fields={"aaron_ruling_doc": "ops/SYNTHETIC_RULING.md"})
    ok.add("P2", commit40=C2)
    resolves(ok.text())
    reg = Reg().chain(("P1", "P2", "F1"))
    reg.add("P2S", actor="main agent")
    refuse(reg.text(), "p2s_main_agent_without_aaron_ruling_doc")


def test_reauthorized_p2_must_carry_the_declared_successor_commit():
    reg = Reg().chain(("P1", "P2", "F1"))
    reg.add("P2S")                                    # declares successor C2
    reg.add("P2", commit40=C3)
    refuse(reg.text(), "p2s_successor_commit_mismatch")


# ===========================================================================
# 8 — at most one live P2 per id
# ===========================================================================

def test_second_authorization_while_one_is_live_refused():
    reg = Reg().chain(("P1", "P2"))
    reg.add("P2", commit40=C2)
    refuse(reg.text(), "multiple_live_p2_for_one_id")


def test_live_authorization_is_consumed_by_the_run_start():
    """`EXECUTION_SENTENCE_ONE_RUN_ONLY=YES` — after P3 the authorization
    is spent, so the resolver stops reporting it as live."""
    before = sr.resolve_supplement_chain(Reg().chain(("P1", "P2")).text(), SID)
    assert len(before.live_authorizations) == 1
    after = sr.resolve_supplement_chain(
        Reg().chain(("P1", "P2", "P3")).text(), SID)
    assert after.live_authorizations == ()


# ===========================================================================
# 9 — pre-start commit change
# ===========================================================================

def test_f1_then_retry_with_unchanged_commit_resolves():
    reg = Reg().chain(("P1", "P2", "F1", "P3"))
    assert resolves(reg.text())[SID].short_ids == ("P1", "P2", "F1", "P3")


def test_prestart_commit_change_without_p2s_refused():
    reg = Reg().chain(("P1", "P2", "F1"))
    reg.add("P3", commit=C2[:7])
    refuse(reg.text(), "prestart_commit_change_requires_p2s")


def test_run_start_commit_must_match_the_live_authorization():
    reg = Reg().chain(("P1", "P2"))
    reg.add("P3", commit=C2[:7])
    refuse(reg.text(), "p3_commit_not_authorized_by_live_p2")


def test_f1_to_p2_directly_is_a_forbidden_edge():
    reg = Reg().chain(("P1", "P2", "F1"))
    reg.add("P2", commit40=C2)
    refuse(reg.text(), "f1_to_p2_without_p2s")


def test_run_start_without_a_live_authorization_is_guarded():
    """Guard-level: every edge into P3 implies a live P2, so this asserts
    the guard directly with a doctored supersede state."""
    events, refusal = sr.parse_supplement_events(
        Reg().chain(("P1", "P2", "F1", "P3")).text())
    assert refusal is None
    state = sr._SupersedeState()
    state.dead_p2_positions[events[1].pos] = 0         # kill the live P2
    resolution, refusal = sr._walk_chain(SID, list(events), state)
    assert resolution is None
    assert refusal.code == "p3_without_live_p2"


# ===========================================================================
# 10 — post-start failure needs a NEW id via F3 -> T1 -> P2'
# ===========================================================================

def successor_chain() -> Reg:
    reg = Reg().chain(("P1", "P2", "P3", "F2", "F3"))
    reg.add("T1", SID2)
    reg.add("P2", SID2, commit40=C3)
    return reg


def test_post_start_failure_retries_under_a_new_id():
    chains = resolves(successor_chain().text())
    assert chains[SID].short_ids == ("P1", "P2", "P3", "F2", "F3")
    assert chains[SID].retired is True
    assert chains[SID].live_authorizations == ()
    assert chains[SID2].short_ids == ("T1", "P2")
    assert len(chains[SID2].live_authorizations) == 1


def test_in_place_retry_after_post_start_failure_refused():
    reg = Reg().chain(("P1", "P2", "P3", "F2"))
    reg.add("P3")
    refuse(reg.text(), "f2_to_p3_in_place_retry")


def test_retired_id_may_not_be_reused():
    reg = Reg().chain(("P1", "P2", "P3", "F2", "F3"))
    reg.add("P1")                                     # same id again
    refuse(reg.text(), "retired_supplement_id_reused")


def test_f3_successor_may_not_reuse_the_retired_id():
    reg = Reg().chain(("P1", "P2", "P3", "F2"))
    reg.add("F3", fields={"successor_supplement_id": SID})
    refuse(reg.text(), "f3_successor_equals_superseded_id")


def test_successor_id_must_be_registered_by_t1():
    reg = Reg().chain(("P1", "P2", "P3", "F2", "F3"))
    reg.add("P1", SID2)                               # P1, not T1
    refuse(reg.text(), "f3_successor_not_registered_by_t1")


def test_pending_successor_registration_is_not_a_defect():
    reg = Reg().chain(("P1", "P2", "P3", "F2", "F3"))
    assert resolves(reg.text())[SID].terminal == "F3"


def test_t1_bracket_must_equal_its_successor_id():
    reg = Reg().chain(("P1", "P2", "P3", "F2", "F3"))
    reg.add("T1", SID2, fields={"successor_supplement_id": SID3})
    refuse(reg.text(), "t1_bracket_id_not_successor_id")


def test_t1_successor_may_not_equal_its_predecessor():
    reg = Reg().chain(("P1", "P2", "P3", "F2", "F3"))
    reg.add("T1", SID2, fields={"predecessor_supplement_id": SID2})
    refuse(reg.text(), "t1_successor_equals_predecessor")


def test_t1_without_a_superseding_f3_refused():
    reg = Reg().chain(("P1", "P2"))
    reg.add("T1", SID2, fields={"superseded_at_event": "1"})
    refuse(reg.text(), "t1_predecessor_not_superseded_by_f3")


def test_t1_predecessor_f3_must_name_this_successor():
    reg = Reg().chain(("P1", "P2", "P3", "F2"))
    reg.add("F3", fields={"successor_supplement_id": SID3})
    reg.add("T1", SID2)
    refuse(reg.text(), "t1_predecessor_f3_names_other_successor")


def test_t1_superseded_at_event_must_equal_the_f3_sequence():
    reg = Reg().chain(("P1", "P2", "P3", "F2", "F3"))
    reg.add("T1", SID2, fields={"superseded_at_event": "99"})
    refuse(reg.text(), "t1_superseded_at_event_mismatch")


def test_t1_may_not_precede_its_f3():
    # seq values must now be the NEXT global value (N06 repair), so the
    # forward reference is expressed as 3 -> 4 rather than 4 -> 5.
    reg = Reg().chain(("P1", "P2", "P3", "F2"))
    reg.add("T1", SID2, seq="3", fields={"superseded_at_event": "4"})
    reg.add("F3", seq="4")
    refuse(reg.text(), "t1_forward_reference")


@pytest.mark.parametrize("code,mutate", [
    ("f3_no_target_row",
     lambda r: r.add("F3", fields={"supersedes_event_sequence": "99"})),
    ("f3_commit_mismatch",
     lambda r: r.add("F3", fields={"superseded_commit": C3})),
    ("f3_supplement_id_mismatch",
     lambda r: r.add("F3", fields={"superseded_supplement_id": SID2})),
])
def test_f3_supersede_reference_fails_closed(code, mutate):
    ok = Reg().chain(("P1", "P2", "P3", "F2"))
    ok.add("F3")
    resolves(ok.text())                                   # positive control
    reg = Reg().chain(("P1", "P2", "P3", "F2"))
    mutate(reg)
    refuse(reg.text(), code)


def test_f3_target_ambiguous():
    reg = Reg().chain(("P1", "P2", "P3", "F2"))
    reg.add("P1", SID2, seq="2")
    reg.add("F3")
    refuse(reg.text(), "f3_target_ambiguous")


def test_f3_forward_reference():
    reg = Reg().chain(("P1",))
    reg.add("F3", fields={"supersedes_event_sequence": "3",
                          "superseded_commit": C1})
    reg.add("P1", SID2, seq="3")
    refuse(reg.text(), "f3_forward_reference")


def test_f3_duplicate_supersede():
    reg = Reg().chain(("P1", "P2", "F1"))
    reg.add("F3")
    reg.add("F3", fields={"supersedes_event_sequence": "2",
                          "superseded_commit": C1})
    refuse(reg.text(), "f3_duplicate_supersede")


def test_f3_target_must_belong_to_the_superseded_id():
    reg = Reg().chain(("P1",))
    reg.add("P1", SID2)
    reg.add("F3", fields={"supersedes_event_sequence": "2",
                          "superseded_commit": C1})
    refuse(reg.text(), "f3_target_supplement_id_mismatch")


# ===========================================================================
# 11 — archive policy A, every branch
# ===========================================================================

def test_archive_ok_path_p4_then_p5():
    assert resolves(happy().text())[SID].terminal == "P5"


def test_archive_recovery_path_a1_a2_p5():
    reg = Reg().chain(("P1", "P2", "P3", "A1", "A2", "P5"))
    chains = resolves(reg.text())
    assert chains[SID].short_ids == ("P1", "P2", "P3", "A1", "A2", "P5")
    assert chains[SID].closed is True


def test_archive_permanent_failure_path_a1_ax_f3():
    reg = Reg().chain(("P1", "P2", "P3", "A1", "AX", "F3"))
    chains = resolves(reg.text())
    assert chains[SID].terminal == "F3"
    assert chains[SID].retired is True


def test_p4_may_not_carry_archive_failed_under_policy_a():
    reg = Reg().chain(("P1", "P2", "P3"))
    reg.add("P4", fields={"archive": f"archive_failed:{ARCHIVE_CODE_A}"})
    refuse(reg.text(), "p4_with_archive_failed_under_policy_a")


def test_p4_archive_code_outside_the_closed_enum_refused():
    reg = Reg().chain(("P1", "P2", "P3"))
    reg.add("P4", fields={"archive": "archive_failed:cosmic_rays"})
    refuse(reg.text(), "archive_code_outside_closed_enum")


def test_p4_archive_field_must_be_well_formed():
    reg = Reg().chain(("P1", "P2", "P3"))
    reg.add("P4", fields={"archive": "probably fine"})
    refuse(reg.text(), "archive_field_malformed")


def test_a1_without_local_seal_digest_refused():
    reg = Reg().chain(("P1", "P2", "P3"))
    reg.add("A1", drop=("local_seal_sha256",))
    refuse(reg.text(), "a1_without_local_seal_digest")


def test_a2_without_recovery_authorization_doc_refused():
    reg = Reg().chain(("P1", "P2", "P3", "A1"))
    reg.add("A2", drop=("recovery_authorization_doc",))
    refuse(reg.text(), "a2_without_recovery_authorization_doc")


def test_a2_inventory_claimed_without_a_complete_sha_table_refused():
    # N06 repair: `n_files: 0` is now refused one layer EARLIER by the
    # generic integer floor, which subsumes this A2-specific branch for
    # the zero case. Both refuse; only the code differs. The A2 guard is
    # retained as defence-in-depth and is disclosed as a third
    # guard-level code alongside multiple_live_p2_after_p2s and
    # p3_without_live_p2.
    reg = Reg().chain(("P1", "P2", "P3", "A1"))
    reg.add("A2", fields={"n_files": "0"})
    refuse(reg.text(), "integer_field_below_minimum")


def test_a2_local_seal_digest_changed_refused():
    reg = Reg().chain(("P1", "P2", "P3", "A1"))
    reg.add("A2", fields={"local_seal_sha256_unchanged": "NO"})
    refuse(reg.text(), "a2_local_seal_digest_changed")


def test_a2_without_preceding_a1_refused():
    reg = Reg().chain(("P1", "P2", "P3", "P4"))
    reg.add("A2")
    refuse(reg.text(), "a2_without_preceding_a1")


def test_ax_without_preceding_a1_refused():
    reg = Reg().chain(("P1", "P2", "P3", "P4"))
    reg.add("AX")
    refuse(reg.text(), "ax_without_preceding_a1")


def test_ax_without_aarons_ruling_doc_refused():
    reg = Reg().chain(("P1", "P2", "P3", "A1"))
    reg.add("AX", drop=("aaron_ruling_doc",))
    refuse(reg.text(), "ax_without_aaron_ruling_doc")


def test_p5_after_a1_without_a2_refused():
    reg = Reg().chain(("P1", "P2", "P3", "A1"))
    reg.add("P5")
    refuse(reg.text(), "p5_after_a1_without_a2")


def test_p5_after_ax_refused():
    reg = Reg().chain(("P1", "P2", "P3", "A1", "AX"))
    reg.add("P5")
    refuse(reg.text(), "p5_after_ax")


def test_p5_predecessor_must_be_p4_or_a2():
    reg = Reg().chain(("P1", "P2", "P3"))
    reg.add("P5")
    refuse(reg.text(), "p5_predecessor_not_p4_or_a2")


def test_ax_successor_must_be_f3():
    reg = Reg().chain(("P1", "P2", "P3", "A1", "AX"))
    reg.add("A2")
    refuse(reg.text(), "ax_successor_not_f3")


def test_chain_ending_at_ax_is_unclosed():
    reg = Reg().chain(("P1", "P2", "P3", "A1", "AX"))
    refuse(reg.text(), "ax_treated_as_terminal")


def test_chain_pausing_at_a1_is_not_a_defect():
    """A1 awaiting Aaron's archive ruling is a legitimate open state; only
    a chain STOPPING at AX is the ratified refusal."""
    reg = Reg().chain(("P1", "P2", "P3", "A1"))
    chains = resolves(reg.text())
    assert chains[SID].closed is False
    assert chains[SID].terminal == ""


def test_p5_may_not_record_a_failed_verification():
    reg = Reg().chain(("P1", "P2", "P3", "P4"))
    reg.add("P5", fields={"rederivation_reproduced": "NO"})
    refuse(reg.text(), "p5_claims_failed_verification")


def test_p5_verifier_may_not_be_the_producing_seat():
    reg = Reg().chain(("P1", "P2", "P3", "P4"))
    reg.add("P5", actor="main agent")
    refuse(reg.text(), "verifier_actor_is_producer_or_aaron")


def test_runner_rows_must_carry_the_runner_actor():
    reg = Reg().chain(("P1", "P2"))
    reg.add("P3", actor="Aaron")
    refuse(reg.text(), "actor_not_permitted_for_event")


def test_archive_unclassified_code_is_never_a_legal_a1_code():
    """`ARCHIVE_UNCLASSIFIED_CODE` is the runner's refusal for an archive
    report it could not classify; it must never be recordable as if the
    failure were understood."""
    # Asserted, never skipped: if the contract stops exposing this code
    # the AttributeError is a REAL failure, not a reason to go quiet.
    code = sc.ARCHIVE_UNCLASSIFIED_CODE
    assert code not in sc.ARCHIVE_CODES
    reg = Reg().chain(("P1", "P2", "P3"))
    reg.add("A1", fields={"archive_code": code})
    refuse(reg.text(), "a1_archive_code_outside_closed_enum")


def test_non_terminal_traps_never_close_a_chain():
    for short in sc.NON_TERMINAL_TRAPS:
        assert short not in sc.TERMINAL_SHORT_IDS
    reg = Reg().chain(("P1", "P2", "P3", "A1"))
    assert resolves(reg.text())[SID].closed is False


def test_archive_codes_come_from_the_contract():
    assert set(sr.ARCHIVE_REFUSAL_CODES) <= sr.REFUSAL_CODES
    for code in sc.ARCHIVE_CODES:
        reg = Reg().chain(("P1", "P2", "P3"))
        reg.add("A1", fields={"archive_code": code})
        resolves(reg.text())


# ===========================================================================
# 12 / 13 — deferred and unknown tokens
# ===========================================================================

@pytest.mark.parametrize("token", sc.ND3_STILL_REFUSED_BY_NAME)
def test_nd3_deferred_tokens_refused_by_name(token):
    """Three of §D.3.4's five, not all five.

    `MC-REG-COLLISION-001` C3 discharged two of them — see the companion
    test below. The parametrization moved to `ND3_STILL_REFUSED_BY_NAME`
    rather than to a hand-written list of three, so it can never disagree
    with the exclusion it is derived from."""
    reg = Reg().chain(("P1", "P2", "P3", "P4", "P5"))
    reg.raw(f"| 4 | {UTC} | **{token}** | {C1} | main agent "
            f"| [{SID}] schema: x |")
    refusal = refuse(reg.text(), "token_deferred_to_nd3")
    assert token in refusal.detail
    assert "N-D3" in refusal.detail


@pytest.mark.parametrize("token", sc.ND3_DEFERRAL_DISCHARGED)
def test_the_two_discharged_tokens_are_skipped_as_another_lifecycles_rows(
        token):
    """The discharge, at the only place it is observable.

    §D.3.4 deferred these two under a stated condition — "before the N-D3
    ruling" — for a stated reason: their lifecycle definitions were
    incomplete. N-D3 (G1-G8) supplied those definitions, so the guard's own
    condition has fired. They are now `mc_registry`'s rows and this grammar
    skips them the way it has always skipped `MC_BRANCH_SEALED`.

    Skipping is not permissiveness: nothing may act on this file except
    through `registry_boundary`, which runs MC resolution over the SAME
    snapshot and refuses everything if the MC record is broken. That
    coupling is pinned in `tests/test_registry_boundary.py`."""
    reg = Reg().chain(("P1", "P2", "P3", "P4", "P5"))
    reg.raw(f"| 4 | {UTC} | **{token}** | {C1} | Aaron "
            f"| [MC-R001] run_id: MC-R001 |")
    chains, refusal = sr.resolve_supplement_chains(reg.text())
    assert refusal is None, f"{token} should no longer be refused here"
    assert chains, "the supplement chain must still resolve"


def test_the_ratified_five_name_transcription_is_still_verifiable():
    """C3: the discharge is an EXCLUSION citing the ruling, never a silent
    deletion of names from a ratified list. Someone checking this file
    against §D.3.4 must still find all five."""
    assert len(sc.ND3_DEFERRED_TOKENS) == 5
    assert set(sc.ND3_DEFERRAL_DISCHARGED) < set(sc.ND3_DEFERRED_TOKENS)
    assert set(sc.ND3_STILL_REFUSED_BY_NAME) == (
        set(sc.ND3_DEFERRED_TOKENS) - set(sc.ND3_DEFERRAL_DISCHARGED))
    assert "MC-REG-COLLISION-001" in sc.ND3_DEFERRAL_DISCHARGED_BY
    assert "DELEGATED=YES" in sc.ND3_DEFERRAL_DISCHARGED_BY


def test_the_grid_replay_deferral_was_not_discharged():
    """Its condition never fired. N-D3 ruled the MC event family; it ruled
    nothing about the GRID-replay coupling, which is the reason §D.3.4
    gave for deferring this one."""
    assert "SUPPLEMENT_CONSUMED_BY_GRID_REPLAY" in sc.ND3_STILL_REFUSED_BY_NAME
    assert "SUPPLEMENT_CONSUMED_BY_GRID_REPLAY" \
        not in sc.ND3_DEFERRAL_DISCHARGED


def test_p6_grid_replay_consumption_is_deferred():
    assert "SUPPLEMENT_CONSUMED_BY_GRID_REPLAY" in sc.ND3_DEFERRED_TOKENS


def test_unknown_lookalike_token_is_named_in_the_refusal():
    reg = Reg().chain(("P1",))
    reg.raw(f"| 2 | {UTC} | **SUPPLEMENT_EXECUTION_APPROVED** | {C1} | Aaron "
            f"| [{SID}] supplement_id: {SID} |")
    refusal = refuse(reg.text(), "unknown_event_token")
    assert "SUPPLEMENT_EXECUTION_APPROVED" in refusal.detail


# ===========================================================================
# every forbidden edge
# ===========================================================================

PREFIX = {
    "F1": ("P1", "P2", "F1"),
    "A1": ("P1", "P2", "P3", "A1"),
    "AX": ("P1", "P2", "P3", "A1", "AX"),
    "P2S": ("P1", "P2", "F1", "P2S"),
    "P3": ("P1", "P2", "P3"),
    "F2": ("P1", "P2", "P3", "F2"),
}


def test_forbidden_edge_code_table_covers_the_contract():
    assert set(sr.FORBIDDEN_EDGE_CODES) == set(sc.FORBIDDEN_EDGES)


@pytest.mark.parametrize("edge", sc.FORBIDDEN_EDGES)
def test_every_forbidden_edge_is_refused(edge):
    src, dst = edge
    reg = Reg().chain(PREFIX[src])
    reg.add(dst, commit40=(C2 if dst == "P2" else None))
    refuse(reg.text(), sr.FORBIDDEN_EDGE_CODES[edge])


def test_generic_illegal_transition_still_refuses():
    reg = Reg().chain(("P1",))
    reg.add("P3")
    refuse(reg.text(), "illegal_transition")


def test_chain_must_start_at_a_proposal_row():
    reg = Reg()
    reg.add("P2")
    refuse(reg.text(), "chain_does_not_start_at_proposal")


def test_event_after_the_p5_terminal_refused():
    reg = happy()
    reg.add("P4")
    refuse(reg.text(), "event_after_terminal")


# ===========================================================================
# 14 — any chain defect refuses the WHOLE resolution
# ===========================================================================

def test_a_defect_in_one_chain_poisons_every_chain():
    reg = Reg().chain(("P1", "P2", "P3", "P4", "P5"))          # SID: clean
    reg.add("P1", SID2)
    reg.add("P1", SID2)                                        # SID2: broken
    chains, refusal = sr.resolve_supplement_chains(reg.text())
    assert refusal is not None
    assert chains == {}
    good = sr.resolve_supplement_chain(reg.text(), SID)
    assert good.problem
    assert good.live_authorizations == ()


def test_resolution_result_is_never_partially_successful():
    reg = happy(("P1", "P2"))
    reg.raw(f"| + | {UTC} | **{sc.EVENTS['P3'].token}** | oops |")
    chains, refusal = sr.resolve_supplement_chains(reg.text())
    assert (chains, bool(refusal)) == ({}, True)


# ===========================================================================
# 15 — default fail-closed
# ===========================================================================

def test_unknown_id_is_not_authorized():
    resolution = sr.resolve_supplement_chain(happy().text(), SID3)
    assert resolution.events == ()
    assert resolution.live_authorizations == ()
    assert resolution.retired is False
    assert resolution.problem == ""
    assert "NOT AUTHORIZED" in resolution.detail.upper()


def test_empty_registry_text_is_not_authorized():
    for text in ("", "no table here", None):
        resolution = sr.resolve_supplement_chain(text, SID)
        assert resolution.live_authorizations == ()
        event, detail = sr.find_live_authorization(text or "", SID)
        assert event is None
        assert "NOT AUTHORIZED" in detail.upper()


def test_find_live_authorization_reports_the_row_without_blessing_it():
    text = Reg().chain(("P1", "P2")).text()
    event, detail = sr.find_live_authorization(text, SID)
    assert event is not None
    assert event.authorized_commit == C1
    assert event.output_root == ROOT
    assert event.actor == sc.ACTOR_AARON
    assert "not permission to execute" in detail


def test_find_live_authorization_refuses_a_retired_id():
    event, detail = sr.find_live_authorization(successor_chain().text(), SID)
    assert event is None
    assert "retired" in detail


def test_resolver_seam_never_raises():
    """`supplement_runner._default_resolver` calls this with whatever the
    registry file happens to contain; it must not explode."""
    for text in ("", "|||", "| 1 | 2 | 3 | 4 | 5 | 6 |",
                 "```\n| 1 |\n", happy().text()):
        resolution = sr.resolve_supplement_chain(text, SID)
        assert isinstance(resolution, sr.ChainResolution)


def test_runner_seam_attributes_exist():
    resolution = sr.resolve_supplement_chain(happy(("P1", "P2")).text(), SID)
    assert hasattr(resolution, "problem")
    assert hasattr(resolution, "live_authorizations")
    assert hasattr(resolution, "retired")
    assert resolution.short_ids == ("P1", "P2")
    assert sr.resolve_chain is sr.resolve_supplement_chain


def test_or_raise_entry_point_raises_the_code():
    reg = Reg()
    reg.add("P1", drop=("schema",))
    with pytest.raises(sr.SupplementRegistryError) as excinfo:
        sr.resolve_supplement_chains_or_raise(reg.text())
    assert excinfo.value.code == "missing_required_field"


def test_the_real_registry_authorizes_no_supplement():
    """READ-ONLY. The live registry must resolve to zero supplement chains
    and therefore to NOT AUTHORIZED — the ratified profile says
    `ND1_SUPPLEMENT_EXECUTION_AUTHORIZED=NO`."""
    registry = (Path(__file__).resolve().parents[1] / "ops"
                / "TRIAL_REGISTRY.md")
    assert registry.exists(), f"{registry} is missing"
    text = registry.read_text(encoding="utf-8")
    chains, refusal = sr.resolve_supplement_chains(text)
    assert refusal is None, str(refusal)
    assert chains == {}
    event, detail = sr.find_live_authorization(text, SID)
    assert event is None
    assert "NOT AUTHORIZED" in detail.upper()


# ===========================================================================
# contract fidelity
# ===========================================================================

def test_required_note_keys_are_derived_from_the_contract():
    for short, spec in sc.EVENTS.items():
        derived = set(sr.REQUIRED_NOTE_KEYS[short])
        declared = set(spec.required_fields)
        if short == "P2":
            declared = {"supplement_id", "authorized_commit", "output_root"}
        else:
            declared.discard("supplement_id")
        assert derived == declared, short


def test_allowed_fields_never_shrink_below_required():
    for short in sc.EVENTS:
        assert set(sr.REQUIRED_NOTE_KEYS[short]) <= \
            set(sr.ALLOWED_NOTE_FIELDS[short])


def test_every_ratified_token_can_be_parsed():
    seen = set()
    for short in sc.EVENTS:
        prefix = {"P1": (), "P2": ("P1",), "P2S": ("P1", "P2", "F1"),
                  "P3": ("P1", "P2"), "P4": ("P1", "P2", "P3"),
                  "A1": ("P1", "P2", "P3"), "A2": ("P1", "P2", "P3", "A1"),
                  "AX": ("P1", "P2", "P3", "A1"),
                  "P5": ("P1", "P2", "P3", "P4"), "F1": ("P1", "P2"),
                  "F2": ("P1", "P2", "P3"), "F2v": ("P1", "P2", "P3", "P4"),
                  "F3": ("P1", "P2"), "T1": ()}[short]
        reg = Reg().chain(prefix)
        if short == "T1":
            reg.chain(("P1", "P2", "P3", "F2", "F3"))
            reg.add("T1", SID2)
            events, refusal = sr.parse_supplement_events(reg.text())
        else:
            reg.add(short)
            events, refusal = sr.parse_supplement_events(reg.text())
        assert refusal is None, f"{short}: {refusal}"
        seen.add(events[-1].short_id)
    assert seen == set(sc.EVENTS)


def test_refusal_codes_are_unique_and_lowercase():
    assert all(c == c.lower() for c in sr.REFUSAL_CODES)
    assert len(sr.P2S_REFUSAL_CODES) == 11
    assert len(set(sr.P2S_REFUSAL_CODES)) == 11
