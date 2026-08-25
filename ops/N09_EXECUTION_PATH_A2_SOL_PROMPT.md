```ini
RECOMMENDED_MODEL=Codex GPT-5.6 Sol
EFFORT_INTENT=HIGH
RECOMMENDED_EFFORT=High
EXECUTION_MODE=STANDARD
ROLE=A2 pre-build design challenger — challenge the design, do not build it
WINDOW=NEW_TOP_LEVEL_SESSION
MUST_NOT_BE=the Opus 5 builder session that authored the design and the code;
            any subagent of it; the Sol session that ratified
            MC-REG-COLLISION-001 (that one authored C2, which §5 of this
            design is downstream of)
LANE=FULL
OUTCOME_EXPOSED=NONE
PREREG_SEALED=YES
SUBAGENT_OR_WORKFLOW_BUDGET=0 — read-only
WHY_THIS_MODEL=QROS FULL routing puts a fresh-Sol A2 design challenge before
            the build on evidence-critical production-runner work. This is
            the only remaining block that reads real Development data,
            creates directories under quant-data, and writes sealed bytes.
```

# A2 — challenge the N09 execution-path design before it is built

## Transport

Recompute and match before any work. On mismatch, truncation or absence:
**STOP and report.**

| SHA256 | bytes | path |
|---|---|---|
| `C44162D7F45AE45A0AA9F5AF1533DDD6CEBCD2BCD7810F26B9C528D46B386808` | 7477 | `ops/N09_EXECUTION_PATH_DESIGN.md` |
| `FDB6F99A58180E1439749F6A1E2B9343FB83B7E59E42461B28DDFFD56C7F0520` | 9185 | `src/itsf/mc/registry_boundary.py` |
| `3CB698AEF52DCC14EE0987E585EE5B46705A3046E7E53EA42D3DB69E001CF746` | 45975 | `src/itsf/mc/supplement_runner.py` |
| `4AC9A2D62E05BDA7DFBE3EC48B3883222D62F8A9103DDE0575903207E3827AE8` | 22862 | `src/itsf/mc/supplement_production.py` |
| `774CD76F927EFFA4560E699F4243269D833B34F09DBD8FFF800044FE39D9B652` | 37130 | `src/itsf/mc/supplement_authority.py` |
| `069659902E50ABC372CD271E6F7C5D53E123DACB4C8E18AA973798674D479A07` | 20018 | `src/itsf/mc/day_strata_supplement.py` |

Repo: `C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework`

**On HEAD — not a matched field.** Pinning HEAD is self-defeating: committing
the prompt changes it. What is declared instead:

```
REVIEW_ID                    = N09-EXECUTION-PATH-A2
REVIEWED_SET_UNCHANGED_SINCE = d4d7c6ead513f6526f7237bfca3f81ca4fb92d14
VERIFY = git log d4d7c6e..HEAD -- <the six paths above>   ->  must be EMPTY
```

An empty result proves no commit since that point touched a reviewed byte.
Re-run it rather than comparing HEADs.

## What is being asked

`ops/N09_EXECUTION_PATH_DESIGN.md` is the design. **Nothing is implemented.**
Challenge it before it is built, in the shape:

```
ITEM_ID=N09-EXECUTION-PATH-A2
VERDICT=PROCEED | PROCEED_WITH_MODIFICATIONS | REDESIGN
MODIFICATIONS=<exact and quotable>
UNRESOLVED_FOR_AARON=<what the builder must NOT decide alone>
```

## The four questions the design itself raises

The design names them; it does not answer them, and the builder must not.

1. **Q3 — the two-snapshot rule (§5).** The C2 boundary requires one read per
   result, but the execution path APPENDS P3 mid-run, so the A_PRECHECK
   snapshot goes stale by the run's own hand. The design proposes exactly
   two snapshots with the invariant that the second differs from the first by
   exactly this run's P3 row, and that any other difference is a post-start
   (F2) failure with exposure consumed and the id burned. This rule is the
   builder's invention, not ratified text. Is it right? Is two the right
   number? Is "differs by exactly one predictable row" mechanically
   checkable the way the design claims?

2. **Q1/Q2 — who appends P3, and who appends the failure events?** Global
   boundary 4 says the registry is append-only and *only the main agent
   writes*. If the orchestrator appends its own P3, production code writes
   to the registry. But `scripts/s0_real_run.py` set the opposite precedent
   on the real S0 run — it appended its own `RUN_STARTED`. Both readings
   hold. Say which governs, or refer it to Aaron explicitly.

3. **Q4 — the five C_BUILD stubs.** They refuse unconditionally today
   (`unreachable in this build`). Making them real converts an unconditional
   refusal into a conditional one. The design proposes landing them in the
   same change as the orchestrator so they never sit implemented-but-
   unreviewed. Is that sufficient, or should each stub's replacement carry
   its own red proof before the orchestrator exists at all?

4. **§4 — the `day_rows` producer.** The design's position is that it must
   join two ALREADY-RULED sources (`s0/dataset.py` for the vol terciles,
   `s0/context.py` for the event strata) and carry no stratification logic of
   its own. Verify that both are genuinely ruled and genuinely reusable per
   day over the sealed universe. If either is not — if the producer would
   have to re-derive or re-interpret anything — that is a methodological
   decision wearing engineering clothes, and it stops here.

## What to attack beyond those

The builder surveyed rather than remembered, and one earlier suspicion was
withdrawn on evidence: a suspected circular dependency (supplement needs
`PreparedMCInput` → `real_input` → the MC-run authorization gate → which
comes after the supplement) does NOT exist, because
`consumer.prepare_mc_input` carries no MC gate. Check that withdrawal — if
the circularity is real after all, the design's call chain is wrong at its
root.

Also worth attacking: the design asserts the execution path must NOT route
through `real_input.prepare_real_mc_input`. If that is wrong, the supplement
would inherit the MC-run gate and deadlock; if it is right, the two paths
duplicate bundle loading, and the design does not discuss whether that second
read of the sealed bundle matters. The sealed bundle is immutable (14 files,
run == archive), so the C2 mutable-file hazard should not apply — confirm or
refute.

## Standing prohibitions — in force

- **Read-only. Do not build any part of this.** A challenge is prose plus
  exact file-and-symbol references.
- No real Development data read. No supplement / MC / S0 / strategy
  execution. No directory creation under `C:\Users\Aaron\quant-data\` — both
  `supplements\` subtrees must stay non-existent (verified absent at this
  writing).
- No write probes. No registry appends. No exposure events. No READY or
  authorization events. No push, tag, or amend.
- Do not change samples, labels, NA policy, costs, Primary, Oracle,
  feasibility or run definitions.
- Do not fill the P2 template's placeholders. Do not issue any authorization.
- Do not decide Stage I vs discretionary Tier-1. Do not infer LANE or STAGE.

## Provenance

This challenge is a **delegated** act under Aaron's standing routing. Anything
citing its outcome must carry `DELEGATED=YES` and must not be written as
Aaron's own judgement. A PROCEED verdict authorizes a BUILD, never a RUN:
N09's execution still requires Aaron's P2 sentence against a stable HEAD.
