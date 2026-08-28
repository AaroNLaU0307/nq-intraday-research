"""A record cited by path must be reachable at that path.

THE INCIDENT THIS GENERALISES. On 2026-08-26 a fresh Sol review returned HOLD
and the verdict existed only in the conversation. A handoff cited a record for
it; the record on disk held different content. Nothing on disk was false — the
ruling simply was not there, and the citation made it look as though it were.

WHY A DANGLING CITATION IS A SAFETY PROBLEM HERE AND NOT ONLY UNTIDINESS.
Eight of the paths below moved into `ops/outcome_quarantine/` and their
citations did not move with them. A reader following one gets "not found" —
and what a reader does next is search. Of the three reviewer seats burned on
this project, two were burned by exactly that: one broad symbol search, one
single targeted grep. A citation that resolves to nothing is an invitation to
the one action the blind-seat rule forbids.

THREE CLASSES, and they are not the same fact:

  QUARANTINED_MOVED        the artifact exists, at the quarantine path; the
                           citation is stale. Each entry is CHECKED — the
                           quarantine copy must be there, so the reason
                           becomes false if someone moves or deletes it.
  PROPOSED_NOT_YET_EXISTING a path a plan proposes and does not claim exists.
                           Legitimate. One of them is the S5 filename that
                           collides with failure-model boundary (2) and is
                           currently before a decision seat.
  PROSE_PLACEHOLDER        `ops/...md` in running text. Not a citation.
  CITED_BUT_NEVER_EXISTED  never added and never deleted anywhere in git
                           history, absent from the worktree, AND cited as
                           though it existed. CURRENTLY EMPTY — all three
                           original members turned out to be proposals when
                           someone finally read the citing lines. Kept as a
                           class because the shape is real (2026-08-26: a
                           ruling that existed only in chat), not because
                           anything is in it.

The remediation of the stale citations is deliberately NOT done here. How an
outcome-clean extract should cite a quarantined source is a quarantine-
discipline question, not a path typo, and the builder choosing a reading is
the failure mode this project has paid for twice this week.
"""

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OPS = REPO / "ops"
QUARANTINE = OPS / "outcome_quarantine"

#: SCOPE, stated because the decision seat asked for it to be. This matches
#: the FORWARD-SLASH `ops/...` form only. A backslash path or a bare filename
#: is not covered, so "pinned, cannot grow" means: cannot grow IN THIS FORM.
#:
#: That limit is load-bearing rather than accidental — it is the same edge as
#: ruling C1, whose markers keep the BARE filename precisely so they do not
#: read as citations. One blade, two sides: what the regex ignores is exactly
#: what a marker is allowed to say.
_REF = re.compile(r"`?(ops/[A-Za-z0-9_./-]+\.(?:md|json|py))`?")

#: SOURCE-PATH REFERENCES, added 2026-08-28. `ops/` documents also cite code
#: by path, and those dangle the same way — a reader who cannot resolve one
#: searches, which is the action the blind-seat rule forbids.
#:
#: THE LOOKBEHIND IS THE WHOLE TRICK, and it was learned by getting it wrong.
#: Without it the pattern matches the TAIL of a correctly-qualified
#: cross-repository path: `qros-runtime/tests/x.py` contains `tests/x.py`, so
#: a properly written reference was reported as dangling. Half of the two
#: "findings" that motivated this guard were the detector manufacturing them.
_SRC_REF = re.compile(
    r"(?<![A-Za-z0-9_./-])((?:tests|src|scripts)/[A-Za-z0-9_./-]+\.py)")

#: Sibling repositories a cross-repo reference may name. A reference that
#: starts with one of these is qualified and is not this repository's to
#: resolve — which is why the lookbehind above must not strip the prefix.
_SIBLING_REPOS = ("qros-runtime", "quant-research-knowledge-base")

_KNOWN = {
    "ops/...md": "PROSE_PLACEHOLDER",
    "ops/PROMPT_...md": "PROSE_PLACEHOLDER",
    "ops/TRIAL_REGISTRY.pre-migration.2026-08-27.md":
        "PROPOSED_NOT_YET_EXISTING",
    "ops/migration-2026-08-27/registry-snapshot-pre-migration.md":
        "PROPOSED_NOT_YET_EXISTING",
    "ops/DECISION_PACKET_ND2_ND3.md": "QUARANTINED_MOVED",
    "ops/MC_DR5_BUILD_PACKET.md": "QUARANTINED_MOVED",
    "ops/MC_TO_STRATEGY_MASTER_PLAN.md": "QUARANTINED_MOVED",
    "ops/ND2_ND3_FABLE_DECISION_PROMPT.md": "QUARANTINED_MOVED",
    "ops/ND2_ND3_RULING_REVIEW_FINDINGS.md": "QUARANTINED_MOVED",
    "ops/RULING_FABLE_FOUR_OPEN_2026-08-26.md": "QUARANTINED_MOVED",
    "ops/RULING_PROPOSAL_ND2_ND3_FABLE_2026-08-24.md": "QUARANTINED_MOVED",
    "ops/S0_T001_RESULT_DECISION_ADDENDUM.md": "QUARANTINED_MOVED",
    #: RECLASSIFIED 2026-08-27, and the reclassification is the finding.
    #:
    #: All three were first recorded as CITED_BUT_NEVER_EXISTED on the
    #: strength of a claim this file's author made without checking: that
    #: they read as citations of existing records. They do not. Reading the
    #: surrounding lines — which the first pass never did — each one is an
    #: option or a target:
    #:
    #:   MC_RUN_REGISTRY            "### R1 — a separate MC registry file",
    #:                              one of three options in an open collision
    #:                              decision. Its RULING_PROPOSAL says
    #:                              `RULING=R2`, so R1 was DECLINED: this file
    #:                              is a rejected option's hypothetical and
    #:                              will never exist by design.
    #:   STRATEGY_COUNCIL_ROUND4_LOCK
    #:                              the declared landing target of the
    #:                              recovery path already recorded in
    #:                              DECISION_PACKET_N00_AND_ND1 §D.1.3,
    #:                              waiting on Aaron's sealed proposal text.
    #:                              N00_N08_PROVENANCE_AUDIT_2026-08-25
    #:                              already searched exhaustively for it and
    #:                              recorded its absence — two days before
    #:                              this file claimed nobody had noticed.
    #:   SUPPLEMENT_LEDGER          "1. 是否新建 ops/SUPPLEMENT_LEDGER.md
    #:                              (…工程建议：建)" — literally an open
    #:                              question with a recommendation.
    #:
    #: THE LESSON, since it cost a decision seat a wasted item: the mechanical
    #: half (absent from history) was measured and correct. The intent half
    #: (cited as existing vs proposed) was ASSERTED — in the same document
    #: that argued intent cannot be inferred mechanically. Being right that a
    #: distinction is unmechanisable does not license guessing it by eye.
    "ops/MC_RUN_REGISTRY.md": "PROPOSED_NOT_YET_EXISTING",
    "ops/STRATEGY_COUNCIL_ROUND4_LOCK.md": "PROPOSED_NOT_YET_EXISTING",
    "ops/SUPPLEMENT_LEDGER.md": "PROPOSED_NOT_YET_EXISTING",
}


def _citing_documents():
    """`ops/*.md`, NOT recursive: the quarantine subtree is a valid target of
    a citation and is not scanned as a source of one."""
    return sorted(OPS.glob("*.md"))


def _dangling():
    out = {}
    for path in _citing_documents():
        text = path.read_text(encoding="utf-8")
        for ref in _REF.findall(text):
            if not (REPO / ref).exists():
                out.setdefault(ref, set()).add(path.name)
    return out


class TestNoUnrecordedDanglingCitation(unittest.TestCase):

    def test_the_scan_reaches_the_documents(self):
        """This file's own premise: every assertion below is over a scanned
        set, and an empty scan would report all of them clean."""
        docs = _citing_documents()
        self.assertGreater(len(docs), 40,
                           f"the citation scan reached {len(docs)} documents; "
                           "at that count it proves nothing")

    def test_every_dangling_citation_is_recorded(self):
        new = sorted(set(_dangling()) - set(_KNOWN))
        self.assertEqual([], new,
                         "these paths are cited in ops/ and do not resolve; a "
                         "reader who follows one gets nothing, and what a "
                         "reader does next is search:\n  " + "\n  ".join(new))

    def test_no_recorded_entry_has_gone_stale(self):
        fixed = sorted(set(_KNOWN) - set(_dangling()))
        self.assertEqual([], fixed,
                         "these are recorded as dangling but are no longer "
                         "SCANNED as dangling. Two ways that happens and the "
                         "old wording named only one: the path now resolves, "
                         "OR every citation of it became a marker (ruling C3 "
                         "— expected; delete the entry in the same "
                         "change):\n  " + "\n  ".join(fixed))


class TestEachClassificationIsCheckable(unittest.TestCase):
    """A reason that cannot be falsified is a comment, not a record.

    MEASURED HOLE, closed here. Reclassifying `MC_TO_STRATEGY_MASTER_PLAN.md`
    from QUARANTINED_MOVED to PROSE_PLACEHOLDER left every test green: the
    only checked class was the one being escaped FROM. A classification
    scheme where one class carries no check is a scheme with an exit.
    """

    def test_the_class_names_are_a_closed_set(self):
        """Otherwise a fifth class invented on the spot carries no check at
        all, which is the same exit one level up."""
        legal = {"PROSE_PLACEHOLDER", "PROPOSED_NOT_YET_EXISTING",
                 "QUARANTINED_MOVED", "CITED_BUT_NEVER_EXISTED"}
        stray = sorted({k for k in _KNOWN.values()} - legal)
        self.assertEqual([], stray, "unknown classification: " + ", ".join(stray))

    def test_a_prose_placeholder_is_not_a_real_filename(self):
        """The class the mutation escaped into. A placeholder contains an
        ellipsis; anything that looks like an actual path is a citation and
        has to be classified as one."""
        wrong = [ref for ref, kind in sorted(_KNOWN.items())
                 if kind == "PROSE_PLACEHOLDER" and "..." not in ref]
        self.assertEqual([], wrong,
                         "classified as running-text placeholders but they "
                         "are real paths:\n  " + "\n  ".join(wrong))

    def test_the_two_absent_classes_are_absent_from_history_too(self):
        """PROPOSED_NOT_YET_EXISTING and CITED_BUT_NEVER_EXISTED both assert
        the file is nowhere. That part IS checkable and is checked.

        WHAT IS NOT MECHANICAL, said plainly rather than faked: which of the
        two applies is a judgement about intent — a plan proposing a path
        versus a document citing a record as though it existed. Both look
        identical on disk.

        THE COUNTER-EXAMPLE THIS DOCSTRING USED TO GIVE WAS FALSE, and the
        correction matters more than the original point. It argued that a
        "PACKET means proposal" rule would misclassify, citing
        `DECISION_PACKET_N00_AND_ND1.md` naming `SUPPLEMENT_LEDGER.md` as a
        supposedly real missing record. The actual line reads
        "1. 是否新建 ops/SUPPLEMENT_LEDGER.md (…工程建议：建)" — an open
        question with a recommendation. On that example the name-based rule
        would have been RIGHT, and the eyeball classification was wrong.

        The name-based rule is still rejected, for a better reason: it keys
        on the container instead of the sentence, so it would be right by
        accident here and wrong wherever a packet cites a genuinely missing
        record. But the honest statement is that intent lives in the
        surrounding LINES — which are readable, and were simply not read.
        Nothing about the distinction was unmechanisable; it was unmeasured.
        """
        import subprocess
        present = []
        for ref, kind in sorted(_KNOWN.items()):
            if kind not in ("PROPOSED_NOT_YET_EXISTING",
                            "CITED_BUT_NEVER_EXISTED"):
                continue
            if (REPO / ref).exists():
                present.append(f"{ref}: on disk now")
                continue
            out = subprocess.run(
                ["git", "-C", str(REPO), "log", "--all", "--oneline",
                 "--diff-filter=AD", "--", ref],
                capture_output=True, text=True, errors="replace").stdout.strip()
            if out:
                present.append(f"{ref}: {out.splitlines()[0]}")
        self.assertEqual([], present,
                         "classified as never having existed, but they do or "
                         "did:\n  " + "\n  ".join(present))

    def test_every_quarantined_moved_artifact_is_in_the_quarantine(self):
        missing = []
        for ref, kind in sorted(_KNOWN.items()):
            if kind != "QUARANTINED_MOVED":
                continue
            if not (QUARANTINE / Path(ref).name).exists():
                missing.append(ref)
        self.assertEqual([], missing,
                         "classified QUARANTINED_MOVED, but not present in "
                         "ops/outcome_quarantine/ either — the classification "
                         "is now false:\n  " + "\n  ".join(missing))

    def test_nothing_is_classified_quarantined_while_sitting_in_ops(self):
        """The reverse: a file restored to ops/ would make the class wrong
        without making the guard above fail."""
        wrong = [ref for ref, kind in sorted(_KNOWN.items())
                 if kind == "QUARANTINED_MOVED" and (OPS / Path(ref).name).exists()]
        self.assertEqual([], wrong, "\n  ".join(wrong))

    def test_the_cited_but_never_existed_class_is_currently_empty(self):
        """DELETED THE GUARD THAT USED TO SIT HERE, and this replaces it.

        `test_the_never_existed_ones_are_still_absent_from_history` filtered
        `_KNOWN` for CITED_BUT_NEVER_EXISTED and asserted over the result. The
        reclassification emptied that class, so the test began passing over
        zero items — green, permanently, checking nothing. It was also
        strictly subsumed by the guard above, which covers both absent
        classes.

        A dormant guard reporting green is the failure this suite was built
        to find, so it is gone. What is pinned instead is the FACT that the
        class is empty: nothing in this repository is currently believed to
        have been cited into existence. If an entry ever joins the class this
        assertion fails, which is the right moment to look at it again — and
        the guard above already covers it mechanically from that instant."""
        cited = sorted(r for r, k in _KNOWN.items()
                       if k == "CITED_BUT_NEVER_EXISTED")
        self.assertEqual(
            [], cited,
            "something is classified CITED_BUT_NEVER_EXISTED again. That "
            "class was emptied on 2026-08-27 when all three members turned "
            "out to be proposals; re-read the citing LINES before trusting "
            "the label:\n  " + "\n  ".join(cited))


class TestSourcePathsCitedInOpsResolve(unittest.TestCase):
    """`ops/` documents cite code by path, and a dangling one behaves exactly
    like a dangling `ops/` citation: the reader searches.

    THE CROSS-REPOSITORY CASE is the reason this needs care rather than
    another regex. A reference to the sister runtime is not this
    repository's to resolve, and writing it qualified — `qros-runtime/…` —
    is the correct form, not a defect. The first version of this scan
    reported those as dangling because the pattern matched their tails.
    """

    def _dangling(self):
        out = {}
        for path in _citing_documents():
            text = path.read_text(encoding="utf-8")
            for ref in _SRC_REF.findall(text):
                if not (REPO / ref).exists():
                    out.setdefault(ref, set()).add(path.name)
        return out

    def test_the_scan_finds_source_references_at_all(self):
        """Premise. `assertEqual([], dangling)` is true of a scan that
        matched nothing."""
        total = set()
        for path in _citing_documents():
            total |= set(_SRC_REF.findall(path.read_text(encoding="utf-8")))
        self.assertGreater(len(total), 20,
                           "the source-path scan found %d references; at that "
                           "count it proves nothing" % len(total))

    def test_no_source_path_cited_in_ops_dangles(self):
        """NO ALLOWLIST, and that is measured rather than aspired to.

        A first version carried two entries for the unqualified paths that
        `FINDINGS_PENDING_UNFREEZE_2026-08-27.md` quotes while recording this
        very defect. Clearing that allowlist did not turn the test red —
        the entries were dead, because the record writes those paths in a
        deliberately broken form the pattern cannot match. A dead allowlist
        entry is worse than none: it implies a live exception."""
        dangling = sorted(self._dangling())
        self.assertEqual([], dangling,
                         "these code paths are cited in ops/ and do not "
                         "resolve here; if the target lives in a sibling "
                         "repository the reference needs its repo name:\n  "
                         + "\n  ".join(dangling))

    def test_the_record_of_the_defect_still_quotes_it_unresolvably(self):
        """The other half of the sentence above, asserted so it stays true.

        That record has to show the bad forms in order to be a record of
        them. It writes `<tests>/…` — close enough to read, impossible to
        match. If someone later "tidies" it into real paths, the record
        becomes two more instances of the defect it documents, and this
        fires before the scan above does."""
        record = OPS / "FINDINGS_PENDING_UNFREEZE_2026-08-27.md"
        self.assertTrue(record.exists())
        text = record.read_text(encoding="utf-8")
        self.assertIn("<tests>/", text,
                      "the record no longer quotes the paths in the broken "
                      "form, so it is about to start dangling itself")
        # NOT "contains no matchable path" — that was the first version and
        # it was too strong: the record legitimately names
        # `tests/test_cited_records_exist.py`, which resolves. What must hold
        # is that none of its paths DANGLE.
        unresolved = sorted(r for r in _SRC_REF.findall(text)
                            if not (REPO / r).exists())
        self.assertEqual([], unresolved,
                         "the record now carries a dangling source path: %r"
                         % unresolved)

    def test_a_qualified_cross_repo_reference_is_not_flagged(self):
        """The lookbehind, asserted as behaviour. Without it a correctly
        written cross-repo path is reported as dangling — measured, and it
        produced half of the two findings that motivated this guard."""
        for repo in _SIBLING_REPOS:
            sample = "see `%s/tests/test_x.py` for the detail" % repo
            self.assertEqual([], _SRC_REF.findall(sample),
                             "a qualified %s reference still matches; the "
                             "lookbehind is not doing its job" % repo)

    def test_an_unqualified_reference_is_still_flagged(self):
        """The other direction — otherwise the lookbehind could be widened
        until nothing matches at all."""
        self.assertEqual(["tests/test_x.py"],
                         _SRC_REF.findall("see `tests/test_x.py` for detail"))


class TestTheOffLimitsListItselfResolves(unittest.TestCase):
    """Every blind-seat prompt says: read that json, treat every path in it
    as closed. A dangling entry there is a seat that cannot know what to
    avoid — the same failure as a dangling citation, at the one place where
    it decides whether a seat gets burned.

    CHECKED AND CLEAN as of 2026-08-27, including the pair that looks like a
    typo: `EXPOSURE_LEDGER.md` and `ops/EXPOSURE_LEDGER.md` are two real,
    distinct files and both are listed."""

    LIST = OPS / "OUTCOME_CARRYING_ARTIFACTS.json"

    def _paths(self):
        import json
        data = json.loads(self.LIST.read_text(encoding="utf-8"))
        return [e["path"] for e in data["carries_outcome"]]

    def test_the_list_is_not_empty(self):
        self.assertGreater(len(self._paths()), 5,
                           "an empty off-limits list would make the check "
                           "below pass while protecting nothing")

    def test_every_off_limits_path_resolves_from_the_repository_root(self):
        missing = [p for p in self._paths() if not (REPO / p).exists()]
        self.assertEqual([], missing,
                         "the authoritative off-limits list names paths that "
                         "do not exist; a seat told to treat them as closed "
                         "cannot act on them:\n  " + "\n  ".join(missing))

    def test_every_quarantined_file_on_disk_is_on_the_list(self):
        """The direction that matters most: a file sitting in the quarantine
        and NOT declared outcome-carrying is one a seat has no instruction
        to avoid.

        The count is not decoration: `assertEqual([], undeclared)` is true of
        an empty quarantine, so a wrong QUARANTINE root would report this
        clean forever. Flagged by test_no_vacuous_guards on its first full
        run — by the guard written hours earlier, in this same file's
        sibling, for exactly this shape."""
        listed = {Path(p).name for p in self._paths()}
        on_disk = {p.name for p in QUARANTINE.glob("*.md")}
        self.assertGreater(len(on_disk), 5,
                           f"the quarantine scan found {len(on_disk)} files; "
                           "at that count this proves nothing")
        undeclared = sorted(on_disk - listed)
        self.assertEqual([], undeclared,
                         "these sit in ops/outcome_quarantine/ but are not in "
                         "carries_outcome, so no prompt names them:\n  "
                         + "\n  ".join(undeclared))


class TestTheDetectorDetects(unittest.TestCase):

    def _tmp(self):
        """Cleaned up. Flagged by the decision seat as hygiene — and hygiene
        here has teeth: a suite that leaves temp trees behind on a machine
        whose Desktop is a synced OneDrive tree is feeding the sync engine
        garbage, which is the failure family this project is migrating away
        from."""
        import shutil
        import tempfile
        d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        return d

    def test_a_reference_to_a_missing_file_is_found(self):
        d = self._tmp()
        (d / "ops").mkdir()
        (d / "ops" / "a.md").write_text("see `ops/NOPE.md`\n", encoding="utf-8")
        refs = [r for r in _REF.findall((d / "ops" / "a.md").read_text(
            encoding="utf-8")) if not (d / r).exists()]
        self.assertEqual(["ops/NOPE.md"], refs)

    def test_a_reference_that_resolves_is_not_flagged(self):
        d = self._tmp()
        (d / "ops").mkdir()
        (d / "ops" / "b.md").write_text("x\n", encoding="utf-8")
        (d / "ops" / "a.md").write_text("see `ops/b.md`\n", encoding="utf-8")
        refs = [r for r in _REF.findall((d / "ops" / "a.md").read_text(
            encoding="utf-8")) if not (d / r).exists()]
        self.assertEqual([], refs)


if __name__ == "__main__":
    unittest.main()
