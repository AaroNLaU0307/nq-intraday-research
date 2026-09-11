# -*- coding: utf-8 -*-
"""REVIEW.md -- the reviewer's only entry point inside a sealed bundle."""
from __future__ import annotations

OBLIGATION_TEXT = {
 "O1": "Frozen-grid conformance: does the implementation compute the sealed cells, "
       "per-cell draw counts and rounding FROM the sealed definitions, rather than from "
       "constants that merely agree with them today?",
 "O2": "The `infeasible_by_sample` rule -- mark, skip, report in full, continue -- at every "
       "grid shape: one marked cell among feasible ones, a mixed grid, and a grid where "
       "EVERY cell is marked.",
 "O3": "Can a marked cell acquire draw metadata, cell statistics, a feasibility verdict or a "
       "lifecycle evaluation -- anything that would let a consumer treat it as ruled? Absence "
       "must be represented as absence.",
 "O4": "Information flow and leakage across the calendar, session, supplement, label, feature "
       "and handoff boundaries. Can anything on the MC path observe a label, an outcome, a "
       "future bar, or a quantity derived from them? This is the obligation the seat exists "
       "for; the rest of the tree is worth less than this one.",
 "O5": "One lifecycle execution site: does that hold on this tree, and can any caller reach a "
       "second one?",
 "O6": "Determinism: same seed, same draws; draws stable across phases; the doubled run's "
       "draws a prefix-extension rather than a fresh enumeration.",
 "O7": "The K to 2K convergence witness: is the count the runner reports the count the frozen "
       "policy prescribes, and can a disagreement pass silently?",
 "O8": "The seal path: what is sealed, can a caller-supplied object reach it, and can a forged "
       "or hand-built input be sealed as though the governed path produced it?",
 "O9": "The registry boundary: can any path through the subsystem append an authorization row, "
       "a READY row, or any row a later gate would read as permission?",
 "O10": "Fail-closed before the first write: does a change to a production-semantic dependency "
        "after authorization either change the authorized identity or cause a refusal before "
        "anything is written? Silent tolerance is the failure mode.",
 "O11": "Aggregation: within-world reduction before anything combines across worlds, and no "
        "pooling where the design forbids it.",
 "O12": "The region map: boundary band, drift rule and cross-seed quantifiers against their "
        "authoritative definitions, and how each treats a marked cell.",
 "O13": "Input identity and binding: is the supplement chain's identity, provenance and "
        "binding checked rather than assumed, and is a mismatched or substituted input refused "
        "rather than absorbed?",
}


def render(profile: dict) -> str:
    L = []
    a = L.append
    a("# REVIEW -- %s" % profile["review_id"])
    a("")
    a("```")
    a("REVIEW_ID          = %s" % profile["review_id"])
    a("LINEAGE            = %s" % profile["lineage"])
    a("SUBSTANTIVE_ROUND  = %s   ROUND_CONSUMED_BEFORE_THIS = NO" % profile["substantive_round"])
    a("CONTRACT           = %s" % profile["contract_version"])
    a("PROFILE            = %s" % profile["profile_version"])
    a("BLINDNESS          = OUTCOME_BLIND + JUDGMENT_FIRST")
    a("SEAT               = one new fresh top-level independent session. Record whatever")
    a("                     runtime identity you can actually establish; do not assert a")
    a("                     product name you cannot. Branding is not independence evidence.")
    a("MUST_NOT_BE        = the builder (Claude Opus / Claude Code) session; any subagent")
    a("                     of it; any session that previously stopped on this node; the")
    a("                     session that reviewed the preceding issue lineage.")
    a("REAL_MC_AUTHORIZED = NO    REAL_MC_EXECUTED = NO")
    a("STATISTICAL_SIGNAL = NOT_TESTED    STATISTICAL_OUTCOME_EXPOSED = NO")
    a("```")
    a("")
    a("## 0. This bundle is the whole world")
    a("")
    a("Everything you may read is in this directory. There is no allowlist to consult, no")
    a("carrier to open, no repository to browse: **if it is not in this bundle, it is not")
    a("part of the review**, and reaching for it is a transport defect rather than")
    a("initiative. The execution guard enforces that rather than trusting it.")
    a("")
    a("Verify `MANIFEST.json` against the digest you were given out of band, then check")
    a("every payload row against the file it names. `MANIFEST.json` does not contain its")
    a("own hash -- a document that certifies itself certifies nothing.")
    a("")
    a("## 1. Judgment first, and why the order is load-bearing")
    a("")
    a("Form and record your findings **before** any builder or prior-review comparand")
    a("could reach you. Write `return/INITIAL_FINDINGS.md`, then `return/FREEZE.json`")
    a("recording `REVIEW_ID`, `MANIFEST_SHA256`, `INITIAL_FINDINGS_SHA256`, a timestamp and")
    a("your session identity. **After that freeze those bytes are immutable.** Any later")
    a("change goes in a separate artifact, never by editing the frozen one.")
    a("")
    a("**For this round no compare phase is planned.** `comparand/` is absent and stays")
    a("absent. Exact-tree comments and docstrings are NOT separately delivered comparands:")
    a("their correctness assertions are SELF_REPORTED and cannot alone support PASS or")
    a("HOLD in either direction.")
    a("")
    a("## 2. The obligations")
    a("")
    a("`OBLIGATION_MAP.json` binds each one to its authority, implementation locus, test or")
    a("probe, non-imported evidence and environment-input identity -- every cell resolving")
    a("to a pinned artifact in this bundle, or to NONE with a stated reason. **An")
    a("implementation comment is evidence about what the producer believes it built. It is")
    a("never the rule that same implementation is judged against.**")
    a("")
    for oid in sorted(OBLIGATION_TEXT, key=lambda k: int(k[1:])):
        a("**%s** -- %s" % (oid, OBLIGATION_TEXT[oid]))
        a("")
    a("Beyond these: a test that pins the implementation instead of the requirement, or")
    a("that would still pass on an implementation violating a sealed rule, is itself a")
    a("finding. The tests are IN the review, not evidence for it.")
    a("")
    a("## 3. Running the tests")
    a("")
    a("```")
    a("run_review.cmd                        # from the bundle root")
    a("```")
    a("")
    a("**That is the whole command, and it needs no Python on your PATH.** Two earlier")
    a("seats could not start the review at all -- one because `python` and `py` were not")
    a("on their PATH, one because the only invocable route to the host interpreter was a")
    a("Windows App Execution Alias. So this delivery carries its own runtime, which")
    a("travels BESIDE the bundle as a sibling directory. `run_review.cmd` resolves it by")
    a("one relative path, checks it against a digest fixed when this bundle was cut")
    a("(using `certutil`, so the first check on the runtime is made by something the")
    a("runtime did not provide), has the runtime verify its own files and pinned package")
    a("versions, and only then starts the review. **Every refusal it prints is a DELIVERY")
    a("failure to report, not something to work around** -- in particular, do not")
    a("substitute a different Python.")
    a("")
    a("That arms the execution guard and runs the selected tests from `tree/`. The guard")
    a("denies, in-process: reads and listings outside this bundle; link escape; subprocess")
    a("and shell; outbound network; and file-content reads under the two run directories")
    a("whose NAMES alone one test enumerates under a bounded Owner admission. **If")
    a("something you need is denied, that is a transport defect -- report it and STOP.**")
    a("Do not work around the guard; working around it is the failure it exists to catch.")
    a("")
    a("### 3.1 What is deliberately NOT executed, and why you are told")
    a("")
    a("`OBLIGATION_MAP.json` -> `withheld_execution` lists every test whose EXECUTION is")
    a("withheld, each with its reason. Two kinds:")
    a("")
    a("* **deselected node ids** -- collected, then skipped. Each reads a real historical")
    a("  artifact, which is an actual-artifact identity claim rather than an")
    a("  implementation one; the DAG binds those to the run-identity stage that follows")
    a("  this node.")
    a("* **not-collected files** -- pytest is told not to import them at all, because the")
    a("  import itself is what fails. One file is in this class and the reason is")
    a("  mechanical, not editorial: it reads a governed path that the frozen")
    a("  implementation declares non-overridable, so the read cannot be satisfied")
    a("  anywhere but on the Owner's machine.")
    a("")
    a("**Their SOURCE is in `tree/` and reading it is part of this review.** What is")
    a("withheld is execution, never text. `withheld_execution.measured_consequence`")
    a("records a coverage measurement comparing this bundle's selection against the full")
    a("local one: treat that number as a builder SELF-REPORT unless you re-derive it, and")
    a("treat statement coverage as what it is -- not property coverage. **If you judge")
    a("that a withheld test carried a property nothing here establishes, that is a")
    a("finding, and it is exactly the kind this section exists to make possible.**")
    a("")
    a("### 3.2 What is writable, and what appears while it runs")
    a("")
    a("**The sealed payload is READ-ONLY to review execution** and the guard enforces that,")
    a("not just the filesystem: a mutation anywhere in this bundle outside `return/` is")
    a("denied even if your account could perform it. `return/` is the one writable")
    a("surface -- it is where your findings, freeze and attestation go.")
    a("")
    a("The run creates `return/.scratch/` for ephemeral state (pytest's temp tree lives")
    a("there). **It is not yours and it is not evidence.** On a clean run the runner")
    a("removes it; if the run fails it is kept for diagnosis and labelled")
    a("`EPHEMERAL_DO_NOT_READ_AS_EVIDENCE.txt`. Your returns are the three named files")
    a("below, which live in `return/` itself and never inside `.scratch/`.")
    a("")
    a("`return/GUARD_REPORT.json` is written by the runner, not by you. It records the")
    a("boundary's refusals and the scratch and writable roots it used.")
    a("")
    a("## 4. Output")
    a("")
    a("`return/INITIAL_FINDINGS.md` must cover EVERY obligation with: `DISPOSITION`,")
    a("`SUPPORTING_ARGUMENT`, `EXAMINED_LOCUS`, `EVIDENCE_CLASS`, `UNRESOLVED_LIMITATION`,")
    a("and where BLOCKING also `THREAT` (one of T1-T6) and `FAILURE_PATH` (concrete input")
    a("or state, and the wrong output or refusal that follows). End with")
    a("`PROPOSED_OVERALL_VERDICT`.")
    a("")
    a("```")
    a("PASS                 no BLOCKING finding")
    a("PASS_WITH_BACKLOG    no BLOCKING finding; one or more NON-BLOCKING rows")
    a("HOLD                 at least one BLOCKING finding")
    a("```")
    a("")
    a("There is no fourth value. A finding that cannot name a threat is NON-BLOCKING.")
    a("Then `return/ATTESTATION.md`, stating independence per dimension (context,")
    a("authorship, model diversity, empirical) and declaring anything you executed but did")
    a("not inspect.")
    a("")
    a("**A STOP is not a HOLD and costs no review round.** Reporting a defective package is")
    a("worth more than a verdict formed on one, and this node has already proved that four")
    a("times.")
    a("")
    a("## 5. What a PASS does")
    a("")
    a("It satisfies N14 and nothing else. It authorizes no run, appends no READY row,")
    a("releases no data, and does not move `REAL_MC_AUTHORIZED` off `NO`.")
    return "\n".join(L) + "\n"
