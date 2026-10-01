"""Mechanical consistency validator for the R1 UNSEALED preregistration, its
structured companion manifest and the project state. Schema/consistency only --
it executes NO research statistic and reads NO market data.

r4 (2026-09-17) adds two things: the P-7 manifest cross-check (group 13), and
the PSMV output-surface repair checks (group 9b), which make a numeric MDE
anywhere in the record a FAILURE rather than an allowlisted planning figure.

SEAL (2026-09-17): group 10 now asserts the SEALED state rather than the
unsealed one, and group 14 verifies the seal attestation -- recomputing the
sha256 of every sealed file, so the seal is checkable rather than declared.
Group 14 is skipped while the attestation does not exist, which is exactly the
state of the CONTENT_COMMIT itself (a commit cannot attest to its own SHA)."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

P = Path(__file__).resolve().parent.parent
PREREG = P / "R1_S1_PREREGISTRATION_SEALED.md"
MANIFEST = P / "R1_PREREG_MANIFEST.json"
SEAL = P / "R1_S1_SEAL_ATTESTATION.json"
STATE = P / "PROJECT_STATE.md"
DECISIONS = P / "R1_DELEGATED_OWNER_DECISIONS.md"
PROVENANCE = P / "R1_S0_PROVENANCE.md"
REGISTRY = P / "R1_TRIAL_REGISTRY.md"
REPORT = P / "artifacts" / "PSMV_STRUCTURAL_REPORT.json"
ATTEST = P / "artifacts" / "PSMV_PURITY_ATTESTATION.json"

failures: list[str] = []
notes: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    (notes if ok else failures).append(f"{'PASS' if ok else 'FAIL'}  {name}"
                                       + (f" -- {detail}" if detail else ""))


def has(text: str, phrase: str) -> bool:
    """Whitespace-tolerant containment: the documents wrap, so a phrase may be
    split across lines with arbitrary indentation."""
    return re.search(r"\s+".join(re.escape(t) for t in phrase.split()),
                     text) is not None


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    for f in (PREREG, STATE, DECISIONS, PROVENANCE, REGISTRY, REPORT, ATTEST,
              MANIFEST):
        check(f"exists:{f.name}", f.exists())
    if failures:
        for line in failures:
            print(line)
        return 1

    doc = PREREG.read_text(encoding="utf-8")
    state = STATE.read_text(encoding="utf-8")
    rep = json.loads(REPORT.read_text(encoding="utf-8"))
    att = json.loads(ATTEST.read_text(encoding="utf-8"))

    # ---- 1. stale OD values -------------------------------------------
    check("no stale 'k = 2' presented as operative",
          "k = 2 is the correct choice" not in doc
          and "OPTION B (k=2)" not in doc,
          "OPTION B is retained only as an audited, non-operative alternative")
    check("OD-4 recorded as k = 1", "OD-4 MATERIALITY     = k = 1" in doc)
    check("operative M is $3.99", "M = 1 x C_base_RT = $3.99" in doc)
    check("no unruled 'k in {1,2}' left in the claim table",
          "`k ∈ {1, 2}` is an **Owner decision" not in doc)

    # ---- 2. stale project-home alternatives ---------------------------
    for stale in ("(b) a subtree inside ITSF",
                  "(c) workspace root only, as this draft is now",
                  "RECOMMENDED]"):
        check(f"no stale project-home option: {stale[:34]!r}", stale not in doc)
    check("OD-5 recorded as OPTION A", "OD-5 PROJECT HOME    = OPTION A" in doc)

    # ---- 3. stale P-2 ambiguity ---------------------------------------
    m = re.search(r"^P-2  Reaction window.*$", doc, re.M)
    check("P-2 row in section P recorded as CLOSED",
          m is not None and "CLOSED" in m.group(0),
          m.group(0)[:70] if m else "absent")
    check("P-2 OPTION A recorded",
          "P-2  REACTION WINDOW = OPTION A (fixed; no alternative arm, no scan)" in doc)

    # ---- 4. stale FOMC ambiguity --------------------------------------
    check("OD-7 defer recorded", "OD-7 FOMC            = CONFIRM_DEFER" in doc)
    for bad in ("FOMC = FALSIFIED", "FOMC falsified", "FOMC rejected"):
        check(f"FOMC never {bad!r}", bad not in doc)

    # ---- 5. stale S2-before-seal wording ------------------------------
    check("no 'S2-1' assigned to the structural preflight",
          "S2-1  Structural preflight" not in doc)
    check("PSMV block present", "PSMV-1  DONE." in doc)
    check("S2 gated behind the seal",
          "=== S2 BUILD (only after the seal) ===" in doc)

    # ---- 6. stale O(08:32) primary references -------------------------
    # An occurrence is LIVE only if no disqualifying phrase appears within a
    # two-line context window. Single-line matching is too crude for a wrapped
    # document: section E.2 explains at length WHY O(08:32) is unusable, and
    # the explanation wraps across lines.
    NEG = (r"not mechanically attainable|DROPPED|moves O\(08:32\)|"
           r"r1 \(O\(08:32\)\)|idealised|arm was dropped|"
           r"why `?O\(08:32\)`?|is by definition|Booking a fill|"
           r"assumes an observe|first transaction")
    L = doc.splitlines()
    live_0832 = []
    for i, ln in enumerate(L):
        if "O(08:32)" not in ln:
            continue
        ctx = chr(10).join(L[max(0, i - 2):i + 3])
        if not re.search(NEG, ctx):
            live_0832.append(ln)
    check("no live O(08:32) primary reference", not live_0832,
          f"{len(live_0832)} suspicious line(s)")
    check("primary entry is O(08:33)",
          "PRIMARY_ENTRY_REFERENCE  = O(08:33)" in doc
          or "PRIMARY_ENTRY = O(08:33)" in doc
          or "entry `O(08:33)`" in doc)
    check("holding period is 56 minutes", "56 minutes" in doc
          and "57 minutes" not in doc and "57-minute" not in doc)

    # ---- 7. n semantics -----------------------------------------------
    n_struct = rep["pre_seal_structural_n"]
    check("PRE_SEAL_STRUCTURAL_N == 252", n_struct == 252, str(n_struct))
    check("prereg carries the measured n",
          f"PRE_SEAL_STRUCTURAL_N      = {n_struct}" in doc)
    check("POST_SEAL_SIGNAL_DEFINED_N is NOT a number in the artifact",
          rep["post_seal_signal_defined_n"] is None)
    check("prereg keeps the two n's distinct",
          "POST_SEAL_SIGNAL_DEFINED_N = to be determined mechanically in S2" in doc)
    check("E4 deferral recorded in the artifact",
          rep["event_funnel"]["E4_r_init_zero_no_direction"]["status"]
          == "DEFERRED_TO_S2")
    check("PSMV_SCOPE_CONFLICT is declared, not hidden",
          "PSMV_SCOPE_CONFLICT = " in doc and "SAFE_RESOLUTION     = " in doc)

    # ---- 8. funnel conservation carried across artifact and prereg ----
    ef = rep["event_funnel"]
    e0 = ef["E0_cpi_or_nfp_calendar_events"]
    e1 = ef["E1_minus_any_fomc_calendar_entry"]["remaining"]
    e2 = ef["E2_minus_exact_roll_transition_sessions"]["remaining"]
    e3 = ef["E3_minus_missing_required_structural_anchors"]["remaining"]
    check("funnel arithmetic E0=277 E1=258 E2=258 E3=252",
          (e0, e1, e2, e3) == (277, 258, 258, 252), f"{(e0, e1, e2, e3)}")
    check("all artifact conservation checks true",
          all(ef["conservation_checks"].values()))
    check("all session-funnel checks true",
          all(rep["session_funnel"]["checks"].values()))
    check("exact roll overlap is 0",
          ef["E2_minus_exact_roll_transition_sessions"]["removed"] == 0)

    # ---- 9. accidental R1 outcome values ------------------------------
    # A MEASURED R1 outcome would carry a decimal value. Definitional text such
    # as `R_init = 0` (the prespecified no-direction rule) is not a measurement
    # and must not be flagged, so the pattern requires a decimal fraction.
    # Section G.5 carries a deliberately HYPOTHETICAL illustration
    # (`mean(Y_net) = $2.10 +- $0.90`), which is not an R1 measurement and is
    # excluded BY NAME so the check stays meaningful instead of being weakened.
    #
    # r4: the four MDE exclusions that used to live here are GONE. The record
    # repair of 2026-09-17 removed every recalculated MDE from the pre-seal
    # record, so an MDE attached to a value is now a FAILURE wherever it
    # appears -- see group 9b.
    HYPOTHETICAL_OK = {"mean(Y_net) = $2.1"}
    for bad in ("mean(Y_net)", "point estimate", "CI_lower", "CI_upper",
                "s_hat", "SE_hat", "MDE_50", "MDE_80", "Y_net"):
        hits = [m.group(0) for m in
                re.finditer(re.escape(bad) + r"\s*(?:=|was|is)\s*\$?-?\d+\.\d",
                            doc)
                if m.group(0) not in HYPOTHETICAL_OK]
        check(f"no measured R1 value attached to {bad!r}", not hits,
              "; ".join(hits[:3]))
    # and the positive assertion: no R1 outcome exists at all
    check("prereg states R1_OUTCOME_INSPECTED = NO",
          "R1_OUTCOME_INSPECTED = NO" in doc)
    check("artifact purity verdict PASS", att["verdict"] == "PASS")
    check("artifact live purity pass", att["live_pass"] is True)
    check("mutation demonstration pass", att["mutation_demonstration_pass"] is True)
    check("every mutation fixture was refused",
          all(d["refused"] for d in att["mutation_demonstration"].values()))

    # ---- 9b. PSMV OUTPUT-SURFACE REPAIR (r4) --------------------------
    # The PSMV authorization permitted structural facts only and prohibited
    # computing or exposing MDE. A numeric detection floor is therefore a
    # record defect anywhere in the pre-seal record -- including in the
    # sections that legitimately DEFINE the prospective form.
    for pat_, label in ((r"MDE_\d+\s*(?:=|is|of|to)\s*\$?\s*\d",
                         "MDE attached to a value"),
                        (r"detection floor is\s*\*{0,2}\s*\$\s*\d",
                         "numeric detection floor"),
                        (r"floor\s+(?:of|to)\s*\$\s*\d",
                         "numeric floor")):
        hits = [m.group(0) for m in re.finditer(pat_, doc)]
        check(f"no {label} in the pre-seal record", not hits,
              "; ".join(hits[:3]))
    for phrase in ("PLANNING_POWER_TABLE = TO_BE_REFRESHED_OUTSIDE_PSMV / "
                   "BEFORE_SEAL IF REQUIRED",
                   "PSMV_MDE_SCOPE_VIOLATION = RECORD_HYGIENE_ONLY",
                   "R1_OUTCOME_CONTAMINATION = NO",
                   "PSMV_RERUN_REQUIRED      = NO"):
        check(f"record-repair line present: {phrase.split('=')[0].strip()}",
              has(doc, phrase))
    check("the prospective power FORM is preserved",
          has(doc, "MDE_80  = M + 2.486 * SE")
          and has(doc, "MDE_80   = M + 2.486 * SE_hat"),
          "I.4 form and the I.3 gate")
    # The artifacts must be BYTE-IDENTICAL to their PSMV-time digests: the
    # repair touched prose only, and a changed artifact would mean PSMV had
    # been re-run or edited.
    recorded_digests = REGISTRY.read_text(encoding="utf-8")
    for art in (REPORT, ATTEST):
        check(f"artifact unmodified since PSMV: {art.name}",
              sha256_of(art) in recorded_digests, sha256_of(art)[:16])

    # ---- 10. accidental IV / Lockbox / S2 authority -------------------
    check("artifact denies IV access",
          rep["authority"]["INTERNAL_VALIDATION"] == "NOT GRANTED / NOT ACCESSED")
    check("artifact denies Lockbox access",
          rep["authority"]["LOCKBOX"] == "NOT GRANTED / NOT ACCESSED")
    check("artifact denies protected ITSF outcomes",
          rep["authority"]["PROTECTED_ITSF_OUTCOMES"] == "NOT GRANTED / NOT ACCESSED")
    # HISTORICAL, not current: the PSMV artifact records the authority state
    # at PSMV time, when S1 was correctly not yet sealed. It is frozen.
    check("PSMV artifact still records S1 unsealed AT PSMV TIME",
          rep["authority"]["S1_SEALED"] is False)
    check("artifact: S2 not authorized", rep["authority"]["S2_AUTHORIZED"] is False)
    check("prereg: PREREG_SEALED = YES", "PREREG_SEALED        = YES" in doc)
    check("prereg: SEALED_BY = Aaron", "SEALED_BY            = Aaron (Owner)" in doc)
    check("prereg: the seal was EXECUTED by Claude Opus, not decided by it",
          has(doc, "SEAL_EXECUTED_BY = Claude Opus (Main Agent), acting under "
                   "explicit Aaron authorization"))
    check("prereg: Fable is NOT recorded as the sealer",
          has(doc, "Fable did not seal this preregistration")
          and not has(doc, "SEALED_BY = Fable"))
    check("prereg: the delegated provenance survives the seal, separately",
          has(doc, "DELEGATED_BY  = Aaron        DECIDED_BY = Fable 5.1      "
                   "ACCEPTED_BY = ChatGPT"))
    check("prereg: S1_SEALED = YES in the trailer",
          has(doc, "S1_SEALED            = YES"))
    check("prereg: S2_STARTED = NO in the trailer",
          has(doc, "S2_STARTED           = NO"))
    check("prereg: S2_AUTHORIZED = NO", "S2_AUTHORIZED        = NO" in doc)
    check("prereg: R1_OUTCOME_INSPECTED = NO",
          "R1_OUTCOME_INSPECTED = NO" in doc)
    check("state: S2 NOT AUTHORIZED", "S2                   = NOT AUTHORIZED" in state)
    check("state: IV not granted", "INTERNAL_VALIDATION  = NOT GRANTED" in state)
    check("state: Lockbox not granted", "LOCKBOX              = NOT GRANTED" in state)
    check("state: outcome reveal not granted",
          "OUTCOME_REVEAL       = NOT GRANTED" in state)
    check("state: S1 SEALED", "S1                   = SEALED" in state)
    check("state: sealed by Aaron",
          "SEALED_BY            = Aaron (Owner)" in state)

    # ---- 11. delegated provenance recorded exactly --------------------
    dec = DECISIONS.read_text(encoding="utf-8")
    for field in ("DECISION_TYPE = DELEGATED_OWNER_RULING",
                  "DELEGATED_BY  = Aaron",
                  "DECIDED_BY    = Fable 5.1",
                  "ACCEPTED_BY   = ChatGPT"):
        check(f"provenance field: {field}", field in dec)
    check("prereg repeats the delegation provenance",
          "DELEGATED_OWNER_RULING" in doc and "DECIDED_BY = Fable 5.1" in doc)

    # ---- 12. trial identity -------------------------------------------
    reg = REGISTRY.read_text(encoding="utf-8")
    for field in ("SAMPLE_FORMAL_TRIAL_ORDINAL         2",
                  "INHERITED_RESEARCHER_EXPOSURE_COUNT 1575",
                  "PRIOR_LINEAGE                       ITSF S0-T001",
                  "R1_OUTCOME_EXPOSURE                 NONE",
                  "R1_TRIAL_CONSUMED                   NO"):
        check(f"registry field: {field.split()[0]}", field in reg)
    check("ITSF registry digest recorded unchanged",
          "b964b19a6b788bf9f47d1d24018dfc93836f74cbfd7ef69e4680471368d11fe9" in reg)

    # ---- 13. P-7: the structured companion manifest --------------------
    # The manifest is NOT authoritative. Its whole value is that every field it
    # carries is checked against the prose, the state, the decisions record,
    # the registry and the PSMV artifact, so it cannot silently drift.
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    ef_status_e4 = ef["E4_r_init_zero_no_direction"]["status"]   # from group 8
    for g in ("lineage_identity", "stage", "event_family", "reaction_timing",
              "entry_exit", "materiality", "data_grant",
              "outcome_reveal_authority", "seal_status", "trial_identity",
              "structural_n", "e4_status", "record_repair_2026_09_17",
              "artifacts", "version_control"):
        check(f"manifest group present: {g}", g in man)
    check("manifest declares itself non-authoritative",
          "NOT AUTHORITATIVE" in man["authority_note"])
    check("manifest names the prose document as authoritative",
          man["authoritative_document"] == PREREG.name)

    li = man["lineage_identity"]
    check("manifest lineage identity", li["lineage"] == "R1"
          and li["is_continuation_of_prior_lineage"] is False)
    check("manifest provenance matches the decisions record",
          all(v in dec for v in ("DELEGATED_OWNER_RULING", "Aaron",
                                 "Fable 5.1", "ChatGPT")))

    st = man["stage"]
    check("manifest stage: S1 SEALED / S0 CLOSED / PSMV COMPLETE",
          (st["stage"], st["s0"], st["s1"], st["psmv"])
          == ("S1 SEALED", "CLOSED", "SEALED", "COMPLETE"))
    check("manifest stage: S2 not authorized, nothing run",
          st["s2_authorized"] is False and st["experiments_run"] is False
          and st["backtest_run"] is False)
    check("manifest revision matches the prereg header",
          has(doc, f"REVISION = {st['revision']}"), st["revision"])

    efam = man["event_family"]
    check("manifest event family == {CPI, NFP}, pooled",
          sorted(efam["included"]) == ["CPI", "NFP"] and efam["pooled"] is True)
    check("manifest FOMC deferred, never falsified",
          efam["deferred"] == ["FOMC"] and efam["fomc_falsified"] is False
          and has(doc, "FOMC = UNRESOLVED / DEFERRED"))

    rt, ee = man["reaction_timing"], man["entry_exit"]
    check("manifest reaction anchors appear in the prose",
          all(a in doc for a in (rt["p_pre"], "C(08:31)"))
          and rt["reaction_window_bars"] == 2)
    check("manifest signal instant matches the prose",
          rt["signal_complete_et"] == "08:32:00" and "08:32:00" in doc)
    check("manifest P-2 ruling matches the prose", rt["p_2_ruling"] == "OPTION A"
          and has(doc, "P-2  REACTION WINDOW = OPTION A"))
    check("manifest entry/exit match the prose",
          ee["entry"] == "O(08:33)" and ee["exit"] == "O(09:29)"
          and ee["holding_minutes"] == 56 and "56 minutes" in doc)
    check("manifest records O(08:32) as DROPPED",
          ee["dropped_entry_reference"] == "O(08:32)")

    mt = man["materiality"]
    check("manifest k matches OD-4 in the prose",
          mt["k"] == 1 and has(doc, "OD-4 MATERIALITY = k = 1"))
    check("manifest M matches the prose", mt["M"] == "$3.99"
          and has(doc, "M = 1 x C_base_RT = $3.99"))
    check("manifest forbids post-hoc k revision",
          mt["k_revisable_after_an_outcome"] is False)
    check("manifest carries the PLANNING_POWER_TABLE status",
          mt["planning_power_table"]
          == "TO_BE_REFRESHED_OUTSIDE_PSMV / BEFORE_SEAL IF REQUIRED")

    dg = man["data_grant"]
    check("manifest OD-1 = GRANT, R1 scope only",
          dg["od_1"] == "GRANT" and dg["scope"] == "R1 only")
    check("manifest denies IV / Lockbox / protected ITSF outcomes",
          dg["internal_validation"] == dg["lockbox"]
          == dg["protected_itsf_outcomes"] == "NOT GRANTED")
    check("manifest calendar digest == the digest PSMV verified",
          dg["event_calendar_sha256"] == rep["inputs"]["event_calendar_sha256"])
    check("manifest symbology digest == the digest PSMV verified",
          dg["symbology_csv_sha256"] == rep["inputs"]["symbology_csv_sha256"])
    check("manifest: ITSF repository not modified",
          dg["itsf_repository_modified"] is False)

    ra = man["outcome_reveal_authority"]
    check("manifest: outcome reveal NOT GRANTED, Owner only",
          ra["outcome_reveal"] == "NOT GRANTED"
          and ra["reveal_authority"].startswith("Aaron"))
    check("manifest: no R1 outcome inspected, no exposure, no engine",
          ra["r1_outcome_inspected"] is False
          and ra["r1_outcome_exposure"] == "NONE"
          and ra["r1_outcome_engine_built"] is False)
    check("manifest: OD-3 gate accepted, post-seal, NOT RUN",
          "NOT RUN" in ra["pre_reveal_power_gate"])

    ss = man["seal_status"]
    check("manifest: prereg SEALED, by Aaron, executed by Claude Opus",
          ss["prereg_sealed"] is True
          and ss["sealed_by"] == "Aaron (Owner)"
          and ss["seal_executed_by"].startswith("Claude Opus"))
    check("manifest seal-condition count matches the prose",
          ss["seal_conditions_total"] == 11
          and ss["seal_conditions_satisfied"] == 11
          and not ss["outstanding_conditions"]
          and has(doc, "STATUS: 11 of 11 satisfied"))
    check("manifest does not fake a sealed-commit SHA inside the sealed content",
          "R1_S1_SEAL_ATTESTATION.json" in ss["sealed_commit"])
    check("manifest still names the sealed document",
          man["authoritative_document"] == "R1_S1_PREREGISTRATION_SEALED.md")

    ti = man["trial_identity"]
    check("manifest trial ordinal matches the registry",
          ti["sample_formal_trial_ordinal"] == 2
          and "SAMPLE_FORMAL_TRIAL_ORDINAL         2" in reg)
    check("manifest exposure count matches the registry",
          ti["inherited_researcher_exposure_count"] == 1575
          and "INHERITED_RESEARCHER_EXPOSURE_COUNT 1575" in reg)
    check("manifest: R1 trial NOT consumed",
          ti["r1_trial_consumed"] is False
          and "R1_TRIAL_CONSUMED                   NO" in reg)
    check("manifest ITSF registry digest matches the registry record",
          ti["itsf_registry_sha256"] in reg
          and ti["itsf_registry_mutated"] is False)

    sn = man["structural_n"]
    check("manifest n matches the PSMV artifact",
          sn["pre_seal_structural_n"] == rep["pre_seal_structural_n"] == 252)
    check("manifest CPI/NFP split matches the artifact",
          sn["cpi"] == rep["balance_at_pre_seal_structural_n"]
                          ["per_event_type"]["CPI"]
          and sn["nfp"] == rep["balance_at_pre_seal_structural_n"]
                              ["per_event_type"]["NFP"])
    check("manifest funnel matches the artifact funnel",
          sn["funnel"]["E0_cpi_or_nfp_calendar_events"] == e0
          and sn["funnel"]["E1_minus_any_fomc_calendar_entry"] == e1
          and sn["funnel"]["E2_minus_exact_roll_transition_sessions"] == e2
          and sn["funnel"]["E3_minus_missing_required_structural_anchors"] == e3)
    check("manifest exact roll exclusions == 0",
          sn["exact_roll_transition_exclusions"] == 0)
    check("manifest keeps POST_SEAL_SIGNAL_DEFINED_N unset",
          sn["post_seal_signal_defined_n"] is None)

    e4 = man["e4_status"]
    check("manifest E4 status matches the artifact",
          e4["status"] == ef_status_e4)
    check("manifest: no price was inspected to close E4",
          e4["price_inspected_to_close_e4"] is False)

    rr = man["record_repair_2026_09_17"]
    check("manifest carries PSMV_MDE_SCOPE_VIOLATION = RECORD_HYGIENE_ONLY",
          rr["PSMV_MDE_SCOPE_VIOLATION"] == "RECORD_HYGIENE_ONLY")
    check("manifest carries R1_OUTCOME_CONTAMINATION = NO",
          rr["R1_OUTCOME_CONTAMINATION"] == "NO")
    check("manifest carries PSMV_RERUN_REQUIRED = NO and PSMV_RERUN = NO",
          rr["PSMV_RERUN_REQUIRED"] == "NO" and rr["PSMV_RERUN"] == "NO")
    check("manifest: structural facts unchanged, artifacts unmodified",
          rr["structural_facts_changed"] is False
          and rr["artifacts_modified"] is False)

    for name, dig in man["artifacts"].items():
        check(f"manifest digest matches the file on disk: {name}",
              sha256_of(P / "artifacts" / name) == dig, dig[:16])

    vc = man["version_control"]
    commit = vc["PRE_SEAL_PROJECT_COMMIT"]
    check("manifest commit field is PENDING or a full 40-hex sha",
          commit == "PENDING" or re.fullmatch(r"[0-9a-f]{40}", commit)
          is not None, commit[:12])
    check("manifest: the PRE-SEAL commit is NOT the sealed commit",
          vc["pre_seal_commit_is_the_sealed_commit"] is False)
    check("manifest points at the seal identity, and keeps both tags",
          vc["SEAL_IDENTITY"] == "R1_S1_SEAL_ATTESTATION.json"
          and vc["seal_tag"] == "r1-s1-sealed"
          and vc["pre_seal_tag_preserved"] == "r1-pre-seal")
    if commit != "PENDING":
        check("PROJECT_STATE records the same PRE_SEAL_PROJECT_COMMIT",
              commit in state)
        check("the trial registry records the same PRE_SEAL_PROJECT_COMMIT",
              commit in reg)

    # ---- 14. the seal attestation -------------------------------------
    # Skipped in the CONTENT_COMMIT itself, where the attestation does not yet
    # exist. Once it does, every sealed digest is recomputed from disk.
    if not SEAL.exists():
        notes.append("SKIP  seal attestation not present yet "
                     "(expected inside the CONTENT_COMMIT)")
    else:
        seal = json.loads(SEAL.read_text(encoding="utf-8"))
        check("seal: PREREG_SEALED = YES", seal["PREREG_SEALED"] == "YES")
        check("seal: SEALED_BY = Aaron", seal["SEALED_BY"].startswith("Aaron"))
        check("seal: SEAL_EXECUTED_BY = Claude Opus under Aaron authorization",
              seal["SEAL_EXECUTED_BY"].startswith("Claude Opus"))
        check("seal: Fable recorded as packet decider, NOT as sealer",
              seal["delegated_owner_packet"]["DECIDED_BY"] == "Fable 5.1"
              and "Fable" not in seal["SEALED_BY"]
              and "Fable" not in seal["SEAL_EXECUTED_BY"])
        cc = seal["CONTENT_COMMIT"]
        check("seal: CONTENT_COMMIT is a full 40-hex sha",
              re.fullmatch(r"[0-9a-f]{40}", cc) is not None, cc[:12])
        check("seal: CONTENT_COMMIT is not the pre-seal commit",
              cc != "8656701564d798a227efa9f46e2f581353017ff5")
        check("seal: the sealed set covers every required record",
              all(k in seal["sealed_digests"] for k in (
                  "R1_S1_PREREGISTRATION_SEALED.md", "R1_PREREG_MANIFEST.json",
                  "R1_DELEGATED_OWNER_DECISIONS.md", "R1_S0_PROVENANCE.md",
                  "R1_TRIAL_REGISTRY.md",
                  "artifacts/PSMV_STRUCTURAL_REPORT.json",
                  "artifacts/PSMV_PURITY_ATTESTATION.json")))
        for rel, dig in seal["sealed_digests"].items():
            check(f"seal digest verifies on disk: {rel}",
                  (P / rel).exists() and sha256_of(P / rel) == dig, dig[:16])
        check("seal: PSMV artifacts keep their PSMV-time digests",
              seal["sealed_digests"]["artifacts/PSMV_STRUCTURAL_REPORT.json"]
              == "df0242bad6e2a1e2eb6ad1c412f91ffc1d9d421ef036ea802f7fd382e68aef47"
              and seal["sealed_digests"]["artifacts/PSMV_PURITY_ATTESTATION.json"]
              == "67e13b1770d1895084c2a989fb8c67e5692b1888f11d3c21cd464cdb7f546c7e")
        check("seal: S2 explicitly NOT authorized by the seal",
              seal["authorizes"]["S2_IMPLEMENTATION"] == "NOT AUTHORIZED"
              and seal["authorizes"]["R1_OUTCOME_REVEAL"] == "NOT AUTHORIZED")
        check("seal: PSMV record preserved",
              seal["psmv"]["PSMV_COMPLETE"] == "YES"
              and seal["psmv"]["PSMV_RERUN"] == "NO"
              and seal["psmv"]["PSMV_MDE_SCOPE_VIOLATION"] == "RECORD_HYGIENE_ONLY"
              and seal["psmv"]["R1_OUTCOME_CONTAMINATION"] == "NO")
        check("seal: P-5 preserved as NON_BLOCKING_RESIDUAL",
              seal["residuals"]["P-5"] == "NON_BLOCKING_RESIDUAL")
        check("seal: operative design matches the manifest",
              seal["operative_design"]["k"] == man["materiality"]["k"]
              and seal["operative_design"]["PRIMARY_ENTRY_REFERENCE"]
              == man["entry_exit"]["entry"]
              and seal["operative_design"]["EXIT"] == man["entry_exit"]["exit"]
              and seal["operative_design"]["PRE_SEAL_STRUCTURAL_N"]
              == man["structural_n"]["pre_seal_structural_n"])
        if "SEALED_COMMIT        = PENDING" not in state:
            check("PROJECT_STATE records the attested CONTENT_COMMIT",
                  cc in state)

    for line in notes:
        print(line)
    print()
    for line in failures:
        print(line)
    print(f"\n{len(notes)} passed, {len(failures)} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
