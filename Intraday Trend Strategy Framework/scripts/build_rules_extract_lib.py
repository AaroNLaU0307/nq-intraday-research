# -*- coding: utf-8 -*-
"""Generate authority/RULES_EXTRACT.md for a sealed code-review bundle.

FIELD SELECTION, NOT ROW COPYING. The previous authority artifact quoted whole
source rows for provenance and thereby handed a claim-blind seat prior actors'
retrospective judgements of the code under review. The rule that broke: an
authority surface may carry a PROSPECTIVE RULE and may not carry anyone's
RETROSPECTIVE JUDGEMENT of the implementation being judged. An Owner ruling is
not contaminated merely by being the Owner's -- what matters is whether its
function is to DEFINE or to ASSESS.

So: from the ratified design only ITEM_ID / TIER / RULING / POST_FREEZE_DEFINITION;
from the Owner ruling only the verdict cell, which defines scope. Exclusions are
COUNTED, never restated. The generator refuses rather than emit if a kept field
matches an outcome pattern, if a RULING is missing, or if the verdict cell
carries retrospective vocabulary.
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

KEEP = ("ITEM_ID", "TIER", "RULING", "POST_FREEZE_DEFINITION")
RETRO_VOCAB = ("PASS", "never wrong", "CLOSED", "passed", "accepted",
               "no production-logic change", "acceptance check")


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def render(repo: Path, profile: dict) -> bytes:
    sys.path.insert(0, str(repo))
    from tests.test_review_artifacts_are_outcome_clean import OUTCOME_RESTATEMENTS

    def clean(s: str) -> bool:
        return not [l for l, pat, _ in OUTCOME_RESTATEMENTS if pat.search(s)]

    rat = repo / "ops" / "outcome_quarantine" / "RULING_PROPOSAL_ND2_ND3_FABLE_2026-08-24.md"
    lines = rat.read_text(encoding="utf-8").splitlines()
    starts = {}
    for i, ln in enumerate(lines):
        m = re.match(r"^ITEM_ID=(M(?:[6-9]|10))$", ln.strip())
        if m:
            starts[m.group(1)] = i
    order = sorted(starts, key=lambda k: starts[k])
    if len(order) != 5:
        raise SystemExit("RULES_EXTRACT refused: expected M6..M10, found %s" % order)
    blocks, spans, excluded_fields = {}, {}, 0
    for n, k in enumerate(order):
        a = starts[k]
        b = starts[order[n + 1]] if n + 1 < len(order) else a + 12
        kept = []
        for i in range(a, b):
            key = lines[i].split("=", 1)[0]
            if key in KEEP:
                if not clean(lines[i]):
                    raise SystemExit("RULES_EXTRACT refused: outcome pattern inside a "
                                     "kept normative field at line %d" % (i + 1))
                kept.append(lines[i])
            elif "=" in lines[i]:
                excluded_fields += 1
        if not any(x.startswith("RULING=") for x in kept):
            raise SystemExit("RULES_EXTRACT refused: %s has no RULING field" % k)
        blocks[k], spans[k] = kept, (a + 1, b)

    chain = [l for l in lines[424:430] if "M6→M7→M8→M9" in l]
    if not chain or not clean(chain[0]):
        raise SystemExit("RULES_EXTRACT refused: the dependency chain line is unavailable")

    dec = repo / "ops" / "DECISIONS.md"
    rows = [l for l in dec.read_text(encoding="utf-8").splitlines()
            if l.startswith("| DEC-N11-B25-1 |")]
    if len(rows) != 1:
        raise SystemExit("RULES_EXTRACT refused: the Owner ruling row is not unique")
    cells = [c.strip() for c in rows[0].split(" | ")]
    verdict, consequence = cells[4], cells[6]
    if not clean(verdict) or any(t in verdict for t in RETRO_VOCAB):
        raise SystemExit("RULES_EXTRACT refused: the Owner verdict cell mixes rule "
                         "with retrospective judgement; it cannot be field-selected")
    excluded = {
        "PRIOR_VERDICT": 1, "PRIOR_ACCEPTANCE": 1,
        "PRIOR_CLOSURE": consequence.count("CLOSED") + 1,
        "PRIOR_TEST_RESULT": len(re.findall(r"\d+ passed", consequence)) + 2,
        "IMPLEMENTATION_CORRECTNESS": 2,
        "RATIFIED_NON_NORMATIVE_FIELDS": excluded_fields,
    }

    L = ["# NORMATIVE RULES -- N14 code review", "",
         "```", "RECORD_TYPE=CLAIM_BLIND_NORMATIVE_RULES_EXTRACT",
         "CONTENT=prospective rules, definitions, thresholds, scopes, quantifiers and",
         "        precedence ONLY. Field-selected from the sources, never row-copied.",
         "EXCLUDED_BY_CONSTRUCTION=any prior verdict, acceptance judgement, closure claim,",
         "        test result, or retrospective assessment of the implementation under",
         "        review. Excluded material is COUNTED below and reproduced nowhere.",
         "```", "",
         "Nothing here says, or implies, anything about whether the implementation",
         "satisfies these rules. That is the question you are being asked; this file only",
         "supplies the rules.", "",
         "## 1. Frozen convergence policy (O5-O11)", "",
         "```",
         "SOURCE_ID      = MC-METHOD-SPEC-S5",
         "SOURCE_PATH    = authority/MC_METHOD_SPEC.md (also tree/MC_METHOD_SPEC.md)",
         "SOURCE_SHA256  = " + _sha(repo / "MC_METHOD_SPEC.md"),
         "SOURCE_RANGE   = section 5",
         "AUTHORITY_TYPE = FROZEN METHODOLOGY SPECIFICATION",
         "PROVENANCE     = the runner seals a method_spec_sha256 of this exact file into",
         "                 the run identity, so its standing is machinery, not a comment;",
         "                 verifiable inside the bundle.",
         "```", "",
         "Read it there in full. Section 5 fixes the exhaustive enumeration of inner",
         "random sources and the convergence rule in five clauses, under a heading",
         "stating that what is frozen is the RULE and not the counts.", "",
         "## 2. Ratified boundary / drift / quantifier design (O12)", "",
         "```",
         "SOURCE_ID      = ND2-M6..M10",
         "SOURCE_ARTIFACT= ops/outcome_quarantine/RULING_PROPOSAL_ND2_ND3_FABLE_2026-08-24.md **OFF-LIMITS (outcome-carrying, do not open)**",
         "                 Quoted here so it is never needed.",
         "SOURCE_SHA256  = " + _sha(rat),
         "SOURCE_RANGE   = " + ", ".join("%s lines %d-%d" % (k, *spans[k]) for k in order),
         "AUTHORITY_TYPE = RATIFIED DESIGN (RATIFIED_UNCHANGED 2026-08-24), prospective",
         "FIELDS_INCLUDED= " + " / ".join(KEEP) + " only",
         "```", ""]
    for k in order:
        L += ["```"] + blocks[k] + ["```", ""]
    L += ["Dependency, quoted from the same ratification:", "", "```", chain[0], "```", "",
          "## 3. Owner ruling fixing the scope the band applies at (O12)", "",
          "```",
          "SOURCE_ID      = DEC-N11-B25-1",
          "SOURCE_RANGE   = verdict cell ONLY; the consequence cell of the same row and",
          "                 the whole of the following row are excluded, their function",
          "                 being retrospective rather than rule-defining",
          "AUTHORITY_TYPE = OWNER RULING, rule-defining (interpretation and scope)",
          "```", "", "```", verdict, "```", "",
          "## 4. Controlling precedence -- quoted, not decided here", "", "```",
          "M8    defines the boundary-band equivalence test and its width.",
          "B-25  is later and fixes the SCOPE at which that test is applied. By its own",
          "      words it \"introduces no new tolerance\": it changes neither the band nor",
          "      its width, only which statistics the band is applied to.",
          "M9    transplants clause (c) to the cell layer; its tolerance is clause (c)'s,",
          "      taken from MC_METHOD_SPEC section 5.",
          "M10   fixes the quantifiers.",
          "Where the sealed preregistration or MC_METHOD_SPEC speak directly they outrank",
          "this extract; both are in the bundle in full.",
          "```", "",
          "## 5. What was excluded -- counted, not reproduced", "", "```"]
    for k, v in excluded.items():
        L.append("%-34s = %d" % (k + "_EXCLUDED", v))
    L += ["",
          "None of it is a rule. All of it is some prior actor's assessment of the",
          "implementation you are reviewing, which is the one thing a claim-blind surface",
          "may not carry.", "```", ""]
    return ("\n".join(L) + "\n").encode("utf-8")
