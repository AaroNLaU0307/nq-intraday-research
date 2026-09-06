"""Cross-lane integration for the ratified supplement machinery.

Three jobs, none of which either lane can do for itself:

1. **Pin the code to the GOVERNANCE TEXT.** `supplement_contract.py` is a
   transcription of `ops/DECISION_PACKET_N00_AND_ND1.md` §D.3. A
   transcription that nobody re-derives is a doc-vs-code drift waiting to
   happen (`session-conventions.md` §10 records that class biting more
   than once). These tests re-extract the vocabulary FROM the ratified
   document at test time and assert equality, so renaming a token in code
   goes red against the text Aaron approved.

2. **Pin the code to the RATIFICATION.** The profile is approved by
   digest. If the profile bytes move, every implementation decision below
   is resting on something that is no longer what was signed, so the
   digest is recomputed here too.

3. **Prove the protected state is untouched** by importing and exercising
   the whole supplement surface: registry, exposure ledger and the two
   governed `supplements` subtrees.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest

from itsf.mc import registry_boundary as _rb
from itsf.mc import supplement_contract as sc
from itsf.mc import supplement_registry as sreg
from itsf.mc import supplement_runner as runner

REPO = Path(__file__).resolve().parents[1]
PACKET = REPO / "ops" / "DECISION_PACKET_N00_AND_ND1.md"
RATIFICATION = REPO / "ops" / "ND1_PROFILE_RATIFICATION.md"

APPROVED_PROFILE_ID = "ND1_RECOMMENDED_PROFILE_R1"
APPROVED_PROFILE_SHA256 = (
    "0a08319a408f068ce4c92f93c2c4c39e409937dddfd0ef9f7af43618c70b50a5")
APPROVAL_BINDS_DOC_HEAD = "803d99162d0a018ae5a3b44273601d98d9439d50"


def _packet() -> str:
    return PACKET.read_bytes().decode("utf-8")


def _section(text: str, start: str, end: str) -> str:
    return text[text.index(start):text.index(end)]


#: R3, ratified 2026-08-27. THE RATIFIED GRAMMAR NOW HAS TWO DOCUMENTS.
#: §D.3.2 of the decision packet carries the original 13 events. CR1 could
#: not be added there: the packet's bytes are what R1's and R2's
#: `APPROVAL_BINDS_DOC_HEAD` bind, and editing it would invalidate both
#: approvals — the R2 ratification record says exactly that. So R3 put
#: CR1's grammar in its own canonical block, bound into the profile by
#: `RECOMMENDED_CR1_GRAMMAR_SHA256`.
#:
#: Nothing in the transcription obligations anticipated that these
#: derivation guards read a document which cannot contain CR1. The full
#: suite found it.
PROPOSAL = REPO / "ops" / "PREP_ITEM6_ND1_R3_AMENDMENT_PROPOSAL.md"
CR1_GRAMMAR_SHA256 = (
    "c251335f8d8c4dc89bce4ff7fb445f862d29a04b676bb3a90f6ef5ce5d5e3483")


def _cr1_grammar() -> dict:
    """CR1's ratified grammar, read only after its bytes prove to be the
    approved ones. Deriving from unverified bytes would turn this guard
    into an assertion that the code matches whatever someone last wrote."""
    text = PROPOSAL.read_bytes().decode("utf-8")
    b, e = "BEGIN_ND1_CR1_GRAMMAR_R3\n", "END_ND1_CR1_GRAMMAR_R3"
    block = text[text.index(b) + len(b):text.index(e)]
    got = hashlib.sha256(block.encode("utf-8")).hexdigest()
    assert got == CR1_GRAMMAR_SHA256, (
        "the CR1 grammar bytes changed; Aaron's 2026-08-27 approval of "
        f"{CR1_GRAMMAR_SHA256[:16]}... no longer covers them, so nothing "
        "may be derived from this block")
    return dict(ln.split("=", 1) for ln in block.splitlines() if "=" in ln)


# ===========================================================================
# 1. the ratification itself
# ===========================================================================

def test_the_approved_profile_digest_still_matches_the_document():
    """The profile is approved BY DIGEST. If its bytes move, the approval
    no longer covers what the code implements — that must be loud."""
    text = _packet()
    b, e = ("BEGIN_ND1_RECOMMENDED_PROFILE_R1\n",
            "END_ND1_RECOMMENDED_PROFILE_R1\n")
    canonical = text[text.index(b) + len(b):text.index(e)]
    got = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    assert got == APPROVED_PROFILE_SHA256, (
        "the ratified profile bytes changed; the approval at doc head "
        f"{APPROVAL_BINDS_DOC_HEAD} no longer covers this document")


def test_the_ratification_record_is_present_and_carries_aarons_three_lines():
    text = RATIFICATION.read_bytes().decode("utf-8")
    for line in (f"APPROVED_PROFILE_ID={APPROVED_PROFILE_ID}",
                 f"APPROVED_PROFILE_SHA256={APPROVED_PROFILE_SHA256}",
                 f"APPROVAL_BINDS_DOC_HEAD={APPROVAL_BINDS_DOC_HEAD}"):
        assert line in text, f"ratification record lost {line}"
    assert "ND1_PROFILE_RATIFICATION=VALID" in text


def test_the_ratification_still_authorizes_no_execution():
    """Ratifying grammar is not authorizing a run. If any of these ever
    reads YES, an implementation round has quietly widened its own
    mandate."""
    text = RATIFICATION.read_bytes().decode("utf-8")
    for boundary in ("SUPPLEMENT_EXECUTION_AUTHORIZED=NO",
                     "REAL_DATA_READ_AUTHORIZED=NO",
                     "DIRECTORY_CREATION_AUTHORIZED=NO",
                     "WRITE_PROBE_AUTHORIZED=NO",
                     "REGISTRY_EVENT_APPEND_AUTHORIZED=NO",
                     "EXPOSURE_EVENT_APPEND_AUTHORIZED=NO",
                     "MC_EXECUTION_AUTHORIZED=NO",
                     "STRATEGY_BUILD_AUTHORIZED=NO"):
        assert boundary in text


def test_the_profile_ratified_the_options_the_code_implements():
    """The implementation branches on four ratified choices. Read them
    back out of the approved profile rather than trusting a comment."""
    text = _packet()
    b, e = ("BEGIN_ND1_RECOMMENDED_PROFILE_R1\n",
            "END_ND1_RECOMMENDED_PROFILE_R1\n")
    prof = dict(
        ln.split("=", 1) for ln in
        text[text.index(b) + len(b):text.index(e)].splitlines() if "=" in ln)
    assert prof["RECOMMENDED_ND1_ARCHIVE_FAILURE_POLICY"] == "A"
    assert prof["RECOMMENDED_ND1_PRESTART_COMMIT_CHANGE_REAUTH"] == "YES"
    assert prof["RECOMMENDED_ND1_POSTSTART_FAILURE_NEW_ID"] == "YES"
    assert prof["RECOMMENDED_ND1_PARTIAL_RECOVERY_RULE"] == "MODIFY"
    assert prof["RECOMMENDED_ND1_SUPPLEMENT_SEQUENCE_NAMESPACE"] == "GLOBAL"


# ===========================================================================
# 2. code re-derived from the governance text
# ===========================================================================

def test_every_event_token_is_re_derived_from_the_ratified_document():
    """The decisive doc-vs-code check: extract `TOKEN=` from §D.3.2 and
    compare with what the contract module declares. A token renamed in
    code changes the MEANING of a sealed registry row, so it must not be
    possible to do it quietly."""
    sec = _section(_packet(), "### D.3.2 逐事件语法", "### D.3.3")
    from_packet = set(re.findall(r"^TOKEN=([A-Z_]+)", sec, re.M))
    assert len(from_packet) == 13, (
        "§D.3.2 no longer carries exactly 13 tokens; the packet is bound by "
        "R1's and R2's approvals and must not have been edited")
    from_r3 = {_cr1_grammar()["CR1_TOKEN"]}
    assert from_r3 == {"SUPPLEMENT_RUN_CRASH_RESOLVED"}
    assert from_packet.isdisjoint(from_r3), (
        "both ratified sources declare the same token; one was edited")
    assert from_packet | from_r3 == set(sc.EVENT_TOKENS)


def test_every_short_id_in_the_contract_appears_in_the_document():
    sec = _section(_packet(), "### D.3.2 逐事件语法", "### D.3.3")
    cr1 = _cr1_grammar()
    for short_id in sc.EVENTS:
        if short_id == cr1["CR1_SHORT_ID"]:
            continue     # ratified in the R3 grammar block, verified above
        assert f"**{short_id} `" in sec or f"**{short_id} " in sec, \
            f"{short_id} is declared in code but not in §D.3.2"


def test_the_stage_enum_is_the_documents_closed_set():
    sec = _section(_packet(), "### D.3.2 逐事件语法", "### D.3.3")
    raw = re.search(r"STAGE_ENUM=CLOSED:\s*\{([^}]*)\}", sec).group(1)
    assert tuple(s.strip() for s in raw.split(",")) == sc.STAGE_ENUM


def test_the_verification_failure_codes_are_the_documents_closed_set():
    sec = _section(_packet(), "### D.3.2 逐事件语法", "### D.3.3")
    raw = re.search(r"FAILURE_CODE_ENUM=CLOSED:\s*\{([^}]*)\}",
                    sec, re.S).group(1)
    from_doc = tuple(s.strip() for s in raw.replace("\n", " ").split(","))
    assert from_doc == sc.VERIFICATION_FAILURE_CODES


def test_the_two_terminals_and_the_three_traps_match_the_documents():
    """Two terminals from §D.3.3; the traps now come from BOTH sources.

    A1 and AX are the packet's; CR1 is R3's, and its non-terminality is
    stated by `CR1_TERMINAL=NO` in the approved grammar block rather than
    by anything in the packet."""
    sec = _section(_packet(), "### D.3.3", "### D.3.4")
    assert "AX_TERMINAL" not in sc.TERMINAL_SHORT_IDS
    assert sc.TERMINAL_SHORT_IDS == ("P5", "F3")
    assert sc.NON_TERMINAL_TRAPS == ("A1", "AX", "CR1")
    # the document must still say AX is NOT a terminal
    assert "`AX` | 只记录 Aaron 的" in sec or "AX_TERMINAL=NO" in _packet()
    cr1 = _cr1_grammar()
    assert cr1["CR1_TERMINAL"] == "NO", (
        "the approved grammar makes CR1 terminal; it may not be a trap")
    assert cr1["CR1_SHORT_ID"] not in sc.TERMINAL_SHORT_IDS


def test_the_cr1_spec_matches_its_approved_grammar_field_for_field():
    """The transcription itself, checked against the bytes it came from —
    every field, not a sample. Written after the P3-successor half of this
    transcription was left out and only the reachability guard caught it."""
    cr1, spec = _cr1_grammar(), sc.EVENTS["CR1"]
    assert spec.short_id == cr1["CR1_SHORT_ID"]
    assert spec.token == cr1["CR1_TOKEN"]
    assert spec.row_class == cr1["CR1_ROW_CLASS"]
    assert spec.actor == cr1["CR1_ACTOR"]
    assert spec.terminal is (cr1["CR1_TERMINAL"] == "YES")
    assert spec.incident_required is (cr1["CR1_INCIDENT_REQUIRED"] == "YES")
    assert spec.predecessors == tuple(
        cr1["CR1_PERMITTED_PREDECESSOR"].split("|"))
    assert spec.successors == tuple(
        cr1["CR1_PERMITTED_SUCCESSOR"].split("|"))
    assert spec.required_fields == tuple(
        cr1["CR1_REQUIRED_FIELDS"].split("|"))
    # and the other half of every edge, which is where I went wrong
    for pred in spec.predecessors:
        assert "CR1" in sc.EVENTS[pred].successors
    for succ in spec.successors:
        assert "CR1" in sc.EVENTS[succ].predecessors


def test_p5_has_exactly_the_two_ratified_predecessors():
    assert "P5_PERMITTED_PREDECESSOR=P4 | A2" in _packet()
    assert sc.EVENTS["P5"].predecessors == ("P4", "A2")


def test_ax_has_f3_as_its_only_successor_in_both_code_and_document():
    assert sc.EVENTS["AX"].successors == ("F3",)
    assert "AX_PERMITTED_SUCCESSOR=F3" in _packet()
    assert sc.EVENTS["AX"].terminal is False


def test_p6_and_the_mc_family_are_deferred_not_implemented():
    """§D.3.4 defers them to N-D3. They must be nameable so the parser can
    refuse them by name, and absent from the implemented vocabulary."""
    assert "SUPPLEMENT_CONSUMED_BY_GRID_REPLAY" in sc.ND3_DEFERRED_TOKENS
    assert "SUPPLEMENT_CONSUMED_BY_GRID_REPLAY" not in sc.EVENT_TOKENS
    for token in sc.ND3_DEFERRED_TOKENS:
        assert token not in sc.EVENT_TOKENS
        assert not any(s.token == token for s in sc.EVENTS.values())
    assert "ND3_DEFERRED=[SUPPLEMENT_CONSUMED_BY_GRID_REPLAY（原 P6）" \
        in _packet()


def test_the_id_pattern_and_first_id_are_the_ratified_ones():
    # Anchored with \\Z, not $: Python's $ also matches before a
    # trailing newline, so "MC-DS-S001\\n" satisfied the grammar and the
    # newline travelled into a planned directory name. The RATIFIED text
    # states the id grammar, not the anchor dialect.
    assert sc.SUPPLEMENT_ID_PATTERN.pattern == r"^MC-DS-S[0-9]{3}\Z"
    assert not sc.SUPPLEMENT_ID_PATTERN.match("MC-DS-S001" + chr(10))
    assert sc.FIRST_SUPPLEMENT_ID == "MC-DS-S001"
    assert "SUPPLEMENT_ID_PATTERN=^MC-DS-S[0-9]{3}$" in _packet()


def test_commit_widths_follow_the_ratified_row_classes():
    assert sc.COMMIT_WIDTH[sc.NUMBERED] == 40
    assert sc.COMMIT_WIDTH[sc.UNNUMBERED] == 7
    for spec in sc.EVENTS.values():
        assert spec.commit_width in (7, 40)
        assert (spec.commit_width == 40) == (spec.row_class == sc.NUMBERED)


def test_the_partial_rule_matches_the_ratified_modify_text():
    assert sc.SILENT_DELETE_FORBIDDEN is True
    assert sc.DIVERGENT_PARTIAL_TEMPLATE == ".partial.divergent.{incident_id}"
    assert ("RECOMMENDED_ND1_PARTIAL_MODIFY_TEXT=BRANCH_E_RENAME_TO_"
            ".partial.divergent.<incident_id>;"
            "BRANCH_C_RENAME_THEN_ALLOW_RETRY") in _packet()


# ===========================================================================
# 3. graph coherence — every declared edge is symmetric and closed
# ===========================================================================

def test_predecessor_and_successor_declarations_agree_with_each_other():
    """An asymmetric declaration is how an unreachable branch gets in —
    exactly the defect rounds 2 and 3 removed at the document level."""
    for short_id, spec in sc.EVENTS.items():
        for nxt in spec.successors:
            assert short_id in sc.EVENTS[nxt].predecessors, \
                f"{short_id} lists {nxt} as a successor, but {nxt} does " \
                f"not list {short_id} as a predecessor"
        for prev in spec.predecessors:
            assert short_id in sc.EVENTS[prev].successors, \
                f"{short_id} lists {prev} as a predecessor, but {prev} " \
                f"does not list {short_id} as a successor"


def test_every_non_terminal_event_can_reach_a_terminal():
    """No dead ends. If an event cannot reach P5 or F3, a chain that
    passes through it can never be closed."""
    reach = {}

    def can_close(node, seen=()):
        if node in reach:
            return reach[node]
        if node in seen:
            return False
        spec = sc.EVENTS[node]
        if node in sc.TERMINAL_SHORT_IDS:
            reach[node] = True
            return True
        ok = any(can_close(n, seen + (node,)) for n in spec.successors
                 if not sc.is_forbidden_edge(node, n))
        reach[node] = ok
        return ok

    unreachable = [n for n in sc.EVENTS if not can_close(n)]
    assert unreachable == [], f"cannot reach a terminal from {unreachable}"


def test_every_event_is_reachable_from_a_chain_start():
    """The mirror check. A1 is the one this would have caught: §D.3.2's
    P3 line omits it, and taking that literally would strand it."""
    starts = [n for n, s in sc.EVENTS.items() if not s.predecessors]
    assert starts == ["P1"], starts
    seen, frontier = {"P1"}, ["P1"]
    while frontier:
        node = frontier.pop()
        for nxt in sc.EVENTS[node].successors:
            if sc.is_forbidden_edge(node, nxt) or nxt in seen:
                continue
            seen.add(nxt)
            frontier.append(nxt)
    assert seen == set(sc.EVENTS), f"unreachable: {sorted(set(sc.EVENTS) - seen)}"


def test_forbidden_edges_name_pairs_that_are_otherwise_plausible():
    """A forbidden edge that nothing would ever propose is decoration. Each
    one must connect two real events."""
    for frm, to in sc.FORBIDDEN_EDGES:
        assert frm in sc.EVENTS and to in sc.EVENTS, (frm, to)
        assert not sc.transition_allowed(frm, to)


# ===========================================================================
# 4. protected state is untouched by the whole surface
# ===========================================================================

PROTECTED = (
    # The OLD path stays: after migration Route A it holds a
    # tombstone, and a tombstone is still a file nothing may write.
    REPO / "ops" / "TRIAL_REGISTRY.md",
    # ADDED 2026-08-31: the registry moved, so this is where an
    # unauthorised write would now actually do damage.
    _rb.REGISTRY_REPO_ROOT / _rb.REGISTRY_PATH,
    REPO / "EXPOSURE_LEDGER.md",
    REPO / "ops" / "S0_T001_POST_RUN_ATTESTATION.md",
)
GOVERNED_SUBTREES = (
    Path(r"C:\Users\Aaron\quant-data\itsf-runs") / "supplements",
    Path(r"C:\Users\Aaron\quant-data\itsf-runs-archive") / "supplements",
)


def test_exercising_the_supplement_surface_writes_nothing_protected():
    from _governed_subtrees import (assert_governed_subtrees_untouched,
                                    snapshot)
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in PROTECTED}
    subtrees_before = snapshot()
    # touch everything a caller could reach without an authorization
    with pytest.raises(Exception):
        runner.run_supplement_production()
    for stage in sc.STAGE_ENUM:
        for gate in sc.GATE_TABLE[stage]:
            assert callable(runner.GATES[gate])
    after = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in PROTECTED}
    assert before == after
    # They exist by the 2026-08-29 grant, so "did not create" is no longer
    # the check -- "did not touch" is, and it is the stronger one.
    assert_governed_subtrees_untouched(subtrees_before,
                                       "the supplement surface")


#: Every SUPPLEMENT_ row that exists BY AUTHORIZATION, with the record that
#: authorised it. A row not listed here has appeared without an
#: authorization round, which is what this guard is for.
#:
#: REGISTERED, NOT REMOVED, 2026-08-31. The test used to assert the registry
#: carried NO supplement row at all -- an empty registry standing in for
#: "nothing appeared unauthorised". Aaron authorised P1 that day, so the
#: proxy stopped being true while the property it stood for still held. A
#: proxy that fails when the property is intact is only half the danger; the
#: other half is a proxy that holds after the property is gone, which is how
#: three tests read a tombstone and passed earlier the same day.
AUTHORISED_SUPPLEMENT_ROWS = {
    ("SUPPLEMENT_PROPOSED", "MC-DS-S001"):
        "Aaron, 2026-08-31, 「追加 P1」; recorded in "
        "ops/P1_APPENDED_MC_DS_S001_2026-08-31.md; registry commit e53234e",
    ("SUPPLEMENT_EXECUTION_AUTHORIZED", "MC-DS-S001"):
        "Aaron, 2026-09-05, verbatim signing block; recorded in "
        "ops/P2_APPENDED_MC_DS_S001_2026-09-05.md; registry commit a875740; "
        "witness WITNESS_P2_APPENDED_2026-09-05.json. RE-AUTHORIZED the same "
        "day at seq 17 after the commit went stale; recorded in "
        "ops/P2S_AND_REAUTH_MC_DS_S001_2026-09-05.md; registry commit "
        "ffb15ae; witness WITNESS_P2_REAUTHORIZED_2026-09-05.json",
    ("SUPPLEMENT_EXECUTION_AUTHORIZATION_SUPERSEDED", "MC-DS-S001"):
        "Aaron, 2026-09-05, pre-start supersede of the seq-15 authorization "
        "under the same-day P2 -> P2S amendment; recorded in "
        "ops/P2S_AND_REAUTH_MC_DS_S001_2026-09-05.md; registry commit "
        "ba8c244; witness WITNESS_P2S_APPENDED_2026-09-05.json. Twice more "
        "the same day at seq 18 and seq 20 (registry 6258f07, a99840b) as "
        "each repair moved HEAD; witnesses WITNESS_P2S_2/3_APPENDED",
    # --- the first real N09 run, and how it ended ------------------------
    # Added 2026-09-06, AFTER each event actually happened. Nothing here is
    # pre-registered: an entry exists only because the row is already in the
    # ledger with a witness behind it.
    ("SUPPLEMENT_RUN_STARTED", "MC-DS-S001"):
        "the runner, 2026-09-05, through the P3-only append seam during the "
        "first real N09 execution; registry commit a4f0386; witness "
        "WITNESS_P3_APPENDED_2026-09-05.json. The first row this project's "
        "code ever wrote",
    ("SUPPLEMENT_SEALED", "MC-DS-S001"):
        "the runner, 2026-09-05; verdict P4, archive_ok, 2842 rows. Signed "
        "off by Aaron field by field after every digest was recomputed from "
        "the sealed artifact; registry commit 7e92be6; witness "
        "WITNESS_P4_APPENDED_2026-09-05.json",
    ("SUPPLEMENT_VERIFICATION_FAILED", "MC-DS-S001"):
        "a fresh independent verifier seat, 2026-09-05: "
        "headline_replay_mismatch, 8 of 2842 days carrying a stratum label "
        "different from the one S0-T001 stratified on; attestation "
        "ops/P5_VERIFIER_ATTESTATION_MC_DS_S001_2026-09-06.md; registry "
        "commit 78a2586",
    ("SUPPLEMENT_SUPERSEDED", "MC-DS-S001"):
        "Aaron, ops/OWNER_DECISIONS_2026-09-06.md OD-1, retiring the id "
        "after the failed verification; registry commit c2a8ac9",
    ("SUPPLEMENT_PROPOSED", "MC-DS-S002"):
        "Aaron, 2026-09-05, T1 successor registration for the retired "
        "MC-DS-S001; registry commit 3fec004; witness "
        "WITNESS_T1_APPENDED_2026-09-05.json. NOT an authorization",
    # --- the N09 v2 run, and how it ended --------------------------------
    # Added 2026-09-06 under Aaron's explicit approval, AFTER each of these
    # three rows was already in the ledger with a registry commit and a
    # witness behind it. TIME MATTERS IN THIS PROSE: OD-2 was written after
    # the F2 landed, so nothing here may read as if OD-2 authorised the P2,
    # the P3 or the F2 in advance -- it documents them. The fourth row this
    # run will produce, ("SUPPLEMENT_SUPERSEDED", "MC-DS-S002"), is
    # deliberately ABSENT: that F3 has not happened yet, and pre-registering
    # it is the one thing this table must never do.
    ("SUPPLEMENT_EXECUTION_AUTHORIZED", "MC-DS-S002"):
        "Aaron, 2026-09-06, seq 25, signed field by field after a "
        "memory-only re-verification at the actual signing UTC; the N09 v2 "
        "authorization at framework HEAD f49a6770, the first tree on which "
        "the production supplement-id repair existed; registry commit "
        "ee25019; witness WITNESS_P2_S002_APPENDED_2026-09-06.json. "
        "Subsequently documented in ops/OWNER_DECISIONS_2026-09-06.md OD-2, "
        "which was written after this row and after the F2 below",
    ("SUPPLEMENT_RUN_STARTED", "MC-DS-S002"):
        "the runner, 2026-09-06, through the P3-only append seam during the "
        "N09 v2 execution: appended after B_DERIVE and before the first side "
        "effect, which SPENT the seq 25 authorization. The attempt then "
        "refused at C_BUILD_1, so this row records a start that never "
        "reached a seal; registry commit 9c9d8ae; witness "
        "WITNESS_P3_S002_APPENDED_2026-09-06.json",
    ("SUPPLEMENT_FAILED", "MC-DS-S002"):
        "the runner's own post-start, pre-seal failure -- C_BUILD_1 / "
        "c_build_1_not_empty, no supplement byte written and no archive "
        "attempt -- appended by hand because the run had already exited; "
        "residue preserved at MC-DS-S002_20260905T205325Z, verified present "
        "and empty at the moment of the append; registry commit ec1b9c3; "
        "witness WITNESS_F2_S002_APPENDED_2026-09-06.json. Subsequently "
        "documented in ops/OWNER_DECISIONS_2026-09-06.md OD-2",
    # Added only AFTER the F3 was appended, witnessed and committed -- the
    # entry that was deliberately withheld from the three above while the
    # row did not yet exist.
    ("SUPPLEMENT_SUPERSEDED", "MC-DS-S002"):
        "Aaron, ops/OWNER_DECISIONS_2026-09-06.md OD-2, seq 26, retiring the "
        "id after the post-start C_BUILD_1 failure and naming MC-DS-S003 as "
        "successor; registry commit cc520c5; witness "
        "WITNESS_F3_S002_APPENDED_2026-09-06.json. Its `superseded_commit` "
        "points at seq 25 rather than at the F2, because F2 and P3 are "
        "UNNUMBERED and the F3 reference field can only name numbered rows",
    # Added only AFTER the T1 was appended, witnessed and committed. NOTHING
    # for MC-DS-S003 beyond this row is registered here: its P2, P3, P4, P5,
    # F2 and F3 have not happened, and this table is not where a future
    # event gets permission in advance.
    ("SUPPLEMENT_PROPOSED", "MC-DS-S003"):
        "main agent, 2026-09-06, seq 27, T1 successor registration for the "
        "retired MC-DS-S002, appended from framework HEAD c44d36e2 -- the "
        "tree carrying the C_BUILD_1 archive-scope repair and the pre-P3 "
        "residue check, which are the two defects that cost MC-DS-S002 its "
        "authorization; registry commit ed6259b; witness "
        "WITNESS_T1_S003_APPENDED_2026-09-06.json. NOT an authorization: "
        "MC-DS-S003 has zero live P2 and started=False",
    # --- the N09 v3 run, and how it ended --------------------------------
    # Added 2026-09-06 under Aaron's explicit approval, AFTER each of these
    # four rows was in the ledger with a registry commit and a witness. The
    # fifth row this lineage will produce, ("SUPPLEMENT_SUPERSEDED",
    # "MC-DS-S003"), is ABSENT: that F3 has not happened yet. Nothing for
    # MC-DS-S004 appears here either.
    ("SUPPLEMENT_EXECUTION_AUTHORIZED", "MC-DS-S003"):
        "Aaron, 2026-09-06, seq 28, the N09 v3 authorization, signed at "
        "framework HEAD c0420ffc -- the first tree carrying the C_BUILD_1 "
        "archive-scope repair and the pre-P3 residue check, without which a "
        "run under any fresh id would have failed the way MC-DS-S002's did; "
        "registry commit 7101f02; witness "
        "WITNESS_P2_S003_APPENDED_2026-09-06.json. No framework commit "
        "accompanied it, so `authorized_commit_matches_head` held for the "
        "life of the authorization",
    ("SUPPLEMENT_RUN_STARTED", "MC-DS-S003"):
        "the runner, 2026-09-06, through the P3-only append seam during the "
        "N09 v3 execution: after B_DERIVE and the pre-P3 residue check, "
        "before the first side effect, spending the seq 28 authorization; "
        "registry commit e4cba11; witness "
        "WITNESS_P3_S003_APPENDED_2026-09-06.json",
    ("SUPPLEMENT_SEALED", "MC-DS-S003"):
        "the runner, 2026-09-06; verdict P4, archive_ok, 2842 rows, local "
        "seal 3d966a46. Signed off by Aaron field by field after every "
        "digest was RECOMPUTED from the sealed bytes and the archive copy "
        "re-read as byte-identical; registry commit 336be7e; witness "
        "WITNESS_P4_S003_APPENDED_2026-09-06.json. A seal is a fact about "
        "the run, not about correctness -- see the F2v below",
    ("SUPPLEMENT_VERIFICATION_FAILED", "MC-DS-S003"):
        "a fresh STRICT-BLIND independent verifier seat, 2026-09-06, seq 29: "
        "headline_replay_mismatch, with the blind artifact frozen and hashed "
        "before P4 was opened. Evidence under "
        "quant-data/review/itsf-mc-ds-s003-strict-blind-verifier-2026-09-06 "
        "-- blind artifact MC-DS-S003_STRICT_BLIND_PHASE3_FROZEN.json "
        "sha256 372cc6ce6b622cc5cb620a07573a6e6632c823f64d7298cf0100aed53e9fc30e "
        "and attestation "
        "MC-DS-S003_STRICT_BLIND_P5_VERIFIER_ATTESTATION.md sha256 "
        "1df1e04996169dedc7873645bab13708c4c71ba4e8087da6db958eada896695d, "
        "both re-hashed and matched before the row was appended; registry "
        "commit cae0d9c; witness "
        "WITNESS_F2V_S003_APPENDED_2026-09-06.json. Grounded in "
        "headline_replay_identity alone: the report's re-derivation claim "
        "was left out because the contract keeps that a separate condition "
        "and no code defines its operation",
    # Added only AFTER the F3 was appended, witnessed and committed -- the
    # entry deliberately withheld from the four above while the row did not
    # exist. Nothing for MC-DS-S004 is registered: it has no rows at all.
    ("SUPPLEMENT_SUPERSEDED", "MC-DS-S003"):
        "Aaron, ops/OWNER_DECISIONS_2026-09-06.md OD-3, seq 30, retiring the "
        "id after the strict-blind verification failed and naming "
        "MC-DS-S004 as successor; registry commit 2421460; witness "
        "WITNESS_F3_S003_APPENDED_2026-09-06.json. Unlike MC-DS-S002's F3 "
        "this one supersedes the FAILURE EVENT itself -- the F2v is numbered "
        "at seq 29 -- so there is no reference ambiguity to record",
}


def test_no_supplement_event_appeared_without_authorization():
    """The whole point of default-refuse. A SUPPLEMENT_ row that is not in
    AUTHORISED_SUPPLEMENT_ROWS appeared without an authorization round, and
    adding a name there is a deliberate act with a record behind it -- not a
    way to make this quiet."""
    text = (_rb.REGISTRY_REPO_ROOT / _rb.REGISTRY_PATH).read_bytes().decode("utf-8")
    rows = [ln for ln in text.splitlines()
            if ln.strip().startswith("|") and "SUPPLEMENT_" in ln]
    unregistered = []
    for line in rows:
        token = next((t for t in line.split("|") if "SUPPLEMENT_" in t), "")
        sid = next((p.strip("[]") for p in line.split()
                    if p.startswith("[MC-DS-S")), "")
        if (token.strip(" *"), sid) not in AUTHORISED_SUPPLEMENT_ROWS:
            unregistered.append(line)
    assert unregistered == [], (
        "a SUPPLEMENT_ row is present that no authorization record covers:\n"
        + "\n".join(unregistered))


def test_every_authorised_row_is_actually_there():
    """The other direction. A registration that outlives its row would let
    the check above pass over something that no longer exists, and would
    quietly widen what counts as authorised."""
    text = (_rb.REGISTRY_REPO_ROOT / _rb.REGISTRY_PATH).read_bytes().decode("utf-8")
    for (token, sid), why in sorted(AUTHORISED_SUPPLEMENT_ROWS.items()):
        assert any(token in ln and sid in ln for ln in text.splitlines()), (
            "%s for %s is registered as authorised (%s) but no such row is "
            "in the registry" % (token, sid, why))


# ===========================================================================
# 5. blind guarantee — the supplement surface cannot reach an outcome
# ===========================================================================

import ast  # noqa: E402

SUPPLEMENT_MODULES = ("supplement_contract.py", "supplement_runner.py",
                      "supplement_authority.py", "supplement_registry.py")

#: Modules that produce or carry research OUTCOME values. A supplement is
#: a STRUCTURAL artifact (§D.7: "它不读取 target outcome"), so nothing on
#: this surface may import one — an import is the only way the value could
#: arrive, and an AST check is cheaper and louder than a code review.
OUTCOME_BEARING = ("itsf.s0.study", "itsf.mc.orchestrator", "itsf.mc.verdict",
                   "itsf.mc.account", "itsf.s0.report", "itsf.s0.stats")


def _module_paths():
    src = REPO / "src" / "itsf" / "mc"
    return [src / n for n in SUPPLEMENT_MODULES if (src / n).exists()]


def test_no_supplement_module_imports_an_outcome_bearing_module():
    offenders = []
    for path in _module_paths():
        tree = ast.parse(path.read_bytes().decode("utf-8"))
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                if any(name == bad or name.startswith(bad + ".")
                       for bad in OUTCOME_BEARING):
                    offenders.append(f"{path.name}: {name}")
    assert offenders == [], offenders


def test_the_supplement_modules_are_actually_present_so_this_is_not_vacuous():
    """A sweep over an empty list passes trivially. Pin the count."""
    found = {p.name for p in _module_paths()}
    assert "supplement_contract.py" in found
    assert "supplement_runner.py" in found


def test_no_supplement_module_names_an_outcome_field():
    """The four structural row keys are the whole vocabulary. A P&L /
    return / oracle / EV identifier appearing anywhere on this surface is
    the blind guarantee leaking."""
    banned = ("final_pnl", "pnl_per_contract", "y_cont", "oracle_usd",
              "prop_operating_ev", "strategy_account_ev", "sharpe",
              "payout_cash", "terminal_cash")
    offenders = []
    for path in _module_paths():
        text = path.read_bytes().decode("utf-8").lower()
        for token in banned:
            if token in text:
                offenders.append(f"{path.name}: {token}")
    assert offenders == [], offenders


# ===========================================================================
# 6. the residual N03 does NOT close — pinned so it cannot widen unnoticed
# ===========================================================================

def test_a_hand_made_supplement_cannot_reach_the_production_seal():
    """REVERSED at the N06 repair. This test used to assert the bypass
    EXISTED — that `build_day_strata_supplement` would accept a
    hand-assembled `(expected_day_set, binding)` and produce a sealable
    supplement. Measured at 617f7c3: "BUILT AND SEALED from a hand-made
    pair". The hermetic core is now named `_test_only` and its payload
    carries no production receipt, so the production seal refuses it.
    """
    from itsf.mc import day_strata_supplement as ds
    from itsf.mc import supplement_production as sp

    payload = ds.build_day_strata_supplement_test_only(
        [], expected_day_set=frozenset(),
        binding={"trial_id": "S0-T001", "authorized_commit": "a" * 40,
                 "day_universe_digest": "b" * 64, "method_version": "v1",
                 "source_input_sha256": "c" * 64})
    # a raw mapping is refused on type
    with pytest.raises(sp.SupplementProductionError) as ei:
        sp.verify_production_receipt(payload, None, None)
    assert ei.value.code == "production_product_type"
    # and so is a hand-wrapped product, because the receipt is init=False
    product = sp.SupplementProduct(payload=payload)
    assert product.receipt is None
    with pytest.raises(sp.SupplementProductionError) as ei:
        sp.verify_production_receipt(product, None, None)
    assert ei.value.code == "production_not_factory_built"


def test_the_production_builder_refuses_the_decisive_arguments():
    """The caller supplies ROWS and nothing else: passing
    `expected_day_set` or `binding` is a refusal, not a silently ignored
    keyword."""
    from itsf.mc import supplement_production as sp
    for name in ("expected_day_set", "binding"):
        with pytest.raises(sp.SupplementProductionError) as ei:
            sp.build_supplement_from_authority(None, None, [], **{name: object()})
        assert ei.value.code == "production_decisive_argument_supplied"


def test_the_hermetic_core_is_named_test_only_at_every_call_site():
    """A helper whose status is only in a docstring gets called by
    accident. The name carries it."""
    from itsf.mc import day_strata_supplement as ds
    assert hasattr(ds, "build_day_strata_supplement_test_only")
    assert hasattr(ds, "seal_supplement_test_only")
    assert not hasattr(ds, "build_day_strata_supplement")
    assert not hasattr(ds, "seal_supplement")


def test_no_production_code_calls_the_hermetic_core_outside_the_factory():
    """Only `supplement_production` may call the TEST_ONLY core. A new
    caller anywhere else turns this red."""
    import ast
    roots = [REPO / "src", REPO / "scripts"]
    callers = []
    for root in roots:
        for path in root.rglob("*.py"):
            if path.name in ("day_strata_supplement.py",
                             "supplement_authority.py",
                             "supplement_production.py"):
                # the definition, the argument seam, and the production
                # factory that is now the ONLY sanctioned caller
                continue
            tree = ast.parse(path.read_bytes().decode("utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    fn = node.func
                    name = (fn.attr if isinstance(fn, ast.Attribute)
                            else getattr(fn, "id", ""))
                    if name == "build_day_strata_supplement_test_only":
                        callers.append(f"{path.relative_to(REPO)}:{node.lineno}")
    assert callers == [], (
        "a production caller now reaches the builder directly, bypassing "
        f"the N03 authority: {callers}")


# ===========================================================================
# 7. cross-lane wiring — N03 authority, N04 runner, N05 registry
# ===========================================================================

def test_the_runner_discovers_the_registry_resolver_through_its_seam():
    """N04 was written against a NAMED seam rather than N05's eventual
    API, so the two lanes could run concurrently. This is the test that
    the seam actually closed."""
    from itsf.mc import supplement_registry as sr
    text = (_rb.REGISTRY_REPO_ROOT / _rb.REGISTRY_PATH).read_bytes().decode("utf-8")
    chain = runner._default_resolver(text, sc.FIRST_SUPPLEMENT_ID)
    assert type(chain).__name__ == "ChainResolution"
    assert chain is not None
    # the surface N04's gates read must exist on N05's object
    for attr in ("problem", "live_authorizations", "retired"):
        assert hasattr(chain, attr), f"seam is missing {attr}"
    assert sr.resolve_supplement_chain is not None


def test_the_real_registry_resolves_cleanly_and_authorizes_at_most_once():
    """Not "it refused" — it must resolve WITHOUT DEFECT. A parser that
    refused the real registry outright would produce the same "not
    authorized" outcome for the wrong reason.

    REWRITTEN 2026-09-05. This used to also require `live == 0`, which
    stopped being true the moment Aaron signed the P2 at row 15. "Zero
    today" was never the property — it was the state of the ledger on the
    day the test was written. What the ledger must satisfy at every moment
    is what stands here now:

      * it parses without defect;
      * it never carries more than ONE live authorization — two make
        `live_authorization_unique` refuse, which wedges the chain; and
      * a live authorization is Aaron's and names a 40-hex commit.

    The row itself is recorded in
    `ops/P2_APPENDED_MC_DS_S001_2026-09-05.md`.
    """
    text = (_rb.REGISTRY_REPO_ROOT / _rb.REGISTRY_PATH).read_bytes().decode("utf-8")
    chain = runner._default_resolver(text, sc.FIRST_SUPPLEMENT_ID)
    assert chain.problem == "", chain.problem
    live = chain.live_authorizations
    assert len(live) <= 1, (
        "%d live authorizations; more than one is illegal and the runner "
        "refuses on it" % len(live))
    for row in live:
        assert sc.ACTOR_AARON in (getattr(row, "actor", "") or ""), row
        assert sc.HEX40_RE.match(getattr(row, "authorized_commit", "") or ""), \
            row
    # `retired is False` used to be asserted here. MC-DS-S001 was retired on
    # 2026-09-05 after its independent verification failed, so that was a
    # snapshot too. The durable property is the RELATIONSHIP: a retired chain
    # authorizes nothing.
    if chain.retired:
        assert len(live) == 0, (
            "%s is retired and still carries %d live authorization(s)"
            % (sc.FIRST_SUPPLEMENT_ID, len(live)))


def test_the_production_entry_refuses_when_nothing_authorises_it():
    """REWRITTEN 2026-09-05. This drove the refusal off the REAL registry,
    so Aaron signing a P2 turned a property test into a snapshot test — it
    went red for a correct reason in the wrong place, and the property it
    is named for never stopped holding.

    The property is "no live authorization means no run". It is driven
    through the resolver seam `run_supplement_production` documents for
    exactly this, so it holds whatever today's ledger happens to contain.
    The seam swaps the RESOLVER only; the boundary's single read still
    happens.
    """
    def _nothing_authorises(_text, supplement_id):
        return sreg.resolve_supplement_chain("", supplement_id)

    with pytest.raises(runner.SupplementRunNotAuthorized) as ei:
        runner.run_supplement_production(resolver=_nothing_authorises)
    msg = str(ei.value)
    assert "0 live" in msg
    assert sc.EVENTS["P2"].token in msg


def test_the_three_lanes_share_one_vocabulary_and_do_not_fork_it():
    """Each lane defines its own refusal codes, but the EVENT vocabulary
    has exactly one home. A lane that re-spelled a token would be
    describing a different registry row than the other two."""
    from itsf.mc import supplement_authority as sa
    from itsf.mc import supplement_registry as sr
    for module in (sa, sr, runner):
        for name in dir(module):
            if name.startswith("SUPPLEMENT_") and name.endswith("_TOKEN"):
                raise AssertionError(
                    f"{module.__name__} defines its own token {name}")
    assert sr.REFUSAL_CODES, "the registry lane exposes no refusal codes"
    assert sa.IDENTITY_REFUSAL_CODES, "the authority lane exposes none"


def test_the_authority_lane_reuses_the_prepare_batterys_identity_codes():
    """The §D.2.2 identity has ONE meaning. If N03 had invented parallel
    codes, a sealed-input integrity failure would report differently
    depending on which layer noticed it."""
    from itsf.mc import supplement_authority as sa
    battery_src = (REPO / "src" / "itsf" / "mc"
                   / "consumer.py").read_bytes().decode("utf-8")
    for code in sa.IDENTITY_REFUSAL_CODES:
        assert f'"{code}"' in battery_src, (
            f"{code} is presented as a reused battery code but does not "
            "appear in consumer.py")


def test_no_supplement_test_is_muted():
    """`final_candidate_scans.py` refuses a skipped test in `tests/`. Pin
    it here too so a muted supplement test fails the focused run, not just
    the release scan."""
    import re as _re
    # Match CODE, not prose: a docstring that merely NAMES the muting
    # decorators while explaining they are forbidden is not a muted
    # test - another lane's battery tripped exactly that.
    #
    # The name carries `_PAT` on purpose. `final_candidate_scans.py`
    # excludes lines containing `_PAT` or `re.compile` from its own
    # SKIP scan (rule E7, "this scanner's own pattern-definition
    # lines"), and without the marker THIS detector's pattern literal
    # is itself reported as a muted test. Same self-match class.
    _MUTED_PAT = (r"pytest\.skip\(|pytest\.mark\.skip"
                  r"|@\s*pytest\.mark\.xf" + "ail"
                  + r"|\bxf" + r"ail\s*=")
    muted = []
    for path in (REPO / "tests").glob("test_mc_supplement*.py"):
        text = path.read_bytes().decode("utf-8")
        for i, line in enumerate(text.splitlines(), 1):
            # exclude this detector's OWN pattern literal, exactly as
            # `final_candidate_scans.py` excludes its `_PAT` lines (E7).
            if "_re.search" in line or "_MUTED_PAT" in line:
                continue
            if _re.search(_MUTED_PAT, line):
                muted.append(f"{path.name}:{i}")
    assert muted == [], muted


# ===========================================================================
# 9. the anchor class, swept across EVERY module — not just two of them
# ===========================================================================

ANCHOR_MODULES = ("supplement_contract.py", "supplement_runner.py",
                  "supplement_registry.py", "supplement_authority.py",
                  "supplement_production.py", "day_strata_supplement.py")


def test_no_validating_anchor_in_any_supplement_module_uses_dollar():
    r"""The N06 repair swept `$` -> `\Z` in TWO modules and this session
    CLAIMED the class was swept. It was not: `day_strata_supplement.py`
    carried three more of exactly the same defect, and a fresh Sol review
    found them. The earlier guard only reflected over the two modules it
    knew about, so it could not have caught them either.

    CORRECTED 2026-08-29 — AND THE CORRECTION IS THE POINT. The paragraph
    above ended "This sweeps every module by SOURCE, so a new one joins the
    check by existing rather than by being remembered." **It did not.** It
    iterated `ANCHOR_MODULES`, a hand-written tuple of six names, while
    `src/itsf/mc/` holds twenty-one modules.

    So the repair written because a guard "only reflected over the two
    modules it knew about" reflected over six, and said in its own docstring
    that it did otherwise. MEASURED: at HEAD~6, `atoms.py` (2 patterns) and
    `consumer.py` (2) carried the same defect, both outside the tuple, both
    invisible to this test.

    It now globs the directory. `ANCHOR_MODULES` is kept only as a floor —
    every name in it must still be found, so a glob that silently stops
    matching fails here rather than passing over nothing."""
    import re as _re
    src_dir = REPO / "src" / "itsf" / "mc"
    modules = sorted(p for p in src_dir.glob("*.py") if p.name != "__init__.py")
    assert len(modules) > len(ANCHOR_MODULES), (
        f"the glob found {len(modules)} modules, which is not more than the "
        "old hand-written list — the derivation is not deriving")
    found_names = {p.name for p in modules}
    missing = [n for n in ANCHOR_MODULES if n not in found_names]
    assert missing == [], f"named modules the glob no longer sees: {missing}"

    offenders = []
    for path in modules:
        for i, line in enumerate(
                path.read_bytes().decode("utf-8").splitlines(), 1):
            if _re.search(r're\.compile\(rf?"\^[^"]*\$"\)', line):
                offenders.append(f"{path.name}:{i}")
    assert offenders == [], (
        "these anchors accept a trailing newline, because Python's `$` also "
        f"matches before one: {offenders}")


def test_every_validating_pattern_rejects_a_trailing_newline():
    """Behaviour, not source text. Compiled patterns are probed directly,
    so a pattern that dodges the source check still fails here."""
    import re as _re
    from itsf.mc import day_strata_supplement as _ds
    from itsf.mc import supplement_runner as _run
    probes = [
        (sc.SUPPLEMENT_ID_PATTERN, "MC-DS-S001"),
        (sc.HEX40_RE, "a" * 40),
        (sc.HEX7_RE, "a" * 7),
        (sc.HEX64_RE, "c" * 64),
        (sc.INCIDENT_RE, "INC-0123456789ab"),
        (sc.REASON_CODE_RE, "SOME_CODE"),
        (_run.UTC_STAMP_RE, "20260821T000000Z"),
        (_ds._HEX40, "a" * 40),
        (_ds._HEX64, "c" * 64),
        (_ds._ISO_DATE, "2024-01-02"),
    ]
    assert len(probes) == 10
    for pattern, good in probes:
        assert pattern.match(good), (pattern.pattern, good)
        for bad in (good + "\n", good + "\r\n", good + "\n" + "X"):
            assert not pattern.match(bad), (pattern.pattern, repr(bad))
