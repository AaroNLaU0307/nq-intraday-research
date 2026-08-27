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
  CITED_BUT_NEVER_EXISTED  measured: never added and never deleted anywhere
                           in git history, and absent from the worktree. This
                           is the R2-ruling shape and is recorded as an OPEN
                           finding, not as an accepted state.

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

_REF = re.compile(r"`?(ops/[A-Za-z0-9_./-]+\.(?:md|json|py))`?")

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
    "ops/MC_RUN_REGISTRY.md": "CITED_BUT_NEVER_EXISTED",
    "ops/STRATEGY_COUNCIL_ROUND4_LOCK.md": "CITED_BUT_NEVER_EXISTED",
    "ops/SUPPLEMENT_LEDGER.md": "CITED_BUT_NEVER_EXISTED",
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
                         "these are recorded as dangling but now resolve; "
                         "delete the entries:\n  " + "\n  ".join(fixed))


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
        identical on disk. Keying it off the citing document's name was
        tried and rejected: `DECISION_PACKET_N00_AND_ND1.md` cites
        `SUPPLEMENT_LEDGER.md`, so a PACKET-means-proposal rule would
        silently reclassify a real missing record as a legitimate proposal.
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

    def test_the_never_existed_ones_are_still_absent_from_history(self):
        """MEASURED, and re-measured every run: `git log --diff-filter=AD`
        over all refs returns nothing for these paths, so they were never
        added and never deleted — they were cited into existence."""
        import subprocess
        appeared = []
        for ref, kind in sorted(_KNOWN.items()):
            if kind != "CITED_BUT_NEVER_EXISTED":
                continue
            out = subprocess.run(
                ["git", "-C", str(REPO), "log", "--all", "--oneline",
                 "--diff-filter=AD", "--", ref],
                capture_output=True, text=True, errors="replace").stdout.strip()
            if out:
                appeared.append(f"{ref}: {out.splitlines()[0]}")
        self.assertEqual([], appeared,
                         "these are recorded as never having existed, but git "
                         "history now shows them added or deleted; the "
                         "classification needs revisiting:\n  "
                         + "\n  ".join(appeared))


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
        to avoid."""
        listed = {Path(p).name for p in self._paths()}
        on_disk = {p.name for p in QUARANTINE.glob("*.md")}
        undeclared = sorted(on_disk - listed)
        self.assertEqual([], undeclared,
                         "these sit in ops/outcome_quarantine/ but are not in "
                         "carries_outcome, so no prompt names them:\n  "
                         + "\n  ".join(undeclared))


class TestTheDetectorDetects(unittest.TestCase):

    def test_a_reference_to_a_missing_file_is_found(self):
        import tempfile
        d = Path(tempfile.mkdtemp())
        (d / "ops").mkdir()
        (d / "ops" / "a.md").write_text("see `ops/NOPE.md`\n", encoding="utf-8")
        refs = [r for r in _REF.findall((d / "ops" / "a.md").read_text(
            encoding="utf-8")) if not (d / r).exists()]
        self.assertEqual(["ops/NOPE.md"], refs)

    def test_a_reference_that_resolves_is_not_flagged(self):
        import tempfile
        d = Path(tempfile.mkdtemp())
        (d / "ops").mkdir()
        (d / "ops" / "b.md").write_text("x\n", encoding="utf-8")
        (d / "ops" / "a.md").write_text("see `ops/b.md`\n", encoding="utf-8")
        refs = [r for r in _REF.findall((d / "ops" / "a.md").read_text(
            encoding="utf-8")) if not (d / r).exists()]
        self.assertEqual([], refs)


if __name__ == "__main__":
    unittest.main()
