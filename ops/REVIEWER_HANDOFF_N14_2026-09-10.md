# REVIEWER HANDOFF -- review `N14-EXACT-TREE-002`

```
RECORD_TYPE=REVIEWER_FACING_HANDOFF
REVIEW_ID=N14-EXACT-TREE-002
DELIVERY_STATUS=ISSUED
NODE=N14   ISSUE_LINEAGE=N14   REVIEW_ROUND=1 of at most 2 (UNCONSUMED)
REVIEWED_SET_UNCHANGED_SINCE=b2e7a3c9bdc15e085ba80c2ba9194116c6cb811d
IMPLEMENTATION_REVIEW_TARGET=b2e7a3c9bdc15e085ba80c2ba9194116c6cb811d
IMPLEMENTATION_REVIEW_TREE=84f9388d53557685e641929a9b5fb6e85a575e4e
FOR=ONE NEW fresh top-level GPT-6 Astra session, claim-blind
CREATED=2026-09-10
```

**This file is part of the reviewer's authorized read surface, and that is the whole
point of it.** An earlier attempt at this node was opened from a dispatcher-side file
that declared itself outside the read set and then carried the text the reviewer had to
receive. That put the seat in a position it could not obey -- it had to be handed the
file, and reading the file broke the transport it was being asked to follow. It stopped,
correctly, before inspecting any code. This file exists so that everything the reviewer
is handed is something the reviewer is allowed to read.

It carries no dispatcher commentary, no builder opinion about the code, no prior verdict,
no Owner decision and no outcome. If you are the reviewer and you find any of those here,
that is a transport defect worth reporting.

## The paste block

Everything between the two markers is what the Owner pastes into the new session, and
nothing else is. Compare what you were given against this block byte-for-byte; a
mismatch means something outside the governed transport reached you.

<!-- BEGIN PASTE BLOCK -->

```
You are the independent reviewer for N14, a node of the ITSF canonical DAG.
N14's whole content is an exact-tree review of the Monte Carlo implementation,
and your verdict is the node's completion condition.

REVIEW_ID     = N14-EXACT-TREE-002
ISSUE_LINEAGE = N14
REVIEW_ROUND  = 1 of at most 2 (UNCONSUMED)
ROLE          = independent reviewer; ONE NEW fresh top-level GPT-6 Astra session
BLINDNESS     = CLAIM_BLIND
MUST_NOT_BE   = the builder (Claude Opus / Claude Code) session; any subagent of it;
                the session that stopped on this node's earlier transport defect;
                the Astra session that reviewed the preceding issue lineage on part
                of this subsystem

Repository:
C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework

IMPLEMENTATION TARGET = b2e7a3c9bdc15e085ba80c2ba9194116c6cb811d
TREE                  = 84f9388d53557685e641929a9b5fb6e85a575e4e
FREEZE PIN            = b2e7a3c9bdc15e085ba80c2ba9194116c6cb811d
  Two quantities, not one. The target is the code; the pin covers the whole
  reference set. They are equal in this package because the newest change to any
  allowlisted path IS the implementation commit -- a coincidence. Verify both.

READ THESE TWO FILES FROM DISK, IN THIS ORDER, BEFORE ANYTHING ELSE.
Chat-carried bytes are never a source of truth in this project.

  1. ops/OFF_LIMITS_N14_EXACT_TREE_2026-09-10.md      (in the repository)
     sha256 c50d32e9bf08d7b1c3ee4bb6920d9c0ff3ee2f86e82429fcc67a0951ed9c6b39
  2. C:\Users\Aaron\quant-data\review\itsf-n14-exact-tree-2026-09-10\BRIEF.md
     sha256 000aee6b2938e4ed8c279c98eea30a3485c72f7859781a876f0ff3a0b836dfb9

RECOMPUTE BOTH HASHES FIRST. A mismatch is STOP, not a warning. Then recompute
every hash in the carrier's section 3 -- 93 files -- before any substantive work.

YOUR AUTHORIZED READ SURFACE is exactly: the 93 files listed in the carrier's
section 3, plus the three transport documents that section authorizes by name --
the carrier itself, the brief, and ops/REVIEWER_HANDOFF_N14_2026-09-10.md,
which is the file this text was pasted from. Open it and confirm this block is
byte-identical to the block it marks. NOTHING ELSE IS AUTHORIZED.

  - No repository-wide grep, no recursive directory listing, no broad symbol search.
  - No skill, checklist, playbook, template, tool or remembered procedure from
    outside this package. It is self-contained by construction: the carrier's
    section 2 is every command and the brief's section 3 is every obligation.
    Opening an outside procedure is the same contamination as opening a forbidden
    file.
  - Do not open ops/DECISIONS.md, ops/RESEARCH_STATE.md, ops/BACKLOG.md,
    qros-state.yaml, anything under ops/outcome_quarantine/, either exposure
    ledger, or any earlier review package. The carrier's section 1 is the
    exhaustive forbidden set and says what each would cost.
  - Read-only: commit nothing, append to no ledger, write no repository file.

ALLOWED COMMANDS are exactly those in the carrier's section 2: four
`python -m pytest -q ...` invocations over the MC test surface, and `git log`
range checks against the freeze pin above. Nothing else.

PROHIBITED: scripts/run_governed.cmd; any real Monte Carlo run; the full test
suite; any write, commit, push or ledger append. REAL_MC_AUTHORIZED = NO, and
nothing in this package authorizes a run.

STOP -- returning no substantive verdict -- if any hash mismatches, if an
obligation needs a path outside the surface, if you have read anything outside
it, if you need an outside procedure, or if this pasted text is not byte-identical
to its source block. A STOP is not a HOLD and costs no review round; reporting one
is worth more than a verdict formed on a surface you should not have seen.

RETURN exactly one verdict -- PASS, PASS_WITH_BACKLOG, or HOLD -- with the findings
table the brief's section 5 specifies. Every BLOCKING finding names exactly one of
the six threats T1-T6, exactly one evidence class (REPRODUCED / REASONED /
SELF-REPORTED), and a concrete failure path. Then the attestation, using
ops/templates/ATTESTATION_HEADER_TEMPLATE.md. Hand it back to the Owner.

A PASS SATISFIES N14 AND NOTHING ELSE. It authorizes no run, appends no READY row,
releases no data, and does not move REAL_MC_AUTHORIZED off NO.
```

<!-- END PASTE BLOCK -->

## The two documents the block names

| sha256 | bytes | path |
|---|---|---|
| `c50d32e9bf08d7b1c3ee4bb6920d9c0ff3ee2f86e82429fcc67a0951ed9c6b39` | 27093 | `ops/OFF_LIMITS_N14_EXACT_TREE_2026-09-10.md` |
| `000aee6b2938e4ed8c279c98eea30a3485c72f7859781a876f0ff3a0b836dfb9` | 15647 | `C:\Users\Aaron\quant-data\review\itsf-n14-exact-tree-2026-09-10\BRIEF.md` |

Recompute both. A mismatch is STOP.

The carrier is also the off-limits list, and `ops/OUTCOME_CARRYING_ARTIFACTS.json` is on
the read allowlist so the forbidden set can be checked against the machine-readable
register rather than taken on trust. Everything that register names is **OFF-LIMITS
(outcome-carrying)** and must not be opened.

## Why the hashes point one way only

The carrier states the brief's hash; this handoff states the carrier's and the brief's.
Nothing states its own, and nothing certifies its own certifier: two documents each
hashing the other is a loop with no fixed point, not a chain. This file is pinned by
content hash in `ops/ARTIFACTS_UNDER_REVIEW.json` and is excluded from pin derivation,
which is what lets it state the freeze pin without being one commit stale.

## What this handoff does not do

It dispatches nothing. The Owner is the external handoff point: the builder wrote the
code under review and may neither dispatch nor perform the review.
