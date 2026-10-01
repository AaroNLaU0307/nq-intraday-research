# MC-REG-COLLISION-001 — Fable ruling proposal

```
PROPOSAL_ID=RULING_PROPOSAL_MC_REG_COLLISION_FABLE_V1
PROPOSAL_DATE=2026-08-25
DECIDER_SEAT=Fable 5 (fresh top-level session, adversarial auditor; Aaron's
             standing instruction routes decisions that would otherwise need
             him to this seat; NOT the builder session and not its subagent)
RECORD=ops/DECISION_MC_REGISTRY_COLLISION.md
RECORD_SHA256_RECOMPUTED=3D9A4E385FF88D18914C92C4942291813370955C4E077AC46FAAD89AA7FD5295 (10194 bytes, match)
TRANSPORT_VERIFIED=all five files match the transport table byte-for-byte:
  817419CD… src/itsf/mc/mc_contract.py (10894)
  B56D4205… src/itsf/mc/mc_registry.py (23458)
  9BE097BC… tests/test_mc_registry_contract.py (12736)
  73E837FA… tests/test_mc_registry_parser.py (25548)
HEAD_AT_PROPOSAL=0991d6f — NOT the 13fb936 the prompt records. The five
  files are no longer uncommitted working-tree state; they are committed,
  byte-identical (worktree clean). Non-material: the transport rule keys on
  bytes, and the bytes match.
STATUS=PROPOSAL_ONLY — awaits fresh Sol ratification, then Aaron. Releases
  no gate, authorizes no run, amends nothing by itself.
REPO_WRITES=1 (this file only; nothing ratified edited, no appends,
  no commits, workflows used 0/0)
```

## What was independently verified, not taken from the record

- The reproduction: `tests/test_mc_registry_contract.py::
  test_a_ratified_mc_row_breaks_supplement_resolution` exists and pins
  `token_deferred_to_nd3` + empty chains for both colliding tokens.
- Prefix ownership is code, not docstring: `mc_registry.is_mc_row` is
  `row.event.startswith("MC_")` (mc_registry.py:138), `_classify` refuses
  any `MC_`-prefixed token outside the ratified sixteen
  (`mc_unknown_event_token`, mc_registry.py:231), and `_malformed_mc_line`
  closes the WHOLE prefix at stage 1 — wider than the supplement side's
  `_TOKEN_SCAN_RE`, which scans only `SUPPLEMENT_*|MC_RUN_*`
  (supplement_registry.py:268).
- The by-name guard's ratified source, §D.3.4 of
  `ops/DECISION_PACKET_N00_AND_ND1.md`, is EXPLICITLY temporal:
  `REASON=其生命周期定义…尚不完整`, `CONSEQUENCE=在 N-D3 裁定前…`
  ("before the N-D3 ruling"). The N-D3 ruling (G1–G8, ratified 2026-08-24)
  supplied exactly the missing lifecycle definitions for
  `MC_RUN_AUTHORIZED` / `MC_RUN_STARTED`.
- G8's ratified proposal text carries its own falsifier clause:
  «若被裁反=放宽 allowlist → 授权对象与复审对象出现差集»
  (RULING_PROPOSAL_ND2_ND3_FABLE_2026-08-24.md, ITEM G8).
- `consumer.authorize_real_mc` raises UNCONDITIONALLY today
  (consumer.py:3181); so does `day_strata_supplement.authorize_supplement`.
  Among the four "production paths" the record names, only
  `supplement_runner` (via `RESOLVER_SEAM`, supplement_runner.py:911)
  actually calls `resolve_supplement_chains`; `real_input`, `consumer` and
  `day_strata_supplement` read the registry text and refuse
  deterministically without resolving.
- Global sequence coupling: enforced from both sides
  (`supplement_registry._check_global_sequence`:1181 counts foreign
  numbered rows into "highest"; `mc_registry._check_global_sequence`:419
  demands next-value for MC rows over the same file-wide namespace).

---

## ITEM

```
ITEM_ID=MC-REG-COLLISION-001
RULING=R2 — discharge the expired deferral guard for MC_RUN_AUTHORIZED and
       MC_RUN_STARTED only, conditioned as below. R1 rejected. R3 stays
       rejected. R4 (sequencing) examined and rejected.
```

### Why R2 survives the four attacks

**Attack 1 — is the guard actually expired?** Yes, and by ratified text,
not by the builder's paraphrase. §D.3.4's deferral names its own discharge
condition ("before the N-D3 ruling") and its own reason (lifecycle
definitions incomplete). Both are now false for exactly the two tokens R2
discharges. The same test shows the discharge is NOT total:
`SUPPLEMENT_CONSUMED_BY_GRID_REPLAY` was deferred for a reason (GRID-replay
coupling) the N-D3 ruling did NOT rule — its deferral stands, and R2 as
conditioned keeps it refused by name. `MC_RUN_SEALED` / `MC_RUN_FAILED`
were anticipated but never created (record §5, verified against
`mc_contract.EVENTS`); they stay on the by-name list AND are refused by
prefix ownership. So this is not a loosening dressed as a cleanup: every
string the old guard refused remains refused somewhere mechanical, and the
two that stop being refused by the supplement grammar acquire a STRICTER
owner — the old guard refused them unconditionally; `mc_registry` refuses
them unless they are fully valid governance rows (rebuilt authorization
sentence, Aaron-only actor, 40-hex commit, next-value sequence, legal
transitions, chain starting at MC_PACKET_DRAFTED).

**Attack 2 — does prefix ownership replace what is lost?** Checked against
code, and one genuine class of string survives both grammars: case and
prefix variants (`mc_run_authorized`, `Mc_Run_Authorized`, `XMC_RUN_…`)
are invisible to `is_mc_row` (case-sensitive `startswith`), to
`_MC_TOKEN_SCAN_RE` (uppercase-only), and to the supplement grammar. BUT
the old by-name guard let every one of those through too
(`token in ND3_DEFERRED_TOKENS` is exact-match) — this is a PRE-EXISTING
hole of the shared-file design, neither created nor widened by R2, and
inert to every machine reader (`find_live_mc_authorization` only sees
`MC_`-prefixed rows; `authorize_real_mc`'s marker is exact-case). Recorded
here so nobody later mistakes it for an R2 regression; no string was found
that the old guard refused and the conditioned R2 regime admits.

**Attack 3 — the coverage window, and a correction to the record.** The
window is real but the record misdescribes it twice. (a) §4's example
token is wrong: under the R2 shape the record itself specifies (by-name
list narrowing 5→3), `MC_RUN_SEALED` REMAINS refused by name — §4
contradicts §5. The window's actual membership is exactly
{`MC_RUN_AUTHORIZED`, `MC_RUN_STARTED`} rows, valid or forged — the
authorization-bearing tokens, i.e. the worst two. (b) The window is NOT an
R2-specific weakness: under R1 a separate `ops/MC_RUN_REGISTRY.md` is
parsed by NOBODY until N13 wires it, so a stray or forged row there is
equally unrefused — the window is a property of wiring order, not of file
choice, which is why the ordering CONDITION and not the file split is the
operative safeguard. Severity is bounded either way:
`authorize_real_mc` raises unconditionally until N13, so no production
path can act on a forged MC row during any window; the residual harm is
human readers and delayed wedge detection. The record's proposed ordering
condition closes the first window but is phrased as a call-site INVENTORY
("every path that today resolves supplement chains") — an inventory
quantified over today's paths silently excludes paths N13 creates.
Condition C2 below restates it as an invariant pinned by a test.

**Attack 4 — is R1 cheaper than the record admits?** No — it is more
expensive, on grounds the record undersells. (a) R1's required amendment
is the exact failure mode G8's own ratified falsifier clause names:
widening the dirty allowlist creates a diff between the authorized object
and the reviewed object, on the one path where a dirty-worktree mistake
ends a run. R2 amends no ruled decision — it retires a guard whose ratified
discharge condition has fired. (b) The §2.2 measurement read the other way,
as instructed: the coupling is an argument FOR one file, not against it.
The global sequence's job is to make the event chain countable — one
mechanically-checkable total order that includes the CROSS-lifecycle
ordering (supplement authorized and verified BEFORE the MC run that
consumes it). Split the file and that ordering degrades to self-reported
UTC prose, in a repo whose entire discipline is evidence over self-report.
The wedge hazard fires only on an INVALID append, which both grammars now
refuse from both sides — a wedge that fires is fail-closed working, not a
cost of cohabitation. (c) R1's remaining virtue, the misplacement tripwire,
guards 4 of 16 MC tokens: a misplaced `MC_BRANCH_SEALED` in
TRIAL_REGISTRY.md under R1 is skipped silently by the supplement grammar
(measured, record §2 table). A tripwire that misses 12/16 tokens does not
outweigh (a) and (b).

**R4 — the fourth reading (sequencing), constructed and rejected.** Nothing
in G1/G8 or the ruling text requires MC rows and OPEN supplement chains to
coexist; one can ask whether "all supplement chains resolved and closed
before any MC row is appended" dissolves the collision. It does not,
three ways. (i) The refusal is over the FILE, not over open chains:
`ANY_CHAIN_DEFECT=REFUSE_WHOLE_RESOLUTION` means one MC_RUN_AUTHORIZED row
poisons every FUTURE call to `resolve_supplement_chains` — and future
calls are guaranteed: the A_PRECHECK gate `registry_chain_resolvable` runs
at every future supplement execution, and the deferred
`SUPPLEMENT_CONSUMED_BY_GRID_REPLAY` registration (K-axis, still owed)
means supplement-family rows WILL be appended after MC rows exist. So the
collision is only unreachable if supplement resolution never runs again
after the first MC append — a prohibition nothing enforces. (ii) That
prohibition would be sequencing-by-prose, exactly the unenforced-invariant
class this repo has repeatedly had to repair into parsers. (iii) It
contradicts verify-at-use: the N09 mandatory mitigation orders gates to
re-read real bytes at consumption time, not trust prior resolutions.
R4 amends nothing and fixes nothing; rejected.

```
CONDITIONS=
  C1 (prefix ownership, load-bearing): mc_registry retains ownership of
     every MC_*-prefixed token in ops/TRIAL_REGISTRY.md — unknown-inside-
     prefix refuses the whole resolution (mc_unknown_event_token), and the
     stage-1 malformed-line scan keeps covering the whole MC_ prefix.
     Already built and pinned (test_an_unknown_mc_token_is_refused);
     the condition is that no later change narrows it.
  C2 (atomic ordering, as an invariant not an inventory): the two tokens
     leave the by-name refusal ONLY in the same change that wires
     mc_registry.resolve_mc_chains / find_live_mc_authorization into every
     production path that treats ops/TRIAL_REGISTRY.md as an authorization
     or chain-resolution source (today that is supplement_runner's
     resolver seam and its A_PRECHECK gates; day_strata_supplement,
     real_input and consumer currently refuse unconditionally and MUST NOT
     lose that property before their parse-based replacements land), AND
     that lands with a pinned invariant test: no production reader may act
     on supplement resolution over that file without MC resolution also
     having run and failed closed on either refusal. Until that change,
     the by-name refusal stays byte-identical to today.
  C3 (scope of discharge): exactly MC_RUN_AUTHORIZED and MC_RUN_STARTED.
     The by-name refusal narrows 5→3; SUPPLEMENT_CONSUMED_BY_GRID_REPLAY
     (deferral not discharged — N-D3 ruled no GRID-replay coupling),
     MC_RUN_SEALED and MC_RUN_FAILED (never created) remain refused by
     name. §D.3.4's transcription must remain verifiable: the discharge is
     recorded as an exclusion citing this ruling, not as a silent deletion
     of the ratified list.
  C4 (consumer gate): consumer.authorize_real_mc's unconditional raise may
     be replaced only by a find_live_mc_authorization-based parse, never a
     substring check, and never before C2's wiring. Same for
     day_strata_supplement.authorize_supplement's MC-side successor if one
     is ever built.
  C5 (no riders): the discharging change appends no registry rows, moves
     no exposure state, authorizes nothing, and touches no ratified
     decision record. This ruling is not MC-run authorization and not
     Stage-I/Tier-1 routing.

FALSIFIER=
  F1: a string is found that the pre-R2 supplement grammar refused on a
      well-formed six-cell row and that the post-R2+wiring regime lets
      through at any production call site (mechanically checkable by token
      fuzz across both resolvers).
  F2: after the C2 change, a production path is found that resolves
      supplement chains over ops/TRIAL_REGISTRY.md without MC resolution
      running — the invariant test failing, or a path outside its net.
  F3: a reading of §D.3.4 is established under which the deferral of
      MC_RUN_AUTHORIZED / MC_RUN_STARTED is conditioned on anything beyond
      the N-D3 ruling (e.g. on the GRID-replay coupling being ruled) — that
      would make the discharge premature and this ruling wrong at its root.
  F4: a cross-lifecycle ordering or wedge defect occurs that the single-
      file global sequence would have caught and the post-R2 regime did
      not — that would show the reconciliation traded away real evidence.

COLLATERAL=
  Amend (only after Sol ratification + Aaron, in the C2 change):
    - src/itsf/mc/supplement_registry.py :: is_supplement_row and/or
      _classify_and_validate — the two-token jurisdiction transfer;
      _TOKEN_SCAN_RE untouched (its MC_RUN_* coverage is harmless belt-
      and-braces at stage 1).
    - src/itsf/mc/supplement_runner.py :: the RESOLVER_SEAM gate path —
      MC resolution wired in per C2.
    - tests/test_mc_supplement_registry.py ::
      test_nd3_deferred_tokens_refused_by_name — parametrization 5→3.
    - tests/test_mc_registry_contract.py ::
      test_a_ratified_mc_row_breaks_supplement_resolution — rewritten from
      reproduction to discharge-pin, citing this ruling;
      test_the_two_names_that_do_appear_in_both_are_refused_by_the_
      supplement — assertion inverts (skipped-as-foreign at the supplement
      layer, validated by the MC layer).
    - src/itsf/mc/mc_registry.py :: module docstring "AN OPEN
      CONTRADICTION" paragraph — updated to record the resolution.
    - src/itsf/mc/supplement_contract.py :: annotation on
      ND3_DEFERRED_TOKENS recording the two-token discharge with citation;
      the ratified five-name transcription itself stays verifiable per C3.
    - ops/DECISION_MC_REGISTRY_COLLISION.md — STATUS closure APPENDED
      (append-style, the record's body is not rewritten).
  Must NOT be touched:
    - ops/DECISION_PACKET_N00_AND_ND1.md, ops/DECISION_PACKET_ND2_ND3.md,
      ops/DELEGATED_RULINGS_2026-08-24.md,
      ops/RULING_PROPOSAL_ND2_ND3_FABLE_2026-08-24.md,
      ops/ND1_PROFILE_RATIFICATION.md — ratified/immutable records.
    - G8 itself: NOT amended, in either artifact — that is R2's point.
    - ops/TRIAL_REGISTRY.md — no appends of any kind ride this ruling.
    - scripts/s0_real_run.py — the sealed run's resolver; R3 stays dead.
    - src/itsf/mc/mc_contract.py :: EVENTS / LEGAL_TRANSITIONS /
      AUTHORIZATION_SENTENCE / AARON_ONLY_EVENTS — ruled content, out of
      scope here (including the two G7 tightened edges, which are inside
      the ruling and not part of this question).
    - ops/EXPOSURE_LEDGER.md, STUDY_0_PREREGISTRATION.md, qros-state lane/
      exposure declarations — nothing here is an exposure or lane event.
```

## Findings against the record itself (for the Sol pass)

1. §4's example token contradicts §5: under the recorded R2 shape,
   `MC_RUN_SEALED` stays refused by name. The window's real membership is
   the two discharged tokens — the record overstates by example and
   understates by shape.
2. §4 presents the window as R2-specific; it applies equally to R1
   (nothing parses a new file until wired). Wiring order is the safeguard,
   not file choice.
3. §4 says four production paths "run resolve_supplement_chains"; verified:
   only supplement_runner resolves — the other three refuse
   unconditionally without resolving. The window is narrower than recorded.
4. §2.2 is read one-way in the record; read the other way it favors R2
   MORE strongly (cross-lifecycle order as evidence), argued above.
5. HEAD has moved (13fb936 → 0991d6f) and the five transported files are
   now committed, byte-identical. Non-material; recorded for the chain.

PROPOSAL ENDS. Fresh Sol session ratifies or modifies; Aaron adjudicates.
