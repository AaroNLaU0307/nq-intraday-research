# -*- coding: utf-8 -*-
"""VERIFY.md -- the contract for a POST-HOLD REMEDIATION VERIFICATION.

WHY THIS IS A DIFFERENT DOCUMENT FROM `REVIEW.md`. That one opens an
outcome-blind, judgment-first adjudication of O1-O13 against a tree the
reviewer has never seen. This one opens something much narrower and with the
opposite blindness posture on exactly one axis: the reviewer's OWN frozen
findings are the comparand, deliberately, because closure cannot be verified
against a baseline the verifier is not allowed to read.

Everything else is unchanged. Outcome blindness stands. The delivery is sealed,
the guard arms before pytest, the workspace is supplied explicitly, and a
builder sentence is worth nothing here that it was not worth before.
"""


def _targets_section(profile: dict, add) -> None:
    for target in profile["verification_targets"]:
        add("### %s -- %s" % (target["id"], target["title"]))
        add("")
        add("**FROZEN FINDING (the claim under verification).** %s"
            % target["frozen_finding"])
        add("")
        add("**WHERE TO LOOK.** The repaired loci are:")
        add("")
        for locus in target["loci"]:
            add("* `%s`" % locus)
        add("")
        add("**WHAT CLOSURE REQUIRES.** %s" % target["closure_requires"])
        add("")
        if target.get("frozen_probe_refs"):
            add("**THE PROBE THAT ESTABLISHED IT.** %s"
                % ", ".join("`%s`" % r for r in target["frozen_probe_refs"]))
            add("")
        add("**BUILDER'S CLAIM, which is SELF_REPORTED and proves nothing.** %s"
            % target["builder_claim"])
        add("")
        # A DECLARED OPEN HALF BELONGS BESIDE THE CLAIM, not in a later
        # section a reader might skip. The builder saying what it did NOT
        # repair is the one builder sentence worth printing in full, because
        # it is the only one that cannot flatter the repair.
        if target.get("builder_declared_incompleteness"):
            add("**BUILDER-DECLARED INCOMPLETENESS -- read this before "
                "judging closure.** %s"
                % target["builder_declared_incompleteness"])
            add("")


import textwrap


def _wrap(text: str, width: int = 74) -> list:
    return textwrap.wrap(text, width=width) or [""]


def _field(label: str, text: str, a) -> None:
    """A fixed-width header field whose value wraps under its own column."""
    lines = _wrap(text, 74 - 21)
    a("%-18s = %s" % (label, lines[0]))
    for line in lines[1:]:
        a("%s%s" % (" " * 21, line))


_WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six",
          7: "seven", 8: "eight", 9: "nine", 10: "ten"}


def _count(n: int) -> str:
    return _WORDS.get(n, str(n))


def render(profile: dict) -> str:
    L = []
    a = L.append
    baselines = profile["frozen_baseline"]
    if not isinstance(baselines, list):
        baselines = [baselines]
    target = profile["repaired_target"]
    ids = ", ".join(t["id"] for t in profile["verification_targets"])
    control_ids = [c["id"] for c in profile.get("non_regression_controls") or []]

    a("# VERIFY -- %s" % profile["review_id"])
    a("")
    a("```")
    a("VERIFICATION_ID    = %s" % profile["review_id"])
    _field("KIND", profile["verification_kind"], a)
    a("THIS IS NOT        = N14 Round 3. It is not a substantive round of any")
    a("                     kind, it consumes no review round, and it does not")
    a("                     reopen O1-O13.")
    a("ROUND ACCOUNTING   = unchanged. Round 1 HOLD/CONSUMED, Round 2")
    a("                     HOLD/CONSUMED, ordinary N14 budget EXHAUSTED.")
    a("CONTRACT           = %s" % profile["contract_version"])
    a("PROFILE            = %s" % profile["profile_version"])
    _field("BLINDNESS",
           "OUTCOME_BLIND. Judgment-first does NOT apply to the frozen "
           "material in `frozen/`: those findings are the verification "
           "baseline on purpose, and closure cannot be checked against a "
           "baseline you may not read. Everything else is unchanged.", a)
    _field("SEAT",
           "the SAME independent session that authored the %s. That is "
           "deliberate here and is the one place this differs from an "
           "ordinary review seat: you are checking whether YOUR OWN stated "
           "failure paths still exist." % profile["seat_note"], a)
    _field("MUST_NOT_BE",
           "the builder (Claude Opus / Claude Code) session or any subagent "
           "of it.", a)
    a("REAL_MC_AUTHORIZED = NO    REAL_MC_EXECUTED = NO")
    a("STATISTICAL_SIGNAL = NOT_TESTED    STATISTICAL_OUTCOME_EXPOSED = NO")
    a("```")
    a("")

    a("## 0. What you are being asked, and what you are not")
    a("")
    controls = profile.get("non_regression_controls") or []
    if controls:
        a("**ASKED, PRIMARY:** for %s -- the findings you left NOT_CLOSED, and"
          % ids)
        a("the consequential blocker you raised -- determine independently")
        a("whether the stated failure path still exists in the exact repaired")
        a("tree carried in `tree/`.")
        a("")
        a("**ASKED, CONTROL ONLY:** for %s -- which you already verified CLOSED"
          % ", ".join(control_ids))
        a("-- determine whether this residual repair REOPENED any of them. That")
        a("is a non-regression question and nothing more: do not re-derive their")
        a("closure and do not treat them as fresh substantive review.")
        a("")
    else:
        a("**ASKED:** for each of the %s frozen findings %s, determine"
          % (_count(len(profile["verification_targets"])), ids))
        a("independently whether the stated failure path still exists in the")
        a("exact repaired tree carried in `tree/`.")
        a("")
    a("**ALSO ASKED, and it is not a broad audit:** whether the repairs")
    a("themselves broke something in the seams they directly changed. A repair")
    a("that closes its finding by damaging the code around it has not produced")
    a("a verified remediation, and a contract that could only report that in a")
    a("footnote would be asking you to certify closure you do not believe in.")
    a("")
    a("**THE SEAMS THAT ARE IN SCOPE ARE MECHANICAL, not a judgement call.**")
    a("They are the %s production files listed in section 1, and the call"
      % _count(len(profile["repaired_target"]["production_files_changed"])))
    a("sites the repair itself altered inside them. Anything reachable only by")
    a("going further afield is out of scope.")
    a("")
    a("**NOT ASKED:** to re-adjudicate O1-O13, to audit the repository, to")
    a("re-derive a verdict you have already returned, or to go looking outside")
    a("those seams. A finding that is genuinely unrelated to the repairs --")
    a("pre-existing, elsewhere in the tree, or reachable only by widening the")
    a("search -- goes in a clearly separated section and does NOT affect")
    a("closure. The line between the two is the one drawn above: did this")
    a("repair introduce it, in a seam this repair changed.")
    a("")
    a("**A BUILDER SENTENCE IS NOT EVIDENCE HERE EITHER.** Every 'FIX' and")
    a("'BUILDER'S CLAIM' line below is SELF_REPORTED. The repaired source, the")
    a("focused tests and your own frozen probes are in this package precisely")
    a("so that closure can be established rather than accepted.")
    a("")

    a("## 1. The exact repaired target")
    a("")
    a("```")
    a("REPAIR_COMMIT   = %s" % target["repair_commit"])
    a("ROOT_TREE       = %s" % target["root_tree"])
    a("ITSF_SRC_TREE   = %s" % target["itsf_src_tree"])
    a("MC_SUBTREE_TREE = %s" % target["mc_subtree_tree"])
    a("```")
    a("")
    a("`tree/` is a Git export of that commit, file by file, and `MANIFEST.json`")
    a("records each file's blob id beside its sha256. Verify `MANIFEST.json`")
    a("against the digest you were given out of band, then check every payload")
    a("row against the file it names. `MANIFEST.json` does not contain its own")
    a("hash -- a document that certifies itself certifies nothing.")
    a("")
    a("**The %s production files the repair touched:**"
      % _count(len(profile["repaired_target"]["production_files_changed"])))
    a("")
    for path in profile["repaired_target"]["production_files_changed"]:
        a("* `%s`" % path)
    a("")
    a("Nothing else in `src/` moved. That claim is checkable here: the three")
    a("tree digests above pin it, and `git` is not needed to check them because")
    a("every payload row carries its blob id.")
    a("")

    a("## 2. The frozen baseline, carried byte-exact")
    a("")
    width = max(len(f.get("prefix", "frozen/") + r["name"])
                for f in baselines for r in f["artifacts"])
    for frozen in baselines:
        for line in _wrap(frozen["intro"]):
            a(line)
        a("")
        a("```")
        for row in frozen["artifacts"]:
            a("%-*s %8d bytes  %s"
              % (width, frozen.get("prefix", "frozen/") + row["name"],
                 row["byte_count"], row["sha256"][:16] + "..."))
        a("```")
        a("")
    for line in profile["frozen_baseline_statement"]:
        a(line)
    a("")
    a("**Nothing in `frozen/` was edited, reformatted or excerpted.** If any of")
    a("it disagrees with how a finding is restated in section 3, `frozen/` is")
    a("authoritative and the restatement is the defect.")
    a("")
    a("**One honest note about the blindness machinery.** An ordinary delivery")
    a("runs a CLAIM_BLIND scan that refuses any admitted prose carrying prior")
    a("judgement of the implementation under review. This package carries")
    a("exactly that, on purpose -- and the scan did not fire on any of it. The")
    a("patterns are narrow and do not match your phrasing, so no exemption was")
    a("needed and none is declared. Read that as: the gate is not what is")
    a("keeping this package honest here; the declared purpose is. The outcome")
    a("scan is unchanged and did run over every byte.")
    a("")

    a("## 3. The %s verification targets"
      % _count(len(profile["verification_targets"])))
    a("")
    a("Each is stated as the FROZEN claim, the repaired loci, and what closure")
    a("requires. The closure criterion is the finding's own required repair")
    a("intent -- not a criterion invented to be satisfiable.")
    a("")
    _targets_section(profile, a)

    if profile.get("non_regression_controls"):
        a("## 3.1 The non-regression controls")
        a("")
        a("You verified these CLOSED against the previous repair. The only")
        a("question here is whether the residual repair reopened one. A repair")
        a("that closes its own findings by reopening an earlier one has not")
        a("produced a remediation, which is why they are in the package at all")
        a("-- and equally, re-adjudicating them would be the broad review this")
        a("delivery is not.")
        a("")
        for control in profile["non_regression_controls"]:
            a("**%s -- %s.** %s" % (control["id"], control["title"],
                                    control["control_question"]))
            a("")
            a("Controls: %s"
              % ", ".join("`%s`" % t for t in control["control_tests"]))
            a("")
        a("**Report each as NO_REGRESSION or REGRESSED.** A REGRESSED control")
        a("fails the whole verification on its own, however the primary targets")
        a("came out: closure bought by reopening something already closed is")
        a("not closure.")
        a("")

    for index, block in enumerate(profile.get("singled_out_sections", [])):
        a("## 4%s %s" % ("." + str(index) if index else ".",
                         block["heading"]))
        a("")
        for line in block["body"]:
            a(line)
        a("")

    a("## 5. Running the focused evidence")
    a("")
    a("```")
    a("run_review.cmd --review-output-base \"<the writable base your dispatch names>\"")
    a("```")
    a("")
    a("Same launcher, same sealed runtime, same explicit workspace capability as")
    a("the delivery you last ran -- nothing about that machinery changed. It")
    a("takes exactly one argument: the writable base your dispatch authorised.")
    a("There is no default and `TMP`/`TEMP`/`TMPDIR` are never read to choose")
    a("one.")
    a("")
    a("It runs the selected repository tests from `tree/` plus the boundary")
    a("probes. The focused evidence is:")
    a("")
    for row in profile["focused_test_files"]:
        a("* `%s` -- %s" % (row["path"], row["what"]))
    a("")
    a("Read those first: every test in them asserts a FINAL")
    a("OBSERVABLE -- the seal candidate, the returned object, the ledger bytes --")
    a("rather than that a helper exists or a source string appears. That")
    a("distinction is the builder's own account of why several of your findings")
    a("survived a green suite; judge whether the new tests actually avoid it.")
    a("")
    a("**Guard denials.** `GUARD_REPORT.json` splits `expected_denials` from")
    a("`unexpected_denials`: a sealed negative control declares the refusal it")
    a("is about to cause. STOP on a non-empty `unexpected_denials`, on a")
    a("non-empty `missing_prescribed_denials`, or on any launcher/runtime")
    a("refusal. The runner applies the same rule and exits non-zero on it,")
    a("independently of the test result.")
    a("")
    a("**Builder-reported figures, SELF_REPORTED, for you to confirm or refute:**")
    a("")
    a("```")
    for line in profile["builder_reported_measurements"]:
        a(line)
    a("```")
    a("")
    for line in profile["measurement_provenance"]:
        a(line)
    a("")

    a("## 6. Your output")
    a("")
    a("Write into the review workspace the launcher prints, never into this")
    a("delivery, which is immutable:")
    a("")
    a("```")
    a("<review workspace>\\VERIFICATION_FINDINGS.md")
    a("<review workspace>\\VERIFICATION_FREEZE.json")
    a("<review workspace>\\VERIFICATION_ATTESTATION.md")
    a("```")
    a("")
    a("`VERIFICATION_FINDINGS.md` must give, for EACH of %s:" % ids)
    a("")
    a("```")
    a("CLOSURE          CLOSED | NOT_CLOSED | CLOSED_WITH_RESERVATION")
    a("BASIS            what you executed or read that established it")
    a("EXAMINED_LOCUS   the exact file and symbol")
    a("EVIDENCE_CLASS   REPRODUCED | READ | SELF_REPORTED")
    a("RESIDUAL         what closure does NOT cover, if anything")
    a("```")
    a("")
    a("`CLOSED_WITH_RESERVATION` exists so that a repair which closes the stated")
    a("failure path while leaving a named narrower one open can be recorded")
    a("honestly instead of being forced into a binary.")
    a("")
    if profile.get("non_regression_controls"):
        a("**Then a section `NON_REGRESSION`**, one line per control:")
        a("")
        a("```")
        for index, cid in enumerate(control_ids):
            a("%-5s NO_REGRESSION | REGRESSED%s"
              % (cid, "   + what you ran or read" if not index else ""))
        a("```")
        a("")
    a("**Then a section `CONSEQUENTIAL_REGRESSIONS`**, for anything the repair")
    a("broke in the seams it directly changed (section 0). For each:")
    a("")
    a("```")
    a("SEVERITY         BLOCKER | NON_BLOCKING")
    a("INTRODUCED_BY    which repair, and the changed seam it lives in")
    a("FAILURE_PATH     concrete input or state, and the wrong output or refusal")
    a("BASIS            what you executed or read that established it")
    a("```")
    a("")
    a("**A BLOCKER needs a concrete failure path**, the same standard a")
    a("blocking finding needed: an input or state, and the wrong behaviour that")
    a("follows. A cleaner design you would have preferred is not a blocker, and")
    a("neither is a risk nobody can reach. An observation unrelated to the")
    a("changed seams does not affect closure -- put it in a separate section.")
    a("")
    a("End with:")
    a("")
    a("```")
    for line in profile["overall_verdict_rule"]:
        a(line)
    a("```")
    a("")
    a("There is no fourth value and this is **not** a GO/STOP verdict on N14.")
    a("Whether N14 proceeds is Aaron's decision and is not being delegated here.")
    a("")
    a("Then `VERIFICATION_FREEZE.json` recording `VERIFICATION_ID`,")
    a("`MANIFEST_SHA256`, `VERIFICATION_FINDINGS_SHA256`, the digest of every")
    a("frozen return you verified against, a timestamp and your")
    a("session identity; then `VERIFICATION_ATTESTATION.md` stating what you")
    a("executed but did not inspect.")
    a("")

    a("## 7. STOP conditions")
    a("")
    a("Report and STOP, rather than working around, if:")
    a("")
    a("* `MANIFEST.json` does not match the digest you were given, or any")
    a("  payload row does not match its file;")
    for frozen in baselines:
        a("* `%s` does not hash to the value `%s` declares;"
          % (frozen.get("prefix", "frozen/") + frozen["findings_name"],
             frozen.get("prefix", "frozen/") + frozen["freeze_name"]))
    a("* the launcher or the runtime refuses;")
    a("* `unexpected_denials` or `missing_prescribed_denials` is non-empty;")
    a("* a locus named in section 3 is absent from `tree/`;")
    a("* you need something to adjudicate a closure that is not in this package.")
    a("")
    a("**A STOP is not a NOT_CLOSED and costs nothing.** Reporting a defective")
    a("package is the correct outcome for a defective package.")
    a("")
    a("Finally: if you conclude that a finding is closed only because the")
    a("finding was restated more narrowly than you wrote it, say that. The")
    a("frozen text in `frozen/` is authoritative over section 3, and a")
    a("re-scoped finding is itself a result worth returning.")
    return "\n".join(L) + "\n"
